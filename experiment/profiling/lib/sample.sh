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
