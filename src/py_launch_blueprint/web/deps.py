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

"""Shared dependencies: config access and core service wiring.

The web mirror of the CLI's ``AppContext``: config loads once (in the app
lifespan) and the token is only demanded by endpoints that need it, so
token-free endpoints (``/healthz``, ``/readyz``) never trigger lookup.
"""

from typing import Annotated

from fastapi import Depends, Request

from py_launch_blueprint.core.config import TOKEN_ENV_VAR, Config, load_config
from py_launch_blueprint.core.errors import AuthError
from py_launch_blueprint.core.services.projects import ProjectsService


def get_config(request: Request) -> Config:
    """The :class:`Config` loaded at startup (see ``app._lifespan``).

    Falls back to loading lazily when the lifespan hasn't run (raw ASGI
    callers like schemathesis) — load_config never raises on missing files.
    """
    config: Config | None = getattr(request.app.state, "config", None)
    if config is None:
        config = load_config()
        request.app.state.config = config
    return config


ConfigDep = Annotated[Config, Depends(get_config)]


def get_projects_service(config: ConfigDep) -> ProjectsService:
    """A :class:`ProjectsService` for the resolved token (401 when missing)."""
    if not config.token:
        raise AuthError(f"no API token configured (set ${TOKEN_ENV_VAR})")
    return ProjectsService(token=config.token)


ProjectsServiceDep = Annotated[ProjectsService, Depends(get_projects_service)]
