# 0017. Testing strategy & tooling (the second-round testing shortlist)

- **Status:** Accepted
- **Date:** 2026-06-14
- **Deciders:** Steve Morin
- **Related:** `docs/research/0002-dev-tooling-wishlist.md` (Category B — the
  deferred testing items this implements), `docs/design/0005-hexagonal-architecture-and-enforcement.md`
  (HEX-40 test pyramid / port-contract suite), WL-005 (Codecov gates), ADR-03 (ty)

## Context

The suite already had a solid base: a marker taxonomy (`live`/`slow`,
default-excluded), coverage with Codecov project/patch gates, CLI `--help`
golden snapshots, an OpenAPI contract snapshot plus schemathesis fuzzing
(WEB-50/51), a six-way OS×Python matrix, and a `tests/` tree that mirrors
source. What it lacked were the *resilience and depth* improvements catalogued
but deferred in the dev-tooling wishlist (Category B): nothing parallelised the
suite, nothing bounded a hung test, test order was fixed (so inter-test
coupling could hide), coverage counted lines but not branches, no property
tests guarded the serialization seams, no scheduled run caught upstream
dependency breakage, and the new hexagonal ports (#433) had no substitutability
guarantee between their fake and real adapters.

These are independently valuable, low-risk, and mostly cheap. This ADR records
adopting them as a batch so the template's testing posture is documented in one
place and inherited by forks.

## Decision

We will adopt the following testing improvements:

- **Parallel execution (WL-008, `pytest-xdist`).** Available via `-n auto`,
  used by the CI test matrix and the canary. Kept **opt-in per invocation**,
  *not* in default `addopts`, so the fast local inner loop keeps clean
  `-x`/pdb behaviour and worker startup never slows the small suite.
- **Per-test timeout (WL-009, `pytest-timeout`).** A 60s cap via the
  `thread` method (the POSIX-only signal default cannot interrupt on the
  Windows matrix leg); a genuinely slow test overrides with
  `@pytest.mark.timeout(N)`.
- **Randomized order (WL-010, `pytest-randomly`).** Each run reshuffles with a
  printed, replayable seed, surfacing hidden ordering dependencies while they
  are cheap to fix.
- **Branch coverage (`[tool.coverage.run] branch = true`).** The Codecov gate
  now also catches untested conditionals, not just unexecuted lines.
- **Property-based tests (WL-013, `hypothesis`).** Applied selectively at the
  serialization seams (`Project` JSON round-trip, config write→read), with a
  CI-robust profile (deadline disabled) registered in `tests/conftest.py`.
- **Port-contract substitutability suite (HEX-40, `responses`).** One
  parametrized suite runs the same behavioural assertions against *both* the
  in-memory fake and the real HTTP adapter (network mocked), guaranteeing the
  fake the ring-2 service tests depend on stays faithful.
- **Scheduled "canary" workflow (WL-012).** A weekly (+ dispatch) run of the
  full suite — `slow`/`live` included — against a **re-resolved** dependency
  graph (`uv sync --upgrade`, not `--locked`). Upstream breaking releases
  surface in a calm scheduled run, not inside an unrelated feature PR. It
  never gates a PR (schedule/dispatch only): a red canary is a signal.

## Consequences

- CI tests run faster (xdist across runner cores); a hung test fails loudly
  instead of consuming a slot; an order-coupled test is caught the first time
  randomization exposes it; the coverage gate is stricter (branches).
- The fake↔real adapter parity is now mechanically enforced, which is what
  lets the bulk of logic testing stay at the fast ring-2 layer (HEX-40).
- Dependency rot is monitored continuously rather than discovered by accident.
- Cost: five new dev-group tools (`pytest-xdist`, `pytest-timeout`,
  `pytest-randomly`, `hypothesis`, `responses`), all standard and locked in
  `uv.lock` (WL-001); one new always-green-or-signal workflow.
- For generated projects: this is part of the template's opinion; forks
  inherit the config, the property/contract test patterns, and the canary.
  Keep `AGENTS.md`'s command surface in step.

## Alternatives considered

- **`-n auto` in default `addopts`** — rejected: worker startup makes the
  current small/fast suite *slower* locally and muddies `-x`/pdb. Opt-in where
  the full (incl. slow/live) suite justifies it.
- **Mutation testing (mutmut/cosmic-ray)** — deferred: high noise-to-signal at
  this suite size; revisit if correctness regressions slip through.
- **Pin the canary to a fixed seed / lockfile** — defeats its purpose; the
  point is to test *un*-pinned latest deps.
- **A second type checker alongside ty** — out of scope; ty already proves the
  port seams (HEX-33).
