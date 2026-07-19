---
name: python-typing-ty-best-practices
topic: 01-python-typing-best-practices
date: 2026-07-18
status: current
tooling_versions:
  ty: "0.0.39 (2026-05-22)"
  python_floor: "3.12"
confidence: high (mechanism) / mixed (specific rule promotions — see caveats)
sources: primary (ty docs, PEPs 692/695/698/742, Pydantic v2 docs, FastAPI docs)
---

# Python typing best practices, grounded in `ty` — reference leaf

Decision-ready reference for the type audit. Every claim in §1–§2 is either
research-verified (3-0 adversarial vote, primary source) or live-doc-verified
against docs.astral.sh on 2026-07-18. Rows marked **[convention]** are
established typing-spec guidance the research pass did not independently verify —
apply them, but they carry lower evidentiary weight than the cited rows.

---

## 0. The one-line verdict (ty vs Pyright reconciliation)

**`ty` at any strictness will never flag a missing annotation or implicit
`Any` — it honors the gradual-typing guarantee and ships no such rule.**
Pyright-`strict` (IDE) *does* flag those. So the CI-vs-IDE divergence closes
**only** by adding **ruff `ANN`** for annotation *presence*, while `ty` owns
annotation *correctness*. Tightening `[tool.ty.rules]` alone cannot make CI
match the Pyright-strict intent.

Division of labor:

| Concern | Owner | Why |
|---|---|---|
| Type *correctness* (bad assignments, unresolved refs, wrong arg types, Protocol conformance) | **ty** (CI authority, ADR-03) | Already errors by default; stricter than mypy/pyright in body-checking |
| Annotation *presence* (every def/param/return annotated) | **ruff `ANN`** | ty deliberately does not check this |
| Annotation *style*/import hygiene (type-only imports, `X \| None`) | **ruff `TC`, `UP`, `RUF`** | Lint-level, complements ty |
| Runtime validation at I/O edges | **Pydantic v2** | Static types can't validate external data |

---

## 1. `ty` configuration (VERIFIED live 2026-07-18)

### 1a. Config surface — six sections (research's "5-section" model was REFUTED)

`pyproject.toml` `[tool.ty.*]` (or bare `[*]` in `ty.toml`):

| Section | Key highlights (with defaults) |
|---|---|
| `[tool.ty.environment]` | `python-version` **default `"3.14"`**, `python-platform` (current), `python`, `root`, `extra-paths=[]`, `typeshed` |
| `[tool.ty.src]` | `include=null`, `exclude=null`, `respect-ignore-files=true`, `root` (deprecated → use `environment.root`) |
| `[tool.ty.rules]` | `dict[RuleName \| "all", "ignore"\|"warn"\|"error"]` |
| `[tool.ty.terminal]` | `output-format="full"`, **`error-on-warning=true`** (per config ref; see caveat C1) |
| `[[tool.ty.overrides]]` | `include`, `exclude`, nested `rules` table; later overrides win; override rules take precedence over global |
| `[tool.ty.analysis]` | `strict-literal-narrowing=false`, `respect-type-ignore-comments=true`, `allowed-unresolved-imports=[]`, `replace-imports-with-any=[]` |

### 1b. Strictness model

- **Rule-based, not mode-based.** No `--strict` flag; no `check_untyped_defs`
  toggle (ty checks unannotated function *bodies* unconditionally). Default
  posture is already "stricter than mypy or pyright in many ways."
- **Correctness core already errors by default**: `unresolved-import`,
  `unresolved-reference`, `unresolved-attribute`, `invalid-assignment`,
  `invalid-argument-type`, `unused-ignore-comment`, and most others.
- **A strict config therefore mostly promotes the handful of `warn`/`ignore`
  rules** and adds explicit intent.

### 1c. Rules shipping below `error` (the promote-to-error candidate set)

Default **`warn`**: `ambiguous-protocol-member`, `deprecated`,
`ignore-comment-unknown-rule`, `ineffective-final`,
`invalid-enum-member-annotation`, `invalid-ignore-comment`,
`invalid-legacy-positional-parameter`, `invalid-named-tuple-override`,
`experimental-syntax`.

Default **`ignore`**: `blanket-ignore-comment`, `division-by-zero`.

### 1d. Recommended `[tool.ty.rules]` block (strict-but-practical)

Tiered so the audit can pick a comfort level. **Tier 1 = zero-cost, high-value**
(the repo already complies or the rule targets its own patterns):

