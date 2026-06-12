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

"""HTTP middleware: request-id context, access log, security headers (WEB-23).

Request-scoped log context uses the same structlog contextvars mechanism the
CLI uses for command-scoped context (``core/logging.py``). The canonical
``http_request`` access event (WEB-12) is emitted here — one wide event per
request with the route *template* (bounded cardinality), status, and
``duration_ms`` — replacing uvicorn's plain-text access line (see
``web/logging.py``).
"""

import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from py_launch_blueprint.core.logging import (
    bind_contextvars,
    clear_contextvars,
    get_logger,
)

log = get_logger(__name__)

#: Probe/scrape endpoints are excluded from access logging (as they already
#: are from metrics instrumentation) — they'd dominate the volume.
ACCESS_LOG_EXCLUDED_PATHS: frozenset[str] = frozenset(
    {"/healthz", "/readyz", "/metrics"}
)

#: Conservative defaults for a JSON API: no sniffing, no framing, no referrer
#: leakage. HSTS is set unconditionally — harmless over plain http in dev,
#: required behind the TLS-terminating proxy in prod.
SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Bind a request id, emit the access event, echo the id as a header."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        clear_contextvars()
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # The canonical line must exist even when the request dies — the
            # 500 problem handler logs the traceback; this records the request.
            _log_access(request, status_code=500, start=start)
            raise
        response.headers["x-request-id"] = request_id
        _log_access(request, status_code=response.status_code, start=start)
        return response


def _log_access(request: Request, *, status_code: int, start: float) -> None:
    """Emit the one-per-request ``http_request`` event (WEB-12)."""
    if request.url.path in ACCESS_LOG_EXCLUDED_PATHS:
        return
    # The router sets scope["route"] once matched. Unmatched requests (404s)
    # log route=None — falling back to the raw path here would let URL spam
    # blow up the one field kept bounded-cardinality on purpose.
    matched = request.scope.get("route")
    log.info(
        "http_request",
        method=request.method,
        route=getattr(matched, "path", None),
        path=request.url.path,
        status=status_code,
        duration_ms=round((time.perf_counter() - start) * 1000, 2),
        client=request.client.host if request.client else None,
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Stamp the standard security headers on every response."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        return response
