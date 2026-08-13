# Citry UI Avatar specification

**Status (2026-08-09): production implementation pass complete. Runtime,
public documentation, focused server/browser evidence, previews, quality and
scaling scenarios, and wheel qualification are wired. Human visual review,
independent implementation review, multi-browser checks, and final release
qualification remain.**

## 1. Purpose and product bar

`CAvatar` presents a compact visual identity for a person, creature, place, or
other named entity. It shows an image when available and a useful fallback
otherwise. It is a display primitive, not an upload control, presence system,
profile menu, badge positioner, or grouped-avatar collection.

| Job | Shortest template | Support path |
|---|---|---|
| Display a named portrait | `<c-CAvatar src="/fern.jpg" alt="Fern keeper" />` | direct API |
| Display authored initials | `<c-CAvatar alt="Mira Vale">MV</c-CAvatar>` | default slot |
| Display a generic fallback | `<c-CAvatar alt="Unassigned explorer" />` | built-in fallback |
| Make an avatar decorative | `<c-CAvatar src="/moon.jpg" />` | empty `alt` |
| Choose geometry | `size="lg" shape="rounded"` | direct API |
| Style the fallback | `variant="solid"` and public variables | direct API and CSS |
| Add status or count | compose `CBadge` in a consumer wrapper | composition |
| Show overlapping identities | `CGroup` plus application CSS | composition; AvatarGroup deferred |

Python composition uses the same inputs through `CAvatar(...)`.

Production completeness requires useful server output, image-error fallback,
stable accessible naming, reactive browser-provided image URLs, no broken-image
artifact, nested light/dark support, and a compact public styling contract. No
headless API exists.

## 2. Prior art and complaints

| Product or standard | Version or review date | Surface inspected | Decision supported |
|---|---|---|---|
| Citry UI | workspace reviewed 2026-08-09 | Badge, Icon, Alert, theme and authoring policy | Reuse concise variants/sizes, stable parts, inherited variables, and one runtime owner. |
| HTML and WAI guidance | reviewed 2026-08-09 | `img`, alternative text, broken-image behavior, accessible-name rules | Give the neutral root one stable name and keep the internal image decorative. |
| Vuetify | 4.0.7 source reviewed 2026-08-09 | `VAvatar.tsx`, Sass, image/icon/text/default/badge paths, size, rounded, variant | Adopt image/fallback composition, size, shape, variant, and class/style. Compose badges externally. |
| Material UI | current docs reviewed 2026-08-09 | image, letters, icon, grouping, badge and generated-color examples | Support authored text and generic fallback; do not guess initials or colors from names. |
| Mantine | current docs reviewed 2026-08-09 | image, fallback, initials, group, polymorphism and accessibility | Preserve fallback composition and explicit label. Defer group and name algorithms. |
| Chakra UI | current docs reviewed 2026-08-09 | Root/Image/Fallback, variants, sizes, group and image status | Adopt explicit anatomy and status callback; keep grouping separate. |
| Radix Avatar | 1.2.3 docs reviewed 2026-08-09 | Root/Image/Fallback and loading status | Confirm client image-state ownership and fallback behavior. |
| Spectrum Web Components | 1.12.2 docs reviewed 2026-08-09 | image, label, sizes and fallback guidance | Confirm explicit label and broad CSS customization. |

Citry rejects automatic initials and deterministic colors. Those algorithms
encode locale and identity assumptions and are easy to author explicitly.
Responsive `srcset` and cross-fade/delay policy are deferred until real image
delivery requirements establish the right API.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| image | direct API | `src` | adopt, including client updates |
| text/default content | slot | `default` | adopt |
| icon | fallback or composition | built-in silhouette or `CIcon` in default slot | no duplicate icon prop |
| badge/start/end positioning | composition | wrapper plus `CBadge` | omit from Avatar |
| size | direct API and CSS | `size`, `--cui-avatar-size` | adopt |
| rounded | direct API | `shape` | adopt as circle/rounded/square |
| variants/theme | direct API and CSS | `variant`, public variables | adopt |
| arbitrary tag | composition | consumer wrapper | omit; root remains neutral `span` |
| class/style | normal Citry styling | `class_`, `style`, `attrs` | adopt |

## 3. Public composition and anatomy

```citry-html
<c-CAvatar src="/portraits/mira.jpg" alt="Mira Vale" />
```

```html
<span role="img" aria-label="Mira Vale" data-citry-ui-part="avatar">
  <span aria-hidden="true" data-citry-ui-part="fallback">...</span>
  <img alt="" data-citry-ui-part="image" />
</span>
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CAvatar` | neutral `span`, or `span[role=img]` when named | root | fallback precedes an optional decorative image in one clipped visual surface |

