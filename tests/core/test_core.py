"""Tests for the core library layer (pure, no CLI)."""

import logging
import sys
from pathlib import Path

import pytest

from py_launch_blueprint.core import (
    Config,
    ConfigPath,
    Project,
    ProjectList,
    load_config,
    paths,
)
from py_launch_blueprint.core.config import (
    TOKEN_ENV_VAR,
    get_file_value,
    set_config_value,
)
from py_launch_blueprint.core.errors import ConfigError
from py_launch_blueprint.core.logging import LogFormat, configure_logging, get_logger
from py_launch_blueprint.core.settings import writable_keys


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


def test_token_never_read_from_file(tmp_path, monkeypatch):
    # R8: a token in the config file is ignored — secrets are flag/env only.
    cfg_file = tmp_path / "plbp_config.toml"
    cfg_file.write_text('token = "file_token"\n')
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg = load_config(config_file=str(cfg_file))
    assert cfg.token is None
    assert cfg.source is None


def test_load_config_missing(monkeypatch):
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg = load_config(config_file="/nonexistent/path/plbp_config.toml")
    assert isinstance(cfg, Config)
    assert cfg.token is None
    assert cfg.source is None


def test_settings_parsed_from_file(tmp_path, monkeypatch):
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg_file = tmp_path / "plbp_config.toml"
    cfg_file.write_text('[output]\ncolor = "always"\n[logging]\nlevel = "info"\n')
    cfg = load_config(config_file=str(cfg_file))
    assert cfg.settings.output.color == "always"
    assert cfg.settings.logging.level == "info"
    assert cfg.settings.output.format == "text"  # default for unset keys


def test_settings_defaults_when_no_file(monkeypatch):
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg = load_config(config_file="/nonexistent/plbp_config.toml")
    assert cfg.settings.output.format == "text"
    assert cfg.settings.output.color == "auto"
    assert cfg.settings.logging.level == "warning"


def test_set_config_value_writes_nested_table(tmp_path):
    cfg_file = tmp_path / "plbp_config.toml"
    set_config_value(cfg_file, "logging.level", "info")
    set_config_value(cfg_file, "output.color", "always")
    assert get_file_value(cfg_file, "logging.level") == "info"
    assert get_file_value(cfg_file, "output.color") == "always"
    # Re-loading reflects the written values.
    cfg = load_config(config_file=str(cfg_file))
    assert cfg.settings.logging.level == "info"
    assert cfg.settings.output.color == "always"


def test_set_config_value_rejects_unknown_key(tmp_path):
    cfg_file = tmp_path / "plbp_config.toml"
    with pytest.raises(ConfigError):
        set_config_value(cfg_file, "logging.nope", "x")
    with pytest.raises(ConfigError):
        set_config_value(cfg_file, "token", "secret")  # secrets not settable


def test_set_config_value_rejects_invalid_value(tmp_path):
    cfg_file = tmp_path / "plbp_config.toml"
    with pytest.raises(ConfigError):
        set_config_value(cfg_file, "output.color", "rainbow")


def test_writable_keys_excludes_secrets():
    keys = writable_keys()
    assert "output.color" in keys
    assert "logging.file_level" in keys
    assert "token" not in keys


def test_logging_configures_without_error():
    configure_logging(level=logging.DEBUG, fmt=LogFormat.JSON)
    log = get_logger("test")
    # Should not raise; bound logger supports structured kwargs.
    log.info("hello", key="value")


# -- XDG paths -----------------------------------------------------------


def test_config_file_naming_under_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert paths.config_file() == tmp_path / "plbp" / "plbp_config.toml"


def test_database_file_naming_under_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert paths.database_file() == tmp_path / "plbp" / "plbp_db.db"


def test_state_file_naming_under_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert paths.state_file("history") == tmp_path / "plbp" / "plbp_history.log"


