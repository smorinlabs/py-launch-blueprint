# Set project-wide variables
py_package_name := "py_launch_blueprint"
# Filesystem path to the package (src/ layout). Module name stays
# `py_package_name`; tooling that takes a *path* uses this.
py_package_path := "src/" + py_package_name
repo_name := "py-launch-blueprint"
app_name := "plbp"
contributors_owner := "smorinlabs"
contributors_package := "contributors-please@1"
args := " "

# Blueprint setup guard — Tier 1 (universal discovery warning).
# `just` evaluates top-level `:=` variables EAGERLY on every recipe run, so this
# fires on every recipe with zero per-recipe boilerplate. `guard.sh warn` prints
# to stderr and MUST exit 0 — a non-zero exit from a `shell()` call aborts `just`.
# `just --list` / `--summary` do not evaluate variables, so introspection stays silent.
_blueprint_notice := shell('bash init/guard.sh warn')

# Text colors
BLACK := '\033[30m'
RED := '\033[31m'
GREEN := '\033[32m'
YELLOW := '\033[33m'
BLUE := '\033[34m'
MAGENTA := '\033[35m'
CYAN := '\033[36m'
WHITE := '\033[37m'
GRAY := '\033[90m'

# Background colors
BG_BLACK := '\033[40m'
BG_RED := '\033[41m'
BG_GREEN := '\033[42m'
BG_YELLOW := '\033[43m'
BG_BLUE := '\033[44m'
BG_MAGENTA := '\033[45m'
BG_CYAN := '\033[46m'
BG_WHITE := '\033[47m'

# Text styles
BOLD := '\033[1m'
DIM := '\033[2m'
ITALIC := '\033[3m'
UNDERLINE := '\033[4m'

# Reset all styles
NC := '\033[0m'

# Display a symbol
# This should not use interpolation because it is a string literal
# The variables are not expanded when the string is created but when it is used
# VARIABLE_NAME + "TEXT" + VARIABLE_NAME should be written as CHECK := GREEN + "✓" + NC
CHECK := GREEN + "✓" + NC
CROSS := RED + "✗" + NC
DASH := GRAY + "-" + NC


CLIPBOARD_CMD := if os_family() == "windows" { "clip" } else if os() == "linux" { "xclip -selection clipboard" } else { "pbcopy" }
DATE_TIME := datetime("%Y-%m-%d-%H-%M")
BRANCH_NAME := "test-actions-" + DATE_TIME

# List all available recipes
[group('help')]
@default:
    just --list --unsorted

# ================================
# COMMANDS GROUPS
# ================================
# SETUP: Initial project setup and environment initialization
# INSTALL: Installing the project and its dependencies
# UPDATE: Updating dependencies, versions, and configurations
# DEV: Development workflow commands and utilities
# TEST: Test execution and test environment management
# BUILD: Building distributable packages and artifacts
# RUN: Executing the application in various modes
# DOCS: Documentation generation and management
# PRE-COMMIT: Linting, formatting, and code quality checks
# HELP: Usage instructions and command information
# UTILITIES: General utility and maintenance commands
# DEBUG: Debugging and troubleshooting tools
# RELEASES: Version management and publishing
# WORKFLOW: CI/CD pipelines and multi-step processes
# QUICK START: Essential commands for basic usage
# ================================

# Select a just recipe
[group('utilities'), group('help')]
@select-shell:
    @just --choose

# Check if required tools are installed
[group('setup'), group('debug')]
check-deps:
    #!/usr/bin/env sh
    if ! command -v uv >/dev/null 2>&1; then echo "{{YELLOW}}uv is not installed{{NC}}\n RUN {{BLUE}}make bootstrap{{NC}}"; exit 1; fi
    if ! command -v python3 >/dev/null 2>&1; then echo "{{YELLOW}}python3 is not installed{{NC}}"; exit 1; fi
    if ! command -v just >/dev/null 2>&1; then echo "{{YELLOW}}just is not installed{{NC}}\n RUN {{BLUE}}make bootstrap{{NC}}"; exit 1; fi
    if ! command -v lefthook >/dev/null 2>&1; then echo "{{YELLOW}}WARNING: lefthook is not installed{{NC}}\n RUN {{BLUE}}just setup{{NC}}"; fi
    if ! command -v taplo >/dev/null 2>&1; then echo "{{YELLOW}}Taplo is not installed{{NC}}\n RUN {{BLUE}}just install-taplo{{NC}}"; exit 1; fi
    if ! command -v yamlfmt >/dev/null 2>&1; then echo "{{YELLOW}}yamlfmt is not installed{{NC}}\n RUN {{BLUE}}just install-yamlfmt{{NC}}"; exit 1; fi
    echo "All required tools are installed"

