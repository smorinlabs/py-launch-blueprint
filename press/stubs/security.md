# Security Policy

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests. Use GitHub's private vulnerability reporting
from this repository's **Security** tab instead.

Include the affected version or commit, the steps to reproduce, and the
impact you expect.

## Code Scanning Setup

This project ships **advanced** CodeQL setup: the analysis is configured in
`.github/workflows/codeql.yml` and `.github/codeql/codeql-config.yml`, kept in
version control so it is reviewed in pull requests.

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
