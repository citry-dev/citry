# Phase 4 dossier: Bootstrap

**Snapshot:** 2026-07-23. **Studied line:** Bootstrap 5.3.8. **Evidence
scope:** current official documentation, tagged/current source links, and the
project issue tracker. No runtime reproduction was performed. Popularity and
adoption are not inferred from repository activity.

Evidence labels are **Docs**, **Source/release**, **Maintainer report**, **User
report**, and **Inference**. Confidence is high, medium, or low. A material
finding also records counterevidence and what remains unresolved. Complaint
grades follow the [Phase 3 protocol](candidate-map.md#52-complaint-sample-and-confidence).

## 1. Product snapshot, boundary, and maintenance

Bootstrap 5.3.8 is an MIT-licensed CSS framework with an optional JavaScript
runtime. It ships compiled CSS/JS, Sass source, utilities, layout, forms, and
interactive plugins; Popper is required for dynamically positioned dropdowns,
popovers, and tooltips unless the bundled build is used.
[Introduction](https://getbootstrap.com/docs/5.3/getting-started/introduction/),
[JavaScript](https://getbootstrap.com/docs/5.3/getting-started/javascript/), and
[license](https://github.com/twbs/bootstrap/blob/v5.3.8/LICENSE), **Docs and
Source/release, high confidence.** There is no paid component boundary in the
studied distribution. Bootstrap Icons is a separate optional project, not part
of the component package. **Docs, high.**

The 5.3 documentation identifies 5.3.8 as current and the tracker shows active
v5 maintenance while v6 work proceeds. This establishes maintenance, not
usage or future v5 support duration. **Docs and tracker observation, high;
counterevidence:** active v6 work can redirect fixes; **unresolved:** v6 release
date and remaining v5 support window.

## 2. Normalized inventory

| Citry category | Bootstrap 5.3.8 |
|---|---|
| Actions | Buttons, button groups, close button, links styled as buttons |
| Form controls | Input, textarea, select, checks/radios, switches, range, input groups, floating labels, layout and validation styles |
| Layout/content | Grid, containers, cards, accordion, collapse, ratio, stacks, typography, images, list groups |
| Navigation | Navbar, navs/tabs, breadcrumb, pagination, scrollspy |
| Overlays/feedback | Modal, offcanvas, dropdown, tooltip, popover, toast, alert, spinner, progress, placeholders |
| Data/collections | Styled semantic tables and responsive wrappers; no stateful Data Table, virtualizer, sorter, filterer, or row model |
| Utilities | Utility API, helpers, color modes, responsive display/spacing/position, RTL build |
| Specialist workflows | Carousel only; no combobox, date picker, file uploader, rich editor, tree, or form collection engine |

The inventory comes from the current
[documentation navigation](https://getbootstrap.com/docs/5.3/getting-started/introduction/)
and [table docs](https://getbootstrap.com/docs/5.3/content/tables/), **Docs,
high. Counterevidence:** third-party Bootstrap plugins add these families;
**unresolved:** those plugins are outside this product and were not counted.

## 3. Composition, behavior, and frozen slice

Bootstrap composes with authored HTML, semantic elements, classes, `data-bs-*`
attributes, and optional imperative plugin instances. Plugins expose methods
and lifecycle events, and `dispose()` removes instance data. Configuration
merges JSON config, individual data attributes, and JavaScript options, with
later sources winning. [JavaScript](https://getbootstrap.com/docs/5.3/getting-started/javascript/)
and [Modal API](https://getbootstrap.com/docs/5.3/components/modal/#api),
**Docs, high.** This is not a typed props/slots/compound-parts API. Markup is
consumer-owned, while plugin behavior and CSS selectors remain upstream-owned.

| Frozen probe | Verified finding | Evidence and status |
|---|---|---|
| Button | Native `button` or link plus `.btn` variants and sizes; no loading protocol or headless behavior object | [Button](https://getbootstrap.com/docs/5.3/components/buttons/), Docs, high; loading semantics unresolved |
| Field/Input | Native controls retain names, values, submission, labels, hints, and browser validation; Bootstrap adds wrappers and state classes | [Forms](https://getbootstrap.com/docs/5.3/forms/overview/), Docs, high |
| Dialog | Modal plugin owns backdrop, body scroll, Escape, focus, async transitions, and events; only one open modal is supported and nested modals are unsupported | [Modal](https://getbootstrap.com/docs/5.3/components/modal/), Docs, high; screen-reader matrix not published |
| Combobox/searchable Select | Not shipped. Dropdown accepts arbitrary content but explicitly does not supply a complete ARIA menu role contract | [Dropdown accessibility](https://getbootstrap.com/docs/5.3/components/dropdowns/#accessibility), Docs, high |
| Tabs | Nav markup plus tab plugin, target IDs, ARIA authoring, show/hide events, and keyboard-oriented markup examples | [Tabs](https://getbootstrap.com/docs/5.3/components/navs-tabs/#javascript-behavior), Docs, high |
| Table/Data Table | Semantic table styling, variants, captions, and horizontal responsive wrapper only | [Tables](https://getbootstrap.com/docs/5.3/content/tables/), Docs, high |
| Advanced form/collection | No collection state or workflow engine; forms remain native/application-owned | Inventory absence, Docs observation, high; third-party extensions excluded |
| Provider/context | No component provider. `data-bs-theme` and inherited CSS variables provide subtree-scoped visual context | [Color modes](https://getbootstrap.com/docs/5.3/customize/color-modes/), Docs, high |

IDs and `data-bs-target` selectors are the item/relationship identity mechanism
for tabs, collapse, carousel, and overlays. Dynamic lists must preserve unique
IDs across server renders and Citry morphs. **Inference, high; counterevidence:**
imperative element references can avoid some selectors; **unresolved:** no
library-level generated-ID or collision diagnostic exists.

### Ambient-context audit

| Question | Finding |
|---|---|
| Values carried | Theme/color mode through `data-bs-theme` and inherited custom properties; no locale, direction, portal root, nonce, or service context |
| Nesting and shadowing | Nearest `data-bs-theme` scope wins through normal CSS cascade; nested component overrides are documented |
| Defaults and overrides | Light is default; dark/custom modes require attributes and variable/Sass overrides; a picker is not shipped |
| Reactive update | Changing the attribute updates CSS reactively; persistence, system preference, and flash avoidance require application JavaScript |
| SSR/client agreement | Server HTML can set the same attribute with no hydration layer; client togglers must agree with stored/system preference |
| Portal/teleport | Plugins append backdrops and positioning artifacts in the document; no logical provider follows relocated DOM |
| Cleanup | Plugin `dispose()` exists, but application code must call it when removing imperatively initialized nodes |
| Diagnostics | No missing-provider, nested-theme, duplicate-ID, or stale-instance diagnostic was found |

**Docs, high** for theme behavior and disposal; **Inference, medium-high** for
Citry lifecycle pressure. Counterevidence is that CSS inheritance needs no
provider runtime. Unresolved is whether Citry's future `$provide`/`$inject`
must carry theme or only non-CSS ambient values; `$component.init()` cleanup
hooks are clearly pressured by plugin instances.

## 4. Customization ladder and styled/headless implications

| Level | Bootstrap contract | Citry reading |
|---|---|---|
| Tokens | Global and component CSS variables plus Sass maps/variables | Useful semantic-token precedent, but coverage is incomplete |
| Variants | Classes such as `.btn-primary`, sizes, responsive utilities, and color modes | Compact, predictable styled vocabulary |
| Parts | Conventional descendant classes, not a versioned named-part API | Consumers couple to markup and class structure |
| State | Classes, pseudo-classes, ARIA/data attributes, and plugin events | State names should be explicit in both Citry layers |
| Markup | Fully consumer-authored within documented structural expectations | Strong escape hatch, weak structural enforcement |
| Behavior | Data API or imperative plugins; some asynchronous methods ignore calls during transitions | Citry Events needs lifecycle and transition-state semantics |
| Source | Sass customization or fork; installed compiled assets remain upstream-owned | Do not require source ownership for ordinary branding |

Sources: [customize overview](https://getbootstrap.com/docs/5.3/customize/overview/),
[component variables](https://getbootstrap.com/docs/5.3/customize/components/),
and [CSS variables](https://getbootstrap.com/docs/5.3/customize/css-variables/),
**Docs, high.** Counterevidence to a pure Sass reading is substantial runtime
custom-property support. Unresolved is consistent token coverage across every
state. Bootstrap is a styled layer with behavior plugins, not a reusable
headless layer. Citry should borrow its default polish and native markup while
keeping an independently consumable behavior contract.

## 5. Accessibility, input modes, direction, and locale

Bootstrap says outcomes depend heavily on author markup, styling, and scripts;
some default palette combinations can miss WCAG 2.2 contrast. Generic
interactive components can require author-supplied ARIA. It supports reduced
motion for many transitions, and modal/dropdown plugins provide Escape and
keyboard behavior. [Accessibility](https://getbootstrap.com/docs/5.3/getting-started/accessibility/)
and [Dropdown accessibility](https://getbootstrap.com/docs/5.3/components/dropdowns/#accessibility),
**Docs claim and limitation, high confidence as published contract, not an
independent conformance audit.**

RTL is experimental, requires document `lang`/`dir`, and normally uses a
separate RTLCSS-generated stylesheet. [RTL](https://getbootstrap.com/docs/5.3/getting-started/rtl/),
**Docs, high.** No component localization or date engine is shipped. Touch is
claimed as a supported interaction mode, but no current forced-colors, IME,
zoom, or named screen-reader test matrix was found. **Docs observation, medium;
counterevidence:** individual components use native semantics; **unresolved:**
actual cross-AT results.

## 6. Forms, validation, submission, and async state

Bootstrap preserves native form controls and submission. Client styling uses
`:valid`/`:invalid` scoped by `.was-validated`; server errors can use
`.is-valid`/`.is-invalid`. The application owns request state, async errors,
loading, retries, and result reconciliation. [Validation](https://getbootstrap.com/docs/5.3/forms/validation/),
**Docs, high.**

The same page explicitly says custom client validation styles and tooltips are
not exposed to assistive technology and recommends server-side or browser
default validation. **Docs limitation, high. Counterevidence:** native browser
validation and server feedback remain accessible options; **unresolved:** no
published fix schedule. This directly supports Citry keeping native submission
and server errors first-class in both headless and styled forms.

## 7. Trust and security boundaries

Bootstrap does not escape application HTML or validate URLs; server templates
retain that responsibility. Tooltip and popover HTML is sanitized by default
with an allowlist. Sanitizer controls cannot be set through data attributes,
and disabling sanitization is explicitly a consumer risk.
[Tooltip options](https://getbootstrap.com/docs/5.3/components/tooltips/#options)
and [Popover options](https://getbootstrap.com/docs/5.3/components/popovers/#options),
**Docs, high.**

Broad `data-bs-*` and class forwarding can activate behavior, targets, or
styles, so Citry wrappers must not treat arbitrary attribute forwarding as a
non-security decision. **Inference, high.** Bootstrap has no file upload,
remote-result, generated-ID, or URL-policy layer. Strict CSP also requires
attention because v5 modal code writes inline `style` properties; a 2026
request documents the issue and says v6's native dialog path avoids it.
[Issue 42440](https://github.com/twbs/bootstrap/issues/42440), **User report
with source excerpt, grade B, medium-high. Counterevidence:** the issue is
closed and CSP can allow style attributes; **unresolved:** no evidence reviewed
that 5.3.8 removed the writes.

## 8. Assets, runtime, payload, and upgrades

Consumers can use CDN or self-hosted compiled CSS/JS, import Sass and selected
plugins, or bundle ES modules. The optimization guide recommends importing
only required Sass and JavaScript. Popper is bundled or separately required;
icons and fonts are not mandatory. [Optimize](https://getbootstrap.com/docs/5.3/customize/optimize/)
and [JavaScript](https://getbootstrap.com/docs/5.3/getting-started/javascript/),
**Docs, high.** No normalized payload reproduction was performed.

Markup, Sass variables, CSS variables, and JS APIs all form the upgrade
surface. The [5.3 migration guide](https://getbootstrap.com/docs/5.3/migration/)
documents breaking and deprecation changes. **Docs, high. Counterevidence:**
compiled no-build use is simple; **unresolved:** consumer override breakage is
application-specific. Citry should offer precompiled first-party assets and
selective imports without making a Node/Sass toolchain mandatory.

## 9. Material shortcomings and complaint evidence

| ID | De-duplicated pattern | Window, status, workflow, workaround, and grade |
|---|---|---|
| BS-1 | Runtime theming stops at Sass-compiled values in some states | Checkbox checked colors remained static in 5.3.7; issue opened 2025-08-09 and closed not planned. Use targeted CSS overrides or rebuild Sass. [Issue 41652](https://github.com/twbs/bootstrap/issues/41652), grade B; current 5.3.8 source not reproduced |
| BS-2 | The Sass customization path emits upstream deprecation warnings | Open 2024-10-21 through snapshot, with `@import` and global-function warnings under Dart Sass 1.80+. Pin/silence Sass, consume compiled CSS, or track the pending work. [Issue 40962](https://github.com/twbs/bootstrap/issues/40962), grade B |
| BS-3 | Custom client validation feedback is not accessible | Current official limitation affecting every styled form-validation workflow. Use server feedback or browser defaults. [Validation](https://getbootstrap.com/docs/5.3/forms/validation/), grade A |
| BS-4 | RTL is a separate experimental build | Current official limitation; mixed-direction pages can require both generated directions and added complexity. Use the RTL bundle and test nested validation/layout. [RTL](https://getbootstrap.com/docs/5.3/getting-started/rtl/), grade A |
| BS-5 | Responsive-table overflow can clip overlays | Current docs say `overflow-y: hidden` can clip dropdowns and other widgets. Move overlays outside the wrapper or change overflow with layout testing. [Responsive tables](https://getbootstrap.com/docs/5.3/content/tables/#responsive-tables), grade A |

BS-1 and BS-2 are user reports backed by quoted source/build output. BS-3 to
BS-5 are stronger current official limitations, not inferred complaint volume.
The CSP modal report is retained in the trust section rather than counted
again. No claim about prevalence is made.

### Complaint metadata audit

| ID | Affected and current version | Dates and status | Maintainer response and workaround | Impact |
|---|---|---|---|---|
| BS-1 | Report reproduces on Checkbox 5.3.7; current 5.3.8 was not reproduced in this audit. | Opened 2025-08-09 and closed not planned; a separate last-update date was not found. | Maintainers declined the requested runtime-token expansion. Use targeted CSS overrides or rebuild the relevant Sass variables. | Medium-high for runtime-branded themes. |
| BS-2 | Bootstrap 5.3.x Sass customization with Dart Sass 1.80 or later; current 5.3.8 output was not reproduced. | Opened 2024-10-21 and still open at snapshot; precise last-update date was not recorded here. | Upstream migration work remains pending. Pin or silence Sass, consume compiled CSS, or follow the issue. | Medium upgrade and build friction. |
| BS-3 | Current 5.3.8 documentation states the custom validation limitation. | Current documentation at snapshot, so no tracker open/update date or issue status applies. | Official workaround is server-side feedback or browser-default validation until a custom accessible implementation exists. | High for form completion and error discovery. |
| BS-4 | Current 5.3.8 RTL documentation; separate RTL output remains experimental. | Current documentation at snapshot, so no tracker open/update date or maintainer issue response applies. | Build and load the RTL artifact and test nested direction, validation, and layout explicitly. | Medium for RTL and mixed-direction applications. |
| BS-5 | Current 5.3.8 responsive-table documentation. | Current documentation at snapshot, so no tracker open/update date or issue status applies. | Move overlays outside the overflow wrapper or change overflow after layout testing. | Medium for tables containing dropdowns or overlays. |

### Complaint search log

Window: 2024-07-23 through 2026-07-23. Exact tracker queries:

- `repo:twbs/bootstrap is:issue created:2024-07-23..2026-07-23 accessibility focus modal dropdown`
- `repo:twbs/bootstrap is:issue created:2024-07-23..2026-07-23 theme css variables`
- `repo:twbs/bootstrap is:issue created:2024-07-23..2026-07-23 CSP`
- `repo:twbs/bootstrap is:issue created:2024-07-23..2026-07-23 RTL`

## 10. Citry conclusions

### Adopt or re-derive

- Native semantic markup and form submission as the default substrate.
- A broad, coherent styled catalog with small variant vocabularies.
- Precompiled no-build assets plus selective CSS/behavior imports.
- Semantic tokens, subtree theme overrides, responsive utilities, lifecycle
  events, and explicit disposal for imperative behavior.
- Honest component-level limitations and author-responsibility notes.

### Do not transfer directly

- CSS class conventions as the only parts API or Sass as the only complete
  customization route.
- A dropdown as a substitute for a true combobox or menu contract.
- Inaccessible custom validation, separate direction builds as the long-term
  model, or inline style mutation without a CSP policy.
- A styled package without a corresponding headless behavior contract.

### Pressure on Citry contracts

Bootstrap pressures Citry to define stable state and part names, generated-ID
ownership, reason-bearing lifecycle events, and cleanup when morphs remove an
initialized node. Theme can remain CSS inheritance, but direction, locale,
portal roots, CSP nonce, and service defaults require an explicit decision in
the `$provide`/`$inject` exploration. `$component.init()` needs a documented
disposer path. The default distribution should match Bootstrap's immediate
usability while its headless counterpart preserves native forms and lets users
replace markup without inheriting a second runtime.