alias c := check-deps

# One-command project setup — Level 2 of the two-level flow. Level 1 is
# `make bootstrap` (base toolchain: just + uv); run that first on a bare
# machine. Idempotent: safe to re-run in every fresh clone/container/session.
[group('setup'), group('quick start')]
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    # Bootstrap gate — catches `just setup` being run before `make bootstrap`.
    if command -v make >/dev/null 2>&1; then
        if ! make --no-print-directory check; then
            echo -e "{{RED}}Base toolchain incomplete — run {{BLUE}}make bootstrap{{RED}} first, then re-run {{BLUE}}just setup{{RED}}.{{NC}}" >&2
            exit 1
        fi
    elif command -v uv >/dev/null 2>&1; then
        echo -e "{{YELLOW}}make not found — skipping bootstrap check (uv is present, continuing).{{NC}}"
    else
        echo -e "{{RED}}uv not found (and make is unavailable to bootstrap it).{{NC}}" >&2
        echo -e "{{RED}}Run {{BLUE}}make bootstrap{{RED}} on a machine with make, or install uv: https://docs.astral.sh/uv/{{NC}}" >&2
        exit 1
    fi
    # Tools installed below land in these dirs; make them visible to the
    # rest of this run (the final check-deps) even on a fresh machine.
    export PATH="$HOME/.local/bin:$HOME/.bun/bin:${CARGO_HOME:-$HOME/.cargo}/bin:$PATH"
    echo -e "{{BLUE}}[1/4] Syncing dev environment: uv sync --group dev --extra web{{NC}}"
    uv sync --group dev --extra web
    echo -e "{{BLUE}}[2/4] Installing hook toolchain (bun, lefthook, gitleaks)...{{NC}}"
    scripts/install-bun.sh
    scripts/install-lefthook.sh
    scripts/install-gitleaks.sh
    bun install
    echo -e "{{BLUE}}[3/4] Installing formatters (taplo, yamlfmt)...{{NC}}"
    just install-taplo
    just install-yamlfmt
    echo -e "{{BLUE}}[4/4] Verifying...{{NC}}"
    just check-deps
    echo -e "{{GREEN}}✓ Setup complete.{{NC}} Try {{BLUE}}just check{{NC}} to run the full quality pipeline."
    echo -e "If a tool is missing in NEW shells, ensure ~/.local/bin, ~/.bun/bin and ~/.cargo/bin are on your PATH."

# Install package in editable mode with dev dependencies
[group('install'), group('quick start')]
@install-dev: check-deps
    uv sync --group dev --extra web

# Install Taplo from upstream pre-built binary (much faster than `cargo install`,
# which compiles from source — ~1s vs ~2min). Detects OS + arch and pulls the
# matching release asset from https://github.com/tamasfe/taplo/releases.
# Falls back to `cargo install` if the platform isn't covered.
#
# Uses a shebang body so bash interprets $(...) and ${...} directly — Just's
# template engine would otherwise mangle them.
[group('install')]
install-taplo:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v taplo >/dev/null 2>&1; then
        echo -e "{{YELLOW}}Taplo is already installed{{NC}}"
        exit 0
    fi
    VERSION=0.10.0
    case "$(uname -s)" in
        Linux*)  os=linux ;;
        Darwin*) os=darwin ;;
        *)       os= ;;
    esac
    case "$(uname -m)" in
        x86_64)        arch=x86_64 ;;
        arm64|aarch64) arch=aarch64 ;;
        *)             arch= ;;
    esac
    if [ -z "$os" ] || [ -z "$arch" ]; then
        echo -e "{{YELLOW}}No pre-built binary for $(uname -s)/$(uname -m); using cargo install{{NC}}"
        cargo install taplo-cli \
            || { echo -e "{{RED}}Failed to install taplo-cli.{{NC}} Try '{{BLUE}}rustup update{{NC}}' first." >&2; exit 1; }
        exit 0
    fi
    INSTALL_DIR="${CARGO_HOME:-$HOME/.cargo}/bin"
    mkdir -p "$INSTALL_DIR"
    URL="https://github.com/tamasfe/taplo/releases/download/${VERSION}/taplo-${os}-${arch}.gz"
    TMP_TAPLO="$(mktemp "$INSTALL_DIR/taplo.tmp.XXXXXX")"
    trap 'rm -f "$TMP_TAPLO"' EXIT
    echo -e "{{BLUE}}Downloading $URL{{NC}}"
    if curl -fsSL "$URL" | gunzip > "$TMP_TAPLO" && chmod +x "$TMP_TAPLO" && mv -f "$TMP_TAPLO" "$INSTALL_DIR/taplo"; then
        trap - EXIT
        echo -e "{{GREEN}}✓ Taplo ${VERSION} installed to $INSTALL_DIR/taplo{{NC}}"
    else
        rm -f "$TMP_TAPLO"
        echo -e "{{RED}}Failed to download pre-built taplo; falling back to cargo install{{NC}}" >&2
        cargo install taplo-cli
    fi

