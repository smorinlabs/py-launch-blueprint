# Test suite and CI speed: analysis and proposal

Status: proposal. Nothing in this document has been implemented. Owner
decision on 2026-11-22: R4 declined; keep the full test matrix on PRs. Priority order agreed with the owner: the local inner loop
first, then pull request (PR) wall-clock time in CI.

## Answer first

The pytest suite is not the bottleneck. Of its 419 tests, the 418 that are
not marked `live` run serially in about 3.2 s. The one `live` test, an
end-to-end project generation, takes 55–89 s and runs only in CI. The waits
come from four other places:

| Where you wait | Measured today | What sets it | Proposed result |
|---|---|---|---|
| Local `just check` | 15–21 s | Ten recipes run one after another; `test-release` (bun) alone is 11.5 s | 8.3 s measured in a prototype; about 4 s estimated after one more step |
| Local `git push` (pre-push hook) | 6.3 s | `press verify` (6.28 s); the six other checks finish in under 0.7 s | Keep as is (see R8) |
| PR time-to-mergeable (required checks) | 66 s p50 | macOS and Windows test legs, mostly runner queue time | Unchanged: R4 (about 52 s) was declined |
| PR time-to-all-green | 96 s p50 | `bootstrap-acceptance` (not required); its inner `just check` takes 45 s in a typical PR run | About 70 s estimated, via the same `just check` fix |

One change helps both priorities. Making `just check` parallel shortens the
local loop. It also shortens `bootstrap-acceptance`, which runs `just check`
inside a freshly generated project.

No test is worth removing to save time. The most expensive pytest file costs
0.83 s.

## Method and data provenance

- **Local:** a 14-core macOS machine (Darwin 27.2) with `uv`, just 1.59.0, and
  lefthook 2.2.2, at commit `cfdfb07`. Each figure is wall time from 1–3 runs,
  so treat differences under about 0.5 s as noise. Measurements ran in a
  throwaway clone and in a fresh worktree, so the main checkout's state (see
  Side findings) did not affect them.
- **bun:** the measurements used bun 1.4.5, the version installed locally. The
  repository pins 1.3.5 in `.bun-version`. CI runs the same bun suite in 7 s
  on Linux against 11.5 s here. The difference matches macOS's slower process
  spawning; disabling global and system git configuration changed nothing.
- **CI:** the GitHub Actions REST API, using the last 12–30 successful runs of
  each workflow on the PR path, as of 2026-11-22. Figures are p50 and p90 (the
  median and the 90th percentile). Job duration runs from `started_at` to
  `completed_at`. Queue time runs from `created_at` to `started_at`.
- **Required checks:** classic branch protection requires `ci-ok`,
  `commitlint (humans)`, `actionlint`, `bandit`, `codespell`,
  `editorconfig-check`, `yamllint`, and `press-verify`. The "CodeQL & PR
  Enforcement" ruleset adds a `code_scanning` rule and a merge queue
  (`ALLGREEN`, `min_entries_to_merge: 1`). `bootstrap-acceptance` is **not**
  required.

## Local inner loop

### `just check`, step by step (warm `.venv`)

`just` runs a recipe's dependencies one at a time unless the recipe carries
`[parallel]`. `check` does not carry it, so the gate costs the **sum** of its
steps.

| Step (recipe) | What it runs | Time | Share |
|---|---|---|---|
| `test-release` | `bun test tests/release` (20 tests, 3 files) | 11.8 s | ~75% |
| `test` | `uv run pytest` (default markers, no `-n`) | 3.35 s | ~20% |
| `typecheck` | `ty check` | 0.49 s | |
| `tach` | `tach check` | 0.41 s | |
| `lint` | `ruff check .` and `ruff format --check .` | 0.38 s | |
| `lint-imports` | import-linter | 0.37 s | |
| `check-yaml` | yamllint | 0.36 s | |
| `check-spelling` | codespell | 0.29 s | |
| `check-editorconfig` | editorconfig-checker | 0.29 s | |
| `check-shell` | shellcheck | 0.25 s | |
| **Whole gate** | | **15.1–20.9 s** | |

