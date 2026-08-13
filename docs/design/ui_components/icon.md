# Citry UI Icon specification

**Status (2026-08-08): production implementation, public guide, structured
reference, quality scenario, focused server/browser evidence, and distribution
provenance are checked in; human visual and assistive-technology review remains
release evidence.** This document defines the styled `CIcon` and its bundled
alias catalog. It does not define an IconButton, remote icon loader, arbitrary
SVG renderer, icon font, or third-party collection registry.

## 1. Purpose and product bar

`CIcon` renders a small, consistent SVG symbol from Citry UI's bundled local
catalog. It works in server-only pages, inherits the surrounding text color,
has useful sizing, remains decorative by default, and can become a named image
when an icon alone conveys information.

Production-complete means:

- every alias renders deterministically from the installed wheel with no
  network, font, Node, or browser-runtime dependency;
- decorative and meaningful uses have explicit, testable accessibility
  behavior;
- aliases needed by Citry UI components share one visual language and cannot
  flash as text or disappear while a client collection loads;
- physical and logical direction names behave predictably in LTR and RTL;
- source markup cannot be supplied through untrusted component inputs; and
- the bundled icon source, version, license, attribution, and wheel contents
  remain auditable.

The common jobs and shortest intended expressions are:

| Job | Template | Python composition | Support path |
|---|---|---|---|
| Add a decorative icon beside visible text | `<c-CIcon name="search" />` | `CIcon(name="search")` | direct API; decorative by default |
| Present a meaningful standalone symbol | `<c-CIcon name="triangle-alert" label="Storm warning" />` | `CIcon(name="triangle-alert", label="Storm warning")` | direct API; named image semantics |
| Use an icon in a Button | `<c-CButton><c-CIcon name="search" /> Search</c-CButton>` | compose `CIcon` in the Button slot | composition; the Button owns interaction and its accessible name |
| Match compact or prominent text | `size="sm"`, `size="md"`, or `size="lg"` | same input | direct API |
| Apply an arbitrary CSS size or color | `style="font-size: 2rem; color: ..."` | structured `style` or a class | CSS; Icon inherits `currentColor` |
| Override icon geometry consistently | set `--cui-icon-size` or `--cui-icon-stroke-width` | structured `style` or ancestor CSS | public CSS variables |
| Use an application-specific SVG | author a trusted SVG/component | same | separate component or ordinary trusted template markup |
| Trigger an action with only an icon | compose `CButton` and `CIcon`, naming the Button | same | Button + Icon composition; no new IconButton in this batch |
| Change a glyph from browser-owned state | render both fixed Icons in parent-owned `x-show` wrappers and keep them decorative | same composition in a parent component | composition; the parent owns the accessible name or status text |

Non-goals:

- raw SVG, path, HTML, URL, data URL, sprite, CSS-mask, ligature, or font-class
  inputs;
- runtime fetch, cache, fallback, collection discovery, or icon search;
- brand logos, flags, emoji, illustrations, multicolor art, or duotone icons;
- click, press, tooltip, badge, loading, spin, pulse, or animation behavior;
- arbitrary rotation or physical flipping inputs; use CSS when the visual job
  is genuinely physical; and
- a headless Icon API.

## 2. Prior art and complaints

