---
title: Component libraries
description: Package components that applications can install into their own Citry instance.
---

# Component libraries

You want to publish reusable components as a Python package, such as a
design system other teams install with `pip`. An ordinary component belongs
to one [`Citry`][citry.Citry] instance, but your package cannot know which
instance each application uses.

A component library solves this. The package defines its components once,
and each application installs them into its own `Citry` instance.

For components that belong to one application, register them as usual.
A library adds nothing there.

## Lay out the package

A small library keeps its components in one package and lists them in one
place:

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

Add Citry as a normal package dependency. If a component loads its
template, JavaScript, or CSS from a file, include those files in the built
distribution as package data.

## Define a component

Subclass [`LibraryComponent`][citry.LibraryComponent] instead of
`Component`. You write it exactly like a component, but defining it does
not register it with any `Citry` instance:

```citry
# src/acme_ui/components/badge.py
from citry import LibraryComponent


class AcmeBadge(LibraryComponent):
    class Kwargs:
        label: str
        tone: str = "neutral"

    template = """
      <span c-class="['badge', 'badge--' + tone]">
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

Do not set `citry` on a library component. Each application that installs
the library gets its own copy of the class, bound to its own instance.

## Write the manifest

The manifest is a [`ComponentLibrary`][citry.ComponentLibrary] object that
names the library and lists its components, in the order Citry should
register them. Store it as `__citry_library__` in the package:

```python
# src/acme_ui/__init__.py
from citry import ComponentLibrary

from acme_ui.components.badge import AcmeBadge

__citry_library__ = ComponentLibrary(
    name="acme-ui",
    components=(AcmeBadge,),
)
```

If the components need a custom [extension](/advanced/extensions/), list
its name. Installing the library then fails if the application has not
added that extension:

```python
__citry_library__ = ComponentLibrary(
    name="acme-ui",
    components=(AcmeBadge,),
    required_extensions=("acme_theme",),
)
```

## Install the library

An application passes the package, or its manifest, to
[`register_library()`][citry.Citry.register_library]:

```python
import acme_ui
from citry import Citry

app = Citry()
installed = app.register_library(acme_ui)
```

The components then work in templates like any other registered component:

```citry-html
<c-acme-badge label="Ready" tone="success" />
```

## Use it from Python

Calling a library component records its inputs. Citry builds the actual
component when a template inserts the value, using the `Citry` instance
that renders that template:

```citry
from citry import Component

from acme_ui import AcmeBadge


class Receipt(Component):
    citry = app

    class Kwargs:
        status: str

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

Here `badge` renders through `Receipt`'s `Citry` instance. To render a
library component on its own, outside any template, pass the instance:

```python
badge = AcmeBadge(label="Ready")
html = str(badge.render(citry=app))
```

Citry checks the inputs against `Kwargs` when it builds the component, not
when you call `AcmeBadge(...)`. Your editor also cannot check the inputs
of that call, because its signature accepts any keyword arguments.

Your own Python objects can turn into components the same way. See
[Custom component values](/advanced/custom-component-values/).

## Get the bound class

Templates and library calls cover most code. When you need the actual
component class bound to your `Citry` instance, look it up on the value
`register_library()` returned:

```python
Badge = installed[AcmeBadge]
html = str(Badge(label="Ready"))
```

## Show it in the editor

The Citry VS Code extension can read the manifest directly. Point
`citry.app` at it:

```json
{
  "citry.app": "acme_ui:__citry_library__"
}
```

The editor then knows Citry's built-in components and the library's
components, but nothing from an application. If the manifest lists
`required_extensions`, point `citry.app` at a configured `Citry` instance
that installs the library instead.

## Publishing rules

### Edit classes first

Creating the manifest locks its components. Setting or deleting a class
attribute afterwards raises `AttributeError`. Values stored inside an
attribute, such as a list, are not locked, so treat the whole component
as read-only from then on. Apply class decorators before you create the
manifest.

### Failed installs

If validation, a name clash, or an extension hook raises during
`register_library()`, Citry removes every component the call had
registered. It cannot undo side effects outside Citry, such as a file an
import or a hook wrote.

### Installing again

Registering the same manifest again returns the existing installation. To
install a changed or reloaded version under the same name, call
[`Citry.clear()`][citry.Citry.clear] and run your normal application
startup again. Without the clear, `register_library()` raises
[`LibraryManifestChanged`][citry.LibraryManifestChanged].

### Old handles expire

After `Citry.clear()`, the value `register_library()` returned earlier no
longer gives out classes.
Looking one up raises
[`LibraryInstallationStale`][citry.LibraryInstallationStale], so you never
get a class from a library that is no longer installed.

## Related reference

- [`LibraryComponent`][citry.LibraryComponent]
- [`LibraryComponentInvocation`][citry.LibraryComponentInvocation]
- [`ComponentLibrary`][citry.ComponentLibrary]
- [`LibraryInstallation`][citry.LibraryInstallation]
- [`Citry.register_library()`][citry.Citry.register_library]