# Format code
[group('dev')]
@format:
    echo "Running formatters..."
    echo "  ruff format"
    uv run ruff format {{py_package_path}}/
    echo "  ruff isort"
    uv run ruff check --select I --fix {{py_package_path}}/

alias f := format

# Format TOML files (comments preserved via pyproject.toml config)
[group('dev')]
@format-toml:
    taplo format *.toml --config .taplo.toml

alias ft := format-toml

# Check TOML formatting without modifying files
[group('dev')]
@check-toml:
    taplo check *.toml --config .taplo.toml

alias ct := check-toml

# Run linter (code style and quality checks)
[group('dev')]
@lint:
    echo "Running linter..."
    echo "  ruff"
    uv run ruff check {{py_package_path}}/

alias l := lint

# Run type checker
[group('dev')]
@typecheck:
    echo "Running type checker..."
    echo "  ty (ITM-026, per ADR-03)"
    uv run --extra web ty check {{py_package_path}}/

alias tc := typecheck

# Run tests
[group('test'), group('dev')]
@test *options:
    uv run pytest {{options}}

alias t := test

# Run tests with coverage and generate term-missing + HTML + XML reports
[group('test'), group('dev')]
@coverage:
    uv run pytest --cov=py_launch_blueprint --cov-report=term-missing --cov-report=html --cov-report=xml
    echo "Coverage report at htmlcov/index.html"

# Open the local HTML coverage report (macOS: open / Linux: xdg-open)
[group('test'), group('dev')]
@open-coverage-report:
    if command -v open >/dev/null 2>&1; then open htmlcov/index.html; else xdg-open htmlcov/index.html; fi

# Run all checks
[group('test'), group('dev'), group('quick start')]
@check: test lint typecheck check-yaml check-spelling check-editorconfig
    echo "All checks passed!"

alias ca := check

# Run package command.
[group('run'), group('quick start')]
@run cmd=app_name *args=args:
    uvx --with-editable . {{cmd}} {{args}}

# Run the FastAPI dev server (web extra) with auto-reload. Dev defaults to
# pretty console logs (prod default is JSON; WEB-12) — export
# <APP_NAME>_WEB_LOG_FORMAT yourself to override.
[group('run'), group('dev')]
serve host="127.0.0.1" port="8000":
    #!/usr/bin/env bash
    set -euo pipefail
    var="$(echo {{app_name}} | tr '[:lower:]' '[:upper:]')_WEB_LOG_FORMAT"
    export "${var}=${!var:-console}"
    exec uv run --extra web uvicorn {{py_package_name}}.web.app:create_app --factory --host {{host}} --port {{port}} --reload --timeout-graceful-shutdown 5

# Run web layer tests incl. slow contract fuzzing (web extra; httpx for TestClient)
[group('test'), group('dev')]
@test-web *options:
    uv run --extra web pytest tests/web -m "" {{options}}

# Regenerate the committed OpenAPI snapshot (WEB-51). Run after ANY route
# change — tests/web/test_openapi_snapshot.py fails until you do.
[group('build'), group('dev')]
@export-openapi:
    uv run --extra web python scripts/export_openapi.py

# Generate a typed Python client from the OpenAPI snapshot (WEB-60)
[group('build')]
@client-python out="clients/python":
    uvx openapi-python-client generate --path docs/api/openapi.json --output-path {{out}} --overwrite
    echo "client written to {{out}}"

# Build the production web-service image (WEB-32)
[group('build')]
@docker-web tag="plbp-web:dev": _guard
    docker build -t {{tag}} .

# Audit locked dependencies (all extras + groups) against known CVEs (WL-014).
# Same pipeline as the scheduled dep-audit workflow.
[group('dev')]
audit:
    #!/usr/bin/env bash
    set -euo pipefail
    tmp="$(mktemp)"
    trap 'rm -f "$tmp"' EXIT
    uv export --locked --no-emit-project --all-extras --all-groups \
        --format requirements.txt --quiet -o "$tmp"
    uv run pip-audit --strict --disable-pip -r "$tmp"

