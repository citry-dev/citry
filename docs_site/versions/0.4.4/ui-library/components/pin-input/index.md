---
title: Pin input
url: https://citry.dev/v/0.4.4/ui-library/components/pin-input/
description: "Capture fixed-length verification and recovery codes without losing native input behavior."
---
# Pin input

Use `CPinInput` for one-time codes, PINs, and short recovery tokens. Its value
is always a string, so a leading zero is preserved.

## Enter a verification code

Give a standalone PinInput an accessible `label`, or place it in `CField` for a
visible label, help, error, and shared state.


```citry-html
<c-CField required>
  <c-fill name="label">Verification code</c-fill>
  <c-fill name="description">Enter the six digits from your message.</c-fill>
  <c-fill name="default"><c-CPinInput name="code" /></c-fill>
</c-CField>
```



### Enter a verification code

[Open the rendered preview](/v/0.4.4/ui-library/components/pin-input/_previews/basic/)

````citry
from citry import Component


class BasicPinInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CField required>
        <c-fill name="label">Verification code</c-fill>
        <c-fill name="description">Enter the six digits from your message.</c-fill>
        <c-fill name="default"><c-CPinInput name="code" /></c-fill>
      </c-CField>
    """


preview = BasicPinInput()
preview  # noqa: B018
````


One native text input owns focus, selection, paste, autofill, validation, and
submission. The separate cells are visual only and create neither extra Tab
stops nor separate Form values. Without JavaScript the native input remains a
normal usable text box.

## Accept recovery-code letters

The default `type="numeric"` accepts ASCII digits. Use `alphabetic` or
`alphanumeric` for protocol tokens containing ASCII letters. These values are
opaque identifiers, not localized numbers.


### Enter an alphanumeric recovery code

[Open the rendered preview](/v/0.4.4/ui-library/components/pin-input/_previews/alphanumeric/)

````citry
from citry import Component


class AlphanumericPinInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CField>
        <c-fill name="label">Recovery code</c-fill>
        <c-fill name="description">Use the eight letters and digits printed with your account.</c-fill>
        <c-fill name="default"><c-CPinInput name="recovery" type="alphanumeric" c-length="8" /></c-fill>
      </c-CField>
    """


preview = AlphanumericPinInput()
preview  # noqa: B018
````


Invalid characters are discarded and reported through `onValueInvalid`.
`length` is structural and supports 1 through 32 characters.

## Control the value

Client `value` controls the exact string. An edit is a request: the displayed
cells and Form value remain owner-controlled until the Alpine expression
returns the requested value.


### Control a PinInput

[Open the rendered preview](/v/0.4.4/ui-library/components/pin-input/_previews/controlled/)

````citry
from citry import Component

# ruff: noqa: E501 - Alpine expression stays readable in public source


class ControlledPinInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="pin-input-demo-stack" x-data="{code:'12',last:'No request yet'}">
        <c-CPinInput
          label="Controlled four-digit code"
          value="12"
          c-length="4"
          $c-props="{value:code,onValueChange:(next,detail)=>{code=next;last=`${detail.source}: ${next}`},onComplete:(next)=>last=`Complete: ${next}`}"
        />
        <output x-text="last">No request yet</output>
        <c-CButton type="button" @click="code=''">Clear</c-CButton>
      </section>
    """
    css = ":where(.pin-input-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = ControlledPinInput()
preview  # noqa: B018
````


`onValueChange` reports accepted edits. `onComplete` reports a transition to a
full value and never submits the Form automatically. Paste and autofill remain
available.

## Preserve native Form behavior

`required` combines with an exact-length native pattern, so an empty or partial
required code blocks submission. Readonly values remain focusable and submit;
disabled values do not submit.


### Submit and reset codes

[Open the rendered preview](/v/0.4.4/ui-library/components/pin-input/_previews/forms/)

````citry
from citry import Component

# ruff: noqa: E501 - template expression stays readable in public source


class PinInputForms(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <form class="pin-input-demo-stack" x-data="{result:'Submit or reset the Form'}" @submit.prevent="result=JSON.stringify(Array.from(new FormData($event.target).entries()))">
        <c-CField required>
          <c-fill name="label">One-time code</c-fill>
          <c-fill name="default"><c-CPinInput name="code" value="01" /></c-fill>
        </c-CField>
        <c-CPinInput name="issued" label="Issued code" value="246810" readonly />
        <c-CRow><c-CButton type="submit">Submit</c-CButton><c-CButton type="reset" variant="outline">Reset</c-CButton></c-CRow>
        <output x-text="result">Submit or reset the Form</output>
      </form>
    """
    css = ":where(.pin-input-demo-stack){display:grid;justify-items:start;gap:1rem}"


