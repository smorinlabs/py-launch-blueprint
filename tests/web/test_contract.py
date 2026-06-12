"""Schemathesis contract fuzzing straight from the OpenAPI schema (WEB-50).

Generates property-based test cases for every documented operation and
asserts none of them produce a 5xx. Marked ``slow`` (hypothesis generation),
so the default `pytest` run skips it; CI runs `-m ""` and `just test-web`
includes it.

Scope note: checks are limited to ``not_a_server_error`` until error
responses (401/422/...) are declared per-operation in the schema — widening
to full response-conformance checks is the natural next step.
"""

import pytest
import schemathesis
from hypothesis import settings as hypothesis_settings
from schemathesis.checks import not_a_server_error

from py_launch_blueprint.web.app import create_app
from py_launch_blueprint.web.settings import WebSettings

schema = schemathesis.openapi.from_asgi(
    "/openapi.json", create_app(WebSettings.model_construct())
)


@pytest.mark.slow
@schema.parametrize()
@hypothesis_settings(max_examples=10, deadline=None)
def test_no_server_errors(case):
    case.call_and_validate(checks=(not_a_server_error,))
