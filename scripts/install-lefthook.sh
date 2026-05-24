#!/usr/bin/env bash
# ITM-021 — lefthook installer.
# Pins a lefthook release; verifies SHA256 against upstream checksums.txt;
# installs to ~/.local/bin; runs `lefthook install` to wire .git/hooks/.
# Idempotent. Decided round 2.
#
# Review pin every 6 months (round-7 cadence).

set -euo pipefail

LEFTHOOK_VERSION="${LEFTHOOK_VERSION:-1.13.6}"
INSTALL_DIR="${HOME}/.local/bin"
BIN="${INSTALL_DIR}/lefthook"

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

    local platform tar checksums url tmpdir
    platform=$(detect_platform)
    tar="lefthook_${LEFTHOOK_VERSION}_${platform/_/_}.tar.gz"
    # lefthook release filenames use Darwin/Linux capitalised + arch suffix
    # e.g. lefthook_1.13.6_Darwin_arm64.tar.gz
    local cap_os cap_arch
    cap_os=$(uname -s)
    cap_arch=$(uname -m)
    case "${cap_arch}" in x86_64|amd64) cap_arch="x86_64" ;; aarch64) cap_arch="arm64" ;; esac
    tar="lefthook_${LEFTHOOK_VERSION}_${cap_os}_${cap_arch}.tar.gz"
    checksums="lefthook_${LEFTHOOK_VERSION}_checksums.txt"
    url="https://github.com/evilmartians/lefthook/releases/download/v${LEFTHOOK_VERSION}"

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
    mv "${tmpdir}/lefthook" "${BIN}"
    chmod +x "${BIN}"

    if ! echo "${PATH}" | tr ':' '\n' | grep -qx "${INSTALL_DIR}"; then
        echo "WARN: ${INSTALL_DIR} is not on PATH; add to your shell rc:"
        echo "      export PATH=\"\${HOME}/.local/bin:\${PATH}\""
    fi

    echo "PASS: lefthook ${LEFTHOOK_VERSION} installed at ${BIN}"
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
