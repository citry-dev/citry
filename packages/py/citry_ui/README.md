# citry-ui experimental component library

This distribution is becoming Citry's first-party styled component library.
Button, Field/Input, Form, Tabs, Dialog, Combobox, and Table now have direct
styled Phase 7 implementations targeting Vuetify-level configuration and
browser behavior through native Citry APIs. The package remains pre-release
while its repository and human qualification records are completed.

The package develops against the released `citry>=0.3.1,<0.4.0` line,
which contains `LibraryComponent`, `ComponentLibrary`, typed slot data, and
the server and client context contracts used here, including the corrected
Events browser asset. The current package remains experimental because its
APIs and visual design have not completed release review.

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

The public catalog ships styled components. Headless counterparts remain
parked until applications provide concrete authoring requirements and
representative render trees.

Fill `data` is an immutable `SlotData` record. Identifier keys are available
as attributes, and the value remains a mapping for spreads and unusual keys.
A declared component `Slots` value is different: Citry constructs that
component's nested dataclass before it calls `template_data`.

Python composition calls the same imported definition:

```python
from citry_ui import CButton

button = CButton(
    loading=True,
    class_=["toolbar-action", {"is-prominent": True}],
    style={"inline-size": "100%"},
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

The first compound interactive family uses direct tags:

```html
<c-CTabs
  default_value="account"
  aria_label="Account settings"
  variant="pill"
>
  <c-CTab value="account">
    Account
  </c-CTab>
  <c-CTab value="security">
    Security
  </c-CTab>
  <c-CTabPanel value="account">
    Account preferences
  </c-CTabPanel>
  <c-CTabPanel value="security">
    Security preferences
  </c-CTabPanel>
</c-CTabs>
```

It renders the complete initial ARIA state on the server and adds pointer,
automatic/manual keyboard activation, RTL-aware focus movement, controlled
`$c-props`, including the `onValueChange` selection-request callback. Its
evolving contract is specified in
[`docs/design/ui_components/tabs.md`](https://github.com/citry-dev/citry/blob/main/docs/design/ui_components/tabs.md).
The Button contract is specified in
[`docs/design/ui_components/button.md`](https://github.com/citry-dev/citry/blob/main/docs/design/ui_components/button.md).

Python's current typing model cannot derive an exact class-call signature from
the definition's nested `Kwargs` and `Slots` schemas. Those schemas remain the
runtime validation contract. Generated stubs can add exact editor diagnostics
later without changing the publishing API.

Each family lives in one `citry_ui/components/c*/` directory. Its runtime module owns
its schemas, behavior, template, and CSS. `components/__init__.py` contains the
only ordered definition catalog, and the package root combines it with
`ComponentLibrary`. Citry owns materialization, registration rollback,
invocation resolution, and installation records.

See
[`component-authoring.md`](https://github.com/citry-dev/citry/blob/main/packages/py/citry_ui/docs/component-authoring.md)
for the spike's source-formatting rules and the required specification process
before any pressure component becomes a supported public component.
