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

"""Projects endpoints — thin adapter over ``core.services.projects``.

Returns the same ``core.models`` objects the CLI renders, so the API and the
CLI share one data contract. Handlers are sync (``def``) because
``ProjectsService`` uses ``requests``; FastAPI runs them in its threadpool.
"""

from fastapi import APIRouter

from py_launch_blueprint.core.models import Project, ProjectList
from py_launch_blueprint.web.deps import ProjectsServiceDep

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects(
    service: ProjectsServiceDep,
    workspace: str | None = None,
    limit: int = 200,
) -> ProjectList:
    """List projects, optionally filtered by workspace name."""
    return ProjectList(projects=service.list_projects(workspace=workspace, limit=limit))


@router.get("/{project_id}")
def get_project(service: ProjectsServiceDep, project_id: str) -> Project:
    """Fetch a single project by its id."""
    return service.get_project(project_id)
