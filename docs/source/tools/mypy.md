## Mypy

This project uses both Mypy and pyright/Pylance for type checking:

- **Mypy** is used in CI and pre-commit hooks for strict type checking.
- **Pylance** is used in VS Code for real-time feedback during development.

### About Mypy
[Mypy](http://mypy-lang.org/) is a static type checker for Python that allows you to add type annotations to your Python code. It checks whether your code adheres to these type annotations and helps you catch errors early. Mypy is especially useful in large codebases where manually reviewing every line for type correctness can be cumbersome. It can be integrated into CI pipelines to automatically check for type issues before code is merged.

This combination of Mypy and Pylance ensures comprehensive type checking while maintaining a smooth development experience.

### Difference Between `disallow_untyped_defs = false` vs `true`

**disallow_untyped_defs = true**
```python
# This will raise an error
def process_data(data):  # Error: Function is missing type annotations
    return data + 1

# This is required instead
def process_data(data: int) -> int:
    return data + 1
```

**disallow_untyped_defs = false**
```python
# This is allowed
def process_data(data):
    return data + 1

# This is also allowed
def process_data(data: int) -> int:
    return data + 1
```

### When to Use Each

- **Use `true` when**:
  - Starting a new project.
  - Working on a codebase fully committed to type hints.
  - Ensuring complete type coverage.
  - Your team is comfortable with Python type hints.

- **Use `false` when**:
  - Gradually adding types to a legacy codebase.
  - Working with test files (commonly disabled for tests).
  - Training team members new to type hints.
  - Temporarily bypassing type checking for specific modules.

### Best Practice Recommendation

- Start new projects with `true` for maximum type safety.
- For existing projects, use `false` initially and gradually enable it as type hints are added.
- Many teams set it to `false` for test files but `true` for production code.

### VS Code Settings for pyright/Pylance

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

### Common Type Annotation Examples

```python
from typing import Dict, List, Optional, Tuple, Union, TypeVar, Generic

# Basic type annotations
def greet(name: str) -> str:
    return f"Hello {name}"

# Optional parameters
def fetch_user(user_id: Optional[int] = None) -> Dict[str, Union[str, int]]:
    ...

# Generic types
T = TypeVar('T')
class Stack(Generic[T]):
    def __init__(self) -> None:
        self.items: List[T] = []

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T:
        return self.items.pop()

# Type aliases
UserId = int
UserDict = Dict[UserId, Dict[str, Union[str, int]]]

# Callable types
from typing import Callable
Handler = Callable[[str, int], bool]

def process(handler: Handler) -> None:
    ...
```

## Python Types Common Issues and Solutions
1. Third-party library types:
```bash
# Install type stubs for common libraries
pip install types-requests types-PyYAML types-python-dateutil
```

2. Ignoring specific lines:
```python
# mypy
reveal_type(x)  # type: ignore

# pyright
x = something()  # pyright: ignore
```

3. Type checking only specific files:
```bash
# mypy
mypy src/main.py src/utils.py

# pyright
pyright src/main.py src/utils.py
```

disallow_untyped_defs = true vs false
- Use `true` when starting new projects or working with teams experienced in type hints who want complete type coverage.
- Use `false` when adding types to legacy code, working with test files, or training developers new to type hints.

disallow_untyped_defs = true
```python
# This will raise an error
def process_data(data):  # Error: Function is missing type annotations
    return data + 1

# This is required instead
def process_data(data: int) -> int:
    return data + 1
```

disallow_untyped_defs = false
```python
# This is allowed
def process_data(data):
    return data + 1

# This is also allowed
def process_data(data: int) -> int:
    return data + 1
```
