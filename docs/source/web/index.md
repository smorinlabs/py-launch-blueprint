# Web Service (FastAPI)

The blueprint ships an optional REST service: a *thin adapter* over the same
`core` library the CLI uses, with production best practices already wired.
Each convention carries a **WEB-xx** id — the full catalog and rationale live
in [design 0002](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/design/0002-web-api-conventions.md)
and [ADR 0013](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0013-web-service-best-practices.md).
For the root-level walkthrough (the web counterpart of EXAMPLECLI.md) see
[EXAMPLEWEB.md](https://github.com/smorinlabs/py-launch-blueprint/blob/main/EXAMPLEWEB.md).

## Quick start

```bash
uv sync --group dev --extra web   # install (the web extra)
just serve                        # dev server with auto-reload
python -m py_launch_blueprint.web # production-shaped runner
just test-web                     # web test suite incl. contract fuzzing
```

Interactive docs are at `http://127.0.0.1:8000/docs` once running.

## Endpoints

| Path | Purpose |
|---|---|
| `/healthz` | Liveness + version (unversioned ops endpoint) |
| `/readyz` | Readiness — same checks as `plbp doctor`; 503 problem doc on failure |
| `/metrics` | Prometheus RED metrics (WEB-11; on by default) |
| `/v1/projects` | Paginated project collection (WEB-02/03) |
| `/v1/projects/{id}` | Single project |

Business routes live under `/v1`; a breaking change means a `/v2` tree, never
an in-place mutation.

## Configuration (WEB-30)

Everything is an env var with the `PLBP_WEB_` prefix (derived from the app
name, so forks rename cleanly). Invalid values fail at boot.

| Env var | Default | Effect |
|---|---|---|
| `PLBP_WEB_HOST` / `PLBP_WEB_PORT` | `127.0.0.1` / `8000` | Bind address for the runner |
| `PLBP_WEB_CORS_ORIGINS` | `[]` | JSON list; empty = CORS middleware not installed |
| `PLBP_WEB_RATE_LIMIT` | unset | e.g. `100/minute`; unset = rate limiting off (WEB-22) |
| `PLBP_WEB_METRICS_ENABLED` | `true` | `/metrics` endpoint (WEB-11) |
| `PLBP_WEB_OTEL_ENABLED` | `false` | OTel tracing — needs the `otel` extra (WEB-10) |
| `PLBP_WEB_IDEMPOTENCY_TTL_SECONDS` | `86400` | Idempotency replay-cache TTL (WEB-05) |
| `PLBP_WEB_GRACEFUL_SHUTDOWN_SECONDS` | `10` | Drain window on shutdown (WEB-31) |

## The error contract (WEB-01)

Every non-2xx response — domain errors, 404s, validation failures, 429s,
failed readiness — is an [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html)
`application/problem+json` document:

```json
{
  "type": "about:blank",
  "title": "Unauthorized",
  "status": 401,
  "detail": "no API token configured (set $PLBP_TOKEN)",
  "instance": "/v1/projects"
}
```

Validation errors add an `errors` extension; failed readiness adds
`diagnostics`. The OpenAPI schema declares this shape (not FastAPI's default),
so generated clients parse errors correctly.

## Baked-in behaviors

- **Pagination (WEB-03)** — collections take `page`/`size` and return
  `items`/`total`/`pages` (fastapi-pagination envelope).
- **Idempotency (WEB-05)** — send `Idempotency-Key` on POST/PUT/PATCH;
  successful responses replay (marked `Idempotency-Replayed: true`) instead
  of re-executing. In-memory store; swap in Redis before scaling out.
- **Request ids + security headers (WEB-23)** — every response (including
  rate-limited and CORS-preflight short circuits) carries `x-request-id`
  (bound into structlog context) plus HSTS/nosniff/frame-deny headers.
- **Rate limiting (WEB-22)** — one env var enables an app-wide limit; 429s
  are problem docs with accurate `Retry-After`/`X-RateLimit-*` headers.
- **Observability (WEB-10/11)** — Prometheus metrics by default; OTel
  tracing via `uv sync --extra web --extra otel` + standard `OTEL_*` vars.

## Contract safety (WEB-50/51/60)

The committed snapshot `docs/api/openapi.json` **is** the API contract:

1. After any route change run `just export-openapi` and commit — a test
   fails while the snapshot is stale.
2. PRs touching the snapshot trigger the `api-contract` workflow: oasdiff
   flags breaking changes against the base branch.
3. Schemathesis fuzzes every documented operation (`just test-web`).
4. Generate a typed client with `just client-python` — never hand-write one.

## Deployment (WEB-31/32)

`just docker-web` builds a multi-stage uv image: locked dependencies,
bytecode-compiled, non-root user, `/healthz` HEALTHCHECK, graceful shutdown.
The container binds `0.0.0.0`; the in-code default stays loopback.

Docker itself is **optional** — only this recipe needs it. `make check`
reports it as an optional dependency; install with `make install-docker`
(or `make install-docker-force` on Linux).

## Adding an endpoint

1. Put logic in `core/` (models + service) — the web layer stays thin.
2. Create a router in `web/routers/`, add it to `ROUTERS` in
   `web/routers/__init__.py` (one import + one entry, like the CLI's
   command groups).
3. `just export-openapi`, commit the snapshot, and register any new files
   containing identity values in `init/manifest.toml`.
