<!-- ITM-081 — badges. Single horizontal row (decided round 23). -->
[![PyPI version](https://img.shields.io/pypi/v/py-launch-blueprint.svg)](https://pypi.org/project/py-launch-blueprint/)
[![Python versions](https://img.shields.io/pypi/pyversions/py-launch-blueprint.svg)](https://pypi.org/project/py-launch-blueprint/)
[![CI](https://github.com/smorinlabs/py-launch-blueprint/actions/workflows/ci.yml/badge.svg)](https://github.com/smorinlabs/py-launch-blueprint/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/smorinlabs/py-launch-blueprint/branch/main/graph/badge.svg)](https://codecov.io/gh/smorinlabs/py-launch-blueprint)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://www.conventionalcommits.org/)

# Py Launch Blueprint: A Production-Ready 🐍 Python Project Template with Integrated Best Practices
 Py Launch Blueprint is a comprehensive Python project template that eliminates setup friction by providing a pre-configured development environment with carefully selected tools for linting, formatting, and type checking. It includes an annotated CLI example and detailed documentation explaining each tool choice and configuration decision, making it an ideal starting point for professional Python projects.

![Py Launch Blueprint Logo](./assets/images/logos/py_launch_blueprint_logo_100x100.png)

## Why Choose Py Launch Blueprint?

Py Launch Blueprint eliminates the setup friction in Python projects by providing a production-ready template with carefully curated tools and best practices.

## Full documentation on ReadTheDocs
- [py-launch-blueprint Docs](https://py-launch-blueprint.readthedocs.io/en/latest/)

### 🚀 Key Features

**Zero-config** development environment with **type safety** built in.

## ✨ Features TLDR
- 🛠️ **Dev Tools**: Ruff (linting/formatting), `ty` (type checking, Astral), lefthook (hooks), commitlint
- 🔒 **Security**: gitleaks (commit/push), TruffleHog (CI), bandit (pre-push + CI), CodeQL
- 🧠 **AI Ready**: AGENTS.md as the single canonical agent config (CLAUDE.md imports it; Cursor, Windsurf, Codex read it natively) + a project-bootstrap skill
- 💪 **Production**: Python 3.12+, uv + uv_build, PEP 735 dependency-groups, static version
- 🚀 **DX - Developer Experience**: VS Code DevContainer, sensible defaults, quality documentation
- 🔄 **CI/CD**: GitHub Actions workflows, release-please version bumps, OIDC trusted publishing

## Quick start

```bash
git clone https://github.com/smorinlabs/py-launch-blueprint.git
cd py-launch-blueprint
make bootstrap           # level 1 — base toolchain (just + uv); skip if installed
just setup               # level 2 — dev env, git hooks, hook toolchain
just check               # full quality pipeline
```

Install as a tool: `uvx --from py-launch-blueprint plbp` (uvx needs `--from` because the distribution name differs from the console-script name) or `pip install py-launch-blueprint && plbp`.

The [`plbp` noun-verb CLI](EXAMPLECLI.md) documents the template's CLI conventions: global flags, the text/JSON/Markdown output contract, stable exit & error codes, and layered TOML config.

See [AGENTS.md](AGENTS.md) for the canonical command set, [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) for the daily workflow, and [docs/RELEASE.md](docs/RELEASE.md) for the release flow.

## Web service (FastAPI)

The blueprint includes an optional REST API (`uv sync --extra web`, `just serve`) with production best practices already baked in: RFC 9457 problem+json errors, `/v1` versioning, pagination, Idempotency-Key replay, Prometheus metrics, opt-in OpenTelemetry tracing, rate limiting, security headers, typed env settings, a committed OpenAPI snapshot with breaking-change CI (oasdiff) and schemathesis fuzzing, generated typed clients, and a production Dockerfile. See [EXAMPLEWEB.md](EXAMPLEWEB.md) for the service walkthrough (the web counterpart of [EXAMPLECLI.md](EXAMPLECLI.md)), the [web service docs](docs/source/web/index.md), the [WEB-xx convention catalog](docs/design/0002-web-api-conventions.md), and [ADR 0013](docs/adr/0013-web-service-best-practices.md) for the design decisions.

**Starting a new project from this template?** If you use Claude Code or any agent that reads `AGENTS.md`, just say *"create a new Python project from py-launch-blueprint"* — the [`new-python-project`](.claude/skills/new-python-project/SKILL.md) skill (Claude Code discovers it in `.claude/skills/`; Codex via the `.agents/skills/` symlink) will walk you through `gh repo create --template`, identity collection, the init rebrand with dry-run preview, and an optional handoff to post-init for publishing/Codecov/ReadTheDocs setup. For humans without an agent: the skill is also a copy-pasteable runbook. After init, work through [`docs/POST_INIT.md`](docs/POST_INIT.md) — the checklist of decisions, secrets, and repo settings to configure. Internal engineering docs (ADRs, design specs, research) live under [`docs/`](docs/README.md).

### 🎯 Perfect For
Teams and professionals needing maintainable, type-safe Python projects following best practices.

## Complete Feature List

### Development Tools

- **Bootstrap dependency check and install with `make`**: Execute common development tasks with simple commands, standardizing workflows across team members.

- **Optional one-command toolchains with [`mise`](https://mise.jdx.dev/) or [`flox`](https://flox.dev/)**: `mise install` (root `mise.toml`) or `flox activate` (root `.flox/`) provisions the same 10-tool set as the native installers — pick whichever fits your machine; see [ADR 0005](docs/adr/0005-mise-flox-first-class-toolchains.md).

- **Command running with `just`**: Define and run project-specific commands with a modern Make alternative, simplifying complex operations with clear syntax.

- **Linting with `ruff`**: Catch errors and enforce code style at lightning speed (10-100x faster than traditional linters), reducing waiting time and improving developer productivity.

- **Type checking with [`ty`](https://docs.astral.sh/ty/)**: Prevent type-related bugs before they occur with Astral's fast Rust-based type checker, making your codebase more robust and easier to maintain as it grows.

- **Formatting with `ruff`**: Ensure consistent code style across your project automatically, eliminating style debates and pull request revision cycles.

- **Git hooks with [`lefthook`](https://lefthook.dev/)**: Enforce quality standards before code enters your repository (secret scanning, linting, commit-message checks at commit/push), preventing bad code from ever being committed and reducing technical debt.

- **TOML formatting and validation with `taplo`**: Verify Toml files for syntax correctness, maintain consistent configuration files, ensuring readability and avoiding syntax errors in critical project settings.

- **YAML validation with [yamllint](docs/source/tools/yaml_lint.md)**: Verify YAML files for syntax correctness, preventing configuration errors and deployment failures.

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

- **CLA (Contributor License Agreement) check via [`CLA Assistant`](docs/source/tools/cla-assistant.md)**: Ensure all contributors have signed appropriate licensing agreements, protecting the project legally.

### IDE Integration

- **VS Code integration**: Provide optimized settings and configurations for Visual Studio Code, enhancing developer productivity.

- **PyRight configuration**: Enable accurate, real-time type checking in the editor, catching errors before running tests.

- **Editor extensions recommendations**: Suggest optimal VS Code extensions automatically, standardizing the development environment.

### AI Integration

- **AI assistance with common agents `Cursor, Windsurf, Claude Code, Codex`**: Support popular AI coding assistants enabling AI-powered development.

- **Cursor Rules configuration**: Optimize Cursor AI assistant for your specific project structure, improving suggestion relevance.

- **Windsurf Rules configuration**: Configure Windsurf IDE to understand your project architecture, enhancing code generation quality.

Start your next Python project with confidence, knowing you're building on a foundation of best practices and modern development tools.

## Full documentation on ReadTheDocs including how to run
- [py-launch-blueprint Docs](https://py-launch-blueprint.readthedocs.io/en/latest/)
