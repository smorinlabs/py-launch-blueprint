# 0015. One logging pipeline, two front-end profiles

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer (interactive), implemented in PR #420
- **Related:** `docs/design/0003-logging-conventions.md` (the full
  conventions this decision anchors); `core/logging.py`, `web/logging.py`,
  `cli/context.py`; ADR 0012 (redact at collection), ADR 0013 (web service
  baseline, WEB-12)

## Context

The structlog pipeline in `core/logging.py` was designed CLI-first (TTY
detection, `-v`/`-q` levels, an opt-in rotating file sink). The web service
initially borrowed it with all defaults: its own INFO-level startup logs
were silently dropped (console default WARNING), telemetry wiring logged
*before* configuration (landing unformatted on stdout), uvicorn's plain-text
access lines interleaved with structured app logs, and there was no way to
configure web log level or format at all. Meanwhile `core/` library code
logs without knowing which front-end invoked it — so the rendering pipeline
itself cannot fork per front-end without splitting every shared event's
shape.

## Decision

We will keep **one** logging implementation — the processor chain,
renderers, sinks, and guarantees in `core/logging.py` — and express
front-end differences as thin **policy profiles** on top of it:

- The **pipeline** (shared, both profiles): logger names, ISO-UTC
  timestamps, contextvars merging, trace correlation (`trace_id`/`span_id`
  when the `otel` extra is active), key-based secret redaction, exception
  rendering, and `JSONRenderer(default=str)` so a log call never raises.
- The **CLI profile** (`cli/context.py`): level from flag → env → config →
  WARNING; TTY-auto format; opt-in rotating file sink.
- The **web profile** (`web/logging.py`): level/format from `WebSettings`
  env vars only, defaulting to INFO + JSON Lines on stderr; no file sink
  (the platform ships logs); uvicorn loggers folded into the root pipeline
  with its access line replaced by the canonical `http_request` event;
  configured at the top of `create_app()` so logging precedes any code
  that can log.

## Consequences

- `core/` code emits identically shaped events under both front-ends; one
  redaction implementation, one test surface for the pipeline.
- A deployment emits a single JSONL stream — uvicorn lifecycle, access
  events, and app logs all parse the same way.
- The dependency arrow stays one-way: `core/logging.py` knows nothing of
  `WebSettings` or uvicorn; new front-ends (worker, TUI) add a profile,
  not a pipeline.
- Per-sink exception rendering (e.g. `dict_tracebacks` for JSON only) is
  harder, since the pre-chain is shared — accepted: tracebacks stay strings.
- Adding a logging knob now means deciding which layer owns it (pipeline
  vs. profile) — a deliberate speed bump.

## Alternatives considered

- **Separate web logging stack** (own structlog config or a different
  library) — rejected: shared `core/` events would render divergently,
  redaction would exist twice, and the test surface doubles.
- **Web reuses the CLI's resolution (config file `[logging]` table)** —
  rejected: 12-factor services configure via environment; the config file
  is a CLI-user concern and would make deployments host-state-dependent.
- **Route uvicorn's access log through a formatter instead of replacing
  it** — rejected: the line would be structured but still lack
  `request_id`, the route template, and `duration_ms`; it is the wrong
  event, not the wrong format.
