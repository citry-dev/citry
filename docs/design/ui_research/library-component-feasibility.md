# Library component feasibility

Status: core experiment implemented, 2026-07-24. This records the evidence and
the chosen publishing model. The normative runtime contract is now
[`component_publishing.md`](../component_publishing.md).

## 1. Outcome

`LibraryComponent` is the implemented core abstraction. Citry UI now defines
its pressure components directly with it and publishes one explicit manifest.

The desired model has two distinct stages:

1. importing a library creates inert, engine-neutral definitions;
2. `Citry.register_library(...)` atomically creates and records one concrete
   `Component` class per definition for that Citry instance.

Citry owns component identity, the installation record, materialization,
rollback, and contextual invocation resolution. Citry UI owns only its direct
definitions, ordered catalog, and manifest. Exact Python call typing remains
an independent enhancement.

`LibraryComponent` is the clearest name. `DeferredComponent` already names an
internal render-queue value, `SharedComponent` incorrectly suggests sharing a
concrete class between Citry instances, and `DeferComponent` describes timing
rather than purpose.

## 2. Intended author and user API

A library author should be able to write an ordinary-looking definition:

```python
from dataclasses import dataclass
from typing import Any

from citry import LibraryComponent, SlotInput


@dataclass(slots=True)
class CButtonHeadlessKwargs:
    loading: bool = False


@dataclass(slots=True)
class CButtonHeadlessSlots:
    default: SlotInput[dict[str, object]]


class CButtonHeadless(LibraryComponent):
    Kwargs = CButtonHeadlessKwargs
    Slots = CButtonHeadlessSlots

    template = """
      <c-slot
        name="default"
        required
        c-bind="slot_data"
      />
    """

    def template_data(
        self,
        kwargs: CButtonHeadlessKwargs,
        slots: CButtonHeadlessSlots,
    ) -> dict[str, Any]:
        return {"slot_data": {"loading": kwargs.loading}}
```

The package should publish an explicit manifest rather than rely on module
scanning:

```python
__citry_library__ = ComponentLibrary(
    name="citry-ui",
    components=(CButtonHeadless, CButton),
)
```

Application setup and both composition styles then stay small:

```python
import citry_ui
from citry import Citry
from citry_ui import CButton

app = Citry(autodiscover=False)
app.register_library(citry_ui)

button = CButton(slots={"default": "Save"})
```

```html
<c-CButton>
  Save
</c-CButton>
```

Calling the inert definition returns a generic library invocation that
implements `ComponentLike`. During rendering, that invocation resolves only
through the installation record for the active Citry instance. It must never
accept an unrelated class merely because `app.get("CButton")` finds the same
registry name.

## 3. What `LibraryComponent` must represent

The class object is a definition, not a concrete Citry `Component` class. It
must retain:

- its canonical component name;
- its stable module and qualified-name definition identity, with the manifest
  supplying library identity;
- `Kwargs`, `Slots`, and other data schemas;
- templates and assets with declaring-module provenance;
- methods, descriptors, inheritance, and zero-argument `super()` behavior;
- extension declarations such as Events, Cache, and Dependencies;
- whether it is public in the library manifest.

The installation map uses the exact definition object, while the manifest also
validates its module and qualified name as a portable identity. A reload
creates a new exact definition generation and is rejected while the earlier
generation remains installed.

## 4. Concrete class construction

Copying a definition's namespace into `type(...)` is rejected. It can break
descriptors, duplicate nested types, lose the hidden `__class__` cell used by
zero-argument `super()`, and blur asset provenance.

The implemented construction shape is multiple inheritance:

```python
class ConcreteButton(CButton, Component):
    citry = app
```

Conceptually its method-resolution order is:

```text
ConcreteButton -> engine-neutral CButton definition -> Component -> object
```

`ComponentMeta` derives from the dedicated `LibraryComponentMeta`, which makes
the definition inert and callable for composition while Python selects the
more specialized concrete metaclass for the generated class.

## 5. Landed declaration foundation

The reproducible
[`library_component_probe.py`](probes/library_component_probe.py) constructs a
plain definition with inherited `Kwargs`, `Slots`, Events, a helper base, and
zero-argument `super()`, then creates:

```python
class Bound(LibraryDefinition, HelperBase, Component):
    citry = app
```

Current results:

```text
MRO: Bound, LibraryDefinition, HelperBase, Component, object
Kwargs inherited and converted to a dataclass
Slots inherited and converted to a dataclass
Events received an engine-specific derived configuration
Dependencies inherited from the reusable definition
render succeeded
```

Run it from the repository root with:

```console
uv run --no-sync python docs/design/ui_research/probes/library_component_probe.py
```

Core now snapshots authored nested declarations before replacing component
attributes, resolves their component C3 chain, and reuses that operation for
normal components and inherited definition bases. Plain core schemas become
one effective slotted dataclass. Generic extension config classes combine the
original declaration classes without copying their namespaces. Events and
State use the same chain, while Dependencies retains its specialized
branch-based merge. Dependencies traverses reusable definition bases too and
resolves relative files from the declaration owner's module while registering
them against the concrete component.

Cross-branch schema composition is adapter-aware. Plain schemas, unslotted
dataclasses with one consistent frozen mode, compatible plain/dataclass
combinations, and Pydantic models from the same generation compose. Compatible
frozen dataclasses produce a frozen effective schema. NamedTuple branches,
more than one slotted dataclass layout, mixed frozen modes, and incompatible
mixed adapters fail explicitly instead of publishing a constructor that
silently omits fields. Once a concrete component is created, its nested
declarations cannot be rebound; a changed definition requires a new component
generation.

Class-created extension hooks receive the exact source records through
`ctx.nested_declarations(name)`. A record identifies the declaring class and
the authored class or explicit `None`, so hooks do not infer source data from
the effective runtime attribute. Validation is once per source declaration
for each receiving Citry instance and uses weak tracking.

This removed the inherited-schema and source-definition blockers from the
original spike. The core implementation now adds the inert metaclass,
validated manifest, per-Citry materialization and installation record,
transactional rollback integration, clear behavior, and an explicit reload
generation policy.

## 6. Static typing is a follow-up enhancement

Citry's current `ComponentMeta.__call__` accepts `**kwargs: Any`; mypy and
pyright do not derive an exact call signature from nested `Kwargs` and `Slots`.
Citry UI now exports direct `LibraryComponent` definitions, whose calls share
that limitation. This does not block the clean publishing API: Citry components
already rely on runtime input validation, and the library can do the same.
Exact editor diagnostics can be added later through one of:

- generated `.pyi` functions for published library components;
- generated overloads in checked source;
- a mypy and pyright integration;
- a declaration syntax compatible with `dataclass_transform` that preserves
  the desired nested schema authoring experience.

Generated stubs are the smallest plausible package-level option, but they
create an important tradeoff: typing the public name as a function makes
runtime subclassing of the definition difficult to express. That tradeoff is
separate from materializing and registering a correct runtime component.

## 7. Registration responsibilities

`Citry.register_library(...)` now:

1. resolve a `ComponentLibrary` value directly or through an explicit
   `__citry_library__` module attribute;
2. validate library identity, definition identity, canonical names, and
   duplicates before constructing anything;
3. owns one atomic registration lifecycle operation for the complete catalog;
4. create concrete classes in declared order;
5. validate exact Citry association and registration identity;
6. commits the per-Citry installation record before lifecycle ownership is
   released, after every class succeeds;
7. return the existing record on an identical repeated call;
8. reject collisions and changed manifests without partial repair.

The installation record remains necessary for contextual Python invocations,
repeated registration, collision safety, `Citry.clear()`, introspection, and
future library uninstall or replacement. It should be owned by Citry rather
than a package-global weak map once this becomes a core API.

## 8. Falsifier results

The focused core suite passes these publishing constraints:

- inert import and an explicit manifest;
- two Citry instances receiving distinct concrete classes with stable logical
  identities;
- inherited `Kwargs`, `Slots`, `TemplateData`, `JsData`, and `CssData`;
- Events, Cache, Dependencies, and an unknown third-party extension;
- methods using zero-argument `super()`, descriptors, mixins, and definition
  inheritance;
- module-relative templates, JavaScript, and CSS retaining provenance;
- internal template tags between definitions in one library;
- circular definition references that do not require import-time registration;
- preflight collision rejection, rollback for `Exception` and `BaseException`,
  hook-created auxiliary-class rollback, repeated and recursive registration,
  competing readers, `Citry.clear()`, stale handles, and module reload
  rejection while an old generation is active;
- contextual `ComponentLike` composition and collision-safe lookup;
- runtime validation for kwargs and the reserved `slots=` mapping.

## 9. Decision

The focused core experiment selected `LibraryComponentMeta`,
`ComponentLibrary`, and a Citry-owned installation record. Citry UI's direct
definitions and integration tests now exercise that API without compatibility
adapters.

The final model must preserve component and extension behavior. Exact typed
calls remain an independent enhancement and do not gate the publishing API.
The resulting normative contract is recorded in
[`component_publishing.md`](../component_publishing.md).
