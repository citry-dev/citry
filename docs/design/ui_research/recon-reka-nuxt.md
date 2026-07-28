# Reka UI and Nuxt UI reconnaissance

Status: Phase 4 combined dossier
Snapshot: 2026-07-23
Complaint window: 2024-07-23 through 2026-07-23

This is one work unit because Nuxt UI 4.10.0 uses Reka UI 2.10.1 for many
behavioral primitives. Findings retain their layer: Reka owns headless state
machines and compound parts; Nuxt UI owns styled wrappers, variants,
application services, and additional workflows. Shared implementation receives
one comparative weight.

## Evidence register

| ID | Finding and stable citation | Evidence type | Confidence | Counterevidence and unresolved questions |
|---|---|---|---|---|
| RN1 | Reka UI 2.10.1 is MIT licensed, requires Vue 3.4 or later, ships no theme, and depends on positioning, international date/number, virtualization, and utility packages. [Tagged manifest](https://github.com/unovue/reka-ui/blob/v2.10.1/packages/core/package.json) | Source observation | High | A dependency is not necessarily loaded by each component; route payload needs a build reproduction. |
| RN2 | Nuxt UI 4.10.0 is MIT licensed and pins Reka UI 2.10.1 while adding Tailwind CSS 4, variants/class merging, Nuxt modules, icons/fonts/color mode, table/virtualization, carousel, fuzzy search, drawer, and editor dependencies. [Tagged manifest](https://github.com/nuxt/ui/blob/v4.10.0/package.json) | Source observation | High | Tree shaking may exclude unused families, but the default toolchain boundary is materially broader than Reka's. |
| RN3 | Reka documents unstyled compound primitives, controlled and uncontrolled state, `asChild`, and tree-shakable imports. [Introduction](https://reka-ui.com/docs/overview/introduction), [styling guide](https://reka-ui.com/docs/guides/styling), [tagged source](https://github.com/unovue/reka-ui/tree/v2.10.1/packages/core/src) | Current documentation and source observation | High | “Accessible” remains a claim until each composition and browser/AT pair is tested. Polymorphism transfers native-semantics obligations to the implementation and consumer. |
| RN4 | Nuxt UI describes a styled catalog of more than 125 components built with Reka UI and Tailwind CSS; the tagged component source is inventoried below. [Components catalog](https://ui.nuxt.com/docs/components/), [tagged source](https://github.com/nuxt/ui/tree/v4.10.0/src/runtime/components) | Current documentation and source observation | High | The marketing count includes application, content, and specialist families; it is not the minimum Citry scope. |
| RN5 | Reka `ConfigProvider` provides reactive direction, locale, scroll-body policy, CSP nonce, portal target, and an injectable `useId`; portal instances can override the target. [Provider guide](https://reka-ui.com/docs/utilities/config-provider), [provider source](https://github.com/unovue/reka-ui/blob/v2.10.1/packages/core/src/ConfigProvider/ConfigProvider.vue) | Current documentation and source observation | High | Because nested providers apply defaults before replacing the nearest context, inheritance of unspecified values needs a dedicated nesting reproduction. |
| RN6 | Reka's context factory throws a named missing-provider error; focus and dismissable-layer listeners register cleanup. [Context source](https://github.com/unovue/reka-ui/blob/v2.10.1/packages/core/src/shared/createContext.ts), [FocusScope source](https://github.com/unovue/reka-ui/blob/v2.10.1/packages/core/src/FocusScope/FocusScope.vue), [dismissable-layer source](https://github.com/unovue/reka-ui/blob/v2.10.1/packages/core/src/DismissableLayer/utils.ts) | Source observation | High | Cleanup source does not prove every overlay composition is leak-free. |
| RN7 | Reka states that primitives follow WAI-ARIA patterns and are tested with modern browsers and common assistive technologies; source contains keyboard, focus, touch/pointer, RTL, and date-locale logic. [Accessibility guide](https://reka-ui.com/docs/overview/accessibility), [tagged tests](https://github.com/unovue/reka-ui/tree/v2.10.1/packages/core/src) | Current documentation and source observation | Medium-high | There is no public per-version WCAG 2.2 AA conformance report. Current issues below show gaps and regressions. |
| RN8 | Nuxt UI's `App` wraps Reka `ConfigProvider`, injects Vue's SSR-stable `useId`, derives direction and locale, provides a portal target, and hosts tooltip, toaster, and overlay providers. [App source](https://github.com/nuxt/ui/blob/v4.10.0/src/runtime/components/App.vue) | Source observation | High | This is a Vue/Nuxt solution, not directly portable to server-rendered Python. Nested `App` behavior is unresolved. |
| RN9 | Nuxt UI uses generated variant definitions, app-level configuration, CSS variables, per-component `ui` part classes, slots, and a descendant Theme component. [Theme guide](https://ui.nuxt.com/docs/getting-started/theme), [Button source](https://github.com/nuxt/ui/blob/v4.10.0/src/runtime/components/Button.vue), [release evidence](https://github.com/nuxt/ui/releases/tag/v4.5.0) | Current documentation and source observation | High | Tailwind class generation/merging and CSS layer order are part of the contract; issue #6172 shows an unresolved cascade edge. |
| RN10 | Nuxt UI ships Form/FormField with nested state, validation, loading, errors, and submit/reset methods, plus native-oriented Input/Textarea and rich Reka-backed controls. [Form source](https://github.com/nuxt/ui/blob/v4.10.0/src/runtime/components/Form.vue), [FormField source](https://github.com/nuxt/ui/blob/v4.10.0/src/runtime/components/FormField.vue) | Source observation | High | No-JavaScript and native `FormData` behavior still varies by rich control and was not reproduced here. |
| RN11 | Reka source has no general raw-HTML content prop in the frozen slice. Nuxt UI CommandPalette explicitly renders `labelHtml`, `suffixHtml`, and `descriptionHtml` with `v-html`. [CommandPalette source](https://github.com/nuxt/ui/blob/v4.10.0/src/runtime/components/CommandPalette.vue) | Source observation | High | Safe slots and text labels are counterevidence to a library-wide problem. The named HTML fields still need an explicit trust/sanitization contract. |
| RN12 | Registry metadata reports about 8.4 MB unpacked across 2,956 files for Reka UI 2.10.1 and about 2.6 MB across 828 files for Nuxt UI 4.10.0. [Reka package](https://www.npmjs.com/package/reka-ui/v/2.10.1), [Nuxt UI package](https://www.npmjs.com/package/@nuxt/ui/v/4.10.0) | Registry observation | High | Archive size is not browser payload. Nuxt UI's smaller archive relies on substantial dependency packages. |

## 1. Snapshot, boundaries, dependencies, and maintenance

Both audited packages are MIT and actively maintained [RN1, RN2]. Reka is the
headless foundation; Nuxt UI is the broad styled product. Nuxt UI's runtime is
free, while templates or ecosystem services are separate and not required for
the package. Neither product's commercial ecosystem was scored.

Reka's dependencies support hard behaviors such as popup positioning, date and
number semantics, and virtual collections [RN1]. Nuxt UI adds a full build and
application ecosystem [RN2]. That makes the pair excellent architectural prior
art but a poor delivery template for Citry's no-Node, no-Tailwind consumer
contract. Current tags, releases, docs, and issue activity show maintenance;
the 2.10 regressions show that activity is not the same as stability.

## 2. Normalized component inventory

### Reka UI 2.10.1

The full tagged family census is [RN3]:

| Citry category | Reka UI families |
|---|---|
| Actions and status | Progress, Rating, Toast, Toggle, Toggle Group |
| Form controls | Autocomplete, Checkbox, Color Area, Color Field, Color Picker, Color Slider, Color Swatch, Color Swatch Picker, Combobox, Date Field, Date Range Field, Editable, Label, Listbox, Number Field, Pin Input, Radio Group, Select, Slider, Switch, Tags Input, Time Field, Time Range Field |
| Overlays and disclosure | Accordion, Alert Dialog, Collapsible, Context Menu, Dialog, Drawer, Dropdown Menu, Hover Card, Menu, Menubar, Navigation Menu, Popover, Tooltip |
| Navigation and collections | Calendar, Date Picker, Date Range Picker, Month Picker, Month Range Picker, Pagination, Range Calendar, Stepper, Tabs, Tree, Year Picker, Year Range Picker |
| Layout and content primitives | Aspect Ratio, Avatar, Primitive, Scroll Area, Separator, Splitter, Toolbar, Viewport, Visually Hidden |
| Infrastructure | Collection, Config Provider, Dismissable Layer, Focus Guards, Focus Scope, Popper, Presence, Roving Focus, Teleport |

There is deliberately no styled Button, generic text Input, simple Table, Data
Table, Card, Alert, or application shell. Native elements and user styling fill
some gaps; Table/DataTable is a true missing member of the frozen slice.

### Nuxt UI 4.10.0

The tagged source census [RN4] is grouped without hiding its higher-level
breadth:

| Citry category | Nuxt UI families |
|---|---|
| Actions and status | Alert, Badge, Banner, Button, Chip, Empty, Progress, Skeleton, Toast, Toaster |
| Form controls | Checkbox, Checkbox Group, Color Picker, File Upload, Input, Input Date, Input Menu, Input Number, Input Rating, Input Tags, Input Time, Listbox, Pin Input, Radio Group, Select, Select Menu, Slider, Switch, Textarea |
| Forms and authentication | Auth Form, Form, Form Field, Field Group |
| Overlays and disclosure | Accordion, Collapsible, Context Menu, Drawer, Dropdown Menu, Modal, Popover, Slideover, Tooltip |
| Navigation | Breadcrumb, Command Palette, Kbd, Link, Navigation Menu, Pagination, Sidebar, Stepper, Tabs |
| Data and collections | Calendar, Carousel, Table, Timeline, Tree |
| Content and media | Avatar, Avatar Group, Card, Icon, Marquee, Scroll Area, Separator, User |
| Layout and application shell | App, Container, Footer, Footer Columns, Header, Main, Overlay Provider, Theme |
| Page and marketing compositions | Blog Post(s), Changelog Version(s), Page, Page Anchors, Page Aside, Page Body, Page CTA, Page Card, Page Columns, Page Feature, Page Grid, Page Header, Page Hero, Page Links, Page List, Page Logos, Page Section, Pricing Plan(s), Pricing Table |
| Dashboard compositions | Dashboard Group, Navbar, Panel, Resize Handle, Search, Search Button, Sidebar, Sidebar Collapse, Sidebar Toggle, Toolbar |
| Chat and editor specialist | Chat Message(s), Chat Palette, Chat Prompt, Chat Prompt Submit, Chat Reasoning, Chat Shimmer, Chat Tool, Editor, Editor Drag Handle, Editor Emoji Menu, Editor Mention Menu, Editor Suggestion Menu, Editor Toolbar |
| Utility compositions | App, Error, Field Group, Icon, Link Base, Overlay Provider, Theme |

The inventory supports an application without immediately adding another UI
kit. Citry should not absorb chat, editor, pricing, dashboard, or domain-heavy
table breadth into its initial default.

## 3. Composition, state, identity, and portals

| Frozen probe | Reka finding | Nuxt UI finding |
|---|---|---|
| Button | Missing by design; use a native button or compose `Primitive`. | Styled Button wraps link/button behavior with variants, icons, loading, slots, and part classes. |
| Field and Input | No generic text input; Label plus specialized fields expose compound parts and native inputs. | Styled Input/FormField add labels, help, errors, icons, size/color/variant, and native attributes. |
| Dialog | Root, Trigger, Portal, Overlay, Content, Title, Description, Close; controlled/uncontrolled open state and dismiss/focus hooks. | Modal wraps Reka parts into a styled higher-level API and portal policy. |
| Combobox | Full compound API with Anchor, Input, Trigger, Portal, Content, Viewport, Item, groups, empty and cancel parts; item identity and filtering are explicit. | InputMenu/SelectMenu wrap Reka with item arrays, label/value keys, filtering, virtualization, slots, remote loading patterns, and styled states. |
| Tabs | Root, List, Trigger, Content, indicator and controlled/uncontrolled value. | Styled Tabs maps items into Reka parts and generated variants. |
| Table/DataTable | Missing. | Table uses a table engine for columns, sorting, filtering, selection, pagination, virtualization-related patterns, and slots; it remains a rich styled wrapper. |
| Workflow probe | Date and collection primitives exercise locale, range state, virtual focus, and dynamic items. | Form, FileUpload, CommandPalette, Table, and InputMenu exercise validation, files, async results, selection, and loading [RN10]. |
| Provider | ConfigProvider supplies direction, locale, scroll policy, nonce, portal target, and ID generation [RN5]. | App binds those concerns to locale, portal, tooltip, toaster, and overlay providers [RN8]. |

Reka's compound parts, controlled/default props, emits, `asChild`, data
attributes, and exposed refs provide deep markup and behavior control [RN3].
Nuxt UI intentionally narrows that surface into item props, generated variants,
slots, and `ui` part classes [RN9]. Item identity, multiple selection, remote
result replacement, and portal focus must be tested at both layers when the
wrapper changes foundation defaults.

Provider audit:

| Concern | Observed behavior | Citry pressure |
|---|---|---|
| Nesting and shadowing | Vue injection selects the nearest provider. A nested ConfigProvider supplies a whole defaulted context [RN5]. | Define whether omitted nested values inherit or reset, and test it. |
| Defaults and overrides | Global values flow into primitives; component props and individual Portal `to` override them [RN5]. | Publish field-by-field precedence. |
| Reactivity | Provider fields are Vue refs; Nuxt locale and portal are refs [RN5, RN8]. | Keep inherited values live after activation. |
| SSR agreement | Injectable `useId` lets Nuxt provide Vue's SSR-stable ID [RN5, RN8]. | Make deterministic server/client IDs a first-class provider hook. |
| Portals | Global target plus per-portal override; Vue context follows logical ancestry [RN5]. | Preserve logical scope while testing physical CSS and focus boundaries. |
| Cleanup | FocusScope and dismissable-layer listeners remove themselves [RN6]. | Require disposal tests for every global listener and scroll lock. |
| Diagnostics | Missing contexts throw named errors [RN6]; effective inherited values have no provenance view. | Report missing provider, owner scope, and resolved source. |

The pair pressures both `$component.init()` provide/inject and Alpine
`$provide`/`$inject`, implemented over one scoped registry. Locale API design
remains follow-up work; direction, IDs, portals, theme, and generic values can
establish the transport first.

## 4. Customization and styled/headless implications

Reka offers markup and behavior control through compound parts, slots,
controlled state, `asChild`, attributes, CSS selectors, and source ownership
[RN3]. Nuxt UI adds semantic CSS variables, color/size/variant axes,
application defaults, descendant themes, per-part classes, slots, and source
ownership [RN9]. This is the closest surveyed shape to Citry's intended pair.

The important caveat is that Nuxt wrappers are independently authored APIs,
not automatic skins over every Reka part. Wrapper conveniences can hide
headless capabilities, as SelectMenu's selected-label limitation shows. Citry
should define the behavior contract first, then test the styled and headless
renderers against identical state, event, ARIA, form, and async fixtures.

## 5. Accessibility, input modes, direction, and motion

Reka provides substantial keyboard, focus, touch/pointer, screen-reader, RTL,
and locale-aware behavior [RN7]. Nuxt inherits much of it and adds direction-
aware icons and higher-level labels [RN8]. That inheritance must be counted
once, and wrapper changes must be tested separately.

Open toast and popover issues plus the resolved 2.10 focus regression show why
documentation is not conformance. No complete current evidence was found for
forced colors, all reduced-motion paths, IME under every searchable control,
mobile screen readers, nested portals, or 400% zoom. Citry should combine axe
and Lighthouse with APG keyboard traces, focus assertions, pointer/touch tests,
forced-colors and reduced-motion screenshots, RTL interaction, IME composition,
and manual VoiceOver, NVDA, and TalkBack runs.

## 6. Forms, validation, loading, errors, and async behavior

Reka specializes in control state rather than a whole form. Nuxt Form adds
schema or custom validation, nested forms, loading, error events, focus/scroll
to errors, submit/reset/validate exposure, and FormField linkage [RN10]. Inputs
usually retain native names and elements; compound selects and date values need
explicit `FormData`, reset, autofill, required, Enter-submit, and no-JavaScript
tests.

InputMenu, SelectMenu, CommandPalette, Table, and FileUpload expose loading,
empty, error, query, or progress presentation. Request cancellation, stale
result rejection, retries, server-error mapping, filename trust, upload type and
size enforcement, and idempotent submission remain application/server work.

## 7. Content trust and threat cases

Reka normally renders slots/text and forwards attributes to chosen primitives.
`asChild` and arbitrary URLs increase consumer control without making unsafe
schemes safe. Nuxt CommandPalette's named HTML fields cross a raw-HTML sink
[RN11]. Remote search results make that particularly relevant.

Citry should default to escaped text, name trusted fragments explicitly, state
who sanitizes them, validate library-owned URL schemes, constrain attribute
destinations, and test hostile remote labels, filenames, error messages, image
URLs, and table cells. Generated IDs must be unique, deterministic across SSR,
and emitted only when their ARIA target exists. Client file filters and form
schemas are not server security boundaries.

## 8. Delivery, assets, CSP, payload, and upgrades

Reka requires Vue and a bundler but no theme CSS [RN1]. Nuxt UI requires the
Nuxt/Tailwind build, generated classes and CSS layers, plus configurable icon
and font infrastructure [RN2, RN9]. Reka's provider carries a nonce for relevant
dynamic behavior [RN5]. These are useful mechanisms but violate Citry's
consumer requirement if copied literally.

Archive sizes [RN12] are not bundle sizes. Build the frozen slice at both
layers and record raw/compressed JavaScript and CSS, dependency chunks, icons,
fonts, requests, SSR output, and hydration work. Upgrade contracts must pin
Reka part semantics and focus traces, Nuxt slot/part names, variant resolution,
CSS layer order, generated IDs, portal targets, and native form serialization.

## 9. Complaint register

| Pattern | Layer, evidence, dates, and versions | Workflow, response, workaround, recurrence, status, impact | Grade |
|---|---|---|---|
| Reka 2.10 changed keyboard/focus behavior across composed overlays | Reka issues [#2756](https://github.com/unovue/reka-ui/issues/2756) and [#2749](https://github.com/unovue/reka-ui/issues/2749), opened 2026-06-24 and 2026-06-23 against 2.10.0, closed via #2752 on 2026-06-24. | Arrow navigation failed in DropdownMenu and a Combobox inside Dialog could not focus/type. Reproducers compared 2.9.x. Upgrade to the fix release was the resolution. Resolved history with cross-component recurrence; high core-interaction impact. | B |
| Popover without tabbables self-dismisses in test DOMs | Reka [#2803](https://github.com/unovue/reka-ui/issues/2803), opened 2026-07-14 against 2.10.1, open. | FocusScope fallback lands outside DismissableLayer in jsdom/happy-dom; real browsers mask it while wrapper remains unfocusable. Report includes a deterministic test and source trace. Workaround prevents mount autofocus in tests. Current defect affecting tests, with a latent composition concern; medium impact. | A |
| Toast focus sentinels are both focusable and ARIA-hidden | Reka [#2776](https://github.com/unovue/reka-ui/issues/2776), opened 2026-07-01, reproduced on 2.10.0 and 2.10.1, open with follow-up PR. | Axe reports serious `aria-hidden-focus` on two proxies. A prior fix addressed siblings but not this path, establishing recurrence. Workaround requires patching the proxy. Current accessibility defect, high impact. | A |
| Nuxt UI semantic-variable overrides lose to CSS layers after navigation | Nuxt UI [#6172](https://github.com/nuxt/ui/issues/6172), opened 2026-03-10 against 4.5.1, open at snapshot with reproduction and related v3 lineage. | Dark-mode/view-transition reapplication restores library values because `theme` layer outranks `base`. Put overrides outside layers as workaround. Current defect or undocumented constraint, recurring across versions, medium-high customization impact. | C |
| SelectMenu cannot format selected labels as richly as list items | Nuxt UI [#4581](https://github.com/nuxt/ui/issues/4581), opened 2025-07-23 and open; 4.10.0 source still derives selected text from `labelKey` while item labels have a slot. | Compound labels need wrapper/computed data while list items can use markup. No maintainer resolution at snapshot. Current deliberate limitation, medium workflow/customization impact. | A |

### Complaint search log

- `repo:unovue/reka-ui is:issue created:2024-07-23..2026-07-23 sort:comments-desc`
- `repo:unovue/reka-ui is:issue created:2024-07-23..2026-07-23 (accessibility OR aria OR keyboard OR focus)`
- `repo:unovue/reka-ui is:issue created:2024-07-23..2026-07-23 (SSR OR hydration OR teleport)`
- `repo:unovue/reka-ui is:issue created:2024-07-23..2026-07-23 (Combobox OR Dialog OR Popover OR Toast)`
- `repo:unovue/reka-ui is:issue created:2026-06-01..2026-07-23 (2.10 OR regression)`
- `repo:nuxt/ui is:issue created:2024-07-23..2026-07-23 sort:comments-desc`
- `repo:nuxt/ui is:issue created:2024-07-23..2026-07-23 (theme OR variant OR override OR layer)`
- `repo:nuxt/ui is:issue created:2024-07-23..2026-07-23 (accessibility OR aria OR keyboard OR focus)`
- `repo:nuxt/ui is:issue created:2024-07-23..2026-07-23 (SSR OR hydration OR portal)`
- `repo:nuxt/ui is:issue created:2024-07-23..2026-07-23 (SelectMenu OR Form OR Table)`
- foundation: `repo:tailwindlabs/tailwindcss is:issue created:2024-07-23..2026-07-23 (layer OR theme OR Nuxt)`
- foundation: `repo:heroui-inc/tailwind-variants is:issue created:2024-07-23..2026-07-23 (merge OR variant OR slot)`
- foundation: `repo:floating-ui/floating-ui is:issue created:2024-07-23..2026-07-23 (Vue OR focus OR RTL)`
- foundation: `repo:TanStack/table is:issue created:2024-07-23..2026-07-23 Vue`
- foundation: `repo:TanStack/virtual is:issue created:2024-07-23..2026-07-23 Vue`

No foundation issue was retained when it did not explain a current observed
wrapper outcome or would double-count Reka/Nuxt behavior. Unresolved: reproduce
the five patterns on the exact frozen tags, test nested providers, and run the
shared accessibility, SSR, form, security, RTL, IME, and payload matrix.

## 10. Transfer to Citry

### Adopt

- Headless compound parts with controlled and uncontrolled state, stable data
  attributes, and native-element defaults.
- A styled wrapper catalog broad enough for real applications, but built over
  the same tested behavioral contract.
- Configurable direction, portal target, scroll policy, nonce, and deterministic
  ID generation in one provider.
- Missing-provider diagnostics and strict listener/scroll-lock cleanup.
- Semantic tokens, variants, stable part overrides, slots, and descendant theme
  scopes with explicit precedence.

### Do not transfer

- Vue, Nuxt, Tailwind, or a Node build as consumer requirements.
- `asChild`-style polymorphism without full semantic and form invariants.
- Wrapper APIs that silently hide headless capabilities.
- CSS layer ordering as undocumented customization knowledge.
- Raw HTML fields without a named trust boundary.
- Specialist chat, editor, charts, maps, or domain-heavy table behavior in the
  initial default package.

### Citry contract pressure

The pair gives the strongest evidence for both provider surfaces. Built-ins
need `$component.init()` provide/inject; user-authored headless templates need
`$provide`/`$inject`; both must share lexical shadowing, reactivity, SSR IDs,
portal continuity, cleanup, and diagnostics. Citry also needs versioned
contracts for state, events, parts, tokens, attributes, forms, async results,
focus, and trusted content. Locale messages and translation-key policy should
be a later extension over this transport, not a Phase 4 API commitment.
