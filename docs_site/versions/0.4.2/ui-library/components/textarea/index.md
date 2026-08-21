---
title: Textarea
url: https://citry.dev/v/0.4.2/ui-library/components/textarea/
description: "Enter multiline plain text with native editing, forms, validation, and optional browser control."
---
# Textarea

Use `CTextarea` for notes, descriptions, reports, and other multiline plain
text. It renders one native multiline text control, so editing, selection,
validation, submission, reset, spelling, and mobile keyboards keep their
browser behavior.

## Textarea at a glance


### Textarea at a glance

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/at-a-glance/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "canopy_note": "Beech leaves moving in a light western wind.\nA woodpecker crossed the clearing twice.",
        }

    template = """
      <section class="forest-glance" aria-label="Woodland field journal">
        <c-CField>
          <c-fill name="label">Canopy observation</c-fill>
          <c-fill name="default">
            <c-CTextarea
              name="canopy"
              c-value="canopy_note"
              rows="5"
            />
          </c-fill>
          <c-fill name="description">Record light, weather, and visible wildlife.</c-fill>
        </c-CField>

        <div class="forest-glance__night" style="color-scheme: dark">
          <c-CField required invalid>
            <c-fill name="label">Nocturnal call</c-fill>
            <c-fill name="default">
              <c-CTextarea name="night_call" placeholder="Describe the sound" />
            </c-fill>
            <c-fill name="error">Add enough detail to identify the call.</c-fill>
          </c-CField>
        </div>
      </section>
    """

    css = """
      :where(.forest-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 54rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-glance > *) {
        padding: 1rem;
        border: 1px solid light-dark(#a9c6ae, #43634a);
        border-radius: 0.875rem;
        background: light-dark(#f4faf4, #132319);
      }

      :where(.forest-glance__night) {
        --cui-textarea-background: #17251c;
        --cui-textarea-border-color: #5f8067;
        --cui-textarea-focus-color: #91d39d;
      }
    """


preview = TextareaAtAGlance()

preview  # noqa: B018
````


## Compose a labelled control

Put Textarea inside `CField` when it needs a label, description, or error.
Field owns those relationships and the composed required, disabled, read-only,
and invalid states.


### Compose labelled and standalone Textareas

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/compose-textarea/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ComposeTextarea(Component):
    template = """
      <section class="forest-compose">
        <c-CField>
          <c-fill name="label">Trail condition</c-fill>
          <c-fill name="default">
            <c-CTextarea name="trail_condition" placeholder="Roots, mud, fallen limbs…" />
          </c-fill>
          <c-fill name="description">Shared with the next ranger patrol.</c-fill>
        </c-CField>

        <div>
          <label for="quick-sketch">Quick sketch notes</label>
          <c-CTextarea id="quick-sketch" name="quick_sketch" rows="3" />
        </div>
      </section>
    """

    css = """
      :where(.forest-compose) {
        display: grid;
        gap: 1.25rem;
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-compose > div) {
        display: grid;
        gap: 0.5rem;
      }

      :where(.forest-compose > div > label) {
        font-weight: 600;
      }
    """


preview = ComposeTextarea()

preview  # noqa: B018
````


Outside `CField`, provide a native label or an accessible name yourself:


```citry-html
<label for="quick-note">Quick note</label>
<c-CTextarea id="quick-note" name="quick_note" />
```


`CTextarea` has no slots or child content. Pass initial text with `value`.

## Choose rows and resizing

`rows` sets the initial visible line count. The default `resize="vertical"`
keeps the control within its container. `horizontal` and `both` deliberately
allow the browser resize handle to exceed a narrow container.


