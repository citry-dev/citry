# Citry UI Divider specification

**Status (2026-08-09): production implementation pass complete. Runtime,
public documentation, focused server/browser evidence, previews, quality and
scaling scenarios, and wheel qualification are wired. Human visual review,
independent implementation review, multi-browser checks, and final release
qualification remain.**

## 1. Purpose and product bar

`CDivider` separates adjacent sections with a semantic thematic break or a
purely decorative line. It supports horizontal and vertical layouts, concise
thickness and line-style choices, logical inset, and an optional visible label.
It is not an adjustable splitter, resize handle, menu separator declaration,
heading system, or spacing primitive.

Common jobs:

| Job | Shortest template | Support path |
|---|---|---|
| Mark a thematic break | `<c-CDivider />` | direct API and native `hr` |
| Add a visual line with no semantic meaning | `<c-CDivider c-decorative="True" />` | direct API |
| Separate controls horizontally | `<c-CDivider orientation="vertical" c-decorative="True" />` | direct API inside flex/grid layout |
| Name a new visible section | `<c-CDivider>Archived worlds</c-CDivider>` | default slot composition |
| Choose emphasis | `variant="dashed" size="md"` | direct API |
| Align with nested content | `inset="start"` or `--cui-divider-inset` | direct API and CSS |
| Control exact length, color, or opacity | `style` or public variables | CSS contract |
| Let a user resize adjacent panes | future Splitter family | unsupported by Divider |

Python composition follows the same shape:

```python
from citry_ui import CDivider

break_line = CDivider()
labelled = CDivider(slots={"default": "Archived worlds"})
```

Production completeness means correct native semantics, useful no-JavaScript
output, logical LTR/RTL geometry, readable light/dark and forced-color output,
compact repeated call sites, stable theming surfaces, and zero client runtime.
No headless API exists.

## 2. Prior art and complaints

Current source record:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI | workspace reviewed 2026-08-09 | Flow, Badge, Card, theme, component-authoring policy | Keep spacing outside Divider, expose root class/style/attrs, stable parts, inherited variables, and zero JavaScript. |
| HTML and WAI-ARIA | reviewed 2026-08-09 | `hr`, `separator`, `aria-orientation`, focusable separator guidance | Use native `hr` for horizontal thematic breaks; use `role="separator"` plus vertical orientation on a neutral element; exclude adjustable separators. |
| Vuetify | 4.0.7 source reviewed 2026-08-09 | `VDivider.tsx`, Sass, orientation, variant, inset, length, thickness, content, gradient | Adopt orientation, compact style/thickness choices, inset, and labelled composition. Route exact dimensions/colors through CSS and omit gradient. |
| Material UI | current docs reviewed 2026-08-09 | Divider orientation, inset/middle variants, flex item, child labels, text alignment, decorative guidance | Preserve native horizontal semantics, labelled composition, logical alignment, and explicit decorative mode. Do not add a `flexItem` prop when vertical CSS can stretch naturally. |
| Mantine | current docs reviewed 2026-08-09 | horizontal/vertical forms, size, solid/dashed/dotted, label position | Confirm concise size/style inputs and start/center/end labels. |
| Spectrum Web Components | 1.12.2 docs reviewed 2026-08-09 | `sp-divider` size, vertical layout, public thickness/color variables, separator semantics | Confirm three sizes, vertical stretch, and a small public token surface. |

