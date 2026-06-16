# Template-Press Bootstrap Dogfood Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `smorinlabs/template-press` by dogfooding the blueprint's
template machinery in two runs (throwaway `blueprint-dryrun` first), with a
live problem log and POST_INIT.md coverage matrix as deliverables feeding
issue #423.

**Architecture:** Operational plan, not code: each task is a command
sequence with expected outcomes, followed by a log update. Three phases —
Run 1 (Tasks 1–12), Triage + design review hard pause (Tasks 13–14), Run 2
(Tasks 15–21, **provisional**: subject to revision at the Task 14
checkpoint, which gates them on explicit user approval). Spec:
`docs/superpowers/specs/2026-06-12-template-press-bootstrap-dogfood-design.md`
(superseded for the build loop by the operative v2 design,
`docs/superpowers/specs/2026-06-13-template-press-bootstrap-dogfood-v2-design.md`).

**Tech Stack:** gh CLI, uv, just, `init/init.py`, `init/post_init.py`,
`init/init_doctor.py`, `repo-secrets` skill, GitHub REST via `gh api`.

**Logging rule (applies to every task):** after each step, append to the
current run's Steps table in
`docs/research/0004-template-press-dogfood-log.md` (blueprint repo). Any
unexpected behavior becomes the next `PROBLEM-NN` entry **before**
continuing. Timestamps: `date -u +%Y-%m-%dT%H:%M:%SZ`. Working directory
is the blueprint repo (`/Users/stevemorin/c/py-launch-blueprint`) unless a
step says otherwise; dry-run repo steps run in `~/c/blueprint-dryrun`.

---

## Phase A — Run 1: blueprint-dryrun

**Skill invocation note:** Tasks 2–8 implement the `new-python-project`
skill's runbook. The executor MUST invoke that skill
explicitly (Skill tool) at the start of Task 2 and follow it; the tasks
below mirror its steps so progress is trackable and deviations between
skill text and reality are loggable (the runbook's accuracy is itself
under test). Where the skill prompts interactively, the identity answers
are pre-decided in Task 4 / the spec. Same applies to Task 15 for run 2.

### Task 1: Create the live log

**Files:**
- Create: `docs/research/0004-template-press-dogfood-log.md`

- [ ] **Step 1: Write the log skeleton**

```markdown
# Template-Press Dogfood — Live Log

- **Spec:** ../superpowers/specs/2026-06-12-template-press-bootstrap-dogfood-design.md
- **Issue:** https://github.com/smorinlabs/py-launch-blueprint/issues/423
- **Started:** <UTC timestamp>

Problems use `PROBLEM-NN` (global numbering across runs): severity
(low/med/high) · what happened · workaround · root cause · disposition
(blueprint fix commit, or #423 phase mapping).

## Run 1 — blueprint-dryrun

### Steps

| time (UTC) | step | command / action | outcome |
|---|---|---|---|

### Problems

(none yet)

### Coverage matrix — POST_INIT.md walk

| POST_INIT.md item | decision | automated by post_init.py? | how actually done | phase-2 module candidate? | problems |
|---|---|---|---|---|---|

## Triage

(after Run 1)

## Run 2 — template-press

(gated on design review checkpoint)
```

- [ ] **Step 2: Commit**

```bash
git add docs/research/0004-template-press-dogfood-log.md
git commit -m "docs: open template-press dogfood live log"
```

### Task 2: Preconditions (runbook step 1)

- [ ] **Step 1: Run the four precondition checks**

```bash
command -v gh && gh auth status && command -v uv && ls ~/c/blueprint-dryrun 2>/dev/null
```

Expected: gh present, authenticated as an account that can create repos
under `smorinlabs`; uv present; `~/c/blueprint-dryrun` absent. (The
runbook's fourth check — "not inside an initialized project" — passes by
construction: the blueprint has no `init/.blueprint-initialized`.)

- [ ] **Step 2: Log the outcome** (and any PROBLEM if a check fails — stop
  on failure, surface to user)