# Blueprint setup guard — Tier 2 (hard block on the risk subset).
# Private. Used as a dependency on recipes that produce a wrong artifact,
# an external side effect, or an identity-bearing write when run un-migrated.
[private]
@_guard:
    bash init/guard.sh block

# Run the blueprint init walkthrough (re-brands this project).
# `init` and `init-doctor` deliberately OMIT the _guard dependency — they are
# the escape hatch and must always be runnable.
[group('setup'), group('init')]
init *args=args:
    uv run init/init.py {{args}}

# Audit blueprint migration completeness and environment readiness.
[group('setup'), group('init')]
init-doctor *args=args:
    uv run init/init_doctor.py {{args}}

# Post-init walkthrough: configure publishing (PyPI/release-please),
# Codecov uploads, and ReadTheDocs. Run AFTER `just init` and after the
# first push to GitHub (or with --skip-remote for local-only changes).
[group('setup'), group('init')]
post-init *args=args:
    uv run init/post_init.py {{args}}

# Build package
[group('build'), group('dev')]
@build: _guard check
    uv build

alias b := build

# Wire lefthook into .git/hooks (idempotent)
[group('setup'), group('hooks')]
@hooks-install:
    lefthook install

# Run all lefthook pre-commit checks against the whole tree
[group('hooks')]
@hooks-run:
    lefthook run pre-commit --all-files

alias hooks := hooks-run

# Check installed package version
[group('releases'), group('utilities')]
@version cmd=app_name:
    {{cmd}} --version

# Collect system and environment information for debugging
[group('debug')]
debug-info:
    #!/usr/bin/env sh
    echo "## Debug Information"
    echo ""
    echo "### System Information"
    echo "- Date: $(date)"
    echo "- OS Family: {{os_family()}}"
    if [ "{{os_family()}}" = "macos" ]; then
        echo "- macOS Version: $(sw_vers -productVersion)"
        echo "- Kernel: $(uname -r)"
        echo "- Architecture: $(uname -m)"
    elif [ "{{os_family()}}" = "unix" ]; then
        if command -v lsb_release >/dev/null 2>&1; then
            echo "- Distribution: $(lsb_release -ds)"
        elif [ -f /etc/os-release ]; then
            . /etc/os-release
            echo "- Distribution: ${PRETTY_NAME}"
        fi
        echo "- Kernel: $(uname -r)"
        echo "- Architecture: $(uname -m)"
        echo "- Git Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'Not a git repository or error')"
    elif [ "{{os_family()}}" = "windows" ]; then
        # Basic Windows info, might need refinement based on user env (Git Bash, Cygwin, WSL)
        echo "- Windows Version: $(systeminfo | findstr /B /C:"OS Name" | sed 's/.*: //')" # May need admin rights or fail
        echo "- Kernel: $(uname -r)"
        echo "- Architecture: $(uname -m)"
    else
        echo "- Kernel: $(uname -r)"
        echo "- Architecture: $(uname -m)"
    fi
    echo ""
    echo "### Development Tools"
    if command -v python3 >/dev/null 2>&1; then echo "python: $(python3 --version)"; else echo "python: Not Found"; fi
    if command -v uv >/dev/null 2>&1; then echo "uv: $(uv --version)"; else echo "uv: Not Found"; fi
    echo "ruff: $(uvx ruff --version)"
    if command -v git >/dev/null 2>&1; then echo "git: $(git --version)"; else echo "git: Not Found"; fi
    if command -v just >/dev/null 2>&1; then echo "just: $(just --version)"; else echo "just: Not Found"; fi
    echo "CLI Version:{{app_name}}: $(uvx --with-editable . {{app_name}} --version 2>/dev/null || echo 'Not Found or Error')"
    echo "Project Version: $(uvx --with-editable . python -c 'import {{py_package_name}}; print({{py_package_name}}.__version__)' 2>/dev/null || echo 'Version Not Found')"

    echo ""
    echo "### Installed Project Packages"
    if command -v uv >/dev/null 2>&1; then uv pip list; else echo "uv not found, cannot list packages"; fi

    echo ""
    echo "### Declared Dependencies (pyproject.toml)"
    grep -E '^\[project(\.optional-dependencies)?\.\[^]]*\]|^\s*\w+\s*=|^\s*"?[^"=\s]+"?\s*=' pyproject.toml 2>/dev/null || echo "Could not read dependencies from pyproject.toml"

