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
| [0001](0001-app-short-name-plbp.md) | App short name `plbp` (hard rename from `pylb`) | Superseded by 0016 |
| [0002](0002-no-secrets-in-config-file.md) | Secrets are never stored in the config file | Accepted |
| [0003](0003-keep-markdown-output-mode.md) | Keep `markdown` as a third output format (spec deviation) | Accepted |
| [0004](0004-config-errors-degrade-to-warnings.md) | Invalid config values degrade to warnings, never crashes | Accepted |
| [0005](0005-mise-flox-first-class-toolchains.md) | mise and flox are first-class toolchain provisioners (lean 10-tool set) | Accepted |
| [0006](0006-stable-error-codes-hints-crash-log.md) | Stable error codes, hints, and a crash log | Accepted |
| [0007](0007-did-you-mean-stdlib-difflib.md) | Did-you-mean suggestions via stdlib difflib | Accepted |
| [0008](0008-pager-for-long-text-output.md) | Long text output pages through the user's pager | Accepted |
| [0009](0009-config-init-and-first-run-hint.md) | Guided `config init` plus a marker-backed one-time first-run hint | Accepted |
| [0010](0010-rich-row-variant-on-result-models.md) | Terminal niceties via a rich-only row variant on result models | Accepted |
| [0011](0011-windows-native-paths-xdg-overrides.md) | Windows-native default directories; XDG overrides win everywhere | Accepted |
| [0012](0012-doctor-bundle-redact-at-collection.md) | `doctor --bundle` redacts at collection time, excludes log contents | Accepted |
| [0013](0013-web-service-best-practices.md) | Web service: baked-in REST best practices behind the `web` extra | Accepted |
| [0014](0014-repo-simplification-batch.md) | Repo simplification batch — canonical agent config, skill placement, docs & CI layout (SIMP series) | Accepted |
| [0015](0015-one-logging-pipeline-two-profiles.md) | One logging pipeline, two front-end profiles (CLI vs web policy) | Accepted |
| [0016](0016-app-short-name-placeholder.md) | App short name is an obvious placeholder (`acmeapp`), not a brand | Accepted |

## Note on historical decisions

This project references earlier decisions by short id (e.g. `ADR-01` lefthook,
`ADR-06` uv_build, `ADR-07` trusted publishing) throughout the codebase and
commit history. Those were recorded in the maintainer's analysis workspace
before this directory existed. New decisions are recorded **here** going
forward; historical ADRs can be backfilled into this format as needed.
