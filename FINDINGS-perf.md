# Flox provisioning — root-cause findings

**Status: root cause identified.** Method, evidence, and ranked fixes below.
Companion: harness `experiment/profiling/`, playbook `experiment/PROFILING.md`,
journey log `PROFILE_LOG.md`, prior experiment `experiment/FINDINGS.md` + ADR-12.

## TL;DR

Flox CI cost is ~90% **provisioning** = materializing the env's Nix store closure onto
the runner, **not** the checks and **not** local compilation. **Confirmed, high
confidence:** the **uncompressed** macOS (aarch64-darwin) closure is **1653 MB vs 549 MB
for Linux (x86_64) — a 3.0× ratio that matches the ~2.9× macOS time penalty almost
exactly** — and the entire ~1.1 GB difference is **LLVM + Clang + the Apple SDK dragged
into the runtime closure by `python3` on darwin** (proven by `why-depends`). That is a
real, isolated, upstream-fixable bloat and the #1 optimization target.

**The cost is unpack, not download.** The *compressed* download is only ~1.4× bigger on
macOS (256 vs 180 MB) — but *uncompressed* it's 3.0× (1653 vs 549 MB), and the time
penalty tracks the **uncompressed** ratio. So provisioning is bound by **decompress +
write-to-`/nix`** (bytes + file count), not network transfer. This also explains why CI
warm ≈ cold: restoring a cached `/nix` untars the same uncompressed bytes. Shrinking the
closure (candidate #1) attacks the binding constraint directly. (Still inferred, not
step-measured, on real CI: see "CI mechanism".)

## Method (why closure analysis, not flame graphs, was the primary tool)

