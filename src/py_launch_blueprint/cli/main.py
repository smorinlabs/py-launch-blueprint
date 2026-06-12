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

"""Root command group for the ``plbp`` CLI.

Wires the global help option, an extended ``--version``, shell completion, and
every noun group. Adding a noun is one import + one entry in ``COMMAND_GROUPS``
(see ``commands/__init__.py``).
"""

import platform
from typing import Any

import click
from click.shell_completion import get_completion_class

from py_launch_blueprint import __version__
from py_launch_blueprint.cli.commands import COMMAND_GROUPS
from py_launch_blueprint.cli.context import AppContext
from py_launch_blueprint.cli.groups import SuggestingGroup
from py_launch_blueprint.cli.options import global_options
from py_launch_blueprint.core.diagnostics import build_bundle, run_diagnostics
from py_launch_blueprint.core.errors import ExitCode
from py_launch_blueprint.core.paths import APP_NAME

# Derived from the single APP_NAME source (core/paths.py) — not greppable
# user-facing literals, so they track a rename automatically. The env-var
# prefix and the click completion var are both APP_NAME-shaped.
_COMPLETE_VAR = f"_{APP_NAME.upper()}_COMPLETE"
_PROG_NAME = "plbp"


def _print_version(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    """Eager callback: print version + runtime info, then exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"{_PROG_NAME} {__version__}")
    click.echo(f"python {platform.python_version()}")
    click.echo(f"platform {platform.platform()}")
    ctx.exit()


@click.group(
    name=_PROG_NAME,
    cls=SuggestingGroup,
    context_settings={
        "help_option_names": ["-h", "--help"],
        # Every option also resolves from a <APP_NAME>_* env var (R1.2). The
        # shared global options set explicit flat names (PLBP_OUTPUT,
        # PLBP_CONFIG); this prefix is the catch-all for any others.
        "auto_envvar_prefix": APP_NAME.upper(),
    },
)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_print_version,
    help="Show version, Python, and platform, then exit.",
)
def cli() -> None:
    """plbp — a gh-style CLI for Py.

    Commands follow a noun-verb shape, e.g. `plbp projects list`. Every command
    supports -o/--output {text,json,markdown}, --json, -v/--verbose, --no-color,
    and --config. Results go to stdout; logs and errors go to stderr.
    """


@cli.command(name="completion")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell: str) -> None:
    """Print a shell completion script.

    Examples:
        plbp completion bash >> ~/.bashrc
        eval "$(plbp completion zsh)"
    """
    comp_cls = get_completion_class(shell)
    if comp_cls is None:  # pragma: no cover - click ships all three
        raise click.ClickException(f"Unsupported shell: {shell}")
    comp: Any = comp_cls(cli, {}, _PROG_NAME, _COMPLETE_VAR)
    click.echo(comp.source())


@cli.command(name="doctor")
@click.option(
    "--bundle",
    is_flag=True,
    help="Emit a redacted diagnostics bundle to attach to bug reports.",
)
@global_options
def doctor(app: AppContext, bundle: bool) -> None:
    """Diagnose configuration and environment.

    Reports Python/platform, the resolved config file, and token status.
    Exits non-zero if any check is an error (useful in CI). Honors -o/--json.
    --bundle widens the report into a redacted snapshot (version, settings,
    app env vars with secrets masked) safe to paste into a public issue.
    """
    report = run_diagnostics(app.config)
    if bundle:
        app.renderer.render(build_bundle(app.config, report))
    else:
        app.renderer.render(report)
    if report.has_error():
        raise SystemExit(int(ExitCode.CONFIG))


for _group in COMMAND_GROUPS:
    cli.add_command(_group)


if __name__ == "__main__":
    cli()
