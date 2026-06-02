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
