# P07 — Template Press upgrade and Python 3.13 bootstrap

Adopt the released press and prove a usable generated project.

**References**

- **Trunk:** [PROJECTS.md](../PROJECTS.md)
- **Plan:** [Implementation and validation plan](../docs/superpowers/specs/2026-09-10-press-upgrade-and-python-313.md)
- **Validation:** [Acceptance evidence](../docs/superpowers/reviews/2026-09-10-press-upgrade-acceptance.md)
- **Release:** [Template Press 4.1.0](https://github.com/smorinlabs/template-press/releases/tag/v4.1.0)
- **Dependency gate:** [Template Press PR #131](https://github.com/smorinlabs/template-press/pull/131)

**Status:** `[x]` implementation complete in [PR #530](https://github.com/smorinlabs/py-launch-blueprint/pull/530) and [PR #532](https://github.com/smorinlabs/py-launch-blueprint/pull/532). T06–T10 are implemented on `ci/p07-bootstrap-followups`. Merge and release are outside the implementation tasks.

### Scope

Python 3.13 minimum, released Template Press integration, declared cleanup and
normalization, generated-project documentation and bootstrap, first-PR CI, and
an end-to-end generated-project acceptance test.

### Out of scope

Downstream application repositories and feedback logs, unrelated feature
requests, platform-policy changes, engine implementation, merge and publishing.

### Open questions

None requiring an owner decision at the start. Reproduced engine limitations
will be recorded separately from blueprint fixes.

### Tests & Tasks

- [x] [P07-TS01] Establish regression controls and a generated-project acceptance test.
- [x] [P07-T01] Align supported Python and the locked press release.
- [x] [P07-T02] Implement declared clean/edit/reset/removal and consistent Bun use.
- [x] [P07-T03] Update bootstrap instructions, generated docs, and first-PR CI.
- [x] [P07-T04] Pass source checks, then bootstrap and exercise a generated project.
- [x] [P07-T05] Commit and prepare the delivery PR with exact validation evidence.
- [x] [P07-T06] Add provisioned scheduled or manually dispatched bootstrap acceptance CI. Deferred from [review 3986130902](https://github.com/smorinlabs/py-launch-blueprint/pull/530#discussion_r3986130902); requires the native toolchain and network, and remains separate from generic CI's deliberate live-test exclusion.
- [x] [P07-T07] Evaluate and add Python 3.14 CI/canary coverage alongside the 3.13 minimum. Deferred from [review 3986130907](https://github.com/smorinlabs/py-launch-blueprint/pull/530#discussion_r3986130907); Python 3.14 lock resolution and the coverage gap already existed before this PR.
- [x] [P07-T08] Refresh the retained CI tutorial against actual workflow commands and supported platforms. Deferred from [review 3986130826](https://github.com/smorinlabs/py-launch-blueprint/pull/530#discussion_r3986130826); the Ubuntu-only example, macOS prose, wrong workflow extension, and floating tool examples predate this PR.
- [x] [P07-T09] Correct retained generated documentation for optional contributor automation. Deferred from [Copilot review 5175179607](https://github.com/smorinlabs/py-launch-blueprint/pull/530#pullrequestreview-5175179607); Sphinx pages advertise the removed workflow/roster. The separate claim that initialization requires an existing `.contributors.yml` was refuted against published contributors-please 1.4.3: `init` uses defaults when the file is absent. Verify generated links without enabling external automation.
- [x] [P07-T10] Use `anthropics/claude-code-action@v1` in both Claude workflows. The owner selected the maintained major-version tag on 2026-09-12, replacing the immutable-commit proposal from [review 3995193747](https://github.com/smorinlabs/py-launch-blueprint/pull/530#discussion_r3995193747). Preserve the automatic review credential gate and both workflows' permissions; validate workflow syntax and the configured/missing-secret controls.

### Follow-up recommendation and delivery

The owner delegated reassessment and implementation of the recommended P07
follow-ups. T06 through T09 are worth fixing now because they close missing
regression coverage or correct instructions that users encounter.

| Item | Decision | Delivered scope |
|---|---|---|
| P07-T06 | Implement | A dedicated weekly/manual/bootstrap-path PR workflow provisions the native toolchain and exercises the existing live generation test. Generation removes this workflow with its tests. |
| P07-T07 | Implement with limited extra CI | Add Linux/Python 3.14 to the normal test matrix and 3.14 to the weekly dependency canary. Keep Python 3.13 as the minimum and preserve its Linux/macOS/Windows coverage. |
| P07-T08 | Implement | Replace the obsolete CI example with the real workflow paths, triggers, jobs, locked commands and separate release/acceptance behavior. |
| P07-T09 | Implement | Document contributor tracking as an explicit opt-in for generated applications; remove links and claims that assume the retired roster/workflow exists. |
| P07-T10 | Implement owner-selected major tag | Use `anthropics/claude-code-action@v1` in the automatic review and interactive Claude workflows, retaining their existing configuration and permissions. |

The owner resolved T10 on 2026-09-12: follow the maintained `v1` tag and
receive updates within major version 1. A future major version requires an
explicit workflow-reference change. The earlier SHA-pinning proposal is closed
by this decision, with no deferred pinning requirement. The automatic review
still uses `CLAUDE_CODE_OAUTH_TOKEN` as its single configuration switch and
reports a successful skip when that secret is absent. Sources: Anthropic
[documented usage](https://github.com/anthropics/claude-code-action/releases/tag/v1)
and [major-tag release automation](https://github.com/anthropics/claude-code-action/blob/main/.github/workflows/release.yml).

Implementation commit `204961118e208969b751bb4644a76570c28938bc` passed source
checks (327 tests, 11 snapshots), Actionlint, Sphinx with warnings as errors,
and the full generated-application acceptance in 71.54 seconds (321 tests,
11 snapshots, setup/check, press verification, documentation, wheel/sdist,
CLI and real HTTP health). The exact Python 3.14 CI test command also passed
331 tests and 11 snapshots on macOS; three native PowerShell cases skip there.
GitHub runner execution is recorded on the follow-up PR. Scheduled/manual
triggers become available after the workflow lands on the default branch.

The additional normal CI runtime cell is Linux-only: the prior PR's three
Python 3.13 test jobs took 20, 17 and 24 seconds on Linux, macOS and Windows,
respectively. This change adds one runtime cell instead of doubling all three
platforms. These observations are not an estimate of future hosted CI cost.
All P07 implementation tasks are complete with the owner-approved T10
decision. The original bootstrap upgrade remains on PR #530, and the
follow-ups are on PR #532. Merge and publication remain separate from delivery.

### Notes

Owner decisions on 2026-09-11: retain the original large-file restriction;
run Claude review when its credential is present and otherwise report a clean
skip, with no separate enable variable; remove the inherited release-history
cutoff; ship neutral application introduction pages; and automatically remove
blueprint planning records while retaining an empty `projects/` directory after
setup. These refine the existing implementation tasks, without adding downstream
application work or external-service configuration.

The two subsequent owner-approved fixes at `7af9e0d` replace the generated setup
tutorial through `press/stubs/application-setup.md` and validate release-helper
JSON before writing. The source template tutorial is preserved. Source checks
passed 327 tests and 11 snapshots. The full generation test passed in 67.87
seconds with 321 generated tests and 11 snapshots, rendered application setup
guidance, independent verification, both distribution formats, CLI version, and
real HTTP health. All eight release-helper controls passed, including malformed
JSON and non-object roots that leave the input unchanged.

The agreed refinements at `c9992cb` passed source checks (319 tests and
11 snapshots), source verification/build, and Sphinx with warnings as errors.
The complete generation test passed in 71.97 seconds: 313 generated tests,
11 snapshots, independent verification, rendered documentation, both package
formats, CLI version, and real HTTP health. It verifies the release cutoff is
absent and an extra planning record is removed before setup recreates only
`projects/.gitkeep`. Credential controls verify both configured and missing
secrets without an authenticated Claude request.

The owner approved implementation on 2026-09-10 after Template Press PR #131
merged. The merge gate was met on 2026-09-11 at commit
`405a80f278c699b6d4d3504da011e78f9922b361`. The published baseline is Template
Press 4.1.0, verified through GitHub Releases and PyPI. The owner selected
Python 3.13 as the minimum supported version. Downstream application work and
feedback-log updates are excluded. Delivery is a reviewed PR, without merge or
publication authorization.

The pushed implementation at `64490e3` passed the full local bootstrap again
(62.36 seconds). GitHub Actions passed, including Python 3.13 on Linux, macOS
and Windows. Automated review results are tracked on PR #530.

The review repair at `2b5ba26` passed `just check` (317 tests and 11 snapshots),
Sphinx with warnings treated as errors, and the full generated-project
acceptance in 63.14 seconds. The generated application passed 311 tests and
11 snapshots, built both distributions, and served healthy CLI/HTTP behavior
at version `0.1.0`. Inverse controls verified stale-lock refusal, isolation
from system Bun, and LF/CRLF version-pin handling. Every original review
thread received an evidence reply and a confirmed resolution.
