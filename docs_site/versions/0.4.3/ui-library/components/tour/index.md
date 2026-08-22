---
title: Tour
url: https://citry.dev/v/0.4.3/ui-library/components/tour/
description: "Build polished, target-aware product walkthroughs with Citry UI."
---
# Tour

Use `CTour` with direct `CTourStep` declarations for a short walkthrough.
Every title, body, and media slot renders on the server. A step can point to an
exact element ID or remain centered in the viewport.

When the Tour card is narrow, its progress text and step dots occupy their own
row above the skip, previous, next, and finish actions. This responds to the
card width, including a custom `--cui-tour-width`, rather than only to the page
viewport.

## Tour at a glance


### Tour at a glance

[Open the rendered preview](/v/0.4.3/ui-library/components/tour/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourAtAGlance(Component):
    template = """
      <div>
        <button id="tour-save" type="button">Save project</button>
        <c-CTour>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Show tour</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CTourStep value="welcome">
              <c-fill name="title">Welcome to the workspace</c-fill>
              <c-fill name="default">This short tour explains the primary workflow.</c-fill>
            </c-CTourStep>
            <c-CTourStep value="save" target_id="tour-save" placement="bottom-end">
              <c-fill name="title">Save your work</c-fill>
              <c-fill name="default">Use this action when the project is ready.</c-fill>
            </c-CTourStep>
          </c-fill>
        </c-CTour>
      </div>
    """


preview = TourAtAGlance()
preview  # noqa: B018
````


## Explain page targets

Set `target_id` to a stable HTML ID. Tour scrolls that element into view,
positions the card using logical placement, and keeps the highlighted target
available for interaction while the Tour is open. The spotlight never captures
pointer input, and collision handling keeps the card off the highlighted area.


### Target page elements

[Open the rendered preview](/v/0.4.3/ui-library/components/tour/_previews/targeted/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourTargets(Component):
    template = """
      <section class="tour-targets">
        <c-CButton c-attrs="{'id':'tour-filter'}" variant="outline">Filter</c-CButton>
        <c-CButton c-attrs="{'id':'tour-export'}">Export</c-CButton>
        <c-CTour>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Explain actions</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CTourStep value="filter" target_id="tour-filter" placement="bottom-start">
              <c-fill name="title">Narrow the results</c-fill>
              <c-fill name="default">Choose filters before exporting.</c-fill>
            </c-CTourStep>
            <c-CTourStep value="export" target_id="tour-export" placement="inline-end">
              <c-fill name="title">Export the current view</c-fill>
              <c-fill name="default">The export respects the active filters.</c-fill>
            </c-CTourStep>
          </c-fill>
        </c-CTour>
      </section>
    """
    css = ":where(.tour-targets){display:flex;flex-wrap:wrap;gap:1rem;align-items:center}"


preview = TourTargets()
preview  # noqa: B018
````


## Use centered introduction and finish steps

Omit `target_id` for a centered dialog step. Centered steps work well for an
introduction, a summary, or a finish message that does not belong to one page
control.


### Center Tour steps

[Open the rendered preview](/v/0.4.3/ui-library/components/tour/_previews/centered/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourCentered(Component):
    template = """
      <div class="tour-centered-preview">
        <c-CTour size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open introduction</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CTourStep value="intro" c-describe="True">
              <c-fill name="title">A focused introduction</c-fill>
              <c-fill name="default">Centered steps do not require a page target.</c-fill>
            </c-CTourStep>
            <c-CTourStep value="finish">
              <c-fill name="title">You are ready</c-fill>
              <c-fill name="default">Finish closes the Tour and restores focus.</c-fill>
            </c-CTourStep>
          </c-fill>
        </c-CTour>
      </div>
    """
    css = ":where(.tour-centered-preview) { min-block-size: 22rem; }"


preview = TourCentered()
preview  # noqa: B018
````


## Control open and active state

`open` and `active` are independent `$c-props` controls. In controlled mode,
`onOpenChange` and `onActiveChange` report requests; update your Alpine state
to accept them. Each detail includes a reason and the stable step value.


### Control a Tour

[Open the rendered preview](/v/0.4.3/ui-library/components/tour/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourControlled(Component):
    template = """
      <section x-data="{open:false,active:0,last:'No request'}">
        <c-CButton @click="open=true">Open controlled tour</c-CButton>
        <output x-text="last">No request</output>
        <c-CTour
          $c-props="{
            open,
            active,
            onOpenChange:(next,detail)=>{last=`Open: ${detail.reason}`;open=next},
            onActiveChange:(next,detail)=>{last=`Step: ${detail.reason}`;active=next},
          }"
        >
          <c-CTourStep value="first">
            <c-fill name="title">First controlled step</c-fill>
            <c-fill name="default">The parent accepts each requested index.</c-fill>
          </c-CTourStep>
          <c-CTourStep value="second">
            <c-fill name="title">Second controlled step</c-fill>
            <c-fill name="default">Open and active ownership are independent.</c-fill>
          </c-CTourStep>
        </c-CTour>
      </section>
    """


preview = TourControlled()
preview  # noqa: B018
````


## Handle conditional targets

With `missing_target="skip"`, Tour searches in the navigation direction for
the next available or centered step. Use `close` when continuing without the
requested target would be misleading. Tour accepts IDs, not arbitrary CSS
selectors or trusted HTML.


### Choose a missing-target policy

[Open the rendered preview](/v/0.4.3/ui-library/components/tour/_previews/missing-targets/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourMissingTargets(Component):
    template = """
      <c-CTour missing_target="skip">
        <c-fill name="activator" data="{ activator_attrs }">
          <c-CButton c-attrs="activator_attrs">Show conditional tour</c-CButton>
        </c-fill>
        <c-fill name="default">
          <c-CTourStep value="intro">
            <c-fill name="title">Conditional features</c-fill>
            <c-fill name="default">Unavailable targeted steps are skipped.</c-fill>
          </c-CTourStep>
          <c-CTourStep value="optional" target_id="feature-not-rendered">
            <c-fill name="title">Optional feature</c-fill>
            <c-fill name="default">This step is skipped because its target is absent.</c-fill>
          </c-CTourStep>
          <c-CTourStep value="summary">
            <c-fill name="title">Summary</c-fill>
            <c-fill name="default">The next available centered step remains usable.</c-fill>
          </c-CTourStep>
        </c-fill>
      </c-CTour>
    """


preview = TourMissingTargets()
preview  # noqa: B018
````


## Customize Tour

Public parts and `--cui-tour-*` variables customize the card, mask, spotlight,
progress, spacing, and focus treatment without replacing Tour behavior.


### Customize Tour

[Open the rendered preview](/v/0.4.3/ui-library/components/tour/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourCustomization(Component):
    template = """
      <c-CTour c-class_="['ocean-tour']">
        <c-fill name="activator" data="{ activator_attrs }">
          <c-CButton c-attrs="activator_attrs">Open custom tour</c-CButton>
        </c-fill>
        <c-fill name="close"><c-CIcon name="close" /></c-fill>
        <c-fill name="default">
          <c-CTourStep value="theme">
            <c-fill name="title">Ocean theme</c-fill>
            <c-fill name="default">Variables customize the stable Tour anatomy.</c-fill>
          </c-CTourStep>
        </c-fill>
      </c-CTour>
    """
    css = """
      :where(.ocean-tour) {
        --cui-tour-background: light-dark(#eff8ff, #102a43);
        --cui-tour-border-color: light-dark(#84caff, #2e90fa);
        --cui-tour-backdrop-color: rgb(2 32 71 / 62%);
        --cui-tour-radius: 1.25rem;
      }
    """


preview = TourCustomization()
preview  # noqa: B018
````


## Accessibility and localization

Tour uses a nonmodal native `<dialog>` so the highlighted page control remains
usable. Opening or changing a step focuses its title, Escape closes when
allowed, and closing restores focus to the activator. Tab is not trapped: it
may move between the Tour actions and the explained page. `describe=True`
explicitly connects a step body through `aria-describedby`; leave it false for
complex structured content.

Close, previous, next, finish, skip, and progress text come from the Citry UI
catalog. Explicit label inputs remain fixed; catalog defaults are server
rendered and update through `$c-tr` under a client-enabled i18n provider.

Because background controls remain interactive, do not use Tour for a decision
that must block the rest of the page. Use `CDialog` for that job.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CTour server inputs

Server inputs are passed in a template through `<c-CTour ... />` or in Python through
`CTour(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tour-input-ctour-server-inputs-id"></span>`id` | `str | None` | generated | Sets the host ID and bases dialog title and description IDs. |
| <span id="tour-input-ctour-server-inputs-open"></span>`open` | `bool` | `False` | Sets initial open state. |
| <span id="tour-input-ctour-server-inputs-active"></span>`active` | `int` | `0` | Sets the initial zero-based step index. |
| <span id="tour-input-ctour-server-inputs-dismissible"></span>`dismissible` | `bool` | `True` | Enables the built-in close action and permitted dismissal. |
| <span id="tour-input-ctour-server-inputs-close-on-escape"></span>`close_on_escape` | `bool` | `True` | Allows Escape dismissal when dismissible. |
| <span id="tour-input-ctour-server-inputs-close-on-outside"></span>`close_on_outside` | `bool` | `False` | Allows pointer dismissal outside the card when dismissible. |
| <span id="tour-input-ctour-server-inputs-skippable"></span>`skippable` | `bool` | `True` | Shows and enables the skip action. |
| <span id="tour-input-ctour-server-inputs-scroll"></span>`scroll` | `CTourScroll` ([`CTourScroll`](#tour-interface-scroll)) | `"auto"` | Selects target scrolling or disables it. |
| <span id="tour-input-ctour-server-inputs-missing-target"></span>`missing_target` | `CTourMissingTarget` ([`CTourMissingTarget`](#tour-interface-missing-target)) | `"skip"` | Skips unavailable targeted steps or closes the Tour. |
| <span id="tour-input-ctour-server-inputs-size"></span>`size` | `CTourSize` ([`CTourSize`](#tour-interface-size)) | `"md"` | Selects the default card width profile. |
| <span id="tour-input-ctour-server-inputs-close-label"></span>`close_label` | `str` | `"Close tour"` | Overrides the localized close action name. |
| <span id="tour-input-ctour-server-inputs-previous-label"></span>`previous_label` | `str` | `"Previous"` | Overrides the localized previous action text. |
| <span id="tour-input-ctour-server-inputs-next-label"></span>`next_label` | `str` | `"Next"` | Overrides the localized next action text. |
| <span id="tour-input-ctour-server-inputs-finish-label"></span>`finish_label` | `str` | `"Finish"` | Overrides the localized finish action text. |
| <span id="tour-input-ctour-server-inputs-skip-label"></span>`skip_label` | `str` | `"Skip tour"` | Overrides the localized skip action text. |
| <span id="tour-input-ctour-server-inputs-progress-label"></span>`progress_label` | `str` | `"Step {current} of {total}"` | Overrides progress text and must retain both placeholders. |
| <span id="tour-input-ctour-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#tour-interface-class-value)) | `None` | Adds classes to the Tour host. |
| <span id="tour-input-ctour-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#tour-interface-style-value)) | `None` | Adds styles to the Tour host. |
| <span id="tour-input-ctour-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed host attributes without replacing owned Tour state identity or behavior. |

</div>

#### CTour client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTour />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="tour-input-ctour-client-inputs-open"></span>`open` | `boolean | null` | Releases control to the committed value. | Controls Tour visibility independently from active step. |
| <span id="tour-input-ctour-client-inputs-active"></span>`active` | `number | null` | Releases control to the committed value. | Controls the zero-based active step independently from visibility. |
| <span id="tour-input-ctour-client-inputs-dismissible"></span>`dismissible` | `boolean` | Uses the server value. | Controls dismissal availability. |
| <span id="tour-input-ctour-client-inputs-close-on-escape"></span>`closeOnEscape` | `boolean` | Uses the server value. | Controls Escape dismissal. |
| <span id="tour-input-ctour-client-inputs-close-on-outside"></span>`closeOnOutside` | `boolean` | Uses the server value. | Controls outside-pointer dismissal. |
| <span id="tour-input-ctour-client-inputs-skippable"></span>`skippable` | `boolean` | Uses the server value. | Controls skip availability. |
| <span id="tour-input-ctour-client-inputs-scroll"></span>`scroll` | `CTourScroll` ([`CTourScroll`](#tour-interface-scroll)) | Uses the server value. | Controls target scroll behavior. |
| <span id="tour-input-ctour-client-inputs-missing-target"></span>`missingTarget` | `CTourMissingTarget` ([`CTourMissingTarget`](#tour-interface-missing-target)) | Uses the server value. | Controls missing-target reconciliation. |
| <span id="tour-input-ctour-client-inputs-size"></span>`size` | `CTourSize` ([`CTourSize`](#tour-interface-size)) | Uses the server value. | Controls card width profile. |
| <span id="tour-input-ctour-client-inputs-on-open-change"></span>`onOpenChange` | `function` | No open-state callback. | Receives reasoned visibility requests and commits. |
| <span id="tour-input-ctour-client-inputs-on-active-change"></span>`onActiveChange` | `function` | No active-step callback. | Receives reasoned step requests and commits. |

</div>

#### CTourStep server inputs

Server inputs are passed in a template through `<c-CTourStep ... />` or in Python through
`CTourStep(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tour-input-ctour-step-server-inputs-value"></span>`value` | `str` | required | Supplies unique stable step identity. |
| <span id="tour-input-ctour-step-server-inputs-target-id"></span>`target_id` | `str | None` | `None` | Targets one exact document element ID; omission creates a centered step. |
| <span id="tour-input-ctour-step-server-inputs-placement"></span>`placement` | `CTourPlacement` ([`CTourPlacement`](#tour-interface-placement)) | `"bottom"` | Requests logical target-relative card placement with flip and clamp. |
| <span id="tour-input-ctour-step-server-inputs-arrow"></span>`arrow` | `bool` | `True` | Shows the target-pointing arrow for targeted steps. |
| <span id="tour-input-ctour-step-server-inputs-describe"></span>`describe` | `bool` | `False` | Connects the active body through aria-describedby. |
| <span id="tour-input-ctour-step-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#tour-interface-class-value)) | `None` | Adds classes to the native step section. |
| <span id="tour-input-ctour-step-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#tour-interface-style-value)) | `None` | Adds styles to the native step section. |
| <span id="tour-input-ctour-step-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed step attributes without replacing owned identity state or visibility. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CTour slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tour-slot-ctour-slots-default"></span>`default` | yes | `{}` ([`CTourDefaultSlotData`](#tour-interface-ctour-default-slot-data)) | None; contains direct CTourStep declarations. |
| <span id="tour-slot-ctour-slots-activator"></span>`activator` | no | `{activator_attrs}` ([`CTourActivatorSlotData`](#tour-interface-ctour-activator-slot-data)) | Omitted. |
| <span id="tour-slot-ctour-slots-close"></span>`close` | no | `{}` ([`CTourCloseSlotData`](#tour-interface-ctour-close-slot-data)) | Decorative multiplication sign. |

</div>

#### CTourStep slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tour-slot-ctour-step-slots-title"></span>`title` | yes | `{index, total, value}` ([`CTourStepTitleSlotData`](#tour-interface-ctour-step-title-slot-data)) | None. |
| <span id="tour-slot-ctour-step-slots-default"></span>`default` | yes | `{index, total, value}` ([`CTourStepDefaultSlotData`](#tour-interface-ctour-step-default-slot-data)) | None. |
| <span id="tour-slot-ctour-step-slots-media"></span>`media` | no | `{index, total, value}` ([`CTourStepMediaSlotData`](#tour-interface-ctour-step-media-slot-data)) | Omitted. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CTour events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="tour-event-ctour-events-on-open-change"></span>`onOpenChange` | `(open: boolean, detail: CTourOpenChangeDetail) => void` ([`CTourOpenChangeDetail`](#tour-interface-ctour-open-change-detail)) | Activator dismissal skip finish target loss or native lifecycle requests a visibility change. | `{reason, active, value, controlled, source}` ([`CTourOpenChangeDetail`](#tour-interface-ctour-open-change-detail)) | Uncontrolled state commits before notification; controlled state is request-only. |
| <span id="tour-event-ctour-events-on-active-change"></span>`onActiveChange` | `(active: number, detail: CTourActiveChangeDetail) => void` ([`CTourActiveChangeDetail`](#tour-interface-ctour-active-change-detail)) | Previous next client reconciliation or missing-target skip requests a step change. | `{previousActive, value, previousValue, reason, controlled, source}` ([`CTourActiveChangeDetail`](#tour-interface-ctour-active-change-detail)) | Uncontrolled state commits before notification; controlled state is request-only. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTour CSS variables

Apply these variables to `CTour` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="tour-css-ctour-css-variables-width"></span>`--cui-tour-width` | `length` | Card inline size overriding the selected profile. | `sm 20rem; md 26rem; lg 30rem` |
| <span id="tour-css-ctour-css-variables-background"></span>`--cui-tour-background` | `color` | Card and arrow background. | `Adaptive canvas` |
| <span id="tour-css-ctour-css-variables-foreground"></span>`--cui-tour-foreground` | `color` | Card text and control color. | `CanvasText` |
| <span id="tour-css-ctour-css-variables-muted-color"></span>`--cui-tour-muted-color` | `color` | Progress and secondary action foreground. | `Adaptive high-contrast neutral` |
| <span id="tour-css-ctour-css-variables-border-color"></span>`--cui-tour-border-color` | `color` | Card control and arrow borders. | `Adaptive neutral` |
| <span id="tour-css-ctour-css-variables-shadow"></span>`--cui-tour-shadow` | `shadow` | Card elevation. | `Elevated overlay shadow` |
| <span id="tour-css-ctour-css-variables-radius"></span>`--cui-tour-radius` | `length` | Card corner radius. | `0.875rem` |
| <span id="tour-css-ctour-css-variables-padding"></span>`--cui-tour-padding` | `length` | Step panel padding. | `1.25rem` |
| <span id="tour-css-ctour-css-variables-gap"></span>`--cui-tour-gap` | `length` | Step anatomy spacing. | `1rem` |
| <span id="tour-css-ctour-css-variables-offset"></span>`--cui-tour-offset` | `length` | Target-to-card distance. | `0.75rem` |
| <span id="tour-css-ctour-css-variables-spotlight-padding"></span>`--cui-tour-spotlight-padding` | `length` | Space around the highlighted target. | `0.5rem` |
| <span id="tour-css-ctour-css-variables-spotlight-radius"></span>`--cui-tour-spotlight-radius` | `length` | Highlighted target corner radius. | `0.625rem` |
| <span id="tour-css-ctour-css-variables-backdrop-color"></span>`--cui-tour-backdrop-color` | `color` | Centered mask and target spotlight surround. | `rgb(0 0 0 / 58%)` |
| <span id="tour-css-ctour-css-variables-focus-color"></span>`--cui-tour-focus-color` | `color` | Action and title focus outline. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTour attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tour-attribute-ctour-attributes-data-open"></span>`data-open` | Tour host and dialog | `present | absent` | Marks effective Tour visibility. |
| <span id="tour-attribute-ctour-attributes-data-active"></span>`data-active` | Tour host | `nonnegative integer` | Mirrors effective active index. |
| <span id="tour-attribute-ctour-attributes-data-value"></span>`data-value` | Tour host and step panels | `string` | Mirrors stable active or declared step identity. |
| <span id="tour-attribute-ctour-attributes-data-size"></span>`data-size` | Tour host and surface | `CTourSize` ([`CTourSize`](#tour-interface-size)) | Mirrors card width profile. |
| <span id="tour-attribute-ctour-attributes-data-targeted"></span>`data-targeted` | Tour host | `present | absent` | Marks an active available target step. |
| <span id="tour-attribute-ctour-attributes-aria-labelledby"></span>`aria-labelledby` | Native dialog | `IDREF` | Refers to the active step title. |
| <span id="tour-attribute-ctour-attributes-aria-describedby"></span>`aria-describedby` | Native dialog | `IDREF | absent` | Refers to the active body only when describe is enabled. |
| <span id="tour-attribute-ctour-attributes-aria-modal"></span>`aria-modal` | Native dialog | `false` | States that the explained page remains available for interaction. |
| <span id="tour-attribute-ctour-attributes-data-index"></span>`data-index` | Step panel | `nonnegative integer` | Mirrors server-rendered order. |
| <span id="tour-attribute-ctour-attributes-data-current"></span>`data-current` | Step panel | `present | absent` | Marks the active panel. |
| <span id="tour-attribute-ctour-attributes-data-placement"></span>`data-placement` | Step panel and surface | `string` | Stores requested logical and applied physical placement respectively. |
| <span id="tour-attribute-ctour-attributes-data-target-id"></span>`data-target-id` | Step panel | `IDREF | absent` | Stores the exact authored target ID. |
| <span id="tour-attribute-ctour-attributes-data-describe"></span>`data-describe` | Step panel | `boolean-string` | Mirrors whether the body describes the dialog. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTour selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="tour-selector-ctour-selectors-tour"></span>`[data-citry-ui-part="tour"]` | Host div | State reflections and customization destination. |
| <span id="tour-selector-ctour-selectors-dialog"></span>`[data-citry-ui-part="dialog"]` | Native nonmodal dialog | Full-viewport Tour geometry owner. |
| <span id="tour-selector-ctour-selectors-spotlight"></span>`[data-citry-ui-part="spotlight"]` | Decorative div | Pointer-transparent target geometry and mask cutout. |
| <span id="tour-selector-ctour-selectors-surface"></span>`[data-citry-ui-part="surface"]` | Fixed card div | Placement scroll and visual surface. |
| <span id="tour-selector-ctour-selectors-panel"></span>`[data-citry-ui-part="panel"]` | Native section | Server-rendered step content and visibility owner. |
| <span id="tour-selector-ctour-selectors-media"></span>`[data-citry-ui-part="media"]` | Optional div | Authored step media. |
| <span id="tour-selector-ctour-selectors-header"></span>`[data-citry-ui-part="header"]` | Native header | Active step heading region. |
| <span id="tour-selector-ctour-selectors-title"></span>`[data-citry-ui-part="title"]` | Native h2 | Dialog name and step focus destination. |
| <span id="tour-selector-ctour-selectors-description"></span>`[data-citry-ui-part="description"]` | Native div | Authored step body and optional dialog description. |
| <span id="tour-selector-ctour-selectors-arrow"></span>`[data-citry-ui-part="arrow"]` | Decorative span | Target direction indicator. |
| <span id="tour-selector-ctour-selectors-close"></span>`[data-citry-ui-part="close"]` | Native Button | Dismissal action. |
| <span id="tour-selector-ctour-selectors-footer"></span>`[data-citry-ui-part="footer"]` | Native footer | Progress and navigation grouping. |
| <span id="tour-selector-ctour-selectors-progress-group"></span>`[data-citry-ui-part="progress-group"]` | Div | Groups text and visual step position. |
| <span id="tour-selector-ctour-selectors-progress"></span>`[data-citry-ui-part="progress"]` | Polite span | Localized step position. |
| <span id="tour-selector-ctour-selectors-steps"></span>`[data-citry-ui-part="steps"]` | Decorative span | Visual step indicator group. |
| <span id="tour-selector-ctour-selectors-step-dot"></span>`[data-citry-ui-part="step-dot"]` | Decorative span | One visual step position marker. |
| <span id="tour-selector-ctour-selectors-actions"></span>`[data-citry-ui-part="actions"]` | Div | Skip previous next and finish controls. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="tour-interface-placement"></span>`CTourPlacement` | `Literal["top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end", "inline-start", "inline-end"]` |
| <span id="tour-interface-scroll"></span>`CTourScroll` | `Literal["auto", "smooth", "none"]` |
| <span id="tour-interface-missing-target"></span>`CTourMissingTarget` | `Literal["skip", "close"]` |
| <span id="tour-interface-size"></span>`CTourSize` | `Literal["sm", "md", "lg"]` |
| <span id="tour-interface-open-reason"></span>`CTourOpenReason` | `Literal["activator", "close", "escape", "outside", "skip", "finish", "missing-target", "native"]` |
| <span id="tour-interface-active-reason"></span>`CTourActiveReason` | `Literal["next", "previous", "client", "missing-target"]` |
| <span id="tour-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="tour-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="tour-interface-ctour-default-slot-data"></span>

#### `CTourDefaultSlotData`

Empty dataclass: `{}`.

<span id="tour-interface-ctour-activator-slot-data"></span>

#### `CTourActivatorSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tour-interface-ctour-activator-slot-data-activator-attrs"></span>`activator_attrs` | `dict[str, object]` | - | Form-safe dialog activation ARIA and behavior attributes. |

</div>

<span id="tour-interface-ctour-close-slot-data"></span>

#### `CTourCloseSlotData`

Empty dataclass: `{}`.

<span id="tour-interface-ctour-step-slot-data"></span>

#### `CTourStepSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tour-interface-ctour-step-slot-data-index"></span>`index` | `int` | - | Zero-based server-rendered index. |
| <span id="tour-interface-ctour-step-slot-data-total"></span>`total` | `int` | - | Total rendered step count. |
| <span id="tour-interface-ctour-step-slot-data-value"></span>`value` | `str` | - | Stable step identity. |

</div>

<span id="tour-interface-ctour-step-title-slot-data"></span>

#### `CTourStepTitleSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tour-interface-ctour-step-title-slot-data-index"></span>`index` | `int` | - | Zero-based server-rendered index. |
| <span id="tour-interface-ctour-step-title-slot-data-total"></span>`total` | `int` | - | Total rendered step count. |
| <span id="tour-interface-ctour-step-title-slot-data-value"></span>`value` | `str` | - | Stable step identity. |

</div>

<span id="tour-interface-ctour-step-default-slot-data"></span>

#### `CTourStepDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tour-interface-ctour-step-default-slot-data-index"></span>`index` | `int` | - | Zero-based server-rendered index. |
| <span id="tour-interface-ctour-step-default-slot-data-total"></span>`total` | `int` | - | Total rendered step count. |
| <span id="tour-interface-ctour-step-default-slot-data-value"></span>`value` | `str` | - | Stable step identity. |

</div>

<span id="tour-interface-ctour-step-media-slot-data"></span>

#### `CTourStepMediaSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tour-interface-ctour-step-media-slot-data-index"></span>`index` | `int` | - | Zero-based server-rendered index. |
| <span id="tour-interface-ctour-step-media-slot-data-total"></span>`total` | `int` | - | Total rendered step count. |
| <span id="tour-interface-ctour-step-media-slot-data-value"></span>`value` | `str` | - | Stable step identity. |

</div>

<span id="tour-interface-ctour-open-change-detail"></span>

#### `CTourOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tour-interface-ctour-open-change-detail-reason"></span>`reason` | `CTourOpenReason` ([`CTourOpenReason`](#tour-interface-open-reason)) | - | Cause of the visibility request or commit. |
| <span id="tour-interface-ctour-open-change-detail-active"></span>`active` | `int` | - | Effective active index. |
| <span id="tour-interface-ctour-open-change-detail-value"></span>`value` | `str` | - | Effective stable step identity. |
| <span id="tour-interface-ctour-open-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client state controls visibility. |
| <span id="tour-interface-ctour-open-change-detail-source"></span>`source` | `object | None` | - | Native source element or null for client reconciliation. |

</div>

<span id="tour-interface-ctour-active-change-detail"></span>

#### `CTourActiveChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tour-interface-ctour-active-change-detail-previous-active"></span>`previousActive` | `int` | - | Effective index before the request. |
| <span id="tour-interface-ctour-active-change-detail-value"></span>`value` | `str` | - | Requested stable step identity. |
| <span id="tour-interface-ctour-active-change-detail-previous-value"></span>`previousValue` | `str` | - | Effective stable identity before the request. |
| <span id="tour-interface-ctour-active-change-detail-reason"></span>`reason` | `CTourActiveReason` ([`CTourActiveReason`](#tour-interface-active-reason)) | - | Cause of the step request or commit. |
| <span id="tour-interface-ctour-active-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client state controls the active index. |
| <span id="tour-interface-ctour-active-change-detail-source"></span>`source` | `object | None` | - | Native source element or null for client reconciliation. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CTour translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="tour-translation-ctour-translations-close"></span>`citry-ui-tour-close` | Names the built-in dismissal control. | `None.` | `close_label` | `$c-tr` updates each stable `aria-label` destination. |
| <span id="tour-translation-ctour-translations-previous"></span>`citry-ui-tour-previous` | Labels previous-step actions. | `None.` | `previous_label` | `$c-tr` updates server-rendered action text. |
| <span id="tour-translation-ctour-translations-next"></span>`citry-ui-tour-next` | Labels next-step actions. | `None.` | `next_label` | `$c-tr` updates server-rendered action text. |
| <span id="tour-translation-ctour-translations-finish"></span>`citry-ui-tour-finish` | Labels final-step completion actions. | `None.` | `finish_label` | `$c-tr` updates server-rendered action text. |
| <span id="tour-translation-ctour-translations-skip"></span>`citry-ui-tour-skip` | Labels skip actions. | `None.` | `skip_label` | `$c-tr` updates server-rendered action text. |
| <span id="tour-translation-ctour-translations-progress"></span>`citry-ui-tour-progress` | Reports current step position. | `current: str; total: str` | `progress_label` with `{current}` and `{total}` | `$c-tr` updates every stable progress destination with checked literal values. |

</div>