Cold path in a fresh worktree: `just setup` takes 7.1 s, then the first
`just check` takes 20.9 s.

### Why `test-release` is slow

- `release_runner.test.js` takes 8.06 s of the 11.5 s. It starts **1,114 git
  processes**. `release_commits.test.js` takes 3.75 s and starts 481 git
  processes. `reproduction.test.js` takes 0.34 s and starts 30.
- The test helpers (`tests/release/helpers.cjs`) and the generator
  (`scripts/release_commits.cjs`) call git through `execFileSync`. That call
  blocks bun's event loop, so `bun test --concurrent` measured 11.5 s, the
  same as the default. Only separate processes run in parallel.
- Six tests take over 1 s each: 1.91, 1.26, 1.22, 1.11, 1.03, and 1.01 s.

### pytest

| Variant | Time (pytest-reported) |
|---|---|
| Serial, default markers (what `just check` runs) | 3.17 s |
| Serial, `-m "not live"` (adds the 4 `slow` tests) | 3.24 s |
| `-m "not live" -n auto` (14 workers) | 2.82 s |
| `-m "not live" -n 4` | 2.44 s |
| `-n auto` with coverage (the CI configuration) | 3.78 s |
| Collection only | 0.52 s |

Starting 14 xdist workers costs about as much as the tests themselves, so
parallelism adds little at this suite size. Per directory, serially:
`meta` 1.59 s (143 tests), `test_guard.py` 0.36 s (11), `web` 0.27 s (55),
`core` 0.21 s (110), `cli` 0.10 s (95).

### Git hooks (lefthook, measured over all files)

| Hook | Total | Slowest command |
|---|---|---|
| pre-commit | 0.94 s | `large-files` 0.94 s and `taplo` 0.76 s over all files (a typical commit stages only a few); all others ≤ 0.28 s |
| pre-push | 6.28 s | `press verify` 6.28 s; `openapi-snapshot` 0.66 s; all others ≤ 0.34 s |

### Prototype results (throwaway clone, not committed)

| Change | `just check` |
|---|---|
| Baseline | 15.1–20.9 s |
| R1: `[parallel]` on `check` | 11.7 s (now bound by `test-release`) |
| R1 with a cold `.venv` (ten `uv run` calls start at once) | 11.9 s, passed; the collected test count was not recorded, so the web tests may have been skipped (see R1) |
| R1 + R2: also run the bun test files as parallel processes | 8.3 s (now bound by `release_runner.test.js`) |
| R1 + R2 + R3: also split `release_runner.test.js` into about 3 files | **about 4 s (estimate, not measured)** |

## CI

### PR critical path in `ci.yml` (p50, seconds after the run starts)

| Milestone | `pull_request` (n=20) | `merge_group` (n=6) | `push` (n=4) |
|---|---|---|---|
| `changes` done | 12 | 12 | 12 |
| All non-test jobs done | 32 | 33 | 30 |
| Slowest test leg done | 57 | 58 | 56 |
| `ci-ok` done | **66** | **68** | **65** |

The slowest leg is macOS or Windows in every run sampled. Their queue time
(p50 26 s for macOS and 17 s for Windows, against 6 s for Ubuntu) is most of
the gap. Everything else finishes by about 32 s.

### Every workflow

"PR path" means the workflow runs on `pull_request`. "Required" means a
failure blocks merging.

