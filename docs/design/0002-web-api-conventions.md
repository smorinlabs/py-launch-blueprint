# 0002 — Web API conventions (the WEB-xx baseline)

Status: accepted. Scope: `src/py_launch_blueprint/web/` — the FastAPI service
behind the `web` extra. Each convention carries the WEB-xx id from the
best-practices catalog so future work can reference and extend it.

## Getting started

Install with `uv sync --group dev --extra web`; run with `just serve`
(dev reload) or `python -m py_launch_blueprint.web` (production-shaped).
Optional toggles are env vars (`PLBP_WEB_*`), e.g. `PLBP_WEB_OTEL_ENABLED=1`.
The committed contract lives at `docs/api/openapi.json` — regenerate with
`just export-openapi` after any route change (a test enforces it).

## Contract (A)

- **WEB-01 — errors are [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) Problem Details.** Every non-2xx body is
  `application/problem+json` with `type/title/status/detail/instance`,
  including FastAPI's own 422 validation errors (an `errors` extension
  carries the field details) and bare `HTTPException`s. The
  `PyError → HTTP status` table in `web/problems.py` mirrors the `ExitCode`
  taxonomy in `core/errors.py` and is append-only like it.
- **WEB-02 — business routes live under `/v1`.** Ops endpoints (`/healthz`,
  `/readyz`, `/metrics`) are unversioned. A breaking change means a `/v2`
  router tree, never an in-place mutation. Sunsetting uses
  `versioning.deprecation_headers()`
  ([RFC 8594](https://www.rfc-editor.org/rfc/rfc8594.html) `Deprecation` +
  `Sunset`) plus OpenAPI's `deprecated` flag.
- **WEB-03 — collections paginate** with fastapi-pagination's standard
  envelope: `page`/`size` query params, `items/total/page/size/pages` body.
  Items remain `core.models` objects — the CLI and API share one data
  contract; only the collection envelope is web-specific.
- **WEB-04 — OpenAPI is curated**: tag metadata, `tag-function` operation ids
  (stable names for generated clients), and a real description.
- **WEB-05 — unsafe methods honor `Idempotency-Key`.** Replayed responses are
  marked `Idempotency-Replayed: true`; only 2xx outcomes are cached
  (Stripe semantics). The in-memory store is single-instance — swap in
  Redis behind the same middleware before scaling out.

## Observability (B)

- **WEB-10 — tracing** is opt-in: `otel` extra +
  `PLBP_WEB_OTEL_ENABLED=1` + standard `OTEL_EXPORTER_OTLP_*` env vars.
  Soft-imported; absence degrades to a warning, never a crash.
- **WEB-11 — Prometheus RED metrics** at `/metrics` (on by default,
  excluded from the schema and from its own measurements).
- **WEB-12 — structured logging profile.** One canonical `http_request`
  event per request (route template, status, `duration_ms`, `request_id`);
  JSON Lines on stderr by default (`PLBP_WEB_LOG_LEVEL` / `_LOG_FORMAT`);
  uvicorn loggers folded into the same pipeline. Full conventions:
  `0003-logging-conventions.md`.
- Request-scoped structlog context (`x-request-id` in, bound to every log
  line, echoed out) predates this doc — see `web/middleware.py`.

## Security & traffic (C subset)

- **WEB-22 — rate limiting** is wired (slowapi) but off by default; one env
  var (`PLBP_WEB_RATE_LIMIT=100/minute`) turns it on app-wide. 429s are
  problem documents with `Retry-After`.
- **WEB-23 — security headers** (`nosniff`, `DENY`, `no-referrer`, HSTS) on
  every response; CORS middleware is only installed when
  `PLBP_WEB_CORS_ORIGINS` is non-empty.

## Config & lifecycle (D)

- **WEB-30 — `WebSettings`** (pydantic-settings) is the single config
  surface; env prefix `PLBP_WEB_*` derives from `APP_NAME` so forks rename
  cleanly. Invalid config fails at boot.
- **WEB-31 — graceful shutdown**: `python -m py_launch_blueprint.web` and the
  Dockerfile run uvicorn with `--timeout-graceful-shutdown`; lifespan
  teardown is the hook for closing pools/clients.
- **WEB-32 — production image**: multi-stage uv Dockerfile (locked deps,
  bytecode-compiled, non-root). `just docker-web`.

## Contract safety (F/G subset)

- **WEB-50 — schemathesis** fuzzes every documented operation
  (`tests/web/test_contract.py`, `slow` marker; CI runs it). Currently
  asserts "no 5xx"; widen to response-conformance once error responses are
  declared per-operation.
- **WEB-51 — the OpenAPI snapshot is committed** at `docs/api/openapi.json`.
  `just export-openapi` regenerates; a test fails when stale; the
  `api-contract` workflow runs oasdiff against the base branch and fails
  PRs on breaking changes.
- **WEB-60 — typed clients are generated, never hand-written**:
  `just client-python` (openapi-python-client) from the committed snapshot.

## Deliberately deferred

AuthN/AuthZ middleware (WEB-20/21 — should resolve the same token sources
`core.config` knows), Redis-backed idempotency/rate-limit stores, async
upstream client + retries (WEB-40/41), full schemathesis conformance
checks, and upstream pass-through pagination (today `/v1/projects` slices
pages from one upstream fetch, so `total` reflects that window — fixing it
properly means cursor support in `ProjectsService`).
