# Citry UI AlertDialog specification

**Status (2026-08-10):** implementation pass complete. Runtime, structured
reference, public previews, quality fixture, three-engine browser evidence,
and package wiring are checked in. Manual release evidence remains pre-release
work.

## 1. Purpose and product bar

`CAlertDialog` interrupts the current workflow with an important message that
requires one immediate response. Typical jobs are destructive confirmation,
irreversible state changes, session-expiry acknowledgement, and blocking error
confirmation.

It is not persistent `CAlert`, a general-purpose `CDialog`, a Toast, or a
browser `confirm()` wrapper. The production bar is a real modal native Dialog,
`role="alertdialog"`, required name and description relationships, safe initial
focus, an explicit cancel/action pair, exact controlled ownership, and reuse of
the proven Dialog focus, modality, scroll-lock, and nested-close behavior.

```citry-html
<c-CAlertDialog id="delete-project">
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs" intent="danger">Delete project</c-CButton>
  </c-fill>
  <c-fill name="title">Delete this project?</c-fill>
  <c-fill name="description">This permanently removes all project data.</c-fill>
  <c-fill name="cancel" data="{ cancel_attrs }">
    <c-CButton c-attrs="cancel_attrs" variant="outline">Keep project</c-CButton>
  </c-fill>
  <c-fill name="action" data="{ action_attrs }">
    <c-CButton c-attrs="action_attrs" intent="danger">Delete</c-CButton>
  </c-fill>
</c-CAlertDialog>
```

## 2. Prior art and complaints

Sources reviewed on 2026-08-10:

- WAI-ARIA APG Alert and Message Dialogs requires a modal `alertdialog`, an
  accessible name, and `aria-describedby` pointing to the alert message.
- WAI-ARIA APG Modal Dialog supplies the focus loop, Escape, and return-focus
  behavior.
- Radix AlertDialog separates Trigger, Title, Description, Cancel, and Action,
  supports controlled state, and distinguishes Cancel visually from Action.
- Material UI exposes `role="alertdialog"` on Dialog and recommends it only for
  urgent interruptions that require acknowledgement.
- existing Citry UI `CDialog` already owns native `showModal()`, focus trapping,
  focus restoration, nested close, controlled native-close repair, scroll lock,
  environmental CSS, and action-close attributes.

Citry adopts explicit title, description, cancel, and action slots while
avoiding a second modal runtime. Unlike general Dialog, AlertDialog has no
outside dismissal and no built-in corner close. Complex forms, browsing, and
multi-step content remain CDialog jobs.

## 3. Public composition and anatomy

`CAlertDialog` is one public component. It renders an owned host, optional
activator, and native `<dialog role="alertdialog">`.

| Part | Element | Ownership |
|---|---|---|
| host | `div` with `display: contents` | lifecycle and activator boundary |
| alert dialog | native `dialog` | `class_`, `style`, `attrs`, role, modality, open state |
| surface | `div` | layout and bounded scrolling |
| header/title | `header > h2` | required accessible name |
| description | `div` | required alert message and accessible description |
| body | `div`, optional | supplemental noninteractive content |
| actions | `footer` | required cancel then action decisions |

The native Dialog ID is supplied by `id` or generated as
`cui-alert-dialog-<render-id>`. Title and description IDs derive from it.

## 4. Server inputs and client inputs

### Server inputs

| Input | Type | Default | Class | Effect |
|---|---|---|---|---|
| `id` | `str | None` | `None` | structural | exact native Dialog and relationship prefix |
| `open` | `bool` | `False` | initial value | initial modal visibility |
| `close_on_escape` | `bool` | `True` | reactive configuration | permits Escape as the cancel-equivalent dismissal |
| `size` | `"sm" | "md" | "lg"` | `"sm"` | reactive configuration | bounded decision surface width |
| `scroll` | `"body" | "dialog"` | `"body"` | reactive configuration | overflow owner |
| `class_` | `CClassValue | None` | `None` | structural | native Dialog classes |
| `style` | `CStyleValue | None` | `None` | structural | native Dialog inline styles |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | trusted native Dialog attrs after owned rejection |

