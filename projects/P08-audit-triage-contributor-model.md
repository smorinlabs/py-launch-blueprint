# P08 — Audit-triage contributor model

Move the audit-triage bot from the standard Muse Spark tier to the
`muse-github-setup` default, `model_api/muse-spark-1.3-contributor`.

**References**

- **Trunk:** [PROJECTS.md](../PROJECTS.md)
- **Skill default:** `smorinlabs-skills` `plugins/muse-github/skills/muse-github-setup/SKILL.md`

**Status:** `[x]` merged in [PR #578](https://github.com/smorinlabs/py-launch-blueprint/pull/578) (merge commit `1ec77e4`, 2026-10-21).

### Scope

The model pin in the workflow, triage script, policy, and test, plus the
comments that describe the tier. Owner decision (2026-10-12): use the
contributor tier, which permits Meta to train on submitted content.

### Out of scope

repo-secrets consumer detection. It requires the OpenCode GitHub Action step,
so this CLI-based workflow keeps the manual `META_MUSE_CI_API_KEY` path.

### Tests & Tasks

- [x] [P08-TS01] Pin `model_api/muse-spark-1.3-contributor` in `test_policy_pins_model_and_organization`.
- [x] [P08-T01] Switch `audit-triage.yml`, `audit_triage.py`, and `policy.json` to the contributor model and correct the tier comments.
- [x] [P08-T02] Pass `just check`, open the PR, and merge. Review added a guard that refuses replays of pre-contributor snapshots before their helper runs.
