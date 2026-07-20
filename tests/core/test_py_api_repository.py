"""Adapter boundary tests (HEX-40, ring 4): raw API JSON -> domain Project.

P04: the adapter validates upstream payloads at the *edge* rather than mapping
them with silent defaults. The tests come in two halves — the mapping still
maps (nothing about the happy path changes), and schema drift now raises
``APIError`` instead of yielding an empty-id ``Project`` or an empty list that
reads to the user as "no projects found".
"""

import pytest
import responses
from pydantic import ValidationError

from py_launch_blueprint.core.adapters.py_api import (
    PyApiProjectsRepository,
    _ProjectPayload,
)
from py_launch_blueprint.core.errors import APIError

BASE = PyApiProjectsRepository.BASE_URL

# A credential-shaped *field* planted in a payload to prove its value never
# reaches the error message or the log. The value itself is deliberately not
# key-shaped: a realistic-looking fake trips the repo's gitleaks hook, and a
# scanner that could tell fake from real would be a scanner that misses real ones.
CANARY = "canary-must-not-appear-in-logs"


def _repo() -> PyApiProjectsRepository:
    return PyApiProjectsRepository(token="test-token")


# --- mapping: validated payload -> domain Project ----------------------------


def test_maps_gid_name_and_workspace():
    payload = _ProjectPayload.model_validate(
        {"gid": "123", "name": "Proj", "workspace": {"name": "WS"}}
    )
    project = PyApiProjectsRepository._to_project(payload)
    assert (project.id, project.name, project.workspace) == ("123", "Proj", "WS")


def test_falls_back_to_id_when_gid_absent():
    """The ``gid``-or-``id`` fallback is declared, not buried in a .get() chain."""
    payload = _ProjectPayload.model_validate({"id": "7", "name": "X"})
    assert PyApiProjectsRepository._to_project(payload).id == "7"


def test_numeric_gid_is_coerced_to_str():
    """Preserves the intent of the old ``str(item.get("gid", ...))``."""
    payload = _ProjectPayload.model_validate({"gid": 123, "name": "X"})
    assert PyApiProjectsRepository._to_project(payload).id == "123"


@pytest.mark.parametrize("empty", [{}, None])
def test_empty_workspace_is_treated_as_absent(empty):
    """Lenient on empty: mirrors the old ``item.get("workspace") or {}``."""
    payload = _ProjectPayload.model_validate(
        {"gid": "1", "name": "X", "workspace": empty}
    )
    assert PyApiProjectsRepository._to_project(payload).workspace is None


def test_missing_workspace_key_is_absent():
    payload = _ProjectPayload.model_validate({"gid": "1", "name": "X"})
    assert PyApiProjectsRepository._to_project(payload).workspace is None


def test_present_workspace_without_a_name_is_rejected():
    """Strict on present: a typo'd key is drift, not an absent workspace."""
    with pytest.raises(ValidationError):
        _ProjectPayload.model_validate(
            {"gid": "1", "name": "X", "workspace": {"nayme": "typo"}}
        )


@pytest.mark.parametrize("wrong", ["", [], 0, False, "acme"])
def test_falsy_but_non_empty_workspace_is_drift_not_absence(wrong):
    """ "Lenient on empty" is not "lenient on anything falsy".

    ``""``/``[]``/``0``/``False`` are the wrong *type* for this field rather
    than an empty one, so they must raise instead of silently becoming None.
    """
    with pytest.raises(ValidationError):
        _ProjectPayload.model_validate({"gid": "1", "name": "X", "workspace": wrong})


def test_numeric_name_is_drift_even_though_numeric_gid_is_not():
    """The gid coercion is per-field, so it must not leak onto ``name``."""
    with pytest.raises(ValidationError):
        _ProjectPayload.model_validate({"gid": "1", "name": 12345})


def test_boolean_gid_is_drift():
    """``bool`` subclasses ``int``; it is still not a gid."""
    with pytest.raises(ValidationError):
        _ProjectPayload.model_validate({"gid": True, "name": "X"})


