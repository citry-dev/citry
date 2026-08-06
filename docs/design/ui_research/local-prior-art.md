# Local prior art for Citry UI

**Snapshot: 2026-07-23. Phase 2 complete.** This report studies two local
evidence sources: the former Alpinui/Vuetify experiment in `old-vuetify.zip`
and the maintainer's production Django application in `old-chk.zip`. It asks
what product requirements and engineering lessons Citry UI should retain. It
does not approve either archive as implementation source.

The product target is defined in
[`product-charter.md`](product-charter.md). Current framework capabilities and
constraints are recorded in [`citry-baseline.md`](citry-baseline.md).

## 1. Executive conclusions

1. **The breadth ambition has credible local precedent.** The Alpinui archive
   attempted roughly ninety Vuetify-derived component families across layout,
   forms, navigation, overlays, feedback, and data display. It demonstrates
   that the maintainer's intended product was a suite, not a small widget
   pack.
2. **The production application validates the core of that breadth.** Its
   generic components are used hundreds of times. Forms, tables, tabs,
   disclosures, dialogs, menus, remote selection, and editable collections
   are recurring infrastructure rather than speculative features.
3. **Composition mattered more than a long prop list.** Typed inputs, named
   slots, compound children, explicit root and part attributes, semantic
   variants, and provider-style specialization recur across the application.
4. **The previous client architecture should not return.** Alpinui maintained
   shared TypeScript behavior, Vue-rendered DOM, and separately handwritten
   Django-rendered DOM. Its Alpine adapter did not use the shared render
   function, so the representations could drift. Vue-shaped compatibility
   layers, Alpine private-state mutations, handwritten serialization filters,
   raw JavaScript callback strings, DOM-query based communication, and
   patched distribution bundles added further coupling and performance risk.
   Current Citry owns the relevant component graph, prop, slot, Events, morph,
   and cleanup contracts.
5. **Styled and headless components need one behavior implementation.** The
   archives contain useful behavior requirements, but do not establish an
   accessibility-quality implementation. Citry UI should re-derive state
   machines and semantics from current web standards, then expose both the
   default theme and a headless surface over that shared contract.
6. **A separate distribution is supported by the history.** The old work had
   separate JavaScript and Django adapter packages, but its adapter covered
   only part of the suite and required manual asset insertion. `citry-ui`
   should likewise be independently installable, while making component
   registration, asset discovery, compatibility, and coverage explicit
   product contracts.

## 2. Evidence scope, safety, and confidence

The existing written audits were the starting point:

- [`../alpinejs/alpine-vuetify-audit.md`](../alpinejs/alpine-vuetify-audit.md)
  covers the Alpine packages, component model, private integration, and
  performance experiments associated with Alpinui.
- [`../alpinejs/alpine-workproject-audit.md`](../alpinejs/alpine-workproject-audit.md)
  covers the production application's browser architecture and recurring
  failure modes.
- [`../events_research/audit-context.md`](../events_research/audit-context.md)
  and the four `audit-chunk-*.md` reports cover the application's server
  interactions, forms, component use, and migration pressure.

Targeted read-only archive checks filled inventory and packaging gaps. The
archives were not extracted into the repository. Database contents, settings,
credentials, fixtures, and business records were outside the inspection
scope. No secret values or proprietary implementation excerpts are recorded
here.

| Evidence | Confidence | Permitted use |
|---|---|---|
| Current Citry source and design ledger | High | Framework baseline and integration constraints |
| Existing archive audits with cited paths | High for the inspected snapshot | Requirements and engineering lessons |
| Targeted archive filenames and package metadata | High for inventory and package shape | Coverage, distribution, asset, and maintenance evidence |
| Archive TODO claims | Medium | Intent and reported status, clearly labeled as claims |
| One production application | High for that application's needs | Pressure cases and reusable jobs, not market-wide demand |
| Archived implementation | Not approved for reuse | No copying without separate provenance and license review |

The Alpinui JavaScript package declares MIT metadata, as does its Django
adapter. The production archive has no project-level copying notice outside
its dependency trees, and several UI files attribute visual source to
Tailwind UI. Package metadata is not sufficient provenance for individual
templates or ported code. The archives therefore remain design-history and
requirements evidence.

