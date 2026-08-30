---
title: Rating
url: https://citry.dev/v/0.4.6/ui-library/components/rating/
description: "Select or display an exact localized score with native radio Form behavior."
---
# Rating

Use `CRating` for a short qualitative score such as a product review or
conversation rating. Its public value is an exact canonical decimal string;
`None` means unrated.

## Select a rating

Supply a standalone accessible `label`, or compose Rating in `CField` for a
visible label, description, error, and shared state.


```citry-html
<c-CField required>
  <c-fill name="label">Product rating</c-fill>
  <c-fill name="default"><c-CRating name="rating" /></c-fill>
</c-CField>
```



### Select a rating

[Open the rendered preview](/v/0.4.6/ui-library/components/rating/_previews/basic/)

````citry
from decimal import Decimal
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CRating

citry.register_library(citry_ui)

# ruff: noqa: E501 - template and CSS lines stay readable in public source examples


class BasicRating(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"python_rating": CRating(label="Python-composed rating", value=Decimal("4.0"))}

    template = """
      <section class="rating-demo-grid">
        <c-CField required>
          <c-fill name="label">Product rating</c-fill>
          <c-fill name="description">Choose one through five stars.</c-fill>
          <c-fill name="default"><c-CRating name="rating" value="3" /></c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_rating }}</article>
      </section>
    """
    css = """
      :where(.rating-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1.25rem}
      :where(.rating-demo-grid article){display:grid;align-content:start;gap:.75rem}:where(.rating-demo-grid h3){margin:0}
    """


preview = BasicRating()
preview  # noqa: B018
````


Without JavaScript, the component remains a same-name native radio group. It
submits and validates `required` normally. The visual stars are decorative;
each radio has a localized “value out of maximum” name.

## Choose fractional precision

`precision` is an exact decimal that divides one. Half, quarter, fifth, and
tenth ratings are supported as long as `max / precision` produces at most 200
choices. Floats and exponent notation are rejected.


### Use half and tenth ratings

[Open the rendered preview](/v/0.4.6/ui-library/components/rating/_previews/precision/)

````citry
from citry import Component


