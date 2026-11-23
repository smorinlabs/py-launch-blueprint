#!/usr/bin/env bash
# Run each release test file in its own bun process, in parallel.
# The release scripts call git synchronously, so `bun test --concurrent`
# cannot overlap them; separate processes can. Each file's output is
# buffered and printed in file order. Exits non-zero if any file fails
# or if the directory has no test files.
set -euo pipefail
dir="${1:-tests/release}"
files=("$dir"/*.test.js)
if [ ! -e "${files[0]}" ]; then
    echo "FAIL: no *.test.js files in $dir" >&2
    exit 1
fi
logs="$(mktemp -d)"
trap 'rm -rf "$logs"' EXIT
pids=()
for i in "${!files[@]}"; do
    bun test "${files[$i]}" >"$logs/$i.log" 2>&1 &
    pids+=("$!")
done
status=0
for i in "${!files[@]}"; do
    if ! wait "${pids[$i]}"; then
        status=1
    fi
    cat "$logs/$i.log"
done
exit "$status"
