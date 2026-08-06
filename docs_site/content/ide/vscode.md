---
title: VS Code
description: Highlight Citry templates and connect VS Code to the Citry language server.
---

# VS Code

The Citry extension highlights `template`, `js`, and `css` multiline strings
inside Python components. It also supplies a **Citry Template** language mode
for standalone files and starts one `citry-lsp` process for each workspace
folder. Formatter commands edit definite Citry-authored sections while leaving
the selected Python formatter in place.

The extension and `citry-lsp` are implemented in the repository. Their public
registry releases are part of the Citry 0.3.2 open beta, so the installation
commands below become the public path when those artifacts are available.

## Install the language server

Install `citry-lsp` in the same Python environment as the Citry project:

```console
python -m pip install citry-lsp
```

Keeping the server in the project environment lets it import the registered
component catalog. An isolated server can still check syntax, but it cannot
know the application's component names, inputs, or slots.

Install **Citry** from the Visual Studio Marketplace. Cursor, Windsurf,
VSCodium, and other compatible forks will use the matching Open VSX release.

## Select the application

Set `citry.app` to the `module:attribute` path of the project's
[`Citry`][citry.Citry] instance:

```json
{
  "citry.app": "myproject.app:citry_app"
}
```

The extension normally follows the interpreter selected by Microsoft's Python
extension. Set `citry.python` to an explicit executable when that integration
is unavailable:

```json
{
  "citry.python": "/path/to/project/.venv/bin/python"
}
```

With no app configured, the status bar reports **syntax only**. Definite
inline templates and files explicitly using the Citry Template language are
still checked, but unknown components and their contracts are not inferred.

## Associate standalone templates

Citry accepts any filename in `template_file`, so the extension does not claim
ordinary `.html` files. Add a project-specific association when appropriate:

```json
{
  "files.associations": {
    "templates/components/**/*.html": "citry-html"
  }
}
```

## Format Citry documents

The command palette exposes only two Citry formatting commands:

- **Citry: Format Document** formats every definite direct `template`, `js`,
  and `css` literal in the current Python file.
- **Citry: Format at Cursor** formats only the direct literal body containing
  the cursor.

Both include Citry/HTML structure and Python expressions, eligible direct
JavaScript and CSS, and eligible `<script>` and `<style>` bodies. A cursor on a
`template_file`, `js_file`, or `css_file` path, a method such as
`template_data`, or unrelated Python code is outside a format region and is
refused without edits. The commands do not follow a Python declaration into
another file; open the target directly or use `citry format` for statically
resolved file assets. For a standalone JavaScript or CSS file, “directly” means
its normal language formatter; Citry does not wrap generic JS/CSS documents.

A file in the Citry Template language is one template, so either command
formats the whole document. The explicit commands also accept an HTML-mode
file that the configured registry proves is a resolved `template_file`, while
unrelated HTML is refused. Associate the file with `citry-html` to use VS
Code's standard formatter and format-on-save:

```json
{
  "[citry-html]": {
    "editor.defaultFormatter": "citry-dev.citry",
    "editor.formatOnSave": true
  }
}
```

Citry sends each JavaScript or CSS region to an immutable standalone document
and asks VS Code's public formatter command for edits. In VS Code 1.93 this is
the first applicable
non-empty formatter result; the API does not identify the provider or
guarantee that it is the configured default. Citry reports this honestly as
the `vscode-first-result` mechanism. A missing provider leaves the region
unchanged and writes a notice to the Citry output channel.

VS Code's built-in CSS formatter accepts these virtual documents. Its built-in
JavaScript/TypeScript formatter does not, so JavaScript formatting currently
requires an installed formatter that accepts non-file virtual documents;
Prettier is the recommended compatible option. This affects formatting only,
not embedded JavaScript highlighting, completion, hover, or definitions. The
CLI uses its explicit native Biome adapter instead of an editor formatter.

```console
code --install-extension esbenp.prettier-vscode
```

Whitespace-sensitive multiline literals/comments and position-sensitive
hashbang, `@charset`, or BOM bodies are also left unchanged rather than being
unsafely reindented.

Keep the normal Python formatter selected and add Citry as an independent
save action. This uses the same whole-document Citry behavior as **Citry:
Format Document**:

```json
{
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.format.citry": "explicit"
    }
  }
}
```

The Citry/HTML and built-in Python-expression, `c-for`, and `c-fill data`
passes produce the same bytes across the CLI, Python API, language server, and
extension. Embedded JavaScript/CSS output also matches when the provider,
version, and options match. For deterministic automation, configure the CLI's
explicit Biome adapter instead of relying on editor provider ordering.

## Current limits

- Highlighting of deeply nested or unfinished expressions is best effort.
- Parsing stops after the first syntax error.
- Python analysis remains the responsibility of Pylance or Pyright.
- Embedded CSS and JavaScript receive highlighting, completion, hover, and
  formatting through VS Code providers, but Citry cannot request their
  diagnostics through VS Code's public API.
- The built-in CSS formatter accepts Citry's virtual documents, but the
  built-in JavaScript/TypeScript formatter does not. Install Prettier or another
  formatter that accepts non-file virtual documents for embedded JavaScript
  formatting.
- Each embedded provider pass is bounded to 30 seconds. VS Code does not expose
  cancellation for the underlying public formatter command, so Citry discards
  any result that arrives after that bound.
- `<script>` and `<style>` bodies containing Citry interpolation remain
  unchanged until a context-safe placeholder adapter is available.
- A TextMate grammar cannot prove that a class with a `template`, `js`, or
  `css` assignment inherits from `Component`, so unrelated assignments with
  those exact names may receive Citry highlighting.
