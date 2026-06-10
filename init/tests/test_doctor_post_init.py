"""Tests for init_doctor.py's new post_init check class.

Each test sets up a tmp fixture with a known marker + workflow layout, then
calls the individual check functions and asserts the resulting Finding.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

INIT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(INIT_DIR))

import init_doctor  # noqa: E402

_BASE_MARKER_NO_POSTINIT = """\
[meta]
version = "0.1.0"
date    = "2026-05-25"

[answers]
package_name = "my_project"
repo_name = "my-project"
author = "Test User"
email = "test@example.com"
owner = "newowner"
"""

_POSTINIT_PYPI_ENABLED = """

[post_init]
version = "0.1.0"
date    = "2026-05-25"
mode    = "full"

[post_init.publishing]
pypi           = "enabled"
testpypi       = "enabled"
release_please = "enabled"

[post_init.codecov]
status    = "enabled"
token_set = false

[post_init.readthedocs]
status = "deferred"

[post_init.oidc]
"""

_POSTINIT_PYPI_DISABLED = """

[post_init]
version = "0.1.0"
date    = "2026-05-25"
mode    = "full"

[post_init.publishing]
pypi           = "disabled"
testpypi       = "disabled"
release_please = "disabled"

[post_init.codecov]
status    = "deferred"
token_set = false

[post_init.readthedocs]
status = "deferred"

[post_init.oidc]
"""


@pytest.fixture
def doctor_fixture(tmp_path, monkeypatch):
    """tmp_path with a stubbed marker + .github/workflows tree. Returns the tmp_path."""
    marker = tmp_path / ".blueprint-initialized"
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    monkeypatch.setattr(init_doctor, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(init_doctor, "MARKER_PATH", marker)
    return tmp_path


def _write_marker(fixture: Path, *suffixes: str) -> None:
    text = _BASE_MARKER_NO_POSTINIT + "".join(suffixes)
    (fixture / ".blueprint-initialized").write_text(text, encoding="utf-8")


# ──────────────────────────────────────────────────────────────
# marker-present
# ──────────────────────────────────────────────────────────────


class TestMarkerPresent:
    def test_no_marker_at_all_returns_warn(self, doctor_fixture):
        # don't write a marker
        r = init_doctor.check_post_init_marker_present()
        assert r.status == "warn"
        assert "post-init" in r.message.lower() or "[post_init]" in r.message

    def test_marker_without_post_init_section_returns_warn(self, doctor_fixture):
        _write_marker(doctor_fixture)
        r = init_doctor.check_post_init_marker_present()
        assert r.status == "warn"

    def test_marker_with_post_init_returns_pass(self, doctor_fixture):
        _write_marker(doctor_fixture, _POSTINIT_PYPI_ENABLED)
        r = init_doctor.check_post_init_marker_present()
        assert r.status == "pass"
        assert "2026-05-25" in r.message


# ──────────────────────────────────────────────────────────────
# workflows-match-state
# ──────────────────────────────────────────────────────────────


class TestWorkflowsMatchState:
    def test_no_post_init_returns_empty(self, doctor_fixture):
        # no marker — function returns []
        results = init_doctor.check_post_init_workflows_match_state()
        assert results == []

    def test_enabled_and_in_workflows_dir_passes(self, doctor_fixture):
        _write_marker(doctor_fixture, _POSTINIT_PYPI_ENABLED)
        (doctor_fixture / ".github" / "workflows" / "publish.yml").write_text(
            "name: x\n"
        )
        (doctor_fixture / ".github" / "workflows" / "release-please.yml").write_text(
            "name: x\n"
        )
        results = init_doctor.check_post_init_workflows_match_state()
        statuses = {r.status for r in results}
        assert "error" not in statuses

    def test_enabled_but_in_disabled_dir_errors(self, doctor_fixture):
        _write_marker(doctor_fixture, _POSTINIT_PYPI_ENABLED)
        disabled = doctor_fixture / ".github" / "workflows.disabled"
        disabled.mkdir(parents=True)
        (disabled / "publish.yml").write_text("name: x\n")
        # release-please.yml properly in workflows/
        (doctor_fixture / ".github" / "workflows" / "release-please.yml").write_text(
            "name: x\n"
        )
        results = init_doctor.check_post_init_workflows_match_state()
        pypi_finding = next(r for r in results if r.name.endswith("publishing.pypi"))
        assert pypi_finding.status == "error"
        assert (
            "reconcile" in pypi_finding.message.lower()
            or "workflows.disabled" in pypi_finding.message
        )

    def test_disabled_and_in_disabled_dir_passes(self, doctor_fixture):
        _write_marker(doctor_fixture, _POSTINIT_PYPI_DISABLED)
        disabled = doctor_fixture / ".github" / "workflows.disabled"
        disabled.mkdir(parents=True)
        (disabled / "publish.yml").write_text("name: x\n")
        (disabled / "release-please.yml").write_text("name: x\n")
        results = init_doctor.check_post_init_workflows_match_state()
        assert all(r.status == "pass" for r in results)

    def test_disabled_but_still_in_active_dir_errors(self, doctor_fixture):
        _write_marker(doctor_fixture, _POSTINIT_PYPI_DISABLED)
        (doctor_fixture / ".github" / "workflows" / "publish.yml").write_text(
            "name: x\n"
        )
        results = init_doctor.check_post_init_workflows_match_state()
        pypi_finding = next(r for r in results if r.name.endswith("publishing.pypi"))
        assert pypi_finding.status == "error"

    def test_enabled_but_file_missing_everywhere_errors(self, doctor_fixture):
        _write_marker(doctor_fixture, _POSTINIT_PYPI_ENABLED)
        # don't create publish.yml at all
        results = init_doctor.check_post_init_workflows_match_state()
        pypi_finding = next(r for r in results if r.name.endswith("publishing.pypi"))
        assert pypi_finding.status == "error"


# ──────────────────────────────────────────────────────────────
# codecov-gate
# ──────────────────────────────────────────────────────────────

_CI_WITH_GATE = """\
name: ci
jobs:
  test:
    steps:
      - name: codecov
        # post-init: codecov-gated
        if: secrets.CODECOV_TOKEN != ''
        uses: codecov/codecov-action@v5
