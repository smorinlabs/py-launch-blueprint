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

"""Typed web-service settings — 12-factor configuration (WEB-30).

Every knob resolves from an env var with the ``<APP_NAME>_WEB_`` prefix
(derived from the single ``APP_NAME`` source in ``core/paths.py``, so a fork's
rename keeps working). Validation happens at construction, so a misconfigured
deployment fails loudly at boot instead of silently at request time.

List values parse from JSON, e.g.::

    PLBP_WEB_CORS_ORIGINS='["https://app.example.com"]'
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from py_launch_blueprint.core.paths import APP_NAME

ENV_PREFIX: str = f"{APP_NAME.upper()}_WEB_"


class WebSettings(BaseSettings):
    """Runtime configuration for the web service."""

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, extra="ignore")

    #: Bind address for ``python -m py_launch_blueprint.web`` (loopback by
    #: default; set 0.0.0.0 explicitly for containers — see Dockerfile).
    host: str = "127.0.0.1"
    port: int = 8000
    #: ASGI root path when served behind a path-stripping proxy.
    root_path: str = ""
    #: Console (stderr) log level. INFO by default — a server logs its
    #: lifecycle and one canonical `http_request` event per request (WEB-12),
    #: unlike the CLI's quiet WARNING default.
    log_level: Literal["debug", "info", "warning", "error", "critical"] = "info"
    #: Log render mode: "json" (default — structured JSONL, what collectors
    #: parse), "console" (pretty, dev; `just serve` sets this), or "auto"
    #: (TTY-based, the CLI behavior).
    log_format: Literal["auto", "console", "json"] = "json"
    #: CORS allowlist. Empty (the default) means the CORS middleware is not
    #: installed at all — cross-origin browser calls are opt-in (WEB-23).
    cors_origins: list[str] = []
    #: Expose Prometheus RED metrics at /metrics (WEB-11).
    metrics_enabled: bool = True
    #: Enable OpenTelemetry tracing (WEB-10). Requires the `otel` extra and
    #: the standard OTEL_EXPORTER_OTLP_* env vars for the exporter.
    otel_enabled: bool = False
    #: Default rate limit, e.g. "100/minute" (`limits` notation). None (the
    #: default) disables rate limiting entirely (WEB-22).
    rate_limit: str | None = None
    #: Idempotency-Key replay cache tuning (WEB-05).
    idempotency_ttl_seconds: int = 86400
    idempotency_max_entries: int = 1024
    #: Drain window for in-flight requests on shutdown (WEB-31); used by the
    #: ``python -m py_launch_blueprint.web`` runner (and the Dockerfile).
    graceful_shutdown_seconds: int = 10
