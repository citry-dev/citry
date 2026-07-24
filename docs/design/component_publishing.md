# Component library publishing

**Status (2026-07-24): core publishing API implemented.** Citry now supports
inert `LibraryComponent` definitions, explicit `ComponentLibrary` manifests,
atomic per-Citry materialization, contextual Python composition, and immutable
installation handles. Library uninstall and live replacement remain future
lifecycle APIs. Citry UI now publishes its pressure catalog through this
contract without package-owned registration or invocation adapters.

## 1. Goals and boundaries

The publishing API lets a reusable package define each component once without
binding it to Citry's module-level default instance. An application explicitly
installs the package into each Citry instance that should receive it.

The first contract provides:

- inert package imports with no registry mutation;
- ordinary class-shaped definitions with templates, assets, schemas, methods,
  inheritance, and extension declarations;
- one distinct concrete `Component` class per definition and Citry instance;
- direct template tags and engine-neutral Python composition;
- exact installation records owned by Citry;
- complete rollback of Citry-owned registration and installation state.

The contract does not provide live uninstall, hot replacement, semantic
extension-version constraints, or exact static call signatures derived from
nested `Kwargs` and `Slots` declarations.

## 2. Library authoring

A library component uses the same authored surface as a normal `Component`,
but inherits `LibraryComponent`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from citry import ComponentLibrary, LibraryComponent, SlotInput


class CButtonHeadlessDefaultSlotData:
    attrs: dict[str, object]
    loading: bool


class CButtonHeadless(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        loading: bool = False

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CButtonHeadlessDefaultSlotData]

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        return {
            "slot_data": {
                "attrs": {
                    "aria-busy": "true" if kwargs.loading else None,
                    "disabled": kwargs.loading,
                },
                "loading": kwargs.loading,
            }
        }

    template = """
      <c-slot
        name="default"
        required
        c-bind="slot_data"
      />
    """


class CButtonDefaultSlotData:
    pass


class CButton(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs(CButtonHeadless.Kwargs):
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CButtonDefaultSlotData]

    template = """
      <c-CButtonHeadless c-loading="loading">
        <c-fill name="default" data="data">
          <button
            class="c-button"
            c-bind="data.attrs"
          >
            <c-slot />
          </button>
        </c-fill>
      </c-CButtonHeadless>
    """


__citry_library__ = ComponentLibrary(
    name="citry-ui",
    components=(CButtonHeadless, CButton),
)
```

The tuple is the complete ordered catalog. A package root exposes it through
`__citry_library__` when it wants `app.register_library(package)` support.
Code may pass the manifest itself too.

Manifest construction validates the whole catalog before publishing it. Both
catalog fields must be explicitly ordered, non-string sequences. Validation
rejects non-definition entries, empty catalogs, duplicate objects, duplicate
module and qualified-name identities, generated alias collisions, reserved
tag names, duplicate stable class IDs, and malformed extension requirements.
After validation, attributes on participating `LibraryComponent` definition
classes are sealed so class decorators can finish before manifest creation.

Python cannot deeply freeze an arbitrary class graph. From manifest creation
onward, library authors must treat the complete authored definition graph as
immutable. That includes nested declarations, plain helper bases and mixins,
and mutable values stored anywhere on those classes. Mutating that graph is
unsupported and can change already-installed behavior or make later Citry
installations differ without creating a detectable definition generation.
Release a newly defined class and manifest generation instead.

## 3. Application setup and use

Registration is an application-startup operation:

```python
import citry_ui
from citry import Citry

app = Citry()
installed = app.register_library(citry_ui)
app.initialize()
```

Templates use the normal component registry:

```html
<c-CButton loading>
  Save
</c-CButton>
<c-CButtonHeadless>
  <c-fill name="default" data="data">
    <button
      class="brand-action"
      c-bind="data.attrs"
    >
      Save
    </button>
  </c-fill>
</c-CButtonHeadless>
```

The variable named by `<c-fill data="...">` is an immutable `SlotData` record
with attribute access for identifier keys and mapping behavior for spreads and
unusual keys. This is separate from the component's declared nested `Slots`
dataclass passed to Python data methods. Slot-data type arguments are plain
shape declarations; they do not subclass or construct the runtime record.

Python imports the engine-neutral definition and calls it before an engine is
known:

```python
from citry import Component
from citry_ui import CButton

save_button = CButton(loading=False, slots={"default": "Save"})


class Toolbar(Component):
    def template_data(self, kwargs, slots):
        return {"save_button": save_button}

    template = """
      <nav>
        {{ save_button }}
      </nav>
    """
```

Calling `CButton(...)` returns a `LibraryComponentInvocation`, which implements
`ComponentLike`. During the `Toolbar` render, Citry resolves it through the
exact installed definition map for `Toolbar.citry`. Registry name lookup is
not used for this step, so an unrelated component named `CButton` can never
satisfy the invocation.

Outside a component tree, pass the engine explicitly:

```python
render = CButton(slots={"default": "Save"}).render(citry=app)
```

`render()` or `str()` without a Citry instance raises
`LibraryComponentContextError`. The reserved `slots=` argument must be a
mapping and remains separate from normal kwargs, matching ordinary Component
composition.

Advanced code can obtain the concrete class from the installation handle:

```python
BoundButton = installed.component(CButton)


class BrandedButton(BoundButton):
    name = "BrandedButton"
