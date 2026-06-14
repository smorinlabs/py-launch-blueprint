# Template-Press Bootstrap Dogfood — Design v2

- **Status:** Active (supersedes the v1 spec for the build loop)
- **Date:** 2026-06-13
- **Supersedes:** `2026-06-12-template-press-bootstrap-dogfood-design.md`
- **Evidence:** `docs/research/0004-template-press-dogfood-log.md` (Run 1,
  13 problems + coverage matrix), advisor review 2026-06-13
- **Drives:** issue [#423](https://github.com/smorinlabs/py-launch-blueprint/issues/423)

## 0. What changed since v1

v1 assumed one throwaway run, a human design-review gate, then one real
template-press run. Reality (Run 1) and the expanded user direction changed
three things:

1. The approval gate is removed — the loop runs autonomously, each stage
   producing a design + critique before the next build.
2. Run 1 surfaced a **structural cluster** (PROBLEM-06/10/11): generated
   repos inherit the blueprint's own init-maintenance machinery (drift
   check, init-tests, init-integration CI, pre-push hooks) which is
   meaningless and broken in a fork. The throwaway could only push with
   `--no-verify`. A *real* repo we intend to keep cannot end that way.
3. `template-press` is already reserved on PyPI + TestPyPI at `0.0.0.dev0`
   — name-squatting urgency is gone, and **PyPI version immutability now
   constrains the rebuild loop** (§2).

## 1. The four governing decisions (advisor 2026-06-13)

These are binding for every build below.

### D-v2-1 — Defer ALL real publishing to the final build only

PyPI and TestPyPI releases are immutable and unique. If an intermediate
build publishes `0.1.0`, no later build can republish it, and a repo that
already holds a published release + trusted-publisher config is messy to
delete. Therefore:

- **Intermediate builds** prove the publish path is *wired and green up to
  the publish step*: `publish.yml` present and valid, OIDC reached,
  trusted-publisher form values computed — but **no trusted publisher is
  configured and no release tag is cut.** Nothing irreversible fires.
- **Only the final build** configures trusted publishers, merges the
  release-please PR, cuts the tag, and publishes `0.1.0` over `0.0.0.dev0`.
- Consequence: an intermediate `smorinlabs/template-press` has never
  published and has no publisher config, so deleting it to free the name
  for the final build is clean.

### D-v2-2 — Explicit cheap-fix vs. #423-scale line

Between builds, only **cheap, local, non-extraction** fixes are applied to
the blueprint. Everything structural is mapped to a #423 phase and is
allowed to *deliberately re-hit* in the next build (the re-hit is evidence,
not failure). The line:

| Fixed before next build (cheap) | Deferred to #423 (structural, re-hits) |
|---|---|
| PROBLEM-02 runbook `--directory` flag | PROBLEM-06 same-value identity in drift/doctor (phase 1/3) |
| PROBLEM-04 answers.toml dirty-tree (doc/flag) | PROBLEM-10 init-integration CI in forks (phase 3) |
| PROBLEM-05 bun.lock workspace name | PROBLEM-11 init machinery in forks — *partial* cheap fix below (D-v2-3) |
| PROBLEM-07 copyright-year | PROBLEM-12 post-init headless/`--config` (phase 1) |
| PROBLEM-08 `mise trust` setup step | PROBLEM-13 release-please/publish coupling (phase 2) |
| PROBLEM-09 secret-scan BASE==HEAD first push | PROBLEM-03 agent-flow permission (process, not code) |

If v3/v4 cannot point to a *material* difference from the prior build,
the loop has stopped earning its cost and should converge to the final
build.

### D-v2-3 — Marker-gate the init-maintenance hooks/CI (the one structural-ish fix worth doing now)

This is NOT the engine extraction (D5 still holds: extract third). It is
the minimum that lets a *kept* repo end with green CI and a working
pre-push, consistent with the migration map's intent ("guard/CI/tests stay
with the blueprint, never run in forks"):

- Gate the init-maintenance lefthook pre-push steps and the
  `init-integration` / drift CI on the **absence** of
  `init/.blueprint-initialized` — exactly how `init/guard.sh` already
  gates its banner. In a generated (initialized) repo they become no-ops;
  in the blueprint they run unchanged.
- Acceptance: in a freshly bootstrapped repo, `git push` succeeds with
  hooks enabled (no `--no-verify`) and CI has no init-maintenance failures.

This fix is applied to the blueprint *before* the final build, so the real
`template-press` ends green. It may be applied before the intermediate
build too (preferred), so the intermediate validates the fix.

### D-v2-4 — Same-value identity is a known finding, not a release gate

Author `Steve Morin` and owner `smorinlabs` equal the blueprint's own
identity, so `init-doctor`'s `no-identity-leak` and the manifest-drift
check report false leftovers (PROBLEM-06). For this loop we **do not gate
any build on doctor-clean**; we record the false-positive count and move
on. A scoped "expected-new-value aware" fix is #423 work (phase 1/3), not
loop work. (The marker-gate in D-v2-3 already removes the *pre-push/CI*
manifestation; D-v2-4 governs the remaining local `init-doctor` report.)

