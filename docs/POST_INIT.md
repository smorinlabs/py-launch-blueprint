# Post-Init Configuration — Decisions & Checklist

A single place to track everything that needs a **decision** or **configuration**
after you create a project from this template (`gh repo create --template …`,
then `just init` to rebrand). It is a *living registry*: as features are added
to the template, add a row here so downstream forks know they exist and how to
turn them on or off.

This complements the automated paths and the deeper per-topic docs — it does not
replace them:

- `just init` — rebrands identity (name, owner, package) across the repo.
- `just post-init` — automates the publishing / Codecov / Read the Docs wiring.
- [`RELEASE.md`](RELEASE.md) — the release/publish flow in detail.
- [`.github/SECURITY.md`](../.github/SECURITY.md) — security controls + CodeQL setup.

Legend: **Default** = how the template ships. Each item is a checkbox so you can
track what you've decided.

---

## 1. Decisions — features to include or drop

Optional capabilities. For each, decide **keep** or **remove**; the "to remove"
column lists what to delete if you don't want it. Anything you keep has matching
setup in [§2](#2-checks--configuration).

### CI / quality gates (recommended: keep all)

- [ ] **Core CI** (lint, format, type-check, tests, coverage) — *Default: on.*
      Files: `.github/workflows/ci.yml`. Removing this removes the
      point of the template; keep it.
- [ ] **Pre-commit/-push hooks** (lefthook: commitlint, gitleaks, formatting) —
      *Default: on.* File: `lefthook.yml`. Remove the file to disable local hooks.
- [ ] **Conventional Commits enforcement** (commitlint) — *Default: on.* Files:
      `.github/workflows/commitlint.yml`, `commitlint.config.mjs`. Note:
      release-please depends on conventional commits; dropping this weakens it.
- [ ] **Lint suite extras** (actionlint, yamllint, codespell, editorconfig-check,
      large-file-guard) — *Default: on.* Files: `.github/workflows/lint.yml`
      (one job per tool) + `.github/workflows/large-file-guard.yml`. Drop
      individual jobs if noisy.

### Security (recommended: keep)

- [ ] **CodeQL code scanning** (advanced setup, `security-extended`) —
      *Default: on.* Files: `.github/workflows/codeql.yml`,
      `.github/codeql/codeql-config.yml`. Removing both disables CodeQL; you can
      instead switch to GitHub's *default setup* (see §2).
- [ ] **Secret scanning** (TruffleHog in CI + gitleaks at hooks) — *Default: on.*
      Files: `.github/workflows/secret-scan.yml`, `.gitleaks.toml`,
      `scripts/check-gitleaks.sh`. Keep.
- [ ] **Dependency review** (PR diff vuln/license check) — *Default: on.* File:
      `.github/workflows/dependency-review.yml`. Free on public repos.
- [ ] **Manual PR security review** (Safety CLI, on-demand) — *Default: present,
      needs a secret.* File: `.github/workflows/manual-pr-security-scan.yml`.
      Remove if you don't have a Safety account.
- [ ] **CLA gate** (`license/cla` check via the external **cla-assistant.io**
      app) — *Default: connected on the upstream repo.* There is **no in-repo
      workflow/file** — it's an external app. A fork starts with it *off* until
      you connect the app. Decide: connect it (and add a `CLA.md` agreement), or
      leave it off.

### Release & distribution (decide per project)

- [ ] **release-please** (PR-driven version bumps + changelog) — *Default: on,
      needs auth.* Files: `.github/workflows/release-please.yml`,
      `release-please-config.json`, `.release-please-manifest.json`. To disable:
      rename the workflow `.disabled` (see `RELEASE.md`).
- [ ] **Publish to PyPI** (OIDC trusted publishing on `v*` tags) — *Default: on,
      needs PyPI + environment config.* File: `.github/workflows/publish.yml`,
      `.pypirc.template` (manual fallback). Remove the workflow if the project is
      not distributed on PyPI.
- [ ] **Read the Docs hosting** — *Default: configured, needs RTD import.* File:
      `.readthedocs.yaml` + `docs/`. Remove if you don't host docs on RTD.
- [ ] **Codecov coverage reporting** — *Default: on, tokenless on public repos.*
      File: `.codecov.yml`; upload step in `ci.yml`. Remove the upload step +
      file to disable.

### Community / project automation (optional)

- [ ] **Contributors automation** (contributors-please app generates
      `CONTRIBUTORS.md`) — *Default: present, needs secrets.* Files:
      `.github/workflows/update-contributors.yml`, `.contributors.yml`,
      `.contributors.jsonl`. Remove all three to disable.
- [ ] **Funding / Sponsor button** — *Default: points at the template author.*
      File: `.github/FUNDING.yml`. Set your own handle or delete the file.
- [ ] **Issue/PR templates, Code of Conduct, Contributing** — *Default: on.*
      Files under `.github/`. Edit to taste.

### Template-only machinery (recommended: remove for a real project)

- [ ] **Blueprint guard** — *Default: removed by `just init`.* File:
      `.github/workflows/blueprint-guard.yml`. It is blueprint-only.

---

## 2. Checks & Configuration

For each feature you kept, the concrete wiring: secrets, environments, external
services, repo settings, and the commands/scripts to run.

### 2.1 GitHub Actions secrets

Add under **Settings → Secrets and variables → Actions** (or org-level).

| Secret | Required by | Needed when | How to get it |
|---|---|---|---|
| `RELEASE_PLEASE_APP_ID` + `RELEASE_PLEASE_PRIVATE_KEY` | `release-please.yml` | Using release-please (preferred auth) | Create a GitHub App with **Contents + Pull requests: write**, install it, use its App ID + a generated private key. |
| `RELEASE_PLEASE_APP_TOKEN` | `release-please.yml` | release-please fallback (instead of the App) | Fine-grained PAT with **Contents + Pull requests: write**. |
| `CONTRIBUTORS_PLEASE_APP_ID` + `CONTRIBUTORS_PLEASE_PRIVATE_KEY` + `CONTRIBUTORS_PLEASE_PAT` | `update-contributors.yml` | Using contributors automation | From the contributors-please GitHub App install (+ a PAT). |
| `SAFETY_API_KEY` | `manual-pr-security-scan.yml` | Using the manual Safety review | A Safety (safetycli.com) account API key. |
| `CODECOV_TOKEN` | `ci.yml` upload | **Private repos only** (public repos upload tokenless via OIDC) | From the repo page on codecov.io. |

> `GITHUB_TOKEN` is provided automatically — no setup. PyPI/TestPyPI publishing
> uses **OIDC trusted publishing**, so it needs **no secret** (see §2.3).

### 2.2 GitHub Environments

Create under **Settings → Environments**. The publish environments can be
provisioned automatically:

```bash
# Creates the `pypi` + `testpypi` environments, restricted to main + release/*
init/setup-github-environments.sh <owner>/<repo>
# Requires: gh CLI authenticated with admin (repo scope / Administration: write)
```

| Environment | Used by | Notes |
|---|---|---|
| `pypi` | `publish.yml` | Production PyPI publish. Pair with the PyPI trusted-publisher config in §2.3. |
| `testpypi` | `publish.yml` (currently commented out) | TestPyPI smoke test; enable by uncommenting the job. |
| `security-review` | `manual-pr-security-scan.yml` | Scopes the `SAFETY_API_KEY` secret to a gated environment. |

### 2.3 External services to connect

| Service | Action | Config in repo |
|---|---|---|
| **CodeQL** | In **Settings → Code security**, ensure **default setup is OFF** (advanced setup is mutually exclusive with it — see `.github/SECURITY.md`). To verify/disable: `gh api /repos/<owner>/<repo>/code-scanning/default-setup` then `gh api --method PATCH … -f state=not-configured`. | `codeql.yml`, `codeql-config.yml` |
| **PyPI trusted publisher** | On pypi.org (and test.pypi.org) → your project → *Publishing* → add a GitHub Actions trusted publisher: this repo, workflow `publish.yml`, environment `pypi` (`testpypi`). | `publish.yml` |
| **Codecov** | Add the repo at codecov.io. Public repos need no token (OIDC). | `.codecov.yml` |
| **Read the Docs** | Import the project at readthedocs.org; it reads `.readthedocs.yaml`. | `.readthedocs.yaml` |
| **Dependabot** | Enable **Dependabot version + security updates** in Settings; `dependabot.yml` does the rest. | `.github/dependabot.yml` |
| **release-please App** | Create/install the GitHub App (or set the PAT) per §2.1. | `release-please.yml` |
| **contributors-please App** | Install the app + set secrets per §2.1. | `update-contributors.yml` |
| **CLA assistant** | If keeping the CLA gate, connect the repo at cla-assistant.io and point it at your agreement. | *(external; no repo file)* |
| **Sponsor button** | Set the `github:` handle in `.github/FUNDING.yml` (or delete it). | `.github/FUNDING.yml` |

### 2.4 Repository settings (away from defaults)

Under **Settings**:

- [ ] **Branch protection** on `main`: require status checks anchored on the
      aggregate gates — `ci-ok` (all of `ci.yml`), `integration-ok`, `guard`,
      `unit-tests`, `commitlint (humans)`, plus the `lint.yml` job names
      (`actionlint`, `bandit`, `codespell`, `editorconfig-check`, `yamllint`;
      safe to require — they report *skipped* rather than never reporting).
      Avoid listing individual `ci.yml` jobs: `ci-ok` subsumes them and its
      `needs:` list is versioned in-repo, so job renames never desync the
      settings. Full command in [§3.6](#36-branch-protection).
- [ ] **Actions → General → Workflow permissions**: enable **"Allow GitHub
      Actions to create and approve pull requests"** (release-please and
      Dependabot open PRs).
- [ ] **Code security → Code scanning default setup: OFF** (CodeQL advanced).
- [ ] **Code security → Dependabot**: enable version + security updates.
- [ ] **Code security → Private vulnerability reporting**: enable (referenced by
      `SECURITY.md`).
- [ ] **General → Pull requests**: pick a merge strategy consistent with
      conventional commits (squash with a conventional title is a good default).

### 2.5 Local development setup (per clone)

```bash
# Toolchain
scripts/install-bun.sh          # bun (used to install lefthook + commitlint deps)
scripts/install-lefthook.sh     # wires git hooks from lefthook.yml
scripts/install-gitleaks.sh     # local secret scanning

# Python env
uv sync --group dev             # dev dependencies (PEP 735)

# Sanity
just check                      # format + lint + typecheck + test
```

### 2.6 Application / runtime config

For the bundled CLI example (not repo infrastructure):

- **API token** — provide via `--token` or the `PLBP_TOKEN` env var (it is
  never stored in the config file; non-secret settings use
  `plbp config set <section>.<key> <value>`).
- **Manual publish fallback** — `cp .pypirc.template ~/.pypirc`, fill in PyPI
  tokens, `chmod 600 ~/.pypirc` (only needed if OIDC publishing is unavailable).

---

## 3. Settings to verify & set — one by one

Go through these in order. Each item names its **type** (repo setting · secret ·
environment · external service · file), a **Check** (how to see the current
state — `gh` CLI where one exists, otherwise the UI path), and **Set** (how to
apply the target). Skip any feature you dropped in [§1](#1-decisions--features-to-include-or-drop).
Replace `<owner>/<repo>` throughout; `gh` must be authenticated with repo admin.

### 3.1 Code scanning — if keeping CodeQL

- [ ] **CodeQL default setup must be OFF** · *repo setting* — advanced
      `codeql.yml` is rejected at SARIF upload if default setup is also enabled.
  - Check: `gh api /repos/<owner>/<repo>/code-scanning/default-setup --jq .state` → want `not-configured`
  - Set (if it returns `configured`): `gh api --method PATCH /repos/<owner>/<repo>/code-scanning/default-setup -f state=not-configured`

### 3.2 Actions permissions

- [ ] **Actions enabled** · *repo setting*
  - Check/Set: Settings → Actions → General → "Allow all actions and reusable workflows".
- [ ] **Allow Actions to create & approve PRs** · *repo setting* — release-please
      and Dependabot open PRs.
  - Check: `gh api /repos/<owner>/<repo>/actions/permissions/workflow --jq '{perm: .default_workflow_permissions, approve: .can_approve_pull_request_reviews}'`
  - Set: `gh api --method PUT /repos/<owner>/<repo>/actions/permissions/workflow -F default_workflow_permissions=write -F can_approve_pull_request_reviews=true`

### 3.3 Secrets

List what's present with `gh secret list -R <owner>/<repo>`, then set each one
you need (`gh secret set NAME -R <owner>/<repo>` prompts for the value).

- [ ] **`RELEASE_PLEASE_APP_ID` + `RELEASE_PLEASE_PRIVATE_KEY`** (or the
      `RELEASE_PLEASE_APP_TOKEN` PAT) · *secret* — if keeping release-please.
  - Set: `gh secret set RELEASE_PLEASE_APP_ID …` / `… RELEASE_PLEASE_PRIVATE_KEY < key.pem`
- [ ] **`CONTRIBUTORS_PLEASE_APP_ID` + `_PRIVATE_KEY` + `_PAT`** · *secret* — if
      keeping contributors automation.
- [ ] **`SAFETY_API_KEY`** · *environment secret* — if keeping the manual scan;
      scope it to the `security-review` environment:
      `gh secret set SAFETY_API_KEY --env security-review`
- [ ] **`CODECOV_TOKEN`** · *secret* — **private repos only** (public repos use
      tokenless OIDC).

### 3.4 Environments

- [ ] **`pypi` (and `testpypi`) exist** · *environment* — if publishing.
  - Check: `gh api /repos/<owner>/<repo>/environments --jq '.environments[].name'`
  - Set: `init/setup-github-environments.sh <owner>/<repo>`
- [ ] **`security-review` exists** · *environment* — if keeping the manual scan
      (created implicitly when you add its env secret, or via the script).

### 3.5 Dependabot & vulnerability settings

- [ ] **Dependabot alerts** · *repo setting*
  - Set: `gh api --method PUT /repos/<owner>/<repo>/vulnerability-alerts`
- [ ] **Dependabot security updates** · *repo setting*
  - Set: `gh api --method PUT /repos/<owner>/<repo>/automated-security-fixes`
- [ ] **Dependabot version updates** · *file + setting* — driven by
      `.github/dependabot.yml`; just ensure Dependabot is enabled for the repo.
- [ ] **Private vulnerability reporting** · *repo setting* — referenced by
      `SECURITY.md`.
  - Set: `gh api --method PUT /repos/<owner>/<repo>/private-vulnerability-reporting`
- [ ] **Secret scanning + push protection** · *repo setting (optional)* — GitHub
      native, complements TruffleHog/gitleaks. Settings → Code security.

### 3.6 Branch protection

- [ ] **Protect `main`** · *repo setting* — require status checks (contexts are
  **job names** as shown on a PR's checks tab, not workflow filenames).
  - Check: `gh api /repos/<owner>/<repo>/branches/main/protection --jq '.required_pull_request_reviews, .required_status_checks.contexts' 2>/dev/null || echo "unprotected"`
  - Set (recommended baseline — aggregate gates + always-reporting linters):

    ```bash
    gh api -X PUT /repos/<owner>/<repo>/branches/main/protection --input - <<'JSON'
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

  - Knobs: `strict: true` additionally forces every PR up-to-date with `main`
    before merge (safer, but every merge invalidates all other open PRs);
    `enforce_admins: true` removes the admin escape hatch; add
    `required_pull_request_reviews` once you have collaborators.

### 3.7 External services (UI / no `gh` check)

- [ ] **PyPI trusted publisher** · *external* — pypi.org → project → Publishing →
      add GitHub Actions publisher: this repo, `publish.yml`, env `pypi` (repeat
      on test.pypi.org for `testpypi`).
- [ ] **Codecov** · *external* — add the repo at codecov.io.
- [ ] **Read the Docs** · *external* — import the project at readthedocs.org.
      (Verify the webhook landed: `gh api /repos/<owner>/<repo>/hooks --jq '.[].config.url'`.)
- [ ] **release-please GitHub App** · *external* — install on the repo/org (or use the PAT).
- [ ] **contributors-please GitHub App** · *external* — install + set the §3.3 secrets.
- [ ] **CLA assistant** · *external* — connect the repo at cla-assistant.io and
      point it at your agreement (only if keeping the `license/cla` gate).

### 3.8 Repo metadata & merge strategy

- [ ] **Funding handle** · *file* — set `github:` in `.github/FUNDING.yml` or delete it.
- [ ] **Merge strategy** · *repo setting* — squash with a conventional title pairs
      well with commitlint + release-please.
  - Set: `gh api --method PATCH /repos/<owner>/<repo> -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false -F delete_branch_on_merge=true`

### 3.9 Local (per clone)

- [ ] Toolchain + hooks installed and env synced — see [§2.5](#25-local-development-setup-per-clone).

---

## Quick start (typical public OSS project)

1. `just init` → rebrand identity.
2. Remove template-only machinery (§1, last group).
3. Decide release/publish: keep release-please + `publish.yml`, set the
   release-please App secrets (§2.1), run `setup-github-environments.sh` (§2.2),
   add the PyPI trusted publisher (§2.3).
4. Connect Codecov + Read the Docs (§2.3).
5. Confirm CodeQL **default setup is OFF** (§2.3).
6. Set branch protection + Actions PR permissions (§2.4).
7. Decide CLA, contributors automation, funding (§1).
8. Local: run the `scripts/install-*` + `uv sync` steps (§2.5).
