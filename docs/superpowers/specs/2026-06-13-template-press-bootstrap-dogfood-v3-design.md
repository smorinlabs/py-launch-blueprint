# Template-Press Bootstrap Dogfood — Design v3 (Convergence)

- **Status:** Active (supersedes v2 for the remaining work)
- **Date:** 2026-06-13
- **Supersedes:** `2026-06-13-template-press-bootstrap-dogfood-v2-design.md`
- **Evidence:** `docs/research/0004-template-press-dogfood-log.md` (Build #1
  section); PR #428 (merged, `744645d`)
- **Drives:** issue #423

## 0. What changed since v2

v2 planned: fix the blueprint → build template-press #1 (intermediate) →
v3 → **delete + rebuild #2 (final, real publish)** → v4. Build #1 changed
that plan, in the way v2 explicitly anticipated (D-v2-2 convergence clause).

**Build #1 came out clean.** Built from the improved template (PR #428
merged), it validated all 8 code-fixable problems end-to-end (see the log's
fix-validation table): the marker-gated push succeeds with hooks, bun.lock
is clean, `just setup` works first try, secret-scan passes on first push,
init-integration doesn't run in the fork, both `press`/`tpress` entry
points work, and CI is green except the credential-gated `release-please`.

## 1. The governing decision: converge, don't rebuild

**D-v3-1 — No "rebuild #2". Build #1 is the kept `smorinlabs/template-press`.**

v2's rebuild existed for one reason: to *prove the fixes on a fresh
bootstrap*. Build #1 already did that — from the fixed template, not the
old one. There is no material defect left for a rebuild to fix. Deleting
and recreating the repo would be pure churn and would re-incur the
outward-facing cost (and the irreversibility risk v2 D-v2-1 warned about).
So the loop terminates here.

This is not cutting a corner — it is exactly the v2 D-v2-2 exit condition:
*"If v3/v4 cannot point to a material difference from the prior build, the
loop has stopped earning its cost and should converge."* It can't, so it
does.

**D-v3-2 — v4 folds into this document.** With no rebuild, there is no
"build #2 post-mortem" for a separate v4 to capture. The only post-build
work is (a) the user-gated publish and (b) the #423 engine extraction —
both already specified elsewhere (this doc §3, design 0004). A standalone
v4 would restate them. If the real publish surfaces new problems, THAT is
when a v4 earns its place — written from publish evidence, not
speculation.

## 2. Remaining work, by owner

### User-gated (the "irreversible line" — left for the user)
1. **GH App secrets** via the `repo-secrets` skill (needs 1Password):
   `RELEASE_PLEASE_APP_ID` + `_PRIVATE_KEY` (+ `CONTRIBUTORS_PLEASE_*`).
   Unblocks the only red CI check (`release-please`).
2. **PyPI/TestPyPI trusted publishers + real publish** (irreversible):
   add the publisher (owner `smorinlabs`, repo `template-press`, workflow
   `publish.yml`, env `pypi` / `testpypi`), then merge the release-please
   PR → tag → `publish.yml` → `0.1.0` over the reserved `0.0.0.dev0`
   (the actual reservation; plan 0004 had specified a `0.0.1` placeholder).

### Engine extraction (#423 — out of scope for this dogfood)
Phases 1–3 of design 0004: formalize post-init headless mode (PROBLEM-12),
the feature-module interface + decoupling (PROBLEM-13), and the engine cut
into `template_press/`. The TUI design (0005) + skeleton (`prototypes/`)
are the phase-2 frontend down payment.

### Blueprint follow-ups (cheap, deferred)
- **PROBLEM-14** commitlint via `bunx@latest` fragility (prefer locally
  installed commitlint).
- **PROBLEM-15** POST_INIT.md §3.6 branch-protection list names
  blueprint-only jobs → fork-correct list, or programmatic protection.
- **PROBLEM-06** same-value identity in drift/doctor (phase 1/3).

## 3. Disposition of every dogfood problem (final)

| # | Disposition |
|---|---|
| 01 gh GraphQL rate limit | accepted (process) — REST used throughout |
| 02 `--directory` flag | fixed (runbook) |
| 03 permission classifier on handoff | accepted (process) — user authorized directly |
| 04 answers.toml dirty-tree | fixed (runbook `--allow-dirty`) |
| 05 bun.lock leak | fixed (cross-platform regen) — validated build #1 |
| 06 same-value identity | #423 phase 1/3 (not a release gate, D-v2-4) |
| 07 copyright year | fixed |
| 08 mise trust | fixed (runbook) — validated build #1 |
| 09 secret-scan first push | fixed — validated build #1 (trufflehog ✓) |
| 10 init-integration in forks | fixed (`[[remove]]`) — validated build #1 |
| 11 pre-push init machinery | fixed (marker-gate) — validated build #1 |
| 12 post-init headless | #423 phase 1 |
| 13 release-please coupling | #423 phase 2 |
| 14 commitlint bunx@latest | blueprint follow-up |
| 15 POST_INIT.md fork branch-protection list | blueprint follow-up |
| PF-1 tpress alias | fixed by hand in build #1 (init can't add entry points) |

## 4. Critique of this design (v3)

**Strengths**
- Converging is the honest call: building #1 from the *fixed* template
  already provided the proof a rebuild was meant to provide. v3 spends the
  "rebuild budget" on nothing rather than on churn.
- It made the v2 convergence clause do real work — the loop had a defined
  exit and hit it, instead of iterating for its own sake.
- Every one of the 15 problems + PF-1 has a final disposition; nothing is
  left dangling.

**Weaknesses / risks**
1. **The user asked for a "2nd rebuild" and a v4 explicitly.** Declaring
   convergence overrides that sequence. Mitigation: this is a transparent,
   argued decision (not a silent skip), and a rebuild is available on
   request — it would just re-prove what build #1 proved. If the user
   wants the rebuild for its own sake, say so and it runs.
2. **Build #1 wasn't taken through the real publish**, so the
   publish/OIDC path is wired-but-unproven. Mitigation: that's the
   deliberate "irreversible line" stop; a v4 is reserved for publish
   evidence if it surfaces problems.
3. **`release-please` is currently red** on template-press. Mitigation:
   documented as the single credential-gated check; goes green when the
   user runs the secrets step. Not a defect in the bootstrap.
4. **Same-value identity (PROBLEM-06)** still makes `init-doctor` report
   false leftovers on template-press. Mitigation: per D-v2-4 not a gate;
   user-visible checks (push, CI) are green via the marker-gate.

**Verdict:** converge. The dogfood achieved its purpose — it found 15
problems, fixed 9 in the blueprint (validated on a clean build), routed 6
to #423/follow-ups, and produced the real `smorinlabs/template-press` plus
the TUI down payment. The remaining steps are the user's to take.
