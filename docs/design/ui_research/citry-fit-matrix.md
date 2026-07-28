# Phase 5 synthesis: Citry capability fit

**Snapshot:** 2026-07-23; publishing status updated 2026-07-24. **Status:**
complete; independent synthesis gate passed 2026-07-23. This report maps the approved component-library evidence
onto Citry's implemented contracts. It does not select final component APIs or
an implementation architecture.

The product target comes from the [charter](product-charter.md), current
framework facts come from the [Citry baseline](citry-baseline.md), and external
pressure comes from the twelve approved [Phase 4 dossiers](README.md) and the
de-duplicated [complaint register](complaint-register.md). Grade-D reports are
used only as test leads. They do not establish requirements by themselves.

## 1. Outcome

Citry can already support a useful first-party UI package, including static
styled components, typed server inputs, slots, explicit attribute placement,
prebuilt package assets, interactive components over the graph-first Alpine
runtime, native server forms, Events, fragments, morphing, teleports, and
engine-local registration.

It is not yet ready to promise the whole product contract without additional
work. One framework-level gap is release-critical:

1. client ambient context is not public, so reactive defaults, direction,
   portal policy, generated-ID policy, and later localization cannot follow
   logical component ancestry reliably.

Several other gaps are important but do not block comparative prototypes. The
first package can ship namespaced prebuilt CSS without scoped-CSS rewriting,
use classic scripts without ESM, register its manifest through
`app.register_library(citry_ui)`, and document Citry's existing Alpine CSP
limitation. Those are bounded constraints, not reasons to invent a second
client runtime.

The main architecture implication is therefore a split:

```text
Citry core contracts
  ownership, props, slots, Events, lifecycle, assets, server context
                         |
                         v
citry-ui behavior contract
  semantics, state, identity, forms, focus, keyboard, cleanup
                /                     \
               v                       v
       styled templates          headless parts
       tokens and recipes        author-owned markup
```

Both surfaces must use the same behavior and conformance tests. Static families
should stay server-only, while interactive families opt into browser behavior.

## 2. Framework capability matrix

Fit labels mean:

- **Ready:** a live public Citry contract supports the job.
- **Convention needed:** the live contract is sufficient, but `citry-ui` must
  define and test a consistent library-level policy.
- **Core prerequisite:** Citry needs a public framework contract before the UI
  library can promise the behavior.
- **Follow-up:** useful work that is outside the initial architecture decision.

