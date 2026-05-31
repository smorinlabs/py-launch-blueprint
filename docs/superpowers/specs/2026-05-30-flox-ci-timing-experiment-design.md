# Flox vs. Traditional CI — timing experiment design

- Date: 2026-05-30
- Branch: `experiment/flox-ci-timing`
- Status: design (awaiting user review)
- Related: [ADR-12](../../adr/0012-flox-environment-management.md)

## Goal

Empirically measure whether provisioning this repo's CI toolchain via **Flox**
is faster or slower than the **traditional** per-tool installation, in GitHub
Actions — with real timing data, broken down by job and by OS, for both cold and
warm caches. The experiment **informs** the ADR-12 adoption decision; it does not
itself adopt Flox.

## Non-goals

- Not performing the ADR-12 deletions (retiring install scripts / gutting the
  Makefile). The branch is **additive** — both toolchains must coexist so the
  baseline and Flox sides can both run.
- Not changing what the checks *do*. The work (ruff/ty/pytest/… invocations) is
  held byte-identical across sides; only **provisioning** varies.
- Not measuring GitHub-native or release machinery (CodeQL, dependency-review,
  publish, release-please, etc.) — those aren't a toolchain-provisioning compare.

## Decisions (settled in brainstorming)

| Dimension | Decision |
| --- | --- |
| CI scope | Full developer-toolchain suite (~11 checks) |
| Metric | Total run wall-clock **and** per-job breakdown (plus setup-vs-work split where cheap) |
| Cache | Measure **both** cold and warm, reported separately |
| Repetition | **5 reps** per cell, driver-orchestrated, serial dispatch |
| Run location | This repo, branch `experiment/flox-ci-timing`; experiment workflows are `workflow_dispatch`-only (won't pollute normal CI) |
| Execution boundary | Build harness + validate on fixture data; **user triggers** the live 60 runs |
| Flox structure | **Both** a 1:1 mirror and a consolidated variant |
| OS | **Linux vs macOS as an explicit dimension** |
| Stats | min / max / avg / **median / stddev** |
| Output | Markdown report **+ a downloadable artifact with visuals (charts) and tables** |

## Experiment matrix

```
3 sides × 2 OS × 2 cache × 5 reps = 60 measured runs
  sides: traditional, flox-mirror, flox-consolidated
  OS:    ubuntu-latest, macos-latest
  cache: cold, warm
+ 6 warm-cache priming runs (1 per side × OS)
+ 6 correctness smoke runs (1 per side × OS, gate before timing)
```

**Cost note:** GitHub-hosted **macOS runners bill ~10× Linux**; half the runs are
macOS, so they dominate the minute bill. Accepted tradeoff for the OS signal.

**Controls:** Python pinned to 3.12 (the floor) — the 3.12/3.13 matrix is dropped
so OS is the clean second axis. Cold/warm separated by **cache key** (cold = unique
per-run key → guaranteed miss; warm = stable key, primed once) so cache state is
robust regardless of run timing.

## Measured checks (~11)

`ruff check`, `ruff format --check`, `ty check`, `pytest` + coverage,
`taplo check`, `codespell`, `yamllint`, `editorconfig-checker`, `bandit`,
`gitleaks`, `commitlint`.

## Architecture (Approach B — reusable workflow + provisioner input)

### Reusable checks workflow — `.github/workflows/_checks.yml`
`workflow_call` with inputs `provisioner: traditional|flox`, `os`, `cache:
cold|warm`. Defines the ~11 checks as jobs. Per job:

- `provisioner == traditional` → that job's existing installer (`setup-uv` +
  `uvx`, `setup-just`, or bun + `bunx`), then run the command bare.
- `provisioner == flox` → `./.github/actions/provision-flox` composite, then run
  the command under a `$RUN="flox activate -- "` prefix.

The **check command string is identical** across both branches — this is the
experimental control that guarantees only provisioning differs.

### Sides
- `trad-suite.yml` → calls `_checks.yml` with `provisioner: traditional`.
- `flox-mirror-suite.yml` → calls `_checks.yml` with `provisioner: flox`.
  (Identical job topology to traditional → clean per-job comparison.)
- `flox-consolidated.yml` → standalone; 2–3 jobs: one job activates the Flox env
  once and runs all fast hygiene checks sequentially; `pytest` stays its own job
  so parallelism on the long pole isn't lost. Reflects real-world Flox usage.

### Composite Flox provisioner — `.github/actions/provision-flox/`
Installs Flox branching on `runner.os` (Linux vs macOS install paths), and
restores/saves the Nix-store cache with a key derived from `manifest.lock` and
the `cache` input (unique-per-run for cold, stable for warm).

### Prerequisite — repo Flox environment
`.flox/env/manifest.toml` + `manifest.lock` committed on the branch, holding the
ADR-12 toolchain: `python312, uv, just, bun, lefthook, gitleaks, gh, taplo,
ruff, yamllint, codespell, editorconfig-checker, bandit, commitlint, gnumake`.

### Driver — `.github/workflows/experiment-driver.yml`
`workflow_dispatch` with inputs to **scope a slice** (e.g. one OS or one side per
invocation) so no single driver job approaches the 6h limit. Dispatches the
measured workflows serially via `gh`, spaces runs, tags them queryable, and on
completion uploads the results artifact.

### Analysis — `experiment/analyze.py`
uv PEP-723 shebang script (deps: `matplotlib`). Pulls **run / job / step**
timings via `gh api`; computes min/max/avg/median/stddev per cell. Emits:

- `experiment/results/results.json`, `results.csv` (raw + aggregated)
- `experiment/results/REPORT.md` — headline total-time table (side × OS × cache,
  Δ% vs traditional baseline) + per-job breakdown table
- Charts (PNG/SVG): (1) grouped bars of total time by side, grouped by OS,
  faceted cold/warm, stddev error bars; (2) box/strip plots of the 5 reps per
  cell (variance); (3) per-job small-multiples (job × side, per OS); (4) Δ%-vs-
  baseline per OS.

### Output artifact
Driver bundles `REPORT.md` + charts + raw data into a downloadable Actions
artifact via `upload-artifact`; the same is committed under `experiment/results/`.

## Validation gates (the "testable" requirement)

1. **Harness unit gate** — `analyze.py` runs against a **synthetic fixture
   dataset**; proves stats + every chart + `REPORT.md` render with zero Actions
   minutes. Demonstrates the output format before any live run.
2. **Correctness gate** — one smoke run per side × OS (6 runs); confirm all three
   sides are green and equivalent before timing.
3. **Full experiment** — the 60 measured runs (+6 warm priming), driven in slices.

## Deliverables

- `.flox/` environment (additive).
- `.github/workflows/_checks.yml`, `trad-suite.yml`, `flox-mirror-suite.yml`,
  `flox-consolidated.yml`, `experiment-driver.yml`.
- `.github/actions/provision-flox/action.yml`.
- `experiment/analyze.py` + `experiment/fixtures/` (synthetic dataset).
- `experiment/results/` (generated: report, charts, raw data).

## Open risks

- Flox-on-macOS-runner install/caching behavior is the least-certain piece;
  the correctness gate de-risks it before the timing run.
- Driver wall-clock for 60 serial runs is long; mitigated by slice-scoping inputs.
- macOS minute cost; accepted, but rep count could drop to 3 on macOS if needed.
