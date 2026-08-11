# Citry UI Disclosure component specification

**Status (2026-08-11): production implementation pass and independent
implementation review complete. Runtime, public documentation, focused
server/browser evidence, API projection, quality scenarios, asset/scaling
accounting, and packaging registration are checked in. Human visual review,
live assistive-technology review, and release qualification remain.**

## 1. Purpose and product bar

`CDisclosure` reveals or hides one independently owned block of supporting
content. It targets system requirements, advanced settings, explanatory help,
metadata, optional form controls, and other isolated reveal/hide jobs. The
production bar is a styled, accessible, server-rendered component with
controlled and uncontrolled browser ownership, native heading and button
semantics, effective disabledness, stable panel content, adjacent actions,
responsive styling, reliable animation, nested instances, and public
customization.

The closest accessibility baseline is the WAI-ARIA Disclosure pattern. The
component renders an authored neutral root, native heading/button trigger, and
always-mounted panel. It does not use `details`/`summary`. Native details is the
preferred raw-HTML path when no-JavaScript operation, browser-native
find-in-page behavior, or a plain uncontrolled disclosure matters more than
Citry's controlled-state, disabled, actions, focus, and animation contract.

Common jobs and their shortest supported paths:

| Job | Shortest path | Classification |
|---|---|---|
| Reveal one requirements note | `CDisclosure(slots={"title": "System requirements", "default": "Python 3.13 or newer"})` | direct API |
| Render initially expanded | `open=True` | direct API |
| Control expansion in Alpine | `$c-props="{open: shown, onOpenChange: next => shown = next}"` | client API |
| Disable the trigger without erasing state | `disabled=True` or client `disabled` | direct API |
| Add an action beside the heading | `actions` slot with optional `actions_label` | composition |
| Set the document outline | `heading_level=2` through `6` | direct API |
| Expose one deliberate region landmark | `region=True` | direct API |
| Preserve controls and edits while closed | default always-mounted panel | built-in behavior |
| Put a Disclosure inside another panel | nested `CDisclosure` in the default slot | composition |
| Adapt colors, spacing, and borders | public variables, selectors, `class_`, `style`, and attrs | CSS or native HTML |
| Provide a plain no-JavaScript disclosure | native `details` and `summary` | native HTML |
| Coordinate related expandable items | `CAccordion` and `CAccordionItem` | separate component |
| Animate an arbitrary content block | application CSS or a future motion utility | unsupported by this family |

Smallest template:

```citry-html
<c-CDisclosure>
  <c-fill name="title">System requirements</c-fill>
  <c-fill name="default">
    Python 3.13 or newer is required.
  </c-fill>
</c-CDisclosure>
```

Smallest Python composition:

```python
CDisclosure(
    slots={
        "title": "System requirements",
        "default": "Python 3.13 or newer is required.",
    },
)
```

Non-goals are grouped expansion, single or multiple selection, mandatory or
maximum-open policies, item values, item reorder/removal behavior, Arrow key
collection navigation, native `details name` grouping, horizontal collapse,
navigation, tree or stepper behavior, remote loading, URL/hash synchronization,
lazy panel mounting, arbitrary trigger elements, polymorphic tags, custom icon
content, and imperative `show()` or `hide()` methods. A headless API does not
exist. Headless work remains parked until representative applications establish
its authoring and delivery needs.

## 2. Prior art and complaints

Current evidence supports a separate standalone Disclosure rather than a
one-item Accordion. It also supports one Boolean state owner, a native button,
a configurable heading, actions outside the button, controlled and
uncontrolled expansion, always-mounted content, public state reflections, and
height animation that accepts rapid reversal.

