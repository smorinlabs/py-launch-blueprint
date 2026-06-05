# Flox vs Traditional CI — timing results

Appendix: [last-run workflow wall-clock totals](LAST_RUN_TOTALS.md) records the final successful run per cell using GitHub's literal `run_duration_ms`, including the `flox-baked` container runs.

## Total run time (per side × os × cache)

| side | os | cache | n | min | max | avg | median | stddev | Δ% vs base |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| flox-consolidated | macos-latest | cold | 5 | 159.0 | 224.0 | 197.0 | 204.0 | 21.7 | +207.8% |
| flox-mirror | macos-latest | cold | 2 | 408.0 | 424.0 | 416.0 | 416.0 | 8.0 | +550.0% |
| flox-noaction-consolidated | macos-latest | cold | 5 | 181.0 | 196.0 | 191.6 | 193.0 | 5.5 | +199.4% |
| flox-noaction-mirror | macos-latest | cold | 5 | 336.0 | 424.0 | 368.0 | 366.0 | 30.2 | +475.0% |
| flox-nocache-consolidated | macos-latest | cold | 5 | 175.0 | 210.0 | 195.6 | 200.0 | 13.2 | +205.6% |
| mise-consolidated | macos-latest | cold | 5 | 34.0 | 42.0 | 39.4 | 41.0 | 2.9 | -38.4% |
| mise-mirror | macos-latest | cold | 4 | 64.0 | 79.0 | 68.8 | 66.0 | 6.0 | +7.4% |
| traditional | macos-latest | cold | 5 | 38.0 | 125.0 | 64.0 | 55.0 | 31.1 | — |
| flox-consolidated | macos-latest | warm | 1 | 202.0 | 202.0 | 202.0 | 202.0 | 0.0 | +312.2% |
| flox-mirror | macos-latest | warm | 2 | 384.0 | 426.0 | 405.0 | 405.0 | 21.0 | +726.5% |
| flox-noaction-consolidated | macos-latest | warm | 5 | 161.0 | 209.0 | 183.2 | 183.0 | 16.6 | +273.9% |
| flox-noaction-mirror | macos-latest | warm | 5 | 365.0 | 413.0 | 393.0 | 404.0 | 19.3 | +702.0% |
| flox-nocache-consolidated | macos-latest | warm | 5 | 188.0 | 216.0 | 200.8 | 199.0 | 11.1 | +309.8% |
| flox-nocache-mirror | macos-latest | warm | 5 | 342.0 | 404.0 | 384.6 | 396.0 | 22.7 | +684.9% |
| mise-consolidated | macos-latest | warm | 5 | 25.0 | 33.0 | 29.8 | 32.0 | 3.2 | -39.2% |
| mise-mirror | macos-latest | warm | 5 | 49.0 | 65.0 | 55.8 | 55.0 | 5.7 | +13.9% |
| traditional | macos-latest | warm | 5 | 45.0 | 55.0 | 49.0 | 48.0 | 3.4 | — |
| flox-baked | ubuntu-latest | cold | 5 | 58.0 | 74.0 | 65.8 | 66.0 | 5.3 | +153.1% |
| flox-consolidated | ubuntu-latest | cold | 5 | 65.0 | 72.0 | 69.0 | 70.0 | 2.6 | +165.4% |
| flox-mirror | ubuntu-latest | cold | 5 | 64.0 | 75.0 | 70.0 | 69.0 | 4.0 | +169.2% |
| flox-noaction-consolidated | ubuntu-latest | cold | 3 | 66.0 | 223.0 | 118.3 | 66.0 | 74.0 | +355.1% |
| flox-noaction-mirror | ubuntu-latest | cold | 3 | 69.0 | 71.0 | 70.0 | 70.0 | 0.8 | +169.2% |
| flox-nocache-consolidated | ubuntu-latest | cold | 5 | 63.0 | 69.0 | 65.6 | 65.0 | 2.2 | +152.3% |
| flox-nocache-mirror | ubuntu-latest | cold | 5 | 61.0 | 66.0 | 63.6 | 63.0 | 1.7 | +144.6% |
| mise-consolidated | ubuntu-latest | cold | 1 | 25.0 | 25.0 | 25.0 | 25.0 | 0.0 | -3.8% |
| mise-mirror | ubuntu-latest | cold | 5 | 29.0 | 32.0 | 30.2 | 30.0 | 1.2 | +16.2% |
| traditional | ubuntu-latest | cold | 5 | 18.0 | 38.0 | 26.0 | 22.0 | 7.2 | — |
| flox-baked | ubuntu-latest | warm | 5 | 59.0 | 71.0 | 62.8 | 60.0 | 4.4 | +13.4% |
| flox-consolidated | ubuntu-latest | warm | 5 | 63.0 | 66.0 | 64.4 | 64.0 | 1.0 | +16.2% |
| flox-mirror | ubuntu-latest | warm | 5 | 71.0 | 78.0 | 74.0 | 72.0 | 3.3 | +33.6% |
| flox-noaction-consolidated | ubuntu-latest | warm | 5 | 67.0 | 85.0 | 74.0 | 71.0 | 6.2 | +33.6% |
| flox-nocache-consolidated | ubuntu-latest | warm | 5 | 61.0 | 68.0 | 63.2 | 62.0 | 2.6 | +14.1% |
| flox-nocache-mirror | ubuntu-latest | warm | 5 | 62.0 | 69.0 | 64.8 | 64.0 | 2.5 | +17.0% |
| mise-consolidated | ubuntu-latest | warm | 4 | 17.0 | 31.0 | 23.8 | 23.5 | 5.0 | -57.1% |
| mise-mirror | ubuntu-latest | warm | 5 | 17.0 | 115.0 | 44.6 | 26.0 | 36.4 | -19.5% |
| traditional | ubuntu-latest | warm | 5 | 20.0 | 125.0 | 55.4 | 48.0 | 37.0 | — |

