# Design: Retire the embedded `init/` rebrand engine in favor of template-press

**Date:** 2026-07-16
**Status:** Approved (design) — pending implementation plan
**Related:** Issue #423 (extract init/post-init engine into `smorinlabs/template-press`)

## 1. Goal & end-state

`py-launch-blueprint` currently carries a **standalone, embedded rebrand
engine** under `init/` (~2,800 lines of Python plus shell scripts, a manifest,
CI guards, and a test suite). That engine has been extracted and productized
into the separate **`template-press`** repository
(`src/template_press/rebrand/`).

**End-state:** `py-launch-blueprint` becomes a **pure template**. It carries the
template content plus the config data a presser reads; **template-press**
(installed separately) owns all rebrand machinery. The embedded `init/` rebrand
engine is removed — but only after we have *proven* template-press can press
this repo (see the safety gate in §4).

This is deliberately **not** a "keep a thin self-contained `just init`" model.
Going forward the repo is pressed externally:

```
template-press  --(press rebrand --target py-launch-blueprint --config answers.toml)-->  a new project
```

## 2. Current state (inventory)

### This repo's `init/`
- **Rebrand engine:** `init.py` (439), `_engine.py` (304), `_rewriters.py`
  (29), `discover.py` (273), `common.py` (321), `manifest.toml`.
- **Doctor:** `init_doctor.py` (597) — **mixed**: MIGRATION checks (rebrand)
  + ENVIRONMENT/post_init checks (provision).
- **Provisioning:** `post_init.py` (814), `setup-github-environments.sh`,
  `setup-pypi-publishing.sh`.
- **Guard / marker system:** `guard.sh`, `ci/check_guard_wiring.py`,
  `ci/check_manifest_drift.py`, `ci/check_no_marker.sh`,
  `ci/check_path_filter.py`.
- **Docs:** `init-spec.md`, `README.md`.
- **Tests:** `init/tests/` (11 files + `conftest.py` +
  `integration/answers.toml`).

### Consumers of `init/` (must be repointed or removed)
- **Justfile:** `_blueprint_notice := shell('bash init/guard.sh warn')`,
  `init` → `uv run init/init.py`, `init-doctor` → `uv run init/init_doctor.py`,
  `post-init` → `uv run init/post_init.py`, and the `guard.sh block` gate.
- **CI:** `.github/workflows/blueprint-guard.yml` (marker + guard-wiring +
  manifest-drift + path-filter checks), `.github/workflows/init-integration.yml`.
- **Skill:** `.claude/skills/new-python-project/SKILL.md` (invokes `just init`).

### template-press (`~/c/template-press`, `smorinlabs/template-press`)
- Productized package `src/template_press/rebrand/`: `engine.py`,
  `discovery.py`, `rules.py`, `identity.py`, `doctor.py`, `cli.py`,
  `receipt.py`, `config.py`. Its `identity.py` header cites
  `init/common.py:102-130` as its origin — confirming direct lineage.
- **Two-file identity model:** the *target* repo commits `.press/source.toml`
  (the FROM identity); template-press is invoked with `--config answers.toml`
  (the TO identity).
- **`provision` and `status` are "coming in M6"** — i.e. **provisioning is not
  yet migrated**.

## 3. Scope split — the core decision

Two halves, handled on different timelines:

| Bucket | Files (preliminary — Phase 0a finalizes the exact split) | Fate |
|---|---|---|
| **Rebrand engine** | `init.py`, `_engine.py`, `_rewriters.py`, `discover.py`, `common.py` (rebrand parts), `manifest.toml`, `init_doctor.py` MIGRATION checks, rebrand `tests/`, the guard/marker system (`guard.sh`, `ci/check_guard_wiring.py`, `ci/check_manifest_drift.py`, `ci/check_no_marker.sh`, `ci/check_path_filter.py`), `blueprint-guard.yml`, `init-integration.yml` | **Remove in Phase 1**, after the parity gate |
| **Provisioning** | `post_init.py`, `setup-github-environments.sh`, `setup-pypi-publishing.sh`, `init_doctor.py` ENVIRONMENT/post_init checks | **Keep** until template-press ships M6 `provision`; remove in a later **Phase 2** |
| **Config / data (stays, reshaped)** | Adopt template-press's `.press/source.toml` (this repo's own identity), **replacing** `init/manifest.toml` | **Migrate & keep** |
| **Legacy design (historical)** | `docs/design/*template-press*`, `docs/research/0003-init-post-init-analysis.md`, and `init/init-spec.md` as a historical record | **Keep** |

**Confirmed decisions from brainstorming:**
- The guard/marker system is **removed** (it exists to protect the embedded
  engine; a pure external-press template does not need it).