### Choose rows and resize behavior

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/rows-and-resize/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RowsAndResize(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"survey_note": "Fern cover: dense\nSeedlings: abundant\nGround moisture: high"}

    template = """
      <section
        class="forest-resize"
        x-data
        x-init="Alpine.store('forestTextareaResize', {rows: 4, resize: 'vertical'})"
        @citry-ui-preview-controls.window="
          if ($event.detail.rows !== undefined) {
            $store.forestTextareaResize.rows = Number($event.detail.rows);
          }
          if ($event.detail.resize !== undefined) {
            $store.forestTextareaResize.resize = $event.detail.resize;
          }
        "
      >
        <c-CField>
          <c-fill name="label">Understory survey</c-fill>
          <c-fill name="default">
            <c-CTextarea
              name="understory"
              c-value="survey_note"
              $c-props="{
                rows: $store.forestTextareaResize.rows,
                resize: $store.forestTextareaResize.resize,
              }"
            />
          </c-fill>
          <c-fill name="description">
            Horizontal and both-direction resizing may exceed this bounded stage.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.forest-resize) {
        max-width: 34rem;
        overflow: auto;
        padding: 1rem;
        border: 1px dashed light-dark(#789f7f, #698d70);
        border-radius: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview_controls = (
    {
        "name": "rows",
        "label": "Visible rows",
        "type": "select",
        "default": "4",
        "options": (("2", "2"), ("4", "4"), ("7", "7")),
    },
    {
        "name": "resize",
        "label": "Resize",
        "type": "select",
        "default": "vertical",
        "options": (
            ("none", "None"),
            ("vertical", "Vertical"),
            ("horizontal", "Horizontal"),
            ("both", "Both"),
        ),
    },
)

preview = RowsAndResize()

preview  # noqa: B018
````


## Choose a variant

`outline`, `filled`, and `plain` change visual emphasis without changing the
native editing or form contract.


### Compare Textarea variants

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/variants/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaVariants(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"variants": ("outline", "filled", "plain")}

    template = """
      <section class="forest-variants">
        <c-for each="variant in variants">
          <c-CField>
            <c-fill name="label">{{ variant.title() }} field note</c-fill>
            <c-fill name="default">
              <c-CTextarea
                c-name="variant"
                c-variant="variant"
                value="Bracket fungi found on the fallen birch."
                rows="3"
              />
            </c-fill>
          </c-CField>
        </c-for>
      </section>
    """

    css = """
      :where(.forest-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = TextareaVariants()

preview  # noqa: B018
````


## Choose a size

`sm`, `md`, and `lg` adjust padding, font size, and line geometry. They do not
change `rows` or truncate text.


### Compare Textarea sizes

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/sizes/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"sizes": ("sm", "md", "lg")}

    template = """
      <section class="forest-sizes">
        <c-for each="size in sizes">
          <c-CField>
            <c-fill name="label">{{ size.upper() }} specimen note</c-fill>
            <c-fill name="default">
              <c-CTextarea
                c-name="size"
                c-size="size"
                value="Three fox prints beside the stream crossing."
                rows="3"
              />
            </c-fill>
          </c-CField>
        </c-for>
      </section>
    """

    css = """
      :where(.forest-sizes) {
        display: grid;
        gap: 1rem;
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = TextareaSizes()

preview  # noqa: B018
````


## Use Field and Form states

Required, disabled, read-only, and invalid controls retain their native
differences. Read-only text remains focusable and submitted. Disabled text is
not submitted.


### Compare Textarea states

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/field-states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaFieldStates(Component):
    template = """
      <section class="forest-states">
        <c-CField required>
          <c-fill name="label">Required survey</c-fill>
          <c-fill name="default"><c-CTextarea name="required_survey" /></c-fill>
        </c-CField>
        <c-CField disabled>
          <c-fill name="label">Closed plot</c-fill>
          <c-fill name="default"><c-CTextarea name="closed_plot" value="Access suspended." /></c-fill>
        </c-CField>
        <c-CField readonly>
          <c-fill name="label">Archived note</c-fill>
          <c-fill name="default"><c-CTextarea name="archived" value="Old-growth marker confirmed." /></c-fill>
        </c-CField>
        <c-CField invalid>
          <c-fill name="label">Unclear location</c-fill>
          <c-fill name="default"><c-CTextarea name="location" value="Near the large tree" /></c-fill>
          <c-fill name="error">Name a trail marker or grid reference.</c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.forest-states) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = TextareaFieldStates()

preview  # noqa: B018
````


## Validate, submit, and reset

Pass common native constraints such as `minlength`, `maxlength`, and
`spellcheck` through `attrs`. Native length validity follows the browser's
user-edit rules: initial or script-controlled text is not guaranteed to set
`tooShort` or `tooLong`, and browsers usually enforce `maxlength` while typing.


