# Architecture Decision Records (ADRs)

An ADR captures **one architecturally significant decision** — the context, the
choice, and its consequences — so it isn't silently re-litigated later.

## Conventions

- **Filename:** `NNNN-kebab-title.md` (zero-padded, sequential). e.g.
  `0001-config-file-format.md`.
- **Status:** `Proposed` → `Accepted` → (`Superseded by NNNN` | `Deprecated`).
- **One decision per file.** Keep it short; link to the design doc or research
  that motivated it.
- **Immutable once Accepted.** To change a decision, write a new ADR that
  supersedes it (and update the old one's status), rather than editing history.

Start from [`template.md`](template.md).

## Index

| ADR | Title | Status |
|-----|-------|--------|
| —   | _none yet_ | — |

## Note on historical decisions

This project references earlier decisions by short id (e.g. `ADR-01` lefthook,
`ADR-06` uv_build, `ADR-07` trusted publishing) throughout the codebase and
commit history. Those were recorded in the maintainer's analysis workspace
before this directory existed. New decisions are recorded **here** going
forward; historical ADRs can be backfilled into this format as needed.
