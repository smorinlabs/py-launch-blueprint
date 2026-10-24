# Build image for Anthropic OSS Scanner (P09). Not a production image — see
# the root Dockerfile for that. The scanner builds this with the repository
# as the build context, then runs its agents fully offline, so everything a
# test or exploit might need is installed here.
#   docker build -f .oss-scanner/Dockerfile -t plbp-oss-scanner .
#   docker run --rm --network none plbp-oss-scanner uv run pytest

FROM oven/bun:1.3.5-debian AS bun

FROM ghcr.io/astral-sh/uv:python3.13-bookworm
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# bun runs the release generator (scripts/release_commits.cjs) and its tests;
# just runs the Justfile tests. Versions match .bun-version and mise.toml.
COPY --from=bun /usr/local/bin/bun /usr/local/bin/bun
RUN uv tool install rust-just==1.57.0
ENV PATH="/root/.local/bin:$PATH"

# Scanner contract: the checkout lives inside the image, at /src.
COPY . /src
WORKDIR /src

# Dev tools plus every extra (web, otel), so all code paths run offline.
RUN uv sync --locked --group dev --all-extras \
    && bun install --frozen-lockfile
# Offline from here on: never re-resolve, and expose the venv directly.
ENV UV_NO_SYNC=1 \
    PATH="/src/.venv/bin:$PATH"

# Prove the image works without letting one failing test abort the build.
# The deselected test reads git history, which the root .dockerignore keeps
# out of the build context.
RUN uv run pytest -q \
      --deselect "tests/meta/test_contributors_state.py::test_commit_contributor_first_seen_matches_earliest_non_merge_commit" \
    || echo "WARNING: pytest reported failures"
