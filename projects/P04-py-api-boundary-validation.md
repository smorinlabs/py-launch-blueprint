# P04 — Py-API Boundary Validation

**Status**: `[x]` complete (v0.1.0) — merged to `main` 2026-07-20 via #483
**Goal**: Validate every Py-API response into private Pydantic models at the
adapter edge, so upstream schema drift raises `APIError` instead of degrading
into an empty-id `Project` or an empty list that reads to the user as "no
projects found". Closes **P03-F01**, the one item P03 explicitly scoped out.

**References**

- **Trunk:** [PROJECTS.md](../PROJECTS.md)
- **Predecessor:** [P03 — Type Precision Uplevel](P03-type-precision-uplevel.md)
  — F01 originated there and was deferred as a behavior change.
- **Audit (lens 1):**
  [audit-codex.md](../research/topics/01-python-typing-best-practices/audit-codex.md)
  — finding **C1**, highest severity of 26.
- **Audit (lens 2):**
  [audit-fable.md](../research/topics/01-python-typing-best-practices/audit-fable.md)
  — finding **F8**; the two lenses converged on this independently.
- **Design:** [ADR 0005 — Hexagonal architecture and
  enforcement](../docs/design/0005-hexagonal-architecture-and-enforcement.md) —
  defines HEX-12/HEX-13, the absence-vs-error contract this sharpens.
- **Research:**
  [python-typing-ty-2026-07-18.md](../research/reference/python-typing-ty-2026-07-18.md)
  — the verified leaf behind the boundary-validation rule now in
  [AGENTS.md](../AGENTS.md) ("Validate at the boundary, narrow inward"), which
  this adapter was the sole violator of.

## Scope

- `core/adapters/py_api.py`: private boundary models for the wire format
  (`_WorkspaceRef`, `_ProjectPayload`, `_Workspace`, and the three envelopes),
  a generic validating `_request`, and a total `_to_project`.
- Fail-loud semantics: `ValidationError` → `APIError`, with a message that
  locates the offending field.
- Test coverage for both halves — the mapping still maps, and drift raises.

## Out of scope

- `InMemoryProjectsRepository` — see the open question below.
- Other ports/adapters; there is only one HTTP adapter today.
- Retry, backoff, or rate-limit handling: orthogonal to validation.
- Changing the `Project` domain model itself.

## Decisions

Confirmed 2026-07-19, before implementation:

1. **A malformed item fails the whole list call.** No skip-and-warn: returning
   the good rows and logging the bad one reintroduces exactly the quiet
   degradation this project exists to remove.
2. **Lenient on an empty workspace, strict on a present one.** `{}`, `null`
   and a missing key mean absent (the port-contract fixture sends `{}`), but
   `{"nayme": "typo"}` is drift rather than a silent `None`.
   **Sharpened after review** (Greptile P1, Copilot, Codex P2 all flagged it):
   the first implementation used `value if value else None`, which absorbed
   *every* falsy value. `""`, `[]`, `0` and `false` are the wrong **type** for
   this field rather than an empty one — "lenient on empty" is not "lenient on
   anything falsy" — so they now raise. The original mirrored the old
   `or {}` exactly, which is precisely the silent degradation this project
   exists to remove.
5. **Numeric coercion is per-field, not model-wide.** `coerce_numbers_to_str`
   on the model also coerced `name`, so `{"name": 12345}` would have been
   silently accepted. Replaced with a `_Gid` annotated type applied only to the
   id fields — matching what the old `str(...)` actually wrapped. `bool` is
   excluded explicitly, since it subclasses `int` but is never a gid.
3. **The allowed-404 path is typed with `@overload` on
   `Literal[True]`/`Literal[False]`.** The two callers that don't opt in get a
   non-optional `T` instead of a dead `None` branch. A legitimate 404 is now
   the *only* thing that yields `None`; a malformed 200 raises. The old
   `return {}` collapsed those two meanings into one value, which is what let
   drift masquerade as "not found".
4. **The error message names the field but never echoes the payload.**
   `"data.0.name — Field required (+2 more)"`. The string reaches both the
   raised `APIError` and `log.warning`, and we do not control what an upstream
   payload contains — a planted canary in the test asserts it stays
   out. The trailing count distinguishes one odd record from a version bump.

## Open questions

- Should the same validation discipline extend to
  `InMemoryProjectsRepository`'s seed data, or is an in-process fake exempt
  because its input is code, not untrusted upstream bytes?

## Tests & Tasks

- [x] [P04-TS01] Boundary test suite written first (red before green):
      mapping (`gid`/`id` alias, numeric coercion, empty-vs-present workspace)
      plus fail-loud drift (renamed envelope key, missing name, one-bad-item,
      404-is-absence vs malformed-200-is-error, workspace drift, non-JSON body).
- [x] [P04-T01] Private boundary models with `AliasChoices("gid", "id")`,
      `coerce_numbers_to_str`, and the empty-workspace `field_validator`;
      all envelope `data` fields required so a renamed key raises.
- [x] [P04-T02] `_request[T: BaseModel]` generic + `@overload` on `Literal`
      for `allow_not_found`; validates via `model_validate`.
- [x] [P04-T03] `ValidationError` → `APIError` through
      `_describe_validation_error` (loc + msg + count, no payload echo).
- [x] [P04-T04] `_to_project` made total — no `.get()`, no defaults; the
      module no longer imports or uses `Any`.
- [x] [P04-TS02] `just check` green: ruff lint+format, ty, 257 passed.
- [x] [P04-TS03] Regression guard that the error names `data.0.name` and
      `(+1 more)` but never echoes the planted token.
- [x] [P04-T05] Point P03-F01 at this project as its successor (`[>]`).
- [x] [P04-T06] Register the project file in `init/manifest.toml` under
      `py_launch_blueprint`, so a fork's `just init` rewrites it rather than
      shipping half-renamed (caught by `check_manifest_drift.py`, as designed).
- [x] [P04-TS04] PR opened, review threads resolved, merged — #483 (stacked on
      #482, retargeted to `main` on its merge). Six review threads from four
      independent bots: four valid and fixed, two refuted with evidence (see
      Review outcomes).

## Review outcomes

Six threads, four bots. **Four valid** — Greptile (`py_api.py:90`), Copilot
(`:90` and `:100`) and Codex (`:90`) — all converging on two defects:

1. The first empty-workspace validator (`value if value else None`) absorbed
   *every* falsy value. The reasoning that produced it — "mirror the old
   `or {}` exactly" — was itself the defect: that old behavior **is** the
   silent degradation this project removes.
2. `ConfigDict(coerce_numbers_to_str=True)` was model-wide, so a numeric
   `name` would have been silently stringified.

Both fixed in `e8fb025`; see Decisions 2 and 5.

**Two refuted** — `github-code-quality` (`:155`, `:166`) flagged the
`@overload` stub bodies (`...`) as "statement has no effect" and suggested
`pass`. Dismissed as a **false positive**: PEP 484 specifies `...` for overload
stubs, and having no effect is the point. An AST census of the interpreter's
standard library plus this project's installed site-packages found **722 `...`
vs 47 `pass`** (94%); ruff is neutral between the two, so the suggestion was
purely stylistic and pointed away from the dominant convention.

## Automated Verification

- `uv run --extra web ty check src/py_launch_blueprint/` passes.
- `just check` green (the port-contract suite in
  `tests/core/test_projects_repository_contract.py` must stay green unchanged —
  it is the substitutability proof that the fake and the real adapter agree).
