# 0017. Hexagonal core with mechanical boundary enforcement

- **Status:** Accepted
- **Date:** 2026-06-14
- **Deciders:** Steve Morin (maintainer)
- **Related:** design
  [`0005`](../design/0005-hexagonal-architecture-and-enforcement.md)
  (spec + `HEX-xx` rules); PR #433 (implementation);
  ADR [0015](0015-one-logging-pipeline-two-profiles.md) (CLI-vs-web split)

## Context

The package serves one core from multiple front-ends — the Click CLI today,
the FastAPI service behind the `web` extra, and more later. Before this
decision the business logic already lived in `core/` (good), but
`ProjectsService` was simultaneously the use-case **and** the HTTP client, and
nothing prevented the CLI and web layers — or a future contributor — from
importing across boundaries or binding directly to infrastructure. The instinct
was right; the boundaries were neither explicit nor enforced.

Three common patterns exist for a core driven by several interfaces: a shared
in-process library, a CLI that is a thin client of the web API, and the
formalized ports-and-adapters variant of the first. The trade-offs are surveyed
in design 0005.

## Decision

We will structure the core as **ports & adapters (hexagonal)** — a shared
in-process library with dependency inversion at every I/O seam — and **enforce
the boundaries mechanically** rather than by convention:

- Business logic depends on abstract **ports** (`typing.Protocol`); concrete
  **adapters** (HTTP, in-memory) implement them; a **composition root** wires
  them; the CLI and web layers are driving adapters that translate to/from
  their transport.
- Dependencies point inward only; the CLI and web layers never import each
  other; framework imports (`fastapi`/`click`/`uvicorn`) stay out of `core/`.
- Enforcement: **`import-linter`** is the authoritative graph-wide check
  (layering, front-end independence, composition-root isolation,
  framework-bleed) at `just check` + pre-push; **`tach`** guards
  bounded-context isolation; **`ruff` TID251** is a fast pre-commit
  framework-bleed guard scoped to `core/`; **`ty`** verifies adapters satisfy
  the ports.
- We do **not** adopt the CLI-over-HTTP pattern: the CLI talks to the core
  in-process, because nothing here is a remote, multi-tenant deployment.

Each rule carries a `HEX-xx` id; the full specification and the staged
migration plan live in design 0005.

## Consequences

- **Easier:** swapping a real adapter for an in-memory fake makes business
  logic testable without mocking `requests` (the test pyramid, HEX-40); adding
  a third front-end is a thin adapter; boundary violations fail CI instead of
  rotting silently.
- **Harder / cost:** more indirection (ports, a composition root, more files)
  than a two-endpoint tool strictly needs, and two extra dev-group tools
  (`import-linter`, `tach`) to keep current. Accepted deliberately to set the
  growth pattern.
- **Follow-on work (deferred, tracked in 0005):** moving the CLI view models
  out of `core/` (HEX-15) is blocked on decoupling the result-model-as-output
  contract that `core/diagnostics` produces and the web returns; the
  feature-first directory reshape (HEX-02 / migration step 5) waits for a
  second bounded context.
- The new dev tools follow the existing `uv run` dev-group pattern (per ADR
  0005's lean toolchain) — they are **not** added to `mise`/`flox`.

## Alternatives considered

- **Shared in-process library without formal ports** — the status quo.
  Rejected: the use-case/transport fusion blocked fakes-not-mocks testing and
  nothing prevented boundary erosion.
- **CLI as a thin client of the web API (CLI-over-HTTP)** — rejected: it adds a
  network boundary, serialization, and a running-server dependency that only
  pay off when the CLI manages a remote service, which is not the case here.
- **Enforce by convention / code review only** — rejected: conventions decay;
  mechanical enforcement was the whole point.
- **A single enforcement tool** — `import-linter` alone cannot express strict
  public-interface (deny-internals-by-default) isolation for bounded contexts,
  and `ruff` alone cannot express cross-module layer rules; the layered tools
  are complementary (design 0005, HEX-30..35).
