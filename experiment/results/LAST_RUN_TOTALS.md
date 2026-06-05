# Last-run workflow wall-clock totals

This appendix records a single-run remeasurement of the Stage 3 experiment cells
using literal GitHub Actions workflow wall time. It is intended as an
apples-to-apples check for `flox-baked` because the total includes container
image pull/start, setup, checks, post steps, and all other workflow overhead that
GitHub includes in `run_duration_ms`.

This is not a replacement for the aggregate medians in `REPORT.md`: each row
below is `n=1`, taking the last successful run ID recorded for that
`side|os|cache` cell in `run-ids-stage3-all.json`.

## Measurement

- Source run-id artifact: `experiment/results/run-ids-stage3-all.json`
- Timing source: GitHub REST API `actions/runs/{run_id}/timing`
- Total metric: `run_duration_ms / 1000`
- Job verification source: GitHub REST API `actions/runs/{run_id}/jobs`
- Rows fetched: 36 workflow runs, covering 216 GitHub jobs
- Branch: `experiment/flox-ci-timing-perf-analysis`
- Repository: `smorinlabs/py-launch-blueprint`

The committed analyzer uses the same total-run metric for the main report:
`experiment/analyze.py` fetches the timing endpoint, and
`experiment/bench/collect.py` stores `run_duration_ms` as `RunTiming.total_seconds`.

## Flox baked vs consolidated variants

`flox-baked` is Linux-only. On ubuntu, the last-run total workflow timings land
on the same floor as the other consolidated flox variants.

| side | ubuntu cold | cold vs flox-consolidated | ubuntu warm | warm vs flox-consolidated |
| --- | ---: | ---: | ---: | ---: |
| flox-consolidated | 71s | baseline | 63s | baseline |
| flox-nocache-consolidated | 67s | -4s | 68s | +5s |
| flox-noaction-consolidated | 66s | -5s | 71s | +8s |
| flox-baked | 68s | -3s | 64s | +1s |

Interpretation: pre-baking relocates the flox cost into container image
pull/start, but the total workflow time is still effectively the same as normal
flox consolidated execution.

## Last successful run per cell

