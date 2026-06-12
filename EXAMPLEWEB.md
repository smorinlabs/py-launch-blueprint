# `plbp` web service — REST over the same core

The web service is the FastAPI counterpart of the `plbp` CLI: a thin adapter
over the same `core` library, exposing the same Pydantic models over HTTP with
production REST practices already wired (each carries a **WEB-xx** id — see
[docs/design/0002](docs/design/0002-web-api-conventions.md)).

## Architecture

The package is split into three layers under `src/py_launch_blueprint/`:

| Layer | Path | Role |
|-------|------|------|
| Library (`core`) | `core/` | Pure logic + Pydantic models. No printing. Reused by every front-end. |
| CLI (`cli`) | `cli/` | Thin presentation: formats `core` results. See [EXAMPLECLI.md](EXAMPLECLI.md). |
| Web (`web`) | `web/` | Thin adapter: serves `core` results as JSON (behind the `web` extra). |

The model returned by a route **is** the JSON representation — the same
`core/models.py` objects the CLI renders. A new endpoint is one router module
plus one entry in `web/routers/__init__.py`, like the CLI's command groups.

## Run it

```bash
uv sync --group dev --extra web      # install the web extra
just serve                           # dev server with auto-reload
python -m py_launch_blueprint.web    # production-shaped runner (settings-driven)
just docker-web                      # multi-stage production image (optional)
```

Interactive docs are at `http://127.0.0.1:8000/docs` once running.

## Endpoints

| Path | Purpose |
|------|---------|
| `/healthz` | Liveness + version (unversioned ops endpoint) |
| `/readyz` | Readiness — same checks as `plbp doctor`; 503 problem doc on failure |
| `/metrics` | Prometheus RED metrics (on by default) |
| `/v1/projects` | Paginated project collection (`page`/`size` query params) |
| `/v1/projects/{id}` | Single project |

Business routes live under `/v1` (WEB-02); a breaking change means a `/v2`
tree, never an in-place mutation.

## Configuration (env vars, WEB-30)

Everything is a `PLBP_WEB_*` env var (prefix derived from the app name, so
forks rename cleanly). Invalid values fail at boot. Risky features are wired
but **off by default** — one env var enables each.

| Env var | Default | Effect |
|---------|---------|--------|
| `PLBP_WEB_HOST` / `PLBP_WEB_PORT` | `127.0.0.1` / `8000` | Bind address for the runner |
| `PLBP_WEB_ROOT_PATH` | empty | Path prefix when behind a reverse proxy |
| `PLBP_WEB_CORS_ORIGINS` | `[]` | JSON list; empty = CORS middleware not installed |
| `PLBP_WEB_RATE_LIMIT` | unset | e.g. `100/minute`; unset = rate limiting off (WEB-22) |
| `PLBP_WEB_METRICS_ENABLED` | `true` | `/metrics` endpoint (WEB-11) |
| `PLBP_WEB_OTEL_ENABLED` | `false` | OTel tracing — needs the `otel` extra (WEB-10) |
| `PLBP_WEB_IDEMPOTENCY_TTL_SECONDS` | `86400` | Idempotency replay-cache TTL (WEB-05) |
| `PLBP_WEB_GRACEFUL_SHUTDOWN_SECONDS` | `10` | Drain window on shutdown (WEB-31) |

Secrets follow the CLI's rule: the API token resolves from `$PLBP_TOKEN` only
and is never stored in config (see ADR 0002).

## Error contract (RFC 9457, WEB-01)

Every non-2xx response — domain errors, 404s, validation failures, 429s,
failed readiness — is an `application/problem+json` document:

```json
{
  "type": "about:blank",
  "title": "Unauthorized",
  "status": 401,
  "detail": "no API token configured (set $PLBP_TOKEN)",
  "instance": "/v1/projects"
}
```

The `PyError` → HTTP status table mirrors the CLI's exit-code taxonomy in
`core/errors.py` (append-only, shared domain knowledge):

| Failure | CLI exit code | HTTP status |
|---------|---------------|-------------|
| `AuthError` | 2 | 401 |
| `APIError` (upstream failed) | 3 | 502 |
| `ConfigError` | 1 | 500 |
| Validation | — | 422 (+ `errors` extension) |
| Rate limited | — | 429 (+ accurate `Retry-After`) |
| Not ready | — | 503 (+ `diagnostics` extension) |

The OpenAPI schema declares this shape (not FastAPI's default), so generated
clients parse errors correctly.

## Baked-in behaviors

- **Request ids + security headers (WEB-23)** — every response (including
  rate-limited and CORS-preflight short circuits) carries `x-request-id`
  (bound into structlog context, echoed if the client sends one) plus
  HSTS/nosniff/frame-deny headers.
- **Idempotency (WEB-05)** — send `Idempotency-Key` on POST/PUT/PATCH;
  successful responses replay (marked `Idempotency-Replayed: true`) instead
  of re-executing. In-memory store; swap in Redis before scaling out.
- **Pagination (WEB-03)** — collections take `page`/`size` and return
  `items`/`total`/`pages` (fastapi-pagination envelope).
- **Observability (WEB-10/11)** — Prometheus metrics by default; OTel tracing
  via `uv sync --extra web --extra otel` + standard `OTEL_*` env vars.

## Usage

```bash
# Liveness / readiness (readiness mirrors `plbp doctor`)
curl -s http://127.0.0.1:8000/healthz | jq
curl -s http://127.0.0.1:8000/readyz | jq

# Paginated projects (same models as `plbp projects list --json`)
curl -s "http://127.0.0.1:8000/v1/projects?page=1&size=20" | jq
curl -s http://127.0.0.1:8000/v1/projects/12345 | jq

# Errors are problem documents — inspect one
curl -s http://127.0.0.1:8000/v1/projects/does-not-exist | jq

# Idempotent retry (for the POST/PUT/PATCH endpoints you add): the second
# call with the same key replays the first response instead of re-executing
curl -s -X POST -H "Idempotency-Key: demo-1" http://127.0.0.1:8000/v1/<your-endpoint>
```

## Contract safety (WEB-50/51/60)

The committed snapshot `docs/api/openapi.json` **is** the API contract:

1. After any route change run `just export-openapi` and commit — a test
   fails while the snapshot is stale.
2. PRs touching the snapshot trigger oasdiff breaking-change detection
   against the base branch (`api-contract` workflow).
3. Schemathesis fuzzes every documented operation (`just test-web`).
4. Generate a typed client with `just client-python` — never hand-write one.

For the full convention catalog and rationale see
[docs/design/0002](docs/design/0002-web-api-conventions.md) and
[ADR 0013](docs/adr/0013-web-service-best-practices.md); the user guide lives
at [docs/source/web/index.md](docs/source/web/index.md).
