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

Setup is two levels, in order (both idempotent):

```bash
make bootstrap   # Level 1 — base toolchain (just + uv); bare machines only
just setup       # Level 2 — everything else (run every fresh clone/container/session)
```

`just setup` syncs the dev env (`uv sync --group dev --extra web`), wires
lefthook git hooks, and installs the hook toolchain (bun + `bun install`,
gitleaks, taplo, yamlfmt). It starts by running the Makefile's `make check`
gate and fails with a pointer to `make bootstrap` if the base toolchain is
missing — so running it "too early" is safe. The hook wiring is REQUIRED
before any commit/push work: without it none of the hooks below fire. Fresh
clones, containers, and remote agent sessions start without it — run
`just setup` as part of environment setup, every session. (The underlying
`scripts/install-*.sh` installers remain available individually.)

## Canonical commands

| Task | Command |
|---|---|
| Sync dev env | `uv sync --group dev --extra web` (PEP 735 — not `pip install '.[dev]'`) |
| All checks | `just check` |
| Run tests | `pytest` (default excludes `slow`/`live` markers; full: `pytest -m ""`) |
| Lint | `uv run ruff check .` |
| Format check | `uv run ruff format --check .` |
| Typecheck | `uv run --extra web ty check src/py_launch_blueprint/` (ITM-026 / ADR-03) |
| Web tests / dev server | `just test-web` / `just serve` (FastAPI, `web` extra) |
| Secret scan (staged) | `scripts/check-gitleaks.sh --staged` |
| Build | `uv build` (uv_build backend per ADR-06) |

## Verification flow before commit/PR

1. `just setup` (idempotent — REQUIRED in fresh clones/containers so the
   hooks in step 4 actually fire; also refreshes deps).
2. `just check` (full pipeline must pass).
3. Init-system integrity (CI `blueprint-guard` + `init-integration` enforce
   these). If you added/renamed/removed files containing identity values
   (package name, app name, author, owner, repo name), register them in
   `init/manifest.toml` `[[replace]]` blocks, then run:
   - `uv run --script init/ci/check_manifest_drift.py`
   - `uv run pytest init/tests/ --override-ini="addopts=" -q`
4. Stage + commit. Lefthook fires automatically:
   - **commit-msg** → commitlint (Conventional Commits, lowercase subject).
   - **pre-commit** → gitleaks + editorconfig-checker + yamllint + codespell
     + ruff check/format on staged Python files.
   - **pre-push** → gitleaks range scan + bandit + init-system integrity
     (guard wiring, manifest drift, path filter, init tests).

   If lefthook was not installed (step 1 skipped), the hooks are silent
   no-ops — do NOT push until you have either installed it or run the
   step-3 checks manually.

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

## Creating a new project from this template

When the user wants to bootstrap a new Python project from this template
(phrases like *"create a new project from py-launch-blueprint"*, *"start a
new Python project from this template"*, *"scaffold a project from the
blueprint"*), follow the runbook at
[`.claude/skills/new-python-project/SKILL.md`](.claude/skills/new-python-project/SKILL.md).
Claude Code discovers it as the project skill `new-python-project`; Codex
discovers the same directory via the `.agents/skills/new-python-project`
symlink.

It encodes the full sequence: precondition checks (`gh`/`uv`), identity
collection, `gh repo create --template` instantiation, the init rebrand
(`init/init.py`) with a dry-run preview, initial commit + push, and an
optional handoff to post-init (`init/post_init.py`) for publishing/Codecov/
RTD setup — `just` is NOT required for the bootstrap. Auto-triggering is
**unreliable** (empirically 0% recall — agents tend to do the bootstrap
directly and skip the skill); for predictable invocation, tell the agent
explicitly: *"Use the `new-python-project` skill."* For any agent following
this file, the SKILL.md is a direct runbook — every step is a
copy-pasteable shell block.

## For generated projects

If you scaffold from this template and your project's command surface
diverges (extra tools, different test runner, custom hooks), update **this
file first**, then `CLAUDE.md` if you use Claude Code. Vendor-specific
agent configs (`.cursor/`, `.windsurf*`, etc.) inherit from these two.

## Project tracking (plugin: project-harness)

Project state lives in `PROJECTS.md` (trunk) + `projects/` (per-project files).
Route state changes through these skills rather than hand-editing:

- `using-project-harness` — bootstrap / which skill to use
- `project-next` — what's in progress / next / recently touched
- `project-add` — capture an idea (reserves the ID with a commit)
- `project-refine` — scope / decompose a project
- `project-audit` — verify state matches conventions

Planning system: Superpowers (specs under `docs/superpowers/specs/`).
