# 0003. Keep `markdown` as a third output format (spec deviation)

- **Status:** Accepted
- **Date:** 2026-06-09
- **Deciders:** maintainer (interactive), implemented in PR #378
- **Related:** [design 0001](../design/0001-plbp-cli-conventions.md) §3 (R3.2)

## Context

Spec R3.2 allows exactly two output formats: `text` (default) and `json`.
The CLI had already shipped a third, `markdown`, rendering any result model
as a GitHub-flavored table — useful for pasting into issues/PRs and cheap to
maintain because every command renders through one `Renderer` and one result
model.

## Decision

Keep `markdown` as a deliberate superset of the spec:
`-o text|json|markdown`, default `text`. The config schema
(`output.format`) accepts the same three values.

## Consequences

- The spec and implementation intentionally differ on R3.2; design 0001
  carries a deviation note pointing here.
- Every future result model must keep rendering through the shared
  table-shape contract (columns/rows), which is what makes the third format
  free.

## Alternatives considered

- **Strict spec compliance (drop markdown)** — rejected: removing a shipped,
  zero-marginal-cost format to satisfy a list the spec can simply note.
- **Add it to the spec instead** — equivalent outcome; the deviation note +
  this ADR records the decision without rewriting a versioned requirements
  doc.
