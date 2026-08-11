# Citry UI Popover component specification

**Status (2026-08-09): production implementation pass complete. Runtime,
structured reference, nine public previews, focused server and cross-browser
evidence, reusable quality scenario, scaling diagnostics, and exact wheel
qualification are checked in. Independent implementation review remains
pending because the active collaboration policy did not permit delegation.
Human visual, assistive-technology, and remaining release qualification also
remain.**

## 1. Purpose and product bar

`CPopover` reveals a non-modal, interactive surface beside one explicit
Button. It targets compact inspectors, explanations with controls, previews,
small editing forms, sharing panels, and other content that must stay available
while the surrounding page remains operable.

The production bar is a server-rendered, top-layer Popover with accessible
dialog semantics, predictable focus and dismissal, controlled and uncontrolled
browser ownership, logical placement with collision fallback, nested-layer
isolation, responsive styling, and cleanup through retained Citry rerenders.

Common jobs and their shortest supported paths:

| Job | Shortest path | Classification |
|---|---|---|
| Reveal rich information beside a Button | activator, title, and default fills | direct API |
| Edit a compact setting without blocking the page | native controls in the default fill | composition |
| Close from an explicit action | spread `close_attrs` from the actions fill | direct API |
| Control visibility in Alpine | client `open` plus `onOpenChange` | client API |
| Keep a panel open until an explicit action | `dismissible=False` | direct API |
| Align to a trigger edge | `placement` | direct API |
| Match the trigger's inline size | `match_width=True` | direct API |
| Change width, gap, colors, radius, or shadow | public CSS variables | CSS |
| Offer a list of commands or choices | future `CMenu` | separate component |
| Explain a control with noninteractive text | `CTooltip` | separate component |
| Block the page for a task or decision | `CDialog` | separate component |

Smallest template:

```citry-html
<c-CPopover>
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">
      Inspect moon
    </c-CButton>
  </c-fill>
  <c-fill name="title">
    Europa
  </c-fill>
  <c-fill name="default">
    Europa has a water-ice crust above a global ocean.
  </c-fill>
</c-CPopover>
```

Non-goals are menu keyboard semantics, tooltip hover timing, modal focus
containment, a public positioning engine, arbitrary virtual anchors, cursor
anchoring, a portal option, resizable floating windows, and Toast delivery.

## 2. Prior art and complaints

Current sources were checked on 2026-08-09. Vuetify remains the most heavily
weighted product reference; standards and other libraries challenge its broad
overlay approach.

