# Plan: the Citry UI component library

**Status (2026-07-24): active research plan. Phases 0 through 6 are complete;
the generic publishing foundation and expanded pressure catalog are
implemented, and the Phase 7 entry program is underway. The comparative
component prototype has not started.** This plan defines the research and
decision process for Citry's official component library. The ratified product
target is recorded in
[`ui_research/product-charter.md`](ui_research/product-charter.md).

The planned Python distribution is `citry-ui`, imported as `citry_ui`. It is a
separate first-party package built on Citry. The styled component surface is
usable without design work, while a matching renderless headless surface gives
authors the same component behavior and binding contract with fully
author-owned HTML and visual design.

Citry's generic library publishing and engine-neutral invocation APIs are now
implemented. This document does not select production component-family APIs,
the v1 inventory, the theme architecture, or the final styled-to-headless
layering. Those decisions follow the ecosystem study and comparative
prototypes. For repository operating rules, see
[`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. Desired outcome

Citry users should be able to build a polished application without first
assembling an unrelated UI stack. The library should be comparable in product
ambition to established suites such as Vuetify:

- styled and useful immediately;
- native to the framework's component, slot, asset, and client models;
- accessible across the supported interaction modes;
- customizable from theme tokens down to headless component behavior;
- broad enough for the common layout, navigation, form, feedback, overlay,
  and data-display needs of an application.

Specialist products such as charts, rich-text editors, maps, and domain-heavy
data grids may remain companion packages. The research decides that boundary
from evidence rather than treating maximum component count as the goal.

## 2. Decisions already made

The maintainer ratified these product decisions on 2026-07-23:

1. The UI library is a separate first-party Python distribution. The leading
   names are the `citry-ui` distribution and the `citry_ui` import package.
2. The default experience is a styled, coherent, batteries-included library,
   not a collection of unstyled primitives.
3. Each component family should also expose a headless version. It renders no
   library-owned HTML and exposes state, native attributes, ARIA relationships,
   handlers, focus targets, and other behavior through required slots or
   parts. The author owns the markup and visual design. The exact packaging
   and API shape remains a research question.
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
covering users, jobs, styled and headless promises, meaning of "default",
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

**Gate:** at least two viable hypotheses advance to the same comparative
prototype. Local-artifact installation, registration, assets, and atomic
rollback have passed. Publication still waits for a released compatible Citry
lower bound and multi-release upgrade, downgrade, and uninstall fixtures.

### Phase 7 entry program: scenarios, Storybook, and browser readiness

Phase 7 does not begin by polishing the current pressure components. Its entry
program establishes the tooling and framework behavior needed to compare
production candidates without accidentally releasing the probes as public
APIs.

The immediate execution order is:

1. Align the research documents and define the Python-owned
   [scenario-catalog contract](ui_research/scenario-catalog.md).
2. Render the same current server-static scenarios through both
   `@storybook/server-webpack5` and `@storybook/html-vite`. This is a
   provisional comparison and does not select the adapter.
3. Run disposable browser-readiness journeys with direct Playwright against
   standalone scenario routes, while previewing the same interactive scenarios
   through both Storybook adapters. Implement and verify client ambient context
   before any proof that depends on nested context, caller slots, or teleports.
4. Select the Storybook adapter from the combined static and interactive
   evidence. Freeze the formal Phase 7 component specifications, scenario set,
   and acceptance fixtures; ratify or revise the already drafted quantitative
   budgets; and confirm the advancing architecture candidates.
5. Implement the same paired slice for both candidates and run conformance,
   accessibility, visual, host, lifecycle, security, asset, and performance
   measurements.
6. Write the Phase 8 architecture decision and v1 roadmap.

Steps 1 and 2 are complete. Client ambient context and the first disposable
reactive-state and asset-readiness slice of step 3 are also complete. The
static and first interactive two-adapter results are recorded in
[`ui_research/storybook-adapter-exploration.md`](ui_research/storybook-adapter-exploration.md).
Both adapters advance and selection remains deferred until the complete
interactive set in steps 3 and 4.

The Python scenario catalog is the source of truth for isolated states and
composed pages. Storybook is the planned maintainer state browser once its
feasibility gate passes. The same catalog also renders complete standalone
Citry pages for Lighthouse, manual keyboard and assistive-technology work,
performance measurement, and direct Playwright tests. Those pages are test
surfaces, not a second gallery product. A custom state-browser UI is considered
only if Storybook fails documented requirements.

The two-stage Storybook comparison uses identical scenario metadata,
rendering, assets, and behavior. The first stage proves the projection and
server-static cases. The second proves that both adapters can preview every
interactive readiness scenario before selection. Storybook does not execute
the Playwright journeys or become a conformance runner. Small adapter smoke
tests may open its preview iframe to verify mounting, asset activation, Control
updates, diagnostics, and cleanup when a story is replaced.

Together the two stages must prove Args and Controls, Citry CSS and JavaScript
activation, Events transport, nested and composed states, accessibility
inspection, deterministic generated stories, and direct standalone links.
Both adapters now use the same-origin `/citry/**` route through a development
or static-build reverse proxy. This route carries scenario HTML, the Citry
runtime, and extension and component assets; later Events scenarios must use
the same route and exercise the host's real security policy. A `postMessage`
bridge remains a fallback for a future sandboxed or cross-origin deployment.
The comparison also records whether a static Storybook build embeds frozen
output or requires a reachable Citry rendering service.

Node may be required for contributor-only Storybook tooling. Installing and
running `citry-ui`, rendering standalone scenarios, and using the component
library in an application remain Node-free.

The current Button, Field/Input, semantic Table, and Tabs catalog contains no
library-owned client interaction. Native controls retain their browser
behavior, but Tabs expresses server-selected semantics only. Before formal
Phase 7 specifications, disposable proofs outside the public `citry_ui`
manifest must exercise:

- reactive component state, browser-local events, and client asset activation
  (proved for the first private counter probe, including Controls replacement,
  delayed and failed readiness, stale-response rejection, basic story
  navigation, exact component cleanup, Alpine disposal, CSS readiness, and
  stale physical-listener disposal);
- a two-phase client activation contract, or a deliberately narrower readiness
  contract, because a hidden connected candidate already runs Citry and Alpine
  initialization and can otherwise affect global listeners, Events, focus,
  teleports, and CSS before promotion;
- focus-preserving fragment insertion and morphing;
- ambient context over logical ancestry, caller-owned slots, nested providers,
  teleports, reactive updates, defaults, and cleanup;
- stateful Tabs with keyboard navigation, focus, activation modes, dynamic
  removal, server replacement, and morph preservation;
- an Overlay/Dialog with teleport, focus trap and restoration, document
  listeners, stacking, outside interaction, and removal cleanup;
- a remote Combobox or MultiSelect with keyboard behavior, loading, request
  cancellation, stale-result rejection, and native form output;
- Form-owned dynamic child registration, unregistration, validation, and
  submission; and
- one composed repeatable-form workflow that combines those behaviors.

An InfiniteScroll observer/async/cleanup proof is optional if the required
cases already expose the relevant lifecycle constraints. Every readiness proof
must also verify activation and cleanup while Storybook switches scenarios.
These proofs may be deliberately plain and short-lived. They do not establish
component names, markup, CSS, or release support.

### Phase 7: comparative vertical slice

**Goal:** test the decisions that are expensive to reverse.

The slice is selected after synthesis and the entry program. Every advancing
architecture implements the same six component-family probes in both styled
and headless forms. Form composition and client ambient context are
cross-cutting workflow and framework probes rather than styled/headless
families. One shared conformance suite must establish that paired components
have the same semantics, accessibility, state, Events, morph, and lifecycle
behavior. The eight required probes are:

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

The styled prototype must also prove the product claim rather than only
technical correctness. Before implementation, the comparison freezes:

- complete fixtures for every supported state, variant, size, density,
  responsive mode, dark mode, RTL mode, and error condition in the slice;
- a representative public-site form and application/dashboard composition
  built without consumer CSS;
- cross-browser screenshot regression with reviewed tolerances;
- independent design review of hierarchy, typography, spacing, color,
  interaction feedback, responsiveness, and consistency;
- two distinct brand adaptations using documented tokens and parts only.

The typed Python prototype uses direct tags and an imported engine-neutral
component invocation from ordinary application code. It also obtains the
ordered `LibraryInstallation` and its exact-definition class lookup for
advanced composition and introspection, exercises the supported extension
mechanism, and verifies that each pair is exposed deterministically.

Before implementation, Phase 7 ratifies or records a revision to the Phase 6
budgets for compressed asset size, first-interaction cost, documented-token
theme coverage, selector overrides, registration failures, lifecycle cases,
visual-regression tolerances, and complete styled-state coverage.

The slice also measures the cost of styled components rendering their headless
variant internally against independent styled/headless implementations that
share behavior without nesting renders. Record server render time, rendered
component count, allocations, output size, and client initialization across
realistic trees. The pressure components do not decide this production
architecture in advance.

### Phase 8: decision and v1 roadmap

**Goal:** select the architecture from evidence and define the public product.

**Outputs:**

- architecture decision record, including rejected alternatives and
  falsifiers;
- the product-facing compatibility, extension, and release commitments around
  the implemented Python publishing, composition, and per-Citry class-access
  contract;
- v1 component inventory and dependency order;
- a component-specification template requiring focused ecosystem research and
  explicit inputs, slots, slot data, events, states, semantics, keyboard and
  focus behavior, parts, variables, browser behavior, and acceptance tests;
- component, package, asset, browser, and accessibility work packages;
- semantic-versioning policy for names, kwargs, slots, emitted markup, CSS
  tokens and classes, JavaScript hooks, and accessibility-driven DOM changes;
- documentation and Storybook support policy over the Python-owned scenario
  catalog, including standalone routes for complete-page quality work;
- a separate follow-up research brief for localization after component text,
  formatting, direction, and locale-selection requirements are concrete;
- release, compatibility, and maintenance policy.

**Gate:** independent adversarial review of the prototype-backed decision
before implementation dispatch.

The timing is deliberate: release core Citry first, then pass the scenario and
Storybook entry gate before broad production component implementation.
Storybook is the planned maintainer state browser, while the Python catalog and
standalone routes remain the framework-native rendering and quality contract.
No separate custom gallery is planned. If Storybook cannot browse, control,
activate, isolate, and reliably clean up realistic Citry scenarios, record the
failure before designing a replacement.

## 5. Evaluation rubric

The product charter freezes the rubric before the breadth scan:

| Criterion | Weight |
|---|---:|
| Accessibility correctness | 20 |
| Fit with Citry's server and client model | 20 |
| Customization and styled/headless pairing | 15 |
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
| Two distinct brand themes require undocumented selector overrides | Strengthen the token/part contract or prefer the headless/source-owned hypothesis. |
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
