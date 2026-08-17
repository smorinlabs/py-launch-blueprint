"""P06-T02 — scripts/guard.sh skip-condition contract (D-P06-1).

The fork guard survives the init/ engine's retirement with three skip
conditions: press receipt, contributor sentinel, canonical origin (both
owner spellings). Warn mode always exits 0; block mode exits 1 with no
condition; an unrelated press/ dir without a receipt does NOT silence
(the discriminating case PR #505 pinned for the receipt condition).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

GUARD = Path(__file__).parents[1] / "scripts" / "guard.sh"


def _repo(tmp_path: Path, origin: str | None = None) -> Path:
    repo = tmp_path / "clone"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy2(GUARD, repo / "scripts" / "guard.sh")
    subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), "init", "-q", "-b", "main"],  # noqa: S607
        check=True,
        capture_output=True,
    )
    if origin is not None:
        subprocess.run(  # noqa: S603
            ["git", "-C", str(repo), "remote", "add", "origin", origin],  # noqa: S607
            check=True,
            capture_output=True,
        )
    return repo


def _run(repo: Path, mode: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["bash", str(repo / "scripts" / "guard.sh"), mode],  # noqa: S607
        capture_output=True,
        text=True,
    )


class TestGuardModes:
    def test_warn_banners_but_exits_zero(self, tmp_path: Path):
        repo = _repo(tmp_path)
        result = _run(repo, "warn")
        assert result.returncode == 0
        assert "rebrand" in result.stderr

    def test_block_exits_one_with_no_condition(self, tmp_path: Path):
        repo = _repo(tmp_path)
        result = _run(repo, "block")
        assert result.returncode == 1
        assert "blocked" in result.stderr

    def test_unknown_mode_exits_two(self, tmp_path: Path):
        repo = _repo(tmp_path)
        assert _run(repo, "bogus").returncode == 2


class TestSkipConditions:
    def test_receipt_silences_both_modes(self, tmp_path: Path):
        repo = _repo(tmp_path)
        (repo / "press").mkdir()
        (repo / "press" / "press-receipt.toml").write_text(
            "[press]\nverified = true\n", encoding="utf-8"
        )
        assert _run(repo, "block").returncode == 0
        assert _run(repo, "warn").stderr == ""

    def test_unrelated_press_dir_does_not_silence(self, tmp_path: Path):
        repo = _repo(tmp_path)
        (repo / "press").mkdir()
        (repo / "press" / "notes.md").write_text("press\n", encoding="utf-8")
        assert _run(repo, "block").returncode == 1

    def test_contributor_sentinel_silences(self, tmp_path: Path):
        repo = _repo(tmp_path)
        (repo / ".blueprint-contributor").write_text("", encoding="utf-8")
        assert _run(repo, "block").returncode == 0

    @pytest.mark.parametrize(
        "origin",
        [
            "https://github.com/smorinlabs/py-launch-blueprint.git",
            "git@github.com:smorinlabs/py-launch-blueprint.git",
            "https://github.com/smorin/py-launch-blueprint",
        ],
    )
    def test_canonical_origin_silences(self, tmp_path: Path, origin: str):
        repo = _repo(tmp_path, origin=origin)
        assert _run(repo, "block").returncode == 0

    def test_fork_origin_does_not_silence(self, tmp_path: Path):
        repo = _repo(tmp_path, origin="https://github.com/someone/their-fork.git")
        assert _run(repo, "block").returncode == 1

    def test_legacy_marker_no_longer_silences(self, tmp_path: Path):
        """The engine that wrote the marker is retired; the condition is
        deliberately gone (D-P06-1, documented behavior change)."""
        repo = _repo(tmp_path)
        (repo / "init").mkdir()
        (repo / "init" / ".blueprint-initialized").write_text("", encoding="utf-8")
        assert _run(repo, "block").returncode == 1
