#!/usr/bin/env bash
# ITM-006 — gitleaks wrapper. Single entry-point for hooks, CI, manual scans.
# Modes: --staged (commit-time, staged diff) | --range (pre-push, upstream range).
# Decided round 2.

set -euo pipefail

MODE="${1:-}"
CONFIG=".gitleaks.toml"

usage() {
    cat >&2 <<'EOF'
Usage: scripts/check-gitleaks.sh [--staged|--range]
  --staged   Scan staged changes only (pre-commit hook mode).
  --range    Scan range upstream..HEAD (pre-push hook mode).
EOF
    exit 2
}

require_gitleaks() {
    if ! command -v gitleaks >/dev/null 2>&1; then
        echo "FAIL: gitleaks not on PATH — install via scripts/install-gitleaks.sh" >&2
        exit 127
    fi
}

scan_staged() {
    require_gitleaks
    if gitleaks protect --staged --config "${CONFIG}" --no-banner --redact; then
        echo "PASS: no secrets in staged diff"
    else
        echo "FAIL: gitleaks found secret(s) in staged diff" >&2
        exit 1
    fi
}

scan_range() {
    require_gitleaks
    local upstream
    if ! upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null); then
        echo "WARN: no upstream tracking branch; skipping range scan" >&2
        exit 0
    fi
    if gitleaks detect --config "${CONFIG}" --no-banner --redact \
            --log-opts="${upstream}..HEAD"; then
        echo "PASS: no secrets in ${upstream}..HEAD"
    else
        echo "FAIL: gitleaks found secret(s) in ${upstream}..HEAD" >&2
        exit 1
    fi
}

case "${MODE}" in
    --staged) scan_staged ;;
    --range)  scan_range ;;
    *) usage ;;
esac
