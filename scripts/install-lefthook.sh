#!/usr/bin/env bash
# ITM-021 — lefthook installer.
# Installs via Bun (cross-platform; works on macOS where lefthook v2.x
# doesn't ship a GitHub-release Darwin tarball). Requires Bun on PATH
# first — install via scripts/install-bun.sh (ITM-042).
# Idempotent. Wires git hooks if lefthook.yml is present.
# Decided round 2; bun-install path resolved during ITM-021 install (lefthook
# 2.x deprecated GitHub-release Darwin binaries in favor of brew + npm).
# Review pin every 6 months (round-7 cadence).

set -euo pipefail

LEFTHOOK_VERSION="${LEFTHOOK_VERSION:-2.1.8}"

ensure_bun() {
    if ! command -v bun >/dev/null 2>&1; then
        echo "FAIL: bun not on PATH. Install via scripts/install-bun.sh first (ITM-042)." >&2
        echo "      (lefthook 2.x is distributed via npm/brew; this template installs via bun.)" >&2
        exit 127
    fi
}

install_lefthook() {
    if command -v lefthook >/dev/null 2>&1; then
        local existing
        existing=$(lefthook version 2>/dev/null | head -1 || true)
        if [[ "${existing}" == *"${LEFTHOOK_VERSION}"* ]]; then
            echo "PASS: lefthook ${LEFTHOOK_VERSION} already on PATH (${existing})"
            return 0
        fi
        echo "INFO: existing lefthook ${existing}; reinstalling pinned ${LEFTHOOK_VERSION}"
    fi
    ensure_bun
    echo "INFO: installing lefthook@${LEFTHOOK_VERSION} via bun"
    bun install -g "lefthook@${LEFTHOOK_VERSION}"
    echo "PASS: lefthook installed (verify: lefthook version)"
}

wire_hooks() {
    if [[ ! -f lefthook.yml ]]; then
        echo "WARN: lefthook.yml not found; skipping 'lefthook install' (ITM-003 lands the config)"
        return 0
    fi
    if command -v lefthook >/dev/null 2>&1; then
        echo "INFO: wiring git hooks via 'lefthook install'"
        lefthook install
        echo "PASS: hooks wired"
    fi
}

install_lefthook
wire_hooks
