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

"""Exception hierarchy and exit-code taxonomy.

Exit codes live here (not in the CLI layer) because *which failure maps to
which code* is domain knowledge shared by every front-end. The CLI re-exports
``ExitCode`` from ``py_launch_blueprint.cli.exit_codes`` for convenience.
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


class PyError(Exception):
    """Base class for all expected (handled) errors.

    Carries the exit code the CLI should return. Unexpected exceptions that do
    not derive from this class surface as ``ExitCode.IO`` plus a traceback when
    ``--verbose`` is set.
    """

    exit_code: ExitCode = ExitCode.API

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigError(PyError):
    """Configuration is missing or invalid."""

    exit_code = ExitCode.CONFIG


class AuthError(PyError):
    """Authentication/authorization failed (e.g. missing or rejected token)."""

    exit_code = ExitCode.AUTH


class APIError(PyError):
    """A remote API call failed."""

    exit_code = ExitCode.API
