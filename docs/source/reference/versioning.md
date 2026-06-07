# Versioning and Release Management

This project uses explicit package version metadata in `pyproject.toml` and builds distributions with `uv_build`.

## Creating Releases

```bash
# Update pyproject.toml version first, then create an annotated matching tag.
git tag -a v0.0.1 -m "Release version 0.0.1"
git push --tags

# Verify version metadata.
uv run python -c "import py_launch_blueprint; print(py_launch_blueprint.__version__)"

# Build package artifacts.
uv build
```

## Daily Development

```bash
uv sync --all-extras --dev
uv run python -c "import py_launch_blueprint; print(py_launch_blueprint.__version__)"
uv build
```

## CI/CD Automation

The release workflow runs on `v*` tags and performs these checks:

1. Confirms the tag commit is reachable from `main`.
2. Compares the tag version with `project.version` in `pyproject.toml`.
3. Builds wheel and source distributions with `uv build`.
4. Uploads the immutable `dist/` artifact.
5. Publishes to TestPyPI, then PyPI, using Trusted Publishing.

Configure the `testpypi` and `pypi` GitHub environments as Trusted Publishers in the matching package indexes before using the publish jobs.

## Troubleshooting

- **Version mismatch in CI**: update `project.version` in `pyproject.toml` before tagging.
- **Build cannot find the package module**: check `[tool.uv.build-backend]` and keep `module-name = "py_launch_blueprint"` with `module-root = ""`.
- **Publishing fails with OIDC errors**: confirm the GitHub repository, workflow filename, environment, and package name match the Trusted Publishing settings in PyPI and TestPyPI.
