# Configuration Files

This section provides detailed information about the configuration files used in the Py Launch Blueprint project. Understanding these configuration files will help you customize and extend the project to fit your specific needs.

## pyproject.toml

The `pyproject.toml` file is the central configuration file for the project. It contains metadata about the project, dependencies, and tool-specific configurations. See [pyproject.toml](https://github.com/smorinlabs/py-launch-blueprint/blob/main/pyproject.toml) file for more details.

## .pre-commit-config.yaml

The `.pre-commit-config.yaml` file is used to configure pre-commit hooks. These hooks run code quality checks before commits, ensuring that only clean and consistent code is committed. See [pre-commit-config.yaml](https://github.com/smorinlabs/py-launch-blueprint/blob/main/.pre-commit-config.yaml) file for more details.

## [tool.pyright] (in pyproject.toml)

The `[tool.pyright]` section of `pyproject.toml` configures the Pyright static type checker. It specifies settings such as included and excluded directories, defined constants, the Python version to target, and various reporting options for type-related issues. This section allows you to customize how strictly Pyright checks your code for type errors. See [pyproject.toml](https://github.com/smorinlabs/py-launch-blueprint/blob/main/pyproject.toml) for more details.

## cog.toml

The `cog.toml` file configures the `cog` tool, which is used to generate changelog content locally and validate changelog generation in CI. It defines settings such as:

- **Changelog Path**: Defines the generated changelog file.
- **Remote Links**: Links changelog entries to the GitHub repository.
- **Author Mapping**: Maps local git signatures to GitHub usernames for changelog links.

Contributor list updates are handled by `smorinlabs/contributors-please-action` and `.contributors.yml`; `cog.toml` is only used for changelog generation.
