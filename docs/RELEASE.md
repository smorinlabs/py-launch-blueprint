# Release process

Release flow per ADR-05 + ADR-06 + ADR-07. See
`analysis/synthesis/items/ITM-060` for the full sequencing.

## Default flow (release-please)

1. Merge `feat:` / `fix:` / `perf:` commits to `main`.
2. The `release-please` workflow opens (or updates) a release PR
   proposing the next semver bump + a `CHANGELOG.md` entry. Its generated
   commit updates `pyproject.toml` and the editable root entry in `uv.lock`
   atomically, so the PR is internally consistent from its first revision.
3. Merge the release PR. release-please pushes a `v*` tag and publishes a
   GitHub Release.
4. The `publish` workflow fires on the tag:
   - `build` job: tag-reachability + version-matches-tag, then `uv build`.
   - `publish-testpypi`: OIDC upload to TestPyPI (env `testpypi`).
   - `publish-pypi`: OIDC upload to PyPI (env `pypi`).
5. Independently, `publish-container` fires when a stable GitHub Release is
   published. It builds and tests the web image, publishes the version to
   GHCR, verifies anonymous access, and reconciles the `latest` image tag.

## Public container publishing (GHCR)

The image is `ghcr.io/smorinlabs/py-launch-blueprint`. Generated projects use
their own lowercase GitHub owner/repository name. The existing Dockerfile
supplies the web service, runs as a non-root user, and listens on port `8000`.
The initial supported platform is `linux/amd64`.

| Reference | Meaning |
|---|---|
| `:X.Y.Z` | The image for the published stable release `vX.Y.Z`. The workflow never overwrites an existing version image. |
| `:latest` | The highest numeric stable version published to this container package, after its health and public-access checks pass. |
| `@sha256:…` | The exact manifest digest reported by the workflow. Prefer this for repeatable deployments. |

Draft releases, prereleases, and standalone tag pushes do not publish
containers. Publication begins with the next stable release whose tag includes
the workflow. Existing releases are not automatically backfilled. The PyPI
workflow continues to run independently on `v*` tag pushes.

The workflow checks the release tag against the event commit, the checkout,
`main` ancestry, `pyproject.toml`, and the editable root version in `uv.lock`.
A new version is built once and tested by its local image ID. The health
response must report `status: ok` and the released version. The same image is
pushed, and its registry configuration digest must match the digest recorded
by Buildx for that build. Docker's local image ID has different meanings on
its classic and containerd storage backends, so it is not used as a substitute
for the build's configuration digest. Deployment references use the registry
manifest digest.

The publisher uses GitHub Actions' automatic `GITHUB_TOKEN` with
`contents: read` and `packages: write`. No stored GHCR credential is needed.
The release-please App/PAT described below remains responsible for creating
release events that can trigger downstream workflows.

### First public publication

GHCR creates new packages as **Private**, including packages linked to public
repositories. The first run can therefore upload successfully and then fail
its anonymous pull check. The uploaded version is retained for the retry.

1. After that first upload, open
   [this repository](https://github.com/smorinlabs/py-launch-blueprint), select
   the container under **Packages**, then open **Package settings**.
2. Under **Danger Zone**, select **Change visibility**, choose **Public**,
   and confirm the package name. GitHub does not allow a public package to
   become private again. An organization owner must allow public package
   creation if organization policy currently forbids it.
3. Rerun the failed `publish-container` workflow from the release's Actions
   run. Success requires a pull by digest with an empty Docker credential
   configuration, followed by `latest` promotion. Each subsequent version
   uses the package's public visibility.

If the package existed before this workflow, verify that its **Manage Actions
access** grants this repository write access. A repository association alone
does not guarantee write access when permission inheritance is disabled.

### Retries and concurrent releases

An existing version is pulled by digest, its source/revision/version labels
are validated, and its health is tested again. It is never rebuilt or pushed
again. Registry authentication and transport errors stop publication; only an
explicit missing-manifest response permits a new build. A conflicting version
requires investigation and a new release, not an overwrite.

Version jobs serialize by release tag, so different releases can publish
independently. Promotion jobs serialize across the package. GitHub can cancel
an older pending promotion when another arrives. Every surviving promotion
reconciles the highest published stable version, including versions uploaded
by runs whose promotion was canceled. It copies the exact version manifest to
`latest` and refuses a version regression or conflicting digest. These rules
protect writes from this workflow; package administrators can still change
tags outside it, which is why deployment consumers should pin digests.

A canceled run may already have completed version publication. Check its
`publish-version` job and the later promotion's summary, or rerun the canceled
run. Retries are also the recovery path for transient registry/network failures.
GitHub reruns execute the workflow from the original release tag, so a later
workflow fix on `main` does not repair an old release run. Use a new stable
release containing that fix. There is no arbitrary-ref publishing dispatch.

Pull requests and merge queues run a build and smoke test without registry
credentials. The release job always repeats the container check before a new
publication. The standalone `container-check` job is not automatically a
required branch-protection check; selecting it as a required check is a
separate repository setting.

References: [GitHub container authentication and image operations](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry),
[package visibility](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility),
[workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).

## Disabling release-please (downstream projects)

If a generated project doesn't want PR-driven version proposals:

```bash
# Rename to disable:
mv .github/workflows/release-please.yml .github/workflows/release-please.yml.disabled
# Then bump [project] version manually before tagging:
$EDITOR pyproject.toml
uv lock
$EDITOR .release-please-manifest.json
git tag -a v1.2.3 -m "v1.2.3"
git push origin v1.2.3
```

The `publish` workflow still fires on the tag and uploads to PyPI.
To publish the container too, publish a stable GitHub Release for that tag.
Keep the package, lockfile, and release manifest versions consistent before
committing and tagging.

## Token setup

release-please must authenticate with a token that can **both** open PRs and
trigger downstream workflows (so merging the release PR fires `publish.yml`).
`GITHUB_TOKEN` does neither reliably — it never re-triggers other workflows, and
org policy can block it from opening PRs — so it is **not** used. Configure one
of these two mechanisms instead:

1. **GitHub App (preferred).** Create a GitHub App with **Contents** and
   **Pull requests: write**, install it on this repo, then add two secrets:
   - `RELEASE_PLEASE_CLIENT_ID` — the App's Client ID (e.g. `Iv23li...`)
   - `RELEASE_PLEASE_PRIVATE_KEY` — the App's private key (`.pem` contents)

   The workflow mints a short-lived installation token from these.

2. **Fallback PAT.** Create a fine-grained Personal Access Token scoped to this
   repo with **Contents** and **Pull requests: write**, stored as the
   `RELEASE_PLEASE_APP_TOKEN` secret.

With neither configured, release-please fails fast rather than silently
producing a release that can't publish.

## First-release cutover (one-time)

Template generation starts `pyproject.toml`, the editable `uv.lock` entry, and
`.release-please-manifest.json` at `0.1.0`. It removes the source repository's
`bootstrap-sha` from `release-please-config.json`: a fresh repository has its
own commit history, so it must not inherit another repository's release cutoff.

Configure the release credentials above before enabling publication. After the
initialization PR lands, release-please considers this repository's commits and
proposes the next version when it finds releasable changes. Initializing the
version files does not itself publish a release.

For an existing project adopting release-please, seed the manifest with that
project's current version. Set an optional `bootstrap-sha` only when you need
to exclude older commits, and choose a full commit ID from that repository.
See the [release-please bootstrap reference](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md#bootstrapping).
