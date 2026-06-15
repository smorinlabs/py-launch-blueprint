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
  --range    Scan range <base>..HEAD (pre-push hook mode; base is the
             upstream, falling back to origin's default branch).
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
    local base
    if base=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null); then
        : # Prefer the configured upstream tracking branch.
    else
        # ADR 0018: no upstream (e.g. the first push of a new branch) used to
        # skip silently — the staged scans were the only cover for that window.
        # Fall back to the remote default branch so new commits still get a
        # range scan. origin/HEAD resolves to it; fall back to origin/main.
        base=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null) || base="origin/main"
        if ! git rev-parse --verify --quiet "${base}" >/dev/null 2>&1; then
            echo "WARN: no upstream and no '${base}' ref to diff against; skipping range scan" >&2
            exit 0
        fi
        echo "INFO: no upstream tracking branch; scanning ${base}..HEAD instead" >&2
    fi
    if gitleaks detect --config "${CONFIG}" --no-banner --redact \
            --log-opts="${base}..HEAD"; then
        echo "PASS: no secrets in ${base}..HEAD"
    else
        echo "FAIL: gitleaks found secret(s) in ${base}..HEAD" >&2
        exit 1
    fi
}

case "${MODE}" in
    --staged) scan_staged ;;
    --range)  scan_range ;;
    *) usage ;;
esac
