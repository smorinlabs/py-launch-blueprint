# Flox vs Traditional CI — timing results

Appendix: [last-run workflow wall-clock totals](LAST_RUN_TOTALS.md) records the final successful run per cell using GitHub's literal `run_duration_ms`, including the `flox-baked` container runs.

## Total run time (per side × os × cache)

| side | os | cache | n | min | max | avg | median | stddev | Δ% vs base |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| flox-consolidated | macos-latest | cold | 6 | 159.0 | 224.0 | 192.3 | 197.5 | 22.4 | +200.5% |
| flox-mirror | macos-latest | cold | 3 | 385.0 | 424.0 | 405.7 | 408.0 | 16.0 | +533.9% |
| flox-noaction-consolidated | macos-latest | cold | 5 | 181.0 | 196.0 | 191.6 | 193.0 | 5.5 | +199.4% |
| flox-noaction-mirror | macos-latest | cold | 5 | 336.0 | 424.0 | 368.0 | 366.0 | 30.2 | +475.0% |
| flox-nocache-consolidated | macos-latest | cold | 5 | 175.0 | 210.0 | 195.6 | 200.0 | 13.2 | +205.6% |
| flox-nocache-mirror | macos-latest | cold | 1 | 365.0 | 365.0 | 365.0 | 365.0 | 0.0 | +470.3% |
| mise-consolidated | macos-latest | cold | 5 | 34.0 | 42.0 | 39.4 | 41.0 | 2.9 | -38.4% |
| mise-mirror | macos-latest | cold | 4 | 64.0 | 79.0 | 68.8 | 66.0 | 6.0 | +7.4% |
| traditional | macos-latest | cold | 5 | 38.0 | 125.0 | 64.0 | 55.0 | 31.1 | — |
| flox-consolidated | macos-latest | warm | 2 | 185.0 | 202.0 | 193.5 | 193.5 | 8.5 | +294.9% |
| flox-mirror | macos-latest | warm | 3 | 358.0 | 426.0 | 389.3 | 384.0 | 28.0 | +694.6% |
| flox-noaction-consolidated | macos-latest | warm | 5 | 161.0 | 209.0 | 183.2 | 183.0 | 16.6 | +273.9% |
| flox-noaction-mirror | macos-latest | warm | 5 | 365.0 | 413.0 | 393.0 | 404.0 | 19.3 | +702.0% |
| flox-nocache-consolidated | macos-latest | warm | 5 | 188.0 | 216.0 | 200.8 | 199.0 | 11.1 | +309.8% |
| flox-nocache-mirror | macos-latest | warm | 6 | 342.0 | 404.0 | 382.5 | 388.5 | 21.2 | +680.6% |
| mise-consolidated | macos-latest | warm | 5 | 25.0 | 33.0 | 29.8 | 32.0 | 3.2 | -39.2% |
| mise-mirror | macos-latest | warm | 5 | 49.0 | 65.0 | 55.8 | 55.0 | 5.7 | +13.9% |
| traditional | macos-latest | warm | 5 | 45.0 | 55.0 | 49.0 | 48.0 | 3.4 | — |
| flox-baked | ubuntu-latest | cold | 5 | 58.0 | 74.0 | 65.8 | 66.0 | 5.3 | +170.4% |
| flox-consolidated | ubuntu-latest | cold | 5 | 65.0 | 72.0 | 69.0 | 70.0 | 2.6 | +183.6% |
| flox-mirror | ubuntu-latest | cold | 5 | 64.0 | 75.0 | 70.0 | 69.0 | 4.0 | +187.7% |
| flox-noaction-consolidated | ubuntu-latest | cold | 3 | 66.0 | 69.0 | 67.0 | 66.0 | 1.4 | +175.3% |
| flox-noaction-mirror | ubuntu-latest | cold | 4 | 69.0 | 71.0 | 70.2 | 70.5 | 0.8 | +188.7% |
| flox-nocache-consolidated | ubuntu-latest | cold | 5 | 63.0 | 69.0 | 65.6 | 65.0 | 2.2 | +169.6% |
| flox-nocache-mirror | ubuntu-latest | cold | 5 | 61.0 | 66.0 | 63.6 | 63.0 | 1.7 | +161.4% |
| mise-consolidated | ubuntu-latest | cold | 2 | 24.0 | 25.0 | 24.5 | 24.5 | 0.5 | +0.7% |
| mise-mirror | ubuntu-latest | cold | 5 | 29.0 | 32.0 | 30.2 | 30.0 | 1.2 | +24.1% |
| traditional | ubuntu-latest | cold | 6 | 16.0 | 38.0 | 24.3 | 22.0 | 7.5 | — |
| flox-baked | ubuntu-latest | warm | 5 | 59.0 | 71.0 | 62.8 | 60.0 | 4.4 | +173.0% |
| flox-consolidated | ubuntu-latest | warm | 5 | 63.0 | 66.0 | 64.4 | 64.0 | 1.0 | +180.0% |
| flox-mirror | ubuntu-latest | warm | 5 | 71.0 | 78.0 | 74.0 | 72.0 | 3.3 | +221.7% |
| flox-noaction-consolidated | ubuntu-latest | warm | 6 | 66.0 | 85.0 | 72.7 | 71.0 | 6.4 | +215.9% |
| flox-noaction-mirror | ubuntu-latest | warm | 1 | 75.0 | 75.0 | 75.0 | 75.0 | 0.0 | +226.1% |
| flox-nocache-consolidated | ubuntu-latest | warm | 5 | 61.0 | 68.0 | 63.2 | 62.0 | 2.6 | +174.8% |
| flox-nocache-mirror | ubuntu-latest | warm | 5 | 62.0 | 69.0 | 64.8 | 64.0 | 2.5 | +181.7% |
| mise-consolidated | ubuntu-latest | warm | 5 | 17.0 | 31.0 | 22.8 | 23.0 | 4.8 | -0.9% |
| mise-mirror | ubuntu-latest | warm | 5 | 17.0 | 115.0 | 44.6 | 26.0 | 36.4 | +93.9% |
| traditional | ubuntu-latest | warm | 3 | 20.0 | 29.0 | 23.0 | 20.0 | 4.2 | — |

