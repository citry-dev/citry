---
title: Color Picker
url: https://citry.dev/v/0.4.3/ui-library/components/color-picker/
description: "Select an opaque solid sRGB color with native form fallback."
---
# Color Picker

`CColorPicker` combines a native color input with an enhanced spectrum, hue
control, editable representation, and named swatches. Values are canonical
lowercase `#rrggbb` strings.


### Choose a brand color

[Open the rendered preview](/v/0.4.3/ui-library/components/color-picker/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ColorPickerAtAGlance(Component):
    template = '<c-CColorPicker label="Brand color" value="#7f56d9" />'


preview = ColorPickerAtAGlance()
preview  # noqa: B018
````


## Switch representations

Set `format` to `hex`, `rgb`, or `hsl`. The format changes only the editable
representation; the submitted and callback value remains canonical HEX.


### Edit RGB and HSL colors

[Open the rendered preview](/v/0.4.3/ui-library/components/color-picker/_previews/formats/)

````citry
# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ColorPickerFormats(Component):
    template = """<div class="color-format-grid"><c-CColorPicker label="RGB color" value="#12b76a" format="rgb" /><c-CColorPicker label="HSL color" value="#f79009" format="hsl" /></div>"""
    css = ":where(.color-format-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem}"


preview = ColorPickerFormats()
preview  # noqa: B018
````


## Offer named swatches

Pass `CColorSwatch` records with validated color values and meaningful labels.
Swatches are shortcuts, not a separate source of truth.


### Choose from brand swatches

[Open the rendered preview](/v/0.4.3/ui-library/components/color-picker/_previews/swatches/)

````citry
# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CColorSwatch

citry.register_library(citry_ui)


class ColorPickerSwatches(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "swatches": [
                CColorSwatch("#7f56d9", "Violet"),
                CColorSwatch("#12b76a", "Green"),
                CColorSwatch("#f04438", "Red"),
                CColorSwatch("#f79009", "Orange"),
            ]
        }

    template = '<c-CColorPicker label="Accent" c-swatches="swatches" />'


preview = ColorPickerSwatches()
preview  # noqa: B018
````


## Own value and popup state

Client `value` and `open` props are controlled. Change callbacks receive the
requested value or state and details about the interaction.


### Control the selected color

[Open the rendered preview](/v/0.4.3/ui-library/components/color-picker/_previews/controlled/)

````citry
# ruff: noqa: E501 - Alpine expression remains readable in the public example

from citry import Component


class ControlledColorPicker(Component):
    template = """
      <section x-data="{color:'#7f56d9',open:false}">
        <c-CColorPicker label="Controlled accent" $c-props="{value:color,open,onValueChange:(next)=>color=next,onOpenChange:(next)=>open=next}" />
        <output x-text="color">#7f56d9</output>
      </section>
    """


preview = ControlledColorPicker()
preview  # noqa: B018
````


## Submit with native forms

The native color input remains the successful form control. It also owns form
reset behavior, so the no-script and enhanced paths agree.


### Submit a profile color

[Open the rendered preview](/v/0.4.3/ui-library/components/color-picker/_previews/native-form/)

````citry
# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeColorForm(Component):
    template = """<form><c-CColorPicker label="Profile color" name="profile_color" value="#1570ef" /><button type="reset">Reset</button><button type="submit">Save</button></form>"""


preview = NativeColorForm()
preview  # noqa: B018
````


## Keep the field understandable

Provide a concise visible field label and meaningful swatch labels. Readonly
keeps the chosen value available while preventing color changes.


### Present a readonly palette value

[Open the rendered preview](/v/0.4.3/ui-library/components/color-picker/_previews/accessibility/)

````citry
# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CColorSwatch

citry.register_library(citry_ui)


class AccessibleColorPicker(Component):
    def template_data(self, _kwargs, _slots):
        return {"swatches": [CColorSwatch("#005ea8", "Accessible blue"), CColorSwatch("#00703c", "Accessible green")]}

    template = '<c-CColorPicker label="Published theme color" value="#005ea8" c-swatches="swatches" readonly />'


preview = AccessibleColorPicker()
preview  # noqa: B018
````


Alpha, gradients, image sampling, EyeDropper permissions, and wide-gamut color
spaces are outside this first solid-color contract.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CColorPicker server inputs

Server inputs are passed in a template through `<c-CColorPicker ... />` or in Python through
`CColorPicker(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="color-picker-input-ccolor-picker-server-inputs-label"></span>`label` | `str` | required | Supplies the visible field label. |
| <span id="color-picker-input-ccolor-picker-server-inputs-value"></span>`value` | `str` | `"#7f56d9"` | Sets a '#rgb' or '#rrggbb' color normalized to lowercase six-digit HEX. |
| <span id="color-picker-input-ccolor-picker-server-inputs-id"></span>`id` | `str | None` | generated | Sets the root ID and derived control IDs. |
| <span id="color-picker-input-ccolor-picker-server-inputs-name"></span>`name` | `str | None` | `None` | Names the native color form control. |
| <span id="color-picker-input-ccolor-picker-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the native input with an external form. |
| <span id="color-picker-input-ccolor-picker-server-inputs-format"></span>`format` | `CColorPickerFormat` ([`CColorPickerFormat`](#color-picker-interface-format)) | `"hex"` | Chooses the editable HEX RGB or HSL representation. |
| <span id="color-picker-input-ccolor-picker-server-inputs-swatches"></span>`swatches` | `Sequence[CColorSwatch]` | `"()"` | Adds unique named solid-color shortcuts. |
| <span id="color-picker-input-ccolor-picker-server-inputs-open"></span>`open` | `bool` | `False` | Sets initial popup visibility. |
| <span id="color-picker-input-ccolor-picker-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables focus mutation and form submission. |
| <span id="color-picker-input-ccolor-picker-server-inputs-readonly"></span>`readonly` | `bool` | `False` | Prevents color mutation while retaining the value. |
| <span id="color-picker-input-ccolor-picker-server-inputs-size"></span>`size` | `CColorPickerSize` ([`CColorPickerSize`](#color-picker-interface-size)) | `"md"` | Selects trigger height. |
| <span id="color-picker-input-ccolor-picker-server-inputs-variant"></span>`variant` | `CColorPickerVariant` ([`CColorPickerVariant`](#color-picker-interface-variant)) | `"outline"` | Selects outline soft or plain trigger styling. |
| <span id="color-picker-input-ccolor-picker-server-inputs-open-label"></span>`open_label` | `str` | `"Open color picker"` | Overrides the catalog-backed trigger title. |
| <span id="color-picker-input-ccolor-picker-server-inputs-area-label"></span>`area_label` | `str` | `"Saturation and brightness"` | Overrides the compound slider name. |
| <span id="color-picker-input-ccolor-picker-server-inputs-hue-label"></span>`hue_label` | `str` | `"Hue"` | Overrides the hue label. |
| <span id="color-picker-input-ccolor-picker-server-inputs-format-label"></span>`format_label` | `str` | `"Color format"` | Overrides the format label. |
| <span id="color-picker-input-ccolor-picker-server-inputs-value-label"></span>`value_label` | `str` | `"Color value"` | Overrides the text input label. |
| <span id="color-picker-input-ccolor-picker-server-inputs-invalid-label"></span>`invalid_label` | `str` | `"Enter a valid color value"` | Overrides invalid edit announcements. |
| <span id="color-picker-input-ccolor-picker-server-inputs-selected-label"></span>`selected_label` | `str containing '{color}'` | `"Selected {color}"` | Overrides selection announcements. |
| <span id="color-picker-input-ccolor-picker-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#color-picker-interface-class-value)) | `None` | Adds root classes. |
| <span id="color-picker-input-ccolor-picker-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#color-picker-interface-style-value)) | `None` | Adds root styles. |
| <span id="color-picker-input-ccolor-picker-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes. |

</div>

#### CColorPicker client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CColorPicker />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="color-picker-input-ccolor-picker-client-inputs-value"></span>`value` | `string` | Uses uncontrolled state. | Controls the canonical HEX value. |
| <span id="color-picker-input-ccolor-picker-client-inputs-open"></span>`open` | `boolean` | Uses uncontrolled popup state. | Controls popup visibility. |
| <span id="color-picker-input-ccolor-picker-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server value. | Reactively disables the field. |
| <span id="color-picker-input-ccolor-picker-client-inputs-readonly"></span>`readonly` | `boolean` | Uses the server value. | Reactively prevents mutation. |
| <span id="color-picker-input-ccolor-picker-client-inputs-format"></span>`format` | `CColorPickerFormat` ([`CColorPickerFormat`](#color-picker-interface-format)) | Uses the server value. | Controls the editable representation. |
| <span id="color-picker-input-ccolor-picker-client-inputs-on-value-change"></span>`onValueChange` | `function` | No semantic callback runs. | Receives valid color requests. |
| <span id="color-picker-input-ccolor-picker-client-inputs-on-open-change"></span>`onOpenChange` | `function` | No semantic callback runs. | Receives popup visibility requests. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CColorPicker events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="color-picker-event-ccolor-picker-events-value"></span>`onValueChange` | `(value: string, detail: CColorPickerValueChangeDetail) => void` ([`CColorPickerValueChangeDetail`](#color-picker-interface-ccolor-picker-value-detail)) | A valid area hue text swatch native or reset request occurs. | `{value, previousValue, rgb, hsl, hsv, controlled, source, sourceEvent}` ([`CColorPickerValueChangeDetail`](#color-picker-interface-ccolor-picker-value-detail)) | Commits and dispatches native input and change only while uncontrolled. |
| <span id="color-picker-event-ccolor-picker-events-open"></span>`onOpenChange` | `(open: boolean, detail: CColorPickerOpenChangeDetail) => void` ([`CColorPickerOpenChangeDetail`](#color-picker-interface-ccolor-picker-open-detail)) | The popup requests a visibility change. | `{open, reason, sourceEvent}` ([`CColorPickerOpenChangeDetail`](#color-picker-interface-ccolor-picker-open-detail)) | Commits only while uncontrolled. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CColorPicker CSS variables

Apply these variables to `CColorPicker` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="color-picker-css-ccolor-picker-css-width"></span>`--cui-color-picker-width` | `length` | Trigger and popup width. | `20rem` |
| <span id="color-picker-css-ccolor-picker-css-area-height"></span>`--cui-color-picker-area-height` | `length` | Saturation and brightness area height. | `12rem` |
| <span id="color-picker-css-ccolor-picker-css-surface"></span>`--cui-color-picker-surface` | `color` | Popup and trigger surface. | `Canvas` |
| <span id="color-picker-css-ccolor-picker-css-border"></span>`--cui-color-picker-border` | `complete border` | Control boundaries. | `Adaptive 1px neutral` |
| <span id="color-picker-css-ccolor-picker-css-radius"></span>`--cui-color-picker-radius` | `length` | Popup radius. | `0.75rem` |
| <span id="color-picker-css-ccolor-picker-css-shadow"></span>`--cui-color-picker-shadow` | `shadow` | Popup elevation. | `Adaptive shadow` |
| <span id="color-picker-css-ccolor-picker-css-focus"></span>`--cui-color-picker-focus` | `color` | Focus and selected-swatch indicator. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CColorPicker attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="color-picker-attribute-ccolor-picker-attributes-data-open"></span>`data-open` | Root | `present | absent` | Reflects popup visibility. |
| <span id="color-picker-attribute-ccolor-picker-attributes-data-disabled"></span>`data-disabled` | Root | `present | absent` | Reflects disabled state. |
| <span id="color-picker-attribute-ccolor-picker-attributes-data-readonly"></span>`data-readonly` | Root | `present | absent` | Reflects readonly state. |
| <span id="color-picker-attribute-ccolor-picker-attributes-data-format"></span>`data-format` | Root | `CColorPickerFormat` ([`CColorPickerFormat`](#color-picker-interface-format)) | Reflects the editable representation. |
| <span id="color-picker-attribute-ccolor-picker-attributes-data-selected"></span>`data-selected` | Swatch | `present | absent` | Marks the current swatch. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CColorPicker selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="color-picker-selector-ccolor-picker-selectors-root"></span>`[data-citry-ui-part="color-picker"]` | Root | State and root customization destination. |
| <span id="color-picker-selector-ccolor-picker-selectors-native"></span>`[data-citry-ui-part="native"]` | Native color input | Progressive fallback form and reset owner. |
| <span id="color-picker-selector-ccolor-picker-selectors-trigger"></span>`[data-citry-ui-part="trigger"]` | Button | Opens the enhanced picker. |
| <span id="color-picker-selector-ccolor-picker-selectors-popup"></span>`[data-citry-ui-part="popup"]` | Dialog | Enhanced control container. |
| <span id="color-picker-selector-ccolor-picker-selectors-area"></span>`[data-citry-ui-part="area"]` | Compound slider | Changes saturation and brightness. |
| <span id="color-picker-selector-ccolor-picker-selectors-hue"></span>`[data-citry-ui-part="hue"]` | Label and range | Changes hue. |
| <span id="color-picker-selector-ccolor-picker-selectors-format"></span>`[data-citry-ui-part="format"]` | Select | Chooses editable representation. |
| <span id="color-picker-selector-ccolor-picker-selectors-input"></span>`[data-citry-ui-part="input"]` | Text input | Commits a parsed color. |
| <span id="color-picker-selector-ccolor-picker-selectors-swatches"></span>`[data-citry-ui-part="swatches"]` | List | Groups named shortcuts. |
| <span id="color-picker-selector-ccolor-picker-selectors-swatch"></span>`[data-citry-ui-part="swatch"]` | Button | Requests a named color. |
| <span id="color-picker-selector-ccolor-picker-selectors-status"></span>`[data-citry-ui-part="status"]` | Polite status | Announces validation and selection. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="color-picker-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="color-picker-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |
| <span id="color-picker-interface-format"></span>`CColorPickerFormat` | `Literal["hex", "rgb", "hsl"]` |
| <span id="color-picker-interface-size"></span>`CColorPickerSize` | `Literal["sm", "md", "lg"]` |
| <span id="color-picker-interface-variant"></span>`CColorPickerVariant` | `Literal["outline", "soft", "plain"]` |
| <span id="color-picker-interface-source"></span>`CColorPickerSource` | `Literal["area", "hue", "text", "swatch", "native", "reset"]` |
| <span id="color-picker-interface-swatch"></span>`CColorSwatch` | `CColorSwatch(value: str, label: str)` |

</div>

<span id="color-picker-interface-ccolor-picker-value-detail"></span>

#### `CColorPickerValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="color-picker-interface-ccolor-picker-value-detail-value"></span>`value` | `str` | - | Requested canonical HEX value. |
| <span id="color-picker-interface-ccolor-picker-value-detail-previous"></span>`previousValue` | `str` | - | Previous value. |
| <span id="color-picker-interface-ccolor-picker-value-detail-rgb"></span>`rgb` | `dict[str, int]` | - | Requested integer RGB channels. |
| <span id="color-picker-interface-ccolor-picker-value-detail-hsl"></span>`hsl` | `dict[str, float]` | - | Requested HSL channels. |
| <span id="color-picker-interface-ccolor-picker-value-detail-hsv"></span>`hsv` | `dict[str, float]` | - | Requested HSV channels. |
| <span id="color-picker-interface-ccolor-picker-value-detail-controlled"></span>`controlled` | `bool` | - | Whether client value owns state. |
| <span id="color-picker-interface-ccolor-picker-value-detail-source"></span>`source` | `CColorPickerSource` | - | Interaction source. |
| <span id="color-picker-interface-ccolor-picker-value-detail-source-event"></span>`sourceEvent` | `object` | - | Native Event. |

</div>

<span id="color-picker-interface-ccolor-picker-open-detail"></span>

#### `CColorPickerOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="color-picker-interface-ccolor-picker-open-detail-open"></span>`open` | `bool` | - | Requested popup state. |
| <span id="color-picker-interface-ccolor-picker-open-detail-reason"></span>`reason` | `str` | - | Trigger outside escape or selection reason. |
| <span id="color-picker-interface-ccolor-picker-open-detail-source-event"></span>`sourceEvent` | `object` | - | Native Event. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CColorPicker translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="color-picker-translation-ccolor-picker-translations-open"></span>`citry-ui-color-picker-open` | Provides the enhanced trigger title. | `none` | `open_label` | Declarative `$c-tr` attribute binding. |
| <span id="color-picker-translation-ccolor-picker-translations-area"></span>`citry-ui-color-picker-area` | Names the compound saturation and brightness slider. | `none` | `area_label` | Declarative `$c-tr` attribute binding. |
| <span id="color-picker-translation-ccolor-picker-translations-hue"></span>`citry-ui-color-picker-hue` | Labels the hue range. | `none` | `hue_label` | Declarative `$c-tr` text binding. |
| <span id="color-picker-translation-ccolor-picker-translations-format"></span>`citry-ui-color-picker-format` | Labels the format select. | `none` | `format_label` | Declarative `$c-tr` text binding. |
| <span id="color-picker-translation-ccolor-picker-translations-value"></span>`citry-ui-color-picker-value` | Labels the editable value. | `none` | `value_label` | Declarative `$c-tr` text binding. |
| <span id="color-picker-translation-ccolor-picker-translations-invalid"></span>`citry-ui-color-picker-invalid` | Announces an invalid text edit. | `none` | `invalid_label` | Browser-created one-shot `i18n.tr()`. |
| <span id="color-picker-translation-ccolor-picker-translations-selected"></span>`citry-ui-color-picker-selected` | Announces an accepted color. | `color: str` | `selected_label` with `{color}` | Browser-created one-shot `i18n.tr()`. |

</div>