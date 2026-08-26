---
title: Icon
url: https://citry.dev/v/0.4.4/ui-library/components/icon/
description: "Render a consistent, accessible set of local SVG symbols with Citry UI Icon."
---
# Icon

Use `CIcon` for a bundled symbol that follows the surrounding text color and
size. It renders inline SVG from Citry UI itself, so it needs no font, network
request, client runtime, or JavaScript icon package.

## Icon at a glance

Icons are decorative by default. Put them beside visible text and let that
text carry the meaning.


### Icon at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/icon/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconAtAGlance(Component):
    template = """
      <section class="icon-glance" aria-label="Botanical field notes">
        <article>
          <c-CIcon name="search" size="lg" />
          <div>
            <strong>Canopy survey</strong>
            <span>Search the northern transect</span>
          </div>
        </article>
        <article>
          <c-CIcon name="leaf" size="lg" />
          <div>
            <strong>Silver fern</strong>
            <span>Three new fronds recorded</span>
          </div>
        </article>
        <article>
          <c-CIcon name="calendar" size="lg" />
          <div>
            <strong>Next observation</strong>
            <span>At first light on 14 August</span>
          </div>
        </article>
        <article class="icon-glance__status">
          <c-CIcon name="success" size="lg" />
          <div>
            <strong>Specimen verified</strong>
            <span>Matched to the field key</span>
          </div>
        </article>
      </section>
    """

    css = """
      :where(.icon-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 0.75rem;
        max-width: 68rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-glance article) {
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#cbd5c0, #3e5b3a);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.icon-glance [data-citry-ui-part="icon"]) {
        margin-block-start: 0.1rem;
        color: light-dark(#2f6f3e, #80d49a);
      }

      :where(.icon-glance strong, .icon-glance span) {
        display: block;
      }

      :where(.icon-glance span) {
        margin-block-start: 0.2rem;
        color: light-dark(#52604e, #b8c9b5);
        font-size: 0.875rem;
      }
    """


preview = IconAtAGlance()

preview  # noqa: B018
````



```citry-html
<p>
  <c-CIcon name="leaf" />
  Silver fern
</p>
```


Compose the same Icon in Python:


```python
from citry_ui import CIcon

leaf = CIcon(name="leaf")
```


## Browse the catalog

The initial catalog favors common actions, navigation, status, and objects.
Semantic aliases such as `success`, `warn`, and `close` keep application code
about meaning rather than one particular drawing.


### Browse bundled Icons

[Open the rendered preview](/v/0.4.4/ui-library/components/icon/_previews/catalog/)

````citry
from dataclasses import dataclass

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


@dataclass(frozen=True, slots=True)
class IconGroup:
    title: str
    names: tuple[str, ...]


