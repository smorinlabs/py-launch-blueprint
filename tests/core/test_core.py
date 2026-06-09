"""Tests for the core library layer (pure, no CLI)."""

import logging

from py_launch_blueprint.core import (
    Config,
    ConfigPath,
    Project,
    ProjectList,
    load_config,
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
    env_file = tmp_path / ".env"
    env_file.write_text(f"{TOKEN_ENV_VAR}=file_token")
    monkeypatch.setenv(TOKEN_ENV_VAR, "env_token")
    cfg = load_config(config_file=str(env_file))
    assert cfg.token == "env_token"
    assert cfg.source == "env"


def test_load_config_file_fallback(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(f"{TOKEN_ENV_VAR}=file_token")
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg = load_config(config_file=str(env_file))
    assert cfg.token == "file_token"
    assert cfg.source == "file"


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
