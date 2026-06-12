"""Golden snapshots of every command's --help output (WL-023).

A renamed flag, reworded help line, or dropped command shows up as a reviewable
snapshot diff in the PR instead of silently changing the CLI's UX. After an
intentional change, regenerate with:

    uv run pytest tests/cli/test_help_snapshots.py --snapshot-update
"""

import click
import pytest
from click.testing import CliRunner

from py_launch_blueprint.cli.main import cli


def _walk(cmd: click.Command, path: tuple[str, ...]):
    """Yield the argv path of ``cmd`` and (depth-first) every subcommand."""
    yield path
    if isinstance(cmd, click.Group):
        for name in sorted(cmd.commands):
            yield from _walk(cmd.commands[name], (*path, name))


ALL_COMMANDS = list(_walk(cli, ()))


@pytest.mark.parametrize("path", ALL_COMMANDS, ids=lambda p: " ".join(("plbp", *p)))
def test_help_snapshot(path, snapshot, monkeypatch):
    """Each command's --help output must match its committed golden snapshot."""
    # Click wraps help text to the terminal width (shutil.get_terminal_size
    # honors COLUMNS) — pin it so snapshots match across local shells and CI.
    monkeypatch.setenv("COLUMNS", "80")
    result = CliRunner().invoke(cli, [*path, "--help"])
    assert result.exit_code == 0, result.output
    assert result.output == snapshot
