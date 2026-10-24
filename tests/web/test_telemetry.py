"""Tests for tracing wiring (WEB-10).

The enabled-path tests need the ``otel`` extra and skip without it; the
``test-otel`` CI job installs it so they run there. The degrade-path test runs
everywhere because it simulates the missing extra.
"""

import importlib

import pytest
from fastapi import FastAPI

from py_launch_blueprint.core.paths import APP_NAME
from py_launch_blueprint.web import telemetry


def test_instrument_tracing_degrades_without_otel(monkeypatch):
    real_import = importlib.import_module

    def no_otel(name, package=None):
        if name.startswith("opentelemetry"):
            raise ModuleNotFoundError(name)
        return real_import(name, package)

    app = FastAPI()
    monkeypatch.setattr(telemetry.importlib, "import_module", no_otel)
    assert telemetry.instrument_tracing(app) is False
    assert not getattr(app, "_is_instrumented_by_opentelemetry", False)


def test_instrument_tracing_wires_provider_and_app(monkeypatch):
    trace_api = pytest.importorskip("opentelemetry.trace")
    fastapi_instr = pytest.importorskip("opentelemetry.instrumentation.fastapi")
    # Capture the provider instead of installing it process-wide: the global
    # can be set only once, and tests run in random order across workers.
    installed = []
    monkeypatch.setattr(trace_api, "set_tracer_provider", installed.append)

    app = FastAPI()
    try:
        assert telemetry.instrument_tracing(app) is True
        assert len(installed) == 1
        resource = installed[0].resource
        assert resource.attributes["service.name"] == f"{APP_NAME}-web"
        assert app._is_instrumented_by_opentelemetry is True
    finally:
        fastapi_instr.FastAPIInstrumentor.uninstrument_app(app)
        for provider in installed:
            provider.shutdown()
