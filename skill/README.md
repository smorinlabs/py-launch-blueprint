# `skill/` — agent skill for bootstrapping new projects

A self-contained skill that guides an AI agent (Claude Code, Codex, or
anything that reads `AGENTS.md`) through creating a new Python project
from the `py-launch-blueprint` template.

## What's here

| File | Purpose |
|---|---|
| `SKILL.md` | Canonical runbook + YAML frontmatter for Claude's trigger matching |
| `README.md` | This file |

## How agents invoke it

**Claude Code** auto-detects the skill via the YAML frontmatter when the
user describes the intent (e.g., "I want to start a new project from this
template"). No explicit invocation needed.

**Codex** and other agents that follow `AGENTS.md` discover it via the
"Creating a new project from this template" section in the repo root's
`AGENTS.md`, which points here.

**Humans** can read `SKILL.md` directly as a manual runbook — every step
is a copy-pasteable bash block.

## How to use it

The fastest path is to start a fresh Claude Code session, ensure you have
this repo locally, and say something like:

> "I want to create a new Python project from py-launch-blueprint."

Claude will pick up the skill from `skill/SKILL.md` and walk you
through identity collection → `gh repo create --template` → `just init` →
optional `just post-init`. Total time: about 60–90 seconds for the
interactive bits, plus whatever the user spends thinking about the name.

## When this skill might fail to trigger (and how to force it)

Empirically, this skill **undertriggers reliably** — measured via the
skill-creator's trigger eval (20 queries × 3 runs each, see
`optimization-workspace/`), all three description versions tested (V1
original, V2 more aggressive, V3 with CRITICAL framing + named failure
modes) scored ~0% recall on should-trigger queries while keeping 100%
specificity (no false positives).

The root cause is structural, not phrasing: per the skill-creator's own
documentation, *"Claude only consults skills for tasks it can't easily
handle on its own."* The bootstrap task LOOKS simple to Claude even
though it isn't — Claude evaluates "do I need help?" and concludes "I'll
just run `gh repo create` and `git clone` myself," bypassing the skill.
No amount of description-pushing seems to overcome this evaluation.

**The practical workaround is to invoke the skill directly** rather than
relying on auto-triggering:

```text
"Follow the runbook in skill/SKILL.md to bootstrap a new Python project.
 I want it named X, owner Y, package Z."
```

Or even shorter:

```text
"Use the new-python-project skill — repo name X, owner Y."
```

Direct invocation always works. Auto-triggering is best-effort but not
something to rely on for this skill specifically. The descriptions are
written as if auto-triggering will work because it MIGHT in some
contexts, and the skill body's value is the same either way.

## When this skill is most likely to auto-trigger

When the user's request makes the *multi-step nature* obvious:

- "I need to bootstrap a project AND set up publishing AND configure
  Codecov — can you walk me through it?"
- "Help me start a new project from this template, I haven't done it
  before and I always forget the OIDC step"
- "What's the right order to do the bootstrap from py-launch-blueprint?"

Single-line "create a project named X" rarely triggers — Claude treats
it as a one-shot command.
