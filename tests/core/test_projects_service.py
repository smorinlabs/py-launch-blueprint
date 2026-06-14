"""Ring-2 use-case tests (HEX-40): inject the in-memory adapter, no network."""

import pytest

from py_launch_blueprint.core.adapters.in_memory import InMemoryProjectsRepository
from py_launch_blueprint.core.errors import ProjectNotFoundError, WorkspaceNotFoundError
from py_launch_blueprint.core.models import Project
from py_launch_blueprint.core.services.projects import ProjectsService


def _service(projects=None, workspaces=None):
    repo = InMemoryProjectsRepository(projects=projects, workspaces=workspaces)
    return ProjectsService(repo)


def test_list_projects_returns_all():
    svc = _service(projects=[Project(id="1", name="A", workspace="WS")])
    assert [p.id for p in svc.list_projects()] == ["1"]


def test_list_projects_filters_by_workspace():
    projects = [
        Project(id="1", name="A", workspace="Acme"),
        Project(id="2", name="B", workspace="Other"),
    ]
    svc = _service(projects=projects, workspaces={"Acme": "g1", "Other": "g2"})
    assert [p.id for p in svc.list_projects(workspace="Acme")] == ["1"]


def test_list_projects_unknown_workspace_raises():
    svc = _service(projects=[], workspaces={})
    with pytest.raises(WorkspaceNotFoundError):
        svc.list_projects(workspace="ghost")


def test_list_projects_respects_limit():
    projects = [Project(id=str(i), name=f"p{i}") for i in range(5)]
    svc = _service(projects=projects)
    assert len(svc.list_projects(limit=2)) == 2


def test_get_project_returns_match():
    svc = _service(projects=[Project(id="1", name="A")])
    assert svc.get_project("1").name == "A"


def test_get_project_missing_raises():
    svc = _service(projects=[])
    with pytest.raises(ProjectNotFoundError):
        svc.get_project("nope")