Reference libraries occasionally make every line semantic, even when used only
to decorate dense layouts. Citry requires callers to choose `decorative=True`
for that job. Some libraries render labelled dividers as one named separator.
Citry instead keeps both line segments decorative and lets the visible label
remain ordinary document content. This avoids inventing focus or adjustable
separator behavior.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| horizontal and vertical | direct API | `orientation` | adopt |
| solid, dashed, dotted | direct API | `variant` | adopt |
| double line | CSS | `style` or public selector | omit uncommon prop |
| thickness | direct API and CSS | `size`, `--cui-divider-thickness` | adopt with concise preset plus exact override |
| color and opacity | CSS | public color variable or `style` | no duplicate props |
| inset | direct API and CSS | `inset`, `--cui-divider-inset` | adopt logical forms |
| length | CSS | `style`, class, or container layout | no duplicate prop |
| content and content alignment | slot | `default`, `label_pos` | adopt |
| content offset | CSS | label gap/inset variables | omit specialized prop |
| gradient | CSS | consumer selector/style | omit specialized visual mode |
| theme/class/style | normal Citry styling | `class_`, `style`, `attrs`, variables | adopt |

## 3. Public composition and anatomy

Shortest semantic form:

```citry-html
<c-CDivider />
```

Unlabelled horizontal anatomy:

```html
<hr data-citry-ui-part="divider" data-orientation="horizontal" />
```

Unlabelled vertical anatomy:

```html
<div
  role="separator"
  aria-orientation="vertical"
  data-citry-ui-part="divider"
  data-orientation="vertical"
></div>
```

Labelled anatomy:

```html
<div data-citry-ui-part="divider" data-labeled data-label-pos="center">
  <hr aria-hidden="true" data-citry-ui-part="line" />
  <span data-citry-ui-part="label">Archived worlds</span>
  <hr aria-hidden="true" data-citry-ui-part="line" />
</div>
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CDivider` | horizontal `hr`, vertical `div[role=separator]`, or labelled neutral `div` | root | labelled mode owns two decorative lines and one label wrapper |

`attrs`, `class_`, and `style` always land on the root. A labelled Divider is
horizontal only. `orientation="vertical"` with a default fill raises before
rendering. `label_pos` other than its default requires a default fill. Divider
has no administrative child component to remove.

## 4. Server inputs and client inputs

```python
CDividerOrientation = Literal["horizontal", "vertical"]
CDividerVariant = Literal["solid", "dashed", "dotted"]
CDividerSize = Literal["sm", "md", "lg"]
CDividerInset = Literal["none", "start", "end", "both"]
CDividerLabelPos = Literal["start", "center", "end"]
```

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `orientation` | `CDividerOrientation` | `"horizontal"` | structural server configuration | Selects native horizontal or ARIA vertical semantics. |
| `variant` | `CDividerVariant` | `"solid"` | visual server configuration | Selects border line style. |
| `size` | `CDividerSize` | `"sm"` | visual server configuration | Selects 1, 2, or 4 pixel fallback thickness. |
| `inset` | `CDividerInset` | `"none"` | visual server configuration | Adds logical start/end spacing along the line axis. |
| `label_pos` | `CDividerLabelPos` | `"center"` | labelled structural configuration | Changes the relative line lengths around a supplied label. |
| `decorative` | `bool` | `False` | semantic server configuration | Removes an unlabelled Divider from the accessibility tree. Labelled line segments are always decorative. |
| `class_` | `CClassValue | None` | `None` | root styling | Merges root classes with `attrs`. |
| `style` | `CStyleValue | None` | `None` | root styling | Merges root inline style with `attrs`. |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted root attributes | Adds copied nonconflicting native, data, targeted Alpine, and event attributes. |

Divider has no client inputs. Browser-owned visibility can use a targeted
`x-show`; changing orientation or semantics requires a server rerender.

## 5. State model

Divider owns no mutable state. Orientation, variant, size, inset, label
position, and semantic mode are fixed for one server render. Reflected
attributes expose configuration for CSS and inspection, not writable browser
state. A correlated rerender replaces the configuration normally.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---:|---:|---|---|
| `CDivider` | `default` | no | one | `{}` (`CDividerDefaultSlotData`) | renders one unlabelled line |

The default slot accepts ordinary flow content suitable for a short visible
section label. The label wrapper is neutral and does not force heading
semantics. Authors can place a real heading inside when document structure
requires one. Interactive label content is discouraged because Divider is not
an action container, but it remains ordinary document content and receives no
event interception.

