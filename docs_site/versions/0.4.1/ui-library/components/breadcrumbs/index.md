---
title: Breadcrumbs
url: https://citry.dev/v/0.4.1/ui-library/components/breadcrumbs/
description: "Show hierarchical page location with semantic Citry UI Breadcrumbs."
---
# Breadcrumbs

Use `CBreadcrumbs` to show the current page within a hierarchy and link back to
its ancestors.

## Breadcrumbs at a glance


### Breadcrumbs at a glance

[Open the rendered preview](/v/0.4.1/ui-library/components/breadcrumbs/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BreadcrumbsAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Library", "/library"),
                citry_ui.CBreadcrumbItem("Natural history", "/library/nature"),
                citry_ui.CBreadcrumbItem("The hidden life of trees"),
            )
        }

    template = """
      <section class="breadcrumb-shelf">
        <c-CBreadcrumbs c-items="items" label="Book location" />
        <h2>The hidden life of trees</h2>
        <p>Essays on forests, roots, and the communities beneath them.</p>
      </section>
    """
    css = """
      :where(.breadcrumb-shelf) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b8aa92, #655a49);
        border-radius: 0.9rem;
        color: CanvasText;
        font-family: ui-serif, Georgia, serif;
      }

      :where(.breadcrumb-shelf h2, .breadcrumb-shelf p) {
        margin: 0;
      }
    """


preview = BreadcrumbsAtAGlance()

preview  # noqa: B018
````


## Build a trail from records

The final item is current. Give earlier items an `href`; leave the final href
empty for plain current-page text.


### Build a Breadcrumb trail

[Open the rendered preview](/v/0.4.1/ui-library/components/breadcrumbs/_previews/basic/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicBreadcrumbs(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Library", "/library"),
                citry_ui.CBreadcrumbItem("Fiction", "/library/fiction"),
                citry_ui.CBreadcrumbItem("The left hand of darkness"),
            )
        }

    template = '<c-CBreadcrumbs c-items="items" label="Book location" />'


preview = BasicBreadcrumbs()

preview  # noqa: B018
````



```py
items = (
    CBreadcrumbItem("Home", "/"),
    CBreadcrumbItem("Library", "/library"),
    CBreadcrumbItem("The green room"),
)
```


## Keep the current page linked

A final item may retain its href. Citry adds `aria-current="page"`.


### Link the current page

[Open the rendered preview](/v/0.4.1/ui-library/components/breadcrumbs/_previews/current-link/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LinkedCurrentBreadcrumb(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Library", "/library"),
                citry_ui.CBreadcrumbItem("New arrivals", "/library/new"),
            )
        }

    template = '<c-CBreadcrumbs c-items="items" label="Collection location" />'


preview = LinkedCurrentBreadcrumb()

preview  # noqa: B018
````


## Choose a separator

Use concise text directly or replace each separator through the scoped slot.
Separators stay hidden from assistive technology.


### Choose Breadcrumb separators

[Open the rendered preview](/v/0.4.1/ui-library/components/breadcrumbs/_previews/separators/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BreadcrumbSeparators(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Poetry", "/poetry"),
                citry_ui.CBreadcrumbItem("Mary Oliver"),
            )
        }

    template = """
      <c-CStack>
        <c-CBreadcrumbs c-items="items" separator="/" label="Slash trail" />
        <c-CBreadcrumbs c-items="items" separator="»" label="Chevron trail" />
        <c-CBreadcrumbs c-items="items" label="Arrow trail">
          <c-fill name="separator" data="{ index }">
            →
          </c-fill>
        </c-CBreadcrumbs>
      </c-CStack>
    """


preview = BreadcrumbSeparators()

preview  # noqa: B018
````


## Choose size

Use `sm`, `md`, or `lg` to match the surrounding navigation density.


### Compare Breadcrumb sizes