### Validate and reset a habitat report

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/validation-and-forms/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaValidation(Component):
    template = """
      <section class="forest-report" x-data="{submitted: ''}">
        <c-CForm @submit.prevent="submitted = new FormData($event.target).get('habitat')">
          <c-CField required>
            <c-fill name="label">Habitat report</c-fill>
            <c-fill name="default">
              <c-CTextarea
                name="habitat"
                value="Moss"
                c-attrs="{'minlength': 12, 'maxlength': 180, 'spellcheck': True}"
              />
            </c-fill>
            <c-fill name="description">Use 12 to 180 characters.</c-fill>
            <c-fill name="error">Add a fuller habitat description.</c-fill>
          </c-CField>
          <div class="forest-report__actions">
            <c-CButton type="submit">Save report</c-CButton>
            <c-CButton type="reset" variant="outline">Reset</c-CButton>
          </div>
          <output x-show="submitted" x-text="submitted"></output>
        </c-CForm>
      </section>
    """

    css = """
      :where(.forest-report) {
        display: grid;
        gap: 1rem;
        max-width: 40rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-report__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.forest-report output) {
        white-space: pre-wrap;
      }
    """


preview = TextareaValidation()

preview  # noqa: B018
````


## Control the browser value

Supply client `value` through `$c-props` to control current text. Mirror the
native `input` event to accept edits. Omit the prop to release control without
rewriting the current value.


### Control and release a draft

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/controlled-values/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledTextarea(Component):
    template = """
      <section
        class="forest-controlled"
        x-data
        x-init="Alpine.store('forestTextareaDraft', {
          controlled: true,
          draft: 'A tawny owl called from the eastern ridge.',
        })"
      >
        <c-CField>
          <c-fill name="label">Patrol draft</c-fill>
          <c-fill name="default">
            <c-CTextarea
              name="patrol_draft"
              $c-props="{
                value: $store.forestTextareaDraft.controlled
                  ? $store.forestTextareaDraft.draft
                  : undefined,
              }"
              @input="$store.forestTextareaDraft.draft = $event.target.value"
            />
          </c-fill>
          <c-fill name="description">
            <span
              x-text="$store.forestTextareaDraft.controlled
                ? 'Application controlled'
                : 'Browser controlled'"
            ></span>
          </c-fill>
        </c-CField>
        <div class="forest-controlled__actions">
          <c-CButton
            type="button"
            size="sm"
            @click="$store.forestTextareaDraft.controlled = false"
          >
            Release
          </c-CButton>
          <c-CButton
            type="button"
            size="sm"
            variant="outline"
            @click="
              $store.forestTextareaDraft.draft = 'Fresh tracks followed the creek north.';
              $store.forestTextareaDraft.controlled = true;
            "
          >
            Replace draft
          </c-CButton>
        </div>
      </section>
    """

    css = """
      :where(.forest-controlled) {
        display: grid;
        gap: 1rem;
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-controlled__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ControlledTextarea()

preview  # noqa: B018
````


Citry compares before assigning, waits for composition and consumer updates,
and preserves the caret when your handler mirrors the native value. Listen to
native `@input`, `@change`, focus, invalid, and composition events directly;
Textarea adds no competing value-change callback.

## Keep native text and wrapping

Server and client values normalize line endings to LF. Leading and blank lines
remain text, and strings that look like HTML cannot create elements.
`wrap="hard"` requires `cols` and may add line breaks to submitted data;
`soft` does not add wrapping breaks.


### Use native multiline text and wrapping

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/native-text/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeTextareaText(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "preserved_text": "\nFirst line after a deliberate blank.\n\nThird observation.",
            "transect_text": ("A long plain-text observation wraps visually without becoming markup: <fern> & moss."),
        }

    template = """
      <section class="forest-native">
        <c-CField>
          <c-fill name="label">Preserved blank lines</c-fill>
          <c-fill name="default">
            <c-CTextarea name="preserved" c-value="preserved_text" rows="6" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">Hard-wrapped transect log</c-fill>
          <c-fill name="default">
            <c-CTextarea
              name="transect"
              wrap="hard"
              cols="32"
              c-value="transect_text"
              c-attrs="{'spellcheck': True, 'enterkeyhint': 'enter'}"
            />
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.forest-native) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NativeTextareaText()

preview  # noqa: B018
````


## Write in either direction

Use native `dir` and `dirname` attributes for writing direction. Logical
padding and width work in LTR and RTL; long content scrolls inside the control.


