# `new-python-project` — agent skill for bootstrapping new projects

A self-contained skill that guides an AI agent (Claude Code, Codex, or
anything that reads `AGENTS.md`) through creating a new Python project
from the `py-launch-blueprint` template.

Canonical location: `.claude/skills/new-python-project/` (Claude Code's
project-skill discovery path). `.agents/skills/new-python-project` is a
symlink to this directory so Codex discovers it natively too (Codex scans
`$REPO_ROOT/.agents/skills`). Note for Windows checkouts: without git
symlink support the `.agents` entry degrades to a text file — Codex then
won't auto-discover the skill, but the canonical copy still works as a
runbook.

## What's here

| File | Purpose |
|---|---|
| `SKILL.md` | Canonical runbook + YAML frontmatter for Claude's trigger matching |
| `README.md` | This file |

## How agents invoke it

**Claude Code** discovers it as a project skill (it lives in
`.claude/skills/`), so it can be invoked directly as `/new-python-project`
or auto-detected via the YAML frontmatter when the user describes the
intent (e.g., "I want to start a new project from this template").

**Codex** discovers it through the `.agents/skills/new-python-project`
symlink (Codex scans `$REPO_ROOT/.agents/skills`). Other agents that
follow `AGENTS.md` find it via the "Creating a new project from this
template" section in the repo root's `AGENTS.md`, which points here.

**Humans** can read `SKILL.md` directly as a manual runbook — every step
is a copy-pasteable bash block.

## How to use it

The fastest path is to start a fresh Claude Code session, ensure you have
this repo locally, and say something like:

> "I want to create a new Python project from py-launch-blueprint."

…or (per the V6 broader-trigger design):

> "Create a new Python repo for me — it's a CLI for parsing X."

Claude will pick up the skill from `.claude/skills/new-python-project/`
and **first ask** whether you want the full template setup or a minimal
one (Step 0 in the runbook). On confirmation, it walks identity collection
→ `gh repo create --template` → the init rebrand (`init/init.py`) →
optional post-init (`init/post_init.py`). Total time: about
60–90 seconds for the interactive bits, plus whatever the user spends
thinking about the name.

## The "filter-after-trigger" design

V6 of the skill description casts a deliberately wide net — it triggers
on ANY Python project/repo/CLI/script creation intent, not just on
explicit template mentions. The SKILL.md body's **Step 0** then asks the
user whether they want the full template or a minimal setup. If declined,
the skill exits cleanly; if confirmed, the rest of the runbook runs.

This is intentional: rather than try (and fail) to thread a precise
trigger that fires only when the user wants this template specifically,
the skill triggers liberally and uses the conversation itself as the
filter. Costs the user one extra Y/n prompt; gains everyone who would
have otherwise missed the template option entirely.

## When this skill might fail to trigger (and how to force it)

Empirically, this skill **undertriggers reliably** — measured via the
skill-creator's trigger eval (20 queries × 3 runs each; findings in
[`docs/research/0001-skill-trigger-optimization.md`](../../../docs/research/0001-skill-trigger-optimization.md)),
all **six** description versions tested
scored 0% recall on should-trigger queries while keeping 100%
specificity (no false positives). Versions tested:

- V1: original informational
- V2: aggressive "DO NOT do directly"
- V3: CRITICAL framing + named failure modes
- V4: broad Python intent + ask-first framing
- V5: mandatory-prerequisite ("You MUST consult... NEVER bootstrap without")
- V6: "repo" emphasis + ask-first framing (currently shipped)

The root cause is structural, not phrasing: per the skill-creator's own
documentation, *"Claude only consults skills for tasks it can't easily
handle on its own."* The bootstrap task LOOKS simple to Claude even
though it isn't — Claude evaluates "do I need help?" and concludes "I'll
just run `gh repo create` and `git clone` myself," bypassing the skill.
No amount of description-pushing seems to overcome this evaluation.

**The practical workaround is to invoke the skill directly** rather than
relying on auto-triggering:

```text
"Use the new-python-project skill to bootstrap a new Python project.
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
