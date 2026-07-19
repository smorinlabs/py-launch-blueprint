# P03 — Type Precision Uplevel

**Status**: `[~]` in progress (v0.1.0)
**Goal**: Uplevel type precision across `src/py_launch_blueprint/` and close the
CI type-enforcement gap, grounded in the verified research reference
(`research/reference/python-typing-ty-2026-07-18.md`) and a two-lens audit
(Fable design-judgment + Codex empirical). Eliminate *leaking* / overly-general
types, encode closed string domains as `Literal`, add `@override` safety, and
add **empirically-verified** ty rule promotions + scoped ruff `ANN` — without
over-churning legitimate boundary `Any`.

**Non-goals**: purging every `Any` (boundary `Any` at TOML/HTTP/structlog/otel
edges is correct); behavior changes (the Py-API validation redesign is a
deferred design decision); pushing or opening a PR (not requested).

## Execution status — 2026-07-18 (branch `chore/type-precision-uplevel`)

**Landed & fully gated** (`just check` green; ty + ruff `All checks passed`;
241 tests pass; OpenAPI snapshot regenerated twice):
Tier A (T01,T02) · Tier B (T04 status Literal + T06 `@override` sweep) · Tier C
(T07 py_api surface, T08 config/settings `Any`→`str`/`object`, T09
`WrappedLogger`, T10 `comp`) · **Tier D (T13 ruff `ANN` scoped to the package —
src `ANN401` fell 9→3, the 3 legitimate Click slots `# noqa`'d)** · Tier E (T14
`/healthz` → `Health` model). 12 source files, +121/−30.

**ty upgrade (2026-07-18, same branch):** bumped ty **0.0.39 → 0.0.61**
(`uv.lock`); the newer ty passes clean on the code, and
`blanket-ignore-comment = "error"` was **re-added** (it exists in 0.0.61, was
merely absent in 0.0.39) — now 7 promoted rules. Re-verified `just check` green.

**Deferred this pass** (still open, with reasons):
- **T05** (mode `Literal`s) — ripples to local-variable annotations +
  `_resolve_log_format` needs a narrowing restructure; not a clean mechanical
  flip. Do next with per-site care.
- **T11** (idempotency `NamedTuple`s) — contained; skipped only to bound this
  pass. Low risk when resumed.
- **T12** (`mutation_options` `ParamSpec`) — verify-and-maybe-revert; wants its
  own ty + CLI-test loop.
- **F01–F06** — genuine decisions / larger refactors (see below).

## Audit provenance

- Research: deep-research run `wf_0c1ce514-5dd` (23 verified claims) →
  `research/reference/python-typing-ty-2026-07-18.md`.
- Baseline: `research/topics/01-python-typing-best-practices/baseline.md`.
- Lens 1 (Fable): `…/audit-fable.md` — 12 findings, design judgment.
- Lens 2 (Codex): `…/audit-codex.md` — 26 findings, empirically probed against
  pinned **ty 0.0.39** + **ruff 0.15.14**.
- **Cross-validation**: linchpin config claims re-verified by the orchestrator
  against the pinned binary (see "Verified facts").

## Verified facts (orchestrator re-ran these; they gate the config)

| Check | Result |
|---|---|
| `blanket-ignore-comment` in ty 0.0.39 | **UNKNOWN rule** (`Did you mean unused-ignore-comment?`) → would break CI |
| 6 supported promotions (below) as `--error` | **All checks passed** ✅ |
| `analysis.strict-literal-narrowing` | not supported in 0.0.39 (exit 2) — omit |
| `error-on-warning` | warnings exit 0 by default; `true` would gate `deprecated` |
| ruff `TC` (`--no-fix`, project-wide) | **5 errors** (2 safe `TC006`, 3 **unsafe-hidden** `TC003`) |
| ruff `ANN` on `src/py_launch_blueprint/**` | **9 findings, all `ANN401`** — package otherwise fully annotated |
| ruff `ANN` on `init/tests/**` | **142 findings** — must NOT roll ANN out there now |

## How the two lenses were adjudicated

| Topic | Fable | Codex | Decision |
|---|---|---|---|
| `blanket-ignore-comment` | endorse add | **reject** (unknown in 0.0.39) | **Codex** — verified; drop it |
| `error-on-warning=true` | endorse | **reject** (gates `deprecated`) | **Codex** — leave default |
| `python-version="3.12"` pin | "highest priority" | "redundant but harmless" | **Add** as explicit doc; hazard downgraded |
| `coerce_value` return | `str\|int\|float\|bool` | `str` (all fields str today) | **Codex `str`** (honest today; no speculative union) |
| `mutation_options` ParamSpec | lump as "keep cast" (F9) | clean `[**P,R]` (C14, no wrapper) | **Codex** — try it, verify with ty+CLI tests |
| `global_options` typing | keep `cast` (F9) | `Concatenate[AppContext,P]` (C12) | **Fable** — keep cast now; Concatenate is a verified follow-up |
| TOML dicts | bless `dict[str,Any]` (F13) | recursive `TomlValue` alias (C5-7) | **Fable now** (bless); Codex alias = optional follow-up |
| ruff `TC` | needs `runtime-evaluated-base-classes` | 3 unsafe fixes + `--no-fix` | **Both** — combined into a careful follow-up |

