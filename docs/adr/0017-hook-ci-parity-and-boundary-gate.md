# 0017. Hook ↔ CI parity: gate architectural boundaries in CI, mirror slow checks at pre-push

- **Status:** Accepted
- **Date:** 2026-06-14
- **Deciders:** maintainer (interactive review of the lefthook hook suite)
- **Related:** ADR-01 (lefthook), ADR-02 (two-layer secret scanning),
  ADR-03 (ty typecheck), ADR 0005 (toolchain provisioning); HEX-30
  (import-linter), HEX-31 (tach); WL-001 (locked tool versions);
  `lefthook.yml`, `.github/workflows/ci.yml`, `scripts/check-gitleaks.sh`

## Context

A holistic review of the commit-msg / pre-commit / pre-push hook suite
against the CI workflows surfaced a parity problem. The hooks are meant to
be a fast *local mirror* of CI; CI is the authority. Mapping every check
across the four surfaces (pre-commit, pre-push, CI, `just check`) exposed
gaps where a check ran in only one place:

| Check | pre-commit | pre-push | CI | `just check` |
|---|:--:|:--:|:--:|:--:|
| ruff check/format | ✅ | — | ✅ | ✅ |
| gitleaks | ✅ staged | ✅ range | (trufflehog) | — |
| editorconfig / yamllint / codespell | ✅ | — | ✅ | ✅ |
| bandit | — | ✅ | ✅ | — |
| **import-linter** (HEX-30) | — | ✅ | ❌ | ✅ |
| **tach** (HEX-31) | — | ❌ | ❌ | ✅ |
| **ty typecheck** | — | ❌ | ✅ | ✅ |
| **taplo TOML fmt** | — | ❌ | ✅ | ❌ |

The findings, in priority order:

1. **Architectural boundaries had no CI gate.** `import-linter` ran *only*
   in the pre-push hook and `tach` *only* in `just check` — neither was a
   job in `ci.yml`. A contributor who skips hooks (`git push --no-verify`)
   or never ran `just setup` (hooks silently no-op until installed) could
   merge import-layer or bounded-context violations with nothing catching
   them. The cheapest gate (a local hook) was load-bearing for a
   correctness property; the authoritative gate (CI) was blind.
2. **`ty` ran in no hook** — type errors surfaced only in CI, the same
   "should have been caught locally" class as the ruff lint failure that
   motivated adding ruff to pre-commit (PR #319, ITM-066).
3. **`taplo` TOML-format ran in no hook** — CI's `toml-format` job could
   fail on formatting that was never mirrored locally.
4. **Doc drift:** the `lefthook.yml` header comment claimed ITM-066 wired
   `ruff/ty/uv-export` at pre-commit; only ruff was actually wired.
5. **`gitleaks --range` skipped silently** (exit 0) when a branch had no
   upstream tracking ref — the first push of a new branch got no range-scan
   layer. The per-commit staged scans still covered those commits, so this
   was a defense-in-depth hole, not an open door.

## Decision

We will restore hook ↔ CI parity with CI as the authority:

1. **Add an `import-boundaries` job to `ci.yml`** running *both*
   `uv run lint-imports` (import-linter) and `uv run tach check`. It gates
   behind the `changes` detector (skips docs-only PRs, like `typecheck`)
   and is added to the `ci-ok` aggregate. **Also add `tach` to the pre-push
   hook** so the local mirror matches (import-linter was already there).
   Architectural boundaries are now enforced authoritatively in CI, with a
   fast local mirror at pre-push.
2. **Add `ty check` to the pre-push hook** (`uv run --extra web ty check
   src/py_launch_blueprint/`), matching CI's typecheck job. Pre-push, not
   pre-commit: it is a full-tree check, too slow to run per commit (same
   tier rationale as bandit).
3. **Add a staged-scoped `taplo` check to pre-commit** on `*.toml`, mirroring
   CI's `toml-format`. It guards for the binary (`just install-taplo`
   installs it; `just setup` runs that) and fails with guidance if absent,
   rather than skipping silently.
4. **Correct the `lefthook.yml` header comment** to describe what is
   actually wired.
5. **Give `gitleaks --range` a default-branch fallback**: when there is no
   `@{u}`, scan `origin/HEAD` (the remote default branch, falling back to
   `origin/main`)`..HEAD` instead of skipping. Only when neither ref exists
   does it warn and skip.

Tiering principle reaffirmed: pre-commit holds fast, staged-scoped checks;
pre-push holds the slower full-tree checks (bandit, ty, boundaries, init
integrity); CI is the authority and every correctness gate must exist there.

## Consequences

- Import-layer and bounded-context violations can no longer reach `main`
  via `--no-verify` or uninstalled hooks — `ci-ok` blocks them. The local
  pre-push hook still gives fast feedback before the round-trip.
- Type errors and TOML-format drift are caught locally, eliminating two
  more "push → CI red → fix → push again" cycles.
- Pre-push grows by `ty` (~a few seconds, full-tree) and `tach`; pre-commit
  grows by `taplo` on staged TOML only. The pre-commit/pre-push split keeps
  per-commit latency unchanged for non-TOML commits.
- New first-push branches now get a gitleaks range scan instead of a silent
  skip.
- Follow-on: keep the four surfaces in sync when adding a check — the parity
  matrix above is the checklist. `tach` and `import-linter` are now in three
  of the four surfaces (`just check`, pre-push, CI); `just check` remains the
  superset for local one-shot verification.

## Alternatives considered

- **Add `ty`/boundaries to pre-commit instead of pre-push** — rejected:
  both are full-tree and would tax every commit. The fast/slow tiering
  (ADR-01 era) deliberately keeps per-commit cost low.
- **Drop the pre-push hooks and rely on CI alone** — rejected: the hooks'
  value is fast local feedback before a network round-trip; CI being the
  authority does not make the mirror worthless.
- **Run `tach` only in CI, not pre-push** — rejected: import-linter is
  already at pre-push, so adding tach there costs little and keeps the two
  boundary tools together locally.
- **Leave `gitleaks --range` skipping with no upstream** — rejected: the
  fallback is cheap and closes the first-push gap; the staged layer alone
  was the only thing covering that window.