```

`installation[CButton]` is the equivalent concise form. `definitions` and
`classes` retain manifest order.

Static checkers see `LibraryComponent` definitions as having the ordinary
`Component` instance-authoring API, so methods such as `provide()` and
`inject()` remain available while writing a library definition. They do not
treat the inert definition as a concrete `Component` subclass: do not pass it
to APIs expecting `type[Component]` or call concrete class APIs such as
`get_template()` before installation. Python's current class-call typing still
cannot derive an exact constructor signature from nested `Kwargs` and `Slots`;
generated stubs or future typing support remain optional follow-up work.

## 4. Runtime model

Materialization uses inheritance, not namespace copying:

```text
Imported definition                      Citry A installation

CButton                                  generated CButton
  -> LibraryComponent                      -> imported CButton
                                             -> LibraryComponent
                                             -> Component
                                             -> object
```

`ComponentMeta` derives from `LibraryComponentMeta`, so Python selects the
concrete metaclass for the generated multiple-inheritance class. The generated
class keeps the definition's `__module__`, `__qualname__`, and docstring. This
preserves zero-argument `super()`, descriptors, source declarations,
module-relative assets, and stable `class_id` values. Each materialization has
a fresh `definition_id` and an immutable binding to its receiving Citry.

Nested `Kwargs`, `Slots`, output schemas, State, Events, Cache, Dependencies,
and third-party extension declarations pass through the normal ComponentMeta
and extension lifecycle. Each receiving Citry therefore gets its own effective
schemas and extension configuration.

Authored inheritance is preserved through the definition MRO, including
methods, zero-argument `super()`, and nested declarations. Two separately
materialized definitions do not gain a new concrete-class relationship:
installing both `CBase` and `CChild(CBase)` does not make the installed child
a subclass of the separately installed base. Consumers should inspect their
definition relationship or shared authored bases instead.

Introspection treats the retained module and qualified name as the logical
library-definition path. It reports the generated class's engine and runtime
generation identities alongside that logical path. The path names the inert
definition in Python source, while `LibraryInstallation.component()` returns
the live concrete class.

## 5. Registration and lifecycle contract

`Citry.register_library()` owns one root lifecycle transaction:

1. resolve the explicit manifest;
2. check an existing installation;
3. validate exact required extension names;
4. preflight registry aliases, portable definition identities, and class IDs;
5. materialize each class in manifest order through normal hooks;
6. verify exact registry and class-ID entries;
7. commit the installation record and all definition maps;
8. release lifecycle ownership.

Classes and their installation record become observable together. Another
thread receives `CitryLifecycleInProgress` during the operation. A recursive
registration attempt receives `RuntimeError`. Separate Citry instances may
install the same manifest concurrently.

Any escaping `BaseException` restores component names, class IDs, loaded-file
index entries, tag-rule state, discovery state, and every library map to their
entry snapshots. This also removes auxiliary classes that extension hooks
registered into the same Citry during the attempt. Rollback does not fire
compensating unregistration hooks.

The transaction covers Citry's registration and installation indexes listed
above. Rendered-output caches, ordinary Python side effects, extension-owned
collections, retained failed class objects, and registrations made to another
Citry instance remain outside its rollback boundary.

Repeating the same manifest with the same exact definition objects returns the
same `LibraryInstallation` and does not refire component hooks. The same
library name with changed components, requirements, or reloaded definition
objects raises `LibraryManifestChanged`. This first API never silently runs old
installed code for a newly imported definition generation. Call `clear()` and
register the new manifest during development reload or application teardown.

`Citry.clear()` retires every installation inside its normal lifecycle
operation. Old handles report `is_active == False`; their component lookup
raises `LibraryInstallationStale`. Retained invocations do not reinstall a
library implicitly. Registering again creates fresh concrete classes with the
same stable class IDs and new definition IDs.

A raw concrete class previously obtained from the advanced installation API is
not a revocable capability. If application code retains it across `clear()`,
normal Python references keep it executable even though Citry no longer
recognizes it as active. Using such a retired class is unsupported; discard
concrete classes and installation handles together at teardown. A new
generation may have the same `class_id`, while Citry's class-ID lookup correctly
points only to the new active class.

Manifest-owned registry names and their complete concrete class cannot be
removed individually. `unregister()` rejects those operations so the registry
cannot diverge from its installation record. A complete library uninstall API
must later coordinate names, caches, extension state, retained pages, and the
installation generation atomically.

## 6. Required extensions

`required_extensions` is an ordered tuple of exact lowercase extension names:

```python
ComponentLibrary(
    name="acme-controls",
    components=(CChartLegend,),
    required_extensions=("acme_theme",),
)
```

Presence is checked before any component class is created. Extra installed
extensions remain allowed and receive normal hooks. Citry has no general
extension capability or semantic-version protocol, so version expressions are
not accepted as requirement names.

## 7. Future work

The initial publishing contract deliberately leaves these as separate designs:

- atomic `unregister_library()` and hot replacement;
- compatibility negotiation between library and extension versions;
- explicit library-family metadata in component introspection;
- generated stubs or checker integrations for exact component-call types;
- tooling discovery that reads wheel metadata without importing package code;

## Related designs

- [`component_introspection.md`](component_introspection.md)
- [`component_initialization.md`](component_initialization.md)
- [`extensions.md`](extensions.md)
- [`asset_loading.md`](asset_loading.md)
- [`ui_research/library-component-feasibility.md`](ui_research/library-component-feasibility.md)
