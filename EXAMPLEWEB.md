# `web` — FastAPI front-end

The web service is the second front-end over the same typed core as the
[`plbp` CLI](EXAMPLECLI.md): one set of Pydantic models, one services layer,
one error taxonomy. `plbp projects list --json` and `GET /projects` return
the same object.

## Architecture

| Layer | Path | Role |
|-------|------|------|
| Library (`core`) | `core/` | Pure logic + Pydantic models. No printing. Reused by every front-end. |
| CLI (`cli`) | `cli/` | Thin presentation over `core` (see [EXAMPLECLI.md](EXAMPLECLI.md)). |
| Web (`web`) | `web/` | FastAPI app factory + routers, behind the `web` extra. One module per noun in `web/routers/`. |

`create_app()` (in `web/app.py`) wires logging, config, error handling, the
operational endpoints, and every router. Adding a noun is one import + one
entry in `ROUTERS` (`web/routers/__init__.py`) — the web mirror of adding a
noun group to the CLI.

## Install & run

The web service ships behind the `web` extra; the core library and CLI never
pay for FastAPI unless you ask for it:

```bash
uv sync --extra web                    # dev environment
pip install "py-launch-blueprint[web]" # consumers

just serve                             # dev server with auto-reload
just serve 0.0.0.0 9000                # custom host/port
# equivalent raw command:
uv run --extra web uvicorn py_launch_blueprint.web.app:create_app --factory --reload
```

FastAPI serves interactive OpenAPI docs at `/docs` while running.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /healthz` | Liveness: process is up; returns the version (the web analog of `--version`). |
| `GET /readyz` | Readiness: runs the same checks as `plbp doctor`; `503` if any check errors. |
| `GET /projects?workspace=&limit=` | List projects — same `ProjectList` model the CLI renders. |
| `GET /projects/{id}` | Fetch one project. |

## Error contract

Handled `PyError`s map to HTTP statuses in `ERROR_STATUS` (`web/app.py`) —
the web analog of the CLI's exit-code table in `core/errors.py`, and
append-only for the same reason:

| Error | Status |
|-------|--------|
| `AuthError` | 401 |
| `ConfigError` | 500 |
| `APIError` | 502 (this service is a gateway; the upstream API failed) |

The body is `{"error": "<message>"}`; statuses share the domain knowledge
("which failure is whose fault") with the CLI's `ExitCode`/`PLBP###` tables.

## Config, auth, and logging

- Config loads **once** in the app lifespan (the web mirror of the CLI's
  `AppContext`) and is injected per-request via `ConfigDep`.
- The token resolves from `$PLBP_TOKEN` only — never a config file (same
  rule as the CLI; see ADR 0002) — and only endpoints that need it trigger
  the lookup: `/healthz` and `/readyz` work tokenless; `/projects` returns
  `401` when it is missing.
- Every request gets a **request id** (`x-request-id` honored or generated),
  bound into the structlog context and echoed in the response header — the
  request-scoped twin of the CLI's command-scoped log context.

## Testing

```bash
just test-web        # pytest tests/web (installs the web extra; TestClient needs httpx)
```

Tests drive the app in-process with FastAPI's `TestClient`; no server or
network required.
