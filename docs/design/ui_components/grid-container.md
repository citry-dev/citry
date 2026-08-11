# Citry UI Grid and Container specification

**Status (2026-08-09): production runtime, structured API, eight public
examples, docs/quality/scaling/wheel wiring, and focused server and Chromium
evidence are complete. Human, multi-browser, released-artifact, and independent
implementation review remain.**

## 1. Purpose and product bar

`CContainer`, `CGrid`, and `CGridItem` provide the small two-dimensional
layout vocabulary that Flow deliberately omits:

- `CContainer` centers page content and constrains its maximum inline size;
- `CGrid` creates equal responsive columns, or an intrinsic auto-fitting
  grid when a minimum column width is supplied;
- `CGridItem` spans tracks for the less-common asymmetric layout.

The common template stays flat:

```citry-html
<c-CContainer>
  <c-CGrid sm="2" lg="4">
    ...
  </c-CGrid>
</c-CContainer>
```

Python composition uses the same names:

```python
from citry_ui import CContainer, CGrid

gallery = CContainer(
    slots={"default": CGrid(sm=2, lg=4, slots={"default": cards})},
)
```

Common jobs:

| Job | Shortest surface | Support path |
|---|---|---|
| Center ordinary page content | `<c-CContainer>...</c-CContainer>` | direct API |
| Remove the maximum width | `<c-CContainer fluid>...</c-CContainer>` | direct API |
| Render a fixed equal grid | `<c-CGrid cols="3">...</c-CGrid>` | direct API |
| Add responsive equal columns | `<c-CGrid sm="2" lg="4">...</c-CGrid>` | direct API |
| Fit as many useful columns as space permits | `<c-CGrid min_col="16rem">...</c-CGrid>` | direct API |
| Build a main/sidebar split | `CGrid(cols=12)` with `CGridItem(md=8)` and `CGridItem(md=4)` | direct API |
| Change spacing | `gap="lg"` or a public CSS variable | direct API / CSS |
| Add bespoke breakpoints, alignment, placement, or ordering | `class_`, `style`, or consumer CSS | CSS/Tailwind escape path |

Production completeness means native CSS Grid, zero component JavaScript,
mobile-first rendering, predictable nesting, valid semantic-root choices,
public CSS variables and selectors, RTL-safe logical sizing, narrow-content
evidence, and exact packaging/docs integration.

Non-goals: a utility framework, row/column utility classes, arbitrary
responsive prop objects, container-query syntax, subgrid, masonry, overlap,
absolute placement, individual breakpoint gaps/alignment, observation,
animation, or JavaScript layout measurement. Tailwind and other utility
systems remain compatible consumer choices.

## 2. Prior art and complaints

Current source record:

| Product or standard | Reviewed | Surface | Citry decision |
|---|---|---|---|
| Vuetify | current source, 2026-08-09 | `VContainer`, `VRow`, `VCol`, breakpoint composable and Grid Sass | Give Vuetify extra weight: adopt flat `sm`/`md`/`lg`/`xl` inputs, a 12-track asymmetric model, `fluid`, and concise native roots. Do not copy the surrounding utility framework. |
| Bootstrap | 5.3, 2026-08-09 | Containers, `row-cols-*`, and column spans | Confirm parent-owned equal column counts and item-owned asymmetric spans are distinct frequent jobs. |
| Ionic | current source, 2026-08-09 | flat `size`, `sizeSm`, `sizeMd`, and later breakpoint inputs | Confirm a flat responsive component surface works without a configuration object. |
| Mantine | 9.x, 2026-08-09 | Grid and SimpleGrid | Adopt intrinsic minimum-column mode. Reject responsive object props and a JavaScript breakpoint resolver. |
| Chakra UI | 3.x, 2026-08-09 | SimpleGrid | Confirm minimum-child-width auto-fit is a valuable direct surface. |
| Material UI | 7/9-era docs, 2026-08-09 | Grid and Container | Keep centered max-width Container and direct Grid inputs; reject object-heavy responsive props. |
| Tailwind CSS | current docs, 2026-08-09 | responsive variants and container queries | Use familiar mobile-first thresholds and preserve classes as the escape path. Do not turn Citry UI into a utility framework. |
| Quasar, Radix Themes, GOV.UK, Lightning, Carbon, Bulma | current docs, 2026-08-09 | Grid/container APIs | Confirm flat classes are concise but would expand Citry UI beyond component scope; object/minilanguage alternatives are too verbose in Citry templates. |
| CSS Grid Layout and Media Queries | current standards, 2026-08-09 | native tracks, spans, auto-fit/minmax, viewport breakpoints | Use CSS only. DOM and reading order always remain authored order. |

The breakpoint vocabulary is fixed and mobile-first:

| Name | Minimum viewport width |
|---|---:|
| `sm` | `40rem` |
| `md` | `48rem` |
| `lg` | `64rem` |
| `xl` | `80rem` |
| `xxl` | `96rem` |

These thresholds are a stable Citry UI contract, not user-redefinable design
tokens: custom properties cannot drive media-query conditions. Applications
that need different viewport thresholds or CSS container queries should add a
class and write ordinary consumer CSS. Breakpoint inputs affect only column
count or item span; multiplying them across every gap/alignment input would
recreate a utility framework inside component props.

`CContainer` is a width-constraining page-content wrapper. It is not a CSS
query container and does not establish `container-type` or `container-name`.

## 3. Public composition and anatomy

```citry-html
<c-CContainer size="lg">
  <c-CGrid cols="12" gap="lg">
    <c-CGridItem span="12" md="8">
      <main>...</main>
    </c-CGridItem>
    <c-CGridItem span="12" md="4">
      <aside>...</aside>
    </c-CGridItem>
  </c-CGrid>
</c-CContainer>
```

| Component | Root | Relationship |
|---|---|---|
| `CContainer` | selected semantic element, default `div` | centered block with inline gutters and optional max width |
| `CGrid` | selected semantic element, default `div` | native Grid formatting context for direct children |
| `CGridItem` | selected semantic element, default `div` | ordinary direct Grid child with a responsive column span |

Every component renders exactly one root and its default slot. There are no
implicit row wrappers and no child cloning. `CGridItem` is a real styled
wrapper, not a declaration component. It renders valid standalone HTML, but
its span only has useful meaning as a Grid item. The caller remains
responsible for matching an item span to the containing track count.

Allowed tags:

- Container: `div`, `main`, `section`, `article`, `nav`, `aside`;
- Grid: `div`, `section`, `ul`, `ol`;
- GridItem: `div`, `section`, `article`, `li`.

Citry adds no role, name, heading, landmark label, or list semantics beyond
the selected native element. A list Grid must contain valid `li` children.

## 4. Server inputs and client inputs

`CContainer`:

| Input | Type | Default | Effect |
|---|---|---|---|
| `tag` | `CContainerTag` | `"div"` | selects the native root |
| `size` | `CContainerSize` | `"xl"` | selects the maximum outer inline size |
| `fluid` | `bool` | `False` | removes the maximum width while retaining gutters |
| `gutter` | `CLayoutGap` | `"lg"` | selects inline padding |
| `class_`, `style`, `attrs` | shared root styling/attributes | `None` | customize the one root |

`fluid=True` may use only the default `size="xl"`; another size is rejected
because it would be inactive and misleading.

`CGrid`:

| Input | Type | Default | Effect |
|---|---|---|---|
| `tag` | `CGridTag` | `"div"` | selects the native root |
| `cols` | `int` | `1` | base equal column count, from 1 through 12 |
| `sm`, `md`, `lg`, `xl`, `xxl` | `int | None` | `None` | override the count at and above that breakpoint |
| `min_col` | `str | None` | `None` | selects intrinsic auto-fit mode with one positive CSS length |
| `gap` | `CLayoutGap` | `"md"` | selects row and column gap |
| `class_`, `style`, `attrs` | shared root styling/attributes | `None` | customize the one root |

`min_col` accepts a positive decimal `px`, `rem`, `em`, `ch`, `vw`, `vh`,
`vmin`, or `vmax` length. Functions and arbitrary CSS belong in
`--cui-grid-min-column`. Intrinsic mode rejects `cols != 1` and every
responsive count so there is exactly one track-sizing owner.

`CGridItem`:

| Input | Type | Default | Effect |
|---|---|---|---|
| `tag` | `CGridItemTag` | `"div"` | selects the native root |
| `span` | `int` | `1` | base column span, from 1 through 12 |
| `sm`, `md`, `lg`, `xl`, `xxl` | `int | None` | `None` | override span at and above that breakpoint |
| `class_`, `style`, `attrs` | shared root styling/attributes | `None` | customize the one root |

Static template decimal attributes are accepted because the template syntax
is intentionally concise: `sm="2"`. Python and dynamic template expressions
must supply integers, not numeric strings or Booleans. Missing breakpoint
values inherit the nearest earlier value.

There are no client inputs and no JavaScript. Runtime-derived responsive
layout uses classes or CSS rules, not `$c-props`.

## 5. State model

- Grid is one column before its first override.
- Breakpoints are inclusive minimum widths and cascade upward.
- Equal mode uses `repeat(count, minmax(0, 1fr))`.
- Intrinsic mode uses `repeat(auto-fit, minmax(min(100%, minimum), 1fr))` so
  one column does not force overflow when the viewport is narrower than the
  requested minimum.
