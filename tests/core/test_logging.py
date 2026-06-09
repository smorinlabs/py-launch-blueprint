"""Tests for the dual-sink logging setup (console + rotating file)."""

import json
import logging
from logging.handlers import RotatingFileHandler

import pytest

from py_launch_blueprint.core.logging import (
    LOG_LEVELS,
    ROTATE_BACKUP_COUNT,
    ROTATE_MAX_BYTES,
    LogFormat,
    configure_logging,
    get_logger,
)


@pytest.fixture(autouse=True)
def _reset_root_logger():
    """Leave the root logger clean for other tests."""
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    root.setLevel(logging.WARNING)


def test_console_only_by_default(capsys):
    configure_logging(level=logging.WARNING, fmt=LogFormat.JSON)
    root = logging.getLogger()
    assert len(root.handlers) == 1  # no file sink unless asked for (R9.3)
    get_logger("t").warning("warned")
    assert "warned" in capsys.readouterr().err


def test_file_sink_rotation_policy(tmp_path):
    log_path = tmp_path / "plbp.log"
    configure_logging(file_path=log_path)
    file_handlers = [
        h for h in logging.getLogger().handlers if isinstance(h, RotatingFileHandler)
    ]
    assert len(file_handlers) == 1
    assert file_handlers[0].maxBytes == ROTATE_MAX_BYTES == 10 * 1024 * 1024
    assert file_handlers[0].backupCount == ROTATE_BACKUP_COUNT == 5


def test_dual_sink_independent_levels(tmp_path, capsys):
    # R11.6: console at WARNING, file at DEBUG — debug lands only in the file.
    log_path = tmp_path / "plbp.log"
    configure_logging(
        level=logging.WARNING,
        fmt=LogFormat.JSON,
        file_path=log_path,
        file_level=logging.DEBUG,
        file_format="json",
    )
    assert logging.getLogger().level == logging.DEBUG  # floor = most verbose
    log = get_logger("t")
    log.debug("debug-only")
    log.warning("both-sinks")
    err = capsys.readouterr().err
    assert "both-sinks" in err
    assert "debug-only" not in err  # console filtered it
    body = log_path.read_text()
    assert "debug-only" in body
    assert "both-sinks" in body


def test_file_sink_json_is_jsonl(tmp_path):
    log_path = tmp_path / "plbp.log"
    configure_logging(file_path=log_path, file_format="json")
    get_logger("t").warning("structured", key="value")
    line = log_path.read_text().strip().splitlines()[0]
    payload = json.loads(line)
    assert payload["event"] == "structured"
    assert payload["key"] == "value"
    assert payload["level"] == "warning"


def test_file_sink_text_has_no_ansi(tmp_path):
    log_path = tmp_path / "plbp.log"
    configure_logging(file_path=log_path, file_format="text")
    get_logger("t").warning("plain-line")
    body = log_path.read_text()
    assert "plain-line" in body
    assert "\x1b[" not in body


def test_file_sink_creates_parent_dirs(tmp_path):
    log_path = tmp_path / "nested" / "state" / "plbp.log"
    configure_logging(file_path=log_path)
    assert log_path.parent.is_dir()


def test_level_vocabulary_matches_spec():
    assert set(LOG_LEVELS) == {"debug", "info", "warning", "error", "critical"}
