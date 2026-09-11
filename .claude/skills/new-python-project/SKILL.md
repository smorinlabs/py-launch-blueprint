---
name: new-python-project
description: Use when bootstrapping a new Python repo, project, CLI, package, script, or uv project from py-launch-blueprint. Ask whether the user wants the opinionated template bootstrap or a minimal setup before running commands.
---

# new-python-project

Create a fresh Python project from `smorinlabs/py-launch-blueprint`, validate
its CLI and web application, and deliver the initialization as a pull request.
The generated project starts at version `0.1.0` and requires Python 3.13+.

Use this runbook from the **original blueprint checkout** throughout the
bootstrap. Rebranding removes the generated copy of `SKILL.md` and retires its
companion documentation. The generated project's ongoing setup checklist is
`docs/PROJECT_SETUP.md`; `docs/POST_INIT.md` is a template/provenance pointer.

## Scope and authorization

Use this skill for a new project derived from the blueprint. An existing
project with `press/press-receipt.toml`, the record of a completed rebrand, is
not a fresh bootstrap target.

If the user has already selected the blueprint or approved this bootstrap,
continue without asking them to choose it again. For a generic Python project
request where that choice is unresolved, ask whether they want the blueprint's
full toolchain or a minimal setup. If they decline the template, leave this
skill and follow their chosen approach.

Resolve the GitHub owner, repository name, visibility, and target directory
before creating resources. Summarize the identity, local setup, and intended
initialization pull request. Ask for approval only if those actions are not
already authorized. An approved full bootstrap includes the preview, declared
cleanup, rebrand, local toolchain setup, validation, and initialization PR.
Publishing packages, merging the PR, and configuring external services require
their own requested scope.

## Runbook

Run commands from the stated directory and stop at a failed command. Replace
angle-bracket placeholders with the collected values. The shell examples use
Bash; keep the `bootstrap_*` variables available between steps. Record their
resolved values when the execution tool starts a separate shell for each call.

### 1. Check prerequisites and collect missing identity

From the original blueprint checkout, verify the command-line tools and GitHub
login before creating the new repository:

```bash
command -v git
command -v gh
command -v uv
command -v bash
command -v make
gh auth status
```

Resolve missing tools or interactive authentication before resource creation.
The complete bootstrap also runs the target's `make bootstrap` when needed
and `just setup`; dependency installation and Git hook wiring are part of the
validated result.

Reuse identity values the user already supplied. Collect only missing fields,
show derived defaults, and validate the answers before creating the repository.

| Field | Default | Validation |
|---|---|---|
| GitHub repo name | Required | Lowercase kebab-case: `^[a-z][a-z0-9-]{0,99}$` |
| GitHub owner | `gh api user --jq .login` | Existing account or organization the user can create repositories under |
| Visibility | `public` | `public` or `private`; resolve before creating the repository |
| Target directory | A sibling of the blueprint checkout named after the repo | Absolute path; absent or empty; outside the source checkout |
| Python package name | Repo name with `-` changed to `_` | `^[a-z][a-z0-9_]*$`; not a Python keyword |
| App short name | Python package name | `^[a-z][a-z0-9_]*$`; not a Python keyword |
| Author name | `git config user.name` | Non-empty |
| Author email | `git config user.email` | Valid email address |
| Display name | Repo name with hyphens changed to spaces and words title-cased | Non-empty product name for README and documentation prose |

The repo name is also the Python distribution name, such as `my-project`.
The package name is its import name, such as `my_project`. The app short name
becomes the CLI command, uppercase environment-variable prefix, and XDG
configuration names. For example, `widget` produces the command `widget` and
the environment-variable prefix `WIDGET_`.

### 2. Instantiate the GitHub template and create a working branch

Use a real GitHub template instantiation so `origin` identifies the new
repository. Create and clone separately to support the exact target directory;
`gh repo create` does not have a `--directory` option.

```bash
gh repo create "<owner>/<repo-name>" \
    --template smorinlabs/py-launch-blueprint \
    --<visibility>
gh repo clone "<owner>/<repo-name>" "<target-dir>"
cd "<target-dir>"
git rev-parse --verify HEAD
git remote get-url origin
git status --short
bootstrap_base_branch="$(git branch --show-current)"
git switch -c chore/initialize-project
```

Require a populated, clean clone with `origin` pointing to the selected
repository and no existing receipt. If GitHub has not finished generating the
template, wait for its initial commit and complete the clone before continuing.
Do not recreate the remote or delete an existing directory to retry.