| Workflow | PR path | Required | Wall p50 / p90 | Notes |
|---|---|---|---|---|
| `bootstrap-acceptance.yml` | yes (path-filtered) | no | 96 / 103 s | sets time-to-all-green |
| `ci.yml` | yes | `ci-ok` | 66 / 75 s | sets time-to-mergeable |
| `codeql.yml` | yes | `code_scanning` rule | 52 / 57 s | the floor once `ci.yml` is faster |
| `claude-code-review.yml` | yes | no | 38 / 46 s | |
| `lint.yml` | yes | 5 jobs | 26 / 30 s | |
| `publish-container.yml` | yes | no | 21 / 22 s | |
| `api-contract.yml` | yes | no | 17 / 26 s | |
| `press-verify.yml` | yes | yes | 17 / 19 s | |
| `commitlint.yml` | yes | `commitlint (humans)` | 15 / 17 s | |
| `secret-scan.yml` | yes | no | 15 / 17 s | |
| `dependency-review.yml` | yes | no | 14 / 15 s | |
| `difftree-pr-comment.yml` | yes | no | 14 / 93 s | p90 outlier |
| `large-file-guard.yml` | yes | no | 12 / 13 s | |
| `template-receipt-guard.yml` | yes | no | 7 / 12 s | |
| `canary.yml` | schedule | — | 27 / 31 s | |
| `dep-audit.yml` | schedule | — | 338 / 632 s | Sphinx linkcheck, off the PR path |
| `audit-triage`, `claude`, `publish`, `release-please`, `update-contributors`, `manual-pr-security-scan` | no | — | not measured | triggered by push, tag, comment, schedule, or dispatch |

### `ci.yml` jobs (p50 duration / p50 queue)

| Job | Duration | Queue | Longest step |
|---|---|---|---|
| test (windows / py3.13) | 23 s | 17 s | Run tests 10 s |
| test (ubuntu / py3.13) | 19 s | 6 s | Run tests with coverage 8 s |
| test (macos / py3.13) | 17 s | 26 s | Run tests 8 s |
| test (ubuntu / py3.14) | 16 s | 6 s | Run tests 7 s |
| release-generation | 14 s | 6 s | bun test 7 s |
| test-otel | 13 s | 6 s | pytest 5 s |
| docs | 11 s | 6 s | Sphinx 2 s |
| build-smoke, lint, import-boundaries, toml-format-check, typecheck, shellcheck | 6–10 s | 6–7 s | setup-dominated |
| changes, ci-ok | 5 s, 4 s | 6 s | |

About 6 s of every job is fixed cost: setting up the job, checkout, and
`uv sync`.

### Inside `bootstrap-acceptance`

Across the 12 sampled runs, the live test step took 55–89 s (p50 79 s), and
the job took 70–103 s. One typical PR run's log (a 99 s job with a 78.3 s
live step) accounts for all 32 commands the test starts. Each command is
timed until the next one starts:

| Command inside the live test | Time |
|---|---|
| `just check` (in the generated project) | 45.2 s |
| `press rebrand` (preview, then apply) | 3.3 s + 12.5 s |
| `press verify` | 4.0 s |
| `sphinx-build` | 3.9 s |
| `git commit` | 1.7 s |
| `bun -e` (release preview) | 1.6 s |
| `harborctl --version` | 1.4 s |
| `just setup` | 0.5 s |
| the other 23 git, uv, and bun commands | 1.6 s together |
| pytest startup before the first command | 1.7 s |

The fastest run (a scheduled run with a 55 s step) shows the same shape:
`just check` took 32.9 s of it. The inner `just check` is the same serial gate
as the local one, so R1–R3 apply to it directly. The log does not split the
45 s further.

### Merge queue

Every merged PR runs `ci.yml` at least three times: on each PR push, in the
merge queue (`merge_group`), and again on `push` to `main`. All 13 sampled
`push` runs matched the commit of an earlier `merge_group` run. From the
start of the `merge_group` run to the start of the `push` run took a median
of 87 s (range 77–169 s). That is the queue's own cost on top of PR review.
The proposal does not change it.

## Recommendations, item by item

Effect types: **L** = local loop; **M** = PR time-to-mergeable; **G** = PR
time-to-all-green; **$** = runner minutes only, with no wall-clock change.

