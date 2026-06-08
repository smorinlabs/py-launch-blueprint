"""Guard test for conftest._git().

Prevents recurrence of the fixture-commit-on-real-repo failure class:
a sandboxed identity ("Test Fixture <test@example.com>") commit must never
land on a real repo because of a misdirected `cwd`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import _git


def test_git_helper_refuses_non_tmp_cwd():
    """Verify _git() guard rejects cwd outside the system temp dir."""
    # Use the live blueprint repo root — the exact place a misdirected
    # cwd would land — to prove the guard refuses it.
    real_repo = Path(__file__).resolve().parents[2]
    with pytest.raises(RuntimeError, match="refusing to run sandboxed _git"):
        _git("status", cwd=real_repo)