Top-down, "don't assume CPU." Characterizing the workload first showed the bottleneck
is **download/unpack volume**, not a CPU/latency hotspot — so the decisive evidence is
**closure composition** (`nix path-info`, `nix-store -q --requisites`, substitutability
via `nix path-info --store https://cache.nixos.org`, and `nix why-depends`), not a
flame graph. A cold off-CPU/on-CPU flame is the *confirmatory* next layer (candidate
#5), not the root-cause signal here.

Environments: dev Mac (aarch64-darwin, flox 1.12.1) + Lima VM (Ubuntu 25.10
aarch64-linux, flox 1.12.1).

## Evidence

### 1. It's materialized (downloaded+unpacked), not built locally (refutes the build hypothesis)

Substitutability of the realized closure (cached ⇒ fetched; uncached ⇒ built locally):

| OS | closure paths | on-disk size | cached (fetch) | uncached (build) |
| --- | ---: | ---: | ---: | ---: |
| aarch64-darwin (mac) | 84 | **1714 MB** | 80 | 4 |
| aarch64-linux (Lima) | 65 | **600 MB** | 60 | 5 |

The few "uncached" paths on **both** OSes are flox's own tiny per-env wrappers
(`environment-runtime`, `flox-interpreter`, `manifest`, `flox-activations`) — built on
every machine regardless of OS. **The toolchain itself (python/uv/ruff/bun/…) is
substituted on macOS exactly as on Linux.** macOS does *not* compile it.

Baseline cold `flox activate` on Linux = **8.45 s** (warm = 0.06 s) ⇒ cold is
overwhelmingly network download + unpack, not eval/build.

**Arch-consistent closure sizes (queried straight from `cache.nixos.org`, so no
warm-store or debug-build artifacts):**

| arch (CI target) | closure paths | NAR (uncompressed) | download (compressed) |
| --- | ---: | ---: | ---: |
| x86_64-linux (ubuntu CI) | 43 | 549 MB | 180 MB |
| aarch64-darwin (macOS CI) | 68 | **1653 MB** | 256 MB |
| aarch64-linux (Lima) | 43 | 551 MB | 170 MB |

Two things fall out: (a) x86_64-linux ≈ aarch64-linux, so the Lima leg is representative
of CI ubuntu; (b) the macOS penalty tracks the **uncompressed** ratio (1653/549 = 3.0×),
**not** the compressed-download ratio (256/180 = 1.4×). So provisioning is bound by
**decompress + write to `/nix`** (bytes + file count), not the network transfer — and a
cached `/nix` doesn't help much because the restore untars the same uncompressed bytes.

### 2. The macOS bloat is LLVM + Clang + Apple SDK (~1.2 GB)

Biggest paths, aarch64-darwin closure:

| path | MB |
| --- | ---: |
| llvm-21.1.8-lib | 380 |
| apple-sdk-14.4 | 371 |
| clang-21.1.8-lib | 289 |
| python3-3.12.13 | 113 |
| llvm-21.1.8 | 100 |
| bun-1.3.13 | 61 |
| uv-0.11.16 | 53 |
| libiconv ×2 (113 + 109) | 46 + 46 |

`llvm + clang + apple-sdk ≈ 1185 MB` — **none of which is in the Linux closure**
(Linux's bulk is python 137, bun 97, uv 61, glibc 47). The ~2.9× size ratio matches
the experiment's ~3× macOS time penalty (47 s → 136 s).

### 3. The culprit is `python3`, and the reference chain is direct

Per-tool closure scan — only Python drags the toolchain in:

```
python3-3.12   toolchain paths in closure: 6
bun / uv / ruff / gh / gitleaks / just / taplo / lefthook / gnumake: 0
```

`nix why-depends`:

```
python3-3.12.13 ─→ apple-sdk-14.4                      (direct)
python3-3.12.13 ─→ clang-wrapper-21.1.8 ─→ clang-21.1.8-lib ─→ llvm-21.1.8-lib
```

This is the known nixpkgs pattern: the darwin `python3` retains a runtime reference to
the compiler/SDK it was built with (via `sysconfig`/`distutils`, so `python -m
sysconfig` and on-the-fly C-extension builds keep working), pulling Clang + the Apple
SDK into every consumer's runtime closure. On Linux the equivalent reference is just
gcc/glibc — tiny by comparison.

### 4. CI mechanism — why "warm ≈ cold" doesn't refute the size theory

The prior experiment found flox CI warm ≈ cold (ubuntu 46.5 s cold / 47.6 s warm;
macOS 135.8 / 129.0) — the opposite of the local signature (cold 8.45 s, warm 0.06 s).
That looked like it might refute "download-bound." Reading the workflow
(`.github/actions/provision-flox/action.yml`) resolves it: it **does** cache `/nix` +
`~/.cache/flox` via `actions/cache@v4` (stable warm key) and then runs `flox activate`.
So warm runs restore the store — but restoring + **untarring a 0.6–1.7 GB `/nix` (a
huge count of small files)** costs about as much as downloading it cold. Both paths are
**volume-bound**, so a smaller closure helps cold *and* warm. The local warm (0.06 s) is
fast only because it skips the cache-restore step entirely (store already on disk).

*Still to confirm (the one open item):* that the CI warm ~47 s is actually spent in
cache-restore/untar (not elsewhere). The committed results hold only per-run totals, not
per-step times — a single CI run with step timing on the `Cache Nix store` vs `Warm the
flox env` steps would upgrade this from inference to measurement.

## Ranked optimization candidates

1. **Strip Python's darwin SDK/compiler runtime leak — the dominant lever.**
   *What:* darwin `python3` propagates `apple-sdk` + `clang-wrapper` + `llvm-lib` into
   its runtime closure (~1.2 GB). *Evidence:* §2–§3 above. *Est. impact:* darwin
   closure 1714 → ~530 MB (≈ Linux); macOS cold provisioning potentially ~3× faster
   (~136 s → ~50 s), every run. *Where:* nixpkgs `python3` darwin packaging.
   *Upstream-fixable:* yes. *Mitigations to test, fastest first:* (a) a nixpkgs
   `python3` revision that drops the `sysconfig` cc/SDK reference; (b) `python3Minimal`
   if the env doesn't need `distutils`/headers; (c) a flox overlay that removes the
   propagated SDK from the runtime output.

2. **Dedupe duplicated libraries.** darwin ships `libiconv` ×2 (~92 MB); Linux ships
   `glibc` ×2 (~94 MB). Pin single versions so two toolchain generations don't coexist
   in the closure. Small but free.

3. **Investigate the debug Python on Linux.** The Lima closure pulled
   `python3-3.12.13-debug` while the Mac pulled the normal `python3-3.12.13`. A debug
   build is larger/slower; if flox/nixpkgs is selecting it, switching to release trims
   the Linux closure too. Verify the lock's intent.

4. **The warm cache "works" but barely helps — and that's a size symptom, not a cache
   bug.** `/nix` *is* cached (§4), yet warm ≈ cold because restoring + untarring a large
   `/nix` is itself ~as slow as a cold download. So #1 (shrink the closure) is what makes
   warm cheap too; a `tar`-vs-`zstd` archive method or fewer/larger store paths is a
   secondary lever. Confirm with per-step CI timing first.

5. **Confirmatory flame graph (the literal Brendan-Gregg layer).** On a *fresh* store
   (the only way to a true cold — see "Limitations"), capture an off-CPU + on-CPU flame
   of one cold `flox activate` to split the wall-clock across network-recv vs
   zstd-decompress (CPU) vs `/nix` write/fsync (disk). This tells whether, after the
   closure shrinks, the remaining cost is throughput-bound and where. Harness:
   `profile-flox.sh --deep` in a freshly-recreated Lima VM.

## Limitations (how cold was — and wasn't — reproduced)

- **Arch consistency — resolved.** The headline 3.0× ratio uses cache-queried sizes for
  the *actual* CI arches (x86_64-linux 549 MB vs aarch64-darwin 1653 MB). `macos-latest`
  is arm64, matching the darwin figure. The earlier on-disk numbers (1714/600 MB) were
  realized-store sizes (arch-mixed, debug-Python-inflated) and are superseded by the
  cache table for the ratio.
- **Debug Python — explained.** `python3-3.12.13-debug` appeared only in the *realized*
  Lima store, not in the locked closure queried from cache (x86_64 ≈ aarch64-linux at
  ~550 MB). It's a VM realization artifact, not part of the CI closure — so it does not
  affect the ratio. (Still worth a glance: candidate #3.)
- A true cold provision can't be reproduced on a warm host (`nix store delete` is
  all-or-nothing and refuses in-use/shared paths like `glibc`; flox also roots the env
  internally, so scoped cold-reset frees only the ~2 MB wrapper; global GC is out of
  bounds). Genuine cold needs a fresh store (recreate the Lima VM) or CI — which is why
  the root cause rests on closure composition, which needs no cold reset.
