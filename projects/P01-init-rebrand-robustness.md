# P01 — Init app-name rebrand robustness

- **Status:** `[x]` completed — B + C merged (#389)
- **Captured:** 2026-06-10
- **Scope:** init rebrand system (`init/`), CLI internals (`src/py_launch_blueprint/`)

## Problem

The init rebrand system replaces identity literals (`plbp`, `PLBP`, …) per
*field*: the engine (`init/_engine.py`) rewrites each value **only in the files
listed under that value's `[[replace]]` block**. But the drift guard
(`init/ci/check_manifest_drift.py`) verifies coverage against a **flat union**
of all blocks' files (it builds one `covered_files` set and `continue`s on any
match), so it never checks that a file containing `PLBP` is listed under the
`app_name_upper` field specifically.

Result — a verified failure mode: a file listed under `app_name` (lowercase)
but not `app_name_upper` (uppercase) that contains a `PLBP_*` literal passes
drift, yet a fork ships half-renamed (`widget` command still reading `PLBP_*`).
This was hit twice during the CLI work (`_plbp_owned` in `core/logging.py`,
`plbp` in `tests/conftest.py`) and only caught by the slow full-rebrand
integration run, not the fast checker.

## Plan: B + C

### B — per-field drift coverage (the deep fix)

Make the verifier match the engine. In `check_manifest_drift.py`, build
per-*value* coverage instead of a flat union:

```python
covered_by_value: dict[str, set[Path]] = {}
for op in manifest.replaces:
    files = {(REPO_ROOT / f).resolve() for f in op.files}
    for value in op.current:
        covered_by_value.setdefault(value, set()).update(files)
# per repo file: for each identity value present, require coverage under THAT value
```

Also stop blanket-skipping `[[rename]]` source files for the content check — a
rename moves the *filename*, not the `plbp`/`PLBP` occurrences inside the file
(e.g. `docs/design/0001-…` is both renamed and content-replaced), so content
coverage must be verified independently.

No `src/` changes; every literal stays greppable. Acceptance: a fixture repo
with one deliberately half-covered file makes the checker exit non-zero with a
message naming the exact missing field/list.

### C — derive only the three non-contract internals

Derive from `paths.APP_NAME` the three literals nobody greps in docs/scripts,
removing the highest-risk incidental trap sites:

- `cli/main.py`: `_COMPLETE_VAR = "_PLBP_COMPLETE"` → `f"_{APP_NAME.upper()}_COMPLETE"`
- `cli/main.py`: `auto_envvar_prefix: "PLBP"` → `APP_NAME.upper()`
- `core/logging.py`: the `_plbp_owned` handler marker → `_OWNED_FLAG = f"_{APP_NAME}_owned"` + `setattr`/`getattr`

Leaves all **user-facing** env-var literals (`PLBP_TOKEN`, `PLBP_OUTPUT`, …)
explicit so `grep PLBP_TOKEN src/` keeps working. `core/logging.py` drops out
of the `app_name` replace list as a bonus.

## Out of scope: A (full derivation) — rejected, with rationale

Deriving every env-var name from `APP_NAME` (`envvar=f"{ENV_PREFIX}_OUTPUT"`,
`TOKEN_ENV_VAR = f"{ENV_PREFIX}_TOKEN"`, …) was considered and rejected:

1. Kills greppability in a **template** whose purpose is to be read/learned/copied.
2. Doesn't eliminate the manifest — docs, the spec, ADRs, CHANGELOG, and tests
   keep literal `plbp`/`PLBP_*` (you can't derive prose; tests *should* assert
   the literal contract). ~10 of ~50 entries removed; machinery survives.
3. Tests that assert `setenv(f"{ENV_PREFIX}_OUTPUT")` test nothing — so the
   test files stay literal and keep the half-rename risk B already fixes.
4. ~1–2 days incl. re-running the whole rebrand integration matrix.

B is the deeper fix because the real mechanism is *verification matching the
engine*, not name derivation.

## Acceptance criteria

- [x] Drift checker fails when a file contains an identity value not covered
      under that value's own field (regression fixture test).
- [x] Drift checker verifies content coverage independently of `[[rename]]`.
- [x] `_COMPLETE_VAR`, `auto_envvar_prefix`, and the logging owner-marker derive
      from `APP_NAME` (the owner-marker trap is gone; the one remaining uppercase
      token is the user-facing `*_LOG_FILE` env var named in a docstring).
- [x] User-facing env-var literals unchanged and still greppable.
- [x] Full rebrand integration reports `no-identity-leak: ok` (CI-confirmed:
      the clone_reinit / integration-ok jobs passed on #389).

## References

- Failure mode confirmed in `init/ci/check_manifest_drift.py` (flat-union
  coverage) and `init/_engine.py` (`apply_replace_text` applies only
  `op.current` to `op.files`).
- Originated from the high-effort code review of the `plbp` CLI stack
  (PRs #378–#381); the review's "altitude" finding framed it as derive-vs-
  special-case, resolved here as verify-vs-derive.
