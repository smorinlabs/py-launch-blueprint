# P08 — Audit-triage contributor model

Move the audit-triage bot from the standard Muse Spark tier to the
`muse-github-setup` default, `model_api/muse-spark-1.3-contributor`.

**References**

- **Trunk:** [PROJECTS.md](../PROJECTS.md)
- **Skill default:** `smorinlabs-skills` `plugins/muse-github/skills/muse-github-setup/SKILL.md`

**Status:** `[~]` implementation on `fix/audit-triage-contributor-model`.

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
- [ ] [P08-T02] Pass `just all`, open the PR, and merge.
