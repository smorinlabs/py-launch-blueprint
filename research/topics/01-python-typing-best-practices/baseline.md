# Current type posture — factual baseline (2026-07-18)

Snapshot taken before the audit, to anchor phase 2 (Fable + Codex).

## Tooling state
- **ty 0.0.39** — `uv run --extra web ty check src/py_launch_blueprint/` →
  **"All checks passed!"** on **defaults** (no `[tool.ty]` section in
  `pyproject.toml`).
- **Pyright `strict`** configured (`[tool.pyright]`) — IDE only, not gated in CI.
- **Ruff** rule families: `E,F,I,B,C4,UP,N,RUF,W,YTT,S`. **No `ANN`
  (flake8-annotations), no `TC` (flake8-type-checking), no `PYI`.**
- PEP 695 syntax already in use (e.g. `def global_options[F: Callable[..., Any]]`)
  → codebase is already modern; audit is about *precision*, not modernization.

## `Any` inventory — 38 occurrences, clustered at boundaries
| Area | Files | Nature | Likely verdict |
|---|---|---|---|
| **TOML/config boundary** | `core/config.py`, `core/settings.py` | `dict[str, Any]` for parsed TOML, `coerce_value -> Any` | Boundary `Any` — candidate for `TypedDict`/narrowing or documented-OK |
| **HTTP/JSON boundary** | `core/adapters/py_api.py` | `**kwargs: Any`, `dict[str, Any]` from `response.json()`, `_to_project(item: dict[str, Any])` | Boundary — narrow inward with a model/TypedDict |
| **Decorator plumbing** | `cli/options.py` | `Callable[[Any], Any]`, `*args/**kwargs: Any`, `cast(F, ...)` | Classic — candidate for `ParamSpec`, or documented-OK |
| **structlog processors** | `core/logging.py` | `logger: Any` processor signatures | Third-party callback shape — likely OK |
| **web problem+json** | `web/problems.py` | `dict[str, Any]` extensions / openapi | Boundary — partly TypedDict-able |
| **shell completion** | `cli/main.py` | internal Click completion object | Likely OK |

## Other signals
- **No bare/unparameterized containers** (`dict`/`list`/`tuple` without args) — good.
- Suppressions are **rule-scoped** and minimal: 2× `# ty: ignore[<rule>]`
  (`web/idempotency.py`, `web/problems.py`) — good hygiene.
- 2× `cast(F, ...)` in `cli/options.py` decorator code.

## Audit hypotheses to test in phase 2
1. Add a `[tool.ty.rules]` strict-but-practical block so CI matches the
   strict *intent* Pyright-strict signals (reconcile the two voices).
2. Tighten boundary `Any` where a `TypedDict`/model/narrowing is cheap and real;
   explicitly bless the `Any` that is genuinely correct (don't churn).
3. Consider `ParamSpec` for `cli/options.py` decorators to drop `cast`/`Any`.
4. Consider adding ruff `TC` (type-checking-only imports) and a scoped `ANN`.
