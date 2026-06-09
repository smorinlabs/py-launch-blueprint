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

from pydantic import BaseModel


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
