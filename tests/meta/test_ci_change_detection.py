"""The CI `changes` detector decides which jobs a pull request starts."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "owner/repo"
RELEASE_BRANCH = "release-please--branches--main--components--pkg"

BASE_FILES = {
    ".release-please-manifest.json": '{\n  ".": "1.0.0"\n}\n',
    "CHANGELOG.md": "# Changelog\n",
    "pyproject.toml": (
        '[project]\nname = "pkg"\nversion = "1.0.0"\ndependencies = ["click>=8"]\n'
    ),
    "uv.lock": (
        '[[package]]\nname = "click"\nversion = "8.0.0"\n\n'
        '[[package]]\nname = "pkg"\nversion = "1.0.0"\n'
        'source = { editable = "." }\n'
    ),
    "src/pkg/__init__.py": "",
    "docs/index.md": "# Docs\n",
    "scripts/release_commits.cjs": "module.exports = {};\n",
}

RELEASE_BUMP = {
    ".release-please-manifest.json": '{\n  ".": "1.1.0"\n}\n',
    "CHANGELOG.md": "# Changelog\n\n## 1.1.0\n\n- feat: thing\n",
    "pyproject.toml": BASE_FILES["pyproject.toml"].replace("1.0.0", "1.1.0"),
    "uv.lock": BASE_FILES["uv.lock"].replace('version = "1.0.0"', 'version = "1.1.0"'),
}


def _detect_script() -> str:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["changes"]["steps"]
    (detect,) = [step for step in steps if step.get("id") == "detect"]
    return detect["run"]


def _git(repo: Path, *args: str) -> str:
    git = shutil.which("git")
    assert git
    return subprocess.run(  # noqa: S603 — fixed git arguments in a temp repo
        [git, "-c", "commit.gpgsign=false", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write(repo: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def _run(
    tmp_path: Path,
    change: dict[str, str],
    *,
    event: str = "pull_request",
    head_ref: str = "feature",
    head_repo: str = REPOSITORY,
) -> dict[str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "ci@example.invalid")
    _git(repo, "config", "user.name", "ci")
    _write(repo, BASE_FILES)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _write(repo, change)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "change")

    output = tmp_path / "output"
    output.touch()
    bash = shutil.which("bash")
    assert bash
    env = {
        **os.environ,
        "GITHUB_OUTPUT": str(output),
        "EVENT_NAME": event,
        "BASE_SHA": base if event == "pull_request" else "",
        "HEAD_REF": head_ref if event == "pull_request" else "",
        "HEAD_REPO": head_repo if event == "pull_request" else "",
        "REPOSITORY": REPOSITORY,
    }
    result = subprocess.run(  # noqa: S603 — checked-in script, synthetic repo
        [bash, "-c", _detect_script()],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    pairs = (line.split("=", 1) for line in output.read_text().splitlines())
    return dict(pairs)


def _expect(code: str, release: str, tooling: str) -> dict[str, str]:
    return {"code": code, "release": release, "release_tooling": tooling}


pytestmark = pytest.mark.skipif(os.name == "nt", reason="CI detector runs on Ubuntu")


def test_push_runs_everything(tmp_path):
    outputs = _run(tmp_path, {"docs/index.md": "# New\n"}, event="push")
    assert outputs == _expect("true", "false", "true")


def test_docs_only_pull_request_skips_heavy_jobs(tmp_path):
    outputs = _run(tmp_path, {"docs/index.md": "# New\n"})
    assert outputs == _expect("false", "false", "false")


def test_code_pull_request_skips_release_generation(tmp_path):
    outputs = _run(tmp_path, {"src/pkg/__init__.py": "X = 1\n"})
    assert outputs == _expect("true", "false", "false")


@pytest.mark.parametrize(
    "path",
    [
        "scripts/release_commits.cjs",
        "scripts/release_please.cjs",
        "scripts/release-notes.cjs",
        "scripts/run-release-tests.sh",
        "tests/release/new.test.js",
        "package.json",
        "bun.lock",
        ".bun-version",
        "release-please-config.json",
        ".github/workflows/ci.yml",
    ],
)
def test_release_tooling_change_runs_release_generation(tmp_path, path):
    outputs = _run(tmp_path, {path: "changed\n"})
    assert outputs == _expect("true", "false", "true")


def test_release_please_version_bump_takes_the_fast_path(tmp_path):
    outputs = _run(tmp_path, RELEASE_BUMP, head_ref=RELEASE_BRANCH)
    assert outputs == _expect("false", "true", "false")


def test_release_named_branch_touching_source_runs_everything(tmp_path):
    change = {**RELEASE_BUMP, "src/pkg/__init__.py": "X = 1\n"}
    outputs = _run(tmp_path, change, head_ref=RELEASE_BRANCH)
    assert outputs == _expect("true", "false", "false")


def test_release_named_branch_with_dependency_change_runs_everything(tmp_path):
    pyproject = RELEASE_BUMP["pyproject.toml"].replace("click>=8", "click>=9")
    change = {**RELEASE_BUMP, "pyproject.toml": pyproject}
    outputs = _run(tmp_path, change, head_ref=RELEASE_BRANCH)
    assert outputs == _expect("true", "false", "false")


def test_release_named_branch_with_lock_dependency_bump_runs_everything(tmp_path):
    lock = RELEASE_BUMP["uv.lock"].replace('version = "8.0.0"', 'version = "8.1.0"')
    change = {**RELEASE_BUMP, "uv.lock": lock}
    outputs = _run(tmp_path, change, head_ref=RELEASE_BRANCH)
    assert outputs == _expect("true", "false", "false")


def test_large_non_version_edit_on_release_branch_runs_everything(tmp_path):
    # A big diff must not let an early-exiting grep SIGPIPE the pipeline
    # under pipefail and turn "found a bad line" into "release-only".
    noise = "".join(f"# filler line {i}\n" for i in range(20000))
    pyproject = RELEASE_BUMP["pyproject.toml"] + noise
    change = {**RELEASE_BUMP, "pyproject.toml": pyproject}
    outputs = _run(tmp_path, change, head_ref=RELEASE_BRANCH)
    assert outputs == _expect("true", "false", "false")


def test_large_code_diff_is_not_docs_only(tmp_path):
    change = {f"src/pkg/mod_{i}.py": "X = 1\n" for i in range(3000)}
    change["docs/index.md"] = "# New\n"
    outputs = _run(tmp_path, change)
    assert outputs == _expect("true", "false", "false")


def test_release_branch_with_extra_manifest_change_runs_everything(tmp_path):
    manifest = '{\n  ".": "1.1.0",\n  "extra": "1.0.0"\n}\n'
    change = {**RELEASE_BUMP, ".release-please-manifest.json": manifest}
    outputs = _run(tmp_path, change, head_ref=RELEASE_BRANCH)
    assert outputs == _expect("true", "false", "false")


def test_release_bump_from_a_fork_runs_everything(tmp_path):
    outputs = _run(
        tmp_path, RELEASE_BUMP, head_ref=RELEASE_BRANCH, head_repo="fork/repo"
    )
    assert outputs == _expect("true", "false", "false")


def test_release_bump_on_an_ordinary_branch_runs_everything(tmp_path):
    outputs = _run(tmp_path, RELEASE_BUMP, head_ref="feature/bump")
    assert outputs == _expect("true", "false", "false")


def test_release_named_branch_without_version_change_runs_everything(tmp_path):
    change = {"pyproject.toml": BASE_FILES["pyproject.toml"] + "# note\n"}
    outputs = _run(tmp_path, change, head_ref=RELEASE_BRANCH)
    assert outputs == _expect("true", "false", "false")


# --- workflow shape ---------------------------------------------------------

WORKFLOWS = ROOT / ".github" / "workflows"
PR_ONLY_CANCEL = "${{ github.event_name == 'pull_request' }}"


# The press [[remove]]s these from generated projects (press/press-rules.toml).
TEMPLATE_ONLY = {"bootstrap-acceptance.yml", "template-receipt-guard.yml"}


def _workflow(name: str) -> dict:
    path = WORKFLOWS / name
    if name in TEMPLATE_ONLY and not path.exists():
        # Only a pressed project (which carries a receipt) may lack them.
        assert (ROOT / "press" / "press-receipt.toml").exists(), name
        pytest.skip(f"{name} is template-only")
    return yaml.safe_load(path.read_text())


def test_ci_ok_needs_every_other_job():
    jobs = _workflow("ci.yml")["jobs"]
    assert set(jobs["ci-ok"]["needs"]) == set(jobs) - {"ci-ok"}


def test_heavy_jobs_follow_the_code_output():
    jobs = _workflow("ci.yml")["jobs"]
    code = "needs.changes.outputs.code == 'true'"
    for name in ("typecheck", "test", "test-otel"):
        assert jobs[name]["if"] == code, name
    assert jobs["build-smoke"]["if"] == (
        f"{code} || needs.changes.outputs.release == 'true'"
    )


@pytest.mark.parametrize(
    ("job", "commands"),
    [
        (
            "lint",
            [
                "uv run --no-sync ruff check .",
                "uv run --no-sync ruff format --check .",
                "taplo check '**/*.toml'",
                "bash scripts/check-shell.sh",
                "uv run --no-sync sphinx-build -W -b html docs/source docs/_build/html",
            ],
        ),
        (
            "typecheck",
            [
                "uv run --no-sync ty check src/py_launch_blueprint/",
                "uv run --no-sync lint-imports",
                "uv run --no-sync tach check",
            ],
        ),
    ],
)
def test_merged_jobs_report_every_tool(job, commands):
    steps = _workflow("ci.yml")["jobs"][job]["steps"]
    by_run = {step.get("run"): step for step in steps}
    for command in commands:
        assert command in by_run, command
        # One failing tool must not hide the others' results.
        assert by_run[command]["if"] == (
            "${{ !cancelled() && steps.setup.outcome == 'success' }}"
        )


def test_bootstrap_acceptance_skips_release_please_pull_requests():
    job = _workflow("bootstrap-acceptance.yml")["jobs"]["bootstrap-acceptance"]
    assert "startsWith(github.head_ref, 'release-please--')" in job["if"]


@pytest.mark.parametrize(
    ("workflow", "job"),
    [
        ("press-verify.yml", None),
        ("template-receipt-guard.yml", None),
        ("claude-code-review.yml", None),
        ("dependency-review.yml", None),
        ("publish-container.yml", "container-check"),
        ("ci.yml", None),
        ("lint.yml", None),
        ("codeql.yml", None),
        ("commitlint.yml", None),
        ("secret-scan.yml", None),
        ("large-file-guard.yml", None),
        ("api-contract.yml", None),
        ("bootstrap-acceptance.yml", None),
    ],
)
def test_pull_request_runs_cancel_without_cancelling_main(workflow, job):
    data = _workflow(workflow)
    owner = data["jobs"][job] if job else data
    concurrency = owner["concurrency"]
    assert "github.event.pull_request.number || github.sha" in concurrency["group"]
    assert concurrency["cancel-in-progress"] == PR_ONLY_CANCEL
