# Editable

**Status:** production implementation pass completed on 2026-08-10. Checked-in
server, three-engine browser, docs, quality-scenario, API-projection, and asset
evidence satisfy this contract; live assistive-technology and release visual
review remain human qualification work.

## 1. Purpose and product bar

`CEditable` turns one short text value into an explicit view/edit interaction.
It is for renaming titles, labels, and similarly compact strings in place. The
default visual treatment keeps the pencil, confirm, and cancel actions inside
the input-shaped surface at logical inline-end. `action_position="outside"`
places those actions beside the surface when an application needs a more
prominent control group.

Use `CInput` for ordinary always-editable data entry, `CTextarea` for long text,
and application-specific editors for rich text, async validation workflows, or
multi-field records.

## 2. Prior art and complaints

Reviewed 2026-08-10: Chakra UI and Ark UI Editable anatomy, activation,
controlled value/edit mode, submit modes, focus and keyboard; PrimeVue Inplace
view/content model; MUI Data Grid edit/view transitions and commit validation;
current Vuetify Text Field composition (no dedicated inline Editable); and the
repository's Input, Field, Form, Button, and client-control contracts.

Adopt explicit preview/input/action anatomy, draft-versus-committed state,
Enter save, Escape cancel, optional blur commit, controlled requests, native
form truth, and focus restoration. Avoid a headless multi-part declaration API:
Citry's common short-text job benefits from a polished complete recipe. Rich
preview/input slots, multiline mode, async pending state, and validation
callbacks are deferred to composition rather than hidden in a small control.

Vuetify disposition: Text Field append-inner affordances motivate the default
inside placement; external Button composition maps to `action_position`;
variants, density, disabled, readonly, validation, and native attributes map to
direct inputs or `input_attrs`. General utility styling remains outside scope.

## 3. Public composition and anatomy

One public `CEditable` renders a root `div`; an input-shaped preview surface
containing visible text and a native edit Button; an edit surface containing
one native text Input plus native submit/cancel Buttons; and no public child
components. Action icons are decorative while author-overridable labels name
their Buttons. All actions are `type=button`.

Before client initialization, only the native Input is visible and fully
operable. After successful initialization, exactly one view or edit surface is
visible. The same Input owns form value, validity, reset, and edit focus.

## 4. Server inputs and client inputs

Server inputs:

| Input | Type | Default | Contract |
|---|---|---|---|
| `value` | `str` | `""` | initial committed and native form value |
| `placeholder` | `str` | `"Click to edit"` | empty preview/input copy; author-localizable |
| `name`, `form`, `id` | `str | None` | `None` | native form and identity inputs |
| `editing` | `bool` | `False` | initial edit mode |
| `required`, `disabled`, `readonly`, `invalid` | `bool | None` | `None` | standalone state; Field owns when composed |
| `max_length` | `int | None` | `None` | native maximum length |
| `autocomplete`, `inputmode` | `str | None` | `None` | native text-input hints |
| `submit_mode` | `enter | blur | both | explicit` | `both` | commit triggers |
| `select_on_focus` | `bool` | `True` | select draft when edit begins |
| `action_position` | `inside | outside` | `inside` | visual action placement |
| `edit_label`, `submit_label`, `cancel_label` | `str` | English fallbacks | author-localizable Button names |
| `variant` | `outline | filled | plain` | `outline` | surface treatment |
| `size` | `sm | md | lg` | `md` | surface/action geometry |
| `class_`, `style`, `attrs` | trusted root attributes | empty | root customization |
| `input_attrs`, `preview_attrs` | trusted mappings | empty | bounded native destinations |

Client inputs mirror `value`, `editing`, state/config inputs and expose
`onValueChange` plus `onEditChange`. Supplied string `value` controls committed
value; supplied Boolean `editing` controls mode. `null` or omission releases
either channel to its current committed internal state. Configuration uses
server fallback when omitted.

## 5. State model

