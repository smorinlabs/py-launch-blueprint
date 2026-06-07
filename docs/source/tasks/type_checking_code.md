# Type Checking with MyPy and Pyright

Type checking is an essential part of maintaining a robust and error-free codebase. MyPy and Pyright are both static type checkers for Python that help you ensure your code adheres to specified type annotations.

## Setting Up MyPy

To set up MyPy for your project, follow these steps:

1. **Install MyPy**:

   ```bash
   uv pip install mypy
   ```

2. **Configure MyPy**:
   check in the [`pyproject.toml`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/pyproject.toml) file the [tool.mypy] section

3. **Run MyPy**:
   To check your code with MyPy, run the following command:
   ```bash
   uvx --with-editable . mypy py_launch_blueprint/
   ```
   or
   ```bash
   just typecheck
   ```

## Setting Up Pyright

To set up Pyright for your project, follow these steps:

1. **Install Pyright**:

   ```bash
   uv pip install pyright
   ```

2. **Configure Pyright**:
   check [`pyrightconfig.json`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/pyrightconfig.json) file in the root of the project
3. **Run Pyright**:
   To check your code with Pyright, run the following command:
   ```bash
   uvx --with-editable . pyright py_launch_blueprint/
   ```


## Best Practices for Type Checking

- **Annotate All Functions**: Ensure all functions have type annotations for their parameters and return types.
- **Use Type Hints**: Utilize Python's built-in type hints (e.g., `List`, `Dict`, `Optional`) to specify the expected types.
- **Avoid `Any`**: Minimize the use of the `Any` type to maintain strict type checking.
- **Leverage `TypedDict`**: Use `TypedDict` for dictionaries with a fixed set of keys and value types.
- **Check Third-Party Libraries**: Ensure third-party libraries used in your project have type stubs available.

## Common Issues and Solutions

1. **Missing Type Annotations**:

   - **Issue**: MyPy/Pyright reports missing type annotations for functions.
   - **Solution**: Add type annotations to all function parameters and return types.

2. **Incompatible Types**:

   - **Issue**: MyPy/Pyright reports incompatible types in assignments or function calls.
   - **Solution**: Ensure the types of variables and function arguments match the expected types.

3. **Ignoring Errors**:

   - **Issue**: MyPy/Pyright reports errors that you want to ignore.
   - **Solution**: Use `# type: ignore` comments to suppress specific errors, but use them sparingly.

   ```python
      # mypy
      reveal_type(x)  # type: ignore

      # pyright
      x = something()  # pyright: ignore
   ```

4. **Third-Party Libraries**:

   - **Issue**: MyPy/Pyright reports missing type stubs for third-party libraries.
   - **Solution**: Install type stubs for the libraries using `uv pip install types-<library>`.

5. **Type checking only specific files**:

   - **Issue**: You want to run MyPy/Pyright on specific files or directories.
   - **Solution**: Specify the files or directories to check as arguments to the MyPy/Pyright command.

   ```bash
   # mypy
   mypy src/main.py src/utils.py

   # pyright
   pyright src/main.py src/utils.py
   ```
  By following these best practices and addressing common issues, you can effectively use MyPy and Pyright to maintain a type-safe and reliable codebase.
Read more about [mypy](../tools/mypy.md)
