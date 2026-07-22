"""Guard visibility-aware GitHub security workflows."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
PULL_REQUEST_PUBLIC_CONDITION = "${{ github.event.repository.visibility == 'public' }}"
CODEQL_PUBLIC_CONDITION = (
    "${{ needs.repository-visibility.outputs.is-public == 'true' }}"
)


def _job_block(workflow: str, job_name: str) -> str:
    """Return one top-level job block from a workflow's raw YAML."""
    marker = f"  {job_name}:\n"
    _, separator, remainder = workflow.partition(marker)
    assert separator, f"workflow job {job_name!r} was not found"
    next_job_offsets = [
        offset
        for offset, line in enumerate(remainder.splitlines(keepends=True))
        if line.startswith("  ") and not line.startswith("    ")
    ]
    if not next_job_offsets:
        return remainder

    lines = remainder.splitlines(keepends=True)
    return "".join(lines[: next_job_offsets[0]])


def test_dependency_review_skips_private_repositories() -> None:
    """Dependency Review must not fail private pull requests."""
    workflow = (WORKFLOW_DIR / "dependency-review.yml").read_text(encoding="utf-8")

    assert f"    if: {PULL_REQUEST_PUBLIC_CONDITION}\n" in _job_block(
        workflow, "dependency-review"
    )


def test_codeql_uses_trigger_independent_repository_visibility() -> None:
    """CodeQL must gate every trigger, including schedule, on API visibility."""
    workflow = (WORKFLOW_DIR / "codeql.yml").read_text(encoding="utf-8")
    visibility_job = _job_block(workflow, "repository-visibility")
    analyze_job = _job_block(workflow, "analyze")

    assert 'gh api "repos/${REPOSITORY}"' in visibility_job
    assert "    needs: repository-visibility\n" in analyze_job
    assert f"    if: {CODEQL_PUBLIC_CONDITION}\n" in analyze_job


def test_codeql_runs_when_repository_becomes_public() -> None:
    """The visibility change must trigger the first public CodeQL scan."""
    workflow = (WORKFLOW_DIR / "codeql.yml").read_text(encoding="utf-8")
    _, on_separator, after_on = workflow.partition("\non:\n")
    assert on_separator, "codeql.yml has no top-level on block"
    triggers, permissions_separator, _ = after_on.partition("\npermissions:")
    assert permissions_separator, "codeql.yml has no top-level permissions block"

    assert "\n  public:\n" in triggers
