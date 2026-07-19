# Independent adversarial type audit — Codex

Date: 2026-07-18

This is an analysis-only second-lens audit of the requested production source.
I read the reference leaf and baseline in full before opening the source, then
read every scoped file in full. No existing repository file was intentionally
changed.

## Executive verdict

The core port and service types are precise, and most explicit `Any` use is
clustered at real framework or I/O edges. The main exception is the Py API
adapter: unvalidated `response.json()` data is allowed to flow through
`dict[str, Any]` into domain-model construction. The config path has lower-risk
but cheap precision wins: all currently writable settings coerce to `str`, and
parsed TOML can be represented by a recursive TOML value alias instead of
`Any`.

The reference leaf's proposed configuration must not be copied as-is. Against
the repo-pinned `ty 0.0.39`, `blanket-ignore-comment` is an unknown rule and the
optional `analysis.strict-literal-narrowing` key is not supported. Combined
with the recommended `error-on-warning = true`, the unknown-rule diagnostic
makes the proposed `ty` command exit 1. The proposed Ruff rollout also misses
`init/tests/**`, producing 142 annotation findings there alone.

## Audit accounting

- `rg` finds 38 source lines containing `Any` (40 tokens). Seven lines are
  imports, leaving 31 actual type-use lines (33 tokens). Findings C1–C16 cover
  every one of those 31 lines.
- Pinned tools observed: `ty 0.0.39` and Ruff `0.15.14`.
- Baseline `ty check src/py_launch_blueprint` passes.
- The known, supported Tier 1/Tier 2 promotions all pass against production
  source: `ambiguous-protocol-member`, `invalid-ignore-comment`,
  `ignore-comment-unknown-rule`, `ineffective-final`,
  `invalid-enum-member-annotation`, and `invalid-named-tuple-override`.
- `ports.py` and `services/projects.py` are precise. The structural Protocol is
  appropriate and does not need `@runtime_checkable`.

Concrete aliases and boundary models referenced below are:

```python
import datetime
from collections.abc import Callable, Mapping, Sequence
from typing import Concatenate, Literal, ParamSpec, Protocol, TypeVar

type TomlScalar = (
    str
    | int
    | float
    | bool
    | datetime.datetime
    | datetime.date
    | datetime.time
)
type TomlValue = TomlScalar | list[TomlValue] | dict[str, TomlValue]
type TomlDocument = dict[str, TomlValue]

type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)
type RequestParam = str | int

type TokenSource = Literal["flag", "env"]
type ConfigValueSource = Literal[
    "flag", "env", "config", "default", "dry-run", "file"
]
type DoctorStatus = Literal["ok", "warn", "error"]
type FileLogFormat = Literal["text", "json"]

P = ParamSpec("P")
R = TypeVar("R")

class _OptionDecorator(Protocol):
    def __call__[F: Callable[..., object]](self, func: F, /) -> F: ...

# Pydantic boundary models, with gid/id normalized by AliasChoices.
class _WorkspacePayload(BaseModel):
    id: str = Field(validation_alias=AliasChoices("gid", "id"))
    name: str

class _WorkspaceRef(BaseModel):
    name: str

class _ProjectPayload(BaseModel):
    id: str = Field(validation_alias=AliasChoices("gid", "id"))
    name: str
    workspace: _WorkspaceRef | None = None

class _WorkspaceListEnvelope(BaseModel):
    data: list[_WorkspacePayload] = []

class _ProjectListEnvelope(BaseModel):
    data: list[_ProjectPayload] = []

class _ProjectEnvelope(BaseModel):
    data: _ProjectPayload | None = None

class _ApiErrorItem(BaseModel):
    message: str

class _ApiErrorEnvelope(BaseModel):
    errors: list[_ApiErrorItem] = []
```

## Findings