## 3. Alpinui and the Vuetify-derived experiment

### 3.1 What it attempted to ship

The JavaScript archive TODO reports **89 of 89 standard component families
ported, 1 of 9 Labs families ported, and 0 of 89 tested**. The standard Alpine
build exports 91 family entrypoints including the Alpinui root; following
those modules produces 168 distinct public `A*` component names because many
families contain subcomponents. There are 93 component directories when
support and transition directories are included. These counts describe
different levels of the same catalog rather than an exact release claim.

| Category | Families visible in the archive |
|---|---|
| Application and layout | App, Main, AppBar, SystemBar, Footer, NavigationDrawer, Layout, Grid, Sheet, Responsive, Aspect-oriented image layout, Parallax, Lazy, NoSsr |
| Foundations and utilities | Alpinui root, ThemeProvider, DefaultsProvider, LocaleProvider, Icon, Image, Divider, Hover, Code, KeyboardKey, selection and item groups, transitions and visibility helpers |
| Actions | Button, floating action button, SpeedDial, ButtonGroup, ButtonToggle, Chip, ChipGroup |
| Forms and selection | Form, Field, Input, Label, Messages, Counter, TextField, Textarea, Select, Combobox, Autocomplete, FileInput, Checkbox, Radio, Switch, SelectionControl, Slider, RangeSlider, Rating, OTP input, ColorPicker, DatePicker, ConfirmEdit, validation helpers |
| Navigation and disclosure | Breadcrumbs, Tabs, Pagination, Stepper, ExpansionPanel, BottomNavigation, SlideGroup, Window, Carousel |
| Overlays | Overlay, Dialog, Menu, Tooltip, BottomSheet |
| Feedback and status | Alert, Banner, Badge, Snackbar, ProgressLinear, ProgressCircular, SkeletonLoader, EmptyState |
| Data display and collections | Avatar, Card, Chip, ChipGroup, List, Table, DataTable, DataIterator, VirtualScroll, InfiniteScroll, Timeline, Sparkline |

Examples of the larger compound surface include Card Title/Text/Actions,
DataTable Server/Virtual/Rows/Headers, DatePicker Month/Years/Controls, List
Item/Group/Children, Slider Thumb/Track, Stepper Item/Window, Tabs Window, and
Timeline Item/Divider. Picker is the only reported Labs family. Calendar,
DateInput, NumberInput, TimePicker, Treeview, SnackbarQueue, PullToRefresh, and
the vertical Stepper remained unported.

This is not a verified public API inventory. Some entries are internal
helpers, labs features, or compound subcomponents, and archive presence does
not establish completion. It is enough to recover the intended category
coverage and dependency graph for the later ecosystem comparison.

### 3.2 JavaScript and style architecture

The archive is structured as a JavaScript component system with several
supporting Alpine packages rather than as Python-first Citry components. A
family has three independently maintained representations:

```text
TypeScript *.base.ts
  -> props, composables, state, and setupHeadless()
Vue *.tsx
  -> consumes renderInput and renders the styled DOM
Alpine *.alpine.ts plus handwritten Django Python template
  -> publishes state into Alpine; Django recreates the styled DOM
```

The shared engine interface accepts a headless render function, but the Alpine
engine does not call it. Instead, `setupHeadless()` exposes public state and
separate DOM-rendering inputs to Alpine, and the Django template must reproduce
the markup and bind those values. As a result, "headless" here is an internal
state/composable layer, not a public accessible component without styles. DOM,
keyboard, focus, and accessibility behavior can still diverge between the Vue
and Django renderers.

The filename audit found 281 `*.alpine.ts` or `*.alpine.tsx` files, 180
`*.base.ts` or `*.base.tsx` files, and roughly 120 Sass/SCSS component-style
files. The build also separates normal and Labs bundles, directives,
blueprints, generated props, locale, themes, icons, and composable utilities.

The style system is broader than isolated component CSS. It includes reset
and cascade-layer work, colors, typography, display utilities, elevation,
radius, density, animation and transition primitives, screen-reader helpers,
and RTL support. That layering is valuable product evidence: a useful styled
suite needs foundations, state rules, and utilities in addition to component
templates.

The prebuilt assets were already substantial:

