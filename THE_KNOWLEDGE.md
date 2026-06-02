# THE KNOWLEDGE — the flox CI performance investigation, explained

> A teaching doc, written for someone new to the project (think: smart intern, first
> week). Read top to bottom — each part builds on the last. The goal is that you can
> **explain the why in your own words**, not just repeat the conclusion.
>
> Companion files: `FINDINGS-perf.md` (the formal report), `PROFILE_LOG.md` (the raw
> decision/blocker journal), `experiment/FINDINGS.md` (the earlier benchmark),
> `experiment/profiling/` (the reusable tooling).

---

## ✅ Understanding checklist

Tick these off as you go. If you can't explain one in a sentence, re-read its section.

**1. The problem**
- [ ] What "CI provisioning" is, and why it's separate from "running the checks"
- [ ] What flox / Nix / a "closure" / a "substituter" are (the vocabulary)
- [ ] What we measured: flox CI is 3.8–8.7× slower; ~90% of that is provisioning
- [ ] The competing hypotheses ("branches") for *why* macOS was ~3× worse than Linux

**2. The solution / root cause**
- [ ] Why we used *closure analysis* instead of flame graphs (matching tool to bottleneck)
- [ ] The actual root cause: `python3` on macOS drags ~1.1 GB of Apple SDK + Clang + LLVM into the runtime closure
- [ ] Why that costs *time* — and why it's **unpack** cost, not **download** cost
- [ ] Why "warm cache" barely helped in CI
- [ ] The edge cases/caveats that almost fooled us (warm store, debug Python, cross-arch)

**3. The mise comparison**
- [ ] How mise installs tools differently from flox (release binaries vs Nix closure)
- [ ] Why mise's Python is ~53 MB while flox's drags ~1.1 GB (loose `cc` ref vs concrete store-path ref)
- [ ] Why mise is OS-insensitive and its warm cache works, but flox's doesn't
- [ ] The trade-off: what flox gives you *in exchange* for the tax

**4. The broader context**
- [ ] What changes this implies (the ranked fixes) and their expected impact
- [ ] What the reusable harness gives the team going forward
- [ ] The transferable lessons (silent failures, "don't assume CPU", scoping claims)

---

## Part 0 — the 30-second map

A "py-launch-blueprint" repo can install its dev tools (python, uv, ruff, bun, …) three
ways in CI: **traditional** (a script per tool), **mise**, or **flox**. An earlier
benchmark found flox is **3.8–8.7× slower**, almost entirely in *setup*, worst on macOS.
flox is open source, so we set out to find the **root cause** so it can be fixed.

The answer: on macOS, the `python3` package secretly carries the **C compiler + Apple
SDK** (~1.1 GB) into what gets installed, because of how Python is packaged for macOS.
That triples the amount of data the CI runner has to **unpack onto disk** every run, and
unpacking is the bottleneck — so macOS pays ~3×. Fix the packaging leak and macOS
provisioning should drop to roughly Linux levels.

Everything below is *how we know that*, and *why each piece is true*.

---

## Part 1 — THE PROBLEM

### 1.1 The vocabulary (you need these 5 words)

- **CI provisioning** — before CI can run your tests/linters ("the checks"), it must
  *install the tools*. That install step is "provisioning." It is pure overhead: it
  produces no test results, it just gets you to the starting line. Key idea: **the
  checks and the provisioning are separate costs.** Our whole story is about provisioning.
- **flox** — a tool that declares your whole toolchain in one file and installs it with
  one command (`flox activate`). It's built on **Nix**.
- **Nix** — a package manager where every package lives at a unique path like
  `/nix/store/<hash>-python3-3.12.13`. The hash is computed from *everything* that went
  into building it, so two builds that differ at all get different paths. This makes
  installs reproducible.
- **Closure** — a package plus *everything it depends on*, transitively. Python's closure
  isn't just Python; it's Python + the C library it links + … When flox "installs" your
  env, it must put the **entire closure** of every tool on disk. Remember this word — the
  whole root cause is about closure *contents*.
- **Substituter / binary cache** — Nix doesn't have to *build* a package locally if a
  prebuilt copy exists in a cache (the public one is `cache.nixos.org`). Downloading a
  prebuilt path = "substituting." If no prebuilt copy exists, Nix **builds it locally**
  (slow). "Is this path in the cache?" → "download" vs "build" is a recurring question.

### 1.2 What we observed (the symptom)

