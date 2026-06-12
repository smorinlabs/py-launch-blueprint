"""Tests for the output renderer contract (text / JSON / Markdown)."""

import json

from py_launch_blueprint.cli import output as output_mod
from py_launch_blueprint.cli.output import (
    OutputMode,
    Renderer,
    _resolve_pager_command,
)
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
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["projects"][0]["name"] == "Alpha"


def test_output_file_markdown(tmp_path, capsys):
    target = tmp_path / "out.md"
    Renderer(OutputMode.MARKDOWN, output_file=str(target)).render(_result())
    assert capsys.readouterr().out == ""
    assert "| Alpha | WS | 1 |" in target.read_text(encoding="utf-8")


def test_output_file_text_has_no_ansi(tmp_path):
    target = tmp_path / "out.txt"
    Renderer(OutputMode.TEXT, output_file=str(target)).render(_result())
    body = target.read_text(encoding="utf-8")
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


# -- error codes, hints, crash pointer (REC-02/REC-22) ---------------------


def test_error_json_includes_error_code_and_hint(capsys):
    Renderer(OutputMode.JSON).error(
        "boom",
        ExitCode.AUTH,
        error_code="PLBP002",
        hint="set $PLBP_TOKEN",
        traceback_path="/state/plbp_crash.log",
    )
    payload = json.loads(capsys.readouterr().err)
    assert payload["error"]["error_code"] == "PLBP002"
    assert payload["error"]["hint"] == "set $PLBP_TOKEN"
    assert payload["error"]["traceback_path"] == "/state/plbp_crash.log"


def test_error_json_omits_absent_optional_keys(capsys):
    Renderer(OutputMode.JSON).error("boom", ExitCode.CONFIG)
    payload = json.loads(capsys.readouterr().err)
    assert "error_code" not in payload["error"]
    assert "hint" not in payload["error"]
    assert "traceback_path" not in payload["error"]


def test_error_text_shows_code_hint_and_traceback_path(capsys):
    Renderer(OutputMode.TEXT, no_color=True).error(
        "boom",
        ExitCode.AUTH,
        error_code="PLBP002",
        hint="set $PLBP_TOKEN",
        traceback_path="/state/plbp_crash.log",
    )
    err = capsys.readouterr().err
    assert "PLBP002" in err
    assert "hint: set $PLBP_TOKEN" in err
    assert "full traceback: /state/plbp_crash.log" in err


# -- pager (REC-04) ---------------------------------------------------------


def _tall_result(rows: int = 40):
    return ProjectList(
        projects=[Project(id=str(i), name=f"P{i}", workspace="WS") for i in range(rows)]
    )


def test_pager_env_precedence(monkeypatch):
    monkeypatch.delenv("PLBP_PAGER", raising=False)
    monkeypatch.delenv("PAGER", raising=False)
    assert _resolve_pager_command() == "less -FRX"
    monkeypatch.setenv("PAGER", "more")
    assert _resolve_pager_command() == "more"
    monkeypatch.setenv("PLBP_PAGER", "bat")
    assert _resolve_pager_command() == "bat"
    monkeypatch.setenv("PLBP_PAGER", "")  # set-but-empty disables (git-style)
    assert _resolve_pager_command() == ""


def test_pager_not_used_when_not_a_terminal(capsys, monkeypatch):
    def explode(*args, **kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("pager must not run for piped output")

    monkeypatch.setattr(output_mod.subprocess, "run", explode)
    Renderer(OutputMode.TEXT, no_color=True).render(_tall_result())
    assert "P39" in capsys.readouterr().out


def test_pager_invoked_for_tall_terminal_output(monkeypatch):
    calls = {}

    def fake_run(args, **kwargs):
        calls["args"] = args
        calls["input"] = kwargs.get("input", "")

    monkeypatch.setenv("PLBP_PAGER", "fakepager --flag")
    monkeypatch.setattr(output_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(output_mod, "_isatty", lambda console: True)
    Renderer(OutputMode.TEXT, color="always").render(_tall_result())
    assert calls["args"] == ["fakepager", "--flag"]
    assert "P39" in calls["input"]


def test_pager_skipped_for_short_output(capsys, monkeypatch):
    def explode(*args, **kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("short output must not be paged")

    monkeypatch.setenv("PLBP_PAGER", "fakepager")
    monkeypatch.setattr(output_mod.subprocess, "run", explode)
    monkeypatch.setattr(output_mod, "_isatty", lambda console: True)
    Renderer(OutputMode.TEXT, color="always").render(_result())
    assert "Alpha" in capsys.readouterr().out


def test_pager_missing_binary_falls_back_to_plain_output(capsys, monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError("no such pager")

    monkeypatch.setenv("PLBP_PAGER", "definitely-not-a-pager")
    monkeypatch.setattr(output_mod.subprocess, "run", missing)
    monkeypatch.setattr(output_mod, "_isatty", lambda console: True)
    Renderer(OutputMode.TEXT, color="always").render(_tall_result())
    assert "P39" in capsys.readouterr().out


def test_pager_not_used_when_color_forced_but_piped(capsys, monkeypatch):
    # color="always" forces rich's is_terminal True; the real stdout is
    # still a pipe here, and a piped run must never block on a pager.
    def explode(*args, **kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("pager must not run when stdout is not a tty")

    monkeypatch.setenv("PLBP_PAGER", "fakepager")
    monkeypatch.setattr(output_mod.subprocess, "run", explode)
    Renderer(OutputMode.TEXT, color="always").render(_tall_result())
    assert "P39" in capsys.readouterr().out


def test_pager_disabled_by_paging_false(capsys, monkeypatch):
    def explode(*args, **kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("paging=False must never page")

    monkeypatch.setenv("PLBP_PAGER", "fakepager")
    monkeypatch.setattr(output_mod.subprocess, "run", explode)
    monkeypatch.setattr(output_mod, "_isatty", lambda console: True)
    Renderer(OutputMode.TEXT, color="always", paging=False).render(_tall_result())
    assert "P39" in capsys.readouterr().out


# -- pager tokenization (windows-aware; coderabbit review) -------------------


def test_pager_argv_posix(monkeypatch):
    monkeypatch.setattr(output_mod, "_WINDOWS", False)
    assert output_mod._pager_argv("less -FRX") == ["less", "-FRX"]


def test_pager_argv_windows_preserves_backslashes(monkeypatch):
    monkeypatch.setattr(output_mod, "_WINDOWS", True)
    assert output_mod._pager_argv(r"C:\tools\less.exe -FRX") == [
        r"C:\tools\less.exe",
        "-FRX",
    ]


def test_pager_argv_windows_strips_quotes_around_spaced_path(monkeypatch):
    monkeypatch.setattr(output_mod, "_WINDOWS", True)
    assert output_mod._pager_argv(r'"C:\Program Files\less.exe" -FRX') == [
        r"C:\Program Files\less.exe",
        "-FRX",
    ]
