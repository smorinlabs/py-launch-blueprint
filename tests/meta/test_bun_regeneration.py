"""A mismatched lockfile writer must fail before deleting the existing lock."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("runner", ["shell", "powershell"])
@pytest.mark.parametrize("version", [None, "0.0.0", "1.3.5"])
def test_regeneration_checks_bun_before_replacing_lock(tmp_path, runner, version):
    if runner == "shell":
        executable = shutil.which("sh") if os.name != "nt" else None
        command = [executable, str(ROOT / "scripts/regen-bun-lock.sh")]
    else:
        executable = shutil.which("pwsh") or shutil.which("powershell")
        command = [
            executable,
            "-NoProfile",
            "-File",
            str(ROOT / "scripts/regen-bun-lock.ps1"),
        ]
    if executable is None:
        pytest.skip(f"{runner} is unavailable on this platform")

    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake_bun = bindir / ("bun.cmd" if os.name == "nt" else "bun")
    if version is None:
        pass  # No Bun on PATH: fail before touching the original lock.
    elif os.name == "nt":
        fake_bun.write_text(
            f'@echo off\nif "%1"=="--version" (\necho {version}\n'
            "exit /b 0\n)\necho regenerated>bun.lock\n"
        )
    else:
        fake_bun.write_text(
            f'#!/bin/sh\nif [ "$1" = --version ]; then echo {version}; '
            "else printf regenerated > bun.lock; fi\n"
        )
        fake_bun.chmod(0o755)
    lock = tmp_path / "bun.lock"
    lock.write_bytes(b"original lock contents\n")
    result = subprocess.run(  # noqa: S603 — controlled test executables
        command,
        cwd=tmp_path,
        env={**os.environ, "PATH": str(bindir) + os.pathsep + os.defpath},
        capture_output=True,
        text=True,
        check=False,
    )
    if version == "1.3.5":
        assert result.returncode == 0, result.stdout + result.stderr
        assert lock.read_text().strip() == "regenerated"
    else:
        assert result.returncode != 0
        assert lock.read_bytes() == b"original lock contents\n"
        if version is not None:
            assert "1.3.5" in result.stdout + result.stderr
            assert "0.0.0" in result.stdout + result.stderr
        else:
            assert "bun" in (result.stdout + result.stderr).lower()
