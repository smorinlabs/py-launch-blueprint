# Template Press — Reusable Init/Post-Init Engine Plan

- **Status:** Accepted (implementation not started)
- **Type:** Design / decision record
- **Created:** 2026-06-12
- **Applies to:** the `init/` system (rebrand + post-init) and its future
  extraction into the `template-press` engine

> Decision record and implementation plan for extracting the init and
> post-init systems into a reusable engine. This concretizes the
> recommendations of the
> [init/post-init analysis](../research/0003-init-post-init-analysis.md)
> (Part 3), which were reviewed and **accepted** on 2026-06-12. The analysis
> remains the rationale; this document is the contract.

---

# Table of Contents

1. [Decisions taken](#1-decisions-taken)
2. [Naming](#2-naming)
3. [Architecture: one core, two frontends](#3-architecture-one-core-two-frontends)
4. [The `press/` directory contract](#4-the-press-directory-contract)
5. [Config file contracts](#5-config-file-contracts)
6. [CLI surface](#6-cli-surface)
7. [Phasing and migration map](#7-phasing-and-migration-map)
8. [Risks and guardrails](#8-risks-and-guardrails)

---

# 1. Decisions taken

| # | Decision | Choice |
|---|---|---|
| D1 | Post-init architecture | **Hybrid**: decide → derive board → work the board (analysis Part 2B, option 4) |
| D2 | Init architecture | **Unchanged**: working repo + manifest + drift check (analysis Part 2A, option A) |
| D3 | Engine packaging | **One package, two entry points** — not two engine projects (shared kernel: config/marker I/O, plan→apply, prompts, doctor, JSON contract) |
| D4 | Repo end state | **Exactly two repos**: the blueprint (data: manifest, feature defs, tests) and the engine (code). No third shared-lib repo. |
| D5 | Extraction timing | **Extract third, not first** — formalize in place, prove the feature-module interface, then cut the engine out |
| D6 | Frontends | **Core engine + TUI frontend + CLI/JSON frontend**, all three required for post-init; init reuses the CLI frontend |
| D7 | Engine name | **template-press** (see §2; verified free on PyPI and GitHub, 2026-06-12) |
| D8 | Consumer-repo directory | **Visible, tool-named: `press/`** — discoverable by forkers, one association to learn |
| D9 | Feature lifecycle | Four states: `deferred → enabled ⇄ dormant → removed`; `removed` is one-way behind a shown plan + confirm gate |
| D10 | Status semantics | **Computed from reality on every run** (repo files, `gh` API, PyPI API), never merely stored |

# 2. Naming

The print-shop metaphor fits the system exactly: a press takes a fixed
plate, is made ready, runs, and the output is proofed.

| Thing | Name | Notes |
|---|---|---|
| PyPI distribution | `template-press` | Free as of 2026-06-12 (404 on `pypi.org/pypi/template-press/json`); `templatepress` also free. **Reserve early** with a 0.0.1 placeholder once the repo exists. |
| Import package | `template_press` | PEP 8 normalization of the distribution name |
| GitHub repo | `template-press` under the blueprint owner's account | `github.com/template-press` (org/user name) also free as of 2026-06-12 |
| CLI command | `press` | Short, verb-like: `press init`, `press setup`. A legacy `press` distribution exists on PyPI (Rackspace imaging tool); collision only matters if co-installed — ship `tpress` as an alias console script as the escape hatch. |
| Consumer-repo dir | `press/` | See §4 |

Metaphor glossary (for docs, not for CLI verbs — verbs stay plain):

| Print term | System concept |
|---|---|
| Plate | The template repo (the fixed master — this blueprint) |
| Makeready | `press init` — the preparation that turns the plate's output into *yours* |
| Press run | Applying the plan (deterministic; same inputs → same output) |
| Proofing | `press doctor` / checks — verifying the output against the master |
| Presswork | `press setup` — the ongoing work of running the shop (features, services) |

# 3. Architecture: one core, two frontends

Strict three-part layering. Frontends never touch effects directly; the
core is pure (no I/O except through injected adapters).

```
template_press/
├── core/                    # PURE — no direct I/O
│   ├── schema.py            #   manifest + feature/decision-graph models
│   ├── config.py            #   answers.toml / decisions.toml models
│   ├── state.py             #   state.toml (receipt) models
│   ├── plan.py              #   config + state → plan (init: build_plan;
│   │                        #   setup: derive the task board)
│   ├── board.py             #   board derivation, pruning (no → tasks
│   │                        #   never exist), lifecycle state machine
│   └── checks.py            #   check definitions; status computed from
│                            #   adapter results, never stored
├── effects/                 # ADAPTERS — all I/O lives here
│   ├── local.py             #   file edits / moves / deletes (always automatable)
│   ├── remote.py            #   gh API, PyPI API (automatable when authed)
│   └── manual.py            #   errand cards: instruct + poll-verify only
└── frontends/
    ├── tui/                 # HUMAN FACE (post-init)
    │   ├── interview.py     #   first run: linear questions, defaults,
    │   │                    #   "later" always available
    │   ├── dashboard.py     #   every later run: the live board
    │   └── errand.py        #   cards: open URL, pre-computed values,
    │                        #   self-closing verification
    └── cli/                 # AGENT FACE (and init's only face)
        ├── init_cmd.py      #   press init / doctor
        └── setup_cmd.py     #   press setup decide|plan|apply|status|verify
                             #   --json everywhere; exit code = board state
```

```
              ┌────────────── core engine ───────────────┐
              │  schema · config · state · plan · board  │
              │  checks (status computed from reality)   │
              └───────┬──────────────────────┬───────────┘
                      │                      │
               TUI frontend            CLI / JSON frontend
               (human)                 (agent)
               interview, dashboard,   press setup status --json
               errand cards            press setup decide --set codecov=yes
                                       press setup apply  --json
                                       press setup check  (exit code = board)
```

Non-negotiable properties (from the analysis, ranked by value):

1. Every task has a check; status is computed, never stored.
2. Decisions are separate from actions; "no" prunes whole subtrees.
3. `local` / `remote` / `manual` are honestly different action classes.
4. `dormant` ≠ `removed`; destruction only behind a shown plan + confirm.
5. Init stays exactly the compiler it is.

# 4. The `press/` directory contract

What a consumer repo (a project pressed from a template, or the template
itself) contains. Visible on purpose: forkers should see it and know the
machinery is there.

```
press/
├── manifest.toml        # INIT SCHEMA — what to rewrite (replace/rename/
│                        #   remove/reset); ships with the template
├── features/            # SETUP SCHEMA — one file per feature module;
│   ├── publishing.toml  #   each declares decisions (+ relevant_when),
│   ├── codecov.toml     #   actions tagged local/remote/manual, checks,
│   └── readthedocs.toml #   and BOTH directions (enabled + dormant + removed)
├── answers.toml         # INIT CONFIG — identity answers (headless input;
│                        #   optional — the interview generates it)
├── decisions.toml       # SETUP CONFIG — desired feature state (committed;
│                        #   yes/no/later/remove per decision)
└── state.toml           # STATE — the receipt: applied init answers +
                         #   per-feature lifecycle + timestamps
                         #   (replaces init/.blueprint-initialized)
```

Rules:

- **Schema files ship with the template; config files belong to the
  project.** `manifest.toml` + `features/` are template content; the
  engine never writes them. `answers.toml`, `decisions.toml`, `state.toml`
  are project-owned.
- **`press/` is not pruned.** Unlike today's `init/` tree, the directory
  persists after init because the setup board is open-ended. Pruning
  (analog of `init --prune`) removes only template-only content the
  manifest marks as such (e.g. the blueprint's own walkthrough docs).
- Contributor sentinel moves: `init/.blueprint-contributor` →
  `press/.contributor` (git-ignored), same guard-skip semantics.
- Every TOML file carries `meta.schema = <int>`; the schema version is
  the compatibility contract between a template's data and a pinned
  engine version (`uvx template-press@X.Y`).

# 5. Config file contracts

The four-artifact model, per pipe, with concrete homes:

| Artifact | Init | Setup (post-init) |
|---|---|---|
| **Schema** | `press/manifest.toml` | `press/features/*.toml` |
| **Config** | `press/answers.toml` | `press/decisions.toml` |
| **Plan** | ephemeral — `press init --plan` / `--json` (never a committed file) | ephemeral — `press setup plan` / `--json` |
| **State** | `press/state.toml` `[init]` table | `press/state.toml` `[setup.<feature>]` tables |

Sketches (illustrative, to be refined in the spec phase):

```toml
# press/decisions.toml — desired state; "no" prunes sub-decisions
[meta]
schema = 1

[decide]
pypi = "enabled"            # enabled | dormant | deferred | removed
testpypi = "enabled"        # relevant_when: pypi == enabled
release_please = "enabled"  # relevant_when: pypi == enabled
codecov = "deferred"        # zero-cost "ask me later"
readthedocs = "dormant"     # wired but switched off, reversible
funding = "removed"         # one-way; was confirmed at apply time
```

```toml
# press/features/codecov.toml — a feature module (setup schema)
[meta]
schema = 1

[feature]
id = "codecov"
title = "Coverage · Codecov"

[[decision]]
id = "codecov"
question = "Upload coverage to Codecov?"

[[action.enabled]]
kind = "local"              # gate the upload step in ci.yml
[[action.enabled]]
kind = "manual"             # create account, copy token → errand card
url = "https://app.codecov.io/gh/{owner}/{repo}"
[[action.enabled]]
kind = "remote"             # gh secret set CODECOV_TOKEN

[[action.dormant]]
kind = "local"              # comment out / gate the upload step

[[action.removed]]
kind = "local"              # strip upload step, badge, config (confirm gate)

[[check]]
id = "secret-set"
kind = "remote"             # status recomputed from gh API every run
```

```toml
# press/state.toml — the receipt; written only by the engine
[meta]
schema = 1

[init]
applied_at = "2026-06-12T00:00:00Z"
package_name = "my_project"   # ...the applied answers

[setup.pypi]
state = "enabled"
last_verified = "2026-06-12T00:00:00Z"

[setup.funding]
state = "removed"             # sub-decisions permanently not_applicable
```

# 6. CLI surface

```
press init   [--config press/answers.toml] [--plan|--dry-run] [--json]
             [--force] [--allow-dirty] [--commit]
press doctor [--fix] [--json]            # init completeness + env readiness

press setup                              # TUI: interview on first run,
                                         #   dashboard (the board) after
press setup decide  [--set codecov=yes] [--config press/decisions.toml]
press setup plan    [--json]             # derived board diff, no changes
press setup apply   [--json] [--only local,remote]
press setup status  [--json]             # exit code encodes board state
press setup verify                       # re-run checks only, refresh board
```

Agent session shape (the CLI/JSON frontend is the agent mode — same core,
no parallel logic, no TUI scraping):

1. `press setup status --json` → read the board
2. `press setup decide --set ...` → record/confirm decisions
3. `press setup apply --json` → all local + remote tasks run
4. Report the remaining ⚠ manual errands as a short human checklist with
   the pre-computed values inlined.

Exit-code contract (status/check): `0` board all ✓/⊘ · `1` machine tasks
pending · `2` manual errands pending · `3` broken (check failed on a
supposedly-done task).

# 7. Phasing and migration map

The extraction seam — declarative files in, plans out — is what matters;
the repo boundary comes last because it is cheap to add later and
expensive to coordinate prematurely.

**Phase 1 — Formalize post-init in place** (blueprint repo, no extraction)

- Split `init/post_init.py` (804 lines, everything interleaved) into
  schema/generator/engine modules mirroring init's structure.
- Add `--config decisions.toml` headless mode and a real plan stage.
- Add the four-state lifecycle (split today's "no" into `dormant` vs
  `removed`; `removed` behind plan + confirm).
- Exit criterion: an agent can drive post-init end-to-end via config +
  JSON with no TTY.

**Phase 2 — Prove the feature-module interface**

- Define the `features/*.toml` module format (§5) and migrate the three
  existing features onto it: publishing, codecov, readthedocs.
- Absorb 2–3 manual POST_INIT.md items (dependabot, funding, CodeQL) as
  new modules — including at least one exercising the `removed` path —
  to prove the interface generalizes.
- Build the board + checks (status computed from reality) and the TUI
  dashboard/errand cards on top.
- Exit criterion: POST_INIT.md's covered items are board entries, not
  prose; adding a feature touches only `features/` data.

**Phase 3 — Extract the engine**

- Create the `template-press` repo; reserve the PyPI name immediately.
- Move engine code (everything that is not template data) into
  `template_press/` per §3; blueprint keeps only the `press/` data dir.
- Blueprint Justfile recipes become `uvx template-press@<pinned> ...`
  wrappers; `meta.schema` is the compatibility contract.
- The five-mode integration matrix and the manifest-drift CI checks move
  to the engine as its test fixtures **intact** — blueprint CI invokes
  the engine's drift checker. This test suite is the most valuable asset
  in the migration and must not be weakened.

Migration map (current → target, executed during phase 3):

| Today (blueprint) | Target |
|---|---|
| `init/init.py`, `init/_engine.py`, `init/_rewriters.py`, `init/common.py`, `init/discover.py` | engine repo `template_press/core` + `effects` + `frontends/cli` |
| `init/post_init.py` (post phase-1 modules) | engine repo `template_press/core` + `frontends/tui` |
| `init/init_doctor.py` | engine repo (`press doctor`) |
| `init/manifest.toml` | `press/manifest.toml` (stays in blueprint) |
| POST_INIT.md feature knowledge | `press/features/*.toml` (stays in blueprint) |
| `init/.blueprint-initialized` marker | `press/state.toml` |
| `init/.blueprint-contributor` | `press/.contributor` |
| `init/guard.sh` two-tier guard | stays in blueprint (template concern), reads `press/state.toml` |
| `init/tests/` five-mode matrix, `init/ci/` drift checks | engine repo test fixtures; blueprint CI calls the engine |
| `init/init-spec.md`, the [analysis](../research/0003-init-post-init-analysis.md) + this plan | engine repo docs (design history) |

The `init/` → `press/` directory rename happens at the start of phase 3,
together with the `uvx` cutover, so guards/CI/manifest paths are touched
exactly once.

# 8. Risks and guardrails

- **Over-generalizing the engine** before a second consumer template
  exists — the feature-module interface must be exactly as expressive as
  POST_INIT.md's real feature list demands, no more. Guardrail: phase 2's
  exit criterion is met with real features, not hypothetical ones.
- **Drifting toward copier** — a generic manifest-driven repo rewriter
  reinvents copier. The deliberate difference: the blueprint is a
  *working, permanently green repo*, not a Jinja skeleton, and the engine
  must preserve that property. Borrow copier's `copier.yml`
  conditional-question conventions for the decision-graph schema only.
- **Two-repos-too-early** — D5 exists precisely to prevent this; do not
  start phase 3 until phase 2's exit criterion holds.
- **Reconciler purism** — manual errands are first-class (instruct +
  verify), never pretended to be automatable; a human can always answer
  "later" at zero cost.
- **Name squatting risk** — `template-press` is free today (2026-06-12);
  reserve on PyPI as soon as the engine repo is created.
