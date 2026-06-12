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
flags after the verb, gh-style: ``plbp projects list --json``. The decorator
consumes the global values, builds an :class:`AppContext`, and passes it as the
first argument to the wrapped command.
"""

import datetime
import functools
import traceback
from collections.abc import Callable
from typing import Any, cast

import click

from py_launch_blueprint.cli.context import (
    LOG_FILE_DEFAULT_SENTINEL,
    AppContext,
    maybe_show_first_run_hint,
)
from py_launch_blueprint.cli.output import OutputMode, Renderer
from py_launch_blueprint.core import paths
from py_launch_blueprint.core.errors import (
    ERROR_CODE_INTERRUPT,
    ERROR_CODE_UNEXPECTED,
    ConfigError,
    ExitCode,
    PyError,
)
from py_launch_blueprint.core.logging import LOG_LEVELS

_OUTPUT_CHOICES = [mode.value for mode in OutputMode]

# Applied bottom-up (reversed) so they appear top-down in --help.
_GLOBAL_OPTIONS: list[Callable[[Any], Any]] = [
    click.option(
        "-o",
        "--output",
        "output_mode",
        type=click.Choice(_OUTPUT_CHOICES),
        default=None,
        envvar="PLBP_OUTPUT",
        help="Output format. [default: text]",
    ),
    click.option(
        "--json",
        "json_mode",
        is_flag=True,
        help="Shorthand for --output json.",
    ),
    click.option(
        "--output-file",
        "output_file",
        type=click.Path(dir_okay=False, writable=True),
        default=None,
        help="Write results to a file instead of stdout (format set by --output).",
    ),
    click.option(
        "-v", "--verbose", count=True, help="Increase log verbosity (-vv for debug)."
    ),
    click.option(
        "-q", "--quiet", is_flag=True, help="Suppress non-essential stderr output."
    ),
    click.option(
        "--log-level",
        "log_level",
        type=click.Choice(list(LOG_LEVELS)),
        default=None,
        envvar="PLBP_LOG_LEVEL",
        help="Explicit console log level (overrides -v/-q).",
    ),
    click.option(
        "--log-file",
        "log_file",
        is_flag=False,
        flag_value=LOG_FILE_DEFAULT_SENTINEL,
        default=None,
        envvar="PLBP_LOG_FILE",
        help="Enable rotating file logging (PATH optional; default: XDG state).",
    ),
    click.option("--no-color", is_flag=True, help="Disable colored output."),
    click.option(
        "--config",
        "config_file",
        type=click.Path(dir_okay=False),
        default=None,
        envvar="PLBP_CONFIG",
        help="Path to a TOML config file (overrides layered discovery).",
    ),
    click.option(
        "--token",
        default=None,
        help="Py Personal Access Token (overrides $PLBP_TOKEN). Never stored.",
    ),
    click.option(
        "--no-input", is_flag=True, help="Never prompt; fail instead (for scripts/CI)."
    ),
]


def _fallback_renderer(
    output_mode: str | None, json_mode: bool, no_color: bool
) -> Renderer:
    """Minimal renderer for errors raised *while building* the context.

    Resolved from flags only — the config that would refine format/color is
    exactly what failed to load.
    """
    mode = OutputMode.JSON if json_mode else OutputMode(output_mode or "text")
    return Renderer(mode=mode, color="never" if no_color else "auto")


def _write_crash_log(exc: BaseException) -> str | None:
    """Append the traceback to the crash log; return its path (best-effort).

    Unexpected errors must never vanish: without ``--verbose`` the user only
    sees the message, so the full traceback goes to
    ``<state>/plbp/plbp_crash.log`` and the error output points at it.
    Returns ``None`` if even that write fails — reporting a crash must not
    crash.
    """
    try:
        crash_path = paths.state_file("crash")
        paths.ensure_dir(crash_path.parent)
        stamp = datetime.datetime.now(datetime.UTC).isoformat()
        rendered = "".join(traceback.format_exception(exc))
        with crash_path.open("a", encoding="utf-8") as handle:
            handle.write(f"--- {stamp} ---\n{rendered}\n")
        return str(crash_path)
    except OSError:
        return None


def global_options[F: Callable[..., Any]](func: F) -> F:
    """Attach the global options and inject an ``AppContext`` first arg."""

    @functools.wraps(func)
    def wrapper(
        *args: Any,
        output_mode: str | None,
        json_mode: bool,
        output_file: str | None,
        verbose: int,
        quiet: bool,
        log_level: str | None,
        log_file: str | None,
        no_color: bool,
        config_file: str | None,
        token: str | None,
        no_input: bool,
        **kwargs: Any,
    ) -> Any:
        # create() does real work now (config load, logging setup), so its
        # failures must be rendered, not tracebacked. Errors here are
        # configuration-shaped by construction -> ExitCode.CONFIG.
        try:
            app = AppContext.create(
                output_mode=output_mode,
                json_mode=json_mode,
                output_file=output_file,
                verbose=verbose,
                quiet=quiet,
                log_level=log_level,
                log_file=log_file,
                no_color=no_color,
                config_file=config_file,
                token=token,
                no_input=no_input,
            )
        except PyError as exc:
            _fallback_renderer(output_mode, json_mode, no_color).error(
                exc.message, exc.exit_code, error_code=exc.error_code, hint=exc.hint
            )
            raise SystemExit(int(exc.exit_code)) from exc
        except Exception as exc:
            # Unexpected failure while building the context (renderer,
            # logging, paths setup) follows the same contract as any other
            # unexpected error: PLBP000 + crash log — not a config error,
            # which would send the user debugging a healthy config file.
            _fallback_renderer(output_mode, json_mode, no_color).error(
                str(exc),
                ExitCode.IO,
                error_code=ERROR_CODE_UNEXPECTED,
                traceback_path=_write_crash_log(exc),
            )
            raise SystemExit(int(ExitCode.IO)) from exc
        try:
            maybe_show_first_run_hint(app)
            return func(app, *args, **kwargs)
        except PyError as exc:
            app.renderer.error(
                exc.message, exc.exit_code, error_code=exc.error_code, hint=exc.hint
            )
            raise SystemExit(int(exc.exit_code)) from exc
        except KeyboardInterrupt:
            app.renderer.error(
                "Interrupted.", ExitCode.INTERRUPT, error_code=ERROR_CODE_INTERRUPT
            )
            raise SystemExit(int(ExitCode.INTERRUPT)) from None
        except Exception as exc:
            app.renderer.error(
                str(exc),
                ExitCode.IO,
                error_code=ERROR_CODE_UNEXPECTED,
                traceback_path=_write_crash_log(exc),
            )
            if app.verbose:
                app.renderer.err.print_exception()
            raise SystemExit(int(ExitCode.IO)) from exc

    decorated: Any = wrapper
    for option in reversed(_GLOBAL_OPTIONS):
        decorated = option(decorated)
    return cast(F, decorated)


# Safety options for mutating commands (create/delete/set). Unlike the global
# options, these add no wrapper — the command just receives `dry_run` and
# `assume_yes` as parameters.
_MUTATION_OPTIONS: list[Callable[[Any], Any]] = [
    click.option(
        "--dry-run",
        "dry_run",
        is_flag=True,
        help="Show what would change; write nothing.",
    ),
    click.option(
        "-y",
        "--yes",
        "assume_yes",
        is_flag=True,
        help="Skip confirmation prompts (for scripts/CI).",
    ),
]


def mutation_options[F: Callable[..., Any]](func: F) -> F:
    """Attach ``--dry-run`` and ``-y/--yes`` to a mutating command."""
    decorated: Any = func
    for option in reversed(_MUTATION_OPTIONS):
        decorated = option(decorated)
    return cast(F, decorated)


def confirm(app: AppContext, prompt: str, *, assume_yes: bool) -> bool:
    """Gate a destructive action; return True to proceed.

    ``--yes`` proceeds unconditionally; ``--no-input`` refuses (it cannot
    prompt); otherwise ask on **stderr** so stdout stays clean for piping.
    """
    if assume_yes:
        return True
    if app.no_input:
        raise ConfigError(
            f"refusing to proceed without confirmation (--no-input): {prompt}",
            hint="pass --yes to confirm non-interactively",
        )
    return click.confirm(prompt, default=False, err=True)
