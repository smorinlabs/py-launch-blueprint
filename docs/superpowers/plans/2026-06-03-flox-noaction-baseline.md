# flox-noaction Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `flox-noaction` CI-provisioning variant that installs flox by direct package download (no GitHub Action), enabling a three-layer decomposition (`flox` → `flox-nocache` → `flox-noaction`).

**Architecture:** A new `provision-flox-noaction` composite mirrors `provision-flox` but replaces the `flox/install-flox-action` step with a pinned per-OS `.deb`/`.pkg` download+install, and uses its own Nix-store cache namespace. Two new dispatch workflows (`flox-noaction-suite` mirror caller + `flox-noaction-consolidated` standalone) and driver mappings wire it into the existing harness. The reused `provision (flox)` step name keeps `collect.py` working unchanged.

**Tech Stack:** GitHub Actions (composite + reusable + dispatch workflows), bash, flox 1.12.2 (pinned), `actionlint`, `yamllint`. Spec: `docs/superpowers/specs/2026-06-03-flox-noaction-baseline-design.md`.

**Branches:** build on `experiment/flox-ci-timing-perf-analysis` (harness runtime); a separate dispatch-only PR off `main` makes the entry workflows dispatchable.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `.github/actions/provision-flox-noaction/action.yml` | Create | Manual pinned flox install + namespaced Nix cache + warm activate |
| `.github/workflows/flox-noaction-suite.yml` | Create | Mirror-topology dispatch caller → `_checks.yml` (provisioner=flox-noaction) |
| `.github/workflows/flox-noaction-consolidated.yml` | Create | Consolidated-topology standalone dispatch workflow |
| `.github/workflows/_checks.yml` | Modify | Add flox-noaction provision step + run-case arm (×10 jobs via 2 replace_all) |
| `.github/workflows/experiment-driver.yml` | Modify | Side→workflow mappings + `sides` description |
| `init/manifest.toml` | Modify (dispatch branch only) | Register `flox-noaction-consolidated.yml` for blueprint-guard |

---

## Task 1: `provision-flox-noaction` composite

**Files:**
- Create: `.github/actions/provision-flox-noaction/action.yml`
- Reference (do not edit): `.github/actions/provision-flox/action.yml`

- [ ] **Step 1: Create the composite action**

Create `.github/actions/provision-flox-noaction/action.yml` with exactly:

```yaml
name: provision-flox-noaction
description: Install Flox via direct package download (no GitHub Action) and restore/save the Nix store cache.
inputs:
  cache:
    description: cold | warm
    required: true
runs:
  using: composite
  steps:
    - name: Install Flox (no action — manual package install, pinned)
      shell: bash
      run: |
        set -euo pipefail
        # Pinned to current stable; matches what flox/install-flox-action installs
        # today. BUMP before running if stable advances past this (see spec caveat).
        VER=1.12.2
        case "${{ runner.os }}" in
          Linux)
            url="https://downloads.flox.dev/by-env/stable/deb/flox-${VER}.x86_64-linux.deb"
            curl -fsSL "$url" -o /tmp/flox.deb
            sudo apt-get install -y /tmp/flox.deb
            ;;
          macOS)
            case "$(uname -m)" in
              arm64 | aarch64) a=aarch64-darwin ;;
              *) a=x86_64-darwin ;;
            esac
            url="https://downloads.flox.dev/by-env/stable/osx/flox-${VER}.${a}.pkg"
            curl -fsSL "$url" -o /tmp/flox.pkg
            sudo installer -pkg /tmp/flox.pkg -target /
            ;;
          *)
            echo "unsupported runner.os: ${{ runner.os }}" >&2
            exit 1
            ;;
        esac
        # Match install-flox-action: avoid first-run metrics prompt/behavior in CI.
        flox config --set disable_metrics true
        flox --version
    - name: Cache Nix store
      uses: actions/cache@v4
      with:
        path: |
          /nix
          ~/.cache/flox
        # Own namespace (flox-noaction-) so it is measured independently and cannot
        # cross-hit the action sides' caches. cold -> unique key (guaranteed miss);
        # warm -> stable key per lock+os.
        key: >-
          flox-noaction-${{ inputs.cache }}-${{ runner.os }}-${{ hashFiles('.flox/env/manifest.lock') }}-${{
            inputs.cache == 'cold' && github.run_id || 'stable' }}
        restore-keys: |
          ${{ inputs.cache == 'warm' && format('flox-noaction-warm-{0}-{1}-stable', runner.os, hashFiles('.flox/env/manifest.lock')) || 'flox-never-restore' }}
    - name: Warm the flox env
      shell: bash
      run: flox activate -- true
```

