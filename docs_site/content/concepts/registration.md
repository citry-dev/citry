---
title: Registration and autodiscovery
description: How citry finds and registers your components: automatic registration when a class is defined, and autodiscovery of an engine's directories.
---

# Registration and autodiscovery

Before citry can render a `<c-greeting>` tag, it has to know which component
class that tag maps to. That mapping lives in a registry, and citry fills it in
for you: a component registers itself the moment its class is defined. This page
covers when that happens, how components are grouped by engine, and how
autodiscovery imports your component files so their classes get defined in the
first place. If components themselves are new to you, start with
[Components](/concepts/components/).

## A component registers itself

A citry component is a subclass of [`Component`][citry.Component]. Defining the
class registers it: there is no decorator to add and no registration list to
maintain.

```citry
from citry import Component, citry

class Greeting(Component):
    class Kwargs:
        name: str

    template = """
      <p class="greet">Hello, {{ name }}!</p>
    """

    def template_data(self, kwargs: Kwargs, slots):
        return {"name": kwargs.name}

# Greeting is already registered; you can look it up.
assert citry.get("greeting") is Greeting
```

A component registers under its class name, normalized the way Vue normalizes
component names:

- lowercased: `MyCard` becomes `mycard`
- kebab-case: `MyCard` becomes `my-card`

For a single-word name like `Greeting`, both forms are the same (`greeting`).
Lookups are case-insensitive, so a template can reach the component as
`<c-greeting>`, and a two-word one as `<c-mycard>` or `<c-my-card>`. To register
under a different name, set the `name` attribute:

```citry
from citry import Component

class MyWidget(Component):
    name = "fancy-widget"  # usable as <c-fancy-widget>
    template = """
      <div class="widget"></div>
    """
```

Once a component is registered, every template rendered on the same engine can
use it by tag, so one component can compose another:

```citry
from citry import Component

class Page(Component):
    template = """
      <main>
        <c-greeting name="World" />
      </main>
    """

html = str(Page())
```

`str(Page())` renders the page, and the `<c-greeting>` tag resolves to the
`Greeting` class registered earlier. Looking up a name that was never registered
raises [`NotRegistered`][citry.NotRegistered]. If two components would register
under the same name, the second class definition raises
[`AlreadyRegistered`][citry.AlreadyRegistered], so a clash fails right away
instead of quietly shadowing one component with another.

## The default engine and your own

Every component is bound to one [`Citry`][citry.Citry] instance. When a
`<c-...>` tag is rendered, citry looks the name up on the engine of the
component whose template contains the tag. Components only see each other when
they share an engine.

Most projects use one engine: the shared default instance, exported as
[`citry`][citry.citry]. A component that does not set `citry` registers there,
which is why the examples above just work.

To group components on their own engine, construct a [`Citry`][citry.Citry] and
set `citry = app` in each component's class body:

```citry
from citry import Citry, Component

app = Citry()

class Button(Component):
    citry = app

    class Kwargs:
        label: str

    template = """
      <button type="button">{{ label }}</button>
    """

    def template_data(self, kwargs: Kwargs, slots):
        return {"label": kwargs.label}

# Button is on app; the default engine never sees it.
assert app.get("button") is Button
assert not citry.has("button")
```

A separate engine keeps its components, settings, and
[extensions](/advanced/extensions/) to itself, which makes it useful for
[tests](/advanced/testing/). A component class keeps the engine chosen when its
class is defined, and a subclass of a concrete component keeps that component's
engine. Use `register()` to give a class an additional name on the same engine:

```python
app.register(Button, name="primary-button")
assert app.get("primary-button") is Button
```

For a private reusable helper inside one application, a function may still
define concrete classes for the receiving engine:

```citry
def register_components(app):
    class LibraryButton(Component):
        citry = app
        name = "library-button"

        template = """
          <button>Library button</button>
        """


register_components(app)
app.initialize()
```

For a distributable component package, use engine-neutral `LibraryComponent`
definitions and one explicit `ComponentLibrary` manifest instead. Citry then
owns materialization, atomic rollback, and exact installation lookup. See
[Component libraries](/advanced/share-components/).

## Autodiscovery

For a component to register, its module has to be imported, since defining the
class is what registers it. You can import your component modules by hand, but
citry can also do it for you: give an engine a set of directories and it imports
every component module it finds under them. This is autodiscovery.

Point an engine at its component directories with `dirs`:

```python
# myproject/engine.py
from pathlib import Path

from citry import Citry

app = Citry(dirs=[Path(__file__).parent / "components"])
```

