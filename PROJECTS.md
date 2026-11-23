# Projects

Index of every project in this repo. Per-project files live in
`projects/`. Skills in the `project-harness` plugin operate on this
file plus those.

Route every project-state change through a project-harness skill
(`project-add`, `project-refine`, `project-audit`) rather than editing this
file by hand — see Conventions.

## Status legend

| Glyph | Meaning                | Reach for…                    |
|-------|------------------------|-------------------------------|
| `[?]` | Idea                   | `project-refine` to scope     |
| `[ ]` | Scoped, not started    | start work; flip to `[~]`     |
| `[~]` | In progress            | continue; check next task     |
| `[x]` | Completed              | leave alone                   |
| `[-]` | Decided not to do      | leave alone                   |
| `[>]` | Proceeded to successor | follow the redirect           |

## Conventions

- Filename: `projects/P<NN>-<kebab-slug>.md` for scoped/active/done;
  `projects/P<NN>-<roughName>-.md` (trailing hyphen) for ideas.
- Trunk row: `- [<glyph>] **P<NN>** — [<title>](projects/<filename>)`.
  The title is a standard markdown link to the per-project file —
  external tools (markdown linters, doc generators, AI agents
  reading the repo without project-harness loaded) can parse the
  schema without prior knowledge of the conventions.
- Every non-`[?]` per-project file has a `**References**` block at
  the top whose first bullet is `- **Trunk:** [PROJECTS.md](../PROJECTS.md)`,
  the back-pointer to this file. Bidirectional schema.
- One trunk row per file; one file per trunk row.
- Status glyph mirrors the rolled-up state of the per-project file.
- Flip task checkboxes immediately as each task lands (no batching).
- TDD bias: every project has at least one `TS` task before its first
  `T` task. Opt out with `**TDD: not applicable**` in the body.

Planning system: **Superpowers** — specs/plans live under
`docs/superpowers/specs/`. Per-project `**References**` blocks point there.

### Project workflow skills (plugin: project-harness)

- `using-project-harness` — bootstrap: when to use which skill below
- `project-next` — orient: what's in progress, what's next, what's recently touched
- `project-add` — capture an idea (≤4 questions, reserves the ID with a commit)
- `project-refine` — flesh out / scope / decompose an existing project
- `project-audit` — verify state matches conventions; fix per finding

## Project index

<!-- One row per project. Scoped / in-progress / done first; ideas last. -->
- [x] **P01** — [Init app-name rebrand robustness](projects/P01-init-rebrand-robustness.md) — per-field drift coverage (B) + derive non-contract internals (C)
- [x] **P02** — [Repo simplification & organization (SIMP series)](projects/P02-repo-simplification.md) — single-purpose PRs to simplify/consolidate Justfile, docs, setup, tests, workflows, agent configs
- [~] **P03** — [Type Precision Uplevel](projects/P03-type-precision-uplevel.md) — eliminate leaking/overly-general types + verified ty rule promotions + scoped ruff ANN, from a Fable×Codex two-lens audit
- [x] **P04** — [Py-API Boundary Validation](projects/P04-py-api-boundary-validation.md) — validate Py-API responses at the edge with Pydantic; silent drift → APIError
- [x] **P05** — [Template-press v3.4 dogfood & conform](projects/P05-template-press-v34-dogfood-conform.md) — press/ config from scratch, verify to declarations-only green, rebrand + publish an instance; findings → Run 4 PROBLEM-NN
- [x] **P06** — [Full conform — retire the embedded engine](projects/P06-full-conform.md) — delete init/, CI cutover to press verify, v3.6.0 config upgrade ([[remove]], verify_exempt, scan=boundary); closes #423
- [x] **P07** — [Template Press upgrade and Python 3.13 bootstrap](projects/P07-press-upgrade-and-python-313.md) — adopt the released press and prove a usable generated project
- [x] **P08** — [Audit-triage contributor model](projects/P08-audit-triage-contributor-model.md) — move the triage bot to the muse-github-setup default `muse-spark-1.3-contributor`
- [x] **P10** — [OTel extra CI coverage](projects/P10-otel-extra-ci-coverage.md) — tracing tests + a `test-otel` CI job so `opentelemetry-*` bumps are exercised at PR time (sweep ISS-001)
- [x] **P11** — [Parallel `just check` gate](projects/P11-parallel-check-gate.md) — run the gate's recipes in parallel and split the bun release tests; spec Phase A (R1–R3)
- [~] **P12** — [Slim PR CI job count](projects/P12-slim-pr-ci-jobs.md) — fewer billed jobs per PR: release-please fast path, path-gated `release-generation`, merged static jobs, PR-only concurrency; required checks unchanged
- [?] **P09** — [Enroll in Anthropic OSS Scanner](projects/P09-enroll-anthropic-oss-scanner-.md) — Add SECURITY.md, scanner Dockerfile, and threat model; open the enrollment PR
