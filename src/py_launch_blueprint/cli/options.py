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

"""The ``@global_options`` decorator — one set of flags on every command.

Stacking these per-command (rather than only on the root group) lets users put
flags after the verb, gh-style: ``pylb projects list --json``. The decorator
consumes the global values, builds an :class:`AppContext`, and passes it as the
first argument to the wrapped command.
"""

import functools
from collections.abc import Callable
from typing import Any, cast

import click

from py_launch_blueprint.cli.context import AppContext
from py_launch_blueprint.cli.output import OutputMode
from py_launch_blueprint.core.errors import ExitCode, PyError

_OUTPUT_CHOICES = [mode.value for mode in OutputMode]

# Applied bottom-up (reversed) so they appear top-down in --help.
_GLOBAL_OPTIONS: list[Callable[[Any], Any]] = [
    click.option(
        "-o",
        "--output",
        "output_mode",
        type=click.Choice(_OUTPUT_CHOICES),
        default=None,
        help="Output format. [default: human]",
    ),
    click.option(
        "--json",
        "json_mode",
        is_flag=True,
        help="Shorthand for --output json.",
    ),
    click.option(
        "-v", "--verbose", count=True, help="Increase log verbosity (-vv for debug)."
    ),
    click.option(
        "-q", "--quiet", is_flag=True, help="Suppress non-essential stderr output."
    ),
    click.option("--no-color", is_flag=True, help="Disable colored output."),
    click.option(
        "--config",
        "config_file",
        type=click.Path(dir_okay=False),
        default=None,
        help="Path to a .env config file.",
    ),
    click.option(
        "--token",
        default=None,
        help="Py Personal Access Token (overrides env and config file).",
    ),
    click.option(
        "--no-input", is_flag=True, help="Never prompt; fail instead (for scripts/CI)."
    ),
]


def global_options[F: Callable[..., Any]](func: F) -> F:
    """Attach the global options and inject an ``AppContext`` first arg."""

    @functools.wraps(func)
    def wrapper(
        *args: Any,
        output_mode: str | None,
        json_mode: bool,
        verbose: int,
        quiet: bool,
        no_color: bool,
        config_file: str | None,
        token: str | None,
        no_input: bool,
        **kwargs: Any,
    ) -> Any:
        app = AppContext.create(
            output_mode=output_mode,
            json_mode=json_mode,
            verbose=verbose,
            quiet=quiet,
            no_color=no_color,
            config_file=config_file,
            token=token,
            no_input=no_input,
        )
        try:
            return func(app, *args, **kwargs)
        except PyError as exc:
            app.renderer.error(exc.message, exc.exit_code)
            raise SystemExit(int(exc.exit_code)) from exc
        except KeyboardInterrupt:
            app.renderer.error("Interrupted.", ExitCode.INTERRUPT)
            raise SystemExit(int(ExitCode.INTERRUPT)) from None
        except Exception as exc:
            app.renderer.error(str(exc), ExitCode.IO)
            if app.verbose:
                app.renderer.err.print_exception()
            raise SystemExit(int(ExitCode.IO)) from exc

    decorated: Any = wrapper
    for option in reversed(_GLOBAL_OPTIONS):
        decorated = option(decorated)
    return cast(F, decorated)
