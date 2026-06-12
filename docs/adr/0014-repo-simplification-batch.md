# 0014. Repo simplification batch — canonical agent config, skill placement, docs & CI layout (SIMP series)

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer (interactive), implemented across PRs #401, #402,
  #405, #407, #409–#413
- **Related:** `projects/P02-repo-simplification.md` (the tracked initiative
  with per-item verification analysis); ADR 0005 (toolchain provisioning);
  the init-system contract (`init/manifest.toml` + `init/ci/*` guards)

## Context

The repo accreted overlapping configuration surfaces: five files of agent
guidance, duplicated community files, a bootstrap skill no tool could
discover, half-organized tests, root-level markdown of mixed audiences, and
five CI workflows that were 80% identical boilerplate. A ranked
simplification catalogue (SIMP-01..12) was verified item-by-item against the
init/rebrand machinery before acting; this ADR records the decisions the
batch settled. Execution model: one verified, single-purpose PR per item.

## Decisions

### 1. AGENTS.md is the single canonical agent config (SIMP-06)

Shared agent guidance lives in **`AGENTS.md`** only. `CLAUDE.md` is a thin
entrypoint that imports it (`@AGENTS.md`) plus Claude-specific notes.
Vendor rule files (`.windsurfrules`, `.cursor/rules/`, `.windsurf/rules/`)
are **deleted** — Cursor, Windsurf, and Codex read AGENTS.md natively.

Why this direction and not the inverse: Claude Code's `@`-import is the
only *mechanical* cross-file link available; AGENTS.md is plain markdown
with no import syntax, so content placed only in CLAUDE.md would reach
other agents via a prose pointer at best. Durable content from the deleted
files (Justfile editing conventions) moved to
`docs/source/tools/justfiles.md`.

### 2. The bootstrap skill lives in real discovery paths and never requires `just` (SIMP-11)

`skill/` at the repo root was no tool's discovery path — the skill was
documentation wearing a skill's clothes. Canonical location is now
**`.claude/skills/new-python-project/`** (Claude Code project-skill
discovery; invocable as `/new-python-project`), with an
**`.agents/skills/new-python-project` symlink** for Codex (its documented
repo scan path). On Windows checkouts without git symlink support the
symlink degrades to a text file — accepted; only Codex auto-discovery is
lost.

The runbook is **universal**: it requires only `gh` + `uv`, invoking
`init/init.py` / `init/post_init.py` directly (`just` recipes are thin
wrappers). It *recommends* the toolchain path — `make check`,
`make install-just` (prints, never runs), `make bootstrap` — but never
executes machine-modifying installs on the user's behalf.

### 3. Bootstrap dirs are for blueprint-only tooling; fork-facing files must not live there (SIMP-07 corollary)

`init/` (and the skill dir) are pruned by `init --prune` and exempt from
identity scans. Therefore anything a fork must keep — like `POST_INIT.md`,
the fork-facing post-init checklist — must NOT live there. This corrected
the original analysis, which had slated `POST_INIT.md` for `init/`.

### 4. Root markdown placement policy (SIMP-07, SIMP-10)

- **Operational guides** → `docs/` (unpublished, alongside the engineering
  docs): `POST_INIT.md`, `RELEASE.md`.
- **Analysis / research artifacts** → `docs/research/` with `NNNN-` naming
  and an index entry (skill trigger-optimization writeup, init/post-init
  systems analysis). Files there carrying blueprint identity get manifest
  coverage rather than exemption.
- **Product-front docs stay at root**: `EXAMPLECLI.md` keeps its prominent
  README placement (deliberate; ~49 manifest occurrences made the move
  high-churn for no gain).
- **Community files GitHub surfaces natively live in `.github/` as the
  single source**; the Sphinx copy includes them via MyST `{include}`
  (`CODE_OF_CONDUCT.md` — the duplicate was byte-identical).

### 5. Test layout mirrors what is being tested (SIMP-08)

`tests/{cli,core,web}` test the shipped package; **`tests/meta/`** tests
the repo's own machinery (contributor automation, Justfile recipes,
version consistency). No flat test files at the root besides
`conftest.py`/`__init__.py`. Root-finding in meta tests uses
`parents[2]`.

### 6. One lint workflow, jobs keep their check names, path-aware where filters existed (SIMP-09)

The five single-purpose lint workflows (actionlint, bandit, codespell,
editorconfig-check, yamllint) are jobs of one **`lint.yml`**. Job names
match the old check contexts exactly, so branch-protection required checks
survive unchanged. actionlint and yamllint keep their historical path
filters via a `lint-changes` detection job (per-job `if:`), because
workflow-level `paths:` cannot be applied per job. A skipped job
*satisfies* a required status check — strictly better than the old
filtered-out workflows, which never reported their context at all.

## Consequences

- One file to edit for agent behavior; generated projects update AGENTS.md
  and nothing else.
- The bootstrap skill is actually invocable (verified live in a Claude Code
  session) and usable by gh+uv-only environments.
- Forks no longer inherit blueprint-only artifacts (skill pruned, as
  before, now at the new path) but always keep their operational guides.
- Adding a linter is a six-line job in `lint.yml`, not a new workflow file;
  docs-only PRs skip actionlint/yamllint without risking a hung required
  check.
- Dropped/deferred for the record: SIMP-05 (Makefile replacement —
  superseded by the two-level setup, ADR'd in the P02 file), SIMP-12
  (commitlint config merge — the split is load-bearing), SIMP-04 (Justfile
  module split — breaks four init couplings; in-place reorg only, optional).
