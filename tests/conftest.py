"""Shared fixtures for the whole test suite."""

import logging

import pytest
from hypothesis import settings

# WL-013 — Hypothesis property tests run under load on the CI matrix; the
# default 200ms per-example deadline flakes there. Disable it (our strategies
# are cheap round-trips, not perf tests) so a slow shared runner never fails a
# correctness property. Registered + loaded once for the whole suite.
settings.register_profile("plbp", deadline=None)
settings.load_profile("plbp")


@pytest.fixture(autouse=True)
def _reset_root_logger():
    """Detach any handlers the CLI attached to the GLOBAL root logger.

    CLI invocations (CliRunner) call ``configure_logging``, which adds
    handlers to the root logger — including a RotatingFileHandler holding an
    open fd when a test exercises ``--log-file``. Without this reset those
    leak across tests, making later log capture order-dependent.
    """
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        if getattr(handler, "_plbp_owned", False):
            root.removeHandler(handler)
            handler.close()
    root.setLevel(logging.WARNING)