## Provisioning (setup) vs work — per job

setup = the `provision` step (flox install/activate, or setup-uv/just/bun); work = the rest of the job. `total provisioning/run` = setup summed across all jobs in a run (the cumulative billable provisioning cost).

| side | os | cache | jobs | avg setup/job | avg work/job | setup % | total provisioning/run |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| flox-consolidated | macos-latest | cold | 2 | 156.6s | 15.2s | 91% | 313s |
| flox-mirror | macos-latest | cold | 10 | 163.8s | 10.2s | 94% | 1638s |
| flox-noaction-consolidated | macos-latest | cold | 2 | 150.6s | 14.9s | 91% | 301s |
| flox-noaction-mirror | macos-latest | cold | 10 | 152.0s | 9.5s | 94% | 1520s |
| flox-nocache-consolidated | macos-latest | cold | 2 | 166.0s | 16.1s | 91% | 332s |
| flox-nocache-mirror | macos-latest | cold | 10 | 150.7s | 9.0s | 94% | 1507s |
| mise-consolidated | macos-latest | cold | 2 | 13.9s | 13.3s | 51% | 28s |
| mise-mirror | macos-latest | cold | 10 | 13.7s | 8.5s | 62% | 137s |
| traditional | macos-latest | cold | 10 | 5.5s | 10.9s | 34% | 55s |
| flox-consolidated | macos-latest | warm | 2 | 165.5s | 15.8s | 91% | 331s |
| flox-mirror | macos-latest | warm | 10 | 161.3s | 9.8s | 94% | 1613s |
| flox-noaction-consolidated | macos-latest | warm | 2 | 146.4s | 13.8s | 91% | 293s |
| flox-noaction-mirror | macos-latest | warm | 10 | 157.7s | 9.8s | 94% | 1577s |
| flox-nocache-consolidated | macos-latest | warm | 2 | 159.3s | 14.6s | 92% | 319s |
| flox-nocache-mirror | macos-latest | warm | 10 | 158.2s | 9.7s | 94% | 1582s |
| mise-consolidated | macos-latest | warm | 2 | 5.7s | 12.8s | 31% | 11s |
| mise-mirror | macos-latest | warm | 10 | 6.2s | 9.2s | 40% | 62s |
| traditional | macos-latest | warm | 10 | 5.2s | 9.1s | 36% | 52s |
| flox-baked | ubuntu-latest | cold | 2 | 46.3s | 9.3s | 83% | 93s |
| flox-consolidated | ubuntu-latest | cold | 2 | 47.6s | 9.3s | 84% | 95s |
| flox-mirror | ubuntu-latest | cold | 10 | 47.6s | 5.6s | 89% | 476s |
| flox-noaction-consolidated | ubuntu-latest | cold | 2 | 50.5s | 9.5s | 84% | 101s |
| flox-noaction-mirror | ubuntu-latest | cold | 10 | 52.4s | 5.5s | 91% | 524s |
| flox-nocache-consolidated | ubuntu-latest | cold | 2 | 47.9s | 9.7s | 83% | 96s |
| flox-nocache-mirror | ubuntu-latest | cold | 10 | 47.5s | 5.4s | 90% | 475s |
| mise-consolidated | ubuntu-latest | cold | 2 | 9.5s | 8.8s | 52% | 19s |
| mise-mirror | ubuntu-latest | cold | 10 | 10.9s | 5.8s | 65% | 109s |
| traditional | ubuntu-latest | cold | 10 | 3.3s | 6.1s | 35% | 33s |
| flox-baked | ubuntu-latest | warm | 2 | 46.3s | 9.3s | 83% | 93s |
| flox-consolidated | ubuntu-latest | warm | 2 | 47.3s | 9.2s | 84% | 95s |
| flox-mirror | ubuntu-latest | warm | 10 | 48.1s | 6.4s | 88% | 481s |
| flox-noaction-consolidated | ubuntu-latest | warm | 2 | 54.5s | 10.6s | 84% | 109s |
| flox-noaction-mirror | ubuntu-latest | warm | 10 | 52.0s | 5.6s | 90% | 520s |
| flox-nocache-consolidated | ubuntu-latest | warm | 2 | 46.0s | 9.2s | 83% | 92s |
| flox-nocache-mirror | ubuntu-latest | warm | 10 | 47.8s | 5.4s | 90% | 478s |
| mise-consolidated | ubuntu-latest | warm | 2 | 5.4s | 10.1s | 35% | 11s |
| mise-mirror | ubuntu-latest | warm | 10 | 4.9s | 7.7s | 39% | 49s |
| traditional | ubuntu-latest | warm | 10 | 3.4s | 5.5s | 38% | 34s |

