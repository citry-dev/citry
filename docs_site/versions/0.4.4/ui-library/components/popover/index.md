---
title: Popover
url: https://citry.dev/v/0.4.4/ui-library/components/popover/
description: "Place accessible interactive content beside a Button with Citry UI Popover."
---
# Popover

Use `CPopover` for compact interactive content that belongs beside one Button
without blocking the rest of the page. It enters the browser top layer, so it
escapes clipping while keeping its original DOM, theme, and Form relationships.

## Popover at a glance

Open each Button to compare concise content, a description, an explicit action,
and trigger-width matching.


### Popover at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/popover/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PopoverAtAGlance(Component):
    template = """
      <section class="popover-sampler">
        <c-CPopover placement="bottom-start">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Europa
            </c-CButton>
          </c-fill>
          <c-fill name="title">Europa</c-fill>
          <c-fill name="default">An ocean world beneath fractured ice.</c-fill>
        </c-CPopover>
        <c-CPopover placement="top">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">
              Enceladus
            </c-CButton>
          </c-fill>
          <c-fill name="title">Enceladus</c-fill>
          <c-fill name="description">Saturn II</c-fill>
          <c-fill name="default">Bright plumes erupt above its south pole.</c-fill>
        </c-CPopover>
        <c-CPopover placement="bottom-end" match_width>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="ghost" c-attrs="activator_attrs">
              Titan atmosphere
            </c-CButton>
          </c-fill>
          <c-fill name="title">Titan</c-fill>
          <c-fill name="default">A dense nitrogen sky conceals methane lakes.</c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton size="sm" c-attrs="close_attrs">
              Mark explored
            </c-CButton>
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.popover-sampler) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }
    """


preview = PopoverAtAGlance()

preview  # noqa: B018
````


## Build a Popover

Provide an activator, visible title, and body. Spread `activator_attrs` onto one
native Button. `CButton` renders the required Button when `href` is omitted.


### Inspect a moon