`attrs`, `class_`, and `style` land on the root. `img_attrs` lands on the
internal image and cannot replace its source, alternative text, ownership, or
runtime fields. Avatar contains no structural child component.

## 4. Server inputs and client inputs

```python
CAvatarVariant = Literal["soft", "solid", "outline"]
CAvatarSize = Literal["sm", "md", "lg"]
CAvatarShape = Literal["circle", "rounded", "square"]
CAvatarStatus = Literal["fallback", "loading", "loaded", "error"]
```

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `src` | `str | None` | `None` | initial image source | A nonempty plain string starts image loading; `None` renders fallback only. |
| `alt` | `str` | `""` | stable accessible name | Nonempty text gives the root `role=img` and `aria-label`; empty text makes Avatar decorative. |
| `variant` | `CAvatarVariant` | `"soft"` | reactive presentation | Selects fallback treatment. |
| `size` | `CAvatarSize` | `"md"` | reactive presentation | Selects compact dimensions. |
| `shape` | `CAvatarShape` | `"circle"` | reactive presentation | Selects clipping radius. |
| `class_` | `CClassValue | None` | `None` | root styling | Merges root classes with `attrs`. |
| `style` | `CStyleValue | None` | `None` | root styling | Merges root inline style with `attrs`. |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted root attributes | Adds copied nonconflicting native/data/targeted Alpine attributes. |
| `img_attrs` | `Mapping[str, object] | None` | `None` | trusted image attributes | Adds copied inert image-loading and presentation attributes without replacing source or semantics. |

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `src` | `string | null` | server source | fallback only | one diagnostic per episode; server source | image, status |
| `alt` | `string` | server name | invalid | one diagnostic per episode; server name | root role/name |
| `variant` | enum | server value | invalid | one diagnostic per episode; server value | root reflection/CSS |
| `size` | enum | server value | invalid | one diagnostic per episode; server value | root reflection/CSS |
| `shape` | enum | server value | invalid | one diagnostic per episode; server value | root reflection/CSS |
| `onStatusChange` | callable | no callback | no callback | diagnostic and ignore | status transition notification |

Client values win while supplied. Omission restores the current server
fallback. A new valid source starts a new loading generation; stale events
from a prior URL cannot commit status.

## 5. State model

| State | Entry | DOM effect | Exit |
|---|---|---|---|
| `fallback` | no source | image absent; fallback visible | valid source supplied |
| `loading` | source assigned and not complete | image present over fallback; fallback remains behind it | load or error |
| `loaded` | image loaded successfully | image visible | source change/removal/error |
| `error` | current image errors | image hidden; fallback visible | source change/removal |

`data-status` mirrors the effective state. Same-source reactive updates do not
restart loading. Status callbacks fire only when the committed status changes.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---:|---:|---:|---|---|
| `CAvatar` | `default` | no | one | `{}` (`CAvatarDefaultSlotData`) | generic decorative silhouette |

Fallback content is always hidden from assistive technology because the root
owns the accessible name. It must not contain controls, form-associated
content, or essential independent text.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onStatusChange` | `{status: CAvatarStatus, src: str | None}` | committed status change | after DOM synchronization | reports client- or server-sourced image state | not cancellable |

Native root events use Alpine `@...` attributes. Avatar exposes no methods and
emits no custom DOM event.

## 8. Semantics, keyboard, focus, and assistive technology

Named Avatar is one `img` semantic on the root. The nested HTML image has
`alt=""` to avoid duplicate exposure. Decorative Avatar has no role or name.
Avatar is not focusable and has no keyboard interaction. Authored fallback
content never contributes a second accessible name.

## 9. Native forms and validation

Avatar is not form-associated, successful, required, resettable, or a
constraint-validation surface. Form controls are forbidden in fallback
content.

## 10. Styling and theme contract

Variants affect fallback presentation only. `soft` uses a quiet surface,
`solid` uses a strong surface, and `outline` uses a transparent surface with a
visible border. Sizes are `sm`, `md`, and `lg`; shapes are circle, rounded, and
square.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-avatar-size` | length | width and height | size-derived 2/2.5/3rem |
| `--cui-avatar-background` | color | fallback surface | variant/scheme-derived |
| `--cui-avatar-foreground` | color | fallback foreground | variant/scheme-derived |
| `--cui-avatar-border-color` | color | outline | variant-derived |
| `--cui-avatar-border-width` | length | border thickness | `1px` |
| `--cui-avatar-radius` | length | clipping radius | shape-derived |
| `--cui-avatar-font-size` | length | fallback text | size-derived |
| `--cui-avatar-font-weight` | font-weight | fallback text | `700` |
| `--cui-avatar-image-fit` | `<image>` fit keyword | image fit | `cover` |
| `--cui-avatar-image-position` | position | image position | `center` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="avatar"]` | root, styling and attrs destination | always | one root |
| `[data-citry-ui-part="fallback"]` | authored or generic fallback | always | first direct child |
| `[data-citry-ui-part="image"]` | decorative loaded image | source present | last direct child |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-variant` | `soft`, `solid`, `outline` | fallback treatment |
| `data-size` | `sm`, `md`, `lg` | size preset |
| `data-shape` | `circle`, `rounded`, `square` | clipping shape |
| `data-status` | `fallback`, `loading`, `loaded`, `error` | current image state |

