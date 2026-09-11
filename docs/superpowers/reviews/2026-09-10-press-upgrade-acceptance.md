# P07 — Press upgrade acceptance

The updated blueprint generated a working CLI and web application with released
Template Press 4.1.0 and Python 3.13.14. The new application starts at version
0.1.0. This records local acceptance; current GitHub Actions results are on
[PR #530](https://github.com/smorinlabs/py-launch-blueprint/pull/530).

## Source and dependency gate

- Blueprint base: `c1216c6089f768ae0a3f3a465460d2d384f5fa44`.
- Initial implementation snapshot: `c9347573bdee6c7bf0fa3e46a3619c985181a753`.
- Current implementation and live acceptance snapshot: `c9992cb56c20e022193b856bc33c455a57dbaf95`. The complete live test passed in 71.97 seconds.
- Template Press PR #131 merged on 2026-09-11 at `405a80f278c699b6d4d3504da011e78f9922b361`.
- GitHub Releases and PyPI reported Template Press 4.1.0 as the latest published
  version. Its release predates PR #131. The tests used the published package,
  not an unreleased checkout.
- Native toolchain used Python 3.13.14, Bun 1.3.5 and the committed Python lock.
  The [public Flox catalog](https://api.flox.dev/api/v1/catalog/packages/bun?pageSize=1000) also lists Bun 1.3.5 for all four manifest systems,
  with available builds and no broken/insecure flag. Full Flox activation was
  not exercised; `flox show` stalled locally, so availability was verified via
  the catalog's read-only package endpoint.

## Results

| Check | Outcome |
|---|---|
| Source `just setup` | Passed; locked dev/web environment and hooks installed; frozen Bun install left its lock unchanged |
| Source `just check` | 319 passed, 3 PowerShell cases skipped on macOS, 5 slow/live tests deselected; 11 snapshots passed; lint, types, boundaries, spelling and EditorConfig passed |
| Source `press verify --target .` | Passed after committing the removal declarations and their target directories |
| Source `uv build` | Wheel and source distribution built at blueprint version 2.4.2 |
| Source Sphinx build with `-W` | Passed with warnings treated as errors |
| Bun regression controls | Old script accepted wrong Bun and replaced the lock; fixed script preserved the lock for wrong/missing Bun and regenerated with supported Bun |
| Generated `just setup` and `just check` | Passed; 313 tests passed, 3 skipped, 4 deselected; 11 snapshots passed |
| Generated `press verify` | Passed on the staged generated tree |
| Generated version and build | Project metadata, release manifest, editable lock entry, CLI and web report 0.1.0; wheel and source distribution built |
| Generated release configuration | Inherited `bootstrap-sha` removed; all other settings preserved apart from the expected package-name rewrite |
| Generated application documentation | Introduction pages match neutral stubs; Sphinx builds with `-W`; rendered homepage has no template-marketing title |
| Generated planning scaffold | Extra `P08` control and all existing records removed; setup restores only `projects/.gitkeep` |
| Claude credential controls | Actual configuration shell succeeds for present and absent synthetic credentials; absence prints the skip message; no credential reaches logs; checkout/review are gated on the result |
| Generated CLI | `harborctl --help` and `harborctl --version` passed |
| Generated web app | Real loopback HTTP `/healthz` returned `status=ok`, `version=0.1.0`, `python=3.13.14`; server shut down cleanly |
| Bootstrap skill | Static and session-backed loader checks passed for Claude Code and Codex; Bash blocks and embedded Python parsed; description unchanged |

The full bootstrap has an explicit 300-second timeout, with per-command
timeouts also enforced. The current run passed in 71.97 seconds. An initial
attempt failed because Template Press's declared-command environment dropped
the operator's cache overrides and the local sandbox blocked the default uv
cache. The same committed code passed with access to the uv and Bun caches.

[GitHub CI](https://github.com/smorinlabs/py-launch-blueprint/actions/runs/34564289149)
passed on the earlier `64490e3` snapshot, including Linux, macOS and Windows
Python 3.13, build installation smoke tests, documentation, types and lint.
Those results are historical; checks and automated reviews for the current
head are tracked separately on PR #530.

## What the acceptance test proves

`tests/bootstrap/test_template_press.py` archives committed blueprint content
into a new local Git repository. Its `origin` already names the destination,
matching GitHub template-instantiation behavior. It creates no remote resources.
Operator answers remain outside the target.

Cleanup preview leaves every file unchanged. Actual declared cleanup removes an
ignored source cache while retaining tracked files, a tracked ignored control,
and an unignored local control. After those controls are removed, rebrand
preview leaves a clean tree and apply produces a verified receipt for the new
identity. The receipt records both destination-origin fields.

The test checks removal of template research, the entire planning directory,
project rows, prototype code, and the active bootstrap skill. An additional
tracked planning record proves cleanup covers future files without a rule
for each filename. Setup recreates only the empty `.gitkeep` placeholder.
The Codex directory symlink
still resolves to a directory containing neutral documentation. Generated
README and POST_INIT files point to the retained project setup checklist.

The generated CLI and web application run after its own setup, complete local
checks, independent press verification and build. This supplies execution
evidence for the lockfile and help-snapshot regeneration commands that the
hermetic `press verify` sandbox explicitly exempts.

The agreed large-file policy is retained: only `docs/assets/` is exempt from
the 1 MB limit. The generated project passes its original large-file gate.
Claude review uses credential presence without a separate enable variable.
Missing credentials produce a successful skip; configured review failures
remain errors. Local credential controls use synthetic values and make no
authenticated Claude request.

An additional released-engine matcher probe detected `Py Launch Blueprint`,
`PyLaunchBlueprint`, `pyLaunchBlueprint`, and `PyLaunchBlueprintConfig` while
leaving `UnrelatedConfig` clear. No matcher-policy change was needed for these
cases; this is narrower evidence than a claim about every possible identifier.

## Reproduction

From a clean blueprint checkout, run `just setup`, then:

```bash
just check
uv run --locked press verify --target .
uv build
uv run --locked --group docs --extra web sphinx-build -W -b html docs/source docs/build/html
uv run --locked --extra web pytest tests/bootstrap -m live -s
```

The live test requires the native toolchain and network access for regeneration.
It is intentionally excluded from generic CI, which does not provision those
tools. The test must read a committed snapshot because directory removals reject
dirty or untracked members. Windows PowerShell behavior is exercised by the
regular Windows test matrix, not certified by the local macOS run.

Local evidence from this run is retained under
`/private/tmp/py-launch-blueprint-pr530-decisions-20260911/`, including
`source-check.log`, `source-docs.log`, `source-press-verify.log`, and
`acceptance-c9992cb-r2.log`. The generated project is under
`/private/tmp/blueprint-acceptance-c9992cb-r2/test_committed_blueprint_gener0/harbor-sample`.
These paths are local diagnostics; the committed test and commands are the
portable reproduction procedure.

Downstream application repositories, feedback logs, merges and publishing were
outside this run. External service configuration remains a project-owner choice.
