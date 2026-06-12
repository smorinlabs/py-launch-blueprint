"""Tests for the new noun-verb `plbp` CLI (via Click's CliRunner)."""

import json
import tomllib
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from py_launch_blueprint import __version__
from py_launch_blueprint.cli.context import AppContext, maybe_show_first_run_hint
from py_launch_blueprint.cli.main import cli
from py_launch_blueprint.cli.output import OutputMode, Renderer
from py_launch_blueprint.core.config import Config
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
    # str(Path(...)) so the expectation tracks the platform separator
    assert payload["path"] == str(Path("/nope/.env"))
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


# -- context-build error boundary (review finding) --------------------------


def test_corrupt_explicit_config_renders_clean_error(runner, tmp_path, monkeypatch):
    # Errors raised while building the context (eager config load) must be
    # rendered, not tracebacked.
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text("[output\n")  # TOML syntax error in an EXPLICIT --config
    result = runner.invoke(cli, ["config", "path", "--config", str(cfg)])
    assert result.exit_code == 1  # ExitCode.CONFIG
    assert "Traceback" not in result.output
    assert "invalid TOML" in result.output


def test_corrupt_explicit_config_json_error_envelope(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text("[output\n")
    result = runner.invoke(cli, ["config", "path", "--config", str(cfg), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.output)  # structured even pre-context
    assert payload["error"]["name"] == "CONFIG"


def test_invalid_config_value_warns_on_stderr(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"
    cfg.write_text('[output]\ncolor = "yes"\n')
    result = runner.invoke(cli, ["config", "path", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "warning:" in result.output
    assert "output.color" in result.output


# -- phase 3: logging flags + file sink -------------------------------------


def test_log_file_flag_with_path(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    log = tmp_path / "run.log"
    result = runner.invoke(
        cli,
        [
            "config",
            "path",
            "--config",
            str(tmp_path / "c.toml"),
            "--log-file",
            str(log),
        ],
    )
    assert result.exit_code == 0
    assert log.exists()  # file sink was wired up


def test_log_file_flag_defaults_to_xdg_state(runner, tmp_path, monkeypatch):
    # R11.2: bare --log-file uses $XDG_STATE_HOME/plbp/plbp.log.
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    result = runner.invoke(
        cli,
        ["config", "path", "--config", str(tmp_path / "c.toml"), "--log-file"],
    )
    assert result.exit_code == 0
    assert (tmp_path / "plbp" / "plbp.log").exists()


def test_log_file_from_config(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    monkeypatch.delenv("PLBP_LOG_FILE", raising=False)
    log = tmp_path / "cfg.log"
    cfg = tmp_path / "plbp_config.toml"
    # as_posix(): backslashes would be TOML escape sequences on windows
    cfg.write_text(f'[logging]\nfile = "{log.as_posix()}"\n')
    result = runner.invoke(cli, ["config", "path", "--config", str(cfg)])
    assert result.exit_code == 0
    assert log.exists()


def test_console_level_precedence():
    import logging as stdlib_logging

    from py_launch_blueprint.cli.context import _resolve_console_level

    # --log-level beats everything, including -q (R10.4 explicit override).
    assert _resolve_console_level("debug", 0, True, "warning") == stdlib_logging.DEBUG
    # -q then -vv then -v...
    assert _resolve_console_level(None, 0, True, "warning") == stdlib_logging.ERROR
    assert _resolve_console_level(None, 2, False, "warning") == stdlib_logging.DEBUG
    assert _resolve_console_level(None, 1, False, "warning") == stdlib_logging.INFO
    # ...then the config value, then the WARNING default baked into config.
    assert _resolve_console_level(None, 0, False, "info") == stdlib_logging.INFO
    assert _resolve_console_level(None, 0, False, "warning") == stdlib_logging.WARNING


# -- logging env contracts (review findings) --------------------------------


def test_log_file_env_empty_enables_default(runner, tmp_path, monkeypatch):
    # R12: PRESENCE of PLBP_LOG_FILE enables the sink; empty value means
    # the default XDG state location.
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setenv("PLBP_LOG_FILE", "")
    result = runner.invoke(
        cli, ["config", "path", "--config", str(tmp_path / "c.toml")]
    )
    assert result.exit_code == 0
    assert (tmp_path / "plbp" / "plbp.log").exists()


def test_log_format_env_invalid_value_rejected(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    monkeypatch.setenv("PLBP_LOG_FORMAT", "yaml")
    result = runner.invoke(
        cli, ["config", "path", "--config", str(tmp_path / "c.toml")]
    )
    assert result.exit_code == 1  # ConfigError via the create() boundary
    assert "PLBP_LOG_FORMAT" in result.output


def test_log_format_env_case_insensitive(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    monkeypatch.setenv("PLBP_LOG_FORMAT", "JSON")
    log = tmp_path / "x.log"
    result = runner.invoke(
        cli,
        [
            "config",
            "path",
            "--config",
            str(tmp_path / "c.toml"),
            "--log-file",
            str(log),
        ],
    )
    assert result.exit_code == 0
    line = log.read_text().strip().splitlines()[0]
    json.loads(line)  # JSONL, not text: the env value was normalized


def test_config_get_reports_default_source(runner, tmp_path, monkeypatch):
    # A built-in default must not claim a config file provided it.
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    cfg = tmp_path / "plbp_config.toml"  # does not exist
    result = runner.invoke(
        cli, ["config", "get", "logging.level", "--config", str(cfg), "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["value"] == "warning"
    assert payload["source"] == "default"
    # ...and a file-provided value still reports "config".
    cfg.write_text('[logging]\nlevel = "info"\n')
    result = runner.invoke(
        cli, ["config", "get", "logging.level", "--config", str(cfg), "--json"]
    )
    payload = json.loads(result.output)
    assert payload["source"] == "config"


# -- did-you-mean suggestions (REC-01) -------------------------------------


def test_unknown_root_command_suggests_near_miss(runner):
    result = runner.invoke(cli, ["porjects"])
    assert result.exit_code != 0
    assert "Did you mean 'projects'?" in result.output


def test_unknown_verb_suggests_near_miss(runner):
    result = runner.invoke(cli, ["projects", "lst", "--token", "t"])
    assert result.exit_code != 0
    assert "Did you mean 'list'?" in result.output


def test_unknown_command_without_match_keeps_plain_error(runner):
    result = runner.invoke(cli, ["zzzzzzzz"])
    assert result.exit_code != 0
    assert "Did you mean" not in result.output


# -- error codes, hints, crash log (REC-02 / REC-22) -----------------------


def test_auth_error_carries_error_code_and_hint(runner, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    result = runner.invoke(
        cli, ["projects", "list", "--config", "/nope/.env", "--json"]
    )
    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["error"]["error_code"] == "PLBP002"
    assert "PLBP_TOKEN" in payload["error"]["hint"]


def test_auth_error_text_shows_hint(runner, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    result = runner.invoke(cli, ["projects", "list", "--config", "/nope/.env"])
    assert result.exit_code == 2
    assert "PLBP002" in result.output
    assert "hint:" in result.output


def test_unexpected_error_writes_crash_log(runner, mock_service, tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    mock_service.list_projects.side_effect = RuntimeError("kaboom")
    result = runner.invoke(cli, ["projects", "list", "--token", "t"])
    assert result.exit_code == 4
    assert "kaboom" in result.output
    assert "full traceback:" in result.output
    crash = tmp_path / "plbp" / "plbp_crash.log"
    assert crash.exists()
    assert "RuntimeError: kaboom" in crash.read_text()


def test_unexpected_error_json_includes_traceback_path(
    runner, mock_service, tmp_path, monkeypatch
):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    mock_service.list_projects.side_effect = RuntimeError("kaboom")
    result = runner.invoke(cli, ["projects", "list", "--token", "t", "--json"])
    assert result.exit_code == 4
    payload = json.loads(result.output)
    assert payload["error"]["error_code"] == "PLBP000"
    assert payload["error"]["traceback_path"].endswith("plbp_crash.log")


# -- config init (REC-05) ---------------------------------------------------


def test_config_init_yes_writes_current_defaults(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    target = tmp_path / "cfg.toml"
    result = runner.invoke(cli, ["config", "init", "--yes", "--config", str(target)])
    assert result.exit_code == 0
    data = tomllib.loads(target.read_text())
    assert data["output"]["format"] == "text"
    assert data["output"]["color"] == "auto"
    assert data["logging"]["level"] == "warning"


def test_config_init_prompts_and_writes_answers(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    target = tmp_path / "cfg.toml"
    result = runner.invoke(
        cli,
        ["config", "init", "--config", str(target)],
        input="json\nalways\ninfo\n",
    )
    assert result.exit_code == 0
    data = tomllib.loads(target.read_text())
    assert data["output"]["format"] == "json"
    assert data["output"]["color"] == "always"
    assert data["logging"]["level"] == "info"


def test_config_init_no_input_refuses_with_hint(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    target = tmp_path / "cfg.toml"
    result = runner.invoke(
        cli, ["config", "init", "--no-input", "--config", str(target)]
    )
    assert result.exit_code == 1
    assert "--yes" in result.output
    assert not target.exists()


def test_config_init_dry_run_writes_nothing(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("PLBP_TOKEN", raising=False)
    target = tmp_path / "cfg.toml"
    result = runner.invoke(
        cli, ["config", "init", "--yes", "--dry-run", "--config", str(target)]
    )
    assert result.exit_code == 0
    assert not target.exists()


# -- first-run hint (REC-05) -------------------------------------------------


def _hint_app(monkeypatch, tmp_path, **overrides):
    """Build an AppContext whose stderr renders as a terminal."""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    kwargs = {
        "renderer": Renderer(OutputMode.TEXT, color="always"),
        "output_mode": OutputMode.TEXT,
        "config_file": None,
        "token": None,
        "no_input": False,
        "verbose": 0,
        "quiet": False,
        "_config": Config(),
    }
    kwargs.update(overrides)
    return AppContext(**kwargs)


def test_first_run_hint_shown_once(monkeypatch, tmp_path, capsys):
    app = _hint_app(monkeypatch, tmp_path)
    maybe_show_first_run_hint(app)
    assert "config init" in capsys.readouterr().err
    maybe_show_first_run_hint(app)  # marker written -> silent now
    assert capsys.readouterr().err == ""
    assert (tmp_path / "plbp" / "plbp_first_run.marker").exists()


def test_first_run_hint_suppressed_for_scripts(monkeypatch, tmp_path, capsys):
    for overrides in ({"quiet": True}, {"no_input": True}):
        maybe_show_first_run_hint(_hint_app(monkeypatch, tmp_path, **overrides))
        assert capsys.readouterr().err == ""


def test_first_run_hint_suppressed_when_config_exists(monkeypatch, tmp_path, capsys):
    config = Config(loaded_paths=[tmp_path / "cfg.toml"])
    maybe_show_first_run_hint(_hint_app(monkeypatch, tmp_path, _config=config))
    assert capsys.readouterr().err == ""


def test_first_run_hint_json_mode_burns_nothing(monkeypatch, tmp_path, capsys):
    app = _hint_app(
        monkeypatch,
        tmp_path,
        renderer=Renderer(OutputMode.JSON, color="always"),
        output_mode=OutputMode.JSON,
    )
    maybe_show_first_run_hint(app)
    assert capsys.readouterr().err == ""
    # marker must NOT be written: the hint was never shown, so a later
    # interactive text-mode run still gets it
    assert not (tmp_path / "plbp" / "plbp_first_run.marker").exists()


def test_first_run_hint_suppressed_when_not_a_terminal(monkeypatch, tmp_path, capsys):
    app = _hint_app(
        monkeypatch, tmp_path, renderer=Renderer(OutputMode.TEXT, no_color=True)
    )
    maybe_show_first_run_hint(app)
    assert capsys.readouterr().err == ""
    # and no marker burned: the hint can still fire on a real terminal later
    assert not (tmp_path / "plbp" / "plbp_first_run.marker").exists()


# -- doctor --bundle (REC-21) -------------------------------------------------


def test_doctor_bundle_json_redacts_secrets(runner, monkeypatch):
    monkeypatch.setenv("PLBP_TOKEN", "supersecret123")
    result = runner.invoke(cli, ["doctor", "--bundle", "--json"])
    assert result.exit_code == 0
    assert "supersecret123" not in result.output
    payload = json.loads(result.output)
    assert payload["version"] == __version__
    assert payload["env"]["PLBP_TOKEN"] == "<redacted>"
    assert payload["token_present"] is True
    assert payload["token_source"] == "env"
    assert any(check["name"] == "python" for check in payload["checks"])


def test_doctor_bundle_text_summary(runner, monkeypatch):
    monkeypatch.setenv("PLBP_TOKEN", "t")
    result = runner.invoke(cli, ["doctor", "--bundle"])
    assert result.exit_code == 0
    assert "Diagnostics bundle" in result.output


def test_unexpected_context_failure_follows_crash_contract(
    runner, tmp_path, monkeypatch
):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))

    def boom(cls, **kwargs):
        raise RuntimeError("context exploded")

    monkeypatch.setattr(AppContext, "create", classmethod(boom))
    result = runner.invoke(cli, ["config", "path", "--json"])
    assert result.exit_code == 4
    payload = json.loads(result.output)
    assert payload["error"]["error_code"] == "PLBP000"
    assert payload["error"]["traceback_path"].endswith("plbp_crash.log")
    assert (tmp_path / "plbp" / "plbp_crash.log").exists()
