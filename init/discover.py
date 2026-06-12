#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Phase-0 discovery: scan blueprint identity strings, emit draft manifest.toml.

One-off tool. Reads the live repo, finds every occurrence of every value in
common.BLUEPRINT_IDENTITY, groups by (field, mode), and emits a manifest draft
to stdout (or `-o PATH`). Intended for human review before commit.

Mode heuristic:
- TOML files                          → "structured"
- everything else                     → "text"

Rename candidates (path names containing an identity value) are emitted as
[[rename]] blocks. Lockfiles are emitted as [[regenerate]] blocks. Binary
files are reported in the discovery summary but never put into [[replace]].

Usage (from repo root):
    uv run init/discover.py                       # write to stdout
    uv run init/discover.py -o init/manifest.toml # write to file
    uv run init/discover.py --summary             # human-readable summary only
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    BLUEPRINT_IDENTITY,
    REPO_ROOT,
    is_bootstrap_path,
    iter_repo_files,
)

LOCKFILES = {"uv.lock", "bun.lock"}
# Files reset to a fresh stub on init (the blueprint's own history a fork must
# not inherit), so their identity strings are discarded, not rewritten.
RESET_FILES = {"CHANGELOG.md"}
CHANGELOG_STUB = "# Changelog\n"
STRUCTURED_SUFFIXES = {".toml"}


def file_mode(path: Path) -> str:
    return "structured" if path.suffix in STRUCTURED_SUFFIXES else "text"


def is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
    except OSError:
        return True
    return b"\x00" in chunk


