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
release-please bumps it together with ``.release-please-manifest.json``, and the
CLI/docs derive their version from the installed package metadata
(``py_launch_blueprint.__version__``). These tests fail if any of those copies
drift apart.
"""

import json
import tomllib
from pathlib import Path

from py_launch_blueprint import __version__

ROOT = Path(__file__).resolve().parents[2]


def _pyproject_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    return data["project"]["version"]


def _manifest_version() -> str:
    data = json.loads((ROOT / ".release-please-manifest.json").read_text())
    return data["."]


def test_manifest_matches_pyproject():
    """release-please bumps both; they must never diverge."""
    assert _manifest_version() == _pyproject_version()


def test_installed_version_matches_pyproject():
    """The CLI/docs derive __version__ from installed metadata.

    Requires a synced environment (``uv sync``); the version baked into the
    installed distribution must match the source-of-truth in pyproject.toml.
    """
    assert __version__ == _pyproject_version()
