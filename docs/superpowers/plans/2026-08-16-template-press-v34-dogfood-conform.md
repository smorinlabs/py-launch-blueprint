# Template-Press v3.4 Dogfood & Conform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove template-press v3.4/P07 end-to-end against py-launch-blueprint — author the blueprint's `press/` config from scratch, iterate `press verify` to a declarations-only exit 0, rebrand a local instance, and publish it to a throwaway GitHub repo — logging every finding as a PROBLEM-NN with a disposition.

**Architecture:** Operational dogfood campaign, not a code build. Config authoring + verify runs happen in the blueprint worktree `~/c/py-launch-blueprint-press-conform` (branch `feat/press-conform`); engine bugs, if found, are fixed in separate template-press worktrees per the triage protocol (Task 7). Exit codes are the assertions: `press` verbs exit 0/1/2 by contract, so each run is a test.

**Tech Stack:** template-press `press` CLI (run as `uv run press …` from `~/c/template-press`), TOML config, sh/PowerShell regen scripts, `gh` REST, lefthook-gated commits.

**Spec:** `docs/superpowers/specs/2026-08-16-template-press-v34-dogfood-design.md` (committed `05254e5` on this branch — read it first; §2 has the gap table, §3 the standing decisions D-v4-1..6, §4 the phases).

## Global Constraints

