# 0007. Did-you-mean suggestions via stdlib difflib

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer (interactive), implemented in PR #400
- **Related:** `cli/groups.py`; design 0001 (noun-verb command shape)

## Context

A mistyped noun or verb (`plbp porjects list`, `plbp projects lst`)
answered with a bare "No such command", leaving the user to run `--help`
and scan. git/gh-style "Did you mean …?" is table-stakes CLI polish, but
the obvious implementation (`click-didyoumean`) adds a dependency for ~20
lines of behavior.

## Decision

A single `SuggestingGroup(click.Group)` in `cli/groups.py` overrides
`resolve_command` and, on an unknown command, appends up to three close
matches computed with **stdlib `difflib.get_close_matches`** (cutoff 0.6,
the difflib default). The root group and every noun group use it, so
suggestions work at every level.

## Consequences

- Zero new dependencies; one small class any new noun group reuses by
  passing `cls=SuggestingGroup`.
- The intentional typo used by tests (`porjects`) is whitelisted in the
  codespell config with a rationale comment.
- Suggestion quality is bounded by difflib's ratio; exotic typos may get no
  suggestion (the plain error is preserved in that case).

## Alternatives considered

- **`click-didyoumean` dependency** — rejected: trivial to implement on
  stdlib; a template should not add dependencies for one-liner behavior.
- **Suggest only at the root group** — rejected: verbs are mistyped at
  least as often as nouns.
