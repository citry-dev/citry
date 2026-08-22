# Form Collection

**Status:** accepted implementation contract for the first production pass.
Research refreshed 2026-08-21.

## 1. Purpose and product bar

`CFormCollection` groups a repeatable ordered set of field groups inside one
real application form. `CFormCollectionItem` declares one stable key, plain
label, fields, and optional mutation controls. It does not render a nested
`form`, parse field names, clone initialized component DOM, or own application
records.

```html
<form method="post">
  <c-CFormCollection label="Email addresses" action_name="contacts_action">
    <c-CFormCollectionItem value="primary" label="Primary address">
      <c-CInput name="contacts[primary][email]" type="email" />
    </c-CFormCollectionItem>
  </c-CFormCollection>
</form>
```

The same family supports one repeated field or a multi-field group. Nested
collections compose as content but are not specially coordinated in v1.

## 2. Prior art and complaints

| Product or standard | Surface inspected | Decision |
|---|---|---|
| Phoenix LiveView 1.2 `inputs_for` | persistent IDs, sort parameters, named insert/remove buttons, server rerender | Adopt stable keys and real named mutation buttons. |
| Django current formsets | management data, deletion, ordering, min/max validation | Adopt explicit min/max control availability, but do not invent a field-name codec. |
| Symfony current `CollectionType` | `allow_add`, `allow_delete`, prototypes, entry types, list reindexing | Adopt add/remove configuration and flexible entry content. Reject cloning an initialized prototype in v1. |
| Rails current nested attributes | `fields_for`, stable record IDs, destruction markers | Preserve application-owned names and hidden identity fields. |
| Existing Citry repeatable-contact workflow | keyed morphs, edit/focus preservation, native validation and FormData | Promote the repeated-group anatomy and controls without hiding application state. |
| Vuetify 3 | no first-class form-array family | Use Field, Button, Card, and density styling as comparison only. |

The family addresses nested forms, opaque index rewriting, lost edits after
rerender, icon-only unnamed controls, validation blocking an add/remove
request, and focus loss caused by unstable identity.

## 3. Public composition and anatomy

```text
CFormCollection -> fieldset
|- legend
|- optional description
|- ol
|  `- CFormCollectionItem -> li/section[role=group]
|     |- header: label and mutation buttons
|     `- consumer fields
`- Add button
```

Items must be direct logical declarations and values must be unique. Consumer
fields remain normal descendants of the outer application form. The Item is
retained because key, label, controls, focus destination, and content must stay
one record.

## 4. Server inputs and client inputs

Root inputs are `id`, required `label`, optional `description`, `action_name`,
`add_value`, `allow_add`, `allow_remove`, `allow_reorder`, `min_items`,
`max_items`, `disabled`, `size`, localized action labels, and root styling
inputs. Item inputs are `value`, `label`, `remove_value`, `move_up_value`,
`move_down_value`, `removable`, `movable`, `disabled`, and Item styling inputs.

`action_name=None` renders `type=button` controls for client callbacks.
Supplying it renders submit buttons with `name`, encoded or explicit value, and
`formnovalidate`. Client inputs are `disabled` and `onAction`. Invalid client
values are diagnosed and the last valid value remains.

## 5. State model

The component owns no record collection state. DOM declaration order is the
current order. Clicking a control sends one request. Named submit buttons let
the outer form/server receive the request without JavaScript. With enhancement,
`onAction(detail)` receives it before normal submission unless the callback
calls `preventDefault()` on the source event. The component never assumes the
request succeeded. The owner returns a keyed rerender.

Min/max values disable Add/Remove controls based on the current rendered count.
Disabled roots or Items suppress their actions but not their consumer form
fields; applications disable fields separately when that is intended.

## 6. Slots and slot data

Root default accepts Item declarations only. Item default receives
`{value, label, index, count, is_first, is_last, disabled}` and must contain the
actual field group. Optional `header` content may accompany the owned label,
but cannot replace the label or controls.

## 7. Callbacks, native events, and methods

`onAction(detail)` receives `{action, value, index, toIndex, sourceEvent}`.
Action is `add`, `remove`, `move-up`, or `move-down`; value is null for Add.
The callback may update Alpine state, send a Citry Event, or permit the named
submit button to continue. No custom DOM event or imperative method ships.

## 8. Semantics, keyboard, focus, and assistive technology

The root is a native fieldset with a visible legend. Each Item is a list item
containing `role=group` labeled by its visible heading. Controls are native
buttons in normal Tab order. Disabled actions use native `disabled`. A keyed
rerender preserves a focused surviving field. After Add or Remove, the
application chooses the focus target because only it knows the new record.

## 9. Native forms and validation

The family never nests a form. Consumer controls determine submitted data and
validation. Mutation submit buttons use `formnovalidate`, so incomplete fields
do not block adding, removing, or reordering. `action_name` and action values
are plain application protocol. Buttons are successful controls only when
activated. The family does not parse bracket notation, renumber names, or add
deletion markers.

## 10. Styling and theme contract

Parts are `form-collection`, `legend`, `description`, `items`, `item`,
`item-header`, `item-label`, `item-actions`, `item-content`, and `add`.
Variables cover gap, Item surface/border/radius, action gap, focus color, and
disabled opacity. Reflections are `data-size`, `data-disabled`, `data-count`,
`data-first`, and `data-last`.

## 11. Environmental behavior

Logical layout supports RTL. Action controls wrap instead of squeezing Item
content. Long labels and 400 percent zoom remain usable. Forced colors retain
borders/focus; reduced motion removes transitions; print hides mutation
controls but prints all fields. Catalog messages own action text; application
labels and fields keep their language and direction.

## 12. Overlay and layering behavior

The family creates no overlay. Consumer fields may compose their own overlays
under their normal ownership contracts.

## 13. Collections, async data, and identity

Stable unique Item values are required and should also be used in `#c-key` by
the application owner. Requests may be asynchronous; the component does not
optimistically mutate or globally lock. Applications may expose pending state
through `disabled`. Out-of-order server results remain the application's Event
or request-supersession responsibility.