Lay the components out under that directory, each bound to `app`:

```text
myproject/
  __init__.py
  engine.py            # builds app with dirs=[.../components]
  components/
    __init__.py
    card.py            # a component bound to app
```

```citry
# myproject/components/card.py
from citry import Component

from myproject.engine import app

class Card(Component):
    citry = app

    template = """
      <div class="card">A card</div>
    """
```

The first time you look a component up or render a template on `app`, citry
imports every `.py` file under its `dirs`, which defines and registers their
component classes. From then on `<c-card>` resolves without you importing
`myproject.components.card` yourself.

Two requirements apply to every entry in `dirs`:

- **Absolute paths.** [`Citry`][citry.Citry] rejects a relative path at
  construction with a `ValueError`. Build the path from a known root, for
  example `Path(__file__).parent / "components"`.
- **Importable.** Each directory (or a parent of it) must be on Python's import
  path (`sys.path` / `PYTHONPATH`), so a file like `components/card.py` has an
  import name like `myproject.components.card`. A directory that holds component
  modules but is not importable raises a `ValueError` naming the fix.

A few more things worth knowing:

- Importing a file runs its top-level code, so keep component modules free of
  import-time side effects you would not want to run on startup.
- Only `.py` files are scanned, and their names have to be valid Python module
  names, since citry imports them by name. A file or subdirectory whose name
  starts with an underscore is skipped, except `__init__.py`.
- The default engine is created with no `dirs`, so it never scans anything on
  its own. Autodiscovery matters once you build a [`Citry`][citry.Citry] with
  `dirs`.
- Turn the automatic scan off with `autodiscover=False`:

```python
app = Citry(
    dirs=[Path(__file__).parent / "components"],
    autodiscover=False,
)
```

## Initialize before starting worker threads

A web server should finish component initialization before it starts handling
requests concurrently:

```python
from myproject.engine import app

app.initialize()
```

This gives startup a known point where Citry has:

- Imported component Python modules from `dirs` when `autodiscover=True`.
- Created and registered the built-in components.
- Built the current parse-time rules from component `Kwargs` and `Slots`.

It does not load every component's `template_file`, `js_file`, or `css_file`.
Those files remain lazy and are read when rendering needs them.

`initialize()` returns `None`. Repeated successful calls are safe, and the
registry remains mutable. If startup code registers or unregisters components
after initialization, call `initialize()` again to rebuild the invalidated tag
rules before starting workers.

The method respects `autodiscover=False`. To scan explicitly under that
setting, run the scan first:

```python
app.autodiscover()
app.initialize()
```

Lazy first use remains supported for small and single-threaded programs. If a
different thread is already discovering, registering, clearing, creating
built-ins, or building tag rules, a lifecycle operation raises
[`CitryLifecycleInProgress`][citry.CitryLifecycleInProgress] promptly. It never
waits, because waiting during a Python module import can deadlock with Python's
module-import locks. Retry after the active operation finishes, or initialize
before starting worker threads so requests only use ready state.

If initialization fails, the incomplete work remains retryable. Components
from earlier modules that imported successfully may remain registered, since
Python caches those modules and will not execute them again. Citry cannot undo
arbitrary top-level side effects from imported Python modules, so a server
should abort startup or explicitly retry after an initialization error.

## Trigger autodiscovery yourself

Autodiscovery runs automatically on first use, but you can also run it on demand
with an engine's `autodiscover` method to rescan configured directories or
import an extra directory:

```python
from myproject.engine import app

modules = app.autodiscover()  # import the modules under app's dirs
```

It returns the dotted import paths of the modules it imported, and it is safe to
call more than once. Pass `dirs` to import an extra set of directories without
changing the engine's own automatic scan:

```python
extra = ["/abs/path/to/more/components"]
app.autodiscover(dirs=extra)
```

If a component module raises while importing, citry does not mark discovery as
complete. Registrations that the failing module made to this engine are removed,
and the next lookup or `autodiscover()` call retries it. Modules that completed
before the failure remain registered. So do successfully imported dependency
modules, including their explicit registration aliases: Python caches those
dependencies and would not execute their registration code again on retry.

This recovery covers citry's registration state. It cannot undo arbitrary
Python side effects performed by the module, or registrations deliberately made
to a different [`Citry`][citry.Citry] instance. A component module also cannot
start another `autodiscover()` call while its current scan is running; doing so
raises `RuntimeError` instead of starting a nested scan.
