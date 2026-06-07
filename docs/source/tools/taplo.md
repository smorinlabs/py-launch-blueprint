## Taplo: A Fast TOML Formatter & Linter

### Introduction
Taplo is used to automatically format and validate project files like pyproject.toml and cog.toml, ensuring consistent structure and preventing syntax errors across the codebase.

---

**Key Benefits**:

* 🚀 **High Performance**: Built in Rust, Taplo formats TOML files extremely fast.
* 🛠 **Highly Configurable**: Supports options like entry alignment, array expansion, and comment alignment.
* ✅ **Formatter + Linter**: Formats and validates TOML files.
* 🧩 **Editor Integration**: Works with editors through `taplo-lsp`.
* 🤖 **CI/CD Friendly**: Use `taplo format` to fix and `taplo check` to enforce formatting in CI.

---

### ⚙️ Getting Started

**Installation**
Install Taplo CLI (requires Rust):

```bash
just install-taplo
```

**Quick Example**
Create a sample TOML file and format it:

```bash
echo '[table]\nkey = "value"   # Needs formatting' > example.toml
taplo format example.toml
cat example.toml
```

Expected output will show aligned key/value and comment (based on config).

---

### 🚀 Usage

**Example Use Case**:

During continuous integration (CI), you want to enforce consistent TOML formatting. With `taplo check` in your CI pipeline, you can automatically reject pull requests that don’t follow the formatting standards, saving time on manual code review for formatting issues.


**Format TOML files:**

```bash
just format-toml
```

**Check TOML formatting (without modifying files):**

```bash
just check-toml
```

Run it manually:

```bash
just pre-commit-run
```

---

### 🛠 Recommended Configuration

`.taplo.toml`:

```toml
[formatting]
respect-ignores = true
line-width = 80
indent-width = 4
align-entries = true
align-comments = true
array-auto-expand = true
array-auto-collapse = false
compact-arrays = false
compact-inline-tables = false
newline-style = "LF"
```

➡️ [Full option list here](https://taplo.tamasfe.dev/configuration/formatter-options.html)

---

### 🛑 Disabling Taplo

**To temporarily skip formatting:**
* Disable specific rules in `.taplo.toml`:

```toml
[formatting]
respect-ignores = true
line-width = 80
indent-width = 4
align-entries = true
align-comments = true
array-auto-expand = true
array-auto-collapse = false
compact-arrays = false
compact-inline-tables = false
newline-style = "LF"
```

**To completely remove Taplo:**
* Delete `.taplo.toml`
* Remove Taplo commands from your `Justfile`

---

### 📚 References

* [📘 Taplo Docs](https://taplo.tamasfe.dev/)
* [🛠 Taplo GitHub](https://github.com/tamasfe/taplo)
---
