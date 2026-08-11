# Citry for LSP4IJ

This is Citry's tested LSP4IJ definition for PyCharm and other JetBrains IDEs.
In LSP4IJ's **New Language Server** dialog, choose **Import from custom
template...** and select this directory.

The defaults assume:

- the project interpreter lives in `.venv`;
- the Citry application is importable as `app:app`;
- the project root is the server working directory.

After importing, adjust the command and the `app` initialization option when
the project uses a different interpreter or application target. The Python
mapping intentionally attaches Citry as a second language server alongside
PyCharm's own Python support. The `*.citry-html` mapping covers standalone
component templates.

The definition was verified with PyCharm 2026.2.0.1 and LSP4IJ 0.20.1. It
provides Citry's standard LSP diagnostics, completion, hover, navigation,
references, type definitions, and standalone formatting. It does not add
Citry-specific syntax coloring, and it cannot provide VS Code's private
HTML/JavaScript/CSS delegation features.
