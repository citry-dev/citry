# Citry UI Alert component specification

**Status (2026-08-08): production pass complete; independent implementation
review found no remaining high- or medium-severity issue.** Runtime, structured
reference, ten public previews, focused evidence, and exact wheel qualification
are checked in. Human visual and assistive-technology review remains release
evidence.

## 1. Purpose and product bar

`CAlert` presents persistent feedback about a page, section, action, or system
condition. It combines useful default styling, an optional title, message
content, a visual intent icon, and optional actions without taking ownership of
visibility, focus, or a notification queue.

The production bar is a styled, useful-by-default feedback surface with clear
light and dark treatments, color-independent intent cues, concise server and
client configuration, long-content and narrow-layout behavior, stable theme
hooks, deliberate live-region semantics, and no hidden dismissal lifecycle.
The closest standards patterns are an ordinary native `div`, `role="status"`
for polite updates, and `role="alert"` for urgent updates.

Common jobs and their shortest intended surfaces:

| Job | Template | Python composition | Support path |
|---|---|---|---|
| Show persistent information | `<c-CAlert>Comet viewing begins at 22:40.</c-CAlert>` | `CAlert(slots={"default": "Comet viewing begins at 22:40."})` | direct API |
| Show success, warning, or error feedback | `intent="success"`, `intent="warn"`, or `intent="error"` | same | direct API |
| Add a title | `<c-fill name="title">Telescope aligned</c-fill>` | `slots={"title": "Telescope aligned"}` | direct slot |
| Add related actions | `<c-fill name="actions"><c-CButton>Retry</c-CButton></c-fill>` | `slots={"actions": retry_button}` | slot and composition |
| Label an action group | `actions_label="Camera recovery"` | `actions_label="Camera recovery"` | direct API |
| Hide the intent icon | `c-icon="False"` | `icon=False` | direct API |
| Choose another registered icon | `icon_name="star"` | `icon_name="star"` | direct server input |
| Change visual emphasis | `variant="solid"` | `variant="solid"` | direct API |
| Change spacing and text scale | `size="sm"` | `size="sm"` | direct API |
| Derive presentation in the browser | `$c-props="{ intent: condition, variant: emphasis }"` | same rendered component | client inputs |
| Mark a nonurgent update for announcement | `announce="polite"` | `announce="polite"` | direct API with bounded live-region semantics |
| Mark an urgent update for announcement | `announce="assertive"` | `announce="assertive"` | direct API with bounded alert semantics |
| Dismiss feedback | consumer-owned conditional rendering plus an action Button | same | application composition |
| Guarantee queued announcements | future persistent announcer service | future extension | separate component or service |
| Show transient notifications | future Toast or Notification family | future component | separate family |
| Require an immediate decision | future AlertDialog or reviewed Dialog semantic mode | future component | unsupported by current Alert and Dialog APIs |

Production completeness includes server-only rendering, client presentation
updates, ordinary links and controls in actions, public variables and
selectors, nested color schemes, RTL, forced colors, print, hostile content,
and exact package evidence.

Non-goals:

- Alert does not own open state, a close Button, a close callback, timeout,
  focus restoration, animation, or DOM removal.
- Alert does not guarantee that inserting a pre-populated live region will be
  announced by every browser and assistive-technology pair. A reliable
  announcer needs a persistent owner and a separately qualified contract.
- Toast queues, banners, Form summaries, empty states, progress, and alert
  dialogs remain separate jobs.
- `intent` describes visual meaning. It does not imply announcement urgency.
- Alert never moves focus and is not a keyboard widget.
- No headless variant ships in this pass.

## 2. Prior art and complaints

The shared taxonomy reports Alert coverage in 9 of 12 surveyed suites. Local
prior art repeatedly needed persistent feedback but did not establish one
consistent announcement or dismissal owner.

