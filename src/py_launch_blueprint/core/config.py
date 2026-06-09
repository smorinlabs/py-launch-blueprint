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

"""Configuration loading: a TOML file in an XDG-compliant location.

The config file defaults to ``$XDG_CONFIG_HOME/pylb/pylb_config.toml`` (see
``core.paths``). Its format is TOML::

    # ~/.config/pylb/pylb_config.toml
    token = "your_token_here"

    # (an [auth] table is also accepted, for forward-compatibility)
    # [auth]
    # token = "your_token_here"

Precedence (highest wins):

1. explicit override (e.g. the ``--token`` flag)
2. environment variable (``PY_TOKEN``)
3. the TOML config file

This module only *loads* configuration; it never prints.
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from py_launch_blueprint.core import paths

TOKEN_ENV_VAR = "PY_TOKEN"  # noqa: S105 — env var name, not a secret value


@dataclass
class Config:
    """Resolved runtime configuration."""

    token: str | None = None
    #: Where the token was resolved from ("flag", "env", "file", or None).
    source: str | None = None
    #: The config file path that was consulted (whether or not it existed).
    config_path: Path | None = None


def get_config_dir() -> Path:
    """Return the per-user config directory (``$XDG_CONFIG_HOME/pylb``)."""
    return paths.config_dir()


def get_default_config_path() -> Path:
    """Return the default TOML config file path (``…/pylb/pylb_config.toml``)."""
    return paths.config_file()


def _read_toml_token(path: Path) -> str | None:
    """Extract a token from a TOML config file (top-level or ``[auth]``)."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    token = data.get("token")
    if token is None and isinstance(data.get("auth"), dict):
        token = data["auth"].get("token")
    return token if isinstance(token, str) else None


def load_config(
    config_file: str | None = None,
    token_override: str | None = None,
) -> Config:
    """Resolve configuration from flag, environment, then the TOML file.

    Args:
        config_file: Optional explicit path to a TOML config file. Falls back
            to the default XDG location when omitted.
        token_override: Optional token supplied directly (e.g. ``--token``),
            taking precedence over all other sources.

    Returns:
        A :class:`Config`. ``token`` may be ``None`` if nothing provided one;
        callers that require a token should raise ``AuthError`` themselves.
    """
    config_path = Path(config_file) if config_file else get_default_config_path()

    # 1. explicit override
    if token_override:
        return Config(token=token_override, source="flag", config_path=config_path)

    # 2. environment variable
    env_token = os.getenv(TOKEN_ENV_VAR)
    if env_token:
        return Config(token=env_token, source="env", config_path=config_path)

    # 3. TOML config file (only if present; missing file is not an error here)
    if config_path.exists():
        file_token = _read_toml_token(config_path)
        if file_token:
            return Config(token=file_token, source="file", config_path=config_path)

    return Config(token=None, source=None, config_path=config_path)
