# Using the Justfile

This project includes a [`Justfile`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/Justfile) that defines useful commands for common development tasks. [Just](https://github.com/casey/just) is a simple command runner that helps standardize commands across your project.

To use these commands, first [install Just](https://github.com/casey/just#installation). Alternatively, this project's root `Makefile` is the Level 1 bootstrap — it installs `just` (and `uv`) for you:

```bash
make bootstrap
```
Refer to the [Makefiles documentation](./makefiles.md) for more details on these `make` commands.

Once `just` is installed, you can view all available commands by running:

```bash
just --list
```
Here are some commonly used commands (this is just a subset of all available commands):

```bash
# Setup your development environment
just setup

# Format code (includes ruff format and import sorting)
just format

# Run linter (code style and quality checks)
just lint

# Run type checker
just typecheck

# Run tests
just test

# Run all checks (tests, linting, and type checking)
just check

# Check installed package version
just version

# Clean up temporary files and caches
just clean

# Set up pre-commit hooks
just pre-commit-setup

# Build the package
just build

# Install in development mode
just install-dev
```

The Justfile standardizes common development tasks and provides a consistent interface for running them.

For a full list of available commands, refer to [this guide](../reference/cli_reference.md).

## Editing conventions

When adding or changing recipes in the `Justfile` (formerly enforced via a
Windsurf rule file; recorded here as the durable home):

- Leave a blank line between recipes.
- Every recipe belongs to a `[group('…')]` that already exists in the file —
  don't invent new groups casually.
- Document each recipe with a comment on the line directly above it (this is
  what `just --list` displays).

```text
# Format code
[group('dev')]
@format:
    echo "Running formatters..."
    uvx --with-editable . ruff format {{py_package_path}}/
    uvx --with-editable . ruff check --select I --fix {{py_package_path}}/

alias f := format
```
