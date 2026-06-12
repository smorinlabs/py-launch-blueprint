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

"""Exception hierarchy, exit-code taxonomy, and stable error codes.

Exit codes live here (not in the CLI layer) because *which failure maps to
which code* is domain knowledge shared by every front-end. The CLI re-exports
``ExitCode`` from ``py_launch_blueprint.cli.exit_codes`` for convenience.

Error codes (``PLBP###``) are finer-grained than exit codes: many error codes
may share one exit code, so scripts can branch on the number while docs and
issue reports reference the precise failure. Both tables are append-only.
"""

from enum import IntEnum


class ExitCode(IntEnum):
    """Process exit codes (documented in EXAMPLECLI.md).

    Keep this table stable and append-only: scripts depend on the numbers.
    """

    SUCCESS = 0
    CONFIG = 1
    AUTH = 2
    API = 3
    IO = 4
    INTERRUPT = 5


#: Stable error-code strings (documented in EXAMPLECLI.md). Append-only:
#: scripts and issue reports reference these. A new error class claims the
#: next free number; numbers are never reused or renumbered.
ERROR_CODE_UNEXPECTED = "PLBP000"
ERROR_CODE_CONFIG = "PLBP001"
ERROR_CODE_AUTH = "PLBP002"
ERROR_CODE_API = "PLBP003"
ERROR_CODE_INTERRUPT = "PLBP004"


class PyError(Exception):
    """Base class for all expected (handled) errors.

    Carries the exit code the CLI should return, a stable ``error_code``
    string, and an optional ``hint`` — one actionable next step rendered
    under the error message. Unexpected exceptions that do not derive from
    this class surface as ``ExitCode.IO`` plus a pointer to the crash log
    (and an inline traceback when ``--verbose`` is set).
    """

    exit_code: ExitCode = ExitCode.API
    error_code: str = ERROR_CODE_API

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ConfigError(PyError):
    """Configuration is missing or invalid."""

    exit_code = ExitCode.CONFIG
    error_code = ERROR_CODE_CONFIG


class AuthError(PyError):
    """Authentication/authorization failed (e.g. missing or rejected token)."""

    exit_code = ExitCode.AUTH
    error_code = ERROR_CODE_AUTH


class APIError(PyError):
    """A remote API call failed."""

    exit_code = ExitCode.API
    error_code = ERROR_CODE_API
