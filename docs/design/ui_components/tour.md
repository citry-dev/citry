# Tour

**Status:** implementation contract accepted for a modal, target-aware product
Tour. Interactive spotlight targets, cross-page persistence, and asynchronous
wait steps are explicit deferred work rather than implicit partial behavior.

## 1. Purpose and product bar

`CTour` guides a user through a short ordered explanation. `CTourStep`
declares either a centered dialog step or a step attached to an existing page
element. The production bar is meaningful server HTML, native modal semantics,
controlled and uncontrolled state, resilient target geometry, localized
chrome, deterministic missing-target behavior, direction-aware placement,
focus restoration, cleanup, and useful default styling.

Common jobs are: introduce a feature with a centered first step; explain a
sequence of existing controls by `target_id`; finish or skip; control open and
active state from Alpine; and style one step or the complete Tour. `CTour`
solves those directly. Rich target interaction, route transitions, persistence,
analytics storage, beacons, and arbitrary selector/callback targets remain
application orchestration or deferred APIs.

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

Python composition uses the same `CTour` and `CTourStep` definitions and named
slots. There is no separate headless API.

## 2. Prior art and complaints

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| WAI-ARIA APG | reviewed 2026-08-21 | [Modal Dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) | Use a named modal dialog, move focus inside, contain Tab, support Escape, retain a visible close action, and restore focus. |
| HTML/WCAG technique | reviewed 2026-08-21 | [H102 native dialog technique](https://www.w3.org/WAI/WCAG21/Techniques/html/H102) | Reuse native `showModal()` and the shared Citry UI Dialog controller instead of another inert/focus system. |
| Ant Design | 6.6.1, reviewed 2026-08-21 | [Tour docs/API](https://ant.design/components/tour/) and current source directory | Adopt target and centered steps, controlled current/open state, placement, progress, target scrolling, mask/spotlight geometry, semantic parts, and lifecycle callbacks. Narrow twelve physical placements to eight logical placements. |
| Zag / Ark | 1.41.1 release and current docs reviewed 2026-08-21 | [Tour docs](https://zagjs.com/components/vue/tour) and [changelog](https://github.com/chakra-ui/zag/blob/main/CHANGELOG.md) | Adopt stable step IDs, dialog/target steps, missing-target status, progress, controlled state, cleanup, and explicit navigation reasons. Defer wait/effect steps and highlighted-target interaction; recent fixes demonstrate their separate lifecycle and focus cost. |
| Driver.js | current docs reviewed 2026-08-21 | [Configuration](https://driverjs.com/docs/configuration), [basic use](https://driverjs.com/docs/basic-usage), and changelog | Confirm offset/radius, progress, next/previous/close labels, scrolling, cleanup, and reduced-motion needs. Reject trusted title/description HTML and global selector strings. |
| React Aria | current docs reviewed 2026-08-21 | [Popover](https://react-aria.adobe.com/Popover) | Confirm custom-anchor positioning, explicit trigger semantics, and focus ownership. Tour remains a dialog rather than pretending its card is a tooltip. |
| Vuetify | 4.0.7 catalog/source reviewed 2026-08-21 | current component catalog and overlay/dialog primitives | Vuetify has no first-party Tour family. Use its mature overlay concerns—controlled state, logical placement, scroll and focus ownership—as comparison inputs without exposing the complete overlay prop tree. |
| Citry UI | current source reviewed 2026-08-21 | `CDialog`, `_dialog_controller`, `_anchored_layer`, `CPopover`, declaration families, i18n contract | Reuse the native modal/focus/scroll/overlay coordinator and declaration collection pattern. Keep Tour-specific target geometry local. |

Material complaints are target disappearance, stale positioning after scroll or
resize, focus escaping or excluding an intended interactive target, listener
leaks, selector ambiguity, accidental outside dismissal, and state callbacks
that cannot distinguish finish, skip, dismiss, or target failure. The v1
contract answers those with exact ID targets, observer cleanup, modal-only
interaction, reason-bearing callbacks, and conservative outside dismissal.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| Controlled overlay visibility | direct API | `open`, client `open`, `onOpenChange` | Adopt. |
| Activator composition | scoped slot | `activator_attrs` | Adopt without cloning child nodes. |
| Native modal focus, Escape, restoration, scroll lock | shared foundation | native `<dialog>` plus Dialog controller | Adopt. |
| Logical anchored placement and collision handling | direct Tour API | `CTourStep.placement` | Adopt a bounded placement set. |
| Generic overlay dimensions/transitions/location strategy | CSS or omitted | public Tour variables and fixed viewport geometry | Do not inherit the overlay prop tree. |
| Teleport/portal target | omitted | logical in-place host; native top layer | Native dialog supplies top-layer behavior without moving ownership. |
| Target interaction while open | omitted | none in v1 | Requires multi-container focus and interaction semantics; defer. |

## 3. Public composition and anatomy

`CTour > CTourStep` is the declaration relationship. The default Tour slot may
contain only direct step declarations and formatting whitespace. Nested Tours
are valid inside a rendered step body because the declaration context is
removed before authored content renders.

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CTour` | host `<div>` containing native `<dialog>` | `class_`, `style`, `attrs` reach the host | At least one direct `CTourStep`; unique step values. |
| `CTourStep` | active step `<section>` inside the dialog surface | `class_`, `style`, `attrs` reach that section | Required `title` and default slots; optional unique target ID reference. |

Stable anatomy is host `tour`, native `dialog`, visual `spotlight`, positioned
`surface`, `arrow`, `close`, step `panel`, `media`, `header`, `title`, `description`,
`footer`, `progress`, and `actions`. Only the active panel is exposed. The
dialog remains in the Tour host; it is not portalled.

## 4. Server inputs and client inputs

`CTour` server inputs are `id: str | None`, `open: bool=False`,
`active: int=0`, `dismissible: bool=True`, `close_on_escape: bool=True`,
`close_on_outside: bool=False`, `skippable: bool=True`,
`scroll: "auto" | "smooth" | "none"="auto"`,
`missing_target: "skip" | "close"="skip"`, `size: "sm" | "md" | "lg"="md"`,
six string overrides (`close_label`, `previous_label`, `next_label`,
`finish_label`, `skip_label`, `progress_label`), and `class_`, `style`, `attrs`.
`active` must name a rendered step. `open=True` is initial state, not proof
that JavaScript loaded.

`CTourStep` server inputs are unique nonempty `value`, optional valid HTML
`target_id`, logical `placement`, `arrow: bool=True`, `describe: bool=False`,
and `class_`, `style`, `attrs`. No selector text is accepted.

Client inputs are `open: boolean | null`, `active: number | null`, the five
reactive policy inputs (`dismissible`, `closeOnEscape`, `closeOnOutside`,
`scroll`, `missingTarget`), and callbacks `onOpenChange`, `onActiveChange`.
`null` or omission releases controlled open/active state to the last committed
value. Invalid values are diagnosed once per episode and retain the current
valid configuration. Open and active ownership are independent.

## 5. State model

The Tour is closed or open at one active step. Opening resolves the requested
step and its target before showing the dialog. A missing target either advances
in the requested direction until a valid/centered step is found or closes with
`missing-target`; `missing_target="close"` closes immediately. A successful
step transition updates panel visibility, dialog relationships, target scroll,
spotlight, placement, progress, focus, public state, then notifies.

Uncontrolled actions commit before callback. Controlled actions notify and
wait for the corresponding client prop. `finish` closes with `finish`; `skip`
closes with `skip`; close button, Escape, outside, and activator use their own
reasons. Same-value requests do nothing. Removing the active target uses the
same missing-target policy. Removal or morph cleans observers and closes or
hands off through the shared controller.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---:|---:|---|---|
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

Callbacks cannot cancel. Controlled state is acceptance. v1 exposes no
imperative method because `$c-props` open/active state and native activator
composition cover Citry/Alpine orchestration without adding a second retained
controller-reference lifecycle.

## 8. Semantics, keyboard, focus, and assistive technology

The browser-visible overlay is a native modal `<dialog>` named by the active
step title. `describe=True` adds `aria-describedby` to the active description;
the default omits it so structured body content is not flattened into one
announcement. The visual spotlight is `aria-hidden`. Buttons are native and
form-safe.

Tab and Shift+Tab remain inside through the shared Dialog controller. Focus
enters the active title (`tabindex=-1`), while all actions remain reachable.
Escape closes only when dismissible and enabled. Arrow keys do not change Tour
steps because they would steal keys from content. Target elements remain
inert while the modal is open and are never presented as interactive.

## 9. Native forms and validation

Tour is not a form participant. Every built-in action uses `type=button`.
Authored controls inside a step retain native Form semantics, but a Tour is
guidance rather than a transactional form container; complex tasks should open
a separate Dialog or page.

## 10. Styling and theme contract

Public variables are `--cui-tour-width`, `--cui-tour-background`,
`--cui-tour-foreground`, `--cui-tour-border-color`, `--cui-tour-shadow`,
`--cui-tour-radius`, `--cui-tour-padding`, `--cui-tour-gap`,
`--cui-tour-offset`, `--cui-tour-spotlight-padding`,
`--cui-tour-spotlight-radius`, `--cui-tour-backdrop-color`, and
`--cui-tour-focus-color`. Sizes currently select width fallbacks of 20, 24,
and 30 rem. Public parts are those named in section 3.

Host mirrors are `data-open`, `data-active`, `data-value`, `data-size`, and
`data-targeted`. Surface mirrors actual `data-placement`; panels mirror
`data-index`, `data-value`, `data-target-id`, `data-placement`, `data-describe`,
and active `data-current`. The dialog updates `aria-labelledby` and optional
`aria-describedby` to the active panel. Variables resolve
through private fallbacks in `citry-ui.theme`.

## 11. Environmental behavior

Placement uses logical inline direction and flips/clamps inside the viewport.
Long content scrolls within the surface, target scrolling uses `nearest`, and
narrow viewports center a bounded card. Reduced motion disables geometry
transitions and smooth scrolling. Forced colors retains borders and focus.
Touch actions remain at least 44 CSS pixels. Print hides Tour chrome entirely.

Localized built-ins use component-owned English source messages. Exact prop
overrides omit their catalog bindings. Stable text and `aria-label` outputs use
server `tr()` plus `$c-tr`; progress passes numeric `current` and `total`
values captured per pre-rendered panel. Application title, body, and media
slots retain their own language, bidi, and formatting ownership.

## 12. Overlay and layering behavior

The native dialog owns top-layer ordering, inertness, focus containment,
Escape, and restoration. The shared Dialog controller coordinates nested
modal/anchored surfaces and scroll locks. A transparent full-viewport dialog
contains a fixed spotlight whose large shadow produces the mask and a fixed
surface positioned from target geometry. Outside dismissal defaults off.
No portal breaks logical ownership or inherited theme.

## 13. Collections, async data, and identity

Steps are a finite server declaration collection with unique stable `value`
identity and numeric rendered order. Reordering across a morph follows values;
active numeric control is revalidated. Async wait steps, route transitions,
dynamic add/remove methods, and remote step content are deferred. Conditional
targets should open only after the application has rendered them.

## 14. Server render, morph, and cleanup

All step content renders on the server; inactive panels are hidden. An
initially open server Tour is a nonmodal visible dialog until enhancement
promotes it with `showModal()`. The dialog controller handles compatible morph
handoff. Tour cleanup disconnects resize/mutation observers, scroll/resize
listeners, animation frames, and click listeners before controller cleanup.
No retained observer may outlive its host.

## 15. Security and content trust

`target_id` is validated and passed only to `getElementById`; arbitrary CSS
selectors and HTML strings are rejected. Slot HTML follows ordinary Citry
trust and escaping. The runtime never assigns `innerHTML`, evaluates authored
code, clones target content, or moves target nodes. Attribute maps cannot
replace owned dialog, state, identity, i18n, or behavior hooks.

## 16. Assets and performance

Tour reuses the existing anchored-layer and Dialog-controller dependencies.
Its incremental JavaScript is bounded to finite-step state, ID lookup,
geometry, and observers. It ships no third-party package. Inactive/closed
instances attach no viewport listeners. Per-family and full-catalog raw,
gzip, and Brotli deltas must be recorded; frozen catalog ceilings remain a
release gate.

## 17. Acceptance matrix

Evidence covers centered and targeted steps; one and many steps; every action
and callback reason; controlled/open and active ownership independently;
missing targets; target removal; scrolling, resize, flip and clamp; LTR/RTL;
keyboard focus loop, Escape and restoration; nested modal coordination;
server-open enhancement; source/configured/switched locale and explicit label
overrides; long content, narrow, zoom, dark, forced colors, reduced motion,
touch and print; morph/removal cleanup; CSP; wheel/catalog/docs projection;
and exact asset deltas. Serious or critical Axe violations fail.

## 18. Compatibility classification

This is a new additive public family. `CTour`, `CTourStep`, their aliases,
slots, callbacks, parts, variables, reflected attributes, message IDs, and
deferred-mode boundary become semver-governed once released.

## 19. Public documentation contract

The guide teaches: at a glance, target steps, centered introduction/finish,
controlled open and active state, missing targets, placement and scrolling,
localization overrides, styling, accessibility, and modal limitations. The
quality scenario combines a centered/targeted tour, missing target, controlled
request, RTL, long content, dark mode, and focus restoration. `api.yml` is the
only structured API source and ends with Translation keys.

## 20. Open decisions and deferred work

Deferred: interactive spotlight targets, nonmodal tours, arbitrary target
resolver callbacks, wait/effect steps, cross-route persistence, analytics
storage, beacons/hints, dynamic step mutation, custom action arrays, and an
imperative retained API. Each needs separate product evidence and lifecycle,
focus, security, or typing work.

## 21. Internationalization

Keys are `citry-ui-tour-close`, `citry-ui-tour-previous`,
`citry-ui-tour-next`, `citry-ui-tour-finish`, `citry-ui-tour-skip`, and
`citry-ui-tour-progress`. The first five have no variables. Progress requires
numeric `current` and `total`. All are server-rendered and stable `$c-tr`
bindings; labels supplied explicitly by the caller produce no binding. Source
messages are the final `CTour` class member with `messages_locale="en-US"`.
