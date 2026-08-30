---
title: Accordion
url: https://citry.dev/v/0.4.6/ui-library/components/accordion/
description: "Organize related sections with native headings, controlled expansion, stable panel content, and nested groups."
---
# Accordion

Use `CAccordion` for a finite group of related sections. Each
`CAccordionItem` renders a native heading and button. Panel content stays in
the document when closed, preserving forms, browser-owned values, and nested
component state.

## Accordion at a glance

Open the field-guide sections to see the complete item pattern in a compact
group.


### Accordion at a glance

[Open the rendered preview](/v/0.4.6/ui-library/components/accordion/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AccordionAtAGlance(Component):
    template = """
      <section class="forest-guide" aria-labelledby="forest-guide-title">
        <header>
          <p>Temperate rainforest</p>
          <h2 id="forest-guide-title">Layers of the forest</h2>
        </header>
        <c-CAccordion value="canopy" variant="separated">
          <c-CAccordionItem value="canopy">
            <c-fill name="title">Canopy</c-fill>
            <c-fill name="default">
              Interlocking crowns collect most sunlight and shelter the layers below.
            </c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="understory">
            <c-fill name="title">Understory</c-fill>
            <c-fill name="default">
              Ferns, saplings, and mosses thrive in filtered green light.
            </c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="floor">
            <c-fill name="title">Forest floor</c-fill>
            <c-fill name="default">
              Fungi and invertebrates return fallen wood to the soil.
            </c-fill>
          </c-CAccordionItem>
        </c-CAccordion>
      </section>
    """

    css = """
      :where(.forest-guide) {
        display: grid;
        gap: 1rem;
        max-width: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-guide h2, .forest-guide p) {
        margin: 0;
      }

      :where(.forest-guide header > p) {
        color: light-dark(#2f6b45, #86d29e);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = AccordionAtAGlance()

preview  # noqa: B018
````


## Compose Accordion items

Give every item a stable `value`, a `title` fill, and a default panel fill.


### Compose an Accordion

[Open the rendered preview](/v/0.4.6/ui-library/components/accordion/_previews/basic-accordion/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicAccordion(Component):
    template = """
      <c-CAccordion value="moss">
        <c-CAccordionItem value="moss">
          <c-fill name="title">Moss gardens</c-fill>
          <c-fill name="default">
            Moss retains moisture around roots and fallen logs.
          </c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="streams">
          <c-fill name="title">Cold streams</c-fill>
          <c-fill name="default">
            Shaded water stays cool enough for salmon and stoneflies.
          </c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="nurse-logs">
          <c-fill name="title">Nurse logs</c-fill>
          <c-fill name="default">
            Seedlings use decaying trunks as raised, nutrient-rich beds.
          </c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """


preview = BasicAccordion()

preview  # noqa: B018
````



```citry-html
<c-CAccordion value="canopy">
  <c-CAccordionItem value="canopy">
    <c-fill name="title">
      Forest canopy
    </c-fill>
    <c-fill name="default">
      The canopy captures most incoming sunlight.
    </c-fill>
  </c-CAccordionItem>
  <c-CAccordionItem value="understory">
    <c-fill name="title">
      Understory
    </c-fill>
    <c-fill name="default">
      Shade-tolerant plants grow beneath the canopy.
    </c-fill>
  </c-CAccordionItem>
</c-CAccordion>
```


For Python composition, supply one component whose output contains the direct
items. This preserves item registration without introducing a DOM wrapper.


```python
from citry import Component
from citry_ui import CAccordion


class FieldGuideItems(Component):
    template = """
      <c-CAccordionItem value="canopy">
        <c-fill name="title">Forest canopy</c-fill>
        <c-fill name="default">Upper forest layer</c-fill>
      </c-CAccordionItem>
    """


field_guide = CAccordion(
    value="canopy",
    slots={"default": FieldGuideItems()},
)
```


`CAccordionItem` is not standalone. Put it directly inside the nearest
Accordion. Transparent components may generate items when they add no wrapper
or other output.

## Control expansion in the browser

Server inputs are passed in Python through `<c-CAccordion ... />` attributes
or a `CAccordion(...)` composition call. Client inputs are passed in the
browser through `$c-props="{...}"`.


### Control Accordion value

[Open the rendered preview](/v/0.4.6/ui-library/components/accordion/_previews/controlled-value/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledAccordion(Component):
    template = """
      <section
        class="controlled-accordion"
        x-data="{selected: 'lichen'}"
      >
        <p aria-live="polite">
          Open section: <strong x-text="selected ?? 'none'">lichen</strong>
        </p>
        <c-CAccordion
          value="lichen"
          $c-props="{
            value: selected,
            onValueChange: (value) => selected = value,
          }"
        >
          <c-CAccordionItem value="lichen">
            <c-fill name="title">Lichen</c-fill>
            <c-fill name="default">A partnership between fungi and algae.</c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="mushrooms">
            <c-fill name="title">Mushrooms</c-fill>
            <c-fill name="default">Temporary fruiting bodies of hidden fungal networks.</c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="ferns">
            <c-fill name="title">Ferns</c-fill>
            <c-fill name="default">Ancient plants that reproduce through spores.</c-fill>
          </c-CAccordionItem>
        </c-CAccordion>
      </section>
    """

    css = """
      :where(.controlled-accordion) {
        display: grid;
        gap: 0.75rem;
        max-width: 44rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.controlled-accordion > p) {
        margin: 0;
        color: light-dark(#356548, #8bcda0);
      }
    """


preview = ControlledAccordion()

preview  # noqa: B018
````


Single mode uses `string | null`; multiple mode uses `string[] | null`.
`onValueChange` receives requests before an uncontrolled commit. When `value`
is supplied, update it in the callback to accept the request. Omit the client
value to release control without resetting the current valid browser state.

## Choose an expansion policy

The default single mode keeps at most one panel open. Set `multiple=True` to
open several. Set `collapsible=False` in single mode when an open item should
stay open.


### Compare expansion modes

[Open the rendered preview](/v/0.4.6/ui-library/components/accordion/_previews/expansion-modes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ExpansionModes(Component):
    template = """
      <section class="expansion-modes" aria-label="Accordion expansion modes">
        <article>
          <h2>One section, always open</h2>
          <c-CAccordion value="roots" c-collapsible="False" variant="soft">
            <c-CAccordionItem value="roots">
              <c-fill name="title">Root network</c-fill>
              <c-fill name="default">Roots trade nutrients with underground fungi.</c-fill>
            </c-CAccordionItem>
            <c-CAccordionItem value="soil">
              <c-fill name="title">Living soil</c-fill>
              <c-fill name="default">A pinch of soil can hold billions of organisms.</c-fill>
            </c-CAccordionItem>
          </c-CAccordion>
        </article>
        <article>
          <h2>Several sections</h2>
          <c-CAccordion c-value="('cedar', 'hemlock')" multiple variant="soft">
            <c-CAccordionItem value="cedar">
              <c-fill name="title">Western red cedar</c-fill>
              <c-fill name="default">Scale-like leaves stay green through winter.</c-fill>
            </c-CAccordionItem>
            <c-CAccordionItem value="hemlock">
              <c-fill name="title">Western hemlock</c-fill>
              <c-fill name="default">Drooping leaders distinguish its young crowns.</c-fill>
            </c-CAccordionItem>
          </c-CAccordion>
        </article>
      </section>
    """

    css = """
      :where(.expansion-modes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.expansion-modes article) {
        min-width: 0;
      }

      :where(.expansion-modes h2) {
        margin-block: 0 0.625rem;
        font-size: 1rem;
      }
    """


preview = ExpansionModes()

preview  # noqa: B018
````


`collapsible=False` does not force an initial selection. After a section opens,
its trigger remains focusable and exposes `aria-disabled="true"` while it is
the item that cannot close.

## Add adjacent actions

Put related Buttons, links, or menus in the `actions` slot. They render beside
the heading, never inside its trigger. `actions_label` creates one named
`group` for the controls.


### Add item actions

[Open the rendered preview](/v/0.4.6/ui-library/components/accordion/_previews/actions/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AccordionActions(Component):
    template = """
      <c-CAccordion value="trail" variant="separated">
        <c-CAccordionItem
          value="trail"
          actions_label="Trail actions"
        >
          <c-fill name="title">River trail</c-fill>
          <c-fill name="actions">
            <a href="#river-map">Map</a>
            <button type="button">Save</button>
          </c-fill>
          <c-fill name="default">
            A shaded six-kilometre route follows the river upstream.
          </c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem
          value="ridge"
          actions_label="Ridge actions"
        >
          <c-fill name="title">Ridge trail</c-fill>
          <c-fill name="actions">
            <a href="#ridge-map">Map</a>
          </c-fill>
          <c-fill name="default">
            An exposed climb reaches the old fire lookout.
          </c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """


preview = AccordionActions()

preview  # noqa: B018
````


Title content is inside a native button. Keep it to noninteractive phrasing
content. Links, form controls, nested headings, and another Accordion belong in
the panel or actions slot.

## Disable groups or items

Group `disabled` blocks every trigger. Item `disabled` blocks only that item.
An open disabled item stays open.


### Disable Accordion items

[Open the rendered preview](/v/0.4.6/ui-library/components/accordion/_previews/disabled-items/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisabledItems(Component):
    template = """
      <c-CAccordion value="open-trail">
        <c-CAccordionItem value="open-trail">
          <c-fill name="title">Fern loop</c-fill>
          <c-fill name="default">Open from dawn until dusk.</c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="closed-trail" disabled>
          <c-fill name="title">Cedar crossing — temporarily closed</c-fill>
          <c-fill name="default">High water has covered the footbridge.</c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="accessible-trail">
          <c-fill name="title">Wetland boardwalk</c-fill>
          <c-fill name="default">A level route through reeds and alder groves.</c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """


preview = DisabledItems()

preview  # noqa: B018
````


An enclosing disabled native `fieldset`, including CForm's fieldset, remains
authoritative. Client `disabled=False` cannot re-enable its descendant
buttons.

## Nest Accordion

Put a nested `CAccordion` in a panel. Do not place it in a title or action
area. The nested root becomes a new registration and keyboard boundary.


### Nest Accordion groups

[Open the rendered preview](/v/0.4.6/ui-library/components/accordion/_previews/nested-accordion/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedAccordion(Component):
    template = """
      <c-CAccordion value="trees" variant="separated">
        <c-CAccordionItem value="trees">
          <c-fill name="title">Trees</c-fill>
          <c-fill name="default">
            <p>Compare two trees found along the valley trail.</p>
            <c-CAccordion value="cedar" variant="plain" size="sm">
              <c-CAccordionItem value="cedar">
                <c-fill name="title">Western red cedar</c-fill>
                <c-fill name="default">A long-lived tree of moist lowland forests.</c-fill>
              </c-CAccordionItem>
              <c-CAccordionItem value="maple">
                <c-fill name="title">Bigleaf maple</c-fill>
                <c-fill name="default">Broad leaves support hanging gardens of moss.</c-fill>
              </c-CAccordionItem>
            </c-CAccordion>
          </c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="wildflowers">
          <c-fill name="title">Wildflowers</c-fill>
          <c-fill name="default">Trillium and violets bloom before the canopy closes.</c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """

    css = """
      :where([data-citry-ui-part="accordion-body"] > p:first-child) {
        margin-block-start: 0;
      }
    """


preview = NestedAccordion()

preview  # noqa: B018
````


## Choose variant and size

`outline`, `soft`, `separated`, and `plain` cover connected and independent
surfaces. `sm`, `md`, and `lg` change trigger, action, indicator, and panel
geometry.


### Compare variants and sizes

[Open the rendered preview](/v/0.4.6/ui-library/components/accordion/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AccordionVariants(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="accordion-variants" aria-label="Accordion variants">
        <c-for each="variant in variants">
          <article>
            <h2>{{ variant }}</h2>
            <c-CAccordion c-variant="variant" value="rain">
              <c-CAccordionItem value="rain">
                <c-fill name="title">Rainfall</c-fill>
                <c-fill name="default">Frequent mist keeps the forest green.</c-fill>
              </c-CAccordionItem>
              <c-CAccordionItem value="light">
                <c-fill name="title">Filtered light</c-fill>
                <c-fill name="default">Sunflecks move across the understory.</c-fill>
              </c-CAccordionItem>
            </c-CAccordion>
          </article>
        </c-for>
        <article class="accordion-variants__sizes">
          <h2>Sizes</h2>
          <div class="accordion-variants__size-grid">
            <c-for each="size in sizes">
              <div>
                <h3>{{ size }}</h3>
                <c-CAccordion c-size="size" value="moss" variant="soft">
                  <c-CAccordionItem value="moss">
                    <c-fill name="title">Moss cover</c-fill>
                    <c-fill name="default">Soft ground holds overnight rain.</c-fill>
                  </c-CAccordionItem>
                </c-CAccordion>
              </div>
            </c-for>
          </div>
        </article>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "variants": ("outline", "soft", "separated", "plain"),
            "sizes": ("sm", "md", "lg"),
        }

    css = """
      :where(.accordion-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1.25rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.accordion-variants article) {
        min-width: 0;
      }

      :where(.accordion-variants__sizes) {
        grid-column: 1 / -1;
      }

      :where(.accordion-variants__size-grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1rem;
      }

      :where(.accordion-variants h2) {
        margin-block: 0 0.625rem;
        font-size: 0.875rem;
        text-transform: capitalize;
      }

      :where(.accordion-variants h3) {
        margin-block: 0 0.5rem;
        font-size: 0.75rem;
        text-transform: uppercase;
      }
    """


preview = AccordionVariants()

preview  # noqa: B018
````


## Customize Accordion

Override public variables on an ancestor or one root. Stable part selectors
target item anatomy. Browser inputs can change `variant`, `size`, `indicator`,
and `indicatorPosition` without a server render.


### Theme a field guide

[Open the rendered preview](/v/0.4.6/ui-library/components/accordion/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizeAccordion(Component):
    template = """
      <section
        class="accordion-configurator"
        x-data="{
          variant: 'separated',
          size: 'md',
          indicator: true,
          indicator_position: 'end',
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Live configuration</p>
          <h2>Forest field guide</h2>
        </header>
        <c-CAccordion
          value="watershed"
          class_="accordion-configurator__group"
          $c-props="{
            variant,
            size,
            indicator,
            indicatorPosition: indicator_position,
          }"
        >
          <c-CAccordionItem value="watershed">
            <c-fill name="title">Watershed</c-fill>
            <c-fill name="default">Every hillside stream eventually meets the river.</c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="wildlife">
            <c-fill name="title">Wildlife corridor</c-fill>
            <c-fill name="default">Connected forest lets animals move between habitats.</c-fill>
          </c-CAccordionItem>
        </c-CAccordion>
      </section>
    """

    css = """
      :where(.accordion-configurator) {
        display: grid;
        gap: 1rem;
        max-width: 48rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.accordion-configurator h2, .accordion-configurator p) {
        margin: 0;
      }

      :where(.accordion-configurator header > p) {
        color: light-dark(#39724e, #8fd4a6);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.accordion-configurator__group) {
        --cui-accordion-radius: 1rem;
        --cui-accordion-trigger-open-color: light-dark(#1f6b3c, #8fe0aa);
        --cui-accordion-focus-color: light-dark(#2f855a, #70d397);
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "separated",
        "options": (
            ("outline", "Outline"),
            ("soft", "Soft"),
            ("separated", "Separated"),
            ("plain", "Plain"),
        ),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "indicator_position",
        "label": "Indicator position",
        "type": "select",
        "default": "end",
        "options": (("start", "Start"), ("end", "End")),
    },
    {
        "name": "indicator",
        "label": "Show indicator",
        "type": "checkbox",
        "default": True,
    },
)

preview = CustomizeAccordion()

preview  # noqa: B018
````


`class_`, `style`, and `attrs` target the Accordion root. An item has its own
`class_`, `style`, and `attrs`, plus exact maps for its native heading,
trigger, panel, and optional actions wrapper. Unlayered consumer CSS overrides
Citry UI defaults; named layers follow the site-wide layer-order contract.

## Keyboard and accessibility

Every enabled trigger remains in normal Tab order. Enter and Space use native
button activation. Arrow Up, Arrow Down, Home, and End move focus among enabled
triggers without opening them; `loop` controls wrapping.

Choose `heading_level` to fit the page outline. Panels are neutral by default.
Set `region=True` only when the panels benefit from landmarks; this adds
`role="region"` and trigger-based naming as one pair.

Closing a panel that contains focus moves focus to its trigger before the panel
becomes inert. A structural update that removes the focused item moves focus to
the nearest enabled surviving trigger. If none survives, the update owner must
choose an external destination.

## Forms, animation, and content lifetime

Closed panel content remains mounted. Uncontrolled edits, successful controls,
and nested component state survive close and reopen. Closed controls still
belong to `FormData` and native constraint validation. A hidden required
control can therefore block submission; applications must open the relevant
panel before moving focus to it.

Rapid expansion requests replace the active animation instead of being
ignored. Reduced-motion users receive an immediate commit. Settled panels do
not clip overlays; a panel clips its contents only during the bounded height
transition. Print shows every panel.

## Trust boundaries

Item values and generated IDs are plain text. Raw values appear only in the
public `data-value`; generated trigger/panel IDs use a stable hash. Title and
panel content use ordinary Citry escaping. The chevron comes from the packaged
icon allowlist.

Attribute maps are trusted authoring surfaces for unowned values. Accordion
rejects attributes and Alpine directives that could replace native semantics,
children, expansion visibility, focus ownership, a second popover/command
activation owner, public mirrors, or Citry runtime markers.

## API reference

### Inputs

#### CAccordion server inputs

Server inputs are passed in a template through `<c-CAccordion ... />` or in Python through
`CAccordion(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="accordion-input-caccordion-server-inputs-value"></span>`value` | `str | Sequence[str] | None` | `None` | Sets initial expansion. Single mode accepts one value; multiple mode accepts a duplicate-free sequence. |
| <span id="accordion-input-caccordion-server-inputs-multiple"></span>`multiple` | `bool` | `False` | Uses an ordered array value and allows several panels to remain open. |
| <span id="accordion-input-caccordion-server-inputs-collapsible"></span>`collapsible` | `bool` | `True` | Allows the open item to close in single mode. Multiple mode always remains collapsible. |
| <span id="accordion-input-caccordion-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables every trigger without closing panels. An enclosing disabled Form or fieldset remains dominant. |
| <span id="accordion-input-caccordion-server-inputs-loop"></span>`loop` | `bool` | `True` | Wraps optional Arrow Up and Arrow Down focus navigation. |
| <span id="accordion-input-caccordion-server-inputs-variant"></span>`variant` | `"outline" | "soft" | "separated" | "plain"` ([`CAccordionVariant`](#accordion-interface-accordion-variant)) | `"outline"` | Selects connected border, quiet surface, separated card, or divider treatment. |
| <span id="accordion-input-caccordion-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CAccordionSize`](#accordion-interface-accordion-size)) | `"md"` | Selects title, indicator, action, and panel geometry. |
| <span id="accordion-input-caccordion-server-inputs-indicator"></span>`indicator` | `bool` | `True` | Shows the owned decorative chevron. |
| <span id="accordion-input-caccordion-server-inputs-indicator-pos"></span>`indicator_pos` | `"start" | "end"` ([`CAccordionIndicatorPos`](#accordion-interface-accordion-indicator-pos)) | `"end"` | Places the chevron at the logical start or end of every trigger. |
| <span id="accordion-input-caccordion-server-inputs-heading-level"></span>`heading_level` | `Literal[2, 3, 4, 5, 6]` ([`CAccordionHeadingLevel`](#accordion-interface-accordion-heading-level)) | `3` | Chooses the native heading level for every direct item. |
| <span id="accordion-input-caccordion-server-inputs-region"></span>`region` | `bool` | `False` | Adds `role="region"` and trigger-based naming to every panel. Use selectively to avoid landmark proliferation. |
| <span id="accordion-input-caccordion-server-inputs-id"></span>`id` | `str | None` | `None` | Sets the root ID and stable trigger/panel ID prefix. |
| <span id="accordion-input-caccordion-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#accordion-interface-accordion-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="accordion-input-caccordion-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#accordion-interface-accordion-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="accordion-input-caccordion-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned root attributes. Accordion semantics, focus, alternate visibility or overlay ownership, public mirrors, structure, and runtime namespaces are reserved. |

</div>

#### CAccordion client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CAccordion />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 14rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="accordion-input-caccordion-client-inputs-value"></span>`value` | `string | null; string[] | null in multiple mode` | Releases client control and preserves the current valid browser state. | Controls expansion with the mode-dependent public shape. |
| <span id="accordion-input-caccordion-client-inputs-on-value-change"></span>`onValueChange` | `function` | No callback. | Receives accepted activation and structural-removal requests. |
| <span id="accordion-input-caccordion-client-inputs-collapsible"></span>`collapsible` | `boolean` | Uses the server input. | Controls whether the open single item may close. |
| <span id="accordion-input-caccordion-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls group disabledness below native Form or fieldset ownership. |
| <span id="accordion-input-caccordion-client-inputs-loop"></span>`loop` | `boolean` | Uses the server input. | Controls Arrow-key wrapping. |
| <span id="accordion-input-caccordion-client-inputs-variant"></span>`variant` | `"outline" | "soft" | "separated" | "plain"` ([`CAccordionVariant`](#accordion-interface-accordion-variant)) | Uses the server input. | Controls visual treatment. |
| <span id="accordion-input-caccordion-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CAccordionSize`](#accordion-interface-accordion-size)) | Uses the server input. | Controls geometry. |
| <span id="accordion-input-caccordion-client-inputs-indicator"></span>`indicator` | `boolean` | Uses the server input. | Controls chevron visibility. |
| <span id="accordion-input-caccordion-client-inputs-indicator-position"></span>`indicatorPosition` | `"start" | "end"` ([`CAccordionIndicatorPos`](#accordion-interface-accordion-indicator-pos)) | Uses the server input. | Controls logical chevron placement. |

</div>

#### CAccordionItem server inputs

Server inputs are passed in a template through `<c-CAccordionItem ... />` or in Python
through `CAccordionItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="accordion-input-caccordion-item-server-inputs-value"></span>`value` | `non-empty str` | required | Supplies stable item identity. Values must be unique within the nearest Accordion. |
| <span id="accordion-input-caccordion-item-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables this trigger without closing its panel. |
| <span id="accordion-input-caccordion-item-server-inputs-actions-label"></span>`actions_label` | `non-whitespace str | None` | `None` | Names the optional action group and emits its owned `group` role; requires actions. |
| <span id="accordion-input-caccordion-item-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#accordion-interface-accordion-class-value)) | `None` | Adds item-root classes and merges them with `attrs`. |
| <span id="accordion-input-caccordion-item-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#accordion-interface-accordion-style-value)) | `None` | Adds item-root inline styles and merges them with `attrs`. |
| <span id="accordion-input-caccordion-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned item-root attributes. |
| <span id="accordion-input-caccordion-item-server-inputs-heading-attrs"></span>`heading_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned native-heading attributes. |
| <span id="accordion-input-caccordion-item-server-inputs-trigger-attrs"></span>`trigger_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned native-button attributes and event listeners. Button semantics, activation ownership, and state are reserved. |
| <span id="accordion-input-caccordion-item-server-inputs-panel-attrs"></span>`panel_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned panel attributes. Visibility, region semantics, ID, and state are reserved. |
| <span id="accordion-input-caccordion-item-server-inputs-actions-attrs"></span>`actions_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned action-wrapper attributes. Requires actions; group naming and focus/live-region ownership are reserved. |

</div>

#### CAccordionItem client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CAccordionItem />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 14rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="accordion-input-caccordion-item-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls this item's disabledness below group and native fieldset ownership. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CAccordion slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="accordion-slot-caccordion-slots-default"></span>`default` | yes | `{}` ([`CAccordionDefaultSlotData`](#accordion-interface-accordion-slot-data)) | None. Requires one or more direct CAccordionItem components. |

</div>

#### CAccordionItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="accordion-slot-caccordion-item-slots-title"></span>`title` | yes | `{}` ([`CAccordionItemTitleSlotData`](#accordion-interface-accordion-item-title-slot-data)) | None. Renders inside the native trigger and accepts noninteractive phrasing content. |
| <span id="accordion-slot-caccordion-item-slots-default"></span>`default` | yes | `{}` ([`CAccordionItemDefaultSlotData`](#accordion-interface-accordion-item-default-slot-data)) | None. Renders as always-mounted panel flow content. |
| <span id="accordion-slot-caccordion-item-slots-actions"></span>`actions` | no | `{}` ([`CAccordionItemActionsSlotData`](#accordion-interface-accordion-item-actions-slot-data)) | No adjacent action wrapper. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CAccordion events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="accordion-event-caccordion-events-on-value-change"></span>`onValueChange` | `(value: string | null | string[], detail: CAccordionValueChangeDetail) => void` | Accepted trigger activation or one batched structural-removal fallback. Initial state and owner prop updates are excluded. | `{value, previousValue, itemValue: string | null, removedValues: string[], expanded: boolean, source: "activation" | "removal"}` | Runs before an uncontrolled commit. Controlled Accordion waits for `value`; return values do not cancel the request. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CAccordion CSS variables

Apply these variables to `CAccordion` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="accordion-css-caccordion-css-variables-background"></span>`--cui-accordion-background` | `color` | Connected root and item surface. | `` `Canvas` `` |
| <span id="accordion-css-caccordion-css-variables-foreground"></span>`--cui-accordion-foreground` | `color` | Title and panel foreground. | `` `CanvasText` `` |
| <span id="accordion-css-caccordion-css-variables-border-color"></span>`--cui-accordion-border-color` | `color` | Root item and divider boundary. | `22% current-color mix.` |
| <span id="accordion-css-caccordion-css-variables-border-width"></span>`--cui-accordion-border-width` | `length` | Stable border geometry. | `1px` |
| <span id="accordion-css-caccordion-css-variables-radius"></span>`--cui-accordion-radius` | `length` | Group and separated-item corners. | `0.75rem` |
| <span id="accordion-css-caccordion-css-variables-gap"></span>`--cui-accordion-gap` | `length` | Separated-item gap. | `0.75rem` |
| <span id="accordion-css-caccordion-css-variables-shadow"></span>`--cui-accordion-shadow` | `shadow` | Separated-item elevation. | `Scheme-derived shadow.` |
| <span id="accordion-css-caccordion-css-variables-trigger-background"></span>`--cui-accordion-trigger-background` | `color` | Resting trigger background. | `transparent` |
| <span id="accordion-css-caccordion-css-variables-trigger-hover-background"></span>`--cui-accordion-trigger-hover-background` | `color` | Enabled hover background. | `8% current-color mix.` |
| <span id="accordion-css-caccordion-css-variables-trigger-open-background"></span>`--cui-accordion-trigger-open-background` | `color` | Expanded trigger background. | `9% LinkText mix.` |
| <span id="accordion-css-caccordion-css-variables-trigger-open-color"></span>`--cui-accordion-trigger-open-color` | `color` | Expanded title and chevron foreground. | `` `LinkText` `` |
| <span id="accordion-css-caccordion-css-variables-focus-color"></span>`--cui-accordion-focus-color` | `color` | Trigger focus ring. | `` `Highlight` `` |
| <span id="accordion-css-caccordion-css-variables-indicator-color"></span>`--cui-accordion-indicator-color` | `color` | Chevron foreground. | `currentColor` |
| <span id="accordion-css-caccordion-css-variables-trigger-padding-inline"></span>`--cui-accordion-trigger-padding-inline` | `length` | Trigger inline inset. | `Size-derived.` |
| <span id="accordion-css-caccordion-css-variables-trigger-padding-block"></span>`--cui-accordion-trigger-padding-block` | `length` | Trigger block inset. | `Size-derived.` |
| <span id="accordion-css-caccordion-css-variables-panel-padding-inline"></span>`--cui-accordion-panel-padding-inline` | `length` | Panel-body inline inset. | `Size-derived.` |
| <span id="accordion-css-caccordion-css-variables-panel-padding-block"></span>`--cui-accordion-panel-padding-block` | `length` | Panel-body block inset. | `Size-derived.` |
| <span id="accordion-css-caccordion-css-variables-actions-gap"></span>`--cui-accordion-actions-gap` | `length` | Adjacent action spacing. | `0.5rem` |
| <span id="accordion-css-caccordion-css-variables-duration"></span>`--cui-accordion-duration` | `time` | Panel and chevron transition duration. | `180ms` |
| <span id="accordion-css-caccordion-css-variables-easing"></span>`--cui-accordion-easing` | `easing` | Panel and chevron transition curve. | `ease-out` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CAccordion attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="accordion-attribute-caccordion-attributes-data-variant"></span>`data-variant` | Root | `"outline" | "soft" | "separated" | "plain"` | Mirrors effective visual treatment. |
| <span id="accordion-attribute-caccordion-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Mirrors effective geometry. |
| <span id="accordion-attribute-caccordion-attributes-data-multiple"></span>`data-multiple` | Root | `present | absent` | Present in structural multiple mode. |
| <span id="accordion-attribute-caccordion-attributes-data-collapsible"></span>`data-collapsible` | Root | `present | absent` | Present while open items may close; always present in multiple mode. |
| <span id="accordion-attribute-caccordion-attributes-data-disabled-root"></span>`data-disabled` | Root | `present | absent` | Mirrors browser-effective group disabledness. |
| <span id="accordion-attribute-caccordion-attributes-data-loop"></span>`data-loop` | Root | `present | absent` | Present while Arrow navigation wraps. |
| <span id="accordion-attribute-caccordion-attributes-data-indicator"></span>`data-indicator` | Root | `present | absent` | Present while chevrons are visible. |
| <span id="accordion-attribute-caccordion-attributes-data-indicator-pos"></span>`data-indicator-pos` | Root | `"start" | "end"` | Mirrors logical chevron placement. |
| <span id="accordion-attribute-caccordion-attributes-id-root"></span>`id` | Root | `str` | Uses the supplied root ID or a generated instance ID. |

</div>

#### CAccordionItem attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="accordion-attribute-caccordion-item-attributes-data-state"></span>`data-state` | Item, trigger, and panel | `"open" | "closed"` | Mirrors committed expansion. |
| <span id="accordion-attribute-caccordion-item-attributes-data-disabled-item"></span>`data-disabled` | Item and trigger | `present | absent` | Mirrors browser-effective item disabledness. |
| <span id="accordion-attribute-caccordion-item-attributes-data-value"></span>`data-value` | Item | `str` | Exposes canonical item identity for styling and inspection. |
| <span id="accordion-attribute-caccordion-item-attributes-aria-expanded"></span>`aria-expanded` | Trigger | `"true" | "false"` | Exposes native expansion state. |
| <span id="accordion-attribute-caccordion-item-attributes-aria-disabled"></span>`aria-disabled` | Trigger | `absent | "true"` | Marks an otherwise enabled open trigger that cannot collapse. |
| <span id="accordion-attribute-caccordion-item-attributes-disabled"></span>`disabled` | Trigger | `present | absent` | Present for component-owned group or item disabledness. A native fieldset can also disable the trigger without adding this attribute. |
| <span id="accordion-attribute-caccordion-item-attributes-generated-ids"></span>`id` | Trigger and panel | `generated str` | Derives a stable relationship pair from the root ID and canonical item value. |
| <span id="accordion-attribute-caccordion-item-attributes-aria-controls"></span>`aria-controls` | Trigger | `panel IDREF` | Identifies the panel controlled by this trigger. |
| <span id="accordion-attribute-caccordion-item-attributes-aria-labelledby"></span>`aria-labelledby` | Panel | `absent | trigger IDREF` | Names a region panel from its trigger only when region mode is enabled. |
| <span id="accordion-attribute-caccordion-item-attributes-aria-hidden"></span>`aria-hidden` | Panel | `absent | "true"` | Present while the panel is collapsed. |
| <span id="accordion-attribute-caccordion-item-attributes-inert"></span>`inert` | Panel | `present | absent` | Removes collapsed panel descendants from focus and interaction. |
| <span id="accordion-attribute-caccordion-item-attributes-hidden-panel"></span>`hidden` | Panel | `present | absent` | Removes a settled collapsed panel from rendering. |
| <span id="accordion-attribute-caccordion-item-attributes-hidden-indicator"></span>`hidden` | Indicator wrapper | `present | absent` | Removes the chevron when indicator is disabled. |
| <span id="accordion-attribute-caccordion-item-attributes-role"></span>`role` | Panel | `absent | "region"` | Present with aria-labelledby only when region mode is enabled. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CAccordion selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="accordion-selector-caccordion-selectors-accordion"></span>`[data-citry-ui-part="accordion"]` | Root div | Group surface and class/style/attrs destination. |
| <span id="accordion-selector-caccordion-selectors-accordion-item"></span>`[data-citry-ui-part="accordion-item"]` | Item root div | Keyed item surface and item attrs destination. |
| <span id="accordion-selector-caccordion-selectors-accordion-header"></span>`[data-citry-ui-part="accordion-header"]` | Header row div | Heading and adjacent-action layout. |
| <span id="accordion-selector-caccordion-selectors-accordion-heading"></span>`[data-citry-ui-part="accordion-heading"]` | Native h2-h6 | Document-outline heading and heading_attrs destination. |
| <span id="accordion-selector-caccordion-selectors-accordion-trigger"></span>`[data-citry-ui-part="accordion-trigger"]` | Native button | Expansion control and trigger_attrs destination. |
| <span id="accordion-selector-caccordion-selectors-accordion-title"></span>`[data-citry-ui-part="accordion-title"]` | Trigger title span | Visible title and accessible-name content. |
| <span id="accordion-selector-caccordion-selectors-accordion-indicator"></span>`[data-citry-ui-part="accordion-indicator"]` | Decorative span | Owned chevron wrapper. |
| <span id="accordion-selector-caccordion-selectors-accordion-actions"></span>`[data-citry-ui-part="accordion-actions"]` | Optional adjacent-action div | Action layout naming and actions_attrs destination. |
| <span id="accordion-selector-caccordion-selectors-accordion-panel"></span>`[data-citry-ui-part="accordion-panel"]` | Controlled panel div | Visibility region semantics and panel_attrs destination. |
| <span id="accordion-selector-caccordion-selectors-accordion-body"></span>`[data-citry-ui-part="accordion-body"]` | Panel-body div | Content inset and overflow-neutral surface. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="accordion-interface-accordion-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="accordion-interface-accordion-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="accordion-interface-accordion-variant"></span>`CAccordionVariant` | `Literal["outline", "soft", "separated", "plain"]` |
| <span id="accordion-interface-accordion-size"></span>`CAccordionSize` | `Literal["sm", "md", "lg"]` |
| <span id="accordion-interface-accordion-indicator-pos"></span>`CAccordionIndicatorPos` | `Literal["start", "end"]` |
| <span id="accordion-interface-accordion-heading-level"></span>`CAccordionHeadingLevel` | `Literal[2, 3, 4, 5, 6]` |
| <span id="accordion-interface-accordion-value-change-detail"></span>`CAccordionValueChangeDetail` | `{value: string | null | string[], previousValue: string | null | string[], itemValue: string | null, removedValues: string[], expanded: boolean, source: "activation" | "removal"}` |

</div>

<span id="accordion-interface-accordion-slot-data"></span>

#### `CAccordionDefaultSlotData`

Empty dataclass: `{}`.

<span id="accordion-interface-accordion-item-title-slot-data"></span>

#### `CAccordionItemTitleSlotData`

Empty dataclass: `{}`.

<span id="accordion-interface-accordion-item-default-slot-data"></span>

#### `CAccordionItemDefaultSlotData`

Empty dataclass: `{}`.

<span id="accordion-interface-accordion-item-actions-slot-data"></span>

#### `CAccordionItemActionsSlotData`

Empty dataclass: `{}`.

### Translation keys

-