# Command-Line Interface (CLI) Commands

This section provides an overview of the available commands in the Py Launch Blueprint CLI. These commands enable you to perform various tasks directly from the command line, such as running the project, managing dependencies, and ensuring code quality.

## Overview

The CLI includes a variety of commands to streamline development and project management. Each command is designed to handle specific tasks efficiently, making it easier to interact with the project.

---

## 1. Running the Project

### `run`
Run the main application.

#### Usage
```bash
just run [cmd] [args]
```

#### Arguments
- `cmd`: The command to run (default: `plbp`).
- `args`: Arguments to pass to the command.

---

## 2. Code Quality and Testing

### `check`
Perform code quality checks, including linting, type checking, and testing.

#### Usage
```bash
just check
```

### `lint`
Run the linter and check for code style violations.

#### Usage
```bash
just lint
```

### `format`
Format the code using the configured code formatter.

#### Usage
```bash
just format
```

### `typecheck`
Run the type checker.

#### Usage
```bash
just typecheck
```

### `test`
Run the tests.

#### Usage
```bash
just test [OPTIONS]
```

#### Options
- `options`: Additional pytest options.

---

## 3. Dependency Management

### `setup`
One-command project setup (Level 2). Verifies the base toolchain via the
Makefile's `make check` (Level 1 — run `make bootstrap` first on a bare
machine), syncs the dev environment, wires lefthook git hooks, and installs
the hook toolchain (bun, gitleaks, taplo, yamlfmt). Idempotent.

#### Usage
```bash
just setup
```

### `install-dev`
Install the package in editable mode with dev dependencies.

#### Usage
```bash
just install-dev
```

---

## 4. Documentation Management

Docs recipes run Sphinx via `uv run --group docs`, which installs the `docs`
dependency group on demand — there is no separate install step.

### `init-docs`
Initialize documentation (use only for new projects).

#### Usage
```bash
just init-docs
```

### `docs-help`
Show the available Sphinx build targets.

#### Usage
```bash
just docs-help
```

### `docs`
Build the documentation in the specified format (default is HTML).

#### Usage
```bash
just docs [target]
```

#### Arguments
- `target`: Specify the build target (e.g., `html`, `latexpdf`). Defaults to `html`.

### `docs-dev`
Run a documentation server with hot reloading for development purposes.

#### Usage
```bash
just docs-dev
```

### `docs-clean`
Clean the documentation build files.

#### Usage
```bash
just docs-clean
```

---

## 5. Development Tools

### `pre-commit-setup`
Set up pre-commit hooks.

#### Usage
```bash
just pre-commit-setup
```

### `pre-commit-run`
Run all pre-commit hooks.

#### Usage
```bash
just pre-commit-run
```

### `contributors`
Update `CONTRIBUTORS.md` file.

#### Usage
```bash
just contributors
```

---

## 6. Build and Package Management

### `build`
Build the package.

#### Usage
```bash
just build
```

---

## 7. Utility Commands

### `version`
Check installed package version.

#### Usage
```bash
just version
```

### `clean`
Clean up temporary files and caches.

#### Usage
```bash
just clean
```