| ID | Item | Today | Verdict | Change | Effect | Estimated saving |
|---|---|---|---|---|---|---|
| R1 | `just check` dependency order | serial | **change** | Add `[parallel]` to `check` (needs just ≥ 1.42.0). First make the `test` recipe install the web extra itself (`uv run --extra web pytest`, as `typecheck` already does). On a cold `.venv`, plain `uv run pytest` collects 359 tests because `tests/web/conftest.py` skips the 55 web tests without `fastapi`; under `[parallel]` the count would depend on whether `typecheck` installed the extra first | L, G | measured −3 to −9 s locally |
| R2 | `test-release` recipe | 1 process | **change** | Run each `tests/release/*.test.js` as its own process and fail if any fails. Keep the CI step string `bun test tests/release`, which `tests/meta/test_release_generation.py` asserts | L, G | measured −3.4 s |
| R3 | `release_runner.test.js` | 8.1 s, 9 tests | **change** | Split into about 3 files of similar duration; no test logic changes | L, G | about −4 s (estimate) |
| R4 | macOS and Windows test legs | every PR event | **declined by owner** | Run them on `merge_group` and `push` only. A job-level `if` cannot read `matrix`, so build the matrix from the event (for example `fromJSON` over an include list). `ci-ok` stays required in the merge queue, so they still gate `main` | M, $ | about −14 s to mergeable (estimate; CodeQL then sets the floor) |
| R5 | git spawns in release tests | 1,625 per run | optional | Build the fixture histories once per file and copy them, instead of replaying commits in every test | L, G | unknown; measure after R3 |
| R6 | CI pytest `-n auto` | 7–10 s steps | measure | Compare `-n 2` and serial against `-n auto` on 4-vCPU runners | M (only after R4) | 0–3 s (estimate) |
| R7 | bun pin 1.3.5 | no `--parallel` flag | optional | A later bump could replace R2's shell loop with `bun test --parallel` | — | none by itself |
| R8 | pre-push `press verify` | 6.3 s | keep | It is the required `press-verify` check run locally; dropping it moves failures to CI | — | — |
| R9 | `changes` job before the test jobs | +12 s | keep | A workflow-level `paths-ignore` would leave the required `ci-ok` unreported on docs-only PRs | — | — |
| R10 | `lint.yml`: 6 jobs of about 9 s | parallel | keep | Merging them saves runner minutes but renames 5 required checks | $ | — |
| R11 | `ci.yml` on `push` to `main` | repeats the merge-group run | keep | Codecov needs the `main` upload as its comparison baseline | $ | — |
| R12 | `test-otel` | 13 s | keep | It covers the 3 OpenTelemetry tests that every other leg skips | — | — |
| R13 | `docs`, `build-smoke`, `typecheck`, `import-boundaries`, `toml-format-check`, `shellcheck`, `lint` | ≤ 11 s, off the critical path | keep | — | — | — |
| R14 | `bootstrap-acceptance` | 93 s p50, path-filtered, not required | keep, improved by R1–R3 | Its failures do not block merges; changing that is out of scope here | G | about −25 s (estimate: the inner 45 s `just check` falling to about 20 s) |
| R15 | `codeql.yml` | 52 s | keep | Required by the ruleset | — | — |

### R4 trade-off

- **For:** time-to-mergeable drops from about 66 s to about 52 s, and each PR
  push saves two of the slowest-queued runners.
- **Against:** a macOS-only or Windows-only failure would first appear in the
  merge queue, not on the PR. The queue would then eject the PR.
- **Failure history:** of the last 40 failed `ci.yml` runs, none failed on
  macOS or Windows alone. 2 failed on every test leg, 1 failed in
  `release-generation`, and in the other 37 no job concluded `failure`; those
  runs failed for other reasons, such as cancellation.
- **Recommendation:** adopt it. Platform-specific code is small: 3 PowerShell
  tests run only on Windows, and the 11 `scripts/guard.sh` tests skip there.
  Every change still passes all three operating systems in the merge queue
  before it reaches `main`.
- **Decision (2026-11-22):** declined. The full matrix stays on PRs.

## Test value review

Scope: whether any test should be removed or retiered **for time**. This is
not a full coverage-quality audit.

