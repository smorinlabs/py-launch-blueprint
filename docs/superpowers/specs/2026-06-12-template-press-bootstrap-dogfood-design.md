# Template-Press Bootstrap Dogfood — Design

- **Status:** Approved (pending user review of this written spec)
- **Date:** 2026-06-12
- **Drives:** issue [#423](https://github.com/smorinlabs/py-launch-blueprint/issues/423)
  (create `smorinlabs/template-press`); feeds phases 1–2 of
  [design doc 0004](../../design/0004-template-press-plan.md)
- **Rationale inputs:** [research doc 0003](../../research/0003-init-post-init-analysis.md),
  [`docs/POST_INIT.md`](../../POST_INIT.md)

## 1. Goal

Create `smorinlabs/template-press` by **dogfooding the blueprint's own
template machinery** (the `new-python-project` runbook, `init/init.py`
rebrand, `init/post_init.py`, and the full `docs/POST_INIT.md` checklist),
in two runs:

1. **Run 1 — throwaway dry run** (`blueprint-dryrun`): find problems on a
   repo nobody cares about; skip publishing.
2. **Triage gate + design review (hard pause):** fix small blueprint
   defects upstream; map structural findings to #423 phases; then re-review
   this design with the user against the run-1 log before any run-2 action.
3. **Run 2 — template-press:** repeat against the improved blueprint, with
   publishing wired to the already-reserved PyPI/TestPyPI names.

Every step and every problem is logged live. The log and its POST_INIT
coverage matrix are first-class deliverables — they are the empirical input
to phase 1 (formalize post-init) and phase 2 (feature-module interface) of
the template-press plan.

## 2. Constraints and non-goals

- **No engine extraction.** Per decision D5 ("extract third, not first")
  and the two-repos-too-early guardrail, run 2 creates the template-press
  *repo scaffold* only — a rebranded placeholder package. Engine code moves
  in phase 3, later, separately.
- **Name reservation is already done.** `template-press 0.0.0.dev0` exists
  on both PyPI and TestPyPI (verified 2026-06-12). Run 2's publishing step
  is "add trusted publishers to the existing projects," not "claim the
  name." The first release-please release (≥ 0.0.1) supersedes the dev0
  placeholder.
- **Problems are never silently worked around.** Each gets a log entry
  (see §6) before work continues.
- **Destructive steps are confirmed.** Deleting the throwaway repo at the
  end is its own confirmed step, with its contents shown first.

## 3. Identities

Common: author **Steve Morin** · email **steve.morin@gmail.com** · owner
**smorinlabs** · public visibility. Note author/email equal
`BLUEPRINT_IDENTITY` in `init/common.py` — the rebrand's author/email
replacements are same-value no-ops (predicted finding PF-2, §7).

| Field | Run 1 | Run 2 |
|---|---|---|
| GitHub repo | `smorinlabs/blueprint-dryrun` | `smorinlabs/template-press` |
| Local path | `~/c/blueprint-dryrun` | `~/c/template-press` |
| Package | `blueprint_dryrun` | `template_press` |
| CLI app name | `bpd` | `press` |
| PyPI dist | — (publishing skipped) | `template-press` (exists, dev0) |

Design doc 0004 §2 also wants a `tpress` alias console script for run 2;
the init rebrand cannot express "add a second entry point" (predicted
finding PF-1) — added by hand after init, logged.

## 4. Run sequence (both runs; run-specific deltas marked)

1. **Log first.** Append a run header to the live log (§6) before any
   action.
2. **Bootstrap via the `new-python-project` skill, invoked explicitly**
   (its auto-trigger recall is known-zero; explicit invocation is itself
   the test): precondition checks → `gh repo create --template
   smorinlabs/py-launch-blueprint` → clone → `init/init.py` rebrand with
   **dry-run preview shown to the user before apply** → verification
   (`just setup`, `just check`, `init-doctor`) → initial commit + push.
3. **Automated post-init** (`just post-init`):
   - Run 1: publishing **no** (exercises today's conflated "no"/dormant
     path that phase 1 splits), Codecov **later**, RTD **later**.
     `post_init.py` treats release-please as a sub-decision of PyPI
     publishing, so "no" will also disable `release-please.yml`; we then
     re-enable it by hand during step 4 and log the coupling (PF-5).
   - Run 2: publishing **yes** (PyPI + TestPyPI + release-please),
     Codecov **later**, RTD **later** ("later" leaves live `deferred`
     fixtures for the future four-state lifecycle).
4. **Full POST_INIT.md §1–§3 walk**, building the coverage matrix (§5).
   Decisions for both runs:

   | Item group | Decision |
   |---|---|
   | Core CI, hooks, commitlint, lint extras | keep |
   | CodeQL (verify default-setup OFF), secret scanning, dependency review | keep |
   | release-please (+ secrets via the `repo-secrets` skill / 1Password) | keep — run 1 included: tests secret wiring + release PR flow with publish.yml disabled, zero PyPI side effects |
   | Contributors automation (same skill) | keep |
   | Branch protection, Actions-PR permission, dependabot, private vuln reporting, merge strategy | set via the documented `gh api` commands |
   | publish.yml / PyPI + TestPyPI trusted publishers | run 1: **skip** · run 2: **yes**, against the existing PyPI projects (manual errand for the user, values pre-computed) |
   | Codecov, ReadTheDocs | later |
   | Safety manual scan, CLA gate | defer |
   | Funding | keep as-is (already points at the author) |

5. **Release (run 2 only):** merge the release-please PR → `v0.x` tag →
   `publish.yml` → TestPyPI then PyPI.
6. **Wrap-up:** finalize the run's log section; run 1 proceeds to the
   triage gate, run 2 to the feedback loop (§8).

## 5. Coverage matrix (key deliverable)

One row per POST_INIT.md item, recorded during step 4:

> item · decision taken · automated by `post_init.py`? · how actually done
> (command / UI / skill) · phase-2 feature-module candidate? · problems hit

This is the ground truth for phase 2's `features/*.toml` set. The
`repo-secrets` skill is the reference implementation for the
release-please/contributors `remote` actions and is cross-referenced.

## 6. Logging protocol

Live log: `docs/research/0004-template-press-dogfood-log.md` (this repo),
sections **Run 1 / Triage / Run 2**. Written *during* the run — each step's
entry recorded before moving on, so a mid-run failure leaves an honest
record. Steps are timestamped commands + outcomes. Problems are numbered
`PROBLEM-NN` with: severity · what happened · workaround · root cause ·
disposition (fixed-in-blueprint commit, or #423 phase mapping).

## 7. Predicted findings (verify, don't assume)

- **PF-1:** init cannot add the `tpress` alias entry point (run 2).
- **PF-2:** same-value author/email rebrand edge case (validation, drift
  check, doctor behavior when new == blueprint value).
- **PF-3:** post-init's "no" conflates dormant/removed (run 1 publishing
  = no shows the concrete behavior).
- **PF-4:** POST_INIT.md manual items vastly outnumber automated ones —
  the matrix quantifies the gap.
- **PF-5:** release-please is modeled as a sub-decision of PyPI publishing,
  but it is useful without publishing (changelog + version bumps) — the
  `relevant_when` coupling in the future decision graph may be wrong.

## 8. Triage gate and feedback loop

**Triage (between runs):** for each run-1 `PROBLEM-NN`, either (a) small,
clear blueprint defect → fix, verify per AGENTS.md flow, conventional
commit upstream before run 2; or (b) structural → disposition recorded as
a #423 phase mapping. Run 2 must start from the improved blueprint.

**Design review checkpoint (hard pause — run 2 is gated on it):** after
triage, present the run-1 log and triage outcomes to the user and
re-review this design — including the live-log protocol itself (§6) and
the run-2 sequence — incorporating what run 1 taught. Run 2 starts only
on explicit user approval of the (possibly revised) design.

**Feedback (after run 2):** log + matrix committed here; summary comment
on #423 mapping every problem to a phase; phase-3 "create repo" checkbox
checked (PyPI reservation noted as already done); work registered on the
trunk via `project-add`. Finally, with confirmation, delete
`smorinlabs/blueprint-dryrun` and `~/c/blueprint-dryrun`.

## 9. Success criteria

- `smorinlabs/template-press` exists, green CI, rebranded, post-init
  decisions recorded, first release published over the dev0 placeholder.
- The log contains both runs with zero unlogged problems, and the coverage
  matrix covers every POST_INIT.md item.
- Run-1 fixes are committed to the blueprint; remaining findings appear on
  issue #423.
