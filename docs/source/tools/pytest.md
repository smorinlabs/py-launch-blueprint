# Pytest Test Framework

Pytest is a powerful and flexible testing framework for Python. It simplifies writing and running tests, making it an essential tool for ensuring code quality.

## Installation

To install Pytest, use `uv`:

```bash
uv pip install pytest
```

## Basic Usage

1.  **Create Test Files**:

    - Tests are typically placed in a `tests/` directory.
    - Test file names should start with `test_` or end with `_test.py`.
    - Test functions should start with `test_`.

2.  **Write Tests**:

    - Use `assert` statements to verify expected behavior.

    ```python
    # tests/test_example.py
    def add(a, b):
        return a + b

    def test_add():
        assert add(2, 3) == 5
        assert add(-1, 1) == 0
        assert add(0, 0) == 0
    ```

3.  **Run Tests**:

    - Navigate to the project root directory.
    - Run `uvx pytest` or just `pytest` if your virtual environment is activated.

    ```bash
    uvx pytest
    ```

## Key Features

- **Simple Assertions**: Use standard `assert` statements for test conditions.
- **Test Discovery**: Automatically finds test files and functions.
- **Fixtures**: Define reusable test components.
- **Parametrization**: Run the same test with multiple inputs.
- **Plugins**: Extend functionality with a wide range of plugins.

## Configuration

Pytest can be configured using a `pytest.ini`, `pyproject.toml`, or `tox.ini` file. Here’s an example `pyproject.toml` configuration:

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- **`testpaths`**: Specifies the directories to search for tests.
- **`python_files`**: Specifies the file naming pattern for test files.

## Fixtures

Fixtures are functions that provide a fixed baseline for tests. They are used to set up and tear down resources, such as database connections or temporary files.

```python
import pytest

@pytest.fixture
def temp_file(tmp_path):
    file = tmp_path / "tempfile.txt"
    file.write_text("Hello, Pytest!")
    return file

def test_file_content(temp_file):
    assert temp_file.read_text() == "Hello, Pytest!"
```

## Best Practices

- **Keep Tests Isolated**: Each test should be independent and not rely on the state of other tests.
- **Use Descriptive Names**: Test function names should clearly describe what is being tested.
- **Test Edge Cases**: Include tests for boundary conditions and error handling.
- **Use Fixtures Wisely**: Use fixtures to reduce code duplication and improve test readability.
- **Follow the Arrange-Act-Assert Pattern**:
  - **Arrange**: Set up the test environment and prepare the inputs.
  - **Act**: Execute the code being tested.
  - **Assert**: Verify the expected results.

## Troubleshooting

- **Tests Not Being Discovered**:
  - Ensure test files and functions follow the naming conventions.
  - Check the `testpaths` and `python_files` settings in `pyproject.toml`.
- **Import Errors**:
  - Make sure your project is installed in editable mode (`uv pip install --editable .`).
  - Verify that your virtual environment is activated.

By following these guidelines, you can effectively use Pytest to write and run tests, ensuring the reliability and quality of your Python code.
