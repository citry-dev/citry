---
title: Spinner
url: https://citry.dev/v/0.4.3/ui-library/components/spinner/
description: "Show compact unknown-duration activity with a labelled Citry UI Spinner."
---
# Spinner

Use `CSpinner` for compact activity whose duration is unknown. It renders one
indeterminate `progressbar`, works before JavaScript loads, and always requires
an accessible task label.

## Spinner at a glance


### Spinner at a glance

[Open the rendered preview](/v/0.4.3/ui-library/components/spinner/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SpinnerAtAGlance(Component):
    template = """
      <section class="spinner-glance">
        <div class="spinner-glance__sky" aria-hidden="true">✦ · ✧ · ✦</div>
        <c-CRow justify="center">
          <c-CSpinner label="Calibrating deep-sky camera" size="lg" />
          <div><h2>Calibrating the camera</h2><p>Reading dark frames from the observatory sensor.</p></div>
        </c-CRow>
      </section>
    """
    css = """
      :where(.spinner-glance) {
        display: grid;
        gap: 1rem;
        max-inline-size: 34rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b8b8dd, #4b4a78);
        border-radius: 0.9rem;
        background: light-dark(#f7f6ff, #17172a);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-glance__sky) {
        color: light-dark(#5b4bb7, #c4b5fd);
        font-size: 1.3rem;
        letter-spacing: 0.6rem;
        text-align: center;
      }

      :where(.spinner-glance h2, .spinner-glance p) {
        margin: 0;
      }

      :where(.spinner-glance p) {
        margin-block-start: 0.25rem;
        color: light-dark(#55546f, #c6c4de);
        font-size: 0.8rem;
      }
    """


preview = SpinnerAtAGlance()

preview  # noqa: B018
````


## Show active work

Pass a concise label that identifies the active task. Spinner does not display
the label, so pair it with visible text when users need the same context.


### Show basic Spinners

[Open the rendered preview](/v/0.4.3/ui-library/components/spinner/_previews/basic/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicSpinners(Component):
    template = """
      <c-CRow class_="spinner-basic" gap="lg">
        <c-CSpinner label="Loading lunar atlas" />
        <c-CSpinner label="Aligning telescope mount" intent="success" />
        <c-CSpinner label="Reconnecting weather station" intent="warn" />
      </c-CRow>
    """
    css = """
      :where(.spinner-basic) {
        padding: 1.25rem;
        color: CanvasText;
      }
    """


preview = BasicSpinners()

preview  # noqa: B018
````



```citry-html
<c-CSpinner label="Loading star catalog" />
```


## Choose a palette

Intent changes the ring color. Keep status meaning in surrounding text rather
than color alone.


### Compare Spinner intents

[Open the rendered preview](/v/0.4.3/ui-library/components/spinner/_previews/intents/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SpinnerIntents(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CRow class_="spinner-intents" gap="lg" wrap>
        <c-for each="intent in intents">
          <c-CCol c-attrs="{'data-spinner-intent-example': intent}" align="center" gap="xs">
            <c-CSpinner c-label="f'{intent} observatory task'" c-intent="intent" />
            <span>{{ intent }}</span>
          </c-CCol>
        </c-for>
      </c-CRow>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"intents": ("neutral", "primary", "success", "warn", "danger")}

    css = """
      :where(.spinner-intents) {
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-intents span) {
        font-size: 0.72rem;
      }
    """


preview = SpinnerIntents()

preview  # noqa: B018
````


## Choose a size

Use `sm`, `md`, or `lg`. Public CSS variables can set a one-off diameter or
thickness.


### Compare Spinner sizes

[Open the rendered preview](/v/0.4.3/ui-library/components/spinner/_previews/sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SpinnerSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CRow class_="spinner-sizes" gap="lg" align="center">
        <c-for each="size in sizes">
          <c-CCol align="center" gap="xs">
            <c-CSpinner c-label="f'{size} star-map load'" c-size="size" />
            <span>{{ size }}</span>
          </c-CCol>
        </c-for>
      </c-CRow>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"sizes": ("sm", "md", "lg")}

    css = """
      :where(.spinner-sizes) {
        min-block-size: 4rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-sizes span) {
        font-size: 0.72rem;
      }
    """


preview = SpinnerSizes()

preview  # noqa: B018
````


## Pair Spinner with text

Spinner is inline-sized and works beside concise status text. It never adds a
focus stop or changes surrounding controls.


### Compose inline activity

[Open the rendered preview](/v/0.4.3/ui-library/components/spinner/_previews/inline/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InlineSpinner(Component):
    template = """
      <section class="spinner-inline">
        <c-CRow gap="sm">
          <c-CSpinner label="Indexing nebula spectra" size="sm" />
          <span>Indexing nebula spectra</span>
        </c-CRow>
        <p>The rest of the observing log remains readable while the index catches up.</p>
      </section>
    """
    css = """
      :where(.spinner-inline) {
        max-inline-size: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-inline p) {
        margin-block-end: 0;
        color: light-dark(#57566f, #c8c6df);
        font-size: 0.8rem;
      }
    """


preview = InlineSpinner()

preview  # noqa: B018
````


## Control presentation in the browser

Client inputs are passed through `$c-props="{...}"`. They can update `label`,
`intent`, and `size`; omission returns to the server fallback.


### Control Spinner in the browser

[Open the rendered preview](/v/0.4.3/ui-library/components/spinner/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledSpinner(Component):
    template = """
      <section
        class="spinner-controlled"
        x-init="Alpine.store('spinnerControls', {intent: 'primary', size: 'md'})"
      >
        <c-CRow>
          <c-CSpinner
            label="Refreshing orbital catalog"
            $c-props="{
              intent: $store.spinnerControls.intent,
              size: $store.spinnerControls.size,
            }"
          />
          <span>Refreshing orbital catalog</span>
        </c-CRow>
        <c-CRow wrap>
          <label>
            Intent
            <select x-model="$store.spinnerControls.intent">
              <option>primary</option><option>success</option>
              <option>warn</option><option>danger</option>
            </select>
          </label>
          <label>
            Size
            <select x-model="$store.spinnerControls.size">
              <option>sm</option><option>md</option><option>lg</option>
            </select>
          </label>
        </c-CRow>
      </section>
    """
    css = """
      :where(.spinner-controlled) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-controlled label) {
        display: grid;
        gap: 0.3rem;
        font-size: 0.75rem;
      }
    """


preview = ControlledSpinner()

preview  # noqa: B018
````


## Describe a busy region

The region owner sets `aria-busy`, controls Spinner presence, and clears busy
state when work completes. Spinner does not mutate another element.


### Connect Spinner to a busy region

[Open the rendered preview](/v/0.4.3/ui-library/components/spinner/_previews/busy-region/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SpinnerBusyRegion(Component):
    template = """
      <section class="spinner-busy" aria-busy="true" aria-describedby="star-chart-status">
        <c-CRow>
          <c-CSpinner label="Updating star chart" c-attrs="{'id': 'star-chart-status'}" />
          <strong>Updating the star chart</strong>
        </c-CRow>
        <div class="spinner-busy__chart" aria-hidden="true">
          ✦&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;✧<br />
          &nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;✦&nbsp;&nbsp;·
        </div>
      </section>
    """
    css = """
      :where(.spinner-busy) {
        display: grid;
        gap: 1rem;
        max-inline-size: 30rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-busy__chart) {
        min-block-size: 5rem;
        padding: 1rem;
        border-radius: 0.7rem;
        background: light-dark(#ecebff, #1d1d35);
        color: light-dark(#5148a0, #c4b5fd);
        letter-spacing: 0.7rem;
        line-height: 2;
      }
    """


preview = SpinnerBusyRegion()

preview  # noqa: B018
````


## Avoid flashes for brief work

Delay Spinner in application state when a task normally finishes immediately.
The application also owns any minimum-visible duration.


### Delay brief activity feedback

[Open the rendered preview](/v/0.4.3/ui-library/components/spinner/_previews/delayed/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DelayedSpinner(Component):
    template = """
      <section class="spinner-delayed" x-data="{visible: false}">
        <button type="button" @click="visible = !visible">Toggle long-running observation</button>
        <div x-show="visible" class="spinner-delayed__status">
          <c-CSpinner label="Waiting for long exposure" size="sm" />
          <span>Waiting for the long exposure</span>
        </div>
        <p>Real applications show this only after their chosen delay.</p>
      </section>
    """
    css = """
      :where(.spinner-delayed) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-delayed__status) {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      :where(.spinner-delayed p) {
        margin: 0;
        color: light-dark(#57566f, #c8c6df);
        font-size: 0.78rem;
      }
    """


preview = DelayedSpinner()

preview  # noqa: B018
````


## Customize Spinner

Override public color, track, diameter, thickness, and duration variables on an
ancestor or one Spinner root.


### Customize Spinner with public CSS

[Open the rendered preview](/v/0.4.3/ui-library/components/spinner/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SpinnerCustomization(Component):
    template = """
      <c-CRow class_="spinner-custom" gap="lg">
        <div class="spinner-custom__violet"><c-CSpinner label="Violet observatory task" /></div>
        <div class="spinner-custom__solar"><c-CSpinner label="Solar observatory task" /></div>
        <div class="spinner-custom__ice"><c-CSpinner label="Ice observatory task" /></div>
      </c-CRow>
    """
    css = """
      :where(.spinner-custom > div) {
        display: grid;
        place-items: center;
        min-inline-size: 5rem;
        min-block-size: 5rem;
        border-radius: 0.75rem;
        background: light-dark(#f5f4ff, #17172a);
      }

      :where(.spinner-custom__violet) {
        --cui-spinner-color: #7c3aed;
        --cui-spinner-track-color: #ddd6fe;
        --cui-spinner-size: 2rem;
      }

      :where(.spinner-custom__solar) {
        --cui-spinner-color: #c2410c;
        --cui-spinner-track-color: #fed7aa;
        --cui-spinner-thickness: 0.24rem;
      }

      :where(.spinner-custom__ice) {
        --cui-spinner-color: #0891b2;
        --cui-spinner-track-color: #a5f3fc;
        --cui-spinner-duration: 1.2s;
      }
    """


preview = SpinnerCustomization()

preview  # noqa: B018
````


## Choose the right indicator

Use `CProgress` when completion has a meaningful linear track or known value.
Use `CButton(loading=True)` for a Button-owned pending action. Spinner does not
own overlays, live announcements, task timing, or determinate values.

## API reference

### Inputs

#### CSpinner server inputs

Server inputs are passed in a template through `<c-CSpinner ... />` or in Python through
`CSpinner(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="spinner-input-cspinner-server-inputs-label"></span>`label` | `str` | required | Sets the required nonempty accessible task name. |
| <span id="spinner-input-cspinner-server-inputs-intent"></span>`intent` | `"neutral" | "primary" | "success" | "warn" | "danger"` ([`CSpinnerIntent`](#spinner-interface-input-type-aliases-cspinner-intent)) | `"primary"` | Selects the visual ring palette; surrounding text still carries meaning. |
| <span id="spinner-input-cspinner-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CSpinnerSize`](#spinner-interface-input-type-aliases-cspinner-size)) | `"md"` | Sets ring diameter and default thickness. |
| <span id="spinner-input-cspinner-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#spinner-interface-input-type-aliases-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="spinner-input-cspinner-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#spinner-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="spinner-input-cspinner-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted nonconflicting metadata, description relationships, visibility, and targeted Alpine attributes to the Spinner root. |

</div>

#### CSpinner client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CSpinner />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="spinner-input-cspinner-client-inputs-label"></span>`label` | `string` | Uses the server fallback. | Controls the nonempty accessible task name; omission returns to server fallback. |
| <span id="spinner-input-cspinner-client-inputs-intent"></span>`intent` | `"neutral" | "primary" | "success" | "warn" | "danger"` | Uses the server fallback. | Controls the public visual palette reflection. |
| <span id="spinner-input-cspinner-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` | Uses the server fallback. | Controls the public size reflection. |

</div>

### Slots

-

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CSpinner CSS variables

Apply these variables to `CSpinner` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="spinner-css-cspinner-css-variables-cui-spinner-color"></span>`--cui-spinner-color` | `color` | Active ring arc. | `Intent-derived color.` |
| <span id="spinner-css-cspinner-css-variables-cui-spinner-track-color"></span>`--cui-spinner-track-color` | `color` | Quiet remainder of the ring. | `Current color mixed with transparency.` |
| <span id="spinner-css-cspinner-css-variables-cui-spinner-size"></span>`--cui-spinner-size` | `length` | Ring diameter. | `Size-derived length.` |
| <span id="spinner-css-cspinner-css-variables-cui-spinner-thickness"></span>`--cui-spinner-thickness` | `length` | Ring border width. | `Size-derived length.` |
| <span id="spinner-css-cspinner-css-variables-cui-spinner-duration"></span>`--cui-spinner-duration` | `time` | One rotation duration when motion is allowed. | `0.75s.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CSpinner attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="spinner-attribute-cspinner-attributes-role"></span>`role` | Root | `"progressbar"` | Exposes an indeterminate progress indicator. |
| <span id="spinner-attribute-cspinner-attributes-aria-label"></span>`aria-label` | Root | `nonempty string` | Carries the required accessible task name. |
| <span id="spinner-attribute-cspinner-attributes-data-intent"></span>`data-intent` | Root | `"neutral" | "primary" | "success" | "warn" | "danger"` | Reflects the effective visual palette. |
| <span id="spinner-attribute-cspinner-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Reflects effective diameter and default thickness. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CSpinner selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="spinner-selector-cspinner-selectors-data-citry-ui-part-spinner"></span>`[data-citry-ui-part="spinner"]` | Spinner root | Stable public root and `attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="spinner-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="spinner-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="spinner-interface-input-type-aliases-cspinner-intent"></span>`CSpinnerIntent` | `Literal["neutral", "primary", "success", "warn", "danger"]` |
| <span id="spinner-interface-input-type-aliases-cspinner-size"></span>`CSpinnerSize` | `Literal["sm", "md", "lg"]` |

</div>

### Translation keys

-