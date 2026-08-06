# Product charter: Citry UI

**Status (2026-07-29): product direction ratified and Phase 7 started.** The
generic publishing API is complete. Production work now targets one styled
component library with Vuetify-level configuration, breadth, and browser
interaction. Headless component APIs are parked until real applications and
representative pages provide evidence for their useful shape and cost.
Production component APIs and the exact v1 inventory remain Phase 7 and 8
work. This charter fixes what the library
should accomplish. The implementation and research sequence live in
[`../ui_library_plan.md`](../ui_library_plan.md).

## 1. Mission

Citry UI is the official general-purpose component library for Citry. It lets
a developer build a polished application with components that work naturally
with Citry, look coherent without project-specific styling, and remain deeply
customizable.

The ambition is comparable to established full suites such as Vuetify, not to
a small starter pack. A developer should not need another generic UI library
for the common interface of a product.

## 2. Primary users and jobs

The primary user is a Python web developer building with Citry. They may be
working in Django, FastAPI, Flask, bare ASGI or WSGI, or another host supported
by Citry.

The library should support three ordinary jobs from one coherent system:

1. Public-facing sites with navigation, content, calls to action, responsive
   layout, and accessible overlays.
2. Application interfaces and dashboards with dense forms, filtering,
   navigation, feedback, lists, and tables.
3. Server-backed interactions that combine native HTML forms, local browser
   state, and Citry Events without forcing the author to assemble a separate
   JavaScript application.

The production application in `old-chk.zip` is one evidence source for these
jobs. It does not define the market by itself.

## 3. Meaning of "default"

"Default" means the first-party library Citry recommends, documents, tests,
and uses for its own component examples. It has a stable compatibility and
release policy alongside Citry.

It does not mean that every `citry` installation receives the UI files. The
library is a separate distribution so applications choose its code and asset
footprint explicitly:

```sh
uv add citry-ui
```

The intended distribution and import names are:

```text
Distribution: citry-ui
Import:       citry_ui
```

The documented installation path remains `uv add citry-ui`. Installing the
distribution and registering its component classes into one `Citry` engine
are separate contracts.

## 4. Styled production promise

Every production family provides a coherent, accessible, styled assembly that
is useful without project CSS. The target is the practical product depth of a
suite such as Vuetify: rich configuration, consistent variants and states,
compound composition where warranted, and complete browser interaction for
interactive components. Citry UI does not copy Vuetify's API or require its
Sass-based customization system.

Headless component APIs are not part of the Phase 7 production promise. The
existing renderless pressure components remain research evidence only. Revisit
headless components after the styled library has enough real components and
at least one actual application provides concrete customization needs. At that
point, representative full pages also provide the right basis for measuring
nested rendering, client initialization, and alternative implementation costs.

## 5. Breadth target

The long-term suite should cover the ordinary categories below. Phase 5
produced the staged taxonomy; Phase 8 freezes the exact v1 inventory after the
comparative prototype.

| Category | Expected scope |
|---|---|
| Foundations | Theme tokens, color, typography, spacing, elevation, motion, responsive rules, icons |
| Layout | Container, stack, inline/group, grid, divider, aspect ratio, surface |
| Actions | Button, icon button, link/action variants, toggle controls |
| Forms | Field, label, description, error, input, textarea, checkbox, radio, switch, select, combobox, file and date-oriented controls where justified |
| Navigation | Breadcrumbs, tabs, pagination, menu, navigation groups, application bars and drawers where justified |
| Feedback | Alert, badge, progress, spinner, skeleton, empty state, toast or inline notification |
| Overlays | Dialog, popover, tooltip, dropdown/menu positioning, drawer where justified |
| Data display | Card, avatar, list, table, key/value display, disclosure and expansion patterns |
| Utilities | Visually hidden content, focus handling, presence/transition helpers, responsive visibility |

The success test is practical: common marketing pages, account/settings
flows, CRUD interfaces, dashboards, and forms should not require another
generic component library.

Specialist products such as charts, rich-text editors, maps, diagramming,
domain-specific grids, and media editors may remain companion libraries. Their
absence must not be disguised as complete coverage.

## 6. Native Citry contract

Citry UI should feel like authored Citry rather than a foreign runtime behind
an adapter:

- Python component classes with typed `Kwargs` and `Slots`;
- V3 templates and explicit attribute mappings;
- caller-owned supplied slots and receiver-owned fallback slots;
- `$c-props` and component-tag handlers for client composition;
- the Citry-owned Alpine runtime for local interaction;
- Citry Events for server interaction, forms, loading, and errors;
- Citry asset collection, fragments, morphing, initialization, and
  introspection;
- static components that remain server-only when they need no browser
  behavior.

The library uses public Citry contracts and one Citry-owned browser runtime. It
does not require React, Vue, or a second component framework.

## 7. Customization promise

Customization should form a deliberate ladder:

1. global design tokens;
2. theme variants such as light, dark, density, and brand themes;
3. component variants, sizes, states, and semantic colors;
4. per-instance class, style, data, ARIA, and ordinary HTML attributes through
   explicit component APIs;
5. named slots and documented parts for structural composition;
6. source ownership, composition, or subclassing only where the earlier levels cannot
   express a legitimate product need.

Two distinct brand themes must be achievable through documented tokens and
parts without escalating selector specificity or depending on internal DOM.
Exact thresholds are frozen before the comparative prototype.

## 8. Quality and support floors

### Accessibility

- WCAG 2.2 AA is the target for the supported component states.
- Native HTML semantics are preferred when they meet the interaction contract.
- Composite widgets follow the relevant WAI-ARIA APG keyboard model.
- Automated checks are necessary but cannot establish an accessibility claim
  without manual keyboard, focus, and representative screen-reader testing.
