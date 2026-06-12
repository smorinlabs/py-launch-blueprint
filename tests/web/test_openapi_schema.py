"""WL-026 — the committed OpenAPI contract must match the live app.

``docs/api/openapi.json`` is the API's reviewable contract. If this test
fails, the web layer changed shape without the contract being regenerated:

    just export-openapi

then review the JSON diff — that diff IS the API change.
"""

import json
from pathlib import Path

from py_launch_blueprint.web.openapi import build_openapi_schema

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"


def test_committed_schema_matches_live_app():
    committed = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert committed == build_openapi_schema(), (
        "docs/api/openapi.json is stale — run `just export-openapi` and commit "
        "the regenerated contract"
    )
