from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_must_do_infrastructure_files_exist() -> None:
    required_paths = [
        ".github/dependabot.yml",
        ".github/codeql/codeql-config.yml",
        ".editorconfig",
        ".editorconfig-checker.json",
        ".yamllint",
        ".gitleaks.toml",
        ".gitleaksignore",
        "scripts/check-gitleaks.sh",
        "scripts/install-gitleaks.sh",
        ".devcontainer/devcontainer.json",
        "AGENTS.md",
        "LICENSE",
        "CHANGELOG.md",
        ".pypirc.template",
    ]

    missing = [path for path in required_paths if not (ROOT / path).exists()]

    assert missing == []


def test_pyproject_uses_uv_build_and_shared_tool_config() -> None:
    pyproject = read("pyproject.toml")

    assert 'version = "0.0.1"' in pyproject
    assert 'license = "MIT"' in pyproject
    assert 'license-files = ["LICENSE"]' in pyproject
    assert 'requires = ["uv_build>=' in pyproject
    assert 'build-backend = "uv_build"' in pyproject
    assert "[tool.uv.build-backend]" in pyproject
    assert 'module-name = "py_launch_blueprint"' in pyproject
    assert 'module-root = ""' in pyproject
    assert "[project.urls]" in pyproject
    assert 'Repository = "https://github.com/smorin/py-launch-blueprint"' in pyproject
    assert "[tool.codespell]" in pyproject
    assert "hatchling" not in pyproject
    assert "setuptools_scm" not in pyproject


def test_ci_workflow_contains_missing_quality_security_jobs() -> None:
    ci = read(".github/workflows/ci.yaml").lower()

    for marker in [
        "actionlint",
        "trufflehog",
        "yamllint",
        "codespell",
        "editorconfig-checker",
    ]:
        assert marker in ci


def test_release_workflow_builds_with_uv_and_uses_trusted_publishing() -> None:
    release = read(".github/workflows/release.yml")

    assert "uv build" in release
    assert "uv run hatch build" not in release
    assert "Upload distribution artifacts" in release
    assert "publish-testpypi:" in release
    assert "publish-pypi:" in release
    assert "uv publish --trusted-publishing always" in release
    assert "id-token: write" in release


def test_changelog_workflow_uses_cog_without_commit_check() -> None:
    changelog_workflow = read(".github/workflows/changelog.yml")
    cog_config = read("cog.toml")

    assert "cocogitto/cocogitto-action@v3" in changelog_workflow
    assert "check: false" in changelog_workflow
    assert "github.event.pull_request.head.sha" in changelog_workflow
    assert "cog changelog HEAD~1..HEAD > /tmp/CHANGELOG.md" in changelog_workflow
    assert "git diff --exit-code -- CHANGELOG.md" not in changelog_workflow
    assert 'git commit -m "chore: update changelog"' not in changelog_workflow
    assert "[changelog]" in cog_config
    assert "[changelog.sections]" not in cog_config
    assert "[changelog.git]" not in cog_config
    assert "[contributors]" not in cog_config


def test_onboarding_and_secret_files_are_template_safe() -> None:
    devcontainer = json.loads(read(".devcontainer/devcontainer.json"))
    pypirc = read(".pypirc.template")
    gitignore = read(".gitignore")
    agents = read("AGENTS.md")
    gitleaks = read(".gitleaks.toml")

    assert (
        devcontainer["image"] == "mcr.microsoft.com/devcontainers/python:3.10-bookworm"
    )
    assert ".pypirc" in gitignore
    assert "REPLACE_WITH_PYPI_TOKEN" in pypirc
    assert "REPLACE_WITH_TESTPYPI_TOKEN" in pypirc
    assert "CLAUDE.md" in agents
    assert "just check" in agents
    assert "doxa" not in agents.lower()
    assert re.search(r"\[extend\]\s+useDefault = true", gitleaks)
