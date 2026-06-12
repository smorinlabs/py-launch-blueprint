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

Items are the same ``core.models.Project`` objects the CLI renders (one data
contract); the collection endpoint wraps them in the standard pagination
envelope (WEB-03: ``page``/``size`` query params, ``items``/``total`` body).
Handlers are sync (``def``) because ``ProjectsService`` uses ``requests``;
FastAPI runs them in its threadpool.
"""

from fastapi import APIRouter
from fastapi_pagination import Page, paginate

from py_launch_blueprint.core.models import Project
from py_launch_blueprint.web.deps import ProjectsServiceDep

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects(
    service: ProjectsServiceDep,
    workspace: str | None = None,
) -> Page[Project]:
    """List projects, optionally filtered by workspace name.

    Pagination window note: pages are sliced from one upstream fetch (the
    service's default limit), so ``total`` reflects the fetched window, not
    the upstream universe. True pass-through pagination needs cursor support
    in ``ProjectsService`` — deferred; see "Deliberately deferred" in
    docs/design/0002-web-api-conventions.md.
    """
    return paginate(service.list_projects(workspace=workspace))


@router.get("/{project_id}")
def get_project(service: ProjectsServiceDep, project_id: str) -> Project:
    """Fetch a single project by its id."""
    return service.get_project(project_id)
