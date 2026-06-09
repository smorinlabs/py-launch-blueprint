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

"""Configuration loading: layered TOML files in XDG-compliant locations.

Discovery (each layer overrides the previous), per the conventions spec:

1. system  — ``$XDG_CONFIG_DIRS/plbp/plbp_config.toml`` (default ``/etc/xdg``)
2. user    — ``$XDG_CONFIG_HOME/plbp/plbp_config.toml`` (default ``~/.config``)
3. project — ``./plbp_config.toml`` (or ``./.plbp_config.toml``)

``--config PATH`` (env ``PLBP_CONFIG``) overrides discovery entirely. Settings
are validated against :mod:`core.settings` (the ``[output]`` / ``[logging]``
tables).

Secrets are **never** stored in the config file (R8): the token resolves from
``--token`` then ``$PLBP_TOKEN`` only — never from a file. This module only
*loads* and *writes* configuration; it never prints.
"""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomli_w

from py_launch_blueprint.core import paths
from py_launch_blueprint.core.settings import (
    Settings,
    coerce_value,
    parse_key,
    settings_from_layers,
)

TOKEN_ENV_VAR = "PLBP_TOKEN"  # noqa: S105 — env var name, not a secret value


@dataclass
class Config:
    """Resolved runtime configuration."""

    #: Auth token, from ``--token`` or ``$PLBP_TOKEN`` only (never a file).
    token: str | None = None
    #: Where the token came from ("flag", "env", or None).
    source: str | None = None
    #: Validated, layered settings (the ``[output]`` / ``[logging]`` tables).
    settings: Settings = field(default_factory=Settings)
    #: The writable (user, or ``--config``) config file path.
    config_path: Path | None = None
    #: Config files that existed and were merged, lowest precedence first.
    loaded_paths: list[Path] = field(default_factory=list)


def get_config_dir() -> Path:
    """Return the per-user config directory (``$XDG_CONFIG_HOME/plbp``)."""
    return paths.config_dir()


def get_default_config_path() -> Path:
    """Return the default (user) TOML config path (``…/plbp/plbp_config.toml``)."""
    return paths.config_file()


def _read_toml(path: Path) -> dict[str, Any]:
    """Parse a TOML file to a dict; missing/invalid files read as empty."""
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _discovery_paths(config_file: str | None) -> tuple[Path, list[Path]]:
    """Return ``(write_target, layer_paths)`` lowest precedence first.

    ``--config`` collapses discovery to that single file; otherwise the
    system → user → project layers apply.
    """
    if config_file:
        target = Path(config_file)
        return target, [target]
    target = paths.config_file()
    layers = [
        *reversed(paths.system_config_files()),  # system (lowest first)
        target,  # user
        paths.project_config_file(),  # project (highest)
    ]
    return target, layers


def load_config(
    config_file: str | None = None,
    token_override: str | None = None,
) -> Config:
    """Resolve settings (layered files) and the token (flag/env only)."""
    target, layer_paths = _discovery_paths(config_file)
    settings = settings_from_layers([_read_toml(p) for p in layer_paths])

    token: str | None = None
    source: str | None = None
    if token_override:
        token, source = token_override, "flag"
    else:
        env_token = os.getenv(TOKEN_ENV_VAR)
        if env_token:
            token, source = env_token, "env"

    return Config(
        token=token,
        source=source,
        settings=settings,
        config_path=target,
        loaded_paths=[p for p in layer_paths if p.exists()],
    )


def get_file_value(config_path: Path, dotted_key: str) -> Any:
    """Return the value of ``section.key`` as stored in ``config_path``, or None."""
    section, key = parse_key(dotted_key)
    table = _read_toml(config_path).get(section)
    if isinstance(table, dict) and key in table:
        return table[key]
    return None


def set_config_value(config_path: Path, dotted_key: str, raw_value: str) -> Any:
    """Validate + write one ``section.key`` into the TOML file, preserving rest.

    Returns the coerced value. Raises :class:`ConfigError` for unknown keys or
    invalid values (secrets are not part of the schema, so cannot be set here).
    """
    section, key = parse_key(dotted_key)
    value = coerce_value(section, key, raw_value)

    data = _read_toml(config_path)
    table = data.get(section)
    if not isinstance(table, dict):
        table = {}
    table[key] = value
    data[section] = table

    config_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    config_path.write_text(tomli_w.dumps(data), encoding="utf-8")
    return value
