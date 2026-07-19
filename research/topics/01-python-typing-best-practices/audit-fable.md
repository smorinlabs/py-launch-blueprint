# Type audit — Fable lens (whole-codebase type-design judgment)

- **Date**: 2026-07-18
- **Scope**: `src/py_launch_blueprint/` (all 40 files read; ~4,530 LOC)
- **Grounding**: `research/reference/python-typing-ty-2026-07-18.md` (rubric §5,
  replacement table §2) + `research/topics/01-python-typing-best-practices/baseline.md`
- **Mode**: read-only; findings only

## Overall assessment

This codebase is **already in the top tier of typing discipline**: PEP 695
generics in use, `Protocol` ports with no inheritance, Pydantic + `Literal` at
every config edge, zero bare containers, and both `# ty: ignore`s rule-scoped
with load-bearing comments. The audit therefore surfaces *precision up-levels*
and *anti-churn blessings*, not repairs. The single most valuable systemic gap
is **no `@override` anywhere** despite a renderer-hook pattern (`CLIResult`
subclasses) that is exactly the bug class PEP 698 exists for.

Finding count: **1 high, 7 med, 4 low** (F9 is a deliberate *no-change*
verdict), plus one blessing bundle (F13).

---

## Findings (ranked by severity × leverage)

### F1 — `DoctorCheck.status` is stringly-typed with the Literal spelled in a comment
- **Where**: `src/py_launch_blueprint/core/models.py:139`
- **Category**: stringly-typed · **Severity**: high · **Effort**: trivial
- **Current**:
  ```python
  status: str  # "ok" | "warn" | "error"
  ```
- **Proposed**:
  ```python
  from typing import Literal

  type CheckStatus = Literal["ok", "warn", "error"]

  class DoctorCheck(BaseModel):
      name: str
      status: CheckStatus
      detail: str
  ```
- **Rationale**: Rubric #4 — the comment *is* the type; encode it. Today a
  status typo type-checks, passes Pydantic, and silently defeats
  `has_error()` (models.py:158) — which gates both the CLI `doctor` exit code
  and the `/readyz` 503. With `Literal`, construction sites
  (`core/diagnostics.py:54,62,67,76,82`) are statically checked, comparisons
  against non-members become ty `comparison` diagnostics, and Pydantic
  enforces at runtime. Bonus: `DoctorReport` is the `/readyz`
  `response_model`, so the OpenAPI schema gains an enum — a strictly tighter
  public contract.
- **Risk**: none behavioral; the OpenAPI snapshot changes → run
  `just export-openapi` and commit (the api-contract workflow enforces this).
- **Verdict**: **EXECUTE-NOW-SAFE**

### F2 — No `@override` markers anywhere (PEP 698, stdlib on 3.12)
- **Where** (all subclass overrides in the tree):
  - `core/models.py` — `ProjectList` (86, 89, 92, 95), `ConfigValue` (106, 109),
    `ConfigPath` (121, 124, 127), `DoctorReport` (148, 151, 154),
    `DiagnosticsBundle` (183, 186, 189) overriding `CLIResult` hooks
  - `web/idempotency.py:66`, `web/middleware.py:66,107` — `dispatch` overriding
    `BaseHTTPMiddleware.dispatch`
  - `cli/groups.py:39` — `resolve_command` overriding `click.Group`
