# Phase 3 candidate map and deep-dive corpus

**Snapshot: 2026-07-23. Status: complete; independent Phase 3 review passed.**
This report maps current component-library
architectures before the detailed dossiers begin. Selection favors distinct
delivery and behavior models, relevance to Citry, current maintenance,
adoption evidence, and enough product breadth to test the charter.

The corpus contains twelve dossier-sized work units covering fourteen UI
products plus their load-bearing behavior and Python publishing foundations.
Related products share one dossier and one evidence weight.

## 1. Selection method

Candidates were sampled across six architecture strata:

1. installed styled suites;
2. installed headless accessible primitives;
3. source-copy styled systems;
4. framework-neutral CSS and optional JavaScript;
5. Web Components;
6. server-rendered Python and form-specialist systems.

Selection used these questions:

- Does the project expose a mechanism that is meaningfully different from
  another candidate?
- Is it broad or deep enough to pressure Citry's component model?
- Does it have current releases, usable documentation, and an identifiable
  maintenance story?
- Is there credible adoption evidence beyond the project's own marketing?
- Can its customization and failure modes be evaluated from stable evidence?
- Does it fill a gap in styled/headless pairing, server rendering, forms,
  assets, accessibility, or source ownership?

Framework balance is a coverage check, not a quota. Projects that share a
behavior library or design lineage are marked as related evidence and will
not be counted as independent confirmation.

## 2. Proposed Phase 4 corpus

| Candidate | Ecosystem | Architecture role | Why it is selected | Main question for Citry |
|---|---|---|---|---|
| Vuetify 4 and the v0 direction | Vue | Installed styled full suite plus emerging composable foundation | Essential benchmark for the requested breadth and a direct successor to the local Vuetify-derived experiment | Can a very broad themed suite expose a genuine reusable behavior foundation without duplicating renderer work? |
| PrimeVue 5 with v4 lineage | Vue | Compiled styled and globally unstyled product over one core; final public MIT v4 supplies source lineage | Strong data-heavy catalog, design-token tiers, and named Pass Through parts, with a material current licensing/source boundary | How well does one behavior implementation support both default styling and deep control, and what is lost when its source and redistribution rights close? |
| Reka UI 2 plus Nuxt UI 4 | Vue | Installed headless primitives and their broad installed styled consumer | The pair makes behavior ownership, inherited configuration, styled value, and duplicated work directly comparable | Which contracts belong in the shared primitive, and what value and coupling does the styled product add? |
| Ant Design 6 | React | Installed styled enterprise suite | Extremely broad forms, data, navigation, feedback, token, and enterprise workflow coverage | What makes a suite extensive in practice, and where do large APIs and generated styling become costly? |
| Mantine 9 | React | Installed styled suite with unstyled options and named parts | Close match to the charter: broad, usable defaults, Styles API, and per-component unstyled behavior | Is "unstyled" a real paired authoring contract or mainly a styling switch? |
| Chakra UI 3 plus Ark UI/Zag.js | React | Styled recipes over separately maintained headless components and state machines | Explicit multi-project behavior-to-style layering | What boundaries keep behavior, accessibility, and styled recipes coherent across packages? |
| React Aria Components 1 | React | Installed unstyled accessible components | Strongest interaction, collections, device, internationalization, and accessibility-testing reference | Which behavior and testing contracts transfer to a server-rendered Python component system? |
| Base UI 1, shadcn/ui, and Radix lineage | React | Modern installed headless primitives plus a styled source-copy consumer | Shows the same product jobs across installed behavior, compound lineage, copied assembly, and update tooling | Which benefits are unique to source ownership, and what maintenance and accessibility cost follows? |
| Bootstrap 5 | Framework-neutral | Global CSS plus optional JavaScript plugins | Mature no-build and server-rendered baseline with native markup and long compatibility history | How far can semantic classes, data attributes, Sass, and CSS variables go without a component runtime? |
| Web Awesome 3 | Web Components | Installed styled custom elements with Shadow DOM | Strongest current standards-based cross-framework component package | Do encapsulation and native custom elements help enough to offset upgrade, form, morph, and styling constraints? |
| Django Cotton UI plus Cotton and django-components publishing | Python/Django | Installed styled server-rendered suite plus two Python component distribution models | Closest product peer together with direct evidence for discovery, registry, template, asset, and package ownership | What does a Python-native suite get right, and which publishing contracts or frontend dependencies remain costly? |
| django-formset 2 | Python/Django | Advanced form-specialist renderer plus custom-element runtime | Deepest current Python evidence for collections, uploads, validation, selection, steppers, and rich forms | Which form capabilities belong in UI components, and which would duplicate Citry Events or native forms? |

