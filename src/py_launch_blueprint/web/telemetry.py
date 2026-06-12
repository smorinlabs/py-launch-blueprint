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

"""Metrics (WEB-11) and tracing (WEB-10) wiring.

Prometheus metrics ship with the ``web`` extra and are on by default
(``/metrics``, excluded from the OpenAPI schema). OpenTelemetry is a further
opt-in: install the ``otel`` extra, set ``<APP_NAME>_WEB_OTEL_ENABLED=1``, and
point the exporter via the standard ``OTEL_EXPORTER_OTLP_*`` env vars. The
otel imports are dynamic so the ``web``-only install (and ty) never sees them.
"""

import importlib

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from py_launch_blueprint.core.logging import get_logger
from py_launch_blueprint.core.paths import APP_NAME

log = get_logger(__name__)


def instrument_metrics(app: FastAPI) -> None:
    """Expose RED metrics (rate/errors/duration per handler) at /metrics.

    Args:
        app: The application to instrument.
    """
    Instrumentator(
        excluded_handlers=["/metrics", "/healthz", "/readyz"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


def instrument_tracing(app: FastAPI) -> bool:
    """Set up an OTLP tracer and auto-instrument the app.

    Args:
        app: The application to instrument.

    Returns:
        True when tracing was wired. False (with a log line, never a crash)
        when the ``otel`` extra is not installed — tracing degrades to "off",
        the service still serves.
    """
    try:
        sdk_resources = importlib.import_module("opentelemetry.sdk.resources")
        sdk_trace = importlib.import_module("opentelemetry.sdk.trace")
        sdk_export = importlib.import_module("opentelemetry.sdk.trace.export")
        otlp = importlib.import_module(
            "opentelemetry.exporter.otlp.proto.http.trace_exporter"
        )
        trace_api = importlib.import_module("opentelemetry.trace")
        fastapi_instr = importlib.import_module("opentelemetry.instrumentation.fastapi")
    except ModuleNotFoundError:
        log.warning(
            "otel_unavailable",
            hint="install the 'otel' extra: uv sync --extra web --extra otel",
        )
        return False

    resource = sdk_resources.Resource.create({"service.name": f"{APP_NAME}-web"})
    # No explicit shutdown wiring needed: TracerProvider defaults to
    # shutdown_on_exit=True, registering an atexit hook that flushes the
    # BatchSpanProcessor — pending spans survive graceful shutdown (WEB-31).
    provider = sdk_trace.TracerProvider(resource=resource)
    # Exporter endpoint/headers come from the standard OTEL_EXPORTER_OTLP_*
    # env vars (collector default: http://localhost:4318).
    provider.add_span_processor(sdk_export.BatchSpanProcessor(otlp.OTLPSpanExporter()))
    trace_api.set_tracer_provider(provider)
    fastapi_instr.FastAPIInstrumentor.instrument_app(app)
    log.info("otel_tracing_enabled", service=f"{APP_NAME}-web")
    return True