"""

_CI_WITHOUT_GATE = """\
name: ci
jobs:
  test:
    steps:
      - name: codecov
        uses: codecov/codecov-action@v5
"""


class TestCodecovGate:
    def test_deferred_status_passes(self, doctor_fixture):
        _write_marker(doctor_fixture)  # no [post_init] at all → effectively deferred
        r = init_doctor.check_post_init_codecov_gate()
        assert r.status == "pass"

    def test_status_enabled_with_gate_passes(self, doctor_fixture):
        _write_marker(doctor_fixture, _POSTINIT_PYPI_ENABLED)
        (doctor_fixture / ".github" / "workflows" / "ci.yml").write_text(_CI_WITH_GATE)
        r = init_doctor.check_post_init_codecov_gate()
        assert r.status == "pass"

    def test_status_enabled_without_gate_errors(self, doctor_fixture):
        _write_marker(doctor_fixture, _POSTINIT_PYPI_ENABLED)
        (doctor_fixture / ".github" / "workflows" / "ci.yml").write_text(
            _CI_WITHOUT_GATE
        )
        r = init_doctor.check_post_init_codecov_gate()
        assert r.status == "error"
        assert "post-init" in r.message.lower() or "gate" in r.message.lower()


# ──────────────────────────────────────────────────────────────
# oidc-freshness
# ──────────────────────────────────────────────────────────────

_POSTINIT_OIDC_VERIFIED = """

[post_init]
date = "2026-05-25"
mode = "full"

[post_init.publishing]
pypi = "enabled"
testpypi = "enabled"
release_please = "enabled"

[post_init.codecov]
status = "deferred"
token_set = false

[post_init.readthedocs]
status = "deferred"

[post_init.oidc]
pypi_trust_verified_at = "2026-05-25T10:00:00+00:00"
testpypi_trust_verified_at = "2026-05-25T10:01:00+00:00"
"""


class TestOidcFreshness:
    def test_publishing_enabled_with_verification_passes(self, doctor_fixture):
        _write_marker(doctor_fixture, _POSTINIT_OIDC_VERIFIED)
        r = init_doctor.check_post_init_oidc_freshness()
        assert r.status == "pass"
        assert "2026-05-25" in r.message

    def test_publishing_enabled_without_verification_warns(self, doctor_fixture):
        _write_marker(doctor_fixture, _POSTINIT_PYPI_ENABLED)
        r = init_doctor.check_post_init_oidc_freshness()
        assert r.status == "warn"

    def test_no_post_init_section_passes_as_na(self, doctor_fixture):
        _write_marker(doctor_fixture)
        r = init_doctor.check_post_init_oidc_freshness()
        assert r.status == "pass"