# Clean up temporary files and caches
[group('clean')]
@clean:
    rm -rf .pytest_cache
    rm -rf .mypy_cache
    rm -rf .ruff_cache
    rm -rf .coverage
    rm -rf htmlcov
    rm -rf dist
    rm -rf build
    rm -rf *.egg-info
    rm -rf .venv
    rm -rf {{py_package_path}}/__pycache__/

# Docs recipes call Sphinx via `uv run --group docs` (PEP 735 dependency
# group, per ITM-063 — same path Read the Docs uses). uv syncs the group
# on demand, so there is no separate install step.

# Not usually needed, Initialize docs only if you are starting a new project
[group('docs'), group('setup')]
@init-docs:
    uv run --group docs --directory=docs sphinx-quickstart
# recommend you separate "source" and "build" directories within the root path (docs/source and docs/build)

# Show available Sphinx build targets
[group('docs'), group('help')]
@docs-help:
    uv run --group docs sphinx-build -M help docs/source docs/build

# Build documentation (default html format) change the target if needed e.g. just docs latexpdf
[group('docs'), group('build')]
@docs target="html":
    uv run --group docs sphinx-build -M {{target}} docs/source docs/build

# Run documentation server with hot reloading
[group('docs'), group('run'), group('dev')]
@docs-dev:
    uv run --group docs sphinx-autobuild -b html docs/source docs/build

# Clean documentation build files
[group('docs'), group('clean')]
@docs-clean:
    rm -rf docs/build

# Update CONTRIBUTORS.md file
alias contributors := update-contributors

[group('build')]
update-contributors:
    npx {{contributors_package}} init --non-interactive --owner {{contributors_owner}} --repo {{repo_name}} --config-file .contributors.yml

# Verify commit messages follow conventional commit format (commitlint per ADR-04).
[group('hooks')]
verify-commits start="HEAD~10" end="HEAD":
    echo "Verifying commit messages with commitlint..."
    bunx --bun commitlint --from={{start}} --to={{end}}

# Version-bump and create-commit recipes (cog) retired in ITM-044:
# - release-please opens version-bump PRs automatically (ADR-05).
# - Use `git commit -m "feat: ..."` directly; commitlint enforces format.

# Install COG (Cocogitto) for changelog and commit management
[group('install'), group('releases')]
install-cog:
    echo "Installing Cocogitto (cog)..."
    case "$(uname -s)" in \
    Linux*) \
        if command -v cargo >/dev/null 2>&1; then \
            cargo install --force cocogitto; \
        else \
            echo "{{YELLOW}}Please install Rust's cargo to install cog{{NC}}"; \
            echo "Visit https://www.rust-lang.org/tools/install"; \
        fi \
        ;; \
    Darwin*) \
        if command -v brew >/dev/null 2>&1; then \
            brew install cocogitto; \
        else \
            echo "{{YELLOW}}Please install Homebrew to install cog{{NC}}"; \
            echo "Visit https://brew.sh/"; \
        fi \
        ;; \
    CYGWIN*|MINGW*|MSYS*|Windows*) \
        echo "{{YELLOW}}On Windows, please install from https://github.com/cocogitto/cocogitto/releases{{NC}}"; \
        ;; \
    *) \
        echo "{{RED}}Unknown OS, please install manually from https://github.com/cocogitto/cocogitto{{NC}}"; \
        ;; \
    esac
    command -v cog >/dev/null 2>&1 && echo "{{GREEN}}✓{{NC}} Cocogitto installed successfully" || echo "{{RED}}✗{{NC}} Failed to install Cocogitto"

# Check if COG is installed and setup pre-commit hook for commit message verification
[group('setup'), group('pre-commit')]
setup-cog-hooks:
    command -v cog >/dev/null 2>&1 || { echo "{{RED}}Error: Cocogitto (cog) is not installed{{NC}}"; just install-cog; }
    cog install-hook commit-msg
    echo "{{GREEN}}✓{{NC}} Commit message hook installed"

# Generate the changelog locally
[group('releases')]
changelog:
    command -v cog >/dev/null 2>&1 || { echo "{{RED}}Error: Cocogitto (cog) is not installed{{NC}}"; exit 1; }
    cog changelog > CHANGELOG.md
    echo "{{GREEN}}✓{{NC}} CHANGELOG.md updated"

# Install gitleaks for local secret scanning
[group('setup'), group('install'), group('pre-commit')]
install-gitleaks:
    bash scripts/install-gitleaks.sh

