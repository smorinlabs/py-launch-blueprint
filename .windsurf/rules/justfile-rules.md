---
trigger: glob
globs: Justfile
---

Ensure that there's proper spacing between recipes, a new line.

Every recipe is part of a group that already exists in the Just file, and that there is documentation which should be a comment right before the recipe.



```Justfile
# Install Taplo in editable mode with dev dependencies
[group('install')]
@install-taplo:
	if ! command -v taplo >/dev/null 2>&1; then \
		cargo install taplo-cli && echo "{{GREEN}} Taplo installed successfully{{NC}}" || \
		(echo "{{RED}}Failed to install taplo-cli.{{NC}} Try running '{{BLUE}}rustup update{{NC}}' to update your Rust toolchain." && exit 1); \
	else \
		echo "{{YELLOW}}Taplo is already installed{{NC}}"; \
	fi

# Format code
[group('dev')]
@format:
    echo "Running formatters..."
    echo "  ruff format"
    uvx --with-editable . ruff format {{py_package_name}}/
    echo "  ruff isort"
    uvx --with-editable . ruff check --select I --fix {{py_package_name}}/

alias f := format

```
