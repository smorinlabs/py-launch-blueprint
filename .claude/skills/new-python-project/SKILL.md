---
name: new-python-project
description: Use when bootstrapping a new Python repo, project, CLI, package, script, or uv project from py-launch-blueprint. Ask whether the user wants the opinionated template bootstrap or a minimal setup before running commands.
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
rebranded, carrying a `press/press-receipt.toml`) and just wants to modify
something — that's `docs/POST_INIT.md` checklist territory, not this
skill.

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

# 3b. bun installed — the press's declared bun.lock regeneration needs it;
# without it the rebrand fails mid-press (regen-bun-lock.sh exits 127).
command -v bun >/dev/null || {
    echo "bun not found. Install: https://bun.sh (required to regenerate bun.lock during the press)"
    exit 1
}

# 4. Not already inside a rebranded project
if [ -f "press/press-receipt.toml" ]; then
    echo "Already inside a rebranded blueprint project. This skill bootstraps a NEW project."
    echo "To reconfigure THIS project, follow docs/POST_INIT.md."
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
| Display name (product name in prose) | `<repo-name>` title-cased, `-` → spaces | non-empty; shown in docs/README prose, so confirm it reads as a product name |

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
  Display name:  <display_name>  (product name in docs/README prose)
  Author:        <author> <<email>>

Proceed? [Y/n]
```

If the user says no, stop. They've spent ~30 seconds answering questions,
and stopping cleanly with no partial state is the right behavior. If yes,
proceed.

### Step 4 — Bootstrap via `gh repo create --template`

`gh repo create` has **no `--directory` flag** (P0004 dogfood PROBLEM-02);
`--clone` always clones into a subdirectory of the current working
directory named after the repo. So run the command from the PARENT of your
target directory:

```bash
cd "$(dirname "<target-dir>")"
gh repo create "<owner>/<repo-name>" \
    --template smorinlabs/py-launch-blueprint \
    --<visibility> \
    --clone
# clone lands at ./<repo-name>; if your target dir name differs, `mv` it.
```

This creates the repo on GitHub, clones it locally, and configures `origin`
correctly. After this completes, the user has a fresh repo with the
blueprint's identity (`py_launch_blueprint`, `py-launch-blueprint`, etc.) —
The press will rebrand it next. Note: template generation is async on GitHub's
side; if the clone is empty or warns, wait a few seconds and retry
`gh repo clone <owner>/<repo-name> <target-dir>`.

`cd` into the new directory before any further steps.

### Step 5 — Write answers.toml from collected identity

Write to `<target-dir>/press-answers.toml` (transient operator input —
do NOT commit it):

```toml
[answers]
package_name = "<package_name>"
repo_name = "<repo_name>"
app_name = "<app_name>"
author = "<author>"
email = "<email>"
owner = "<owner>"
display_name = "<Display Name>"
```

All seven keys are required — the template's source config declares
`display_name`, so the answers must supply the new one (the press refuses
a half-specified display identity).

### Step 6 — Preview the rebrand

Run the press in dry-run mode and show the user the plan summary:

```bash
uvx --from 'template-press>=3.6.0' press rebrand --target . --config press-answers.toml --dry-run --allow-dirty
```

`--allow-dirty` is REQUIRED here: the `press-answers.toml` you just wrote
is an untracked file, which trips the press's clean-tree precondition. It
is safe for `--dry-run` (writes nothing) and for the real apply below (the
only "dirty" file is the config the press itself consumes). The plan lists
every replace/rename, the declared resets/regenerations (CHANGELOG stub,
lockfiles, help snapshots), and the declared removals of blueprint-only
files — that's the user's checkpoint to spot anything unexpected.

Prompt: "Apply these changes? [Y/n]"

On no: stop. The repo exists on GitHub and locally with the blueprint's
identity unchanged — the user can manually rerun or abandon the project.
On yes: continue.

### Step 7 — Apply the rebrand

```bash
uvx --from 'template-press>=3.6.0' press rebrand --target . --config press-answers.toml --allow-dirty
```

Without `--dry-run` this time (`--allow-dirty` still needed for the
untracked `press-answers.toml`). On success the receipt
`press/press-receipt.toml` is written and `press/press-source.toml` is
refreshed to the new identity — verify the receipt exists before
proceeding. Then run the one manual normalization step:

```bash
uv run ruff format .
rm press-answers.toml
```

(Help snapshots regenerate automatically during the press; formatting is
the only post-press normalization left — see `docs/POST_INIT.md`.)

If the press fails, exit 1 leaves the tree rewritten — recover with
`git checkout . && git clean -fd`; exit 2 wrote nothing. Don't try to
recover silently — the user needs to know something failed.

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
✓ Project rebranded at <target-dir>
  Pushed to https://github.com/<owner>/<repo-name>
  Receipt:  press/press-receipt.toml

Next: docs/POST_INIT.md is the decision checklist for publishing
(PyPI/release-please), Codecov uploads, ReadTheDocs, and the app secrets
the maintenance workflows need. Walk it now? [y/N]
```

If yes: open `docs/POST_INIT.md` in the new project and walk its registry
rows one decision at a time. If no: print the deferred-message:

```text
Skipped. When ready: open docs/POST_INIT.md — every post-setup decision
lives there.
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
  mise trust       # mise users only: trust the repo's mise.toml (see below)
  just setup       # Level 2 — dev env sync, git hooks, hook toolchain

Run `make check` first; it tells you exactly what's missing and how to fix it.
```

If you use **mise**, run `mise trust` in the new repo before `just setup`
(P0004 dogfood PROBLEM-08): mise refuses to load an untrusted `mise.toml`
on a fresh clone and `just setup` fails with "Config files in mise.toml
are not trusted." Non-mise users can ignore this.

Do not run `make bootstrap` or `just setup` on the user's behalf — they
modify the user's machine (`~/.local/bin`, git hooks) beyond the project
directory the user asked for.

## Common failure modes and how to handle them

**`gh repo create` says the repo already exists.** The user picked a name
that's already taken in their account. Re-prompt for the repo name and
retry. Don't try to "use the existing repo" — that conflates "fresh
project" with "reset existing project."

**The press fails on a dirty tree without `--allow-dirty`.** Shouldn't
happen — the invocations above carry the flag because step 5's
`press-answers.toml` is untracked. If it fails for a different dirty file,
stop and show the user what is dirty.

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
- Codecov / ReadTheDocs / PyPI publisher setup → `docs/POST_INIT.md`
- Codespaces / Devcontainer customization → manual edit of
  `.devcontainer/`
- Forks (mode #4 in §4.7) → `gh repo fork` then the press invocation manually

## Underlying contract

This skill assumes:

- `smorinlabs/py-launch-blueprint` is a valid GitHub template repository
  (the "Template repository" toggle in repo settings is on)
- The released `template-press` (>= 3.6.0) is reachable via `uvx`, and
  the template commits its press config (`press/press-source.toml` +
  `press/press-rules.toml`) — `just` is NOT required for the bootstrap
- The user's authed gh account has permission to create repos under the
  chosen owner

If any of these change, this skill needs to change with them. The press
contract lives in template-press's design 0006 (external target model)
and its CLI reference.
