# Last-run workflow wall-clock totals

This appendix records a single-run remeasurement of the Stage 3 experiment
cells using literal GitHub Actions workflow wall time. It is the apples-to-
apples check for `flox-baked` because the total includes container image
pull/start, setup, checks, post steps, and all overhead GitHub counts in
`run_duration_ms`. Each row is n=1 (the last successful run per cell in the
cleaned `run-ids-stage3-all.json`); the aggregate medians in `REPORT.md`
remain the primary evidence.

## Measurement

- Source run-id artifact: `experiment/results/run-ids-stage3-all.json` (cross-OS-cleaned)
- Timing: GitHub REST `actions/runs/{id}/timing` -> `run_duration_ms / 1000`
- Rows fetched: 38 workflow runs, covering 236 GitHub jobs
- Branch: `experiment/flox-ci-timing-perf-analysis`

## Flox baked vs consolidated variants

`flox-baked` is Linux-only. On ubuntu, the last-run totals land on the same
floor as the other consolidated flox variants.

| side | ubuntu cold | cold vs flox-consolidated | ubuntu warm | warm vs flox-consolidated |
| --- | ---: | ---: | ---: | ---: |
| flox-consolidated | 71s | baseline | 63s | baseline |
| flox-nocache-consolidated | 67s | -4s | 68s | +5s |
| flox-noaction-consolidated | 69s | -2s | 66s | +3s |
| flox-baked | 68s | -3s | 64s | +1s |

Interpretation: pre-baking relocates the flox cost into container image
pull/start, but the total workflow time is still effectively the same as
normal flox consolidated execution.

## Last successful run per cell

| side | os | cache | run | total | vs traditional same os/cache | jobs | longest job |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| traditional | ubuntu-latest | cold | 26987506666 | 16s | baseline | 10 | checks / gitleaks 12s |
| mise-mirror | ubuntu-latest | cold | 26967674536 | 30s | 1.9x / +88% | 10 | checks / taplo 23s |
| mise-consolidated | ubuntu-latest | cold | 26987790112 | 24s | 1.5x / +50% | 2 | hygiene 19s |
| flox-mirror | ubuntu-latest | cold | 26966361270 | 69s | 4.3x / +331% | 10 | checks / ty 58s |
| flox-consolidated | ubuntu-latest | cold | 26967105937 | 71s | 4.4x / +344% | 2 | pytest 61s |
| flox-nocache-mirror | ubuntu-latest | cold | 26969309977 | 63s | 3.9x / +294% | 10 | checks / commitlint 57s |
| flox-nocache-consolidated | ubuntu-latest | cold | 26969989179 | 67s | 4.2x / +319% | 2 | pytest 59s |
| flox-noaction-mirror | ubuntu-latest | cold | 26987664615 | 71s | 4.4x / +344% | 10 | checks / commitlint 65s |
| flox-noaction-consolidated | ubuntu-latest | cold | 26987541491 | 69s | 4.3x / +331% | 2 | hygiene 63s |
| flox-baked | ubuntu-latest | cold | 26972884364 | 68s | 4.2x / +325% | 2 | hygiene 60s |
| traditional | ubuntu-latest | warm | 26987529314 | 20s | baseline | 10 | checks / pytest 14s |
| mise-mirror | ubuntu-latest | warm | 26967928183 | 21s | 1.1x / +5% | 10 | checks / commitlint 14s |
| mise-consolidated | ubuntu-latest | warm | 26987817687 | 19s | 0.9x / -5% | 2 | pytest 14s |
| flox-mirror | ubuntu-latest | warm | 26966771450 | 72s | 3.6x / +260% | 10 | checks / ty 62s |
| flox-consolidated | ubuntu-latest | warm | 26967485964 | 63s | 3.1x / +215% | 2 | pytest 57s |
| flox-nocache-mirror | ubuntu-latest | warm | 26969680352 | 66s | 3.3x / +230% | 10 | checks / pytest 60s |
| flox-nocache-consolidated | ubuntu-latest | warm | 26970353345 | 68s | 3.4x / +240% | 2 | pytest 59s |
| flox-noaction-mirror | ubuntu-latest | warm | 26987747149 | 75s | 3.8x / +275% | 10 | checks / ruff-check 69s |
| flox-noaction-consolidated | ubuntu-latest | warm | 26987623372 | 66s | 3.3x / +230% | 2 | hygiene 62s |
| flox-baked | ubuntu-latest | warm | 26973242820 | 64s | 3.2x / +220% | 2 | hygiene 56s |
| traditional | macos-latest | cold | 26965852444 | 125s | baseline | 10 | checks / gitleaks 114s |
| mise-mirror | macos-latest | cold | 26966469523 | 65s | 0.5x / -48% | 10 | checks / ty 28s |
| mise-consolidated | macos-latest | cold | 26966997054 | 39s | 0.3x / -69% | 2 | pytest 26s |
| flox-mirror | macos-latest | cold | 26987807812 | 385s | 3.1x / +208% | 10 | checks / commitlint 227s |
| flox-consolidated | macos-latest | cold | 26987514490 | 169s | 1.4x / +35% | 2 | pytest 164s |
| flox-nocache-mirror | macos-latest | cold | 26988425959 | 365s | 2.9x / +192% | 10 | checks / ruff-format 217s |
| flox-nocache-consolidated | macos-latest | cold | 26974478895 | 200s | 1.6x / +60% | 2 | hygiene 193s |
| flox-noaction-mirror | macos-latest | cold | 26977001538 | 366s | 2.9x / +193% | 10 | checks / bandit 182s |
| flox-noaction-consolidated | macos-latest | cold | 26979989174 | 196s | 1.6x / +57% | 2 | pytest 189s |
| traditional | macos-latest | warm | 26966181424 | 50s | baseline | 10 | checks / bandit 24s |
| mise-mirror | macos-latest | warm | 26966782870 | 55s | 1.1x / +10% | 10 | checks / ty 28s |
| mise-consolidated | macos-latest | warm | 26967200432 | 25s | 0.5x / -50% | 2 | pytest 17s |
| flox-mirror | macos-latest | warm | 26988228917 | 358s | 7.2x / +616% | 10 | checks / yamllint 203s |
| flox-consolidated | macos-latest | warm | 26987705158 | 185s | 3.7x / +270% | 2 | hygiene 179s |
| flox-nocache-mirror | macos-latest | warm | 26988804596 | 372s | 7.4x / +644% | 10 | checks / commitlint 190s |
| flox-nocache-consolidated | macos-latest | warm | 26975505575 | 211s | 4.2x / +322% | 2 | pytest 205s |
| flox-noaction-mirror | macos-latest | warm | 26978965925 | 408s | 8.2x / +716% | 10 | checks / ruff-format 200s |
| flox-noaction-consolidated | macos-latest | warm | 26980898703 | 183s | 3.7x / +266% | 2 | hygiene 174s |

## Reading notes

- Point-in-time appendix; the aggregate table in `REPORT.md` is the primary evidence.
- macOS traditional baselines carry high runner-queue variance, so same-cell
  macOS ratios against them are noisy.
- The workflow total is the right metric for `flox-baked` vs normal flox because
  GitHub includes container initialization in the run wall clock.
