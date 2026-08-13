# Citry UI Tooltip component specification

**Status (2026-08-09): production implementation pass complete. The runtime,
exports, structured API, ten public previews, focused server and
Chromium/Firefox/WebKit tests, retained-rerender evidence, quality/scaling
wiring, docs projection, and exact wheel qualification are checked in. Human
visual/assistive-technology review, hosted Nu evidence, and independent review
remain release qualification; delegation is unavailable under the active
policy.**

## 1. Purpose and product bar

`CTooltip` supplies a brief, noninteractive description for one focusable
element. It appears on keyboard focus or fine-pointer hover, remains hoverable,
can be dismissed with Escape without moving focus, and never becomes a second
control surface.

The production bar is an accessible, styled, server-rendered Tooltip with
shared hover warm-up, a pointer bridge, focus parity, touch suppression,
controlled and uncontrolled visibility, logical collision-aware placement,
retained-rerender cleanup, and public customization comparable to a mature
suite such as Vuetify.

Common jobs and shortest paths:

| Job | Shortest path | Classification |
|---|---|---|
| Explain an icon-only Button | `text` plus an activator fill | direct API |
| Add a longer static phrase | default fill instead of `text` | direct API |
| Update a description from browser state | client `text` in text mode | client API |
| Show on focus without hover delay | built in | direct behavior |
| Tune hover timing | `delay` and `close_delay` | direct API |
| Control visibility in Alpine | client `open` and `onOpenChange` | client API |
| Align to a logical edge | `placement` | direct API |
| Change width, color, radius, offset, or motion | public CSS variables | CSS |
| Put links, controls, or rich help in the surface | `CPopover` | separate component |
| Expose essential instructions | persistent visible text or Field description | composition |

Smallest template:

```citry-html
<c-CTooltip text="Inspect Europa">
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">
      Europa
    </c-CButton>
  </c-fill>
</c-CTooltip>
```

Tooltip text supplements the trigger's accessible name; it never replaces the
name. Non-goals are interactive content, persistent help, validation messages,
touch long-press, mouse-following geometry, arrows, portals, virtual anchors,
modal behavior, and a public generic Overlay.

## 2. Prior art and complaints

Current sources were checked on 2026-08-09.

