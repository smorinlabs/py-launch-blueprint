"""Tests for the web logging profile (WEB-12).

The full pipeline is exercised end-to-end: ``create_app()`` configures the
shared structlog pipeline from ``WebSettings`` (JSON to stderr by default),
so assertions parse the JSONL that lands on captured stderr.
"""

import json
import logging

import pytest
from fastapi.testclient import TestClient

from py_launch_blueprint.web.app import create_app
from py_launch_blueprint.web.settings import WebSettings


def make_client(**settings_overrides):
    settings = WebSettings.model_construct(**settings_overrides)
    return TestClient(create_app(settings), raise_server_exceptions=False)


def stderr_events(capsys, event: str) -> list[dict]:
    """Parse captured stderr as JSONL and return entries for one event."""
    entries = []
    for line in capsys.readouterr().err.strip().splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("event") == event:
            entries.append(payload)
    return entries


@pytest.fixture(autouse=True)
def _no_ambient_token(monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)


# NOTE: clients are built INSIDE each test (not in a fixture) so the stderr
# handler created by configure_web_logging binds capsys' replaced stream.


def test_access_event_shape(capsys):
    # One canonical http_request event per request, with the route template,
    # status, and duration — the WEB-12 wide event.
    with make_client() as client:
        response = client.get("/v1/projects")
    events = stderr_events(capsys, "http_request")
    assert len(events) == 1
    event = events[0]
    assert event["method"] == "GET"
    assert event["route"] == "/v1/projects"
    assert event["status"] == response.status_code
    assert isinstance(event["duration_ms"], float)
    assert event["level"] == "info"
    assert event["logger"] == "py_launch_blueprint.web.middleware"


def test_unmatched_route_logs_none(capsys):
    # 404s must not leak raw URLs into `route` — it is the
    # bounded-cardinality field; the raw URL stays in `path`.
    with make_client() as client:
        client.get("/no/such/route-12345")
    (event,) = stderr_events(capsys, "http_request")
    assert event["route"] is None
    assert event["path"] == "/no/such/route-12345"
    assert event["status"] == 404


def test_access_event_carries_request_id(capsys):
    with make_client() as client:
        response = client.get("/v1/projects", headers={"x-request-id": "rid-123"})
    assert response.headers["x-request-id"] == "rid-123"
    (event,) = stderr_events(capsys, "http_request")
    assert event["request_id"] == "rid-123"


def test_probe_endpoints_not_access_logged(capsys):
    # /v1/projects in the same session proves capture works; the probes must
    # be the only requests missing from the access log.
    with make_client() as client:
        client.get("/healthz")
        client.get("/readyz")
        client.get("/v1/projects")
    events = stderr_events(capsys, "http_request")
    assert [e["path"] for e in events] == ["/v1/projects"]


def test_unhandled_error_returns_problem_and_logs(capsys):
    # The catch-all handler: structured traceback in the logs, generic RFC
    # 9457 document (no internals) to the client.
    app = create_app(WebSettings.model_construct())

    @app.get("/boom")
    async def boom():
        raise RuntimeError("kaboom-internal-detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["title"] == "Internal Server Error"
    assert "kaboom-internal-detail" not in response.text
    (event,) = stderr_events(capsys, "unhandled_error")
    assert "kaboom-internal-detail" in event["exception"]
    assert "request_id" in event


def test_log_level_setting_filters(capsys):
    # log_level=warning silences the INFO-level access event.
    with make_client(log_level="warning") as client:
        client.get("/v1/projects")
    assert stderr_events(capsys, "http_request") == []


def test_uvicorn_loggers_adopted():
    # web/logging.py folds uvicorn into the root pipeline: lifecycle loggers
    # propagate (structured output), the bespoke access line is silenced.
    with make_client():
        pass
    for name in ("uvicorn", "uvicorn.error"):
        assert logging.getLogger(name).handlers == []
        assert logging.getLogger(name).propagate is True
    access = logging.getLogger("uvicorn.access")
    assert access.handlers == []
    assert access.propagate is False


def test_log_settings_resolve_from_env(monkeypatch):
    monkeypatch.setenv("PLBP_WEB_LOG_LEVEL", "debug")
    monkeypatch.setenv("PLBP_WEB_LOG_FORMAT", "console")
    settings = WebSettings()
    assert settings.log_level == "debug"
    assert settings.log_format == "console"
