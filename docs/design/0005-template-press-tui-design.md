# Template-Press Post-Init TUI — Design

- **Status:** Draft (design only; implementation starts with the interview skeleton)
- **Type:** Design
- **Created:** 2026-06-13
- **Applies to:** the `press setup` (post-init) **TUI frontend** of the
  template-press engine (design doc
  [0004](0004-template-press-plan.md) §3, frontends/tui)
- **Inputs:** [analysis 0003](../research/0003-init-post-init-analysis.md)
  Part 2B (the concierge model, board + errand mockups, the four-state
  lifecycle); [dogfood log 0004](../research/0004-template-press-dogfood-log.md)
  Run 1 (PROBLEM-12 no-headless / EOF-writes-defaults, PROBLEM-13
  release-please coupling)

> The CLI/JSON frontend is the agent face and init's only face; this doc is
> the **human** face of post-init. Both sit over the same pure core
> (`schema · config · state · plan · board · checks`). The TUI never
> touches effects directly — it renders the board the core derives and asks
> the core to plan/apply. This is what keeps "agent mode" and "human mode"
> the same program with two faces, not two codebases.

---

## 1. Why a TUI at all

Run 1 made the human pain concrete. Today's `post_init.py` is a wizard:
question → act → question → act. Its failures (dogfood Run 1):

- **No "where was I?"** — re-running replays the interview; there is no
  board showing what's done vs. pending vs. blocked-on-you.
- **EOF/empty input silently commits defaults** (PROBLEM-12): a non-answer
  is treated as "accept all defaults and write the marker."
- **Decisions and actions are interleaved** — quit halfway and you're
  nowhere; the state is whatever happened to be written.
- **Manual errands (accounts, tokens, consent screens) have no home** —
  the most fatiguing work is exactly what the wizard can't represent.

The concierge model (analysis 0003 Part 2B) fixes this: **decide → derive
the board → work the board**, with status computed from reality every run.
The TUI is the surface that makes that model low-fatigue for a human.

## 2. Architecture fit (no new logic in the frontend)

```text
        core (pure)                         TUI frontend (this doc)
  ┌───────────────────────┐          ┌──────────────────────────────┐
  │ schema  (features/*)  │  board   │ interview.py  first run        │
  │ config  (decisions)   │ ───────► │ dashboard.py  every later run  │
  │ state   (state.toml)  │          │ errand.py     one manual task  │
  │ plan / board / checks │ ◄─────── │  (emits decisions + apply reqs)│
  └──────────┬────────────┘  intents └──────────────────────────────┘
             │ effects (local/remote/manual) — invoked by core, never by TUI
             ▼
        repo files · gh API · pypi API
```

Contract: the TUI calls exactly three core entry points —
`derive_board(config, state)`, `apply(plan, only=…)`, and
`run_checks(board)` — and renders their results. It records the user's
choices into the `decisions` config and asks the core to re-plan. No
status is stored by the TUI; every render recomputes from reality
(repo files, `gh`, PyPI). This is the load-bearing rule from analysis 0003
("status computed, never stored").

## 3. Three screens, one model

### 3.1 Interview (first run only — lowest fatigue)

Linear questions, sensible defaults, **"later" always available at zero
cost**. Crucially (fixing PROBLEM-12): the interview distinguishes
*answered* from *not-answered*. Empty input/EOF means **defer**, never
"commit defaults silently" — and nothing is written until an explicit
confirm step. The decision graph prunes: answering "no" to a parent
removes its sub-questions entirely.

```text
 ┌─ template-press · setup (first run) ───────────────────────────┐
 │  I'll ask a few questions, then show you a board. "later" is    │
 │  always fine — nothing is written until you confirm.           │
 │                                                                │
 │  Publish releases to PyPI?            (y) yes  (n) no  (l) later│
 │    └ on yes →  mirror to TestPyPI?            [Y/n]            │
 │  Use release-please for version PRs?  (y) yes  (n) no  (l) later│   ← independent of PyPI (PROBLEM-13)
 │  Upload coverage to Codecov?          (y) yes  (n) no  (l) later│
 │  Host docs on ReadTheDocs?            (y) yes  (n) no  (l) later│
 │                                                                │
 │  [enter] review the plan before anything is written            │
 └────────────────────────────────────────────────────────────────┘
```

Note the decoupling: release-please is its own question, not a child of
"publish to PyPI" (Run 1 PROBLEM-13 — release-please is useful without
publishing).

### 3.2 Dashboard / board (every later run — "where was I?")

The second-session question is never "ask me everything again," it's
"where was I?" The board is the answer. Status glyphs are computed from
reality on open.

```text
 ┌─ template-press · setup board ───────────────────── checks: 3s ago ─┐
 │                                                                     │
 │  Publishing            ● enabled         2 of 4 done                │
 │    ├ publish.yml wired              ✓                               │
 │    ├ release-please wired           ✓                               │
 │    ├ PyPI OIDC trusted publisher    ⚠ needs you      [enter]        │
 │    └ TestPyPI trusted publisher     ◌ blocked by ↑                  │
 │                                                                     │
 │  Coverage · Codecov    ◐ deferred         [enter] to decide         │
 │  Docs · ReadTheDocs    ○ dormant          re-enable anytime         │
 │  Branch protection     ◌ not asked        [enter] to decide         │
 │  Funding / sponsors    ⊘ removed                                    │
 │                                                                     │
 │  [a]pply machine tasks   [r]efresh checks   [enter] open   [q]uit   │
 └─────────────────────────────────────────────────────────────────────┘
```

