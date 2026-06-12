# Trigger-optimization results

**Question:** can description wording make the
[`new-python-project`](../../.claude/skills/new-python-project/SKILL.md)
agent skill auto-trigger reliably? (Findings originally lived in the
skill's `optimization-workspace/`; moved here as research.)

Ran the skill-creator's `run_eval.py` against six candidate descriptions
across two distinct strategic axes (description style + scope of trigger
intent). Two eval sets — the first (`trigger_eval.json`) used
template-specific phrasings, the second (`trigger_eval_v2.json` and
`trigger_eval_v3.json`) used broader Python-creation phrasings including
"repo" vocabulary.

## Metrics summary

| Version | Description style + scope | Eval set | Recall | Specificity |
|---|---|---|---:|---:|
| **V1** | Original (informational, template-centric) | v1 | 0/10 | 10/10 |
| **V2** | "ALWAYS use" + "DO NOT do directly" (template-centric) | v1 | ~5% | 10/10 |
| **V3** | CRITICAL framing + named failure modes (template-centric) | v1 | 0/10 | 10/10 |
| **V4** | Broad Python intent + ask-first framing | v2 (Python intent) | 0/10 | 10/10 |
| **V5** | "You MUST consult" + "NEVER bootstrap without this" | v2 (Python intent) | 0/10 | 10/10 |
| **V6** | "repo" emphasis + ask-first framing | v3 (repo + Python intent) | 0/10 | 10/10 |

Every recall result: 0 or near-0. Every specificity result: 100% (no
false-positives).

## What we tried (in order)

1. **V1**: standard "Use this skill when..." with trigger phrases enumerated.
2. **V2**: stronger imperative voice, "DO NOT run gh repo create manually".
3. **V3**: "CRITICAL:", named 6 specific failure modes, "USE THIS SKILL —
   DO NOT improvise the bootstrap."
4. **V4**: pivoted to broader Python-creation intent — trigger on ANY
   Python project/CLI/package/UV-project creation, even without template
   mention. Added "safe to over-trigger because it ASKS THE USER FIRST"
   framing.
5. **V5**: mandatory-prerequisite framing borrowed from system skills
   like `superpowers:brainstorming` — "You MUST consult this skill BEFORE
   creating, starting, scaffolding, bootstrapping, or 'making' ANY new
   Python project... This is NOT optional."
6. **V6**: incorporated "repo" vocabulary (user's intuition: developers
   say "create a Python repo" more naturally than "create a Python
   project"). Front-and-center "repo" + "project" + "CLI/package/script"
   trigger language with the ask-first framing.

## Why recall is structurally pinned at 0%

Per the skill-creator's own documentation:

> Claude only consults skills for tasks it can't easily handle on its own
> — simple, one-step queries like "read this PDF" may not trigger a skill
> even if the description matches perfectly, because Claude can handle
> them directly with basic tools.

The Python project creation task LOOKS one-step to Claude (it's
essentially `gh repo create --template && cd && just init` — or for the
broader-intent versions, even `uv init`). Claude's evaluator decides "do
I need help?" → "no, I can run these commands myself." The skill
description never enters the decision once Claude has committed to
direct execution.

We tested across three axes to confirm this is structural:

| Axis varied | V1 ↔ V3 | V4 ↔ V5 | V4 ↔ V6 |
|---|---|---|---|
| Description tone (info → CRITICAL → MUST) | identical recall | identical recall | n/a |
| Scope (template-only → broad Python intent) | n/a | n/a | n/a |
| Vocabulary ("project" → "project + repo") | n/a | n/a | identical recall |

None of these variations moves recall off zero. The constraint is in
Claude's task-difficulty assessment, not in the description.

## Important caveat about the eval environment

`run_eval.py` uses `claude -p` (Claude's non-interactive CLI mode). This
may have a *different* skill-consultation threshold than the interactive
Claude Code session a real user is in. The 0% recall is "what `claude -p`
decides" — interactive sessions might trigger more readily. The eval can
*underestimate* live triggering, though we have no way to measure
interactive recall systematically.

## Why we shipped V6 anyway

The description's *secondary* purposes — when the skill DOES load via any
path (auto-trigger, direct invocation, AGENTS.md pointer, README) — are
unchanged by the recall ceiling:

- V6 accurately describes the new "filter-after-trigger" behavior (skill
  asks "want the template?" before doing any work)
- V6 uses vocabulary that matches the user's mental model ("repo" and
  "project" both)
- V6's broader trigger list is more useful for human readers scanning the
  skill catalog

Plus, the SKILL.md *body* gained a new Step 0 ("Confirm the user wants
this template") which is invocation-mechanism agnostic. Whether the skill
loads via auto-trigger, direct invocation, or AGENTS.md, the user
*always* gets the safety question before any GitHub or filesystem work
happens.

## Optimizer-loop note

The skill-creator's full optimizer (`run_loop.py`) would iterate
descriptions automatically via the Anthropic API. It requires
`ANTHROPIC_API_KEY`, which isn't set in this environment (Claude Code
uses OAuth, not raw API keys). The manual 6-iteration loop above
substitutes; results across two strategic axes suggest the optimizer
would have plateaued at the same structural ceiling.

The raw eval sets (`trigger_eval*.json`, `eval_v3.json`) and the
`run_loop.py` log were one-off run artifacts and are not kept; the metrics
table above is the durable record, and the chosen trigger wording lives in
`SKILL.md`.
