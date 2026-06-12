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

"""Result models — the single source of truth for every command's output.

Each command returns one of these Pydantic models. The CLI renderer turns the
*same* object into human text, JSON, or Markdown; the future web service will
return it as a JSON response. Because the model is the contract, the JSON
representation of every command is defined here, in one place.

To add a new result type: subclass :class:`CLIResult` and implement
``table_columns``/``table_rows`` (used by the human and Markdown renderers).
JSON rendering is automatic via Pydantic's ``model_dump_json``.
"""

from pathlib import Path

from pydantic import BaseModel

from py_launch_blueprint.core.format import rich_link


class CLIResult(BaseModel):
    """Base class for renderable command results.

    Subclasses describe how they tabulate for the human/Markdown renderers.
    The JSON renderer ignores these helpers and serializes the model fields.
    """

    def table_title(self) -> str | None:
        """Optional heading shown above the table (human/Markdown)."""
        return None

    def table_columns(self) -> list[str]:
        """Column headers. Empty means "no table" (renderer falls back to note)."""
        return []

    def table_rows(self) -> list[list[str]]:
        """Row cells as strings, aligned with :meth:`table_columns`."""
        return []

    def table_rows_rich(self) -> list[list[str]]:
        """Row cells for the *text* renderer only — may carry rich markup.

        Override to add terminal niceties (OSC-8 hyperlinks via
        :func:`core.format.rich_link`, relative times via
        :func:`core.format.relative_time`). Defaults to :meth:`table_rows`;
        Markdown and JSON always use the plain representations.
        """
        return self.table_rows()

    def human_note(self) -> str | None:
        """Optional plain message shown when there is nothing tabular to show."""
        return None


class Project(BaseModel):
    """A single Py project."""

    id: str
    name: str
    workspace: str | None = None


class ProjectList(CLIResult):
    """A collection of projects."""

    projects: list[Project]

    def table_title(self) -> str | None:
        return f"Projects ({len(self.projects)})"

    def table_columns(self) -> list[str]:
        return ["Name", "Workspace", "ID"]

    def table_rows(self) -> list[list[str]]:
        return [[p.name, p.workspace or "-", p.id] for p in self.projects]

    def human_note(self) -> str | None:
        return "No projects found." if not self.projects else None


class ConfigValue(CLIResult):
    """A single resolved configuration value and where it came from."""

    key: str
    value: str | None = None
    source: str | None = None

    def table_columns(self) -> list[str]:
        return ["Key", "Value", "Source"]

    def table_rows(self) -> list[list[str]]:
        return [
            [self.key, self.value if self.value is not None else "", self.source or "-"]
        ]


class ConfigPath(CLIResult):
    """The location of the config file and whether it exists on disk."""

    path: str
    exists: bool

    def table_columns(self) -> list[str]:
        return ["Config path", "Exists"]

    def table_rows(self) -> list[list[str]]:
        return [[self.path, "yes" if self.exists else "no"]]

    def table_rows_rich(self) -> list[list[str]]:
        try:
            uri = Path(self.path).as_uri()
        except ValueError:  # relative path — no sensible file:// form
            return self.table_rows()
        return [[rich_link(self.path, uri), "yes" if self.exists else "no"]]


class DoctorCheck(BaseModel):
    """One diagnostic check result."""

    name: str
    status: str  # "ok" | "warn" | "error"
    detail: str


class DoctorReport(CLIResult):
    """Aggregated diagnostics for `plbp doctor`."""

    checks: list[DoctorCheck]

    def table_title(self) -> str | None:
        return "Diagnostics"

    def table_columns(self) -> list[str]:
        return ["Check", "Status", "Detail"]

    def table_rows(self) -> list[list[str]]:
        return [[c.name, c.status, c.detail] for c in self.checks]

    def has_error(self) -> bool:
        return any(c.status == "error" for c in self.checks)


class DiagnosticsBundle(CLIResult):
    """Redacted environment snapshot for bug reports (`doctor --bundle`).

    Everything a maintainer needs to reproduce a setup problem, nothing the
    user would regret pasting into a public issue: secrets are redacted at
    collection time (see ``diagnostics.build_bundle``), and log *contents*
    are deliberately excluded — only the sink path is included.
    """

    version: str
    python: str
    platform: str
    checks: list[DoctorCheck]
    settings: dict[str, dict[str, str]]
    config_path: str
    config_exists: bool
    loaded_paths: list[str]
    token_present: bool
    token_source: str | None
    env: dict[str, str]
    log_file: str

    def table_title(self) -> str | None:
        return "Diagnostics bundle"

    def table_columns(self) -> list[str]:
        return ["Field", "Value"]

    def table_rows(self) -> list[list[str]]:
        ok = sum(1 for c in self.checks if c.status == "ok")
        warn = sum(1 for c in self.checks if c.status == "warn")
        error = sum(1 for c in self.checks if c.status == "error")
        token = f"present ({self.token_source})" if self.token_present else "absent"
        return [
            ["version", self.version],
            ["python", self.python],
            ["platform", self.platform],
            ["checks", f"{ok} ok / {warn} warn / {error} error"],
            ["config path", self.config_path],
            ["config exists", "yes" if self.config_exists else "no"],
            ["loaded configs", ", ".join(self.loaded_paths) or "-"],
            ["token", token],
            ["env", ", ".join(sorted(self.env)) or "-"],
            ["log file", self.log_file],
        ]
