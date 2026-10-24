# Security Policy

## Supported Versions

Security fixes ship as patch releases on the latest major version.

| Version | Supported          |
| ------- | ------------------ |
| 4.x     | :white_check_mark: |
| < 4.0   | :x:                |

## Scope

py-launch-blueprint is a project template. In scope:

- The template's own code (`src/py_launch_blueprint/`), CLI, and web service
- The project scaffolding and generation scripts
- The GitHub Actions workflows and release pipeline in this repository

If you maintain a project generated from this template and find a flaw it
inherited from the template, please report it here so the fix reaches every
generated project. Vulnerabilities in code you added to your own project are
out of scope.

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.

1. **Preferred:** use GitHub's
   [private vulnerability reporting](https://github.com/smorinlabs/py-launch-blueprint/security/advisories/new).
2. **Fallback:** if you cannot use GitHub, email
   [steve.morin@gmail.com](mailto:steve.morin@gmail.com).

Include the affected version or commit, the steps to reproduce, and the
impact you expect.

Automated and AI-generated reports are welcome when they include a working
reproduction or proof of concept. Reports without one may be closed.

## What to Expect

- **Acknowledgment:** within 7 days, on a best-effort basis.
- **Investigation and fix:** we confirm the issue, develop a fix, and release
  it as a 4.x patch.
- **Disclosure:** we publish a GitHub Security Advisory, requesting a CVE when
  warranted, once the fix is released, or 90 days after the report at most.
  Reporters are credited unless they ask not to be.

## Security Controls

- **Code scanning:** CodeQL with the `security-extended` queries
  (`.github/workflows/codeql.yml`)
- **Dependency auditing:** pip-audit over the full locked dependency graph
  (`.github/workflows/dep-audit.yml`) and dependency review on pull requests
  (`.github/workflows/dependency-review.yml`)
- **Dependency updates:** Dependabot alerts and version updates
  (`.github/dependabot.yml`)
- **Secret scanning:** TruffleHog in CI, reporting verified secrets only
  (`.github/workflows/secret-scan.yml`), and gitleaks pattern scanning in the
  pre-commit and pre-push hooks (`lefthook.yml`)
- **Branch protection:** `main` requires passing status checks before merge

## Code Scanning Setup

This project ships **advanced** CodeQL setup: the analysis is configured in
`.github/workflows/codeql.yml` and `.github/codeql/codeql-config.yml`, kept in
version control so it is reviewed in pull requests and inherited by forks.

Because of this, GitHub's **default setup** for code scanning must stay
**disabled**. Enabling both makes the workflow fail at upload with
`CodeQL analyses from advanced configurations cannot be processed when the
default setup is enabled`. To check or disable default setup on your repo
(requires admin):

```bash
# check current state
gh api /repos/<OWNER>/<REPO>/code-scanning/default-setup

# disable it, handing control to the committed workflow
gh api --method PATCH /repos/<OWNER>/<REPO>/code-scanning/default-setup \
  -f state=not-configured
```
