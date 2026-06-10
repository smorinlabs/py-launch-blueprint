"""Per-field manifest-drift coverage (P01-B).

The drift checker must flag a file that contains an identity value which is not
listed under THAT value's own ``[[replace]]`` block. The flat-union predecessor
passed such a file (it was covered under *some* other field) and a fork would
then ship half-renamed — e.g. a file under ``app_name`` but not
``app_name_upper`` keeps a literal ``PLBP`` after init.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_INIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_INIT))
sys.path.insert(0, str(_INIT / "ci"))

_spec = importlib.util.spec_from_file_location(
    "check_manifest_drift", _INIT / "ci" / "check_manifest_drift.py"
)
assert _spec and _spec.loader
drift = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(drift)

from common import Manifest, ReplaceOp  # noqa: E402

ROOT = drift.REPO_ROOT


def _p(rel: str) -> Path:
    return (ROOT / rel).resolve()


def test_covered_by_value_is_per_value() -> None:
    # a.py is listed under app_name (plbp) and app_name_upper (PLBP);
    # b.py only under app_name.
    m = Manifest(
        replaces=(
            ReplaceOp(
                field="app_name", current=("plbp",), files=("a.py", "b.py"), mode="text"
            ),
            ReplaceOp(
                field="app_name_upper", current=("PLBP",), files=("a.py",), mode="text"
            ),
        )
    )
    cov = drift.covered_by_value(m)
    assert cov["plbp"] == {_p("a.py"), _p("b.py")}
    assert cov["PLBP"] == {_p("a.py")}  # b.py is NOT covered for PLBP


def test_half_covered_file_is_flagged() -> None:
    # The regression: b.py contains both `plbp` and `PLBP` but is only covered
    # for `plbp`. The uppercase env-prefix would survive a rebrand.
    coverage = {"plbp": {_p("b.py")}}  # PLBP intentionally uncovered for b.py
    text = "cmd = plbp\nenv = PLBP_TOKEN\n"
    assert drift.uncovered_values(text, _p("b.py"), coverage) == ["PLBP"]


def test_fully_covered_file_has_no_leak() -> None:
    coverage = {"plbp": {_p("a.py")}, "PLBP": {_p("a.py")}}
    assert drift.uncovered_values("plbp / PLBP", _p("a.py"), coverage) == []


def test_value_absent_from_file_is_not_flagged() -> None:
    # No coverage for PLBP at all, but the file doesn't contain it → no leak.
    assert (
        drift.uncovered_values("just plbp here", _p("a.py"), {"plbp": {_p("a.py")}})
        == []
    )


def test_committed_manifest_is_per_field_clean() -> None:
    # The live manifest must pass the per-field check (guards against a future
    # edit that adds an identity value without per-field coverage).
    assert drift.main() == 0
