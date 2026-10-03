---
title: Command line
description: Scaffold components, check templates, inspect an engine, watch files, and run extension commands.
---

# Command line

Installing Citry gives you the `citry` command. Use it to create a
component file, find template mistakes before you render, format component
files, reload templates while you develop, and see what your application
registered.

Every command and subcommand lists its options with `--help`:

```bash
citry --help
citry watch --help
citry --version
```

## `citry create` component

`citry create` writes a new component file:

```bash
citry create MyButton
```

This creates `my_button.py` in the current directory, with a
[`Component`][citry.Component] that has `Kwargs`, `Slots`, and an inline
template. Use `--path` or `-p` to write it to another directory:

```bash
citry create MyButton --path ./components
```

You can write the name in PascalCase, snake_case, or kebab-case. All of
these create `my_button.py` with `class MyButton(Component)`:

```bash
citry create MyButton
citry create my_button
citry create my-button
```

A PascalCase name is kept as written, acronyms included:
`citry create HTTPServer` creates `http_server.py` with
`class HTTPServer(Component)`.

The command never overwrites an existing file. It also refuses a Python
keyword, such as `class`, and a name that turns into a module name starting
with `__`.

## Point at your app

Most commands work on a [`Citry`][citry.Citry] instance: they read its
registered components and extensions. By default they use the module-level
[`citry`][citry.citry] instance, except `check`, which needs `--app` or
`--static`. If your application creates its own instance, name it with
`--app module:attribute`, before the command name:

```bash
citry --app myproject.engine:app list
citry --app myproject.engine:app inspect --json
citry --app myproject.engine:app check
citry --app myproject.engine:app ext list
```

`--app` must be the first argument, written as `--app VALUE` or
`--app=VALUE`. The value must name a `Citry` instance. Citry imports
it from the current directory, as web servers such as uvicorn do.

If importing the application fails, the command stops with an error.
`check` is the exception, described below.

## `citry check` templates { #check-component-templates }

`citry check` finds template mistakes without rendering anything. Run it
against your application:

```bash
citry --app myproject.engine:app check
```

It reads the inline and file templates of every component your
application registers, and reports:

- template syntax errors;
- inputs and slots that do not match the component's `Kwargs` and `Slots`,
  including a missing required input and wrong slot data;
- a component tag that names no registered component (built-in names and
  aliases count as registered);
- a template variable that comes from nowhere, following your
  [template lint settings](/ide/template-linting/). Values from
  `template_globals` and declared analysis-only variables count as known.

Each error shows the template excerpt and where it came from: the
component, such as `myapp.card.Card.template`, or the template file. Line
and column numbers count from the start of the template, not the start of
the Python file.

The exit status is:

- `0` when there are no errors, including when there are only warnings;
- `1` when a template or source file has an error;
- `2` when the command line is wrong, or the application could not be
  imported (see below).

Add `--format json` to print one JSON report instead of text lines. Each
finding has an `origin`, `code`, `severity`, `message`, and `range`.
`range` is `null` when the finding has no position.

### `check --static` syntax

When you cannot import the project, for example in a CI job without its
dependencies, check template syntax only:

```bash
citry check --static
```

This mode reads the Python files in the current directory without running
them. It finds only undecorated classes that subclass `Component` or
`LibraryComponent` imported at the top of the module, and checks only a
`template` written on the class as a plain string. It skips file
templates, inherited and computed templates, and cannot report an unknown
component, because it never sees the full list of registered components.
An error's origin is the file's full path followed by the attribute, such
as `/home/me/proj/myapp/card.py (Card.template)`.

`citry check` without `--app` or `--static` is rejected with status 2, so a
passing result always says which kind of check ran. The two options cannot
be combined.

### When import fails

With `--app`, a failed import does not stop the check. The command reports
the failure once, checks template syntax as `--static` would, and exits
with status 2. It never reports results from a partly loaded set of
components as complete.

### What is not checked

- It does not look for unknown component tags inside attribute values
  that hold template source.
- It does not run template transform hooks. It checks the template as you
  wrote it, and notes this once in its output.

### `check --types` typing { #check-types-with-typescript-and-ty }

Add `--types` to also type-check your components the way the editor does:

```bash
citry --app myproject.engine:app check --types
```

Two type checkers run on every component whose source is in the current
directory:

- TypeScript checks each component's JavaScript and the Vue expressions in
  its template, the same check the
  [VS Code extension](/ide/vscode/#typescript-errors-in-component-javascript-and-templates)
  runs;
- ty, the Python type checker that `citry-lsp` installs, checks the Python
  expressions in its template.

A TypeScript error shows the file's full path, line, column, and
TypeScript's code (wrapped here to fit):

```text
/srv/shop/app/components/lane.py:24:13: error: TS2322: Type
'boolean' is not assignable to type '() => void'.
```

A ty finding, such as adding a number to a string, keeps ty's severity and
starts with ty's rule name:

```text
/srv/shop/app/components/card.py:56:16: error: unsupported-operator:
Operator `+` is not supported between objects of type `str` and
`Literal[1]`
```

In `--format json`, the codes are `citry.typescript.ts2322` and
`citry.python.unsupported-operator`.

The findings match what the editor shows, with one difference: ty's own
unknown-name finding is left out, because Citry's
[`citry.template.unknown-variable`](/ide/diagnostics/#citry.template.unknown-variable)
rule already reports that mistake. ty runs first and works out the types
of `js_data()` values Citry cannot type on its own, such as a method call.
TypeScript then uses those types to check the browser code that reads
them, as in the
[editor](/ide/vscode/#complete-vue-expressions-and-component-javascript).

An error exits with status 1, like any other error. A ty warning is shown
but does not change the exit status.

Run the command from the project root. ty resolves imports from the
current directory, so from a subdirectory it can miss findings in code
that imports the rest of the project.

`--types` needs:

- the `citry-lsp` package, which prepares the files TypeScript and ty
  check, and installs ty;
- Node.js on `PATH`;
- TypeScript's `tsc`, from the nearest `node_modules` in the current
  directory or a parent, or from `PATH`. Install it with
  `npm install --save-dev typescript`.

If one is missing, or ty cannot start or stops responding, the command
exits with status 2 and says what to install or fix.

`--types` skips components installed from another package. It needs your
registered components, so it cannot be combined with `--static`, and it
does not run when the application fails to import. The report notes that
it was skipped.

## `citry format` files { #format-component-files }

`citry format` formats component templates in place. It reads source files
without importing your application:

```bash
citry format path/to/components
```

It accepts files and directories, and formats the current directory when
you give no path:

- in a Python file, the `template`, `js`, and `css` strings of each
  component it can find without running the code;
- in a directory, those Python files, plus the files named by a fixed
  `template_file`, `js_file`, or `css_file` inside that directory;
- standalone `.html`, `.citry`, and `.citry-html` template files, and
  `.js` and `.css` files.

Preview a change without writing it:

```bash
citry format --check path/to/components
citry format --diff path/to/card.py
```

`--check` lists the files that would change, and `--diff` prints the
changes. Both exit with status 1 when a file would change. They cannot be
combined. A file that cannot be formatted makes the command exit with
status 2. `citry format` rejects `--app` and `--static` with status 2.

The formatter lays out the HTML structure conservatively and formats
Python expressions, `c-for` clauses, and `c-fill data` patterns. Add
`--verbose` to see which formatters are active.

### Format JS and CSS

Citry formats JavaScript and CSS only when you name a
[Biome](https://biomejs.dev/) executable:

```bash
citry format path/to/components \
  --javascript-provider biome:/absolute/path/to/native/biome \
  --css-provider biome:/absolute/path/to/native/biome
```

The path must point to Biome's native binary for your platform. Citry
rejects scripts and launchers such as the npm, pnpm, or Windows command
wrappers, because it cannot tell which files they would load.

Biome then formats component `js` and `css` strings, standalone `.js` and
`.css` files, and `<script>` and `<style>` bodies in templates. Citry
leaves a `<script>` or `<style>` body unchanged, and reports it, when the
body:

- contains Citry syntax such as `{{ value }}` or a `{# ... #}` comment;
- is not plain JavaScript or CSS, or sets its language with an
  expression;
- has a multiline string or template literal, a line continuation, or a
  multiline block comment, whose exact whitespace must stay;
- starts with a hashbang (`#!`), `@charset`, or a byte order mark.

`--embedded` decides what happens when no Biome path is given for a
language:

- `available`, the default, formats what it can and reports the rest
  without failing;
- `required` treats a missing provider as an error and leaves the
  affected file unchanged;
- `off` turns Biome off, and ignores any provider paths you passed.

A region you turned off with `{# fmt: off #}` never counts as missing.

### Repeatable Biome runs

Citry identifies each Biome setup by a fingerprint: a hash of the Biome
binary and of the exact configuration it used. Error messages include it,
and two runs with the same fingerprint used the same inputs. To keep that
true, Citry:

- uses the nearest `biome.json` or `biome.jsonc` for each file and gives
  Biome a private copy, or an empty configuration when none exists. File
  patterns in it still match paths relative to the configuration file.
  Having both files in one directory is an error;
- rejects a configuration that uses `extends` or `plugins`, including
  override plugins, because the files they load are not in the
  fingerprint;
- rejects a configuration file that is a symlink;
- ignores `BIOME_*` environment variables, `.editorconfig`, and settings
  taken from version control;
- runs a copy of the binary from a private per-user cache.

Citry never searches `PATH` for Biome, never runs it through a shell, and
never lets it write files itself. It stops Biome after 15 seconds, or when
its output passes 8 MiB.

## `citry watch` reloads

`watch` watches your component directories. When a template, JavaScript,
or CSS file changes, the next render uses the new file:

```bash
citry --app myproject.engine:app watch
```

Press <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop it.

To watch other directories than the ones your application configures,
pass `--path` or `-p`, once per directory:

```bash
citry --app myproject.engine:app watch \
  -p ./components \
  -p ./plugins/components
```

`watch` does not reload changed Python code or restart your web server.
Run your framework's reloader alongside it. See
[Hot reload](/guides/dev-server/) for the complete setup.

If `watchfiles` or `watchdog` is installed, Citry uses it to get file
change events from the operating system. Otherwise it checks the files
for changes at regular intervals.

## `citry list` components

`list` prints every component your application registered, Citry's
built-in components included:

```bash
citry --app myproject.engine:app list
```

Each row shows the component's names, its Python class, and its source
file. Use it when a template tag does not find the component you expect,
or to check that [component discovery](/advanced/component-discovery/)
found a module.

## `inspect --json` export

`inspect --json` prints a description of your components, as a
[`ComponentCatalog`][citry.ComponentCatalog] in JSON, for tools to read:

```bash
citry --app myproject.engine:app inspect --json
```

Add a registered name or alias to describe one component:

```bash
citry --app myproject.engine:app inspect checkout-page --json
```

The name ignores letter case, and the output uses the component's main
name. You can name a built-in component this way too. An unknown name
exits with status 2.

`--json` is required. The command leaves out built-in components (unless
you name one), does not resolve asset paths on disk, leaves out the default
values of inputs, and does not run extension inspectors. For other options, call
[`inspect_component()`][citry.Citry.inspect_component] or
[`inspect_components()`][citry.Citry.inspect_components] from Python.

The output can contain absolute paths from your machine, so do not serve
it from a public endpoint. Anything your application prints while it is
imported also goes to the output, so keep imports quiet when another tool
reads the JSON.

## `ext list` extensions

`ext list` prints the [extensions](/advanced/extensions/) your
application uses:

```bash
citry --app myproject.engine:app ext list
```

Every application has `cache`, `dependencies`, `events`, and `i18n`.
Extensions your application adds come after them.

## `ext run` commands { #run-an-extension-command }

Extensions can add their own commands. Run one with `ext run`, the
extension name, and the command name:

```bash
citry --app myproject.engine:app \
  ext run events openapi
```

Leave out the command name to list the commands an extension offers:

```bash
citry --app myproject.engine:app ext run events
```

### Add a command

Subclass [`ExtensionCommand`][citry.ExtensionCommand], describe its
arguments with [`CommandArg`][citry.CommandArg], and list it in the
extension's `commands`:

```python
from citry import CommandArg, Extension, ExtensionCommand


class Greet(ExtensionCommand):
    name = "greet"
    help = "Greet someone."
    arguments = (CommandArg("who"),)

    def handle(self, **kwargs):
        print(f"Hello {kwargs['who']}")


class Greeter(Extension):
    name = "greeter"
    commands = (Greet,)
```

Add the extension to your application's `Citry` instance, then run:

```bash
citry --app myproject.engine:app \
  ext run greeter greet Ada
```

In `handle()`, `self.citry` is the selected `Citry` instance. Accept
`**kwargs`, because `handle()` receives every parsed option, including
options of the commands above it.

See [Extensions](/advanced/extensions/) for the rest of the extension API.

## Related reference

- [`Citry.inspect_components()`][citry.Citry.inspect_components]
- [`ComponentCatalog`][citry.ComponentCatalog]
- [`ExtensionCommand`][citry.ExtensionCommand]
- [`CommandArg`][citry.CommandArg]
- [`CommandArgGroup`][citry.CommandArgGroup]
