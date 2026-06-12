# Project Structure

The Py Launch Blueprint project follows a modular and organized directory layout to ensure maintainability and scalability. This section provides an overview of the directory structure and the purpose of each directory and file.

## Directory Layout

The project is organized into the following directories:

```
py-launch-blueprint/
├── tests/                          # Test files
├── docs/                           # Documentation files
├── Justfile                        # Just task runner configuration
├── Makefile                        # Makefile for building the project
└── src/py_launch_blueprint/        # Source code for the project
```

Detailed version of the project structure:


```
py-launch-blueprint/
├── .github/                        # GitHub configuration files
│   ├── ISSUE_TEMPLATE/             # Issue templates
│   ├── PULL_REQUEST_TEMPLATE       # Pull request templates
│   └── workflows/                  # GitHub Actions workflows
├── docs/                           # Documentation files
│   ├── source/                     # Sphinx source files
│   │   ├── _static/                # Static assets (CSS, images)
│   │   ├── _templates/             # Sphinx template overrides
│   │   ├── about/                  # Project context and philosophy
│   │   ├── tasks/                  # Step-by-step workflows
│   │   ├── tools/                  # Technical tooling reference
│   │   ├── tutorials/              # Guided learning paths
│   │   ├── reference/              # Technical references
│   │   └── contributing/           # Contribution guidelines
│   └── build/                      # Built documentation files
├── src/py_launch_blueprint/        # Source code for the project
│   ├── __init__.py                 # Package initialization
│   ├── cli/                        # Click CLI (thin presentation layer)
│   ├── core/                       # Library: logic + Pydantic models
│   └── web/                        # FastAPI web service (behind the `web` extra)
├── tests/                          # Test files
│   ├── __init__.py                 # Test package initialization
│   ├── cli/                        # CLI tests
│   └── core/                       # Library tests
├── .flox/                          # Flox environment (optional toolchain provisioner; ADR 0005)
│   └── env/manifest.toml           # Declares the 10-tool dev set for `flox activate`
├── .gitignore                      # Git ignore file
├── .pre-commit-config.yaml         # Pre-commit hooks configuration
├── .python-version                 # Python version file
├── .readthedocs.yaml               # Read the Docs configuration
├── .vscode/                        # VS Code configuration files
│   └── extensions.json             # Recommended extensions
├── CLAUDE.md                       # CLAUDE documentation
├── CODE_OF_CONDUCT.md              # Code of conduct
├── CONTRIBUTING.md                 # Contributing guidelines
├── docs/                           # Documentation files
│   ├── cla_faq.md                  # CLA FAQ
│   ├── cla/                        # CLA files
│   │   ├── corporate_cla.md        # Corporate CLA
│   │   └── individual_cla.md       # Individual CLA
│   ├── Makefile                    # Makefile for building documentation
│   ├── source/                     # Sphinx source files
│   │   ├── _templates/             # Sphinx template overrides
│   │   ├── about/                  # Project context and philosophy
│   │   ├── tasks/                  # Step-by-step workflows
│   │   ├── tools/                  # Technical tooling reference
│   │   ├── tutorials/              # Guided learning paths
│   │   ├── reference/              # Technical references
│   │   └── contributing/           # Contribution guidelines
│   └── build/                      # Built documentation files
├── EXAMPLECLI.md                   # Example CLI documentation
├── EXAMPLEWEB.md                   # Example web service documentation
├── Justfile                        # Just task runner configuration
├── Makefile                        # Makefile for building the project
├── mise.toml                       # mise toolchain (optional provisioner; ADR 0005)
├── PULL_REQUEST_TEMPLATE.md        # Pull request template
├── src/py_launch_blueprint/        # Source code for the project
│   ├── __init__.py                 # Package initialization
│   ├── cli/                        # Click CLI (thin presentation layer)
│   ├── core/                       # Library: logic + Pydantic models
│   └── web/                        # FastAPI web service (behind the `web` extra)
├── pyproject.toml                  # Project configuration file
├── cog.toml                        # Cog configuration file
├── CONTRIBUTORS.md                 # Project contributors
├── README.md                       # Project overview and navigation
├── SECURITY.md                     # Security policy
└── tests/                          # Test files
    ├── __init__.py                 # Test package initialization
    ├── cli/                        # CLI tests
    └── core/                       # Library tests
```

## Directory Descriptions

### .github/

Contains GitHub-specific configuration files, including GitHub Actions workflows and issue templates.

### docs/

Contains all documentation files, including Sphinx source files, static assets, and built documentation.

### src/py_launch_blueprint/

Contains the source code for the project, organized into the `cli/`, `core/`, and `web/` layers.

### tests/

Contains test files for the project, organized under `tests/cli/`, `tests/core/`, and `tests/web/`.

### .gitignore

Specifies files and directories to be ignored by Git.

### .pre-commit-config.yaml

Configuration file for pre-commit hooks to ensure code quality and consistency.

### .python-version

Specifies the Python version used for the project.

### .readthedocs.yaml

Configuration file for Read the Docs to build and host the documentation.

### .vscode/

Contains VS Code-specific configuration files, including recommended extensions.

### CLAUDE.md

Contains documentation for the CLAUDE tool.

### CODE_OF_CONDUCT.md

Specifies the code of conduct for contributors to the project.

### CONTRIBUTING.md

Provides guidelines for contributing to the project.

### EXAMPLECLI.md

Contains documentation for the example CLI tool.

### EXAMPLEWEB.md

Contains documentation for the example FastAPI web service (the `web` extra).

### Justfile

Configuration file for the Just task runner to manage development tasks.

### Makefile

Contains build instructions for the project.

### PULL_REQUEST_TEMPLATE.md

Template for pull requests to ensure consistency and completeness.

### pyproject.toml

Configuration file for the project, including dependencies and build settings.

### cog.toml
Configuration file for COG (Cocogitto), used for changelog generation.

### CONTRIBUTORS.md
Auto-generated file that lists the project contributors.

### README.md

Provides an overview of the project and serves as a navigation hub for the documentation.

### SECURITY.md

Specifies the security policy for the project.