- Direct Grid children receive `min-inline-size: 0` and `min-block-size: 0`.
- GridItem uses `grid-column: span n / span n`; it does not alter DOM order.
- Container gutters use logical inline padding and remain correct in RTL.
- Container width includes its padding through `box-sizing: border-box`.
- All roots keep settled `overflow: visible`, `position: static`, and no
  containment, transform, isolation, or stacking context.
- Nested Grid/Container roots reset private responsive custom properties;
  inherited public custom properties remain deliberate theme inputs.

## 6. Slots and slot data

| Owner | Slot | Required | Data | Fallback |
|---|---|---|---|---|
| `CContainer` | `default` | no | `{}` (`CContainerDefaultSlotData`) | empty root |
| `CGrid` | `default` | no | `{}` (`CGridDefaultSlotData`) | empty root |
| `CGridItem` | `default` | no | `{}` (`CGridItemDefaultSlotData`) | empty root |

Unknown fills use Citry's ordinary slot validation. Slot content remains
caller-owned and may contain forms, controls, nested components, or text
allowed by the selected root's native content model.

## 7. Callbacks, native events, and methods

The family defines no callbacks, custom events, or methods. Native descendant
events bubble normally. Root listeners supplied through `attrs` observe
ordinary browser events and must inspect `event.target`.

## 8. Semantics, keyboard, focus, and assistive technology

No root becomes focusable or receives a role by default. Responsive visual
layout never changes DOM, reading, focus, or submission order. Consumers must
not use CSS placement or ordering utilities to create a visual order that
contradicts source meaning.

Container landmarks require the ordinary heading/name relationships for the
selected native tag. Grid `ul` and `ol` roots require `li` children. GridItem
`li` belongs under a valid list. Layout roots expose no accessibility state.

## 9. Native forms and validation

The family has no Form ownership or validity of its own. Grid and Container
preserve native controls, labels, validation, submission, reset, selection,
and focus in their slots. Roots never apply `inert`, `hidden`, `aria-hidden`,
or disabled state.

## 10. Styling and theme contract

Stable selectors:

- `[data-citry-ui-part="container"]`
- `[data-citry-ui-part="grid"]`
- `[data-citry-ui-part="grid-item"]`

Stable configuration reflections:

- Container: `data-size`, `data-fluid`, `data-gutter`;
- Grid: `data-cols`, `data-cols-sm`, `data-cols-md`, `data-cols-lg`,
  `data-cols-xl`, `data-cols-xxl`, `data-gap`, and `data-intrinsic`;
- GridItem: `data-span`, `data-span-sm`, `data-span-md`, `data-span-lg`,
  `data-span-xl`, and `data-span-xxl`.

Stable public variables:

| Component | Variable | Fallback |
|---|---|---|
| Container | `--cui-container-max-width` | selected size (`40rem` through `96rem`) |
| Container | `--cui-container-gutter` | selected gap preset |
| Grid | `--cui-grid-columns` | effective responsive count |
| Grid | `--cui-grid-gap` | selected gap preset |
| Grid | `--cui-grid-min-column` | `min_col` in intrinsic mode |
| GridItem | `--cui-grid-item-span` | effective responsive span |

Public variables are inherited and may be set on an ancestor or one root.
`--cui-grid-columns` and `--cui-grid-item-span` override every breakpoint;
custom responsive overrides use a class or public selector inside consumer
media/container queries.

Library defaults live in `citry-ui.theme` with zero-specificity selectors.
Unlayered consumer CSS wins regardless of source order. Applications using
named consumer layers must establish their layer order before both stylesheets.

The family defines no colors, typography, surface, elevation, or light/dark
state. Content styling remains consumer-owned.

## 11. Environmental behavior

Logical gutters and inline sizes follow LTR and RTL automatically. Narrow
containers retain zero-minimum tracks; authored content still owns its own
wrapping/overflow behavior. Zoom changes the effective pixel thresholds of
the fixed `rem` breakpoints as normal CSS does.

Forced colors retain native layout and consumer content colors. Reduced
motion has no effect because the family does not animate. Print retains the
same track and maximum-width contract; print-specific reflow is consumer CSS.

## 12. Overlay and layering behavior

Every root keeps `overflow: visible`, `position: static`, and no transform,
containment, isolation, or stacking context. The family does not clip menus,
tooltips, popovers, focus rings, or other descendant overlays. Consumer styles
may deliberately change that behavior.

## 13. Collections, async data, and identity

Grid does not inspect children or own collection identity. Server loops,
conditional content, client-owned DOM, and async results participate in native
CSS Grid as ordinary direct children. Citry morph keys remain caller-owned.

