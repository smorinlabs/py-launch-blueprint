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

"""XDG Base Directory resolution with intent-revealing, app-namespaced names.

Follows the `XDG Base Directory Specification
<https://specifications.freedesktop.org/basedir-spec/latest/>`_:

* ``$XDG_CONFIG_HOME`` (default ``~/.config``)      — config
* ``$XDG_DATA_HOME``   (default ``~/.local/share``) — data you'd hate to lose
* ``$XDG_STATE_HOME``  (default ``~/.local/state``) — logs/history (recoverable)
* ``$XDG_CACHE_HOME``  (default ``~/.cache``)       — regenerable cache

Everything is namespaced under one per-app directory (``<XDG>/plbp/``), and
files are named ``<app>_<kind>.<ext>`` so a stray file on disk announces both
its owner and its purpose:

    ~/.config/plbp/plbp_config.toml
    ~/.local/share/plbp/plbp_db.db
    ~/.local/state/plbp/plbp.log
    ~/.cache/plbp/

Spec edge cases handled: an XDG variable that is unset, empty, or holds a
*relative* path is ignored in favor of the default (the spec mandates absolute
paths). Resolve once; never read the raw env vars elsewhere.
"""

import os
from pathlib import Path

#: The CLI/binary name — also the XDG namespace and the filename prefix.
APP_NAME = "plbp"


def _xdg_base(env_var: str, default: Path) -> Path:
    """Return an absolute XDG base dir, falling back to ``default``.

    Per the spec, a value that is empty or not absolute must be ignored.
    """
    raw = os.environ.get(env_var, "")
    if raw:
        candidate = Path(raw)
        if candidate.is_absolute():
            return candidate
    return default


def _home() -> Path:
    return Path.home()


def config_home() -> Path:
    return _xdg_base("XDG_CONFIG_HOME", _home() / ".config")


def config_dirs() -> list[Path]:
    """System config dirs from ``$XDG_CONFIG_DIRS`` (default ``/etc/xdg``).

    Returned highest-precedence first, matching the spec (earlier entries in
    ``XDG_CONFIG_DIRS`` win). Empty/relative entries are ignored.
    """
    raw = os.environ.get("XDG_CONFIG_DIRS", "")
    dirs = [Path(p) for p in raw.split(os.pathsep) if p and Path(p).is_absolute()]
    return dirs or [Path("/etc/xdg")]


def data_home() -> Path:
    return _xdg_base("XDG_DATA_HOME", _home() / ".local" / "share")


def state_home() -> Path:
    return _xdg_base("XDG_STATE_HOME", _home() / ".local" / "state")


def cache_home() -> Path:
    return _xdg_base("XDG_CACHE_HOME", _home() / ".cache")


# -- per-app directories (namespaced under APP_NAME) ----------------------


def config_dir() -> Path:
    return config_home() / APP_NAME


def data_dir() -> Path:
    return data_home() / APP_NAME


def state_dir() -> Path:
    return state_home() / APP_NAME


def cache_dir() -> Path:
    return cache_home() / APP_NAME


# -- intent-revealing filenames: <app>_<kind>.<ext> -----------------------


CONFIG_FILENAME = f"{APP_NAME}_config.toml"


def config_file() -> Path:
    """Default (user) config file: ``<config>/plbp/plbp_config.toml``."""
    return config_dir() / CONFIG_FILENAME


def system_config_files() -> list[Path]:
    """System config files, lowest-precedence layer (``<dir>/plbp/...``)."""
    return [d / APP_NAME / CONFIG_FILENAME for d in config_dirs()]


def project_config_file(start: Path | None = None) -> Path:
    """Project-local config file in ``start`` (cwd): ``./plbp_config.toml``.

    The dotfile form ``./.plbp_config.toml`` is preferred when it exists.
    """
    base = start or Path.cwd()
    dotfile = base / f".{CONFIG_FILENAME}"
    return dotfile if dotfile.exists() else base / CONFIG_FILENAME


def log_file() -> Path:
    """Default log file (state): ``<state>/plbp/plbp.log``."""
    return state_dir() / f"{APP_NAME}.log"


def database_file(name: str = "db", ext: str = "db") -> Path:
    """Default database file: ``<data>/plbp/plbp_db.db``."""
    return data_dir() / f"{APP_NAME}_{name}.{ext}"


def state_file(name: str, ext: str = "log") -> Path:
    """A state file (logs/history): ``<state>/plbp/plbp_<name>.<ext>``."""
    return state_dir() / f"{APP_NAME}_{name}.{ext}"


def ensure_dir(path: Path) -> Path:
    """Create ``path`` (mode 0700, like the spec recommends) and return it."""
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path
