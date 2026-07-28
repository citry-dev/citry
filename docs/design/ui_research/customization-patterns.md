# Cross-library customization patterns for Citry UI

**Snapshot:** 2026-07-23. **Status:** complete; independent synthesis gate
passed 2026-07-23. This report identifies recurring mechanisms, trade-offs,
and test obligations. It does not select public class names, prop names,
export layout, or a client provide/inject syntax.

The evidence base is the twelve Phase 4 dossiers, the
[complaint register](complaint-register.md), the
[product charter](product-charter.md), and the implemented-versus-proposed
[Citry baseline](citry-baseline.md). Complaint-based conclusions use grades A
through C only. Grade D reports are separated as test leads in section 8.

The central conclusion is that Citry should distribute an installed,
centrally updatable styled suite and a supported theme-free surface over one
behavior contract. “Theme-free” cannot mean “remove the CSS and hope”: some
components require structural styles for positioning, presence, scroll
containment, or visually hidden native controls. Those requirements must be
small, documented, and tested separately from the default theme.

## 1. Normalized API and composition patterns

Different frameworks use different syntax, but the successful component
systems repeatedly expose the same concepts.

| Normalized concept | Recurring implementation | Evidence across the corpus | Citry consequence |
|---|---|---|---|
| Root-owned state | A root owns open, selected, active, invalid, or pending state and coordinates child parts | [React Aria](recon-react-aria.md), [Base UI](recon-base-shadcn.md), [Reka/Nuxt](recon-reka-nuxt.md), and [Ark/Zag](recon-chakra-ark-zag.md) | Define one owner for each behavior; styled wrappers must not create a second state store |
| Controlled and uncontrolled use | A controlled value is owned by the caller; an uncontrolled value starts from a default and is then owned locally | [Base UI](recon-base-shadcn.md#4-composition-and-behavior-apis), [Vuetify](recon-vuetify.md#3-composition-state-identity-and-portals), and [Mantine](recon-mantine.md#3-architecture-delivery-and-composition) | Support both ownership modes where the interaction needs them, without freezing prop names in this synthesis |
| Compound parts | Root, Trigger, Content, Item, Label, Description, and similar named pieces form one component | [React Aria](recon-react-aria.md#5-frozen-comparison-slice), [Base UI](recon-base-shadcn.md#6-frozen-comparison-slice), [Reka/Nuxt](recon-reka-nuxt.md#3-composition-state-identity-and-portals), and [Ark/Zag](recon-chakra-ark-zag.md#4-composition-state-and-item-identity) | Use explicit parts only where they expose meaningful semantic or structural choices; keep simple components simple |
| Slots and render hooks | Named content areas let callers supply labels, icons, descriptions, items, and panels | Every styled suite; especially [Nuxt UI](recon-reka-nuxt.md), [PrimeVue](recon-primevue.md), and [Cotton UI](recon-python-component-packaging.md) | Prefer template-authored fills so Citry preserves caller scope; document fallback ownership and every slot's semantic duty |
| Stable state markers | Public data attributes, classes, or custom states expose open, selected, disabled, highlighted, and placement state | [React Aria](recon-react-aria.md#4-customization-ladder), [Base UI](recon-base-shadcn.md#5-customization-ladder), [Ark/Zag](recon-chakra-ark-zag.md#5-customization-ladder), and [Web Awesome](recon-web-awesome.md#4-customization-ladder-and-styledheadless-implications) | Styled and theme-free forms should publish the same normalized state vocabulary |
| Explicit item identity | A configured value or key identifies an item independently of DOM position or display text | Combobox, Tabs, Tree, Table, and collection findings throughout the shared slice | Require stable application identity across filter, reorder, pagination, fragments, and morphing; never infer it from an index or label |
| Explicit attribute routing | APIs say whether attributes target the root, native input, trigger, popup, item, or another named part | [PrimeVue Pass Through](recon-primevue.md#3-composition-state-identity-and-portals), [Ant semantic parts](recon-ant-design.md#4-customization-ladder-and-styledheadless-implications), and the [Citry baseline](citry-baseline.md#2-constraints-the-library-must-design-around) | Define typed, node-specific mappings instead of pretending all arbitrary attributes fall through to one root |
| Inherited configuration | Providers carry defaults, direction, theme, environment, portal policy, generated-ID policy, CSP values, or services | Every framework suite's provider audit | Use CSS and native HTML inheritance for visual/direction values where possible; reserve client context for behavioral values |
| Portaled overlays | Logical ownership stays with the component while content is physically placed elsewhere | All React/Vue headless foundations and styled suites; Web Awesome uses its own popup infrastructure | Preserve logical Citry scope across teleport while separately testing physical CSS, focus, inertness, stacking, and scroll boundaries |
| Native form bridge | A native control or hidden proxy carries name, value, validity, and reset/submission state | [React Aria](recon-react-aria.md#7-forms-trust-assets-and-runtime), [Base UI](recon-base-shadcn.md#8-forms-trust-assets-performance-and-upgrades), [Ark/Zag](recon-chakra-ark-zag.md#8-accessibility-forms-trust-and-async-behavior), and [django-formset](recon-django-formset.md#6-forms-validation-submission-and-async-state) | Native submission remains the baseline; rich controls must prove that visible and submitted state stay synchronized |
| Transition metadata | State-change callbacks may carry the reason, originating event, and a cancellation operation | Base UI is the clearest current reference; other suites usually expose less consistent callbacks | Define behavior-level reasons and cancellation boundaries before connecting transitions to Citry Events |

### Controlled and uncontrolled state

The distinction is about ownership, not framework syntax:

- In an uncontrolled interaction, the component owns current local state after
  receiving an initial value. It still reports changes and remains subject to
  server morph and reset rules.
- In a controlled interaction, an external owner supplies current state and
  decides whether a requested transition becomes authoritative.
- Server-rendered state is not automatically controlled state. A fragment may
  replace canonical data while still preserving local focus, text editing, or
  open state according to an explicit morph policy.
- Form reset, browser autofill, Back/Forward Cache restoration, and a Citry
  Events response are independent state sources. Each component must document
  which source wins and why.

Citry should first normalize ownership, transition, and reconciliation rules.
This report deliberately does not choose paired kwargs, magic names, or a
Python state-object API.

### Reasons and cancellation

A reason distinguishes transitions such as pointer selection, keyboard
selection, Escape, outside interaction, form reset, server replacement, and
programmatic control. This matters because dismissing a Dialog after Escape is
not the same request as closing it after a successful server action.

Cancellation must also have one owner and one time boundary. Preventing a
local transition before it commits is different from canceling an in-flight
network request, superseding an old response, or compensating after the server
has committed work. Citry should not overload one “cancel” flag for all four.
The comparative prototype should record reason, original browser event when
one exists, whether prevention is still possible, and the resulting local and
server states.

## 2. The customization ladder

The ladder starts with safe, centralized changes and ends with application
ownership. A library is deeply customizable when ordinary branding stays near
the top, structural adaptation is possible in the middle, and source ownership
is an exceptional last step.

| Level | Intended job | Required contract | Recurring shortcoming when this level is weak |
|---|---|---|---|
| 1. Foundation tokens | Color, typography, space, radius, elevation, motion, and responsive foundations | Typed or documented semantic variables with stable fallback values | Sass-only or build-only changes block runtime branding; primitive-only variables make coherent changes laborious |
| 2. Theme and scope | Light/dark, density, brand, and descendant theme scopes | Deterministic precedence, direction support, server/client agreement, and portal behavior | First-render theme mismatch, context loss, and unclear nested-provider behavior |
| 3. Component defaults and variants | Size, appearance, emphasis, density, semantic color, and repeated application defaults | One vocabulary and one precedence table across families | Per-family names and merge order drift, as in AD-3 and resolved Vuetify CSS ordering history |
| 4. Public states and per-instance values | Disabled, invalid, pending, selected, open, placement, classes, style, data, ARIA, and ordinary HTML attributes | Stable state names and explicit destination nodes | Broad forwarding creates injection/semantic risk; one root mapping cannot address compound markup |
| 5. Named parts and slots | Replace or decorate meaningful substructure | Few semantic part names, slot ownership, fallback rules, required relationships, and stable IDs | Too few parts force internal selectors; too many expose the whole DOM and make upgrades expensive |
| 6. Theme-free component | Application-owned visuals with library-owned semantics and behavior | Same state, events, IDs, form contract, and accessibility behavior as styled form; required structural CSS named separately | “Unstyled” may only suppress classes while markup and visual accessibility remain unclear |
| 7. Behavior or advanced controller | Application-authored markup around the supported state machine or controller | Strict part registration, lifecycle, identity, reason, and cleanup rules | Verbose assembly and reliance on internal context or collection details |
| 8. Source ownership or subclassing | Product needs that cannot fit the supported public contract | Provenance, local-diff visibility, security/accessibility update process, and an exit path back to upstream | Every application becomes responsible for merging upstream behavior and security fixes |

This ordering synthesizes the charter with the strongest token systems in
[Ant Design](recon-ant-design.md#4-customization-ladder-and-styledheadless-implications),
[PrimeVue](recon-primevue.md#4-customization-and-styledheadless-implications),
[Chakra](recon-chakra-ark-zag.md#5-customization-ladder), and
[Nuxt UI](recon-reka-nuxt.md#4-customization-and-styledheadless-implications),
plus the source-ownership evidence from
[shadcn/ui](recon-base-shadcn.md#3-delivery-dependencies-and-ownership).

### CSS layers, tokens, and parts

CSS custom properties are the strongest common transport for inherited visual
values. They cross server rendering without serialization code, update
reactively through the cascade, and do not activate a client component. They
do not carry portal targets, generated-ID services, focus policy, or request
state.

Citry UI therefore needs:

- a small semantic token taxonomy with documented fallback values;
- a frozen reset and cascade-layer order before the comparative prototype;
- logical properties and explicit `dir` tests for LTR and RTL;
- component variables only where a semantic/global token is insufficient;
- public part classes or attributes whose specificity is intentionally low;
- one documented application override layer that wins without `!important`;
- no requirement that consumers run Sass, Tailwind, or another compiler; and
- collision tests with ordinary application CSS, Bootstrap, and Tailwind.

The exact layer names and token names remain open. The Nuxt and Vuetify
complaints show that merely having layers does not establish a stable cascade.
The Bootstrap findings show that runtime variables are insufficient when
component states are still compiled from Sass. The Web Awesome Parts contract
shows the value of versioning named targets without exposing private markup.

## 3. Sharing styled and theme-free behavior

The product charter requires both forms of every family. The corpus supports
several implementation strategies, but it does not justify choosing one yet.
Possible shapes include shared Python/controller internals with two public
renderers, one renderer with an explicit styling choice, generated sibling
classes, or layered exports. The comparative prototype must decide among them.

What can be fixed now is the shared contract.

| Must remain identical | May differ when documented |
|---|---|
| State ownership and transition reasons | Decorative wrappers with no semantic or focus role |
| Keyboard, pointer, touch, focus, and dismissal behavior | Default classes and theme CSS |
| Accessible roles, names, relationships, and live-region timing | Optional visual-only icons and separators |
| Generated identity and collection item identity | Layout markup required only by the styled recipe |
| Native form name, value, disabled, required, reset, validation, and submission behavior | Theme-level motion, provided reduced-motion behavior remains equivalent |
| Loading, empty, error, cancellation, retry, and stale-result states | Convenience slots that compile to the same supported parts |
| Content escaping, URL policy, attribute routing, and trusted-content boundaries | Additional style-only variants |
| Initialization, morph preservation, removal, and cleanup | Asset loading when the theme-free form needs no theme CSS |

The theme-free surface still owns semantic defaults. A polymorphic Button
cannot stop behaving like a button merely because an author chooses another
element. A Dialog title or Field label relationship cannot point to a missing
part. A Toast cannot delegate announcement timing to the user's CSS. The
current `@vuetify/v0` findings VU-3 through VU-5 make these failures concrete.

Purely presentational components should not acquire artificial browser state.
A styled Card can share semantic structure and slots with a theme-free Card
while both remain server-only. Static components should not initialize Alpine
or load JavaScript because they belong to the same package as Dialog.

### Structural CSS

“Headless” and “CSS-free” are not synonyms. Visually hidden native inputs,
overlay positioning, focus guards, scroll locking, and presence may require
small structural rules. Citry should classify every rule as one of:

1. semantic or structural behavior required in both forms;
2. accessible visual behavior, such as a minimum focus indicator when the
   theme-free author has not supplied one;
3. default-theme presentation; or
4. documentation/example styling that is not shipped as behavior.

The prototype should prove that removing category 3 leaves a usable semantic
component and should report the byte cost of categories 1 and 2 separately.

## 4. Delivery-model comparison

| Model | Control and customization | Central fixes and upgrades | Assets, CSP, and server rendering | Main shortcomings | Citry fit |
|---|---|---|---|---|---|
| Styled installed suite | Tokens, variants, defaults, slots, parts, then wrappers; application usually does not own internals | Maintainer can ship fixes to all consumers; public DOM/part changes still create migration cost | Often brings a client framework, runtime styling, aggregate CSS, icon choices, and hydration requirements | Rich defaults can hide native semantics, provider complexity, context-blind services, inconsistent style precedence, and large shared payloads | Best product and maintenance model, but Citry must replace React/Vue/runtime styling with Python components, Citry behavior, and prebuilt assets |
| Headless installed foundation | Maximum behavior and markup composition through parts, state, and controllers | Central keyboard, focus, and ARIA fixes; consumer wrappers must still be retested | Usually little or no theme CSS, but a substantial client runtime, positioning, and portal infrastructure remains | No coherent visual default, verbose assembly, visual accessibility delegated to users, and wrapper drift | Best behavior reference; insufficient as the default product unless paired with a maintained styled layer |
| Source-copy catalog | Application can edit any markup, behavior, class, or dependency | No automatic merge for local edits; upstream accessibility and security fixes require review and manual integration | Build tool, copied dependencies, registry provenance, and project-specific payload become application concerns | Upgrade diff/overwrite friction, implementation base changes, supply-chain breadth, and loss of suite-wide guarantees | Useful only as an optional future export or ejection tool, not the primary Citry distribution |
| CSS-only or CSS-first suite | Fast styling through classes, Sass variables, utilities, and limited custom properties | CSS and optional plugins update centrally | Excellent static SSR and no framework runtime for noninteractive markup; Sass customization may require a build | Behavior APIs are shallow, headless parity is absent, Sass and runtime variables can diverge, validation accessibility and overlay clipping need care | Useful for static delivery, cascade, and no-build lessons; insufficient for Citry's behavior-heavy forms and overlays |
| Web Component suite | Framework-neutral elements, slots, CSS variables, Parts, methods, properties, and events | Installed custom elements receive central fixes; shadow internals reduce accidental coupling | Client upgrade is mandatory for rich behavior; Shadow DOM, asset base paths, dynamic imports, strict CSP, and experimental SSR add constraints | Pre-upgrade form behavior, shadow styling limits, portal/document context, conditional-slot hints, and a second runtime model | Valuable Parts and framework-neutral evidence; not the Citry implementation model because Citry already owns server rendering and client lifecycle |

The Python evidence fits the installed model. Cotton UI demonstrates that a
separate wheel can carry templates and prebuilt CSS/JavaScript, while
django-components demonstrates package discovery and asset concerns. Their
registry, context, and Alpine choices are evidence, not Citry dependencies.
django-formset is a specialist installed form controller rather than a
general suite, but its dynamic-activation and upload findings are important
for Citry lifecycle and security tests.

### Upgrade ownership

Installed packages centralize implementation ownership but do not erase
consumer migration work. Tokens, part names, semantic DOM, provider defaults,
form serialization, and event reasons all need versioning. Source-copy moves
that entire burden into each application. CSS-only systems make selectors and
layer order the upgrade surface. Web Components add element upgrade and
Shadow DOM contracts.

For `citry-ui`, the distribution should own templates, behavior, structural
CSS, theme CSS, and an asset manifest. Applications should own theme values,
documented part overrides, and explicit wrappers. A future source export must
record its originating package/component version and support a reviewable
upstream diff. It cannot be the only route to ordinary customization.

## 5. Ambient context, portals, and services

Providers recur because some values belong to a logical subtree rather than a
single component. The comparison does not establish a Citry API syntax, but it
does establish the required semantics.

| Concern | Required behavior |
|---|---|
| Values | Theme mode or scope when CSS is insufficient, density behavior, direction, environment/document root, portal target, generated-ID scope, CSP nonce or policy values, and component services |
| Nesting | The nearest provider may override a field. The contract must say whether omitted fields inherit, reset, or use defaults |
| Precedence | Library default, ancestor provider, nearer provider, component default, explicit instance value, and part override need one field-by-field order |
| Reactivity | Descendants observe supported changes without reinitializing unrelated components or losing local state |
| Server/client agreement | Initial values and IDs are serialized or deterministically recomputed; a first client render must not branch from different inputs |
| Teleport | Logical context follows Citry ownership; CSS inheritance, DOM `dir`, focus, stacking, and environment follow the physical target and need separate handling |
| Cleanup | Providers, global services, observers, scroll locks, and listeners release on removal, compatible morph, replacement, and application shutdown |
| Diagnostics | Missing values, invalid targets, cross-root access, duplicate IDs, and effective-value provenance are inspectable |

CSS custom properties and native `dir` should carry what the DOM already
handles well. A client registry is justified for values such as portal target,
environment root, generated-ID policy, and behavior defaults. A static global
service must not claim local context it does not possess. Ant Design's AD-2
shows why globally triggered Modal, Message, or Notification APIs need either
an explicit owner scope or documented global defaults.

The [Citry baseline](citry-baseline.md#2-constraints-the-library-must-design-around)
has server provide/inject but no public reactive client counterpart. The
pre-Phase-7 browser-readiness proof must compare `$component.init()` methods with
`$provide`/`$inject` magics over one underlying registry. It must not create a
second component tree. Citry's existing logical graph, slot ownership,
teleport, roots, and cleanup remain authoritative.

Localization design is explicitly deferred. This context work may carry a
future locale selection, but this report does not define translation keys,
catalog loading, plural rules, formatters, fallback, or release policy.

## 6. Forms, asynchronous state, and trust

### Native forms first

The common safe baseline is a real `form` and real native controls wherever
HTML can express the interaction. A styled input should not require a client
form store to submit, reset, autocomplete, or show authoritative server
errors. Enhanced validation can improve feedback but must not displace server
validation.

Custom visual controls may use a native hidden control, but that creates two
representations. CZA-5 and PrimeVue's PV-5 show how visible input, formatted
value, machine state, and submitted value can disagree. Every rich control
therefore needs tests for:

- `FormData`, Enter submission, explicit submit buttons, and `form` ownership;
- browser constraint validation and server-returned errors;
- reset, autofill, restored pages, disabled and read-only state;
- stable focus and edited values across Citry Events and morphs;
- JavaScript-disabled output where progressive enhancement is feasible; and
- hostile or stale server values after the option collection changes.

django-formset's DF-1 shows the cost of making JSON/fetch the only natural
enhanced path. Citry Events should enhance native submission rather than make
ordinary host views unusable.

### Loading, errors, and asynchronous transitions

The suites expose many loading visuals but rarely one transport contract.
Citry UI should normalize visible states while Citry Events owns server
transport. At minimum, behavior-heavy families need idle, pending, success,
empty, validation-error, transport-error, canceled, superseded, and retrying
states where applicable.

Client initialization is synchronous in the current Citry baseline. Async
work must start after initialization under an explicit owner, AbortController
or equivalent cancellation, monotonically ordered request identity, and a
stale-result guard. Removing or morphing a component must prevent old results
from mutating a new owner. DF-3 demonstrates why activation must also work for
fragments inserted after startup.

### Content and security boundaries

- Text, labels, descriptions, errors, filenames, table cells, and remote
  results render as escaped text by default.
- Trusted markup uses a clearly named typed capability with documented
  sanitization ownership. A boolean such as “escape false” is too easy to
  misuse.
- URL-bearing components define allowed protocols and disabled/external-link
  behavior. Attribute maps cannot silently introduce script-bearing URLs or
  replace required internal handlers.
- File controls treat `accept`, MIME, size, and preview checks as feedback.
  The server revalidates content and authorization, and temporary uploads have
  expiry and cleanup. DF-5 proves why every selection path needs the same
  checks.
- Generated IDs are deterministic, unique across engines and fragments, and
  emitted only when the referenced target exists.
- Rich tables and future exports separately address formula injection,
  encoding, and data disclosure.

The Cotton PCP-2 attribute-injection history shows that convenient dynamic
attribute syntax is a security boundary. PrimeVue and Nuxt UI show why named
raw-HTML fields also require explicit review. Citry's typed kwargs and
component-owned `c-bind` placement are the safer starting point.

## 7. Assets, CSP, server rendering, morphing, and performance

Citry's implementation constraints rule out consumer builds. The wheel must
contain deterministic plain CSS and classic JavaScript compatible with the
current asset loader. Maintainers may use build tools before publication, but
`uv add citry-ui`, asset collection, and runtime cannot require Node, a CDN,
Tailwind, Sass, or network downloads.

The asset contract should record:

- core structural CSS, default-theme CSS, and component or grouped chunks;
- static versus interactive JavaScript and feature dependencies;
- icon license, format, sprite/subset policy, and fallback;
- any font choice, license, metrics, loading behavior, and offline behavior;
- CSP needs, including the current Alpine `unsafe-eval` baseline, nonces,
  inline style attributes, and dynamic positioning;
- content hashes, dependency order, fragment loading, deduplication, and
  diagnostics; and
- raw, compressed, parsed, and runtime cost for the frozen shared slice and
  representative pages.

Citry does not hydrate a React/Vue tree. It server-renders semantic HTML and
activates Citry-owned behavior. Tests must cover the useful pre-activation
state, first activation, fragment insertion, compatible morph, incompatible
replacement, reconnect, and removal. Focus, open state, field edits, generated
IDs, provider values, pending work, global listeners, and teleported content
must have explicit preservation or reset rules.

Performance must be measured by behavior unit, not package archive size.
Static components should add no client graph work. Runtime recipe compilation
and per-component context processing have produced CZA-3 and PCP-3; prefer
prebuilt recipe CSS and request-scoped or graph-scoped shared work. M-5 shows
the opposite trade-off: one aggregate CSS file is simple but can load unused
families. The prototype should compare an aggregate asset, automatic grouped
chunks, and a small representative route without requiring manual dependency
ordering from applications.

Strict CSP compatibility cannot be promised while Citry's standard Alpine
runtime requires `unsafe-eval`. Citry UI must still avoid adding unnecessary
inline script, unsafe raw HTML, remote assets, or opaque dynamic styles. Its
documentation should separate the inherited core limitation from additional
component-specific requirements.

## 8. De-duplicated recurring failure modes

The map below uses only grade A through C evidence from the
[complaint register](complaint-register.md). A row combines reports only when
they expose the same design or test obligation. It is not a prevalence score.

| Failure mode | Retained evidence | Delivery models affected | Citry design and test response |
|---|---|---|---|
| Native semantics lost through polymorphism or proxies | VU-3, VU-4, CZA-4, CZA-5, PV-5 | Headless, styled, and source-copy rich controls | Prefer native roots; test Enter/Space, form type, hidden-control sync, conditional ARIA targets, autofill, reset, and `FormData` |
| Live-region timing and error announcement gaps | VU-5, M-2, RN-3, WA-5, BS-3 | Every model, including CSS-first forms | Keep error/live nodes mounted when required, test initial and repeated announcements, and run representative screen readers rather than axe alone |
| Virtualized or dense collections diverge from accessible state | RA-4, AD-1, PV-4 | Installed rich suites and headless collection engines | Make virtualization explicit, preserve stable identity, compare virtual and non-virtual modes, and test keyboard drag, position announcements, grouping, and scrolling |
| Nested overlays conflict over focus, inertness, dismissal, scroll, clipping, hover, or mobile keyboards | BSR-3, RN-1, RN-2, M-1, M-3, RA-3, RA-5, BS-5 | Installed headless/styled, source-copy, CSS-first, and portal-based systems | One overlay owner registry, reason-bearing dismissal, nested stack tests, interactive-content policy, overflow containers, iOS keyboard/scroll runs, Shadow DOM/environment tests, and cleanup assertions |
| Theme or CSS precedence changes across navigation or upgrades | VU-1, RN-4, AD-3, AD-4, BS-1, BS-2, PCP-1 | Styled installed, CSS-first, server-template, and source-copy wrappers | Freeze layer and merge precedence, test two brand themes after navigation/morph, version semantic parts, and prohibit ordinary reliance on internal selectors |
| Wrapper APIs expose too little or too much compound structure | RA-2, RN-5, PCP-1 | Installed headless/styled and server-template systems | Freeze a small semantic part vocabulary, test list-item and selected-value composition, and supply convenient styled assemblies without hiding supported behavior |
| Direction or mode support forks assets and first-render state | BS-4, M-4 | CSS-first and installed styled systems | One direction-aware artifact where practical, logical CSS, explicit inherited `dir`, deterministic initial mode, and LTR/RTL interaction plus screenshot tests |
| First-render style or provider state disagrees with the client | PV-2, PV-3, M-4, CZA-1, WA-1 | Runtime-styled suites, Web Components, SSR frameworks | Deterministic server inputs, prebuilt critical CSS, useful pre-activation HTML, no client-only branch from unknown preference, and screenshot/morph tests |
| Local or static services lose descendant context | AD-2 plus provider/portal mechanisms corroborated across the corpus | Installed styled suites and service APIs | Require an explicit owner scope for local feedback; test nested theme/direction/portal values and reject context-blind convenience APIs |
| Copied or multi-layer implementations make upgrades application work | BSR-1, BSR-2, CZA-2, PCP-4, PCP-5 | Source-copy and independently versioned styled/headless layers | Installed default, synchronized compatibility matrix, provenance for any exported source, asset/registry versioning, and migration fixtures |
| Client runtime or styling work scales with component count | CZA-3, PCP-3, M-5 | Runtime recipe systems, server template engines, aggregate CSS | Prebuild recipes, capture shared request/graph context once, keep static output static, and measure dense forms/tables plus route CSS |
| Dynamic insertion misses behavior or assets | DF-3, WA-1, PCP-5 | Lazy installed runtimes, Web Components, Python asset managers | Fragment-aware asset discovery, idempotent activation, readiness diagnostics, reconnect/removal tests, and no document-load-only scan |
| Attribute or trusted-content flexibility crosses a security boundary | PCP-2, DF-5 and current documented raw-content mechanisms in the dossiers | Every delivery model | Typed destinations, escaped defaults, explicit trusted fragments, uniform file-path checks, server validation, and hostile-input fixtures |
| Specialist form transport or nested paths diverge from ordinary host behavior | DF-1, DF-4, PV-5 | Form controllers and rich installed suites | Native form baseline, explicit path/identity grammar, traditional host-view fixture, nested collection tests, and separate transport enhancement |
| Library behavior leaves visual accessibility to every consumer | RA-1, BSR-5 | Headless installed and source-copy | Ship a first-party styled layer, provide minimum theme-free focus/forced-color guidance, and test the exact styled wrapper rather than only its foundation |
| Licensing or source closure changes continuity and redistribution | PV-1 | Closed/dual-licensed installed suites | Keep Citry UI auditable and redistributable under project-compatible terms; record dependency licenses and avoid runtime license keys |

Resolved history remains useful when it identifies a permanent regression
test. It is not described as a current upstream defect. Shared foundations are
counted once even when several wrappers expose the same behavior.

### Grade D test leads

The following reports cannot support design conclusions by themselves. They
are still inexpensive, high-value additions to the Citry acceptance matrix:

- AD-5: Pagination control names, roles, and states;
- WA-2: small touch drift during dropdown selection in an installed iOS PWA;
- WA-3: Safari scrolling after custom-control validity reporting;
- WA-4: consistency of public part names across related form controls;
- DF-2: whether interactive validation feedback can be disabled without
  disabling authoritative validation;
- the grade D portion of RA-3: native popover and non-standard overlay hosts;
- the grade D portion of CZA-1: non-Next SSR attribute-order mismatch; and
- the grade D portion of DF-1: reuse of built-in traditional Django account
  views, while the mandatory endpoint architecture itself remains grade A.

These leads should be marked exploratory until reproduced in Citry. Passing
them would not prove the associated upstream report false.

## 9. Citry design and test implications

### Contracts to prototype before public production component API design

1. **Behavior ownership:** exercise Button, Field/Input, Dialog, Combobox,
   Tabs, Table, and one dynamic form collection in controlled, uncontrolled,
   server-replaced, and form-reset states.
2. **Parts and slots:** prove compound part registration, optional parts,
   caller-owned fills, receiver-owned fallback, multi-root output, and stable
   IDs without exposing private descendants.
3. **Transitions:** record reasons, pre-commit prevention, post-commit events,
   transport cancellation, request supersession, and stale response rejection
   as different operations.
4. **Ambient context:** compare the two proposed access styles over one scoped
   registry across nesting, shadowing, teleports, fragments, morphs, cleanup,
   defaults, reactivity, server agreement, and diagnostics.
5. **Style delivery:** compile semantic tokens, variants, state selectors,
   parts, structural CSS, theme CSS, direction, forced colors, and reduced
   motion into deterministic wheel assets with no consumer build.
6. **Registration and upgrades:** install the package into two engines, repeat
   registration through the implemented `ComponentLibrary` contract, inspect
   metadata, exercise real release compatibility and upgrade/downgrade
   artifacts, and verify asset cleanup and any required richer family
   metadata.

### Shared styled and theme-free verification

Run the same semantic and behavior suite against both forms. The styled form
adds visual regression, contrast, two-brand-theme, density, responsive, and
cross-CSS tests. The theme-free form adds minimum-markup and minimum-structural-
CSS fixtures. Neither can waive keyboard, focus, form, trust, morph, or
lifecycle tests.

Required evidence includes:

- Playwright behavior in Chromium, Firefox, and WebKit;
- axe checks in every exposed state plus role/name/state assertions;
- APG-derived keyboard tables, touch, coarse pointer, IME, RTL, 200%/400%
  zoom, forced colors, and reduced motion;
- manual VoiceOver, NVDA, and TalkBack task scripts for the highest-risk
  controls;
- native form, JavaScript-disabled, server-error, Events, fragment, morph,
  reconnect, and removal fixtures;
- nested overlays, removed activators, portal targets, mobile keyboards, and
  stale asynchronous results;
- hostile text, URL, attributes, files, remote results, generated IDs, and CSP
  fixtures; and
- transfer size, parse/startup cost, interaction traces, listener/memory
  counts, and scaling runs for dense collections.

The full testing method is already specified in the
[quality strategy](quality-test-strategy.md). This synthesis adds failure-mode
traceability: every retained complaint ID above should map to at least one
Citry test or an explicit out-of-scope decision.

## 10. Trade-offs and open decisions

The installed model is the leading delivery choice because it centralizes
accessibility, security, compatibility, and upgrade work. It carries a real
maintenance obligation: Citry must version public parts, tokens, state,
events, form behavior, and package compatibility, not only Python signatures.

The strongest architectural reference is a versioned behavior foundation with
styled recipes over it. The corpus also warns against three independently
moving public layers. Citry should seek one shared implementation and test
contract before deciding whether users see separate classes, modes, exports,
or generated siblings.

Still open:

- the public styled/theme-free class and import shape;
- the exact component, token, variant, state, part, and event names;
- how much styled and theme-free markup is identical versus behaviorally
  equivalent;
- which structural CSS is mandatory;
- whether per-component, grouped, or aggregate assets are the default;
- the icon strategy and whether any font ships;
- whether advanced behavior controllers are public in the first release;
- the exact client ambient-context API and its ownership between Citry core
  and `citry-ui`;
- the initial boundary between a semantic Table and a specialist DataGrid;
  and
- source export or subclassing policy after installed customization has been
  proven insufficient.

Localization remains a separate follow-up. Direction, application-supplied
text, stable IDs, and provider transport must work now, but translation keys,
catalogs, locale data, formatting, fallback, plural rules, and release policy
are not selected here.
