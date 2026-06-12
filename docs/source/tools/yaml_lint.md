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
Install yamlfmt (downloads the pre-built binary; no Go toolchain needed):
```bash
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

## 🔄 Git Hook Integration (lefthook)

Git hooks are managed by [lefthook](https://lefthook.dev/) (`lefthook.yml`), not
the Python `pre-commit` framework. YAML *linting* runs automatically on staged
files at commit time; YAML *formatting* is a manual step.

- The `yamllint` pre-commit hook validates staged `.yaml`/`.yml` files on every
  commit and blocks commits with syntax/style errors.
- `yamlfmt` formatting is **not** wired into a hook — run it on demand with
  `just format-yaml` (or `yamlfmt .`).

The relevant `lefthook.yml` entry:

```yaml
pre-commit:
  commands:
    yamllint:
      glob: "*.{yml,yaml}"
      run: uv run yamllint -c .yamllint {staged_files}
```

---

## 🛑 Disabling or Skipping YAML Linting

- To skip linting temporarily, use the `--no-verify` flag on `git commit`.
- To disable formatting rules, edit `.yamlfmt`.
- To disable lint rules, edit `.yamllint`.
- To remove linting completely, remove the related `lefthook.yml` hooks and `just` commands.

---

## 📚 References

* [📘 yamlfmt GitHub Repository](https://github.com/google/yamlfmt)
* [🛠 yamlfmt Configuration Options](https://github.com/google/yamlfmt#configuration)
* [🔧 Our yamlfmt Configuration](https://github.com/smorinlabs/py-launch-blueprint/blob/main/.yamlfmt)
* [🔧 yamllint Documentation](https://yamllint.readthedocs.io/)
* [🚀 Pre-commit Integration](https://pre-commit.com/)