class IconCatalog(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="icon-catalog">
        <c-for each="group in groups">
          <section>
            <h2>{{ group.title }}</h2>
            <ul>
              <c-for each="name in group.names">
                <li>
                  <c-CIcon c-name="name" size="lg" />
                  <code>{{ name }}</code>
                </li>
              </c-for>
            </ul>
          </section>
        </c-for>
      </section>
    """

    css = """
      :where(.icon-catalog) {
        display: grid;
        gap: 1.25rem;
        max-width: 72rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-catalog h2) {
        margin: 0 0 0.6rem;
        color: light-dark(#285c36, #8bdd9f);
        font-size: 0.875rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.icon-catalog ul) {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(9.5rem, 1fr));
        gap: 0.35rem;
        margin: 0;
        padding: 0;
        list-style: none;
      }

      :where(.icon-catalog li) {
        display: flex;
        gap: 0.55rem;
        align-items: center;
        min-width: 0;
        padding: 0.55rem 0.65rem;
        border: 1px solid light-dark(#d9e2d4, #38513a);
        border-radius: 0.5rem;
        background: Canvas;
      }

      :where(.icon-catalog code) {
        overflow-wrap: anywhere;
        font-size: 0.75rem;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "groups": (
                IconGroup(
                    "Actions",
                    (
                        "check",
                        "close",
                        "copy",
                        "download",
                        "edit",
                        "plus",
                        "minus",
                        "refresh-cw",
                        "search",
                        "trash",
                        "upload",
                    ),
                ),
                IconGroup(
                    "Navigation",
                    (
                        "arrow-down",
                        "arrow-left",
                        "arrow-right",
                        "arrow-up",
                        "chevron-down",
                        "chevron-left",
                        "chevron-right",
                        "chevron-up",
                        "back",
                        "forward",
                        "prev",
                        "next",
                        "external-link",
                        "home",
                        "menu",
                        "more-horizontal",
                        "more-vertical",
                    ),
                ),
                IconGroup(
                    "Status and meaning",
                    (
                        "circle-check",
                        "circle-help",
                        "circle-info",
                        "circle-x",
                        "triangle-alert",
                        "success",
                        "info",
                        "warn",
                        "danger",
                        "expand",
                        "collapse",
                        "dropdown",
                        "clear",
                    ),
                ),
                IconGroup(
                    "Objects",
                    (
                        "calendar",
                        "clock",
                        "eye",
                        "eye-off",
                        "file",
                        "folder",
                        "heart",
                        "leaf",
                        "link",
                        "lock",
                        "mail",
                        "settings",
                        "star",
                        "unlock",
                        "user",
                        "x",
                    ),
                ),
            )
        }


preview = IconCatalog()

preview  # noqa: B018
````


Names are a versioned public contract. Unknown names fail during server render
instead of leaving a blank placeholder.

## Match size and color

`sm`, `md`, and `lg` scale with nearby type. Icons inherit `currentColor`, so
ordinary text color utilities and component intent colors work without an
Icon-specific color input.


### Set Icon size and color

[Open the rendered preview](/v/0.4.4/ui-library/components/icon/_previews/size-and-color/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconSizeAndColor(Component):
    template = """
      <section class="icon-scale">
        <article>
          <h2>Preset sizes</h2>
          <p><c-CIcon name="leaf" size="sm" /> Small seedling</p>
          <p><c-CIcon name="leaf" /> Mature frond</p>
          <p><c-CIcon name="leaf" size="lg" /> Canopy specimen</p>
        </article>
        <article class="icon-scale__seasons">
          <h2>Inherited color</h2>
          <p class="icon-scale__spring"><c-CIcon name="leaf" /> Spring</p>
          <p class="icon-scale__summer"><c-CIcon name="leaf" /> Summer</p>
          <p class="icon-scale__autumn"><c-CIcon name="leaf" /> Autumn</p>
        </article>
        <article>
          <h2>Exact local override</h2>
          <p><c-CIcon name="leaf" style="--cui-icon-size: 2rem" /> Alpine frond</p>
        </article>
      </section>
    """

    css = """
      :where(.icon-scale) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-scale article) {
        padding: 1rem;
        border: 1px solid light-dark(#d4ddce, #40533e);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.icon-scale h2) {
        margin: 0 0 0.75rem;
        font-size: 0.9rem;
      }

      :where(.icon-scale p) {
        display: flex;
        gap: 0.55rem;
        align-items: center;
        margin: 0.6rem 0;
      }

      :where(.icon-scale__spring) {
        color: #16a34a;
      }

      :where(.icon-scale__summer) {
        color: #15803d;
      }

      :where(.icon-scale__autumn) {
        color: #c2410c;
      }
    """


preview = IconSizeAndColor()

preview  # noqa: B018
````


Set `--cui-icon-size` for an exact local size. Use `class_` and `style` directly
for routine root styling.

## Give standalone Icons meaning

Pass `label` only when the Icon must communicate without nearby text. It adds
`role="img"` and `aria-label`. Without `label`, the Icon has
`aria-hidden="true"`.


### Choose decorative or meaningful semantics

[Open the rendered preview](/v/0.4.4/ui-library/components/icon/_previews/meaning/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconMeaning(Component):
    template = """
      <section class="icon-meaning">
        <article>
          <h2>Visible text carries meaning</h2>
          <p class="icon-meaning__notice">
            <c-CIcon name="warn" size="lg" />
            Frost is expected above the tree line.
          </p>
          <code>aria-hidden="true"</code>
        </article>
        <article>
          <h2>Icon stands alone</h2>
          <div class="icon-meaning__weather">
            <c-CIcon name="leaf" size="lg" label="Good growing conditions" />
          </div>
          <code>role="img" aria-label="Good growing conditions"</code>
        </article>
      </section>
    """

    css = """
      :where(.icon-meaning) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 58rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-meaning article) {
        padding: 1rem;
        border: 1px solid light-dark(#d8dac7, #55563a);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.icon-meaning h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.icon-meaning__notice) {
        display: flex;
        gap: 0.6rem;
        align-items: center;
        color: light-dark(#9a3412, #fdba74);
      }

      :where(.icon-meaning__weather) {
        display: grid;
        place-items: center;
        min-block-size: 4rem;
        color: light-dark(#15803d, #86efac);
        font-size: 2rem;
      }

      :where(.icon-meaning code) {
        font-size: 0.72rem;
        overflow-wrap: anywhere;
      }
    """


preview = IconMeaning()

preview  # noqa: B018
````


Do not repeat visible text in `label`. An Icon never enters the focus order and
does not own a click action.

## Compose Icons with controls

Put Icons inside the decoration slots of the component that owns the action.
The Button keeps the accessible name, focus, keyboard behavior, loading state,
and target size.


### Compose Icons with Buttons

[Open the rendered preview](/v/0.4.4/ui-library/components/icon/_previews/composition/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconComposition(Component):
    template = """
      <section class="icon-composition">
        <div class="icon-composition__actions">
          <c-CButton variant="outline" intent="neutral">
            <c-fill name="start">
              <c-CIcon name="search" />
            </c-fill>
            <c-fill name="default">
              Search specimens
            </c-fill>
          </c-CButton>
          <c-CButton intent="success">
            <c-fill name="start">
              <c-CIcon name="success" />
            </c-fill>
            <c-fill name="default">
              Save field note
            </c-fill>
          </c-CButton>
          <c-CButton variant="ghost">
            <c-fill name="default">
              Next trail
            </c-fill>
            <c-fill name="end">
              <c-CIcon name="next" />
            </c-fill>
          </c-CButton>
          <c-CButton
            variant="outline"
            intent="neutral"
            c-attrs="{'aria-label': 'Open field settings'}"
          >
            <c-CIcon name="settings" />
          </c-CButton>
        </div>
        <p class="icon-composition__warning">
          <c-CIcon name="warn" />
          The western footbridge is closed after rain.
        </p>
      </section>
    """

    css = """
      :where(.icon-composition) {
        display: grid;
        gap: 1rem;
        max-width: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-composition__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.65rem;
        align-items: center;
      }

      :where(.icon-composition__warning) {
        display: flex;
        gap: 0.55rem;
        align-items: center;
        width: fit-content;
        margin: 0;
        padding: 0.75rem 0.9rem;
        border-inline-start: 0.25rem solid light-dark(#d97706, #fbbf24);
        color: light-dark(#78350f, #fde68a);
        background: light-dark(#fffbeb, #451a03);
      }
    """


preview = IconComposition()

preview  # noqa: B018
````


For an icon-only action, name the Button through its `attrs`. Do not attach an
event listener or `tabindex` to `CIcon`.

## Use physical and logical direction

Physical names such as `arrow-left` always point the same way. Logical names
`back`, `forward`, `prev`, and `next` mirror automatically in right-to-left
content.


### Compare physical and logical direction

[Open the rendered preview](/v/0.4.4/ui-library/components/icon/_previews/direction/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconDirection(Component):
    template = """
      <section class="icon-direction">
        <article dir="ltr">
          <h2>Left to right</h2>
          <dl>
            <div><dt>Physical left</dt><dd><c-CIcon name="arrow-left" size="lg" /></dd></div>
            <div><dt>Back</dt><dd><c-CIcon name="back" size="lg" /></dd></div>
            <div><dt>Forward</dt><dd><c-CIcon name="forward" size="lg" /></dd></div>
            <div><dt>Next</dt><dd><c-CIcon name="next" size="lg" /></dd></div>
          </dl>
        </article>
        <article dir="rtl">
          <h2>Right to left</h2>
          <dl>
            <div><dt>Physical left</dt><dd><c-CIcon name="arrow-left" size="lg" /></dd></div>
            <div><dt>Back</dt><dd><c-CIcon name="back" size="lg" /></dd></div>
            <div><dt>Forward</dt><dd><c-CIcon name="forward" size="lg" /></dd></div>
            <div><dt>Next</dt><dd><c-CIcon name="next" size="lg" /></dd></div>
          </dl>
        </article>
      </section>
    """

    css = """
      :where(.icon-direction) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-direction article) {
        padding: 1rem;
        border: 1px solid light-dark(#d4ddce, #40533e);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.icon-direction h2) {
        margin: 0 0 0.8rem;
        font-size: 0.95rem;
      }

      :where(.icon-direction dl) {
        display: grid;
        gap: 0.45rem;
        margin: 0;
      }

      :where(.icon-direction dl div) {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.4rem 0.55rem;
        border-radius: 0.4rem;
        background: light-dark(#f1f6ee, #233526);
      }

      :where(.icon-direction dt) {
        font-size: 0.85rem;
      }

      :where(.icon-direction dd) {
        margin: 0;
        color: light-dark(#236538, #7bd596);
      }
    """


preview = IconDirection()

preview  # noqa: B018
````


Choose a logical name for reading or navigation order. Choose a physical name
when the direction itself is the content, such as a compass or diagram.

## Theme and customize Icon

Icon follows the surrounding `color-scheme`. Override the two documented CSS
variables on an ancestor or one Icon; use the public part selector for targeted
root styling.


### Customize Icon

[Open the rendered preview](/v/0.4.4/ui-library/components/icon/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconCustomization(Component):
    template = """
      <section class="field-keys">
        <article class="field-key field-key--light">
          <h2>Day survey key</h2>
          <p><c-CIcon name="leaf" /> Native species</p>
          <p><c-CIcon name="circle-help" /> Identity uncertain</p>
          <p><c-CIcon name="warn" /> Habitat under pressure</p>
        </article>
        <article class="field-key field-key--dark">
          <h2>Night survey key</h2>
          <p><c-CIcon name="leaf" /> Native species</p>
          <p><c-CIcon name="circle-help" /> Identity uncertain</p>
          <p><c-CIcon name="warn" /> Habitat under pressure</p>
        </article>
      </section>
    """

    css = """
      :where(.field-keys) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 54rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.field-key) {
        --cui-icon-size: 1.25rem;
        --cui-icon-stroke-width: 1.6;
        padding: 1rem;
        border: 1px solid currentColor;
        border-radius: 0.75rem;
      }

      :where(.field-key--light) {
        color-scheme: light;
        color: #20452a;
        background: #f4f9f1;
      }

      :where(.field-key--dark) {
        color-scheme: dark;
        color: #d7f3dc;
        background: #172b1c;
      }

      :where(.field-key h2) {
        margin: 0 0 0.8rem;
        font-size: 0.95rem;
      }

      :where(.field-key p) {
        display: flex;
        gap: 0.65rem;
        align-items: center;
        margin: 0.6rem 0;
      }

      :where(.field-key [data-citry-ui-part="icon"]) {
        color: light-dark(#15803d, #86efac);
      }

      :where(.field-key [data-name="warn"]) {
        color: light-dark(#b45309, #fcd34d);
      }
    """


preview = IconCustomization()

preview  # noqa: B018
````



```css
.field-key {
  --cui-icon-size: 1.4rem;
  --cui-icon-stroke-width: 1.6;
}

.field-key [data-citry-ui-part="icon"] {
  color: #15803d;
}
```


The documented variables, part, and reflected attributes are public CSS API.
`.cui-*` classes and `--_cui-*` variables are private.

## Accessibility and security

Decorative and meaningful semantics are decided on the server and work without
JavaScript. The SVG is non-interactive, ignores pointer events, and contains
only reviewed package-owned geometry.

`attrs` accepts inert metadata but rejects executable Alpine and Citry
directives, event attributes, geometry, focus controls, and accessible-name
overrides. Citry runtime data namespaces are reserved. Trusted
`Markup`/`__html__` values are rejected across every input, including nested
class, style, and attribute structures. `CIcon` is not a raw SVG escape hatch.

## API reference

### Inputs

#### CIcon server inputs

Server inputs are passed in a template through `<c-CIcon ... />` or in Python through
`CIcon(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="icon-input-cicon-server-inputs-name"></span>`name` | `CIconName` ([`CIconName`](#icon-interface-input-type-aliases-cicon-name)) | required | Selects one bundled visual glyph or semantic alias. |
| <span id="icon-input-cicon-server-inputs-label"></span>`label` | `str | None` | `None` | Gives a standalone Icon `img` semantics and this escaped accessible name. Omit it when visible text already explains the Icon. Trusted HTML values are rejected. |
| <span id="icon-input-cicon-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CIconSize`](#icon-interface-input-type-aliases-cicon-size)) | `"md"` | Sets the Icon to 0.875em, 1em, or 1.25em before CSS-variable overrides. |
| <span id="icon-input-cicon-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#icon-interface-input-type-aliases-class-value)) | `None` | Adds root SVG classes from a string, conditional mapping, or nested sequence and merges them with `attrs`. |
| <span id="icon-input-cicon-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#icon-interface-input-type-aliases-style-value)) | `None` | Adds root SVG inline styles from CSS text, a property mapping, or nested sequence and merges them with `attrs`. |
| <span id="icon-input-cicon-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds inert root SVG metadata such as `id`, `lang`, `dir`, `hidden`, `aria-describedby`, `aria-details`, and consumer `data-*` attributes. Geometry, naming, focus, executable directives, event bindings, reserved Citry runtime attributes, and trusted HTML values at any supported nesting depth are rejected. |

</div>

### Slots

-

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CIcon CSS variables

Apply these variables to `CIcon` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="icon-css-cicon-css-variables-cui-icon-size"></span>`--cui-icon-size` | `length` | Overrides the rendered inline and block size. | `Size-derived em length.` |
| <span id="icon-css-cicon-css-variables-cui-icon-stroke-width"></span>`--cui-icon-stroke-width` | `number` | Overrides the Lucide line weight. | `2` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CIcon attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="icon-attribute-cicon-attributes-data-name"></span>`data-name` | Root SVG | `CIconName` | Reflects the requested public glyph or alias name. |
| <span id="icon-attribute-cicon-attributes-data-size"></span>`data-size` | Root SVG | `"sm" | "md" | "lg"` | Reflects the size preset before CSS-variable overrides. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CIcon selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="icon-selector-cicon-selectors-data-citry-ui-part-icon"></span>`[data-citry-ui-part="icon"]` | Root SVG | Stable Icon root and `attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="icon-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="icon-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="icon-interface-input-type-aliases-cicon-size"></span>`CIconSize` | `Literal["sm", "md", "lg"]` |
| <span id="icon-interface-input-type-aliases-cicon-name"></span>`CIconName` | `Literal["arrow-down", "arrow-left", "arrow-right", "arrow-up", "calendar", "check", "chevron-down", "chevron-left", "chevron-right", "chevron-up", "circle-check", "circle-help", "circle-info", "circle-x", "clock", "copy", "download", "edit", "external-link", "eye", "eye-off", "file", "folder", "heart", "home", "leaf", "link", "lock", "mail", "menu", "minus", "more-horizontal", "more-vertical", "plus", "refresh-cw", "search", "settings", "star", "trash", "triangle-alert", "unlock", "upload", "user", "x", "back", "forward", "prev", "next", "close", "clear", "success", "info", "warn", "danger", "expand", "collapse", "dropdown"]` |

</div>

### Translation keys

-