# CLAUDE.md - Agent Guidelines for Py Launch Blueprint

## Project Commands
- Setup: `just setup` or `uv sync --group dev` (PEP 735; per ITM-063)
- Format: `just format` or `uvx ruff format py_launch_blueprint/`
- Lint: `just lint` or `uvx ruff check py_launch_blueprint/`
- Type check: `just typecheck` or `uv run ty check py_launch_blueprint/` (ITM-026 / ADR-03; ty must be in dev deps)
- Test all: `just test` or `pytest` (default skips `slow`/`live` markers per ITM-046)
- Test single: `pytest tests/test_file.py::test_name`
- All checks: `just check`
- Hooks: lefthook auto-runs at commit/push (`scripts/install-lefthook.sh` to set up)
- Manual secret scan: `scripts/check-gitleaks.sh --staged` or `--range`

## Code Style Guidelines
- Line length: 88 characters (Black standard)
- Types: Strict typing required for all functions
- Imports: Sorted with relative imports preferred
- Naming: PEP 8 conventions enforced via Ruff
- Errors: Prefer explicit error handling over assertions
- Tests: Type annotations optional for test files
- Security: No hardcoded credentials, follow bandit rules
- Commit messages: Conventional Commits (lowercase subject); commitlint enforces

## Developer Environment
- Python: 3.12+ required (per ITM-033)
- Package manager: `uv` (dev environment), `bun` (commitlint deps; per ADR-04)
- Hook manager: `lefthook` (per ADR-01)
- Build backend: `uv_build` with static `[project] version` (per ADR-06)
- Releases: `release-please` opens version PR; tag triggers OIDC trusted publish (per ADR-05/07)
- IDE: VS Code with Ruff, Pyright, EditorConfig extensions

## Project tracking (plugin: project-harness)

Project state lives in `PROJECTS.md` (trunk) + `projects/` (per-project files).
Route state changes through these skills rather than hand-editing:

- `using-project-harness` — bootstrap / which skill to use
- `project-next` — what's in progress / next / recently touched
- `project-add` — capture an idea (reserves the ID with a commit)
- `project-refine` — scope / decompose a project
- `project-audit` — verify state matches conventions

Planning system: Superpowers (specs under `docs/superpowers/specs/`).