## 11. Environmental behavior

Logical geometry supports LTR and RTL without directional changes. Default
colors adapt through `light-dark()`, including nested scheme scopes. Forced
colors retains the outline and fallback glyph. Reduced motion needs no special
case because Avatar has no transition. Long fallback text clips within the
fixed visual surface. Print shows the loaded image or fallback.

Visible library-authored strings: none.

## 12. Overlay and layering behavior

Avatar opens and owns no overlay. Status badges, menus, and upload flows are
separate compositions whose owners define positioning, focus, and layering.

## 13. Collections, async data, and identity

Avatar owns one browser image request at a time and ignores stale load/error
events from superseded sources. It does not fetch through JavaScript, retry,
cancel, cache, group, reorder, or virtualize identities.

## 14. Server render, morph, and cleanup

Server output immediately shows authored fallback beneath the image. Client
activation checks `complete` and `naturalWidth`, then records loaded/error
without waiting for another event. A correlated rerender reinitializes from
the new server source. Cleanup removes listeners and invalidates the current
generation. Repeated initialization must not duplicate callbacks.

## 15. Security and content trust

`src` is an ordinary escaped URL string, not trusted markup. `alt` is converted
to an exact plain string before rendering. Both reject U+0000; `src` also
rejects empty strings. Root attrs are a trusted expression boundary but cannot
replace role/name, public reflections, parts, children, focus semantics, or
Citry runtime fields. Image attrs cannot replace `src`, `srcset`, `sizes`,
`alt`, role/ARIA, load/error handlers, part markers, or runtime ownership.

## 16. Assets and performance

Avatar adds one shared CSS asset and one bounded initializer with two image
listeners when a source exists. Instances without a source still use the
initializer so reactive client `src` can activate later. Diagnostic scaling
records 1, 10, 100, and 1,000 instances; release qualification records asset
bytes and first source update without turning those diagnostics into hard
performance claims.

## 17. Acceptance matrix

Checked-in focused evidence must cover:

- schema defaults, every enum/type/error path, plain-string de-trusting, attrs
  copying, reserved fields, root/image destinations, fallback anatomy, and
  public exports;
- server source, no-source, authored fallback, decorative/named semantics,
  class/style merging, hostile strings, and exact reflected attributes;
- initial complete success/error, load/error transitions, source replacement,
  null/omission, stale events, callback payloads, invalid episodes, cleanup,
  and repeated activation;
- computed size/shape/variant defaults, root and ancestor token overrides,
  public selector overrides, light/dark, forced colors, narrow layout, print,
  and image fit; and
- docs preview discovery, zero serious axe findings, scenario/wheel/catalog
  wiring, and exact runtime-file qualification.

Manual release evidence retains screen-reader naming, actual slow/broken image
behavior across supported browsers, zoom, print, and visual polish.

## 18. Compatibility classification

Stable public API: `CAvatar`, its server and client inputs, default slot,
callback payload, type aliases, three public parts, four reflected attributes,
and documented CSS variables. Private implementation details: silhouette SVG
geometry, listener layout, diagnostic wording, and internal generations.

Adding `srcset`, grouping, automatic initials, upload, or badge positioning is
additive only after a separate design pass. Removing a part, callback field, or
accepted enum value is breaking.

## 19. Public documentation contract

Page theme: a fantasy field guide. Examples remain within one expedition
theme and show:

| Preview | Contract |
|---|---|
| `at_a_glance.py` | portraits, initials, and generic fallback |
| `images_and_fallbacks.py` | working, missing, and source-free paths |
| `accessible_names.py` | named and decorative use |
| `variants_and_sizes.py` | three variants and sizes |
| `shapes.py` | circle, rounded, square |
| `reactive_sources.py` | client source and status callback |
| `composition.py` | status Badge and compact group composition |
| `customization.py` | variables and public selector override |

The guide orders: see the family, choose image/fallback, provide a name,
choose appearance, update source in the browser, compose adjacent UI,
customize, then API reference.

## 20. Open decisions and deferred work

Deferred: `srcset`/`sizes`, loading delay/cross-fade, name-derived initials and
colors, upload/edit affordances, AvatarGroup/overflow count, remote image
proxying, and badge placement. Revisit only with application evidence. Human
visual and assistive-technology review remains release work.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
