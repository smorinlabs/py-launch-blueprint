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

"""FastAPI web service — a thin adapter over ``py_launch_blueprint.core``.

Ships behind the ``web`` extra (``pip install py-launch-blueprint[web]`` /
``uv sync --extra web``). Layout::

    web/
    ├── app.py          # FastAPI app factory: create_app() -> FastAPI
    ├── deps.py         # shared dependencies (config, service wiring)
    └── routers/
        └── projects.py # /projects → core.services + core.models

Design rule: the web layer, like the CLI, is a *thin* adapter over
``py_launch_blueprint.core``. It returns ``core.models`` objects directly as
JSON responses, so the API and the CLI share one data contract. Run locally
with ``just serve``.
"""

try:
    from py_launch_blueprint.web.app import create_app
except ModuleNotFoundError as exc:  # pragma: no cover - import-time guard
    if exc.name and exc.name.split(".")[0] in {"fastapi", "starlette"}:
        raise ModuleNotFoundError(
            "the web service requires the 'web' extra: "
            "pip install 'py-launch-blueprint[web]' (or: uv sync --extra web)"
        ) from exc
    raise

__all__ = ["create_app"]
