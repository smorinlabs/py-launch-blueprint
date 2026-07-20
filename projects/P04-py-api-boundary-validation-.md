# P04 — Py-API Boundary Validation

Validate Py-API responses at the edge with Pydantic; silent drift → APIError.

### Open questions

- Should the same validation discipline extend to
  `InMemoryProjectsRepository`'s seed data, or is an in-process fake exempt
  because its input is code, not untrusted upstream bytes?

### Notes

Promoted from **P03-F01**, which P03 explicitly scoped out — its non-goals name
"the Py-API validation redesign" as a deferred design decision. Audit lineage:
Codex **C1** / Fable **F8**, the highest-severity finding of the two-lens type
audit.

**The gap.** `core/adapters/py_api.py` returns unvalidated `response.json()` as
`dict[str, Any]`, then maps to `Project` through silent-default `.get()` chains
(`id=str(item.get("gid", item.get("id", "")))`, `name=item.get("name", "")`).
Upstream schema drift therefore yields structurally-valid but semantically-empty
`Project`s, and a renamed `data` key makes `list_projects` return `[]` — which
the CLI renders as "No projects found.", indistinguishable from a genuinely
empty account. It is the one place the repo violates its own AGENTS.md boundary
rule ("validate at the boundary, narrow inward"), which for a template repo
means forks copy the wrong pattern.

**Shape of the fix.** Pydantic boundary models (`_WorkspaceRef`,
`_ProjectPayload` with `AliasChoices("gid", "id")`, `_ProjectListEnvelope`,
`_ProjectEnvelope`); a generic `_request[T: BaseModel](..., response_model:
type[T])` that `model_validate`s; `ValidationError` → `APIError`.

**This is a behavior change** — silent degradation becomes a loud `APIError`.

Design decisions confirmed 2026-07-19, before implementation:

1. A malformed item fails the **whole** list call. No skip-and-warn: that would
   reintroduce the quiet degradation this project exists to remove.
2. `workspace: {}` is lenient (treated as absent, matching today's
   `item.get("workspace") or {}`), but a *present* workspace must carry a
   `name` — so `{"nayme": "typo"}` is an error rather than a silent `None`.
3. The allowed-404 path is typed with `@overload` on
   `Literal[True]`/`Literal[False]` for `allow_not_found`, so the two callers
   that do not opt in receive a non-optional `T` instead of a dead `None`
   branch. A legitimate 404 becomes `None`; a malformed 200 becomes an error —
   two meanings that the current `return {}` collapses into one value.

Existing coverage that must stay green: `tests/core/test_py_api_repository.py`
(adapter mapping) and `tests/core/test_projects_repository_contract.py` (the
port-contract substitutability suite, network mocked with `responses`).

<!-- Idea state. Scope this with `project-refine P04`. -->