- "Keep answers.toml / the configs" means **adopt `.press/source.toml`**
  (template-press's format), replacing `manifest.toml` — not keeping
  `manifest.toml` as-is.

**The genuinely mixed files** — `common.py` and `init_doctor.py` — carry both
rebrand and provision concerns. Their exact line-level split is **determined by
Phase 0a's holistic map**, not assumed here. `init_doctor.py`'s ENVIRONMENT and
post_init checks may survive (repointed) even as its MIGRATION checks go.

## 4. Phases

### Phase 0 — Verify (the gate; nothing is deleted)
The removal is **blocked** until this gate passes.

- **0a. Holistic map** — one recon agent produces, for every `init/` file, its
  template-press equivalent (module/function) and a category tag:
  `rebrand-redundant` / `provision-keep` / `config-keep` / `legacy-keep`.
  Output: a structured map + a per-file rationale.
- **0b. Parallel per-file verification** — one sub-agent per
  `rebrand-redundant` file, run in **isolated scratch worktrees**, each
  answering: *does template-press fully cover this file's behavior, including
  edge cases?* Each returns a structured verdict
  `{file, covered: bool, tp_equivalent, gaps: [...], evidence}`.
- **0c. Behavioral parity** — run template-press against a fresh
  `py-launch-blueprint` clone (`press rebrand --target … --config …`) and diff
  the pressed result against the current `just init` output on the same inputs.

**Gate = (0b: every rebrand-redundant file `covered`) AND (0c: diff is empty or
every difference is explained and accepted).** Any gap becomes a
prerequisite task in template-press before removal proceeds.

### Phase 1 — Remove the rebrand engine (only if the gate passes)
1. Adopt `.press/source.toml` (derive from `manifest.toml`'s identity block);
   remove `manifest.toml`.
2. Delete the rebrand engine files and the guard/marker system.
3. Repoint/remove Justfile recipes (`init`, the `guard.sh` notice + block,
   `init-doctor` MIGRATION parts) and delete `blueprint-guard.yml` +
   `init-integration.yml`.
4. Update the `new-python-project` skill to invoke template-press instead of
   `just init`.
5. Keep `post_init.py` + `setup-*.sh` + `init_doctor.py` ENVIRONMENT/post_init
   checks wired and working.

### Phase 2 — Remove provisioning (future, separate effort)
After template-press ships M6 `provision`, repeat the Phase-0 gate for
`post_init.py` + `setup-*.sh` + the remaining doctor checks, then remove them.

## 5. Sub-agent methodology

Per the Agent/Model matrix:
- **0a holistic map** → `sonnet` (recon/mapping).
- **0b per-file verifiers** → `sonnet`, fanned out in parallel, each in its own
  scratch worktree, returning the structured verdict schema above.
- **0c behavioral parity** → `opus` (a live-state dry-run / mutating recipe).
- **Synthesis** (aggregate verdicts → removal manifest + gate verdict) →
  `fable`.

This maps cleanly onto a **Workflow** pipeline
(`map → parallel-verify → parity → synthesize`) if deterministic orchestration
is wanted; the parallel per-file verify stage is the fan-out.

Agents are **read-only** in Phase 0 (comparison + verification only). They
create their own worktrees in scratch dirs; they never mutate the user's live
checkout and never switch branches in it.

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| template-press can't yet fully press this repo → removing `init/` breaks the template | The Phase-0 gate (0b + 0c) blocks removal until parity is proven. |
| A "mixed" file (`common.py`, `init_doctor.py`) is over-removed, taking provisioning with it | Phase 0a maps at line/function granularity; provisioning stays until Phase 2. |
| `.press/source.toml` diverges from what template-press expects | 0c presses with the real `.press/source.toml`; a mismatch shows up as a diff and blocks the gate. |
| Removing CI (`blueprint-guard`, `init-integration`) drops a guard some other flow relies on | 0a confirms these are engine-only before they're bucketed for removal. |
| GitHub branch-protection lists these CI jobs as required contexts | Phase 1 must also remove the corresponding required-status-check entries from branch protection, or new PRs block forever. |

## 7. Deliverable

This brainstorm produces this **design spec**. The Phase-0 comparison and
verification run during the implementation phase (writing-plans →
executing-plans). Phase 1 removal is a follow-on once the gate is green.

## 8. Open items (tracked, not blocking this design)

- Capture this as a `PROJECTS.md` project (P03/next available) via
  `project-add` — it is the `py-launch-blueprint` side of the #423 migration.
- Confirm which required-status-check contexts must be dropped from branch
  protection in Phase 1 (`guard`, `integration-ok`, and any others the
  removed workflows post).