### 3. Keep operator input outside the target

From `<target-dir>`, allocate a separate directory for answers and validation
notes. This keeps operator input out of Git's clean-tree check.

```bash
bootstrap_operator_dir="$(mktemp -d "${TMPDIR:-/tmp}/blueprint-bootstrap.XXXXXX")"
bootstrap_answers="$bootstrap_operator_dir/press-answers.toml"
```

Write the following TOML to the exact path in `$bootstrap_answers`, using the
collected identity and valid TOML string escaping:

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

Supply all seven keys: the blueprint declares a display name, so its new
identity must supply one too. Keep this file outside the target through the
receipt check in step 6. It is operator input, not a project artifact.

### 4. Install and check the locked press engine and Bun

All remaining commands run from `<target-dir>`. Sync the committed lockfile
and use its released `template-press==4.1.0` throughout this runbook:

```bash
uv sync --locked --group dev --extra web
uv run --locked python --version
test "$(uv run --locked python -c 'from importlib.metadata import version; print(version("template-press"))')" = "4.1.0"
```

Require Python 3.13 or newer. If the lockfile is stale or the expected engine
is unavailable, resolve that failure before rebranding. Do not substitute a
floating `uvx` invocation or a different press checkout for one of the phases.

Install the target's pinned Bun, the JavaScript runtime used to regenerate
`bun.lock`, and verify the executable that regeneration will see:

```bash
export PATH="$HOME/.local/bin:$HOME/.bun/bin:${CARGO_HOME:-$HOME/.cargo}/bin:$PATH"
scripts/install-bun.sh
test "$(bun --version)" = "1.3.5"
uv run --locked press check-tools --target .
git status --short
```

`press check-tools` resolves the declared command entry points without running
them. It cannot establish the version of Bun called inside a script; the
explicit Bun check must pass before regeneration. The working tree must still
be clean. If mise blocks an untrusted configuration, inspect the new target's
`mise.toml` and resolve trust before running its tools.

### 5. Preview cleanup, clean, preview rebrand, then apply

Imports during environment setup can create ignored bytecode directories
inside source-package paths that the rebrand must rename. Use the target's
`[[clean]]` declarations, which select the permitted cleanup paths:

```bash
uv run --locked press clean --target . --show
```

Review and report the listed paths, then execute the declared cleanup:

```bash
uv run --locked press clean --target .
uv run --locked press rebrand --target . \
    --config "$bootstrap_answers" --dry-run
```

Inspect the dry-run plan. It should cover the new identity, initial-version
edits, reset documentation and history, removal of template-only material,
and regeneration of lockfiles and CLI help snapshots. `--allow-dirty` is not
needed because the answers file is outside the target.

Show the plan summary and continue within the approved bootstrap scope. Pause
only for unexpected changes that need a new decision. The preview does not
run declared edit or regeneration commands; their successful execution is
part of the apply and validation gates.

```bash
uv run --locked press rebrand --target . --config "$bootstrap_answers"
test -f press/press-receipt.toml
```

Keep the cleanup outcome with the run's evidence. A `[[press.clean]]` receipt
row records a declaration, not proof that cleanup ran. A successful rebrand
writes the receipt and refreshes `press/press-source.toml` to the new identity.
Continue reading the runbook in the original blueprint checkout after this
step; its generated `SKILL.md` has been removed.

### 6. Normalize, set up, and validate the generated project

Format the **full tree** because longer identity values can affect tests as
well as package code. `just format` covers only the package directory.

```bash
uv run --locked ruff format .
make check
```

If `make check` reports missing base tools, run the target's `make bootstrap`
and repeat the check. Then complete the required setup and resync the locked
environment for the new package identity:

```bash
just setup
uv sync --locked --group dev --extra web
```

Review `git status --short` and `git diff` against the preview. Stage the
reviewed generated changes so Git-backed checks see the new paths. Investigate
unexpected changes before staging.

```bash
git add -A
git diff --cached --check
just check
uv run --locked press verify --target .
uv lock --check
uv build
uv run --locked <app_name> --help
uv run --locked <app_name> --version
```

Require every command to pass. `press verify` checks identity conformance in
an isolated copy; it does not run declared commands and reports its exempt
outputs. The real apply and generated-project checks supply that additional
evidence. The CLI must show the selected app name and version `0.1.0`.

Check that the receipt matches the answers, and that project metadata,
release state, the editable lock entry, and installed runtime all start at
`0.1.0`:

```bash
uv run --locked python - "$bootstrap_answers" <<'PY'
import importlib
import json
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path


def read_toml(path):
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


project = read_toml("pyproject.toml")["project"]
answers = read_toml(sys.argv[1])["answers"]
receipt = read_toml("press/press-receipt.toml")["press"]
editable = [
    package for package in read_toml("uv.lock")["package"]
    if package.get("source") == {"editable": "."}
]
if len(editable) != 1:
    raise SystemExit("Expected one editable project entry in uv.lock")
versions = {
    "pyproject.toml": project["version"],
    "release manifest": json.loads(Path(".release-please-manifest.json").read_text())["."],
    "uv.lock": editable[0]["version"],
    "installed metadata": version(project["name"]),
    "runtime": importlib.import_module(answers["package_name"]).__version__,
}
if any(value != "0.1.0" for value in versions.values()):
    raise SystemExit(f"Initial version mismatch: {versions}")
if receipt.get("verified") is not True or any(
    receipt.get("to", {}).get(key) != value for key, value in answers.items()
):
    raise SystemExit("Receipt does not certify the requested identity")
print("PASS: receipt identity and initial 0.1.0 versions agree")
PY
```

Smoke-test the actual web entry point. In `<target-dir>`, start the server:

```bash
uv run --locked --extra web uvicorn <package_name>.web.app:create_app \
    --factory --host 127.0.0.1 --port 8000 --timeout-graceful-shutdown 5
```

Wait for `Application startup complete.` and the listening address
`http://127.0.0.1:8000`. This command stays running. From another shell in the
same `<target-dir>`, check its health response:

```bash
uv run --locked python - <<'PY'
import json
from urllib.request import urlopen

with urlopen("http://127.0.0.1:8000/healthz", timeout=5) as response:
    health = json.load(response)
if health.get("status") != "ok" or health.get("version") != "0.1.0":
    raise SystemExit(f"Unexpected health response: {health}")
print("PASS: web health reports ok and version 0.1.0")
PY
```

Use a different free local port in both commands if `8000` is occupied. Stop
this server with Ctrl+C after the probe and confirm it exits. Build artifacts
must include a wheel and source distribution for the new project at `0.1.0`.

### 7. Commit the validated initialization and open its PR

After the checks pass, inspect the final changes and stage any reviewed
normalization outputs. Keep the answers and logs outside the repository.

```bash
git add -A
git diff --cached --check
git commit -m "chore: initialize <repo-name> from py-launch-blueprint"
git push -u origin chore/initialize-project
```

Write a PR body to `$bootstrap_operator_dir/initialization-pr.md` describing
the generated identity, initial version, completed checks, and deferred
external-service setup. Use actual results, including any reported verification
exemptions. Then create the PR against the branch recorded before rebranding:

```bash
gh pr create --repo "<owner>/<repo-name>" \
    --base "$bootstrap_base_branch" --head chore/initialize-project \
    --title "chore: initialize <repo-name>" \
    --body-file "$bootstrap_operator_dir/initialization-pr.md"
```

Report the target path, PR URL, receipt path, and validation result. Distinguish
local checks from pending or completed GitHub checks. The delivered result is
an initialization PR; do not push the initialization directly to the default
branch or treat an open PR as merged.

Point to the generated `docs/PROJECT_SETUP.md` for publishing, Codecov,
Read the Docs, and repository configuration decisions. Continue those tasks
only when they are part of the user's requested scope.

## Failure handling

- **Repository already exists:** determine whether the current run just
  created it. Resume that known bootstrap if appropriate; otherwise resolve
  the name conflict without adopting or resetting someone else's repository.
- **Dirty-tree or ignored-path refusal:** inspect the exact target paths in
  the diagnostic. Keep user work intact. Preview and run `press clean` only
  for the target's declared paths; resolve remaining collisions explicitly.
- **Apply failure:** record the exit code and engine diagnostics, then inspect
  the target and receipt state. A failed apply can leave rewritten files.
  Use target-scoped restoration for individually reviewed paths, or start a
  separate fresh clone while retaining the failed checkout for diagnosis.
  Do not run blanket `git clean` or silently retry with force flags.
- **Check, build, hook, or push failure:** fix confirmed bootstrap problems
  and rerun the affected checks before proceeding. Report missing access or
  service configuration precisely; do not disable gates to create a green PR.
- **User stops the bootstrap:** report which resources and changes exist and
  leave them intact. Stopping does not authorize repository deletion.
