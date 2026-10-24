# P10 — OTel extra CI coverage

Exercise the `otel` extra in CI so `opentelemetry-*` dependency bumps are
validated by a PR check instead of by hand.

**References**

- **Trunk:** [PROJECTS.md](../PROJECTS.md)
- **Origin:** dependabot sweep `RUN-PLBP-20261024`, follow-up `ISS-001` (PRs #570/#571 needed manual otel validation)

**Status:** `[x]` merged in [PR #587](https://github.com/smorinlabs/py-launch-blueprint/pull/587) (merge commit `ef9675e`, 2026-10-24).

### Scope

Every CI job syncs `--extra web` only, so `instrument_tracing()` in
`web/telemetry.py` always takes its "extra missing" branch and
`_add_trace_context()` in `core/logging.py` always no-ops. No test covers the
enabled path. Add tests for both paths and one CI job that installs the extra.

### Out of scope

- Adding `--extra otel` to the main test matrix: that matrix keeps testing the
  default no-otel install and its degrade path.
- Exporting spans to a real collector.

### Tests & Tasks

- [x] [P10-TS01] `instrument_tracing` returns True, installs a provider named `<APP_NAME>-web`, and instruments the app (skips without the extra).
- [x] [P10-TS02] `instrument_tracing` returns False and leaves the app uninstrumented when otel imports fail (runs in every env).
- [x] [P10-TS03] `_add_trace_context` stamps `trace_id`/`span_id` inside a recording span and is a no-op outside one (skips without the extra).
- [x] [P10-T01] Add a `test-otel` CI job (ubuntu / py3.13) syncing `--extra web --extra otel`, running the web and logging tests; wire it into `ci-ok`.
- [x] [P10-T02] Pass `just check`, open the PR, and merge. `test-otel` passed on its first CI run.

### Automated Verification

- `test-otel` runs the otel tests (not skipped) and passes; `ci-ok` depends on it.
- The main matrix still passes with the otel tests skipped.