### Write long LTR and RTL notes

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/direction-and-content/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaDirection(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "english_note": (
                "A very-long-unbroken-specimen-code-FOREST-TRANSECT-NORTH-204 remained readable inside the control."
            ),
            "arabic_note": "كانت أوراق البلوط تتحرك مع الريح الخفيفة قرب الجدول.",
        }

    template = """
      <section class="forest-direction">
        <c-CField>
          <c-fill name="label">English trail note</c-fill>
          <c-fill name="default">
            <c-CTextarea name="english" c-value="english_note" c-attrs="{'dir': 'ltr'}" />
          </c-fill>
        </c-CField>
        <div dir="rtl">
          <c-CField>
            <c-fill name="label">ملاحظة الغابة</c-fill>
            <c-fill name="default">
              <c-CTextarea
                name="arabic"
                c-value="arabic_note"
                c-attrs="{'dir': 'rtl', 'dirname': 'arabic.dir'}"
              />
            </c-fill>
          </c-CField>
        </div>
      </section>
    """

    css = """
      :where(.forest-direction) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-direction > *) {
        min-width: 0;
      }
    """


preview = TextareaDirection()

preview  # noqa: B018
````


## Customize the theme

Override public variables on an ancestor or one Textarea. Use the stable part
selector for targeted rules.


### Theme two field journals

