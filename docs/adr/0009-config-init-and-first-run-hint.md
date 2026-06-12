# 0009. Guided `config init` plus a marker-backed one-time first-run hint

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** maintainer (interactive + Copilot/CodeRabbit review), implemented in PR #400
- **Related:** `cli/commands/config.py`; `cli/context.py`; ADR 0002 (no secrets in config)

## Context

A fresh install had no on-ramp: users had to discover `config set` and the
dotted-key schema from docs. First-run hints are easy to get wrong — they
must never pollute scripted output, never repeat, and never be "consumed"
invisibly.

## Decision

Two pieces:

1. **`plbp config init`** walks the most common keys (`output.format`,
   `output.color`, `logging.level`) with prompts **on stderr**, offering
   currently resolved values as defaults (allowed values come from the
   settings schema via `allowed_values()`). `--yes` writes the defaults
   non-interactively, `--dry-run` previews, and bare `--no-input` refuses
   with a hint. Secrets remain excluded (ADR 0002).
2. A **one-time hint** points fresh installs at it. It fires only when it
   cannot pollute anything: interactive stderr, not `--quiet`, not
   `--no-input`, **not JSON mode**, and no config file found in any layer.
   Once-ever is enforced by a marker file in the XDG state dir — and the
   marker is written **only when the hint is actually shown**, so a first
   run under `--json` or a pipe does not silently burn it.

## Consequences

- Fresh installs get a guided path; scripts and CI never see the hint.
- The marker-only-when-shown rule (a review finding) means deleting the
  config later can re-trigger the hint once — acceptable, arguably correct.
- The hint suppresses itself while running `config init` (command-path
  check), a string-based check that must be revisited if the command is
  renamed or nested.

## Alternatives considered

- **Auto-create a config file on first run** — rejected: writing to the
  user's home without being asked violates least surprise; the schema's
  defaults already work with no file.
- **Show the hint until config exists (no marker)** — rejected: nagging on
  every invocation is the pattern users mute tools over.
