# Citry UI Badge specification

**Status (2026-08-08): production implementation, structured API, nine public
examples, quality route, scaling profile, wheel boundary, and focused server
and Chromium evidence are complete. Human visual and assistive-technology
release review remains.**

## 1. Purpose and product bar

`CBadge` presents a short inline status, category, count, or piece of metadata.
It is a static visual label, not an action, filter, selectable Chip, removable
Tag, notification overlay, or live announcer.

Common jobs:

| Job | Shortest template | Support path |
|---|---|---|
| Mark a release as new | `<c-CBadge>New</c-CBadge>` | direct API |
| Show a state | `<c-CBadge intent="success">Ready</c-CBadge>` | direct API; text carries meaning |
| Show a count | `<c-CBadge>12</c-CBadge>` | direct API; caller supplies contextual text or accessible naming on the owner |
| Add an icon | `start` or `end` fill with `CIcon` | slot composition |
| Fit a brand | public variables, selector, `class_`, or `style` | CSS contract |
| Attach a badge to a control corner | ordinary relative/absolute consumer layout | composition; no positioning ownership |
| Make it clickable, selectable, or removable | Button, link, or `CTag` | unsupported by Badge |

Production completeness means concise repeated call sites, useful variants and
sizes, readable light/dark and forced-color output, text-based status meaning,
predictable inline layout, icon slots, public theming, zero JavaScript, and a
strict boundary from interactive Chip/Tag behavior.

## 2. Prior art and complaints

Current source record:

| Product | Version or review date | Surface inspected | Decision supported |
|---|---|---|---|
| Citry UI | workspace reviewed 2026-08-08 | Button, Alert, Icon, theme, Flow, and authoring policy | Reuse intent/variant/size vocabulary, registered Icon composition, stable parts, inherited variables, and server-only rendering. |
| Vuetify | 4.0.7 reviewed 2026-08-08 | current `VBadge` source/API and examples | Treat wrapped-corner notification badges as a real peer job, but keep positioning and visibility out of this first inline Badge boundary. |
| Mantine | 9.2.2 reviewed 2026-08-08 | Badge guide, source, variants, sections, circle/full-width behavior | Adopt inline status presentation, concise sizes, variants, and start/end content. Omit child-dependent width and interactive section behavior. |
| Material UI | 9.0.1 reviewed 2026-08-08 | Badge guide/API, count capping, dot, overlap, visibility, accessibility guidance | Record overlay/count/dot demand. Do not copy a wrapper-positioning component into the inline label boundary. Preserve its guidance that badge meaning belongs in visible or owner context. |
| Chakra UI | 3.35 reviewed 2026-08-08 | Badge usage, variants, sizes, color palettes | Confirm a static inline status primitive with direct content and no behavior. |
| Bootstrap | 5.3 guidance reviewed 2026-08-08 | inline, button-count, positioned, pill, color, and screen-reader guidance | Adopt relative typography, pill option, and explicit warning that isolated counts and color-only meaning are ambiguous. |

Vuetify has greater decision weight than any other single library. Its broad
Badge supports wrapping arbitrary content, overlap positioning, dot/content,
offsets, location, color, borders, and transitions. Citry disposes those jobs:

| Vuetify job | Citry path | Decision |
|---|---|---|
| Inline short label | `CBadge` | direct |
| Visual variants, theme, size | Badge inputs and CSS variables | direct |
| Icon content | `start`/`end` slots | direct |
| Badge over an Avatar or Button | consumer layout with stable Badge selector | composition |
| Dynamic visibility | `hidden`, targeted `x-show`, or conditional server render | composition |
| Dot without visible meaning | explicit text or consumer visually-hidden context | no first-class dot mode |
| Numeric capping and zero suppression | caller formats slot content | no duplicated formatting policy |
| Transition | consumer CSS or future presence foundation | deferred |

The strongest complaint pattern is semantic ambiguity: a lone number or color
can become random text in an accessible name, while a decorative dot carries no
meaning outside visual context. The first Badge therefore always presents
authored content and never claims automatic count, dot, or announcement logic.

## 3. Public composition and anatomy

Shortest composition:

```citry-html
<c-CBadge>Ready</c-CBadge>
```

Stable anatomy:

```html
<span data-citry-ui-part="badge" data-variant="soft" data-intent="neutral" data-size="md" data-shape="rounded">
  <span data-citry-ui-part="start">...</span>
  <span data-citry-ui-part="label">...</span>
  <span data-citry-ui-part="end">...</span>
</span>
```

