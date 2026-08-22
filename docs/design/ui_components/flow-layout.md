# Citry UI Flow layout specification

**Status (2026-08-08): production implementation, structured API, public
examples, quality route, scaling profile, wheel boundary, and focused server
and Chromium evidence are complete. Human visual and assistive-technology
release review remains.**

## 1. Purpose and product bar

`CCol` and `CRow` arrange direct content in one dimension. Col is a
vertical flex container. Row is a horizontal flex container that wraps by
default. Both provide concise spacing and alignment without activating client
behavior or introducing a responsive breakpoint vocabulary.

Common jobs:

| Job | Shortest template | Python composition | Support path |
|---|---|---|---|
| Space form sections vertically | `<c-CCol>...</c-CCol>` | `CCol(slots={"default": ...})` | direct API |
| Place actions in one row | `<c-CRow><c-CButton>...</c-CButton></c-CRow>` | `CRow(slots={"default": ...})` | direct API |
| Change spacing | `<c-CCol gap="lg">...</c-CCol>` | `CCol(gap="lg", ...)` | direct API |
| Align children | `<c-CRow align="end">...</c-CRow>` | `CRow(align="end", ...)` | direct API |
| Distribute free space | `<c-CRow justify="between">...</c-CRow>` | `CRow(justify="between", ...)` | direct API |
| Keep actions on one line | `<c-CRow c-wrap="False">...</c-CRow>` | `CRow(wrap=False, ...)` | direct API |
| Reverse visual order | `<c-CCol c-reverse="True">...</c-CCol>` | `CCol(reverse=True, ...)` | direct API; DOM and reading order stay unchanged |
| Use list or navigation semantics | `<c-CRow tag="nav">...</c-CRow>` | `CRow(tag="nav", ...)` | direct API; caller owns required content semantics and naming |
| Use an arbitrary gap | `style="--cui-col-gap: 2.25rem"` | structured `style` | public CSS variable |
| Change direction responsively | class or public selector CSS | same | consumer CSS; Flow has no breakpoint inputs |
| Build a two-dimensional layout | `CGrid` and `CGridItem` | same | separate component family |

Production completeness means valid static HTML, zero component JavaScript,
concise frequent inputs, logical LTR/RTL behavior, long-content and narrow
layout safety, semantic-root choice, public gap overrides, and predictable
nested Flow components.

Non-goals: absorbing the separate Grid and Container contracts, masonry,
overlap, absolute positioning, responsive
prop objects, breakpoint names, child cloning, equal-width children,
separators, ordering individual children, animation, observation, or a
headless API.

## 2. Prior art and complaints

Current source record:

| Product or standard | Version or review date | Surface inspected | Decision supported |
|---|---|---|---|
| Citry UI | workspace reviewed 2026-08-08 | theme contract, Card action rows, Tabs list, component policy, inventory, and quality harness | Reuse server-only rendering, `class_`/`style`, inherited variables, stable selectors, and no implicit breakpoint vocabulary. |
| Vuetify | 4.0.7 reviewed 2026-08-08 | [`VRow` source](https://github.com/vuetifyjs/vuetify/blob/v4.0.7/packages/vuetify/src/components/VGrid/VRow.ts), Grid CSS, flex and spacing utilities | Treat utility CSS as a valid capability path. Adopt short alignment and gap values, but do not import Grid columns, density, or breakpoints into one-dimensional Flow. |
| Mantine | 9.2.2 reviewed 2026-08-08 | [Stack](https://mantine.dev/core/stack/) and [Group](https://mantine.dev/core/group/) guides and source links | Adopt distinct vertical and horizontal names, direct flex gap, Group wrapping, and concise align/justify inputs. Reject child-count-dependent grow behavior. |
| Material UI | 9.0.1 reviewed 2026-08-08 | [Stack guide](https://mui.com/material-ui/react-stack/) and [Stack API](https://mui.com/material-ui/api/stack/) | Confirm one root, direction, gap, alignment, and direct-child long-content pressure. Use native flex gap, not child margins or cloning. |
| Chakra UI | 3.35 reviewed 2026-08-08 | [Stack guide](https://chakra-ui.com/docs/components/stack) | Confirm Stack/HStack vocabulary and separator demand. Keep separators in composition or `CDivider` because Flow must not clone or reinterpret children. |
| Web Awesome | 3.2.1 reviewed 2026-08-08 | [layout utilities](https://webawesome.com/docs/layout) | Confirm Stack, cluster/group, gap, alignment, and wrapping can remain CSS-only with no custom-element runtime. |
| Shopify App Home UI | reviewed 2026-08-08 | [Stack](https://shopify.dev/docs/api/app-home-ui-extension/latest/web-components/layout-and-structure/stack) | Confirm a framework-neutral stack can support horizontal and vertical layout while leaving semantics to the root. |
| CSS Flexible Box Layout | reviewed 2026-08-08 | [Flexbox Level 1](https://www.w3.org/TR/css-flexbox-1/) and [Box Alignment Level 3](https://www.w3.org/TR/css-align-3/) | Use native flex layout, `gap`, logical start/end alignment, DOM-order semantics, and direct-item sizing behavior. |

Material limitations disposition:

| Finding | Status | Citry consequence |
|---|---|---|
| MUI Stack historically used child margins and documents margin conflicts | current guide retains the limitation for its non-gap path | Citry always uses native `gap`; it never rewrites child margins. |
| MUI documents `min-width: auto` overflow with no-wrap descendants | current documented limitation | Flow roots and direct element children receive `min-inline-size: 0`; content can still deliberately overflow through its own CSS. |
| Mantine Group grow depends on countable React element children and warns about strings/fragments | current documented limitation | No `grow` input. Callers use child classes, `CGrid`, or ordinary CSS. |
| Vuetify 4 deprecates direct Row alignment props in favor of utility classes | current source | Flow keeps only the frequent one-dimensional inputs; specialized responsive alignment stays in consumer CSS. |

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `VRow` horizontal flex layout | direct API | `CRow` | Adopt the one-dimensional job without Grid column ownership. |
| `gap` | direct API and CSS | `gap`, `--cui-col-gap`, `--cui-row-gap` | Adopt named presets plus arbitrary CSS override. |
| align and justify | direct API | `align`, `justify` | Keep concise logical values; responsive variants stay CSS. |
| align-content | CSS | `class_`, `style`, selector | Omit until multi-line alignment is a repeated job. |
| density, gutters, column count | separate Grid | none | Omit from Flow. |
| breakpoints | consumer media/container-query CSS, or separate `CGrid` | no Flow breakpoint inputs | Keep Flow one-dimensional; `CGrid` owns the suite's fixed responsive grid vocabulary. |
| tag | direct API | constrained `tag` | Adopt common neutral and semantic roots. |
| class and style | direct API | `class_`, `style` | Adopt. |
| flex and spacing utilities | CSS | ordinary consumer CSS | Document as the escape path for specialized layout. |

The family keeps two public components because their shortest call sites
communicate different stable jobs. A single direction-heavy component would
make the common horizontal wrapping case longer and less legible. They share
types, validation, tokens, and one documentation family without sharing a
public generic `CFlow` abstraction.

## 3. Public composition and anatomy

```citry-html
<c-CCol gap="lg">
  <h2>Glaze notes</h2>
  <p>Layer the pale ash glaze over the iron slip.</p>
  <c-CRow>
    <c-CButton>Save notes</c-CButton>
    <c-CButton variant="outline">Discard</c-CButton>
  </c-CRow>
</c-CCol>
```

```python
from citry_ui import CCol, CRow

actions = CRow(
    gap="sm",
    slots={"default": "..."},
)
panel = CCol(
    gap="lg",
    slots={"default": actions},
)
```

| Component | Semantic root | Attribute destination | Relationship |
|---|---|---|---|
| `CCol` | selected `tag`, default `div` | root receives `attrs`, `class_`, and `style` | lays out direct children vertically |
| `CRow` | selected `tag`, default `div` | root receives `attrs`, `class_`, and `style` | lays out direct children horizontally and wraps by default |

Each component renders exactly one root and the supplied default slot. There
are no child wrappers. Supported tags are `div`, `section`, `nav`, `ul`, and
`ol`. Callers own heading requirements, accessible names, and valid list
children for the semantic tags they select.

## 4. Server inputs and client inputs

Shared aliases:

- `CFlowTag = Literal["div", "section", "nav", "ul", "ol"]`
- `CFlowGap = Literal["0", "xs", "sm", "md", "lg", "xl"]`
- `CFlowAlign = Literal["start", "center", "end", "stretch", "baseline"]`
- `CFlowJustify = Literal["start", "center", "end", "between", "around", "evenly"]`

`CCol` inputs:

| Python input | Type | Default | Class | Effect |
|---|---|---|---|---|
| `tag` | `CFlowTag` | `"div"` | structural | Selects the one native root. |
| `gap` | `CFlowGap` | `"md"` | presentation | Selects the vertical flex gap fallback. |
| `align` | `CFlowAlign` | `"stretch"` | presentation | Sets cross-axis item alignment. |
| `justify` | `CFlowJustify` | `"start"` | presentation | Sets main-axis distribution when the root has extra block size. |
| `reverse` | `bool` | `False` | presentation | Uses `column-reverse` without changing DOM order. |
| `class_` | `CClassValue | None` | `None` | root styling | Merges root classes. |
| `style` | `CStyleValue | None` | `None` | root styling | Merges root inline styles. |
| `attrs` | `Mapping[str, object] | None` | `None` | root attributes | Adds native, ARIA, data, and bounded Alpine attributes. |

`CRow` has the same inputs except `gap` defaults to `"sm"`, `align`
defaults to `"center"`, and it adds `wrap: bool = True`.

There are no client inputs. Flow contributes no JavaScript. Browser-owned
layout changes use ordinary classes, inline styles, or targeted Alpine class
and style bindings supplied through `attrs`. The component configuration and
public owned attributes cannot be dynamically rebound.

## 5. State model

Flow has no interaction state, controlled state, disabled state, loading
state, or client lifecycle. Server inputs deterministically select CSS
configuration. Consumer DOM insertion and removal participate in native flex
layout without component bookkeeping.

`reverse=True` changes only visual order. Focus, reading, selection, and form
submission order continue to follow the authored DOM. Documentation must warn
against using reverse to create a semantic order different from the source.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CCol` | `default` | no | zero or one fill | `{}` (`CColDefaultSlotData`) | empty root |
| `CRow` | `default` | no | zero or one fill | `{}` (`CRowDefaultSlotData`) | empty root |

The default slot accepts ordinary flow content and nested components. The
selected root's HTML content model remains the caller's responsibility. Slot
data is static and empty. Unknown named fills raise through Citry's normal slot
validation.

## 7. Callbacks, native events, and methods

Flow defines no callbacks, custom events, or methods. Native events from
descendants bubble normally. Root listeners supplied through `attrs` observe
ordinary browser events and must inspect `event.target`.

## 8. Semantics, keyboard, focus, and assistive technology

The default `div` is neutral. Flow adds no role, name, ARIA state, focus
target, keyboard behavior, or Tab stop. Semantic tags retain their native
meaning. `nav` needs an accessible name when several navigation landmarks
exist; `ul` and `ol` require appropriate list content.

Visual reversal never changes DOM or accessibility-tree order. Alignment and
wrapping never trap or move focus. Forced-colors mode keeps content and native
focus indicators under descendant ownership.

## 9. Native forms and validation

Flow is not a form participant. Native controls inside its slot preserve their
own Form owner, order, successful-control behavior, reset, validation, and
submission. A `CRow` of Buttons does not become a Button group semantic or
state owner.

## 10. Styling and theme contract

Gap presets:

| Name | Current fallback |
|---|---:|
| `0` | `0` |
| `xs` | `0.25rem` |
| `sm` | `0.5rem` |
| `md` | `0.75rem` |
| `lg` | `1rem` |
| `xl` | `1.5rem` |

| Public variable | Type | Purpose | Current default |
|---|---|---|---|
| `--cui-col-gap` | length | Overrides the selected Col gap. | selected `gap` fallback |
| `--cui-row-gap` | length | Overrides the selected Row gap. | selected `gap` fallback |

| Public selector | Element | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="col"]` | Col root | all Col configuration attributes | one native root |
| `[data-citry-ui-part="row"]` | Row root | all Row configuration attributes | one native root |

| Public attribute | Values | Meaning |
|---|---|---|
| `data-gap` | `0`, `xs`, `sm`, `md`, `lg`, `xl` | Selected named gap fallback. |
| `data-align` | `start`, `center`, `end`, `stretch`, `baseline` | Cross-axis alignment. |
| `data-justify` | `start`, `center`, `end`, `between`, `around`, `evenly` | Main-axis distribution. |
| `data-reverse` | present or absent | Visual direction is reversed when present. |
| `data-wrap` | present or absent on Row | Row wrapping is enabled when present. |

Default CSS lives in `citry-ui.theme`, uses `:where()` selectors, and applies
native flexbox directly to the root. Direct element children receive
`min-inline-size: 0`; Flow does not reset margins, widths, flex factors, or
overflow owned by consumer content.

## 11. Environmental behavior

Flow has no authored colors and follows every light, dark, and nested scheme.
It uses logical start/end alignment and native direction-aware row layout.
No animation means reduced motion has no special path. Forced colors and print
preserve the same layout. At narrow widths, Row wraps by default and Col
children can shrink; `wrap=False` deliberately allows the caller to choose
overflow or child shrinking.

Long unbroken descendant content may still overflow when that descendant owns
`white-space`, a fixed width, or min-content behavior. Flow removes the common
flex-item `min-inline-size:auto` barrier without overriding deliberate child
styles.

Library-authored visible strings: none.

## 12. Overlay and layering behavior

Flow creates no overlay and no stacking context. It sets no `overflow`,
`position`, `z-index`, `transform`, `contain`, or `isolation`, so descendant
menus and overlays retain their own layout and clipping contracts.

## 13. Collections, async data, and identity

Flow does not treat children as a collection. It assigns no keys, reads no
child identity, and owns no selection. Async insertion and removal are normal
DOM changes handled by flex layout. Equal growth, sorting, and reordering stay
with application CSS or future collection components.

## 14. Server render, morph, and cleanup

Server output is complete and useful without JavaScript. A morph may replace
configuration attributes or slot content; CSS recomputes without an
initializer, listener, observer, timer, or cleanup callback. Retained native
controls preserve behavior according to Citry's normal morph contract.

## 15. Security and content trust

Slot text uses normal Citry escaping. Flow never accepts HTML strings, URLs,
or executable data as direct inputs. `attrs` is the established trusted
attribute boundary, copied before validation.

Flow rejects:

- its owned part and configuration attributes, case-insensitively;
- dynamic bindings targeting owned attributes;
- Citry and Events runtime namespaces;
- whole-object `x-bind`; and
- structural or child-replacing Alpine directives such as `x-if`, `x-for`,
  `x-teleport`, `x-ignore`, `x-html`, `x-text`, `x-model`, and `x-modelable`.

Targeted unrelated bindings, `x-data`, `x-init`, `x-effect`, native listeners,
ARIA, and ordinary native attributes remain allowed. Callers choosing semantic
tags own their content-model and naming correctness.

## 16. Assets and performance

The family adds one shared CSS asset and no JavaScript, icons, fonts,
listeners, observers, timers, or per-instance data. Each instance renders one
root around its slot. Asset tooling records raw, gzip, and Brotli bytes;
diagnostic scaling records 1, 10, 100, 500, and 1,000 roots without a timing
gate.

## 17. Acceptance matrix

Checked-in focused evidence must cover:

- every valid and invalid enum and Boolean input;
- root tag, default slot, empty root, class/style merge, attrs copying, and
  trust-boundary rejection;
- exact Col and Row anatomy with zero child wrappers;
- gap, alignment, justification, reverse, and Row wrap computed styles;
- ancestor and root public variable overrides and a public selector override;
- direct-child min-inline-size behavior, nested Flow, narrow wrapping, LTR,
  RTL, print, and forced colors;
- zero family JavaScript and exact package exports;
- schema-valid structured API data, public previews, quality scenario, asset
  accounting, scaling inclusion, and wheel allowlist.

Manual release evidence covers visual rhythm in representative pages,
keyboard order under visual reversal, zoom and long-content inspection, and
screen-reader order for semantic roots. Automated checks do not claim design
approval or assistive-technology sign-off.

## 18. Compatibility classification

Stable public API: `CCol`, `CRow`, their server inputs, aliases, default
slots, public CSS variables, selectors, reflected attributes, validation, and
zero-JavaScript behavior.

Behavioral contract: one native root, no child wrappers, Col vertical layout,
Row horizontal layout and default wrapping, DOM-order semantics, and no
stacking or clipping context.

Evolvable design: exact gap fallback lengths and undocumented `.cui-*`
classes. Private implementation: private CSS variables and validation helper
organization.

## 19. Public documentation contract

The page uses a ceramics-studio theme and teaches the common jobs before edge
cases. Planned previews:

| Module | Reader task | Visible coverage | Focused evidence |
|---|---|---|---|
| `at_a_glance.py` | recognize Col and Row | studio note Col plus action Row | roots, default gaps, no wrappers |
| `col_spacing.py` | choose vertical rhythm | all six gaps | reflected gaps and computed spacing |
| `row_alignment.py` | align and distribute actions | align and justify combinations | computed flex properties |
| `wrapping.py` | handle narrow action rows | wrapping and no-wrap groups | narrow geometry |
| `semantic_roots.py` | retain document meaning | nav and list roots | native tags and relationships |
| `nested_layouts.py` | compose practical layouts | nested Col and Row | direct-child isolation |
| `customization.py` | apply brand spacing | public variables and selector override | computed cascade |
| `direction.py` | support RTL and long content | LTR/RTL paired layout | order and overflow geometry |

The guide orders composition, spacing, alignment, wrapping, semantic roots,
customization, direction, and API reference. Static examples use side-by-side
rendered output instead of browser controls that merely swap server inputs.

## 20. Open decisions and deferred work

Implementation blockers: none.

Deferred:

- Container and Grid are now provided by the separate `grid-container` family;
- responsive input objects and named breakpoints;
- Divider/separator insertion until a Divider family exists and child
  insertion can remain semantic and wrapper-free;
- equal-width or grow behavior because it depends on child cardinality and
  content shape;
- generic Flex because `class_`, `style`, and CSS already cover specialized
  combinations; and
- a global spacing-token tier until this and later layout families provide
  representative application evidence.

Falsifier for the two-component family: if implementation or public examples
show that one class plus a direction input is materially clearer and no more
verbose across the common horizontal wrapping jobs, remove `CRow` before
release. Current Mantine, Chakra, MUI, Web Awesome, and local composition
evidence supports retaining the two concise names.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
