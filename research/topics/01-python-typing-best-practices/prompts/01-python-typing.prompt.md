# Deep-research prompt — Python typing best practices, grounded in `ty` (Astral)

## Objective

Produce a practitioner's reference on **state-of-the-art Python typing
(2024–2026) for a Python 3.12+ codebase**, specifically actionable for a
subsequent audit that will (a) eliminate overly-general types and (b) configure
the **`ty`** type checker (Astral) to enforce strictness. The output must be
concrete enough that an auditor reads recommendations from it without
re-searching.

## Context (answers to preempt clarifying questions)

- Target: **Python 3.12+ only** — assume PEP 695 (`type` statement + `class
  Foo[T]` / `def f[T]` type-parameter syntax), `Self`, `@override`
  (via `typing`/`typing_extensions`), `TypedDict` with `Required`/`NotRequired`,
  `Unpack`/PEP 692 typed `**kwargs`, and `Annotated` are all available.
- Type checker of record is **`ty`** (Astral), the fast Rust checker, run in CI
  as `ty check`. **Pyright strict** is used for the IDE only. The codebase uses
  **hexagonal architecture** with `typing.Protocol` ports, plus **FastAPI** and
  likely **Pydantic**.

## Questions to answer (fan out; verify against primary sources)

### A. `ty`-specific (HIGH PRIORITY — least-documented, most decision-relevant)
1. What is `ty`'s **strictness model** and inference philosophy? Does it have a
   "strict mode" analogous to `mypy --strict` / Pyright `strict`, or is it
   rule-based? Enumerate the **rule catalog** and the config surface
   (`[tool.ty.environment]`, `[tool.ty.rules]`, `[tool.ty.src]`,
   `[[tool.ty.overrides]]`, `[tool.ty.terminal]`).
2. Which `ty` rules are **off or lenient by default** that a
   quality-focused project should turn to `error` (e.g. around `Any`,
   unresolved refs, unused ignores, possibly-undefined, redundant casts)?
   Give a **recommended `[tool.ty.rules]` block** for a strict-but-practical
   posture, plus a **relaxed `[[tool.ty.overrides]]` for `tests/**`**.
3. How does `ty` treat **`Any`** and the **gradual-typing guarantee**? Does it
   flag implicit `Any` (missing annotations, untyped calls) — and if so, under
   which rule? How does it handle unannotated function bodies vs signatures?
4. Concrete **differences vs mypy-strict and Pyright-strict** that would change
   which errors surface — so we understand what CI (`ty`) will and won't catch
   that Pyright-strict (IDE) does. Note current maturity caveats / known
   limitations of `ty` (it is pre-1.0).
5. How to suppress correctly in `ty`: `# ty: ignore[rule]` (rule-scoped), and
   whether `ty` reports **unused ignores**.

### B. Avoiding overly-general types (the audit's core rubric)
6. Define the anti-patterns and the precise replacement for each:
   - `Any` → `object` vs `Unknown` vs a real generic vs `Protocol`; when `Any`
     is genuinely correct.
   - Bare `dict`/`list`/`tuple`/`set` and `dict[str, Any]` → parameterized
     generics, `TypedDict`, `dataclass`, `NamedTuple`, `pydantic.BaseModel`,
     fixed-length `tuple[A, B]`.
   - Untyped `*args`/`**kwargs` → `Unpack[TypedDict]` (PEP 692), `ParamSpec`.
   - Stringly-typed values → `Literal`, `enum.Enum`/`StrEnum`, `NewType`.
   - `Optional`/`| None` overuse and truthiness traps.
   - Broad `Exception` typing; `Callable` without arg/return types →
     `Callable[P, R]` / `Protocol` with `__call__`.
7. **`Protocol` vs ABC vs `Callable`**: when structural typing wins, variance
   (`covariant`/`contravariant`), `@runtime_checkable` costs, and Protocol
   design for ports-and-adapters (directly relevant to this repo's `core/ports`).
8. **`TypedDict` vs `dataclass` vs `NamedTuple` vs Pydantic `BaseModel`** —
   decision guidance and typing implications (mutability, validation boundary,
   `Required`/`NotRequired`, `total=False`).
9. **Variance & generics**: `TypeVar` bounds/constraints, PEP 695 syntax,
   invariance pitfalls with mutable containers, `Self`, `@override` (PEP 698),
   `@final`, `assert_never` for exhaustiveness.
10. **Boundary typing**: precise types at I/O edges (JSON, env, HTTP) —
    validate-then-narrow with Pydantic/`TypeGuard`/`TypeIs` (PEP 742) rather
    than propagating `Any` inward.

### C. Framework interplay
11. **Pydantic v2 + typing**: `model_config`, `Annotated` validators,
    `Field(...)`, how Pydantic types interact with static checkers, and where
    Pydantic replaces vs complements static typing.
12. **FastAPI typing**: dependency-injection typing, `Annotated[...,
    Depends()]`, response_model, avoiding `Any` in route signatures.

### D. Process / enforcement
13. Which **ruff typing-lint families** (`ANN` flake8-annotations, `TC`
    flake8-type-checking, `PYI`, `RUF`) complement `ty` without redundant noise,
    and a recommended selection + per-file ignores for `tests/**`.
14. A short **audit rubric / checklist** an agent can apply file-by-file to
    grade type precision and flag overly-general types.

## Output shape

- Lead with a **decision-ready summary**: the recommended `[tool.ty.rules]` +
  overrides block, the recommended ruff typing rules, and a one-line verdict on
  ty-vs-Pyright reconciliation.
- Then a **replacement table** (overly-general → precise, with a 1-line "when
  the general form is actually fine").
- Then the **file-by-file audit rubric**.
- Cite primary sources (ty docs, PEPs, Pydantic/FastAPI docs, typing spec).
  Flag anything version-sensitive or where `ty`'s pre-1.0 status makes the
  answer provisional.
