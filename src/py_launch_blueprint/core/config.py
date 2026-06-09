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

"""Configuration loading with a documented precedence order.

Precedence (highest wins):

1. explicit override (e.g. the ``--token`` flag)
2. environment variable (``PY_TOKEN``)
3. config file (``~/.config/py-cli/.env`` by default, or ``--config PATH``)

This module only *loads* configuration; it never prints. The CLI decides how
to report a missing token (see ``cli/commands``).
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

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
    """Return the per-user configuration directory (cross-platform)."""
    if os.name == "nt":  # Windows
        base_path = Path(os.environ.get("USERPROFILE", str(Path.home())))
    else:  # Unix-like
        base_path = Path.home()
    return base_path / ".config" / "py-cli"


def get_default_config_path() -> Path:
    """Return the default ``.env`` config file location."""
    return get_config_dir() / ".env"


def load_config(
    config_file: str | None = None,
    token_override: str | None = None,
) -> Config:
    """Resolve configuration from flag, environment, then file.

    Args:
        config_file: Optional explicit path to a ``.env`` file. Falls back to
            the default location when omitted.
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

    # 3. config file (only if present; missing file is not an error here)
    if config_path.exists():
        file_values = dotenv_values(config_path)
        file_token = file_values.get(TOKEN_ENV_VAR)
        if file_token:
            return Config(token=file_token, source="file", config_path=config_path)

    return Config(token=None, source=None, config_path=config_path)