def test_xdg_default_when_unset(monkeypatch):
    # Pin the POSIX branch: Windows defaults are covered in test_paths.py.
    monkeypatch.setattr(paths, "_WINDOWS", False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert paths.config_home() == Path.home() / ".config"


def test_xdg_relative_value_ignored(monkeypatch):
    # Spec: a non-absolute XDG value must be ignored in favor of the default.
    monkeypatch.setattr(paths, "_WINDOWS", False)
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative/not/absolute")
    assert paths.config_home() == Path.home() / ".config"


# -- config robustness (review findings) -----------------------------------


def test_invalid_value_warns_and_defaults(tmp_path, monkeypatch):
    # An invalid setting value must never brick loading: dropped + warned.
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg_file = tmp_path / "plbp_config.toml"
    cfg_file.write_text('[output]\ncolor = "yes"\nformat = "json"\n')
    cfg = load_config(config_file=str(cfg_file))
    assert cfg.settings.output.color == "auto"  # invalid value -> default
    assert cfg.settings.output.format == "json"  # valid sibling survives
    assert any("output.color" in w for w in cfg.warnings)


def test_explicit_config_invalid_toml_raises(tmp_path, monkeypatch):
    # --config naming an unparsable file is a loud user error (not ignored).
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg_file = tmp_path / "plbp_config.toml"
    cfg_file.write_text('[output\ncolor = "always"\n')  # unclosed table
    with pytest.raises(ConfigError):
        load_config(config_file=str(cfg_file))


def test_explicit_config_missing_is_tolerated(tmp_path, monkeypatch):
    # A missing explicit file stays fine: it's the target `config set` creates.
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    cfg = load_config(config_file=str(tmp_path / "nope.toml"))
    assert cfg.settings.output.format == "text"
    assert cfg.warnings == []


def test_set_config_value_refuses_corrupt_file(tmp_path):
    # Never silently rewrite a corrupt config (would destroy user settings).
    cfg_file = tmp_path / "plbp_config.toml"
    cfg_file.write_text('[output\ncolor = "always"\n')  # corrupt
    before = cfg_file.read_text()
    with pytest.raises(ConfigError):
        set_config_value(cfg_file, "logging.level", "info")
    assert cfg_file.read_text() == before  # untouched


def test_set_config_value_restricts_permissions(tmp_path):
    cfg_file = tmp_path / "plbp_config.toml"
    set_config_value(cfg_file, "output.color", "never")
    if sys.platform != "win32":  # POSIX modes don't exist on windows
        assert (cfg_file.stat().st_mode & 0o777) == 0o600


# -- vocabulary single-sourcing guards (review findings) ---------------------


def test_log_level_vocabularies_stay_in_sync():
    # The settings Literal and LOG_LEVELS must agree; the click choices
    # derive from LOG_LEVELS directly.
    from typing import get_args

    from py_launch_blueprint.core.logging import LOG_LEVELS
    from py_launch_blueprint.core.settings import LoggingSettings

    literal = get_args(LoggingSettings.model_fields["level"].annotation)
    assert tuple(LOG_LEVELS) == literal
    file_literal = get_args(LoggingSettings.model_fields["file_level"].annotation)
    assert tuple(LOG_LEVELS) == file_literal


def test_output_format_vocabularies_stay_in_sync():
    from typing import get_args

    from py_launch_blueprint.cli.output import OutputMode
    from py_launch_blueprint.core.settings import OutputSettings

    literal = get_args(OutputSettings.model_fields["format"].annotation)
    assert tuple(m.value for m in OutputMode) == literal


def test_write_leaves_no_temp_files(tmp_path):
    # Atomic write: only the config file remains after a set.
    cfg_file = tmp_path / "plbp_config.toml"
    set_config_value(cfg_file, "output.color", "never")
    set_config_value(cfg_file, "logging.level", "info")
    assert [p.name for p in tmp_path.iterdir()] == ["plbp_config.toml"]
    if sys.platform != "win32":  # POSIX modes don't exist on windows
        assert (cfg_file.stat().st_mode & 0o777) == 0o600
