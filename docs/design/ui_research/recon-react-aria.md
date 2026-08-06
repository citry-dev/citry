# Phase 4 dossier: React Aria Components

**Snapshot:** 2026-07-23. **Studied line:** `react-aria-components`
1.19.0. **Evidence scope:** current official documentation, release and license
metadata, and the project's issue and discussion tracker. No local runtime
reproduction was performed in this phase.

Evidence labels used below are **Docs**, **Source/release**, **Maintainer
report**, **User report**, and **Inference**. Confidence grades follow the
[Phase 3 protocol](candidate-map.md#52-complaint-sample-and-confidence).

## 1. Product snapshot

React Aria Components is an installed, unstyled React behavior library. The
current [catalog](https://react-aria.adobe.com/getting-started) exposes more
than fifty component families plus lower-level interaction and utility hooks.
It deliberately ships no visual style layer; its quick start instead offers
copyable CSS and Tailwind examples and Storybook starter kits. **Docs, high
confidence.**

The package is Apache-2.0 under the
[react-spectrum license](https://github.com/adobe/react-spectrum/blob/main/LICENSE).
No component paywall was found. It is maintained in Adobe's React Spectrum
monorepo and its current release metadata is published through the
[package registry](https://www.npmjs.com/package/react-aria-components) and
[project releases](https://github.com/adobe/react-spectrum/releases).
**Source/release, high confidence.**

The product is a strong behavior and accessibility reference, but it is not a
direct product-shape reference for Citry's styled default. A Citry user given
only the equivalent of React Aria would still need to invent or adopt a full
visual system. **Inference, high confidence, based on the documented absence
of styles.**

### Evidence boundary register

| Material area | Direct evidence | Confidence | Counterevidence and unresolved boundary |
|---|---|---|---|
| Product and version | `react-aria-components` 1.19.0 registry metadata, the Apache-2.0 repository license, and current official documentation | High | The monorepo contains React Spectrum and lower-level packages that are not part of this installed component surface. |
| Inventory | Every independently documented component family in the current [catalog](https://react-aria.adobe.com/getting-started) is named below | High | Hooks, child parts, utilities, and styling examples are not counted as additional component families. Documentation can move ahead of a published package. |
| Architecture and delivery | Official framework, styling, forms, modal, and provider documentation | High | No local bundle, SSR, portal, or browser reproduction was run. React behavior does not prove compatibility with Citry activation or morphing. |
| Dependencies and upgrade cost | The [1.19.0 package](https://www.npmjs.com/package/react-aria-components/v/1.19.0) declares React and React DOM peers and pins React Aria, React Stately, shared types, date utilities, SWC helpers, and a client-only marker | High for the manifest; medium-high for upgrade inference | A transitive license and bundle graph was not reproduced. Release cadence and public docs do not prove that an application's wrappers and CSS upgrade without changes. |
| Accessibility | Official quality, testing, and component documentation plus the issue evidence below | High for published process; medium for suite-wide outcome | This is not an independent WCAG conformance report. Visual contrast, focus appearance, target size, forced colors, and motion remain partly author-owned. |
| Content trust and security | Component contracts, React's normal rendering model, forms, FileTrigger, DropZone, link, modal, and provider APIs | Medium-high where documented; medium for inferred threats | No suite-level sanitizer, URL-policy, CSP, file-validation, or threat-model document was found. The detailed threat cases below are acceptance risks, not claims of known vulnerabilities. |

## 2. Normalized inventory

The inventory below names every independently documented current component
family rather than collapsing date, color, collection, or file-interaction
families. Exported compound parts and lower-level hooks are not counted again.
**Docs, high confidence:** [catalog](https://react-aria.adobe.com/getting-started).

| Citry category | React Aria families |
|---|---|
| Actions | Button, Link, ToggleButton, ToggleButtonGroup |
| Native-form-oriented controls | Checkbox, CheckboxGroup, Form, Group, NumberField, RadioGroup, SearchField, Select, Slider, Switch, TextField |
| Searchable and selectable collections | Autocomplete, ComboBox, GridList, ListBox, TagGroup, Tree |
| Date and time | Calendar, DateField, DatePicker, DateRangePicker, RangeCalendar, TimeField |
| Color | ColorArea, ColorField, ColorPicker, ColorSlider, ColorSwatch, ColorSwatchPicker, ColorWheel |
| Files and drag targets | DropZone, FileTrigger |
| Navigation and disclosure | Breadcrumbs, Disclosure, DisclosureGroup, Menu, Tabs, Toolbar |
| Overlays and feedback | Modal, Popover, Toast, Tooltip |
| Data and status | Meter, ProgressBar, Table, Virtualizer |
| Layout and structure | Separator |
| Interaction utilities | press, hover, focus, focus-visible, long press, move, keyboard, drag and drop, FocusScope |
| Ambient utilities | I18nProvider, PortalProvider, SSRProvider, stable ID, locale, collator, date and number formatting |
| Missing as a product layer | Cards, application shell, grid/layout primitives, typography system, icons, theme tokens, density, branded variants, charts, maps, rich text |

The collection, date, color, drag-and-drop, and virtualizer coverage is much
deeper than a narrow primitive library. The missing items are chiefly visual
and application-shell jobs rather than interaction machinery. **Inference,
high confidence.** Counterevidence: some visual examples and starter kits are
published, but they are examples rather than a versioned product token and
recipe layer. Whether the catalog navigation and 1.19.0 exports are perfectly
synchronized remains unresolved.

## 3. Architecture, delivery, and composition

- Installation is a React package, with subpath examples such as
  `react-aria-components/Select`; the
  [framework guide](https://react-aria.adobe.com/frameworks) covers Next.js,
  React Router, Parcel, Vite, webpack, Rollup, and ESBuild. **Docs, high
  confidence.**
- Complex controls are explicit assemblies. The
  [Select quick start](https://react-aria.adobe.com/getting-started) composes
  Select, Label, Button, SelectValue, Popover, ListBox, and ListBoxItem instead
  of hiding all markup behind one component. **Docs, high confidence.**
- Components expose controlled and uncontrolled state, events, render props,
  state data attributes, semantic slots, and collection item identity. The
  [styling guide](https://react-aria.adobe.com/styling) documents default
  classes, functional `className` and `style`, render-prop state, slots, CSS
  variables, and entry/exit states. **Docs, high confidence.**
- Popovers and modals use portals and lifecycle-managed focus/visibility.
  `PortalProvider`, `SSRProvider`, `useId`, and `FocusScope` are public
  utilities in the catalog. Exact behavior under Citry morphing was not
  reproduced and remains unresolved. **Docs plus unresolved transfer risk.**
- The package supplies a second, React-specific client component and state
  runtime. Citry cannot adopt it directly under the charter, but can transfer
  its behavior contracts and tests. **Inference, high confidence.**

The 1.19.0 manifest requires React and React DOM as peers and installs pinned
React Aria and React Stately behavior layers, shared types, internationalized
date support, SWC helpers, and a client-only marker. Registry metadata reports
about 6.2 MB unpacked across 1,386 files, which is a publication size rather
than route payload. **Registry observation, high confidence:**
[1.19.0 package](https://www.npmjs.com/package/react-aria-components/v/1.19.0).
No tree-shaken browser measurement or complete transitive dependency and
license audit was run.

Upgrade cost has three distinct owners: the installed package graph, the
application's compound wrappers, and its CSS or Tailwind layer. Package updates
can deliver centralized behavior fixes, while application wrappers still need
regression tests when part structure, DOM output, state attributes, or typing
change. **Docs plus inference, medium-high confidence:**
[releases](https://github.com/adobe/react-spectrum/releases) and
[styling](https://react-aria.adobe.com/styling). Counterevidence is that public
semantic parts and state attributes intentionally reduce this coupling. No
representative application upgrade was reproduced, so merge effort and
breaking-change frequency remain unresolved.

## 4. Customization ladder

| Level | Available mechanism | Assessment |
|---|---|---|
| Tokens | No product token system; examples use an author-defined `--tint` | Insufficient for Citry's styled promise by itself |
| Variants | Author wrapper props and functional classes/styles | Flexible, but the consumer owns consistency |
| Parts | Explicit compound components and semantic slots | Excellent behavior-to-markup contract |
| State styling | `data-*` attributes and render-prop state | Strong and input-modality aware |
| Markup | Authors assemble documented parts and wrap them into their own APIs | High control with non-trivial assembly work |
| Behavior | Controlled state, interaction hooks, collection APIs, event callbacks | Very deep; this is the product's main value |
| Source | Installed package plus open source; examples can be copied | Forking is possible but not the normal delivery model |

Styled and headless Citry components should share similarly explicit parts,
states, identity, and event reasons, while adding a maintained token and recipe
layer. Copying React Aria's lack of defaults would contradict the charter.

## 5. Frozen comparison slice

| Probe | Current contract and finding | Evidence |
|---|---|---|
| Button | Normalizes press, hover, keyboard focus, touch, disabled, and pending visual states through events and data attributes | [Button and interaction catalog](https://react-aria.adobe.com/quality), Docs, high |
| Field and Input | TextField composes Label, Input, description, and error; labels are automatically associated | [Forms](https://react-aria.adobe.com/forms), Docs, high |
| Dialog | DialogTrigger, Modal, Dialog, title, close slots, focus management, dismissability, and entry/exit states are separate parts | [Modal](https://react-aria.adobe.com/Modal), Docs, high |
| ComboBox | Composes an input and ListBox; supports dynamic collections, sections, disabled items, async loading, and current single/multiple modes | [ComboBox](https://react-aria.adobe.com/ComboBox), Docs, high |
| Tabs | Exposes collection identity, orientation, selected state, and keyboard semantics; detailed behavior was not reproduced | [Tabs](https://react-aria.adobe.com/Tabs), Docs, medium-high |
| Table | Supports directional navigation, selection, sorting, hierarchy, drag and drop, and collection identity | [Table](https://react-aria.adobe.com/Table), Docs, high |
| Form/collection workflow | Browser submission, React actions or `onSubmit`, native constraints, custom/server errors, async loading, and collection utilities are documented | [Forms](https://react-aria.adobe.com/forms), Docs, high |
| Provider/context | I18nProvider, PortalProvider, SSRProvider, and contextual slots carry descendant configuration | [I18nProvider](https://react-aria.adobe.com/I18nProvider), Docs, high |

The slice exposes a consistent pattern: root components own state and semantic
relationships, while named child parts own DOM nodes. That is closer to the
needed Citry headless contract than a single template with a large kwargs
surface. **Inference, high confidence.**

## 6. Accessibility and interaction quality

### Ambient-context audit

| Question | Finding |
|---|---|
| Values carried | Locale/direction, portal target, SSR/stable-ID state, component slots, and overlay-trigger state are documented context uses. |
| Nesting and shadowing | I18nProvider applies to all descendants. Exact nested-provider and default-value rules were not explicitly documented in the pages reviewed and remain unresolved. |
| Reactive updates | A provider accepts the application locale as a prop; no cross-server update protocol exists because this is ordinary React state. Hydration behavior must not be assumed to transfer to Citry. |
| Portal behavior | React portals preserve React context even though DOM placement changes. React Aria adds PortalProvider and document-hiding/focus machinery; Shadow DOM required explicit fixes. |
| Lifecycle and cleanup | Overlay visibility, focus restoration, outside hiding, and exit animation are runtime-owned. Citry removal, morph, and reconnect behavior remains untested. |
| Diagnostics | No provider-cycle, missing-value, or cross-root diagnostic contract was found in the reviewed public docs. |

**Docs and unresolved findings:**
[I18nProvider](https://react-aria.adobe.com/I18nProvider),
[Modal](https://react-aria.adobe.com/Modal), and
[Shadow DOM issue 8675](https://github.com/adobe/react-spectrum/issues/8675).

The project says it follows WAI-ARIA and APG, manages roles, attributes,
keyboard and pointer events, focus, and announcements, and tests VoiceOver,
JAWS, NVDA, iOS VoiceOver, and Android TalkBack across listed browser pairs.
It also explicitly leaves labels, contrast, target size, visible focus, and
motion-sensitive visual design partly to the author.
[Quality documentation](https://react-aria.adobe.com/quality), **Docs claim,
high confidence that this is the published process, not an independent
conformance result.**

Direction-aware keyboard behavior and more than thirty localized internal
string sets are documented. Citry should treat the provider pattern and RTL
behavior as evidence, but defer translation-key and locale architecture as
already decided. **Docs, high confidence.**

The [testing guide](https://react-aria.adobe.com/testing) recommends semantic
queries and realistic user events and ships test helpers for CheckboxGroup,
ComboBox, Dialog, GridList, ListBox, Menu, RadioGroup, Select, Table, Tabs, and
Tree. Its need to manage timers and mock geometry for drag controls is also a
warning: headless correctness still requires real-browser and assistive-
technology tests. **Docs and inference, high confidence.**

Forced-colors behavior is not summarized as a suite guarantee in the sources
reviewed. Because React Aria ships no theme, the author owns forced-color and
reduced-motion visuals even where the behavior exposes appropriate state.
**Unresolved, medium confidence.**

## 7. Forms, trust, assets, and runtime

- Form controls preserve native names and submission and extend browser
  constraint validation; controlled submission and third-party form libraries
  are optional. **Docs, high:** [forms](https://react-aria.adobe.com/forms).
- FileTrigger selects files but does not define an upload transport. Remote
  collection loading is application code. Citry should retain the same
  separation between UI state and trusted server action. **Docs plus
  inference, medium-high.**
- The package ships no theme CSS, icons, fonts, or design assets. That lowers
  imposed asset cost but transfers the whole styled payload to consumers.
  Numeric JavaScript payloads were not verified. **Docs, high for asset
  absence; unresolved for payload.**
- SSR and stable-ID utilities exist, but no Citry fragment/morph compatibility
  can be inferred from React hydration support. **Docs plus inference, high.**
- No suite-level CSP guide was found in the reviewed material. Portal targets,
  generated IDs, inline positioning styles, and strict CSP require a separate
  prototype check. **Unresolved.**

### Content-trust and threat-case audit

This table separates documented ownership from proposed Citry tests. It does
not allege vulnerabilities in React Aria.

| Surface | Observed boundary | Citry acceptance threat case |
|---|---|---|
| Text, descriptions, errors, and collection labels | Normal React text children are escaped. Render props and application components can still return arbitrary markup; no library sanitizer contract was found. | Hostile remote labels, filenames, help text, validation messages, and table cell strings render as text. Any trusted-fragment escape hatch is separately named and reviewed. |
| Link and URL-bearing renderers | Link behavior composes with application routing and author-supplied destinations. The library does not document a URL-scheme allowlist. | Reject or explicitly delegate `javascript:`, unsafe `data:`, protocol-relative, redirect, image, and download URL policy. Test disabled and external-link behavior after element replacement. |
| Attribute and event routing | Compound parts and contextual slots route props to particular semantic nodes; author wrappers can spread extra attributes or replace output. | Verify which node receives `id`, `name`, `form`, `aria-*`, `data-*`, style, class, events, and refs. Prevent trusted internal handlers from being silently replaced. |
| FileTrigger and DropZone | These acquire browser `File` objects and interaction state, not a secure upload pipeline. MIME and `accept` hints are client affordances. | Server revalidates size, type, extension, content, filename, authorization, storage target, and archive handling. Drag payloads and rejected files do not become trusted HTML or URLs. |
| Generated IDs and SSR | SSRProvider and stable-ID utilities coordinate relationships under React rendering. Their guarantee does not cover Citry roots or server fragments. | IDs remain unique and deterministic across full render, fragments, repeated collections, morphs, portals, reconnects, and concurrent roots. Mismatches fail visibly without cross-linking labels. |
| ComboBox, Autocomplete, and async collections | Applications own remote fetching, ordering, errors, and the content returned by renderers. | Stale responses cannot overwrite current state; result labels remain text; selected identity survives reorder; server authorization is rechecked on submit. |
| Modal and portal infrastructure | The runtime owns focus scopes, restoration, outside-content hiding, portal targets, and document mutations. | Nested overlays, removed activators, Shadow DOM, morphing, failed transitions, and cross-root portals clean up inert/hidden state and restore focus safely. |
| Table and export | Table owns interaction and collection behavior. No first-party CSV, spreadsheet, or HTML export contract was found. | A future export feature must separately prevent formula injection, unsafe HTML, encoding ambiguity, and data disclosure. This risk is not attributed to current React Aria Table. |

**Evidence and confidence:** official [forms](https://react-aria.adobe.com/forms),
[FileTrigger](https://react-aria.adobe.com/FileTrigger),
[DropZone](https://react-aria.adobe.com/DropZone),
[Link](https://react-aria.adobe.com/Link),
[Modal](https://react-aria.adobe.com/Modal), and
[SSR documentation](https://react-spectrum.adobe.com/react-aria/ssr.html)
establish the component responsibilities with high confidence. URL policy,
sanitization, generated-ID failure modes outside React, and export threats are
medium-confidence security inferences. No public suite-level threat model was
found, which is the unresolved counterevidence boundary.

## 8. Material shortcomings and complaint evidence

The retained set is de-duplicated. It combines verified limitations and
current or historically useful issue evidence rather than treating issue count
as a score.

| ID | Pattern | Status and impact | Evidence |
|---|---|---|---|
| RA-1 | No built-in visual design, tokens, layout, icons, or density system | Deliberate trade-off, high impact for Citry's default-product goal; every consumer must assemble and maintain a styled layer | [Getting started](https://react-aria.adobe.com/getting-started) and [styling](https://react-aria.adobe.com/styling), current limitation, grade A |
| RA-2 | Compound assembly is powerful but verbose, and bespoke integration can require internal collection/context knowledge | Recurring integration friction. A 2024 discussion was answered in 2025 by introducing Autocomplete, so part of the reported need is resolved history; the general assembly cost remains | [Discussion 6281](https://github.com/adobe/react-spectrum/discussions/6281), maintainer response, grade B for the historical resolution; current docs, grade A for compound complexity |
| RA-3 | Portaled overlays require document-wide hiding and mutation management, which complicates native popover and non-standard host integration | Current architectural limitation; the cited report had no confirmed fix in the reviewed evidence, so the defect claim itself is not promoted | [Issue 7067](https://github.com/adobe/react-spectrum/issues/7067) plus current Modal/Portal APIs, grade A for the portal trade-off and grade D for the individual failure |
| RA-4 | Keyboard table drag-and-drop regressed when rows outnumbered columns | Open current defect reported against 1.12/1.13, with reproduction, maintainer diagnosis, and `textValue` workaround; high accessibility impact in the affected optional workflow | [Issue 9000](https://github.com/adobe/react-spectrum/issues/9000), grade B |
| RA-5 | Portal and focus infrastructure has needed explicit Shadow DOM integration fixes | Resolved-history warning for custom-element hosts rather than a current defect; relevant to Citry only as evidence that portal ownership and event roots must be tested | [Issue 8675](https://github.com/adobe/react-spectrum/issues/8675), linked test work, grade B |

Versioned detail: RA-2 has corroborating activity on 2024-08-22 and a
maintainer resolution on 2025-01-29. RA-3 was opened 2024-09-23 and was closed
by the snapshot; no current-version reproduction or verified workaround was
found, so only the documented portal mechanism survives as grade A. RA-4 was
opened 2025-10-09, remained open at the snapshot, affected 1.12.1 and 1.13,
and has a maintainer-suggested `textValue` workaround. RA-5 was opened
2025-08-06 against React Aria Components 1.11.0 and is marked closed and done
after linked Shadow DOM tests. RA-1 is a 1.19.0 current documentation
limitation rather than a dated user report.

### Complaint search log

All searches were run for the 2024-07-23 through 2026-07-23 window; older
results were retained only as background or when current contracts confirmed
the mechanism.

- `site:github.com/adobe/react-spectrum/issues "react-aria-components" ComboBox accessibility issue 2025 OR 2026`
- `site:github.com/adobe/react-spectrum/issues "react-aria-components" SSR hydration issue 2025 OR 2026`
- `site:github.com/adobe/react-spectrum/issues "react-aria-components" form validation issue 2025 OR 2026`
- `site:github.com/adobe/react-spectrum/issues "react-aria-components" bundle size issue 2025 OR 2026`
- `site:github.com/adobe/react-spectrum/issues "react-aria-components" portal Shadow DOM focus 2025 OR 2026`

No credible current broad payload or CSP complaint survived verification. That
is an evidence shortfall, not evidence that those risks are absent.

## 9. Citry conclusions

### Adopt or re-derive

- Root-owned state with explicit semantic parts and stable collection IDs.
- State data attributes that mean the same thing in styled and headless forms.
- Input-modality-normalized press, hover, focus-visible, and long-press
  behavior.
- Per-pattern keyboard tables and semantic test helpers.
- Native form participation plus controlled and server-error paths.
- Provider concepts for direction, portal targets, generated IDs, and future
  locale, with portal behavior tested across ownership changes.

### Do not transfer directly

- React, React Context, or React hydration as a second client runtime.
- An unstyled-only product that delegates all visual accessibility to users.
- DOM-wide hiding or portal machinery without proving Citry morph, teleport,
  cleanup, and nested-overlay behavior.
- The full date, color, virtualizer, and drag-and-drop breadth in the first
  release merely because a mature specialist library supports it.

### Pressure on Citry contracts

React Aria provides strong evidence for a client ambient-context mechanism,
but not its syntax. Citry must compare `$component.init()` provide/inject
methods with `$provide`/`$inject` magics for reactive direction, portal policy,
stable IDs, defaults, and nested overrides. The same context must survive
morphing and teleports without creating a second component tree. Localization
keys and catalogs remain separate follow-up work.

The largest unresolved transfer questions are compound-part ergonomics in
Python templates, collection identity across server fragments, and whether
Citry Events can express the same cancelable reason-bearing state transitions
without shipping a parallel client state library.