| Asset | Archived size | Approximate gzip `-9` |
|---|---:|---:|
| `alpinui.min.js` | 369,789 bytes | 105,772 bytes |
| `alpinui.min.css` | 443,224 bytes | 56,046 bytes |
| `alpinui.js` | 838,158 bytes | 158,726 bytes |
| `alpinui.css` | 561,531 bytes | 67,293 bytes |

These are uncompressed file sizes from an unfinished snapshot, not proposed
Citry budgets. They establish why asset splitting, static-versus-interactive
cost, compressed measurements, and first-interaction work must be designed
before breadth is implemented.

The lower-level packages rebuilt Vue-like concepts over Alpine:

- `alpine-reactivity` added ref, computed, watch, readonly, and related APIs
  over Alpine's exposed reactivity primitives;
- `alpine-composition` added declared props, emitted events, `setup`, lifecycle
  shims, isolation, plugins, and instance magics;
- `alpine-provide-inject` attached provider state to DOM elements;
- `alpine-alpine` exposed the owning Alpine instance.

The `createAlpinui()` framework factory supports selective component and
directive registration, aliases, and instance plugins. Its output tree
contains aggregate UMD and ESM bundles, minified variants, source maps, Labs
bundles, an import map, individual modules, aggregate and per-component CSS,
Sass forwarding files, and generated type work products. Selective
registration and explicit per-component asset inventories are useful ideas,
even though the archived package metadata does not expose them reliably.

The detailed audit found important gaps in those layers: incomplete shallow
and readonly semantics, unstable identity, simplified scheduling, undeclared
runtime coupling, async setup without a readiness contract, and version
coupling to Alpine internals. Citry UI has no reason to recreate Vue fidelity.
The current `$component`, `$c-props`, component-handler, slot-ownership, and
managed-lifecycle contracts cover the product jobs directly.

The Django dependency component follows a much less suitable path. It loads
Alpine, four support packages, the unminified Alpinui bundle, and a global
helper from mutable CDN version ranges without integrity metadata, followed
by inline initialization. Its `minified=True` setting does not select the
Alpinui minified assets. The adapter source also vendors byte-identical copies
of the unminified Alpinui JS and CSS. This is network-dependent,
all-or-nothing delivery rather than the deterministic wheel assets required
for Citry UI.

### 3.3 Theme, defaults, locale, and icons

The styling model is substantially Vuetify 3.6.12's Material-oriented Sass
and utility system. Shared component props cover class, style, color, variant,
density, dimensions, elevation, location, position, rounding, size, theme,
tag, disabled, loading, and model values. Styled variants include elevated,
flat, tonal, outlined, text, and plain.

Runtime themes generate CSS custom properties and color utilities. Light and
dark themes are present by default, named themes can be added, and options
cover generated variants, default-theme choice, disabling, and a CSP nonce.
MD1, MD2, and MD3 blueprints change defaults, shapes, input appearances, and
palettes. Defaults can be global, per family, nested for subcomponents,
scoped, reset, or rooted.

This is strong evidence for tokens, theme providers, nested defaults, and
coherent cross-component variants. It also carries substantial implementation
risk: the Alpinui root unconditionally expects a global `unhead` object that
the Django loader does not provide, so its theme initialization can fail.
Citry UI needs a framework-owned, dependency-declared theme path with no
undeclared browser globals.

The archive contains 43 locale message modules with RTL defaults. Icon
adapters cover MDI font classes, MDI inline SVG aliases, Material Icons, Font
Awesome, and Font Awesome 4, using class, ligature, SVG, or component
renderers. Several Alpine icon modes remained unsupported, and font-based
sets require external CSS or fonts not installed by the Django adapter. The
lesson is to separate semantic icon aliases from rendering adapters and to
make every font, SVG, attribution, and optional dependency explicit.

### 3.4 Django adapter architecture and coverage

The archived adapter is a distinct `django_alpinui` distribution, version
`0.0.4`, declaring Python 3.8+, Django 4.2+, and django-components 0.84+.
Installation placed it in Django's application registry, while consumers
manually rendered the library's CSS and JavaScript components in the page.