The local audit found no Icon implementation in `citry_ui`. Existing Button,
Dialog, and Combobox code authors small symbols independently. The archived
Alpinui work supported class, ligature, SVG, and component adapters but left
some modes incomplete and did not install required font assets. That is direct
evidence for one local SVG format and explicit asset ownership.

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI and local prior art | workspace reviewed 2026-08-08 | existing Button, Dialog, and Combobox symbols plus [`local-prior-art.md`](../ui_research/local-prior-art.md#33-theme-defaults-locale-and-icons) | Replace repeated symbols with one catalog; do not recreate incomplete font and adapter modes. |
| WAI image guidance and ARIA `img` | reviewed 2026-08-08 | [WAI images](https://www.w3.org/WAI/tutorials/images/), [Decorative images](https://www.w3.org/WAI/tutorials/images/decorative/), and [MDN `img` role](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/img_role) | Decorative output stays out of the accessibility tree; meaningful standalone output uses `role="img"` and an accessible name. |
| WAI-ARIA APG | reviewed 2026-08-08 | [Button pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/) and [Names and descriptions](https://www.w3.org/WAI/ARIA/apg/practices/names-and-descriptions/) | Functional graphics describe the action, not the picture. Icon never imitates Button focus or Enter/Space behavior. |
| SVG accessibility | reviewed 2026-08-08 | [MDN SVG `title`](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/title) | Prefer an explicit label on the outer image; do not add an incidental browser tooltip through `<title>`. |
| Vuetify | 4.1.8 source reviewed 2026-08-08 | [`VIcon`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VIcon/VIcon.tsx), [icon resolver](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/composables/icons.tsx), and [icon configuration](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/icons.ts) | Keep semantic aliases, local SVG output, current color, fixed geometry, logical start/end composition, and missing-name diagnostics. Reject clickable Icon and broad renderer polymorphism. |
| Material UI | 9.3.1 docs and source reviewed 2026-08-08 | [Icons guide](https://mui.com/material-ui/icons/), [`SvgIcon` API](https://mui.com/material-ui/api/svg-icon/), and [source](https://github.com/mui/material-ui/blob/v9.3.1/packages/mui-material/src/SvgIcon/SvgIcon.js) | SVG is preferable to fonts; default decorative output; explicit naming for meaningful icons; fixed view box, current color, sizes, and native SVG customization. Keep the catalog independent of a second framework package. |
| Chakra UI | 3.36.1 source and docs reviewed 2026-08-08 | [Icon guide](https://chakra-ui.com/docs/components/icon) and [Icon source](https://github.com/chakra-ui/chakra-ui/blob/%40chakra-ui%2Freact%403.36.1/packages/react/src/components/icon/icon.tsx) | A small SVG wrapper can be static, focus-free, and decorative. Chakra's removal of bundled icons shows the consumer-dependency cost Citry's default product must avoid. |
| Nuxt UI | 4.10.0 source and issues reviewed 2026-08-08 | [Icon source](https://github.com/nuxt/ui/blob/v4.10.0/src/runtime/components/Icon.vue), [current internal-icon plugin](https://github.com/nuxt/ui/blob/v4.10.0/src/plugins/icons.ts), [first-load failure #2195](https://github.com/nuxt/ui/issues/2195), and [loader complexity complaint #1188](https://github.com/nuxt/ui/issues/1188) | Current Nuxt embeds internal icons for synchronous offline SSR and hard-fails listed missing icons. Citry adopts those outcomes without requiring a build scan; dynamic names and external collection licenses remain Nuxt-side costs. |
| Web Awesome | 3.11.0 docs and published source reviewed 2026-08-08 | [Icon docs and API](https://webawesome.com/docs/components/icon) and [published source revision](https://github.com/shoelace-style/webawesome/blob/f20d6faff79ac347612d03ce4892869c9c4ab672/packages/webawesome/src/components/icon/icon.ts) | Labels, current color, local aliases, and stable parts are useful. Reject remote `src`, load/error events, family-specific rotation/animation, and executable external SVG risk. |
| Lucide | 1.30.0 reviewed and selected 2026-08-08 | [release](https://github.com/lucide-icons/lucide/releases/tag/1.30.0), [catalog](https://lucide.dev/icons/), and [ISC/Feather MIT license](https://github.com/lucide-icons/lucide/blob/main/LICENSE) | Vendor a reviewed subset as source data, preserve notices, use a consistent 24-unit stroke system, and exclude brand marks. |
| Nuxt Icon | issues reviewed 2026-08-08 | [server bundle memory #226](https://github.com/nuxt/icon/issues/226) and [custom collection recognition #252](https://github.com/nuxt/icon/issues/252) | Do not ship the full upstream catalog or make build-time scanning and collection recognition part of `CIcon`. |

The strongest recurring patterns are local SVG, `currentColor`, a square view
box, font-relative sizing, decorative defaults, explicit labels for meaningful
icons, and composition into semantic controls. The recurring shortcomings are
missing or flashing icons when loading is remote, large dependency or build
costs when a whole catalog is included, ambiguous collection configuration,
icon-font asset coupling, and clickable visual wrappers that imitate Buttons
without complete native semantics.

Material complaints shape the boundary rather than merely supporting it:

| Report | Status on 2026-08-08 | Citry decision |
|---|---|---|
| [Vuetify #21521](https://github.com/vuetifyjs/vuetify/issues/21521), documented aliases missing from `IconAliases` | fixed 2025-06-04 | Generate or validate the public name type, catalog, semantic aliases, docs, and tests from one catalog source. |
| [Vuetify #22807](https://github.com/vuetifyjs/vuetify/issues/22807), generic Iconify support | closed after documentation 2026-04-27 | Build extraction can support broad sets, but Citry's first catalog stays local and build-free. |
| [MUI #33421](https://github.com/mui/material-ui/issues/33421), `titleAccess` title loss with a replaced root | open | Keep one SVG root and put the name on that root instead of combining title insertion with polymorphism. |
| [MUI #45391](https://github.com/mui/material-ui/issues/45391), import and bundle ambiguity across hundreds of icons | open | Ship an audited subset and no barrel-style second package in this batch. |
| [Nuxt UI #1188](https://github.com/nuxt/ui/issues/1188) and [#2195](https://github.com/nuxt/ui/issues/2195), parallel loaders and first-render gaps | closed in 2024; current 4.10 architecture changed | Preserve synchronous offline SSR; document that broad dynamic catalogs remain a different build problem. |
| [Web Awesome #2285](https://github.com/shoelace-style/webawesome/issues/2285), default icon CDN returned 403 | closed completed 2026-04-15 | Never make a remote service the default Icon source. |
| [Chakra #357](https://github.com/chakra-ui/chakra-ui/issues/357), compound Icons lacked decorative and focus suppression | fixed 2020-02-26 | Own `aria-hidden` and `focusable` on the one Icon root and prove composition. |

Vuetify receives the primary styled-suite comparison weight:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `icon` prop and default text slot | direct API | required `name` | Use one explicit spelling; do not parse slot text as configuration. |
| `$alias` lookup | direct API | bundled semantic aliases such as `close`, `success`, `prev`, and `next` | Adopt deterministic aliases without an application provider in this batch. |
| named icon sets and default set | omitted for now | fixed bundled Lucide-derived catalog | A configurable registry needs a per-Citry installation/configuration contract and must not be improvised as global mutation. |
| SVG path arrays and component icons | separate component or trusted template SVG | composition | Do not expose raw executable markup or framework component values through `CIcon`. |
| class and ligature sets | omitted | none | Avoid fonts, external CSS, ligatures, and fallback text flashes. |
| `color` | CSS or utility classes | `class_`, `style`, and inherited `currentColor` | Avoid a second arbitrary color vocabulary. |
| named and numeric `size` | direct API plus CSS | `sm`, `md`, `lg`; `--cui-icon-size`; `style` | Keep the frequent sizes concise while preserving arbitrary CSS sizing. |
| `start` and `end` spacing | composition | parent layout or Button slots | Spacing belongs to the component that owns the relationship. |
| `disabled` | composition | owning Button, control, or text state | A non-interactive image cannot be disabled. |
| `opacity` | CSS | `style`, class, or ancestor CSS | No dedicated input. |
| `tag` polymorphism | omitted | fixed `<svg>` | One renderer keeps semantics and assets predictable. |
| theme | inherited theme contract | `currentColor` and public variables | No Icon-local theme provider. |
| click detection, `role="button"`, and `tabindex` | separate component | `CButton` + `CIcon` | Reject non-native Button imitation and missing keyboard activation. |
| missing-alias warning | direct API | server-render error | Fail before output instead of rendering an empty icon. |

## 3. Public composition and anatomy

Template use:

```citry-html
<p>
  <c-CIcon name="leaf" />
  New growth
</p>
```

Python composition:

```python
from citry_ui import CIcon

warning = CIcon(
    name="triangle-alert",
    label="High wind warning",
)
```

Button composition:

```citry-html
<c-CButton c-attrs="{'aria-label': 'Search field notes'}">
  <c-CIcon name="search" />
</c-CButton>
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CIcon` | `<svg>` | `attrs`, `class_`, and `style` merge on the SVG root | `name` must resolve in the bundled catalog; `label` chooses meaningful rather than decorative semantics |

The SVG owns a `0 0 24 24` view box and Lucide-compatible geometry. The exact
number and kind of child geometry nodes are private. No wrapper element is
promised. The SVG is never interactive. Put it inside `CButton`, a native
Button, or a native link when it participates in an action.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `name` | `CIconName` | required | structural server-only | Resolves one bundled glyph or semantic alias. Unknown names raise `ValueError` before output. |
| `label` | `str | None` | `None` | structural server-only | `None` makes the Icon decorative. A non-empty escaped string creates named-image semantics. Empty or whitespace-only strings and trusted `Markup`/`__html__` values raise `ValueError`. |
| `size` | `CIconSize` | `"md"` | structural server-only | Selects the `sm`, `md`, or `lg` size fallback. |
| `class_` | `CClassValue | None` | `None` | structural server-only | Adds structured root classes and merges them with `attrs`. |
| `style` | `CStyleValue | None` | `None` | structural server-only | Adds structured root styles and merges them with `attrs`. |
| `attrs` | `Mapping[str, object] | None` | `None` | structural server-only | Adds allowed inert SVG metadata such as `id`, `lang`, `dir`, `hidden`, `aria-describedby`, `aria-details`, and consumer `data-*` attributes. It cannot contain Alpine/Citry browser directives, event bindings, or replace owned geometry, focus, naming, catalog, or part attributes. |

There are no client inputs. Icons have no browser-owned configuration or state,
so `$c-props` would require shipping the catalog and a swap initializer for
every otherwise static Icon. Replace a server-rendered Icon to change it, or
prerender the finite alternatives in parent-owned wrappers:

```citry-html
<button
  type="button"
  c-x-data="{'revealed': False}"
  :aria-label="revealed ? 'Hide observation' : 'Show observation'"
  @click="revealed = !revealed"
>
  <span x-show="!revealed">
    <c-CIcon name="eye" />
  </span>
  <span x-show="revealed">
    <c-CIcon name="eye-off" />
  </span>
</button>
```

Both Icons remain decorative; the Button owns its changing accessible name.
Accordion uses one fixed chevron and transforms it from parent-owned expanded
state instead of swapping glyphs. A large or unbounded client-selected catalog
would justify a separately budgeted client registry. The finite composition
costs two SVGs per binary visual state and no Icon-specific JavaScript.

## 5. State model

`CIcon` has no interactive state. Its complete render states are:

| State | Trigger | Semantic result | Visual result |
|---|---|---|---|
| decorative | `label is None` | `aria-hidden="true"`, no image role, not focusable | selected glyph |
| meaningful | non-empty `label` | `role="img"`, `aria-label=label`, not focusable | selected glyph |
| invalid name | unknown `name` | no output | server `ValueError` names the bad alias |
| invalid name type | non-string `name`, including unhashable values | no output | server `TypeError` names the value |
| invalid label | non-string label | no output | server `TypeError` names the value |
| empty label | empty or whitespace-only label | no output | server `ValueError` names the field |
| invalid size | value outside `sm`, `md`, and `lg` | no output | server `ValueError` lists the accepted values |
| invalid attrs | non-mapping value or non-string key | no output | server `TypeError` names the value or key |
| owned or executable attr | owned attribute, browser directive, or event binding | no output | server `ValueError` names the rejected attribute |

Disabled, read-only, loading, selected, pending, empty, and error do not belong
to Icon. The component that owns those states selects and describes an Icon.

## 6. Slots and slot data

`CIcon` defines an empty `Slots` schema and exposes no public slots. Its finite
geometry comes from the audited bundled catalog. A slot for paths or raw SVG
would turn trusted package code into an unbounded renderer without improving
ordinary composition.

Application-specific SVG belongs in trusted template markup or a separate
component. A future configurable icon registry must define its own source,
trust, alias-collision, installation, and licensing contract.

## 7. Callbacks, native events, and methods

There are no component callbacks, custom events, or public methods. The SVG is
not an action. Compose it into a Button or link and listen to that native
control's events.

`attrs` rejects `@...`, `:...`, inline `on*` handlers, `x-*`, `c-x-*`,
`x-bind:*`, `c-bind:*`, and equivalent mixed-case spellings. Put directives and
native event listeners on the semantic parent. This preserves fixed geometry
and naming after browser activation instead of relying on `pointer-events:
none` as a security boundary.

## 8. Semantics, keyboard, focus, and assistive technology

Decorative is the default because Icons commonly repeat adjacent Button or
text labels. Meaningful output is opt-in and requires a non-empty `label`.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| Icon reinforces adjacent text | omit `label` | hidden from the accessibility tree | none | no |
| Icon alone communicates non-interactive information | set `label` | one named `img` node | none | no |
| Icon is visual content of a Button or link | omit Icon `label`; name the control | control supplies the accessible name | native control focus | native control behavior only |
| Consumer adds `tabindex`, `role`, `aria-hidden`, `aria-label`, `aria-labelledby`, or an executable browser attribute through `attrs` | invalid | render fails | none | not applicable |

The SVG always has `focusable="false"`. It never enters Tab order, handles a
key, restores focus, or creates touch behavior. A meaningful label describes
what the symbol communicates in context, not the catalog name. Prefer visible
text when practical.

## 9. Native forms and validation

`CIcon` is not a form participant and submits no value. It does not own
disabled, read-only, required, validation, reset, or submission behavior. A
form control containing an Icon owns all of those semantics and keeps the Icon
decorative.

## 10. Styling and theme contract

The SVG uses `fill="none"`, `stroke="currentColor"`, round caps and joins, and
non-scaling square geometry. Its color follows the surrounding foreground.
There are no intent or color inputs.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-icon-size` | length | Square inline and block size | size-derived: `0.875em`, `1em`, or `1.25em` |
| `--cui-icon-stroke-width` | number | Glyph stroke width in the 24-unit view box | `2` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="icon"]` | SVG root and customization target | every Icon | sole component root |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-name` | any documented `CIconName` | Resolved public alias requested by the caller |
| `data-size` | `"sm" | "md" | "lg"` | Effective named size fallback |

Defaults live in `citry-ui.theme`. Public variables resolve through private
effective variables so ancestor and root overrides both work. Internal
`.cui-icon*` classes and private variables are not API.

## 11. Environmental behavior

- Light and dark schemes need no Icon-specific palette; `currentColor` follows
  the surrounding foreground.
- Physical aliases such as `arrow-left` and `chevron-right` keep their authored
  direction in RTL.
- Logical aliases `back`, `forward`, `prev`, and `next` mirror in RTL. The name,
  accessible label, and DOM alias remain unchanged.
- Vertical aliases and non-directional shapes never mirror.
- The component has no motion. Reduced motion changes nothing.
- Forced colors retain `currentColor`; public overrides cannot make the SVG a
  CSS background image.
- Font-relative sizing follows zoom and text scaling. The root does not shrink
  in flex layouts.
- Pointer and touch add no behavior. Narrow layouts treat the Icon as one
  inline square.
- Icons print using the surrounding print color. Meaning must not rely on color
  or the Icon alone when printed information needs text.

The only library-authored visible content is the glyph itself. `label` is
application-authored accessible text and remains part of later localization
work.

## 12. Overlay and layering behavior

`CIcon` never creates or controls an overlay, tooltip, top-layer node, portal,
stacking context, focus scope, or dismissal behavior. Compose a separately
specified Tooltip when the product supports one; `label` is not a tooltip.

## 13. Collections, async data, and identity

The alias catalog is immutable package data. Lookup is synchronous and local.
There is no collection request, cache, suspense state, fallback glyph, retry,
offline branch, or runtime registration. An invalid name fails server render
instead of producing an empty placeholder.

The first catalog contains these visual glyph names:

`arrow-down`, `arrow-left`, `arrow-right`, `arrow-up`, `calendar`, `check`,
`chevron-down`, `chevron-left`, `chevron-right`, `chevron-up`, `circle-check`,
`circle-help`, `circle-info`, `circle-x`, `clock`, `copy`, `download`, `edit`,
`external-link`, `eye`, `eye-off`, `file`, `folder`, `heart`, `home`, `leaf`,
`link`, `lock`, `mail`, `menu`, `minus`, `more-horizontal`, `more-vertical`,
`plus`, `refresh-cw`, `search`, `settings`, `star`, `trash`, `unlock`, `upload`,
`user`, `triangle-alert`, and `x`.

It also contains these semantic aliases:

| Alias | Glyph | Mirrors in RTL | Meaning |
|---|---|---:|---|
| `back` | `arrow-left` | yes | Return in logical navigation history |
| `forward` | `arrow-right` | yes | Advance in logical navigation history |
| `prev` | `chevron-left` | yes | Previous item or page in logical order |
| `next` | `chevron-right` | yes | Next item or page in logical order |
| `close` | `x` | no | Close a surface |
| `clear` | `x` | no | Clear a value |
| `success` | `circle-check` | no | Successful outcome |
| `info` | `circle-info` | no | Informational message |
| `warn` | `triangle-alert` | no | Warning condition |
| `danger` | `circle-x` | no | Error or dangerous condition |
| `expand` | `chevron-down` | no | Reveal content on the block axis |
| `collapse` | `chevron-up` | no | Hide content on the block axis |
| `dropdown` | `chevron-down` | no | Open a popup below the control in the default writing mode |

Alias-to-glyph mappings and the RTL column are public behavior. The exact path
data is evolvable visual design.

## 14. Server render, morph, and cleanup

Server output is the complete useful Icon. No-JavaScript output and activated
output are identical. The component emits CSS only when Icon is used and emits
no JavaScript.

Morphing may replace `name`, `label`, size, classes, styles, or attributes as
ordinary SVG output. Icon owns no focus, selection, observer, listener, timer,
request, or disposable resource. Repeated initialization and removal therefore
need no cleanup hook.

## 15. Security and content trust

`name` indexes an immutable mapping. It is never interpolated into an HTML
fragment, path, class name, URL, file path, or import. The selected SVG body is
maintainer-vendored trusted package markup from the pinned Lucide source.

Plain `label` and allowed attribute strings follow Citry escaping. Every
consumer input rejects trusted `Markup`/`__html__` values recursively,
including mapping keys and nested class, style, and attrs structures. This
prevents Citry's explicit trusted-markup protocol from crossing Icon's strict
SVG boundary. `attrs` cannot replace
`viewBox`, `xmlns`, `fill`, `stroke`, `stroke-width`, `stroke-linecap`,
`stroke-linejoin`, `width`, `height`, `focusable`, `role`, `aria-hidden`,
`aria-label`, `aria-labelledby`, `tabindex`, `data-name`, `data-size`, or
`data-citry-ui-part`. It also rejects every inline event or Alpine/Citry browser
directive, including direct, shorthand, `x-bind:*`, and `c-bind:*` spellings.
Citry runtime namespaces beginning with `data-citry-`, `data-cev`, or
`data-cid` are also reserved. Checks are case-insensitive and occur before
attributes reach the template.

Raw SVG, remote URLs, external `<use>`, data URLs, script, style, foreign
objects, event attributes inside vendored geometry, and caller-supplied trusted
HTML are outside the API. The vendoring check parses every upstream SVG and
allows only the reviewed geometry tags and attributes before generating the
immutable source mapping.

Citry UI components that need a registered decorative glyph use CIcon's
private resolver instead of reading the generated mapping directly. The
resolver performs the same allowlist and safe-Markup conversion and returns
logical-direction metadata with the glyph. It does not expose a second public
Icon API or accept client-selected names.

## 16. Assets and performance

The family adds:

- one small static CSS block;
- one Python mapping containing the selected Lucide 1.30.0 SVG geometry;
- the Lucide ISC and inherited Feather MIT notices in the source distribution
  and wheel; and
- no JavaScript, font, image, network request, observer, listener, or external
  runtime package.

Only the selected subset ships, not Lucide's complete 1,600-plus catalog. The
asset report records emitted CSS raw, gzip, and Brotli bytes; wheel
qualification inventories the exact three Icon runtime modules and both
license notices. The scaling report records output bytes and diagnostic timing
for 1, 10, 100, and 1,000 Icons. It must remain linear and must not add one
component asset per alias or per instance. Exact timing is diagnostic, not a
release gate without a stable hosted baseline.

## 17. Acceptance matrix

Checked-in automated evidence must cover:

- every public alias and semantic mapping, non-string and unknown-name
  diagnostics, label and size validation, malformed attrs, owned-attribute and
  direct/shorthand/bound directive rejection, reserved runtime namespaces,
  recursively nested trusted-markup rejection, mapping immutability, and
  consumer-mapping snapshots;
- exact decorative and meaningful SVG semantics, no focusability, fixed view
  box, class/style merge, public attributes, part marker, and escaped text;
- the bundled SVG allowlist and absence of script, style, foreign object,
  external references, URLs, and event-handler attributes;
- ancestor and root variable overrides, part-selector overrides, all named
  sizes, `currentColor`, flex behavior, nested light/dark schemes, forced
  colors, zoom, print, and LTR/RTL physical-versus-logical directions;
- composition inside Button, Alert, Card, Field, Dialog, Table, and Accordion
  scenarios as those families exist;
- Nu HTML/SVG validation, axe, CSP, screenshot candidates, and focused Chromium,
  Firefox, and WebKit browser coverage;
- 1/10/100/1,000-instance diagnostic render and output-size records; and
- source distribution and wheel contents, license notices, offline install,
  no undeclared dependency, and installed-artifact render.

Manual release evidence covers visual consistency at every size, light/dark
and forced-color legibility, 200%/400% zoom, screen-reader decorative and named
output, RTL direction meaning, and real Safari/mobile rendering. Automated
role/name assertions do not replace an assistive-technology sample.

## 18. Compatibility classification

1. **Stable public API:** `CIcon`, `CIconName`, `CIconSize`, input names and
   meanings, alias names and semantic mappings, errors, public variables,
   selector, reflected attributes, and decorative/meaningful behavior.
2. **Behavioral and structural contract:** one SVG root, fixed view box, no
   focus or interaction, current-color rendering, RTL behavior, no-JavaScript
   output, local lookup, and no runtime fetch.
3. **Evolvable design:** exact glyph paths, stroke shapes, size fallback values,
   and private alignment details may improve without changing alias meaning.
4. **Private implementation:** Python mapping organization, the shared
   registered-glyph resolver and metadata record, trusted-markup
   representation, `.cui-*` classes, private variables, and vendoring tools.

Adding an alias is backward-compatible. Removing or repurposing one is a
breaking change. A materially changed glyph meaning requires the same review
even when the name remains.

## 19. Public documentation contract

The page theme is botany and field observation. It avoids application-dashboard
copy and lets color, direction, Button composition, and meaningful versus
decorative output appear in recognizable contexts.

| Order and module | Reader task | Rendered content and controls | Contract coverage | Focused browser evidence |
|---|---|---|---|---|
| 1. `at_a_glance.py` | Recognize the component immediately | A compact field-note legend using search, leaf, calendar, circle-info, and circle-check; no controls | default size, current color, decorative composition | preview loads, no console errors, accessible surrounding text |
| 2. `catalog.py` | Find the bundled vocabulary | Grouped action, navigation, status, object, and semantic aliases with visible names | every alias resolves; no missing glyph; catalog discoverability | all names and SVGs present; narrow wrapping |
| 3. `size_and_color.py` | Match nearby typography | Side-by-side `sm`, `md`, `lg`, inherited colors, and one public size override | size input, `currentColor`, public variables, class/style | computed size/color and light/dark |
| 4. `meaning.py` | Choose decorative or meaningful semantics | The same weather symbol beside visible text and alone with `label` | `aria-hidden`, `role=img`, accessible name, no focus | axe and accessibility-tree assertions |
| 5. `composition.py` | Use Icons in real controls and feedback | Search, save, and next-trail Buttons plus a passive field warning | Button ownership, semantic aliases, non-interactive Icon | keyboard reaches controls, never Icon |
| 6. `direction.py` | Distinguish physical and logical direction | LTR and RTL trail maps comparing arrow-left/right with back/forward and prev/next | automatic logical mirroring, physical stability | computed transforms and screenshots in both directions |
| 7. `customization.py` | Apply stable theme overrides | A botanical key using ancestor variables and the public selector in light/dark | both public variables, selector, nested schemes, forced colors | computed override and forced-color smoke |

No configurator is needed. Inputs are server-only, and side-by-side results are
more honest than browser controls that swap hidden prerendered output. Source
stays collapsed by default and every preview supports **Try live**.

The conceptual guide order is: smallest use, catalog, size and color, meaning,
Button and component composition, direction, customization, then the generated
API reference. `api.yml` exhaustively lists Inputs, CSS, Attributes, Selectors,
and Interfaces. Slots, Events, and Methods are empty categories.

## 20. Open decisions and deferred work

No unresolved decision blocks implementation after design review.

Deferred work:

- per-Citry custom icon registries, collection packages, alias overrides, and
  provider/configuration APIs;
- a larger optional Lucide catalog or build-time subset generator;
- IconButton, Tooltip, animation, progress symbols, badges, and multicolor or
  duotone artwork;
- raw/local URL SVG loading and its sanitization, CORS, CSP, caching, load/error,
  fallback, and offline contract; and
- locale-specific icon choice beyond the logical RTL aliases defined here.

Revisit reactive `name` and `label` only if real components repeatedly need
duplicated conditional SVG, the documented parent-owned pattern becomes
materially verbose, or repeated-instance output measurements show that it is
more expensive than a bounded client registry. The replacement design must
retain server output, offline behavior, accessible-name ownership, and a clear
asset budget.

The dedicated IconButton falsifier remains active: add it only if real Button +
Icon call sites prove materially too verbose, unsafe, or inconsistent after
`CIcon` exists. A preference for one tag is not enough.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