# Run gitleaks. Use `just check-gitleaks staged` for pre-commit-style checks.
[group('dev'), group('pre-commit')]
check-gitleaks mode="full":
    bash scripts/check-gitleaks.sh {{mode}}

# Create a test repository from a PR
[group('workflow')]
[confirm("Are you sure you want to create a new repository from a PR?")]
pr-to-testrepo pr_number new_repo_name="test-actions-repo": _guard
    #!/usr/bin/env bash
    set -euo pipefail

    # Check if gh CLI is installed
    if ! command -v gh >/dev/null 2>&1; then
        echo -e "{{RED}}Error: GitHub CLI (gh) is not installed. Please install it to use this command.{{NC}}"
        exit 1
    fi

    # Check if gh is authenticated
    if ! gh auth status >/dev/null 2>&1; then
        echo -e "{{RED}}Error: Not logged in to GitHub CLI. Please run 'gh auth login'.{{NC}}"
        exit 1
    fi

    # Get current repo URL
    repo_url=$(gh repo view --json url -q .url)

    # Move down one directory and clone
    cd ..
    echo -e "{{BLUE}}Cloning repository into {{new_repo_name}}...{{NC}}"
    if ! git clone "$repo_url" "{{new_repo_name}}"; then
        echo -e "{{RED}}Error: Failed to clone repository{{NC}}"
        exit 1
    fi

    cd "{{new_repo_name}}"
    echo -e "{{BLUE}}Downloading PR #{{pr_number}}...{{NC}}"
    if ! gh pr checkout {{pr_number}}; then
        echo -e "{{RED}}Error: Failed to checkout PR #{{pr_number}}. Does it exist?{{NC}}"
        exit 1
    fi

    echo -e "{{BLUE}}Removing existing git references...{{NC}}"
    rm -rf .git

    echo -e "{{BLUE}}Initializing new git repository...{{NC}}"
    git init -b main # Initialize with main branch

    # Create the marker file
    echo "This repository was created by the pr-to-testrepo just recipe." > pr2testrepo.txt
    echo -e "{{BLUE}}Created marker file pr2testrepo.txt{{NC}}"

    git add .
    git add pr2testrepo.txt # Explicitly add marker file

    # Check if there are any changes to commit (other than the marker file)
    if git diff --staged --quiet -- ':!pr2testrepo.txt'; then
        echo -e "{{YELLOW}}Warning: No changes detected after checkout. Initial commit will be empty.{{NC}}"
    fi

    git commit -m "Initial commit from PR #{{pr_number}}" --allow-empty

    echo -e "{{BLUE}}Creating and pushing to GitHub repository '{{new_repo_name}}'...{{NC}}"
    if ! gh repo create {{new_repo_name}} --private --source=. --push; then
        echo -e "{{RED}}Error: Failed to create or push to the repository '{{new_repo_name}}'.{{NC}}"
        echo -e "{{YELLOW}}Please check if a repository with this name already exists or if you have the necessary permissions.{{NC}}"
        # Attempt to clean up the local repo if creation failed
        echo -e "{{BLUE}}Attempting to clean up local git repository...{{NC}}"
        rm -rf .git
        exit 1
    fi
    echo ""
    # Print shell information
    echo -e "{{BLUE}}Shell in use: $SHELL{{NC}}"
    echo -e "{{YELLOW}}Please cd to the repository directory and ...{{NC}}"
    echo -e "{{RED}}MANUALLY EXECUTE THE NEXT COMMAND{{NC}}"
    echo -e "{{BLUE}}cd ../{{new_repo_name}}{{NC}}"
    echo "cd ../{{new_repo_name}}" | {{CLIPBOARD_CMD}}
    # Get the URL of the newly created repository
    #repo_url=$(gh repo view {{new_repo_name}} --json url -q .url); \
    #echo -e "{{GREEN}}{{CHECK}} Repository created and ready for testing at: ${repo_url}{{NC}}"




