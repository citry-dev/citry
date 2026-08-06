---
title: Combobox
description: Search a local or remote collection and submit one stable option value.
---

# Combobox

`CCombobox` is a searchable single select. The submitted value must match an
option. Use it when a plain Select would be too slow to scan. It does not accept
arbitrary text as a value.

## Combobox at a glance

Options may include supporting descriptions and disabled choices. Selection,
query text, popup visibility, loading, empty, and error state stay distinct.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccombobox/snippets/at_a_glance.py"
  title="Combobox at a glance"
/>

## Build a searchable single select

Pass `CComboboxOption` values. Add `name` only when the canonical value should
join native FormData.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccombobox/snippets/choose_a_moon.py"
  title="Choose a moon"
/>

```citry-html
<c-CCombobox
  name="moon_id"
  c-options="moons"
  placeholder="Search moons"
/>
```

```python
from citry_ui import CCombobox, CComboboxOption

moon_picker = CCombobox(
    name="moon_id",
    options=(
        CComboboxOption("europa", "Europa", "Icy moon of Jupiter"),
        CComboboxOption("titan", "Titan", "Moon with a dense atmosphere"),
    ),
)
```

`value` is the stable identity. `label` is visible and filterable text.
`description` adds optional supporting text. Duplicate labels are allowed;
values must be unique.

Opening a local Combobox whose text still mirrors its selection shows all
options, so the trigger can choose a replacement. Once the user edits the
text, it filters normally. An explicitly controlled `inputValue` is always a
search query.

Use `CField` for the accessible label, description, error, required state, and
shared Form state. Do not use `placeholder` as the only label.

## Configure Combobox

Server inputs are passed in Python through `<c-CCombobox ... />` attributes or
a `CCombobox(...)` composition call. Client inputs are passed in the browser
through `$c-props="{...}"`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccombobox/snippets/configuration.py"
  title="Configure Combobox"
/>

`variant`, `size`, `filter`, `clearable`, `open_on_focus`, and
`auto_highlight` have matching client inputs. A valid client input wins. Remove
it to return configuration to the server value.

`value`, `inputValue`, and `open` behave differently: each is independently
controlled while supplied. Removing query or popup control preserves its last
committed state. `value=null` is an intentional controlled empty selection.

`auto_highlight` only moves the active option. It does not select on blur or
Tab. `min_chars` applies to popup visibility and remote loading, including
trigger and keyboard opening.

## Search remote options

Pass `loadOptions` through client props. It receives the committed query, an
AbortSignal, and a request ID. Return one complete valid item array.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccombobox/snippets/remote_catalog.py"
  title="Search a star catalog"
/>

```citry-html
<c-CCombobox
  c-min_chars="2"
  c-debounce_ms="250"
  $c-props="{
    loadOptions: async ({ query, signal, requestId }) => {
      const response = await fetch(`/stars?q=${encodeURIComponent(query)}`, {
        signal,
      });
      return await response.json();
    },
  }"
/>
```

A new qualifying query aborts the previous request. Request identity still
rejects stale results when a loader ignores abort. Closing, reset, disabled or
read-only state, replacement, and cleanup also abort work.

Replacing `loadOptions` aborts its current request. A valid replacement loads
the current qualifying query when the popup is open; `null` returns to local
filtering.

Use the `loading`, `empty`, and `error` slots to match surrounding language.
Errors never render exception text. A later valid query can recover.

Remote mode bypasses local filtering. For local data, choose `contains`,
`starts_with`, or `none`. Matching is plain case-insensitive text matching, not
locale-aware or fuzzy search.

## Control browser state

Control selection, query, and popup independently. Every callback reports the
affected axis, reason, ownership, and browser source.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccombobox/snippets/controlled_state.py"
  title="Control a mission target"
/>

```citry-html
<c-CCombobox
  $c-props="{
    value: targetId,
    inputValue: targetQuery,
    open: targetOpen,
    onValueChange: (value, detail) => targetId = value,
    onInputValueChange: (query, detail) => targetQuery = query,
    onOpenChange: (open, detail) => targetOpen = open,
  }"
/>
```

An uncontrolled axis commits before its callback. A controlled callback is a
request; update the matching client input to accept it. Owner commits do not
notify again. Selecting an option requests value, label query, then close in
that order, but controlling one axis never takes ownership of another.

If a selected value temporarily has no item, its canonical value and last
known label survive. A later matching item rehydrates the label without a
callback. This supports options that arrive after selection.

## Use native Forms and validation

`name` adds a hidden canonical input. The visible text input owns native
validation but never submits its label.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccombobox/snippets/form_destination.py"
  title="Submit a launch destination"
/>

Required validity needs a selected option, not merely typed text. Disabled
Comboboxes are omitted from FormData. Read-only Comboboxes keep their value but
cannot edit, open, select, or clear.

An uncanceled native reset restores uncontrolled server values. Controlled
axes reassert their browser values after the reset turn. A canceled reset does
nothing.

Before browser activation, the visible input is read-only. If scripts fail,
the displayed label cannot change while an old hidden key is submitted. The
server must still verify that every submitted key is allowed.

Browser autofill is treated as text input. It clears an old canonical value and
never guesses identity from a label, including duplicate labels.

## Use the keyboard

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccombobox/snippets/keyboard_navigation.py"
  title="Navigate constellations"
/>

- ArrowDown and ArrowUp open and move across enabled options with wrap.
- Home and End move to the first or last enabled option while open.
- Enter selects the highlighted option.
- Escape closes without selecting.
- Tab closes and continues native focus order without selecting.
- Printable keys, IME, editing shortcuts, and horizontal arrows remain native.

DOM focus stays on the input. `aria-activedescendant` exposes the highlighted
option. Pointer selection keeps input focus through the commit. The trigger and
clear actions are outside sequential Tab order so the composite uses one Tab
stop.

## Theme and customize Combobox

Use `class_`, `style`, public CSS variables, or documented selectors. Do not
target private `.cui-*` classes.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccombobox/snippets/theme_customization.py"
  title="Theme a deep-sky picker"
/>

Variables inherit, so a container can theme several Comboboxes. Set one on the
root for an isolated override. Public selectors such as
`[data-citry-ui-part="option-description"]` target stable elements. Reflected
attributes such as `data-open`, `data-loading`, `data-selected`, and
`data-highlighted` expose current styling state.

The popup stays under the component and inherits its theme. It does not use the
browser top layer yet, so an ancestor with clipped overflow may clip it.

## Support narrow, translated, and directional content

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccombobox/snippets/environment.py"
  title="Explore long celestial names"
/>

Logical properties support RTL. Labels and descriptions wrap inside the
scrollable popup. Default colors support light and dark schemes and retain
boundaries and highlight in forced colors.

Version 1 targets ordinary collections up to 1,000 items. Grouping,
virtualization, infinite loading, multiple selection, free values, create-new,
and arbitrary option rendering remain separate later work.
