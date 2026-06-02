# Flox deep-profiling — decision & blocker log

Running log of decisions, errors overcome, blockers, and unexpected findings while
building + running the flox cold-provision profiler. Newest entries at the bottom.
Companion to the harness (`experiment/profiling/`), the playbook
(`experiment/PROFILING.md`), and the root-cause report (`FINDINGS-perf.md`).

Branch: `experiment/flox-ci-timing-perf-analysis`. Goal: root-cause flox's CI
provisioning cost (3.8–8.7× slower than traditional; ~90% provisioning) to a
fixable level, with flame graphs + ranked candidates.

---

## 2026-06-01 — Harness built (T1–T9), then validated

Built a cross-platform harness via subagent-driven development: a stdlib Python
analysis layer (`analyze.py`, 5 tests) + bash helpers (`phases.sh`, `cold_reset.sh`,
`sample.sh`, `io.sh`, `deep_linux.sh`) + orchestrator (`profile-flox.sh`) + a
dedicated isolated flox env (`flox-env/`, locked for 4 systems).

### Bugs the smoke gate caught (all fixed)
- **run_phase wrapped a shell function with `/usr/bin/time`.** The orchestrator ran
  `run_phase ... -- sample_cmd ...`, but `/usr/bin/time` execs a *real program* and
  can't see a bash function → the dominant phase was silently measured as ~0s.
  Fixed: time the raw `flox activate` binary; sample the nix-daemon by PID instead.
- **`--mode dev-only` is invalid in flox 1.12.1** (only `dev` / `run`). lock-eval was
  timing an *error* that `run_phase`'s `|| true` swallowed into a fake 0.1s phase.
  Fixed the flag **and** made `run_phase` emit a WARNING on non-zero exit — silent
  swallowing is *how* both phantoms slipped through.
- **Deep branch flamed a cold run, then timed a warm cache hit** (review-found). The
  off-CPU flame consumed the cold store, then the timed re-activate was a flox cache
  hit. Fixed: re-cold before the timed realize.

### Learning: macOS host cannot reproduce a true cold provision
Scoped cold-reset can only free an env's *unshared* paths, and flox short-circuits a
2nd back-to-back activate via an activation cache (warm activate ≈ 0.06s vs cold
8.45s). So genuine cold numbers must come from a disposable store (Lima/CI), not the
dev Mac. Documented inline + in PROFILING.md.

---

## 2026-06-01 — Lima Linux deep leg

### Setup
- VM `ubuntu`: **Ubuntu 25.10 aarch64, kernel 6.17**, BTF present
  (`/sys/kernel/btf/vmlinux`) → eBPF-ready. `perf`, `offcputime-bpfcc`, `bpftrace`
  already installed; `git` present; net to cache.nixos.org works.
- The repo is mounted **read-only**, so the harness was copied to `~/work` (writable)
  and the VM's own fresh nix store is the cold environment.
- flox 1.12.1 installed via the official aarch64 `.deb` (sets up nix + daemon).
- FlameGraph cloned to `~/FlameGraph` for `flamegraph.pl`.

### Unexpected: baseline cold is *fast* on Linux
First-ever cold `flox activate` (aarch64-linux) = **8.45s** (warm = 0.06s). That is far
below CI's ~47s ubuntu / ~136s macOS. **Early signal: Linux cold is download-bound and
cheap; the macOS 3–9× penalty is the real target and is likely local *builds*** (paths
not substitutable on darwin). This must be verified with nix `building` vs
`copying path from cache` evidence — the headline can't rest on the 8s Linux case.

### Unexpected: the env pulls a *debug* Python
The realized closure contains `python3-3.12.13-debug` (a debug build, larger/slower).
Flagged for follow-up — if debug variants aren't cached they'd be built locally,
which could feed the macOS penalty.

### Bug: `cold_reset` needs the nix-command experimental feature
`nix store delete` failed in the vanilla VM with *"experimental Nix feature
'nix-command' is disabled"*. The dedicated `--extra-experimental-features` flag is
**not honored early enough** to unlock the subcommand; `--option
extra-experimental-features nix-command` and `NIX_CONFIG` both work. Harness updated
to the `--option` form. (`--help` masks this — the gate only fires at runtime.)