- **No pytest test is worth removing for time.** The suite costs 3.2 s. The
  costliest file, `tests/meta/test_audit_triage.py`, has 67 tests in 0.83 s;
  its parametrized subprocess cases cover shell-quoting edge cases.
- **The `slow` marker is mislabeled.** `pyproject.toml` defines it as "takes
  >1s". Its only users, the 4 schemathesis cases in
  `tests/web/test_contract.py`, take 0.6 s together. CI runs them already
  (`-m "not live"`). Unmarking them would add about 0.6 s to the local run and
  bring local behavior in line with CI. This is optional and does not affect
  speed.
- **The `live` test** (`tests/bootstrap/test_template_press.py`) is the only
  end-to-end proof that a generated project works. Keep it.
- **No unintended duplicate coverage was found.** `test-otel` reruns
  `tests/web` deliberately, with the `otel` extra installed.
  `openapi-snapshot` appears both in pre-push and in pytest because pre-push
  does not run pytest.

## Side findings (environment, not code)

1. The main checkout's `origin` still named the old owner
   (`https://github.com/smorin/py-launch-blueprint.git`). press's
   `source-config` expects `smorinlabs`, so `press verify` exited 2 there and
   the pre-push hook failed in every worktree. GitHub redirects the old URL,
   so ordinary git operations still worked. Fixed during this analysis with
   `git remote set-url`; any other clone made before the move has the same
   problem.
2. The main checkout has no `node_modules/`, so `just check` stops at
   `test-release` after about 3 s. `just setup` fixes this.
3. Locally the `live` test fails at `bun.lock` regeneration
   (`scripts/regen-bun-lock.sh` exits 1). The likely cause is installed bun
   1.4.5 against the pinned 1.3.5; this was not verified.

## Proposed implementation phases

These are not yet in `PROJECTS.md`. After approval, `project-add` can reserve
the IDs.

1. **Phase A, local gate (R1, R2, R3).** One PR. Verify by timing
   `just check` before and after over 3 runs, and by confirming that a
   deliberately failing bun file and a failing pytest test each still fail
   the gate under `[parallel]`. On a cold `.venv`, confirm that pytest
   collects 414 tests (default markers), so skipped web tests are visible.
2. **Phase B, CI matrix (R4).** Declined by the owner; not planned.
3. **Phase C, optional (R5, R6, R7).** Only if Phase A leaves the gate above
   about 5 s.

## Risks

- **`[parallel]` output interleaves.** When the gate fails, the failing
  recipe's output mixes with the others. Each recipe already prints a
  heading, and `just` reports which recipe failed.
- **just version floor.** `[parallel]` needs just ≥ 1.42.0 (released
  2025-07-13). `make bootstrap`, `mise.toml` (`just = "latest"`), and
  `extractions/setup-just` install the latest release. `.flox` does not pin a
  version and has no lock file, so its version was not verified. A
  contributor with an older just gets a parse error that names the attribute.
- **Parallel `uv run` on a cold `.venv`.** uv serializes environment syncs
  with a lock. The cold-`.venv` prototype passed in 11.9 s.

## Appendix: per-test timings

### A. pytest, per file (serial, default markers, one local run)

