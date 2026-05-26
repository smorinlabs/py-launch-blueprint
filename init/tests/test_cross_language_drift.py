"""Cross-language drift tests.

The system has exactly one language boundary that defeats import-based DRY:
init/guard.sh is POSIX shell (so it can run on a bare clone before `uv sync`)
and cannot import from init/common.py. The blueprint-origin owner/repo list
therefore exists in BOTH places. This test asserts they match — a guard
silently skipping when it shouldn't, or warning when it shouldn't, is a
high-consequence failure mode with zero structural mitigation otherwise.

If you change either list, run pytest and the failure will tell you
exactly what's out of sync.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

INIT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(INIT_DIR))

from common import BLUEPRINT_ORIGIN_OWNER_REPO  # noqa: E402


def _parse_shell_owner_repos() -> set[tuple[str, str]]:
    """Extract the `blueprint_owner_repos="..."` assignment from guard.sh."""
    guard_text = (INIT_DIR / "guard.sh").read_text(encoding="utf-8")
    m = re.search(r'^blueprint_owner_repos="([^"]+)"', guard_text, re.MULTILINE)
    assert m, 'guard.sh: expected `blueprint_owner_repos="..."` assignment'
    pairs = set()
    for item in m.group(1).split():
        owner, _, repo = item.partition("/")
        assert owner and repo, f"guard.sh: malformed owner/repo entry {item!r}"
        pairs.add((owner, repo))
    return pairs


def test_blueprint_origin_owner_repos_match_across_python_and_shell() -> None:
    shell_set = _parse_shell_owner_repos()
    python_set = set(BLUEPRINT_ORIGIN_OWNER_REPO)
    only_in_shell = shell_set - python_set
    only_in_python = python_set - shell_set
    assert not (only_in_shell or only_in_python), (
        "cross-language drift between init/common.py BLUEPRINT_ORIGIN_OWNER_REPO "
        "and init/guard.sh blueprint_owner_repos:\n"
        f"  only in guard.sh:   {sorted(only_in_shell) or '(none)'}\n"
        f"  only in common.py:  {sorted(only_in_python) or '(none)'}"
    )
