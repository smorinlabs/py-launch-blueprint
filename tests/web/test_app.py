"""Web layer tests: app factory, problem envelope, middleware, and routers.

Uses ``dependency_overrides`` for the projects service so nothing touches the
network (keeps these out of the ``live`` marker). Apps are built with
``WebSettings.model_construct()`` (pure defaults, no env) unless a test is
specifically about settings.
"""

import pytest
from fastapi.testclient import TestClient

from py_launch_blueprint import __version__
from py_launch_blueprint.core.errors import APIError
from py_launch_blueprint.core.models import Project
from py_launch_blueprint.web.app import create_app
from py_launch_blueprint.web.deps import get_projects_service
from py_launch_blueprint.web.settings import WebSettings

PROBLEM_TYPE = "application/problem+json"


class FakeProjectsService:
    """In-memory stand-in for ProjectsService (no network)."""

    def list_projects(self, workspace=None, limit=200):
        return [Project(id="1", name="alpha", workspace="w1")]

    def get_project(self, project_id):
        if project_id == "missing":
            raise APIError(f"Project not found: {project_id}")
        return Project(id=project_id, name="alpha", workspace="w1")


def make_client(settings=None, override=True):
    app = create_app(settings or WebSettings.model_construct())
    if override:
        app.dependency_overrides[get_projects_service] = FakeProjectsService
    return TestClient(app)


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    with make_client() as test_client:
        yield test_client


@pytest.fixture()
def tokenless_client(monkeypatch):
    """An app with NO service override and no token: exercises real deps."""
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    with make_client(override=False) as test_client:
        yield test_client


# --- ops endpoints -----------------------------------------------------------


