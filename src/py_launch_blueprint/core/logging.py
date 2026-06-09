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

"""Structured logging, configured once and shared by every front-end.

We use `structlog <https://www.structlog.org/>`_ (see the proposal notes for
why over loguru / python-json-logger). Logs always go to **stderr** so that
machine-readable results on stdout stay clean and pipe-safe.

Two render modes:

* ``LogFormat.CONSOLE`` — colorized, human-friendly (default on a TTY).
* ``LogFormat.JSON`` — one JSON object per line (default when stderr is not a
  TTY, e.g. in CI / containers / when piped), ideal for log shippers.

Call :func:`configure_logging` once at startup, then ``get_logger(__name__)``
anywhere. Use ``bind_contextvars`` to attach request/command-scoped context.
"""

import logging
import sys
from enum import StrEnum

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
from structlog.typing import Processor

__all__ = [
    "LogFormat",
    "bind_contextvars",
    "clear_contextvars",
    "configure_logging",
    "get_logger",
]


class LogFormat(StrEnum):
    """How log lines are rendered."""

    AUTO = "auto"
    CONSOLE = "console"
    JSON = "json"


def _resolve_format(fmt: LogFormat) -> LogFormat:
    """Resolve ``AUTO`` to console on a TTY, JSON otherwise."""
    if fmt is not LogFormat.AUTO:
        return fmt
    return LogFormat.CONSOLE if sys.stderr.isatty() else LogFormat.JSON


def configure_logging(
    level: int = logging.WARNING,
    fmt: LogFormat = LogFormat.AUTO,
) -> None:
    """Configure structlog for the whole process.

    Args:
        level: Standard logging level (e.g. ``logging.INFO``). Map CLI
            verbosity to this: default WARNING, ``-v`` INFO, ``-vv`` DEBUG.
        fmt: Render mode; ``AUTO`` picks console vs JSON from the TTY state.
    """
    resolved = _resolve_format(fmt)

    shared: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    renderer: Processor
    if resolved is LogFormat.JSON:
        shared.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[*shared, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        # WriteLoggerFactory writes atomically to stderr (avoids interleaving).
        logger_factory=structlog.WriteLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger (configure first)."""
    return structlog.get_logger(name)
