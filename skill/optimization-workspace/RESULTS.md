# Trigger-optimization results (2026-05-25)

Ran the skill-creator's `run_eval.py` against 3 candidate descriptions
on a 20-query eval set (10 should-trigger, 10 should-not-trigger), 3
runs per query.

## Metrics summary

| Version | Description style | Recall | Specificity | Overall |
|---|---|---:|---:|---:|
| **V1** | Original (informational, "use when…") | 0% (0/10) | 100% (10/10) | 10/20 |
| **V2** | More aggressive ("ALWAYS use", "DO NOT do directly") | ~5% (1/10) | 100% (10/10) | 11/20 |
| **V3** | CRITICAL framing + named failure modes | 0% (0/10) | 100% (10/10) | 10/20 |

V2's "improvement" over V1 is within noise — across runs it sometimes
matches V1's 0% recall exactly.

## What we tried

1. **V1 (original)**: standard "Use this skill when..." with trigger phrases enumerated.
2. **V2**: stronger imperative voice, "DO NOT run gh repo create manually",
   "even simple invocations need this skill".
3. **V3**: started with "CRITICAL:", named 6 specific failure modes the user
   would hit if they tried to bootstrap manually (cryptic auth error, invalid
   package_name, marker corruption, etc.), closed with "USE THIS SKILL — DO
   NOT improvise the bootstrap."

## Why recall is stuck near 0%

Per the skill-creator's own documentation:

> Claude only consults skills for tasks it can't easily handle on its own
> — simple, one-step queries like "read this PDF" may not trigger a skill
> even if the description matches perfectly, because Claude can handle
> them directly with basic tools.

The bootstrap task LOOKS one-step to Claude (it's essentially `gh repo
create --template && cd && just init`). Claude evaluates "do I need help?"
and decides "no, I can run these commands myself." The skill description
doesn't enter the decision once Claude has committed to direct execution.

This is a property of the task class, not the description quality. The
same skill description used for, say, a domain-specific data-extraction
flow would likely trigger fine because Claude wouldn't have a default
approach.

## Why we kept V3 anyway

The description's *secondary* purpose — when the skill does load — is to
remind Claude what the skill actually contains. V3's failure-mode list
is more educational than V1's generic "handles the full bootstrap flow",
so even when triggered via fallback paths (direct invocation, AGENTS.md
pointer), the metadata is more useful.

## Operational recommendation

**Do not rely on auto-triggering for this skill.** The README and
AGENTS.md now document the direct-invocation pattern:

```text
"Follow the runbook in skill/SKILL.md to bootstrap a new project."
```

This always works. Auto-triggering may fire occasionally on multi-step
phrasings (#2 of the should-trigger eval set, which mentioned uv/ruff/
lefthook explicitly, did trigger on 1/3 runs in V2 — suggesting that
when the user signals complexity, the skill fires).

## Optimizer-loop note

The skill-creator's full optimizer (`run_loop.py`) would call the
Anthropic API directly via the `anthropic` Python SDK and iterate
description proposals. It requires `ANTHROPIC_API_KEY`, which isn't set
in this environment (Claude Code uses OAuth, not raw API keys). The
manual 3-iteration loop above substitutes; results suggest the
optimizer would also have plateaued because the constraint is
structural, not phrasing.

## Files

- `trigger_eval.json` — 20-query eval set (10 should-trigger, 10 should-not)
- `eval_v3.json` — full per-query results for V3
- `optimizer.log` — log from the failed `run_loop.py` invocation (shows
  Iteration 1 baseline metrics matching what V1 showed via `run_eval.py`)
