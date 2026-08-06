---
title: PyCharm
description: Use Citry's command-line checks in PyCharm and understand the planned editor integration.
---

# PyCharm

Citry does not currently publish an official PyCharm plugin. PyCharm therefore
does not yet receive Citry-aware coloring inside Python `template`, `js`, and
`css` strings.

## What works today

Run Citry's batch checker from PyCharm's terminal or as an external tool:

```console
citry check --static
```

Use registry mode when the project can import its [`Citry`][citry.Citry]
instance:

```console
citry --app myproject.app:citry_app check
```

This provides the same parser diagnostics used by the language server, but as
a command rather than live editor feedback.

## Planned integration

The first candidate is a documented LSP4IJ configuration that starts
`citry-lsp` from the project's Python environment. It still needs a real
PyCharm test proving that a second language server can attach to Python files
already owned by PyCharm's Python support. Citry will not claim diagnostics,
completion, or navigation in `.py` files until that test passes.

A thin official JetBrains plugin remains a later option if configuration is
too difficult or if users need Citry-aware inline highlighting. That work will
be tracked on the public roadmap rather than implied by the current package.