# Cleanup / Delete test repository from a PR from pr-to-testrepo
[group('workflow')]
[confirm("Are you sure you want to delete the remote repository '{{new_repo_name}}' and clean up the local directory?")]
clean-pr-to-testrepo new_repo_name="test-actions-repo": _guard
    #!/usr/bin/env bash
    set -euo pipefail

    echo -e "{{BLUE}}Shell in use: $SHELL{{NC}}"

    # Safety check: Ensure the marker file exists in the parent directory
    # We expect this command to be run from the original repo,
    # and the test repo to be a sibling directory.
    marker_file="../{{new_repo_name}}/pr2testrepo.txt"

    if [[ ! -f "$marker_file" ]]; then
        echo -e "{{RED}}Error: Marker file '$marker_file' not found relative to current directory.{{NC}}"
        echo -e "{{YELLOW}}This might not be a repository created by 'pr-to-testrepo', the local directory might be missing, or you might be in the wrong directory.{{NC}}"
        echo -e "{{YELLOW}}Aborting delete. Please ensure you are in the original repository directory.{{NC}}"
        exit 1
    fi
    echo -e "{{GREEN}}{{CHECK}} Marker file found. Proceeding with deletion...{{NC}}"

    # Delete the remote GitHub repository
    echo -e "{{BLUE}}Attempting to delete remote repository '{{new_repo_name}}'...{{NC}}"
    if ! gh repo delete {{new_repo_name}} --yes; then
        echo -e "{{RED}}Error: Failed to delete remote repository '{{new_repo_name}}'. It might not exist or permissions are missing.{{NC}}"
        # Do not exit immediately, still offer local cleanup instructions
    else
         echo -e "{{GREEN}}{{CHECK}} Remote repository deleted successfully.{{NC}}"
    fi

    echo ""
    echo -e "{{YELLOW}}Remote deletion step complete (check status above).{{NC}}"
    echo -e "{{YELLOW}}Please clean up the local git repository directory:{{NC}}"
    echo -e "{{RED}}MANUALLY EXECUTE THE NEXT COMMAND(S){{NC}}"
    local_cleanup_cmd="cd .. && rm -rf {{new_repo_name}} && cd {{repo_name}}"
    echo -e "{{BLUE}}${local_cleanup_cmd}{{NC}}"
    # Attempt to copy the cleanup command to clipboard
    echo "${local_cleanup_cmd}" | {{CLIPBOARD_CMD}} || echo "(Failed to copy command to clipboard)"

# Create a test Pull Request for triggering GitHub Actions
[group('workflow')]
@create-test-pr message="Test PR for GitHub Actions verification":
    #!/usr/bin/env bash
    set -euo pipefail

    # Check if gh CLI is installed
    if ! command -v gh >/dev/null 2>&1; then
        echo -e "{{RED}}Error: GitHub CLI (gh) is not installed. Please install it to use this command.{{NC}}"
        exit 1
    fi

    # Check if gh is authenticated
    if ! gh auth status >/dev/null 2>&1; then
        echo -e "{{RED}}Error: Not logged in to GitHub CLI. Please run 'gh auth login'.{{NC}}"
        exit 1
    fi
    CURRENT_BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)

    echo "{{BLUE}}CURRENT_BRANCH: $CURRENT_BRANCH_NAME{{NC}}"
    # Ensure we are on the main/master branch before starting Add common main branch names here if needed
    if [[ "$CURRENT_BRANCH_NAME" != "main" && "$CURRENT_BRANCH_NAME" != "master" ]]; then
        echo "{{YELLOW}}Warning: Not on main/master branch. Checking out main...{{NC}}"
        if ! git checkout main; then
            echo "{{RED}}Error: Could not checkout main branch. Please switch manually and retry.{{NC}}"
            exit 1
        fi
    fi

    # Ensure local main is up-to-date
    echo -e "{{BLUE}}Pulling latest changes for main branch...{{NC}}"
    if ! git pull origin main; then
        echo -e "{{RED}}Error: Failed to pull latest changes for main. Please check your connection or repository status.{{NC}}"
        exit 1
    fi

    echo -e "{{BLUE}}Creating test branch: {{BRANCH_NAME}}{{NC}}"
    if ! git checkout -b {{BRANCH_NAME}}; then
        echo -e "{{RED}}Error: Failed to create branch {{BRANCH_NAME}}.{{NC}}"
        exit 1
    fi

    # Add timestamp to README
    echo -e "{{BLUE}}Modifying README.md...{{NC}}"
    echo "" >> README.md # Add a blank line for spacing
    echo "Test change at $(date) to trigger Actions." >> README.md
    MESSAGE="Test PR for GitHub Actions verification"

    # Commit and push
    echo -e "{{BLUE}}git add README.md...{{NC}}"
    git add README.md
    echo -e "{{BLUE}}Committing and pushing changes...{{NC}}"
    if ! git commit -m "$MESSAGE"; then
        echo -e "{{RED}}Error: Failed to commit changes.{{NC}}"
        # Attempt to switch back to main branch on failure
        git checkout main
        exit 1
    fi
    echo -e "{{BLUE}}git push -u origin {{BRANCH_NAME}}...{{NC}}"
    if ! git push -u origin "{{BRANCH_NAME}}"; then
        echo -e "{{RED}}Error: Failed to push branch {{BRANCH_NAME}} to origin.{{NC}}"
        # Attempt to switch back to main branch on failure
        git checkout main
        exit 1
    fi

    # Create PR
    echo -e "{{BLUE}}Creating Pull Request...{{NC}}"
    # Get the current repo info
    REPO_NAME=$(gh repo view --json nameWithOwner -q .nameWithOwner)
    echo "REPO_NAME: $REPO_NAME"
    PR_URL=$(gh pr create --title "$MESSAGE" --body "This is an automated PR to test GitHub Actions." --repo "$REPO_NAME")
    echo "PR_URL: $PR_URL"
    if [[ $? -ne 0 ]]; then
        echo "{{RED}}Error: Failed to create Pull Request via GitHub CLI.{{NC}}"
        # Attempt to switch back to main branch on failure
        git checkout main
        exit 1
    else
        echo "{{GREEN}}{{CHECK}} Test PR created successfully: $PR_URL{{NC}}"
        # Switch back to main branch after successful PR creation
        git checkout main
    fi

