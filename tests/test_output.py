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


# -- --output-file (R4: destination, independent of format) ----------------


def test_output_file_json(tmp_path, capsys):
    target = tmp_path / "out.json"
    Renderer(OutputMode.JSON, output_file=str(target)).render(_result())
    assert capsys.readouterr().out == ""  # nothing on stdout
    payload = json.loads(target.read_text())
    assert payload["projects"][0]["name"] == "Alpha"


def test_output_file_markdown(tmp_path, capsys):
    target = tmp_path / "out.md"
    Renderer(OutputMode.MARKDOWN, output_file=str(target)).render(_result())
    assert capsys.readouterr().out == ""
    assert "| Alpha | WS | 1 |" in target.read_text()


def test_output_file_text_has_no_ansi(tmp_path):
    target = tmp_path / "out.txt"
    Renderer(OutputMode.TEXT, output_file=str(target)).render(_result())
    body = target.read_text()
    assert "Alpha" in body
    assert "\x1b[" not in body  # a file is not a TTY: no escape codes


def test_output_file_messages_still_on_stderr(tmp_path, capsys):
    renderer = Renderer(OutputMode.TEXT, output_file=str(tmp_path / "o.txt"))
    renderer.message("working...")
    captured = capsys.readouterr()
    assert "working" in captured.err
    assert captured.out == ""


# -- color modes (R5) -------------------------------------------------------


def test_color_never_disables_color():
    renderer = Renderer(OutputMode.TEXT, color="never")
    assert renderer.out.no_color is True


def test_color_always_forces_terminal():
    renderer = Renderer(OutputMode.TEXT, color="always")
    assert renderer.out.is_terminal is True


def test_no_color_kwarg_backcompat_maps_to_never():
    renderer = Renderer(OutputMode.TEXT, no_color=True)
    assert renderer.color == "never"
    assert renderer.out.no_color is True
