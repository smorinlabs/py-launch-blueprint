# Flox vs Traditional CI — timing results

## Total run time (per side × os × cache)

| side | os | cache | n | min | max | avg | median | stddev | Δ% vs base |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| flox-consolidated | macos-latest | cold | 5 | 169.0 | 199.0 | 181.6 | 173.0 | 13.9 | +398.9% |
| flox-mirror | macos-latest | cold | 5 | 295.0 | 331.0 | 318.4 | 324.0 | 13.5 | +774.7% |
| traditional | macos-latest | cold | 5 | 35.0 | 39.0 | 36.4 | 36.0 | 1.5 | — |
| flox-consolidated | macos-latest | warm | 5 | 132.0 | 201.0 | 161.6 | 158.0 | 27.1 | +317.9% |
| flox-mirror | macos-latest | warm | 5 | 292.0 | 323.0 | 303.6 | 302.0 | 10.9 | +685.2% |
| traditional | macos-latest | warm | 3 | 34.0 | 41.0 | 38.7 | 41.0 | 3.3 | — |
| flox-consolidated | ubuntu-latest | cold | 5 | 60.0 | 71.0 | 64.8 | 65.0 | 3.8 | +276.7% |
| flox-mirror | ubuntu-latest | cold | 5 | 60.0 | 68.0 | 64.8 | 64.0 | 3.0 | +276.7% |
| traditional | ubuntu-latest | cold | 5 | 15.0 | 20.0 | 17.2 | 17.0 | 2.0 | — |
| flox-consolidated | ubuntu-latest | warm | 5 | 60.0 | 65.0 | 62.8 | 64.0 | 2.3 | +265.1% |
| flox-mirror | ubuntu-latest | warm | 5 | 63.0 | 67.0 | 64.6 | 64.0 | 1.4 | +275.6% |
| traditional | ubuntu-latest | warm | 5 | 16.0 | 19.0 | 17.2 | 17.0 | 1.2 | — |

## Provisioning (setup) vs work — per job

setup = the `provision` step (flox install/activate, or setup-uv/just/bun); work = the rest of the job. `total provisioning/run` = setup summed across all jobs in a run (the cumulative billable provisioning cost).

| side | os | cache | jobs | avg setup/job | avg work/job | setup % | total provisioning/run |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| flox-consolidated | macos-latest | cold | 2 | 150.6s | 14.7s | 91% | 301s |
| flox-mirror | macos-latest | cold | 10 | 135.8s | 9.0s | 94% | 1358s |
| traditional | macos-latest | cold | 10 | 4.1s | 7.8s | 34% | 41s |
| flox-consolidated | macos-latest | warm | 2 | 128.8s | 12.8s | 91% | 258s |
| flox-mirror | macos-latest | warm | 10 | 128.8s | 7.8s | 94% | 1288s |
| traditional | macos-latest | warm | 10 | 5.0s | 7.3s | 41% | 50s |
| flox-consolidated | ubuntu-latest | cold | 2 | 49.3s | 8.7s | 85% | 99s |
| flox-mirror | ubuntu-latest | cold | 10 | 46.5s | 5.1s | 90% | 465s |
| traditional | ubuntu-latest | cold | 10 | 3.0s | 5.3s | 36% | 30s |
| flox-consolidated | ubuntu-latest | warm | 2 | 48.3s | 8.2s | 85% | 97s |
| flox-mirror | ubuntu-latest | warm | 10 | 47.6s | 5.1s | 90% | 476s |
| traditional | ubuntu-latest | warm | 10 | 3.3s | 5.2s | 39% | 33s |

## Per-job breakdown (total job seconds)

