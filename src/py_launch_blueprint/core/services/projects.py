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

"""Projects service — talks to the Py API and returns typed models.

This is the library half of the old ``projects.py``: pure logic, no printing,
no Click. It raises ``APIError`` on failure and returns ``Project`` models on
success so the same data can be rendered as human text, JSON, or Markdown.
"""

from typing import Any

import requests

from py_launch_blueprint.core.errors import APIError
from py_launch_blueprint.core.logging import get_logger
from py_launch_blueprint.core.models import Project

log = get_logger(__name__)

DEFAULT_TIMEOUT = 30  # seconds


class ProjectsService:
    """Client for the Py projects API."""

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

    def _resolve_workspace_gid(self, workspace_name: str) -> str:
        workspaces = self._request("GET", "/workspaces").get("data", [])
        match = next(
            (w for w in workspaces if w["name"].lower() == workspace_name.lower()),
            None,
        )
        if not match:
            raise APIError(f"Workspace not found: {workspace_name}")
        gid: str = match["gid"]
        return gid

    def list_projects(
        self, workspace: str | None = None, limit: int = 200
    ) -> list[Project]:
        """List projects, optionally filtered by workspace name."""
        params: dict[str, Any] = {
            "limit": limit,
            "opt_fields": "name,workspace.name",
        }
        if workspace:
            params["workspace"] = self._resolve_workspace_gid(workspace)

        raw = self._request("GET", "/projects", params=params).get("data", [])
        return [self._to_project(item) for item in raw]

    def get_project(self, project_id: str) -> Project:
        """Fetch a single project by its gid."""
        params = {"opt_fields": "name,workspace.name"}
        raw = self._request("GET", f"/projects/{project_id}", params=params).get(
            "data", {}
        )
        if not raw:
            raise APIError(f"Project not found: {project_id}")
        return self._to_project(raw)

    @staticmethod
    def _to_project(item: dict[str, Any]) -> Project:
        workspace = item.get("workspace") or {}
        return Project(
            id=str(item.get("gid", item.get("id", ""))),
            name=item.get("name", ""),
            workspace=workspace.get("name"),
        )
