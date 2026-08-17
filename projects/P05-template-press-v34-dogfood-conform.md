## [~] Project P05: Template-press v3.4 dogfood & conform (v1.0.0)
**Goal/Requirement**: Test template-press main @ bd52085 against this repo and
bring this repo's press config in sync — verify exit 0 via declarations, a
rebranded instance passes its own checks, and an instance publishes to a
throwaway repo. Spec: docs/superpowers/specs/2026-08-16-template-press-v34-dogfood-design.md
(spec and plan are blueprint-only history — `init/manifest.toml` removes them in
generated projects, so this link resolves only in the blueprint itself)

**Out of Scope**
- press provision/status (M6); G4 display-name design changes beyond using the
  shipped display_name field; deleting init/ unless the scope gate approves.

### Tests & Tasks
- [x] [P05-T01] Register project + open dogfood log Run 4
- [x] [P05-T02] Author press/press-source.toml (from scratch)
- [x] [P05-T03] Author regen scripts + press/press-rules.toml
- [x] [P05-T04] Satisfy init-system integrity for the press/ files
- [x] [P05-TS01] press check-tools exits 0 against the worktree
- [x] [P05-TS02] press verify reaches exit 0, zero ignores
- [x] [P05-T05] Scope gate decision recorded (user)
- [x] [P05-T06] PR #505 merged (user-confirmed)
- [x] [P05-T07] Round-1 PR merged; verify green from fresh main clone
- [x] [P05-TS03] Local rebrand battery passes (dry-run/apply/re-press/check-tools/instance checks)
- [x] [P05-T08] Instance published to throwaway repo; CI triaged (user-gated)
- [ ] [P05-T09] Close-out: dispositions, cleanup, report

### Deliverable
```bash
$ cd ~/c/template-press && uv run press verify --target <fresh plbp main clone>
$ echo $?
0
```

### Automated Verification
- `press verify` exit 0 with zero `[[verify.ignore]]` entries
- `press check-tools` exit 0
- pressed instance passes `make check` and `just check`

### Manual Verification
- Throwaway repo CI green (release-please may stay credential-gated red)

### Known coexistence limitation (deferred to the full-conform follow-up)
- Legacy `just init` rewrites the six tracked fields in `press/press-source.toml`
  but leaves `display_name` behind — `init/common.py` `BLUEPRINT_IDENTITY` has no
  display-name field (the legacy engine never handled the display name; Run-3
  PROBLEM-19). Resolved by the full conform (init/ retirement), decided at the
  Run 4 scope gate; not by extending the retiring engine.
