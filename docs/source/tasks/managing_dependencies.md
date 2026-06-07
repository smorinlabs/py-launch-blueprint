# Managing Dependencies with UV and Pip

## Using UV
[UV](https://github.com/astral-sh/uv) is a fast Python package manager for efficient dependency management.

### Installation
To install UV, run the following command:

```sh
pip install uv
```

### Installing Dependencies
To install project dependencies in editable mode, use:

```sh
uv pip install --editable ".[dev]"
```

### Development Tools
Use UV to run various development tools:

```sh
uvx ruff format py_launch_blueprint/       # Format code
uvx ruff check py_launch_blueprint/        # Run linter
uvx --with-editable . mypy py_launch_blueprint/  # Type check
uvx --with-editable . pytest               # Run tests
uvx --with pytest-cov --with-editable . pytest --cov=py_launch_blueprint.projects --cov-report=term-missing  # Test coverage
```

### Pre-Commit Hooks (Optional)
Set up and run pre-commit hooks with:

```sh
uvx --with-editable . pre-commit install
uvx pre-commit run --all-files
```

### Updating & Removing Packages
To update all dependencies, use:

```sh
uv pip install --upgrade                    # Update all dependencies
uv pip install --upgrade <package-name>     # Update a specific package
uv pip uninstall <package-name>             # Remove a package
```

### Freezing Dependencies
To freeze the dependencies into a `requirements.lock` file:

```sh
uv pip freeze > requirements.lock
```

---

## Using Pip

### Virtual Environment Setup
To create and activate a virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate   # Unix/macOS
.venv\Scripts\activate      # Windows
```

### Installing Dependencies
Install project dependencies in editable mode:

```sh
pip install --editable ".[dev]"
```

### Running Tools
You can run development tools directly with pip:

```sh
ruff format py_launch_blueprint/
ruff check py_launch_blueprint/
mypy py_launch_blueprint/
pytest --cov=py_launch_blueprint.projects --cov-report=term-missing
```


For more details, refer to the official [UV documentation](https://github.com/astral-sh/uv).
