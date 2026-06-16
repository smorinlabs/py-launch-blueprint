#!/usr/bin/env bash
# ADR 0018 — actionlint installer (11th toolchain tool; amends ADR 0005).
# Pins an actionlint release; verifies SHA256 against upstream checksums.txt;
# installs to ~/.local/bin. Idempotent. Mirrors scripts/install-gitleaks.sh.
#
# Review pin every 6 months (round-7 cadence for tool installers).
# Keep the version in sync with the CI actionlint job (.github/workflows/lint.yml).

set -euo pipefail

ACTIONLINT_VERSION="${ACTIONLINT_VERSION:-1.7.12}"
INSTALL_DIR="${HOME}/.local/bin"
BIN="${INSTALL_DIR}/actionlint"

detect_platform() {
    local os arch
    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    arch=$(uname -m)
    case "${arch}" in
        x86_64|amd64) arch="amd64" ;;
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
    if command -v actionlint >/dev/null 2>&1; then
        local existing
        existing=$(actionlint --version 2>/dev/null | head -1 || true)
        if [[ "${existing}" == *"${ACTIONLINT_VERSION}"* ]]; then
            echo "PASS: actionlint ${ACTIONLINT_VERSION} already on PATH (${existing})"
            return 0
        fi
        echo "INFO: existing actionlint at ${existing}; reinstalling pinned ${ACTIONLINT_VERSION}"
    fi

    local platform tar checksums url
    platform=$(detect_platform)
    tar="actionlint_${ACTIONLINT_VERSION}_${platform}.tar.gz"
    checksums="actionlint_${ACTIONLINT_VERSION}_checksums.txt"
    url="https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}"

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
    mv "${tmpdir}/actionlint" "${BIN}"
    chmod +x "${BIN}"

    if ! echo "${PATH}" | tr ':' '\n' | grep -qx "${INSTALL_DIR}"; then
        echo "WARN: ${INSTALL_DIR} is not on PATH; add to your shell rc:"
        echo "      export PATH=\"\${HOME}/.local/bin:\${PATH}\""
    fi

    echo "PASS: actionlint ${ACTIONLINT_VERSION} installed at ${BIN}"
}

main "$@"
