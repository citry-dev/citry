# Citry UI Accordion component specification

**Status (2026-08-08): production runtime, public documentation, focused
server and browser evidence, reusable quality scenario, and independent
implementation review complete. Human visual, assistive-technology, and
release qualification remain.**

## 1. Purpose and product bar

`CAccordion` groups related sections whose headings reveal or hide their own
content. It targets FAQs, reference material, settings explanations, product
details, filters, and other finite disclosure groups. The production bar is a
styled, accessible, server-rendered family with controlled and uncontrolled
browser ownership, single and multiple expansion, item-level disabling,
keyboard navigation, stable form content, nested groups, responsive styling,
and public customization comparable to a mature suite such as Vuetify.

The closest accessibility baseline is the WAI-ARIA Accordion pattern. The
family uses native heading and button elements, not `details`/`summary`, because
it owns grouped expansion, controlled browser state, heading levels, adjacent
actions, and stable cross-browser animation as one contract.

Common jobs and their shortest supported paths:

| Job | Shortest path | Classification |
|---|---|---|
| Reveal one forest-guide section | `CAccordion(value="canopy")` with `CAccordionItem` declarations | direct API |
| Let every section close | default `collapsible=True` | direct API |
| Require an open section after the first expansion | `collapsible=False` | direct API |
| Open several sections | `multiple=True`, with a sequence `value` | direct API |
| Control expansion in Alpine | `$c-props="{value: open, onValueChange: next => open = next}"` | client API |
| Disable the complete group | `disabled=True` or client `disabled` | direct API |
| Disable one item | `CAccordionItem(disabled=True)` or its client `disabled` | direct API |
| Add an action beside a heading | the item's `actions` slot and `actions_label` | composition |
| Set the document outline | `heading_level=2` through `6` | direct API |
| Keep panel controls in native forms | default always-mounted panel content | built-in behavior |
| Put one Accordion inside a panel | nested `CAccordion` in the parent item's default slot | composition |
| Adapt color, spacing, and borders | public variables, selectors, `class_`, `style`, and attrs | CSS or native HTML |
| Show one unrelated disclosure | future `CDisclosure` | separate component |
| Build navigation, a tree, or a stepper | dedicated component | separate component |

Smallest template:

```citry-html
<c-CAccordion value="canopy">
  <c-CAccordionItem value="canopy">
    <c-fill name="title">Forest canopy</c-fill>
    <c-fill name="default">
      The canopy captures most incoming sunlight.
    </c-fill>
  </c-CAccordionItem>
  <c-CAccordionItem value="understory">
    <c-fill name="title">Understory</c-fill>
    <c-fill name="default">
      The understory supports shade-tolerant plants.
    </c-fill>
  </c-CAccordionItem>
</c-CAccordion>
```

Python composition uses one component that emits the direct item roots:

```python
class FieldGuideItems(Component):
    template = """
      <c-CAccordionItem value="canopy">
        <c-fill name="title">Forest canopy</c-fill>
        <c-fill name="default">Upper forest layer</c-fill>
      </c-CAccordionItem>
    """


CAccordion(
    value="canopy",
    slots={"default": FieldGuideItems()},
)
```

Non-goals are a standalone Disclosure, horizontal disclosure layout, tree or
menu navigation, stepper progress, virtualized or remote panels, drag and drop,
automatic URL/hash synchronization, and a headless API. Headless work remains
parked until real applications establish its authoring and performance needs.

## 2. Prior art and complaints

Current evidence supports one state owner, real native buttons, configurable
heading levels, a separate action area, controlled and uncontrolled values,
single and multiple modes, item disabling, public state markers, always-mounted
content by default, and optional arrow-key focus movement.

