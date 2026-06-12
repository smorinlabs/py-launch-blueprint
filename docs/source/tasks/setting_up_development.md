# Setting Up Development

## Setup & Dependency Check

Run the following command to check if the base dependencies are installed.
```bash
make check
```

### (Optional) Provision the whole toolchain with mise or flox

Instead of installing each tool natively, you can provision the project's full
10-tool set (python, uv, ruff, taplo, gitleaks, just, bun, gh, lefthook, make)
with a single command — both manifests live at the repo root and are kept in
sync with the native installers (see
[ADR 0005](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0005-mise-flox-first-class-toolchains.md)):

```bash
# Option A: mise (https://mise.jdx.dev/) — reads mise.toml
curl https://mise.run | sh   # install mise itself, then:
mise install

# Option B: flox (https://flox.dev/) — reads .flox/
make install-flox            # prints platform-specific install instructions
flox activate
```

Note: yamllint, codespell, bandit, editorconfig-checker, and commitlint are
deliberately not in these manifests — they are fetched on demand via
`uvx`/`bunx` by the git hooks and Justfile recipes.

# Setup Development Environment

Project requires Python 3.12+ (which is also specified inside [.python-version](https://github.com/smorinlabs/py-launch-blueprint/blob/main/.python-version) file)
There are two options for setting up the development environment:

- Using [uv](https://docs.astral.sh/uv/getting-started/installation/):
- Using [pip](https://pip.pypa.io/en/stable/installation/):

It depends on the tool you choose, but both offer a convenient way to install the package in editable mode with development dependencies. UV is recommended as it offers much greater speed and a lot of features and tools out of the box.

## Using uv:

```bash
# This command creates a live development installation that allows you to modify the code without reinstalling while also installing additional development tools (like pytest, ty, etc.) specified in your project's dev dependencies.
uv pip install --editable ".[dev]"

# Format the code
uvx ruff format py_launch_blueprint/

# Run linter
uvx ruff check py_launch_blueprint/

# Run type checker
uv run ty check src/py_launch_blueprint/

# Run tests
uvx --with-editable . pytest

# Run tests with coverage
uvx --with pytest-cov --with-editable . pytest --cov=py_launch_blueprint --cov-report=term-missing

# Run command
uvx --from . plbp
```

### (Optional) Pre-Commit Hooks with uv

```bash
# Setup Pre-Commit Hook
uvx --with-editable . pre-commit install

#Run all pre-Commit Hooks
uvx pre-commit run --all-files
```

## Using pip:

```bash

# Create and activate a virtual environment if needed
python3 -m venv .venv
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate  # On Windows

# Install the package in editable mode with development dependencies
pip install --editable ".[dev]"

# Run development tools directly (no need for 'uv pip run')
ruff format py_launch_blueprint/
ruff check py_launch_blueprint/
ty check src/py_launch_blueprint/
pytest --cov=py_launch_blueprint --cov-report=term-missing

# Check the installed package cli tool version
plbp --version
```

### (Optional) Pre-Commit Hooks with pip

```bash
# Setup Pre-Commit Hook
pre-commit install

#Run all pre-Commit Hooks
pre-commit run --all-files
```

## Customization for New Projects

When using this workflow as a template for a new project, update the following:

1. **Project Name**:
   Replace `py_launch_blueprint` with your package name in the version verification step:

   ```yaml
   PY_VERSION=$(uv run python -c "import your_package_name; print(your_package_name.__version__)")
   ```

2. **Python Version**:
   Update the Python version to match your project's requirements:
   ```yaml
   with:
     python-version: "3.12" # Change to your required version
   ```
