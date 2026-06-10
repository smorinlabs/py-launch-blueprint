# Design / requirements specs

Normative documents that specify **what to build and how it must behave** —
feature proposals, conventions, and requirements — before or while implementing.

## Conventions

- **Filename:** `NNNN-kebab-title.md` (zero-padded, sequential).
- **Status header** at the top of each doc: `Status`, `Type`, `Created`, and
  what it `Applies to`.
- **Status lifecycle:** `Draft` → `Proposed` → `Accepted` →
  (`Implemented` | `Superseded` | `Withdrawn`).
- A design doc may **spawn ADRs** for its load-bearing decisions, and may cite
  **research** docs that motivated it. Cross-link them.

## Index

| Doc | Title | Status |
|-----|-------|--------|
| [0001](0001-plbp-cli-conventions.md) | `plbp` CLI conventions — output, color, config (TOML), logging | Proposed |
