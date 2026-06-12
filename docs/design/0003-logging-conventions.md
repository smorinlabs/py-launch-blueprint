# 0003 — Logging conventions (one pipeline, two profiles)

- **Status:** Accepted
- **Type:** Conventions
- **Created:** 2026-06-12
- **Applies to:** every log line the project emits — `core/logging.py`
  (the shared pipeline), `cli/context.py` (the CLI profile), and
  `web/logging.py` (the web profile, WEB-12)

Spawned from the web conventions catalog (`0002-web-api-conventions.md`,
Observability section); the load-bearing decision is recorded in ADR
[0015](../adr/0015-one-logging-pipeline-two-profiles.md).

## Architecture: pipeline vs. policy

There is **one** logging implementation, in `core/logging.py`: structlog
renders events, stdlib handlers own the sinks. `core/` library code logs
without knowing which front-end is running, so the pipeline — processors,
renderers, redaction — cannot fork. What differs per front-end is *policy*:

| Concern | CLI profile (`cli/context.py`) | Web profile (`web/logging.py`) |
|---|---|---|
| Level source | flag → env → config file → default | `<APP_NAME>_WEB_LOG_LEVEL` only |
| Default level | `warning` (quiet tool) | `info` (lifecycle + access events) |
| Default format | `auto` (pretty on a TTY, JSON piped) | `json` (structured is the contract) |
| File sink | opt-in, rotating (R11) | never — stderr only, platform ships logs |
| Bound context | command-scoped | `request_id` (+ `trace_id` when otel is on) |

## Output format

Machine output is **JSON Lines**: one self-contained JSON object per event,
newline-terminated, on **stderr** (stdout stays pipe-safe for results).
Non-JSON-native values degrade via `default=str` — a log call must never
raise. Keep values JSON-native (numbers as numbers: `duration_ms=12.3`, not
`"12.3ms"`) and never nest pre-serialized JSON strings inside fields.

## Event taxonomy

- **Event names** are `snake_case` facts: `web_startup`, `request_failed`,
  `http_request`, `otel_unavailable`. The name identifies *what happened*;
  everything variable rides in keys.
- **Reserved keys** (stamped by the pipeline, never set manually):
  `event`, `level`, `logger`, `timestamp` (ISO-8601 UTC), `request_id`,
  `trace_id`, `span_id`.
- **Units live in key names**: `duration_ms`, `size_bytes`, `ttl_seconds`.
- **Bounded cardinality** for queryable fields: the access event's `route`
  is the template (`/v1/projects/{project_id}`), with the raw `path`
  alongside for debugging. Unmatched requests (404s) log `route=null` —
  never the raw URL, which would unbound the field.

## Level policy

- `warning`+ — actionable: someone may need to do something.
- `info` — lifecycle (`web_startup`) and the canonical access event.
- `debug` — diagnostics (`api_request`, resolved invocation context).
- Log a failure **once**, at the boundary that handles it (the problem
  handlers, the CLI error renderer) — no log-and-raise double reporting.

## Pipeline guarantees (every sink, both profiles)

- **Redaction is structural**: values whose key contains a sensitive
  fragment (`token`, `password`, `secret`, `authorization`, `api_key`, …,
  see `SENSITIVE_KEY_PARTS`) are masked in the processor chain — the logging
  analog of ADR-12's redact-at-collection. Call sites still must not put
  secrets in *values* of innocent keys or in event names.
- **Trace correlation**: when the `otel` extra is active and a span is
  recording, every event carries `trace_id`/`span_id`, so logs join traces.
- **Tracebacks ride inside the event** (`exception` key) so they survive
  JSON output. They stay strings (not `dict_tracebacks`): the pre-chain is
  shared with the pretty console renderer, which formats strings well.

## The canonical access event (WEB-12)

`RequestIDMiddleware` emits exactly one `http_request` per request —
`method`, `route`, `path`, `status`, `duration_ms`, `client`, plus the
pipeline's `request_id` — including when the handler raises (status 500).
Probe endpoints (`/healthz`, `/readyz`, `/metrics`) are excluded, mirroring
the metrics instrumentation. uvicorn's plain-text access line is silenced
and its lifecycle loggers propagate through the shared pipeline
(`web/logging.py`), so a deployment emits **one** format. Unexpected
exceptions are logged once, structured, by the catch-all problem handler
(`unhandled_error`) — the client gets a generic RFC 9457 document, never
internals.