## Tests & Tasks

### Tier A — Enforcement config (verified safe; near-zero churn)
- [x] [P03-T01] Add `[tool.ty.rules]` promoting the **6 verified-supported**
      rules to `error`: `ambiguous-protocol-member`, `invalid-ignore-comment`,
      `ignore-comment-unknown-rule`, `ineffective-final`,
      `invalid-enum-member-annotation`, `invalid-named-tuple-override`.
      (Explicitly NOT `blanket-ignore-comment`.)
- [x] [P03-T02] Add `[tool.ty.environment] python-version = "3.12"`.
- [x] [P03-TS01] `uv run --extra web ty check src/py_launch_blueprint/` → passes.

### Tier B — Literals + `@override` (mechanical, high leverage)
- [x] [P03-T04] `DoctorCheck.status: str` → `Literal["ok","warn","error"]`
      (latent bug: a typo currently defeats `has_error()`→`/readyz` 503).
- [ ] [P03-T05] Closed string domains → `Literal`: color mode
      (`cli/output.py`,`cli/context.py`), file log format (`core/logging.py`),
      token source + config value source (`core/config.py`,`core/models.py`).
- [x] [P03-T06] `@override` sweep: `CLIResult` hook overrides (`core/models.py`),
      middleware `dispatch` (`web/middleware.py`,`web/idempotency.py`),
      `resolve_command` (`cli/groups.py`).
- [x] [P03-TS02] Regenerate + commit OpenAPI snapshot (`just export-openapi`);
      `just check` green.

### Tier C — `Any`-surface shrink (low risk, verified callers)
- [x] [P03-T07] `py_api._request(**kwargs: Any)` → explicit
      `params: dict[str, str|int] | None`; tighten the params dict value type.
- [x] [P03-T08] `coerce_value`/`set_config_value` → `str`; `get_file_value` →
      `object` (stop the core→CLI `Any` leak).
- [x] [P03-T09] structlog processors `logger: Any` → `WrappedLogger`.
- [x] [P03-T10] `cli/main.py` `comp: Any` → drop annotation / `ShellComplete`
      (confirm with one `ty check`).
- [ ] [P03-T11] `web/idempotency.py` `_Entry` + cache key → `NamedTuple`s.
- [ ] [P03-T12] `mutation_options` → `ParamSpec [**P, R]` (verify ty + CLI tests;
      revert to `cast` if either objects).
- [x] [P03-TS03] `just check` green; CLI tests pass.

### Tier D — Annotation-presence gate (after Tier C shrinks the `Any` surface)
- [x] [P03-T13] Add ruff `ANN` scoped to `src/py_launch_blueprint/**`; NO global
      `ANN401` ignore; two targeted `# noqa: ANN401` for the Click forwarding
      slots (`cli/options.py:159,171`); per-file `ANN` ignore for `tests/*` and
      `init/tests/**`.
- [x] [P03-TS04] `uv run ruff check .` clean; `just check` green.

### Tier E — `/healthz` response model
- [x] [P03-T14] `/healthz -> dict[str,str]` → `Health` BaseModel response_model.
- [x] [P03-TS05] Regenerate OpenAPI snapshot; `just check` green.

### Deferred follow-ups (documented; NOT executed — need decisions)
- [ ] [P03-F01] Py-API boundary validation with Pydantic models (Codex C1 /
      Fable F8) — **behavior change** (silent empty-`Project` → fail-loud
      `APIError`). Design decision.
- [ ] [P03-F02] Recursive `TomlValue` alias across config read/merge/write (C5-7).
- [ ] [P03-F03] `global_options` `Concatenate[AppContext, P]` typing (C12) —
      Fable×Codex disagreement; verify against every decorated command.
- [ ] [P03-F04] `assert_never` exhaustiveness for `OutputMode` dispatch (F10).
- [ ] [P03-F05] Optional-OTel `_TraceApi` Protocol (C15).
- [ ] [P03-F06] ruff `TC` rollout: configure
      `flake8-type-checking.runtime-evaluated-base-classes =
      ["pydantic.BaseModel","pydantic_settings.BaseSettings"]`, fix 2 `TC006`
      (quote `cast("F", …)`), review 3 unsafe `TC003`, pass `--no-fix` in audits.

## Automated Verification
- `uv run --extra web ty check src/py_launch_blueprint/` passes after every tier.
- `just check` (ruff lint+format, ty, pytest) green before considering a tier done.
- OpenAPI snapshot regenerated + committed after T04 and T14 (api-contract CI).

## References
- `research/reference/python-typing-ty-2026-07-18.md`
- `research/topics/01-python-typing-best-practices/{audit-fable,audit-codex,DECISION}.md`
