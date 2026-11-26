# `new-python-project` — bootstrap a project from the blueprint

This skill creates a fresh GitHub repository from `py-launch-blueprint`,
rebrands it, validates the generated Python project, and opens its
initialization pull request. The canonical procedure is [SKILL.md](SKILL.md).

## Location and invocation

The maintained source is `.claude/skills/new-python-project/` in
`py-launch-blueprint`.

- **Project-scoped:** inside a blueprint checkout, Claude Code discovers it at
  `.claude/skills/new-python-project/` and Codex uses the committed
  `.agents/skills/new-python-project` directory symlink. Agents following
  `AGENTS.md` can read the same file as a runbook. On Windows checkouts without
  Git symlink support, use the canonical path directly.
- **User-scoped (global):** because the runbook instantiates directly from
  `smorinlabs/py-launch-blueprint` via `gh repo create --template`, you can
  install it globally and invoke it from any directory without entering a local
  blueprint clone:

  ```bash
  mkdir -p ~/.claude/skills ~/.agents/skills
  ln -s /path/to/py-launch-blueprint/.claude/skills/new-python-project ~/.claude/skills/new-python-project
  ln -s /path/to/py-launch-blueprint/.claude/skills/new-python-project ~/.agents/skills/new-python-project
  ```

For predictable invocation, name the skill and supply the identity you know:

```text
Use the new-python-project skill to create a project from py-launch-blueprint.
Repo: my-project. Owner: my-org. Package: my_project. App: widget.
Use a private repository at /absolute/path/to/my-project.
```

The description still matches broad Python project creation intent. When the
template choice is unresolved, the skill asks whether the user wants the full
blueprint or a minimal setup. An explicit template request or prior approval
settles that choice; the skill does not ask for it again. Declining the
template exits the skill without introducing a separate minimal-setup mode.

Automatic selection varies by agent and context. The
[historical trigger evaluation](../../../docs/research/0001-skill-trigger-optimization.md)
records the earlier experiments; it is not a guarantee of current behavior.

## Bootstrap contract

| Area | Required behavior |
|---|---|
| Python | Python 3.13 or newer; generated project version `0.1.0` |
| Press engine | Released `template-press==4.1.0` from committed `uv.lock`; `uv run --locked press` for every phase |
| Input | Answers file outside the target; the clean-tree guard stays enabled |
| Bun | Target installer and regeneration agree on Bun `1.3.5`; verify it before rebranding |
| Order | Sync tools, check declared commands, preview cleanup, clean, preview rebrand, apply, format the full tree, set up, validate |
| Validation | Setup and project checks, press verification, lock consistency, build, CLI smoke, and actual web health probe |
| Delivery | Initialization branch and pull request with validation evidence |
| Ongoing setup | Generated `docs/PROJECT_SETUP.md` holds external-service and repository decisions |

The template's declared edits reset initial versions before lock regeneration.
Declared resets and removals retire template history and maintenance content.
The runbook checks the resulting receipt and version agreement before commit.

Rebranding removes the generated target's `SKILL.md` and resets this README to
a retirement notice. When running project-scoped from a local blueprint
checkout, keep reading the runbook from that checkout rather than the generated
target; when installed globally, the user-scoped skill remains available
unchanged. The existing Codex directory symlink remains resolvable, but the
generated project no longer exposes this bootstrap skill. Its `docs/POST_INIT.md`
is a short template/provenance pointer.

Full bootstrap authorization covers the necessary local setup and validation.
Package publication, external-service setup, and PR merge remain separate
requested work. The runbook preserves failed checkouts and directs recovery
through engine diagnostics and explicitly reviewed target paths.
