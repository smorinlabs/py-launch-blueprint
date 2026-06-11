# GitHub Actions

## Setup

GitHub Actions automates testing and deployment. The Py Launch Blueprint project includes a pre-configured workflows in [`.github/workflows/`](https://github.com/smorinlabs/py-launch-blueprint/tree/main/.github/workflows).

## Workflow Configuration

The workflow runs on every push or pull request to `main`:

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --all-extras --dev
      - run: uv run ty check src/py_launch_blueprint/
      - run: uvx ruff check py_launch_blueprint/
```

## Best Practices

- **Keep It Simple**: Start small and expand as needed.
- **Use Matrix Builds**: Test across multiple Python versions.
- **Cache Dependencies**: Speed up workflows by caching dependencies.
- **Fail Fast**: Identify and fix issues quickly.
- **Monitor Regularly**: Ensure workflows run efficiently.

[Actions documentation](https://docs.github.com/en/actions) for more details.
