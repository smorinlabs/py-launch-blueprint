# P07 — Template Press upgrade and Python 3.13 bootstrap

Adopt the released press and prove a usable generated project.

**References**

- **Trunk:** [PROJECTS.md](../PROJECTS.md)
- **Plan:** [Implementation and validation plan](../docs/superpowers/specs/2026-09-10-press-upgrade-and-python-313.md)
- **Validation:** [Acceptance evidence](../docs/superpowers/reviews/2026-09-10-press-upgrade-acceptance.md)
- **Release:** [Template Press 4.1.0](https://github.com/smorinlabs/template-press/releases/tag/v4.1.0)
- **Dependency gate:** [Template Press PR #131](https://github.com/smorinlabs/template-press/pull/131)

**Status:** `[~]` implementation and local acceptance complete; delivery PR pending.

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
- [ ] [P07-T05] Commit and prepare the delivery PR with exact validation evidence.

### Notes

The owner approved implementation on 2026-09-10 after Template Press PR #131
merged. The merge gate was met on 2026-09-11 at commit
`405a80f278c699b6d4d3504da011e78f9922b361`. The published baseline is Template
Press 4.1.0, verified through GitHub Releases and PyPI. The owner selected
Python 3.13 as the minimum supported version. Downstream application work and
feedback-log updates are excluded. Delivery is a reviewed PR, without merge or
publication authorization.
