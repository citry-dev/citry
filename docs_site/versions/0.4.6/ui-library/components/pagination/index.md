---
title: Pagination
url: https://citry.dev/v/0.4.6/ui-library/components/pagination/
description: "Navigate finite page sequences with native links or client-owned controls."
---
# Pagination

Use `CPagination` to move through a finite sequence while preserving native URLs or browser-local state.

## Pagination at a glance


### Pagination at a glance

[Open the rendered preview](/v/0.4.6/ui-library/components/pagination/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PaginationGlance(Component):
    template = '<c-CPagination c-pages="24" c-page="8" href="?page={page}" />'


preview = PaginationGlance()
preview  # noqa: B018
````


## Navigate with links

Put `{page}` in `href`. Server output then works before JavaScript and remains shareable.


### Navigate with page links

[Open the rendered preview](/v/0.4.6/ui-library/components/pagination/_previews/links/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LinkPagination(Component):
    template = '<c-CPagination c-pages="12" c-page="4" href="/field-notes?page={page}" />'


preview = LinkPagination()
preview  # noqa: B018
````


## Control the current page in the browser

Omit `href` for Button controls. Client inputs are passed with `$c-props="{...}"`.
Rebuilt Button ranges retain the server locale even without browser i18n; a client-enabled i18n provider also updates recreated labels when its locale changes.


### Control Pagination in the browser

[Open the rendered preview](/v/0.4.6/ui-library/components/pagination/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledPagination(Component):
    template = """
      <section x-data="{ page: 3 }">
        <p>Plate <strong x-text="page"></strong> of 18</p>
        <c-CPagination
          c-pages="18"
          c-page="3"
          $c-props="{ page, onPageChange: (next) => page = next }"
        />
      </section>
    """


preview = ControlledPagination()
preview  # noqa: B018
````


## Compact long ranges

`siblings` keeps pages around the current page. `boundaries` keeps pages at both ends.


### Compact long page ranges

[Open the rendered preview](/v/0.4.6/ui-library/components/pagination/_previews/ranges/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PaginationRanges(Component):
    template = """
      <c-CCol gap="md">
        <c-CPagination c-pages="100" c-page="50" c-siblings="0" c-boundaries="1" />
        <c-CPagination c-pages="100" c-page="50" c-siblings="2" c-boundaries="2" />
      </c-CCol>
    """


preview = PaginationRanges()
preview  # noqa: B018
````


## Add edge controls


### Choose Pagination controls

[Open the rendered preview](/v/0.4.6/ui-library/components/pagination/_previews/controls/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PaginationControls(Component):
    template = """
      <c-CCol gap="md">
        <c-CPagination c-pages="14" c-page="7" c-show_edges="True" />
        <c-CPagination c-pages="14" c-page="7" c-show_controls="False" />
      </c-CCol>
    """


preview = PaginationControls()
preview  # noqa: B018
````


## Choose presentation


### Compare Pagination variants and sizes

[Open the rendered preview](/v/0.4.6/ui-library/components/pagination/_previews/presentation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PaginationPresentation(Component):
    template = """
      <c-CCol gap="md">
        <c-CPagination c-pages="8" c-page="3" variant="soft" size="sm" />
        <c-CPagination c-pages="8" c-page="3" variant="outline" />
        <c-CPagination c-pages="8" c-page="3" variant="plain" size="lg" />
      </c-CCol>
    """


preview = PaginationPresentation()
preview  # noqa: B018
````


## Customize Pagination


### Customize Pagination

[Open the rendered preview](/v/0.4.6/ui-library/components/pagination/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PaginationCustomization(Component):
    template = '<c-CPagination class_="lunar-pages" c-pages="9" c-page="5" />'
    css = """
      :where(.lunar-pages) {
        --cui-pagination-current-background: light-dark(#6d28d9, #c4b5fd);
        --cui-pagination-current-foreground: light-dark(white, #2e1065);
        --cui-pagination-radius: 999px;
      }
    """


preview = PaginationCustomization()
preview  # noqa: B018
````


## Accessibility and behavior

Pagination is a named navigation landmark. Current page uses `aria-current="page"`. Links and Buttons keep native Tab and activation behavior; ellipses are inert.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CPagination server inputs

Server inputs are passed in a template through `<c-CPagination ... />` or in Python through
`CPagination(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="pagination-input-cpagination-server-inputs-pages"></span>`pages` | `int` | required | Sets the finite page count; must be at least 1. |
| <span id="pagination-input-cpagination-server-inputs-page"></span>`page` | `int` | `1` | Sets the current page between 1 and pages. |
| <span id="pagination-input-cpagination-server-inputs-href"></span>`href` | `str | None` | `None` | Creates native links by replacing a required `{page}` placeholder; None creates client-owned Buttons. |
| <span id="pagination-input-cpagination-server-inputs-siblings"></span>`siblings` | `int` | `1` | Keeps this many pages on either side of the current page. |
| <span id="pagination-input-cpagination-server-inputs-boundaries"></span>`boundaries` | `int` | `1` | Keeps this many pages at both sequence edges. |
| <span id="pagination-input-cpagination-server-inputs-show-controls"></span>`show_controls` | `bool` | `True` | Renders previous and next controls. |
| <span id="pagination-input-cpagination-server-inputs-show-edges"></span>`show_edges` | `bool` | `False` | Renders first and last controls. |
| <span id="pagination-input-cpagination-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables all Button-mode controls and removes link navigation. |
| <span id="pagination-input-cpagination-server-inputs-variant"></span>`variant` | `"soft" | "outline" | "plain"` ([`CPaginationVariant`](#pagination-interface-input-type-aliases-pagination-variant)) | `"soft"` | Selects visual treatment. |
| <span id="pagination-input-cpagination-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CPaginationSize`](#pagination-interface-input-type-aliases-pagination-size)) | `"md"` | Selects control geometry. |
| <span id="pagination-input-cpagination-server-inputs-label"></span>`label` | `str` | `"Pagination"` | Names the navigation landmark. |
| <span id="pagination-input-cpagination-server-inputs-page-label"></span>`page_label` | `str` | `"Page {page}"` | Labels numbered controls; must contain `{page}`. |
| <span id="pagination-input-cpagination-server-inputs-previous-label"></span>`previous_label` | `str` | `"Previous page"` | Labels the previous control. |
| <span id="pagination-input-cpagination-server-inputs-next-label"></span>`next_label` | `str` | `"Next page"` | Labels the next control. |
| <span id="pagination-input-cpagination-server-inputs-first-label"></span>`first_label` | `str` | `"First page"` | Labels the first control. |
| <span id="pagination-input-cpagination-server-inputs-last-label"></span>`last_label` | `str` | `"Last page"` | Labels the last control. |
| <span id="pagination-input-cpagination-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#pagination-interface-input-type-aliases-class-value)) | `None` | Adds root classes. |
| <span id="pagination-input-cpagination-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#pagination-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles. |
| <span id="pagination-input-cpagination-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted nav attributes without replacing naming, children, focus ownership, or runtime fields. |

</div>

#### CPagination client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CPagination />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="pagination-input-cpagination-client-inputs-page"></span>`page` | `number | undefined` | Uses the server input. | Controls and rebuilds the current compact range while supplied. |
| <span id="pagination-input-cpagination-client-inputs-disabled"></span>`disabled` | `boolean | undefined` | Uses the server input. | Overrides local disabled state while valid and supplied. |
| <span id="pagination-input-cpagination-client-inputs-variant"></span>`variant` | `"soft" | "outline" | "plain" | undefined` | Uses the server input. | Overrides visual treatment. |
| <span id="pagination-input-cpagination-client-inputs-size"></span>`size` | `"sm" | "md" | "lg" | undefined` | Uses the server input. | Overrides control geometry. |
| <span id="pagination-input-cpagination-client-inputs-on-page-change"></span>`onPageChange` | `((page: number, detail: CPaginationChangeDetail) => void) | undefined` | Uses the server input. | Runs before accepted Button state changes or native link navigation. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CPagination events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="pagination-event-cpagination-events-on-page-change"></span>`onPageChange` | `(page: number, detail: CPaginationChangeDetail) => void` ([`CPaginationChangeDetail`](#pagination-interface-cpagination-change-detail)) | Enabled noncurrent control activation. | `{page, previousPage, kind, sourceEvent}` ([`CPaginationChangeDetail`](#pagination-interface-cpagination-change-detail)) | Reports the target before Button state change or link navigation; preventing sourceEvent prevents a link. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CPagination CSS variables

Apply these variables to `CPagination` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="pagination-css-cpagination-css-variables-cui-pagination-gap"></span>`--cui-pagination-gap` | `length` | Control gap. | `0.35rem` |
| <span id="pagination-css-cpagination-css-variables-cui-pagination-control-size"></span>`--cui-pagination-control-size` | `length` | Minimum control width and height. | `Size-derived.` |
| <span id="pagination-css-cpagination-css-variables-cui-pagination-radius"></span>`--cui-pagination-radius` | `length` | Control radius. | `0.55rem` |
| <span id="pagination-css-cpagination-css-variables-cui-pagination-foreground"></span>`--cui-pagination-foreground` | `color` | Resting foreground. | `CanvasText` |
| <span id="pagination-css-cpagination-css-variables-cui-pagination-background"></span>`--cui-pagination-background` | `color` | Resting background. | `transparent` |
| <span id="pagination-css-cpagination-css-variables-cui-pagination-border-color"></span>`--cui-pagination-border-color` | `color` | Outline border. | `Nested-scheme border color.` |
| <span id="pagination-css-cpagination-css-variables-cui-pagination-current-background"></span>`--cui-pagination-current-background` | `color` | Current-page background. | `Nested-scheme blue.` |
| <span id="pagination-css-cpagination-css-variables-cui-pagination-current-foreground"></span>`--cui-pagination-current-foreground` | `color` | Current-page foreground. | `Contrasting nested-scheme color.` |
| <span id="pagination-css-cpagination-css-variables-cui-pagination-disabled-opacity"></span>`--cui-pagination-disabled-opacity` | `number` | Disabled opacity. | `0.5` |
| <span id="pagination-css-cpagination-css-variables-cui-pagination-focus-ring"></span>`--cui-pagination-focus-ring` | `color` | Keyboard focus outline. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CPagination attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="pagination-attribute-cpagination-attributes-aria-current"></span>`aria-current` | Current page control | `"page"` | Identifies the current page. |
| <span id="pagination-attribute-cpagination-attributes-data-current"></span>`data-current` | Current page control | `present-or-absent` | Public current-page styling hook. |
| <span id="pagination-attribute-cpagination-attributes-data-page"></span>`data-page` | Control | `integer-string` | Target page. |
| <span id="pagination-attribute-cpagination-attributes-data-kind"></span>`data-kind` | Control | `"page" | "previous" | "next" | "first" | "last"` | Control job. |
| <span id="pagination-attribute-cpagination-attributes-data-disabled"></span>`data-disabled` | Root | `present-or-absent` | Present while navigation is disabled. |
| <span id="pagination-attribute-cpagination-attributes-data-variant"></span>`data-variant` | Root | `"soft" | "outline" | "plain"` | Visual treatment. |
| <span id="pagination-attribute-cpagination-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Control geometry. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CPagination selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="pagination-selector-cpagination-selectors-data-citry-ui-part-pagination"></span>`[data-citry-ui-part="pagination"]` | nav root | Stable root and attrs destination. |
| <span id="pagination-selector-cpagination-selectors-data-citry-ui-part-list"></span>`[data-citry-ui-part="list"]` | ul | Stable list layout. |
| <span id="pagination-selector-cpagination-selectors-data-citry-ui-part-control"></span>`[data-citry-ui-part="control"]` | link or Button | Stable interactive target. |
| <span id="pagination-selector-cpagination-selectors-data-citry-ui-part-ellipsis"></span>`[data-citry-ui-part="ellipsis"]` | inert span | Stable omitted-range marker. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="pagination-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="pagination-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="pagination-interface-input-type-aliases-pagination-variant"></span>`CPaginationVariant` | `Literal["soft", "outline", "plain"]` |
| <span id="pagination-interface-input-type-aliases-pagination-size"></span>`CPaginationSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="pagination-interface-cpagination-change-detail"></span>

#### `CPaginationChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="pagination-interface-cpagination-change-detail-page"></span>`page` | `number` | - | Requested page. |
| <span id="pagination-interface-cpagination-change-detail-previous-page"></span>`previousPage` | `number` | - | Current page before activation. |
| <span id="pagination-interface-cpagination-change-detail-kind"></span>`kind` | `"page" | "previous" | "next" | "first" | "last"` | - | Activated control job. |
| <span id="pagination-interface-cpagination-change-detail-source-event"></span>`sourceEvent` | `Event` | - | Native click event; prevent it to stop a link. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CPagination translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="pagination-translation-cpagination-translations-label"></span>`citry-ui-pagination-label` | Names the pagination navigation landmark. | `None` | `label` input | $c-tr updates `aria-label`. |
| <span id="pagination-translation-cpagination-translations-page"></span>`citry-ui-pagination-page` | Names each numbered page control. | `page: str` | `page_label` input | $c-tr handles server controls; recreated controls use a fixed server-translated pattern without client i18n and `i18n.bind()` with it. |
| <span id="pagination-translation-cpagination-translations-previous"></span>`citry-ui-pagination-previous` | Names the previous-page control. | `None` | `previous_label` input | $c-tr or `i18n.bind()` updates `aria-label`. |
| <span id="pagination-translation-cpagination-translations-next"></span>`citry-ui-pagination-next` | Names the next-page control. | `None` | `next_label` input | $c-tr or `i18n.bind()` updates `aria-label`. |
| <span id="pagination-translation-cpagination-translations-first"></span>`citry-ui-pagination-first` | Names the first-page control. | `None` | `first_label` input | $c-tr or `i18n.bind()` updates `aria-label`. |
| <span id="pagination-translation-cpagination-translations-last"></span>`citry-ui-pagination-last` | Names the last-page control. | `None` | `last_label` input | $c-tr or `i18n.bind()` updates `aria-label`. |

</div>