```{figure} _static/py_launch_blueprint_logo_100x100.png
:alt: py-launch-blueprint
:width: 100px
:align: left
```

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

# Py Launch Blueprint
**A Production-Ready Python Project Template with Integrated Best Practices**

![GitHub repo](https://img.shields.io/badge/github-repo-green)
![Changelog](https://img.shields.io/github/v/release/smorinlabs/py-launch-blueprint?include_prereleases&label=changelog)
![Tests](https://github.com/simonw/llm/workflows/Test/badge.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![GitHub stars](https://img.shields.io/github/stars/smorinlabs/py-launch-blueprint?style=social)
![Discord](https://img.shields.io/discord/1364098187375153192?style=flat&logo=discord)

---
Py Launch Blueprint is a comprehensive Python project template that eliminates setup friction by providing a pre-configured development environment with carefully selected tools for linting, formatting, and type checking. It includes an annotated CLI example and detailed documentation explaining each tool choice and configuration decision, making it an ideal starting point for professional Python projects.

## Why Choose Py Launch Blueprint?

Py Launch Blueprint eliminates the setup friction in Python projects by providing a production-ready template with carefully curated tools and best practices. Here's what makes it special:

## Full documentation on ReadTheDocs
- [py-launch-blueprint Docs](https://py-launch-blueprint.readthedocs.io/en/latest/)
- [Discord Community](https://discord.gg/3zh8JyV6fU)


### 🚀 Key Features

# 🐍 Python Project Template - Py Launch Blueprint

**Zero-config** development environment with **type safety** built in.

## ✨ Features TLDR
- 🛠️ **Dev Tools**: Ruff (linting/formatting), `ty` (type checking, Astral), lefthook (hooks), commitlint
- 🧠 **AI Ready**: Default configs for Cursor, Windsurf, Claude Code
- 💪 **Production**: Python 3.12+, uv + uv_build, PEP 735 dependency-groups
- 🚀 **DX - Developer Experience**: VS Code integration, sensible defaults, quality documentation
- 🔄 **CI/CD**: GitHub Actions workflows, automatic testing, version management

## 🎯 Perfect For
Teams and professionals needing maintainable, type-safe Python projects following best practices.

## Quick Start

### Step 1 - Copy repository
```bash
git clone https://github.com/smorinlabs/py-launch-blueprint
cd py-launch-blueprint
```

### Step 2 - Install dependencies
```bash
make check #follow any suggested instructions
make help
```

### Step 3 - Install project
```bash
    just check-deps
    just install-dev
    just hooks-install
    just help
```

### Step 4 - Use
```bash
just hooks-run
just check
```

## Complete Feature List

### Development Tools

- **Bootstrap dependency check and install with `make`**: Execute common development tasks with simple commands, standardizing workflows across team members.

- **Command running with `just`**: Define and run project-specific commands with a modern Make alternative, simplifying complex operations with clear syntax.

- **Linting with `ruff`**: Catch errors and enforce code style at lightning speed (10-100x faster than traditional linters), reducing waiting time and improving developer productivity.

- **Type checking with [`ty`](https://docs.astral.sh/ty/)**: Prevent type-related bugs before they occur with Astral's fast Rust-based type checker, making your codebase more robust and easier to maintain as it grows.

- **Formatting with `ruff`**: Ensure consistent code style across your project automatically, eliminating style debates and pull request revision cycles.

- **Git hooks with [`lefthook`](https://lefthook.dev/)**: Enforce quality standards before code enters your repository (secret scanning, linting, commit-message checks at commit/push), preventing bad code from ever being committed and reducing technical debt.

- **TOML formatting and validation with `taplo`**: Verify Toml files for syntax correctness, maintain consistent configuration files, ensuring readability and avoiding syntax errors in critical project settings.

- **YAML validation with [yamllint](tools/yaml_lint.md)**: Verify YAML files for syntax correctness, preventing configuration errors and deployment failures.

### Project Structure & Management

- **Project configuration with `pyproject.toml`**: Organize all project settings in one standardized location, simplifying maintenance and configuration.

- **Dependency groups separation**: Organize dependencies into main, dev, and doc categories, preventing bloated installations and clarifying requirements as part of `pyproject.toml` configuration.

- **Dependency management with [`uv`](https://docs.astral.sh/uv/)**: Install and manage packages at blazing speed (100x faster than pip/poetry), dramatically reducing environment setup time.

- **Build system with `uv_build`**: Build wheel and source distributions with uv's build backend and `uv build`.

- **Versioning with explicit project metadata**: Keep release tags aligned with the static version in `pyproject.toml` for predictable package metadata.

- **Copyright license automation**: Automatically add license headers to all files, ensuring legal compliance without manual effort.

### Documentation

- **Documentation with `sphinx + MyST`**: Generate comprehensive documentation that supports both reStructuredText and Markdown, improving contributor accessibility.

- **`Read the Docs` integration**: Deploy documentation automatically, providing instant hosting and versioning for your project's documentation.

- **Changelog management with `release-please`**: Generate the changelog and version bumps automatically from Conventional Commits, improving project transparency and adoption.

### Testing & Quality Assurance

- **Testing framework with `pytest`**: Write and run tests with a modern, powerful testing framework that supports fixtures and parameterization.

- **CI/CD with `GitHub Actions`**: Automatically test, build, and deploy your project on multiple Python versions, catching compatibility issues early.

- **Matrix testing with `GitHub Actions`**: Run tests across multiple Python versions and operating systems, ensuring broad compatibility.

- **Simplified debugging info with `just debug-info`**: Automatically collect and format essential system, tool, and dependency information for streamlined bug reporting via a simple command.

### GitHub Integration

- **Pull request template**: Guide contributors through the PR process with structured information requirements, improving submission quality.

- **Issue templates (Feature, Bug, Documentation)**: Standardize issue reporting with appropriate fields for each type, gathering all necessary information upfront.

- **Automated contributor recognition with `contributors-please`**: Automatically update contributor lists, acknowledging all project participants without manual tracking.

- **Conventional commits enforced with `commitlint`**: Enforce structured commit messages so `release-please` can automate changelog generation and version bumps.

- **Security policy**: Establish clear vulnerability reporting procedures, promoting responsible disclosure and faster security fixes.

- **Code of conduct**: Set community behavior expectations, fostering an inclusive and respectful project environment.

- **Contributing guidelines**: Provide clear instructions for contributors, reducing friction for new participants.

- **Automated dependency security scanning with `codeql`**: Detect vulnerable dependencies automatically, protecting your users from known security issues.

- **CLA (Contributor License Agreement) check `[TODO:LOOKUP ISSUE](https://github.com/smorinlabs/py-launch-blueprint/issues/162)`**: Ensure all contributors have signed appropriate licensing agreements, protecting the project legally.

### IDE Integration

- **VS Code integration**: Provide optimized settings and configurations for Visual Studio Code, enhancing developer productivity.

- **PyRight configuration**: Enable accurate, real-time type checking in the editor, catching errors before running tests.

- **Editor extensions recommendations**: Suggest optimal VS Code extensions automatically, standardizing the development environment.

### AI Integration

- **AI assistance with common agents `Cursor, Windsurf, Claude Code, Codex`**: Support popular AI coding assistants enabling AI-powered development.

- **Cursor Rules configuration**: Optimize Cursor AI assistant for your specific project structure, improving suggestion relevance.

- **Windsurf Rules configuration**: Configure Windsurf IDE to understand your project architecture, enhancing code generation quality.

Start your next Python project with confidence, knowing you're building on a foundation of best practices and modern development tools.



### Installation

#### From PyPI

```bash
pip install py-launch-blueprint
```

#### From Source

```bash
git clone https://github.com/smorinlabs/py-launch-blueprint.git
cd py-launch-blueprint
pip install -e ".[dev]"  # Install with development dependencies
```

#### Direct Usage

After installing, the CLI is available as `plbp`:

```bash
plbp --help
```

### Configuration

`plbp` reads settings from a layered TOML config (system → user → project),
with per-setting precedence `flag → env (PLBP_*) → project → user → system →
default`. Secrets are never stored in config — the API token resolves from
`--token` or `$PLBP_TOKEN` only.

```bash
# show the resolved config file path
plbp config path

# read / write non-secret keys by dotted path (no network needed)
plbp config get output.color
plbp config set output.format json
```

### Usage

```bash
# Projects (noun) → list / get (verbs)
plbp projects list
plbp projects list --workspace "My Workspace"
plbp projects list --limit 50
plbp projects get 12345

# JSON output (pipe-safe; logs stay on stderr)
plbp projects list --json

# Diagnose setup (Python / platform, config file, token)
plbp doctor

# Help and version
plbp --help
plbp --version
```

For the full flag reference, output contract, and logging model, see
[EXAMPLECLI.md](https://github.com/smorinlabs/py-launch-blueprint/blob/main/EXAMPLECLI.md).

### Error Codes

- 0: Successful execution
- 1: Configuration error
- 2: Authentication error
- 3: API error
- 4: Input/Output error
- 5: User interrupt

## Table of Contents

```{toctree}
---
maxdepth: 3
---
about/index
tasks/index
tools/index
tutorials/index
web/index
reference/index
contributing/index
github-templates
```
