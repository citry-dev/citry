# Citry UI

Citry UI is Citry's own styled component library.

It gives you the building blocks for polished application interfaces without
assembling a separate frontend component stack:

- forms, navigation, dialogs, menus, feedback, layout, and data display;
- accessible HTML with keyboard and pointer interactions;
- useful server-rendered output before browser behavior starts;
- consistent light and dark styling with theme variables and component parts;
- built-in labels that applications can translate and override; and
- Python composition alongside ordinary Citry template tags.

Browse the [component catalog](https://citry.dev/ui-library/) for current
guides and API references.

## Alpha release

Citry UI is in alpha.

Components that already exist won't be removed (for example, `CButton` stays
`CButton`), but component inputs may yet change before v1.0.

## Installation

Install it with Python 3.10 or newer. Needs `citry>=0.4.2`:

```console
python -m pip install citry-ui
```

## Usage

Register components with `Citry.register_library()`:

```python
import citry_ui
from citry import Citry, Component

app = Citry()
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

You can also directly import the components:

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

See [`docs/design/ui_components/button.md`](https://github.com/citry-dev/citry/blob/main/docs/design/ui_components/button.md).

Note: Calling `str(button)` or `button.render()` without `citry=app` raises
`LibraryComponentContextError`.

## Locales

To add selectable translations, named Citry UI format
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

## Subclassing

Advanced code can access or subclass the concrete class installed for this
Citry instance:

```python
import citry_ui
from citry import Citry, Component

app = Citry()
installed = app.register_library(citry_ui)
...
BoundButton = installed[CButton]
```

## Development

Each family lives in one `citry_ui/components/c*/` directory. Its runtime module owns
its schemas, behavior, template, and CSS. `components/__init__.py` contains the
only ordered definition catalog, and the package root combines it with
`ComponentLibrary`. Citry owns materialization, registration rollback,
invocation resolution, and installation records.

For editor completion and diagnostics without a host application, point the
Citry VS Code setting directly at the same manifest:

```json
{
  "citry.app": "citry_ui:__citry_library__"
}
```

Contributors can read the
[component-authoring guide](https://github.com/citry-dev/citry/blob/main/packages/py/citry_ui/docs/component-authoring.md)
for the specification and source-formatting rules.

## Early-access feedback

Please report bugs, missing component states, accessibility problems, and API
friction in the [Citry issue tracker](https://github.com/citry-dev/citry/issues).
Include the component name, Citry UI version, browser, and a small reproduction
when possible.
