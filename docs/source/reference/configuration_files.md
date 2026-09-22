# Configuration Files

This section provides detailed information about the configuration files used in the Py Launch Blueprint project. Understanding these configuration files will help you customize and extend the project to fit your specific needs.

## pyproject.toml

The `pyproject.toml` file is the central configuration file for the project. It contains metadata about the project, dependencies, and tool-specific configurations. See [pyproject.toml](https://github.com/smorinlabs/py-launch-blueprint/blob/main/pyproject.toml) file for more details.

## lefthook.yml

The `lefthook.yml` file configures lefthook, the Git hooks manager used for pre-commit checks. These hooks run code quality checks before commits, ensuring that only clean and consistent code is committed. See [lefthook.yml](https://github.com/smorinlabs/py-launch-blueprint/blob/main/lefthook.yml) file for more details.

## [tool.pyright] (in pyproject.toml)

The `[tool.pyright]` section of `pyproject.toml` configures the Pyright static type checker. It specifies settings such as included and excluded directories, defined constants, the Python version to target, and various reporting options for type-related issues. This section allows you to customize how strictly Pyright checks your code for type errors. See [pyproject.toml](https://github.com/smorinlabs/py-launch-blueprint/blob/main/pyproject.toml) for more details.