Its package includes Python component modules, templates expressed through
Python, generated type information, static assets, and build caches. Its TODO
reports **28 of 172 components implemented and 0 tested**. Visible wrappers
cover parts of Alert, App, AppBar, Avatar, Badge, Banner, Breadcrumbs, Card,
Code, DefaultsProvider, Divider, KeyboardKey, Label, List, LocaleProvider,
NoSsr, and Table, among others.

The generated Python type file is 9,667 lines and models typed static props,
raw-JavaScript props, attributes, and slots. The adapter translates static
values to JSON but inserts values from a separate `js` mapping as Alpine
expressions. Its slot experiment uses Alpine teleport targets and a wrapper
that introduces scoped slot data. Both mechanisms show the desired jobs, but
also show why Citry's native typed props, handler scope, slot ownership, and
graph identity should be the only transport.

The built `0.0.4` wheel is only 6,165 bytes and contains an early subset:
Divider, the Alpinui root, dependency helpers, app/registry files, and
metadata. It omits the generated types, utility modules, bundled assets, and
almost all working-tree templates. The source distribution is similarly
stale. These artifacts cannot validate the later working tree.

The JavaScript package has related distribution defects in this snapshot.
Its `main` points to a Vue framework build, its root and type exports name
files that are absent, and the declared README and changelog are absent.
Hundreds of generated declarations remain in a temporary directory rather
than the exported library. These are archive observations, not claims about
an unpublished later state.

That gap exposes three requirements for `citry-ui`:

1. Python components and browser assets must be released from one coverage
   ledger so a component cannot silently exist on only one side.
2. Generated props or type tables need conformance tests against the actual
   component classes and templates.
3. Registration and asset inclusion should be explicit, deterministic, and
   inspectable rather than depending on manual page fragments and implicit
   framework discovery.

### 3.5 What was valuable

- The category map and the recognition that foundations, utilities,
  component styles, locale, theme, icons, and interaction belong to one
  coherent product.
- A base-versus-runtime-specific source split, which shows an attempt to
  share behavior, together with clear evidence that independently rendered
  DOM still duplicates accessibility and structural work.
- Compound families and internal helpers rather than one monolithic class per
  visual example.
- Generated prop/type infrastructure as an attempt to keep a large catalog
  consistent.
- Prebuilt distribution assets and a separate host adapter.
- Selective registration, aliases, nested defaults, and modular asset output.
- A shared design system spanning tokens, component styles, locale, RTL, and
  icon adapters rather than unrelated widget CSS.
- Measured attention to dense-page initialization cost.

These are design lessons, not endorsements of the exact implementation.

### 3.6 What did not reach a releasable state

| Area | Evidence and consequence |
|---|---|
| Testing | The JavaScript TODO says 0 of 89 ported families were tested and the Django TODO says 0 of its 28 implemented components were tested. The archive has 148 source specs and 57 Cypress specs, but they predominantly mount the inherited Vue components. The 23 Django test files are copied django-components tests that do not exercise `django_alpinui`. Filename presence must not be reported as adapted coverage. |
| Accessibility | Ported markup and click behavior do not establish keyboard, focus, screen-reader, touch, forced-color, RTL, or morph behavior. The work predates the acceptance contract now required by the product charter. |
| Adapter completeness | The Django TODO reports 28 of 172 component names implemented, so the advertised JavaScript suite and Python-consumable suite diverge. Its built wheel contains only a smaller early subset. |
| Renderer drift | Shared TypeScript behavior feeds a Vue DOM renderer but the Alpine engine leaves DOM rendering to handwritten Django templates. Accessibility, slots, structure, classes, and types can diverge across three representations. |
| Runtime coupling | Isolation mutates Alpine's private `_x_dataStack`; other helpers rebuild Vue concepts over Alpine or attach state directly to DOM nodes. This is version-coupled infrastructure that current Citry should own only through its existing tested adapters. |
| Performance source | The remembered initialization improvements survive only in hand-patched distribution bundles, not in the TypeScript sources or published packages. The patches include their own visible defects. |
| Asset cost | The unfinished minified JS and CSS are each hundreds of kilobytes before transfer compression. The Django path loads unminified aggregate bundles and multiple support packages. No evidence establishes production budgets or selective delivery in that host. |
| Theme and icon dependencies | Theme setup expects an undeclared global; several icon modes are incomplete; external icon fonts are not declared or installed by the adapter. |
| Maintenance | The supporting packages had no changelogs or tests, generated/build artifacts were mixed into the snapshot, exports point at absent files, and the main component TODO still described all families as untested. Debugger statements and a global counter remain in the Django helper. |
| Package boundary | Consumers had to coordinate a JavaScript suite, undeclared or loosely versioned browser packages, a partial Django adapter, mutable CDN assets, and manual page inclusion. Version and compatibility guarantees were not evident. |
| Provenance and security | A previously recorded live-looking upload credential must be considered compromised and revoked outside this research. No value is reproduced here. Ported templates still require source-by-source license and provenance clearance. |

