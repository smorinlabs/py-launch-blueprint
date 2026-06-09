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

# `pylb` — noun-verb CLI (new)

`pylb` is the gh-style entry point for this project. Commands follow a
`pylb <noun> <verb>` shape and share one set of global flags, one output
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
| `-o, --output [human\|json\|markdown]` | output format (default `human`) |
| `--json` | shorthand for `--output json` |
| `-v, --verbose` | increase log verbosity (`-vv` for debug) |
| `-q, --quiet` | suppress non-essential stderr |
| `--no-color` | disable ANSI color |
| `--config PATH` | path to a `.env` config file |
| `--token TEXT` | Py token (overrides env and config file) |
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
pylb projects list
pylb projects list --workspace "My Workspace" --json
pylb projects list -o markdown
pylb projects get 12345

# Config (no network required)
pylb config path
pylb config get token --json

# Shell completion
pylb completion bash >> ~/.bashrc
eval "$(pylb completion zsh)"
```

## Structured logging

Logging uses [`structlog`](https://www.structlog.org/): human-friendly colored
output on a TTY, one-JSON-object-per-line when piped or in CI. All logs go to
stderr. Configure verbosity with `-v`/`-vv`/`-q`.
