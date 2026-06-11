"""Safety rail for the fixture git helper (``conftest._git``).

The init fixtures run real ``git init`` / ``git commit`` (identity
``Test Fixture``) inside a temp sandbox. If ``cwd`` were ever misdirected at the
live repo, that commit would land on the real project — the root cause of the
152-file-wipe incident (a phantom ``initial commit (fixture)`` that wiped the
repo, later reverted in #366). ``_git`` refuses to run outside the system temp
dir; this verifies the rail fires on the live repo and stays out of the way for
a genuine sandbox.
"""

from __future__ import annotations

import pytest
from conftest import LIVE_BLUEPRINT, _git


def test_git_refuses_to_run_at_the_live_repo_root() -> None:
    with pytest.raises(RuntimeError, match="refusing to run sandboxed _git"):
        _git("status", cwd=LIVE_BLUEPRINT)


def test_git_runs_in_a_temp_sandbox(tmp_path) -> None:
    # A real temp sandbox is allowed: initializing a throwaway repo succeeds.
    assert _git("init", "-q", cwd=tmp_path).returncode == 0
