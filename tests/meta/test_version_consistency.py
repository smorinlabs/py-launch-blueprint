# Copyright (c) 2025, Steve Morin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Guard that the project version stays single-sourced.

``pyproject.toml`` ``[project] version`` is the single source of truth (ADR-06).
release-please bumps it together with ``.release-please-manifest.json`` and the
editable root entry in ``uv.lock``. The CLI/docs derive their version from the
installed package metadata (``py_launch_blueprint.__version__``). These tests
fail if any copy or the atomic release updater drifts.
"""

import json
import tomllib
from pathlib import Path

from py_launch_blueprint import __version__

ROOT = Path(__file__).resolve().parents[2]
UV_LOCK_UPDATER = {
    "type": "toml",
    "path": "uv.lock",
    "jsonpath": "$.package[?(@.name.value=='py-launch-blueprint' && "
    "@.source.editable.value=='.')].version",
}


def _pyproject_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    return data["project"]["version"]


def _manifest_version() -> str:
    data = json.loads((ROOT / ".release-please-manifest.json").read_text())
    return data["."]


def test_manifest_matches_pyproject():
    """release-please bumps both; they must never diverge."""
    assert _manifest_version() == _pyproject_version()


def test_uv_lock_matches_pyproject():
    """The editable root package metadata must match the source version."""
    data = tomllib.loads((ROOT / "uv.lock").read_text())
    editable_packages = [
        package
        for package in data["package"]
        if package["name"] == "py-launch-blueprint"
        and package.get("source", {}).get("editable") == "."
    ]

    assert len(editable_packages) == 1
    assert editable_packages[0]["version"] == _pyproject_version()


def test_release_please_updates_uv_lock_atomically():
    """The release commit must include uv.lock before the PR becomes visible."""
    config = json.loads((ROOT / "release-please-config.json").read_text())
    assert UV_LOCK_UPDATER in config["packages"]["."]["extra-files"]


def test_installed_version_matches_pyproject():
    """The CLI/docs derive __version__ from installed metadata.

    Requires a synced environment (``uv sync``); the version baked into the
    installed distribution must match the source-of-truth in pyproject.toml.
    """
    assert __version__ == _pyproject_version()