### Task 3: Create and clone the repo (runbook step 4)

- [ ] **Step 1: Create from template**

```bash
gh repo create "smorinlabs/blueprint-dryrun" \
    --template smorinlabs/py-launch-blueprint \
    --public \
    --clone
mv blueprint-dryrun ~/c/blueprint-dryrun 2>/dev/null || true
```

(If running from the blueprint dir, `gh` clones into `./blueprint-dryrun`;
move it to `~/c/blueprint-dryrun`. Alternatively run the create from `~/c`.)

Expected: repo exists at github.com/smorinlabs/blueprint-dryrun, local
clone at `~/c/blueprint-dryrun` with origin set.

- [ ] **Step 2: Verify origin and log**

```bash
git -C ~/c/blueprint-dryrun remote get-url origin
```

Expected: `https://github.com/smorinlabs/blueprint-dryrun.git` (or ssh).

### Task 4: answers.toml + dry-run preview (runbook steps 5–6)

**Files:**
- Create: `~/c/blueprint-dryrun/answers.toml`

- [ ] **Step 1: Write answers.toml**

```toml
[answers]
package_name = "blueprint_dryrun"
repo_name = "blueprint-dryrun"
app_name = "bpd"
author = "Steve Morin"
email = "steve.morin@gmail.com"
owner = "smorinlabs"
```

- [ ] **Step 2: Dry-run the rebrand**

```bash
cd ~/c/blueprint-dryrun && uv run init/init.py --config answers.toml --dry-run --yes
```

Expected: plan listing replaces/renames/removes, ending in a summary line
like `Summary: N removes, N replaces, N renames.` Watch PF-2: author/email
equal the blueprint values — note how same-value fields appear in the plan.

