---
title: TagsInput
description: Create and submit an ordered list of free-form text tags.
---

# TagsInput

Use `CTagsInput` when a person creates an ordered list of free-form strings,
such as labels, aliases, search terms, or routing keys. Committed tags and the
unfinished editor draft are separate values.

Use [MultiSelect](/ui-library/components/multi-select/) when choices come from
a fixed collection. Suggestions, remote filtering, and create-from-search
belong to a future Combobox rather than this component. Use
[Tag and TagGroup](/ui-library/components/tag/) to display tags without an
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

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctags_input/snippets/basic_tags.py" title="Template and Python TagsInput composition" />

## Control committed tags and the draft separately

Client `value` owns the ordered committed tags. Client `inputValue` owns the
raw editor draft. Either axis can be controlled alone, both can be controlled,
or both can remain uncontrolled.

`onValueChange` receives a complete proposed collection. A controlled request
does not update tags or native Form values until the owner supplies that exact
collection. An uncontrolled draft clears only after the related value request
is accepted, so refusing a controlled value does not erase the person's text.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctags_input/snippets/controlled_axes.py" title="Control tags and draft ownership" />

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

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctags_input/snippets/paste_and_ime.py" title="Paste, delimiters, and composition" />

Enter and delimiters do not commit while an input method editor is composing.
The final non-composing input is reconciled once after composition ends.

## Preserve native Form behavior

The visible text editor is unnamed. The hidden native
[`select multiple`](https://html.spec.whatwg.org/multipage/form-elements.html#the-select-element)
owns `name`, `form`, native required validity, and repeated values. A nonempty
editable draft sets native custom validity until the person commits or clears
it, so submission cannot silently omit unfinished text.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctags_input/snippets/forms_and_reset.py" title="Required values, external Forms, and reset" />

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

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctags_input/snippets/field_states.py" title="Field-owned TagsInput states" />

The visible editor mirrors effective requiredness with `aria-required`. Native
invalid focus moves to the editor when possible, then to a safe Dialog or
document fallback if the editor is unavailable.

## Navigate tags without leaving the editor

The editor is the sole sequential Tab stop. At the start of an empty draft,
Backspace first highlights the last tag and a second Backspace removes it.
Logical arrow movement visits tags while DOM focus remains in the editor.
Delete removes the highlighted tag, Home and End jump to an edge, and Escape
returns to ordinary editing.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctags_input/snippets/keyboard_and_focus.py" title="Keyboard, focus, and removal" />

Remove controls are native Buttons named from the tag value. A persistent
polite status announces accepted additions and removals, highlighted tags, and
rejected transactions. TagsInput does not use listbox, grid, combobox, or
toolbar roles.

## Choose a variant and size

`outline`, `filled`, and `plain` variants combine with `sm`, `md`, and `lg`
sizes. Long values wrap inside the control. `max_tags` blocks only later
additions when the current collection is already at or above the maximum.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctags_input/snippets/variants_and_sizes.py" title="Variants, sizes, and boundary states" />

## Customize stable parts and variables

Public `--cui-tags-input-*` variables tune color, spacing, sizing, and tag
presentation. Stable part selectors target the root, control, tag list, tags,
labels, remove Buttons, editor, and status node.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctags_input/snippets/customization.py" title="Brand and environment customization" />

Unlayered application rules override the Citry UI theme layer whether loaded
before or after the component stylesheet. A named application layer must be
ordered after `citry-ui.theme`.

## Preserve state through server updates

Correlated server morphs preserve uncontrolled committed tags, draft,
selection, focus, and highlighted-tag identity when their server baselines are
unchanged. A changed baseline replaces only the matching uncontrolled axis.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctags_input/snippets/morph_and_cleanup.py" title="Morph preservation and cleanup" />

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