| Source | Version or review date | Evidence | Decision supported |
|---|---|---|---|
| HTML and CSS | living standards, 2026-08-09 | [Popover API](https://html.spec.whatwg.org/multipage/popover.html), [CSS Anchor Positioning](https://drafts.csswg.org/css-anchor-position-1/) | native manual top layer, anchor geometry, author-owned dismissal |
| WAI-ARIA APG | 2026-08-09 | [Dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) | named dialog surface and deliberate focus placement; Popover stays non-modal |
| Vuetify | 4.1.8 | [`VOverlay`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VOverlay/VOverlay.tsx), [location strategy](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VOverlay/locationStrategies.ts), [`VMenu`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VMenu/VMenu.tsx) | topmost dismissal, activator contracts, connected placement, controlled state, focus restoration |
| React Aria Components | 1.20.0 | [Popover](https://react-aria.adobe.com/Popover) | default dialog role, placement and trigger-width jobs, initial/return focus, nested surface care |
| Radix Primitives | Popover 1.1.23 | [docs](https://www.radix-ui.com/primitives/docs/components/popover), [source](https://github.com/radix-ui/primitives/tree/main/packages/react/popover) | Trigger/Content/Title/Description/Close anatomy, controlled state, modal and non-modal distinction |
| Mantine | 9.5.1 | [Popover](https://mantine.dev/core/popover/) | concise placement, match-target-width, outside/Escape policy, optional focus trap and portal trade-offs |
| Web Awesome | 3.11.0 | [Popover](https://webawesome.com/docs/components/popover/), [Popup](https://webawesome.com/docs/components/popup/) | keep low-level geometry private; an accessible Popover must add semantics and focus behavior |

Material findings and Citry responses:

| Finding | Citry response |
|---|---|
| Mature overlay engines expose many geometry and transport combinations. | Publish only six proved logical placements and a trigger-width shorthand. Keep the engine private. |
| Portals escape clipping but disturb CSS inheritance, event ancestry, reading order, and focus scopes. | Use native top-layer Popover without DOM reparenting. No portal input. |
| Native `auto` popovers own light-dismiss and single-open policy. | Use `popover="manual"`; Citry owns controlled requests, nesting, callbacks, and exit presence. |
| Browser CSS exit transitions are not reliable across the supported matrix. | Use generation-owned Web Animations and call `hidePopover()` after the settled exit. |
| Rich popovers are frequently unnamed or opened by non-button elements. | Require a visible title and exactly one native Button activator. |
| Menus and Tooltips are often built by adding a role to generic Popover content. | Design them as separate families over shared private mechanics. |

Vuetify disposition:

| Vuetify surface | Citry path | Decision |
|---|---|---|
| `modelValue`, `update:modelValue` | Python/client `open`, `onOpenChange` | adopt |
| `persistent` | inverse `dismissible` | adopt clearer name |
| activator props/slot | `activator_attrs` slot data | adopt |
| connected location and origin | six `placement` values | adopt proved common subset |
| offset | `--cui-popover-offset` | use CSS, avoid another frequent prop |
| min/max width/height | public variables and `style` | capability without prop parity |
| scrim, scroll block, focus trap | `CDialog` | reject for non-modal Popover |
| teleport/attach/contained | native top layer | no public transport modes |
| close on content click | explicit `close_attrs` | avoid accidental closure from rich content |
| transitions | owned entry/exit animation | fixed accessible behavior, public duration/easing |
| public low-level Overlay | private foundation | reject public universal overlay |

## 3. Public composition and anatomy

`CPopover` is one public component:

```text
private host (div, display: contents)
├─ activator fill
│  └─ exactly one native button carrying activator_attrs
└─ popover (div, popover="manual", role="dialog")
   ├─ header
   │  └─ title (h2)
   ├─ description (optional)
   ├─ body
   └─ actions (optional)
```

The host exists only to give Citry one stable root around activator and surface.
It is not a public selector or attribute destination. `class_`, `style`, and
`attrs` land on the Popover surface.

The activator fill must settle to exactly one owned native `<button>` carrying
all `activator_attrs`. A `CButton` without `href` satisfies this contract.
Links, generic elements, multiple triggers, or a missing spread fail during
client initialization. The Button remains in ordinary DOM flow. The Popover
surface remains its DOM descendant but enters the browser top layer while open.

The surface requires one title and one default fill. Description and actions
are optional. The title is its accessible name. The description is concise
supporting text. The body accepts flow content, native controls, and nested
Citry components. Actions are ordinary explicit controls; spreading
`close_attrs` marks one as a close request.

Nested Popovers are valid inside the body or actions of an open Popover. The
outer layer treats the complete nested Popover route as inside interaction.
`CMenu` and `CTooltip` share the private layer coordinator without sharing this
component's dialog semantics.

## 4. Server inputs and client inputs

`CPopover.Kwargs`:

| Python input | Type | Default | Class | Effect |
|---|---|---|---|---|
| `id` | `str | None` | generated | structural | Popover identity and title/description/activator relationships |
| `open` | `bool` | `False` | initial state | server-visible initial state and uncontrolled fallback |
| `dismissible` | `bool` | `True` | reactive configuration | permits Escape, outside pointer, and focus-outside close requests |
| `placement` | `Literal["top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end"]` | `"bottom-start"` | reactive presentation | preferred logical placement; collision fallback may choose another rendered side |
| `match_width` | `bool` | `False` | reactive presentation | makes the surface at least as wide as its activator |
| `class_` | `CClassValue | None` | `None` | server presentation | adds classes to the surface |
| `style` | `CStyleValue | None` | `None` | server presentation | adds inline styles to the surface |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted native attributes | copied, validated, and added to the surface |

Client inputs through `$c-props`:

| Client input | Type | Omitted or `null` | Invalid | Effect |
|---|---|---|---|---|
| `open` | `boolean | null` | releases control and preserves the committed state | one diagnostic per episode; releases from current state | controls visibility while supplied as a Boolean |
| `dismissible` | `boolean` | server value | server fallback | controls passive dismissal |
| `placement` | six placement strings | server value | server fallback | controls preferred placement and reflection |
| `matchWidth` | `boolean` | server value | server fallback | controls trigger-width matching |
| `onOpenChange` | function or null | no callback | one diagnostic per episode; callback disabled | receives open and close requests |

Invalid episodes end only when the input becomes valid or omitted. Unrelated
prop changes do not repeat a diagnostic.

## 5. State model

`open` has controlled and uncontrolled ownership:

- without a valid client Boolean, the browser commits trigger and dismissal
  requests, then calls `onOpenChange`;
- with a valid client Boolean, requests call `onOpenChange` but do not commit;
- changing the valid client Boolean is an owner commit and never calls back;
- removing or setting the client input to `null` releases control without
  resetting the current committed state;
- an invalid client value reports once and releases from the current state;
- an activator that is natively disabled or otherwise unavailable cannot open
  the Popover. Disable the Button itself so focus, styling, and semantics remain
  owned by one component.

Opening enters a generation. Closing removes interactive ownership immediately,
marks the surface inert, and begins an exit animation. Only that generation may
eventually call `hidePopover()`. Reopening cancels the old exit and begins a new
entry. A removed component cancels every pending animation and task.

The private owner-document coordinator orders active layers across Document and
open-ShadowRoot scopes. Only the topmost active dismissible layer handles
Escape, outside pointer, or focus-outside.
A declined controlled close still consumes that dismissal request; it must not
fall through and close an ancestor.

## 6. Slots and slot data

| Slot | Required | Data | Content contract |
|---|---|---|---|
| `activator` | yes | `{activator_attrs: dict[str, object]}` | exactly one native Button; spread all attrs |
| `title` | yes | `{}` | visible concise heading content |
| `description` | no | `{}` | concise supporting flow content; omitted from `aria-describedby` when absent |
| `default` | yes | `{}` | flow content and interactive controls |
| `actions` | no | `{close_attrs: dict[str, object]}` | explicit action controls; spread close attrs only on controls that close |

Unknown, duplicate, or missing required fills raise during server render.

## 7. Callbacks, native events, and methods

`onOpenChange` has this shape:

```text
(requestedOpen: boolean, detail: CPopoverOpenChangeDetail) => void
```

Detail fields:

| Field | Type | Meaning |
|---|---|---|
| `reason` | `"trigger" | "action" | "escape" | "outside" | "focus-outside" | "native" | "ancestor" | "modal"` | request or forced-close source |
| `controlled` | `boolean` | whether a valid client Boolean owns `open` |
| `forced` | `boolean` | whether ancestor or modal safety required the close regardless of controlled ownership |
| `source` | `Element | EventTarget | null` | associated browser source |

Uncontrolled requests commit before the callback. Controlled requests wait for
the owner. Native reconciliation repairs unavoidable external
`showPopover()`/`hidePopover()` calls and reports `native` only when the browser
changed state outside the component's own transition.

Structural invalidation and modal exclusion are safety closures rather than
declinable requests. They report `forced: true` with `ancestor` or `modal`.

No custom DOM event and no imperative public method are added. Native events
authored on the activator or descendants continue to work. The component's
owned activation listener runs in capture and applies only after consumer
listeners have had a chance to call `preventDefault`; stopping propagation does
not disable Popover behavior.

## 8. Semantics, keyboard, focus, and assistive technology

- The activator is a native Button with `aria-haspopup="dialog"`,
  `aria-controls`, and synchronized `aria-expanded`.
- The surface is `role="dialog"`, labelled by the required visible title and
  optionally described by the description.
- The Popover is non-modal: it never emits `aria-modal`, never traps Tab, never
  makes the page inert, and never locks scrolling.
- On open, `[autofocus]` wins. Otherwise the first tabbable descendant is
  focused. If none exists, the focusable surface receives focus.
- Tab and Shift+Tab follow native document order. Leaving the surface closes a
  dismissible uncontrolled Popover after focus settles outside.
- Escape requests closure only from the topmost layer.
- Trigger or explicit-action closure returns focus to the activator when focus
  was inside the Popover. Outside pointer/focus closure keeps the user's new
  destination.
- A missing, non-Button, duplicate, or unmarked activator logs one initialization
  error and leaves the surface closed rather than installing partial behavior.

Touch has no hover dependency. Zoom, forced colors, and reduced motion must not
hide focus or the surface boundary.

## 9. Native forms and validation

`CPopover` is not a form participant. Controls inside its body and actions keep
their ordinary native owners, FormData behavior, reset, and constraint
validation because the surface is not portalled or unmounted.

The activator uses `type="button"` through `CButton`'s default or an explicit
native Button attribute. Authors using a raw Button must set `type="button"`
when it sits inside a Form. Citry does not silently rewrite consumer-owned
button type.

Closing does not reset fields. Reopening exposes the same retained DOM and
browser-owned values. A server rerender may deliberately replace those values
under each child control's own ownership contract.

## 10. Styling and theme contract

The component uses native `color-scheme` inheritance and `light-dark()`
fallbacks. Consumer variables inherit from ancestors and can be overridden on
the surface through `style`.

Public variables:

| Variable | Purpose | Default |
|---|---|---|
| `--cui-popover-background` | surface background | `Canvas` |
| `--cui-popover-foreground` | surface text | `CanvasText` |
| `--cui-popover-border-color` | surface boundary | subtle CanvasText mix |
| `--cui-popover-border-width` | boundary width | `1px` |
| `--cui-popover-radius` | corner radius | `0.75rem` |
| `--cui-popover-shadow` | elevation | `0 1rem 3rem rgb(15 23 42 / 22%)` |
| `--cui-popover-inline-size` | preferred inline size | `20rem` |
| `--cui-popover-max-inline-size` | viewport-aware maximum | `calc(100dvi - 1rem)` |
| `--cui-popover-max-block-size` | viewport-aware maximum | `calc(100dvb - 1rem)` |
| `--cui-popover-padding` | body/header/actions padding | `1rem` |
| `--cui-popover-gap` | region gap | `0.75rem` |
| `--cui-popover-offset` | anchor gap | `0.5rem` |
| `--cui-popover-duration` | entry/exit duration | `140ms` |
| `--cui-popover-easing` | entry/exit easing | `cubic-bezier(.2,.8,.2,1)` |
| `--cui-popover-focus-color` | fallback focus outline | `Highlight` |

Public selectors:

| Selector | Element |
|---|---|
| `[data-citry-ui-part="popover"]` | semantic surface and attrs destination |
| `[data-citry-ui-part="header"]` | title/description header |
| `[data-citry-ui-part="title"]` | visible title |
| `[data-citry-ui-part="description"]` | optional description |
| `[data-citry-ui-part="body"]` | main content |
| `[data-citry-ui-part="actions"]` | optional action row |

Public reflected attributes:

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| `data-open` | surface | present/absent | logical visible state; absent during exit ownership |
| `data-placement` | surface | six placement strings | requested placement, not a guarantee of collision result |
| `data-match-width` | surface | present/absent | trigger-width matching enabled |

All selectors use zero specificity and direct-child constraints where nested
Popovers could otherwise inherit internal layout. Unlayered consumer CSS and
inline style win. `data-*` reflections are state/configuration inspection and
styling contracts, never a writable state API.

## 11. Environmental behavior

- logical placement and inline/block dimensions support RTL and vertical-safe
  writing where the proved placement subset allows it;
- viewport maxima use dynamic logical viewport units;
- long titles, body text, URLs, and actions wrap without horizontal overflow;
- internal body scrolling preserves the title and actions when height is
  constrained;
- `prefers-reduced-motion: reduce` makes duration zero;
- forced colors preserves a visible boundary, focus outline, and readable
  foreground;
- print renders an initially server-open surface in document flow without
  shadow, and omits closed surfaces;
- nested light/dark schemes inherit correctly because the surface is not
  physically reparented;
- an open Popover repositions through CSS while its anchor or viewport moves;
  no perpetual JavaScript geometry loop is installed.

## 12. Overlay and layering behavior

The production path ratified in
[`ui_overlay_foundations.md`](../ui_overlay_foundations.md) is:

- `popover="manual"` for native top-layer presence;
- CSS anchor positioning for the six block-axis placements, trigger width,
  logical flip fallback, and anchor visibility;
- one private coordinator per `ownerDocument`, with one capture listener set
  and bounded modal observer for its Document and each active open ShadowRoot;
- composed-path containment, logical parent cascades, and modal eligibility
  shared with Tooltip and Menu;
- generation-owned Web Animations for entry/exit; and
- no portal, global z-index scale, scrim, scroll lock, or inert page owner.

`placement` is preferred. Collision fallback may flip block or inline alignment.
The component does not promise a rendered-placement reflection in the first
release because current CSS does not expose the chosen fallback as a stable DOM
value.

When the anchor is fully clipped, `position-visibility: anchors-visible` hides
the surface. This does not change logical `open`; scrolling the anchor back
restores it. If later testing shows this produces unusable focus behavior,
anchor-hidden closure becomes a separately specified change.

## 13. Collections, async data, and identity

Popover has one activator and one surface, not a collection. Stable identity
comes from `id` or the Citry component ID. Raw application text never becomes
an HTML ID.

Async body changes do not announce automatically and do not move focus. Use an
Alert or an intentionally authored live region when updates require
announcement. If a server rerender removes the activator or surface, cleanup
removes the layer record before the DOM disappears.

## 14. Server render, morph, and cleanup

The server renders complete activator, title, description, body, and actions
source. Initially open content has a readable no-JavaScript fallback in normal
flow; initially closed content stays hidden. Client activation upgrades an
initially open surface into the top layer without changing ownership.

On a correlated retained rerender:

- uncontrolled open state is handed to the new initializer through a private
  DOM symbol and preserved;
- controlled state is reapplied from the latest valid prop;
- changed placement/configuration updates without rebuilding the layer;
- the activator relationship is re-resolved and all generated ARIA values are
  synchronized;
- the old initializer unregisters listeners, cancels animations/tasks, removes
  its layer record, and never leaves inertness or a shown orphan.

On removal, an open or exiting surface is hidden synchronously where possible,
focus restoration occurs only if the removed Popover still owns focus, and all
resources settle to zero. Reinitialization is idempotent and does not duplicate
owner-document, scope, or trigger listeners.

## 15. Security and content trust

Slot content follows Citry's ordinary template escaping. `class_`, `style`, and
`attrs` are explicit trusted customization surfaces. The component copies the
mapping once per render before validation and binding.

Surface attrs reject, case-insensitively, every component-owned semantic,
presence, identity, relationship, focus, and reflection attribute, their
dynamic/property aliases, Citry/Events runtime namespaces, whole-object binds,
and structural/ownership directives including `x-html`, `x-text`, `x-if`,
`x-for`, `x-show`, `x-ignore`, `x-teleport`, `x-model`, and `x-modelable`.
Notably, callers cannot replace `popover`, `role`, `tabindex`, `id`, `hidden`,
`inert`, `aria-labelledby`, `aria-describedby`, `data-open`, anchor ownership,
or initialization markers.

The generated `activator_attrs` and `close_attrs` are the only supported ways
to claim those behaviors. Whole-object consumer spreads on the Button may merge
around them through that component's own attr contract, but must not replace
the generated relationship markers.

## 16. Assets and performance

One Popover contributes static CSS and one initializer. There is no icon asset,
positioning dependency, portal tree, per-instance MutationObserver,
ResizeObserver, or animation-frame geometry loop.

While at least one anchored layer is active, the shared coordinator owns one
capture listener set and one modal observer for the Document and each active
open ShadowRoot. It performs work only against the ordered active layer stack
and removes every scope resource when the stack reaches zero. Each instance
owns one activator listener, one native toggle listener, at most one animation,
and bounded cleanup tasks.

Diagnostic scaling records 1, 10, 100, 500, and 1,000 server-rendered Popovers
and output bytes. Focused browser evidence proves that closing the final layer
removes the shared document listeners and that one retained correlated
rerender preserves one open layer without duplicating its registration. These
are bounded diagnostics and invariants, not timing gates.

## 17. Acceptance matrix

Checked-in server tests cover the public nested schemas and type hints; default
and custom semantic anatomy; generated activator, title, description, and close
relationships; server-open source; every invalid input kind; required,
unknown, and duplicate fills; safe-string de-trusting; representative reserved
attributes and directives; copied one-read attrs; class/style merging; and
package exports.

Focused browser tests run in Chromium, Firefox, and WebKit. They cover native
top-layer opening; initial and return focus; explicit action, Escape, outside
pointer, and focus-outside dismissal; controlled request refusal and owner
commit; nested Escape ownership; reactive placement and trigger-width geometry;
symmetric controlled reconciliation of external native show/hide operations;
logical parent-close cascades; open-ShadowRoot composed-path ownership and
cleanup; modal suppression and modal-close cleanup; closed-surface zero
geometry; final-layer listener teardown; and retained
correlated rerender of an open Popover with edited form content and one layer
registration.

The `popover.states` route covers ordinary, form, nested, controlled,
explicit-only, trigger-width, RTL, long-content, and two theme specimens.
Shared browser tooling runs initial and active axe checks. Public documentation
discovers and initializes all nine previews, exercises native form continuity,
controls, nesting, theme customization, and page-wide console cleanliness.
Reference schema, component-contract, registration, asset, scaling, and exact
wheel tools include the family; the freshly built wheel passes its exact
runtime inventory gate.

Release qualification still covers the broader matrix without turning every
row into a permanent browser test: all six placements and collision outcomes
in LTR/RTL; Tab and Shift+Tab boundaries; autofocus and surface-fallback focus;
declined controlled dismissal from every passive source; rapid animation
reversal; activator replacement and removal while focused or exiting;
100-instance browser resource diagnostics; public selector and cascade-layer
overrides; light/dark/nested schemes; forced colors; reduced motion; print;
zoom; touch; and Nu HTML in an environment with Java. The local Nu run is
currently unavailable because this workstation has no Java runtime.

Manual release evidence covers VoiceOver, NVDA, and JAWS dialog naming and
focus behavior; keyboard and touch interaction; 200/400 percent zoom;
collision behavior near viewport and scroll-container edges; forced colors;
print; and representative application integration. Independent adversarial
implementation review also remains pending under the current no-delegation
policy.

## 18. Compatibility classification

Stable public contract:

- `CPopover` name and nested `Kwargs`, `Slots`, and slot-data types;
- server and client input names/value domains/defaults;
- required slots, slot data, callback shape/reasons;
- semantic Button/dialog/label/description relationships;
- public selectors, CSS variables, and reflected attributes; and
- controlled/uncontrolled, dismissal, focus, and form-continuity behavior.

Private and replaceable:

- host markup/class, generated ID format, anchor-name format;
- controller symbols, stack data structures, listener implementation;
- exact keyframes and internal CSS variables;
- CSS-anchor declaration details and fallback order; and
- the absence or presence of an extracted private helper module.

Any change to stable anatomy, semantics, slot cardinality, callback detail,
open ownership, or styling contracts requires migration review. A later browser
baseline may replace internal placement or animation mechanics without changing
the public API.

## 19. Public documentation contract

The public guide must explain, in this order:

1. at-a-glance visual states and placements;
2. the smallest activator/title/body composition;
3. interactive body content and explicit actions;
4. controlled visibility;
5. dismissal and unavailable-activator behavior;
6. placement and trigger-width matching;
7. nested Popovers and the boundary with Menu/Tooltip/Dialog;
8. focus, keyboard, forms, responsive behavior, and customization; and
9. terse generated API reference.

Every preview uses one coherent theme per page, concise copy, rendered examples
early, controls visually outside the rendered specimen, collapsed code by
default, and no intentional console diagnostics. Planned previews:

| File | Job |
|---|---|
| `at_a_glance.py` | six astronomy specimens across placement/open/content states |
| `moon_inspector.py` | smallest complete composition |
| `interactive_form.py` | retained native controls and explicit close action |
| `controlled_open.py` | owner accepts/declines requests |
| `dismissal.py` | dismissible and explicit-only behavior |
| `placements.py` | six placements and match width |
| `nested_popovers.py` | nested top-layer ownership |
| `customization.py` | variables, class/style, two brand adaptations |
| `responsive_content.py` | narrow, long, RTL, and scroll behavior |

The API reference is generated from `api.yml`; prose must not duplicate its
tables by hand.

## 20. Open decisions and deferred work

Resolved for the first release:

- native manual Popover, not portal or inline absolute positioning;
- required native Button activator and visible title;
- non-modal dialog semantics with initial and return focus but no trap;
- six proved block-axis placements, preferred rather than guaranteed;
- explicit action markers rather than close-on-any-content-click;
- one shared private controller with generation-owned Web Animations; and
- no public universal Overlay/Popup component.

Deferred until evidence justifies expansion:

- inline-start/inline-end placements and arrows after cross-browser geometry
  and collision evidence;
- virtual/range/cursor anchors and multiple triggers;
- portal/transport escapes after a real top-layer limitation;
- rendered-placement reflection when CSS exposes a reliable mechanism;
- modal Popover mode, which should normally be Dialog;
- imperative methods after a job cannot use client `open`.
