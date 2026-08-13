# Citry UI Card specification

**Status (2026-08-08): production pass complete. Research, design and
implementation review gates passed; runtime, structured reference, nine public
examples, focused evidence, and exact wheel qualification are checked in.**
This specification advances one styled
`CCard`. Generic Surface stays private, and Card does not become an interactive
link or Button.

## 1. Purpose and product bar

`CCard` presents content and actions about one subject as a visually contained
unit. It supplies a styled root plus optional media, header, body, footer, and
action anatomy. It works in server-only output, supports native controls and
overlays outside its clipped media region, and follows the surrounding color
scheme.

Common jobs and their shortest supported forms:

| Job | Shortest template | Shortest Python composition | Support path |
|---|---|---|---|
| Contain one subject | `<c-CCard>Details</c-CCard>` | `CCard(slots={"default": "Details"})` | direct API; default body is optional |
| Add a heading | `<c-fill name="header"><h2>Fern chair</h2></c-fill>` | `slots={"header": "..."}` | slot; caller owns heading rank |
| Add a header action | `<c-fill name="header_actions"><c-CButton ... /></c-fill>` | `slots={"header_actions": action}` | slot beside the header content |
| Add media | `<c-fill name="media"><img ... /></c-fill>` | `slots={"media": image}` | slot; caller owns media semantics |
| Add actions | `<c-fill name="actions"><c-CButton>Buy</c-CButton></c-fill>` | `slots={"actions": action}` | slot and composition |
| Add footer metadata | `<c-fill name="footer">Updated today</c-fill>` | `slots={"footer": "Updated today"}` | slot beside footer actions |
| Change visual emphasis | `<c-CCard variant="outline">...</c-CCard>` | `CCard(variant="outline", ...)` | direct API |
| Change spacing | `<c-CCard size="sm">...</c-CCard>` | `CCard(size="sm", ...)` | direct API |
| Use a list item or neutral container | `<c-CCard tag="li">...</c-CCard>` | `CCard(tag="li", ...)` | direct API |
| Make content responsive or horizontal | `class_`, `style`, or public selectors | same | unlayered consumer CSS, correctly ordered named layers, or inline style |
| Make one action cover a Card | unsupported | unsupported | deferred separate contract; do not stretch a nested link across Card |
| Put menus, Combobox, or Dialog triggers inside | ordinary nested components | same | composition; Card does not clip overflow |
| Label an action cluster | `c-actions_attrs="{'role': 'group', 'aria-label': 'Chair actions'}"` | `CCard(actions_attrs={...}, ...)` | direct wrapper attrs without an extra flex item |
| Attach per-section classes, data, or Alpine bindings | `c-body_attrs="{...}"` and related inputs | `CCard(body_attrs={...}, ...)` | six explicit attrs destinations |

Production completeness means a useful static render, concise repeated use,
semantic-root choice, useful optional anatomy, long-content and narrow
layout behavior, light/dark and forced-colors support, stable public theme
hooks, no overlay clipping or stacking context, and no client asset.

Non-goals: generic Surface, dashboard layout, masonry, media loading, entire-
Card navigation, selection, hover state, disabled state, drag and drop,
expansion, remote content, or a headless variant. Use ordinary HTML when a
styled subject container adds no value.

## 2. Prior art and complaints