- **Category**: missing-override · **Severity**: med · **Effort**: small (mechanical)
- **Current**: plain `def table_rows(self) -> ...:` etc.
- **Proposed**: `from typing import override` + `@override` on each.
- **Rationale**: Rubric #6 / replacement table row 9. The `CLIResult` hook
  pattern is the sharp edge: `table_rows_rich` *defaults* to `table_rows` in
  the base (models.py:58-66), so a renamed or mis-spelled override in a
  subclass silently degrades to the base behavior — no error, just wrong
  output. `@override` converts that failure mode into a static diagnostic
  (Pyright-strict today; ty's override checking as it matures). Same
  protection for starlette/click upstream renames.
- **Risk**: zero — identity decorator at runtime.
- **Verdict**: **EXECUTE-NOW-SAFE**

### F3 — `PyApiProjectsRepository._request(**kwargs: Any)` is wider than every call site
- **Where**: `src/py_launch_blueprint/core/adapters/py_api.py:56-63`, plus `:106`
- **Category**: any-boundary · **Severity**: med · **Effort**: small
- **Current**:
  ```python
  def _request(self, method: str, path: str, *, allow_not_found: bool = False,
               **kwargs: Any) -> dict[str, Any]:
  ...
  params: dict[str, Any] = {"limit": limit, "opt_fields": "name,workspace.name"}
  ```
- **Proposed**:
  ```python
  def _request(self, method: str, path: str, *, allow_not_found: bool = False,
               params: dict[str, str | int] | None = None) -> dict[str, Any]:
      ...
      response = self.session.request(method, url, timeout=self.timeout, params=params)
  ...
  params: dict[str, str | int] = {"limit": limit, "opt_fields": "name,workspace.name"}
  ```
- **Rationale**: Verified: all three call sites (`:96`, `:113`, `:118-123`)
  pass at most `params`. The `**kwargs: Any` pass-through is generality nobody
  uses — the replacement-table's `Unpack`/`ParamSpec` machinery is overkill
  when the honest signature is one optional parameter. A future call needing
  another `requests` kwarg adds it explicitly. The `dict[str, Any]` *return*
  stays: that is the HTTP-JSON boundary, narrowed one hop later (see F8).
- **Risk**: none — private helper, adapter-owned.
- **Verdict**: **EXECUTE-NOW-SAFE**

### F4 — `coerce_value` / `set_config_value` return `Any` that leaks into the CLI layer
- **Where**: `src/py_launch_blueprint/core/settings.py:105`,
  `src/py_launch_blueprint/core/config.py:239`, `config.py:186`
- **Category**: dict-str-any / leaking-Any · **Severity**: med · **Effort**: small
- **Current**:
  ```python
  def coerce_value(section: str, key: str, raw: str) -> Any: ...
  def set_config_value(config_path: Path, dotted_key: str, raw_value: str) -> Any: ...
  def get_file_value(config_path: Path, dotted_key: str) -> Any: ...
  ```
- **Proposed** (in `settings.py`, reused by `config.py`):
  ```python
  type SettingValue = str | int | float | bool   # TOML scalar; schema fields only

  def coerce_value(section: str, key: str, raw: str) -> SettingValue: ...
  def set_config_value(...) -> SettingValue: ...
  def get_file_value(...) -> object:  # raw user TOML — could be any TOML value
  ```
- **Rationale**: Rubric #7 (boundary `Any` must not leak inward). `coerce_value`'s
  `Any` propagates into `cli/commands/config.py:113,179` and `config.py:247` —
  three hops of untyped values in the *core→CLI* direction, the direction the
  reference says must stay precise. Every schema field is a `str`-based
  `Literal` today; the scalar union covers plausible schema growth (bools,
  ints) without touching call sites (`str()`, TOML write, f-strings all
  accept it). `get_file_value` is different: it returns a raw value from an
  *arbitrary user file* (could be a TOML array or datetime), so `object` is
  the honest type — its only current consumers are equality checks in tests,
  which `object` supports.
- **Risk**: none for `coerce_value`/`set_config_value` (`getattr` result is
  assignable). `object` on `get_file_value` could statically break a fork
  that calls methods on the result — which is exactly the point.
- **Verdict**: **EXECUTE-NOW-SAFE**

### F5 — Idempotency store contract is positional tuples documented by comments
- **Where**: `src/py_launch_blueprint/web/idempotency.py:46-49` (`_Entry`),
  `:64` and `:76` (cache key `tuple[str, str, str, str]`)
- **Category**: protocol-design · **Severity**: med · **Effort**: small
- **Current**:
  ```python
  #: (stored_at_monotonic, status_code, raw_headers, body)
  _Entry = tuple[float, int, list[tuple[bytes, bytes]], bytes]
  ...
  self._store: OrderedDict[tuple[str, str, str, str], _Entry] = OrderedDict()
  cache_key = (request.method, request.url.path, request.url.query, key)
  ```
- **Proposed**:
  ```python
  class _CacheKey(NamedTuple):
      method: str
      path: str
      query: str
      idempotency_key: str

  class _Entry(NamedTuple):
      stored_at: float          # monotonic
      status_code: int
      raw_headers: list[tuple[bytes, bytes]]
      body: bytes
  ```
- **Rationale**: Replacement-table guidance — "NamedTuple for immutable
  positional tuples". The module docstring declares these shapes "the
  contract" for a future Redis-backed store; a contract deserves named
  fields. The cache key is four *indistinguishable* `str`s — a swapped
  `(path, method, ...)` construction type-checks today and would silently
  shard the cache wrong. Unpacking (`stored_at, status_code, ... = entry`)
  and hashing are unchanged. Also makes ty's `invalid-named-tuple-override`
  promotion (leaf §1d Tier 2) non-vacuous.
- **Risk**: none — private types, structural drop-in.
- **Verdict**: **EXECUTE-NOW-SAFE**

### F6 — Resolved-mode strings lose their `Literal` precision in plumbing
- **Where**:
  - color: `cli/context.py:188-194` (`_resolve_color -> str`),
    `cli/output.py:109` (`_console_color_args(color: str)`),
    `cli/output.py:129-138` (`Renderer(color: str | None)`)
  - file log format: `core/logging.py:172-177` (`file_format: str = "text"`),
    `cli/context.py:233-245` (`_resolve_log_format -> str`)
  - token source: `core/config.py:64-66` (`Config.source: str | None`)
- **Category**: stringly-typed · **Severity**: med · **Effort**: small
- **Current**: the schema end is already `Literal["auto","always","never"]` /
  `Literal["text","json"]` (settings.py:45-57) — but every function between
  the schema and the consumer widens to `str`, so the docstrings
  (`"auto" | "always" | "never"`, `("flag", "env", or None)`) carry the type
  the signatures dropped.
- **Proposed**:
  ```python
  # cli/output.py
  type ColorMode = Literal["auto", "always", "never"]
  def _resolve_color(...) -> ColorMode: ...
  def __init__(self, mode: OutputMode, ..., color: ColorMode | None = None, ...)

  # core/logging.py
  type FileLogFormat = Literal["text", "json"]
  def configure_logging(..., file_format: FileLogFormat = "text") -> None: ...

  # core/config.py
  source: Literal["flag", "env"] | None = None
  ```
- **Rationale**: Rubric #4. These are closed three/two-value domains the
  schema already proves; widening to `str` mid-pipe means a typo'd
  `Renderer(color="nevr")` or `configure_logging(file_format="jsonl")`
  type-checks and silently falls into the else-branch. One sub-part needs a
  touch more than annotation: `_resolve_log_format`'s
  `if normalized not in ("text", "json"): raise` does not narrow `str` to the
  Literal — restructure to explicit branches
  (`if normalized == "json": return "json"` / `if normalized == "text": return "text"` / raise).
- **Risk**: low; all producers verified to supply members of the literal sets
  (flags come from `click.Choice`, config from the `Literal` schema).
- **Verdict**: **EXECUTE-NOW-SAFE** (color + source trivial; log-format needs
  the small guard restructure)

### F7 — `/healthz` publishes an untyped `dict[str, str]` contract
- **Where**: `src/py_launch_blueprint/web/app.py:143-150`
- **Category**: dict-str-any (contract) · **Severity**: med · **Effort**: small
- **Current**:
  ```python
  @app.get("/healthz", tags=["ops"])
  async def healthz() -> dict[str, str]:
  ```
- **Proposed**:
  ```python
  class Health(BaseModel):
      status: Literal["ok"]
      version: str
      python: str

  @app.get("/healthz", tags=["ops"])
  async def healthz() -> Health: ...
  ```
- **Rationale**: The repo itself established the principle one endpoint down:
  `/readyz` got `response_model=DoctorReport` because "without it the
  snapshot publishes an empty `{}` schema" (app.py:156-158, WEB-50). `/healthz`
  currently publishes `additionalProperties: string` — same defect, smaller.
  Per the leaf §3, the FastAPI return annotation *is* the response model and
  a security/contract boundary.
- **Risk**: none behavioral (identical JSON); OpenAPI snapshot changes → run
  `just export-openapi` (pairs naturally with F1's regen).
- **Verdict**: **EXECUTE-NOW-SAFE**

### F8 — Py API payload narrowing is manual `.get()` chains over `dict[str, Any]`
- **Where**: `src/py_launch_blueprint/core/adapters/py_api.py:128-135`
  (`_to_project(item: dict[str, Any])`), `:90-93` (`_extract_error` payload)
- **Category**: any-boundary · **Severity**: med · **Effort**: moderate
- **Current**:
  ```python
  @staticmethod
  def _to_project(item: dict[str, Any]) -> Project:
      workspace = item.get("workspace") or {}
      return Project(id=str(item.get("gid", item.get("id", ""))), ...)
  ```
- **Proposed** (two options, in ascending strength):
  1. **TypedDict** (static shape doc, no runtime change):
     ```python
     class _WorkspaceRef(TypedDict, total=False):
         name: str
     class _ProjectPayload(TypedDict, total=False):
         gid: str
         id: str
         name: str
         workspace: _WorkspaceRef | None
     ```
  2. **Pydantic `TypeAdapter`** validating the envelope at the boundary
     (leaf §3) — turns malformed upstream payloads into an explicit
     `APIError` instead of today's silent `Project(id="", name="")`.
- **Rationale**: Rubric #2/#7 — this *is* narrowed within one hop (boundary
  discipline holds), so it is not wrong today. But the silent-default mapping
  (`item.get("gid", item.get("id", ""))` → empty-id `Project`) means a
  changed upstream schema degrades data quietly rather than failing loudly.
  Which failure mode is wanted is a design decision, not a mechanical fix.
- **Risk**: option 2 changes runtime failure behavior (better, but a behavior
  change); option 1 is weakly enforced because the data arrives as `Any`.
- **Verdict**: **FOLLOW-UP** (decide silent-default vs validate-loudly first;
  if the current tolerance is intentional, option 1 alone is fine)

### F9 — `cli/options.py` decorators: keep the `cast` — ParamSpec does NOT fit (anti-churn verdict)
- **Where**: `src/py_launch_blueprint/cli/options.py:154,231-234` and `:257-262`
- **Category**: decorator-typing · **Severity**: low · **Effort**: n/a
- **Current**: `def global_options[F: Callable[..., Any]](func: F) -> F:` with
  `cast(F, decorated)`; same shape for `mutation_options`.
- **Verdict on baseline hypothesis 3** ("Consider ParamSpec … to drop
  cast/Any"): **REJECT.** `global_options` is a *signature-changing*
  decorator — it consumes eleven named kwargs Click injects and prepends an
  `AppContext` positional. That is precisely the replacement table's stated
  exception ("decorator that changes the signature — `cast` may still be
  cleanest"): PEP 612 cannot express "consume some keywords, forward the
  rest" (`Concatenate` is positional-only; `P.kwargs` is all-or-nothing).
  The current PEP 695 `[F: Callable[..., Any]]` + `functools.wraps` + `cast`
  is the state-of-the-art shape for Click decorator stacks.
- **Optional trivial precision**: `_GLOBAL_OPTIONS` / `_MUTATION_OPTIONS` are
  `list[Callable[[Any], Any]]` (:55, :240); `click.option(...)` returns an
  identity-typed decorator, so `list[Callable[[Callable[..., Any]], Callable[..., Any]]]`
  is more honest. Marginal value.
- **Verdict**: **NO CHANGE** (bless; record so future audits don't churn it)

### F10 — `OutputMode` dispatch has no exhaustiveness guard
- **Where**: `src/py_launch_blueprint/cli/output.py:150-160` (`render`) and
  `:195-212` (`_render_to_file`)
- **Category**: exhaustiveness · **Severity**: low · **Effort**: small
- **Current**: `if JSON … elif MARKDOWN … else` (text is the implicit fallback).
- **Proposed**: `match self.mode:` with explicit `OutputMode.TEXT` case and
  `case _: assert_never(self.mode)` (rubric #9).
- **Rationale**: In a template repo, "add an output mode" is a likely fork
  activity; today a new `OutputMode.CSV` member silently renders as text at
  both sites. `assert_never` makes ty fail the build until both dispatchers
  handle it.
- **Risk**: control-flow reshuffle at two sites; behavior identical.
- **Verdict**: **FOLLOW-UP** (worthwhile, but it is churn with no present bug)

### F11 — structlog processors: use the library's own alias for the `Any`
- **Where**: `src/py_launch_blueprint/core/logging.py:128,144` (`logger: Any`)
- **Category**: any-boundary (cosmetic) · **Severity**: low · **Effort**: trivial
- **Current**: `def _redact_sensitive(logger: Any, method_name: str, event_dict: EventDict)`
- **Proposed**: `from structlog.typing import WrappedLogger` →
  `logger: WrappedLogger` (the module already imports `EventDict`/`Processor`
  from `structlog.typing`).
- **Rationale**: This `Any` is legitimately third-party-shaped (the reference
  explicitly blesses structlog processors). `WrappedLogger` *is* `Any` under
  the hood — the gain is purely self-documentation: it says "this Any is
  structlog's contract, not our laziness", which the baseline's audit had to
  re-derive.
- **Verdict**: **EXECUTE-NOW-SAFE**

### F12 — Shell-completion object annotated `Any` where inference suffices
- **Where**: `src/py_launch_blueprint/cli/main.py:100`
- **Category**: any-boundary · **Severity**: low · **Effort**: trivial
- **Current**: `comp: Any = comp_cls(cli, {}, _PROG_NAME, _COMPLETE_VAR)`
- **Proposed**: drop the annotation (let ty infer `ShellComplete` from
  `get_completion_class`'s return, already narrowed by the `is None` guard at
  :98) — `comp.source()` is a real `ShellComplete` method.
- **Risk**: none expected, but the explicit `Any` may have been working around
  a click-stubs gap — **verify with one `uv run --extra web ty check` before
  keeping**; if ty objects, restore with a rule-scoped ignore instead of `Any`.
- **Verdict**: **EXECUTE-NOW-SAFE** (pending that one-command check)

### F13 — Blessed boundaries (explicitly no action — record to prevent future churn)
- `core/config.py` TOML layer plumbing (`_read_toml`, `_read_layer`,
  `_read_explicit`, `read_config_for_write`, `write_config_data`,
  `settings_from_layers` input): `dict[str, Any]` is the *correct* type for
  "arbitrary user TOML that must round-trip unknown keys", and every path
  into the core narrows through `Settings.model_validate` — textbook §2
  boundary discipline.
- `web/problems.py` `extensions: dict[str, Any]` and
  `openapi_with_problems() -> dict[str, Any]`: RFC 9457 extension members are
  arbitrary JSON and the OpenAPI dict is FastAPI's own shape.
- `web/idempotency.py:97` `# ty: ignore[unresolved-attribute]` on
  `body_iterator`: starlette's middleware response is a *private*
  `_StreamingResponse` (not a `StreamingResponse` subclass in current
  starlette), so an `isinstance` narrow would be **wrong at runtime** — the
  rule-scoped ignore with its comment is the honest solution.
- `web/app.py:220` `handle_rate_limited(request, exc: Exception)`: the broad
  signature is what starlette's handler registration requires
  (contravariance); the comment + `getattr` is correct.
- `core/logging.py:107` `_otel_trace: Any` soft import: optional-extra
  boundary, deliberately invisible to ty — fine.

---

## Per-file verdicts (rubric §5)

| File | Verdict | Findings |
|---|---|---|
| core/ports.py | **precise** | — (exemplary Protocol port) |
| core/models.py | needs-tightening | F1, F2 |
| core/errors.py | **precise** | — |
| core/settings.py | needs-tightening | F4 (otherwise exemplary `Literal` schema) |
| core/config.py | acceptable-boundary | F4, F6(source); TOML dicts blessed (F13) |
| core/adapters/py_api.py | needs-tightening | F3; F8 follow-up |
| core/adapters/in_memory.py | **precise** | (F2 n/a — structural, no base) |
| core/services/projects.py | **precise** | — |
| core/logging.py | acceptable-boundary | F6(file_format), F11; otel blessed |
| core/diagnostics.py | **precise** | (inherits F1) |
| core/paths.py, core/format.py, composition.py | **precise** | — |
| cli/options.py | acceptable-boundary | F9 (bless) |
| cli/context.py | needs-tightening | F6 |
| cli/output.py | acceptable-boundary | F6(color); F10 follow-up |
| cli/main.py | acceptable-boundary | F12 |
| cli/groups.py | **precise** | F2 (add `@override`) |
| cli/commands/{config,projects}.py | **precise** | (consume F4's fix) |
| web/problems.py | acceptable-boundary | blessed (F13) |
| web/idempotency.py | needs-tightening | F5, F2; ignore blessed |
| web/middleware.py | **precise** | F2 |
| web/app.py | acceptable-boundary | F7 |
| web/deps.py, web/settings.py, web/versioning.py, web/routers/projects.py, web/telemetry.py, web/logging.py | **precise** | — |

---

## Enforcement-config verdict (leaf §1d + §4)

**AGREE with the package as a whole**, with two refinements:

| Recommendation | Verdict | Notes |
|---|---|---|
| `python-version = "3.12"` pin | **AGREE — highest priority** | ty defaults to 3.14; unpinned, ty would bless 3.13/3.14-only stdlib usage that breaks on the declared floor. Zero cost, real hazard. |
| Tier 1 rules → error (`ambiguous-protocol-member`, `blanket-ignore-comment`, `invalid-ignore-comment`, `ignore-comment-unknown-rule`) | **AGREE** | Verified zero-cost against source: both existing ignores are rule-scoped; `ports.py` members fully annotated. Pure guard-rail. |
| Tier 2 → error (`ineffective-final`, `invalid-enum-member-annotation`, `invalid-named-tuple-override`) | **AGREE** | No current violations; F5 introduces NamedTuples, making the third rule non-vacuous. |
| Tier 3 `deprecated = "error"` | **AGREE with leaf's hold-back** | Keep at `warn` — a template repo must not let a dependency's deprecation fail every fork's CI. |
| `error-on-warning = true` explicit | **AGREE** | Set it explicitly per caveat C1, and do the leaf's own empirical confirm (inject a `deprecated` call, observe exit code) in the same PR. |
| `[[tool.ty.overrides]]` for `tests/**` | **MODIFY** | Currently dead weight: CI runs `ty check src/py_launch_blueprint/` only, so tests never enter scope. Either expand the check scope to `tests/` *and* add the override together, or drop the block until then. |
| ruff `TC` | **AGREE, with a mandatory caveat the leaf understates** | Before enabling, configure `[tool.ruff.lint.flake8-type-checking] runtime-evaluated-base-classes = ["pydantic.BaseModel", "pydantic_settings.BaseSettings"]` (and audit FastAPI `Annotated` DI params). Naive TC autofix moves annotations Pydantic/FastAPI evaluate **at runtime** behind `if TYPE_CHECKING:` and breaks the app. "Low-noise, mechanical" holds only with that config. |
| ruff `ANN` (scoped) | **AGREE** | Source is already ~fully annotated (this audit found no unannotated defs), so churn ≈ 0 — it is exactly the annotation-*presence* gate ty cannot provide (leaf §0), and it closes the Pyright-strict(IDE) vs ty(CI) divergence. Adopt with `per-file-ignores` `"tests/*" = ["ANN"]` (mirror the existing S-rule exemptions incl. `init/tests/**`) and global `ANN401` ignore initially — F3/F4/F11 shrink the `Any` surface first. |
| `PYI` | **AGREE — skip** | No shipped stubs. |

**Ordering note**: land F1/F7 (snapshot-touching) together with one
`just export-openapi` run; land the ty config + ANN/TC in a separate,
revert-friendly commit after the C1 empirical check.

## Execute-now-safe set (in suggested order)

1. F1 (status Literal) + F7 (healthz model) + one `just export-openapi`
2. F2 (`@override` sweep)
3. F3, F4, F11, F12 (Any-surface shrink; F12 needs one ty run to confirm)
4. F5 (NamedTuples), F6 (mode Literals)
5. Enforcement: `[tool.ty]` block per verdict above, then ruff `ANN`+`TC`
   with the runtime-evaluated-base-classes config

Follow-up queue: F8 (boundary validation design decision), F10 (assert_never
dispatch), F9 recorded as no-change.
