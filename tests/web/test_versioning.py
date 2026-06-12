"""Versioning + deprecation helpers (WEB-02)."""

from datetime import date

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from py_launch_blueprint.web.versioning import V1_PREFIX, deprecation_headers


def test_v1_prefix_value():
    assert V1_PREFIX == "/v1"


def test_deprecation_headers_dependency():
    app = FastAPI()

    @app.get(
        "/legacy",
        deprecated=True,
        dependencies=[Depends(deprecation_headers(date(2027, 1, 1)))],
    )
    def legacy():
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/legacy")
        assert response.status_code == 200
        assert response.headers["deprecation"] == "true"
        assert response.headers["sunset"] == "Fri, 01 Jan 2027 00:00:00 GMT"
        spec = client.get("/openapi.json").json()
        assert spec["paths"]["/legacy"]["get"]["deprecated"] is True
