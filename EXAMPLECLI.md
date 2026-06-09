## Features

- 🔍 Fuzzy search for project names
- 🏢 Filter by workspace
- 📋 Multiple output formats (text, JSON, CSV)
- 📎 Clipboard integration
- 🎨 Rich terminal UI with color support
- 🔐 Secure token handling
- ⚡ Fast and efficient pagination

## Installation

### From PyPI

```bash
pip install py-launch-blueprint
```

### From Source

```bash
git clone https://github.com/smorinlabs/py-launch-blueprint.git
cd py-launch-blueprint
pip install -e ".[dev]"  # Install with development dependencies
```

### Direct Usage

You can also run the script directly:

```bash
python projects.py --help
```

## Configuration

The tool supports multiple ways to provide your Py Personal Access Token (PAT), in order of precedence:

1. Command-line argument: `--token`
2. Environment variable: `PY_TOKEN`
3. Configuration file: `~/.config/py-launch-blueprint/.env`

### Setting Up Configuration File

1. Create the config directory:
```bash
mkdir -p ~/.config/py-launch-blueprint
```

2. Create `.env` file:
```bash
echo "PY_TOKEN=your_token_here" > ~/.config/py-launch-blueprint/.env
```

3. Set proper permissions:
```bash
chmod 600 ~/.config/py-launch-blueprint/.env
```

## Usage

### Basic Usage

```bash
# Search for projects
py-projects

# Filter by workspace
py-projects --workspace "My Workspace"

# Limit results
py-projects --limit 50
```

### Output Formats

```bash
# JSON output
py-projects --format json

# CSV output
py-projects --format csv

# Copy to clipboard
py-projects --copy

# Save to file
py-projects --output projects.txt
```

### Additional Options

```bash
# Show verbose output
py-projects --verbose

# Disable colors
py-projects --no-color

# Show help
py-projects --help

# Show version
py-projects --version
```

## Error Codes

- 0: Successful execution
- 1: Configuration error
- 2: Authentication error
- 3: API error
- 4: Input/Output error
- 5: User interrupt

---

# `plbp` — noun-verb CLI (new)

`plbp` is the gh-style entry point for this project. Commands follow a
`plbp <noun> <verb>` shape and share one set of global flags, one output
contract, and structured logging out of the box. The legacy `py-projects`
command above is preserved for back-compat.

## Architecture

The package is split into three layers under `src/py_launch_blueprint/`:

| Layer | Path | Role |
|-------|------|------|
| Library (`core`) | `core/` | Pure logic + Pydantic models. No printing. Reused by every front-end. |
| CLI (`cli`) | `cli/` | Thin presentation: formats `core` results. One module per noun in `cli/commands/`. |
| Web (`web`) | `web/` | Reserved stub for a future FastAPI service (behind the `web` extra). |

The result of every command is a Pydantic model in `core/models.py` — that
model *is* the JSON representation, and the renderer turns the same object into
human text, JSON, or Markdown.

## Global flags (on every command)

| Flag | Purpose |
|------|---------|
| `-o, --output [text\|json\|markdown]` | output format (default `text`) |
| `--json` | shorthand for `--output json` |
| `-v, --verbose` | increase log verbosity (`-vv` for debug) |
| `-q, --quiet` | suppress non-essential stderr |
| `--no-color` | disable ANSI color |
| `--config PATH` | path to a TOML config file (overrides discovery; env `PLBP_CONFIG`) |
| `--token TEXT` | Py token (overrides `$PLBP_TOKEN`; never stored on disk) |
| `--no-input` | never prompt; fail instead (scripts/CI) |
| `-V, --version` | version + Python + platform (root) |
| `-h, --help` | help at every level |

## Output contract

- **Results** → stdout (pipe-safe). **Logs, messages, errors** → stderr.
- In `--json` mode, stdout is clean parseable JSON; errors become a structured
  `{"error": {"code", "name", "message"}}` object on stderr.

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

## Structured logging

Logging uses [`structlog`](https://www.structlog.org/): human-friendly colored
output on a TTY, one-JSON-object-per-line when piped or in CI. All logs go to
stderr. Configure verbosity with `-v`/`-vv`/`-q`.
