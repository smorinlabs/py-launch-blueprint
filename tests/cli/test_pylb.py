"""Tests for the new noun-verb `pylb` CLI (via Click's CliRunner)."""

import json
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from py_launch_blueprint import __version__
from py_launch_blueprint.cli.main import cli
from py_launch_blueprint.core.models import Project


@pytest.fixture
def runner():
    return CliRunner()


# -- root group -----------------------------------------------------------


def test_version(runner):
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
    assert "python" in result.output
    assert "platform" in result.output


def test_help_lists_nouns(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "projects" in result.output
    assert "config" in result.output


def test_completion_bash(runner):
    result = runner.invoke(cli, ["completion", "bash"])
    assert result.exit_code == 0
    assert "_PYLB_COMPLETE" in result.output


# -- projects noun --------------------------------------------------------


@pytest.fixture
def mock_service():
    with patch("py_launch_blueprint.cli.commands.projects.ProjectsService") as mock_cls:
        svc = Mock()
        svc.list_projects.return_value = [
            Project(id="1", name="Test Project", workspace="Test WS")
        ]
        svc.get_project.return_value = Project(
            id="1", name="Test Project", workspace="Test WS"
        )
        mock_cls.return_value = svc
        yield svc


def test_projects_list_human(runner, mock_service):
    result = runner.invoke(cli, ["projects", "list", "--token", "t"])
    assert result.exit_code == 0
    assert "Test Project" in result.output


def test_projects_list_json(runner, mock_service):
    result = runner.invoke(cli, ["projects", "list", "--token", "t", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["projects"][0]["name"] == "Test Project"
    assert payload["projects"][0]["id"] == "1"


def test_projects_list_markdown(runner, mock_service):
    result = runner.invoke(cli, ["projects", "list", "--token", "t", "-o", "markdown"])
    assert result.exit_code == 0
    assert "| Name | Workspace | ID |" in result.output
    assert "| --- | --- | --- |" in result.output


def test_projects_list_passes_filters(runner, mock_service):
    runner.invoke(
        cli,
        ["projects", "list", "--token", "t", "--workspace", "WS", "--limit", "5"],
    )
    mock_service.list_projects.assert_called_with(workspace="WS", limit=5)


def test_projects_get(runner, mock_service):
    result = runner.invoke(cli, ["projects", "get", "1", "--token", "t", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["projects"][0]["id"] == "1"


def test_projects_no_token_auth_error(runner, monkeypatch):
    monkeypatch.delenv("PY_TOKEN", raising=False)
    result = runner.invoke(cli, ["projects", "list", "--config", "/nope/.env"])
    assert result.exit_code == 2  # ExitCode.AUTH
    assert "No Py token" in result.output


def test_projects_no_token_auth_error_json(runner, monkeypatch):
    monkeypatch.delenv("PY_TOKEN", raising=False)
    result = runner.invoke(
        cli, ["projects", "list", "--config", "/nope/.env", "--json"]
    )
    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["error"]["code"] == 2
    assert payload["error"]["name"] == "AUTH"


# -- config noun ----------------------------------------------------------


def test_config_path(runner, monkeypatch):
    monkeypatch.delenv("PY_TOKEN", raising=False)
    result = runner.invoke(cli, ["config", "path", "--config", "/nope/.env", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["path"] == "/nope/.env"
    assert payload["exists"] is False


def test_config_get_token_masked(runner):
    result = runner.invoke(
        cli, ["config", "get", "token", "--token", "supersecret", "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["value"] == "****cret"
    assert payload["source"] == "flag"


# -- doctor ---------------------------------------------------------------


def test_doctor_human(runner, monkeypatch):
    monkeypatch.delenv("PY_TOKEN", raising=False)
    result = runner.invoke(cli, ["doctor", "--config", "/nope/pylb_config.toml"])
    assert result.exit_code == 0  # missing token is a warn, not an error
    assert "python" in result.output
    assert "config-file" in result.output


def test_doctor_json(runner, monkeypatch):
    monkeypatch.delenv("PY_TOKEN", raising=False)
    result = runner.invoke(
        cli, ["doctor", "--config", "/nope/pylb_config.toml", "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    names = {c["name"] for c in payload["checks"]}
    assert {"python", "platform", "config-file", "token"} <= names


# -- config set (mutating: dry-run + confirmation) ------------------------


def test_config_set_writes_toml(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PY_TOKEN", raising=False)
    cfg = tmp_path / "pylb_config.toml"
    result = runner.invoke(
        cli, ["config", "set", "token", "secrettoken", "--config", str(cfg)]
    )
    assert result.exit_code == 0
    assert cfg.exists()
    assert 'token = "secrettoken"' in cfg.read_text()
    assert "secrettoken" not in result.output  # value is masked in output


def test_config_set_dry_run_writes_nothing(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PY_TOKEN", raising=False)
    cfg = tmp_path / "pylb_config.toml"
    result = runner.invoke(
        cli, ["config", "set", "token", "x", "--config", str(cfg), "--dry-run"]
    )
    assert result.exit_code == 0
    assert not cfg.exists()


def test_config_set_overwrite_refused_with_no_input(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PY_TOKEN", raising=False)
    cfg = tmp_path / "pylb_config.toml"
    cfg.write_text('token = "old"\n')
    result = runner.invoke(
        cli, ["config", "set", "token", "new", "--config", str(cfg), "--no-input"]
    )
    assert result.exit_code == 1  # ExitCode.CONFIG — refused without --yes
    assert cfg.read_text() == 'token = "old"\n'  # unchanged


def test_config_set_overwrite_with_yes(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PY_TOKEN", raising=False)
    cfg = tmp_path / "pylb_config.toml"
    cfg.write_text('token = "old"\n')
    result = runner.invoke(
        cli, ["config", "set", "token", "newtoken", "--config", str(cfg), "--yes"]
    )
    assert result.exit_code == 0
    assert 'token = "newtoken"' in cfg.read_text()
