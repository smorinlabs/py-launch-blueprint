# Using the Justfile

This project includes a [`Justfile`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/Justfile) that defines useful commands for common development tasks. [Just](https://github.com/casey/just) is a simple command runner that helps standardize commands across your project.

To use these commands, first [install Just](https://github.com/casey/just#installation). Alternatively, this project's root `Makefile` provides convenient targets for installing and force-installing `just`:

```bash
make install-just
make install-just-force
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