State is committed value, edit draft, view/edit mode, controlled ownership,
external/native invalid state, effective Field/Form/native-fieldset state, and
configuration. Entering edit snapshots committed value into the Input. Typing
changes only draft. Submit validates, requests/commits draft, then requests
view mode. Cancel restores committed value and requests view mode.

Controlled requests notify without mutating that channel. Owner changes during
editing update committed value but do not overwrite a dirty draft; cancellation
uses the newest committed value. A value owner accepting synchronously before
the edit-close request produces the accepted value without a stale flash.
Invalid client values diagnose once per continuous episode.

## 6. Slots and slot data

There are no slots. The finite text/input/action anatomy is owned so the
default stays polished, form-safe, and accessible. Rich preview or custom
editor composition is deliberately outside this family.

## 7. Callbacks, native events, and methods

`onValueChange(next, detail)` runs for submit and reset requests with
`value`, `previousValue`, `controlled`, source `submit | blur | reset`, and
native source event. `onEditChange(next, detail)` runs for edit, submit, cancel,
blur, reset, disabled, and readonly transitions with `editing`, `reason`,
`controlled`, `forced`, and source.

The native Input emits its ordinary `input` and `change` events while the user
edits it. Component commit is reported through `onValueChange`; it does not
synthesize a second native event pair. Programmatic controlled synchronization
and cancel emit no native events. There are no public methods.

## 8. Semantics, keyboard, focus, and assistive technology

The preview is ordinary text beside a native edit Button. Edit mode exposes one
native text Input and confirm/cancel Buttons. Button labels are real accessible
names; icon marks are `aria-hidden`. Enter commits when the submit mode includes
Enter and IME composition is inactive. Escape cancels. Tab follows ordinary
page order; a submit mode containing blur commits only when focus leaves the
whole component, never while moving among its actions.

Entering edit focuses the Input and optionally selects its contents. Submit or
cancel returns focus to the edit Button when still connected and enabled.
Forced disabled/readonly closure never focuses an unavailable action and leaves
focus at the nearest safe owner chosen by the browser.

## 9. Native forms and validation

The native text Input owns `name`, `form`, required/max-length validity,
FormData, and reset. In view mode it remains successful although visually
hidden. A required invalid submission enters edit mode, focuses the Input, and
exposes native/Field invalid state. Reset restores the server default value;
uncontrolled mode commits it, while controlled mode requests it. Reset always
requests view mode. Disabled contributes nothing; readonly remains successful.
Field and trusted static relationships merge onto the Input through
`aria-describedby` and active `aria-errormessage`; external or native invalid
state is reflected with `aria-invalid`.

## 10. Styling and theme contract

Variants are `outline`, `filled`, and `plain`; sizes are `sm`, `md`, and `lg`.
Public variables are `--cui-editable-background`, `--cui-editable-foreground`,
`--cui-editable-border-color`, `--cui-editable-hover-border-color`,
`--cui-editable-focus-color`, `--cui-editable-invalid-border-color`,
`--cui-editable-muted-color`, `--cui-editable-action-background`,
`--cui-editable-action-foreground`, `--cui-editable-radius`,
`--cui-editable-height`, `--cui-editable-padding`,
`--cui-editable-action-size`, and `--cui-editable-gap`.

Stable parts: `root`, `preview`, `preview-value`, `edit-action`, `edit-surface`,
`input`, `actions`, `submit-action`, and `cancel-action`. Stable reflections:
root `data-editing`, `data-empty`, `data-required`, `data-disabled`,
`data-readonly`, `data-invalid`, `data-submit-mode`, `data-action-position`,
`data-variant`, and `data-size`.

## 11. Environmental behavior

All alignment is logical: internal actions sit at inline-end in LTR and
inline-start in RTL. Long preview text wraps or truncates without page overflow;
outside actions wrap below at narrow widths. Live inherited color scheme,
forced colors, reduced motion, print, and 400% zoom remain coherent. Print
shows the committed preview without controls.

## 12. Overlay and layering behavior

