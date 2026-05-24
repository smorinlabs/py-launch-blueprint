# Release process

Release flow per ADR-05 + ADR-06 + ADR-07. See
`analysis/synthesis/items/ITM-060` for the full sequencing.

## Default flow (release-please)

1. Merge `feat:` / `fix:` / `perf:` commits to `main`.
2. The `release-please` workflow opens (or updates) a release PR
   proposing the next semver bump + a `CHANGELOG.md` entry.
3. Merge the release PR. release-please pushes a `v*` tag.
4. The `publish` workflow fires on the tag:
   - `build` job: tag-reachability + version-matches-tag, then `uv build`.
   - `publish-testpypi`: OIDC upload to TestPyPI (env `testpypi`).
   - `publish-pypi`: OIDC upload to PyPI (env `pypi`).
   - `sync-uv-lock` job (in release-please workflow) keeps `uv.lock` current.

## Disabling release-please (downstream projects)

If a generated project doesn't want PR-driven version proposals:

```bash
# Rename to disable:
mv .github/workflows/release-please.yml .github/workflows/release-please.yml.disabled
# Then bump [project] version manually before tagging:
$EDITOR pyproject.toml
git tag -a v1.2.3 -m "v1.2.3"
git push origin v1.2.3
```

The `publish` workflow still fires on the tag and uploads to PyPI.

## Token setup

Default token for the release-please job is `RELEASE_PLEASE_APP_TOKEN`
(GitHub App, needed so the merge of release-please's PR re-triggers
downstream workflows). Falls back to `GITHUB_TOKEN` if the secret is
not set — fine for single-repo use but won't re-trigger other workflows.

App setup: https://github.com/apps/release-please-action — install on
the repo and create a secret named `RELEASE_PLEASE_APP_TOKEN`.

## First-release cutover (one-time)

When this template lands in a fresh repo:

1. Ensure `[project] version` in `pyproject.toml` matches the latest
   release (or `0.0.0` if none). For this template the static cutover
   is `1.0.0`.
2. Update `.release-please-manifest.json` to `{".": "<that version>"}`.
3. Update `release-please-config.json` `bootstrap-sha` to the merge
   commit that lands the release-please cluster.
4. Push to main. release-please opens its first PR.
