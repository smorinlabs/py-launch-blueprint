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

"""``python -m py_launch_blueprint.web`` — run the service with its settings.

Everything is settings-driven, no CLI flags: host, port, and the graceful
shutdown drain window come from
:class:`~py_launch_blueprint.web.settings.WebSettings` (``<APP_NAME>_WEB_HOST``
/ ``_PORT`` / ``_GRACEFUL_SHUTDOWN_SECONDS`` env vars; WEB-30/31). Dev reload
lives in ``just serve``; this entry point is the production-shaped one (also
used by the Dockerfile).
"""

import uvicorn

from py_launch_blueprint.web.settings import WebSettings


def main() -> None:
    settings = WebSettings()
    uvicorn.run(
        "py_launch_blueprint.web.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        timeout_graceful_shutdown=settings.graceful_shutdown_seconds,
    )


if __name__ == "__main__":
    main()
