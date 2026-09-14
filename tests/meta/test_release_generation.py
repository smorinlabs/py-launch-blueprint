"""The release regression job must reach the existing required CI gate."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("release_result", "expected"),
    [("success", 0), ("skipped", 0), ("failure", 1), ("cancelled", 1)],
)
def test_release_result_reaches_required_gate(release_result, expected):
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    jobs = workflow["jobs"]
    gate = jobs["ci-ok"]
    assert "release-generation" in gate["needs"]
    assert gate["if"] == "always()"
    release = jobs["release-generation"]
    assert release["if"] == "needs.changes.outputs.code == 'true'"
    assert any(step.get("run") == "bun test tests/release" for step in release["steps"])
    step = gate["steps"][0]
    assert step["env"]["RESULTS"] == "${{ join(needs.*.result, ' ') }}"
    results = " ".join(
        release_result if name == "release-generation" else "success"
        for name in gate["needs"]
    )
    bash = shutil.which("bash")
    assert bash
    result = subprocess.run(  # noqa: S603 — checked-in script, synthetic results
        [bash, "-c", step["run"]],
        cwd=ROOT,
        env={**os.environ, "RESULTS": results},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == expected, result.stdout + result.stderr
