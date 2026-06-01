# Flox deep-profiling harness — design

- Date: 2026-06-01
- Branch: `experiment/flox-ci-timing-perf-analysis`
- Status: design (awaiting user review)
- Related: [`experiment/FINDINGS.md`](../../../experiment/FINDINGS.md),
  [ADR-12](../../adr/0012-flox-environment-management.md)

## Goal

The CI timing experiment showed flox is **3.8× slower on ubuntu and up to ~8.7× on macOS**,
and that **~90–94% of a flox job is provisioning** (not the checks). flox is open source, so
the next step is to **root-cause that provisioning cost to a fixable level** — attribute it to
a specific operation (download vs unpack vs nix-eval vs activation vs cache-save) and produce
**ranked optimization candidates** that could be addressed (likely upstream in flox/nix).

Deliverable: a **reusable, cross-platform profiling harness** (re-runnable as flox is
optimized) plus an initial **root-cause report**.

## Non-goals

- Not profiling `traditional`/`mise` (they're the fast baselines, not the optimization
  target). Contrast profiling is a later option.
- Not patching flox in this work — the deliverable is root-cause + ranked candidates;
  fixes are downstream (possibly upstream PRs).
- Not wiring a GitHub Actions profiling workflow in the first plan — the harness is
  CI-runnable, but GHA wiring is a documented follow-up. Start local (Mac), then Lima/Linux.

## Methodology (top-down, Brendan-Gregg)

Measure top-down; **do not assume CPU**. Provisioning is likely I/O/network-bound.

1. **Characterize** the flox cold-provision workload (the phases below).
2. **Latency breakdown** — split wall-clock into phases; find the dominant phase.
3. **Resource attribution** (USE lens) of the dominant phase — CPU, off-CPU (blocked on
   disk/network), disk, or network?
4. **Drill** with the matching tool — on-CPU flame graph (CPU), **off-CPU flame graph**
   (blocking), download bytes/time (network), I/O syscall summary (disk).
5. **Output** ranked root causes → flox fix candidates.

## Phases (instrumented; each gets timestamps + resource stats)

| phase | what | likely-dominant resource |
| --- | --- | --- |
| `flox-install` | install the flox binary (CI-relevant; local one-time baseline) | net/disk |
| `lock-eval` | `flox` resolve/lock + Nix evaluation | CPU (flox Rust + nix eval) |
| `realize` | `nix-daemon` downloads + unpacks the env's store closure | network + disk |
| `build` | closure paths not substitutable get built (expected larger on macOS) | CPU + disk |
| `activate` | flox sets up PATH/hook/profile + runs activation | CPU/disk (small) |
| `cache-save` | CI-only: `actions/cache` of `/nix` | disk |

Splitting `realize` from `build` is deliberate: if macOS lacks a substituter for some darwin
paths it **builds** (a different, upstream-fixable root cause than slow downloads).

## Environment

- **macOS (start here):** local profiling on the dev Mac (aarch64-darwin). Tools: `samply`
  (CPU flame graphs, cross-platform), `/usr/bin/time -l` (RSS/faults/IO), `fs_usage` (sudo,
  file-I/O attribution), `sample`, `nettop`. No eBPF/`perf` (SIP).
- **Linux-deep (comparison):** a **Lima VM, Ubuntu 24.04 aarch64, `vz` backend** — a full
  controllable kernel with BTF, run profiling directly in the VM as root. Tools: `samply` +
  `perf record -g` (on-CPU), **eBPF `offcputime` → off-CPU flame graph** (the linchpin),
  `strace -f -c` (syscall summary), `biolatency`/`biosnoop` (disk), `tcplife` (network).
  Confirm readiness: `/sys/kernel/btf/vmlinux` exists; install `bpfcc-tools bpftrace
  linux-tools-$(uname -r)`.
  - Arch caveat: Lima is aarch64-linux (CI is x86_64). The flox lock already includes
    `aarch64-linux`, so `flox activate` works. Deep profiling is about *mechanism/attribution*
    (transfers across arch); CI/x86 remains the source of headline timings.
