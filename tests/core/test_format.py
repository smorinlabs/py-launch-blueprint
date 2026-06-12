"""Tests for the human-display helpers in ``core/format.py`` (REC-06)."""

from datetime import UTC, datetime, timedelta

from py_launch_blueprint.core.format import relative_time, rich_link
from py_launch_blueprint.core.models import ConfigPath

NOW = datetime(2026, 6, 12, 12, 0, 0, tzinfo=UTC)


def test_relative_time_just_now():
    assert relative_time(NOW - timedelta(seconds=30), now=NOW) == "just now"


def test_relative_time_singular_and_plural():
    assert relative_time(NOW - timedelta(minutes=1), now=NOW) == "1 minute ago"
    assert relative_time(NOW - timedelta(minutes=5), now=NOW) == "5 minutes ago"


def test_relative_time_buckets():
    assert relative_time(NOW - timedelta(hours=3), now=NOW) == "3 hours ago"
    assert relative_time(NOW - timedelta(days=2), now=NOW) == "2 days ago"
    assert relative_time(NOW - timedelta(days=70), now=NOW) == "2 months ago"
    assert relative_time(NOW - timedelta(days=800), now=NOW) == "2 years ago"


def test_relative_time_future():
    assert relative_time(NOW + timedelta(days=2), now=NOW) == "in 2 days"


def test_relative_time_naive_moment_treated_as_utc():
    naive = datetime(2026, 6, 12, 11, 0, 0)
    assert relative_time(naive, now=NOW) == "1 hour ago"


def test_rich_link_markup():
    assert rich_link("docs", "https://example.com") == (
        "[link=https://example.com]docs[/link]"
    )


def test_config_path_rich_row_hyperlinks_absolute_path(tmp_path):
    target = tmp_path / "cfg.toml"
    rows = ConfigPath(path=str(target), exists=True).table_rows_rich()
    assert rows[0][0] == f"[link={target.as_uri()}]{target}[/link]"
    assert rows[0][1] == "yes"


def test_config_path_rich_row_falls_back_for_relative_path():
    rows = ConfigPath(path="rel.toml", exists=False).table_rows_rich()
    assert rows == [["rel.toml", "no"]]


def test_plain_rows_never_carry_markup(tmp_path):
    result = ConfigPath(path=str(tmp_path / "cfg.toml"), exists=True)
    assert "[link=" not in result.table_rows()[0][0]


def test_rich_link_escapes_markup_in_text():
    # a path containing brackets must render literally, not parse as markup
    assert rich_link("a[b]", "https://e") == "[link=https://e]a\\[b][/link]"
