---
title: Textarea
description: Enter multiline plain text with native editing, forms, validation, and optional browser control.
---

# Textarea

Use `CTextarea` for notes, descriptions, reports, and other multiline plain
text. It renders one native multiline text control, so editing, selection,
validation, submission, reset, spelling, and mobile keyboards keep their
browser behavior.

## Textarea at a glance

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/at_a_glance.py"
  title="Textarea at a glance"
/>

## Compose a labelled control

Put Textarea inside `CField` when it needs a label, description, or error.
Field owns those relationships and the composed required, disabled, read-only,
and invalid states.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/compose_textarea.py"
  title="Compose labelled and standalone Textareas"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/rows_and_resize.py"
  title="Choose rows and resize behavior"
/>

## Choose a variant

`outline`, `filled`, and `plain` change visual emphasis without changing the
native editing or form contract.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/variants.py"
  title="Compare Textarea variants"
/>

## Choose a size

`sm`, `md`, and `lg` adjust padding, font size, and line geometry. They do not
change `rows` or truncate text.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/sizes.py"
  title="Compare Textarea sizes"
/>

## Use Field and Form states

Required, disabled, read-only, and invalid controls retain their native
differences. Read-only text remains focusable and submitted. Disabled text is
not submitted.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/field_states.py"
  title="Compare Textarea states"
/>

## Validate, submit, and reset

Pass common native constraints such as `minlength`, `maxlength`, and
`spellcheck` through `attrs`. Native length validity follows the browser's
user-edit rules: initial or script-controlled text is not guaranteed to set
`tooShort` or `tooLong`, and browsers usually enforce `maxlength` while typing.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/validation_and_forms.py"
  title="Validate and reset a habitat report"
/>

## Control the browser value

Supply client `value` through `$c-props` to control current text. Mirror the
native `input` event to accept edits. Omit the prop to release control without
rewriting the current value.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/controlled_values.py"
  title="Control and release a draft"
/>

Citry compares before assigning, waits for composition and consumer updates,
and preserves the caret when your handler mirrors the native value. Listen to
native `@input`, `@change`, focus, invalid, and composition events directly;
Textarea adds no competing value-change callback.

## Keep native text and wrapping

Server and client values normalize line endings to LF. Leading and blank lines
remain text, and strings that look like HTML cannot create elements.
`wrap="hard"` requires `cols` and may add line breaks to submitted data;
`soft` does not add wrapping breaks.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/native_text.py"
  title="Use native multiline text and wrapping"
/>

## Write in either direction

Use native `dir` and `dirname` attributes for writing direction. Logical
padding and width work in LTR and RTL; long content scrolls inside the control.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/direction_and_content.py"
  title="Write long LTR and RTL notes"
/>

## Customize the theme

Override public variables on an ancestor or one Textarea. Use the stable part
selector for targeted rules.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctextarea/snippets/theme_customization.py"
  title="Theme two field journals"
/>

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