## 2. The build loop

```
Run 1  blueprint-dryrun        DONE — throwaway, 13 problems, kept as fixture
  │
  ▼
v2 design + critique           ← this doc
  │
  ▼
blueprint fixes (D-v2-2 cheap + D-v2-3 marker-gate)   committed to blueprint
  │
  ▼
Build #1  smorinlabs/template-press  (intermediate, NO real publish)
  │   bootstrap → init → post-init(publishing=yes, codecov/rtd=later)
  │   prove: CI green, push w/ hooks, publish.yml valid, OIDC reached
  ▼
v3 design + critique           from build-#1 learnings
  │
  ▼
delete intermediate template-press (clean: no publisher, no release)
  │   + any further cheap blueprint fixes
  ▼
Build #2  smorinlabs/template-press  (FINAL, real publish)
  │   full post-init → trusted publishers → merge release PR → 0.1.0
  ▼
v4 design + critique           from build-#2 learnings
  │
  ▼
TUI design + start building     (post-init concierge: interview → board → errand cards)
  │
  ▼
feedback loop on #423 (comment, phase mapping, project-add)
```

Deleting the intermediate public repo is a destructive, outward-facing
action; it is in-scope (the user asked for a rebuild) and is gated on
D-v2-1 holding (no publisher/release on the intermediate) and a contents
check first.

## 3. Per-build invariants (all builds)

- Identity (both template-press builds): package `template_press`, repo
  `template-press`, app `press`, author `Steve Morin
  <steve.morin@gmail.com>`, owner `smorinlabs`, public.
- `tpress` alias entry point is added by hand post-init (init can't add a
  second console script) — PF-1, log it.
- Live log appended during the run; every deviation a numbered PROBLEM
  with disposition.
- No build is gated on `init-doctor` clean (D-v2-4). Builds ARE gated on
  `just check` passing and (post D-v2-3) CI + push green.

## 4. Success criteria

- Each design (v2/v3/v4) names a material change from its predecessor or
  declares convergence.
- The final `smorinlabs/template-press` exists, CI green, pushes with
  hooks enabled, and has published `0.1.0` to PyPI over `0.0.0.dev0`.
- The blueprint carries the cheap fixes + the D-v2-3 marker-gate, each a
  conventional commit referencing its PROBLEM number.
- A TUI design doc exists and TUI implementation has begun.
- `#423` has a summary comment mapping every PROBLEM to a phase.

## 5. Critique of this design (v2)

Self-review with fresh eyes, per the user's "design then critique" ask:

**Strengths**
- D-v2-1 is the load-bearing call; without it the loop is incoherent
  (you cannot rebuild over an immutable published version). It is now
  explicit and gates deletion safety.
- D-v2-3 converts the headline finding (PROBLEM-11) into a concrete,
  bounded, non-extraction fix with a falsifiable acceptance test, and it
  reuses an existing pattern (`guard.sh` marker-gating) rather than
  inventing mechanism.
- The cheap/structural table (D-v2-2) makes "did the redesign earn its
  cost?" answerable instead of vibes-based.

**Weaknesses / risks (and mitigations)**
1. **Loop may not converge — v3/v4 risk being near-duplicates.** Mitigation:
   D-v2-2's convergence clause is a real exit condition; if build #1 is
   clean after D-v2-3, build #2 becomes "apply remaining cheap fixes +
   real publish," and v4 is mostly the publish post-mortem + TUI runway —
   that's acceptable convergence, not wasted motion.
2. **D-v2-3 is more than "cheap."** Marker-gating CI + lefthook touches the
   blueprint's most load-bearing invariant (the drift check that keeps the
   manifest honest). Risk: gating it too broadly disables the check *for
   the blueprint itself*. Mitigation: gate strictly on marker presence;
   the blueprint has no marker, so its own CI is unchanged — must be
   verified by running blueprint CI locally after the change
   (`init/ci/check_manifest_drift.py`, init tests) before any build.
3. **Deleting + recreating the real repo name** is irreversible-ish and
   outward-facing. Mitigation: only the *intermediate* is deleted, and
   only after confirming it never published; the final repo is created
   once and kept.
4. **Same-value identity (D-v2-4) is punted, not solved** — the real repo
   will show a non-clean `init-doctor`. Risk: looks broken to a future
   reader. Mitigation: documented explicitly as a known #423 finding in
   the repo's own notes, and the *user-visible* gates (push, CI) are green
   via D-v2-3.
5. **TUI scope is open-ended** and tacked on at the end. Mitigation: the
   TUI step's deliverable is bounded to "a design doc + a runnable
   skeleton (interview screen)", not a finished TUI; full TUI is phase-2
   engine work.

**Verdict:** proceed. The one item to verify empirically before trusting
the loop is weakness #2 — confirm the marker-gate leaves the blueprint's
own drift check fully armed.
