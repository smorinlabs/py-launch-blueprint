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

"""The output contract: render any result as text / JSON / Markdown.

Rules (per clig.dev):

* **Results** go to **stdout** (pipe-friendly).
* **Messages, prompts, errors** go to **stderr**.
* JSON mode emits clean, parseable stdout with no color codes — including for
  errors, which become a structured ``{"error": {...}}`` object on stderr.
"""

import json
from enum import StrEnum
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from py_launch_blueprint.core.errors import ExitCode
from py_launch_blueprint.core.models import CLIResult


class OutputMode(StrEnum):
    """Supported output formats. Every command honors all three."""

    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


def _console_color_args(color: str) -> tuple[bool | None, bool | None]:
    """Map a resolved color mode to rich's ``(no_color, force_terminal)``.

    ``auto`` leaves both unset so rich detects the TTY itself.
    """
    if color == "never":
        return True, None
    if color == "always":
        return None, True
    return None, None


class Renderer:
    """Renders results and messages according to the selected output mode.

    ``color`` is the *resolved* mode (flag > NO_COLOR env > config > auto —
    see ``context._resolve_color``). ``output_file`` redirects **results** to
    a file (R4); messages and errors stay on stderr either way.
    """

    def __init__(
        self,
        mode: OutputMode,
        no_color: bool = False,
        color: str | None = None,
        output_file: str | None = None,
    ) -> None:
        self.mode = mode
        self.color = color or ("never" if no_color else "auto")
        self.output_file = Path(output_file) if output_file else None
        nc, force = _console_color_args(self.color)
        # stdout console for results; stderr console for everything else.
        self.out = Console(highlight=False, no_color=nc, force_terminal=force)
        self.err = Console(
            stderr=True, highlight=False, no_color=nc, force_terminal=force
        )

    # -- results (stdout, or --output-file) --------------------------------

    def render(self, result: CLIResult) -> None:
        """Write a command result in the active mode (stdout or the file)."""
        if self.output_file:
            self._render_to_file(result)
            return
        if self.mode is OutputMode.JSON:
            click.echo(result.model_dump_json(indent=2))
        elif self.mode is OutputMode.MARKDOWN:
            click.echo(self._to_markdown(result))
        else:
            self._render_text(result, self.out)

    def _render_to_file(self, result: CLIResult) -> None:
        """R4: --output-file changes the destination, never the format."""
        if self.output_file is None:  # pragma: no cover — guarded by render()
            return
        with self.output_file.open("w", encoding="utf-8") as handle:
            if self.mode is OutputMode.JSON:
                handle.write(result.model_dump_json(indent=2) + "\n")
            elif self.mode is OutputMode.MARKDOWN:
                handle.write(self._to_markdown(result) + "\n")
            else:
                # A file is not a TTY: color only if explicitly "always".
                file_console = Console(
                    file=handle,
                    highlight=False,
                    force_terminal=(self.color == "always"),
                    no_color=(self.color != "always"),
                )
                self._render_text(result, file_console)

    def _render_text(self, result: CLIResult, console: Console) -> None:
        columns = result.table_columns()
        if not columns or not result.table_rows():
            note = result.human_note()
            if note:
                console.print(note)
            return
        title = result.table_title()
        table = Table(title=title, show_header=True, header_style="bold cyan")
        for column in columns:
            table.add_column(column)
        for row in result.table_rows():
            table.add_row(*row)
        console.print(table)

    @staticmethod
    def _to_markdown(result: CLIResult) -> str:
        columns = result.table_columns()
        if not columns or not result.table_rows():
            return result.human_note() or ""
        lines: list[str] = []
        title = result.table_title()
        if title:
            lines.append(f"## {title}")
            lines.append("")
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("| " + " | ".join("---" for _ in columns) + " |")
        for row in result.table_rows():
            cells = [cell.replace("|", "\\|") for cell in row]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)

    # -- messages & errors (stderr) ---------------------------------------

    def message(self, text: str) -> None:
        """Informational message to stderr (suppressed in JSON mode)."""
        if self.mode is OutputMode.JSON:
            return
        self.err.print(text)

    def error(self, message: str, code: ExitCode = ExitCode.API) -> None:
        """Report an error to stderr in a mode-appropriate way."""
        if self.mode is OutputMode.JSON:
            payload = {
                "error": {"code": int(code), "name": code.name, "message": message}
            }
            click.echo(json.dumps(payload), err=True)
        else:
            self.err.print(f"[red]Error:[/red] {message}")