| id | file:line | category | severity | current type | proposed precise type | rationale | risk/effort | verdict |
|---|---|---|---|---|---|---|---|---|
| C1 | `src/py_launch_blueprint/core/adapters/py_api.py:63,74,87-92,96-101,113-134` | precision gap — unvalidated external boundary | high | `_request -> dict[str, Any]`; `data: dict[str, Any]`; implicit `Any` error payload; `_to_project(item: dict[str, Any])` | Generic `_request[T: BaseModel](..., response_model: type[T], ...) -> T` plus the concrete `_WorkspaceListEnvelope`, `_ProjectListEnvelope`, `_ProjectEnvelope`, `_ApiErrorEnvelope`, and `_ProjectPayload` models defined above | `requests.Response.json()` returns `Any`. The adapter immediately assumes mappings, lists, string names, and nested workspaces; malformed or changed upstream JSON can therefore raise `AttributeError`/`KeyError` or silently produce empty domain fields. This is exactly the external edge where runtime validation belongs. Catch `ValidationError`/`ValueError` and translate it to `APIError`. | medium behavior risk / medium effort | FOLLOW-UP |
| C2 | `src/py_launch_blueprint/core/adapters/py_api.py:56-67` | precision gap — overly broad request plumbing | med | `**kwargs: Any` | Explicit keyword `params: Mapping[str, RequestParam] \| None = None` | Every in-repo caller passes only `params`. An open-ended `**kwargs` hides misspelled request options and makes the internal adapter surface broader than its actual contract. If future options are needed, add named parameters or a concrete `TypedDict` with `Unpack`. | low risk / low effort | EXECUTE-NOW-SAFE |
| C3 | `src/py_launch_blueprint/core/adapters/py_api.py:106-111` | precision gap — container value | low | `dict[str, Any]` | `dict[str, RequestParam]` | The only values are integer `limit` and string `opt_fields`/`workspace`; `Any` is unnecessary. | negligible risk / trivial effort | EXECUTE-NOW-SAFE |
| C4 | `src/py_launch_blueprint/core/settings.py:105-114`; `src/py_launch_blueprint/core/config.py:239-255` | precision gap — core return value | med | `coerce_value(...) -> Any`; `set_config_value(...) -> Any` | Both return `str` | Every field in `OutputSettings` and `LoggingSettings` is currently `str` or a string `Literal`, and both functions return one of those validated fields. This `Any` crosses from the Pydantic boundary into config mutation and CLI rendering even though the closed schema is homogeneous. | low risk / low effort; update if a non-string setting is later introduced | EXECUTE-NOW-SAFE |
| C5 | `src/py_launch_blueprint/core/config.py:88,96,106,155,195,213` | precision gap — TOML boundary propagation | low | `dict[str, Any]`, `list[dict[str, Any]]` | `_read_toml`, `_read_explicit`, and `read_config_for_write` return `TomlDocument`; `_read_layer -> tuple[TomlDocument, str \| None]`; `layers: list[TomlDocument]`; `write_config_data(..., data: Mapping[str, TomlValue]) -> None` | `Any` is understandable at the `tomllib` stub boundary, but TOML has a finite recursive value domain. A single checked cast immediately after `tomllib.loads` contains the library's broad return type instead of propagating it through read/merge/write operations. | low behavior risk / low-medium type-refactor effort | EXECUTE-NOW-SAFE |
| C6 | `src/py_launch_blueprint/core/settings.py:138-152` | precision gap — TOML layer merge | low | `layers: list[dict[str, Any]]`; `merged: dict[str, dict[str, Any]]` | `layers: Sequence[Mapping[str, TomlValue]]`; `merged: dict[str, dict[str, TomlValue]]` | These values are parsed TOML, not arbitrary Python objects. `Mapping`/`Sequence` also describe the read-only input contract more accurately while retaining a mutable merged result. | low risk / low effort once C5 alias exists | EXECUTE-NOW-SAFE |
| C7 | `src/py_launch_blueprint/core/config.py:186-192` | precision gap — raw stored value | low | `get_file_value(...) -> Any` | `TomlValue \| None` | The function intentionally returns an unvalidated value as stored, so `str` would be too narrow; the recursive TOML union is the exact domain and preserves the documented `None` sentinel. | negligible risk / trivial effort after C5 | EXECUTE-NOW-SAFE |
| C8 | `src/py_launch_blueprint/web/problems.py:76-93` | precision gap — JSON extension boundary | low | `extensions: dict[str, Any] \| None`; implicit `dict[str, Any]` from `model_dump` | `extensions: Mapping[str, JsonValue] \| None`; `body: dict[str, JsonValue]` after one boundary cast from `model_dump(mode="json")` | RFC 9457 extension members are open by key, not open to arbitrary non-JSON Python objects. The recursive JSON union retains extensibility while statically preventing values that `JSONResponse` cannot serialize. | low risk / low effort | EXECUTE-NOW-SAFE |
| C9 | `src/py_launch_blueprint/web/problems.py:104-130` | LEGITIMATE boundary type — keep | low | `openapi_with_problems() -> dict[str, Any]` | `dict[str, Any]` unchanged (FastAPI's `app.openapi`/`openapi_schema` contract) | The function mutates a deeply recursive, extension-friendly OpenAPI document owned and typed by FastAPI as `dict[str, Any]`. Introducing a local partial `TypedDict` would require repeated casts and would not make the external framework contract safer. | no change / no effort | FOLLOW-UP |
| C10 | `src/py_launch_blueprint/cli/main.py:97-101` | precision gap — unnecessary framework result `Any` | low | `comp: Any` | `comp: click.shell_completion.ShellComplete` (or omit the annotation and use the inferred `ShellComplete`) | Installed Click declares `get_completion_class -> type[ShellComplete] \| None`; after the `None` guard, construction has the exact base type. | negligible risk / trivial effort | EXECUTE-NOW-SAFE |
| C11 | `src/py_launch_blueprint/cli/options.py:55,240` | precision gap — decorator collection | low | `list[Callable[[Any], Any]]` | `list[_OptionDecorator]` using the concrete generic Protocol defined above | Click's `option()` decorator preserves the callable it receives (`Callable[[FC], FC]`). The current list annotation erases that relationship twice per element. A generic callable Protocol records it without claiming a uniform command signature. | low risk / low-medium checker-validation effort | FOLLOW-UP |
| C12 | `src/py_launch_blueprint/cli/options.py:154,172,231-234` | precision gap — signature/result erasure | med | `F: Callable[..., Any]`; wrapper return `Any`; `decorated: Any`; `cast(F, decorated)` | `global_options[**P, R](func: Callable[Concatenate[AppContext, P], R]) -> Callable[P, R]`; wrapper return `R`; decorated value `Callable[P, R]` after one narrow cast at the Click boundary | The decorator changes the signature by injecting `AppContext`, so preserving `F -> F` is not truthful. `Concatenate` expresses the removed first parameter and a result type variable prevents return-type `Any` from leaking. Click's dynamically injected option keywords still require a boundary cast. | medium risk / medium effort; verify every decorated command with ty and CLI tests | FOLLOW-UP |
| C13 | `src/py_launch_blueprint/cli/options.py:159,171` | LEGITIMATE boundary type — keep | low | `*args: Any`; `**kwargs: Any` | `Any` unchanged at these two forwarding slots | Click constructs argument values and injects both shared and command-specific keywords at runtime. Because this wrapper also changes the callable signature, Python's current `ParamSpec`/`Unpack` forms cannot describe both the fixed injected keyword set and arbitrary per-command keywords without a cast. Keep the dynamism isolated here while making the public decorator result generic as in C12. | no behavior risk / no action beyond targeted `ANN401` exemptions | FOLLOW-UP |
| C14 | `src/py_launch_blueprint/cli/options.py:257-262` | precision gap — signature-preserving decorator | low | `F: Callable[..., Any]`; `decorated: Any`; `cast(F, decorated)` | `mutation_options[**P, R](func: Callable[P, R]) -> Callable[P, R]` with `decorated: Callable[P, R]` | Unlike `global_options`, this decorator explicitly adds no wrapper. Click's option decorator preserves the input callable type, so ordinary `ParamSpec`/result typing is sufficient and the `Any` staging value is unnecessary. | low risk / low effort | EXECUTE-NOW-SAFE |
| C15 | `src/py_launch_blueprint/core/logging.py:104-109,127-139` | precision gap — optional dynamic module | low | `_otel_trace: Any` | `_otel_trace: _TraceApi \| None`, where `_TraceApi`, `_Span`, and `_SpanContext` are local Protocols for `get_current_span()`, `get_span_context()`, `is_valid`, `trace_id`, and `span_id`; cast the one `import_module` result to `_TraceApi` | The optional import is a legitimate dynamic boundary, but `Any` need not control all downstream attribute access. A small structural interface contains the trust to one cast and documents the exact OpenTelemetry surface used. | low runtime risk / medium maintenance effort if upstream API changes | FOLLOW-UP |
| C16 | `src/py_launch_blueprint/core/logging.py:127-145` | LEGITIMATE third-party callback boundary | low | `logger: Any` in two structlog processors | `logger: structlog.typing.WrappedLogger` | Structlog's own `Processor` contract deliberately defines `WrappedLogger` as `Any` because it makes no assumptions about the wrapped logger. Using the semantic upstream alias documents that this is intentional and avoids pretending the app owns a narrower type. | negligible risk / trivial effort | EXECUTE-NOW-SAFE |
| C17 | `src/py_launch_blueprint/core/config.py:64-66,167-174`; `src/py_launch_blueprint/core/models.py:102-104,135-140,173-180`; `src/py_launch_blueprint/core/logging.py:172-178` | precision gap — closed string domains | low | token/config sources, doctor status, and file log format are plain `str` | `Config.source` and `DiagnosticsBundle.token_source: TokenSource \| None`; `ConfigValue.source: ConfigValueSource \| None`; `DoctorCheck.status: DoctorStatus`; `configure_logging(..., file_format: FileLogFormat = "text")` | Each domain is closed by the actual branches and call sites. `Literal` types catch misspellings and make `DoctorReport.has_error()` and logging format branching exhaustively meaningful. | low risk / low effort | EXECUTE-NOW-SAFE |
| C18 | `src/py_launch_blueprint/core/models.py:86,89,92,95,106,109,121,124,127,148,151,154,183,186,189`; `src/py_launch_blueprint/web/idempotency.py:66` | override safety | low | correctly typed overrides without markers | Add `@typing.override` to the listed subclass methods | The repo floor is Python 3.12. These are nominal subclass overrides (unlike the structural port adapter), so PEP 698 lets ty detect a future base-method rename or signature drift. | negligible risk / mechanical effort | EXECUTE-NOW-SAFE |
| C19 | `src/py_launch_blueprint/web/idempotency.py:92-103`; `src/py_launch_blueprint/web/problems.py:104-130` | LEGITIMATE framework-stub mismatch — keep scoped suppressions | low | `Response` lacks the runtime `_StreamingResponse.body_iterator` member in Starlette's public annotation; FastAPI exposes `openapi` as a method while permitting replacement | Keep `Response` and `Callable[[], dict[str, Any]]`, with the existing rule-scoped `ty: ignore[unresolved-attribute]` and `ty: ignore[invalid-assignment]` | Starlette's `call_next` annotation says `Response` but its implementation returns private `_StreamingResponse`; importing that private class would be more brittle than the narrow suppression. FastAPI intentionally supports replacing `app.openapi`. Both ignores are specific and live. | no change / no effort | FOLLOW-UP |
| C20 | `research/reference/python-typing-ty-2026-07-18.md:88-104` | config disagreement — nonexistent ty rule | high | recommends `blanket-ignore-comment = "error"` together with `error-on-warning = true` | Omit `blanket-ignore-comment`; no equivalent rule exists in pinned `ty 0.0.39` | `ty 0.0.39` reports `warning[unknown-rule]` for this key. With the same block's `error-on-warning = true`, that warning exits 1, so copying the exact recommendation breaks CI before checking code. The existing two ignores are already rule-scoped. | zero behavior risk / trivial config correction | EXECUTE-NOW-SAFE |
| C21 | `research/reference/python-typing-ty-2026-07-18.md:112-113` | config disagreement — unsupported ty option | med | recommends optional `analysis.strict-literal-narrowing = true` | Omit the key for ty `0.0.39` | The pinned binary rejects the key with a TOML parse error and exit 2; its accepted analysis keys are `respect-type-ignore-comments`, `allowed-unresolved-imports`, and `replace-imports-with-any`. | zero behavior risk / trivial correction | EXECUTE-NOW-SAFE |
| C22 | `research/reference/python-typing-ty-2026-07-18.md:69-104,212-216` | config disagreement — warning policy contradiction | med | leaves `deprecated` and other warning rules unpromoted but sets `error-on-warning = true` | `error-on-warning = false` with only the chosen rules promoted to `error` | Live probing showed warning diagnostics exit 0 by default and exit 1 when `error-on-warning` is true. Therefore the proposed setting also gates unpromoted warnings such as dependency deprecations, contradicting the stated Tier 3 judgment call. If the desired policy is genuinely “all warnings fail,” say so and drop the tier distinction. | policy risk / low effort | FOLLOW-UP |
| C23 | `research/reference/python-typing-ty-2026-07-18.md:106-110`; `.github/workflows/ci.yml:95-110` | config disagreement — ineffective test override | med | downgrades `possibly-unresolved-reference` to `warn` for tests | No test override in the current source-only CI configuration | CI invokes ty only on `src/py_launch_blueprint/`, so the override is inactive. Even if tests are added, `error-on-warning = true` means the downgrade still fails CI. A live test check produced five diagnostics, but they were `unresolved-import` and `unresolved-attribute`, not the overridden rule. | low immediate risk / low effort; requires a separate decision before expanding CI scope | EXECUTE-NOW-SAFE |
| C24 | `research/reference/python-typing-ty-2026-07-18.md:174-182`; `pyproject.toml:189-192`; `init/init.py:166` | config disagreement — Ruff ANN rollout scope | med | recommends global `ANN` with only `"tests/*" = ["ANN"]` and global `ANN401` ignore | Also exempt `"init/tests/**" = ["ANN"]`, and annotate `derive: Callable[[], str] \| None = None` at `init/init.py:166` (or scope the first rollout to `src/py_launch_blueprint/**`) | The suggested `tests/*` pattern does suppress the nested main test tree in this Ruff version, but it does not cover `init/tests/**`: that tree alone emits 142 ANN findings. One additional production init helper lacks a parameter annotation. Enabling the recommendation as-is creates immediate CI churn unrelated to the audited package. | medium CI disruption / low config effort plus deferred test cleanup | EXECUTE-NOW-SAFE |
| C25 | `research/reference/python-typing-ty-2026-07-18.md:174-182`; `src/py_launch_blueprint/cli/options.py:234,262`; `init/_engine.py:23`; `init/discover.py:31`; `init/tests/test_doctor.py:14` | config disagreement — Ruff TC is not zero-churn | med | describes `TC` as low-noise/mechanical and recommends adding it directly | Resolve two `TC006` findings by quoting `cast("F", ...)`; separately review three `TC003` moves into `TYPE_CHECKING` before adding `TC` to the global select | A live no-fix run finds five project-wide TC errors. The two source `TC006` fixes are safe. Ruff marks the three import moves as hidden unsafe fixes, so they must be reviewed rather than treated as unconditional mechanical autofix. Also note this repo has `fix = true`; plain `ruff check` can mutate safe findings unless audit commands pass `--no-fix`. | medium CI disruption / low implementation effort | EXECUTE-NOW-SAFE |
| C26 | `research/reference/python-typing-ty-2026-07-18.md:174-182`; `src/py_launch_blueprint/cli/options.py:159,171`; `src/py_launch_blueprint/core/adapters/py_api.py:62`; `src/py_launch_blueprint/core/config.py:186,239`; `src/py_launch_blueprint/core/logging.py:128,144`; `src/py_launch_blueprint/core/settings.py:105` | config disagreement — global ANN401 blind spot | med | recommends globally ignoring `ANN401` initially | Enable `ANN` without a global `ANN401` ignore after C1–C16; retain only two targeted `# noqa: ANN401` exemptions for the legitimate Click forwarding slots at `cli/options.py:159,171` | Ruff reports nine production `ANN401` diagnostics. Most correspond to concrete precision gaps identified in this audit; a global ignore would hide them indefinitely. `ANN` also cannot see implicit local `Any` from `response.json()`, so manual boundary review remains necessary. | low runtime risk / medium staged-cleanup effort | EXECUTE-NOW-SAFE |

## Dedicated disagreement list for reference-leaf configuration

These are all recommendations from the reference leaf that I disagree with as
written:

1. **`blanket-ignore-comment = "error"` — disagree (C20).** It is not a rule in
   pinned ty 0.0.39, and the full proposed block exits 1 because warnings are
   configured as fatal.
2. **Optional `analysis.strict-literal-narrowing = true` — disagree (C21).** The
   pinned binary rejects the configuration with exit 2.
3. **`error-on-warning = true` while treating `deprecated` as a non-gating
   judgment call — disagree (C22).** The live exit-code probe proves all warning
   diagnostics become gating.
4. **The test `possibly-unresolved-reference = "warn"` override — disagree
   (C23).** Current CI does not check tests, the recommended fatal-warning policy
   defeats the downgrade, and the real test diagnostics are different rules.
5. **Ruff ANN with only `tests/*` relaxed — disagree (C24).** It misses
   `init/tests/**` and produces 142 annotation findings there.
6. **Ruff TC as a direct low-noise/mechanical addition — disagree as rollout
   guidance (C25).** It creates five immediate errors; three fixes are explicitly
   classified as unsafe by Ruff and need review.
7. **Global `ANN401` ignore — disagree (C26).** It suppresses five real
   precision-gap signatures and two semantically improvable structlog callback
   annotations in addition to the two legitimate Click forwarding slots.

I agree with promoting the six supported Tier 1/Tier 2 rules listed in Audit
accounting, and the current production source passes them. I also agree with
adding ANN and TC after the corrected baseline/scoping work. An explicit
`python-version = "3.12"` is harmless documentation, but it is redundant in
this repo: `ty -vv` shows that ty already resolves `requires-python = ">=3.12"`
to Python 3.12 rather than falling back to 3.14.

## Severity totals

- high: 2
- med: 9
- low: 15

Total findings: 26.

## Recommended order

1. Correct the proposed config before adoption (C20–C26), especially C20.
2. Validate upstream API JSON at the adapter boundary (C1), then narrow its
   request surface and params (C2–C3).
3. Remove the cheap config return-value `Any` leak (C4), then introduce the
   shared TOML aliases (C5–C7).
4. Apply the low-risk framework/model refinements (C8, C10, C14, C16–C18).
5. Treat the global Click decorator and optional OTel Protocol as focused
   follow-ups (C11–C13, C15); retain the justified boundaries (C9, C13, C16,
   C19).
