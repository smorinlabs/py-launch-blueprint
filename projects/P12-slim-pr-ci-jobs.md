# P12 — Slim PR CI job count

Cut the number of GitHub Actions jobs each pull request starts, without
changing any required check. Private repositories generated from this
template bill every job as at least one minute, so job count drives cost
more than runtime does. Wall-clock is already short (about 1–2 minutes).

**References**

- **Trunk:** [PROJECTS.md](../PROJECTS.md)

**Status:** `[~]` in progress.

### Scope

- `release-generation` runs only when release tooling changes.
- Release-please PRs whose diff is only the version bump and changelog skip
  the test matrix, `test-otel`, `typecheck`, `release-generation` and
  `bootstrap-acceptance`. `build-smoke` still runs because the version is a
  packaging input.
- Merge the non-required static jobs inside `ci.yml`: `lint`,
  `toml-format-check`, `shellcheck` and `docs` become one `lint` job;
  `typecheck` and `import-boundaries` become one `typecheck` job. `ci-ok`
  still aggregates everything.
- Add PR-only `concurrency` (cancel superseded PR runs; main pushes group
  per commit and never cancel) to the PR-triggered workflows that lack it.

### Out of scope

- The test matrix: already 4 cells by design (3 OS on Python 3.13 plus
  Linux on 3.14). The owner declined moving macOS and Windows off the PR
  path in P11.
- CodeQL path filtering: the "CodeQL & PR Enforcement" ruleset has a
  `code_scanning` rule, which waits for a CodeQL analysis on every PR. A PR
  that skips CodeQL would never become mergeable.
- Folding the required `lint.yml` jobs (`actionlint`, `bandit`, `codespell`,
  `editorconfig-check`, `yamllint`): branch protection requires each by
  name, so merging them needs a protection change by the owner.

### Tests & Tasks

- [x] [P12-TS01] The `changes` detector, run in a temporary git repository, classifies push, docs-only, code, release-tooling, genuine release-please, and spoofed release-please diffs correctly.
- [x] [P12-TS02] `ci.yml` shape: `ci-ok` needs every other job; `release-generation` keys on `release_tooling`; `build-smoke` also runs on the release fast path; merged jobs keep every tool step reporting.
- [x] [P12-TS03] Every PR-triggered workflow that gained `concurrency` cancels only `pull_request` runs.
- [x] [P12-T01] Extend the `changes` job with `release` and `release_tooling` outputs.
- [x] [P12-T02] Merge the static jobs in `ci.yml` and update `ci-ok`.
- [x] [P12-T03] Skip `bootstrap-acceptance` on release-please PRs.
- [x] [P12-T04] Add PR-only concurrency to `press-verify`, `template-receipt-guard`, `claude-code-review`, `dependency-review` and `container-check`.
- [x] [P12-T05] Update the CI docs and `AGENTS.md` for the merged job names.
- [ ] [P12-T06] Open the PR, pass CI, and resolve review threads.

### Deliverable

A code PR starts 5 fewer `ci.yml` jobs; a docs-only PR starts 3 fewer; a
release-please PR skips the test matrix and acceptance run.

### Automated Verification

- `tests/meta/test_ci_change_detection.py` and
  `tests/meta/test_release_generation.py` pass.
- `just check` and `uv run --locked press verify` pass.

### Manual Verification

- Job counts on this PR compared with recent PR runs (GitHub REST).