Source record:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI inventory and Accordion | inventory reviewed 2026-08-11; Accordion production spec 2026-08-08 | [inventory](../ui_component_inventory.md), [Accordion specification](./accordion.md), runtime, server tests, browser tests, docs, and quality scenario | Disclosure owns one heading/panel Boolean; Accordion retains collection identity, coordination, and group keyboard behavior; reuse proven semantics, presence, focus, form, morph, and styling rules |
| WHATWG HTML | Living Standard reviewed 2026-08-11 | [`details` and `summary`](https://html.spec.whatwg.org/multipage/interactive-elements.html) | native `open` and `name` behavior, first-summary legend, UA activation, and queued/coalesced post-change `toggle` event |
| WAI-ARIA APG | reviewed 2026-08-11 | [Disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) | native button, Enter/Space, `aria-expanded`, and optional `aria-controls` |
| ARIA in HTML and HTML AAM | editor drafts reviewed 2026-08-11 | [ARIA in HTML](https://w3c.github.io/html-aria/), [HTML AAM](https://w3c.github.io/html-aam/) | do not override a real summary role; summary mappings vary by platform; authored button gives a stable role/state contract |
| Vuetify | 4.1.8 and `@vuetify/v0` 1.0.3 | [VExpansionPanels source](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VExpansionPanel/VExpansionPanels.tsx), [item](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VExpansionPanel/VExpansionPanel.tsx), [title](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VExpansionPanel/VExpansionPanelTitle.tsx), [text](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VExpansionPanel/VExpansionPanelText.tsx), and current v0 Collapsible inventory | primary styled-suite reference; separate group and item concerns, state, disabledness, title/text slots, icons, eager content, variants, and styling pressure |
| React Aria Components | 1.20.0 registry and current docs | [Disclosure](https://react-aria.adobe.com/Disclosure), [DisclosureGroup](https://react-aria.adobe.com/DisclosureGroup) | separate standalone and group contracts, controlled/default expansion, disabledness, adjacent actions, state reflections, and measured panel animation variables |
| React Spectrum | v3 docs reviewed 2026-08-11 | [Disclosure](https://react-spectrum.adobe.com/v3/Disclosure.html) | Disclosure, title, and panel composition; controlled/default expansion; disabledness; quiet styling; optional combination as Accordion |
| Base UI, shadcn, and Radix | Base UI 1.7.0; current shadcn/Radix docs | [Base UI Collapsible](https://base-ui.com/react/components/collapsible), [shadcn Collapsible](https://ui.shadcn.com/docs/components/collapsible), [Radix Collapsible](https://www.radix-ui.com/primitives/docs/components/collapsible) | compound root/trigger/panel precedent, controlled/default open, disabledness, state attributes, mounted-content tradeoffs, and intrinsic animation dimensions |
| Web Awesome | 3.11.0 | [Details](https://webawesome.com/docs/components/details/) | strongest styled native-details alternative; summary/content/icon slots, disabled and open properties, lifecycle events, methods, appearances, Parts, and duration/spacing variables |
| WebKit and Web Platform DX | Safari 18.4 and platform snapshot reviewed 2026-08-11 | [Safari 18.4 details styling](https://webkit.org/blog/16574/webkit-features-in-safari-18-4/), [`::details-content` status](https://web-platform-dx.github.io/web-features-explorer/features/details-content/) | native closing-animation support has improved, but its compatibility horizon and state ownership do not settle Citry's controlled/disabled contract |
| Bootstrap, Mantine, and Material UI | Bootstrap 5.3; current docs reviewed 2026-08-11 | [Bootstrap Collapse](https://getbootstrap.com/docs/5.3/components/collapse/), [Mantine Accordion](https://mantine.dev/core/accordion/), [MUI Accordion](https://mui.com/material-ui/react-accordion/) | rapid transition and mounting complaints, safe placement of adjacent actions, and mounted-by-default content |

The 2026-08-11 freshness pass compared the current Vuetify, React Aria,
Base UI, and Web Awesome releases with the recorded surfaces. Their newer
minor releases did not change the standalone Boolean, disabled, slot,
presence, or animation decisions below.

Material complaints and dispositions:

| Complaint or limitation | Status | Citry decision |
|---|---|---|
| Native `details` changes `open` before its non-cancelable `toggle` notification, and rapid changes may coalesce. | Living Standard behavior. | Do not build the controlled Citry contract on post-change reversion. The authored button requests a change before an uncontrolled commit. |
| Native `details` has no disabled state, and disabled fieldsets do not disable a `summary` activator. | Platform behavior. Web Awesome adds its own disabled layer. | Use a native `button` and let browser-effective `:disabled` remain authoritative. |
| Real `summary` accessibility mappings vary, and ARIA in HTML disallows replacing its role. | Current ARIA/HTML mapping guidance. | Use one ordinary button with stable `aria-expanded` and `aria-controls`. |
| Radix users lost collapsed descendants or expected retained form/SEO content. | [#3601](https://github.com/radix-ui/primitives/issues/3601) closed with `forceMount` guidance; [#2808](https://github.com/radix-ui/primitives/issues/2808) records the form pitfall. | Keep the complete panel mounted. Closed means hidden and inert, not unmounted. |
| Radix users treated writable `data-state` as controlled state. | [#2353](https://github.com/radix-ui/primitives/issues/2353) closed with controlled-state guidance. | Reflected `data-state` is read-only styling output. Python `open`, client `open`, and accepted activation own expansion. |
| Bootstrap transition methods ignore requests while a transition is active. | Current Bootstrap 5.3 documented behavior. | Cancel or supersede the old height animation from its current geometry. Never ignore a valid request. |
| Interactive actions cannot safely sit inside a disclosure button. | Current Mantine and APG composition constraint. | Provide a separate optional actions wrapper beside the heading. |
| Mounted panels can increase large-tree cost. | MUI and other current libraries document this tradeoff. | Prefer form, source, and state continuity for the standalone core. Measure repeated instances and defer lazy mounting until an application proves the need and accepts the semantic cost. |

Vuetify receives the primary styled-suite comparison weight. Its expansion
panel is group-oriented, so many surfaces belong only to `CAccordion`:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` and update event for one panel | direct API | Python/client `open` and `onOpenChange` | adopt a Boolean standalone contract |
| group `modelValue` item identity | separate component | `CAccordion.value` and item values | omit from Disclosure |
| `multiple`, `mandatory`, and `max` | separate component | `CAccordion` expansion policy | omit from Disclosure |
| group `disabled` | separate/direct API | Accordion group disabled; Disclosure `disabled` for its sole trigger | adopt only the standalone meaning |
| item `value` | separate component | Accordion item identity | omit because Disclosure has no collection identity |
| selected class/state classes | public reflections | root, trigger, and panel `data-state` | adopt read-only state output, not a class input |
| item disabled | direct API | server/client `disabled` | adopt |
| default/accordion/inset/popout variants | direct API or CSS | `outline`, `soft`, `plain`; utilities for layout | simplify to standalone visual jobs |
| `flat`, `gap`, `noDivider`, `tile`, rounded, and elevation | CSS or separate component | public border/radius variables and utilities; group geometry stays Accordion | capability without prop parity |
| theme, background, and color | theme/CSS | color-scheme defaults and public variables | adopt |
| hover input | CSS | hover selector and trigger hover variable | omit a presentation Boolean |
| root `tag` | native HTML | fixed neutral `div` and `class_`/`style`/`attrs` | reject polymorphism to protect anatomy |
| title and text props/slots | slots | required `title` and default slots | adopt slots instead of duplicate string props |
| title actions/default scoped content | composition | separate `actions` slot and optional accessible label | adopt safer anatomy; slot data is a server snapshot |
| expand/collapse icons and hide-actions | direct API | fixed chevron, `indicator`, and `indicator_pos` | adopt common jobs; reject arbitrary icon replacement initially |
| `eager` | built-in behavior | every panel stays mounted | always eager |
| readonly, focusable, static, and ripple | controlled state, native HTML, or CSS | controlled refusal, native focus, no ripple | omit ambiguous or presentation-specific inputs |
| title click event | native event/client callback | Alpine `@click` for native observation; `onOpenChange` for state requests | do not duplicate native click as a custom event |
| group default slot `prev`/`next` and public methods | separate component | Accordion keyboard/state API | no imperative Disclosure API |

Citry adopts the semantic button/panel pattern, Boolean controlled state,
disabledness, adjacent actions, public reflections, always-mounted content,
and bounded animation hooks. It rejects native-details ownership for this
component, collection APIs, arbitrary part replacement, lazy presence, and
imperative methods. The implementation must prove disabled-fieldset
reconciliation, controlled morph handoff, focus before close, rapid reversal,
and nested-root isolation.

## 3. Public composition and anatomy

The public family has one rendered component:

```text
CDisclosure (div)
├─ header row (div)
│  ├─ heading (h2...h6)
│  │  └─ trigger (button)
│  │     ├─ indicator (optional span at logical start)
│  │     │  └─ decorative svg
│  │     ├─ title (span)
│  │     └─ indicator (optional span at logical end)
│  │        └─ decorative svg
│  └─ actions (optional div, outside heading/button)
└─ panel (div, optional region role)
   └─ body (div)
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CDisclosure` | neutral `div` | `class_`, `style`, and `attrs` land on the root; heading, trigger, panel, and optional actions maps have exact destinations | one heading owns one button; the button controls one stable panel; optional region semantics label that panel |

The `title` and default fills are required exactly once. The `actions` fill is
optional and may occur at most once. Missing, duplicate, or unknown fills use
normal Citry slot validation errors. `actions_label` and nonempty
`actions_attrs` require the actions slot. The label must contain
non-whitespace text and no U+0000.

Title content renders inside the button and therefore accepts phrasing,
noninteractive content only. Links, form controls, nested headings, and nested
Disclosure or Accordion roots belong in the panel. The actions slot is for
related Buttons, links, and menus, not another Disclosure or Accordion.
Panel content accepts normal flow content and nested components except native
`dialog`, `CDialog`, and `CDrawer`. A control in the panel or actions may open
one of those modal surfaces rendered as a sibling outside the Disclosure.
Accepted title/actions/panel output is standard HTML plus server-resolved
Citry components. Unresolved custom-element tags, customized built-ins using
`is`, and authored descendants that host an open ShadowRoot are rejected in
actions and panel content. Disclosure itself may be mounted inside an open
ShadowRoot; the restriction applies only to opaque authored descendants
within its slots.

A private transparent title boundary validates the completed server-rendered
title before output. Outside SVG it accepts text plus `abbr`, `b`, `bdi`,
`bdo`, `br`, `cite`, `code`, `data`, `del`, `dfn`, `em`, `i`, `img`, `ins`,
`kbd`, `mark`, `picture`, `q`, `rp`, `rt`, `ruby`, `s`, `samp`, `small`,
`source`, `span`, `strong`, `sub`, `sup`, `svg`, `time`, `u`, `var`, and
`wbr`. Inside decorative SVG it accepts only `svg`, `g`, `path`, `polyline`,
`line`, `circle`, `rect`, `ellipse`, and `polygon`. Images require an empty
`alt`; SVG requires `aria-hidden="true"` and `focusable="false"`.

Every title descendant rejects `role`, `tabindex`, `contenteditable`,
`autofocus`, `href`, `xlink:href`, `controls`, `usemap`, `form`, `popover`,
`is`, `hidden`, `inert`, ARIA naming/description attributes, `on*`, `@*`, `x-on:*`,
and structural or ownership Alpine directives. The two decorative SVG
attributes above are the only ARIA/focus exceptions. All other elements, including anchors, labels,
Buttons, form controls, media, `details`/`summary`, headings, flow-only HTML,
`foreignObject`, script/style/animation elements, and unresolved custom
elements are rejected. Dynamic binding aliases targeting any rejected
attribute are rejected before render.

Client initialization verifies the browser-settled trigger/title anatomy and
the same element, semantic, and attribute rules. After HTML ASCII whitespace
normalization, the title must contain nonempty textual content outside
decorative SVG and every `aria-hidden` subtree. Decorative-only images or SVG,
SVG `<text>`, empty output, and whitespace-only output fail because
`trigger_attrs` cannot replace the title with `aria-label` or
`aria-labelledby`. This is a structural textual-title rule, not a browser
accessible-name computation. Consumers must not use their own classes, styles,
or CSS to remove all title text from rendering or the accessibility tree.
Focused examples prove the final button name with axe and an accessibility
snapshot; the runtime does not reproduce the platform name algorithm.
A bounded title-subtree observer rechecks child additions and changes to all
descendant attributes without an `attributeFilter`, then classifies them
through the rules above. It observes character data as well as child changes
so event/directive additions and removal of the visible name are both
detected. One bounded content-structure observer watches subtree child-list
changes in the panel for forbidden modal-dialog or raw-popover roots and
watches the actions subtree for nested Disclosure/Accordion roots or the same
forbidden native surfaces. The private server panel and actions boundaries
reject the same rendered elements before output. The actions boundary
identifies family roots by their exact public root part, so it does not require
changes to Accordion's implementation. A native `dialog` is rejected
regardless of its current `open` or `:modal` state. The content observer also
watches `popover`, `data-citry-ui-part`, and `is` so post-initialization
attribute mutations cannot forge an allowed subtree.

The content validator also rejects unresolved custom elements, customized
built-ins, and every detectable descendant with a non-null `shadowRoot`.
Imperative attachment of a closed ShadowRoot to an ordinary standard element
cannot be detected by the platform and is outside the slot contract, as is
reparenting already-open top-layer content. Server-rendered Citry components
resolve to their documented native anatomy before this boundary validates
them, so they are not unresolved custom elements.

An element with native `popover` is accepted only when `popover="manual"` and
its exact `data-citry-ui-part` is `popover`, `tooltip`, `menu`, `popup`, or
`hover-card`, the current coordinator-participating Citry anchored surfaces.
Raw native popovers, `auto`/`hint` popovers, and an unknown future surface are
rejected until the family is deliberately requalified. This structural
allowlist is a trusted-component marker, not a tenant-input security boundary.

Structural validation has a private `valid` or `invalid` state. Initial
invalid output installs the validation observers, a passive prop recorder, and
one capture-phase `beforetoggle` safety listener on the root. It does not
install activation, begin animation, apply client props to the DOM, or publish
the ready marker. Server HTML remains at its
declared committed open/closed state. The recorder retains the latest raw
owner inputs without validation diagnostics or state effects while structure
is invalid. The observers make repair detectable without requiring an
unrelated re-render. A valid repair validates those latest inputs and performs
ordinary initialization without a callback.

When a valid initialized root becomes invalid, the component cancels and
settles any current animation to the already committed logical state, removes
its activation listener, records later owner inputs without applying them,
and reports once per continuous invalid episode. Exact suspended presence is:

- invalidation during or after a committed open cancels animation, removes
  transient block-size/overflow, and leaves the panel open without `hidden`,
  `inert`, or `aria-hidden`;
- invalidation during or after a committed close cancels animation, removes
  transient styles, and completes closed presence with `hidden`, `inert`, and
  `aria-hidden` already established by that earlier commit; and
- invalidity found by synchronous preflight before a requested commit rejects
  that commit, so an open panel stays open and a closed panel stays closed.

Validation never changes the logical state, starts a new presence transition,
or moves focus by itself. A valid repair ends the episode, rebuilds disabled
ancestry, reconciles the latest recorded owner state once without a callback,
restores activation, and publishes readiness. Cleanup disconnects
validation-only and fully initialized roots equally. This rule prevents a
newly inserted modal Dialog from being hidden by a new close commit; the
invalid subtree must be removed or rendered outside Disclosure before that
recorded close can apply.

Mutation observers provide proactive diagnostics and repair detection, but
they are not the safety gate. Every trigger activation and every owner/server
path that would apply an open or closed state synchronously revalidates title,
actions, and panel structure first. A same-task title mutation cannot activate
the trigger, and a same-task `dialog` insertion plus `open=False` update cannot
make that dialog's ancestor inert or hidden before the component enters its
invalid suspended state.

The root's capture-phase `beforetoggle` listener also rejects an opening event
whose target is a descendant native `dialog` or a descendant popover that does
not match the exact Citry surface allowlist. It calls `preventDefault()` before
`showModal()` or `showPopover()` can commit and enters the same
structural-invalid episode.
This guard stays installed in validation-only and normal initialized states,
including while a panel close animation is running. It does not affect a
Dialog rendered as a sibling outside the Disclosure and never intercepts a
Dialog close. Reparenting a Dialog that is already `:modal` into a Disclosure
subtree through arbitrary script is outside the component lifecycle contract;
the observer diagnoses and suspends Disclosure, but the application that
moved the live modal must move or close it. Citry server rendering and
correlated morphs never perform that unsupported transition.

`beforetoggle` is not composed across descendant ShadowRoot boundaries. The
slot contract above therefore rejects detectable authored shadow hosts rather
than claiming cross-boundary interception. A Disclosure root placed inside an
open ShadowRoot still works because its own listener and light-DOM slot output
share that root. A closed or imperatively attached opaque descendant shadow
tree capable of opening top-layer content is unsupported and must remain
outside Disclosure.

A nested `CDisclosure` or `CAccordion` is valid only inside the default panel
slot. The transparent title and actions boundaries validate their completed
rendered output, and the client repeats that settled-DOM validation. Nesting
either family in the title or actions area raises before server output or
suspends an already initialized invalid root until repair. Adjacent Disclosure
roots have no relationship and never coordinate.

The root ID is the validated explicit `id` or
`cui-disclosure-{component-id}`. An explicit ID must be nonempty, contain no
ASCII whitespace, and contain no U+0000. The trigger ID is
`{root-id}-trigger` and the panel ID is `{root-id}-panel`. Generated IDs are
instance-unique. Callers remain responsible for uniqueness of explicit IDs.

Stable anatomy is the root, header row, heading containing only the button,
actions beside that heading, and panel/body relationship shown above. The
indicator's private SVG and implementation-only wrappers may change. A
separate public Trigger, Panel, Header, or Item component would add ceremony
without adding composition because every Disclosure owns exactly one of each.

## 4. Server inputs and client inputs

`CDisclosure.Kwargs`:

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `open` | `bool` | `False` | initial value and server fallback | chooses initial committed visibility; a changed value on a later server morph is an intentional uncontrolled reset |
| `disabled` | `bool` | `False` | reactive configuration | disables the native trigger without changing open state; enclosing CForm/native fieldset disabledness remains dominant |
| `variant` | `Literal["outline", "soft", "plain"]` | `"outline"` | reactive presentation | selects one supported standalone treatment |
| `size` | `Literal["sm", "md", "lg"]` | `"md"` | reactive presentation | selects type, trigger, panel, and indicator geometry |
| `indicator` | `bool` | `True` | reactive presentation | shows the owned decorative chevron |
| `indicator_pos` | `Literal["start", "end"]` | `"end"` | reactive presentation | places the chevron at logical start or end |
| `heading_level` | `Literal[2, 3, 4, 5, 6]` | `3` | structural server-only | chooses the native heading tag |
| `region` | `bool` | `False` | structural server-only | adds a named region to this panel; use deliberately |
| `actions_label` | `str | None` | `None` | structural server-only | names an actions group when supplied; requires the actions slot |
| `id` | `str | None` | `None` | structural server-only | supplies the root and trigger/panel ID prefix |
| `class_` | `CClassValue | None` | `None` | server presentation | merges root classes with `attrs` |
| `style` | `CStyleValue | None` | `None` | server presentation | merges root inline styles with `attrs` |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted root attributes | copied, validated, and bound to the root |
| `heading_attrs` | `Mapping[str, object] | None` | `None` | trusted heading attributes | copied, validated, and bound to the native heading |
| `trigger_attrs` | `Mapping[str, object] | None` | `None` | trusted trigger attributes | copied, validated, and bound to the button |
| `panel_attrs` | `Mapping[str, object] | None` | `None` | trusted panel attributes | copied, validated, and bound to the controlled panel |
| `actions_attrs` | `Mapping[str, object] | None` | `None` | trusted actions attributes | copied, validated, and bound only when the actions slot exists |

Public type aliases are exact:

```python
CDisclosureVariant = Literal["outline", "soft", "plain"]
CDisclosureSize = Literal["sm", "md", "lg"]
CDisclosureIndicatorPos = Literal["start", "end"]
CDisclosureHeadingLevel = Literal[2, 3, 4, 5, 6]
```

The family module and package root export exactly `CDisclosure`, those four
aliases, `CDisclosureTitleSlotData`, `CDisclosureDefaultSlotData`,
`CDisclosureActionsSlotData`, and `CDisclosureOpenChangeDetail`. `Kwargs`
remains the public nested schema on `CDisclosure`, not a second top-level
export. Private parser boundaries, validation records, and client-state types
are not exported.

Client inputs use `$c-props`:

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `open` | Boolean | releases control and preserves the current committed baseline | same as omission | one diagnostic per episode; release control from the committed baseline | trigger ARIA, panel presence, reflections, and animation |
| `onOpenChange` | function | no callback | no callback | one diagnostic per episode; ignore callback | activation requests |
| `disabled` | Boolean | Python fallback | invalid | Python fallback with one diagnostic | native button and disabled reflections; ancestor fieldset remains dominant |
| `variant` | `outline`, `soft`, or `plain` | Python fallback | invalid | Python fallback with one diagnostic | root reflection and CSS |
| `size` | `sm`, `md`, or `lg` | Python fallback | invalid | Python fallback with one diagnostic | root reflection and CSS |
| `indicator` | Boolean | Python fallback | invalid | Python fallback with one diagnostic | indicator visibility |
| `indicatorPosition` | `start` or `end` | Python fallback | invalid | Python fallback with one diagnostic | indicator order and root reflection |

Heading level, region semantics, ID, slots, attribute destinations, and actions
labeling remain structural server data. Public reflected attributes are
read-only outputs and never inputs.

On first activation, Python `open` supplies the committed baseline. A valid
client `open` then controls the rendered state. A same-root server morph with
an unchanged server-open fingerprint preserves browser-owned state. A changed
Python `open` replaces the uncontrolled baseline. Valid client control remains
visually authoritative across that replacement, while the changed server value
becomes the next release baseline. Omitting or nulling client `open` releases
control without resetting that baseline.

Every client effect and DOM query is scoped to the nearest Disclosure root.
Nested instances cannot read, style, toggle, animate, or clean up an ancestor's
panel.

## 5. State model

The component has one public logical state, `open` or `closed`, plus effective
disabledness, controlled/uncontrolled ownership, and private structural
validity. `opening` and `closing` are private visual phases. Public ARIA and
`data-state` reflect the committed logical state, never an intermediate
animation frame.

| Trigger | Guard | Requested state | Uncontrolled result | Controlled result |
|---|---|---|---|---|
| first render | valid Python inputs | Python `open` | commit without callback or animation | same until a valid client owner appears |
| enabled trigger activation while closed | button is not browser-disabled | `open=True` | callback, commit, then animate open | callback only |
| enabled trigger activation while open | button is not browser-disabled | `open=False` | callback, recover panel focus, commit, then animate closed | callback only |
| disabled trigger activation | native/effective disabled | none | no-op | no-op |
| valid client `open` update | Boolean | exact supplied state | not applicable | commit exact state without callback |
| repeated current client value | valid and unchanged | current state | not applicable | no callback and no new animation |
| client `open` omission or `null` | prior control episode | current baseline | browser becomes owner | release without callback |
| invalid client `open` | any non-Boolean, non-null value | current baseline | one diagnostic and browser ownership | release invalid control without callback |
| changed Python `open` on same root | server fingerprint changed | new server baseline | apply as reset without callback | retain valid client-visible state; store new release baseline |
| effective disabledness changes | any logical state | no open change | update button and mirrors | same |
| accepted request during animation | enabled | opposite logical state | cancel and supersede from current geometry | callback only until owner accepts |
| root removal | any state | none | cancel and clean up | cancel and clean up |

`onOpenChange` receives every accepted activation request before an
uncontrolled commit. If a controlled owner supplies the requested value later,
that prop update commits without another callback. Callback return values do
not cancel. A disabled request, repeated owner value, initialization, morph,
release, or cleanup never calls it.

When closing commits, `aria-expanded` and `data-state` become closed
immediately. If focus is inside the panel and the trigger remains focusable,
focus moves to the trigger before the panel becomes inert. `aria-hidden` and
`inert` then apply while the visible box animates. `hidden` applies only after
the closing animation finishes. Opening removes `hidden`, `inert`, and
`aria-hidden` before measurement and exposes open semantics immediately.

If an owner closes while the trigger is disabled, disconnected, or not
rendered, the component must not leave focus in the panel it makes inert. It
first attempts the ordinary trigger focus path when eligible and verifies the
deep active element after that attempt. If focus is still in the panel, it
moves focus to the nearest containing modal Dialog, resolved through composed
ancestors, or to `ownerDocument.body` when no such Dialog exists. It may add
`tabindex="-1"` to that fallback only for the focus operation and then restores
the prior attribute. A callback or owner update that already moved focus
outside the panel wins and is not overridden. This also covers a close in the
same update that hides the complete root through its allowed `hidden` or
`x-show` presence surface.

Invalid client episodes report once even if the invalid value changes. A
valid value or omission ends the episode. The family has no read-only,
loading, pending, empty, or error state. Applications compose those meanings
inside title, actions, or panel content.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CDisclosure` | `title` | yes | exactly one fill | `CDisclosureTitleSlotData`, empty server snapshot | none |
| `CDisclosure` | `default` | yes | exactly one fill | `CDisclosureDefaultSlotData`, empty server snapshot | none |
| `CDisclosure` | `actions` | no | zero or one fill | `CDisclosureActionsSlotData`, empty server snapshot | omit actions wrapper |

Slot data never changes in the browser. Client state is available through
public DOM reflections and `$c-props`, not reactive render-prop data.

The title slot accepts noninteractive phrasing content. The actions slot
accepts related interactive controls and remains outside the heading/button.
The default slot accepts standard flow content, native form controls,
server-resolved Citry components including coordinator-participating anchored
layers, and nested Disclosure or Accordion roots. It does not accept an
unresolved custom element, authored shadow host, raw native popover, or modal
Dialog root. The actions slot has the same shadow/overlay limits and does not
accept nested Disclosure or Accordion roots.

No collection renderer or dynamic slot namespace exists. Unknown, missing, or
duplicate fill names fail through normal Citry slot validation. A nested
`CDisclosure` or `CAccordion` in the title or actions context raises a
composition error.

## 7. Callbacks, native events, and methods

Public callback detail:

```python
class CDisclosureOpenChangeDetail(TypedDict):
    open: bool
    previousOpen: bool
    source: Literal["activation"]
    controlled: bool
```

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onOpenChange` | `(next_open: bool, detail: CDisclosureOpenChangeDetail)` | enabled native-button activation | after validation and before an uncontrolled commit | reports the request; owner must update client `open` to accept it | return value ignored |

`detail.open` equals the first argument. `detail.previousOpen` is the logical
state before the request. `detail.source` is always `"activation"` in this
version. `detail.controlled` records whether a valid client `open` owned state
when the request occurred.

Alpine `@click`, `@focus`, and other listeners remain the surface for native
events. The component dispatches no custom `toggle`, `show`, `hide`, or
animation lifecycle event. It exposes no public method. Client `open`,
`onOpenChange`, the trigger ref, and native `focus()` are sufficient.

## 8. Semantics, keyboard, focus, and assistive technology

The root and header row are neutral `div` elements. `heading_level` renders
`h2` through `h6`. That heading contains only one `button type="button"`.
Visible title content gives the button its accessible name. The button owns
`aria-expanded="true|false"` and `aria-controls` pointing to the stable panel
ID.

The panel has no role by default. When `region=True`, it owns
`role="region"` and `aria-labelledby` pointing to the trigger. This is opt-in
to avoid landmark proliferation. The closed panel owns `aria-hidden="true"`,
`inert`, and `hidden` when settled. Those states are removed when open.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| enabled trigger | pointer or touch activation | request opposite `open` | remains on trigger | no; native click |
| enabled trigger | Enter | native click requests opposite `open` | remains on trigger | no extra handler |
| enabled trigger | Space | native click requests opposite `open` | remains on trigger | no extra handler |
| trigger | Arrow keys, Home, or End | no Disclosure behavior | unchanged | no |
| anywhere | Tab or Shift+Tab | normal document order | enabled trigger and open-panel controls participate | no |
| open panel containing focus | accepted close | focus controlling trigger before inert/hidden state | trigger when focusable | no |
| open panel containing focus while trigger becomes unavailable | accepted close | verify trigger focus, then focus a safe owner outside the panel before inert/hidden state | trigger when focus succeeds; otherwise nearest containing modal Dialog or document body | no |
| trigger becomes browser-disabled | native disabled behavior | user activation blocked | Tab skips trigger | no |
| nested Disclosure trigger | activation | only nearest root requests state | nested trigger | no extra handler |

The root never receives `tabindex`. Native disabled buttons are omitted from
Tab order and require no redundant `aria-disabled`. Effective disabledness
comes from the component configuration, CForm context, and the browser's
`:disabled` result. The latter preserves native fieldset and first-legend
rules.

Actions follow the trigger in DOM order and remain separate focus stops. With
`actions_label`, their wrapper is one named `group`. Without it, the wrapper
is neutral. The decorative indicator is `aria-hidden` and its SVG is
nonfocusable.

Required assistive-technology outcome is one button announced with its
expanded/collapsed and disabled state, followed in ordinary reading order by
available panel content. Region mode additionally announces one named region.
No screen reader should encounter a second synthetic button role, hidden panel
focus target, or group keyboard behavior.

## 9. Native forms and validation

Disclosure is not a form participant. It submits no name or value and has no
required, read-only, validity, autocomplete, or form-owner API. Its trigger is
always `type="button"` and never submits a form.

Consumer controls inside the panel keep native form ownership, names, values,
autocomplete, reset behavior, validation, and submission. The panel is never
unmounted, so closing does not erase an uncontrolled edit, remove an enabled
successful control from `FormData`, or reset a nested client component.
`form.reset()` resets descendants normally but does not reset Disclosure
`open`.

An enclosing disabled native `fieldset`, including CForm's fieldset, disables
the trigger. Server output consumes CForm's disabled fallback when available.
Client behavior checks `button.matches(":disabled")`, so an ordinary fieldset
and its first-legend exception remain browser-authoritative. Dynamic
`disabled` changes and legend insertion, removal, or reorder must update public
disabled reflections without changing `open`.

`hidden` and `inert` do not disable panel controls or exempt them from
constraint validation. A required invalid control in a closed panel can block
submission while being unavailable for focus. Disclosure does not guess
whether validation or collapse should win. Applications must keep required
content open, control `open` from validation state, or handle captured
`invalid` events to open the owning Disclosure before moving focus.

Citry Events rerenders preserve browser-owned panel controls under their normal
morph keys. Disclosure adds no form serialization, server action, validation
message, transport retry, or error protocol.

## 10. Styling and theme contract

Variants:

- `outline`: one bordered standalone surface;
- `soft`: one quiet filled surface; and
- `plain`: transparent surface without invented group dividers.

Sizes `sm`, `md`, and `lg` change title scale, trigger/panel padding, and
indicator geometry. `indicator_pos` uses logical start/end and follows RTL.
There is no standalone `separated` variant because separation is a relationship
among Accordion items.

Public variables:

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-disclosure-background` | color | root surface | scheme-derived `Canvas` |
| `--cui-disclosure-foreground` | color | title and panel foreground | `CanvasText` |
| `--cui-disclosure-border-color` | color | outline border | scheme-derived current-color mix |
| `--cui-disclosure-border-width` | length | stable border geometry | `1px` |
| `--cui-disclosure-radius` | length | root corner radius | `0.75rem` |
| `--cui-disclosure-trigger-background` | color | resting trigger surface | transparent |
| `--cui-disclosure-trigger-hover-background` | color | enabled hover surface | current-color mix |
| `--cui-disclosure-trigger-open-background` | color | expanded trigger surface | accent mix |
| `--cui-disclosure-trigger-open-color` | color | expanded title and indicator | scheme blue |
| `--cui-disclosure-focus-color` | color | trigger focus ring | `Highlight` |
| `--cui-disclosure-indicator-color` | color | chevron foreground | `currentColor` |
| `--cui-disclosure-trigger-padding-inline` | length | horizontal trigger inset | size-derived |
| `--cui-disclosure-trigger-padding-block` | length | vertical trigger inset | size-derived |
| `--cui-disclosure-panel-padding-inline` | length | horizontal body inset | size-derived |
| `--cui-disclosure-panel-padding-block` | length | vertical body inset | size-derived |
| `--cui-disclosure-actions-gap` | length | adjacent action spacing | `0.5rem` |
| `--cui-disclosure-duration` | time | panel and indicator transition | `180ms` |
| `--cui-disclosure-easing` | easing | panel and indicator transition | `ease-out` |

Public selectors:

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="disclosure"]` | root surface | always | owns one header and one panel |
| `[data-citry-ui-part="disclosure-header"]` | heading/action row | always | direct root child |
| `[data-citry-ui-part="disclosure-heading"]` | native heading | always | contains only trigger |
| `[data-citry-ui-part="disclosure-trigger"]` | native button | always | heading's only child; controls panel |
| `[data-citry-ui-part="disclosure-title"]` | title wrapper | always | trigger child |
| `[data-citry-ui-part="disclosure-indicator"]` | decorative indicator `span` | always, optionally hidden | trigger child; owns one private SVG |
| `[data-citry-ui-part="disclosure-actions"]` | adjacent actions | when filled | header child outside heading |
| `[data-citry-ui-part="disclosure-panel"]` | controlled panel | always | direct root child |
| `[data-citry-ui-part="disclosure-body"]` | panel content inset | always | direct panel child |

Public reflected attributes:

| Public reflected attribute | Values | Meaning |
|---|---|---|
| root `data-variant` | `outline`, `soft`, `plain` | effective treatment |
| root `data-size` | `sm`, `md`, `lg` | effective size |
| root `data-state` | `open`, `closed` | committed expansion |
| root `data-disabled` | present/absent | browser-effective trigger disabledness |
| root `data-indicator` | present/absent | indicator is visible |
| root `data-indicator-pos` | `start`, `end` | effective logical placement |
| trigger `data-state` | `open`, `closed` | committed expansion |
| trigger `data-disabled` | present/absent | browser-effective disabledness |
| panel `data-state` | `open`, `closed` | committed expansion |

Every public reflection is read-only styling and inspection output. Defaults
live in the `citry-ui.theme` layer with zero-specificity `:where()` selectors.
Public variables resolve through private effective variables so ancestor and
root overrides work. Consumer unlayered CSS and inline style remain able to
override defaults.

Structural CSS uses logical properties and direct-child relationships so an
outer Disclosure does not restyle a nested root. Public variables inherit by
design and may be reset on a nested root. Settled panels do not retain
`overflow`, fixed block size, transform, containment, or stacking styles.

## 11. Environmental behavior

Default tokens support light and dark color schemes and nested scheme scopes.
Long titles, URLs, body text, and action labels wrap without horizontal page
overflow. The header lets title and actions shrink or wrap independently.
Logical properties support RTL and place start/end indicators without changing
semantic order.

At narrow widths and 200 or 400 percent zoom, title, actions, and open panel
content remain reachable. Text-spacing overrides do not clip the title or
body. Pointer and coarse-touch activation use the native button target.
Disclosure neither opens a virtual keyboard nor changes viewport scrolling.

Panel animation reads the public duration/easing variables, cancels stale
animations, and clears transient block size and overflow after completion.
`prefers-reduced-motion: reduce` and zero duration commit immediately. Closed
panels use a component-owned `[hidden] { display: none !important; }` rule so
other component display styles cannot defeat native hidden behavior.

Forced colors uses system foreground, border, focus, and indicator colors.
Open state is not color-only because `aria-expanded`, panel presence, and
indicator rotation remain. Print disables animation and prints every panel
expanded so supporting content is not lost. The printed heading remains
identifiable without relying on an interactive affordance.

There are no library-authored visible strings. Title, panel, action content,
and `actions_label` belong to the application. Diagnostic text is developer
output, not localized UI. Locale selection and translation remain separate
work.

## 12. Overlay and layering behavior

Disclosure never creates or controls an overlay. The header and settled panel
do not create a z-index, transform, isolation, containment, scroll lock, or
focus scope. Temporary clipping is confined to the panel while block size
animates.

Anchored nonmodal Citry layers such as Menu, Select and MultiSelect popups,
Popover, Tooltip, and HoverCard may be composed in actions or an open panel.
They keep their own positioning, dismissal, Escape, and outside-interaction
contracts. Before closing makes the panel inert, Disclosure resolves panel
focus according to section 5. The shared anchored-layer coordinator then
observes the new inert/hidden ancestry and force-closes every descendant layer
with its structural ancestor reason. That safety close cannot be rejected by
a controlled layer owner, and it must preserve focus that Disclosure already
moved outside the panel.

Raw native popovers are not accepted descendants. Unlike coordinator
participants, a native manual popover remains `:popover-open` when an ancestor
panel becomes inert and hidden, then can resurface stale when the panel opens.
The server/settled validator rejects raw `popover`, and the synchronous
`beforetoggle` guard prevents the same observer-delivery race described for
Dialog. A consumer needing a native popover renders it as a sibling or closes
it before closing Disclosure; the supported shortest path is `CPopover`.

All descendant guarantees in this section cover standard light-DOM output
within Disclosure. The Disclosure root itself may be inside an open ShadowRoot
and retains the same behavior. A nested unresolved web component or authored
ShadowRoot is not accepted slot content because native top-layer events are
not composed across that boundary. Applications keep such an opaque component
outside Disclosure and control it from the panel or actions.

Native `dialog`, `CDialog`, and `CDrawer` roots are not
valid panel or actions descendants. A modal top-layer element can remain
`:modal` after its physical ancestor becomes inert and hidden, leaving an
invisible focus-blocking surface. Applications render the modal as a sibling
outside Disclosure and let a panel/action control own its open state. Server
composition rejects known Citry modal roots, settled validation rejects any
native `dialog`, and dynamic insertion suspends Disclosure at its last
committed state until the forbidden subtree is removed. A capture-phase
`beforetoggle` guard prevents a newly inserted descendant Dialog from entering
its open state before observer delivery. Disclosure never calls `close()` on
a consumer Dialog and never hides a modal descendant. Arbitrary script that
reparents an already-open modal is explicitly unsupported as described in
section 3.

## 13. Collections, async data, and identity

Disclosure is not a collection. It has no item key, selected value, ordering,
empty state, add/remove/reorder policy, dynamic slot, pagination,
virtualization, or grouped disabled-item behavior. Adjacent instances are
independent. Jobs requiring coordinated identities use `CAccordion`.

Its only identity is the stable root/trigger/panel ID trio. Browser state is a
Boolean and never derives from DOM position, title text, or an application
value. It does not expose native `details name` grouping.

Disclosure starts no async work. Remote content, loading, cancellation,
supersession, stale responses, errors, retries, and offline behavior belong to
components placed inside the panel. Closing does not cancel that work because
the panel remains mounted.

## 14. Server render, morph, and cleanup

Server output is complete and useful before activation. An initially open
Disclosure exposes its full heading and panel content. An initially closed
Disclosure exposes the heading button and retains the hidden panel in source,
but the button cannot toggle without JavaScript. Applications requiring a
working no-JavaScript toggle use native `details`.

The initializer attaches once per current root and tolerates repeated
`$component.init()` calls. It owns one logical-state handoff record on that
root. A same-root morph compares the new Python-open fingerprint with the
prior fingerprint:

- unchanged server input preserves the latest uncontrolled committed state;
- changed server input replaces the uncontrolled baseline;
- valid client `open` remains authoritative;
- client omission, `null`, or invalid release uses the current baseline; and
- no owner/morph reconciliation emits `onOpenChange`.

Opening removes `hidden`, `inert`, and `aria-hidden` before measuring the body.
Closing moves panel focus to an eligible rendered trigger. When trigger focus
fails because it is disabled, disconnected, or hidden with the complete root,
the component uses the containing-modal or document-body fallback. It then
applies inaccessible closed state, animates from current geometry, and adds
`hidden` after completion. It preserves focus that an owner already moved
outside the panel.
Rapid reversals cancel the prior Web Animation and start from computed current
height. Settled cleanup removes temporary height, overflow, and animation
styles.

Panel descendants remain under their normal Citry morph keys, so browser-owned
form values, selection, editing state, and nested component handoff use
ordinary platform/runtime behavior. Disclosure does not reconstruct panel
content to toggle it.

Runtime ownership checks use the nearest Disclosure root. Cleanup stops the
client effect, removes activation and `beforetoggle` listeners, disconnects
the fieldset, title-subtree, and content-structure observers, cancels
animation, clears temporary styles, and deletes private
initialization markers or leaves a valid root-local handoff record only for
the next morph. Removing the complete component does not move focus to an
unknown external element.

Each initialization rebuilds the exact set of ancestor fieldsets it observes,
including direct-child changes that can change the first-legend exception. A
correlated move into or out of a fieldset, or between a fieldset and its first
legend, must run cleanup and initialization again before the new root is marked
ready. Arbitrary script reparenting without Citry lifecycle activation is not a
supported state-transfer path; native `:disabled` behavior still applies, and
the public mirror is reconciled on the next component activation.

## 15. Security and content trust

Title, panel, and actions slot content use normal Citry escaping and component
rendering. The family has no raw-HTML, remote-HTML, URL, file, or raw-SVG input.
The indicator resolves one allowlisted registered CIcon glyph and renders a
nonfocusable decorative SVG.

`class_`, `style`, and attribute maps are trusted author inputs, not a
sanitizer for tenant-controlled data. Every mapping is copied before
validation. Generated IDs use a component-owned prefix. Explicit IDs reject
empty values, ASCII whitespace, and U+0000.

Every attribute destination rejects `data-citry-*`, `data-cev*`, and
`data-cid*` runtime namespaces. It also rejects whole-element or structural
ownership directives including `x-bind`, `x-for`, `x-html`, `x-if`,
`x-ignore`, `x-model`, `x-modelable`, `x-teleport`, and `x-text`. Dynamic
aliases such as `:aria-expanded`, `.disabled`, and
`x-bind:aria-controls` are checked by their target names.

Owned destination rules:

| Destination | Rejected ownership |
|---|---|
| root `attrs` | `id`, `is`, `role`, `tabindex`, `contenteditable`, `inert`, `popover`, `aria-hidden`, `aria-label`, `aria-labelledby`, `aria-description`, `aria-describedby`, `aria-details`, `aria-roledescription`, `aria-live`, `aria-atomic`, `data-citry-ui-part`, `data-citry-disclosure-root`, `data-citry-disclosure-initialized`, `data-variant`, `data-size`, `data-state`, `data-disabled`, `data-indicator`, and `data-indicator-pos` |
| `heading_attrs` | `is`, `role`, `aria-level`, `tabindex`, `contenteditable`, `hidden`, `inert`, `popover`, `x-show`, `aria-hidden`, `aria-label`, `aria-labelledby`, `aria-description`, `aria-describedby`, `aria-details`, `aria-roledescription`, and `data-citry-ui-part` |
| `trigger_attrs` | `id`, `is`, `type`, `disabled`, `role`, `tabindex`, `hidden`, `inert`, `popover`, `x-show`, `command`, `commandfor`, `popovertarget`, `popovertargetaction`, `aria-controls`, `aria-disabled`, `aria-expanded`, `aria-hidden`, `aria-label`, `aria-labelledby`, `aria-roledescription`, `aria-haspopup`, `aria-pressed`, `aria-selected`, `aria-checked`, `aria-current`, `aria-activedescendant`, `aria-autocomplete`, `aria-multiline`, `aria-orientation`, `aria-readonly`, `aria-required`, `aria-valuemax`, `aria-valuemin`, `aria-valuenow`, `aria-valuetext`, `aria-modal`, `aria-level`, `aria-posinset`, `aria-setsize`, `data-citry-ui-part`, `data-citry-disclosure-trigger`, `data-state`, and `data-disabled` |
| `panel_attrs` | `id`, `is`, `role`, `hidden`, `inert`, `popover`, `x-show`, `aria-hidden`, `aria-label`, `aria-labelledby`, `aria-roledescription`, `data-citry-ui-part`, `data-citry-disclosure-panel`, and `data-state` |
| `actions_attrs` | `is`, `role`, `tabindex`, `contenteditable`, `hidden`, `inert`, `popover`, `x-show`, `aria-hidden`, `aria-label`, `aria-labelledby`, `aria-description`, `aria-describedby`, `aria-details`, `aria-roledescription`, `aria-live`, `aria-atomic`, and `data-citry-ui-part` |

Root `hidden` and root `x-show` remain allowed so a consumer may own presence
of the complete component. Trigger `aria-describedby`, `aria-details`, and
`aria-keyshortcuts` remain allowed supplementary metadata; they do not replace
the visible title or create another widget state. Targeted unrelated
listeners, consumer `data-*`, and non-owned conforming native/ARIA attributes
remain allowed. Consumers cannot replace the trigger's visible-name
relationship, expansion state, disabled state, popup/widget state, panel
identity/presence, region semantics, or runtime ownership.

## 16. Assets and performance

Disclosure contributes one component CSS asset, one root initializer, and one
registered chevron SVG. Each instance owns one activation listener, one prop
effect, one capture-phase `beforetoggle` safety listener, at most one active
Web Animation, one title-subtree observer, one content-structure observer, and
one optional observer shared across its relevant ancestor fieldsets. The
title observer watches `childList`, `characterData`, and all attributes
throughout the title subtree, then classifies only the rules in section 3.
The content observer watches panel/actions subtree `childList`, `popover`,
`data-citry-ui-part`, and `is` changes. The fieldset observer watches ancestor
`disabled` attributes and direct-child changes needed for the first-legend
rule. It creates no global store, network request, font, resize observer,
collection registry, per-panel child component, or third-party runtime.

The implementation may reuse shared `_attrs`, `_validation`, Form context, and
CIcon machinery. It must not import Accordion's registry, item collector,
value canonicalizer, group client context, or keyboard delegation. Accordion's
height animation and morph handoff are embedded in its initializer rather than
a reusable asset. The first Disclosure implementation should use a bounded
family-local controller. A later private extraction is justified only after
tests prove identical behavior without changing either public contract.

Every panel stays in the DOM. Diagnostics record component CSS and JavaScript
raw, gzip, and Brotli sizes plus server render/output at 1, 10, 100, 500, and
1,000 instances. Browser diagnostics compare initialization, first activation,
and rapid reversal at 1, 10, and 100 instances. The operational budget is O(1)
listeners/effects/observers and one possible animation per instance, no new
third-party dependency, no idle timer, and no work proportional to panel
descendant count during settled state. Measured size and timing become the
release baseline; a material increase requires requalification.

## 17. Acceptance matrix

Required automated evidence:

| Area | Required evidence |
|---|---|
| Render and schema | open/closed server output; exact native anatomy and IDs; conditional region semantics; actions placement/labeling; every input default and validation; missing/duplicate/unknown fills; invalid nested Disclosure/Accordion placement; server and settled-DOM title validation with recovery; empty/whitespace/decorative-only titles; post-init text/attribute invalidation and repair; server/dynamic modal-dialog and raw-popover rejection; unresolved custom-element/customized-built-in/open-shadow-host rejection; Disclosure root inside an open ShadowRoot; same-task title mutation plus activation; same-task Dialog insertion plus close/open request; descendant `beforetoggle` cancellation during a close animation; validation-only initialization, exact opening/closing suspension, queued owner reconciliation, and repaired readiness; exact exports and API schema |
| Attribute and security | copied maps; class/style merging; every destination; representative static/dynamic reserved aliases; runtime-prefix rejection; hostile title/action/panel text; fixed icon path |
| Interaction | pointer, touch-equivalent click, Enter, Space, programmatic button click, no Arrow/Home/End interception, disabled no-op, capture-phase consumer listeners, and native Tab order |
| Controlled state | pre-commit callback shape/order, controlled refusal, owner acceptance, repeated values, omission/null release, invalid episodes, Python/server fallback, and no callback from owner updates |
| Focus and accessibility | exact `aria-expanded`/`aria-controls`; optional region label; panel focus recovery before close; close-plus-disable and hidden-root fallback through open ShadowRoots; anchored descendant force-close order and focus preservation; modal-dialog sibling composition and descendant rejection; nested-root isolation; initial and active axe checks |
| Forms | trigger `type=button`, FormData continuity, retained uncontrolled edit, reset independence, closed required control behavior, CForm/native fieldset disabledness, dynamic fieldset, and first-legend insertion/reorder |
| Animation and lifecycle | intermediate opening geometry, closing presence order, rapid reversal, zero/reduced motion, settled style cleanup, repeated initialization, same/different server fingerprint morphs, controlled morph, fragment insertion, correlated moves across disabled fieldset/first-legend ancestry, and root removal |
| Styling and environment | all variants/sizes/indicator positions; public variable and selector overrides; nested inheritance/isolation; narrow layout, long content, RTL, nested color scheme, forced colors, reduced motion, print expansion, and two brand adaptations |
| Documentation and packaging | every component-owned preview discovered and initialized; page-wide console cleanliness; `api.yml` contract; family exports, registration, asset map, wheel contents, reference schema, scaling diagnostics, Nu HTML, and visual-candidate tooling |

The Python-owned `disclosure.states` quality route includes every variant and
size, open and closed instances, disabled open/closed states, both indicator
positions, no indicator, actions, optional region, nested Disclosure and
Accordion, real form content, long content, RTL, nested light/dark schemes,
reduced-motion and print hooks, and two scheme-aware brand adaptations. Shared
tooling runs initial and active axe checks, brand contrast checks, collapsed
form continuity, and screenshot discovery.

Focused Chromium tests carry the detailed interaction and lifecycle matrix.
Release qualification covers current Firefox and WebKit behavior, complete
Tab/Shift+Tab order, touch, fieldset/legend edge cases, animation reversal,
print, and host integration without turning every browser row into a permanent
unit test.

Manual evidence covers visual-design sign-off; VoiceOver, NVDA, and JAWS
announcement of button name, expanded/collapsed state, disabled state, and
optional region; keyboard and touch use; 200 and 400 percent zoom; forced
colors; text spacing; print; real form controls; IME/editor content inside a
panel; and nested overlays during close. A source file or working preview alone
does not qualify the family.

## 18. Compatibility classification

Stable public API includes `CDisclosure`; every server/client input and
fallback rule; the title/default/actions slots and empty slot-data types;
`CDisclosureOpenChangeDetail`; callback arguments/timing; composition errors;
public variables, selectors, and reflections; ID rules; protected attribute
destinations; and always-mounted panel behavior.

Stable behavioral and structural contracts include one Boolean owner, native
heading/button semantics, actions outside the heading, no root tab stop,
Enter/Space native activation, no group keyboard handling, optional named
region, browser-effective disabledness, nested Disclosure/Accordion only in panels,
focus before close, hidden/inert closed content, server-fingerprint handoff,
rapid-animation supersession, non-clipping settled panels, and complete server
content.

The title element/attribute allowlist, nonempty textual-title rule, panel-only
placement of nested Disclosure and Accordion, prohibition of native
`dialog`/CDialog/CDrawer descendants, raw native popover rejection, the exact
coordinator-participating surface allowlist, unresolved custom-element and
authored-shadow-host rejection, sibling-modal composition path, synchronous
structure preflight, descendant `beforetoggle` guard, private
valid/invalid suspension behavior, one-diagnostic episode, and repair
reconciliation are also stable composition and error contracts. Changing
those rules can change accepted templates, focus safety, or whether a
controlled update is applied, so they are not private implementation details.

Exact default colors, type scale, spacing, radii, transition duration/easing,
and chevron path are evolvable design. Changes remain within public variable
meanings, contrast, environmental, and acceptance requirements.

`.cui-*` classes, `--_cui-*` variables, behavior-only attributes, private
context keys, initialization and handoff properties, diagnostic wording,
observer/listener organization, Web Animation organization, and incidental SVG
markup are private. Public examples and tests must not depend on them.

Changing a stable name, type, meaning, default behavior, slot, callback, public
selector/reflection, or protected destination follows the library's semantic
versioning and deprecation policy.

## 19. Public documentation contract

The reader-first `api.md` uses a software setup and operations handbook theme.
It starts with a rendered sampler, then teaches the shortest composition,
initial and browser-controlled expansion, adjacent actions and disabledness,
variants/sizes, nesting, forms/focus, customization/environment behavior, and
the structured reference. It explicitly contrasts one Disclosure with
Accordion and links native `details` for plain no-JavaScript use.

Planned component-owned examples:

| Source module | Reader task | Fixture theme and copy | Visible states | Controls | Interaction | Environmental profiles | Contract coverage | Focused browser evidence |
|---|---|---|---|---|---|---|---|---|
| `at_a_glance.py` | recognize one independent disclosure | setup handbook, "System requirements" | one closed disclosure with concise panel | trigger only | open and close | default light; narrow-safe copy | basic anatomy, default styling, indicator, always-mounted content | click, Enter, Space, ARIA, initial/active axe |
| `basic_disclosure.py` | write template and Python composition | setup handbook, "Install prerequisites" | one initially open and one initially closed independent instance | triggers | compare initial state and normal toggling | default scheme | required fills, `open`, heading level, optional region, sibling independence | server output, IDs, region relationship, no group keyboard |
| `controlled_open.py` | control expansion in the browser | diagnostic handbook, "Advanced logging" | controlled panel plus current-owner text | external Show, Hide, and Release Buttons; trigger | owner accepts/refuses requests and releases control | default scheme | client `open`, `onOpenChange` detail/timing, controlled noncommit, release | callback count/order, refusal, owner update, release, console cleanliness |
| `actions_and_disabled.py` | keep secondary actions safe and explain unavailable content | release handbook, "Release notes" and "Managed policy" | actions beside one heading; disabled open and disabled closed examples | Copy link action, trigger, external disabled toggle | Tab through trigger/actions; toggle disabledness | coarse-pointer target and narrow width | actions slot/label/attrs, heading purity, effective disabledness, open-state preservation | DOM placement, Tab order, disabled no-op, dynamic fieldset |
| `variants_and_sizes.py` | choose treatment and geometry | operations handbook status notes | outline, soft, plain; sm, md, lg; both indicator positions and hidden indicator | compact configurator outside preview content | change client presentation inputs and open panels | light and dark | variants, sizes, indicator, position, reflections, long-title wrapping | computed styles, logical placement, invalid-free prop updates |
| `nested_disclosures.py` | organize a deeper optional topic | deployment handbook, "Network setup" with "Proxy settings" and one nested Accordion | open parent with closed nested Disclosure and grouped troubleshooting items | parent, nested, and Accordion triggers | toggle each owner independently | narrow and RTL | panel-only nesting, cross-family composition, nearest-root isolation, direct-child CSS | nested activation, focus recovery, no ancestor state/style mutation |
| `overlays_and_dialogs.py` | compose transient help and a modal action safely | operations handbook, "Credential help" and "Rotate credential" | one Disclosure with an anchored Popover plus a sibling Dialog opened from the panel | Disclosure, help, open-Dialog, and close controls | close with anchored help open; open the sibling modal; close Disclosure before and after | default light DOM; open ShadowRoot is focused component evidence | anchored descendant structural close, focus preservation, sibling-modal ownership, forbidden descendant guidance | forced anchored close, same-task Dialog guard, sibling modal remains visible and focus-contained, no invisible modal |
| `forms_and_focus.py` | preserve edits and plan validation | notification handbook with email and checkbox fields | open editable panel and closed required-field warning | form controls, submit/reset, disclosure trigger | edit, close/reopen, submit, reset, close while focus is inside | default and 200 percent zoom | FormData/state continuity, validation caveat, reset independence, focus-before-close | value retention, FormData, invalid capture path, focus destination |
| `customization.py` | adapt the public surface | two operations handbook brands | one warm variable-focused and one dark RTL selector-focused Disclosure | none | compare the two stable public customization paths | light-dark tokens, explicit dark nested scheme, RTL, long title | public variables/selectors and zero-specificity consumer overrides | computed styles, logical layout, overflow, and contrast |

Every example is result-first, keeps source beside the family and out of the
wheel, collapses source by default, places configurator controls outside the
rendered subject, and produces no console error. Public examples do not teach
invalid client values or private selectors.

`api.yml` is organized by Inputs, Slots, Events, Methods, CSS, Attributes,
Selectors, and Interfaces, split by `CDisclosure`. Methods is `-`. Inputs say
whether they are server tag/Python values or browser `$c-props`. Event rows
document `onOpenChange` as a component callback and distinguish native Alpine
events. CSS rows list every `--cui-disclosure-*` variable. Attributes list
public reflected `data-*` output. Selectors use exact
`[data-citry-ui-part="..."]` names. Interfaces expand every alias, slot-data
record, and callback-detail field. All entries receive stable kebab-case IDs.

## 20. Open decisions and deferred work

No product decision blocks implementation. This design gate settles:

- authored heading/button/panel rather than `details`/`summary`;
- one public `CDisclosure` and Boolean `open`, with no item/group/value API;
- omitted or null client `open` releases control, and other invalid values
  diagnose once and release from the committed baseline;
- the exact `onOpenChange(next_open, detail)` payload and pre-commit timing;
- required title/default slots plus optional adjacent actions;
- always-mounted panel presence and focus-before-close behavior;
- browser-effective fieldset disabledness;
- family-local animation/handoff code for the first implementation; and
- no-JavaScript toggling, lazy presence, arbitrary icons, methods, and headless
  behavior outside the initial contract.

Deferred work:

- a shared private height-presence helper after two production families prove
  identical lifecycle needs and tests;
- arbitrary registered indicator names or an indicator slot after real theming
  demand;
- lazy mounting after representative application-scale evidence and an
  explicit form, validation, source, focus, state, and accessibility contract;
- automatic validation-driven opening after controlled-state and focus timing
  are proven across Citry Events;
- URL/hash ownership and application persistence;
- a generic motion/collapse utility for non-disclosure content; and
- headless disclosure behavior after representative application pages justify
  a second delivery mode.

Requalify or reject this architecture if:

- working without JavaScript or native find-in-page auto-expansion becomes a
  release requirement;
- current browser and assistive-technology evidence shows native `details` can
  satisfy controlled refusal, disabled fieldsets, heading/actions anatomy,
  closing animation, focus, and morph behavior with less complexity;
- applications repeatedly need values, mutual exclusion, multiple expansion,
  mandatory state, or Arrow navigation, in which case the job belongs to
  Accordion;
- always-mounted representative panels cause material cost and a lazy contract
  can state every form, validation, state, focus, and accessibility consequence;
- the actions slot has no concrete application use before release, in which
  case its input, attrs, slot type, part, and variable should be removed
  together;
- `soft` and `plain` do not deliver distinct supported jobs, in which case the
  variant surface should shrink; or
- after controlled state, disabledness, actions, and animation are removed,
  the result offers no meaningful benefit over documented native `details`.
