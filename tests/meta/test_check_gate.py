"""The local `just check` gate runs its recipes in parallel without losing tests."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "run-release-tests.sh"

PASSING = (
    'import {test, expect} from "bun:test";\ntest("ok", () => expect(1).toBe(1));\n'
)
FAILING = (
    'import {test, expect} from "bun:test";\ntest("no", () => expect(1).toBe(2));\n'
)


def _recipes():
    just = shutil.which("just")
    if just is None:
        pytest.skip("just is not installed in this test job")
    dump = subprocess.run(  # noqa: S603
        [just, "--dump", "--dump-format", "json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(dump.stdout)["recipes"]


def _body(recipe):
    return " ".join(
        part if isinstance(part, str) else ""
        for line in recipe["body"]
        for part in line
    )


def test_check_runs_its_dependencies_in_parallel():
    assert "parallel" in _recipes()["check"]["attributes"]


def test_pytest_recipe_installs_the_web_extra():
    # A cold .venv without the web extra skips tests/web; under [parallel]
    # the outcome would depend on whether `typecheck` installed it first.
    assert "uv run --extra web pytest" in _body(_recipes()["test"])


def test_release_recipe_uses_the_parallel_runner():
    assert "scripts/run-release-tests.sh" in _body(_recipes()["test-release"])


def _run_runner(tmp_path, files):
    bun = shutil.which("bun")
    bash = shutil.which("bash")
    if bun is None or bash is None:
        pytest.skip("bun and bash are required to run release test files")
    for name, content in files.items():
        (tmp_path / name).write_text(content)
    return subprocess.run(  # noqa: S603
        [bash, str(RUNNER), str(tmp_path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_runner_passes_when_every_file_passes(tmp_path):
    result = _run_runner(tmp_path, {"a.test.js": PASSING, "b.test.js": PASSING})
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("failing", ["a.test.js", "b.test.js"])
def test_runner_fails_when_any_file_fails(tmp_path, failing):
    files = {"a.test.js": PASSING, "b.test.js": PASSING} | {failing: FAILING}
    result = _run_runner(tmp_path, files)
    assert result.returncode != 0, result.stdout + result.stderr


def test_runner_fails_when_no_test_files_exist(tmp_path):
    result = _run_runner(tmp_path, {})
    assert result.returncode != 0, result.stdout + result.stderr
