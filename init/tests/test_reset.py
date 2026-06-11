"""CHANGELOG reset on init — the root-cause fix for the CHANGELOG identity leak.

The blueprint's own CHANGELOG accumulates release history naming the blueprint
(`plbp`, `smorinlabs`, compare-URLs). Rewriting those into a fork's identity
would graft a fabricated history; instead `init` resets the file to a stub.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _engine import apply_reset
from common import ResetOp, load_manifest


def test_manifest_resets_changelog_to_stub() -> None:
    resets = {r.path: r.stub for r in load_manifest().resets}
    assert resets.get("CHANGELOG.md") == "# Changelog\n"


def test_apply_reset_overwrites_then_is_idempotent(tmp_path: Path) -> None:
    f = tmp_path / "CHANGELOG.md"
    f.write_text("# Changelog\n\n## [2.0.0] rename to plbp\n- smorinlabs/py-…\n")
    op = ResetOp(path="CHANGELOG.md", stub="# Changelog\n")
    assert apply_reset(op, root=tmp_path) is True
    assert f.read_text() == "# Changelog\n"  # blueprint history (plbp) discarded
    assert apply_reset(op, root=tmp_path) is False  # already the stub → no change


def test_reset_files_are_not_also_replaced() -> None:
    # A reset file must not appear in any [[replace]] block, or init would both
    # rewrite identity in it and then reset it (order-dependent, confusing).
    manifest = load_manifest()
    reset_paths = {r.path for r in manifest.resets}
    for op in manifest.replaces:
        overlap = set(op.files) & reset_paths
        assert not overlap, f"field {op.field!r} lists reset file(s): {overlap}"
