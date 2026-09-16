#!/usr/bin/env bash
# Install ShellCheck 0.11.0 from upstream, verified against release SHA256 digests.
# Update the version and all four hashes together when upgrading.
set -euo pipefail
version=0.11.0
install_dir="${SHELLCHECK_INSTALL_DIR:-${HOME}/.local/bin}"
os=$(uname -s | tr '[:upper:]' '[:lower:]')
arch=$(uname -m)
case "$arch" in arm64) arch=aarch64 ;; amd64) arch=x86_64 ;; esac
case "$os.$arch" in
    darwin.aarch64) sha=339b930feb1ea764467013cc1f72d09cd6b869ebf1013296ba9055ab2ffbd26f ;;
    darwin.x86_64) sha=c2c15e08df0e8fbc374c335b230a7ee958c313fa5714817a59aa59f1aa594f51 ;;
    linux.aarch64) sha=68a8133197a50beb8803f8d42f9908d1af1c5540d4bb05fdfca8c1fa47decefc ;;
    linux.x86_64) sha=b7af85e41cc99489dcc21d66c6d5f3685138f06d34651e6d34b42ec6d54fe6f6 ;;
    *) echo "Unsupported platform: $os.$arch" >&2; exit 1 ;;
esac
if [ -x "$install_dir/shellcheck" ] &&
    "$install_dir/shellcheck" --version | grep -qx "version: $version"; then
    echo "ShellCheck $version already installed at $install_dir/shellcheck"
    exit 0
fi
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
archive="shellcheck-v$version.$os.$arch.tar.gz"
curl -fsSL "https://github.com/koalaman/shellcheck/releases/download/v$version/$archive" -o "$tmpdir/$archive"
if command -v sha256sum >/dev/null 2>&1; then
    (cd "$tmpdir" && printf '%s  %s\n' "$sha" "$archive" | sha256sum -c -)
else
    (cd "$tmpdir" && printf '%s  %s\n' "$sha" "$archive" | shasum -a 256 -c -)
fi
tar -xzf "$tmpdir/$archive" -C "$tmpdir"
mkdir -p "$install_dir"
install -m 755 "$tmpdir/shellcheck-v$version/shellcheck" "$install_dir/shellcheck"
echo "Installed ShellCheck $version to $install_dir; ensure it is on PATH."
