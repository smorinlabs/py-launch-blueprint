"""Guards for the weekly-audit triage bot (workflow shape + helper logic)."""

import email.message
import importlib.util
import io
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import urllib.response
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


@pytest.fixture
def run_create_pr(tmp_path):
    """Execute the workflow shell with a recording CLI and no inherited secrets."""
    gh = tmp_path / "gh"
    gh.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "with Path(os.environ['GH_RECORD']).open('a') as record:\n"
        "    record.write(json.dumps(args) + '\\n')\n"
        "if args[:2] == ['api', 'repos/owner/repository']:\n"
        "    operation, response = 'read', 'pilot-main'\n"
        "elif args[:4] == ['api', '--method', 'POST', "
        "'repos/owner/repository/pulls']:\n"
        "    operation, response = 'create', os.environ['PR_NUMBER']\n"
        "else:\n"
        "    sys.exit('unsupported gh command')\n"
        "if operation == os.environ['FAIL_OPERATION']:\n"
        "    print('simulated API failure', file=sys.stderr)\n"
        "    sys.exit(23)\n"
        "print(response)\n"
    )
    gh.chmod(0o755)
    output = tmp_path / "output"
    record = tmp_path / "record.jsonl"

    def run(*, repository="owner/repository", fail="", number="417"):
        # Execute only the checked-in workflow in an isolated temporary directory.
        result = subprocess.run(  # noqa: S603
            [
                "/bin/bash",
                "-e",
                "-o",
                "pipefail",
                "-c",
                _step_named("Create triage PR")["run"],
            ],
            cwd=tmp_path,
            env={
                "PATH": f"{tmp_path}{os.pathsep}/usr/bin:/bin",
                "GH_REPO": "owner/repository",
                "GITHUB_REPOSITORY": repository,
                "BRANCH": "bot/weekly-audit-987654",
                "GITHUB_OUTPUT": str(output),
                "GH_RECORD": str(record),
                "FAIL_OPERATION": fail,
                "PR_NUMBER": number,
            },
            capture_output=True,
            text=True,
            check=False,
        )
        calls = [json.loads(line) for line in record.read_text().splitlines()]
        return result, calls, output.read_text() if output.exists() else ""

    return run


@pytest.mark.parametrize(
    "repository",
    [
        "owner/repository",
        'owner/repo "quoted"\\path\n$(touch evaluated)`touch evaluated`',
    ],
)
def test_create_pr_uses_rest_and_preserves_fields(run_create_pr, repository, tmp_path):
    result, calls, output = run_create_pr(repository=repository)
    assert result.returncode == 0, result.stderr
    assert calls == [
        ["api", "repos/owner/repository", "--jq", ".default_branch"],
        [
            "api",
            "--method",
            "POST",
            "repos/owner/repository/pulls",
            "--raw-field",
            "head=bot/weekly-audit-987654",
            "--raw-field",
            "base=pilot-main",
            "--raw-field",
            "title=fix(docs): triage weekly-audit run 987654",
            "--raw-field",
            "body=Triage of weekly-audit run 987654.\n\n"
            "Automated docs repair; verification table follows from the finish step.\n"
            f"Audit run: https://github.com/{repository}/actions/runs/987654",
            "--jq",
            ".number",
        ],
    ]
    assert output == "number=417\n"
    assert not (tmp_path / "evaluated").exists()


@pytest.mark.parametrize(("fail", "call_count"), [("read", 1), ("create", 2)])
def test_create_pr_propagates_api_failure(run_create_pr, fail, call_count):
    result, calls, output = run_create_pr(fail=fail)
    assert result.returncode == 23
    assert "simulated API failure" in result.stderr
    assert len(calls) == call_count
    assert output == ""


@pytest.mark.parametrize("number", ["null", "0", "-1", "abc", "417\n418"])
def test_create_pr_requires_a_positive_number(run_create_pr, number):
    result, calls, output = run_create_pr(number=number)
    assert result.returncode != 0
    assert len(calls) == 2
    assert output == ""


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


_JOB_LOG_URL = "https://api.github.com/repos/o/r/actions/jobs/106294708263/logs"
_STORAGE_URL = "https://logs.example.invalid/job.txt?signature=fixture"
# Bounded excerpt from the pilot's actual job log, including ANSI and timestamp.
_BROKEN_LINE = (
    "2026-09-21T10:14:50.0156914Z (tasks/contributing_code: line   52) "
    "\x1b[91mbroken    \x1b[39;49;00mhttps://github.com/casey/just#installation"
    "\x1b[91m - Anchor 'installation' not found\x1b[39;49;00m\n"
)
_PLAINTEXT_LOG = (
    "2026-09-21T10:14:48.0000000Z checking links\n" + _BROKEN_LINE
).encode()


