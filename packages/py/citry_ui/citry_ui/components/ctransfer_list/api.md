---
title: Transfer List
description: Build an ordered chosen set with an accessible, form-capable Citry UI PickList.
---

# Transfer List

Use `CTransferList` when people need to compare a finite set of available
items with an ordered chosen set. `CTransferListItem` declares stable values,
plain accessible labels, optional rich presentation, and disabled state.

## Move items between two lists

The enhanced component uses two labeled multi-select listboxes and explicit
buttons. Without JavaScript, the same values remain available through a native
`select[multiple]` form control.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctransfer_list/snippets/at_a_glance.py" title="Choose and order reviewers" />

Selection inside a pane is separate from the chosen form value. Select one or
more enabled options, then use Add or Remove. The Add all and Remove all
buttons can be omitted with `show_move_all=False`. Chosen items retain the
exact order in `value` and in submitted form entries.

## Render rich, noninteractive items

The Item default slot can replace its visible label with server-rendered
presentation. Keep `label` plain and descriptive because native fallback,
typeahead, and assistive naming use it.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctransfer_list/snippets/rich_items.py" title="Render rich Transfer List items" />

Do not place links, buttons, inputs, editable content, or other focus stops
inside an Item. The family follows the listbox interaction model and rejects
interactive descendants during enhancement.

## Control chosen values from Alpine

Pass `value` and `onValueChange` through `$c-props` for controlled state.
Transfer and reorder actions become requests: the visible order changes only
after the owner accepts the proposed array.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctransfer_list/snippets/controlled.py" title="Control a Transfer List" />

Omit client `value`, or set it to `null`, for uncontrolled behavior. In that
mode an accepted action updates the native form owner, emits native `input`
then `change`, and calls `onValueChange`.

## Submit and validate forms

Set `name` to submit one entry per chosen item in chosen order. `form` can
associate the control with a non-ancestor form. `required=True` requires at
least one chosen value and moves focus to the chosen list when native
validation fails.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctransfer_list/snippets/forms.py" title="Submit a required ordered selection" />

Native reset restores the server-rendered value. A disabled Item cannot be
moved or reordered. An initially chosen disabled Item remains submitted by
the native fallback through an ordered hidden option proxy.

## Keyboard and accessibility

Each pane has one tab stop and an active descendant. Arrow keys, Home, End,
typeahead, Space, Enter, Shift+Arrow range selection, and Ctrl/Cmd+A are
available. Explicit transfer and reorder buttons remain reachable in normal
tab order, so drag and drop is never required.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctransfer_list/snippets/accessibility.py" title="Use disabled items and accessible labels" />

The family announces accepted moves and reorders through a polite live region.
Pane labels, counts, controls, empty states, announcements, and required
validation use Citry UI catalog messages by default. Any explicit `*_label`
input belongs to the caller and does not switch with the Citry client locale.

## Responsive layout and customization

The three-column layout stacks automatically in a narrow container and uses
logical CSS properties for RTL. Customize the root and Items with `class_`,
`style`, and `attrs`, or use the documented public variables and part
selectors.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctransfer_list/snippets/customization.py" title="Customize Transfer List" />

`size` changes the default list height. Forced colors preserve selected-state
outlines, reduced-motion environments disable component motion, and print
hides action controls while retaining both supplied panes.

## Scope boundaries

This first family owns a complete finite server-rendered collection. It does
not fetch, filter, virtualize, group into a tree, expose read-only mode, or
provide drag and drop. Use `CMultiSelect` for compact selection and compose
application state with `CVirtualWindow` when the collection cannot be fully
rendered.

<!-- UI_LIBRARY_API_REFERENCE -->
