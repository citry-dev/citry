# citry-ui component-library spike

This distribution exercises Citry's first-party styled and headless component
model. The current Button, Field, Input, Table, and Tabs families are pressure
components, not a production component release.

Its `citry>=0.2.0,<0.3.0` dependency is a workspace placeholder, not a
compatibility claim for the published Citry 0.2.0 package. Publication must
wait for the first Citry release containing `LibraryComponent` and
`ComponentLibrary`.

Application setup installs the package's explicit manifest into one Citry
instance:

```python
import citry_ui
from citry import Citry, Component

app = Citry(autodiscover=False)
installed = app.register_library(citry_ui)


class Page(Component):
    citry = app
    template = """
      <main>
        <c-CButton type="submit">
          Save
        </c-CButton>
      </main>
    """
```

A headless component owns no HTML. Its required fill receives state and native
bindings as slot data:

```html
<c-CButtonHeadless loading>
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

Fill `data` is an immutable `SlotData` record. Identifier keys are available
as attributes, and the value remains a mapping for spreads and unusual keys.
A declared component `Slots` value is different: Citry constructs that
component's nested dataclass before it calls `template_data`.

Python composition calls the same imported definition:

```python
from citry_ui import CButton

button = CButton(
    loading=True,
    slots={"default": "Save"},
)
rendered = button.render(citry=app)
```

The result is a core `LibraryComponentInvocation`. It implements Citry's
structural `ComponentLike` protocol, so it resolves through the active Citry
instance when used inside another component tree:

```python
class Toolbar(Component):
    citry = app
    template = """
      <nav>
        {{ button }}
      </nav>
    """

    def template_data(self, kwargs, slots):
        return {"button": button}
```

Calling `str(button)` or `button.render()` without `citry=app` raises
`LibraryComponentContextError`. Contextual and explicit resolution use the
exact installed definition map, not registry-name lookup.

Advanced code can access or subclass the concrete class installed for this
Citry instance:

```python
BoundButton = installed[CButton]
```

Python's current typing model cannot derive an exact class-call signature from
the definition's nested `Kwargs` and `Slots` schemas. Those schemas remain the
runtime validation contract. Generated stubs can add exact editor diagnostics
later without changing the publishing API.

Each family lives in one `citry_ui/components/c*.py` module. That module owns
its schemas, behavior, template, and CSS. `components/__init__.py` contains the
only ordered definition catalog, and the package root combines it with
`ComponentLibrary`. Citry owns materialization, registration rollback,
invocation resolution, and installation records.

See
[`component-authoring.md`](docs/component-authoring.md)
for the spike's source-formatting rules and the required specification process
before any pressure component becomes a supported public component.
