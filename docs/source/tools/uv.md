# UV Package Manager

UV is a fast Python package manager that provides efficient dependency management. This guide covers how to set up and use UV in the *Py Launch Blueprint* project.

## Installation

To install UV, run:

```bash
pip install uv
```

Alternatively, this project's root `Makefile` provides convenient targets for installing and force-installing `uv`:

```bash
make install-uv
make install-uv-force
```
Refer to the [Makefiles documentation](./makefiles.md) for more details on these `make` commands, especially if you prefer a project-standardized installation method or encounter issues with other methods.

## Using UV for Dependency Management

### Installing Dependencies

To install dependencies from `pyproject.toml`, use:

```bash
uv pip install -r requirements.txt
```

Or, if using `pyproject.toml`:

```bash
uv pip install
```

### Adding a Package

To install a package and add it to your dependencies:

```bash
uv pip install <package-name>
```

### Removing a Package

To uninstall a package:

```bash
uv pip uninstall <package-name>
```

### Creating a Lockfile

To generate a lockfile (`requirements.lock`), run:

```bash
uv pip freeze > requirements.lock
```

## Additional Resources

For more details, check the [official UV documentation](https://github.com/astral-sh/uv).
