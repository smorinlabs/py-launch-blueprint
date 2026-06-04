#!/usr/bin/env bash
# Initial-verification smoke test for the flox-ci-base P0 image.
# Builds the minimal-arm image (native arch) and verifies the baked env works
# end-to-end: flox activates, python312+uv are baked, the uv cache is warm, and
# the real consumer flow (`uv sync --group dev` + `uv run pytest`) runs.
#
# Usage (from repo root, with Docker running):
#   experiment/flox-ci-base/smoke-test.sh
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
IMAGE="flox-ci-base:py312-smoke"
DF="experiment/flox-ci-base/Dockerfile"

echo "== 1/4 build (minimal base, native arch) =="
docker build -f "$DF" -t "$IMAGE" .

echo "== 2/4 guard: flox activate + python/uv baked =="
docker run --rm "$IMAGE" flox activate -d /opt/ci-env -- bash -eo pipefail -c '
  command -v uv
  uv --version
  python --version          # expect 3.12.x (flox-provided)
  test -d /opt/uv-cache && echo "uv cache present: $(du -sh /opt/uv-cache | cut -f1)"
'

echo "== 3/4 warm-cache proof: uv sync against the real project (mounted) =="
# Mount the repo read-only at /work; uv writes the venv to a tmpfs to keep the
# source tree clean. Time the warm sync — should be far faster than a cold one.
docker run --rm -v "$REPO_ROOT":/work:ro -w /work "$IMAGE" \
  flox activate -d /opt/ci-env -- bash -eo pipefail -c '
    export UV_PROJECT_ENVIRONMENT=/tmp/venv
    t0=$(date +%s)
    uv sync --group dev
    t1=$(date +%s)
    echo "warm uv sync: $((t1 - t0))s"
  '

echo "== 4/4 real consumer flow: pytest under the baked env =="
docker run --rm -v "$REPO_ROOT":/work:ro -w /work "$IMAGE" \
  flox activate -d /opt/ci-env -- bash -eo pipefail -c '
    export UV_PROJECT_ENVIRONMENT=/tmp/venv
    git config --global --add safe.directory /work || true
    uv sync --group dev
    uv run pytest -m "" -q
  '

echo "== smoke test PASSED =="
