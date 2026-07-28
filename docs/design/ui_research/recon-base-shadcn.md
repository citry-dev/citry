# Phase 4 dossier: Base UI, shadcn/ui, and Radix lineage

**Snapshot:** 2026-07-23. **Studied lines:** Base UI 1.6.0, shadcn CLI
4.14.0 and its current Base UI/Radix/React Aria registries, and current Radix
Primitives 1.x packages as lineage. **Evidence scope:** current official docs,
release and license sources, and project issue/discussion trackers. No local
runtime reproduction was performed.

Evidence labels are **Docs**, **Source/release**, **Maintainer report**, **User
report**, and **Inference**. Confidence grades follow the
[Phase 3 protocol](candidate-map.md#52-complaint-sample-and-confidence). Shared
Radix behavior or the same copied shadcn implementation receives one evidence
weight.

## 1. Product snapshots and relationship

### Base UI

Base UI 1.6.0 is an installed MIT-licensed React package containing thirty-seven
documented unstyled families. It reached 1.0 in December 2025 and has shipped
frequent feature, performance, form, and accessibility releases since.
[About](https://base-ui.com/react/overview/about),
[releases](https://base-ui.com/react/overview/releases), and
[license](https://github.com/mui/base-ui/blob/master/LICENSE), **Docs and
Source/release, high confidence.**

No paid component or runtime boundary was identified for the studied Base UI,
shadcn/ui, or Radix packages: their first-party code is MIT licensed and their
documented catalogs are usable without a commercial tier. Third-party shadcn
registries and copied dependencies are separate software and may impose their
own licenses, services, or payment terms. **Source and docs observation, high
confidence for the first-party packages; unresolved for the unbounded registry
ecosystem:** [Base license](https://github.com/mui/base-ui/blob/master/LICENSE),
[shadcn license](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md), and
[Radix license](https://github.com/radix-ui/primitives/blob/main/LICENSE).

It supplies no CSS or design tokens. Its focus is accessible behavior,
compound composition, state, and direct access to rendered nodes. The package
is tree-shakable and supports React 17 onward and modern Baseline browsers at
the last major-release cutoff. **Docs claim, high confidence that this is the
published contract.**

### shadcn/ui

shadcn/ui explicitly says it is a code distribution platform rather than a
traditional installed component library. The CLI copies component source,
styles, dependencies, utilities, hooks, and registry content into the
application. The current catalog contains about sixty styled components and
recipes plus blocks. It is MIT-licensed.
[Introduction](https://ui.shadcn.com/docs),
[catalog](https://ui.shadcn.com/docs/components),
[CLI](https://ui.shadcn.com/docs/cli), and
[license](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md), **Docs and
Source/release, high confidence.**

Base UI is the current default behavior foundation. Radix remains supported,
and React Aria became a first-class base in July 2026. Existing projects remain
on their selected base, so “a shadcn component” is not one behavior
implementation. [July 2026 changelog](https://ui.shadcn.com/docs/changelog),
**Docs, high confidence.**

### Radix lineage

Radix Primitives remains an MIT-licensed installed headless library organized
as compound parts, portals, controlled state, state attributes, and `asChild`
composition. It is both a continuing shadcn base and important design lineage
for Base UI. [Introduction](https://www.radix-ui.com/primitives/docs/overview/introduction),
[composition](https://www.radix-ui.com/primitives/docs/guides/composition), and
[license](https://github.com/radix-ui/primitives/blob/main/LICENSE), **Docs and
Source, high confidence.** It is not scored independently here.

### Evidence boundary register

| Material area | Direct evidence | Confidence | Counterevidence and unresolved boundary |
|---|---|---|---|
| Product and version | Base UI 1.6.0, shadcn CLI 4.14.0/current registries, and current Radix lineage are separated above | High | shadcn registry contents can change without a traditional package release, and one component name may select different foundations. |
| Inventory | Every Base UI family and every first-party shadcn catalog entry visible at the snapshot is named below | High | Compound parts, blocks, community registry items, forms guides, and helpers are not counted as additional families. Registry variants can add transitive packages. |
| Architecture and delivery | Official Base composition/customization docs and shadcn CLI/registry docs | High | No local installation, portal reproduction, registry provenance audit, or bundle measurement was run. |
| Dependencies and upgrades | Base is installed; shadcn copies source and can add dependencies; Radix, React Aria, and TanStack are named foundations or recipe dependencies | High for documented mechanisms; medium-high for cost inference | A complete transitive graph and representative three-way upgrade were not reproduced. CLI diff and overwrite reduce discovery cost but do not merge local edits. |
| Accessibility | Base and Radix behavior documentation, shadcn's selected foundations, and issue evidence below | Medium-high | Source ownership means upstream quality can be changed locally. No suite-wide independent conformance report covers all bases, wrappers, and revisions. |
| Content trust and security | CSPProvider, registry schema, source-copy model, forms, link-like composition, and application-owned code | Medium-high for mechanisms; medium for inferred threats | No end-to-end threat model or registry trust policy was found. A registry can distribute code and dependencies, so exact installed content remains the security unit. |

## 2. Normalized inventory

| Citry category | Base UI installed behavior | shadcn styled/source layer |
|---|---|---|
| Actions and feedback | Button, Toggle, Toggle Group, Meter, Progress, Toast | Alert, Badge, Button, Button Group, Progress, Skeleton, Sonner, Spinner, Toast, Toggle, Toggle Group |
| Form controls | Autocomplete, Checkbox, Checkbox Group, Combobox, Field, Fieldset, Form, Input, Number Field, OTP Field, Radio, Select, Slider, Switch | Checkbox, Combobox, Field, Input, Input Group, Input OTP, Label, Native Select, Radio Group, Select, Slider, Switch, Textarea |
| Navigation and disclosure | Accordion, Collapsible, Menu, Menubar, Navigation Menu, Tabs, Toolbar | Accordion, Breadcrumb, Collapsible, Menubar, Navigation Menu, Pagination, Tabs |
| Overlays and menus | Alert Dialog, Context Menu, Dialog, Drawer, Popover, Preview Card, Tooltip | Alert Dialog, Context Menu, Dialog, Drawer, Dropdown Menu, Hover Card, Popover, Sheet, Tooltip |
| Layout and content | Avatar, Scroll Area, Separator | Aspect Ratio, Avatar, Card, Direction, Empty, Item, Kbd, Resizable, Scroll Area, Separator, Sidebar, Typography |
| Data and specialist recipes | No general table or specialist visual component | Calendar, Carousel, Chart, Command, Data Table, Date Picker, Table |
| Messaging recipes | None | Attachment, Bubble, Marker, Message, Message Scroller |
| Utilities | CSPProvider, DirectionProvider, mergeProps, useRender | `components.json`, CLI, registry schema, presets, `cn`, theme variables, base choice |

Sources:
[Base UI catalog](https://base-ui.com/react/overview/about) and
[shadcn catalog](https://ui.shadcn.com/docs/components). **Docs, high
confidence.** shadcn's apparent breadth includes recipes over separate
dependencies such as TanStack Table rather than one behavior runtime; the
[Data Table guide](https://ui.shadcn.com/docs/components/base/data-table)
describes that assembly. **Docs, high confidence.**

This census intentionally lists all thirty-seven Base UI families and all
first-party shadcn catalog entries present at the snapshot. Counterevidence:
shadcn's catalog mixes primitives, styled wrappers, higher-level recipes, and
specialist integrations, so equal row presence does not imply equal behavior
ownership. Community registry entries and blocks are unbounded and excluded.
Whether every registry base exposes every catalog name with identical maturity
remains unresolved.

## 3. Delivery, dependencies, and ownership

Base UI is an installed, versioned runtime dependency. Its 1.6.0 package
requires React and React DOM as peers, treats the date-fns packages and React
types as optional peers, and directly depends on Floating UI DOM/utilities,
`@base-ui/utils`, Babel runtime, and the external-store compatibility package.
Registry metadata reports about 9.3 MB unpacked across 3,187 files, which is a
publication size rather than a browser payload. [Base UI 1.6.0 package](https://www.npmjs.com/package/@base-ui/react/v/1.6.0),
**Registry observation, high confidence.** This graph places popup geometry,
shared utilities, and external-store compatibility outside the component
source itself. A tree-shaken browser payload and transitive license graph were
not reproduced.

Popup components use
portals and require a documented application-root stacking context; current
iOS Safari also needs a global body positioning rule for full-viewport
backdrops. [Quick start](https://base-ui.com/react/overview/quick-start),
**Docs, high confidence.**

shadcn performs source installation. `init` selects a base, configures CSS
variables and dependencies, and can enable RTL. `add` can preview, diff, or
overwrite files. A registry can distribute arbitrary project files,
dependencies, hooks, pages, configuration, and rules.
[CLI](https://ui.shadcn.com/docs/cli) and
[registry](https://ui.shadcn.com/docs/registry), **Docs, high confidence.**
This changes the upgrade unit from a package version to every locally modified
file and transitive registry item. **Inference, high confidence.**

The source-copy layer broadens the dependency graph. Data Table is a TanStack
Table recipe; calendar, chart, carousel, command, drawer, OTP, and toast
families may use specialist packages. Their licenses, payloads, CSP behavior,
and update schedules must be audited independently. **Docs plus inference,
medium-high; a complete transitive inventory was not reproduced.**

Neither architecture transfers directly to Citry: both require React. Source
copy is nevertheless valid comparison evidence for the benefits and costs of
application ownership.

## 4. Composition and behavior APIs

Base UI families use namespaces such as `Dialog.Root`, `Dialog.Trigger`,
`Dialog.Portal`, `Dialog.Backdrop`, and `Dialog.Popup`. Authors can remove or
reorder parts and use `render` to replace the underlying element. A custom
rendered component must forward the ref and all received props. Multiple
behaviors can nest through repeated render props.
[Composition](https://base-ui.com/react/handbook/composition), **Docs, high
confidence.**

Components are uncontrolled by default and can be controlled with paired
state and change props. Change callbacks carry a reason, native event, cancel
operation, and propagation control. This is a more expressive contract than a
bare `onChange`, especially for nested overlays and server synchronization.
[Customization](https://base-ui.com/react/handbook/customization), **Docs,
high confidence.**

Radix's `asChild` achieves similar element replacement by cloning a single
child. It transfers accessibility obligations to the consumer, who must spread
props and forward refs. [Radix composition](https://www.radix-ui.com/primitives/docs/guides/composition),
**Docs, high confidence.** Base UI's render contract and Radix's `asChild` are
related goals but not API-compatible.

shadcn wraps or copies those primitives into higher-level styled components.
Since consumers own the wrapper, they can change markup and behavior without
an upstream escape hatch, but can also break implicit part, focus, or ARIA
contracts. **Inference, high confidence.**

## 5. Customization ladder

| Level | Base UI | shadcn/ui | Citry lesson |
|---|---|---|---|
| Tokens | None | Semantic CSS variables for surfaces, foregrounds, radius, charts, sidebar, and dark mode | Default library needs a documented semantic token layer |
| Variants | State-driven class/style functions | Copied variant recipes and component props | Keep a coherent first-party variant vocabulary |
| Parts | Every important DOM node is a named compound part | Wrapper exposes selected parts and `data-slot` hooks | Headless contract should not depend on undocumented descendants |
| State styling | State data attributes, class/style callbacks, CSS variables | Tailwind selectors over base state and local data attributes | Styled and headless surfaces should share state names |
| Markup | `render` can replace elements and nest behaviors | Edit any copied source | Offer explicit parts before considering source ejection |
| Behavior | Controlled/uncontrolled state, cancellable reason-bearing events | Edit wrappers or underlying-base use | Citry Events needs reason and cancellation semantics where relevant |
| Source | Open installed package | Application owns generated files | Ownership maximizes control and maximizes per-app maintenance |

The [shadcn theming guide](https://ui.shadcn.com/docs/theming) defines semantic
CSS variables and dark-mode overrides. Base UI's
[styling guide](https://base-ui.com/react/handbook/styling) exposes class,
functional class/style, data attributes, and dynamic CSS variables for every
part. **Docs, high confidence.**

## 6. Frozen comparison slice

| Probe | Finding | Evidence |
|---|---|---|
| Button | Base UI supplies press semantics but no visuals; shadcn adds sizes, variants, loading-adjacent composition, and theme styling in copied code | [Base catalog](https://base-ui.com/react/overview/about), [shadcn Button](https://ui.shadcn.com/docs/components/base/button), Docs, high |
| Field and Input | Base Field/Form connect labels, descriptions, validation, and native controls; shadcn adds a styled Field family and optional third-party form guides | [Base forms](https://base-ui.com/react/handbook/forms), [shadcn Field](https://ui.shadcn.com/docs/components/base/field), Docs, high |
| Dialog | Explicit root, trigger, portal, backdrop, viewport/popup, title, description, and close parts; shadcn selects and styles an assembly | [Base Dialog](https://base-ui.com/react/components/dialog), [shadcn Dialog](https://ui.shadcn.com/docs/components/base/dialog), Docs, high |
| Combobox | Base UI owns complex collection, filtering, multi-selection, popup, virtualized and form behavior; shadcn supplies a styled assembly | [Base Combobox](https://base-ui.com/react/components/combobox), [shadcn Combobox](https://ui.shadcn.com/docs/components/base/combobox), Docs, high |
| Tabs | Base compound parts and orientation/state attributes receive copied styling | [Base Tabs](https://base-ui.com/react/components/tabs), [shadcn Tabs](https://ui.shadcn.com/docs/components/base/tabs), Docs, high |
| Table/Data Table | Base UI has no general Table. shadcn's semantic Table is styling; sorting, filtering, pagination, and selection come from a separate TanStack Table recipe | [Table](https://ui.shadcn.com/docs/components/base/table), [Data Table](https://ui.shadcn.com/docs/components/base/data-table), Docs, high |
| Form workflow | Base UI extends native constraint validation and supports custom/server errors and third-party form stores; shadcn documents React Hook Form, TanStack Form, and Formisch separately | [Base forms](https://base-ui.com/react/handbook/forms), [shadcn forms](https://ui.shadcn.com/docs/forms/react-hook-form), Docs, high |
| Provider/context | Base UI supplies DirectionProvider and CSPProvider; theme is CSS-variable inheritance; portals preserve behavior context but need explicit DOM direction | [DirectionProvider](https://base-ui.com/react/utils/direction-provider), [CSPProvider](https://base-ui.com/react/utils/csp-provider), Docs, high |

## 7. Accessibility, input modes, and ambient context

Base UI claims APG-aligned roles, pointer interaction, keyboard navigation,
focus management, and testing across browsers, devices, and screen readers.
Its accessibility page explicitly makes visible focus, contrast, and labels a
shared author responsibility. [Accessibility](https://base-ui.com/react/overview/accessibility),
**Docs claim, high confidence as published posture, not independent
conformance.**

DirectionProvider changes behavioral direction for descendants but does not
set HTML `dir` or CSS direction. `useDirection` exists specifically for
portaled components outside the DOM direction subtree. This is strong evidence
that Citry's future client context must distinguish component ancestry from DOM
ancestry and teleported placement. **Docs and inference, high confidence.**

CSPProvider passes a per-request nonce to inline style or script tags and can
disable certain injected style elements, but inline style attributes require a
separate policy decision. [CSPProvider](https://base-ui.com/react/utils/csp-provider),
**Docs, high confidence.** This is a useful ambient security value, not only a
theme or locale concern.

shadcn's accessibility quality is the combined result of the selected base,
the current registry wrapper, its default CSS, and local edits. The source-copy
model prevents a suite-wide guarantee after installation. **Inference, high
confidence.** Forced-color, reduced-motion, zoom, touch, IME, and screen-reader
coverage must therefore be tested on the exact installed revision.

### Ambient-context audit

| Question | Finding |
|---|---|
| Values carried | Base UI documents direction and CSP nonce/settings. shadcn theme values use CSS custom-property inheritance, while application dark-mode providers are external recipes. |
| Nesting and shadowing | Providers wrap a subtree, but exact nested-provider shadowing and missing-value diagnostics are not specified in the reviewed docs. CSS variables follow normal cascade and inheritance. |
| Reactive updates | Direction is a provider prop and theme is CSS state. Server-to-client nonce agreement is explicitly per request. No generic reactive defaults provider exists. |
| Portal behavior | `useDirection` exists because a portal can leave the DOM `dir` subtree. Behavior context follows React ownership; CSS and HTML direction need explicit DOM placement. |
| Lifecycle and cleanup | Popup roots own state, focus, inertness, Escape, outside interaction, and exit transitions. Nested portal reports show cleanup and ownership need integration tests. |
| Diagnostics | No generic provider collision, cross-root, or missing-context diagnostics were found. CSP failures are observable browser policy errors rather than library diagnostics. |

**Docs and unresolved findings:**
[DirectionProvider](https://base-ui.com/react/utils/direction-provider),
[CSPProvider](https://base-ui.com/react/utils/csp-provider), and
[quick-start portal setup](https://base-ui.com/react/overview/quick-start).

## 8. Forms, trust, assets, performance, and upgrades

- Base UI form controls extend native constraint validation, keep native form
  names/submission, and add client and server validation APIs. **Docs, high:**
  [forms](https://base-ui.com/react/handbook/forms).
- shadcn recipes often add a form store. That can improve application
  ergonomics but is not required for Citry's native server-form baseline.
  **Docs and inference, high.**
- React normally escapes text, but copied source may introduce raw HTML,
  unsafe URL forwarding, or arbitrary attribute behavior. Registries can add
  code and dependencies, so a registry is a software supply-chain trust
  boundary, not a theme catalog. **Inference, high confidence.**
- Base UI bundles no CSS. shadcn installs Tailwind-oriented source and semantic
  variables; icons and specialist recipes add dependencies. No normalized
  payload measurement was made. **Docs, high for delivery; unresolved for
  payload.**
- Base UI is tree-shakable but uses client behavior and portals. shadcn's static
  visual pieces may be server-renderable while behavior-base imports are
  client code. Exact React Server Component boundaries vary by copied file and
  base. **Docs and issue history, medium-high.**
- Installed packages receive normal dependency updates. Copied components need
  deliberate diff, overwrite, or manual merge. Changing shadcn base changes
  part APIs and behavior contracts, not merely styling. **Docs and inference,
  high.**

## 9. Material shortcomings and complaint evidence

| ID | Pattern | Status and impact | Evidence |
|---|---|---|---|
| BSR-1 | Source ownership has no automatic three-way upgrade path for locally edited components | Recurring current friction. The CLI offers `--diff` and `--overwrite`, but users report manual merge/version-tracking problems. Accessibility and security fixes can therefore diverge per app | [Discussion 790](https://github.com/shadcn-ui/ui/discussions/790) plus [CLI](https://ui.shadcn.com/docs/cli), grade C for recurrence and A for current tool limits |
| BSR-2 | Choosing Base UI, Radix, or React Aria creates multiple non-compatible implementations behind the same catalog | Deliberate product trade-off. Existing projects stay on their base; migration is component-by-component and local customizations magnify the cost | [July 2026 changelog](https://ui.shadcn.com/docs/changelog), grade A; [migration report 9562](https://github.com/shadcn-ui/ui/discussions/9562), grade D supporting report |
| BSR-3 | Nested portaled controls can conflict over focus, inertness, Escape, and pointer suppression | Recurring Radix-lineage friction visible through shadcn Drawer/Sheet and Select combinations. Some reports are fixed by aligned versions, so this is an integration/version risk rather than one universal current defect | [Radix issue 3520](https://github.com/radix-ui/primitives/issues/3520) and [issue 3432](https://github.com/radix-ui/primitives/issues/3432), grade C |
| BSR-4 | Strict CSP support differed across the lineage | Current Radix users reported missing nonce support; Base UI now has an explicit provider. Treat as a resolved architectural gap for the default base but a continuing risk for Radix-based copied projects | [Radix discussion 3130](https://github.com/radix-ui/primitives/discussions/3130) and [Base CSPProvider](https://base-ui.com/react/utils/csp-provider), grade B for maintainer/community lineage and A for current Base contract |
| BSR-5 | Headless primitives transfer visual accessibility and consistent wrapping to every consumer | Deliberate limitation. Base UI handles behavior but says focus visuals, contrast, and labels still require author work; one current user asks how to wrap every primitive into a coherent default system | [Accessibility](https://base-ui.com/react/overview/accessibility) and [Base issue 2916](https://github.com/mui/base-ui/issues/2916), grade A for the limitation and D for the individual report |

Versioned detail: BSR-1 recurs in reports dated 2024-10-01, 2025-02-13,
2025-07-18, and 2026-02-23; current workarounds are CLI diff/overwrite,
wrappers, and manual merge. BSR-2 is a July 2026 documented contract; the
supporting migration report is dated 2026-02-05. BSR-3 combines a Select in
Drawer report opened 2025-05-01 and a focus-scope report opened 2025-03-27;
both were closed by the snapshot, and aligned current packages or changed
modal/portal composition were reported workarounds. It is retained as
integration lineage, not a universal current defect. BSR-4 had recurring
Radix reports through 2025-07-26 and 2026-02-05 before the discussion closed
on 2026-02-18 pointing to Base UI's nonce provider. BSR-5's supporting Base UI
question was opened 2025-10-04 and remained open at the snapshot; the verified
limitation is current official documentation.

### Complaint search log

Searches covered every named layer and the 2024-07-23 through 2026-07-23
window. Older reports were used only where current docs or activity confirmed
the mechanism.

- `site:github.com/mui/base-ui/issues "Base UI" "opened" "2026" Combobox`
- `site:github.com/mui/base-ui/issues "Base UI" "2025" Dialog focus`
- `site:github.com/mui/base-ui/issues "Base UI" CSP portal SSR bug`
- `site:github.com/mui/base-ui/issues "Base UI" form submit accessibility`
- `site:github.com/shadcn-ui/ui/issues shadcn update overwrite diff accessibility 2025 2026`
- `site:github.com/shadcn-ui/ui/discussions update components upstream changes source code 2025 2026`
- `site:github.com/radix-ui/primitives/issues Radix accessibility dialog select portal 2025 2026`
- `site:github.com/radix-ui/primitives/discussions CSP nonce 2025 2026`
- `repo:adobe/react-spectrum is:issue created:2024-07-23..2026-07-23 "react-aria-components" (shadcn OR registry)`
- `repo:TanStack/table is:issue created:2024-07-23..2026-07-23 React (accessibility OR keyboard OR virtual OR shadcn)`

The Base UI tracker search yielded fewer stable, independently corroborated
current defects than expected. Its detailed release log shows many recent
focus, form, SSR, and accessibility fixes, but release churn alone is not a
complaint. This dossier therefore retains mechanism-backed limitations and
does not manufacture a defect quota. Broader React Aria complaint evidence is
de-duplicated in [its own dossier](recon-react-aria.md); no separate report was
retained here without a verified shadcn registry outcome. The TanStack search
did not yield a current wrapper-specific complaint strong enough to retain;
Data Table remains a documented external dependency and specialist recipe.

## 10. Citry conclusions

### Adopt or re-derive

- Named, removable compound parts with public state attributes.
- Reason-bearing, cancelable state-change events for nested interactive UI.
- A semantic token layer plus state and part hooks, with the behavior layer
  independently usable.
- Explicit providers for direction, portal policy, generated IDs, CSP nonce,
  and other tree-scoped values.
- CLI dry-run and diff concepts if Citry ever offers optional source export.
- Full-stack recipes, such as Data Table, documented as recipes over specialist
  dependencies rather than pretending every workflow is one primitive.

### Do not transfer directly

- React, React Context, or a second portal/focus runtime.
- Source copy as the only official delivery path. It weakens centralized
  accessibility, security, compatibility, and upgrade fixes.
- A component name that silently changes its behavior foundation by project.
- Generic registry execution without provenance, review, and dependency
  policy.
- `asChild` or render replacement without a Citry-native contract for
  attributes, refs/identity, Events, and semantic responsibility.

### Pressure on Citry contracts

Citry needs behavior-level reasons and cancellation in addition to styled
events, stable compound-part identity across morphs, and ambient context that
follows component ownership through teleports. The future provide/inject spike
must cover nested override, reactive updates, CSP nonce, direction, theme,
portal roots, cleanup, and diagnostics. It must compare `$component.init()`
methods with `$provide`/`$inject` magics without presuming both are needed.

The styled package should remain installed and centrally updatable. A later
source-export tool may be valuable for exceptional customization, but this
dossier shows why it must record provenance and support reviewable upstream
diffs. Localization architecture remains separate follow-up work.
