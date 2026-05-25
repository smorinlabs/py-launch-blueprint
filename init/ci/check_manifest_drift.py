#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""CI check: manifest must cover every live occurrence of every identity value.

Walks the repo, finds every occurrence of every value in BLUEPRINT_IDENTITY,
and asserts each occurrence falls inside a `[[replace]]` block's `files` list
(or is in a `[[rename]]` source path, or is in a `[[remove]]` path, or is in
the always-excluded init/ tree).

A failure here means the manifest fell out of date relative to the repo — new
code added an identity string the manifest doesn't know about, and the
rewrite engine would silently leave that occurrence untouched on init.

Exit 0  → manifest covers all live occurrences
Exit 1  → drift detected; print offending files

Usage:
    python init/ci/check_manifest_drift.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (  # noqa: E402
    BLUEPRINT_IDENTITY,
    INIT_DIR,
    REPO_ROOT,
    iter_repo_files,
    load_manifest,
)


def main() -> int:
    manifest = load_manifest()
    covered_files: set[Path] = set()
    for op in manifest.replaces:
        for f in op.files:
            covered_files.add((REPO_ROOT / f).resolve())
    rename_srcs = {(REPO_ROOT / r.src).resolve() for r in manifest.renames}
    remove_paths = {(REPO_ROOT / r.path).resolve() for r in manifest.removes}
    regenerate_paths = {(REPO_ROOT / r.path).resolve() for r in manifest.regenerates}

    leftover: dict[Path, list[str]] = {}
    for path in iter_repo_files():
        try:
            path.relative_to(INIT_DIR)
            continue
        except ValueError:
            pass
        resolved = path.resolve()
        if (
            resolved in rename_srcs
            or resolved in remove_paths
            or resolved in covered_files
            or resolved in regenerate_paths
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        hits: list[str] = []
        for value in BLUEPRINT_IDENTITY.values():
            if value in text:
                hits.append(value)
        if hits:
            leftover[path] = hits

    if not leftover:
        print("manifest-drift: ok — every identity occurrence is covered.")
        return 0

    print("manifest-drift: DRIFT detected — the following files contain identity",
          "values but are not listed in the manifest's [[replace]] / [[rename]] /",
          "[[remove]] sections:")
    for path, values in sorted(leftover.items()):
        rel = path.relative_to(REPO_ROOT)
        print(f"  {rel}  ({', '.join(values)})")
    print(
        "\nFix by re-running `uv run init/discover.py` and merging the new files into",
        "init/manifest.toml.",
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
