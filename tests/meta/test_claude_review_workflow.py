"""Credential presence controls optional Claude review without exposing it."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(os.name == "nt", reason="Review workflow runs on Ubuntu")
@pytest.mark.parametrize("credential", ["", 'synthetic-credential-$special"value'])
def test_claude_review_configuration_controls_execution(tmp_path, credential):
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/claude-code-review.yml").read_text()
    )
    job = workflow["jobs"]["claude-review"]
    configuration, checkout, review = job["steps"]
    assert configuration["env"]["CLAUDE_CODE_OAUTH_TOKEN"] == (
        "${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}"
    )
    assert "vars.CLAUDE_REVIEW_ENABLED" not in job["if"]
    assert "github.event.pull_request.head.repo.full_name" in job["if"]
    assert "github.event.pull_request.user.type != 'Bot'" in job["if"]
    assert "github.event.sender.type != 'Bot'" in job["if"]
    condition = f"steps.{configuration['id']}.outputs.configured == 'true'"
    assert checkout["if"] == condition
    assert review["if"] == condition
    assert not job.get("continue-on-error", False)
    assert not review.get("continue-on-error", False)

    output = tmp_path / "output"
    summary = tmp_path / "summary"
    output.touch()
    summary.touch()
    bash = shutil.which("bash")
    assert bash is not None
    result = subprocess.run(  # noqa: S603 — checked-in workflow, synthetic input
        [
            bash,
            "--noprofile",
            "--norc",
            "-e",
            "-o",
            "pipefail",
            "-c",
            configuration["run"],
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "CLAUDE_CODE_OAUTH_TOKEN": credential,
            "GITHUB_OUTPUT": str(output),
            "GITHUB_STEP_SUMMARY": str(summary),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_text() == f"configured={str(bool(credential)).lower()}\n"
    if credential:
        assert credential not in result.stdout + result.stderr + output.read_text()
        assert summary.read_text() == ""
    else:
        message = "Claude review is not configured; skipping.\n"
        assert result.stdout == message
        assert summary.read_text() == message