- **Press-under-test pin (D-v4-1):** template-press `main` @ `bd52085`. Run every press command as `cd ~/c/template-press && uv run press …`. If main moves, re-pin explicitly in the dogfood log.
- **Target:** the worktree `/Users/stevemorin/c/py-launch-blueprint-press-conform` (never the live checkout `~/c/py-launch-blueprint`).
- **Green via declarations, never ignores (D-v4-5):** an engine capability gap is fixed in template-press or deferred with a reasoned `[[verify.ignore]]` — never dodged by rewording blueprint content. Target: zero ignores.
- **Findings (D-v4-6):** every unexpected outcome becomes a `PROBLEM-NN` entry (severity · what happened · workaround · root cause · disposition) in `docs/research/0004-template-press-dogfood-log.md` "Run 4", numbering starts at **PROBLEM-21**.
- **Commits:** Conventional Commits, lowercase subject (commitlint hook enforces; `bun install --frozen-lockfile` already run in this worktree so hooks fire). Merge PRs with `--merge` (squash is disabled repo-wide).
- **GitHub polling:** REST only (`gh api`), never more than once per 20 seconds.
- **User gates:** Task 8 (scope gate), Task 9 (merging PR #505), Task 13 (repo creation) require explicit user confirmation — do not proceed past them autonomously.
- **Blueprint verification before any push:** `just check` plus init-system integrity (`uv run --script init/ci/check_manifest_drift.py` and `uv run pytest init/tests/ --override-ini="addopts=" -q`) — the pre-push hook runs these; they must pass, not be bypassed.

---

### Task 1: Register the campaign as project P05

**Files:**
- Modify: `PROJECTS.md` (trunk table, after the P04 row)
- Create: `projects/P05-template-press-v34-dogfood-conform.md`

**Interfaces:**
- Produces: project ID `P05`, referenced by later commits and the close-out (Task 14).

- [ ] **Step 1: Add the trunk row**

In `PROJECTS.md`, after the P04 row, add:

```markdown
| P05 | `[~]` | [Template-press v3.4 dogfood & conform](projects/P05-template-press-v34-dogfood-conform.md) — press/ config from scratch, verify to declarations-only green, rebrand + publish an instance; findings → Run 4 PROBLEM-NN |
```

- [ ] **Step 2: Create the project file**

Create `projects/P05-template-press-v34-dogfood-conform.md`:

```markdown
## [~] Project P05: Template-press v3.4 dogfood & conform (v1.0.0)
**Goal/Requirement**: Test template-press main @ bd52085 against this repo and
bring this repo's press config in sync — verify exit 0 via declarations, a
rebranded instance passes its own checks, and an instance publishes to a
throwaway repo. Spec: docs/superpowers/specs/2026-08-16-template-press-v34-dogfood-design.md

**Out of Scope**
- press provision/status (M6); G4 display-name design changes beyond using the
  shipped display_name field; deleting init/ unless the scope gate approves.

### Tests & Tasks
- [ ] [P05-T01] Register project + open dogfood log Run 4
- [ ] [P05-T02] Author press/press-source.toml (from scratch)
- [ ] [P05-T03] Author regen scripts + press/press-rules.toml
- [ ] [P05-T04] Satisfy init-system integrity for the press/ files
- [ ] [P05-TS01] press check-tools exits 0 against the worktree
- [ ] [P05-TS02] press verify reaches exit 0, zero ignores
- [ ] [P05-T05] Scope gate decision recorded (user)
- [ ] [P05-T06] PR #505 merged (user-confirmed)
- [ ] [P05-T07] Round-1 PR merged; verify green from fresh main clone
- [ ] [P05-TS03] Local rebrand battery passes (dry-run/apply/re-press/check-tools/instance checks)
- [ ] [P05-T08] Instance published to throwaway repo; CI triaged (user-gated)
- [ ] [P05-T09] Close-out: dispositions, cleanup, report

### Deliverable
```bash
$ cd ~/c/template-press && uv run press verify --target <fresh plbp main clone>
$ echo $?
0
```

### Automated Verification
- `press verify` exit 0 with zero `[[verify.ignore]]` entries
- `press check-tools` exit 0
- pressed instance passes `make check` and `just check`

### Manual Verification
- Throwaway repo CI green (release-please may stay credential-gated red)
```

- [ ] **Step 3: Commit**

```bash
cd /Users/stevemorin/c/py-launch-blueprint-press-conform
git add PROJECTS.md projects/P05-template-press-v34-dogfood-conform.md
git commit -m "docs(projects): register p05 template-press v3.4 dogfood and conform"
```

---

### Task 2: Open dogfood log Run 4

**Files:**
- Modify: `docs/research/0004-template-press-dogfood-log.md` (append after Run 3)

**Interfaces:**
- Produces: the "Run 4" section every later task appends findings to (PROBLEM-21+).

- [ ] **Step 1: Append the Run 4 header**

Append to `docs/research/0004-template-press-dogfood-log.md` (match Run 3's style):

```markdown
## Run 4 — v3.4/P07 conform + rebrand + publish (2026-08-16)

**Context.** Spec `docs/superpowers/specs/2026-08-16-template-press-v34-dogfood-design.md`
(P05). Press-under-test: template-press `main` @ `bd52085` (P07 merge; v3.4.0
tag + platform-conditional declared commands). Target: this repo, branch
`feat/press-conform` from `origin/main` @ `734abfd`.

**Expectations.** All five Run-3 gaps (G1–G5) now have opt-in engine support
(G3/G4/G5 in v3.3.0: substring mode, display_name, replace/path rules;
G1/G2 in v3.4.0: declared [[reset]]/[[regenerate]]). Prediction: with a
fully-declared config, verify reaches exit 0 with zero ignores. Any leak is a
config-authoring gap (blueprint) or an engine regression (template-press) —
no known-gap bucket remains. Numbering continues at PROBLEM-21.

### Steps

| time (UTC) | step | command / action | outcome |
|---|---|---|---|
```

- [ ] **Step 2: Commit**

```bash
git add docs/research/0004-template-press-dogfood-log.md
git commit -m "docs(research): open dogfood log run 4 with v3.4 expectations"
```

---

### Task 3: Author `press/press-source.toml` from scratch

**Files:**
- Create: `press/press-source.toml`

**Interfaces:**
- Produces: the source identity every press verb reads. Field names are fixed by the engine: `package_name`, `repo_name`, `app_name`, `author`, `email`, `owner`, `display_name`.

- [ ] **Step 1: Cross-check identity values against the repo**

```bash
cd /Users/stevemorin/c/py-launch-blueprint-press-conform
grep -E '^name|^authors' pyproject.toml
grep -E 'package|app|owner|author|email' init/manifest.toml | head -12
```
Expected: package `py_launch_blueprint`, repo `py-launch-blueprint`, app `plbp`, owner `smorinlabs`, author `Steve Morin`, email `steve.morin@gmail.com`. If any value differs, use the repo's value and log a PROBLEM entry.

- [ ] **Step 2: Write the file**

Create `press/press-source.toml`:

```toml
[identity]
package_name = "py_launch_blueprint"
repo_name    = "py-launch-blueprint"
app_name     = "plbp"
author       = "Steve Morin"
email        = "steve.morin@gmail.com"
owner        = "smorinlabs"
display_name = "Py Launch Blueprint"
```

- [ ] **Step 3: Run verify to prove the config parses (failure expected, but not "missing config")**

```bash
cd /Users/stevemorin/c/template-press
uv run press verify --target /Users/stevemorin/c/py-launch-blueprint-press-conform --json; echo "exit=$?"
```
Expected: **not** the exit-2 "missing source-config" refusal Run 3 started from. Exit 1 (leaks — no rules yet) or exit 2 for a *different* stated reason (e.g. excluded-file contract) are both acceptable here; record the exact exit + reason in the Run 4 steps table. Commit the log row together with Step 4.

- [ ] **Step 4: Commit**

```bash
cd /Users/stevemorin/c/py-launch-blueprint-press-conform
git add press/press-source.toml docs/research/0004-template-press-dogfood-log.md
git commit -m "feat(press): declare source identity for external press"
```

---

### Task 4: Regen scripts for `bun.lock`

**Files:**
- Create: `scripts/regen-bun-lock.sh`
- Create: `scripts/regen-bun-lock.ps1`

**Interfaces:**
- Consumes: nothing.
- Produces: the argv targets for Task 5's `[[regenerate]]` bun.lock entries.

- [ ] **Step 1: Write the POSIX script**

Create `scripts/regen-bun-lock.sh` (mechanism per template-press's own script — `bun install` never rewrites an existing lock's workspace name, so the lock must go first; tool check must precede the destructive rm):

```sh
#!/bin/sh
# Regenerate bun.lock FROM SCRATCH for the declared [[regenerate]] rule.
# `bun install` never rewrites an existing lockfile's workspace name, so a
# pressed identity survives in bun.lock unless the lock is removed first.
set -e
# check-tools resolves this script, not the bun inside it: a missing bun
# must fail here with the lock still intact, before the rm.
command -v bun >/dev/null 2>&1 || { echo "regen-bun-lock: bun not found" >&2; exit 127; }
rm -f bun.lock
exec bun install
```

- [ ] **Step 2: Write the PowerShell script**

Create `scripts/regen-bun-lock.ps1`:

```powershell
# Regenerate bun.lock FROM SCRATCH for the declared [[regenerate]] rule.
$ErrorActionPreference = "Stop"
if (-not (Get-Command bun -ErrorAction SilentlyContinue)) {
    Write-Error "regen-bun-lock: bun not found"
    exit 127
}
Remove-Item -Force -ErrorAction SilentlyContinue bun.lock
bun install
exit $LASTEXITCODE
```

- [ ] **Step 3: Verify syntax + executability**

```bash
cd /Users/stevemorin/c/py-launch-blueprint-press-conform
chmod +x scripts/regen-bun-lock.sh
sh -n scripts/regen-bun-lock.sh && echo "sh OK"
```
Expected: `sh OK`.

- [ ] **Step 4: Commit**

```bash
git add scripts/regen-bun-lock.sh scripts/regen-bun-lock.ps1
git commit -m "feat(press): add bun.lock regeneration scripts for declared rules"
```

---

### Task 5: Author `press/press-rules.toml`

**Files:**
- Create: `press/press-rules.toml`

**Interfaces:**
- Consumes: Task 4's scripts; Task 3's identity fields.
- Produces: the rules/verify config Tasks 6–12 run against.

- [ ] **Step 1: Write the initial rules file**

Create `press/press-rules.toml`. This is the from-scratch first draft encoding the five gap closures; Task 6/7 iterate it against real verify output:

```toml
# This repo is a press target (design 0006): every tracked excluded file
# declares its neutralization, and the identity variants that leaked in
# dogfood Run 3 (G3/G4/G5) are closed by declaration, not by ignores.

[rules]
# G3: plbp appears in glued forms (_plbp_owned, plbp-web) and PLBP in
# uppercase glued forms — the token is word-disjoint in this repo.
substring_rewrite_fields = ["app_name", "app_name_upper"]

# G2: bun.lock is excluded from rewrite; regenerate under the new identity.
[[regenerate]]
file = "uv.lock"
command = ["uv", "lock"]

[[regenerate]]
file = "bun.lock"
command = ["scripts/regen-bun-lock.sh"]
platforms = ["darwin", "linux"]

[[regenerate]]
file = "bun.lock"
command = ["powershell", "-NoProfile", "-File", "scripts/regen-bun-lock.ps1"]
platforms = ["win32"]

# G1: CHANGELOG is release history of the template, not the fork.
[[reset]]
file = "CHANGELOG.md"
stub = "# Changelog\n"
```

Notes for the implementer:
- `display_name` needs no `[rules]` entry — declaring it in `[identity]` (Task 3) turns the feature on; `display_forms` defaults to all three forms (spaced/Pascal/camel).
- G5 (doc filenames `docs/adr/0001-app-short-name-plbp.md`, `docs/design/0001-plbp-cli-conventions.md`) should be covered by substring mode, which applies to path components too. If verify still flags them, add a `[[replace]]` rule (keys: `pattern` with `{app_name}` placeholders, required `reason`, optional `files` globs, `paths = true`) — do NOT add an ignore.
- If the excluded-file contract gate (exit 2) names other tracked excluded files (candidates: `dist/`, `coverage.xml`, `llms.txt`), each needs a `[[regenerate]]`, `[[reset]]`, or an explicit engine-supported declaration — record each as a PROBLEM entry first, then fix.

- [ ] **Step 2: Run check-tools (config-parse + tool-resolution test)**

```bash
cd /Users/stevemorin/c/template-press
uv run press check-tools --target /Users/stevemorin/c/py-launch-blueprint-press-conform; echo "exit=$?"
```
Expected: exit 0, reporting `uv`, `scripts/regen-bun-lock.sh` (and the win32 entry as not-applicable on darwin). Exit 2 = config error: read the message, fix the TOML, re-run. Log the run in Run 4.

- [ ] **Step 3: Commit**

```bash
cd /Users/stevemorin/c/py-launch-blueprint-press-conform
git add press/press-rules.toml docs/research/0004-template-press-dogfood-log.md
git commit -m "feat(press): declare rules — substring mode, regenerate, reset"
```

---

### Task 6: First full verify run (the measurement)

**Files:**
- Modify: `docs/research/0004-template-press-dogfood-log.md`
- Create (scratch, not committed): `/private/tmp/claude-501/-Users-stevemorin-c/f9c90818-964e-465b-a70c-b5cac723b07b/scratchpad/verify-run1.json`

**Interfaces:**
- Produces: the leak inventory Task 7 iterates on and Task 8 presents.

- [ ] **Step 1: Run verify, capture JSON**

```bash
cd /Users/stevemorin/c/template-press
uv run press verify --target /Users/stevemorin/c/py-launch-blueprint-press-conform --json \
  > /private/tmp/claude-501/-Users-stevemorin-c/f9c90818-964e-465b-a70c-b5cac723b07b/scratchpad/verify-run1.json; echo "exit=$?"
```
Expected per spec §2: exit 0. Exit 1 → findings JSON lists surviving (file, field, value, line) tuples. Exit 2 → read the stated reason (likely the excluded-file contract).

- [ ] **Step 2: Classify every finding**

For each finding class (group by field + file pattern), decide:
- **Config-authoring gap** (a declaration exists that would express this) → fix in this worktree (Task 7 loop).
- **Engine gap/regression** (no declaration can express it, or a declared rule didn't do what its docs say) → template-press finding (Task 7 protocol B).
Record each class as `PROBLEM-21`, `PROBLEM-22`, … in Run 4 with severity/root cause/disposition, and add a steps-table row for the run itself.

- [ ] **Step 3: Commit the log update**

```bash
cd /Users/stevemorin/c/py-launch-blueprint-press-conform
git add docs/research/0004-template-press-dogfood-log.md
git commit -m "docs(research): record run 4 first verify results"
```

---

### Task 7: Iterate verify to declarations-only exit 0

**Files:**
- Modify: `press/press-rules.toml`, `press/press-source.toml`, blueprint content files as findings dictate
- Modify: `docs/research/0004-template-press-dogfood-log.md` (every round)

**Interfaces:**
- Consumes: Task 6's inventory.
- Produces: verify exit 0 against this worktree, zero `[[verify.ignore]]` entries.

This is a loop, not a straight line. Per round:

- [ ] **Step 1: Fix the largest finding class** by its Task 6 classification:
  - **(A) Blueprint config/content fix** — edit rules/content in this worktree. Rules first (a missing declaration), content second (genuine drift, e.g. a stale hardcoded name), and only with D-v4-5 in mind: never reword content merely to dodge the scanner.
  - **(B) Engine bug** — do NOT work around it here. Create a template-press worktree
    (`git -C ~/c/template-press worktree add ../template-press-run4-fix -b fix/run4-<slug> origin/main`),
    reproduce with a failing test (template-press uses pytest under `tests/`; follow its existing test layout), fix minimally, run its gate (`cd ~/c/template-press-run4-fix && just all` — or `make check` first if the toolchain is cold), open a PR, merge per template-press conventions, then `git -C ~/c/template-press pull --ff-only` and **re-pin**: record the new main SHA in Run 4 (D-v4-1). Remove the worktree after merge.
- [ ] **Step 2: Re-run verify** (same command as Task 6 Step 1, incrementing the JSON filename). Log the round's row.
- [ ] **Step 3: Commit the round** (`fix(press): …` or `docs(research): …` as appropriate, one commit per coherent fix).
- [ ] **Step 4: Exit condition** — verify exit 0 AND `grep -c 'verify.ignore' press/press-rules.toml` returns 0. If a finding genuinely cannot be fixed either side this campaign, STOP and take it to the user at the scope gate instead of adding an ignore.

---

### Task 8: SCOPE GATE — user decision (checkpoint)

**Interfaces:**
- Consumes: Task 7's final inventory + Run 4 log.

- [ ] **Step 1: Present to the user**: rounds run, PROBLEM entries with dispositions, final verify status, ignore count (target 0). Then ask, per spec §4:
  - Verify green via declarations → offer upgrading to the **full conform** (delete `init/`, CI cutover — a NEW plan via writing-plans if accepted; not folded into this one).
  - New engine gaps surfaced → recommend staying sync+publish; gaps filed against template-press.
- [ ] **Step 2: Record the decision** in Run 4 and in `projects/P05-…md` (P05-T05), commit `docs(research): record run 4 scope gate decision`. **Do not proceed to Task 9 without the user's answer.**

---

### Task 9: Merge PR #505 (user-confirmed; prerequisite for Tasks 11–13)

**Interfaces:**
- Produces: receipt-aware `init/guard.sh` on `main`, so a pressed instance's guard does not block build/publish (July PROBLEM-11 class).

- [ ] **Step 1: Confirm with the user** that PR #505 (`fix(guard): accept a press receipt as an initialized marker`) should merge now. It is the user's own open PR; do not merge unprompted.
- [ ] **Step 2: Drive it to merge** with the `pr-merge-flow` skill (this repo's merge guard requires every review thread resolved; merge with `--merge`).
- [ ] **Step 3: Verify** `gh api repos/smorinlabs/py-launch-blueprint/pulls/505 --jq .merged` → `true`.

---

### Task 10: Round-1 PR — land the branch

**Files:**
- Modify: `init/manifest.toml` (track the new identity-bearing files)

**Interfaces:**
- Consumes: everything committed on `feat/press-conform`.
- Produces: press config + spec + plan + log on `main`.

- [ ] **Step 1: Satisfy init-system integrity.** The new `press/` files and regen scripts contain identity values, so the legacy drift guard will flag them. Add entries for `press/press-source.toml`, `press/press-rules.toml` (and the scripts if flagged) to the matching `[[replace]]` blocks in `init/manifest.toml`, then prove it:

```bash
cd /Users/stevemorin/c/py-launch-blueprint-press-conform
uv run --script init/ci/check_manifest_drift.py
uv run pytest init/tests/ --override-ini="addopts=" -q
```
Expected: both pass. (This coexistence tax disappears if the scope gate approved the full conform — it still must pass HERE, since init/ is alive on this branch.)

- [ ] **Step 2: Full gate**

```bash
just check
```
Expected: pass. Commit any fixes (`fix(press): …`).

- [ ] **Step 3: Commit manifest update, push, open PR**

```bash
git add init/manifest.toml
git commit -m "chore(init): track press config files in the drift manifest"
git push -u origin feat/press-conform
gh pr create --repo smorinlabs/py-launch-blueprint \
  --title "feat(press): conform to template-press v3.4 — source identity, declared rules, run 4 log" \
  --body "Implements docs/superpowers/specs/2026-08-16-template-press-v34-dogfood-design.md Phase 1. press verify (template-press main @ <final pin>) exits 0 against this branch with zero ignores. Findings: see dogfood log Run 4 (PROBLEM-21+)."
```

- [ ] **Step 4: Drive to merge** via `pr-merge-flow` (merge commit). Then sync the live checkout is NOT done here — the user's live checkout has local divergence (spec Phase 0); leave it, note it for close-out.

---

### Task 11: Post-merge gate — verify green from a fresh main clone

**Interfaces:**
- Produces: the round-exit evidence (D-v4-4): green against committed `main`, not a branch.

- [ ] **Step 1: Fresh clone + verify + check-tools**

```bash
cd /private/tmp/claude-501/-Users-stevemorin-c/f9c90818-964e-465b-a70c-b5cac723b07b/scratchpad
git clone --depth 1 https://github.com/smorinlabs/py-launch-blueprint.git plbp-main-gate
cd /Users/stevemorin/c/template-press
uv run press verify --target /private/tmp/claude-501/-Users-stevemorin-c/f9c90818-964e-465b-a70c-b5cac723b07b/scratchpad/plbp-main-gate; echo "verify=$?"
uv run press check-tools --target /private/tmp/claude-501/-Users-stevemorin-c/f9c90818-964e-465b-a70c-b5cac723b07b/scratchpad/plbp-main-gate; echo "tools=$?"
```
Expected: both 0. Any other result → new PROBLEM entry, back to Task 7 (new round).

- [ ] **Step 2: Log the gate row** in Run 4 (small follow-up PR or fold into the next round's PR — Run 4 log updates after the round-1 merge accumulate on a fresh branch).

---

### Task 12: Local rebrand battery (Phase 3)

**Interfaces:**
- Consumes: merged `main` (Task 11 green), PR #505 merged (Task 9).
- Produces: a pressed local instance passing its own checks; coverage of the v3.4/P07 surface.

Scratch base: `SCRATCH=/private/tmp/claude-501/-Users-stevemorin-c/f9c90818-964e-465b-a70c-b5cac723b07b/scratchpad`. Answers file lives OUTSIDE the target (transient operator input, per template-press README).

- [ ] **Step 1: Clone + answers**

```bash
git clone https://github.com/smorinlabs/py-launch-blueprint.git "$SCRATCH/blueprint-press-dryrun"
cat > "$SCRATCH/press-answers.toml" <<'EOF'
[answers]
package_name = "blueprint_press_dryrun"
repo_name    = "blueprint-press-dryrun"
app_name     = "bpd"
author       = "Steve Morin"
email        = "steve.morin@gmail.com"
owner        = "smorinlabs"
display_name = "Blueprint Press Dryrun"
EOF
```
(`display_name` is REQUIRED in answers because the source declares one — half-specified is exit 2 by design.)

- [ ] **Step 2: Dry-run** — `cd ~/c/template-press && uv run press rebrand --target "$SCRATCH/blueprint-press-dryrun" --config "$SCRATCH/press-answers.toml" --dry-run; echo $?` → expect 0 + a plan whose counts include the CHANGELOG reset preview and both lockfile regenerations. Review the plan; anomalies → PROBLEM entry.
- [ ] **Step 3: Apply** — same command without `--dry-run` → expect exit 0, `press/press-receipt.toml` written, `press/press-source.toml` refreshed to the new identity.
- [ ] **Step 4: Independent leak audit** (don't trust only the scanner):

```bash
cd "$SCRATCH/blueprint-press-dryrun"
grep -rn --exclude-dir=.git -e py_launch_blueprint -e py-launch-blueprint -e "Py Launch Blueprint" -e PyLaunchBlueprint . | grep -v press-receipt || echo "CLEAN"
grep -rn --exclude-dir=.git -we plbp -we PLBP . | grep -v press-receipt || echo "CLEAN(app)"
head -3 CHANGELOG.md   # expect the stub
grep -c blueprint-press-dryrun bun.lock  # expect >=1 (regenerated workspace name)
```
Any survivor → PROBLEM entry + triage (Task 7 protocol).
- [ ] **Step 5: Forced re-press (receipt invalidation, new in v3.4)** — re-run apply WITHOUT `--force` → expect exit 2 (existing receipt); re-run WITH `--force` → expect exit 0 and a receipt referencing the new press (prior receipt invalidated). Record both exits.
- [ ] **Step 6: check-tools on the instance** → expect 0. Negative case: `PATH=/usr/bin:/bin uv run press check-tools --target …` (bun absent from PATH) → expect a missing-tool report, exit per its contract (0 with report or 2 — record actual; surprising behavior → PROBLEM entry).
- [ ] **Step 7: Instance stands on its own**

```bash
cd "$SCRATCH/blueprint-press-dryrun"
git add -A && git commit -m "chore: press to blueprint-press-dryrun identity"
mise trust && make check && just setup && just check
```
Expected: all pass (July PROBLEM-08 order: `mise trust` first). Guard must NOT fire on push-simulation (`git push --dry-run` to nowhere is skipped; the guard check happens for real in Task 13). Failures → PROBLEM entries.
- [ ] **Step 8: Log the battery** in Run 4 (steps table rows + any PROBLEMs), commit on a fresh branch, PR per D-v4-4 batching (may combine with Task 11's log rows).

---

### Task 13: Publish the instance (Phase 4 — user-gated)

**Interfaces:**
- Consumes: Task 12's pressed instance.
- Produces: `smorinlabs/blueprint-press-dryrun` (or user's chosen name) with CI evidence.

- [ ] **Step 1: Reader step — repo creation.** Present the user a reader-step block to create (or explicitly authorize creating) the repo, default `smorinlabs/blueprint-press-dryrun`, public, no template. Do not create it without that authorization (July PROBLEM-03).
- [ ] **Step 2: Push**

```bash
cd "$SCRATCH/blueprint-press-dryrun"
git remote add origin https://github.com/smorinlabs/blueprint-press-dryrun.git
git push -u origin main
```
Expected: push succeeds — the pre-push guard accepts the press receipt (Task 9's #505). A guard block here = PROBLEM entry (regression of the #505 contract).
- [ ] **Step 3: Watch CI** — `gh api repos/smorinlabs/blueprint-press-dryrun/actions/runs --jq '.workflow_runs[] | {name, status, conclusion}'`, at most once per 20s, bounded (stop after 30 min of no movement). Pre-listed classes to check on any red, before deep debugging: secret-scan first push, release-please credentials (expected red, not a finding), stale bun.lock, inherited maintenance workflows.
- [ ] **Step 4: Triage + log** every unexpected red as a PROBLEM entry (Task 7 protocol for fixes — template fixes go to the blueprint, engine fixes to template-press; the throwaway repo itself only gets hand-fixes needed to continue testing, each logged).

---

### Task 14: Close-out (Phase 5)

- [ ] **Step 1: Dispositions.** Every Run 4 PROBLEM entry ends fixed+merged / filed (issue URL) / accepted (reason). No dangling entries.
- [ ] **Step 2: Project state.** Flip P05 tasks/tests in `projects/P05-…md` and the trunk row status; final log commit + PR + merge.
- [ ] **Step 3: Cleanup with the user** (per-item consent):
  - campaign worktrees removed + pruned (only after their PRs merged);
  - stale July artifacts: `py-launch-blueprint-p1verify` worktree (uncommitted draft — superseded), `py-launch-blueprint-guard` (branch merged via Task 9?);
  - the user's live blueprint checkout divergence (ahead 1/behind 2) — surface, user reconciles;
  - throwaway repo: keep as evidence or delete;
  - template-press untracked handoff doc — surface only.
- [ ] **Step 4: Final report** — spec §5 exit criteria checked one by one, with the evidence (exit codes, PR numbers, CI run links).

---

## Self-Review (done at write time)

- **Spec coverage:** §1 pin → Global Constraints + Task 2; §2 expectations → Tasks 2/6; D-v4-1 → Task 7 Step 1B re-pin; D-v4-2/scope gate → Task 8; D-v4-3 → Tasks 12–13; D-v4-4 → Tasks 10/11 + batching notes; D-v4-5 → Task 7 exit condition (zero ignores); D-v4-6 → Tasks 2/6/7 logging; Phase 3 new-surface items (check-tools, reset/regen execution, P07 platform path, receipt invalidation) → Task 12 Steps 2–6; Phase 4 failure classes → Task 13 Step 3; Phase 5 → Task 14; PR #505 prerequisite → Task 9 ordering before 12/13. §6 out-of-scope respected (no provision/status, no G4 redesign, no init/ deletion inside this plan — the scope gate spawns a NEW plan if approved).
- **Placeholder scan:** the genuinely unknowable (Task 6 findings, Task 7 fix content) is structured as measurement + protocol with concrete commands and decision rules, not "TBD".
- **Consistency:** paths, branch name (`feat/press-conform`), pin (`bd52085`), scratch dir, and identity values match across tasks.
