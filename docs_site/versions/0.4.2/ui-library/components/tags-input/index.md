---
title: TagsInput
url: https://citry.dev/v/0.4.2/ui-library/components/tags-input/
description: "Create and submit an ordered list of free-form text tags."
---
# TagsInput

Use `CTagsInput` when a person creates an ordered list of free-form strings,
such as labels, aliases, search terms, or routing keys. Committed tags and the
unfinished editor draft are separate values.

Use [MultiSelect](/v/0.4.2/ui-library/components/multi-select/) when choices come from
a fixed collection. Suggestions, remote filtering, and create-from-search
belong to a future Combobox rather than this component. Use
[Tag and TagGroup](/v/0.4.2/ui-library/components/tag/) to display tags without an
editor or native Form value.

## Add and submit tags

Press Enter or type a configured delimiter to add one tag. Each committed tag
becomes one selected Option in a native multiple Select, so
`FormData.getAll(name)` returns repeated values in tag order.


```citry-html
<c-CTagsInput
  name="labels"
  c-value="['urgent', 'billing']"
  c-input_attrs="{'aria-label': 'Routing labels'}"
/>
```


Standalone use requires a nonempty static `aria-label` in `input_attrs`.
Compose the component inside `CField` when it needs a visible label,
description, error, required marker, or shared disabled and readonly state.


### Template and Python TagsInput composition

[Open the rendered preview](/v/0.4.2/ui-library/components/tags-input/_previews/basic-tags/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTagsInput

citry.register_library(citry_ui)


class BasicTagsInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "python_tags": CTagsInput(
                name="reviewers",
                value=("ada@example.test", "grace@example.test"),
                variant="filled",
                input_attrs={"aria-label": "Reviewers"},
            )
        }

    template = """
      <section
        class="tags-input-basic"
        x-data="{submitted:'Nothing submitted yet'}"
      >
        <form
          @submit.prevent="
            submitted = JSON.stringify(
              new FormData($event.target).getAll('labels')
            )
          "
        >
          <c-CField required>
            <c-fill name="label">Routing labels</c-fill>
            <c-fill name="description">
              Press Enter or comma to add a label.
            </c-fill>
            <c-fill name="default">
              <c-CTagsInput
                name="labels"
                c-value="['urgent', 'billing']"
              />
            </c-fill>
          </c-CField>
          <button type="submit">Inspect repeated values</button>
        </form>

        <article>
          <h3>Direct Python composition</h3>
          {{ python_tags }}
        </article>

        <output x-text="submitted">Nothing submitted yet</output>
      </section>
    """

    css = """
      :where(.tags-input-basic) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-basic form, .tags-input-basic article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        margin: 0;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.75rem;
      }

      :where(.tags-input-basic h3) {
        margin: 0;
      }

      :where(.tags-input-basic output) {
        grid-column: 1 / -1;
      }
    """


preview = BasicTagsInput()

preview  # noqa: B018
````


## Control committed tags and the draft separately

Client `value` owns the ordered committed tags. Client `inputValue` owns the
raw editor draft. Either axis can be controlled alone, both can be controlled,
or both can remain uncontrolled.

`onValueChange` receives a complete proposed collection. A controlled request
does not update tags or native Form values until the owner supplies that exact
collection. An uncontrolled draft clears only after the related value request
is accepted, so refusing a controlled value does not erase the person's text.


### Control tags and draft ownership

