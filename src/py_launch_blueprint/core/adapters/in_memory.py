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

"""In-memory adapter for tests and demos (HEX-41).

A first-class :class:`ProjectsRepository` with no network, so use-case tests
inject it instead of mocking ``requests``. ``workspaces`` maps a workspace
*name* to its gid; ``Project.workspace`` carries the name, so filtering by a
resolved gid mirrors the real upstream's behaviour.
"""

from py_launch_blueprint.core.models import Project


class InMemoryProjectsRepository:
    """Non-persistent ``ProjectsRepository`` backed by lists/dicts."""

    def __init__(
        self,
        projects: list[Project] | None = None,
        workspaces: dict[str, str] | None = None,
    ) -> None:
        self._projects = list(projects or [])
        self._workspaces = dict(workspaces or {})

    def list_projects(
        self, *, workspace_gid: str | None = None, limit: int = 200
    ) -> list[Project]:
        items = self._projects
        if workspace_gid is not None:
            items = [
                p
                for p in items
                if self._workspaces.get(p.workspace or "") == workspace_gid
            ]
        return items[:limit]

    def get_project(self, project_id: str) -> Project | None:
        return next((p for p in self._projects if p.id == project_id), None)

    def resolve_workspace_gid(self, name: str) -> str | None:
        return self._workspaces.get(name)
