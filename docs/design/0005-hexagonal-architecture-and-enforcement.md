# 0005 — Hexagonal architecture & boundary enforcement (the HEX-xx baseline)

- **Status:** Proposed
- **Type:** Design / convention
- **Created:** 2026-06-14
- **Applies to:** `src/py_launch_blueprint/` package structure, the CLI and web
  front-ends, and the dev/CI tooling that keeps the boundaries honest.

This doc specifies how the core logic is structured so it can be driven from
multiple front-ends (CLI today, web behind the `web` extra, more later) and
how those boundaries are *enforced* mechanically rather than by convention.
Each rule carries a `HEX-xx` id so later work can cite and extend it. It is
motivated by the interface-pattern research and supersedes nothing — it makes
the *existing* core/cli/web split explicit and gives it teeth.

## Context

The package already has the right instinct: business logic lives in
`core/`, and both `cli/` and `web/` import it without importing each other.
That is the **shared in-process core library** pattern (a.k.a. *functional
core, imperative shell*): the same `ProjectsService` and `Project` models
serve `plbp projects list` and `GET /v1/projects`. We deliberately do **not**
adopt the *CLI-over-HTTP* pattern (CLI as a thin client of the running web
service) — that boundary only earns its cost when the CLI's job is to manage
a remote, multi-tenant deployment, which is not the case here.

What is missing is (a) a clean split between *application logic* and
*infrastructure* — today `ProjectsService` is both the use-case **and** the
HTTP client — and (b) any mechanism that *prevents* the boundaries from
eroding. This doc fixes both.

## Decision

Adopt **Ports & Adapters (hexagonal) architecture** for each capability, with
a small **shared kernel**, **dependency inversion** at every I/O seam, and a
**composition root** that wires concrete adapters to abstract ports. Enforce
the resulting boundaries with `import-linter` (layer rules), `tach`
(bounded-context isolation + strict interfaces), `ruff` (framework-bleed),
and `ty` (port satisfaction).

## The rings & layout

- **HEX-01 — four rings, dependencies point inward only.** From the centre
  out: `domain` → `application` → `adapters` → `interfaces`. An inner ring
  may never import an outer one. The domain knows nothing; the application
  knows the domain and its own ports; adapters know the application; the
  front-ends know everything beneath them. This is the one load-bearing rule;
  everything else is detail.

- **HEX-02 — capabilities are bounded contexts (feature-first growth
  target).** Each capability is a self-contained hexagon. The *driven*
  adapters (e.g. the HTTP client for projects) live **inside** the capability
  because they are specific to it; the *driving* adapters (CLI, web) are
  cross-cutting entrypoints that sit **above** all capabilities, because one
  CLI exposes commands from many of them.

  ```
  src/py_launch_blueprint/
  ├── shared/                       # shared kernel: depended on by all, depends on nothing
  │   ├── errors.py                 #   PyError, ConfigError, AuthError, APIError + ExitCode
  │   ├── logging.py  paths.py  config.py  settings.py  format.py
  │
  ├── projects/                     # one bounded context = one hexagon
  │   ├── domain/
  │   │   └── models.py             #   Project  (pure entity; workspace stays a str)
  │   ├── application/
  │   │   ├── ports.py              #   ProjectsRepository  (Protocol)        ← driven port
  │   │   ├── services.py           #   ProjectsService     (use-cases only)
  │   │   └── errors.py             #   ProjectNotFoundError, WorkspaceNotFoundError    ← application errors
  │   └── adapters/
  │       ├── py_api.py             #   PyApiProjectsRepository (requests)    ← driven adapter
  │       └── in_memory.py          #   InMemoryProjectsRepository            ← test/dev adapter
  │
  ├── diagnostics/                  # capability WITHOUT an external port — see HEX-05
  │
  ├── interfaces/                   # driving/primary adapters — the ONLY place frameworks live
  │   ├── cli/
  │   │   ├── main.py  context.py  options.py  output.py
  │   │   ├── view_models.py        #   ProjectList / CLIResult table rendering
  │   │   └── commands/projects.py
  │   └── web/
  │       ├── app.py  deps.py  problems.py
  │       └── routers/projects.py
  │
  └── composition.py                # composition root: build_projects_service(token)
  ```

- **HEX-03 — start layer-first, migrate to feature-first at the second
  capability.** Until a second context exists, the current single-package
  shape (`core/` + `cli/` + `web/`) is acceptable; the refactor in
  "Migration" below is staged so the directory reshape (HEX-02) is the *last*
  step, not the first.

- **HEX-04 — the composition root is the only place that names concrete
  adapters.** `composition.py` constructs `PyApiProjectsRepository` and
  injects it into `ProjectsService`. Nothing in `domain`/`application`/
  `adapters` may import `composition`; only the `interfaces` may. (This is
  enforced — see HEX-31 — which is what neutralises the otherwise-real
  circular-import risk of a top-level composition module.)

