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

"""The web logging *profile* (WEB-12) — policy over the shared core pipeline.

Same engine as the CLI (``core/logging.py``), different policy: level and
format come from :class:`~py_launch_blueprint.web.settings.WebSettings` env
vars only (12-factor), the default is INFO + JSON lines (structured output is
the contract, not a TTY accident), and there is **no file sink** — a service
logs to stderr and the platform owns rotation and shipping.

uvicorn's loggers are folded into the same pipeline: ``uvicorn``/
``uvicorn.error`` propagate to the root structlog handlers (server lifecycle
lines come out structured like everything else), and ``uvicorn.access`` is
silenced — the canonical ``http_request`` event emitted by
:class:`~py_launch_blueprint.web.middleware.RequestIDMiddleware` replaces it,
carrying ``request_id``, the route template, and ``duration_ms``.

Called at the top of ``create_app()`` so logging is configured before any
code that can log runs (telemetry wiring logs during app construction).
"""

import logging

from py_launch_blueprint.core.logging import LOG_LEVELS, LogFormat, configure_logging
from py_launch_blueprint.web.settings import WebSettings

__all__ = ["configure_web_logging"]


def configure_web_logging(settings: WebSettings) -> None:
    """Configure the shared pipeline with the web policy and adopt uvicorn.

    Args:
        settings: Source of ``log_level``/``log_format``
            (``<APP_NAME>_WEB_LOG_LEVEL`` / ``_LOG_FORMAT`` env vars).

    Idempotent, like :func:`configure_logging` — safe under ``--reload`` and
    repeated app construction in tests.
    """
    configure_logging(
        level=LOG_LEVELS[settings.log_level],
        fmt=LogFormat(settings.log_format),
    )
    # uvicorn configures its own handlers before loading the app factory;
    # detach them so server lifecycle logs flow through the root structlog
    # handlers instead (foreign_pre_chain renders them like native events).
    for name in ("uvicorn", "uvicorn.error"):
        server_logger = logging.getLogger(name)
        server_logger.handlers.clear()
        server_logger.propagate = True
    # The plain-text access line is superseded by the structured
    # `http_request` event (which uvicorn's line could never carry:
    # request_id, route template, duration_ms).
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False
