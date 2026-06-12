# Copyright (c) 2025, Steve Morin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""FastAPI app factory — the web counterpart of ``cli/main.py``.

``create_app()`` wires, in order: typed settings (WEB-30), the RFC 9457
problem-details handlers (WEB-01), the middleware stack (request-id logging,
security headers WEB-23, idempotency replay WEB-05, optional CORS and rate
limiting WEB-22), metrics/tracing (WEB-11/10), the unversioned operational
endpoints, and every business router under ``/v1`` (WEB-02). Adding a noun is
one import + one entry in ``ROUTERS`` (see ``routers/__init__.py``).

Run it via the factory (``just serve``), ``python -m py_launch_blueprint.web``,
or the Dockerfile::

    uvicorn py_launch_blueprint.web.app:create_app --factory
"""

import platform
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi_pagination import add_pagination

from py_launch_blueprint import __version__
from py_launch_blueprint.core.config import load_config
from py_launch_blueprint.core.diagnostics import run_diagnostics
from py_launch_blueprint.core.logging import configure_logging, get_logger
from py_launch_blueprint.web.deps import ConfigDep
from py_launch_blueprint.web.idempotency import IdempotencyMiddleware
from py_launch_blueprint.web.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from py_launch_blueprint.web.problems import (
    install_problem_handlers,
    problem_response,
)
from py_launch_blueprint.web.routers import ROUTERS
from py_launch_blueprint.web.settings import WebSettings
from py_launch_blueprint.web.telemetry import instrument_metrics, instrument_tracing
from py_launch_blueprint.web.versioning import V1_PREFIX

log = get_logger(__name__)

OPENAPI_TAGS = [
    {"name": "projects", "description": "Py projects (same models the CLI renders)."},
    {"name": "ops", "description": "Liveness, readiness, and build info."},
]


def _operation_id(route: APIRoute) -> str:
    """Stable, client-friendly operation ids: ``<tag>-<function-name>``."""
    prefix = f"{route.tags[0]}-" if route.tags else ""
    return f"{prefix}{route.name}"


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Configure logging and load config once for the app's lifetime."""
    configure_logging()
    app.state.config = load_config()
    log.info("web_startup", version=__version__)
    yield
    # Shutdown side of graceful termination (WEB-31): uvicorn stops accepting,
    # drains in-flight requests (--timeout-graceful-shutdown), then runs this.
    log.info("web_shutdown")


def create_app(settings: WebSettings | None = None) -> FastAPI:
    """Build the FastAPI application (``uvicorn ... --factory`` entry point)."""
    settings = settings if settings is not None else WebSettings()

    app = FastAPI(
        title="py-launch-blueprint",
        version=__version__,
        description=(
            "REST API over the same core library the CLI uses. Errors are "
            "RFC 9457 `application/problem+json`; business routes live under "
            "`/v1`; collections paginate with `page`/`size` query params."
        ),
        openapi_tags=OPENAPI_TAGS,
        generate_unique_id_function=_operation_id,
        lifespan=_lifespan,
        root_path=settings.root_path,
    )
    app.state.settings = settings

    install_problem_handlers(app)

    # Middleware (added inside-out: the last add_middleware runs first).
    app.add_middleware(
        IdempotencyMiddleware,
        ttl_seconds=settings.idempotency_ttl_seconds,
        max_entries=settings.idempotency_max_entries,
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    if settings.rate_limit:
        _install_rate_limiting(app, settings.rate_limit)

    if settings.metrics_enabled:
        instrument_metrics(app)
    if settings.otel_enabled:
        instrument_tracing(app)

    @app.get("/healthz", tags=["ops"])
    async def healthz() -> dict[str, str]:
        """Liveness + build info (the web analog of ``--version``)."""
        return {
            "status": "ok",
            "version": __version__,
            "python": platform.python_version(),
        }

    @app.get("/readyz", tags=["ops"])
    async def readyz(config: ConfigDep) -> JSONResponse:
        """Readiness: the same checks as ``plbp doctor`` (503 on any error)."""
        report = run_diagnostics(config)
        return JSONResponse(
            status_code=503 if report.has_error() else 200,
            content=report.model_dump(mode="json"),
        )

    for router in ROUTERS:
        app.include_router(router, prefix=V1_PREFIX)

    add_pagination(app)
    return app


def _install_rate_limiting(app: FastAPI, default_limit: str) -> None:
    """Wire slowapi with one app-wide default limit (WEB-22)."""
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address
    from starlette.requests import Request

    limiter = Limiter(key_func=get_remote_address, default_limits=[default_limit])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # Sync on purpose: SlowAPIMiddleware silently swaps async handlers for
    # its default (plain JSON) one — see slowapi.middleware.sync_check_limits.
    def handle_rate_limited(request: Request, exc: Exception) -> JSONResponse:
        # exc is always RateLimitExceeded (registered below); getattr keeps
        # the broad signature slowapi calls with, without an assert.
        response = problem_response(
            request,
            status_code=429,
            title="Too Many Requests",
            detail=f"Rate limit exceeded: {getattr(exc, 'detail', exc)}",
        )
        response.headers["Retry-After"] = "1"
        return response

    app.add_exception_handler(RateLimitExceeded, handle_rate_limited)