[Open the rendered preview](/v/0.4.2/ui-library/components/tags-input/_previews/controlled-axes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledTagsInputAxes(Component):
    template = """
      <section class="tags-input-controlled">
        <article x-data="{last:'Uncontrolled'}">
          <h3>Uncontrolled tags and draft</h3>
          <c-CTagsInput
            c-value="['alpine']"
            c-input_attrs="{'aria-label':'Uncontrolled labels'}"
            $c-props="{
              onValueChange:(next)=>last=JSON.stringify(next),
            }"
          />
          <output x-text="last">Uncontrolled</output>
        </article>

        <article x-data="{draft:'coastal',last:'Draft owned'}">
          <h3>Controlled draft</h3>
          <c-CTagsInput
            c-value="['alpine']"
            c-input_attrs="{'aria-label':'Draft-owned labels'}"
            $c-props="{
              inputValue:draft,
              onInputValueChange:(next)=>{
                draft=next;
                last=`Draft: ${next}`;
              },
            }"
          />
          <output x-text="last">Draft owned</output>
        </article>

        <article
          x-data="{
            tags:['alpine'],
            accept:false,
            last:'Value request not sent',
          }"
        >
          <h3>Controlled tags, uncontrolled draft</h3>
          <c-CTagsInput
            c-input_attrs="{'aria-label':'Value-owned labels'}"
            $c-props="{
              value:tags,
              onValueChange:(next,detail)=>{
                last=`Requested ${JSON.stringify(next)}`;
                if (accept) tags=next;
              },
            }"
          />
          <label>
            <input type="checkbox" x-model="accept" />
            Accept the next value request
          </label>
          <output x-text="last">Value request not sent</output>
        </article>

        <article
          x-data="{
            tags:['alpine'],
            draft:'harbor',
            last:'Both axes owned',
          }"
        >
          <h3>Controlled tags and draft</h3>
          <c-CTagsInput
            c-input_attrs="{'aria-label':'Fully controlled labels'}"
            $c-props="{
              value:tags,
              inputValue:draft,
              onValueChange:(next,detail)=>{
                tags=next;
                draft=detail.nextInputValue || 'owner note';
                last=`Accepted ${JSON.stringify(next)}`;
              },
              onInputValueChange:(next)=>draft=next,
            }"
          />
          <button type="button" @click="tags=['owner','ordered']">
            Replace tags from the owner
          </button>
          <output x-text="last">Both axes owned</output>
        </article>
      </section>
    """

    css = """
      :where(.tags-input-controlled) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-controlled article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.75rem;
      }

      :where(.tags-input-controlled h3) {
        margin: 0;
      }
    """


preview = ControlledTagsInputAxes()

preview  # noqa: B018
````


Passing `null` or removing a controlled axis releases it to its latest
uncontrolled committed baseline. It does not adopt the last controlled value.

## Keep paste and IME input atomic

Paste text containing a delimiter or newline to add several tags at once. The
component replaces the current editor selection, validates every completed
fragment, and commits the batch in order. The final unterminated fragment
remains the draft.

If any fragment is empty, duplicated, invalid, or over `max_tags`, the whole
batch is rejected. Existing tags, draft text, and selection remain unchanged.
The component never partially accepts a paste.


### Paste, delimiters, and composition

[Open the rendered preview](/v/0.4.2/ui-library/components/tags-input/_previews/paste-and-ime/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputPasteAndIme(Component):
    template = """
      <section
        class="tags-input-paste"
        x-data="{
          last:'Paste or compose in the editor',
          composing:false,
        }"
      >
        <c-CField>
          <c-fill name="label">Survey regions</c-fill>
          <c-fill name="description">
            Comma, semicolon, and a pasted newline separate regions.
            At most five tags are accepted.
          </c-fill>
          <c-fill name="default">
            <c-CTagsInput
              name="regions"
              c-value="['alpine']"
              c-delimiters="[',', ';']"
              max_tags="5"
              c-input_attrs="{
                '@compositionstart':'composing=true;last=`Composition started`',
                '@compositionend':'composing=false;last=`Composition ended`',
                '@paste':'last=`Paste received`',
              }"
              $c-props="{
                onValueChange:(next,detail)=>
                  last=`${detail.source}: ${JSON.stringify(next)}`,
                onValueInvalid:(reason,detail)=>
                  last=`Rejected ${reason}: ${detail.candidate || 'batch'}`,
              }"
            />
          </c-fill>
        </c-CField>

        <div class="tags-input-paste__sample">
          <p>Try replacing selected draft text with:</p>
          <pre>coast,forest;wetland
harbor</pre>
        </div>

        <output aria-live="polite" x-text="last">
          Paste or compose in the editor
        </output>
        <p x-show="composing">The input method editor owns Enter and delimiters.</p>
      </section>
    """

    css = """
      :where(.tags-input-paste) {
        display: grid;
        gap: 1rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-paste__sample) {
        padding: 0.85rem;
        border-radius: 0.75rem;
        background: color-mix(in srgb, CanvasText 6%, Canvas);
      }

      :where(.tags-input-paste__sample p) {
        margin-block-start: 0;
      }

      :where(.tags-input-paste pre) {
        margin: 0;
        white-space: pre-wrap;
      }
    """


preview = TagsInputPasteAndIme()

preview  # noqa: B018
````


Enter and delimiters do not commit while an input method editor is composing.
The final non-composing input is reconciled once after composition ends.

## Preserve native Form behavior

The visible text editor is unnamed. The hidden native
[`select multiple`](https://html.spec.whatwg.org/multipage/form-elements.html#the-select-element)
owns `name`, `form`, native required validity, and repeated values. A nonempty
editable draft sets native custom validity until the person commits or clears
it, so submission cannot silently omit unfinished text.


### Required values, external Forms, and reset

[Open the rendered preview](/v/0.4.2/ui-library/components/tags-input/_previews/forms-and-reset/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputFormsAndReset(Component):
    template = """
      <section
        class="tags-input-forms"
        x-data="{
          cancelReset:false,
          result:'No Form action yet',
        }"
      >
        <form
          id="tags-input-external-form"
          @submit.prevent="
            result = JSON.stringify(
              Array.from(new FormData($event.target).entries())
            )
          "
          @reset="
            if (cancelReset) {
              $event.preventDefault();
              result='Reset canceled';
            } else {
              setTimeout(() => result='Server baselines restored', 0);
            }
          "
        >
          <h3>Specimen routing Form</h3>
          <button type="submit">Submit repeated values</button>
          <button type="reset">Reset values and draft</button>
        </form>

        <c-CTagsInput
          id="external-routing-labels"
          name="labels"
          form="tags-input-external-form"
          required
          c-value="['urgent', 'billing']"
          input_value="unfinished"
          c-input_attrs="{'aria-label':'External routing labels'}"
        />

        <label>
          <input type="checkbox" x-model="cancelReset" />
          Cancel the next reset
        </label>

        <div class="tags-input-forms__transport">
          <c-CTagsInput
            name="readonly-labels"
            form="tags-input-external-form"
            readonly
            c-value="['preserved', 'ordered']"
            c-input_attrs="{'aria-label':'Readonly labels'}"
          />
          <c-CTagsInput
            name="disabled-labels"
            form="tags-input-external-form"
            disabled
            c-value="['omitted']"
            c-input_attrs="{'aria-label':'Disabled labels'}"
          />
        </div>

        <output aria-live="polite" x-text="result">
          No Form action yet
        </output>
      </section>
    """

    css = """
      :where(.tags-input-forms) {
        display: grid;
        gap: 1rem;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-forms form, .tags-input-forms__transport) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }

      :where(.tags-input-forms h3) {
        flex-basis: 100%;
        margin: 0;
      }
    """


preview = TagsInputFormsAndReset()

preview  # noqa: B018
````


An uncanceled reset reconstructs the server values and initial draft after the
native reset action. A canceled reset changes nothing. Controlled axes receive
reset requests and remain owner-supplied until accepted.

Readonly keeps the editor focusable and submits committed values through
repeated hidden controls. A draft that becomes dormant while readonly remains
visible but does not block submission and is not submitted. Disabled state
submits no entries.

Without JavaScript, the native multiple Select is visible. It supports
deselecting server values, required validity, repeated submission, external
Form ownership, and reset, but it cannot create new free-form values.

## Let Field own shared state

Inside `CField`, configure `required`, `disabled`, `readonly`, and `invalid` on
the Field. The TagsInput registers its editor as the one visible control while
the native Select retains Form validity.


### Field-owned TagsInput states

[Open the rendered preview](/v/0.4.2/ui-library/components/tags-input/_previews/field-states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputFieldStates(Component):
    template = """
      <section
        class="tags-input-fields"
        x-data="{
          required:true,
          readonly:false,
          moveDisabled:true,
        }"
      >
        <div class="tags-input-fields__controls">
          <label><input type="checkbox" x-model="required" /> Required</label>
          <label><input type="checkbox" x-model="readonly" /> Readonly</label>
          <button
            type="button"
            @click="
              const target = moveDisabled ? $refs.disabled : $refs.enabled;
              target.append($refs.moving);
              moveDisabled = !moveDisabled;
            "
          >
            Move the Field between fieldsets
          </button>
        </div>

        <c-CField
          $c-props="{required,readonly}"
        >
          <c-fill name="label">Publication topics</c-fill>
          <c-fill name="description">
            Field owns required and readonly state for the TagsInput.
          </c-fill>
          <c-fill name="default">
            <c-CTagsInput
              name="topics"
              c-value="['botany', 'fieldwork']"
            />
          </c-fill>
        </c-CField>

        <c-CField invalid>
          <c-fill name="label">Review labels</c-fill>
          <c-fill name="default">
            <c-CTagsInput name="review" c-value="['needs-source']" />
          </c-fill>
          <c-fill name="error">Resolve the review label before publishing.</c-fill>
        </c-CField>

        <div class="tags-input-fields__fieldsets">
          <fieldset x-ref="enabled">
            <legend>Enabled ancestry</legend>
            <div x-ref="moving">
              <c-CField>
                <c-fill name="label">Moved labels</c-fill>
                <c-fill name="default">
                  <c-CTagsInput name="moved" c-value="['portable']" />
                </c-fill>
              </c-CField>
            </div>
          </fieldset>
          <fieldset x-ref="disabled" disabled>
            <legend>Disabled ancestry</legend>
          </fieldset>
        </div>
      </section>
    """

    css = """
      :where(.tags-input-fields) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-fields__controls, .tags-input-fields__fieldsets) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.tags-input-fields fieldset) {
        flex: 1 1 16rem;
        min-inline-size: 0;
      }
    """


preview = TagsInputFieldStates()

preview  # noqa: B018
````


The visible editor mirrors effective requiredness with `aria-required`. Native
invalid focus moves to the editor when possible, then to a safe Dialog or
document fallback if the editor is unavailable.

## Navigate tags without leaving the editor

The editor is the sole sequential Tab stop. At the start of an empty draft,
Backspace first highlights the last tag and a second Backspace removes it.
Logical arrow movement visits tags while DOM focus remains in the editor.
Delete removes the highlighted tag, Home and End jump to an edge, and Escape
returns to ordinary editing.


### Keyboard, focus, and removal

[Open the rendered preview](/v/0.4.2/ui-library/components/tags-input/_previews/keyboard-and-focus/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputKeyboardAndFocus(Component):
    template = """
      <section
        class="tags-input-keyboard"
        x-data="{last:'Focus an editor to begin'}"
      >
        <article>
          <h3>Left-to-right navigation</h3>
          <p>
            At an empty start position, Backspace selects the last tag.
            Press it again to remove. Arrow keys, Home, End, Delete, and Escape
            operate while focus stays in the editor.
          </p>
          <c-CTagsInput
            c-value="['alpine', 'forest', 'harbor']"
            c-input_attrs="{
              'aria-label':'Keyboard labels',
              '@focus':'last=`LTR editor focused`',
            }"
            $c-props="{
              onValueChange:(next,detail)=>
                last=`${detail.source}: ${JSON.stringify(next)}`,
            }"
          />
        </article>

        <article dir="rtl">
          <h3>Right-to-left navigation</h3>
          <p>Physical arrows follow the visual row while value order stays stable.</p>
          <c-CTagsInput
            c-value="['جبال', 'غابة', 'ميناء']"
            c-input_attrs="{
              'aria-label':'وسوم لوحة المفاتيح',
              '@focus':'last=`RTL editor focused`',
            }"
          />
        </article>

        <output aria-live="polite" x-text="last">
          Focus an editor to begin
        </output>
      </section>
    """

    css = """
      :where(.tags-input-keyboard) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-keyboard article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.75rem;
      }

      :where(.tags-input-keyboard h3, .tags-input-keyboard p) {
        margin: 0;
      }

      :where(.tags-input-keyboard output) {
        grid-column: 1 / -1;
      }
    """


preview = TagsInputKeyboardAndFocus()

preview  # noqa: B018
````


Remove controls are native Buttons named from the tag value. A persistent
polite status announces accepted additions and removals, highlighted tags, and
rejected transactions. TagsInput does not use listbox, grid, combobox, or
toolbar roles.

## Choose a variant and size

`outline`, `filled`, and `plain` variants combine with `sm`, `md`, and `lg`
sizes. Long values wrap inside the control. `max_tags` blocks only later
additions when the current collection is already at or above the maximum.


### Variants, sizes, and boundary states

[Open the rendered preview](/v/0.4.2/ui-library/components/tags-input/_previews/variants-and-sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputVariantsAndSizes(Component):
    def template_data(self, kwargs, slots) -> dict[str, object]:  # noqa: ANN001, ARG002
        return {
            "variants": ("outline", "filled", "plain"),
            "sizes": ("sm", "md", "lg"),
        }

    template = """
      <section class="tags-input-variants">
        <div class="tags-input-variants__grid">
          <c-for each="variant in variants">
            <c-for each="size in sizes">
              <article>
                <code>{{ variant }} / {{ size }}</code>
                <c-CTagsInput
                  #c-key="f'{variant}-{size}'"
                  c-variant="variant"
                  c-size="size"
                  c-value="['alpine', 'coastal']"
                  c-input_attrs="{
                    'aria-label':f'{variant} {size} labels',
                  }"
                />
              </article>
            </c-for>
          </c-for>
        </div>

        <div class="tags-input-variants__boundaries">
          <article>
            <h3>Empty and required</h3>
            <c-CTagsInput
              required
              placeholder="Add a required label"
              c-input_attrs="{'aria-label':'Required empty labels'}"
            />
          </article>
          <article>
            <h3>At maximum</h3>
            <c-CTagsInput
              max_tags="2"
              c-value="['one', 'two']"
              c-input_attrs="{'aria-label':'Maximum labels'}"
            />
          </article>
          <article style="color-scheme:dark">
            <h3>Dark and narrow</h3>
            <c-CTagsInput
              invalid
              c-value="[
                'a-very-long-unbroken-routing-label-that-stays-contained',
              ]"
              c-input_attrs="{'aria-label':'Long invalid labels'}"
            />
          </article>
        </div>
      </section>
    """

    css = """
      :where(.tags-input-variants) {
        display: grid;
        gap: 1.25rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-variants__grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        gap: 0.75rem;
      }

      :where(.tags-input-variants article) {
        display: grid;
        gap: 0.5rem;
        min-inline-size: 0;
      }

      :where(.tags-input-variants__boundaries) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 0.75rem;
      }

      :where(.tags-input-variants__boundaries article) {
        inline-size: min(100%, 20rem);
        padding: 0.85rem;
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.tags-input-variants h3) {
        margin: 0;
      }
    """


preview = TagsInputVariantsAndSizes()

preview  # noqa: B018
````


## Customize stable parts and variables

Public `--cui-tags-input-*` variables tune color, spacing, sizing, and tag
presentation. Stable part selectors target the root, control, tag list, tags,
labels, remove Buttons, editor, and status node.


### Brand and environment customization

[Open the rendered preview](/v/0.4.2/ui-library/components/tags-input/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputCustomization(Component):
    template = """
      <section class="tags-input-customization">
        <article class="tags-input-brand tags-input-brand--orchard">
          <h3>Orchard field notes</h3>
          <c-CTagsInput
            class_="brand-tags"
            c-value="['pear', 'pollinator']"
            c-input_attrs="{'aria-label':'Orchard labels'}"
          />
        </article>

        <article
          class="tags-input-brand tags-input-brand--harbor"
          style="color-scheme:dark"
        >
          <h3>Harbor field notes</h3>
          <c-CTagsInput
            class_="brand-tags"
            variant="filled"
            c-value="['tide', 'harbor']"
            c-input_attrs="{'aria-label':'Harbor labels'}"
          />
        </article>
      </section>
    """

    css = """
      :where(.tags-input-customization) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-brand) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        min-block-size: 12rem;
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.tags-input-brand h3) {
        margin: 0;
      }

      :where(.tags-input-brand--orchard) {
        background: #f5f0df;
        color: #203422;
        --cui-tags-input-background: #fffdf5;
        --cui-tags-input-border-color: #78916d;
        --cui-tags-input-focus-color: #315f37;
        --cui-tags-input-tag-background: #d9e9cf;
        --cui-tags-input-tag-border-color: #78916d;
      }

      :where(.tags-input-brand--harbor) {
        background: #102b38;
        color: #eefaff;
        --cui-tags-input-background: #173c4c;
        --cui-tags-input-foreground: #eefaff;
        --cui-tags-input-border-color: #72b5ce;
        --cui-tags-input-focus-color: #c6ecff;
        --cui-tags-input-tag-background: #29586b;
        --cui-tags-input-tag-foreground: #eefaff;
      }

      .tags-input-brand .brand-tags
      [data-citry-ui-part="remove"] {
        border-radius: 999px;
        outline-offset: 2px;
      }

      @media (forced-colors: active) {
        :where(.tags-input-brand) {
          border: 1px solid CanvasText;
        }
      }

      @media print {
        :where(.tags-input-brand) {
          min-block-size: auto;
          background: transparent;
          color: black;
        }
      }
    """


preview = TagsInputCustomization()

preview  # noqa: B018
````


Unlayered application rules override the Citry UI theme layer whether loaded
before or after the component stylesheet. A named application layer must be
ordered after `citry-ui.theme`.

## Preserve state through server updates

Correlated server morphs preserve uncontrolled committed tags, draft,
selection, focus, and highlighted-tag identity when their server baselines are
unchanged. A changed baseline replaces only the matching uncontrolled axis.


### Morph preservation and cleanup

[Open the rendered preview](/v/0.4.2/ui-library/components/tags-input/_previews/morph-and-cleanup/)

````citry
from __future__ import annotations

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputMorphAndCleanup(Component):
    class Kwargs:
        step: int = 0

    class Slots:
        pass

    class Events:
        def refresh(self) -> TagsInputMorphAndCleanup:
            return TagsInputMorphAndCleanup()

        def advance(self) -> TagsInputMorphAndCleanup:
            return TagsInputMorphAndCleanup(step=2)

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        baseline = ("server-one", "server-two")
        if kwargs.step >= 2:
            baseline = ("new-server-baseline",)
        return {"baseline": baseline, "step": kwargs.step}

    template = """
      <section
        class="tags-input-morph"
        x-data="{
          controlled:false,
          tags:['owner-one'],
          mounted:true,
        }"
      >
        <div class="tags-input-morph__controls">
          <button type="button" @c-click="refresh">
            Morph with the same baseline
          </button>
          <button type="button" @c-click="advance">
            Morph to a new baseline
          </button>
          <button type="button" @click="controlled=!controlled">
            Toggle controlled handoff
          </button>
          <button type="button" @click="mounted=!mounted">
            Remove or restore the fixture
          </button>
        </div>

        <p>Server step: <output>{{ step }}</output></p>

        <template x-if="mounted">
          <div>
            <c-CTagsInput
              #c-key="'tags-input-morph-target'"
              id="tags-input-morph-target"
              c-value="baseline"
              input_value="unfinished"
              c-input_attrs="{'aria-label':'Morph labels'}"
              $c-props="{
                value:controlled ? tags : null,
                onValueChange:(next)=>{
                  if (controlled) tags=next;
                },
              }"
            />
          </div>
        </template>

        <p>
          Unchanged server baselines preserve uncontrolled tags, draft,
          selection, and focus. Step two supplies a new baseline. An active
          composition keeps the exact editor node through either morph.
        </p>
      </section>
    """

    css = """
      :where(.tags-input-morph) {
        display: grid;
        gap: 1rem;
        max-inline-size: 40rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-morph__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.tags-input-morph p) {
        margin: 0;
      }
    """


preview = TagsInputMorphAndCleanup()

preview  # noqa: B018
````


An active composition keeps the exact editor DOM node. Removing the component
cancels pending reset, focus, status, and controlled-acceptance work.

## Distinguish callbacks from native events

Use these semantic component callbacks through `$c-props`:

- `onValueChange` for a valid add, removal, or controlled reset request;
- `onInputValueChange` for draft edits and accepted draft transitions; and
- `onValueInvalid` for a rejected empty, duplicate, maximum, delimiter, or
  invalid-value transaction.

Native editor events remain ordinary Alpine listeners such as `@input`,
`@paste`, `@focus`, and `@blur` in `input_attrs`. Native bubbling `input` and
`change` events on the Select proxy report accepted uncontrolled value
changes. Controlled value requests dispatch no native proxy change event.

TagsInput dispatches no custom DOM event and exposes no public method. Use an
ordinary ref when application code needs to focus or inspect the editor.

## Treat attributes and values as data

`attrs` targets the root and `input_attrs` targets the editor. They accept
ordinary nonconflicting attributes, styling, permitted accessibility hints,
and Alpine `@event` or `x-on:event` observers. The component rejects values
that can replace its identity, native Form ownership, state, Field
relationships, structure, or Alpine lifecycle.

Tag values, drafts, placeholders, and message substitutions are assigned as
text or native values. They are never evaluated as HTML, URLs, selectors, or
Alpine expressions.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CTagsInput server inputs

Server inputs are passed in a template through `<c-CTagsInput ... />` or in Python through
`CTagsInput(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tags-input-input-ctags-input-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the repeated native Form field name; omission makes values nonparticipating. |
| <span id="tags-input-input-ctags-input-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the native proxy and readonly transports with a Form ID. |
| <span id="tags-input-input-ctags-input-server-inputs-id"></span>`id` | `str | None` | generated | Sets the public control ID exchanged between the native fallback and initialized editor. |
| <span id="tags-input-input-ctags-input-server-inputs-value"></span>`value` | `Sequence[str]` | () | Sets the initial ordered canonical unique tags and repeated Form values. |
| <span id="tags-input-input-ctags-input-server-inputs-input-value"></span>`input_value` | `str` | `""` | Sets the initial raw unfinished editor draft. |
| <span id="tags-input-input-ctags-input-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native required validity outside Field. |
| <span id="tags-input-input-ctags-input-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Disables interaction and removes all successful controls outside Field. |
| <span id="tags-input-input-ctags-input-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Blocks editing while repeated hidden controls preserve submission outside Field. |
| <span id="tags-input-input-ctags-input-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds owner-supplied invalid presentation outside Field. |
| <span id="tags-input-input-ctags-input-server-inputs-placeholder"></span>`placeholder` | `str | None` | `None` | Sets editor placeholder text. |
| <span id="tags-input-input-ctags-input-server-inputs-delimiters"></span>`delimiters` | `Sequence[str]` | (",",) | Sets unique server-only single-code-point token separators. |
| <span id="tags-input-input-ctags-input-server-inputs-max-tags"></span>`max_tags` | `int | None` | `None` | Limits later additions to a positive maximum without removing existing tags. |
| <span id="tags-input-input-ctags-input-server-inputs-autocomplete"></span>`autocomplete` | `str | None` | `None` | Sets the editor autocomplete hint. |
| <span id="tags-input-input-ctags-input-server-inputs-inputmode"></span>`inputmode` | `str | None` | `None` | Sets the editor virtual-keyboard hint. |
| <span id="tags-input-input-ctags-input-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CTagsInputVariant`](#tags-input-interface-variant)) | `"outline"` | Selects the control treatment. |
| <span id="tags-input-input-ctags-input-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CTagsInputSize`](#tags-input-interface-size)) | `"md"` | Selects editor, tag, and control geometry. |
| <span id="tags-input-input-ctags-input-server-inputs-messages"></span>`messages` | `CTagsInputMessages | None` ([`CTagsInputMessages`](#tags-input-interface-ctags-input-messages)) | `None` | Overrides catalog-backed removal, status, rejection, and unfinished-draft text per field. |
| <span id="tags-input-input-ctags-input-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#tags-input-interface-class-value)) | `None` | Adds root classes and merges them with attrs. |
| <span id="tags-input-input-ctags-input-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#tags-input-interface-style-value)) | `None` | Adds root inline styles and merges them with attrs. |
| <span id="tags-input-input-ctags-input-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed attributes to the root. |
| <span id="tags-input-input-ctags-input-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed naming, descriptive, hint, style, and native-listener attributes to the editor. |

</div>

#### CTagsInput client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTagsInput />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 16rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="tags-input-input-ctags-input-client-inputs-value"></span>`value` | `string[] | null` | Releases to the latest committed uncontrolled baseline; null has the same effect. | Controls ordered committed tags while supplied as a valid array. |
| <span id="tags-input-input-ctags-input-client-inputs-input-value"></span>`inputValue` | `string | null` | Releases to the latest committed uncontrolled draft baseline; null has the same effect. | Controls the raw editor draft while supplied as a valid string. |
| <span id="tags-input-input-ctags-input-client-inputs-placeholder"></span>`placeholder` | `string | null` | Uses the server value. | Controls editor placeholder text; null releases and an empty string removes the attribute. |
| <span id="tags-input-input-ctags-input-client-inputs-autocomplete"></span>`autocomplete` | `string | null` | Uses the server value. | Controls the editor autocomplete hint; null releases and an empty string removes the attribute. |
| <span id="tags-input-input-ctags-input-client-inputs-inputmode"></span>`inputmode` | `string | null` | Uses the server value. | Controls the editor inputmode hint; null releases and an empty string removes the attribute. |
| <span id="tags-input-input-ctags-input-client-inputs-required"></span>`required` | `boolean` | Uses the server or Field fallback. | Controls native required validity and the editor accessibility mirror outside Field. |
| <span id="tags-input-input-ctags-input-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server or Field fallback. | Controls interaction and Form participation outside Field. |
| <span id="tags-input-input-ctags-input-client-inputs-readonly"></span>`readonly` | `boolean` | Uses the server or Field fallback. | Controls read-only interaction and repeated hidden transport outside Field. |
| <span id="tags-input-input-ctags-input-client-inputs-invalid"></span>`invalid` | `boolean` | Uses the server or Field fallback. | Controls owner-supplied invalid presentation outside Field. |
| <span id="tags-input-input-ctags-input-client-inputs-max-tags"></span>`maxTags` | `positive integer | null` | Uses the server value. | Controls the addition limit; null removes the maximum. |
| <span id="tags-input-input-ctags-input-client-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CTagsInputVariant`](#tags-input-interface-variant)) | Uses the server value. | Controls presentation treatment. |
| <span id="tags-input-input-ctags-input-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CTagsInputSize`](#tags-input-interface-size)) | Uses the server value. | Controls editor, tag, and control geometry. |
| <span id="tags-input-input-ctags-input-client-inputs-on-value-change"></span>`onValueChange` | `function` | Omission or null selects no value callback. | Receives valid add, removal, and controlled reset requests. |
| <span id="tags-input-input-ctags-input-client-inputs-on-input-value-change"></span>`onInputValueChange` | `function` | Omission or null selects no draft callback. | Receives direct draft edits and acceptance-gated draft transitions. |
| <span id="tags-input-input-ctags-input-client-inputs-on-value-invalid"></span>`onValueInvalid` | `function` | Omission or null selects no rejection callback. | Receives one structured notice for each rejected user transaction. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CTagsInput events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="tags-input-event-ctags-input-events-value-change"></span>`onValueChange` | `(nextValue: string[], detail: CTagsInputValueChangeDetail) => void` ([`CTagsInputValueChangeDetail`](#tags-input-interface-ctags-input-value-change-detail)) | A valid enabled add or removal is requested, or a controlled value axis receives an uncanceled reset request. | `{source, added, removed, candidates, previousValue, nextInputValue, controlled}` ([`CTagsInputValueChangeDetail`](#tags-input-interface-ctags-input-value-change-detail)) | Runs after full batch validation. Uncontrolled values commit first; controlled values remain unchanged until an exact later acceptance edge. |
| <span id="tags-input-event-ctags-input-events-input-value-change"></span>`onInputValueChange` | `(nextDraft: string, detail: CTagsInputInputValueChangeDetail) => void` ([`CTagsInputInputValueChangeDetail`](#tags-input-interface-ctags-input-input-value-change-detail)) | A direct editor input or accepted commit changes the draft, or a controlled draft receives an uncanceled reset request. | `{source, previousValue, nextValue, controlled, composing}` ([`CTagsInputInputValueChangeDetail`](#tags-input-interface-ctags-input-input-value-change-detail)) | Direct input is synchronous. Commit-related clear or trailing draft waits for the related value acceptance and matching draft generation. |
| <span id="tags-input-event-ctags-input-events-value-invalid"></span>`onValueInvalid` | `(reason: CTagsInputInvalidReason, detail: CTagsInputInvalidDetail) => void` ([`CTagsInputInvalidReason`](#tags-input-interface-invalid-reason), [`CTagsInputInvalidDetail`](#tags-input-interface-ctags-input-invalid-detail)) | An enabled editable Enter, delimiter, or paste transaction fails an empty, duplicate, maximum, delimiter, or invalid-value guard. | `{source, candidate, candidates, value, inputValue, maxTags, controlled}` ([`CTagsInputInvalidDetail`](#tags-input-interface-ctags-input-invalid-detail)) | Fires once for the atomic transaction without changing tags, proxy values, draft, or selection. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTagsInput CSS variables

Apply these variables to `CTagsInput` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="tags-input-css-ctags-input-css-variables-background"></span>`--cui-tags-input-background` | `color` | Control background. | `Canvas` |
| <span id="tags-input-css-ctags-input-css-variables-foreground"></span>`--cui-tags-input-foreground` | `color` | Editor and tag text. | `CanvasText` |
| <span id="tags-input-css-ctags-input-css-variables-border-color"></span>`--cui-tags-input-border-color` | `color` | Resting control border. | `color-mix(in srgb, CanvasText 28%, transparent)` |
| <span id="tags-input-css-ctags-input-css-variables-hover-border-color"></span>`--cui-tags-input-hover-border-color` | `color` | Enabled hover border. | `color-mix(in srgb, CanvasText 55%, transparent)` |
| <span id="tags-input-css-ctags-input-css-variables-focus-color"></span>`--cui-tags-input-focus-color` | `color` | Focus-visible outline. | `Highlight` |
| <span id="tags-input-css-ctags-input-css-variables-invalid-border-color"></span>`--cui-tags-input-invalid-border-color` | `color` | Revealed or owner-supplied invalid border. | `light-dark(#b42318, #fda29b)` |
| <span id="tags-input-css-ctags-input-css-variables-disabled-background"></span>`--cui-tags-input-disabled-background` | `color` | Disabled control background. | `color-mix(in srgb, CanvasText 6%, Canvas)` |
| <span id="tags-input-css-ctags-input-css-variables-tag-background"></span>`--cui-tags-input-tag-background` | `color` | Tag background. | `color-mix(in srgb, CanvasText 8%, Canvas)` |
| <span id="tags-input-css-ctags-input-css-variables-tag-foreground"></span>`--cui-tags-input-tag-foreground` | `color` | Tag text and removal foreground. | `CanvasText` |
| <span id="tags-input-css-ctags-input-css-variables-tag-border-color"></span>`--cui-tags-input-tag-border-color` | `color` | Tag boundary. | `color-mix(in srgb, CanvasText 18%, transparent)` |
| <span id="tags-input-css-ctags-input-css-variables-tag-highlighted-background"></span>`--cui-tags-input-tag-highlighted-background` | `color` | Keyboard-active tag background. | `light-dark(#dbeafe, #19376d)` |
| <span id="tags-input-css-ctags-input-css-variables-tag-highlighted-border-color"></span>`--cui-tags-input-tag-highlighted-border-color` | `color` | Keyboard-active tag border. | `Highlight` |
| <span id="tags-input-css-ctags-input-css-variables-radius"></span>`--cui-tags-input-radius` | `length` | Control and tag rounding. | `0.5rem` |
| <span id="tags-input-css-ctags-input-css-variables-min-height"></span>`--cui-tags-input-min-height` | `length` | Minimum control height. | `2.5rem` |
| <span id="tags-input-css-ctags-input-css-variables-padding"></span>`--cui-tags-input-padding` | `length` | Control internal inset. | `0.375rem 0.5rem` |
| <span id="tags-input-css-ctags-input-css-variables-gap"></span>`--cui-tags-input-gap` | `length` | Space between tags and editor. | `0.375rem` |
| <span id="tags-input-css-ctags-input-css-variables-tag-gap"></span>`--cui-tags-input-tag-gap` | `length` | Space between each tag label and remove Button. | `0.25rem` |
| <span id="tags-input-css-ctags-input-css-variables-font-size"></span>`--cui-tags-input-font-size` | `length` | Editor and tag text size. | `1rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTagsInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tags-input-attribute-ctags-input-root-attributes-data-empty"></span>`data-empty` | Root div | `present | absent` | Present when no effective tags exist. |
| <span id="tags-input-attribute-ctags-input-root-attributes-data-required"></span>`data-required` | Root div | `present | absent` | Mirrors effective requiredness. |
| <span id="tags-input-attribute-ctags-input-root-attributes-data-disabled"></span>`data-disabled` | Root div | `present | absent` | Mirrors effective disabledness. |
| <span id="tags-input-attribute-ctags-input-root-attributes-data-readonly"></span>`data-readonly` | Root div | `present | absent` | Mirrors effective readonly state. |
| <span id="tags-input-attribute-ctags-input-root-attributes-data-invalid"></span>`data-invalid` | Root div | `present | absent` | Mirrors owner invalidity or a revealed native-invalid episode. |
| <span id="tags-input-attribute-ctags-input-root-attributes-data-focused"></span>`data-focused` | Root div | `present | absent` | Present while the editor has focus-visible context. |
| <span id="tags-input-attribute-ctags-input-root-attributes-data-at-max"></span>`data-at-max` | Root div | `present | absent` | Present when the effective count is at or above maxTags. |
| <span id="tags-input-attribute-ctags-input-root-attributes-data-variant"></span>`data-variant` | Root div | `"outline" | "filled" | "plain"` ([`CTagsInputVariant`](#tags-input-interface-variant)) | Mirrors effective treatment. |
| <span id="tags-input-attribute-ctags-input-root-attributes-data-size"></span>`data-size` | Root div | `"sm" | "md" | "lg"` ([`CTagsInputSize`](#tags-input-interface-size)) | Mirrors effective geometry. |

</div>

#### CTagsInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tags-input-attribute-ctags-input-proxy-attributes-proxy-id"></span>`id` | Native multiple Select | `public ID or derived native ID` | Owns the public ID in fallback mode and the derived ID after initialization. |
| <span id="tags-input-attribute-ctags-input-proxy-attributes-proxy-multiple"></span>`multiple` | Native multiple Select | `present` | Produces one repeated Form entry per selected Option. |
| <span id="tags-input-attribute-ctags-input-proxy-attributes-proxy-name"></span>`name` | Native multiple Select | `string | absent` | Supplies the repeated Form field name while editable. |
| <span id="tags-input-attribute-ctags-input-proxy-attributes-proxy-form"></span>`form` | Native multiple Select | `Form ID | absent` | Associates an external Form owner. |
| <span id="tags-input-attribute-ctags-input-proxy-attributes-proxy-required"></span>`required` | Native multiple Select | `present | absent` | Owns native required validity. |
| <span id="tags-input-attribute-ctags-input-proxy-attributes-proxy-disabled"></span>`disabled` | Native multiple Select | `present | absent` | Bars validation and submission for readonly or disabled transport modes. |
| <span id="tags-input-attribute-ctags-input-proxy-attributes-proxy-aria-hidden"></span>`aria-hidden` | Native multiple Select | `"true" | absent` | Hides the proxy from accessibility APIs only after successful initialization. |
| <span id="tags-input-attribute-ctags-input-proxy-attributes-proxy-tabindex"></span>`tabindex` | Native multiple Select | `"-1" | absent` | Removes the initialized proxy from sequential focus. |
| <span id="tags-input-attribute-ctags-input-proxy-attributes-proxy-aria-invalid"></span>`aria-invalid` | Native multiple Select | `"true" | absent` | Mirrors effective visible invalidity. |

</div>

#### CTagsInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tags-input-attribute-ctags-input-editor-attributes-editor-id"></span>`id` | Editor input | `public ID or derived editor ID` | Owns the public ID after initialization and the derived ID in fallback mode. |
| <span id="tags-input-attribute-ctags-input-editor-attributes-editor-type"></span>`type` | Editor input | `"text"` | Provides ordinary text editing and IME behavior. |
| <span id="tags-input-attribute-ctags-input-editor-attributes-editor-readonly"></span>`readonly` | Editor input | `present | absent` | Blocks edits while retaining focusability. |
| <span id="tags-input-attribute-ctags-input-editor-attributes-editor-disabled"></span>`disabled` | Editor input | `present | absent` | Removes editor interaction and focus. |
| <span id="tags-input-attribute-ctags-input-editor-attributes-editor-aria-label"></span>`aria-label` | Editor and proxy | `non-whitespace string | absent` | Supplies the required standalone static accessible name. |
| <span id="tags-input-attribute-ctags-input-editor-attributes-editor-aria-labelledby"></span>`aria-labelledby` | Editor and proxy | `Field label IDREF | absent` | Mirrors Field-owned generated naming. |
| <span id="tags-input-attribute-ctags-input-editor-attributes-editor-aria-describedby"></span>`aria-describedby` | Editor and proxy | `description and error IDREFs | absent` | Mirrors Field or allowed standalone descriptions. |
| <span id="tags-input-attribute-ctags-input-editor-attributes-editor-aria-required"></span>`aria-required` | Editor input | `"true" | absent` | Mirrors native proxy requiredness on the visible control. |
| <span id="tags-input-attribute-ctags-input-editor-attributes-editor-aria-invalid"></span>`aria-invalid` | Editor input | `"true" | absent` | Mirrors owner invalidity or a revealed native-invalid episode. |

</div>

#### CTagsInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tags-input-attribute-ctags-input-tag-attributes-data-highlighted"></span>`data-highlighted` | Tag span | `present | absent` | Marks the visually active tag while DOM focus remains in the editor. |
| <span id="tags-input-attribute-ctags-input-tag-attributes-remove-type"></span>`type` | Remove Button | `"button"` | Prevents accidental Form submission. |
| <span id="tags-input-attribute-ctags-input-tag-attributes-remove-tabindex"></span>`tabindex` | Remove Button | `"-1"` | Keeps the editor as the sole sequential Tab stop. |
| <span id="tags-input-attribute-ctags-input-tag-attributes-remove-aria-label"></span>`aria-label` | Remove Button | `localized string` | Names removal with the exact tag value. |
| <span id="tags-input-attribute-ctags-input-tag-attributes-remove-disabled"></span>`disabled` | Remove Button | `present | absent` | Blocks removal while readonly or disabled. |

</div>

#### CTagsInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tags-input-attribute-ctags-input-status-attributes-status-role"></span>`role` | Status span | `"status"` | Exposes nonurgent accepted, rejected, and navigation updates. |
| <span id="tags-input-attribute-ctags-input-status-attributes-status-aria-live"></span>`aria-live` | Status span | `"polite"` | Queues updates without interrupting current speech. |
| <span id="tags-input-attribute-ctags-input-status-attributes-status-aria-atomic"></span>`aria-atomic` | Status span | `"true"` | Announces each complete status sentence. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTagsInput selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="tags-input-selector-ctags-input-selectors-tags-input"></span>`[data-citry-ui-part="tags-input"]` | Root div | State reflections and class, style, and attrs destination. |
| <span id="tags-input-selector-ctags-input-selectors-control"></span>`[data-citry-ui-part="control"]` | Visible control div | Wraps committed tags and the editor. |
| <span id="tags-input-selector-ctags-input-selectors-tag-list"></span>`[data-citry-ui-part="tag-list"]` | Tag-list span | Wraps zero or more component-owned tag visuals before the editor. |
| <span id="tags-input-selector-ctags-input-selectors-tag"></span>`[data-citry-ui-part="tag"]` | Tag span | Displays one effective canonical value and highlighted state. |
| <span id="tags-input-selector-ctags-input-selectors-tag-label"></span>`[data-citry-ui-part="tag-label"]` | Tag label span | Displays the exact effective string. |
| <span id="tags-input-selector-ctags-input-selectors-remove"></span>`[data-citry-ui-part="remove"]` | Native Button | Removes its named tag by pointer, touch, or programmatic activation. |
| <span id="tags-input-selector-ctags-input-selectors-input"></span>`[data-citry-ui-part="input"]` | Native text input | Sole custom editor and initialized focus owner. |
| <span id="tags-input-selector-ctags-input-selectors-status"></span>`[data-citry-ui-part="status"]` | Visually hidden span | Persistent polite accepted, rejected, and navigation announcements. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="tags-input-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="tags-input-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |
| <span id="tags-input-interface-variant"></span>`CTagsInputVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="tags-input-interface-size"></span>`CTagsInputSize` | `Literal["sm", "md", "lg"]` |
| <span id="tags-input-interface-change-source"></span>`CTagsInputChangeSource` | `Literal["input", "enter", "delimiter", "paste", "backspace", "delete", "remove", "reset"]` |
| <span id="tags-input-interface-invalid-reason"></span>`CTagsInputInvalidReason` | `Literal["empty", "duplicate", "maximum", "delimiter", "invalid-value"]` |

</div>

<span id="tags-input-interface-ctags-input-messages"></span>

#### `CTagsInputMessages`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tags-input-interface-ctags-input-messages-remove-label"></span>`remove_label` | `str | None` | None | Overrides the catalog-backed remove label and requires `{value}`. |
| <span id="tags-input-interface-ctags-input-messages-added-message"></span>`added_message` | `str | None` | None | Overrides the accepted-addition announcement and requires `{value}`. |
| <span id="tags-input-interface-ctags-input-messages-removed-message"></span>`removed_message` | `str | None` | None | Overrides the accepted-removal announcement and requires `{value}`. |
| <span id="tags-input-interface-ctags-input-messages-selected-message"></span>`selected_message` | `str | None` | None | Overrides the active-tag announcement and requires `{value}`. |
| <span id="tags-input-interface-ctags-input-messages-duplicate-message"></span>`duplicate_message` | `str | None` | None | Overrides duplicate rejection and requires `{value}`. |
| <span id="tags-input-interface-ctags-input-messages-maximum-message"></span>`maximum_message` | `str | None` | None | Overrides maximum rejection and requires `{max}`. |
| <span id="tags-input-interface-ctags-input-messages-empty-message"></span>`empty_message` | `str | None` | None | Overrides the empty-candidate announcement. |
| <span id="tags-input-interface-ctags-input-messages-invalid-message"></span>`invalid_message` | `str | None` | None | Overrides the noncanonical-candidate announcement. |
| <span id="tags-input-interface-ctags-input-messages-uncommitted-message"></span>`uncommitted_message` | `str | None` | None | Overrides native custom validity for an editable unfinished draft. |

</div>

<span id="tags-input-interface-ctags-input-value-change-detail"></span>

#### `CTagsInputValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tags-input-interface-ctags-input-value-change-detail-source"></span>`source` | `CTagsInputChangeSource` | - | Identifies the interaction or reset request. |
| <span id="tags-input-interface-ctags-input-value-change-detail-added"></span>`added` | `string[]` | - | Contains accepted or requested additions in order. |
| <span id="tags-input-interface-ctags-input-value-change-detail-removed"></span>`removed` | `string[]` | - | Contains accepted or requested removals in order. |
| <span id="tags-input-interface-ctags-input-value-change-detail-candidates"></span>`candidates` | `string[]` | - | Contains the complete atomic candidate batch. |
| <span id="tags-input-interface-ctags-input-value-change-detail-previous-value"></span>`previousValue` | `string[]` | - | Copies the effective collection before the request. |
| <span id="tags-input-interface-ctags-input-value-change-detail-next-input-value"></span>`nextInputValue` | `string` | - | Supplies the draft requested only after exact value acceptance. |
| <span id="tags-input-interface-ctags-input-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Reports whether client value owns the collection. |

</div>

<span id="tags-input-interface-ctags-input-input-value-change-detail"></span>

#### `CTagsInputInputValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tags-input-interface-ctags-input-input-value-change-detail-source"></span>`source` | `CTagsInputChangeSource` | - | Identifies direct input, accepted tokenization, or reset. |
| <span id="tags-input-interface-ctags-input-input-value-change-detail-previous-value"></span>`previousValue` | `string` | - | Copies the effective draft before the request. |
| <span id="tags-input-interface-ctags-input-input-value-change-detail-next-value"></span>`nextValue` | `string` | - | Copies the requested next draft. |
| <span id="tags-input-interface-ctags-input-input-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Reports whether client inputValue owns the draft. |
| <span id="tags-input-interface-ctags-input-input-value-change-detail-composing"></span>`composing` | `boolean` | - | Reports whether an input callback occurred during active composition. |

</div>

<span id="tags-input-interface-ctags-input-invalid-detail"></span>

#### `CTagsInputInvalidDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tags-input-interface-ctags-input-invalid-detail-source"></span>`source` | `CTagsInputChangeSource` | - | Identifies Enter, delimiter, or paste as the rejected source. |
| <span id="tags-input-interface-ctags-input-invalid-detail-candidate"></span>`candidate` | `string | null` | - | Identifies the first offending candidate when one exists. |
| <span id="tags-input-interface-ctags-input-invalid-detail-candidates"></span>`candidates` | `string[]` | - | Copies the complete attempted atomic batch. |
| <span id="tags-input-interface-ctags-input-invalid-detail-value"></span>`value` | `string[]` | - | Copies the unchanged effective tags. |
| <span id="tags-input-interface-ctags-input-invalid-detail-input-value"></span>`inputValue` | `string` | - | Copies the unchanged effective draft. |
| <span id="tags-input-interface-ctags-input-invalid-detail-max-tags"></span>`maxTags` | `number | null` | - | Reports the effective maximum. |
| <span id="tags-input-interface-ctags-input-invalid-detail-controlled"></span>`controlled` | `boolean` | - | Reports whether client value owns the collection. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CTagsInput translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="tags-input-translation-ctags-input-translations-remove"></span>`citry-ui-tags-input-remove` | Names each tag remove control. | `value: str` | `messages.remove_label` | $c-tr handles initial controls; `i18n.bind()` handles recreated controls. |
| <span id="tags-input-translation-ctags-input-translations-added"></span>`citry-ui-tags-input-added` | Announces accepted additions. | `value: str` | `messages.added_message` | One-shot `i18n.tr()` when the interaction occurs. |
| <span id="tags-input-translation-ctags-input-translations-removed"></span>`citry-ui-tags-input-removed` | Announces accepted removals. | `value: str` | `messages.removed_message` | One-shot `i18n.tr()` when the interaction occurs. |
| <span id="tags-input-translation-ctags-input-translations-selected"></span>`citry-ui-tags-input-selected` | Announces keyboard-active tags. | `value: str` | `messages.selected_message` | One-shot `i18n.tr()` when the interaction occurs. |
| <span id="tags-input-translation-ctags-input-translations-duplicate"></span>`citry-ui-tags-input-duplicate` | Announces duplicate rejection. | `value: str` | `messages.duplicate_message` | One-shot `i18n.tr()` when the interaction occurs. |
| <span id="tags-input-translation-ctags-input-translations-maximum"></span>`citry-ui-tags-input-maximum` | Announces the maximum-tag limit. | `max: str` | `messages.maximum_message` | One-shot `i18n.tr()` with locale-formatted `max`. |
| <span id="tags-input-translation-ctags-input-translations-required"></span>`citry-ui-tags-input-required` | Announces an empty candidate. | `None` | `messages.empty_message` | One-shot `i18n.tr()` when the interaction occurs. |
| <span id="tags-input-translation-ctags-input-translations-invalid"></span>`citry-ui-tags-input-invalid` | Announces a noncanonical candidate. | `None` | `messages.invalid_message` | One-shot `i18n.tr()` when the interaction occurs. |
| <span id="tags-input-translation-ctags-input-translations-unfinished"></span>`citry-ui-tags-input-unfinished` | Supplies native validity text for an unfinished draft. | `None` | `messages.uncommitted_message` | One-shot `i18n.tr()` when validity is evaluated. |

</div>