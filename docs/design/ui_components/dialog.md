# Citry UI Dialog specification

**Status (2026-08-06): production contract, implementation, automated evidence,
structured reference, and public examples complete; human visual, assistive-
technology, and real-device review remain.**
`CDialog` is a styled native modal Dialog. It keeps the browser's top-layer,
inertness, native Form, and focus-restoration behavior, then adds predictable
dismissal, focus looping, responsive sizing, scrolling, theming, and cleanup.

## 1. Purpose and product bar

`CDialog` presents a task or decision that blocks interaction with the page
until the user completes or dismisses it. It must work without consumer CSS,
retain useful server-rendered output, contain keyboard focus, support nested
Dialogs, preserve its authored theme, and undo every document mutation.

Production-complete means:

- a native `<dialog>` supplies modal semantics, the top layer, background
  inertness, native close events, `method="dialog"`, and the restoration target;
- Citry supplies consistent forward and reverse focus looping across supported
  browsers, scoped dismissal, nested-instance isolation, and page scroll lock;
- server and browser inputs produce the same DOM, behavior, and styling;
- controlled owners may accept or decline every user-authored open change;
- long content, narrow viewports, zoom, light and dark schemes, forced colors,
  and right-to-left content remain usable; and
- all public parts, variables, reflected attributes, slot data, and callback
  detail are documented and tested.

Common jobs are first-class:

| Job | Shortest contract |
|---|---|
| Open from a control | spread `activator_attrs` on a Button in the `activator` slot |
| Present a named modal task | provide the required `title` and `default` slots |
| Add supporting context | provide a short plain-language `description` slot |
| Offer explicit actions | spread `close_attrs` on cancel or completion actions |
| Control visibility in browser code | pass `open` and `onOpenChange` through `$c-props` |
| Prevent passive dismissal | set `dismissible=False`; explicit action bindings still work |
| Allow Escape but not backdrop dismissal | set `close_on_outside=False` |
| Focus long structured content first | set `initial_focus="title"` |
| Focus a specific control first | put native `autofocus` on that control |
| Keep actions visible over long content | use the default `scroll="body"` |
| Scroll the complete surface | set `scroll="dialog"` |
| Close a native Form and read its result | use `method="dialog"`; inspect callback `returnValue` |
| Fill the viewport | set `size="full"` |
| Adjust dimensions or visual design | set public variables, `class_`, `style`, or allowed `attrs` |

Template use:

```citry-html
<c-CDialog size="md">
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">
      Open atlas
    </c-CButton>
  </c-fill>
  <c-fill name="title">
    Celestial atlas
  </c-fill>
  <c-fill name="default">
    ...
  </c-fill>
</c-CDialog>
```

Python composition:

```python
from citry_ui import CDialog

atlas = CDialog(
    size="md",
    slots={
        "title": "Celestial atlas",
        "default": atlas_content,
    },
)
```

An AlertDialog, Drawer, Popover, global Dialog service, transition system, and
generic positioning engine are separate products. A headless Dialog API is
parked until real application use establishes a useful contract.

## 2. Prior art and complaints

The family was re-audited from its runtime, render and browser tests, quality
scenario, structured API, public guide, and composed uses. Existing behavior
remained provisional wherever those artifacts disagreed.

