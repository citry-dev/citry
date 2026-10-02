---
title: IDE support
description: Catch template mistakes as you type in your editor, or from the command line and CI, with the same checks Citry runs when it renders.
---

# IDE support

A misspelled component tag, a variable your template data never provides, or
an unclosed element otherwise shows up only when the page renders. Citry's
editor tools report these mistakes while you type, and `citry check` reports
them from a terminal or CI.

All of these tools use the same parser that renders your templates. A template
that shows an error in the editor fails for the same reason in `citry check`
and at runtime.

## Pick your editor

| Editor | What you get | Setup |
| --- | --- | --- |
| VS Code, Cursor, and other VS Code forks | Errors as you type, completion, hover, go to definition, type checking, formatting, and template coloring | [VS Code](/ide/vscode/) |
| PyCharm | The same errors, completion, hover, and navigation, without Citry coloring | [PyCharm](/ide/pycharm/) |
| Any editor | `citry check` in a terminal | [Check from a terminal](#check-from-a-terminal) |

!!! note

    VS Code has the most complete support. The editor help comes from a
    separate program, the Citry language server (`citry-lsp` on PyPI), which
    the VS Code extension starts for you. It uses the standard Language
    Server Protocol, so another editor can use it too, once that editor is
    set up to start it for Python and Citry template files.

## Check from a terminal

`citry check` runs the same checks without an editor. Point it at the
[`Citry`][citry.Citry] instance your application uses:

```console
citry --app myproject.app:citry_app check
```

With the application loaded, Citry knows every component you registered, so it
also reports unknown component tags, wrong inputs and slots, and template
variables that come from nowhere.

When the project cannot be imported, for example in a CI job without its
dependencies, run the checks that do not need your components, such as
template syntax:

```console
citry check --static
```

If the import fails under `--app`, Citry reports the failure, checks syntax
only, and exits with status 2, so a CI job cannot mistake it for a full check.
See [Command line](/cli/#check-component-templates) for every option and exit
status.

## Choose what's an error

Your application decides which template mistakes are errors, warnings, or
ignored, and which extra variable names are known. `citry check` and the
editor read the same settings. See [Template linting](/ide/template-linting/).

To look up an error code such as `citry.template.unknown-variable`, see the
[diagnostic reference](/ide/diagnostics/).

To color Citry code in documentation or other tools built on Pygments, install
the separate
[`pygments-citry`](https://pypi.org/project/pygments-citry/){: target="_blank" rel="noopener"}
package.
