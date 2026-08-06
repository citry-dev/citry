# Citry UI repeatable contact workflow

**Status (2026-07-30): Phase 7 acceptance composition.** This is an
application fixture, not a public Citry UI component. It combines the
production Form, Field, Input, Combobox, and Button families with Citry Events
to test behavior that isolated family examples cannot establish.

## 1. Business scenario

An administrator edits an ordered escalation team. Every contact row has a
stable business ID, required email address, and required role selection. The
administrator can add a contact, reorder the list, remove a contact, correct
native validation failures, and submit the resulting nested browser form.

The scenario deliberately keeps text-entry values in native controls instead
of copying every keystroke into server state. Citry Events owns only the row
collection and order. This proves that server updates can change collection
structure without erasing unrelated browser-owned edits.

## 2. Composition and identities

The application component renders one `CForm`. Each row is an ordinary
application `<section>` with `#c-key` set to its stable contact ID. It contains:

- one required `CField > CInput` email control;
- one required `CField > CCombobox` role control;
- one `CButton` that removes that contact.

The form names use the application's native bracket convention:
`contacts[<id>][email]` and `contacts[<id>][role]`. Citry UI preserves these
names and `FormData` ordering but does not parse them into Python objects.

The Events state stores the ordered IDs, the next generated ID, and an
optional post-mutation focus target. Add, remove, and reverse-order handlers
return a fresh rendering of the workflow. They never receive or echo the
current text inputs, which is the key edit-preservation pressure.

## 3. Mutation and focus policy

- Add appends a new stable ID and focuses its email input after replacement.
- Reorder reverses the rows. A focused surviving input remains the exact keyed
  DOM node with its value and selection.
- Remove deletes one stable ID. When the triggering remove button disappears,
  focus moves to the email input at the former position, then the previous
  row, then the Add contact button when the collection becomes empty.
- The browser's live `form.elements`, native validity, and `FormData` reflect
  added, removed, and reordered controls without a parallel Citry registry.

The post-removal target is application policy, not a hidden Form feature. The
fixture implements it in its own client initializer so the library does not
guess what a collection mutation means.

## 4. Validation and submission

Email uses native `type=email` plus `required`. Role uses the Combobox's native
hidden canonical value and visible constraint-validation control. A native
submit with an incomplete row is blocked and focuses an invalid control. A
complete submit reaches the normal `submit` event, and `FormData` contains the
current nested names and canonical role values in visible row order.

Citry Events powers the collection mutations on the same form. This scenario
does not claim that Events' form argument codec parses bracket notation.
Applications that need nested typed Event inputs must map their own flat wire
schema or use a future documented codec extension.

## 5. Public contracts under pressure

The fixture locks onto these existing public contracts only:

- native Form, Input, Button, and Combobox semantics;
- browser-owned dynamic Form membership, native validity, and CForm cleanup;
- Field labels, descriptions, errors, IDs, and inherited required state;
- Combobox keyboard selection and canonical form value;
- documented component parts and tokens for inspection and branding;
- Citry `#c-key` identity and Events replacement behavior.

Row markup, contact IDs, bracketed names, action layout, and post-mutation
focus policy belong to the application and are not Citry UI API.

## 6. Acceptance evidence

The cross-browser workflow must prove:

1. initial controls appear in `form.elements` and expose the expected invalid
   names;
2. editing two existing rows survives an Events reorder, including exact DOM
   identity and focus for the active input;
3. adding a row adds two live Form controls and focuses the new email input;
4. removing a row removes both controls from `form.elements` and `FormData`,
   then applies the deterministic focus policy;
5. native submission is blocked while required data is missing;
6. a completed form submits nested email and canonical role values in current
   order; and
7. replacing or removing the whole workflow leaves no Citry UI listeners,
   timers, observers, requests, or detached-control references attached to
   live DOM.

Manual follow-up covers mobile email keyboards, autofill, zoom, and
representative screen-reader announcement of invalid fields and collection
changes. The fixture should become a docs live example only after its business
copy and teaching narrative are edited for the docs audience.
