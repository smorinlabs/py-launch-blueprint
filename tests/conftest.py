"""Shared fixtures for the whole test suite."""

import logging

import pytest


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