[Open the rendered preview](/v/0.4.2/ui-library/components/textarea/_previews/theme-customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaThemes(Component):
    template = """
      <section class="forest-themes">
        <div class="forest-themes__fern">
          <c-CField>
            <c-fill name="label">Fern journal</c-fill>
            <c-fill name="default"><c-CTextarea value="New fronds opened after rain." /></c-fill>
          </c-CField>
        </div>
        <div class="forest-themes__charcoal" style="color-scheme: dark">
          <c-CField>
            <c-fill name="label">Charcoal journal</c-fill>
            <c-fill name="default"><c-CTextarea value="Embers cooled before dawn patrol." /></c-fill>
          </c-CField>
        </div>
      </section>
    """

    css = """
      :where(.forest-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-themes > div) {
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.forest-themes__fern) {
        --cui-textarea-background: #f7fff7;
        --cui-textarea-foreground: #153d24;
        --cui-textarea-border-color: #739b7d;
        --cui-textarea-hover-border-color: #315f3c;
        --cui-textarea-focus-color: #16713a;
        --cui-textarea-invalid-border-color: #b42318;
        --cui-textarea-disabled-background: #e1eee3;
        --cui-textarea-placeholder-color: #58715e;
        --cui-textarea-radius: 1rem;
        --cui-textarea-inline-padding: 1rem;
        --cui-textarea-block-padding: 0.875rem;
        --cui-textarea-font-size: 1rem;
        --cui-textarea-line-height: 1.6;
        background: #e2f0e4;
      }

      :where(.forest-themes__charcoal) {
        --cui-textarea-background: #162019;
        --cui-textarea-foreground: #e6f2e9;
        --cui-textarea-border-color: #66806d;
        --cui-textarea-hover-border-color: #9abc9f;
        --cui-textarea-focus-color: #8de49e;
        --cui-textarea-invalid-border-color: #ff8a80;
        --cui-textarea-disabled-background: #242d26;
        --cui-textarea-placeholder-color: #a7b8ab;
        --cui-textarea-radius: 0.25rem;
        --cui-textarea-inline-padding: 0.875rem;
        --cui-textarea-block-padding: 0.75rem;
        --cui-textarea-font-size: 1.025rem;
        --cui-textarea-line-height: 1.55;
        background: #0c120e;
      }

      :where(.forest-themes [data-citry-ui-part="textarea"]:focus-visible) {
        outline-style: double;
      }
    """


preview = TextareaThemes()

preview  # noqa: B018
````


`class_` and `style` target the native root. Unlayered consumer CSS overrides
the low-specificity defaults; named layers follow the site-wide Citry UI layer
ordering contract.

## Know the fixed-height boundary

Textarea does not auto-grow, count characters, add adornments, or render rich
text. Those jobs need measurement, announcement, or editor contracts beyond a
native fixed-row control. Manual CSS resize remains observer-free and works
without JavaScript.

## Accessibility and trust

Keep a visible label even when placeholder text is present. Textarea adds no
role, focus proxy, or keyboard handler. `value`, name, ID, placeholder,
autocomplete, and inputmode are always rendered as plain text, including
trusted-string subclasses. `attrs`, `class_`, and `style` remain trusted code
surfaces for native, ARIA, data, and Alpine attributes.

## API reference

### Inputs

#### CTextarea server inputs

Server inputs are passed in a template through `<c-CTextarea ... />` or in Python through
`CTextarea(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="textarea-input-ctextarea-server-inputs-name"></span>`name` | `non-empty str | None` | `None` | Sets the native submitted name; an unnamed Textarea contributes no `FormData` entry. |
| <span id="textarea-input-ctextarea-server-inputs-id"></span>`id` | `str | None` | generated | Uses the Field control ID when composed, otherwise sets or generates native identity. |
| <span id="textarea-input-ctextarea-server-inputs-value"></span>`value` | `str | None` | `None` | Sets LF-normalized, escaped native child text as the initial value and reset default. |
| <span id="textarea-input-ctextarea-server-inputs-rows"></span>`rows` | `positive int` | `4` | Sets the initial visible line count. |
| <span id="textarea-input-ctextarea-server-inputs-cols"></span>`cols` | `positive int | None` | `None` | Sets the native preferred character width and is required by hard wrapping; CSS still owns rendered inline size. |
| <span id="textarea-input-ctextarea-server-inputs-wrap"></span>`wrap` | `"soft" | "hard"` ([`CTextareaWrap`](#textarea-interface-input-type-aliases-ctextarea-wrap)) | `"soft"` | Selects native submission wrapping; hard requires cols. |
| <span id="textarea-input-ctextarea-server-inputs-required"></span>`required` | `bool | None` | `None` | Sets native required state when standalone; omit it inside `CField`, which owns the state. |
| <span id="textarea-input-ctextarea-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Sets local disabled state when standalone; disabled `CForm` always wins. |
| <span id="textarea-input-ctextarea-server-inputs-readonly"></span>`readonly` | `bool | None` | Inherits `CForm` when standalone. | Sets read-only state when standalone; omit it inside `CField`. |
| <span id="textarea-input-ctextarea-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Sets application invalid state when standalone; omit it inside `CField`. |
| <span id="textarea-input-ctextarea-server-inputs-autocomplete"></span>`autocomplete` | `str | None` | `None` | Sets the native autofill hint. |
| <span id="textarea-input-ctextarea-server-inputs-inputmode"></span>`inputmode` | `str | None` | `None` | Sets the native virtual-keyboard hint. |
| <span id="textarea-input-ctextarea-server-inputs-placeholder"></span>`placeholder` | `str | None` | `None` | Sets short hint text; it does not replace a label. |
| <span id="textarea-input-ctextarea-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CTextareaVariant`](#textarea-interface-input-type-aliases-ctextarea-variant)) | `"outline"` | Selects presentation. |
| <span id="textarea-input-ctextarea-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CTextareaSize`](#textarea-interface-input-type-aliases-ctextarea-size)) | `"md"` | Selects padding, text size, and line geometry. |
| <span id="textarea-input-ctextarea-server-inputs-resize"></span>`resize` | `"none" | "vertical" | "horizontal" | "both"` ([`CTextareaResize`](#textarea-interface-input-type-aliases-ctextarea-resize)) | `"vertical"` | Selects the native CSS resize policy; horizontal and both may overflow a narrow container. |
| <span id="textarea-input-ctextarea-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#textarea-interface-input-type-aliases-class-value)) | `None` | Adds native-root classes and merges them with `attrs`. |
| <span id="textarea-input-ctextarea-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#textarea-interface-input-type-aliases-style-value)) | `None` | Adds native-root inline styles and merges them with `attrs`. |
| <span id="textarea-input-ctextarea-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds native constraints, ARIA, data, and trusted Alpine attributes not owned by explicit inputs. |

</div>

#### CTextarea client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTextarea />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="textarea-input-ctextarea-client-inputs-value"></span>`value` | `string` | Releases control and preserves the current native value. | Controls the LF-normalized native current value while supplied; an invalid value retains the prior valid controlled value. |
| <span id="textarea-input-ctextarea-client-inputs-rows"></span>`rows` | `positive integer` | Uses the server input. | Controls the native rows property; invalid values use the server fallback. |
| <span id="textarea-input-ctextarea-client-inputs-required"></span>`required` | `boolean` | Uses the server value. | Controls required state when standalone; `CField` owns it when composed. |
| <span id="textarea-input-ctextarea-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server value. | Controls local disabled state when standalone; disabled `CForm` always wins. |
| <span id="textarea-input-ctextarea-client-inputs-readonly"></span>`readonly` | `boolean` | Uses the server or reactive Form value. | Controls read-only state when standalone; `CField` owns it when composed. |
| <span id="textarea-input-ctextarea-client-inputs-invalid"></span>`invalid` | `boolean` | Uses the server value. | Controls application invalid state when standalone; native invalidity still combines with it. |
| <span id="textarea-input-ctextarea-client-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CTextareaVariant`](#textarea-interface-input-type-aliases-ctextarea-variant)) | Uses the server input. | Controls presentation. |
| <span id="textarea-input-ctextarea-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CTextareaSize`](#textarea-interface-input-type-aliases-ctextarea-size)) | Uses the server input. | Controls padding and text geometry. |
| <span id="textarea-input-ctextarea-client-inputs-resize"></span>`resize` | `"none" | "vertical" | "horizontal" | "both"` ([`CTextareaResize`](#textarea-interface-input-type-aliases-ctextarea-resize)) | Uses the server input. | Controls the native CSS resize policy. |

</div>

### Slots

-

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTextarea CSS variables

Apply these variables to `CTextarea` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-background"></span>`--cui-textarea-background` | `color` | Native root background. | `Canvas, variant adjusted` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-foreground"></span>`--cui-textarea-foreground` | `color` | Entered text. | `CanvasText` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-border-color"></span>`--cui-textarea-border-color` | `color` | Resting border. | `Subtle CanvasText mix, variant adjusted` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-hover-border-color"></span>`--cui-textarea-hover-border-color` | `color` | Hover border. | `Stronger CanvasText mix.` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-focus-color"></span>`--cui-textarea-focus-color` | `color` | Focus outline and border. | `Highlight` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-invalid-border-color"></span>`--cui-textarea-invalid-border-color` | `color` | Invalid border. | `Scheme-aware negative color.` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-disabled-background"></span>`--cui-textarea-disabled-background` | `color` | Disabled background. | `Subtle CanvasText/Canvas mix.` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-placeholder-color"></span>`--cui-textarea-placeholder-color` | `color` | Placeholder text. | `Muted CanvasText mix.` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-radius"></span>`--cui-textarea-radius` | `length` | Corner radius. | `0.5rem; 0 for plain` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-inline-padding"></span>`--cui-textarea-inline-padding` | `length` | Logical inline padding. | `Size-derived length.` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-block-padding"></span>`--cui-textarea-block-padding` | `length` | Logical block padding. | `Size-derived length.` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-font-size"></span>`--cui-textarea-font-size` | `length` | Editing text size. | `Size-derived length.` |
| <span id="textarea-css-ctextarea-css-variables-cui-textarea-line-height"></span>`--cui-textarea-line-height` | `number | length` | Editing line height and row geometry. | `1.5` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTextarea attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="textarea-attribute-ctextarea-attributes-data-required"></span>`data-required` | Native Textarea | `present | absent` | Mirrors effective required state. |
| <span id="textarea-attribute-ctextarea-attributes-data-disabled"></span>`data-disabled` | Native Textarea | `present | absent` | Mirrors effective disabled state. |
| <span id="textarea-attribute-ctextarea-attributes-data-readonly"></span>`data-readonly` | Native Textarea | `present | absent` | Mirrors effective read-only state. |
| <span id="textarea-attribute-ctextarea-attributes-data-invalid"></span>`data-invalid` | Native Textarea | `present | absent` | Mirrors combined application and native invalid state. |
| <span id="textarea-attribute-ctextarea-attributes-data-variant"></span>`data-variant` | Native Textarea | `"outline" | "filled" | "plain"` | Mirrors effective presentation variant. |
| <span id="textarea-attribute-ctextarea-attributes-data-size"></span>`data-size` | Native Textarea | `"sm" | "md" | "lg"` | Mirrors effective visual size. |
| <span id="textarea-attribute-ctextarea-attributes-data-resize"></span>`data-resize` | Native Textarea | `"none" | "vertical" | "horizontal" | "both"` | Mirrors the effective native CSS resize policy. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTextarea selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="textarea-selector-ctextarea-selectors-textarea"></span>`[data-citry-ui-part="textarea"]` | Native Textarea | Stable root, styling hook, and `attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="textarea-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="textarea-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="textarea-interface-input-type-aliases-ctextarea-variant"></span>`CTextareaVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="textarea-interface-input-type-aliases-ctextarea-size"></span>`CTextareaSize` | `Literal["sm", "md", "lg"]` |
| <span id="textarea-interface-input-type-aliases-ctextarea-resize"></span>`CTextareaResize` | `Literal["none", "vertical", "horizontal", "both"]` |
| <span id="textarea-interface-input-type-aliases-ctextarea-wrap"></span>`CTextareaWrap` | `Literal["soft", "hard"]` |

</div>

### Translation keys

-