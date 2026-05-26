"""Tests for the five §4.7 instantiation modes.

Each mode gets two assertions per §4.7's table:
  1. Guard behavior — does it skip or fire as the spec mandates?
  2. init behavior — does init proceed (modes 1-4) or refuse (mode 5)?

Modes 1 (template button) and 2 (gh CLI template) produce identical state, so
they share the same assertion set but run as separate tests for regression
clarity.

These are the loop's termination contract: when all pass, the system has been
proven against every documented entry path.
"""

from __future__ import annotations

import pytest
from conftest import (
    build_fixture,
    run_guard,
    run_init,
)

BANNER = "blueprint un-initialized"


# ──────────────────────────────────────────────────────────────
# Mode 1 — GitHub "Use this template" button
# ──────────────────────────────────────────────────────────────


class TestMode1TemplateButton:
    @pytest.fixture
    def proj(self, tmp_path):
        return build_fixture(tmp_path, "template_button")

    def test_guard_warn_fires(self, proj):
        r = run_guard(proj, "warn")
        assert r.returncode == 0, "warn must always exit 0"
        assert BANNER in r.stderr, "warn must print banner on non-blueprint origin"

    def test_guard_block_exits_nonzero(self, proj):
        r = run_guard(proj, "block")
        assert r.returncode == 1, "block must exit 1 on non-blueprint origin"
        assert "blocked" in r.stderr.lower()

    def test_init_proceeds_and_writes_marker(self, proj):
        r = run_init(proj)
        assert r.returncode == 0, f"init failed:\nstderr={r.stderr}\nstdout={r.stdout}"
        assert (proj / "init" / ".blueprint-initialized").exists()


# ──────────────────────────────────────────────────────────────
# Mode 2 — `gh repo create --template` (state identical to mode 1)
# ──────────────────────────────────────────────────────────────


class TestMode2GhTemplate:
    @pytest.fixture
    def proj(self, tmp_path):
        return build_fixture(tmp_path, "gh_template")

    def test_guard_warn_fires(self, proj):
        r = run_guard(proj, "warn")
        assert r.returncode == 0
        assert BANNER in r.stderr

    def test_guard_block_exits_nonzero(self, proj):
        r = run_guard(proj, "block")
        assert r.returncode == 1

    def test_init_proceeds(self, proj):
        r = run_init(proj)
        assert r.returncode == 0, f"init failed:\nstderr={r.stderr}"
        assert (proj / "init" / ".blueprint-initialized").exists()


# ──────────────────────────────────────────────────────────────
# Mode 3 — Clone + rm -rf .git + git init  (no origin configured)
# ──────────────────────────────────────────────────────────────


class TestMode3CloneReinit:
    @pytest.fixture
    def proj(self, tmp_path):
        return build_fixture(tmp_path, "clone_reinit")

    def test_guard_does_not_skip_when_origin_missing(self, proj):
        """§4.7: 'guard's origin check returns empty and does NOT skip'."""
        r = run_guard(proj, "warn")
        assert r.returncode == 0
        assert BANNER in r.stderr, (
            "guard must NOT skip when origin is unset (§4.7 mode #3): "
            "an unconfigured origin is not the same as 'this IS the blueprint'."
        )

    def test_init_proceeds_with_no_origin(self, proj):
        """§4.7: 'init proceeds with no origin'."""
        r = run_init(proj)
        assert r.returncode == 0, f"init failed:\nstderr={r.stderr}"
        assert (proj / "init" / ".blueprint-initialized").exists()


# ──────────────────────────────────────────────────────────────
# Mode 4 — Fork (origin owner differs, repo name collides)
# ──────────────────────────────────────────────────────────────


class TestMode4Fork:
    @pytest.fixture
    def proj(self, tmp_path):
        return build_fixture(tmp_path, "fork")

    def test_guard_does_not_skip_on_name_only_match(self, proj):
        """§4.7 regression: skip must compare OWNER+NAME, not name alone.

        Without this guard, a fork at alice/py-launch-blueprint would silently
        skip migration and ship as the blueprint to alice's users.
        """
        r = run_guard(proj, "warn")
        assert r.returncode == 0
        assert BANNER in r.stderr, (
            "guard must NOT skip a fork: alice/py-launch-blueprint shares the "
            "repo name with the blueprint but the owner differs (§4.7 mode #4)."
        )

    def test_block_fires_on_fork(self, proj):
        r = run_guard(proj, "block")
        assert r.returncode == 1
        assert "blocked" in r.stderr.lower()

    def test_init_proceeds_on_fork(self, proj):
        r = run_init(proj)
        assert r.returncode == 0, f"init failed:\nstderr={r.stderr}"
        assert (proj / "init" / ".blueprint-initialized").exists()

    def test_contributor_sentinel_silences_guard(self, proj):
        """§4.7: contributors who fork to PR upstream use the local sentinel."""
        (proj / "init" / ".blueprint-contributor").touch()
        r = run_guard(proj, "warn")
        assert r.returncode == 0
        assert BANNER not in r.stderr, "sentinel must silence the warn banner"


# ──────────────────────────────────────────────────────────────
# Mode 5 — ZIP download (no .git at all)
# ──────────────────────────────────────────────────────────────


class TestMode5Zip:
    @pytest.fixture
    def proj(self, tmp_path):
        return build_fixture(tmp_path, "zip")

    def test_no_git_dir(self, proj):
        assert not (proj / ".git").exists(), (
            "fixture sanity: ZIP mode should have no .git"
        )

    def test_guard_warns_with_no_git(self, proj):
        """Guard's git invocation fails → no origin → guard does not skip."""
        r = run_guard(proj, "warn")
        assert r.returncode == 0
        assert BANNER in r.stderr

    def test_init_refuses_without_git_dir(self, proj):
        """§4.7: init refuses with actionable 'run git init first' message."""
        r = run_init(proj)
        assert r.returncode != 0, "init must refuse on missing .git"
        msg = (r.stderr + r.stdout).lower()
        assert "no .git" in msg or "git init" in msg, (
            f"refusal must be actionable; got stderr={r.stderr!r}"
        )

    def test_allow_dirty_does_not_override_missing_git(self, proj):
        """§4.7: --allow-dirty does NOT bypass the missing-.git precondition."""
        r = run_init(proj, "--allow-dirty")
        assert r.returncode != 0


# ──────────────────────────────────────────────────────────────
# Cross-mode invariants — the marker silences everything (post-init)
# ──────────────────────────────────────────────────────────────


class TestMarkerSilences:
    @pytest.fixture(params=["template_button", "gh_template", "clone_reinit", "fork"])
    def proj(self, tmp_path, request):
        return build_fixture(tmp_path, request.param)

    def test_marker_silences_warn_and_block(self, proj):
        (proj / "init" / ".blueprint-initialized").write_text(
            '[meta]\nversion="0.1.0"\n',
            encoding="utf-8",
        )
        warn = run_guard(proj, "warn")
        block = run_guard(proj, "block")
        assert warn.returncode == 0
        assert BANNER not in warn.stderr
        assert block.returncode == 0  # block exits 0 when skipping
