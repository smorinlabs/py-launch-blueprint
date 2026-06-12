#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""CI check: the manifest must cover every identity value *under its own field*.

For every value in BLUEPRINT_IDENTITY, every repo file that contains it must be
listed in a `[[replace]]` block whose `current` includes that value (or be a
`[[remove]]`/`[[regenerate]]` path, or live in the bootstrap init/ tree). This
is **per-field**, mirroring the engine: a file listed under `app_name` but not
`app_name_upper` that contains `PLBP` passes a flat-union check yet ships
half-renamed. `[[rename]]` sources are content-checked too — a rename moves the
filename, not the identity strings inside the file.

A failure means the rewrite engine would silently leave an occurrence untouched
on init, so a fork would ship half-renamed.

Exit 0  → every value is covered under its own field
Exit 1  → drift detected; print offending files and the uncovered value(s)

Usage:
    python init/ci/check_manifest_drift.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (
    BLUEPRINT_IDENTITY,
    REPO_ROOT,
    Manifest,
    is_bootstrap_path,
    iter_repo_files,
    load_manifest,
)


def covered_by_value(manifest: Manifest) -> dict[str, set[Path]]:
    """Map each identity *value* to the files that rewrite it.

    Mirrors the engine: a value is only rewritten in the files listed under a
    ``[[replace]]`` block whose ``current`` contains that value. Built per-value
    (not as a flat union of all blocks) so coverage is checked field-by-field.
    """
    coverage: dict[str, set[Path]] = {}
    for op in manifest.replaces:
        files = {(REPO_ROOT / f).resolve() for f in op.files}
        for value in op.current:
            coverage.setdefault(value, set()).update(files)
    return coverage


def uncovered_values(
    text: str, path: Path, coverage: dict[str, set[Path]]
) -> list[str]:
    """Identity values present in ``text`` but not covered for ``path``.

    Per-field: a value is "covered" only if ``path`` is listed under that
    value's own ``[[replace]]`` block. A file covered under ``app_name`` but not
    ``app_name_upper`` that contains ``PLBP`` is reported here — the flat-union
    predecessor missed exactly this case.
    """
    return [
        value
        for value in BLUEPRINT_IDENTITY.values()
        if value in text and path not in coverage.get(value, set())
    ]


def main() -> int:
    manifest = load_manifest()
    coverage = covered_by_value(manifest)

    # Files init deletes, regenerates, or resets wholesale are exempt — their
    # content is never rewritten in place ([[reset]] overwrites the file with a
    # fresh stub, so the blueprint identity it carries today is discarded, not
    # renamed). [[rename]] sources are deliberately NOT exempt: a rename moves
    # the *filename*, not the identity strings inside the file, so a
    # renamed-and-replaced file (e.g. docs/design/0001-…) must still be listed
    # under each value its content contains, verified independently here.
    exempt = {(REPO_ROOT / r.path).resolve() for r in manifest.removes}
    exempt |= {(REPO_ROOT / r.path).resolve() for r in manifest.regenerates}
    exempt |= {(REPO_ROOT / r.path).resolve() for r in manifest.resets}

    leftover: dict[Path, list[str]] = {}
    for path in iter_repo_files():
        if is_bootstrap_path(path):
            continue  # bootstrap tooling (init/, the agent skill), not migration targets
        resolved = path.resolve()
        if resolved in exempt:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # A value present in the file must be covered under THAT value's block.
        missing = uncovered_values(text, resolved, coverage)
        if missing:
            leftover[path] = missing

    if not leftover:
        print(
            "manifest-drift: ok — every identity value is covered under its own field."
        )
        return 0

    print(
        "manifest-drift: DRIFT detected — these files contain an identity value",
        "NOT listed under that value's own [[replace]] block, so the engine would",
        "leave it un-rewritten on init (a fork would ship half-renamed):",
    )
    for path, values in sorted(leftover.items()):
        rel = path.relative_to(REPO_ROOT)
        print(f"  {rel}  (uncovered: {', '.join(values)})")
    print(
        "\nFix: add the file to the [[replace]] block of each listed value",
        "(`uv run init/discover.py --summary` shows the expected per-field coverage).",
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
