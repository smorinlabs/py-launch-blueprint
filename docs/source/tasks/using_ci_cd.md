# CI/CD with GitHub Actions

The checked-in workflows are the source of truth. CI validates the project;
release workflows publish only after their separate release triggers and setup.

## Pull-request and merge checks

The main workflow is `.github/workflows/ci.yml`. It runs for pull requests to
`main`, pushes to `main`, and the merge queue's `merge_group` event.

| Check | What it validates |
|---|---|
| `changes` | Detects code and packaging changes; documentation-only pull requests can skip the heavier jobs. |
| `lint` | Ruff lint and formatting checks using locked development tools. |
| `typecheck` | Types under `src/py_launch_blueprint/`, with the web extra installed. |
| `import-boundaries` | Import and module boundaries through import-linter and Tach. |
| `test` | Python 3.13 on Linux, macOS and Windows; Python 3.14 on Linux. Includes slow tests and excludes provisioned live tests. |
| `build-smoke` | Builds wheel and source archives, checks metadata, installs both and runs the CLI. |
| `docs` | Builds Sphinx documentation with warnings treated as errors. |
| `toml-format-check` | Checks TOML formatting. |
| `ci-ok` | Aggregates the preceding jobs for branch protection. A failed prerequisite cannot produce a successful aggregate. |

Coverage is collected and uploaded from the Linux/Python 3.13 test job.
Other test jobs validate runtime compatibility without uploading duplicate coverage.
Python 3.13 remains the minimum supported version and default development interpreter.

`.github/workflows/lint.yml` adds Actionlint, Bandit, spelling, EditorConfig
and YAML checks. Other workflows handle press conformance, secret scanning,
dependency review, CodeQL and container checks. Required check names come from
GitHub branch protection and repository rules; keep those rules aligned when
renaming or removing jobs.

## Reproduce the checks locally

Run these commands from the repository root:

```bash
just setup
just check
uv run --locked press verify
```

`just setup` installs the native tools, locked development/web dependencies and
Lefthook hooks. See [Setting Up Development](setting_up_development.md) for
fresh-machine setup.

To reproduce a CI test job, select its Python version and include slow tests:

```bash
uv sync --locked --python 3.14 --group dev --extra web
uv run --no-sync pytest -m "not live" -n auto
```

Use `3.13` instead to reproduce the minimum-version job. `--locked` requires the
committed dependency resolution; `--no-sync` then uses that prepared environment.
This switches the local environment's interpreter. Run `just setup` afterward
to restore the default selected by `.python-version`.

## Scheduled dependency checks

`.github/workflows/canary.yml` runs weekly and supports manual dispatch. It
tests Python 3.13 and 3.14 against newly resolved allowed dependency versions.
Its `uv sync --upgrade` is intentional: ordinary PR CI uses the lock, while
the canary detects future dependency incompatibilities. The canary is not a
required PR check and does not commit its temporary lock changes.

## Blueprint generation acceptance

Before rebranding, `.github/workflows/bootstrap-acceptance.yml` provisions the
native toolchain and runs `tests/bootstrap` weekly, on manual dispatch, and
for pull requests changing bootstrap-related files. It generates a fresh
application, runs its setup and checks, builds documentation and distributions,
and exercises its CLI and web health endpoint. It creates no GitHub repository
and publishes nothing. Generic CI continues to exclude these live tests.

Generation removes this blueprint-only workflow and its tests. Application
maintainers should add acceptance tests for their own application behavior.

## Releases

`.github/workflows/release-please.yml` prepares release PRs after pushes to
`main`. Tagged releases trigger `publish.yml`, which publishes to TestPyPI
before PyPI. `publish-container.yml` checks containers on PRs and publishes
stable release images separately. Configure the required services before the
first release; see [release instructions](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/RELEASE.md).
