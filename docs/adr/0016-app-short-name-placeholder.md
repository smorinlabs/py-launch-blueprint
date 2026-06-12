# 0016. App short name becomes an obvious placeholder: `plbp` → `acmeapp`

- **Status:** Accepted (implementation pending — the mechanical rename has not
  been applied yet; until it lands, `plbp`/`PLBP` remain the live identity)
- **Date:** 2026-06-12
- **Deciders:** maintainer (interactive)
- **Supersedes:** [ADR 0001](0001-app-short-name-plbp.md) — the *choice of
  name* only; the hard-rename / no-back-compat-alias policy ADR 0001 set
  still stands
- **Related:** [design 0001](../design/0001-plbp-cli-conventions.md) §0–§1;
  `init/manifest.toml` (`app_name` / `app_name_upper` fields)

## Context

This repository is permanently a template. It publishes to PyPI solely to
prove the release machinery works, so nothing about the app short name needs
to be brand-like or claimable. Yet the short name is the template's most
user-visible surface: it is the console command, the `PLBP_*` env-var prefix,
the XDG namespace (`~/.config/<app>/`), and the file-name prefix
(`<app>_config.toml`, `<app>.log`).

`plbp` (ADR 0001) was invented for substring-disjointness — text-mode
replacement is provably safe because the token cannot occur incidentally. But
it *reads* like real product branding, which misleads every audience the
template serves:

- **Repo browsers** can't tell template brand from rename-me placeholder.
- **Doc readers** can't tell whether `plbp config set token` refers to a real
  tool or to their future command.
- **Forks that skip or half-run `just init`** ship what looks like someone
  else's product name in env vars and config paths.
- **AI agents** working in forks pattern-match `PLBP_*` as intentional
  project vocabulary and propagate it into new code, instead of flagging it
  as a placeholder to replace.

## Decision

Replace `plbp` / `PLBP` with **`acmeapp` / `ACMEAPP`** everywhere the
`app_name` / `app_name_upper` identities apply: the console-script name, the
`ACMEAPP_*` env prefix, the `_ACMEAPP_COMPLETE` completion var, the XDG
namespace, and file-name prefixes.

`acmeapp` was chosen because it satisfies both properties at once:

1. **Obviously a placeholder.** ACME is the canonical fake company; no
   reader or AI agent parses `acmeapp` as real branding.
2. **Still effectively substring-disjoint.** Unlike `myapp` (the most common
   placeholder on the internet), `acmeapp` is rare in real-world snippets and
   vendored content, so the naive text-mode replacement that the init engine
   performs stays safe in practice. Residual risk is gated by the per-file
   occurrence lists in `init/manifest.toml` plus the manifest drift check,
   which force every new occurrence through review.

Scope is the short token **only**. `package_name` / `repo_name` / `owner` /
`author` stay real: the live PyPI publishing proof depends on a claimable
distribution name, and keeping real identities in the manifest means the
template's CI keeps proving the rename machinery against a genuine brand,
not just a fill-in-the-blank.

This ADR records the decision; the repo-wide rename (≈330 occurrences,
manifest `current` values, `init/common.py` ground truth, doc-file renames,
regenerated OpenAPI snapshot) lands as a separate change.

## Consequences

- **Breaking change** when implemented: the console command, env prefix,
  config/log file names, and XDG paths all change spelling. Per ADR 0001's
  still-standing policy, this is a hard rename with no `plbp` alias.
- The placeholder reads as rename-me to humans and AI agents, so a
  half-initialized fork leaks an obvious TODO instead of another project's
  brand.
- The invented-token guarantee weakens from *proven* (a string that exists
  nowhere else) to *reviewed* (a rare string whose occurrences the drift
  check forces into the manifest). This trade-off is accepted; the drift
  check is the load-bearing control either way.
- `init/tests/` fixtures keep using `myapp` as the *fork-target* example
  name with no collision against the template's own identity.
- Until the rename lands, this file mentions the live `plbp` / `PLBP`
  identity and is therefore tracked under `app_name` / `app_name_upper` in
  `init/manifest.toml`.

## Alternatives considered

- **Keep `plbp`, add disclaimers** (README/AGENTS notes that it's a
  placeholder) — rejected: mitigates but doesn't fix the first-impression
  problem or agent propagation; relies on readers finding the disclaimer.
- **`myapp` / `MYAPP`** — rejected: maximum recognizability, but it is the
  most common placeholder in external docs (false-positive rewrites in
  vendored content become likely, drift review gets noisy) and it collides
  with the fork-target name the init tests already use.
- **`myacmeapp` / `MYACMEAPP`** — rejected: the `my` prefix adds a redundant
  second cue at the cost of two extra characters in every env var and
  88-column doc line, and the triple compound reads poorly.
- **Full identity swap** (placeholder package/repo/owner too) — rejected:
  breaks the live publishing proof and removes the real-brand rename that
  keeps the init machinery honest.
