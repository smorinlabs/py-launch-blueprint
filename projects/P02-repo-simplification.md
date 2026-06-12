# P02 — Repo simplification & organization (SIMP series)

- **Status:** `[x]` complete (2026-06-12) — SIMP-01/02/03 merged (#401/#402/#405); SIMP-10 in #407; SIMP-11/06/08/07/09 merged (#409–#413); SIMP-05/12 dropped; SIMP-04 deferred as optional (in-place Justfile reorg only, if ever). Decisions recorded in ADR 0014; lint path-detection validated live in #415/#416.
- **Captured:** 2026-06-12
- **Scope:** repo-wide structure & tooling — `Justfile`, `Makefile`, `docs/`,
  `tests/`, `.github/workflows/`, agent-config files, root markdown

## Original requirement

Two requests framed this project. The first asked for a ranked catalogue of
simplification ideas:

> I like to get ideas on ways to simplify, better organize, consolidate this
> project. Stuff on the files, directory structure, things like that. So
> looking for ideas, rank each one, making clear what the benefit would be,
> what it would be, give it an ID, give it the type of improvement it would be,
> how much value it would have, and how recommended it would be. […] This is in
> the idea of streamlining many things more obvious, things like that.

The second asked for each idea to be verified against the codebase before
acting:

> Can you analyze each one of these and verify it to see what a recommended
> change for each one is? And if any of those changes might break something
> else or have […] side consequences that are unforeseen.

Each item therefore carries: an **ID**, a **type** of improvement, a **value**
rating, a **recommendation**, and — from the verification pass — a **verdict**
plus the concrete **side-effects / coupling** discovered.

## Context & approach

The repo is a production-ready Python project *template*: a fork runs
`just init` to rebrand identity literals across ~50 files, so the init system
(`init/manifest.toml` + `init/ci/*` guards + `init-integration` CI) couples
many files that look independent. Verification consisted of tracing each idea
through that init machinery, the lefthook hooks, CI workflows, and
cross-references before assigning a verdict.

Execution model: **one single-purpose PR per item**, each verified end-to-end
locally (`just check`, init suite, manifest drift, hooks un-bypassed) before a
draft PR, then merged independently. This keeps every change separately
reviewable and revertible.

## Execution order

| Order | ID | Item | Type | Value | Verdict |
|-------|------|------|------|-------|---------|
| done | SIMP-01 | Purge dead/legacy Justfile recipes | Dead-code removal | High | ✅ merged #401 |
| done | SIMP-02 | Fix the broken docs toolchain | Drift fix / consolidation | High | ✅ merged #402 |
| done | SIMP-03 | Two-level setup (`make bootstrap` + `just setup`) | Consolidation / DX | High | ✅ merged #405 |
| done | SIMP-10 | Single-source CODE_OF_CONDUCT | DRY | Low-Med | ✅ in #407 |
| done | SIMP-11 | Relocate skill to `.claude/skills/` + Codex symlink; research moved | Organization | Low-Med | 🔄 PR #409 |
| done | SIMP-06 | AGENTS.md canonical; CLAUDE.md `@`-imports it; vendor rules deleted | DRY / consolidation | Med | 🔄 PR #410 (stacked on #409) |
| done | SIMP-08 | Group flat test files (`tests/meta/`, `tests/cli/`) | Organization | Med | 🔄 PR #411 |
| done | SIMP-07 | `POST_INIT.md` + `RELEASE.md` → `docs/`; analysis → research on #408 | Organization | Med | 🔄 PR #412 (stacked on #410) |
| done | SIMP-09 | Five lint workflows → one `lint.yml` with path-aware jobs | Consolidation | Med | 🔄 PR #413 (stacked on #406) |
| 7 (opt) | SIMP-04 | Reorganize the Justfile (in place) | Organization | Med | Defer/optional |
| — | SIMP-05 | Replace the root Makefile | Simplification | — | **Dropped — superseded by SIMP-03** |
| — | SIMP-12 | Merge the two commitlint configs | DRY | — | **Dropped — split is load-bearing** |

The logic: items 1–3 touch disjoint files (any order; no rebases), 4–5 are the
manifest-touching moves in increasing size, 6 waits on a repo-settings check
only the maintainer can do quickly, and 7 is optional polish.

**Corrections discovered during execution** (amending the analysis above):

- SIMP-11's "manifest `[[remove]]` question" was moot — `init/init.py` already
  prunes `skill/` on `just init` (forks never shipped it). The skill moved to
  `.claude/skills/new-python-project/` (real Claude Code discovery) with an
  `.agents/skills/` symlink for Codex, and was de-just'd (#409).
- SIMP-07's `POST_INIT.md → init/` destination was wrong: `init/` is prunable,
  scan-excluded bootstrap tooling, while POST_INIT.md is fork-facing and must
  survive prune. It went to `docs/` instead (#412); `EXAMPLECLI.md` stays at
  root per maintainer decision.
- SIMP-08: all five meta tests (not just `test_justfile.py`) resolved the repo
  root via `parents[1]`/`parent.parent` — all bumped to `parents[2]` (#411).
- SIMP-09: per maintainer direction, actionlint/yamllint keep their path-
  filtered behavior via a `lint-changes` detection job (validated against six
  diff scenarios); skipped jobs satisfy required checks, which the old
  filtered-out workflows did not (#413, stacked on #406).

## Completed work

### SIMP-01 — Purge dead/legacy Justfile recipes (merged #401)

Removed the legacy pip recipe set (`setup-venv`, `install-dev-pip`,
`format-pip`, `lint-pip`, `typecheck-pip`, `test-pip`), the `_foo` demo recipe,
and `install-go`. Rewrote `install-yamlfmt` to download the upstream pre-built
binary (taplo-style) so Go is no longer an onboarding requirement just to
format YAML. **Verification correction:** the original pass wrongly called
`install-go` dead — `check-deps` hard-failed without Go because
`install-yamlfmt` depended on it. Also fixed `check-deps` pointing at
nonexistent `make install-go` / `make install-yamlfmt` targets. Docs updated
(`cli_reference.md`, `justfiles.md`, `yaml_lint.md`).

### SIMP-02 — Fix the broken docs toolchain (merged #402)

`docs/Makefile`, `just init-docs`, and `just install-docs` were **broken on
main** — they used `uv run --extra docs`, which fails since docs deps moved to
a PEP 735 dependency group (ITM-063). Rewrote the docs recipes to call Sphinx
directly via `uv run --group docs` (the path Read the Docs already uses),
deleted `docs/Makefile` and `install-docs`. `install-docs` was independently
broken (installed `sphinx-rtd-theme` while `conf.py` uses furo, off-lockfile).

### SIMP-03 — Two-level setup (merged #405)

Per maintainer refinement, made setup explicitly two-level:
**Level 1** `make bootstrap` (base toolchain: just + uv), **Level 2**
`just setup` (dev env sync, git hooks, hook toolchain). `just setup` gates on
`make check` and fails with a pointer to `make bootstrap` if the base toolchain
is missing. Devcontainer `postCreateCommand` now runs both levels via
`.devcontainer/post-create.sh`. Fixed three live bugs: `SHELL := /bin/zsh` (the
Makefile didn't run on stock Linux), `just install-dev` silently installing
zero dev deps (stale `.[dev]` extra), and a stale `bun.lock` (commitlint
19→21). CLAUDE.md + AGENTS.md document the flow as canonical.

### SIMP-10 — Single-source CODE_OF_CONDUCT (implemented in #407)

`CODE_OF_CONDUCT.md` existed byte-identically in both `.github/` and
`docs/source/contributing/` (`diff` clean). The Sphinx copy now pulls the
`.github/` source (which GitHub surfaces natively) via a MyST `{include}`
wrapper. Verified: docs build succeeds with no new warnings and the rendered
page contains the CoC content; RTD builds from a full checkout so `.github/`
is present; neither file is in the init manifest.

## Planned items

### SIMP-11 — Move `skill/optimization-workspace/` out (Organization · Low-Med)

`RESULTS.md` is an internal prompt-optimization writeup, not template content,
and already forces a codespell skip in `pyproject.toml`. Move it to
`docs/research/` (empty, exists for exactly this) and update `skill/README.md`
+ the codespell skip list. **Decision surfaced:** the manifest has no
`[[remove]]` for `skill/` at all, so every fork ships the blueprint's own
bootstrap skill. Whether to add a `skill/` removal is a judgment call (forks
may want the skill) — to be raised in the PR, not decided incidentally.

### SIMP-06 — Canonical AGENTS.md; thin vendor rules (DRY · Med)

Five files carry overlapping guidance: `AGENTS.md`, `CLAUDE.md`,
`.windsurfrules`, `.cursor/rules/projectenv.mdc`, `.windsurf/rules/`. Keep
AGENTS.md canonical and detailed; reduce vendor files to pointers plus only
genuinely vendor-specific content (CLAUDE.md keeps its project-harness
section). Cursor and Windsurf both follow AGENTS.md now, so `.windsurfrules`
and `.windsurf/` may be deletable. **Coupling:** `.windsurfrules` is in two
manifest `[[replace]]` blocks (`app_name`, `package_name`); deleting it needs
matching manifest edits — but `check_manifest_drift.py` runs on every PR and
pre-push, so a miss fails loudly rather than shipping a broken fork.
`.cursor/rules/projectenv.mdc` references `.windsurfrules` by name — update in
the same change.

### SIMP-08 — Group flat test files (Organization · Med)

`tests/` is half-organized (`cli/`, `core/`, `web/` subdirs + 6 flat files).
Group the repo/tooling meta-tests (`test_contributors_*`, `test_justfile`,
`test_version_consistency`) under `tests/meta/`; move `test_output.py` to
`tests/cli/`. **Coupling:** manifest has `[[remove]]` entries for the
contributor/justfile tests and `[[replace]]` for output/version tests — paths
must update on move (CI-enforced). `test_justfile.py` resolves root via
`parents[1]` → becomes `parents[2]` one level deeper. New `tests/meta/`
needs `__init__.py` (package-style suite). Codecov `paths: tests/` and pytest
`testpaths` still match.

### SIMP-07 — Relocate root markdown (Organization · Med)

Move `POST_INIT.md` → `init/` (it documents the init system) and `RELEASE.md`
→ `docs/`. **New fact (re-eval):** a prominent README link to `EXAMPLECLI.md`
was added recently, suggesting its root placement may be deliberate — so the
PR should ask whether to scope EXAMPLECLI.md out and keep it at root. Largest
reference churn: manifest blocks, README, the `errors.py` docstring, and an
absolute GitHub-blob link in `docs/source/index.md`. The strict-mode
`init-integration` workflow + drift check make a missed manifest path fail CI,
so misses can't silently merge.

### SIMP-09 — Consolidate single-purpose lint workflows (Consolidation · Med)

actionlint, codespell, editorconfig-check, yamllint, and bandit are each a
checkout + one tool; they could be jobs in one `lint.yml` (separate jobs keep
independent status checks). **External unknown — only the maintainer can
confirm:** branch-protection / ruleset *required status checks* reference check
names; keep job names identical and confirm in repo settings before deleting
old workflow files, or a PR could wait forever on a check that never reports.
Don't fold in `blueprint-guard.yml` / `update-contributors.yml` (manifest
`[[remove]]` names them). `bandit.yml` is in the manifest `package_name` block
— path update needed.

## Dropped / deferred

### SIMP-05 — Replace the root Makefile — **DROPPED (superseded by SIMP-03)**

The original idea was to replace the Makefile with a bootstrap script. SIMP-03
instead made the Makefile the *permanent* Level-1 bootstrap: `make bootstrap`
is now load-bearing in the devcontainer, README quick start, CLAUDE.md, and
AGENTS.md, and PR #403 added `install-flox` to it. Replacing it would undo
just-merged architecture. The original SIMP-05 bug (zsh shebang, `~/bin` PATH
handling) was folded into SIMP-03.

### SIMP-12 — Merge the two commitlint configs — **DROPPED (split is load-bearing)**

`commitlint.config.mjs` and `commitlint.dependabot.config.mjs` differ only in
two line-length rules, but the split is structural: `commitlint.yml` selects
the config per PR author (`user.login == 'dependabot[bot]'`) via the action's
`configFile` input. Merging would mean plumbing an env var through a Docker
action into the Node config — more fragile and less explicit than two
well-commented files. The current design is correct.

### SIMP-04 — Reorganize the Justfile — **DEFERRED (in-place only, optional)**

Originally "split into imported modules"; **downgraded** during verification
because a real `import` split breaks four init couplings: blueprint-guard
Check 3 copies only `Justfile` + `init/` to a temp dir; `init/tests/conftest.py`
builds fixtures from a curated list including `Justfile`; `init/init.py` prunes
recipes from the root Justfile and `init_doctor.py` parses identity vars from
it; and `check_guard_wiring.py` scans only the root file (a moved guarded
recipe would *silently pass*). After SIMP-01 the file is ~780 lines and the
pain is mostly gone. Do only as an in-place reorg if it still bothers the
maintainer; the one worthwhile piece is extracting the ~200-line
`pr-to-testrepo` bash body into `scripts/` with a thin wrapper (keeps its name,
`: _guard` dep, and root location, so all four checks keep working).

## References

- Initiative originated from the simplification-ideas request (2026-06-12) and
  a follow-up verification pass tracing each idea through `init/manifest.toml`,
  `init/ci/{check_manifest_drift,check_guard_wiring,check_path_filter}.py`,
  `lefthook.yml`, and `.github/workflows/`.
- Merged PRs: #401 (SIMP-01), #402 (SIMP-02), #405 (SIMP-03).
- Init-system contract that couples otherwise-independent files:
  `init/manifest.toml` `[[replace]]`/`[[remove]]`/`[[rename]]` blocks, enforced
  by `blueprint-guard` + `init-integration` CI (strict mode, every PR).
