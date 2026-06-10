# 0002. Secrets are never stored in the config file

- **Status:** Accepted
- **Date:** 2026-06-09
- **Deciders:** maintainer (interactive), implemented in PR #378
- **Related:** [design 0001](../design/0001-plbp-cli-conventions.md) §8 (R8)

## Context

An early iteration of the CLI both read the auth token from the TOML config
file and offered `config set token <value>` to write it there. Spec R8 says
secrets live in the `--token` flag or `$PLBP_TOKEN` env var only: config
files get copied, committed, backed up, and shared in ways secret stores are
not, and a "convenient" token-in-file path normalizes leaking.

## Decision

The token resolves from `--token` then `$PLBP_TOKEN` — **never** from a
file; a `token` key found in config is silently ignored by the loader.
`config set`/`config get` operate only on the typed, non-secret settings
schema (`[output]`, `[logging]`), so a secret cannot even be named as a key.
The config file is still written `0600` as defense-in-depth, because users
put sensitive things in CLI config files out of habit.

## Consequences

- Removed a shipped feature (`config set token`) — a deliberate reversal.
- Setup docs must say "export PLBP_TOKEN" instead of "run config set".
- `doctor` reports token presence/source so the env-only path stays
  debuggable.

## Alternatives considered

- **Keep token-in-file as a convenience** — rejected: convenience here is
  the attack surface.
- **OS keyring integration** — out of scope for a template; the env-var
  contract composes with any secret manager.
