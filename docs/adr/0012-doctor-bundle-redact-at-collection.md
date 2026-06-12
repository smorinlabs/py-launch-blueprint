# 0012. `doctor --bundle` redacts at collection time, excludes log contents

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer (interactive), implemented in PR #400
- **Related:** `core/diagnostics.py`; `core/models.py` (`DiagnosticsBundle`); ADR 0002

## Context

Bug reports need environment context (version, platform, resolved config,
relevant env vars), but a diagnostics dump is built precisely to be pasted
into a **public** issue — anything secret that enters the bundle model will
eventually leak via serialization, logging, or copy-paste.

## Decision

`plbp doctor --bundle` renders a `DiagnosticsBundle` in which secrets are
**redacted at collection time** — they never enter the model at all. The
token appears only as presence + source; app-prefixed env vars whose names
contain a secret-shaped marker (`TOKEN`, `SECRET`, `KEY`, `PASSWORD`,
`CRED`, `PRIVATE`) have their values replaced with `<redacted>` before the
model is constructed. Log file **contents are excluded** — only the sink
path is included — because logs can quote user data the redaction markers
cannot anticipate.

## Consequences

- No renderer, serializer, or future front-end can leak what was never
  collected.
- Maintainers may occasionally need to ask for specific log lines that the
  bundle deliberately omits — an explicit, conscious second step.
- The marker list is intentionally broad and append-friendly; false
  positives (redacting a non-secret) are harmless.

## Alternatives considered

- **Redact at render time** — rejected: every output path (JSON, text,
  future web) must then re-implement redaction; one missed path leaks.
- **Include the last N log lines** — rejected for the default: logs are
  free-form and may quote tokens or user data; the path lets users share
  deliberately.
