# ty

This project uses both ty and pyright/Pylance for type checking (per
[ADR-03](https://github.com/smorinlabs/py-launch-blueprint/blob/main/docs/adr/README.md)):

- **ty** is used in CI and at the command line for strict type checking.
- **Pylance** is used in VS Code for real-time feedback during development.

## About ty
[ty](https://docs.astral.sh/ty/) is an extremely fast static type checker for
Python, written in Rust by [Astral](https://astral.sh/) (the makers of Ruff and
uv). It checks whether your code adheres to its type annotations and helps you
catch errors early — especially useful in large codebases where manually
reviewing every line for type correctness is cumbersome. Because it shares
Astral's toolchain philosophy with Ruff and uv, it runs fast enough to be part
of every check cycle, locally and in CI.

> **Note:** ty is pre-1.0; the pinned version in `pyproject.toml`
> (`[dependency-groups] dev`) is bumped as needed.

This combination of ty and Pylance ensures comprehensive type checking while
maintaining a smooth development experience.

## Running ty

```bash
just typecheck
```

or directly:

```bash
uv run ty check src/py_launch_blueprint/
```

## Suppressing diagnostics

Use suppression comments sparingly, and prefer fixing the type error:

```python
x = something()  # ty: ignore[possibly-unbound-attribute]

# type: ignore is also honored (PEP 484 style, suppresses all rules on the line)
y = other()  # type: ignore
```

## Third-party library stubs

ty consumes the same stub packages as other type checkers. Install stubs for
libraries that don't ship inline types:

```bash
uv add --group dev types-requests
```

## Type checking only specific files

```bash
uv run ty check src/py_launch_blueprint/cli/main.py
```

## VS Code Settings for pyright/Pylance

```json
{
    "python.analysis.typeCheckingMode": "strict",
    "python.analysis.diagnosticMode": "workspace",
    "python.analysis.autoImportCompletions": true,
    "python.analysis.importFormat": "relative",
    "python.analysis.inlayHints.functionReturnTypes": true,
    "python.analysis.inlayHints.variableTypes": true
}
```

## Common Type Annotation Examples

```python
from collections.abc import Callable
from typing import TypeVar, Generic

# Basic type annotations
def greet(name: str) -> str:
    return f"Hello {name}"

# Optional parameters
def fetch_user(user_id: int | None = None) -> dict[str, str | int]:
    ...

# Generic types
T = TypeVar('T')
class Stack(Generic[T]):
    def __init__(self) -> None:
        self.items: list[T] = []

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T:
        return self.items.pop()

# Type aliases
UserId = int
UserDict = dict[UserId, dict[str, str | int]]

# Callable types
Handler = Callable[[str, int], bool]

def process(handler: Handler) -> None:
    ...
```
