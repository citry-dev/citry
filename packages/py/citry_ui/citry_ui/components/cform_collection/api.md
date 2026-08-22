---
title: Form Collection
description: Compose keyed repeatable field groups inside one real form with accessible add remove and reorder requests.
---

# Form Collection

Use `CFormCollection` for an ordered set of repeated fields or repeated
multi-field groups. It never creates a nested form. Put it inside your normal
`form` or `CForm`, and keep names, parsing, records, and persistence in the
application.

## Repeat one field

Each `CFormCollectionItem` has a stable `value`, a visible `label`, and ordinary
form controls in its default slot.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cform_collection/snippets/at_a_glance.py" title="Collect several email addresses" />

The component does not rewrite indexes or bracketed names. Choose stable keys
when an edit must survive a keyed server rerender.

## Repeat a multi-field group

An Item may contain any coherent set of fields. All controls remain direct
members of the one outer form for native validation, autofill, reset, and
`FormData`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cform_collection/snippets/field_groups.py" title="Edit several contacts" />

Nested collections may be placed inside Item content, but the first release
does not coordinate their action protocols or focus policy.

## Handle requests with Citry Events

Set `action_name` to turn Add, Remove, Move up, and Move down into real named
submit buttons. Each uses `formnovalidate`, so an incomplete new row does not
block a collection mutation. The server reads the activated button's value and
returns a keyed rerender.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cform_collection/snippets/server_actions.py" title="Send collection actions through the outer form" />

The docs preview accepts those named requests locally because this static page
has no application endpoint. In an application, let the named submit continue
and return the updated keyed collection from the server.

Defaults encode `add`, `remove:<value>`, `move-up:<value>`, and
`move-down:<value>`. Override each value when your server protocol differs.
For example, `remove_value="delete:member-17"` makes the Remove button submit
`team_action=delete:member-17`. The colon has no Citry-specific meaning; the
whole string is simply the application-defined value of the activated submit
button.

## Handle requests in Alpine

Without `action_name`, controls use `type=button`. Pass `onAction` through
`$c-props` to receive `{action, value, index, toIndex, sourceEvent}` and update
application state or send a Citry Event.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cform_collection/snippets/client_actions.py" title="Apply client collection requests" />

The component deliberately does not clone existing component DOM. The owner
must add, remove, or reorder records and render the resulting keyed Items.
The preview emulates that owner locally. It creates stable records for new
phone fields and keeps removed Items connected while applying the same callback
details, so Add remains unbounded and edits survive reorder and restoration on
this static page.

## Limit available actions

`min_items` and `max_items` guard Remove and Add controls. Root `disabled`
disables mutation controls without silently disabling consumer fields.
`removable`, `movable`, and Item `disabled` refine one group.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cform_collection/snippets/limits.py" title="Keep required and fixed groups" />

If the entire form group must stop submitting, disable its actual native
controls or an application-owned ancestor fieldset too.

## Preserve edits and choose focus

Citry keyed rerenders can retain surviving native controls, their browser-owned
edits, selection, and focus while Items reorder. After adding or removing an
Item, the application chooses the new focus target because it owns the new
record and business policy.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cform_collection/snippets/accessibility.py" title="Label repeated shipping addresses" />

The fieldset, legend, grouped Items, and native buttons provide the semantic
baseline. Action labels come from Citry UI catalog messages; application Item
labels and fields retain their own locale and direction.

<!-- UI_LIBRARY_API_REFERENCE -->
