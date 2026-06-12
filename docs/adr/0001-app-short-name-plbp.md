# 0001. App short name `plbp` (hard rename from `pylb`)

- **Status:** Superseded by [ADR 0016](0016-app-short-name-placeholder.md)
  (the name choice; the hard-rename/no-alias policy below still stands)
- **Date:** 2026-06-09
- **Deciders:** maintainer (interactive), implemented in PR #378
- **Related:** [design 0001](../design/0001-plbp-cli-conventions.md) §0–§1; ADR 0002

## Context

The modern noun-verb CLI shipped as `pylb` with a `PY_TOKEN` env var, while
the conventions spec (design 0001) standardized on the short name **`plbp`**
with a **`PLBP_*`** env prefix. The name is load-bearing: it is the console
command, the uppercased env-var prefix, the XDG namespace
(`~/.config/<app>/`), and the file-name prefix (`<app>_config.toml`,
`<app>.log`). Two names cannot coexist without confusing every doc and fork.

## Decision

Rename to `plbp`/`PLBP_*` everywhere, as a **hard rename** — no `pylb`
back-compat alias. (At the time of this decision the legacy single-command
entry point `py-projects` was retained under its own name and `PY_TOKEN`; it
was **removed in a later cleanup**, leaving `plbp` as the sole console script.)

## Consequences

- Breaking change for anyone invoking `pylb` (released as v2.0.0).
- One spelling across spec, code, docs, and the init rebrand system.
- The app name became a tracked init identity so forks rename it wholesale
  (see the `app_name` / `app_name_upper` fields in `init/manifest.toml`).

## Alternatives considered

- **Keep `pylb`, adapt the spec** — rejected: the spec's name was chosen
  deliberately; adapting docs to an accidental name inverts the authority.
- **Ship both (`pylb` deprecated alias)** — rejected: a template should not
  teach forks to carry alias debt from day one.
