---
title: CommandPalette
description: Search and run grouped application commands in a modal dialog.
---

# CommandPalette

Use `CCommandPalette` for a finite collection of application commands that
people can search and run without leaving their current task. It combines a
native modal Dialog, one editable combobox, and grouped listbox options. The
application still owns command registration, authorization, routing, and side
effects.

## Open and run a command

Pass immutable records through `entries`, give the Dialog a visible `label`,
and handle values with `onAction`. The activator slot receives
`activator_attrs` and `activator_disabled`. Spread the complete attribute map
on one ordinary native activator. For `CButton`, also pass
`c-disabled="activator_disabled"` because Button owns its disabled state.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/basic_command_palette.py"
  title="Open and run a command"
  source_open
/>

Commands are callback-only options. They are not links, selected form values,
or Menu items. Use a native navigation list or Menu when people need link
semantics, modifier keys, a browser context menu, or copyable destinations.

## Build records in Python

`CCommandPaletteCommand`, `CCommandPaletteGroup`, and
`CCommandPaletteSeparator` are frozen value records. They do not render alone.
Command values stay globally unique across top-level entries and groups.
Separators are visual boundaries between top-level regions.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/python_command_records.py"
  title="Build command records in Python"
/>

## Search labels and aliases

Filtering normalizes labels, keywords, and the exact query with NFKC, collapses
Unicode whitespace, trims, and applies locale-neutral lowercase. A command
matches when the whole normalized query appears in its label or one keyword.
Descriptions, shortcut hints, values, and slot content are not searched.
Matches keep their server order and are never fuzzy-ranked.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/search_and_empty.py"
  title="Search aliases and empty results"
/>

## Show disabled commands and shortcut hints

Disabled commands remain visible and searchable, expose disabled option state,
and are skipped by active navigation. `shortcut` is presentational text only.
The component never registers that key combination.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/disabled_and_shortcuts.py"
  title="Show disabled commands and shortcut hints"
/>

Use `intent="danger"` to give a destructive command visual emphasis. It does
not authorize the action or bypass disabled state.

## Add safe visual adornments

The `item_start` and `item_end` slots receive immutable
`CCommandPaletteItemSlotData`. Their output is decorative, inert, and hidden
from the accessibility tree. Keep the owned label and description as the
command's complete semantic content. Interactive controls, links, meaningful
images, form controls, and custom elements are rejected.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/command_adornments.py"
  title="Add safe visual adornments"
/>

## Control open state and query text

Client `open` and `query` values own independent axes while supplied. User
edits and dismissals are requests through `onQueryChange` and `onOpenChange`.
If the owner retains its old value, the input, results, active command, focus,
and Dialog remain on that accepted state.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/controlled_command_palette.py"
  title="Control open state and query text"
/>

A completed close clears the uncontrolled query exactly once. A declined
controlled close preserves it. Releasing a controlled value with `null` or by
omitting it continues from the last accepted fallback, never rejected browser
text or the original server seed.

## Choose action and close policy

`onAction(value, detail)` runs synchronously before an optional close request.
The root `close_on_action` default can be overridden by one command. Callback
return values are ignored. If the callback throws, the close step does not run.
If it deliberately moves focus, that connected focus destination wins over
Dialog return-focus behavior.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/command_actions.py"
  title="Choose action and close policy"
/>

## Own global shortcuts in the application

CommandPalette installs no document or window shortcut listener. The
application decides how `Mod+K` behaves around editable controls, composition,
multiple palettes, operating-system reservations, and shortcut collisions,
then updates controlled `open`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/application_shortcut.py"
  title="Own a global shortcut in the application"
/>

Shortcut text inside a command is a hint, not a binding or authorization rule.

## Keep Forms and IME input safe

The search input has no name, value contribution, reset behavior, or validity.
Every noncomposing Enter is contained before an ancestor Form can submit,
including empty and all-disabled results. During composition, Arrow, Enter,
and Escape remain with the IME and cannot navigate, act, clear, or dismiss.
The final committed text produces at most one query request.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/form_safe_palette.py"
  title="Keep Forms and IME input safe"
/>

An action callback may explicitly submit application data. The palette itself
never calls `requestSubmit()` or changes FormData.

## Compose with modal and anchored layers

CommandPalette uses the same native Dialog controller as `CDialog`. A nested
Dialog becomes the topmost focus owner. Popovers opened from a command close
before the palette. Escape closes only the deepest owned layer, and ordinary
close restores the eligible deep-focus invoker.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/palette_layers.py"
  title="Compose with modal and anchored layers"
/>

The Dialog stays in its authored Document or open ShadowRoot. Closed
ShadowRoots, cross-document adoption, invalid anatomy, and hostile ownership
changes fail closed.

## Adapt size, direction, and environment

`size` coordinates surface width, input height, and row density. Public
variables and part selectors support application styling. Logical layout keeps
start/end decoration correct in RTL, while vertical command order remains
unchanged.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccommand_palette/snippets/command_palette_environment.py"
  title="Inspect responsive and environment behavior"
/>

The active option stays visible at narrow widths, 200% and 400% zoom, with a
virtual keyboard, coarse pointer, text spacing, reduced motion, and forced
colors. The modal palette is hidden in print.

Without JavaScript, a server-closed palette stays closed. A server-open native
Dialog remains readable in document flow without claiming modality. Its search
input remains disabled and commands do not run, so it cannot submit an
ancestor Form or promise unavailable interaction.

## Distinguish callbacks from native events

`onOpenChange`, `onQueryChange`, and `onAction` are component callbacks passed
through `$c-props`. Native input, composition, keyboard, pointer, click,
Dialog cancel, and close events remain browser events. The family dispatches no
custom DOM event.

`attrs` target the native Dialog. `input_attrs` target the owned search input
and accept only attributes that cannot replace its identity, value, disabled
state, Form boundary, combobox relationships, or active descendant. Mappings
are copied once. Labels, descriptions, keywords, shortcut hints, and values are
escaped text, not HTML or authorized domain actions.

<!-- UI_LIBRARY_API_REFERENCE -->
