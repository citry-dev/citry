---
title: Checkbox
url: https://citry.dev/v/0.4.4/ui-library/components/checkbox/
description: "Choose independent Boolean options with native forms, mixed state, and controlled browser checkedness."
---
# Checkbox

Use `CCheckbox` for one independent Boolean choice or one item in a native
multi-value field. It keeps a real checkbox input, visible label, optional
description, form submission, validation, reset, and browser events.

## Checkbox at a glance

Unchecked, checked, disabled, and described choices retain the same native
interaction model.


### Checkbox at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/checkbox/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxAtAGlance(Component):
    template = """
      <section class="botanical-checklist" aria-label="Botanical field checklist">
        <header>
          <p>Morning survey</p>
          <h2>Woodland observations</h2>
        </header>
        <div class="botanical-checklist__grid">
          <c-CCheckbox name="observed" value="fern" checked>
            Lady fern unfurled
          </c-CCheckbox>
          <c-CCheckbox name="observed" value="moss">
            <c-fill name="default">Cushion moss fruiting</c-fill>
            <c-fill name="description">
              Check the shaded side of fallen trunks.
            </c-fill>
          </c-CCheckbox>
          <c-CCheckbox name="observed" value="lichen" variant="outline">
            Reindeer lichen present
          </c-CCheckbox>
          <c-CCheckbox disabled>
            <c-fill name="default">Alpine saxifrage</c-fill>
            <c-fill name="description">
              Outside this survey's elevation range.
            </c-fill>
          </c-CCheckbox>
        </div>
      </section>
    """

    css = """
      :where(.botanical-checklist) {
        display: grid;
        gap: 1rem;
        max-width: 48rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b8d2bd, #365c42);
        border-radius: 1rem;
        background: light-dark(#f6fbf5, #12251a);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.botanical-checklist h2, .botanical-checklist p) {
        margin: 0;
      }

      :where(.botanical-checklist header p) {
        color: light-dark(#286b43, #7bd9a0);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.botanical-checklist__grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
      }
    """


preview = CheckboxAtAGlance()

preview  # noqa: B018
````


## Compose a Checkbox

Write the visible label in the default slot. Add `description` when the choice
needs supporting text.


### Compose Checkbox in templates and Python

