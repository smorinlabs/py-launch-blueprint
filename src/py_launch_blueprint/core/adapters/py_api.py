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

"""HTTP adapter: the Py API implementation of :class:`ProjectsRepository`.

The transport half of the original ``ProjectsService`` (requests session, base
URL, request/error helpers, and the raw-dict → :class:`Project` mapping). It
returns ``None`` for absence and raises :class:`APIError` on transport failure
(HEX-12/HEX-13); the application service turns absence into a domain error.
"""

from typing import Any

import requests

from py_launch_blueprint.core.errors import APIError
from py_launch_blueprint.core.logging import get_logger
from py_launch_blueprint.core.models import Project

log = get_logger(__name__)

DEFAULT_TIMEOUT = 30  # seconds


class PyApiProjectsRepository:
    """Client for the Py projects API (satisfies ``ProjectsRepository``)."""

    BASE_URL = "https://app.py.com/api/1.0"

    def __init__(self, token: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        log.debug("api_request", method=method, path=path)
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        except requests.exceptions.RequestException as exc:
            message = self._extract_error(exc)
            log.warning("api_request_failed", path=path, error=message)
            raise APIError(f"API request failed: {message}") from exc

    @staticmethod
    def _extract_error(exc: requests.exceptions.RequestException) -> str:
        response = exc.response
        if response is None:
            return str(exc)
        try:
            payload = response.json()
        except ValueError:
            return str(exc)
        errors = payload.get("errors") or [{}]
        first = errors[0] if errors else {}
        message: str = first.get("message", str(exc))
        return message

    def resolve_workspace_gid(self, name: str) -> str | None:
        workspaces = self._request("GET", "/workspaces").get("data", [])
        match = next(
            (w for w in workspaces if w["name"].lower() == name.lower()),
            None,
        )
        return str(match["gid"]) if match else None

    def list_projects(
        self, *, workspace_gid: str | None = None, limit: int = 200
    ) -> list[Project]:
        params: dict[str, Any] = {
            "limit": limit,
            "opt_fields": "name,workspace.name",
        }
        if workspace_gid:
            params["workspace"] = workspace_gid

        raw = self._request("GET", "/projects", params=params).get("data", [])
        return [self._to_project(item) for item in raw]

    def get_project(self, project_id: str) -> Project | None:
        params = {"opt_fields": "name,workspace.name"}
        raw = self._request("GET", f"/projects/{project_id}", params=params).get(
            "data", {}
        )
        if not raw:
            return None
        return self._to_project(raw)

    @staticmethod
    def _to_project(item: dict[str, Any]) -> Project:
        workspace = item.get("workspace") or {}
        return Project(
            id=str(item.get("gid", item.get("id", ""))),
            name=item.get("name", ""),
            workspace=workspace.get("name"),
        )