| Source | Version or review date | Evidence | Decision supported |
|---|---|---|---|
| WAI-ARIA APG | 2026-08-09 | [Tooltip pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/) | `role="tooltip"`, `aria-describedby`, focus remains on trigger, Escape, noninteractive content |
| WCAG 2.2 | 2026-08-09 | [Content on Hover or Focus](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html) | Tooltip must be dismissible, hoverable, and persistent |
| Vuetify | 4.1.8 | [`VTooltip`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VTooltip/VTooltip.tsx), `VOverlay` inputs/source | activator relationship, eager content, connected placement, controlled state, concise text shorthand |
| React Aria Components | current 2026-08-09 | [Tooltip](https://react-aria.adobe.com/Tooltip) and `useTooltipTrigger` | global warm-up/cool-down, immediate focus opening, no touch Tooltip, close-on-press |
| Radix Primitives | Tooltip 1.2.13 | [Tooltip](https://www.radix-ui.com/primitives/docs/components/tooltip) and release notes | provider delay/skip-delay, hoverable content, controlled state, trigger/content anatomy, historical delay bug |
| Mantine | 9.5.1 | [Tooltip](https://mantine.dev/core/tooltip/) | one trigger, open/close delay, grouped delay, focus/touch event configuration evidence |
| Web Awesome | 3.11.0 | [Tooltip](https://webawesome.com/docs/components/tooltip/) | Web Component boundary and CSS customization evidence |
| Mantine issue #9072 | closed/fixed report reviewed 2026-08-09 | Tooltip content was not hoverable under the affected contract | test the actual pointer bridge, not only trigger hover |

Adopted patterns:

- one focusable activator and one always-authored descriptive surface;
- text shorthand plus an exclusive static content slot;
- focus opens immediately; first fine-pointer hover uses a delay;
- after one Tooltip is shown, nearby peers warm up and open immediately;
- the surface itself keeps hover visibility alive;
- Escape and trigger press dismiss without moving focus;
- `aria-describedby` remains present so assistive technology can obtain the
  description independently of visual delay; and
- touch does not trigger a visual Tooltip.

Rejected patterns:

- Vuetify's `interactive` option: interactive content is `CPopover`;
- configurable focus-off behavior: keyboard access is mandatory;
- touch long-press: the interface must remain usable without Tooltip;
- broad VOverlay geometry, scroll, portal, scrim, focus, and z-index inputs;
- arbitrary children as activator without a settled-DOM focusability check;
- title-attribute fallback, because browser Tooltip timing and styling are not
  the authored component contract; and
- a public provider/group component solely for delay sharing.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `text` / default content | direct API | `text` or default fill | adopt, mutually exclusive |
| activator slot/props | scoped slot | `activator_attrs` | adopt with one focusable settled root |
| `modelValue` and update event | client API | `open`, `onOpenChange` | adopt controlled/uncontrolled ownership |
| `disabled` | direct API | `disabled` | adopt Tooltip-local availability |
| open/close delays | direct API plus shared private warm-up | `delay`, `close_delay` | adopt concise surface |
| `location`, offset, flipping | direct API/CSS | six `placement` values and `--cui-tooltip-offset` | narrow to proved subset |
| `interactive` | separate component | `CPopover` | reject from Tooltip |
| color, width, transition | CSS | public variables, `class_`, `style` | capability without prop parity |
| portal/attach/contained/absolute | fixed private transport | native top layer, no relocation | reject public transport switches |
| click/context-menu activators | separate behavior | Popover/Menu | reject |
| methods and generic Overlay slots | ordinary client state/composition | none | omit |

## 3. Public composition and anatomy

```text
CTooltip (private host)
├─ activator fill → exactly one focusable HTMLElement carrying activator_attrs
└─ div[popover=manual][role=tooltip]  public semantic/styled root
```

The activator remains owned by its authored component. `class_`, `style`, and
`attrs` target the Tooltip surface. The private host and generated anchor name
are not public anatomy.

The activator fill is required and must spread `activator_attrs` onto exactly
one enabled/focusable HTML element. Native Buttons, links with `href`, inputs,
and explicit `tabindex="0"` elements qualify. A disabled native control does
not; expose any useful explanation persistently or choose a separate focusable
owner rather than creating a pointer-only Tooltip.

The surface ID comes from `id` or a generated Citry identity. The trigger owns
`aria-describedby=<surface-id>`. Existing trigger description IDREFs may be
composed by using the provided `tooltip_id`; runtime normalization preserves
unique tokens already present when it adds the Tooltip ID.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `id` | `str | None` | generated | structural | nonempty HTML ID without ASCII whitespace or U+0000 |
| `text` | `str | None` | `None` | structural/fallback | nonempty plain text; exactly one of `text` and default fill |
| `open` | `bool` | `False` | initial state | server/no-JavaScript state and uncontrolled fallback |
| `disabled` | `bool` | `False` | reactive configuration | suppresses requests and derived visible state |
| `delay` | `int` | `600` | reactive configuration | first fine-pointer hover delay in milliseconds, 0–60,000 |
| `close_delay` | `int` | `100` | reactive configuration | pointer bridge delay in milliseconds, 0–60,000 |
| `placement` | `CTooltipPlacement` | `"top"` | reactive configuration | preferred logical placement |
| `class_` | `CClassValue | None` | `None` | styling | surface classes |
| `style` | `CStyleValue | None` | `None` | styling | surface inline style; private anchor ownership wins |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted customization | allowed surface attributes after ownership checks |

| Client input | Type | Omitted | `null` | Invalid value | Effect |
|---|---|---|---|---|---|
| `open` | `boolean | null` | release control | release control | report once and release | controlled visibility while Boolean |
| `text` | nonempty string | server text | invalid | report once, server fallback | updates text-mode content only; rejected in slot mode |
| `disabled` | boolean | server value | invalid | report once, server fallback | Tooltip-local availability |
| `delay` | integer 0–60,000 | server value | invalid | report once, server fallback | pending/future hover timing |
| `closeDelay` | integer 0–60,000 | server value | invalid | report once, server fallback | pointer bridge timing |
| `placement` | six-value enum | server value | invalid | report once, server fallback | requested placement/reflection |
| `onOpenChange` | function or null | none | none | report once, none | visibility request callback |

`disabled` dominates `open`: a disabled Tooltip is hidden even when an owner
supplies `open=True`; re-enabling reapplies the current controlled or
uncontrolled state. Client values beat server fallbacks while valid. Every
invalid episode reports once until a valid or omitted value ends it.

## 5. State model

Public logical state is open or closed. Internal sources track trigger focus,
trigger hover, surface hover, a pending warm-up, a pending pointer bridge,
controlled ownership, disabledness, and a dismissal latch.

| Transition | Guard | Request/commit | Result |
|---|---|---|---|
| focus enters activator | enabled, latch clear | immediate open request | focus stays on activator |
| fine pointer enters activator | enabled, latch clear | delayed or warmed immediate request | surface opens without focus movement |
| pointer enters surface | already open/pending close | cancel close | remains open |
| pointer leaves both | no activator focus | close after `close_delay` | bridge remains hoverable |
| activator blur | neither surface nor trigger hovered | immediate close | new focus destination remains |
| Escape | open | immediate close request and latch | focus unchanged; no immediate reopen |
| trigger press | open | immediate close request and latch | native activation continues |
| peer Tooltip opens | open | immediate `peer` close request | shared warm state remains |
| touch pointer/following focus | uncontrolled | no visual open | native activation continues |
| valid client `open` | controlled | owner commit | exact supplied state, unless disabled |
| client `open` omitted/null | controlled | release | preserve current committed state |

The dismissal latch clears only after focus and pointer have both left the
activator/surface pair. This satisfies Escape dismissal while the trigger
remains focused or hovered. Opening one Tooltip warms the document group;
peers entered while it is open or within a private 300 ms cooldown skip their
hover delay. Focus always opens immediately.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CTooltip` | `activator` | yes | one settled focusable element | `{activator_attrs: dict[str, object], tooltip_id: str}` | none |
| `CTooltip` | `default` | iff `text` omitted | one static noninteractive content region | `{}` | escaped `text` |

`text` and the default fill are mutually exclusive. Default content may contain
noninteractive phrasing and simple formatting. It must not contain links,
Buttons, inputs, form-associated elements, editable content, focus targets,
widgets, nested Tooltips, or essential instructions. Settled-DOM validation
rejects known interactive/focusable descendants.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onOpenChange` | `(requestedOpen, CTooltipOpenChangeDetail)` | hover/focus, pointer leave/blur, Escape, press, peer, native visibility | after delay when applicable, before owner commit when controlled | owner must update `open`; unchanged value declines | no return-value cancellation |

`detail.reason` is `hover`, `focus`, `pointer-leave`, `blur`, `escape`,
`press`, `peer`, `native`, `ancestor`, or `modal`; it also supplies
`controlled`, `forced`, and browser `source`. Ancestor and modal safety closes
set `forced: true` and cannot be declined. Owner commits do not notify. Native
trigger events remain ordinary Alpine `@...` events, and Tooltip never
prevents the trigger's activation.

No public methods are needed. Client state and refs cover the supported jobs.

## 8. Semantics, keyboard, focus, and assistive technology

The surface is `div[role="tooltip"]`. The trigger references it through
`aria-describedby`; Tooltip does not name the trigger. The visual surface does
not receive focus and cannot contain focusable content.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| keyboard | focus trigger | open immediately | stays on trigger | no |
| keyboard | Escape while open | close and latch | stays where it is | yes, only for the top owned layer |
| keyboard | Tab/Shift+Tab | native navigation | moves normally; Tooltip closes | no |
| pointer | fine hover | open after warm-up | unchanged | no |
| pointer | move onto Tooltip | remains open | unchanged | no |
| pointer | activate trigger | close, then native action | native behavior | no |
| touch | tap | no visual Tooltip | native behavior | no |

Tooltip text must never be the only source of an accessible name, instructions,
validation feedback, or task-critical information. Assistive technology can
resolve the referenced description even while the visual top-layer surface is
closed.

## 9. Native forms and validation

Tooltip is not a form participant. It never changes trigger `name`, value,
disabledness, submission, reset, validation, or Form owner. Tooltip content
cannot contain form controls. A form control may be the activator when enabled
and focusable; its existing form and Field relationships remain authoritative.

## 10. Styling and theme contract

There are no semantic variants or sizes in the first release.

| Public variable | Type | Purpose | Default |
|---|---|---|---|
| `--cui-tooltip-background` | color | surface background | strong CanvasText mix |
| `--cui-tooltip-foreground` | color | text | Canvas |
| `--cui-tooltip-border-color` | color | boundary | transparent/light mix |
| `--cui-tooltip-border-width` | length | boundary width | `1px` |
| `--cui-tooltip-radius` | length | corners | `0.375rem` |
| `--cui-tooltip-shadow` | shadow | top-layer elevation | subtle shadow |
| `--cui-tooltip-max-inline-size` | length | maximum line width | `18rem` |
| `--cui-tooltip-padding-block` | length | block padding | `0.375rem` |
| `--cui-tooltip-padding-inline` | length | inline padding | `0.625rem` |
| `--cui-tooltip-offset` | length | activator gap | `0.375rem` |
| `--cui-tooltip-duration` | time | entry/exit | `100ms` |
| `--cui-tooltip-easing` | easing | entry/exit | standard emphasized ease |

| Public selector | Element | Stable relationship |
|---|---|---|
| `[data-citry-ui-part="tooltip"]` | semantic/styled surface | one per `CTooltip`; `attrs` destination |

| Public attribute | Values | Meaning |
|---|---|---|
| `data-open` | present/absent | logical visible state, absent during exit |
| `data-placement` | six placement values | requested placement, not collision result |

Defaults use zero-specificity rules in `citry-ui.theme`. Public variables are
inherited inputs resolved through private effective variables. Unlayered
consumer CSS and correctly ordered named layers can override defaults.

## 11. Environmental behavior

- logical placement and dimensions support RTL;
- long words and text wrap; the surface never creates horizontal viewport
  overflow at 200/400 percent zoom;
- the Tooltip is hoverable with large pointers and keeps a close-delay bridge;
- `prefers-reduced-motion` sets duration to zero;
- forced colors preserves a boundary and readable text;
- dark and nested color schemes inherit through retained DOM ancestry;
- print omits Tooltips; persistent source text must live outside them; and
- no library-authored visible string exists beyond consumer Tooltip content.

## 12. Overlay and layering behavior

Tooltip uses native `popover="manual"`, CSS anchors, the private shared layer
stack, and generation-owned Web Animations. It is not relocated, does not lock
scroll, does not inert the page, and does not add a scrim or focus scope.

The preferred placement subset is `top-start`, `top`, `top-end`,
`bottom-start`, `bottom`, and `bottom-end`, with block/inline collision
fallback. There is no arrow because current CSS does not expose the rendered
fallback side reliably enough to orient one.

Tooltip registers above its enclosing Popover/Dialog layer. Escape dismisses
only the top Tooltip first. A newly opened peer requests immediate closure of
the previous Tooltip. The owner-document coordinator's Document/open-ShadowRoot
listeners and modal observer exist only while an anchored layer is open.

## 13. Collections, async data, and identity

Tooltip is not a collection or async owner. Browser text mode can update from
application state but does not fetch, debounce, announce, or resolve results.
Async or essential changing help belongs in visible content, Alert, or Popover.
Identity comes only from `id` or generated Citry identity; raw text never
becomes an ID.

## 14. Server render, morph, and cleanup

The server renders the complete trigger relationship and Tooltip content.
Closed content stays hidden. An initially open Tooltip has a readable
no-JavaScript in-flow fallback; client activation upgrades it to the top layer.

On retained correlated rerender, uncontrolled committed visibility, pending
dismissal latch, and relevant focus/pointer ownership are handed to the new
initializer where the retained elements allow it. Latest controlled state and
configuration win. Text-mode edits from a valid client prop remain controlled;
slot content follows the server morph.

Cleanup cancels warm-up, bridge, animation, and reconciliation tasks; removes
trigger/surface listeners; unregisters the layer and peer owner; hides native
top-layer presence; and leaves no stale shared listener. Reinitialization is
idempotent. Raw consumer DOM removal outside Citry lifecycle is not a supported
cleanup signal.

## 15. Security and content trust

Python `text` is de-trusted to an exact plain string before escaping. Slot
content follows ordinary Citry escaping. Client `text` writes `textContent`,
never HTML.

`class_`, `style`, and `attrs` are explicit trusted customization surfaces.
The attrs mapping is copied once per render. Surface attrs reject, case
insensitively, owned identity, semantics, focus, presence, relationship, and
reflection attributes; their dynamic/property aliases; Citry/Events runtime
namespaces; object spreads; and structural/ownership directives such as
`x-html`, `x-text`, `x-if`, `x-for`, `x-show`, `x-ignore`, `x-teleport`,
`x-model`, and `x-modelable`.

Settled-DOM validation rejects interactive, focusable, editable, and
form-associated Tooltip descendants. The generated activator marker and
description relationship are the only supported behavior attachment path.

## 16. Assets and performance

One Tooltip contributes static CSS and one initializer. It adds no icon, font,
positioning dependency, portal, per-instance observer, geometry loop, or
per-frame work.
Each instance owns bounded trigger/surface listeners, at most one warm-up timer,
one close timer, and one animation. Open anchored layers share one capture
listener set and one modal observer per active Document/open-ShadowRoot scope.

The diagnostic scaling tool is wired for 1, 10, 100, 500, and 1,000
server-rendered Tooltips and output bytes; checked-in tests exercise bounded
1- and 10-instance samples, while scheduled runs own the complete count set.
Browser tests prove closed instances leave no scope listener, peer warm-up uses
the shared listener set, and repeated closure/rerender returns layer
registrations to the expected count. These are diagnostics, not hard timing
gates.

## 17. Acceptance matrix

Checked-in focused evidence covers:

- schemas, type hints, defaults, text/slot exclusivity, all validation and
  reserved attrs/directives, safe-string de-trusting, and one-read snapshots;
- semantic anatomy, generated/merged description IDREFs, no-JavaScript
  open/closed output, text mode, static slot mode, and zero portal output;
- focus-immediate opening, delayed/warmed hover, close-delay bridge, surface
  hover, blur, Escape latch, press, peer replacement, touch suppression, and
  controlled request/decline and owner reconciliation;
- one direct focusable activator, disabled/unfocusable failure, interactive
  Tooltip-content failure, and native focus preservation;
- placement reflection and CSS-anchor ownership, live text, long wrapping,
  two scheme-aware brands, public variable overrides, reduced-motion/forced
  color rules, and print omission;
- retained rerender, pending timer cancellation, one shared layer registration,
  listener cleanup, and settled-DOM failure paths; and
- Chromium/Firefox/WebKit behavior smoke, shared axe scenario, package exports,
  structured API/schema validation, ten docs previews and their live browser
  interactions, asset/scaling wiring, and exact wheel contents.

Release qualification still needs hosted Nu output, explicit AX-description
sampling across screen readers, exhaustive placement/collision screenshots,
real touch hardware, nested scroll/viewport-change review, high zoom, forced
colors, and manual animation/reversal review. These are not claimed by the
focused suite.

Human release evidence remains keyboard-only, large pointer, touch device,
VoiceOver/NVDA/JAWS description timing, visual placement/collision review,
zoom, forced colors, reduced motion, and representative application use.

## 18. Compatibility classification

Stable public API includes `CTooltip`, nested schemas, server/client inputs,
the activator/default slots and data, callback shape/reasons, public variables,
selector, reflections, and validation errors.

Stable behavior includes one focusable activator, `role="tooltip"` plus
`aria-describedby`, focus/hover parity, shared warm-up, hoverability, Escape
dismissal without focus movement, press closure, touch suppression,
noninteractive content, controlled ownership, and no portal.

Exact colors, spacing, radius, shadow, duration, and easing are evolvable.
Private host markup/class, `.cui-*` classes, `--_cui-*` variables, generated
IDs/anchor names, cooldown duration, controller symbols, timers, listener
organization, keyframes, and placement implementation are private.

## 19. Public documentation contract

The guide explains, in reader order:

1. visual examples and the Tooltip/Popover boundary;
2. concise text mode and one focusable activator;
3. keyboard, hover, Escape, press, and touch behavior;
4. static slot content and client text updates;
5. delays and shared warm-up;
6. controlled visibility and disabling;
7. placement, RTL, narrow content, and customization; and
8. terse generated API reference.

All examples use an astronomy theme, concise direct copy, rendered specimens
early, controls outside the rendered surface, collapsed code, and zero
intentional console errors.

| File | Reader job and evidence |
|---|---|
| `at_a_glance.py` | compare three descriptions and shared warm-up |
| `moon_labels.py` | Button, link, and accessible icon-control activators |
| `formatted_description.py` | static formatted content and the Popover boundary |
| `live_text.py` | client text derived from browser state |
| `timing.py` | first-hover and close-bridge timing |
| `controlled_open.py` | controlled request, accept, and decline behavior |
| `placements.py` | six placement controls and RTL |
| `dismissal.py` | focus, Escape latch, and revisiting the activator |
| `customization.py` | public variables and two scheme-aware brands |
| `responsive_text.py` | RTL, narrow surfaces, and unbroken text |

`api.yml` owns exhaustive Inputs, Slots, Events, Methods, CSS, Attributes,
Selectors, and Interfaces tables. `api.md` does not duplicate them.

## 20. Open decisions and deferred work

Resolved for the first release:

- text shorthand plus exclusive static default content;
- mandatory focus and hover behavior;
- no touch visual Tooltip;
- global private warm-up with 600 ms first-hover and 300 ms cooldown;
- 100 ms pointer bridge by default;
- six block-axis logical placements, no arrow;
- native manual Popover transport without portal; and
- interactive content delegated to `CPopover`.

Deferred until evidence justifies expansion:

- public delay providers/groups;
- arrows after rendered-side reflection exists;
- inline-start/end, virtual, range, or cursor anchors;
- follow-pointer behavior;
- touch long-press;
- imperative methods; and
- extracting a separately shipped public overlay foundation.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
