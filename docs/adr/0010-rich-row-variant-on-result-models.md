# 0010. Terminal niceties via a rich-only row variant on result models

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer (interactive + CodeRabbit review), implemented in PR #400
- **Related:** `core/models.py`; `core/format.py`; ADR 0003 (output modes)

## Context

Terminal niceties (OSC-8 hyperlinks, relative timestamps) belong only in
interactive text output — JSON must stay raw fields + ISO-8601 UTC and
Markdown must stay plain text. But the result models in `core/models.py`
are the single source of truth for tabulation (`table_columns`,
`table_rows`), and `core` is documented as "no printing". Where do
presentation-flavored strings live?

## Decision

Result models gain an optional **`table_rows_rich()`** hook, defaulting to
`table_rows()`, consumed **only by the text renderer**. Helpers live in
`core/format.py` as pure string functions: `relative_time()` (coarse human
deltas; naive datetimes treated as UTC) and `rich_link()` (OSC-8 markup
with the link text **escaped**, so data containing `[` renders literally
instead of parsing as markup — a review finding). `ConfigPath` hyperlinks
its path as the working example.

This is an extension of the existing compromise, not a new leak: models
already encode presentation (column headers, row stringification); the
rich variant is one more representation of the same data, and `core` still
never prints.

## Consequences

- JSON and Markdown output are provably unaffected (they read the plain
  representations; tests pin this).
- Rich strips the styling itself for non-terminal destinations, so the
  hook needs no TTY awareness in models.
- Forks adding models with URLs or timestamps get the pattern for free.

## Alternatives considered

- **Renderer-side type switching** (renderer decorates known model types) —
  rejected: `isinstance` ladders in the renderer couple it to every model.
- **Structured cell metadata** (models return URL/timestamp objects, the
  renderer formats) — rejected for now: heavier machinery than the
  template needs; the hook can evolve into it without breaking callers.