### Source record

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI prototype | 2026-08-06 | `cdialog.py`, browser tests, `dialog.states`, `api.md`, and `api.yml` | Keep the native modal, controlled/uncontrolled ownership, reason-bearing callback, reference-counted scroll lock, and token model. Repair nested event leakage, focus semantics, scrolling, size names, and native Form results. |
| HTML Living Standard | reviewed 2026-08-06 | [Dialog element](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element) | `showModal()`, top-layer behavior, close requests, `returnValue`, focus steps, removal cleanup, and browser-owned focus restoration. |
| MDN | reviewed 2026-08-06 | [Dialog element](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog) | Do not put `tabindex` on `<dialog>`; preserve native `autofocus`, Form, and modal behavior. |
| WAI-ARIA APG | reviewed 2026-08-06 | [Modal Dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) | Accessible naming, forward and reverse focus looping, Escape, visible close action, initial focus choices, and description guidance. |
| Vuetify | 4.1.7 source reviewed 2026-08-06 | [`VDialog.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.7/packages/vuetify/src/components/VDialog/VDialog.tsx) and `VOverlay` composables | Confirm controlled state, activator composition, persistent mode, scrolling, fullscreen, nested overlay ordering, scroll strategies, focus retention, restoration, dimensions, and transitions. Prefer native modality and focused Citry inputs over the full overlay-prop inheritance tree. |
| Chakra UI | current docs reviewed 2026-08-06 | [Dialog](https://chakra-ui.com/docs/components/dialog) | Confirm compound anatomy, controlled and store use, nested Dialogs, initial focus, inside/outside scrolling, placement, sizing, lazy mounting, and motion breadth. Keep one native component and slots instead of many administrative wrappers. |
| React Spectrum | current docs reviewed 2026-08-06 | [Dialog](https://react-spectrum.adobe.com/Dialog) | Confirm standard sizes, dismissible and non-keyboard-dismissible modes, specialized AlertDialog/fullscreen variants, replaceable regions, and programmatic containers. Keep AlertDialog and global mounting separate. |
| Web Awesome | current docs reviewed 2026-08-06 | [Dialog](https://webawesome.com/docs/components/dialog/) | Confirm light dismissal, header actions, footer, label, show/hide lifecycle detail, preventable close, and SSR. Use Citry callback ownership instead of a second custom-event protocol. |
| Browser interoperability | Chromium, Firefox, and WebKit checked 2026-08-06 | local native `<dialog>` focus probe; [`closedby` support](https://caniuse.com/mdn-html_elements_dialog_closedby) | Native engines do not provide the same focus-loop result at each boundary. Keep a scoped loop. Safari lacks the current `closedby` contract, so keep Citry dismissal gates. |
| Overlay issue reports | reviewed 2026-08-06 | [Radix focus-scope stack overflow #3432](https://github.com/radix-ui/primitives/issues/3432), [Radix nested Select focus #3520](https://github.com/radix-ui/primitives/issues/3520), [Reka keyboard regression #2756](https://github.com/unovue/reka-ui/issues/2756), and [Mantine iOS modal focus/scroll #8928](https://github.com/mantinedev/mantine/issues/8928) | Treat nested ownership, focus cleanup, focusable discovery, scroll containment, and cross-browser evidence as release contracts rather than implementation details. |

Common shortcomings informed the contract:

- portal roots can lose inherited theme, environment, and ownership context;
- parent overlay listeners can mistake nested triggers and close actions for
  their own;
- custom focus scopes can omit valid targets, recurse, leak, or fight nested
  overlays;
- native focus restoration cannot truthfully be disabled by a wrapper after
  `showModal()` has recorded its target;
- a Boolean scroll option does not distinguish fixed-header body scrolling
  from whole-surface scrolling;
- body scroll locks can leak, overwrite application styles, or release before
  the final nested overlay closes; and
- controlled state often emits callbacks for owner commits or closes before
  the owner accepts a request.

Citry adopts native modality, explicit reason-bearing requests, native
autofocus, a title-focus option, two scroll modes, and instance-scoped markers.
It rejects arbitrary root polymorphism, portal relocation, a fake
`restore_focus` switch, selector-shaped initial focus, a partial imperative API,
and dependence on unsupported `closedby` behavior.

Vuetify carries roughly 30% of the comparative decision weight:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` | direct client API | `open`, `onOpenChange` | adopt controlled and uncontrolled ownership |
| `activator` slot and props | scoped slot data | `activator`, `activator_attrs` | adopt without activator wrapper |
| `persistent` | direct API | `dismissible=False` | adopt the user job with positive close-action escape hatch |
| `retainFocus` | required overlay behavior | scoped focus loop | always retain while modal; no disabling switch |
| focus restoration | native HTML plus interoperability fallback | browser close target, repeated only when an engine omits restoration | adopt without a disabling switch |
| `fullscreen` | direct API | `size="full"` | adopt with concise naming |
| `scrollable` | direct API | `scroll="body"` or `"dialog"` | expand into explicit useful modes |
| width, max-width, height, max-height | CSS or utility classes | public variables, `style`, `class_` | omit dedicated inputs |
| location, origin, absolute, contained | separate overlay families | none | omit from modal Dialog |
| attach and teleport | authored DOM plus native top layer | none | reject relocation for this family |
| scrim color and opacity | CSS | `--cui-dialog-backdrop` | support through token |
| z-index and overlay stack | native top layer | nested native Dialogs | use platform stacking |
| close on back | integration | none | defer browser-history integration |
| transitions | separate motion contract | none | defer |
| eager/lazy mounting | server composition and conditional rendering | native Citry control flow | no Dialog-specific input |
| loader and async operation | composition | Button loading and app state | Dialog does not own async work |
| default slot props | named slot bindings | `close_attrs` in actions | expose the common explicit-close job |

## 3. Public composition and anatomy

```citry-html
<c-CDialog>
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">
      Read the field notes
    </c-CButton>
  </c-fill>
  <c-fill name="title">
    Aurora field notes
  </c-fill>
  <c-fill name="description">
    Observations from the northern ridge.
  </c-fill>
  <c-fill name="default">
    ...
  </c-fill>
  <c-fill name="actions" data="{ close_attrs }">
    <c-CButton
      variant="ghost"
      c-attrs="close_attrs"
    >
      Done
    </c-CButton>
  </c-fill>
</c-CDialog>
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CDialog` | native modal `<dialog>` | `class_`, `style`, and allowed `attrs` merge onto the Dialog | required `title` labels the Dialog; optional `description` describes it |

The authored host is private and uses `display: contents`. Activator content is
rendered directly. The native Dialog contains `surface`, `header`, `title`,
optional `close`, optional `description`, `body`, and optional `actions`
elements. Only documented selectors and relationships are stable.

`class_` and `style` accept Citry's structured values. `attrs` accepts other
native Dialog, ARIA, `data-*`, and Alpine attributes. It may contribute class
and style values, which merge with the direct inputs. It cannot replace `id`,
`open`, `role`, `aria-label`, `aria-modal`, `aria-labelledby`, `aria-describedby`,
`data-open`, `data-size`, `data-scroll`, `data-citry-ui-part`, private behavior
markers, `tabindex`, `popover`, or `closedby`.

The title and default slots are required. The activator is optional because an
owner may control `open`. Any number of Dialog instances may be nested through
ordinary slot content. Markers from a nested Dialog belong only to the nearest
Dialog host.

The anatomy review found no public administrative component to remove. The
private host is required to scope activators, close actions, ownership, and
cleanup but carries no public layout or selector promise.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `id` | `str` or `None` | generated | structural server-only | sets native identity and title, description, and activator relationships |
| `open` | `bool` | `False` | initial controlled-state fallback | renders the initial `open` state; valid client `open` controls later state |
| `dismissible` | `bool` | `True` | reactive configuration fallback | shows the built-in close control and permits passive dismissal |
| `close_on_escape` | `bool` | `True` | reactive configuration fallback | permits Escape and equivalent platform cancel requests when dismissible |
| `close_on_outside` | `bool` | `True` | reactive configuration fallback | permits a press that begins and ends on this Dialog's backdrop when dismissible |
| `initial_focus` | `auto` or `title` | `auto` | reactive configuration fallback | uses native autofocus/focus steps or focuses the fixed title on open |
| `size` | `sm`, `md`, `lg`, or `full` | `md` | reactive configuration fallback | sets the responsive surface size |
| `scroll` | `body` or `dialog` | `body` | reactive configuration fallback | scrolls only content or the complete surface |
| `close_label` | non-empty `str` | `Close` | structural server-only | names the built-in close Button |
| `class_` | Citry class value or `None` | `None` | structural server-only | merges consumer classes onto the native Dialog |
| `style` | Citry style value or `None` | `None` | structural server-only | merges consumer inline styles onto the native Dialog |
| `attrs` | mapping or `None` | `None` | structural server-only | merges allowed native and consumer attributes onto the native Dialog |

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `open` | Boolean | uncontrolled from current committed state | uncontrolled from current committed state | log once and become uncontrolled | native open state, scroll lock, focus, `data-open`, and activator `aria-expanded` |
| `dismissible` | Boolean | server fallback | invalid, server fallback | log once per invalid episode and use server fallback | built-in close and passive dismissal |
| `closeOnEscape` | Boolean | server fallback | invalid, server fallback | same | platform cancel requests |
| `closeOnOutside` | Boolean | server fallback | invalid, server fallback | same | backdrop requests |
| `initialFocus` | enum | server fallback | invalid, server fallback | same | focus placement on the next opening |
| `size` | enum | server fallback | invalid, server fallback | same | `data-size` and CSS |
| `scroll` | enum | server fallback | invalid, server fallback | same | `data-scroll` and overflow behavior |
| `onOpenChange` | function | no callback | no callback | log once and ignore | user-authored open requests only |

A valid client prop wins. Removing a configuration prop returns that field to
its server fallback. Removing `open` preserves the last committed visible
state and makes later requests uncontrolled. Owner updates do not notify the
owner again. Invalid fields do not disable independent valid fields. Server
rerenders reset server fallbacks and preserve the normal Citry instance and
client-prop lifecycle.

## 5. State model

| Current state | Trigger | Guard | Commit and effects | Callback |
|---|---|---|---|---|
| closed, uncontrolled | owned activator | none | open, claim scroll lock, update activators, place focus | `true`, reason `trigger` |
| open, uncontrolled | built-in close | `dismissible` | close with empty return value and release lock | `false`, reason `close-button` |
| open, uncontrolled | explicit `close_attrs` action | none | close with action Button value when present | `false`, reason `action` |
| open, uncontrolled | platform cancel | `dismissible` and `close_on_escape` | close | `false`, reason `escape` |
| open, uncontrolled | same-Dialog backdrop press | `dismissible` and `close_on_outside` | close | `false`, reason `outside` |
| open, uncontrolled | native Form or direct native close | none | reconcile native state and release lock | `false`, reason `native` |
| either, controlled | any user request | same guards | retain supplied `open`; owner may later commit | requested value and reason |
| either | owner changes `open` | valid Boolean | commit without notification | none |

The callback detail contains `reason`, `controlled`, `source`, and
`returnValue`. Opening resets the native return value. Explicit action Buttons
use their `value` when present. Native `method="dialog"` submission reports the
submitter value through the later native close reconciliation.

Repeated owner commits to the current value do nothing. A controlled owner
declines a request by retaining its prop. A native close cannot be held open by
controlled browser state, so CDialog immediately reconciles to closed and
notifies with `reason="native"`; the owner must update its prop before the next
reactive pass.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CDialog` | `activator` | no | one | `{activator_attrs: dict[str, object]}` | omitted |
| `CDialog` | `title` | yes | one | `{}` | none |
| `CDialog` | `description` | no | one | `{}` | omitted with no `aria-describedby` |
| `CDialog` | `default` | yes | one | `{}` | none |
| `CDialog` | `actions` | no | one | `{close_attrs: dict[str, object]}` | omitted |
| `CDialog` | `close` | no | one | `{}` | built-in close icon |

`activator_attrs` contains `aria-haspopup="dialog"`, `aria-controls`, the
server-visible `aria-expanded`, and a private ownership marker. The runtime
updates `aria-expanded` for every owned activator. `close_attrs` contains a
private explicit-close marker. Spread either mapping onto the intended native
or Citry UI Button.

The `close` slot replaces only the icon content inside the built-in close
Button. It does not replace the accessible Button, label, behavior, or public
`close` selector. Its content must remain non-interactive. Slot data is a
server-render snapshot. Dynamic slots do not apply.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onOpenChange` | `(requestedOpen, detail)` | owned trigger, built-in close, explicit action, Escape, outside press, or native close | after an uncontrolled commit; before a controlled owner commit | reports the request without changing supplied state, except unavoidable native close reconciliation | return value does not cancel; retain controlled `open` to decline ordinary requests |

`detail` is `{reason, controlled, source, returnValue}`. Reasons are `trigger`,
`close-button`, `action`, `escape`, `outside`, and `native`. Native `cancel` and
`close` events remain observable through Alpine `@...` listeners. CDialog emits
no custom DOM event.

No public component method is needed. The native Dialog remains available to
browser refs, but direct `showModal()`, `show()`, `requestClose()`, and
`close()` calls are outside the controlled-state contract. Direct native close
is reconciled safely; opening imperatively can bypass CDialog bookkeeping.

## 8. Semantics, keyboard, focus, and assistive technology

The root is a native modal `<dialog>` labelled by the required visible title.
The optional description supplies `aria-describedby` only when present.
Structured or lengthy body content should not be placed in the description
slot because announcing it as one description is difficult to understand.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| closed | activate owned trigger | request open | native autofocus/first focus target, or title | native Button behavior continues |
| open | `Tab` on last owned tabbable | wrap forward | first owned tabbable | yes |
| open | `Shift+Tab` on first owned tabbable | wrap backward | last owned tabbable | yes |
| open with no tabbables | `Tab` or `Shift+Tab` | remain contained | title in title mode; otherwise native Dialog focus target | yes when a usable target exists |
| open | `Escape` or platform cancel | request close when allowed | browser restores the previously focused connected element after close | yes; CDialog owns the request |
| open | backdrop pointer sequence | request close when allowed | browser restoration after close | yes when committed |

`initial_focus="auto"` preserves native `[autofocus]` and browser Dialog focus
steps. `initial_focus="title"` gives the title `tabindex="-1"` and focuses it
without scrolling after modal entry. CDialog never adds `tabindex` to the
Dialog itself.

Focus-loop discovery includes enabled, rendered native focus targets in this
Dialog, excludes targets inside nested Dialogs, respects positive `tabindex`
ordering, and handles the key event only when this native Dialog is the nearest
Dialog ancestor. The native close algorithm defines the restoration target.
Citry records the same target before `showModal()` and focuses it only when an
engine does not restore it. A workflow that needs a different destination may
focus it after the close callback.

The built-in close Button is visible whenever dismissible and has the
consumer-supplied accessible label. A non-dismissible Dialog must contain an
explicit completion or cancel action unless the owner has another documented
way to close it.

## 9. Native forms and validation

Forms in the default slot retain native validation, submit events, reset,
`FormData`, and Citry Events. A Form with `method="dialog"` requests closure
after successful submission and supplies the submitter value as the Dialog
return value. Uncontrolled closure remains native. In controlled mode, CDialog
intercepts only the final close so the owner can accept or decline it. The
callback reports the value with `reason="native"`.

Applications performing asynchronous work should control `open`, set Button
loading state, retain the Dialog on validation or transport failure, and close
only after success. Explicit `close_attrs` are appropriate for cancel or for a
completion action that is already safe to close. They must not be placed on a
submit Button when closing before submission completion would lose feedback.

Server `open=True` produces visible non-modal content without JavaScript
because only `showModal()` enters the top layer. Client activation upgrades it
immediately. Closed content remains in the DOM.

## 10. Styling and theme contract

The Dialog follows [`../ui_theme.md`](../ui_theme.md).

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-dialog-backdrop` | color | modal backdrop | light/dark theme value |
| `--cui-dialog-background` | color | surface background | light/dark theme value |
| `--cui-dialog-foreground` | color | surface text | light/dark theme value |
| `--cui-dialog-border-color` | color | surface boundary | light/dark theme value |
| `--cui-dialog-radius` | length | surface corner radius | `0.875rem` |
| `--cui-dialog-shadow` | shadow | surface elevation | theme shadow |
| `--cui-dialog-inline-size` | length | responsive preferred width | size-specific |
| `--cui-dialog-max-block-size` | length | maximum non-full height | `calc(100dvb - 2rem)` |
| `--cui-dialog-padding` | length | region padding | `1.25rem` |
| `--cui-dialog-gap` | length | region spacing | `1rem` |
| `--cui-dialog-close-size` | length | close Button target | `2.5rem` |
| `--cui-dialog-close-radius` | length | close Button corner radius | `0.5rem` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="dialog"]` | native Dialog and attribute destination | open, size, scroll | contains surface |
| `[data-citry-ui-part="surface"]` | visual surface | all | fills Dialog root |
| `[data-citry-ui-part="header"]` | title and built-in close layout | all | first surface region |
| `[data-citry-ui-part="title"]` | accessible visible title | all | labels Dialog |
| `[data-citry-ui-part="description"]` | concise accessible description | when slot supplied | describes Dialog |
| `[data-citry-ui-part="close"]` | built-in close Button | dismissible | inside header |
| `[data-citry-ui-part="body"]` | primary content | all | between description/header and actions |
| `[data-citry-ui-part="actions"]` | action layout | when slot supplied | final surface region |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-open` | present or absent | effective native open state |
| `data-size` | `sm`, `md`, `lg`, `full` | effective responsive size |
| `data-scroll` | `body`, `dialog` | effective overflow mode |

Public variables are inherited inputs resolved through private effective
variables. Defaults use low-specificity rules in the Citry UI layer. Full size
fills the dynamic viewport and does not retain ordinary radius or shadow.
Classes remain private; only the selectors above are public.

## 11. Environmental behavior

Default light and dark schemes supply legible surface, text, border, backdrop,
and focus colors. A nested opposite `color-scheme` scope remains effective
because native top-layer painting does not relocate the Dialog in the DOM.

Layout uses logical properties. Header, title, actions, and body wrap at narrow
widths and high zoom. `body` scrolling keeps header and actions visible;
`dialog` scrolling keeps the complete surface reachable. Full size uses
dynamic viewport units. Forced-colors mode preserves a visible surface border,
close control, and focus outline. Reduced motion has no required animation.
Coarse pointers retain the same outside start-and-end rule. Print omits closed
Dialogs and uses ordinary flow for an explicitly open Dialog where supported.

The only library-authored visible string is the default `close_label` value,
`Close`. Locale selection and translation remain separate follow-up work.

## 12. Overlay and layering behavior

The native Dialog stays in its authored DOM ancestry and enters the browser
top layer through `showModal()`. The browser supplies background inertness and
top-layer ordering. CDialog adds one page-scroll-lock claim per open instance.

Each instance handles only elements whose nearest private Dialog host is that
instance. Each focus key event belongs only to the nearest native Dialog.
Nested Dialogs therefore cannot trigger, close, or trap focus through a parent
instance accidentally. Closing a parent closes its open descendants from the
deepest level first, preventing an invisible modal from retaining top-layer
inertness or a scroll-lock claim. Top-layer order decides the visually active
Dialog.

The first open CDialog stores exact inline `overflow` and scrollbar
compensation values on the document root. The final close restores them.
Nested closes release only their own claim. Outside dismissal requires a
pointer sequence that both starts and ends on this Dialog's backdrop; dragging
from content to backdrop does not close it.

## 13. Collections, async data, and identity

Dialog owns no collection or asynchronous operation. Application code owns
loading, cancellation, supersession, errors, retry, and when a controlled
Dialog closes. Stable `id` links the native Dialog, title, description, and
owned activators. Nested Dialog identity and markers remain isolated.

## 14. Server render, morph, and cleanup

Closed server output retains semantic content in an inert native Dialog. Open
server output is visible but non-modal without JavaScript; activation calls
`showModal()` and establishes the complete contract.

Repeated initialization must not duplicate listeners, focus transitions, or
scroll claims. Same-identity morphs preserve the normal Citry client-data
lifecycle. Cleanup removes host and Dialog listeners, releases this instance's
scroll claim, closes any top-layer Dialog, and clears instance records. Native
close restoration applies when its stored target remains eligible. Removal
leaves no top-layer entry, stale activator state, global listener, or inline
page mutation.

## 15. Security and content trust

Slots follow Citry escaping and trusted-fragment rules. `initial_focus` is a
closed enum, not a selector or executable expression. Consumer mappings cannot
replace owned identity, modality, ARIA relationships, public mirrors, or
private markers. `source` in callback detail is a browser object and must not
be serialized as trusted data automatically. `returnValue` is ordinary
consumer-controlled Form or Button text and must be escaped when later shown.
Closed content remains in the DOM and follows the same trust policy as visible
content.

## 16. Assets and performance

The family adds one shared CSS asset and one JavaScript initializer when used.
It adds no request, CDN asset, icon font, observer, or Node runtime. Each
instance owns bounded event listeners; all instances share one scroll-lock
record.

Qualification records raw, gzip, and Brotli assets, repeated open/close
behavior, nested isolation, and retained resources after removal. These are
diagnostic budgets, not reasons to build outsized benchmark infrastructure.
The private `display: contents` host avoids a layout wrapper.

## 17. Acceptance matrix

Automated evidence currently covers:

- schema validation, required slots, generated identity, rejected owned attrs,
  exact slot-data records, and public exports;
- representative server render for open state, dismissal, title/description,
  size, scroll, custom close content, and class/style merging;
- controlled and uncontrolled triggers, explicit action, Escape, outside
  press, drag-out protection, repeated requests, and invalid controlled open;
- native autofocus, title focus, forward and reverse focus wrapping, nested
  Dialog focus isolation, and native focus restoration;
- nested trigger/action isolation, parent-close cleanup, scroll-lock reference
  counting, controlled and uncontrolled `method="dialog"`, return values,
  stale controlled native-close suppression, and removal cleanup;
- public variables, selectors, reflected attributes, ancestor overrides,
  narrow viewport, and long content with or without optional regions;
- docs schema, snippets, projections, links, packaging exclusions, axe, and
  supported Chromium, Firefox, and WebKit behavior.

Manual evidence covers keyboard-only use, VoiceOver/Safari, NVDA/Firefox or
Chrome, touch and coarse-pointer outside interaction, 200% and 400% zoom, text
spacing, forced colors, RTL, real mobile dynamic viewports, visual hierarchy,
copy, and final API polish.

## 18. Compatibility classification

Stable public API includes `CDialog`, all server and client input names and
meanings, slots and exact data shapes, callback and detail fields, dismissal
reasons, size and scroll values, variables, selectors, reflected attributes,
validation errors, and owned-attribute policy.

Native modal semantics, the native restoration target, scoped focus looping,
controlled requests, no-JavaScript output, native Form behavior, nested
isolation, and cleanup are behavioral contracts. Exact colors, spacing,
shadows, and private markup may evolve without changing those meanings.
`.cui-*` classes, `--_cui-*` variables, host and behavior markers, listener
organization, and scroll-lock storage are private.

## 19. Public documentation contract

[`cdialog/api.md`](../../../packages/py/citry_ui/citry_ui/components/cdialog/api.md)
is the reader-first guide. Its sibling `api.yml` is the exhaustive structured
reference. The guide teaches anatomy and a working Dialog first, then
controlled state, dismissal, focus, long content, native Forms, nested
Dialogs, and customization. It does not author an API reference in Markdown.

The page uses one coherent astronomy field-guide theme and the shared
[`preview contract`](./_preview.md). Planned examples are:

| Example | Reader task and visible states | Controls and interaction | Contract coverage | Source |
|---|---|---|---|---|
| Dialog at a glance | compare closed triggers and `sm`, `md`, `lg`, `full` surfaces | open each; close by Button | styling, scale, basic focus | `at_a_glance.py` |
| Open a field note | compose title, description, body, and actions | open, cancel, complete | ordinary anatomy and slot bindings | `open_field_note.py` |
| Configure a sighting | inspect effective size, scroll, and dismissal | controls for size, scroll, dismissible, Escape, outside | client precedence and reflected output | `configuration.py` |
| Own visibility | accept or decline a requested close | controlled toggle and request log | controlled state and callback detail | `controlled_dialog.py` |
| Place initial focus | compare native autofocus and title focus | mode control, repeated opens | initial focus and accessible structure | `initial_focus.py` |
| Read a long expedition log | keep header/actions fixed or scroll the full surface | scroll-mode control | long content, narrow layout, zoom | `long_content.py` |
| Record an observation | submit native choices and inspect result | `method="dialog"` submitters | Form close, native event, return value | `dialog_form.py` |
| Open a nested chart | open and close two Dialog levels independently | nested triggers and actions | ownership, focus, top layer, scroll refcount | `nested_dialogs.py` |
| Require an explicit decision | block passive dismissal | try close, Escape, backdrop, then action | non-dismissible workflow | `explicit_decision.py` |
| Customize the observatory | replace close icon and override variables/parts | theme control | close slot, CSS variables, selectors | `theme_customization.py` |
| Explore a narrow viewport | verify full size and wrapped actions | viewport profile and open | dynamic viewport, responsive behavior | `narrow_dialog.py` |

Every interactive example uses `c-ui-demo`, renders the result before source,
keeps source collapsed by default, and has focused browser evidence. API data
defines Inputs, Slots, Events, Methods, CSS, Attributes, Selectors, and
Interfaces with stable entry IDs.

## 20. Open decisions and deferred work

- AlertDialog needs distinct urgency semantics, focus guidance, and examples.
- Drawer, Popover, non-modal Dialog, generic positioning, and a global Dialog
  service need separate specifications.
- Motion waits for a library-wide transition and reduced-motion contract.
- Browser-history close integration waits for a router/history extension.
- Localization owns the default close label in follow-up work.
- A future headless API and portal host require real application evidence and
  must preserve theme context, nested ownership, focus, and cleanup.
