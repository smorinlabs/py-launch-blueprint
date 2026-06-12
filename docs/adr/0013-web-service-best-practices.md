# 0013. Web service: baked-in REST best practices behind the `web` extra

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer, implemented in PRs #395 and #399
- **Related:** [design 0002](../design/0002-web-api-conventions.md) (the
  WEB-xx convention catalog); ADR 0001 (app naming), ADR 0002 (no secrets in
  config); docs section: [Web service](../source/web/index.md)

## Context

The blueprint's goal is to bake in the well-researched best practices teams
rarely get around to. The CLI layer already had this treatment (design 0001);
the web layer was a reserved stub. A REST service has its own catalog of
"everyone wants it, nobody wires it" practices: a single error envelope,
versioning, pagination, idempotency, metrics/tracing, rate limiting, security
headers, typed configuration, and — above all — contract safety (knowing when
a PR breaks the API).

Constraints: the web layer must stay a *thin adapter* over
`py_launch_blueprint.core` (one data contract shared with the CLI), must not
burden CLI-only installs, and every file must remain rebrandable by the init
system.

## Decision

Implement the catalog as identified conventions (**WEB-01..WEB-60**, see
design 0002) with one best-of-breed library each, all behind extras:

1. **Packaging** — the service ships in the `web` extra (FastAPI + uvicorn +
   pydantic-settings + fastapi-pagination + slowapi +
   prometheus-fastapi-instrumentator). OpenTelemetry is a further `otel`
   extra, soft-imported so its absence degrades to a log line.
2. **One error envelope** — every non-2xx response (including FastAPI's own
   422s and ops endpoints) is RFC 9457 `application/problem+json`; the
   `PyError` → HTTP status table mirrors `core/errors.py`'s exit-code
   taxonomy. The OpenAPI schema is post-processed to declare this truthfully.
3. **Typed env config** — `WebSettings` (pydantic-settings) under a
   `<APP_NAME>_WEB_` prefix derived from the single `APP_NAME` source;
   invalid config fails at boot. Risky features (CORS, rate limiting,
   tracing) are wired but **off by default**; one env var enables each.
4. **Contract safety is enforced, not aspirational** — the OpenAPI snapshot
   is committed (`docs/api/openapi.json`); a test fails when it is stale;
   the `api-contract` workflow runs oasdiff breaking-change detection
   against the base branch; schemathesis fuzzes every documented operation
   in CI; typed clients are generated from the snapshot, never hand-written.
5. **Middleware ordering is a contract** — request-id and security-headers
   middleware sit OUTERMOST so short-circuiting layers (CORS preflights,
   rate-limit 429s) still emit them. Idempotency replay
   (`Idempotency-Key`, Stripe semantics: only 2xx cached) sits innermost
   with an in-memory store shaped for a Redis swap.
6. **Production posture** — `python -m py_launch_blueprint.web` runs
   uvicorn with settings-driven graceful shutdown; the multi-stage uv
   Dockerfile is non-root, lockfile-frozen, bytecode-compiled, with a
   `/healthz` HEALTHCHECK.

## Consequences

- The API surface is reviewable: route changes show up as an
  `openapi.json` diff, and breaking changes fail the PR.
- `/v1/projects` moved from `/projects`, and error bodies changed shape —
  acceptable pre-any-consumer; future breaking changes require `/v2`.
- New web files (and docs naming identity values) must be registered in
  `init/manifest.toml` — the drift check and fork-mode integration enforce
  this, and both were exercised by these PRs.
- Deliberately deferred (documented in design 0002): AuthN/AuthZ (must
  resolve the same token sources as the CLI), Redis-backed
  idempotency/rate-limit stores, async upstream client + retries
  (WEB-40/41), upstream pass-through pagination, and full schemathesis
  response-conformance checks.

## Alternatives considered

- **Hand-rolled error shape** (`{"error": ...}`) — rejected: RFC 9457 is the
  standard, machine-parseable, and extensible; the first skeleton's ad-hoc
  shape was replaced before any consumer existed.
- **Bigger frameworks for cross-cutting concerns** (e.g. a full API gateway,
  Kong/Envoy-side rate limiting) — out of scope for a template; slowapi and
  in-process middleware keep the blueprint self-contained while leaving the
  gateway path open.
- **Always-on OTel in the `web` extra** — rejected: the dependency tree is
  heavy and tracing is deployment-specific; a soft-imported `otel` extra
  keeps `pip install py-launch-blueprint[web]` lean.
- **Generating OpenAPI on the fly only** (no committed snapshot) — rejected:
  without a committed artifact there is nothing for PR review, oasdiff, or
  client generation to diff against; the snapshot IS the contract.
