"""Web layer tests: app factory, error mapping, and the projects router.

Uses ``dependency_overrides`` for the projects service so nothing touches the
network (keeps these out of the ``live`` marker).
"""

import pytest
from fastapi.testclient import TestClient

from py_launch_blueprint import __version__
from py_launch_blueprint.core.errors import APIError
from py_launch_blueprint.core.models import Project
from py_launch_blueprint.web.app import create_app
from py_launch_blueprint.web.deps import get_projects_service


class FakeProjectsService:
    """In-memory stand-in for ProjectsService (no network)."""

    def list_projects(self, workspace=None, limit=200):
        return [Project(id="1", name="alpha", workspace="w1")]

    def get_project(self, project_id):
        if project_id == "missing":
            raise APIError(f"Project not found: {project_id}")
        return Project(id=project_id, name="alpha", workspace="w1")


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    app = create_app()
    app.dependency_overrides[get_projects_service] = FakeProjectsService
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def tokenless_client(monkeypatch):
    """An app with NO service override and no token: exercises real deps."""
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    with TestClient(create_app()) as test_client:
        yield test_client


def test_healthz_reports_version(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_request_id_is_echoed(client):
    response = client.get("/healthz", headers={"x-request-id": "abc123"})
    assert response.headers["x-request-id"] == "abc123"


def test_request_id_is_generated_when_absent(client):
    response = client.get("/healthz")
    assert response.headers["x-request-id"]


def test_readyz_returns_doctor_report(client):
    response = client.get("/readyz")
    # Missing token/config are warnings, not errors, so readiness holds.
    assert response.status_code == 200
    checks = {c["name"] for c in response.json()["checks"]}
    assert {"python", "platform", "token"} <= checks


def test_list_projects(client):
    response = client.get("/projects")
    assert response.status_code == 200
    assert response.json() == {
        "projects": [{"id": "1", "name": "alpha", "workspace": "w1"}]
    }


def test_get_project(client):
    response = client.get("/projects/42")
    assert response.status_code == 200
    assert response.json()["id"] == "42"


def test_api_error_maps_to_502(client):
    response = client.get("/projects/missing")
    assert response.status_code == 502
    assert "Project not found" in response.json()["error"]


def test_missing_token_maps_to_401(tokenless_client):
    response = tokenless_client.get("/projects")
    assert response.status_code == 401
    assert "token" in response.json()["error"]