The family neither virtualizes nor measures large collections. Data tables,
masonry, and virtual grids require separate behavior contracts.

## 14. Server render, morph, and cleanup

All configuration is resolved during server render into owned data attributes
and private inline custom properties. No client asset, initializer, observer,
listener, cleanup, or retained-root handoff exists. A correlated rerender
simply replaces the relevant server snapshot; native CSS recomputes layout.

Nested roots reset private breakpoint properties so an outer Grid's supplied
values do not leak inward. Public variables intentionally inherit as design
inputs.

## 15. Security and content trust

`attrs` is a trusted native-attribute escape hatch, but each destination
reserves its stable part/configuration reflections and every Citry runtime
prefix (`data-citry-*`, `data-cev*`, `data-cid*`). Static and dynamic aliases
that target an owned field are rejected case-insensitively.

Whole-object `x-bind` and Alpine ownership/structural directives (`x-for`,
`x-html`, `x-if`, `x-ignore`, `x-model`, `x-modelable`, `x-teleport`, and
`x-text`) are rejected because they can replace children, roots, or ownership.
Targeted unrelated bindings, listeners, `x-data`, `x-init`, and `x-effect`
remain allowed. Consumer `class` and `style` may deliberately change layout.

Caller-owned mappings are copied before validation. Direct choice/length
strings are converted to exact plain strings; trusted-string subclasses do
not bypass validation.

Render raises deterministically for unknown choices; Boolean/non-integer,
below-1, or above-12 counts; dynamic/Python numeric strings; malformed,
zero/negative, or unsupported `min_col`; intrinsic/fixed conflicts; fluid with
a non-default size; non-Boolean `fluid`; non-mapping attrs; and owned/runtime/
structural attributes. Slot children and spans relative to a particular
parent are not inspected.

## 16. Assets and performance

The family contributes CSS only. It performs no client work and adds one root
per authored component. Equal grids need no item component; the asymmetric
path pays for `CGridItem` only where spans are required.

Asset tooling records raw/gzip/Brotli CSS. Diagnostic scaling records server
render time and output bytes at 1/10/100/500/1,000 Grid instances. These are
bounded diagnostics, not timing gates. Hosted results require release review.

## 17. Acceptance matrix

Checked-in server tests cover schemas, defaults, flat static numbers,
validation branches, intrinsic conflicts, semantic roots, attribute trust,
class/style merging, reflections, responsive snapshots, empty roots, nested
components, and zero JavaScript.

Focused Chromium tests cover exact columns/spans immediately below and at
breakpoints, missing-value inheritance, intrinsic fitting, public variables,
selector/class overrides, Container centering/fluid/gutters, nested private
reset, RTL, zero-minimum tracks, semantic roots, and settled overflow/position.

The repository scenario is registered for axe, browser, CSS coexistence,
docs, Nu HTML, screenshot, and diagnostic performance tools. Pairwise profiles
include light, dark, narrow, RTL, 200%/400% zoom, forced colors, and print.

Human visual review across supported browsers, assistive-technology sanity
review of representative semantic composition, and hosted artifact acceptance
remain release work. Independent implementation review was unavailable in
this session and is not claimed.

## 18. Compatibility classification

Stable: component names; nested Kwargs/Slots; server inputs; breakpoint values;
default values; one-root anatomy; public selectors; reflected attributes;
public variables; zero-JavaScript behavior; intrinsic/fixed exclusivity; and
deterministic failures.

Evolvable internals: private classes/custom properties, exact rule grouping,
template whitespace, validation helper organization, and quality-fixture text.

Deferred: CSS query-container ownership, user-defined breakpoint maps,
responsive gaps/alignment, subgrid, masonry, offset/order props, and utility
classes. Adding one requires its own research and compatibility review.

## 19. Public documentation contract

The public page uses one geological field-atlas theme and includes:

1. at-a-glance responsive specimen cards;
2. fixed and responsive equal columns;
3. asymmetric twelve-track field notes;
4. intrinsic mineral cards with `min_col`;
5. Container size and fluid comparisons;
6. gap and gutter presets;
7. semantic list composition and nested grids;
8. public-variable, RTL, and custom-query adaptation.

Examples use `c-ui-demo`, keep code collapsed initially, and do not teach
invalid inputs. There are no client controls because the first-class inputs
are server-only. The structured API is authoritative for inputs, slots, CSS,
attributes, selectors, and interfaces.

## 20. Open decisions and deferred work

No implementation blocker remains. Future project evidence may justify a
dedicated CSS query-container component or offset/order shorthand, but neither
belongs in the initial contract. Applications that need utility breadth should
use Tailwind or another utility layer through `class_`, not expand Citry UI
into a parallel utility framework.
