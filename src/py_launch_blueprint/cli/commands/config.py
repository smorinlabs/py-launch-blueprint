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

"""``plbp config`` — inspect and edit configuration (no network required).

``config set``/``get`` operate on **dotted keys** into the config tables, e.g.
``output.color`` or ``logging.level``. Secrets are never stored in the config
file — the token comes from ``--token`` or ``$PLBP_TOKEN`` only.
"""

import click

from py_launch_blueprint.cli.context import AppContext
from py_launch_blueprint.cli.groups import SuggestingGroup
from py_launch_blueprint.cli.options import confirm, global_options, mutation_options
from py_launch_blueprint.core.config import (
    get_default_config_path,
    read_config_for_write,
    write_config_data,
)
from py_launch_blueprint.core.errors import ConfigError, ExitCode
from py_launch_blueprint.core.models import ConfigPath, ConfigValue
from py_launch_blueprint.core.settings import (
    allowed_values,
    coerce_value,
    parse_key,
    writable_keys,
)

#: Keys `config get` can resolve: every settable key plus the read-only token.
_GETTABLE_KEYS = sorted([*writable_keys(), "token"])


@click.group(name="config", cls=SuggestingGroup)
def config_group() -> None:
    """Inspect and edit CLI configuration."""


#: Keys ``config init`` walks through, in prompt order — the settings a
#: fresh install most plausibly wants to pin down.
_INIT_KEYS = ["output.format", "output.color", "logging.level"]


@config_group.command(name="init")
@mutation_options
@global_options
def config_init(app: AppContext, dry_run: bool, assume_yes: bool) -> None:
    """Create or update the config file with guided prompts.

    Asks (on stderr, so stdout stays pipe-safe) for the most common settings,
    offering the currently resolved values as defaults, then writes them to
    the TOML config file. Secrets are never written — the token stays in
    --token / $PLBP_TOKEN. Examples:

        plbp config init
        plbp config init --yes       # accept current values, no prompts
        plbp config init --dry-run   # preview, write nothing
    """
    path = app.config.config_path or get_default_config_path()
    settings = app.config.settings
    current: dict[str, str] = {}
    for dotted in _INIT_KEYS:
        section, name = parse_key(dotted)
        current[dotted] = str(getattr(getattr(settings, section), name))

    if assume_yes:
        chosen = current
    elif app.no_input:
        raise ConfigError(
            "config init cannot prompt (--no-input set)",
            hint="pass --yes to write the current defaults non-interactively",
        )
    else:
        chosen = {}
        for dotted, default in current.items():
            section, name = parse_key(dotted)
            choices = allowed_values(section, name)
            chosen[dotted] = click.prompt(
                dotted,
                default=default,
                type=click.Choice(choices) if choices else str,
                err=True,
            )

    if dry_run:
        for dotted, value in chosen.items():
            app.renderer.message(f"[dry-run] would set {dotted} = {value} in {path}")
        app.renderer.render(ConfigPath(path=str(path), exists=path.exists()))
        return

    data = read_config_for_write(path)  # ConfigError if existing+corrupt
    for dotted, value in chosen.items():
        section, name = parse_key(dotted)
        table = data.get(section)
        if not isinstance(table, dict):
            table = {}
        table[name] = coerce_value(section, name, value)
        data[section] = table
    write_config_data(path, data)
    app.renderer.message(f"Wrote {path}")
    app.renderer.render(ConfigPath(path=str(path), exists=True))


@config_group.command(name="path")
@global_options
def config_path(app: AppContext) -> None:
    """Show the config file path and whether it exists.

    Examples:
        plbp config path
        plbp config path --json
    """
    path = app.config.config_path or get_default_config_path()
    app.renderer.render(ConfigPath(path=str(path), exists=path.exists()))


@config_group.command(name="get")
@click.argument("key", type=click.Choice(_GETTABLE_KEYS))
@global_options
def config_get(app: AppContext, key: str) -> None:
    """Show a resolved config value and where it came from.

    The token is masked and resolves from flag/env only. Examples:
        plbp config get output.color
        plbp config get logging.level --json
        plbp config get token
    """
    cfg = app.config
    if key == "token":
        value = _mask(cfg.token) if cfg.token else None
        app.renderer.render(ConfigValue(key=key, value=value, source=cfg.source))
        return
    section, name = parse_key(key)
    table = getattr(cfg.settings, section)
    resolved = getattr(table, name)
    # model_fields_set tracks keys a config layer actually supplied — anything
    # else is the schema default, and claiming "config" for it sends users
    # hunting for a file that doesn't set it.
    source = "config" if name in table.model_fields_set else "default"
    app.renderer.render(ConfigValue(key=key, value=str(resolved), source=source))


@config_group.command(name="set")
@click.argument("key", type=click.Choice(writable_keys()))
@click.argument("value")
@mutation_options
@global_options
def config_set(
    app: AppContext, key: str, value: str, dry_run: bool, assume_yes: bool
) -> None:
    """Write a non-secret config value to the TOML config file.

    KEY is a dotted path into the config tables. Examples:
        plbp config set output.color always
        plbp config set logging.level info
        plbp config set logging.file_level debug --yes

    Secrets are never stored here — supply the token via --token or
    $PLBP_TOKEN. Prompts before overwriting an existing value unless --yes.
    """
    path = app.config.config_path or get_default_config_path()
    section, name = parse_key(key)
    coerced = coerce_value(section, name, value)  # validates up front

    if dry_run:
        app.renderer.message(f"[dry-run] would set {key} = {coerced} in {path}")
        app.renderer.render(ConfigValue(key=key, value=str(coerced), source="dry-run"))
        return

    # One read serves both the overwrite check and the write — the value
    # shown in the prompt is the value the write preserves around.
    data = read_config_for_write(path)  # ConfigError if existing+corrupt
    table = data.get(section)
    if not isinstance(table, dict):
        table = {}
    existing = table.get(name)
    if (
        existing is not None
        and existing != coerced
        and not confirm(
            app,
            f"Overwrite {key} ({existing} → {coerced}) in {path}?",
            assume_yes=assume_yes,
        )
    ):
        app.renderer.message("Aborted.")
        raise SystemExit(int(ExitCode.INTERRUPT))

    table[name] = coerced
    data[section] = table
    write_config_data(path, data)
    app.renderer.message(f"Set {key} = {coerced} in {path}")
    app.renderer.render(ConfigValue(key=key, value=str(coerced), source="file"))


def _mask(secret: str) -> str:
    """Mask a secret, revealing only the last 4 characters."""
    if len(secret) <= 4:
        return "****"
    return "****" + secret[-4:]
