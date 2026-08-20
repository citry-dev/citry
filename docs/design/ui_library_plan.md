# Plan: the Citry UI component library

**Status (2026-08-19): `citry-ui` 0.1.0 is publicly available as an early-access
release. The source-development catalog contains 60 documented component
families and 107 registered definitions, including compound-family
declarations and private renderers; its contracts remain alpha rather than
stable.**

Phases 0 through 6 are complete. Citry's generic publishing contracts, slot
contracts, client ambient context, and docs live-component host are
implemented. Phase 7 began on the released `citry 0.3.1` and `citry_core
1.4.0` floor. Current source development and the released 0.1.0 line use the
published `citry 0.4.0` and `citry_core 1.5.0` floor. The
[active component inventory](ui_component_inventory.md) owns current family
status. Counts and family lists inside the chronological phase records below
describe those dated slices rather than the current catalog.

This plan defines the research and decision process for Citry's
official component library. The ratified product
target is recorded in
[`ui_research/product-charter.md`](ui_research/product-charter.md).

The planned Python distribution is `citry-ui`, imported as `citry_ui`. It is a
separate first-party package built on Citry. Phase 7 builds a styled component
surface that is usable without design work and has Vuetify-level configuration
and browser interaction. Headless component APIs are parked until real
application usage reveals their useful contract.

