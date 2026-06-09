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
- [`.github/SECURITY.md`](.github/SECURITY.md) — security controls + CodeQL setup.

Legend: **Default** = how the template ships. Each item is a checkbox so you can
track what you've decided.

---

## 1. Decisions — features to include or drop

Optional capabilities. For each, decide **keep** or **remove**; the "to remove"
column lists what to delete if you don't want it. Anything you keep has matching
setup in [§2](#2-checks--configuration).

### CI / quality gates (recommended: keep all)

- [ ] **Core CI** (lint, format, type-check, tests, coverage) — *Default: on.*
      Files: `.github/workflows/ci.yml`, `_checks.yml`. Removing this removes the
      point of the template; keep it.
- [ ] **Pre-commit/-push hooks** (lefthook: commitlint, gitleaks, formatting) —
      *Default: on.* File: `lefthook.yml`. Remove the file to disable local hooks.
- [ ] **Conventional Commits enforcement** (commitlint) — *Default: on.* Files:
      `.github/workflows/commitlint.yml`, `commitlint.config.mjs`. Note:
      release-please depends on conventional commits; dropping this weakens it.
- [ ] **Lint suite extras** (actionlint, yamllint, codespell, editorconfig-check,
      large-file-guard) — *Default: on.* Files: the like-named workflows. Drop
      individually if noisy.

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

- [ ] **Experiment / benchmarking harness** — the template's own tooling-matrix
      experiments, not part of a downstream app. Files:
      `.github/workflows/{flox-*,mise-*,trad-suite,experiment-driver}.yml`,
      `.github/actions/provision-*`. `just init` removes most blueprint-only
      pieces; delete any that remain.
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

- [ ] **Branch protection** on `main`: require PR reviews, require status checks
      (e.g. `ci`, `commitlint`, `codeql`), and (optionally) linear history. The
      template assumes a protected `main` with required reviews.
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

- **API token** — provide via `--token`, the `PY_TOKEN` env var, or
  `pylb config set token <TOKEN>` (writes the XDG config file at mode `0600`).
- **Manual publish fallback** — `cp .pypirc.template ~/.pypirc`, fill in PyPI
  tokens, `chmod 600 ~/.pypirc` (only needed if OIDC publishing is unavailable).

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
