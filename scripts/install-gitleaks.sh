#!/usr/bin/env bash
set -euo pipefail

# Install helper called by `just install-gitleaks`.

GITLEAKS_VERSION="${GITLEAKS_VERSION:-8.21.2}"

if command -v gitleaks >/dev/null 2>&1; then
    echo "gitleaks is already installed ($(gitleaks version 2>/dev/null || echo unknown))"
    exit 0
fi

os="$(uname -s | tr '[:upper:]' '[:lower:]')"
case "$os" in
    darwin | linux) ;;
    *)
        echo "Unsupported OS: $os" >&2
        echo "Install gitleaks manually: https://github.com/gitleaks/gitleaks/releases" >&2
        exit 1
        ;;
esac

if command -v brew >/dev/null 2>&1; then
    brew install gitleaks
    exit 0
fi

arch="$(uname -m)"
case "$arch" in
    x86_64 | amd64) arch=x64 ;;
    arm64 | aarch64) arch=arm64 ;;
    *)
        echo "Unsupported arch: $arch" >&2
        echo "Install gitleaks manually: https://github.com/gitleaks/gitleaks/releases" >&2
        exit 1
        ;;
esac

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
url="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_${os}_${arch}.tar.gz"
echo "Downloading gitleaks ${GITLEAKS_VERSION} (${os}/${arch})..."
curl -fsSL "$url" -o "$tmp/gitleaks.tar.gz"
tar -xzf "$tmp/gitleaks.tar.gz" -C "$tmp"

dest="${HOME}/.local/bin"
mkdir -p "$dest"
install -m 0755 "$tmp/gitleaks" "$dest/gitleaks"
echo "Installed gitleaks to $dest/gitleaks"

case ":$PATH:" in
    *":$dest:"*) ;;
    *) echo "NOTE: add $dest to your PATH" ;;
esac
