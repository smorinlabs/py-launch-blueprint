"""Property-based round-trip tests (WL-013).

Example-based tests check the cases we thought of; these check a *property* of
every input Hypothesis can generate, at the two seams where a silent
serialization bug would be costly: the domain model's JSON wire form and the
config file's persist→reload cycle. Reaching into a private reader
(``_read_toml``) is the documented test exemption (HEX-35).
"""

from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from py_launch_blueprint.core.config import _read_toml, write_config_data
from py_launch_blueprint.core.models import Project

# Real-world-ish text: any unicode except surrogates (not valid UTF-8) and
# control chars — so the property is about *our* round-trip, not the encoder's
# escaping minutiae. Identifiers/names/config values don't carry control chars.
_text = st.text(st.characters(exclude_categories=("Cs", "Cc")), max_size=60)


@given(pid=_text, name=_text, workspace=st.none() | _text)
def test_project_survives_json_round_trip(pid: str, name: str, workspace: str | None):
    """Every Project re-parses from its own JSON unchanged (the wire contract)."""
    project = Project(id=pid, name=name, workspace=workspace)
    assert Project.model_validate_json(project.model_dump_json()) == project


# Config is section-tables of scalars. int bounded to TOML's 64-bit range;
# keys are identifier-shaped, as the real schema's keys are.
_key = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
    min_size=1,
    max_size=24,
)
_scalar = st.booleans() | st.integers(-(2**63), 2**63 - 1) | _text
_config_data = st.dictionaries(
    keys=_key,
    values=st.dictionaries(keys=_key, values=_scalar, max_size=6),
    max_size=6,
)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=_config_data)
def test_config_write_read_round_trips(tmp_path: Path, data: dict):
    """write_config_data always emits TOML that _read_toml reads back identically.

    `tmp_path` is reused across examples, but each example fully overwrites the
    file atomically and reads its own data back — no cross-example leakage —
    hence the function-scoped-fixture health check is suppressed deliberately.
    """
    target = tmp_path / "plbp_config.toml"
    write_config_data(target, data)
    assert _read_toml(target) == data