[Open the rendered preview](/v/0.4.4/ui-library/components/checkbox/_previews/compose-checkbox/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCheckbox

citry.register_library(citry_ui)


class ComposeCheckbox(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "python_checkbox": CCheckbox(
                name="archive",
                value="photographs",
                variant="outline",
                slots={"default": "Archive specimen photographs"},
            )
        }

    template = """
      <section class="checkbox-compose" aria-label="Checkbox authoring forms">
        <div>
          <p class="checkbox-compose__eyebrow">Template</p>
          <c-CCheckbox name="archive" value="notes" checked>
            Archive handwritten field notes
          </c-CCheckbox>
        </div>
        <div>
          <p class="checkbox-compose__eyebrow">Python composition</p>
          {{ python_checkbox }}
        </div>
      </section>
    """

    css = """
      :where(.checkbox-compose) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        max-width: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-compose > div) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
        border: 1px solid light-dark(#c8d8c3, #3d5540);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.checkbox-compose__eyebrow) {
        margin: 0;
        color: light-dark(#38714a, #86c999);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
      }
    """


preview = ComposeCheckbox()

preview  # noqa: B018
````



```citry-html
<c-CCheckbox
  name="field_notes"
  value="included"
>
  Include field notes
</c-CCheckbox>
```


Compose the same control in Python:


```python
from citry_ui import CCheckbox

field_notes = CCheckbox(
    name="field_notes",
    value="included",
    slots={"default": "Include field notes"},
)
```


The default and description slots accept phrasing content. Keep controls,
editable content, and nested labels outside Checkbox.

## Configure Checkbox

Server inputs are passed in Python through `<c-CCheckbox ... />` attributes or
a `CCheckbox(...)` composition call. Client inputs are passed in the browser
through `$c-props="{...}"`.


### Configure Checkbox

[Open the rendered preview](/v/0.4.4/ui-library/components/checkbox/_previews/configuration/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxConfiguration(Component):
    template = """
      <section
        class="checkbox-configurator"
        x-data="{
          variant: 'solid',
          size: 'md',
          label_pos: 'end',
          checked: true,
          indeterminate: false,
          required: false,
          disabled: false,
          invalid: false,
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Living collection</p>
          <h2>Configure the record marker</h2>
        </header>
        <c-CCheckbox
          $c-props="{
            variant,
            size,
            label_pos,
            checked,
            indeterminate,
            required,
            disabled,
            invalid,
          }"
          @input="checked = $event.target.checked; indeterminate = false"
        >
          <c-fill name="default">Verified against the herbarium sheet</c-fill>
          <c-fill name="description">
            Match leaf shape, vein pattern, and collection date.
          </c-fill>
        </c-CCheckbox>
      </section>
    """

    css = """
      :where(.checkbox-configurator) {
        display: grid;
        gap: 1.25rem;
        max-width: 50rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b7cfba, #3a5940);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.checkbox-configurator h2, .checkbox-configurator p) {
        margin: 0;
      }

      :where(.checkbox-configurator header p) {
        color: light-dark(#287047, #7ed6a0);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "solid",
        "options": (("solid", "Solid"), ("outline", "Outline")),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "label_pos",
        "label": "Label position",
        "type": "select",
        "default": "end",
        "options": (("end", "End"), ("start", "Start")),
    },
    {"name": "checked", "label": "Checked", "type": "checkbox", "default": True},
    {"name": "indeterminate", "label": "Indeterminate", "type": "checkbox", "default": False},
    {"name": "required", "label": "Required", "type": "checkbox", "default": False},
    {"name": "disabled", "label": "Disabled", "type": "checkbox", "default": False},
    {"name": "invalid", "label": "Invalid", "type": "checkbox", "default": False},
)

preview = CheckboxConfiguration()

preview  # noqa: B018
````


`checked` and `indeterminate` are independently controllable. Omit either
client input to release that property without replacing the browser's current
value. Other omitted client inputs return to their server, Field, or Form
fallback.

## Submit and validate native values

A checked, enabled Checkbox with a name contributes one `FormData` entry.
Unchecked controls contribute nothing. Reuse a name to submit several checked
values.


### Submit, validate, and reset Checkbox values

[Open the rendered preview](/v/0.4.4/ui-library/components/checkbox/_previews/forms-and-validation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxForms(Component):
    template = """
      <section
        class="checkbox-form-demo"
        x-data="{result: 'Submit the form to inspect its native values.'}"
      >
        <c-CForm
          id="botanical-survey"
          @submit.prevent="result = JSON.stringify(
            Array.from(new FormData($event.target).entries())
          )"
          @reset="result = 'The browser restored the server defaults.'"
        >
          <fieldset>
            <legend>Habitats observed</legend>
            <c-CCheckbox name="habitat" value="meadow" checked>
              Meadow edge
            </c-CCheckbox>
            <c-CCheckbox name="habitat" value="woodland" checked>
              Ancient woodland
            </c-CCheckbox>
            <c-CCheckbox name="habitat" value="wetland">
              Wetland margin
            </c-CCheckbox>
          </fieldset>
          <c-CCheckbox name="confirmed" value="yes" required>
            I checked the location against the field map
          </c-CCheckbox>
          <div class="checkbox-form-demo__actions">
            <c-CButton type="submit">Record survey</c-CButton>
            <c-CButton type="reset" variant="outline" intent="neutral">Reset</c-CButton>
          </div>
        </c-CForm>
        <output x-text="result" aria-live="polite"></output>
      </section>
    """

    css = """
      :where(.checkbox-form-demo) {
        display: grid;
        gap: 1rem;
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-form-demo fieldset) {
        display: grid;
        gap: 0.75rem;
        margin: 0;
        padding: 1rem;
        border: 1px solid light-dark(#bfd1ba, #415943);
        border-radius: 0.75rem;
      }

      :where(.checkbox-form-demo legend) {
        padding-inline: 0.35rem;
        font-weight: 700;
      }

      :where(.checkbox-form-demo__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.checkbox-form-demo output) {
        padding: 0.75rem;
        border-radius: 0.625rem;
        background: light-dark(#f1f7ef, #18271a);
        font-family: ui-monospace, monospace;
        font-size: 0.875rem;
      }
    """


preview = CheckboxForms()

preview  # noqa: B018
````


`required` applies to one Checkbox. It means that exact control must be
checked, not that one item in a group must be selected. Use application
validation for group minimums until `CCheckboxGroup` has its own contract.

Checkbox does not add a hidden false value. Native Form submission remains the
source of truth.

## Control checked state in the browser

Mirror `event.target.checked` from the native bubbling `input` event to accept
the browser's change. The listener lives on Checkbox's neutral root, so
`event.currentTarget` is not the native input.


### Control, release, and reacquire checkedness

[Open the rendered preview](/v/0.4.4/ui-library/components/checkbox/_previews/controlled-states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledCheckbox(Component):
    template = """
      <section
        class="checkbox-control-demo"
        x-data
        x-init="Alpine.store('checkboxOwnership', {controlled: true, checked: false})"
      >
        <c-CCheckbox
          $c-props="{
            checked: $store.checkboxOwnership.controlled
              ? $store.checkboxOwnership.checked
              : undefined,
          }"
          @input="$store.checkboxOwnership.checked = $event.target.checked"
        >
          <c-fill name="default">Press this leaf in the field journal</c-fill>
          <c-fill name="description">
            <span
              x-text="$store.checkboxOwnership.controlled
                ? 'Application controlled'
                : 'Browser controlled'"
            ></span>
          </c-fill>
        </c-CCheckbox>
        <div class="checkbox-control-demo__actions">
          <c-CButton
            size="sm"
            @click="$store.checkboxOwnership.controlled = false"
          >
            Release
          </c-CButton>
          <c-CButton
            size="sm"
            variant="outline"
            @click="$store.checkboxOwnership.checked = true; $store.checkboxOwnership.controlled = true"
          >
            Check and reacquire
          </c-CButton>
          <c-CButton
            size="sm"
            variant="ghost"
            intent="neutral"
            @click="$store.checkboxOwnership.checked = false; $store.checkboxOwnership.controlled = true"
          >
            Clear and reacquire
          </c-CButton>
        </div>
      </section>
    """

    css = """
      :where(.checkbox-control-demo) {
        display: grid;
        gap: 1rem;
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-control-demo__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ControlledCheckbox()

preview  # noqa: B018
````



```citry-html
<c-CCheckbox
  $c-props="{ checked: selected }"
  @input="selected = $event.target.checked"
>
  Archive specimen
</c-CCheckbox>
```


Both `input` and `change` observe the browser-produced value before an
unchanged controlled prop is restored. Use `focusin` and `focusout` at the
component boundary. Observe native validation with `@invalid.capture`.

Do not drive state from root `click`: clicking label text produces the native
label click followed by the input click.

## Show a mixed aggregate

Indeterminate is visual state independent of checkedness and Form submission.
Use it for an aggregate whose descendants are partly selected.


### Control a mixed habitat summary

[Open the rendered preview](/v/0.4.4/ui-library/components/checkbox/_previews/indeterminate/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IndeterminateCheckbox(Component):
    template = """
      <section
        class="habitat-summary"
        x-data="{
          meadow: true,
          woodland: false,
          wetland: true,
          get count() { return [this.meadow, this.woodland, this.wetland].filter(Boolean).length },
          get all() { return this.count === 3 },
          get mixed() { return this.count > 0 && this.count < 3 },
          setAll(value) { this.meadow = value; this.woodland = value; this.wetland = value },
        }"
      >
        <c-CCheckbox
          variant="outline"
          $c-props="{checked: all, indeterminate: mixed}"
          @input="setAll($event.target.checked)"
        >
          <c-fill name="default">All survey habitats</c-fill>
          <c-fill name="description">
            <span x-text="`${count} of 3 selected`"></span>
          </c-fill>
        </c-CCheckbox>
        <div class="habitat-summary__children">
          <c-CCheckbox
            $c-props="{checked: meadow}"
            @input="meadow = $event.target.checked"
          >
            Limestone meadow
          </c-CCheckbox>
          <c-CCheckbox
            $c-props="{checked: woodland}"
            @input="woodland = $event.target.checked"
          >
            Beech woodland
          </c-CCheckbox>
          <c-CCheckbox
            $c-props="{checked: wetland}"
            @input="wetland = $event.target.checked"
          >
            Reed wetland
          </c-CCheckbox>
        </div>
      </section>
    """

    css = """
      :where(.habitat-summary) {
        display: grid;
        gap: 0.9rem;
        max-width: 36rem;
        padding: 1rem;
        border: 1px solid light-dark(#b8d0b9, #3b5a41);
        border-radius: 0.875rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.habitat-summary__children) {
        display: grid;
        gap: 0.7rem;
        padding-inline-start: 1.75rem;
      }
    """


preview = IndeterminateCheckbox()

preview  # noqa: B018
````


HTML has no indeterminate content attribute. Citry's browser runtime sets the
native `indeterminate` property and the native accessibility mapping exposes
mixed state. Server-only output remains an ordinary two-state Checkbox.

Native activation clears indeterminate before `input` and `change`. Supply a
client `indeterminate` value when application state must restore or recompute
it.

## Use Field and Form state

Put Checkbox inside `CField` for an external label, Field description, error,
and shared required, disabled, or invalid state. Omit Checkbox's own label and
description slots in this composition.


### Compose Checkbox with Field and Form

[Open the rendered preview](/v/0.4.4/ui-library/components/checkbox/_previews/field-states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxFieldStates(Component):
    template = """
      <section class="checkbox-field-states">
        <c-CField required>
          <c-fill name="label">Seed-bank handling agreement</c-fill>
          <c-fill name="default">
            <c-CCheckbox name="agreement" value="accepted" />
          </c-fill>
          <c-fill name="description">Required before opening a preserved packet.</c-fill>
          <c-fill name="error">Accept the handling agreement.</c-fill>
        </c-CField>

        <c-CField invalid>
          <c-fill name="label">Provenance confirmed</c-fill>
          <c-fill name="default">
            <c-CCheckbox name="provenance" />
          </c-fill>
          <c-fill name="error">Confirm the collector and location first.</c-fill>
        </c-CField>

        <c-CField disabled>
          <c-fill name="label">Destructive pollen sampling</c-fill>
          <c-fill name="default">
            <c-CCheckbox name="pollen" />
          </c-fill>
          <c-fill name="description">Unavailable for this rare specimen.</c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.checkbox-field-states) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1.25rem;
        max-width: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-field-states > [data-citry-ui-part="field"]) {
        align-content: start;
        padding: 1rem;
        border: 1px solid light-dark(#c5d5c1, #3e5541);
        border-radius: 0.75rem;
        background: Canvas;
      }
    """


preview = CheckboxFieldStates()

preview  # noqa: B018
````


Native checkbox inputs do not support read-only. A standalone Checkbox ignores
Form read-only. A Field requesting read-only rejects Checkbox instead of
presenting an editable control as locked. Set `CField(readonly=False)` to opt
that Field out of an enclosing read-only Form.

A disabled Form always wins over local server or client `disabled=False`.
The same applies to a native disabled `fieldset`: browser-effective disabled
state drives the public mirror and styling even when the input's own
`disabled` property is false.

## Label long and compact choices

`label_pos="start"` moves the authored label and description to the logical
start. Direction-aware layout keeps that meaning in RTL. Long text wraps while
the control stays aligned with the first line.


### Use labels, descriptions, and accessible-name-only controls

[Open the rendered preview](/v/0.4.4/ui-library/components/checkbox/_previews/label-and-description/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxLabels(Component):
    template = """
      <section class="checkbox-labels">
        <c-CCheckbox label_pos="start" variant="outline">
          <c-fill name="default">
            Preserve this unusually long field-note label when the observation is
            exported to the regional botanical archive
          </c-fill>
          <c-fill name="description">
            Logical start placement and narrow wrapping remain direction-aware.
          </c-fill>
        </c-CCheckbox>
        <div dir="rtl">
          <c-CCheckbox label_pos="start">
            <c-fill name="default">تضمين ملاحظات الموطن</c-fill>
            <c-fill name="description">يبقى موضع التسمية منطقيًا في الاتجاه من اليمين.</c-fill>
          </c-CCheckbox>
        </div>
        <div class="checkbox-labels__row">
          <span>Polypody fern, row 17</span>
          <c-CCheckbox c-input_attrs="{'aria-label': 'Select polypody fern row 17'}" />
        </div>
      </section>
    """

    css = """
      :where(.checkbox-labels) {
        display: grid;
        gap: 1.25rem;
        max-width: 32rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-labels > *) {
        min-width: 0;
        padding: 0.9rem;
        border: 1px solid light-dark(#c7d7c5, #3c5541);
        border-radius: 0.75rem;
      }

      :where(.checkbox-labels__row) {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
      }
    """


preview = CheckboxLabels()

preview  # noqa: B018
````


For a label-free standalone Checkbox, pass exactly one non-empty static
`aria-label` or `aria-labelledby` through `input_attrs`. Do not add ARIA naming
when a default label or Field label renders: hidden text must not replace the
visible accessible name.

## Choose variant and size

`solid` fills checked and mixed controls. `outline` keeps the surface and uses
the active color for the indicator and border. `sm`, `md`, and `lg` change
control geometry and associated text scale.


### Compare Checkbox variants and sizes

[Open the rendered preview](/v/0.4.4/ui-library/components/checkbox/_previews/variants-and-sizes/)

````citry
from typing import Any, NamedTuple

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxVariantView(NamedTuple):
    value: str
    title: str


class CheckboxVariantsAndSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="checkbox-matrix" aria-label="Checkbox variants and sizes">
        <c-for each="variant in variants">
          <article>
            <h3>{{ variant.title }}</h3>
            <c-for each="size in sizes">
              <c-CCheckbox
                c-variant="variant.value"
                c-size="size"
                checked
              >
                {{ size }} preserved specimen
              </c-CCheckbox>
            </c-for>
            <c-CCheckbox c-variant="variant.value" indeterminate>
              Partly cataloged collection
            </c-CCheckbox>
            <c-CCheckbox c-variant="variant.value" disabled checked>
              Locked archive record
            </c-CCheckbox>
            <c-CCheckbox c-variant="variant.value" invalid>
              Provenance needs review
            </c-CCheckbox>
          </article>
        </c-for>
      </section>
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "variants": (
                CheckboxVariantView("solid", "Solid"),
                CheckboxVariantView("outline", "Outline"),
            ),
            "sizes": ("sm", "md", "lg"),
        }

    css = """
      :where(.checkbox-matrix) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-matrix article) {
        display: grid;
        align-content: start;
        gap: 0.8rem;
        padding: 1rem;
        border: 1px solid light-dark(#c3d5c0, #405743);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.checkbox-matrix h3) {
        margin: 0 0 0.2rem;
      }
    """


preview = CheckboxVariantsAndSizes()

preview  # noqa: B018
````


## Customize the theme

Override public variables on an ancestor or one Checkbox. Use stable part
selectors for targeted rules.


### Theme two botanical checklists

[Open the rendered preview](/v/0.4.4/ui-library/components/checkbox/_previews/theme-customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxThemeCustomization(Component):
    template = """
      <section class="checkbox-themes">
        <article class="checkbox-themes__conservatory">
          <p>Sunlit conservatory</p>
          <c-CCheckbox checked>
            Mist the cloud-forest ferns
          </c-CCheckbox>
          <c-CCheckbox variant="outline">
            Rotate the orchid trays
          </c-CCheckbox>
        </article>
        <article class="checkbox-themes__night" style="color-scheme: dark">
          <p>Moonlit field station</p>
          <c-CCheckbox checked>
            Log nocturnal flower opening
          </c-CCheckbox>
          <c-CCheckbox indeterminate variant="outline">
            Review moth-pollination images
          </c-CCheckbox>
        </article>
      </section>
    """

    css = """
      :where(.checkbox-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 52rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-themes article) {
        display: grid;
        align-content: start;
        gap: 0.9rem;
        padding: 1.1rem;
        border-radius: 1rem;
      }

      :where(.checkbox-themes article > p) {
        margin: 0;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.checkbox-themes__conservatory) {
        --cui-checkbox-active-color: #24734a;
        --cui-checkbox-focus-color: #4b9b69;
        --cui-checkbox-radius: 0.45rem;

        border: 1px solid #a9cbb3;
        background: #f3fbf4;
        color: #173c25;
      }

      :where(.checkbox-themes__night) {
        --cui-checkbox-active-color: #c4a7ff;
        --cui-checkbox-indicator-color: #22173d;
        --cui-checkbox-focus-color: #e2d5ff;
        --cui-checkbox-description-color: #cbbde7;

        border: 1px solid #584873;
        background: #191426;
        color: #f2ecff;
      }

      :where(.checkbox-themes__night [data-citry-ui-part="input"]) {
        border-width: 2px;
      }
    """


preview = CheckboxThemeCustomization()

preview  # noqa: B018
````


`class_`, `style`, and `attrs` target the neutral root. `input_attrs` targets
the native input. Unlayered consumer CSS overrides the low-specificity Citry
UI defaults; named layers follow the site-wide layer-order contract.

`data-checked` and `data-indeterminate` are public runtime mirrors. No-runtime
checked styling uses native `:checked`, so it stays accurate without static
mirror attributes.

## Accessibility and trust

The native input owns role, keyboard behavior, focus, checkedness, required
validity, and mixed accessibility state. Checkbox does not author
`aria-checked`, simulate read-only, or add a focus proxy.

The visible label is an explicit `<label for="...">`. The description is its
sibling and is linked with `aria-describedby`, so supporting text does not also
enter the accessible name.

Direct string inputs render as plain text even when supplied through a trusted
string subclass. `attrs`, `input_attrs`, `class_`, and `style` remain trusted
authoring surfaces for unowned attributes. Checkbox rejects directives and
attributes that could replace its native input, label relationship, semantics,
state ownership, runtime markers, or accessibility exposure.

## API reference

### Inputs

#### CCheckbox server inputs

Server inputs are passed in a template through `<c-CCheckbox ... />` or in Python through
`CCheckbox(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="checkbox-input-ccheckbox-server-inputs-name"></span>`name` | `non-empty str | None` | `None` | Sets the native submitted name; an unnamed Checkbox contributes no `FormData` entry. |
| <span id="checkbox-input-ccheckbox-server-inputs-value"></span>`value` | `str` | `"on"` | Sets the token submitted while checked; newline spelling is canonicalized and U+0000 is rejected. |
| <span id="checkbox-input-ccheckbox-server-inputs-id"></span>`id` | `str | None` | generated | Uses the Field control ID when composed, otherwise sets or generates native identity and label association. |
| <span id="checkbox-input-ccheckbox-server-inputs-checked"></span>`checked` | `bool` | `False` | Sets native default and initial checkedness plus the reset destination. |
| <span id="checkbox-input-ccheckbox-server-inputs-indeterminate"></span>`indeterminate` | `bool` | `False` | Seeds runtime-enhanced native mixed state; server-only HTML remains a two-state Checkbox. |
| <span id="checkbox-input-ccheckbox-server-inputs-required"></span>`required` | `bool | None` | `None` | Sets native required state when standalone; omit it inside `CField`, which owns the state. |
| <span id="checkbox-input-ccheckbox-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Sets local disabled state when standalone; disabled `CForm` always wins. |
| <span id="checkbox-input-ccheckbox-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Sets application invalid presentation when standalone; omit it inside `CField`. |
| <span id="checkbox-input-ccheckbox-server-inputs-variant"></span>`variant` | `"solid" | "outline"` ([`CCheckboxVariant`](#checkbox-interface-checkbox-variant)) | `"solid"` | Selects filled or outlined checked and mixed presentation. |
| <span id="checkbox-input-ccheckbox-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CCheckboxSize`](#checkbox-interface-checkbox-size)) | `"md"` | Selects control geometry and associated text scale. |
| <span id="checkbox-input-ccheckbox-server-inputs-label-pos"></span>`label_pos` | `"start" | "end"` ([`CCheckboxLabelPos`](#checkbox-interface-checkbox-label-pos)) | `"end"` | Places authored label and description at the logical start or end of the control. |
| <span id="checkbox-input-ccheckbox-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#checkbox-interface-checkbox-class-value)) | `None` | Adds neutral-root classes and merges them with `attrs`. |
| <span id="checkbox-input-ccheckbox-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#checkbox-interface-checkbox-style-value)) | `None` | Adds neutral-root inline styles and merges them with `attrs`. |
| <span id="checkbox-input-ccheckbox-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned attributes to the neutral root. Structural ownership directives, `for`, `role`, `tabindex`, `contenteditable`, and `aria-hidden` are rejected. |
| <span id="checkbox-input-ccheckbox-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted unowned attributes to the native input, including static Form ownership and merged ARIA IDREFs. Label-free standalone usage requires one static ARIA name. |

</div>

#### CCheckbox client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CCheckbox />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 14rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="checkbox-input-ccheckbox-client-inputs-checked"></span>`checked` | `boolean` | Releases control and preserves current native checkedness. | Controls current checkedness after native input and change handlers settle. |
| <span id="checkbox-input-ccheckbox-client-inputs-indeterminate"></span>`indeterminate` | `boolean` | Releases control and preserves current native indeterminateness. | Controls the native mixed property and its runtime root reflection. |
| <span id="checkbox-input-ccheckbox-client-inputs-value"></span>`value` | `string` | Uses the private server fallback. | Controls the native submitted token; omission or invalid supply reapplies the server value. |
| <span id="checkbox-input-ccheckbox-client-inputs-required"></span>`required` | `boolean` | Uses the server or Field value. | Controls native required state when standalone; `CField` owns it when composed. |
| <span id="checkbox-input-ccheckbox-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the local server or Field value. | Controls local disabled state when standalone; disabled `CForm` always wins. |
| <span id="checkbox-input-ccheckbox-client-inputs-invalid"></span>`invalid` | `boolean` | Uses the server or Field value. | Controls application invalid presentation; native invalidity still combines with it. |
| <span id="checkbox-input-ccheckbox-client-inputs-variant"></span>`variant` | `"solid" | "outline"` ([`CCheckboxVariant`](#checkbox-interface-checkbox-variant)) | Uses the server input. | Controls presentation. |
| <span id="checkbox-input-ccheckbox-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CCheckboxSize`](#checkbox-interface-checkbox-size)) | Uses the server input. | Controls geometry and associated text size. |
| <span id="checkbox-input-ccheckbox-client-inputs-label-pos"></span>`label_pos` | `"start" | "end"` ([`CCheckboxLabelPos`](#checkbox-interface-checkbox-label-pos)) | Uses the server input. | Controls logical label placement. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CCheckbox slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="checkbox-slot-ccheckbox-slots-default"></span>`default` | no | `{}` ([`CCheckboxDefaultSlotData`](#checkbox-interface-checkbox-default-slot-data)) | Required unless a static ARIA name or `CField` label owns naming. |
| <span id="checkbox-slot-ccheckbox-slots-description"></span>`description` | no | `{}` ([`CCheckboxDescriptionSlotData`](#checkbox-interface-checkbox-description-slot-data)) | No description element. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CCheckbox CSS variables

Apply these variables to `CCheckbox` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-background"></span>`--cui-checkbox-background` | `color` | Unchecked control surface. | `Canvas` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-foreground"></span>`--cui-checkbox-foreground` | `color` | Label foreground. | `CanvasText` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-border-color"></span>`--cui-checkbox-border-color` | `color` | Resting unchecked border. | `Subtle CanvasText mix.` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-hover-border-color"></span>`--cui-checkbox-hover-border-color` | `color` | Enabled hover border. | `Stronger CanvasText mix.` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-active-color"></span>`--cui-checkbox-active-color` | `color` | Checked and mixed fill or outline. | `Scheme-aware blue.` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-indicator-color"></span>`--cui-checkbox-indicator-color` | `color` | Check and mixed indicator. | `Scheme-aware high-contrast color; active color in outline variant.` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-focus-color"></span>`--cui-checkbox-focus-color` | `color` | Focus-visible outline. | `Highlight` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-invalid-color"></span>`--cui-checkbox-invalid-color` | `color` | Invalid border accent. | `Scheme-aware danger color.` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-disabled-opacity"></span>`--cui-checkbox-disabled-opacity` | `number` | Disabled root opacity. | `0.55` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-control-size"></span>`--cui-checkbox-control-size` | `length` | Native control inline and block size. | `Size-derived length.` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-radius"></span>`--cui-checkbox-radius` | `length` | Control corner radius. | `0.3rem` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-gap"></span>`--cui-checkbox-gap` | `length` | Control-to-text gap. | `Size-derived length.` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-description-color"></span>`--cui-checkbox-description-color` | `color` | Description foreground. | `Muted CanvasText mix.` |
| <span id="checkbox-css-ccheckbox-css-variables-cui-checkbox-description-gap"></span>`--cui-checkbox-description-gap` | `length` | Label-to-description gap. | `0.2rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CCheckbox attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="checkbox-attribute-ccheckbox-attributes-data-checked"></span>`data-checked` | Neutral root | `present | absent` | Runtime mirror of current native checkedness; static HTML does not emit it. |
| <span id="checkbox-attribute-ccheckbox-attributes-data-indeterminate"></span>`data-indeterminate` | Neutral root | `present | absent` | Runtime mirror of current native indeterminateness; static HTML does not emit it. |
| <span id="checkbox-attribute-ccheckbox-attributes-data-required"></span>`data-required` | Neutral root | `present | absent` | Mirrors effective required state. |
| <span id="checkbox-attribute-ccheckbox-attributes-data-disabled"></span>`data-disabled` | Neutral root | `present | absent` | Mirrors effective disabled state. |
| <span id="checkbox-attribute-ccheckbox-attributes-data-invalid"></span>`data-invalid` | Neutral root | `present | absent` | Mirrors combined application and native invalid state. |
| <span id="checkbox-attribute-ccheckbox-attributes-data-variant"></span>`data-variant` | Neutral root | `"solid" | "outline"` | Mirrors effective presentation variant. |
| <span id="checkbox-attribute-ccheckbox-attributes-data-size"></span>`data-size` | Neutral root | `"sm" | "md" | "lg"` | Mirrors effective size. |
| <span id="checkbox-attribute-ccheckbox-attributes-data-label-pos"></span>`data-label-pos` | Neutral root | `"start" | "end"` | Mirrors logical label placement. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CCheckbox selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="checkbox-selector-ccheckbox-selectors-checkbox"></span>`[data-citry-ui-part="checkbox"]` | Neutral root | Stable root, layout hook, and `attrs` destination. |
| <span id="checkbox-selector-ccheckbox-selectors-input"></span>`[data-citry-ui-part="input"]` | Native checkbox input | Native state, focus, indicator, and `input_attrs` destination. |
| <span id="checkbox-selector-ccheckbox-selectors-label"></span>`[data-citry-ui-part="label"]` | Internal label | Visible default-slot label and activation target. |
| <span id="checkbox-selector-ccheckbox-selectors-description"></span>`[data-citry-ui-part="description"]` | Description span | Optional described-by content outside the accessible name. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="checkbox-interface-checkbox-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="checkbox-interface-checkbox-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="checkbox-interface-checkbox-variant"></span>`CCheckboxVariant` | `Literal["solid", "outline"]` |
| <span id="checkbox-interface-checkbox-size"></span>`CCheckboxSize` | `Literal["sm", "md", "lg"]` |
| <span id="checkbox-interface-checkbox-label-pos"></span>`CCheckboxLabelPos` | `Literal["start", "end"]` |

</div>

<span id="checkbox-interface-checkbox-default-slot-data"></span>

#### `CCheckboxDefaultSlotData`

Empty dataclass: `{}`.

<span id="checkbox-interface-checkbox-description-slot-data"></span>

#### `CCheckboxDescriptionSlotData`

Empty dataclass: `{}`.

### Translation keys

-