# P07 — Template Press upgrade and Python 3.13 bootstrap

Adopt the released press and prove a usable generated project.

**References**

- **Trunk:** [PROJECTS.md](../PROJECTS.md)
- **Plan:** [Implementation and validation plan](../docs/superpowers/specs/2026-09-10-press-upgrade-and-python-313.md)
- **Validation:** [Acceptance evidence](../docs/superpowers/reviews/2026-09-10-press-upgrade-acceptance.md)
- **Release:** [Template Press 4.1.0](https://github.com/smorinlabs/template-press/releases/tag/v4.1.0)
- **Dependency gate:** [Template Press PR #131](https://github.com/smorinlabs/template-press/pull/131)

**Status:** `[~]` implementation delivered in [PR #530](https://github.com/smorinlabs/py-launch-blueprint/pull/530); deferred review follow-ups remain. Merge and release are outside the implementation tasks.

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
- [ ] [P07-T06] Add provisioned scheduled or manually dispatched bootstrap acceptance CI. Deferred from [review 3986130902](https://github.com/smorinlabs/py-launch-blueprint/pull/530#discussion_r3986130902); requires the native toolchain and network, and remains separate from generic CI's deliberate live-test exclusion.
- [ ] [P07-T07] Evaluate and add Python 3.14 CI/canary coverage alongside the 3.13 minimum. Deferred from [review 3986130907](https://github.com/smorinlabs/py-launch-blueprint/pull/530#discussion_r3986130907); Python 3.14 lock resolution and the coverage gap already existed before this PR.
- [ ] [P07-T08] Refresh the retained CI tutorial against actual workflow commands and supported platforms. Deferred from [review 3986130826](https://github.com/smorinlabs/py-launch-blueprint/pull/530#discussion_r3986130826); the Ubuntu-only example, macOS prose, wrong workflow extension, and floating tool examples predate this PR.
- [ ] [P07-T09] Correct retained generated documentation for optional contributor automation. Deferred from [Copilot review 5175179607](https://github.com/smorinlabs/py-launch-blueprint/pull/530#pullrequestreview-5175179607); Sphinx pages advertise the removed workflow/roster. The separate claim that initialization requires an existing `.contributors.yml` was refuted against published contributors-please 1.4.3: `init` uses defaults when the file is absent. Verify generated links without enabling external automation.

Tasks P07-T06 through P07-T09 are tracked follow-ups, not merge requirements
for the Python 3.13 / Template Press 4.1.0 upgrade. The delivered implementation
tasks above remain complete; the trunk stays open to keep follow-ups visible.
The owner reaffirmed on 2026-09-11 that these four items belong in a separate
CI and documentation follow-up, after the two approved bootstrap fixes.

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
