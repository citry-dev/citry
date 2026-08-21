---
title: Command line
url: https://citry.dev/v/0.4.2/cli/
description: "Scaffold components, check templates, inspect an engine, watch files, and run extension commands."
---
# Command line

Installing Citry gives you the `citry` command. It can create a component file,
check templates, show what an engine registered, watch component files during
development, and run commands supplied by extensions.

See the available commands at any level with `--help`:


```bash
citry --help
citry watch --help
citry --version
```


## Create a component file

`citry create` turns a component name into a Python file:


```bash
citry create MyButton
```


This creates `my_button.py` in the current directory. The file contains a
[`Component`](/v/0.4.2/reference/component/#citry-component) with `Kwargs`, `Slots`, and an inline template.
Use `--path` or `-p` to choose another directory:


```bash
citry create MyButton --path ./components
```


Names may use PascalCase, snake_case, or kebab-case. These commands all create
`my_button.py` with `class MyButton(Component)`:


```bash
citry create MyButton
citry create my_button
citry create my-button
```


Citry preserves an already-PascalCase name, including acronyms. For example,
`citry create HTTPServer` creates `http_server.py` containing
`class HTTPServer(Component)`.

The command never overwrites an existing file. It also rejects Python keywords
and reserved double-underscore module names.

## Select your application's engine

`list`, `inspect`, `watch`, and extension commands use the module-level
[`citry`](/v/0.4.2/reference/citry/#citry-citry-2) engine by default. `check` requires one of the explicit
modes described below. If your application creates its own engine, pass `--app
module:attribute` before the subcommand:


```bash
citry --app myproject.engine:app list
citry --app myproject.engine:app inspect --json
citry --app myproject.engine:app check
citry --app myproject.engine:app ext list
```


The target must be an imported [`Citry`](/v/0.4.2/reference/citry/#citry-citry) instance. `--app` must be
the first argument, either as `--app VALUE` or `--app=VALUE`.

Import and discovery errors stop other engine commands. An app-backed `check`
reports the project failure once, continues with syntax-only analysis, and
exits with status 2. It never treats a partial registry as complete.

## Check component templates

Use the application engine for the registry-backed check:


```bash
citry --app myproject.engine:app check
```


This checks the authored inline and file templates of every registered
application component. It applies the component declarations from `Kwargs` and
`Slots`, including required inputs and typed slot data, and reports component
tags the complete registry does not know. Built-in component names and
registered aliases are included in that lookup. It also applies the
application's [template lint policy](/v/0.4.2/ide/template-linting/) to free root
variables. Runtime `template_globals` and declared analysis-only variables are
known automatically.

When importing project code is intentionally unavailable, select the limited
static mode explicitly:


```bash
citry check --static
```


Syntax-only mode recognizes direct module-level `Component` and
`LibraryComponent` imports that remain unshadowed before the class. It checks
direct literal `template` assignments on undecorated, unambiguous component
candidates whose base template language is known. It skips computed values,
inherited declarations, and file templates; file ownership remains
registry-backed in this first version. This mode validates base template syntax
but does not report an unknown component from an incomplete static view.

Bare `citry check` is rejected so a successful result always identifies which
level of checking ran. `--static` cannot be combined with `--app`.

Unknown-component checks cover ordinary retained template bodies. They do not
yet inspect template-valued attributes, whose public parser kind arrives with
the next IDE-analysis contract; this avoids mistaking expression strings for
template source.

The checker reads authored template text directly. It does not run template
transform hooks, because transformed diagnostics cannot be placed back onto
authored text without a source mapping. The command reports this capability
limit once and continues checking the base Citry syntax.

Each parser failure includes the parser's annotated template excerpt and an
origin naming the file or component. The excerpt's line and column are local to
the template body; exact Python-file ranges arrive with the structured
diagnostic work described in the IDE integration design.

The exit status is:

- `0` when no error is present, including a warning-only report
- `1` when a template or source asset has an error
- `2` for a missing or conflicting mode, or when explicit app selection or
  discovery fails after syntax-only fallback finishes

## Format component assets

`citry format` formats standalone Citry files and statically identifiable
component assets without importing an application. That includes direct
`template`, `js`, and `css` literals, plus constant `template_file`, `js_file`,
and `css_file` declarations discovered beneath an explicit directory:


```bash
citry format path/to/components
citry format --check path/to/components
citry format --diff path/to/card.py
citry format --verbose path/to/card.citry-html
```


The shared formatter handles conservative Citry/HTML structure, Python
expressions, `c-for` clauses, and `c-fill data` patterns. JavaScript and CSS
formatting is opt-in and uses an explicitly named Biome executable:


```bash
citry format path/to/components \
  --javascript-provider biome:/absolute/path/to/native/biome \
  --css-provider biome:/absolute/path/to/native/biome
```


The path must name Biome's self-contained platform-native binary. Every
interpreter script and npm/pnpm or Windows command launcher is rejected because
its effective dependencies cannot be isolated and fingerprinted.

`--embedded=available` (the default) formats regions whose provider is
configured and reports the rest without failing the file.
`--embedded=required` makes a missing provider an error and writes none of the
affected file; `--embedded=off` disables embedded providers and does not even
probe provider paths supplied alongside it. The initial
adapter formats expression-free `<script>` and `<style>` bodies. Bodies that
contain Citry interpolation stay unchanged until a context-safe placeholder
adapter is available. Bodies with multiline quoted/template literals,
line continuations, multiline block comments, or start-sensitive hashbang,
`@charset`, and BOM bytes also stay unchanged until a language-aware source
map can preserve their exact lexical whitespace. Explicit `{# fmt: off #}`
suppression remains an opt-out and does not count as a missing provider in
required mode.

Citry selects the nearest `biome.json` or `biome.jsonc` for each asset and
includes its exact bytes in the reported per-target provider fingerprint.
The initial adapter rejects configurations that use `extends` or `plugins`
(including override plugins), because it cannot yet fingerprint those external
dependencies. Symlinked configuration files are rejected so config-relative
paths cannot disagree with the exact bytes being hashed. It also ignores
`BIOME_*`, editorconfig, and VCS-derived options so the same reported
fingerprint means the same provider inputs.

Citry hashes the selected executable and runs a secured copy from its private
per-user executable cache. It passes an isolated copy of the nearest Biome
configuration—or an explicit empty configuration when none exists—so config
discovery cannot change during the run. Config-relative source paths are
preserved. Configurations using external `extends` or `plugins` remain
unsupported because their dependency bytes cannot yet be included in the
fingerprint.

`--check` and `--diff` do not write. `--verbose` reports every active
capability and provider identity. Citry never searches `PATH`, invokes a shell,
or asks Biome to write the target file. Provider output has one 8 MiB bound
across stdout and stderr, and the provider process tree is stopped after 15
seconds. App selection and `--static` are not formatter modes.

## List registered components

`list` completes component discovery and prints the engine's component
registry:


```bash
citry --app myproject.engine:app list
```


Each row shows the registered names, Python class, and source path. The list
includes Citry's built-in components as well as application components.

Use this when a template tag does not resolve as expected, or to check that
[component discovery](/v/0.4.2/advanced/component-discovery/) found a module.

## Export the runtime catalog

`inspect --json` prints the versioned
[`ComponentCatalog`](/v/0.4.2/reference/component-introspection/#citry-componentcatalog) as compact JSON:


```bash
citry --app myproject.engine:app inspect --json
```


The `--json` flag is required. The command uses the Python introspection API's
defaults: built-ins are excluded, asset paths are not resolved on disk,
portable field defaults are omitted, and extension inspectors do not run.
Call [`inspect_components()`](/v/0.4.2/reference/citry/#citry-citry-inspect-components) from Python when
a tool needs different options.

The output may contain absolute paths from the developer's machine. Treat it
as a local tooling artifact rather than sending it directly from a public HTTP
endpoint. Output printed by application imports also goes to stdout, so keep
those imports quiet when another tool will parse the JSON.

## Watch component files

`watch` monitors the engine's configured component directories. When a
template, JavaScript, or CSS file changes, it clears the affected component's
loaded files:


```bash
citry --app myproject.engine:app watch
```


Press <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop it.

Pass `--path` or `-p` more than once to replace the engine's configured
directories for this run:


```bash
citry --app myproject.engine:app watch \
  -p ./components \
  -p ./plugins/components
```


The watcher reloads component templates and assets. It does not reload changed
Python class definitions or restart your web server. Pair it with your host
framework's Python reloader when both kinds of files may change. See
[Hot reload](/v/0.4.2/guides/dev-server/) for the complete development setup.

When installed, `watchfiles` or `watchdog` supplies native filesystem events.
Without either optional package, Citry uses its dependency-free polling
watcher.

## List installed extensions

`ext list` prints the extensions attached to the selected engine:


```bash
citry --app myproject.engine:app ext list
```


Every engine includes `cache`, `dependencies`, and `events`. Extensions added
by the application appear after them.

## Run an extension command

Extensions can provide their own commands. Run one beneath its extension name:


```bash
citry --app myproject.engine:app \
  ext run events openapi
```


Omit the command name to see the commands that extension provides:


```bash
citry --app myproject.engine:app ext run events
```


### Add a command to an extension

Define an [`ExtensionCommand`](/v/0.4.2/reference/extensions/#citry-extensioncommand), describe its arguments
with [`CommandArg`](/v/0.4.2/reference/extensions/#citry-commandarg), and list it on the extension:


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


Expose the application engine from an importable module, then run:


```bash
citry --app myproject.engine:app \
  ext run greeter greet Ada
```


Citry binds the selected engine to `self.citry` before calling `handle()`.
Accept `**kwargs` because it receives every parsed option, including options
defined by a parent command.

See [Extensions](/v/0.4.2/advanced/extensions/) for the rest of the extension API.

## Related reference

- [`Citry.inspect_components()`](/v/0.4.2/reference/citry/#citry-citry-inspect-components)
- [`ComponentCatalog`](/v/0.4.2/reference/component-introspection/#citry-componentcatalog)
- [`ExtensionCommand`](/v/0.4.2/reference/extensions/#citry-extensioncommand)
- [`CommandArg`](/v/0.4.2/reference/extensions/#citry-commandarg)
- [`CommandArgGroup`](/v/0.4.2/reference/extensions/#citry-commandarggroup)