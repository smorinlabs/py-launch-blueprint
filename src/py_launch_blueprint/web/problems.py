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

"""RFC 9457 Problem Details — the single error envelope (WEB-01).

EVERY non-2xx response body is an ``application/problem+json`` document with
the same shape, including FastAPI's own 422 validation errors and bare
``HTTPException``s. The ``PyError`` → HTTP status table is the web analog of
the ``ExitCode`` taxonomy in ``core/errors.py`` — which failure maps to which
code is domain knowledge every front-end shares. Append-only, like the
exit-code table.
"""

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from py_launch_blueprint.core.errors import APIError, AuthError, ConfigError, PyError
from py_launch_blueprint.core.logging import get_logger

log = get_logger(__name__)

PROBLEM_CONTENT_TYPE = "application/problem+json"

ERROR_STATUS: dict[type[PyError], int] = {
    AuthError: status.HTTP_401_UNAUTHORIZED,
    ConfigError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    APIError: status.HTTP_502_BAD_GATEWAY,  # upstream Py API failed
}


class Problem(BaseModel):
    """RFC 9457 problem document (extension members are allowed by the RFC)."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None


def problem_response(
    request: Request,
    *,
    status_code: int,
    title: str,
    detail: str | None = None,
    extensions: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build an ``application/problem+json`` response."""
    body = Problem(
        title=title,
        status=status_code,
        detail=detail,
        instance=request.url.path,
    ).model_dump(exclude_none=True)
    if extensions:
        body.update(extensions)
    return JSONResponse(body, status_code=status_code, media_type=PROBLEM_CONTENT_TYPE)


def declare_problem_responses(app: FastAPI) -> None:
    """Make the OpenAPI schema tell the truth about 422s (WEB-01 + WEB-04).

    Runtime returns problem documents, so the schema must not advertise
    FastAPI's default ``HTTPValidationError`` + ``application/json`` —
    generated clients would parse the wrong shape. Call AFTER all routers
    are included (it wraps ``app.openapi``).
    """
    original_openapi = app.openapi

    def openapi_with_problems() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = original_openapi()
        components = schema.setdefault("components", {}).setdefault("schemas", {})
        components["Problem"] = Problem.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        for methods in schema.get("paths", {}).values():
            for operation in methods.values():
                response_422 = operation.get("responses", {}).get("422")
                if response_422 is not None:
                    response_422["description"] = "Validation Error (RFC 9457)"
                    response_422["content"] = {
                        PROBLEM_CONTENT_TYPE: {
                            "schema": {"$ref": "#/components/schemas/Problem"}
                        }
                    }
        # FastAPI's default validation-error schemas are now unreferenced.
        components.pop("HTTPValidationError", None)
        components.pop("ValidationError", None)
        app.openapi_schema = schema
        return schema

    app.openapi = openapi_with_problems  # ty: ignore[invalid-assignment]


def install_problem_handlers(app: FastAPI) -> None:
    """Register the handlers that funnel every error into one envelope."""

    @app.exception_handler(PyError)
    async def handle_py_error(request: Request, exc: PyError) -> JSONResponse:
        status_code = ERROR_STATUS.get(type(exc), 500)
        log.warning("request_failed", error=exc.message, exit_code=int(exc.exit_code))
        return problem_response(
            request,
            status_code=status_code,
            title=HTTPStatus(status_code).phrase,
            detail=exc.message,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return problem_response(
            request,
            status_code=exc.status_code,
            title=HTTPStatus(exc.status_code).phrase,
            detail=str(exc.detail) if exc.detail else None,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return problem_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Validation Error",
            detail="Request validation failed.",
            extensions={"errors": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # The catch-all: without it, unexpected errors bypass structlog (no
        # request_id) and answer in plain text, breaking WEB-01. The
        # traceback goes to the logs; the body stays generic — internals
        # are not for clients. Unlike handlers for specific exception
        # classes, Exception-level handlers run in Starlette's
        # ServerErrorMiddleware, which ALWAYS re-raises after the response
        # is sent (so the server can log/crash-report); test clients
        # therefore need raise_server_exceptions=False.
        log.error("unhandled_error", exc_info=exc)
        return problem_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            detail="An unexpected error occurred.",
        )
