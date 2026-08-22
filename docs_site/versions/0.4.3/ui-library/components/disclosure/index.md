---
title: Disclosure
url: https://citry.dev/v/0.4.3/ui-library/components/disclosure/
description: "Reveal one independent block of supporting content."
---
# Disclosure

Use `CDisclosure` for one independently expandable note, setting group, or
supporting section. Use `CAccordion` when several items share selection,
expansion policy, or collection keyboard behavior.

## Disclosure at a glance


### Disclosure at a glance

[Open the rendered preview](/v/0.4.3/ui-library/components/disclosure/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisclosureAtAGlance(Component):
    template = """
      <c-CDisclosure>
        <c-fill name="title">System requirements</c-fill>
        <c-fill name="default">
          <p>Python 3.13 or newer and 512 MB of available storage.</p>
        </c-fill>
      </c-CDisclosure>
    """


preview = DisclosureAtAGlance()
preview  # noqa: B018
````


## Write the shortest Disclosure


### Basic Disclosure

[Open the rendered preview](/v/0.4.3/ui-library/components/disclosure/_previews/basic-disclosure/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicDisclosure(Component):
    template = """
      <c-CCol gap="md">
        <c-CDisclosure open heading_level="2" region>
          <c-fill name="title">Install prerequisites</c-fill>
          <c-fill name="default">
            Install Python, create a virtual environment, then add Citry.
          </c-fill>
        </c-CDisclosure>
        <c-CDisclosure>
          <c-fill name="title">Optional database tools</c-fill>
          <c-fill name="default">
            Add the PostgreSQL client only when the application uses it.
          </c-fill>
        </c-CDisclosure>
      </c-CCol>
    """


preview = BasicDisclosure()
preview  # noqa: B018
````


The title becomes the native Button name. Choose `heading_level` to fit the
document outline. Add `region` only when the expanded panel deserves a
landmark.

Python composition uses the same two required slots:


```python
from citry_ui import CDisclosure

requirements = CDisclosure(
    slots={
        "title": "System requirements",
        "default": "Python 3.13 or newer",
    },
)
```


## Control expansion


### Control Disclosure

[Open the rendered preview](/v/0.4.3/ui-library/components/disclosure/_previews/controlled-open/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDisclosure(Component):
    template = """
      <section
        class="controlled-disclosure"
        x-data="{open:false, controlled:true, accept:true, last:'none'}"
      >
        <c-CDisclosure
          $c-props="{
            open: controlled ? open : null,
            onOpenChange: (next, detail) => {
              last = `${detail.source}: ${next ? 'open' : 'closed'}`;
              if (controlled && accept) open = next;
            },
          }"
        >
          <c-fill name="title">Advanced logging</c-fill>
          <c-fill name="default">
            Include request identifiers and timing details in diagnostic output.
          </c-fill>
        </c-CDisclosure>
        <label>
          <input type="checkbox" x-model="accept" />
          Accept trigger requests
        </label>
        <div class="controlled-disclosure__controls" role="group" aria-label="Disclosure owner controls">
          <button type="button" @click="controlled=true; open=true">Show</button>
          <button type="button" @click="controlled=true; open=false">Hide</button>
          <button type="button" @click="controlled=false">Release control</button>
        </div>
        <output>
          Ownership: <span x-text="controlled ? 'browser-controlled' : 'released'">browser-controlled</span>
          · Requests: <span x-text="accept ? 'accepted' : 'refused'">accepted</span>
          · Last: <span x-text="last">none</span>
        </output>
      </section>
    """

    css = """
      :where(.controlled-disclosure) { display: grid; gap: 0.75rem; }
      :where(.controlled-disclosure__controls) { display: flex; flex-wrap: wrap; }
      :where(.controlled-disclosure__controls > button) {
        min-block-size: 2rem;
        padding-inline: 0.75rem;
        border: 1px solid color-mix(in srgb, currentColor 24%, transparent);
        background: Canvas;
        color: CanvasText;
        font: inherit;
      }
    """


preview = ControlledDisclosure()
preview  # noqa: B018
````


A Boolean client `open` owns expansion. Omit it or supply `null` to release
control and commit the retained uncontrolled/server baseline, which may differ
from the visible controlled state.

`onOpenChange` is a component callback, not a DOM event. Native listeners such
as `@click` and `@focus` still receive their ordinary browser events;
Disclosure dispatches no custom toggle, show, or hide event.

## Add actions and disabled state


### Disclosure actions and disabled state

[Open the rendered preview](/v/0.4.3/ui-library/components/disclosure/_previews/actions-and-disabled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisclosureActionsAndDisabled(Component):
    template = """
      <section
        class="disclosure-actions-demo"
        x-data="{disabled:false, fieldsetDisabled:false}"
      >
        <c-CDisclosure
          actions_label="Release note actions"
          c-actions_attrs="{'data-demo-actions':'release'}"
        >
          <c-fill name="title">Release notes</c-fill>
          <c-fill name="actions">
            <c-CButton size="sm" variant="ghost">Copy link</c-CButton>
          </c-fill>
          <c-fill name="default">Review migration notes before deploying version 4.</c-fill>
        </c-CDisclosure>
        <c-CDisclosure open $c-props="{disabled}">
          <c-fill name="title">Managed policy</c-fill>
          <c-fill name="default">Your organization keeps this guidance visible.</c-fill>
        </c-CDisclosure>
        <label><input type="checkbox" x-model="disabled" /> Disable managed policy</label>
        <c-CDisclosure disabled>
          <c-fill name="title">Unavailable audit appendix</c-fill>
          <c-fill name="default">This closed section cannot be activated.</c-fill>
        </c-CDisclosure>
        <fieldset :disabled="fieldsetDisabled">
          <legend>
            <label><input type="checkbox" x-model="fieldsetDisabled" /> Disable native fieldset</label>
          </legend>
          <c-CDisclosure>
            <c-fill name="title">Fieldset-owned policy</c-fill>
            <c-fill name="default">Native fieldset ownership disables this trigger.</c-fill>
          </c-CDisclosure>
        </fieldset>
      </section>
    """

    css = """
      :where(.disclosure-actions-demo) { display: grid; gap: 1rem; }
      :where(.disclosure-actions-demo fieldset) {
        min-inline-size: 0;
        padding: 0.75rem;
        border: 1px solid color-mix(in srgb, currentColor 24%, transparent);
        border-radius: 0.75rem;
      }
    """


preview = DisclosureActionsAndDisabled()
preview  # noqa: B018
````


Actions stay beside the heading rather than inside its Button. Disabledness
blocks activation without erasing an already-open panel.

## Choose treatment and geometry


### Disclosure variants and sizes

[Open the rendered preview](/v/0.4.3/ui-library/components/disclosure/_previews/variants-and-sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisclosureVariantsAndSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section
        class="disclosure-variants"
        x-data="{variant:'outline',size:'md',indicator:true,indicator_position:'end'}"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <div class="disclosure-variants__stage" style="color-scheme:dark">
          <c-CDisclosure
            open
            class_="disclosure-variants__subject"
            $c-props="{variant,size,indicator,indicatorPosition:indicator_position}"
          >
            <c-fill name="title">Deployment requirements for the observability gateway in restricted networks</c-fill>
            <c-fill name="default">The live subject reflects every external control.</c-fill>
          </c-CDisclosure>
        </div>
        <div class="disclosure-variants__matrix">
          <c-for each="variant in variants">
            <c-CDisclosure c-variant="variant" open>
              <c-fill name="title">{{ variant }} treatment</c-fill>
              <c-fill name="default">A concise operations handbook note.</c-fill>
            </c-CDisclosure>
          </c-for>
          <c-for each="size in sizes">
            <c-CDisclosure c-size="size" indicator_pos="start">
              <c-fill name="title">{{ size }} geometry</c-fill>
              <c-fill name="default">Size changes the complete component geometry.</c-fill>
            </c-CDisclosure>
          </c-for>
        </div>
      </section>
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {"variants": ("outline", "soft", "plain"), "sizes": ("sm", "md", "lg")}

    css = """
      :where(.disclosure-variants) {
        display: grid;
        gap: 1rem;
      }
      :where(.disclosure-variants__stage) {
        padding: 1rem;
        border-radius: 1rem;
        background: #111827;
      }
      :where(.disclosure-variants__matrix) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        gap: 0.75rem;
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "outline",
        "options": (("outline", "Outline"), ("soft", "Soft"), ("plain", "Plain")),
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
    {"name": "indicator", "label": "Show indicator", "type": "checkbox", "default": True},
)


preview = DisclosureVariantsAndSizes()
preview  # noqa: B018
````


## Nest independent and grouped content


### Nested Disclosure and Accordion

[Open the rendered preview](/v/0.4.3/ui-library/components/disclosure/_previews/nested-disclosures/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedDisclosures(Component):
    template = """
      <section class="nested-disclosure-demo" dir="rtl">
        <c-CDisclosure open>
          <c-fill name="title">Network setup</c-fill>
          <c-fill name="default">
            <c-CCol gap="md">
              <p>Configure the application endpoint before optional proxy rules.</p>
              <c-CDisclosure variant="soft" size="sm">
                <c-fill name="title">Proxy settings</c-fill>
                <c-fill name="default">Use HTTPS_PROXY for outbound requests.</c-fill>
              </c-CDisclosure>
              <c-CAccordion value="timeouts" variant="plain" size="sm">
                <c-CAccordionItem value="timeouts">
                  <c-fill name="title">Timeout troubleshooting</c-fill>
                  <c-fill name="default">Check firewall and DNS resolution first.</c-fill>
                </c-CAccordionItem>
              </c-CAccordion>
            </c-CCol>
          </c-fill>
        </c-CDisclosure>
      </section>
    """

    css = """
      :where(.nested-disclosure-demo) { inline-size: min(100%, 20rem); }
      :where(.nested-disclosure-demo p) { overflow-wrap: anywhere; }
    """


preview = NestedDisclosures()
preview  # noqa: B018
````


Nested Disclosure and Accordion roots belong in the panel, never in the title
or adjacent actions.

## Compose overlays and Dialogs safely


### Disclosure overlays and sibling Dialog

[Open the rendered preview](/v/0.4.3/ui-library/components/disclosure/_previews/overlays-and-dialogs/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisclosureOverlaysAndDialogs(Component):
    template = """
      <section
        class="disclosure-overlay-demo"
        x-data="{dialogOpen:false}"
        @click="if ($event.target.closest('[data-open-credential-dialog]')) dialogOpen=true"
      >
        <c-CDisclosure open>
          <c-fill name="title">Credential help</c-fill>
          <c-fill name="default">
            <c-CCol gap="sm" align="start">
              <p>Review token scope before rotating a credential.</p>
              <c-CPopover>
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton size="sm" variant="outline" c-attrs="activator_attrs">Scope help</c-CButton>
                </c-fill>
                <c-fill name="title">Credential scope</c-fill>
                <c-fill name="default">Grant only the permissions this worker needs.</c-fill>
              </c-CPopover>
              <button
                type="button"
                class="disclosure-overlay-demo__dialog-trigger"
                data-open-credential-dialog
              >Rotate credential</button>
            </c-CCol>
          </c-fill>
        </c-CDisclosure>

        <c-CDialog
          size="sm"
          $c-props="{
            open: dialogOpen,
            onOpenChange: (next) => dialogOpen = next,
          }"
        >
          <c-fill name="title">Rotate credential</c-fill>
          <c-fill name="default">The old credential stops working immediately.</c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.disclosure-overlay-demo) { display: grid; gap: 1rem; justify-items: start; }
      :where(.disclosure-overlay-demo > [data-citry-ui-part="disclosure"]) { inline-size: min(100%, 40rem); }
      :where(.disclosure-overlay-demo__dialog-trigger) {
        min-block-size: 2.25rem;
        padding-inline: 0.875rem;
        border: 1px solid color-mix(in srgb, currentColor 24%, transparent);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
      }
    """


preview = DisclosureOverlaysAndDialogs()
preview  # noqa: B018
````


Citry anchored layers may live in an open panel and close structurally with
it. Render `CDialog` and `CDrawer` as siblings outside Disclosure, then open
them from a panel or action control. Native `dialog` elements, `CDialog`, and
`CDrawer` are rejected as panel or actions descendants regardless of their
current open state. Raw native popovers, unresolved web components, customized
built-ins, and authored shadow hosts are also outside that slot contract.

## Keep title content structural

The title accepts text and only these native elements: `abbr`, `b`, `bdi`,
`bdo`, `br`, `cite`, `code`, `data`, `del`, `dfn`, `em`, `i`, `img`, `ins`,
`kbd`, `mark`, `picture`, `q`, `rp`, `rt`, `ruby`, `s`, `samp`, `small`,
`source`, `span`, `strong`, `sub`, `sup`, `svg`, `time`, `u`, `var`, and
`wbr`. Images must have empty `alt`. Decorative SVG must use
`aria-hidden="true"` and `focusable="false"`, and may contain only `g`, `path`,
`polyline`, `line`, `circle`, `rect`, `ellipse`, and `polygon`. The title must
still contain non-whitespace text outside decorative content. Links, controls,
custom elements, and other HTML do not belong inside the trigger. Every title
descendant rejects `role`, `tabindex`, `contenteditable`, `autofocus`, `href`,
`xlink:href`, `controls`, `usemap`, `form`, `popover`, `is`, `hidden`, `inert`,
ARIA naming or description attributes, inline or Alpine event listeners, and
Alpine structural or ownership directives.

The default panel accepts normal flow content and nested Disclosure or
Accordion roots within the overlay boundary above. Actions follow the same
boundary but do not accept nested Disclosure or Accordion roots.

## Preserve forms and focus


### Disclosure forms and focus

[Open the rendered preview](/v/0.4.3/ui-library/components/disclosure/_previews/forms-and-focus/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisclosureFormsAndFocus(Component):
    template = """
      <form
        class="disclosure-form"
        x-data="{notificationOpen:true, escalationOpen:false, invalidTarget:null}"
        @invalid.capture="
          if ($event.target.name === 'notification-email') {
            $event.preventDefault();
            notificationOpen = true;
          } else if ($event.target.name === 'escalation-contact') {
            $event.preventDefault();
            escalationOpen = true;
          } else {
            return;
          }
          if (invalidTarget === null) {
            invalidTarget = $event.target;
            $nextTick(() => {
              invalidTarget?.focus();
              invalidTarget = null;
            });
          }
        "
      >
        <c-CDisclosure
          open
          $c-props="{
            open: notificationOpen,
            onOpenChange: (next) => notificationOpen = next,
          }"
        >
          <c-fill name="title">Notification settings</c-fill>
          <c-fill name="default">
            <c-CCol gap="sm">
              <c-CField>
                <c-fill name="label">Notification email</c-fill>
                <c-fill name="default">
                  <c-CInput name="notification-email" type="email" value="ops@example.com" />
                </c-fill>
                <c-fill name="description">Edits survive closing and reopening.</c-fill>
              </c-CField>
              <c-CCheckbox name="weekly-summary">Send a weekly summary</c-CCheckbox>
            </c-CCol>
          </c-fill>
        </c-CDisclosure>
        <c-CDisclosure
          $c-props="{
            open: escalationOpen,
            onOpenChange: (next) => escalationOpen = next,
          }"
        >
          <c-fill name="title">Required escalation contact</c-fill>
          <c-fill name="default">
            <label>Contact <input name="escalation-contact" required /></label>
          </c-fill>
        </c-CDisclosure>
        <c-CButton type="submit">Save settings</c-CButton>
        <c-CButton type="reset" variant="outline">Reset form</c-CButton>
      </form>
    """

    css = """
      :where(.disclosure-form) { display: grid; gap: 1rem; max-inline-size: 42rem; }
    """


preview = DisclosureFormsAndFocus()
preview  # noqa: B018
````


Panels stay mounted, so closing preserves edits and FormData participation.
It does not exempt a required closed control from constraint validation. Keep
required content open or open it from captured validation handling.

## Customize Disclosure


### Customize Disclosure

[Open the rendered preview](/v/0.4.3/ui-library/components/disclosure/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedDisclosure(Component):
    template = """
      <section class="disclosure-brands">
        <div class="disclosure-brand disclosure-brand--orchard">
          <c-CDisclosure open indicator_pos="start">
            <c-fill name="title">Orchard operations and seasonal irrigation planning</c-fill>
            <c-fill name="default">Warm surfaces for the harvest handbook.</c-fill>
          </c-CDisclosure>
        </div>
        <div class="disclosure-brand disclosure-brand--harbor" dir="rtl" style="color-scheme:dark">
          <c-CDisclosure variant="soft">
            <c-fill name="title">Harbor operations</c-fill>
            <c-fill name="default">A cool scheme with logical indicator placement.</c-fill>
          </c-CDisclosure>
        </div>
      </section>
    """

    css = """
      :where(.disclosure-brands) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
      }
      :where(.disclosure-brand) { padding: 1rem; border-radius: 1rem; }
      :where(.disclosure-brand--orchard) {
        color-scheme: light dark;
        --cui-disclosure-background: light-dark(#fff7ed, #2b170b);
        --cui-disclosure-foreground: light-dark(#431407, #ffedd5);
        --cui-disclosure-trigger-open-color: light-dark(#9a3412, #fdba74);
      }
      :where(.disclosure-brand--harbor) {
        color-scheme: light dark;
        --cui-disclosure-background: light-dark(#ecfeff, #082f49);
        --cui-disclosure-foreground: light-dark(#164e63, #cffafe);
        --cui-disclosure-trigger-open-color: light-dark(#0369a1, #7dd3fc);
        --cui-disclosure-radius: 1.25rem;
      }
      :where(.disclosure-brand [data-citry-ui-part="disclosure-title"]) {
        letter-spacing: 0.01em;
      }
    """


preview = CustomizedDisclosure()
preview  # noqa: B018
````


## Accessibility and interaction

The trigger is a native `button type="button"` with `aria-expanded` and
`aria-controls`. Enter and Space use native activation. Disclosure does not
add Arrow, Home, or End behavior. When accepted closing would hide focused
panel content, focus moves to the trigger or a safe modal/document fallback
before the panel becomes inert.

For a plain no-JavaScript reveal, use native
[`details`](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-details-element)
and `summary`. Citry's authored pattern exists for controlled ownership,
disabled fieldsets, adjacent actions, focus safety, and reversible animation.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CDisclosure server inputs

Server inputs are passed in a template through `<c-CDisclosure ... />` or in Python through
`CDisclosure(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="disclosure-input-cdisclosure-server-inputs-open"></span>`open` | `bool` | `False` | Sets the initial committed expansion and the uncontrolled server fallback. |
| <span id="disclosure-input-cdisclosure-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables the native trigger without changing expansion. CForm and native fieldset disabledness remain dominant. |
| <span id="disclosure-input-cdisclosure-server-inputs-variant"></span>`variant` | `"outline" | "soft" | "plain"` ([`CDisclosureVariant`](#disclosure-interface-variant)) | `"outline"` | Selects bordered, quiet filled, or transparent treatment. |
| <span id="disclosure-input-cdisclosure-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CDisclosureSize`](#disclosure-interface-size)) | `"md"` | Selects title, trigger, panel, and indicator geometry. |
| <span id="disclosure-input-cdisclosure-server-inputs-indicator"></span>`indicator` | `bool` | `True` | Shows the owned decorative chevron. |
| <span id="disclosure-input-cdisclosure-server-inputs-indicator-pos"></span>`indicator_pos` | `"start" | "end"` ([`CDisclosureIndicatorPos`](#disclosure-interface-indicator-pos)) | `"end"` | Places the chevron at the logical start or end of the trigger. |
| <span id="disclosure-input-cdisclosure-server-inputs-heading-level"></span>`heading_level` | `Literal[2, 3, 4, 5, 6]` ([`CDisclosureHeadingLevel`](#disclosure-interface-heading-level)) | `3` | Chooses the native heading tag. |
| <span id="disclosure-input-cdisclosure-server-inputs-region"></span>`region` | `bool` | `False` | Adds one trigger-named region landmark to the panel. Use selectively. |
| <span id="disclosure-input-cdisclosure-server-inputs-actions-label"></span>`actions_label` | `non-whitespace str | None` | `None` | Names the optional actions group and requires the actions slot. |
| <span id="disclosure-input-cdisclosure-server-inputs-id"></span>`id` | `str | None` | generated | Sets the root ID and stable trigger/panel ID pair. |
| <span id="disclosure-input-cdisclosure-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#disclosure-interface-class-value)) | `None` | Adds root classes and merges them with attrs. |
| <span id="disclosure-input-cdisclosure-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#disclosure-interface-style-value)) | `None` | Adds root inline styles and merges them with attrs. |
| <span id="disclosure-input-cdisclosure-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned root attributes. Presence may be owned only for the complete root. |
| <span id="disclosure-input-cdisclosure-server-inputs-heading-attrs"></span>`heading_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned native-heading attributes. |
| <span id="disclosure-input-cdisclosure-server-inputs-trigger-attrs"></span>`trigger_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned Button attributes and native listeners. Identity, semantics, state, alternate activation, and popup ownership are reserved. |
| <span id="disclosure-input-cdisclosure-server-inputs-panel-attrs"></span>`panel_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned panel attributes. Identity, region semantics, and presence are reserved. |
| <span id="disclosure-input-cdisclosure-server-inputs-actions-attrs"></span>`actions_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned action-wrapper attributes and requires actions. Group naming, presence, and overlay ownership are reserved. |

</div>

#### CDisclosure client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CDisclosure />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 14rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="disclosure-input-cdisclosure-client-inputs-open"></span>`open` | `boolean | null` | Releases control and commits the retained uncontrolled or server baseline. null has the same effect. | Controls expansion while supplied as a Boolean. |
| <span id="disclosure-input-cdisclosure-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Omission or null selects no component callback. | Receives accepted native-trigger requests before an uncontrolled commit. |
| <span id="disclosure-input-cdisclosure-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls local disabledness below native Form or fieldset ownership. |
| <span id="disclosure-input-cdisclosure-client-inputs-variant"></span>`variant` | `"outline" | "soft" | "plain"` ([`CDisclosureVariant`](#disclosure-interface-variant)) | Uses the server input. | Controls visual treatment. |
| <span id="disclosure-input-cdisclosure-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CDisclosureSize`](#disclosure-interface-size)) | Uses the server input. | Controls geometry. |
| <span id="disclosure-input-cdisclosure-client-inputs-indicator"></span>`indicator` | `boolean` | Uses the server input. | Controls chevron visibility. |
| <span id="disclosure-input-cdisclosure-client-inputs-indicator-position"></span>`indicatorPosition` | `"start" | "end"` ([`CDisclosureIndicatorPos`](#disclosure-interface-indicator-pos)) | Uses the server input. | Controls logical chevron placement. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CDisclosure slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="disclosure-slot-cdisclosure-slots-title"></span>`title` | yes | `{}` ([`CDisclosureTitleSlotData`](#disclosure-interface-cdisclosure-title-slot-data)) | None. Uses the guide's exact text/image/decorative-SVG allowlist and requires nonempty structural text. |
| <span id="disclosure-slot-cdisclosure-slots-default"></span>`default` | yes | `{}` ([`CDisclosureDefaultSlotData`](#disclosure-interface-cdisclosure-default-slot-data)) | None. Accepts standard flow content and resolved Citry components but rejects native dialog, CDialog, CDrawer, raw popovers, unresolved custom elements, customized built-ins, and authored shadow hosts. |
| <span id="disclosure-slot-cdisclosure-slots-actions"></span>`actions` | no | `{}` ([`CDisclosureActionsSlotData`](#disclosure-interface-cdisclosure-actions-slot-data)) | No adjacent actions wrapper. Uses the default boundary and also rejects nested Disclosure or Accordion roots. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CDisclosure events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="disclosure-event-cdisclosure-events-on-open-change"></span>`onOpenChange` | `(open: boolean, detail: CDisclosureOpenChangeDetail) => void` ([`CDisclosureOpenChangeDetail`](#disclosure-interface-cdisclosure-open-change-detail)) | An enabled native trigger activation requests the opposite expansion state. | `{open: boolean, previousOpen: boolean, source: "activation", controlled: boolean}` ([`CDisclosureOpenChangeDetail`](#disclosure-interface-cdisclosure-open-change-detail)) | Runs before an uncontrolled commit. A controlled Disclosure waits for open; return values do not cancel. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CDisclosure CSS variables

Apply these variables to `CDisclosure` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="disclosure-css-cdisclosure-css-variables-background"></span>`--cui-disclosure-background` | `color` | Root surface. | `Canvas` |
| <span id="disclosure-css-cdisclosure-css-variables-foreground"></span>`--cui-disclosure-foreground` | `color` | Title and panel foreground. | `CanvasText` |
| <span id="disclosure-css-cdisclosure-css-variables-border-color"></span>`--cui-disclosure-border-color` | `color` | Outline boundary. | `Scheme-derived current-color mix.` |
| <span id="disclosure-css-cdisclosure-css-variables-border-width"></span>`--cui-disclosure-border-width` | `length` | Stable border geometry. | `1px` |
| <span id="disclosure-css-cdisclosure-css-variables-radius"></span>`--cui-disclosure-radius` | `length` | Root corner radius. | `0.75rem` |
| <span id="disclosure-css-cdisclosure-css-variables-trigger-background"></span>`--cui-disclosure-trigger-background` | `color` | Resting trigger surface. | `transparent` |
| <span id="disclosure-css-cdisclosure-css-variables-trigger-hover-background"></span>`--cui-disclosure-trigger-hover-background` | `color` | Enabled hover surface. | `Current-color mix.` |
| <span id="disclosure-css-cdisclosure-css-variables-trigger-open-background"></span>`--cui-disclosure-trigger-open-background` | `color` | Expanded trigger surface. | `Accent mix.` |
| <span id="disclosure-css-cdisclosure-css-variables-trigger-open-color"></span>`--cui-disclosure-trigger-open-color` | `color` | Expanded title and indicator. | `Scheme blue.` |
| <span id="disclosure-css-cdisclosure-css-variables-focus-color"></span>`--cui-disclosure-focus-color` | `color` | Trigger focus ring. | `Highlight` |
| <span id="disclosure-css-cdisclosure-css-variables-indicator-color"></span>`--cui-disclosure-indicator-color` | `color` | Chevron foreground. | `currentColor` |
| <span id="disclosure-css-cdisclosure-css-variables-trigger-padding-inline"></span>`--cui-disclosure-trigger-padding-inline` | `length` | Logical trigger inset. | `Size-derived.` |
| <span id="disclosure-css-cdisclosure-css-variables-trigger-padding-block"></span>`--cui-disclosure-trigger-padding-block` | `length` | Block trigger inset. | `Size-derived.` |
| <span id="disclosure-css-cdisclosure-css-variables-panel-padding-inline"></span>`--cui-disclosure-panel-padding-inline` | `length` | Logical body inset. | `Size-derived.` |
| <span id="disclosure-css-cdisclosure-css-variables-panel-padding-block"></span>`--cui-disclosure-panel-padding-block` | `length` | Block body inset. | `Size-derived.` |
| <span id="disclosure-css-cdisclosure-css-variables-actions-gap"></span>`--cui-disclosure-actions-gap` | `length` | Adjacent action spacing. | `0.5rem` |
| <span id="disclosure-css-cdisclosure-css-variables-duration"></span>`--cui-disclosure-duration` | `time` | Panel and indicator transition. | `180ms` |
| <span id="disclosure-css-cdisclosure-css-variables-easing"></span>`--cui-disclosure-easing` | `easing` | Panel and indicator transition curve. | `ease-out` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CDisclosure attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="disclosure-attribute-cdisclosure-attributes-data-variant"></span>`data-variant` | Root | `"outline" | "soft" | "plain"` | Mirrors effective treatment. |
| <span id="disclosure-attribute-cdisclosure-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Mirrors effective geometry. |
| <span id="disclosure-attribute-cdisclosure-attributes-data-state"></span>`data-state` | Root, trigger, and panel | `"open" | "closed"` | Mirrors committed expansion. |
| <span id="disclosure-attribute-cdisclosure-attributes-data-disabled"></span>`data-disabled` | Root and trigger | `present | absent` | Mirrors browser-effective trigger disabledness. |
| <span id="disclosure-attribute-cdisclosure-attributes-data-indicator"></span>`data-indicator` | Root | `present | absent` | Present while the chevron is shown. |
| <span id="disclosure-attribute-cdisclosure-attributes-data-indicator-pos"></span>`data-indicator-pos` | Root | `"start" | "end"` | Mirrors logical chevron placement. |
| <span id="disclosure-attribute-cdisclosure-attributes-id-root"></span>`id` | Root | `str` | Uses the supplied root ID or a generated instance ID. |
| <span id="disclosure-attribute-cdisclosure-attributes-generated-ids"></span>`id` | Trigger and panel | `generated str` | Derives the stable relationship pair from the root ID. |
| <span id="disclosure-attribute-cdisclosure-attributes-aria-expanded"></span>`aria-expanded` | Trigger | `"true" | "false"` | Exposes native expansion state. |
| <span id="disclosure-attribute-cdisclosure-attributes-aria-controls"></span>`aria-controls` | Trigger | `panel IDREF` | Identifies the controlled panel. |
| <span id="disclosure-attribute-cdisclosure-attributes-disabled"></span>`disabled` | Trigger | `present | absent` | Present for component-owned disabledness; a native fieldset can also disable without adding this attribute. |
| <span id="disclosure-attribute-cdisclosure-attributes-role-region"></span>`role` | Panel | `absent | "region"` | Present only when region is enabled. |
| <span id="disclosure-attribute-cdisclosure-attributes-aria-labelledby"></span>`aria-labelledby` | Panel | `absent | trigger IDREF` | Names an optional region from its trigger. |
| <span id="disclosure-attribute-cdisclosure-attributes-aria-hidden"></span>`aria-hidden` | Panel | `absent | "true"` | Present while closed. |
| <span id="disclosure-attribute-cdisclosure-attributes-inert"></span>`inert` | Panel | `present | absent` | Removes closed descendants from focus and interaction. |
| <span id="disclosure-attribute-cdisclosure-attributes-hidden-panel"></span>`hidden` | Panel | `present | absent` | Removes a settled closed panel from rendering. |
| <span id="disclosure-attribute-cdisclosure-attributes-hidden-indicator"></span>`hidden` | Indicator | `present | absent` | Removes the chevron when indicator is false. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CDisclosure selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="disclosure-selector-cdisclosure-selectors-disclosure"></span>`[data-citry-ui-part="disclosure"]` | Root div | Surface and class/style/attrs destination. |
| <span id="disclosure-selector-cdisclosure-selectors-disclosure-header"></span>`[data-citry-ui-part="disclosure-header"]` | Header div | Heading and adjacent-action layout. |
| <span id="disclosure-selector-cdisclosure-selectors-disclosure-heading"></span>`[data-citry-ui-part="disclosure-heading"]` | Native h2-h6 | Document-outline heading and heading_attrs destination. |
| <span id="disclosure-selector-cdisclosure-selectors-disclosure-trigger"></span>`[data-citry-ui-part="disclosure-trigger"]` | Native Button | Expansion control and trigger_attrs destination. |
| <span id="disclosure-selector-cdisclosure-selectors-disclosure-title"></span>`[data-citry-ui-part="disclosure-title"]` | Span | Structural title text wrapper. |
| <span id="disclosure-selector-cdisclosure-selectors-disclosure-indicator"></span>`[data-citry-ui-part="disclosure-indicator"]` | Decorative span | Owned chevron wrapper. |
| <span id="disclosure-selector-cdisclosure-selectors-disclosure-actions"></span>`[data-citry-ui-part="disclosure-actions"]` | Optional div | Adjacent actions and actions_attrs destination. |
| <span id="disclosure-selector-cdisclosure-selectors-disclosure-panel"></span>`[data-citry-ui-part="disclosure-panel"]` | Controlled div | Always-mounted presence surface and panel_attrs destination. |
| <span id="disclosure-selector-cdisclosure-selectors-disclosure-body"></span>`[data-citry-ui-part="disclosure-body"]` | Div | Panel content inset. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="disclosure-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="disclosure-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="disclosure-interface-variant"></span>`CDisclosureVariant` | `Literal["outline", "soft", "plain"]` |
| <span id="disclosure-interface-size"></span>`CDisclosureSize` | `Literal["sm", "md", "lg"]` |
| <span id="disclosure-interface-indicator-pos"></span>`CDisclosureIndicatorPos` | `Literal["start", "end"]` |
| <span id="disclosure-interface-heading-level"></span>`CDisclosureHeadingLevel` | `Literal[2, 3, 4, 5, 6]` |

</div>

<span id="disclosure-interface-cdisclosure-title-slot-data"></span>

#### `CDisclosureTitleSlotData`

Empty dataclass: `{}`.

<span id="disclosure-interface-cdisclosure-default-slot-data"></span>

#### `CDisclosureDefaultSlotData`

Empty dataclass: `{}`.

<span id="disclosure-interface-cdisclosure-actions-slot-data"></span>

#### `CDisclosureActionsSlotData`

Empty dataclass: `{}`.

<span id="disclosure-interface-cdisclosure-open-change-detail"></span>

#### `CDisclosureOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="disclosure-interface-cdisclosure-open-change-detail-open"></span>`open` | `boolean` | - | Requested next expansion. |
| <span id="disclosure-interface-cdisclosure-open-change-detail-previous-open"></span>`previousOpen` | `boolean` | - | Committed expansion before the request. |
| <span id="disclosure-interface-cdisclosure-open-change-detail-source"></span>`source` | `"activation"` | - | Native trigger activation source. |
| <span id="disclosure-interface-cdisclosure-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client Boolean owned state when requested. |

</div>

### Translation keys

-