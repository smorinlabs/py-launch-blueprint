# Application setup

This guide prepares this application's development environment, checks the
installation, and builds its distribution files. Run the commands from the
repository root.

## Set up the development environment

Use Python 3.13 or later, `uv`, and `just`. If `uv` or `just` is missing, run
`make bootstrap` first. See [development setup](../tasks/setting_up_development.md)
for alternative toolchain provisioning options.

```bash
just setup
```

This installs the locked development dependencies, the optional web dependencies,
and the Git hook toolchain. Run it for each fresh clone or development environment.

## Verify the application

```bash
just check
```

The checks cover tests, linting, types, import boundaries, and repository quality
rules. A successful run exits with no failed checks.

Use the [CLI reference](../reference/cli_reference.md) to run the application
from a terminal. Its command name is listed in `pyproject.toml` under
`[project.scripts]`. The [web documentation](../web/index.md) explains how to
start and check the optional web interface.

## Build distribution files

```bash
uv build
```

The wheel and source distribution are written to `dist/`.

## Configure repository services

Use `docs/PROJECT_SETUP.md` in this repository to configure releases, publishing,
and optional services. Complete the relevant configuration before enabling a
service that needs credentials.
