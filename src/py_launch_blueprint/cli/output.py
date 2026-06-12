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
import os
import shlex
import subprocess  # nosec B404 — only ever runs the user's own pager
import sys
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


#: ``-F`` quit if one screen, ``-R`` pass ANSI colors, ``-X`` no screen clear.
DEFAULT_PAGER = "less -FRX"

#: True on Windows. Module-level so tests can exercise both tokenization
#: branches by monkeypatching (same pattern as ``core.paths._WINDOWS``).
_WINDOWS = sys.platform == "win32"


def _pager_argv(pager: str) -> list[str]:
    """Tokenize the pager command per-platform.

    POSIX shlex rules eat backslashes, mangling Windows paths like
    ``C:\\tools\\less.exe``. On Windows, split with ``posix=False`` (which
    preserves backslashes) and strip the surrounding quotes that mode keeps.
    Quoting is the supported spelling for a path with spaces; an unquoted
    one still tokenizes wrong, fails to launch, and falls back to plain
    output via the caller's error handling.
    """
    if not _WINDOWS:
        return shlex.split(pager)
    argv = shlex.split(pager, posix=False)
    return [
        arg[1:-1] if len(arg) >= 2 and arg[0] == arg[-1] and arg[0] in "'\"" else arg
        for arg in argv
    ]


def _resolve_pager_command() -> str:
    """Pager precedence: ``PLBP_PAGER`` > ``PAGER`` > ``less -FRX``.

    A variable that is set but empty *disables* paging (git convention) —
    only an unset variable falls through to the next layer.
    """
    for var in ("PLBP_PAGER", "PAGER"):
        if var in os.environ:
            return os.environ[var].strip()
    return DEFAULT_PAGER


def _isatty(console: Console) -> bool:
    """True when the console's underlying stream is a real TTY.

    ``Console.is_terminal`` is forced True by ``color="always"`` — right for
    styling, wrong for paging: a piped run must never block on a pager, no
    matter how color was resolved.
    """
    isatty = getattr(console.file, "isatty", None)
    if isatty is None:
        return False
    try:
        return bool(isatty())
    except ValueError:  # closed/replaced stream
        return False


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
        paging: bool = True,
    ) -> None:
        self.mode = mode
        self.color = color or ("never" if no_color else "auto")
        self.output_file = Path(output_file) if output_file else None
        self.paging = paging
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
            self._render_text_paged(result)

    def _render_text_paged(self, result: CLIResult) -> None:
        """Text mode: pipe through the user's pager when output won't fit.

        Paging happens only when results go to an interactive terminal —
        never when piped, redirected to a file, in JSON/Markdown mode, or
        under ``--no-input`` (``paging=False``). The pager resolves from
        ``PLBP_PAGER`` > ``PAGER`` > ``less -FRX``; an empty value disables.
        """
        if not (self.paging and self.out.is_terminal and _isatty(self.out)):
            self._render_text(result, self.out)
            return
        pager = _resolve_pager_command()
        if not pager:
            self._render_text(result, self.out)
            return
        with self.out.capture() as capture:
            self._render_text(result, self.out)
        text = capture.get()
        if text.count("\n") < self.out.size.height:
            self.out.file.write(text)
            self.out.file.flush()
            return
        try:
            # argv comes from the user's own PAGER environment — running it
            # is the feature, same trust model as git/less.
            subprocess.run(  # noqa: S603 # nosec B603
                _pager_argv(pager), input=text, text=True, check=False
            )
        except (OSError, ValueError):
            # Missing pager binary or unparsable command: never lose output.
            self.out.file.write(text)
            self.out.file.flush()

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
        # Rich rows may carry markup (hyperlinks, relative times); rich strips
        # the styling itself for non-terminal destinations (pipes, files).
        for row in result.table_rows_rich():
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

    def error(
        self,
        message: str,
        code: ExitCode = ExitCode.API,
        *,
        error_code: str | None = None,
        hint: str | None = None,
        traceback_path: str | None = None,
    ) -> None:
        """Report an error to stderr in a mode-appropriate way.

        ``error_code`` is the stable ``PLBP###`` string (append-only table in
        ``core/errors.py``); ``hint`` is one actionable next step;
        ``traceback_path`` points at the crash log for unexpected errors.
        The JSON ``error`` object only ever gains keys (append-only contract).
        """
        if self.mode is OutputMode.JSON:
            detail: dict[str, int | str] = {
                "code": int(code),
                "name": code.name,
                "message": message,
            }
            if error_code:
                detail["error_code"] = error_code
            if hint:
                detail["hint"] = hint
            if traceback_path:
                detail["traceback_path"] = traceback_path
            click.echo(json.dumps({"error": detail}), err=True)
        else:
            suffix = f" [dim]({error_code})[/dim]" if error_code else ""
            self.err.print(f"[red]Error:[/red] {message}{suffix}")
            if hint:
                self.err.print(f"[yellow]hint:[/yellow] {hint}")
            if traceback_path:
                self.err.print(f"full traceback: {traceback_path}")
