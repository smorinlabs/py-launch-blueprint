# Flox vs. Traditional CI — Timing Experiment Findings

**Question:** Does provisioning this repo's CI toolchain with [Flox](https://flox.dev)
(Nix-based) instead of the traditional per-tool installs (`setup-uv`, `setup-just`,
`bunx`, release-download scripts) make GitHub Actions faster or slower? Informs ADR-12.

**TL;DR:** Flox is **3.8× slower on ubuntu and up to ~8.7× slower on macOS**, because
**~75% of every flox job is provisioning** (the `flox` install/activate step). Traditional
wins decisively on speed; Flox wins decisively on reliability (0 failures vs traditional's
flaky binary downloads). Consolidating flox activations is the single biggest mitigation.

## Method

- **Matrix:** 3 sides × 2 OS × 2 cache × 5 reps on GitHub-hosted runners.
  - Sides: `traditional` (per-tool install), `flox-mirror` (same 10 checks, each under its
    own `flox activate`), `flox-consolidated` (checks share one activation; 2 jobs).
  - OS: `ubuntu-latest`, `macos-latest`. Cache: cold / warm (Nix store + uv/bun caches).
- **10 checks measured:** ruff-check, ruff-format, ty, pytest, taplo, codespell, yamllint,
  bandit, gitleaks, commitlint. (`editorconfig` dropped — see caveats.)
- A driver dispatches runs serially, **excludes failed reps** (never records bad samples);
  `analyze.py` pulls run/job/step timings from the GitHub API.
- Samples: n=5 per cell except `traditional·macOS·warm` (n=3, one transient failure).

## Results — total run time (avg seconds, Δ% vs traditional)

| side | ubuntu cold | ubuntu warm | macOS cold | macOS warm |
| --- | ---: | ---: | ---: | ---: |
| traditional | 17.2 | 17.2 | 36.4 | 38.7 |
| flox-mirror | 64.8 (+277%) | 64.6 (+276%) | 318.4 (+775%) | 303.6 (+685%) |
| flox-consolidated | 64.8 (+277%) | 62.8 (+265%) | 181.6 (+399%) | 161.6 (+318%) |

## Results — provisioning (setup) vs work

`setup` = the `provision` step (flox install/activate, or setup-uv/just/bun).
`provisioning/run` = setup summed across all jobs in a run (cumulative billable cost).

| side | setup/job (ubuntu) | setup/job (macOS) | setup % of job | provisioning/run (ubuntu) | provisioning/run (macOS) |
| --- | ---: | ---: | ---: | ---: | ---: |
| traditional | ~3s | ~4–5s | 33–39% | ~30s | ~40–48s |
| flox-mirror | ~38s | ~110s | 74–77% | ~381s | **~1100s** |
| flox-consolidated | ~41s | ~120s | 71–74% | ~82s | ~225s |

## Results — reliability

| side | failures across ~110 runs |
| --- | --- |
| flox-mirror / flox-consolidated | **0** (both OS) |
| traditional | flaky `editorconfig` (removed); 1 transient on macOS |

## Key findings

1. **The flox CI tax is provisioning, not the checks.** ~75% of each flox job is the
   `flox` install/activate step; the actual check work (~13s ubuntu, ~33s macOS) is small
   and comparable to traditional. Traditional tool installs are ~3–5s.
2. **macOS is where Flox hurts most.** Per-job flox setup is ~110s on macOS vs ~38s on
   ubuntu (Nix-on-macOS cold build), pushing flox-mirror to ~8.7× slower.
3. **Consolidation is the decisive lever — where provisioning is costly.** mirror and
   consolidated have ~equal per-job setup, but mirror pays it 10× (1100s/run on macOS) vs
   consolidated ~2× (225s/run). Identical work, ~4.5× less provisioning. On ubuntu the two
   are equal because the per-job flox cost is small enough not to dominate.
4. **Warm cache barely helps** (macOS setup 110→105s; ubuntu 38→39s). The
   `flox/install-flox-action` + activation overhead dominates over the cacheable Nix store —
   the thing to fix if flox-in-CI is ever to be viable.
5. **Reliability flips for Flox.** Zero flox failures; traditional's runtime binary downloads
   flake under load (the deterministic Nix store does not).

## Implication for ADR-12

The maintenance win is real (~400 LOC deleted, one declarative manifest) and Flox is more
reliable — but it carries a quantified **CI-speed tax of 3.8–8.7×**, dominated by
provisioning. It's a **simplicity + reliability vs. CI-speed** tradeoff, not a free win.
If adopted: **the consolidated-activation topology is mandatory** (especially on macOS), and
the install-action/activation overhead (not caching) is the lever to optimize.

## Caveats

- `editorconfig` was excluded: its only traditional path (npm `editorconfig-checker`)
  downloads a binary from GitHub at runtime and flaked ~45% (rate-limit + corrupt archive)
  under the driver's rapid runs — isolated entirely to that one item (0 failures elsewhere or
  on the flox side). Itself a reliability data point.
- "Total run time" = GitHub's reported run wall-clock (parallel jobs for mirror/traditional;
  2 jobs for consolidated). Setup is per-job; `provisioning/run` sums it (billable view).
- Preliminary; single repo; GitHub-hosted runners; n=5 (n=3 for one cell).
