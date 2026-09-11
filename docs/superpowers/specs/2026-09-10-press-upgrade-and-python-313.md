# P07 — Released press integration and Python 3.13 bootstrap

Status: owner-approved execution, in progress.

## Contract and baseline

The blueprint must support Python 3.13 and later and use the latest published
Template Press release. A fresh generated project must accept a new identity,
start at version 0.1.0, pass setup/check/build/verify, and run its CLI and web
application. All changes remain in this repository. No downstream application
or feedback log is part of this work. The delivery is a PR; merging and
publishing are separate actions.

Template Press PR #131 merged on 2026-09-11 as `405a80f`. GitHub and PyPI both
reported 4.1.0 as the latest release. That release predates #131's directory
advice and inventory optimization; the released package is the dependency and
acceptance baseline. Blueprint starts at `c1216c6`. Its locked press was 3.6.0,
its Python floor was 3.12, and `just setup` and baseline `just check` passed.

## Implementation

1. Set the Python floor, formatter/type-check targets, CI, images, development
   environments, and maintained user documentation to 3.13. Keep platform
   policy unchanged. Upgrade only the necessary locked dependencies.
2. Require Template Press 4.1.0 or newer and lock the tested release. Run
   bootstrap and conformance with that lock. Do not use a floating tool runner
   for hook/CI checks.
3. Declare cleanup of ignored artifacts under source package and test paths.
   Keep cleanup separate and previewable. Reset release metadata and use an
   edit to seed the project version before lock regeneration.
4. Remove blueprint-owned history. Reset README, POST_INIT and the project
   index to useful identity-free content. Preserve the general configuration
   checklist in PROJECT_SETUP. Remove the bootstrap SKILL.md and its dedicated
   test; retain a neutral companion README so its Codex symlink resolves.
5. Check Bun's supported version before removing either lockfile. Keep native,
   mise and Flox provisioning aligned. Use frozen installation for routine
   setup. An incompatible Bun must fail with the existing lock intact.
6. Update the bootstrap runbook to store answers outside the target, check
   tools, preview cleanup/rebrand, apply, format, validate, and open the initial
   PR from a branch. Scope recovery to the actual failed operation.
7. Supply commitlint PR-read permission and opt-in Claude review. Generic
   tests exclude unprovisioned live tests. Correct the asset allowlist and
   explain the actual visibility gates on security workflows.

## Reassessment boundaries

The prior record is input, not a list of automatic fixes. Correct setup already
installs the web extra. Contributor-history tests are removed when pressing.
Existing-code adoption, a new `just all` command, Dependabot policy, Markdown
formatter upgrades and Windows opt-in are outside this integration. PascalCase
verification is an engine question to probe without changing matcher policy.

## Validation

Focused controls cover wrong/missing Bun preserving lock contents and correct
Bun reaching regeneration; clean preview preserving every file, actual clean
removing only ignored artifacts; and successful press with an origin already
naming the destination. Assert receipt provenance, version/manifest/lock
agreement, disappearance of active template-only skills/history, and useful
retained setup links. Validate a second `press verify` on the generated tree.

Run all required source checks and build. Generate a local disposable repository
with fresh Git history and a destination origin. Press committed blueprint
content, run its setup and checks, invoke the generated CLI, and make a real
request to its local web app. Record exact commands, package versions, source
commits, results and limitations before preparing the PR.
