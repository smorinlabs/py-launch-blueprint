"""Guards for the weekly-audit triage bot (workflow shape + helper logic)."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/audit-triage.yml").read_text())

_spec = importlib.util.spec_from_file_location(
    "audit_triage", ROOT / ".github/scripts/audit_triage.py"
)
audit_triage = importlib.util.module_from_spec(_spec)
sys.modules["audit_triage"] = audit_triage
_spec.loader.exec_module(audit_triage)


def _job():
    return WORKFLOW["jobs"]["triage"]


def _step_named(name):
    return next(s for s in _job()["steps"] if s["name"] == name)


def test_triage_job_gates_automatic_schedule_failures_only():
    condition = _job()["if"]
    assert "vars.MUSE_CI_ENABLED == 'true'" in condition
    assert "owner.type == 'Organization'" in condition
    assert "github.event_name == 'workflow_dispatch'" in condition
    assert "github.event.workflow_run.conclusion == 'failure'" in condition
    assert "github.event.workflow_run.event == 'schedule'" in condition
    assert "github.event.workflow_run.event == 'schedule'" in condition


def test_triage_job_permissions_are_minimal():
    assert _job()["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
        "actions": "read",
    }


def test_muse_credential_is_scoped_to_agent_and_presence_check():
    holders = {
        "Diagnose and repair with Muse Spark",
        "Check Meta credential is configured",
    }
    for step in _job()["steps"]:
        env = step.get("env", {})
        if step["name"] in holders:
            assert env["META_MUSE_CI_API_KEY"] == "${{ secrets.META_MUSE_CI_API_KEY }}"
        else:
            assert "META_MUSE_CI_API_KEY" not in env, step["name"]


def test_no_step_continues_on_error():
    for step in _job()["steps"]:
        assert not step.get("continue-on-error", False), step["name"]


def test_finish_reports_even_when_the_agent_fails():
    finish = _step_named("Verify scope and touched URLs")
    assert finish["if"] == "always() && steps.prepare.outputs.should_run == 'true'"


def test_agent_prompt_passes_through_the_environment():
    agent = _step_named("Diagnose and repair with Muse Spark")
    assert agent["env"]["TRIAGE_PROMPT"] == "${{ steps.prepare.outputs.prompt }}"
    assert '"$TRIAGE_PROMPT"' in agent["run"]


def test_dispatch_input_reaches_shell_through_the_environment():
    resolve = _step_named("Validate target run and resolve audited commit")
    assert resolve["env"]["DISPATCH_RUN_ID"] == "${{ inputs.run_id }}"
    assert "inputs.run_id" not in resolve["run"]
    assert 'case "$DISPATCH_RUN_ID" in' in resolve["run"]


def test_broken_line_extraction_strips_ansi_and_timestamps():
    log = (
        "2026-09-21T10:14:50.01Z (tools/x: line 1) \x1b[91mbroken    \x1b[39;49;00m"
        "https://example.invalid/dead - 404 Client Error\n"
        "2026-09-21T10:14:50.02Z (tools/x: line 2) \x1b[32mok        \x1b[39;49;00m"
        "https://example.invalid/ok\n"
    )
    (broken,) = audit_triage.extract_broken_lines(log)
    assert broken.startswith("(tools/x")
    assert "\x1b" not in broken
    assert not broken.startswith("2026-")


def test_touched_urls_reads_added_lines_only():
    diff = (
        "+++ b/docs/a.md\n"
        "--- a/docs/a.md\n"
        "+see [x](https://example.invalid/one) and https://example.invalid/two.\n"
        "-old https://example.invalid/gone\n"
        "+again https://example.invalid/one\n"
    )
    assert audit_triage.touched_urls(diff) == [
        "https://example.invalid/one",
        "https://example.invalid/two",
    ]


@pytest.mark.parametrize(
    ("paths", "allowed"),
    [
        (["docs/a.md", "docs/source/conf.py"], True),
        (["docs/a.md", "src/x.py"], False),
        (["/etc/passwd"], False),
        (["docs/../pyproject.toml"], False),
        ([""], False),
    ],
)
def test_docs_scope_enforcement(paths, allowed):
    assert audit_triage.scope_ok(paths) is allowed


@pytest.mark.parametrize(
    ("code", "verdict"),
    [
        (200, "pass"),
        (301, "warn"),
        (403, "warn"),
        (404, "fail"),
        (410, "fail"),
        (500, "warn"),
    ],
)
def test_verdict_mapping(code, verdict):
    assert audit_triage.verdict_for_status(code)[0] == verdict


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "https://169.254.169.254/latest",
        "http://10.0.0.5/x",
        "https://user:pass@example.invalid/",
        "ftp://example.invalid/x",
        "https://nonexistent.invalid/",
    ],
)
def test_non_public_targets_are_refused(url):
    with pytest.raises(audit_triage.RefusalError):
        audit_triage.assert_public_url(url)


def test_public_literal_ip_is_allowed():
    audit_triage.assert_public_url("https://93.184.216.34/")


class _FakeAPI:
    def __init__(self, runs):
        self.runs = runs

    def get(self, path):
        return self.runs[path]


def _run(**overrides):
    base = {
        "id": 1,
        "name": "weekly-audit",
        "conclusion": "failure",
        "head_branch": "main",
        "head_sha": "abc",
        "event": "schedule",
    }
    return base | overrides


def _event(run):
    return {
        "repository": {"full_name": "o/r", "default_branch": "main"},
        "workflow_run": run,
    }


def test_automatic_path_accepts_failed_schedule_runs():
    run = audit_triage.resolve_target_run(
        _FakeAPI({}), _event(_run()), "workflow_run", "o/r"
    )
    assert run["id"] == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "ci"},
        {"conclusion": "success"},
        {"head_branch": "feat"},
        {"event": "workflow_dispatch"},
        {"event": "push"},
    ],
)
def test_automatic_path_rejects_anything_else(overrides):
    with pytest.raises(audit_triage.RefusalError):
        audit_triage.resolve_target_run(
            _FakeAPI({}), _event(_run(**overrides)), "workflow_run", "o/r"
        )


def test_dispatch_path_accepts_schedule_and_manual_failures():
    for event in ("schedule", "workflow_dispatch"):
        api = _FakeAPI({"repos/o/r/actions/runs/9": _run(id=9, event=event)})
        event_payload = {
            "repository": {"full_name": "o/r", "default_branch": "main"},
            "inputs": {"run_id": "9"},
        }
        run = audit_triage.resolve_target_run(
            api, event_payload, "workflow_dispatch", "o/r"
        )
        assert run["id"] == 9


@pytest.mark.parametrize("run_id", ["x", "", "1;id", "-5"])
def test_dispatch_path_rejects_non_numeric_run_ids(run_id):
    event_payload = {
        "repository": {"full_name": "o/r", "default_branch": "main"},
        "inputs": {"run_id": run_id},
    }
    with pytest.raises(audit_triage.RefusalError):
        audit_triage.resolve_target_run(
            _FakeAPI({}), event_payload, "workflow_dispatch", "o/r"
        )


def test_agent_profile_is_docs_only_and_locked_down():
    profile = json.loads((ROOT / ".opencode/audit-triage/triage.json").read_text())
    assert profile["default_agent"] == "muse-triage"
    assert profile["permission"]["*"] == "deny"
    assert profile["permission"]["edit"] == {"*": "deny", "docs/*": "allow"}
    assert profile["permission"]["read"] == {"*": "deny", "docs/*": "allow"}
    assert profile["enabled_providers"] == ["model_api"]


def test_policy_pins_model_and_organization():
    policy = json.loads((ROOT / ".opencode/audit-triage/policy.json").read_text())
    assert policy["schema_version"] == 1
    assert policy["model"] == audit_triage.MODEL == "model_api/muse-spark-1.3"
    assert policy["organization"] == "smorinlabs"
