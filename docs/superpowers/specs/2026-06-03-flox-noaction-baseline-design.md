# Design: `flox-noaction` CI-provisioning baseline

**Date:** 2026-06-03
**Status:** approved (pending spec review)
**Branch (harness runtime):** `experiment/flox-ci-timing-perf-analysis`
**Related:** extends the flox-vs-traditional-vs-mise CI timing experiment
(`2026-05-30-flox-ci-timing-experiment-design.md`); follows the rollout pattern of
the merged `flox-nocache` work (PR #348).

## Problem

The CI-timing experiment compares provisioning strategies. All existing flox sides
install flox via `flox/install-flox-action@v2` (confirmed by git archaeology: the
action has been the sole install mechanism since the `provision-flox` composite's
first commit `073829a`; no alternative installer has ever existed in the experiment
or the profiling harness). The current `flox` vs `flox-nocache` A/B only toggles the
action's **flox-CLI-binary download cache** (`use-cache`). There is no measurement of
the cost of the **GitHub Action wrapper itself** — i.e. what installing flox *without*
the action looks like.

## Goal

Add a `flox-noaction` variant that installs flox by the official package-download
method (no GitHub Action), enabling a three-layer decomposition that attributes
savings to each layer independently:

| Config | Install | flox-binary cache | Isolates |
|--------|---------|-------------------|----------|
| `flox` (orig) | `flox/install-flox-action`, `use-cache=true` | cached | baseline |
| `flox-nocache` | `flox/install-flox-action`, `use-cache=false` | downloaded each run | the binary-cache layer (`flox` → `flox-nocache`) |
| `flox-noaction` (new) | manual `.deb`/`.pkg` download + install | downloaded each run | the action-wrapper layer (`flox-nocache` → `flox-noaction`) |

Each adjacent pair changes exactly one variable.

Two new sides (mirror + consolidated topologies):
`flox-noaction-mirror`, `flox-noaction-consolidated`.

## Non-goals

- Not changing the `flox` or `flox-nocache` sides (they remain exactly as-is).
- Not adding a package-manager path (apt-repo / `brew`); rejected because `brew`
  introduces its own update/index variance and is asymmetric with Ubuntu's `.deb`,
  which would conflate two variables in one arm.
- Not reverse-engineering the action's `dist/index.js`; the direct package install
  already reproduces what the action does internally (download flox package +
  install), minus the wrapper and its cache.

## Install method (approved: Approach A — direct package download + install, pinned)

Official flox install (no curl one-liner exists) is per-OS package install:

- **Ubuntu** (`x86_64-linux`):
  `curl -fsSL https://downloads.flox.dev/by-env/stable/deb/flox-<VER>.x86_64-linux.deb -o /tmp/flox.deb`
  then `sudo apt-get install -y /tmp/flox.deb`
- **macOS** (arch-detected; `macos-latest` is Apple Silicon → `aarch64-darwin`):
  `curl -fsSL https://downloads.flox.dev/by-env/stable/osx/flox-<VER>.<arch>-darwin.pkg -o /tmp/flox.pkg`
  then `sudo installer -pkg /tmp/flox.pkg -target /`
- Verify with `flox --version`.

**Pinned version `VER=1.12.2`** — the current stable release, which is exactly what
`flox/install-flox-action@v2` (`channel: stable`, no `version` pin) installs today, so
the A/B is version-matched. All three URLs verified resolvable (HTTP 200; `.deb`
81 MB, `aarch64 .pkg` 53 MB, `x86_64 .pkg` 57 MB) on 2026-06-03.

**Caveat — re-verify the pin before running.** If the matrix is run after stable
advances past 1.12.2, the action's `stable` would move while the pin stays, drifting
the comparison. Bump `VER` (and confirm the action's installed version) immediately
before any run.

## Components

### New: `.github/actions/provision-flox-noaction/action.yml`

Mirrors `provision-flox` with the install step replaced:

1. **Install Flox (no action — manual package install, pinned)** — `shell: bash`,
   per-OS `case "${{ runner.os }}"` as above, `set -euo pipefail`, `VER=1.12.2`
   hardcoded with a "bump before runs" comment.
2. **Cache Nix store** — `actions/cache@v4`, identical paths (`/nix`, `~/.cache/flox`)
   and cold/warm key logic as `provision-flox`, but with its **own key namespace**
   (`flox-noaction-${cache}-${os}-${hash}-…` and matching `restore-keys`) so it is
   measured independently and cannot cross-hit the action sides' caches. The flox CLI
   binary installs to a system path (`/usr/bin`), **outside** the cached paths, so the
   binary is re-downloaded every run by design (the point of "no action, no cache").
3. **Warm the flox env** — `flox activate -- true` (same as `provision-flox`).

Input: `cache: cold | warm` (required). No `use-cache` input (N/A without the action).

### New: `.github/workflows/flox-noaction-suite.yml`

Mirror caller (like `flox-nocache-suite.yml`): `workflow_dispatch` inputs `os`, `cache`;
calls `./.github/workflows/_checks.yml` with `provisioner: flox-noaction`.

### Modified: `.github/workflows/_checks.yml` (×10 jobs)

- Add a provision step gated `if: inputs.provisioner == 'flox-noaction'` that
  `uses: ./.github/actions/provision-flox-noaction` with `cache`. **Name it
  `provision (flox)`** so `collect.py`'s `SETUP_STEP_NAMES` substring-match captures it
  with no code change.
- Extend the per-job run `case` from `flox | flox-nocache)` to
  `flox | flox-nocache | flox-noaction)` (work commands are identical).

### New: `.github/workflows/flox-noaction-consolidated.yml`

Standalone (mirrors `flox-nocache-consolidated.yml`): self-contained `hygiene` + test
jobs, each `uses: ./.github/actions/provision-flox-noaction` directly (does not route
through `_checks.yml`). Contains ~3 `py_launch_blueprint` references.

### Modified: `.github/workflows/experiment-driver.yml`

- Add side→workflow mappings:
  `flox-noaction-mirror) wf="flox-noaction-suite"` and
  `flox-noaction-consolidated) wf="flox-noaction-consolidated"`.
- Update the `sides` input description to list the two new sides.

### Modified: `init/manifest.toml` (on the dispatch-to-main branch only)

Register `.github/workflows/flox-noaction-consolidated.yml` (~3×) under the
`package_name (text)` `[[replace]]` block and bump the header count. **This update
lands on the dispatch PR branch off `main`** (where `blueprint-guard` runs), starting
from main's current count — not on the experiment branch (the experiment branch is a
runtime, never merged to main, so its manifest is moot).

### Unchanged: `experiment/collect.py`

No change — `SETUP_STEP_NAMES = ("provision (flox)", …)` already substring-matches the
reused `provision (flox)` step name, capturing both the pre-step and the `Post …`
cache-save.

## Rollout (mirrors the flox-nocache pattern)

1. Build all components on `experiment/flox-ci-timing-perf-analysis`.
2. Lint locally (`yamllint`, `actionlint`).
3. Open a **dispatch-only PR to `main`** carrying the dispatchable entry workflows
   (`flox-noaction-suite.yml`, `flox-noaction-consolidated.yml`) plus the supporting
   files (composite, `_checks.yml`, driver, manifest). The two entry workflows must
   exist on `main` to be dispatchable by the driver; the harness still executes the
   branch versions via `--ref experiment/flox-ci-timing-perf-analysis`. Address review
   (incl. Copilot) and merge.
4. **Extended 1-rep ubuntu correctness gate**: re-run Stage 1 with sides =
   the four existing flox sides **plus** `flox-noaction-mirror,flox-noaction-consolidated`,
   `oses=ubuntu-latest caches=cold,warm reps=1`. Confirm all green — this validates the
   manual `.deb` install works on a real runner before spending the full ramp.
5. Continue the ramp: Stage 2 macOS 1-rep → Stage 3 full both-OS reps=5.
6. Post-data: fold the three-layer decomposition into `experiment/FINDINGS.md`, the
   figures (`summary.png`, `infographic.py`), and ADR-12 — **preserving the existing
   design decisions, references, and structure**.

## Testing

- **Static:** `yamllint -c .yamllint` + `actionlint` on every new/modified workflow;
  `provision-flox-noaction/action.yml` validates as a composite action.
- **Runtime correctness gate:** the extended ubuntu 1-rep stage (step 4 above) is the
  acceptance test — `flox-noaction` cells must conclude `success` (manual install +
  `flox activate` works) before the full matrix runs.
- **Data integrity:** driver excludes non-success runs from samples (unchanged);
  `collect.py` captures `flox-noaction` timings via the reused step name.

## Risks & mitigations

- **Version drift** (pin vs action's `stable`): re-verify/bump `VER` immediately before
  any run (see caveat above).
- **macOS arch:** `macos-latest` is Apple Silicon → `aarch64-darwin`; arch is detected
  at runtime via `uname -m` (`arm64` → `aarch64`) rather than assumed, so an Intel
  runner would still resolve correctly.
- **`sudo` availability:** GitHub-hosted ubuntu/macos runners provide passwordless
  `sudo`; `apt-get install` and `installer` both require it (same as standard CI).
- **Cache cross-contamination:** avoided by the dedicated `flox-noaction-` cache key
  namespace.