> **⚠ CORRECTED 2026-07-18 by the empirical audit (Codex + orchestrator
> re-verification against pinned ty 0.0.39).** The original block below listed
> `blanket-ignore-comment` (an **unknown rule** in 0.0.39 → `warning[unknown-rule]`,
> which with `error-on-warning=true` **breaks CI**), `strict-literal-narrowing`
> (**unsupported** → exit 2), and `error-on-warning=true` (which would gate
> `deprecated`, contradicting the Tier-3 hold-back). The **verified** block is:

```toml
[tool.ty.environment]
python-version = "3.12"          # explicit; redundant on this repo (ty resolves
                                 # 3.12 from requires-python) but documents intent

[tool.ty.rules]
# All six verified against pinned ty 0.0.39: `ty check --error <each>` → passes.
ambiguous-protocol-member   = "error"  # this repo's ports ARE Protocols (core/ports.py)
blanket-ignore-comment      = "error"  # re-added after upgrading to ty 0.0.61 (see note)
invalid-ignore-comment      = "error"
ignore-comment-unknown-rule = "error"
ineffective-final           = "error"
invalid-enum-member-annotation = "error"
invalid-named-tuple-override = "error"

# UPDATE 2026-07-18 (later): the repo upgraded ty 0.0.39 → 0.0.61.
# `blanket-ignore-comment` EXISTS in 0.0.61 (it was merely absent in 0.0.39), so it
# was re-added above and passes on the source. This is the drift caveat C2 playing
# out — always re-verify rule availability against the pinned ty after an upgrade.
# `deprecated` deliberately left at its default `warn` — a template repo must not
# let a dependency deprecation fail every fork's CI.

# error-on-warning: LEAVE DEFAULT. Warnings exit 0 in 0.0.39; setting it true
# would gate `deprecated`. No [tool.ty.terminal] / [[overrides]] block needed —
# CI runs `ty check src/py_launch_blueprint/` only, so a tests/** override is inert.
```

~~Optional stricter knob: `strict-literal-narrowing`~~ — **not supported in
0.0.39** (rejected with exit 2); revisit after a ty upgrade.

### 1e. Suppression hygiene

- Use **rule-scoped** `# ty: ignore[rule]` (repo already does — 2 occurrences).
- `unused-ignore-comment` (default `error`) flags dead suppressions and can
  ONLY be silenced with `# ty: ignore[unused-ignore-comment]`.
- Enabling `blanket-ignore-comment=error` bans bare `# ty: ignore`.

---

## 2. Overly-general → precise replacement table

"When the general form is fine" prevents over-churn — not every `Any` is a bug.

| Overly-general | Precise replacement (3.12+) | When the general form is actually fine |
|---|---|---|
| `Any` (function boundary) | A real generic (PEP 695 `def f[T]`), `Protocol`, or concrete type | True dynamic dispatch; third-party callback whose shape you don't own (e.g. structlog processors) |
| `dict[str, Any]` | `TypedDict` (PEP 589), `dataclass`, or `pydantic.BaseModel` | Genuinely heterogeneous parse output *at the boundary*, immediately narrowed inward |
| bare `dict`/`list`/`tuple` | Parameterized `dict[K,V]`, `list[T]`, fixed `tuple[A,B]` | Never — always parameterize (repo already clean here) |
| untyped/uniform `**kwargs` | `**kwargs: Unpack[SomeTypedDict]` (PEP 692, stdlib `typing` on 3.12) | Pass-through `**kwargs` forwarded verbatim to a wrapped callable → use `ParamSpec` instead |
| stringly-typed value | `Literal[...]`, `enum.StrEnum`, or `NewType` **[convention]** | Free-form user text; genuinely open string domain |
| decorator `Callable[..., Any]` + `cast` | `ParamSpec` + `TypeVar`: `def deco[**P, R](f: Callable[P, R]) -> Callable[P, R]` **[convention]** | Decorator that changes the signature (adds/removes params) — `cast` may still be cleanest |
| broad `except Exception` typed loosely | Narrow exception types; `assert_never` for exhaustiveness **[convention]** | Top-level "catch-all-and-log" boundary handler |
| validate-then-narrow returning `bool` | `TypeIs` (PEP 742; `typing_extensions` on 3.12 — 3.13 stdlib) narrows both branches; prefer over `TypeGuard` | `TypeGuard` when you deliberately only want positive-branch narrowing |
| override without marker | `@override` (PEP 698, stdlib `typing` 3.12) | Non-override methods |