[Open the rendered preview](/v/0.4.1/ui-library/components/breadcrumbs/_previews/sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BreadcrumbSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Essays", "/essays"),
                citry_ui.CBreadcrumbItem("On keeping a notebook"),
            ),
            "sizes": ("sm", "md", "lg"),
        }

    template = """
      <c-CStack>
        <c-for each="size in sizes">
          <c-CBreadcrumbs c-items="items" c-size="size" c-label="f'{size} book location'" />
        </c-for>
      </c-CStack>
    """


preview = BreadcrumbSizes()

preview  # noqa: B018
````


## Wrap or scroll long trails

Wrapping is the default. Set `wrap=False` for one horizontal scroll row.


### Handle long Breadcrumb trails

[Open the rendered preview](/v/0.4.1/ui-library/components/breadcrumbs/_previews/overflow/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BreadcrumbOverflow(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        labels = ("Library", "Collections", "Natural history", "Forests", "Temperate woodland", "Field notes")
        return {
            "items": tuple(
                citry_ui.CBreadcrumbItem(label, f"/shelf/{index}")
                if index < len(labels) - 1
                else citry_ui.CBreadcrumbItem(label)
                for index, label in enumerate(labels)
            )
        }

    template = """
      <c-CStack class_="breadcrumb-overflow">
        <c-CBreadcrumbs c-items="items" label="Wrapping book location" />
        <c-CBreadcrumbs c-items="items" label="Scrolling book location" c-wrap="False" />
      </c-CStack>
    """
    css = """
      :where(.breadcrumb-overflow) {
        inline-size: min(100%, 22rem);
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
      }
    """


preview = BreadcrumbOverflow()

preview  # noqa: B018
````


## Customize item rendering

The `item` slot receives the record, index, current flag, and owned native attrs.
Bind `attrs` to preserve link and current-page semantics.


### Customize Breadcrumb items

[Open the rendered preview](/v/0.4.1/ui-library/components/breadcrumbs/_previews/item-slot/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BreadcrumbItemSlot(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Reading lists", "/lists"),
                citry_ui.CBreadcrumbItem("Summer shelf"),
            )
        }

    template = """
      <c-CBreadcrumbs c-items="items" label="Reading-list location">
        <c-fill name="item" data="{ item, index, is_current, attrs }">
          <c-if cond="item.href is not None">
            <a c-bind="attrs">
              <span aria-hidden="true">◌</span>
              {{ item.label }}
            </a>
          </c-if>
          <c-else>
            <span c-bind="attrs">
              {{ item.label }}
            </span>
          </c-else>
        </c-fill>
      </c-CBreadcrumbs>
    """


preview = BreadcrumbItemSlot()

preview  # noqa: B018
````


## Compose route-derived records

Route integration stays outside the component. Turn your router hierarchy into
`CBreadcrumbItem` records and pass the resulting tuple.


### Compose route-derived Breadcrumbs

[Open the rendered preview](/v/0.4.1/ui-library/components/breadcrumbs/_previews/route-records/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RouteBreadcrumbs(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        route = (("Authors", "/authors"), ("Ursula K. Le Guin", "/authors/le-guin"), ("Books", None))
        return {"items": tuple(citry_ui.CBreadcrumbItem(label, href) for label, href in route)}

    template = '<c-CBreadcrumbs c-items="items" label="Author location" />'


preview = RouteBreadcrumbs()

preview  # noqa: B018
````


## Customize Breadcrumbs

Override public link, current, separator, focus, and spacing variables or stable
parts.


### Customize Breadcrumbs with public CSS

[Open the rendered preview](/v/0.4.1/ui-library/components/breadcrumbs/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomBreadcrumbs(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Archive", "/archive"),
                citry_ui.CBreadcrumbItem("Rare books"),
            )
        }

    template = '<c-CBreadcrumbs c-items="items" label="Archive location" class_="rare-trail" separator="✦" />'
    css = """
      :where(.rare-trail) {
        --cui-breadcrumbs-link-color: light-dark(#7c2d12, #fdba74);
        --cui-breadcrumbs-current-color: light-dark(#4c1d95, #c4b5fd);
        --cui-breadcrumbs-separator-color: light-dark(#9a3412, #fb923c);
        --cui-breadcrumbs-gap: 0.8rem;
        padding: 1rem;
        border-block: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
      }
    """


preview = CustomBreadcrumbs()

preview  # noqa: B018
````


## API reference

### Inputs

#### CBreadcrumbs server inputs

Server inputs are passed in a template through `<c-CBreadcrumbs ... />` or in Python through
`CBreadcrumbs(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="breadcrumbs-input-cbreadcrumbs-server-inputs-items"></span>`items` | `Sequence[CBreadcrumbItem]` | required | Renders a nonempty hierarchy whose final record is current. |
| <span id="breadcrumbs-input-cbreadcrumbs-server-inputs-label"></span>`label` | `str` | `"Breadcrumbs"` | Names the navigation landmark. |
| <span id="breadcrumbs-input-cbreadcrumbs-server-inputs-separator"></span>`separator` | `str` | `"/"` | Sets hidden-from-AT visual separator fallback. |
| <span id="breadcrumbs-input-cbreadcrumbs-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CBreadcrumbsSize`](#breadcrumbs-interface-size)) | `"md"` | Sets trail type scale. |
| <span id="breadcrumbs-input-cbreadcrumbs-server-inputs-wrap"></span>`wrap` | `bool` | `True` | Wraps the trail; false keeps one horizontally scrollable row. |
| <span id="breadcrumbs-input-cbreadcrumbs-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#breadcrumbs-interface-class-value)) | `None` | Adds root classes and merges them with attrs. |
| <span id="breadcrumbs-input-cbreadcrumbs-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#breadcrumbs-interface-style-value)) | `None` | Adds root inline styles and merges them with attrs. |
| <span id="breadcrumbs-input-cbreadcrumbs-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted nonconflicting nav metadata. |
| <span id="breadcrumbs-input-cbreadcrumbs-server-inputs-list-attrs"></span>`list_attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted nonconflicting ordered-list metadata. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CBreadcrumbs slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="breadcrumbs-slot-cbreadcrumbs-slots-item"></span>`item` | no | `{item: CBreadcrumbItem, index: int, is_current: bool, attrs: Mapping[str, object]}` ([`CBreadcrumbsItemSlotData`](#breadcrumbs-interface-item-slot-data)) | Renders the record as a native anchor or current span. |
| <span id="breadcrumbs-slot-cbreadcrumbs-slots-separator"></span>`separator` | no | `{index: int}` ([`CBreadcrumbsSeparatorSlotData`](#breadcrumbs-interface-separator-slot-data)) | Renders the `separator` input inside its hidden wrapper. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CBreadcrumbs CSS variables

Apply these variables to `CBreadcrumbs` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="breadcrumbs-css-cbreadcrumbs-css-variables-cui-breadcrumbs-foreground"></span>`--cui-breadcrumbs-foreground` | `color` | Root inherited foreground. | `CanvasText.` |
| <span id="breadcrumbs-css-cbreadcrumbs-css-variables-cui-breadcrumbs-link-color"></span>`--cui-breadcrumbs-link-color` | `color` | Ancestor link color. | `LinkText.` |
| <span id="breadcrumbs-css-cbreadcrumbs-css-variables-cui-breadcrumbs-current-color"></span>`--cui-breadcrumbs-current-color` | `color` | Current-page color. | `CanvasText.` |
| <span id="breadcrumbs-css-cbreadcrumbs-css-variables-cui-breadcrumbs-separator-color"></span>`--cui-breadcrumbs-separator-color` | `color` | Visual separator color. | `Scheme-aware muted foreground.` |
| <span id="breadcrumbs-css-cbreadcrumbs-css-variables-cui-breadcrumbs-gap"></span>`--cui-breadcrumbs-gap` | `length` | Item and separator spacing. | `0.5rem.` |
| <span id="breadcrumbs-css-cbreadcrumbs-css-variables-cui-breadcrumbs-focus-color"></span>`--cui-breadcrumbs-focus-color` | `color` | Link keyboard focus ring. | `Highlight.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CBreadcrumbs attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="breadcrumbs-attribute-cbreadcrumbs-attributes-aria-label"></span>`aria-label` | Nav root | `nonempty string` | Names the navigation landmark. |
| <span id="breadcrumbs-attribute-cbreadcrumbs-attributes-href"></span>`href` | Linked item anchor | `nonempty string` | Native ancestor or linked-current destination. |
| <span id="breadcrumbs-attribute-cbreadcrumbs-attributes-aria-current"></span>`aria-current` | Final anchor or span | `"page"` | Marks the final item as current. |
| <span id="breadcrumbs-attribute-cbreadcrumbs-attributes-data-size"></span>`data-size` | Nav root | `"sm" | "md" | "lg"` | Mirrors type scale. |
| <span id="breadcrumbs-attribute-cbreadcrumbs-attributes-data-wrap"></span>`data-wrap` | Nav root | `boolean present or absent` | Present while the trail wraps. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CBreadcrumbs selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="breadcrumbs-selector-cbreadcrumbs-selectors-breadcrumbs"></span>`[data-citry-ui-part="breadcrumbs"]` | Nav root | Landmark and root attrs destination. |
| <span id="breadcrumbs-selector-cbreadcrumbs-selectors-list"></span>`[data-citry-ui-part="list"]` | Ordered list | Trail layout and list attrs destination. |
| <span id="breadcrumbs-selector-cbreadcrumbs-selectors-item"></span>`[data-citry-ui-part="item"]` | List item | One hierarchy record. |
| <span id="breadcrumbs-selector-cbreadcrumbs-selectors-link"></span>`[data-citry-ui-part="link"]` | Native anchor | Navigable ancestor or linked current item. |
| <span id="breadcrumbs-selector-cbreadcrumbs-selectors-current"></span>`[data-citry-ui-part="current"]` | Span | Plain current-page item. |
| <span id="breadcrumbs-selector-cbreadcrumbs-selectors-separator"></span>`[data-citry-ui-part="separator"]` | Hidden-from-AT span | Visual hierarchy separator. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="breadcrumbs-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="breadcrumbs-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="breadcrumbs-interface-size"></span>`CBreadcrumbsSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="breadcrumbs-interface-item"></span>

#### `CBreadcrumbItem`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="breadcrumbs-interface-item-label"></span>`label` | `str` | - | Visible nonempty item text. |
| <span id="breadcrumbs-interface-item-href"></span>`href` | `str | None` | - | Native destination; None renders plain text. |
| <span id="breadcrumbs-interface-item-attrs"></span>`attrs` | `Mapping[str, object] | None` | - | Copied trusted nonconflicting anchor/span attrs. |

</div>

<span id="breadcrumbs-interface-item-slot-data"></span>

#### `CBreadcrumbsItemSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="breadcrumbs-interface-item-slot-data-item"></span>`item` | `CBreadcrumbItem` | - | Normalized item record. |
| <span id="breadcrumbs-interface-item-slot-data-index"></span>`index` | `int` | - | Zero-based hierarchy position. |
| <span id="breadcrumbs-interface-item-slot-data-is-current"></span>`is_current` | `bool` | - | True only for the final item. |
| <span id="breadcrumbs-interface-item-slot-data-attrs"></span>`attrs` | `Mapping[str, object]` | - | Required native href/current attrs plus record attrs. |

</div>

<span id="breadcrumbs-interface-separator-slot-data"></span>

#### `CBreadcrumbsSeparatorSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="breadcrumbs-interface-separator-slot-data-index"></span>`index` | `int` | - | Zero-based preceding item index. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CBreadcrumbs translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="breadcrumbs-translation-cbreadcrumbs-translations-label"></span>`citry-ui-breadcrumbs-label` | Names the navigation landmark. | `None` | `label` input | $c-tr updates `aria-label`. |

</div>