## 7. Callbacks, native events, and methods

Component callbacks: none. Public methods: none. Divider emits no custom
events and installs no listeners. Native listeners in `attrs` run on the root
but do not turn Divider into a supported control.

## 8. Semantics, keyboard, focus, and assistive technology

| Context | Result | Focus result | Prevent default |
|---|---|---|---|
| horizontal semantic, no label | native `hr` thematic break | no focus | no |
| vertical semantic, no label | `separator` with vertical orientation | no focus | no |
| decorative, no label | root has `aria-hidden="true"` | no focus | no |
| labelled | label is ordinary visible content; both lines are hidden from AT | only authored interactive descendants can focus | no |

Divider never uses `tabindex`, `aria-valuenow`, keyboard handlers, or resize
semantics. A focusable separator is a different Splitter component.

## 9. Native forms and validation

Divider is not form-associated, successful, required, resettable, or a
validation surface. Consumer content inside a label remains ordinary authored
HTML, including any independently owned form controls.

## 10. Styling and theme contract

Sizes map to fallback line thickness: `sm` 1px, `md` 2px, and `lg` 4px.
Variants map to solid, dashed, or dotted border style. Divider adds no external
block margin; surrounding `CStack`, `CGroup`, or application layout owns
spacing.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-divider-color` | color | line color | nested-scheme border color |
| `--cui-divider-thickness` | length | line thickness | size-derived |
| `--cui-divider-inset` | length | logical inset amount | `1.5rem` |
| `--cui-divider-label-gap` | length | gap from label to each line | `0.75rem` |
| `--cui-divider-label-color` | color | label foreground | `CanvasText` |
| `--cui-divider-label-font-size` | length | label text size | `0.875rem` |
| `--cui-divider-label-font-weight` | font-weight | label emphasis | `600` |
| `--cui-divider-min-length` | length | useful vertical minimum length | `1em` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="divider"]` | root and `attrs` destination | always | one root per component |
| `[data-citry-ui-part="line"]` | decorative line segment | labelled mode only | exactly two direct children |
| `[data-citry-ui-part="label"]` | visible label wrapper | labelled mode only | exactly one direct child between lines |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-orientation` | `horizontal`, `vertical` | line axis and semantics |
| `data-variant` | `solid`, `dashed`, `dotted` | line style |
| `data-size` | `sm`, `md`, `lg` | thickness preset |
| `data-inset` | `none`, `start`, `end`, `both` | logical inset preset |
| `data-labeled` | present or absent | default label slot is rendered |
| `data-label-pos` | `start`, `center`, `end` | labelled line balance; present only when labelled |
| `data-decorative` | present or absent | no separator semantics are exposed |

Default CSS lives in `@layer citry-ui.theme`, uses zero-specificity selectors,
and resolves public inputs through private effective variables.

## 11. Environmental behavior

Divider follows nested light/dark `color-scheme`, uses logical insets in LTR
and RTL, and retains a system-color line under forced colors and print. There
is no motion. Long labels wrap without causing page overflow. Vertical mode
stretches in flex/grid layouts and keeps a small useful minimum length. Zoom
and text spacing may increase labelled height without clipping.

Library-authored visible strings: none.

## 12. Overlay and layering behavior

Divider creates no overlay, containing block, stacking context, clipping,
portal, top-layer element, focus trap, or outside-interaction behavior.

## 13. Collections, async data, and identity

Divider owns no collection, key, async request, selection, pagination, or
virtualization behavior. Repeated Dividers use ordinary parent identity.

## 14. Server render, morph, and cleanup

Server output is complete without JavaScript. Divider has no initializer,
listener, observer, timer, retained state, or cleanup. Morphing can change any
server input and replace the documented root form while Citry retains normal
component ownership.

## 15. Security and content trust

Slot content uses normal Citry escaping. Enum inputs are converted to exact
plain strings before validation. `attrs` is copied before validation and is
the explicit trusted attribute boundary.

Divider rejects case-insensitive owned semantics, part/reflection attributes,
Citry/Events runtime namespaces, role/focus/editability/naming fields,
whole-object binding, and structural or child-replacing Alpine directives.
Dynamic aliases for owned fields are also rejected. Targeted unrelated
bindings, `x-data`, `x-init`, `x-effect`, `x-show`, native listeners, and
nonconflicting native/data attributes remain available.

## 16. Assets and performance

Divider adds one CSS asset and zero JavaScript, icons, fonts, listeners,
observers, timers, or per-instance data. Unlabelled output is one element;
labelled output is one root plus three children. Diagnostic scaling records 1,
10, 100, 500, and 1,000 instances without timing gates. Asset tools record
raw, gzip, and Brotli CSS bytes.

## 17. Acceptance matrix

Checked-in automated evidence must cover:

- nested schema/type introspection and exact defaults;
- every enum, Boolean, mapping, invalid type, and cross-input error;
- horizontal native `hr`, vertical ARIA separator, decorative roots, and
  labelled neutral anatomy;
- required ARIA presence and forbidden redundant or focusable semantics;
- labelled line cardinality, label positions, and vertical-label rejection;
- root class/style/attrs merging, copied mappings, reserved fields, dynamic
  aliases, runtime namespaces, and hostile trusted-string subclasses;
- computed orientation, variant, size, inset, label layout, public variable,
  and public selector overrides;
- LTR/RTL logical geometry, long labels, nested light/dark schemes, forced
  colors, and print;
- zero JavaScript, asset/scaling inclusion, exact exports, structured API,
  docs projection, preview discovery, and wheel contents.

The public scenario supplies semantic, decorative, labelled, vertical,
variant, size, inset, long-label, and two brand-token specimens. Shared tools
register axe, Nu HTML, screenshots, assets, scaling, and wheel evidence.
Manual release review still covers visual rhythm, real assistive-technology
separator phrasing, print, and browser matrix sign-off.

## 18. Compatibility classification

Stable public API: `CDivider`, its inputs and aliases, default slot/data,
validation errors, public variables, selectors, reflected attributes, and
zero-JavaScript behavior.

Behavioral and structural contract: native horizontal `hr`, vertical separator
semantics, decorative hiding, neutral labelled root, exactly two labelled line
segments, no focus, and no external margin.

Evolvable design: exact fallback colors and spacing lengths. Private:
`.cui-*`, `--_cui-*`, validation helpers, and incidental class names.

## 19. Public documentation contract

The page uses an astronomy theme and teaches:

| Preview | Reader task |
|---|---|
| `at_a_glance.py` | recognize semantic, labelled, and vertical Dividers |
| `basic_dividers.py` | write shortest template and Python compositions |
| `semantic_and_decorative.py` | choose whether a line belongs in the accessibility tree |
| `orientations.py` | separate vertical and horizontal layouts |
| `labels.py` | place visible section labels at start, center, or end |
| `variants_and_sizes.py` | compare line styles and thickness presets |
| `insets.py` | align lines with nested content using logical insets |
| `customization.py` | apply two theme treatments and stable selectors |

`api.md` owns the reader-first guide and embeds these previews. `api.yml` owns
the exhaustive structured reference. Neither duplicates the other.

## 20. Open decisions and deferred work

Implementation blockers: none.

Deferred: adjustable splitters, double and gradient variants, exact length and
opacity props, client-reactive configuration, named separator semantics,
automatic heading semantics, menu-specific separator declarations, and a
standalone spacing primitive.

Falsifier for the labelled design: if assistive-technology and application
evidence shows a named nonadjustable separator is materially clearer than
ordinary visible label content plus decorative line segments, research an
explicit labelled semantic mode without changing the default composition.
