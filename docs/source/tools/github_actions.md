# GitHub Actions

GitHub Actions runs automated checks and release workflows for Py Launch Blueprint.
The checked-in configuration lives in
[`.github/workflows/`](https://github.com/smorinlabs/py-launch-blueprint/tree/main/.github/workflows).

## Workflow configuration

The main workflow is
[`ci.yml`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/.github/workflows/ci.yml).
It runs for pushes to `main`, pull requests targeting `main`, and merge-queue
validation through the `merge_group` event.

The test matrix covers these combinations:

| Python version | Platforms |
|---|---|
| 3.13 | Linux, macOS and Windows |
| 3.14 | Linux |

Python 3.13 remains the minimum and setup default. Pull-request CI uses the
committed dependency lock; the separate weekly dependency canary tests both
Python versions with the latest allowed dependencies.

The main workflow also checks lint, types, import boundaries, package builds,
documentation and TOML formatting. Its `ci-ok` job reports the aggregate result.

For exact local commands, job conditions, the canary and release workflows, see
[Using CI/CD](../tasks/using_ci_cd.md). Use the checked-in workflows as the source
for executable configuration.

## Scheduled documentation repair

`audit-triage.yml` handles failed default-branch `weekly-audit` schedule runs and
explicit replays of failed schedule or dispatch runs. `MUSE_CI_ENABLED` retains
its existing activation role. The job uses the official Anthropic Claude Code
Action with Muse Spark 1.3 Contributor; unrelated Claude workflows are unchanged.

Trusted current-default tooling in `.github/scripts/muse_audit_triage.py` and
`.github/muse-audit-triage/` validates the target run before freezing its audited
commit and bounded log bundle. Read-only tools remain permitted. File edits are
restricted to ordinary documentation under `docs/`; the model cannot run project
commands or publish GitHub changes. The trusted validator checks scope and stages
literal paths before the workflow commits, pushes, and opens a PR for human review.
Page-level URL checks are reported on that PR; fragments still require review or
the next linkcheck. Ordinary PR CI runs without the Muse credential.

The model and 20,000-byte failure-bundle bound are recorded in
`.github/muse-audit-triage/policy.json`. The two vendored Python files are excluded
from local Ruff autofixes so they remain byte-identical to the shared skill.
Migration installation and live runtime acceptance are separate checks.
