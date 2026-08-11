# Citry UI component inventory

**Status (2026-08-09): provisional Phase 8 inventory with three completed
source-development batches plus completed responsive-layout and overlay-family
passes.**
This document orders component work while publication waits for compatible
`citry` and `citry_core` releases. It does not freeze the v1 public contract,
package compatibility range, exact class names, or release contents.

The dated ecosystem census remains in the
[Phase 5 component taxonomy](ui_research/component-taxonomy.md). The
[Citry UI plan](ui_library_plan.md) owns the current product decisions. This
inventory combines both with evidence from the thirty-four implemented production
families.

## 1. What this inventory decides

The inventory answers three questions:

1. Which ordinary application jobs still need a first-party component?
2. Which foundations must exist before those components can share a coherent
   API and visual language?
3. Which work can proceed against the current workspace while release and
   compatibility qualification wait?

A component family owns one cohesive user job, research package,
specification, public guide, structured API reference, and acceptance suite.
It may expose several cooperating classes, as Tabs does. A batch is an ordered
set of families, not permission to implement them in parallel. Each family
still follows the complete
[component-authoring workflow](../../packages/py/citry_ui/docs/component-authoring.md#requalify-one-component-family-at-a-time).

The next-batch selection began with seven planning groups. A bounded
family-boundary and dependency pass split them into independently qualified
specifications, counted every specification as one batch slot, and stopped at
seven. When two components needed different state, accessibility, composition,
or release contracts, the pass kept them separate and carried lower-priority
candidates forward instead of hiding the distinction behind one generic API.

## 2. Selection criteria

Commonality is evidence that users expect a job, not a release-order score.
The batch also considers:

- common application jobs and local production demand;
- whether the family unlocks several later components;
- reuse of the existing Field, Form, collection, context, and Dialog work;
- interaction, accessibility, asset, and maintenance cost;
- whether static families remain free of unrelated browser behavior;
- dependencies on positioning, global services, localization, file security,
  or specialist engines; and
- whether the family can be implemented and tested against the current
  workspace without claiming compatibility with an unreleased artifact.

The `x/12` signals below come from the Phase 5 normalized corpus. They measure
eligible coverage across twelve independent work units. Several census rows
combine related jobs, such as Text input/Textarea or Select/Listbox. Their
counts establish demand for the grouped job, not identical coverage for every
candidate component. Component-specific research must disaggregate that
evidence before the candidate earns a batch slot.

## 3. Current production baseline

| Family | Public boundary | Current state | Remaining release work |
|---|---|---|---|
| Button | `CButton` | Runtime, specification, structured reference, examples, and focused automation complete | Human visual, keyboard, and assistive-technology review |
| Field and Input | `CField`, `CInput` | Runtime, native form integration, controlled editing, documentation, and focused automation complete | Human visual, autofill, password-manager, mobile, and assistive-technology review |
| Form | `CForm` | Runtime, native submission/reset/validation contracts, documentation, and focused automation complete | Human visual, assistive-technology, and real-device review |
| Tabs | `CTabs`, `CTab`, `CTabPanel` | Reference family for compound declarations, browser ownership, documentation, and quality coverage | Human visual/content polish and live browser review |
| Dialog | `CDialog` | Native modal runtime, nested ownership, focus behavior, documentation, and focused automation complete | Human visual, assistive-technology, and real-device review |
| Combobox | `CCombobox` | Local/remote editable selection, request ordering, native Form and IME behavior, documentation, and focused automation complete | Human visual, keyboard, assistive-technology, and real-device review |
| Table | `CTable` and its row, column, and cell records | Native semantic Table, responsive and sticky modes, documentation, and focused cross-browser automation complete | Human visual, keyboard, assistive-technology, print, and real-device review |
| Icon | `CIcon` | Static registered catalog, accessible naming, logical RTL aliases, licensing, documentation, and focused automation complete | Human visual and assistive-technology review |
| Card | `CCard` | Optional semantic anatomy, exact part destinations, public theming, documentation, and focused automation complete | Human visual, responsive-content, and assistive-technology review |
| Textarea | `CTextarea` | Native multiline editing, Field/Form integration, controlled ownership, documentation, and focused automation complete | Human visual, mobile editing, IME, and assistive-technology review |
| Native Select | `CNativeSelect` | Native option/group semantics, Field capabilities, controlled ownership, documentation, and focused automation complete | Human visual, platform-select, mobile, and assistive-technology review |
| Checkbox | `CCheckbox` | Native checked and mixed states, Field/Form ownership, documentation, and focused family automation complete | Final cross-family qualification plus human visual and assistive-technology review |
| Alert | `CAlert` | Persistent feedback, announcement roles, registered icons, actions, documentation, and focused automation complete | Human visual, live-region, and assistive-technology review |
| Accordion | `CAccordion`, `CAccordionItem` | Single/multiple expansion, declaration ownership, keyboard/focus behavior, documentation, focused automation, and independent closure review complete | Human visual, assistive-technology, and release qualification |
| Flow layout | `CStack`, `CGroup` | Server-only one-dimensional layout, semantic roots, direction, wrapping, documentation, and focused automation complete | Human visual, responsive-layout, and host-CSS review |
| Badge | `CBadge` | Static inline status, count, metadata, icons, documentation, and focused automation complete | Human visual and assistive-technology review |
| Progress | `CProgress` | Native determinate and indeterminate task progress, documentation, and focused automation complete | Human visual, announcement-context, and assistive-technology review |
| Spinner | `CSpinner` | Compact unknown-duration activity cue, delayed composition, documentation, and focused automation complete | Human visual, motion, and assistive-technology review |
| Radio | `CRadioGroup`, `CRadio` | Native one-of-many selection, Field/Form ownership, controlled state, documentation, and focused automation complete | Human visual, keyboard, mobile, and assistive-technology review |
| Switch | `CSwitch` | Immediate native Boolean setting, Field/Form ownership, controlled state, documentation, and focused automation complete | Human visual, mobile, and assistive-technology review |
| Breadcrumbs | `CBreadcrumbs`, `CBreadcrumbItem` | Semantic hierarchical navigation, scoped rendering, overflow, documentation, and focused automation complete | Human visual, long-translation, and assistive-technology review |
| Divider | `CDivider` | Semantic/decorative separation, labelled anatomy, public theming, documentation, and focused automation complete | Human visual, RTL, forced-colors, and multi-browser review |
| Avatar | `CAvatar` | Image/fallback identity, error settlement, controlled source changes, documentation, and focused automation complete | Human visual, image-loading, and assistive-technology review |
| Skeleton | `CSkeleton` | Composable rectangle, circle, and text placeholders, reduced-motion behavior, documentation, and focused automation complete | Human visual, motion, and layout-composition review |
| Button Group | `CButtonGroup` | Named related-action grouping, attached/growing layouts, documentation, and focused automation complete | Human visual, RTL, narrow-content, and host-CSS review |
| Toggle | `CToggle`, `CToggleGroup` | Standalone and grouped pressed Buttons, controlled/uncontrolled ownership, Form-disabled precedence, documentation, and focused automation complete | Human keyboard, RTL, color-environment, and multi-browser review |
| Pagination | `CPagination` | Native URL and browser-controlled finite-page navigation, compact range generation, documentation, and focused automation complete | Human focus, RTL, responsive, and multi-browser review |
| List | `CList`, `CListItem` | Semantic static/navigation/action Lists with composable Item anatomy, documentation, and focused automation complete | Human narrow-layout, RTL, nested-content, and assistive-technology review |
| Container and Grid | `CContainer`, `CGrid`, `CGridItem` | CSS-only centered constraints, equal responsive/intrinsic Grids, asymmetric spans, public documentation, and focused automation complete | Human responsive-layout, zoom, RTL, host-CSS, and multi-browser review |
| Popover | `CPopover` | Native manual-Popover anchoring, controlled dismissal, shared layer coordination, documentation, and focused cross-browser automation complete | Human visual, touch, zoom, and assistive-technology review |
| Tooltip | `CTooltip` | Noninteractive hover/focus descriptions, shared warm-up, touch suppression, documentation, and focused cross-browser automation complete | Human visual, touch, zoom, and assistive-technology review |
| Menu | `CMenu` and its command, choice, grouping, separator, and submenu declarations | Application action/choice Menu, nested layer ownership, keyboard and focus behavior, documentation, focused cross-browser automation, and independent closure review complete | Human visual, live Safari Tab behavior, touch/pen, and assistive-technology review |
| Drawer | `CDrawer` | Native modal edge Drawer/Sheet, controlled ownership, nesting, Form-safe close paths, documentation, and focused cross-browser automation complete | Human visual, mobile viewport, touch, and assistive-technology review |
| Toast | `CToastRegion`, `CToastMessage` | Persistent declarative queue, stable live announcers, timeout/focus/modal policy, documentation, and focused cross-browser automation complete | Human visual, live-region/assistive-technology, mobile, and real-device review |

The framework foundations already proven by this baseline include explicit
library registration, atomic rollback, engine-neutral Python composition,
typed slot data, client and server context, asset ownership, live docs
previews, and structured API reference generation.

## 4. Completed source-development batch

The bounded family-boundary pass selected seven independently qualified
families. The batch deliberately mixes product foundations with
high-commonality controls. It broadens real application coverage without
beginning a positioning engine, imperative notification service, localization
system, or specialist data product.

| Order | Selected family | Public job and initial boundary | Evidence and leverage | Relative risk | Entry decision and falsifier |
|---:|---|---|---|---|---|
| 1 | Icon | Render an accessible decorative or meaningful registered icon | Icon adapter 5/12; icons recur throughout controls, feedback, navigation, and later families | High API and content-trust risk; low runtime risk | Research registered aliases, trusted source boundaries, CSP, licensing, payload ownership, RTL mirroring, missing aliases, sizing, and accessible naming. Hold bundled collections if their trust, licensing, or asset cost is not justified. `CButton` plus `CIcon` remains the icon-action composition unless it proves materially less concise or safe than a dedicated component. |
| 2 | Card | Present related content with stable title, media, body, and action anatomy | Surface/Card 9/12; establishes elevation, border, radius, padding, and background tokens used by later components | Moderate | Keep generic Surface behavior as private styling infrastructure. If research shows that Card has no stable anatomy or accessibility job beyond ordinary composition, document a recipe instead of exporting `CCard`. |
| 3 | Textarea | Enter and edit multiline plain text inside or outside Field | Text input/Textarea 12/12; reuses Field, Form, controlled editing, and native validation work | Moderate | Treat newline, wrapping, resize, scroll, morph, and browser-owned editing as first-class. Hold auto-grow until it can preserve editing, cleanup, and server replacement behavior. |
| 4 | Native Select | Choose from a finite native option list inside or outside Field | Select/Listbox 12/12; closes a common native-form gap without importing a custom collection runtime | Moderate | Use an explicit native name so a future ARIA Listbox or custom Select retains a clear boundary. Start with single selection. Multiple selection must earn its own interaction and presentation contract. |
| 5 | Checkbox | Choose an independent Boolean or set-valued option using native checkbox semantics | Checkbox/Radio/Switch 12/12; closes the highest-priority choice-control gap and exercises Field/Form boundaries | High | Qualify `CCheckbox` first. Add `CCheckboxGroup` only if it owns real group relationships or aggregate behavior; do not export an administrative wrapper. Radio and Switch keep separate future specifications because their semantics and ownership differ. |
| 6 | Alert | Present persistent informational, success, warning, or error feedback with optional title and actions | Alert 9/12 and direct local evidence that feedback was inconsistent or invisible | Moderate to high | Treat Callout as an Alert presentation recipe when it communicates feedback, not a second export. Keep visual intent separate from announcement urgency. If reliable announcements require a persistent external owner, keep `CAlert` passive and defer that announcer. Toast queues remain separate. |
| 7 | Accordion | Coordinate one or several expandable sections through `CAccordion` and declaration-only items | Disclosure 11/12 and strong local recurrence; reuses Tabs declaration, context, identity, and simplification lessons | High | `CAccordion` owns expanded identities and single or multiple coordination. `CAccordionItem` cannot work standalone or change ownership by context. Defer standalone Disclosure and use native `details` where it suffices. Reconsider only if one ownership and callback contract can serve both jobs without hidden precedence. |

Batch progress as of 2026-08-08:

- Icon completed research, specification, implementation, public examples and
  reference, focused quality evidence, wheel qualification, and independent
  closure review.
- Card completed the same pipeline, including static optional anatomy, exact
  part destinations, non-clipping overlay boundaries, one-child row geometry,
  media-only corner handling, public theming, and independent closure review.
- Textarea completed the same pipeline, including native multiline editing,
  controlled and uncontrolled browser ownership, Field/Form integration, safe
  RCDATA handling, eleven public examples, scaling and quality coverage, exact
  wheel qualification, and independent closure review.
- Native Select completed the same pipeline, including native option/group
  semantics, placeholder-required conformance, controlled and uncontrolled
  selection, reactive Field capabilities, exact value/morph ownership, ten
  public examples, quality and wheel coverage, and independent closure review.
- Checkbox completed its production runtime, public documentation, focused
  family evidence, quality scenario, and wheel wiring. Final cross-family
  qualification remains pending.
- Alert completed the full pipeline, including announcement semantics, a
  single allowlisted icon path, actions, ten public previews, quality and wheel
  evidence, and independent closure review.
- Accordion completed the full pipeline, including direct declaration
  ownership, controlled and uncontrolled expansion, keyboard and focus
  recovery, nested groups, ten public previews, reusable quality evidence, and
  independent closure review.

### 4.1 Boundary decisions carried forward

The pass deliberately did not spend batch slots on these adjacent jobs:

- **IconButton:** `CButton` already supports icon-only composition and naming.
  Add a dedicated family only if Icon research proves that composition too
  verbose, unsafe, or inconsistent.
- **Surface:** keep the shared visual recipe private unless applications need a
  stable component job that Card cannot satisfy.
- **Layout:** carry Flow (`CStack`/`CGroup`) first, then Container and Grid.
  This batch used its seven slots for more immediate foundation, form, choice,
  feedback, and interaction jobs. Named responsive Grid inputs additionally
  wait for a public breakpoint or container-query vocabulary.
- **Radio and Switch:** retain separate future specifications. Do not hide
  Checkbox, Radio, and Switch behind a generic Choice contract.
- **Standalone Disclosure:** retain a separate later specification. Accordion
  owns group coordination; native `details` remains the current standalone
  alternative.
- **Callout:** present it as an Alert recipe when it communicates persistent
  feedback, or compose Card and ordinary content for editorial emphasis.

These are batch decisions, not permanent v1 exclusions. Component-specific
research may still falsify one selected boundary. When that happens, record
the reason and use the substitute queue rather than silently expanding the
batch.

### 4.2 Batch execution order

Then, for each selected family:

1. audit the current workspace and refresh component-specific sources;
2. decide the family boundary and public jobs;
3. complete the specification and public example catalog;
4. review the design package before runtime work;
5. implement runtime, tests, quality scenarios, docs, and structured API data;
6. simplify the public anatomy; and
7. update this inventory before starting the next family.

The batch may use unreleased workspace behavior during development. Before a
Citry UI release, record the first released `citry` and `citry_core` versions
that supply every used contract, update package metadata, and run the released
artifact compatibility matrix. No workspace-only result counts as published
compatibility evidence.

### 4.3 Substitutes

Progress and Spinner are the first substitute if a selected family exposes a
new core dependency or grows beyond the batch budget. They have 11/12 corpus
coverage, immediate pending-state value, and no need for a global service.
Skeleton and EmptyState remain distinct presentation jobs and should not gain
live-region behavior merely because they appear near loading states.

Badge/Tag, Breadcrumbs, and semantic List are the next low-risk substitutes.

## 5. Selected second source-development batch

The second batch broadens everyday layout, feedback, form, and navigation
coverage without requiring positioning, portals, localization, or a global
service. Its seven slots are independently specified even where two families
share visual tokens or native form lessons.

| Order | Selected family | Initial public boundary | Main reason to advance |
|---:|---|---|---|
| 1 | Flow layout | `CStack` and `CGroup` for one-dimensional vertical and horizontal layout | Establish the spacing and alignment vocabulary used by later families while remaining server-only. |
| 2 | Badge | `CBadge` for static status, count, and metadata presentation | Add a common low-cost data-display primitive without absorbing interactive Tag or Chip behavior. |
| 3 | Progress | `CProgress` for determinate and indeterminate task progress | Cover native progress semantics, async status, and public value styling. |
| 4 | Spinner | `CSpinner` for unknown-duration activity feedback | Provide a compact activity cue with a contract distinct from measurable Progress. |
| 5 | Radio | `CRadioGroup` and `CRadio` for one choice from a finite set | Complete the primary native choice-control set using the established Field/Form capability model. |
| 6 | Switch | `CSwitch` for an immediate Boolean setting | Preserve Switch semantics and feedback instead of treating it as a visual Checkbox alias. |
| 7 | Breadcrumbs | `CBreadcrumbs` for semantic hierarchical navigation | Add a high-commonality navigation family without requiring popup or route-provider infrastructure. |

The second batch is complete. Flow retains separate concise Stack and Group
surfaces; Badge stays an inline, text-bearing static label
without absorbing Chip/Tag or overlay behavior; Progress preserves native
determinate and indeterminate task semantics; Spinner stays a compact,
unknown-duration cue without absorbing task timing or overlay ownership. Radio
keeps native one-of-many selection under one Group owner; Switch keeps immediate
on/off settings distinct from Checkbox selection; Breadcrumbs stays semantic,
server-owned navigation without premature router or disclosure ownership.
Responsive Grid and Container remained separate during this batch; the later
unblocking pass has now ratified their public responsive vocabulary.

DescriptionList and Statistic are the first general substitutes. EmptyState
and FormSummary stay at the end of the backlog because current components can
compose their jobs. The shared overlay gate recorded below is cleared.
Popover, Tooltip, Menu, Drawer/Sheet, and Toast have completed their family
specifications, runtime, public documentation, focused automation, and
repository qualification.

## 6. Completed third source-development batch

The third batch adds reusable action, feedback, navigation, media, and
semantic-content surfaces without beginning overlay positioning,
localization-sensitive controls, or a responsive layout vocabulary. As with
the earlier batches, every row is one independently qualified family.

| Order | Selected family | Initial public boundary | Main reason to advance |
|---:|---|---|---|
| 1 | Divider | `CDivider` for semantic or decorative separation | Establish a concise native separation primitive with horizontal and vertical presentation before later dense layouts. |
| 2 | Avatar | `CAvatar` for images, initials, and icon fallbacks | Add a common identity surface while proving image failure, fallback, naming, and layout-stability contracts. |
| 3 | Skeleton | `CSkeleton` primitives and common presets composed through Flow | Match mature-suite placeholder flexibility without adopting a string mini-language or component-owned announcements. |
| 4 | ButtonGroup | `CButtonGroup` for related momentary `CButton` commands | Decide whether connected styling, shared sizing, naming, and direct-child validation add durable value beyond `CGroup`; otherwise keep it as a recipe and use the substitute queue. |
| 5 | Toggle | `CToggle` and `CToggleGroup` for persistent pressed state | Keep pressed buttons distinct from immediate Switch settings, ordinary Button commands, and radio-backed segmented selection. |
| 6 | Pagination | `CPagination` for finite page navigation through links or controlled requests | Add a common dynamic navigation collection with exact current-page, ellipsis, responsive, URL, and callback ownership. |
| 7 | List | `CList` with the smallest justified semantic item surface | Add reusable native list presentation without importing Menu, Listbox, Tree, or selection behavior into a static collection. |

`CEmptyState` and `CFormSummary` move to the end of the general backlog. Their
current jobs can be reconstructed from existing Flow, Icon, Button, Alert,
Field, and ordinary semantic content. They should advance only when repeated
application code proves a stable component contract that composition does not
serve clearly.

After this batch, explicitly revisit three blocked groups:

1. Grid and Container, including the minimal public responsive vocabulary;
2. Menu, Tooltip, Popover, Drawer, and Toast, including the shared overlay,
   portal, positioning, focus, dismissal, presence, and queue foundations; and
3. Number, date, time, and advanced range controls, including localization,
   parsing, formatting, stepping, pointer, touch, and server/browser agreement.

This revisit is a dependency and unblocking decision, not automatic approval
to implement every listed family in the next batch.

The batch completed the full source-development pipeline for all seven rows:
runtime and exports, component-owned research/specifications, conceptual
guides, structured API references, live examples, focused server and Chromium
tests, reusable quality and scaling scenarios, docs-site projection, and exact
wheel qualification. Remaining work is human visual and assistive-technology
review, multi-browser qualification, independent implementation review where
available, and the released-artifact compatibility matrix.

### 6.1 Responsive-layout unblocking pass

The first deferred-group review studied current Vuetify, Bootstrap, Ionic,
Mantine, Chakra, Material UI, Tailwind, Quasar, Radix, GOV.UK, Lightning,
Carbon, Bulma, and native CSS Grid patterns. It rejected nested responsive
objects, quoted mini-languages, and a Citry-owned utility framework because
all three make the common template path longer or expand beyond component
scope.

The completed family exports `CContainer`, `CGrid`, and `CGridItem`:

- `CContainer` owns a centered maximum inline size, logical gutters, and
  `fluid` mode; it deliberately does not establish CSS query containment;
- `CGrid` uses flat `sm`, `md`, `lg`, `xl`, and `xxl` equal-column inputs,
  fixed `cols`, or exclusive intrinsic `min_col` auto-fit sizing;
- `CGridItem` adds the same flat responsive vocabulary only for asymmetric
  1-through-12 spans; and
- bespoke thresholds, query containers, alignment, placement, and utility
  breadth remain ordinary consumer CSS or Tailwind through `class_`/`style`.

The family completed its specification, runtime/export pass, structured API,
eight live examples, focused server/Chromium evidence, reusable quality and
scaling routes, docs projection, and exact wheel allowlist. Human visual,
assistive-technology, multi-browser, independent implementation, and
released-artifact review remain.

The overlay-family ecosystem review is now recorded in
[`ui_overlay_foundations.md`](ui_overlay_foundations.md). It narrows the old
single "overlay foundation" label into anchored positioning, dismissible-layer
ordering, focus/modality, presence, physical context, and a separate Toast
host. The three-engine
[`prototype report`](ui_overlay_foundations_spikes/prototype-report.md)
ratifies a platform-first hybrid: native manual Popover and CSS anchors, a
small private controlled-dismissal/presence controller, no default teleport,
native Dialog for modal Drawer, and a separate persistent Toast host. The
shared blocker is cleared for one-family-at-a-time specification beginning
with Popover. Popover has now completed its specification, runtime/export,
structured reference, nine public previews, focused server and three-engine
browser evidence, reusable quality/scaling wiring, docs projection, and exact
wheel pass. Independent implementation review and human release evidence
remain. Tooltip has now completed the same pipeline with its noninteractive
description boundary, shared hover warm-up, focus/hover parity, touch
suppression, native anchored surface, ten public previews, and three-engine
focused evidence. Menu has completed its eight-class command/choice/submenu
family, thirteen public previews, three-engine focused evidence, real
correlated-rerender coverage, docs/quality/scaling wiring, exact wheel pass,
and independent implementation review. Modal Drawer/Sheet has now completed
its native-Dialog implementation, ten public previews, and focused
three-engine evidence. Toast has completed its persistent declarative queue,
stable announcers, timer/focus/modal behavior, ten public previews, and
focused three-engine evidence. Human visual, assistive-technology, real-device,
and released-artifact review remain. Localization-sensitive
numeric/date/time/range controls remain gated on the foundation proposal in
[`i18n.md`](i18n.md).

### 6.2 Substitutes

ButtonGroup and semantic List both earned exports by adding durable named-group,
joined-action, semantic-surface, and composable-item contracts beyond Flow or
raw markup. `CVisuallyHidden` should advance only when research proves a public
component job; otherwise `CDescriptionList` and `CStatistic` remain the first
substitutes after the blocked-group review.

### 6.3 Approved non-localized interaction batch

The 2026-08-11 follow-up keeps locale-sensitive number, date, time, Rating,
PinInput, Slider, and Range work behind the `i18n.md` gate. It instead advances
seven families whose values and behavior do not require localized parsing or
formatting. Each family still completes the full research, design,
implementation, documentation, evidence, and review pipeline before runtime
work starts on the next family.

| Order | Selected family | Initial public boundary | Main reason to advance |
|---:|---|---|---|
| 1 | Disclosure | One independently controlled heading and panel, without Accordion collection ownership | Give isolated reveal/hide jobs a concise contract rather than asking callers to configure a one-item Accordion. |
| 2 | SplitButton | One primary Button joined to a separate Menu trigger | Reuse the completed Button, ButtonGroup, and Menu foundations for a common action pattern without inventing another menu model. |
| 3 | TagsInput | Free-form string tokens inside a Field-compatible control | Add token creation, paste, removal, duplicate, reset, and native repeated-value behavior that MultiSelect does not own. |
| 4 | ScrollArea | Native scrolling with a styled viewport and scrollbar affordances | Preserve browser scrolling while providing a durable cross-browser visual and RTL surface for dense collections. |
| 5 | ContextMenu | Contextual activation and point anchoring over the existing Menu declaration family | Add right-click, keyboard context-menu, and bounded long-press entry without duplicating Menu items or selection semantics. |
| 6 | Image | Native responsive image loading with stable geometry and fallback settlement | Generalize the proven Avatar image lifecycle into a common media surface without importing an image-processing engine. |
| 7 | CommandPalette | Dialog-hosted searchable command collection with grouped actions | Integrate the completed Dialog and collection foundations while leaving application shortcuts and domain command registration with the owner. |

`CLoadingOverlay` remains deferred. It should advance only if research proves
that busy semantics, interaction blocking, and focus recovery add a durable
contract beyond Spinner plus ordinary composition.

If localization-sensitive controls remain blocked after this batch, the next
review group is DataGrid, virtualized collections, Tour, and
Transfer/PickList. That is a research and boundary pass, not automatic approval
to place all four specialist systems in the core package.

## 7. Remaining core candidates

These families remain likely parts of a broad first-party suite. Their order
depends on lessons from the completed batch and final Phase 8 scope.

| Area | Families or foundations | Evidence signal | Dependency or open decision |
|---|---|---:|---|
| Foundations | Reset and cascade layers; typography and native content styles; global semantic tokens, component defaults, density, motion, and responsive vocabulary | Theme/tokens 9/12; typography/native content 6/12 | Card and the existing production families supply the current surface, elevation, shape, spacing, and responsive evidence. Global aliases and reset/layer policy remain foundation work unless an application/component earns a public job. |
| Actions | SplitButton | Group/toggle 10/12 | ButtonGroup and Toggle are selected for batch three. SplitButton depends on Menu. |
| Forms | NumberInput, Slider/Range, Rating, PinInput | NumberInput 10/12; Slider/Rating 11/12 | Numeric and pointer controls need parsing, stepping, locale boundaries, keyboard, touch, and controlled-state research. |
| Navigation | NavList/NavLink, Menu, application navigation | Menu 11/12; app navigation 7/12 | Pagination and Menu are implemented. Route awareness stays with applications or host integrations. |
| Feedback | interactive Tag/Chip, Toast/Notification | Badge 9/12; Toast 10/12 | Skeleton and Toast are implemented. Interactive or removable Chips need their own behavior contract. |
| Overlays | AlertDialog, Drawer/Sheet, Popover, Tooltip, Menu popup, HoverCard | 10 to 11/12 for the main families | The platform-first private foundation plus Popover, Tooltip, Menu, and modal Drawer/Sheet passes are complete. AlertDialog and HoverCard remain separate jobs; persistent navigation remains a layout job. |
| Layout and shell | AppShell, Header/AppBar, Main, Footer, Sidebar, responsive navigation | 7/12 plus strong local application demand | Build on the selected layout vocabulary. Responsive navigation may also depend on Drawer. |
| Overflow and resizing | ScrollArea, Splitter, and overflow helpers | Grouped row 10/12 | Native overflow remains the baseline. Advance a component only for a concrete focus, scrollbar, resize, persistence, or responsive job that CSS does not solve clearly. |
| Data display | DescriptionList/DataList, Timeline, Statistic | Avatar/List 9/12; Timeline/Statistic 6/12 | Avatar and semantic List are selected for batch three. Establish collection identity only where items are stateful. |
| Collections | MultiSelect/TagsInput, richer Combobox presentations, Tree, Carousel | MultiSelect inherits 9/12 Combobox evidence; Tree 8/12; Carousel 7/12 | Rich option content, multiple native form values, selection identity, drag, virtualization, and async ownership require separate proofs. |
| Utilities | VisuallyHidden, focus-visible policy, focus scope/restoration, portal, presence, dismissal, responsive visibility | 7 to 8/12 | Prefer internal foundations until user-authored composition demonstrates a stable public job. |

## 8. Gated and companion work

| Work | Stage | Gate or boundary |
|---|---|---|
| Date, time, calendar, date range, and locale-sensitive number controls | Later general-suite work | [`i18n.md`](i18n.md) must ratify parsing, formatting, time zones, locale resolution, direction, and server/browser agreement. |
| FileInput and DropTarget | Later | Native file selection may advance after focused research. Upload transport, storage, previews, cancellation, retry, and server validation form a larger security and lifecycle product. |
| Sortable and editable collections, virtual windows, and infinite loading | Later | Identity, focus, drag, async, and server replacement behavior need a dedicated collection contract. |
| Stateful DataTable or DataGrid | Companion candidate | Spreadsheet navigation, column models, editing, grouping, aggregation, pinning, virtualization, export, and server query protocols exceed semantic Table. |
| Charts, rich-text editing, maps, schedulers, diagramming, and media editors | Companion packages | Each adds a specialist engine, payload, security model, accessibility contract, or domain model. |
| Headless component APIs | Follow-up research | Real applications and a broader styled catalog must first reveal the authoring jobs, API shape, and representative performance cases. |
| Storybook | Optional extension | The docs live-component host remains the first-party preview surface. Storybook does not gate component work or publication. |
| EmptyState and FormSummary | End of general backlog | Existing components and semantic markup reconstruct both jobs. Advance only when repeated application composition proves a missing durable contract. |

## 9. Inventory maintenance

Update this document when a family enters design, its boundary changes, its
specification uncovers a new prerequisite, or implementation changes a shared
foundation. Record public release commitments only in the final Phase 8
decision record.

The next-batch selection must change when any of these conditions appears:

- a family needs an unreleased core capability beyond the already accepted
  workspace contract;
- one planning group expands into several high-risk families and exceeds the
  batch budget;
- a static family activates unrelated JavaScript or cannot meet the asset
  budget;
- Field, Form, context, or lifecycle behavior cannot express the required
  native contract;
- two brand adaptations require private selectors or undocumented tokens; or
- focused research shows that a proposed component adds no durable value over
  native HTML, CSS, or composition.
