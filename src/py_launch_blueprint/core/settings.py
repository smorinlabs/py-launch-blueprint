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

"""Typed configuration schema for the TOML config file.

Config is organized into tables by concern — ``[output]`` and ``[logging]`` —
with ``snake_case`` keys. This module is the single source of truth for that
schema: the loader validates files against it, and ``config set``/``config
get`` operate on **dotted keys** (e.g. ``logging.level``) resolved against it.

Secrets are deliberately *not* part of this schema — the token is supplied via
``--token`` or ``$PLBP_TOKEN`` only, never written to the config file.
"""

from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from py_launch_blueprint.core.errors import ConfigError

_Level = Literal["debug", "info", "warning", "error", "critical"]


class OutputSettings(BaseModel):
    """The ``[output]`` table."""

    model_config = {"extra": "ignore"}

    format: Literal["text", "json", "markdown"] = "text"
    color: Literal["auto", "always", "never"] = "auto"


class LoggingSettings(BaseModel):
    """The ``[logging]`` table."""

    model_config = {"extra": "ignore"}

    level: _Level = "warning"
    file: str = ""
    file_level: _Level = "debug"
    format: Literal["text", "json"] = "text"


class Settings(BaseModel):
    """Resolved, validated config (defaults applied for anything unset)."""

    model_config = {"extra": "ignore"}

    output: OutputSettings = OutputSettings()
    logging: LoggingSettings = LoggingSettings()


#: section name -> submodel, the only tables `config set`/`get` accept.
_SECTIONS: dict[str, type[BaseModel]] = {
    "output": OutputSettings,
    "logging": LoggingSettings,
}


def writable_keys() -> list[str]:
    """All settable dotted keys, e.g. ``["logging.level", "output.color", …]``."""
    return sorted(
        f"{section}.{name}"
        for section, model in _SECTIONS.items()
        for name in model.model_fields
    )


def parse_key(dotted: str) -> tuple[str, str]:
    """Split ``"logging.level"`` into ``("logging", "level")``, validating both.

    Raises :class:`ConfigError` for an unknown section or key (never a secret).
    """
    parts = dotted.split(".")
    if len(parts) != 2 or parts[0] not in _SECTIONS:
        raise ConfigError(
            f"unknown config key {dotted!r}. "
            f"Settable keys: {', '.join(writable_keys())}"
        )
    section, key = parts
    if key not in _SECTIONS[section].model_fields:
        raise ConfigError(
            f"unknown config key {dotted!r}. "
            f"Settable keys: {', '.join(writable_keys())}"
        )
    return section, key


def coerce_value(section: str, key: str, raw: str) -> Any:
    """Validate + coerce a raw string against the field's type/allowed values."""
    model = _SECTIONS[section]
    try:
        validated = model.model_validate({key: raw})
    except ValidationError as exc:
        allowed = _allowed_hint(model, key)
        hint = f" (allowed: {allowed})" if allowed else ""
        raise ConfigError(f"invalid value for {section}.{key}: {raw!r}{hint}") from exc
    return getattr(validated, key)


def allowed_values(section: str, key: str) -> tuple[str, ...] | None:
    """Allowed string literals for a settable key, or None if unconstrained.

    Used for error messages and interactive prompts (``config init``).
    """
    annotation = _SECTIONS[section].model_fields[key].annotation
    choices = getattr(annotation, "__args__", None)
    if choices and all(isinstance(c, str) for c in choices):
        return tuple(choices)
    return None


def _allowed_hint(model: type[BaseModel], key: str) -> str | None:
    """Render the allowed values for a Literal field, for error messages."""
    annotation = model.model_fields[key].annotation
    choices = getattr(annotation, "__args__", None)
    if choices and all(isinstance(c, str) for c in choices):
        return ", ".join(choices)
    return None


def settings_from_layers(
    layers: list[dict[str, Any]],
) -> tuple[Settings, list[str]]:
    """Merge config dicts (lowest precedence first) and validate into Settings.

    Invalid values are **dropped with a warning** rather than raised: config
    must never brick the CLI — the user needs ``config set``/``config path``
    working in order to repair the file. Returns ``(settings, warnings)``.
    """
    merged: dict[str, dict[str, Any]] = {}
    for layer in layers:
        for section in _SECTIONS:
            table = layer.get(section)
            if isinstance(table, dict):
                merged.setdefault(section, {}).update(table)

    warnings: list[str] = []
    try:
        return Settings.model_validate(merged), warnings
    except ValidationError as exc:
        for err in exc.errors():
            loc = err["loc"][:2]
            if len(loc) == 2 and loc[0] in merged:
                section, key = str(loc[0]), str(loc[1])
                bad = merged[section].pop(key, None)
                hint = (
                    _allowed_hint(_SECTIONS[section], key)
                    if (key in _SECTIONS[section].model_fields)
                    else None
                )
                suffix = f" (allowed: {hint})" if hint else ""
                warnings.append(
                    f"ignoring invalid config value {section}.{key} = {bad!r}{suffix}"
                )
    try:
        return Settings.model_validate(merged), warnings
    except ValidationError:  # pragma: no cover — defensive double-fault
        warnings.append("config could not be validated; using built-in defaults")
        return Settings(), warnings
