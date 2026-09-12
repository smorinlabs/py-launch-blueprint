# Setting Up Development

Run these commands from the repository root. The project requires Python 3.13
or later; `.python-version` selects the default interpreter.

## Check the base tools

```bash
make check
```

If `uv` or `just` is missing, install the base toolchain first:

```bash
make bootstrap
```

You can also use the [optional toolchain provisioning](#optional-toolchain-provisioning)
options below. After the base tools are available, continue with `just setup`.

## Set up the development environment

Run this for every fresh clone or development environment:

```bash
just setup
```

This syncs the locked development and web dependencies with
`uv sync --locked --group dev --extra web`, installs the hook toolchain, and
wires Lefthook's Git hooks. It also installs commitlint's dependencies with
`bun install --frozen-lockfile`.

Development dependencies are the `dev` dependency group in `pyproject.toml`,
not an optional package extra. Dependency sync alone does not install the Git
hooks; use `just setup` before committing or pushing.

## Verify the installation

```bash
just check
uv run --locked plbp --version
```

`just check` runs the tests, lint and format checks, type checks, import
boundaries, spelling, YAML, and EditorConfig checks. Both commands must exit
successfully. Use the [CLI reference](../reference/cli_reference.md) and
[web documentation](../web/index.md) for the application interfaces.

For individual checks, use the locked environment:

```bash
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked --extra web ty check src/py_launch_blueprint/
uv run --locked --extra web pytest
```

## Optional toolchain provisioning

The repository's `mise.toml` and `.flox/` manifests provision the same native
toolchain as the installers. See
[ADR 0005](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/0005-mise-flox-first-class-toolchains.md)
for the supported tools.

With mise installed, run:

```bash
mise install
```

For Flox:

```bash
make install-flox
flox activate
```

After activating either toolchain, run `just setup` to sync Python dependencies,
install commitlint's dependencies, and wire Git hooks. Python quality tools come
from the locked `dev` dependency group and run through `uv run --locked`.