class RatingPrecision(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="rating-demo-stack">
        <c-CField>
          <c-fill name="label">Half-star rating</c-fill>
          <c-fill name="default"><c-CRating value="3.5" precision="0.5" /></c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">Tenth precision</c-fill>
          <c-fill name="default"><c-CRating value="4.2" precision="0.1" /></c-fill>
        </c-CField>
      </section>
    """
    css = ":where(.rating-demo-stack){display:grid;gap:1.25rem}"


preview = RatingPrecision()
preview  # noqa: B018
````


`max` is an integer from 1 through 20. Use `CRadioGroup` if individual values
need different text labels or meanings.

## Clear or control the value

Set `allow_clear=True` to let a person click the committed value again and
return to the unrated state. A required Rating then becomes natively invalid.


### Control and clear a rating

[Open the rendered preview](/v/0.4.6/ui-library/components/rating/_previews/controlled/)

````citry
from citry import Component

# ruff: noqa: E501 - Alpine expression stays readable in the public source example


class ControlledRating(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="rating-demo-stack" x-data="{score:'3',last:'No request yet'}">
        <c-CRating
          label="Controlled conversation rating"
          value="3"
          allow_clear
          $c-props="{value:score,onValueChange:(next,detail)=>{score=next;last=`${detail.source}: ${next ?? 'unrated'}`}}"
        />
        <output x-text="last">No request yet</output>
        <button type="button" @click="score='5'">Set five stars</button>
      </section>
    """
    css = ":where(.rating-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = ControlledRating()
preview  # noqa: B018
````


Client `value` is a canonical string or `null`. A controlled interaction is a
request: stars, checked radio, and FormData remain unchanged until the owner
returns the requested value. `onHoverChange` reports preview only and never
changes the submitted value.

## Preserve Form and reset behavior

Editable Rating submits the checked native radio. Readonly Rating blocks
mutation but submits its exact value through an owned hidden transport.
Disabled Rating neither focuses nor submits.


### Submit and reset ratings

[Open the rendered preview](/v/0.4.6/ui-library/components/rating/_previews/forms/)

````citry
from citry import Component

# ruff: noqa: E501 - template expressions stay readable in the public source example


class RatingForms(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <form class="rating-demo-stack" x-data="{result:'Submit or reset the Form'}" @submit.prevent="result=JSON.stringify(Array.from(new FormData($event.target).entries()))">
        <c-CField required>
          <c-fill name="label">Service rating</c-fill>
          <c-fill name="default"><c-CRating name="service" value="2" /></c-fill>
        </c-CField>
        <c-CRating name="published" label="Published rating" value="4.5" precision="0.5" readonly />
        <c-CRow><c-CButton type="submit">Submit</c-CButton><c-CButton type="reset" variant="outline">Reset</c-CButton></c-CRow>
        <output x-text="result">Submit or reset the Form</output>
      </form>
    """
    css = ":where(.rating-demo-stack){display:grid;justify-items:start;gap:1rem}"


preview = RatingForms()
preview  # noqa: B018
````


An uncanceled reset restores the server value. Controlled state receives a
reset request and waits for its owner. `form` supports an external native Form;
inside `CForm`, Rating cannot redirect ownership.

## Localize accessible value names

`citry-ui-rating-value` names each exact choice and updates in place beneath a
client-enabled `<c-i18n>` provider. The number profile is
`citry-ui-rating`. Zero-configuration source mode uses canonical digits and the
component's English source message.


### Localize Rating choice names

[Open the rendered preview](/v/0.4.6/ui-library/components/rating/_previews/locales/)

````citry
from citry import Component


class RatingLocales(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="rating-demo-stack">
        <c-CRating label="Catalog-backed value names" value="3.5" precision="0.5" />
        <c-CRating label="Application-owned value names" value="4" value_label="Score {value} / {max}" />
        <p>The first Rating follows its nearest client-enabled i18n provider; the explicit pattern stays fixed.</p>
      </section>
    """
    css = ":where(.rating-demo-stack){display:grid;justify-items:start;gap:1rem}"


preview = RatingLocales()
preview  # noqa: B018
````


Set `value_label="Score {value} / {max}"` for an application-owned fixed
pattern. An explicit override creates no catalog binding.

## Choose states and public styles

Solid and subtle variants combine with sm, md, and lg sizes. Public
`--cui-rating-*` variables and `[data-citry-ui-part="..."]` selectors
customize the documented anatomy.


### Compare Rating states and styling

[Open the rendered preview](/v/0.4.6/ui-library/components/rating/_previews/states/)

````citry
from citry import Component


class RatingStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="rating-state-grid">
        <c-CRating label="Small subtle rating" value="2" size="sm" variant="subtle" />
        <c-CRating label="Default rating" value="3" />
        <c-CRating label="Large readonly rating" value="4.5" precision="0.5" size="lg" readonly />
        <c-CRating label="Disabled rating" value="1" disabled />
        <div dir="rtl"><c-CRating label="RTL rating" value="4" /></div>
        <c-CRating label="Brand rating" value="5" class_="rating-brand" />
      </section>
    """
    css = """
      :where(.rating-state-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:1.5rem;align-items:start}
      :where(.rating-brand){--cui-rating-fill-color:#059669;--cui-rating-hover-color:#10b981;--cui-rating-gap:.4rem}
    """


preview = RatingStates()
preview  # noqa: B018
````


RTL uses logical geometry. Coarse pointers retain large hit targets and forced
colors preserve fill and focus. Custom symbol markup is intentionally not part
of this contract; use Radio for differently named choices.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CRating server inputs

Server inputs are passed in a template through `<c-CRating ... />` or in Python through
`CRating(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 13rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="rating-input-crating-server-inputs-value"></span>`value` | `CRatingExact | None` ([`CRatingExact`](#rating-interface-exact)) | `None` | Sets the initial exact score; zero and None mean unrated. |
| <span id="rating-input-crating-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the progressive native radio Form field name. |
| <span id="rating-input-crating-server-inputs-form"></span>`form` | `str | None` | `None` | Associates every radio and readonly transport with an external Form ID. |
| <span id="rating-input-crating-server-inputs-id"></span>`id` | `str | None` | generated | Sets the first radio ID and bases later radio root and transport IDs. |
| <span id="rating-input-crating-server-inputs-max"></span>`max` | `int` | `5` | Sets one through twenty visual stars and the maximum score. |
| <span id="rating-input-crating-server-inputs-precision"></span>`precision` | `CRatingExact` ([`CRatingExact`](#rating-interface-exact)) | `1` | Sets a positive exact selectable interval that divides one. |
| <span id="rating-input-crating-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native required radio-group validity outside Field. |
| <span id="rating-input-crating-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks focus mutation and Form submission outside Field. |
| <span id="rating-input-crating-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Preserves focus and exact submission while blocking mutation outside Field. |
| <span id="rating-input-crating-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Reflects application invalid state outside Field. |
| <span id="rating-input-crating-server-inputs-allow-clear"></span>`allow_clear` | `bool` | `False` | Lets a repeat click on the committed choice return to unrated. |
| <span id="rating-input-crating-server-inputs-label"></span>`label` | `str | None` | `None` | Names a standalone radiogroup; use the Field label slot inside Field. |
| <span id="rating-input-crating-server-inputs-value-label"></span>`value_label` | `str containing '{value}' and '{max}'` | `"{value} out of {max}"` | Overrides the catalog-backed accessible choice-name pattern. |
| <span id="rating-input-crating-server-inputs-variant"></span>`variant` | `"solid" | "subtle"` ([`CRatingVariant`](#rating-interface-variant)) | `"solid"` | Selects active-star treatment. |
| <span id="rating-input-crating-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CRatingSize`](#rating-interface-size)) | `"md"` | Selects coordinated symbol sizing. |
| <span id="rating-input-crating-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#rating-interface-class-value)) | `None` | Adds classes to the documented root and merges with attrs. |
| <span id="rating-input-crating-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#rating-interface-style-value)) | `None` | Adds styles to the documented root and merges with attrs. |
| <span id="rating-input-crating-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed radiogroup attributes without replacing owned state or identity. |
| <span id="rating-input-crating-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed attributes to every native radio. |

</div>

#### CRating client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CRating />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="rating-input-crating-client-inputs-value"></span>`value` | `canonical decimal string | null` | Releases control to the last uncontrolled value. | Controls the exact score or unrated state. |
| <span id="rating-input-crating-client-inputs-required"></span>`required` | `boolean` | Uses server or Field state. | Controls standalone required validity. |
| <span id="rating-input-crating-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or owner state. | Controls mutation and Form participation. |
| <span id="rating-input-crating-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or owner state. | Controls focusable nonmutable submission. |
| <span id="rating-input-crating-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server or Field state. | Controls application invalid state. |
| <span id="rating-input-crating-client-inputs-allow-clear"></span>`allowClear` | `boolean` | Uses the server value. | Controls repeat-click clearing. |
| <span id="rating-input-crating-client-inputs-variant"></span>`variant` | `CRatingVariant` ([`CRatingVariant`](#rating-interface-variant)) | Uses the server value. | Controls active-star treatment. |
| <span id="rating-input-crating-client-inputs-size"></span>`size` | `CRatingSize` ([`CRatingSize`](#rating-interface-size)) | Uses the server value. | Controls coordinated sizing. |
| <span id="rating-input-crating-client-inputs-on-value-change"></span>`onValueChange` | `function` | No semantic value callback. | Receives each user selection clear or reset request. |
| <span id="rating-input-crating-client-inputs-on-hover-change"></span>`onHoverChange` | `function` | No hover-preview callback. | Receives pointer preview changes without committing. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CRating events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="rating-event-crating-events-on-value-change"></span>`onValueChange` | `(value: string | null, detail: CRatingValueChangeDetail) => void` ([`CRatingValueChangeDetail`](#rating-interface-crating-value-change-detail)) | A user selects or clears a value or resets the owning Form. | `{value, previousValue, controlled, source, sourceEvent}` ([`CRatingValueChangeDetail`](#rating-interface-crating-value-change-detail)) | Uncontrolled native and visual state commit before notification; controlled state is request-only. |
| <span id="rating-event-crating-events-on-hover-change"></span>`onHoverChange` | `(value: string | null, detail: CRatingHoverChangeDetail) => void` ([`CRatingHoverChangeDetail`](#rating-interface-crating-hover-change-detail)) | Pointer preview enters a new exact choice or leaves the choices layer. | `{value, previousValue, sourceEvent}` ([`CRatingHoverChangeDetail`](#rating-interface-crating-hover-change-detail)) | Updates preview only and never changes FormData. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CRating CSS variables

Apply these variables to `CRating` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="rating-css-crating-css-variables-empty-color"></span>`--cui-rating-empty-color` | `color` | Empty-star color. | `Mixed CanvasText.` |
| <span id="rating-css-crating-css-variables-fill-color"></span>`--cui-rating-fill-color` | `color` | Committed active-star color. | `Amber.` |
| <span id="rating-css-crating-css-variables-hover-color"></span>`--cui-rating-hover-color` | `color` | Pointer-preview color. | `Brighter amber.` |
| <span id="rating-css-crating-css-variables-focus-color"></span>`--cui-rating-focus-color` | `color` | Keyboard focus outline. | `Highlight` |
| <span id="rating-css-crating-css-variables-gap"></span>`--cui-rating-gap` | `length` | Space between stars. | `0.25rem` |
| <span id="rating-css-crating-css-variables-symbol-size"></span>`--cui-rating-symbol-size` | `length` | Star size. | `1.5rem` |
| <span id="rating-css-crating-css-variables-control-size"></span>`--cui-rating-control-size` | `length` | Minimum pointer-target block size. | `2.75rem` |
| <span id="rating-css-crating-css-variables-disabled-opacity"></span>`--cui-rating-disabled-opacity` | `number` | Disabled treatment opacity. | `0.52` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CRating attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="rating-attribute-crating-root-attributes-data-hovering"></span>`data-hovering` | Root div | `present | absent` | Marks an active pointer preview. |
| <span id="rating-attribute-crating-root-attributes-data-required"></span>`data-required` | Root div | `present | absent` | Mirrors effective requiredness. |
| <span id="rating-attribute-crating-root-attributes-data-disabled"></span>`data-disabled` | Root div | `present | absent` | Mirrors effective disabledness. |
| <span id="rating-attribute-crating-root-attributes-data-readonly"></span>`data-readonly` | Root div | `present | absent` | Mirrors effective readonly state. |
| <span id="rating-attribute-crating-root-attributes-data-invalid"></span>`data-invalid` | Root div | `present | absent` | Mirrors application invalid state. |
| <span id="rating-attribute-crating-root-attributes-data-variant"></span>`data-variant` | Root div | `CRatingVariant` ([`CRatingVariant`](#rating-interface-variant)) | Mirrors active-star treatment. |
| <span id="rating-attribute-crating-root-attributes-data-size"></span>`data-size` | Root div | `CRatingSize` ([`CRatingSize`](#rating-interface-size)) | Mirrors coordinated sizing. |

</div>

#### CRating attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="rating-attribute-crating-choice-attributes-data-checked"></span>`data-checked` | Choice label | `present | absent` | Marks the committed exact choice. |
| <span id="rating-attribute-crating-choice-attributes-data-highlighted"></span>`data-highlighted` | Choice label | `present | absent` | Marks choices included in pointer preview. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CRating selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="rating-selector-crating-selectors-rating"></span>`[data-citry-ui-part="rating"]` | Root div | State reflections and root customization destination. |
| <span id="rating-selector-crating-selectors-visual"></span>`[data-citry-ui-part="visual"]` | Decorative visual span | Contains empty and clipped active stars. |
| <span id="rating-selector-crating-selectors-empty"></span>`[data-citry-ui-part="empty"]` | Empty-star span | Displays the unfilled scale. |
| <span id="rating-selector-crating-selectors-fill"></span>`[data-citry-ui-part="fill"]` | Clipped active-star span | Displays preview or committed fill. |
| <span id="rating-selector-crating-selectors-symbol"></span>`[data-citry-ui-part="symbol"]` | Decorative star span | Repeated fixed visual symbol. |
| <span id="rating-selector-crating-selectors-choices"></span>`[data-citry-ui-part="choices"]` | Choice layer span | Owns bounded exact hit targets and radios. |
| <span id="rating-selector-crating-selectors-choice"></span>`[data-citry-ui-part="choice"]` | Choice label | Exact pointer hit target and state hook. |
| <span id="rating-selector-crating-selectors-input"></span>`[data-citry-ui-part="input"]` | Native radio input | Keyboard semantics Form value and input_attrs destination. |
| <span id="rating-selector-crating-selectors-choice-label"></span>`[data-citry-ui-part="choice-label"]` | Visually hidden span | Supplies the localized native radio accessible name. |
| <span id="rating-selector-crating-selectors-readonly-value"></span>`[data-citry-ui-part="readonly-value"]` | Visually hidden span | Announces the readonly exact value. |
| <span id="rating-selector-crating-selectors-readonly-transport"></span>`[data-citry-ui-part="readonly-transport"]` | Hidden input | Submits a named readonly value. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="rating-interface-exact"></span>`CRatingExact` | `int | Decimal | str` |
| <span id="rating-interface-variant"></span>`CRatingVariant` | `Literal["solid", "subtle"]` |
| <span id="rating-interface-size"></span>`CRatingSize` | `Literal["sm", "md", "lg"]` |
| <span id="rating-interface-change-source"></span>`CRatingChangeSource` | `Literal["pointer", "keyboard", "reset"]` |
| <span id="rating-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="rating-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="rating-interface-crating-value-change-detail"></span>

#### `CRatingValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="rating-interface-crating-value-change-detail-value"></span>`value` | `string | null` | - | Requested exact canonical score or unrated state. |
| <span id="rating-interface-crating-value-change-detail-previous-value"></span>`previousValue` | `string | null` | - | Effective score before the request. |
| <span id="rating-interface-crating-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns committed state. |
| <span id="rating-interface-crating-value-change-detail-source"></span>`source` | `CRatingChangeSource` ([`CRatingChangeSource`](#rating-interface-change-source)) | - | Pointer keyboard or reset cause. |
| <span id="rating-interface-crating-value-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native interaction event when one exists. |

</div>

<span id="rating-interface-crating-hover-change-detail"></span>

#### `CRatingHoverChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="rating-interface-crating-hover-change-detail-value"></span>`value` | `string | null` | - | Current exact preview or null after leaving. |
| <span id="rating-interface-crating-hover-change-detail-previous-value"></span>`previousValue` | `string | null` | - | Preview before the pointer transition. |
| <span id="rating-interface-crating-hover-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native pointer event. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CRating translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="rating-translation-crating-translations-value"></span>`citry-ui-rating-value` | Names every exact radio choice and the readonly current value. | `value: str; max: str` | `value_label` | `i18n.bind()` formats the values and updates the native label text. |

</div>