Glyphs (computed, never stored): `✓` done · `◌` todo · `⊘` n/a (pruned by
a decision) · `⚠` needs-human · `✗` broken (a check failed on a
supposedly-done task) · `●` enabled · `○` dormant · `◐` deferred.

These map onto the four-state lifecycle `deferred → enabled ⇄ dormant →
removed` (design 0004 D9); `removed` is one-way and only reached behind a
shown plan + confirm.

### 3.3 Errand card (one manual task — the direct attack on fatigue)

Pressing `enter` on a `⚠ needs-you` task opens a card that **opens the
page, pre-computes every value, and verifies completion itself**:

```text
 ┌─ PyPI trusted publishing (manual, ~3 min) ──────────────────┐
 │  1. open  https://pypi.org/manage/project/template-press/    │
 │           settings/publishing/                              │
 │  2. add a GitHub Actions publisher with EXACTLY:            │
 │       owner       smorinlabs                                │
 │       repository  template-press                            │
 │       workflow    publish.yml                               │
 │       environment pypi                                      │
 │  3. submit                                                  │
 │                                                             │
 │  verify: polling pypi.org for the publisher… ⠋             │
 │  (this card closes itself when the check passes)            │
 │  [o]pen page   [c]opy values   [s]kip for now   [esc] back  │
 └─────────────────────────────────────────────────────────────┘
```

The card is generated from the feature module's `manual` action +
`check`: the instructions and pre-filled values come from the schema; the
self-closing verification is the check recomputed against reality.

## 4. Tech choice

| Concern | Choice | Why |
|---|---|---|
| Dashboard + errand cards | **Textual** | Rich interactive widgets, async polling for self-closing checks, testable via its `Pilot` harness, themable, runs in any modern terminal |
| Interview | **Textual** (same app, a linear screen) | One dependency, one event loop; the interview is just the app's first screen. (questionary was the wizard's tool; a single Textual app avoids two input models) |
| Rendering primitives | Rich (bundled with Textual) | Tables, spinners, styled glyphs |

Rationale: a single Textual app with three screens (`InterviewScreen`,
`DashboardScreen`, `ErrandScreen`) over the pure core. Async is needed
anyway for the self-closing `⚠` checks (poll `gh`/PyPI without freezing the
UI), and Textual's test harness lets the TUI be CI-tested — preserving the
blueprint's "permanently green, testable" property.

## 5. Data flow (one cycle)

1. On launch: `state = read(press/state.toml)`; if no `[setup]` section →
   InterviewScreen, else DashboardScreen.
2. `board = core.derive_board(decisions, state)`; `core.run_checks(board)`
   fills each task's live status (async).
3. Render. User acts:
   - decide → mutate `decisions`, re-derive board, re-render (no writes
     yet for `removed`, which needs the confirm gate).
   - `[a]pply` → `core.apply(plan, only={"local","remote"})`; manual tasks
     become `⚠` cards.
   - open `⚠` card → instruct + poll the task's `check`; on pass the card
     self-closes and the glyph flips to `✓`.
4. On any state change the core writes `press/state.toml` (the receipt);
   the TUI never writes state directly.

## 6. First build deliverable (bounded)

Per the dogfood plan, "start building the TUI" = a **runnable interview
skeleton**, not the finished TUI:

- A Textual app with `InterviewScreen` that asks the four real decisions
  (publishing, release-please, codecov, readthedocs) with y/n/later and
  the PROBLEM-12 fix (empty/EOF = defer, explicit confirm before any
  write).
- It produces a `decisions` object and prints it as JSON (the same shape
  the CLI/JSON frontend consumes) — proving the frontend↔core seam before
  the dashboard/cards exist.
- A Textual `Pilot` test that drives the interview headlessly and asserts
  the emitted decisions — so the TUI is CI-testable from day one.

DashboardScreen and ErrandScreen are subsequent increments; this skeleton
proves the architecture and the interview UX.

## 7. Critique

**Strengths**
- The TUI adds **zero domain logic** — it's a pure renderer of the core's
  board plus an editor of the decisions config. That keeps agent-mode and
  human-mode genuinely the same engine (the analysis's central promise).
- It directly fixes two Run 1 defects in the UX layer: PROBLEM-12
  (EOF≠commit; explicit confirm) and PROBLEM-13 (release-please as an
  independent question).
- Self-closing errand cards attack the actual fatigue (manual steps that
  are checkable but not automatable).

**Risks / open questions**
1. **Core doesn't exist yet.** The TUI depends on `core.derive_board` /
   `apply` / `run_checks`, which are #423 phase-1/2 work. The bounded
   deliverable (interview → JSON decisions) is chosen precisely so it can
   be built and tested against a *thin* core stub, not the full engine.
2. **Textual is a new dependency** for a repo that values a small,
   locked toolchain. Mitigation: it lands in the engine (template-press),
   not the blueprint; the blueprint only ever calls `uvx template-press`.
3. **Async self-closing checks can hang** on a slow `gh`/PyPI. Mitigation:
   every poll has a timeout and a manual `[s]kip for now` that leaves the
   task `⚠` on the board — never a frozen UI.
4. **Two input models risk** (interview vs. dashboard) is avoided by
   making the interview a Textual screen, but that couples the first
   deliverable to Textual. Accepted: one event loop is simpler than
   bridging questionary + Textual.

**Verdict:** the design is sound and bounded. Build the interview skeleton
against a thin core stub; it validates the frontend↔core seam (the thing
that matters) before the engine is fully extracted.