## Per-job breakdown (total job seconds)

| job | side | os | cache | avg | stddev |
| --- | --- | --- | --- | ---: | ---: |
| hygiene | flox-consolidated | macos-latest | cold | 160.0 | 12.4 |
| hygiene | flox-consolidated | macos-latest | warm | 178.0 | 1.0 |
| pytest | flox-consolidated | macos-latest | cold | 183.5 | 25.9 |
| pytest | flox-consolidated | macos-latest | warm | 184.5 | 10.5 |
| checks / bandit | flox-mirror | macos-latest | cold | 173.3 | 9.0 |
| checks / bandit | flox-mirror | macos-latest | warm | 143.3 | 18.4 |
| checks / codespell | flox-mirror | macos-latest | cold | 167.3 | 5.3 |
| checks / codespell | flox-mirror | macos-latest | warm | 161.0 | 30.8 |
| checks / commitlint | flox-mirror | macos-latest | cold | 190.3 | 43.6 |
| checks / commitlint | flox-mirror | macos-latest | warm | 167.0 | 22.2 |
| checks / gitleaks | flox-mirror | macos-latest | cold | 170.3 | 16.7 |
| checks / gitleaks | flox-mirror | macos-latest | warm | 166.7 | 25.3 |
| checks / pytest | flox-mirror | macos-latest | cold | 162.7 | 14.6 |
| checks / pytest | flox-mirror | macos-latest | warm | 187.0 | 4.3 |
| checks / ruff-check | flox-mirror | macos-latest | cold | 168.0 | 26.2 |
| checks / ruff-check | flox-mirror | macos-latest | warm | 165.3 | 17.8 |
| checks / ruff-format | flox-mirror | macos-latest | cold | 153.0 | 6.4 |
| checks / ruff-format | flox-mirror | macos-latest | warm | 167.7 | 20.8 |
| checks / taplo | flox-mirror | macos-latest | cold | 191.7 | 16.7 |
| checks / taplo | flox-mirror | macos-latest | warm | 191.0 | 27.1 |
| checks / ty | flox-mirror | macos-latest | cold | 183.7 | 35.2 |
| checks / ty | flox-mirror | macos-latest | warm | 176.0 | 20.4 |
| checks / yamllint | flox-mirror | macos-latest | cold | 179.3 | 1.9 |
| checks / yamllint | flox-mirror | macos-latest | warm | 186.7 | 17.7 |
| hygiene | flox-noaction-consolidated | macos-latest | cold | 165.4 | 16.9 |
| hygiene | flox-noaction-consolidated | macos-latest | warm | 164.6 | 22.5 |
| pytest | flox-noaction-consolidated | macos-latest | cold | 165.6 | 23.8 |
| pytest | flox-noaction-consolidated | macos-latest | warm | 155.8 | 18.9 |
| checks / bandit | flox-noaction-mirror | macos-latest | cold | 152.2 | 20.7 |
| checks / bandit | flox-noaction-mirror | macos-latest | warm | 166.8 | 33.8 |
| checks / codespell | flox-noaction-mirror | macos-latest | cold | 165.8 | 30.0 |
| checks / codespell | flox-noaction-mirror | macos-latest | warm | 173.0 | 24.0 |
| checks / commitlint | flox-noaction-mirror | macos-latest | cold | 165.6 | 16.5 |
| checks / commitlint | flox-noaction-mirror | macos-latest | warm | 171.4 | 25.5 |
| checks / gitleaks | flox-noaction-mirror | macos-latest | cold | 151.4 | 20.4 |
| checks / gitleaks | flox-noaction-mirror | macos-latest | warm | 173.2 | 23.9 |
| checks / pytest | flox-noaction-mirror | macos-latest | cold | 181.2 | 21.2 |
| checks / pytest | flox-noaction-mirror | macos-latest | warm | 181.0 | 29.0 |
| checks / ruff-check | flox-noaction-mirror | macos-latest | cold | 161.2 | 20.0 |
| checks / ruff-check | flox-noaction-mirror | macos-latest | warm | 179.0 | 34.5 |
| checks / ruff-format | flox-noaction-mirror | macos-latest | cold | 160.0 | 15.9 |
| checks / ruff-format | flox-noaction-mirror | macos-latest | warm | 174.2 | 27.4 |
| checks / taplo | flox-noaction-mirror | macos-latest | cold | 165.6 | 19.9 |
| checks / taplo | flox-noaction-mirror | macos-latest | warm | 145.4 | 21.1 |
| checks / ty | flox-noaction-mirror | macos-latest | cold | 150.0 | 15.4 |
| checks / ty | flox-noaction-mirror | macos-latest | warm | 155.4 | 12.4 |
| checks / yamllint | flox-noaction-mirror | macos-latest | cold | 161.4 | 19.0 |
| checks / yamllint | flox-noaction-mirror | macos-latest | warm | 156.2 | 19.4 |
| hygiene | flox-nocache-consolidated | macos-latest | cold | 184.0 | 10.8 |
| hygiene | flox-nocache-consolidated | macos-latest | warm | 162.2 | 25.2 |
| pytest | flox-nocache-consolidated | macos-latest | cold | 180.2 | 22.1 |
| pytest | flox-nocache-consolidated | macos-latest | warm | 185.6 | 22.3 |
| checks / bandit | flox-nocache-mirror | macos-latest | cold | 151.0 | 0.0 |
| checks / bandit | flox-nocache-mirror | macos-latest | warm | 174.8 | 18.8 |
| checks / codespell | flox-nocache-mirror | macos-latest | cold | 161.0 | 0.0 |
| checks / codespell | flox-nocache-mirror | macos-latest | warm | 176.0 | 25.0 |
| checks / commitlint | flox-nocache-mirror | macos-latest | cold | 132.0 | 0.0 |
| checks / commitlint | flox-nocache-mirror | macos-latest | warm | 179.0 | 17.4 |
| checks / gitleaks | flox-nocache-mirror | macos-latest | cold | 133.0 | 0.0 |
| checks / gitleaks | flox-nocache-mirror | macos-latest | warm | 170.2 | 20.0 |
| checks / pytest | flox-nocache-mirror | macos-latest | cold | 166.0 | 0.0 |
| checks / pytest | flox-nocache-mirror | macos-latest | warm | 171.7 | 22.2 |
| checks / ruff-check | flox-nocache-mirror | macos-latest | cold | 190.0 | 0.0 |
| checks / ruff-check | flox-nocache-mirror | macos-latest | warm | 171.7 | 23.3 |
| checks / ruff-format | flox-nocache-mirror | macos-latest | cold | 217.0 | 0.0 |
| checks / ruff-format | flox-nocache-mirror | macos-latest | warm | 154.2 | 14.7 |
| checks / taplo | flox-nocache-mirror | macos-latest | cold | 154.0 | 0.0 |
| checks / taplo | flox-nocache-mirror | macos-latest | warm | 158.3 | 26.3 |
| checks / ty | flox-nocache-mirror | macos-latest | cold | 132.0 | 0.0 |
| checks / ty | flox-nocache-mirror | macos-latest | warm | 159.3 | 17.5 |
| checks / yamllint | flox-nocache-mirror | macos-latest | cold | 161.0 | 0.0 |
| checks / yamllint | flox-nocache-mirror | macos-latest | warm | 163.7 | 16.5 |
| hygiene | mise-consolidated | macos-latest | cold | 26.0 | 3.5 |
| hygiene | mise-consolidated | macos-latest | warm | 16.8 | 3.2 |
| pytest | mise-consolidated | macos-latest | cold | 28.4 | 2.4 |
| pytest | mise-consolidated | macos-latest | warm | 20.2 | 2.7 |
| checks / bandit | mise-mirror | macos-latest | cold | 21.2 | 3.7 |
| checks / bandit | mise-mirror | macos-latest | warm | 14.8 | 2.9 |
| checks / codespell | mise-mirror | macos-latest | cold | 22.5 | 4.7 |
| checks / codespell | mise-mirror | macos-latest | warm | 13.0 | 2.4 |
| checks / commitlint | mise-mirror | macos-latest | cold | 22.8 | 2.5 |
| checks / commitlint | mise-mirror | macos-latest | warm | 14.2 | 1.2 |
| checks / gitleaks | mise-mirror | macos-latest | cold | 21.8 | 1.1 |
| checks / gitleaks | mise-mirror | macos-latest | warm | 14.2 | 2.0 |
| checks / pytest | mise-mirror | macos-latest | cold | 25.5 | 3.8 |
| checks / pytest | mise-mirror | macos-latest | warm | 21.4 | 1.2 |
| checks / ruff-check | mise-mirror | macos-latest | cold | 20.5 | 1.5 |
| checks / ruff-check | mise-mirror | macos-latest | warm | 15.2 | 3.5 |
| checks / ruff-format | mise-mirror | macos-latest | cold | 22.2 | 4.3 |
| checks / ruff-format | mise-mirror | macos-latest | warm | 14.2 | 1.6 |
| checks / taplo | mise-mirror | macos-latest | cold | 19.8 | 1.3 |
| checks / taplo | mise-mirror | macos-latest | warm | 13.4 | 2.2 |
| checks / ty | mise-mirror | macos-latest | cold | 24.5 | 3.4 |
| checks / ty | mise-mirror | macos-latest | warm | 19.6 | 6.7 |
| checks / yamllint | mise-mirror | macos-latest | cold | 21.0 | 3.5 |
| checks / yamllint | mise-mirror | macos-latest | warm | 13.8 | 2.9 |
| checks / bandit | traditional | macos-latest | cold | 12.8 | 1.7 |
| checks / bandit | traditional | macos-latest | warm | 14.4 | 4.9 |
| checks / codespell | traditional | macos-latest | cold | 12.2 | 0.7 |
| checks / codespell | traditional | macos-latest | warm | 12.6 | 1.0 |
| checks / commitlint | traditional | macos-latest | cold | 13.8 | 2.2 |
| checks / commitlint | traditional | macos-latest | warm | 16.8 | 3.2 |
| checks / gitleaks | traditional | macos-latest | cold | 33.0 | 40.5 |
| checks / gitleaks | traditional | macos-latest | warm | 12.8 | 2.2 |
| checks / pytest | traditional | macos-latest | cold | 17.6 | 4.3 |
| checks / pytest | traditional | macos-latest | warm | 18.8 | 3.0 |
| checks / ruff-check | traditional | macos-latest | cold | 14.6 | 4.8 |
| checks / ruff-check | traditional | macos-latest | warm | 14.2 | 1.7 |
| checks / ruff-format | traditional | macos-latest | cold | 12.8 | 1.0 |
| checks / ruff-format | traditional | macos-latest | warm | 13.4 | 2.3 |
| checks / taplo | traditional | macos-latest | cold | 16.2 | 4.9 |
| checks / taplo | traditional | macos-latest | warm | 11.4 | 0.8 |
| checks / ty | traditional | macos-latest | cold | 16.8 | 3.3 |
| checks / ty | traditional | macos-latest | warm | 14.8 | 2.1 |
| checks / yamllint | traditional | macos-latest | cold | 14.4 | 4.0 |
| checks / yamllint | traditional | macos-latest | warm | 13.2 | 1.3 |
| hygiene | flox-baked | ubuntu-latest | cold | 56.0 | 3.8 |
| hygiene | flox-baked | ubuntu-latest | warm | 55.8 | 4.9 |
| pytest | flox-baked | ubuntu-latest | cold | 55.2 | 5.9 |
| pytest | flox-baked | ubuntu-latest | warm | 55.4 | 3.3 |
| hygiene | flox-consolidated | ubuntu-latest | cold | 56.8 | 1.0 |
| hygiene | flox-consolidated | ubuntu-latest | warm | 56.4 | 0.8 |
| pytest | flox-consolidated | ubuntu-latest | cold | 57.0 | 2.1 |
| pytest | flox-consolidated | ubuntu-latest | warm | 56.6 | 1.0 |
| checks / bandit | flox-mirror | ubuntu-latest | cold | 51.2 | 1.9 |
| checks / bandit | flox-mirror | ubuntu-latest | warm | 52.4 | 3.1 |
| checks / codespell | flox-mirror | ubuntu-latest | cold | 51.6 | 1.0 |
| checks / codespell | flox-mirror | ubuntu-latest | warm | 50.6 | 2.0 |
| checks / commitlint | flox-mirror | ubuntu-latest | cold | 53.4 | 1.7 |
| checks / commitlint | flox-mirror | ubuntu-latest | warm | 55.6 | 4.3 |
| checks / gitleaks | flox-mirror | ubuntu-latest | cold | 51.8 | 4.4 |
| checks / gitleaks | flox-mirror | ubuntu-latest | warm | 54.6 | 2.4 |
| checks / pytest | flox-mirror | ubuntu-latest | cold | 57.0 | 2.6 |
| checks / pytest | flox-mirror | ubuntu-latest | warm | 61.2 | 2.8 |
| checks / ruff-check | flox-mirror | ubuntu-latest | cold | 54.6 | 3.5 |
| checks / ruff-check | flox-mirror | ubuntu-latest | warm | 53.6 | 2.1 |
| checks / ruff-format | flox-mirror | ubuntu-latest | cold | 51.6 | 2.7 |
| checks / ruff-format | flox-mirror | ubuntu-latest | warm | 53.4 | 3.0 |
| checks / taplo | flox-mirror | ubuntu-latest | cold | 51.0 | 0.9 |
| checks / taplo | flox-mirror | ubuntu-latest | warm | 54.4 | 2.6 |
| checks / ty | flox-mirror | ubuntu-latest | cold | 57.2 | 2.5 |
| checks / ty | flox-mirror | ubuntu-latest | warm | 54.8 | 4.3 |
| checks / yamllint | flox-mirror | ubuntu-latest | cold | 52.8 | 2.3 |
| checks / yamllint | flox-mirror | ubuntu-latest | warm | 53.6 | 1.6 |
| hygiene | flox-noaction-consolidated | ubuntu-latest | cold | 60.7 | 1.7 |
| hygiene | flox-noaction-consolidated | ubuntu-latest | warm | 64.5 | 6.7 |
| pytest | flox-noaction-consolidated | ubuntu-latest | cold | 59.3 | 1.2 |
| pytest | flox-noaction-consolidated | ubuntu-latest | warm | 65.7 | 6.1 |
| checks / bandit | flox-noaction-mirror | ubuntu-latest | cold | 56.8 | 1.9 |
| checks / bandit | flox-noaction-mirror | ubuntu-latest | warm | 50.0 | 0.0 |
| checks / codespell | flox-noaction-mirror | ubuntu-latest | cold | 57.8 | 3.3 |
| checks / codespell | flox-noaction-mirror | ubuntu-latest | warm | 55.0 | 0.0 |
| checks / commitlint | flox-noaction-mirror | ubuntu-latest | cold | 56.5 | 5.0 |
| checks / commitlint | flox-noaction-mirror | ubuntu-latest | warm | 58.0 | 0.0 |
| checks / gitleaks | flox-noaction-mirror | ubuntu-latest | cold | 59.5 | 2.9 |
| checks / gitleaks | flox-noaction-mirror | ubuntu-latest | warm | 59.0 | 0.0 |
| checks / pytest | flox-noaction-mirror | ubuntu-latest | cold | 58.5 | 5.6 |
| checks / pytest | flox-noaction-mirror | ubuntu-latest | warm | 62.0 | 0.0 |
| checks / ruff-check | flox-noaction-mirror | ubuntu-latest | cold | 58.2 | 1.6 |
| checks / ruff-check | flox-noaction-mirror | ubuntu-latest | warm | 69.0 | 0.0 |
| checks / ruff-format | flox-noaction-mirror | ubuntu-latest | cold | 55.2 | 1.8 |
| checks / ruff-format | flox-noaction-mirror | ubuntu-latest | warm | 58.0 | 0.0 |
| checks / taplo | flox-noaction-mirror | ubuntu-latest | cold | 57.8 | 4.4 |
| checks / taplo | flox-noaction-mirror | ubuntu-latest | warm | 56.0 | 0.0 |
| checks / ty | flox-noaction-mirror | ubuntu-latest | cold | 60.5 | 3.6 |
| checks / ty | flox-noaction-mirror | ubuntu-latest | warm | 55.0 | 0.0 |
| checks / yamllint | flox-noaction-mirror | ubuntu-latest | cold | 57.5 | 2.3 |
| checks / yamllint | flox-noaction-mirror | ubuntu-latest | warm | 54.0 | 0.0 |
| hygiene | flox-nocache-consolidated | ubuntu-latest | cold | 57.2 | 3.9 |
| hygiene | flox-nocache-consolidated | ubuntu-latest | warm | 53.8 | 4.0 |
| pytest | flox-nocache-consolidated | ubuntu-latest | cold | 58.0 | 1.1 |
| pytest | flox-nocache-consolidated | ubuntu-latest | warm | 56.6 | 1.6 |
| checks / bandit | flox-nocache-mirror | ubuntu-latest | cold | 53.2 | 2.9 |
| checks / bandit | flox-nocache-mirror | ubuntu-latest | warm | 54.2 | 1.5 |
| checks / codespell | flox-nocache-mirror | ubuntu-latest | cold | 51.8 | 2.5 |
| checks / codespell | flox-nocache-mirror | ubuntu-latest | warm | 53.6 | 3.1 |
| checks / commitlint | flox-nocache-mirror | ubuntu-latest | cold | 54.0 | 1.8 |
| checks / commitlint | flox-nocache-mirror | ubuntu-latest | warm | 53.0 | 1.4 |
| checks / gitleaks | flox-nocache-mirror | ubuntu-latest | cold | 51.8 | 4.4 |
| checks / gitleaks | flox-nocache-mirror | ubuntu-latest | warm | 52.4 | 4.6 |
| checks / pytest | flox-nocache-mirror | ubuntu-latest | cold | 55.6 | 2.6 |
| checks / pytest | flox-nocache-mirror | ubuntu-latest | warm | 58.0 | 2.1 |
| checks / ruff-check | flox-nocache-mirror | ubuntu-latest | cold | 51.6 | 2.0 |
| checks / ruff-check | flox-nocache-mirror | ubuntu-latest | warm | 51.6 | 1.9 |
| checks / ruff-format | flox-nocache-mirror | ubuntu-latest | cold | 52.2 | 1.3 |
| checks / ruff-format | flox-nocache-mirror | ubuntu-latest | warm | 51.0 | 0.6 |
| checks / taplo | flox-nocache-mirror | ubuntu-latest | cold | 51.8 | 1.8 |
| checks / taplo | flox-nocache-mirror | ubuntu-latest | warm | 52.0 | 1.1 |
| checks / ty | flox-nocache-mirror | ubuntu-latest | cold | 53.0 | 1.7 |
| checks / ty | flox-nocache-mirror | ubuntu-latest | warm | 53.4 | 2.1 |
| checks / yamllint | flox-nocache-mirror | ubuntu-latest | cold | 54.0 | 1.4 |
| checks / yamllint | flox-nocache-mirror | ubuntu-latest | warm | 53.2 | 3.9 |
| hygiene | mise-consolidated | ubuntu-latest | cold | 19.0 | 0.0 |
| hygiene | mise-consolidated | ubuntu-latest | warm | 14.0 | 3.8 |
| pytest | mise-consolidated | ubuntu-latest | cold | 17.5 | 0.5 |
| pytest | mise-consolidated | ubuntu-latest | warm | 17.0 | 4.4 |
| checks / bandit | mise-mirror | ubuntu-latest | cold | 15.8 | 1.9 |
| checks / bandit | mise-mirror | ubuntu-latest | warm | 9.0 | 1.1 |
| checks / codespell | mise-mirror | ubuntu-latest | cold | 16.6 | 2.7 |
| checks / codespell | mise-mirror | ubuntu-latest | warm | 9.8 | 2.3 |
| checks / commitlint | mise-mirror | ubuntu-latest | cold | 16.0 | 2.0 |
| checks / commitlint | mise-mirror | ubuntu-latest | warm | 10.8 | 2.5 |
| checks / gitleaks | mise-mirror | ubuntu-latest | cold | 18.4 | 2.0 |
| checks / gitleaks | mise-mirror | ubuntu-latest | warm | 9.8 | 1.9 |
| checks / pytest | mise-mirror | ubuntu-latest | cold | 21.4 | 2.4 |
| checks / pytest | mise-mirror | ubuntu-latest | warm | 13.8 | 3.5 |
| checks / ruff-check | mise-mirror | ubuntu-latest | cold | 17.4 | 2.9 |
| checks / ruff-check | mise-mirror | ubuntu-latest | warm | 11.0 | 3.5 |
| checks / ruff-format | mise-mirror | ubuntu-latest | cold | 14.4 | 2.0 |
| checks / ruff-format | mise-mirror | ubuntu-latest | warm | 11.2 | 6.9 |
| checks / taplo | mise-mirror | ubuntu-latest | cold | 17.0 | 3.3 |
| checks / taplo | mise-mirror | ubuntu-latest | warm | 28.4 | 39.9 |
| checks / ty | mise-mirror | ubuntu-latest | cold | 16.0 | 2.5 |
| checks / ty | mise-mirror | ubuntu-latest | warm | 14.0 | 12.0 |
| checks / yamllint | mise-mirror | ubuntu-latest | cold | 14.4 | 1.4 |
| checks / yamllint | mise-mirror | ubuntu-latest | warm | 8.6 | 1.9 |
| checks / bandit | traditional | ubuntu-latest | cold | 9.8 | 1.8 |
| checks / bandit | traditional | ubuntu-latest | warm | 7.7 | 1.7 |
| checks / codespell | traditional | ubuntu-latest | cold | 8.8 | 2.1 |
| checks / codespell | traditional | ubuntu-latest | warm | 9.3 | 2.4 |
| checks / commitlint | traditional | ubuntu-latest | cold | 7.8 | 0.9 |
| checks / commitlint | traditional | ubuntu-latest | warm | 9.3 | 1.2 |
| checks / gitleaks | traditional | ubuntu-latest | cold | 10.5 | 5.6 |
| checks / gitleaks | traditional | ubuntu-latest | warm | 7.0 | 0.8 |
| checks / pytest | traditional | ubuntu-latest | cold | 13.7 | 6.4 |
| checks / pytest | traditional | ubuntu-latest | warm | 13.7 | 2.9 |
| checks / ruff-check | traditional | ubuntu-latest | cold | 8.5 | 2.5 |
| checks / ruff-check | traditional | ubuntu-latest | warm | 9.0 | 2.2 |
| checks / ruff-format | traditional | ubuntu-latest | cold | 8.3 | 1.7 |
| checks / ruff-format | traditional | ubuntu-latest | warm | 9.0 | 2.4 |
| checks / taplo | traditional | ubuntu-latest | cold | 6.8 | 1.6 |
| checks / taplo | traditional | ubuntu-latest | warm | 6.3 | 0.5 |
| checks / ty | traditional | ubuntu-latest | cold | 9.5 | 1.3 |
| checks / ty | traditional | ubuntu-latest | warm | 10.0 | 2.2 |
| checks / yamllint | traditional | ubuntu-latest | cold | 10.0 | 1.2 |
| checks / yamllint | traditional | ubuntu-latest | warm | 8.3 | 1.7 |

## Charts

![total time](total_time.png)
