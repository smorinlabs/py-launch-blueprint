#!/usr/bin/env bash
# ITM-042 — Bun installer.
# Uses Bun's official installer (https://bun.sh/install) with a pinned
# version. Bun installs to ~/.bun/bin by default. Idempotent.
# Decided round 19. Review pin every 6 months (round-7 cadence).
#
# Why the official installer (not GitHub-release tarball): bun.sh/install
# handles platform detection, decompression, PATH hints, and shell-rc
# updates in one well-tested script. The trade-off is curl-pipe-bash;
# we pin the version so the install is reproducible.

set -euo pipefail

BUN_VERSION="${BUN_VERSION:-1.3.5}"
INSTALL_HOME="${HOME}/.bun"
BIN="${INSTALL_HOME}/bin/bun"

main() {
    if command -v bun >/dev/null 2>&1; then
        local existing
        existing=$(bun --version 2>/dev/null || true)
        if [[ "${existing}" == "${BUN_VERSION}" ]]; then
            echo "PASS: bun ${BUN_VERSION} already on PATH (${existing})"
            return 0
        fi
        echo "INFO: existing bun ${existing}; installing pinned ${BUN_VERSION}"
    fi

    echo "INFO: installing bun ${BUN_VERSION} via official installer"
    curl -fsSL https://bun.sh/install | bash -s "bun-v${BUN_VERSION}"

    if [[ ! -x "${BIN}" ]]; then
        echo "FAIL: bun installer did not produce ${BIN}" >&2
        exit 1
    fi

    if ! echo "${PATH}" | tr ':' '\n' | grep -qx "${INSTALL_HOME}/bin"; then
        echo "WARN: ${INSTALL_HOME}/bin not on PATH; add to shell rc:"
        echo "      export BUN_INSTALL=\"\${HOME}/.bun\""
        echo "      export PATH=\"\${BUN_INSTALL}/bin:\${PATH}\""
    fi

    echo "PASS: bun ${BUN_VERSION} installed at ${BIN}"
}

main "$@"