- [ ] **Step 2: Lint the composite**

Run: `flox activate -- actionlint .github/actions/provision-flox-noaction/action.yml`
Expected: no output, exit 0. (actionlint validates composite-action shell scripts.)

If actionlint reports shellcheck issues on the embedded script, fix them; the script above is `set -euo pipefail`-clean and quotes all expansions.

- [ ] **Step 3: Commit**

```bash
git add .github/actions/provision-flox-noaction/action.yml
git commit -m "feat(experiment): add provision-flox-noaction composite (manual pinned install)"
```

---

## Task 2: `flox-noaction-suite` mirror caller

**Files:**
- Create: `.github/workflows/flox-noaction-suite.yml`
- Reference (do not edit): `.github/workflows/flox-nocache-suite.yml`

- [ ] **Step 1: Create the suite workflow**

Create `.github/workflows/flox-noaction-suite.yml` with exactly:

```yaml
name: flox-noaction-suite
on:
  workflow_dispatch:
    inputs:
      os:
        type: string
        required: true
      cache:
        type: string
        required: true

permissions:
  contents: read

jobs:
  checks:
    uses: ./.github/workflows/_checks.yml
    with:
      provisioner: flox-noaction
      os: ${{ inputs.os }}
      cache: ${{ inputs.cache }}
```

- [ ] **Step 2: Lint**

Run: `flox activate -- actionlint .github/workflows/flox-noaction-suite.yml`
Expected: no output, exit 0.

(`actionlint` may warn that `_checks.yml` does not yet accept `provisioner: flox-noaction` only via value checks — it does not validate input *values*, so this passes. Task 3 makes `_checks.yml` handle the value.)

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/flox-noaction-suite.yml
git commit -m "feat(experiment): add flox-noaction-suite mirror caller"
```

---

## Task 3: Wire `flox-noaction` into `_checks.yml`

**Files:**
- Modify: `.github/workflows/_checks.yml` (10 jobs; two `replace_all` edits)

The flox provision block and the run-case prefix are byte-identical across all 10 jobs, so each edit is a single `replace_all`.

- [ ] **Step 1: Add the flox-noaction provision step to every job (replace_all)**

Replace this exact block (appears 10×):

```yaml
      - name: provision (flox)
        if: inputs.provisioner == 'flox' || inputs.provisioner == 'flox-nocache'
        uses: ./.github/actions/provision-flox
        with:
          cache: ${{ inputs.cache }}
          use-cache: ${{ inputs.provisioner == 'flox-nocache' && 'false' || 'true' }}
```

with (note: second step reuses the name `provision (flox)` so collect.py captures it):

```yaml
      - name: provision (flox)
        if: inputs.provisioner == 'flox' || inputs.provisioner == 'flox-nocache'
        uses: ./.github/actions/provision-flox
        with:
          cache: ${{ inputs.cache }}
          use-cache: ${{ inputs.provisioner == 'flox-nocache' && 'false' || 'true' }}
      - name: provision (flox)
        if: inputs.provisioner == 'flox-noaction'
        uses: ./.github/actions/provision-flox-noaction
        with:
          cache: ${{ inputs.cache }}
```

Use Edit with `replace_all: true`.

- [ ] **Step 2: Extend the run-case arm to every job (replace_all)**

Replace this exact string (appears 10×):

```
            flox | flox-nocache)
```

with:

```
            flox | flox-nocache | flox-noaction)
```

Use Edit with `replace_all: true`.

- [ ] **Step 3: Verify counts**

Run:
```bash
grep -c "provisioner == 'flox-noaction'" .github/workflows/_checks.yml
grep -c "flox | flox-nocache | flox-noaction)" .github/workflows/_checks.yml
```
Expected: `10` and `10`.

- [ ] **Step 4: Lint**

Run: `flox activate -- actionlint .github/workflows/_checks.yml`
Expected: no output, exit 0.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/_checks.yml
git commit -m "feat(experiment): handle flox-noaction provisioner in _checks.yml"
```

---

## Task 4: `flox-noaction-consolidated` standalone

**Files:**
- Create: `.github/workflows/flox-noaction-consolidated.yml`
- Reference (do not edit): `.github/workflows/flox-nocache-consolidated.yml`

- [ ] **Step 1: Create the consolidated workflow**

Create `.github/workflows/flox-noaction-consolidated.yml` with exactly:

```yaml
name: flox-noaction-consolidated
on:
  workflow_dispatch:
    inputs:
      os:
        type: string
        required: true
      cache:
        type: string
        required: true

permissions:
  contents: read

# Same as flox-consolidated, but flox is installed by direct package download
# (no flox/install-flox-action — A/B against flox-consolidated / flox-nocache-consolidated).

jobs:
  hygiene:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - name: provision (flox)
        uses: ./.github/actions/provision-flox-noaction
        with:
          cache: ${{ inputs.cache }}
      - name: all hygiene checks under one activation
        shell: bash
        run: |
          flox activate -- bash -euo pipefail -c '
            ruff check .
            ruff format --check .
            uv sync --group dev && uv run ty check py_launch_blueprint/
            taplo check "**/*.toml"
            codespell --toml pyproject.toml
            yamllint -c .yamllint .
            bandit -r py_launch_blueprint/ -c pyproject.toml
            gitleaks detect --source . --config .gitleaks.toml --no-banner
            commitlint --from=HEAD~10 --to=HEAD
          '

  pytest:
    runs-on: ${{ inputs.os }}
    steps:
      - uses: actions/checkout@v6
      - name: provision (flox)
        uses: ./.github/actions/provision-flox-noaction
        with:
          cache: ${{ inputs.cache }}
      - name: tests under one activation
        shell: bash
        run: flox activate -- bash -c 'uv sync --group dev && uv run pytest -m "" --cov=py_launch_blueprint --cov-report=xml'
```

- [ ] **Step 2: Lint**

Run: `flox activate -- actionlint .github/workflows/flox-noaction-consolidated.yml`
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/flox-noaction-consolidated.yml
git commit -m "feat(experiment): add flox-noaction-consolidated standalone"
```

---

## Task 5: Driver mappings + `sides` description

**Files:**
- Modify: `.github/workflows/experiment-driver.yml`

- [ ] **Step 1: Add side→workflow mappings**

Replace:

```
              flox-nocache-consolidated) wf="flox-nocache-consolidated" ;;
              *) echo "unknown side: $side" >&2; exit 1 ;;
```

with:

```
              flox-nocache-consolidated) wf="flox-nocache-consolidated" ;;
              flox-noaction-mirror) wf="flox-noaction-suite" ;;
              flox-noaction-consolidated) wf="flox-noaction-consolidated" ;;
              *) echo "unknown side: $side" >&2; exit 1 ;;
```

- [ ] **Step 2: Update the `sides` input description**

Replace:

```
        description: comma-separated subset of traditional,flox-mirror,flox-consolidated,mise-mirror,mise-consolidated,flox-nocache-mirror,flox-nocache-consolidated
```

with:

```
        description: comma-separated subset of traditional,flox-mirror,flox-consolidated,mise-mirror,mise-consolidated,flox-nocache-mirror,flox-nocache-consolidated,flox-noaction-mirror,flox-noaction-consolidated
```

- [ ] **Step 3: Lint**

Run: `flox activate -- actionlint .github/workflows/experiment-driver.yml`
Expected: no output, exit 0.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/experiment-driver.yml
git commit -m "feat(experiment): map flox-noaction sides in experiment-driver"
```

---

## Task 6: Full local validation sweep + push experiment branch

**Files:** none modified (verification only)

- [ ] **Step 1: actionlint the whole `.github` tree**

Run: `flox activate -- actionlint`
Expected: no output, exit 0 (lints every workflow + composite action).

- [ ] **Step 2: yamllint the new/changed workflows**

Run:
```bash
flox activate -- yamllint -c .yamllint \
  .github/actions/provision-flox-noaction/action.yml \
  .github/workflows/flox-noaction-suite.yml \
  .github/workflows/flox-noaction-consolidated.yml \
  .github/workflows/_checks.yml \
  .github/workflows/experiment-driver.yml
```
Expected: no output, exit 0.

- [ ] **Step 3: codespell guard (the earlier blocker)**

Run: `flox activate -- codespell --toml pyproject.toml`
Expected: exit 0 (no new typos introduced).

- [ ] **Step 4: Push the experiment branch**

```bash
git push origin experiment/flox-ci-timing-perf-analysis
```
Expected: push succeeds.

---

## Task 7: Dispatch-only PR to `main`

**Files (on a new branch off `main`):**
- Add: the five files from Tasks 1–5 (copied verbatim from the experiment branch)
- Modify: `init/manifest.toml`

This mirrors the merged flox-nocache dispatch PR (`e7cdfd6`). The entry workflows must exist on `main` to be dispatchable by the driver.

- [ ] **Step 1: Branch off main and copy the exact files**

