# Tour

**Status:** implementation contract accepted for a nonmodal, target-aware
product Tour. Highlighted targets remain usable. Cross-page persistence and
asynchronous wait steps are explicit deferred work.

## 1. Purpose and product bar

`CTour` guides a user through a short ordered explanation. `CTourStep`
declares either a centered step or a step attached to an existing page element.
The production bar is meaningful server HTML, controlled and uncontrolled
state, resilient target geometry, localized chrome, deterministic
missing-target behavior, direction-aware placement, focus restoration,
cleanup, visual progress, and useful default styling.

A Tour explains an interface; it does not block that interface. A targeted
step must leave the highlighted control available for pointer and keyboard
interaction, and the card must not cover the highlighted area when another
placement fits. Use `CDialog`, not Tour, when the user must finish or dismiss
an overlay before returning to the page.

The shortest intended template is:

```html
<c-CTour>
  <c-fill name="activator" data="{ activator_attrs }">
    <button c-bind="activator_attrs">Show tour</button>
  </c-fill>
  <c-fill name="default">
    <c-CTourStep value="welcome">
      <c-fill name="title">Welcome</c-fill>
      <c-fill name="default">A short introduction.</c-fill>
    </c-CTourStep>
    <c-CTourStep value="save" target_id="save-button">
      <c-fill name="title">Save changes</c-fill>
      <c-fill name="default">Use this action when you are ready.</c-fill>
    </c-CTourStep>
  </c-fill>
</c-CTour>
```

Python composition uses the same definitions and named slots. There is no
separate headless API.

