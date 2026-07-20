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
URL, request/error helpers, and the payload → :class:`Project` mapping). It
returns ``None`` for absence and raises :class:`APIError` on transport failure
(HEX-12/HEX-13); the application service turns absence into a domain error.

This module is the one place the process ingests data it does not control, so
it is where the AGENTS.md boundary rule applies: every response is validated
into a private ``_*`` model *before* anything reaches the domain (P04). Nothing
inward of here sees ``Any``, and upstream schema drift raises instead of
degrading into an empty-id ``Project`` or an empty list that reads to the user
as "no projects found".
"""

from collections.abc import Mapping
from typing import Annotated, Literal, overload

import requests
from pydantic import (
    AliasChoices,
    BaseModel,
    BeforeValidator,
    Field,
    ValidationError,
    field_validator,
)

from py_launch_blueprint.core.errors import APIError
from py_launch_blueprint.core.logging import get_logger
from py_launch_blueprint.core.models import Project

log = get_logger(__name__)

DEFAULT_TIMEOUT = 30  # seconds


# --- boundary models: the upstream wire format, not the domain ---------------


def _numeric_to_str(value: object) -> object:
    """Accept a numeric gid where the upstream normally sends a string.

    Applied per *field* rather than model-wide (`coerce_numbers_to_str`),
    because the old code's `str(...)` only ever wrapped the gid: a numeric
    `name` is drift and must still fail.
    """
    if isinstance(value, bool):  # bool subclasses int, but is never a gid
        return value
    return str(value) if isinstance(value, int | float) else value


_Gid = Annotated[str, BeforeValidator(_numeric_to_str)]


class _WorkspaceRef(BaseModel):
    """The nested workspace stub carried inside a project payload."""

    name: str


class _ProjectPayload(BaseModel):
    """One project as the upstream sends it.

    ``id`` and ``name`` are required on purpose: a payload that cannot fill
    them is drift, and the point of P04 is to say so rather than substitute an
    empty string that looks like a real project downstream.
    """

    id: _Gid = Field(validation_alias=AliasChoices("gid", "id"))
    name: str
    workspace: _WorkspaceRef | None = None

    @field_validator("workspace", mode="before")
    @classmethod
    def _empty_workspace_is_absent(cls, value: object) -> object:
        # Upstream sends {} — not a missing key — for a project with no
        # workspace, which is what the old ``item.get("workspace") or {}``
        # absorbed. Absorb exactly that, plus null. Other falsy values ("", [],
        # 0, false) are the wrong *type* for this field rather than an empty
        # one, so they fall through to the model and raise: "lenient on empty"
        # is not "lenient on anything that happens to be falsy".
        return None if value is None or value == {} else value


class _Workspace(BaseModel):
    """A workspace from ``/workspaces`` — unlike the nested ref, it has a gid."""

    gid: _Gid
    name: str


class _ProjectListEnvelope(BaseModel):
    """``data`` is required: a renamed envelope key must raise, not read as []."""

    data: list[_ProjectPayload]


class _ProjectEnvelope(BaseModel):
    """Absence is a 404, so a 200 here must carry a project or be drift."""

    data: _ProjectPayload


class _WorkspaceListEnvelope(BaseModel):
    data: list[_Workspace]


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

    # Two signatures, one implementation: only a caller that opts into
    # ``allow_not_found`` can receive None, so the other call sites get a
    # non-optional model back instead of a None-check that can never fire.
    @overload
    def _request[T: BaseModel](
        self,
        method: str,
        path: str,
        *,
        response_model: type[T],
        allow_not_found: Literal[False] = False,
        params: Mapping[str, str | int] | None = None,
    ) -> T: ...

    @overload
    def _request[T: BaseModel](
        self,
        method: str,
        path: str,
        *,
        response_model: type[T],
        allow_not_found: Literal[True],
        params: Mapping[str, str | int] | None = None,
    ) -> T | None: ...

    def _request[T: BaseModel](
        self,
        method: str,
        path: str,
        *,
        response_model: type[T],
        allow_not_found: bool = False,
        params: Mapping[str, str | int] | None = None,
    ) -> T | None:
        """Fetch, then validate into ``response_model``.

        ``None`` means one thing only: the upstream legitimately answered 404
        for a by-id lookup.
        """
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        log.debug("api_request", method=method, path=path)
        try:
            response = self.session.request(
                method, url, timeout=self.timeout, params=params
            )
            # A 404 is a legitimate "absent" answer for by-id lookups, not a
            # transport failure: the caller returns None and the service
            # raises the domain not-found error (HEX-12). This is now the ONLY
            # path that yields None — a 200 we cannot parse raises below
            # instead of sharing this channel, which is what previously let
            # schema drift masquerade as "not found".
            if allow_not_found and response.status_code == 404:
                return None
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.RequestException as exc:
            message = self._extract_error(exc)
            log.warning("api_request_failed", path=path, error=message)
            raise APIError(f"API request failed: {message}") from exc

        try:
            return response_model.model_validate(payload)
        except ValidationError as exc:
            detail = self._describe_validation_error(exc)
            log.warning("api_response_invalid", path=path, error=detail)
            raise APIError(f"unexpected API response from {path}: {detail}") from exc

    @staticmethod
    def _describe_validation_error(exc: ValidationError) -> str:
        """Summarize why a payload failed validation, for the user-facing error.

        Deliberately reports the location and reason but NOT the offending
        value: we do not control what the upstream puts in a payload, and this
        string lands in both the raised error and the log. The trailing count
        is what distinguishes one odd record from a version bump — a caller
        seeing "+2 more" knows the schema moved, not that one row is bad.
        """
        errors = exc.errors()
        first = errors[0]
        # loc is a tuple of keys and list indices — "data.2.workspace.name" —
        # so the int members need stringifying before the join.
        location = ".".join(str(part) for part in first["loc"])
        remainder = f" (+{len(errors) - 1} more)" if len(errors) > 1 else ""
        return f"{location} — {first['msg']}{remainder}"

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
        envelope = self._request(
            "GET", "/workspaces", response_model=_WorkspaceListEnvelope
        )
        match = next(
            (w for w in envelope.data if w.name.lower() == name.lower()),
            None,
        )
        return match.gid if match else None

    def list_projects(
        self, *, workspace_gid: str | None = None, limit: int = 200
    ) -> list[Project]:
        params: dict[str, str | int] = {
            "limit": limit,
            "opt_fields": "name,workspace.name",
        }
        if workspace_gid:
            params["workspace"] = workspace_gid

        envelope = self._request(
            "GET", "/projects", response_model=_ProjectListEnvelope, params=params
        )
        return [self._to_project(item) for item in envelope.data]

    def get_project(self, project_id: str) -> Project | None:
        envelope = self._request(
            "GET",
            f"/projects/{project_id}",
            response_model=_ProjectEnvelope,
            params={"opt_fields": "name,workspace.name"},
            allow_not_found=True,
        )
        if envelope is None:
            return None
        return self._to_project(envelope.data)

    @staticmethod
    def _to_project(item: _ProjectPayload) -> Project:
        # Total: no .get(), no defaults. Validation already guaranteed the
        # fields are present, so there is nothing left to paper over.
        return Project(
            id=item.id,
            name=item.name,
            workspace=item.workspace.name if item.workspace else None,
        )
