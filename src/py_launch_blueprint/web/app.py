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

``create_app()`` wires logging, config, the ``PyError`` → HTTP status mapping,
a request-id middleware, the operational endpoints (``/healthz``, ``/readyz``),
and every router. Adding a noun is one import + one entry in ``ROUTERS``
(see ``routers/__init__.py``).

Run it via the factory (``just serve``)::

    uvicorn py_launch_blueprint.web.app:create_app --factory
"""

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from py_launch_blueprint import __version__
from py_launch_blueprint.core.config import load_config
from py_launch_blueprint.core.diagnostics import run_diagnostics
from py_launch_blueprint.core.errors import APIError, AuthError, ConfigError, PyError
from py_launch_blueprint.core.logging import (
    bind_contextvars,
    clear_contextvars,
    configure_logging,
    get_logger,
)
from py_launch_blueprint.web.deps import ConfigDep
from py_launch_blueprint.web.routers import ROUTERS

log = get_logger(__name__)

#: HTTP status for each handled error class. The web analog of the ExitCode
#: taxonomy in ``core/errors.py`` — which failure maps to which code is domain
#: knowledge every front-end shares. Append-only, like the exit-code table.
ERROR_STATUS: dict[type[PyError], int] = {
    AuthError: 401,
    ConfigError: 500,
    APIError: 502,  # upstream Py API failed; this service is the gateway
}


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Configure logging and load config once for the app's lifetime."""
    configure_logging()
    app.state.config = load_config()
    log.info("web_startup", version=__version__)
    yield
    log.info("web_shutdown")


def create_app() -> FastAPI:
    """Build the FastAPI application (``uvicorn ... --factory`` entry point)."""
    app = FastAPI(
        title="py-launch-blueprint",
        version=__version__,
        lifespan=_lifespan,
    )

    @app.exception_handler(PyError)
    async def handle_py_error(_request: Request, exc: PyError) -> JSONResponse:
        status = ERROR_STATUS.get(type(exc), 500)
        log.warning("request_failed", error=exc.message, exit_code=int(exc.exit_code))
        return JSONResponse(status_code=status, content={"error": exc.message})

    @app.middleware("http")
    async def bind_request_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Request-scoped log context, same mechanism the CLI uses for
        # command-scoped context (core/logging.py contextvars).
        clear_contextvars()
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        """Liveness: the process is up (the web analog of ``--version``)."""
        return {"status": "ok", "version": __version__}

    @app.get("/readyz")
    async def readyz(config: ConfigDep) -> JSONResponse:
        """Readiness: the same checks as ``plbp doctor`` (503 on any error)."""
        report = run_diagnostics(config)
        return JSONResponse(
            status_code=503 if report.has_error() else 200,
            content=report.model_dump(mode="json"),
        )

    for router in ROUTERS:
        app.include_router(router)

    return app