| job | side | os | cache | avg | stddev |
| --- | --- | --- | --- | ---: | ---: |
| hygiene | flox-consolidated | macos-latest | cold | 167.4 | 20.4 |
| hygiene | flox-consolidated | macos-latest | warm | 137.4 | 20.5 |
| pytest | flox-consolidated | macos-latest | cold | 163.2 | 20.1 |
| pytest | flox-consolidated | macos-latest | warm | 145.8 | 26.3 |
| checks / bandit | flox-mirror | macos-latest | cold | 134.4 | 10.3 |
| checks / bandit | flox-mirror | macos-latest | warm | 143.6 | 19.7 |
| checks / codespell | flox-mirror | macos-latest | cold | 138.6 | 11.6 |
| checks / codespell | flox-mirror | macos-latest | warm | 137.6 | 19.4 |
| checks / commitlint | flox-mirror | macos-latest | cold | 135.8 | 17.3 |
| checks / commitlint | flox-mirror | macos-latest | warm | 133.2 | 4.1 |
| checks / gitleaks | flox-mirror | macos-latest | cold | 156.2 | 14.7 |
| checks / gitleaks | flox-mirror | macos-latest | warm | 134.0 | 14.2 |
| checks / pytest | flox-mirror | macos-latest | cold | 142.6 | 15.2 |
| checks / pytest | flox-mirror | macos-latest | warm | 140.6 | 10.8 |
| checks / ruff-check | flox-mirror | macos-latest | cold | 155.8 | 17.2 |
| checks / ruff-check | flox-mirror | macos-latest | warm | 129.4 | 5.7 |
| checks / ruff-format | flox-mirror | macos-latest | cold | 152.8 | 19.1 |
| checks / ruff-format | flox-mirror | macos-latest | warm | 139.2 | 16.1 |
| checks / taplo | flox-mirror | macos-latest | cold | 145.8 | 19.6 |
| checks / taplo | flox-mirror | macos-latest | warm | 138.2 | 10.2 |
| checks / ty | flox-mirror | macos-latest | cold | 150.2 | 24.3 |
| checks / ty | flox-mirror | macos-latest | warm | 131.8 | 13.2 |
| checks / yamllint | flox-mirror | macos-latest | cold | 136.0 | 17.7 |
| checks / yamllint | flox-mirror | macos-latest | warm | 137.8 | 13.5 |
| checks / bandit | traditional | macos-latest | cold | 11.4 | 0.8 |
| checks / bandit | traditional | macos-latest | warm | 12.3 | 1.7 |
| checks / codespell | traditional | macos-latest | cold | 12.2 | 1.7 |
| checks / codespell | traditional | macos-latest | warm | 12.0 | 1.4 |
| checks / commitlint | traditional | macos-latest | cold | 12.8 | 1.0 |
| checks / commitlint | traditional | macos-latest | warm | 13.0 | 0.8 |
| checks / gitleaks | traditional | macos-latest | cold | 11.4 | 0.8 |
| checks / gitleaks | traditional | macos-latest | warm | 11.3 | 0.5 |
| checks / pytest | traditional | macos-latest | cold | 16.6 | 1.0 |
| checks / pytest | traditional | macos-latest | warm | 18.0 | 2.2 |
| checks / ruff-check | traditional | macos-latest | cold | 10.8 | 1.5 |
| checks / ruff-check | traditional | macos-latest | warm | 11.3 | 1.2 |
| checks / ruff-format | traditional | macos-latest | cold | 9.8 | 0.4 |
| checks / ruff-format | traditional | macos-latest | warm | 10.3 | 0.5 |
| checks / taplo | traditional | macos-latest | cold | 11.6 | 0.5 |
| checks / taplo | traditional | macos-latest | warm | 10.3 | 0.5 |
| checks / ty | traditional | macos-latest | cold | 11.8 | 0.7 |
| checks / ty | traditional | macos-latest | warm | 12.0 | 0.8 |
| checks / yamllint | traditional | macos-latest | cold | 10.8 | 1.2 |
| checks / yamllint | traditional | macos-latest | warm | 12.7 | 0.5 |
| hygiene | flox-consolidated | ubuntu-latest | cold | 57.8 | 4.2 |
| hygiene | flox-consolidated | ubuntu-latest | warm | 56.8 | 2.3 |
| pytest | flox-consolidated | ubuntu-latest | cold | 58.2 | 2.1 |
| pytest | flox-consolidated | ubuntu-latest | warm | 56.2 | 2.7 |
| checks / bandit | flox-mirror | ubuntu-latest | cold | 53.4 | 3.9 |
| checks / bandit | flox-mirror | ubuntu-latest | warm | 52.2 | 2.8 |
| checks / codespell | flox-mirror | ubuntu-latest | cold | 50.6 | 4.2 |
| checks / codespell | flox-mirror | ubuntu-latest | warm | 53.6 | 3.2 |
| checks / commitlint | flox-mirror | ubuntu-latest | cold | 49.8 | 3.0 |
| checks / commitlint | flox-mirror | ubuntu-latest | warm | 53.4 | 1.9 |
| checks / gitleaks | flox-mirror | ubuntu-latest | cold | 53.6 | 4.7 |
| checks / gitleaks | flox-mirror | ubuntu-latest | warm | 51.8 | 3.2 |
| checks / pytest | flox-mirror | ubuntu-latest | cold | 55.4 | 6.3 |
| checks / pytest | flox-mirror | ubuntu-latest | warm | 52.8 | 2.8 |
| checks / ruff-check | flox-mirror | ubuntu-latest | cold | 52.2 | 3.7 |
| checks / ruff-check | flox-mirror | ubuntu-latest | warm | 51.4 | 3.4 |
| checks / ruff-format | flox-mirror | ubuntu-latest | cold | 50.2 | 3.9 |
| checks / ruff-format | flox-mirror | ubuntu-latest | warm | 51.4 | 2.1 |
| checks / taplo | flox-mirror | ubuntu-latest | cold | 49.0 | 1.3 |
| checks / taplo | flox-mirror | ubuntu-latest | warm | 53.2 | 2.9 |
| checks / ty | flox-mirror | ubuntu-latest | cold | 53.4 | 5.1 |
| checks / ty | flox-mirror | ubuntu-latest | warm | 55.8 | 4.5 |
| checks / yamllint | flox-mirror | ubuntu-latest | cold | 48.4 | 1.5 |
| checks / yamllint | flox-mirror | ubuntu-latest | warm | 51.4 | 4.5 |
| checks / bandit | traditional | ubuntu-latest | cold | 8.0 | 1.8 |
| checks / bandit | traditional | ubuntu-latest | warm | 10.8 | 0.4 |
| checks / codespell | traditional | ubuntu-latest | cold | 6.6 | 1.7 |
| checks / codespell | traditional | ubuntu-latest | warm | 7.4 | 1.5 |
| checks / commitlint | traditional | ubuntu-latest | cold | 9.4 | 1.2 |
| checks / commitlint | traditional | ubuntu-latest | warm | 9.0 | 1.4 |
| checks / gitleaks | traditional | ubuntu-latest | cold | 10.4 | 2.4 |
| checks / gitleaks | traditional | ubuntu-latest | warm | 7.2 | 1.2 |
| checks / pytest | traditional | ubuntu-latest | cold | 11.2 | 1.5 |
| checks / pytest | traditional | ubuntu-latest | warm | 11.6 | 1.9 |
| checks / ruff-check | traditional | ubuntu-latest | cold | 7.2 | 1.6 |
| checks / ruff-check | traditional | ubuntu-latest | warm | 6.8 | 1.0 |
| checks / ruff-format | traditional | ubuntu-latest | cold | 8.0 | 1.4 |
| checks / ruff-format | traditional | ubuntu-latest | warm | 7.4 | 1.4 |
| checks / taplo | traditional | ubuntu-latest | cold | 7.2 | 2.0 |
| checks / taplo | traditional | ubuntu-latest | warm | 8.0 | 1.3 |
| checks / ty | traditional | ubuntu-latest | cold | 7.2 | 1.2 |
| checks / ty | traditional | ubuntu-latest | warm | 8.4 | 2.2 |
| checks / yamllint | traditional | ubuntu-latest | cold | 8.0 | 1.7 |
| checks / yamllint | traditional | ubuntu-latest | warm | 8.2 | 1.6 |

## Charts

![total time](total_time.png)