preview = PinInputForms()
preview  # noqa: B018
````


`one_time_code=True` emits `autocomplete="one-time-code"`. Set an explicit
`input_attrs={"autocomplete": "..."}` when another autocomplete policy is
required. Citry never invokes WebOTP or reads SMS messages.

## Mask or group the visual cells

`mask=True` replaces filled visual cells with bullets without changing the
submitted string. It reduces shoulder surfing but is not encryption and does
not hide the accessible text-field value from assistive software.


### Mask a code

[Open the rendered preview](/v/0.4.4/ui-library/components/pin-input/_previews/masked/)

````citry
from citry import Component


class MaskedPinInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="pin-input-demo-stack">
        <c-CPinInput label="Private access code" name="access-code" value="7412" c-length="4" mask />
        <p>Masking changes the visual cells only. Treat the submitted token as sensitive data.</p>
      </section>
    """
    css = ":where(.pin-input-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = MaskedPinInput()
preview  # noqa: B018
````


Use `attached=True` to join cells. For a 3–3 presentation, provide
`separator_after=(2,)` and the `separator` slot. Separator output is visual;
put instructions in Field description text.


### Group code cells

[Open the rendered preview](/v/0.4.4/ui-library/components/pin-input/_previews/separator/)

````citry
from citry import Component


class SeparatedPinInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="pin-input-demo-stack">
        <c-CPinInput label="Grouped recovery code" type="alphanumeric" c-separator_after="(2,)">
          <c-fill name="separator" data="{ index }">-</c-fill>
        </c-CPinInput>
        <c-CPinInput label="Attached four-digit code" c-length="4" attached />
      </section>
    """
    css = ":where(.pin-input-demo-stack){display:grid;justify-items:start;gap:1rem}"


preview = SeparatedPinInput()
preview  # noqa: B018
````


## Keep code direction and locale ownership clear

PinInput renders protocol tokens left-to-right by default, including inside an
RTL page. ASCII digits are not localized. Labels, Field text, placeholders,
and separators belong to the application and stay in its locale.


### Use PinInput in RTL content

[Open the rendered preview](/v/0.4.4/ui-library/components/pin-input/_previews/locales/)

````citry
from citry import Component


