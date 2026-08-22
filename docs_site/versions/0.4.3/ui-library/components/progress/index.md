---
title: Progress
url: https://citry.dev/v/0.4.3/ui-library/components/progress/
description: "Communicate determinate and indeterminate task progress with a native Citry UI progress element."
---
# Progress

Use `CProgress` for completion of an ongoing task. It renders the native
`progress` element, so determinate values, unknown duration, direction, and
assistive-technology semantics stay browser-owned.

## Progress at a glance


### Progress at a glance

[Open the rendered preview](/v/0.4.3/ui-library/components/progress/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ProgressAtAGlance(Component):
    template = """
      <section class="progress-glance">
        <c-CRow justify="between">
          <div><p>Research dive 08</p><h2>Mapping the reef shelf</h2></div>
          <strong>68%</strong>
        </c-CRow>
        <c-CProgress label="Mapping the reef shelf" c-value="68" shape="pill" />
        <p>Sonar pass 17 of 25 · 42 minutes remaining</p>
      </section>
    """
    css = """
      :where(.progress-glance) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 38rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#9fc5d4, #406572);
        border-radius: 0.85rem;
        background: light-dark(#f0fbff, #11252c);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-glance h2, .progress-glance p) {
        margin: 0;
      }

      :where(.progress-glance > p, .progress-glance [data-citry-ui-part="row"] p) {
        color: light-dark(#416a78, #a7cbd7);
        font-size: 0.78rem;
      }
    """


preview = ProgressAtAGlance()

preview  # noqa: B018
````


## Show known completion

Pass a finite `value` from zero through `max`. The default maximum is 100.


### Compare determinate values

[Open the rendered preview](/v/0.4.3/ui-library/components/progress/_previews/determinate/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DeterminateProgress(Component):
    template = """
      <c-CCol class_="progress-values">
        <div>
          <c-CRow justify="between"><span>Preparing vessel</span><strong>15%</strong></c-CRow>
          <c-CProgress label="Preparing vessel" c-value="15" />
        </div>
        <div>
          <c-CRow justify="between"><span>Descending</span><strong>50%</strong></c-CRow>
          <c-CProgress label="Descending" c-value="50" />
        </div>
        <div>
          <c-CRow justify="between"><span>Survey complete</span><strong>100%</strong></c-CRow>
          <c-CProgress label="Survey complete" c-value="100" intent="success" />
        </div>
      </c-CCol>
    """
    css = """
      :where(.progress-values) {
        max-inline-size: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-values > div) {
        display: grid;
        gap: 0.4rem;
      }
    """


preview = DeterminateProgress()

preview  # noqa: B018
````



```citry-html
<c-CProgress label="Mapping the reef shelf" c-value="68" />
```


## Show unknown duration

Omit `value`, or pass `None`, while work is active but its remaining duration
is unknown. This removes the native value attribute.


### Show indeterminate work

[Open the rendered preview](/v/0.4.3/ui-library/components/progress/_previews/indeterminate/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IndeterminateProgress(Component):
    template = """
      <section class="progress-unknown">
        <h2>Contacting the deep-sea relay</h2>
        <c-CProgress label="Contacting the deep-sea relay" shape="pill" />
        <p>The operation is active, but its remaining duration is unknown.</p>
      </section>
    """
    css = """
      :where(.progress-unknown) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 32rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-unknown h2, .progress-unknown p) {
        margin: 0;
      }

      :where(.progress-unknown p) {
        color: GrayText;
        font-size: 0.8rem;
      }
    """


preview = IndeterminateProgress()

preview  # noqa: B018
````


Reduced-motion preferences replace continuous motion with a static patterned
track.

## Use custom units

Set a positive `max` and supply `value_text` when the value is better explained
as items, bytes, stages, or another unit.


### Use a custom range and value text

[Open the rendered preview](/v/0.4.3/ui-library/components/progress/_previews/custom-range/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomRangeProgress(Component):
    template = """
      <section class="progress-range">
        <c-CRow justify="between"><h2>Sample crates cataloged</h2><strong>6 / 10</strong></c-CRow>
        <c-CProgress
          label="Sample crates cataloged"
          c-value="6"
          c-max="10"
          value_text="6 of 10 sample crates"
          intent="success"
        />
      </section>
    """
    css = """
      :where(.progress-range) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 32rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-range h2) {
        margin: 0;
        font-size: 0.95rem;
      }
    """


preview = CustomRangeProgress()

preview  # noqa: B018
````


## Choose a palette

Intent changes the range color. Keep the task label and surrounding text clear
without color.


### Compare Progress intents

[Open the rendered preview](/v/0.4.3/ui-library/components/progress/_previews/intents/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ProgressIntents(Component):
    template = """
      <c-CCol class_="progress-intents" gap="sm">
        <c-for each="item in items">
          <div><span>{{ item[1] }}</span><c-CProgress c-label="item[1]" c-value="62" c-intent="item[0]" /></div>
        </c-for>
      </c-CCol>
    """

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "items": (
                ("neutral", "Equipment check"),
                ("primary", "Survey pass"),
                ("success", "Samples secured"),
                ("warn", "Current increasing"),
                ("danger", "Pressure limit"),
            )
        }

    css = """
      :where(.progress-intents) {
        max-inline-size: 32rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-intents > div) {
        display: grid;
        gap: 0.3rem;
      }

      :where(.progress-intents span) {
        font-size: 0.8rem;
      }
    """


preview = ProgressIntents()

preview  # noqa: B018
````


## Choose thickness and shape

Sizes set track thickness. Shape selects square, rounded, or pill geometry.


### Compare Progress sizes and shapes

[Open the rendered preview](/v/0.4.3/ui-library/components/progress/_previews/sizes-and-shapes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ProgressSizesAndShapes(Component):
    template = """
      <c-CCol class_="progress-sizes">
        <c-CProgress label="Small square progress" c-value="35" size="sm" shape="square" />
        <c-CProgress label="Medium rounded progress" c-value="55" />
        <c-CProgress label="Large pill progress" c-value="75" size="lg" shape="pill" />
      </c-CCol>
    """
    css = """
      :where(.progress-sizes) {
        max-inline-size: 34rem;
        color: CanvasText;
      }
    """


preview = ProgressSizesAndShapes()

preview  # noqa: B018
````


## Control progress in the browser

Client inputs are passed through `$c-props="{...}"`. A number controls
determinate completion; `null` switches to indeterminate; omission returns to
the server fallback.


### Control Progress in the browser

[Open the rendered preview](/v/0.4.3/ui-library/components/progress/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledProgress(Component):
    template = """
      <section class="progress-controlled" x-data="{value: 28}">
        <c-CRow justify="between"><h2>Transect upload</h2><output x-text="`${value}%`"></output></c-CRow>
        <c-CProgress label="Transect upload" $c-props="{value}" shape="pill" />
        <label>Completion <input type="range" min="0" max="100" x-model.number="value" /></label>
      </section>
    """
    css = """
      :where(.progress-controlled) {
        display: grid;
        gap: 0.85rem;
        max-inline-size: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-controlled h2) {
        margin: 0;
        font-size: 1rem;
      }

      :where(.progress-controlled label) {
        display: grid;
        gap: 0.35rem;
        font-size: 0.8rem;
      }

      :where(.progress-controlled input) {
        inline-size: 100%;
      }
    """


preview = ControlledProgress()

preview  # noqa: B018
````


## Describe a busy region

When Progress describes another region, the application owns `aria-busy` on
that region and connects it to Progress. Clear busy state when the work
finishes.


### Connect Progress to a busy region

[Open the rendered preview](/v/0.4.3/ui-library/components/progress/_previews/busy-region/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BusyRegionProgress(Component):
    template = """
      <section class="progress-busy" aria-busy="true" aria-describedby="reef-progress">
        <h2>Reconstructing the reef map</h2>
        <p>Existing survey results remain visible while the new contour layer loads.</p>
        <c-CProgress
          label="Reconstructing the reef map"
          c-value="74"
          c-attrs="{'id': 'reef-progress'}"
        />
      </section>
    """
    css = """
      :where(.progress-busy) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 34rem;
        padding: 1rem;
        border: 1px solid light-dark(#b5d0d9, #436571);
        border-radius: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-busy h2, .progress-busy p) {
        margin: 0;
      }
    """


preview = BusyRegionProgress()

preview  # noqa: B018
````


## Customize Progress

Override public track, range, height, and radius variables on an ancestor or
one native Progress root.


### Customize Progress with public CSS

[Open the rendered preview](/v/0.4.3/ui-library/components/progress/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ProgressCustomization(Component):
    template = """
      <c-CCol class_="progress-themes">
        <div class="progress-themes__coral"><c-CProgress label="Coral lab" c-value="58" shape="pill" /></div>
        <div class="progress-themes__abyss"><c-CProgress label="Abyss lab" c-value="58" shape="pill" /></div>
      </c-CCol>
    """
    css = """
      :where(.progress-themes > div) {
        padding: 1.25rem;
        border-radius: 0.75rem;
      }

      :where(.progress-themes__coral) {
        --cui-progress-track-color: #f8ddd6;
        --cui-progress-range-color: #b9382f;
        --cui-progress-height: 0.75rem;
        background: #fff6f2;
      }

      :where(.progress-themes__abyss) {
        color-scheme: dark;
        --cui-progress-track-color: #1f3b48;
        --cui-progress-range-color: #63d4e8;
        --cui-progress-height: 0.75rem;
        background: #0b1b24;
      }
    """


preview = ProgressCustomization()

preview  # noqa: B018
````


## Choose the right indicator

Progress represents task completion. Use `CSpinner` for a compact unknown wait
without a linear track, and native `meter` for a scalar measurement that is not
task completion.

Progress has no focus, keyboard behavior, form value, live announcement, or
automatic busy-region mutation.

## API reference

### Inputs

#### CProgress server inputs

Server inputs are passed in a template through `<c-CProgress ... />` or in Python through
`CProgress(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="progress-input-cprogress-server-inputs-label"></span>`label` | `str` | required | Sets the required nonempty native accessible name and fallback text. |
| <span id="progress-input-cprogress-server-inputs-value"></span>`value` | `float | int | None` | `None` | Sets determinate completion from zero through max; None omits the native value attribute for indeterminate progress. |
| <span id="progress-input-cprogress-server-inputs-max"></span>`max` | `float | int` | `100` | Sets the positive native task maximum. |
| <span id="progress-input-cprogress-server-inputs-value-text"></span>`value_text` | `str | None` | `None` | Sets optional `aria-valuetext` when units are not naturally understood as a percentage. |
| <span id="progress-input-cprogress-server-inputs-intent"></span>`intent` | `"neutral" | "primary" | "success" | "warn" | "danger"` ([`CProgressIntent`](#progress-interface-input-type-aliases-cprogress-intent)) | `"primary"` | Selects the visual range palette; surrounding text still carries meaning. |
| <span id="progress-input-cprogress-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CProgressSize`](#progress-interface-input-type-aliases-cprogress-size)) | `"md"` | Sets track thickness. |
| <span id="progress-input-cprogress-server-inputs-shape"></span>`shape` | `"square" | "rounded" | "pill"` ([`CProgressShape`](#progress-interface-input-type-aliases-cprogress-shape)) | `"rounded"` | Sets native track and range radius. |
| <span id="progress-input-cprogress-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#progress-interface-input-type-aliases-class-value)) | `None` | Adds native root classes and merges them with `attrs`. |
| <span id="progress-input-cprogress-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#progress-interface-input-type-aliases-style-value)) | `None` | Adds native root inline styles and merges them with `attrs`. |
| <span id="progress-input-cprogress-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted nonconflicting native, ARIA relationship, data, and targeted Alpine attributes to the native progress root. |

</div>

#### CProgress client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CProgress />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="progress-input-cprogress-client-inputs-value"></span>`value` | `number | null` | Uses the server fallback. | Controls native determinate value; null removes the attribute for indeterminate state; omission returns to server fallback. |
| <span id="progress-input-cprogress-client-inputs-label"></span>`label` | `string` | Uses the server fallback. | Controls the nonempty native accessible name; omission returns to server fallback. |
| <span id="progress-input-cprogress-client-inputs-value-text"></span>`valueText` | `string | null` | Uses the server fallback. | Controls `aria-valuetext`; null removes it; omission returns to server fallback. |
| <span id="progress-input-cprogress-client-inputs-intent"></span>`intent` | `"neutral" | "primary" | "success" | "warn" | "danger"` | Uses the server fallback. | Controls the public visual palette reflection. |
| <span id="progress-input-cprogress-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` | Uses the server fallback. | Controls the public thickness reflection. |
| <span id="progress-input-cprogress-client-inputs-shape"></span>`shape` | `"square" | "rounded" | "pill"` | Uses the server fallback. | Controls the public radius reflection. |

</div>

### Slots

-

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CProgress CSS variables

Apply these variables to `CProgress` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="progress-css-cprogress-css-variables-cui-progress-track-color"></span>`--cui-progress-track-color` | `color` | Unfilled native track. | `Scheme-aware neutral color.` |
| <span id="progress-css-cprogress-css-variables-cui-progress-range-color"></span>`--cui-progress-range-color` | `color` | Completed range and indeterminate accent. | `Intent-derived color.` |
| <span id="progress-css-cprogress-css-variables-cui-progress-height"></span>`--cui-progress-height` | `length` | Native track thickness. | `Size-derived length.` |
| <span id="progress-css-cprogress-css-variables-cui-progress-radius"></span>`--cui-progress-radius` | `length` | Native track and range radius. | `Shape-derived length.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CProgress attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="progress-attribute-cprogress-attributes-value"></span>`value` | Native root | `number or absent` | Present only for determinate progress and controlled by the effective value. |
| <span id="progress-attribute-cprogress-attributes-max"></span>`max` | Native root | `positive number` | Reflects the server-owned task maximum. |
| <span id="progress-attribute-cprogress-attributes-aria-label"></span>`aria-label` | Native root | `nonempty string` | Carries the required accessible task name. |
| <span id="progress-attribute-cprogress-attributes-aria-valuetext"></span>`aria-valuetext` | Native root | `string or absent` | Carries optional application-authored value phrasing. |
| <span id="progress-attribute-cprogress-attributes-data-state"></span>`data-state` | Native root | `"determinate" | "indeterminate"` | Reflects whether the native value attribute is present. |
| <span id="progress-attribute-cprogress-attributes-data-intent"></span>`data-intent` | Native root | `"neutral" | "primary" | "success" | "warn" | "danger"` | Reflects the effective visual palette. |
| <span id="progress-attribute-cprogress-attributes-data-size"></span>`data-size` | Native root | `"sm" | "md" | "lg"` | Reflects effective thickness. |
| <span id="progress-attribute-cprogress-attributes-data-shape"></span>`data-shape` | Native root | `"square" | "rounded" | "pill"` | Reflects effective radius. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CProgress selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="progress-selector-cprogress-selectors-data-citry-ui-part-progress"></span>`[data-citry-ui-part="progress"]` | Native progress root | Stable public root and `attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="progress-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="progress-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="progress-interface-input-type-aliases-cprogress-intent"></span>`CProgressIntent` | `Literal["neutral", "primary", "success", "warn", "danger"]` |
| <span id="progress-interface-input-type-aliases-cprogress-size"></span>`CProgressSize` | `Literal["sm", "md", "lg"]` |
| <span id="progress-interface-input-type-aliases-cprogress-shape"></span>`CProgressShape` | `Literal["square", "rounded", "pill"]` |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CProgress translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="progress-translation-cprogress-translations-value-text"></span>`citry-ui-progress-value-text` | Provides readable fallback text for determinate progress. | `label: str; value: str; max: str` | None | `i18n.bind()` tracks locale and reactive value changes. |

</div>