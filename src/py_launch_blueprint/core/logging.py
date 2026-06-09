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

"""Structured logging: a console sink plus an optional rotating file sink.

structlog renders the events; stdlib ``logging`` handlers own the sinks, which
is what makes the dual-sink behavior (R11.6) work: both handlers attach to the
root logger, the logger floor is the most verbose sink, and each handler
filters independently — e.g. console at WARNING while the file gets DEBUG.

* **Console sink** (stderr, always on): human-friendly colored output on a
  TTY, JSON lines otherwise (CI/containers). Level from ``-v``/``-q``/
  ``--log-level`` (default WARNING).
* **File sink** (off by default): enabled by ``--log-file``/``$PLBP_LOG_FILE``
  or config ``logging.file``; rotates at 10 MB x 5 backups; has its own level
  (default DEBUG) and format (``text`` or ``json`` JSONL).

Logs always go to **stderr** (never stdout) so machine-readable results stay
pipe-safe. Call :func:`configure_logging` once at startup, then
``get_logger(__name__)`` anywhere; ``bind_contextvars`` attaches
command-scoped context.
"""

import logging
import sys
from enum import StrEnum
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
from structlog.typing import Processor

__all__ = [
    "LOG_LEVELS",
    "LogFormat",
    "bind_contextvars",
    "clear_contextvars",
    "configure_logging",
    "get_logger",
]

#: CLI/config level names -> stdlib levels (spec R10.4 / R11.4 vocabulary).
LOG_LEVELS: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

#: File sink rotation policy (R11.3): 10 MB per file, 5 backups.
ROTATE_MAX_BYTES = 10 * 1024 * 1024
ROTATE_BACKUP_COUNT = 5


class LogFormat(StrEnum):
    """How console log lines are rendered."""

    AUTO = "auto"
    CONSOLE = "console"
    JSON = "json"


def _resolve_format(fmt: LogFormat) -> LogFormat:
    """Resolve ``AUTO`` to console on a TTY, JSON otherwise."""
    if fmt is not LogFormat.AUTO:
        return fmt
    return LogFormat.CONSOLE if sys.stderr.isatty() else LogFormat.JSON


def _shared_processors() -> list[Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]


def configure_logging(
    level: int = logging.WARNING,
    fmt: LogFormat = LogFormat.AUTO,
    file_path: Path | None = None,
    file_level: int = logging.DEBUG,
    file_format: str = "text",
) -> None:
    """Configure the console sink and (optionally) the rotating file sink.

    Args:
        level: Console (stderr) level — default WARNING, ``-v`` INFO,
            ``-vv`` DEBUG, ``-q`` ERROR, ``--log-level`` explicit.
        fmt: Console render mode; ``AUTO`` picks console vs JSON from the TTY.
        file_path: Enables the file sink when set (R11.1). The parent
            directory is created (0700) if needed.
        file_level: File sink level, independent of the console (R11.4).
        file_format: ``"json"`` for JSONL or ``"text"`` for the file (R11.5).

    Idempotent: reconfiguring replaces previous handlers (safe in tests and
    repeated invocations).
    """
    shared = _shared_processors()

    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,  # stays reconfigurable
    )

    resolved = _resolve_format(fmt)
    console_renderer: Processor
    if resolved is LogFormat.JSON:
        console_renderer = structlog.processors.JSONRenderer()
    else:
        console_renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                console_renderer,
            ],
            foreign_pre_chain=shared,
        )
    )

    root = logging.getLogger()
    for handler in root.handlers[:]:  # close before removing (open log files)
        root.removeHandler(handler)
        handler.close()
    root.addHandler(console_handler)
    floor = level

    if file_path is not None:
        file_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        file_renderer: Processor
        if file_format == "json":
            file_renderer = structlog.processors.JSONRenderer()
        else:
            file_renderer = structlog.dev.ConsoleRenderer(colors=False)
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=ROTATE_MAX_BYTES,
            backupCount=ROTATE_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    file_renderer,
                ],
                foreign_pre_chain=shared,
            )
        )
        root.addHandler(file_handler)
        floor = min(level, file_level)

    # R11.6: the logger floor is the most verbose sink; handlers filter.
    root.setLevel(floor)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger (configure first)."""
    return structlog.get_logger(name)
