---
title: IDE support
description: Check Citry templates and add editor intelligence with the command-line checker, language server, and editor integrations.
---

# IDE support

Citry uses the same parser in its command-line checker and editor tooling. A
template that fails in the editor should therefore fail for the same reason in
`citry check` and at runtime.

The open-beta tooling is VS Code-first. The language server is editor-neutral,
but each editor still needs a client that knows how to start it and which files
to send.

## Current tooling

| Tool | What it does | Status |
| --- | --- | --- |
| `citry check` | Checks templates from a terminal or CI | Included in Citry |
| `pygments-citry` | Highlights Citry source in Pygments-based tools | Published separately |
| `citry-lsp` | Provides diagnostics, completion, hover, navigation, and symbols | Implemented; public release is part of the open beta |
| VS Code extension | Highlights inline and standalone templates and starts `citry-lsp` | Implemented; public release is part of the open beta |
| PyCharm + LSP4IJ | Connects PyCharm to Citry's standard language-server features | Tested setup available; no Citry-specific coloring or official plugin yet |

Start with [VS Code](/ide/vscode/) for the complete editor integration. See
[PyCharm](/ide/pycharm/) for the tested LSP4IJ setup and its current coloring
and embedded-language limits.

## Check templates without an editor extension

Every editor can run the batch checker in a terminal. Choose the explicit
static mode when importing the application is unnecessary:

```console
citry check --static
```

For registered component names, inputs, and slots, point the command at the
[`Citry`][citry.Citry] instance used by the application:

```console
citry --app myproject.app:citry_app check
```

If the app import fails, Citry reports the failure, continues with syntax-only
checks, and exits with status 2. CI cannot mistake that degraded result for a
complete registry check.

Registry-backed checks also report unknown free template roots. Configure the
shared batch/editor rule, runtime globals, and analysis-only variables on the
application as described in [Template linting](/ide/template-linting/).
