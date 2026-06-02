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

# lock-eval: a dev-mode activate exercising flox resolve + nix eval. On a warm
# store this overlaps realize (the first activate also realizes); the lock-eval
# vs realize split is meaningful on a cold store (Lima/CI), not a warm host.
run_phase lock-eval -- flox activate -d "$ENV_DIR" --mode dev -- true

# realize + activate: the cold materialization is the big one. The heavy lifting
# runs in the nix-daemon (NOT a child of flox), so time the flox binary directly
# and sample the daemon by pid over the same window.
DAEMON_PID="$(nix_daemon_pid)"
if [ "$DEEP" = "1" ] && [ "$(uname -s)" = "Linux" ]; then
  offcpu_flame "$OUT/realize.offcpu.svg" 120 -- \
    flox activate -d "$ENV_DIR" -- true
  FLAMEGRAPHS="$FLAMEGRAPHS realize.offcpu.svg"
  # The offcpu run above already materialized the env, so a second activate would
  # be a warm cache hit. Re-cold the closure so realize-activate times cold too
  # (a separate but equivalent cold provision to the flame graph above).
  [ "$CACHE" = "cold" ] && cold_reset_env "$ENV_DIR"
  run_phase realize-activate -- flox activate -d "$ENV_DIR" -- true
else
  sample_pid "$OUT/realize.daemon.json" "$DAEMON_PID" 120 &
  SAMPLE_BG=$!
  run_phase realize-activate -- flox activate -d "$ENV_DIR" -- true
  wait "$SAMPLE_BG" 2>/dev/null || true
  [ -f "$OUT/realize.daemon.json" ] && FLAMEGRAPHS="$FLAMEGRAPHS realize.daemon.json"
fi

export FLAMEGRAPHS
assemble_phases_json "$OUT/phases.json"
python3 -m experiment.profiling.analyze "$OUT/phases.json" "$OUT/report.md"
echo "=== phase summary ==="; python3 -m experiment.profiling.analyze "$OUT/phases.json" | sed -n '/Phase breakdown/,/Resource/p'
