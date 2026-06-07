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

"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from py_launch_blueprint.projects import Config, ConfigError, get_config


def test_config_from_env():
    """Test creating config from environment variables."""
    with patch.dict(os.environ, {"PY_TOKEN": "test_token"}):
        config = Config.from_env()
        assert config.token == "test_token"


def test_config_from_env_file(tmp_path):
    """Test creating config from env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("PY_TOKEN=file_token")

    with patch.dict(os.environ, {}, clear=True):
        config = Config.from_env(str(env_file))
        assert config.token == "file_token"


def test_config_precedence(tmp_path):
    """Test configuration source precedence."""
    env_file = tmp_path / ".env"
    env_file.write_text("PY_TOKEN=file_token")

    # Environment variable should take precedence
    with patch.dict(os.environ, {"PY_TOKEN": "env_token"}):
        config = get_config(str(env_file))
        assert config.token == "env_token"


def test_invalid_config_file(monkeypatch):
    """Test behavior when .env file is missing and no PY_TOKEN is set."""
    monkeypatch.delenv("PY_TOKEN", raising=False)
    with pytest.raises(ConfigError, match="No PY_TOKEN found"):
        Config.from_env("/nonexistent/path")