Current source record:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI | workspace reviewed 2026-08-08 | current theme, Button, Icon, Dialog, Combobox, Table, component policy, inventory, and local prior-art dossier | Reuse concise sizes, direct root styling, public variables/selectors, no-JavaScript rendering, and non-clipping nested overlays. |
| Vuetify | 4.1.8 reviewed 2026-08-08 | [VCard source](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VCard/VCard.tsx), [VCard CSS](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VCard/VCard.sass), and API | Adopt a styled contained subject, variants, compact configuration, and named anatomy. Reject root click inference and opaque heading generation. |
| Material UI | 9.3.1 reviewed 2026-08-08 | [Card guide](https://mui.com/material-ui/react-card/), [Card source](https://github.com/mui/material-ui/blob/v9.3.1/packages/mui-material/src/Card/Card.js), and CardHeader/CardContent/CardActions/CardMedia sources | Preserve separate content jobs while avoiding six public wrapper components. Keep interactive ActionArea separate from the static Card job. |
| Chakra UI | 3.36.1 reviewed 2026-08-08 | [Card guide](https://chakra-ui.com/docs/components/card) and [Card source](https://github.com/chakra-ui/chakra-ui/blob/%40chakra-ui%2Freact%403.36.1/packages/react/src/components/card/card.tsx) | Adopt `sm`/`md`/`lg`, elevated/outline/subtle vocabulary, and stable anatomy. Let callers choose heading elements rather than imposing `h3`. |
| Mantine | 9.5.1 source and 9.1.1 Section fix reviewed 2026-08-08 | [Card guide](https://mantine.dev/core/card/), [Card source](https://github.com/mantinedev/mantine/blob/9.5.1/packages/%40mantine/core/src/components/Card/Card.tsx), [Card CSS](https://github.com/mantinedev/mantine/blob/9.5.1/packages/%40mantine/core/src/components/Card/Card.module.css), [9.5.1 release](https://github.com/mantinedev/mantine/releases/tag/9.5.1), and [9.1.1 release](https://github.com/mantinedev/mantine/releases/tag/9.1.1) | Its neutral `div` default, orientation, Section styling, and SSR child-discovery failure are useful pressure. Adopt the neutral default and explicit slots; keep horizontal layout as a documented CSS recipe until one responsive contract proves durable. |
| Bootstrap | 5.3.8 reviewed 2026-08-08 | [Card guide](https://getbootstrap.com/docs/5.3/components/card/) and [5.3.8 release](https://blog.getbootstrap.com/2025/08/14/bootstrap-5-3-8/) | Confirm header/body/footer/media composition, CSS-driven sizing and horizontal composition. Reject Card-wide navigation inference. |
| Web Awesome | 3.11 reviewed 2026-08-08 | [Card guide, slots, properties, parts, and variables](https://webawesome.com/docs/components/card/) | Confirm optional default content, explicit header/footer actions, SSR anatomy flags, and horizontal orientation pressure. Adopt header/footer action slots; defer orientation because its own horizontal anatomy differs from vertical and omits header/footer. |
| HTML | living standard updated 2026-07-20 and reviewed 2026-08-08 | [`article`](https://html.spec.whatwg.org/multipage/sections.html#the-article-element), [`section`](https://html.spec.whatwg.org/multipage/sections.html#the-section-element), and interactive-content constraints | Default to a neutral `div`; callers opt into `article` or `section` when their content satisfies those semantics. Never make the root an anchor around arbitrary controls. |

Material complaint disposition:

| Report | Status | Citry consequence |
|---|---|---|
| [Vuetify #17628](https://github.com/vuetifyjs/vuetify/issues/17628), VCard overflow and `z-index: 0` create clipping and stacking surprises | closed as not planned 2023-06-28 | Do not set root `overflow: hidden`, `z-index`, transform, containment, or isolation. Clip only the owned media wrapper. |
| [MUI #44201](https://github.com/mui/material-ui/issues/44201), nested Grid did not fill CardActions after migration | closed as expected behavior 2024-11-04 | Make actions flex and wrapping explicit; document `--cui-card-actions-justify` and allow caller CSS instead of inferring descendant width. |
| [Mantine #8846](https://github.com/mantinedev/mantine/issues/8846), Card.Section recognition failed under React server-component SSR | fixed in 9.1.1 | Use named Citry slots and render flags, not runtime child-type recognition or cloning. |

Patterns adopted: a styled subject container, concise variants and sizes,
fixed optional anatomy, semantic roots from a small allowlist, caller-owned
headings/media, and CSS-first layout customization. Rejected: click
inference, root overflow clipping, root stacking contexts, title strings that
choose a heading rank, arbitrary component polymorphism, loader state, and
public subcomponents that only wrap one slot.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| title, subtitle, prepend, append, avatars, icons | composition | `header` slot with ordinary HTML and `CIcon` | caller owns semantic structure and heading rank |
| text prop and text slot | direct API | optional default body slot | adopt the job without a string shortcut |
| image prop and image slot | direct API | optional `media` slot | adopt slot; image loading and alt text stay native |
| item slot | direct API | `header` slot | simplify one level |
| prepend/append/header actions | direct API | `header` and `header_actions` slots | preserve common header layout without choosing title semantics |
| actions slot | direct API | `actions` slot in the footer row | adopt |
| default slot | direct API | optional default body slot | adopt with an owned body wrapper only when supplied |
| loader/loading | separate component | future Progress or consumer composition | omit from static Card |
| href, to, link, ripple, click inference | native composition or later component | link/Button inside Card | reject root interaction |
| disabled | owned by nested controls | native controls | reject Card-wide disabled state |
| hover | CSS | public selector and caller class | no first-class state |
| variant, flat, border, elevation | direct API and CSS | `variant`, public variables | consolidate as elevated/outline/subtle |
| density | direct API | `size` | use suite-wide `sm`/`md`/`lg` |
| color and theme | CSS | currentColor, color-scheme, variables | no Card color vocabulary |
| dimensions, position, location | CSS | `class_`, `style`, `attrs` | consumer CSS subject to the documented cascade-layer order, or inline style |
| rounded | CSS | `--cui-card-radius` | one public variable |
| tag | direct API | constrained `tag` | adopt safe semantic roots |
| native events | native listeners | Alpine `@...` through root attrs | pass through; Card emits none |
| methods | none | none | omit |

Web Awesome disposition:

| Web Awesome surface | Citry support path | Citry surface | Decision |
|---|---|---|---|
| default, media, header, footer | direct API | slots with the same jobs | adopt as optional anatomy |
| header-actions, footer-actions | direct API | `header_actions` and `actions` | adopt because action alignment is common and should not require consumer layout CSS |
| horizontal-only actions | composition | footer `actions` and responsive public-selector CSS | one action destination works in every layout |
| appearance | direct API | `variant` | consolidate to `elevated`, `outline`, and `subtle` |
| orientation | public CSS | class plus stable part selectors | defer a first-class input until one horizontal anatomy works with every optional section and responsive change |
| SSR presence flags | internal implementation | slot-presence render flags | no public flags because the server already knows supplied slots |
| CSS parts | direct API | documented `data-citry-ui-part` selectors | adopt equivalent stable customization targets |
| one spacing variable | direct API | padding, section-gap, and action-gap variables | split the high-value layout concerns |

## 3. Public composition and anatomy

Smallest template:

```citry-html
<c-CCard>
  A handwoven reading chair for quiet corners.
</c-CCard>
```

Full anatomy:

```citry-html
<c-CCard variant="outline">
  <c-fill name="media">
    <img src="/chair.webp" alt="Oak reading chair" />
  </c-fill>
  <c-fill name="header">
    <h2>Oak reading chair</h2>
    <p>Handwoven rush seat</p>
  </c-fill>
  <c-fill name="header_actions">
    <c-CButton variant="ghost" c-attrs="{'aria-label': 'Save chair'}">
      <c-CIcon name="heart" />
    </c-CButton>
  </c-fill>
  <c-fill name="default">
    Built for a sunny reading corner.
  </c-fill>
  <c-fill name="footer">
    Ships in three weeks
  </c-fill>
  <c-fill name="actions">
    <c-CButton>Add to room</c-CButton>
  </c-fill>
</c-CCard>
```

Python composition:

```python
from citry_ui import CCard

chair = CCard(
    variant="outline",
    slots={
        "header": "Oak reading chair",
        "default": "Built for a sunny reading corner.",
    },
)
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CCard` | allowed `tag`, default `<div>` | root gets `attrs`, `class_`, `style` | at least one supported slot; zero or one of every slot |

The stable order is media, header row, body, then footer row. Every owned
wrapper is a neutral `<div>`:

```text
CCard (selected semantic root)
├── media div                         when media is supplied
├── header div                        when header or header_actions is supplied
│   ├── private content div           when header is supplied
│   └── header-actions div            when header_actions is supplied
├── body div                          when default is supplied
└── footer div                        when footer or actions is supplied
    ├── private content div           when footer is supplied
    └── actions div                   when actions is supplied
```

The header and footer rows provide alignment only. They are not HTML
`header` or `footer` landmarks. Consumers put headings, metadata, semantic
containers, links, and controls inside the corresponding slots. A supplied
empty fill counts as supplied and renders its wrapper. Ordinary Citry slot
schema validation rejects unknown or duplicate fills. `CCard` additionally
raises `ValueError` when no supported slot is supplied.

The two content wrappers in the diagram are private grid helpers, have no part
marker or attrs destination, and may change without compatibility impact. The
six public part maps cover the four direct root sections plus the two action
groups. Action-group maps are separate because a consumer wrapper would become
one flex item and prevent the Card-owned direct-button wrapping layout.

`div` is neutral and therefore the safe default. `article`, `section`, and
`li` are opt-ins when the surrounding document and Card content satisfy those
native semantics. Consumers own heading structure and accessible naming. No
part subcomponent is public because named slots retain the same composition
and customization jobs with less markup.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `tag` | `CCardTag` | `"div"` | structural server-only | One of `div`, `article`, `section`, or `li`; selects the native root. |
| `variant` | `CCardVariant` | `"elevated"` | structural server-only | One of `elevated`, `outline`, or `subtle`; selects the visual surface treatment. |
| `size` | `CCardSize` | `"md"` | structural server-only | One of `sm`, `md`, or `lg`; selects section padding and action gap fallbacks. |
| `class_` | `CClassValue | None` | `None` | structural server-only | Adds structured root classes and merges them with `attrs`. |
| `style` | `CStyleValue | None` | `None` | structural server-only | Adds structured root styles and merges them with `attrs`. |
| `attrs` | `Mapping[str, object] | None` | `None` | structural server-only | Adds allowed native, ARIA, Alpine, and data attributes but cannot replace public reflected attributes or the part marker. |
| `media_attrs` | `Mapping[str, object] | None` | `None` | structural server-only | Adds native, ARIA, data, and trusted Alpine attributes to the media wrapper; cannot replace its part marker. |
| `header_attrs` | `Mapping[str, object] | None` | `None` | structural server-only | Adds native, ARIA, data, and trusted Alpine attributes to the header row; cannot replace its part marker. |
| `header_actions_attrs` | `Mapping[str, object] | None` | `None` | structural server-only | Adds native, ARIA, data, and trusted Alpine attributes to the header-actions wrapper; cannot replace its part marker. |
| `body_attrs` | `Mapping[str, object] | None` | `None` | structural server-only | Adds native, ARIA, data, and trusted Alpine attributes to the body wrapper; cannot replace its part marker. |
| `footer_attrs` | `Mapping[str, object] | None` | `None` | structural server-only | Adds native, ARIA, data, and trusted Alpine attributes to the footer row; cannot replace its part marker. |
| `actions_attrs` | `Mapping[str, object] | None` | `None` | structural server-only | Adds native, ARIA, data, and trusted Alpine attributes to the footer-actions wrapper; cannot replace its part marker. |

There are no client inputs. Card has no browser-owned state. Server replacement
changes structure or presentation without a Card initializer.

## 5. State model

Card has no interactive or controlled state. The render state is the product of
valid `tag`, `variant`, `size`, and optional-slot presence. Invalid enum values
raise `ValueError`; non-string enum values raise `TypeError`; invalid attrs use
the shared attribute validation errors. Supplying no slot raises `ValueError`.
Supplying a nonempty part-attrs mapping for an absent destination also raises
`ValueError`. `header_attrs` has a destination when `header` or
`header_actions` exists; `footer_attrs` has one when `footer` or `actions`
exists. The other four maps require their same-named slot. `None` and empty
mappings normalize harmlessly when the destination is absent.
Loading, disabled, selected,
expanded, empty, and error belong to nested content or another component.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CCard` | `media` | no | zero or one | `CCardMediaSlotData {}` | wrapper omitted |
| `CCard` | `header` | no | zero or one | `CCardHeaderSlotData {}` | wrapper omitted |
| `CCard` | `header_actions` | no | zero or one | `CCardHeaderActionsSlotData {}` | wrapper omitted |
| `CCard` | `default` | no | zero or one | `CCardDefaultSlotData {}` | wrapper omitted |
| `CCard` | `footer` | no | zero or one | `CCardFooterSlotData {}` | wrapper omitted |
| `CCard` | `actions` | no | zero or one | `CCardActionsSlotData {}` | wrapper omitted |

Slot data is static and empty. Slots inherit ordinary Citry fill scope. The
header and footer action slots align beside their corresponding content; they
do not imply a native event or change the root semantics. Dynamic slot names
and whole-root replacement are unsupported. Unknown, duplicate, and misplaced
fills use ordinary Citry errors. At least one slot must be supplied, but no
specific slot is required. A nonempty part-attrs mapping cannot silently wait
for a missing slot: it follows the destination-presence errors in section 5.

## 7. Callbacks, native events, and methods

Card emits no component callback or custom event and exposes no method. Listen
to native events on controls, links, or other content inside slots. Root native
listeners passed through `attrs` remain ordinary Alpine listeners; they do not
turn Card into an accessible action.

## 8. Semantics, keyboard, focus, and assistive technology

Card adds no role, accessible name, keyboard handling, focus stop, or live
announcement. Its selected native root supplies document semantics. Opt-in
`article` and `section` roots should normally have an identifying heading or
accessible name. The component does not guess heading rank.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| Static Card | none | native root and content semantics | Card is not focusable | no |
| Nested link or control | native content | native semantics and events | native element owns focus | native behavior only |

Do not make the root click-only with `@click`. A Card containing multiple
interactive descendants cannot also be one enclosing link or Button. Visible
focus treatment belongs to the actual nested interactive element. A
whole-Card action is not part of the initial contract; do not stretch an
absolutely positioned link over other content.

## 9. Native forms and validation

Card is not a form participant. Native controls and `CForm` may appear inside
its slots and retain their own name, value, validation, submission, reset,
disabled, read-only, and Events behavior. Card does not disable or intercept
them.

## 10. Styling and theme contract

Variants and sizes form a complete 3 by 3 matrix. `elevated` uses `Canvas`
with a shadow, `outline` uses `Canvas` with a visible border and no shadow,
and `subtle` mixes 5 percent `CanvasText` into `Canvas` without elevation.
Size affects owned section padding and action gaps, not consumer typography.

| Preset | Background fallback | Border fallback | Shadow fallback |
|---|---|---|---|
| `elevated` | `Canvas` | `transparent` | `0 0.5rem 1.5rem color-mix(in srgb, CanvasText 14%, transparent)` |
| `outline` | `Canvas` | `color-mix(in srgb, CanvasText 24%, transparent)` | `none` |
| `subtle` | `color-mix(in srgb, CanvasText 5%, Canvas)` | `transparent` | `none` |

| Size | Section padding | Header/footer gap | Action gap |
|---|---|---|---|
| `sm` | `0.75rem` | `0.5rem` | `0.375rem` |
| `md` | `1rem` | `0.75rem` | `0.5rem` |
| `lg` | `1.25rem` | `1rem` | `0.625rem` |

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-card-background` | color | root background | variant fallback from the preset matrix |
| `--cui-card-foreground` | color | inherited content color | `CanvasText` |
| `--cui-card-border-color` | color | outline border | variant fallback from the preset matrix |
| `--cui-card-shadow` | shadow | elevated shadow | variant-derived shadow |
| `--cui-card-radius` | length | root and edge-media rounding | `0.75rem` |
| `--cui-card-padding` | length | header, body, and footer row padding | size-derived length |
| `--cui-card-section-gap` | length | space between header/footer content and actions | size-derived length |
| `--cui-card-actions-gap` | length | action spacing | size-derived length |
| `--cui-card-actions-justify` | CSS `justify-content` | action alignment | `flex-start` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="card"]` | semantic root and attrs destination | all | one per Card |
| `[data-citry-ui-part="media"]` | media clipping and layout wrapper | media fill present | direct root child before content rows |
| `[data-citry-ui-part="header"]` | neutral header layout row | header or header-actions fill present | direct root child before body |
| `[data-citry-ui-part="header-actions"]` | header controls wrapper | header-actions fill present | direct child of header row after content |
| `[data-citry-ui-part="body"]` | main content wrapper | default fill present | direct root child between header and footer |
| `[data-citry-ui-part="footer"]` | neutral footer layout row | footer or actions fill present | last direct root child |
| `[data-citry-ui-part="actions"]` | flex footer-controls wrapper | actions fill present | direct child of footer row after content |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-variant` | `elevated`, `outline`, `subtle` | selected surface treatment |
| `data-size` | `sm`, `md`, `lg` | selected spacing preset |

All variables are inherited inputs resolved through private variables in the
`citry-ui.theme` layer. Public selectors use direct-child CSS where needed so
nested Cards do not inherit structural layout rules. `.cui-*` classes and
`--_cui-*` variables remain private. Header and footer rows use one
`minmax(0, 1fr)` track when only content or only actions are present, and
`minmax(0, 1fr) auto` when both are present. A missing peer does not reserve an
empty track or gap. An actions-only group stretches across the row and starts
at the inline start by default; `--cui-card-actions-justify` controls its inner
flex alignment.

Media edge behavior is deliberately minimal. The media wrapper clips its own
contents to the Card's block-start corners, and to all four corners when media
is the sole section. Direct `img`, `picture`, and `video` children render as
blocks with `max-inline-size: 100%`; Card does not force an aspect ratio, block
size, `object-fit`, or crop. Multiple media nodes are allowed and remain
consumer-laid-out. Put popups and controls whose visual content must escape the
Card in header, body, or footer slots, not media.

## 11. Environmental behavior

System colors and `color-mix()` follow nested `color-scheme`. Logical borders,
padding, and action flow support RTL. Card has no motion, hover dependency, or
coarse-pointer behavior. Long words wrap; content and actions wrap under narrow
widths; 200% and 400% zoom must not create page overflow from the component's
own CSS. In forced colors every variant receives a one-pixel `CanvasText`
boundary and no shadow. Print removes the decorative shadow and keeps a
`currentColor` border. Card authors no visible text, so locale work applies
only to consumer content.

## 12. Overlay and layering behavior

Card never creates or controls an overlay. Its root and the header, body, and
footer rows deliberately do not set clipping overflow, `z-index`, `isolation`,
`contain`, or transform. The root remains `position: static`; Card does not
establish an overlay containing block.
Nested Combobox, menu, popover, and Dialog triggers in those regions can use
their ordinary overlay strategy without Card clipping or a new stacking
context. The media wrapper is the explicit exception: it clips its contents to
the Card edge and is not a supported home for an escaping popup.

## 13. Collections, async data, and identity

Card owns no collection, key, selection, async request, loading, empty, retry,
or error behavior. Repeated Cards use ordinary Citry loop keys and surrounding
layout. Consumer content owns its data and request lifecycle.

## 14. Server render, morph, and cleanup

The complete component renders without JavaScript. It registers no listeners,
observers, timers, client data, or cleanup. Server replacement may change
inputs and slot presence atomically. Focus and edits inside stable nested
controls follow the nested component and Citry morph contracts; Card adds no
client owner that could interfere.

## 15. Security and content trust

Slot text and values use ordinary Citry escaping. Media URLs, image alt text,
links, and remote content belong to consumer elements and retain their native
trust requirements. Every attrs mapping is copied before rendering, requires
string keys, rejects its owned `data-citry-ui-part`, and rejects reserved Citry
ownership attributes. Root attrs also reject owned `data-variant` and
`data-size`. Alpine listeners and other executable attrs remain an intentional
trusted-code surface on root and part mappings. Card accepts no raw HTML, URL,
generated ID, or remote data input of its own.

## 16. Assets and performance

Card adds one static CSS asset and no JavaScript, icon, font, listener,
observer, request, or shared client dependency. CSS is emitted once per
registered concrete class, not per instance. The diagnostic harness records
1, 10, 100, and 1,000 Card instances; exact timings remain diagnostic until a
stable hosted baseline exists. Asset evidence records Card CSS raw, gzip, and
Brotli bytes. The installed-wheel check confirms the runtime module and CSS
source ship while family docs, snippets, tests, and reports do not.

## 17. Acceptance matrix

Checked-in server tests cover schema and defaults; valid representative enum
values and every invalid enum or type path; body-only, header-only,
media-plus-actions, and complete anatomy; no-slot failure; unknown and
duplicate fills; absent-destination attrs errors; attrs destinations and
reserved fields; class/style merging; reflected attributes; ordered wrappers;
hostile text; and zero Card JavaScript. Focused Chromium tests cover neutral
root semantics and non-focusability; anatomy; computed row geometry and
spacing; ancestor and root variable overrides; a public part-selector
override; unlayered class precedence before and after the component CSS; one
dark scoped Card; nested direct-child anatomy; forced-colors and print shadow
removal; computed root/header/body/footer overflow; position and z-index; and
media overflow.

The Card route is registered with axe, Nu HTML, and pairwise screenshot
profiles for light/dark, RTL, narrow, zoom, and forced-colors. Asset,
scaling, and exact-wheel tools include Card. Manual release evidence covers
visual hierarchy, all
variant/size combinations, dense repeated layouts, keyboard and screen-reader
reading order, escaping real overlays from header/body/footer, high contrast,
real Safari/mobile rendering, and the judgment that Card remains useful beyond
ordinary HTML.

## 18. Compatibility classification

1. **Stable public API:** `CCard`, aliases, inputs and defaults, slot names and
   empty data shapes, errors, variables, selectors, and reflected attributes.
2. **Behavioral and structural contract:** allowed semantic roots, ordered
   media/header/body/footer relationships, no root interaction, no root
   clipping or stacking context, no-JavaScript output, and nested-control
   ownership.
3. **Evolvable design:** exact colors, shadows, radii, padding, gaps, and media
   edge details may improve without changing public meaning.
4. **Private implementation:** `.cui-*` classes, private variables, render-flag
   calculation, and incidental whitespace.

Removing or repurposing a tag, variant, size, slot, variable, selector, or
attribute is breaking. Adding a new optional presentation value is compatible
only when existing fallbacks and output do not change.

## 19. Public documentation contract

The page theme is home and living. One coherent room-and-furniture vocabulary
makes surface, media, hierarchy, actions, responsive composition, and theme
customization recognizable without dashboard copy.

| Order and module | Reader task | Rendered content and controls | Contract coverage | Focused browser evidence |
|---|---|---|---|---|
| 1. `at_a_glance.py` | Recognize Card immediately | Three living-space Cards with media, heading, body, footer, and actions | complete anatomy, elevated default, Icon/Button composition | result loads; neutral roots and native controls |
| 2. `basic_card.py` | Write the smallest useful Cards | body-only reading note and header-only material label | optional default/header, at-least-one rule, heading ownership, template/Python forms | wrapper omission and reading order |
| 3. `variants.py` | Choose surface emphasis | the same lamp in elevated, outline, and subtle Cards | every variant and reflected attribute | computed background/border/shadow |
| 4. `sizes.py` | Choose content spacing | compact swatch, ordinary sample, roomy material note | sm/md/lg and long text | computed padding; narrow wrapping |
| 5. `media.py` | Add meaningful media | furniture and textile media with native alt text and edge clipping | media slot, intrinsic sizing, no root clipping | alt names; media clips while root overflow stays visible |
| 6. `actions.py` | Add metadata and controls | save in a header, shipping note and compare/details in a footer | header, header_actions, footer, actions, Button/Icon composition | grid/flex alignment, Tab order, wrapping |
| 7. `nested_content.py` | Put interactive content inside | room chooser Combobox and Dialog trigger inside a Card | form/overlay composition, no clipping or stacking context | popup/dialog visible and keyboard usable |
| 8. `customization.py` | Build responsive branded Cards | linen and studio adaptations, horizontal wide layout, vertical narrow layout, nested light/dark pair | all variables/selectors, class/style, RTL-safe CSS | two brand treatments, responsive switch, computed overrides |
| 9. `semantics.py` | Choose the correct native root | article, list-item, section, and neutral div examples | every `tag`, heading/naming guidance | accessibility tree and no Card focus stop |

No configurator is needed because inputs are server-only and side-by-side
results expose the differences directly. The guide order is glance, smallest
use, anatomy, variants, size, media, footer actions, nested content,
customization, semantics, then generated API reference.

## 20. Open decisions and deferred work

No unresolved decision blocks the initial implementation.

Deferred work:

- a CardAction or whole-Card link contract, only after real pages establish
  click target, nested interactive content, focus ring, naming, and browser
  navigation requirements;
- selectable Cards, drag and drop, expansion, media loading, badges, and
  progress states;
- generic Surface remains private until several components prove one public
  semantic job; and
- horizontal layout remains public-CSS composition unless repeated call sites
  show that one responsive orientation contract is materially clearer.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
