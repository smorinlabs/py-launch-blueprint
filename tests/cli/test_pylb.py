"""Tests for the new noun-verb `plbp` CLI (via Click's CliRunner)."""

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
    assert "_PLBP_COMPLETE" in result.output


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
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    result = runner.invoke(cli, ["projects", "list", "--config", "/nope/.env"])
    assert result.exit_code == 2  # ExitCode.AUTH
    assert "No Py token" in result.output


def test_projects_no_token_auth_error_json(runner, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    result = runner.invoke(
        cli, ["projects", "list", "--config", "/nope/.env", "--json"]
    )
    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["error"]["code"] == 2
    assert payload["error"]["name"] == "AUTH"


# -- config noun ----------------------------------------------------------


def test_config_path(runner, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
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
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    result = runner.invoke(cli, ["doctor", "--config", "/nope/plbp_config.toml"])
    assert result.exit_code == 0  # missing token is a warn, not an error
    assert "python" in result.output
    assert "config-file" in result.output


def test_doctor_json(runner, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    result = runner.invoke(
        cli, ["doctor", "--config", "/nope/plbp_config.toml", "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    names = {c["name"] for c in payload["checks"]}
    assert {"python", "platform", "config-file", "token"} <= names


def test_config_get_setting(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text('[output]\ncolor = "always"\n')
    result = runner.invoke(
        cli, ["config", "get", "output.color", "--config", str(cfg), "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["value"] == "always"


# -- config set (nested keys; mutating: dry-run + confirmation) -----------


def test_config_set_writes_nested_table(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    result = runner.invoke(
        cli, ["config", "set", "logging.level", "info", "--config", str(cfg)]
    )
    assert result.exit_code == 0
    assert cfg.exists()
    body = cfg.read_text()
    assert "[logging]" in body
    assert 'level = "info"' in body


def test_config_set_rejects_token_key(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    result = runner.invoke(
        cli, ["config", "set", "token", "secret", "--config", str(cfg)]
    )
    assert result.exit_code != 0  # secrets are not settable keys
    assert not cfg.exists()


def test_config_set_rejects_invalid_value(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    result = runner.invoke(
        cli, ["config", "set", "output.color", "rainbow", "--config", str(cfg)]
    )
    assert result.exit_code != 0
    assert not cfg.exists()


def test_config_set_dry_run_writes_nothing(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    result = runner.invoke(
        cli,
        ["config", "set", "output.color", "never", "--config", str(cfg), "--dry-run"],
    )
    assert result.exit_code == 0
    assert not cfg.exists()


def test_config_set_overwrite_refused_with_no_input(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text('[logging]\nlevel = "warning"\n')
    result = runner.invoke(
        cli,
        ["config", "set", "logging.level", "info", "--config", str(cfg), "--no-input"],
    )
    assert result.exit_code == 1  # refused: overwriting an existing value
    assert 'level = "warning"' in cfg.read_text()  # unchanged


def test_config_set_overwrite_with_yes(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text('[logging]\nlevel = "warning"\n')
    result = runner.invoke(
        cli,
        ["config", "set", "logging.level", "info", "--config", str(cfg), "--yes"],
    )
    assert result.exit_code == 0
    assert 'level = "info"' in cfg.read_text()


def test_config_set_env_var_resolution(runner, tmp_path, monkeypatch):
    # PLBP_OUTPUT resolves the --output format (R12); --json still overrides.
    monkeypatch.setenv("PLBP_OUTPUT", "json")
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text('[logging]\nlevel = "info"\n')
    result = runner.invoke(
        cli, ["config", "get", "logging.level", "--config", str(cfg)]
    )
    assert result.exit_code == 0
    # PLBP_OUTPUT=json → output is parseable JSON without passing --json.
    payload = json.loads(result.output)
    assert payload["value"] == "info"


# -- config robustness (review findings) -----------------------------------


def test_invalid_config_value_does_not_crash_commands(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text('[output]\ncolor = "yes"\n')  # invalid value
    result = runner.invoke(cli, ["config", "path", "--config", str(cfg)])
    assert result.exit_code == 0  # command works on defaults
    # ...and config set can still repair the bad value:
    result = runner.invoke(
        cli, ["config", "set", "output.color", "auto", "--config", str(cfg), "--yes"]
    )
    assert result.exit_code == 0
    assert 'color = "auto"' in cfg.read_text()


def test_config_set_refuses_corrupt_file(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text('[output\ncolor = "always"\n')  # TOML syntax error
    before = cfg.read_text()
    result = runner.invoke(
        cli, ["config", "set", "logging.level", "info", "--config", str(cfg)]
    )
    assert result.exit_code != 0
    assert cfg.read_text() == before  # nothing destroyed


# -- phase 2: output-file, format-from-config, color precedence ------------


def test_output_file_redirects_results(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    out = tmp_path / "result.json"
    result = runner.invoke(
        cli,
        ["config", "path", "--config", str(cfg), "--json", "--output-file", str(out)],
    )
    assert result.exit_code == 0
    assert result.stdout == ""  # results went to the file, not stdout
    payload = json.loads(out.read_text())
    assert payload["path"] == str(cfg)


def test_output_format_resolves_from_config(runner, tmp_path, monkeypatch):
    # R7: config supplies the format when no flag/env does.
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    monkeypatch.delenv("PLBP_OUTPUT", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text('[output]\nformat = "json"\n')
    result = runner.invoke(cli, ["config", "path", "--config", str(cfg)])
    assert result.exit_code == 0
    payload = json.loads(result.output)  # JSON without passing --json
    assert payload["exists"] is True


def test_output_flag_beats_config_format(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text('[output]\nformat = "json"\n')
    result = runner.invoke(
        cli, ["config", "path", "--config", str(cfg), "-o", "markdown"]
    )
    assert result.exit_code == 0
    assert "| Config path |" in result.output  # markdown, not JSON


def test_color_precedence_resolution(monkeypatch):
    from py_launch_blueprint.cli.context import _resolve_color

    monkeypatch.delenv("NO_COLOR", raising=False)
    assert _resolve_color(False, "auto") == "auto"
    assert _resolve_color(False, "always") == "always"
    # config "always" is overridden by NO_COLOR env (R5.5)...
    monkeypatch.setenv("NO_COLOR", "1")
    assert _resolve_color(False, "always") == "never"
    # ...and the --no-color flag overrides everything.
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert _resolve_color(True, "always") == "never"
