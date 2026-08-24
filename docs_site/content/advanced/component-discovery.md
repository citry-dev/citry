---
title: Component discovery and startup
description: Find component modules and prepare Citry before serving requests.
---

# Component discovery and startup

In a small project, you can import every component module yourself. In a
larger project, Citry can find those modules for you. Point it at one or more
directories and it will import the Python files inside them.

Discovery happens automatically when Citry first needs the complete component
catalog. Production applications should usually run it during startup, before
worker threads begin serving requests.

## Put components in an importable directory

Create one [`Citry`][citry.Citry] instance in a module that every component can
import:

```python
# myproject/engine.py
from pathlib import Path

from citry import Citry

component_dir = Path(__file__).parent / "components"
app = Citry(dirs=[component_dir])
```

Then bind each component to that instance:

```citry
# myproject/components/card.py
from citry import Component

from myproject.engine import app


class Card(Component):
    class Kwargs:
        title: str

    citry = app

    template = """
      <article>
        <h2>{{ title }}</h2>
      </article>
    """
```

The directory must be importable from Python. A typical layout is:

```text
myproject/
  __init__.py
  engine.py
  components/
    __init__.py
    card.py
```

Paths passed to `Citry(dirs=...)` must be absolute. Build them from
`__file__`, as above, or call `Path(...).resolve()` before creating the
engine.

## Let Citry discover components on first use

You do not need to call discovery in a small script. Operations that need the
complete registry trigger it automatically, including rendering an unknown
component tag and inspecting the component catalog.

```python
from myproject.engine import app

catalog = app.inspect_components()
```

Each configured directory is scanned recursively. Citry imports `.py` files in
a stable order. It skips private names beginning with `_`, except
`__init__.py`, and paths whose import-name pieces contain a dot, such as
`.cache/` or `card.old.py`. Non-files are skipped too. Point discovery at the
component directory itself rather than a broad project or environment root.

Only class definitions register components. Discovery does not instantiate or
render them, and it does not load their templates, JavaScript, or CSS.

## Inspect authored component dependencies

Use [`inspect_component_graph()`][citry.Citry.inspect_component_graph] when a
tool needs to know which registered components refer to each other:

```python
from myproject.engine import app

graph = app.inspect_component_graph()

for dependency in graph.dependencies("checkout-page"):
    print(dependency.name)

for dependent in graph.dependents("price"):
    print(dependent.name)
```

The graph reads each component's effective primary template without rendering
it. `references_from()` and `references_to()` retain every authored occurrence
and its source range, while `dependencies()` and `dependents()` return unique
component definitions. Names and aliases are matched case-insensitively.

Unknown tags and dynamic `<c-component c-is="...">` targets appear in
`graph.unresolved`. A missing, unreadable, or malformed source appears in
`graph.problems` without discarding facts from other templates. Check
`graph.coverage_complete` and `graph.fully_resolved` before treating the result
as exhaustive for its documented scope.

That scope is deliberately narrower than a runtime call graph. It covers
component tags written in registered components' authored primary templates.
It does not discover components composed in Python, inserted by a
template-loading transform, or chosen dynamically at render time. Built-in
components are omitted by default; pass `include_builtins=True` to include
them. [`ComponentGraph.to_json()`][citry.ComponentGraph.to_json] produces a
versioned local-tooling document, which may contain absolute developer-machine
paths.

## Initialize before starting worker threads

Call [`initialize()`][citry.Citry.initialize] before starting worker threads.
It completes discovery and prepares validation for every registered component
tag, so configuration and import errors fail during startup rather than during
the first request.

```python
from myproject.engine import app

app.initialize()
```

Calling `initialize()` again has no effect while the registry stays unchanged.
Registering or removing a component invalidates that prepared state, so the
next call rebuilds it. If initialization raises, fix the problem and call it
again. Citry does not mark a failed initialization as complete.

Your web framework decides where startup code belongs. See
[Web frameworks](/web-frameworks/) for framework-specific setup.

## Run discovery explicitly

Use [`autodiscover()`][citry.Citry.autodiscover] when you want the imported
module names or need to discover a one-off set of directories:

```python
from myproject.engine import app

modules = app.autodiscover()
```

Pass `dirs` to replace the configured directories for that call. Unlike the
constructor setting, this one-off path may be relative to the current working
directory:

```python
modules = app.autodiscover(["plugins/components"])
```

This does not change `app.settings.dirs`. A later automatic discovery still
uses the directories configured on the engine.

## Recover from an import error

Discovery stops at the first module that cannot be imported and raises the
original exception. It remembers modules imported successfully before the
failure, so retrying does not define their components twice.

```python
try:
    app.autodiscover()
except ImportError:
    # Report the startup failure, or fix it in a development tool.
    raise
```

Do not start concurrent discovery yourself. Run
[`initialize()`][citry.Citry.initialize] once during startup, then let request
workers use the prepared engine.

## Related reference

- [`Citry`][citry.Citry]
- [`Citry.initialize()`][citry.Citry.initialize]
- [`Citry.autodiscover()`][citry.Citry.autodiscover]
- [`Citry.inspect_component_graph()`][citry.Citry.inspect_component_graph]
- [`ComponentGraph`][citry.ComponentGraph]
- [Registration](/concepts/registration/)
- [Hot reload](/guides/dev-server/)
