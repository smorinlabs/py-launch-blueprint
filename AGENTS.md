# AGENTS.md

Canonical guidance for ALL coding agents (Claude Code, Cursor, Codex,
Windsurf, Aider, etc.) — this is the single file to edit.
[`CLAUDE.md`](CLAUDE.md) imports it verbatim (`@AGENTS.md`); Cursor,
Windsurf, and Codex read this file natively. For human-contributor flow see
[`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md).

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
| Run tests | `pytest` (default excludes `slow`/`live` markers per ITM-046; full: `pytest -m ""`; parallel: add `-n auto`) |
| Run one test | `pytest tests/test_file.py::test_name` |
| Lint | `uv run ruff check .` |
| Format | `just format` or `uv run ruff format src/py_launch_blueprint/` |
| Format check | `uv run ruff format --check .` |
| Typecheck | `uv run --extra web ty check src/py_launch_blueprint/` (ITM-026 / ADR-03; `--extra web` so web/ imports resolve) |
| Dependency CVE audit | `just audit` (WL-014; same pipeline as the weekly CI workflow) |
| Web tests / dev server | `just test-web` / `just serve` (FastAPI, `web` extra) |
| Secret scan | `scripts/check-gitleaks.sh --staged` or `--range` |
| Build | `uv build` (uv_build backend per ADR-06) |

Hook/CI tools run from the locked dev group (`uv run`, never floating
`uvx`) per WL-001 — versions come from `uv.lock`.

Web API conventions (problem+json, `/v1`, pagination, WEB-xx ids):
`docs/design/0002-web-api-conventions.md`. After ANY web route change:
`just export-openapi` and commit the snapshot (a test + the api-contract
workflow enforce it).

## Verification flow before commit/PR

1. `just setup` (idempotent — REQUIRED in fresh clones/containers so the
   hooks in step 4 actually fire; also refreshes deps).
2. `just check` (full pipeline must pass).
3. Init-system integrity (CI `blueprint-guard` + `init-integration` enforce
   these). Rule behind the drift check: any added/renamed file containing an
   identity value (`py_launch_blueprint`, `py-launch-blueprint`, `plbp`,
   `PLBP`, author/owner names) must be listed in that value's `[[replace]]`
   block in `init/manifest.toml`, or a fork's `just init` ships
   half-renamed. Then run:
   - `uv run --script init/ci/check_manifest_drift.py`
   - `uv run pytest init/tests/ --override-ini="addopts=" -q`
4. Stage + commit. Lefthook fires automatically:
   - **commit-msg** → commitlint (Conventional Commits, lowercase subject).
   - **pre-commit** (fast, staged-scoped) → gitleaks + editorconfig-checker
     + yamllint + actionlint (workflows) + codespell + ruff check/format
     + taplo (TOML) + `uv lock --check` (lockfile freshness) + large-files
     guard (1 MB).
   - **pre-push** (slower, full-tree) → gitleaks range scan + bandit + ty
     typecheck + import-linter + tach + openapi-snapshot (web-layer gated)
     + init-system integrity (guard wiring, manifest drift, path filter,
     init tests).

   Hooks mirror CI; CI is the authority (ADR 0018). Boundaries (import-linter
   + tach) are gated by the `import-boundaries` CI job, so a `--no-verify`
   push can't bypass them.

   If lefthook was not installed (step 1 skipped), the hooks are silent
   no-ops — do NOT push until you have either installed it or run the
   step-3 checks manually.

## Pull request review comments — MERGE GUARD (hard, enforced)

**This is a hard gate, not a guideline.** This repo has an active ruleset
("CodeQL & PR Enforcement") with `required_review_thread_resolution: true`, so
**a PR with ANY unresolved review thread CANNOT be merged — GitHub blocks it.**
A PR will sit silently `blocked` on a single dangling bot thread. (Do not be
misled by classic branch protection reporting
`required_conversation_resolution: false` — the *ruleset* is the real enforcer;
verify with `gh api "repos/<owner>/<repo>/rulesets"`.)

Because of this guard, treat review comments as blocking work that must be kept
current **before opening a PR and continuously while it is open** — bots
(Copilot, CodeRabbit, Codex, Greptile, …) re-review on every push and add fresh
threads, so a PR that was clean can become blocked again after a commit.

For **every** review comment (human or bot), do all three steps — never skip to
merge:

1. **Pre-validate** it against the actual code/docs — decide valid or invalid.
   Do not take a comment (especially a bot's) at face value; confirm it.
2. **Reply** with a comment recording the verdict and the action taken:
   - valid → fix the underlying issue *in the PR*, then reply noting the fix;
   - invalid or intentional → reply with the concrete rationale.
3. **Resolve** the thread — always, after step 2. Resolving requires the GraphQL
   `resolveReviewThread` mutation; there is no REST equivalent, so a GraphQL
   rate-limit (common on some machines) can block *resolution* even when the PR
   is otherwise green. Plan for that; do not merge around it.

Only purely informational bot comments (e.g. the dependency-review ✅ summary)
need no action. Never merge — and never assume a PR is mergeable — while any
actionable thread is unresolved.

## Commit message format

Conventional Commits with lowercase subject (commitlint enforces):

```
<type>(<optional scope>): <lowercase subject>
```

Allowed types: `feat`, `fix`, `perf`, `refactor`, `revert`, `deps`, `chore`,
`docs`, `style`, `test`, `ci`, `build`.

This format is REQUIRED for **every** commit — no exceptions for bot or
autofix commits (e.g. Copilot's "Potential fix…"). The required
`commitlint (humans)` CI check lints every non-merge commit in a PR, so a
single non-conventional commit blocks the merge; reword it before merging.
This matters more under merge commits than it did under squash: the branch's
individual commits land on the trunk, and release-please parses *those* —
not the PR title. The merge commit's own subject is left deliberately
non-conventional (`merge_commit_title=MERGE_MESSAGE`, i.e.
`Merge pull request #N from …`) precisely so release-please skips it and counts each
change exactly once. Conventional PR titles are still expected for review
legibility; they are simply not what the changelog is built from.

## Code style

- Line length: 88 characters (Black standard)
- Types: strict typing required for all functions
- Imports: sorted (ruff isort); absolute intra-package imports
  (`from py_launch_blueprint…` — the codebase convention)
- Naming: PEP 8 conventions enforced via Ruff
- Errors: prefer explicit error handling over assertions
- Tests: type annotations optional for test files
- Security: no hardcoded credentials, follow bandit rules

## Typing conventions

`ty` (type correctness) + ruff `ANN` (annotation presence) enforce the
mechanical rules in CI/hooks — the durable guardrails; `ty` deliberately does
not flag missing annotations, so `ANN` owns that half. The judgment calls below
are what tooling can't check:

- **Validate at the boundary, narrow inward.** External data (HTTP/JSON, TOML,
  env, untrusted input) arrives as `Any`/`dict[str, Any]`; validate it once at
  the edge (Pydantic model / `TypeIs`) and pass *precise* types in. Never let
  boundary `Any` leak into `core/`.
- **Boundary `Any` is fine; a function that *returns* `Any` into the core/CLI
  is a bug** — give it a real return type.
- **Encode closed domains** as `Literal`/`StrEnum`, not `str` (a comment
  listing the allowed values IS the type — write it as one).
- **`@override` every nominal override** (PEP 698) so a renamed base method
  fails the check instead of silently degrading.
- **Precise over general, without over-churn:** `ParamSpec` for pass-through
  decorators, parameterized generics over bare `dict`/`list`; a
  signature-changing decorator may legitimately keep a `cast`.

Deep-dive + rationale: [`projects/P03-type-precision-uplevel.md`](projects/P03-type-precision-uplevel.md).

## Developer environment

- Toolchain provisioning (per ADR 0005, extended by ADR 0018) — three
  first-class options, all declaring the SAME 11-tool set (python, uv, ruff,
  taplo, gitleaks, just, bun, gh, lefthook, make, actionlint); keep them in
  sync when adding/removing a tool:
  1. Native installs (Makefile + Justfile `install-*` targets,
     `scripts/install-*.sh`)
  2. `mise install` (root `mise.toml`)
  3. `flox activate` (root `.flox/`)
- Deliberately NOT in `mise.toml`/`.flox`: yamllint, codespell, bandit,
  editorconfig-checker (run via `uv run` from the locked dev group, per WL-001)
  and commitlint (run as `./node_modules/.bin/commitlint`) — `uv sync`/bun
  provide them, and bun.lock stays the single version source (see note in
  lefthook.yml)
- Build backend: `uv_build` with static `[project] version` (per ADR-06)
- IDE: VS Code with Ruff, Pyright, EditorConfig extensions

### Astral Python tools for Claude Code and Codex

Python code intelligence for Claude Code comes from the **official Astral
plugin** (`astral@astral-sh`), enabled by default for this repo in
`.claude/settings.json` (which also registers the `astral-sh` marketplace,
`github.com/astral-sh/claude-code-plugins`). The plugin ships a `ty` language
server (`uvx ty@latest server`) plus `/astral:` skills for uv, ty, and ruff.

Codex does not have an official Astral plugin marketplace entry. This repo
therefore carries a repo-local Codex adapter:
`.agents/plugins/marketplace.json` registers `astral@py-launch-blueprint`
from `plugins/astral` with `INSTALLED_BY_DEFAULT`. The adapter is skill-only:
it vendors Astral's upstream `uv`, `ruff`, and `ty` `SKILL.md` files plus the
upstream license files. Do not add duplicate `.agents/skills/uv`,
`.agents/skills/ruff`, or `.agents/skills/ty` entries; keep those skills
plugin-scoped so Codex has one source of truth.

`ty` is this repo's type-check authority (ADR-03), so its LSP diagnostics —
which the plugin leaves **on** by default — agree with what CI gates on rather
than introducing a second, divergent type-checker voice. No separate binary
install is needed: `uvx` is provided by `uv`, already in the toolchain.

Activation: collaborators are prompted to install from the `astral-sh`
marketplace after they accept the workspace-trust dialog; the LSP server starts
only once the workspace is trusted. Run `/reload-plugins` (or restart) to pick
it up in an existing session.

Note: the LSP runs `ty@latest` via `uvx`, which can drift from the `ty` version
pinned in the dev group that CI uses (`uv run ty`); treat CI as authoritative.

When validating the LSP outside Claude Code, smoke-test the same server command
with JSON-RPC `initialize`/`shutdown` against `uvx ty@latest server`.

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
file** — it is the single source of truth. `CLAUDE.md` imports it; add
Claude-specific notes there only. Vendor-specific rule files (`.cursor/`,
`.windsurf*`) are deliberately absent: Cursor, Windsurf, and Codex all read
`AGENTS.md` directly.

## Project tracking (plugin: project-harness)

Project state lives in `PROJECTS.md` (trunk) + `projects/` (per-project files).
Route state changes through these skills rather than hand-editing:

- `using-project-harness` — bootstrap / which skill to use
- `project-next` — what's in progress / next / recently touched
- `project-add` — capture an idea (reserves the ID with a commit)
- `project-refine` — scope / decompose a project
- `project-audit` — verify state matches conventions

Planning system: Superpowers (specs under `docs/superpowers/specs/`).
