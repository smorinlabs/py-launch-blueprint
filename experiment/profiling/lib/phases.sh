# Sourced by profile-flox.sh. Provides run_phase: run a command as one named
# phase, capturing wall-clock + max RSS, appending one JSON object per phase to
# $PHASES_TMP (one JSON object per line; assembled into phases.json at the end).
# Portable across macOS (/usr/bin/time -l) and Linux (/usr/bin/time -v).

now() { python3 -c 'import time; print(time.time())'; }

# usage: run_phase NAME -- cmd args...
run_phase() {
  local name="$1"; shift
  [ "$1" = "--" ] && shift
  local timefile start end secs rss_mb rc=0
  timefile="$(mktemp)"
  start="$(now)"
  if [ "$(uname -s)" = "Darwin" ]; then
    /usr/bin/time -l "$@" 2>"$timefile" || rc=$?
    rss_mb="$(awk '/maximum resident set size/ {print $1/1048576}' "$timefile")"
  else
    /usr/bin/time -v "$@" 2>"$timefile" || rc=$?
    rss_mb="$(awk -F': ' '/Maximum resident set size/ {print $2/1024}' "$timefile")"
  fi
  end="$(now)"
  secs="$(python3 -c "print(round($end-$start,3))")"
  rss_mb="${rss_mb:-0}"
  # A non-zero exit means the wrapped command failed; without this warning a
  # failed phase is silently recorded as a fast (~0s) success. Return 0 so the
  # harness keeps going (the caller decides whether a phase is fatal).
  [ "$rc" -ne 0 ] && echo "[phase] WARNING: ${name} exited ${rc}; timing is invalid" >&2
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