From the earlier benchmark (`experiment/FINDINGS.md`, 5 setups × 2 OSes × cold/warm ×
5 reps):

| total run time (avg) | ubuntu cold/warm | macOS cold/warm |
| --- | ---: | ---: |
| traditional | 17 / 17 s | 36 / 39 s |
| flox-consolidated | 65 / 63 s | **182 / 162 s** |

- flox is **3.8× slower on ubuntu, up to ~8.7× on macOS**.
- The *checks themselves run at the same speed* on all three approaches. The entire
  difference is **provisioning** (~90% of a flox job).
- flox is **OS-sensitive**: ~47 s provisioning on ubuntu vs ~136 s on macOS — a **~3×
  macOS penalty**.
- flox's **warm cache barely helps** (~47 s → ~48 s ubuntu). That's strange and becomes
  an important clue.

### 1.3 Why the problem *exists* (drill into the why)

- **Why is flox slower than traditional at all?** Traditional installs only the few tools
  each job needs, as small prebuilt binaries. flox installs the **whole closure** of the
  whole toolchain through Nix every time. More stuff to materialize = more time.
- **Why care, if it's "just setup"?** Because it's paid on **every CI run, by every
  contributor, forever.** A 100 s tax × thousands of runs is real money and developer
  wait time. And it's the one thing blocking flox adoption (which otherwise has nice
  properties: one source of truth, reproducible, 0 flaky failures in the benchmark).
- **Why is flox open source relevant?** Because if we find the cause, we (or upstream)
  can actually fix it — this isn't a vendor black box.

### 1.4 The "branches" — the competing explanations we had to choose between

When you see "macOS is 3× worse," there are several plausible stories. Good debugging =
listing them and finding evidence that *kills* the wrong ones:

1. **Build hypothesis** — macOS has to *compile* some packages locally (no prebuilt in
   the cache) while Linux downloads them. Local compiles are slow → explains macOS.
2. **Download-volume hypothesis** — macOS just has *more/bigger* packages to download.
3. **Cache-broken hypothesis** — the CI cache isn't working, so every run re-does
   everything (this would explain "warm ≈ cold").
4. **Runner-slowness hypothesis** — macOS CI runners are just slower hardware/network.

(There were also the three *approaches* — traditional/mise/flox — but the earlier
experiment already settled those; here we zoom into **flox's** provisioning specifically,
and specifically the **macOS vs Linux** gap.)

The investigation is the story of gathering evidence to pick the right branch. Spoiler:
the truth is a **refinement** of #2 — but the naive version of #2 ("bigger download") is
also wrong; it's bigger **unpack**. Getting that distinction right is the payoff.

---

## Part 2 — THE INVESTIGATION (how we found the truth)

### 2.1 Methodology: top-down, "don't assume CPU" (Brendan Gregg)

The user asked for "deep profiling like Brendan Gregg." His core rule: **characterize the
workload first; don't assume where the time goes.** People reflexively reach for CPU
profilers (flame graphs). But if the bottleneck is disk or network, a CPU flame graph
shows an idle CPU and tells you nothing. So: measure top-down (total → phases → which
resource), *then* reach for the matching tool.

We built a reusable harness (`experiment/profiling/`) to do exactly this: time each phase
of a cold `flox activate`, capture memory/IO, and (on Linux) produce flame graphs.

### 2.2 Lesson: silent failures are the enemy (the harness bugs)

Before trusting *any* measurement, you must trust your *measuring instrument*. We ran a
smoke test and it immediately caught bugs that would have produced **confident, wrong
numbers**:

- **Bug A — timing a function that never ran.** The harness wrapped a command with
  `/usr/bin/time` to measure it. But it accidentally wrapped a *bash function* —
  `/usr/bin/time` can only run real programs, so the function never executed, and the
  phase was recorded as **0.03 s** (looked blazing fast; was actually nothing).
- **Bug B — timing an error.** A flag (`--mode dev-only`) was invalid in this flox
  version. The command errored instantly, and a `|| true` in the code **swallowed the
  error**, recording a fake fast phase.
- *The deeper lesson:* both bugs share a root — **errors were being silently swallowed.**
  We added a rule: if a measured command exits non-zero, print a WARNING. A failed step
  must never be able to masquerade as a fast success. (This is the single most important
  habit in performance work: distrust suspiciously-good numbers.)

> Why this matters to *you*: if we hadn't smoke-tested the instrument, we'd have "found"
> that provisioning is instant and gone looking in the wrong place for days.

### 2.3 The cold-reset saga (a lesson in Nix internals and respecting boundaries)

