---
title: PyCharm
description: Get Citry errors, completion, hover, and go to definition in PyCharm by connecting the Citry language server through the LSP4IJ plugin.
---

# PyCharm

In PyCharm, Citry can report template mistakes as you type, complete
component names and inputs, show types on hover, and take you to where a
name is defined. This works inside the `template` strings of your Python
components and in standalone `*.citry-html` template files.

This help comes from the Citry language server, `citry-lsp`. PyCharm starts it
through the free [LSP4IJ plugin](https://plugins.jetbrains.com/plugin/23257-lsp4ij){: target="_blank" rel="noopener"}.
Citry runs next to PyCharm's own Python support, so nothing you already rely
on changes.

Two things are not included: Citry adds no coloring to templates in PyCharm,
and HTML help inside nested templates is missing. For those, use
[VS Code](/ide/vscode/).

## Set up PyCharm

1. Install the language server in your project's Python environment, the one
   that can import your application:

    ```console
    python -m pip install citry-lsp
    ```

2. Install **LSP4IJ** from PyCharm's plugin Marketplace.
3. Download Citry's
   [LSP4IJ template folder]({{ repo_url }}/tree/main/packages/editors/jetbrains/lsp4ij/citry){: target="_blank" rel="noopener"}.
4. Open **Settings → Languages & Frameworks → Language Servers**, add a
   language server, open the template selector, and choose
   **Import from custom template…**. Select the downloaded `citry` folder.
5. If your virtual environment is not in `.venv`, change the server command.
   The template starts it from there:

    ```text
    macOS/Linux: $PROJECT_DIR$/.venv/bin/citry-lsp
    Windows:     $PROJECT_DIR$/.venv/Scripts/citry-lsp.exe
    ```

6. Tell Citry where your application is, as the next section shows.

Then open a component module or a template file. One Citry server handles
both kinds of file for the project.

## Connect your app

Citry needs your [`Citry`][citry.Citry] instance to know which components you
registered. Without it, Citry checks only template syntax: it cannot complete
your components or report a misspelled component tag.

Set `app` in the server's initialization options to the instance's
`module:attribute` path. The template uses `app:app`; change it to match your
project:

```json
{
  "protocolVersion": 1,
  "app": "myproject.app:citry_app",
  "standardFormatting": true
}
```

`app` can also name a [`ComponentLibrary`][citry.ComponentLibrary], to work on
a component library without a host application.

## Settings

These keys go in the same initialization options:

| Key | What it does | Default |
| --- | --- | --- |
| `app` | The `module:attribute` path of your `Citry` instance or `ComponentLibrary` | `"app:app"` in the template |
| `envFile` | A dotenv file to load before importing `app`, relative to the project root | None |
| `typeCheck` | Report TypeScript errors in component JavaScript and templates | `true` |
| `standardFormatting` | Let PyCharm format standalone `*.citry-html` files with Citry | `true` |
| `protocolVersion` | The settings format version | Required. Keep it at `1` |

Use `envFile` when importing your application needs environment variables,
such as Django settings:

```json
{
  "protocolVersion": 1,
  "app": "myproject.app:citry_app",
  "envFile": ".env",
  "standardFormatting": true
}
```

Citry uses these variables only while it imports your application. If you
edit the file and Citry does not pick up the change, restart the language
server.

The VS Code page describes these TypeScript errors under
[TypeScript errors](/ide/vscode/#typescript-errors-in-component-javascript-and-templates).
In PyCharm, the server needs Node.js and TypeScript's `tsc`, from your
project's `node_modules` or on `PATH`. When it finds neither, it logs a
warning and looks again every minute.

## Check from a terminal

PyCharm's terminal, or an external tool entry, can run the same checks as a
command. This is also what you run in CI:

```console
citry --app myproject.app:citry_app check
```

Use `citry check --static` when the project cannot be imported. See
[Command line](/advanced/cli/#check-component-templates).

## Current limits

- **No Citry coloring.** Inline `template`, `js`, and `css` strings keep
  PyCharm's normal Python string color, and `*.citry-html` files get no
  Citry coloring either.
- **No HTML, JavaScript, or CSS help inside nested templates.** Citry's own
  checks and completion still work in nested templates, the markup you
  write inside an attribute value, but PyCharm's HTML, JavaScript, and CSS help does not reach them, as it
  does in VS Code.
- **No status message when the application fails to import.** You see the
  standard editor warning instead, and Citry checks syntax only until the
  import works.
- **Remote development is untested.** The setup was tested in local PyCharm
  2026.2.0.1 with LSP4IJ 0.20.1.

Citry has no native PyCharm or IntelliJ plugin. To follow or vote for one, see
[GitHub issue #78](https://github.com/citry-dev/citry/issues/78){: target="_blank" rel="noopener"}.
