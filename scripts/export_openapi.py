"""Export the canonical OpenAPI snapshot (WEB-51).

Writes the spec for a default-configured app to docs/api/openapi.json. The
snapshot is committed; tests/web/test_openapi_snapshot.py fails when routes
change without regenerating it, and .github/workflows/api-contract.yml runs
oasdiff against the base branch to flag breaking changes on PRs.

Usage:
    uv run --extra web python scripts/export_openapi.py  (or: just export-openapi)
"""

import json
import sys
from pathlib import Path

from py_launch_blueprint.web.app import create_app
from py_launch_blueprint.web.settings import WebSettings

DEFAULT_OUT = "docs/api/openapi.json"

# The committed snapshot is a version-independent contract (see export() below).
# Keep this in sync with tests/web/test_openapi_snapshot.py.
SNAPSHOT_VERSION = "0.0.0"


def export(out: str = DEFAULT_OUT) -> Path:
    """Generate and write the canonical OpenAPI snapshot.

    Args:
        out: Output path for the OpenAPI JSON file.

    Returns:
        The path the snapshot was written to.
    """
    # model_construct: pure field defaults, no env — the snapshot must not
    # depend on the exporting machine's environment.
    spec = create_app(WebSettings.model_construct()).openapi()
    # Pin info.version to a fixed sentinel so the committed snapshot is a pure
    # route/schema contract, independent of the package version. Otherwise the
    # snapshot goes stale on every release (the runtime spec derives its version
    # from package metadata) and either fails the snapshot test or has to be
    # re-bumped by release-please — which round-trips and reformats the whole
    # file. The real version stays single-sourced in pyproject.toml and is
    # guarded by tests/meta/test_version_consistency.py.
    spec["info"]["version"] = SNAPSHOT_VERSION
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    target = export(*sys.argv[1:2])
    print(f"wrote {target}")