## 2. Prior art and complaints

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| WAI-ARIA APG | reviewed 2026-08-21 | [Dialog (Modal) pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) | Do not claim modal semantics while the explained page remains usable. Name the dialog, focus its title on entry, provide explicit actions, support Escape, and restore focus without trapping Tab. |
| HTML | reviewed 2026-08-21 | native `<dialog>` API | Use `show()`, not `showModal()`. The element supplies dialog semantics without making the rest of the document inert. |
| Ant Design | 6.6.1, reviewed 2026-08-21 | [Tour docs/API](https://ant.design/components/tour/) and current source directory | Adopt target and centered steps, controlled current/open state, placement, progress dots, target scrolling, mask/spotlight geometry, semantic parts, lifecycle callbacks, and interactive targets by default. |
| Zag / Ark | 1.41.1, reviewed 2026-08-21 | [Tour docs](https://zagjs.com/components/react/tour) and current anatomy | Adopt separate backdrop, spotlight, positioner, content, progress, stable step IDs, missing-target handling, reasoned state changes, and cleanup. Target interaction is available unless an author deliberately prevents it; Citry's first API keeps it available. |
| Driver.js | current docs reviewed 2026-08-21 | [Configuration](https://driverjs.com/docs/configuration), [basic use](https://driverjs.com/docs/basic-usage), and changelog | Confirm offset/radius, progress, next/previous/close labels, scrolling, cleanup, and reduced-motion needs. Reject trusted title/description HTML and global selector strings. |
| React Aria | current docs reviewed 2026-08-21 | [Popover](https://react-aria.adobe.com/Popover) | Confirm custom-anchor positioning, explicit trigger semantics, and focus ownership. Tour remains a named dialog rather than pretending its card is a tooltip. |
| Citry UI | current source reviewed 2026-08-21 | declaration families, controlled-state conventions, i18n contract | Reuse declaration collection, exact-ID ownership, request/accept state, localization, diagnostics, and cleanup conventions. Keep Tour-specific target geometry local. |

Material complaints are a card covering the control it explains, target
disappearance, stale positioning after scroll or resize, unstyled or weak
actions, listener leaks, selector ambiguity, accidental outside dismissal, and
callbacks that cannot distinguish finish, skip, dismiss, or target failure.
The contract answers those with exact ID targets, collision-scored placement,
observer cleanup, pointer-transparent spotlight geometry, visible progress,
reason-bearing callbacks, and conservative outside dismissal.

## 3. Public composition and anatomy

`CTour > CTourStep` is the declaration relationship. The default Tour slot may
contain only direct step declarations and formatting whitespace. Nested Tours
are valid inside rendered content because declaration context is removed before
authored content renders.

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CTour` | host `<div>` containing native nonmodal `<dialog>` | `class_`, `style`, `attrs` reach the host | At least one direct `CTourStep`; unique step values. |
| `CTourStep` | active `<section>` inside the dialog surface | `class_`, `style`, `attrs` reach that section | Required `title` and default slots; optional exact target ID. |

Stable anatomy is host `tour`, native `dialog`, visual `spotlight`, positioned
`surface`, `arrow`, `close`, step `panel`, `media`, `header`, `title`,
`description`, `footer`, `progress-group`, `progress`, `steps`, `step-dot`, and
`actions`. Only the active panel is exposed. The dialog remains in the Tour
host; it is not portalled.

## 4. Server inputs and client inputs

`CTour` server inputs are `id: str | None`, `open: bool=False`,
`active: int=0`, `dismissible: bool=True`, `close_on_escape: bool=True`,
`close_on_outside: bool=False`, `skippable: bool=True`,
`scroll: "auto" | "smooth" | "none"="auto"`,
`missing_target: "skip" | "close"="skip"`, `size: "sm" | "md" | "lg"="md"`,
six string overrides (`close_label`, `previous_label`, `next_label`,
`finish_label`, `skip_label`, `progress_label`), and `class_`, `style`, `attrs`.
`active` must name a rendered step.

`CTourStep` server inputs are unique nonempty `value`, optional valid HTML
`target_id`, logical `placement`, `arrow: bool=True`, `describe: bool=False`,
and `class_`, `style`, `attrs`. No selector text is accepted.

Client inputs are `open: boolean | null`, `active: number | null`, the reactive
policy inputs (`dismissible`, `closeOnEscape`, `closeOnOutside`, `skippable`,
`scroll`, `missingTarget`, `size`), and callbacks `onOpenChange`,
`onActiveChange`. `null` or omission releases controlled open/active state to
the last committed value. Invalid values are diagnosed once per episode and
retain the current valid configuration. Open and active ownership are
independent.

## 5. State model

The Tour is closed or open at one active step. Opening resolves the requested
step and its target before showing the nonmodal dialog. A missing target either
advances in the requested direction until a valid or centered step is found,
or closes with `missing-target`; `missing_target="close"` closes immediately.
A successful step transition updates panel visibility, dialog relationships,
target scroll, spotlight, placement, progress, focus, public state, then
notifies.

Uncontrolled actions commit before callback. Controlled actions notify and
wait for the corresponding client prop. `finish` closes with `finish`; `skip`
closes with `skip`; close, Escape, outside, and activator use distinct reasons.
Same-value requests do nothing. Removing the active target uses the same
missing-target policy. Removal or morph disconnects all retained observers and
listeners.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---:|---:|---:|---|---|
| `CTour` | `default` | yes | one | `{}` | none; contains declarations |
| `CTour` | `activator` | no | one | `{activator_attrs}` | omitted |
| `CTour` | `close` | no | one | `{}` | decorative multiplication sign |
| `CTourStep` | `title` | yes | one | `{index, total, value}` | none |
| `CTourStep` | `default` | yes | one | `{index, total, value}` | none |
| `CTourStep` | `media` | no | one | `{index, total, value}` | omitted |

Slot data is server-render data. Browser navigation reveals pre-rendered slot
content and does not rerun Python slots.

## 7. Callbacks, native events, and methods

`onOpenChange(open, detail)` receives `{reason, active, value, controlled,
source}`. Reasons are `activator`, `close`, `escape`, `outside`, `skip`,
`finish`, `missing-target`, and `native`. `onActiveChange(active, detail)`
receives `{previousActive, value, previousValue, reason, controlled, source}`;
reasons are `next`, `previous`, `client`, and `missing-target`.

Callbacks cannot cancel. Controlled state is acceptance. The first release
exposes no imperative method because `$c-props` open/active state and native
activator composition cover Citry/Alpine orchestration without adding a second
retained controller lifecycle.

## 8. Semantics, keyboard, focus, and assistive technology

The browser-visible overlay is a native nonmodal `<dialog aria-modal="false">`
named by the active step title through `aria-labelledby`. `describe=True` adds `aria-describedby` to the
active description; the default omits it so structured body content is not
flattened into one announcement. The spotlight and progress dots are hidden
from assistive technology. Actions are native, form-safe buttons.

Opening and step changes focus the active title (`tabindex=-1`). Tab is not
trapped and may reach both Tour actions and application controls. Escape closes
only when dismissal and Escape dismissal are enabled. Closing restores focus
to the activator when it still exists. Arrow keys do not change Tour steps.

The full-viewport dialog and spotlight do not accept pointer input; the card
does. Consequently, clicking the highlighted control reaches that control.
`close_on_outside=True` may close the Tour from an outside pointer press, but
does not cancel the underlying page action. This is guidance, not modality.

## 9. Native forms and validation

Tour is not a form participant. Every built-in action uses `type=button`.
Authored controls inside a step retain native form semantics, but complex
transactions belong in a separate page or `CDialog`.

## 10. Styling and theme contract

Public variables are `--cui-tour-width`, `--cui-tour-background`,
`--cui-tour-foreground`, `--cui-tour-muted-color`, `--cui-tour-border-color`, `--cui-tour-shadow`,
`--cui-tour-radius`, `--cui-tour-padding`, `--cui-tour-gap`,
`--cui-tour-offset`, `--cui-tour-spotlight-padding`,
`--cui-tour-spotlight-radius`, `--cui-tour-backdrop-color`, and
`--cui-tour-focus-color`. Sizes select width fallbacks of 20, 26, and 30 rem.
Public parts are those named in section 3.

Host mirrors are `data-open`, `data-active`, `data-value`, `data-size`, and
`data-targeted`. Surface mirrors actual `data-placement`; panels mirror
`data-index`, `data-value`, `data-target-id`, `data-placement`, `data-describe`,
and active `data-current`. The current progress dot also receives
`data-current`.

## 11. Environmental behavior

Placement uses logical inline direction, tests the requested side and fallback
sides, rejects overlap with the padded target, then clamps within the viewport.
CSS lengths expressed in px, rem, em, vw/vh, or dvi/dvb are converted to real
pixel geometry. Long content scrolls within the card, target scrolling uses
`nearest`, and narrow viewports center a bounded card. Scroll, resize,
`ResizeObserver`, and target-removal changes schedule fresh geometry. Reduced
motion disables smooth movement. Forced colors retains borders and focus.
Touch actions remain at least 44 CSS pixels. Print hides Tour entirely.
The surface is an inline-size query container. At narrow card widths, including
author-customized widths, progress text and dots form one row above the action
group so neither group is compressed into unreadable columns.

Localized built-ins use component-owned English source messages. Exact prop
overrides omit their catalog bindings. Stable text and `aria-label` outputs use
server `tr()` plus `$c-tr`; progress passes numeric `current` and `total`
values captured per pre-rendered panel. Application title, body, and media
slots retain their own language, bidi, and formatting ownership.

## 12. Overlay and layering behavior

The nonmodal dialog is fixed over the viewport with pointer input disabled.
Its spotlight uses a large shadow to produce the visual mask, and its surface
re-enables pointer input. Targeted steps cut a pointer-transparent opening
around the target. Centered steps use a full backdrop. Outside dismissal
defaults off. No portal breaks logical ownership or inherited theme.

Tour deliberately does not use the shared modal Dialog controller: no page
inertness, focus trap, or scroll lock is wanted while a target remains usable.

## 13. Collections, async data, and identity

Steps are a finite server declaration collection with unique stable `value`
identity and numeric rendered order. Reordering across a morph follows values;
active numeric control is revalidated. Async wait steps, route transitions,
dynamic add/remove methods, and remote step content are deferred. Conditional
targets should open only after the application has rendered them.

## 14. Server render, morph, and cleanup

All step content renders on the server; inactive panels are hidden and inert.
An initially open server Tour is visible before enhancement; enhancement
reconciles it with `dialog.show()` and current client state. A retained host
hands off the activator used for focus restoration. Cleanup disconnects
resize/mutation observers, document scroll/resize/key/pointer listeners,
animation frames, and host/dialog listeners. No retained observer may outlive
its host.

## 15. Security and content trust

`target_id` is validated and passed only to `getElementById`; arbitrary CSS
selectors and HTML strings are rejected. Slot HTML follows ordinary Citry
trust and escaping. The runtime never assigns `innerHTML`, evaluates authored
code, clones target content, or moves target nodes. Attribute maps cannot
replace owned dialog, state, identity, i18n, or behavior hooks.

## 16. Assets and performance

Tour ships its finite-step state, exact-ID lookup, geometry, and observer code
without a third-party package or the modal Dialog controller. Closed instances
attach no geometry observers or viewport listeners. Per-family and full-catalog
raw, gzip, and Brotli deltas remain release evidence.

## 17. Acceptance matrix

Evidence covers centered and targeted steps; one and many steps; visual
progress; every action and callback reason; independently controlled open and
active state; missing and removed targets; scrolling, resize, collision
avoidance, flip, and clamp; actual pointer interaction with a highlighted
target; LTR/RTL; title focus, ordinary Tab flow, Escape, and restoration;
server-open enhancement; localization and overrides; long content, narrow,
zoom, dark, forced colors, reduced motion, touch, and print; morph/removal
cleanup; CSP; wheel/catalog/docs projection; and family/catalog asset budgets.
Serious or critical Axe violations fail.

## 18. Compatibility classification

This is a new additive public family. `CTour`, `CTourStep`, aliases, slots,
callbacks, parts, variables, reflected attributes, message IDs, and the
nonmodal/interactive-target boundary become semver-governed once released.

## 19. Public documentation contract

The guide teaches target steps, centered introduction/finish, controlled state,
missing targets, placement and scrolling, target interaction, localization,
styling, accessibility, and when to use Dialog instead. The quality scenario
combines centered and targeted steps, an interactive target, missing target,
controlled request, RTL, long content, dark mode, and focus restoration.
`api.yml` is the only structured API source and ends with Translation keys.

## 20. Open decisions and deferred work

Deferred: an opt-in target-interaction blocker, arbitrary target resolver
callbacks, wait/effect steps, cross-route persistence, analytics storage,
beacons/hints, dynamic step mutation, custom action arrays, and an imperative
retained API. Each needs separate product evidence and lifecycle, focus,
security, or typing work.

## 21. Internationalization

Keys are `citry-ui-tour-close`, `citry-ui-tour-previous`,
`citry-ui-tour-next`, `citry-ui-tour-finish`, `citry-ui-tour-skip`, and
`citry-ui-tour-progress`. The first five have no variables. Progress requires
numeric `current` and `total`. All are server-rendered and stable `$c-tr`
bindings; labels supplied explicitly by the caller produce no binding. Source
messages are the final `CTour` class member with `messages_locale="en-US"`.