### Current-source record

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI | workspace reviewed 2026-08-08 | Icon, Button, Dialog, Card, Field, Form, component policy, theme contract, inventory, and quality harness | Reuse concise intents and sizes, registered icons, explicit slots, public variables and selectors, trusted attrs rules, and independent visual/client configuration. |
| Vuetify | 4.1.8 reviewed 2026-08-08 | [`VAlert` source](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VAlert/VAlert.tsx), [Alert CSS](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VAlert/VAlert.sass), and API | Weight its full styled anatomy, contextual types, default icons, title/text/actions, variants, density, and close composition most heavily. Reject always-assertive semantics, built-in model ownership, broad layout props, and root clipping. |
| Material UI | 9.3.1 reviewed 2026-08-08 | [Alert guide and accessibility guidance](https://mui.com/material-ui/react-alert/), Alert and AlertTitle sources, actions, icon mapping, and variants | Adopt clear intents, soft/solid/outline treatments, optional title/icon/actions, no focus movement, and explicit urgency guidance. Keep dismissal consumer-owned. |
| Chakra UI | 3.36.1 reviewed 2026-08-08 | [Alert guide](https://chakra-ui.com/docs/components/alert) and alert recipe source | Adopt `sm`/`md`/`lg`, info/success/warning/error meaning, stable anatomy, and a quiet default treatment. Use one closed component instead of requiring six compound tags. |
| Mantine | 9.5.1 reviewed 2026-08-08 | [Alert guide](https://mantine.dev/core/alert/), Alert source, styles API, title, icon, and close behavior | Confirm persistent message, title, icon, body, and close-action demand. Reject an unconditional alert role and built-in close lifecycle. |
| Bootstrap | 5.3.8 reviewed 2026-08-08 | [Alert guide](https://getbootstrap.com/docs/5.3/components/alerts/), arbitrary content, icons, dismissal, CSS variables, and accessibility notes | Adopt flexible persistent content and runtime variables. Avoid color-only meaning and focus loss after component-owned removal. |
| Web Awesome | 3.11.0 reviewed 2026-08-08 | [Callout guide](https://webawesome.com/docs/components/callout/), variants, appearances, sizes, icon slot, parts, and styling | Treat Callout as the passive presentation boundary of Alert. Adopt optional icon and ordinary CSS customization without adding a second export. |
| WAI-ARIA APG and ARIA | alert example updated 2026-01-20, reviewed 2026-08-08 | [Alert pattern](https://www.w3.org/WAI/ARIA/apg/patterns/alert/), role semantics, atomicity, and no-keyboard contract | Use `role="alert"` only for genuinely urgent updates; add no keyboard behavior or focus shift. |
| MDN | reviewed 2026-08-08 | [Alert role](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/alert_role) and [live-region guidance](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions) | Do not duplicate role plus explicit live attributes. Document initial-render and assistive-technology variability. |

### Material shortcomings and consequences

| Shortcoming | Current evidence | Citry consequence |
|---|---|---|
| Several styled suites give every Alert `role="alert"`, even for ordinary static information. | Current Vuetify and Mantine source; MUI explicitly warns that its assertive default is too aggressive for less urgent messages. | Default `announce="off"`; keep visual intent separate from off, polite, or assertive announcement semantics. |
| Removing a focused dismiss Button can lose focus or reset it to the document start. | Bootstrap 5.3 dismissal documentation describes the failure and requires application-specific focus recovery. | Alert does not own dismissal. The owner that removes it also chooses the correct focus destination. |
| Filled Alert colors can require special contrast overrides. | [MUI issue 33512](https://github.com/mui/material-ui/issues/33512), closed without a runtime change and retained as documentation work. | Test every default intent and variant pairing in both schemes; public foreground, background, border, and icon variables remain independently overridable. |
| Root clipping can cut off nested action overlays. | Vuetify Alert CSS uses `overflow: hidden`; this is a known general overlay risk in composed surfaces. | Alert root, content, and actions do not clip overflow or create a stacking context. |
| A populated live region inserted as one node is not a universal announcement service. | MUI and MDN live-region guidance distinguish dynamic updates, page-load content, and browser/assistive-technology variability. | The announcement input exposes honest semantics but not queue, deduplication, timing, or delivery guarantees. Persistent announcer work remains separate. |

### Patterns adopted and rejected

Citry adopts one closed styled Alert with title, message, icon, and action
slots; four concise visual intents; three appearances and sizes; client
presentation inputs; public variables and selectors; and opt-in live-region
semantics. It rejects always-assertive output, built-in removal, automatic
timers, arbitrary color props, whole-root replacement, root clipping, and a
second Callout export with the same job.

### Vuetify disposition

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `type` success/info/warning/error | direct API | `intent` info/success/warn/error | Adopt with the suite's concise `warn` spelling. |
| default contextual icon | direct API | `icon=True` plus intent-owned registered CIcon | Adopt; the icon tracks client intent. |
| custom or no icon | direct API | registered `icon_name`; `icon=False` | Adopt registered names without an arbitrary-markup indicator slot. |
| title prop and title slot | direct slot | `title` | Slot avoids a duplicate string and markup API. |
| text prop, text slot, and default slot | direct slot | default message slot | One content surface is enough. |
| prepend | registered icon input | `icon_name` | Adopt the visual-indicator job without an unrestricted slot. |
| append | actions slot | `actions` | Name the user job, not physical placement. |
| close and close slot | application composition | Button in `actions` plus owner-managed conditional render | Reject hidden visibility and focus ownership. |
| `closable`, `modelValue`, and update events | application state | none | Omit. Alert has no open state. |
| role alert | direct API | `announce="assertive"` | Opt in instead of applying to every Alert. |
| less urgent announcement | direct API | `announce="polite"` | Add because visual intent is not urgency. |
| variants and flat/text/plain/elevated treatments | direct API and CSS | soft/solid/outline plus public variables | Consolidate to three clear Alert jobs. |
| density | direct API | `size` sm/md/lg | Use suite vocabulary. |
| prominent and icon size | CSS or size | `size`, icon selector, and variables | Omit a second emphasis Boolean. |
| border, border color, rounded, elevation | variant and public CSS | `variant` and variables | Consolidate appearance without broad one-off props. |
| color and theme | public CSS | intent selectors and variables | Keep meaning and palette related; no arbitrary color prop. |
| width, height, location, position, and tag | native CSS/composition | `class_`, `style`, `attrs`, surrounding layout | Alert stays a static neutral `div`. |
| native close event | native listeners on consumer action | ordinary Button events | No component-authored callback. |
| methods | none | none | Omit. |

## 3. Public composition and anatomy

Smallest template:

```citry-html
<c-CAlert>
  Comet viewing begins at 22:40.
</c-CAlert>
```

Full template:

```citry-html
<c-CAlert
  intent="warn"
  actions_label="Cloud cover actions"
>
  <c-fill name="title">
    Cloud cover approaching
  </c-fill>
  <c-fill name="default">
    The western ridge may obscure the observatory after midnight.
  </c-fill>
  <c-fill name="actions">
    <c-CButton size="sm" variant="outline">
      View forecast
    </c-CButton>
  </c-fill>
</c-CAlert>
```

Python composition:

```python
from citry_ui import CAlert

forecast_alert = CAlert(
    intent="warn",
    slots={
        "title": "Cloud cover approaching",
        "default": "The western ridge may obscure the observatory after midnight.",
    },
)
```

Stable anatomy:

```text
div[data-citry-ui-part="alert"]
├── div[data-citry-ui-part="indicator"]   decorative, aria-hidden; may be hidden
├── div[data-citry-ui-part="content"]     announcement role lands here
│   ├── div[data-citry-ui-part="title"]?
│   └── div[data-citry-ui-part="message"]?
└── div[data-citry-ui-part="actions"]?
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CAlert` | neutral `<div>` | `class_`, `style`, and `attrs` land on root; `actions_attrs` and the owned action-group label land on the optional action group | At least one of title or default message; zero or one title, default, and actions fill. Announcement role applies only to content, so action labels are not part of the live-region message. |

The stable order is icon, content, then actions. The icon wrapper always
renders so a client `icon` value can show an icon even when the server fallback
was false. Effective `icon=False` applies the native `hidden` attribute.
With `icon_name=None`, the wrapper contains the four registered intent icons
as private groups inside one package-owned SVG shell and exposes only the
current group. A supplied `icon_name` renders one fixed registered glyph in
the same shell. The wrapper is `aria-hidden="true"`; the SVG is not focusable,
icons are decorative, and essential meaning remains in title or message text.

Native `hidden` alone is not a sufficient visual mechanism because ordinary
author `display` rules can override the user-agent default. Alert CSS therefore
owns a final, important `display: none` rule for the hidden HTML indicator.
Inactive SVG groups use a private `data-cui-alert-hidden` marker because
`hidden` is not valid on SVG `<g>`. The same owned rule keeps both cases at
zero geometry.

The title and message wrappers render only when their fills are supplied. At
least one is required. A title does not choose a heading rank. Authors place an
appropriate native heading inside the title fill when the Alert introduces a
document section.

The actions wrapper renders only for an actions fill. It may contain Buttons,
links, menus, or other ordinary interactive content. `actions_label` adds the
owned `group` role and nonempty accessible name without introducing an extra
layout wrapper. A nonempty `actions_attrs` mapping or supplied `actions_label`
without an actions fill raises `ValueError`.

Unknown and duplicate fills use Citry's ordinary slot errors. No subcomponent
is needed because fixed named slots preserve the complete anatomy with less
markup.

Post-implementation simplification must try title-only, message-only,
title-plus-message, icon-off, fixed-icon, action-only-adjacent, long action,
and nested component cases. Any wrapper without a documented job remains
private or is removed.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `intent` | `Literal["info", "success", "warn", "error"]` | `"info"` | reactive presentation | Selects visual colors and the automatic icon. It never chooses announcement urgency. |
| `variant` | `Literal["soft", "solid", "outline"]` | `"soft"` | reactive presentation | Selects background, foreground, and border emphasis. |
| `size` | `Literal["sm", "md", "lg"]` | `"md"` | reactive presentation | Selects spacing, text scale, icon size, and action gap fallbacks. |
| `announce` | `Literal["off", "polite", "assertive"]` | `"off"` | reactive accessibility configuration | Applies no role, `status`, or `alert` to the content wrapper. It does not guarantee delivery from a newly inserted populated node. |
| `icon` | `bool` | `True` | reactive presentation | Shows or hides the automatic or fixed decorative icon wrapper. |
| `icon_name` | `CIconName | None` | `None` | structural server-only | Uses one registered decorative icon when supplied. `None` uses the automatic intent icon set. |
| `actions_label` | `str | None` | `None` | structural server-only | Non-whitespace plain text when supplied; CRLF/CR normalize to LF and U+0000 is rejected. Requires the actions slot and emits `role="group"` plus `aria-label` on its wrapper. |
| `class_` | `CClassValue | None` | `None` | server presentation | Adds structured root classes and merges with `attrs`. |
| `style` | `CStyleValue | None` | `None` | server presentation | Adds structured root inline styles and merges with `attrs`. |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted root attributes | Copied per render. Accepts unrelated native, ARIA, data, and targeted Alpine attributes, including consumer-owned visibility. Cannot replace semantics, children, public mirrors, part markers, or Citry runtime ownership. |
| `actions_attrs` | `Mapping[str, object] | None` | `None` | trusted action-group attributes | Copied per render. Accepts unrelated native, ARIA, data, and targeted Alpine attributes. It cannot replace owned role/name, add another focus/live-region owner, replace children or the part marker, or enter Citry runtime ownership. A nonempty mapping requires actions. |

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `intent` | enum | server fallback | invalid | report once per invalid episode and use server fallback | intent mirror, colors, automatic icon |
| `variant` | enum | server fallback | invalid | same | variant mirror and colors |
| `size` | enum | server fallback | invalid | same | size mirror and geometry |
| `announce` | enum | server fallback | invalid | same | announcement mirror and content role |
| `icon` | Boolean | server fallback | invalid | same | icon mirror and wrapper visibility |

Valid client values override their server fallback. Omission releases each
input immediately to the latest server fallback. `null`, wrong types, and
unknown enums never acquire ownership. One diagnostic is reported for a
continuous invalid episode; a valid value or omission ends the episode.

Client intent changes update both color and the automatic icon. A fixed
`icon_name` does not change with intent, but effective `icon=False` still hides its
wrapper. Client announcement changes update semantics without claiming that
changing a role on pre-populated content forces an assistive-technology
announcement.

## 5. State model

Alert has no open, dismissed, selected, pending, or browser-owned content
state. Its effective configuration is the resolved intent, variant, size,
announcement mode, icon visibility, and structural slot presence.

| Trigger | Guard | Commit | Observable result |
|---|---|---|---|
| Initial render | valid server inputs and title or message supplied | server fallback becomes effective | complete styled output and matching public mirrors |
| Client input becomes valid | valid type and enum | client value becomes effective | affected mirrors, styles, icon, or content role update in one effect |
| Client input is omitted | any prior client episode | release to current server fallback | no stale client value remains |
| Client input becomes invalid | continuous invalid episode | fallback stays effective | one diagnostic; no invalid public mirror |
| Server correlated rerender | retained or replaced root | new server inputs and slots become fallbacks | initializer reruns; structural content follows server output |
| Consumer removes Alert | owner-specific condition | DOM removal | Alert performs no focus movement or callback |

Repeated same-value client inputs do not rewrite unchanged attributes or icon
visibility. Presentation changes never move focus, dispatch a custom event, or
create a live-region queue.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CAlert` | `title` | conditionally | zero or one | `CAlertTitleSlotData {}` | Wrapper omitted; default message must exist. |
| `CAlert` | `default` | conditionally | zero or one | `CAlertDefaultSlotData {}` | Wrapper omitted; title must exist. |
| `CAlert` | `actions` | no | zero or one | `CAlertActionsSlotData {}` | Wrapper omitted. |

All slot data is server-owned and empty. The actions slot may contain interactive
content. The title and message slots may contain flow content, but authors
remain responsible for valid nesting and heading hierarchy. Dynamic slot names
and whole-content or indicator replacement are unsupported.

## 7. Callbacks, native events, and methods

Alert emits no component callback or custom DOM event and exposes no public
method. Client presentation inputs do not represent user-authored changes, so
there is no `onIntentChange` or equivalent notification.

Native events from links and controls inside actions remain ordinary browser
events. Listen on those controls. Root listeners passed through `attrs` receive
normal bubbling events and must inspect `event.target`; they do not turn Alert
into one large action.

## 8. Semantics, keyboard, focus, and assistive technology

The root is a neutral `div`. The content wrapper receives semantics according
to effective `announce`:

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| Static or already visible feedback | `off` | no live-region role | none | no |
| Nonurgent dynamic update | `polite` | `role="status"` on content | none | no |
| Urgent dynamic update | `assertive` | `role="alert"` on content | none | no |
| Alert with actions | any mode | actions remain outside announcement role | native action Tab order | no |

`status` and `alert` carry their implicit live and atomic semantics. Alert does
not redundantly author `aria-live` or `aria-atomic`, avoiding conflicting or
duplicated announcements.

The component never focuses itself, adds a Tab stop, traps focus, restores
focus, or handles Escape. Actions follow native DOM order after the message.
Forward and reverse Tab visit only authored interactive descendants. A
consumer that removes a focused action must choose the next meaningful focus
destination before or after removal.

Visual intent is never conveyed by color alone: the default icon changes shape
and the authored text must state the condition. Fixed registered icons are hidden from
the accessibility tree. Essential meaning therefore belongs in title or
message text.

An Alert already present at page load, a complete populated Alert inserted in
one operation, or a client role change may not be announced consistently.
`announce` expresses semantic urgency, not guaranteed delivery. Applications
that require queueing, deduplication, retries, or cross-page delivery wait for
the persistent announcer contract.

## 9. Native forms and validation

Alert is not a form participant. It contributes no name/value pair, validation
state, reset behavior, submitter, or default Button. Forms and Fields may
render Alert beside controls or inside their own content, but Alert does not
infer Form ownership.

Buttons inside actions must set the appropriate native `type`; `CButton`
defaults and the surrounding Form contract remain authoritative. A future
FormSummary may coordinate focus, error links, and announcement. It must not be
implemented as hidden behavior inside generic Alert.

## 10. Styling and theme contract

Alert follows [`../ui_theme.md`](../ui_theme.md). The default `soft` variant is
quiet but visibly bounded. `solid` provides the strongest visual emphasis and
must maintain foreground/icon contrast. `outline` keeps a transparent
background and a clear intent-colored boundary. `sm`, `md`, and `lg` adjust
Alert-owned geometry and text scale.

### Public variables

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-alert-background` | color | Root background after intent and variant fallback. | Variant and intent derived. |
| `--cui-alert-foreground` | color | Inherited title, message, and action foreground. | Variant and intent derived. |
| `--cui-alert-border-color` | color | Root boundary color. | Variant and intent derived. |
| `--cui-alert-icon-color` | color | Automatic or fixed registered icon foreground. | Intent color or solid foreground. |
| `--cui-alert-border-width` | length | Root border width. | `1px`. |
| `--cui-alert-radius` | length | Root corner radius. | `0.75rem`. |
| `--cui-alert-padding` | length | Root block and inline padding. | Size-derived. |
| `--cui-alert-gap` | length | Gap between icon, content, and actions. | Size-derived. |
| `--cui-alert-content-gap` | length | Space between title and message. | Size-derived. |
| `--cui-alert-actions-gap` | length | Gap between direct action controls. | Size-derived. |
| `--cui-alert-title-font-weight` | number | Title emphasis without choosing heading semantics. | `650`. |

### Public selectors

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="alert"]` | root surface and attrs destination | every Alert | contains icon, content, then actions in that order when present |
| `[data-citry-ui-part="indicator"]` | decorative automatic or fixed-icon wrapper | always present; native `hidden` plus Alert's owned hidden rule tracks effective icon false | direct child of root; its SVG shell and glyph groups are private implementation |
| `[data-citry-ui-part="content"]` | title/message group and announcement-role destination | every Alert | direct child of root |
| `[data-citry-ui-part="title"]` | optional title wrapper | title supplied | direct child of content |
| `[data-citry-ui-part="message"]` | optional message wrapper | default supplied | direct child of content |
| `[data-citry-ui-part="actions"]` | optional direct-control group and attrs destination | actions supplied | direct child of root |

### Public reflected attributes

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-intent` | `info`, `success`, `warn`, `error` | Effective visual intent. |
| `data-variant` | `soft`, `solid`, `outline` | Effective visual treatment. |
| `data-size` | `sm`, `md`, `lg` | Effective geometry preset. |
| `data-announce` | `off`, `polite`, `assertive` | Effective announcement semantics. |
| `data-icon` | present or absent | Present while the effective icon wrapper is visible. |
| `role` on content | absent, `status`, `alert` | Native role derived from announcement mode. |

Public variables are inherited inputs resolved through private effective
variables. Generic variables override variant and intent fallbacks on an
ancestor or one root. Per-intent brand adaptation uses the stable intent
attribute selector and generic variables. `.cui-*` classes, automatic-icon
selectors, and `--_cui-*` variables remain private.

The root, content, and actions do not set `overflow: hidden`, `z-index`,
transform, isolation, or containment. Nested menus and overlays can escape.

## 11. Environmental behavior

Default tokens provide distinct light and dark soft, solid, and outline
treatments. Nested `color-scheme` scopes resolve independently. Two brand
fixtures must prove that generic public variables and per-intent selectors can
adapt the family without private hooks.

Logical properties and DOM order support RTL without moving the icon away from
the logical start. Long titles, messages, URLs, and action labels wrap instead
of creating horizontal overflow. Actions wrap while preserving native Tab
order. At 200 and 400 percent zoom, message content and actions remain
reachable and no page-level two-dimensional scrolling is introduced by Alert.

Forced colors removes semantic fills as needed, preserves a visible system
border, keeps the intent icon visible, and does not use color as the only cue.
Print removes decorative solid fills and shadow, preserves a readable border,
and keeps message and action text visible. Alert defines no animation, so
reduced-motion behavior is inert. Coarse pointers and touch use the native hit
targets of authored actions.

There are no library-authored visible strings. Titles, messages, and action
labels are application content. Locale and
translation remain outside this family.

## 12. Overlay and layering behavior

Alert neither creates nor controls an overlay. Action content may open Dialog,
Combobox, menu, or other overlays. The Alert root and wrappers do not clip
them or create a stacking context. Overlay ownership, focus, Escape,
positioning, dismissal, and cleanup belong to the nested component.

## 13. Collections, async data, and identity

Alert is not a collection and performs no async work. It has no item keys,
pagination, retry protocol, or loading owner. Applications may place retry or
refresh controls in actions, but those controls own pending state and result
ordering.

Repeated Alerts are independent roots. A future Toast queue or announcer owns
message identity, deduplication, ordering, lifetime, and supersession instead
of extending generic Alert.

## 14. Server render, morph, and cleanup

Server-only output is complete and useful. It includes the effective visual
intent, variant, size, icon treatment, content, actions, and requested native
role. No-JavaScript output never dismisses itself or moves focus.

Client activation resolves the five client inputs in one component effect and
sets only changed mirrors, roles, and icon visibility. Alert's owned presence
rule keeps the off indicator and three inactive automatic icons at
`display: none` with zero geometry before and after activation. It adds no event
listener, timer, observer, global store, or DOM relocation. Repeated
initialization must not duplicate behavior. Correlated rerender gives the
initializer fresh server fallbacks; structural slot changes follow the
morphed server DOM. Removal needs no component cleanup beyond Citry's normal
reactive-effect disposal.

If a consumer removes Alert while an action owns focus, focus behavior is the
consumer's responsibility. Alert cannot infer the correct destination.

## 15. Security and content trust

Title and message slot content use ordinary Citry escaping and component
composition. Alert never treats application text as HTML. Registered icon
names resolve only through CIcon's package-owned catalog and allowlist. `actions_label`
unwraps a static Citry `Const`, verifies a string, copies it into an exact base
`str` without honoring `__html__`, normalizes newlines, rejects U+0000 and
whitespace-only values, and only then reaches the attribute renderer.

`attrs` and `actions_attrs` are explicit trusted attribute boundaries. They
are copied before validation and rendering. Root attrs reject case-insensitive
static and dynamic aliases for:

- the root part marker and every public mirror;
- `role`, `aria-live`, `aria-atomic`, and `aria-hidden`;
- `tabindex` and `contenteditable` because Alert is not a focus owner;
- `x-html`, `x-text`, `x-if`, `x-for`, and `x-teleport`, which would replace
  or relocate component-owned structure;
- `x-ignore`, which would suppress Alert or nested action initialization;
- whole-object Alpine attribute spreads that cannot be validated; and
- Citry, Citry Events, and component ownership namespaces.

Targeted unrelated Alpine bindings, events, `x-show`, native attributes, ARIA
relationships, classes, styles, and consumer data attributes remain allowed.
Actions attrs reject their part marker, structural replacement, whole-object
spreads, and runtime ownership namespaces. They also reject static and dynamic
`tabindex`, `contenteditable`, `aria-hidden`, `aria-live`, `aria-atomic`,
`role`, `aria-label`, and `aria-labelledby`. `actions_label` is the only
action-group naming path and emits `role="group"` and `aria-label` together.
These rules keep the wrapper out of Tab order, prevent an unnamed or duplicate
group, and prevent a second live region around focusable actions.

Client enums and Booleans are validated before reaching public mirrors. The
automatic and fixed icon sets use that package-owned catalog. No remote
URL, raw SVG, file metadata, or arbitrary icon name enters from client props.

## 16. Assets and performance

Alert contributes component CSS and a small client initializer for the five
reactive inputs. It has no listener, observer, timer, request, portal, or global
service. Static server output still loads that initializer because client
inputs are a supported family contract.

Automatic intent rendering uses one nonfocusable, hidden-from-assistive-
technology SVG shell with four allowlisted package glyph groups and hides
three. A fixed `icon_name` emits one group. CIcon owns one private registered-
name resolver over its generated catalog; it returns safe Markup plus audited
metadata such as whether a logical direction alias mirrors in RTL. Both CIcon
and Alert must use that resolver. Alert applies the same logical-icon RTL
transform to its fixed glyph. It does not read raw caller SVG, copy catalog
validation, duplicate CIcon's component root, or expose its selector.

A disposable five-sample render comparison on 2026-08-08 chose this
architecture over four nested CIcon roots. The decision rule was at least 25
percent less output and twice the median render speed at 100 Alerts, without a
new public API or glyph source. At 100 instances, four CIcons produced 175,044
bytes at a 76.30 ms median; one SVG shell produced 71,123 bytes at 2.17 ms,
about 59 percent less output and 35 times faster in that diagnostic. At one
instance the outputs were 2,595 and 743 bytes. These numbers select the
architecture only; they are not product timing gates.

Repository tools record raw, gzip, and Brotli component assets; diagnostic
server-render time and output bytes for 1, 10, 100, 500, and 1,000 Alerts; and
exact wheel contents. Focused browser tests prove client updates functionally;
they do not claim activation or first-update timings. These are diagnostic
evidence, not release timing gates. Alert must not add an unbounded icon
catalog, font, network fetch, or third-party browser runtime.

## 17. Acceptance matrix

Checked-in server tests cover the nested Kwargs/Slots schema; complete,
title-only, and message-only anatomy; no-content and absent-action-destination
failures; one-SVG automatic and fixed registered icons; logical-icon metadata;
icon off; every enum and Boolean validation path; invalid registered names;
plain, Const, Markup, SafeString, and hostile `__html__` action labels; root
class/style/attrs merging; reserved static, dynamic, structural, and runtime
attributes; shared CIcon glyph resolution; and the zero-listener/observer,
forced-color, print, and non-clipping asset contract.

Checked-in focused browser tests cover:

- neutral root, content role, named action group, no root Tab stop, and native
  action Tab order;
- valid client updates across every public mirror and role, invalid fallback,
  and one diagnostic per continuous invalid intent episode;
- one SVG, four automatic groups, one visible group, icon-off zero geometry,
  and fixed logical-icon mirroring in RTL; and
- ancestor variables, a public part-selector override, narrow long content,
  visible overflow, no stacking owner, forced colors, and print.

The Python-owned `alert.states` route contains every intent, variant, size,
announcement role, icon mode, actions, RTL, nested color scheme, long content,
nested Alert, and a brand adaptation. The shared browser harness proves its
initial and active states have no serious or critical axe findings and no
console errors. The public docs project discovers all ten component-owned
previews; its focused browser pass initializes every preview, exercises action
dismissal/restoration, all configurator inputs, theme overrides, and page-wide
console cleanliness. Reference-schema, component-contract, registration,
asset, scaling, and exact wheel tools include Alert.

Configured release qualification still covers exhaustive omission and invalid
client episodes for every input; assignment counting; fixed-icon stability
through client intent changes; accessibility-tree role, name, hidden-icon, and
inactive-group evidence; unknown/duplicate fills and hostile slot content;
correlated rerender with changed fallbacks and structural slots; fragment
insertion, repeated initialization, nested removal, class-order and per-intent
selector overrides, two complete brand adaptations, light/dark/nested schemes,
RTL, 200/400 percent zoom, forced colors, print, Nu HTML, and a real nested
overlay escaping Alert.

Manual release evidence covers VoiceOver, NVDA, and JAWS behavior for existing
and dynamically inserted off/polite/assertive content; browser/assistive-
technology announcement variability; keyboard navigation through actions;
visual design in both schemes and at zoom; touch; print; and real nested
overlays. Manual evidence must not turn the bounded `announce` input into a
guaranteed announcer claim.

## 18. Compatibility classification

Stable public API includes `CAlert`; all server and client input names,
meanings, defaults, validation, and fallback behavior; three slots and their
data; absence of component callbacks and methods; public variables, selectors,
reflected attributes, and announcement-role mapping; no-content and
absent-actions-destination errors; and no built-in dismissal.

Behavioral and structural contracts include the neutral root; optional icon,
title, message, and actions wrappers in documented order; role on content
rather than actions; no focus or keyboard ownership; automatic icon tracking;
native event behavior; non-clipping overlays; and complete server-only output.

Exact default colors, spacing, radius, icon glyph choices, type scale, and
private wrapping details are evolvable design. `.cui-*` classes,
`--_cui-*` variables, automatic-icon implementation markers, JavaScript
organization, and diagnostics are private.

## 19. Public documentation contract

The component-owned `api.md` begins with an observatory-themed result showing
the four intents. It then teaches the smallest Alert, title/message anatomy,
visual intent, variants, sizes, icons, actions and dismissal ownership, client
configuration, announcement urgency, customization, and accessibility. The
structured `api.yml` supplies the exhaustive reference.

Planned examples:

| Source module | Reader task | Visible content and states | Controls or interaction | Contract evidence |
|---|---|---|---|---|
| `at_a_glance.py` | recognize the family | four soft Alerts for observatory info, success, warning, and error conditions | none | intent shape/color distinction, titles, messages, auto icons |
| `basic_alert.py` | write the shortest useful Alert | one message-only info Alert and one title-plus-message Alert | none | optional anatomy and concise markup |
| `intents.py` | choose meaning | same observatory condition expressed across all intents | intent control | server and client intent plus icon tracking |
| `variants.py` | choose emphasis | soft, solid, and outline warning Alerts | variant control | every treatment and foreground contrast |
| `sizes.py` | choose density | sm, md, and lg info Alerts | size control | geometry and text scale |
| `icons.py` | choose visual indicator | automatic, hidden, and fixed star icon Alerts | icon visibility control | automatic/fixed/off behavior and decorative semantics |
| `actions.py` | add related controls | weather warning with forecast and instrument actions | native Buttons and link | action layout, group attrs, Tab order, no built-in dismissal |
| `configure.py` | derive presentation in browser | one live Alert | intent, variant, size, announce, and icon controls outside rendered result | all client inputs, fallback behavior, controls visually separate from result |
| `announcements.py` | choose urgency honestly | static, polite, and assertive examples | announcement selector | role mapping plus delivery limitation text |
| `customization.py` | adapt a brand | two observatory themes and one per-intent override | none | ancestor/root variables and public selectors |

The page uses direct, compact prose. Each example stays within the astronomy
and observatory theme. Controls render in the docs control area, remain
collapsed by default, and never look like part of the Alert result. Empty
announcements that only point at an adjacent example are omitted.

## 20. Open decisions and deferred work

No open decision blocks implementation. The single-SVG automatic-icon
architecture is selected by the bounded diagnostic in section 16. It must be
revisited only if implementation cannot keep the generated catalog as its sole
glyph source through CIcon's private safe resolver, preserve CIcon logical-alias
RTL behavior, keep inactive groups at zero geometry, and keep the SVG absent
from the accessibility tree.

Deferred work:

- a persistent announcement owner with queueing, deduplication, urgency,
  atomic update timing, browser/assistive-technology evidence, and cleanup;
- Toast or Notification queues with lifetime, pause, actions, ordering,
  focus, and cross-page ownership;
- FormSummary with linked errors, focus policy, and submission lifecycle;
- consumer-owned transition/presence patterns for Alert insertion/removal;
- a built-in dismissal surface only if real applications reveal a repeated
  focus-restoration contract that application composition cannot express; and
- alternate registered icon mappings at a library theme level after more
  component families prove the need.
