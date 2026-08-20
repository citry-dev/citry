---
title: Toolbar
url: https://citry.dev/v/0.4.1/ui-library/components/toolbar/
description: "Group persistent controls under one name and one page Tab stop."
---
# Toolbar

Use `CToolbar` for three or more persistent editor, map, table, or contextual
controls. Toolbar owns focus movement only: Buttons own actions, Toggles own
pressed state, and Menu or Popover owns its surface.

## Toolbar at a glance


### Toolbar at a glance

[Open the rendered preview](/v/0.4.1/ui-library/components/toolbar/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarAtAGlance(Component):
    template = """
      <c-CToolbar label="Document tools" variant="soft">
        <c-CButton variant="ghost">Undo</c-CButton>
        <c-CToggle>Bold</c-CToggle>
        <c-CToggle>Italic</c-CToggle>
        <c-CDivider orientation="vertical" decorative />
        <a href="#toolbar-preview">Help</a>
      </c-CToolbar>
    """


preview = ToolbarAtAGlance()

preview  # noqa: B018
````


## Group persistent commands

Give each Toolbar a concise label. One owned control participates in the page
Tab order; Left and Right move among controls in a horizontal Toolbar.


### Group persistent commands

[Open the rendered preview](/v/0.4.1/ui-library/components/toolbar/_previews/commands/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarCommands(Component):
    template = """
      <c-CToolbar label="Text formatting" variant="outline">
        <c-CButton>Undo</c-CButton>
        <c-CButton>Redo</c-CButton>
        <c-CToggle c-pressed="True">Bold</c-CToggle>
        <c-CToggle>Italic</c-CToggle>
      </c-CToolbar>
    """


preview = ToolbarCommands()

preview  # noqa: B018
````



```citry-html
<c-CToolbar label="Text formatting">
  <c-CButton>Undo</c-CButton>
  <c-CToggle>Bold</c-CToggle>
  <c-CToggle>Italic</c-CToggle>
</c-CToolbar>
```


Use `CButtonGroup` instead when related actions should remain separate page
Tab stops. Use `CToggleGroup` when a group owns one shared selection value.

## Compose groups, separators, links, and overlays

ButtonGroup and ToggleGroup may organize controls without becoming a second
focus owner. Divider stays noninteractive. Menu and Popover activators remain
Toolbar controls while their opened surfaces keep independent focus behavior.


### Compose Toolbar controls

[Open the rendered preview](/v/0.4.1/ui-library/components/toolbar/_previews/composition/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarComposition(Component):
    template = """
      <c-CToolbar label="Map tools" variant="soft">
        <c-CButtonGroup label="Zoom">
          <c-CButton variant="outline">Zoom in</c-CButton>
          <c-CButton variant="outline">Zoom out</c-CButton>
        </c-CButtonGroup>
        <c-CDivider orientation="vertical" decorative />
        <c-CToggleGroup label="Map layer" value="terrain">
          <c-CToggle value="terrain">Terrain</c-CToggle>
          <c-CToggle value="satellite">Satellite</c-CToggle>
        </c-CToggleGroup>
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Details</c-CButton>
          </c-fill>
          <c-fill name="title">Map details</c-fill>
          <c-fill name="default"><p>Projection and data source information.</p></c-fill>
        </c-CPopover>
      </c-CToolbar>
    """


preview = ToolbarComposition()

preview  # noqa: B018
````


## Choose orientation and boundaries

Vertical Toolbars use Up and Down. Home and End reach the first and last
available control. Set `loop=False` when arrow movement should stop at an edge.
Horizontal direction follows LTR or RTL.


### Choose Toolbar orientation

[Open the rendered preview](/v/0.4.1/ui-library/components/toolbar/_previews/orientation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarOrientation(Component):
    template = """
      <div style="display:grid; grid-template-columns:1fr auto; gap:1rem; align-items:start">
        <c-CToolbar label="Horizontal tools" c-loop="False">
          <c-CButton>Previous</c-CButton>
          <c-CButton>Current</c-CButton>
          <c-CButton>Next</c-CButton>
        </c-CToolbar>
        <c-CToolbar label="Vertical tools" orientation="vertical" variant="outline">
          <c-CButton>Up</c-CButton>
          <c-CButton>Center</c-CButton>
          <c-CButton>Down</c-CButton>
        </c-CToolbar>
      </div>
    """


preview = ToolbarOrientation()

preview  # noqa: B018
````


## Compare variants and sizes

Plain adds no surface, soft adds a quiet background, and outline adds a
boundary. Toolbar does not change child Button or Toggle variants.


### Compare Toolbar variants and sizes

[Open the rendered preview](/v/0.4.1/ui-library/components/toolbar/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarVariants(Component):
    template = """
      <c-CStack gap="md">
        <c-CToolbar
          c-for="variant, size in [('plain', 'sm'), ('soft', 'md'), ('outline', 'lg')]"
          c-label="variant + ' ' + size + ' tools'"
          c-variant="variant"
          c-size="size"
        >
          <c-CButton>Cut</c-CButton>
          <c-CButton>Copy</c-CButton>
          <c-CButton>Paste</c-CButton>
        </c-CToolbar>
      </c-CStack>
    """


preview = ToolbarVariants()

preview  # noqa: B018
````


## Respect disabled ownership

Native disabled controls, `aria-disabled="true"`, hidden or inert controls,
disabled native fieldsets, and disabled `CForm` state are skipped. If the
focused control becomes unavailable, focus moves to the nearest available
Toolbar control only when focus had belonged to the Toolbar.


### Toolbar disabled controls

[Open the rendered preview](/v/0.4.1/ui-library/components/toolbar/_previews/disabled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarDisabled(Component):
    template = """
      <fieldset disabled>
        <legend>Unavailable editor</legend>
        <c-CToolbar label="Unavailable tools" variant="outline">
          <c-CButton>Cut</c-CButton>
          <c-CButton>Copy</c-CButton>
          <c-CButton>Paste</c-CButton>
        </c-CToolbar>
      </fieldset>
    """


preview = ToolbarDisabled()

preview  # noqa: B018
````


## Customize Toolbar

Public variables control the Toolbar surface and spacing. Child controls keep
their own component variables and public parts.


### Customize Toolbar

[Open the rendered preview](/v/0.4.1/ui-library/components/toolbar/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarCustomization(Component):
    template = """
      <c-CToolbar
        label="Forest tools"
        variant="soft"
        c-style="{
          '--cui-toolbar-gap': '0.75rem',
          '--cui-toolbar-radius': '1.25rem',
          '--cui-toolbar-background': '#eef8ec',
          '--cui-toolbar-border-color': '#497a43'
        }"
      >
        <c-CButton variant="ghost">Canopy</c-CButton>
        <c-CButton variant="ghost">Understory</c-CButton>
        <c-CButton variant="ghost">Soil</c-CButton>
      </c-CToolbar>
    """


preview = ToolbarCustomization()

preview  # noqa: B018
````


## Accessibility and content rules

Toolbar requires at least three owned Buttons or links after browser
initialization. Do not place text inputs, selects, textareas, contenteditable
regions, nested Toolbars, or authored `tabindex` inside it. Their keyboard or
focus contracts conflict with Toolbar's roving focus. Icon-only controls still
need their own accessible name.

Native Buttons remain responsible for `type="button"` when they must not
submit a Form. Citry UI Button and Toggle already use form-safe Button roots.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CToolbar server inputs

Server inputs are passed in a template through `<c-CToolbar ... />` or in Python through
`CToolbar(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="toolbar-input-ctoolbar-server-inputs-label"></span>`label` | `str` | required | Supplies the accessible Toolbar name. |
| <span id="toolbar-input-ctoolbar-server-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CToolbarOrientation`](#toolbar-interface-input-type-aliases-ctoolbar-orientation)) | `"horizontal"` | Selects layout and arrow-key axis. |
| <span id="toolbar-input-ctoolbar-server-inputs-loop"></span>`loop` | `bool` | `True` | Wraps arrow movement at the first and last available controls. |
| <span id="toolbar-input-ctoolbar-server-inputs-variant"></span>`variant` | `"plain" | "soft" | "outline"` ([`CToolbarVariant`](#toolbar-interface-input-type-aliases-ctoolbar-variant)) | `"plain"` | Selects the Toolbar surface treatment. |
| <span id="toolbar-input-ctoolbar-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CToolbarSize`](#toolbar-interface-input-type-aliases-ctoolbar-size)) | `"md"` | Selects Toolbar gap padding and minimum height. |
| <span id="toolbar-input-ctoolbar-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#toolbar-interface-input-type-aliases-class-value)) | `None` | Adds root classes. |
| <span id="toolbar-input-ctoolbar-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#toolbar-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles. |
| <span id="toolbar-input-ctoolbar-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted root attributes without replacing Toolbar semantics focus visibility reflections children or runtime markers. |

</div>

#### CToolbar client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CToolbar />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="toolbar-input-ctoolbar-client-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CToolbarOrientation`](#toolbar-interface-input-type-aliases-ctoolbar-orientation)) | Uses the server value. | Reactively changes layout ARIA orientation and arrow-key axis. |
| <span id="toolbar-input-ctoolbar-client-inputs-loop"></span>`loop` | `bool` | Uses the server value. | Reactively enables or disables arrow-key wrapping. |
| <span id="toolbar-input-ctoolbar-client-inputs-variant"></span>`variant` | `"plain" | "soft" | "outline"` ([`CToolbarVariant`](#toolbar-interface-input-type-aliases-ctoolbar-variant)) | Uses the server value. | Reactively changes the surface treatment. |
| <span id="toolbar-input-ctoolbar-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CToolbarSize`](#toolbar-interface-input-type-aliases-ctoolbar-size)) | Uses the server value. | Reactively changes Toolbar geometry. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CToolbar slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="toolbar-slot-ctoolbar-slots-default"></span>`default` | yes | `{}` ([`CToolbarDefaultSlotData`](#toolbar-interface-ctoolbar-default-slot-data)) | None. Settled enhanced content requires at least three owned Buttons or links. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CToolbar CSS variables

Apply these variables to `CToolbar` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="toolbar-css-ctoolbar-css-variables-cui-toolbar-gap"></span>`--cui-toolbar-gap` | `length` | Gap between Toolbar children. | `sm: 0.375rem; md: 0.5rem; lg: 0.625rem` |
| <span id="toolbar-css-ctoolbar-css-variables-cui-toolbar-padding"></span>`--cui-toolbar-padding` | `length` | Toolbar inner padding. | `sm: 0.25rem; md: 0.375rem; lg: 0.5rem` |
| <span id="toolbar-css-ctoolbar-css-variables-cui-toolbar-min-height"></span>`--cui-toolbar-min-height` | `length` | Minimum logical Toolbar height. | `sm: 2.25rem; md: 2.75rem; lg: 3.25rem` |
| <span id="toolbar-css-ctoolbar-css-variables-cui-toolbar-radius"></span>`--cui-toolbar-radius` | `length` | Toolbar corner radius. | `0.75rem` |
| <span id="toolbar-css-ctoolbar-css-variables-cui-toolbar-background"></span>`--cui-toolbar-background` | `color` | Toolbar surface color. | `plain and outline: transparent; soft: a 7 percent CanvasText mix over Canvas` |
| <span id="toolbar-css-ctoolbar-css-variables-cui-toolbar-foreground"></span>`--cui-toolbar-foreground` | `color` | Inherited Toolbar foreground. | `CanvasText` |
| <span id="toolbar-css-ctoolbar-css-variables-cui-toolbar-border-color"></span>`--cui-toolbar-border-color` | `color` | Outline Toolbar border. | `a 16 percent CanvasText mix` |
| <span id="toolbar-css-ctoolbar-css-variables-cui-toolbar-focus-color"></span>`--cui-toolbar-focus-color` | `color` | Focus outline color for owned controls. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CToolbar attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="toolbar-attribute-ctoolbar-attributes-role"></span>`role` | Root | `toolbar` | Exposes one named Toolbar composite. |
| <span id="toolbar-attribute-ctoolbar-attributes-aria-label"></span>`aria-label` | Root | `string` | Supplies the required accessible name. |
| <span id="toolbar-attribute-ctoolbar-attributes-aria-orientation"></span>`aria-orientation` | Root | `horizontal | vertical` | Mirrors the effective navigation axis. |
| <span id="toolbar-attribute-ctoolbar-attributes-data-orientation"></span>`data-orientation` | Root | `horizontal | vertical` | Mirrors effective orientation. |
| <span id="toolbar-attribute-ctoolbar-attributes-data-loop"></span>`data-loop` | Root | `present-or-absent` | Present when arrow navigation wraps. |
| <span id="toolbar-attribute-ctoolbar-attributes-data-variant"></span>`data-variant` | Root | `plain | soft | outline` | Mirrors effective variant. |
| <span id="toolbar-attribute-ctoolbar-attributes-data-size"></span>`data-size` | Root | `sm | md | lg` | Mirrors effective size. |
| <span id="toolbar-attribute-ctoolbar-attributes-tabindex"></span>`tabindex` | Owned Button or link | `0 | -1` | Exactly one available control participates in the page Tab order. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CToolbar selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="toolbar-selector-ctoolbar-selectors-data-citry-ui-part-toolbar"></span>`[data-citry-ui-part="toolbar"]` | Root div | Stable Toolbar root and attrs destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="toolbar-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="toolbar-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="toolbar-interface-input-type-aliases-ctoolbar-orientation"></span>`CToolbarOrientation` | `Literal["horizontal", "vertical"]` |
| <span id="toolbar-interface-input-type-aliases-ctoolbar-variant"></span>`CToolbarVariant` | `Literal["plain", "soft", "outline"]` |
| <span id="toolbar-interface-input-type-aliases-ctoolbar-size"></span>`CToolbarSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="toolbar-interface-ctoolbar-default-slot-data"></span>

#### `CToolbarDefaultSlotData`

Empty dataclass: `{}`.

### Translation keys

-