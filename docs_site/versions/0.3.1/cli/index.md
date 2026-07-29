---
title: Command line
url: https://citry.dev/v/0.3.1/cli/
description: "The citry command: inspect an engine, scaffold a component, list registered components, and run extension commands."
---
# Command line

Installing citry gives you a `citry` console command. Use it to scaffold a new
component, inspect or list the components an app has registered, and run
commands that extensions ship. This page walks through each subcommand.

Run `citry --help` to see the whole tree at a glance:


```text
usage: citry [-h] [--version] {list,inspect,create,watch,ext} ...
```


Every subcommand has its own `--help`, and `citry --version` prints the
installed version:


```bash
citry --version    # e.g. citry {{ version }}
```


## Scaffold a component with citry create

`citry create <name>` writes a starter component file for you:


```bash
# Writes my_button.py containing `class MyButton(Component)`
citry create MyButton
```


The command derives a snake_case filename and a PascalCase class name from the
name you pass, so `MyButton`, `my-button`, and `my_button` all produce
`my_button.py`. An already-PascalCase name is kept verbatim on the class so
acronyms survive: `citry create HTTPServer` writes `http_server.py` with
`class HTTPServer(Component)`. On success it prints `Created <path>`.

Choose where the file lands with `--path` (or `-p`):


```bash
citry create MyButton --path ./components   # or -p ./components
```


The generated file is a working starting point (see
[Your first component](/v/0.3.1/getting-started/your-first-component/)), with a
[citry.Component](/v/0.3.1/reference/component/#citry-component) subclass, a `Kwargs` typed input class, a
`template_data` method, and a multiline `template` string.

A few things `create` deliberately will not do, each of which prints a warning
and exits without writing anything:

- It never overwrites. If `<snake_name>.py` already exists, the existing file
  is left untouched.
- It rejects a name that maps to a Python keyword (like `True`) or to a
  reserved dunder module (like `__init__`).

## Point the CLI at an engine with --app

By default the `citry` command runs against the global engine
([citry.citry](/v/0.3.1/reference/citry/#citry-citry-2)). To run against an engine you constructed
yourself, pass `--app module:attribute` (the same `module:object` convention
web-server entry points use) as the **first** argument:


```bash
# Inspect a specific app's engine
citry --app myproject.app:engine list        # components on that engine
citry --app myproject.app:engine inspect --json  # runtime catalog JSON
citry --app myproject.app:engine ext list    # extensions installed on it
```


Two rules to keep in mind:

- `--app` is recognized only as the very first argument (`--app VALUE` or
  `--app=VALUE`). Placed after a subcommand it is treated as a normal option
  and errors out.
- The target must be a [citry.Citry](/v/0.3.1/reference/citry/#citry-citry) *instance*, not the class.
  If it cannot be imported or is not a `Citry`, the command prints
  `citry: error: ...` and exits.

## Emit the runtime catalog with inspect --json

`citry inspect --json` imports the selected engine, completes normal component
autodiscovery, and prints its versioned
[citry.ComponentCatalog](/v/0.3.1/reference/component-introspection/#citry-componentcatalog) as compact JSON:


```bash
citry --app myproject.app:engine inspect --json
```


This is a runtime inventory only. If the app cannot import or discovery fails,
the command fails instead of falling back to a partial static scan. The
`--json` flag is required; bare `citry inspect` has no text format yet.

The command uses the introspection API defaults: framework built-ins are
excluded, asset paths are reported without filesystem resolution, portable
field default values are omitted, and extension-owned inspectors do not run.
Use the Python introspection API when a tool needs different options.

Catalog JSON is a local tooling artifact. It can contain absolute paths from
the developer's machine, so do not return it unchanged from an HTTP endpoint.
For clean machine-readable stdout, application modules imported by the command
must not print unrelated output during import or discovery; Citry does not
capture project output.

Static source inspection is a separate future tooling contract. It will not
serialize partially known source facts as runtime `ComponentInfo` records.

## Inspect an engine with list and ext list

`citry list` prints a table of the components registered on the engine: one
row per component, with a `name` column holding all its registered names (a
component answers to both its lowercased and kebab-case name, so `MyButton`
shows as `mybutton, my-button`), a `class` column (the class name), and a
`path` column (the file that defines it, relative to your working directory
when inside it; a component built without a source file leaves the cell
empty). Reading the runtime catalog runs autodiscovery first, so the table
reflects what the engine would actually render. Rows and additional manual
aliases use the catalog's deterministic order.


```bash
citry list
```


`citry ext list` prints the extensions installed on the engine. On the default
engine this shows the built-in `cache`, `dependencies`, and `events`
extensions:


```bash
citry ext list
```


## Run extension commands with ext run

Extensions can ship their own CLI commands. `citry ext run <extension> <command>` dispatches to them:


```bash
citry ext run <extension> <command> [args]
```


`citry ext run <extension>` with no command name prints that extension's help
instead of erroring. Only extensions that actually declare commands show up
here. On the default engine, Events exposes its `openapi` command; Cache and
Dependencies declare none. Extensions are covered in
[Extensions](/v/0.3.1/advanced/extensions/).

### Ship a command from your own extension

A command is a [citry.ExtensionCommand](/v/0.3.1/reference/extensions/#citry-extensioncommand) subclass listed
in your extension's `commands`. Declare its arguments as
[citry.CommandArg](/v/0.3.1/reference/extensions/#citry-commandarg) values and define `handle`, which receives
every parsed option as keyword arguments (so accept `**kwargs`). The engine is
bound to the command as `self.citry` before `handle` runs:


```python
from citry import Citry, CommandArg, Extension, ExtensionCommand


class Greet(ExtensionCommand):
    name = "greet"
    help = "Greet someone."
    arguments = [CommandArg("who")]

    def handle(self, **kwargs):
        print(f"hello {kwargs['who']}")
        # self.citry is the bound engine


class Greeter(Extension):
    name = "greeter"
    commands = [Greet]


engine = Citry(extensions=[Greeter])
```


With that engine exposed as `yourmod:engine`, the command is reachable as:


```bash
citry --app yourmod:engine ext run greeter greet world
# hello world
```