| Product requirement | Current Citry capability | Fit | Consequence for `citry-ui` | Evidence |
|---|---|---|---|---|
| Separate first-party distribution | The uv workspace accepts packages under `packages/py/*`; each package owns the dependencies and files it imports | Ready | Publish `citry-ui`, import `citry_ui`, and depend one-way on a tested Citry range | [Baseline sections 1 and 3](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Component registration | `ComponentLibrary` and `register_library()` provide ordered inert definitions, per-Citry classes, collision preflight, repeat installation, rollback, required extensions, two-engine behavior, and retained-generation checks | Ready; uninstall and live replacement are follow-ups | Publish one explicit manifest and register it before initialization; test the package against the complete publishing contract | [Publishing contract](../component_publishing.md) |
| Typed component inputs | `Kwargs`, `Slots`, template data, JavaScript data, and CSS data are implemented | Ready | Define typed family contracts and keep unsafe JavaScript or trusted fragments visibly separate | [Typed inputs](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Template composition | Named slots, caller/receiver scope, fallback content, and multi-root rendering are implemented | Ready | Compound components and named parts can be native Citry components rather than string templates | [Slots and root shapes](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Attribute forwarding | Components can declare mappings and place them with `c-bind`; generic root fallthrough does not exist | Convention needed | Publish attribute destinations by family and part. Distinguish control, label, input, popup, and container attributes | [Explicit attributes](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Static styled rendering | Server-only components incur no active client graph | Ready | Card, Badge, Alert, layout, typography, structural Table, and similar families should remain useful without JavaScript | [Static cost constraint](citry-baseline.md#2-constraints-the-library-must-design-around) |
| Interactive ownership | Graph-first Alpine owns logical components, roots, regions, slots, placements, and stable browser identity | Ready | Implement behavior through public `$component`, directives, and managed lifecycle, not DOM discovery or Alpine internals | [Client ownership](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Parent-to-child client values | `$c-props` exposes declared reactive values in authored scope | Ready | Controlled state and parent-supplied behavior inputs can cross component boundaries without raw callback strings | [Client props](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| State changes and server actions | Events v1 includes state, bindings, forms, transport, queues, preservation, and conformance | Ready with UI conventions | Define family-level event reasons, cancellation, pending, success, error, and stale-result behavior over Events rather than another transport | [Events](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Server ambient context | `Component.provide()`, `Component.inject()`, and `<c-provide>` reach rendered descendants and slot content | Ready for immutable server values | Server theme name, defaults, direction, and future locale inputs can be scoped during rendering | [Server provide/inject](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Client ambient context | No public `$provide`/`$inject` or `$component` provide/inject contract exists | Core prerequisite | Design one reactive registry beneath author-facing and component-facing access. It must follow logical ownership, not only DOM ancestry | [Client context constraint](citry-baseline.md#2-constraints-the-library-must-design-around) |
| Morph and fragment continuity | Stable graph identity, compatible render revisions, fragment assets, and managed cleanup exist | Ready, high-risk verification | Every interactive conformance suite must rerun across initial render, fragment insertion, compatible morph, replacement, removal, and reconnect | [Ownership and assets](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Portals and teleports | Logical lifecycle covers teleported and mirrored placements | Ready, context prerequisite | Overlay ownership can remain logical, but ambient context, focus restoration, CSS ancestry, direction, and portal roots require explicit tests | [Root shapes](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Stable collection identity | Citry owns stable browser identity, but UI item-value and generated DOM-ID policy are not predefined | Convention needed | Separate logical component ID, collection key, form value, and DOM/ARIA ID. Specify collision and SSR rules | [Client ownership](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Native forms | Events forms and ordinary server handling exist; controls may render native elements | Ready with UI conventions | Prefer native names, values, submit, reset, autocomplete, constraints, and `FormData`; add hidden controls only when rich widgets cannot use a native control directly | [Events and form baseline](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Async behavior | Events owns transport, but client initialization is synchronous | Convention needed | Start async work after readiness, record ownership, cancel on disposal, reject stale results, and never make descendant readiness depend on a Promise initializer | [Synchronous initialization](citry-baseline.md#2-constraints-the-library-must-design-around) |
| Client-created component instances | Alpine conditionals may clone ordinary DOM but cannot instantiate rendered server components | Constraint | Repeatable rich collections either render components on the server or keep client-created rows as DOM owned by one existing component | [Instantiation constraint](citry-baseline.md#2-constraints-the-library-must-design-around) |
| Package assets | Template, CSS, and JavaScript files can be package-relative; the dependency extension deduplicates and loads fragment assets | Ready | Ship deterministic prebuilt plain CSS and classic JavaScript inside the wheel, with family-level dependency declarations | [Assets](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Advanced asset compilation | The asset compiler is unimplemented | Follow-up, not a consumer prerequisite | Maintainers may build source assets before packaging. Ordinary users must not need TypeScript, Sass, JSX, or Tailwind | [Asset compiler constraint](citry-baseline.md#2-constraints-the-library-must-design-around) |
| CSS isolation and theming | Scoped CSS is roadmap work; ordinary package CSS and CSS custom properties work | Convention needed | Use a documented prefix, cascade layers, low specificity, semantic tokens, logical properties, and component tokens. Do not rely on selector rewriting | [Scoped CSS constraint](citry-baseline.md#2-constraints-the-library-must-design-around) |
| Strict CSP | Current standard Alpine expressions require `unsafe-eval`; classic component assets are the live baseline | Known product limitation | Avoid adding new unsafe sinks, inline untrusted style generation, or undeclared remote assets. Do not claim strict CSP until core changes | [CSP and scripts](citry-baseline.md#2-constraints-the-library-must-design-around) |
| ESM and module imports | ESM is parked; classic IIFEs are implemented | Follow-up | Keep the initial browser layer small and library-owned. ESM may improve authoring and splitting later but cannot be required now | [Script baseline](citry-baseline.md#2-constraints-the-library-must-design-around) |
| Catalog and diagnostics | Deterministic introspection and JSON catalog output are implemented | Ready | Expose component modes, parts, assets, schemas, deprecations, requirements, and library version through public metadata | [Introspection](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Host portability | Django, FastAPI, Flask, ASGI, and WSGI integrations serve core routes and assets | Ready with matrix tests | Keep package registration and assets host-neutral; run a reduced smoke matrix outside Django | [Hosts](citry-baseline.md#1-capabilities-the-library-may-rely-on) |
| Localization | Server strings and direction can be authored, but no UI translation contract is selected | Follow-up | Accept author-supplied text and support direction. Defer keys, catalogs, fallback, negotiation, pluralization, and translation extensions | [Charter scope](product-charter.md) |

## 3. Cross-library pressure mapped to Citry

The following rows synthesize repeated mechanisms and grade A through C
shortcomings. Multiple wrappers over one implementation count once.

| Ecosystem pressure | Evidence pattern | Citry response | Failure if omitted |
|---|---|---|---|
| A polished default needs a system, not isolated CSS | Vuetify, PrimeVue, Nuxt UI, Ant, Mantine, Chakra, Bootstrap, and Web Awesome combine tokens, variants, layout, feedback, and utilities | Version semantic tokens, component tokens, state names, part names, variant vocabulary, typography, focus, motion, and density as one product | Users rebuild a design system around nominally “built-in” components |
| Headless flexibility still needs an owned binding contract | React Aria, Base UI, Reka, Ark/Zag, and stable Vuetify v0 own compound behavior; VU-3 to VU-5 show stable headless code can still ship semantic defects | Share state, focus, keyboard, form, ARIA, ID, and cleanup logic, then expose required native bindings to the author-owned headless assembly | Styled/headless drift or undocumented transfer of accessibility obligations to every author |
| Compound parts scale better than monolithic kwargs | Repeated across React Aria, Base/Radix, Reka, Ark, Vuetify v0, and local prior art | Use named roots and parts only where the interaction warrants them; preserve caller slot scope and stable part identity | Unbounded props, inaccessible markup replacement, and brittle descendant selectors |
| Explicit attribute placement is a public contract | Base render composition, React Aria slots, PrimeVue Pass Through, Ant semantic DOM, Web Awesome Parts, and Citry's lack of generic fallthrough | Publish per-part attribute groups with safe merge and handler order | IDs, names, refs, events, and ARIA land on the wrong node or override required behavior |
| Provider state follows logical ownership across portals | Vuetify defaults/theme, React Aria portals, Chakra providers, Ant static-root limitation AD-2, Base direction/CSP, and multiple overlay complaints | Add logical client context with nested shadowing, live updates, portal continuity, and diagnostics | Portaled controls lose theme, direction, defaults, IDs, or policy; static service roots diverge |
| Portal correctness includes focus, inertness, and cleanup | BSR-3, M-3, RN-1/RN-2, RA-3/RA-5, and CZA-5 | Centralize overlay stack, focus restoration, outside interaction, Escape, scroll lock, portal target, and disposal policy | Nested overlays deadlock focus, dismiss parents, leak inert state, or become unreachable on touch/AT |
| Collection identity is distributed state | Combobox, Select, Table, Tabs, Tree, virtualization, autofill, hidden controls, and fragment morphs recur across the corpus | Require explicit item keys and separate active, focused, selected, displayed, and submitted values | Visual state, machine state, hidden form state, and server value disagree |
| Native forms are the dependable server boundary | Bootstrap, React Aria, Base UI, Web Awesome, Vuetify, PrimeVue, django-formset, Cotton, and local production needs | Build rich controls around native form semantics and server revalidation; test reset, autofill, validation focus, and no-JS paths | Client-only validation or JSON controllers replace reliable browser and server behavior |
| CSS customization has an upgrade budget | VU-1, RN-4, AD-3/AD-4, BS-1/BS-2, M-5, and Web Awesome's versioned Parts | Freeze supported tokens, layers, parts, state attributes, and documented DOM only; provide upgrade fixtures | Cascade order, compiled values, DOM changes, and wrapper styles silently alter production output |
| Source copy maximizes control and diff burden | BSR-1/BSR-2 and shadcn's multi-base registry | Keep installed `citry-ui` as the normal path; consider provenance-aware export only later | Accessibility and security fixes fork per application and no longer arrive centrally |
| Runtime styling and recipes can cost dense views | CZA-3, large styled suites, local bundle history, and measured package publication sizes | Precompile default CSS, keep static components inactive, split family assets, and benchmark cold mount/update/cleanup | Broad catalog ambition turns into unavoidable JS, CSS, memory, and first-interaction cost |
| SSR claims do not prove fragment and morph safety | Web Awesome SSR, React hydration, Chakra/Emotion setup, PrimeVue history, and Citry's distinct graph model | Test rendered output through Citry's actual full-page, fragment, morph, and teleport paths | A library passes isolated hydration but duplicates handlers, loses IDs, or leaks state after server updates |
| Accessibility posture is not conformance | Every dossier distinguishes docs claims from independent outcomes; current defects exist in mature suites | Use standards as acceptance baselines, automated scans as gates, browser behavior tests, and manual assistive-technology evidence | Marketing claims or Lighthouse scores substitute for keyboard, focus, touch, screen-reader, zoom, and forced-color behavior |
| Licensing and paid boundaries affect architecture | PrimeVue 5 changed source and redistribution terms; Web Awesome gates Pro breadth; other work units have explicit open boundaries | Keep core breadth first-party and redistributable, audit every optional dependency, and make companion-package terms visible | Required generic components become procurement, source-continuity, or redistribution risks |

## 4. Client ambient-context prerequisite

The UI library should not choose an API spelling before a focused Citry design,
but its required semantics are now concrete. One client registry must back both
component-internal access and any Alpine template magic. Candidate surfaces are
methods available during `$component.init()` and `$provide`/`$inject` magics;
they must not become separate state systems.

The initial investigation should cover these values:

- theme identifier and resolved mode where CSS inheritance is insufficient;
- component defaults and density;
- writing direction and direction-sensitive interaction;
- portal target and overlay-stack policy;
- generated-ID scope or allocator;
- CSP nonce or security policy if later core support needs ambient data;
- diagnostics and development provenance.

Localization may eventually use the same transport, but translation keys,
catalogs, locale negotiation, fallback, formatting, and author APIs remain a
separate research package.

### 4.1 Required semantics

| Question | Required answer before release |
|---|---|
| Ancestry | Resolution follows Citry's logical ownership graph, including receiver fallback content and caller-owned supplied slots as explicitly specified, rather than incidental DOM parents |
| Shadowing | The nearest provider wins; defaults and missing-value behavior are deterministic; merging is limited to named value types that define it |
| Reactivity | Descendants observe provider updates without reinitialization; equality and batching behavior are defined |
| Server agreement | Initial browser values agree with server rendering, or a documented deterministic recomputation occurs before interaction |
| Teleport | Context follows logical ownership while CSS and HTML direction differences at the physical destination remain visible and testable |
| Morph | Compatible graph revisions preserve providers and consumers; replacement and ownership changes reconnect exactly once |
| Cleanup | Provider disposal releases consumers, effects, observers, global listeners, portal registrations, and generated resources |
| Diagnostics | Missing provider, wrong type, collision, cross-root access, stale consumer, and server/client mismatch identify component and value provenance |
| Multiple roots | Separate Citry engines and page roots do not share ambient state accidentally |
| Security | Values have declared trust and serialization policies; tenant-controlled strings cannot become HTML, CSS, URLs, or executable expressions merely through context |

### 4.2 Acceptance scenarios

The prerequisite spike should include nested theme/default providers, a
direction-sensitive Tabs or Combobox, a Dialog teleported outside its visual
theme subtree, a supplied slot whose caller and receiver have different
providers, a fragment that replaces one provider value, a morph that preserves
it, removal while an overlay is open, and two independent Citry roots. Each
scenario should assert resolved values, updates, focus, cleanup, generated IDs,
and diagnostic output.

## 5. Library-level conventions to decide in Phase 6

These do not require new Citry core mechanisms, but the component package must
make them public and consistent.

### 5.1 Styled and headless contract

- One behavior implementation owns semantics, state transitions, keyboard,
  focus, form serialization, ARIA, IDs, outside interaction, and cleanup.
- Styled components select supported markup and add token-based recipes.
- Headless components render no library HTML. Required slots expose typed
  state, attributes, handlers, relationships, and focus targets to
  author-owned markup.
- Both modes run the same behavioral conformance cases. Visual assertions apply
  only to the styled mode and author-responsibility checks apply to headless use.
- Headless documentation states which native element and bindings the author
  must apply. The conformance renderer treats omitted required bindings as a
  failure and diagnostics should catch omissions where the framework can.

### 5.2 Attributes, parts, and content trust

- Define attribute groups by destination, such as root, control, input, label,
  popup, backdrop, list, item, and description.
- Merge required handlers and ARIA relationships predictably. Document whether
  author handlers run before or after internal state changes and how
  cancellation works.
- Render ordinary labels, errors, filenames, remote results, and table cells as
  text. Name any trusted-fragment capability explicitly.
- Validate or delegate URL schemes visibly. Treat file hints as client
  affordances and revalidate everything on the server.
- Keep IDs deterministic across repeated collections, fragments, portals, and
  multiple roots; fail diagnostically rather than cross-linking unrelated
  controls.

### 5.3 CSS and tokens

- Use a library prefix and explicit cascade layers.
- Separate foundation, semantic, component, state, and user-override tokens.
- Prefer logical properties and direction-aware placement.
- Support light/dark and subtree theme changes without runtime generation of a
  whole style sheet.
- Freeze only documented parts and state attributes, not incidental descendants.
- Provide stable focus, forced-color, reduced-motion, zoom/reflow, and touch
  behavior in the default theme.

### 5.4 Events and async state

- Use controlled and uncontrolled forms where both are meaningful.
- State-change events identify the reason and originating native event and
  define cancellation before mutation where cancellation is supported.
- Standardize `idle`, `pending`, `success`, `error`, `empty`, and stale-result
  behavior without turning network policy into a component concern.
- Dispose timers, observers, requests, global listeners, and overlay-stack
  entries on replacement or removal.

## 6. Prototype-fit matrix

Phase 7 should implement the same risk-heavy slice in at least two plausible
architectures. The slice should include a minimal static control only where it
tests a shared foundation; component count is not the objective.

| Probe | Why it belongs | Citry contracts exercised | Primary falsification target |
|---|---|---|---|
| Button | Smallest native-interaction and variant probe | typed props, attributes, Events, loading, form type, styled/headless pairing | element replacement or headless use loses keyboard/form semantics |
| Field and Input | Core server-form and content-trust probe | labels, descriptions, errors, IDs, attribute destinations, native form, Events server errors | visual state, browser validity, server errors, and accessible descriptions disagree |
| Dialog | Highest-value overlay ownership probe | teleport, focus, Escape, outside interaction, scroll lock, morph cleanup, provider continuity | nested or removed overlays leak focus, inertness, listeners, or theme/direction |
| Combobox | Highest-risk collection probe | item keys, input/listbox state, async ordering, hidden/native submission, portal, IME, touch | displayed, selected, focused, submitted, and server-authorized values diverge |
| Tabs | Compact compound-part and keyboard probe | named parts, controlled state, generated IDs, orientation, direction, fragments | panel relationships or focus order break across morph and RTL |
| Semantic Table | Separates useful server HTML from optional grid behavior | static rendering, responsive CSS, row identity, fragments, composed cell actions | broad data behavior forces a domain-heavy grid into core or makes static tables client-active |
| Dynamic form/collection workflow | Combines the highest-risk contracts in one user job | repeated server rows, Field/Input, async Combobox, add/remove, validation, focus after mutation, morphing, cleanup | item, field, visible selection, submitted value, and server identity diverge after mutation |
| Theme/default provider | Exercises the missing ambient contract | server provide/inject, proposed client registry, nesting, updates, slots, teleport, diagnostics | provider behavior depends on DOM ancestry or duplicates server/client state |

The comparison must not hide missing framework work inside application globals.
If a prototype needs private Alpine state, DOM queries for logical ownership,
raw executable callback strings, a second client component tree, or duplicated
styled/headless behavior, that architecture is falsified for the official
package.

## 7. Verification mapped to fit risks

The complete approach is in the
[quality and support test strategy](quality-test-strategy.md). This matrix
connects the highest architectural risks to concrete gates.

| Risk | Automated gate | Browser or assistive-technology gate | Manual or release gate |
|---|---|---|---|
| Semantic markup and ARIA | Nu HTML validator, axe, role/name snapshots, relationship assertions | keyboard scripts and focus assertions in Chromium, Firefox, and WebKit | NVDA, VoiceOver, TalkBack, and JAWS when available for the release-critical slice |
| Styled visual accessibility | token contrast checks where computable; screenshot assertions | forced colors, reduced motion, 200% and 400% zoom/reflow, coarse pointer, RTL | design review for focus visibility, target size, error discovery, and high-contrast meaning |
| Forms | server tests for coercion/errors plus `FormData` assertions | submit, reset, autofill, constraint validation, failed-focus, and no-JS paths | hostile and malformed input review; framework-host smoke matrix |
| Morph and lifecycle | identity, graph, cleanup, and dependency tests | repeated fragment/morph/replace/remove/reconnect scenarios | memory/listener review for the risk slice |
| Portals and context | provider-resolution and stack unit tests | nested Dialog/Popover/Combobox, removed trigger, teleported theme/direction, outside interaction | screen-reader and mobile-keyboard runs |
| Async collections | deterministic state-machine tests and stale-result tests | latency, reorder, abort, error, retry, IME, touch, and autofill scenarios | server-authorization and data-disclosure review |
| Assets and payload | dependency manifest, duplicate-load, source-map, wheel-content, and size budgets | cold route and fragment-load measurement | install/upgrade/downgrade/uninstall across supported Citry ranges |
| Whole-page quality | Lighthouse CI on representative complete pages | real browser performance and accessibility traces | Treat a score of 100 as a regression smoke result, not conformance certification |

## 8. Phase 6 entry conditions

Phase 6 may begin with these explicit boundaries:

1. The ambient-context design is a named prerequisite work item. Prototypes may
   compare internal shapes, but no private shape becomes a public UI API.
2. Prototypes and the final package use explicit per-Citry
   `register_library()` before initialization. Complete uninstall and live
   replacement remain separate lifecycle work.
3. Namespaced prebuilt CSS and classic JavaScript are the supported baseline.
   Scoped CSS, ESM, and an asset compiler are possible improvements, not hidden
   consumer requirements.
4. The current Alpine CSP limitation is documented. The UI package must not
   worsen the trust boundary or claim strict CSP support.
5. Localization architecture stays outside the prototype. Direction and
   author-supplied text remain in scope.
6. Charts, rich-text editors, maps, and domain-heavy data grids remain
   companion-package candidates. Structural Table and ordinary collection UI
   remain in the general suite.
7. Every prototype is evaluated through actual Citry full-page, fragment,
   morph, teleport, form, and cleanup paths, not only isolated HTML examples.

With those conditions, the remaining Phase 5 artifacts can select staged
breadth and compare customization models without prematurely freezing the
component API.
