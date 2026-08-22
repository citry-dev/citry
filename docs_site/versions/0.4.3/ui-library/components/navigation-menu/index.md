---
title: NavigationMenu
url: https://citry.dev/v/0.4.3/ui-library/components/navigation-menu/
description: "Compose native website navigation with rich disclosure panels."
---
# NavigationMenu

Use `CNavigationMenu` for persistent site navigation whose top-level entries
are native links or Buttons that disclose richer link collections. It keeps
ordinary `nav`, list, link, and Tab behavior—application commands belong in
`CMenu`.

## NavigationMenu at a glance


### NavigationMenu at a glance

[Open the rendered preview](/v/0.4.3/ui-library/components/navigation-menu/_previews/at-a-glance/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationMenuAtAGlance(Component):
    template = """
      <c-CNavigationMenu label="Main navigation" variant="surface">
        <c-CNavigationMenuLink href="#overview" c-current="True">Overview</c-CNavigationMenuLink>
        <c-CNavigationMenuItem value="products">
          <c-fill name="label">Products</c-fill>
          <c-fill name="default"><c-CCol gap="sm"><strong>Explore products</strong><a href="#analytics">Analytics</a><a href="#automations">Automations</a></c-CCol></c-fill>
        </c-CNavigationMenuItem>
        <c-CNavigationMenuLink href="#pricing">Pricing</c-CNavigationMenuLink>
      </c-CNavigationMenu>
    """


preview = NavigationMenuAtAGlance()
preview  # noqa: B018
````


## Link-only navigation


### Native navigation links

[Open the rendered preview](/v/0.4.3/ui-library/components/navigation-menu/_previews/links/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationLinks(Component):
    template = """
      <c-CNavigationMenu label="Documentation">
        <c-CNavigationMenuLink href="#guide" c-current="True">Guide</c-CNavigationMenuLink>
        <c-CNavigationMenuLink href="#reference">Reference</c-CNavigationMenuLink>
        <c-CNavigationMenuLink href="#examples">Examples</c-CNavigationMenuLink>
      </c-CNavigationMenu>
    """


preview = NavigationLinks()
preview  # noqa: B018
````


## Rich navigation panels


### Rich navigation panels

[Open the rendered preview](/v/0.4.3/ui-library/components/navigation-menu/_previews/panels/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RichNavigationPanels(Component):
    template = """
      <c-CNavigationMenu label="Product navigation" value="platform">
        <c-CNavigationMenuLink href="#home">Home</c-CNavigationMenuLink>
        <c-CNavigationMenuItem value="platform">
          <c-fill name="label">Platform</c-fill>
          <c-fill name="default"><c-CGrid cols="2" gap="sm"><c-CCard variant="subtle"><c-fill name="header"><strong>Observe</strong></c-fill><c-fill name="default">Capture field signals.</c-fill></c-CCard><c-CCard variant="subtle"><c-fill name="header"><strong>Coordinate</strong></c-fill><c-fill name="default">Keep teams aligned.</c-fill></c-CCard></c-CGrid></c-fill>
        </c-CNavigationMenuItem>
        <c-CNavigationMenuLink href="#company">Company</c-CNavigationMenuLink>
      </c-CNavigationMenu>
    """


preview = RichNavigationPanels()
preview  # noqa: B018
````


## Control the open panel


### Controlled NavigationMenu

[Open the rendered preview](/v/0.4.3/ui-library/components/navigation-menu/_previews/controlled/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledNavigation(Component):
    template = """
      <section x-data="{open:null}"><p>Open: <strong x-text="open ?? 'none'"></strong></p>
        <c-CNavigationMenu label="Controlled navigation" $c-props="{value:open,onValueChange:(next)=>open=next}">
          <c-CNavigationMenuLink href="#home">Home</c-CNavigationMenuLink>
          <c-CNavigationMenuItem value="learn"><c-fill name="label">Learn</c-fill><c-fill name="default"><a href="#tutorials">Tutorials</a></c-fill></c-CNavigationMenuItem>
        </c-CNavigationMenu>
      </section>
    """


preview = ControlledNavigation()
preview  # noqa: B018
````


## Choose orientation


### NavigationMenu orientations

[Open the rendered preview](/v/0.4.3/ui-library/components/navigation-menu/_previews/orientation/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationOrientation(Component):
    template = """
      <c-CNavigationMenu label="Account navigation" orientation="vertical" variant="surface">
        <c-CNavigationMenuLink href="#profile" c-current="True">Profile</c-CNavigationMenuLink>
        <c-CNavigationMenuItem value="teams"><c-fill name="label">Teams</c-fill><c-fill name="default"><a href="#research">Research</a><br><a href="#operations">Operations</a></c-fill></c-CNavigationMenuItem>
        <c-CNavigationMenuLink href="#billing">Billing</c-CNavigationMenuLink>
      </c-CNavigationMenu>
    """


preview = NavigationOrientation()
preview  # noqa: B018
````


## Disabled states


### NavigationMenu states

[Open the rendered preview](/v/0.4.3/ui-library/components/navigation-menu/_previews/states/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationStates(Component):
    template = """
      <c-CNavigationMenu label="Navigation states">
        <c-CNavigationMenuLink href="#home" c-current="True">Current page</c-CNavigationMenuLink>
        <c-CNavigationMenuItem value="available"><c-fill name="label">Available</c-fill><c-fill name="default">Ready to explore.</c-fill></c-CNavigationMenuItem>
        <c-CNavigationMenuItem value="locked" disabled><c-fill name="label">Unavailable</c-fill><c-fill name="default">Hidden panel.</c-fill></c-CNavigationMenuItem>
      </c-CNavigationMenu>
    """


preview = NavigationStates()
preview  # noqa: B018
````


## Variants and sizes


### NavigationMenu variants and sizes

[Open the rendered preview](/v/0.4.3/ui-library/components/navigation-menu/_previews/variants/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationVariants(Component):
    template = """
      <c-CCol gap="lg"><c-CNavigationMenu label="Small plain" size="sm"><c-CNavigationMenuLink href="#one">Small</c-CNavigationMenuLink><c-CNavigationMenuItem value="more"><c-fill name="label">More</c-fill><c-fill name="default">Small panel</c-fill></c-CNavigationMenuItem></c-CNavigationMenu><c-CNavigationMenu label="Large surface" variant="surface" size="lg"><c-CNavigationMenuLink href="#two">Large</c-CNavigationMenuLink><c-CNavigationMenuItem value="details"><c-fill name="label">Details</c-fill><c-fill name="default">Large panel</c-fill></c-CNavigationMenuItem></c-CNavigationMenu></c-CCol>
    """


preview = NavigationVariants()
preview  # noqa: B018
````


## Keyboard navigation


### NavigationMenu keyboard behavior

[Open the rendered preview](/v/0.4.3/ui-library/components/navigation-menu/_previews/keyboard/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationKeyboard(Component):
    template = """
      <c-CCol gap="sm"><p>Tab normally. Use Arrow keys between top-level controls, Down to enter an open panel, and Escape to close it.</p><c-CNavigationMenu label="Keyboard example" loop><c-CNavigationMenuLink href="#start">Start</c-CNavigationMenuLink><c-CNavigationMenuItem value="topics"><c-fill name="label">Topics</c-fill><c-fill name="default"><a href="#accessibility">Accessibility</a></c-fill></c-CNavigationMenuItem><c-CNavigationMenuLink href="#finish">Finish</c-CNavigationMenuLink></c-CNavigationMenu></c-CCol>
    """


preview = NavigationKeyboard()
preview  # noqa: B018
````


## Customize NavigationMenu


### Customize NavigationMenu

[Open the rendered preview](/v/0.4.3/ui-library/components/navigation-menu/_previews/customization/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomNavigation(Component):
    template = """
      <c-CNavigationMenu label="Aurora navigation" class_="aurora-nav" variant="surface"><c-CNavigationMenuLink href="#mission">Mission</c-CNavigationMenuLink><c-CNavigationMenuItem value="field-notes"><c-fill name="label">Field notes</c-fill><c-fill name="default"><strong>Fresh observations</strong><p>Follow the latest work from the field.</p></c-fill></c-CNavigationMenuItem></c-CNavigationMenu>
    """
    css = """
      .aurora-nav { --cui-navigation-menu-trigger-open-background:#dbeafe; --cui-navigation-menu-radius:1rem; --cui-navigation-menu-panel-inline-size:20rem; }
    """


preview = CustomNavigation()
preview  # noqa: B018
````


## Accessibility and interaction

Give every root a concise `label`. Links remain native and all top-level links
and disclosure Buttons remain in ordinary Tab order. Arrow keys provide an
additional convenience between top-level controls; Escape closes an open panel
and returns focus to its Button. Panels can contain ordinary links, Buttons,
and forms, but nested NavigationMenu disclosures are intentionally deferred.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CNavigationMenu server inputs

Server inputs are passed in a template through `<c-CNavigationMenu ... />` or in Python
through `CNavigationMenu(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="navigation-menu-input-navigation-menu-server-inputs-label"></span>`label` | `str` | required | Names the native navigation landmark. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-id"></span>`id` | `str | None` | generated | Sets root identity and generated trigger/panel relationship prefixes. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-value"></span>`value` | `str | None` | `None` | Selects the server-open Item and uncontrolled fallback. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CNavigationMenuOrientation`](#navigation-menu-interface-orientation)) | `"horizontal"` | Sets visual layout and optional arrow-key axis. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Prevents disclosure opening and forces an open panel closed. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-delay"></span>`delay` | `int` | `200` | Sets fine-pointer open delay from 0 through 60000 milliseconds. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-close-delay"></span>`close_delay` | `int` | `300` | Sets fine-pointer root-leave close delay from 0 through 60000 milliseconds. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-loop"></span>`loop` | `bool` | `False` | Allows optional top-level arrow navigation to wrap. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-variant"></span>`variant` | `"plain" | "surface"` ([`CNavigationMenuVariant`](#navigation-menu-interface-variant)) | `"plain"` | Selects root visual treatment. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CNavigationMenuSize`](#navigation-menu-interface-size)) | `"md"` | Selects geometry for the complete tree. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-class"></span>`class_` | `CClassValue` ([`CClassValue`](#navigation-menu-interface-class-value)) | `None` | Adds root classes. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-style"></span>`style` | `CStyleValue` ([`CStyleValue`](#navigation-menu-interface-style-value)) | `None` | Adds root inline styles. |
| <span id="navigation-menu-input-navigation-menu-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native and data attributes to the nav root. |

</div>

#### CNavigationMenu client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CNavigationMenu />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="navigation-menu-input-navigation-menu-client-inputs-value"></span>`value` | `string | null` | Releases control and preserves committed state. | Controls the open Item while supplied. |
| <span id="navigation-menu-input-navigation-menu-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Reactively disables disclosure behavior. |
| <span id="navigation-menu-input-navigation-menu-client-inputs-delay"></span>`delay` | `integer` | Uses the server input. | Controls future pointer-open delay. |
| <span id="navigation-menu-input-navigation-menu-client-inputs-close-delay"></span>`closeDelay` | `integer` | Uses the server input. | Controls future pointer-close delay. |
| <span id="navigation-menu-input-navigation-menu-client-inputs-loop"></span>`loop` | `boolean` | Uses the server input. | Controls arrow-key wrapping. |
| <span id="navigation-menu-input-navigation-menu-client-inputs-orientation"></span>`orientation` | `CNavigationMenuOrientation` | Uses the server input. | Changes layout and keyboard axis. |
| <span id="navigation-menu-input-navigation-menu-client-inputs-variant"></span>`variant` | `CNavigationMenuVariant` | Uses the server input. | Changes root treatment. |
| <span id="navigation-menu-input-navigation-menu-client-inputs-size"></span>`size` | `CNavigationMenuSize` | Uses the server input. | Changes tree geometry. |
| <span id="navigation-menu-input-navigation-menu-client-inputs-on-value-change"></span>`onValueChange` | `function` | Does not notify a component callback. | Receives open-value requests and forced safety closes. |

</div>

#### CNavigationMenuLink server inputs

Server inputs are passed in a template through `<c-CNavigationMenuLink ... />` or in Python
through `CNavigationMenuLink(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="navigation-menu-input-navigation-menu-link-server-inputs-href"></span>`href` | `str` | required | Sets the native link destination without URL rewriting. |
| <span id="navigation-menu-input-navigation-menu-link-server-inputs-current"></span>`current` | `bool` | `False` | Emits aria-current page. |
| <span id="navigation-menu-input-navigation-menu-link-server-inputs-target"></span>`target` | `str | None` | `None` | Sets native target. |
| <span id="navigation-menu-input-navigation-menu-link-server-inputs-rel"></span>`rel` | `str | None` | `None` | Sets native rel. |
| <span id="navigation-menu-input-navigation-menu-link-server-inputs-download"></span>`download` | `str | None` | `None` | Sets native download. |
| <span id="navigation-menu-input-navigation-menu-link-server-inputs-class"></span>`class_` | `CClassValue` ([`CClassValue`](#navigation-menu-interface-class-value)) | `None` | Adds list-item classes. |
| <span id="navigation-menu-input-navigation-menu-link-server-inputs-style"></span>`style` | `CStyleValue` ([`CStyleValue`](#navigation-menu-interface-style-value)) | `None` | Adds list-item styles. |
| <span id="navigation-menu-input-navigation-menu-link-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed list-item attributes. |
| <span id="navigation-menu-input-navigation-menu-link-server-inputs-link-attrs"></span>`link_attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native link attributes. |

</div>

#### CNavigationMenuItem server inputs

Server inputs are passed in a template through `<c-CNavigationMenuItem ... />` or in Python
through `CNavigationMenuItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="navigation-menu-input-navigation-menu-item-server-inputs-value"></span>`value` | `str` | required | Sets unique Item identity and callback value. |
| <span id="navigation-menu-input-navigation-menu-item-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables the disclosure Button. |
| <span id="navigation-menu-input-navigation-menu-item-server-inputs-class"></span>`class_` | `CClassValue` ([`CClassValue`](#navigation-menu-interface-class-value)) | `None` | Adds list-item classes. |
| <span id="navigation-menu-input-navigation-menu-item-server-inputs-style"></span>`style` | `CStyleValue` ([`CStyleValue`](#navigation-menu-interface-style-value)) | `None` | Adds list-item styles. |
| <span id="navigation-menu-input-navigation-menu-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed list-item attributes. |
| <span id="navigation-menu-input-navigation-menu-item-server-inputs-trigger-attrs"></span>`trigger_attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native Button attributes. |
| <span id="navigation-menu-input-navigation-menu-item-server-inputs-panel-attrs"></span>`panel_attrs` | `Mapping[str, object] | None` | `None` | Adds allowed panel attributes. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CNavigationMenu slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="navigation-menu-slot-navigation-menu-slots-default"></span>`default` | yes | `{}` ([`CNavigationMenuDefaultSlotData`](#navigation-menu-interface-root-slot)) | none |

</div>

#### CNavigationMenuLink slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="navigation-menu-slot-navigation-menu-link-slots-default"></span>`default` | yes | `{}` ([`CNavigationMenuLinkDefaultSlotData`](#navigation-menu-interface-link-slot)) | none |

</div>

#### CNavigationMenuItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="navigation-menu-slot-navigation-menu-item-slots-label"></span>`label` | yes | `{}` ([`CNavigationMenuItemLabelSlotData`](#navigation-menu-interface-item-label-slot)) | none |
| <span id="navigation-menu-slot-navigation-menu-item-slots-default"></span>`default` | yes | `{}` ([`CNavigationMenuItemDefaultSlotData`](#navigation-menu-interface-item-default-slot)) | none |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CNavigationMenu events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="navigation-menu-event-navigation-menu-events-on-value-change"></span>`onValueChange` | `(value: string | null, detail: CNavigationMenuValueChangeDetail) => void` ([`CNavigationMenuValueChangeDetail`](#navigation-menu-interface-value-change-detail)) | Trigger, hover, Escape, outside interaction, link activation, disabledness, or structure requests a different open value. | `{value, previousValue, reason, controlled, forced, source}` ([`CNavigationMenuValueChangeDetail`](#navigation-menu-interface-value-change-detail)) | Uncontrolled requests commit before notification; controlled requests wait for acceptance; safety closes are forced. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CNavigationMenu CSS variables

Apply these variables to `CNavigationMenu` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="navigation-menu-css-navigation-menu-css-variables-background"></span>`--cui-navigation-menu-background` | `color` | Root background. | `transparent` |
| <span id="navigation-menu-css-navigation-menu-css-variables-foreground"></span>`--cui-navigation-menu-foreground` | `color` | Tree foreground. | `CanvasText` |
| <span id="navigation-menu-css-navigation-menu-css-variables-border-color"></span>`--cui-navigation-menu-border-color` | `color` | Surface boundaries. | `Scheme-aware neutral.` |
| <span id="navigation-menu-css-navigation-menu-css-variables-trigger-background"></span>`--cui-navigation-menu-trigger-background` | `color` | Resting top-level control background. | `transparent` |
| <span id="navigation-menu-css-navigation-menu-css-variables-trigger-hover-background"></span>`--cui-navigation-menu-trigger-hover-background` | `color` | Hovered control background. | `Scheme-aware neutral.` |
| <span id="navigation-menu-css-navigation-menu-css-variables-trigger-open-background"></span>`--cui-navigation-menu-trigger-open-background` | `color` | Open control background. | `Scheme-aware neutral.` |
| <span id="navigation-menu-css-navigation-menu-css-variables-focus-color"></span>`--cui-navigation-menu-focus-color` | `color` | Focus ring. | `Highlight` |
| <span id="navigation-menu-css-navigation-menu-css-variables-radius"></span>`--cui-navigation-menu-radius` | `length` | Root and panel radius. | `0.75rem` |
| <span id="navigation-menu-css-navigation-menu-css-variables-gap"></span>`--cui-navigation-menu-gap` | `length` | Top-level gap. | `0.25rem` |
| <span id="navigation-menu-css-navigation-menu-css-variables-padding"></span>`--cui-navigation-menu-padding` | `length` | Root padding. | `Size-derived.` |
| <span id="navigation-menu-css-navigation-menu-css-variables-panel-background"></span>`--cui-navigation-menu-panel-background` | `color` | Panel surface. | `Canvas` |
| <span id="navigation-menu-css-navigation-menu-css-variables-panel-inline-size"></span>`--cui-navigation-menu-panel-inline-size` | `length` | Preferred panel width. | `24rem` |
| <span id="navigation-menu-css-navigation-menu-css-variables-panel-max-inline-size"></span>`--cui-navigation-menu-panel-max-inline-size` | `length` | Viewport-safe maximum panel width. | `calc(100vw - 2rem)` |
| <span id="navigation-menu-css-navigation-menu-css-variables-panel-padding"></span>`--cui-navigation-menu-panel-padding` | `length` | Panel padding. | `1rem` |
| <span id="navigation-menu-css-navigation-menu-css-variables-panel-shadow"></span>`--cui-navigation-menu-panel-shadow` | `shadow` | Panel elevation. | `Scheme-aware shadow.` |
| <span id="navigation-menu-css-navigation-menu-css-variables-offset"></span>`--cui-navigation-menu-offset` | `length` | Panel offset. | `0.45rem` |
| <span id="navigation-menu-css-navigation-menu-css-variables-duration"></span>`--cui-navigation-menu-duration` | `time` | Indicator transition duration. | `150ms` |
| <span id="navigation-menu-css-navigation-menu-css-variables-easing"></span>`--cui-navigation-menu-easing` | `easing` | Indicator transition easing. | `ease-out` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CNavigationMenu attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="navigation-menu-attribute-navigation-menu-attributes-aria-label"></span>`aria-label` | Root nav | `string` | Names the navigation landmark. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-data-orientation"></span>`data-orientation` | Root nav | `CNavigationMenuOrientation` | Reflects layout and arrow-key axis. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-data-disabled"></span>`data-disabled` | Root and disabled Item/trigger | `present | absent` | Reflects effective component disabledness. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-data-loop"></span>`data-loop` | Root nav | `present | absent` | Reflects arrow wrapping. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-data-variant"></span>`data-variant` | Root nav | `CNavigationMenuVariant` | Reflects treatment. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-data-size"></span>`data-size` | Root nav | `CNavigationMenuSize` | Reflects geometry. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-data-value"></span>`data-value` | Root Item trigger and panel | `string` | Reflects open or owned Item identity according to destination. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-data-open"></span>`data-open` | Open Item trigger and panel | `present | absent` | Reflects open state. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-aria-current"></span>`aria-current` | Current Link | `"page"` | Identifies the current destination. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-aria-controls"></span>`aria-controls` | Item trigger | `IDREF` | Points to the adjacent panel. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-aria-expanded"></span>`aria-expanded` | Item trigger | `"true" | "false"` | Reflects panel visibility. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-disabled"></span>`disabled` | Item trigger | `present | absent` | Uses native Button disabledness. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-hidden"></span>`hidden` | Closed panel | `present | absent` | Removes closed content from rendering and accessibility. |
| <span id="navigation-menu-attribute-navigation-menu-attributes-inert"></span>`inert` | Closed panel | `present | absent` | Prevents programmatic closed-panel interaction. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CNavigationMenu selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="navigation-menu-selector-navigation-menu-selectors-root"></span>`[data-citry-ui-part="navigation-menu"]` | nav | Root style and attrs destination. |
| <span id="navigation-menu-selector-navigation-menu-selectors-list"></span>`[data-citry-ui-part="list"]` | ul | Direct child collection. |
| <span id="navigation-menu-selector-navigation-menu-selectors-link-item"></span>`[data-citry-ui-part="link-item"]` | Link li | Link list item. |
| <span id="navigation-menu-selector-navigation-menu-selectors-link"></span>`[data-citry-ui-part="link"]` | Native a | Navigation destination. |
| <span id="navigation-menu-selector-navigation-menu-selectors-item"></span>`[data-citry-ui-part="item"]` | Disclosure li | Item state boundary. |
| <span id="navigation-menu-selector-navigation-menu-selectors-trigger"></span>`[data-citry-ui-part="trigger"]` | Native Button | Disclosure control. |
| <span id="navigation-menu-selector-navigation-menu-selectors-indicator"></span>`[data-citry-ui-part="indicator"]` | Decorative span | Open-state chevron. |
| <span id="navigation-menu-selector-navigation-menu-selectors-panel"></span>`[data-citry-ui-part="panel"]` | Neutral div | Rich navigation content. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="navigation-menu-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="navigation-menu-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="navigation-menu-interface-orientation"></span>`CNavigationMenuOrientation` | `Literal["horizontal", "vertical"]` |
| <span id="navigation-menu-interface-variant"></span>`CNavigationMenuVariant` | `Literal["plain", "surface"]` |
| <span id="navigation-menu-interface-size"></span>`CNavigationMenuSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="navigation-menu-interface-root-slot"></span>

#### `CNavigationMenuDefaultSlotData`

Empty dataclass: `{}`.

<span id="navigation-menu-interface-link-slot"></span>

#### `CNavigationMenuLinkDefaultSlotData`

Empty dataclass: `{}`.

<span id="navigation-menu-interface-item-label-slot"></span>

#### `CNavigationMenuItemLabelSlotData`

Empty dataclass: `{}`.

<span id="navigation-menu-interface-item-default-slot"></span>

#### `CNavigationMenuItemDefaultSlotData`

Empty dataclass: `{}`.

<span id="navigation-menu-interface-value-change-detail"></span>

#### `CNavigationMenuValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="navigation-menu-interface-value-change-detail-value"></span>`value` | `str | None` | - | Requested open value. |
| <span id="navigation-menu-interface-value-change-detail-previous"></span>`previousValue` | `str | None` | - | Previously effective value. |
| <span id="navigation-menu-interface-value-change-detail-reason"></span>`reason` | `string` | - | Request source. |
| <span id="navigation-menu-interface-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a supplied client value owns state. |
| <span id="navigation-menu-interface-value-change-detail-forced"></span>`forced` | `boolean` | - | Whether safety close overrides control. |
| <span id="navigation-menu-interface-value-change-detail-source"></span>`source` | `EventTarget | null` | - | Browser source. |

</div>

### Translation keys

-