## 4. Production application evidence

### 4.1 Scale and recurring component families

The written Events audit covers 38 components with server views: 24 pages,
14 widgets, and three inherited autocomplete endpoints. It records 116
generated endpoint references and 47 `$fetch` call sites
([`audit-context.md`](../events_research/audit-context.md), opening scope).
The browser audit counts 373 component invocations and 51 Alpine roots, with
dense pages capable of reaching hundreds of roots
([`alpine-workproject-audit.md`](../alpinejs/alpine-workproject-audit.md),
"Scale").

Static template-call counts below are lower bounds because Python inline
templates and dynamic invocations are excluded.

| Family | Production components and usage evidence | Reusable requirement |
|---|---|---|
| Actions and icons | Button has at least 78 static calls; Icon has at least 56. Button supports link/button output, disabled state, appearance and semantic color choices, slots, and explicit attrs. | Buttons need semantic element choice, intent, appearance, size, icon placement, loading, disabled behavior, slots, and predictable attributes. |
| Forms | Form, FormLabel, TextInput, and Select recur across create, edit, and delete pages. The wider audit counts 25 Form instances. | Native submission, Event submission, initial values, typed payloads, validation, errors, loading, disabled/editable state, action regions, and dynamic fields must compose. |
| Search and selection | Autocomplete, Multiselect, PillToggle, and domain specializations perform remote search, debounce, keyboard movement, chips, hidden values, and removal. | Combobox and multi-selection are first-class async components, not decorative Select variants. Provider specialization should not fork core behavior. |
| Overlays | At least 10 destructive dialogs, 4 general dialogs, and 3 menus occur in static templates; the broader audit also finds repeated Dialog and Menu use. | Dialog, AlertDialog, Menu, and Popover need activators, controlled state, Escape, outside interaction, focus management, layering, placement, and nested table/tree use. |
| Navigation and disclosure | Breadcrumbs, Tabs, TabItem, TabsStatic, ExpansionPanel, Navbar, Sidebar, and project navigation are recurring. | Local panels, URL-aware navigation, server-fragment navigation, disclosure, responsive shell, and history behavior need distinct documented modes. |
| Data display | Table, TableCell, List, ListItem, Tags, Vote, badges, and activity views recur. At least 10 Table and 22 explicit TableCell calls appear in static templates; the broader audit counts 32 table-related instances. | Tables and lists need cell/row composition, row actions, links, attrs, empty/loading/error states, and dense rendering without assuming ORM objects. |
| Editable collections | Attachments, template attachments, project modules, and process trees combine add/remove, tagging, drag reorder, nested nodes, and external synchronization. | Sortable list, editable collection, and tree are credible later families and immediate pressure tests for identity, morphing, forms, and cleanup. |
| Application shell | Layout, Navbar, Sidebar, Calendar, Bookmarks, and project layouts establish dashboard composition needs. | General shell and navigation primitives belong in the breadth study; domain route maps and page controllers do not. |

The archived Storybook snapshot includes stories for most generic widgets and
many composites. It establishes demand for a browsable catalog with realistic
examples. Static story files do not establish browser interaction,
accessibility, or visual-regression coverage.

### 4.2 Form and server-interaction pressure

Create, edit, and delete forms dominate the audited pages. Recurring needs
include initial values, structured data, loading and disabled state, field and
form errors, destructive confirmation, and redirect or rerender after success.
Attachments, tags, selected events, roles, and modules introduce repeated and
nested values.