- [ ] **Step 3: Show the user the summary, get explicit go-ahead, log**
  (this is the spec's "dry-run preview shown to the user before apply")

### Task 5: Apply the rebrand (runbook step 7)

- [ ] **Step 1: Apply**

```bash
cd ~/c/blueprint-dryrun && uv run init/init.py --config answers.toml --yes
```

Expected: success; `init/.blueprint-initialized` exists. On failure: log
PROBLEM, recover with `git checkout . && git clean -fd`, surface to user.

- [ ] **Step 2: Verify marker + spot-check rebrand**

```bash
cd ~/c/blueprint-dryrun && ls init/.blueprint-initialized \
  && grep -rn "py_launch_blueprint\|py-launch-blueprint\|plbp" --include="*.py" --include="*.toml" -l . | head
```

Expected: marker present; grep finds no hits outside `init/` machinery.

- [ ] **Step 3: Log** (include whether answers.toml made the tree "dirty"
  — a known runbook failure mode worth a PROBLEM if `--allow-dirty` was
  needed)

### Task 6: Initial commit and push (runbook step 8)

- [ ] **Step 1: Commit + push**

```bash
cd ~/c/blueprint-dryrun && git add -A \
  && git commit -m "chore: initialize blueprint-dryrun from py-launch-blueprint" \
  && git push -u origin main
```

Expected: push succeeds. Note for the log: hooks are NOT yet installed in
this clone (runbook commits before toolchain setup) — record as a matrix
observation, PROBLEM if it bites.

- [ ] **Step 2: Log**

### Task 7: Verification in the new repo

- [ ] **Step 1: Toolchain + env**

```bash
cd ~/c/blueprint-dryrun && make check && just setup
```

Expected: `make check` reports tools present (this machine already has the
toolchain); `just setup` syncs deps and wires hooks.

- [ ] **Step 2: Full check pipeline + doctor**

```bash
cd ~/c/blueprint-dryrun && just check && uv run init/init_doctor.py
```

Expected: all checks pass; doctor reports migration + environment clean.
Any failure → PROBLEM-NN (these are exactly the defects run 1 exists to
find). Commit any resulting fixes in the dryrun repo only if needed to
proceed; blueprint-side fixes wait for triage.

- [ ] **Step 3: Confirm CI on GitHub**

```bash
gh run list -R smorinlabs/blueprint-dryrun --limit 10
```

Expected: workflows from the initial push; note which fail (e.g. jobs
needing secrets/settings not yet configured — matrix material).

- [ ] **Step 4: Log + start filling the coverage matrix** (rows: core CI,
  hooks, commitlint, lint extras — decision "keep", automated "n/a
  (default-on)")

### Task 8: Automated post-init — publishing no, Codecov/RTD later

- [ ] **Step 1: Status before**

```bash
cd ~/c/blueprint-dryrun && uv run init/post_init.py --status
```

- [ ] **Step 2: Run interactively**

`post_init.py` has no headless mode (the #423 phase-1 gap). Attempt:

```bash
cd ~/c/blueprint-dryrun && uv run init/post_init.py
```

Answers: PyPI publish **no** · Codecov **later/defer** · ReadTheDocs
**later/defer**. If it cannot run without a TTY from the agent shell,
that is a PROBLEM (likely the run's most important finding — it is
phase 1's exit criterion) — then ask the user to run
`! cd ~/c/blueprint-dryrun && uv run init/post_init.py` with those answers.

- [ ] **Step 3: Observe PF-3/PF-5 behavior**

```bash
cd ~/c/blueprint-dryrun && ls .github/workflows/ .github/workflows.disabled/ 2>/dev/null \
  && cat init/.blueprint-initialized
```

Record: what "no" did to `publish.yml` and `release-please.yml` (moved to
`.disabled/`? what marker states were written for testpypi/release_please
that were never asked?).

- [ ] **Step 4: Commit the post-init changes in the dryrun repo, push, log**

```bash
cd ~/c/blueprint-dryrun && git add -A && git commit -m "chore: record post-init decisions" && git push
```

### Task 9: POST_INIT.md walk — release-please + secrets

- [ ] **Step 1: Ensure release-please.yml is enabled (PF-5 hand-fix)**

```bash
cd ~/c/blueprint-dryrun && ls .github/workflows/release-please.yml 2>/dev/null \
  || (git mv .github/workflows.disabled/release-please.yml .github/workflows/release-please.yml \
      && git commit -m "ci: re-enable release-please without pypi publishing" && git push)
```

Log the coupling observation against PF-5 in Problems + matrix.

- [ ] **Step 2: Set release-please + contributors secrets via the
  repo-secrets skill** — invoke skill `repo-secrets` with args
  `smorinlabs/blueprint-dryrun` (both apps, values from 1Password).
  Expected: `RELEASE_PLEASE_CLIENT_ID`, `RELEASE_PLEASE_PRIVATE_KEY`,
  `CONTRIBUTORS_PLEASE_CLIENT_ID`, `CONTRIBUTORS_PLEASE_PRIVATE_KEY`,
  `CONTRIBUTORS_PLEASE_PAT` set.

- [ ] **Step 3: Verify + check app installation coverage**

```bash
gh secret list -R smorinlabs/blueprint-dryrun
gh api /repos/smorinlabs/blueprint-dryrun/installation --jq .app_slug 2>&1 || true
```

If the GitHub Apps are not installed on the new repo (org install not
"All repositories"), that's a manual errand: present the user the install
URLs with pre-computed values. Log either way; matrix rows:
release-please (keep, partially automated via skill), contributors (keep).

### Task 10: POST_INIT.md walk — repo settings via gh api

Run each check/set pair; log each as a matrix row (decision "set",
automated by post_init.py "no"). All commands from POST_INIT.md §3 with
`smorinlabs/blueprint-dryrun` substituted.

- [ ] **Step 1: CodeQL default setup OFF (§3.1)**

```bash
gh api /repos/smorinlabs/blueprint-dryrun/code-scanning/default-setup --jq .state
# if "configured":
gh api --method PATCH /repos/smorinlabs/blueprint-dryrun/code-scanning/default-setup -f state=not-configured
```

Expected final state: `not-configured`.

- [ ] **Step 2: Actions can create/approve PRs (§3.2)**

```bash
gh api --method PUT /repos/smorinlabs/blueprint-dryrun/actions/permissions/workflow \
  -F default_workflow_permissions=write -F can_approve_pull_request_reviews=true
gh api /repos/smorinlabs/blueprint-dryrun/actions/permissions/workflow
```

- [ ] **Step 3: Dependabot + private vulnerability reporting (§3.5)**

```bash
gh api --method PUT /repos/smorinlabs/blueprint-dryrun/vulnerability-alerts
gh api --method PUT /repos/smorinlabs/blueprint-dryrun/automated-security-fixes
gh api --method PUT /repos/smorinlabs/blueprint-dryrun/private-vulnerability-reporting
```

- [ ] **Step 4: Merge strategy (§3.8)**

```bash
gh api --method PATCH /repos/smorinlabs/blueprint-dryrun \
  -F allow_squash_merge=true -F allow_merge_commit=false \
  -F allow_rebase_merge=false -F delete_branch_on_merge=true
```

- [ ] **Step 5: Branch protection (§3.6)**

```bash
gh api -X PUT /repos/smorinlabs/blueprint-dryrun/branches/main/protection --input - <<'JSON'
{
  "required_status_checks": {
    "strict": false,
    "contexts": [
      "ci-ok", "integration-ok", "guard", "unit-tests",
      "commitlint (humans)",
      "actionlint", "bandit", "codespell", "editorconfig-check", "yamllint"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
```

Caution: `integration-ok` / `guard` are blueprint-CI job names — verify
each context actually exists on this repo's PRs
(`gh run list` + check names); a context that never reports blocks all
merges. Adjust the list to reality and log any divergence as a PROBLEM
(POST_INIT.md §3.6 accuracy).

- [ ] **Step 6: Log + matrix rows for §3.2–§3.8; also add deferred rows**
  (Codecov later, RTD later, Safety defer, CLA defer, funding keep-as-is,
  secret scanning / dependency review keep-default-on)

### Task 11: Release-please flow (no publishing)

- [ ] **Step 1: Trigger / find the release PR**

```bash
gh run list -R smorinlabs/blueprint-dryrun --workflow=release-please.yml --limit 3
gh pr list -R smorinlabs/blueprint-dryrun
```

Expected: a `chore(main): release ...` PR (release-please runs on push to
main; the Task 9/10 pushes count). If the workflow fails on auth, the
secrets/app from Task 9 are wrong → PROBLEM + fix.

- [ ] **Step 2: Merge the release PR**

```bash
gh pr merge <PR#> -R smorinlabs/blueprint-dryrun --squash
```

Expected: tag `v0.1.0` created. `publish.yml` is disabled, so nothing
publishes — confirm:

```bash
gh release list -R smorinlabs/blueprint-dryrun
gh run list -R smorinlabs/blueprint-dryrun --limit 5
```

If branch protection blocks the merge on never-reporting contexts, fix the
context list (Task 10 step 5) and log.

- [ ] **Step 3: Log + matrix row** (release-please: end-to-end works
  without publishing — evidence for PF-5)

### Task 12: Close out Run 1

- [ ] **Step 1: Completeness sweep** — every POST_INIT.md §1 item has a
  matrix row; every §3 subsection has an outcome; every problem has a
  numbered entry with disposition "pending triage".

- [ ] **Step 2: Commit the log to the blueprint**

```bash
cd /Users/stevemorin/c/py-launch-blueprint \
  && git add docs/research/0004-template-press-dogfood-log.md \
  && git commit -m "docs: record dogfood run 1 (blueprint-dryrun) log and coverage matrix"
```

---

## Phase B — Triage + design review (HARD PAUSE)

### Task 13: Triage every PROBLEM-NN

- [ ] **Step 1: Classify each problem**: (a) small, clear blueprint defect
  → fix now; (b) structural → map to #423 phase 1/2/3 in the log's Triage
  section.

- [ ] **Step 2: For each (a) fix**: make the change in the blueprint,
  verify per AGENTS.md (`just check`, plus
  `uv run --script init/ci/check_manifest_drift.py` and
  `uv run pytest init/tests/ --override-ini="addopts=" -q` if the change
  touches the init system), conventional commit referencing the problem
  number, e.g. `fix(init): <subject> (dogfood PROBLEM-03)`.

- [ ] **Step 3: Update each problem's disposition in the log; commit**

```bash
git add docs/research/0004-template-press-dogfood-log.md
git commit -m "docs: triage run 1 dogfood problems"
```

### Task 14: Design review checkpoint — STOP

- [ ] **Step 1: Present to the user**: the run-1 log (problems, matrix,
  triage outcomes) and proposed spec revisions (including the live-log
  protocol itself and the run-2 sequence).

- [ ] **Step 2: Revise the spec** per the discussion; commit revisions.

- [ ] **Step 3: WAIT for explicit user approval.** Run 2 (Tasks 15–21)
  must not start without it. Revise Tasks 15–21 here first if the review
  changed the design.

---

## Phase C — Run 2: template-press (provisional until Task 14 approval)

### Task 15: Bootstrap template-press

- [ ] **Step 1: Preconditions** (as Task 2; also `~/c/template-press`
  absent, `smorinlabs/template-press` not on GitHub)

- [ ] **Step 2: Create + clone**

```bash
gh repo create "smorinlabs/template-press" \
    --template smorinlabs/py-launch-blueprint \
    --public \
    --clone
mv template-press ~/c/template-press 2>/dev/null || true
git -C ~/c/template-press remote get-url origin
```

- [ ] **Step 3: answers.toml**

```toml
[answers]
package_name = "template_press"
repo_name = "template-press"
app_name = "press"
author = "Steve Morin"
email = "steve.morin@gmail.com"
owner = "smorinlabs"
```

- [ ] **Step 4: Dry-run, show user, apply, verify** (as Tasks 4–5)

```bash
cd ~/c/template-press && uv run init/init.py --config answers.toml --dry-run --yes
# user approves →
uv run init/init.py --config answers.toml --yes
ls init/.blueprint-initialized
```

- [ ] **Step 5: Add the `tpress` alias entry point (PF-1 hand-fix)** —
  in `~/c/template-press/pyproject.toml`, extend `[project.scripts]`:

```toml
[project.scripts]
press = "template_press.cli.main:cli"
tpress = "template_press.cli.main:cli"
```

(Verify the actual module path from the rebranded pyproject's existing
`press = ...` line and mirror it; then `uv lock` to refresh.) Log PF-1.

- [ ] **Step 6: Commit + push; verify** (as Tasks 6–7: initial commit,
  push, `make check`, `just setup`, `just check`, `init_doctor.py`, CI
  green; log everything)

```bash
cd ~/c/template-press && git add -A \
  && git commit -m "chore: initialize template-press from py-launch-blueprint" \
  && git push -u origin main \
  && make check && just setup && just check && uv run init/init_doctor.py
```

### Task 16: Post-init — publishing YES, Codecov/RTD later

- [ ] **Step 1: Run post-init** (method per run-1 learning: agent-driven
  if a headless path was added in triage, else user runs
  `! cd ~/c/template-press && uv run init/post_init.py`). Answers: PyPI
  **yes**, TestPyPI **yes**, release-please **yes**, Codecov **later**,
  RTD **later**.

Expected: `publish.yml` + `release-please.yml` active; GitHub
environments `pypi` + `testpypi` created (script
`init/setup-github-environments.sh` runs inside post-init full mode);
OIDC walkthrough reaches the trusted-publisher step.

- [ ] **Step 2: PyPI/TestPyPI trusted publishers (manual errand — user).**
  The projects already exist (0.0.0.dev0), so this is "add a publisher to
  an existing project": pypi.org → manage project `template-press` →
  Publishing → add GitHub Actions publisher, then the same on
  test.pypi.org. Present exactly:

```text
project:   template-press
owner:     smorinlabs
repo:      template-press
workflow:  publish.yml
environment: pypi        (testpypi on test.pypi.org)
URL: https://pypi.org/manage/project/template-press/settings/publishing/
URL: https://test.pypi.org/manage/project/template-press/settings/publishing/
```

post-init's poll-verify checks project existence, which already passes —
note in the log whether it can actually verify the *publisher* (suspected
check weakness; possible new PROBLEM).

- [ ] **Step 3: Commit decisions, push, log**

### Task 17: POST_INIT.md walk for template-press

- [ ] **Step 1: Secrets via repo-secrets skill** for
  `smorinlabs/template-press` (both apps), verify with
  `gh secret list -R smorinlabs/template-press`, check app installation
  (as Task 9 step 3).

- [ ] **Step 2: Repo settings** — repeat Task 10 steps 1–5 against
  `smorinlabs/template-press` (same commands, repo substituted; branch
  protection context list as corrected by run 1).

- [ ] **Step 3: Matrix rows for run 2** (publishing rows now "yes";
  reuse run-1 dispositions where identical, note diffs)

### Task 18: First release over the dev0 placeholder

- [ ] **Step 1: Merge the release-please PR**

```bash
gh pr list -R smorinlabs/template-press
gh pr merge <PR#> -R smorinlabs/template-press --squash
```

Expected: tag `v0.1.0`, `publish.yml` fires: TestPyPI then PyPI via OIDC.

- [ ] **Step 2: Verify publication**

```bash
gh run list -R smorinlabs/template-press --workflow=publish.yml --limit 2
curl -s https://pypi.org/pypi/template-press/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
```

Expected: workflow green; PyPI latest version `0.1.0` (supersedes
0.0.0.dev0). Failures → PROBLEM + fix (common: publisher form mismatch on
environment name).

- [ ] **Step 3: Log**

### Task 19: Close out Run 2 + commit log

- [ ] **Step 1: Completeness sweep** (as Task 12 step 1, for Run 2
  section)

- [ ] **Step 2: Commit**

```bash
cd /Users/stevemorin/c/py-launch-blueprint \
  && git add docs/research/0004-template-press-dogfood-log.md \
  && git commit -m "docs: record dogfood run 2 (template-press) log"
```

### Task 20: Feedback loop on issue #423

- [ ] **Step 1: Comment on #423** — summary: repo created, release
  published, link to log + matrix, every PROBLEM-NN with its phase
  mapping, PF-1..PF-5 verdicts.

```bash
gh issue comment 423 --repo smorinlabs/py-launch-blueprint --body-file /tmp/423-comment.md
```

- [ ] **Step 2: Update the #423 phase-3 checklist** — check "Create the
  repo; reserve `template-press` on PyPI immediately" via
  `gh issue edit 423 --repo smorinlabs/py-launch-blueprint --body-file <updated-body>`
  (fetch current body, flip the checkbox, note reservation predated this
  work).

- [ ] **Step 3: Register tracking** — invoke skill `project-add` to
  capture the #423 implementation work on the blueprint trunk
  (PROJECTS.md), referencing the spec, plan, and log.

### Task 21: Throwaway cleanup (confirmed, destructive)

- [ ] **Step 1: Show the user what exists** — `gh repo view
  smorinlabs/blueprint-dryrun` summary + local `git -C ~/c/blueprint-dryrun
  status`; confirm both deletions explicitly.

- [ ] **Step 2: On confirmation only**

```bash
gh repo delete smorinlabs/blueprint-dryrun --yes
rm -rf ~/c/blueprint-dryrun
```

- [ ] **Step 3: Final log entry; commit; push the blueprint branch work**
  per the user's instruction at that time (push/PR is a user call).
