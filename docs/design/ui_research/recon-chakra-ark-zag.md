# Phase 4 dossier: Chakra UI, Ark UI, and Zag

**Snapshot:** 2026-07-23. **Studied lines:** `@chakra-ui/react` 3.36.1,
`@ark-ui/react` 5.37.2, the Zag 1.41.2 components actually pinned by that Ark
release, and current Zag core 1.42.0 as direct-project context. **Evidence
scope:** current official documentation, tagged package/source metadata, and
the three projects' issue trackers within the Phase 3 complaint window. No
local runtime reproduction was run.

Evidence labels are **Docs**, **Source/release**, **Maintainer report**, **User
report**, and **Inference**. Confidence grades follow the
[Phase 3 protocol](candidate-map.md#52-complaint-sample-and-confidence). This is
one architectural unit for comparison, but complaints and versions retain
their originating layer.

## 1. Product snapshots and relationship

Chakra UI 3.36.1 is an MIT-licensed styled React suite. Its tagged manifest
requires React 18.0.0 or newer, Emotion, and Ark UI React 5.37.2. Ark UI 5.37.2 is
an MIT-licensed headless multi-framework component layer whose React package
pins Zag component packages at 1.41.2. Current direct Zag core is 1.42.0 at the
snapshot, so “latest Zag” and “Zag underneath current Chakra” are not the same
version. [Chakra manifest](https://github.com/chakra-ui/chakra-ui/blob/%40chakra-ui%2Freact%403.36.1/packages/react/package.json)
and [Ark manifest](https://github.com/chakra-ui/ark/blob/%40ark-ui%2Freact%405.37.2/packages/react/package.json),
**Source/release, high confidence. Counterevidence:** package managers may
deduplicate compatible transitive packages. Unresolved: complete transitive
payload and license audit.**

The intended pipeline is explicit: Zag implements framework-agnostic state
machines and interaction logic; Ark connects those machines to framework
components and exposes headless parts; Chakra composes Ark parts with a styled
system. [Chakra contributing architecture](https://chakra-ui.com/docs/get-started/contributing),
**Docs, high confidence. Counterevidence:** not every simple Chakra primitive
needs an Ark/Zag machine. Unresolved: an export-by-export provenance map was
not generated.**

All three reviewed cores are open source with no paid component gate. Chakra
and Ark maintain separate repositories and release lines; this gives the
headless layer independent consumers but also creates a versioned integration
boundary. **Source/inference, high confidence from the manifests and
repositories. Counterevidence:** coordinated maintainers can resolve changes
quickly. Unresolved: compatibility policy and support SLA across all three
lines were not found.**

This is the clearest current reference for Citry's desired styled/headless
pair. It proves the product shape is viable, but its runtime code cannot be
reused: Chakra and Ark require React, and Zag is JavaScript behavior machinery
outside Citry's Alpine-owned component runtime. **Inference, high confidence
from package peers and the Citry charter. Counterevidence:** statecharts and
generated prop contracts can still transfer as design and test artifacts.
Unresolved: whether any Zag algorithms can be re-derived without importing a
parallel runtime.**

## 2. Normalized full inventory

### Chakra styled suite

The normalized list follows the 3.36.1 tagged source tree and current public
catalog. Internal helpers are grouped under utilities. **Docs and Source, high
confidence:** [catalog](https://chakra-ui.com/docs/components/concepts/overview)
and [tagged component tree](https://github.com/chakra-ui/chakra-ui/tree/%40chakra-ui%2Freact%403.36.1/packages/react/src/components).
**Counterevidence:** some newly present source families may still have limited
documentation. Unresolved: stability labels need heatmap review.**

| Citry category | Chakra families |
|---|---|
| Foundations | ChakraProvider/system, Box, Text, Heading, Span, Strong, Em, Link, Image, Icon, tokens, semantic tokens, conditions, recipes, slot recipes, LocaleProvider, EnvironmentProvider, Portal, Presence, VisuallyHidden, SkipNav |
| Layout | AbsoluteCenter, AspectRatio, Bleed, Center, Circle, Container, Flex, Float, Grid, Group, SimpleGrid, Spacer, Square, Stack, Sticky, Wrap |
| Actions | Button, IconButton composition, CloseButton, Toggle, Clipboard, DownloadTrigger |
| Forms | Field, Fieldset, Input, InputAddon/Element/Group, Textarea, NativeSelect, Checkbox, CheckboxCard, RadioGroup, RadioCard, Switch, Slider, NumberInput, PinInput, RatingGroup, SegmentGroup, Select, Combobox, Listbox, TagsInput, Editable, ColorPicker, DatePicker, FileUpload |
| Navigation | Accordion, Breadcrumb, Menu, Navigation-like list compositions, Pagination, Steps, Tabs, TreeView |
| Feedback | Alert, EmptyState, Loader, Spinner, Skeleton, Progress, ProgressCircle, Status, Toast |
| Overlays | ActionBar, Dialog, Drawer, HoverCard, Menu, Popover, Tooltip, FloatingPanel, Carousel overlays, FocusTrap, Portal |
| Data display | Avatar, Badge, Blockquote, Card, Carousel, Code, CodeBlock, ColorSwatch, DataList, Highlight, Kbd, List, Marquee, Mark, QRCode, Quote, ScrollArea, Separator, Stat, Table, Tag, Timeline |
| Utilities | ClientOnly, Collapsible, Environment, For, Format, Presence, Show, Splitter and responsive/condition helpers |
| Specialist boundary | DatePicker, ColorPicker, QRCode, CodeBlock, Carousel, FileUpload, and Marquee are distinctive built-ins. Charts, maps, rich text, and domain data grids are not core suite claims. |

### Ark headless breadth

Ark 5.37.2 exposes Accordion, AngleSlider, Avatar, Carousel, Checkbox,
ClientOnly, Clipboard, Collapsible, Collection, ColorPicker, Combobox,
DateInput, DatePicker, Dialog, DownloadTrigger, Drawer, Editable, Field,
Fieldset, FileUpload, FloatingPanel, FocusTrap, Format, Frame, Highlight,
HoverCard, ImageCropper, JsonTreeView, Listbox, Marquee, Menu,
NavigationMenu, NumberInput, Pagination, PasswordInput, PinInput, Popover,
Portal, Presence, Progress, QRCode, RadioGroup, RatingGroup, ScrollArea,
SegmentGroup, Select, SignaturePad, Slider, Splitter, Steps, Swap, Switch,
Tabs, TagsInput, Timer, Toast, Toggle, ToggleGroup, Tooltip, Tour, and
TreeView. [Ark catalog](https://ark-ui.com/docs/overview/about) and
[5.37.2 source](https://github.com/chakra-ui/ark/tree/%40ark-ui%2Freact%405.37.2/packages/react/src/components),
**Docs and Source, high confidence. Counterevidence:** Chakra may offer styled
equivalents under different names or compositions. Unresolved: exact parity
and release maturity per framework adapter.**

Ark therefore has headless families not surfaced as styled Chakra products,
including ImageCropper, JsonTreeView, NavigationMenu, PasswordInput,
SignaturePad, Swap, Timer, and Tour. Conversely, Chakra has visual/layout
primitives that need no Ark machine. Styled/headless parity must be assessed
per family rather than inferred from the shared brand. **Source/inference,
high confidence. Counterevidence:** application recipes can style any Ark
family. Unresolved: whether Chakra plans first-party styled wrappers.**

## 3. Delivery, dependencies, and ownership

Chakra is an installed React and Emotion runtime. It uses a Panda-derived
system configured at runtime with `createSystem` and passed to ChakraProvider.
Ark is an installed headless runtime. Zag supplies state machines and DOM prop
getters beneath it. Ordinary Chakra consumption therefore has at least three
versioned behavior/style layers, even though the application imports one main
package. [Theming overview](https://chakra-ui.com/docs/theming/overview) and
[architecture](https://chakra-ui.com/docs/get-started/contributing), **Docs,
high confidence. Counterevidence:** the package manager and maintainers hide
most coordination from ordinary users. Unresolved: real bundle attribution by
layer.**

No source-copy step is required, but Chakra's CLI can generate snippets and
theme typings. Icons and fonts are not imposed as a single bundled brand set;
applications commonly choose icons. [CLI](https://chakra-ui.com/docs/get-started/cli),
**Docs, high confidence. Counterevidence:** generated snippets become local
source to maintain. Unresolved: payload of representative routes.**

React, Emotion injection, and client state machines violate Citry's no-second-
runtime boundary. The architecture transfers more cleanly than the delivery:
separate behavior, headless parts, and styled recipes can map to Python
components plus Citry's Alpine runtime and prebuilt CSS. **Inference, high
confidence. Counterevidence:** reproducing mature machine behavior is costly.
Unresolved: code generation versus hand-maintained behavior contracts.**

## 4. Composition, state, and item identity

Chakra and Ark use explicit compound components such as `Dialog.Root`,
`Dialog.Trigger`, `Dialog.Positioner`, `Dialog.Content`, title, description,
and close parts. `as` changes the rendered element and `asChild` composes
behavior onto a child, with documented requirements to forward refs and props.
[Chakra composition](https://chakra-ui.com/docs/components/concepts/composition),
**Docs, high confidence. Counterevidence:** convenient snippets often wrap the
parts and reduce call-site verbosity. Unresolved: which wrappers are stable
package exports versus generated examples.**

Ark roots commonly expose controlled/uncontrolled state, callbacks, part
props, `data-scope`, `data-part`, and `data-state`, collection objects, and
`RootProvider` variants that accept a machine service created by a hook. Select
and Listbox use explicit collection item values rather than DOM position as
identity. [Ark Listbox](https://ark-ui.com/docs/components/listbox) and
[Ark styling](https://ark-ui.com/docs/guides/styling), **Docs, high
confidence. Counterevidence:** service/root-provider use is an advanced path,
not required for ordinary use. Unresolved: a suite-wide event-reason and
cancellation matrix was not found.**

Zag machines return prop getters and state from a framework-neutral model.
That separation is excellent design evidence for deriving identical styled
and headless semantics. It also means a defect in machine IDs, focus, or
collection state can propagate through every Ark framework and into Chakra.
**Docs plus inference, high confidence from the
[architecture](https://chakra-ui.com/docs/get-started/contributing).
Counterevidence:** framework adapters can repair platform-specific behavior.
Unresolved: ownership rules for fixes across the layers.**

## 5. Customization ladder

| Level | Mechanism | Assessment for Citry |
|---|---|---|
| Global tokens | `createSystem`, tokens with explicit values, semantic tokens, CSS variables, breakpoints and conditions | Strong typed semantic foundation |
| Themes and modes | ChakraProvider system, semantic color tokens, conditions; current color-mode setup composes `next-themes` | Powerful, but external provider layering adds SSR complexity |
| Component variants | Recipes and slot recipes with base, variants, sizes, defaults, and compound variants | One of the strongest transferable recipe models |
| Per instance | Style props, `css`, ordinary component props, data/ARIA where forwarded, `unstyled` on recipe contexts | Flexible, but runtime style resolution has performance cost |
| Parts | Ark/Chakra compound parts and `data-scope`/`data-part`/`data-state` | Excellent stable contract if versioned deliberately |
| Markup | `as`, `asChild`, snippets, or direct Ark parts | High control with explicit ref/prop forwarding responsibility |
| Behavior | Controlled roots, machine hooks, RootProvider, collection APIs | Deepest level before machine/source ownership |
| Source | MIT repositories and locally generated snippets | Possible escape hatch, but can split upgrades between package and app code |

Sources: [tokens](https://chakra-ui.com/docs/theming/tokens),
[recipes](https://chakra-ui.com/docs/theming/customization/recipes),
[slot recipes](https://chakra-ui.com/docs/theming/slot-recipes), and
[Ark styling](https://ark-ui.com/docs/guides/styling), **Docs, high confidence.
Counterevidence:** `unstyled` at Chakra's recipe layer still runs React, Ark,
and Zag. Unresolved: stable versioning policy for part names and data states.**

Citry should copy the architectural boundary, not the runtime: one behavior
contract should generate or power explicit headless parts and styled recipes.
The styled version may add wrappers only when it does not change semantics,
identity, keyboard, form participation, or events. **Inference, high
confidence. Counterevidence:** visual wrappers sometimes are necessary for
positioning. Unresolved: permitted DOM differences need a formal contract.**

## 6. Frozen comparison slice

| Probe | Chakra/Ark/Zag finding | Evidence and qualification |
|---|---|---|
| Button | Chakra supplies recipe variants, sizes, loading composition and polymorphism; simple Button does not need a Zag machine. Ark supplies Toggle for stateful press behavior. | [Chakra Button](https://chakra-ui.com/docs/components/button), Docs, high. Counterevidence: snippets may define loading details. Unresolved: pointer/keyboard press normalization was not reproduced. |
| Field and Input | Field and Fieldset compose labels, descriptions, errors, required/invalid/disabled state, and native controls; Ark can inject field IDs into control machines. | [Chakra Field](https://chakra-ui.com/docs/components/field) and [Ark forms](https://ark-ui.com/docs/guides/forms), Docs, high. Counterevidence: automatic wiring is convenient. Unresolved: CZA-4 shows a broken-reference edge. |
| Dialog | Root, Trigger, Backdrop, Positioner, Content, Title, Description, Close, Portal, focus, dismissal, controlled state, and lazy/presence behavior are explicit. | [Chakra Dialog](https://chakra-ui.com/docs/components/dialog), Docs, high. Counterevidence: snippets reduce verbosity. Unresolved: Citry morph and nested-dialog behavior cannot be inferred. |
| Combobox/searchable Select | Zag owns machine state, Ark exposes collections and parts, and Chakra adds recipes/snippets. Open state, input value, selected value, highlighted item, portal, virtual focus, and native hidden control are distinct concerns. | [Chakra Combobox](https://chakra-ui.com/docs/components/combobox) and [Ark Combobox](https://ark-ui.com/docs/components/combobox), Docs, high. Counterevidence: high-level examples cover ordinary cases. Unresolved: CZA-5 shows cross-boundary edge cases. |
| Tabs | Machine-driven value/focus plus explicit Root, List, Trigger, Indicator, and Content parts; horizontal/vertical and controlled modes. | [Chakra Tabs](https://chakra-ui.com/docs/components/tabs), Docs, high. Counterevidence: custom roots can alter semantics. Unresolved: dynamic removal and server reconciliation were not tested. |
| Table/DataTable | Chakra Table supplies styled semantic table parts and interactive styling, but no integrated sorting/filtering/virtualized grid engine. | [Chakra Table](https://chakra-ui.com/docs/components/table), Docs, high. Counterevidence: simple application tables benefit from staying native. Unresolved: a general data-grid companion recommendation belongs later. |
| Complex form/collection workflow | Ark hidden inputs make custom Checkbox, Radio, Select and similar controls participate in native form submission/reset; FileUpload and collection machines cover richer workflows. | [Ark forms](https://ark-ui.com/docs/guides/forms), Docs, high. Counterevidence: hidden controls can preserve native transport. Unresolved: autofill synchronization in CZA-5 and server-error/live-region integration. |
| Provider/context | ChakraProvider carries the style system; EnvironmentProvider supplies the correct document/root for machine DOM queries; LocaleProvider, color mode, and portals add other ambient values. | [EnvironmentProvider](https://chakra-ui.com/docs/components/environment-provider), [theming](https://chakra-ui.com/docs/theming/overview), Docs, high. Counterevidence: CSS variables and DOM `dir` carry many values naturally. Unresolved: exact nested shadowing and cross-portal matrix. |

## 7. Provider and ambient-context audit

| Question | Finding |
|---|---|
| Values carried | Styling system/tokens/recipes, color mode through `next-themes`, locale/direction, DOM environment/root, compound-root machine state, collections, and portal target. |
| Nesting and shadowing | React context permits nested providers; component roots also provide local machine context. A single published precedence table across ChakraProvider, LocaleProvider, EnvironmentProvider, and nested recipe contexts was not found. |
| Defaults and overrides | System recipes set defaults, provider value selects the system, component variants and style props override it, and `unstyled` can bypass recipe output. |
| Reactive updates | React provider props and machine services rerender subscribers. CSS variables propagate visual changes. Performance consequences appear in CZA-3. |
| Server/client agreement | Current Next.js guide composes ChakraProvider with `next-themes`, uses `suppressHydrationWarning`, and documents a webpack fallback for an Emotion/Turbopack hydration issue. |
| Portals | React context is logically retained, while content moves physically. Chakra Portal renders in place during SSR; client-only rendering may be needed for mismatch-sensitive content. Environment root and DOM direction still matter. |
| Lifecycle | React and machines own listeners, observers, focus, presence, and cleanup. Citry removal/morph/reconnect needs a separate lifecycle proof. |
| Diagnostics | Hooks fail or expose context when used under expected roots, but no broad missing-provider, cycle, stale-environment, or cross-root diagnostic framework was found. |

Sources: [Next.js guide](https://chakra-ui.com/docs/get-started/frameworks/next-app),
[Portal](https://chakra-ui.com/docs/components/portal), and
[EnvironmentProvider](https://chakra-ui.com/docs/components/environment-provider),
**Docs, high for published behavior. Counterevidence:** the framework guide
provides working first-party setup. Unresolved: React Router SSR, shadow DOM,
iframes, nested portals, and server-only rendering require direct tests.**

This architecture applies direct pressure for client provide/inject in Citry.
The prototype should compare `provide()`/`inject()` within `$component.init()`
with `$provide`/`$inject` magics for nesting, shadowing, reactive updates,
teardown, morphing, teleportation, missing providers, and server defaults.
Theme tokens should remain CSS custom properties where inheritance suffices;
machine services, portal policy, and environment roots are behavioral values.
**Inference, high confidence. Counterevidence:** first release could restrict
providers to the document root. Unresolved: public API location in core versus
`citry-ui`.**

## 8. Accessibility, forms, trust, and async behavior

Ark and Zag publicly target accessible roles, keyboard/focus behavior, native
form integration, and framework parity. Chakra adds visible styles, focus
rings, color tokens, direction, reduced-motion conditions, and touch-target
responsibility. This is a strong architecture, not independent conformance
proof. [Ark overview](https://ark-ui.com/docs/overview/about) and
[Chakra conditions](https://chakra-ui.com/docs/styling/conditional-styles),
**Docs claim, high as published intent. Counterevidence:** CZA-4 and CZA-5 are
current/recent accessibility edge cases. Unresolved: no public per-family
screen-reader matrix was found.**

Native form participation through hidden inputs is one of the best mechanisms
in this corpus. It preserves names and values for custom visual controls, but
the visible machine and browser-controlled hidden element must remain
synchronized for reset, autofill, required, disabled, and server errors.
[Ark forms](https://ark-ui.com/docs/guides/forms), **Docs, high.
Counterevidence:** native Checkbox/Radio roots are simpler where styling
permits. Unresolved: browser-by-browser autofill and no-JS fallback.**

React escapes ordinary text. The suite accepts URLs, arbitrary child content,
file selections, image sources, clipboard data, QR values, download targets,
and attribute forwarding through polymorphic composition. No general sanitizer
or safe-protocol policy was found; application trust boundaries remain
necessary. FileUpload cannot replace server validation of filename, type,
content, size, preview, and authorization. **Docs plus inference, medium-high
from [FileUpload](https://chakra-ui.com/docs/components/file-upload) and
[composition](https://chakra-ui.com/docs/components/concepts/composition).
Counterevidence:** explicit composition is necessary for trusted rich UI.
Unresolved: raw-HTML and URL-protocol source audit.**

Machines expose loading/open/invalid states where relevant, but remote request
cancellation, stale-result rejection, retry, and transport are application
work. Citry must connect those states to Events without letting an old response
overwrite a newer collection. **Inference, high confidence from the absence of
a transport in [Ark Combobox](https://ark-ui.com/docs/components/combobox).
Counterevidence:** controlled state makes application handling possible.
Unresolved: canonical async examples were not audited.**

RTL/locale provider features are inventory evidence only. Citry localization
keys, catalogs, selection, plural rules, and server/client agreement remain the
separate follow-up already chosen. Forced colors, zoom, representative screen
readers, touch, virtual keyboards, and IME require direct acceptance testing.
**Docs plus unresolved evidence; no broad conformance claim.**

## 9. Assets, CSP, SSR, performance, and upgrades

- Chakra uses Emotion as a peer and resolves recipes/style props at runtime.
  It imposes no single font or icon set. [3.36.1 manifest](https://github.com/chakra-ui/chakra-ui/blob/%40chakra-ui%2Freact%403.36.1/packages/react/package.json),
  **Source, high. Counterevidence:** Emotion caching and tree-shaking reduce
  repeated work. Unresolved: route payload and runtime cost measurements.**
- No current first-party strict-CSP guide was found in the reviewed Chakra
  docs. Emotion supports configured style insertion, but nonce setup and
  inline positioning need an application prototype. **Documentation absence
  plus inference, low-medium. Counterevidence:** lack of a guide does not mean
  CSP is impossible. Unresolved: nonce, hashes, `style-src-attr`, portals, and
  SSR extraction.**
- SSR is supported through React frameworks, but current Next.js setup needs a
  client provider, color-mode agreement, hydration-warning handling, and a
  documented bundler workaround. [Next.js guide](https://chakra-ui.com/docs/get-started/frameworks/next-app),
  **Docs, high. Counterevidence:** the guide supplies a tested route.
  Unresolved: behavior after framework/Emotion updates.**
- The 2.0.0-to-3.0.0 migration replaces many single components with compound APIs,
  changes style/theming configuration, removes or relocates features, moves
  color mode to `next-themes`, and provides CLI snippets and guidance.
  [Migration guide](https://chakra-ui.com/docs/get-started/migration), **Docs,
  high. Counterevidence:** explicit mappings and snippets reduce effort.
  Unresolved: measured cost for deeply wrapped applications.**

Citry cannot ship these JavaScript layers directly under its charter. A
prebuilt CSS recipe output and Citry-owned behavior runtime can nevertheless
preserve their architectural split without imposing Node on consumers.
**Inference, high confidence.**

## 10. Material shortcomings and complaint register

The retained patterns are de-duplicated across Chakra, Ark, and Zag for
2024-07-23 through 2026-07-23. Layer attribution prevents counting one machine
bug three times.

| ID | Pattern | Window evidence, workflow, response, workaround, and status | Classification |
|---|---|---|---|
| CZA-1 | SSR styling and color-mode providers create hydration and bundler integration friction | Current [Next.js guidance](https://chakra-ui.com/docs/get-started/frameworks/next-app) requires `suppressHydrationWarning` and documents a webpack fallback for Emotion with Turbopack. [Chakra issue 10730](https://github.com/chakra-ui/chakra-ui/issues/10730), opened 2026-03-25 against 3.34.0 and closed not planned, reports a React Router SSR prop-order mismatch without a complete reproduction. Workarounds are the first-party provider setup, deterministic server/client inputs, and documented bundler choice. | Grade A for current documented setup cost; grade D for the individual issue. Counterevidence: first-party Next setup is available and works for many apps. Unresolved: 3.36.1 plus current Turbopack and non-Next SSR matrix. |
| CZA-2 | The 2.0.0-to-3.0.0 migration breadth creates wrapper, theme, and provider upgrade cost | The [official migration guide](https://chakra-ui.com/docs/get-started/migration) documents compound-API replacements, removed/renamed features, provider changes, new snippets, and `next-themes`. Multiple search results concern missing component-specific mappings, but no one report is treated as prevalence proof. | Current deliberate major-version cost, grade A. Counterevidence: CLI snippets and explicit tables materially help. Unresolved: real application effort and stability of future major migrations. |
| CZA-3 | Runtime recipe resolution has produced repeated large-list/render performance reports | [Issue 10413](https://github.com/chakra-ui/chakra-ui/issues/10413), opened 2025-10-24 against 3.15.0 and closed not planned, links multiple 3.0.0-series render regressions. [Issue 10878](https://github.com/chakra-ui/chakra-ui/issues/10878), opened 2026-07-03 against 3.33.0 and closed, profiles recipe compilation/style resolution in a 50-row table and reports a userland static-recipe workaround. The latter may be resolved in 3.36.1, so it is retained as architecture history, not a current defect claim. | Recurring reports, grade C; grade B for the instrumented resolved report. Counterevidence: latest-version fix status and production benchmarks were not verified. Unresolved: 3.36.1 cold mount, update, memory, and CSS serialization costs. |
| CZA-4 | Automatic Field-to-machine label wiring can create broken ARIA references | [Ark issue 3824](https://github.com/chakra-ui/ark/issues/3824), opened 2026-03-17 with Zag 1.31.1 and closed not planned, gives a source-level reproduction where Checkbox/Switch hidden inputs point `aria-labelledby` at a missing Field label even when `aria-label` exists. It identifies both Zag prop getters and Ark Vue Field ID override. Workaround is rendering the expected visible label or manually verifying the hidden input wiring. | Source-specific maintainer-triaged report, grade B. Counterevidence: affected version predates Ark's pinned Zag 1.41.2 and current behavior was not reproduced. Unresolved: whether every framework and current version remains affected. |
| CZA-5 | Combobox state split across visible input, portal, machine, collection, and hidden native control produces integration edge cases | [Zag issue 2936](https://github.com/chakra-ui/zag/issues/2936), opened 2026-01-19 against Chakra 3.31.0 and open/stale, reports VoiceOver cannot browse portaled options on macOS/iOS. [Ark issue 3779](https://github.com/chakra-ui/ark/issues/3779), opened 2026-02-11 against 5.31.0 and closed not planned, reports browser autofill updates the hidden select but not visible value/machine state. Portal avoidance may help the first; no verified general autofill workaround was found for the second. | Two current/recent reports on distinct boundaries, grade C as a distributed-state risk. Counterevidence: neither was reproduced on Chakra 3.36.1/Ark 5.37.2. Unresolved: browser/AT/version matrix and accepted hidden-control synchronization policy. |

### Complaint search log

Exact searches were logged for every named layer:

Chakra UI:

- `repo:chakra-ui/chakra-ui is:issue created:>=2024-07-23 accessibility`
- `repo:chakra-ui/chakra-ui is:issue created:>=2024-07-23 hydration`
- `repo:chakra-ui/chakra-ui is:issue created:>=2024-07-23 migration v3`
- `repo:chakra-ui/chakra-ui is:issue created:>=2024-07-23 performance`

Ark UI:

- `repo:chakra-ui/ark is:issue created:>=2024-07-23 accessibility`
- `repo:chakra-ui/ark is:issue created:>=2024-07-23 form`

Zag:

- `repo:chakra-ui/zag is:issue created:>=2024-07-23 accessibility`
- `repo:chakra-ui/zag is:issue created:>=2024-07-23 combobox`

Load-bearing styling and provider dependencies:

- `repo:emotion-js/emotion is:issue created:2024-07-23..2026-07-23 (SSR OR hydration OR CSP)`
- `repo:pacocoursey/next-themes is:issue created:2024-07-23..2026-07-23 (hydration OR CSP OR provider)`

Each retained page was opened directly for date, reported version, status,
reproduction, workaround, and maintainer outcome. Zag search also found many
completed accessibility and Combobox fixes; that is important counterevidence
to a “machines are broadly broken” narrative. No credible current security or
CSP complaint survived this sample; both remain under-researched. Emotion and
next-themes were searched because Chakra's current SSR and color-mode setup
depends on their behavior. No independent issue from either tracker was
retained without a verified Chakra workflow outcome, so CZA-1 remains one
de-duplicated integration finding.

## 11. Citry conclusions

### Adopt or re-derive

- A clearly versioned behavior layer, headless part layer, and styled recipe
  layer with shared semantics and tests.
- Compound parts with stable `data-scope`, `data-part`, and `data-state`
  vocabulary.
- Machine/service access for advanced control without making it the ordinary
  component API.
- Native hidden-form participation for custom controls, paired with exhaustive
  autofill/reset/required/disabled/server-error tests.
- Typed semantic tokens, recipes, slot recipes, variants, defaults, and
  compound variants compiled to prebuilt CSS where possible.
- An EnvironmentProvider-like contract for document, shadow root, iframe,
  portal target, and DOM queries.

### Do not transfer directly

- React, Emotion, Ark adapters, or Zag JavaScript as a second runtime.
- Three independently moving public layers without a tested Citry compatibility
  matrix and synchronized releases.
- `asChild`-style composition that silently loses props, refs, semantics, or
  ownership when a Python template supplies an incompatible child.
- Runtime recipe compilation on every component instance when deterministic
  CSS can be built into the wheel.
- Portaled or hidden-control patterns without representative screen-reader,
  mobile, autofill, and native-form evidence.
- Localization architecture merely because the comparison suite has a locale
  provider; that remains separate follow-up work.

### Pressure on Citry's public contracts

The strongest pressure is for a public behavior/part contract that both styled
and headless Python components consume. It needs stable item identity,
controlled and uncontrolled state, change reasons, cancellation boundaries,
form participation, generated IDs, data-state attributes, named parts,
presence, portals, and lifecycle cleanup under fragments and morphing.

The provider study also makes the client-side provide/inject question
concrete. Citry needs to decide whether `$component.init()` owns
`provide()`/`inject()` or Alpine-style `$provide`/`$inject` magics expose it.
The decision must cover nesting, shadowing, reactive changes, missing-provider
diagnostics, portal logical ancestry, physical DOM environment, teardown,
reconnect, and server defaults. CSS inheritance should continue to carry
visual tokens and `dir` whenever it can. **Inference, high confidence from the
provider and complaint audits. Counterevidence:** a root-only first release
would reduce complexity. Unresolved: core-Citry versus `citry-ui` ownership.**

The most important Phase 5 experiments are one shared Button/Field/Dialog/
Combobox/Tabs/Table slice across styled and headless exports, a portaled
Combobox with VoiceOver and native autofill, provider shadowing across morphs,
and prebuilt recipe CSS that needs no client compiler.