## Provisioning (setup) vs work — per job

setup = the `provision` step (flox install/activate, or setup-uv/just/bun); work = the rest of the job. `total provisioning/run` = setup summed across all jobs in a run (the cumulative billable provisioning cost).

| side | os | cache | jobs | avg setup/job | avg work/job | setup % | total provisioning/run |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| flox-consolidated | macos-latest | cold | 2 | 158.4s | 15.3s | 91% | 317s |
| flox-mirror | macos-latest | cold | 10 | 162.4s | 10.2s | 94% | 1624s |
| flox-noaction-consolidated | macos-latest | cold | 2 | 150.6s | 14.9s | 91% | 301s |
| flox-noaction-mirror | macos-latest | cold | 10 | 152.0s | 9.5s | 94% | 1520s |
| flox-nocache-consolidated | macos-latest | cold | 2 | 166.0s | 16.1s | 91% | 332s |
| mise-consolidated | macos-latest | cold | 2 | 13.9s | 13.3s | 51% | 28s |
| mise-mirror | macos-latest | cold | 10 | 13.7s | 8.5s | 62% | 137s |
| traditional | macos-latest | cold | 10 | 5.5s | 10.9s | 34% | 55s |
| flox-consolidated | macos-latest | warm | 2 | 170.5s | 15.5s | 92% | 341s |
| flox-mirror | macos-latest | warm | 10 | 166.3s | 10.1s | 94% | 1664s |
| flox-noaction-consolidated | macos-latest | warm | 2 | 146.4s | 13.8s | 91% | 293s |
| flox-noaction-mirror | macos-latest | warm | 10 | 157.7s | 9.8s | 94% | 1577s |
| flox-nocache-consolidated | macos-latest | warm | 2 | 159.3s | 14.6s | 92% | 319s |
| flox-nocache-mirror | macos-latest | warm | 10 | 159.1s | 9.9s | 94% | 1591s |
| mise-consolidated | macos-latest | warm | 2 | 5.7s | 12.8s | 31% | 11s |
| mise-mirror | macos-latest | warm | 10 | 6.2s | 9.2s | 40% | 62s |
| traditional | macos-latest | warm | 10 | 5.2s | 9.1s | 36% | 52s |
| flox-baked | ubuntu-latest | cold | 2 | 46.3s | 9.3s | 83% | 93s |
| flox-consolidated | ubuntu-latest | cold | 2 | 47.6s | 9.3s | 84% | 95s |
| flox-mirror | ubuntu-latest | cold | 10 | 47.6s | 5.6s | 89% | 476s |
| flox-noaction-consolidated | ubuntu-latest | cold | 2 | 93.7s | 11.0s | 89% | 187s |
| flox-noaction-mirror | ubuntu-latest | cold | 10 | 51.6s | 5.7s | 90% | 516s |
| flox-nocache-consolidated | ubuntu-latest | cold | 2 | 47.9s | 9.7s | 83% | 96s |
| flox-nocache-mirror | ubuntu-latest | cold | 10 | 47.5s | 5.4s | 90% | 475s |
| mise-consolidated | ubuntu-latest | cold | 2 | 9.5s | 9.0s | 51% | 19s |
| mise-mirror | ubuntu-latest | cold | 10 | 10.9s | 5.8s | 65% | 109s |
| traditional | ubuntu-latest | cold | 10 | 3.5s | 6.1s | 36% | 35s |
| flox-baked | ubuntu-latest | warm | 2 | 46.3s | 9.3s | 83% | 93s |
| flox-consolidated | ubuntu-latest | warm | 2 | 47.3s | 9.2s | 84% | 95s |
| flox-mirror | ubuntu-latest | warm | 10 | 48.1s | 6.4s | 88% | 481s |
| flox-noaction-consolidated | ubuntu-latest | warm | 2 | 55.0s | 10.8s | 84% | 110s |
| flox-nocache-consolidated | ubuntu-latest | warm | 2 | 46.0s | 9.2s | 83% | 92s |
| flox-nocache-mirror | ubuntu-latest | warm | 10 | 47.8s | 5.4s | 90% | 478s |
| mise-consolidated | ubuntu-latest | warm | 2 | 5.9s | 10.2s | 36% | 12s |
| mise-mirror | ubuntu-latest | warm | 10 | 4.9s | 7.7s | 39% | 49s |
| traditional | ubuntu-latest | warm | 10 | 4.7s | 9.6s | 33% | 47s |

