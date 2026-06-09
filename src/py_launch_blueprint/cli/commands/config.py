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

"""``pylb config`` — inspect configuration (no network required).

A second noun that exercises the same pattern without touching the API, so the
template is clear with zero credentials.
"""

import click

from py_launch_blueprint.cli.context import AppContext
from py_launch_blueprint.cli.options import confirm, global_options, mutation_options
from py_launch_blueprint.core.config import get_default_config_path, save_token
from py_launch_blueprint.core.errors import ExitCode
from py_launch_blueprint.core.models import ConfigPath, ConfigValue

#: Configuration keys this command knows how to surface.
_KNOWN_KEYS = {"token"}
#: Keys `config set` knows how to write.
_WRITABLE_KEYS = {"token"}


@click.group(name="config")
def config_group() -> None:
    """Inspect CLI configuration."""


@config_group.command(name="path")
@global_options
def config_path(app: AppContext) -> None:
    """Show the config file path and whether it exists.

    Examples:
        pylb config path
        pylb config path --json
    """
    path = app.config.config_path or get_default_config_path()
    app.renderer.render(ConfigPath(path=str(path), exists=path.exists()))


@config_group.command(name="get")
@click.argument("key", type=click.Choice(sorted(_KNOWN_KEYS)))
@global_options
def config_get(app: AppContext, key: str) -> None:
    """Show a resolved config value and which source provided it.

    Secrets are masked. Examples:
        pylb config get token
        pylb config get token --json
    """
    cfg = app.config
    if key == "token":
        value = _mask(cfg.token) if cfg.token else None
        app.renderer.render(ConfigValue(key=key, value=value, source=cfg.source))


@config_group.command(name="set")
@click.argument("key", type=click.Choice(sorted(_WRITABLE_KEYS)))
@click.argument("value")
@mutation_options
@global_options
def config_set(
    app: AppContext, key: str, value: str, dry_run: bool, assume_yes: bool
) -> None:
    """Write a config value to the TOML config file.

    Prompts before overwriting an existing file unless --yes is given.
    Examples:
        pylb config set token abc123
        pylb config set token abc123 --dry-run
        pylb config set token abc123 --yes
    """
    path = app.config.config_path or get_default_config_path()

    if dry_run:
        app.renderer.message(f"[dry-run] would write {key} to {path}")
        app.renderer.render(ConfigValue(key=key, value=_mask(value), source="dry-run"))
        return

    if path.exists() and not confirm(
        app, f"Overwrite existing config at {path}?", assume_yes=assume_yes
    ):
        app.renderer.message("Aborted.")
        raise SystemExit(int(ExitCode.INTERRUPT))

    save_token(path, value)
    app.renderer.message(f"Wrote {key} to {path}")
    app.renderer.render(ConfigValue(key=key, value=_mask(value), source="file"))


def _mask(secret: str) -> str:
    """Mask a secret, revealing only the last 4 characters."""
    if len(secret) <= 4:
        return "****"
    return "****" + secret[-4:]
