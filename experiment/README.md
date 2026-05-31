# Flox vs Traditional CI timing experiment

## What this is
Measures CI provisioning time: traditional vs flox-mirror vs flox-consolidated,
across ubuntu/macOS, cold/warm cache, 5 reps. See
`docs/superpowers/specs/2026-05-30-flox-ci-timing-experiment-design.md`.

## Validation gates (run in order)

### Gate 1 — harness (no Actions minutes)
    flox activate -- uv run --script experiment/analyze.py \
      --fixture experiment/fixtures/synthetic_runs.json --out /tmp/exp-out
Confirm /tmp/exp-out has REPORT.md (populated tables) and total_time.png.

### Gate 2 — correctness smoke (6 runs)
Push the branch, then for each side x os, one cold run:
    gh workflow run trad-suite.yml --ref experiment/flox-ci-timing -f os=ubuntu-latest -f cache=cold
    gh workflow run flox-mirror-suite.yml --ref experiment/flox-ci-timing -f os=ubuntu-latest -f cache=cold
    gh workflow run flox-consolidated.yml --ref experiment/flox-ci-timing -f os=ubuntu-latest -f cache=cold
    # repeat with os=macos-latest
Confirm ALL jobs are green (equivalent checks pass) before timing.

### Gate 3 — full experiment
Run the driver per OS to stay under the job time limit:
    gh workflow run experiment-driver.yml --ref experiment/flox-ci-timing -f oses=ubuntu-latest
    gh workflow run experiment-driver.yml --ref experiment/flox-ci-timing -f oses=macos-latest
Download the run-ids artifact from each driver run, merge into run-ids.json, then:
    flox activate -- uv run --script experiment/analyze.py --live \
      --repo smorinlabs/py-launch-blueprint --run-ids run-ids.json \
      --out experiment/results
Commit experiment/results/ (REPORT.md, charts, raw data).
