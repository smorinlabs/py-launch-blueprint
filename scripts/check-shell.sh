#!/usr/bin/env bash
# Check tracked shell scripts, including hidden directories and paths with spaces.
# Explicit arguments let git hooks check only staged paths.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
command -v shellcheck >/dev/null 2>&1 || {
    echo "ShellCheck missing: run bash scripts/install-shellcheck.sh and add ~/.local/bin to PATH" >&2
    exit 1
}
if [ "$#" -gt 0 ]; then
    exec shellcheck -- "$@"
fi
files=()
while IFS= read -r -d '' file; do
    [ ! -f "$file" ] || files+=("$file")
done < <(git ls-files -z -- '*.sh' '*.bash')
if [ "${#files[@]}" -gt 0 ]; then
    shellcheck -- "${files[@]}"
fi