def test_healthz_reports_version(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert "python" in body


def test_readyz_returns_doctor_report(client):
    response = client.get("/readyz")
    # Missing token/config are warnings, not errors, so readiness holds.
    assert response.status_code == 200
    checks = {c["name"] for c in response.json()["checks"]}
    assert {"python", "platform", "token"} <= checks


def test_metrics_exposed_by_default(client):
    client.get("/healthz")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_request" in response.text


def test_metrics_can_be_disabled(monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    settings = WebSettings.model_construct(metrics_enabled=False)
    with make_client(settings) as test_client:
        assert test_client.get("/metrics").status_code == 404


# --- middleware --------------------------------------------------------------


def test_request_id_is_echoed(client):
    response = client.get("/healthz", headers={"x-request-id": "abc123"})
    assert response.headers["x-request-id"] == "abc123"


def test_request_id_is_generated_when_absent(client):
    assert client.get("/healthz").headers["x-request-id"]


def test_security_headers_present(client):
    headers = client.get("/healthz").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "max-age" in headers["strict-transport-security"]


def test_cors_off_by_default(client):
    response = client.get("/healthz", headers={"origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_enabled_via_settings(monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    settings = WebSettings.model_construct(cors_origins=["https://app.example"])
    with make_client(settings) as test_client:
        response = test_client.get(
            "/healthz", headers={"origin": "https://app.example"}
        )
        assert response.headers["access-control-allow-origin"] == (
            "https://app.example"
        )


# --- projects router (under /v1) ---------------------------------------------


def test_list_projects_paginated(client):
    response = client.get("/v1/projects")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == [{"id": "1", "name": "alpha", "workspace": "w1"}]
    assert body["total"] == 1
    assert body["page"] == 1


def test_pagination_params_validated(client):
    response = client.get("/v1/projects", params={"page": 0})
    assert response.status_code == 422
    assert response.headers["content-type"] == PROBLEM_TYPE


def test_get_project(client):
    response = client.get("/v1/projects/42")
    assert response.status_code == 200
    assert response.json()["id"] == "42"


def test_old_unversioned_path_is_gone(client):
    assert client.get("/projects").status_code == 404


# --- problem details envelope (WEB-01) ----------------------------------------


def test_api_error_maps_to_502_problem(client):
    response = client.get("/v1/projects/missing")
    assert response.status_code == 502
    assert response.headers["content-type"] == PROBLEM_TYPE
    body = response.json()
    assert body["status"] == 502
    assert body["instance"] == "/v1/projects/missing"
    assert "Project not found" in body["detail"]


def test_missing_token_maps_to_401_problem(tokenless_client):
    response = tokenless_client.get("/v1/projects")
    assert response.status_code == 401
    assert response.headers["content-type"] == PROBLEM_TYPE
    assert "token" in response.json()["detail"]


def test_404_is_a_problem(client):
    response = client.get("/no/such/route")
    assert response.status_code == 404
    assert response.headers["content-type"] == PROBLEM_TYPE
    assert response.json()["title"] == "Not Found"


def test_validation_error_is_a_problem_with_errors(client):
    response = client.get("/v1/projects", params={"size": "not-a-number"})
    assert response.status_code == 422
    assert response.headers["content-type"] == PROBLEM_TYPE
    body = response.json()
    assert body["title"] == "Validation Error"
    assert isinstance(body["errors"], list) and body["errors"]


# --- rate limiting (WEB-22) ---------------------------------------------------


def test_rate_limit_disabled_by_default(client):
    for _ in range(30):
        assert client.get("/healthz").status_code == 200


def test_rate_limit_429_problem(monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    settings = WebSettings.model_construct(rate_limit="2/minute")
    with make_client(settings) as test_client:
        assert test_client.get("/healthz").status_code == 200
        assert test_client.get("/healthz").status_code == 200
        response = test_client.get("/healthz")
        assert response.status_code == 429
        assert response.headers["content-type"] == PROBLEM_TYPE
        # Computed by slowapi (headers_enabled), not hard-coded.
        assert int(response.headers["retry-after"]) >= 0
        assert "x-ratelimit-limit" in response.headers
        assert response.json()["title"] == "Too Many Requests"
        # Short-circuited responses still pass through the outermost
        # middleware: request id + security headers must be present.
        assert response.headers["x-request-id"]
        assert response.headers["x-content-type-options"] == "nosniff"


def test_cors_preflight_gets_request_id_and_security_headers(monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    settings = WebSettings.model_construct(cors_origins=["https://app.example"])
    with make_client(settings) as test_client:
        response = test_client.options(
            "/v1/projects",
            headers={
                "origin": "https://app.example",
                "access-control-request-method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["x-request-id"]
        assert response.headers["x-content-type-options"] == "nosniff"


def test_readyz_failure_is_a_problem_with_diagnostics(client, monkeypatch):
    from py_launch_blueprint.core.models import DoctorCheck, DoctorReport
    from py_launch_blueprint.web import app as app_module

    failing = DoctorReport(
        checks=[DoctorCheck(name="python", status="error", detail="boom")]
    )
    monkeypatch.setattr(app_module, "run_diagnostics", lambda _config: failing)
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.headers["content-type"] == PROBLEM_TYPE
    body = response.json()
    assert body["title"] == "Service Unavailable"
    assert body["diagnostics"]["checks"][0]["name"] == "python"


# --- OpenAPI polish (WEB-04) --------------------------------------------------


def test_operation_ids_are_tag_prefixed(client):
    spec = client.get("/openapi.json").json()
    ops = {
        op["operationId"]
        for methods in spec["paths"].values()
        for op in methods.values()
    }
    assert "projects-list_projects" in ops
    assert "projects-get_project" in ops
    assert "ops-healthz" in ops


def test_metrics_not_in_schema(client):
    assert "/metrics" not in client.get("/openapi.json").json()["paths"]


def test_422_documented_as_problem_json(client):
    spec = client.get("/openapi.json").json()
    listing = spec["paths"]["/v1/projects"]["get"]["responses"]["422"]
    assert list(listing["content"]) == [PROBLEM_TYPE]
    assert listing["content"][PROBLEM_TYPE]["schema"]["$ref"].endswith("/Problem")
    assert "Problem" in spec["components"]["schemas"]
    # FastAPI's default validation schemas must not linger unreferenced.
    assert "HTTPValidationError" not in spec["components"]["schemas"]
