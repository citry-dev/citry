---
title: Color Picker
description: Select an opaque solid sRGB color with native form fallback.
---

# Color Picker

`CColorPicker` combines a native color input with an enhanced spectrum, hue
control, editable representation, and named swatches. Values are canonical
lowercase `#rrggbb` strings.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccolor_picker/snippets/at_a_glance.py" title="Choose a brand color" />

## Switch representations

Set `format` to `hex`, `rgb`, or `hsl`. The format changes only the editable
representation; the submitted and callback value remains canonical HEX.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccolor_picker/snippets/formats.py" title="Edit RGB and HSL colors" />

## Offer named swatches

Pass `CColorSwatch` records with validated color values and meaningful labels.
Swatches are shortcuts, not a separate source of truth.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccolor_picker/snippets/swatches.py" title="Choose from brand swatches" />

## Own value and popup state

Client `value` and `open` props are controlled. Change callbacks receive the
requested value or state and details about the interaction.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccolor_picker/snippets/controlled.py" title="Control the selected color" />

## Submit with native forms

The native color input remains the successful form control. It also owns form
reset behavior, so the no-script and enhanced paths agree.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccolor_picker/snippets/native_form.py" title="Submit a profile color" />

## Keep the field understandable

Provide a concise visible field label and meaningful swatch labels. Readonly
keeps the chosen value available while preventing color changes.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccolor_picker/snippets/accessibility.py" title="Present a readonly palette value" />

Alpha, gradients, image sampling, EyeDropper permissions, and wide-gamut color
spaces are outside this first solid-color contract.

<!-- UI_LIBRARY_API_REFERENCE -->
