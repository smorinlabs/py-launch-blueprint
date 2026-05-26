#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""CI check: every manifest-listed file must trigger init-integration.

If `.github/workflows/init-integration.yml` declares a `paths:` filter on its
PR/push triggers, this check asserts every file the manifest references is
matched by at least one path pattern. Otherwise a PR that modifies *only*
that file would silently skip the integration matrix — a real gap caught by
the weekly cron at best, by a downstream user at worst.

If the workflow has NO `paths:` filter (strict mode — runs on every PR), this
check passes trivially with a one-line note. The check stays useful as
insurance against any future regression to permissive mode with an
incomplete filter.

Exit codes:
  0  ok (filter complete OR no filter present)
  1  drift detected: manifest files exist that the filter doesn't cover
  2  internal error (can't read workflow / manifest)

Usage:
    python init/ci/check_path_filter.py
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, load_manifest

WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "init-integration.yml"


def _collect_manifest_files() -> set[str]:
    """Every file the manifest references — replace/rename/remove/regenerate."""
    m = load_manifest()
    files: set[str] = set()
    for r in m.replaces:
        files.update(r.files)
    files.update(r.src for r in m.renames)
    files.update(r.path for r in m.removes)
    files.update(r.path for r in m.regenerates)
    return files


def _collect_workflow_paths() -> set[str]:
    """Union of `paths:` lists across pull_request and push triggers.

    Returns an empty set if no `paths:` filter exists on either trigger
    (strict mode — workflow runs on every PR).
    """
    import yaml

    if not WORKFLOW_PATH.exists():
        raise FileNotFoundError(f"{WORKFLOW_PATH} not found")
    doc = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    # PyYAML quirk: bare `on:` key is parsed as the YAML boolean True.
    triggers = doc.get("on", doc.get(True, {}))
    if not isinstance(triggers, dict):
        return set()
    out: set[str] = set()
    for trig in ("pull_request", "push"):
        t = triggers.get(trig, {})
        if isinstance(t, dict) and "paths" in t and isinstance(t["paths"], list):
            out.update(t["paths"])
    return out


def _gh_path_matches(path: str, pattern: str) -> bool:
    """GitHub Actions paths-filter style matching.

    `**` matches across directory boundaries; single `*` matches within one
    path segment. Exact strings match exactly. This is a faithful-enough
    implementation for the patterns the workflow actually uses.
    """
    if "**" in pattern:
        regex = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
        return re.fullmatch(regex, path) is not None
    if "*" in pattern:
        return fnmatch.fnmatchcase(path, pattern)
    return path == pattern


def main() -> int:
    try:
        manifest_files = _collect_manifest_files()
        workflow_paths = _collect_workflow_paths()
    except Exception as e:
        print(f"check_path_filter: internal error — {e}", file=sys.stderr)
        return 2

    if not workflow_paths:
        print(
            "check_path_filter: no `paths:` filter on init-integration.yml — "
            "strict mode (workflow runs on every PR). Check trivially passes."
        )
        return 0

    missing: list[str] = []
    for f in sorted(manifest_files):
        if not any(_gh_path_matches(f, p) for p in workflow_paths):
            missing.append(f)

    if missing:
        print(
            f"check_path_filter: DRIFT — {len(missing)} manifest files not "
            f"covered by init-integration.yml `paths:` filter. A PR that "
            f"modifies only one of these would skip the integration matrix:",
            file=sys.stderr,
        )
        for f in missing[:20]:
            print(f"  {f}", file=sys.stderr)
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more", file=sys.stderr)
        print(
            "\nFix by either: (a) extend the workflow's `paths:` to cover these "
            "files, or (b) remove the `paths:` filter entirely (strict mode).",
            file=sys.stderr,
        )
        return 1

    print(
        f"check_path_filter: ok — all {len(manifest_files)} manifest files "
        f"matched by one of {len(workflow_paths)} path patterns."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
