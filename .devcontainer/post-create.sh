#!/bin/sh
# Devcontainer setup — the two-level flow (see CLAUDE.md / AGENTS.md):
#   Level 1: make bootstrap  (base toolchain: just + uv)
#   Level 2: just setup      (dev env sync, git hooks, hook toolchain)
# The uv base image is slim — install make/curl first if absent so Level 1
# can run at all.
set -eu

if ! command -v make >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends make curl ca-certificates
fi

export PATH="$HOME/.local/bin:$PATH"
make bootstrap
just setup