The corpus deliberately includes both sides of related architectures inside
one dossier:

```text
Reka UI behavior
└── Nuxt UI installed styled product

Ark UI and Zag.js behavior
└── Chakra UI styled recipes
```

Each shared behavior implementation, inherited catalog, and complaint lineage
receives one evidence weight in Phase 5 regardless of how many styled wrappers
or delivery products expose it.

### 2.1 Selection evidence

"Active" means current releases or commits on the snapshot date. Repository
interest is only an adoption signal; it is not a quality score.

| Work unit | License and paid boundary | Maintenance and adoption evidence | Selection result |
|---|---|---|---|
| [Vuetify](https://github.com/vuetifyjs/vuetify) | MIT core; no core component paywall identified | About 41,000 repository stars, long history, active v3/v4 releases; v0 1.0.0 became stable on 2026-07-22 | Select |
| [PrimeVue](https://primevue.dev/migration/v5) | Current v5 compiled packages use Community or per-developer Commercial terms; v4 and earlier remain MIT. Current terms constrain eligibility, seats, updates, and component-library redistribution. | Company-backed current commercial release; about 14,500 stars and broad use apply to the archived public v4 lineage, while current v5 adoption was not established | Select for the distinctive styled/unstyled architecture, treating closed source, procurement, redistribution, and continuity as explicit risks |
| [Reka UI](https://github.com/unovue/reka-ui) + [Nuxt UI](https://github.com/nuxt/ui) | Both MIT; no core component paywall identified | Active 2026 releases, about 6,700 and 6,800 stars; installed headless/styled relationship is documented | Select as one unit |
| [Ant Design](https://github.com/ant-design/ant-design) | MIT core; commercial ecosystem offerings do not gate the component package | Large established repository and active v6 releases | Select |
| [Mantine](https://github.com/mantinedev/mantine) | MIT; no core component paywall identified | Large established repository, active v9 releases and maintained extension packages | Select |
| [Chakra UI](https://github.com/chakra-ui/chakra-ui) + [Ark UI](https://github.com/chakra-ui/ark) + [Zag.js](https://github.com/chakra-ui/zag) | MIT projects; no core component paywall identified | Established Chakra adoption with active multi-project releases | Select as one unit |
| [React Aria](https://github.com/adobe/react-spectrum) | Apache-2.0; no core component paywall identified | Adobe-maintained, established Spectrum use, active monthly release line | Select |
| [Base UI](https://github.com/mui/base-ui) + [shadcn/ui](https://github.com/shadcn-ui/ui) | MIT projects; third-party registries may set their own terms | Base UI stable since late 2025 with frequent releases; shadcn has very high current repository and registry activity | Select as one unit |
| [Bootstrap](https://github.com/twbs/bootstrap) | MIT; no core component paywall | Long-established, very high adoption, active 5.3.x maintenance | Select |
| [Web Awesome](https://github.com/shoelace-style/webawesome) | MIT free core; Pro themes, blocks, and tooling are separate | Active 3.x releases and continuity from archived Shoelace; broad current-package adoption was not established in this scan | Select for the distinct standards-based custom-element mechanism despite incomplete adoption evidence |
| [Django Cotton UI](https://pypi.org/project/django-cotton-ui/) + [Django Cotton](https://pypi.org/project/django-cotton/) + [django-components](https://pypi.org/project/django-components/) | MIT; no core paywall identified | Cotton UI is active but Alpha; Cotton 2.7.2 and django-components 0.151.1 have current 2026 releases; broad adoption of the suite was not established | Select as the closest current Python-native product and as direct publishing evidence despite incomplete suite-adoption evidence |
| [django-formset](https://pypi.org/project/django-formset/) | MIT; no core paywall identified | Production/Stable classifier and active 2.2.x releases; broad adoption was not established | Select because its advanced form and collection contract is otherwise absent from the corpus, while treating adoption as an explicit risk |

## 3. Current breadth scan

Versions below are the current stable release or documented release line on
the snapshot date. Counts are project-defined families or documentation
entries and are not normalized component scores.

### 3.1 React candidates

| Candidate | Current line | Breadth and customization | Phase 3 result |
|---|---:|---|---|
| Material UI | 9.2.0 | Roughly fifty Material components; `sx`, theme defaults/overrides, standardized slots and slot props; advanced grid, dates, charts, and trees in MUI X | Supporting reference. Mature and popular, but its Material and theme evidence overlaps Vuetify while Ant, Mantine, and Chakra add more distinct mechanisms. Keep MUI sources in the complaint and customization comparisons. |
| Ant Design | 6.5.1 | Official overview enumerates more than seventy layout, navigation, data-entry, data-display, and feedback entries; global and component tokens, theme algorithms, semantic structure APIs | Selected work unit. |
| Mantine | 9.4.2 | More than one hundred core entries plus dates, forms, notifications, dropzone, carousel, and other packages; named Styles API, tokens, theme defaults, per-instance styles, unstyled mode | Selected work unit. |
| Chakra UI | 3.36.1 | Broad styled suite using recipes and slot recipes; logic-heavy families compose Ark UI and Zag.js state machines | Selected with Ark UI and Zag.js in one work unit. |
| React Aria Components | 1.19.0 | More than fifty unstyled components including sophisticated collections, dates, color, table, tree, virtualizer, drag-and-drop, and async selection | Selected work unit. |
| Base UI | 1.6.0 | Roughly thirty-six headless families including autocomplete, combobox, drawer, dialogs, menus, forms, number fields, select, and toast | Selected with shadcn/ui and Radix lineage in one work unit. |
| Radix Primitives | Current 1.x packages | Roughly thirty narrow headless families with compound parts, portals, controlled state, `asChild`, and state attributes | Required lineage reference, not a separate scored dossier. Base UI adds newer form and combobox breadth, while shadcn documents Radix's source-layer effect. |
| shadcn/ui | CLI 4.14.0 | Roughly sixty documented components plus blocks; source registry, semantic CSS variables, multiple bases and styles | Selected with Base UI and Radix lineage in one work unit. |

Primary maps:
[Material UI](https://mui.com/material-ui/all-components/),
[Ant Design](https://ant.design/components/overview/),
[Mantine](https://mantine.dev/core/package/),
[Chakra UI](https://chakra-ui.com/docs/components/concepts/overview),
[React Aria](https://react-aria.adobe.com/getting-started),
[Base UI](https://base-ui.com/react/overview/about),
[Radix](https://www.radix-ui.com/primitives/docs/overview/introduction), and
[shadcn/ui](https://ui.shadcn.com/docs/components).

### 3.2 Vue candidates

| Candidate | Current line | Breadth and customization | Phase 3 result |
|---|---:|---|---|
| Vuetify | 4.1.5; `@vuetify/v0` 1.0.0 | More than eighty styled families, application layout, services, themes, defaults, slots, Sass, and tree shaking; v0 ships a stable unstyled component and composable foundation | Selected work unit covering mature styled v4 and newly stable unstyled v0 separately. |
| PrimeVue | 5.0.0 current; 4.5.5 final public MIT line | Current catalog advertises more than ninety forms, overlays, data, navigation, feedback, and layout families; styled/unstyled modes, token tiers, and named Pass Through parts remain public APIs | Selected work unit. Phase 4 corrected the source and license boundary after the Phase 3 gate. |
| Reka UI | 2.10.1 | More than forty unstyled primitive families with Root/Trigger/Content/Item parts, controlled state, slots, data attributes, portals, collection and date utilities | Selected in the shared Reka/Nuxt work unit. |
| Nuxt UI | 4.10.0 | More than 125 styled components and application blocks over Reka and Tailwind CSS 4; global slot/variant theme configuration and per-instance overrides | Selected in the shared Reka/Nuxt work unit. |
| Quasar | 2.22.0 | Styled components plus a larger SPA/SSR/PWA/Electron/mobile framework, application services, gestures, forms, tables, editors, uploads, and layout | Reserve. Valuable for application-shell and multi-platform evidence, but its tooling scope exceeds Citry UI and overlaps Vuetify. |
| Element Plus | 2.14.3 | More than eighty documentation entries with strong enterprise, virtualized, date/time, form, and data controls; BEM, Sass, CSS variables, slots, Config Provider | Reserve. PrimeVue supplies similar enterprise breadth with a more relevant styled/unstyled contract. |
| Headless UI Vue | 1.7.23 | Roughly ten focused headless families using slot props, state attributes, and element control | Historical supporting reference. The Vue package has not followed the active React 2.x line. |
| shadcn-vue | 2.8.0 | Roughly sixty-nine source-owned styled recipes, mostly over Reka, distributed by CLI | Supporting paired reference. shadcn/ui receives the full source-copy dossier; Vue-specific update and Reka composition evidence stays in the Reka/Nuxt report. |

Primary maps:
[Vuetify](https://vuetifyjs.com/),
[PrimeVue](https://primevue.dev/components),
[Reka UI](https://reka-ui.com/),
[Nuxt UI](https://ui.nuxt.com/docs/components/),
[Quasar](https://quasar.dev/components/),
[Element Plus](https://element-plus.org/en-US/component/overview), and
[shadcn-vue](https://www.shadcn-vue.com/docs/components).

### 3.3 Framework-neutral, Web Component, and Python candidates

| Candidate | Current line | Breadth and customization | Phase 3 result |
|---|---:|---|---|
| Bootstrap | 5.3.8 | Broad layout, forms, navigation, feedback, overlays, utilities, Sass, color modes, CSS variables, optional data-API plugins | Selected work unit. |
| daisyUI | 5.7.0 | Sixty-eight CSS-first component recipes, thirty-five built-in themes, Tailwind 4, semantic classes, no runtime dependency | Supporting reference. Use it in CSS-first theming and labb lineage rather than spend a second full CSS slot. |
| Web Awesome | 3.10.0 | Lit custom elements across forms, overlays, navigation, disclosure, carousel, utilities, CSS tokens and parts; free core plus Pro products | Selected work unit. |
| Shoelace | Archived 2026-03-24 | Predecessor to Web Awesome | Lifecycle and migration evidence inside the Web Awesome dossier, not a current candidate. |
| Django Cotton UI | 0.3.2, Alpha | Roughly forty styled components using Django Cotton, Tailwind 4, and Alpine 3; precompiled assets plus source-exposure command | Selected with Cotton and django-components publishing in one work unit. |
| django-components | 0.151.1 | General Django component model with scoped registries, package discovery guidance, template/static ownership, manifests, and library publishing documentation | Selected as the publishing foundation in the Cotton UI work unit, not scored as a UI suite. |
| labb | 0.4.4, Alpha | More than seventy Cotton wrappers around daisyUI, with static and Alpine-enhanced variants | Supporting comparison in Cotton UI and daisyUI material. Its breadth inherits the daisyUI taxonomy. |
| django-formset | 2.2.4 | Advanced Django forms, collections, uploads, rich selection, dialogs, steppers, multiple renderers, custom-element runtime | Selected work unit. |
| django-crispy-forms | 2.6 | Mature form rendering, Python layout objects, separately packaged visual template packs | Supporting mature packaging and form-renderer reference. It has no general component or behavior layer. |
| shadcn_django | 0.24.1 | CLI copies Django Cotton, Tailwind, and Alpine component source into an application | Source-copy sidebar in the shadcn and Cotton reports. |
| django-bootstrap5 | 26.2 | Mature Django tags around Bootstrap forms, messages, pagination, buttons, and assets | Supporting integration example, not a component architecture. |
| Djinn UI | 0.1.11 | Very young Django include/Tailwind registry and visual-tooling direction | Watchlist only; present catalog and maturity are not established. |

Primary maps:
[Bootstrap](https://getbootstrap.com/docs/5.3/getting-started/introduction/),
[daisyUI](https://daisyui.com/components/),
[Web Awesome](https://webawesome.com/docs/components/),
[Django Cotton UI](https://django-cotton.com/ui),
[django-components publishing](https://django-components.github.io/django-components/latest/concepts/advanced/component_libraries/),
[labb](https://pypi.org/project/labbui/),
[django-formset](https://django-formset.fly.dev/), and
[django-crispy-forms](https://django-crispy-forms.readthedocs.io/).

## 4. Architecture relationship map

```text
Installed behavior primitives
├── Reka UI
│   ├── Nuxt UI: installed styled suite
│   └── shadcn-vue: source-owned styled recipes
├── Ark UI + Zag.js
│   └── Chakra UI: installed styled recipes
├── Base UI, Radix, or React Aria
│   └── shadcn/ui: source-owned styled recipes
└── PrimeVue 5 compiled core; public v4 source is lineage evidence
    ├── styled mode: preset and token CSS
    ├── unstyled mode: no built-in theme rules, but library markup remains
    └── Pass Through: named internal attributes, listeners, and classes

CSS behavior and server wrappers
├── Bootstrap CSS + plugins
│   └── django-bootstrap5 and crispy-bootstrap packs
└── daisyUI CSS
    └── labb Django Cotton wrappers + optional Alpine behavior

Custom-element runtime
├── Shoelace: archived predecessor
└── Web Awesome: current successor
```

The map makes three anti-bias rules explicit:

1. Reka, Nuxt UI, and shadcn-vue reveal different delivery layers over related
   behavior. They are not three independent accessibility implementations.
2. shadcn's visual breadth depends on its selected Base UI, Radix, or React
   Aria foundation plus copied assembly code.
3. labb's inventory is useful Python evidence but inherits much of daisyUI's
   taxonomy and styling contract.

## 5. Evidence protocol frozen for Phase 4

Every dossier records:

- snapshot date, exact version or release line, license, paid boundary, and
  maintenance evidence;
- normalized component inventory by the Citry charter categories;
- delivery, dependencies, assets, forms, server rendering, and client state;
- composition through props, events, slots, compound parts, attributes,
  portals, identity, and inherited configuration;
- customization at token, variant, part, markup, behavior, and source levels;
- accessibility claims separately from reproduced or source-backed behavior;
- concrete shortcomings, affected workflows, current status, workaround,
  recurrence, impact, and evidence confidence;
- mechanisms worth adopting, non-transferable mechanisms, and pressure on
  Citry's public contracts.

The ten Phase 4 dimensions in the controlling plan are normative and may not
be shortened to the summary above. In particular, each dossier must explicitly
cover:

- keyboard, focus, touch, screen-reader, reduced-motion, forced-colors, RTL,
  and direction behavior;
- native form submission, validation, loading, errors, and asynchronous state;
- content trust, escaping, URL and attribute forwarding, files, generated IDs,
  remote results, and component-specific threat cases;
- CSS and JavaScript delivery, build requirements, icons, fonts, CSP, payload,
  upgrade cost, and dependency boundaries.

Every material claim, not only a complaint, carries a direct stable citation
and is labeled as current documentation, source observation, reproduction,
user report, or inference. The dossier also records its confidence,
counterevidence, and unresolved questions. Catalog and version claims cite the
current catalog or release source; license, dependency, accessibility, and
architecture claims cite the corresponding authoritative source. Unsupported
marketing language remains a claim and cannot be restated as verified fact.

### 5.1 Shared comparison slice

The catalog census covers every documented family. Detailed behavior analysis
uses the same risk-bearing slice wherever the library ships an equivalent:

1. Button;
2. Field and Input;
3. Dialog;
4. Combobox or the closest searchable Select;
5. Tabs;
6. Table or Data Table;
7. one form or collection workflow that exercises validation, dynamic items,
   selection, upload, or asynchronous state;
8. the provider or ambient-context mechanism used for theme, direction,
   defaults, services, or other inherited values.

A dossier may add at most two library-specific probes when a distinctive
family would otherwise disappear, such as a date picker, virtualizer, command
palette, form collection, or application layout. Missing members of the shared
slice are findings, not reasons to substitute several favorable components.

The provider comparison records nesting and shadowing, defaults and overrides,
reactive updates, server-to-client agreement, portal or teleport behavior,
lifecycle cleanup, and diagnostics. For Citry it states whether the evidence
pressures `$component.init()` methods, `$provide`/`$inject` Alpine magics, both,
or neither. It does not choose a locale contract; locale and translation
architecture remain follow-up work.

### 5.2 Complaint sample and confidence

Each work unit seeks three to five de-duplicated material complaint patterns from the
twenty-four-month window ending on the snapshot date, 2024-07-23 through
2026-07-23. Older reports may establish lineage only when current docs, source,
an open issue, or a current reproduction shows that the behavior still exists.
If fewer than three credible patterns survive verification, the dossier records
the searches and the shortfall instead of filling the quota with weak claims.

Combined work units log complaint searches for every named product,
user-facing layer, and load-bearing foundation. Retention remains three to five
patterns for the combined unit after de-duplicating shared state machines,
inherited implementation, migration ancestry, and the same report repeated
across trackers. The search log therefore cannot silently substitute Nuxt UI
for Reka UI, Chakra for Ark UI or Zag.js, shadcn/ui for Base UI or Radix, or
Cotton UI for Cotton or django-components.

For each pattern, record the exact query, stable URL, report and update dates,
affected versions or current line, affected workflow, maintainer response,
workaround, recurrence, current status, impact, and one of these confidence
grades:

| Grade | Minimum evidence |
|---|---|
| A | Current official documentation or source, or a current reproduction. |
| B | A current maintainer-confirmed issue, discussion, response, or accepted limitation. |
| C | Recurring independent current reports without stronger confirmation. |
| D | A single unverified report. Useful as a search lead, not as a synthesis finding. |

The complaint register classifies each retained item as a current limitation,
current defect, recurring friction with a workaround, resolved history,
deliberate trade-off, preference, or unverified claim. Phase 5 may use grades A
through C as evidence, clearly labeled. Grade D cannot support a conclusion by
itself. Project issues and discussions are user reports, not confirmed defects
until the stronger evidence above corroborates them. Raw and
popularity-normalized complaint counts will not be used as quality scores.

### 5.3 Evidence de-duplication

The evidence unit for synthesis is the underlying implementation, state
machine, token catalog, publishing mechanism, or complaint ancestry, not the
number of products that wrap it. A pattern may be displayed under every
product where users encounter it, but it receives one comparative weight when
those products inherit the same implementation. Independent wrapper behavior
or independently reproduced outcomes may receive separate weight when the
dossier demonstrates the difference.

## 6. Phase 4 work order and corpus boundary

Deep dives proceed in architecture order so later reports can ask sharper
questions:

1. styled and styled/unstyled suites;
2. installed headless foundations;
3. installed styled-over-headless pairs;
4. source-copy delivery;
5. CSS and Web Components;
6. Python server-rendered and form-specialist systems.

The ecosystem scans ran in parallel, so the plan's sequential two-candidate
saturation rule was not measured and no saturation claim is made. Instead,
Phase 3 bounds the work at the twelve de-duplicated units in section 2. The
reserves add breadth or counterevidence but not enough distinct architecture to
displace one of those units. A later candidate enters Phase 4 only if it exposes
a component category, delivery architecture, customization mechanism, or
failure mode missing from all twelve; adding it requires recording which unit
it replaces or explicitly expanding the approved corpus.