Citry's generic library publishing and engine-neutral invocation APIs are now
implemented. Production families follow the reusable
[`component specification template`](ui_components/_template.md). The working
[`theme and color-scheme contract`](ui_theme.md) fixes light/dark ownership and
acceptance while the production slice supplies evidence for the final provider
and global token architecture. The
[active component inventory](ui_component_inventory.md) orders source work;
the public v1 contract remains a Phase 8 decision.
For repository operating rules, see [`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. Desired outcome

Citry users should be able to build a polished application without first
assembling an unrelated UI stack. The library should be comparable in product
ambition to established suites such as Vuetify:

- styled and useful immediately;
- native to the framework's component, slot, asset, and client models;
- accessible across the supported interaction modes;
- customizable through theme tokens, variants, slots, documented parts, and
  explicit HTML attributes;
- broad enough for the common layout, navigation, form, feedback, overlay,
  and data-display needs of an application.

Specialist products such as charts, rich-text editors, maps, and domain-heavy
data grids may remain companion packages. The research decides that boundary
from evidence rather than treating maximum component count as the goal.

## 2. Decisions already made

The maintainer ratified these product decisions on 2026-07-23 and updated the
Phase 7 scope on 2026-07-29:

1. The UI library is a separate first-party Python distribution. The leading
   names are the `citry-ui` distribution and the `citry_ui` import package.
2. The default experience is a styled, coherent, batteries-included library,
   not a collection of unstyled primitives.
3. Phase 7 ships styled production components only. Existing headless pressure
   components are not production commitments. Reconsider a headless surface
   after the library has broader real-world usage, concrete customization
   requests, and representative pages for API and performance evaluation.
4. The breadth target is a general-purpose suite. A developer should not need
   another generic component library for ordinary application UI.
5. The library uses Citry's public server and browser contracts. It does not
   add React, Vue, or a second client component runtime.

The supported installation path is direct and explicit:

```sh
uv add citry-ui
```

`citry-ui` owns its package files and depends on a compatible Citry release.
Installing the Python distribution and registering its components into a
Citry engine remain separate contracts.

## 3. Research principles

### 3.1 Compare architectures, not only brands

The ecosystem sample is stratified by delivery and customization model:

- styled batteries-included systems;
- headless accessible primitives;
- source-copy systems;
- CSS-only and Web Component systems;
- server-rendered Python systems;
- form-specialist systems.

Libraries that share the same lower-level implementation are related evidence,
not independent votes. Standards such as WAI-ARIA APG, Open UI, and the HTML
standard are acceptance baselines rather than scored libraries.

### 3.2 Gather evidence before designing Citry APIs

Each library receives the same evidence record: version and date, license and
paid boundaries, component inventory, composition API, customization depth,
accessibility, internationalization, form behavior, client state, assets,
performance, maintenance, complaints, and Citry fit.

Documentation claims and reproduced behavior carry separate confidence. A
polished example is not proof of keyboard, screen-reader, morph, or server-form
behavior.

### 3.3 Treat complaints as versioned evidence

The complaint protocol is frozen before reading community reports. Every
material complaint records:

- the exact library version and research date;
- the stable source and the search query that found it;
- the affected component or workflow;
- a reproduction, source check, or current documented contract;
- maintainer response and available workaround;
- recurrence across independent users;
- impact, current status, and evidence confidence.

Findings are classified as current limitations, current defects, recurring
friction with a workaround, resolved history, deliberate trade-offs,
preferences, or unverified claims. One report remains one report. Raw issue
counts are not quality scores, and lack of complaints is not evidence of
satisfaction.

### 3.4 Let prototypes falsify the architecture

The architecture stage produces hypotheses, not a final decision. At least two
plausible approaches implement the same risk-heavy slice. The final decision
follows those results so the prototype cannot become confirmation work for the
preferred design.

## 4. Work phases

### Phase 0: product charter

**Goal:** define what the library is trying to be before popular libraries
influence the criteria.

**Output:** [`ui_research/product-charter.md`](ui_research/product-charter.md),
covering users, jobs, the styled production promise, meaning of "default",
breadth, framework integration, accessibility, support floors, hard
boundaries, and evaluation weights.

The concrete verification approach for those floors is recorded in
[`ui_research/quality-test-strategy.md`](ui_research/quality-test-strategy.md).

**Gate:** maintainer approval of the charter and of any later change that
materially shifts the target.

### Phase 1: current Citry baseline

**Goal:** separate live Citry capabilities from proposals and parked work.

**Output:** [`ui_research/citry-baseline.md`](ui_research/citry-baseline.md), a
sourced matrix of mechanisms the library may rely on and constraints it must
design around.

**Gate:** every implementation assumption maps to a live public contract or is
marked as a prerequisite with its own design and work package.

### Phase 2: local prior art

**Goal:** recover lessons from the former Alpinui/Vuetify work and the
maintainer's production application without treating either as a blueprint.

**Output:** [`ui_research/local-prior-art.md`](ui_research/local-prior-art.md),
including:

- the actual Alpinui component-family and capability inventory;
- its JavaScript/Python distribution and asset architecture;
- unfinished integration, testing, performance, and maintenance lessons;
- the reusable component families and UI jobs observed in the production app;
- a reuse, re-derive, and reject classification.

The existing written audits are the first source. Raw archives are read only
for targeted gaps, never extracted into the repository, and never used to
publish secrets, private data, or proprietary implementation. Code reuse
requires a separate provenance and license review.

### Phase 3: breadth scan and corpus selection

**Goal:** map the field, then freeze a manageable, representative deep-dive
set.

**Seed set:**

- React: MUI, Ant Design, Mantine, Chakra UI, shadcn/ui, React Aria, and
  Radix or Base UI;
- Vue: Vuetify, PrimeVue, Quasar, Reka UI, Nuxt UI, and Element Plus;
- framework-neutral: Bootstrap, daisyUI, Web Awesome, and a current
  standards-based design-system implementation;
- Python and Django: Cotton UI, labb, django-crispy-forms, django-formset,
  django-components publishing, and Cotton's component model.

**Selection rule:** choose about twelve deep dives across the architecture
strata, based on distinct mechanism, relevance, maintenance, license, and
adoption. Record why each was selected and which alternatives it represents.
Stop secondary additions when two consecutive candidates add no component
category, architecture, or failure mode.

**Gate:** corpus and evidence-protocol approval, followed by independent
adversarial review.

### Phase 4: deep dives and complaint register

**Goal:** produce comparable, evidence-rich reports.

Each dossier records:

1. snapshot, license, paid boundaries, dependencies, and maintenance;
2. normalized component inventory;
3. props, events, slots, compound APIs, state, attributes, portals, and item
   identity;
4. theme tokens, variants, parts, markup control, behavior control, and source
   ownership;
5. accessibility, keyboard, focus, touch, screen reader, RTL, locale, dates,
   reduced motion, and forced colors;
6. forms, validation, native submission, loading, errors, and async behavior;
7. content trust, escaping, URLs, attribute forwarding, files, generated IDs,
   remote results, and component-specific threat cases;
8. CSS/JS delivery, build requirements, icons, fonts, CSP, payload, and
   upgrade cost;
9. current shortcomings and their evidence;
10. mechanisms worth adopting, mechanisms that do not transfer, and pressure
   on Citry's public contracts.

**Gate:** evidence review checks dates, citations, confidence, counterevidence,
and unresolved claims.

### Phase 5: synthesis

**Goal:** turn individual reports into cross-library conclusions before
proposing a Citry API.

**Outputs:**

- normalized component-inventory heatmap;
- common API and composition patterns;
- customization ladder from theme tokens through source ownership;
- recurring failure-mode map;
- styled, headless, source-copy, CSS-only, and Web Component comparison;
- Citry capability-fit matrix;
- proposed component taxonomy and staged breadth.

**Gate:** a maintainer checkpoint and an independent adversarial review. The
exact prototype components are selected here using a risk rubric.

### Phase 6: architecture hypotheses and packaging spike

**Goal:** make the plausible product shapes concrete without selecting one.

The comparison covers:

- paired styled and headless components as installed dependencies;
- source-owned or generated headless components with a styled distribution;
- CSS utilities where they solve a distinct problem;
- a hybrid of stable behavior primitives, default theme, and optional source
  ownership.

Web Components remain comparison evidence and may be supported as isolated
leaf interoperability helpers. They are not a candidate architecture for the
Python Citry styled/headless core and may not introduce a second component,
state, slot, Events, or lifecycle runtime.

The packaging and registration spike covers:

- direct `citry-ui` installation under pip and uv;
- the required `citry-ui -> citry` compatibility relationship;
- clean installs, upgrades, downgrades, wheel contents, and uninstall;
- the separate `citry_ui` import namespace;
- first, repeated, concurrent, two-engine, collision, rollback, and failed
  initialization behavior;
- direct registered tags, engine-neutral public Python invocations, flat
  per-Citry styled/headless references for advanced use, annotations,
  Python composition, subclassing or supported alternatives, and
  deterministic family pairing;
- deterministic component introspection and asset discovery;
- version compatibility, release ordering, and deprecation policy;
- installation and runtime without Node, a compiler, a CDN, or a network
  download.

**Gate:** the publishing architecture is proven. Local-artifact installation,
registration, assets, and atomic rollback have passed. Current source
development targets `citry>=0.4.0,<0.5.0` with the published `citry_core
1.5.0` floor. The 0.1.0 release gate verified that pair in clean installs.
Multi-release upgrade, downgrade,
uninstall, and wheel fixtures remain publication work. Phase 7 uses one public architecture:
`LibraryComponent` definitions in the separate `citry-ui` distribution,
registered explicitly into each Citry engine. The earlier H1/H2/H3 comparison
is historical research rather than multiple advancing production architectures.

### Phase 7 readiness and optional preview tooling

The framework and quality foundations needed to begin Phase 7 now exist:

- the accepted Python-owned
  [scenario-catalog contract](ui_research/scenario-catalog.md) separates
  reusable states and workflows from their quality-tool consumers;
- the docs site provides first-party live components and a playground without
  requiring Node;
- direct Playwright, axe, Lighthouse, screenshots, host tests, and manual
  accessibility work remain the authoritative quality paths;
- `LibraryComponent`, `ComponentLike`, nested declarations, typed slot data,
  slot-data destructuring, `SlotInput[T]` validation, and atomic library
  registration are implemented;
- server and client `provide`, `inject`, and `unprovide` contracts are
  implemented and browser-tested; and
- the published `citry 0.4.0` and `citry_core 1.5.0` line is the current
  development and published 0.1.0 line.

Storybook is now independent optional extension work, tracked in
[`extensions_storybook.md`](extensions_storybook.md) and its supporting
[`extensions_storybook/`](extensions_storybook/) research. Its private Citry
UI spike remains useful evidence about Controls, generated stories, asset
activation, preview replacement, and contributor workflow. Adapter selection
and broader interactive coverage do not gate Citry UI specifications,
implementation, documentation, or publication.

At this point in the chronological Phase 7.5 record, the implementation slice
contained thirty-one production families.
Direct cross-browser suites cover native actions and forms, compound Tabs,
native modal Dialog, remote Combobox request ordering, keyed semantic Table,
browser-owned dynamic Form membership, and the repeatable business workflow. Tabs includes
server reorder and removal, deterministic focus recovery, and client-owned
removal callbacks. The representative public-site form and dashboard exercise
two brands through documented tokens and parts. Aggregate Brotli assets and
local interaction timing are inside the frozen budgets, and the representative
complete page has zero serious or critical axe violations. Tabs has also
completed the first full public-documentation pass: 13 component-owned
previews cover composition, configuration, variants, density, layout,
controlled selection, disabled behavior, keyboard activation, overflow,
nesting, direction, and theming. Its public reference is generated from the
family-owned `api.yml`.

Phase 7.5 now supplies the repository-side release qualification described
below: per-state axe coverage, visual-candidate capture, Nu HTML and Lighthouse
CI profiles, Bootstrap and Tailwind coexistence, bounded asset and scaling
profiles, host fixtures, public live examples, and clean-wheel lifecycle jobs.
That infrastructure does not turn configured CI into a pass or replace human
review. Hosted Nu, Lighthouse, approved screenshots, manual keyboard and
assistive-technology results, and real mobile and Safari evidence remain
stabilization work after the bounded 0.1 early-access gate.

An InfiniteScroll observer and async-cleanup proof remains optional if those
required cases expose the same lifecycle constraints. All disposable helpers
stay outside the public `citry_ui` manifest. A custom gallery is not planned:
the docs live-component host is the first-party preview surface, and a
different state browser should be designed only if a concrete need remains
unserved by the docs site and the optional Storybook extension.

The 0.1.0 early-access release qualification sequence was:

1. build and inspect one wheel and source distribution;
2. install the wheel with the published Citry floor across supported Python
   versions, render representative components, and exercise one browser
   interaction from those exact bytes; and
3. publish only the retained artifacts that passed that gate.

Visual approval, manual assistive-technology and real-device evidence,
multi-release upgrade and downgrade checks, and the final Phase 8 production
contract continue as stabilization work. Source development follows the next
batch in the
[active component inventory](ui_component_inventory.md). Each planning group
receives a bounded family-boundary and dependency pass before implementation
begins. The resulting batch reserves capacity across foundations/layout,
native forms/choice controls, and feedback/compound interaction. Each selected
family then completes the full research, specification, example,
implementation, documentation, and review pipeline before the next begins.

Button completed first, followed by Field/Input, Form, Dialog, and Combobox. Dialog now
has its revised native-modal runtime, nested ownership and focus evidence,
structured reference, and eleven component-owned live examples. Human visual,
keyboard, assistive-technology, and real-device polish remains part of the
release review. Combobox now has its strict editable-single-select contract,
independent value/query/open ownership, abort-safe local and remote behavior,
native Form and IME evidence, structured reference, and nine astronomy-themed
live examples. Table now has its native simple-Table boundary, one-row footer,
column-wide cell attributes, named responsive scrolling, distinct sticky
modes, nested-Table CSS isolation, structured reference, and nine
astronomy-themed live examples. Human visual, keyboard,
assistive-technology, print, and real-device review remains release evidence.

Compatible `citry` and `citry_core` releases are now public. The active
component inventory pulls forward the Phase 8 inventory and source work that
can continue after the 0.1.0 early-access release. Its
bounded family pass selected Icon, Card, Textarea, Native Select, Checkbox,
Alert, and Accordion, in that order. IconButton remains a Button + Icon
composition, generic Surface remains private styling infrastructure, and this
seven-slot batch carries layout forward behind the selected foundation, form,
choice, feedback, and interaction jobs. Named responsive Grid inputs originally
had the additional prerequisite of a public breakpoint or container-query
vocabulary; the post-third-batch layout pass has now resolved it with fixed
mobile-first `sm` through `xxl` viewport thresholds and consumer CSS for
bespoke queries.
Callout is an Alert recipe, and standalone Disclosure remains separate from
grouped Accordion. Each selected family received its own research,
specification, example, implementation, documentation, and review pass. The
final v1 contract, compatibility range, and release contents remain Phase 8
decisions.

Icon completed that pipeline on 2026-08-08. It ships a static local Lucide
catalog with semantic aliases, decorative and labelled accessibility modes,
logical RTL mirroring, strict SVG trust boundaries, exact third-party notice
qualification, public documentation, and focused server/browser/wheel
evidence. Card also completed the pipeline with static optional anatomy,
explicit part destinations, overlay-safe overflow, one-child row geometry,
media-only edge handling, nine public examples, focused evidence, exact wheel
qualification, and independent closure review. Textarea completed the same
pipeline with native multiline editing, controlled and uncontrolled browser
ownership, Field/Form integration, safe RCDATA handling, eleven public
examples, scaling and quality coverage, exact wheel qualification, and
independent closure review. Native Select completed the same pipeline with a
native single-Select root, structured options and groups,
placeholder-required conformance, controlled and uncontrolled ownership,
reactive Field capabilities, ten public examples, exact wheel qualification,
and independent closure review. Checkbox completed its production runtime,
public guide, structured reference, focused family evidence, quality scenario,
and wheel wiring; final cross-family qualification remains pending. Alert
completed the pipeline with persistent feedback,
announcement-role ownership, one allowlisted icon path, actions, ten public
previews, focused evidence, wheel qualification, and independent closure
review. Accordion completed it with direct declaration ownership, single and
multiple expansion, keyboard and focus recovery, nested groups, ten public
previews, reusable quality evidence, wheel qualification, and independent
closure review.

This follows component dependencies and increases interaction risk gradually.
Each pass starts by auditing the existing
design, source, tests, quality scenarios, public guide, and structured
reference. Existing work may be retained when current evidence supports it,
but it does not bypass research or freeze the API. No runtime changes begin
until the family's current-source record, complete specification, and example
coverage catalog are ready for review.

The Tabs pass left one maintained source for each reusable lesson:

| Concern | Maintained source |
|---|---|
| Family research, source freshness, specification, implementation, and review order | [`citry_ui` component policy](../../packages/py/citry_ui/docs/component-authoring.md#requalify-one-component-family-at-a-time) |
| Required component decisions and source record | [Component specification template](ui_components/_template.md) |
| Result-first examples, controls, page tone, and coverage catalog | [Preview and public-example contract](ui_components/_preview.md) |
| Server inputs, client overrides, callbacks, slots, anatomy, templates, and CSS authoring | [Repository component best practices](../best-practices/component-authoring.md) |
| Theme and color-scheme ownership | [Theme contract](ui_theme.md) |
| Reusable quality scenarios and complete-page routes | [Scenario catalog](ui_research/scenario-catalog.md) |
| Automated and human evidence | [Quality strategy](ui_research/quality-test-strategy.md) |
| Tabs-specific products, standards, complaints, choices, and example progression | [Tabs specification](ui_components/tabs.md) |

The family workflow links these documents rather than copying their details.
When a later family exposes a reusable rule, update the narrowest owning source
before beginning the next family.

### Phase 7: production vertical slice

**Goal:** prove that Citry UI can deliver Vuetify-level component
configuration and browser interaction through native Citry contracts before
expanding the catalog.

The slice is selected after synthesis and the readiness work. Production
components use the one `LibraryComponent` publishing architecture and own
their styled markup, configuration, interaction, and accessibility behavior.
Form composition and client ambient context are cross-cutting workflow and
framework probes. The eight required probes are:

- Button for attributes, variants, slots, icons, loading, and disabled
  semantics;
- Field plus Input for labels, descriptions, errors, native forms, Events,
  and edit preservation;
- stateful Tabs for compound ownership, selection, keyboard navigation,
  direction, focus, dynamic removal, server replacement, and morphing;
- Overlay/Dialog for focus, Escape, outside interaction, scroll, layering,
  teleport, and cleanup;
- remote Combobox or MultiSelect for collections, keyboard navigation, async
  data, ARIA, request cancellation, stale results, and native form output;
- semantic Table for keyed collections, slot composition, empty/loading/error
  states, large output, and fragment replacement;
- Form plus one repeatable workflow for dynamic child ownership, nested values,
  validation, browser submission, Events, and add/remove/reorder identity; and
- client ambient context for defaults, nesting, shadowing, reactivity, logical
  ancestry, caller-owned slots, teleports, morphs, cleanup, and diagnostics.

Toast remains an optional ninth pressure case only if the charter still needs
a cross-component imperative service.

The acceptance matrix includes the charter's desktop and mobile browser
floor; WCAG 2.2 AA; APG keyboard behavior; automated and manual accessibility
checks; representative screen-reader pairs; touch, IME, zoom, forced colors,
reduced motion, RTL, author-supplied text, and dark mode; content-trust and
component-specific threat cases; morphing while open, focused, editing, or
awaiting data; slot ownership; nested and conditional roots; fragment
insertion; cleanup; server and native form behavior; CSS coexistence;
deterministic assets; deep Django and FastAPI fixtures; and registration,
asset, render, form, and Events smoke tests for every shipped Citry host.

The styled slice must also prove the product claim rather than only
technical correctness. Before implementation, the comparison freezes:

- complete fixtures for every supported state, variant, size, density,
  responsive mode, dark mode, RTL mode, and error condition in the slice;
- a representative public-site form and application/dashboard composition
  built without consumer CSS;
- cross-browser screenshot regression with reviewed tolerances;
- independent design review of hierarchy, typography, spacing, color,
  interaction feedback, responsiveness, and consistency;
- two distinct brand adaptations using documented tokens and parts only.

Each production component comparison must also inventory the notification
surfaces of relevant React, Vue, Web Component, and native counterparts:
names, trigger conditions, request-versus-commit meaning, controlled and
programmatic behavior, ordering, cancellation, and payload. Citry UI uses
optional callback inputs such as `onValueChange` through `$c-props` for
component-authored notifications and leaves Alpine `@...` listeners to native
browser events. A custom DOM event advances only with a documented interop or
lifecycle need that those two surfaces cannot meet.

The same comparison must inventory composition surfaces: ordinary children,
named and scoped slots, render callbacks, collection renderers, and
replaceable internal parts. The resulting specification records every chosen
slot's purpose, data shape, fallback, cardinality, nesting, and error behavior.
Data-driven families must explicitly decide whether they need dynamic keyed
slot namespaces such as `header.<key>` or `item.<key>`, including their name
grammar, fallback precedence, collisions, typing, and introspection. A dynamic
slot family does not advance until Citry's parser and runtime behavior are
proven for it.

Every production family fills the complete component specification template
before implementation. The template also classifies stable public API,
behavioral and required structural contracts, evolvable default design, and
private implementation. Exact theme values and incidental wrappers must not
become accidental semantic-versioning commitments merely because a screenshot
or implementation test observes them.

After the family works end to end, repeat its public-anatomy review before
freezing the API. Implementation evidence may show that a structural component
only groups declarations or forwards inputs. Remove it when an existing owner
can accept those inputs and preserve every supported composition, validation,
semantic, customization, and extension scenario. Tabs establish the reference
case: `CTabs` can collect lazy `CTab` and `CTabPanel` declarations and generate
the single semantic TabList internally, so a public list wrapper does not earn
its API cost.

Styled components support the default light and dark schemes as a library
quality requirement. Applications choose and persist the active scheme and
own brand overrides. The Phase 7 Overlay slice must prove nested scopes and
theme continuity when an overlay's physical DOM location differs from its
Citry owner before the final theme-provider API is selected.

The typed Python slice uses direct tags and an imported engine-neutral
component invocation from ordinary application code. It also obtains the
ordered `LibraryInstallation` and its exact-definition class lookup for
advanced composition and introspection, exercises the supported extension
mechanism, and verifies that each component is exposed deterministically.

Before implementation, Phase 7 ratifies or records a revision to the Phase 6
budgets for compressed asset size, first-interaction cost, documented-token
theme coverage, selector overrides, registration failures, lifecycle cases,
visual-regression tolerances, and complete styled-state coverage.

Headless APIs and the styled-via-headless performance comparison are parked.
Revisit them only after the styled catalog and an actual application provide
representative pages, concrete authoring needs, and realistic render trees.

### Phase 7.5: repository release qualification

**Goal:** turn the implemented Phase 7 slice into reproducible release
evidence using work that can be completed in this repository and its CI. This
phase adds quality infrastructure, fixtures, host coverage, package checks,
and user-facing examples. It does not add another required component family or
change the publishing architecture.

Phase 7.5 is distinct from manual release qualification. Repository automation
can prepare screen-reader scripts, visual candidates, and real-device task
lists, but it cannot honestly approve visual design, verify announcements from
assistive technology, or claim behavior on hardware it did not run. Those
results remain explicit human release records, not simulated passing tests.

Phase 7.5 follows a bounded evidence budget. Each automated profile names the
release decision it protects, the failure threshold that would change that
decision, and the smallest representative scenario set that can exercise it.
Pull requests run deterministic correctness, one Chromium accessibility and
interaction profile, docs synchronization, asset budgets, and wheel inventory.
Broader browser, visual, host, and scaling profiles run on a schedule or for a
release candidate only after their harness is stable. A local exploratory run
stops within five minutes unless a concrete failure requires a narrower
follow-up. Adding another state, browser, viewport, host, or instance count is
not useful by itself: the addition must protect a distinct decision that the
existing sample cannot make.

The scenario catalog uses pairwise and boundary coverage rather than a
Cartesian product of every state and environment. Metadata can enumerate the
full supported state contract while one scenario exercises several compatible
states. A component specification remains the source of the complete contract;
the catalog records which representative scenario supplies evidence for each
part of it.

#### Component-owned files and package boundary

Phase 7.5 groups files by the component family a maintainer changes. The target
layout is:

```text
packages/py/citry_ui/
  citry_ui/components/
    ctabs/
      __init__.py
      ctabs.py
      README.md
      api.md
      api.yml
      tests/
        e2e/
  citry_ui/quality/
    scenarios.py
    routes.py
    tools/
```

The family directory owns runtime code, focused internal notes, public docs
source, component scenarios, and focused tests. Shared scenario types, route
hosting, tool adapters, composed workflows, and cross-family checks live once
under `quality/`. The package catalog remains
`citry_ui/components/__init__.py`; a component author does not edit registration
plumbing.

Only `__init__.py`, the runtime module, shared runtime helpers, and `py.typed`
belong in the wheel. Setuptools excludes family `tests/` and quality tooling,
and package data does not include `README.md`, `api.md`, `api.yml`, screenshots,
reports, or fixtures. The wheel qualification check inspects the built artifact
and rejects those paths. This is an enforced package boundary, not a
convention.

Each family owns two authoritative public documentation sources. `api.md`
contains explanation and task-oriented examples. `api.yml` contains the
complete structured reference for every component in the family: server
inputs, client inputs, slots and slot data, callbacks and native events, public
selectors, reflected attributes, public CSS variables, and named interfaces as
applicable. Whole-family semantics, keyboard, focus, forms, and lifecycle
behavior belong in the explanatory guide. The docs builder validates the YAML
schema, generates the fixed reference hierarchy and tables, and appends them to
the guide.
The docs catalog maps the combined result directly to
`/ui-library/components/<slug>/`; the static builder and development server
read the authoritative files without a second copy under
`docs_site/content/`. A docs guard reports a missing or invalid source.

The explanatory half follows reader priority rather than the implementation
layout. Lead with the smallest valid composition, then the most common
configuration and controlled-use tasks. Move nesting, alternate interaction
modes, environmental behavior, and other specialized cases later. Keyboard,
focus, and semantics that apply to a compound family as a whole belong in this
explanatory half rather than under one component's API entry.

The API-reference half uses this categorical hierarchy when applicable:

1. **Inputs**, split by component and explicitly named **server inputs** or
   **client inputs**. Every server subsection says that values are passed
   through `<c-CXyz />` or `CXyz(...)`; every client subsection says that
   values are passed through `$c-props="{ ... }"`.
2. **Slots**, split by owner component. Each row shows the complete inline data
   shape and links a named type to **Interfaces** when one exists.
3. **Events**, split by owner component. Callback inputs such as
   `onValueChange` are event entries even though `$c-props` carries them;
   native DOM events are identified separately. Event rows define signature,
   trigger, timing, payload, controlled behavior, and cancellation.
4. **Methods**, with one row per imperative surface. Write `-` when the family
   exposes no methods.
5. **CSS**, split by the component that reads each variable. State where a
   variable should be applied and do not imply that a descendant reads a
   root-scoped variable independently. Each row records its accepted value
   kind, purpose, and current fallback or fallback derivation.
6. **Attributes**, split by rendered component. This name covers supported
   reflected `data-*` values and identity hooks. Do not call them "state
   attributes", because Citry State means server event-handler state. Explain
   before the tables that attributes are read-only CSS and inspection output,
   not configuration inputs.
7. **Selectors**, split by component. Document the exact
   `[data-citry-ui-part="..."]` selector, element, and purpose. Public docs use
   "Selectors" because these are attribute selectors, not Shadow DOM
   `::part()` selectors; the internal anatomy may still call each marker a
   part.
8. **Interfaces**, containing every public alias and data shape referenced by
   earlier rows, including explicit fields for non-empty slot data and an
   explicit empty signature for empty data.

Reference rows remain understandable without following a link. When an input
uses a public alias, its Type cell shows the complete inline expansion and a
link to the alias under **Interfaces**. Interface links provide a stable target
and reusable definition; they do not hide the type needed to read the row.

Keep the reference categorical and terse. Routine contract detail belongs in
table rows. Longer behavior that applies across components or explains an edge
case belongs in the guide, preferably beside the task it affects or in a short
admonition. Avoid trailing prose below a table when the same rule fits in its
rows or in the category introduction.

Omit empty per-component subsections. If a top-level category has no entries
for the whole family, write `-` and do not enumerate every component that lacks
the surface.

Every table and entry in `api.yml` receives a stable kebab-case ID. The docs
renderer derives anchors for individual inputs, slots, events, methods, CSS
variables, attributes, selectors, interfaces, and interface fields from those
IDs. A reader can link directly to one contract entry without relying on an
auto-generated table or heading ID. Released IDs do not change. The optional
selector-entry `anchor` field exists only to retain an already published
noncanonical anchor during migration. Explanatory copy appears before the
table it qualifies, not after it.

The cross-family contract test compares every implementation's exact public
variables, selector markers, and reflected attributes with both its production
specification and public reference. It also locks the 20-section specification
shape, public-variable resolution through private fallbacks, and the template
ordering that keeps an owned selector marker after consumer attribute spreads.
Adding or removing a reflected attribute requires updating this explicit
inventory, so a runtime-only public surface cannot ship accidentally.

Citry UI is a top-level docs area with grouped navigation; Components is one of
its groups. Component pages do not use `/examples/` for either their public
route or their embedded presentation. Complete reader-facing modules live in
the owning family's `snippets/` directory. Use `<c-ui-demo>` when a
build-rendered result should precede a source disclosure; use `<c-live-code>`
for source-first teaching. The local authoring server adds a lazy **Try live**
workspace to `<c-ui-demo>` using its workspace `citry-ui` wheel. Deployed
component pages omit that action until the published wheel is installed in the
committed browser runtime. Repository-only snippet directories are excluded
from the wheel.

#### 7.5.1 Shared state catalog and standalone routes

Create one reusable Python scenario source for every frozen state and
meaningful state combination. Playwright, axe, screenshots, Lighthouse, Nu
HTML, and host fixtures should consume the same composition and data instead
of maintaining tool-specific copies. Reader-facing docs snippets remain
task-shaped modules that use only public package imports, so they do not import
repository-only quality tooling; their behavior must still be covered by the
corresponding shared scenario.

The catalog must include:

- Button variants, intents, sizes, loading positions, disabled state, slots,
  and native action types;
- Field/Input required, disabled, read-only, invalid, described, controlled,
  uncontrolled, reset, and native constraint states;
- Form native-valid, native-invalid, attempted, disabled, read-only,
  submitting, dynamic-membership, external-control, reset, and native
  submission states;
- Tabs orientation, activation, direction, loop, density, variant, disabled,
  long-label, nested, controlled, reordered, and removed states;
- Dialog open, closed, controlled, persistent, nested, long-content, form,
  removed-trigger, and removed-open states;
- Combobox local, remote, open, selected, empty, loading, failed, aborted,
  stale, disabled, read-only, invalid, and form-reset states;
- Table normal, empty, loading, error, dense, striped, hover, sticky,
  overflowing, large-output, reordered, edited, and removed-row states;
- the repeatable contact workflow and both representative composed pages; and
- light, dark, RTL, forced-colors, reduced-motion, narrow, touch-emulated, and
  zoom profiles wherever they affect the component.

Every scenario declares its stable ID, purpose, supported states, fixture
data, expected assets, safe standalone status, and applicable quality tools.
State setup belongs to the Python scenario or an explicit browser action, not
to hidden test-only markup. Standalone routes include complete document
metadata so page-level tools audit a realistic page.

**Acceptance:** a registry test proves unique IDs and deterministic ordering;
every supported public state maps to at least one scenario; standalone and
embedded rendering agree on markup, assets, semantics, and behavior; and no
catalog import requires Node, a host framework, network access, or a running
server.

#### 7.5.2 Automated accessibility and semantic contracts

Expand the representative-page axe smoke test into per-state coverage. Each
visible state is activated before scanning, including open overlays, visible
errors, remote failures, loading status, empty collections, and content after
Events replacement. Hidden DOM does not count as coverage of an open state.

For each scenario, combine axe with focused assertions for:

- roles, accessible names, descriptions, errors, and referenced IDs;
- expanded, selected, disabled, invalid, busy, modal, and live-region state;
- landmark, heading, form, list, table, and dialog structure;
- DOM and accessible order after add, remove, reorder, open, close, and morph;
- keyboard focus, roving `tabindex`, `aria-activedescendant`, restoration, and
  escape paths; and
- duplicate IDs, dangling references, and relationships after repeated render.

Store compact accessible-structure snapshots only for intentional public
relationships. Do not snapshot incidental wrappers or private class names.
Axe `incomplete` results receive an explicit disposition with a linked manual
task; broad rule exclusions are not accepted as fixes.

**Acceptance:** zero serious or critical axe violations; every incomplete
result is owned and explained; all APG and native keyboard cases pass in the
supported browser matrix; and every public semantic relationship has a focused
assertion that fails when the relationship is broken.

#### 7.5.3 Visual and environmental regression profiles

Build Playwright screenshot profiles from the shared scenarios. Pin browser,
operating environment, fonts, device scale, viewport, animation policy, and
color scheme. Record both the pixel threshold and the maximum differing-pixel
ratio. Mask only content proven to be nondeterministic.

The initial matrix covers:

- default light and dark schemes;
- both Orbit and Ledger brand adaptations;
- every public variant, size, density, state, and slot-backed anatomy;
- focus-visible, hover, active, disabled, loading, invalid, empty, and error;
- horizontal and vertical Tabs, RTL, long labels, and overflowing Table;
- Dialog backdrop, nested scope, long content, and narrow viewport;
- 200 and 400 percent zoom-oriented layouts;
- reduced motion and forced colors; and
- desktop, narrow mobile viewport, and touch-emulated input.

Automated work can generate candidate baselines, prove deterministic output,
and enforce future diffs. Maintainer approval of the initial images and an
independent review of hierarchy, typography, spacing, color, responsiveness,
and consistency remain human release tasks.

**Acceptance:** every frozen visual state has a deterministic candidate
baseline; subsequent CI runs remain within the 0.1 percent differing-pixel
budget; there are no unexplained masks or platform-dependent fonts; and the
review ledger distinguishes approved, rejected, and awaiting-human-review
images.

#### 7.5.4 Complete-page HTML and Lighthouse validation

Run the Nu Html Checker against rendered standalone routes rather than source
templates. Validate the default and composed pages, every component state that
changes structure, and output after representative Events replacements.
Diagnostics must name the scenario and preserve the rendered artifact for
inspection.

Add Lighthouse CI for the public-site form and dashboard. Use a pinned Chrome
profile, at least three runs per page, explicit resource budgets, and source-
controlled assertions. Require an accessibility score of 100 for these
controlled first-party fixtures while treating that score only as a regression
smoke test. Track performance, best-practice, LCP, CLS, and interaction
findings diagnostically without claiming the library alone guarantees Web
Vitals.

**Acceptance:** zero Nu HTML errors caused by Citry UI; Lighthouse
accessibility is 100 on both representative pages; resource budgets pass; run
variance and configuration are recorded; and generated reports are available
as CI artifacts without becoming package contents.

#### 7.5.5 CSS coexistence and customization proof

Test the actual pinned compiled output of Bootstrap and Tailwind, including
Tailwind's reset, rather than a small hand-written imitation. Exercise each
stylesheet before and after Citry UI to make cascade-order assumptions visible.
Plain CSS remains the control profile.

The fixtures verify native controls, Button, Field/Input, Form, Tabs, Dialog,
Combobox, and Table in each environment. They assert semantics and computed
styles for layout, visibility, box sizing, typography inheritance, focus,
disabled state, overlay backdrop, popup stacking, and responsive overflow.
Orbit and Ledger continue to prove customization using documented variables
and parts only.

**Acceptance:** components remain operable and legible in plain CSS,
Bootstrap, and Tailwind profiles; no fix requires `!important`, a private
class, a private data marker, or a private variable; selector specificity
stays within the frozen budget; and any required reset or cascade-layer order
is documented as public installation behavior.

#### 7.5.6 Performance, scaling, assets, and cleanup

Extend the existing Brotli asset and local interaction tests into reproducible
route and scaling profiles. Measure a control page and subtract Citry, Alpine,
Events, and host costs before attributing incremental work to Citry UI.

Record:

- raw, gzip, and Brotli bytes per family and for representative routes;
- asset request count, duplicate registration, and fragment insertion;
- initialization and first interaction over thirty runs in pinned desktop and
  mobile-emulation profiles;
- 1, 10, 100, 500, and 1,000 instances where the component contract permits;
- large Table output and the repeatable workflow under add, remove, and
  reorder pressure;
- cold load, warm cache, repeated morph, and fragment activation; and
- retained listeners, observers, timers, requests, scroll locks, component
  roots, and detached DOM after cleanup checkpoints.

Prefer direct counters and browser performance marks over score-only gates.
Profiles that cannot run reliably on every pull request move to nightly CI,
but their thresholds remain executable and versioned.

**Acceptance:** the Phase 7 compressed-asset and p95 interaction budgets pass;
Table remains script-free; inactive Button retains no global resource;
fragment insertion executes each family asset once; cleanup returns every
tracked resource to baseline; and scaling results have an explicit threshold
or a documented diagnostic-only status.

#### 7.5.7 Host integration matrix

Render the same shared scenarios through Django and FastAPI rather than
testing host-specific toy components. Each deep fixture covers registration,
document and fragment assets, native forms, Events, errors, mounted prefixes,
request context, cleanup, and the representative composed pages. Generic ASGI
and WSGI receive smaller smoke coverage for the same core contracts.

Browser assertions should be shared across hosts wherever behavior is meant to
be identical. Host-specific tests remain only for routing, request objects,
middleware, CSRF, static serving, and framework error integration. No adapter
may patch or copy Citry UI component definitions.

**Acceptance:** Django and FastAPI pass the render, asset, form, Events,
fragment, error, and teardown matrix; ASGI and WSGI smoke tests pass; mounted
prefixes and asset URLs are correct; and behavioral differences are either
fixed or documented as host contracts rather than hidden test branches.

#### 7.5.8 Wheel and clean-environment lifecycle

Build the `citry-ui` wheel once and use that exact artifact for all package
qualification. Do not let source-checkout imports accidentally satisfy wheel
tests.

The matrix covers:

- wheel inventory, `RECORD`, license, `py.typed`, modules, and declared assets;
- clean `uv add` and `pip install` environments;
- the lowest and highest currently testable Python and compatible Citry
  versions;
- offline installation from a prepared wheelhouse;
- import and render with no Node executable, network access, Django, or
  FastAPI installed;
- reinstalling the same wheel, replacing a local candidate wheel, and clean
  environment uninstall;
- confirmation that uninstall removes `citry_ui` while leaving `citry`
  importable; and
- registration, two-engine isolation, collisions, rollback, introspection,
  assets, and a browser smoke test from the installed artifact.

Upgrade and downgrade between multiple published `citry-ui` releases cannot
be completed before those releases exist. Phase 7.5 supplies the reusable
harness and tests every currently available local and published artifact; the
multi-release result remains a future release record.

**Acceptance:** the built wheel is self-contained and deterministic; clean and
offline installs work; runtime performs no build or download; uninstall is
isolated; installed-artifact browser smoke passes; and the deferred
multi-release cells are named as unavailable rather than counted as passing.

#### 7.5.9 Public docs live examples

Add one polished docs live example for each production family, plus the
repeatable workflow and representative compositions. Examples use only public
imports, registration, tags, kwargs, slots, callbacks, variables, parts, and
native browser behavior. They must not import test helpers or private
component modules.

Each family documentation demonstrates:

- installation with `uv add citry-ui` and explicit library registration;
- direct template usage and imported Python composition where useful;
- common configuration, slots and slot data, callbacks, native events, forms,
  validation, and controlled or uncontrolled state as applicable;
- public theme variables, parts, light/dark ownership, and one focused brand
  override;
- no-JavaScript behavior and the interactions that require Citry's client
  runtime; and
- accessibility expectations, known limitations, and links to the exact
  component contract.

The examples share scenario data where that improves fidelity, but their copy
and explanation are edited for readers rather than exposing internal research
terminology. Playground auto-install and auto-registration wait for a
published compatible wheel; the docs can use the workspace package in the
meantime.

**Acceptance:** every public family has a rendered and tested live example;
all snippets execute in CI; examples pass relevant axe, HTML, browser, and
asset checks; public links resolve; and no example relies on Storybook, Node at
runtime, a private selector, or unpublished behavior presented as stable.

#### 7.5.10 CI organization and exit record

Wire fast deterministic checks to pull requests, the full browser, visual,
host, and scaling matrix to nightly CI, and clean-wheel plus release reports to
release-candidate workflows. Cache browsers and toolchains without caching
rendered success. Upload rendered HTML, axe details, screenshots, Lighthouse
reports, traces, and package inventories only when useful for diagnosis.

The Phase 7.5 exit record contains:

- a machine-readable list of scenarios and applicable quality profiles;
- exact tool and browser versions;
- passed automated gates and links to CI artifacts;
- open axe incomplete results and manual-task owners;
- candidate visual baselines awaiting or carrying human approval;
- unavailable real-device, assistive-technology, and multi-release cells;
- known limitations with a release decision; and
- the evidence that supports each Phase 8 contract recommendation.

**Repository gate:** all applicable automated scenarios pass with no silent
skip, generated artifacts are current, budgets pass, and any unavailable cell
is explicitly excluded from the automated claim. The broader release remains
blocked on the separately recorded visual approval, manual keyboard and
assistive-technology tasks, real Safari/mobile samples, and independent design
review.

#### Phase 7.5 implementation record

Repository implementation status through 2026-08-09:

- component families co-locate runtime code, maintainer notes, public docs
  source, reader-facing snippets, family scenarios, and focused browser tests
  under `citry_ui/components/c*/`;
- the docs catalog publishes every authoritative family source under the
  top-level `/ui-library/components/` area. Every family page owns a
  public-import-only live module. Its `api.md` teaches component use, while
  schema-validated `api.yml` data generates the categorical Inputs, Slots,
  Events, Methods, CSS, Attributes, Selectors, and Interfaces reference. The
  renderer derives stable entry anchors and the docs guard enforces the direct
  source-to-route contract. All thirty-one families in this dated slice have complete
  feature-by-feature preview catalogs;
- the Field/Input pass retains a separate relationship owner and native Input,
  makes Field authoritative for composed state, makes Form-disabled state
  dominant, enforces exactly one control across library and custom content,
  supports unnamed client-only inputs, uses `sm`, `md`, and `lg` visual sizes,
  and preserves native character-width `size` through `attrs`. Its twelve
  tidepool examples cover composition, configuration, variants, layout,
  states, forms, controlled values, native types, custom controls, direction,
  and theming;
- the Form pass keeps the browser as the complete validity, membership,
  submission, reset, and `FormData` authority; exposes direct native routing
  inputs; shares only disabled and read-only descendant configuration; uses a
  private first legend to close the disabled-fieldset exemption; guards later
  submits without disabling successful controls; and has twelve observatory
  examples covering configuration, native validation, reset, submitting,
  multiple submitters, external ownership, server errors, dynamic controls,
  and theming;
- the machine-readable catalog in this dated slice had thirty-four ready routes: all thirty-one
  component families, the repeatable contact workflow, and the Orbit and Ledger
  compositions. Embedded and complete-document renders are checked for the
  same normalized component markup;
- the bounded Chromium profile scans every route before and after one
  representative action. Serious and critical axe violations fail the run,
  while the two observed incomplete rule classes have source-controlled
  dispositions tied to manual tasks;
- Tabs and both representative compositions run against pinned Bootstrap and
  compiled Tailwind output on both sides of Citry's CSS. Focused tests also
  prove public variables and selectors through computed styles;
- `capture_visuals.py` creates pairwise light, dark, narrow, RTL,
  reduced-motion, forced-colors, touch, and 200- and 400-percent-reflow
  candidates with pinned browser metadata and `awaiting-human-review` status.
  Scheduled CI uploads the candidates rather than treating generated pixels
  as approved;
- every ready route is wired through the pinned Nu wrapper in pull-request CI.
  A dedicated Lighthouse profile audits the Orbit form and Ledger dashboard
  three times, requires accessibility and best-practice scores of 100, enforces
  a total byte ceiling, and uploads reports;
- asset tooling records raw, gzip, and Brotli bytes per family and for the
  catalog. Frozen compressed budgets and interaction checks remain the gates;
  the 1, 10, 100, 500, and 1,000 scaling profile is diagnostic and scheduled;
- Django and FastAPI serve both shared compositions and all assets they
  reference. Generic ASGI and WSGI adapters serve the shared Tabs assets;
- CI builds the pure-Python wheel once, checks its exact runtime allowlist,
  installs the same artifact with pip and `uv add` in the lowest and highest
  Python environments, proves offline reinstall and isolated uninstall, and
  runs an installed-artifact Chromium smoke test; and
- `exit_record.py` records exact installed tool versions, scenario metadata,
  profile results, artifact links, axe incomplete ownership, visual-review
  status, unavailable cells, and known limitations without converting
  configured work into a pass. `MANUAL_QUALIFICATION.md` defines the bounded
  visual, keyboard, assistive-technology, and real-device sessions referenced
  by that record.

The repository implementation does not complete the human release record.
Initial visual candidates still need maintainer approval and independent design
review. Keyboard scripts need manual assistive-technology runs, and real
Safari, mobile hardware, touch, zoom, and high-contrast samples remain
unavailable until somebody runs them. The first hosted Nu, Lighthouse, and
clean-wheel CI artifacts remain pending until these workflow changes run.
Multi-release upgrade and downgrade evidence remains unavailable until at least
two `citry-ui` releases exist. Localization is now tracked in
[`i18n.md`](i18n.md); headless counterparts remain separate follow-up work.

### Phase 8: decision and v1 roadmap

**Goal:** freeze the production component contract from Phase 7 evidence and
define the public v1 product.

The provisional
[component inventory](ui_component_inventory.md) advances the candidate
ledger, dependency order, and source-development batches while release
qualification waits. Its completed third batch contains Divider, Avatar,
Skeleton, ButtonGroup, Toggle, Pagination, and List, each with runtime, public
docs/reference, previews, focused automation, quality/scaling wiring, and wheel
qualification. It is input to this phase, not the final contract or release
commitment.

**Outputs:**

- production contract decision record, including parked alternatives and
  falsifiers;
- the product-facing compatibility, extension, and release commitments around
  the implemented Python publishing, composition, and per-Citry class-access
  contract;
- v1 component inventory and dependency order;
- a component-specification template requiring focused ecosystem research and
  explicit inputs, static and dynamic slots, slot data, slot fallback and
  collision rules, callbacks, exceptional custom events, states, semantics,
  keyboard and focus behavior, parts, variables, browser behavior, and
  acceptance tests;
- component, package, asset, browser, and accessibility work packages;
- semantic-versioning policy for names, kwargs, slots, emitted markup, CSS
  tokens and classes, JavaScript hooks, and accessibility-driven DOM changes;
- documentation support policy over the Python-owned scenario catalog,
  including docs live examples and standalone routes for complete-page
  quality work; optional Storybook support remains a separate extension;
- playground integration after publication: pin the compatible `citry-ui`
  wheel, register it after each playground registry reset, allow `citry_ui`
  imports, and resolve direct library-component final expressions;
- the research-backed [`i18n.md`](i18n.md) migration contract for component
  text, locale selection, formatting, direction, extraction, delivery, and
  locale-sensitive controls. Its Phase 3 plan freezes the shared compiler
  contract, hardens locale transactions, adds checked `$c-tr` records and the
  `i18n.bind()` browser manager, then gates fragment activation on current-locale
  preparation before Citry UI migrates reactive component strings;
- release, compatibility, and maintenance policy.

**Gate:** independent adversarial review of the prototype-backed decision
before implementation dispatch.

The timing remains deliberate: the released `citry-ui 0.1.0`, `citry 0.4.0`,
and `citry_core 1.5.0` artifacts support production component work.
Production component work proceeds through specifications, docs live examples,
standalone scenarios, and direct quality tools. Storybook may later add an
optional contributor previewer, but it is not an entry gate. No separate
custom gallery is planned unless a concrete need remains after using the docs
site and evaluating the optional Storybook extension. Later stabilization
still needs the released-artifact compatibility matrix.

The post-third-batch review has resolved and implemented Grid and Container.
The research pass for Menu, Tooltip, Popover, Drawer, and Toast is complete in
[`ui_overlay_foundations.md`](ui_overlay_foundations.md). It found that the
group does not need one monolithic public Overlay: anchored positioning,
dismissible-layer ordering, focus/modality, presence, physical context, and a
Toast host are distinct capabilities. The disposable Chromium, Firefox, and
WebKit [prototype pass](ui_overlay_foundations_spikes/prototype-report.md)
ratifies the platform-first hybrid with native manual Popover and CSS anchors,
a bounded private dismissal/presence controller, no default teleport, native
Dialog for modal Drawer, and a separate Toast host. The shared architecture
gate is cleared for one-family-at-a-time work. Popover has completed its
production implementation pass: authoritative specification, runtime and
exports, structured API, nine public previews, focused server and
Chromium/Firefox/WebKit evidence, retained-rerender coverage, reusable quality
and scaling routes, docs projection, and exact wheel qualification. Its human
visual/assistive-technology and independent review remain release evidence.
Tooltip has also completed its production pass: authoritative specification,
runtime/exports, structured API, ten public previews, focused server and
Chromium/Firefox/WebKit evidence, retained-rerender coverage, quality/scaling
wiring, docs projection, and exact wheel qualification. Its human
visual/assistive-technology, hosted Nu, and independent review remain release
evidence. Menu completed its production pass and independent implementation
review: the eight-class runtime/export family, structured API, thirteen public
previews, focused three-engine evidence, correlated-rerender coverage,
quality/scaling wiring, docs projection, and exact wheel qualification are
checked in. Modal Drawer/Sheet and Toast subsequently completed their
source-development passes, as recorded in the active inventory. Number, date,
time, and advanced range controls may now enter family research against the
implemented core i18n contracts. Each family still ratifies its own browser
editing, stepping, calendar/time-zone, direction, and server/browser agreement;
a generic browser temporal parser is not an entry gate.

## 5. Evaluation rubric

The product charter freezes the rubric before the breadth scan:

| Criterion | Weight |
|---|---:|
| Accessibility correctness | 20 |
| Fit with Citry's server and client model | 20 |
| Configuration and customization depth | 15 |
| API consistency and composition | 15 |
| Useful default visual design | 10 |
| General-purpose component coverage | 10 |
| Asset and runtime cost | 5 |
| Maintenance, licensing, and upgrade story | 5 |

Scores organize evidence. They do not mechanically select a library to copy
or an architecture to adopt. The charter's accessibility, security, browser,
host, installation, and content-trust floors are pass/fail gates rather than
weighted trade-offs.

## 6. Falsifiers and response rules

Each quantitative threshold is set before the relevant prototype. A failure
must change the plan rather than receive a favorable explanation afterwards.

| Evidence | Response |
|---|---|
| Accessible composite controls require a second client framework | Narrow the first release or choose a different behavior architecture. |
| Common compound APIs cannot be expressed through Citry's component and slot contracts | Redesign the public composition model before building breadth. |
| Morphing breaks focus, edits, overlay identity, stale-result guards, or cleanup | Hold the affected component family until the lifecycle contract passes. |
| Two distinct brand themes require undocumented selector overrides | Strengthen the token/part contract before expanding the catalog. |
| Static visual primitives activate substantial client machinery | Split static and interactive paths before expanding the inventory. |
| Clean installation, registration, upgrade, or rollback cases fail | Simplify the distribution and registration contract or hold the release until its lifecycle is explicit. |
| The prebuilt assets exceed the agreed payload or interaction budgets | Split delivery, reduce runtime work, or narrow the first release. |
| The suite cannot cover common application UI without another generic library | Expand the staged roadmap or revise the product claim explicitly. |

## 7. Research artifacts

Research lives under [`ui_research/`](ui_research/):

```text
ui_research/
  README.md
  product-charter.md
  citry-baseline.md
  local-prior-art.md
  candidate-map.md
  recon-<library>.md
  complaint-register.md
  component-taxonomy.md
  customization-patterns.md
  citry-fit-matrix.md
  architecture-options.md
  scenario-catalog.md
  prototype-report.md
  decision-record.md
```

Every report records its snapshot date, versions, sources, confidence, and
unresolved evidence. The README remains the status and routing index.
Current family status and batch order live in
[`ui_component_inventory.md`](ui_component_inventory.md); the Phase 5
taxonomy remains the dated ecosystem evidence behind it.