- **HEX-05 — not every capability is a full hexagon.** `diagnostics`
  (`doctor`, the redacted bundle) has **no external dependency to invert** —
  it reads env vars, the Python version, and config. Forcing a
  `DiagnosticsRepository` port on it would be cargo-cult. It stays a plain
  module of pure functions returning result models. Apply hexagonal structure
  *where there is an I/O seam to abstract*, not reflexively.

## Naming & calling conventions

- **HEX-10 — domain entities are pure and named for the thing.** `Project`
  lives in `projects/domain/models.py`, has no I/O, and does not raise
  application errors. A workspace is a **string** (its name), not a
  `Workspace` entity — promote it only if it grows identity/behaviour.

- **HEX-11 — ports are `Protocol`s named for the role, methods named for the
  domain verb.** One port per role; merge rather than over-split. We use a
  single `ProjectsRepository` (not a separate `WorkspacesRepository`) because
  workspace resolution is an implementation concern of the same upstream:

  ```python
  # projects/application/ports.py
  from typing import Protocol
  from py_launch_blueprint.projects.domain.models import Project

  class ProjectsRepository(Protocol):
      def list_projects(self, *, workspace_gid: str | None, limit: int) -> list[Project]: ...
      def get_project(self, project_id: str) -> Project | None: ...   # None = absent
      def resolve_workspace_gid(self, name: str) -> str | None: ...    # None = unknown
  ```

  Method names match the use-case names across rings (`list_projects`, not
  `list`) so a single grep finds the whole call chain.

- **HEX-12 — `None` means "absent", exceptions mean "broke".** A port method
  returns `None`/`[]` for *legitimate absence* (no such id, empty result) and
  *raises* `APIError` for *transport failure*. The **application service**, not
  the adapter, decides that absence is a user-facing error and raises the
  application error:

  ```python
  # projects/application/services.py
  class ProjectsService:
      def __init__(self, projects: ProjectsRepository) -> None:
          self._projects = projects

      def list_projects(self, *, workspace: str | None = None, limit: int = 200) -> list[Project]:
          gid = None
          if workspace:
              gid = self._projects.resolve_workspace_gid(workspace)
              if gid is None:
                  raise WorkspaceNotFoundError(f"Workspace not found: {workspace}")
          return self._projects.list_projects(workspace_gid=gid, limit=limit)

      def get_project(self, project_id: str) -> Project:
          project = self._projects.get_project(project_id)
          if project is None:
              raise ProjectNotFound(f"Project not found: {project_id}")
          return project
  ```

- **HEX-13 — adapters own transport and mapping.** `requests.Session`,
  `BASE_URL`, the `_request`/`_extract_error` helpers, and the
  `raw dict → Project` mapping (`_to_project`) all live in the driven adapter.
  A second adapter (a fake, a CSV, a GraphQL backend) brings its own mapping.

  ```python
  # projects/adapters/py_api.py
  class PyApiProjectsRepository:                # structurally satisfies ProjectsRepository
      BASE_URL = "https://app.py.com/api/1.0"
      def __init__(self, token: str, timeout: int = 30) -> None: ...
      def list_projects(self, *, workspace_gid, limit) -> list[Project]: ...
      def get_project(self, project_id) -> Project | None: ...   # None on 404, raise on 5xx
      def resolve_workspace_gid(self, name) -> str | None: ...
      @staticmethod
      def _to_project(item: dict) -> Project: ...
  ```

- **HEX-14 — one error hierarchy in the shared kernel; mapping lives in each
  driving adapter.** Keep `PyError`/`ConfigError`/`AuthError`/`APIError` in
  `shared/errors.py`. **Keep `exit_code` as a class attribute on the
  exceptions** — it is the single source of truth shared by every front-end,
  and the current design already does this well; do **not** duplicate it into
  a CLI-side lookup table. Each front-end *translates* the same exception:
  the CLI to its `ExitCode`, the web layer to an HTTP status in
  `web/problems.py` (the `PyError → status` table already mirrors the
  `ExitCode` taxonomy). *New* errors specific to a capability
  (`ProjectNotFoundError`) live in that capability's `application/errors.py` and
  subclass the shared base.

- **HEX-15 — view models are a CLI concern.** `ProjectList`/`CLIResult` with
  `table_columns()`/`table_rows_rich()`/OSC-8 links move to
  `interfaces/cli/view_models.py`. The pure `Project` stays in the domain.
  The web layer serialises `Project` directly; the CLI wraps it in a view
  model for rendering. Both consume the *same* domain object.

