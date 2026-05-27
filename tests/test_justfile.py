from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_contributors_recipe_runs_contributors_please() -> None:
    if shutil.which("just") is None:
        pytest.skip("just is not installed in this test job")

    result = subprocess.run(
        ["just", "--dry-run", "contributors"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    assert "npx @smorinlabs/contributors-please@1 init" in output
    assert "--config-file .contributors.yml" in output
