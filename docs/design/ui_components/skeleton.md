# Citry UI Skeleton specification

**Status (2026-08-09): production implementation pass complete. Runtime,
public documentation, focused server/browser evidence, previews, quality and
scaling scenarios, and wheel qualification are wired. Human visual review,
independent implementation review, multi-browser checks, and final release
qualification remain.**

## 1. Purpose and product bar

`CSkeleton` is a decorative placeholder primitive for content whose layout is
known before its data arrives. It provides rectangles, circles, and one or
more text lines that applications compose into cards, lists, media rows,
tables, and other domain-specific loading shapes.

| Job | Shortest template | Support path |
|---|---|---|
| Placeholder block | `<c-CSkeleton height="8rem" />` | direct API |
| Avatar shape | `<c-CSkeleton kind="circle" width="3rem" height="3rem" />` | direct API |
| Paragraph | `<c-CSkeleton kind="text" c-lines="3" />` | direct API |
| Card or list shape | several Skeletons inside `CStack`/`CGroup` | composition |
| Announce loading | `aria-busy` and visible/status text on the owning region | native composition |

The family deliberately rejects Vuetify's type mini-language. Primitive
composition preserves equivalent expressive power while keeping DOM, spacing,
and responsive behavior visible in ordinary Citry templates. Skeleton does not
fetch, reveal content, own async state, or infer the shape of children.

## 2. Prior art and complaints

| Product or standard | Version or review date | Surface inspected | Decision supported |
|---|---|---|---|
| Citry UI | workspace 2026-08-09 | Flow, Card, Avatar, theme contract | Build complex shapes with normal composition and stable tokens. |
| WAI-ARIA | reviewed 2026-08-09 | `aria-busy`, status/live-region guidance | Keep placeholders decorative; loading semantics belong to the owning region. |
| Vuetify | 4.0.7/current docs reviewed 2026-08-09 | loader types, animation/boilerplate, dimensions, loading wrapper | Match shape capability through composition; adopt animation off; omit type grammar and content switching. |
| Material UI | current docs reviewed 2026-08-09 | text/circular/rectangular/rounded, pulse/wave, inferred dimensions | Adopt primitive variants and pulse/wave; keep explicit dimensions. |
| Mantine | current docs reviewed 2026-08-09 | width, height, radius, circle, animate | Confirm dimension-first primitive design. |
| Chakra UI | current docs reviewed 2026-08-09 | Skeleton, Circle, Text and loading/content wrapper | Confirm separate shapes; omit wrapper ownership. |

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| predefined bones/type grammar | composition | `kind`, `lines`, `CStack`, `CGroup`, CSS | reject opaque grammar |
| avatar/button/image/text/paragraph | direct primitive | `kind`, dimensions, lines | adopt capability |
| card/list/table/article patterns | composition | ordinary component/layout tree | adopt capability without presets |
| loading content switch | owner state | `c-if`/`x-if` outside Skeleton | omit competing async owner |
| boilerplate | direct API | `animation="none"` | adopt |
| dimensions | direct API | `width`, `height` | adopt |
| elevation/theme/class/style | CSS | `class_`, `style`, `attrs`, public variables | no elevation prop |

## 3. Public composition and anatomy

```citry-html
<c-CGroup>
  <c-CSkeleton kind="circle" width="3rem" height="3rem" />
  <c-CStack c-gap="'xs'">
    <c-CSkeleton kind="text" />
    <c-CSkeleton kind="text" width="65%" />
  </c-CStack>
</c-CGroup>
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CSkeleton` | decorative `span[aria-hidden=true]` | root | text mode contains one or more direct line spans |

`attrs`, `class_`, and `style` land on the root. Skeleton has no child
component or slot. Complex patterns are ordinary sibling composition.

## 4. Server inputs and client inputs

```python
CSkeletonKind = Literal["rect", "text", "circle"]
CSkeletonAnimation = Literal["pulse", "wave", "none"]
```

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `kind` | `CSkeletonKind` | `"rect"` | structural presentation | Selects rectangle, text lines, or circle. |
| `lines` | positive `int` | `1` | structural presentation | Number of text lines; values other than one require `kind="text"`. |
| `animation` | `CSkeletonAnimation` | `"pulse"` | presentation | Selects pulse, wave, or static output. |
| `width` | `str | None` | `None` | root geometry | Sets `--cui-skeleton-width`; explicit nonempty CSS length/percentage. |
| `height` | `str | None` | `None` | root geometry | Sets `--cui-skeleton-height`; explicit nonempty CSS length/percentage. |
| `last_line_width` | `str` | `"70%"` | text geometry | Width of the last line when `lines > 1`. |
| `class_`, `style`, `attrs` | standard root styling | `None` | styling/trust | Merge copied root customization. |

