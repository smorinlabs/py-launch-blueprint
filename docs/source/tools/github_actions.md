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
