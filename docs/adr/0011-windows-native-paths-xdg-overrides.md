# 0011. Windows-native default directories; XDG overrides win everywhere

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer (interactive + CodeRabbit review), implemented in PR #400
- **Related:** `core/paths.py`; `tests/core/test_paths.py`; `.github/workflows/ci.yml` (windows matrix)

## Context

`core/paths.py` hand-rolled XDG resolution, which is simply wrong on
Windows: config belongs in `%APPDATA%`, not `~/.config`. The obvious fix —
the `platformdirs` library — changes macOS behavior too (it returns
`~/Library/Application Support`, ignoring XDG), which would silently move
existing users' config and break the env-var override mechanism tests rely
on.

## Decision

Keep one override mechanism on every platform: **an XDG variable that is
set, absolute, and non-empty always wins.** Only the *defaults* become
platform-native on Windows, matching `platformdirs` shapes without taking
the dependency: config → `%APPDATA%\plbp`, data/state → `%LOCALAPPDATA%\plbp`
(Windows has no data/state split), cache → `%LOCALAPPDATA%\plbp\Cache`,
system config → `%PROGRAMDATA%`. `XDG_CONFIG_DIRS` splits on `;` under the
Windows flag. POSIX (including macOS) behavior is byte-identical to before.

The branch is selected by a module-level `_WINDOWS` flag so tests
monkeypatch it and exercise **both** branches on every OS; `windows-latest`
joins the CI test matrix as the real-platform check.

## Consequences

- Correct Windows behavior with zero new dependencies and zero macOS/Linux
  changes.
- `XDG_*` env vars remain a deterministic, cross-platform test/override
  mechanism (deliberately honored on Windows too).
- The first Windows CI run surfaced five POSIX-assuming tests (path
  literals, TOML backslash escapes, `0o600` asserts, cp1252 `read_text`),
  fixed as part of this decision's rollout.

## Alternatives considered

- **Adopt `platformdirs`** — rejected: breaks documented macOS XDG behavior
  and the uniform env-override contract; the needed subset is ~40 lines.
- **Windows-only `platformdirs` import** — rejected: two resolution systems
  with different override semantics is worse than one explicit branch.