Editable creates no overlay, top layer, scroll lock, inert subtree, or global
listener. It composes inside Dialog, Drawer, Popover, Menu content, Accordion,
Tabs, Table cells, and Cards without joining the anchored-layer coordinator.

## 13. Collections, async data, and identity

Each instance owns one scalar text value. Correlated retained-root
reinitialization preserves committed value, dirty draft, and edit mode when the
server value baseline is unchanged; a changed server baseline resets them.
Async saving, optimistic rollback, editable collections, and cross-row
coordination are application responsibilities.

## 14. Server render, morph, and cleanup

Server HTML is a valid native text Input fallback. Activation installs only
root/input listeners and bounded ancestor-fieldset observers. Cleanup removes
listeners/observers, invalid Field state, and the private readiness marker.
Generation checks prevent reset/blur work from mutating a replacement.

## 15. Security and content trust

All direct strings are de-trusted, canonicalized, and reject U+0000. Values and
labels render as text. Attribute mappings are copied and reject owned identity,
form/value/state, role/focus/visibility, action type, runtime markers, object
spreads, `x-model`, `x-show`, `x-html`, `x-text`, `x-if`, `x-for`, `x-ignore`,
and teleport ownership. Dynamic writers to owned ARIA relationships are
rejected; static description IDREFs are extracted and merged.

## 16. Assets and performance

One instance owns one native Input and three native Buttons, one root click and
focusout listener, native input/invalid/composition hooks, form reset, and
bounded fieldset observation. There is no shared runtime dependency. Quality
tools record raw/compressed family assets and bounded 1/10/100/500/1000 server
render/output diagnostics.

## 17. Acceptance matrix

Server tests cover public schema, progressive fallback, Field/Form ownership,
labels/relationships, attrs/security, string/ID validation, states, parts,
reflections, and tokens. Chromium/Firefox/WebKit tests cover edit/submit/cancel,
inside/outside actions, controlled reject/accept/release, draft preservation,
Enter/Escape/blur/Tab/IME, native FormData/reset/required invalid, fieldset,
RTL/narrow/theme/forced colors/print, retained cleanup, and Axe.

Manual release evidence remains VoiceOver/Safari, NVDA/Firefox or Chromium,
JAWS/Chromium, touch targets, live Safari Tab, 400% zoom, and Nu HTML.

## 18. Compatibility classification

Public: component/type names, inputs, callbacks, state transitions, native form
behavior, keyboard/focus, parts, reflections, variables, variants, sizes, and
default inside action placement. Private: readiness marker, generated IDs,
icon glyphs, exact transition mechanics, listener layout, and handoff storage.

## 19. Public documentation contract

Examples: at a glance rename; native form/reset; controlled save; explicit and
blur submit modes; inside default versus outside actions; states; variants and
sizes; keyboard; and brand customization. Docs browser evidence initializes
every preview, edits at least one value, confirms zero console/page errors,
and runs serious/critical Axe scans.

## 20. Open decisions and deferred work

- The default action position is `inside`; `outside` is the explicit opt-out.
- Actions use compact native Buttons rather than nested CButton instances so
  the family owns exact input geometry and avoids extra component lifecycle.
- English action/placeholder defaults are author-overridable until Citry UI's
  i18n contract lands; integrating catalog defaults is deferred to that pass.
- Multiline, rich preview/input slots, async pending/error protocols, arbitrary
  validators, and editable collections are deferred.

Changing draft/commit ownership, form truth, focus restoration, or the default
inside action anatomy requires another design review.

## 21. Internationalization

The previously deferred localization pass is complete. Placeholder, edit,
save, and cancel keys and overrides are recorded in the structured
[Translation keys table](../../../packages/py/citry_ui/citry_ui/components/ceditable/api.yml).
Stable action labels use `$c-tr`; the placeholder uses `i18n.bind()` because
the runtime writes it to both the editor and empty preview as state changes.
Each explicitly supplied label remains caller-owned.
