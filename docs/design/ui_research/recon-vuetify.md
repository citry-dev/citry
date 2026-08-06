# Vuetify reconnaissance

Status: Phase 4 dossier
Snapshot: 2026-07-23
Complaint window: 2024-07-23 through 2026-07-23

This dossier treats Vuetify 4.1.5 and `@vuetify/v0` 1.0.0 as separate
products. Vuetify 4 is the mature styled library. `@vuetify/v0` is the newly
stable unstyled primitives and composables package, and its site describes it
as the foundation for a future Vuetify rebuild. Evidence from one is not proof
about the other.

## Evidence register

Material findings below cite an evidence ID. Confidence means confidence that
the finding is described accurately, not a general quality score.

| ID | Finding and stable citation | Evidence type | Confidence | Counterevidence and unresolved questions |
|---|---|---|---|---|
| V1 | Vuetify 4.1.5 is MIT licensed and declares Vue 3.5 or later, with optional Vite and webpack plugins and TypeScript support. [Tagged manifest](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/package.json) | Source observation | High | Peer compatibility does not establish the minimum browser set or usable payload. |
| V2 | The 4.1.5 source publishes a large styled catalog, plus component-level Sass and tests. [Tagged component tree](https://github.com/vuetifyjs/vuetify/tree/v4.1.5/packages/vuetify/src/components) | Source observation | High | Source directories include structural helpers and aliases, so this dossier inventories families rather than claiming a marketing count. |
| V3 | `@vuetify/v0` 1.0.0 is MIT licensed, requires Vue 3.5 or later, and exposes unstyled components and composables. The stable release was published on 2026-07-22 and promoted its component spine and v1 set to stable. [Tagged manifest](https://github.com/vuetifyjs/0/blob/v1.0.0/packages/0/package.json), [v1.0.0 release](https://github.com/vuetifyjs/0/releases/tag/v1.0.0), [official positioning](https://0.vuetifyjs.com/introduction/why-vuetify0) | Current release, documentation, and source observation | High | The stable label applies to v0's selected v1 surface, not to feature parity with mature Vuetify 4. The documentation's component and composable counts can move independently of the tag. |
| V4 | Vuetify 4 supports direct component imports and plugin registration; icons are separately configured. [Installation guide](https://vuetifyjs.com/en/getting-started/installation/), [framework source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/framework.ts), [icon source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/composables/icons.tsx) | Current documentation and source observation | High | Actual tree shaking depends on the consumer build. No browser-bundle reproduction was run here. |
| V5 | `createVuetify()` creates reactive defaults, display, theme, icon, locale, date, and navigation services, provides them to the Vue app, updates display after SSR hydration, and stops the theme effect scope on app unmount. [Framework source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/framework.ts) | Source observation | High | The source covers app-level lifecycle. It does not prove correct behavior for every nested provider and portal combination. |
| V6 | Defaults use a reactive ancestor chain with global, named-component, nested-subcomponent, scoped, reset, and root behavior; explicit props win. [Defaults source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/composables/defaults.ts), [provider source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VDefaultsProvider/VDefaultsProvider.tsx) | Source observation | High | Deep merging is powerful but makes the effective value harder to inspect. There is no equivalent Citry diagnostic yet. |
| V7 | Theme and locale can be shadowed below the app provider; theme CSS is generated into a nonce-capable style element. [Theme source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/composables/theme.ts), [theme provider](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VThemeProvider/VThemeProvider.tsx), [locale source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/composables/locale.ts) | Source observation | High | Runtime-generated CSS adds CSP and server/client-ordering obligations. Locale architecture is explicitly outside Citry's current decision scope. |
| V8 | Overlays accept an attach target and use Vue Teleport; dialogs add modal semantics, focus containment, and focus restoration. [Overlay source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VOverlay/VOverlay.tsx), [dialog source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VDialog/VDialog.tsx), [browser tests](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VDialog/__tests__/VDialog.spec.browser.tsx) | Source observation | High | Browser tests are stronger than documentation, but this dossier did not repeat screen-reader and nested-overlay testing. |
| V9 | Vuetify documents keyboard and semantic-HTML accessibility goals, while component source and browser tests cover concrete focus and keyboard paths. [Accessibility guide](https://vuetifyjs.com/en/features/accessibility/), [combobox browser tests](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VCombobox/__tests__/VCombobox.spec.browser.tsx) | Current documentation and source observation | Medium-high | This is not a WCAG conformance report. Forced-colors, reduced-motion, touch, RTL, and assistive-technology coverage are uneven by component. |
| V10 | `VForm` coordinates registered controls and synchronous or promise-returning rules; native submit is possible when the developer uses a submit button. [Form source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/composables/form.ts), [form component](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VForm/VForm.tsx), [submit tests](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VForm/__tests__/VForm.spec.cy.tsx) | Source observation | High | Enhanced validation is client-side. Behavior without JavaScript falls back only where rendered markup remains native and server validation is implemented. |
| V11 | Most user content is rendered through Vue text and slots, but generated CSS is assigned to `style.innerHTML`, and calendar translated “more” content is assigned to element `innerHTML`. [Theme source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/composables/theme.ts), [calendar source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VCalendar/composables/calendarWithEvents.tsx) | Source observation | High | Theme CSS is library-generated. Calendar locale messages are normally application-authored, but the API needs a documented trust boundary if messages can be tenant supplied. |
| V12 | The published npm artifacts are large package archives: the registry metadata for 4.1.5 reports about 67.4 MB unpacked across 2,184 files; v0 1.0.0 reports 4,583,470 bytes across 173 files. [Vuetify package](https://www.npmjs.com/package/vuetify/v/4.1.5), [`@vuetify/v0` package](https://www.npmjs.com/package/@vuetify/v0/v/1.0.0) | Registry observation | High | Unpacked package size is not shipped browser payload. Route-level CSS and JavaScript measurements remain unresolved. |
| V13 | All three v0 audit defects retained below are still present in the v1.0.0 tag and remain open in the 1.0.x milestone one day after stable release: dangling dialog/progress ID references, the Snackbar `status`-only synchronous live region, and incomplete non-native button semantics. [Issue 608](https://github.com/vuetifyjs/0/issues/608), [issue 615](https://github.com/vuetifyjs/0/issues/615), [issue 616](https://github.com/vuetifyjs/0/issues/616), [tagged Dialog source](https://github.com/vuetifyjs/0/blob/v1.0.0/packages/0/src/components/Dialog/DialogContent.vue), [tagged Snackbar source](https://github.com/vuetifyjs/0/blob/v1.0.0/packages/0/src/components/Snackbar/SnackbarRoot.vue), [tagged Button source](https://github.com/vuetifyjs/0/blob/v1.0.0/packages/0/src/components/Button/ButtonRoot.vue) | Maintainer-authored audit plus stable-tag source observation | High | The release contains many other accessibility fixes, so these findings do not characterize the entire package. Later 1.0.x patches may resolve them. |

## 1. Snapshot, boundaries, dependencies, and maintenance

Vuetify 4.1.5 is a styled Vue 3 library under MIT. Its manifest and tagged
source are the baseline for all mature-product findings [V1, V2]. The library
has no paid runtime boundary in the package. Commercial support and ecosystem
offerings are not necessary to use its components, but their terms were not
scored.

The mature package contains its own styles and framework services. Its direct
consumer peers are Vue and optional build plugins; icons are configured as a
distinct concern [V1, V4]. The npm archive is not a useful proxy for a Citry
browser budget, but its size reinforces the need to measure per-route imports,
CSS, and icon choices rather than quote one headline number [V12].

`@vuetify/v0` 1.0.0 is a separate stable unstyled package under MIT [V3]. Its
optional peer surface includes feature-specific packages such as Temporal,
color tooling, and `vue-i18n`; those dependencies do not make every feature
mandatory. The correct comparison is “mature styled Vuetify 4 plus an emerging
unstyled foundation,” not “one library already offering mature paired
renderers.” Stable v0 establishes a supported behavior surface, but not a
one-to-one styled/headless renderer pair with Vuetify 4.

Maintenance evidence is current tagged releases, current documentation, and
issue activity in both repositories. Release cadence alone does not show
regression rate or long-term API stability.

## 2. Normalized component inventory

The following is a full family census from the Vuetify 4.1.5 component tree
[V2]. Structural subparts are grouped with their public family.

| Citry category | Vuetify 4.1.5 families |
|---|---|
| Actions and status | Alert, Badge, Banner, Button, Button Group, Button Toggle, Chip, Chip Group, Confirm Edit, Empty State, Fab, Icon Button, Progress Circular, Progress Linear, Pull to Refresh, Snackbar, Snackbar Queue, Speed Dial |
| Form controls | Autocomplete, Checkbox, Color Input, Combobox, Counter, Field, File Input, File Upload, Form, Input, Label, Messages, Number Input, OTP Input, Radio, Radio Group, Range Slider, Rating, Select, Selection Control, Selection Control Group, Slider, Switch, Text Field, Textarea, Validation |
| Overlays and disclosure | Bottom Sheet, Dialog, Expansion Panel, Hover, Menu, Overlay, Tooltip |
| Navigation | App Bar, Bottom Navigation, Breadcrumbs, Hotkey, Navigation Drawer, Pagination, Stepper, Vertical Stepper, System Bar, Tabs, Toolbar |
| Data and collections | Data Iterator, Data Table, Infinite Scroll, Item Group, List, Slide Group, Table, Treeview, Virtual Scroll |
| Content and media | Avatar, Card, Carousel, Code, Divider, Image, Keyboard Key, Lazy, Parallax, Responsive, Sheet, Skeleton Loader, Sparkline, Timeline, Window |
| Date, time, and specialist | Calendar, Color Picker, Date Input, Date Picker, Picker, Time Picker |
| Layout and application shell | App, Footer, Grid, Layout, Main, No SSR |
| Ambient providers | Defaults Provider, Locale Provider, Theme Provider |
| Motion | Transition exports and window, carousel, expansion, slide, and overlay transitions |

The v0 1.0.0 inventory is independently normalized from its tagged component
and composable exports [V3]:

| Citry category | `@vuetify/v0` 1.0.0 families |
|---|---|
| Actions and status | Button, Progress, Rating, Snackbar, Toggle |
| Form controls | Checkbox, Combobox, Form, Input, Number Field, Radio, Select, Selection, Slider, Switch |
| Overlays and disclosure | Alert Dialog, Collapsible, Dialog, Expansion Panel, Popover, Portal, Presence, Scrim, Tooltip |
| Navigation and collections | Breadcrumbs, Carousel, Group, Overflow, Pagination, Single, Step, Tabs, Treeview |
| Content, media, and layout | Aspect Ratio, Atom, Avatar, Image, Splitter |
| Ambient providers | Locale, Theme |

v0 also exposes creation and behavior composables for forms, inputs,
collections, tables and grids, virtual focus, roving focus, popovers, RTL,
reduced motion, themes, and registries. A composable is not counted as a
finished user-facing component.

## 3. Composition, state, identity, and portals

The frozen comparison slice is broad in Vuetify 4 [V2, V8, V10].

| Probe | Composition and state finding |
|---|---|
| Button | `VBtn` combines link or button behavior, props, events, icon/content slots, group state, loading, and native `type`; polymorphism raises the usual obligation to preserve native keyboard and form semantics. |
| Field and Input | `VInput` and `VField` are structural layers used by `VTextField` and richer controls. Labels, hints, errors, validation state, prepend/append content, density, and variants are composable, but consumers inherit a sizeable internal DOM contract. |
| Dialog | `VDialog` wraps `VOverlay`; open state is controllable, content is slotted, activation can be declarative, and Teleport separates logical ownership from DOM placement. Focus restoration and containment are library-owned. |
| Combobox | `VCombobox` combines text input, list, menu, chips, multiple selection, item transforms, filtering, and async item replacement. Stable item identity depends on configured item value and comparator behavior. |
| Tabs | `VTabs`, `VTab`, and the optional window layer separate tab controls from panels. Selection is controlled or uncontrolled through the group machinery. |
| Table and Data Table | `VTable` is a styled structural table. `VDataTable` adds headers, sorting, selection, pagination, grouping, virtualization-related integrations, and extensive slots. The richer API is not a headless behavior engine. |
| Workflow probe | `VForm` registers descendant fields and aggregates validity; `VFileUpload` and data components add async/loading surfaces. Remote fetching, cancellation, and server error mapping remain application responsibilities. |
| Provider | `createVuetify`, defaults, theme, locale, icons, dates, display, and navigation are injected. Nested defaults and theme/locale providers shadow ancestor state [V5-V7]. |

Vue props and emits provide controlled state; defaults provide ambient initial
or fallback props; slots expose selected markup regions. `$attrs` forwarding is
component-specific, so consumers cannot assume that every arbitrary attribute
lands on the semantic root. Teleported content keeps Vue injection context,
but CSS ancestry changes, which makes scoped selectors and local theme wrappers
an explicit test obligation [V8].

Provider behavior is unusually instructive for Citry:

| Concern | Observed behavior | Citry pressure |
|---|---|---|
| Nesting and shadowing | Theme, locale, and defaults can be provided below app scope [V6, V7]. | Support lexical scopes, not only a single global store. |
| Defaults and overrides | Explicit component props beat named and global defaults; nested subcomponent defaults are merged [V6]. | Specify precedence and expose the resolved value in diagnostics. |
| Reactive updates | Provider values are refs or computed values [V5-V7]. | Inherited values must remain live after initialization. |
| SSR agreement | Display has an explicit post-hydration update; theme can install through a head manager or style element [V5, V7]. | Serialize or deterministically recompute inherited state and generated IDs. |
| Portals | Overlay attachment is configurable and uses Teleport [V8]. | Preserve logical provider ancestry across physical relocation. |
| Cleanup | Theme app effects stop on app unmount [V5]. | Scope observers and global listeners to component or application disposal. |
| Diagnostics | Missing injected services throw, but merged-default provenance is not surfaced [V5, V6]. | Explain missing providers and effective-value provenance. |

This evidence pressures both `$component.init()` provide/inject methods and
`$provide`/`$inject` Alpine-facing access. The internal API is needed by built-in
components; the magic layer is useful to user-authored headless markup. Citry
should implement one scoped registry beneath both surfaces, not two state
systems. Locale contract design remains follow-up work.

## 4. Customization and the styled/headless split

Vuetify 4's customization ladder is broad but coupled to its rendered
structure [V2, V6, V7]:

1. theme colors and generated CSS variables;
2. global or component defaults;
3. named variants, density, shape, elevation, and utility props;
4. classes, styles, and targeted Sass variables;
5. documented slots and activator props;
6. component composition or source ownership when internal markup must change.

This makes a polished default inexpensive, but deep DOM overrides can become
upgrade-sensitive. Defaults are a particularly transferable mechanism because
they define precedence without forcing source copies. Runtime CSS generation
is less transferable to Citry because the charter requires a no-build,
server-first delivery path and strict CSP operation.

v0 offers the other half: compound unstyled parts, controlled and uncontrolled
state, polymorphic atoms, and behavior composables [V3]. It is stable prior
art for a headless contract, but current 1.0.0 defects show why headless cannot
mean “semantics assembled by the consumer.” Citry should own tested behavior
once and expose both a styled template and supported headless parts over it.

## 5. Accessibility, input modes, direction, and motion

The mature implementation has real keyboard and focus code, including dialog
focus containment and restoration and combobox tests around async item removal
[V8, V9]. Source contains semantic roles and relationships for tabs, dialogs,
lists, and form controls. Touch and pointer paths are implemented across
overlays, sliders, carousels, and selection controls. RTL is tied to locale and
used by layout, navigation, and directional icons [V7].

Those facts do not establish WCAG 2.2 AA conformance. The current evidence set
does not show one public matrix that proves, for every shared-slice component:

- keyboard order and focus restoration in nested overlays;
- VoiceOver, NVDA, TalkBack, and browser combinations;
- IME composition in searchable controls;
- touch target and gesture alternatives;
- Windows forced-colors rendering;
- reduced-motion behavior for every animation;
- RTL interaction, placement, and logical CSS; or
- 200% and 400% zoom/reflow.

For Citry, automated axe checks and Lighthouse accessibility scores should be
entry checks, followed by APG keyboard scripts, focus assertions, forced-colors
and reduced-motion screenshots, RTL interaction tests, IME scenarios, and
manual screen-reader runs. The v0 complaint register below demonstrates why
source intent and automated scans still need behavioral verification.

## 6. Forms, validation, loading, errors, and async behavior

Vuetify's form layer coordinates descendants, supports lazy or eager validation,
and accepts promise-returning rules [V10]. Controls render native inputs where
appropriate, so names, values, disabled state, autocomplete, constraints, and
submit buttons can participate in a real form. Rich controls often serialize
through hidden or managed input state and therefore need explicit browser tests
for `FormData`, reset, autofill, failed validation focus, and no-JavaScript
submission.

Loading and error affordances are common props rather than one cross-component
async protocol. Data Table, Autocomplete, Combobox, File Upload, buttons, and
progress components can display pending states, but applications still own
request ordering, cancellation, stale-result rejection, upload constraints,
server error normalization, and retry. Citry should define those state names
consistently while leaving network policy outside the component.

## 7. Content trust and threat cases

Vue text interpolation and slots are the normal content path. Attribute and URL
forwarding still require policy: link-like buttons must reject or clearly leave
unsafe schemes to the application; image and file components must not imply
that client `accept` checks are security validation; and remote combobox labels
must render as text unless a separately named trusted-HTML API is used.

Vuetify assigns generated theme CSS to a style element and assigns a translated
calendar string to `innerHTML` [V11]. The former is generated from theme data
and supports a nonce [V7]. The latter means tenant-controlled translation
messages could cross an HTML sink. Citry should avoid an ambiguous “HTML
label” prop, keep safe text as the default, require an explicitly named trusted
fragment escape hatch, document sanitization ownership, validate forwarded
URLs, and test hostile filenames, labels, error messages, and remote results.

Generated IDs are used for ARIA relationships across compound components. The
contract must be deterministic across SSR and client activation, unique across
multiple roots, and conditional when the referenced part is absent. v0 issue
#608 is direct evidence for the last requirement.

## 8. Delivery, assets, CSP, payload, and upgrades

Vuetify 4 expects a Vue client runtime and normally a Vite or webpack pipeline;
component Sass and generated theme CSS are integral [V1, V4, V7]. Icons are an
adapter with separate icon-set choices; fonts are application choices rather
than required by the core source. A CSP nonce is supported for runtime theme
styles, but applications still need to account for every dynamic style path.

Imports can be per component, yet the real unit of cost includes shared
composables, CSS, icon assets, overlay infrastructure, and Vue itself. Archive
size [V12] should not be converted into a bundle claim. A fair reproduction
would build the frozen slice, record raw and compressed JavaScript and CSS,
count requests and fonts/icons, then repeat for SSR and lazy routes.

Upgrade cost comes from three surfaces: component APIs, internal DOM and class
contracts, and theme/default precedence. The 4.0 CSS-layer complaints show that
even a documented styling system can change cascade behavior. Citry should
version tokens, parts, and behavior contracts independently and publish DOM
changes only for explicitly supported parts.

## 9. Complaint register

Issues are user reports unless a tagged fix, maintainer acceptance, or current
source raises the evidence grade. The v0 findings are not attributed to
Vuetify 4.

| Pattern | Product, evidence, dates, and versions | Workflow, response, workaround, recurrence, status, impact | Grade |
|---|---|---|---|
| CSS layer order changed production output | Vuetify 4 issues [#22752](https://github.com/vuetifyjs/vuetify/issues/22752) and [#22801](https://github.com/vuetifyjs/vuetify/issues/22801), reported 2026-03-24 and 2026-04-14; affected 4.0.3 through 4.0.5; closed by 2026-07-03 and 2026-05-20. | Vite production styles and custom overrides differed because layer ordering changed. Reports included reproductions; downgrade or explicit layer ordering was the practical workaround. Two related reports establish recurrence. Resolved history, but a high-impact upgrade hazard for customized applications. | B |
| Mobile screen-reader selection failed | Vuetify 3 issue [#22226](https://github.com/vuetifyjs/vuetify/issues/22226), reported 2025-10-21, closed 2026-03-09, targeted to 3.12; VoiceOver and TalkBack with `VSelect`. | Selecting an option on mobile assistive technology did not complete reliably. Maintainers labeled and scheduled the issue; the report links related fixes. Resolved history for Vuetify 3. Current Vuetify 4 behavior remains unverified here. High impact for a core form workflow. | B |
| Polymorphic button roots lost native keyboard and form semantics | `@vuetify/v0` issue [#616](https://github.com/vuetifyjs/0/issues/616), reported 2026-07-15; open, assigned, and in the 1.0.x milestone at snapshot. The exact behavior remains in tagged 1.0.0 source [V13]. | `Button`, `Toggle`, and `PaginationItem` rendered as non-buttons had incomplete Enter/Space behavior; a polymorphic button could also default to form submission. The maintainer-authored audit includes exact source locations and a sibling implementation pattern. Workaround: retain native elements or add handlers/type explicitly. Current stable defect, cross-family recurrence, high impact. | A |
| Optional labelled parts produced dangling ARIA references | `@vuetify/v0` issue [#608](https://github.com/vuetifyjs/0/issues/608), reported 2026-07-15; open, assigned, and in the 1.0.x milestone at snapshot. The unconditional attributes remain in tagged 1.0.0 source [V13]. | Dialog, Alert Dialog, and Progress emitted relationships even when optional targets were absent. The maintainer-authored audit specifies acceptance tests and conditional registration. Workaround: always render the referenced parts or patch attributes. Current stable defect with multi-family recurrence and high assistive-technology impact. | A |
| Snackbar live-region contract missed urgent and first announcements | `@vuetify/v0` issue [#615](https://github.com/vuetifyjs/0/issues/615), reported 2026-07-15; open, assigned, and in the 1.0.x milestone at snapshot. Tagged 1.0.0 still hard-codes the reported behavior [V13]. | Snackbar hard-coded `status` and mounted initial text synchronously. The maintainer-authored audit contrasts a working sibling deferred-announcement pattern. Workaround: application-owned live region. Current stable defect, medium-high impact. | A |

### Complaint search log

Queries were run against GitHub issue search within the required window. The
exact strings were:

- `repo:vuetifyjs/vuetify is:issue created:2024-07-23..2026-07-23 sort:comments-desc`
- `repo:vuetifyjs/vuetify is:issue created:2024-07-23..2026-07-23 (accessibility OR aria OR keyboard OR focus)`
- `repo:vuetifyjs/vuetify is:issue created:2024-07-23..2026-07-23 (theme OR sass OR css OR customize)`
- `repo:vuetifyjs/vuetify is:issue created:2026-01-01..2026-07-23 (v4 OR 4.0 OR 4.1)`
- `repo:vuetifyjs/0 is:issue created:2024-07-23..2026-07-23 sort:comments-desc`
- `repo:vuetifyjs/0 is:issue created:2024-07-23..2026-07-23 (accessibility OR aria OR keyboard OR focus)`

The retained five patterns de-duplicate the two Vuetify 4 CSS reports and the
multi-component v0 audit findings. No complaint count is used as a quality
score. Unresolved: repeat the Vuetify 4 shared slice in current Safari,
VoiceOver, NVDA, TalkBack, forced colors, reduced motion, RTL, and IME; reproduce
the two resolved 4.0 styling issues on 4.1.5; and verify which v0 fixes land in
a later 1.0.x release.

## 10. Transfer to Citry

### Adopt

- One behavior contract with controlled and uncontrolled state, explicit item
  identity, and compound parts where the interaction warrants them.
- A deterministic defaults ladder: library default, provider default,
  component variant, explicit instance prop, and local part override.
- Lexically nested reactive providers with clear missing-provider errors,
  portal continuity, and cleanup.
- Styled components that are immediately useful, backed by supported headless
  behavior rather than a separate reimplementation.
- Native form elements and real submit/reset behavior wherever HTML can carry
  the contract.
- Browser-level focus and keyboard tests alongside automated accessibility
  scans.

### Do not transfer

- Vue, Vite, webpack, or Sass as consumer runtime requirements.
- A theme engine that must generate large style sheets in the browser.
- Unlimited ambient deep merges without effective-value diagnostics.
- Internal DOM classes as an accidental public customization API.
- Polymorphism that swaps away native semantics without taking over their full
  keyboard, focus, and form behavior.
- A newly stable headless layer treated as evidence of mature styled parity.

### Citry contract pressure

Vuetify pressures both provider surfaces: component authors need
`$component.init()` provide/inject methods, while application templates benefit
from `$provide` and `$inject` magics. Both should share scoped identity,
reactivity, shadowing, teleport continuity, cleanup, SSR serialization, and
diagnostics. The UI package also needs stable contracts for part names, token
fallbacks, form serialization, generated IDs, trusted content, overlay focus,
and async states. Localization should consume that provider foundation later;
it should not determine the initial UI API.
