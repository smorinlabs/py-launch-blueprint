# `plbp` — noun-verb CLI

`plbp` is the gh-style entry point for this project. Commands follow a
`plbp <noun> <verb>` shape and share one set of global flags, one output
contract, and structured logging out of the box.

## Architecture

The package is split into three layers under `src/py_launch_blueprint/`:

| Layer | Path | Role |
|-------|------|------|
| Library (`core`) | `core/` | Pure logic + Pydantic models. No printing. Reused by every front-end. |
| CLI (`cli`) | `cli/` | Thin presentation: formats `core` results. One module per noun in `cli/commands/`. |
| Web (`web`) | `web/` | Thin adapter: serves `core` results as JSON (behind the `web` extra). See [EXAMPLEWEB.md](EXAMPLEWEB.md). |

The result of every command is a Pydantic model in `core/models.py` — that
model *is* the JSON representation, and the renderer turns the same object into
human text, JSON, or Markdown.

## Global flags (on every command)

| Flag | Purpose |
|------|---------|
| `-o, --output [text\|json\|markdown]` | output format (default `text`; env `PLBP_OUTPUT`; config `output.format`) |
| `--json` | shorthand for `--output json` |
| `--output-file PATH` | write results to a file instead of stdout (format still set by `--output`) |
| `-v, --verbose` | raise console log level (`-v` info, `-vv` debug) |
| `-q, --quiet` | lower console log level to error |
| `--log-level LEVEL` | explicit console level, overrides `-v`/`-q` (env `PLBP_LOG_LEVEL`) |
| `--log-file [PATH]` | enable rotating file logging; bare flag uses the XDG state path (env `PLBP_LOG_FILE`) |
| `--no-color` | force color off (`NO_COLOR` env and config `output.color` also honored) |
| `--config PATH` | path to a TOML config file (overrides discovery; env `PLBP_CONFIG`) |
| `--token TEXT` | Py token (overrides `$PLBP_TOKEN`; never stored on disk) |
| `--no-input` | never prompt; fail instead (scripts/CI) |
| `-V, --version` | version + Python + platform (root) |
| `-h, --help` | help at every level |

## Output contract

- **Results** → stdout (pipe-safe), or the `--output-file` path when given.
  **Logs, messages, errors** → stderr, always.
- In `--json` mode, stdout is clean parseable JSON; errors become a structured
  `{"error": {"code", "name", "message"}}` object on stderr.
- Format never auto-switches on TTY: piped output formats the same as
  interactive output unless `-o`/`PLBP_OUTPUT`/config says otherwise.
- Color: auto-detected from the TTY; `--no-color` > `NO_COLOR` env >
  `output.color` config (`auto`/`always`/`never`) > auto-detect.

## Usage

```bash
# Projects (noun) → list / get (verbs)
plbp projects list
plbp projects list --workspace "My Workspace" --json
plbp projects list -o markdown
plbp projects get 12345

# Config — set/get non-secret keys by dotted path (no network required)
plbp config path
plbp config get output.color
plbp config set logging.level info               # writes [logging] level
plbp config set output.color always --dry-run    # preview, write nothing
plbp config set logging.file_level debug --yes   # skip the overwrite prompt
# the token is NEVER stored in config — pass --token or set $PLBP_TOKEN
plbp config get token --json                     # masked; resolves from flag/env

# Diagnose setup (Python/platform, config file, token). Exits non-zero on errors.
plbp doctor
plbp doctor --json

# Shell completion
plbp completion bash >> ~/.bashrc
eval "$(plbp completion zsh)"
```

Mutating commands (e.g. `config set`) share a safety pattern: `--dry-run`
previews the change, an overwrite prompts for confirmation on stderr, and
`--yes` / `--no-input` make it non-interactive (the latter refuses rather than
prompting).

## Configuration file (TOML, XDG)

`plbp` reads a TOML config file from an XDG-compliant location, namespaced
under the app and named so its purpose is obvious:

```
~/.config/plbp/plbp_config.toml          # $XDG_CONFIG_HOME/plbp/plbp_config.toml
```

```toml
# plbp_config.toml — non-secret settings only, organized into tables
[output]
format = "text"   # text | json | markdown
color  = "auto"   # auto | always | never

[logging]
level = "warning" # console level
```

Config is discovered in layers, each overriding the previous: system
(`$XDG_CONFIG_DIRS`) → user (`$XDG_CONFIG_HOME`) → project
(`./plbp_config.toml`); `--config` overrides discovery entirely. Per-setting
precedence: flag → env (`PLBP_*`) → project → user → system → default.

Secrets are **never** stored here — the token resolves from `--token` or
`$PLBP_TOKEN` only. The same XDG convention applies to other file kinds
(resolved in `core/paths.py`): data → `$XDG_DATA_HOME/plbp/plbp_db.db`,
state/logs → `$XDG_STATE_HOME/plbp/plbp.log`, cache → `$XDG_CACHE_HOME/plbp/`.

## Structured logging (dual sink)

Logging uses [`structlog`](https://www.structlog.org/) rendered through stdlib
handlers, giving two independent sinks:

- **Console (stderr, always on)** — human-friendly colored output on a TTY,
  one-JSON-object-per-line when piped or in CI. Level: `WARNING` by default;
  `-v` info, `-vv` debug, `-q` error, `--log-level` explicit override
  (also `PLBP_LOG_LEVEL` / config `logging.level`).
- **Rotating file (off by default)** — enabled by `--log-file [PATH]`,
  `$PLBP_LOG_FILE`, or config `logging.file`. Bare `--log-file` writes to
  `$XDG_STATE_HOME/plbp/plbp.log` (logs are *state*, not config). Rotates at
  10 MB x 5 backups. Its level (`logging.file_level`, default `debug`) and
  format (`logging.format`: `text` or `json` JSONL; env `PLBP_LOG_FORMAT`)
  are independent of the console.

When both sinks are active they attach to the same logger: the logger floor is
the most verbose sink and each handler filters independently — e.g. a quiet
console at `warning` while the file captures full `debug` detail.

```bash
plbp doctor -vv                          # debug detail on stderr
plbp doctor --log-file                   # + JSONL/text file under XDG state
plbp doctor --log-file /tmp/run.log --log-level error   # quiet console, full file
plbp config set logging.file_level info --yes           # tune the file sink
```

Results on stdout are never mixed with logs — `plbp ... --json | jq` stays
safe at any verbosity.
