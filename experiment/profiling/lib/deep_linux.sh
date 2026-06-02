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