Only supplied slot wrappers render. The root is always a native `span`; Badge
does not add role, accessible name, focus, event ownership, positioning,
clipping, or a stacking context. The root accepts `class_`, `style`, and
`attrs` directly.

## 4. Server inputs and client inputs

Public aliases:

```python
CBadgeVariant = Literal["soft", "solid", "outline"]
CBadgeIntent = Literal["neutral", "primary", "success", "warn", "danger"]
CBadgeSize = Literal["sm", "md", "lg"]
CBadgeShape = Literal["rounded", "pill"]
```

Server inputs:

| Input | Type | Default | Effect |
|---|---|---:|---|
| `variant` | `CBadgeVariant` | `"soft"` | Selects quiet fill, solid fill, or outline treatment. |
| `intent` | `CBadgeIntent` | `"neutral"` | Selects a visual palette; authored text must still carry meaning. |
| `size` | `CBadgeSize` | `"md"` | Sets compact height, type, padding, icon size, and gap. |
| `shape` | `CBadgeShape` | `"rounded"` | Selects compact rounded or pill geometry. |
| `class_` | `CClassValue | None` | `None` | Adds root classes. |
| `style` | `CStyleValue | None` | `None` | Adds root inline styles. |
| `attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted native, ARIA, data, and targeted Alpine attributes without replacing owned fields. |

Badge has no `$c-props` client inputs. Dynamic text can be authored inside a
slot with ordinary trusted Alpine text binding; dynamic visibility can use
`hidden`, targeted `x-show`, or a server rerender. Adding client inputs would
duplicate those native composition paths without creating component-owned
state.

## 5. State model

Badge owns no mutable state. Variant, intent, size, and shape are immutable
server configuration for one render. Reflected attributes expose the selected
configuration to styling and inspection. A correlated server rerender replaces
configuration through normal Citry ownership.

Status text changing in the browser does not make Badge a live region. Apps
that need announcements own a separate persistent `CAlert`/status region and
update it deliberately.

## 6. Slots and slot data

| Slot | Required | Data | Contract |
|---|---:|---|---|
| `default` | yes | `{}` (`CBadgeDefaultSlotData`) | Short visible label or count. |
| `start` | no | `{}` (`CBadgeStartSlotData`) | Leading icon or short decorative content. |
| `end` | no | `{}` (`CBadgeEndSlotData`) | Trailing icon or short decorative content. |

`default` must be supplied. All three slots accept phrasing content only. Do
not place Buttons, links, inputs, labels, or other interactive/labelable
content inside Badge. Use a Button or link as the owner and place Badge inside
it instead.

## 7. Callbacks, native events, and methods

Component callbacks: none. Public methods: none. Badge emits no custom events
and installs no listeners. Native event attributes in `attrs` behave on the
root span but do not make it a supported control.

## 8. Semantics, keyboard, focus, and assistive technology

The native span remains neutral and unfocusable. Badge adds no ARIA role.
Visible status words are read in document order. Counts need surrounding
context, such as “Inbox 4,” or an owner accessible name such as “Inbox, 4
unread messages.” Color must never be the only status carrier.

The component rejects root role, tabindex, contenteditable, `aria-hidden`,
child-replacing directives, and dynamic aliases for those fields. These would
create false interaction, remove visible text from the accessibility tree, or
replace owned anatomy. Apps that need decorative duplication should hide a
larger redundant wrapper with a reviewed accessible-name strategy rather than
turning Badge into invisible focus-adjacent text.

## 9. Native forms and validation

Badge is not a control, label, form-associated element, validation message, or
successful form participant. It can appear next to form text, but it must not
replace `CField` error relationships or `CAlert` feedback semantics.

## 10. Styling and theme contract

Variants:

- `soft`: quiet tinted background, transparent border;
- `solid`: strong intent background and contrast-checked foreground; and
- `outline`: transparent background with intent border and foreground.

Sizes `sm`, `md`, and `lg` change compact type and spacing. Shape changes only
radius. Public CSS variables:

| Variable | Purpose |
|---|---|
| `--cui-badge-background` | root fill |
| `--cui-badge-foreground` | text and icon color |
| `--cui-badge-border-color` | root border |
| `--cui-badge-radius` | root radius |
| `--cui-badge-min-height` | minimum block size |
| `--cui-badge-padding-inline` | inline padding |
| `--cui-badge-gap` | slot gap |
| `--cui-badge-font-size` | label size |
| `--cui-badge-font-weight` | label weight |

Stable parts: `badge`, `start`, `label`, `end`. Private `.cui-*` classes and
`--_cui-*` variables remain implementation details. Unlayered consumer CSS
loaded before or after the component layer can override defaults.

## 11. Environmental behavior

Badge follows nested `color-scheme` through `light-dark()` and system colors.
Forced colors preserves a visible border and text while removing nonessential
palette claims. Print uses a transparent background, visible border, and
readable text. Logical padding and slot order support LTR/RTL. Long authored
labels wrap instead of forcing page overflow; authors should still keep badges
short.

## 12. Overlay and layering behavior

Badge owns no position, inset, transform, z-index, overflow, top layer, portal,
or collision logic. A corner badge is ordinary consumer composition with a
positioned owner and the stable `[data-citry-ui-part="badge"]` selector. This
keeps Badge usable inline and avoids silently changing a control's containing
block or stacking context.

## 13. Collections, async data, and identity

Badge is one static item. It has no collection, key, capping, zero-suppression,
loading, or async policy. Callers format count text before composition and use
ordinary Citry keys on repeated owners. Frequently updating counts should use
text binding inside the slot or server morphing, not a Badge-owned store.

## 14. Server render, morph, and cleanup

Server output is complete and usable without JavaScript. There is no init,
cleanup, timer, observer, listener, or retained handoff. A correlated rerender
uses Citry's normal root ownership and re-renders only supplied wrappers.

## 15. Security and content trust

Slot content uses normal Citry escaping. Direct enum strings are converted to
exact plain strings before validation. `attrs` is copied before validation and
is the explicit trusted attribute boundary.

Badge rejects case-insensitive owned part/configuration attributes, Citry and
Events runtime namespaces, whole-object binding, structural/child-replacing
directives, root role/focus/editability/hiding fields, and dynamic aliases of
all owned fields. Targeted unrelated bindings, `x-data`, `x-init`, `x-effect`,
`x-show`, native listeners, and nonconflicting native/data attributes remain
allowed.

## 16. Assets and performance

Badge adds one CSS asset and zero JavaScript, icons, fonts, listeners,
observers, timers, or per-instance data. Each instance renders one root plus
only the slot wrappers it uses. Diagnostic scaling records 1, 10, 100, 500,
and 1,000 instances without a timing gate.

## 17. Acceptance matrix

Checked-in focused evidence must cover:

- valid and invalid variants, intents, sizes, shapes, and attrs;
- required default fill, optional wrapper omission, class/style merging, and
  hostile attribute rejection;
- exact root and slot anatomy with no empty optional wrappers;
- every variant, intent, size, and shape computed surface;
- visible text and count semantics without role/focus/event ownership;
- public variable and selector overrides;
- nested schemes, two brand adaptations, narrow long text, LTR/RTL, forced
  colors, and print;
- zero JavaScript, exports, schema API, previews, quality route, scaling, and
  exact wheel contents.

Manual release evidence covers visual balance beside body text, headings,
Buttons, and Icons; real screen-reader phrasing for counts; and approved
light/dark palette contrast. Automation does not claim aesthetic approval.

## 18. Compatibility classification

Stable: `CBadge`, server inputs, aliases, slots/data, CSS variables, selectors,
reflected attributes, zero-JavaScript behavior, and validation failures.

Behavioral: one neutral span root, supplied wrappers only, authored text as the
meaning carrier, no interaction, and no positioning ownership.

Evolvable: exact fallback colors and spacing lengths. Private: `.cui-*`,
`--_cui-*`, validation helper organization, and internal class names.

## 19. Public documentation contract

The page uses a geology/mineral-collection theme and teaches:

| Preview | Reader task |
|---|---|
| `at_a_glance.py` | recognize inline status, category, and count badges |
| `basic_badges.py` | compose the shortest template and Python forms |
| `intents.py` | keep textual meaning across palettes |
| `variants.py` | choose soft, solid, or outline emphasis |
| `sizes_and_shapes.py` | compare repeated compact geometry |
| `icons.py` | compose registered start/end icons |
| `counts_and_context.py` | give counts understandable owner context |
| `positioning.py` | build a corner badge with consumer layout |
| `customization.py` | apply two brand treatments and public selectors |

The API reference follows from `api.yml`; the conceptual guide contains no
duplicated manual reference tables.

## 20. Open decisions and deferred work

Implementation blockers: none.

Deferred: automatic count capping, show-zero policy, dot-only mode, reactive
client configuration, arbitrary palette names, gradient, full-width, corner
location/overlap, transitions, removable content, selection, and Chip/Tag.

Falsifier for the inline-only boundary: if representative applications show
that the dominant Badge job is attached overlay positioning and every call site
repeats the same safe owner geometry, research a separate overlay composition
or extend Badge after proving it does not compromise inline semantics.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
