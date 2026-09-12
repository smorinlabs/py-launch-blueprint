"""Release cleanup preserves settings and rejects invalid input without writing."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/reset_release_history.py"


def _run(directory):
    return subprocess.run(  # noqa: S603 — checked-in helper, isolated test input
        [sys.executable, str(SCRIPT)],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("has_cutoff", [False, True])
def test_reset_preserves_release_settings_and_is_idempotent(tmp_path, has_cutoff):
    expected = {
        "release-type": "python",
        "packages": {".": {"package-name": "sample_app", "include-v-in-tag": True}},
        "extra-files": ["version.txt"],
    }
    config = dict(expected)
    if has_cutoff:
        config["bootstrap-sha"] = "abc123"
    path = tmp_path / "release-please-config.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    first = _run(tmp_path)
    assert first.returncode == 0, first.stderr
    assert json.loads(path.read_text(encoding="utf-8")) == expected
    after_first = path.read_bytes()

    second = _run(tmp_path)
    assert second.returncode == 0, second.stderr
    assert path.read_bytes() == after_first


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("[]", "must contain a JSON object"),
        ('"text"', "must contain a JSON object"),
        ("42", "must contain a JSON object"),
        ("true", "must contain a JSON object"),
        ("null", "must contain a JSON object"),
        ('{"packages":', "must contain valid JSON"),
    ],
)
def test_reset_rejects_invalid_config_without_writing(tmp_path, contents, message):
    original = (contents + "\n").encode("utf-8")
    path = tmp_path / "release-please-config.json"
    path.write_bytes(original)

    result = _run(tmp_path)

    assert result.returncode != 0
    assert f"release-please-config.json {message}" in result.stderr
    assert "Traceback" not in result.stderr
    assert path.read_bytes() == original
