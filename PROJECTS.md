# PROJECTS.md

Project trunk. One row per project below; detailed scope, tasks, and
references live in per-project files under `projects/`.

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

## Projects

| ID  | St    | Project                                                                 |
|-----|-------|------------------------------------------------------------------------|
| P01 | `[x]` | [Init app-name rebrand robustness](projects/P01-init-rebrand-robustness.md) — per-field drift coverage (B) + derive non-contract internals (C) |
| P02 | `[x]` | [Repo simplification & organization (SIMP series)](projects/P02-repo-simplification.md) — single-purpose PRs to simplify/consolidate Justfile, docs, setup, tests, workflows, agent configs |

## Conventions

Planning system: **Superpowers** — specs/plans live under
`docs/superpowers/specs/`. Per-project `**References**` blocks point there.

### Project workflow skills (plugin: project-harness)

- `using-project-harness` — bootstrap: when to use which skill below
- `project-next` — orient: what's in progress, what's next, what's recently touched
- `project-add` — capture an idea (≤3 questions, reserves the ID with a commit)
- `project-refine` — flesh out / scope / decompose an existing project
- `project-audit` — verify state matches conventions; fix per finding