- **HEX-16 — front-ends compose, call, translate.** Every driving adapter
  follows the same three-beat shape — build the service from the composition
  root, call the use-case, render/translate:

  ```python
  # interfaces/cli/commands/projects.py
  def list_projects(app, workspace, limit):
      svc = build_projects_service(require_token(app))      # compose (not `new`)
      projects = svc.list_projects(workspace=workspace, limit=limit)  # call core
      app.renderer.render(ProjectList(projects=projects))   # render (view model)

  # interfaces/web/deps.py
  def get_projects_service(config: ConfigDep) -> ProjectsService:
      return build_projects_service(config.token)           # same composition root
  ```

## Enforcement

Convention without enforcement decays. Five mechanisms, each at the cheapest
stage that can catch its class of error:

| Tool | Purpose | When |
|---|---|---|
| `import-linter` | Layer dependency rules + framework-bleed (HEX-01/HEX-32), authoritative | `just check` + pre-push hook |
| `tach` | Bounded-context isolation (HEX-31) | `just check` |
| `ruff` TID251 | Fast framework-bleed guard in `core/` (pre-commit first line) | pre-commit (nested `core/ruff.toml`) |
| `ty` / pyright | Port (`Protocol`) satisfaction | `just check` (already running) |
| `__all__` | IDE ergonomics + documentation of the public surface | at authoring time |

All four executable checks are wired today against the current layer-first
layout (`core` / `cli` / `web`): `import-linter` and `tach` run in `just check`
(import-linter also at pre-push), and `ruff` TID251 rides the existing
pre-commit ruff hook via a nested `core/ruff.toml`. Framework-bleed is enforced
in two places on purpose — `ruff` as the fast pre-commit first line scoped to
`core/`, `import-linter` as the authoritative graph-wide check; `import-linter`
is the system of record where they overlap.

- **HEX-30 — `import-linter` owns the layer rule.** Its `layers` contract
  expresses HEX-01 in a single declaration; a `forbidden` contract keeps the
  two front-ends apart. Config lives in `pyproject.toml`:

  ```toml
  [tool.importlinter]
  root_package = "py_launch_blueprint"

  [[tool.importlinter.contracts]]
  name = "Hexagonal layers (inner rings know nothing of outer)"
  type = "layers"
  layers = ["interfaces", "adapters", "application", "domain"]
  containers = ["py_launch_blueprint.projects"]

  [[tool.importlinter.contracts]]
  name = "CLI and web never import each other"
  type = "forbidden"
  source_modules = ["py_launch_blueprint.interfaces.cli"]
  forbidden_modules = ["py_launch_blueprint.interfaces.web"]
  # …and the symmetric contract.

  [[tool.importlinter.contracts]]
  name = "Composition root is imported only by the front-ends"
  type = "forbidden"
  source_modules = [
    "py_launch_blueprint.projects.domain",
    "py_launch_blueprint.projects.application",
    "py_launch_blueprint.projects.adapters",
  ]
  forbidden_modules = ["py_launch_blueprint.composition"]
  ```

  Run via `uv run lint-imports` (locked dev group, per WL-001), wired into
  `just check` and the pre-push hook alongside the existing gates.

- **HEX-31 — `tach` owns context isolation and the public interface.** Its
  `independence` semantics keep bounded contexts from importing each other
  (they must go via `shared/`), and — the capability `import-linter` lacks —
  its **strict interface** makes a context's internals *private by default*:
  even a front-end that is allowed to depend on `projects` may only touch the
  declared public surface (`ProjectsService`, `Project`), never reach in to
  `projects.adapters.py_api.PyApiProjectsRepository`. This fails *closed*
  (new internal modules are private automatically), where an `import-linter`
  `forbidden` blacklist fails *open* (you must enumerate each internal). It is
  wired now (`tach.toml`, baselined with `tach sync`, run in `just check`);
  with one context today it mostly restates the cli/web/core boundaries
  import-linter already guards, and earns its keep — independence + strict
  interfaces — at the second context.

- **HEX-32 — `ruff` TID251 is the fast, coarse framework guard.** A
  `banned-api` rule catches framework-bleed at pre-commit speed. Because
  ruff's `banned-api` is global, it is scoped to the layer via a nested
  `src/py_launch_blueprint/core/ruff.toml` that bans `click`/`fastapi`/
  `uvicorn` under `core/` (`requests` stays allowed — the HTTP adapter needs
  it). The authoritative, graph-wide framework-bleed rule remains the
  `import-linter` contract; ruff is the cheap first line, not the system of
  record.

- **HEX-33 — `ty` proves the seam.** Structural typing means an adapter
  satisfies a port without inheritance; `ty`/pyright verifies that
  `PyApiProjectsRepository` actually implements every `ProjectsRepository`
  method with compatible signatures. This is correctness of the *contract*,
  orthogonal to import *direction*; both are required. Already in `just check`
  (`uv run --extra web ty check`).