| File | Tests | Skipped | Time | Verdict |
|---|---|---|---|---|
| `tests/meta/test_audit_triage.py` | 67 | 0 | 0.83 s | keep |
| `tests/meta/test_bun_regeneration.py` | 8 | 3 | 0.44 s | keep |
| `tests/test_guard.py` | 11 | 0 | 0.36 s | keep |
| `tests/web/test_app.py` | 25 | 0 | 0.20 s | keep |
| `tests/core/test_properties.py` | 2 | 0 | 0.18 s | keep |
| `tests/meta/test_reset_release_history.py` | 8 | 0 | 0.17 s | keep |
| `tests/cli/test_pylb.py` | 58 | 0 | 0.07 s | keep |
| `tests/web/test_logging.py` | 13 | 0 | 0.04 s | keep |
| `tests/meta/test_release_generation.py` | 4 | 0 | 0.04 s | keep |
| `tests/meta/test_contributors_state.py` | 1 | 0 | 0.03 s | keep |
| `tests/meta/test_version_consistency.py` | 4 | 0 | 0.02 s | keep |
| `tests/meta/test_claude_review_workflow.py` | 2 | 0 | 0.02 s | keep |
| `tests/cli/test_output.py` | 26 | 0 | 0.02 s | keep |
| `tests/meta/test_justfile.py` | 1 | 0 | 0.02 s | keep |
| `tests/web/test_idempotency.py` | 8 | 0 | 0.02 s | keep |
| `tests/meta/test_publish_container.py` | 36 | 0 | 0.01 s | keep |
| `tests/cli/test_help_snapshots.py` | 11 | 0 | 0.01 s | keep |
| `tests/core/test_logging.py` | 14 | 2 | 0.01 s | keep |
| `tests/core/test_core.py` | 27 | 0 | 0.01 s | keep |
| `tests/core/test_projects_repository_contract.py` | 16 | 0 | 0.01 s | keep |
| `tests/core/test_py_api_repository.py` | 25 | 0 | 0.01 s | keep |
| `tests/web/test_openapi_snapshot.py` | 1 | 0 | 0.01 s | keep |
| `tests/web/test_versioning.py` | 2 | 0 | 0.00 s | keep |
| `tests/core/test_paths.py` | 8 | 0 | 0.00 s | keep |
| `tests/meta/test_codex_astral_plugin.py` | 4 | 0 | 0.00 s | keep |
| `tests/meta/test_contributors_workflow.py` | 3 | 0 | 0.00 s | keep |
| `tests/core/test_format.py` | 10 | 0 | 0.00 s | keep |
| `tests/core/test_projects_service.py` | 8 | 0 | 0.00 s | keep |
| `tests/meta/test_bootstrap_skill.py` | 1 | 0 | 0.00 s | keep |
| `tests/meta/test_contributors_render.py` | 1 | 0 | 0.00 s | keep |
| `tests/meta/test_security_workflow_visibility.py` | 3 | 0 | 0.00 s | keep |
| `tests/web/test_settings.py` | 4 | 0 | 0.00 s | keep |
| `tests/web/test_telemetry.py` | 2 | 1 | 0.00 s | keep |
| **Total** | **414** | | **2.52 s** | |

Not in this run: the 4 `slow` cases in `tests/web/test_contract.py` (0.59 s together, run by CI) and the `live` test in `tests/bootstrap/test_template_press.py` (55–89 s in CI).

### B. pytest, 25 slowest tests

