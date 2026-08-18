---
title: PyCharm
description: Connect PyCharm to the Citry language server with LSP4IJ, or run the command-line checker.
---

# PyCharm

!!! warning "No first-party JetBrains plugin yet"

    Citry does not currently have a native PyCharm or IntelliJ plugin. Follow
    development and vote for the integration on
    [GitHub issue #78](https://github.com/citry-dev/citry/issues/78){: target="_blank" rel="noopener"}.
    The tested LSP4IJ setup below provides substantial language-server
    support while that work remains parked.

Citry's tested PyCharm integration uses the free
[LSP4IJ plugin](https://plugins.jetbrains.com/plugin/23257-lsp4ij){: target="_blank" rel="noopener"}
to start `citry-lsp` from the project's Python environment. Citry attaches as
a second language server to Python files, so PyCharm's own Python support
continues to work.

This setup provides live Citry diagnostics, completion, hover, Definition,
References, Declaration, and Type Definition in inline Python templates and
standalone `*.citry-html` files. Standalone Citry formatting also works. The
setup was exercised in PyCharm 2026.2.0.1 with LSP4IJ 0.20.1.

Citry does not currently publish an official JetBrains plugin. The LSP4IJ
route therefore does not add Citry syntax coloring, and it cannot reproduce
the VS Code extension's private HTML, JavaScript, and CSS provider bridges.

## Install the language server

Install `citry-lsp` in the same Python environment as the Citry project:

```console
python -m pip install citry-lsp
```

Keeping the server in the project environment lets it import the registered
component catalog. Then install **LSP4IJ** from PyCharm's plugin Marketplace.

## Import the Citry server definition

1. Download or copy Citry's
   [LSP4IJ template directory]({{ repo_url }}/tree/main/packages/editors/jetbrains/lsp4ij/citry){: target="_blank" rel="noopener"}.
2. Open **Settings → Languages & Frameworks → Language Servers** in PyCharm.
3. Add a language server, open the template selector, and choose
   **Import from custom template…**.
4. Select the downloaded `citry` template directory.

The definition maps Python documents to the `python` language ID and
`*.citry-html` files to `citry-html`. Its default command expects the project
environment at `.venv`:

```text
macOS/Linux: $PROJECT_DIR$/.venv/bin/citry-lsp
Windows:     $PROJECT_DIR$/.venv/Scripts/citry-lsp.exe
```

Change the command after importing when the environment lives elsewhere.

## Select the registry target

The imported definition defaults to this initialization option:

```json
{
  "protocolVersion": 1,
  "app": "app:app",
  "standardFormatting": true
}
```

Change `app` to the `module:attribute` path of the project's [`Citry`][citry.Citry]
instance or [`ComponentLibrary`][citry.ComponentLibrary]. For example:

```json
{
  "protocolVersion": 1,
  "app": "myproject.app:citry_app",
  "standardFormatting": true
}
```

Open a component module or standalone template after saving the definition.
One Citry server serves both mappings for that project.

## Current limitations

- Inline `template`, `js`, and `css` values retain normal Python string
  coloring. Standalone `*.citry-html` files also have no Citry-specific
  coloring through this setup.
- Nested-template and `<c-element>` Citry semantics still work, but LSP4IJ
  cannot delegate their embedded HTML to JetBrains' HTML provider as the
  VS Code extension does. The same limitation applies to the richer embedded
  JavaScript and CSS provider integrations.
- LSP4IJ does not display Citry's private registry status notification. An app
  discovery failure still appears through the standard editor warning and the
  server falls back to syntax-only analysis.
- The completed spike covered local PyCharm. JetBrains remote development was
  not part of the tested matrix.

These are the reasons a small official JetBrains plugin may still be useful
later: easier setup, first-party status UI, Citry coloring, and private
embedded-language bridges. That work is tracked in
[GitHub issue #78](https://github.com/citry-dev/citry/issues/78){: target="_blank" rel="noopener"}.
A plugin is not needed merely to attach Citry to Python files.

## Check templates from PyCharm

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
a command rather than live editor feedback. It remains useful in CI and when
LSP4IJ is unavailable.
