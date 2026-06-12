from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_update_contributors_workflow_uses_contributors_please_action() -> None:
    workflow = (ROOT / ".github/workflows/update-contributors.yml").read_text()

    assert "uses: smorinlabs/contributors-please-action@v1" in workflow
    assert "mode: pull-request" in workflow
    assert "fetch-depth: 0" in workflow
    assert "contents: write" in workflow
    assert "pull-requests: write" in workflow
    assert "issues: write" in workflow


def test_update_contributors_workflow_has_layer_one_loop_guard() -> None:
    workflow = (ROOT / ".github/workflows/update-contributors.yml").read_text()

    assert "paths-ignore:" in workflow
    assert "- CONTRIBUTORS.md" in workflow
    assert "- .contributors.jsonl" in workflow
    assert "pull_request:" not in workflow


def test_legacy_update_contributors_script_is_removed() -> None:
    workflow = (ROOT / ".github/workflows/update-contributors.yml").read_text()

    assert not (ROOT / "scripts/update_contributors.py").exists()
    assert "scripts/update_contributors.py" not in workflow
    assert "peter-evans/create-pull-request" not in workflow
