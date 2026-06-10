# `plbp` CLI Conventions — Requirements

- **Status:** Implemented (PRs #378–#380; naming per [ADR 0001](../adr/0001-app-short-name-plbp.md))
- **Type:** Design / requirements spec
- **Created:** 2026-06-09
- **Applies to:** the py-launch-blueprint CLI (`plbp`)

> **Deviations from this spec, all deliberate:**
> 1. **R3.2** — a third output format, `markdown`, is kept in addition to
>    `text`/`json` ([ADR 0003](../adr/0003-keep-markdown-output-mode.md)).
> 2. **R6/R7 strictness** — invalid config *values* degrade to warnings
>    rather than errors so the CLI can always repair its own config; an
>    unparsable explicit `--config` file is a hard error
>    ([ADR 0004](../adr/0004-config-errors-degrade-to-warnings.md)).
> 3. Secrets policy implemented per **R8** ([ADR 0002](../adr/0002-no-secrets-in-config-file.md)).

Scope: output, color, configuration (TOML), and logging conventions for the
`py-launch-blueprint` CLI. App short name: **`plbp`**. Environment variable
prefix: **`PLBP`**.

---

## 0. Terminology

- **App name (namespace):** `plbp`
- **Env prefix:** `PLBP` (every flag also resolves from `PLBP_*`)
- **Config home:** `$XDG_CONFIG_HOME`, default `~/.config`
- **State home:** `$XDG_STATE_HOME`, default `~/.local/state`

---

## 1. Framework & wiring

- **R1.1** Built on Click (Typer acceptable; it is Click underneath).
- **R1.2** Click is configured with `auto_envvar_prefix="PLBP"` so every flag
  automatically resolves from a `PLBP_*` environment variable. Env wiring is
  not hand-maintained.

## 2. Streams

- **R2.1** Program **data** is written to **stdout** only.
- **R2.2** All **logs, diagnostics, and human messaging** are written to
  **stderr** only.
- **R2.3** The two streams are never mixed, so `plbp ... | jq` and similar
  pipelines are always safe.

## 3. Output format

- **R3.1** `--output` / `-o` selects the **format**, not a destination.
- **R3.2** Allowed values: `text` (default) and `json`.
- **R3.3** Format **never** auto-switches based on TTY detection. A piped
  invocation produces the same format as an interactive one unless `--output`
  is given explicitly.
- **R3.4** Default format is `text`.

## 4. Output file

- **R4.1** `--output-file PATH` writes program output to a file instead of
  stdout. (Short form `-O` may be added; reserved, not required.)
- **R4.2** `--output-file` is independent of `--output`: format is chosen by
  `--output`, destination by `--output-file`.
- **R4.3** Shell redirection (`plbp ... > file`) remains fully supported; the
  flag and redirection are both valid and the user chooses.

## 5. Color

- **R5.1** Color auto-detects: enabled when stdout is a TTY, disabled
  otherwise.
- **R5.2** The universal `NO_COLOR` environment variable is honored (any
  non-empty value disables color).
- **R5.3** `--no-color` flag forces color off and overrides auto-detection.
- **R5.4** Config key `color` accepts `auto` (default), `always`, `never`.
- **R5.5** Precedence for color: `--no-color` flag > `NO_COLOR` env > config
  `color` > auto-detect.

## 6. Configuration file (TOML)

- **R6.1** Config format is **TOML**, read with stdlib `tomllib` (Python 3.11+);
  `tomli` is the fallback for older interpreters. `tomlkit` only if
  comment-preserving writes are needed.
- **R6.2** Config file path: `$XDG_CONFIG_HOME/plbp/plbp_config.toml`
  (default `~/.config/plbp/plbp_config.toml`). `$XDG_CONFIG_HOME` is honored
  when set (not hardcoded to `~/.config`).
- **R6.3** Optional layered discovery, each layer overriding the previous:
  1. system: `$XDG_CONFIG_DIRS/plbp/plbp_config.toml`
  2. user: `$XDG_CONFIG_HOME/plbp/plbp_config.toml`
  3. project-local: `./plbp_config.toml` (or `./.plbp_config.toml`)
- **R6.4** `--config PATH` (env `PLBP_CONFIG`) overrides discovery entirely.
- **R6.5** Config is organized into tables by concern: `[output]`, `[logging]`.
  Keys are `snake_case`.

## 7. Precedence (global)

- **R7.1** Every configurable behavior resolves in this fixed order, highest
  wins:

  **CLI flag → environment variable → project config → user config →
  system config → built-in default**

## 8. Secrets

- **R8.1** Secrets (e.g. tokens) are **never** stored in the TOML config file.
- **R8.2** The token is supplied via `--token` flag or the `PLBP_TOKEN`
  environment variable only.

## 9. Logging — defaults

- **R9.1** The logging subsystem is always configured; what varies is level and
  sinks.
- **R9.2** The **console (stderr) sink is on by default** at level `WARNING`.
- **R9.3** The **file sink is off by default**.

## 10. Logging — verbosity controls

- **R10.1** `-v` raises the console level to `INFO`.
- **R10.2** `-vv` raises the console level to `DEBUG`.
- **R10.3** `-q` / `--quiet` lowers the console level to `ERROR`.
- **R10.4** `--log-level {debug,info,warning,error,critical}` (env
  `PLBP_LOG_LEVEL`) is an explicit override of the console level.
- **R10.5** Verbosity flags affect the **console** sink only; the file sink
  level is controlled independently (R11.4).

## 11. Logging — file sink

- **R11.1** The file sink is enabled by `--log-file [PATH]` (env
  `PLBP_LOG_FILE`) or by setting `logging.file` in config.
- **R11.2** When enabled without an explicit path, the default location is
  `$XDG_STATE_HOME/plbp/plbp.log` (default `~/.local/state/plbp/plbp.log`).
  Logs are treated as **state**, not config or data.
- **R11.3** The file sink uses rotation (`RotatingFileHandler`,
  default 10 MB × 5 backups).
- **R11.4** The file sink has its own level (`logging.file_level`, env
  `PLBP_LOG_FILE` companion / config), defaulting to `DEBUG`, independent of
  the console level.
- **R11.5** File sink format is controlled by `logging.format` (env
  `PLBP_LOG_FORMAT`): `json` (JSONL, recommended for the file) or `text`.
- **R11.6** Dual-sink behavior: when both sinks are active they attach to the
  same logger; the logger floor is set to the most verbose sink, and each
  handler filters independently — e.g. console at `WARNING`, file at `DEBUG`.

## 12. Environment variables

- **R12.1** All env vars are prefixed `PLBP_`. The full set:

| Variable          | Controls                                   | Equivalent flag        |
|-------------------|--------------------------------------------|------------------------|
| `PLBP_CONFIG`     | Path to config file (overrides discovery)  | `--config`             |
| `PLBP_OUTPUT`     | Output format (`text` \| `json`)           | `--output` / `-o`      |
| `PLBP_COLOR`      | Color mode (`auto`\|`always`\|`never`)     | `--no-color`           |
| `PLBP_LOG_LEVEL`  | Console log level                          | `--log-level`/`-v`/`-q`|
| `PLBP_LOG_FILE`   | Log file path (presence enables file sink) | `--log-file`           |
| `PLBP_LOG_FORMAT` | File sink format (`text` \| `json`)        | (config only)          |
| `PLBP_TOKEN`      | Auth token (secret)                        | `--token`              |

- **R12.2** The universal `NO_COLOR` is also honored (R5.2).
- **R12.3** `XDG_CONFIG_HOME` and `XDG_STATE_HOME` are honored for config and
  log-file locations respectively.

---

## Appendix A — Example `plbp_config.toml`

```toml
# $XDG_CONFIG_HOME/plbp/plbp_config.toml

[output]
format = "text"        # text | json        (PLBP_OUTPUT)
color  = "auto"        # auto | always | never

[logging]
level      = "warning" # console level       (PLBP_LOG_LEVEL)
file       = ""        # empty = off; path enables file sink (PLBP_LOG_FILE)
file_level = "debug"   # file sink level, independent of console
format     = "text"    # text | json (JSONL) for the file sink (PLBP_LOG_FORMAT)
```

Note: no `[auth]`/token in this file — the token is env/flag only (R8).

## Appendix B — Flag summary

| Flag                  | Meaning                                  | Default   |
|-----------------------|------------------------------------------|-----------|
| `--output` / `-o`     | Output format: `text` \| `json`          | `text`    |
| `--output-file PATH`  | Write output to a file instead of stdout | (stdout)  |
| `--no-color`          | Force color off                          | (auto)    |
| `--config PATH`       | Config file override                     | (XDG)     |
| `-v`                  | Console level → INFO                     | —         |
| `-vv`                 | Console level → DEBUG                     | —         |
| `-q` / `--quiet`      | Console level → ERROR                     | —         |
| `--log-level LEVEL`   | Explicit console level                   | `warning` |
| `--log-file [PATH]`   | Enable file sink (default XDG state path) | (off)     |
| `--token TOKEN`       | Auth token (secret)                      | (env)     |

## Appendix C — Defaults at a glance

| Concern        | Default                                             |
|----------------|-----------------------------------------------------|
| Output format  | `text`                                              |
| Output dest    | stdout                                              |
| Color          | auto (TTY-detected), `NO_COLOR` honored             |
| Config file    | `$XDG_CONFIG_HOME/plbp/plbp_config.toml`            |
| Console logging| on, `WARNING`, to stderr                            |
| File logging   | off                                                 |
| File log path  | `$XDG_STATE_HOME/plbp/plbp.log` (when enabled)      |
| File log format| JSONL recommended                                   |
| Precedence     | flag → env → project → user → system → default      |

## Appendix D — Migration notes for `py-launch-blueprint`

1. Replace `.env` config with TOML; honor `$XDG_CONFIG_HOME` instead of
   hardcoding `~/.config`.
2. Rename the format flag usage so `--output`/`-o` is the format and
   `--output-file` is the destination (current code uses `--format` for type
   and `--output` for a file path — resolve before it spreads across tools).
3. Add a real `logging` setup (currently none): console sink at `WARNING`,
   opt-in rotating file sink under `$XDG_STATE_HOME`, dual-sink with
   independent levels.
4. Keep the existing stdout/stderr separation (`error_console` on stderr) — it
   already satisfies R2.
5. Keep the token in an env var (current `PY_TOKEN` → `PLBP_TOKEN`).
