# AGENTS.md

Vendor-neutral entrypoint for coding agents (Claude Code, Cursor, Codex,
Aider, etc.). For Claude-specific rules see [`CLAUDE.md`](CLAUDE.md); for
human-contributor flow see [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md).

## Required tools

- **Python 3.12+** (per `requires-python = ">=3.12"`; see ITM-033).
- **uv** — Python dependency + venv management.
- **bun** — commitlint runtime (per ADR-04).
- **lefthook** — hook manager (per ADR-01).
- **gitleaks** — secret scanner (per ADR-02).

One-shot install (idempotent):

```bash
scripts/install-bun.sh
scripts/install-lefthook.sh
scripts/install-gitleaks.sh
```

## Canonical commands

| Task | Command |
|---|---|
| Sync dev env | `uv sync --group dev` (PEP 735 — not `pip install '.[dev]'`) |
| All checks | `just check` |
| Run tests | `pytest` (default excludes `slow`/`live` markers; full: `pytest -m ""`) |
| Lint | `uvx ruff check .` |
| Format check | `uvx ruff format --check .` |
| Typecheck | `uvx mypy py_launch_blueprint/` (switching to `uvx ty check` per ADR-03) |
| Secret scan (staged) | `scripts/check-gitleaks.sh --staged` |
| Build | `uv build` (uv_build backend per ADR-06) |

## Verification flow before commit/PR

1. `uv sync --group dev` (refresh deps).
2. `just check` (full pipeline must pass).
3. Stage + commit. Lefthook fires automatically:
   - **commit-msg** → commitlint (Conventional Commits, lowercase subject).
   - **pre-commit** → gitleaks + editorconfig-checker + yamllint + codespell.
   - **pre-push** → gitleaks range scan.

## Commit message format

Conventional Commits with lowercase subject (commitlint enforces):

```
<type>(<optional scope>): <lowercase subject>
```

Allowed types: `feat`, `fix`, `perf`, `refactor`, `revert`, `deps`, `chore`,
`docs`, `style`, `test`, `ci`, `build`.

## Releases

`release-please` opens a release PR on every push to `main`; merging the PR
cuts a `v*` tag; `publish.yml` uploads to TestPyPI then PyPI via OIDC
Trusted Publishing. See [ITM-053..060] for the full chain.

## For generated projects

If you scaffold from this template and your project's command surface
diverges (extra tools, different test runner, custom hooks), update **this
file first**, then `CLAUDE.md` if you use Claude Code. Vendor-specific
agent configs (`.cursor/`, `.windsurf*`, etc.) inherit from these two.