# --- the boundary: drift is loud ---------------------------------------------


@responses.activate
def test_valid_list_maps_every_project():
    responses.get(
        f"{BASE}/projects",
        json={
            "data": [
                {"gid": "1", "name": "Alpha", "workspace": {"name": "Acme"}},
                {"gid": "2", "name": "Beta", "workspace": {}},
            ]
        },
    )
    got = _repo().list_projects()
    assert [(p.id, p.name, p.workspace) for p in got] == [
        ("1", "Alpha", "Acme"),
        ("2", "Beta", None),
    ]


@responses.activate
def test_renamed_data_key_raises_instead_of_reading_as_no_projects():
    """The headline bug: ``.get("data", [])`` turned drift into "No projects found."."""
    responses.get(f"{BASE}/projects", json={"results": []})
    with pytest.raises(APIError):
        _repo().list_projects()


@responses.activate
def test_project_without_a_name_raises_instead_of_an_empty_name():
    responses.get(f"{BASE}/projects", json={"data": [{"gid": "1"}]})
    with pytest.raises(APIError):
        _repo().list_projects()


@responses.activate
def test_one_malformed_item_fails_the_whole_list():
    """Decided in P04: no skip-and-warn — a partial answer is a quiet lie."""
    responses.get(
        f"{BASE}/projects",
        json={"data": [{"gid": "1", "name": "Good"}, {"gid": "2"}]},
    )
    with pytest.raises(APIError) as err:
        _repo().list_projects()
    # The error must be actionable: it names the field that broke.
    assert "name" in str(err.value)


@responses.activate
def test_error_locates_the_field_without_echoing_the_payload():
    """Actionable, but not an archive: we do not control what upstream sends."""
    responses.get(
        f"{BASE}/projects",
        json={"data": [{"gid": "1", "auth_token": CANARY}, {"name": "B"}]},
    )
    with pytest.raises(APIError) as err:
        _repo().list_projects()
    message = str(err.value)
    assert "data.0.name" in message  # which record, which field
    assert "(+1 more)" in message  # the drift is systemic, not a bad row
    assert CANARY not in message  # the payload stays out of logs


@responses.activate
def test_legitimate_404_is_absence_not_an_error():
    responses.get(
        f"{BASE}/projects/missing",
        json={"errors": [{"message": "not found"}]},
        status=404,
    )
    assert _repo().get_project("missing") is None


@responses.activate
def test_malformed_200_is_an_error_not_absence():
    """The distinction the old ``return {}`` collapsed: absent vs. unintelligible."""
    responses.get(f"{BASE}/projects/1", json={"data": {"gid": "1"}})
    with pytest.raises(APIError):
        _repo().get_project("1")


@responses.activate
def test_get_project_maps_a_valid_payload():
    responses.get(
        f"{BASE}/projects/1",
        json={"data": {"gid": "1", "name": "Alpha", "workspace": {"name": "Acme"}}},
    )
    project = _repo().get_project("1")
    assert project is not None
    assert (project.id, project.name, project.workspace) == ("1", "Alpha", "Acme")


@responses.activate
def test_resolve_workspace_is_case_insensitive():
    responses.get(
        f"{BASE}/workspaces", json={"data": [{"gid": "ws-1", "name": "Acme"}]}
    )
    assert _repo().resolve_workspace_gid("acme") == "ws-1"


@responses.activate
def test_workspace_without_a_name_raises_instead_of_keyerror():
    """Was an unguarded ``w["name"]`` subscript — a KeyError escaping the adapter."""
    responses.get(f"{BASE}/workspaces", json={"data": [{"gid": "ws-1"}]})
    with pytest.raises(APIError):
        _repo().resolve_workspace_gid("Acme")


@responses.activate
def test_non_json_body_is_still_a_transport_error():
    """Validation must not swallow the pre-existing transport failure path."""
    responses.get(f"{BASE}/projects", body="<html>502 Bad Gateway</html>")
    with pytest.raises(APIError):
        _repo().list_projects()
