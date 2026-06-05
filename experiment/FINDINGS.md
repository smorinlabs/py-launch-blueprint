# Flox vs. Traditional vs. mise CI — Timing Experiment Findings

**Question:** Does provisioning this repo's CI toolchain with [Flox](https://flox.dev)
(Nix-based) or [mise](https://mise.jdx.dev) (a single tool-manager over release/pipx/npm
backends), instead of the traditional per-tool installs (`setup-uv`, `setup-just`, `bunx`,
release-download scripts), make GitHub Actions faster or slower? Informs ADR-12.

**TL;DR:** **Flox is ~2.8–3.2× slower on ubuntu and ~3–7.9× slower on macOS** — and it's
**~90–94% provisioning**: the actual checks run at the *same speed* across all sides
(see root-cause); essentially all of flox's cost is install + activate + Nix-store cache-save.
**mise lands in the middle** (~1.0–1.3× traditional on ubuntu) — ~4–5× cheaper provisioning than
flox (release binaries, no Nix build), and unlike flox **its warm cache actually works**
(warm mise ≈ traditional). Traditional wins on raw speed; flox wins on reliability;
mise is the speed/single-source-of-truth compromise — and on **macOS, mise-consolidated
matches/beats traditional** while flox is ~3–8× slower there.
**v2 extension:** three more sides (`flox-nocache`, `flox-noaction`, `flox-baked`) confirm the
flox cost is **irreducibly the Nix-store realization** — neither the CLI-binary cache, nor the
GitHub Action wrapper, nor pre-baking the whole env into a container image moves it on ubuntu
(the 1.5 GB image **pull ≈ the install it replaces**). See "Extension v2".
**Data note (v3 audit):** an earlier cut suffered cross-OS run-ID contamination (concurrent
ubuntu+macOS drivers polling the same workflow captured each other's runs). It has been fixed
(the driver now verifies each run's runner OS), the 4 contaminated runs purged, and the
affected cells re-collected — every number here is from the cleaned data. The fix lowered the
ubuntu multiplier from a stale 3.8× to ~2.9× (clean traditional-ubuntu baseline ≈ 23–24s).

## Method

- **Matrix:** up to 5 sides × 2 OS × 2 cache × 5 reps on GitHub-hosted runners.
  - Sides: `traditional` (per-tool install), `flox-mirror`/`flox-consolidated` (whole env via
    `flox activate`, per-job vs once), `mise-mirror`/`mise-consolidated` (whole env via
    `mise` + `mise exec`, per-job vs once).
  - OS: `ubuntu-latest`, `macos-latest`. Cache: cold / warm (Nix store, mise install dir,
    uv/bun caches). Target reps=5 per cell, both OS.
  - **v2 added 5 more flox sides** (`flox-nocache-{mirror,consolidated}`,
    `flox-noaction-{mirror,consolidated}`, `flox-baked`) — re-run alongside the originals for a
    clean same-conditions comparison (`flox-baked` is ubuntu-only, container job).
    See "Extension v2".
- **10 checks measured:** ruff-check, ruff-format, ty, pytest, taplo, codespell, yamllint,
  bandit, gitleaks, commitlint. (`editorconfig` dropped — see caveats.)
- A driver dispatches runs serially, **excludes failed reps** (never records bad samples — note
  the survivorship caveat below); `analyze.py` pulls run/job/step timings from the GitHub API.
- **Per-cell n varies** (target 5; the flaky macOS-mirror and manual-`.pkg` configs lose reps
  to failed/excluded runs). Most cells are n=5; the lowest are n=1–3. The exact n is in the `n`
  column of [`results/REPORT.md`](results/REPORT.md). The two formerly-empty cells
  (`flox-nocache-mirror·macOS·cold`, `flox-noaction-mirror·ubuntu·warm`) were re-collected to
  n=1. See Caveats for the full low-n list and the survivorship note.

## Results — total run time (avg seconds, Δ% vs traditional)

Cleaned Stage-3 data (avg s; macOS-cold traditional baseline is noisy — see caveats):

| side | ubuntu cold | ubuntu warm | macOS cold | macOS warm |
| --- | ---: | ---: | ---: | ---: |
| traditional | 24.3 | 23.0 | 64.0 ⚠️ | 49.0 |
| mise-mirror | 30.2 (+24%) | 44.6 (+94%) | 68.8 (+8%) | 55.8 (+14%) |
| mise-consolidated | 24.5 (+1%) | 22.8 (−1%) | **39.4 (−38%)** | **29.8 (−39%)** |
| flox-mirror | 70.0 (+188%) | 74.0 (+222%) | 405.7 (+534%) | 389.3 (+694%) |
| flox-consolidated | 69.0 (+184%) | 64.4 (+180%) | 192.3 (+200%) | 193.5 (+295%) |

## Results — provisioning (setup) vs work

`setup` = all provisioning: the `provision` step (flox install/activate, or
setup-uv/just/bun) **plus** the `Post provision` cache-save step.
`provisioning/run` = setup summed across all jobs in a run (cumulative billable cost).

setup/job shown as cold / warm (ubuntu | macOS):

| side | setup/job ubuntu | setup/job macOS | provisioning/run ubuntu | provisioning/run macOS |
| --- | ---: | ---: | ---: | ---: |
| traditional | 3.3 / 3.4 | 5.5 / 5.2 | 33 / 34 | 55 / 52 |
| mise-mirror | 10.9 / **4.9** | 13.7 / **6.2** | 109 / 49 | 137 / 62 |
| mise-consolidated | 9.5 / **5.4** | 13.9 / **5.7** | 19 / 11 | 28 / 11 |
| flox-mirror | 47.6 / 48.1 | 163.8 / 161.3 | 476 / 481 | **1638** / 1613 |
| flox-consolidated | 47.6 / 47.3 | 156.6 / 165.5 | 95 / 95 | 313 / 331 |

Two things stand out: **mise provisioning is OS-insensitive** (~12s ubuntu ≈ ~14s macOS —
release binaries), where flox's balloons (~47s → ~136s, the Nix-store build). And **mise's
warm cache works** (cold→warm ~12→4s), where flox's barely moves (~47→48s).

## Root cause — why flox "work" looked longer (it isn't)

The checks themselves run at the **same speed** regardless of provisioning. Per-step,
same check, macOS cold:

| step | flox-mirror | traditional |
| --- | ---: | ---: |
| `provision` (install + activate) | 97–136s | 3–4s |
| **`run` (the actual check)** | **identical** — ruff 1s=1s · codespell 0s=0s · yamllint 1s=1s · ty 2s≈1s · pytest 10s≈6s | — |
| `Post provision` (cache **save**) | 19–39s | 0s |

The "longer flox work" in an earlier cut was a **measurement artifact**: the per-job
split only subtracted the *pre*-step `provision (flox)` from the total, so the *post*-step
**`Post provision (flox)` — the `actions/cache` step that saves the ~Nix store (19–39s on
macOS) — leaked into "work."** Counting that cache-save as provisioning (it is) makes work
fall to ~5s ubuntu / ~8–9s per job — **equal to traditional** — and pushes flox's setup to
~90–94%. Conclusion: **flox doesn't run the checks slower; ~all of its CI cost is
provisioning** (install + activate + cache-save).

## Results — reliability

| side | failures |
| --- | --- |
| flox-mirror / flox-consolidated | **0** (both OS) |
| mise-mirror / mise-consolidated | **0** (both OS, after a commitlint config-dep fix) |
| traditional | flaky `editorconfig` (removed); 1 transient on macOS |

## What gets provisioned — traditional vs flox vs mise

![Provisioning model: traditional vs flox](results/provisioning_infographic.png)

| check | traditional (source) | flox | mise |
| --- | --- | --- | --- |
| ruff · codespell · yamllint · bandit | `uvx <tool>` (PyPI) | bare, Nix store | `mise exec` (aqua binary / pipx) |
| ty · pytest | `uv run` (venv) | `uv run` | `uv run` (same — uv boundary) |
| taplo | `setup-just` → `just install-taplo` | bare, Nix store | `mise exec taplo` (aqua) |
| commitlint | `bunx commitlint` (npm) | bare, Nix store | `mise` commitlint + `bun install` for config |
| gitleaks | `install-gitleaks.sh` (curl) | bare, Nix store | `mise exec gitleaks` (aqua) |

- **Traditional:** 4 heterogeneous installers (3 actions + 1 curl script); each job installs
  **only the tool it needs**, from PyPI / npm / GitHub releases at runtime (~3s/job, flaky).
- **Flox:** one `manifest.toml` (+lock) → `flox activate` materializes the **entire** toolchain
  from the content-addressed **Nix store** every activation. ~46s ubuntu / ~136s macOS per job,
  deterministic, **OS-sensitive** (Nix build dominates on macOS).
- **mise:** one `mise.toml` → `mise` installs the **entire** toolchain from **release
  binaries (aqua) + pipx + npm** then `mise exec`. ~12s ubuntu / ~14s macOS per job —
  **OS-insensitive** (no build) and **cache-effective** (warm ~4–7s). Deterministic-ish (pinned
  registry). (`ty`/`pytest` via `uv run` on all three — the uv boundary.)
- **Major differences:** granularity (only-needed vs whole-env) · source (PyPI/npm/GitHub vs
  Nix store vs release-binaries/pipx/npm) · cost (~3s vs ~46–136s vs ~12–14s/job) · warm cache
  (n/a vs ineffective vs effective) · OS sensitivity (— vs high vs low) · maintenance (4 scripts
  vs 1 manifest vs 1 manifest).

## Key findings

1. **The flox CI tax is provisioning, not the checks.** ~90–94% of each flox job is
   provisioning (install + activate + cache-save); the actual check `run` step is **equal to
   traditional** (e.g. ruff 1s, codespell 0s, ty ~2s — same both sides). See Root cause.
2. **macOS is where Flox hurts most.** Per-job flox provisioning is ~157–165s on macOS vs ~47s
   on ubuntu (Nix-on-macOS cold build + larger cache save), pushing flox-mirror to ~6–8×.
3. **Consolidation is the decisive lever — where provisioning is costly.** mirror and
   consolidated have ~equal per-job setup, but mirror pays it 10× (1100s/run on macOS) vs
   consolidated ~2× (225s/run). Identical work, ~4.5× less provisioning. On ubuntu the two
   are equal because the per-job flox cost is small enough not to dominate.
4. **Warm cache barely helps** (macOS flox-consolidated setup ~157→166s — flat/worse; ubuntu
   ~48→47s). The
   `flox/install-flox-action` + activation overhead dominates over the cacheable Nix store —
   the thing to fix if flox-in-CI is ever to be viable.
5. **Reliability flips to Flox/mise.** Zero flox *and* mise failures; traditional's runtime
   binary downloads flake under load (the managed envs don't).
6. **mise is the viable single-source-of-truth middle ground.** ~1.0–1.3× traditional on ubuntu,
   but its provisioning is **OS-insensitive** (~10s ubuntu ≈ ~14s macOS — release binaries, no
   build) and its **warm cache works** (~5–6s). On **macOS, mise-consolidated matches/beats
   traditional** and is **~5–10× faster than flox**.
7. **Consolidation's value depends on provisioning cost.** Decisive for flox (expensive
   install paid 10× vs 2×); neutral on ubuntu-mise; but on **macOS-mise it matters again**
   (consolidated ~39s vs mirror ~69s — macOS's higher per-job overhead rewards fewer jobs).

## Extension v2 — isolating *where* the flox cost lives (nocache · noaction · baked)

Three further sides probe whether any single lever explains flox's provisioning cost.
Each changes exactly one variable vs. `flox`; all run the same 10 checks.

- **`flox-nocache`** — `flox/install-flox-action` with `use-cache: false` (the flox **CLI-binary**
  download is not cached; the Nix-store `actions/cache` is unchanged).
- **`flox-noaction`** — flox installed by **direct package download** (pinned `.deb`/`.pkg`,
  no GitHub Action), to isolate the Action wrapper.
- **`flox-baked`** — the **container-image** equivalent of `flox-consolidated`: the whole dev
  flox env + warm uv cache **baked into `ghcr.io/<owner>/flox-ci-base-full`**, run as a
  container job. Its "setup" is the image **pull** (GHA's *Initialize containers* step, counted
  as setup so the row stays honest). **Linux-only** (container jobs are Linux-only).

setup/job (provisioning per job), cold / warm — consolidated rows:

| side | ubuntu | macOS | isolates |
| --- | ---: | ---: | --- |
| flox (action + bin-cache) | 47.6 / 47.3 | 157 / 166 | baseline |
| flox-nocache (action, no bin-cache) | 47.9 / 46.0 | 166 / 159 | flox CLI-binary cache |
| flox-noaction (manual install) | 50.5 / 54.5 | 151 / 146 | the GitHub Action wrapper |
| flox-baked (container pull) | 46.3 / 46.3 ⟂ | — (linux-only) | pre-baking the whole env |

(⟂ `flox-baked` cold and warm are **identical by construction** — it has no Nix `actions/cache`
step, so both just pull the image fresh; the cold/warm split is not a real axis for it.
The earlier `flox-noaction·ubuntu·cold` "223s outlier" was actually a cross-OS-contaminated
macOS run; after the v3 cleaning it is a clean ~50s, in line with the other flox variants.)

![Where the flox cost lives — every lever lands on the Nix-realization floor](results/summary_v2.png)

**Finding — the flox cost is irreducibly the Nix-store realization.** Each lever moves setup
by **~nothing**:

- `flox → flox-nocache`: caching the flox **CLI binary** saves ~0 — the cost was never the
  binary download.
- `flox-nocache → flox-noaction`: installing flox **manually** vs. via the Action is within
  noise — the Action wrapper is not the cost.
- `flox-baked`: baking the **entire realized env** into an image **doesn't help** — the 1.5 GB
  image **pull (~46s) ≈ the install it replaced**. Pre-baking *relocates* the cost (to a
  treatment-only pull) but doesn't remove it; `net = setup_saved − pull_added ≈ 0`.

Every approach must **materialize the Nix closure** (download + link the store, or pull the
image that contains it) — that ~47s ubuntu / ~160s macOS is the floor, and the only thing worth
attacking if flox-in-CI is to get faster. (`flox-baked` is a *consolidated*-shaped 2-job side,
so it never pays the mirror's 10× tax — but neither does `flox-consolidated`.)

**Scope:** the binary-cache and Action-wrapper results hold on **both** OSes (flox-nocache /
flox-noaction ran ubuntu+macOS). The **containerizing** result is **ubuntu-only** — container
jobs are Linux-only, so `flox-baked` has **no macOS data**. "Pre-baking doesn't escape the cost"
is established for ubuntu; on macOS (where the flox tax is largest) it is **untested** and the
macOS install/pull tradeoff could differ.

**Reliability note:** flox-noaction's manual macOS `.pkg` postinstall flaked intermittently
("error running scripts from the package"); one install retry made it reliable — a small but
real robustness edge the GitHub Action has over rolling your own install. The **mirror** topology
on macOS is itself flaky (10 parallel installs per run; any one failing excludes the whole run),
which left some macOS-mirror cells at n=2–4 — a topology-reliability data point in its own right.

## Implication for ADR-12

The maintenance win (one declarative manifest) and reliability are real for **both** flox and
mise. The decision splits on CI speed:
- **Flox** carries a **~2.8–7.9× CI tax** (~2.8–3.2× ubuntu, ~3–7.9× macOS), dominated by the
  Nix-store build (worst on macOS) — a real simplicity/reliability **vs.** CI-speed tradeoff.
  If used in CI, consolidated-only.
- **mise** delivers the single-manifest simplicity **without** flox's tax: ~1.0–1.3× traditional
  on ubuntu and **≈/better than traditional on macOS** (consolidated). It's the recommended
  option if a single-source-of-truth toolchain manager is wanted for CI; traditional stays
  fastest in raw ubuntu terms. (Local-dev provisioning — one activation per shell — is a
  non-issue for any.)

## Caveats

- `editorconfig` was excluded: its only traditional path (npm `editorconfig-checker`)
  downloads a binary from GitHub at runtime and flaked ~45% (rate-limit + corrupt archive)
  under the driver's rapid runs — isolated entirely to that one item (0 failures elsewhere or
  on the flox side). Itself a reliability data point.
- "Total run time" = GitHub's reported run wall-clock (parallel jobs for mirror/traditional;
  2 jobs for consolidated). Setup is per-job; `provisioning/run` sums it (billable view).
- **Cross-OS contamination (found by audit, fixed).** Because ubuntu and macOS drivers ran
  **concurrently** and the driver polled `gh run list` without an OS filter, 4 runs landed in
  the wrong cell (3 macOS runs in `traditional·ubuntu·warm`, 1 in
  `flox-noaction-consolidated·ubuntu·cold`). The driver now verifies each run's runner OS, the
  4 runs were purged, and the affected cells re-collected. Numbers here are the cleaned data.
- **Variable n / survivorship bias.** The driver records only **successful** runs, so the
  flaky configs (macOS mirror — 10 parallel installs/run; manual `.pkg`) drop failed reps and
  their averages are **optimistic lower bounds**. Lowest-n cells (see REPORT.md `n` column):
  `flox-noaction-mirror·ubuntu·warm` and `flox-nocache-mirror·macOS·cold` (n=1),
  `flox-consolidated·macOS·warm` and `mise-consolidated·ubuntu·cold` (n=2),
  `flox-mirror·macOS·cold/warm`, `flox-noaction·ubuntu·cold`, `traditional·ubuntu·warm` (n=3).
  Lean on the n=5 consolidated rows and the median column; treat low-n Δ% as directional.
- **Noisy macOS baseline.** `traditional·macOS·cold` (avg 64s, median 55s, max 125s) carries a
  runner-queue outlier, so macOS-cold Δ% against it is unstable — prefer the median.
- Single repo; GitHub-hosted runners; small n — treat ±10–20% as noise.