To measure a *cold* install (empty machine), you must first **delete** the installed
toolchain. This turned out to be surprisingly hard, and each failure taught us something:

- **Attempt 1:** `nix store delete --recursive <env>` → *"experimental feature
  disabled."* Lesson: the modern `nix` CLI is gated; you must enable `nix-command`.
- **Attempt 2 (feature enabled):** *"Cannot delete `glibc` — still alive."* Lesson:
  Nix refuses to delete a path that's still **referenced by something live**. `glibc`
  (the C library) is shared by flox's *own* programs, so it can never be deleted while
  flox is installed. And the delete is **all-or-nothing** — one live path blocks the
  whole closure.
- **Attempt 3:** delete the closure **path-by-path** so live paths are skipped
  individually → freed only ~2 MB. Lesson: flox **roots** (pins) the env it built in its
  own internal bookkeeping, so the toolchain stays "alive" and undeletable.
- **The tempting shortcut:** `nix-collect-garbage` (delete *all* dead paths everywhere).
  This was **denied by a safety boundary** — a global garbage-collect could wipe
  unrelated things on the dev machine. Correct call. Lesson: **a faster path that
  violates a stated constraint is not a valid path.** We respected it.

**The conclusion that changed our approach:** *you cannot reproduce a truly cold install
on a warm machine* (without a global wipe or a fresh VM). This sounds like a dead end. It
was actually the unlock — it forced us to a *better* tool (next section).

### 2.4 The pivot: use the right tool for *this* bottleneck

Flame graphs answer "where is CPU/blocking time spent **while a thing runs**." But our
question was really "**what is in the thing we're installing, and is it downloaded or
built?**" That's a question about **closure contents**, answerable with static Nix
queries — *no cold install required*:

- `nix-store -q --requisites <path>` → list everything in a closure.
- `nix path-info --store https://cache.nixos.org <path>` → "is this in the cache?"
  (download vs build).
- `nix path-info -S` / `--closure-size` → how big.
- `nix why-depends A B` → *why* does A drag in B (the dependency chain).

This is still pure Brendan-Gregg thinking: we *characterized the workload* and the
characterization pointed away from CPU profiling toward closure analysis. Matching the
tool to the bottleneck is the skill.

### 2.5 Killing the wrong branches with evidence