```bash
git fetch origin main
git switch -c ci/flox-noaction-dispatch origin/main
git checkout experiment/flox-ci-timing-perf-analysis -- \
  .github/actions/provision-flox-noaction/action.yml \
  .github/workflows/flox-noaction-suite.yml \
  .github/workflows/flox-noaction-consolidated.yml \
  .github/workflows/_checks.yml \
  .github/workflows/experiment-driver.yml
```

- [ ] **Step 2: Register the consolidated workflow in the manifest**

Inspect the current `package_name (text)` block header and file list:
```bash
grep -n "package_name (text)" init/manifest.toml
grep -n "flox-nocache-consolidated.yml" init/manifest.toml
```

`flox-noaction-consolidated.yml` contains 3 `py_launch_blueprint` occurrences (confirm with `grep -c py_launch_blueprint .github/workflows/flox-noaction-consolidated.yml`). Add this line to the `package_name (text)` `[[replace]]` `files` list, immediately after the `flox-nocache-consolidated.yml` entry:

```
  ".github/workflows/flox-noaction-consolidated.yml",   # 3x
```

Then bump the block's header counts by +3 occurrences and +1 file (e.g. `N occurrences in M files` → `N+3 occurrences in M+1 files`), using the values you just read.

- [ ] **Step 3: Verify manifest coverage**

Run: `flox activate -- uv run init/discover.py --summary 2>/dev/null | tail -20` (if available), or confirm the file is listed:
```bash
grep -c "flox-noaction-consolidated.yml" init/manifest.toml
```
Expected: `1`.

- [ ] **Step 4: Commit and push**

```bash
git add .github/ init/manifest.toml
git commit -m "ci: add dispatch-only flox-noaction workflows + register manifest"
git push -u origin ci/flox-noaction-dispatch
```

- [ ] **Step 5: Open the PR**

```bash
gh pr create --base main --head ci/flox-noaction-dispatch \
  --title "ci: add dispatch-only flox-noaction workflows" \
  --body "Adds dispatch-only flox-noaction workflows (manual pinned flox install, no GitHub Action) to main so the driver can dispatch them. workflow_dispatch-only; no change to normal CI. Harness runs from experiment/flox-ci-timing-perf-analysis via --ref. Third layer of the flox decomposition: flox (action+cache) -> flox-nocache (action, no binary cache) -> flox-noaction (no action)."
```

- [ ] **Step 6: Address review (incl. Copilot) and merge**

Per project rule (memory: review-pr-comments-before-merge): fetch and resolve all review comments, including Copilot, before merging. Then:
```bash
gh pr merge --squash --auto
```
Wait for the merge queue to land it on `main`.

---

## Task 8: Extended ubuntu 1-rep correctness gate

**Files:** none (runtime acceptance test)

This is the acceptance test for the whole feature: the manual `.deb` install must work on a real runner before the full ramp.

- [ ] **Step 1: Re-verify the version pin is still current stable**

```bash
gh api repos/flox/flox/releases/latest -q '.tag_name'
```
If this is no longer `v1.12.2`, update `VER` in `provision-flox-noaction/action.yml` on BOTH the experiment branch and `main` (push both), then continue.

- [ ] **Step 2: Dispatch the extended Stage 1 (all 6 flox sides, ubuntu, 1 rep)**

```bash
gh workflow run experiment-driver.yml --ref experiment/flox-ci-timing-perf-analysis \
  -f sides=flox-noaction-mirror,flox-noaction-consolidated,flox-nocache-mirror,flox-nocache-consolidated,flox-mirror,flox-consolidated \
  -f oses=ubuntu-latest -f caches=cold,warm -f reps=1
```
Capture the new driver run id (snapshot-before/after, as the driver itself does).

- [ ] **Step 3: Wait for the driver and verify all child runs green**

```bash
gh run watch <DRIVER_ID> --exit-status
gh run list --branch experiment/flox-ci-timing-perf-analysis --event workflow_dispatch --limit 20 \
  --json workflowName,conclusion -q '.[] | select(.workflowName | startswith("flox-noaction")) | .conclusion'
```
Expected: the driver concludes `success` and every `flox-noaction-*` child is `success`. If a flox-noaction cell fails, inspect `gh run view <id> --log-failed` — the likely culprit is the install step (URL/arch/sudo) or the first-run metrics behavior; fix in the composite and re-run this task.

- [ ] **Step 4: Download the run-ids artifact (first data point)**