The old flat encoding produced comma-joined lists and indexed-field
reconstruction. Current Events typed structured arguments are the appropriate
framework contract. Citry UI should make them easy to use, but must also
preserve ordinary HTML form behavior where the component permits it. Only one
of four literal forms in the audited sample declared a normal action URL;
that application's JavaScript-heavy choice is a warning, not a default to
copy.

Error presentation is inconsistent in the old application. Some forms expose
raw response text and some only log failures. The official library needs a
shared field, description, error, form-summary, loading, and retry contract so
individual components do not invent incompatible failure UI.

### 4.3 Composition and customization pressure

The application relies heavily on typed kwargs and slots. Generic components
often accept a root `attrs` mapping plus named mappings such as
`header_attrs`, `content_attrs`, `activator_attrs`, `item_attrs`, or action
button attrs. Table, Form, Tabs, Dialog, and ExpansionPanel accept rich slot
composition. The Events audit records 138 fills into generic UI components
([`audit-context.md`](../events_research/audit-context.md), section 3).

This supports a consistent library-wide rule for:

- explicit root attributes;
- named-part attributes;
- named slots and compound children;
- semantic intent, appearance, size, density, and state variants;
- documented tokens and parts;
- a headless surface when the styled structure is too prescriptive.

The application does not demonstrate a successful theme system. A few Python
mappings translate semantic colors and appearances into Tailwind classes,
while spacing, typography, brand colors, and state styles remain hardcoded.
There is no coherent density, typography, radius, elevation, motion, dark,
RTL, forced-color, or part-token contract. Override behavior depends on class
merge order and Tailwind specificity rather than documented guarantees.

### 4.4 Accessibility and behavior gaps to use as test cases

The old generic widgets are not suitable accessibility baselines:

- Dialog and Menu lack demonstrated focus trapping, initial focus, focus
  restoration, menu roving focus, arrow navigation, typeahead, and portal
  behavior.
- Dialogs render in place and depend on z-index rather than a defined teleport
  and stacking contract.
- Tabs implement click behavior without the complete ARIA tab and keyboard
  model.
- ExpansionPanel uses a clickable `div` instead of button and disclosure
  semantics.
- Autocomplete lacks a complete combobox/listbox contract, mishandles part of
  its disabled and empty-result rendering, permits stale out-of-order search
  responses, and expands the trust boundary by injecting rich result HTML.
- Shared component tests cover only Dialog and Menu, with no archive evidence
  of browser keyboard, focus, screen-reader, accessibility, or visual tests.

Each item belongs in the future prototype acceptance matrix. None should be
fixed by mechanically translating the old markup.

### 4.5 Bespoke infrastructure Citry UI should eliminate

The application accumulated:

- `$fetch`, `$swap`, and `$loaded` Alpine extensions;
- a Vue-like `defineComponent` layer and 32 named Alpine components;
- three serialization filters, including raw callback expressions;
- slot-scope passthrough conventions;
- a 177-line URL query manager;
- generated per-row action URLs and wrapper components used mainly to carry
  them;
- placeholder identifiers rewritten after client-side creation;
- DOM queries into another component's state in eight files;
- duplicate server-rendered and browser-generated collection rows that need
  manual reconciliation;
- three layers of load-order defense;
- unpinned CDN assets and globally loaded unused HTMX.

The browser audit documents the resulting load-order problems, server/browser
DOM drift, dual-renderer reconciliation, component coupling, flashing,
escaping risk, URL-state complexity, and dead assets
([`alpine-workproject-audit.md`](../alpinejs/alpine-workproject-audit.md),
section 5).

Citry now has direct public contracts for most of these jobs. UI components
should use Events, typed arguments, `$component`, `$c-props`, tag handlers,
stable component identity, graph ownership, fragment assets, morphing, and
managed cleanup instead of recreating application-local transport and
component runtimes.

### 4.6 What belongs to this application only

The following are examples or recipes, not core APIs:

- project phases, modules, outputs, risks, outcomes, feedback notes, status
  updates, and role models;
- Monday, Google Calendar, HubSpot, OAuth, and AI-summary workflows;
- exact attachment, tag, and activity schemas;
- project layouts, permission flags, route maps, and redirect destinations;
- the private color palette and exact Tailwind utility combinations;
- ORM-shaped component inputs and synchronous third-party side effects;
- mutate-then-reload as the ordinary success path.