### Structural-typing guidance **[convention]**
- **`Protocol` vs ABC**: Protocol for *ports* you don't want implementers to
  inherit from (structural) — matches this repo's hexagonal design. ABC when you
  own the hierarchy and want shared implementation. `@runtime_checkable` only if
  you actually `isinstance`-check (it's slower and checks methods, not sigs).
- **`TypedDict` vs `dataclass` vs `NamedTuple` vs `BaseModel`**: TypedDict for
  dict-shaped boundary data (no runtime cost, no validation); dataclass for
  owned mutable records; NamedTuple for immutable positional tuples; `BaseModel`
  when you need *runtime validation* at an external edge.
- **Boundary discipline**: keep `Any`/`dict[str,Any]` at the I/O edge (TOML,
  HTTP-JSON, env), validate/narrow once with Pydantic or `TypeIs`, propagate
  precise types inward. Never let boundary `Any` leak into the core.

---

## 3. Framework interplay (VERIFIED)

- **FastAPI**: the path-operation **return-type annotation** IS the response
  model — FastAPI validates, adds JSON Schema, serializes, and **filters output
  to the declared type (a security boundary)**. Use `Annotated[T, Depends()]`
  (recommended since 0.95.0; pin ≥0.95.1) so checkers keep DI type info.
- **Pydantic v2**: `before`/`plain`/`wrap` validators may accept a wider input
  than the field annotation — declare it with `json_schema_input_type` so the
  validation-mode JSON schema is accurate. `after` validators are the more
  type-safe default. `TypeAdapter` validates non-`BaseModel` shapes (TypedDict,
  `list[Model]`) at boundaries without a BaseModel subclass.

---

## 4. Ruff typing-lint families to add (complements ty, not redundant)

Ruff is a linter, **not** a type checker — `ANN`/`TC`/`PYI` check that
annotations *exist and are well-formed*, not that they're *correct* (that's ty).

| Family | What it buys | Recommendation |
|---|---|---|
| **`ANN`** (flake8-annotations) | **Closes the ty gap**: flags missing param/return annotations (`ANN001`, `ANN201`, …) | **Add** — this is the annotation-coverage enforcement ty lacks. Scope-relax `tests/**`. Consider ignoring `ANN401` (bans `Any`) initially to avoid boundary churn |
| **`TC`** (flake8-type-checking) | Moves type-only imports into `if TYPE_CHECKING:` (faster imports, breaks cycles) | **Add** — low-noise, mechanical autofix |
| **`PYI`** | Rules for `.pyi` stubs | Skip unless the repo ships stubs |

Suggested additions to `lint.select`: `"ANN"`, `"TC"`. Suggested
`per-file-ignores`: `"tests/*" = ["ANN"]`, plus (initially) global
`"ANN401"` ignore.

---

## 5. File-by-file audit rubric **[convention — apply with judgment]**

For each source file, grade and flag:

1. **Signature completeness** — every param + return annotated? (ANN territory)
2. **`Any` justification** — each `Any`: boundary-necessary, third-party-shaped,
   or lazy? Boundary `Any` should be narrowed within ≤1 hop.
3. **Container precision** — every `dict`/`list`/`tuple`/`set` parameterized;
   `dict[str, Any]` challenged against TypedDict/model.
4. **Stringly-typed values** — constants/enums that should be `Literal`/`StrEnum`.
5. **Protocol/ABC fit** — ports are `Protocol`; variance correct; no needless
   `@runtime_checkable`.
6. **Override safety** — subclass overrides carry `@override`.
7. **Boundary narrowing** — external data validated (Pydantic/`TypeIs`) before
   flowing inward; no boundary `Any` leaking to core.
8. **Suppression hygiene** — all ignores rule-scoped and live (no dead ignores).
9. **Exhaustiveness** — `match`/if-elif over closed sets ends in `assert_never`.
10. **Decorator typing** — `ParamSpec` over `Callable[..., Any]` + `cast` where
    the signature is preserved.

Verdict per file: **precise** / **acceptable-boundary** / **needs-tightening**.

---

## Caveats (pre-1.0 fluidity — confirm before relying)

- **C1 — `error-on-warning` default:** the config reference lists default
  `true`, but the mypy-migration doc implies warnings don't fail by default.
  ty is pre-1.0 and hedges with "currently." **Confirm empirically** (add a
  `deprecated` call, run `ty check`, observe exit code) before assuming warn
  ⇒ CI failure. Setting it explicitly (as in §1d) removes the ambiguity.
- **C2 — exact rule defaults drift** between ty releases. §1c was verified
  against v0.0.39 docs on 2026-07-18; re-check `docs.astral.sh/ty/reference/rules/`
  if ty is upgraded.
- **C3 — `[convention]` rows** (§2 lower rows, §5 rubric) are standard
  typing-spec practice but were NOT independently verified by the research
  adversarial pass (no surviving 3-0 claim). Treat as strong defaults, not
  citations.