There are no client inputs. Browser owners switch loading state outside the
component; changing structure requires a server rerender or browser-owned DOM.

## 5. State model

Skeleton has no mutable state. `data-kind` and `data-animation` reflect fixed
render configuration. Motion is CSS-only and disabled by reduced-motion.

## 6. Slots and slot data

Skeleton defines no slots. Composition is explicit around primitives, avoiding
hidden replacement or visibility ownership.

## 7. Callbacks, native events, and methods

No callbacks, component events, listeners, or methods. Native listeners in
`attrs` are allowed only when they do not replace component ownership, but a
decorative placeholder is not a supported action target.

## 8. Semantics, keyboard, focus, and assistive technology

Every root is `aria-hidden="true"`, nonfocusable, and absent from the
accessibility tree. The content owner supplies `aria-busy`, an accessible
name, and any status text. Skeleton never uses `alert`, `status`, or live
regions because repeated visual bones must not generate repeated announcements.

## 9. Native forms and validation

Skeleton is not form-associated and renders no controls. It must not replace a
real disabled form control when the control itself is already available.

## 10. Styling and theme contract

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-skeleton-width` | length/percentage | root or line width | kind-derived `100%` |
| `--cui-skeleton-height` | length/percentage | root/line height | rect `6rem`, text `0.75em`, circle equals width |
| `--cui-skeleton-radius` | length | corner radius | rect `0.5rem`, text `999px`, circle `50%` |
| `--cui-skeleton-background` | color | resting surface | scheme-derived neutral |
| `--cui-skeleton-highlight` | color | wave highlight | scheme-derived translucent white |
| `--cui-skeleton-gap` | length | text line gap | `0.5em` |
| `--cui-skeleton-duration` | time | pulse/wave cycle | `1.5s` |
| `--cui-skeleton-last-line-width` | length/percentage | final text line | input-derived `70%` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="skeleton"]` | root and attrs destination | always | one root |
| `[data-citry-ui-part="line"]` | text bone | text only | one or more direct children |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-kind` | `rect`, `text`, `circle` | primitive geometry |
| `data-animation` | `pulse`, `wave`, `none` | motion treatment |

## 11. Environmental behavior

Colors adapt through `light-dark()`. RTL needs no directional branch. Reduced
motion makes all forms static. Forced colors retains a visible CanvasText
outline and static fill. Narrow layout respects percentages and max width.
Print uses a static neutral outline. Visible library strings: none.

## 12. Overlay and layering behavior

Skeleton owns no overlay or stacking context. A placeholder for overlay content
belongs inside that overlay's existing owner.

## 13. Collections, async data, and identity

Skeleton owns no collection or async request. The application chooses stable
keys and replaces placeholders when its own data state changes.

## 14. Server render, morph, and cleanup

Output is complete without JavaScript. Morphing replaces primitive geometry
normally. There are no listeners, observers, timers, or cleanup work.

## 15. Security and content trust

Choice and dimension strings are converted to exact plain strings. Dimensions
reject U+0000, empty values, semicolons, braces, and CSS comments before being
placed in owned custom properties. Trusted `attrs` cannot replace hidden
semantics, public parts/reflections, focus, children, or Citry runtime fields.

## 16. Assets and performance

One shared CSS asset, zero JavaScript, zero listeners. Animation uses opacity
or a root pseudo-element without per-instance DOM for wave highlights.
Diagnostic scaling records 1, 10, 100, and 1,000 primitives.

## 17. Acceptance matrix

Focused evidence covers every kind/animation, line validation, dimensions,
attrs trust, exact anatomy, no JavaScript, CSS variables, reduced motion,
forced colors, narrow percentages, dark mode, root/ancestor/selector overrides,
docs previews, quality scenario, scaling, exports, schema, and wheel contents.
Human review covers perceived motion, content-shape fidelity, zoom, and print.

## 18. Compatibility classification

Stable: component, inputs, two parts, two reflections, and public variables.
Private: keyframes, pseudo-element implementation, exact neutral colors, and
generic example patterns. Adding convenience composition helpers is additive;
adding a type grammar would require a new design.

## 19. Public documentation contract

Page theme: a natural-history archive. Examples: at a glance; primitives;
text lines; composed field-note card; composed specimen list; motion and
reduced-motion explanation; customization. Examples make controls and rendered
content visually distinct and keep source collapsed by default.

## 20. Open decisions and deferred work

Deferred: type mini-language, automatic child measurement, content-switching
wrapper, table/date-picker presets, shimmer direction customization, and a
dedicated SkeletonGroup. Revisit only when repeated application markup proves
a concise helper can remain transparent.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
