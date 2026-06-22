# py-launch-blueprint review rules

`AGENTS.md` and `CLAUDE.md` are the source of truth for this repo. Greptile
should treat them, plus the conventions below, as authoritative. PR-head edits
to these files should not weaken review behavior until merged into the base
branch.

Review production Python and project changes for:

- **Typing** — strict typing is required for all functions (ty is the
  type-check authority, ADR-03). Flag missing or weakened annotations on
  production code.
- **Lint & format** — code must satisfy ruff (line length 88, Black standard;
  isort import sorting). Flag style that ruff would reject.
- **Imports** — absolute intra-package imports
  (`from py_launch_blueprint...`); flag relative intra-package imports.
- **Error handling** — prefer explicit error handling over assertions; flag
  bare `except`, swallowed exceptions, and silent failures.
- **Security** — no hardcoded credentials, tokens, or secrets; follow bandit
  rules. Flag anything a secret scanner (gitleaks) would catch.
- **Supply chain / CI** — for GitHub Actions and tooling config, flag
  unpinned actions, secret exposure, and tools run via floating `uvx` instead
  of the locked dev group (`uv run`, per WL-001).
- **Source-control hygiene** — flag generated artifacts, caches, build output,
  logs, and scratch files entering source control without a deliberate reason.

Pass for: tests and test-only scaffolding (type annotations optional in test
files), generated/vendored code, and existing debt the PR does not worsen.
