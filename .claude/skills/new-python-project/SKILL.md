---
name: new-python-project
description: |
  Use this skill WHENEVER the user wants to create a new repo, project,
  package, CLI, script, or UV project that involves Python. Trigger on
  phrasings that include the word "repo" (e.g., "create a Python repo",
  "make a new repo for this CLI", "spin up a fresh python repo", "new
  GitHub repo for a Python tool"), the word "project" (e.g., "create a new
  Python project", "start a fresh Python project"), or the words "CLI" /
  "package" / "script" (e.g., "create a Python CLI", "scaffold a Python
  package"). This skill is the project's bootstrap workflow — it uses
  `gh repo create --template` against py-launch-blueprint, then the init
  rebrand (`init/init.py`), then prompts about post-init. The skill ASKS
  THE USER FIRST
  whether they want this opinionated bootstrap or prefer a minimal setup,
  so it's safe to over-trigger — if the user declines, the skill exits
  cleanly. ALWAYS prefer this skill over running `gh repo create` or
  `uv init` manually for ANY Python repo/project creation intent. Common
  triggers: "create a new Python repo", "make a repo for this Python CLI",
  "scaffold a Python project", "start a new Python project", "I want a
  fresh Python repo", "spin up a python repo for X", "create a UV project".
  When confirmed, handles: precondition checks (gh, uv), identity
  collection (repo name, owner, package, app short name, author/email,
  visibility), `gh repo create --template` from py-launch-blueprint,
  the init rebrand with dry-run preview, initial commit + push,
  optional post-init for publishing/Codecov/RTD.
---

# new-python-project

Bootstrap a fresh Python project from `smorinlabs/py-launch-blueprint`. This
skill orchestrates the entire path from "I want a new project" to "the repo
exists on GitHub, is rebranded with the user's identity, and the initial
commit is pushed" — typically 60–90 seconds end-to-end.

## Why a skill rather than just commands

The bootstrap is small *only after you've done it ten times*. The first
time, a user hits a half-dozen "now what?" moments: gh not authed, package
name not a valid Python identifier, post-init failing because the remote
doesn't exist yet, etc. This skill encodes the right sequence with
preconditions checked at the right time, so each "now what?" becomes a
specific actionable prompt — never a surprise.

## When to invoke vs. when not to

**Invoke when**: the user wants a brand new project derived from this
template. They don't need to say "py-launch-blueprint" explicitly — phrases
like "new Python project from this", "scaffold a project", "start a fresh
project using this template" all qualify.

**Don't invoke when**: the user is *inside* an existing project (already
rebranded with a `.blueprint-initialized` marker) and just wants to modify
something — that's `init/init.py`, `init/post_init.py`, or
`init/init_doctor.py` territory (run via `uv run`), not this skill.

## The runbook

Follow these steps in order. At each step the goal is *user clarity*, not
mechanical execution — explain what's about to happen, especially before
anything that creates resources on GitHub or writes to disk.

### Step 0 — Confirm the user wants this template (filter step)

This skill triggers broadly on any Python project creation intent. Before
doing ANY other work, ask the user whether they want this opinionated
bootstrap. The skill is safe to enter on a wide net of phrasings BECAUSE
it asks before acting — that's the whole filter-after-trigger contract.

Ask exactly one question, with this shape (adapt phrasing to the
conversation; do not invent extra options):

> "I can bootstrap this as a full **py-launch-blueprint** project — uv,
> ruff, lefthook, CI workflows, release-please, OIDC publishing, the whole
> production-quality setup. Or set it up minimally (just `uv init`, no
> opinions). The template adds significant tooling; great for projects
> you'll maintain long-term, overkill for quick throwaway scripts.
>
> **Use the py-launch-blueprint template?** [Y/n]"

- **If yes** → continue to Step 1 (preconditions). The user opted in;
  proceed through the rest of the runbook.
- **If no** → stop this skill cleanly. Confirm: "Got it — I'll set this
  up without the template." Then proceed with whatever simpler approach
  fits (a plain `uv init`, a single script, etc.). Do NOT continue with
  the runbook; the user explicitly declined.
- **If unclear or the user asks for more info** → describe what's in the
  template at one level of detail more than the prompt: "It scaffolds the
  whole repo with uv dependency management, ruff lint+format, lefthook
  git hooks, a Justfile with `just check` / `just test` etc., GitHub
  Actions workflows (CI, security scans, dependency review, codecov),
  release-please for automated version PRs, and OIDC publishing to PyPI.
  All optional via post-init." Then re-ask the Y/n question.

This step is **never skipped**, even when the user's initial prompt
explicitly mentions py-launch-blueprint. The confirmation is cheap (one
question, one keypress) and the cost of bootstrapping the wrong way is
high (a half-rebranded project the user has to manually fix).

### Step 1 — Preconditions

Check all four before asking the user anything. If any fail, stop and tell
the user precisely what's missing and how to fix it; do not proceed.

```bash
# 1. gh CLI installed
command -v gh >/dev/null || {
    echo "gh CLI not found. Install: https://cli.github.com/"
    exit 1
}

# 2. gh authenticated
gh auth status >/dev/null 2>&1 || {
    echo "gh not authenticated. Run: gh auth login"
    exit 1
}

# 3. uv installed
command -v uv >/dev/null || {
    echo "uv not found. Install: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
}

# 4. Not already inside an initialized project
if [ -f "init/.blueprint-initialized" ]; then
    echo "Already inside an initialized blueprint project. This skill bootstraps a NEW project."
    echo "If you want to reconfigure THIS project, use \`uv run init/init_doctor.py\` or \`uv run init/post_init.py\`."
    exit 1
fi
```

The last check matters because GitHub template repos *can* be re-templated
infinitely, but you should never bootstrap inside an active project — the
user almost certainly meant something else.

### Step 2 — Collect identity

Ask the user for each field below in order. Use whatever prompt mechanism
your environment provides (Claude: AskUserQuestion; Codex: equivalent
prompt UI; bare CLI: read from stdin). Show defaults inline and accept
empty input to take the default.

**Validate each answer** as it comes in — re-prompt on invalid input rather
than collecting everything and failing at the end.

| Field | Default | Validation |
|---|---|---|
| GitHub repo name | (none — required) | `^[a-z][a-z0-9-]{0,99}$` (kebab-case, lowercase) |
| GitHub owner | `gh api user --jq .login` | `^[a-z0-9][a-z0-9-]{0,38}$` |
| Visibility | `public` | one of `public` / `private` |
| Target directory | `$PWD/<repo-name>` | must not exist OR be empty |
| Python package name | `<repo-name>` with `-` → `_` | `^[a-z][a-z0-9_]*$` (Python identifier) |
| App short name (CLI command) | `<package_name>` | `^[a-z][a-z0-9_]*$` (Python identifier) |
| Author name | `git config user.name` | non-empty |
| Author email | `git config user.email` | `^[^@\s]+@[^@\s]+\.[^@\s]+$` |

The two name conventions matter and are independent: PyPI distribution
names use kebab-case (`my-project`), Python import names use snake_case
(`my_project`). The app short name is the noun-verb CLI's command and
namespace: it becomes the command itself, the `<APP>_*` env-var prefix
(uppercased), and the XDG dir/file names
(`~/.config/<app>/<app>_config.toml`) — which is why it must be
identifier-safe (no hyphens).

### Step 3 — Show what's about to happen

Before any GitHub or filesystem mutation, summarize the plan:

```text
About to create:
  GitHub repo:   <owner>/<repo-name>  (<visibility>)
  Local clone:   <target-dir>
  Package name:  <package_name>
  App name:      <app_name>  (CLI command + <APP_NAME>_* env prefix)
  Author:        <author> <<email>>

Proceed? [Y/n]
```

If the user says no, stop. They've spent ~30 seconds answering questions,
and stopping cleanly with no partial state is the right behavior. If yes,
proceed.

### Step 4 — Bootstrap via `gh repo create --template`

```bash
gh repo create "<owner>/<repo-name>" \
    --template smorinlabs/py-launch-blueprint \
    --<visibility> \
    --clone \
    --directory "<target-dir>"
```

This single command creates the repo on GitHub, clones it locally to the
chosen directory, and configures `origin` correctly. After this completes,
the user has a fresh repo with the blueprint's identity (`py_launch_blueprint`,
`py-launch-blueprint`, etc.) — `init` will rebrand it next.

