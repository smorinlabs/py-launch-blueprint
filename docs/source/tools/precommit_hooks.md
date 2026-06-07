## Precommit hooks

Hooks are designed to maintain clean, consistent, and error-free code and configuration files. They save time by catching issues before they make it into your repository.

Following pre-commit hooks are used in this repo

- `check-yaml` checks if all YAML files in your repository are valid,
- `end-of-file-fixer` ensures every file in your repository ends with a single newline character,
- `trailing-whitespace` removes trailing spaces at the end of lines in your files,
- `check-toml` checks if all TOML files in your repository are valid,
- `check-added-large-files` warns when you try to add large files to the repository,
- `mypy` checks your Python code for type errors based on type annotations,
- `ruff` acts as a fast linter and formatter for Python, ensuring clean code,