def scan_files(files: Iterable[Path]) -> dict[tuple[str, str], dict[Path, int]]:
    """Map (field, mode) → {file: count}.

    Excludes files under the bootstrap dirs (init/, the agent skill) that reference
    identity strings as *data*, not as identity that should be rewritten.
    """
    hits: dict[tuple[str, str], dict[Path, int]] = defaultdict(dict)
    for path in files:
        if is_bootstrap_path(path):
            continue  # bootstrap tooling, not migration targets
        if path.name in LOCKFILES:
            continue  # lockfiles are regenerated, not replaced
        if path.name in RESET_FILES:
            continue  # reset to a stub on init, not identity-rewritten
        if is_binary(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        mode = file_mode(path)
        for fieldname, value in BLUEPRINT_IDENTITY.items():
            count = text.count(value)
            if count:
                hits[(fieldname, mode)][path] = count
    return hits


def find_renames(root: Path = REPO_ROOT) -> list[tuple[str, str]]:
    """Path-name hits that imply a [[rename]] block.

    Returns [(src_rel, dst_template)] sorted longest-first so package-dir
    rename happens before any nested file rename.
    """
    renames: list[tuple[str, str]] = []
    for path in root.rglob("*"):
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if not rel_parts or rel_parts[0] in {
            ".git",
            "node_modules",
            ".venv",
            "dist",
            "build",
        }:
            continue
        if any(
            part.startswith("init") and len(rel_parts) > 1 and rel_parts[0] == "init"
            for part in [rel_parts[0]]
        ):
            continue
        rel = path.relative_to(root)
        rel_str = str(rel)
        for fieldname, value in BLUEPRINT_IDENTITY.items():
            if value in rel.name and fieldname in {"package_name", "repo_name"}:
                template_token = "{" + fieldname + "}"
                new_name = rel.name.replace(value, template_token)
                new_rel = rel.with_name(new_name)
                renames.append((rel_str, str(new_rel)))
                break
    renames.sort(key=lambda pair: -len(pair[0]))
    return renames


def find_removes() -> list[tuple[str, str]]:
    """Files that should be removed during init (blueprint-only artifacts).

    Conservative: only the guard CI workflow (§4.6) and this discovery script.
    Other candidates (docs/source/github-templates.md per §6 open item) are
    left for human review.
    """
    candidates = [
        (".github/workflows/blueprint-guard.yml", "guard CI is blueprint-only"),
        ("init/discover.py", "Phase-0 one-off discovery script"),
    ]
    return [
        c
        for c in candidates
        if (REPO_ROOT / c[0]).exists() or c[0].startswith("init/discover")
    ]


def find_regenerates() -> list[tuple[str, list[str]]]:
    return [
        ("uv.lock", ["uv", "lock"]),
        ("bun.lock", ["bun", "install"]),
    ]


def find_resets() -> list[tuple[str, str]]:
    return [("CHANGELOG.md", CHANGELOG_STUB)]


def _toml_str(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def format_toml(
    hits: dict[tuple[str, str], dict[Path, int]],
    renames: list[tuple[str, str]],
    removes: list[tuple[str, str]],
    regenerates: list[tuple[str, list[str]]],
    resets: list[tuple[str, str]],
) -> str:
    out: list[str] = []
    out.append("# init/manifest.toml — DRAFT generated by init/discover.py.")
    out.append("# Review carefully:")
    out.append("#   * 'text' mode does naive longest-first string replacement;")
    out.append("#     re-classify intent-bearing files as 'structured' as needed.")
    out.append("#   * Some occurrences are historical (CHANGELOG entries, vendored")
    out.append("#     copies) and should be excluded from the file list.")
    out.append("#   * Re-run `uv run init/discover.py --summary` to verify coverage.")
    out.append("")

    for fieldname, mode in sorted(hits.keys()):
        files = hits[(fieldname, mode)]
        total = sum(files.values())
        out.append(
            f"# {fieldname} ({mode}) — {total} occurrences in {len(files)} files"
        )
        out.append("[[replace]]")
        out.append(f'field   = "{fieldname}"')
        out.append(f'current = ["{BLUEPRINT_IDENTITY[fieldname]}"]')
        out.append("files   = [")
        for p in sorted(files):
            rel = p.relative_to(REPO_ROOT)
            out.append(f'  "{rel}",   # {files[p]}x')
        out.append("]")
        out.append(f'mode    = "{mode}"')
        out.append("")

    for src, dst in renames:
        out.append("[[rename]]")
        out.append(f'from = "{src}"')
        out.append(f'to   = "{dst}"')
        out.append("")

    for path, reason in removes:
        out.append("[[remove]]")
        out.append(f'path   = "{path}"')
        out.append(f'reason = "{reason}"')
        out.append("")

    for path, cmd in regenerates:
        out.append("[[regenerate]]")
        out.append(f'path    = "{path}"')
        cmd_str = ", ".join(f'"{c}"' for c in cmd)
        out.append(f"command = [{cmd_str}]")
        out.append("")

    for path, stub in resets:
        out.append("[[reset]]")
        out.append(f'path = "{path}"')
        out.append(f"stub = {_toml_str(stub)}")
        out.append("")

    return "\n".join(out)


def format_summary(hits: dict[tuple[str, str], dict[Path, int]]) -> str:
    out: list[str] = []
    out.append("Discovery summary")
    out.append("=================")
    grand_total = 0
    grand_files: set[Path] = set()
    for (fieldname, mode), files in sorted(hits.items()):
        total = sum(files.values())
        grand_total += total
        grand_files.update(files.keys())
        out.append(
            f"  {fieldname:<14} [{mode:<10}]  {total:>4} x in {len(files):>3} files"
        )
    out.append(
        f"  {'TOTAL':<14} {'':<12}  {grand_total:>4} x in {len(grand_files):>3} files"
    )
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, help="write manifest TOML to PATH")
    parser.add_argument("--summary", action="store_true", help="print summary only")
    args = parser.parse_args()

    files = iter_repo_files()
    hits = scan_files(files)

    if args.summary:
        sys.stdout.write(format_summary(hits) + "\n")
        return 0

    renames = find_renames()
    removes = find_removes()
    regenerates = find_regenerates()
    resets = find_resets()
    rendered = format_toml(hits, renames, removes, regenerates, resets)

    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
        sys.stderr.write(format_summary(hits) + "\n")
        sys.stderr.write(f"\nwrote {args.output}\n")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