- **Containers (optional):** Docker/Podman are weaker for tracing (shared VM kernel) but handy
  for a disposable-cold `/nix`. Not required — the scoped cold-reset works in the VM directly.

## Cold reproduction (scoped, non-destructive, repeatable)

Before each cold run, **delete only the target env's Nix store closure** (`nix store delete`
of the env's paths — NOT a full `nix-collect-garbage`), so the next `flox activate`
re-downloads/realizes cold while the rest of the store stays warm. Iterable locally on mac +
Lima. Warm runs skip the reset. (`build` from CI cold is genuinely cold; local approximates
it well via scoped delete.)

## The nix-daemon catch

The `realize` heavy lifting runs in the separate `nix-daemon` process, not a child of `flox`.
The harness discovers the daemon PID and profiles it explicitly: macOS `samply record --pid
<nix-daemon>` over the realize window; Linux `perf record -a` (system-wide) + eBPF naturally
include the daemon.

## Per-phase tooling contract

| signal | macOS | Linux (Lima) |
| --- | --- | --- |
| wall-clock | timestamps | timestamps |
| resource (RSS/faults/IO) | `/usr/bin/time -l` | `/usr/bin/time -v` |
| CPU flame graph | `samply record` | `samply` or `perf record -g` |
| I/O attribution | `fs_usage` (sudo) | `strace -f -c` |
| off-CPU / blocking | — (SIP) | eBPF `offcputime` → off-CPU flame graph |
| disk / network detail | `nettop`, time-`-l` IO | `biolatency`/`biosnoop`, `tcplife` |

## Outputs

- `phases.json` + `phases.csv` — per-phase wall-clock + resource stats (latency breakdown),
  tagged os/cache/run.
- Flame graphs — `samply` profiles + `.svg` per dominant phase; off-CPU flame graph (Linux).
- `FINDINGS-perf.md` — root-cause report: phase breakdown → dominant phase → resource
  attribution → **ranked flox optimization candidates** (each: what · evidence · est. impact ·
  where in flox/nix · upstream-fixability).

## File structure

```
experiment/profiling/
  profile-flox.sh        # orchestrator: cold-reset -> phased run -> collect artifacts
  lib/
    phases.sh            # phase timestamp + /usr/bin/time resource capture (mac/linux)
    sample.sh            # samply wrappers (target process + nix-daemon pid)
    io.sh                # fs_usage (mac) / strace -c (linux)
    deep_linux.sh        # eBPF offcputime + perf + biolatency/tcplife (Lima only)
    cold_reset.sh        # scoped delete of the env's nix closure
  analyze_profile.py     # parse phases.json -> phase table (md) + report skeleton
  fixtures/              # synthetic phases.json for unit-testing analyze_profile
  results/               # phase tables + flame-graph SVGs (sample committed)
experiment/PROFILING.md  # methodology playbook + how-to (mac / Lima / CI-later)
FINDINGS-perf.md         # root-cause report (filled after runs)
tests/experiment/test_analyze_profile.py
```

Helpers stay small and single-purpose (mirrors `experiment/bench/`): each OS-specific branch
lives in one file, so adding a tool or OS touches one place, not the orchestrator.

## Validation gates

1. **Harness unit** — `analyze_profile.py` renders the phase table + report skeleton from a
   synthetic `phases.json` (zero profiling; TDD'd under `tests/experiment/`).
2. **Smoke (Mac)** — one `profile-flox.sh` run against a cold-reset env produces `phases.json`
   + ≥1 flame graph; phase times ≈ the experiment's known cold provision (sanity).
3. **Linux-deep (Lima)** — same harness in the VM produces an off-CPU flame graph + perf
   on-CPU flame graph for the dominant phase.
4. **Root-cause pass** — fill `FINDINGS-perf.md` with the attribution + ranked candidates.

## Risks / open questions

- macOS off-CPU blindness (SIP) — mitigated by inferring from Linux off-CPU + `fs_usage`.
- `samply` not capturing the nix-daemon by default — mitigated by explicit `--pid`.
- Arch difference (aarch64 Lima vs x86_64 CI) — mechanism transfers; numbers don't.
- Scoped cold-reset must target only the env closure (never a global GC).
