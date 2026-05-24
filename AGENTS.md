Always read `CLAUDE.md` before making changes. It contains the detailed agent rules for this template.

## Canonical Commands

- Setup: `uv sync --all-extras --dev`
- Install editable dev package: `just install-dev`
- Format Python: `just format`
- Lint Python: `just lint`
- Typecheck: `just typecheck`
- Test: `just test`
- Full local gate: `just check`
- Pre-commit gate: `just pre-commit-run`
- Build distributions: `just build`
- Secret scan: `just check-gitleaks`

## Verification Flow

After code or configuration changes, run the smallest focused check first, then run `just check`. For hook or workflow changes, also run `just pre-commit-run` and any focused tool command that owns the changed file.

For release changes, run `uv build` and confirm the version in the tag, `pyproject.toml`, and package metadata agree.

## Maintenance Rule

When a generated project changes its command surface, update this file and `CLAUDE.md` in the same change so future agents get consistent instructions.
