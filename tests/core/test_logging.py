"""Tests for the dual-sink logging setup (console + rotating file)."""

import json
import logging
from logging.handlers import RotatingFileHandler

from py_launch_blueprint.core.logging import (
    LOG_LEVELS,
    REDACTED,
    ROTATE_BACKUP_COUNT,
    ROTATE_MAX_BYTES,
    LogFormat,
    bind_contextvars,
    clear_contextvars,
    configure_logging,
    get_logger,
)


def test_console_only_by_default(capsys):
    configure_logging(level=logging.WARNING, fmt=LogFormat.JSON)
    root = logging.getLogger()
    owned = [h for h in root.handlers if getattr(h, "_plbp_owned", False)]
    assert len(owned) == 1  # no file sink unless asked for (R9.3)
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


def test_json_logs_carry_tracebacks(tmp_path):
    # format_exc_info must render exception text into JSON output.
    log_path = tmp_path / "plbp.log"
    configure_logging(file_path=log_path, file_format="json")
    try:
        raise ValueError("boom-for-logs")
    except ValueError:
        get_logger("t").exception("failed")
    line = log_path.read_text().strip().splitlines()[0]
    payload = json.loads(line)
    assert "boom-for-logs" in payload.get("exception", "")
    assert "Traceback" in payload.get("exception", "")


def test_logger_name_in_output(tmp_path):
    # add_logger_name: the `__name__` passed to get_logger must be queryable.
    log_path = tmp_path / "plbp.log"
    configure_logging(file_path=log_path, file_format="json")
    get_logger("pkg.module").warning("named")
    payload = json.loads(log_path.read_text().strip().splitlines()[0])
    assert payload["logger"] == "pkg.module"


def test_sensitive_keys_redacted(tmp_path):
    # Key-based redaction runs in the shared chain — every sink, including
    # keys merged from contextvars.
    log_path = tmp_path / "plbp.log"
    configure_logging(file_path=log_path, file_format="json")
    bind_contextvars(api_key="bound-secret")
    try:
        get_logger("t").warning("login", token="abc123", username="alice")
    finally:
        clear_contextvars()
    payload = json.loads(log_path.read_text().strip().splitlines()[0])
    assert payload["token"] == REDACTED
    assert payload["api_key"] == REDACTED
    assert payload["username"] == "alice"
    assert "abc123" not in log_path.read_text()


def test_json_sink_serializes_arbitrary_types(tmp_path):
    # JSONRenderer(default=str): non-JSON-native values degrade to their
    # string form; the log line must never be lost to a TypeError.
    log_path = tmp_path / "plbp.log"
    configure_logging(file_path=log_path, file_format="json")
    get_logger("t").warning("wrote", target=tmp_path)
    payload = json.loads(log_path.read_text().strip().splitlines()[0])
    assert payload["target"] == str(tmp_path)


def test_foreign_root_handlers_survive_reconfigure():
    # We must never close/remove handlers we don't own (host apps, caplog).
    foreign = logging.NullHandler()
    root = logging.getLogger()
    root.addHandler(foreign)
    try:
        configure_logging(level=logging.WARNING, fmt=LogFormat.JSON)
        assert foreign in root.handlers
        configure_logging(level=logging.INFO, fmt=LogFormat.JSON)
        assert foreign in root.handlers  # survives repeated reconfigure
        owned = [h for h in root.handlers if getattr(h, "_plbp_owned", False)]
        assert len(owned) == 1  # ...while our own handlers don't accumulate
    finally:
        root.removeHandler(foreign)
