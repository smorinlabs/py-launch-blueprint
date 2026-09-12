# Application documentation

This application was generated from a template. Begin with
[development setup](tasks/setting_up_development.md), then use the CLI reference
and [web documentation](web/index.md) for the provided interfaces.
Repository and external-service configuration lives in `docs/PROJECT_SETUP.md`.
Source-template provenance is recorded in `press/press-receipt.toml`.

Run `just setup` to install the development environment and hooks, `just check`
to validate the project, and `uv build` to build its distributions. The command
name is defined in `pyproject.toml` under `[project.scripts]`.

## Documentation

```{toctree}
---
maxdepth: 3
---
about/index
tasks/index
tools/index
tutorials/index
web/index
reference/index
contributing/index
github-templates
```
