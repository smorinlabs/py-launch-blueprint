"""Tests for the core library layer (pure, no CLI)."""

import logging
from pathlib import Path

from py_launch_blueprint.core import (
    Config,
    ConfigPath,
    Project,
    ProjectList,
    load_config,
    paths,
)
from py_launch_blueprint.core.config import TOKEN_ENV_VAR
from py_launch_blueprint.core.logging import LogFormat, configure_logging, get_logger


def test_project_list_renders_rows():
    result = ProjectList(
        projects=[
            Project(id="1", name="Alpha", workspace="WS"),
            Project(id="2", name="Beta", workspace=None),
        ]
    )
    assert result.table_columns() == ["Name", "Workspace", "ID"]
    rows = result.table_rows()
    assert rows[0] == ["Alpha", "WS", "1"]
    assert rows[1] == ["Beta", "-", "2"]  # None workspace becomes "-"
    assert result.table_title() == "Projects (2)"


def test_empty_project_list_has_note():
    result = ProjectList(projects=[])
    assert result.human_note() == "No projects found."


def test_project_list_json_round_trips():
    result = ProjectList(projects=[Project(id="1", name="Alpha", workspace="WS")])
    data = result.model_dump()
    assert data == {"projects": [{"id": "1", "name": "Alpha", "workspace": "WS"}]}


def test_config_path_model():
    result = ConfigPath(path="/home/u/.config/.env", exists=False)
    assert result.table_rows() == [["/home/u/.config/.env", "no"]]


def test_load_config_flag_wins(monkeypatch):
    monkeypatch.setenv(TOKEN_ENV_VAR, "env_token")
    cfg = load_config(token_override="flag_token")
    assert cfg.token == "flag_token"
    assert cfg.source == "flag"


def test_load_config_env_over_file(tmp_path, monkeypatch):
    cfg_file = tmp_path / "pylb_config.toml"
    cfg_file.write_text('token = "file_token"\n')
    monkeypatch.setenv(TOKEN_ENV_VAR, "env_token")
    cfg = load_config(config_file=str(cfg_file))
    assert cfg.token == "env_token"
    assert cfg.source == "env"


def test_load_config_file_fallback_toml(tmp_path, monkeypatch):
    cfg_file = tmp_path / "pylb_config.toml"
    cfg_file.write_text('token = "file_token"\n')
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg = load_config(config_file=str(cfg_file))
    assert cfg.token == "file_token"
    assert cfg.source == "file"


def test_load_config_file_fallback_auth_table(tmp_path, monkeypatch):
    cfg_file = tmp_path / "pylb_config.toml"
    cfg_file.write_text('[auth]\ntoken = "table_token"\n')
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg = load_config(config_file=str(cfg_file))
    assert cfg.token == "table_token"


def test_load_config_missing(monkeypatch):
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg = load_config(config_file="/nonexistent/path/.env")
    assert isinstance(cfg, Config)
    assert cfg.token is None
    assert cfg.source is None


def test_logging_configures_without_error():
    configure_logging(level=logging.DEBUG, fmt=LogFormat.JSON)
    log = get_logger("test")
    # Should not raise; bound logger supports structured kwargs.
    log.info("hello", key="value")


# -- XDG paths -----------------------------------------------------------


def test_config_file_naming_under_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert paths.config_file() == tmp_path / "pylb" / "pylb_config.toml"


def test_database_file_naming_under_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert paths.database_file() == tmp_path / "pylb" / "pylb_db.db"


def test_state_file_naming_under_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert paths.state_file("history") == tmp_path / "pylb" / "pylb_history.log"


def test_xdg_default_when_unset(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert paths.config_home() == Path.home() / ".config"


def test_xdg_relative_value_ignored(monkeypatch):
    # Spec: a non-absolute XDG value must be ignored in favor of the default.
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative/not/absolute")
    assert paths.config_home() == Path.home() / ".config"
