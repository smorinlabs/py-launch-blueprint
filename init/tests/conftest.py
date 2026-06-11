"""Shared fixtures for init/tests/.

The five §4.7 instantiation modes each leave the working tree in a different
state; `build_fixture(tmp_path, mode)` materializes that state from the live
blueprint into a tmp directory so tests can subprocess-invoke the real
init/guard.sh + init/init.py against it.

Curated copy (rather than full repo) keeps each test under ~1s while still
exercising the real CLI end-to-end. We copy the small set of files the
manifest's [[replace]] / [[rename]] blocks reference; absent files are
skipped by the engine (and that's tested too).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

LIVE_BLUEPRINT = Path(__file__).resolve().parents[2]

# Files copied into every fixture. Curated for speed + manifest coverage.
_CURATED_FILES = (
    "pyproject.toml",
    "Justfile",
    "README.md",
    "LICENSE",
    ".gitignore",
    "docs/source/conf.py",
)
_CURATED_DIRS = (
    "py_launch_blueprint",
    "init",
)

import sys as _sys  # noqa: E402 - deliberate placement after LIVE_BLUEPRINT definition

_sys.path.insert(0, str(LIVE_BLUEPRINT / "init"))
from common import MODES  # noqa: E402 — SSOT; re-exported for legacy imports


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    """Run git with a sandboxed identity (no global config side-effects)."""
    # Safety rail: these fixtures `git init`/`git commit` under a "Test Fixture"
    # identity. If `cwd` were ever misdirected at the live repo, that commit
    # would land on the real project — the root cause of the 152-file-wipe
    # incident. Refuse to run anywhere but the system temp dir. `.resolve()` on
    # both sides normalizes macOS `/var/folders` vs `/private/var/folders`.
    tmp_root = Path(tempfile.gettempdir()).resolve()
    resolved_cwd = Path(cwd).resolve()
    if not resolved_cwd.is_relative_to(tmp_root):
        raise RuntimeError(
            f"refusing to run sandboxed _git outside the system temp dir: "
            f"cwd={resolved_cwd} is not under {tmp_root}"
        )
    env_args = [
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test Fixture",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "init.defaultBranch=main",
    ]
    return subprocess.run(
        ["git", *env_args, *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def build_fixture(tmp_path: Path, mode: str) -> Path:
    """Materialize a §4.7-mode fixture under tmp_path. Returns project root."""
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")

    proj = tmp_path / "proj"
    proj.mkdir()

    for rel in _CURATED_FILES:
        src = LIVE_BLUEPRINT / rel
        dst = proj / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    for rel in _CURATED_DIRS:
        src = LIVE_BLUEPRINT / rel
        if src.exists():
            shutil.copytree(src, proj / rel, dirs_exist_ok=False)

    if mode == "zip":
        # Mode 5: ZIP download — no .git directory at all.
        return proj

    _git("init", "-q", cwd=proj)
    _git("add", "-A", cwd=proj)
    _git("commit", "-q", "-m", "initial commit (fixture)", cwd=proj)

    if mode in ("template_button", "gh_template"):
        _git(
            "remote",
            "add",
            "origin",
            "git@github.com:newowner/my-project.git",
            cwd=proj,
        )
    elif mode == "clone_reinit":
        pass  # Mode 3: no remote configured yet
    elif mode == "fork":
        # Mode 4: fork — same repo NAME, different OWNER.
        _git(
            "remote",
            "add",
            "origin",
            "git@github.com:alice/py-launch-blueprint.git",
            cwd=proj,
        )

    return proj


ANSWERS_TOML = """\
[answers]
package_name = "my_project"
repo_name = "my-project"
app_name = "myapp"
author = "Test User"
email = "test@example.com"
owner = "newowner"
"""


def write_answers(proj: Path) -> Path:
    answers = proj / "answers.toml"
    answers.write_text(ANSWERS_TOML, encoding="utf-8")
    return answers


def run_guard(proj: Path, mode_arg: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "init/guard.sh", mode_arg],
        cwd=proj,
        capture_output=True,
        text=True,
    )


def run_init(proj: Path, *extra: str) -> subprocess.CompletedProcess:
    answers = write_answers(proj)
    return subprocess.run(
        [
            "uv",
            "run",
            "--script",
            "init/init.py",
            "--config",
            str(answers.relative_to(proj)),
            "--no-lockfile",
            "--yes",
            "--allow-dirty",
            *extra,
        ],
        cwd=proj,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def fixture_for_mode(tmp_path):
    """Parametrize-friendly: returns a callable to build a fixture in a mode."""

    def _build(mode: str) -> Path:
        return build_fixture(tmp_path, mode)

    return _build