Full-screen size is intentionally absent. An urgent two-decision prompt should
remain concise; use CDialog for full-screen work.

### Client inputs

| Input | Type | Omitted/null | Invalid | Effect |
|---|---|---|---|---|
| `open` | boolean | releases to internal state | current state plus one episode diagnostic | controlled visibility |
| `closeOnEscape` | boolean | server fallback | fallback plus one episode diagnostic | Escape policy |
| `size` | enum string | server fallback | fallback plus one episode diagnostic | geometry |
| `scroll` | enum string | server fallback | fallback plus one episode diagnostic | overflow owner |
| `onOpenChange` | function | no callback | ignored plus one episode diagnostic | visibility requests |

Controlled behavior and detail reuse `CDialogOpenChangeDetail`: `reason` is
`trigger`, `escape`, `action`, or `native`; `controlled`, `source`, and
`returnValue` are included. Cancel and action Button clicks both report
`reason="action"`; `returnValue` distinguishes `"cancel"` and `"action"`.

## 5. State model

Uncontrolled activation opens immediately. Controlled activation reports a
request and waits for the supplied value. Omission releases control while
preserving effective state. Native close, rapid close/reopen, stale props, and
cleanup follow CDialog's generation-safe rules.

Outside pointer interaction never closes AlertDialog. Escape requests cancel
only when `close_on_escape=True`. Cancel and action controls close through the
same owned action path. Button-native handlers run before `onOpenChange`, so an
application may perform its domain action and then accept or reject closure.

## 6. Slots and slot data

| Slot | Required | Data | Contract |
|---|---|---|---|
| `activator` | no | `{activator_attrs, activator_type}` | exactly one native Button or CButton consumes the mapping and native Button type |
| `title` | yes | `{}` | noninteractive phrasing content |
| `description` | yes | `{}` | concise noninteractive alert message |
| `default` | no | `{}` | supplemental noninteractive flow content |
| `cancel` | yes | `{cancel_attrs, cancel_type}` | exactly one native Button or CButton consumes the mapping and native Button type |
| `action` | yes | `{action_attrs, action_type}` | exactly one native Button or CButton consumes the mapping and native Button type |

Owned attribute mappings include close markers, return values, and `autofocus`
on Cancel. The adjacent `*_type` field supplies form-safe `type="button"` to a
native Button. CButton already owns a safe Button type. Authored event listeners
remain available on the actual Buttons.

## 7. Callbacks, native events, and methods

Only `onOpenChange(nextOpen, detail)` is component-owned. Native Button click
events are the application action/cancel surface; no duplicate `onConfirm` or
custom DOM event is added. The native Dialog `close` event remains available
through attrs. No public method is added; controlled state owns programmatic
visibility.

## 8. Semantics, keyboard, focus, and assistive technology

The native Dialog explicitly uses `role="alertdialog"`, `aria-modal="true"`,
`aria-labelledby` to the required title, and `aria-describedby` to the required
message. Cancel receives initial focus. This avoids placing initial focus on a
destructive action and keeps the complete short message announced with the
Dialog.

Tab and Shift+Tab loop through focusable decisions. Escape requests closure
when enabled. Closing restores the connected activator unless application code
has deliberately moved focus. The family never marks an alertdialog modal
without actually using `showModal()` and an obscuring backdrop.

## 9. Native forms and validation

Owned cancel and action attributes force `type="button"`, so AlertDialog does
not accidentally submit an ancestor Form. Complex form prompts belong to
CDialog. Applications may perform asynchronous domain work from the action
Button and keep `open` controlled until it settles.

## 10. Styling and theme contract

AlertDialog reuses the Dialog layout implementation but exposes family-specific
variables:

`--cui-alert-dialog-backdrop`, `--cui-alert-dialog-background`,
`--cui-alert-dialog-foreground`, `--cui-alert-dialog-border-color`,
`--cui-alert-dialog-radius`, `--cui-alert-dialog-shadow`,
`--cui-alert-dialog-inline-size`, `--cui-alert-dialog-max-block-size`,
`--cui-alert-dialog-padding`, and `--cui-alert-dialog-gap`.

