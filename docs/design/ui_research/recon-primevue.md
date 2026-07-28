# PrimeVue reconnaissance

Status: Phase 4 dossier
Snapshot: 2026-07-23
Complaint window: 2024-07-23 through 2026-07-23

PrimeVue is valuable comparative evidence because one broad catalog supports
styled and unstyled use. The current product boundary is unusually important:
PrimeVue 5.0.0 is a compiled, non-public-source PrimeUI product under Community
or Commercial terms. PrimeVue 4.5.5 is the final MIT line and remains useful as
implementation-lineage evidence, but it is not the current product.

## Evidence register

| ID | Finding and stable citation | Evidence type | Confidence | Counterevidence and unresolved questions |
|---|---|---|---|---|
| P1 | PrimeVue 5 is the first PrimeUI release. Its public APIs are presented as compatible with v4, but its compiled packages use Community or Commercial licensing; v4 and earlier remain MIT. [v5 migration](https://primevue.dev/migration/v5), [PrimeUI announcement](https://primeui.dev/nextchapter) | Current official documentation | High | The v5 implementation source is not public, so API claims and observed runtime behavior cannot receive the same source audit as v4. |
| P2 | The current catalog advertises 90+ components and lists the 91 normalized families below. [v5 catalog](https://primevue.dev/components) | Current official catalog | High | PRO products are separate and excluded. Catalog entries sometimes combine behavior that another library splits into primitives. |
| P3 | Styled and unstyled modes use the same component core. Styled mode adds token-generated rules; unstyled mode omits those variables and rules while retaining library markup, behavior, and accessibility. [styled guide](https://primevue.dev/theming/styled), [unstyled guide](https://primevue.dev/theming/unstyled) | Current official documentation | High | Unstyled is not a separately versioned headless or markup-ownership contract. |
| P4 | Themes use primitive, semantic, and component tokens, presets, light/dark schemes, runtime updates, optional CSS layers, and a 16px v5 base with 14px compatibility presets through June 2027. [styled guide](https://primevue.dev/theming/styled), [v5 migration](https://primevue.dev/migration/v5) | Current official documentation | High | Generated ordering remains difficult to debug; the current complaint register includes a v5 theme-loading failure. |
| P5 | Pass Through maps global or local values onto named internal DOM sections and accepts attributes, listeners, classes, functions, and lifecycle hooks. [Pass Through guide](https://primevue.dev/passthrough), [configuration guide](https://primevue.dev/configuration) | Current official documentation | High | Named parts couple consumers to internal structure; v5 implementation and coverage cannot be independently audited. |
| P6 | v5 documents one application-wide config for license, theme, unstyled mode, Pass Through, CSP, z-index, locale, and interaction defaults. The v4 implementation used a reactive app provider plus separate service providers. [configuration guide](https://primevue.dev/configuration), [v4.5.5 config source](https://github.com/primefaces/primevue/blob/4.5.5/packages/core/src/config/PrimeVue.js) | Current docs plus historical source lineage | Medium-high | No supported nested configuration provider was found. Private v5 internals may have changed despite public compatibility. |
| P7 | Overlays support configurable append targets and the current configuration guide warns that teleported DOM may not inherit ancestor styling classes. v4 source confirms the portal lineage. [configuration guide](https://primevue.dev/configuration), [v4.5.5 portal source](https://github.com/primefaces/primevue/blob/4.5.5/packages/primevue/src/portal/Portal.vue) | Current docs plus historical source lineage | High | Shadow-root, nested-overlay, and provider-shadowing behavior still needs reproduction on v5. |
| P8 | PrimeVue publishes component-specific ARIA and keyboard sections and an accessibility guide. [accessibility guide](https://primevue.dev/guides/accessibility), [DataTable guide](https://primevue.dev/datatable) | Current official documentation | Medium | The guide combines a broad accessibility claim with aspirational language about reaching a high level; it is not a WCAG 2.2 conformance report. |
| P9 | PrimeVue Forms coordinates form state, resolvers, validation timing, Form and FormField, and named PrimeVue controls. [forms guide](https://primevue.dev/forms) | Current official documentation | High | Native serialization, constraint validation, reset, autofill, and no-JavaScript behavior remain component-specific. |
| P10 | Tooltip escapes text by default and exposes rich HTML through `escape=false`. [Tooltip guide](https://primevue.dev/tooltip) | Current official documentation | High | The rich-content opt-out intentionally shifts sanitization responsibility to the application. |
| P11 | v5 accepts a CSP nonce, runs license validation offline, and claims no telemetry. [configuration guide](https://primevue.dev/configuration), [PrimeUI security](https://primeui.dev/security) | Current official documentation | High for documented behavior | Generic Vite SSR theme extraction was unresolved in the last public v4 tracker; a clean v5 reproduction requires the licensed package. |
| P12 | Community eligibility requires every threshold: under $1M revenue, fewer than five developers, fewer than ten employees, and never more than $3M outside capital. It has at most four seats and annual renewal. Commercial is per developer, including users of wrappers. [Community license](https://primeui.dev/licenses/community), [Commercial license](https://primeui.dev/licenses/commercial), [pricing](https://primeui.dev/pricing) | Current license terms and pricing | High | Terms may change. Legal applicability and OEM redistribution require counsel, not this technical dossier. |

## 1. Snapshot, boundaries, dependencies, and maintenance

The audited current release is PrimeVue 5.0.0 [P1]. The historical
`primefaces/primevue` repository was archived on 2026-06-28 after 4.5.5, and
PrimeUI states that current major sources are non-public by design. Community
users receive docs, changelogs, known issues, forum, and Discord; paid users
receive a support portal. This is active commercial maintenance, but removes
public implementation audit and moves community defects from an issue tracker
to Discussions.

The Community license is free only while every eligibility rule holds, has a
four-seat ceiling, and renews annually. Commercial launched at $599 per
developer through 2026, with a stated $799 price from 2027 and one year of
updates [P12]. A Citry wrapper would not reduce seat requirements. The license
also restricts redistribution as a component library, so PrimeVue is prior art,
not reusable implementation for `citry-ui`.

PRO Scheduler, Text Editor, Task Board, Charts, and roadmap-heavy DataGrid,
Gantt, Diagram, and PDF Viewer are separate specialist products. They do not
set Citry's default scope.

## 2. Normalized component inventory

The census uses the current v5 catalog [P2], not the archived v4 source. It
contains 91 entries in ten official categories.

| Official category | PrimeVue 5.0.0 families |
|---|---|
| Form (28) | AutoComplete, CascadeSelect, Checkbox, DatePicker, FloatLabel, IconField, IftaLabel, InputColor, InputGroup, InputNumber, InputOtp, InputPassword, InputTags, InputText, KeyFilter, Knob, Label, Listbox, Mask directive, RadioButton, Rating, Select, SelectButton, Slider, Textarea, ToggleButton, ToggleSwitch, TreeSelect |
| Button (3) | Button, SpeedDial, SplitButton |
| Data (10) | DataTable, DataView, OrderList, OrgChart, Paginator, PickList, Timeline, Tree, TreeTable, VirtualScroller |
| Panel (11) | Accordion, Card, DeferredContent, Divider, Fieldset, Panel, ScrollArea, Splitter, Stepper, Tabs, Toolbar |
| Overlay (7) | ConfirmDialog, ConfirmPopup, Dialog, Drawer, DynamicDialog, Popover, Tooltip |
| File (1) | FileUpload |
| Menu (9) | Breadcrumb, CommandMenu, ContextMenu, Dock, MegaMenu, Menu, Menubar, Sidebar, TieredMenu |
| Messages (2) | Message, Toast |
| Media (3) | Carousel, Compare, Gallery |
| Misc (17) | AnimateOnScroll, Avatar, Badge, BlockUI, Chip, Fluid, FocusTrap, Inplace, MeterGroup, ProgressBar, ProgressSpinner, Ripple, ScrollTop, Skeleton, StyleClass, Tag, Terminal |

v5 adds CommandMenu, Compare, Gallery, InputTags, InputPassword, InputColor,
Sidebar, and ScrollArea, and rebuilds Carousel around a compound API [P1].
Column, row, tab, step, and carousel subparts are structural pieces rather than
additional top-level catalog families. Services and directives enlarge the
runtime surface. DataTable, OrgChart, and Terminal illustrate why catalog count
does not determine Citry's minimum: domain-heavy grids and specialist tools can
stay companion packages.

## 3. Composition, state, identity, and portals

| Frozen probe | Finding |
|---|---|
| Button | Native-button-oriented props, loading, icons, label/default slots, events, and Pass Through parts. Consumers still own the intended form `type`. |
| Field and Input | InputText remains close to native input. FormField, labels, masks, numbers, dates, and selectors add formatting and validation; attribute destinations depend on each root/input split. |
| Dialog | Controlled visibility, header/default/footer slots, modal and dismissal policy, focus behavior, responsive sizing, and a configurable append target. |
| Combobox | AutoComplete is the searchable-input equivalent. Select and TreeSelect cover other ownership shapes; remote search, request ordering, and stale-result policy stay application-owned. |
| Tabs | Compound Tabs, TabList, Tab, TabPanels, and TabPanel expose structure around controlled value. |
| Table and DataTable | There is no separate simple Table family. DataTable owns sort, filter, select, edit, group, paginate, export, virtualize, and lazy-load workflows. |
| Workflow probe | Forms coordinates validation and field state; FileUpload and lazy DataTable expose async callbacks. Cancellation, retry, and stale-result rejection remain external [P9]. |
| Provider | Application config supplies theme, unstyled mode, Pass Through, CSP, z-index, locale, and interactions [P6]. Toast, confirmation, and dialog services add distinct context. |

Props and emits are the state API, slots replace content, and Pass Through
targets internal nodes [P5]. Item identity, event forwarding, and root
attributes remain per-component contracts. Portals retain Vue ownership but can
leave CSS ancestry [P7].

| Provider concern | PrimeVue behavior | Citry implication |
|---|---|---|
| Nesting and shadowing | Current docs expose application-wide configuration; no nested equivalent was found [P6]. | Do not copy a singleton-only limit. |
| Defaults and overrides | Global and local Pass Through merge via documented `mergeSections` and `mergeProps` options [P5]. | Publish one deterministic precedence table. |
| Reactivity | v4 lineage used reactive config and watched theme changes; v5 behavior is documented but its internals are private. | Test inherited Citry updates as a public contract. |
| SSR agreement | Runtime style generation and generic SSR collection need a v5 reproduction [P11]. | Provider state and critical CSS must agree before activation. |
| Portals | Append targets are configurable and CSS ancestry can change [P7]. | Scope follows logical ownership; styles cannot require local ancestry. |
| Cleanup | v4 cleaned config watchers; other services owned global listeners. v5 cleanup is not source-auditable. | Require disposal tests for every provider and service. |
| Diagnostics | Effective token and part provenance is difficult to inspect. | Expose missing-provider and resolved-value diagnostics. |

This pressures both Citry surfaces: `$component.init()` needs the internal scoped
primitive, and `$provide`/`$inject` should expose that same registry to
application-authored headless markup.

## 4. Customization and styled/headless implications

PrimeVue's ladder is preset, primitive/semantic/component tokens, color scheme,
CSS layer, variants, global defaults, Pass Through parts, local classes, slots,
unstyled mode, then wrappers [P3-P5]. Aura, Material, Lara, and Nora are shipped
presets. The semantic token taxonomy and named-part escape hatch are strong
ideas.

The limitation is structural. Unstyled mode removes built-in theme variables
and rules but preserves library markup and behavior [P3]. It is therefore not a
separate headless contract. Citry should publish styled renderers and supported
headless parts over shared state and interaction logic. Part names should be
few, semantic, versioned, and contract-tested rather than mirror every wrapper.

## 5. Accessibility, input modes, direction, and motion

PrimeVue documents keyboard and ARIA behavior per component [P8]. Complex
controls cover focus management, selection, live regions, pointer/touch input,
and configurable RTL. Documentation is useful evidence, not conformance proof.

For Citry, gate each shared-slice component with axe-core, APG keyboard scripts,
focus assertions, touch/pointer runs, forced-colors and reduced-motion
snapshots, RTL interaction tests, IME composition cases, and manual
VoiceOver/NVDA/TalkBack passes. Lighthouse should catch page-level regressions
but cannot certify a component, focus sequence, or assistive-technology
interaction. Nested overlays and portal focus deserve dedicated matrices.

## 6. Forms, validation, loading, errors, and async behavior

Forms provides resolver-driven validation, trigger selection, field metadata,
errors, submission, Form, and FormField [P9]. Rich controls expose `name`,
disabled, invalid, loading, and message integrations, but are not automatically
equivalent to native controls. Test FormData, Enter submission, reset, autofill,
constraint validation, focus-on-error, server-error hydration, and
JavaScript-disabled fallback.

AutoComplete queries, lazy DataTable, FileUpload, and component loading states
cover many presentations. They do not define abort, deduplication, request
ordering, retry, or stale-result rejection. Those remain application or
framework responsibilities.

## 7. Content trust and threat cases

Normal Vue interpolation escapes labels. Tooltip's `escape=false` path is a
trusted-HTML API [P10]. Pass Through deliberately forwards arbitrary attributes
and listeners to internals [P5]. FileUpload client filters remain usability
checks, never server enforcement. Remote labels, table cells, CSV export, URLs,
filenames, and server validation messages all need hostile-input tests.

Citry should default to safe text, use a clearly named trusted-fragment escape
hatch, validate schemes for library-owned navigation, generate deterministic
IDs, and state server-validation ownership. It should not copy a boolean that
quietly changes the sink from text to HTML.

## 8. Delivery, assets, CSP, payload, and upgrades

PrimeVue 5 requires Vue, npm tooling, a license key, and a compiled package.
Styled mode generates theme CSS; unstyled mode still needs Vue and consumer CSS.
PrimeIcons or slots provide icons. The runtime claims zero third-party
dependencies, offline Ed25519 license checks, npm provenance, and no telemetry
[P11]. A missing, invalid, or expired Community key may show a license notice
[P12].

Current route payload and private implementation cannot be inferred from the
old 4.5.5 npm archive. Measure the frozen slice in licensed v5 styled and
unstyled builds, including core, theme, icons, CSS, services, fonts, and lazy
chunks. Upgrade tests should pin tokens, CSS order, supported part names,
semantic DOM, form serialization, provider/portal behavior, and keyboard
traces. Source closure and public-tracker closure make reproducible black-box
contracts and vendor continuity planning more important.

## 9. Complaint register

These patterns separate current v5 evidence from last-public-line v4 evidence.

| Pattern | Evidence, dates, and affected line | Workflow, response, workaround, recurrence, status, impact | Grade |
|---|---|---|---|
| License and source transition raises adoption and continuity cost | PrimeUI announced the dual license and non-public source in June 2026; current [Community terms](https://primeui.dev/licenses/community), [Commercial terms](https://primeui.dev/licenses/commercial), and [pricing](https://primeui.dev/pricing) define seat, eligibility, renewal, redistribution, and update limits. | This is deliberate policy, not a defect. Small teams can use Community; v4 stays MIT. Teams crossing any threshold must buy seats, wrappers still require downstream developer seats, and current implementation audit/forking is unavailable. Current, high procurement and continuity impact. | A |
| One failed first theme load can suppress a component's CSS for the session | [Discussion #4835](https://github.com/orgs/primefaces/discussions/4835), opened 2026-07-16 on 5.0.0-rc.2 and also observed on 4.5.5; maintainer acknowledged it on 2026-07-17. | Reporter supplied root-cause analysis and a manual loader workaround. Trigger involves render-time state churn and is not yet minimal, which is counterevidence. Current report, potentially high visual impact. | B |
| Generic Vite SSR omitted initial theme styles on the last public line | [v4 issue #7289](https://github.com/primefaces/primevue/issues/7289), opened 2025-02-20 and unresolved when the repository was archived. | Server output could flash unstyled until hydration. Reporter supplied a collector; Nuxt integration is counterevidence for framework-specific support. Historical v4 lineage, unresolved on v5 without reproduction, high SSR impact. | C |
| DataTable grouping and virtualization conflicted on the last public line | [v4 issue #4109](https://github.com/primefaces/primevue/issues/4109), repeated on 4.2.4, 4.3.6, and source-analyzed on 4.5.5; an unmerged fix PR was linked 2026-05-18. | Group headers, collapsed rows, spacers, and sticky behavior drifted on large data. Workaround was disabling grouping or virtualization. Recurrent v4 defect; v5 status is not publicly verifiable, high correctness/performance impact. | C |
| Formatted manual input and form submission disagreed on the last public line | [v4 issue #7545](https://github.com/primefaces/primevue/issues/7545), opened 2025-03-28 and unresolved at archive, with related DatePicker reports. | Partially typed dates could mutate or submit the wrong representation. Parsing on input/blur was the workaround. Recurrent v4 form defect; v5 status needs black-box reproduction, high correctness impact. | C |

### Complaint search log

Current product and support surface:

- PrimeFaces Discussions, PrimeVue category, sorted by latest, inspected
  2026-07-23: `https://github.com/orgs/primefaces/discussions/categories/primevue?discussions_q=sort%3Adate_created`
- GitHub Discussions search: `org:primefaces category:PrimeVue created:2024-07-23..2026-07-23`
- web search: `site:github.com/orgs/primefaces/discussions PrimeVue theme CSS v5`
- web search: `site:github.com/orgs/primefaces/discussions PrimeVue accessibility keyboard focus`
- web search: `site:github.com/orgs/primefaces/discussions PrimeVue forms DatePicker input`
- web search: `site:github.com/orgs/primefaces/discussions PrimeVue DataTable virtual`
- web search: `site:primeui.dev PrimeUI license source public community commercial`

Last public implementation line:

- `repo:primefaces/primevue is:issue created:2024-07-23..2026-07-23 sort:comments-desc`
- `repo:primefaces/primevue is:issue created:2024-07-23..2026-07-23 (accessibility OR aria OR keyboard OR focus)`
- `repo:primefaces/primevue is:issue created:2024-07-23..2026-07-23 (theme OR css OR token OR preset)`
- `repo:primefaces/primevue is:issue created:2024-07-23..2026-07-23 (form OR validation OR resolver)`
- `repo:primefaces/primevue is:issue created:2024-07-23..2026-07-23 (DataTable OR virtual OR lazy)`
- `repo:primefaces/primevue is:issue created:2024-07-23..2026-07-23 (PassThrough OR passthrough OR PT)`
- `repo:primefaces/primevue is:issue created:2024-07-23..2026-07-23 (SSR OR hydration OR FOUC)`
- lineage check: `repo:primefaces/primevue is:issue 4109 7289 7545`

Named foundation/layer searches:

- PrimeUIX: `repo:primefaces/primeuix is:issue created:2024-07-23..2026-07-23 (theme OR styled OR token OR css)`
- PrimeIcons: `repo:primefaces/primeicons is:issue created:2024-07-23..2026-07-23`
- PrimeUI PRO: `site:primeuipro.dev Vue Scheduler Charts Text Editor Task Board`
- Vue: `repo:vuejs/core is:issue created:2024-07-23..2026-07-23 (teleport OR provide OR inject)`

No separate foundation complaint was retained when it lacked a verified link to
PrimeVue behavior. Unresolved: obtain licensed v5 bytes and reproduce the
shared slice for accessibility, forced colors, RTL, IME, SSR, native forms,
payload, provider cleanup, portals, and the three v4-line defects.

## 10. Transfer to Citry

### Adopt

- A polished, broad catalog with coherent states and one token vocabulary.
- Primitive, semantic, and component token layers.
- Stable named parts, global defaults, and local overrides with explicit merge
  rules.
- Consistent pending, invalid, empty, and error presentations.
- Rich data and form workflows as design input, with specialist products kept
  in companions.

### Do not transfer

- Unstyled as a synonym for headless while markup remains library-owned.
- A singleton-only provider, unbounded internal-node exposure, or opaque merge
  provenance.
- Runtime theme generation, Vue, Node, Tailwind, or a license key as Citry user
  requirements.
- Client validation as a substitute for native submission and server checks.
- A boolean that switches safe text to raw HTML.
- A license or distribution model that prevents Citry users from auditing,
  redistributing, or maintaining the default library.

### Citry contract pressure

PrimeVue pressures `$component.init()` provider methods and
`$provide`/`$inject` magics backed by one lexically scoped reactive registry. It
also pressures stable contracts for tokens, variants, parts, attributes,
portal targets, service cleanup, native forms, generated IDs, trusted content,
async states, and black-box upgrade tests. The strongest lesson is to share
behavior between styled and headless renderers while granting real markup
ownership only through supported headless parts.
