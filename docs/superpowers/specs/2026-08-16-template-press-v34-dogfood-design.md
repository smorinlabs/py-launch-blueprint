# Template-Press v3.4 Dogfood & Conform — Design (v4 line)

- **Status:** Active
- **Date:** 2026-08-16
- **Lineage:** successor to
  `2026-06-13-template-press-bootstrap-dogfood-v3-design.md` (its D-v3-2
  reserved a v4 "written from publish evidence"; this is it, widened to the
  v3.4 engine surface and the conform milestone)
- **Evidence:** `docs/research/0004-template-press-dogfood-log.md`
  (PROBLEM-NN register, continued here); template-press
  `docs/research/0004-py-launch-blueprint-conformance-gaps.md` (G1–G5
  register, merged PR #40)
- **Drives:** issue #423 (engine extraction) — partially; scope gate in §4
- **Related in-flight:** py-launch-blueprint PR #505 (open,
  `fix(guard): accept a press receipt as an initialized marker`) — a
  **prerequisite for Phases 3–4**: a pressed instance carries
  `press/press-receipt.toml`, not the legacy init marker, so without #505
  the instance's own guard blocks `build`/`publish` (the July PROBLEM-11
  class). Merge it early (it is self-contained: `init/guard.sh` + tests)

## 0. Purpose — two goals that feed each other

1. **Test template-press** (the standalone `press` CLI) by running it for
   real against py-launch-blueprint. Every failure is either a press engine
   bug or blueprint drift; each finding is triaged to its owning repo and
   fixed there.
2. **Bring py-launch-blueprint into sync** with the current template-press
   contract, proving it end-to-end: `press verify` exits 0, and a pressed
   instance publishes into a new repo the way a real user would.

## 1. Press-under-test (pinned)

- **Tool:** template-press `main` @ `bd52085`
  (`Merge pull request #79 … p07-platform-conditional-declared-commands`).
  The `v3.4.0` tag predates P07 (platform-conditional declared commands +
  native platform regeneration), and P07 is part of "the new version" this
  campaign exists to test — so main, not the tag. Run as
  `uv run press …` from `~/c/template-press`.
- **Target baseline:** py-launch-blueprint `origin/main` @ `734abfd`.

**D-v4-1 — pin main, record the commit.** If template-press main moves
mid-campaign (our own fixes), re-pin explicitly in the dogfood log; never
test against an unrecorded tip.

## 2. What changed since the July gap register (expectations)

