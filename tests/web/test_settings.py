"""Typed env settings (WEB-30).

The literal PLBP_WEB_* names below are intentional: they are registered in
init/manifest.toml, so a fork's `just init` rewrites them along with the code
(same convention as tests/cli/test_pylb.py).
"""

import os

import pytest
from pydantic import ValidationError

from py_launch_blueprint.web.settings import ENV_PREFIX, WebSettings


def test_prefix_derives_from_app_name():
    assert ENV_PREFIX == "PLBP_WEB_"


def test_defaults_are_safe(monkeypatch):
    for var in list(os.environ):
        if var.startswith(ENV_PREFIX):
            monkeypatch.delenv(var)
    settings = WebSettings()
    assert settings.host == "127.0.0.1"
    assert settings.cors_origins == []
    assert settings.rate_limit is None
    assert settings.metrics_enabled is True
    assert settings.otel_enabled is False
    assert settings.graceful_shutdown_seconds == 10


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("PLBP_WEB_PORT", "9001")
    monkeypatch.setenv("PLBP_WEB_CORS_ORIGINS", '["https://app.example"]')
    monkeypatch.setenv("PLBP_WEB_RATE_LIMIT", "100/minute")
    settings = WebSettings()
    assert settings.port == 9001
    assert settings.cors_origins == ["https://app.example"]
    assert settings.rate_limit == "100/minute"


def test_invalid_value_fails_at_boot(monkeypatch):
    monkeypatch.setenv("PLBP_WEB_PORT", "not-a-port")
    with pytest.raises(ValidationError):
        WebSettings()
