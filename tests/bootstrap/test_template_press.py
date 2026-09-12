"""Live acceptance: press committed template content, then use the new project.

Run with ``uv run --locked --extra web pytest tests/bootstrap -m live -s``.
Requires the native toolchain and network access for dependency regeneration.
No GitHub repository is created; the local origin models a template instance.
"""

from __future__ import annotations

import io
import json
import os
import shlex
import shutil
import socket
import subprocess
import tarfile
import time
import tomllib
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.live
IDENTITY = {
    "package_name": "harbor_sample",
    "repo_name": "harbor-sample",
    "app_name": "harborctl",
    "owner": "example-labs",
    "author": "Example Maintainer",
    "email": "maintainer@example.org",
    "display_name": "Harbor Sample",
}


def _run(cwd, *command):
    print(f"\n{cwd}\n$ {shlex.join(command)}", flush=True)
    result = subprocess.run(  # noqa: S603 — explicit acceptance commands
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
    )
    print(result.stdout + result.stderr, flush=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def _toml(path):
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _snapshot(target):
    return {
        str(path.relative_to(target)): path.read_bytes()
        for base in ("src", "tests")
        for path in (target / base).rglob("*")
        if path.is_file()
    }


# A complete bootstrap includes dependency regeneration and another test suite.
@pytest.mark.timeout(300)
def test_committed_blueprint_generates_a_usable_project(tmp_path):
    executables = {name: shutil.which(name) for name in ("git", "uv", "just")}
    assert all(executables.values()), executables
    git, uv, just = (executables[name] for name in executables)
    press = (uv, "run", "--locked", "--extra", "web", "--project", str(ROOT), "press")
    target = tmp_path / IDENTITY["repo_name"]
    target.mkdir()
    source_commit = _run(ROOT, git, "rev-parse", "HEAD").strip()
    archive = subprocess.run(  # noqa: S603 — fixed Git archive invocation
        [git, "archive", "--format=tar", source_commit],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        source.extractall(target, filter="data")
    _run(target, git, "init", "--initial-branch=main")
    _run(target, git, "config", "user.name", "Bootstrap Acceptance")
    _run(target, git, "config", "user.email", "acceptance@example.org")
    _run(target, git, "add", "--all")
    _run(target, git, "commit", "-m", "test: instantiate committed blueprint")
    _run(
        target,
        git,
        "remote",
        "add",
        "origin",
        f"https://github.com/{IDENTITY['owner']}/{IDENTITY['repo_name']}.git",
    )

    # Git cleanup must retain tracked files, even if an ignore pattern matches.
    tracked = target / "tests/__pycache__/tracked-control.pyc"
    tracked.parent.mkdir(exist_ok=True)
    tracked.write_bytes(b"tracked control\n")
    future_plan = target / "projects/P08-acceptance-control.md"
    future_plan.write_text("# Independent planning record\n", encoding="utf-8")
    _run(target, git, "add", "--force", str(tracked.relative_to(target)))
    _run(target, git, "add", str(future_plan.relative_to(target)))
    _run(target, git, "commit", "-m", "test: add tracked cleanup control")
    ignored = target / "src/py_launch_blueprint/__pycache__/ignored-control.pyc"
    ignored.parent.mkdir(exist_ok=True)
    ignored.write_bytes(b"ignored control\n")
    unignored = target / "tests/local-control.txt"
    unignored.write_bytes(b"unignored control\n")
    before = _snapshot(target)
    _run(target, *press, "check-tools", "--target", ".")
    _run(target, *press, "clean", "--target", ".", "--show")
    assert _snapshot(target) == before
    _run(target, *press, "clean", "--target", ".")
    assert not ignored.exists()
    assert tracked.read_bytes() == b"tracked control\n"
    assert unignored.read_bytes() == b"unignored control\n"
    assert _snapshot(target) == {
        path: data
        for path, data in before.items()
        if path != str(ignored.relative_to(target))
    }
    unignored.unlink()
    _run(target, git, "rm", str(tracked.relative_to(target)))
    _run(target, git, "commit", "-m", "test: finish cleanup controls")

    answers = tmp_path / "answers.toml"
    answers.write_text(
        "[answers]\n"
        + "".join(f"{key} = {json.dumps(value)}\n" for key, value in IDENTITY.items()),
        encoding="utf-8",
    )
    _run(
        target,
        *press,
        "rebrand",
        "--target",
        ".",
        "--config",
        str(answers),
        "--dry-run",
    )
    assert not _run(target, git, "status", "--porcelain")
    _run(target, *press, "rebrand", "--target", ".", "--config", str(answers))

    receipt = _toml(target / "press/press-receipt.toml")["press"]
    assert receipt["verified"] is True
    assert receipt["from"] == _toml(ROOT / "press/press-source.toml")["identity"]
    assert receipt["to"] == IDENTITY
    assert set(receipt["origin_named_destination"]) == {"owner", "repo_name"}
    assert _toml(target / "press/press-source.toml")["identity"] == IDENTITY
    assert _toml(target / "pyproject.toml")["project"]["version"] == "0.1.0"
    assert json.loads((target / ".release-please-manifest.json").read_text()) == {
        ".": "0.1.0"
    }
    expected_release = json.loads((ROOT / "release-please-config.json").read_text())
    expected_release.pop("bootstrap-sha", None)
    expected_release["packages"]["."]["package-name"] = IDENTITY["package_name"]
    assert json.loads((target / "release-please-config.json").read_text()) == (
        expected_release
    )
    editable = [
        p
        for p in _toml(target / "uv.lock")["package"]
        if p.get("source") == {"editable": "."}
    ]
    assert len(editable) == 1 and editable[0]["version"] == "0.1.0"
    assert not (target / "src/py_launch_blueprint").exists()
    assert (target / "src/harbor_sample").is_dir()
    for removed in (
        "research",
        "docs/research",
        "docs/superpowers",
        "prototypes/press_tui",
        ".claude/skills/new-python-project/SKILL.md",
        "tests/bootstrap",
        "tests/meta/test_bootstrap_skill.py",
    ):
        assert not (target / removed).exists(), removed
    assert (target / ".agents/skills/new-python-project").is_dir()
    assert not (target / "projects").exists()
    for page, stub in (
        ("docs/source/index.md", "docs-index.md"),
        ("docs/source/about/philosophy.md", "project-philosophy.md"),
        ("docs/source/tutorials/full_project_setup.md", "application-setup.md"),
        ("docs/skills/new-python-project.md", "bootstrap-provenance.md"),
    ):
        assert (target / page).read_text() == (
            target / "press/stubs" / stub
        ).read_text()
    provenance = target / "docs/skills/new-python-project.md"
    for link in ("../../press/press-receipt.toml", "../PROJECT_SETUP.md"):
        assert f"]({link})" in provenance.read_text()
        assert (provenance.parent / link).is_file()
    for pointer in ("README.md", "docs/POST_INIT.md"):
        assert "PROJECT_SETUP.md" in (target / pointer).read_text()
    assert (target / "docs/PROJECT_SETUP.md").is_file()
    design = (target / "docs/source/about/design_decisions.md").read_text()
    assert "Rebranding retires the executable skill" in design
    assert ".claude/skills/new-python-project/SKILL.md" not in design
    assert (target / ".claude/skills/new-python-project/README.md").is_file()
    assert (target / "press/stubs/readme.md").read_text() == (
        target / "README.md"
    ).read_text()

    _run(target, uv, "run", "--locked", "ruff", "format", ".")
    _run(target, just, "setup")
    assert [p.name for p in (target / "projects").iterdir()] == [".gitkeep"]
    _run(target, git, "add", "--all")
    _run(target, git, "diff", "--cached", "--check")
    _run(target, just, "check")
    _run(target, uv, "run", "--locked", "press", "verify", "--target", ".")
    _run(target, uv, "lock", "--check")
    docs_output = tmp_path / "generated-docs"
    _run(
        target,
        uv,
        "run",
        "--locked",
        "--group",
        "docs",
        "--extra",
        "web",
        "sphinx-build",
        "-W",
        "-b",
        "html",
        "docs/source",
        str(docs_output),
    )
    home_page = (docs_output / "index.html").read_text(encoding="utf-8")
    assert "Application documentation" in home_page
    assert "Production-Ready Python Project Template" not in home_page
    tutorial = (docs_output / "tutorials/full_project_setup.html").read_text(
        encoding="utf-8"
    )
    assert "Application setup" in tutorial
    assert "Set up the development environment" in tutorial
    assert "end-to-end setup of a new project" not in tutorial
    _run(target, uv, "build")
    assert list((target / "dist").glob("harbor_sample-0.1.0-*.whl"))
    assert list((target / "dist").glob("harbor_sample-0.1.0.tar.gz"))
    help_output = _run(target, uv, "run", "--locked", "harborctl", "--help")
    assert "harborctl" in help_output
    assert "0.1.0" in _run(target, uv, "run", "--locked", "harborctl", "--version")

    # Exercise the installed web entry point over a real loopback HTTP socket.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    python = (
        target / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    with (tmp_path / "web.log").open("w+") as log:
        server = subprocess.Popen(  # noqa: S603 — local generated app
            [
                str(python),
                "-m",
                "uvicorn",
                "harbor_sample.web.app:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--timeout-graceful-shutdown",
                "5",
            ],
            cwd=target,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                assert server.poll() is None, "web server exited before readiness"
                try:
                    with urlopen(
                        f"http://127.0.0.1:{port}/healthz", timeout=1
                    ) as response:
                        health = json.load(response)
                    break
                except (URLError, TimeoutError):
                    time.sleep(0.1)
            else:
                pytest.fail("web server did not become ready")
            assert health["status"] == "ok"
            assert health["version"] == "0.1.0"
            print(f"PASS: generated CLI and web health {health}", flush=True)
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            log.seek(0)
            print(log.read(), flush=True)
    print(f"PASS: source {source_commit}; generated project {target}", flush=True)