Absence is not evidence against a component either. This application has no
reusable checkbox, radio group, switch, textarea, tooltip, toast, drawer,
pagination, date picker, skeleton, or generic card. The broader ecosystem
study must fill those blind spots.

## 5. Classification for Citry UI

### 5.1 Reuse as evidence and acceptance pressure

- The observed category taxonomy and usage frequencies.
- Typed inputs, slots, compound families, and explicit root/part attributes.
- Semantic intent, appearance, disabled, loading, and editable concepts.
- Provider specialization for remote selection without behavior forks.
- A browsable catalog with realistic compound and workflow examples.
- Dense repeated-row and tree performance cases.
- The production form, overlay, remote-selection, URL-state, morph, and
  editable-collection workflows as acceptance fixtures.
- The Alpinui separation of foundations, themes, utilities, components,
  locale, icons, and prebuilt distribution assets.

### 5.2 Re-derive from standards and current Citry contracts

| Priority family | Why local evidence supports it |
|---|---|
| Button and IconButton | High use; exercises element choice, attrs, slots, variants, loading, and disabled semantics. |
| Field, Label, Input, Textarea, Select, Checkbox, Radio, Switch | Forms dominate, while the old application lacks a complete consistent control set. |
| Form layout, validation messages, summary, and actions | Repeated create/edit/delete flows need one native and Events-aware error/loading contract. |
| Dialog, AlertDialog, Menu, Popover, Tooltip | Overlays recur and expose the largest focus, keyboard, layering, and lifecycle gaps. |
| Tabs and Disclosure/Accordion | Both local panels and server-backed navigation recur; old semantics are insufficient. |
| Combobox/Autocomplete and MultiSelect | Remote and multiple selection recur, including async race and content-safety failures. |
| Table, List, Badge/Tag, Breadcrumbs, Pagination | Data-heavy application UI needs composition and dense rendering without app-model coupling. |
| Application shell primitives | Layout and navigation recur, but must remain host and route neutral. |
| Alert, Toast, loading, empty, and error feedback | Current failures are inconsistent and often invisible to users. |
| Later editable collection, sortable list, and tree | Strong production pressure exists, but ecosystem research must determine general contracts and v1 timing. |

For every stateful family, the styled and headless surfaces should share one
semantic, accessibility, state, and lifecycle implementation.

### 5.3 Reject from the default library

- Domain pages, project models, ORM contracts, routes, and permission logic.
- Direct ports of archived templates or styling.
- Vue compatibility as a component architecture.
- Alpine private APIs in library code.
- Raw JavaScript expressions passed through Python strings.
- Quote-rewriting serialization and custom transport filters.
- DOM-query based communication between components.
- Per-row endpoint generation as a component requirement.
- Client flags as authorization decisions.
- Full-page reload as the default successful mutation behavior.
- Unpinned CDN dependencies or consumer-side Tailwind, Sass, or Node builds.
- Arbitrary Tailwind utility strings as the primary customization API.
- Claims of suite coverage based on generated or inherited files without
  Python, browser, accessibility, and documentation conformance.

## 6. Requirements carried into the ecosystem study

Phase 3 and later comparison work must test whether candidate libraries help
answer these locally proven needs:

1. How do large suites keep component names, props, events, slots, parts,
   tokens, documentation, tests, and package exports consistent?
2. Which architectures truly share headless behavior with styled output, and
   which merely maintain two similar implementations?
3. How do components preserve native HTML and server-form behavior while
   adding async and client-enhanced interaction?
4. What are the strongest contracts for explicit root and named-part
   attributes, slots, compound children, variants, and tokens?
5. How are focus, keyboard, overlays, portals, async races, IME, touch, RTL,
   forced colors, reduced motion, and server rerenders tested?
6. How do suites split assets so static components stay static and common
   pages do not pay for the complete catalog?
7. How do source-copy, headless, and styled systems balance deep control with
   upgrades and compatibility?
8. What do real users report about theming ceilings, wrapper depth, generated
   markup, form integration, accessibility defects, performance, bundle size,
   documentation, upgrades, and maintenance?

The old archives establish the pressure cases. They do not preselect the
answer, the v1 ordering, the default visual language, or the final pairing API.
