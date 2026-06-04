# syntax=docker/dockerfile:1
#
# flox-ci-base P0 — a Flox-preloaded GitHub Actions container image that bakes
# the `test` job's setup (python + uv + warm dependency cache) into the image.
# Mirrors py-launch-blueprint's REAL `test` job: python 3.12, `uv sync --group
# dev`, `uv run pytest`. See docs/superpowers/specs/2026-06-03-flox-ci-base-prd.md.
#
# Build context = repo root (needs pyproject.toml + uv.lock for cache warming):
#   docker build -f experiment/flox-ci-base/Dockerfile -t flox-ci-base:py312 .
#
# Two base arms (PRD §5.1): minimal (default) isolates best-case pre-bake value;
# faithful uses the runner-equivalent image. Select via --build-arg BASE=...
ARG BASE=ubuntu:24.04
# faithful arm: --build-arg BASE=ghcr.io/catthehacker/ubuntu:act-24.04
FROM ${BASE}

# Minimal arm needs git + tooling; faithful arm already ships git (idempotent).
# `uses:` steps (checkout) bypass the flox shell and need the base's system git.
RUN command -v git >/dev/null 2>&1 || ( apt-get update && apt-get install -y --no-install-recommends \
      git ca-certificates curl xz-utils && rm -rf /var/lib/apt/lists/* )
# NO `USER` instruction — GHA container jobs run as root for GITHUB_WORKSPACE.

# Install Flox (pinned, arch-detected) from the stable channel.
ARG TARGETARCH
ARG FLOX_VER=1.12.2
RUN set -eux; \
    arch="${TARGETARCH:-$(dpkg --print-architecture)}"; \
    case "$arch" in \
      amd64) a=x86_64-linux ;; \
      arm64) a=aarch64-linux ;; \
      *) echo "unsupported arch: $arch" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "https://downloads.flox.dev/by-env/stable/deb/flox-${FLOX_VER}.${a}.deb" -o /tmp/flox.deb; \
    apt-get update; apt-get install -y /tmp/flox.deb; \
    rm /tmp/flox.deb; rm -rf /var/lib/apt/lists/*; \
    flox config --set disable_metrics true; \
    flox --version

# Build the flox env from the committed manifest: `flox init` generates env.json +
# the default scaffold, `flox edit -f` applies our manifest (python312 + uv + vars)
# and locks it, and `flox activate` realizes the closure at build time — the
# setup-python + setup-uv replacement.
COPY experiment/flox-ci-base/.flox/env/manifest.toml /tmp/ci-env-manifest.toml
RUN flox init -d /opt/ci-env \
 && flox edit -d /opt/ci-env -f /tmp/ci-env-manifest.toml \
 && flox activate -d /opt/ci-env -- true \
 && rm /tmp/ci-env-manifest.toml
WORKDIR /opt/ci-env

# Warm the uv cache exactly as the real `test` job does (`uv sync --group dev`).
# --no-install-project: the project source isn't in the image, only its lock; the
# consumer re-runs `uv sync --group dev` against the checked-out source (warm cache
# -> near-instant). Drop the throwaway venv so only the populated cache persists.
ENV UV_CACHE_DIR=/opt/uv-cache UV_TOOL_DIR=/opt/uv-tools UV_LINK_MODE=copy UV_PYTHON_PREFERENCE=only-system
COPY pyproject.toml uv.lock /tmp/warm/
RUN cd /tmp/warm && flox activate -d /opt/ci-env -- sh -eux -c '\
      uv sync --group dev --no-install-project; \
      uv run --no-sync python -c "import pytest; print(\"pytest\", pytest.__version__)"; \
    ' && rm -rf /tmp/warm

WORKDIR /work
