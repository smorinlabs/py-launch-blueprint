"""Manifest schema + round-trip tests.

Loading the live manifest must succeed, every blueprint field must be covered
by at least one [[replace]] block, and rename templates must be resolvable
against any valid Answers object.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

INIT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(INIT_DIR))

from _engine import Answers, _resolve_renames, _replacement_map  # noqa: E402
from common import (  # noqa: E402
    BLUEPRINT_IDENTITY,
    MANIFEST_PATH,
    load_manifest,
)


def test_manifest_loads() -> None:
    m = load_manifest(MANIFEST_PATH)
    assert m.replaces, "manifest has no [[replace]] blocks"


def test_every_identity_field_has_at_least_one_replace_block() -> None:
    m = load_manifest(MANIFEST_PATH)
    covered = {r.field for r in m.replaces}
    missing = set(BLUEPRINT_IDENTITY) - covered
    assert not missing, f"fields with no [[replace]] block: {sorted(missing)}"


def test_replace_blocks_have_valid_mode() -> None:
    m = load_manifest(MANIFEST_PATH)
    for r in m.replaces:
        assert r.mode in ("structured", "text"), f"unknown mode {r.mode!r} for {r.field!r}"


def test_replace_blocks_enumerate_current_values_against_identity() -> None:
    """Every `current` value must match the live BLUEPRINT_IDENTITY for that field."""
    m = load_manifest(MANIFEST_PATH)
    for r in m.replaces:
        expected = BLUEPRINT_IDENTITY[r.field]
        assert expected in r.current, (
            f"[[replace]] field={r.field!r} current={r.current!r} "
            f"does not include the canonical value {expected!r}"
        )


def test_rename_templates_resolve_cleanly() -> None:
    answers = Answers(
        package_name="acme_widget",
        repo_name="acme-widget",
        command_name="acme",
        author="Jane",
        email="j@example.com",
        owner="acmecorp",
    )
    m = load_manifest(MANIFEST_PATH)
    resolved = _resolve_renames(m.renames, answers)
    for r in resolved:
        assert "{" not in r.dst, f"unresolved template in {r.dst!r}"
        assert "}" not in r.dst, f"unresolved template in {r.dst!r}"


def test_replacement_map_is_longest_first() -> None:
    answers = Answers(
        package_name="a", repo_name="b", command_name="c",
        author="d", email="e", owner="f",
    )
    rep = _replacement_map(answers)
    keys = list(rep.keys())
    lengths = [len(k) for k in keys]
    assert lengths == sorted(lengths, reverse=True), (
        f"replacement map is not longest-first: {lengths}"
    )


def test_manifest_is_valid_toml() -> None:
    raw = MANIFEST_PATH.read_text(encoding="utf-8")
    tomllib.loads(raw)
