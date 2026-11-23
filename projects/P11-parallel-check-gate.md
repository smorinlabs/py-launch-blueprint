# P11 — Parallel `just check` gate

Make the local `just check` gate run its recipes in parallel without losing
any tests, so the inner loop (and `bootstrap-acceptance`, which runs
`just check` inside a generated project) waits for the slowest step instead
of the sum of all of them.

**References**

- **Trunk:** [PROJECTS.md](../PROJECTS.md)
- **Spec:** [Test suite and CI speed](../docs/superpowers/specs/2026-11-22-test-suite-speed-design.md) — Phase A (R1, R2, R3)

**Status:** `[~]` implemented on branch `perf/parallel-check-gate`; PR pending.

### Scope

- R1: `[parallel]` on `check`; the `test` recipe installs the web extra
  itself, so a cold `.venv` still collects `tests/web` whatever the recipe
  order.
- R2: `test-release` runs each `tests/release/*.test.js` file in its own bun
  process (`scripts/run-release-tests.sh`) and fails if any file fails or
  none exist. The release scripts call git synchronously, so
  `bun test --concurrent` cannot overlap them.
- R3: split `tests/release/release_runner.test.js` into lifecycle, preview,
  and guard files. Test bodies are unchanged.

### Out of scope

- R4 (macOS and Windows legs off the PR path): declined by the owner.
- The CI `release-generation` step stays `bun test tests/release`, which
  `tests/meta/test_release_generation.py` asserts.
- Reducing git spawns in the release fixtures (R5).

### Tests & Tasks

- [x] [P11-TS01] `check` carries the `parallel` attribute (`just --dump`).
- [x] [P11-TS02] The `test` recipe runs `uv run --extra web pytest`.
- [x] [P11-TS03] The release runner exits 0 when every file passes, non-zero when any file fails, and non-zero when no test files exist.
- [x] [P11-T01] Add `[parallel]` to `check` and `--extra web` to `test`.
- [x] [P11-T02] Add `scripts/run-release-tests.sh` and call it from `test-release`.
- [x] [P11-T03] Split `release_runner.test.js` into three files; the 20 test names are identical before and after.
- [x] [P11-TS04] A deliberately failing bun file and a deliberately failing pytest test each make `just check` exit 1.
- [ ] [P11-T04] Open the PR, pass CI including `bootstrap-acceptance`, and merge.

### Deliverable

```bash
$ just check
...
All checks passed!
```

### Automated Verification

- `tests/meta/test_check_gate.py` passes.
- `just check` passes; on a cold `.venv` pytest reports 415 passed, 6 skipped.
- `bootstrap-acceptance` passes (it runs the new gate in a generated project).

### Manual Verification

Measured on a 14-core macOS machine, 3 warm runs plus cold runs:

| | Before | After |
|---|---|---|
| `just check`, warm `.venv` | 15.1–20.9 s | 5.1–5.3 s |
| `just check`, cold `.venv` | 20.9 s (first run) | 6.9 s |
| `test-release` alone | 11.5 s | 5.2 s |
