# Component taxonomy and staged breadth

**Snapshot:** 2026-07-23. **Status:** complete; independent synthesis gate
passed 2026-07-23. This report turns the approved Phase 4 corpus into a
normalized catalog and prototype-selection rubric. It does not choose a
Python API, provider syntax, visual language, or implementation architecture.

The controlling product constraints remain the
[product charter](product-charter.md): `citry-ui` is a separate distribution
installed directly with `uv add citry-ui`; it provides a useful styled default
and a supported headless counterpart over shared behavior; it is server-first,
uses Citry's client runtime, and requires no consumer Node build, CDN, or
network download. Localization remains follow-up work.

## 1. Method and evidence boundary

### 1.1 Evidence units

The heatmap has twelve columns because the
[approved corpus](candidate-map.md#2-proposed-phase-4-corpus) has twelve
de-duplicated work units, not because it contains only twelve named products.
Related products that expose the same behavior or complaint ancestry receive
one weight:

| Key | Work unit | Primary role |
|---|---|---|
| VU | [Vuetify 4 and Vuetify v0](recon-vuetify.md) | Broad installed styled suite plus a newer unstyled foundation |
| PV | [PrimeVue](recon-primevue.md) | Broad styled suite with an unstyled switch and named parts |
| RN | [Reka UI and Nuxt UI](recon-reka-nuxt.md) | Installed headless foundation plus installed styled suite and recipes |
| AD | [Ant Design](recon-ant-design.md) | Broad installed styled enterprise suite |
| MN | [Mantine](recon-mantine.md) | Broad styled suite with supported style suppression |
| CZ | [Chakra UI, Ark UI, and Zag](recon-chakra-ark-zag.md) | Styled recipes over a separate headless and behavior stack |
| RA | [React Aria Components](recon-react-aria.md) | Installed headless behavior and collection suite |
| BSR | [Base UI, shadcn/ui, and Radix lineage](recon-base-shadcn.md) | Installed headless behavior plus source-owned styled recipes |
| BS | [Bootstrap](recon-bootstrap.md) | CSS-first structural components plus optional plugins |
| WA | [Web Awesome](recon-web-awesome.md) | Styled custom elements with Shadow DOM |
| PCP | [Python component packaging](recon-python-component-packaging.md) | Cotton UI styled catalog plus Python publishing foundations |
| DF | [django-formset](recon-django-formset.md) | Server-rendered form specialist with a custom-element runtime |

The [local prior-art study](local-prior-art.md#4-production-application-evidence)
is a demand and acceptance source, not a thirteenth ecosystem vote. Its high
use of actions, forms, overlays, navigation, tables, remote selection, and
editable collections influences staging after the ecosystem commonality pass.

### 1.2 Normalization rules

The following rules prevent catalog inflation:

1. A family is counted by its user job, not its upstream product name. Modal
   and Dialog normalize to Dialog; Snackbar and Notification normalize to
   Toast/Notification; Expansion Panel normalizes to Disclosure/Accordion.
2. Root, Trigger, Content, Item, Portal, Label, and similar compound parts do
   not become extra families.
3. A styled wrapper and the behavior it inherits remain one work-unit signal.
   Reka plus Nuxt, Ark/Zag plus Chakra, and Base/Radix/React Aria bases plus
   shadcn therefore do not multiply evidence.
4. A simple semantic Table is separate from a stateful Data Table or domain-
   heavy grid. A styled native input is separate from a searchable Combobox.
5. Installed core, style-suppressed mode, source recipe, structural CSS, and
   specialist companion coverage remain visibly different.
6. Planned, paid-only, or separately packaged specialist products do not count
   as ordinary core breadth.
7. Catalog presence says nothing by itself about quality, accessibility,
   maintenance, payload, or suitability for Citry.
8. Grades A through C in the
   [complaint register](complaint-register.md) may support risks. Grade D is a
   test lead only and cannot establish a conclusion or change a risk band.

### 1.3 Heatmap legend

| Mark | Meaning |
|---|---|
| **S** | First-party styled family in the ordinary general product |
| **H** | Supported headless behavior or explicit unstyled part contract |
| **U** | Style-suppressed mode over library-owned markup; not scored as an independent headless surface |
| **C** | CSS-first, structural, native, or server-rendered presentation without a general owned behavior engine |
| **R** | Styled recipe or application composition whose behavior is inherited from another package or local source |
| **P** | Specialist, paid, optional-extension, or adjacent-package coverage |
| **·** | No documented family in the reviewed surface |

Combined marks describe one work unit, not multiple votes. `S/H` means that
the unit contains both styled and headless evidence; it does not assert mature
one-to-one parity. `S/U` keeps Mantine and PrimeVue's supported unstyled modes
distinct from Ark, Reka, Base UI, React Aria, and Vuetify v0 headless behavior.

The `Eligible` column is reproducible from the cells. A work unit contributes
exactly one eligible coverage unit when its cell contains `S`, `H`, `U`, or
`C`, including in a combined mark. A bare `R`, bare `P`, or `·` contributes
zero. Recipes remain useful evidence that users expect a job, but they do not
show that the reviewed product owns a general family. Specialist or paid
coverage likewise does not inflate general-suite commonality.

## 2. Normalized component-inventory heatmap

### 2.1 Foundations, layout, and actions

| Normalized family | Eligible | VU | PV | RN | AD | MN | CZ | RA | BSR | BS | WA | PCP | DF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Theme and semantic tokens | 9 | S/H | S/U | S | S | S/U | S | · | R | C | S | S | · |
| Typography and native content styles | 6 | S | · | · | S | S/U | S | · | R | C | C | · | · |
| Icon component or adapter | 5 | S | P | S | S | · | S | · | · | · | S/P | · | · |
| Container and responsive grid | 7 | S | S/U | S/R | S | S/U | S | · | · | C | · | · | · |
| Stack, inline/group, and flex layout | 5 | S | · | R | S | S/U | S | · | · | C | · | · | · |
| Surface, sheet, paper, or card | 9 | S | S/U | S | S | S/U | S | · | R | C | S | S | · |
| Divider, separator, and aspect ratio | 10 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | · | · |
| Application shell and navigation layout | 7 | S | S/U | S/R | S | S/U | · | · | R | C | P | S | · |
| Button and icon button | 11 | S/H | S/U | S | S | S/U | S | H | H/R | C | S | S | P |
| Button group, toggle, or segmented control | 10 | S/H | S/U | H | S | S/U | S/H | H | H/R | C | S | · | · |

The strongest universal signal is not a particular design language. It is the
combination of semantic tokens, a small layout vocabulary, surfaces, and
action primitives. React Aria's intentional absence of this layer is useful
counterevidence: excellent behavior alone does not satisfy Citry's styled
default goal. See [RA-1](complaint-register.md#retained-patterns).

### 2.2 Forms and selection

| Normalized family | Eligible | VU | PV | RN | AD | MN | CZ | RA | BSR | BS | WA | PCP | DF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Field, label, description, and error | 11 | S/H | S/U | S | S | S/U | S/H | H | H/R | C | S | S | P |
| Text input and textarea | 12 | S/H | S/U | S | S | S/U | S | H | H/R | C | S | S | C/P |
| Checkbox, radio group, and switch | 12 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | S | C/P |
| Native Select or Listbox | 12 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | S | C/P |
| Combobox or Autocomplete | 9 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | · | P | S | P |
| Number input | 10 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | · | P |
| Slider, range, or rating | 11 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | S | · |
| File selection or drop target | 8 | S | S/U | S | S | S/U/P | S/H | H | R | C | P | · | P |
| Calendar, date, or time control | 8 | S | S/U | S/H | S | P | S/H | H | R | · | S/P | S | P |
| Form state, validation, and summary | 10 | S/H | S/U | S | S | P | S/H | H | H/R | C | S | C | P |
| Repeatable or nested form collection | 1 | · | · | · | S | P | · | · | · | · | · | · | P |

Core field anatomy and ordinary native controls are close to universal. The
apparent depth after that point needs qualification. Date controls frequently
bring locale and date-model dependencies; file controls do not supply a secure
upload lifecycle; recipe form stores may weaken native submission; and
django-formset's nested collections are a specialist controller rather than a
general UI primitive. These distinctions are documented in
[React Aria](recon-react-aria.md#7-forms-trust-assets-and-runtime),
[Chakra/Ark/Zag](recon-chakra-ark-zag.md#8-accessibility-forms-trust-and-async-behavior),
and [django-formset](recon-django-formset.md#6-forms-validation-submission-and-async-state).

### 2.3 Navigation, feedback, and overlays

| Normalized family | Eligible | VU | PV | RN | AD | MN | CZ | RA | BSR | BS | WA | PCP | DF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Breadcrumbs | 10 | S/H | S/U | S | S | S/U | S | H | R | C | S | S | · |
| Tabs | 11 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | S | · |
| Pagination | 8 | S/H | S/U | S/H | S | S/U | S/H | · | R | C | · | S | · |
| Menu, dropdown, or navigation menu | 11 | S | S/U | S/H | S | S/U | S/H | H | H/R | C | S | S | · |
| Sidebar, app bar, or navbar | 7 | S | S/U | S/R | S | S/U | · | · | R | C | P | S | · |
| Alert, callout, or inline message | 9 | S | S/U | S | S | S/U | S | · | R | C | S | S | P |
| Badge, tag, or chip | 9 | S | S/U | S | S | S/U | S | · | R | C | S | S | · |
| Progress, meter, or spinner | 11 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | S | P |
| Skeleton and empty state | 8 | S | S/U | S | S | S/U | S | · | R | C | S | · | · |
| Toast, snackbar, or notification | 10 | S/H | S/U | S/H | S | S/P | S/H | H | H/R | C | P | S | · |
| Dialog and AlertDialog | 11 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | S | P |
| Drawer, sheet, or offcanvas | 10 | S | S/U | S/H | S | S/U | S/H | · | H/R | C | S | S | · |
| Popover and Tooltip | 11 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | S | · |

These rows explain why overlays cannot be treated as optional polish. Dialog,
menu, popover, and tooltip are common, while the complaint evidence repeatedly
finds focus, portal, inertness, Escape, mobile keyboard, provider, and cleanup
problems. The conclusion rests on grades A through C across
[React Aria](recon-react-aria.md#8-material-shortcomings-and-complaint-evidence),
[Base/Radix/shadcn](recon-base-shadcn.md#9-material-shortcomings-and-complaint-evidence),
[Reka/Nuxt](recon-reka-nuxt.md#9-complaint-register),
[Ant Design](recon-ant-design.md#10-material-shortcomings-and-complaint-register),
and [Mantine](recon-mantine.md#10-material-shortcomings-and-complaint-register).

### 2.4 Data display, collections, and utilities

| Normalized family | Eligible | VU | PV | RN | AD | MN | CZ | RA | BSR | BS | WA | PCP | DF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Avatar | 9 | S/H | S/U | S/H | S | S/U | S/H | · | H/R | · | S | S | · |
| List or selectable list | 9 | S/H | S/U | S/H | S | S/U | S/H | H | R | C | · | S | · |
| Semantic Table | 6 | S | · | · | · | S/U | S | · | R | C | C | S | · |
| Stateful Data Table or grid | 5 | S | S/U | S/R | S | · | · | H | R | · | · | · | · |
| Tree or tree view | 8 | S/H | S/U | S/H | S | S/U | S/H | H | · | · | S | · | · |
| Disclosure or Accordion | 11 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | S | · |
| Carousel | 7 | S/H | S/U | S/R | S | P | S/H | · | R | C | S | · | · |
| Timeline, statistic, or key/value display | 6 | S | S/U | S | S | S/U | S | · | · | · | · | · | · |
| Portal, presence, focus, and dismissal | 8 | S/H | S/U | S/H | · | S/U | S/H | H | H | · | S | · | · |
| Scroll area, splitter, or overflow helper | 10 | S/H | S/U | S/H | S | S/U | S/H | H | H/R | C | S | · | · |
| Visually hidden and focus-visible utilities | 7 | S | · | H | · | S/U | S | H | · | C | C | · | · |
| Provider or ambient-context mechanism | 11 | S/H | S/U | S/H | S | S/U | S/H | H | H | C | C | C | P |
| Presence, transition, or motion helper | 7 | S/H | S/U | H | · | S/U | S/H | · | · | C | S | · | · |

The provider row accepts an owned provider or an ambient propagation
mechanism. Bootstrap's `C` is subtree-scoped color mode and inherited CSS, not
a component provider; Web Awesome's `C` is CSS plus document/component
attributes; PCP's `C` is server render-scoped context/provide-inject. These
signals establish the job without claiming equivalent client behavior.

Semantic Table and stateful Data Table are deliberately separate censuses.
PrimeVue, Nuxt UI, Ant Design, and React Aria expose only a rich or interactive
Table family, so their cells appear only in the Data Table row. Vuetify has
distinct `VTable` and `VDataTable` families and therefore appears in both.
Mantine, Chakra, Bootstrap, Web Awesome native styles, and Cotton UI cover only
the semantic row. Base/shadcn documents a styled source Table component and a
richer Data Table recipe; both are marked bare `R` because the consumer owns
the copied source, so neither counts as installed product-owned coverage. The
rich products combine different sets of
sorting, filtering, selection, editing, grouping, pagination, virtualization,
server loading, and export. PrimeVue's grouping/virtualization lineage and
React Aria's keyboard drag report show that “DataTable” is not one stable
cross-library unit. See [PV-4 and RA-4](complaint-register.md#retained-patterns).
Citry should keep semantic Table in the general suite and resist using a domain
grid's breadth to inflate core coverage.

## 3. Commonality tiers

The tiers are a mechanical grouping of the `Eligible` column. They describe
owned product-job commonality, not quality, Citry priority, or release order.
Every heatmap family appears exactly once below. Bare `R` remains expectation
evidence and bare `P` remains boundary evidence, but neither raises the count.

| Tier | Eligible threshold | Complete family set | Interpretation |
|---|---|---|---|
| 1. Suite baseline | 9 to 12 of 12 | Theme/tokens (9/12); surface/card (9/12); divider/aspect (10/12); Button (11/12); button group/toggle (10/12); Field (11/12); text input (12/12); checkbox/radio/switch (12/12); Select/Listbox (12/12); Combobox (9/12); NumberInput (10/12); slider/rating (11/12); form state (10/12); Breadcrumbs (10/12); Tabs (11/12); Menu (11/12); Alert (9/12); Badge (9/12); progress (11/12); Toast (10/12); Dialog (11/12); Drawer (10/12); Popover/Tooltip (11/12); Avatar (9/12); List (9/12); disclosure (11/12); scroll/split/overflow (10/12); provider/ambient mechanism (11/12) | A styled full suite usually feels incomplete without these jobs. Commonality does not make their behavior easy. |
| 2. Broad-suite expectation | 6 to 8 of 12 | Typography/native content styles (6/12); container/grid (7/12); application shell (7/12); file selection (8/12); date/time (8/12); Pagination (8/12); app navigation (7/12); skeleton/empty state (8/12); semantic Table (6/12); Tree (8/12); Carousel (7/12); timeline/statistic (6/12); portal/focus/dismissal (8/12); visually hidden/focus-visible (7/12); presence/motion (7/12) | Common in mature broad suites, but dependencies, semantic depth, or server-first constraints vary. |
| 3. Differentiator | 3 to 5 of 12 | Icon component/adapter (5/12); stack/flex layout (5/12); stateful Data Table/grid (5/12) | The reviewed products often leave these to framework conventions, recipes, or separate engines. |
| 4. Sparse or specialist | 0 to 2 of 12 | Repeatable/nested form collection (1/12) | Ordinary suite ownership is sparse. `P` evidence can still show important specialist demand. |

### 3.1 Commonality is not release staging

Risk, local production demand, product coherence, and prerequisite order may
stage a family differently without changing its tier:

| Family or foundation | Commonality | Citry staging consequence |
|---|---|---|
| Icon adapter | Tier 3, 5/12 | Version 1 foundation because a coherent styled default and local asset policy need it, not because the census says it is universal. |
| Application shell | Tier 2, 7/12 | Version 1 because it is static/server-friendly and local applications repeatedly need it. |
| Semantic Table | Tier 2, 6/12 | Version 1 because native structure and local CRUD demand make it high value without promising a grid engine. |
| Combobox | Tier 1, 9/12 | Version 1 target, but Critical-risk prototype and acceptance gates apply. Risk does not demote its commonality. |
| NumberInput and slider/rating | Tier 1, 10/12 and 11/12 | Near-term because parsing, formatting, pointer, and keyboard scope require more work. This scope decision does not demote commonality. |
| Date/time | Tier 2, 8/12 | Later, after localization work defines parsing, formatting, time zones, and server/client agreement. |
| Stateful Data Table/grid | Tier 3, 5/12 | Later or companion work because the products disagree on grid ownership and breadth. |
| Provider/ambient mechanism | Tier 1, 11/12 | A Version 1 release prerequisite rather than a visible breadth claim. It must pass nested, reactive, portal, environment, and teardown tests first. |
| Toast, Dialog, Drawer, and Popover | Tier 1, 10/12, 11/12, 10/12, and 11/12 | Version 1 targets gated on provider/environment, portal, publishing, lifecycle, focus, and dismissal foundations. |
| Repeatable form workflow | Tier 4, 1/12 | Kept in the exact prototype because local evidence makes it a high-risk integration probe. The probe does not imply a Version 1 general family. |

Specialist domains outside the heatmap, including charts, rich-text editing,
maps, advanced schedulers, and media editors, are not assigned invented
commonality scores. Their companion boundary follows dependency, security,
payload, and maintenance evidence in section 5.4.

## 4. Proposed Citry taxonomy

This taxonomy is about ownership and documentation. It does not prescribe
class names, exports, inheritance, or whether paired surfaces use separate
classes, modes, or generated layers.

### 4.1 Foundations

- reset, cascade-layer, specificity, and application-CSS policy;
- primitive and semantic color tokens;
- typography, spacing, radius, elevation, motion, density, and breakpoints;
- light, dark, brand, forced-colors, reduced-motion, LTR, and RTL behavior;
- icon aliases and rendering policy;
- provider/default context, generated IDs, portal roots, and environment;
- state vocabulary shared by styled and headless components.

Foundations are shipped product surface, not implementation miscellany. The
old Alpinui inventory and every broad styled suite show that components alone
cannot produce a coherent default. The assets must remain prebuilt in the
`citry-ui` wheel and useful without a consumer build.

### 4.2 Layout and shell

- Box/Surface, Container, Stack, Inline/Group, Grid, Divider, and AspectRatio;
- host-neutral AppShell, Header/AppBar, Main, Footer, Sidebar, and responsive
  navigation layout;
- ScrollArea, Splitter, and overflow helpers only where native CSS is
  insufficient and the behavior contract is explicit.

Layout primitives should be predominantly server-only. Shipping them in the
same distribution must not activate browser behavior on a static page.

### 4.3 Actions

- Button, IconButton, ButtonGroup;
- Toggle and ToggleGroup/SegmentedControl;
- semantic link/action variants without hiding element and form behavior.

The headless action surface still owns native-element choice, keyboard, form
type, disabled, loading, focus-visible, and press semantics. Vuetify v0's
[polymorphic-button defect](complaint-register.md#retained-patterns) is grade-A
evidence that styling independence does not transfer those obligations to the
consumer.

### 4.4 Forms and selection

- Field, Label, Description, Error, and FormSummary;
- Input, Textarea, Checkbox/CheckboxGroup, RadioGroup, Switch, NativeSelect;
- Combobox/Autocomplete and MultiSelect/Tags as collection-backed controls;
- NumberInput, Slider/Range, Rating, PinInput, FileInput/DropTarget where
  staged;
- Form layout, native submission, Citry Events submission, loading, disabled,
  reset, autofill, server errors, and focus-on-error as cross-family contracts;
- dynamic collections, uploads, and date/time as later or specialist work
  according to sections 5 and 6.

Field anatomy is a foundation for controls, not a styling wrapper. Labels,
descriptions, errors, generated IDs, native names/values, and persistent live
regions must survive fragments and morphing in both visual modes.

### 4.5 Navigation and disclosure

- Breadcrumbs, Tabs, Pagination, NavList/NavLink, Menu, and NavigationMenu;
- Disclosure/Accordion and Stepper;
- route-aware examples remain recipes over host-neutral component state.

Tabs and Disclosure are separate interaction patterns. Stepper is a workflow
presentation, not a synonym for either. Application route maps, permissions,
and domain navigation do not enter the component API.

### 4.6 Feedback and status

- Alert/Callout, Badge/Tag/Chip, Progress, Spinner, Skeleton, and EmptyState;
- Toast/Notification with queue, priority, lifetime, action, and announcement
  behavior;
- LoadingOverlay and Result/status compositions where they add a consistent
  product job.

Feedback families share semantic intent and pending/success/warning/error
vocabulary. Visual styling must not determine live-region urgency or initial
announcement behavior.

### 4.7 Overlays

- Dialog, AlertDialog, Drawer/Sheet, Popover, Tooltip, Menu popup, and
  HoverCard where staged;
- shared portal, positioning, focus, dismissal, inertness, scroll, stacking,
  presence, and restoration behavior.

Overlay infrastructure is one behavior foundation consumed by several
families. It must not become multiple independent implementations merely
because each family has different styled markup.

### 4.8 Data display and collections

- Avatar, Card, List, DescriptionList/DataList, Table, Timeline/Statistic, and
  Disclosure;
- Tree and Carousel where staged;
- a simple composable Table in core, with sorting/filtering/pagination recipes
  only when their ownership is explicit;
- virtual lists, editable collections, and advanced grid behavior later or in
  companions.

Collection behavior should normalize item identity, disabled items,
selection, highlighting, ordering, empty/loading/error states, and server
replacement. It should not assume ORM objects or a particular endpoint.

### 4.9 Utilities and behavior foundations

- VisuallyHidden, FocusScope/focus restoration, FocusVisible, Portal,
  Presence, DismissableLayer, and responsive visibility;
- collection, roving-focus, generated-ID, form-field, and overlay behavior
  shared internally and exposed only where user-authored headless composition
  needs a stable contract;
- environment and ambient-context behavior for document/root, direction,
  defaults, portal target, density, and future locale selection.

The taxonomy recognizes these foundations without deciding whether they are
public component classes, helpers, or internal contracts. The later provider
study still decides how `$component.init()` and possible `$provide`/`$inject`
magics relate.

## 5. Staged breadth

Staging is a release-order hypothesis, not a promise that every named family
ships in the first `1.0.0` build. A family advances only with its paired
styled/headless contract, documentation, assets, introspection, browser tests,
and quality matrix. Presentational families receive a genuine semantic
headless form rather than invented behavior.

### 5.1 Version 1 core

| Category | Families and foundations |
|---|---|
| Foundations | Reset/layers, semantic tokens, typography, spacing, radius, elevation, motion, density, responsive rules, light/dark/brand themes, LTR/RTL, icon adapter, provider/environment, generated IDs |
| Layout and shell | Surface, Container, Stack, Inline/Group, Grid, Divider, AspectRatio, AppShell, Header, Main, Footer, Sidebar layout |
| Actions | Button, IconButton, ButtonGroup, Toggle, ToggleGroup |
| Forms | Field anatomy, FormSummary, Input, Textarea, Checkbox/Group, RadioGroup, Switch, NativeSelect, Combobox/Autocomplete, native and Events-aware Form behavior |
| Navigation | Breadcrumbs, Tabs, Pagination, NavList/NavLink, Menu, Disclosure/Accordion |
| Feedback | Alert, Badge/Tag, Progress, Spinner, Skeleton, EmptyState, Toast/Notification |
| Overlays | Dialog, AlertDialog, Drawer, Popover, Tooltip, popup behavior shared with Menu |
| Data display | Avatar, Card, List, DescriptionList/DataList, semantic Table |
| Utilities | VisuallyHidden, FocusVisible, FocusScope/restoration, Portal, Presence, dismissal, responsive visibility |

#### Release prerequisites for the Version 1 set

The table is a target set, not permission to call every row shipped
independently. Version 1 release requires all of the following foundations to
pass their acceptance suites first:

- package discovery, registration, asset publishing, asset introspection, and
  direct-install smoke tests for the Python wheel;
- provider and physical-environment behavior across nested scopes, reactive
  changes, concurrent roots, portals, the documented current CSP baseline,
  teardown, and missing-context diagnostics;
- stable generated IDs and server/client agreement through activation,
  fragment insertion, morphing, removal, and reconnection;
- shared portal, presence, focus, inertness, dismissal, scroll, and restoration
  behavior; and
- paired styled/headless documentation and test coverage for every family that
  claims both surfaces.

Context-dependent Toast/Notification, Dialog, Drawer, Menu popup, Popover, and
Tooltip do not count as shipped merely because their templates render. They
remain release-gated until the ambient-context, provider/environment, asset-
publishing, lifecycle, and overlay prerequisites above pass. The later
provider study still decides the public API shape.

This is intentionally more than a starter pack. It covers marketing pages,
account/settings flows, ordinary CRUD, dashboards, navigation, feedback,
forms, and dense server-rendered tables without requiring another general UI
library. It also stays below mature Vuetify or Ant breadth by withholding
families whose locale, security, collection, or specialist contracts are not
yet settled.

### 5.2 Near-term breadth

- NumberInput, Slider/Range, Rating, PinInput, SegmentedControl, SplitButton;
- MultiSelect/TagsInput and richer Combobox collection presentations;
- FileInput and DropTarget as file selection, without pretending to own secure
  upload storage or transport;
- Stepper, NavigationMenu, CommandPalette, ContextMenu, HoverCard, BottomSheet;
- LoadingOverlay, Result/status composition, notification queue refinements;
- ScrollArea, Splitter, Timeline, Statistic, Tree, Carousel;
- sortable/filterable/paginated server Table recipes that preserve the core
  semantic Table and explicit state ownership;
- application-shell recipes for common marketing and dashboard layouts.

### 5.3 Later general-suite work

- date, time, calendar, date-range, and locale-sensitive number controls only
  after the localization follow-up establishes their contracts;
- ColorPicker and advanced color controls;
- repeatable and nested form collections, editable collections, sortable
  lists, drag and drop, and Tree editing;
- virtual list/table windows and infinite scrolling;
- managed upload workflow, previews, cancellation, retry, temporary storage,
  and server validation;
- Tour, Transfer/PickList, image comparison, QRCode, Watermark, and other
  lower-commonality utilities when product demand and maintenance justify them.

Later does not mean unimportant. Editable collections and remote selection are
strong local pressure cases. It means their identity, async, form, security,
and morph behavior must be proven before they become a broad support promise.

### 5.4 Companion-package boundary

The default distribution should not absorb specialist products merely to
match the longest catalogs. The initial boundary is:

| Companion domain | Why it stays separate |
|---|---|
| Charts and data visualization | Rendering engines, accessibility descriptions, export, large-data performance, and domain semantics need a distinct dependency and release policy. |
| Rich-text editing | Trusted HTML, sanitization, paste, schema, collaboration, uploads, selection, and document migration create a separate security and behavior product. |
| Maps and geospatial UI | Map engines, tiles, network services, attribution, geometry, keyboard navigation, and large assets are independent concerns. |
| Domain-heavy data grids | Spreadsheet interaction, column models, aggregation, pinning, virtualization, editing, export, and server query protocols exceed semantic Table. |
| Diagramming, Gantt, scheduling, and organization charts | Domain models, canvas/SVG interaction, drag geometry, time scales, and export need specialist ownership. |
| Media and image editors | Decoding, cropping, transforms, memory, file trust, and output formats require separate payload and threat policies. |

Companions may share Citry UI tokens, Field anatomy, overlays, feedback, and
collection conventions. Their absence from `citry-ui` is an explicit boundary,
not hidden incompleteness.

### 5.5 Localization follow-up marker

This taxonomy does not design translation keys, catalogs, locale resolution,
formatters, plural rules, time zones, or fallback. Version 1 accepts
application-supplied labels and messages and supports inherited LTR/RTL.
Localization research follows after the authored-text inventory is stable.
Locale-aware date/time/number families remain gated on that work.

## 6. Evidence-derived prototype risk rubric

The comparative prototype must reveal difficult contracts, not reward simple
screenshots. Each candidate is assessed on five axes from 0 to 3:

| Axis | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Native semantics and forms | No interactive semantics | One native element with ordinary attributes | Composite semantics or hidden/native synchronization | Element substitution, validation, live regions, or native/Event submission can diverge |
| State, identity, and async | Static | Local scalar state | Collection identity or controlled/uncontrolled state | Remote, reorderable, repeatable, virtual, or stale-response-sensitive state |
| Focus, overlay, and context | None | Local focus-visible behavior | Roving focus or one inherited value | Portal, nested overlay, inertness, restoration, environment, or provider shadowing |
| Server lifecycle | Static server HTML | One activation path | Fragment update or conditional presence | Morph, removal, reconnect, teleport, concurrent roots, or dynamic insertion |
| Trust, delivery, and performance | Escaped text and static CSS | Ordinary URLs/attrs or small behavior | Remote content, runtime style, dense repetition, or optional assets | Files/trusted HTML, strict CSP, large collections, cross-package assets, or security-sensitive transport |

Risk band uses the maximum axis rather than a summed score:

- **Critical:** at least one axis is 3 and the family crosses three or more
  axes at level 2 or 3.
- **High:** one axis is 3, or three axes are 2.
- **Moderate:** remaining interactive or structural work.

An A/B finding can justify a concrete test and a C pattern can justify a
recurrence test. A grade-D report can add a test case only when standards,
source, local requirements, or stronger independent evidence already place the
case inside scope. It cannot raise the band by itself.

### 6.1 Frozen slice assessment

| Prototype member | Semantics/forms | State/async | Focus/context | Server lifecycle | Trust/delivery | Band | Evidence-derived purpose |
|---|---:|---:|---:|---:|---:|---|---|
| Button | 3 | 1 | 1 | 1 | 1 | High | Prove native button/link choice, `type`, disabled/loading, slots, attributes, and styled/headless parity. VU-3 is grade A. |
| Field and Input | 3 | 2 | 1 | 3 | 2 | Critical | Prove stable IDs, labels/descriptions/errors, persistent live regions, native form behavior, server errors, and morph survival. M-2 is A; CZA-4 and PCP-2 are B. |
| Dialog | 1 | 2 | 3 | 3 | 2 | Critical | Prove portal ownership, nested focus, inertness, Escape/outside interaction, restoration after activator removal, presence, cleanup, and local provider values. RA-3 is A for the mechanism; BSR-3 and M-3 add recurring evidence. |
| Combobox | 3 | 3 | 3 | 3 | 3 | Critical | Prove collection identity, keyboard/IME/touch, mobile screen readers, hidden/native value, remote result safety, stale-response rejection, portal behavior, and server replacement. AD-1, M-3, CZA-5, and PV-5 supply grade-C recurrence across distinct mechanisms. |
| Tabs | 2 | 2 | 2 | 2 | 1 | High | Prove roving focus, activation mode, panel identity, orientation/RTL, dynamic removal, URL/server ownership, and styled/headless part equivalence. RN-1 is resolved grade-B history and local prior art shows incomplete ad hoc semantics. |
| Semantic Table | 2 | 2 | 1 | 2 | 2 | High | Prove native structure, composable cells/actions, dense rendering, empty/loading/error states, row identity, fragment replacement, and no accidental DataGrid promise. |
| Dynamic form/collection workflow | 3 | 3 | 3 | 3 | 3 | Critical | Prove repeatable item identity, add/remove/reorder, field errors, async selection, submission, focus after mutation, activation, and cleanup. DF-3 is A and DF-4 is B; local prior art supplies direct demand. |
| Provider and ambient context | 1 | 2 | 3 | 3 | 3 | Critical | Prove defaults, nesting, shadowing, reactive updates, server/client agreement, portal logical ancestry, physical environment, CSP values, teardown, and diagnostics. AD-2 and CZA-1 are grade-A mechanisms. |

### 6.2 Exact comparative prototype set

All eight frozen probes advance because together they cover every risk axis:

1. paired styled/headless Button;
2. paired Field and text Input inside both a native form and a Citry Events
   form;
3. paired Dialog using the shared overlay foundation;
4. paired remote Combobox with deterministic item identity, cancellation, and
   stale-result rejection;
5. paired Tabs with dynamic panels;
6. paired semantic Table with composed row actions, not a DataGrid;
7. one repeatable form-row workflow using Field/Input plus async Combobox,
   add/remove, server validation, and a morphing response;
8. the ambient-context mechanism exercised by nested theme/direction/default
   scopes and a portaled Dialog.

The workflow deliberately omits file upload and date/time. It already reaches
critical identity, validation, async, focus, and morph risk without importing
the upload security product or pre-empting localization. File and date probes
remain later acceptance work.

## 7. Resulting breadth principles

1. Breadth is measured at the `citry-ui` Python, template, browser, asset,
   documentation, and quality contract together. A generated file or CSS class
   alone is not a shipped family.
2. Every family has styled and headless authoring surfaces over one semantic,
   state, accessibility, and lifecycle implementation. A style-off switch is
   useful evidence but not the whole promise.
3. Native HTML is the baseline. Enhancement preserves form submission,
   semantics, and useful server-rendered output wherever the pattern permits.
4. Simple structural components stay static. Catalog membership cannot make a
   page pay for unrelated behavior.
5. Named parts, state attributes, tokens, variants, and explicit root/part
   attributes carry ordinary customization before source ownership.
6. Collections share item identity and async state vocabulary, while
   application endpoints, ORM objects, routes, and authorization remain
   outside the UI taxonomy.
7. Semantic Table is core; domain-heavy DataGrid is a companion. File
   selection is distinct from upload infrastructure. Date presentation is
   distinct from the deferred localization contract.
8. Direct `uv add citry-ui` installation remains the only recommended
   distribution path. No `citry[ui-default]` alias, consumer JavaScript build,
   external runtime, CDN, or mutable network asset is part of the product
   shape.