class PinInputLocales(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="pin-input-demo-stack" dir="rtl">
        <c-CField>
          <c-fill name="label">رمز التحقق</c-fill>
          <c-fill name="description">يبقى رمز البروتوكول من اليسار إلى اليمين.</c-fill>
          <c-fill name="default"><c-CPinInput value="104" /></c-fill>
        </c-CField>
      </section>
    """
    css = ":where(.pin-input-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = PinInputLocales()
preview  # noqa: B018
````


## Choose states and public styles

Outline and subtle variants combine with sm, md, and lg sizes. Public
`--cui-pin-input-*` variables and documented part selectors customize cells,
focus, separators, and state treatment.


### Compare PinInput states

[Open the rendered preview](/v/0.4.4/ui-library/components/pin-input/_previews/states/)

````citry
from citry import Component


class PinInputStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="pin-input-state-grid">
        <c-CPinInput label="Small subtle code" value="12" size="sm" variant="subtle" />
        <c-CPinInput label="Default code" value="123" />
        <c-CPinInput label="Large complete code" value="123456" size="lg" />
        <c-CPinInput label="Readonly code" value="246810" readonly />
        <c-CPinInput label="Disabled code" value="135790" disabled />
        <c-CPinInput label="Invalid code" value="12" invalid class_="pin-input-brand" />
      </section>
    """
    css = """
      :where(.pin-input-state-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));gap:1.5rem;align-items:start}
      :where(.pin-input-brand){--cui-pin-input-focus-color:#7c3aed;--cui-pin-input-radius:.75rem}
    """


preview = PinInputStates()
preview  # noqa: B018
````


Tab enters the component once. Native text editing and clipboard shortcuts
continue to work; Home, End, and pointer selection move the active visual cell.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CPinInput server inputs

Server inputs are passed in a template through `<c-CPinInput ... />` or in Python through
`CPinInput(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 13rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="pin-input-input-cpin-input-server-inputs-value"></span>`value` | `str` | `""` | Sets the initial exact string and preserves leading zeroes. |
| <span id="pin-input-input-cpin-input-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the native Form field name. |
| <span id="pin-input-input-cpin-input-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the native input with an external Form ID. |
| <span id="pin-input-input-cpin-input-server-inputs-id"></span>`id` | `str | None` | generated | Sets the native input ID and bases the root ID. |
| <span id="pin-input-input-cpin-input-server-inputs-length"></span>`length` | `int` | `6` | Sets one through thirty-two characters cells maxlength and exact validity. |
| <span id="pin-input-input-cpin-input-server-inputs-type"></span>`type` | `CPinInputType` ([`CPinInputType`](#pin-input-interface-type)) | `"numeric"` | Chooses the ASCII numeric alphabetic or alphanumeric token alphabet. |
| <span id="pin-input-input-cpin-input-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables exact-length native required validity outside Field. |
| <span id="pin-input-input-cpin-input-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks focus edits and Form submission outside Field. |
| <span id="pin-input-input-cpin-input-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Preserves focus selection and submission while blocking edits outside Field. |
| <span id="pin-input-input-cpin-input-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Reflects application invalid state outside Field. |
| <span id="pin-input-input-cpin-input-server-inputs-mask"></span>`mask` | `bool` | `False` | Replaces filled visual cells with bullets without changing the value. |
| <span id="pin-input-input-cpin-input-server-inputs-one-time-code"></span>`one_time_code` | `bool` | `True` | Emits one-time-code autocomplete unless input_attrs supplies another token. |
| <span id="pin-input-input-cpin-input-server-inputs-placeholder"></span>`placeholder` | `one-code-point str | None` | `"○"` | Supplies the caller-authored empty-cell marker. |
| <span id="pin-input-input-cpin-input-server-inputs-attached"></span>`attached` | `bool` | `False` | Joins adjacent visual cells. |
| <span id="pin-input-input-cpin-input-server-inputs-separator-after"></span>`separator_after` | `Sequence[int] | None` | `None` | Selects zero-based boundaries after which the separator slot renders. |
| <span id="pin-input-input-cpin-input-server-inputs-label"></span>`label` | `str | None` | `None` | Names a standalone native input; use the Field label slot inside Field. |
| <span id="pin-input-input-cpin-input-server-inputs-size"></span>`size` | `CPinInputSize` ([`CPinInputSize`](#pin-input-interface-size)) | `"md"` | Selects coordinated cell sizing. |
| <span id="pin-input-input-cpin-input-server-inputs-variant"></span>`variant` | `CPinInputVariant` ([`CPinInputVariant`](#pin-input-interface-variant)) | `"outline"` | Selects cell surface treatment. |
| <span id="pin-input-input-cpin-input-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#pin-input-interface-class-value)) | `None` | Adds classes to the root and merges with attrs. |
| <span id="pin-input-input-cpin-input-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#pin-input-interface-style-value)) | `None` | Adds styles to the root and merges with attrs. |
| <span id="pin-input-input-cpin-input-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing owned state or identity. |
| <span id="pin-input-input-cpin-input-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds copied native attributes including accessible naming descriptions autocomplete and dir without replacing owned behavior. |

</div>

#### CPinInput client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CPinInput />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="pin-input-input-cpin-input-client-inputs-value"></span>`value` | `string` | Releases control to the last uncontrolled value. | Controls the exact accepted token string. |
| <span id="pin-input-input-cpin-input-client-inputs-required"></span>`required` | `boolean` | Uses server or Field state. | Controls standalone exact-length validity. |
| <span id="pin-input-input-cpin-input-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or owner state. | Controls editing focus and Form participation. |
| <span id="pin-input-input-cpin-input-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or owner state. | Controls focusable nonmutable submission. |
| <span id="pin-input-input-cpin-input-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server or Field state. | Controls application invalid state. |
| <span id="pin-input-input-cpin-input-client-inputs-mask"></span>`mask` | `boolean` | Uses the server value. | Controls visual masking. |
| <span id="pin-input-input-cpin-input-client-inputs-variant"></span>`variant` | `CPinInputVariant` ([`CPinInputVariant`](#pin-input-interface-variant)) | Uses the server value. | Controls surface treatment. |
| <span id="pin-input-input-cpin-input-client-inputs-size"></span>`size` | `CPinInputSize` ([`CPinInputSize`](#pin-input-interface-size)) | Uses the server value. | Controls coordinated sizing. |
| <span id="pin-input-input-cpin-input-client-inputs-on-value-change"></span>`onValueChange` | `function` | No value callback. | Receives each accepted user edit or reset request. |
| <span id="pin-input-input-cpin-input-client-inputs-on-complete"></span>`onComplete` | `function` | No completion callback. | Receives transitions to a complete accepted token. |
| <span id="pin-input-input-cpin-input-client-inputs-on-value-invalid"></span>`onValueInvalid` | `function` | No rejection callback. | Receives discarded characters and their input source. |
| <span id="pin-input-input-cpin-input-client-inputs-on-focus-change"></span>`onFocusChange` | `function` | No focus callback. | Receives native focus entry and exit. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CPinInput slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="pin-input-slot-cpin-input-slots-separator"></span>`separator` | no | `{index: int}` ([`CPinInputSeparatorSlotData`](#pin-input-interface-cpin-input-separator-slot-data)) | No visual content at each separator_after boundary. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CPinInput events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="pin-input-event-cpin-input-events-on-value-change"></span>`onValueChange` | `(value: string, detail: CPinInputValueChangeDetail) => void` ([`CPinInputValueChangeDetail`](#pin-input-interface-cpin-input-value-change-detail)) | An accepted edit or Form reset requests a different value. | `{value, previousValue, controlled, source, sourceEvent}` ([`CPinInputValueChangeDetail`](#pin-input-interface-cpin-input-value-change-detail)) | Uncontrolled state commits first; controlled state is request-only. |
| <span id="pin-input-event-cpin-input-events-on-complete"></span>`onComplete` | `(value: string, detail: CPinInputCompleteDetail) => void` ([`CPinInputCompleteDetail`](#pin-input-interface-cpin-input-complete-detail)) | Accepted input transitions to the exact configured length. | `{value, controlled, source, sourceEvent}` ([`CPinInputCompleteDetail`](#pin-input-interface-cpin-input-complete-detail)) | Reports completion without automatically submitting. |
| <span id="pin-input-event-cpin-input-events-on-value-invalid"></span>`onValueInvalid` | `(detail: CPinInputInvalidDetail) => void` ([`CPinInputInvalidDetail`](#pin-input-interface-cpin-input-invalid-detail)) | One edit contains disallowed or overflow characters. | `{value, rejected, source, sourceEvent}` ([`CPinInputInvalidDetail`](#pin-input-interface-cpin-input-invalid-detail)) | Reports plain rejected text after filtering it from the value. |
| <span id="pin-input-event-cpin-input-events-on-focus-change"></span>`onFocusChange` | `(focused: boolean, detail: CPinInputFocusChangeDetail) => void` ([`CPinInputFocusChangeDetail`](#pin-input-interface-cpin-input-focus-change-detail)) | The native text input focuses or blurs. | `{focused, sourceEvent}` ([`CPinInputFocusChangeDetail`](#pin-input-interface-cpin-input-focus-change-detail)) | Runs after focus reflection changes. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CPinInput CSS variables

Apply these variables to `CPinInput` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="pin-input-css-cpin-input-css-variables-cell-size"></span>`--cui-pin-input-cell-size` | `length` | Visual cell inline and block size. | `Size-dependent 2.75rem.` |
| <span id="pin-input-css-cpin-input-css-variables-gap"></span>`--cui-pin-input-gap` | `length` | Space between separate cells. | `0.5rem` |
| <span id="pin-input-css-cpin-input-css-variables-separator-gap"></span>`--cui-pin-input-separator-gap` | `length` | Extra space for a separator boundary. | `0.4rem` |
| <span id="pin-input-css-cpin-input-css-variables-border-color"></span>`--cui-pin-input-border-color` | `color` | Outline cell border. | `Mixed CanvasText.` |
| <span id="pin-input-css-cpin-input-css-variables-focus-color"></span>`--cui-pin-input-focus-color` | `color` | Active-cell focus ring. | `Highlight` |
| <span id="pin-input-css-cpin-input-css-variables-invalid-color"></span>`--cui-pin-input-invalid-color` | `color` | Invalid border treatment. | `Theme danger color.` |
| <span id="pin-input-css-cpin-input-css-variables-background"></span>`--cui-pin-input-background` | `color` | Cell surface. | `Canvas` |
| <span id="pin-input-css-cpin-input-css-variables-color"></span>`--cui-pin-input-color` | `color` | Entered character color. | `CanvasText` |
| <span id="pin-input-css-cpin-input-css-variables-placeholder-color"></span>`--cui-pin-input-placeholder-color` | `color` | Empty-cell marker color. | `Muted CanvasText.` |
| <span id="pin-input-css-cpin-input-css-variables-radius"></span>`--cui-pin-input-radius` | `length` | Cell corner radius. | `0.5rem` |
| <span id="pin-input-css-cpin-input-css-variables-disabled-opacity"></span>`--cui-pin-input-disabled-opacity` | `number` | Disabled treatment opacity. | `0.58` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CPinInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="pin-input-attribute-cpin-input-root-attributes-data-required"></span>`data-required` | Root div | `present | absent` | Mirrors effective requiredness. |
| <span id="pin-input-attribute-cpin-input-root-attributes-data-disabled"></span>`data-disabled` | Root div | `present | absent` | Mirrors effective disabledness. |
| <span id="pin-input-attribute-cpin-input-root-attributes-data-readonly"></span>`data-readonly` | Root div | `present | absent` | Mirrors effective readonly state. |
| <span id="pin-input-attribute-cpin-input-root-attributes-data-invalid"></span>`data-invalid` | Root div | `present | absent` | Mirrors effective application or native invalidity. |
| <span id="pin-input-attribute-cpin-input-root-attributes-data-focused"></span>`data-focused` | Root div | `present | absent` | Marks native input focus. |
| <span id="pin-input-attribute-cpin-input-root-attributes-data-filled"></span>`data-filled` | Root div | `present | absent` | Marks any accepted character. |
| <span id="pin-input-attribute-cpin-input-root-attributes-data-complete"></span>`data-complete` | Root div | `present | absent` | Marks an accepted exact-length value. |
| <span id="pin-input-attribute-cpin-input-root-attributes-data-attached"></span>`data-attached` | Root div | `present | absent` | Marks joined cell styling. |
| <span id="pin-input-attribute-cpin-input-root-attributes-data-variant"></span>`data-variant` | Root div | `CPinInputVariant` ([`CPinInputVariant`](#pin-input-interface-variant)) | Mirrors surface treatment. |
| <span id="pin-input-attribute-cpin-input-root-attributes-data-size"></span>`data-size` | Root div | `CPinInputSize` ([`CPinInputSize`](#pin-input-interface-size)) | Mirrors coordinated sizing. |

</div>

#### CPinInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="pin-input-attribute-cpin-input-cell-attributes-data-active"></span>`data-active` | Visual cell | `present | absent` | Marks the logical native selection or insertion cell. |
| <span id="pin-input-attribute-cpin-input-cell-attributes-data-filled"></span>`data-filled` | Visual cell | `present | absent` | Marks an accepted character. |
| <span id="pin-input-attribute-cpin-input-cell-attributes-data-masked"></span>`data-masked` | Visual cell | `present | absent` | Marks a character currently displayed as a bullet. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CPinInput selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="pin-input-selector-cpin-input-selectors-pin-input"></span>`[data-citry-ui-part="pin-input"]` | Root div | State reflections and root customization destination. |
| <span id="pin-input-selector-cpin-input-selectors-input"></span>`[data-citry-ui-part="input"]` | Native text input | Owns semantics focus editing validation Form value and input_attrs. |
| <span id="pin-input-selector-cpin-input-selectors-cells"></span>`[data-citry-ui-part="cells"]` | Aria-hidden presentation span | Contains the segmented visual display. |
| <span id="pin-input-selector-cpin-input-selectors-cell"></span>`[data-citry-ui-part="cell"]` | Visual cell span | Displays one accepted position and receives pointer selection. |
| <span id="pin-input-selector-cpin-input-selectors-character"></span>`[data-citry-ui-part="character"]` | Character span | Displays entered masked or placeholder content. |
| <span id="pin-input-selector-cpin-input-selectors-caret"></span>`[data-citry-ui-part="caret"]` | Decorative caret span | Marks an active empty insertion cell. |
| <span id="pin-input-selector-cpin-input-selectors-separator"></span>`[data-citry-ui-part="separator"]` | Visual separator span | Hosts the caller separator slot at selected boundaries. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="pin-input-interface-type"></span>`CPinInputType` | `Literal["numeric", "alphabetic", "alphanumeric"]` |
| <span id="pin-input-interface-size"></span>`CPinInputSize` | `Literal["sm", "md", "lg"]` |
| <span id="pin-input-interface-variant"></span>`CPinInputVariant` | `Literal["outline", "subtle"]` |
| <span id="pin-input-interface-change-source"></span>`CPinInputChangeSource` | `Literal["input", "paste", "autofill", "composition", "reset"]` |
| <span id="pin-input-interface-invalid-source"></span>`CPinInputInvalidSource` | `Literal["input", "paste", "autofill", "composition"]` |
| <span id="pin-input-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="pin-input-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="pin-input-interface-cpin-input-separator-slot-data"></span>

#### `CPinInputSeparatorSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="pin-input-interface-cpin-input-separator-slot-data-index"></span>`index` | `int` | - | Zero-based cell index after which this separator renders. |

</div>

<span id="pin-input-interface-cpin-input-value-change-detail"></span>

#### `CPinInputValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="pin-input-interface-cpin-input-value-change-detail-value"></span>`value` | `string` | - | Requested accepted token. |
| <span id="pin-input-interface-cpin-input-value-change-detail-previous-value"></span>`previousValue` | `string` | - | Effective token before the request. |
| <span id="pin-input-interface-cpin-input-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns committed state. |
| <span id="pin-input-interface-cpin-input-value-change-detail-source"></span>`source` | `CPinInputChangeSource` ([`CPinInputChangeSource`](#pin-input-interface-change-source)) | - | Edit or reset source. |
| <span id="pin-input-interface-cpin-input-value-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native event when one exists. |

</div>

<span id="pin-input-interface-cpin-input-complete-detail"></span>

#### `CPinInputCompleteDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="pin-input-interface-cpin-input-complete-detail-value"></span>`value` | `string` | - | Complete accepted token. |
| <span id="pin-input-interface-cpin-input-complete-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns committed state. |
| <span id="pin-input-interface-cpin-input-complete-detail-source"></span>`source` | `CPinInputChangeSource` ([`CPinInputChangeSource`](#pin-input-interface-change-source)) | - | Completion source. |
| <span id="pin-input-interface-cpin-input-complete-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native event. |

</div>

<span id="pin-input-interface-cpin-input-invalid-detail"></span>

#### `CPinInputInvalidDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="pin-input-interface-cpin-input-invalid-detail-value"></span>`value` | `string` | - | Accepted filtered token. |
| <span id="pin-input-interface-cpin-input-invalid-detail-rejected"></span>`rejected` | `string` | - | Discarded plain characters. |
| <span id="pin-input-interface-cpin-input-invalid-detail-source"></span>`source` | `CPinInputInvalidSource` ([`CPinInputInvalidSource`](#pin-input-interface-invalid-source)) | - | Rejected edit source. |
| <span id="pin-input-interface-cpin-input-invalid-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native input event. |

</div>

<span id="pin-input-interface-cpin-input-focus-change-detail"></span>

#### `CPinInputFocusChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="pin-input-interface-cpin-input-focus-change-detail-focused"></span>`focused` | `boolean` | - | Current native focus state. |
| <span id="pin-input-interface-cpin-input-focus-change-detail-source-event"></span>`sourceEvent` | `object` | - | Native focus or blur event. |

</div>

### Translation keys

-