## 14. Server render, morph, and cleanup

Server output is fully useful. Enhancement only installs delegated click and
prop-effect listeners. Cleanup releases both. A keyed morph can reorder Items
without recreating surviving native controls; removing the focused Item needs
an application-selected focus fallback.

## 15. Security and content trust

Citry escapes labels and content by default. Values reject U+0000, CR, and LF.
General attrs cannot replace IDs, roles, runtime markers, form button protocol,
or browser-expression ownership. No HTML strings, cloning, `innerHTML`, or
dynamic code execution are used.

## 16. Assets and performance

One small delegated-listener runtime and one CSS asset are family-owned. No
observer, timer, or global listener is retained. Static named-button operation
remains complete without JavaScript. The family and catalog asset budgets are
enforced by the shared asset report.

## 17. Acceptance matrix

Evidence covers schema, nesting and duplicates, one real form, arbitrary field
names, min/max buttons, native named actions, `formnovalidate`, callback detail,
disabled state, keyed edit/focus preservation, add/remove/reorder rerenders,
native validation and FormData, i18n, RTL, environmental modes, cleanup, docs,
assets, wheel content, axe, and three browsers. Manual evidence covers screen
reader grouping and server-error recovery.

Examples are basic repeated emails, multi-field contacts, Citry Events
requests, Alpine callbacks, native form actions, and min/max/disabled behavior.

## 18. Compatibility classification

Component names, inputs, slots, action detail, form button protocol, message
keys, public parts/variables/reflections, and validation errors are stable.
Grouping semantics, request-only ownership, and useful server output are
behavioral contracts. Exact styling and private markers may evolve.

## 19. Public documentation contract

`cform_collection/api.md` is the guide and references shared executable
snippets. `api.yml` exhaustively records Inputs, Slots, Events, CSS,
Attributes, Selectors, Interfaces, then Translation keys.

## 20. Open decisions and deferred work

A Citry-safe server-supplied fragment/prototype API and coordinated nested
collections are deferred. Client cloning is not a hidden fallback. A future
form codec may understand structured names, but this UI family will continue
to preserve native names verbatim.

## 21. Internationalization

Catalog keys cover Add, Remove Item, Move Item up, and Move Item down. Item is
a typed plain label variable. Stable buttons use `$c-tr`; explicit label props
remain fixed application text. No locale-sensitive sorting or parsing occurs.
