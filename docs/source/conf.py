# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from py_launch_blueprint import __version__

project = 'py-launch-blueprint'
copyright = '2025, Steve Morin'
author = 'Steve Morin'
# Single-sourced from pyproject.toml [project] version via the installed
# package metadata (py_launch_blueprint.__version__); never hardcode here.
release = __version__
version = '.'.join(release.split('.')[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc', # for auto-generating documentation from docstrings
    'sphinx.ext.viewcode', # for linking to the source code
    'sphinx.ext.napoleon', # for parsing Google-style docstrings
    'sphinx.ext.intersphinx', # for cross-referencing other projects' documentation
    'sphinx_autodoc_typehints', # for type hints
    'myst_parser',  # for Markdown support
    'sphinx_copybutton' # for copy button in code blocks
]

# WL-021: generate anchors for h1-h3 so '#heading-slug' cross-references
# resolve (the -W docs gate treats missing targets as errors).
myst_heading_anchors = 3

myst_enable_extensions = [
    'colon_fence', # for colon fences ::: bash instead of ```bash
    'deflist', # for definition lists Term\n : Definition
]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'

# Theme specific options
html_theme_options = {
    "sidebar_hide_name": False,  # Set to True if you want to hide the project name when logo is present

    # Footer social links
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/smorinlabs/py-launch-blueprint",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
        {
            "name": "GitHub Repository",
            "url": "https://github.com/smorinlabs/py-launch-blueprint",
            "html": """
                <span class="furo-footer-link">View on GitHub</span>
            """,
            "class": "",
        },
    ],
}

# The logo configuration
html_logo = "_static/py_launch_blueprint_logo_100x100.png"