[group('dev'), group('quick start')]
@dev:
    just format
    just lint
    just test
    # just build
    # just run

# Alias for dev (full developer cycle: format → lint → test → build)
alias cycle := dev

# Install yamlfmt from upstream pre-built binary (no Go toolchain needed —
# same approach as install-taplo). Detects OS + arch and pulls the matching
# release asset from https://github.com/google/yamlfmt/releases.
# Falls back to `go install` if the platform isn't covered.
#
# Uses a shebang body so bash interprets $(...) and ${...} directly — Just's
# template engine would otherwise mangle them.
[group('setup'), group('install')]
install-yamlfmt:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v yamlfmt >/dev/null 2>&1; then
        echo -e "{{YELLOW}}yamlfmt is already installed{{NC}}"
        exit 0
    fi
    VERSION=0.17.2
    case "$(uname -s)" in
        Linux*)  os=Linux ;;
        Darwin*) os=Darwin ;;
        *)       os= ;;
    esac
    case "$(uname -m)" in
        x86_64)        arch=x86_64 ;;
        arm64|aarch64) arch=arm64 ;;
        *)             arch= ;;
    esac
    if [ -z "$os" ] || [ -z "$arch" ]; then
        echo -e "{{YELLOW}}No pre-built binary for $(uname -s)/$(uname -m); using go install{{NC}}"
        go install github.com/google/yamlfmt/cmd/yamlfmt@v${VERSION} \
            || { echo -e "{{RED}}Failed to install yamlfmt.{{NC}} Install Go first: https://go.dev/dl/" >&2; exit 1; }
        exit 0
    fi
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
    URL="https://github.com/google/yamlfmt/releases/download/v${VERSION}/yamlfmt_${VERSION}_${os}_${arch}.tar.gz"
    echo -e "{{BLUE}}Downloading $URL{{NC}}"
    if curl -fsSL "$URL" | tar -xz -C "$INSTALL_DIR" yamlfmt && chmod +x "$INSTALL_DIR/yamlfmt"; then
        echo -e "{{GREEN}}✓ yamlfmt ${VERSION} installed to $INSTALL_DIR/yamlfmt{{NC}}"
        command -v yamlfmt >/dev/null 2>&1 \
            || echo -e "{{YELLOW}}Note: add $INSTALL_DIR to your PATH to use yamlfmt{{NC}}"
    else
        echo -e "{{RED}}Failed to download pre-built yamlfmt; falling back to go install{{NC}}" >&2
        go install github.com/google/yamlfmt/cmd/yamlfmt@v${VERSION}
    fi

# YAML formatting and validation with yamlfmt
[group('dev')]
@format-yaml:
    echo "🎨 Formatting YAML files with yamlfmt..."
    yamlfmt .

[group('dev')]
@lint-yaml:
    echo "🔍 Linting YAML files with yamllint..."
    uv run yamllint -c .yamllint .

[group('dev')]
@check-yaml:
    echo "✅ Checking YAML formatting..."
    uv run yamllint -c .yamllint .
    echo "YAML files are properly linted!"

[group('dev')]
@check-spelling:
    echo "🔍 Checking spelling..."
    uv run codespell .

[group('dev')]
@check-editorconfig:
    echo "🔍 Checking EditorConfig rules..."
    uv run ec -config .editorconfig-checker.json
