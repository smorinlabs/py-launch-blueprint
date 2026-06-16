# Astral Codex Adapter

This plugin exposes Astral's official Python tooling guidance to Codex through
the repo-local marketplace entry at `.agents/plugins/marketplace.json`.

## Contents

- `.codex-plugin/plugin.json` declares the Codex plugin metadata.
- `skills/uv/SKILL.md`, `skills/ruff/SKILL.md`, and `skills/ty/SKILL.md` are
  copied from `astral-sh/claude-code-plugins`.
- `LICENSE-APACHE` and `LICENSE-MIT` are copied from the same upstream repo.

The skill files are copied rather than symlinked because the upstream Astral
repository is not part of this checkout. Do not add duplicate `.agents/skills`
entries for `uv`, `ruff`, or `ty`; keep the skills plugin-scoped.

## Validation

Use the Codex plugin validator and skill validator:

```bash
UV_CACHE_DIR=$PWD/.uv-cache uv run --no-sync python \
  "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" \
  plugins/astral

UV_CACHE_DIR=$PWD/.uv-cache uv run --no-sync python \
  "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" \
  plugins/astral/skills/uv
```

Repeat the skill validation for `ruff` and `ty`.

For the underlying `ty` language server, smoke-test `uvx ty@latest server`
with LSP `initialize` and `shutdown` messages. Claude Code starts that server
through the official Astral plugin; this Codex adapter only provides skills.
