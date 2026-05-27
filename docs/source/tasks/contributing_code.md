# Contributing Code

 This section provides guidelines and best practices for contributing code to the project. By following these guidelines, you can ensure that your contributions are consistent, maintainable, and aligned with the project's goals.

## Code Style Guidelines

To ensure consistency and maintainability, please follow these code style guidelines when contributing to the project:

- **Line Length**: Limit lines to 88 characters.
- **Types**: Use strict typing for all functions.
- **Imports**: Sort imports and prefer relative imports.
- **Naming**: Follow PEP 8 naming conventions.
- **Errors**: Prefer explicit error handling over assertions.
- **Tests**: Type annotations are optional for test files.
- **Security**: Avoid hardcoded credentials and follow bandit rules.

## Development Workflow

1. **Fork the Repository**: Create a fork of the repository on GitHub.
2. **Clone the Repository**: Clone your forked repository to your local machine.
   ```bash
   git clone https://github.com/your-username/py-launch-blueprint.git
   cd py-launch-blueprint
   ```
3. **Create a Branch**: Create a new branch for your feature or bugfix.
   ```bash
   git checkout -b my-feature-branch
   ```
4. **Install Dependencies**: Install the project dependencies.
   ```bash
   uv pip install --editable ".[dev]"
   ```
5. **Make Changes**: Make your changes to the codebase.
6. **Run Tests**: Run the tests to ensure your changes do not break anything.
   ```bash
   just test
   ```
7. **Commit Changes**: Commit your changes with a clear and descriptive commit message using [Conventional Commits](https://www.conventionalcommits.org/) format.
   ```bash
   git add .
   git commit -m "Add feature X"
   ```
8. **Push Changes**: Push your changes to your forked repository.
   ```bash
   git push origin my-feature-branch
   ```

## Using the Justfile

This project includes a `Justfile` that provides convenient commands for common development tasks. [Just](https://github.com/casey/just) is a handy command runner that helps standardize commands across your project.

To use these commands, first [install Just](https://github.com/casey/just#installation). You can see all available commands by running:

```bash
just --list
```
see the [Justfile](../reference/cli_reference.md) for more details.

## Code Review Process

The code review process ensures that all contributions meet the project's quality standards. During the review process, maintainers will:

- Review the code for correctness, readability, and adherence to the code style guidelines.
- Provide feedback and request changes if necessary.
- Approve the pull request once all feedback has been addressed.

## Documentation Contributions

- All documentation resides in `docs/source/`.
- Follow the directory structure for consistency.
- Use Sphinx syntax for cross-referencing (e.g., `:doc:` or `:ref:`).

## Contributor License Agreement (CLA)

Before we can accept your contributions, you will need to sign a Contributor License Agreement (CLA). This is a legal document in which you state that you are entitled to contribute the code you are submitting and that you grant us the rights to use that contribution.

for more information, see the [Contributor License Agreement](../contributing/index.md#contributor-license-agreement-cla) page.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Contributors

This project includes a `just contributors` helper that invokes
`contributors-please` to bootstrap or refresh the local contributors list.

### Manual Update

To manually update the contributors list:

```bash
just contributors
```

### How Contributors are Tracked

Contributors are tracked based on git commit history. The system:
- Counts commits per contributor
- Shows contribution statistics
- Joins commit authors to GitHub logins using no-reply addresses and optional
  identity-map configuration
- Sorts contributors by number of commits
