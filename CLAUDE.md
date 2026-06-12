# CLAUDE.md - Agent Guidelines for Py Launch Blueprint

## Project Commands
- Setup (run BOTH in every fresh clone/container/session):
  1. `uv sync --group dev --extra web` (PEP 735; per ITM-063)
  2. `scripts/install-lefthook.sh` (REQUIRED — wires git hooks; idempotent, safe to re-run)
- Format: `just format` or `uvx ruff format src/py_launch_blueprint/`
- Lint: `just lint` or `uvx ruff check src/py_launch_blueprint/`
- Type check: `just typecheck` or `uv run --extra web ty check src/py_launch_blueprint/` (ITM-026 / ADR-03; ty must be in dev deps; `--extra web` so web/ imports resolve)
- Test all: `just test` or `pytest` (default skips `slow`/`live` markers per ITM-046)
- Test single: `pytest tests/test_file.py::test_name`
- All checks: `just check`
- Web (FastAPI, behind `web` extra): `just serve` dev server; `just test-web` runs tests/web
- Web API conventions (problem+json, /v1, pagination, WEB-xx ids): docs/design/0002-web-api-conventions.md
- After ANY web route change: `just export-openapi` and commit the snapshot (a test + the api-contract workflow enforce it)
- Hooks: lefthook runs at commit/push ONLY after `scripts/install-lefthook.sh` — run it before any commit (see Setup)
- Manual secret scan: `scripts/check-gitleaks.sh --staged` or `--range`

## Before pushing a PR (init-system integrity)
Run `scripts/install-lefthook.sh` (idempotent) so the pre-push hook runs these
automatically. If hooks still aren't active (or to double-check), run them
manually before every push (CI `blueprint-guard` + `init-integration` enforce
them):
- `uv run --script init/ci/check_manifest_drift.py`
- `uv run pytest init/tests/ --override-ini="addopts=" -q`
- Rule behind the drift check: any added/renamed file containing an identity
  value (`py_launch_blueprint`, `py-launch-blueprint`, `plbp`, `PLBP`,
  author/owner names) must be listed in that value's `[[replace]]` block in
  `init/manifest.toml`, or a fork's `just init` ships half-renamed.

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
- Toolchain provisioning (per ADR 0005) — three first-class options, all
  declaring the SAME 10-tool set (python, uv, ruff, taplo, gitleaks, just, bun,
  gh, lefthook, make); keep them in sync when adding/removing a tool:
  1. Native installs (Justfile `install-*` recipes)
  2. `mise install` (root `mise.toml`)
  3. `flox activate` (root `.flox/`)
- Deliberately NOT in `mise.toml`/`.flox`: yamllint, codespell, bandit,
  editorconfig-checker (run via `uvx`) and commitlint (run via
  `bunx --bun @commitlint/cli`) — uv/bun fetch them on demand, and a mise
  `commitlint` shim shadows bun's PATH fallback (see note in lefthook.yml)
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
