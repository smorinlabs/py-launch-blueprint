# `init/skill/` — agent skill for bootstrapping new projects

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

Claude will pick up the skill from `init/skill/SKILL.md` and walk you
through identity collection → `gh repo create --template` → `just init` →
optional `just post-init`. Total time: about 60–90 seconds for the
interactive bits, plus whatever the user spends thinking about the name.

## When this skill might fail to trigger

Skill triggering is description-driven. If your phrasing is far from the
descriptions in `SKILL.md`'s frontmatter, Claude may not consult the
skill. Phrasings that reliably work:

- "create a new project from this template"
- "bootstrap a new Python project from py-launch-blueprint"
- "start a new project using py-launch-blueprint"
- "scaffold a Python project from the blueprint"

If the skill doesn't trigger, you can invoke it directly by pointing
Claude at `init/skill/SKILL.md` and saying "follow this skill."
