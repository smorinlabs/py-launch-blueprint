# `init/tests/integration/` — L1 + L2 integration runner

One bash script (`run-mode.sh`) + one static answers file (`answers.toml`).
Drives the full end-to-end pipeline for any of the five §4.7 instantiation
modes against a fresh copy of the blueprint, in a tmp directory.

## What it asserts per mode

| Layer | Assertion | Run for modes |
|---|---|---|
| **L1 — Contract** | Guard fires on un-migrated tree, init exit code matches §4.7, marker present/absent as mandated. | All 5 |
| **L2 — Outcome** | After `init`: `uv sync --group dev`, `uv run pytest`, `uv build`, install wheel + run CLI command, `init-doctor` reports no errors. | 1-4 (ZIP refuses init, no L2 to verify) |
| **Mode #4 extra** | Contributor sentinel silences the guard. | 4 (fork) only |

## Run locally

```bash
MODE=template_button bash init/tests/integration/run-mode.sh
MODE=fork            bash init/tests/integration/run-mode.sh
# ...etc — any of: template_button | gh_template | clone_reinit | fork | zip
```

Each invocation creates a fresh `mktemp` fixture, so runs are independent
and parallelizable. ZIP completes in seconds (no L2); the others take
~60-90s locally (~2-3min in CI before cache warmup).

## How CI uses it

`.github/workflows/init-integration.yml` runs all 5 modes as a matrix.

Triggers:
- **PR** with changes to `init/**`, `Justfile`, `pyproject.toml`, `package.json`, or any lockfile (paths-filtered — silent on doc-only PRs)
- **Push to main** with the same paths filter
- **Cron — Mon 09:00 UTC** — catches drift from `uv` / `just` / `bun` / PyPI releases that wouldn't surface in any PR
- **Manual** via workflow_dispatch

`fail-fast: false` so a single mode failure doesn't hide others. An
`integration-ok` aggregator job lets branch protection require one check
name instead of five.

## Cron cadence review

Re-evaluate weekly cadence after 3 months of signal:
- Green for 3 months → relax to monthly
- Catching real regressions → keep weekly
- Flaky → fix the flake, don't relax cadence (a habitually-failing weekly
  cron trains the team to ignore CI)
