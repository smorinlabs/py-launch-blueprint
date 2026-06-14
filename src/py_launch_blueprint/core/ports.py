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

"""Driven ports for the projects capability (HEX-11).

A ``Protocol`` the application depends on; the HTTP adapter
(:class:`~py_launch_blueprint.core.adapters.py_api.PyApiProjectsRepository`)
and the in-memory fake
(:class:`~py_launch_blueprint.core.adapters.in_memory.InMemoryProjectsRepository`)
both satisfy it *structurally* — no inheritance required.

Methods are named for the domain verb and return domain models. ``None`` means
*absent* (no such id, unknown workspace name); a raised
:class:`~py_launch_blueprint.core.errors.APIError` means the upstream call
*failed*. The application service, not the adapter, decides that absence is a
user-facing error (HEX-12).
"""

from typing import Protocol

from py_launch_blueprint.core.models import Project


class ProjectsRepository(Protocol):
    """The projects upstream the application talks to."""

    def list_projects(
        self, *, workspace_gid: str | None, limit: int
    ) -> list[Project]: ...

    def get_project(self, project_id: str) -> Project | None: ...

    def resolve_workspace_gid(self, name: str) -> str | None: ...