### Blocker → key learning: scoped `--recursive` delete frees nothing on a flox store
Even with the feature enabled, `nix store delete --recursive <env>` **refuses** because
`glibc` is "still alive" (shared with flox's *own* runtime closure) and `--recursive`
is all-or-nothing. So the spec's assumption *"a disposable Lima VM yields a fully cold
store"* is **false once flox itself is installed in the VM** — the toolchain shares base
paths with flox. Diagnosis: the toolchain paths (python312, etc.) have **no gc-roots**
(dead) once the `.flox/run` links are removed; only shared base paths stay alive.

### Blocker: global GC is denied (correctly)
`nix-collect-garbage` would evict the dead toolchain, but it is a **global GC** and was
**denied by the permission boundary** — the user's standing constraint is that
cold-reset must only touch the env closure, never a global GC. Respecting that.
**Decision:** use a **scoped per-path delete** over the env's closure
(`nix-store -q --requisites <env>` → `nix store delete <path>` each; live shared paths
are skipped). This frees the dead toolchain while staying inside the env-closure
boundary — and is the correct fix for the harness `cold_reset` too (replace the
all-or-nothing `--recursive` delete with per-path deletes).

### Blocker confirmed: scoped cold-reset cannot evict the toolchain at all
Per-path delete only freed the 2 MB env *wrapper*; the 600–1700 MB toolchain stayed.
`nix-store -q --roots` misses *in-use* roots (running processes), so liveness is
transitive and subtle, and **flox roots the realized env in its own internal gc-root**,
keeping the whole toolchain alive. Conclusion: **a true cold provision is not
reproducible on a warm host** without a global GC (out of bounds) or a fresh store.
Pivoted away from cold-reset to **closure-composition analysis**, which needs no
deletion and is the *apt* tool for a download-volume bottleneck (characterize first,
don't assume CPU).

---

## 2026-06-01 — ROOT CAUSE FOUND (closure analysis)

Reframed the question with deletion-free Nix queries (`path-info`, substitutability vs
`cache.nixos.org`, `why-depends`):

1. **Refuted the build hypothesis.** Both OSes are download-bound: macOS 80/84 paths
   cached, Linux 60/65 — the few uncached are flox's own tiny env wrappers. macOS does
   **not** compile the toolchain.
2. **The penalty is closure SIZE.** darwin closure **1714 MB** vs linux **600 MB**
   (~2.9×) ≈ the experiment's ~3× macOS time penalty.
3. **The ~1.2 GB darwin excess is LLVM + Clang + Apple SDK**, absent on Linux.
4. **Culprit = `python3`.** Only python's closure carries the toolchain (6 paths; every
   other tool 0). Chain: `python3 → apple-sdk-14.4` (direct) and
   `python3 → clang-wrapper → clang-lib → llvm-lib`. nixpkgs darwin python retains a
   runtime ref to its build compiler/SDK via `sysconfig`.

**Unexpected discrepancy logged:** the Lima closure pulled `python3-3.12.13-debug`
while the Mac pulled the normal `python3-3.12.13` — flagged as candidate #3.

Full write-up + ranked fixes in `FINDINGS-perf.md`. The signature cold flame graph is
now *confirmatory* (candidate #5), needing a fresh Lima VM for a genuine cold store.

### Reconcile: scoping the CI causal claim (advisor catch)
Advisor flagged an overclaim: the experiment shows flox CI **warm ≈ cold** (ubuntu
46.5/47.6 s; macOS 135.8/129.0) — opposite of local (cold 8.45 s, warm 0.06 s). If
download volume drove CI cost *and* the cache restored `/nix`, warm would collapse.
**Read the workflow** (`.github/actions/provision-flox/action.yml`): it **does** cache
`/nix` + `~/.cache/flox` (`actions/cache@v4`, stable warm key). So warm ≈ cold means
**restoring + untarring a 0.6–1.7 GB `/nix` ≈ cold download** — both volume-bound, so
closure size is still the lever, but the warm mechanism is restore/extract, not network.
Reframed FINDINGS: SDK leak = **confirmed 1.2 GB bloat, high confidence**; "explains the
3× CI penalty" **downgraded to inferred** pending per-step CI timing. Also confirmed
`macos-latest` = arm64 (darwin size is arch-consistent); `ubuntu-latest` = x86_64 so the
2.9× ratio is cross-arch/suggestive; the Linux 600 MB baseline is inflated by a debug
python — exact ratio approximate, mechanism unaffected.

### Arch-rigorous sizing (advisor follow-up)
Queried closure sizes straight from `cache.nixos.org` for the real CI arches:
x86_64-linux 549 MB NAR / 180 MB download; aarch64-darwin 1653 MB / 256 MB;
aarch64-linux 551 MB (≈ x86_64 ⇒ Lima representative; debug-python was a realization
artifact, not in the locked closure). **Sharper finding:** the macOS penalty tracks the
**uncompressed** ratio (3.0×) not the **compressed download** (1.4×) ⇒ the bottleneck is
**decompress + write-to-`/nix`** (unpack), not network — which also explains warm ≈ cold.

---

## 2026-06-01 — mise comparison (after flox, by request)

Same closure/footprint method applied to mise (`experiment/mise.toml`, same logical
toolchain):

- **Footprint:** mise Linux **350 MB** vs flox **549 MB** (same-OS, most rigorous); mise
  macOS ~298 MB vs flox 1653 MB. mise ≈ same on both OSes (no 3× explosion) vs flox
  **3.0× (OS-sensitive)**.
- **Measurement-rigor fix (advisor catch):** first macOS mise `du` used a *lexical*
  `sort|tail -1` and grabbed python **3.13.13** (not pinned 3.12.13) + uv 0.11.3 — an
  artifact on the cluttered global mac mise (same class of bug as the flox harness ones).
  Re-measured via `mise where` (mise-resolved dirs) → 298 MB. Reframed both docs to lead
  with the clean same-OS Linux numbers + mechanism, and softened precise cross-tool ratios.
- **Mechanism (the crux):** mise standalone python records `CC = cc` (loose ref, no
  compiler bundled); flox/Nix python records `CC = /nix/store/…-clang` (concrete ref) →
  must materialize apple-sdk + clang + llvm. **Content-addressed hermetic model (flox)
  ships the whole closure incl. build compiler; release-binary model (mise) doesn't.**
- Explains all 3 mise wins: smaller → fast; OS-insensitive (no per-OS closure); warm
  cache works (small few-file dir restores fast).
- **Caveat:** local cold `mise install` 9.6 s ≈ `flox activate` 8.45 s on the fast VM —
  the disk hides the unpack gap; **footprint is the robust predictor** (matches CI flox
  macOS 136 s vs mise ~14 s), not local wall-clock.
- Written up in `FINDINGS-perf.md` ("flox vs mise") + `THE_KNOWLEDGE.md` Part 4.
- (npm commitlint excluded from VM footprint — node absent in VM; immaterial.)

---

## 2026-06-02 — CI timing run (measured) + flame graphs (by request)

Dispatched `flox-mirror-suite` (ubuntu + macOS, cold + warm) on
`experiment/flox-ci-timing`; read per-step timings from logs.

**(1) macOS 3× penalty CONFIRMED on real CI.** `provision (flox)` step: ubuntu cold 36 s
vs **macOS cold 114 s (~3.2×)** — matches the 3.0× closure-size ratio. (+Post cache-save
11 s ubuntu / 30 s macOS.)

**(2) "warm ≈ cold" root cause CORRECTED — it's a cache-SAVE bug, not slow restore.** My
earlier inference (restore-untar ≈ download) was **wrong**. Logs show the `/nix` cache is
**never saved**: `tar: /nix/var/nix/db/reserved: Cannot open: Permission denied` →
`##[warning]Failed to save … exit code 2` → no `flox-warm-*` key (`gh cache list` empty) →
every warm run is a cache **miss** (`Cache not found for input keys: flox-warm-…-stable`)
→ re-downloads. Same failure on macOS (`gtar` on `gc.lock`/`db/reserved`/`userpool`).
Concrete, fixable, cross-OS. Elevated to candidate #4 (was the disproven "size symptom").

**(3) Flame graphs (illustrative, fresh Lima qemu VM, cold activate ~12 s).** Built a
throwaway `floxflame` VM (factory-reset between shots for a genuine cold store, since flox
roots the realized env so scoped delete can't re-cold in place — same blocker as before).
- on-CPU (perf): `cpuidle_idle_call` dominates (CPU idle) + `lzma_decode`/`sha256`
  (decompress/verify). An idle on-CPU flame = proof the bottleneck isn't CPU.
- off-CPU (eBPF offcputime): `nix-daemon` + `tokio-runtime-w` block the most → I/O wait
  (network recv + disk write/unpack). Bug found+fixed mid-capture: `offcputime -d` + SIGINT
  aborts before flush → use a short `-d` window and let it finish (no signal).
- Artifacts: `experiment/profiling/results/flox-cold-activate.{on,off}cpu.svg`.
- Caveat: qemu VM is ~illustrative, not CI-magnitude (advisor's point); used to *see* the
  on/off-CPU split, not to attribute CI wall-clock. The CI attribution comes from §4 above.
