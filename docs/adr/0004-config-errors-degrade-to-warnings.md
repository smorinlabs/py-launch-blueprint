# 0004. Invalid config values degrade to warnings, never crashes

- **Status:** Accepted
- **Date:** 2026-06-10
- **Deciders:** maintainer (via code-review batch), implemented post-review in PR #378/#379
- **Related:** [design 0001](../design/0001-plbp-cli-conventions.md) §6–§7

## Context

Config loading runs eagerly on every invocation (output format, color, and
log levels resolve from it). A review found that one invalid value in any
layer made **every** command crash with a raw validation traceback —
including `config set`, the tool needed to repair the file. Conversely,
silently ignoring problems (the other failure found: an explicit `--config`
with broken TOML read as empty) hides user errors.

## Decision

Tiered strictness:

1. **Invalid values** (right TOML, wrong value) → drop the key, keep valid
   siblings, emit a warning on stderr; the command proceeds on defaults.
2. **Unparsable discovered layers** (system/user/project) → skip the layer
   with a warning.
3. **Unparsable explicit `--config` file** → loud `ConfigError` (the user
   named it; nothing else will supply what they wrote). Missing explicit
   files stay tolerated — they are valid `config set` targets.
4. **Writes refuse corrupt files** — `config set` never rewrites a file it
   cannot parse (that would destroy the user's other settings).
5. Errors raised while building the invocation context render through a
   fallback renderer with `ExitCode.CONFIG` — never a traceback.

## Consequences

- The CLI is always able to inspect and repair its own configuration.
- `Config.warnings` is part of the loader's contract; front-ends must
  surface it.
- Hard failures are reserved for explicit user input and destructive writes.

## Alternatives considered

- **Strict everywhere (raise on any invalid value)** — rejected: bricks the
  repair path; a stray project-local file in cwd could disable the CLI.
- **Tolerant everywhere** — rejected: silently ignoring an explicitly named
  config file or rewriting a corrupt one loses user data/trust.
