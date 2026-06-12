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
| [0001](0001-app-short-name-plbp.md) | App short name `plbp` (hard rename from `pylb`) | Accepted |
| [0002](0002-no-secrets-in-config-file.md) | Secrets are never stored in the config file | Accepted |
| [0003](0003-keep-markdown-output-mode.md) | Keep `markdown` as a third output format (spec deviation) | Accepted |
| [0004](0004-config-errors-degrade-to-warnings.md) | Invalid config values degrade to warnings, never crashes | Accepted |
| [0005](0005-mise-flox-first-class-toolchains.md) | mise and flox are first-class toolchain provisioners (lean 10-tool set) | Accepted |

## Note on historical decisions

This project references earlier decisions by short id (e.g. `ADR-01` lefthook,
`ADR-06` uv_build, `ADR-07` trusted publishing) throughout the codebase and
commit history. Those were recorded in the maintainer's analysis workspace
before this directory existed. New decisions are recorded **here** going
forward; historical ADRs can be backfilled into this format as needed.
