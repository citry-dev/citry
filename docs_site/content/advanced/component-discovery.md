---
title: Discovery and startup
description: Find component modules and prepare Citry before serving requests.
---

# Discovery and startup

A component becomes available to templates when Python runs its `class`
statement, which happens when its module is imported. In a small project you
can import every component module yourself. In a larger one, tell Citry
which directories hold your components, and it imports the Python files in
them for you. This is called discovery.

Discovery runs on its own the first time Citry needs the full list of
components. In a web app, also call
[`initialize()`][citry.Citry.initialize] at startup, so that a broken
component fails before the first request rather than during it.

## Set the component dirs

Create one [`Citry`][citry.Citry] instance in a module that every component
can import, and pass it your component directory in `dirs`:

```python
# myproject/engine.py
from pathlib import Path

from citry import Citry

component_dir = Path(__file__).parent / "components"
app = Citry(dirs=[component_dir])
```

Bind each component to that instance:

```citry
# myproject/components/card.py
from citry import Component

from myproject.engine import app


class Card(Component):
    citry = app

    class Kwargs:
        title: str

    template = """
      <article>
        <h2>{{ title }}</h2>
      </article>
    """
```

The directory must be importable from Python, as in this layout:

```text
myproject/
  __init__.py
  engine.py
  components/
    __init__.py
    card.py
```

A directory that holds component modules but cannot be imported raises
`ValueError` during discovery.

Paths in `dirs` must be absolute; a relative path raises `ValueError`.
Build them from `__file__`, as above, or call `Path(...).resolve()`.

Citry also looks in `dirs` for files that components name, such as a
`template_file`, after looking next to the component's own module.

## Discover on first use

You do not need to start discovery yourself. Citry runs it the first time
it needs the full list of components, for example when a template uses a
component tag that is not registered yet, or when you inspect the
components:

```python
from myproject.engine import app

catalog = app.inspect_components()
```

Citry searches each directory, including subdirectories, and imports every
`.py` file in a fixed order. It skips:

- files and directories whose names start with `_`, except `__init__.py`;
- names that Python cannot import: a file with another dot besides `.py`,
  such as `card.old.py`, or a directory with a dot in its name, such as
  `.cache/`.

Point `dirs` at the component directory itself, not at the project root or
a virtual environment, so Citry imports only component modules.

Importing a module only registers its classes. Citry does not render the
components or read their template, JavaScript, or CSS files until a page
needs them.

## `initialize()` at startup { #initialize-before-starting-worker-threads }

Call [`initialize()`][citry.Citry.initialize] once at startup, before your
server starts handling requests:

```python
from myproject.engine import app

app.initialize()
```

It runs discovery and reads every component's inputs and slots, so Citry
can check each component tag in a template. An import error or invalid
component then stops startup, instead of failing the first request that
needs it.

Calling `initialize()` again does nothing unless components were added or
removed since; then it prepares them again. If it raises, fix the problem
and call it again.

Start discovery from one place, at startup. A second thread that starts
discovery or `initialize()` while one is running raises
[`CitryLifecycleInProgress`][citry.CitryLifecycleInProgress].

[Web frameworks](/advanced/web-frameworks/) shows where startup code goes in each
framework.

## Run discovery yourself

Call [`autodiscover()`][citry.Citry.autodiscover] when you want the names
of the modules it imported:

```python
modules = app.autodiscover()
```

Pass a list of directories to import components from other places, such as
plugins, on demand. These paths may be relative to the current working
directory:

```python
modules = app.autodiscover(["plugins/components"])
```

This does not change `app.settings.dirs`, and it does not count as the
automatic first-use discovery, which still searches the configured `dirs`.

## Fix an import error

Discovery stops at the first module that fails to import and raises that
module's exception. Components from modules imported before it stay
registered. Components that the failing module registered before the error
are removed, so after you fix the module, calling discovery again imports
it cleanly.

## List component usage

Tools such as linters or documentation generators sometimes need to know
which components use which. Call
[`inspect_component_graph()`][citry.Citry.inspect_component_graph]:

```python
graph = app.inspect_component_graph()

for dependency in graph.dependencies("checkout-page"):
    print(dependency.name)

for dependent in graph.dependents("price"):
    print(dependent.name)
```

`dependencies()` lists each component that a component's template uses,
and `dependents()` lists each component whose template uses it. Each
component appears once, however many times the template uses it.

To get every single use instead, such as each `<c-Price>` written in a
template, with its file, line, and column, call `references_from()` and
`references_to()`.

You can name a component in any letter case or with hyphens between
words: `"CheckoutPage"` and `"checkout-page"` find the same component.

The graph reads each registered component's template without rendering it.
It does not see components that Python code creates, or that a template
chooses at render time with `<c-component c-is="...">`. Built-in components
are left out unless you pass `include_builtins=True`.

Before you treat the graph as complete, check two flags:

- `graph.coverage_complete` is false when a template could not be read or
  parsed. `graph.problems` lists those templates.
- `graph.fully_resolved` is also false when a template uses an unknown tag
  or a dynamic component. `graph.unresolved` lists those uses.

[`ComponentGraph.to_json()`][citry.ComponentGraph.to_json] writes the
graph as JSON for other tools. The JSON can contain absolute file paths
from your machine, so check it before you share it.

## Related reference

- [`Citry`][citry.Citry]
- [`Citry.initialize()`][citry.Citry.initialize]
- [`Citry.autodiscover()`][citry.Citry.autodiscover]
- [`Citry.inspect_component_graph()`][citry.Citry.inspect_component_graph]
- [`ComponentGraph`][citry.ComponentGraph]
- [Registration](/concepts/registration/)
- [Hot reload](/guides/dev-server/)
