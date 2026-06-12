# Type Checking with ty and Pyright

Type checking is an essential part of maintaining a robust and error-free codebase. ty and Pyright are both static type checkers for Python that help you ensure your code adheres to specified type annotations.

## Setting Up ty

ty is already part of the project's dev dependency group, so it is installed by `uv sync --group dev`. To use it:

1. **Install dev dependencies** (if you haven't already):

   ```bash
   uv sync --group dev
   ```

2. **Configure ty**:
   ty works with sensible defaults out of the box; project-level options go in the `[tool.ty]` section of [`pyproject.toml`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/pyproject.toml) if needed.

3. **Run ty**:
   To check your code with ty, run the following command:
   ```bash
   uv run ty check src/py_launch_blueprint/
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
   check the `[tool.pyright]` section of [`pyproject.toml`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/pyproject.toml)
3. **Run Pyright**:
   To check your code with Pyright, run the following command:
   ```bash
   uvx --with-editable . pyright src/py_launch_blueprint/
   ```


## Best Practices for Type Checking

- **Annotate All Functions**: Ensure all functions have type annotations for their parameters and return types.
- **Use Type Hints**: Utilize Python's built-in type hints (e.g., `list`, `dict`, `X | None`) to specify the expected types.
- **Avoid `Any`**: Minimize the use of the `Any` type to maintain strict type checking.
- **Leverage `TypedDict`**: Use `TypedDict` for dictionaries with a fixed set of keys and value types.
- **Check Third-Party Libraries**: Ensure third-party libraries used in your project have type stubs available.

## Common Issues and Solutions

1. **Missing Type Annotations**:

   - **Issue**: ty/Pyright reports missing type annotations for functions.
   - **Solution**: Add type annotations to all function parameters and return types.

2. **Incompatible Types**:

   - **Issue**: ty/Pyright reports incompatible types in assignments or function calls.
   - **Solution**: Ensure the types of variables and function arguments match the expected types.

3. **Ignoring Errors**:

   - **Issue**: ty/Pyright reports errors that you want to ignore.
   - **Solution**: Use suppression comments to silence specific errors, but use them sparingly.

   ```python
      # ty (rule-specific) — also honors plain `# type: ignore`
      x = something()  # ty: ignore[unresolved-attribute]

      # pyright
      x = something()  # pyright: ignore
   ```

4. **Third-Party Libraries**:

   - **Issue**: ty/Pyright reports missing type stubs for third-party libraries.
   - **Solution**: Install type stubs for the libraries using `uv add --group dev types-<library>`.

5. **Type checking only specific files**:

   - **Issue**: You want to run ty/Pyright on specific files or directories.
   - **Solution**: Specify the files or directories to check as arguments to the ty/Pyright command.

   ```bash
   # ty
   uv run ty check src/main.py src/utils.py

   # pyright
   pyright src/main.py src/utils.py
   ```
  By following these best practices and addressing common issues, you can effectively use ty and Pyright to maintain a type-safe and reliable codebase.
Read more about [ty](../tools/ty.md)
