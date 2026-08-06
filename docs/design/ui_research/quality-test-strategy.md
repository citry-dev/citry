# Quality test strategy for Citry UI

**Snapshot: 2026-07-24. Status: verification strategy for the research and
prototype gates.** This document turns the product charter's quality floors
into tests. Phase 7's initial quantitative budgets are frozen in
[`architecture-options.md`](architecture-options.md#12-quantitative-budgets-frozen-for-phase-7).
A change requires a recorded decision before prototype implementation begins.

The central rule is that no single score establishes component quality.
Static analysis, browser automation, manual interaction, assistive technology,
visual review, and real host integration find different defect classes.

## 1. Recommended test stack

| Layer | Recommended tool or method | What it establishes | What it cannot establish alone |
|---|---|---|---|
| Python API | pytest, type-check fixtures, introspection snapshots | Typed kwargs and slots, registration, access to the exact installed class, rendering, metadata, error contracts | Browser behavior or appearance |
| HTML validity | Nu Html Checker in batch mode | Invalid HTML, SVG, and structural mistakes in rendered fixtures | Correct accessibility semantics or interaction |
| Browser interaction | Playwright projects | Keyboard, pointer, touch emulation, focus, forms, overlays, morphing, cleanup, browser differences | Screen-reader usability or visual quality by itself |
| Automated accessibility | `@axe-core/playwright` in each exposed state | Common WCAG and ARIA violations in the actual browser DOM | Most workflow, keyboard, focus-order, announcement, and cognitive issues |
| Accessible structure | Playwright ARIA snapshots plus role/name/state assertions | Stable accessible names, roles, hierarchy, and exposed state | Whether the interaction is usable with assistive technology |
| Whole-page audit | Lighthouse CI on representative compositions | Regression signal for accessibility, performance, best practices, and page-level issues | Component completeness or WCAG conformance |
| Keyboard review | Scripted key tables plus manual walkthroughs | APG key behavior, focus order, focus visibility, restoration, escape paths | Screen-reader announcement quality |
| Screen readers | Manual task scripts on representative browser/AT pairs | Announcements, reading order, forms mode, live regions, virtual cursor, actual task completion | Every browser and AT combination |
| Visual regression | Playwright screenshots in pinned environments | Unexpected layout, theme, responsive, state, and browser rendering changes | Whether an intentional design is good |
| Visual design review | Human review against frozen principles and composed pages | Coherence, hierarchy, density, feedback, polish, and cross-family consistency | Mechanical regression protection |
| Performance | asset-size scripts, browser traces, Lighthouse CI, scaling harnesses | Transfer cost, startup, interaction cost, DOM/root scaling, regressions | Real-user performance without field data |
| Security | unit and browser threat fixtures, escaping assertions, dependency and license scans | Safe default text/URL/attribute behavior and known component threats | Complete application security |
| Packaging | clean pip/uv environments and wheel inspection | Install, upgrade, downgrade, uninstall, assets, offline use, compatibility | Runtime behavior without host fixtures |

The [Nu Html Checker](https://github.com/validator/validator) supports local
batch validation of HTML, CSS, and SVG. Playwright documents both
[axe integration](https://playwright.dev/docs/accessibility-testing) and
[ARIA snapshots](https://playwright.dev/docs/aria-snapshots). Its own guidance
states that automated accessibility checks must be combined with manual
assessment and inclusive testing.

## 2. How Lighthouse should be used

Lighthouse is useful, but not as the primary component accessibility test.
The official [Lighthouse overview](https://developer.chrome.com/docs/lighthouse)
describes page-level audits for accessibility, performance, best practices,
and related concerns. Its accessibility score is a weighted result from the
audits it can automate; manual audits do not contribute to that score
([scoring documentation](https://developer.chrome.com/docs/lighthouse/accessibility/scoring/)).

Recommended use:

1. Run Lighthouse CI against complete representative pages, not isolated
   fragments that lack page language, landmarks, headings, and navigation.
2. Require an accessibility score of 100 for those controlled fixtures. Any
   automatically detectable defect in first-party examples is actionable.
3. Treat 100 as "no issue found by this audit," never as an accessibility
   certification.
4. Keep explicit Lighthouse CI assertions and resource budgets in source
   control. Run several samples for variable performance metrics. Lighthouse
   CI supports per-audit assertions, resource budgets, repeated runs, and
   regression tracking
   ([official configuration](https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md)).
5. Use Lighthouse best-practice and performance findings as diagnostic input.
   Component-specific behavior still belongs in Playwright and manual tests.

## 3. Accessibility verification

### 3.1 Automated checks for every component state

Use axe through Playwright on the real rendered component. Axe reports that
automation finds only part of WCAG issues and returns uncertain cases for
manual review ([axe-core project](https://github.com/dequelabs/axe-core)). Its
API also checks only rendered content, so hidden dialogs, menus, tabs, and
validation messages must be opened or activated before each scan
([axe API guidance](https://github.com/dequelabs/axe-core/blob/develop/doc/API.md)).

Every component fixture should scan at least:

- default, hover, focus, active, disabled, loading, invalid, and read-only
  states that the family supports;
- every open overlay or disclosure state;
- empty, one-item, many-item, selected, and no-result collection states;
- light, dark, high-contrast or forced-color, and both text directions;
- every semantic element choice, such as Button rendered as `button`, link,
  or form submit control;
- after a fragment insertion and after a server morph while the component is
  focused or open.

Failures and axe `incomplete` results must have explicit dispositions. Broad
selector exclusions and disabled rules are not acceptable permanent fixes.

### 3.2 Roles, names, relationships, and state

Use role-based Playwright locators and compact ARIA snapshots to assert:

- role and accessible name;
- label, description, error-message, and control relationships;
- expanded, selected, checked, pressed, current, disabled, invalid, busy,
  modal, and live-region state where relevant;
- heading, landmark, list, table, and form structure;
- DOM and accessible-tree order after teleport and morph operations;
- stable, unique IDs and valid references after repeated rendering.

Snapshots should describe the intended accessible contract, not the complete
incidental tree. Updating a snapshot requires the same review as changing a
public behavior.

### 3.3 Keyboard contracts

Each interactive family gets a table derived from native HTML and the
relevant WAI-ARIA Authoring Practices pattern. The
[APG keyboard guidance](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)
distinguishes tab movement between components from arrow-key movement inside
composite widgets, and distinguishes focus from selection.

Automated tests should cover:

- forward and reverse Tab order;
- Enter and Space activation;
- arrow, Home, End, Page Up, and Page Down behavior where the pattern uses
  them;
- Escape, outside interaction, and focus restoration for overlays;
- roving `tabindex` or `aria-activedescendant` state after pointer use and
  server morphs;
- disabled-item discovery rules;
- no focus loss when async results arrive or a list is reordered;
- a visible focus indicator that is not obscured by sticky or overlay content.

Manual keyboard scripts must also attempt the complete task without a mouse.
Drag-and-drop components require a single-pointer and keyboard alternative, as
required by [WCAG 2.2 dragging movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html).

### 3.4 Screen-reader matrix

For the highest-risk families (Dialog, Menu, Popover, Tabs, Combobox,
MultiSelect, Tree, DataGrid, Toast, and validation), maintain short task
scripts with expected announcements and focus locations.

Initial release pairs:

- NVDA with Firefox and Chrome on Windows;
- VoiceOver with Safari on macOS;
- VoiceOver with Safari on iOS for touch exploration and form controls;
- TalkBack with Chrome on Android for the mobile interaction set;
- JAWS with Edge or Chrome when testing access is available.

The release record lists exact OS, browser, and assistive-technology versions.
The [ARIA-AT project](https://aria-at.w3.org/about) is useful evidence for
pattern interoperability, but its results do not replace tests of Citry's own
markup and state transitions.

### 3.5 Vision, motion, zoom, touch, and input methods

Playwright can run desktop and emulated mobile projects, light/dark modes,
touch-capable device profiles, disabled JavaScript, locale, timezone, and
offline scenarios
([emulation guide](https://playwright.dev/docs/emulation)). Its context APIs
also support reduced-motion and forced-color media emulation. Use automation
for repeatability and real devices for the release sample.

Required cases:

- `prefers-reduced-motion: reduce`, with no essential information conveyed
  only by animation;
- forced colors, with visible focus, boundaries, selection, and disabled
  states;
- 200% and 400% browser zoom, reflow, text spacing, and long unbroken content;
- narrow and wide responsive layouts;
- coarse pointer and touch targets, long press, scroll, and virtual keyboard;
- IME composition for search, combobox, tags, and validation;
- high pixel density and platform font differences;
- LTR and RTL layout even before the separate localization system exists.

## 4. Visual design and customization

### 4.1 Scenario catalog and live documentation

One [Python-owned scenario catalog](scenario-catalog.md) contains all supported
states, sizes, variants, densities, content lengths, responsive layouts, and
compound configurations. The same authored scenarios feed standalone pages,
docs live examples, axe, interaction tests, screenshots, and design review.

Standalone routes must include complete pages:

- public-site navigation and a call-to-action form;
- account/settings forms with errors and destructive confirmation;
- a dashboard with navigation, filters, dense data, menu, dialog, and empty
  states;
- a server-backed async selection workflow.

The docs site's live-component host is the first-party public preview surface.
It may present deliberate component examples without becoming the quality
runner. Direct Playwright executes interactions, waits, semantic assertions,
screenshots, lifecycle checks, and host comparisons against standalone
scenario routes.

Storybook is an optional contributor previewer tracked in
[`../extensions_storybook.md`](../extensions_storybook.md). If it advances, it
must project Python examples rather than introduce a second authored story
source. Its adapter smoke tests may verify preview mounting, Controls, assets,
and cleanup, but its availability and adapter choice do not gate Citry UI.

Standalone complete pages remain required for Lighthouse, performance traces,
manual keyboard and assistive-technology work, and direct Playwright. They are
quality surfaces, not a separate public gallery. Optional preview-tool
accessibility feedback may supplement the direct quality suite, but the direct
suite remains authoritative.

### 4.2 Screenshot policy

Playwright's `toHaveScreenshot()` stores and compares browser-specific images.
Its documentation warns that OS, browser version, fonts, hardware, and other
environment differences affect rendering
([visual comparisons](https://playwright.dev/docs/test-snapshots)). Therefore:

- generate and compare baselines in pinned CI images;
- keep separate baselines for each tested browser project;
- disable animation and stabilize time, random values, and remote data;
- mask only data that is genuinely nondeterministic;
- freeze tolerances before the prototype and keep them narrow;
- require human approval for every baseline update;
- pair screenshots with semantic assertions so a visually identical broken
  accessible tree cannot pass.

### 4.3 Theme and override tests

Test the default light and dark themes plus two deliberately different brand
themes using documented tokens and parts only. Record:

- tokens changed;
- any selectors or internal DOM knowledge required;
- component states that fail contrast or lose differentiation;
- part and slot overrides that survive a compatible markup revision;
- CSS collisions when loaded with plain application CSS, Bootstrap, and
  Tailwind;
- cascade-layer, specificity, reset, print, and shadow/portal behavior.

Any undocumented selector required for an ordinary brand adaptation is a
prototype failure, not a documentation omission.

## 5. Interaction, server rendering, and lifecycle

Phase 7 runs the behavioral suite against the styled production component.
Historical headless pressure components are outside the release matrix until
real application usage justifies a supported headless API.

Every stateful family should test:

- initial server render with and without browser activation;
- native form submission where applicable;
- Citry Events success, validation failure, transport failure, retry,
  supersession, and cancellation;
- fragment insertion after the initial page load;
- morph while closed, open, focused, editing, composing text, loading, and
  displaying errors;
- removal, cleanup, re-insertion, repeated initialization, and memory/listener
  counts;
- root element, multiple roots, rootless output, nesting, adjacency, slots,
  fallback slots, and teleport;
- stale async results arriving out of order;
- stable item identity during filter, reorder, add, remove, and pagination;
- two instances with the same values but distinct identity;
- no client activation or JS asset for a static-only component.

Theme state uses Citry's implemented client ambient-context contract:
`$provide`, `$inject`, and `$unprovide` plus matching methods available inside
`$component.init()`. Production-family tests must verify logical graph
ancestry, caller-owned slot content, teleports, reactive updates, morph
continuity, defaults, shadowing, cleanup, and diagnostics. DOM-parent walking
is not an allowed substitute because Citry's logical and physical trees can
differ.

## 6. Forms and progressive enhancement

For each form control and composed Form:

- validate label, description, error, required, disabled, read-only,
  autocomplete, name, value, and form-owner behavior;
- submit through ordinary browser form encoding with JavaScript disabled;
- submit through Events with typed scalar, list, nested, boolean, file, and
  repeated values;
- preserve user edits, selection, focus, and errors across rerenders;
- test browser validation and server validation separately;
- test multiple submit buttons, Enter submission, reset, cancel, and pending
  state;
- verify passwords and file contents are not mirrored into diagnostics,
  tokens, URLs, or unsafe attributes.

Not every enhanced composite can work without JavaScript. Its no-JS state
must still provide meaningful content or a documented native alternative.

## 7. Security checks

Security fixtures should cover:

- hostile text in every label, message, result, chip, tooltip, table cell, and
  slot boundary;
- explicit trusted-HTML APIs, including script, event-handler, SVG, URL, and
  malformed-markup payloads;
- URL protocols and external-link attributes;
- attribute mappings that attempt to introduce browser expressions or
  overwrite library-owned IDs and relationships;
- generated ID uniqueness and safe serialization;
- stale or cross-instance async results;
- file names, MIME claims, preview URLs, size limits, and upload errors;
- focus and scroll containment for overlays without trapping the page after
  removal;
- CSP operation within Citry's documented current constraints;
- dependency, license, source-map, and wheel-content scans before release.

Tests establish safe library defaults. Application authorization and server
content sanitization remain application responsibilities and must be clear in
the API documentation.

## 8. Performance and asset budgets

Measure the library's incremental cost rather than attributing the whole page
to it:

- raw, gzip, and Brotli size for aggregate and per-family CSS/JS;
- number of requests and first-use lazy loads;
- parse, compile, startup, and first-interaction time;
- event listeners, observers, Alpine roots, DOM nodes, and retained objects;
- cold page, warm cache, fragment insertion, and repeated morph cost;
- 1, 10, 100, 500, and 1,000 repeated static and interactive instances where
  the family permits it;
- dense table, menu-per-row, and tree scenarios from the production audit;
- a control page without Citry UI so framework and host cost can be
  subtracted.

Lighthouse CI supplies page-level regression checks and resource budgets.
Browser traces and targeted performance marks explain failures. Core Web
Vitals are useful on representative application pages, but a library should
not claim that it alone guarantees them. Current stable metrics are LCP, INP,
and CLS ([Web Vitals](https://web.dev/articles/vitals)).

Freeze budgets from measurements before implementation. A score-only budget
is insufficient because scores and weights can change; retain direct byte,
time, root-count, and allocation thresholds.

## 9. Packaging, hosts, and browsers

### 9.1 Package matrix

Build the wheel once, then test it rather than the source checkout:

- `uv add citry-ui` and `pip install citry-ui` in clean environments;
- lowest and highest supported Citry and Python versions;
- upgrade, downgrade, reinstall, and uninstall;
- offline install from a local wheelhouse;
- wheel inventory, RECORD, license files, type information, templates, and
  deterministic prebuilt assets;
- import without Django, Node, network access, or optional host packages;
- first and repeated registration, two engines, collisions, partial failure,
  rollback, and deterministic introspection.

### 9.2 Host matrix

Use the same rendered fixture and browser assertions through every shipped
Citry host adapter. Django and FastAPI receive the deep matrix. Flask, generic
ASGI, and generic WSGI receive registration, route, asset, fragment, native
form, Events, error, and teardown smoke tests.

### 9.3 Browser matrix

Playwright continuously covers Chromium, Firefox, and WebKit and can run
branded Chrome and Edge channels
([browser documentation](https://playwright.dev/docs/browsers)). Release
qualification also samples real Safari, Chrome Android, and Safari iOS because
emulation is not the same as the branded browser on its native operating
system.

## 10. Suggested CI cadence

### Every pull request

- Python API, schema, render, and introspection tests;
- HTML validation;
- Chromium interaction tests for all changed component states;
- axe scans and accessible role/name/state assertions for every changed state;
- focused screenshots;
- static/no-JS, Events, morph, and cleanup cases affected by the change;
- asset-size and dependency-diff checks.

### Nightly

- full Chromium, Firefox, and WebKit interaction matrix;
- all themes, RTL, forced colors, reduced motion, zoom, touch emulation, and
  responsive fixtures;
- every Citry host adapter;
- the full component-state and standalone composed-page visual matrix;
- scaling, memory, lifecycle, Lighthouse CI, and clean-package matrices.

### Release candidate

- current and previous supported branded desktop browsers;
- real mobile-browser sample;
- manual keyboard scripts;
- representative screen-reader task scripts;
- independent visual-design review;
- two-brand customization review;
- security threat fixtures and dependency/license review;
- clean wheel installation, offline operation, upgrade, downgrade, uninstall,
  and documentation walkthrough by someone who did not author the component.

## 11. Release evidence per component family

A component family is supported only when its dossier contains:

1. public styled component contracts;
2. all supported states and variants;
3. native HTML and APG behavior decision;
4. automated semantic, interaction, accessibility, visual, lifecycle, and
   security results;
5. manual keyboard and assistive-technology results appropriate to its risk;
6. browser, host, no-JS, morph, and form results;
7. asset and performance measurements;
8. documented tokens, parts, slots, attributes, and extension points;
9. known limitations with an owner and release decision.

This evidence, rather than component-directory presence or an individual story
or scenario, defines actual catalog coverage.