@pytest.fixture
def log_transport(monkeypatch):
    """Replace HTTPS I/O while exercising urllib's real redirect processors."""
    requests = []
    reads = []
    replies = []

    class Response(io.BytesIO):
        def read(self, size=-1):
            reads.append(size)
            return super().read(size)

    class HTTPSHandler(urllib.request.HTTPSHandler):
        def https_open(self, request):
            requests.append(request)
            status, payload = replies.pop(0)
            if isinstance(payload, Exception):
                raise payload
            headers = email.message.Message()
            if status == 302:
                headers["Location"] = payload
                payload = b""
            response = urllib.response.addinfourl(
                Response(payload), headers, request.full_url, status
            )
            response.msg = "Found" if status == 302 else "OK"
            return response

    monkeypatch.setattr(urllib.request, "HTTPSHandler", HTTPSHandler)
    return replies, requests, reads


@pytest.mark.parametrize("redirect", [False, True])
@pytest.mark.parametrize("token", ["", "fixture-token"])
def test_download_plaintext_job_log_and_extract_actual_broken_line(
    log_transport, redirect, token
):
    replies, requests, reads = log_transport
    if redirect:
        replies.append((302, _STORAGE_URL))
    replies.append((200, _PLAINTEXT_LOG))
    text = audit_triage.download_logs(_JOB_LOG_URL, token)
    assert text == _PLAINTEXT_LOG.decode()
    assert audit_triage.extract_broken_lines(text) == [
        "(tasks/contributing_code: line   52) broken    "
        "https://github.com/casey/just#installation - Anchor 'installation' not found"
    ]
    assert requests[0].full_url == _JOB_LOG_URL
    assert requests[0].get_header("Authorization") == (
        f"Bearer {token}" if token else None
    )
    if redirect:
        assert requests[1].full_url == _STORAGE_URL
        assert requests[1].get_header("Authorization") is None
    assert reads == [audit_triage.MAX_LOG_BYTES + 1]
    assert not replies


@pytest.mark.parametrize("redirect", [False, True])
@pytest.mark.parametrize("payload", [b"x" * 10, b"x" * 100])
def test_download_job_log_enforces_bounded_read(log_transport, redirect, payload):
    replies, _, reads = log_transport
    if redirect:
        replies.append((302, _STORAGE_URL))
    replies.append((200, payload))
    if len(payload) > 10:
        with pytest.raises(audit_triage.RefusalError, match="size cap"):
            audit_triage.download_logs(_JOB_LOG_URL, "fixture-token", size_cap=10)
    else:
        assert audit_triage.download_logs(_JOB_LOG_URL, "", size_cap=10) == "x" * 10
    assert reads == [11]


def test_download_job_log_replaces_invalid_utf8(log_transport):
    replies, _, _ = log_transport
    replies.append((200, b"setup \xff\n" + _PLAINTEXT_LOG))
    text = audit_triage.download_logs(_JOB_LOG_URL, "")
    assert text.startswith("setup \ufffd\n")
    assert len(audit_triage.extract_broken_lines(text)) == 1


def test_download_job_log_refuses_non_https_redirect(log_transport):
    replies, requests, reads = log_transport
    replies.append((302, "http://logs.example.invalid/job.txt"))
    with pytest.raises(audit_triage.RefusalError, match="redirected off https"):
        audit_triage.download_logs(_JOB_LOG_URL, "fixture-token")
    assert len(requests) == 1
    assert reads == []


@pytest.mark.parametrize("redirect", [False, True])
@pytest.mark.parametrize(
    "error", [urllib.error.URLError("unavailable"), TimeoutError(), ValueError()]
)
def test_download_job_log_preserves_fetch_failure_paths(log_transport, redirect, error):
    replies, requests, _ = log_transport
    if redirect:
        replies.append((302, _STORAGE_URL))
    replies.append((0, error))
    message = "Log fetch failed" if redirect else "Log download failed"
    with pytest.raises(audit_triage.RefusalError, match=message):
        audit_triage.download_logs(_JOB_LOG_URL, "fixture-token")
    if redirect:
        assert requests[1].get_header("Authorization") is None
