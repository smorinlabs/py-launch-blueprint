"""Committed OpenAPI snapshot stays in sync with the code (WEB-51).

The snapshot (docs/api/openapi.json) is the reviewable API contract: route
changes show up as a diff in the PR, and the api-contract workflow runs
oasdiff against the base branch to call out breaking changes.
"""

import json
from pathlib import Path

from py_launch_blueprint.web.app import create_app
from py_launch_blueprint.web.settings import WebSettings
from scripts.export_openapi import SNAPSHOT_VERSION

SNAPSHOT = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"


def test_openapi_snapshot_is_current():
    generated = create_app(WebSettings.model_construct()).openapi()
    # The committed snapshot pins info.version to a sentinel so it stays a pure
    # route/schema contract (see scripts/export_openapi.py); normalize the
    # runtime spec the same way before comparing. Version drift is guarded
    # separately by tests/meta/test_version_consistency.py.
    generated["info"]["version"] = SNAPSHOT_VERSION
    committed = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert generated == committed, (
        "docs/api/openapi.json is stale — run `just export-openapi` and commit"
    )
