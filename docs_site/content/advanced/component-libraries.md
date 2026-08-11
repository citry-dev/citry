---
title: Component libraries
description: Package components that applications can install into their own Citry instance.
---

# Component libraries

A component library lets you publish reusable Citry components without
choosing the application's engine. The package defines components once, and
each application installs them into its own [`Citry`][citry.Citry] instance.

Use a library when components need to travel as a Python package. For
components that belong to one application, ordinary registration is simpler.

## Create the package

A small library can keep its definitions together and publish one manifest:

```text
acme-ui/
  pyproject.toml
  src/
    acme_ui/
      __init__.py
      py.typed
      components/
        __init__.py
        badge.py
```

Add Citry as a normal package dependency. Include file-backed templates,
JavaScript, and CSS in the built distribution as package data.

## Define a library component

Subclass [`LibraryComponent`][citry.LibraryComponent] instead of `Component`.
It has the same component authoring API, but defining it does not register it
with an engine.

```citry
# src/acme_ui/components/badge.py
from citry import LibraryComponent


class AcmeBadge(LibraryComponent):
    class Kwargs:
        label: str
        tone: str = "neutral"

    template = """
      <span class="badge badge--{{ tone }}">
        {{ label }}
      </span>
    """

    css = """
      .badge {
        border-radius: 999px;
        padding: 0.25rem 0.6rem;
      }
    """
```

Do not set `citry` on a library definition. Citry creates a separate concrete
component class for every engine that installs the library.

## Publish the manifest

List the definitions in a [`ComponentLibrary`][citry.ComponentLibrary], in the
order Citry should register them:

```python
# src/acme_ui/__init__.py
from citry import ComponentLibrary

from acme_ui.components.badge import AcmeBadge

__citry_library__ = ComponentLibrary(
    name="acme-ui",
    components=(AcmeBadge,),
)
```

Construct the manifest after decorators have finished changing the component
classes. Creating it seals the definitions against later top-level class
attribute changes. Objects stored inside an attribute are not deeply frozen,
so library code should treat the entire definition as immutable after this
point.

If the components rely on a custom extension, declare its exact name:

```python
__citry_library__ = ComponentLibrary(
    name="acme-ui",
    components=(AcmeBadge,),
    required_extensions=("acme_theme",),
)
```

Installation fails before publishing any component if a required extension is
missing.

## Use the library catalog in the editor

The Citry VS Code extension accepts the manifest itself as its registry target:

```json
{
  "citry.app": "acme_ui:__citry_library__"
}
```

The language server creates a library-only registry containing Citry's
built-ins and the manifest's components. It does not include host-application
components, configuration, or host-provided extensions. If the manifest has a
custom `required_extensions` entry, expose a configured `Citry` instance that
installs the library and select that instance instead.

## Install and use the library

Applications pass either the package or its manifest to
[`register_library()`][citry.Citry.register_library]:

```python
import acme_ui
from citry import Citry

app = Citry()
installed = app.register_library(acme_ui)
```

The component now works like any other registered component:

```citry-html
<c-acme-badge label="Ready" tone="success" />
```

Installation is atomic for state owned by Citry. If validation, a name
collision, or a registration hook raises, Citry restores its component and
library registries. It cannot undo outside effects performed by package imports
or extension hooks, such as writing a file or changing another global.

Register the same manifest again and Citry returns the existing installation.
To install a changed or reloaded generation with the same name, clear the
engine first and perform normal application startup again.

## Compose a library component from Python

Calling a library definition stores the inputs until an active engine is
known:

```citry
from citry import Component

from acme_ui import AcmeBadge


class Receipt(Component):
    class Kwargs:
        status: str

    citry = app

    def template_data(self, kwargs: Kwargs, slots):
        return {
            "badge": AcmeBadge(
                label=kwargs.status,
                tone="success",
            ),
        }

    template = """
      <p>Status: {{ badge }}</p>
    """
```

When Citry inserts `badge`, it resolves the call through `Receipt`'s engine.
Outside a component tree, pass the engine explicitly:

```python
badge = AcmeBadge(label="Ready")
html = str(badge.render(citry=app))
```

Library calls retain the definition's broad Python signature rather than
generating an exact call signature from `Kwargs`. Component input validation
still runs when the call is resolved.

Other Python objects can take part in this contextual conversion too. See
[Custom component values](/advanced/custom-component-values/).

## Access the installed component class

Most code should use the template tag or call the library definition. When you
need the concrete class bound to one engine, use the installation handle:

```python
Badge = installed[AcmeBadge]
html = str(Badge(label="Ready"))
```

An installation handle becomes stale after
[`Citry.clear()`][citry.Citry.clear] or when another generation replaces it.
Accessing its classes then raises
[`LibraryInstallationStale`][citry.LibraryInstallationStale] instead of
returning a class that no longer belongs to the active registry.

## Related reference

- [`LibraryComponent`][citry.LibraryComponent]
- [`LibraryComponentInvocation`][citry.LibraryComponentInvocation]
- [`ComponentLibrary`][citry.ComponentLibrary]
- [`LibraryInstallation`][citry.LibraryInstallation]
- [`Citry.register_library()`][citry.Citry.register_library]
