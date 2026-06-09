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


class Renderer:
    """Renders results and messages according to the selected output mode."""

    def __init__(self, mode: OutputMode, no_color: bool = False) -> None:
        self.mode = mode
        # stdout console for human output; stderr console for everything else.
        self.out = Console(no_color=no_color, highlight=False)
        self.err = Console(stderr=True, no_color=no_color, highlight=False)

    # -- results (stdout) --------------------------------------------------

    def render(self, result: CLIResult) -> None:
        """Write a command result to stdout in the active mode."""
        if self.mode is OutputMode.JSON:
            click.echo(result.model_dump_json(indent=2))
        elif self.mode is OutputMode.MARKDOWN:
            click.echo(self._to_markdown(result))
        else:
            self._render_text(result)

    def _render_text(self, result: CLIResult) -> None:
        columns = result.table_columns()
        if not columns or not result.table_rows():
            note = result.human_note()
            if note:
                self.out.print(note)
            return
        title = result.table_title()
        table = Table(title=title, show_header=True, header_style="bold cyan")
        for column in columns:
            table.add_column(column)
        for row in result.table_rows():
            table.add_row(*row)
        self.out.print(table)

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