[Open the rendered preview](/v/0.4.4/ui-library/components/popover/_previews/moon-inspector/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MoonInspector(Component):
    template = """
      <section class="moon-inspector">
        <p>Jovian system</p>
        <h2>Four worlds orbit a striped giant</h2>
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Inspect Europa
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Europa
          </c-fill>
          <c-fill name="description">
            Jupiter II · mean radius 1,560.8 km
          </c-fill>
          <c-fill name="default">
            Its fractured water-ice crust may cover a global saltwater ocean.
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.moon-inspector) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.moon-inspector h2, .moon-inspector p) {
        margin: 0;
      }

      :where(.moon-inspector > p) {
        color: light-dark(#4338ca, #a5b4fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = MoonInspector()

preview  # noqa: B018
````



```citry-html
<c-CPopover>
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">
      Inspect Europa
    </c-CButton>
  </c-fill>
  <c-fill name="title">
    Europa
  </c-fill>
  <c-fill name="description">
    Jupiter II · mean radius 1,560.8 km
  </c-fill>
  <c-fill name="default">
    Its fractured water-ice crust may cover a global ocean.
  </c-fill>
</c-CPopover>
```


The title becomes the accessible name. Keep `description` concise; place
structured or lengthy content in the body.

The activator must resolve to exactly one native Button. Do not use an anchor,
generic element, or several controls. Disable that Button itself when opening
is unavailable so native semantics, styling, and Popover behavior agree.

## Add interactive content and actions

The body accepts native controls and nested components. Content stays mounted,
so edits survive closing and reopening. Spread `close_attrs` only onto actions
that should request closure.


### Edit an orbit note

[Open the rendered preview](/v/0.4.4/ui-library/components/popover/_previews/interactive-form/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InteractivePopover(Component):
    template = """
      <section class="orbit-editor">
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Adjust orbit note
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Orbit note
          </c-fill>
          <c-fill name="description">
            Changes stay in the native Form after closing.
          </c-fill>
          <c-fill name="default">
            <form id="orbit-form">
              <label for="orbit-label">Label</label>
              <input id="orbit-label" name="label" value="Perijove pass" />
              <label for="orbit-detail">Detail</label>
              <textarea id="orbit-detail" name="detail">Closest approach before sunrise.</textarea>
            </form>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton variant="ghost" c-attrs="close_attrs">
              Cancel
            </c-CButton>
            <c-CButton c-attrs="close_attrs">
              Keep note
            </c-CButton>
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.orbit-editor) {
        min-block-size: 15rem;
        padding-block: 3rem;
      }

      :where(#orbit-form) {
        display: grid;
        gap: 0.5rem;
      }

      :where(#orbit-form input, #orbit-form textarea) {
        box-sizing: border-box;
        inline-size: 100%;
        padding: 0.5rem 0.625rem;
        border: 1px solid color-mix(in srgb, CanvasText 25%, transparent);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
      }
    """


preview = InteractivePopover()

preview  # noqa: B018
````



```citry-html
<c-fill name="actions" data="{ close_attrs }">
  <c-CButton variant="ghost" c-attrs="close_attrs">
    Cancel
  </c-CButton>
  <c-CButton c-attrs="close_attrs">
    Keep note
  </c-CButton>
</c-fill>
```


Popover never closes merely because body content was clicked. This keeps links,
inputs, selectors, and nested components predictable.

## Control visibility

Client inputs are passed in the browser through `$c-props="{...}"`. Supply a
Boolean `open` to control visibility. `onOpenChange` reports requests; update
the owner value to accept one or leave it unchanged to decline it.


### Control Popover visibility

[Open the rendered preview](/v/0.4.4/ui-library/components/popover/_previews/controlled-open/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledPopover(Component):
    template = """
      <section
        class="controlled-popover"
        x-data="{ open: false, locked: false, lastReason: 'none' }"
      >
        <c-CPopover
          $c-props="{
            open,
            onOpenChange: (nextOpen, detail) => {
              lastReason = detail.reason;
              if (!locked) open = nextOpen;
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Mission controls
            </c-CButton>
          </c-fill>
          <c-fill name="title">Mission controls</c-fill>
          <c-fill name="default">
            The owner may accept or decline every visibility request.
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Close panel</c-CButton>
          </c-fill>
        </c-CPopover>
        <label>
          <input type="checkbox" x-model="locked" />
          Decline visibility requests
        </label>
        <output x-text="`Last request: ${lastReason}`"></output>
      </section>
    """

    css = """
      :where(.controlled-popover) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.controlled-popover output) {
        flex-basis: 100%;
        color: color-mix(in srgb, CanvasText 70%, transparent);
      }
    """


preview = ControlledPopover()

preview  # noqa: B018
````



```citry-html
<c-CPopover
  $c-props="{
    open,
    onOpenChange: (nextOpen, detail) => {
      if (mayApply(nextOpen, detail)) open = nextOpen;
    },
  }"
>
  ...
</c-CPopover>
```


Without a client `open`, Popover commits user requests itself and then notifies.
Removing the client value or passing `null` releases control without resetting
the current state. Owner commits do not call back.

The callback detail identifies `trigger`, `action`, `escape`, `outside`,
`focus-outside`, unavoidable external `native` changes, and safety closures
caused by an `ancestor` or `modal`. It also includes controlled ownership,
whether the close was forced, and the browser source.

## Choose dismissal behavior

`dismissible=True` allows Escape, outside pointer, and focus-outside requests.
The activator and controls carrying `close_attrs` always remain explicit paths.


### Choose dismissal behavior

[Open the rendered preview](/v/0.4.4/ui-library/components/popover/_previews/dismissal/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PopoverDismissal(Component):
    template = """
      <section class="dismissal-samples">
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Dismissible</c-CButton>
          </c-fill>
          <c-fill name="title">Dismissible panel</c-fill>
          <c-fill name="default">Escape, outside pointer, or focus outside may close it.</c-fill>
        </c-CPopover>
        <c-CPopover c-dismissible="False">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">
              Explicit action only
            </c-CButton>
          </c-fill>
          <c-fill name="title">Protected observation</c-fill>
          <c-fill name="default">Outside interaction leaves this panel open.</c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Acknowledge</c-CButton>
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.dismissal-samples) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }
    """


preview = PopoverDismissal()

preview  # noqa: B018
````


Use `dismissible=False` when the user must choose an explicit action. Always
provide a clear close path. In controlled mode, declining a passive request
keeps the surface open and prevents that request from closing an ancestor.

## Place the surface

Server inputs are passed in Python through `<c-CPopover ... />` attributes or a
`CPopover(...)` composition call. `placement` accepts `top-start`, `top`,
`top-end`, `bottom-start`, `bottom`, or `bottom-end`. The same client input can
change it in the browser. Use client `matchWidth` or server `match_width` when
the surface should be at least as wide as the Button.


### Place a Popover

[Open the rendered preview](/v/0.4.4/ui-library/components/popover/_previews/placements/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PopoverPlacements(Component):
    template = """
      <section
        class="placement-preview"
        x-data="{ placement: 'bottom-start', match_width: false }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <c-CPopover
          $c-props="{ placement, matchWidth: match_width }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Position orbital summary
            </c-CButton>
          </c-fill>
          <c-fill name="title">Orbital summary</c-fill>
          <c-fill name="default">
            Collision fallback may flip the requested side near a viewport edge.
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.placement-preview) {
        display: grid;
        place-items: center;
        min-block-size: 22rem;
      }
    """


preview_controls = (
    {
        "name": "placement",
        "label": "Placement",
        "type": "select",
        "default": "bottom-start",
        "options": (
            ("top-start", "Top start"),
            ("top", "Top"),
            ("top-end", "Top end"),
            ("bottom-start", "Bottom start"),
            ("bottom", "Bottom"),
            ("bottom-end", "Bottom end"),
        ),
    },
    {
        "name": "match_width",
        "label": "Match activator width",
        "type": "checkbox",
        "default": False,
    },
)

preview = PopoverPlacements()

preview  # noqa: B018
````


Placement is a preference. The browser may flip it near an edge. Start and end
are logical, so they follow text direction. Change the activator gap with
`--cui-popover-offset`; use `--cui-popover-inline-size` or `style` for width.

Popover uses native top-layer rendering and CSS anchors. It does not teleport
under `<body>`, start a JavaScript geometry loop, or publish a generic placement
engine.

## Nest Popovers

Nested Popovers are valid inside a body or action. Escape and outside
interaction affect only the top open layer.


### Nest Popovers

[Open the rendered preview](/v/0.4.4/ui-library/components/popover/_previews/nested-popovers/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedPopovers(Component):
    template = """
      <section class="nested-popovers">
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Inspect Saturn</c-CButton>
          </c-fill>
          <c-fill name="title">Saturn</c-fill>
          <c-fill name="default">
            <p>Its rings contain countless ice-rich particles.</p>
            <c-CPopover placement="bottom-end">
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton size="sm" variant="outline" c-attrs="activator_attrs">
                  Inspect ring gap
                </c-CButton>
              </c-fill>
              <c-fill name="title">Cassini Division</c-fill>
              <c-fill name="default">
                A broad region shaped by orbital resonance with Mimas.
              </c-fill>
            </c-CPopover>
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.nested-popovers) {
        min-block-size: 14rem;
        padding-block: 3rem;
      }
    """


preview = NestedPopovers()

preview  # noqa: B018
````


Closing a child returns focus to its child activator and leaves the parent
open. Prefer shallow layers; a page section is clearer when content no longer
feels compact or locally related.

## Choose the right surface

Popover is a named, non-modal dialog with rich interactive content.

- Use `CDialog` when a task blocks the page or needs contained focus.
- Use `CMenu` for command/choice collection semantics and menu
  keyboard behavior.
- Use `CTooltip` for brief noninteractive text shown by hover and
  focus.
- Use `CAlert` for persistent status or feedback.

Adding a role to Popover content does not turn it into those components; each
has different activation, focus, dismissal, and assistive-technology rules.

## Theme and customize Popover

Set public `--cui-popover-*` variables on an ancestor or one surface. Use
public part selectors for targeted regions.


### Theme Popovers

[Open the rendered preview](/v/0.4.4/ui-library/components/popover/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedPopover(Component):
    template = """
      <section class="custom-popovers">
        <c-CPopover class_="aurora-popover">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Aurora palette</c-CButton>
          </c-fill>
          <c-fill name="title">Auroral oval</c-fill>
          <c-fill name="default">Charged particles paint green arcs above the poles.</c-fill>
        </c-CPopover>
        <c-CPopover class_="lunar-popover">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Lunar palette</c-CButton>
          </c-fill>
          <c-fill name="title">Lunar highlands</c-fill>
          <c-fill name="default">Ancient pale terrain surrounds younger dark maria.</c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.custom-popovers) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.aurora-popover) {
        --cui-popover-background: light-dark(#ecfdf5, #052e2b);
        --cui-popover-foreground: light-dark(#064e3b, #d1fae5);
        --cui-popover-border-color: light-dark(#6ee7b7, #34d399);
        --cui-popover-radius: 1.25rem;
      }

      :where(.lunar-popover) {
        --cui-popover-background: light-dark(#f8fafc, #172033);
        --cui-popover-foreground: light-dark(#1e293b, #f1f5f9);
        --cui-popover-border-color: light-dark(#94a3b8, #64748b);
        --cui-popover-shadow: 0 1.25rem 2.75rem rgb(15 23 42 / 30%);
      }
    """


preview = CustomizedPopover()

preview  # noqa: B018
````



```css
.aurora-popover {
  --cui-popover-background: light-dark(#ecfdf5, #052e2b);
  --cui-popover-foreground: light-dark(#064e3b, #d1fae5);
  --cui-popover-border-color: light-dark(#6ee7b7, #34d399);
  --cui-popover-radius: 1.25rem;
}
```


`class_`, `style`, and `attrs` target the Popover surface. The activator remains
owned by its own component. Unlayered consumer CSS overrides Citry UI defaults;
named layers follow the site-wide layer-order contract.

The documented variables, selectors, and reflected attributes are public CSS
API. `.cui-*` classes, `--_cui-*` variables, host markup, initialization
markers, and anchor names are private.

## Keyboard, focus, and forms

Opening focuses `[autofocus]`, then the first tabbable descendant, then the
surface itself. Popover does not trap Tab: the rest of the page remains
available. Leaving a dismissible surface closes it after focus reaches the new
destination.

Escape closes only the top open layer. Trigger, action, and Escape closure
return focus to the activator when focus was inside. Outside closure preserves
the browser's new focus destination.

Controls inside Popover retain native Form owners, values, reset, validation,
and FormData behavior. Closing does not reset them because content stays in its
original DOM and remains mounted.

## Support narrow viewports and RTL


### Use long RTL content

[Open the rendered preview](/v/0.4.4/ui-library/components/popover/_previews/responsive-content/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ResponsivePopover(Component):
    template = """
      <section class="responsive-popover" dir="rtl">
        <c-CPopover
          placement="bottom-start"
          style="--cui-popover-inline-size: 28rem"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">افتح سجل المريخ</c-CButton>
          </c-fill>
          <c-fill name="title">سجل المريخ الطويل</c-fill>
          <c-fill name="description">محتوى يختبر الاتجاه والعرض الضيق</c-fill>
          <c-fill name="default">
            <p>يبقى السطح داخل مساحة العرض ويتيح التمرير عند الحاجة.</p>
            <p>OlympusMonsSummitTraverseObservationIdentifier2026</p>
            <p>هبطت المركبة قرب سهل صخري واسع، ثم بدأت قياس الغبار والرياح.</p>
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.responsive-popover) {
        min-block-size: 14rem;
        padding-block: 3rem;
      }
    """


preview = ResponsivePopover()

preview  # noqa: B018
````


Logical dimensions, viewport maxima, wrapping, and body scrolling keep content
reachable at narrow widths and high zoom. The surface follows surrounding
light/dark scope even in the top layer. Forced colors preserve its boundary;
reduced-motion users receive immediate transitions.

Without JavaScript, an initially closed Popover stays hidden. An initially open
Popover renders readable content in document flow, then activation upgrades it
to the top layer.

## API reference

### Inputs

#### CPopover server inputs

Server inputs are passed in a template through `<c-CPopover ... />` or in Python through
`CPopover(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="popover-input-cpopover-server-inputs-id"></span>`id` | `str | None` | generated | Sets native identity and title, description, and activator relationships. |
| <span id="popover-input-cpopover-server-inputs-open"></span>`open` | `bool` | `False` | Sets the server-visible initial state and uncontrolled fallback. A valid client `open` input controls later state. |
| <span id="popover-input-cpopover-server-inputs-dismissible"></span>`dismissible` | `bool` | `True` | Permits Escape, outside-pointer, and focus-outside close requests. Trigger and explicit actions remain available when false. |
| <span id="popover-input-cpopover-server-inputs-placement"></span>`placement` | `"top-start" | "top" | "top-end" | "bottom-start" | "bottom" | "bottom-end"` ([`CPopoverPlacement`](#popover-interface-input-type-aliases-cpopover-placement)) | `"bottom-start"` | Sets the preferred logical placement. Collision fallback may choose a different rendered side. |
| <span id="popover-input-cpopover-server-inputs-match-width"></span>`match_width` | `bool` | `False` | Makes the Popover at least as wide as its activator. |
| <span id="popover-input-cpopover-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#popover-interface-input-type-aliases-class-value)) | `None` | Adds surface classes and merges them with `attrs`. |
| <span id="popover-input-cpopover-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#popover-interface-input-type-aliases-style-value)) | `None` | Adds surface inline styles and merges them with `attrs`; Citry retains anchor ownership. |
| <span id="popover-input-cpopover-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native, ARIA, Alpine, and data attributes to the Popover surface. Owned presence, semantics, focus, and relationships are rejected. |

</div>

#### CPopover client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CPopover />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="popover-input-cpopover-client-inputs-open"></span>`open` | `boolean | null` | Releases control and preserves the current committed state. `null` has the same effect. | Controls visible state while supplied as a Boolean. An invalid value reports once and releases control from the current state. |
| <span id="popover-input-cpopover-client-inputs-dismissible"></span>`dismissible` | `boolean` | Uses the server input. | Controls passive Escape, outside-pointer, and focus-outside dismissal. |
| <span id="popover-input-cpopover-client-inputs-placement"></span>`placement` | `"top-start" | "top" | "top-end" | "bottom-start" | "bottom" | "bottom-end"` ([`CPopoverPlacement`](#popover-interface-input-type-aliases-cpopover-placement)) | Uses the server input. | Controls requested placement and `data-placement`. |
| <span id="popover-input-cpopover-client-inputs-match-width"></span>`matchWidth` | `boolean` | Uses the server input. | Controls trigger-width matching and `data-match-width`. |
| <span id="popover-input-cpopover-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Does not notify a component callback. | Receives trigger, explicit-action, passive-dismissal, and external-native visibility requests. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CPopover slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="popover-slot-cpopover-slots-activator"></span>`activator` | yes | `{activator_attrs: dict[str, object]}` ([`CPopoverActivatorSlotData`](#popover-interface-cpopover-activator-slot-data)) | none |
| <span id="popover-slot-cpopover-slots-title"></span>`title` | yes | `{}` ([`CPopoverTitleSlotData`](#popover-interface-cpopover-title-slot-data)) | none |
| <span id="popover-slot-cpopover-slots-description"></span>`description` | no | `{}` ([`CPopoverDescriptionSlotData`](#popover-interface-cpopover-description-slot-data)) | Omitted, with no `aria-describedby`. |
| <span id="popover-slot-cpopover-slots-default"></span>`default` | yes | `{}` ([`CPopoverDefaultSlotData`](#popover-interface-cpopover-default-slot-data)) | none |
| <span id="popover-slot-cpopover-slots-actions"></span>`actions` | no | `{close_attrs: dict[str, object]}` ([`CPopoverActionsSlotData`](#popover-interface-cpopover-actions-slot-data)) | omitted |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CPopover events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="popover-event-cpopover-events-on-open-change"></span>`onOpenChange` | `(requestedOpen: boolean, detail: CPopoverOpenChangeDetail) => void` ([`CPopoverOpenChangeDetail`](#popover-interface-cpopover-open-change-detail)) | An owned activator, explicit action, Escape, outside pointer, focus outside, or external native Popover operation requests a different state. | `{reason: "trigger" | "action" | "escape" | "outside" | "focus-outside" | "native" | "ancestor" | "modal", controlled: boolean, forced: boolean, source: Element | EventTarget | null}` ([`CPopoverOpenChangeDetail`](#popover-interface-cpopover-open-change-detail)) | Uncontrolled requests commit before notification. Controlled requests wait for the owner. Owner commits do not notify. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CPopover CSS variables

Apply these variables to `CPopover` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="popover-css-cpopover-css-variables-cui-popover-background"></span>`--cui-popover-background` | `color` | Surface background. | `Canvas` |
| <span id="popover-css-cpopover-css-variables-cui-popover-foreground"></span>`--cui-popover-foreground` | `color` | Surface text and inherited control context. | `CanvasText` |
| <span id="popover-css-cpopover-css-variables-cui-popover-border-color"></span>`--cui-popover-border-color` | `color` | Surface boundary. | `Subtle CanvasText mix.` |
| <span id="popover-css-cpopover-css-variables-cui-popover-border-width"></span>`--cui-popover-border-width` | `length` | Boundary width. | `1px` |
| <span id="popover-css-cpopover-css-variables-cui-popover-radius"></span>`--cui-popover-radius` | `length` | Surface corner radius. | `0.75rem` |
| <span id="popover-css-cpopover-css-variables-cui-popover-shadow"></span>`--cui-popover-shadow` | `shadow` | Top-layer elevation. | `0 1rem 3rem rgb(15 23 42 / 22%)` |
| <span id="popover-css-cpopover-css-variables-cui-popover-inline-size"></span>`--cui-popover-inline-size` | `length` | Preferred surface width. | `20rem` |
| <span id="popover-css-cpopover-css-variables-cui-popover-max-inline-size"></span>`--cui-popover-max-inline-size` | `length` | Maximum responsive width. | `calc(100dvi - 1rem)` |
| <span id="popover-css-cpopover-css-variables-cui-popover-max-block-size"></span>`--cui-popover-max-block-size` | `length` | Maximum responsive height. | `calc(100dvb - 1rem)` |
| <span id="popover-css-cpopover-css-variables-cui-popover-padding"></span>`--cui-popover-padding` | `length` | Region inline and edge padding. | `1rem` |
| <span id="popover-css-cpopover-css-variables-cui-popover-gap"></span>`--cui-popover-gap` | `length` | Gap between header, body, and actions. | `0.75rem` |
| <span id="popover-css-cpopover-css-variables-cui-popover-offset"></span>`--cui-popover-offset` | `length` | Gap between activator and surface. | `0.5rem` |
| <span id="popover-css-cpopover-css-variables-cui-popover-duration"></span>`--cui-popover-duration` | `time` | Entry and exit duration; reduced motion resolves to zero. | `140ms` |
| <span id="popover-css-cpopover-css-variables-cui-popover-easing"></span>`--cui-popover-easing` | `easing` | Entry and exit easing. | `cubic-bezier(0.2, 0.8, 0.2, 1)` |
| <span id="popover-css-cpopover-css-variables-cui-popover-focus-color"></span>`--cui-popover-focus-color` | `color` | Surface fallback focus outline. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CPopover attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="popover-attribute-cpopover-attributes-popover"></span>`popover` | Surface | `"manual"` | Uses native top-layer presence while Citry owns dismissal and control. |
| <span id="popover-attribute-cpopover-attributes-role"></span>`role` | Surface | `"dialog"` | Identifies the named non-modal interactive surface. |
| <span id="popover-attribute-cpopover-attributes-aria-labelledby"></span>`aria-labelledby` | Surface | `IDREF` | References the required visible title. |
| <span id="popover-attribute-cpopover-attributes-aria-describedby"></span>`aria-describedby` | Surface | `IDREF | absent` | References the optional concise description. |
| <span id="popover-attribute-cpopover-attributes-data-open"></span>`data-open` | Surface | `present | absent` | Mirrors logical visible ownership; absent during exit. |
| <span id="popover-attribute-cpopover-attributes-data-placement"></span>`data-placement` | Surface | `six placement strings` ([`CPopoverPlacement`](#popover-interface-input-type-aliases-cpopover-placement)) | Mirrors requested placement, not the collision fallback result. |
| <span id="popover-attribute-cpopover-attributes-data-match-width"></span>`data-match-width` | Surface | `present | absent` | Indicates trigger-width matching. |
| <span id="popover-attribute-cpopover-attributes-aria-haspopup"></span>`aria-haspopup` | Activator Button | `"dialog"` | Announces the kind of surface controlled by the Button. |
| <span id="popover-attribute-cpopover-attributes-aria-controls"></span>`aria-controls` | Activator Button | `IDREF` | References the Popover surface. |
| <span id="popover-attribute-cpopover-attributes-aria-expanded"></span>`aria-expanded` | Activator Button | `"true" | "false"` | Mirrors logical open state. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CPopover selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="popover-selector-cpopover-selectors-data-citry-ui-part-popover"></span>`[data-citry-ui-part="popover"]` | Surface | Semantic root, visual surface, and attrs destination. |
| <span id="popover-selector-cpopover-selectors-data-citry-ui-part-header"></span>`[data-citry-ui-part="header"]` | Header | Title and optional-description layout. |
| <span id="popover-selector-cpopover-selectors-data-citry-ui-part-title"></span>`[data-citry-ui-part="title"]` | Title | Required visible accessible name. |
| <span id="popover-selector-cpopover-selectors-data-citry-ui-part-description"></span>`[data-citry-ui-part="description"]` | Description | Optional concise supporting text. |
| <span id="popover-selector-cpopover-selectors-data-citry-ui-part-body"></span>`[data-citry-ui-part="body"]` | Body | Required rich interactive content region. |
| <span id="popover-selector-cpopover-selectors-data-citry-ui-part-actions"></span>`[data-citry-ui-part="actions"]` | Actions | Optional explicit-action row. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="popover-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="popover-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="popover-interface-input-type-aliases-cpopover-placement"></span>`CPopoverPlacement` | `Literal["top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end"]` |

</div>

<span id="popover-interface-cpopover-activator-slot-data"></span>

#### `CPopoverActivatorSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="popover-interface-cpopover-activator-slot-data-activator-attrs"></span>`activator_attrs` | `dict[str, object]` | - | Owned trigger marker, CSS anchor, `aria-haspopup`, `aria-controls`, and synchronized `aria-expanded`. |

</div>

<span id="popover-interface-cpopover-title-slot-data"></span>

#### `CPopoverTitleSlotData`

Empty dataclass: `{}`.

<span id="popover-interface-cpopover-description-slot-data"></span>

#### `CPopoverDescriptionSlotData`

Empty dataclass: `{}`.

<span id="popover-interface-cpopover-default-slot-data"></span>

#### `CPopoverDefaultSlotData`

Empty dataclass: `{}`.

<span id="popover-interface-cpopover-actions-slot-data"></span>

#### `CPopoverActionsSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="popover-interface-cpopover-actions-slot-data-close-attrs"></span>`close_attrs` | `dict[str, object]` | - | Marks an explicit action control as a close request. |

</div>

<span id="popover-interface-cpopover-open-change-detail"></span>

#### `CPopoverOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="popover-interface-cpopover-open-change-detail-reason"></span>`reason` | `"trigger" | "action" | "escape" | "outside" | "focus-outside" | "native" | "ancestor" | "modal"` | - | Source of the requested visibility change. |
| <span id="popover-interface-cpopover-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client `open` Boolean currently owns state. |
| <span id="popover-interface-cpopover-open-change-detail-forced"></span>`forced` | `boolean` | - | Whether structural or modal safety required the component to close regardless of controlled ownership. |
| <span id="popover-interface-cpopover-open-change-detail-source"></span>`source` | `Element | EventTarget | null` | - | Browser source associated with the request. |

</div>

### Translation keys

-