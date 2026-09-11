# P07 — Press upgrade acceptance

The updated blueprint generated a working CLI and web application with released
Template Press 4.1.0 and Python 3.13.14. The new application starts at version
0.1.0. This records local acceptance and the passing GitHub Actions run on
[PR #530](https://github.com/smorinlabs/py-launch-blueprint/pull/530).

## Source and dependency gate

- Blueprint base: `c1216c6089f768ae0a3f3a465460d2d384f5fa44`.
- Initial implementation snapshot: `c9347573bdee6c7bf0fa3e46a3619c985181a753`.
- Final implementation and live acceptance snapshot: `64490e3efa9e4a39db66b9c9b94f74e9d6044618`. The repeated live test passed in 62.36 seconds.
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
| Source `just check` | 315 passed, 3 PowerShell cases skipped on macOS, 5 slow/live tests deselected; 11 snapshots passed; lint, types, boundaries, spelling and EditorConfig passed |
| Source `press verify --target .` | Passed after committing the removal declarations and their target directories |
| Source `uv build` | Wheel and source distribution built at blueprint version 2.4.2 |
| Source Sphinx build with `-W` | Passed with warnings treated as errors |
| Bun regression controls | Old script accepted wrong Bun and replaced the lock; fixed script preserved the lock for wrong/missing Bun and regenerated with supported Bun |
| Generated `just setup` and `just check` | Passed; 309 tests passed, 3 skipped, 4 deselected; 11 snapshots passed |
| Generated `press verify` | Passed on the staged generated tree |
| Generated version and build | Project metadata, release manifest, editable lock entry, CLI and web report 0.1.0; wheel and source distribution built |
| Generated CLI | `harborctl --help` and `harborctl --version` passed |
| Generated web app | Real loopback HTTP `/healthz` returned `status=ok`, `version=0.1.0`, `python=3.13.14`; server shut down cleanly |
| Bootstrap skill | Static and session-backed loader checks passed for Claude Code and Codex; Bash blocks and embedded Python parsed; description unchanged |

The first live acceptance run reached successful generated checks, verification
and builds, then hit pytest's generic 60-second timeout. Giving this full
bootstrap test an explicit 300-second limit allowed the complete second run
to pass in 57.65 seconds. Per-command timeouts remain enforced. The final committed implementation
passed the same test again in 62.36 seconds.

[GitHub CI](https://github.com/smorinlabs/py-launch-blueprint/actions/runs/34564289149)
passed on `64490e3`, including Linux, macOS and Windows Python 3.13, build
installation smoke tests, documentation, types and lint. The separate press,
security, dependency, container and commit checks also passed. Automated review
results and any subsequent tracking-only commit are visible on PR #530.

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

The test checks removal of template research, planning history, project rows,
prototype code, and the active bootstrap skill. The Codex directory symlink
still resolves to a directory containing neutral documentation. Generated
README and POST_INIT files point to the retained project setup checklist.

The generated CLI and web application run after its own setup, complete local
checks, independent press verification and build. This supplies execution
evidence for the lockfile and help-snapshot regeneration commands that the
hermetic `press verify` sandbox explicitly exempts.

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

Local evidence from this run is retained under `/private/tmp/`: logs named
`py-launch-blueprint-*.log`, `py-launch-blueprint-skill-*.json`, and
`blueprint-acceptance-c934757-r2.log`. The generated project is under
`blueprint-acceptance-c934757-r2/test_committed_blueprint_gener0/harbor-sample`.
These paths are local diagnostics; the committed test and commands are the
portable reproduction procedure.

Downstream application repositories, feedback logs, merges and publishing were
outside this run. External service configuration remains a project-owner choice.
