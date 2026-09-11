# Full Conform — Retire the Embedded Engine (P06)

- **Status:** Draft for review
- **Date:** 2026-08-17
- **Lineage:** the deferred second half of P05 (Run 4 scope-gate decision:
  "full conform after publish proof"). The publish proof exists
  (`smorinlabs/blueprint-press-dryrun`, CI green); the engine gaps that
  blocked automation are closed (template-press #80 `[[remove]]`, #81
  `verify_exempt` — both released in **v3.6.0**).
- **Evidence base:** `docs/research/0004-template-press-dogfood-log.md`
  Runs 1–4; the 2026-07-23 conform handoff (phases 4–7, superseded in
  detail by this spec); issue #423 (engine extraction).
- **Press-under-conform:** released `template-press >= 3.6.0` via `uvx`
  (the Run-3 CI-sourcing decision) — never a git pin in CI.

## 0. Purpose

Make py-launch-blueprint depend on exactly ONE rebrand engine — the
external press — by deleting the embedded `init/` engine and everything
that exists only to police it, cutting CI drift detection over to
`press verify`, and upgrading the press config to the v3.6.0 feature set
the P05/P08 dogfoods earned.

## 1. Inventory — what goes, what stays, what moves

### Deleted (the engine and its police)

| Surface | Contents |
|---|---|
| `init/` | 15 entries: `init.py`, `_engine.py`, `_rewriters.py`, `common.py`, `discover.py`, `init_doctor.py`, `post_init.py`, `guard.sh` (moves — below), `manifest.toml`, `init-spec.md`, `README.md`, setup scripts, `ci/` (5 checker scripts), `tests/` (12 modules) |
| `.github/workflows/blueprint-guard.yml` | 5 legacy drift checks — replaced by `press-verify.yml` |
| `.github/workflows/init-integration.yml` | runs `init/tests/` — obsolete with the engine |
| `lefthook.yml` | the 4 init-integrity pre-push gates (`init-guard-wiring`, `init-manifest-drift`, `init-path-filter`, `init-tests`) — replaced by one `press-verify` pre-push job (see §3) |
| `Justfile` | `init` / `init-doctor` / `post-init` recipes (lines ~344–356) |

### Kept, relocated: the fork guard (design decision D-P06-1)

`init/guard.sh` warns/blocks un-rebranded clones — a FORK-facing function
that outlives the engine (`press verify` is TEMPLATE drift detection, a
different job). **Decision: keep the guard, move it to `scripts/guard.sh`,
drop the legacy-marker skip condition** (its only writer dies with
`init/`), keeping receipt + contributor sentinel + canonical-origin.
`Justfile`'s `_blueprint_notice` (Tier 1) and `_guard` (Tier 2) re-point
to the new path. The contributor sentinel moves to
`.blueprint-contributor` at the repo root (git-ignored, as today).
Rejected alternative: deleting the guard — would silently un-protect
`build`/`publish` in every future un-pressed clone.

### CI cutover

