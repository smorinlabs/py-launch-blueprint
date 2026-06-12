#!/usr/bin/env bash
# ITM-007 — gitleaks installer.
# Pins a gitleaks release; verifies SHA256 against upstream checksums.txt;
# installs to ~/.local/bin. Idempotent. Decided round 2.
#
# Review pin every 6 months (round-7 cadence for tool installers).

set -euo pipefail

GITLEAKS_VERSION="${GITLEAKS_VERSION:-8.27.2}"
INSTALL_DIR="${HOME}/.local/bin"
BIN="${INSTALL_DIR}/gitleaks"

detect_platform() {
    local os arch
    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    arch=$(uname -m)
    case "${arch}" in
        x86_64|amd64) arch="x64" ;;
        aarch64|arm64) arch="arm64" ;;
        *) echo "FAIL: unsupported arch ${arch}" >&2; exit 1 ;;
    esac
    case "${os}" in
        darwin|linux) ;;
        *) echo "FAIL: unsupported OS ${os}" >&2; exit 1 ;;
    esac
    echo "${os}_${arch}"
}

main() {
    if command -v gitleaks >/dev/null 2>&1; then
        local existing
        existing=$(gitleaks version 2>/dev/null | head -1 || true)
        if [[ "${existing}" == *"${GITLEAKS_VERSION}"* ]]; then
            echo "PASS: gitleaks ${GITLEAKS_VERSION} already on PATH (${existing})"
            return 0
        fi
        echo "INFO: existing gitleaks at ${existing}; reinstalling pinned ${GITLEAKS_VERSION}"
    fi

    local platform tar checksums url
    platform=$(detect_platform)
    tar="gitleaks_${GITLEAKS_VERSION}_${platform}.tar.gz"
    checksums="gitleaks_${GITLEAKS_VERSION}_checksums.txt"
    url="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}"

    # tmpdir must NOT be `local`: the EXIT trap runs after main() returns,
    # where a local would be out of scope and `set -u` would abort the script.
    tmpdir=$(mktemp -d)
    trap 'rm -rf "${tmpdir}"' EXIT

    echo "INFO: downloading ${tar}"
    curl -sSfL "${url}/${tar}" -o "${tmpdir}/${tar}"
    curl -sSfL "${url}/${checksums}" -o "${tmpdir}/${checksums}"

    echo "INFO: verifying SHA256"
    (cd "${tmpdir}" && grep " ${tar}\$" "${checksums}" | shasum -a 256 -c -)

    echo "INFO: installing to ${INSTALL_DIR}"
    mkdir -p "${INSTALL_DIR}"
    tar -xzf "${tmpdir}/${tar}" -C "${tmpdir}"
    mv "${tmpdir}/gitleaks" "${BIN}"
    chmod +x "${BIN}"

    if ! echo "${PATH}" | tr ':' '\n' | grep -qx "${INSTALL_DIR}"; then
        echo "WARN: ${INSTALL_DIR} is not on PATH; add to your shell rc:"
        echo "      export PATH=\"\${HOME}/.local/bin:\${PATH}\""
    fi

    echo "PASS: gitleaks ${GITLEAKS_VERSION} installed at ${BIN}"
}

main "$@"
