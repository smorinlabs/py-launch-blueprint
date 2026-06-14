"""Port-contract substitutability suite (HEX-40, ring 3).

One set of behavioural assertions run against *both* adapters that satisfy
``ProjectsRepository`` — the in-memory fake and the real HTTP adapter (its
network mocked with ``responses``) — seeded from the *same* canonical data.
If the two ever diverge (a fake that lies, or a real adapter that drifts), a
row here goes red, which is what makes the fake trustworthy as the substitute
the ring-2 service tests depend on.

The real adapter filters/limits server-side (query params), so the mock mirrors
that: the callback honours ``workspace`` and ``limit`` exactly as the upstream
would, keeping the contract about the *adapter*, not the mock.
"""

import json
import re
from collections.abc import Iterator
from urllib.parse import parse_qs, urlparse

import pytest
import responses

from py_launch_blueprint.core.adapters.in_memory import InMemoryProjectsRepository
from py_launch_blueprint.core.adapters.py_api import PyApiProjectsRepository
from py_launch_blueprint.core.models import Project
from py_launch_blueprint.core.ports import ProjectsRepository

# --- canonical seed data (expressed once, shared by both adapters) -----------

_WORKSPACES = {"Acme": "ws-1", "Other": "ws-2"}
_PROJECTS = [
    Project(id="1", name="Alpha", workspace="Acme"),
    Project(id="2", name="Beta", workspace="Other"),
]
_GID_TO_PROJECTS: dict[str, list[Project]] = {}
for _p in _PROJECTS:
    _GID_TO_PROJECTS.setdefault(_WORKSPACES[_p.workspace or ""], []).append(_p)


# --- the real adapter's upstream, faked at the HTTP boundary -----------------


def _api_project(p: Project) -> dict:
    ws = {"name": p.workspace} if p.workspace else {}
    return {"gid": p.id, "name": p.name, "workspace": ws}


def _workspaces_cb(request) -> tuple[int, dict, str]:
    data = [{"gid": gid, "name": name} for name, gid in _WORKSPACES.items()]
    return 200, {}, json.dumps({"data": data})


def _projects_cb(request) -> tuple[int, dict, str]:
    qs = parse_qs(urlparse(request.url).query)
    gid = qs.get("workspace", [None])[0]
    limit = int(qs.get("limit", ["200"])[0])
    items = _GID_TO_PROJECTS.get(gid, []) if gid else list(_PROJECTS)
    body = [_api_project(p) for p in items[:limit]]
    return 200, {}, json.dumps({"data": body})


def _project_by_id_cb(request) -> tuple[int, dict, str]:
    pid = urlparse(request.url).path.rsplit("/", 1)[-1]
    match = next((p for p in _PROJECTS if p.id == pid), None)
    if match is None:
        return 404, {}, json.dumps({"errors": [{"message": "not found"}]})
    return 200, {}, json.dumps({"data": _api_project(match)})


@pytest.fixture(params=["in_memory", "py_api"])
def repo(request: pytest.FixtureRequest) -> Iterator[ProjectsRepository]:
    """Yield each adapter, both seeded from the canonical data above."""
    if request.param == "in_memory":
        yield InMemoryProjectsRepository(
            projects=list(_PROJECTS), workspaces=dict(_WORKSPACES)
        )
        return
    base = PyApiProjectsRepository.BASE_URL
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add_callback(responses.GET, f"{base}/workspaces", callback=_workspaces_cb)
        rsps.add_callback(responses.GET, f"{base}/projects", callback=_projects_cb)
        rsps.add_callback(
            responses.GET,
            re.compile(rf"{re.escape(base)}/projects/[^/?]+"),
            callback=_project_by_id_cb,
        )
        yield PyApiProjectsRepository(token="test-token")


# --- the contract every ProjectsRepository must satisfy ----------------------


def test_resolve_known_workspace(repo: ProjectsRepository):
    assert repo.resolve_workspace_gid("Acme") == "ws-1"


def test_resolve_workspace_is_case_insensitive(repo: ProjectsRepository):
    assert repo.resolve_workspace_gid("acme") == "ws-1"


def test_resolve_unknown_workspace_is_none(repo: ProjectsRepository):
    assert repo.resolve_workspace_gid("ghost") is None


def test_list_returns_all_projects(repo: ProjectsRepository):
    got = repo.list_projects(workspace_gid=None, limit=200)
    assert {p.id for p in got} == {"1", "2"}


def test_list_filters_by_workspace_gid(repo: ProjectsRepository):
    got = repo.list_projects(workspace_gid="ws-1", limit=200)
    assert [p.id for p in got] == ["1"]


def test_list_honors_limit(repo: ProjectsRepository):
    assert len(repo.list_projects(workspace_gid=None, limit=1)) == 1


def test_get_known_project_maps_fields(repo: ProjectsRepository):
    project = repo.get_project("1")
    assert project is not None
    assert (project.id, project.name, project.workspace) == ("1", "Alpha", "Acme")


def test_get_missing_project_is_none(repo: ProjectsRepository):
    assert repo.get_project("missing") is None