New `.github/workflows/press-verify.yml`: on pull_request + push to main,
`uvx --from 'template-press>=3.6.0' press verify` (zero-argument CI usage;
exit 0/1/2 is the contract). This replaces the drift half of
blueprint-guard; the fork-facing half lives in the relocated guard, which
needs no CI (it runs in forks' shells).

## 2. Press-config upgrade (v3.6.0 features)

Additions to `press/press-rules.toml`:

1. **`scan = "boundary"`** on both `bun.lock` `[[regenerate]]` entries
   (PROBLEM-22's fix, adoptable now that the released press knows the key).
2. **Snapshot regeneration** (PROBLEM-24's intended automation):
   `[[regenerate]]` for `tests/cli/__snapshots__/test_help_snapshots.ambr`
   (the documented `--snapshot-update` command, empirically proven in the
   press executor) + `verify_exempt = true` with a reason (#81's mechanism)
   + the file added to `extra_exclude_files`. `docs/POST_INIT.md`'s manual
   step shrinks to `uv run ruff format .` only (PROBLEM-27 remains manual —
   formatting is tree-wide, not a single declarable output).
3. **`[[remove]]` declarations** (#80's mechanism) porting the manifest's
   fork-facing removals that still exist after this campaign's own
   deletions: the dogfood history docs (P05 spec/plan, the v1–v3
   specs/plan, the dogfood log, the P06 spec/plan once merged, handoffs),
   `docs/design/0005-template-press-tui-design.md`, `prototypes/press_tui/*`,
   and `.github/workflows/update-contributors.yml` (app-secret-gated,
   blueprint-only). `press-verify.yml` deliberately SHIPS to forks — a
   pressed fork is itself a valid press target and inherits the drift
   guard. `projects/P05-…`/`P06-…` files stay (trunk-history convention,
   PR #518 review decision).

## 3. Docs, hooks, and skills

- `AGENTS.md`: init-based verification flow (§"Verification flow" step 3,
  the drift-rule paragraph) → press model (`press verify` locally and in
  CI); "Creating a new project" section re-written around `press rebrand`;
  the init-tools rows dropped.
- `.claude/skills/new-python-project/SKILL.md` (+ `.agents` symlink): the
  runbook's rebrand step becomes `uvx template-press press rebrand …` with
  the dry-run → apply → commit flow and the POST_INIT normalization step.
- `lefthook.yml`: the four init gates → one receipt-aware `press-verify`
  pre-push job (`uvx --from 'template-press>=3.6.0' press verify`), skipped
  in forks the same way (receipt present → this IS the fork's drift guard
  and runs fine; no skip needed at all — decision: run it everywhere).
- `docs/POST_INIT.md`: press section updated (snapshot step now automated).

## 4. Phases

1. **Config first** (this worktree): §2 press-rules upgrade + §1 [[remove]]
   set; `press verify` (v3.6.0) exit 0 locally with the new declarations.
2. **Cutover**: add `press-verify.yml`; delete the two legacy workflows;
   lefthook gates swap; guard relocation + Justfile re-point.
3. **Deletion**: `rm -r init/`; Justfile recipe removal; AGENTS.md + skill
   + POST_INIT rewrites in the same PR (a fork pressed from any merged
   state must never see half-migrated docs).
4. **Gate**: `just check` (no init steps left), `press verify` exit 0,
   fresh-clone rebrand battery (dry-run/apply/re-press) against the
   branch, then PR → merge queue → fresh-main verify + check-tools.
5. **Acceptance re-press**: pressed scratch instance passes `make check`
   + `just setup` + `just check` with ZERO hand-fixes for the classes P05
   hand-fixed (workflows inherited → now removed; snapshots → now
   regenerated; pre-push gates → now receipt-aware/deleted). `ruff format`
   remains the one documented post-press step.
6. **Close-out**: dogfood log Run 5 rows; P06 registered/closed in
   PROJECTS.md; issue #423 closed; worktree cleanup with user.

## 5. Out of scope

- `press provision`/`status` (M6); repo provisioning (dependency-graph
  settings, app secrets) stays in POST_INIT docs.
- template-press#86 (shared hardening) — engine backlog, not blocking.
- The kept instance repo `blueprint-press-dryrun` — untouched evidence.

## 6. Risks

1. **The guard relocation changes fork-facing behavior** (marker condition
   dropped). Mitigated: receipt/contributor/origin conditions preserved;
   legacy-marker forks pre-date the org's own usage and PR #505 kept them
   working — after THIS campaign a legacy fork's marker no longer
   silences (accepted: the legacy engine is gone repo-wide; documented in
   the PR).
2. **Deleting init/tests loses 90-test coverage of the guard.** Mitigated:
   the guard's four skip conditions get a small new `tests/` suite
   (pytest, fixture modes ported from the two receipt tests #505 added).
3. **uvx cold-start in CI adds latency** (~seconds; the package has zero
   runtime deps). Accepted.