Stable parts are `alert-dialog`, `surface`, `header`, `title`, `description`,
`body`, and `actions`. Public mirrors are `data-open`, `data-size`, and
`data-scroll`. Defaults match CDialog except the default size is `sm`.

## 11. Environmental behavior

Dialog's logical layout, nested color schemes, narrow viewport clamping,
400-percent zoom, forced colors, print, reduced motion, and touch behavior are
inherited. Long title/message text wraps. The action row wraps without
horizontal overflow and retains Cancel before Action in DOM and visual order.

## 12. Overlay and layering behavior

The family uses the native modal top layer and shared Dialog modal stack. It
locks page scrolling once, closes nested modal descendants deepest-first, and
restores lock state on final close. Opening suppresses unrelated anchored
layers through the shared modal coordinator. AlertDialog never portals or
creates a second overlay coordinator.

## 13. Collections, async data, and identity

There is no owned collection. Applications may update message text while open,
but changing the decision meaning should close and open a new AlertDialog so
assistive technology receives a fresh interruption. Async action state is
composed in the action Button and controlled `open` state.

## 14. Server render, morph, and cleanup

Closed server HTML contains a native Dialog without falsely exposed modality.
Open server HTML is normalized through `showModal()` at activation. Correlated
rerenders preserve controlled/internal visibility under the Dialog runtime.
Cleanup removes listeners, closes descendants and native modal state, releases
scroll lock, and restores focus only when still appropriate.

## 15. Security and content trust

Direct strings are de-trusted and escaped. Attrs reject case-insensitive static
and dynamic aliases for role, ID, open, aria-modal, name/description IDREFs,
popover, owned mirrors, and runtime markers. Structural Alpine directives and
whole-object ownership spreads are rejected consistently with CDialog. Slot
markup uses the ordinary trusted-template boundary but settled action anatomy
requires the supplied mappings on native Buttons.

## 16. Assets and performance

AlertDialog reuses CDialog JavaScript and base CSS rather than shipping another
modal algorithm. Only a small family-specific template and variable mapping are
added. Asset reporting deduplicates identical inherited payloads. Scaling
covers closed instances, one open modal, nested cleanup, and listener/scroll
state returning to baseline.

## 17. Acceptance matrix

Automated evidence covers server anatomy, required slots, IDREFs, exact role,
native Button types/values/autofocus, attr rejection, open/closed output,
controlled accept/reject/release, trigger/cancel/action/Escape, outside refusal,
focus trap and restoration, native close, nested Dialog composition, modal
coordinator interaction, scroll lock, cleanup, three engines, axe, role/name/
description snapshots, variables/selectors, light/dark/RTL/narrow/zoom/forced
colors/print, API schema, previews, registration, wheel contents, assets, and
Ruff/Node syntax.

Manual release evidence covers VoiceOver/Safari, NVDA/Firefox or Chromium,
JAWS/Chromium, TalkBack, touch, browser zoom, and wording review for destructive
examples.

## 18. Compatibility classification

Stable: public inputs, slots, slot-data fields, callback detail, explicit
`alertdialog` relationships, native Button safety, parts, mirrors, variables,
focus destination, and no-outside-close policy. Private: classes, runtime
markers, shared JavaScript organization, scroll-lock bookkeeping, and
incidental wrappers.

## 19. Public documentation contract

The guide teaches confirmation vs Alert/Dialog choice, shortest usage,
controlled async action, Escape policy, native Button composition, focus,
styling, and accessibility. Examples cover deletion, blocking error,
controlled async work, variants/sizes, and customization without deliberately
supplying invalid state.

## 20. Open decisions and deferred work

Complex forms, more than two decisions, full-screen surfaces, wizard steps,
prompt text inputs, automatic timeout, and browser-like promise APIs remain
CDialog/application work. No unresolved decision blocks implementation.
