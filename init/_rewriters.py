"""Per-file structured rewriters.

A rewriter has the signature:
    (path: Path, field: str, current_values: list[str], rep_map: dict[str, str]) -> bool

It returns True iff it changed the file's bytes. If a file in the manifest has
no registered rewriter, the engine falls back to longest-first text replacement
(see _engine.apply_replace_text).

Why this table is mostly empty today: blueprint identity values are highly
distinctive (`py_launch_blueprint`, `smorinlabs`, and the invented 4-char app
token `plbp`/`PLBP` — nothing that occurs incidentally in prose), so text mode
is provably safe for the current manifest. Structured rewriters are
the seam to add when a file appears whose format or naming collides with text
mode (e.g., a YAML key whose *name* contains an identity value, or a CHANGELOG
historical entry that must NOT be rewritten).

To add one: import lazily inside the function (so the engine stays
stdlib-only when this rewriter isn't called) and register at module scope.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

Rewriter = Callable[[Path, str, list[str], dict[str, str]], bool]

STRUCTURED_REWRITERS: dict[str, Rewriter] = {}
