---
title: Tooltip
url: https://citry.dev/v/0.4.2/ui-library/components/tooltip/
description: "Add accessible, noninteractive descriptions to focusable controls with Citry UI Tooltip."
---
# Tooltip

Use `CTooltip` for brief descriptions that appear on keyboard focus or
fine-pointer hover. It keeps focus on the activator, crosses the pointer gap,
and enters the browser top layer without moving its DOM.

## Tooltip at a glance

Focus or hover each Button. The first hover waits briefly; nearby Tooltips then
open immediately.


### Tooltip at a glance

[Open the rendered preview](/v/0.4.2/ui-library/components/tooltip/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TooltipAtAGlance(Component):
    template = """
      <section class="tooltip-sampler">
        <c-CTooltip text="Ocean world beneath fractured ice" placement="top-start">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Europa</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Bright plumes rise above the south pole" placement="top">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Enceladus</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Dense nitrogen skies conceal methane lakes" placement="top-end">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="ghost" c-attrs="activator_attrs">Titan</c-CButton>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.tooltip-sampler) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }
    """


preview = TooltipAtAGlance()

preview  # noqa: B018
````


## Describe one activator

Provide concise `text` and spread `activator_attrs` onto exactly one enabled,
focusable element.


### Describe moon controls

[Open the rendered preview](/v/0.4.2/ui-library/components/tooltip/_previews/moon-labels/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MoonLabels(Component):
    template = """
      <section class="moon-labels">
        <c-CTooltip text="Inspect Europa's fractured water-ice crust">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Europa</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Compare Ganymede's ancient grooved terrain">
          <c-fill name="activator" data="{ activator_attrs }">
            <a id="ganymede" class="moon-link" href="#ganymede" c-bind="activator_attrs">
              Ganymede
            </a>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Filter observations recorded near Callisto">
          <c-fill name="activator" data="{ activator_attrs }">
            <button class="moon-icon" type="button" aria-label="Filter Callisto" c-bind="activator_attrs">
              ◌
            </button>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.moon-labels) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 10rem;
        padding-block: 2rem;
      }

      :where(.moon-link) {
        color: light-dark(#175cd3, #84adff);
        font-weight: 700;
      }

      :where(.moon-icon) {
        display: grid;
        place-items: center;
        inline-size: 2.75rem;
        block-size: 2.75rem;
        border: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
        border-radius: 50%;
        background: Canvas;
        color: CanvasText;
        font-size: 1.5rem;
      }
    """


preview = MoonLabels()

preview  # noqa: B018
````



```citry-html
<c-CTooltip text="Inspect Europa's fractured ice">
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">
      Europa
    </c-CButton>
  </c-fill>
</c-CTooltip>
```


`text` supplements the activator's accessible name. It does not replace one.
An icon-only Button still needs its own accessible name.

The activator may be a Button, link with `href`, form control, or another
element with a real keyboard focus path. Tooltip rejects disabled and
nonfocusable activators; persistent text is clearer for unavailable controls.

## Add simple formatting

Omit `text` and supply the default fill for static, noninteractive formatting.


### Format a description

[Open the rendered preview](/v/0.4.2/ui-library/components/tooltip/_previews/formatted-description/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormattedTooltip(Component):
    template = """
      <section class="formatted-tooltip">
        <c-CTooltip placement="bottom">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">
              Europa orbit
            </c-CButton>
          </c-fill>
          <c-fill name="default">
            Orbital period: <strong>3.55 Earth days</strong>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.formatted-tooltip) {
        display: grid;
        place-items: center;
        min-block-size: 12rem;
      }
    """


preview = FormattedTooltip()

preview  # noqa: B018
````



```citry-html
<c-fill name="default">
  Orbital period: <strong>3.55 Earth days</strong>
</c-fill>
```


Do not put links, Buttons, form controls, editable content, widgets, or nested
Tooltips in the surface. Use `CPopover` for interactive content. Keep essential
instructions and validation feedback persistently visible.

## Update text in the browser

Client inputs are passed through `$c-props="{...}"`. Client `text` safely
updates a Tooltip authored with the server `text` input.


### Update Tooltip text

[Open the rendered preview](/v/0.4.2/ui-library/components/tooltip/_previews/live-text/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LiveTooltipText(Component):
    template = """
      <section class="live-tooltip" x-data="{ unit: 'kilometres' }">
        <c-CTooltip
          text="Europa is 3,122 kilometres wide"
          $c-props="{
            text: unit === 'kilometres'
              ? 'Europa is 3,122 kilometres wide'
              : 'Europa is 1,940 miles wide',
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Europa diameter</c-CButton>
          </c-fill>
        </c-CTooltip>
        <label>
          Units
          <select x-model="unit">
            <option value="kilometres">Kilometres</option>
            <option value="miles">Miles</option>
          </select>
        </label>
      </section>
    """

    css = """
      :where(.live-tooltip) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 11rem;
        padding-block: 2rem;
      }

      :where(.live-tooltip label) {
        display: grid;
        gap: 0.25rem;
        font-size: 0.875rem;
      }
    """


preview = LiveTooltipText()

preview  # noqa: B018
````


Use the default fill for server-authored formatting; client text does not
replace arbitrary slotted markup.

## Tune hover timing

Focus always opens immediately. `delay` affects only the first fine-pointer
hover. `close_delay` keeps a bridge open while the pointer moves from the
activator onto the Tooltip.


### Compare hover timing

[Open the rendered preview](/v/0.4.2/ui-library/components/tooltip/_previews/timing/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TooltipTiming(Component):
    template = """
      <section class="tooltip-timing">
        <c-CTooltip text="Opens after the standard 600 ms hover delay">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Standard delay</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Opens without an initial hover delay" c-delay="0">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Immediate</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="A longer bridge makes the surface easier to reach" c-close_delay="500">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="ghost" c-attrs="activator_attrs">Long bridge</c-CButton>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.tooltip-timing) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }
    """


preview = TooltipTiming()

preview  # noqa: B018
````


Once one Tooltip opens, nearby Tooltips skip the first-hover delay until a
short cooldown ends. No provider or group component is required.

## Control visibility

Supply a client Boolean `open` to control visual visibility. `onOpenChange`
reports requests; update the owner value to accept one or leave it unchanged
to decline it.


### Control Tooltip visibility

[Open the rendered preview](/v/0.4.2/ui-library/components/tooltip/_previews/controlled-open/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledTooltip(Component):
    template = """
      <section class="controlled-tooltip" x-data="{ open: false, locked: false, reason: 'none' }">
        <c-CTooltip
          text="Controlled description for the Europa archive"
          $c-props="{
            open,
            onOpenChange: (nextOpen, detail) => {
              reason = detail.reason;
              if (!locked) open = nextOpen;
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Europa archive</c-CButton>
          </c-fill>
        </c-CTooltip>
        <label>
          <input type="checkbox" x-model="locked" />
          Decline requests
        </label>
        <output x-text="`Last request: ${reason}`"></output>
      </section>
    """

    css = """
      :where(.controlled-tooltip) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.controlled-tooltip output) {
        flex-basis: 100%;
        color: color-mix(in srgb, CanvasText 72%, transparent);
      }
    """


preview = ControlledTooltip()

preview  # noqa: B018
````



```citry-html
<c-CTooltip
  text="Europa has a hidden ocean"
  $c-props="{
    open,
    onOpenChange: (nextOpen) => open = nextOpen,
  }"
>
  ...
</c-CTooltip>
```


Without client `open`, Tooltip commits requests itself and then notifies.
Passing `null` or omitting the client value releases control without resetting
the current state. Owner commits do not notify. Callback detail reports the
interaction reason, controlled ownership, browser source, and whether an
ancestor or modal safety rule forced the Tooltip closed.

## Place the surface

Server inputs are passed through `<c-CTooltip ... />` attributes or a
`CTooltip(...)` composition call. `placement` accepts logical top and bottom
start, center, and end positions. The browser may flip the surface near an
edge.


### Place a Tooltip

[Open the rendered preview](/v/0.4.2/ui-library/components/tooltip/_previews/placements/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TooltipPlacements(Component):
    template = """
      <section
        class="tooltip-placement"
        x-data="{ placement: 'top' }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <c-CTooltip
          text="The browser may flip this surface near an edge"
          $c-props="{ placement }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Place orbital note</c-CButton>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.tooltip-placement) {
        display: grid;
        place-items: center;
        min-block-size: 20rem;
      }
    """


preview_controls = (
    {
        "name": "placement",
        "label": "Placement",
        "type": "select",
        "default": "top",
        "options": (
            ("top-start", "Top start"),
            ("top", "Top"),
            ("top-end", "Top end"),
            ("bottom-start", "Bottom start"),
            ("bottom", "Bottom"),
            ("bottom-end", "Bottom end"),
        ),
    },
)

preview = TooltipPlacements()

preview  # noqa: B018
````


Start and end follow text direction. Change the activator gap with
`--cui-tooltip-offset`; change line length with
`--cui-tooltip-max-inline-size`.

## Dismiss and revisit

Escape closes only the top Tooltip and leaves focus on the activator. Pressing
an open activator also dismisses its Tooltip without canceling the native
action. It stays closed until focus and pointer both leave, so it does not
immediately reopen.


### Dismiss a Tooltip

[Open the rendered preview](/v/0.4.2/ui-library/components/tooltip/_previews/dismissal/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TooltipDismissal(Component):
    template = """
      <section class="tooltip-dismissal">
        <p>Focus the Button, press Escape, then move focus away and return.</p>
        <c-CTooltip text="Escape closes this description without moving focus">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Europa telemetry</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CButton variant="outline">Next observation</c-CButton>
      </section>
    """

    css = """
      :where(.tooltip-dismissal) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.tooltip-dismissal p) {
        flex-basis: 100%;
        margin: 0;
      }
    """


preview = TooltipDismissal()

preview  # noqa: B018
````


Touch activation does not show a visual Tooltip. The interface must remain
understandable without one.

## Theme Tooltip

Set public `--cui-tooltip-*` variables on an ancestor or one surface.


### Theme Tooltips

[Open the rendered preview](/v/0.4.2/ui-library/components/tooltip/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedTooltip(Component):
    template = """
      <section class="custom-tooltips">
        <c-CTooltip text="Charged particles paint green arcs" class_="aurora-tooltip">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Auroral oval</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Ancient pale terrain surrounds dark maria" class_="lunar-tooltip">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Lunar highlands</c-CButton>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.custom-tooltips) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.aurora-tooltip) {
        --cui-tooltip-background: light-dark(#064e3b, #d1fae5);
        --cui-tooltip-foreground: light-dark(#ecfdf5, #052e2b);
        --cui-tooltip-border-color: light-dark(#34d399, #6ee7b7);
        --cui-tooltip-radius: 1rem;
      }

      :where(.lunar-tooltip) {
        --cui-tooltip-background: light-dark(#334155, #e2e8f0);
        --cui-tooltip-foreground: light-dark(#f8fafc, #172033);
        --cui-tooltip-border-color: light-dark(#94a3b8, #64748b);
        --cui-tooltip-shadow: 0 0.75rem 2rem rgb(15 23 42 / 30%);
      }
    """


preview = CustomizedTooltip()

preview  # noqa: B018
````



```css
.aurora-tooltip {
  --cui-tooltip-background: light-dark(#064e3b, #d1fae5);
  --cui-tooltip-foreground: light-dark(#ecfdf5, #052e2b);
  --cui-tooltip-border-color: light-dark(#34d399, #6ee7b7);
  --cui-tooltip-radius: 1rem;
}
```


`class_`, `style`, and `attrs` target the Tooltip surface. The activator stays
owned by its authored component. Unlayered consumer CSS overrides Citry UI
defaults; named layers follow the site-wide layer-order contract.

The documented variables, selector, and reflected attributes are public CSS
API. `.cui-*` classes, `--_cui-*` variables, host markup, initialization
markers, and anchor names are private.

## Support long text, RTL, and zoom


### Use long RTL descriptions

[Open the rendered preview](/v/0.4.2/ui-library/components/tooltip/_previews/responsive-text/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ResponsiveTooltipText(Component):
    template = """
      <section class="responsive-tooltips" dir="rtl">
        <c-CTooltip
          text="أوروبا قمر جليدي يخفي محيطًا عالميًا تحت قشرته المتشققة"
          placement="bottom-start"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">أوروبا</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip
          text="Averylongunbrokenastronomicalcatalogidentifierwrapswithoutwideningthepage"
          placement="bottom-end"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Catalog ID</c-CButton>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.responsive-tooltips) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.responsive-tooltips [data-citry-ui-part="tooltip"]) {
        --cui-tooltip-max-inline-size: 13rem;
      }
    """


preview = ResponsiveTooltipText()

preview  # noqa: B018
````


Logical placement, a viewport-safe maximum, and aggressive wrapping keep text
reachable at narrow widths and high zoom. The surface follows surrounding
light/dark scope even in the top layer. Forced colors preserve its boundary;
reduced motion removes transitions; print omits visual Tooltips.

Without JavaScript, an initially closed Tooltip remains hidden. An initially
open Tooltip renders readable text in document flow, then activation upgrades
it to the top layer.

## Choose the right surface

- Use `CPopover` for links, controls, forms, or other interactive content.
- Use `CAlert` for persistent status or feedback.
- Use a Field description for instructions tied to a form control.
- Use visible prose when the information is essential to completing a task.

## API reference

### Inputs

#### CTooltip server inputs

Server inputs are passed in a template through `<c-CTooltip ... />` or in Python through
`CTooltip(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tooltip-input-ctooltip-server-inputs-id"></span>`id` | `str | None` | generated | Sets the Tooltip identity and activator description relationship. |
| <span id="tooltip-input-ctooltip-server-inputs-text"></span>`text` | `str | None` | `None` | Supplies concise plain text. Use either `text` or the default fill, never both. |
| <span id="tooltip-input-ctooltip-server-inputs-open"></span>`open` | `bool` | `False` | Sets the server-visible initial state and uncontrolled fallback. |
| <span id="tooltip-input-ctooltip-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Suppresses visual opening without changing the activator itself. |
| <span id="tooltip-input-ctooltip-server-inputs-delay"></span>`delay` | `int` | `600` | Sets the first fine-pointer hover delay in milliseconds from 0 through 60000. Focus remains immediate. |
| <span id="tooltip-input-ctooltip-server-inputs-close-delay"></span>`close_delay` | `int` | `100` | Sets the pointer bridge delay in milliseconds from 0 through 60000. |
| <span id="tooltip-input-ctooltip-server-inputs-placement"></span>`placement` | `"top-start" | "top" | "top-end" | "bottom-start" | "bottom" | "bottom-end"` ([`CTooltipPlacement`](#tooltip-interface-input-type-aliases-ctooltip-placement)) | `"top"` | Sets the preferred logical placement. Collision fallback may choose another rendered side. |
| <span id="tooltip-input-ctooltip-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#tooltip-interface-input-type-aliases-class-value)) | `None` | Adds surface classes and merges them with `attrs`. |
| <span id="tooltip-input-ctooltip-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#tooltip-interface-input-type-aliases-style-value)) | `None` | Adds surface inline styles and merges them with `attrs`; Citry retains anchor ownership. |
| <span id="tooltip-input-ctooltip-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native, Alpine, and data attributes to the Tooltip surface. Owned presence, semantics, focus, and relationships are rejected. |

</div>

#### CTooltip client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTooltip />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="tooltip-input-ctooltip-client-inputs-open"></span>`open` | `boolean | null` | Releases control and preserves the current committed state. `null` has the same effect. | Controls visual visibility while supplied as a Boolean. Disabled still dominates. |
| <span id="tooltip-input-ctooltip-client-inputs-text"></span>`text` | `string` | Uses server `text`. | Replaces plain text in text mode. Supplying it to a slotted Tooltip is invalid. |
| <span id="tooltip-input-ctooltip-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls Tooltip-local availability. |
| <span id="tooltip-input-ctooltip-client-inputs-delay"></span>`delay` | `integer` | Uses the server input. | Controls future first-hover delay from 0 through 60000 milliseconds. |
| <span id="tooltip-input-ctooltip-client-inputs-close-delay"></span>`closeDelay` | `integer` | Uses the server input. | Controls the pointer bridge from 0 through 60000 milliseconds. |
| <span id="tooltip-input-ctooltip-client-inputs-placement"></span>`placement` | `"top-start" | "top" | "top-end" | "bottom-start" | "bottom" | "bottom-end"` ([`CTooltipPlacement`](#tooltip-interface-input-type-aliases-ctooltip-placement)) | Uses the server input. | Controls requested placement and `data-placement`. |
| <span id="tooltip-input-ctooltip-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Does not notify a component callback. | Receives hover, focus, dismissal, peer, press, and external-native visibility requests. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CTooltip slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tooltip-slot-ctooltip-slots-activator"></span>`activator` | yes | `{activator_attrs: dict[str, object], tooltip_id: str}` ([`CTooltipActivatorSlotData`](#tooltip-interface-ctooltip-activator-slot-data)) | none |
| <span id="tooltip-slot-ctooltip-slots-default"></span>`default` | no | `{}` ([`CTooltipDefaultSlotData`](#tooltip-interface-ctooltip-default-slot-data)) | Escaped `text`. Required when `text` is omitted and forbidden when it is supplied. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CTooltip events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="tooltip-event-ctooltip-events-on-open-change"></span>`onOpenChange` | `(requestedOpen: boolean, detail: CTooltipOpenChangeDetail) => void` ([`CTooltipOpenChangeDetail`](#tooltip-interface-ctooltip-open-change-detail)) | Hover, focus, pointer departure, blur, Escape, trigger press, a peer Tooltip, or external native visibility requests another state. | `{reason: "hover" | "focus" | "pointer-leave" | "blur" | "escape" | "press" | "peer" | "native" | "ancestor" | "modal", controlled: boolean, forced: boolean, source: EventTarget | null}` ([`CTooltipOpenChangeDetail`](#tooltip-interface-ctooltip-open-change-detail)) | Uncontrolled requests commit before notification. Controlled requests wait for the owner. Owner commits do not notify. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTooltip CSS variables

Apply these variables to `CTooltip` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-background"></span>`--cui-tooltip-background` | `color` | Surface background. | `Scheme-aware dark/light inverse surface.` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-foreground"></span>`--cui-tooltip-foreground` | `color` | Surface text. | `Scheme-aware inverse foreground.` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-border-color"></span>`--cui-tooltip-border-color` | `color` | Surface boundary. | `Subtle currentColor mix.` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-border-width"></span>`--cui-tooltip-border-width` | `length` | Boundary width. | `1px` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-radius"></span>`--cui-tooltip-radius` | `length` | Surface corner radius. | `0.375rem` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-shadow"></span>`--cui-tooltip-shadow` | `shadow` | Top-layer elevation. | `0 0.5rem 1.25rem rgb(15 23 42 / 24%)` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-max-inline-size"></span>`--cui-tooltip-max-inline-size` | `length` | Maximum text width. | `18rem` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-padding-block"></span>`--cui-tooltip-padding-block` | `length` | Block-axis content padding. | `0.375rem` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-padding-inline"></span>`--cui-tooltip-padding-inline` | `length` | Inline-axis content padding. | `0.625rem` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-offset"></span>`--cui-tooltip-offset` | `length` | Gap between activator and surface. | `0.375rem` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-duration"></span>`--cui-tooltip-duration` | `time` | Entry and exit duration; reduced motion resolves to zero. | `100ms` |
| <span id="tooltip-css-ctooltip-css-variables-cui-tooltip-easing"></span>`--cui-tooltip-easing` | `easing` | Entry and exit easing. | `cubic-bezier(0.2, 0.8, 0.2, 1)` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTooltip attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tooltip-attribute-ctooltip-attributes-popover"></span>`popover` | Surface | `"manual"` | Uses native top-layer presence while Citry owns timing and dismissal. |
| <span id="tooltip-attribute-ctooltip-attributes-role"></span>`role` | Surface | `"tooltip"` | Identifies the noninteractive description. |
| <span id="tooltip-attribute-ctooltip-attributes-data-open"></span>`data-open` | Surface | `present | absent` | Mirrors logical visual visibility; absent during exit. |
| <span id="tooltip-attribute-ctooltip-attributes-data-placement"></span>`data-placement` | Surface | `six placement strings` ([`CTooltipPlacement`](#tooltip-interface-input-type-aliases-ctooltip-placement)) | Mirrors requested placement, not the collision fallback result. |
| <span id="tooltip-attribute-ctooltip-attributes-aria-describedby"></span>`aria-describedby` | Activator | `IDREF list` | Includes the Tooltip ID without replacing existing description relationships. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTooltip selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="tooltip-selector-ctooltip-selectors-data-citry-ui-part-tooltip"></span>`[data-citry-ui-part="tooltip"]` | Surface | Semantic root, visual surface, and attrs destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="tooltip-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="tooltip-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="tooltip-interface-input-type-aliases-ctooltip-placement"></span>`CTooltipPlacement` | `Literal["top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end"]` |

</div>

<span id="tooltip-interface-ctooltip-activator-slot-data"></span>

#### `CTooltipActivatorSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tooltip-interface-ctooltip-activator-slot-data-activator-attrs"></span>`activator_attrs` | `dict[str, object]` | - | Owned trigger marker, CSS anchor, and `aria-describedby` relationship. |
| <span id="tooltip-interface-ctooltip-activator-slot-data-tooltip-id"></span>`tooltip_id` | `str` | - | Tooltip ID for composing additional activator description IDREFs. |

</div>

<span id="tooltip-interface-ctooltip-default-slot-data"></span>

#### `CTooltipDefaultSlotData`

Empty dataclass: `{}`.

<span id="tooltip-interface-ctooltip-open-change-detail"></span>

#### `CTooltipOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tooltip-interface-ctooltip-open-change-detail-reason"></span>`reason` | `"hover" | "focus" | "pointer-leave" | "blur" | "escape" | "press" | "peer" | "native" | "ancestor" | "modal"` | - | Source of the requested visibility change. |
| <span id="tooltip-interface-ctooltip-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client `open` Boolean currently owns state. |
| <span id="tooltip-interface-ctooltip-open-change-detail-forced"></span>`forced` | `boolean` | - | Whether structural or modal safety required the component to close regardless of controlled ownership. |
| <span id="tooltip-interface-ctooltip-open-change-detail-source"></span>`source` | `EventTarget | null` | - | Browser source associated with the request. |

</div>

### Translation keys

-