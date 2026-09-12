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
    search_path = str(bindir)
    if version is not None:
        search_path += os.pathsep + os.defpath
    result = subprocess.run(  # noqa: S603 — controlled test executables
        command,
        cwd=tmp_path,
        env={**os.environ, "PATH": search_path},
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


@pytest.mark.parametrize("line_ending", [b"\n", b"\r\n"])
def test_bun_installer_accepts_pin_line_endings(tmp_path, line_ending):
    executable = shutil.which("bash") if os.name != "nt" else None
    if executable is None:
        pytest.skip("Bash is unavailable on this platform")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    installer = scripts / "install-bun.sh"
    installer.write_bytes((ROOT / "scripts/install-bun.sh").read_bytes())
    (tmp_path / ".bun-version").write_bytes(b"1.3.5" + line_ending)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name, body in {
        "bun": "echo 1.3.5\n",
        "curl": "echo unexpected-download >&2\nexit 99\n",
    }.items():
        tool = bindir / name
        tool.write_text("#!/bin/sh\n" + body)
        tool.chmod(0o755)
    result = subprocess.run(  # noqa: S603 — copied installer with controlled tools
        [executable, str(installer)],
        cwd=tmp_path,
        env={**os.environ, "PATH": str(bindir) + os.pathsep + os.defpath},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: bun 1.3.5 already on PATH" in result.stdout
