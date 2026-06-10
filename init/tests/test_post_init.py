"""Unit tests for init/post_init.py.

Covers the testable-without-gh-CLI pieces:
  * Marker I/O round-trip (read, write, preserve [meta]+[answers])
  * Workflow file disable/enable + idempotency
  * ci.yml codecov gate edit + idempotency + warning-step insertion
  * Status output

Tests that need gh/PyPI/browser (oidc_walkthrough, run_setup_github_environments,
set_codecov_token_via_gh) are deliberately NOT covered here — they're integration
concerns and would require heavy mocking that wouldn't catch real failure modes
anyway. Those should be exercised by extending init/tests/integration/run-mode.sh.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

INIT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(INIT_DIR))

import post_init  # noqa: E402
from post_init import (  # noqa: E402
    DEFERRED,
    DISABLED,
    ENABLED,
    CodecovConfig,
    PostInitConfig,
    PublishingConfig,
    RTDConfig,
)

# ──────────────────────────────────────────────────────────────
# Helpers — tmp marker fixture
# ──────────────────────────────────────────────────────────────

_BASE_MARKER = """\
# init/.blueprint-initialized
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


@pytest.fixture
def patched_paths(tmp_path, monkeypatch):
    """Patch post_init's REPO_ROOT/MARKER_PATH/WORKFLOWS_DIR to a tmp fixture."""
    marker = tmp_path / ".blueprint-initialized"
    marker.write_text(_BASE_MARKER, encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    disabled = tmp_path / ".github" / "workflows.disabled"
    workflows.mkdir(parents=True)
    # populate sample workflows that match what post_init knows about
    (workflows / "publish.yml").write_text("name: publish\n", encoding="utf-8")
    (workflows / "release-please.yml").write_text(
        "name: release-please\n", encoding="utf-8"
    )
    monkeypatch.setattr(post_init, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(post_init, "MARKER_PATH", marker)
    monkeypatch.setattr(post_init, "WORKFLOWS_DIR", workflows)
    monkeypatch.setattr(post_init, "DISABLED_WORKFLOWS_DIR", disabled)
    monkeypatch.setattr(post_init, "CI_YML", workflows / "ci.yml")
    return tmp_path


# ──────────────────────────────────────────────────────────────
# Marker I/O
# ──────────────────────────────────────────────────────────────


class TestMarkerRoundTrip:
    def test_write_then_read_preserves_publishing(self, patched_paths):
        cfg = PostInitConfig(
            mode="full",
            publishing=PublishingConfig(
                pypi=ENABLED, testpypi=DISABLED, release_please=ENABLED
            ),
        )
        post_init.write_marker_with_post_init(cfg)
        out = post_init.read_existing_post_init()
        assert out is not None
        assert out.publishing.pypi == ENABLED
        assert out.publishing.testpypi == DISABLED
        assert out.publishing.release_please == ENABLED

    def test_write_preserves_meta_and_answers(self, patched_paths):
        cfg = PostInitConfig(publishing=PublishingConfig(pypi=DEFERRED))
        post_init.write_marker_with_post_init(cfg)
        text = (patched_paths / ".blueprint-initialized").read_text()
        assert "[meta]" in text
        assert "[answers]" in text
        assert 'package_name = "my_project"' in text
        assert "[post_init]" in text

    def test_rewrite_replaces_old_post_init_section(self, patched_paths):
        # Write once
        cfg1 = PostInitConfig(publishing=PublishingConfig(pypi=ENABLED))
        post_init.write_marker_with_post_init(cfg1)
        # Write again with different value
        cfg2 = PostInitConfig(publishing=PublishingConfig(pypi=DISABLED))
        post_init.write_marker_with_post_init(cfg2)
        text = (patched_paths / ".blueprint-initialized").read_text()
        assert text.count("[post_init]") == 1
        assert text.count("[post_init.publishing]") == 1
        out = post_init.read_existing_post_init()
        assert out.publishing.pypi == DISABLED

    def test_read_returns_none_when_no_post_init_section(self, patched_paths):
        # Base fixture has [meta]+[answers] but no [post_init]
        assert post_init.read_existing_post_init() is None

    def test_codecov_token_set_persists(self, patched_paths):
        cfg = PostInitConfig(
            codecov=CodecovConfig(status=ENABLED, token_set=True),
        )
        post_init.write_marker_with_post_init(cfg)
        out = post_init.read_existing_post_init()
        assert out.codecov.token_set is True

    def test_rtd_state_persists(self, patched_paths):
        cfg = PostInitConfig(readthedocs=RTDConfig(status="configured"))
        post_init.write_marker_with_post_init(cfg)
        out = post_init.read_existing_post_init()
        assert out.readthedocs.status == "configured"


# ──────────────────────────────────────────────────────────────
# Workflow file disable / enable
# ──────────────────────────────────────────────────────────────


class TestWorkflowMoves:
    def test_disable_moves_file_to_disabled_dir(self, patched_paths):
        assert post_init.disable_workflow("publish.yml") is True
        assert not (patched_paths / ".github" / "workflows" / "publish.yml").exists()
        assert (
            patched_paths / ".github" / "workflows.disabled" / "publish.yml"
        ).exists()

    def test_disable_is_idempotent(self, patched_paths):
        post_init.disable_workflow("publish.yml")
        # Second call: file already in disabled dir, returns False (no-op)
        assert post_init.disable_workflow("publish.yml") is False

    def test_enable_moves_file_back(self, patched_paths):
        post_init.disable_workflow("publish.yml")
        assert post_init.enable_workflow("publish.yml") is True
        assert (patched_paths / ".github" / "workflows" / "publish.yml").exists()
        assert not (
            patched_paths / ".github" / "workflows.disabled" / "publish.yml"
        ).exists()

    def test_enable_is_idempotent(self, patched_paths):
        # publish.yml starts in workflows/; enable() finds it there → no-op
        assert post_init.enable_workflow("publish.yml") is False

    def test_disable_missing_workflow_skips_gracefully(self, patched_paths):
        assert post_init.disable_workflow("nonexistent.yml") is False


# ──────────────────────────────────────────────────────────────
# ci.yml codecov gate edit
# ──────────────────────────────────────────────────────────────

_SAMPLE_CI_YML = """\
name: ci
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.12', '3.13']
    steps:
      - uses: actions/checkout@v6
      - name: Run tests
        run: pytest --cov

      - name: Codecov upload
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.12'
        uses: codecov/codecov-action@v5
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: coverage.xml

      - name: After codecov step
        run: echo done
"""


class TestCiYmlCodecovGate:
    @pytest.fixture
    def with_ci(self, patched_paths):
        ci = patched_paths / ".github" / "workflows" / "ci.yml"
        ci.write_text(_SAMPLE_CI_YML, encoding="utf-8")
        return ci

    def test_gate_adds_secret_check_to_if_line(self, with_ci):
        assert post_init.edit_ci_yml_codecov_gate() is True
        text = with_ci.read_text()
        assert "secrets.CODECOV_TOKEN != ''" in text

    def test_gate_appends_warning_step(self, with_ci):
        post_init.edit_ci_yml_codecov_gate()
        text = with_ci.read_text()
        assert "Codecov upload dormant warning" in text
        assert "secrets.CODECOV_TOKEN == ''" in text
        assert "post-init: codecov-gated" in text

    def test_gate_is_idempotent(self, with_ci):
        post_init.edit_ci_yml_codecov_gate()
        first = with_ci.read_text()
        # Second call should be no-op
        assert post_init.edit_ci_yml_codecov_gate() is False
        second = with_ci.read_text()
        assert first == second

    def test_gate_preserves_unrelated_steps(self, with_ci):
        post_init.edit_ci_yml_codecov_gate()
        text = with_ci.read_text()
        assert "Run tests" in text
        assert "After codecov step" in text

    def test_gate_returns_false_when_no_ci_yml(self, patched_paths):
        # No ci.yml created — should bail
        assert post_init.edit_ci_yml_codecov_gate() is False


# ──────────────────────────────────────────────────────────────
# Status output
# ──────────────────────────────────────────────────────────────


class TestStatusOutput:
    def test_status_none_shows_not_run(self, capsys):
        post_init.print_status(None)
        captured = capsys.readouterr()
        assert "not been run" in captured.out

    def test_status_shows_publishing_and_codecov(self, capsys):
        cfg = PostInitConfig(
            date="2026-05-25",
            publishing=PublishingConfig(pypi=ENABLED, testpypi=DISABLED),
            codecov=CodecovConfig(status=ENABLED, token_set=True),
        )
        post_init.print_status(cfg)
        out = capsys.readouterr().out
        assert "2026-05-25" in out
        assert "publishing.pypi" in out
        assert "enabled" in out
        assert "token_set=True" in out


# ──────────────────────────────────────────────────────────────
# Project-name derivation
# ──────────────────────────────────────────────────────────────


class TestDeriveProjectName:
    def test_returns_name_from_pyproject(self, tmp_path, monkeypatch):
        py = tmp_path / "pyproject.toml"
        py.write_text('[project]\nname = "acme_widget"\nversion = "0.1.0"\n')
        monkeypatch.setattr(post_init, "REPO_ROOT", tmp_path)
        assert post_init._derive_project_name() == "acme_widget"

    def test_returns_none_when_no_pyproject(self, tmp_path, monkeypatch):
        monkeypatch.setattr(post_init, "REPO_ROOT", tmp_path)
        assert post_init._derive_project_name() is None
