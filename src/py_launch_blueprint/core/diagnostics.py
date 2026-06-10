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

"""Environment/setup diagnostics for `plbp doctor`.

Pure logic: takes a resolved :class:`Config` and inspects the runtime, never
printing. The CLI renders the returned :class:`DoctorReport`.
"""

import platform
import sys

from py_launch_blueprint.core import paths
from py_launch_blueprint.core.config import TOKEN_ENV_VAR, Config
from py_launch_blueprint.core.models import DoctorCheck, DoctorReport

MIN_PYTHON = (3, 12)


def run_diagnostics(config: Config) -> DoctorReport:
    """Collect diagnostic checks for the current environment + config."""
    checks: list[DoctorCheck] = []

    v = sys.version_info
    py_ok = (v.major, v.minor) >= MIN_PYTHON
    checks.append(
        DoctorCheck(
            name="python",
            status="ok" if py_ok else "error",
            detail=f"{v.major}.{v.minor}.{v.micro}"
            + ("" if py_ok else f" (< {MIN_PYTHON[0]}.{MIN_PYTHON[1]} required)"),
        )
    )

    checks.append(DoctorCheck(name="platform", status="ok", detail=platform.platform()))

    cfg_path = config.config_path or paths.config_file()
    found = cfg_path.exists()
    checks.append(
        DoctorCheck(
            name="config-file",
            status="ok" if found else "warn",
            detail=f"{cfg_path} ({'found' if found else 'not found'})",
        )
    )

    if config.token:
        checks.append(
            DoctorCheck(
                name="token", status="ok", detail=f"present (source: {config.source})"
            )
        )
    else:
        checks.append(
            DoctorCheck(
                name="token",
                status="warn",
                detail=(
                    f"not set (supply via --token or ${TOKEN_ENV_VAR}; "
                    "never stored in config)"
                ),
            )
        )

    return DoctorReport(checks=checks)
