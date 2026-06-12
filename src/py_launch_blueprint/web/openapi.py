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

"""Canonical OpenAPI schema export (WL-026).

The committed schema at ``docs/api/openapi.json`` is the reviewable API
contract: ``tests/web/test_openapi_schema.py`` fails whenever the live app's
schema drifts from it, so every endpoint/model change shows up as an explicit
JSON diff in the PR. Regenerate after an intentional API change::

    just export-openapi
"""

import json
import sys
from pathlib import Path
from typing import Any

from py_launch_blueprint.web.app import create_app

#: ``info.version`` mirrors the package version, which release-please bumps on
#: every release. Pinning it keeps the committed contract diff-stable; clients
#: read the real version from a running service's ``/openapi.json``.
SCHEMA_VERSION_PLACEHOLDER = "0.0.0"


def build_openapi_schema() -> dict[str, Any]:
    """Return the app's OpenAPI schema, normalized for committing."""
    schema = create_app().openapi()
    schema["info"]["version"] = SCHEMA_VERSION_PLACEHOLDER
    return schema


def write_schema(target: Path) -> None:
    """Write the normalized schema to ``target`` (stable key order)."""
    payload = json.dumps(build_openapi_schema(), indent=2, sort_keys=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: ``python -m py_launch_blueprint.web.openapi <path>``."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(
            "usage: python -m py_launch_blueprint.web.openapi <output-path>",
            file=sys.stderr,
        )
        return 2
    write_schema(Path(args[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
