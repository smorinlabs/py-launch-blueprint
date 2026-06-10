"""Tests for the output renderer contract (text / JSON / Markdown)."""

import json

from py_launch_blueprint.cli.output import OutputMode, Renderer
from py_launch_blueprint.core.errors import ExitCode
from py_launch_blueprint.core.models import Project, ProjectList


def _result():
    return ProjectList(projects=[Project(id="1", name="Alpha", workspace="WS")])


def test_json_mode_emits_clean_parseable_stdout(capsys):
    Renderer(OutputMode.JSON).render(_result())
    out = capsys.readouterr().out
    payload = json.loads(out)  # must be valid JSON, no color/log noise
    assert payload["projects"][0]["name"] == "Alpha"


def test_markdown_mode_emits_table(capsys):
    Renderer(OutputMode.MARKDOWN).render(_result())
    out = capsys.readouterr().out
    assert "| Name | Workspace | ID |" in out
    assert "| Alpha | WS | 1 |" in out


def test_text_mode_writes_to_stdout(capsys):
    Renderer(OutputMode.TEXT, no_color=True).render(_result())
    out = capsys.readouterr().out
    assert "Alpha" in out


def test_message_goes_to_stderr_not_stdout(capsys):
    Renderer(OutputMode.TEXT, no_color=True).message("hello")
    captured = capsys.readouterr()
    assert "hello" in captured.err
    assert captured.out == ""


def test_message_suppressed_in_json_mode(capsys):
    Renderer(OutputMode.JSON).message("hello")
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_error_json_is_structured_on_stderr(capsys):
    Renderer(OutputMode.JSON).error("boom", ExitCode.CONFIG)
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert payload["error"]["code"] == 1
    assert payload["error"]["name"] == "CONFIG"
    assert payload["error"]["message"] == "boom"
    assert captured.out == ""  # stdout stays clean for piping
