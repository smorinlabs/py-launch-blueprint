# P06 — Full conform: retire the embedded engine

**Status:** `[~]` in progress (v1.0.0)

Delete the embedded init/ engine and everything that polices it; cut CI
drift detection over to press verify; upgrade the press config to the
v3.6.0 feature set. Spec:
docs/superpowers/specs/2026-08-17-full-conform-design.md (blueprint-only
history — removed in generated projects). Closes #423.

### Tests & Tasks
- [ ] [P06-T01] Press-config upgrade (scan=boundary, snapshot regen +
      verify_exempt, [[remove]] set) — verify exit 0 on v3.6.0
- [ ] [P06-T02] Guard relocation (scripts/guard.sh, 3 conditions) + new
      guard test suite + Justfile re-point
- [ ] [P06-T03] CI cutover: press-verify.yml added; blueprint-guard.yml +
      init-integration.yml deleted; lefthook gates swapped
- [ ] [P06-T04] Delete init/; Justfile recipes; AGENTS.md + skill +
      POST_INIT rewrites
- [ ] [P06-TS01] just check green with no init steps; press verify +
      check-tools exit 0 (branch and fresh main)
- [ ] [P06-TS02] Acceptance re-press: pressed instance passes
      make check + just setup + just check with zero P05-class hand-fixes
- [ ] [P06-T05] Close-out: Run 5 log, #423 closed, cleanup with user
