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

"""API versioning + deprecation helpers (WEB-02).

Business routers mount under :data:`V1_PREFIX`; operational endpoints
(``/healthz``, ``/readyz``, ``/metrics``) stay unversioned. Bumping the major
version means mounting a second router tree under ``/v2`` and marking the old
one deprecated — never mutating ``/v1`` responses in place.

To sunset a route, add the dependency AND flip OpenAPI's ``deprecated`` flag::

    @router.get(
        "/legacy",
        deprecated=True,
        dependencies=[Depends(deprecation_headers(date(2027, 1, 1)))],
    )
"""

from collections.abc import Callable, Coroutine
from datetime import UTC, date, datetime
from email.utils import format_datetime

from fastapi import Response

V1_PREFIX = "/v1"


def deprecation_headers(
    sunset: date,
) -> Callable[[Response], Coroutine[None, None, None]]:
    """Dependency factory stamping ``Deprecation`` + ``Sunset`` (RFC 8594)."""
    sunset_http = format_datetime(
        datetime(sunset.year, sunset.month, sunset.day, tzinfo=UTC), usegmt=True
    )

    async def _stamp(response: Response) -> None:
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = sunset_http

    return _stamp