```bash
gh run download <DRIVER_ID> -n experiment-run-ids -D /tmp/noaction-stage1
cat /tmp/noaction-stage1/run-ids.json
```
Confirm non-empty arrays for the `flox-noaction|*` tags.

---

## Task 9: Continue the ramp (Stage 2 → Stage 3)

**Files:** none (runtime)

Only proceed once Task 8 is fully green.

- [ ] **Step 1: Stage 2 — macOS 1-rep (all 6 flox sides)**

```bash
gh workflow run experiment-driver.yml --ref experiment/flox-ci-timing-perf-analysis \
  -f sides=flox-noaction-mirror,flox-noaction-consolidated,flox-nocache-mirror,flox-nocache-consolidated,flox-mirror,flox-consolidated \
  -f oses=macos-latest -f caches=cold,warm -f reps=1
```
Watch to completion; verify all `flox-noaction-*` macOS children are `success` (validates the `.pkg` install + arch detection on Apple Silicon).

- [ ] **Step 2: Stage 3a — full ubuntu reps=5**

```bash
gh workflow run experiment-driver.yml --ref experiment/flox-ci-timing-perf-analysis \
  -f sides=flox-noaction-mirror,flox-noaction-consolidated,flox-nocache-mirror,flox-nocache-consolidated,flox-mirror,flox-consolidated \
  -f oses=ubuntu-latest -f caches=cold,warm -f reps=5
```
Watch to completion; download `experiment-run-ids`.

- [ ] **Step 3: Stage 3b — full macOS reps=5**

```bash
gh workflow run experiment-driver.yml --ref experiment/flox-ci-timing-perf-analysis \
  -f sides=flox-noaction-mirror,flox-noaction-consolidated,flox-nocache-mirror,flox-nocache-consolidated,flox-mirror,flox-consolidated \
  -f oses=macos-latest -f caches=cold,warm -f reps=5
```
(Split per-OS to stay under the driver's 350-min cap.) Watch to completion; download `experiment-run-ids`.

- [ ] **Step 4: Merge run-id sets and analyze**

Merge the Stage 3 run-ids JSON with the existing experiment data, then:
```bash
flox activate -- uv run experiment/analyze.py --live
```
Confirm `flox-noaction` rows appear with timings for all OS/cache cells.

---

## Task 10: Fold results into FINDINGS, figures, ADR-12

**Files:**
- Modify: `experiment/FINDINGS.md`
- Modify: `experiment/results/REPORT.md`
- Modify: `experiment/visualize.py`, `experiment/infographic.py` (extend to include flox-noaction)
- Modify: `docs/adr/0012-flox-environment-management.md`
- Regenerate: `summary.png`, `provisioning_infographic.png`

- [ ] **Step 1: Add the three-layer decomposition to FINDINGS.md**

Add a subsection presenting `flox` → `flox-nocache` → `flox-noaction` deltas (binary-cache layer vs action-wrapper layer), per OS and cold/warm. **Preserve all existing experiment design decisions, references, and structure** (the provisioner-parameterized harness, mirror vs consolidated topology, cold/warm cache keying, setup-vs-work split). Add, do not rewrite.

- [ ] **Step 2: Extend the figure generators**

Add `flox-noaction-mirror` and `flox-noaction-consolidated` series to `experiment/visualize.py` and `experiment/infographic.py`, following the existing per-side styling. Regenerate:
```bash
flox activate -- uv run experiment/visualize.py
flox activate -- uv run experiment/infographic.py
```

- [ ] **Step 3: Update ADR-12**

Fold the action-wrapper finding into ADR-12's empirical evidence section. **Preserve** ADR-12's structure (Buckets 1–4, the governing principle "Flox provides binaries; uv.lock/bun.lock own dependency closures", migration delta, status `proposed`). Add the new data point; do not restructure.

- [ ] **Step 4: Commit**

```bash
git add experiment/ docs/adr/0012-flox-environment-management.md summary.png provisioning_infographic.png
git commit -m "docs(experiment): fold flox-noaction (3-layer decomposition) into findings, figures, ADR-12"
git push origin experiment/flox-ci-timing-perf-analysis
```

---

## Notes for the implementer

- **Dogfooding:** run every tool via `flox activate -- <cmd>` (flox packages are only on PATH after activation).
- **Driver stdout hygiene:** `gh workflow run` prints the run URL to stdout; redirect with `1>&2` when capturing run ids.
- **No silent truncation:** if any rep is excluded (non-success), the driver logs a WARN — check the driver log, don't assume full coverage.
- **collect.py is intentionally untouched** — the reused `provision (flox)` step name is load-bearing; do not rename the flox-noaction provision steps.