- **HEX-34 — `__all__` documents, it does not enforce.** Declare each
  context's public surface in its package `__init__.py` for IDE/autocomplete
  and as the source `tach`'s strict interface reads. It is a convention, not a
  guard — the guards are HEX-30/31.

- **HEX-35 — enforcement gotchas.** Exclude `tests/` and `init/` from the
  boundary rules (tests legitimately reach into internals). `TYPE_CHECKING`
  imports that cross a layer are a *design smell*, not a rule to silence —
  define a `Protocol` in `application/ports.py` and depend on that instead.
  Dynamic imports (the CLI's command-group registration) are invisible to
  every static tool; cover those by review.

## Testing strategy

- **HEX-40 — the test pyramid mirrors the rings; fakes, not mocks.** Logic is
  tested against an in-memory adapter at the port, never by patching
  `requests`. If a business-logic test needs to mock HTTP, logic has leaked
  out of the application ring.

  1. **Domain** — pure, zero mocks (`Project` invariants).
  2. **Application** (most coverage) — inject `InMemoryProjectsRepository`;
     no network. Asserts orchestration, the not-found policy, workspace
     resolution.
  3. **Port contract** — one parametrised suite run against *both* the fake
     and the real adapter to guarantee substitutability; the real variant
     carries the `live` marker (default-excluded per ITM-046).
  4. **Adapter** — `PyApiProjectsRepository` against mocked HTTP
     (`responses`/`respx`): URL building, auth header, error extraction,
     `_to_project` mapping.
  5. **Driving adapter** — CLI via Click's `CliRunner` with a fake use-case
     (rendering + exit codes); web via `TestClient` + `dependency_overrides`
     (problem+json + status). Thin, because logic is covered at ring 2.
  6. **E2E/smoke** — a handful behind `slow`/`live`.

- **HEX-41 — `InMemoryProjectsRepository` ships in the package**, in
  `projects/adapters/in_memory.py`, not in `tests/` — it is a first-class
  adapter (useful for demos/dev too) and is what makes ring-2 tests trivial.

- **HEX-42 — the `tests/` tree mirrors the source tree** (`tests/projects/
  domain`, `…/application`, `…/adapters`, `tests/interfaces/cli`, …) so a
  failing test points at its ring.

## Migration plan

Each step ships independently and leaves `just check` green.

1. **Extract port + adapter (highest value).** Split today's
   `ProjectsService` into `ProjectsRepository` (Protocol) +
   `PyApiProjectsRepository` (transport) + a thin `ProjectsService`
   (use-cases). Add `composition.build_projects_service`. CLI/web change one
   line each. This alone unlocks ring-2 testing.
2. **Add `InMemoryProjectsRepository`; convert service tests** to inject it;
   delete the `requests` mocking from logic tests.
3. **Move view models** (`ProjectList`/`CLIResult`) to
   `interfaces/cli/view_models.py`, updating CLI imports in the same commit so
   the build never breaks.
4. **Wire enforcement.** Add `import-linter` (HEX-30) to the dev group,
   `just check`, and the pre-push hook; add `tach` (HEX-31) to `just check`;
   add the `ruff` TID251 guard for `core/` (HEX-32). *(Done.)*
5. **Reshape to feature-first** (HEX-02) *when the second capability arrives* —
   not before. (`tach` is already wired per step 4; the reshape is what unlocks
   its per-context independence + strict-interface value.)

Still open after this PR (documented, deliberately deferred): **moving the view
models to the CLI** (HEX-15) — blocked on decoupling the result-model-as-output
contract that `core/diagnostics` produces and the web returns (WEB-03); and the
**feature-first reshape** (step 5).

## Consequences

- **Cost.** Ports, a composition root, and extra files are genuine overhead.
  For the current two endpoints and one real capability this is *more*
  structure than strictly needed; it pays off at ~3+ capabilities, a second
  backend, or multiple contributors. We accept it deliberately to set the
  growth pattern, and we front-load only step 1 (which is worth doing
  regardless, because it is what makes the test pyramid possible).
- **Reversibility.** The enforcement tools are thin, dev-only checks;
  `import-linter` and `tach` read the same import graph, so swapping or
  dropping one is a few lines of config.
- **For generated projects.** This structure and its enforcement are part of
  the template's opinion; forks inherit it. Keep `AGENTS.md`'s command
  surface in step with the tools added here.

## References

- Interface-pattern research (shared-core vs CLI-over-API vs hexagonal) and
  the boundary-enforcement tool comparison (`import-linter` vs `tach`) that
  motivated this doc.
- `0002-web-api-conventions.md` — the `PyError → HTTP status` table this doc
  reuses for web-side error translation (HEX-14).
- `0003-logging-conventions.md` — the one-pipeline logging shared by all
  front-ends.
