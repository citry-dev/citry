---
title: Component libraries
url: https://citry.dev/v/0.3.1/advanced/share-components/
description: "Define engine-neutral Citry components, publish an explicit library manifest, register it atomically, and use it from templates or Python."
---
# Component libraries

A reusable component package should define its components once without binding
them to Citry's module-level default instance. Applications then install the
package's explicit manifest into each [`Citry`](/v/0.3.1/reference/citry/#citry-citry) instance that
should use it.

The public pieces are:

- [`LibraryComponent`](/v/0.3.1/reference/component-libraries/#citry-librarycomponent), the engine-neutral definition;
- [`ComponentLibrary`](/v/0.3.1/reference/component-libraries/#citry-componentlibrary), the ordered package manifest;
- [`Citry.register_library()`](/v/0.3.1/reference/citry/#citry-citry-register-library), the application
  startup operation; and
- [`LibraryInstallation`](/v/0.3.1/reference/component-libraries/#citry-libraryinstallation), the committed
  installation handle.

## Create the package

A small library can keep each component family in one module and publish one
ordered catalog:


```text
acme-ui/
  pyproject.toml
  src/
    acme_ui/
      __init__.py
      py.typed
      components/
        __init__.py
        cacmebadge.py
```


Install Citry as an ordinary dependency of the distribution. Applications add
the finished package directly, for example `uv add acme-ui`; a Citry optional
extra is not needed.

## Define a library component

`LibraryComponent` has the normal component authoring surface: nested schemas,
templates, data methods, assets, provide/inject, extension declarations, and
inheritance. Importing the definition does not mutate any component registry.


```citry
# src/acme_ui/components/cacmebadge.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from citry import LibraryComponent, SlotInput


class CAcmeBadgeDefaultSlotData:
    pass


class CAcmeBadge(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        tone: str = "info"
        attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CAcmeBadgeDefaultSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        return {
            "badge_class": f"acme-badge acme-badge--{kwargs.tone}",
            "attrs": kwargs.attrs,
        }

    template = """
      <span
        c-class="badge_class"
        c-bind="attrs or {}"
      >
        <c-slot />
      </span>
    """

    css = """
      .acme-badge {
        border-radius: 999px;
        padding: 0.25rem 0.625rem;
      }
    """
```


Nest `Kwargs` and `Slots` under their component so users can refer to
`CAcmeBadge.Kwargs` without two more package exports. Define distinct schema
classes for distinct components, including headless and styled variants. An
empty `Kwargs` or `Slots` class is useful for a dependable schema surface; do
not add an empty `State` unless the component actually participates in state
or event behavior.

Plain nested component schemas become slotted dataclasses when Citry creates a
concrete component class. An explicit `@dataclass(slots=True)` is useful on a
library definition when code needs to inspect or construct its schema before
registration.

Slot-data shape classes are typing contracts. They can remain plain annotated
classes and are used through `SlotInput[Shape]`; authors do not construct or
subclass the runtime [`SlotData`](/v/0.3.1/reference/slots/#citry-slotdata) record.

## Publish the manifest

List every public definition exactly once and in deterministic registration
order:


```python
# src/acme_ui/components/__init__.py
from citry import LibraryComponent

from acme_ui.components.cacmebadge import CAcmeBadge

COMPONENTS: tuple[type[LibraryComponent], ...] = (CAcmeBadge,)

__all__ = ["CAcmeBadge", "COMPONENTS"]
```


The package root exports the definitions users import and publishes the
conventional `__citry_library__` manifest:


```python
# src/acme_ui/__init__.py
from citry import ComponentLibrary

from acme_ui.components import COMPONENTS, CAcmeBadge

__citry_library__ = ComponentLibrary(
    name="acme-ui",
    components=COMPONENTS,
)

__all__ = ["CAcmeBadge", "__citry_library__"]
```


Construct the manifest after class decorators have finished. A valid manifest
seals participating definitions against later class-attribute mutation and
checks duplicate definitions, registry aliases, stable class IDs, reserved
names, and required extension names.

If every component needs particular Citry extensions, declare their exact
names on the manifest:


```python
__citry_library__ = ComponentLibrary(
    name="acme-ui",
    components=COMPONENTS,
    required_extensions=("events",),
)
```


Registration fails before creating component classes when a requirement is
missing.

## Register the library

Install the package into the application's Citry instance during startup:


```citry
import acme_ui
from citry import Citry, Component

app = Citry(autodiscover=False)
installed = app.register_library(acme_ui)


class Checkout(Component):
    citry = app
    template = """
      <main>
        <c-CAcmeBadge tone="success">
          Ready to pay
        </c-CAcmeBadge>
      </main>
    """


app.initialize()
```


You may pass the `ComponentLibrary` object itself instead of its module.
Registration creates a distinct concrete [`Component`](/v/0.3.1/reference/component/#citry-component) class
for every definition and binds it to `app`. The whole operation is atomic:
if materialization or a component hook fails, Citry restores its registry and
library indexes to their entry state.

Calling `register_library()` again with the same manifest returns the same
installation without refiring registration hooks. Reusing a library name with
a different definition generation raises
[`LibraryManifestChanged`](/v/0.3.1/reference/component-libraries/#citry-librarymanifestchanged).

## Use components in templates

Installed definitions use the ordinary component tag syntax. The class name
`CAcmeBadge` is reachable as `<c-CAcmeBadge>`, `<c-cacmebadge>`, or
`<c-c-acme-badge>` under the normal name normalization rules.

Register libraries before rendering application templates that use their
tags. Name collisions raise [`AlreadyRegistered`](/v/0.3.1/reference/citry/#citry-alreadyregistered)
instead of silently selecting an unrelated class.

Headless definitions use the same manifest and registration path. Their
component module owns behavior and exposes bindings as slot data, while the
caller's fill owns the HTML. Include each headless and styled definition in the
manifest explicitly; registering one never implies the other.

See [Slots](/v/0.3.1/concepts/slots/#scoped-slots-passing-data-to-the-fill) for the
immutable slot-data record and destructuring syntax.

## Compose components from Python

Call the same imported definition to create an engine-neutral invocation:


```citry
from citry import Component
from acme_ui import CAcmeBadge

status = CAcmeBadge(
    tone="success",
    slots={"default": "Paid"},
)


class Receipt(Component):
    citry = app
    template = """
      <aside>
        {{ status }}
      </aside>
    """

    def template_data(self, kwargs, slots):
        return {"status": status}
```


`CAcmeBadge(...)` returns a
[`LibraryComponentInvocation`](/v/0.3.1/reference/component-libraries/#citry-librarycomponentinvocation), which follows
Citry's structural [`ComponentLike`](/v/0.3.1/reference/component-libraries/#citry-componentlike) protocol. At render
time it resolves the exact imported definition through the active Citry
installation. It does not merely call `app.get("CAcmeBadge")`, so a different
component occupying the same registry name cannot satisfy it accidentally.

Outside a component render, pass the Citry instance explicitly:


```python
render = status.render(citry=app)
```


`status.render()` and `str(status)` raise
[`LibraryComponentContextError`](/v/0.3.1/reference/component-libraries/#citry-librarycomponentcontexterror) when no
Citry instance is available.

### Integrate another component-like value

Third-party values can participate in the same contextual composition by
implementing [`ComponentLike`](/v/0.3.1/reference/component-libraries/#citry-componentlike):


```python
from dataclasses import dataclass

from citry import Citry, CitryElement
from acme_ui import CAcmeBadge


@dataclass(frozen=True, slots=True)
class PaymentStatus:
    label: str
    tone: str = "info"

    def __citry_element__(self, citry: Citry, /) -> CitryElement:
        installed = citry.get_library_installation("acme-ui")
        BoundBadge = installed[CAcmeBadge]
        return BoundBadge(
            tone=self.tone,
            slots={"default": self.label},
        )
```


`PaymentStatus(...)` can now appear in `{{ ... }}` or in a slot value. Citry
calls the protocol once with the active render's exact instance. The result
must be a `CitryElement` whose component class belongs to that same instance;
returning another value or an element from another engine is an error.

## Access the installed class when necessary

Most application code should use the imported definition or its normal tag.
Advanced code can obtain the concrete class belonging to one installation:


```python
BoundBadge = installed[CAcmeBadge]

class BrandedBadge(BoundBadge):
    name = "BrandedBadge"
```


`installed.component(CAcmeBadge)` is the equivalent long form. The
installation's `definitions` and `classes` properties preserve manifest order.
After [`Citry.clear()`](/v/0.3.1/reference/citry/#citry-citry-clear), the handle is retired and component
lookup raises [`LibraryInstallationStale`](/v/0.3.1/reference/component-libraries/#citry-libraryinstallationstale).

## Ship component assets

Inline `template`, `js`, and `css` attributes need no extra package-data
configuration. File-backed `template_file`, `js_file`, and `css_file` paths are
resolved relative to the definition's source module, including after
materialization. Configure your chosen Python build backend to include those
non-Python files in both wheel and source distributions, then inspect the built
artifacts before publishing.

Build and install into a clean environment as a release check:


```bash
uv build
uv add ./dist/acme_ui-0.1.0-py3-none-any.whl
```


The application installs the published distribution directly with
`uv add acme-ui`.