## Per-job breakdown (total job seconds)

| job | side | os | cache | avg | stddev |
| --- | --- | --- | --- | ---: | ---: |
| hygiene | flox-consolidated | macos-latest | cold | 160.0 | 13.6 |
| hygiene | flox-consolidated | macos-latest | warm | 177.0 | 0.0 |
| pytest | flox-consolidated | macos-latest | cold | 187.4 | 26.7 |
| pytest | flox-consolidated | macos-latest | warm | 195.0 | 0.0 |
| checks / bandit | flox-mirror | macos-latest | cold | 167.0 | 1.0 |
| checks / bandit | flox-mirror | macos-latest | warm | 148.0 | 21.0 |
| checks / codespell | flox-mirror | macos-latest | cold | 164.0 | 3.0 |
| checks / codespell | flox-mirror | macos-latest | warm | 166.5 | 36.5 |
| checks / commitlint | flox-mirror | macos-latest | cold | 172.0 | 43.0 |
| checks / commitlint | flox-mirror | macos-latest | warm | 182.5 | 4.5 |
| checks / gitleaks | flox-mirror | macos-latest | cold | 181.5 | 6.5 |
| checks / gitleaks | flox-mirror | macos-latest | warm | 166.0 | 31.0 |
| checks / pytest | flox-mirror | macos-latest | cold | 157.5 | 15.5 |
| checks / pytest | flox-mirror | macos-latest | warm | 189.0 | 4.0 |
| checks / ruff-check | flox-mirror | macos-latest | cold | 185.5 | 10.5 |
| checks / ruff-check | flox-mirror | macos-latest | warm | 175.0 | 14.0 |
| checks / ruff-format | flox-mirror | macos-latest | cold | 155.5 | 6.5 |
| checks / ruff-format | flox-mirror | macos-latest | warm | 174.0 | 23.0 |
| checks / taplo | flox-mirror | macos-latest | cold | 191.5 | 20.5 |
| checks / taplo | flox-mirror | macos-latest | warm | 196.0 | 32.0 |
| checks / ty | flox-mirror | macos-latest | cold | 172.5 | 38.5 |
| checks / ty | flox-mirror | macos-latest | warm | 188.5 | 12.5 |
| checks / yamllint | flox-mirror | macos-latest | cold | 180.0 | 2.0 |
| checks / yamllint | flox-mirror | macos-latest | warm | 178.5 | 16.5 |
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
| checks / bandit | flox-nocache-mirror | macos-latest | warm | 174.2 | 20.6 |
| checks / codespell | flox-nocache-mirror | macos-latest | warm | 183.2 | 21.0 |
| checks / commitlint | flox-nocache-mirror | macos-latest | warm | 176.8 | 18.3 |
| checks / gitleaks | flox-nocache-mirror | macos-latest | warm | 172.8 | 21.0 |
| checks / pytest | flox-nocache-mirror | macos-latest | warm | 168.2 | 22.8 |
| checks / ruff-check | flox-nocache-mirror | macos-latest | warm | 178.0 | 20.2 |
| checks / ruff-format | flox-nocache-mirror | macos-latest | warm | 155.0 | 16.0 |
| checks / taplo | flox-nocache-mirror | macos-latest | warm | 162.8 | 26.6 |
| checks / ty | flox-nocache-mirror | macos-latest | warm | 156.8 | 18.2 |
| checks / yamllint | flox-nocache-mirror | macos-latest | warm | 161.6 | 17.3 |
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
| hygiene | flox-noaction-consolidated | ubuntu-latest | cold | 99.3 | 56.3 |
| hygiene | flox-noaction-consolidated | ubuntu-latest | warm | 65.0 | 7.3 |
| pytest | flox-noaction-consolidated | ubuntu-latest | cold | 110.0 | 71.4 |
| pytest | flox-noaction-consolidated | ubuntu-latest | warm | 66.6 | 6.3 |
| checks / bandit | flox-noaction-mirror | ubuntu-latest | cold | 55.7 | 0.5 |
| checks / codespell | flox-noaction-mirror | ubuntu-latest | cold | 59.0 | 2.9 |
| checks / commitlint | flox-noaction-mirror | ubuntu-latest | cold | 53.7 | 1.2 |
| checks / gitleaks | flox-noaction-mirror | ubuntu-latest | cold | 58.0 | 1.4 |
| checks / pytest | flox-noaction-mirror | ubuntu-latest | cold | 57.3 | 6.0 |
| checks / ruff-check | flox-noaction-mirror | ubuntu-latest | cold | 57.3 | 0.5 |
| checks / ruff-format | flox-noaction-mirror | ubuntu-latest | cold | 56.0 | 1.4 |
| checks / taplo | flox-noaction-mirror | ubuntu-latest | cold | 58.3 | 5.0 |
| checks / ty | flox-noaction-mirror | ubuntu-latest | cold | 61.3 | 3.9 |
| checks / yamllint | flox-noaction-mirror | ubuntu-latest | cold | 56.3 | 1.2 |
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
| hygiene | mise-consolidated | ubuntu-latest | warm | 14.5 | 4.2 |
| pytest | mise-consolidated | ubuntu-latest | cold | 18.0 | 0.0 |
| pytest | mise-consolidated | ubuntu-latest | warm | 17.8 | 4.6 |
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
| checks / bandit | traditional | ubuntu-latest | cold | 9.8 | 1.9 |
| checks / bandit | traditional | ubuntu-latest | warm | 10.4 | 1.9 |
| checks / codespell | traditional | ubuntu-latest | cold | 9.4 | 1.9 |
| checks / codespell | traditional | ubuntu-latest | warm | 10.6 | 2.4 |
| checks / commitlint | traditional | ubuntu-latest | cold | 8.0 | 0.9 |
| checks / commitlint | traditional | ubuntu-latest | warm | 14.2 | 4.7 |
| checks / gitleaks | traditional | ubuntu-latest | cold | 10.2 | 6.1 |
| checks / gitleaks | traditional | ubuntu-latest | warm | 31.4 | 41.5 |
| checks / pytest | traditional | ubuntu-latest | cold | 14.4 | 6.8 |
| checks / pytest | traditional | ubuntu-latest | warm | 15.6 | 3.6 |
| checks / ruff-check | traditional | ubuntu-latest | cold | 9.0 | 2.4 |
| checks / ruff-check | traditional | ubuntu-latest | warm | 14.6 | 5.3 |
| checks / ruff-format | traditional | ubuntu-latest | cold | 7.8 | 1.3 |
| checks / ruff-format | traditional | ubuntu-latest | warm | 11.6 | 1.4 |
| checks / taplo | traditional | ubuntu-latest | cold | 7.0 | 1.7 |
| checks / taplo | traditional | ubuntu-latest | warm | 9.6 | 2.9 |
| checks / ty | traditional | ubuntu-latest | cold | 10.0 | 0.6 |
| checks / ty | traditional | ubuntu-latest | warm | 14.2 | 3.1 |
| checks / yamllint | traditional | ubuntu-latest | cold | 10.0 | 1.3 |
| checks / yamllint | traditional | ubuntu-latest | warm | 10.8 | 2.8 |

## Charts

![total time](total_time.png)
