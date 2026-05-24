#!/usr/bin/env bash
set -euo pipefail

# Git-hook wrapper: fails with an actionable install hint when gitleaks is
# missing, otherwise scans for secrets against .gitleaks.toml.
#
# Usage: check-gitleaks.sh [staged|full]
#   staged (default) scans the staged diff only.
#   full scans commits ahead of upstream, falling back to full history.

if ! command -v gitleaks >/dev/null 2>&1; then
    cat >&2 <<'EOF'
gitleaks is not installed and is required for the secret scan.
Install it with one of:
  just install-gitleaks
  brew install gitleaks
  https://github.com/gitleaks/gitleaks/releases
EOF
    exit 1
fi

mode="${1:-staged}"
case "$mode" in
    staged)
        exec gitleaks git --staged --redact --verbose --config .gitleaks.toml
        ;;
    full)
        if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
            exec gitleaks git --log-opts='@{u}..HEAD' --redact --verbose --config .gitleaks.toml
        fi
        echo "gitleaks: no upstream configured; scanning full history" >&2
        exec gitleaks git --redact --verbose --config .gitleaks.toml
        ;;
    *)
        echo "gitleaks: unknown mode '$mode' (expected 'staged' or 'full')" >&2
        exit 1
        ;;
esac
