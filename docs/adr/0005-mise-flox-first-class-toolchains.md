# 0005. mise and flox are first-class toolchain provisioners (lean 10-tool set)

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer
- **Related:** historical ADR-04 (commitlint via bun); the shim note in
  `lefthook.yml`; the CI provisioning benchmark preserved on branch
  `experiment/flox-ci-timing-perf-analysis` (removed from main in PR #386)

## Context

The dev toolchain was provisioned only via native per-tool installs (Makefile
bootstrap + Justfile `install-*` recipes). A CI benchmark experiment built
[mise](https://mise.jdx.dev/) and [flox](https://flox.dev/) manifests to compare
provisioners; those manifests declared a 15-tool set so every linter could run
as a bare binary under `mise exec` / `flox activate` — the experiment's premise,
not the repo's real workflow.

Auditing that set against actual usage surfaced two problems:

1. **Duplicate version sources.** yamllint, codespell, bandit, and
   editorconfig-checker are invoked via `uvx`, and commitlint via
   `bunx --bun @commitlint/cli` (historical ADR-04) — uv/bun fetch them on
   demand. Declaring them in a provisioner manifest creates a second,
   independently-drifting source of versions that the hooks never use.
2. **An active defect.** The mise `commitlint` shim shadowed bun's PATH
   fallback: on a cold bun cache, `bunx --bun commitlint` resolved to the shim
   and failed with "No version is set for shim: commitlint". The commit-msg
   hook had to pin the scoped package name as a workaround (documented in
   `lefthook.yml`).

## Decision

We will support **three first-class, equivalent toolchain provisioners** and
keep them in sync:

1. **Native installs** — Makefile bootstrap (`make check`, `install-*`) +
   Justfile `install-*` recipes (unchanged).
2. **mise** — root `mise.toml`; provision with `mise install`.
3. **flox** — root `.flox/`; provision with `flox activate`.

Both manifests declare the **same lean 10-tool set**: python 3.12, uv, ruff,
taplo, gitleaks, just, bun, gh, lefthook, make. Adding or removing a tool means
updating all three options.

Deliberately excluded from the manifests:

- **uvx-invoked linters** (yamllint, codespell, bandit, editorconfig-checker)
  and **bunx-invoked commitlint** — uv/bun remain their single version source.
  Dropping commitlint also removes the mise shim conflict at its root.
- **ty and pytest** — project dev dependencies, provided by `uv run`.

Supporting choices:

- The manifests live at the **repo root** so both tools auto-discover them —
  that is what "first-class" means here. (The experiment intentionally hid its
  config under `experiment/` to avoid auto-loading.)
- The Makefile gains an **optional, print-only `install-flox` target**
  (matching the `install-just`/`install-uv` pattern): flox installation is
  platform-specific and may need sudo, so we document rather than execute.
  mise bootstrap is covered by its upstream one-liner, linked from the docs.
- The flox `manifest.lock` is **not committed yet**; flox generates it on first
  `flox activate`. Committing it (for fully pinned envs) is left as follow-up.

## Consequences

- Contributors can provision the whole toolchain with one command (`mise
  install` or `flox activate`) instead of N installers; the native path keeps
  working for everyone else.
- Three places now declare the toolchain. The sync rule is recorded in
  CLAUDE.md and in a header comment in each manifest; there is no automated
  drift check between them (possible follow-up).
- The commit-msg hook's pinned `@commitlint/cli` invocation stays — it is
  correct regardless of provisioner — but the failure mode it guarded against
  can no longer occur from our own manifests.
- Anyone with mise installed globally will auto-load `mise.toml` when entering
  the repo; this is now intended behavior.

## Alternatives considered

- **Keep the experiment's 15-tool manifests** — duplicates uv/bun-managed
  versions and re-introduces the commitlint shim defect; the extra five tools
  are never taken from PATH by hooks or CI.
- **Bless a single provisioner (mise-only or flox-only)** — the benchmark
  showed no decisive winner, and forcing one tool on contributors contradicts
  the template's "meet developers where they are" goal.
- **Devcontainer as the only turnkey env** — already exists, but requires
  Docker and an editor that supports it; mise/flox work in any shell.
- **Executing the flox installer from `make install-flox`** — rejected:
  platform-specific packages plus sudo make a curl-pipe-style force target
  riskier than the print-only convention used for just/uv.
