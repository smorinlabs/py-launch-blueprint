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
    ) -> "AppContext":
        """Build the context from raw global-option values."""
        mode = _resolve_mode(output_mode, json_mode)

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
            renderer=Renderer(mode=mode, no_color=no_color),
            output_mode=mode,
            config_file=config_file,
            token=token,
            no_input=no_input,
            verbose=verbose,
        )

    @property
    def config(self) -> Config:
        """Lazily resolve and cache configuration."""
        if self._config is None:
            self._config = load_config(
                config_file=self.config_file, token_override=self.token
            )
        return self._config


def _resolve_mode(output_mode: str | None, json_mode: bool) -> OutputMode:
    """``--json`` wins; otherwise use ``--output`` or default to human."""
    if json_mode:
        return OutputMode.JSON
    if output_mode:
        return OutputMode(output_mode)
    return OutputMode.HUMAN
