# citry-ui experimental component library

This distribution is becoming Citry's first-party styled component library.
Its current experimental catalog is defined by the package's ordered
`COMPONENTS` manifest and the public documentation catalog rather than a
partial list in this README. The package remains pre-release while its
repository and human qualification records are completed.

The package develops against the `citry>=0.4.0,<0.5.0` source line and
`citry_core 1.5.0`. Those releases contain the framework contracts used by the
current workspace but are not yet available as the released-artifact floor.
The current package remains experimental because its dependency artifacts,
APIs, and visual design have not completed release review.

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

Citry UI's component-owned English messages automatically activate Citry's
server source mode. No i18n settings are required to render the library's
default labels: the components use the same checked `tr()` calls they use in a
localized application. To add selectable translations, named Citry UI format
profiles, or browser-side locale switching, configure the catalog package that
ships in this same wheel:

```python
app = Citry(
    autodiscover=False,
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US", "cs-CZ"),
            "catalogs": ("citry_ui_i18n", "my_app_i18n"),
        }
    },
)
app.register_library(citry_ui)
```

Place an application catalog after `citry_ui_i18n` to override selected public
keys. Components render their initial strings on the server. Under a
client-enabled `<c-i18n>` provider, stable Citry UI text and attributes follow
locale changes through `$c-tr`, while values created by component JavaScript
use the same provider through `i18n.bind()`. Explicit component label inputs or
slots always win for that instance and are not replaced after a locale switch.
Each component reference ends with a structured **Translation keys** table.

For editor completion and diagnostics without a host application, point the
Citry VS Code setting directly at the same manifest:

```json
{
  "citry.app": "citry_ui:__citry_library__"
}
```

This library-only editor registry includes Citry's built-ins and the Citry UI
catalog. A configured application instance remains the right target when
editing templates that also use application components or configuration.

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