Prior-art review (changelog v3.2.0→v3.4.0, Run 3 of the dogfood log,
PR #505) shows **all five G1–G5 gaps now have engine support — every one
opt-in via the target's config**:

| Gap | July leaks | Engine support (release) | Blueprint must declare |
|---|---|---|---|
| G1 CHANGELOG excluded-not-reset | 678 | `[[reset]]` schema (v3.4.0) | `[[reset]]` stub for `CHANGELOG.md` |
| G2 bun.lock excluded-not-regenerated | 2 | `[[regenerate]]` + generic executor (v3.4.0) | `[[regenerate]]` via platform-split regen scripts |
| G3 app_name substring variants (`_plbp_owned`, `plbp-web`) | 16 | opt-in per-field substring rewrite mode (v3.3.0) | substring mode for `app_name` |
| G4 display name "Py Launch Blueprint" | 74 | optional `display_name` identity field with closed form set (v3.3.0) | `display_name` in `[identity]` |
| G5 doc filename tokens (`…-plbp.md`) | 2 (+4 refs) | `[[replace]]` rules + substring fields in path renames (v3.3.0) | rename coverage via substring/replace rules |

Plus new v3.4.0 surface to exercise: the excluded-file contract gate (§6),
`press check-tools`, receipt invalidation on forced re-press; and
post-v3.4.0 on main, P07 platform-conditional declared commands with
native platform regeneration.

**Falsifiable prediction: with a fully-declared config, `press verify`
reaches exit 0 with zero (or near-zero) `[[verify.ignore]]` entries.** Any
leak is either a config-authoring gap (blueprint finding) or an engine
regression (template-press finding) — there is no longer a known-gap
bucket to absorb it. Run 3's governing caution still binds: green must be
earned by *declarations*, never by ignores that paper over capability
gaps.

## 3. Standing decisions

- **D-v4-2 — adaptive scope.** Start as *sync + publish*. The full conform
  (delete `init/`, CI cutover to `press verify`, per the 2026-07-23 conform
  handoff's phases 4–7) is decided at the §4 scope gate, not assumed.
- **D-v4-3 — publish lands local-first, then one throwaway GitHub repo.**
  Iterate on local copies; only after rebrand+verify are clean create
  `smorinlabs/blueprint-press-dryrun` (name confirmable at the gate) with
  explicit user authorization (July PROBLEM-03: agent-initiated public repo
  creation is permission-gated by design).
- **D-v4-4 — batch PR per iteration round.** One worktree per repo per
  round; a round's fixes merge together; the round exits only when verify
  is green against fresh clones of both repos' `main`.
- **D-v4-5 — engine gaps are never worked around in the blueprint**
  (carried from the July C/D/E handoff). A leak caused by a missing engine
  capability is fixed in template-press or explicitly deferred with a
  `[[verify.ignore]]` carrying a reason — never papered over by rewording
  blueprint content to dodge the scanner.
- **D-v4-6 — findings go in the existing register.** Continue PROBLEM-NN
  numbering in `docs/research/0004-template-press-dogfood-log.md` as a new
  "Run 4 — v3.4 conform" section, starting at **PROBLEM-21** (Run 3 ended
  at PROBLEM-20); severity/workaround/root-cause/disposition fields as
  established.

## 4. Phases

### Phase 0 — pin & preflight (done at spec time)
Pins recorded (§1), expectations table built (§2). Pre-existing state
reported, not touched:

- py-launch-blueprint local `main` is **ahead 1 / behind 2** of origin —
  user to reconcile; campaign work branches from `origin/main` so this
  does not block.
- Stale worktrees `py-launch-blueprint-guard` (PR #505's branch) and
  `py-launch-blueprint-p1verify` (detached, holds an uncommitted July 25
  draft `press/press-source.toml` — prior art only; per user decision the
  config is authored from scratch). Disposition at close-out, with user.
- template-press live checkout has one untracked handoff doc.

### Phase 1 — conform config, first meaningful verify
In the campaign worktree (branch `feat/press-conform`, from `origin/main`):

1. Author `press/press-source.toml` from scratch (the July `p1verify`
   draft is prior art only, not reused) — `[identity]`: package
   `py_launch_blueprint`, repo `py-launch-blueprint`, app `plbp`, owner
   `smorinlabs`, author `Steve Morin`, email `steve.morin@gmail.com`,
   plus the new optional `display_name = "Py Launch Blueprint"` (G4).
2. Author `press/press-rules.toml` with template-press's own committed
   `press/press-rules.toml` as the canonical model: `[[reset]]`
   `CHANGELOG.md` → stub; `[[regenerate]]` `uv.lock` and `bun.lock`
   (bun.lock needs platform-split regen scripts — bun install alone never
   rewrites an existing lock's workspace name; blueprint needs its own
   copies); substring mode for `app_name` (G3); rename coverage for the
   `…-plbp.md` doc filenames (G5); `[verify]` config as needed.
3. Optionally commit a `press/press-answers.example.toml` placeholder
   (advertised field shape; the filled file stays uncommitted operator
   input).
4. Run `uv run press verify --target <this worktree>` from template-press.
   Exit 2 expected until config parses; then iterate to a real leak scan.
   Record every leak class as a PROBLEM-NN entry mapped to G1–G5 or new.

Without step 1, verify exits 2 by design — so the first *meaningful*
verify, and the scope gate below, sit at the end of this phase.

### Scope gate (user decision, end of Phase 1)
Present the leak inventory vs. the §2 prediction. Decision rule offered:

- **Verify reaches exit 0 via declarations** (zero/near-zero ignores) →
  the Run-3 pause condition ("enhance press to init/ parity first") is
  discharged; offer upgrading this campaign to the full conform (init/
  deletion + CI cutover, per the 2026-07-23 handoff phases 4–7).
- **New engine gaps surface** (leaks no declaration can express) → stay
  sync+publish; file them against template-press; full conform becomes a
  follow-up campaign once they land.

### Phase 2 — iterate loop (repeat until round exits clean)
1. **Triage** each finding: engine bug → template-press worktree (TDD:
   failing test first); config/content drift → blueprint worktree
   (this one, or a fresh one per round after round 1).
2. Mid-round, verify runs against the worktrees.
3. Round exit: PRs merged in both repos (blueprint under its merge guard —
   `pr-merge-flow`; template-press per its conventions), then
   `press verify` green against **fresh clones of both mains**. Re-pin per
   D-v4-1.

### Phase 3 — local rebrand + new-surface coverage
Precondition: **PR #505 merged** (receipt-aware guard), else the pressed
instance's own pre-push guard blocks it (July PROBLEM-11 class).

On a disposable copy of the blueprint (scratch clone, never the live
checkout), with a filled `press-answers.toml` for a synthetic instance
identity (values chosen at execution; e.g. package `blueprint_press_dryrun`
/ repo `blueprint-press-dryrun` / app `bpd`):

- `press rebrand --dry-run` — plan review (counts, renames, resets).
- Apply — exit 0, receipt written; grep-audit for leaks beyond the
  scanner's own claim.
- Forced re-press — prior receipt invalidated (new v3.4 behavior).
- `press check-tools` — declared commands resolve (and a negative case:
  a missing tool reports without crashing).
- Declared-command execution actually ran: CHANGELOG reset to stub,
  bun.lock regenerated (macOS native platform path — P07).
- Exit codes asserted on every run (0/1/2 contract).
- Pressed instance passes its own `make check` and `just check` after
  `mise trust` + `just setup` (July PROBLEM-08 runbook order).

### Phase 4 — GitHub publish (user-gated)
1. User authorizes and/or creates the throwaway repo (reader-step block at
   execution time), pressed instance pushed.
2. Watch CI via REST, polling ≥20s. Pre-listed failure classes from the
   July dogfood to check first on any red: inherited blueprint maintenance
   hooks blocking push (PROBLEM-11 regression), secret-scan on first push,
   release-please coupling/credentials, stale bun.lock.
3. Any new failure is a PROBLEM-NN finding, triaged like Phase 2.

### Phase 5 — close-out
- Dogfood log: every PROBLEM-NN has a final disposition (fixed+merged,
  filed as issue, or accepted with reason).
- PROJECTS.md registration/updates via the project-harness skills.
- Merged worktrees removed + pruned; stale July worktrees and PR #505
  dispositioned with the user; throwaway repo kept or deleted (user call).
- Final report against §5.

## 5. Exit criteria

**Goal 1 (template-press tested):** rebrand (dry-run, apply, forced
re-press), verify, and check-tools all exercised against a real target,
including the declared-commands and P07 platform surface; every discovered
bug dispositioned.

**Goal 2 (blueprint in sync):** `uv run press verify --target
<fresh py-launch-blueprint main clone>` exits 0; a pressed instance passes
its own checks and sits in the new repo with CI green (release-please may
stay credential-gated red, as in v3 — documented, not a gate).

## 6. Out of scope

- `press provision` / `press status` (M6 — unshipped verbs).
- The G4 display-name *design decision* itself (codesign with the user, per
  the C/D/E handoff) — this campaign may *surface* the evidence but not
  unilaterally pick Option A/B.
- Publishing template-press to PyPI; blueprint release engineering beyond
  what the throwaway instance exercises.
- Recreating either repo (v3 D-v3-1 stands: converge, don't rebuild).

## 7. Critique of this design

**Strengths**
- The §2 prediction makes the first verify falsifiable — the run has
  expected numbers, so surprise is measurable, not vibes.
- Adaptive scope avoids committing to the semi-irreversible init/ deletion
  before evidence exists that the engine can carry the blueprint.
- Reuses the established registers (PROBLEM-NN, G1–G5) instead of a third
  findings format.

**Weaknesses / risks**
1. **All five gap closures are unproven against their motivating target.**
   G1–G5 support shipped tested against template-press itself (R3
   self-press), not against the blueprint whose leaks motivated them —
   the 74-occurrence display-name surface and the substring variants may
   hold edge cases. Mitigation: that is precisely what Phase 1 measures;
   the zero-leak prediction makes shortfalls loud.
2. **PR #505 timing** — Phases 3–4 depend on it merging; it is open with
   the blueprint's heavy merge guard. Mitigation: drive it early (Phase 1
   window) via `pr-merge-flow`; it is small and self-contained.
3. **Blueprint's heavy merge guard** makes batch PRs slow (bot threads
   re-open on every push). Mitigation: D-v4-4 batches per round; rounds
   sized so a PR is coherent, not sprawling.
4. **Testing against a moving main** (our own fixes land mid-campaign).
   Mitigation: D-v4-1 re-pin discipline; round exits verify against fresh
   clones.