Source record:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| WAI-ARIA APG Accordion | 2026-08-08 | [pattern](https://www.w3.org/WAI/ARIA/apg/patterns/accordion/) | heading/button/panel relationships, Enter/Space, Tab order, optional arrows, `aria-expanded`, `aria-controls`, conditional `aria-disabled`, and restrained region use |
| Vuetify | master inspected 2026-08-08 | [group source](https://github.com/vuetifyjs/vuetify/blob/master/packages/vuetify/src/components/VExpansionPanel/VExpansionPanels.tsx), [item source](https://github.com/vuetifyjs/vuetify/blob/master/packages/vuetify/src/components/VExpansionPanel/VExpansionPanel.tsx), title/text sources and issue [#21615](https://github.com/vuetifyjs/vuetify/issues/21615) | styled-suite priority; group value, variants, inherited item defaults, title/text slots, eager content, icons, hover, readonly, and customization pressure |
| React Spectrum | reviewed 2026-08-08 | [Accordion](https://react-spectrum.adobe.com/v3/Accordion.html), [Disclosure](https://react-spectrum.adobe.com/Disclosure) | separate standalone Disclosure, controlled keys, multiple mode, per-item disabled, explicit title/panel/header anatomy, sizes and density |
| Radix Primitives | 1.2.17 docs | [Accordion](https://www.radix-ui.com/primitives/docs/components/accordion), issues [#3601](https://github.com/radix-ui/primitives/issues/3601), [#2808](https://github.com/radix-ui/primitives/issues/2808), and [#2353](https://github.com/radix-ui/primitives/issues/2353) | controlled/uncontrolled state, collapsible single mode, public state markers, animation variables, and mounting/form pitfalls |
| Ark UI and Chakra UI | reviewed 2026-08-08 | [Ark Accordion](https://ark-ui.com/docs/components/accordion), [Chakra Accordion](https://www.chakra-ui.com/docs/components/accordion) | root/item context, lazy-mount tradeoffs, item state, keyboard navigation, styled size/variant expectations |
| Mantine | reviewed 2026-08-08 | [Accordion](https://mantine.dev/core/accordion/) | heading order, concise single/multiple values, disable-collapse behavior, indicator position, actions outside the trigger, variants, sizes, and Styles API |
| Material UI | reviewed 2026-08-08 | [guide](https://mui.com/material-ui/react-accordion/), [API](https://mui.com/material-ui/api/accordion/) | summary/details/actions anatomy, heading customization, mounted-by-default SEO decision, controlled item state, and transition escape hatch |
| PrimeVue | reviewed 2026-08-08 | [Accordion](https://primevue.org/accordion/) | Vue compound anatomy, dynamic item generation, single/multiple value shape, and styled panels |
| Bootstrap | 5.3 docs | [Accordion](https://getbootstrap.com/docs/5.3/components/accordion/) | always-open grouping, flush treatment, CSS variables, reduced motion, and the cost of a second Collapse API |

Material complaints and dispositions:

| Complaint or limitation | Status | Citry decision |
|---|---|---|
| Radix closed panels removed descendants, surprising SEO and form users. | #3601 closed with `forceMount` guidance; #2808 remains a documented user pitfall. | Keep every panel's server content mounted. Closed panels are hidden and inert, not unmounted. Do not add a default lazy/unmount mode. |
| Radix users confused writable `data-state` with controlled state. | #2353 closed with `value`/`defaultValue` guidance. | Public `data-state` is a read-only styling reflection. Only Python `value`, client `value`, or user interaction owns expansion. |
| Vuetify required CSS to suppress hover. | #21615 closed for the v4.1.0 milestone; current source carries a `hover` input. | Do not add a hover Boolean. Public hover variables/selectors make the visual state removable without another behavioral input. |
| MUI keeps large collapsed trees mounted and documents an unmount escape hatch for performance. | Current documented tradeoff. | Prefer form, SEO-source, and state continuity for the core family. Record repeated-instance diagnostics; defer lazy mounting until application evidence justifies the semantic cost. |
| Mantine warns that Buttons and links cannot sit inside its button trigger. | Current documented composition constraint. | Give every item a separate `actions` slot adjacent to, never inside, the heading button. |
| Bootstrap transition methods ignore calls while a transition is active. | Current documented behavior. | Rapid Citry requests cancel or supersede the prior panel animation. State changes are never silently ignored. |

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue`, update event | direct API | Python/client `value`, `onValueChange` | adopt with exact mode-dependent value shapes |
| `multiple` | direct API | server `multiple` | adopt as structural mode |
| `mandatory` | direct API | inverse `collapsible` in single mode | adopt clearer behavior name |
| group `disabled` | direct API | server/client `disabled` | adopt |
| `max` selected items | controlled composition | callback limits application state | omit until a common job appears |
| selected class | public selector | item/trigger/panel `data-state` | avoid class-name input |
| `variant=default/accordion/inset/popout` | direct/CSS | `outline`, `soft`, `separated`, `plain`; utilities for inset/popout | adopt common visual jobs without Material-specific motion |
| `flat`, `gap`, `noDivider`, `tile`, `rounded`, elevation | direct/CSS | variant plus public border, radius, gap, and shadow variables | capability without prop parity |
| theme, background, color | theme/CSS | color-scheme defaults and public variables | adopt |
| root tag | native/CSS | fixed neutral `div`, `class_`, `style`, `attrs` | reject polymorphism to keep direct-child contracts |
| title/text props | slots | item `title` and default slots | adopt slots rather than duplicate text inputs |
| expand/collapse icons, hide actions | direct API | fixed chevron, client `indicator`, `indicatorPosition` | adopt the common jobs; omit arbitrary icon replacement initially |
| `eager` | built-in behavior | every panel stays mounted | always eager |
| item disabled | direct API | server/client item `disabled` | adopt |
| readonly/focusable/static/ripple | controlled/CSS/native | controlled value, disabled item, native focus, no ripple | omit ambiguous or presentation-specific inputs |
| title default/actions scoped slots | slots | title slot plus separate adjacent actions slot | adopt safer anatomy; slot data remains server snapshot only |
| text/default slot | slot | item default slot | adopt |
| group default slot `prev`/`next`; public methods | native keyboard/client state | Arrow/Home/End focus, `value`, callback | no imperative group API initially |

## 3. Public composition and anatomy

The public family has two components. `CAccordionItem` is a real rendered
component, not a declaration placeholder. This keeps item-level `$c-props`,
native events, refs, cleanup, and client-context registration available.

```text
CAccordion (div)
└─ CAccordionItem (div)
   ├─ header row (div)
   │  ├─ heading (h2...h6)
   │  │  └─ trigger (button)
   │  │     ├─ title
   │  │     └─ indicator (span)
   │  │        └─ decorative svg
   │  └─ actions (optional div, outside heading/button)
   └─ panel (div, optional region role)
      └─ body (div)
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CAccordion` | neutral `div` | `class_`, `style`, `attrs` land on the root | owns direct item registration and group state |
| `CAccordionItem` | neutral `div` | root, heading, trigger, panel, and optional actions maps have exact destinations | belongs to one Accordion; trigger controls one panel, which region mode labels |

Every item requires one `title` fill and one default fill. It may have one
`actions` fill. Values are nonempty canonical strings and unique within the
nearest Accordion. The owner rejects no items, duplicate values, missing or
duplicate fills, unknown fills, and non-item output in its default slot.

`CAccordionItem` outside `CAccordion` raises. A direct item nested inside
another item's title, panel, or actions raises until a nested `CAccordion`
creates a new owner. A nested Accordion is valid only inside the panel body.
Title content renders inside a native button and therefore permits phrasing,
noninteractive content only. Actions render beside the heading. Panel content
accepts flow content and nested components.

Stable generated IDs use the root's explicit `id` or component ID plus a hash
of the canonical item value. Raw values never become HTML IDs. The trigger owns
`aria-controls`. Every panel owns the referenced ID. When `region=True`, the
panel also owns `role="region"` and `aria-labelledby` as one relationship.

An internal transparent slot collector runs after all item children settle. It
validates the complete server registry while leaving every `CAccordionItem` as
a real component and direct root child. No public third structural component is
needed. This is the post-design anatomy simplification pass: separate Header,
Trigger, Panel, and Indicator declarations would add ceremony without adding
expressivity because each item always owns exactly one of each.

## 4. Server inputs and client inputs

`CAccordion.Kwargs`:

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `str | Sequence[str] | None` | `None` | initial value/server fallback | string or null in single mode; duplicate-free sequence or null in multiple mode; every value must identify an item |
| `multiple` | `bool` | `False` | structural server-only | chooses the value shape and whether several items may remain open |
| `collapsible` | `bool` | `True` | reactive configuration | in single mode, permits the open item to close; must remain true in multiple mode |
| `disabled` | `bool` | `False` | reactive configuration | disables every trigger without changing open panels; enclosing Form/fieldset disabledness remains dominant |
| `loop` | `bool` | `True` | reactive configuration | wraps optional Arrow Up/Down focus navigation |
| `variant` | `Literal["outline", "soft", "separated", "plain"]` | `"outline"` | reactive presentation | selects the visual treatment |
| `size` | `Literal["sm", "md", "lg"]` | `"md"` | reactive presentation | selects trigger and panel geometry |
| `indicator` | `bool` | `True` | reactive presentation | shows the owned decorative chevron |
| `indicator_pos` | `Literal["start", "end"]` | `"end"` | reactive presentation | places the chevron before or after title content |
| `heading_level` | `Literal[2, 3, 4, 5, 6]` | `3` | structural server-only | renders the native heading level for every direct item |
| `region` | `bool` | `False` | structural server-only | adds `role="region"` to every panel; use deliberately to avoid landmark proliferation |
| `id` | `str | None` | `None` | structural server-only | supplies the root and ID-pair prefix |
| `class_` | `CClassValue | None` | `None` | server presentation | merges root classes with `attrs` |
| `style` | `CStyleValue | None` | `None` | server presentation | merges root inline styles with `attrs` |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted root attributes | copied, validated, then bound to the root |

`CAccordionItem.Kwargs`:

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `str` | required | structural identity | canonical, nonempty, U+0000-free, unique item value |
| `disabled` | `bool` | `False` | reactive configuration | disables this trigger while preserving its current panel state |
| `actions_label` | `str | None` | `None` | structural accessibility | when supplied with actions, emits one named `group`; forbidden without actions |
| `class_`, `style` | structured value or `None` | `None` | server presentation | merge onto the item root |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted item-root attrs | item-root destination |
| `heading_attrs` | `Mapping[str, object] | None` | `None` | trusted heading attrs | native heading destination |
| `trigger_attrs` | `Mapping[str, object] | None` | `None` | trusted button attrs | native trigger destination; unrelated Alpine listeners are allowed |
| `panel_attrs` | `Mapping[str, object] | None` | `None` | trusted panel attrs | panel destination; region naming remains component-owned when enabled |
| `actions_attrs` | `Mapping[str, object] | None` | `None` | trusted action-wrapper attrs | valid only when actions exist |

Client inputs on `CAccordion`:

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `value` | single `string | null`; multiple `string[] | null` | releases control and preserves current valid browser state | no open item(s) | one diagnostic per episode; retain the prior valid control or current fallback | item, trigger, and panel states |
| `onValueChange` | function | no callback | invalid | ignore with one diagnostic | user/removal notifications |
| `collapsible` | bool | Python fallback | invalid | Python fallback with one diagnostic | allowed transitions and `aria-disabled` |
| `disabled` | bool | Python fallback | invalid | Python fallback with one diagnostic | trigger disabledness and mirrors; enclosing Form/fieldset disabledness remains dominant |
| `loop` | bool | Python fallback | invalid | Python fallback with one diagnostic | Arrow focus wrapping |
| `variant`, `size`, `indicatorPosition` | documented enum | Python fallback | invalid | Python fallback with one diagnostic | root mirrors and CSS |
| `indicator` | bool | Python fallback | invalid | Python fallback with one diagnostic | indicator visibility |

`CAccordionItem` accepts a client `disabled` Boolean with the same
omitted/null/invalid rules. It registers changes through the nearest Accordion
client context. `multiple`, `heading_level`, `region`, item identity, slots,
attribute destinations, and actions labeling remain server structural data.

## 5. State model

The root owns one normalized expanded value: `string | null` in single mode or
a duplicate-free ordered `string[]` in multiple mode. Item order follows DOM
order; multiple values retain item order rather than caller array order.

| Transition | Guard | Callback | Uncontrolled commit | Controlled result |
|---|---|---|---|---|
| closed item request | group/item enabled | next value, `expanded=True`, source `activation` | open it; close prior single item | callback only, latest valid prop wins |
| open item request | enabled and single `collapsible=True`, or multiple | next value, `expanded=False`, source `activation` | close it | callback only |
| open single item with `collapsible=False` | same item | none | no-op, set `aria-disabled=true` | no-op |
| disabled trigger request | disabled | none | no-op | no-op |
| value prop update | valid shape and known values | none | not applicable | apply exact normalized value |
| value prop omission | controlled episode active | none | release while preserving current valid state | browser becomes owner |
| open item removed | structural change | normalized fallback, source `removal` | drop it; if noncollapsible single, choose nearest enabled survivor or null when none exists | impossible controlled value enters structural fallback until a valid prop arrives |
| focused item becomes disabled | another enabled trigger exists | none | move focus to nearest enabled trigger before native disabling | same |

`collapsible=False` does not force an item open on initialization. After one is
open, users cannot close the group completely. In multiple mode every item
remains independently collapsible; Python `collapsible=False` is rejected and
an invalid client false value falls back to true.

Structural removal may still return a noncollapsible group to null when no
enabled item survives. Reconciliation batches every removed open value in
prior item order and emits at most one callback. The removal callback carries
the normalized value, `itemValue=null`, `removedValues` with the removed open
values, `expanded=False`, and `source="removal"`. When a focused item is
removed, focus moves to the nearest enabled surviving trigger. If none exists,
Accordion adds no synthetic focus target; the application performing the
structural removal owns a stable external focus destination.

Disabled items may remain expanded. Disabled means the user cannot toggle the
item and Arrow navigation skips it; it does not erase state or content.
An enclosing disabled `CForm` or native `fieldset` also disables the native
trigger buttons and therefore dominates client or Python `disabled=False`.
Public disabled mirrors follow that browser-effective result.

Each invalid client input reports once for one continuous invalid episode,
even if its invalid value changes. A valid value or omission ends the episode.
Before the first valid controlled value, invalid control leaves current browser
state untouched. After valid control, invalid control retains that prior value
while its items still exist; otherwise structural fallback applies.

Rapid requests supersede an in-flight animation. They never queue stale state
or receive Bootstrap-style silent rejection.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CAccordion` | `default` | yes | one fill containing one or more direct items | `{}` (`CAccordionDefaultSlotData`) | none |
| `CAccordionItem` | `title` | yes | exactly one | `{}` (`CAccordionItemTitleSlotData`) | none |
| `CAccordionItem` | `default` | yes | exactly one | `{}` (`CAccordionItemDefaultSlotData`) | none |
| `CAccordionItem` | `actions` | no | zero or one | `{}` (`CAccordionItemActionsSlotData`) | wrapper omitted |

Slot data is intentionally empty. Expansion and disabledness change in the
browser, while server slot callbacks do not rerender on client state changes.
Providing an initial `expanded` Boolean would look reactive while becoming
stale. Use client props, callbacks, reflected attributes, and CSS for changing
state.

Title content is inside a native button and must contain only phrasing,
noninteractive content. It cannot contain another button, link, input, label,
select, textarea, audio/video control, nested Accordion, or element that
creates a second focus or activation owner. Actions accept ordinary controls
but are outside the heading. Panel content accepts flow content, forms, and a
nested Accordion.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onValueChange` | `(next_value, detail)` | accepted trigger activation or structural removal fallback | after validation, before uncontrolled DOM commit | callback fires but controlled prop remains authoritative | return value ignored |

`detail` is `{value, previousValue, itemValue, removedValues, expanded,
source}`. For activation, `itemValue` is the trigger value and `removedValues`
is empty. For one batched structural reconciliation, `itemValue` is null and
`removedValues` contains every removed open value in prior item order.
`source` is `"activation"` for every accepted native trigger click or
`"removal"` for a structural fallback. `activation` deliberately does not
claim whether the browser click came from pointer, keyboard, assistive
technology, or `HTMLElement.click()`: those paths are not reliably
distinguishable at the delegated listener. Values use the mode-dependent
public shape. A no-op, disabled request, or same-item request in
noncollapsible mode does not notify.

Native `click`, `keydown`, `focusin`, and action events remain normal browser
events. Component-tag listeners on `CAccordion` observe bubbled descendant
events and must inspect `event.target`. `CAccordionItem.trigger_attrs` is the
advanced path for a listener whose `currentTarget` must be the native trigger.
The component callback is the expansion notification; no custom DOM event is
added.

No public method is needed. Client `value`, `onValueChange`, native element
refs, and `button.focus()` cover the supported jobs without a second state API.

## 8. Semantics, keyboard, focus, and assistive technology

Each item uses one native `h2` through `h6` containing exactly one native
`button`. The button owns `aria-expanded` and `aria-controls`. The panel always
owns the stable ID referenced by the button. `region=True` adds both
`role="region"` and `aria-labelledby` back to the button. With `region=False`,
the neutral panel has neither role nor accessible-name attribute. Region mode
defaults false because the APG warns against landmark proliferation, especially
with more than roughly six open panels.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| trigger | Enter or Space | native click requests toggle | stays on trigger | native button behavior |
| trigger | Arrow Down | focus next enabled trigger | next or first when looping | yes |
| trigger | Arrow Up | focus previous enabled trigger | previous or last when looping | yes |
| trigger | Home | focus first enabled trigger | first | yes |
| trigger | End | focus last enabled trigger | last | yes |
| anywhere | Tab / Shift+Tab | normal document order | every enabled trigger and visible panel control participates | no |
| open panel containing focus closes | accepted close | focus controlling trigger before inert/hidden state | trigger | no |

Arrow/Home/End support is an optional APG enhancement. It never creates a
roving Tab stop: all enabled triggers remain in normal Tab order. Disabled
native buttons are skipped. When a noncollapsible single item is open, its
trigger remains focusable and receives `aria-disabled="true"`, as prescribed
by APG; it is not given the native `disabled` attribute. If the group or item
is actually disabled, the native `disabled` attribute wins and the redundant
`aria-disabled` marker is omitted.

The indicator wrapper is `aria-hidden`; its private SVG is nonfocusable.
`indicator=False` hides the HTML wrapper rather than applying the HTML
`hidden` attribute to an SVG element. Visible title content supplies the
accessible name, so trigger attrs cannot replace it with `aria-label` or
`aria-labelledby`. Adjacent actions do not enter the heading or trigger name.
`actions_label` produces a named `group` only when requested.

Collapsed panels are `hidden`, `inert`, and absent from the accessibility tree.
During close animation they become inert and `aria-hidden` before geometry
shrinks. During open animation those states clear before content becomes
interactive. Assistive technology receives the committed expanded state, not
intermediate animation frames.

## 9. Native forms and validation

Accordion is not itself a form participant. Consumer controls inside panels
retain their native owner, name, value, reset, autocomplete, validation, and
submission behavior. Panels are never unmounted, so closing one does not erase
an uncontrolled edit, remove a successful control from `FormData`, or reset a
client component.

Accordion trigger buttons use `type="button"`. An enclosing disabled native
`fieldset`, including CForm's fieldset, still disables those buttons. Server
output consumes CForm's provided disabled fallback when available. Client
behavior also checks each trigger's native `:disabled` result so an ordinary
ancestor fieldset and its first-legend exception remain browser-authoritative.

`hidden` and `inert` do not disable descendant controls or exempt them from
constraint validation. A required invalid control in a collapsed panel can
still block submission while remaining unavailable for focus. Accordion does
not guess which validation policy or panel should win. Applications using
native constraints across collapsible sections must keep required panels open,
control `value` from validation state, or handle the Form's captured `invalid`
events to expand the owning item before moving focus. Public examples must not
hide an invalid required control without teaching that policy.

Citry Events rerenders preserve browser-owned panel controls under their normal
morph keys. Accordion adds no form serialization, event action, or error
transport protocol.

## 10. Styling and theme contract

Variants:

- `outline`: one connected bordered group;
- `soft`: connected items on a quiet filled surface;
- `separated`: independent elevated item surfaces with root gap; and
- `plain`: transparent items with simple dividers.

Sizes `sm`, `md`, and `lg` change trigger/panel padding, indicator geometry,
and type scale. `indicator_pos` uses logical start/end and follows RTL.

Public variables:

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-accordion-background` | color | connected root/item surface | scheme-derived Canvas |
| `--cui-accordion-foreground` | color | title and panel foreground | CanvasText |
| `--cui-accordion-border-color` | color | root, item, and divider border | scheme-derived current color mix |
| `--cui-accordion-border-width` | length | stable border geometry | `1px` |
| `--cui-accordion-radius` | length | group/item corner radius | `0.75rem` |
| `--cui-accordion-gap` | length | separated item gap | `0.75rem` |
| `--cui-accordion-shadow` | shadow | separated item elevation | small scheme-derived shadow |
| `--cui-accordion-trigger-background` | color | resting trigger surface | transparent |
| `--cui-accordion-trigger-hover-background` | color | enabled hover surface | current-color mix |
| `--cui-accordion-trigger-open-background` | color | expanded trigger surface | accent mix |
| `--cui-accordion-trigger-open-color` | color | expanded title/indicator | scheme blue |
| `--cui-accordion-focus-color` | color | trigger focus ring | Highlight |
| `--cui-accordion-indicator-color` | color | chevron foreground | currentColor |
| `--cui-accordion-trigger-padding-inline` | length | horizontal trigger inset | size-derived |
| `--cui-accordion-trigger-padding-block` | length | vertical trigger inset | size-derived |
| `--cui-accordion-panel-padding-inline` | length | horizontal body inset | size-derived |
| `--cui-accordion-panel-padding-block` | length | vertical body inset | size-derived |
| `--cui-accordion-actions-gap` | length | adjacent action spacing | `0.5rem` |
| `--cui-accordion-duration` | time | panel and indicator transition | `180ms` |
| `--cui-accordion-easing` | easing | panel and indicator transition | `ease-out` |

Public selectors:

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="accordion"]` | group root | always | owns direct items |
| `[data-citry-ui-part="accordion-item"]` | item surface | every item | direct root child |
| `[data-citry-ui-part="accordion-header"]` | heading/action row | every item | direct item child |
| `[data-citry-ui-part="accordion-heading"]` | native heading | every item | contains trigger only |
| `[data-citry-ui-part="accordion-trigger"]` | native button | every item | only heading child |
| `[data-citry-ui-part="accordion-title"]` | title wrapper | every item | trigger child |
| `[data-citry-ui-part="accordion-indicator"]` | decorative indicator `span` | every item | trigger child; owns one private SVG and may be hidden |
| `[data-citry-ui-part="accordion-actions"]` | adjacent actions | when filled | header-row child outside heading |
| `[data-citry-ui-part="accordion-panel"]` | controlled panel | every item | direct item child |
| `[data-citry-ui-part="accordion-body"]` | panel content inset | every item | direct panel child |

Public reflected attributes:

| Public reflected attribute | Values | Meaning |
|---|---|---|
| root `data-variant` | `outline`, `soft`, `separated`, `plain` | effective visual treatment |
| root `data-size` | `sm`, `md`, `lg` | effective size |
| root `data-multiple` | present/absent | structural multiple mode |
| root `data-collapsible` | present/absent | open items may close; always present in multiple mode |
| root `data-disabled` | present/absent | effective group disabledness |
| root `data-loop` | present/absent | Arrow navigation wraps |
| root `data-indicator` | present/absent | indicator is visible |
| root `data-indicator-pos` | `start`, `end` | effective logical placement |
| item/trigger/panel `data-state` | `open`, `closed` | committed item expansion |
| item/trigger `data-disabled` | present/absent | effective item disabledness |
| item `data-value` | canonical string | public item identity |

Every `data-*` row above is a read-only styling and inspection contract, never
an input. Defaults live in the named Citry UI cascade layer with zero-specificity
`:where()` selectors. Public variables resolve through private effective
variables so ancestor and root overrides work. Consumer unlayered CSS and
inline style remain able to override defaults.

## 11. Environmental behavior

Default tokens support light and dark color schemes, including nested scheme
scopes. Direct-child selectors prevent an outer variant, divider, and radius
rule from restyling nested Accordion roots; public variables inherit by design
and may be reset on a nested root.

Long titles, URLs, panel text, and action labels wrap without horizontal page
overflow. The header row lets title and actions shrink or wrap independently.
Logical properties support RTL and move start/end indicators without changing
DOM order. At narrow widths and 200/400 percent zoom, all text and controls
remain reachable.

Panel animation reads the public duration/easing tokens, cancels stale
animations, and restores auto block size after completion. `prefers-reduced-motion:
reduce` and a zero duration commit immediately. Closed panels use a component
owned `[hidden] { display: none !important; }` rule because generic component
display styles can otherwise defeat the native hidden default.

Forced colors uses system borders, foreground, focus, and indicator color.
Open state is not color-only: `aria-expanded`, visible panel content, and
indicator rotation remain. Print disables animation and prints every panel
expanded so hidden reference content is not lost on paper; trigger buttons
remain identifiable headings but do not imply interactive printed behavior.

There are no library-authored visible strings. All title, panel, and action
content belongs to the application. Locale and translation remain separate
follow-up work.

## 12. Overlay and layering behavior

Open panel and action wrappers do not set `overflow: hidden`, z-index,
transform, isolation, or containment after an animation completes. Temporary
animation clipping is confined to the panel while block size changes.
Nested menus, Combobox popups, and Dialogs must use their normal top-layer or
portal strategy if opened during that bounded transition.

Accordion does not own overlay focus, Escape, outside click, positioning, or
dismissal. Actions and panel content retain those responsibilities.

## 13. Collections, async data, and identity

Accordion is a finite keyed collection. Canonical item values are copied,
newline-normalized, U+0000-free strings. Duplicate values fail before the
completed server render is accepted. Root server values and client values use
the same canonicalizer before lookup.

Item client registration records root, trigger, panel, value, disabledness,
and cleanup generation. It never relies on DOM position as identity. Reorder,
insert, and removal preserve open and focused state by value. A removal
fallback uses the prior ordered registry to choose the nearest enabled
survivor when single noncollapsible mode requires one.

Accordion fetches no data. Async panel contents, loading, errors, retry,
cancellation, stale results, and caching belong to panel-owned components.

## 14. Server render, morph, and cleanup

Server output includes all item headings and all panel content. The effective
initial value sets `aria-expanded`, public mirrors, and collapsed
`hidden`/`inert` state. Without JavaScript, the selected panels remain readable
but trigger buttons do not toggle.

`CAccordion` initializes before its child items, creates one reactive client
context with a generation-aware `registerItem()` API, and provides it through
the Citry client provide/inject mechanism. Each real `CAccordionItem`
initializer injects that context, registers its exact DOM surfaces, and updates
its own reactive disabled fallback. Registration and cleanup trigger a bounded
root reconciliation after the current initialization batch, so replacements
do not create transient duplicate-value errors or stale unregisters.

The root observes actual ancestor native fieldsets' `disabled` attributes and
direct child lists. The bounded observer re-reads `trigger.matches(":disabled")`
so dynamic disabledness and first-legend ordering update interaction, styling,
and public mirrors without one observer per item. A correlated move to a
different ancestor reinitializes the Accordion and rebuilds that bounded
ancestor set.

The root installs delegated capture listeners for `click`, `keydown`, and
`focusin`. Capture preserves component behavior when a consumer listener on a
trigger or panel descendant stops propagation. The root creates one Web
Animation only for a panel whose geometry changes.
Opening removes hidden/inert/ARIA-hidden state, measures the body, and animates
from zero to its current block size. Closing first restores focus to the
trigger when needed, makes the panel inert and ARIA-hidden, animates to zero,
then adds native hidden. Completion returns inline block size to auto. A new
request cancels the old Animation and starts from current computed geometry.

Cleanup removes all three root listeners, cancels every active Animation, disposes
the client context, and ignores stale item unregister callbacks. Repeated
initialization must not duplicate listeners or registration. Correlated rerender
uses a root handoff record containing current browser value, previous item
order, focused item value, and last server value fingerprint. A changed server
value updates uncontrolled state; an unchanged server value preserves the
browser-owned value. A supplied valid client prop always wins.

## 15. Security and content trust

Item values, root `id`, and `actions_label` unwrap Citry `Const`, accept only
strings, copy into exact base `str` without honoring `__html__`, normalize
CRLF/CR to LF, reject U+0000, and apply their field-specific nonempty or ID
rules. Raw item values are escaped in data attributes and hashed for generated
IDs. Title and panel slots use ordinary Citry escaping; Accordion never treats
application text as HTML. The indicator uses CIcon's private allowlisted glyph
resolver and no caller SVG or URL.

Every caller-owned attrs mapping is copied before validation. All destinations
reject case-insensitive replacement of their part markers, public mirrors,
owned native/ARIA attributes, IDs, Citry/Citry Events/runtime namespaces, and
whole-object bindings that cannot be inspected. They reject `x-html`, `x-text`,
`x-if`, `x-for`, `x-teleport`, and `x-ignore`, including modifier forms, when
those directives could replace, clone, relocate, or suppress owned runtime.

Additional destination rules:

- root attrs reject role, tabindex, contenteditable, aria-label,
  aria-labelledby, aria-roledescription, aria-hidden, inert, and `popover`;
  whole-component `hidden` and `x-show` remain the consumer presence path;
- item attrs reject role, tabindex, contenteditable, aria-label,
  aria-labelledby, aria-roledescription, aria-hidden, hidden, inert, `popover`,
  and `x-show` because item membership and visibility belong to the Accordion
  state owner;
- heading attrs reject role, aria-level, tabindex, contenteditable, aria-label,
  aria-labelledby, aria-roledescription, aria-hidden, hidden, inert, `popover`,
  and `x-show` so the native heading remains named by its visible trigger;
- trigger attrs reject type, disabled, role, tabindex, aria-expanded,
  aria-controls, aria-disabled, aria-label, aria-labelledby,
  aria-roledescription, aria-hidden, and independent
  hidden/inert/`popover`/`x-show` ownership. They also reject
  `popovertarget`, `popovertargetaction`, `command`, and `commandfor` so one
  activation cannot drive a second native visibility owner;
- panel attrs reject role, ID, aria-label, aria-labelledby,
  aria-roledescription, hidden, inert, aria-hidden, `x-show`, `popover`, and
  dynamic/property aliases of every owned field;
- actions attrs reject role and naming because `actions_label` owns the named
  group atomically, plus aria-roledescription, tabindex, contenteditable,
  aria-hidden/live/atomic;
  and
- actions/panel maps supplied without their destination raise.

Targeted unrelated Alpine bindings, native events, classes, styles, consumer
data attributes, and nonowned ARIA relationships remain allowed. Title's
noninteractive content rule and action/panel content models are author
contracts backed by Nu fixtures and public guidance.

## 16. Assets and performance

Accordion contributes component CSS and root/item initializers. One group has
three delegated listeners, one provided client context, and at most one observer
limited to ancestor fieldset disabled attributes and direct child lists. Each
item has one registration effect
and one decorative SVG, but no independent interaction listener, observer,
timer, global store, network fetch, font, or third-party runtime. The chevron
comes from CIcon's existing registered catalog without a nested CIcon component
owner.

Every panel stays in the DOM. This intentionally trades collapsed-tree memory
for native form continuity, source visibility, stable child state, and simple
server morphs. Diagnostic tools record assets plus server render/output at 1,
10, 100, 500, and 1,000 items. A bounded browser diagnostic may compare first
activation and rapid reversal at 10 and 100 items; it is evidence, not a timing
gate. Lazy mount and unmount remain deferred until representative applications
show a material problem and can absorb the form, SEO-source, state, and
assistive-technology contract.

## 17. Acceptance matrix

Checked-in server tests cover the public schemas; single and multiple values;
one-read value snapshots; invalid root configuration; native anatomy and
conditional region semantics; duplicate, stray, spoofed, misplaced, and nested
item boundaries; transparent item producers; copied attrs; representative
reserved aliases; class/style destinations; hostile item text; action-group
placement; and exact package exports.

Focused Chromium tests cover pointer, Enter, Space, programmatic activation,
Arrow Down, Home, disabled skipping, capture-phase consumer listeners,
noncollapsible no-op behavior, panel focus recovery, nested-root isolation,
controlled single/multiple values, CR/LF/NUL client canonicalization, invalid
episodes, native FormData continuity, dynamic fieldset and first-legend
dominance, one coalesced 100-item initialization, intermediate opening geometry,
rapid reversal cleanup, public radius/soft-surface/spacing overrides, narrow
content, print expansion, retained reorder/removal, callback-array isolation,
and removal focus recovery from trigger, action, panel, and nested content.

The Python-owned `accordion.states` route includes every declared variant,
size, mode, indicator position, disabled state, actions, nested group, real Form
content, RTL, nested color scheme, long content, and two scheme-aware brand
adaptations. Shared tooling runs initial/active axe checks and verifies the
collapsed Form control and brand contrast. Public docs discover and initialize
all component-owned previews, exercise composition, controlled expansion,
nesting, customization, and page-wide console cleanliness. Reference schema,
component contract, registration, asset, scaling, exact wheel, Nu HTML, and
visual-candidate tools include the family.

Release qualification still covers the remaining browser matrix without
turning every row into a permanent unit test: complete Arrow Up/End and
`loop=False`; Tab and Shift+Tab order; batched multiple removal and a
no-enabled-survivor update; stale cleanup and repeated initialization; native
validation focus policy; complete AX relationship review; part-selector and
host-layer overrides; light/dark/RTL/zoom/forced-colors/reduced-motion/print
visual review; and target assistive-technology sessions.

Manual release evidence covers VoiceOver, NVDA, and JAWS heading/expanded/panel
relationships; keyboard and touch behavior; real IME/form controls inside
panels; 200/400 percent zoom; forced colors; print; rapid animation on target
browsers; and nested overlays during and after expansion.

## 18. Compatibility classification

Stable public API includes `CAccordion`, `CAccordionItem`, every server/client
input and fallback rule, their slots/data, `onValueChange` arguments and
timing, value canonicalization, public variables/selectors/reflections,
heading/button/panel/actions semantics, always-mounted panels, and documented
composition errors.

Stable behavioral/structural contracts include direct real item roots, one
state owner, native headings/buttons, actions outside headings, no root Tab
stop, mode-dependent value shape, item registration through client context,
nested Accordion only in panels, focus before close, hidden/inert collapsed
content, cancellation of stale animation, non-clipping settled panels, and
complete server content.

Exact default colors, spacing, radii, shadow, type scale, duration, easing, and
chevron path are evolvable design. `.cui-*` classes, `--_cui-*` variables,
private ownership markers, client-context symbol, registration records,
animation organization, and diagnostic text are private.

## 19. Public documentation contract

The page uses a forest field-guide theme throughout. It starts with a rendered
sampler, then teaches basic composition, browser control, single/multiple and
collapse policy, actions outside headings, disabled items, nested groups,
variants/sizes, customization, keyboard/accessibility, forms, and the complete
structured reference.

Planned examples:

| Source module | Reader task | Visible content and states | Controls or interaction | Contract evidence |
|---|---|---|---|---|
| `at_a_glance.py` | recognize Accordion | one field-guide group with canopy, understory, forest floor | open sections | basic anatomy, one-open state, styling |
| `basic_accordion.py` | write the shortest group | two concise habitat items | native trigger interaction | minimal markup and default policy |
| `expansion_modes.py` | choose a state model | single collapsible, single fixed-open, and multiple groups | open/close comparison | value shapes, multiple, collapsible |
| `controlled_value.py` | derive expansion in browser | one controlled species guide with current-value output | external Buttons plus trigger requests | client value, callback, controlled noncommit, release |
| `variants.py` | choose treatment and geometry | outline, soft, separated, and plain groups plus sm, md, and lg groups | direct comparison | variants, sizes, foreground, border, and spacing |
| `actions.py` | keep secondary actions safe | ranger notes with Bookmark/Open map beside headings | keyboard through triggers and actions | action slot/group label, heading purity, Tab order |
| `disabled_items.py` | explain unavailable sections | one group/item disabled while another open item remains | disabled control toggle | root/item disabled and open-state preservation |
| `nested_accordion.py` | organize deeper material | habitat item containing a nested species Accordion | nested interaction | ownership and direct-child CSS isolation |
| `customization.py` | adapt a field guide | two color-scheme/brand treatments and indicator positions | configurator for variant, size, indicator, position | public variables, selectors, client presentation inputs |

Source stays beside the family and out of the wheel. Examples are result-first,
code is collapsed, controls sit outside rendered content, prose is direct, and
every preview produces no console error. The page does not teach invalid
client values in public examples.

## 20. Open decisions and deferred work

No open decision blocks implementation. A disposable server/Chromium lifecycle
proof on 2026-08-08 validated the two-component architecture: the transparent
collector observed the completed item registry after child settlement, an
item-level `$c-props.disabled` expression updated the real item root, and the
item injected and registered with the root client context through slot scope.
Revisit the internal renderer only if production code cannot retain all three
properties without adding public Trigger/Panel ceremony.

Deferred work:

- standalone `CDisclosure` and whether native `details` is the right baseline;
- arbitrary indicator slots or registered icon names after real theming demand;
- horizontal Accordion, max-open policy, deep linking, and URL/hash ownership;
- lazy mount/unmount after application-scale evidence and an explicit form,
  state, source visibility, and accessibility contract;
- automatic native-validation expansion only after controlled-state timing and
  focus behavior are proven across Citry Events; and
- headless disclosure behavior after representative application pages exist.
