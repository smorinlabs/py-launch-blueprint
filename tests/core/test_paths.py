"""Windows-native default paths (REC-24).

The Windows branch is selected by ``paths._WINDOWS``, monkeypatched here so
both branches run on every OS. XDG env overrides must win everywhere.
"""

from pathlib import Path

import pytest

from py_launch_blueprint.core import paths

_XDG_VARS = (
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_DIRS",
)


@pytest.fixture
def windows(monkeypatch, tmp_path):
    """Simulate Windows: native env vars set, no XDG overrides."""
    monkeypatch.setattr(paths, "_WINDOWS", True)
    for var in _XDG_VARS:
        monkeypatch.delenv(var, raising=False)
    roaming = tmp_path / "Roaming"
    local = tmp_path / "Local"
    monkeypatch.setenv("APPDATA", str(roaming))
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    return roaming, local


def test_windows_config_uses_appdata(windows):
    roaming, _local = windows
    assert paths.config_dir() == roaming / "plbp"
    assert paths.config_file() == roaming / "plbp" / "plbp_config.toml"


def test_windows_data_and_state_use_localappdata(windows):
    _roaming, local = windows
    assert paths.data_dir() == local / "plbp"
    assert paths.state_dir() == local / "plbp"


def test_windows_cache_nested_under_app_dir(windows):
    _roaming, local = windows
    assert paths.cache_dir() == local / "plbp" / "Cache"


def test_windows_xdg_override_still_wins(windows, monkeypatch, tmp_path):
    xdg = tmp_path / "xdg"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    assert paths.config_dir() == xdg / "plbp"
    monkeypatch.setenv("XDG_CACHE_HOME", str(xdg))
    # explicit override keeps the POSIX <base>/plbp shape, no Cache nesting
    assert paths.cache_dir() == xdg / "plbp"


def test_windows_native_env_unset_falls_back_to_home(windows, monkeypatch):
    monkeypatch.delenv("APPDATA")
    monkeypatch.delenv("LOCALAPPDATA")
    assert paths.config_home() == Path.home() / "AppData" / "Roaming"
    assert paths.data_home() == Path.home() / "AppData" / "Local"


def test_windows_system_config_uses_programdata(windows, monkeypatch, tmp_path):
    program_data = tmp_path / "ProgramData"
    monkeypatch.setenv("PROGRAMDATA", str(program_data))
    assert paths.config_dirs() == [program_data]


def test_posix_defaults_unchanged(monkeypatch):
    monkeypatch.setattr(paths, "_WINDOWS", False)
    for var in _XDG_VARS:
        monkeypatch.delenv(var, raising=False)
    assert paths.config_home() == Path.home() / ".config"
    assert paths.data_home() == Path.home() / ".local" / "share"
    assert paths.state_home() == Path.home() / ".local" / "state"
    assert paths.cache_dir() == Path.home() / ".cache" / "plbp"
    assert paths.config_dirs() == [Path("/etc/xdg")]


def test_windows_config_dirs_split_on_semicolons(windows, monkeypatch, tmp_path):
    one = tmp_path / "one"
    two = tmp_path / "two"
    monkeypatch.setenv("XDG_CONFIG_DIRS", f"{one};{two}")
    assert paths.config_dirs() == [one, two]