| side | os | cache | run | total | vs traditional same os/cache | jobs | longest job |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| traditional | ubuntu-latest | cold | 26965764951 | 22s | baseline | 10 | checks / pytest 11s |
| mise-mirror | ubuntu-latest | cold | 26967674536 | 30s | 1.4x / +36% | 10 | checks / taplo 23s |
| mise-consolidated | ubuntu-latest | cold | 26967950674 | 25s | 1.1x / +14% | 2 | hygiene 19s |
| flox-mirror | ubuntu-latest | cold | 26966361270 | 69s | 3.1x / +214% | 10 | checks / ty 58s |
| flox-consolidated | ubuntu-latest | cold | 26967105937 | 71s | 3.2x / +223% | 2 | pytest 61s |
| flox-nocache-mirror | ubuntu-latest | cold | 26969309977 | 63s | 2.9x / +186% | 10 | checks / commitlint 57s |
| flox-nocache-consolidated | ubuntu-latest | cold | 26969989179 | 67s | 3.0x / +205% | 2 | pytest 59s |
| flox-noaction-mirror | ubuntu-latest | cold | 26970542940 | 70s | 3.2x / +218% | 10 | checks / pytest 63s |
| flox-noaction-consolidated | ubuntu-latest | cold | 26972192616 | 66s | 3.0x / +200% | 2 | pytest 61s |
| flox-baked | ubuntu-latest | cold | 26972884364 | 68s | 3.1x / +209% | 2 | hygiene 60s |
| traditional | ubuntu-latest | warm | 26966046838 | 48s | baseline | 10 | checks / ty 18s |
| mise-mirror | ubuntu-latest | warm | 26967928183 | 21s | 0.4x / -56% | 10 | checks / commitlint 14s |
| mise-consolidated | ubuntu-latest | warm | 26969044685 | 23s | 0.5x / -52% | 2 | pytest 18s |
| flox-mirror | ubuntu-latest | warm | 26966771450 | 72s | 1.5x / +50% | 10 | checks / ty 62s |
| flox-consolidated | ubuntu-latest | warm | 26967485964 | 63s | 1.3x / +31% | 2 | pytest 57s |
| flox-nocache-mirror | ubuntu-latest | warm | 26969680352 | 66s | 1.4x / +38% | 10 | checks / pytest 60s |
| flox-nocache-consolidated | ubuntu-latest | warm | 26970353345 | 68s | 1.4x / +42% | 2 | pytest 59s |
| flox-noaction-consolidated | ubuntu-latest | warm | 26972580880 | 71s | 1.5x / +48% | 2 | pytest 65s |
| flox-baked | ubuntu-latest | warm | 26973242820 | 64s | 1.3x / +33% | 2 | hygiene 56s |
| traditional | macos-latest | cold | 26965852444 | 125s | baseline | 10 | checks / gitleaks 114s |
| mise-mirror | macos-latest | cold | 26966469523 | 65s | 0.5x / -48% | 10 | checks / ty 28s |
| mise-consolidated | macos-latest | cold | 26966997054 | 39s | 0.3x / -69% | 2 | pytest 26s |
| flox-mirror | macos-latest | cold | 26967607888 | 408s | 3.3x / +226% | 10 | checks / taplo 212s |
| flox-consolidated | macos-latest | cold | 26970083189 | 191s | 1.5x / +53% | 2 | pytest 185s |
| flox-nocache-consolidated | macos-latest | cold | 26974478895 | 200s | 1.6x / +60% | 2 | hygiene 193s |
| flox-noaction-mirror | macos-latest | cold | 26977001538 | 366s | 2.9x / +193% | 10 | checks / bandit 182s |
| flox-noaction-consolidated | macos-latest | cold | 26979989174 | 196s | 1.6x / +57% | 2 | pytest 189s |
| traditional | macos-latest | warm | 26966181424 | 50s | baseline | 10 | checks / bandit 24s |
| mise-mirror | macos-latest | warm | 26966782870 | 55s | 1.1x / +10% | 10 | checks / ty 28s |
| mise-consolidated | macos-latest | warm | 26967200432 | 25s | 0.5x / -50% | 2 | pytest 17s |
| flox-mirror | macos-latest | warm | 26968995243 | 426s | 8.5x / +752% | 10 | checks / taplo 228s |
| flox-consolidated | macos-latest | warm | 26970393461 | 202s | 4.0x / +304% | 2 | pytest 195s |
| flox-nocache-mirror | macos-latest | warm | 26973475939 | 381s | 7.6x / +662% | 10 | checks / commitlint 195s |
| flox-nocache-consolidated | macos-latest | warm | 26975505575 | 211s | 4.2x / +322% | 2 | pytest 205s |
| flox-noaction-mirror | macos-latest | warm | 26978965925 | 408s | 8.2x / +716% | 10 | checks / ruff-format 200s |
| flox-noaction-consolidated | macos-latest | warm | 26980898703 | 183s | 3.7x / +266% | 2 | hygiene 174s |

## Missing cells

These cells had no successful run IDs in `run-ids-stage3-all.json`, so they are
not present in the last-run table:

- `flox-nocache-mirror|macos-latest|cold`
- `flox-noaction-mirror|ubuntu-latest|warm`

## Reading notes

- Treat this file as a point-in-time appendix. The main statistical evidence is
  still the aggregate table in `REPORT.md`.
- The macOS traditional cold last run is a known noisy outlier at 125s, so the
  same-cell ratios against that baseline understate some macOS cold flox costs.
- The workflow total is the correct metric for comparing `flox-baked` to normal
  flox because GitHub includes container initialization in the run wall clock.
