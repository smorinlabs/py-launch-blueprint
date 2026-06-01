# Flox vs. Traditional vs. mise CI — Timing Experiment Findings

**Question:** Does provisioning this repo's CI toolchain with [Flox](https://flox.dev)
(Nix-based) or [mise](https://mise.jdx.dev) (a single tool-manager over release/pipx/npm
backends), instead of the traditional per-tool installs (`setup-uv`, `setup-just`, `bunx`,
release-download scripts), make GitHub Actions faster or slower? Informs ADR-12.

**TL;DR:** **Flox is 3.8× slower on ubuntu and up to ~8.7× slower on macOS** — and it's
**~90–94% provisioning**: the actual checks run at the *same speed* across all sides
(see root-cause); essentially all of flox's cost is install + activate + Nix-store cache-save.
**mise lands in the middle** (~2× traditional on ubuntu) — ~3–4× cheaper provisioning than
flox (release binaries, no Nix build), and unlike flox **its warm cache actually works**
(warm mise approaches traditional). Traditional wins on raw speed; flox wins on reliability;
mise is the speed/single-source-of-truth compromise — and on **macOS, mise-consolidated
matches/beats traditional** (−2% cold, **−21% warm**) while flox is 5–9× slower there.

## Method

- **Matrix:** up to 5 sides × 2 OS × 2 cache × 5 reps on GitHub-hosted runners.
  - Sides: `traditional` (per-tool install), `flox-mirror`/`flox-consolidated` (whole env via
    `flox activate`, per-job vs once), `mise-mirror`/`mise-consolidated` (whole env via
    `mise` + `mise exec`, per-job vs once).
  - OS: `ubuntu-latest`, `macos-latest`. Cache: cold / warm (Nix store, mise install dir,
    uv/bun caches). All 5 sides ran the full matrix (reps=5, both OS).
- **10 checks measured:** ruff-check, ruff-format, ty, pytest, taplo, codespell, yamllint,
  bandit, gitleaks, commitlint. (`editorconfig` dropped — see caveats.)
- A driver dispatches runs serially, **excludes failed reps** (never records bad samples);
  `analyze.py` pulls run/job/step timings from the GitHub API.
- Samples: n=5 per cell except `traditional·macOS·warm` (n=3, one transient failure).

## Results — total run time (avg seconds, Δ% vs traditional)

| side | ubuntu cold | ubuntu warm | macOS cold | macOS warm |
| --- | ---: | ---: | ---: | ---: |
| traditional | 17.2 | 17.2 | 36.4 | 38.7 |
| mise-mirror | 33.0 (+92%) | 23.0 (+34%) | 63.0 (+73%) | 43.6 (+13%) |
| mise-consolidated | 29.8 (+73%) | 23.2 (+35%) | **35.8 (−2%)** | **30.6 (−21%)** |
| flox-mirror | 64.8 (+277%) | 64.6 (+276%) | 318.4 (+775%) | 303.6 (+685%) |
| flox-consolidated | 64.8 (+277%) | 62.8 (+265%) | 181.6 (+399%) | 161.6 (+318%) |

## Results — provisioning (setup) vs work

`setup` = all provisioning: the `provision` step (flox install/activate, or
setup-uv/just/bun) **plus** the `Post provision` cache-save step.
`provisioning/run` = setup summed across all jobs in a run (cumulative billable cost).

setup/job shown as cold / warm (ubuntu | macOS):

| side | setup/job ubuntu | setup/job macOS | provisioning/run ubuntu | provisioning/run macOS |
| --- | ---: | ---: | ---: | ---: |
| traditional | 3.0 / 3.3 | 4.1 / 5.0 | 30 / 33 | 41 / 50 |
| mise-mirror | 11.9 / **4.0** | 13.7 / **6.2** | 119 / 40 | 137 / 62 |
| mise-consolidated | 11.7 / **4.6** | 14.1 / **7.3** | 23 / 9 | 28 / 15 |
| flox-mirror | 46.5 / 47.6 | 135.8 / ~129 | 465 / 476 | **1358** / 1288 |
| flox-consolidated | 49.3 / 48.3 | 150.6 / ~129 | 99 / 97 | 301 / 258 |

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
2. **macOS is where Flox hurts most.** Per-job flox provisioning is ~130s on macOS vs ~47s
   on ubuntu (Nix-on-macOS cold build + larger cache save), pushing flox-mirror to ~8.7×.
3. **Consolidation is the decisive lever — where provisioning is costly.** mirror and
   consolidated have ~equal per-job setup, but mirror pays it 10× (1100s/run on macOS) vs
   consolidated ~2× (225s/run). Identical work, ~4.5× less provisioning. On ubuntu the two
   are equal because the per-job flox cost is small enough not to dominate.
4. **Warm cache barely helps** (macOS setup 110→105s; ubuntu 38→39s). The
   `flox/install-flox-action` + activation overhead dominates over the cacheable Nix store —
   the thing to fix if flox-in-CI is ever to be viable.
5. **Reliability flips to Flox/mise.** Zero flox *and* mise failures; traditional's runtime
   binary downloads flake under load (the managed envs don't).
6. **mise is the viable single-source-of-truth middle ground.** ~2× traditional on ubuntu,
   but its provisioning is **OS-insensitive** (~12s ubuntu ≈ ~14s macOS — release binaries, no
   build) and its **warm cache works** (~4–7s). On **macOS, mise-consolidated matches/beats
   traditional** (−2% cold, −21% warm) and is **~5–9× faster than flox**.
7. **Consolidation's value depends on provisioning cost.** Decisive for flox (expensive
   install paid 10× vs 2×); neutral on ubuntu-mise; but on **macOS-mise it matters again**
   (consolidated 36s vs mirror 63s — macOS's higher per-job overhead rewards fewer jobs).

## Implication for ADR-12

The maintenance win (one declarative manifest) and reliability are real for **both** flox and
mise. The decision splits on CI speed:
- **Flox** carries a **3.8–8.7× CI tax**, dominated by the Nix-store build (worst on macOS) —
  a real simplicity/reliability **vs.** CI-speed tradeoff. If used in CI, consolidated-only.
- **mise** delivers the single-manifest simplicity **without** flox's tax: ~2× traditional on
  ubuntu and **≈ traditional on macOS** (consolidated). It's the recommended option if a
  single-source-of-truth toolchain manager is wanted for CI; traditional stays fastest in raw
  ubuntu terms. (Local-dev provisioning — one activation per shell — is a non-issue for any.)

## Caveats

- `editorconfig` was excluded: its only traditional path (npm `editorconfig-checker`)
  downloads a binary from GitHub at runtime and flaked ~45% (rate-limit + corrupt archive)
  under the driver's rapid runs — isolated entirely to that one item (0 failures elsewhere or
  on the flox side). Itself a reliability data point.
- "Total run time" = GitHub's reported run wall-clock (parallel jobs for mirror/traditional;
  2 jobs for consolidated). Setup is per-job; `provisioning/run` sums it (billable view).
- All 5 sides ran the full matrix (both OS, cold/warm, n=5); only `traditional·macOS·warm`
  is n=3 (one transient). Single repo; GitHub-hosted runners; small n — treat ±10–20% as noise.