| Time | Test |
|---|---|
| 0.16 s | `tests/meta/test_audit_triage.py::test_create_pr_uses_rest_and_preserves_fields[owner/repository]` |
| 0.15 s | `tests/core/test_properties.py::test_config_write_read_round_trips` |
| 0.14 s | `tests/meta/test_bun_regeneration.py::test_bun_installer_accepts_pin_line_endings[\n]` |
| 0.13 s | `tests/meta/test_bun_regeneration.py::test_regeneration_checks_bun_before_replacing_lock[1.3.5-shell]` |
| 0.11 s | `tests/meta/test_bun_regeneration.py::test_regeneration_checks_bun_before_replacing_lock[0.0.0-shell]` |
| 0.08 s | `tests/web/test_app.py::test_rate_limit_429_problem` |
| 0.08 s | `tests/meta/test_audit_triage.py::test_create_pr_requires_a_positive_number[417\n418]` |
| 0.08 s | `tests/meta/test_audit_triage.py::test_create_pr_propagates_api_failure[create-2]` |
| 0.08 s | `tests/meta/test_audit_triage.py::test_create_pr_uses_rest_and_preserves_fields[owner/repo "quoted"\\...` |
| 0.08 s | `tests/meta/test_audit_triage.py::test_create_pr_requires_a_positive_number[0]` |
| 0.07 s | `tests/meta/test_audit_triage.py::test_create_pr_requires_a_positive_number[abc]` |
| 0.07 s | `tests/meta/test_audit_triage.py::test_create_pr_requires_a_positive_number[-1]` |
| 0.07 s | `tests/meta/test_audit_triage.py::test_create_pr_requires_a_positive_number[null]` |
| 0.06 s | `tests/meta/test_bun_regeneration.py::test_bun_installer_accepts_pin_line_endings[\r\n]` |
| 0.06 s | `tests/meta/test_audit_triage.py::test_create_pr_propagates_api_failure[read-1]` |
| 0.04 s | `tests/test_guard.py::test_fork_origin_does_not_silence` |
| 0.04 s | `tests/test_guard.py::test_canonical_origin_silences[https://github.com/smorinlabs/py-lau...` |
| 0.04 s | `tests/test_guard.py::test_canonical_origin_silences[https://github.com/smorin/py-launch-...` |
| 0.04 s | `tests/test_guard.py::test_canonical_origin_silences[git@github.com:smorinlabs/py-launch-...` |
| 0.04 s | `tests/core/test_properties.py::test_project_survives_json_round_trip` |
| 0.03 s | `tests/meta/test_reset_release_history.py::test_reset_preserves_release_settings_and_is_idempotent[False]` |
| 0.03 s | `tests/meta/test_reset_release_history.py::test_reset_preserves_release_settings_and_is_idempotent[True]` |
| 0.03 s | `tests/test_guard.py::test_warn_banners_but_exits_zero` |
| 0.03 s | `tests/test_guard.py::test_unrelated_press_dir_does_not_silence` |
| 0.03 s | `tests/test_guard.py::test_legacy_marker_no_longer_silences` |

All other tests take under 0.03 s each.

### C. bun release tests, per test (one local run, bun 1.4.5)

| File | Time | Test |
|---|---|---|
| `release_commits.test.js` | 0.70 s | empty ranges produce no release; upstream revert and release-trailer behavior is retained |
| `release_commits.test.js` | 0.60 s | scoped dependency rules stay visible while general chores and builds stay hidden |
| `release_commits.test.js` | 0.40 s | first release uses local bootstrap or all local history |
| `release_commits.test.js` | 0.37 s | the corrected generator includes older branch changes and omits merge bodies |
| `release_commits.test.js` | 0.37 s | upstream discovery respects its limit while final selection remains complete |
| `release_commits.test.js` | 0.36 s | commit identity, multiline messages, and unusual filenames survive selection |
| `release_commits.test.js` | 0.33 s | path exclusions apply to the corrected set, retaining mixed-path changes |
| `release_commits.test.js` | 0.29 s | explicit cutoffs take priority and annotated tags resolve to commits |
| `release_commits.test.js` | 0.19 s | missing and nonancestor cutoffs, invalid sources, and multiple packages fail |
| `release_runner.test.js` | 1.85 s | release-only merge publishes, reloads the manifest, and proposes no extra release |
| `release_runner.test.js` | 1.21 s | snapshot reads stay pinned and stale sources are refused before every write |
| `release_runner.test.js` | 1.16 s | preview uses the pending release as the baseline for later changes without publishing it |
| `release_runner.test.js` | 1.09 s | existing PR keeps its number and branch; unchanged retries perform no writes |
| `release_runner.test.js` | 0.99 s | historical preview ignores releases, tags, and merged PRs outside its source ancestry |
| `release_runner.test.js` | 0.98 s | preview repeats exactly with no writes and renders all version files together |
| `release_runner.test.js` | 0.27 s | invalid cutoff and API failures stop the lifecycle without a new PR |
| `release_runner.test.js` | 0.20 s | workflow entry point rejects invalid input and missing write credentials before API access |
| `release_runner.test.js` | 0.07 s | oversized release notes obey dry-run and stale-source guards before creating a branch |
| `reproduction.test.js` | 0.28 s | upstream stops before older branch changes that landed after the release |
| `reproduction.test.js` | 0.00 s | upstream expands a standard merge body into a second change |
