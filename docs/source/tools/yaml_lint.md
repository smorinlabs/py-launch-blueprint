# YAML Formatting and Linting

## Introduction
Our project uses YAML files extensively for configuration, GitHub Actions workflows, and issue templates. To ensure consistent formatting and catch syntax/style issues early, we use `yamlfmt` for formatting and `yamllint` for validation.

---

**Key Benefits**:
* ✅ **Separated responsibilities**: `yamlfmt` formats YAML and `yamllint` catches syntax/style issues.
* 🎨 **Automatic Formatting**: Consistent YAML style across all files
* 🚀 **Fast Performance**: Go-based tool for speed and reliability
* 🔧 **Highly Configurable**: Customizable rules via `.yamlfmt` configuration
* 🤖 **Pre-commit Integration**: Runs automatically on every commit
* 💻 **No Node.js Required**: Pure Go binary, simpler dependency management
* 🛡️ **GitHub Actions Compatible**: Tested with workflow files

---

## ⚙️ Getting Started

### Prerequisites
Install Go and yamlfmt:
```bash
# Install Go (if not already installed)
just install-go

# Install yamlfmt
just install-yamlfmt

```

---

## Usage

### **Format all YAML files:**
```bash
just format-yaml
```
*Automatically fixes formatting in all `.yml` and `.yaml` files*

### **Check for YAML lint issues:**
```bash
just lint-yaml
```
*Shows detailed output of any lint problems*

### **Verify formatting is clean:**
```bash
just check-yaml
```
*Quick pass/fail lint check with success message*

---

## 🛠 Configuration

### yamlfmt Configuration (`.yamlfmt`)

### yamllint Configuration (`.yamllint`)

---

## 🔄 Pre-commit Integration

YAML formatting runs automatically on every commit via `pre-commit`:

- The `yamlfmt` hook formats `.yaml` and `.yml` files automatically.
- The `yamllint` hook validates `.yaml` and `.yml` files automatically.
- Prevents commits with YAML syntax/style errors.
- Ensures codebase consistency and reduces manual reviews.

Example `.pre-commit-config.yaml` snippet for YAML linting:

```yaml
repos:
  - repo: https://github.com/google/yamlfmt
    rev: v0.13.0
    hooks:
      - id: yamlfmt
        name: "Format YAML files"
        files: \.ya?ml$
  - repo: local
    hooks:
      - id: yamllint
        name: Lint YAML files
        entry: uvx yamllint -c .yamllint .
        language: system
        pass_filenames: false
```

---

## 🛑 Disabling or Skipping YAML Linting

- To skip linting temporarily, use the `--no-verify` flag on `git commit`.
- To disable formatting rules, edit `.yamlfmt`.
- To disable lint rules, edit `.yamllint`.
- To remove linting completely, remove related pre-commit hooks and `just` commands.

---

## 📚 References

* [📘 yamlfmt GitHub Repository](https://github.com/google/yamlfmt)
* [🛠 yamlfmt Configuration Options](https://github.com/google/yamlfmt#configuration)
* [🔧 Our yamlfmt Configuration](.yamlfmt)
* [🔧 yamllint Documentation](https://yamllint.readthedocs.io/)
* [🚀 Pre-commit Integration](https://pre-commit.com/)
