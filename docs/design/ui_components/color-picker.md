# Color Picker

**Status (2026-08-22):** production implementation, public docs, structured
reference, examples, quality scenario, and focused browser
coverage shipped in `citry-ui` 0.2.0. Research refreshed 2026-08-21.

## 1. Purpose and first-release boundary

`CColorPicker` selects one opaque solid sRGB color. It targets the polished
Untitled UI workflow: a clear preview, saturation/value area, hue slider,
editable HEX/RGB/HSL representation, and named saved or brand swatches.
`CColorSwatch` is an immutable data record, not a declaration component.

The accepted value is always canonical lowercase `#rrggbb`. Gradients, alpha,
image sampling, EyeDropper permissions, wide-gamut spaces, color profiles, and
standalone subcontrols are deferred. This avoids pretending those features are
mere presentation flags on an opaque sRGB field.

## 2. Progressive enhancement and anatomy

The server renders a labeled native `input type=color` with `name`, `form`,
disabled state, and accepted value. It is the useful no-script path. The browser
runtime hides that native input visually, retains it as the form and reset
owner, and reveals the custom control.

```text
div root
|- label
|- native color input fallback
|- button trigger with preview and value
|- popup group
|  |- 2D saturation/value control
|  |- native hue range
|  |- format select and text input
|  `- named swatch list
`- polite status
```

## 3. Color model and validation

Python accepts only `#rgb` or `#rrggbb` and normalizes to lowercase six-digit
HEX. Swatches follow the same rule and require nonempty labels. The runtime
converts without external dependencies among HEX, integer RGB, HSL, and HSV.
Text edits are parsed only on commit. Invalid text sets `aria-invalid`, retains
the last accepted color, and never emits a request.

## 4. Interaction and accessibility

The trigger is a native button with dialog-popup state. The saturation/value
surface is one focusable compound color slider whose accessible value text
states both percentages and the canonical color. Left and Right adjust
saturation; Up and Down adjust value; Home and End set saturation to zero or
one hundred; Page Up and Down adjust value by ten. Pointer position controls
both axes. A native range input controls hue using the standard slider model.

The format select switches only the editable representation. Enter or blur
commits valid text; Escape restores accepted text. Named swatches are native
buttons in a list. Escape closes the popup and restores trigger focus; outside
pointer closes without stealing focus. Tab is not trapped.

## 5. State, callbacks, and forms

Server inputs are `value`, `label`, `name`, `form`, `format`, `swatches`,
`open`, `disabled`, `readonly`, `size`, `variant`, message overrides, and root
customization. Client props are `value`, `open`, `disabled`, `readonly`,
`format`, `onValueChange`, and `onOpenChange`.

Uncontrolled changes commit immediately and dispatch native `input` and
`change` from the color input. Controlled changes emit and restore accepted
state. `onValueChange(value, detail)` includes previous value, RGB/HSL/HSV
records, interaction source, controlled flag, and native event. Form reset
restores the server color or requests it from a controlled owner.

## 6. Localization and styling

Catalog messages name the saturation/value surface, hue input, format input,
value input, open trigger, invalid value, and selection announcement. Stable
HTML uses `$c-tr`; browser-created announcements use `i18n.tr()`. Swatch labels
and the field label are application text.

Public parts include `color-picker`, `label`, `native`, `trigger`, `preview`,
`value`, `popup`, `area`, `area-thumb`, `hue`, `fields`, `format`, `input`,
`swatches`, `swatch`, and `status`. Variables cover width, area height, surface,
border, radius, shadow, and focus. Narrow
layouts stack fields, logical properties support RTL, forced colors retain
boundaries, reduced motion removes transitions, and print shows label, preview,
and canonical value only.

## 7. Lifecycle, security, and acceptance

Pointer listeners exist only during an area drag. The outside listener exists
only while open. Initialization is idempotent; cleanup removes listeners,
bindings, form hooks, pointer capture, timers, and state. No input becomes HTML
or CSS syntax without strict HEX validation.

Evidence covers normalization, invalid server values and swatches, useful
native fallback, pointer and keyboard area changes, hue, all three text views,
invalid edit recovery, swatches, controlled rejection, native form/reset,
disabled and readonly behavior, localization, RTL, environments, cleanup, axe,
API schema, six snippets, and three browsers.
