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

"""Per-invocation application context shared across commands.

Built once from the global options (see ``options.py``) and threaded into each
command. Holds the resolved output renderer and lazily loads configuration so
commands that don't need a token (e.g. ``config path``) never trigger lookup.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import click

from py_launch_blueprint.cli.output import OutputMode, Renderer
from py_launch_blueprint.core import paths
from py_launch_blueprint.core.config import Config, load_config
from py_launch_blueprint.core.errors import ConfigError
from py_launch_blueprint.core.logging import (
    LOG_LEVELS,
    LogFormat,
    configure_logging,
    get_logger,
)
from py_launch_blueprint.core.settings import LoggingSettings

#: flag_value sentinel for `--log-file` used without a PATH (R11.2).
LOG_FILE_DEFAULT_SENTINEL = "__PLBP_LOG_FILE_DEFAULT__"


@dataclass
class AppContext:
    """Resolved global state for a single CLI invocation."""

    renderer: Renderer
    output_mode: OutputMode
    config_file: str | None
    token: str | None
    no_input: bool
    verbose: int
    quiet: bool = False

    _config: Config | None = None

    @classmethod
    def create(
        cls,
        *,
        output_mode: str | None,
        json_mode: bool,
        verbose: int,
        quiet: bool,
        no_color: bool,
        config_file: str | None,
        no_input: bool,
        token: str | None,
        output_file: str | None = None,
        log_level: str | None = None,
        log_file: str | None = None,
    ) -> "AppContext":
        """Build the context from raw global-option values.

        Config is loaded eagerly (it never raises on missing/invalid files)
        because output format, color, and logging resolve from it when no
        flag/env says otherwise (R7 precedence: flag → env → config → default).
        """
        config = load_config(config_file=config_file, token_override=token)
        settings = config.settings

        mode = _resolve_mode(output_mode, json_mode, settings.output.format)
        color = _resolve_color(no_color, settings.output.color)
        # --no-input also disables the pager: a script that can't answer
        # prompts can't quit `less` either.
        renderer = Renderer(
            mode=mode, color=color, output_file=output_file, paging=not no_input
        )
        # Non-fatal load problems (invalid values dropped, unreadable
        # discovered layers) are surfaced on stderr, never swallowed.
        for warning in config.warnings:
            renderer.message(f"[yellow]warning:[/yellow] {warning}")

        file_path = _resolve_log_file(log_file, settings.logging)
        configure_logging(
            level=_resolve_console_level(
                log_level, verbose, quiet, settings.logging.level
            ),
            fmt=LogFormat.AUTO,
            file_path=file_path,
            file_level=LOG_LEVELS[settings.logging.file_level],
            file_format=_resolve_log_format(settings.logging.format),
        )
        get_logger(__name__).debug(
            "invocation context ready",
            output_mode=str(mode),
            color=color,
            log_file=str(file_path) if file_path else None,
        )

        return cls(
            renderer=renderer,
            output_mode=mode,
            config_file=config_file,
            token=token,
            no_input=no_input,
            verbose=verbose,
            quiet=quiet,
            _config=config,
        )

    @property
    def config(self) -> Config:
        """Return the resolved configuration (loaded in :meth:`create`)."""
        if self._config is None:
            self._config = load_config(
                config_file=self.config_file, token_override=self.token
            )
        return self._config


def maybe_show_first_run_hint(app: AppContext) -> None:
    """One-time stderr hint pointing fresh installs at ``plbp config init``.

    Fires only when it cannot pollute anything: interactive stderr, prompts
    allowed, not ``--quiet``, no config file found in any layer (JSON mode is
    already silent — ``message()`` is a no-op there). A marker file in the
    XDG state dir makes it once-ever; an unwritable state dir skips the hint
    rather than repeating or failing the command.
    """
    if app.no_input or app.quiet or not app.renderer.err.is_terminal:
        return
    # JSON mode would swallow the message (``message()`` is a no-op there);
    # bail before the marker is written or the hint is burned unseen.
    if app.output_mode is OutputMode.JSON:
        return
    if app.config.loaded_paths:
        return
    ctx = click.get_current_context(silent=True)
    if ctx is not None and ctx.command_path.endswith("config init"):
        return
    marker = paths.state_file("first_run", "marker")
    if marker.exists():
        return
    try:
        paths.ensure_dir(marker.parent)
        marker.touch()
    except OSError:
        return
    app.renderer.message(
        "Welcome to plbp! Run [bold]plbp config init[/bold] to create a "
        "config file. (This hint is shown once.)"
    )


def _resolve_mode(
    output_mode: str | None, json_mode: bool, config_format: str = "text"
) -> OutputMode:
    """``--json`` wins; then ``--output`` (flag or PLBP_OUTPUT); then config.

    Format never auto-switches on TTY (R3.3): a piped run formats the same as
    an interactive one unless something explicitly says otherwise.
    """
    if json_mode:
        return OutputMode.JSON
    if output_mode:
        return OutputMode(output_mode)
    return OutputMode(config_format)


def _resolve_color(no_color_flag: bool, config_color: str) -> str:
    """R5.5 precedence: --no-color flag > NO_COLOR env > config > auto."""
    if no_color_flag:
        return "never"
    if os.environ.get("NO_COLOR"):
        return "never"
    return config_color  # "auto" | "always" | "never"


def _resolve_console_level(
    log_level: str | None, verbose: int, quiet: bool, config_level: str
) -> int:
    """Console level: --log-level (or env) > -q/-v > config > WARNING (R10)."""
    if log_level:
        return LOG_LEVELS[log_level]
    if quiet:
        return logging.ERROR
    if verbose >= 2:
        return logging.DEBUG
    if verbose == 1:
        return logging.INFO
    return LOG_LEVELS[config_level]


def _resolve_log_file(
    log_file: str | None, logging_settings: LoggingSettings
) -> Path | None:
    """File sink path: flag/env > config ``logging.file`` > off (R11.1/R11.2).

    Bare ``--log-file`` (no PATH) selects the default XDG state location.
    R12 says *presence* of ``$PLBP_LOG_FILE`` enables the sink, but click
    treats an empty env value as unset — so check the environment directly:
    ``PLBP_LOG_FILE=`` (set, empty) also enables the default location.
    """
    if log_file is None and "PLBP_LOG_FILE" in os.environ:
        log_file = os.environ["PLBP_LOG_FILE"] or LOG_FILE_DEFAULT_SENTINEL
    if log_file == LOG_FILE_DEFAULT_SENTINEL:
        return paths.log_file()
    if log_file:
        return Path(log_file).expanduser()
    if logging_settings.file:
        return Path(logging_settings.file).expanduser()
    return None


def _resolve_log_format(config_format: str) -> str:
    """File sink format: $PLBP_LOG_FORMAT > config ``logging.format``.

    The env value is validated like every other knob — a typo must not
    silently fall back to text.
    """
    raw = os.environ.get("PLBP_LOG_FORMAT")
    if raw is None or raw == "":
        return config_format
    normalized = raw.strip().lower()
    if normalized not in ("text", "json"):
        raise ConfigError(f"invalid PLBP_LOG_FORMAT: {raw!r} (allowed: text, json)")
    return normalized
