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

import contextlib
import os
import tempfile
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomli_w

from py_launch_blueprint.core import paths
from py_launch_blueprint.core.errors import ConfigError
from py_launch_blueprint.core.settings import (
    Settings,
    coerce_value,
    parse_key,
    settings_from_layers,
)

TOKEN_ENV_VAR = "PLBP_TOKEN"  # noqa: S105 # nosec B105 — env var name, not a secret value


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
    #: Non-fatal problems found while loading (invalid values dropped,
    #: unparsable discovered layers skipped). The CLI logs these to stderr.
    warnings: list[str] = field(default_factory=list)


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


def _read_layer(path: Path) -> tuple[dict[str, Any], str | None]:
    """Tolerantly read one discovered layer, reporting (data, warning)."""
    if not path.exists():
        return {}, None
    try:
        return tomllib.loads(path.read_text(encoding="utf-8")), None
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return {}, f"ignoring unreadable config file {path}: {exc}"


def _read_explicit(path: Path) -> dict[str, Any]:
    """Read an explicitly named config file (``--config``/``$PLBP_CONFIG``).

    A *missing* file is fine — it is a valid target for ``config set`` and
    fresh setups. But a file that exists and cannot be parsed is a user error
    that must not be silently ignored (R6.4: the flag overrides discovery, so
    nothing else would supply the settings the user thinks they wrote).
    """
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in config file {path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"cannot read config file {path}: {exc}") from exc


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
    """Resolve settings (layered files) and the token (flag/env only).

    Tolerant by design — with one exception: an *explicit* ``--config`` file
    that exists but cannot be parsed raises :class:`ConfigError`. Discovered
    layers and invalid values degrade to warnings (see ``Config.warnings``).
    """
    target, layer_paths = _discovery_paths(config_file)

    warnings: list[str] = []
    layers: list[dict[str, Any]] = []
    if config_file:
        layers.append(_read_explicit(target))  # may raise ConfigError
    else:
        for p in layer_paths:
            data, warning = _read_layer(p)
            layers.append(data)
            if warning:
                warnings.append(warning)
    settings, value_warnings = settings_from_layers(layers)
    warnings.extend(value_warnings)

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
        warnings=warnings,
    )


def get_file_value(config_path: Path, dotted_key: str) -> Any:
    """Return the value of ``section.key`` as stored in ``config_path``, or None."""
    section, key = parse_key(dotted_key)
    table = _read_toml(config_path).get(section)
    if isinstance(table, dict) and key in table:
        return table[key]
    return None


def read_config_for_write(config_path: Path) -> dict[str, Any]:
    """Read a config file that is about to be modified.

    Missing files read as ``{}`` (a valid ``config set`` target). A file that
    exists but cannot be parsed raises :class:`ConfigError` — never silently
    rewrite a corrupt file, which would destroy whatever the user had in it.
    """
    if not config_path.exists():
        return {}
    try:
        return tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(
            f"refusing to modify {config_path}: existing file cannot be "
            f"parsed ({exc}). Fix or remove it first."
        ) from exc


def write_config_data(config_path: Path, data: dict[str, Any]) -> None:
    """Write a config dict as TOML, atomically, restricted to the owner.

    Writes to a temp file in the same directory and ``os.replace``s it over
    the target, so an interrupted write can never leave a truncated config
    (which ``config set`` would then refuse to touch). ``mkstemp`` creates
    the file 0600 from the first byte — users habitually put sensitive
    things in CLI config files even though the schema holds no secrets.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    rendered = tomli_w.dumps(data)
    fd, tmp_name = tempfile.mkstemp(
        dir=config_path.parent, prefix=f".{config_path.name}."
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, config_path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


def set_config_value(config_path: Path, dotted_key: str, raw_value: str) -> Any:
    """Validate + write one ``section.key`` into the TOML file, preserving rest.

    Returns the coerced value. Raises :class:`ConfigError` for unknown keys,
    invalid values (secrets are not part of the schema, so cannot be set
    here), or a corrupt existing file (see :func:`read_config_for_write`).
    """
    section, key = parse_key(dotted_key)
    value = coerce_value(section, key, raw_value)
    data = read_config_for_write(config_path)
    table = data.get(section)
    if not isinstance(table, dict):
        table = {}
    table[key] = value
    data[section] = table
    write_config_data(config_path, data)
    return value
