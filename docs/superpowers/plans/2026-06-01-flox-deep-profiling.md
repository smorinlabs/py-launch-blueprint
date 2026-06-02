# Flox Deep-Profiling Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable, cross-platform harness that root-causes flox's CI *provisioning* cost — decomposing a cold `flox` provision into timed phases, attributing the dominant phase to CPU/off-CPU/disk/network with Brendan-Gregg tooling, and producing flame graphs + a ranked-fix-candidate report.

**Architecture:** A stdlib-only Python analysis module (`experiment/profiling/analyze.py`, TDD'd) renders a phase table + report skeleton from a `phases.json` contract. Small single-purpose bash helpers (`lib/*.sh`) capture per-phase wall-clock/resource/IO/flame-graph data; an orchestrator (`profile-flox.sh`) cold-resets a dedicated flox env, runs the phases, and assembles `phases.json` + flame graphs. macOS uses `samply`/`fs_usage`; Linux (Lima) adds `perf` + eBPF off-CPU flame graphs.

**Tech Stack:** bash, Python 3.12 (stdlib), `samply` (cross-platform sampler), `/usr/bin/time`, `fs_usage` (macOS), `perf` + `bpfcc-tools`/`bpftrace` (Linux/Lima), `nix store delete`, flox.

**Spec:** `docs/superpowers/specs/2026-06-01-flox-deep-profiling-design.md`

---

## Conventions

- Branch: `experiment/flox-ci-timing-perf-analysis` (already checked out).
- Run python/tests inside the flox env: `flox activate -- uv run pytest …` (dogfooding rule; the env provides python312 + uv). Shell-syntax check: `bash -n <file>`.
- Tests live under `tests/experiment/`; run with `flox activate -- uv run pytest tests/experiment/test_analyze_profile.py --override-ini="addopts=" -q`.
- `analyze.py` is **stdlib-only** (json, dataclasses) so it runs as `python3 -m experiment.profiling.analyze` with no deps and is unit-testable.
- All Python: `from __future__ import annotations`, line ≤ 88, Python 3.12.

## The `phases.json` contract (source of truth shared by shell + Python)

```json
{
  "meta": {"os": "macos", "arch": "arm64", "cache": "cold", "flox_version": "1.x",
           "env": "profiling", "ts": "2026-06-01T12:00:00Z"},
  "phases": [
    {"name": "lock-eval", "seconds": 2.1, "max_rss_mb": 110.0,
     "io_read_mb": 5.0, "io_write_mb": 1.0},
    {"name": "realize", "seconds": 40.0, "max_rss_mb": 300.0,
     "io_read_mb": 250.0, "io_write_mb": 400.0}
  ],
  "artifacts": {"flamegraphs": ["realize.cpu.svg"]}
}
```

Phase names (fixed vocabulary): `flox-install`, `lock-eval`, `realize`, `build`, `activate`,
`cache-save`. Fields not measurable on a platform are `0.0` (never omitted).

---

## File Structure

- Create: `experiment/profiling/__init__.py` (empty — makes it an importable subpackage)
- Create: `experiment/profiling/analyze.py` — parse `phases.json` → phase table + report skeleton
- Create: `experiment/profiling/fixtures/sample_phases.json` — synthetic profile for tests
- Create: `tests/experiment/test_analyze_profile.py`
- Create: `experiment/profiling/lib/phases.sh` — `run_phase` wall-clock + resource capture
- Create: `experiment/profiling/lib/cold_reset.sh` — scoped delete of the env's nix closure
- Create: `experiment/profiling/lib/sample.sh` — `samply` wrappers (process + nix-daemon pid)
- Create: `experiment/profiling/lib/io.sh` — `fs_usage` (mac) / `strace -c` (linux)
- Create: `experiment/profiling/lib/deep_linux.sh` — eBPF off-CPU + `perf` (Lima only)
- Create: `experiment/profiling/profile-flox.sh` — orchestrator
- Create: `experiment/profiling/flox-env/manifest.toml` — dedicated profiling env (copy of the experiment toolchain)
- Create: `experiment/PROFILING.md` — methodology playbook + how-to
- Create: `FINDINGS-perf.md` — root-cause report (skeleton; filled after runs)

---

## Phase 1 — Analysis layer (TDD, Python, zero profiling)

### Task 1: Profile dataclasses + loader

**Files:**
- Create: `experiment/profiling/__init__.py` (empty)
- Create: `experiment/profiling/analyze.py`
- Test: `tests/experiment/test_analyze_profile.py`
- Create: `experiment/profiling/fixtures/sample_phases.json`

- [ ] **Step 1: Write the fixture**

Create `experiment/profiling/fixtures/sample_phases.json`:

```json
{
  "meta": {"os": "macos", "arch": "arm64", "cache": "cold", "flox_version": "1.12.1",
           "env": "profiling", "ts": "2026-06-01T12:00:00Z"},
  "phases": [
    {"name": "flox-install", "seconds": 3.0, "max_rss_mb": 40.0, "io_read_mb": 10.0, "io_write_mb": 30.0},
    {"name": "lock-eval", "seconds": 2.0, "max_rss_mb": 120.0, "io_read_mb": 2.0, "io_write_mb": 0.5},
    {"name": "realize", "seconds": 90.0, "max_rss_mb": 300.0, "io_read_mb": 250.0, "io_write_mb": 600.0},
    {"name": "build", "seconds": 8.0, "max_rss_mb": 200.0, "io_read_mb": 5.0, "io_write_mb": 40.0},
    {"name": "activate", "seconds": 2.0, "max_rss_mb": 80.0, "io_read_mb": 1.0, "io_write_mb": 1.0}
  ],
  "artifacts": {"flamegraphs": ["realize.cpu.svg", "realize.offcpu.svg"]}
}
```

- [ ] **Step 2: Write the failing test**

Create `tests/experiment/test_analyze_profile.py`:

```python
from __future__ import annotations

from pathlib import Path

from experiment.profiling.analyze import (
    Phase,
    dominant_phase,
    load_profile,
    total_seconds,
)

FIX = Path(__file__).parent.parent.parent / "experiment/profiling/fixtures"


def test_load_profile_reads_meta_and_phases():
    p = load_profile(FIX / "sample_phases.json")
    assert p.os == "macos"
    assert p.cache == "cold"
    assert len(p.phases) == 5
    assert p.phases[2] == Phase("realize", 90.0, 300.0, 250.0, 600.0)


def test_total_seconds_sums_phases():
    p = load_profile(FIX / "sample_phases.json")
    assert total_seconds(p) == 105.0


def test_dominant_phase_is_max_seconds():
    p = load_profile(FIX / "sample_phases.json")
    assert dominant_phase(p).name == "realize"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `flox activate -- uv run pytest tests/experiment/test_analyze_profile.py --override-ini="addopts=" -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'experiment.profiling'`

- [ ] **Step 4: Write minimal implementation**

Create `experiment/profiling/__init__.py` (empty) and `experiment/profiling/analyze.py`:

```python
#!/usr/bin/env python3
"""Analyze a flox-provisioning phases.json into a phase table + report skeleton.

Stdlib-only so it runs as `python3 -m experiment.profiling.analyze <phases.json>`
with no dependencies, and is unit-testable.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Phase:
    name: str
    seconds: float
    max_rss_mb: float
    io_read_mb: float
    io_write_mb: float


@dataclass(frozen=True)
class Profile:
    os: str
    arch: str
    cache: str
    flox_version: str
    phases: list[Phase]
    flamegraphs: list[str]


def load_profile(path: Path) -> Profile:
    raw = json.loads(Path(path).read_text())
    meta = raw["meta"]
    phases = [
        Phase(
            p["name"],
            float(p["seconds"]),
            float(p["max_rss_mb"]),
            float(p["io_read_mb"]),
            float(p["io_write_mb"]),
        )
        for p in raw["phases"]
    ]
    fgs = raw.get("artifacts", {}).get("flamegraphs", [])
    return Profile(
        os=meta["os"],
        arch=meta.get("arch", ""),
        cache=meta["cache"],
        flox_version=meta.get("flox_version", ""),
        phases=phases,
        flamegraphs=fgs,
    )


def total_seconds(p: Profile) -> float:
    return sum(ph.seconds for ph in p.phases)


def dominant_phase(p: Profile) -> Phase:
    if not p.phases:
        raise ValueError("profile has no phases")
    return max(p.phases, key=lambda ph: ph.seconds)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `flox activate -- uv run pytest tests/experiment/test_analyze_profile.py --override-ini="addopts=" -q`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add experiment/profiling/__init__.py experiment/profiling/analyze.py experiment/profiling/fixtures/sample_phases.json tests/experiment/test_analyze_profile.py
git commit -m "feat(profiling): add phases.json loader + profile model"
```

---

### Task 2: Phase table + report skeleton renderer

**Files:**
- Modify: `experiment/profiling/analyze.py` (add `phase_table`, `render_report`, `main`)
- Test: `tests/experiment/test_analyze_profile.py` (add cases)

- [ ] **Step 1: Write the failing test (append)**

Append to `tests/experiment/test_analyze_profile.py`:

```python
from experiment.profiling.analyze import phase_table, render_report  # noqa: E402


def test_phase_table_has_pct_of_total():
    p = load_profile(FIX / "sample_phases.json")
    md = phase_table(p)
    assert "| phase | seconds | % | max RSS (MB) | IO read (MB) | IO write (MB) |" in md
    assert "realize" in md
    # realize is 90 / 105 total = 85.7%
    assert "85.7%" in md


def test_render_report_names_dominant_and_has_sections():
    p = load_profile(FIX / "sample_phases.json")
    rep = render_report(p)
    assert "# Flox provisioning — root-cause report" in rep
    assert "Dominant phase: **realize**" in rep
    assert "## Resource attribution" in rep
    assert "## Ranked optimization candidates" in rep
    assert "realize.cpu.svg" in rep  # flamegraph referenced
```

- [ ] **Step 2: Run test to verify it fails**

Run: `flox activate -- uv run pytest tests/experiment/test_analyze_profile.py --override-ini="addopts=" -q`
Expected: FAIL — `ImportError: cannot import name 'phase_table'`

- [ ] **Step 3: Add the implementation (append to `analyze.py`)**

```python
def phase_table(p: Profile) -> str:
    total = total_seconds(p) or 1.0
    header = (
        "| phase | seconds | % | max RSS (MB) | IO read (MB) | IO write (MB) |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: |"
    )
    rows = [
        f"| {ph.name} | {ph.seconds:.1f} | {100 * ph.seconds / total:.1f}% "
        f"| {ph.max_rss_mb:.0f} | {ph.io_read_mb:.0f} | {ph.io_write_mb:.0f} |"
        for ph in p.phases
    ]
    return header + "\n" + "\n".join(rows) + "\n"


def render_report(p: Profile) -> str:
    dom = dominant_phase(p)
    fg_lines = "\n".join(f"- `{f}`" for f in p.flamegraphs) or "- (none captured yet)"
    return (
        "# Flox provisioning — root-cause report\n\n"
        f"- env: {p.os}/{p.arch} · cache: {p.cache} · flox {p.flox_version}\n"
        f"- total provisioning: {total_seconds(p):.1f}s · "
        f"Dominant phase: **{dom.name}** ({dom.seconds:.1f}s)\n\n"
        "## Phase breakdown\n\n" + phase_table(p) + "\n"
        "## Resource attribution\n\n"
        f"Dominant phase `{dom.name}` — classify via the flame graphs / IO below:\n"
        "- CPU-bound?  on-CPU flame graph hot stacks → (fill)\n"
        "- Off-CPU (blocked)?  off-CPU flame graph (Linux) → (fill: read/write/futex)\n"
        "- Disk?  IO write/read MB + biolatency → (fill)\n"
        "- Network?  bytes downloaded / time → (fill)\n\n"
        "## Flame graphs\n\n" + fg_lines + "\n\n"
        "## Ranked optimization candidates\n\n"
        "1. (fill: what · evidence · est. impact · where in flox/nix · upstream-fixable?)\n"
    )


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: analyze.py <phases.json> [out_report.md]", file=sys.stderr)
        return 2
    profile = load_profile(Path(argv[1]))
    report = render_report(profile)
    if len(argv) >= 3:
        Path(argv[2]).write_text(report)
        print(f"wrote {argv[2]}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `flox activate -- uv run pytest tests/experiment/test_analyze_profile.py --override-ini="addopts=" -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Verify the CLI renders from the fixture**

Run: `flox activate -- python3 -m experiment.profiling.analyze experiment/profiling/fixtures/sample_phases.json`
Expected: prints the report with the phase table and "Dominant phase: **realize**".

- [ ] **Step 6: Commit**

```bash
git add experiment/profiling/analyze.py tests/experiment/test_analyze_profile.py
git commit -m "feat(profiling): render phase table + root-cause report skeleton"
```

---

## Phase 2 — Shell helpers

### Task 3: `phases.sh` — per-phase wall-clock + resource capture

**Files:**
- Create: `experiment/profiling/lib/phases.sh`

- [ ] **Step 1: Write the helper**

Create `experiment/profiling/lib/phases.sh`:

```bash
# Sourced by profile-flox.sh. Provides run_phase: run a command as one named
# phase, capturing wall-clock + max RSS, appending one JSON object per phase to
# $PHASES_TMP (one JSON object per line; assembled into phases.json at the end).
# Portable across macOS (/usr/bin/time -l) and Linux (/usr/bin/time -v).

now() { python3 -c 'import time; print(time.time())'; }

# usage: run_phase NAME -- cmd args...
run_phase() {
  local name="$1"; shift
  [ "$1" = "--" ] && shift
  local timefile start end secs rss_mb
  timefile="$(mktemp)"
  start="$(now)"
  if [ "$(uname -s)" = "Darwin" ]; then
    /usr/bin/time -l "$@" 2>"$timefile" || true
    # macOS: "  <bytes>  maximum resident set size"
    rss_mb="$(awk '/maximum resident set size/ {print $1/1048576}' "$timefile")"
  else
    /usr/bin/time -v "$@" 2>"$timefile" || true
    # Linux: "Maximum resident set size (kbytes): <kb>"
    rss_mb="$(awk -F': ' '/Maximum resident set size/ {print $2/1024}' "$timefile")"
  fi
  end="$(now)"
  secs="$(python3 -c "print(round($end-$start,3))")"
  rss_mb="${rss_mb:-0}"
  python3 - "$name" "$secs" "$rss_mb" <<'PY' >>"$PHASES_TMP"
import json, sys
name, secs, rss = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
print(json.dumps({"name": name, "seconds": secs, "max_rss_mb": round(rss, 1),
                  "io_read_mb": 0.0, "io_write_mb": 0.0}))
PY
  rm -f "$timefile"
  echo "[phase] ${name}: ${secs}s (max RSS ${rss_mb} MB)" >&2
}

# Assemble $PHASES_TMP (json lines) + meta into a phases.json at $1.
assemble_phases_json() {
  local out="$1"
  python3 - "$out" "$PHASES_TMP" <<'PY'
import json, sys, os, platform, datetime
out, tmp = sys.argv[1], sys.argv[2]
phases = [json.loads(l) for l in open(tmp) if l.strip()]
osname = "macos" if platform.system() == "Darwin" else "linux"
meta = {"os": osname, "arch": platform.machine(),
        "cache": os.environ.get("PROFILE_CACHE", "cold"),
        "flox_version": os.environ.get("FLOX_VERSION", ""),
        "env": "profiling",
        "ts": datetime.datetime.now(datetime.UTC).isoformat()}
fgs = [f for f in os.environ.get("FLAMEGRAPHS", "").split() if f]
json.dump({"meta": meta, "phases": phases, "artifacts": {"flamegraphs": fgs}},
          open(out, "w"), indent=2)
print(f"wrote {out}")
PY
}
```

- [ ] **Step 2: Syntax-check + smoke the helper**

Run:
```bash
bash -n experiment/profiling/lib/phases.sh
PHASES_TMP="$(mktemp)"; bash -c 'source experiment/profiling/lib/phases.sh; run_phase demo -- sleep 1; FLAMEGRAPHS="" assemble_phases_json /tmp/p.json'; cat /tmp/p.json
```
Expected: `/tmp/p.json` has a `demo` phase with `seconds` ≈ 1.0 and valid meta.

- [ ] **Step 3: Commit**

```bash
git add experiment/profiling/lib/phases.sh
git commit -m "feat(profiling): add run_phase timing/resource capture helper"
```

---

### Task 4: `cold_reset.sh` — scoped, safe cold reproduction

**Files:**
- Create: `experiment/profiling/lib/cold_reset.sh`

- [ ] **Step 1: Write the helper**

Create `experiment/profiling/lib/cold_reset.sh`:

```bash
# Make the next `flox activate` of $ENV_DIR cold by deleting that env's nix
# store closure. SAFE BY DESIGN: `nix store delete` refuses paths still
# referenced by other gc-roots, so it only removes this env's unshared closure.
# On a disposable Lima VM / container this yields a fully cold store; on a shared
# host store it yields the coldest state possible without breaking other envs.

cold_reset_env() {
  local env_dir="$1"   # path containing .flox (the profiling env)
  local run_link store_path
  # flox materializes the active env under .flox/run/<system>.<name>(.dev)
  run_link="$(ls -d "${env_dir}/.flox/run/"* 2>/dev/null | head -1 || true)"
  if [ -z "$run_link" ]; then
    echo "[cold-reset] no realized env at ${env_dir}/.flox/run — already cold" >&2
    return 0
  fi
  store_path="$(readlink -f "$run_link" 2>/dev/null || true)"
  echo "[cold-reset] deleting closure of ${store_path}" >&2
  # delete the realized env + its closure; nix skips still-referenced paths.
  nix store delete --recursive "$store_path" 2>&1 | tail -3 >&2 || true
  rm -f "$run_link" 2>/dev/null || true
}
```

- [ ] **Step 2: Syntax-check**

Run: `bash -n experiment/profiling/lib/cold_reset.sh`
Expected: no output (valid).

- [ ] **Step 3: Commit**

```bash
git add experiment/profiling/lib/cold_reset.sh
git commit -m "feat(profiling): add safe scoped cold-reset of an env closure"
```

---

### Task 5: `sample.sh` (samply) + `io.sh` (fs_usage/strace)

**Files:**
- Create: `experiment/profiling/lib/sample.sh`
- Create: `experiment/profiling/lib/io.sh`

- [ ] **Step 1: Write `sample.sh`**

Create `experiment/profiling/lib/sample.sh`:

```bash
# CPU flame graphs via samply (cross-platform). Two modes:
#   sample_cmd OUT.json -- cmd args...   # profile a command + its children
#   sample_pid OUT.json PID DURATION     # profile an existing pid (e.g. nix-daemon)
# Produces a samply profile (Firefox Profiler json); convert/serve separately.

have_samply() { command -v samply >/dev/null 2>&1; }

sample_cmd() {
  local out="$1"; shift; [ "$1" = "--" ] && shift
  if have_samply; then
    samply record --save-only -o "$out" -- "$@" || "$@"
  else
    echo "[sample] samply not installed; running uninstrumented" >&2
    "$@"
  fi
}

sample_pid() {
  local out="$1" pid="$2" dur="${3:-30}"
  if have_samply && [ -n "$pid" ]; then
    samply record --save-only -o "$out" -p "$pid" --duration "$dur" || true
  else
    echo "[sample] skipping pid profile (no samply or pid)" >&2
  fi
}

# Best-effort: find the nix-daemon pid (empty string if none).
nix_daemon_pid() { pgrep -n nix-daemon 2>/dev/null | head -1 || true; }
```

- [ ] **Step 2: Write `io.sh`**

Create `experiment/profiling/lib/io.sh`:

```bash
# I/O attribution for one phase command.
#   io_trace OUT.txt -- cmd args...
# macOS: fs_usage (needs sudo; filesystem class). Linux: strace -f -c (syscall
# summary). Output is a human-readable summary file referenced from the report.

io_trace() {
  local out="$1"; shift; [ "$1" = "--" ] && shift
  if [ "$(uname -s)" = "Darwin" ]; then
    if sudo -n true 2>/dev/null; then
      sudo fs_usage -w -f filesys >"$out" 2>/dev/null &
      local fpid=$!
      "$@"; local rc=$?
      sudo kill "$fpid" 2>/dev/null || true
      return $rc
    fi
    echo "fs_usage needs sudo; skipped" >"$out"; "$@"
  else
    if command -v strace >/dev/null 2>&1; then
      strace -f -c -o "$out" "$@"
    else
      echo "strace not installed; skipped" >"$out"; "$@"
    fi
  fi
}
```

- [ ] **Step 3: Syntax-check both**

Run: `bash -n experiment/profiling/lib/sample.sh && bash -n experiment/profiling/lib/io.sh && echo ok`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add experiment/profiling/lib/sample.sh experiment/profiling/lib/io.sh
git commit -m "feat(profiling): add samply + io-trace helpers"
```

---

### Task 6: `deep_linux.sh` — eBPF off-CPU + perf (Lima only)

**Files:**
- Create: `experiment/profiling/lib/deep_linux.sh`

- [ ] **Step 1: Write the helper**

Create `experiment/profiling/lib/deep_linux.sh`:

```bash
# Linux-only deep tracing (run in the Lima Ubuntu VM as root). Captures an
# off-CPU flame graph (where threads BLOCK — the key for I/O/network-bound
# provisioning) and a system-wide on-CPU perf flame graph over a phase command.
# Requires: bpfcc-tools (offcputime) OR bpftrace, perf, and FlameGraph scripts.

# offcpu_flame OUT.svg DURATION -- cmd args...
offcpu_flame() {
  local out="$1" dur="$2"; shift 2; [ "$1" = "--" ] && shift
  if ! command -v offcputime-bpfcc >/dev/null 2>&1; then
    echo "[deep] offcputime-bpfcc missing (apt install bpfcc-tools)" >&2
    "$@"; return $?
  fi
  sudo offcputime-bpfcc -df "$dur" >/tmp/offcpu.folded 2>/dev/null &
  local bpid=$!
  "$@"; local rc=$?
  wait "$bpid" 2>/dev/null || true
  if command -v flamegraph.pl >/dev/null 2>&1; then
    flamegraph.pl --title "off-CPU" --countname us /tmp/offcpu.folded >"$out"
    echo "[deep] wrote $out" >&2
  else
    cp /tmp/offcpu.folded "${out%.svg}.folded"
    echo "[deep] FlameGraph not installed; saved folded stacks" >&2
  fi
  return $rc
}

# oncpu_flame OUT.svg -- cmd args...   (system-wide perf, incl nix-daemon)
oncpu_flame() {
  local out="$1"; shift; [ "$1" = "--" ] && shift
  if ! command -v perf >/dev/null 2>&1; then
    echo "[deep] perf missing (apt install linux-tools-\$(uname -r))" >&2
    "$@"; return $?
  fi
  sudo perf record -F 99 -a -g -o /tmp/perf.data -- "$@"; local rc=$?
  if command -v stackcollapse-perf.pl >/dev/null 2>&1; then
    sudo perf script -i /tmp/perf.data | stackcollapse-perf.pl | flamegraph.pl >"$out"
    echo "[deep] wrote $out" >&2
  fi
  return $rc
}
```

- [ ] **Step 2: Syntax-check**

Run: `bash -n experiment/profiling/lib/deep_linux.sh && echo ok`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add experiment/profiling/lib/deep_linux.sh
git commit -m "feat(profiling): add Linux eBPF off-CPU + perf flame-graph helpers"
```

---

## Phase 3 — Orchestrator + dedicated env

### Task 7: Dedicated profiling flox env

**Files:**
- Create: `experiment/profiling/flox-env/manifest.toml`

- [ ] **Step 1: Create the env manifest** (same toolchain as the experiment, isolated so cold-reset only affects this env)

Create `experiment/profiling/flox-env/manifest.toml`:

```toml
version = 1

[install]
python.pkg-path = "python312"
uv.pkg-path = "uv"
ruff.pkg-path = "ruff"
taplo.pkg-path = "taplo"
gitleaks.pkg-path = "gitleaks"
just.pkg-path = "just"
bun.pkg-path = "bun"
gh.pkg-path = "gh"
lefthook.pkg-path = "lefthook"
gnumake.pkg-path = "gnumake"

[options]
systems = ["aarch64-darwin", "x86_64-linux", "aarch64-linux", "x86_64-darwin"]
```

- [ ] **Step 2: Lock it** (creates `manifest.lock`; the profiling target)

Run: `flox edit -d experiment/profiling/flox-env -f experiment/profiling/flox-env/manifest.toml` (or `flox init -d experiment/profiling/flox-env` then reconcile to match Step 1). Confirm `experiment/profiling/flox-env/.flox/env/manifest.lock` exists and `flox activate -d experiment/profiling/flox-env -- ruff --version` works.

- [ ] **Step 3: Commit**

```bash
git add experiment/profiling/flox-env/.flox/env/manifest.toml experiment/profiling/flox-env/.flox/env/manifest.lock experiment/profiling/flox-env/.flox/env.json
git commit -m "feat(profiling): add dedicated profiling flox env"
```

---

### Task 8: `profile-flox.sh` orchestrator

**Files:**
- Create: `experiment/profiling/profile-flox.sh`

- [ ] **Step 1: Write the orchestrator**

Create `experiment/profiling/profile-flox.sh`:

```bash
#!/usr/bin/env bash
# Root-cause a flox cold provision: cold-reset -> timed phases -> phases.json +
# flame graphs. Cross-platform; Linux adds eBPF off-CPU + perf via deep_linux.sh.
#
# usage: profile-flox.sh [--cache cold|warm] [--deep] [--out DIR]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/lib/phases.sh"
source "$HERE/lib/cold_reset.sh"
source "$HERE/lib/sample.sh"
source "$HERE/lib/io.sh"
[ "$(uname -s)" = "Linux" ] && source "$HERE/lib/deep_linux.sh"

CACHE="cold"; DEEP=0; OUT="$HERE/results"; ENV_DIR="$HERE/flox-env"
while [ $# -gt 0 ]; do case "$1" in
  --cache) CACHE="$2"; shift 2;;
  --deep) DEEP=1; shift;;
  --out) OUT="$2"; shift 2;;
  *) echo "unknown arg: $1" >&2; exit 1;;
esac; done

mkdir -p "$OUT"
export PROFILE_CACHE="$CACHE"
export FLOX_VERSION="$(flox --version 2>/dev/null | head -1 || echo unknown)"
PHASES_TMP="$(mktemp)"; export PHASES_TMP
FLAMEGRAPHS=""

[ "$CACHE" = "cold" ] && cold_reset_env "$ENV_DIR"

# lock-eval: re-lock (cheap if unchanged) — exercises flox resolve + nix eval.
run_phase lock-eval -- flox activate -d "$ENV_DIR" --mode dev-only -- true 2>/dev/null || \
  run_phase lock-eval -- true

# realize + activate: the cold materialization is the big one. Profile the
# nix-daemon over this window (its work isn't a child of flox).
DAEMON_PID="$(nix_daemon_pid)"
if [ "$DEEP" = "1" ] && [ "$(uname -s)" = "Linux" ]; then
  offcpu_flame "$OUT/realize.offcpu.svg" 120 -- \
    flox activate -d "$ENV_DIR" -- true
  FLAMEGRAPHS="$FLAMEGRAPHS realize.offcpu.svg"
  run_phase realize-activate -- flox activate -d "$ENV_DIR" -- true
else
  sample_pid "$OUT/realize.daemon.json" "$DAEMON_PID" 120 &
  run_phase realize-activate -- \
    sample_cmd "$OUT/realize.flox.json" -- flox activate -d "$ENV_DIR" -- true
  wait 2>/dev/null || true
  [ -f "$OUT/realize.flox.json" ] && FLAMEGRAPHS="$FLAMEGRAPHS realize.flox.json"
fi

export FLAMEGRAPHS
assemble_phases_json "$OUT/phases.json"
python3 -m experiment.profiling.analyze "$OUT/phases.json" "$OUT/report.md"
echo "=== phase summary ==="; python3 -m experiment.profiling.analyze "$OUT/phases.json" | sed -n '/Phase breakdown/,/Resource/p'
```

- [ ] **Step 2: Make executable + syntax-check**

Run: `chmod +x experiment/profiling/profile-flox.sh && bash -n experiment/profiling/profile-flox.sh && echo ok`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add experiment/profiling/profile-flox.sh
git commit -m "feat(profiling): add profile-flox orchestrator"
```

---

## Phase 4 — Docs + validation gates

### Task 9: Playbook + report skeleton

**Files:**
- Create: `experiment/PROFILING.md`
- Create: `FINDINGS-perf.md`

- [ ] **Step 1: Write `experiment/PROFILING.md`**

Create `experiment/PROFILING.md`:

```markdown
# Flox deep-profiling playbook

Root-cause flox's CI provisioning cost (see ADR-12 / experiment/FINDINGS.md).
Methodology: top-down — phase breakdown -> resource attribution -> drill. Do NOT
assume CPU; provisioning is usually I/O/network-bound.

## Install tools
- samply (cross-platform CPU sampler): `mise use -g samply` or `cargo install samply`
- macOS: fs_usage (built-in, needs sudo)
- Linux (Lima Ubuntu 24.04 aarch64, vz): `sudo apt install -y bpfcc-tools bpftrace linux-tools-$(uname -r)` + FlameGraph (`git clone https://github.com/brendangregg/FlameGraph`)
  - Confirm eBPF: `ls /sys/kernel/btf/vmlinux`

## Run
- Mac, cold: `experiment/profiling/profile-flox.sh --cache cold`
- Mac, warm: `experiment/profiling/profile-flox.sh --cache warm`
- Lima (deep): `lima experiment/profiling/profile-flox.sh --cache cold --deep`
- Outputs: `experiment/profiling/results/phases.json`, `report.md`, `*.svg` flame graphs.

## Analyze
1. Read `report.md` — find the dominant phase.
2. Open the flame graph for that phase (samply: `samply load realize.flox.json`;
   Linux off-CPU: open `realize.offcpu.svg`).
3. Classify: CPU vs off-CPU (blocked) vs disk vs network.
4. Fill `FINDINGS-perf.md` candidates.

## macOS vs Linux comparison
Run on both; compare phase tables to explain the ~3x macOS penalty (realize/download
vs build vs disk).
```

- [ ] **Step 2: Write `FINDINGS-perf.md` skeleton**

Create `FINDINGS-perf.md`:

```markdown
# Flox provisioning — root-cause findings

Status: in progress. Generated phase tables live in
`experiment/profiling/results/`; this file holds the synthesized root cause.

## Phase breakdown (fill from results/report.md)
- macOS cold: (paste table)
- Linux cold (Lima): (paste table)

## Dominant phase + resource attribution
(fill: which phase, CPU vs off-CPU vs disk vs network, evidence from flame graphs)

## Ranked optimization candidates
1. (what · evidence · est. impact · where in flox/nix · upstream-fixable?)

## macOS vs Linux 3x penalty
(fill: realize/download vs build vs disk differences)
```

- [ ] **Step 3: Commit**

```bash
git add experiment/PROFILING.md FINDINGS-perf.md
git commit -m "docs(profiling): add playbook + findings skeleton"
```

---

### Task 10: Validation gates (runbook)

**Files:** none (validation/runbook).

- [ ] **Step 1: Harness-unit gate (zero profiling)**

Run: `flox activate -- uv run pytest tests/experiment/test_analyze_profile.py --override-ini="addopts=" -q`
Expected: all pass (5). And `flox activate -- python3 -m experiment.profiling.analyze experiment/profiling/fixtures/sample_phases.json` prints a populated report.

- [ ] **Step 2: macOS smoke gate**

Run: `experiment/profiling/profile-flox.sh --cache cold`
Expected: produces `experiment/profiling/results/phases.json` + `report.md`; the `realize-activate` phase dominates; total ≈ the experiment's macOS cold flox provision (~tens of seconds). If `samply` is installed, `results/realize.flox.json` exists.

- [ ] **Step 3: Lima deep gate**

Run (in Lima per PROFILING.md): `experiment/profiling/profile-flox.sh --cache cold --deep`
Expected: `results/realize.offcpu.svg` (off-CPU flame graph) is produced; open it to see where the realize phase BLOCKS (read from substituter vs write/fsync to /nix store).

- [ ] **Step 4: Commit any sample artifacts**

```bash
git add -f experiment/profiling/results/phases.json experiment/profiling/results/report.md
git commit -m "chore(profiling): add sample profile results"
```

- [ ] **Step 5: Root-cause pass** — fill `FINDINGS-perf.md` from the dominant-phase flame graphs (macOS + Lima), with ranked flox optimization candidates. Commit.

---

## Self-Review

**Spec coverage:**
- Methodology (top-down) → PROFILING.md + analyze report sections ✓
- Phases (flox-install/lock-eval/realize/build/activate/cache-save) → phases.json vocabulary + orchestrator (realize-activate combined; build folds into realize on substituted closures — noted) ✓
- macOS tools (samply/fs_usage/time -l) → sample.sh/io.sh/phases.sh ✓
- Linux deep (Lima eBPF off-CPU + perf) → deep_linux.sh + orchestrator `--deep` ✓
- nix-daemon catch → `sample_pid` over daemon pid / system-wide perf ✓
- scoped cold-reset → cold_reset.sh (nix store delete, safe) ✓
- outputs (phases.json + flame graphs + FINDINGS-perf.md) → assemble_phases_json + analyze + skeleton ✓
- validation gates → Task 10 ✓
- file structure → matches spec ✓

**Placeholder scan:** The `(fill: …)` markers in `render_report`/`FINDINGS-perf.md` are intentional *report* placeholders for the human root-cause pass (data the experiment must produce), not plan gaps. No TBD/TODO in code/steps.

**Type/name consistency:** `Phase(name, seconds, max_rss_mb, io_read_mb, io_write_mb)`, `Profile`, `load_profile`, `total_seconds`, `dominant_phase`, `phase_table`, `render_report`, `main` — used identically across Tasks 1–2 and the orchestrator. phases.json keys match between `phases.sh` (writer), `assemble_phases_json`, and `analyze.load_profile` (reader). The orchestrator emits a `realize-activate` phase (not separate `realize`/`activate`) — analyze treats phase names generically, so this is consistent; the dominant phase is found by max seconds regardless of name.

## Known follow-ups (out of scope)
- GitHub Actions profiling workflow (true-cold CI ground truth) — documented, not built here.
- `build` vs `realize` split (orchestrator currently combines realize-activate) — refine once the dominant phase is confirmed.
- io_read_mb/io_write_mb are 0.0 from `run_phase` (populated qualitatively via io.sh summaries); wire numeric IO later if needed.
