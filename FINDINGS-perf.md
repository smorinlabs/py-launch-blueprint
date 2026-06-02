# Flox provisioning — root-cause findings

**Status: root cause identified.** Method, evidence, and ranked fixes below.
Companion: harness `experiment/profiling/`, playbook `experiment/PROFILING.md`,
journey log `PROFILE_LOG.md`, prior experiment `experiment/FINDINGS.md` + ADR-12.

## TL;DR

Flox CI cost is ~90% **provisioning** = materializing the env onto the runner, **not** the
checks and **not** local compilation. The macOS penalty (CI: `provision (flox)` 114 s vs
ubuntu 36 s, *measured* §4) is **two roughly-equal costs**:

1. **A bloated closure** — *confirmed, high confidence.* The uncompressed macOS closure is
   **1653 MB vs 549 MB Linux (3.0×)**; the entire ~1.1 GB difference is **LLVM + Clang +
   Apple SDK dragged into the runtime closure by `python3` on darwin** (proven by
   `why-depends`). This drives the ~54 s vs ~24 s `flox activate` (download+unpack) gap.
   Real, isolated, upstream-fixable — the #1 *closure* lever.
2. **A slow macOS Nix install** — ~58 s vs ~11 s, because `flox/install-flox-action`
   provisions Nix into a dedicated APFS volume every job (§4a). This is ~half the penalty
   and is **not** fixed by shrinking the closure (candidate #2).

Plus a separate **CI defect**: the warm `/nix` cache **never saves** (root-owned store
files break the `tar`), so every run pays full cold cost (§4b) — why "warm ≈ cold."

**The closure cost is unpack, not download.** Compressed download is only ~1.4× bigger on
macOS (256 vs 180 MB); uncompressed it's 3.0× — and the activate time tracks the
**uncompressed** side. So provisioning is bound by **decompress + write-to-`/nix`**, not
network transfer (confirmed by the flame graphs, §5: idle CPU + `nix-daemon` blocked on
I/O). Earlier this section claimed the closure explained the *whole* 3× penalty; per-step
CI timing corrected that to ~half.

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

### 4. CI mechanism — MEASURED (dispatched runs, per-step timing)

I dispatched `flox-mirror-suite` on both OSes (cold + warm) and read per-step timings
from the logs. Two distinct findings, both now measured on real CI rather than inferred:

**(a) The macOS penalty is real (114 vs 36 s) but is TWO costs, only one of which is the
closure.** Splitting `provision (flox)` by sub-step timestamps from the logs:

| sub-step | ubuntu cold | macOS cold | macOS extra |
| --- | ---: | ---: | ---: |
| Download & Install flox (flox/nix install) | ~11 s | **~58 s** | ~47 s |
| configure / verify / cache-restore | ~1 s | ~1 s | — |
| `flox activate` (closure download + unpack) | ~24 s | **~54 s** | ~30 s |
| **total `provision (flox)`** | **36 s** | **114 s** | **~78 s** |

So the ~78 s macOS penalty is **~47 s flox/nix *install* overhead** (macOS installs Nix
into a dedicated APFS volume — slow, and unrelated to our toolchain) **+ ~30 s extra
closure download/unpack** (the part the SDK leak drives; activate is ~2.25× ubuntu,
consistent with the size delta). The earlier "3.2× ≈ 3.0× closure" match was partly a
coincidence of two unrelated costs summing — the closure explains roughly **half** the
gap, not all of it.

**(b) "warm ≈ cold" is a CACHE-SAVE BUG, not slow restore — a concrete, fixable defect.**
The earlier inference (restore-untar ≈ download) was *wrong*. The logs show the warm
`/nix` cache is **never saved**, so every "warm" run is a cache **miss** and re-downloads:

```
Post provision (flox):  /usr/bin/tar: /nix/var/nix/db/reserved: Cannot open: Permission denied
                        ##[warning]Failed to save: "/usr/bin/tar" failed with exit code 2
provision (flox):       Cache not found for input keys: flox-warm-Linux-<hash>-stable
```

`actions/cache` tars `/nix` as the unprivileged runner user, but parts of the Nix store
db are **root-owned** (`/nix/var/nix/db/reserved`) → `tar` exits non-zero → the save is
abandoned → no `flox-warm-*` key is ever stored (confirmed: `gh cache list` shows none).
So warm ≈ cold because **the cache is effectively disabled**, every run pays full cold
provisioning. This is independent of (and compounds with) the closure-size problem.

**Cross-OS:** the same failure occurs on macOS (`gtar: /nix/var/nix/gc.lock`,
`db/reserved`, `db/big-lock`, `userpool/*: Permission denied`) — so the warm cache is
broken on both runners, not a Linux quirk.

### 5. Flame graphs (measured, illustrative) — confirm I/O/unpack-bound

A genuine cold `flox activate` in a fresh Lima VM (12 s; qemu, so ~illustrative not
CI-magnitude) captured system-wide. Artifacts:
`experiment/profiling/results/flox-cold-activate.{on,off}cpu.svg`.

- **on-CPU** (`perf`): dominated by `cpuidle_idle_call` — the CPU is **mostly idle**. The
  only real work is `lzma_decode` + `lzma_crc64` + `sha256_block_armv8` = **decompressing
  and verifying** downloaded NARs. An idle-dominated on-CPU flame is itself the proof the
  bottleneck is *not* CPU.
- **off-CPU** (eBPF `offcputime`): the top blocking process by far is **`nix-daemon`**
  (and `tokio-runtime-w`, its async fetch workers) — i.e. time is spent **blocked on I/O**
  (network recv from the substituter + disk write/unpack into `/nix`).

Together: cold provisioning is **download + decompress + write**, with the CPU idling on
I/O — exactly what the closure-size analysis predicted, and why a CPU flame graph alone
would have been the wrong tool.

## Ranked optimization candidates

1. **Strip Python's darwin SDK/compiler runtime leak — the dominant *closure* lever.**
   *What:* darwin `python3` propagates `apple-sdk` + `clang-wrapper` + `llvm-lib` into
   its runtime closure (~1.2 GB). *Evidence:* §2–§3. *Est. impact (corrected):* shrinks
   the ~54 s macOS `flox activate` to roughly ~18 s (closure 1.65 GB → ~0.5 GB), i.e.
   macOS `provision (flox)` ~114 s → **~78 s**, and ubuntu ~36 → ~28 s. (It does **not**
   touch the ~47 s macOS flox/nix *install* cost — see #2.) *Where:* nixpkgs `python3`
   darwin packaging. *Upstream-fixable:* yes. *Mitigations, fastest first:* (a) a nixpkgs
   `python3` revision dropping the `sysconfig` cc/SDK reference; (b) `python3Minimal` if
   `distutils`/headers aren't needed; (c) a flox overlay stripping the SDK from the
   runtime output.

2. **The macOS flox/nix install is ~58 s per job (vs ~11 s ubuntu) — the *other* half of
   the macOS penalty.** *What:* `flox/install-flox-action` installs Nix into a dedicated
   APFS volume on every macOS job (§4a). *Est. impact:* ~47 s of the ~78 s penalty; not
   addressable by closure shrinking. *Fix options:* cache/pre-provision Nix on the runner;
   a faster macOS install path; or run fewer flox jobs (consolidation — the experiment
   already showed consolidated flox is much better on macOS). This is the **biggest single
   macOS lever** and is orthogonal to #1.

3. **Fix the broken `/nix` cache save (concrete CI bug).**
   *What:* `actions/cache` can't `tar` root-owned Nix store files
   (`/nix/var/nix/db/reserved`, `gc.lock`, …) → save fails → warm cache never exists →
   **every run pays full cold cost** (§4b, both OSes). *Est. impact:* a working warm cache
   makes repeat runs cheap (the experiment's `mise` warm is ~4–7 s). *Fix options:* run
   the archive step with `sudo`; or exclude/`chmod` the root-owned lock/db files; or adopt
   a Nix-aware cache action (`DeterminateSystems/magic-nix-cache`,
   `nix-community/cache-nix-action`) that snapshots the store correctly. Independent of #1
   and stacks: #1 shrinks each cold pay; #3 stops paying cold every time.

4. **Dedupe duplicated libraries.** darwin ships `libiconv` ×2 (~92 MB); Linux ships
   `glibc` ×2 (~94 MB). Pin single versions so two toolchain generations don't coexist
   in the closure. Small but free.

5. **Investigate the debug Python on Linux.** The Lima closure pulled
   `python3-3.12.13-debug` while the Mac pulled the normal `python3-3.12.13`. A debug
   build is larger/slower; if flox/nixpkgs is selecting it, switching to release trims
   the Linux closure too. Verify the lock's intent.

6. **[DONE] Flame graphs captured** — see §5. on-CPU idle-dominated + `lzma_decode`;
   off-CPU dominated by `nix-daemon` blocked on I/O. Confirms I/O/unpack-bound; no further
   action needed unless re-profiling after #1 to find the next constraint.

## flox vs mise — why mise avoids the tax

mise installs the **same logical toolchain** (`experiment/mise.toml`: python, uv, ruff,
taplo, gitleaks, just, bun, gh, lefthook + pipx + npm) but is the experiment's
middle-ground (≈2× traditional on ubuntu; macOS-consolidated ≈ traditional). Same
closure-analysis method, applied to mise:

| metric | flox (Nix closure) | mise (release binaries) |
| --- | ---: | ---: |
| Linux footprint (same-OS, most rigorous) | **549 MB** | **350 MB** |
| macOS footprint | **1653 MB** | ~298 MB |
| macOS ÷ Linux | **3.0× (OS-sensitive)** | ~1× (OS-insensitive) |
| python | pulls apple-sdk + clang + llvm (~1.1 GB) | 66–87 MB standalone, no SDK |

*Measurement note:* flox sizes are `nix path-info` against the cache (the locked closure);
mise sizes are `du` of the dirs `mise where` resolves for the pinned toolchain. Lead with
the **same-OS Linux** numbers (mise 350 vs flox 549 MB) — those are the most directly
comparable. The macOS mise figure is approximate; the OS-insensitivity claim leans on the
**mechanism** (below) and the experiment's own timing (mise ~12 s ubuntu ≈ ~14 s macOS),
not on a precise footprint ratio.

**The root difference is the dependency model, not just size:**

- **Nix is content-addressed and hermetic.** Every reference is a *concrete store path*
  (`CC = /nix/store/…-clang-wrapper/bin/cc`), so the build compiler becomes a **runtime**
  dependency that must be materialized — and on darwin that pulls the Apple SDK + Clang +
  LLVM. The price of perfect reproducibility is that the whole closure ships.
- **mise installs prebuilt release binaries** with *loose* references. Its standalone
  python records `CC = cc` (resolved against the system at use-time), so **no compiler or
  SDK is bundled**. Each tool is self-contained; there is no transitive closure to
  explode, and nothing OS-specific blows up on macOS.

This single difference explains all three observed mise advantages from the experiment:

1. **Much smaller** (~300 MB vs flox's 549 MB Linux / 1653 MB macOS) ⇒ far less to
   unpack ⇒ fast provisioning.
2. **OS-insensitive** (~300 MB on both OSes; experiment timing ~12 s ubuntu ≈ ~14 s
   macOS) ⇒ no macOS penalty — because there's no per-OS closure, just per-OS release
   binaries of similar size.
3. **Warm cache works** (experiment: ~4–7 s warm) ⇒ a ~300 MB install dir of few large
   files restores quickly, unlike flox's ~1.6 GB `/nix` of countless tiny files
   (warm ≈ cold).

*Caveat on local timings:* a cold `mise install` (9.6 s, Linux VM) ≈ a cold `flox
activate` (8.45 s) **on this fast VM**, because a fast disk hides the unpack-volume gap.
**Footprint is the robust predictor** that tracks the CI reality (flox macOS 136 s vs
mise macOS ~14 s), not local wall-clock. (npm `commitlint` was excluded from the VM
footprint — node wasn't present; immaterial to the comparison.)

**Takeaway:** flox's cost is intrinsic to the hermetic Nix model (full closure, concrete
refs); fixing candidate #1 narrows but does not erase the gap to mise. If single-source
simplicity + reliability without a Nix tax is the goal, mise is the better CI fit; flox's
value is reproducibility/local-dev parity, where one activation per shell hides the cost.

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
