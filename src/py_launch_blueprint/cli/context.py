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

from py_launch_blueprint.cli.output import OutputMode, Renderer
from py_launch_blueprint.core.config import Config, load_config
from py_launch_blueprint.core.logging import LogFormat, configure_logging


@dataclass
class AppContext:
    """Resolved global state for a single CLI invocation."""

    renderer: Renderer
    output_mode: OutputMode
    config_file: str | None
    token: str | None
    no_input: bool
    verbose: int

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
    ) -> "AppContext":
        """Build the context from raw global-option values.

        Config is loaded eagerly (it never raises on missing/invalid files)
        because output format and color resolve from it when no flag/env says
        otherwise (R7 precedence: flag → env → config → default).
        """
        config = load_config(config_file=config_file, token_override=token)
        settings = config.settings

        mode = _resolve_mode(output_mode, json_mode, settings.output.format)
        color = _resolve_color(no_color, settings.output.color)
        renderer = Renderer(mode=mode, color=color, output_file=output_file)
        # Non-fatal load problems (invalid values dropped, unreadable
        # discovered layers) are surfaced on stderr, never swallowed.
        for warning in config.warnings:
            renderer.message(f"[yellow]warning:[/yellow] {warning}")

        # Verbosity → log level: default WARNING, -v INFO, -vv DEBUG, -q ERROR.
        if quiet:
            level = logging.ERROR
        elif verbose >= 2:
            level = logging.DEBUG
        elif verbose == 1:
            level = logging.INFO
        else:
            level = logging.WARNING
        configure_logging(level=level, fmt=LogFormat.AUTO)

        return cls(
            renderer=renderer,
            output_mode=mode,
            config_file=config_file,
            token=token,
            no_input=no_input,
            verbose=verbose,
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
