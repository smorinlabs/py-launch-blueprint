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

"""Projects use-cases (HEX-12).

Orchestration only: depends on a :class:`ProjectsRepository` port, decides that
absence is a user-facing error, and returns domain models. No HTTP, no Click,
no FastAPI — the transport lives in
:mod:`py_launch_blueprint.core.adapters.py_api`, and the front-ends build a
wired instance via :func:`py_launch_blueprint.composition.build_projects_service`.
"""

from py_launch_blueprint.core.errors import ProjectNotFoundError, WorkspaceNotFoundError
from py_launch_blueprint.core.models import Project
from py_launch_blueprint.core.ports import ProjectsRepository


class ProjectsService:
    """Application service coordinating a ``ProjectsRepository``."""

    def __init__(self, repository: ProjectsRepository) -> None:
        self._repo = repository

    def list_projects(
        self, workspace: str | None = None, limit: int = 200
    ) -> list[Project]:
        """List projects, optionally filtered by workspace name.

        Raises :class:`WorkspaceNotFoundError` when a workspace name cannot be
        resolved — the absence the repository reports as ``None`` becomes a
        user-facing error here, not in the adapter.
        """
        workspace_gid: str | None = None
        if workspace:
            workspace_gid = self._repo.resolve_workspace_gid(workspace)
            if workspace_gid is None:
                raise WorkspaceNotFoundError(f"Workspace not found: {workspace}")
        return self._repo.list_projects(workspace_gid=workspace_gid, limit=limit)

    def get_project(self, project_id: str) -> Project:
        """Fetch a single project by its gid.

        Raises :class:`ProjectNotFoundError` when the repository reports absence.
        """
        project = self._repo.get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project not found: {project_id}")
        return project
