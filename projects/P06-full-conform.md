# P06 — Full conform: retire the embedded engine

**Status:** `[x]` completed (v1.0.0) — merged as PR #521 (986eafa7), 2026-08-17

Delete the embedded init/ engine and everything that polices it; cut CI
drift detection over to press verify; upgrade the press config to the
v3.6.0 feature set. Spec:
docs/superpowers/specs/2026-08-17-full-conform-design.md (blueprint-only
history — removed in generated projects). Closes #423.

### Tests & Tasks
- [x] [P06-T01] Press-config upgrade (scan=boundary, snapshot regen +
      verify_exempt, [[remove]] set) — verify exit 0 on v3.6.0
- [x] [P06-T02] Guard relocation (scripts/guard.sh, 3 conditions) + new
      guard test suite + Justfile re-point
- [x] [P06-T03] CI cutover: press-verify.yml added; blueprint-guard.yml +
      init-integration.yml deleted; lefthook gates swapped
- [x] [P06-T04] Delete init/; Justfile recipes; AGENTS.md + skill +
      POST_INIT rewrites
- [x] [P06-TS01] just check green with no init steps; press verify +
      check-tools exit 0 (branch and fresh main)
- [x] [P06-TS02] Acceptance re-press: pressed instance passes
      make check + just setup + just check with zero P05-class hand-fixes
- [x] [P06-T05] Close-out: Run 5 log, #423 closed, cleanup with user
