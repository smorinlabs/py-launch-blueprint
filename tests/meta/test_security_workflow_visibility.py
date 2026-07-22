"""Guard visibility-aware GitHub security workflows."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
PUBLIC_REPOSITORY_CONDITION = "${{ github.event.repository.private == false }}"


def _job_block(workflow: str, job_name: str) -> str:
    """Return one top-level job block from a workflow's raw YAML."""
    marker = f"  {job_name}:\n"
    start = workflow.index(marker)
    remainder = workflow[start + len(marker) :]
    next_job_offsets = [
        offset
        for offset, line in enumerate(remainder.splitlines(keepends=True))
        if line.startswith("  ") and not line.startswith("    ")
    ]
    if not next_job_offsets:
        return remainder

    lines = remainder.splitlines(keepends=True)
    return "".join(lines[: next_job_offsets[0]])


@pytest.mark.parametrize(
    ("workflow_name", "job_name"),
    [("codeql.yml", "analyze"), ("dependency-review.yml", "dependency-review")],
)
def test_security_workflow_jobs_skip_private_repositories(
    workflow_name: str, job_name: str
) -> None:
    """Unavailable GitHub security products must not fail private repos."""
    workflow = (WORKFLOW_DIR / workflow_name).read_text(encoding="utf-8")

    assert f"    if: {PUBLIC_REPOSITORY_CONDITION}\n" in _job_block(workflow, job_name)


def test_codeql_runs_when_repository_becomes_public() -> None:
    """The visibility change must trigger the first public CodeQL scan."""
    workflow = (WORKFLOW_DIR / "codeql.yml").read_text(encoding="utf-8")
    triggers = workflow.split("\non:\n", maxsplit=1)[1].split(
        "\npermissions:", maxsplit=1
    )[0]

    assert "\n  public:\n" in triggers