- Forced colors, visible focus, reduced motion, zoom, RTL, touch, and IME
  behavior are part of the acceptance matrix.
- Labels, descriptions, errors, IDs, focus, and edited values must survive the
  supported server-render and morph paths.

### Platforms and hosts

- The initial browser floor is the current and previous stable desktop
  releases of Chrome, Edge, Firefox, and Safari, plus current Chrome on
  Android and Safari on iOS. Each Citry UI release records the exact tested
  versions. Playwright Chromium, Firefox, and WebKit provide continuous
  coverage; representative real mobile and Safari checks remain release
  gates where engine emulation is insufficient.
- Outside the supported window, semantic HTML and native forms should remain
  useful where the component permits progressive enhancement. Unsupported
  browsers do not receive an unqualified interactive-component guarantee.
- Python support follows the compatible Citry release range.
- The component contract remains host-neutral. Django and FastAPI provide the
  deep integration fixtures because they exercise distinct host styles.
  Every host adapter shipped by the compatible Citry release receives
  registration, assets, rendering, forms, and Events smoke coverage. The
  initial matrix therefore also covers Flask, generic ASGI, and generic WSGI.
- Django form adapters may be separate conveniences. Django-specific form
  objects do not define the core component contract.

### Direction and deferred localization

- The initial theme supports explicit inherited LTR and RTL direction. This
  is a layout and interaction requirement, not a complete localization
  system.
- Initial components accept application-supplied labels, descriptions,
  messages, and formatter callbacks through ordinary typed inputs and slots.
  The core library does not freeze translation keys or locale selection while
  its component text inventory is still changing.
- Localization is a separate follow-up design after the component catalog and
  authored-text contracts are stable enough to study. That work should
  evaluate a Citry extension for translation keys, catalog loading, locale
  selection, plural rules, number/date/time formatting, time zones, fallback,
  server/client agreement, and optional locale data.
- Locale-aware date, time, calendar, and number controls do not enter the
  supported catalog until that follow-up defines their parsing, formatting,
  and server/client contracts.

### Security and content trust

- Text, labels, descriptions, messages, remote results, and user-provided
  content are escaped by default. Rendering trusted HTML requires an explicit,
  documented opt-in type or API.
- URL-bearing components define allowed protocols, external-link behavior,
  disabled behavior, and the boundary between library validation and trusted
  application attributes. Unsafe protocols are never introduced by a library
  convenience API.
- Attribute forwarding, generated IDs, inline data, and browser expressions
  use Citry's typed and escaped public contracts. Raw JavaScript strings are
  not a normal component prop channel.
- Async results reject stale responses and expose safe loading, empty, error,
  cancellation, and retry states. File-oriented controls define filename,
  type, size, preview, and upload trust boundaries.
- URL-bearing, HTML-bearing, file, overlay, and async components receive
  component-specific threat cases. Security regressions block release just as
  accessibility regressions do.

### Assets and installation

- Consumer installation and runtime require no Node, Tailwind, Sass, CDN, or
  network download.
- The wheel carries deterministic, prebuilt browser assets.
- Static components do not activate client machinery merely because they are
  part of Citry UI.
- CSS defines an explicit reset, layer, specificity, token, dark-mode,
  density, and RTL policy and is tested alongside application CSS, Bootstrap,
  and Tailwind.
- Icons, fonts, and other assets have an explicit license, attribution,
  loading, and payload policy.

## 9. Hard boundaries

- The library is not a direct Vuetify port. Prior implementations are evidence
  to study, not an architecture to restore wholesale.
- The user does not need a JavaScript application build to consume ordinary
  components.
- A component does not depend on an unbuilt Citry compiler or CSS-scoping
  feature without making that dependency an explicit prerequisite.
- The library does not use Alpine private APIs. Browser behavior uses Citry's
  public component context and managed lifecycle helpers.
- The initial release does not claim specialist coverage that has not been
  designed, tested, documented, and maintained.
- Accessibility and security fixes may require markup changes. The eventual
  semantic-versioning policy must distinguish stable public structure from
  internal DOM that users should not target.

## 10. Evaluation weights

The ecosystem synthesis uses this rubric:

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

Scores organize comparable evidence. They do not select an upstream library
to copy. The accessibility, security, browser, host, installation, and
content-trust floors above are pass/fail gates rather than points a candidate
can trade away for a higher weighted score.

## 11. Product success

Citry UI succeeds when:

- a new project can install it, register it, and render a documented component
  without frontend tooling;
- the styled surface produces a coherent application without project CSS;
- ordinary application categories are covered without a second generic UI
  library;
- customization uses documented tokens, parts, slots, and attributes rather
  than internal selectors;
- server rendering, fragments, morphing, forms, local state, and Events behave
  as one system;
- accessibility, payload, lifecycle, and compatibility claims are backed by
  repeatable tests;
- default content handling is safe without project-specific sanitization
  glue, while trusted-content escape hatches are explicit;
- direction can be changed without forking components, and application text
  remains explicit until the localization extension is designed.

## 12. Decisions the research still owns

- Exact component names and v1 inventory.
- Whether later application evidence justifies a headless surface, and if so,
  which component families and authoring contracts need one.
- Default visual language and theme token schema.
- The separate localization extension, translation-key, catalog, locale
  selection, formatter, and release contracts.
- Release compatibility, multi-release upgrade and downgrade behavior, richer
  family metadata, and whether live uninstall or hot replacement is required.
- Which attributes, slots, markup, CSS variables, CSS classes, and JavaScript
  hooks are semantic-versioning commitments.
- Per-component versus grouped asset delivery.
- Icon strategy and optional specialist packages.
- Production verification of the implemented client ambient-context contract
  for theme, direction, and behavioral defaults through nested, slotted,
  teleported, and morphed components. Later localization work may reuse it.
