# Phase 4 dossier: Mantine

**Snapshot:** 2026-07-23. **Studied line:** `@mantine/core` 9.4.2 and
same-version first-party packages. **Evidence scope:** current official
documentation, the 9.4.2 tagged source tree, package and license metadata, and
issue reports in the Phase 3 window. No local runtime reproduction was run.

Evidence labels are **Docs**, **Source/release**, **Maintainer report**, **User
report**, and **Inference**. Confidence grades follow the
[Phase 3 protocol](candidate-map.md#52-complaint-sample-and-confidence).
Material findings state counterevidence and unresolved limits; a missing report
is never treated as proof of quality.

## 1. Product snapshot

Mantine is an MIT-licensed, styled React suite. Core 9.4.2 peers on React and
React DOM 19.2.0, depends on the exact 9.4.2 hooks package, and uses Floating
UI, `react-number-format`, `react-remove-scroll`, and Type Fest. The
[9.4.2 package manifest](https://github.com/mantinedev/mantine/blob/9.4.2/packages/%40mantine/core/package.json)
freezes that dependency evidence. **Source/release, high confidence.
Counterevidence:** applications may already carry some peers. Unresolved: a
complete transitive payload and license audit was not run.**

The reviewed catalog has no paid component boundary. Core is accompanied by
first-party hooks, forms, dates, notifications, modals, spotlight, dropzone,
carousel, charts, rich-text, code-highlight, schedule, store, and styling
packages. The tagged repository shows frequent work and one versioned
monorepo. [Packages tree](https://github.com/mantinedev/mantine/tree/9.4.2/packages)
and [core catalog](https://mantine.dev/core/package/), **Source and Docs, high
confidence. Counterevidence:** one release train does not make every extension
equally general-purpose. Unresolved: maintenance ownership and support SLAs
per package were not found.**

Mantine is unusually relevant to Citry's two-surface goal. Most styled
components accept `unstyled`, while the tagged provider source also exports
`HeadlessMantineProvider`, which disables library classes and CSS variables.
This is a real supported style-suppression path, but it is not an independently
versioned behavior layer: styled and unstyled forms still use the same React
components and structural markup. [Unstyled components](https://mantine.dev/styles/unstyled/)
and [provider source](https://github.com/mantinedev/mantine/blob/9.4.2/packages/%40mantine/core/src/core/MantineProvider/MantineProvider.tsx),
**Docs and Source, high confidence. Counterevidence:** shared internals are
exactly how behavior parity can be preserved. Unresolved: which families emit
essential inline layout even when headless was not exhaustively audited.**

## 2. Normalized full inventory

The inventory normalizes public core families and separately marks extension
packages. It does not count internal bases, popovers, inputs, portals, or
formatters twice when they exist mainly to implement a public family. Sources:
[core catalog](https://mantine.dev/core/package/) and
[9.4.2 component tree](https://github.com/mantinedev/mantine/tree/9.4.2/packages/%40mantine/core/src/components),
**Docs and Source, high confidence. Counterevidence:** low-level exports such as
InputBase and ModalBase are public and remain relevant to composition.
Unresolved: experimental/new-family maturity was not scored.**

| Citry category | Mantine families |
|---|---|
| Foundations | MantineProvider, theme, CSS variables, colors, typography, direction hooks, responsive style props, Portal, Transition, VisuallyHidden |
| Layout | AppShell, AspectRatio, Center, Container, Flex, Grid, Group, SimpleGrid, Space, Splitter, Stack, Box/Paper/Surface-like primitives, Affix, FloatingWindow |
| Actions | Button, ActionIcon, CloseButton, CopyButton, FileButton, UnstyledButton, Burger, Chip, segmented and toggle-like controls |
| Forms | Fieldset, Input, InputBase, TextInput, Textarea, PasswordInput, NumberInput, MaskInput, JsonInput, Checkbox, Radio, Switch, Slider, AngleSlider, RangeSlider, ColorInput/Picker, FileInput, NativeSelect, Select, MultiSelect, Autocomplete, TagsInput, TreeSelect, PinInput, Rating, Combobox and PillsInput primitives |
| Navigation | Anchor, Breadcrumbs, Menu, Menubar, NavLink, Pagination, Stepper, Tabs, TableOfContents, Tree, AppShell navigation |
| Feedback | Alert, EmptyState, Loader, LoadingOverlay, Notification, Progress, RingProgress, SemiCircleProgress, Skeleton, Spoiler, Indicator |
| Overlays | Dialog, Drawer, HoverCard, Menu, Modal, Popover, Tooltip, Overlay, FocusTrap, Portal |
| Data display | Accordion, Avatar, BackgroundImage, Badge, Blockquote, Card, Code, DataList, Highlight, Image, Kbd, List, Mark, Marquee, Pill, ScrollArea, Scroller, Stat-like NumberFormatter/RollingNumber, Table, Timeline, Title, Typography, OverflowList |
| Utilities | Collapse, FloatingIndicator, FocusTrap, Portal, Transition, VisuallyHidden, formatters, `use-*` hooks |
| First-party extension packages | Carousel, Dates, Dropzone, Form, Modals, Notifications, NProgress, Spotlight, Store, Emotion and vanilla-extract integrations |
| Specialist companions | Charts, Tiptap rich text, Schedule, Code Highlight, Color Generator and MCP server are valuable adjacent products, not baseline generic-suite completeness |

Mantine's breadth sits between a primitive library and Ant Design: it supplies
strong layout, overlays, forms, and content primitives, while data-grid logic
is intentionally absent and Table is predominantly semantic/styling. **Docs
plus inference, high confidence from the inventory. Counterevidence:** Table
supports sticky headers, scrolling, captions, sorting examples, and data
helpers. Unresolved: extension-package heatmap scoring belongs in Phase 5.**

## 3. Architecture, delivery, and composition

Mantine is installed JavaScript plus imported CSS. Consumers may import the
aggregate `@mantine/core/styles.css` or per-component CSS files in documented
dependency order. There is no source-copy ownership model and no style compiler
required for the ordinary CSS path. [Styles delivery](https://mantine.dev/styles/mantine-styles/),
**Docs, high confidence. Counterevidence:** optional Emotion and
vanilla-extract packages provide other integrations. Unresolved: actual CSS
and JS sizes were not measured.**

Composition mixes conventional props with explicit compound families. Inputs
share Input and Input.Wrapper contracts; Combobox exposes Store, Target,
Dropdown, Options, Option, Empty, Chevron, EventsTarget, Search, and related
parts; Modal, Popover, Menu, Table, Tabs, and AppShell expose named children.
Controlled/uncontrolled hooks are common, and `renderRoot` replaces the root
element where polymorphic typing alone is insufficient.
[Polymorphic components](https://mantine.dev/guides/polymorphic/) and
[Combobox](https://mantine.dev/core/combobox/), **Docs, high confidence.
Counterevidence:** not every component is compound or polymorphic. Unresolved:
there is no suite-wide event reason/cancellation vocabulary.**

Popovers, modals, and menus use Floating UI, portals, focus traps, and scroll
locking. Portal placement can be disabled or targeted. React owns lifecycle
cleanup; this does not establish behavior under Citry morphing or Alpine
component removal. [Portal](https://mantine.dev/core/portal/) and
[Popover](https://mantine.dev/core/popover/), **Docs, high confidence for the
API, medium for transfer implications. Counterevidence:** disabling the portal
simplifies some nested/mobile cases. Unresolved: nested overlay, shadow-root,
and iframe behavior was not reproduced.**

## 4. Customization ladder and the two-surface lesson

| Level | Mantine mechanism | Assessment for Citry |
|---|---|---|
| Global tokens | Theme object and generated CSS variables for colors, spacing, radii, type, breakpoints, shadows, and component extensions | Broad and approachable; custom tokens require deliberate CSS-variable output |
| Theme variants | Color scheme, primary color/shade, luminance, focus and cursor policy, component `defaultProps`, `classNames`, `styles`, and `vars` | Strong global defaults; provider size can become an ambient catch-all |
| Component variants | Built-in size/variant/color plus `theme.components.*.extend` | Good recipe model, although variant typing and styling remain React-specific |
| Per instance | `className`, `style`, `classNames`, `styles`, `vars`, style props, data/ARIA and component props | Excellent ladder; inline `styles` cannot express pseudo-classes or media queries |
| Named parts | Styles API selectors and compound subcomponents | Stable named selectors are valuable; not every selector implies markup ownership |
| Headless | `unstyled` per component and `HeadlessMantineProvider` globally | Strong parity reference, but not a separately consumable headless package |
| Full ownership | Wrapper, theme extension, open-source fork | Source fork is possible, not the normal escape hatch |

Sources: [Styles API](https://mantine.dev/styles/styles-api/),
[unstyled mode](https://mantine.dev/styles/unstyled/), and
[MantineProvider](https://mantine.dev/theming/mantine-provider/), **Docs and
Source, high confidence. Counterevidence:** styles passed as inline objects are
less capable and less performant than classes, as the docs themselves warn.
Unresolved: selector stability policy across major versions was not found.**

Citry should adopt one shared behavior implementation and explicit style
suppression, but go further by making the headless contract independently
documented: semantic HTML, keyboard behavior, state attributes, parts, and
required structural CSS must be clear without the default theme. **Inference,
high confidence. Counterevidence:** separate exports can drift if not generated
from the same implementation. Unresolved: one class with `styled=False` versus
layered exports remains an API-design decision.**

## 5. Frozen comparison slice

| Probe | Mantine contract and finding | Evidence and qualification |
|---|---|---|
| Button | Styled variants, gradient, compact/icon-friendly forms, loading, disabled, left/right sections, polymorphism, Styles API, and `unstyled`. | [Button](https://mantine.dev/core/button/), Docs, high. Counterevidence: author owns link-versus-button semantics when changing root. Unresolved: press normalization was not reproduced. |
| Field and Input | Input.Wrapper connects label, description, required indicator, and error; input families reuse this structure and IDs. | [Input](https://mantine.dev/core/input/), Docs, high. Counterevidence: custom composition is possible. Unresolved: current conditional error mounting creates the complaint in M-2. |
| Dialog | Modal is the full modal overlay; Dialog is a simpler positioned notice. Modal provides focus trap, scroll lock, portal, title, overlay, transitions, and controlled state. | [Modal](https://mantine.dev/core/modal/) and [Dialog](https://mantine.dev/core/dialog/), Docs, high. Counterevidence: focus-trap disabling is available. Unresolved: restoration through server morphs cannot be inferred. |
| Combobox/searchable Select | Combobox is a public toolkit underpinning Select, MultiSelect, Autocomplete, TagsInput, and custom searchable collections; store and option values are explicit. | [Combobox](https://mantine.dev/core/combobox/), Docs, high. Counterevidence: high-level Select covers ordinary cases. Unresolved: mobile Safari reports in M-3. |
| Tabs | Root, List, Tab, Panel, controlled value, orientation, keyboard activation, styles, and unstyled mode are explicit. | [Tabs](https://mantine.dev/core/tabs/), Docs, high. Counterevidence: markup replacement remains bounded by part APIs. Unresolved: deletion and dynamic identity were not tested. |
| Table/DataTable | Table supplies semantic table markup, visual options, sticky header, scrolling, caption placement, and data-driven helpers, but no integrated grid state engine. | [Table](https://mantine.dev/core/table/), Docs, high. Counterevidence: simple CRUD tables need no grid engine. Unresolved: large-data virtualization is application work. |
| Complex form/collection workflow | `@mantine/form` supplies uncontrolled/controlled stores, nested paths, lists, validation, errors, dirty/touched state, and `getInputProps`; Dropzone/FileInput and Combobox families extend workflows. | [use-form](https://mantine.dev/form/use-form/), Docs, high. Counterevidence: native form elements remain underneath. Unresolved: server-native and no-JS paths are not the product focus. |
| Provider/context | MantineProvider supplies theme, color scheme manager, CSS variables, class strategy, nonce, root target, and environment options; HeadlessMantineProvider switches styling off. | [MantineProvider](https://mantine.dev/theming/mantine-provider/), Docs/Source, high. Counterevidence: CSS inheritance carries many visual values without component context. Unresolved: supported nested shadowing is not clearly documented. |

## 6. Provider and ambient-context audit

| Question | Finding |
|---|---|
| Values carried | Theme, color scheme and manager, CSS-variable generation, class prefix/static-class policy, nonce, environment, root element, and style deduplication. |
| Nesting and shadowing | Documentation recommends one provider near the root. React permits nesting, but a supported merge/shadow contract for nested themes was not found, so nested providers must not be assumed equivalent to scoped Citry themes. |
| Defaults and overrides | Default theme is merged with overrides; component extensions and instance props/styles form later layers. HeadlessMantineProvider deliberately changes class and variable output. |
| Reactive updates | Theme/color-scheme props and manager state rerender descendants. CSS variables do much visual propagation. Cross-tab persistence is available through the default local-storage manager. |
| Server/client agreement | Server cannot know a first-time client's system preference. `ColorSchemeScript` sets the initial attribute before hydration, while `getRootElement` must return undefined on the server. |
| Portals | Portal target and environment document matter; test environment can disable portals/transitions. React context is logical, while CSS variable availability depends on the physical target/root. |
| Lifecycle | React effects own portal, focus, and listener cleanup. No Citry fragment/morph implication can be inferred. |
| Diagnostics | `useMantineTheme` and context hooks expose ambient values. No general nested-provider or cross-root diagnostic contract was found. |

Evidence: [MantineProvider](https://mantine.dev/theming/mantine-provider/) and
[color schemes](https://mantine.dev/theming/color-schemes/), **Docs, high for
published behavior. Counterevidence:** most branding can use CSS variables and
avoid reactive JS propagation. Unresolved: nested provider, shadow DOM, iframe,
and portaled CSS-variable tests.**

This is direct evidence that Citry may need provide/inject for behavioral
ambient state, but not that theme tokens should all live in JavaScript. A
prototype should compare `$component.init()` `provide()`/`inject()` methods
with `$provide`/`$inject` magics for direction, density, portal root, generated
ID scope, and future locale selection. **Inference, high confidence.
Counterevidence:** inherited `dir` and custom properties already solve much of
the tree. Unresolved: update and diagnostic semantics.**

## 7. Accessibility and interaction quality

Mantine says components follow WAI-ARIA practices and are tested with axe,
keyboard interaction, and VoiceOver. [Accessibility statement](https://help.mantine.dev/q/are-mantine-components-accessible),
**Docs claim, high confidence as a published process, not independent
conformance. Counterevidence:** M-1 and M-2 are current source-backed gaps.
Unresolved: no public per-component assistive-technology matrix was found.**

The suite exposes visible-focus policy, VisuallyHidden, focus traps, direction,
reduced-motion hooks, and transition controls. RTL is documented, but locale
and translation concerns are not a reason to adopt its provider design now.
[RTL guide](https://mantine.dev/styles/rtl/) and
[use-reduced-motion](https://mantine.dev/hooks/use-reduced-motion/), **Docs,
high for APIs. Counterevidence:** application styles and custom render roots can
defeat these defaults. Unresolved: forced colors, 400% zoom, screen readers,
touch targets, mobile keyboards, and IME need direct quality-matrix tests.**

## 8. Forms, trust, async, and content

`@mantine/form` is an optional React state manager over native inputs. It
supports form submit/reset handling, nested/list values, validation, async
application code, errors, dirty/touched status, and adapters through
`getInputProps`. [use-form](https://mantine.dev/form/use-form/), **Docs, high.
Counterevidence:** core inputs work without the package and can submit
natively. Unresolved: browser autofill, server validation, disabled controls,
and no-JS behavior need a matrix.**

Loading, empty, and error visuals exist, but request cancellation, stale-result
rejection, retry, and remote-result trust remain application responsibilities.
Combobox and form stores do not define a transport. **Docs plus inference,
high confidence from [Combobox](https://mantine.dev/core/combobox/) and
[use-form](https://mantine.dev/form/use-form/). Counterevidence:** hooks make
those states straightforward. Unresolved: example quality for racing searches
was not audited.**

React escapes normal text. Mantine also exposes URLs, file selection,
background/image sources, JSON/text display, arbitrary component roots, and
rich-text styling helpers. No suite sanitizer or allowed-protocol policy was
found; applications own trusted HTML and URL validation. FileInput/Dropzone
select files but do not make server-side MIME, size, name, preview, and access
checks unnecessary. [FileInput](https://mantine.dev/core/file-input/) and
[Dropzone](https://mantine.dev/x/dropzone/), **Docs plus inference, medium-high.
Counterevidence:** the separation avoids pretending UI validation is security.
Unresolved: raw-HTML and URL-bearing source audit.**

## 9. Assets, CSP, SSR, performance, and upgrades

- Core CSS can be imported as one aggregate or manually as per-component files
  with dependencies. This is simple, deterministic delivery, but CSS is not
  automatically tree-shaken from the aggregate. [Styles delivery](https://mantine.dev/styles/mantine-styles/),
  **Docs, high. Counterevidence:** per-component imports are documented.
  Unresolved: measured payload.**
- Mantine does not impose a font. Icons are normally consumer-chosen; extension
  packages add their own dependencies. **Docs/inference, medium-high from the
  [core package](https://github.com/mantinedev/mantine/blob/9.4.2/packages/%40mantine/core/package.json).
  Counterevidence:** examples commonly add an icon library. Unresolved:
  aggregate example dependency weight.**
- MantineProvider accepts a CSP nonce and can deduplicate inline styles. Strict
  CSP still needs tests for dynamically positioned overlays and application
  styles. [MantineProvider](https://mantine.dev/theming/mantine-provider/),
  **Docs, high. Counterevidence:** prebuilt CSS reduces runtime injection.
  Unresolved: strict-policy reproduction.**
- SSR requires React hydration and early color-scheme agreement. It does not
  prove Citry fragment/morph compatibility. [Color schemes](https://mantine.dev/theming/color-schemes/),
  **Docs plus inference, high. Counterevidence:** ColorSchemeScript solves the
  initial visual attribute for supported cases. Unresolved: user-dependent
  branch rendering remains limited.**
- Major-version migrations can affect style imports, PostCSS, compound APIs,
  and React floors. Migration guides reduce but do not remove wrapper cost.
  **Docs, medium-high from the [9.0.0 changelog](https://mantine.dev/changelog/9-0-0/).
  Counterevidence:** coordinated monorepo versions simplify compatibility.
  Unresolved: application-scale upgrade measurements.**

## 10. Material shortcomings and complaint register

The retained patterns are de-duplicated within 2024-07-23 through 2026-07-23.

| ID | Pattern | Window evidence, workflow, response, workaround, and status | Classification |
|---|---|---|---|
| M-1 | Tooltip content is not hoverable, conflicting with dismissible/hoverable content expectations | [Issue 9072](https://github.com/mantinedev/mantine/issues/9072), opened 2026-07-20 against 9.4.1 and open at snapshot, reports that moving from target to tooltip closes it. The [9.4.2 Tooltip CSS](https://github.com/mantinedev/mantine/blob/9.4.2/packages/%40mantine/core/src/components/Tooltip/Tooltip.module.css) still sets `pointer-events: none`, and the [hover hook](https://github.com/mantinedev/mantine/blob/9.4.2/packages/%40mantine/core/src/components/Tooltip/use-tooltip.ts) does not establish a hover corridor. Workaround requires custom styling/behavior or avoiding interactive tooltip content. | Current source-confirmed limitation, grade A. Counterevidence: tooltips should not contain essential interactive content, and an associated change is in progress. Unresolved: release/fix status after 9.4.2. |
| M-2 | Built-in field errors are conditionally unmounted, weakening reliable live-region announcements | [Issue 8932](https://github.com/mantinedev/mantine/issues/8932), opened 2026-05-29 against 9.1.0 and open, reports Select validation announcement failure. [InputWrapper 9.4.2 source](https://github.com/mantinedev/mantine/blob/9.4.2/packages/%40mantine/core/src/components/Input/InputWrapper/InputWrapper.tsx) conditionally renders the error. Workaround is a separately mounted persistent live region. | Current source-confirmed limitation, grade A. Counterevidence: described-by relationships work once an error exists. Unresolved: maintainer fix plan and behavior across all input wrappers. |
| M-3 | Focus traps, portals, mobile keyboards, and scrolling interact poorly in iOS overlay collections | [Issue 8928](https://github.com/mantinedev/mantine/issues/8928), opened 2026-05-27 against 9.2.1 and open, reports modal Combobox scroll/focus failures on iOS 26.4/26.5. [Issue 8847](https://github.com/mantinedev/mantine/issues/8847), opened 2026-04-19 against 9.0.2 and closed, reports the official Spotlight/Popover demo would not scroll until focus changed. Reported workarounds include disabling focus trap, avoiding forced search focus, or `withinPortal={false}`. | Recurring user reports, grade C. Counterevidence: platform-specific and one report closed; no 9.4.2 reproduction. Unresolved: exact Safari versions and accepted fix. |
| M-4 | Server rendering cannot synchronously branch on a first-visit system color preference | [Issue 7314](https://github.com/mantinedev/mantine/issues/7314), opened 2024-12-27 against 7.15.2 and closed not planned, records hydration trouble. Current [color-scheme docs](https://mantine.dev/theming/color-schemes/) explain that the server cannot know the client preference and provide ColorSchemeScript for the root attribute. Workaround is CSS/root-attribute rendering or a client-ready branch, not server-rendering different subtrees from unknown state. | Current web-platform trade-off, grade A. Counterevidence: the documented script prevents ordinary theme flash/mismatch. Unresolved: future client hints or app cookies can change what the server knows. |
| M-5 | Aggregate CSS imports include the full selected package rather than component-level tree-shaking | [Issue 8167](https://github.com/mantinedev/mantine/issues/8167), opened 2025-08-13 against 8.1.3 and closed, reports a large aggregate file in Lighthouse. Current [styles docs](https://mantine.dev/styles/mantine-styles/) explicitly offer full or manual per-component imports and list dependency ordering. Workaround is per-component CSS imports maintained by the application. | Current documented delivery trade-off, grade A. Counterevidence: gzip and caching can make aggregate CSS acceptable, and manual imports exist. Unresolved: actual 9.4.2 sizes for Citry-like pages. |

### Complaint search log

Exact issue queries used:

- `repo:mantinedev/mantine is:issue created:>=2024-07-23 accessibility aria`
- `repo:mantinedev/mantine is:issue created:>=2024-07-23 hydration SSR MantineProvider`
- `repo:mantinedev/mantine is:issue created:>=2024-07-23 combobox keyboard`
- `repo:mantinedev/mantine is:issue created:>=2024-07-23 styles performance`
- `repo:mantinedev/mantine is:issue created:>=2024-07-23 v8 migration breaking`
- `repo:mantinedev/mantine is:issue created:>=2024-07-23 native form submit`

The retained pages were opened directly and checked for date, reported
version, status, reproduction, workaround, recurrence, and source
corroboration. No credible current broad security complaint survived the
sample. Security remains an unresolved audit area, not a demonstrated strength.

## 11. Citry conclusions

### Adopt or re-derive

- One behavior implementation with both component-level and tree-level style
  suppression.
- A broad token/theme object compiled primarily to CSS variables.
- Named Styles API parts and component extension/default mechanisms.
- Public lower-level toolkits such as Combobox beneath convenient Select,
  MultiSelect, and Autocomplete wrappers.
- Small layout primitives and application shell components alongside behavior-
  heavy controls.
- Deterministic aggregate CSS plus an automated component-chunk option, with
  measured budgets for both.

### Do not transfer directly

- React, React context, Floating UI React bindings, or hook/store APIs as a
  second runtime.
- A headless claim that only means “the default classes were switched off”
  without a stable semantic and behavior contract.
- Conditional live-region creation, context-blind portals, or focus-trap
  defaults without mobile Safari evidence.
- Manual CSS dependency ordering as the only payload optimization.
- Client form state that displaces native submit, reset, autofill, or server
  error behavior.

### Pressure on Citry's public contracts

Mantine pressures Citry to expose stable style parts, theme/default extension,
polymorphic root rules, compound subcomponents, portal targets, focus/scroll
ownership, and a documented style-free mode. Combobox-like toolkits require
stable item identity, highlighted/selected/open states, reason-bearing events,
virtualization policy, and async freshness semantics.

Ambient state should be divided deliberately: tokens, direction, and many
theme values can inherit through CSS and HTML; portal policy, generated IDs,
density behavior, and future locale resolution may require reactive
provide/inject. The `$component.init()` versus `$provide`/`$inject` prototype
must test nesting, shadowing, updates, teardown, morphing, portals, missing
providers, and server/client defaults. **Inference, high confidence from the
provider audit. Counterevidence:** a root-only provider is simpler and may be
enough for the first release. Unresolved: which scoped theme use cases are
required.**

The most important Phase 5 questions are whether Citry can expose one
implementation as truly styled and headless, how much structural CSS remains
mandatory, how aggregate assets split automatically without a Node consumer
build, and how field errors stay mounted and associated across Citry Events
and DOM morphs.