- **Build hypothesis (branch #1): KILLED.** Substitutability check: macOS **80 of 84**
  closure paths are in the cache (downloaded, not built); Linux 60 of 65. The handful
  that "build" are flox's own tiny per-env wrapper files — *on both OSes*. So **macOS is
  not compiling the toolchain.** The intuitive answer was wrong; we have the receipts.
- **Download-volume (branch #2): PARTLY right, and we sharpened it.** The macOS closure
  is much bigger — but we had to be careful about *which* size (see 3.3).
- **Cache-broken (branch #3): reframed.** We read the CI workflow: it **does** cache
  `/nix`. So the cache isn't "broken" — it's that restoring a *huge* cached store is
  itself slow (more in 3.4).

---

## Part 3 — THE SOLUTION / ROOT CAUSE

### 3.1 What we found

On macOS, the realized closure is **1653 MB** vs **549 MB** on Linux (sizes queried from
the cache for the real CI arches, so apples-to-apples). The **~1.1 GB difference is
almost entirely**: `llvm-lib` (380 MB) + `apple-sdk` (371 MB) + `clang-lib` (289 MB) +
llvm/clang. **None of that exists in the Linux closure.**

Then we asked *which package drags it in*. We scanned every tool's closure for those
paths:

```
python3-3.12   → contains 6 of the toolchain paths
everything else (bun, uv, ruff, gh, gitleaks, just, taplo, lefthook, gnumake) → 0
```

And `nix why-depends` gave the exact chain:

```
python3-3.12.13 ─→ apple-sdk-14.4                       (direct reference)
python3-3.12.13 ─→ clang-wrapper ─→ clang-lib ─→ llvm-lib
```

**Root cause: the macOS build of `python3` keeps a runtime reference to the compiler and
Apple SDK it was built with.**

### 3.2 The "why" chain (keep drilling)

- **Why does Python reference the compiler at runtime?** Python ships a module called
  `sysconfig` that records *how Python was built*, including the path to the C compiler,
  so that things like building C extensions (`pip install <package-with-C-code>`) work
  later. On Linux that reference is to gcc/glibc (small). On macOS the C compiler is
  Clang **and Clang needs the Apple SDK**, so the whole ~1.1 GB toolchain gets pinned
  into Python's closure.
- **Why does that make CI slow?** Because flox must materialize the *entire* closure on
  the runner. 1.1 GB of extra paths = 1.1 GB more to put on disk, every run.
- **Why is it 3× (not 1.4×)? — the subtle, important part.** See 3.3.

### 3.3 The key refinement: it's UNPACK cost, not DOWNLOAD cost

Two different "sizes" matter, and conflating them is the trap:

| | x86_64-linux (ubuntu) | aarch64-darwin (macOS) | ratio |
| --- | ---: | ---: | ---: |
| **download** (compressed, over network) | 180 MB | 256 MB | **1.4×** |
| **NAR** (uncompressed, written to /nix) | 549 MB | 1653 MB | **3.0×** |

The macOS time penalty is **~2.9×** — which matches the **uncompressed (3.0×)** ratio,
**not** the compressed-download (1.4×) ratio.

**Why?** The compiler/SDK binaries *compress really well*, so they add little to the
*download*. But they must be **decompressed and written to `/nix` as a huge number of
files**, and *that* — disk writes + per-file filesystem work — is the actual bottleneck.
So the correct statement is: **provisioning is bound by unpack volume (uncompressed bytes
+ file count), not network transfer.**

> Intern takeaway: "it's bigger" is not specific enough. Bigger *where* — on the wire, or
> on the disk? They differ by 2× here, and only one matches the symptom. Always find the
> number that *tracks the thing you're trying to explain.*

### 3.4 Why "warm cache" barely helped (branch #3, resolved)

CI caches `/nix` and restores it on warm runs. So why is warm (~47 s) ≈ cold (~47 s)?
Because **restoring the cache means un-tarring the same huge uncompressed `/nix`** — the
same unpack cost we just identified. The cache changes *where the bytes come from*
(GitHub cache vs `cache.nixos.org`), not *how many uncompressed bytes hit the disk*. So
shrinking the closure (the #1 fix) is what makes warm cheap too. The cache isn't broken;
it's fighting the wrong cost.

### 3.5 The fix (design decisions + expected impact)

Ranked in `FINDINGS-perf.md`; the dominant one:

1. **Strip Python's darwin SDK/compiler runtime leak.** Expected: macOS closure
   1653 → ~530 MB (≈ Linux) ⇒ macOS provisioning potentially ~3× faster (~136 → ~50 s),
   every run. *Design choices, fastest-to-try first:* (a) a newer nixpkgs `python3` that
   already drops the reference; (b) `python3Minimal` if we don't need `distutils`/headers
   in CI; (c) a flox overlay that removes the SDK from Python's runtime output. Each is a
   different trade between effort and how much Python functionality you keep.
2. Dedupe duplicated libs (two `glibc` / two `libiconv` versions coexist).
3. Confirm the debug-Python is only a local artifact (it was).
4. Treat the warm cache cost as a size symptom, not a cache bug.
5. *Confirmatory* flame graph of a cold install (the literal Brendan-Gregg artifact) — to
   visually prove the time is decompress + disk-write, not network. (Stage in progress;
   documented below as it's produced.)

### 3.6 Edge cases / things that almost fooled us

- **Warm store on the dev Mac.** Our Mac already had everything installed, so a local
  "cold" measurement was impossible — we had to query the cache and use a VM. *Lesson:
  your measurement environment can lie if its state differs from production (CI).*
- **Debug Python.** The Linux *VM* happened to realize `python3-3.12.13-debug` (bigger,
  slower) while the cache-locked closure uses the normal build. If we'd trusted the VM's
  realized size, our Linux baseline would've been wrong. *Lesson: prefer the
  source-of-truth (the lock + cache) over an incidental local realization.*
- **Cross-arch comparison.** Our VM is ARM Linux; CI ubuntu is x86. We re-queried sizes
  for the *actual* CI arches so the 3× ratio is honest, not arch-mixed.
- **Overclaiming causation.** We almost wrote "closure size *explains* the CI penalty."
  An advisor flagged that warm≈cold seemed to contradict "download-bound." Reading the
  workflow + the unpack-vs-download split resolved it — but we **scoped the claim**: the
  1.1 GB leak is *proven*; its exact CI wall-clock impact is *inferred* pending one
  per-step CI timing run. *Lesson: separate what you proved from what you inferred.*

---

## Part 4 — COMPARING flox vs mise (why the alternative is fast)

The team also tests **mise**, which installs the *same logical toolchain* but is much
faster. Understanding *why* makes the flox finding click into place — it's the same root
issue seen from the other side.

### 4.1 The measurements

| | flox (Nix closure) | mise (release binaries) |
| --- | ---: | ---: |
| macOS footprint | **1653 MB** | **285 MB** (~5.8× smaller) |
| Linux footprint | 549 MB | 350 MB |
| macOS ÷ Linux | **3.0× (OS-sensitive)** | ~1× (OS-insensitive) |
| Python | pulls Apple SDK + Clang + LLVM (~1.1 GB) | 53–87 MB standalone, no SDK |

### 4.2 Why mise dodges the bullet (the one idea that explains everything)

The difference is the **dependency model**:

- **flox/Nix is hermetic and content-addressed.** To guarantee a build is *perfectly
  reproducible*, every reference must be an *exact* path: Nix's Python literally records
  `CC = /nix/store/…-clang/bin/cc`. That exact compiler is now a **runtime dependency**
  and must be installed — and on macOS it drags the whole Apple SDK + LLVM. **The price of
  reproducibility is shipping the entire closure.**
- **mise installs prebuilt release binaries with *loose* references.** Its standalone
  Python records `CC = cc` — "use whatever `cc` is around at the time." Nothing is pinned,
  so **no compiler or SDK is bundled.** Each tool is its own self-contained download; there
  is no transitive closure to explode.

> Analogy: flox is like shipping a recipe *plus the exact farm every ingredient came
> from*; mise ships the finished dish and trusts your kitchen has salt. The first is
> perfectly reproducible and enormous; the second is small and "good enough."

### 4.3 Why this explains all three of mise's wins

1. **Smaller** (285 vs 1653 MB on macOS) → less to unpack → fast.
2. **OS-insensitive** → no macOS penalty, because there's no per-OS *closure* to blow up,
   just per-OS *binaries* of similar size. (flox's 3.0× macOS blow-up is the SDK leak;
   mise has nothing equivalent.)
3. **Warm cache actually helps** → ~300 MB of a few big files restores fast; flox's 1.6 GB
   of countless tiny files is slow to restore (which is why flox warm ≈ cold).

### 4.4 The honest trade-off (don't oversell either)

flox isn't "bad" — it buys **true reproducibility** and **identical local-dev /
devcontainer / CI environments** from one file. The closure tax is the cost of that
guarantee, and in *local dev* it's paid once per shell (invisible). It only hurts in
**CI**, where you pay it every run. Fixing the Python leak (candidate #1) **narrows** the
gap but can't fully erase it — the hermetic model inherently ships more. So the decision
(tracked in ADR-12) is a values choice: **reproducibility (flox) vs CI speed + simplicity
(mise)**, not "which is better" in the abstract.

> Intern takeaway: the comparison isn't "mise wins." It's "these tools make *opposite
> trade-offs*, and now you can articulate exactly what each costs and buys." That's what
> lets a team choose deliberately.

## Part 5 — BROADER CONTEXT (why this matters)

### 4.1 What the changes impact

- **If the Python leak is fixed:** macOS flox CI could go from ~136 s to ~50 s
  provisioning — closing most of the macOS penalty and making flox far more viable as the
  single-source-of-truth toolchain. That decision is tracked in **ADR-12**.
- **It's likely an upstream win:** the leak is in nixpkgs' darwin Python packaging, so
  fixing it helps *every* Nix/flox user on macOS, not just this repo. That's leverage.
- **The reusable harness** (`experiment/profiling/`) means the team can re-run this
  analysis after any toolchain change — performance findings don't rot.

### 4.2 Transferable lessons (the real curriculum)

1. **Separate the costs.** "CI is slow" → is it provisioning or the checks? Don't
   optimize the part that isn't the problem.
2. **Don't assume CPU.** Characterize first; pick the tool the bottleneck demands. Here
   the right tool was closure analysis, not a flame graph.
3. **Distrust good numbers.** A 0.03 s phase was a bug, not a win. Make failures loud.
4. **Find the number that tracks the symptom.** Download (1.4×) vs unpack (3.0×) — only
   one matched the 3× penalty. That choice *is* the insight.
5. **Respect boundaries even when slower.** The global-GC shortcut was off-limits; the
   constraint pushed us to a better method.
6. **Scope your claims.** Proven ≠ inferred. Say which is which.

---

*Living doc — extended as remaining stages (the confirmatory cold flame graph) are run.*
