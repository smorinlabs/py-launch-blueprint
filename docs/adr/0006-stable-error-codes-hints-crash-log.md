# 0006. Stable error codes, hints, and a crash log

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer (interactive), implemented in PR #400
- **Related:** `EXAMPLECLI.md` §"Exit codes & error codes"; `core/errors.py`; ADR 0004

## Context

Exit codes are coarse (six values, append-only, scripts branch on them) and
say nothing about *which* failure occurred. Error messages are prose — they
can't be referenced from docs or issue reports, and unexpected exceptions
vanished entirely unless the user happened to pass `--verbose`.

## Decision

Three-part error contract, all append-only:

1. Every expected error carries a **stable `PLBP###` error code** (a string
   constant in `core/errors.py`, finer-grained than exit codes — many codes
   may share one exit code) plus an optional **`hint`**: one actionable next
   step rendered under the message and as a `hint` key in the JSON error
   object.
2. **Unexpected exceptions** — including failures while building the
   `AppContext` at startup — emit `PLBP000`, exit `IO` (4), and always
   append the full traceback to `<state>/plbp/plbp_crash.log`, printing
   `full traceback: <path>` so nothing is lost without `--verbose`.
3. The JSON `error` object only ever **gains** keys (`error_code`, `hint`,
   `traceback_path`); existing keys (`code`, `name`, `message`) are frozen.

Codes are literal strings (not derived from `APP_NAME` at runtime) and the
files carrying them are registered in `init/manifest.toml`, so a fork's
`just init` rewrites the prefix wholesale — same convention as the `PLBP_*`
env vars.

## Consequences

- Scripts and docs can reference precise failures; bug reports gain a
  greppable identifier and a crash log to attach.
- The code table is a contract: numbers are never reused or renumbered, and
  new error classes must claim the next free number.
- Crash-log writes are best-effort (an unwritable state dir must never mask
  the original error).

## Alternatives considered

- **Reuse exit codes as the only identifier** — rejected: six values cannot
  distinguish failure modes, and POSIX exit-code space is too small to grow.
- **Derive the prefix from `APP_NAME` at runtime** — rejected: user-facing
  literals stay greppable and manifest-tracked (repo convention).
