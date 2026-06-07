# Documentation Guide

This guide will help you get started with writing documentation for this project using Sphinx and MyST Markdown.

(quickstart-docs)=
## Quick Start

To start working on the documentation:

1. Make sure you have the dependencies installed:
   ```bash
   just install-docs
   ```

2. Start the documentation server with hot reloading:
   ```bash
   cd docs
   make hotreloadhtml
   ```
   This will start a local server (usually at http://127.0.0.1:8000) that automatically rebuilds and reloads when you make changes.

## Adding New Pages

1. Create a new `.md` file in the `docs/source` directory:
   ```bash
   touch docs/source/my-new-page.md
   ```

2. Add your content using Markdown syntax:
   ```markdown
   # My New Page Title

   This is a new documentation page.
   ```

3. Add the page to the table of contents in `index.md`:
   ```markdown
   ```{toctree}
   :maxdepth: 2
   :caption: Contents

   my-new-page
   other-pages
   ```
   ```

(cross-references)=
## Cross References

### Creating Reference Targets

Add a label above any section you want to reference:

```markdown
(my-custom-label)=
## My Section Title

Content goes here...
```

### Referencing Other Sections

Reference any labeled section using the `{ref}` role:

```markdown
See the {ref}`My Section Title <my-custom-label>` for more information.
```

You can also use a custom link text:
```markdown
Check out our {ref}`installation guide <my-custom-label>`.
```

(static-content)=
## Static Content

### Adding Images

1. Place your images in the `_static` directory:
   ```bash
   cp my-image.png docs/source/_static/
   ```

2. Reference images in your markdown:
   ```markdown
   ![Alt text](_static/my-image.png)
   ```

   Or use the figure directive for more control:
   ```markdown
   ```{figure} _static/my-image.png
   :alt: Alt text
   :width: 200px
   :align: center

   Optional caption goes here
   ```
   ```

### Changing the Logo

1. Add your logo to the `_static` directory
2. Update `conf.py` with the logo path:
   ```python
   html_logo = "_static/your-logo.png"

   # For Furo theme, you can set different logos for light/dark mode:
   html_theme_options = {
       "light_logo": "_static/light-logo.png",
       "dark_logo": "_static/dark-logo.png",
   }
   ```

## Advanced Features

### Admonitions (Note Boxes)

Create attention-grabbing note boxes:

```markdown
```{note}
This is a note box.
```

```{warning}
This is a warning box.
```

```{tip}
This is a tip box.
```
```

### Code Blocks with Syntax Highlighting

```markdown
```python
def hello_world():
    print("Hello, World!")
```
```

### Tables

Create tables using markdown syntax:

```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
```

## Building Documentation

Common make commands:

- `make html` - Build HTML documentation
- `make hotreloadhtml` - Start development server with hot reloading
- `make clean` - Remove built documentation
- `make help` - Show all available commands

## Troubleshooting

Common issues and solutions:

1. **Missing Pages in TOC**:
   - Ensure the file is listed in the `toctree` directive
   - Check file path is relative to the TOC file
   - Verify file extension is `.md` or `.rst`

2. **Broken References**:
   - Check label names match exactly
   - Labels must be unique across all documentation
   - Look for warning messages in the build output

3. **Build Errors**:
   - Run `make clean` before `make html`
   - Check syntax in modified files
   - Look for missing dependencies
