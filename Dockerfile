# Production image for the web service (WEB-32).
# Multi-stage uv build per https://docs.astral.sh/uv/guides/integration/docker/
#   docker build -t plbp-web .          (or: just docker-web)
#   docker run --rm -p 8000:8000 plbp-web

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
# Dependency layer first (cached until the lockfile changes), project second.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --extra web
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra web

FROM python:3.12-slim-bookworm
RUN groupadd -r app && useradd -r -g app app
COPY --from=builder --chown=app:app /app /app
USER app
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    # Containers bind all interfaces; the in-code default stays loopback.
    PLBP_WEB_HOST=0.0.0.0
EXPOSE 8000
# Liveness probe against the unversioned ops endpoint (WEB-02); urllib —
# the slim base image has no curl.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz').read()" || exit 1
# python -m runs WebSettings-driven uvicorn with graceful shutdown (WEB-31).
CMD ["python", "-m", "py_launch_blueprint.web"]