`cd` into the new directory before any further steps.

### Step 5 — Write answers.toml from collected identity

Write to `<target-dir>/answers.toml`. The schema matches
`init/tests/integration/answers.toml`:

```toml
[answers]
package_name = "<package_name>"
repo_name = "<repo_name>"
app_name = "<app_name>"
author = "<author>"
email = "<email>"
owner = "<owner>"
```

All six keys are required. The init engine will use these to compute the
replace/rename operations.

### Step 6 — Preview the rebrand

Run init in dry-run mode and show the user the plan summary:

```bash
uv run init/init.py --config answers.toml --dry-run --yes
```

This prints the full list of replaces/renames/removes without writing
anything. The summary at the end will look like `Summary: 2 removes, 97
replaces, 5 renames.` — that's the user's checkpoint to spot anything
unexpected (e.g., a name that didn't substitute correctly).

Prompt: "Apply these changes? [Y/n]"

On no: stop. The repo exists on GitHub and locally with the blueprint's
identity unchanged — the user can manually rerun or abandon the project.
On yes: continue.

### Step 7 — Apply the rebrand

```bash
uv run init/init.py --config answers.toml --yes
```

Without `--dry-run` this time. The marker `init/.blueprint-initialized` is
written on success — verify it exists before proceeding.

If init fails for any reason, the message will instruct the user to recover
with `git checkout . && git clean -fd`. Don't try to recover silently — the
user needs to know something failed.

### Step 8 — Initial commit and push

```bash
git add -A
git commit -m "chore: initialize <repo-name> from py-launch-blueprint"
git push -u origin main
```

`origin` is already set correctly by `gh repo create --template`, so the
push goes to the new repo. The `-u` sets upstream tracking.

### Step 9 — Prompt about post-init (do not auto-chain)

Tell the user what just happened, then offer post-init:

```text
✓ Project initialized at <target-dir>
  Pushed to https://github.com/<owner>/<repo-name>
  Marker:   init/.blueprint-initialized

Next: post-init configures publishing (PyPI/release-please), Codecov uploads,
and ReadTheDocs. It can run now (the GitHub repo exists, so the full flow
works) or later via `uv run init/post_init.py`.

Run post-init now? [y/N]
```

If yes: `cd <target-dir> && uv run init/post_init.py` — hand control to the
post-init interactive flow. If no: print the deferred-message:

```text
Skipped. When ready:
  cd <target-dir>
  uv run init/post_init.py
```

The default is "no" because the user has just completed a multi-step flow
and may want to commit, look at the diff, or take a break before tackling
another decision tree.

### Step 10 — Recommend the dev-toolchain setup (do NOT run it)

This skill only needs `gh` and `uv`. The generated project's day-to-day
workflow additionally uses `just` (task runner) and the lefthook git hooks
— but installing toolchains on the user's machine is the user's call, not
this skill's. Recommend, don't execute:

```text
Your project works with gh + uv alone, but the full dev workflow uses just.
Inside <target-dir>:

  make check       # report which base tools are present/missing
  make install-just  # PRINT the just install command (runs nothing)
  make bootstrap   # install just + uv if missing (Level 1 setup)
  just setup       # Level 2 — dev env sync, git hooks, hook toolchain

Run `make check` first; it tells you exactly what's missing and how to fix it.
```

Do not run `make bootstrap` or `just setup` on the user's behalf — they
modify the user's machine (`~/.local/bin`, git hooks) beyond the project
directory the user asked for.

## Common failure modes and how to handle them

**`gh repo create` says the repo already exists.** The user picked a name
that's already taken in their account. Re-prompt for the repo name and
retry. Don't try to "use the existing repo" — that conflates "fresh
project" with "reset existing project."

**`uv run init/init.py` fails on a dirty tree.** Shouldn't happen — fresh
clone is clean. If it does, the cause is almost certainly that step 5
(`answers.toml`) is being detected as dirty. Add `--allow-dirty` to the
init invocation, but also flag this as a bug worth investigating.

**`git push` fails because the user doesn't have push access to the org.**
Catch the error and tell the user explicitly — they may have picked an org
they're not a member of. Don't retry; have them pick a different owner.

**User aborts at step 3 (plan confirmation) or step 6 (rebrand
confirmation).** Leave everything as-is. The user can rerun this skill or
manually continue. Do not delete the GitHub repo — that's destructive and
usually wrong.

## What this skill does NOT do

Be explicit about boundaries — these are out of scope and should be
deferred to other tools/skills:

- Branch protection setup → manual `gh api ...branches/main/protection` or
  a future `just protect-main` recipe
- License changes (blueprint ships MIT) → manual `LICENSE` edit
- Codecov / ReadTheDocs / PyPI publisher setup → `uv run init/post_init.py`
- Codespaces / Devcontainer customization → manual edit of
  `.devcontainer/`
- Forks (mode #4 in §4.7) → `gh repo fork` then `uv run init/init.py` manually

## Underlying contract

This skill assumes:

- `smorinlabs/py-launch-blueprint` is a valid GitHub template repository
  (the "Template repository" toggle in repo settings is on)
- The local clone has `init/init.py`, `init/init_doctor.py`, and
  `init/post_init.py`, runnable via `uv run` (the `Justfile` recipes
  `init`, `init-doctor`, `post-init` are thin wrappers over these — `just`
  is NOT required for the bootstrap)
- The user's authed gh account has permission to create repos under the
  chosen owner

If any of these change, this skill needs to change with them. See
`init/init-spec.md` §4.7 for the authoritative list of instantiation
modes the blueprint supports.
