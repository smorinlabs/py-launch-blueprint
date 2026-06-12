import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_contributors_recipe_runs_contributors_please() -> None:
    just = shutil.which("just")
    if just is None:
        pytest.skip("just is not installed in this test job")

    result = subprocess.run(  # noqa: S603
        [just, "--dry-run", "contributors"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    assert "npx contributors-please@1 init" in output
    assert "--config-file .contributors.yml" in output
