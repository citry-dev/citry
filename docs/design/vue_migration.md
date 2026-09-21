# Complete the Vue migration

## Shipped Vue v1 contract

The prepared Vue runtime is the only current Citry browser runtime. It owns
mounted Citry Vue apps and the Events bridge; Alpine is retained in this
document only where older migration notes explain a rejected or historical
implementation.

Events calls are serialized per app. Same-tick calls are intentionally sent as
separate calls; `allowBatching` does not recreate the former Alpine same-tick
batch/dependency scheduler. The Vue v1 runtime also makes no pre-runtime call
queue promise. Page code must wait until the runtime and the target mounted
app are ready before using `Citry.events`.

The target surface is explicit and bounded: `render:<render-id>` addresses a
mounted component occurrence, an `Element` inside an occurrence can address
that occurrence for `Citry.events.send`, and prepared render actions may use
`mark:<caller-render-id>:<name>` for a declared marker. Global target lookup
must resolve exactly one mounted app and occurrence; zero and multiple matches
reject. Arbitrary CSS selectors and `html`, `head`, and `body` replacements
are outside the Vue v1 API.

`Citry.events.applyActions(actions)` uses the same interpreter as a server
result. When a mounted source is selected, it emits the documented
`citry:events:before`, `after`, `error`, and `stale` lifecycle around the
application, with `detail.event` set to `"__external__"`; `before` may cancel.
Global-only actions retain their global behavior and do not acquire a mounted
component lifecycle. A valid server result accepts its dequeued State
transaction before action interpretation begins, so a later action failure
cannot restore State that the server already consumed.

### Menu controller and declaration services

Status: Menu passes 56 browser cases, ContextMenu passes 15, and SplitButton
passes seven. Their server selection passes 66 tests. These checks include
correlated revisions, removal of nested declarations, and keyboard navigation
through groups and radio groups inside submenus. Child services derive omitted
context from their parent and preserve explicit overrides. Independent review
accepted the final inheritance fix and the family's native Vue examples.

The three family API pages and 24 affected public snippets use native Vue.
All 32 family snippets passed serialization checks. The controlled SplitButton
example also passed a fresh browser check for Show, Hide, release of control,
and absence of page errors after the dependency producer became consistent.

The Menu family now separates its instance-owned declaration service from DOM
controller attachment. `CMenu`, `CContextMenu`, and `CSplitButton` create and
provide a stable service during Vue setup; `onServerRender` attaches the shared
controller through an explicit factory and returns its revision cleanup. Child,
group, radio-group, separator, and submenu declarations use native injection and
server-render callbacks. The service queues registrations made before controller
attachment, dispatches retained child scopes through the current controller after
a server revision, removes exact registrations during child cleanup, and clears
pending and retained entries on Vue unmount.

The core Vue renderer is implemented. This work finishes the surrounding
product before comparing the completed implementation with every maintained
framework adapter. The user authorized this migration after the bounded
13-experiment performance round. It is compatibility and integration work,
not an extension of that round's optimization quota.

## Prior art and starting evidence

- [Vue architecture and decisions](vue.md) defines native components/slots,
  Python-selected structure, server revisions and ordinary VNodes.
- The local performance record preserves the frozen benchmark baseline and final report; benchmark artifacts are intentionally outside this promotion.
- The previous fast check recorded 6,761 Python passes, 873 failures and
  14 collection errors. This is a starting inventory, not evidence that every
  failure is stale or predates the work.
- The old ownership graph, retirement implementation and native storage are
  deleted. Browser i18n, UI, authoring tools and current examples still contain
  executable Alpine assumptions. Historical versioned docs and competitor
  implementations remain valid historical or comparison material.

## Delivery stages

| Stage | Work | Acceptance | Status |
| --- | --- | --- | --- |
| Core runtime | Document selection, hooks, assets, root CSS, native Options and Events integration | Static and interactive output, updated instances, hooks and security preserve the selected public contract | In progress |
| Render caching | Export and replay typed component/fragment results with fresh instance data | Cache hits skip the promised work while preserving slots, Events, dependencies, i18n and invalidation behavior | Typed cache replay and safe pure-body reuse implemented and reviewed; repository-wide regression gate remains |
| Events targets | Address component instances and explicit insertion markers through the production transport | Multiple targets validate before publication; retired targets fail; document shell and arbitrary selectors are rejected | Single component and marker updates qualified; contiguous multi-target groups pass nine focused browser cases and i18n passes nine focused cases; broader integration remains |
| Browser i18n | Vue providers, reactive formatting/bindings, disposal and server updates | Locale changes and revision/remount cases work without Alpine | Native provider, binding, revision, rollback and disposal paths implemented; independent lifecycle corrections verified |
| Citry UI | Port file-backed and inline runtimes, native directives, props and events | Forms, keyboard, focus, accessibility and cleanup tests pass on Vue | CForm/CField providers and CInput/CSelect consumers tested; review fixes and broader migration in progress |
| Authoring tools | Vue expression extraction/scopes, lint settings, diagnostics, LSP/editor/lexer | Correct Vue context and source positions; Citry interpolation stays Python | Current gate passes 552 LSP, 111 editor and 70 lexer tests plus editor type/lint/package-inventory checks; final integrated distribution gate remains |
| Owned applications | Six starters, demos, current docs and playground | Real workflows and local/CI lint instructions use Vue | Six starters and project-board pass native-template checks; HTMX flows and FastAPI starter search have browser proof; remaining workflows and demos/docs are pending |
| Integration | Update semantic tests, protocol inventories, CI/distribution checks and typing | Required repository, browser and package gates pass | Pending |
| Benchmark and memory | Every maintained comparison stack at 140 and 1,400 outputs | Qualified frozen artifacts, full HTML graphs, explicit failures and memory scope | Memory collector and combined report implemented and reviewed; final cohort pending |

Core, UI and tooling have separate file ownership. Review is independent,
and full repository gates run only after the integrated source settles.
The user has prioritized runtime behavior, targeting, tooling and integration
ahead of the remaining UI examples and scenarios; those examples come last.
Routine corrections, test execution, linting and mechanical transformations use
Luna Max. Substantive implementation continues with Sol, with independent
review of architectural and behavioral changes.
The user also authorized Luna Max for the bounded rendering fix discussed
during Sol capacity failures, with root design and review retained.
No commits, PRs or branch promotion occur during this local implementation.
The original worktree and historical results remain intact. Do not create
whole-codebase/environment snapshots. Disk cleanup remains restricted to the
previously authorized old qualification captures.

Prepared Vue definitions now carry producer-authenticated browser bindings as typed data. Attribute bindings attach
to an exact element opening, while text bindings attach to the existing prepared text value and preserve its static
fallback. The assembler constructs calls to a reserved template-context helper and keeps JSON operands in prepared
data; only an already-checked authored expression can appear as an optional thunk. Native compiler metadata validates
attribute operand ownership against the generated opening span. Trusted render-cache artifacts preserve both forms,
restore producer provenance, and replace per-render binding identities during replay.

The native i18n plugin resolves each projection by its checked wire binding ID, so supplied slots retain their logical
Python provider instead of inheriting an unrelated receiver service. Reactive values are copied and validated before
they replace the last successful value set; evaluation or formatting failures keep that prior set and a later render
can recover. Focused proof covers the generic compiler/cache round trip, cached ID replacement, real DatePicker and
TimePicker locale changes, and invalid-value recovery. Definition identity also includes dynamic-element metadata, so
equal templates with different validated dynamic tags cannot collide.

### Integration checkpoint, September 13

The direct Vue renderer and typed cache replay are implemented, but the whole
product migration has not passed its integration gates. The following evidence
describes focused checks, not a repository-wide passing result:

- Restored component, fragment and typed-artifact cache contracts passed 234
  focused tests before the subsequent alias-invalidation fix. That fix passed
  its 182-test cache selection and an independent 142-test review selection.
  These selections overlap and must not be added together.
- Tabs passed six interaction tests and its converted controlled-props test.
  Listbox, NavigationMenu, Tree, Toolbar and Pagination have passing focused
  browser checks. ContextMenu passes all 15 browser cases, SplitButton passes
  all seven, and Menu passes all 56. Retained nested service paths derive from
  their parent service, so correlated revisions preserve submenu identity and
  recover removed focused leaves against the authored sibling order.
- Fragment cancellation settles before a stalled stylesheet completes.
  Concurrent same-ID startup, throwing disposal, and late script-error races
  now have focused regression coverage. The late-script proof requests the
  replacement app's identical asset twice and observes only the original two
  network requests after explicitly invoking the saved stale error handler.
  This controls the callback ordering; it does not claim that Chromium
  naturally delivers two independent failures for its coalesced request.
  Pending host selector changes made through `id`, `class`, or ancestor
  attributes now cancel a stalled mount; selector changes driven only by
  pseudo-state are not claimed.
- Declarative text and attribute bindings now use native Vue expressions.
  DatePicker, TimePicker and DateRangePicker locale checks pass, along with
  invalid-value recovery. Independent review also verified provider
  reparenting, retained locale, rollback, disposal, binding authentication,
  and exact prepared-data operand validation.
- Native Events cancellation and disposed-app stylesheet publication have
  focused browser coverage. Reactive loading/error accessors and lazy bridge
  creation when a revision introduces the first Events component are now
  implemented. Writable State and `$sendEvent` pass their focused native
  browser proof and 21 bridge tests; independent review verified the subsequent
  attribute and State fixes against source, generated runtime and focused tests. State
  accepts whole-field assignments and rejects nested mutation. Native control
  bindings authored in templates have passed independent review. Runtime-provided
  bindings are undergoing browser verification. Scheduler compatibility, timing
  and target work remain.
- Memory collection and standalone graphs have a successful plumbing pilot.
  The final all-framework latency and memory runs have not been performed on
  this changing implementation.

A subsequent full UI server-test inventory, run with the worktree's Python
3.12 interpreter, recorded 2,073 passes, 320 failures and 722 deselected tests.
The failed assertions require individual classification; this is not evidence
that all 320 are stale. The inventory found Sidebar's browser callback still
needed migration. Its native Vue port now passes four browser tests, including
correlated server revisions: an unchanged default preserves a local toggle,
while a changed default is adopted. Ref-ownership guards pass 35 focused tests;
independent review accepted these corrections. An earlier run used
the wrong interpreter through a stale executable shebang and is excluded from
this evidence.

Badge and Skeleton now share the selected-attribute binding guard and pass a
68-test unit/browser selection. Browser coverage proves authored Vue class,
style and event bindings remain reactive while static Python attributes and
the components' own classes and anatomy survive. Independent review accepted
that behavior; their Python attribute mappings remain data rather than a way
to introduce executable template source. The review's stale Badge API wording
has also been corrected.

The remaining delivery order is to finish runtime contracts, Events and
explicit targets, then tooling and integration. Finish the remaining UI
examples and scenarios last, before freezing artifacts for the final
140- and 1,400-output comparison. Historical performance graphs remain evidence
for their recorded builds only.

### Control review checkpoint

Native control proofs cover immediate drafts, delayed sends, callback-visible
DOM updates, live input-type changes, custom-element upgrade cancellation,
and synchronous setter echoes. A real FastAPI starter search for `incident`
reached revision 1 with one matching card, retained the query, and produced no
page errors. These checks do not yet establish the full control contract.

Independent review identified invalid-value isolation and pending custom-element
reference retention failures. The corrections now pass eight focused browser
cases, including invalid checkbox recovery, throwing custom-setter recovery,
upward values, and caller scope inside a supplied slot. Binding errors are
handled locally, and disposal clears references held by pending upgrade tokens.
Independent re-review accepted those corrections but found that upward reads
still need isolation: a throwing custom getter or a non-JSON value must leave
State and pending values unchanged, suppress the send, report the binding
failure once, and recover after a valid value. A shared guarded read/adoption
helper now passes that regression test and the five-test affected browser
selection. Independent re-review accepted the new guard and the literal
control-binding implementation. Runtime-provided bindings remain a separately
tracked compatibility gap; they are not required by the shipped Vue v1
contract for literal template bindings.

Each value-holding element accepts one State binding. The prior contract
allows several event handlers on an element but defines no behavior for several
State fields competing for its value. Multiple State bindings produce a
pointed template error. Runtime-provided State bindings now use an authenticated
producer value and typed metadata; their browser verification is in progress.

The client passes its complete package check: TypeScript, lint, formatting, and
43 JavaScript tests, including generated runtime consistency checks. This total
includes the 21 Events bridge tests; it does not include Python or browser tests.

### Runtime-provided control bindings

The attribute extension already validates bindings introduced by Python
`c-bind` after resolving an element's attributes. The native prepared renderer
must receive that validated result as typed producer data rather than infer
trust from an encoded HTML attribute. The existing producer-token pattern in
`PreparedBrowserBinding` is the starting point for this work.

The implementation must preserve metadata through subsequent attribute hooks,
or reject a changed or unauthenticated value explicitly. Direct rendering and
the reusable leaf program both need coverage. A loop may contribute different
State field names at the same authored attribute site, so source position alone
cannot identify the resolved binding. Cache replay must reproduce the exact
validated binding without accepting user-authored internal attributes.

Before selecting the representation, check the attribute hook manager,
`rewrite_resolved_attrs()`, `PreparedElementAttrsNode`, and the leaf program's
precomputed opening elements. A representation that works only after direct
capture is insufficient if a reusable leaf program has already fixed its
directive structure. Required falsifiers include distinct loop bindings,
literal-plus-spread conflicts, later hook changes, cached replay, and caller
scope inside a supplied slot.

The implementation now passes six focused producer checks covering direct and
reusable rendering, distinct loop bindings, an empty-to-present binding with
the same definition, a changed producer value, and cache replay. Each rendered
placement receives its own binding operand; identical immutable specifications
may share an ID. Only eligible State-bearing components
use the optional runtime-control directive. Browser and independent review
remain required before this stage is accepted. The coordinated runtime build
and all 43 JavaScript package tests pass with this change.

The supplied-slot browser falsifier exposed a missing-binding case before
dispatch: runtime-provided State metadata was absent from both the caller and
receiver data, while the equivalent literal binding worked. Carrier production
was testing final Vue serialization instead of active prepared rendering.
Ordinary `Component.render()` captures prepared parts before final serialization,
so the narrower condition skipped its bindings. The corrected producer passes
all 64 prepared-capture tests and three browser control tests, including caller
ownership inside a supplied slot. Independent review accepted the implementation
after a 108-test capture/cache selection and source review of the authenticated
carrier, per-placement operands, empty-binding cleanup and lexical ownership.

The HTMX demo now keeps `SearchResults` server-rendered and serializes each
contact row as its own interactive fragment. Its `.contact-row-host` stays
outside the row's Vue app and persists across row edit/save/cancel actions; a
search replacement replaces those hosts too. Route composition inserts only
trusted final HTML returned by Citry serialization and never compiles those
strings as Vue template source. Native `ContactDetail` and `ContactForm`
`mounted` callbacks call `htmx.process()` on their exact root, and the form also
owns initial focus. The page loads the Citry runtime once explicitly.
Browser proof covers independent
row identity, whole-app edit/cancel replacements, invalid and valid saves,
unrelated-row retention, stale-search cancellation, focus, stylesheet
retention, app disposal, and no page errors. Static CSS-only documents and
fragments emit their styles directly without installing the Vue runtime.

Dependency delivery now passes 24 fragment tests, 24 updated security tests,
and all six HTMX route tests. Static output emits styles and scripts directly,
with dependency-hook entries ordered before component scripts. Interactive
output coordinates the runtime before component Options; interactive fragments
carry the Vue fragment descriptor. These changes await independent re-review.
The full serialization-security suite and remaining dependency suites still
need migration and verification; the focused counts are not full-suite results.

The broader security run exposed an additional production gap: prepared
interactive fragments can omit ordinary `Component.Dependencies` assets.
The native producer includes component code, component CSS and CSS variables,
but the fragment emitter skips dependency records on the assumption that the
producer already included everything. Hook-added dependency entries also need
to reach the final native descriptor. The completed static-delivery tests do
not cover this gap.

The chosen direction is to resolve selected dependencies once through the
existing component and extension hooks, then use their final ordered result in
the native asset descriptors. Initial documents, fragments and Events revisions
must share this handling. Bootstrap configuration must be serialized after
those hooks have finished. Inline assets can use the existing owned-byte
publication mechanism; external assets must retain their security attributes.
Required checks cover dependency-before-component execution, CSS delivery,
exactly-once hooks, selected-subtree filtering, repeated updates, and the
effective nonce, integrity and JavaScript policies. Silently omitting
unsupported assets is not an acceptable fallback.

The installed native loader retains the initial nonce, rejects nonce overrides
in revision assets, and verifies owned resources against their declared byte
digests. External resources retain explicitly declared integrity. Use this
existing delivery contract for revisions rather than trusting security-mode
request headers or adding a server-side app-policy registry. Initial explicit
nonces must pass serializer validation before deferred descriptors omit them;
the installed app supplies its nonce when loading. A revision asset that tries
to declare another nonce must fail. JavaScript omit/forbid output cannot start
an interactive app. Browser checks must verify these assumptions for actual
dependency assets under nonce and integrity settings.

Mounted initial output can load descriptors for documents as well as fragments.
Stylesheet loading and retirement must use one content-addressed identity per
asset. Unmounted document serialization is a separate delivery case: owned
scripts and styles must be supplied inline because their asset routes do not
exist. Reuse the same descriptor identities when adopting that delivered CSS;
do not require test fixtures to invent a server for otherwise self-contained
HTML. A Sidebar browser rerun exposed this distinction by remaining empty
while the loader waited for an owned stylesheet URL from `about:blank`.

Browser checks must prove callbacks observe applied styles and that startup
cancellation and final-owner removal release the right resources. Deferring
mounted initial stylesheet discovery to the loader may affect first-load
timing; measure it in the final comparison. Earlier native link delivery can
be considered later using the same descriptor URLs and app markers, without
creating a second asset identity.

The shared resolver now passes a 391-test dependency, serialization and native
Events selection. A public mounted browser test uses two distinct component
types sharing one stylesheet. Removing the first through a server revision
preserves the single link; the retained component and its `onServerRender`
callback observe the applied style. Removing the final owner detaches the link.
Root reran this browser test successfully. Initial declared assets may load
when their lazy-loading flag is false; the permission for later discovery is
still enforced during revision preparation. Independent review accepted the
resolver and browser asset lifecycle, including final hook ordering, occurrence
references, preflight checks and staged-style cleanup.

Interactive fragment hook contributions must stay inert until the fragment
descriptor has passed validation. Emitting an executable `before_manifest`
script directly would let a rejected fragment run code before acceptance.
Supported active hook assets must join the native loading transaction;
unrepresentable contributions must fail explicitly. Static fragments retain
their direct-tag integration contract. Regression tests must prove that
malformed, stale, or excluded interactive fragments execute no hook payload.

The browser extension and i18n implementation follows
[Vue i18n integration](vue_i18n_migration.md). Independent review requires
retained-subtree state, stable reactive provider forwarding, fixed plugin
installation metadata, and explicit prepublication versus postpublication
failure handling. Vue's normal batched update behavior applies; the integration
does not promise atomic observations across components to synchronous watchers.

## Browser authoring contracts

Use native Vue Options in `$component({...})`, with `Citry.vue` exposing the
exact bundled runtime's Composition API. `onServerRender({component, revision})`
is Citry's integration callback and may return cleanup. Native data/setup,
methods, computed values and lifecycle hooks own ordinary local state.
`$component(callback)` is the shorthand for registering that same
`onServerRender` callback, with the same two context fields and cleanup rules.

Python `js_data` supplies reactive instance values. Collisions with local data
or declared Vue props must be explicit errors, not silently resolved by order.
Citry UI can put its own server-seeded defaults in a distinct `serverDefaults`
object while preserving public Python kwargs and native Vue prop names.
A provided Vue prop controls the corresponding value; an absent prop uses
the server seed. Absence, false, null and invalid values need separate tests.
No global compatibility namespace is introduced for legacy Alpine scope.

Native component props/events use `:prop`, `v-bind` and Vue event bindings.
Retire `$c-props` as agreed in the Vue design. Citry event/marker channels keep
their reserved meanings. Compiler and linter changes must agree tag by tag.
`{{ ... }}` remains Python, and authored Vue loops cannot create Python
component instances. Python `c-for` prepares such instances.

A callback must not assume `component.$el` is an Element: multi-root components
are valid Vue components. Owned widgets should use explicit template refs and
verify their anatomy. Transparent server-only helpers may share their browser
parent's template, but this must be proved by a mounted-component test.

Native Options `inject` participates in server-data collision checks. The
wrapper collects local names from array and object injection forms before
installing server keys and preserves Vue's native provider resolution.
Integration coverage must include Symbol provider keys, aliased injections,
defaults, and collisions with `js_data`.
Private plugin injection must not become a replacement public scope API.

The five web starters and the project-board demo also use `$loading()` in
browser expressions. Their migration needs reactive Events loading/error
queries on the Vue instance, not only click dispatch. Preserve the documented
event-name filtering, concurrent-request accounting and cleanup on completion,
failure or component removal. Prove that a pending indicator returns to idle
after both successful and failed server actions before updating those examples.

## Verification boundaries

The output-cache cutover is unfinished. Typed lookup and publication now work
for initial simple and nested-tree cases. Slot executions, fragment replay and
extension staging are implemented, with deeper forwarding and production
Events/i18n browser checks still in progress. Unsupported typed parts produce
diagnosed misses rather than an apparently successful partial cache hit.
Finish these cases and their semantic
tests before treating the public caching feature as complete. Existing cache keys,
size limits, invalidation and extension hooks remain relevant prior art;
reintroducing the physical ownership graph is not the chosen solution.

A source-environment collection check found 5,400 tests across the Citry and
Citry UI Python test directories with no collection errors. This is an inventory
check, not a passing test run; many existing browser cases still describe the
runtime being migrated and need behavior-preserving replacement coverage.

A bounded serialization/security check later recorded 106 passes and 26
failures across `test_serialize_security.py`, `test_release_security_policy.py`
and `test_serialization_transparent.py`. Some assertions still expect the former
browser runtime or its restricted expression evaluator. Others reveal live
migration gaps: interactive dependency strategies other than document output,
transparent render roots, and final-output security checks parsing generated
JavaScript as Citry template source. These failures remain tracked work, not
approved removals of the corresponding public behavior.

Security validation of settled output must inspect HTML as output data.
Generated script bodies and literal text containing Citry interpolation syntax
must not be evaluated or parsed as Python expressions. Preserve checks on raw
active tags, event attributes, executable URLs, trusted resource provenance,
nonces and integrity. Server-compiled Vue expressions do not need the former
browser evaluator's syntax restrictions; a browser CSP test must prove the
compiled program runs without dynamic evaluation.

The input-widget port exposed a related source/data boundary: HTML escaping
returns `Markup` but leaves literal `{{ ... }}` untouched. Passing that value
straight into Vue template source can interpret user text as a browser
expression. HTML trust does not establish Vue-template-source trust. Textarea
values and option labels need exact-text browser tests, including literal
interpolation delimiters and markup-looking input. Trusted HTML handling must
remain distinct from authenticated authored Vue expressions.

For settled-output validation, the selected native design combines
[html5gum token offsets](https://github.com/untitaker/html5gum) with
[html5ever tree-builder feedback](https://github.com/untitaker/html5gum/blob/main/src/emitters/html5ever.rs).
The tree builder determines
raw-text and foreign-content parsing states; Citry collects source facts for
policy checks without implementing browser insertion rules itself. A source
token rejected conservatively despite being ignored by the browser must be
reported as such. Exact source offsets remain essential for trusted-resource
provenance. SVG/MathML integration points, malformed table/select content,
HTML self-closing syntax and scripting-enabled `noscript` are falsifiers for
this implementation, alongside generated JavaScript and literal braces.

A deleted internal graph assertion may be retired, but its user-visible
behavior must have replacement coverage. Do not classify failures solely by
the occurrence of the word Alpine or ownership. Provider, form, resource and
package ownership are still meaningful independent concepts.

Key falsifiers include callable slots at nonliteral outlets, hooks replacing
selected output, static JavaScript omission, logical Page scope around the body,
head metadata and CSS, selected-only dependencies, published URLs surviving
cache eviction, repeated server callbacks on retained DOM, prop/state
collisions, native slot lexical context, and disposal of subscriptions.

Performance is measured only after implementation and build activity stops.
Qualification and memory runs do not overlap timed latency measurements.

The Events bridge currently accepts only the calling component's render target.
The explicit-target browser experiment in `vue.md` proves marker insertion and
multi-target validation, but the marker syntax and production transport are
not integrated. Complete that agreed targeting contract before claiming the
product migration is finished. Component-boundary polling also currently
raises an unsupported-operation error and needs a defined Vue lifecycle and
replacement coverage. The public action and protocol documentation must match
the implemented target and swap modes.

Native State controls now travel as typed prepared metadata rather than an
opaque DOM payload. The compiler records an exact `v-citry-control` lifecycle
site, and the directive applies State values, records drafts immediately,
flushes through the serial Events bridge with the already-merged debounce or
throttle value, and removes listeners and timers on replacement. Focused
browser proof covers a debounced search draft surviving its server revision;
additional proof covers checkbox, multiple-select and custom JSON values,
custom setter echo suppression, invalid-type recovery, and cancellation of a
pending debounce and custom-element upgrade on unmount. The FastAPI Project
Explorer search also completed a real ASGI/Chromium revision with one filtered
card and no page errors. Runtime-spread `:c-*` bindings still lack authenticated
typed provenance and now fail explicitly; literal bindings are the supported
native path until that producer is carried through the typed contract.

Two additional authoring contracts remain incomplete. Interactive rendering
rejects generic trusted-HTML expression values, and prepared capture rejects
`#c-ignore`. The package-owned icon template path resolves neither general
case. Define their Vue behavior and add equivalent tests before treating the
migration as complete. In particular, freezing all Vue reactivity is not
automatically equivalent to protecting a subtree from server HTML updates.

Prepared element capture now combines an authored Vue binding with unrelated
`c-bind` or runtime-hook output. It retains the original executable source only
when the final resolved key has the exact authored type and value; removal
omits it, while replacement or newly introduced executable syntax is rejected.
Conflicting target names use HTML's ASCII case-insensitive attribute identity.
An authored object `v-bind`, or a dynamic argument such as `:[field]`, cannot
be proven unrelated to generated Python attributes and remains unsupported in
that combination because the current generated spread position cannot preserve
authored merge order. Either authored form remains available without generated
Python attributes. Resolve that ordering contract before treating overlapping
dynamic attributes as migrated.

Declarative i18n output now uses typed Vue text and attribute projections. The
collector keeps checked messages, targets and captured arguments in data, while
the established `values_expression` JavaScript-source API compiles only as an
optional reactive thunk. The runtime resolves the exact recorded provider,
retains the last valid argument set across evaluation failures, and restores
fresh binding identities through cache replay. Focused browser proof covers UI
slots, reactive recovery, retained provider graphs, rollback and disposal.

The bounded Events lifetime stage is implemented. Native `beforeUnmount`
reports the exact occurrence and mount generation, retirement removes that
owner, settles removable queued and active jobs, aborts transport, and cancels
detached action-delay timers. App unmount and rejected startup dispose the
bridge. The timeout now bounds both transport and response-body decoding, with
a consumer cancellation race for transports that ignore `AbortSignal`.
Prepared renders that lose their owner during asynchronous preparation now
cancel the exact attempt record. Completed stylesheet and plugin stages release
immediately, and stages returned after cancellation are aborted once;
transaction attribution lets an accepted render remount
its own sender without cancelling the result-scoped Data value, while app
disposal still wins. Focused tests cover these cases, stale-generation
retirement, repeated mount/remove sequence reset, and exact native unmount
delivery. The bridge deliberately retains app-wide serial ordering at this
stage.

Each mounted record now owns reactive `$loading` and `$error` views. Loading is
counted from enqueue through response application, including queued work;
terminal success clears only that handler's retained error, while normalized
protocol, timeout and transport failures replace it. Cancellation and
supersession finish loading without overwriting errors, and unknown handler
names reject. The native prepared host exists before the bridge, so a revision
that introduces the first Events context creates the bridge and updates exact
generation contexts before callbacks. Mounted output includes the endpoint
without loading an additional Events asset. Focused bridge and native browser
checks cover these boundaries. Writable State and imperative sends also have
focused native coverage. Literal control bindings are implemented and under
review. Runtime-provided bindings, handler timing and polling remain under
separate review; same-tick batching is intentionally outside the shipped Vue
v1 contract. Keep these checks separate from benchmark timing and memory
collection.

Native Vue `$state` supports reactive reads and whole top-level field writes.
Nested objects and arrays are deep read-only views: mutate by replacing the
top-level field, for example `$state.rows = [...$state.rows, row]`. Calls such
as `push`, `pop`, `splice`, nested assignment and nested deletion reject before
changing the value. This makes formerly untracked nested mutations explicit
without adding a second object-identity tracking graph; it is a JavaScript
migration rule and does not change Python State. Each non-GET Events call snapshots
pending fields at dequeue. Later local writes remain pending, accepted server
public State preserves those newer drafts, and a failed call restores its
snapshot only for fields that have no newer draft and remain writable. A
captured facade cannot write after its exact mount or Events contract retires.

The six maintained starters and project-board demo now author native Vue
browser syntax. Local visibility/text bindings use `v-show`, `v-text`, and
`v-cloak`; repeated component occurrences carry stable `#c-key` values. The
project board owns its document notice listener through Vue `mounted` and
`beforeUnmount` hooks and emits its internal move/completion events as bubbling
DOM `CustomEvent`s. The existing `:c-query.debounce.300ms` and other declarative
State/control bindings remain public Citry syntax. Literal bindings have native
browser coverage, including a real FastAPI starter search. The remaining
starter workflows and project-board interactions still need end-to-end checks;
runtime-provided `c-bind` control attributes are also unfinished. The HTMX demo
follows the independently hosted Vue-app contract described above.

Review event dispatch destinations too: the present host sends every custom
event through `document`, even when the action names the calling component.
Define and test component-local delivery for native Vue instances, including
empty and multi-root components, before updating the public documentation.
The bridge remains lazy for an app whose initial snapshot has no Events
instances and is installed before callbacks when a later snapshot first adds
an Events context.

Events acceptance covers the retained input-binding and lifecycle contracts as
well as a clicked button. The Vue v1 bridge intentionally serializes calls and
does not promise same-tick batching or the former Alpine dependency scheduler;
that is a deliberate migration rule rather than an unfinished optimization.
State behavior, polling, timing and explicit target handling have their own
focused coverage and remain subject to the relevant semantic tests.

### Events implementation order

Scoped `$sendEvent`, authored `@c-*` bindings, and the unscoped
`Citry.events` API (`send` and `applyActions`) use the native Vue bridge. A
widget's server-revision test should exercise its authored button and wait for
the accepted update; the global API has separate exact-target and lifecycle
coverage. Global element-based targeting resolves through the mounted Vue
registry and rejects zero or multiple app matches.

Events integration follows three dependent stages. The existing contract
in `events.md` remains the acceptance reference for timing, State writes,
loading, errors, downloads, and event delivery. Moving a callback to a Vue
instance does not implicitly remove those behaviors.

The next transport stage restores the documented single-call HTTP behavior.
Mounted bootstrap provides one per-event base URL from `Citry.build_url` in
addition to the batch endpoint. The browser appends encoded class and handler
segments to that explicit base, allowing components introduced by later
revisions to use the same configuration. GET handlers use the existing flat
query codec and reserved correlation metadata without consuming pending State
writes or attaching a CSRF header. POST handlers that disable batching use
their per-event route. Nested or otherwise ambiguous query values reject
before sending a request.

A successful attachment response must finish buffering under the same timeout
and cancellation checks as JSON responses. Only a current call may start the
download; retiring its component while reading the body prevents the save.
Successful raw responses without attachment disposition produce a transport
error through the browser event API, whose result remains JSON data. This
stage preserves serial queue behavior; it does not complete batching, polling,
supersession or explicit-target support.

The HTTP implementation now passes 27 bridge tests and a 39-test producer and
browser selection. A real browser under `/tenant/citry` exercised GET argument
and metadata decoding, then downloaded the exact expected bytes and filename
from a non-batched POST handler. The wider routes/actions run recorded 213
passes and six failures. Independent review confirmed that the HTML
compatibility failures are a regression: ordinary form posts and explicit
HTML responses must not require a Vue wire-capability advertisement. Their
fix needs both request-local encoder selection and actual server-rendered
fallback content; an empty Vue host would still break JavaScript-disabled
browsers. This compatibility correction is being designed separately from
the passing GET/download path.

The selected correction registers both encoders. Compatibility requests use
HTML with a call-local JavaScript omission policy, preserving the documented
form and htmx/Turbo path without adopting Citry's browser client. Its capability
view must permit that HTML response through both result-validation stages.
Wire requests prefer Vue when advertised and otherwise use a mutually supported
HTML encoder; omitted capabilities still mean the protocol's HTML baseline.
No request changes engine-wide preferences or later serialization behavior.
Transport review also requires isolated PUT/DELETE handlers to retain their
declared verb and GET to reject strings that URL encoding would alter.

These corrections now pass all 370 route, action and dispatcher tests. The
transport's 29 focused tests cover isolated verbs, faithful query encoding and
queue recovery, and the generated runtime has been rebuilt. Independent
re-review and the affected browser checks remain the acceptance gate.

The full generated client suite subsequently passed 51 tests. A real plain-form
navigation also reached its settled HTML response. Independent review then
found that the shared per-event server route still admits only GET and POST,
so isolated PUT/DELETE requests fail before the handler's method check. Fixing
the client verb alone was insufficient; acceptance now requires mounted web
adapter tests for admitted and rejected methods. Another form-port browser
case still requests an arbitrary CSS target with an inner swap. That failure
belongs to the pending explicit-target migration, not HTML compatibility.

The route correction uses the existing per-handler method check as the single
authority for the shared event endpoint. Prior art: `URLRoute.methods` is a
finite tuple, ASGI/WSGI/Django filter against it, and Events already validates
each resolved handler's allowed methods before decoding or dispatch. Handler
declarations accept arbitrary valid HTTP tokens, and classes may register
after the framework routes are mounted. A fixed list or a registration-time
union would therefore leave valid handlers unreachable.

`URLRoute.methods=None` will explicitly delegate method admission to the route
handler. Only the per-event endpoint selects it; batch and asset routes keep
their finite sets. Every adapter and other consumer must handle that value.
Mounted tests must prove PUT/DELETE reach their handlers, rejected methods
return the handler-specific 405/Allow without invoking it, lazy registration
works, and unsafe-method CSRF checks remain effective. This is a public routing
API addition and needs its own documentation and release note.

The route implementation now passes mounted Django/FastAPI checks for PUT,
DELETE, rejected PATCH and CSRF rejection without handler execution. A class
registered after FastAPI mounting is reachable, and a WSGI test verifies
delegated method admission. The broader Events route/Django selection records
135 passes and one HTML-output assertion failure; host parity/request checks
record 44 passes and two output-marker assertions requiring migration review.
Independent review is pending. The focused route tests do not establish that
those broader suites are fully migrated.

Browser method support is narrower than the server's valid HTTP-token contract.
HEAD cannot carry the JSON request body or return the event result body, Fetch
forbids CONNECT/TRACE/TRACK, and current ASGI request normalization omits an
OPTIONS body. The native browser bridge must reject these unsupported primary
methods before enqueueing, fetching or consuming State drafts, while server
route declarations retain their existing token support. It must not silently
choose a secondary declared method. GET keeps its explicit query transport;
PUT/DELETE and other supported body-bearing methods retain their declared verb.

Independent review accepted route delegation and the unsupported-method guard.
The guard rejects before activity counters, sequence/correlation, queues or
State drafts change. After coordinating the opaque-helper source and updating
its internal test fixtures, the generated runtime was rebuilt and the complete
client suite passed all 54 tests, including source/artifact freshness checks.

1. The implemented lifetime stage gives each mounted instance's Events work
   an explicit lifetime. The bridge
   must retire the exact occurrence and mount generation on native unmount,
   and dispose all outstanding work when its app unmounts. Retirement settles
   queued calls, cancels delayed actions and timers, aborts network requests,
   and releases retained arguments and owner records. A timeout covers
   receiving and decoding the whole response, not just receiving its headers.
   A consumer-side cancellation promise must also settle when a test transport
   ignores its abort signal. This stage can retain the current serial queue;
   it establishes cleanup, not scheduler compatibility.
2. Connect the existing Events behavior to Vue reactivity and mounted instance
   identity. Loading/error views, lazy first-Events bridge creation, writable
   State and imperative sends have focused semantic tests. Literal control
   bindings are implemented and under review. Runtime-provided bindings,
   handler timing and polling still need their separate implementation and
   tests; same-tick batching is intentionally not a Vue v1 guarantee.
   Prepared bindings and native mount/unmount hooks identify their owners.
3. Keep component and explicit-marker targets consistent across the Python
   encoder, wire validation, browser coordinator, and authoring diagnostics.
   The selected target is distinct from the caller occurrence. Immediate
   targets and their overlap are validated before publication, and delayed
   targets are rechecked when they execute. Arbitrary CSS selectors and
   document-shell replacements remain outside the selected API.

   A non-caller target needs an explicit mapping between its server render ID
   and its current Vue occurrence. Today that association is available through
   `eventContext` for Events-enabled instances, while a plain component can
   also be a valid update target. Do not assume every target has a State token
   or handler descriptor. Carry only the addressing information needed by the
   target contract, with a defined rule for components whose `simple` mode
   deliberately omits independent identity. The request's caller occurrence
   header cannot identify an unrelated target.

Scheduler work must account for prepared revision ordering. The current
request carries one app-wide base revision, so simply running sibling requests
in parallel would cause otherwise independent responses to conflict. Preserve
that rejection until the implementation can prove safe ordering or explicitly
scope revision checks to affected instances. A newer server credential must
not be overwritten by an older response merely because their UI targets differ.

The native control implementation uses the validated specs in
`citry/ext/events/bindings.py` and the input matrix in `events.md` section 5.1.
It carries those specs as prepared data and attaches their behavior to the exact
control through native Vue directive lifecycle hooks. The directive owns its
listeners and releases them on removal or a binding change. An edit updates
the pending State field immediately; debounce and throttle delay the send,
so another handler can still carry the latest field value. An explicit
`.on:` trigger must preserve an unsent draft across an intervening server
revision. Unsupported live input types must reject updates without silently
falling back to text-input behavior. Tests must exercise real controls,
binding replacement, timer cancellation and retained drafts before the
starters are considered migrated.

The generated directive resolves its owner from the component's lexical
render context, including when the control appears in a supplied slot. Its
value reads the relevant State field during rendering so native Vue updates
the control after a server State change. Keep initial value application
separate from listener installation, and use native directive removal to
release listeners and pending triggers. A binding's delayed send must retain
detached arguments, not a DOM Event or a retired component's control. Handler
defaults and explicit binding overrides share one timing decision; they must
not debounce the same send twice.

Use focused bridge tests for queue settlement, timeout, and response ordering;
use browser tests for reactive state, mounting, and native event delivery. Run
the repository gate and benchmarks after these stages and the shared UI work
settle, not between individual contract fixes.

Asset review must preserve the existing integrity policy: the `citry` setting
computes integrity for owned resource bytes and validates explicitly declared
third-party integrity. It does not require every third-party URL to declare
integrity. Initial output and revision loading must apply the same policy.
Revision-only styles need a CSS response type and a resource identity distinct
from JavaScript. Initial dependency readiness, shared stylesheet adoption and
the final metadata check after serialization hooks require browser or mutation
tests; source ordering alone does not establish those guarantees.

### Integration acceptance cases

Each row needs an observable result. Source-string assertions can check emitted
artifacts, but cannot prove mounted refs, cleanup, reactivity or visual styles.

| Area | Required observable cases |
| --- | --- |
| Component calls | Caller expressions reach child props and listeners; static and callback refs work; spreads keep Vue source order; updates change values without losing bindings |
| Transparent helpers | The public instance receives its declared root ref; nested callable slots preserve their caller's variables; helper expansion introduces no orphan occurrence |
| CSS data | Computed custom properties reach every intended root, including multiple roots and roots supplied through slots; unrelated descendants do not receive extra root markers |
| UI controlled inputs | Absent prop uses server default; explicit false overrides true; a later server callback does not make a prior DOM mutation permanent |
| Cleanup | Listeners, observers and callback effects stop exactly once on replacement or removal; retained instances rerun the server callback after a committed revision |
| Translation | Literal text escapes once; client locale changes update text, attributes and API bindings; server revisions update rich slot output; nested providers and barriers resolve the intended service |
| Extension delivery | Installed plugin assets load before mount; later provider services activate through an already installed plugin; rejected metadata leaves the prior revision usable; runtime assets follow serialization security policy |
| Tooling | Completion, diagnostics, embedded-language scopes and shipped grammar agree with executable Vue syntax and Python interpolation |
| Distribution | A built wheel serves its browser assets and native compiler without Node installed; installed-package tests cover the same public workflow as source tests |

The final benchmark report must identify any adapter that fails qualification.
A failed or unavailable measurement is displayed with its reason, never as a
zero bar or an omitted competitor. Memory endpoints are collected before the
semantic observer serializes the full DOM, using the separately documented
[memory measurement plan](framework_interaction_benchmarks.md).


## First integration findings

### Citry UI DatePicker composition, 2026-09-13

The DatePicker browser fixture exposed two independent native-Vue migration
gaps in its composed dependencies. `CPopover` published `open`, `dismissible`,
`placement`, and `matchWidth` through `js_data` while declaring the same public
Vue props, so mounting correctly rejected the collision. `CCalendar` had the
same pattern across its controlled props. Both now keep server fallbacks under
one `serverDefaults` key. Their callbacks use `onServerRender({component})`,
native instance props and injections, and `Citry.vue.watchEffect` instead of
the retired `init({els, data, ...})` callback shape.

DatePicker now declares its template-facing child state in native `data()` so
updates reach the composed Popover and Calendar. It also provides explicit null
barriers for the Field and Form symbols: the DatePicker itself still injects
its enclosing services, while its implementation-detail Calendar does not
mistakenly register as a second field control in the browser. The focused
DatePicker browser suite passes its open/select/submit/reset and controlled
value/open/required-invalid cases (2 passes). Its locale-switch case currently
stops on the separately tracked browser-i18n error
`i18n requirements conflict for the cs-CZ artifact`; this occurs before the
locale assertions and remains with the i18n integration work. Focused server
coverage records 70 passes; four standalone Popover cases are blocked in the
prepared assembler by `nested component has no prepared call metadata`, a core
composition issue rather than a Popover runtime assertion.

TimePicker follows the same boundary: its controlled Popover/Listbox bindings
now use native Vue props, prop-shaped server values live in `serverDefaults`,
its callback uses native Options APIs, and its implementation-detail children
receive null Field/Form barriers. The family-owned browser fixture, quality
scenario, and controlled snippet no longer use `$c-props`. All 25 focused
server tests pass. Initial browser assembly currently stops before mount with
`transparent prepared render crossed physical occurrence owners` while walking
the supplied Popover/Listbox slots; this is recorded for the prepared-assembler
composition fix rather than worked around in the UI by component class name.

DateRange now uses native Popover and Calendar props, native Options callback
APIs, reactive child state, collision-safe server defaults, and a Form-provider
barrier for its implementation-detail Calendar. Its fixture, quality scenario,
snippets, and guide no longer teach `$c-props` or Alpine state. All 26 focused
server tests and the two non-locale browser routes pass. Calendar now declares
its imperative `citry-ui-calendar-unavailable` client message. The locale
fixture mounts without i18n requirement errors, but its former
`Alpine.evaluate(element, '$i18n')` test control still needs the agreed public
native-Vue way to select the physical nested provider from caller-owned slot
content; lexical Page and child-ref `$i18n` both select the root service.

TagsInput's compact inline runtime now uses `onServerRender`, native component
props, `Citry.vue.watchEffect`, and declared Field/Form injections. Its browser
fixture uses Page-owned Vue data and native prop bindings. All 29 focused server
tests and all 29 browser tests pass, including controlled value/draft axes,
keyboard and IME behavior, form/reset, fieldset moves, invalid state, cleanup,
and retained reactive updates. Attribute-order-only server assertions were
made order-independent while retaining their semantic requirements.

Disclosure source now uses collision-safe `serverDefaults`, declared native
Form injection, `onServerRender({component})`, and Vue's watch effect. Its
focused server run reaches 43 passes; two Accordion-composition cases currently
fail in the server-side direct-item validator, and its Alpine-authored browser
fixtures/snippets remain to port. The remaining requested-family inventory is
18 runtime files still containing the retired `init` callback: Accordion,
Listbox, Menu, NavigationMenu, Tabs, Tree, Toolbar, CommandPalette, Dialog,
Drawer, HoverCard, Tooltip, Carousel, Image, Pagination, ScrollArea, Splitter,
Stepper, plus the TimePicker dependency Listbox. Popover and Disclosure source
callbacks are converted, while their retained fixtures and guides still need
native state syntax.

### Typed render-cache restoration plan

Independent review of the current cache and the former replay implementation
selected typed-tree export and replay. The cache will store the typed result
of Python rendering; the ordinary assembler remains the only path from that
result to Vue compiler input. Caching a second, already assembled browser
manifest would duplicate serialization and extension behavior.

First capture immutable occurrence metadata on the selected render: class
identity, prepared call metadata, slot-presence facts and authored component
bindings. Assembly and serialization will read that snapshot and resolve
classes through the current registry, rather than require live descendant
component objects. Then add a version-1 tagged codec for typed parts, render
frames, direct slot executions and call runs. References within an artifact
use local identities; no original render IDs or live Python objects survive.
Keep authored source and JSON values in separate channels. Export unknown part
kinds as a diagnosed store skip until their codec exists.

`Component.definition_id` is a process-local class-generation token. It may
guard a lookup, replay or publication against a concurrent class replacement,
but must not be persisted as a cross-process compatibility requirement.
Persist stable class/source fingerprints; retain the existing shared-cache
generation, key, vary, TTL, limit and invalidation contracts.

Cache storage is trusted application output, as it already is for cached HTML.
The codec validates the tagged structure and keeps authored source separate
from JSON values. Registered component templates also check their current
source fingerprint; this does not authenticate the writer of the cache entry.
Named fragments may intentionally replay stored source that differs from the
current body, so that source must not be silently replaced or rejected solely
because it is absent from the current template. Rebind its lexical writer to
the current supplied slot without calling that slot on a hit. Cryptographic
authentication of an untrusted cache backend would be a separate API.

Replay validates the complete artifact before changing live render context.
A component hit keeps the current boundary identity and allocates fresh
descendant identities; a fragment hit allocates fresh cached occurrences.
Direct execution order, repeated outlets, fallback/supplied fills and nested
forwarding are restored with local references and symbolic external writer
paths. Events, dependencies and i18n stage typed additions with fresh IDs and
reminted tokens, rather than replace strings in saved HTML. Signed tokens for
the same class, state and expiry can have identical bytes; acceptance checks
reminting and independent event routing, not arbitrary byte uniqueness.
Server-stored state gets a fresh cache key. Their product cache
versions remain 1 under the repository's pre-1.0 convention.

Enable replay after source compatibility, writer rebinding and built-in
extension staging are implemented together. Focused acceptance covers skipped
data/render/slot callbacks on hits, disjoint descendant IDs across hits,
component and fragment browser updates, nested cache hits inside a stored
outer result, extension rollback, and value strings that never become Vue
source. Corrupt or incompatible entries are misses; successful fresh output
may replace them. Backend errors retain their existing propagation behavior.

### Native UI providers

CForm and CField create services in native Vue `data()` and expose them with
`provide()`; CInput and CSelect read them with `inject`. Each service must be
reactive before descendant registration. Service methods
such as field capability registration and native-invalid state updates must
work before any DOM ref is available. `onServerRender` validates the actual
widget anatomy and attaches DOM effects, listeners and timers to that service.
The implementation must work with Vue's child-first mounted callbacks. Each
service keeps the same reactive proxy while its component remains mounted;
its getters read the current revision's server data. Descendant registration
must write through that proxy.

Consumer callbacks read native injection aliases. Cleanup unregisters the old
capability registration, invalid state and listeners exactly once before a
replacement callback installs them again. Use current server-default getters
so a retained service does not capture an obsolete revision's values.

The port must distinguish inherited constraints from defaults. A disabled
ancestor form remains authoritative. Its readonly setting is a default for
CSelect, so an explicit local `readonly=false` overrides it. The browser keeps
an ancestor Form's disabled state authoritative and lets local `readonly=false`
override the Form's readonly default. Focused browser tests cover
Form/Field/Input integration and Form/Select keyboard behavior, the readonly
override, and the ancestor disabled constraint. The remaining widget family
and existing broader semantic tests still need migration.

Independent review found two CField defects after those focused passes. Methods
closed over the raw service object, so native-invalid and capability updates
could bypass Vue's reactive proxy. The service also copied IDs and slot-presence
flags only once, leaving retained revisions with stale ARIA relationships and
error visibility. The service now uses an explicit reactive proxy and getters
for revision-varying values. Focused browser tests prove native validation
updates Field/error visibility and valid input clears it, and that a retained
Field revision preserves DOM identity while changing description/error IDs,
slot text and the Input ARIA references. A transition that adds or removes the
error slot itself, plus the equivalent retained CSelect ARIA proof, remains an
acceptance case.

The native Options/provider migration also covers DateInput, TimeInput,
NumberInput, PinInput, FileInput/DropTarget, Toggle/ToggleGroup, Tag/TagGroup,
Rating, Editable, Slider/RangeSlider, Combobox, MultiSelect, Progress, Spinner,
Alert, Avatar and Button. Rating and Slider focused browser suites exercise
native controlled props, callbacks, keyboard behavior, form transport, reset
and disabled/readonly behavior without the legacy props facade; both pass. The
remaining families and their semantic fixtures are still in progress.

The next UI batches are DatePicker, DateRange, TimePicker and TagsInput;
Accordion, Disclosure, Listbox, Menu, NavigationMenu, Tabs, Tree and Toolbar;
CommandPalette, Dialog, Drawer, HoverCard, Popover and Tooltip; then Carousel,
Image, Pagination, ScrollArea, SplitButton, Splitter and Stepper. DatePicker's
native fixture currently reaches an unsupported trusted-HTML contribution
from an SVG icon. That contribution needs an HTML-data path that does not
compile its text or attributes as Vue expressions. Rendering the first frame
is only the first check for each family: retained updates, form behavior,
keyboard behavior and cleanup remain part of acceptance.

### Browser loader and input-key lifetimes

Definition and type-script loading now removes its temporary script elements
and resolves cached promises without retaining DOM load events. Failed loads
retire their records for retry. Extension-script records belong to an app and
retire when that app is disposed. A focused browser test proves the same app
ID can start again and execute its extension script, a failed load can retry,
and the loader leaves no temporary script elements behind.

Input model lifecycle keys must remain stable across native slot invocations.
Pruning key records after an owner's render was rejected because a receiving
component can invoke the owner's slot later, or rerender independently of
another receiver. The implementation now derives primitive composite keys
directly, without keeping their history. Reference values use weak identity
records where supported. Nonregistered symbols use an instance-lifetime
fallback on engines that cannot hold symbols weakly; this preserves the
existing browser baseline. Distinct-symbol, primitive-type and independently
updated slot-receiver tests remain part of acceptance.

### Prepared children hidden by Vue

Logical prepared occurrences and current Vue mounts have separate validation
rules. The runtime retains updated server data for a child hidden by `v-if`,
so a later local toggle mounts its current revision. A focused browser test
proves this sequence. Server-render callbacks run for instances that mount;
hidden logical occurrences do not require a browser instance.

The independently reviewed choice is to let Vue select a mounted subset of the
checked logical snapshot. Require the app root, validate every actual instance's
ID, type, generation and nearest Citry parent, reject duplicate IDs and mounted
IDs removed from the snapshot. Hidden actions update logical state without
installing instance keys or invoking callbacks. After Vue flushes, callbacks
target the mounted intersection. A later local mount uses the latest snapshot
and the ordinary mounted callback. Transaction logs can include a transient
mount that disappears again before the flush ends.

Source authorization must check the currently mounted record and generation,
including immediately before an event response commits. A component hidden
after dispatch cannot retain authority through an old source-map entry.
Keep declared keyed-replacement checks for relevant mounted instances, but do
not treat an absent optional descendant as a render failure.

An alternative was compiler metadata for conditional calls and slot activation
chains. Review concluded that it would reproduce Vue's control flow mainly to
detect defects in trusted compiled code. The compiler already authenticates
component calls and rejects paths that repeat a stable ID. Exact DOM and local
state tests cover omitted unconditional calls and unexpected remounts without
adding that activation graph to every production render. Qualify conditional
ancestors, inactive supplied/fallback slots, call runs, directive replacements
and local toggles during a pending request under the mounted-subset contract.

Native `setup()` may return `undefined` or a synchronous plain object of
bindings. Reject a returned render function, which would override Citry's
prepared template, and Promise/async results, which require a different mount
settlement contract. Check returned names against Citry's reserved fields and
that app's installed plugin names, as for values returned from `data()`.

### Earlier pilot findings

The later production-path browser checks in
`test_i18n_vue_plugin_e2e.py` now cover a child-only Events revision below a
retained i18n provider. The test uses the real dispatcher, prepared producer
and browser startup. It verifies callback cleanup and rerun, installs an
actual translation binding in the callback scope, and confirms that a later
locale change reaches only the new binding. Authored cleanup failure also
stops the binding and retires the instance records.

Asset checks use two independently serialized applications with the same CSS.
Each application owns its emitted stylesheet node; disposing either preserves
the other and an unrelated authored link with the same URL. Within one
manifest, URL deduplication avoids untracked duplicate nodes. The existing
Events test that introduces a new child verifies its computed CSS after a
revision. These cases exercise actual emitted styles, not only hand-built
asset fixtures.

Focused failure tests also cover invalid graphs and disallowed component types
before definition requests or execution, independent frozen plugin inputs,
reverse rollback of attempted activations, abort of untouched stages, and
initial postpublication disposal without rollback. Hidden-component generation
changes and revision postpublication failure remain explicit qualification
items. Expanding the native helper contract invalidated hardcoded contract
values in several hand-built fixtures; those fixtures must derive the current
exported constant and pass again before this evidence qualifies the new build.
These focused results do not replace the final repository gate or
the frozen comparative benchmark run.

The first UI pilot is CFormCollection. Its Vue Options declare public native
props and a separate `JsData.serverDefaults` object. It uses an explicit
`ref="root"` in a transparent helper and a `watchEffect` owned by the
server-render callback's effect scope. Source/asset checks are insufficient to
prove the ref belongs to the public Vue instance; a mounted test remains required.

Independent review found two disabled-state hazards to test: a callback rerun
can accidentally treat its own prior DOM mutation as a structural default, and
a server-disabled marker can incorrectly prevent native `disabled=false` from
overriding the server default. Structural markers must exclude root disabled.

UI integration also exposed callable Slot uses outside literal outlets:
expression-time invocation in CFormCollection and `template_data()` invocation
in CInfiniteScroll. Both belong to the preserved Python Slot API. The receiving
component must be available across the appropriate callback lifecycle, with
nested calls restoring the outer context. Reinstating the ownership graph is
not needed for this execution context.

The initial tooling slice changed directive completion/routing, but independent
review caught a generated TextMate grammar still recognizing `x-*` and a shared
Vue fixture still containing `x-data`. Generated output and real source fixtures
must migrate together; dropping assertions is not a substitute.

A fresh full language-server run recorded 525 passes and one failure in the
shared formatter corpus. The failing fixture still used the removed client-prop
channel. Giving its Python expression an ordinary component kwarg preserves
the intended formatting coverage and keeps the Vue expressions unchanged.
The corrected corpus test passes, as do all 84 formatter tests. Pygments passes
all 70 tests. The editor package passes compilation, lint, 108 tests and its
packaging inventory after configuration, formatting and README corrections.
Remaining TextMate prop-channel patterns are being checked separately; these
results do not establish completion of every editor migration task.

Independent review subsequently found that accepted Vue `#slot` shorthand did
not reach editor browser-language routing. Routing and TextMate highlighting
now distinguish native `#name` from Citry `#c-*`; the complete editor check
passes 111 tests. Review accepted that correction. Python/LSP semantic support
is a separate remaining gap: both `v-slot` and its shorthand need binding-pattern
analysis rather than ordinary object-expression analysis.

The chosen semantic implementation uses the existing Rust OXC parser to check
a slot's synchronous function parameter list, collect its bound names and report free references
in defaults and computed keys with exact UTF-8 spans. Python and LSP consume
those facts through a narrow native analysis function. Slot names enter scope
only inside the slot body, not other attributes on the declaring element.
Nested aliases, rest patterns, shadowing, malformed patterns and sibling scope
restoration require tests. Slot value types initially remain unknown where the
declaring component supplies no type information. Citry `c-fill` and `#c-*`
semantics are unchanged by this authoring-analysis stage.

The slot implementation now passes 18 Rust analyzer tests, 42 Python browser
analysis tests and three focused LSP tests. Native wrapper checks reject input
that escapes the generated parameter list. LSP projects the pattern as a
synchronous arrow parameter, preserving source/cursor mapping; Node parses the
generated nested-alias/default/rest example successfully. The installed Python
3.12 extension includes the exact-wrapper checks. Independent review is in
progress. Root's subsequent full language-server run passed all 528 tests;
the four warnings concern a test client's Markdown capability declaration.

Independent review found additional accepted Vue forms: multiple parameters,
top-level rest parameters, and dynamic slot names with suffix expressions.
The analyzer must match the generated classic JavaScript function's parsing
mode. Dynamic-name normalization must preserve byte length so editor ranges
remain correct; deleting a delimiter and correcting only the cursor leaves
hover and completion edits wrong. Tests also cover brackets inside JavaScript
strings, Unicode, slot-local shadowing, and Vue's same-element `v-if` precedence
over `v-for`. These corrections are in progress and require a fresh native
build before the earlier passing checks can qualify the final source.

The coordinated CPython 3.12 release build completed successfully with the slot
API and verbatim-content compiler changes. Post-build browser analysis passes
48 tests, with 19 Rust analyzer tests and two focused LSP tests. The final
dynamic-name review remains open: Vue uses a two-state attribute tokenizer,
not balanced JavaScript bracket parsing. In particular, `#[foo][bar]` is invalid
Vue even though removing the first closing bracket makes a valid JavaScript
expression. Compiler comparisons must collect diagnostics as well as inspect
the generated code. Repeated bracket access with a dot inside a later pair
also tests re-entry into Vue's dynamic-argument tokenizer state.

Independent review accepted the final two-state implementation. The native
parameter parser, descendant-only slot bindings, shadowing, conditional/loop
precedence, Python spans and LSP projection passed review. The 48-test browser
analysis selection passes, and a manual check of repeated computed access
reports the correct `slots`, `a` and `foo` references. This completes the slot
authoring slice; callback-instance and `Citry.vue` projection types remain.

### Verbatim template content

The first four public Vue documentation pages and three complete component
examples passed focused link, registry and serialization checks. Broader docs
tests exposed five failures because prepared compilation rejects `<c-raw>`,
which protects fenced and inline code before Markdown processing.

Prior art: the parser stores the raw body as one text or foreign token, and
ordinary compilation emits it verbatim. Prepared source text has a different
contract: it is authenticated Vue template source. Reusing that representation
would let literal braces and directives become executable Vue expressions.
Dynamic trusted HTML values already have a distinct static-only representation.

The first implementation stage introduces a typed verbatim HTML part with
source and span information. Static serialization preserves exact bytes, and
cache export/replay preserves its distinct type. Prepared Vue assembly rejects
it explicitly until opaque browser HTML is supported. Tests must cover empty
content, braces, tags, comments, surrounding source, cache replay, simple
components and the real docs pipeline. This is an intermediate compatibility
stage, not completion of raw HTML support in interactive components.

The first stage passes 93 focused tests, covering ordinary raw output,
`simple=True`, explicit interactive refusal, typed cache artifacts, docs content
rendering and release notes. The full template-parser crate also passes. A full
docs-site inventory records 862 passes, 67 failures and 105 errors. Its shared
reference-build traceback now reaches the separate trusted-HTML limitation
inside Vue assembly; the prepared `<c-raw>` compiler rejection is resolved.
That shared failure affects many setup checks, but the other failures still
need classification. Independent review of the first-stage implementation is
pending. Broad docs checks should rerun after opaque browser HTML is supported.

Subsequent source inspection found an independent reason the reference output
entered Vue preparation: `vue_serialization_requirements` treats every prepared
dynamic element as browser activity. `ReferenceSymbol` selects its heading tag
with a Python `c-is` expression, which does not itself need JavaScript. Runtime
selection must inspect actual browser bindings or behavior on that element.
The correction must keep a static selected tag as settled HTML while retaining
Vue for interactive dynamic elements. It must not compensate by changing the
page-host contract or emitting duplicate fallback content.

The narrow correction passes 44 focused docs/serialization tests. Direct Vue
attributes on dynamic `<c-element>` are currently rejected explicitly; this
change does not add support for them. Events metadata still selects Vue, and
an already-interactive parent retains the dynamic-element assembly path.

Independent review broadened the raw/simple/capture/cache selection and found
167 passes and four failures. Three are real callable-slot regressions: static
simple rendering prints the `PreparedTextValue` representation instead of its
text. They are being fixed in the typed slot/static serialization path. The
fourth is an i18n output assertion requiring separate qualification. The raw
feature's focused tests pass, but this wider result prevents treating the
simple/cache integration as fully verified.

Independent review accepted the bounded verbatim-content implementation.
The broader callable-slot regression remains separate follow-up work.

The callable-slot fix preserves an existing `PreparedTextValue` in
`CitryRender._render_value`. `Slot.__call__` had already produced the typed
value, but the enclosing simple expression escaped its object representation.
The corrected selection passes 170 tests with one remaining i18n output
assertion. Its static-HTML expectation needs a native browser equivalent;
the test has not been removed. Independent review of the fix is pending.

The i18n test now checks the typed startup data and two distinct binding IDs.
A real Chromium test verifies both translations change from Save to Uložit
while the plain simple-component span retains its text and title. No page
errors were recorded. The raw/simple/capture/cache selection now passes all
171 tests. Independent review of this completed correction remains pending.

Independent review accepted the simple-slot correction and browser i18n
coverage. Static serialization still escapes the preserved text value, and
Vue assembly retains it as data; preserving the typed part does not grant HTML
trust. The three original failures also pass in the reviewer's focused run.

Public-document review separately found and corrected four examples: pending
State writes apply to the next non-GET call, nested State values are read-only,
native child events require declaration and emission, Python cannot generate
Vue expression source through a dynamic attribute, and a declared mapping
kwarg must receive a Python expression rather than a literal attribute string.
The corrected Panel and multi-root ColorPicker/parent examples compile and
serialize through prepared Vue. Final prose and technical re-review is pending.

The next stage must represent opaque HTML as Vue-managed nodes without an
extra element or interpreting the contents as template source. It needs explicit
namespace, multiple-root, security and revision behavior. A wrapper with
`v-html` changes the HTML structure and does not satisfy `<c-raw>` semantics.

Pinned Vue runtime source reveals a production-specific constraint for the
opaque-node experiment. Development `patchStaticNode` compares changed HTML,
but the production `Static` branch only mounts a new VNode. An opaque static
VNode therefore needs a different key when its HTML changes so Vue replaces
the range, or another explicit update primitive. Empty content also needs a
defined empty-node representation rather than null range anchors. Both modes
must be tested; passing only Vue's development runtime is insufficient.

A Chromium proof using both pinned Vue development and production runtimes
passes keyed content replacement, unchanged DOM identity, sibling reordering,
range removal and unmount. Mixed text/element/comment roots,
SVG, table rows and options also work. The empty case only mounts an empty
fragment inside a section and removes that section; empty-to-HTML transitions,
empty placement reordering and direct anchor cleanup still require proof.
Literal braces and Vue event attributes
remain inert. The exact HTML string can serve as the returned Static VNode's
key, avoiding a separate hash field. The helper component itself can remain
mounted. Incorrect `staticCount` values did not affect this mount-only proof;
hydration remains outside its qualified contract.

Before production support, validate the exact opaque HTML payload against the
selected JavaScript/CSP/integrity policies before publishing a manifest or
accepting a revision. A settled-shell scanner cannot inspect active HTML hidden
inside JSON. Use existing policy validators and prove both initial and update
rejection insert and execute nothing. If any policy transforms HTML, fallback
and browser payload must use the same transformed value. Root marker handling
also needs the existing static serializer's exact semantics, including mixed
roots and conflicts; raw bytes must never become Vue template source.

Actual policy probes corrected the initial transformation hypothesis: arbitrary
raw scripts and event attributes are not rewritten by dependency integrity
handling. JavaScript allow/warn preserve them, omit preserves raw content while
preventing Vue startup, forbid rejects them, and strict CSP rejects both raw
scripts and inline event handlers. Production opaque support must preserve
these existing policy decisions, with no claim that integrity sanitizes HTML.

The approved integration uses a reserved helper with an exact `{html}` data
record. The browser validates records and their compiled operand references
before loading assets or mutating a revision; validation inside the helper's
render function alone is too late. Root projection reuses the native output
marker scanner with a temporary absent sentinel, then substitutes validated
marker attributes at the identified root tokens. Collisions reject rather
than silently overriding authored attributes. Current mount behavior uses
`staticCount=0`; future hydration requires separate qualification.

Two constraints need explicit proof during implementation. Initial call-local
security overrides must remain effective on later server revisions. Also,
opaque fragments cannot borrow an opening or closing tag from surrounding
typed content: separately inserting an opening `<div>`, typed children and a
closing `</div>` would produce a different tree. Unsupported cross-boundary
markup must reject clearly. Self-contained malformed fragments and namespace
contexts need browser comparisons before support is claimed.

Browser comparisons confirmed the boundary concern: separate insertions of
`<div>`, typed content and `</div>` produce siblings where the combined HTML
would produce nesting. Browser parsing also closes `<div/>`, omitted `li` end
tags and unfinished comments differently from Python's `HTMLParser`. A Python
balance checker therefore cannot establish this contract. Keep unsupported
forms explicit while qualifying a native check; raw-text/RCDATA parents such
as `textarea` need rejection or their own deliberate representation.

Marker review found that ordinary Vue roots already omit the static
serializer's implicit `data-cid-<render_id>` attribute. Actual CSS-variable
markers come from the extension's requested root metadata. Opaque Vue roots
must match ordinary Vue roots and project those requested attributes, without
reintroducing per-render DOM identity attributes. Static compatibility output
retains its existing markers. Consequently, finding the raw HTML as an exact
substring of the final static fallback is not a valid authentication check:
static serialization may add identity attributes. Validate the typed opaque
payload itself with the selected policies and retain producer provenance.

The native strict-boundary implementation now reuses the existing output
scanner's tokenizer/tree-builder feedback. It accepts explicitly balanced HTML
and qualified SVG/MathML self-closing elements, and rejects omitted/unmatched
HTML closes, non-void HTML self-closing syntax and unfinished comments/raw text.
The Python `HTMLParser` check is being replaced through a Rust export, PyO3
function, wrapper and stub. The HTML-transform crate passes 34 tests and the
PyO3 library checks pass. A coordinated release build is required before the
Python/browser acceptance tests can run against this source.

Also audit callback projection types before declaring LSP migration complete.
The generated `CitryComponentContext.component` currently uses a readonly
unknown record even though the native Vue instance supports reactive member
assignment. Its projected type must preserve known `JsData`/Options members
and distinguish the writable instance from readonly nested State values.
Tests should check actual generated declarations and delegated diagnostics,
not only that the callback's two context-field names are recognized.

The typing implementation is testing a declaration bundle generated from the
pinned official Vue types. The development-only
[dts-bundle-generator](https://github.com/timocov/dts-bundle-generator) 9.5.1
can inline dependency declarations; generation must keep validation enabled
and reject unresolved external imports. The Python LSP package will ship the
checked artifact and its third-party license notices. Python installation and
production rendering must not invoke Node. Before integrating the projection,
real TypeScript diagnostics must resolve the artifact from a clean workspace
without `node_modules`, including paths with spaces.

That bundler fails before validation with the workspace's TypeScript 7.0.2
because it expects a JavaScript compiler API that is not available there.
Its proposed development dependency was removed. The next comparison keeps
only the required official declaration files, metadata and licenses in a
closed directory inside the LSP package. This can retain local declaration
imports without relying on a user's dependencies or adding a second compiler.
Clean-workspace resolution and package-inventory checks remain mandatory.

The declaration-tree approach is implemented and source-frozen for review.
The LSP package contains pinned Vue 3.5.42 declarations, their required
declaration dependencies, exact inventory/hashes and license notices. No new
bundler dependency remains. A clean-workspace TypeScript check resolves the
packaged types without user `node_modules`, accepts supported writes and Vue
helpers, and rejects readonly props, nested/locked State writes and unknown
APIs. The focused LSP selection passes 312 tests; freshness, formatting and
wheel-inventory checks pass. Windows execution remains untested, although
paths are normalized and JavaScript-escaped. Independent review is pending.

The native boundary release build has now installed successfully in the
existing Python 3.12 environment. The first wrapper and opaque browser checks
pass 14 tests. Full opaque integration acceptance remains pending.

Security review found that checking policy overrides only when the initial
page contains opaque HTML is insufficient: a later Events response can
introduce the first opaque value. Until an authenticated app policy is retained
across requests, every revisable Events app must use the engine's JavaScript
and CSP settings. Differing call-local overrides reject at serialization;
applications configure their intended policy on Citry. This restriction is
being implemented with an initial-safe-page/later-opaque-response regression
test, rather than silently falling back to a weaker policy on updates.

Independent typing review found three corrections before acceptance: include
declaration freshness in the ordinary package check, narrow native Vue Options
to the forms the Citry runtime supports, and normalize the generator's license
basenames and inventory paths across operating systems. The generated instance
and State types otherwise passed review. The IDE guide and public Options
documentation must describe these actual runtime restrictions.

Storybook integration exposed a callable-slot forwarding defect in Tabs. The
slot producer retains the authored fill, but assembly loses its placement
context when it enters a selected component definition. The approved fix
carries the originating slot execution into that definition's transparent
output while retaining the physical component occurrence identity. Acceptance
requires the actual Tabs scenario, caller-scoped bindings, distinct repeated
placements, and continued rejection of unrelated render reuse. Relaxing the
identity guard is not an acceptable substitute.

A subsequent exact capture trace superseded that assembler hypothesis:
`SimpleContent.as_slot()` drops the original Slot's `extra` metadata when
creating its forwarding Slot. The selected fix first preserves that existing
metadata, as other slot normalization paths already do. The same acceptance
cases still apply; no assembler context propagation is justified if preserving
the original relation resolves them.

The metadata-copy experiment did not fix Tabs and was reverted. The actual
path does not call `SimpleContent.as_slot()`. Further tracing finds the outer
slot relation intact, but direct capture is inactive while nested authored
fills in the Python-composed content are created. Those fills therefore never
receive placement metadata. Both earlier proposals remain unproven; the next
step is tracing the capture context at that nested render entry before editing.

Root review also reproduced a native boundary-validator defect: HTML
integration points and foreign-content breakout tokens can change the new
element's namespace. Using only the previous current node's namespace wrongly
accepts `<svg><foreignObject><div/></foreignObject></svg>` and the corresponding
MathML case. Native/browser acceptance must cover these transitions and the
actual insertion context before the strict-fragment guarantee is accepted.

The exact Tabs capture boundary is now confirmed: an outlet with a
Python-passed Slot has no authored fill source, and its plain rendering path
suspends direct capture across all descendants. That suspension also prevents
real nested template fills from acquiring their own metadata. The chosen fix
keeps the source-less outer slot unwrapped while allowing its descendants to
capture their authored relations normally. Existing identity checks stay in
place. Focused and broader capture/cache verification is in progress.

Storybook's author verification passes standalone and both Webpack/Vite browser
smoke suites, with eight focused tests passing apart from the separately tracked
Tabs failure. Independent review found one additional lifecycle gap: once
`Citry.fragments.load()` starts, Storybook's abort and deadline no longer bound
the wait. A stalled asset can retain a hidden candidate indefinitely. The fix
must race settlement against abort/deadline, remove the failed candidate to
trigger the public fragment manager's host cleanup, and prove no late promotion.
The stage is not accepted until this regression is covered.

The capture-context correction resolves the actual Tabs rendering exception.
Its remaining Storybook assertion inspects static attributes in a response now
carrying an inert Vue manifest and is being replaced with the corresponding
rendered-control check. A new regression covers repeated Python slot execution,
distinct nested authored fill owners/occurrences, and a caller `v-text` binding
against conflicting receiver JsData. The broader capture/simple/cache selection
passes 264 of 265 tests; the remaining fixture needs the concurrently added
static-run context metadata and is owned by the opaque-HTML change.

The opaque insertion-context restriction must cross component and slot
boundaries. Chromium confirms that `<title><b onclick="...">x</b></title>`
contains only an HTML title text value when scanned in a document context, but
when inserted inside SVG it creates a real HTML `b` with an event handler.
Checking only each definition's local element stack would miss a component
physically mounted under SVG. The approved implementation propagates immutable
physical ancestor context through component and selected-slot assembly, without
creating a separate graph. Opaque HTML rejects under any SVG/MathML ancestor,
including integration points, while a self-contained SVG fragment inserted in
ordinary HTML remains eligible. Local element balance and root-marker depth
remain independent of inherited ancestors. Both origins, c-raw and trusted
values, obey the same context rule.

Root browser verification of the slot correction now passes with the actual
document serializer and Chromium: two Python-passed Content instances each
supply an authored button to Receiver. Content supplies `label="caller"` and
Receiver supplies conflicting `label="receiver"`. Both buttons show `caller`;
clicking the first changes only it to `caller!`, and the browser records no
errors. This independently verifies both lexical scope and per-placement
reactive state. The author is retaining it as a permanent regression.

The final slot correction and typing fixes are source-frozen for independent
review. The slot selections pass 220 direct/prepared/simple tests, 45 typed-cache
tests and the permanent Chromium scope regression. The LSP selection passes
312 tests, and the ordinary browser-client package check now includes declaration
freshness and passes its type, formatting and 54 test checks. The isolated
TypeScript test resolves the packaged declaration tree under a path containing
spaces and rejects unsupported Options forms. Windows execution is still not
claimed. Review must confirm the three prior typing findings are closed.

Storybook now passes all nine focused tests and mounted Tabs control checks in
both adapters. Its timeout regression delays the public fragment provider and
proves retained previous content, removal of the timed-out candidate, and no
late callback. Separately, the production fragment-manager browser test stalls
an actual CSS request and verifies host removal cancels pending startup with
safe late settlement. These are complementary checks of the two layers, not
one purported real-network Storybook test. Re-review is pending.

The corrected native release build is installed. Root rechecked the three
foreign integration/breakout self-closing regressions: all reject, while a
balanced SVG with a self-closing path remains accepted. An actual component
used once under HTML and once under SVG also rejects its opaque title payload
on the foreign placement, confirming context is checked per occurrence rather
than bypassed by definition reuse. Focused author acceptance and independent
review remain in progress.

Typing re-review found that applying TypeScript `Omit` to Vue's Options type
loses official member types through its legacy string index signature and can
discard contextual `this` information. The next correction must preserve the
intact official type while restricting unsupported fields, and verify both
supported Options validation and contextual data/method/computed access. Merely
rejecting the forbidden keys does not establish useful editor typing.

The next bounded core inventory stopped at 20 failures after 612 passes, so it
is not a full-suite result. It identifies three next groups: one test assumes
an internal attribute-output cache must be populated on the selected render
path; two canonical render fixtures pass executable `@click`/`@change` strings
through dynamic c-element attributes that the prepared target rejects; and
the remaining failures exercise the retired client-props syntax as successful
behavior. The first needs an assessment of the cache behavior it actually
protects, the fixtures need a deliberate Vue-compatible authoring update, and
the props tests need equivalent native-binding coverage plus rejection cases.
Do not classify all three groups as stale string snapshots.

Opaque review found an omitted physical-context argument in the optimized
component-run path. Ordinary calls pass the ancestor stack, but grouped loop
members currently do not, so foreign placement checks can be bypassed by a
repeated component call. The fix must cover that optimized path and add a
loop-under-SVG/MathML regression with an ordinary-HTML positive control before
acceptance. No native rebuild should be needed for this Python correction.

Independent review now accepts the optimized-run context fix: the keyword
argument carries the physical stack without changing inherited root-marker
eligibility. Six regressions cover both opaque origins under SVG and MathML,
and HTML positives verify that the optimized call-run path remains selected.
The relevant combined selection passes 292 tests. Storybook and Tabs are also
accepted. The final injection typing correction is awaiting its last review.

The next core inventory, excluding the already identified groups, reaches
838 passes before another 20 failures. It separates static void-tag formatting
expectations from unsupported dynamic-element metadata, a public Slot call
returning a private typed text object, and pure-component memoization no longer
capturing typed text output. The latter two need runtime contract investigation;
changing their assertions alone would conceal behavior changes.

The learning-funnel author migrated seven pages and their examples, with 70
docs checks and current-runtime counter/props browser probes passing. The docs
Try-live worker still loads the published browser wheel pinned in runtime.json,
so it cannot qualify unreleased Vue examples. Keep deployed pins on public
artifacts and qualify a local candidate browser wheel separately; a shared
definition URL is normal bundled delivery, not evidence of a bad definition.
Review also found the CRUD lesson's native child event called a Python handler
as if it were a Vue method. That call must use `$sendEvent`, and a mounted
server-flow test must verify both filter controls after list replacement.

The final injection typing fix is independently accepted. The learning CRUD
call now uses `$sendEvent`, and a permanent local ASGI/browser test covers
invalid-row error retention, sibling save isolation and both filter controls.
Its two strict expected failures identify real remaining runtime work, not
accepted behavior: component-targeted Dispatch currently fires only on document,
and a handled server EventError reaches Vue as an uncaught handler rejection.
These expected failures must be removed when the runtime fixes land.

For Dispatch, prior art is `actions.Dispatch` and the Events specification's
single canonical root contract, plus the existing live occurrence/generation
registry in `_vue/client.js`. The host currently ignores the supplied source
argument. Resolve that exact live occurrence and dispatch one bubbling event
from its current Vue-managed root, preserving exact event names and avoiding
duplicate document delivery for multiple roots. Use Vue's retained VNode/DOM
references, not a recreated HTML ownership graph or selector scan. Empty/text
roots and delayed retirement need explicit tests before their behavior is
claimed.

The EventError investigation must distinguish declarative `@c-*` requests,
whose failure is already recorded in per-instance error state, from imperative
`$sendEvent` promises that application code may intentionally catch. A handled
validation failure must leave the app usable; unexpected render-transaction
failures must retain their existing failure behavior. Do not suppress errors
globally or change the documented promise contract merely to silence a test.

Dispatch's canonical carrier uses the first connected element reachable through
the current Vue subtree. Static VNodes require their bounded el-to-anchor range,
not a general DOM search. When an occurrence is text-only or empty, its connected
Vue-owned public `$el` text/anchor node is the carrier; DOM events can bubble
from those nodes too. A stale or disconnected occurrence rejects rather than
dispatching globally. This preserves one document observation while avoiding
an unnecessary exception for valid empty components.

Keyed DOM moves restore a still-connected focused control only when focus falls
to the document/body sentinel; a deliberate move to another connected element
wins, while an intentional blur during the same Vue flush is indistinguishable
and may be restored.

Slot investigation found that simply removing its scalar-to-dataclass branch
restores Python string behavior but makes plain slot text indistinguishable from
intentional Markup at restricted SVG insertion points. The chosen bounded
provenance carrier is a private Markup-compatible subtype only for scalar text
escaped by Slot itself. It preserves the public string/Markup operations while
changing the nominal internal type. Consumers may treat it as text only while
it contains no literal `<`; operations that combine it with explicit trusted
markup must follow normal opaque-HTML handling. Tests must cover comparisons,
length, uppercasing, f-strings, concatenation and trusted-Markup composition,
not merely equality with a short string. Session checks and structured slot
relationships remain unchanged.

Native scoped-slot syntax remains an authoring-analysis contract awaiting a
working public integration example. A `NativeChild` probe compiled its slot
but rendered an unresolved component comment. Public docs must not claim that
the component registration path works based only on successful compilation.

The Slot scalar correction is independently accepted. Review confirmed escaped
scalar provenance, string operations, foreign-content text, and the separation
from intentional Markup. The author reports 292 focused checks; these overlap
other selections and are not an additional full-suite total.

The rebuilt Dispatch runtime passes its canonical-root and stale-generation
browser checks, including text-only and empty components. The tutorial's
Dispatch expected failure is removed. Independent review is still pending.
The remaining tutorial expected failure concerns handled server validation
errors. Its proposed correction classifies exact request-failure identities
only after request activity has recorded them, then consumes them only in
automatic declarative handlers. Imperative promises retain their rejection
contract. Argument construction, malformed responses, and render transaction
failures must remain distinguishable from handled request failures.

Pure-body reuse now has explicit replay records for immutable prepared source,
static runs, closing elements, and unbound scalar text. Component calls, slots,
opening elements and context-dependent browser bindings remain live. The author
reports 13 pure tests and 296 focused regression checks passing; independent
review is pending. This restores the existing purity contract after typed
rendering rather than starting another optimization campaign.

Independent review accepts pure replay after correcting one local type
annotation. It also caught a Dispatch traversal error: a multi-root component
whose first element contained children could select a descendant as its event
target. Checking the current element before its children corrects that case;
the browser regression now uses a section containing a span. The corrected
Dispatch and request-failure classification source are accepted by review;
their final browser verification is still in progress. Declarative retirement
cancellation now ends quietly, while the stale action still cannot dispatch.

Final browser verification passes six focused cases: same-page CRUD validation,
sibling save and both filter updates; imperative structured-error rejection;
terminal callback failure; canonical Dispatch carriers; and stale cancellation
without delivery. Both tutorial expected failures are removed. The client
package check also passes all 55 tests, declaration freshness, TypeScript and
Biome. These results qualify the bounded fixes, not the complete migration or
the final framework benchmark cohort.

The learning-funnel sweep found one omitted runnable example, step 8. It now
uses native props, emits, parent data and methods, matching the preceding
lesson. Its mounted example changes Ocean to Forest without browser errors;
the 70 content/config checks pass. No legacy browser authoring remains in
getting-started pages or snippets. Other examples and Events reference pages
are the next bounded documentation batch; the published playground wheel
still requires separate candidate qualification.

Review of the broader Events pages found semantic claims that a syntax sweep
missed: physical ownership ranges, subtree ignore behavior, and interval
polling. Those sections need source-based correction. Ordinary event bindings
also retain debounce/throttle metadata without applying it in the generated
event dispatcher; control bindings have their own working timer implementation.
Event timing and polling therefore remain runtime migration tasks, not merely
documentation renames. Final qualification must include positive timing and
disposal cases so accepted syntax cannot silently lose its behavior.

The first timing correction is limited to ordinary DOM event bindings. Each
live element and binding ID owns its own lifetime, including repeated copies
of one authored site. Capture validated argument data at the event, without
retaining the Event object. Debounce sends the latest captured arguments after
a quiet period; throttle sends on the leading edge without a trailing send.
Retirement, disconnection and changed bindings must cancel pending work.
Immediate bindings retain their existing path. Timed component-boundary
listeners need a separate per-child lifetime and must reject until that exists.
Polling is a subsequent stage with explicit directive metadata; resuming a
visible page starts a fresh full interval without a catch-up burst.

The polling implementation stage is now authorized for ordinary DOM elements.
The existing parser supplies the handler, argument source and seconds interval;
capture must retain that authenticated metadata through direct and cached
rendering. Generated code passes an argument function to the existing private
timing directive so each tick evaluates the current lexical Vue scope. No
ordinary DOM observer or physical range graph is needed. Runtime-spread poll
bindings and component-boundary polling remain explicit errors in this stage.

The first poll waits one full interval. Subsequent ticks skip a binding whose
previous call remains queued or in flight, matching the Events design's
recurring-call rule. Hiding the document cancels timers; becoming visible
starts a fresh interval. Retaining an element through a local reactive update
refreshes its argument function without restarting its cadence. A server
revision replaces its lifetime and starts a fresh interval. Removal, owner
retirement and app disposal cancel work. A document visibility listener exists
only while an app has live poll bindings. Expected server errors use the same
declarative error handling as clicks; invalid client arguments or lifecycle
faults enter the existing fatal error path. Browser tests must prove these
rules, including repeated elements and supplied-slot lexical scope.

Polling source is now frozen for review and execution. Poll-containing cache
artifacts deliberately use live rendering while artifact version 1 lacks this
typed metadata; the cache must not silently replay a binding without its
timer behavior. Existing untimed and timing-only generation retains its
ordinary path. The browser lifetime checks its exact registration again after
argument evaluation and immediately before the deferred send, so an argument
that removes its own element cannot send afterward. Fatal errors stop all app
polls before reporting the error. These are implementation claims awaiting
the focused producer, browser and client checks, not release qualification.

The client build and all 55 client tests pass with the polling code and the
single-map preflight correction. Focused producer checks pass for polling
metadata, runtime-spread rejection, component-boundary rejection, live cache
fallback, and the three quote-preservation cases. A broader two-file Python
run reports 209 passing and 103 failing cases: 99 failures are in the Events
binding test file, most involving its older HTML serialization helper, which
still expects encoded DOM binding attributes. These failures need individual
classification and a deliberate migration of the assertion boundary. Of the
four prepared-capture failures, one new test named
the wrong exception class; the other three exposed a real marker guard bug.
The guard rejected ambiguous Vue attributes even when no root markers existed.
Fix both ordinary and dynamic-element branches, preserving the restrictions
when markers are actually present. Do not hide this by broadening the expected
error messages. A separate new interval test called a nonexistent helper and
needs a fixture-only correction before its focused rerun.

The interval selector passes after correcting its fixture helper. All five
focused marker-guard cases pass, including ordinary and dynamic roots without
markers and rejection with nonempty markers. The browser batch reports ten
passing cases and two fixture failures: the latter define `js_data` without
its required `kwargs, slots` parameters and fail before browser execution.
The passing cases include all four long-delay tests with payload assertions,
ordinary timing, the throttle race, expected-error/Dispatch regressions, and
fatal polling argument handling. Correct the fixtures and add supplied-slot
lexical polling coverage. Strengthen the revision test by updating halfway
through an interval; updating immediately after a tick cannot distinguish a
restart from the old cadence.

Readiness review found no demonstrated timer race in the current host:
`onServerRender` rejects Promise returns, and the owned mount and pre-callback
hooks execute synchronously. The intervening transaction awaits yield only
microtasks; timer tasks cannot interrupt that sequence. A future asynchronous
callback contract would need an explicit poll readiness rule, but this stage
does not add a speculative gate.

Independent review accepts the polling source, cache fallback, marker fix and
single-map preflight change, conditional on the remaining browser fixture
correction. The supplied-slot poll now passes for the caller's initial and
locally updated values; argument-triggered removal and fatal argument shutdown
also pass. The remaining lifecycle test must wait for route interception, not
only Playwright's earlier request notification, and for the bridge to finish
serializing calls from the same owner. Playwright emits those notifications
separately; this is a test synchronization correction, not a timer change.
The binding compiler also now rejects `@c-poll.0s` at its authored location.

The polling stage is now qualified. The four browser cases pass across their
focused runs: lifecycle and midpoint restart, supplied-slot lexical values,
argument-triggered removal, and fatal argument shutdown. Zero and oversized
interval rejection tests pass, as do the producer/quote and
five marker-guard cases. The rebuilt client passes its 55 tests and checks.
This does not clear the separately recorded broader Events test migration
backlog. The next implementation stage adds target placement metadata and
proves existing self-updates before enabling cross-component targets.

Timing teardown uses a generated private Vue directive only on timed elements.
The first attempt exposed a native metadata requirement: `directive_runtime_identity`
already recognizes the generated control directive, but did not recognize the
new timing directive. Add the timing name to that same native classification
and reuse its existing directive site/signature output. This avoids consuming
public VNode lifecycle attributes and preserves directive-removal validation.
The audit covers the native compiler and regression, Python generated templates
and signature validation, and runtime directive registration/disposal. The
PyO3 function surface, template grammar, five host-language compiler interfaces
and protocol shapes do not change. Native and browser artifacts must be rebuilt
before acceptance tests; declaration/runtime/cache versions remain 1.

The scheduler is shared with control debounce and limits each native timer to
the signed 32-bit maximum. Monotonic elapsed time counts toward the requested
delay, including a suspended tab; long delays must not overflow into immediate
execution. Four fake-clock browser cases now pass for ordinary event and
control debounce: both an exact two-chunk deadline and a first chunk delayed
past the deadline. These execute the built scheduler without long-running
waits. Independent review accepted the scheduler proof and required explicit
handler, argument and State-update assertions. Those assertions are now added
and reviewed; the final rerun waits for the polling runtime build.

The rebuilt native compiler passes its directive regression and all ten
selected producer cases. The client build and its 55 Node tests pass. All
twelve selected browser cases now pass, including the held dynamic tag/key
revision cases, slot scope, expected server errors, and ordinary event timing.
Three test fixtures needed corrections: declare `js_data` as a method, omit
an unnecessary dynamic key from a stable two-item timing fixture, and advance
the throttle test clock far enough to distinguish an incorrectly released
window. Dynamic user keys on elements with lifecycle directives remain a
separate authoring limitation; removing that fixture key does not qualify them.

A subsequent source review found that generated event attributes could lose
authored double quotes. The Python generator now uses one HTML attribute
serializer for leaf, direct DOM and component-boundary bindings. The helper
escapes the attribute representation, while the Vue compiler must receive the
original decoded JavaScript expression. Independent source review accepted
all generation paths and their acyclic imports. Two producer regressions pass;
the timing assertion encountered an in-progress polling generator change and
will be rerun after that source freezes. The preceding browser results predate
this Python fix.

Independent prose review accepted the corrected Events timing, error and State
documentation. It now distinguishes handled server validation responses from
client/protocol failures, identifies the next non-GET call as the carrier of
pending State writes, and explains that nested State values are read-only
views updated through whole-field replacement. The new polling description
remains conditional on its browser qualification.

Production target review found a prerequisite beyond browser target lookup.
The current prepared producer roots a response at the caller occurrence
identified by the request. A different server render ID does not give that
producer the target's stable placement occurrence, which currently lives in
the browser registry. Widening the client allowlist alone would produce a
subtree rooted at the wrong occurrence. Addressable target handles or another
explicit placement contract must be proven before enabling cross-component
targets. Whole-tree request maps and an implicit process-local server registry
are not accepted solutions.

Further inspection found no demonstrated occurrence IDs embedded as literals
in compiled render functions: component calls obtain them from prepared data.
Translating explicitly typed occurrence references in the browser is therefore
a candidate, subject to extension-owned reference handling. Generic string
replacement in application data, server render IDs or signed tokens is not
valid. The current child IDs include a hash of their parent ID, so merely
hashing an incoming ID with the target ID would reset existing descendants on
the first cross-component update. The current wire data also loses explicit
keys for grouped calls. A candidate is a parent-independent placement key on
each occurrence, used to match children under the translated parent before
allocating new IDs. Independent review accepts this for a first bounded stage:
cross-component morphs whose root has the same component type as the target.
Class-changing roots remain rejected because the retained parent definition
and registered Vue component still name the original type.

For authored calls, derive the placement key from the source site, component
type, explicit key or unique unkeyed site, and slot placement route. Grouped
calls retain their explicit keys in this derivation. Python-composed children
need a correction: their current ordinal comes from the whole render session,
so an ancestor or sibling can change it between a whole-page render and an
isolated subtree render. Assign their positional ordinal within the physical
parent and placement route during assembly. Enforce unique placement keys
within each physical parent. Supplied fills retain their physical receiver as
parent; their lexical data owner does not participate in the placement key.
An independently prepared root has a null placement key. When applying that
root at an existing nested component, retain the target's original placement
key and parent ID. This rule also applies to current self-targeted updates;
the new field must not invalidate those updates before cross-target support
is enabled. Every nonroot occurrence requires a nonempty placement key.

Translate the incoming root to the selected target, then match descendants
parent-first using placement key and component type. Retain matching IDs and
allocate collision-free IDs for new children. Core translation visits only
declared reference fields. Before extension staging, each installed plugin
must translate its own validated occurrence references. For i18n these include
provider IDs, occurrence-valued parents, barriers and requirement owners; its
server provider identities and arbitrary application values remain unchanged.
The implementation must enumerate these fields against the current schema,
validate the translated tree, and prove first-update retention, keyed reorder,
Python composition, supplied-slot scope, new/removed children and abort behavior.
Protocol and cache versions stay 1 throughout this pre-1.0 migration.

The placement-metadata foundation is now source-frozen for review. Both strict
and trusted Python occurrence constructors carry the new field; direct
assembly checks its parent-local uniqueness, and browser validation requires
it on every occurrence. Child IDs derive from the parent ID and placement key.
The browser validates an incoming isolated subtree before restoring its root's
existing parent and placement. Cross-component targets are still disabled in
this foundation stage. New tests cover whole-page versus isolated Python
composition, keyed grouped-call reorder, supplied-slot physical parentage,
invalid/duplicate metadata and existing self-target subtree application.
Routine constructor and handwritten browser-fixture updates are separate from
the substantive implementation, with builds deferred until both edits freeze.
No Rust, PyO3, grammar or host-language compiler surface changes are involved.

Foundation qualification passes 132 Python tests and all 56 client tests after
regenerating the runtime. Independent source review accepts the identity
derivation and validation. The new JavaScript self-update test proves stored
placement restoration through application; it does not mount a real target
and is not a claim of DOM instance retention. A wider browser run reports 15
passing and 15 failing cases. The failures expose older fixtures that omit
the fragment module or required opaque-HTML definition metadata, plus a real
serialization fixture that still searches server HTML for a runtime-created
stylesheet marker. Correct their setup while preserving the intended lifecycle,
ownership and rejection assertions, then rerun before calling the browser
qualification complete.

After those fixture corrections, the same browser batch passes 21 cases and
fails nine. Read-only inspection identifies a stale compiler helper contract,
a negative graph fixture whose copied placement key now fails an earlier
validation, and stylesheet fixtures that do not model the bootstrap asset
contract. Correct those specific fixtures without weakening their original
assertions. Browser qualification remains pending.

The nine-case rerun passes seven cases. Two remaining fixtures require semantic
review: one expects a removed internal integrity option to reject external
styles, and one does not actually trigger the terminal lifecycle error whose
stylesheet cleanup it intends to test. The stylesheet identity fixture now
separately tests independent apps and conflicting descriptors within one app,
matching current app-scoped stylesheet ownership. The Python address run passes
45 cases and fails four new fixtures that pass `transparent` as a metaclass
keyword instead of declaring the component attribute. Correct those fixtures
and rerun; neither result establishes a production regression by itself.
After correcting the four class declarations, both Python address test files
pass all 49 cases. The browser coordinator implementation can build on that
qualified Python foundation; the two asset/lifecycle fixtures remain open.
Ruff lint and format checks also pass for the four Python foundation files
after routine grouping, import-order and formatting corrections.

The terminal-fixture investigation identified a separate runtime defect.
When the initial render reads a missing `js_data` key, it cannot subscribe to
that key's getter. A later revision installs the new getter and publishes data,
but an unchanged render definition has no dependency that schedules a render.
Add a focused regression for an initially missing field introduced by a server
revision. The proposed correction schedules a retained instance update when
the server-data key set changes, after publishing its data and within the
existing flush before callbacks. Unchanged key sets retain the current fast
path. The stylesheet cleanup fixture should trigger its intended failure
explicitly and keep the independent new-key regression separate.

Independent review confirms the bounded scheduling correction: flag retained
records whose server-data key membership changes, publish their live data,
then request their Vue update before the existing flush. Added and remounting
instances already render through mounting. The integrity fixture should follow
the existing asset contract: external integrity is optional, supplied values
are validated, and owned assets receive digest integrity. Preserve those
assertions together with nonce rejection and per-app URL identity checks.

The Events binding test inventory separates migration work by assertion
boundary. Successful cases that decode encoded HTML attributes should inspect
prepared bindings and preserve event names, arguments, modifiers, State fields,
ordering and lexical ownership. Existing validation, source-location, raw-text
and malformed-attribute checks remain independently useful. Runtime spreads
and component-boundary behavior require their own capability tests; do not
turn unsupported cases into passing HTML-fallback tests. Assertions against
the physical ownership graph must move to current typed relationships. This
inventory guides the later test migration; it is not a claim that all these
features have already passed the native browser path.

The same source audit found a remaining internal conversion to examine during
that migration: Events compilation creates both typed bindings and encoded
attribute copies, which the prepared path then filters out. Runtime-spread
validation still consumes parts of the encoded representation, so deleting
it requires migrating that validation deliberately. Prefer a single typed
binding representation once its consumers and tests are accounted for; no
performance saving is claimed for this pending cleanup.

Cross-component targeting review found that `render_to_occurrence` also maps
transparent Python frames to their enclosing browser occurrence. It is not a
one-to-one address table and must not be inverted to choose server targets.
Record a canonical render address separately when creating each occurrence;
selected transparent roots need the same explicit treatment. Production
bootstrap and revision validation must reject duplicate addresses and a
disagreement with an occurrence's Events context.

For a selected transparent root, the canonical address is the render ID of
the frame that creates that root occurrence. Nested transparent frames remain
aliases only. Selected transparent roots cannot define Events or State, so an
Events context attached to one is invalid. For ordinary occurrences, reject
multiple Events records resolving to the same occurrence and require the
record's render address and component class to match that occurrence before
attaching its credentials. The Python address foundation is being implemented
separately from enabling browser cross-component targets.

Review of that foundation caught an overly narrow Events selection filter:
selecting only canonical render IDs silently ignored an invalid record for a
selected transparent alias. Select records using the broad assembly mapping,
then reject disagreement with the canonical address during attachment. Records
outside the selected assembly remain excluded. Also explicitly reject an
Events context for a transparent class or a class without Events; do not rely
on a missing descriptor to produce an accidental failure.

The corrected Python address foundation has passed independent source review;
its focused execution gate remains pending. Address validation in the browser
must distinguish generic prepared-tree tests from production Events hosts.
Production serialization emits an address for every occurrence, even without
Events. A generic tree may omit all addresses while it has no Events; partial
coverage is invalid. Activating Events, including lazy activation after a
revision, requires a complete validated address table. New server renders can
issue new addresses: the immutable target handle protects the old instance
until commit, after which the accepted snapshot supplies the current addresses.

Replacing an ancestor can deliberately retire the component that sent the
event. The accepted transaction must cover removed instances as well as
instances expected to remount, using exact instance and generation checks.
Otherwise retirement cancels the transaction applying that replacement.
Preflight must also prevent later source-bound actions from using a source
that the replacement retires. ID translation must restore canonical ordering
of replacement records, remount IDs and stylesheet owner IDs, while preserving
component call order. Application values and signed server tokens are opaque;
translation must never recursively replace arbitrary matching strings.

The reviewed first cross-target stage accepts one same-type component Render
per response. Before applying State actions, synchronously validate the target,
renderer, morph operation, isolated input, translated references and plugin
translation capability. Capture the app, occurrence, generation, render
address, type and revision in an immutable target handle. Recheck that handle
and the caller after asynchronous preparation and immediately before commit.
Asynchronous asset or plugin preparation failures retain the existing State
commit behavior; deterministic targeting errors must fail before State changes.

For a strict ancestor target, reject source-bound State or Event actions after
the Render, and earlier such actions with a positive delay or without awaiting
completion. Synchronous awaited actions before the Render remain supported.
This conservative restriction avoids relying on an instance that the accepted
replacement can retire. Track exact old records for both removals and expected
remounts when allowing an accepted transaction to complete through retirement.

Plugins translate their declared occurrence references with a pure synchronous
hook returning a detached payload. Its resolver rejects unknown incoming IDs.
Reject a plugin without that hook when IDs actually change; ordinary plugin
revision validation still runs afterward. Match existing children by physical
parent, placement and type. For unmatched children, reuse incoming IDs only
when globally free within the app, otherwise allocate from an attempt-local
namespace. Aborting preparation must not advance accepted app allocation state.
Production call records require their key to equal their child ID before both
fields are translated. Markers, class-changing roots and multiple Render
actions remain subsequent stages, rather than implied support in this step.

The first browser coordinator implementation is source-frozen for independent
review while mounted-target tests are added. Its synchronous response plan
carries a target handle and translated envelope into asynchronous preparation.
Root review required normal deterministic validation before State hoisting,
separate tracking of occupied app IDs and reserved incoming IDs during
allocation, and the validator's code-unit ordering after translation. These
corrections are included in the review candidate. Generated-runtime build and
behavioral qualification are separate gates; cross-target support is not yet
reported as qualified.
The client build, official Vue type-surface check and TypeScript check pass for
this candidate. Runtime and i18n generated assets were rebuilt together.
Behavioral tests and independent runtime review remain pending.

Independent review found blockers in that first candidate: the bridge still
enforced its self-target restriction during application, stylesheet retirement
used the caller subtree, and generated IDs did not satisfy the server's
occurrence-ID grammar. Allocation also failed to reuse otherwise free incoming
IDs. Some deterministic extension and lazy-asset checks still happened after
State hoisting. The ancestor rule must cover all State actions because their
execution checks the caller even when they name another State target. Correct
these together and rerun review before claiming cross-component support.

Further review found that extension normalization returns wrapper copies, so
translation must assign each translated extension back into the outgoing
envelope rather than changing only the temporary wrapper. Address validation
must cover the combined retained and incoming app, not just the isolated
subtree. Require complete addresses when Events activates, including lazy
activation, and reject collisions with retained occurrences before State
changes. Cross-app address reuse remains valid because lookup is app-scoped.

The consolidated fix plan shares one synchronous candidate validator between
response preflight and later preparation. Before State mutation it validates
the combined address table, installed extension set and schemas, extension
asset ownership, lazy type/asset permissions and existing or incoming asset
identity collisions. Check extension schemas before invoking translation hooks.
Render addresses follow the public lowercase identifier rule; newly allocated
browser occurrence IDs follow the server's `citryOccurrence` plus alphanumeric
rule so a newly inserted child can send its next event successfully. Required
proofs include that second event, actual i18n reference translation, stale
targets during asynchronous preparation and deterministic rejection with zero
State commits. Exact-record retirement tracking passed the source review.

Narrow re-review accepts the six functional, translation and address fixes.
One pre-State gap remains: asset normalization alone does not detect unseen
assets forbidden by lazy-loading policy or URL identity conflicts. Share a
synchronous asset-candidate validator using the same app-scoped keys and
identity rules as the loaders, checking both live records and duplicates within
the response. Enforce the global component-asset policy only on component
assets; extension assets retain their own policy. Loader checks remain useful
after awaits because shared resource state can change. Focused behavioral
tests run against the frozen candidate while that correction is prepared.

The two focused Node preflight tests pass. The three mounted-target tests stop
before browser setup because their fixtures read `CitryElement.id`; component
IDs are assigned during rendering. Capture the actual target ID from the
rendered component and rerun those tests without changing their behavioral
assertions. This setup failure provides no browser targeting qualification.

After repairing ID capture, root review found another fixture mismatch: Vue
attribute expressions referenced values supplied only through Python
`template_data`. Use server attribute bindings for those static values.
The keyed-retention proof should check actual DOM/instance identity and local
Vue state; an externally edited input controlled by a `value` prop can reset
during patching without any remount. Correct the fixtures and stop the targeted
run before treating their setup failures as runtime evidence.

After rebuilding the corrected candidate, all three focused mounted-target
tests pass: sibling replacement, a no-Events target retaining keyed DOM nodes
and Vue instances, and accepted ancestor replacement removing its caller.
The run uses fail-fast reporting and makes no broader qualification claim.
Asset/lifecycle fixture rechecks and the remaining stale-target, plugin and
new-child round-trip falsifiers remain separate gates.

The two corrected asset/lifecycle fixtures also pass: optional external SRI,
valid and invalid explicit integrity, nonce rejection, per-app isolation,
same-app identity conflicts and per-app stylesheet retirement on intentional
callback failure. Independent review accepts the final asset validator and
incoming-ID correction without a functional blocker. Async preparation still
duplicates some policy checks; reuse the shared candidate validator there
while retaining loader checks for changes during awaits. Required adversarial
targeting proofs remain pending, so this is a bounded acceptance rather than
full Events migration completion.

Two follow-up changes are source-frozen separately for review: asynchronous
preparation now consumes the shared asset validator's normalized records, and
retained instances with changed `js_data` key membership request a Vue update
after data publication. A dedicated regression checks a previously absent field
with an unchanged definition. A second dedicated test exercises an inserted
child sending its own next Event. Neither has been executed yet. Existing
handwritten Events fixtures also need complete render addresses and valid
occurrence IDs; migrate typed references without changing application data or
the negative condition each test is intended to check.

Independent review accepts both follow-up source changes and their regression
designs. The generated i18n translator also has a direct contract test, but it
does not by itself prove coordinator persistence: a separate real-host test
must observe translated references reaching plugin revision preparation.
Otherwise the earlier temporary-wrapper bug could recur while the direct
translator test continued to pass. Test execution for these additions is still
pending while their dedicated module is completed.

The first dedicated-module run passed one case and stopped in the real-host
harness before preflight because its factory interception did not run.
Generated Events exports are getter-only; wrap the global namespace and
delegate to the genuine factory rather than assigning that export. The stalled
plugin test also needs an explicit hook-entered handshake before removing the
target, so it proves the post-await check rather than relying on microtask
timing. Both harness corrections are frozen for rerun; production is unchanged.

The rerun passes all four dedicated tests: direct i18n translation, real-host
translation/persistence and asynchronous target invalidation, an inserted
child's next Event, and the unchanged-definition `js_data` key addition. The
four migrated loader/cancellation/disposed-app/lazy-bridge fixtures also pass.
Together with the earlier three mounted-target and two asset/lifecycle tests,
these establish the bounded paths described above. A final real-response test
will cover partial addresses and collision with a retained sibling while an
immediate State action is present, proving no State or revision publication.
The full client check is the next integrated gate.
That client gate now passes: official Vue type-artifact check, TypeScript,
Biome and all 58 Node tests. Two files required formatting-only corrections;
no behavioral change was made to obtain this result.

The first broad run collects 73 browser cases and stops after 36 passes at an
old script-node-presence assertion. Loaded script elements are removed after
execution; the fixture must wait for and assert its recorded execution effect,
while retaining the stylesheet-lifetime assertions. Independently, review
found the immediate-State test observed a frozen occurrence snapshot rather
than the host's mutable context. Strengthen it by proving the response contains
a new State token, then checking that a second real request still sends the
original token after rejection. Passing the earlier snapshot assertion alone
does not establish that no State commit occurred.

The strengthened State-token proof passes both address cases and has independent
review acceptance. The subsequent integrated run passes all 73 tests across
the default Events, dynamic-element, i18n-plugin and dedicated-targeting browser
modules. Together with 58 client tests and 49 Python address tests, this
qualifies the bounded same-type component-targeting stage and the `js_data`
key-shape correction. Marker targets, multi-Render transactions and the remaining
Events binding migration are still separate work. No full repository or final
framework benchmark qualification is implied by this gate.

The next Events-binding stage starts with tests only. Assemble typed render
output, select its actual owner occurrence, and inspect `eventBindings`,
`pollBindings` and `controlBindings`. Assert the real owner type; do not rebuild
the discarded HTML `cid` field. Use the compiler input template when checking
directive placement or grouping, because owner tables deduplicate repeated
sites. Runtime State spreads already have a typed path; runtime event/poll
spreads and dynamically selected element Events remain separate capability
gaps rather than silently weakened success tests.

Encoded carrier removal follows only after its consumers migrate. Those
include final control/type validation, attribute-hook candidate routing and
prepared capture/filtering. The JavaScript policy must receive a typed active
Events requirement before HTML markers disappear, preserving `forbid` behavior
when dependencies are ignored without treating an unused Events declaration as
active behavior. Cache metadata is already typed. Reserved-prefix checks are
namespace hardening and need not disappear with the encoded representation.

The first test-only batch converts representative literal Events, controls,
polling, argument-text, authored Vue passthrough and source-offset cases to the
typed assembly helper. All 18 selected cases pass. Generated binding IDs are
checked independently, and exact semantic dictionaries exclude those generated
IDs explicitly. The helper and assertions remain under independent review
before mechanically migrating further supported cases. Runtime code and the
held spread/dynamic-element behavior are unchanged.

Review requires the helper to use normal `render_prepared` so it exercises
production leaf selection, and to select the actual root occurrence before
asserting its type. Preserve the owner-table lookup invariant by checking each
map key equals its binding ID. Same-element ordering must inspect the generated
start tag's Events directives; the number of attribute projection spans does
not prove directive placement. Apply these test-strengthening corrections
before expanding the migration. The existing 18-pass result covered the
direct-path helper and is not a substitute for the corrected production path.

The corrected normal-path helper passes all 18 cases, Ruff lint and formatting,
and independent re-review. Mechanical migration of further supported literal
and static assertions is now authorized. Runtime spreads needing a behavior
decision, dynamically selected element bindings, and the encoded-carrier
contract tests stay separate until their production work is ready.

The expanded mechanical batch passes 66 newly converted cases plus a helper
negative check, with Ruff lint and formatting clean. It covers timing defaults,
key filters, raw-text and verbatim regions, static form controls and resolved
input types. That test-only batch held the static `<c-element is="input">`
case because normal capture rejected the control as holding no value. The
production correction below addresses that failure.

The subsequent production correction gives a typed element's shared attribute
hooks its actual selected tag. Static `c-element` controls therefore validate
as their output element; legacy text-prefix inference cannot override that
typed tag. The final control check runs after all hooks and preserves runtime
State metadata authentication. Browser bindings that can change an input's
type defer to the existing live browser classifier, including longhand,
shorthand, modifier, object and dynamic-argument forms. An unrelated binding
does not disable static type validation. The 21-case focused suite passes,
with Ruff lint and formatting clean. Independent review remains pending at
this checkpoint. Dynamically selected `c-is` bindings remain separate work.

Independent review subsequently accepted that control-validation stage,
including the typed-tag guard, dynamic-type predicate and import layering.
The result establishes input-type deferral and live validation, not full
editor support for every shorthand spelling. The original static `c-element`
assertion now uses the typed helper, and its positive and two negative target
cases pass with Ruff clean.

The next production change validates typed State controls after the complete
attribute-hook chain. Events currently validates within its own hook, so a
later extension can change the input type after that check. Reuse the existing
target and control validators over the final tag, final attributes and merged
typed controls. Preserve the authenticated runtime State carrier and ordinary
attribute fast path while making this correction independently of carrier
removal. Focused checks must cover later-hook type changes, runtime State
spreads, forged carriers and ordinary attributes.

Carrier removal also needs to preserve JavaScript policy behavior. Compute
active binding facts from selected render output, not declarations or the
union of possible conditional branches. Feed those facts to policy checks
before serialization hooks. Omit-mode fallback diagnostics currently inspect
settled HTML; their replacement remains under review so removing the carrier
does not silently remove those warnings. No policy change is authorized by
the test-only migration.

Independent review selected a call-local diagnostic attribute for omit-mode
fallback checking. The serialization call allocates an unpredictable attribute
name and passes it to the policy scan. The serializer adds it only to typed
openings with event or polling bindings.
Omit-mode leaf serialization materializes selected typed parts so the opening
retains that information. Other modes keep the existing leaf formatting path.
State controls remain managed-JavaScript requirements but do not gain a new
handler-only fallback warning. Runtime opt-in for an Events declaration also
stays separate from the active-binding facts used by policy enforcement.

The final policy scan recognizes only its own exact diagnostic attribute. It
uses the existing conservative fallback rules and collects attribute byte
spans during that scan. Remove those spans from the returned HTML before CSP
and script-integrity processing; later validation must inspect the cleaned
bytes. Handle attributes moved, duplicated or normalized by serialization
hooks. If the private marker remains outside removable attribute spans, reject
serialization instead of leaking it. This design does not claim more accurate
browser form ancestry than the existing output scanner provides.

Carrier removal must prove selected conditional and loop behavior, cached and
direct openings, Unicode byte offsets, no diagnostic leakage, hook changes,
and composition with CSP/integrity. Forbid checks run from typed facts before
hooks, so deleting a diagnostic attribute cannot bypass that policy. The
ordinary allow-mode path must not allocate diagnostic markers or reconstruct
typed leaf parts for fallback checking.

Review also identified a selected `js_data` policy gap: ignoring dependencies
could hide the runtime requirement from final HTML validation. Nonempty data
actually produced by a selected component must therefore contribute an active
policy fact before HTML hooks, so forbid mode rejects it even if a hook returns
plain HTML. An unused Events declaration retains its separately tested
exception. Component JavaScript dependencies remain under dependency-policy
inspection. Marker cleanup also needs to preserve the separator after a tag
name when a hook places a quoted marker directly before the next attribute.
Deleting the marker must not join the tag name to that attribute.

The focused policy suite passes 20 cases after fixture corrections. It checks
selected branches and empty loops, actual cache replay, repeat serialization,
unused Events declarations, active State bindings and `js_data`, changes made
by HTML hooks, marker cleanup and CSP/integrity composition. Analysis reads the
selected leaf tables without reconstructing typed leaves. It also derives IDs
from its existing selected-render list instead of walking the tree again.
Omit cleanup joins retained byte slices once. Independent source review has
accepted this prerequisite; the existing security/scanner regression modules
and final lint cleanup are the next gate before carrier removal.

That prerequisite gate is complete: the 20 focused tests and 133 existing
serialization-security/output-scanner tests pass. The regression run includes
one expected warning from an intentional inline-handler fixture. Ruff lint
and formatting pass for all five touched files. Encoded carrier removal now
proceeds against this qualified policy behavior.

The typed transport removal is implemented but still awaiting its focused
test gate. Independent review found that a spread containing both a forged
private control attribute and a valid State binding could overwrite the forged
value before validation. It also found inconsistent reservation of that name
in plain HTML rendering. Reject the reserved name, ignoring case, before
creating authenticated metadata in every rendering path. Authentication on
prepared capture and an exception on accidental string conversion provide
additional checks. These findings do not establish an executable-source
bypass, but accepting the collision would make validation depend on attribute
order. The cache artifact version remains 1 because this format is new and
unreleased on the local migration branch.

The first focused gate exposed a real typed-control loss in the leaf renderer.
Two attribute-dictionary shortcuts admitted control-bearing nodes after the
attribute carrier was removed. Their dictionary results omitted typed control
metadata, leaving a compiled directive whose ID was absent from the prepared
table; cache replay then also lost the directive. Both shortcuts now exclude
nodes with typed controls, as they already exclude event and polling bindings.
The regression asserts a real cache hit, fresh render IDs, and retained event
and control semantics. Its assertions remain unchanged. The corrected source
passes all 40 transport/control tests and 153 binding-security,
serialization-security and HTML-output tests. One expected warning comes from
an intentional inline-handler fixture. Ruff lint and formatting pass for all
12 affected production and test files. Independent review accepted the source
and the cache-hit proof. This qualifies typed transport removal, not the whole
migration or a new performance result.

### Runtime Events supplied through Python attribute spreads

Restore runtime event and polling spreads in bounded steps. Python-provided
strings must not become Vue template expressions. The first supported subset
contains a handler name or a handler with empty parentheses. Validate handler
names, timing options and modifiers using the existing Events rules, then
carry the result as authenticated typed data. Capture consumes that metadata
after attribute hooks. Authored template expressions retain their separate
source provenance.

Eligible spread sites use a dedicated `v-citry-runtime-events` directive to
install and reconcile listeners from the typed data. The existing timing
directive continues to manage authored listeners' timers. Sites with no runtime
bindings return an empty list. Ordinary elements without eligible spreads need
no new instrumentation. Reuse the existing dispatch and timing machinery, preserving
automatic form collection for a handler without arguments. Each actual DOM
element owns its listener lifetime, including repeated instances of one loop
site. Updates and unmounts cancel obsolete work; unrelated updates must not
reset an already consumed once-listener. Key filters, self and once
need browser comparisons with authored bindings, since native once-listeners
can otherwise consume an event before its filter accepts it.

A later step may accept an explicit strict JSON object as arguments. It must
distinguish no arguments from an explicit empty object, reject duplicate keys
and unsupported numeric values, and provide independent argument data for each
invocation. JavaScript expressions in Python-provided strings remain errors;
authors can place those expressions directly in the template. No runtime
evaluation or browser compilation of spread values is proposed.

The v1 cache artifact does not represent runtime-origin bindings and their
per-site lifetimes, so eligible runtime-spread sites execute live. Decline
caching even when the current spread produces no event, or a cached empty
result could suppress a later binding. The first implementation covers
handler-only DOM events; polling follows separately. Acceptance checks include
forms, modifiers, loop instances, server revisions, supplied-slot lexical
ownership, forged metadata and proof that runtime strings never enter generated
expression source. The polling follow-up also checks timer cleanup.
Dynamic element selection and component-boundary spreads remain separate
integration cases.

### Validate runtime event references before publishing a revision

Prior art: the native Vue compiler already authenticates element binding spans
and returns element site IDs (`citry_vue_compiler/src/lib.rs`,
`ElementBinding`, `validate_element_binding` and `ElementMetadata`). Python's
leaf compiler knows each conditional and loop's prepared-data scope. Direct
assembly contains only selected server output. Definition assets already carry
other compiler-checked sites through `CompiledRender`, `DefinitionAsset` and
the browser definition registry.

Checking a runtime listener's data during Vue rendering is insufficient for
atomic validation: the candidate snapshot may already have been published.
Add an optional runtime-events binding key to element-binding declarations.
The native compiler must match it to exactly one generated directive with its
exact helper expression, without directive arguments or modifiers. Undeclared
generated directives and mismatched spans or keys reject compilation.

Definitions also carry runtime event sites: a native-confirmed directive site ID, its
binding key, and Python-generated steps to reach selected prepared data. A
branch step tests a conditional index; an each step visits loop records; an
empty step selects the loop's empty branch in its parent scope. Direct sites
have no steps. The native Vue AST path is not a prepared-data path and must
not be used as one. Include these declarations in definition identity and
carry them through every asset and registration path.

Initial and revision preflight follows only declared steps, validates terminal
ID lists and exact runtime binding specs against their owner's declared
handlers, and checks that referenced IDs equal the runtime entries in the
binding table. Multiple placements may reference one identical spec. Empty
loops and inactive branches contribute no references. Wrong shapes, unknown
IDs, authored IDs in runtime lists, unreferenced runtime entries and invalid
handlers reject before State or snapshot publication. Keep the listener's own
reference and liveness checks as an additional boundary.

This explicit metadata avoids scanning arbitrary JSON for reserved-looking
keys. The binding declaration changes the Vue compiler's JSON input, not the
Citry template grammar or its five host-language code generators. Audit the
native input/output, Python compiler client and records, protocol serialization,
asset registration, browser validators and tests together. Confirm the PyO3
entrypoint and stub still pass this JSON contract without a signature change;
update them if the audit finds an exposed shape that changes.

Tests must cover initial loading and revisions, selected conditionals, loop
empty branches, nested scopes, shared sites with different row handlers,
malformed references and prototype handler names. A rejected revision paired
with immediate State must leave the token, state, revision and DOM unchanged.
If an attribute hook creates a runtime binding at a site that was not compiled
as eligible, raise explicitly; do not silently drop the binding or invent a
new directive after compilation.

The native declaration tests pass (19 Rust tests), and the release-mode
editable build succeeds with Python 3.12.13 in this worktree's environment.
Independent source review accepts the declared-route checks and direct
`applyEnvelope` validation against registered definitions. The client build
and all 61 Node tests pass, together with TypeScript, lint and bundled Vue
type checks. Browser qualification remains pending; these results do not
prove rejection before State changes in a running browser.
The first browser case, mixing an authored timed event and a runtime event
on one element, exposed loss of the button's authored `id` attribute.

The comparison with general assembly identifies the failure: the leaf compiler
omits authored attributes from a spread opening, but its typed evaluation path
copies only data-origin attributes. Capture correctly retains an unchanged
`id` as a source-origin attribute, so neither output channel emits it. The
correction must preserve selected ordinary attributes using their parsed
values, respect spread overrides and removals, and keep executable attributes
on the checked source path. Regression coverage checks equivalent selected
attributes on the leaf and general paths rather than changing the browser
selector to hide the missing `id`.

The correction passes all 20 tests in the runtime-binding Python module,
including preserved, overridden and removed static attributes and coexistence
with polling and State bindings. The original browser case now passes with
explicit assertions for `id`, class, style and a boolean attribute. Ruff lint
and formatting pass. Independent review found that parsed source `True`
also represents an empty ordinary attribute, which Vue object binding would
otherwise stringify as `"true"`. Source-origin `True` now becomes `""`;
data-origin `True` retains its existing meaning. Two additional browser cases
prove parity between leaf and general output for bare/empty ordinary
attributes and runtime `True` values. The remaining browser/preflight cases
are still pending.

The loop browser test exposes a separate compiler defect before browser
startup. Prior art: Vize 0.420.0's `codegen/v_for/generate.rs`,
`generate_for_item`, selects an ordinary child with
`unwrap_template_single_element` and emits that child's tag, properties and
children. It still checks and emits runtime directives using the outer
template element. Thus a single button inside `<template v-for>` loses its
directive lifecycle calls, while Citry's metadata correctly records them.
The helper-consistency validator rejects compilation rather than delivering
an inert button. The same source pattern is present in
[the inspected upstream implementation](https://raw.githubusercontent.com/ubugeeei-prod/vize/main/crates/vize_atelier_core/src/codegen/v_for/generate.rs).

This needs a compiler-level correction or an equivalent semantics-preserving
transformation. Disabling the helper-consistency check would conceal missing
behavior. Declining this leaf optimization alone would fix generated server
loops but leave authored Vue template loops affected. Adding wrapper DOM,
moving directives across loop scopes, or rewriting generated JavaScript
without structural validation would introduce different risks. The bounded
fix review must cover custom directives, `v-show`, `v-model`, mixed directives,
single and multiple children, and keyed loops. No compiler correction is
qualified yet.

Independent review recommends a pinned source patch to the published
`vize_atelier_core` 0.420.0 crate. Its public APIs do not provide a replaceable
loop code generator, and a template transformation would need to reproduce
the compiler's scope and key decisions. Select `unwrapped_child.unwrap_or(el)`
for the three runtime-directive checks and closing calls. Keep loop keys and
memo handling on their current paths. This changes neither Citry grammar nor
the compiler's JSON request shape or the five host-language generators.

Keep the patched crate under `third_party/rust`, retain its normalized
published manifest, record the archive checksum and exact patch, and include
upstream license text. Update the workspace patch and lockfile, Python build
cache inputs, and distribution license checks together. Record the patched
compiler identity and verify cache behavior: compiled content IDs include
generated code, while request caches must not survive an incompatible
compiler replacement. A source-distribution rebuild outside the checkout
must use the patched source and ship its attribution. Compiler and browser
checks alone do not qualify packaging.

The source patch and packaging changes are implemented and independently
reviewed. The compiler and patched crate report `0.420.0+citry.1`. The wheel
verifier requires both exact license payloads and metadata entries; the sdist
verifier checks the complete vendored source inventory, patch path and package
identity. Nineteen focused distribution tests pass. They do not prove
Maturin's include-path or manifest rewriting: actual archive verification and
an extracted-source rebuild remain required. Native tests are also being
strengthened to inspect directive tuples and loop-local expressions, rather
than merely checking helper names in generated output.

The first real sdist attempt rejects the explicit include glob because
Maturin does not allow `..` in include paths. The packaging correction must
use its supported local Cargo dependency collection and prove the resulting
archive contains the reviewed source. Root review also found that the new
compiler crate needs explicit workspace MSRV inheritance to satisfy the
distribution contract. Both are build-metadata issues; neither is a reason
to relax the archive verifier.

Stronger facade tests distinguish two Vize emitters. Direct core generation
passes the patched tests, but the production DOM entry point selects the S2
emitter where supported. In `vize_s1_to_s2` 0.420.0,
`emit/directive.rs::wrap_element` also suppresses directive wrappers when
`suppress_template_for_child_key` is set. That flag belongs to loop key
handling; using it to suppress lifecycle calls drops every directive on the
unwrapped loop child. Patch this emitter too, retaining key handling and
Standard template syntax. Switching syntax modes to select another backend
would conflate parser behavior with a code-generation correction.

The second local patch follows the same archive-provenance, explicit path
dependency, registry override and source-distribution checks. Keep the core
patch because the DOM compiler can still use its compatibility fallback.
Qualification must exercise the real DOM facade, not only either emitter in
isolation. It must also verify that loop key handling preserves Citry's
generated lifecycle replacement identities when a server revision changes
directives. Restoring initial directive calls alone does not establish that
update behavior.

The first combined source archive builds and passes full source inventory
verification, including both vendored compiler crates and their licenses.
That archive predates the compiler corrections below; rebuild and verify it
again once those sources settle. Wheel and extracted-source builds remain
pending. Runtime checks exposed two further issues before native
qualification: copying one lifecycle key onto a loop wrapper can give every
row the same key, and the S2 emitter writes numeric-leading directive
modifiers such as `30ms` as unquoted JavaScript property names. Qualification
must preserve distinct row identities, prove cleanup across directive
revisions, and parse the actual generated JavaScript with timing modifiers.
Do not treat different keys between two templates as proof that keys within
one rendered list are unique.

Independent review recommends retaining a Vue Fragment for each loop item
when its single child has a key. The template's existing key identifies the
row Fragment; the child's lifecycle key identifies the element inside it.
An unkeyed loop keeps positional matching. This keeps row identity separate
from directive revision identity without generating new index expressions or
adding producer metadata. Apply the rule in both compiler emitters. If removing
the final directive also removes the need for that Fragment, replacing the
affected row is acceptable, but stale listeners are not. Test multiple rows,
keyed reordering, and directive changes in the browser before accepting this
correction.

The key-suppression review found the same issue in a direct conditional:
an unwrapped `<template v-if>` child can lose its generated bound lifecycle
key to the branch key. Retain the same separate Fragment boundary for keyed
conditional children in both emitters. A facade regression uses real prepared
key metadata, because a static-key example would miss this failure.

Review also found that S2 still unwraps conditional component calls and loses
their generated prepared-data keys. Those keys identify actual Citry calls,
independently of element directives. The same key separation now covers
component children and slot outlets. The slot emitter otherwise puts both keys
on one object, allowing the child key to overwrite the branch key. Independent
source review accepts the final element, component and slot rules and their
fallback consistency. Native and browser qualification remain separate gates.

The stronger fallback test then caught an implementation error in the loop
predicate: its existing key lookup recognized bound keys but missed static
keys. The resulting element had both the row key and lifecycle key on one
object. The unwrap decision must recognize either key spelling, independently
of helpers that retrieve only bound key expressions. Keep the per-row Fragment
assertion as the regression; accepting duplicate object properties would hide
the identity loss.

After that correction, the focused core fallback target passes seven tests.
The S2 runtime-directive target passes four tests and its template target
passes nine, including conditional component and slot key separation. These
are compiler test results. The full native compiler facade now also passes
23 tests, including generated JavaScript parsing and authenticated local-call
metadata. The editable release extension rebuild also succeeds in the existing
CPython 3.12.13 environment, importing the rebuilt extension from this worktree.
The fresh source archive passes full inventory verification with 3,641 files.
Building from that archive in a temporary directory also succeeds; the rebuilt
wheel passes inventory, license, native-extension and isolated import checks.
The verifier removes its temporary wheel and smoke environment afterward.
Browser lifecycle qualification remains before this stage is complete.

The looped runtime-event browser check then exposed a bootstrap metadata
mismatch, despite valid compiler output. Metadata identity uses JSON strings,
but the runtime-site normalizer copied each step's input property order.
The manifest and loaded definition can serialize the same step in different
orders. Construct validated records in one explicit field order, then compare
the normalized values. Audit the other fixed-shape metadata normalizers
for this same pattern. Keep strict value and field validation; changing object
property order must succeed, while a changed route or binding must still fail.

The client patch constructs runtime route steps, local-call bindings, dynamic
element declarations and opaque HTML sites in explicit field order. The
rebuilt client passes TypeScript, Vue type checks, Biome and 64 Node tests.
The regression accepts reordered object properties and still rejects a changed
route. Browser bootstrap is being rechecked using the regenerated runtime.

The two looped runtime-event browser cases now pass, including a selected
conditional branch. The invalid-reference response test also passes: its
immediate State update and DOM update remain unapplied. The next modifier test
assumed `.once` survived a rejected key event. Vue instead installs a native
once listener, so the first event consumes it even if a key or `.self` guard
declines the handler. Keep Vue semantics and test guard behavior separately
from once behavior, with an authored-Vue/runtime-spread parity case. The
source references are Vue 3.5.42's
[event registration](https://github.com/vuejs/core/blob/v3.5.42/packages/runtime-dom/src/modules/events.ts)
and [modifier guards](https://github.com/vuejs/core/blob/v3.5.42/packages/runtime-dom/src/directives/vOn.ts).

The final runtime-event checks pass in eight browser scenarios: two loop-route
cases, invalid-response State/DOM atomicity, modifier parity, once retention
across revisions, form arguments, pending debounce cancellation, and sync/async
error routing. The modifier fixture was rechecked after its final correction.
Runtime polling implementation can proceed. Direct looped model lifecycle
checks and the broader migration gates remain separate unfinished work.

### Runtime polling follow-up

Prior art: `rewrite_resolved_attrs` already parses runtime polling
attributes but rejects them. Authored polling uses typed `pollBindings`,
`registerPoll`, `schedulePoll` and `pollBindingIsCurrent`; the runtime event
directive already owns a separate timing-handle collection. These mechanisms
provide visibility suspension, retirement checks and dispatch without
introducing another timer scheduler.

The implementation candidate is to let the existing generated runtime-binding
site select handler-only polling as well as DOM events. Keep poll specs in
the typed polling table, give runtime polls their own ID prefix, and resolve
each selected ID against its corresponding table during preflight. This
preserves the compiler-authenticated site and its prepared-data route without
adding another directive or repeating native element discovery. Poll handles
must use the existing scheduler, while DOM event handles attach listeners.
The listener reconciliation code needs explicit branches for these two kinds.

Keep runtime poll specs separate from authored `poll_bindings` during typed
capture. Merge their serialized entries into the shared poll table only during
assembly, and select runtime poll IDs through the existing authenticated site.
This prevents the authored directive generator from creating a second timer
for the same runtime poll or treating a runtime value as expression source.

Keep runtime poll arguments restricted to an omitted argument expression for
this first step. Neither a spread string nor its arguments may become
generated JavaScript. Invalid handlers, intervals, references and nonempty
argument expressions reject before publication. Empty eligible sites still
require runtime support and decline cache replay, but do not count as active
bindings for the binding policy.

The falsifiers are an unchanged poll gaining duplicate timers after a server
revision, a removed or replaced poll dispatching later, polling continuing
after retirement, interference with an authored timer on the same element,
and invalid poll metadata being accepted alongside an immediate State update.
The selected ID set must exactly account for both runtime event and runtime
poll table entries. The source implementation now follows this design;
runtime polling is not yet qualified by its focused test gates.

Independent review confirms that scheduler reuse is feasible with explicit
handle kinds and per-binding reconciliation. Resolve IDs by a strict prefix
into exactly one table and validate the complete spec. Runtime poll intervals
must be positive safe integers and `args` must be exactly `null`. Reject swapped
tables and orphan entries as well as malformed selected references.

Install the site's ownership handles before registering a poll: registration
immediately checks that ownership. A poll-only site must have cleanup even
when it has no DOM listeners. An unrelated event change must not reset its
polls. When a retained binding has the same semantic ID and component record,
adopt its newly validated equivalent spec on the existing lifetime, preserving
the timer and `inFlight` flag. Do not call `registerPoll` again for that
lifetime, because it resets `inFlight`. Changed or removed bindings retire
their own lifetimes. A repeated spec on two loop elements still creates two
element-local lifetimes. Browser tests must prove this behavior before the
follow-up is accepted.

Independent source review found four corrections before qualification:
runtime-poll-only HTML needs the existing omitted-JavaScript marker; semantic
timing signatures must use explicit fields rather than input object order;
retained timed events must adopt the refreshed spec and pending debounce
callbacks must use it; and retaining a poll requires an actual matching
lifetime, not only a prior handle. These corrections are implemented and
accepted on source review. The twelve new Python polling checks pass, along
with the updated handler-only acceptance and authenticated-control forgery
checks. After regeneration, the client package gate passes Vue typing,
TypeScript, Biome and 69 Node tests. Negative fixtures now assert the earlier
strict kind/reference guard rather than an error from a later validation step.
The final focused Python batch passes 107 tests across the polling and prepared
capture modules; its five new Node polling tests are included in the package
total above. Ruff and Biome pass for the changed test files.

The first browser polling test passed its assertions for no overlap,
authored-click coexistence, handler replacement and visibility pause/resume.
Its deadline assertion is insufficient: an automatically advancing fake clock
and an eventual-request wait can accept a restarted timer. Do not treat that
run as proof of retained deadlines or in-flight state across revisions.
The direct native `template v-for` input proof also passes: model values update
before and after keyed reordering, node identity follows each key, and removal
detaches only the selected input. It checks reactive model output separately
from native input values, so a missing model listener cannot satisfy the test.
Independent element timers, malformed polling references before State, and
pending debounce retention remain in the browser qualification batch.

The stronger pending-form-debounce test exposed actual cancellation during
every server revision. `applyEnvelope` invokes full `dispose(record)` for a
retained updated record; that function clears all event timing lifetimes before
the directives can reconcile equivalent bindings. The selected correction
is now implemented: separate callback cleanup from full retirement. Retained
records stop and
rerun their callback scope, while directives decide which timers to retain or
remove. Unmount, removal, remount and terminal failure retain full cleanup.
Requalification must freeze the virtual clock or inspect the same lifetime and
deadline across publication; an eventually observed request is insufficient.
Root reviewed the split and the terminal failure path: unmount still invokes
full record cleanup. After client regeneration, captured form arguments survive
the retained debounce, and changed-binding cancellation and event-error checks
pass. The polling deadline test passes with the clock paused. Both event and
poll invalid-reference variants also pass their shared preflight test without
State, DOM or revision mutation. The independent-loop-poller case passes after
correcting its clock and serialized-request observation: snapshots show two
lifetimes before removal, one afterward, and the remaining lifetime in flight
at its retained deadline. No additional source change was needed for that
fixture. The owned browser batch covers 43 cases: 41 passed initially, and the
two failed fixtures pass after focused corrections. One handcrafted i18n
definition omitted required empty metadata fields. The polling-unmount check
now settles in-flight work, pauses time, verifies that timing/poll lifetimes
are gone, and advances two seconds without a new request. This is combined
evidence from the initial batch and two focused reruns, not one fresh 43-case
run. The final client package check passes 69 Node tests, Vue type generation,
TypeScript and Biome. Luna also resolved the 35 existing style findings in the
dynamic-element browser file through forward-annotation cleanup, line wrapping
and explicit test-secret annotations. Ruff and Python syntax checks pass;
behavior tests were not repeated for these mechanical edits.

The removal audit confirms that public component rendering enters typed
capture before compiling its template. The remaining plain-node exception is
static foreign-template fallback, including nested foreign spans. Removing the
encoded binding path must not silently discard Events there: binding-bearing
plain nodes need an explicit unsupported-rendering error until the foreign
provider can supply trusted typed binding metadata. Static foreign HTML without
those bindings keeps its existing fallback. Private tests selecting plain
compilation must move to the normal prepared path for typed binding assertions.

The unused Alpine expression classifier and its pinned expression corpus are
removed after a repository reference audit found no production callers. Its
classifier-only test and the docs test applying that obsolete subset to live
snippets are removed as well. Native Vue expression and CSP tests remain;
the production UI inventory/checker test keeps its assertions with current Vue
wording. The focused browser-analysis suite passes 47 tests, the docs live-code
module collects 33 tests, and Ruff lint/format checks pass. Collection is not
execution of those docs tests, and the broader UI checker gate is still pending.

The targeting review found repeated allocation in browser preflight when
`preflightDefinitions` constructed the entire occurrence map inside each
occurrence iteration and again for graph validation. The current function
constructs that map once before the loop and reuses it. Independent review
confirmed the original quadratic construction pattern; no benchmark saving
is claimed for this correction yet.

Multiple immediate patches also need one shared revision transaction. Separate
current envelopes each propose the same next revision, so applying them in
sequence makes later patches stale. Preserve separately rendered patch trees,
validate all targets and overlaps before mutation, share asset staging and the
existing callback coordinator, then publish once. Marker lexical ownership
must remain separate from the mounted Vue ancestry that controls retirement.
The exact marker syntax, address format and grouping rules are still design
work; no transport support is implied by the earlier browser-only proof.

### Named insertion boundaries: implementation candidate

The next targeting design starts with an ordinary built-in component,
`<c-mark name="summary">...</c-mark>`. Its default slot renders the initial
content. A server update changes that component's prepared contents, so Vue
performs the update through the same component lifecycle used by other
targets. Only explicit markers add occurrences; ordinary HTML elements need
no target registration. This is a reviewed implementation candidate, not an
available API. `#c-mark` could later transform to the same component after the
parser, compiler, bindings and tooling agree on that syntax.

The proposed first public target is `mark:summary`, relative to the component
that sent the event. Transport adds that caller's render ID. Marker names are
literal, nonempty names with a restricted spelling; duplicate names within one
owner reject rather than choosing the first match. The same name in different
owners or apps is independent. Repeated keyed markers, cross-owner shorthand,
append/prepend and multiple Render actions remain later stages. The initial
marker update wraps incoming content in the same built-in component type,
preserving the existing same-type component update contract.

A marker authored inside a supplied fill belongs to the caller's lexical
scope, while its physical Vue parent determines when it is destroyed. Capture
must record both relationships from trusted component-call metadata. The
producer decorates the marker occurrence with its owner and name; ordinary
user data cannot create an alias. The browser resolves the alias through the
current app's address map and reuses target generation checks before and after
asynchronous work. Subtree replacement preserves the selected marker's alias,
translates descendant owner references, and retires aliases of removed
descendants. The owner's server-render callback runs once after publication.

Cache replay is an explicit acceptance boundary: preserve authenticated marker
metadata in artifacts, or decline caching marker-containing output and render
it live. Silently losing aliases on a hit is invalid. Tests must cover supplied
fills, delayed responses after receiver removal, invalid aliases before State
changes, events on newly inserted children, and replacement that does not
evaluate the superseded slot body. Multiple targets will still require one
combined preflight, staging and publication; independent envelopes applied in
sequence do not satisfy that contract.

The public `Render` constructor and its examples also need to enforce the
selected target contract. They still advertise arbitrary selectors while the
Vue transport rejects them later. Move unsupported-target and unsupported-swap
errors to the public action boundary as targeting integration settles, and
update its tests and documentation together. A constructor accepting a target
does not currently prove that the Vue transport can apply it.

#### Marker integration plan and prior art

The first source stage now adds the built-in and initial marker metadata;
focused qualification and production target updates remain unfinished. The
existing paths reviewed are
`component_registry.py::BUILTIN_COMPONENT_NAMES`,
`components/__init__.py::make_builtin_components`, and the per-engine built-in
factory in `components/provide.py`; the typed component and supplied-slot walk
in `_vue/direct_capture.py::assemble_typed_render`; and the rendering path
through `ext/events/results.py::_encode_action`,
`ext/events/renderers.py::VuePreparedRenderEncoder`, and
`_vue/events.py::DirectVueEventsProducer.__call__`. The browser already validates
single-component revisions and coordinates accepted server-render callbacks.
The browser-only experiment in `vue.md` does not establish production marker
support.

1. Add an ordinary, nontransparent Mark built-in with one default slot. Its
   literal template name is case-sensitive and must match
   `[A-Za-z][A-Za-z0-9_-]*`. Reject dynamic or spread names and named fills;
   validate Python constructor names with the same spelling rule. Mark alone
   does not require JavaScript. When another feature activates prepared Vue,
   retain the Mark occurrence and record its alias during the existing typed
   walk. Opaque HTML cannot introduce aliases.
2. Add authenticated marker metadata to initial output, revisions and cache
   replay. Store the lexical owner, marker name and physical occurrence
   separately. Resolve render IDs through the existing render-to-occurrence
   mapping; do not invert that mapping, since several render IDs can identify
   one occurrence. Reject duplicate names within an owner. Cache replay must
   retain these relationships or explicitly render the result live.
3. Accept public `mark:<name>` relative to the event caller and encode
   `mark:<callerRenderId>:<name>` for transport. Keep `render:<id>` and the
   default caller target. Reject malformed addresses, missing callers and
   unsupported swaps before rendering. Rejecting fully qualified public marker
   strings keeps the initial API small; it is not an authorization boundary.
4. Normalize incoming content and render its Mark wrapper within one prepared
   direct session, invoking the payload element's public render method exactly
   once. Reuse an already prepared `CitryRender` unchanged. Render the engine's
   Mark with that result as its static default slot, and validate the final
   prepared tree once. Closing the session between payload and wrapper would
   discard composition context. Passing an unrendered element
   directly into Mark would change the payload's Python parent, root and
   provide/inject context. Validate nested renders against the encoding engine
   during the existing assembly traversal: checking only the new Mark root
   would conceal a foreign-engine body. Compare the nested component's engine
   and registered class identity, including transparent renders and class-ID
   collisions. Carry the expected encoding engine explicitly rather than
   deriving the authority from the new wrapper. This requires no additional
   unconditional graph walk.
5. Resolve and freeze the live marker target before asynchronous staging.
   Preserve its current authenticated owner and name when translating incoming
   root IDs; the incoming wrapper does not establish those facts. Reject stale
   targets and dangling lexical owners before publication. Replacing content
   must skip the old slot factory. Notify the surviving lexical owner's
   server-render callback once, and use physical ancestry for disposal.
6. Extend the same coordinator to multiple targets after the single-marker
   path passes. Freeze all targets, reject duplicates and physical
   ancestor/descendant overlap, allocate IDs and stage assets together, then
   publish one candidate revision. Preflight deterministic failures before
   immediate State writes. Preserve action ordering and define delayed-action
   behavior explicitly; applying several independent envelopes with the same
   base revision is not a transaction. Vue or user callback exceptions after
   publication still require the existing error policy, not a claim of full
   rollback.

The focused acceptance checks are static Mark output without runtime loading;
Mark retention in an independently interactive app; lexical ownership through
supplied fills; payload hooks running once; unchanged root context and IDs;
rejection of foreign nested renders; alias preservation and retirement across
updates and cache replay; stale or malformed targets leaving State untouched;
events on inserted children; and combined updates notifying each owner once.
These checks distinguish producer, cache and browser failures without repeating
the complete matrix at every layer. Grammar shorthand and arbitrary-element
instrumentation remain unnecessary for this implementation.

Read-only review identified two wrapper cases to prove before enabling the
transport. An already prepared render extracted from a nested call may retain
the old parent's authored-call metadata. Selecting it as replacement content
must establish a new placement without rerendering it or discarding its data
and render ID. The generic Python-slot adapter deliberately treats such calls
differently, so an extracted nested render is a required test. Also, the
synthetic Mark wrapper does not establish a fresh lexical alias. Keep its
replacement role private and let the frozen live target supply the retained
owner and name; user kwargs must not authorize that role. The implementation
must distinguish this wrapper from an authored marker before duplicate-name
validation and root-ID translation.

The first implementation stores an ordered `markers` array of
`{ownerId, name, occurrenceId}` records in prepared manifests and revisions,
including an empty array when there are no markers. Assembly proves built-in
class identity; protocol validation checks references, spelling, ordering and
uniqueness. The browser implementation now consumes these aliases; its focused
transport qualification is in progress. Cached boundaries
containing Mark currently use the established live-render fallback, since the
artifact does not retain marker identity. This is an explicit temporary cache
limitation, not a successful alias replay claim.

The existing compiler normalizes `<c-Mark>` and transforms a literal
`<c-component is="mark" name="summary">` into a direct Mark call. Both follow
the literal-input rule. Runtime component selection of Mark rejects; it cannot
establish literal marker authoring. The initial smoke checks static output,
prepared owner/physical metadata and rejected dynamic names. Supplied fills,
duplicate aliases and cache-boundary behavior now have focused tests. The
14-test marker suite passes, including invalid name sources, duplicate aliases,
shared names under distinct owners, supplied-fill ownership, live cache fallback
and strict protocol records. Root reviewed these boundaries; Ruff lint and
format checks pass for the test and the two mechanically formatted runtime
files. Single-marker targeting is implemented and awaiting producer and browser
qualification; multiple-target transactions remain a separate step.

The transport plan does not add render-address aliases preemptively. Current
Events preparation permits exactly one Events instance per occurrence,
requires its render ID to be canonical, and rejects transparent components as
Events owners. A valid event caller therefore already has the occurrence's
canonical address. Test that fact through a supplied fill and transparent
wrapper before changing the wire format. Internal assembly mappings can be
many-to-one without requiring every internal render ID in browser payloads.

The server knows the requested marker name and caller render ID, not the live
browser's marker occurrence or generation. Its synthetic Mark wrapper carries
only its private replacement role. The browser resolves and freezes the owner,
target occurrence and generation from the current tables, then preserves that
alias during root translation. No server-side wrapper may fabricate those
live target facts.

Transport review caught two lifecycle errors before qualification. A marker's
surviving lexical owner needs callback cleanup even when its own definition is
not staged. The coordinator now collects those owners together with retained
staged instances, disposes their callback effects once, and preserves event
timers. The synthetic wrapper also needs exact identity: an ambient render flag
would incorrectly classify authored markers created by extension hooks. A
private element type now identifies only that wrapper. Tests must exercise
repeated cleanup and nested markers created during wrapper hooks. The default
Events dispatcher explicitly supplies the marker preparation callback; testing
only a manually connected encoder would miss that integration point.

The first default-dispatcher producer test passes: it emits a caller-relative
marker address, advances revision 4 to 5, renders the fresh payload once, omits
the synthetic root alias and retains a nested authored marker. This test does
not yet prove hook-created markers, extracted nested-render context or browser
callback cleanup.

Browser qualification then proved the first update's callback cleanup, but the
second update sent the old State token and rendered the same count again.
An idle barrier did not resolve this. Source review found that
`beforeServerCallbacks` adopted the old occurrence's event context for the
callback-only lexical owner, overwriting the State action accepted earlier in
the response. Callback notification must remain separate from adopting a new
server context. Only genuinely updated or newly mounted instances should adopt
incoming contexts; the retained marker owner still needs its callback cleanup
and notification. The two-update test checks both token rotation and counts,
and passes with the corrected client build. It observes
`run0, cleanup0, run1, cleanup1, run2`, content `initial → 1 → 2`, and distinct
sequential State tokens. Its idle barrier waits for Events loading and the
app transaction to finish; it does not assume that a marker-only response also
delivers new public State values for the unrendered owner. Root review caught
an incomplete first correction that gated public State adoption but still
overwrote the token map; the passing build gates both. The default-dispatcher
producer case and existing case-sensitive marker case also pass together.

The editor audit also established a Mark authoring gap: the built-in appears
in the registry but exposed no input schema, so completion omitted `name` and
the editor accepted invalid declarations. The implementation now adds typed
inputs and a default-slot schema, plus shared template analysis for the
literal-name constraint that generic input schemas cannot express. This must
run without enabling browser lint, because a static Mark needs no runtime.
The new schema requires reading typed inputs correctly; the first rerun caught
the old dictionary conversion and qualification paused for that correction.

Producer review additionally found that flattened render results bypassed the
occurrence-level engine check. Validate their origin within the existing
traversal. Simple components require their actual simple component class as
well as the caller context: their context deliberately retains the caller's
component, so checking only that context cannot prove the source engine.

The combined prop/Mark tooling selection now passes 39 cases. It covers CLI
and LSP findings, syntax-only analysis, exact source positions, Mark schema
exposure and the built-in inventory. A real-render comparison caught a
case-handling gap: component tags are case-insensitive, but Mark requires the
literal input spelling `name`; folded `NAME` and `name` plus `NAME` must not
silently pass tooling. The shared analysis now follows that runtime rule.
Exact duplicate attributes remain parser errors. Completion also omits the
invalid dynamic `c-name` suggestion; its focused test and the ordinary-component
completion regression both pass.

The next producer test exposed a separate Python composition gap. An
already-rendered payload whose `on_render()` returns a component element
contained a child without authored-call metadata, and assembly rejected it.
That is a valid Python composition boundary, not malformed user output.
The correction marks settled deferred output and already-rendered hook results
through the existing Python composition adapter, preserving IDs and context
without rerunning the hook or weakening assembly validation. The complete
marker module passes 20 cases, including both hook return forms and foreign
transparent/simple render origins. The focused browser pair passes repeated
marker updates and ordinary Events self-updates. The final client check passes
70 Node tests, generated Vue types, TypeScript and Biome after valid fixtures
adopted `markers: []`; an omitted-array negative preserves strict validation.
These are focused source gates, not the final repository or browser cohort.

The multi-target follow-up must also preserve observable action ordering.
The Events protocol permits delayed actions and a dispatched event between two
renders. Publishing both renders at the first action would let that event see
content that should not exist yet. The implementation candidate is therefore
one contiguous group of immediate, blocking Render actions. Reject interleaved
or deferred multi-render groups before State changes, and document that limit.
Actions before and after the group retain their order. A single Render keeps
its existing timing behavior. Implementation has started after the single-marker
gates passed. The private preflight result collapses a validated group to its
first action and carries the combined candidate in its internal render plan;
the public action format remains unchanged. Source review and grouped tests
remain pending.

Source review corrected several grouped-update hazards before the next client
build. Each member now validates its app, revision, complete update set and
subtree before translation; the group validates the combined graph once.
Single-target plugin preparation still receives its partial subtree. Grouped
preparation uses translated plugin IDs and explicit replaced roots, so an
app-root candidate cannot retire unrelated providers. Shared styles merge
occurrence references while checking the rest of their identity. Marker and
replacement ordering uses deterministic string comparison. Runtime and i18n
qualification of this source is underway; these changes are not yet a passing
grouped-update result.

The rebuilt client passes generated Vue types, TypeScript, Biome and all 70
Node tests. Its valid isolated-subtree fixture needed the required empty
asset arrays. The repeated-marker and ordinary Events browser pair also
passes. Dedicated grouped-update and i18n batch tests are still in progress.

The first i18n batch falsifier found a real validation gap: merging metadata
let a valid configured target supply the required `runtime` field missing from
another configured target. The malformed target failed standalone validation
but passed as a batch member. The bounded correction validates every member
through the existing payload validator and merges its detached result. Empty
array-only payloads remain valid. Cross-member checks and provider resolution
still run once in the combined revision stage. Luna Max owns this correction
under the user's exception; root specified the change and Sol independently
reviewed the plan. Runtime qualification remains pending.

The correction is implemented and root-reviewed. The minimal regression now
passes against the bundled production plugin: standalone and grouped forms
both reject the malformed configured member. All five tests in that focused
i18n module pass. Provider-retention, abort and mixed dormant/configured cases
and the rebuilt browser integration remain to be qualified.

The expanded i18n module passes nine cases, including a new snapshot that
omits the retired nested occurrence while the host still holds its old graph.
That case proves retirement uses the prior ancestry when necessary. Tests
also cover unaffected providers, mixed dormant/configured members in either
order, abort preserving the active provider view and single-subtree behavior.
The regenerated client passes all 75 Node tests, generated types, TypeScript
and Biome. Grouped browser qualification remains in progress.

Three compiler tests now exercise the production in-process compiler rather
than skipping when a research executable is absent. Their module passes all
13 tests. Source-map/raw-text rejection, native model lifecycle metadata and
definition/fill identity remain covered. Caller audit found no remaining
production dependency on the optional subprocess compiler transport; its
private compatibility branch is being removed while preserving production
cache identity and context-manager behavior.

The subprocess branch is removed and root-reviewed. The prepared module and
two authenticated-call metadata cases pass together, 15 tests. One browser
attempt overlapped that source edit and loaded an incomplete class definition;
it is discarded as a coordination failure, with the browser test rerun in a
fresh process after source freeze. No fixture or production workaround is
needed for that transient failure.

The fresh grouped browser run passes eight cases. Three consecutive accepted
groups update both markers together around before/after Dispatch observations,
run the owner callback and cleanup once per revision, and carry each new State
token into the next request. Seven invalid-response variants cover malformed,
stale, foreign-app, duplicate, overlapping, interleaved and deferred targets.
Each leaves HTML and revision unchanged, and the next request retains its old
State token. The token assertions use actual requests: retained occurrence
metadata does not represent the mutable Events token. Existing single-marker
and ordinary Events update cases also pass. Broader integration and final
benchmarks remain pending.

A subsequent grouped-update check passes nine browser cases. Shared scoped
CSS applies to both marker targets across repeated revisions; replacing one
with unstyled content retains the one stylesheet needed by the other. A
conflicting shared definition in the second envelope rejects the group before
State changes, verified through the next request's token. This closes the
specific shared-asset merge concerns from source review. The full core unit
suite starts after this source freeze.

The first broad run selected `not e2e` markers but still collected unmarked
browser files, so its 280 failures are not the clean unit baseline. The
corrected repository-profile run explicitly excludes browser paths and records
258 failures, 4,987 passes, six skips and one expected failure. The log is
`/tmp/citry-benchmark-design-citry-unit-no-e2e-20260914.log`. Failures are being
classified by behavior: retired client-prop contracts, internal representation
assertions, newly added built-in inventory, and possible serializer defects.
No blanket expectation rewrite is accepted. Current source investigations
include trusted HTML string subclasses and self-closing SVG output.

Both bounded serializer defects are corrected and root-reviewed. Exact
`Markup` inside an already typed body records body ownership and is discarded
with the body content replaced by the Vue host; it cannot establish or alter
the physical shell. Static leaf output follows the main serializer's
non-void self-closing normalization. Three shell cases and the existing SVG
regression pass together. Canonical benchmark fixtures now reach a separate
unsupported executable-attribute-from-Python error, which belongs to their
remaining example migration and is not bypassed in production.

Failure classification also identifies two substantive gaps. The prepared
render branch caches by visible names and tracing but bypasses Const
specialization; the public precomputation promise still applies, so missing
legacy cache entries cannot all be dismissed as stale tests. Restoration needs
behavioral evaluation/reuse tests before any representation assertions change.
Nested cache replay also discards validated class provenance when it constructs
componentless contexts. Its artifact decoder already verifies engine registry
identity and source fingerprints. A bounded fix will retain that proof in a
private decoder-issued context token, preserving strict live-instance checks
and rejecting foreign or stale classes without constructing fake components.

The replay provenance correction is implemented and root-reviewed. A private
frozen engine/class token is issued only after artifact validation for detached
occurrence contexts. Consumption rechecks the exact engine, class and current
registry mapping; live occurrences do not execute this extra lookup. Mark and
instance-less transparent frames receive no new allowance. Six focused tests
pass, including both nested cache regressions and unissued/foreign/stale proof
rejection. The complete artifact module is the next check. Const restoration
remains a separate design task and is not counted as fixed.

The independent full typed-cache artifact module passes all 52 tests after the
provenance correction. Const restoration is now approved for implementation:
reuse the existing specialization traversal with prepared-value adapters,
specialize before coalescing and leaf compilation, and include the Const
signature in the bounded prepared cache key. Precomputed scalar text must
remain typed text data, including literal Vue-looking delimiters; trusted
markup remains opaque HTML data. A signature-only cache change would not fix
the missing work reduction. Behavioral equivalence precedes migration of the
older cache-representation assertions.

The docs unit baseline records 36 failures and 887 passes with browser tests
excluded; its failure list is saved in
`/tmp/citry-benchmark-design-docs-unit-summary-20260914.txt`. Four apparent
head-metadata failures were attribute-order/HTML-void-format assertions, not
lost metadata. Parsed attribute/value checks preserve their real contract.
The full chrome module and two corrected catalog checks pass 32 cases. The
authored Mark reference entry also passes the real built-in guard and emits
exactly one generated heading. Separate docs build/browser qualification is
still pending. Runtime-dependent checks are held while the connected Const
implementation is incomplete.

Root review rejects the first Const candidate as incomplete despite its
focused pass count. Its prepared expression adapter called normal value
resolution before excluding components/slots, which could execute structured
rendering while probing specialization. Its loop-output test did not prove
unrolling, and static typed opening/closing nodes were not fully certified by
the adapter. The correction must exclude structured values before rendering,
preserve hook-sensitive nodes, and prove repeated evaluation avoidance as well
as output, compiled text provenance, scope guards and cache lifecycle. Runtime
checks remain held during this correction.

The next frozen-source integration run records 241 passes and two failures
across Const, cache artifacts, markers, Events and direct relationships. The
bounded per-engine cache eviction test also passes. The two failures remain
under investigation: nested-loop source reuse and SVG self-closing siblings.
In particular, the earlier SVG correction does not establish correctness for
all leaf output: the leaf compiler consumes paired close descriptors, so
removing the opening slash can leave no closing syntax at all. Do not classify
either failure as an obsolete assertion before checking the resulting
structure. Const custom value dispatch and constant element keys also remain
review questions. No fresh benchmark result is claimed for this source.

Follow-up inspection distinguishes the loop failure from the SVG defect. The
loop fixture supplies literal component inputs, which become constants; the
restored visitor correctly selects branches and expands their loops. Its HTML
is correct, but distinct constant shapes produce distinct definitions. The
shared dynamic-loop test will use ordinary runtime inputs while retaining its
definition-reuse and generated-loop assertions. Custom rendering dispatch
remains live in the additional exact-string probe. Constant element keys do
need a correction: their metadata is bundled with hook-sensitive attributes,
so specialization currently skips them. A metadata-only specialization will
retain live attribute hooks and reuse the existing key validation.

The metadata-only key correction passes 15 dedicated Const tests and 95
prepared-capture tests. The dynamic-loop fixture passes with every original
output, occurrence, shared-definition and compiled-loop assertion retained.
Chromium confirms the SVG defect: leaf output nests the circles inside the
path, while ordinary typed output creates three siblings. Materializing an
explicit closing tag for a self-closing non-void leaf operation matches the
ordinary serializer without needing namespace inference.

The sibling sweep finds the same missing close in typed leaf fallback. It also
finds a separate static-grouping variant: preserving `<div/>` while consuming
its paired close nests the following sibling in HTML, including HTML inside
SVG `foreignObject`. The correction therefore covers static leaf output,
typed leaf fallback and static grouping. All non-void self-closing elements
will receive explicit closing tags; void elements retain their existing
syntax. Grouped opening offsets, lengths and depth metadata must follow the
normalized bytes. DOM structure, not slash spelling, is the regression
contract.

Independent verification of the corrected paths passes 253 tests across seven
focused files. Chromium confirms sibling structure in HTML, custom elements,
SVG and `foreignObject`, including typed leaf fallback. Static-group opening
slices, insertion offsets, depth changes and tag transitions agree with the
emitted bytes; dynamic self-closing nodes retain their zero-width close until
leaf compilation consumes it. The remaining regression-test refinement is to
capture those HTML browser checks permanently, since XML parsing alone would
accept the malformed-for-HTML self-closing form.

The remaining legacy Const review records 47 passes and 31 failures, plus two
Pydantic Const failures. Each failure first hits a private representation
assertion after its initial public assertion passes. Test migration must also
recover checks hidden behind those failures: repeated zero-variable loop
reuse, a supplied slot taking precedence over fallback, and repeated deferred
expression errors. Evaluation and iteration counts will preserve the work
reduction contract without requiring HTML strings or particular node types
inside the prepared cache.

The next Events-binding audit records 172 passes and 29 failures. Source
inspection identifies three parity gaps rather than accepted removals:
nested-template attributes need an explicit lexical-owner placement route;
combined debounce/throttle must retain throttle admission followed by debounce
scheduling; computed/spread dynamic elements still need Events integration.
Existing rejection in the new runtime does not authorize changing those
public contracts. Nested-template placement will reuse the existing explicit
projection machinery where possible, keeping generic cross-owner rejection
strict. Dynamic-element integration must preserve resolved-tag validation,
typed bindings, cache replay and browser dispatch, and is a separate stage.

The nested-template implementation plan uses an internal native Vue slot.
For Page passing a template attribute into Card, Card emits an unconditional
outlet and Page emits the corresponding `v-slot` content on its Card call.
This keeps authored Vue expressions in Page's lexical closure as well as
keeping prepared Python data and Events attached to Page. Merely changing the
prepared-data owner while inserting source into Card's definition would leave
Vue expressions in the wrong scope and is rejected.

The template attribute captures its lexical source during Python evaluation;
its later insertion binds a fresh physical projection in the same render
session. The existing projection wrapper and fill-emission machinery will
share validation with this distinct nested-template kind. It must not invoke
Python slot hooks, create a slot selection predicate, or relax unwrapped
cross-owner checks. Existing cache tuple fields carry the lexical/receiver
anchors and projection identity, with strict kind-specific reconstruction and
invalid-combination rejection; the wire version remains 1. Browser tests must
distinguish identically named caller/receiver JS values, alongside nested
supplied slots, Events ownership, replay and invalid-session tests.

The first candidate passes 174 focused tests, including browser lexical scope
and supplied-slot nesting, but is not yet accepted. Review finds a Unicode
span-bound error and an overbroad transparent-container exception based merely
on finding a projection among its descendants. That exception must be removed
or replaced with exact producer provenance. The nested kind's execution-parent
handling also needs real cache-backend miss/hit coverage; codec roundtrip alone
does not prove replay. A separate Events test exposes component-boundary
`c-bind` handler support as another parity gap: its runtime-origin binding
currently fails the authored-source authentication check. Preserve the
positive test while designing its typed runtime representation.

The correction plan preserves the selected lexical render inside the explicit
nested projection, so assembly enters the projection before checking the
lexical wrapper. It removes the descendant-scanning exception completely.
Span bounds use UTF-8 byte length. Nested projections may have a legitimate
enclosing slot execution, validated and reconstructed through the existing
parent-anchor rules. A real cache-backend test already proves a simple
nested-template miss/hit retains caller-owned Events and avoids repeated data
callbacks; supplied-slot cache nesting remains in the correction gate.

The corrected source removes the scanning exception and passes focused
leaf/general, browser lexical-scope, Unicode and unrelated-owner checks. The
complete migrated Const and Pydantic modules now pass 95 tests. Their counters
observe renderer evaluation boundaries using scalar inputs; an earlier test
rewrite using `Const`-wrapped callbacks was invalid and was corrected before
acceptance. The original repeated-cache, supplied-slot precedence and repeated
error checks remain present. A fresh clean core unit baseline is the next
integration check, with browser directories explicitly excluded.

The final nested-template gate passes 178 tests: dedicated projection cases,
Unicode/owner guards, existing nested bindings, complete direct-relationship
and typed-cache suites, and Chromium lexical/supplied-slot checks. Actual cache
miss/hit tests cover both a direct nested template and one inside a supplied
slot, with explicit `Cache.vary()` where slot content participates in caching.
Missing external execution parents and unknown projection kinds reject.
The generic cross-owner guard is unchanged. This qualifies the bounded
projection stage, not the remaining migration or a new benchmark cohort.

The refreshed clean core-unit baseline records 132 failures, 5,093 passes,
six skips and one expected failure in 16.98 seconds. The command explicitly
ignores `tests/e2e` and excludes qualification tests using the repository's
four-worker profile. Its log is
`/tmp/citry-benchmark-design-citry-unit-no-e2e-20260914-rerun1.log`.
The reduction from 258 failures reflects both source fixes and migration of
obsolete tests, not 126 independently fixed bugs. Largest remaining groups are
metadata, Events conformance, dynamic elements, Events bindings and i18n.

The next implementation restores combined timing: throttle determines which
events are admitted, and debounce schedules the latest admitted payload.
Dropped events must not reset the pending debounce. If debounce finishes before
the throttle window, its lifetime must retain admission history until that
window ends. Controls retain immediate draft updates, with timing delaying
server delivery. Authored and runtime-spread events must share this behavior;
replacement and unmount cancel pending work. Browser qualification follows a
client rebuild after source freeze. Timed component-boundary listeners remain
a separate parity check.

The rebuilt client passes its package checks and 75 Node tests; 15 existing
timing/control browser cases also pass. New combined-timing tests expose an
additional authored-event issue: unchanged revisions publish equivalent spec
objects, but identity-only reconciliation cancels pending timers. The fix
will share the runtime-event semantic signature and adopt the new spec while
retaining the captured arguments and deadline. Changed bindings still cancel;
polling policy is outside this correction.

Events conformance harness migration passes all 19 cases without changing the
protocol fixtures, dispatcher paths, schema validation or result comparisons.
The helper now obtains credentials from a real prepared Vue occurrence's
`eventContext`, replacing its lookup for a separately emitted Events script.

The final client rebuild passes all package checks and 75 Node tests. All five
new combined-timing browser cases pass, including admission during the
post-send throttle window, unchanged-revision retention and removal cleanup.
Fourteen existing selected browser cases pass; one older case expects an
unchanged authored revision to cancel pending work. Its expectation must be
updated while retaining the later conditional-removal and unmount checks.

Metadata review approves restoring empty component keys: only `None` opts out,
and nonempty occurrence IDs are derived by hashing rather than copying the raw
key. Component-level `#c-ignore` must explicitly reject in prepared Vue, matching
the documented deferred support, rather than disappear silently. The remaining
selector-continuity debug warning only matches caller-owned marker targets
under the current API and is a false positive; redirect warnings remain.

Dynamic-element Events implementation is approved next. It retains the
compiler's typed event/control/poll facts through the dynamic selector, runs
existing final-tag validation after attribute hooks, and emits the existing
generated directives on the dynamic alias. Carrier metadata must survive
Const and extension node rebuilding. Authored cache records may use an exact
extended `dynamic_open` tuple with legacy v1 decoding; runtime-spread cache
eligibility must follow the existing ordinary-element rules. No native
compiler contract change is expected, but native alias spans and browser
dispatch/control behavior require tests before acceptance.

Component-boundary spread handlers remain separate. Giving them fabricated
authored-source provenance is rejected. A DOM directive on a component also
cannot be assumed to cover fragment-root components; native Vue listeners or
a typed listener helper need qualification for that case.

The i18n test audit identifies fixture/transport drift in two modules: client
fixtures still use Alpine attributes and both modules inspect a standalone
i18n script or literal interactive body HTML. Prepared Vue carries the i18n
payload in its extension data and sends a host for interactive output. Test
migration must retain unknown-root errors, locale/root partitioning, omit
policy, false-binding removal, provider-order/Const behavior and literal-text
escaping. Interactive text needs browser or typed-data/compiled-source proof;
omitted-runtime fallback still needs its server HTML assertions.

Dynamic Events review catches an empty-first cache defect: deriving runtime
eligibility only from the resolved binding token allows an empty spread to be
cached and suppresses a later event. A dedicated cache falsifier reproduces
the loss. Preserve the compiled runtime-candidate fact through the carrier and
Const rebuilding, normalize even an empty candidate, and retain the existing
cache exclusion. New dynamic binding fields use the shared normalization and
runtime-candidate invariants.

Metadata test migration also exposes a distinct transparent-wrapper key gap:
the `c-provide` frame retains its explicit key, but the assembled subtree has
no native keyed boundary. Requiring a separate component occurrence would be
wrong for a transparent wrapper, but silently discarding its key is not an
accepted contract change. Keep the positive key-preservation test pending a
native fragment/placement design.

The user authorizes Luna Max for this bounded rendering fix while root retains
design and review. Before implementation, inspect the generated Vue function:
a single-iteration `v-for` can add an unkeyed outer fragment, which could make
Vue remount keyed descendants instead of moving them between wrappers. Compare a keyed
always-true conditional as an alternative. The acceptance case must reorder
wrappers and preserve both DOM state and nested component identities. Carry
the transparent key into descendant placement identities as well as native
Vue keys; do not add a Citry component occurrence for the wrapper.

The official Vue compiler probe confirms the singleton-loop problem. That
candidate is rejected before production changes. Check the remaining template
forms with Citry's in-process native compiler before expanding its contract.
The native probe preserves a dynamic key on a conditional template and emits
a keyed root element or fragment without the extra unkeyed loop boundary.
This requires the existing generated element-binding span metadata. Approve
a bounded Python-only implementation experiment, including stable descendant
placement routes. Empty/text bodies, independently keyed root children and
browser reorder state must pass before accepting the approach. No native
compiler contract change is approved at this stage.
One valid native template composition places the single-iteration list
inside the keyed conditional. Native output puts the key directly on the
list's root Fragment and preserves an independently keyed child. This avoids
both the outer unkeyed-loop problem and conditional key transfer onto a
single child. The implementation instead uses a constant false conditional
child to keep the outer keyed Fragment: this avoids introducing a synthetic
loop into runtime-event route discovery. Verify actual browser state
preservation; generated source inspection alone does not close the gate.
The first reordered assembly falsifies descendant identity preservation:
slot IDs use a source-wide positional counter, so the transparent wrapper's
stable key alone cannot stabilize child placement paths. Scope slot counters
by source and placement path, and include that path in the site identity.
Repeated uses within the same path still receive distinct ordinals. Adding
the path only to the hash while keeping the source-wide counter would retain
the reorder defect. Recheck supplied slots and cache replay with this change.
The corrected implementation passes 11 focused unit/regression cases and a
browser reorder test. The browser retains row/input DOM objects, Vue component
objects, rendered instance IDs and edited input values by key; a runtime
spread event inside the wrapper still dispatches. Existing direct-slot/cache
integration tests and independent source review are the remaining bounded
checks. No performance improvement is claimed for this correctness fix.
The first integration run reports 189 passed and one dynamic-element key
failure. `<c-element>` already assigns its key to the selected native element;
the generic transparent branch should not also manufacture a keyed wrapper.
Inspect the producer's distinction between element metadata and call metadata
before adding a class-name special case. Preserve the existing native-key
assertion while correcting this distinction.
The producer now uses the same element-target decision for native metadata
and component-call metadata, so only the native element receives that key.
The corrected key/slot/cache integration gate passes 190 cases. An explicit
browser-marker run also passes after strengthening the event assertion to
wait for a successful response and verify the Python handler ran once. Ruff
check and formatting pass; no native rebuild is needed.
Independent review finds no concrete defect in the key/route/projection
changes. Existing native-element, independently keyed child, and browser
state tests cover the distinct failures, so no additional cross-product test
is added. This closes the bounded transparent-key fix performed by Luna Max.

The component-boundary runtime-event proposal also needs a compiler check.
The native local-call validator accepts `event` only for `v-on` with an
argument; a listener object is not covered by that contract. The runtime
currently exposes `$citryEvents.dispatch`, not a separate component-dispatch
helper. Compare generated per-event listeners using separately checked runtime
metadata against adding a listener-object contract before choosing a fix.

The i18n fixture audit finds a concrete missing requirement for an inline
provider fill. A Page declaring `title` and rendering
`<c-i18n c-client="True" tag="main"><output v-text="$i18n.tr('title')" /></c-i18n>`
records the Page's client output, but emits no message requirement. The
requirement builder follows provider inheritance rather than the rendered
Page-to-provider relationship. There is also a browser-scope concern: the
native slot expression belongs to Page, while `$i18n` reads the service cell
for that lexical component. The browser falsifier resolves this concern:
`$i18n.context.locale` renders `en-US` without errors in the inline fill, while
`$i18n.tr('title')` fails with `I18N_MESSAGE_MISSING`. Provider lookup works in
this case; the confirmed defect is the omitted message requirement/artifact.
Do not change browser scope resolution based on the rejected hypothesis.

Independent review passes 60 dynamic Events, typed-cache and browser cases.
Additional focused probes verify empty runtime candidates, event/control
collision errors, UTF-8 source spans, acceptance of seven- and nine-field
dynamic cache records and rejection of an eight-field record. The separate
component-boundary spread failure does not invalidate this dynamic-element
gate. This is bounded correctness evidence, not a complete migration gate or
a new benchmark result.

The next frozen core run, excluding the E2E directory and qualification
markers, reports 5,185 passed, 54 failed, six skipped and one expected failure
in 16.13 seconds. The prior comparable checkpoint had 132 failures. This
reduction combines production fixes and test migration, not 78 distinct bug
fixes. Fourteen failures involve i18n; other clusters include runtime asset
expectations, slot-fill output expectations, retired selector fixtures and
the known component-boundary event spread and transparent-key gaps. The log
is `/tmp/citry-benchmark-design-core-no-e2e-20260914-dynamic-review.log`.
One compatibility-flow failure is a production mismatch, not merely a stale
selector fixture: the dispatcher still rewrites an unaddressed compatibility
Render to `:root`, but the public Render constructor now rejects that target.
Keep the stricter public target contract. Resolve the compatibility-only
encoding address at the encoder boundary rather than constructing an invalid
public action; retain rejection of unaddressed instance-less wire calls.
The compatibility correction passes 97 action-encoding tests and the focused
dispatch/error cases. The larger dispatcher/routes/Django gate initially has
290 passing cases and two stale host-parity assertions. Those fixtures now
validate native prepared payloads or compatibility HTML according to mode,
pin the deliberately random app ID, and still compare complete bodies. Both
host cases pass. Independent source review confirms the private address is
restricted to the exact HTML encoder in compatibility mode.

Read-only review identifies three slot contracts behind four failures.
Whitespace-only `PreparedSourceTextNode` objects bypass the string-only
empty-fill check. The same internal objects leak through public
`Slot.contents`, whose documented value is the original input. Required-slot
errors also omit the documented close-fill-name hint in both rendering paths.
Keep these assertions. Recognize prepared source whitespace, preserve public
slot inputs separately from executable prepared bodies, and share the
passed-fill diagnostic between the plain and direct paths.
The first focused gate fixes whitespace and the diagnostic. Once authored
contents pass, two metadata assertions expose a second leak: internal direct
fill data is stored in public `Slot.extra`. Move that data to a private Slot
field, preserving it when slots are normalized/copied. A global weak-key
registry is unnecessary for metadata with the same lifetime as the slot.
The completed slot correction passes five targeted regressions and 182
slot/direct/cache cases, with targeted Ruff checks passing. Normalization
copies preserve the private relation while leaving `Slot.extra` available for
extension data. Independent source review finds no concrete defect in the
projection, whitespace, diagnostic, private-field or normalization changes,
closing this bounded slot correction.

The asset/i18n focused run reports 60 passed and six failures. Both asset
delivery modules and the translation-binding module pass. The six remaining
client-i18n failures cover omitted literal message roots, missing unknown-root
validation and a server-only barrier that leaks requirements to an external
provider. These strict assertions remain in place for a production fix.
The prepared-i18n correction reuses the supplied occurrence-parent mapping
for provider and barrier discovery. All 14 client-i18n tests pass, including
the six strict failures and an actual cache miss/hit barrier case. The typed
cache marker regression also passes. Browser service lookup and cache/wire
versions are unchanged. Independent review and one real producer-to-browser
translation regression remain before accepting this bounded correction.
The real producer-to-browser translation test passes: a serialized Page with
an inline client provider reaches readiness, renders `Client title` and
reports no page or console errors. This confirms the message payload reaches
the live plugin, rather than only passing a Python manifest assertion.
Independent emission review finds no blocker, including multiple disjoint
message requirements mapped to one provider and replayed ancestry. This closes
the bounded provider/barrier payload correction.

Component-boundary runtime event spreads now have a separate data carrier
authenticated against the originating `c-bind`. Detached/cache metadata keeps
an explicit authored-versus-runtime discriminator; version-one old records
default only to authored provenance. Generated listeners use call-local IDs
so repeated calls can carry different handler data. The Python/cache gate
passes 257 tests, but the initial browser fixture is insufficient: forwarding
a DOM click hides the fact that valid Vue `emit('confirm')` has no DOM Event.
The current DOM dispatcher dereferences `event.type`, and even a forwarded
click has the wrong type for a semantic `confirm` event. Add a component-event
dispatch path for both authored and runtime component listeners. Preserve
DOM validation for ordinary elements, require explicit argument objects as
before, and collect implicit form arguments only from an actual forwarded DOM
Event. Arbitrary emitted payloads do not automatically become Python kwargs.
Payload-less/custom-data emit tests must pass before closing this feature.
The new component dispatcher shares live binding/source validation with the
DOM dispatcher but identifies the event through the compiled listener, not
the emitted value's `type`. The browser test now passes for payload-less
`confirm`, explicit arguments derived from a custom payload, and a semantic
form event forwarding a native submit Event. Ordinary element listeners keep
the DOM dispatcher. The rebuilt client passes its 75 checks/tests; the five
existing combined-timing browser cases also pass. Independent backend/cache
and runtime review remains before closing the component-spread correction.
Independent review confirms authenticated export and trusted cache replay keep
the runtime-spread distinction intact. Vue may combine differently modified
listeners, such as `@click` and `@click.stop`, into one listener array; both
handlers survive. Keep that native behavior. Reject duplicate emitted directive
names, which would lose an attribute during template parsing, rather than
rejecting every pair that Vue can combine. This closes the bounded component
event correction without adding a stricter modifier policy.

The next frozen core run reports 5,232 passed, 23 failed, six skipped and one
expected failure in 16.22 seconds. Its log is
`/tmp/citry-benchmark-design-core-no-e2e-20260914-post-contracts.log`.
These counts include fixture migrations and added regressions, so their change
is not a count of independently fixed bugs. The three older i18n modules pass
71 cases and retain two source failures: native `component.$i18n.bind(...)`
message-root discovery, and cache export of captured translation attribute
values. Cache-hit and binding-remap assertions remain intact for those fixes.
The bounded i18n changes pass all 29 usage/binding tests. Binding discovery
now accepts an exact member span already authenticated by component JavaScript
analysis, matching the existing `tr`/`resolve` handling. Translation attribute
values become ordinary strings only after their winning-value identity has
been checked. Cache codecs remain strict and do not accept arbitrary string
subclasses. Independent review remains before closing this correction.
Independent review confirms the authenticated receiver spans and the identity
guard, including an equal-text replacement falsifier: replacing the captured
translation with a different string containing the same text is rejected.
This closes the bounded i18n correction; that falsifier is being retained as
a regression test.

Error-fallback slots reveal a separate callback-lifecycle gap: creating an
`on_render` generator under the receiving component context does not execute
its body. Both priming and subsequent `send()` calls need that same context.
The fix must cover ordinary user generators and preserve the existing slot
placement scope; special-casing the built-in fallback component would leave
the public callback contract broken.
Both generator send paths now enter the receiver scope through one helper.
All 57 render-hook and error-fallback tests pass, including a user generator
that calls its supplied template slot before its first yield and again after
successful resumption. Existing error-fallback cases exercise the failure path.
The placement scope and session validation are unchanged; independent review
remains.
Independent review confirms both receiver and placement context variables
restore their prior values on return, generator completion and errors. The
focused regression also verifies that only the final `resume` text reaches
prepared output. This closes the generator receiver correction.

Two other integration findings remain distinct. Prepared HTML attribute
capture and plain serialization group source attributes before data attributes,
which changes the promised first-seen order when a spread overrides an earlier
static value. Debug highlighting still inserts placeholders resolved by a final
HTML hook, whereas interactive serialization builds Vue definitions before that
hook. The remaining corrections must preserve attribute precedence and Debug's
component/slot boundaries without adding an ownership graph or compiling
rendered user data as Vue source.

Debug migration uses an atomic decoration represented by an internal
`CitryRender` subtype. Its existing `parts` list remains the sole body, so
deferred component replacement and dependency traversal use the same recursion.
Immutable typed opening/closing metadata describes the visual wrapper and its
label; labels remain values. Ordinary serialization adds the wrapper after
marking and assembling that frame's real roots. Vue assembly captures the body
with its existing root-marker and slot context, then surrounds its generated
fragment and adjusts source offsets. Component/CSS/event metadata therefore
stays on the actual output roots.

The subtype must survive component finalization, while typed cache export
continues to reject unsupported render subtypes; active Debug already bypasses
render caching. Wrappers around physical full-document output are omitted.
Dropping a decoration drops the complete wrapper atomically. Repeated
serialization must not mutate it. One deliberate change is that a decorated
embedded render retains its decoration even when the receiving engine does
not install Debug: the wrapper belongs to that output, rather than requiring
a matching root serialization hook.

A standalone new render-part kind would require changes to every recursive
visitor. Generic paired sentinels would recreate the placeholder machinery.
Both were rejected in favor of the existing render-subclass model. The checks
must cover original-root markers, native slot scopes and receiver labels,
same-type siblings sharing definitions with different labels, document and
fragment browser output, extension replacement, and repeated serialization.
The implementation passes 45 static Debug tests and two Chromium tests.
Browser checks cover native refs, supplied slots reading their parent's Vue
data, distinct receiver labels and two same-type instances sharing one compiled
definition. Document delivery is exercised directly; fragment bootstrap uses
the existing delivery path and has no new dedicated Debug browser case.
Independent review caught two subtype integration defects, both corrected:
Python-composed decorated children retain their component-call identity, and
repeated decorated component roots hit the ordinary duplicate-render check.
An apparent callback-root problem came from a test using the retired `els`
argument; the test now uses `{component}` and native Vue refs, with no new
runtime metadata or bundle rebuild. The remaining review edits concern the
Debug design document's descriptions of the current implementation.

The September 14 docs machinery inventory reports 893 passed and 30 failed
in 170.33 seconds. The complete log is
`/tmp/citry-benchmark-design-docs-no-e2e-20260914-current.log`.
The failures include a missing keyword diagnostic suggestion that blocks many
landing-page/build cases, an unsupported template construct, a slot receiver
mismatch in a composer recipe, and fixtures expecting prior HTML/event
transport. Fix shared causes before repeating the full build. This inventory
does not establish a successful docs build or current benchmark qualification.
After the attribute-order correction, the frozen core inventory reports
5,257 passed, two failed, six skipped and one expected failure in 16.36 seconds.
Its log is `/tmp/citry-benchmark-design-core-no-e2e-20260914-post-debug.log`.
The remaining two failures are benchmark templates passing executable
`@click` attributes through Python mappings; migrate their authoring while
preserving the renderer's source/data boundary. This is a core test result,
not a whole-repository or browser qualification.

Attribute capture now retains first-seen resolved HTML identity order. Plain
HTML materializers share an ordered formatter, including typed leaf output
and physical document shells; Vue's generated source/data binding order stays
unchanged. The focused gates pass 60 attribute tests, 11 leaf/document cases
and 52 typed-cache tests. Independent review also passes 133 related tests
and confirms source authentication and first-seen identity behavior. It found
a separate integration discrepancy: an attribute hook can return `False`,
which plain HTML omits but Vue's data binding can stringify for non-boolean
attributes. Normalize that case before prepared delivery; the fix is pending.

Keyword typo hints are now generated by Citry on the input-error path, rather
than depending on interpreter wording. The helper requires a recognized closed
schema, one unknown supplied key and the matching argument-binding `TypeError`;
constructor-body errors are left alone. It preserves the exception object and
does no schema inspection on successful renders. Seven focused component and
landing diagnostic cases pass; independent review confirms the error-path
constraints and finds no concrete gap.

The landing template compiler failure is caused by real external script tags
inside the Vue-owned body, not a false positive in compiler validation. Move
document scripts into the physical head and retain the compiler restriction.
Docs initializers also need to wait for their DOM: the existing physical-head
script records `citry:ready` before body startup, then a docs-owned promise
resolves after parsing for static pages or after the matching root Vue app is
ready. All document entrypoints use that promise before querying elements.
This avoids both a missed early event and calling runtime readiness before
the app has mounted. It adds no Citry runtime API or private runtime-map lookup.

The composer recipe bank is intentionally inert HTML used for cloned visual
previews. Its serializer must request inert output explicitly, and its JSON
belongs in an inert text container that preserves decoded `textContent`.
Compiling a JSON script tag inside Vue's template is not supported. Separately,
isolating all 15 generated recipes identifies Tabs as the sole recipe with a
slot receiver failure. Tabs stores declaration slots and calls them later from
its internal tab/panel renderer. The implementation must preserve the original
lexical scope while representing that final placement; relaxing the receiver
guard globally would hide the defect. Both investigations remain in progress.

The real docs browser check then exposed missing prepared assets. Mounted pages
reference content-addressed definitions and styles, but the static exporter
only writes the base runtimes. The playground's asset route allowlist likewise
omits the registered prepared definition/style routes. Update both consumers
through those existing asset owners. Static export must discover references
from actual prepared configuration, not route-like strings in displayed docs
examples, and reject a missing referenced artifact. Browser readiness correctly
stays pending when asset loading fails; this is not a reason to resolve it early.
The engine retains only 128 definition bundles and 128 styles, so waiting until
all docs pages have rendered can evict early references. Export each page's
assets while writing that page, then validate the completed artifact. Separately,
the behavior of one mounted page requiring more than those retention limits
needs an explicit asset-lifetime check; a larger cache is not a durable fix.
The playground fixture migration passes 15 cases, and the formerly blocked
prepared-fragment asset case passes after allowing the two existing registered
asset routes. It checks real event dispatch and prepared values, rather than
expecting interactive content in the initial empty mount host. Static asset
export has five focused passing cases; fragment extraction and unrelated-script
false positives still require review corrections before that work is accepted.
Those corrections now pass six focused cases, including a real fragment. The
exporter reads the exact generated bootstrap framing or the inert fragment
record, then exports definitions and owned script/style assets. The real browser
run advanced beyond asset loading and found a remaining landing callback using
the prior context shape. That docs callback now receives `{component, revision}`
and accesses its single element root through `component.$el`; no runtime API
change was needed. Browser verification and independent docs review continue.
The frozen docs startup stage now passes the real Chromium landing interaction
test and a separate static/early-event/late-event readiness test. Frontend build
and checks pass, including 12 Node tests; the recipe catalog and six asset export
cases pass. Independent review of the final docs changes remains underway.
Independent review accepts the final exporter and inert recipe bank: generated
framing and fragment protocol extraction are exact, asset identities are
validated, and the bank contains 18 styles with no scripts. Controls in the
cloned visual previews remain intentionally inert. The docs readiness handshake
is also accepted; a failed Vue mount leaves it pending because the required DOM
has not become available. Callback source review remains separate.
Tracing the isolated Tabs failure confirms that slot capture inherits an outer
execution's receiver while `_VALUE_CONTEXT` identifies a later `CInternalTab`
or `CInternalTabPanel`. The eventual selected result has no enclosing slot at
that stale receiver. Correct call-time receiver selection without changing
nested fallback behavior is the next implementation question.
The attribute omission/presence correction passes 103 focused cases. Exact
`False` and `None` data attributes are omitted; `True` keeps presence metadata
for HTML serialization and becomes an empty attribute value for Vue. Authored
source attributes and Vue component props keep their existing paths. Independent
review remains; implementation review also requested removal of an unnecessary
tuple result from the per-attribute helper before broader verification.
That helper now returns only a boolean.
Independent source review accepts the bounded attribute correction: source
attributes, native Vue bindings and component props retain their distinct
paths; leaf and ordinary HTML data share the omission/presence policy.
The frozen broad core run reports
5,261 passed, two failed, six skipped and one expected failure in 17.72 seconds
(`/tmp/citry-core-vue-post-slots-20260914.log`). The failures remain the two
historical benchmark fixtures supplying executable attributes through Python
mappings. The landing callback also now returns cleanup for listeners, timers
and animation frames, and ignores late clipboard completion after cleanup.
An independent source review and one browser regression using the actual
callback verify repeated invocation and cleanup without duplicate listeners.
The next frozen docs inventory reports 911 passed and 15 failed in 177.26
seconds (`/tmp/citry-docs-vue-post-startup-20260914.log`). Several failures
assert initial HTML where the current output carries prepared data. A build
trace identifies its first real page failure in the deliberately deferred UI
examples: `cbutton/snippets/configuration.py` still uses `$c-props`. Do not
weaken build assertions or repeat full builds until that example migration.
Tabs now assembles in Python, but the lexical-scope browser falsifier catches
call metadata declared on the receiver definition while its values belong to
the lexical caller. Preserve browser preflight and project the declarations
with their supplied template; that correction is still being investigated.
The receiver-only and fill-bubbling attempts are rejected and reverted. One
misplaces definition metadata; the other routes content through an intentionally
empty declaration collector and produces no tab content. The next design uses
the existing component-call ancestry to generate native forwarding slots from
the lexical caller through Tabs and its internal renderer to the final tab or
panel. Selected template bytes and their metadata must arrive together at the
lexical caller. This design is not yet implemented or qualified; no runtime
preflight relaxation or new cross-occurrence protocol has been accepted.
The deferred UI inventory finds 208 snippet/scenario Python files across 64
component families containing `$c-props`, Alpine directives or the Alpine name.
This is a search inventory, not a count of distinct defects. Keep these examples
last as requested; their volume explains why core integration progress does not
yet imply a passing complete docs build. Native forwarding for batched calls
must pass only each member's own fills, avoiding quadratic slot-closure creation.
The native-forwarding browser falsifier now passes for generated Tabs with
lexical `v-text` in both tab and panel content and nested components. Seventeen
focused relationship cases pass. The decisive correction compares a fill's
lexical owner to the fragment's eventual data/definition owner, rather than
the intermediate physical occurrence currently processing it; otherwise an
already-projecting fragment gains an extra forwarding layer. Final fallback,
invalid-move, cache and batched-call checks remain before acceptance.
The complete direct-relationship module now passes 117 tests and typed cache
passes 52. A forced two-member deferred-slot batch expands to two ordinary
stable calls, each with exactly one fill; batches without fills retain their
existing `v-for` fast path. Forwarding checks existing parent links and rejects
cycles or a lexical owner outside receiver ancestry. Source review accepts the
metadata movement and bounded batch behavior. A browser check of the forced
batch remains before final acceptance of that additional path.
Both browser paths now pass in one frozen run: generated Tabs and the forced
two-member batch (two passed, nine deselected, 38.91 seconds). Each receiver
mounts only its own lexical `v-text` content, with no page errors. This completes
the bounded forwarding acceptance; the broader Citry UI inventory follows.
That inventory reports 2,122 passed and 289 failed in 57.85 seconds
(`/tmp/citry-ui-vue-post-forwarding-20260914.log`). Many failures still expect
initial flat HTML; real errors are handled separately. The Storybook Tabs
scenario additionally used a nontransparent declaration-only helper outside
the eventual receiver ancestry. It has no browser data/state/identity use, so
making that helper transparent preserves a native forwarding path. This is a
narrow constraint on relocated declaration content, not a rule against normal
empty or multi-root Vue components. The scenario and explicit data-owning
nonancestor-wrapper rejection pass two focused cases.

Tracing Image's duplicate-key failure shows nonroot render carriers inheriting
the outer component's call metadata. They were mistakenly creating additional
keyed wrapper identities. Only actual transparent-root frames now apply that
call metadata. Image scaling at 1/10/100 and transparent-key tests pass 13 cases,
and the Image component module passes all 63. A separate document-shell error
involves the renderer-owned escaped slot-text subtype; its bounded correction
is in progress.
The shell correction accepts only exact `_EscapedSlotText` inside the typed
body, alongside exact `Markup`; it does not broaden physical-head or arbitrary
subclass handling. Four document/slot cases and the Storybook standalone page
falsifier pass. Tour's 20 non-browser component tests also pass after the shared
key correction, without Tour source changes.

The remaining UI test migration distinguishes explicit static HTML contracts
from interactive behavior. Anatomy/no-JS/escaping tests may request static
fallback and retain their full assertions. Runtime, state and asset tests must
inspect prepared values, actual emitted assets or browser DOM. Parser errors in
legacy scenarios, missing loop keys and measured asset-budget failures are not
resolved by changing those assertions. The two server benchmark fixtures also
need a complete Vue state/binding conversion while preserving their Python
workload and plain/Const comparison; that work has started separately.

Asset-budget diagnosis distinguishes real delivered bytes from stale assertions.
The focused budget run has four failures and seven passes: catalog gzip exceeds
its limit by 1,993 bytes, catalog Brotli by 2,229 bytes, and SplitButton and
ContextMenu exceed incremental limits. ContextMenu's loaded JavaScript is
47,965 bytes raw / 11,122 gzip. An isolated minification measurement of its
current source produces 26,786 raw / 9,111 gzip, below its incremental limits.
This is a measurement, not an accepted production change. The existing UI
`tools/build_assets.mjs` already provides checked-in `.source.js` / `.min.js`
assets with Terser, and multiple components use `js_file = "runtime.min.js"`.
The planned correction reuses that build-time route for ContextMenu and
SplitButton; it adds no request-time Node dependency and does not raise budgets.
Source equivalence, generated-asset checks and behavioral gates remain required.

The bounded nine-file UI test migration now passes all 369 cases, with Ruff and
Python compilation clean. Static anatomy/escaping assertions explicitly request
JavaScript omission; interactive and asset assertions retain normal prepared
serialization. NativeSelect verifies its three option keys plus placeholder key
in generated bindings and prepared values, rather than retired HTML attributes.
Tour remains untouched because its tests already pass after the shared key fix.

The reusable Python-expression component regression has a separate narrow fix:
`citry_render._render_value` immediately renders a `CitryElement`, bypassing the
deferred queue's normal composition wrapper. It now uses the existing wrapper
on that finalized result. A proposed small reusable-leaf regression passed
without the fix too, so it was removed and is not evidence for this correction.
The full benchmark is the current before/after falsifier: without the wrapper
its reusable `_HOME_ICON` fails for missing call metadata; with it assembly
advances. The proposed cache-hit queue change did not explain the failure and
was removed. Nested replacement/slot forwarding in the benchmark fixture
remains under investigation separately.

That investigation rejected changing forwarding's ancestry walk to start at
the child call: the problematic lexical owner was the child itself, so the
change would have created a self-facing slot in the parent's scope. The earlier
misclassification occurs while transforming a supplied fill. Its output is
already destined for the lexical component's definition (`data_owner_id`), but
the slot branch compares its receiver to the outer physical traversal closure
(`occurrence_id`). The approved experiment uses the eventual output owner for
projected fragments, consistently across outlet predicates and fill routing;
ordinary body traversal retains its current owner. Existing unrelated-receiver
and ancestry guards remain. Nested-slot browser scope and forwarding tests are
required before accepting the change.

The effective-output-owner experiment was rejected and reverted: the relationship
suite had 120 passes but regressed three established supplied/fallback, dynamic
element and three-component forwarding cases. `data_owner_id` therefore cannot
replace the physical occurrence globally, even while processing a containing
fill. The next proof isolates Parent → Layout → descendant Tabs with distinct
browser data at each level, to establish the precise native forwarding chain
before considering a bounded authenticated-ancestry rule for moved results.

A narrower fallback-only projected-owner experiment passes 125 combined
relationship/identity/benchmark cases, but is not accepted: the real benchmark
mounts without a browser exception while its ProjectLayout fallback content
(Project Info/tab headers) is absent. Server metadata alone is insufficient;
the native slot/call chain must instantiate the visible content correctly.

Existing-pipeline asset extraction clears both incremental budgets: SplitButton
is 2,954 gzip bytes and ContextMenu 8,851 gzip bytes. The full asset-report
module has 24 passes / 10 failures: catalog Brotli remains 20 bytes over its
unchanged cap, with the other failures in repeated unkeyed scaling fixtures.
The exact wheel inventory now includes both generated minified assets and the
production `_direct_output.py` helper. A separate actual duplicate shared Button
runtime was reproduced with pre-extraction inline JavaScript too; it is not
caused by extraction and its deduplication assertion remains unchanged.

The slot correction is now accepted after browser proof. Exact authenticated
flattened transparent receivers have no Vue instance, so their selected content
is inlined with its lexical data and placement route; no synthetic Vue slot or
selection entry is emitted for them. Selected roots that retain a real occurrence
are excluded. The separate fallback-only rule remains necessary when a real
receiver's fallback has already reached its own projected data scope. Supplied
real-component forwarding, nested-template handling and unrelated-receiver guards
remain unchanged. The real benchmark now displays and switches its tab panels;
that browser proof and the dynamic-element lexical-scope proof pass together.
Both plain and Const benchmark fixtures render through Vue; browser proof at
this checkpoint covers mounting and tab switching, not all fixture interactions.
After source review and a freeze, the broad non-e2e/non-qualification core suite
passes **5,265 tests, with 6 skipped, 1 xfailed and 1 warning** in 16.31 seconds
(`/tmp/citry-core-vue-post-fixtures-20260914.log`). This is a core integration
gate, not final repository qualification or a new performance measurement.

Follow-up state audit found remaining fixture gaps: Tags seed data, attachment
editor data, Bookmark data and Dialog model forwarding need native Vue wiring.
Application callback stubs must be compared with the pre-migration fixture to
distinguish pre-existing synthetic behavior from lost behavior. These are pending
before declaring the fixture migration complete.

Standalone shared-asset duplication is fixed by deduplicating physical script/
style materialization using each full source descriptor, including attributes.
All per-owner manifest records remain. The focused ownership/tag proof and
existing UI checks pass; independent serialization-security plus Vue-event
validation passes 165 tests (one warning). The second ten-module UI contract
batch has 232 passing unique tests, preserving shared-runtime assertions and
separating CToast's ordinary attributes from rejected Python executable attrs.

The subsequent frozen broad UI run reports **2,258 passed / 156 failed** in
57.41 seconds (`/tmp/citry-ui-vue-post-contract-batches-20260914.log`), compared
with the earlier 2,122 / 289 baseline. Remaining failures concentrate in quality
routes/scenarios, scaling fixtures, asset budgets and further component-test
contracts. UI examples/scenarios remain last. A read-only overlapping snippet
inventory finds 124 files with `$c-props`, 158 with `x-data`, and 123 with old
structural/text directives; those counts are files/patterns, not independent bugs.
The isolated Tour rerun is 20 passes / 5 failures too; the earlier 20-pass note
was incomplete and did not establish a green module. Remaining assertions split
between static anatomy and the i18n prepared payload, rather than order-dependent
production behavior.
Tour's corrected module now passes all 25 tests, with static labels/anatomy
separate from the six prepared i18n binding messages and custom-label data.

The fixture-state follow-up preserves Tags as keyed server-prepared instances
using `c-for` for initial attachments. This intentionally differs from the old
Alpine fixture's single Python occurrence cloned by a client loop: each initial
attachment now has its own prepared Tags instance. Client-added pending rows use
native markup until a server rerender. Any future renderer timing comparison
must account for that changed occurrence count; this fixture update is not a
measured optimization. Controlled dialogs, Bookmark JSON, parent attachment
state and the original Form submit behavior are being verified in the browser.

**User-directed priority change:** pause the remaining migration work and run
repository checks, then the full eleven-adapter comparison at 140 and 1,400
outputs with separate memory observations and HTML graphs. Source is frozen at
a compilable but not fully green integration checkpoint. Both fixture render
tests pass; the newly structured deep-control browser fixture still has a
known `initialAttachmentCount` server/local data collision and pending window
listener migration. These failures must be reported by checks, not silently
fixed during measurement. After the benchmark/report stage, resume fixture/UI
tests, asset headroom, then examples/scenarios. No historical Citry/Alpine adapter
is included alongside current Citry in the new eleven-adapter graph.

The documented `check.py --profile full --reporter agent` completed in 267s
with failures, not a release qualification pass. Passing phases: lock, Rust
format/tests, Pyright, client/Fluent/protocol-copy/protocol-JS/docs/VSCode checks,
qualification pytest and validators. Failing phases: Clippy (one question-mark
lint), Ruff check/format (70 findings / 62 files), mypy (232 errors in 23 files),
protocol contracts and broad pytest (143 failed / 8,604 passed / 6 skipped /
1 xfailed). Exact evidence is `/tmp/citry-benchmark-design-check-full-20260914.json`.
The user-prioritized benchmark stage proceeds with those known migration failures
retained, and its own measured adapters must independently qualify. New profile
The local Vue migration benchmark profile selects all eleven adapters
at both counts; timing and memory reuse the same fresh prepared build.

Fresh native and Python wheels were built for this cohort. The first Python
wheel contained retired modules from stale setuptools `build/lib`; it was
rejected, that build directory was renamed into ignored quarantine without
deletion, and the rebuilt wheel was checked against live Python sources.
Current wheel digests: Citry `1681009a153b72d1ccda9edf5c00713ffd9bf7e2e0a114e49d8bf48cc66a3afa`,
core `e72a9e5905614bae22c740eeed288de4f9a63528c50ecf1dfae2399efde53832`.

The first qualification attempt exposed a harness error at Reflex 1,400 outputs:
Engine.IO's 25-second text ping/pong (`2`/`3`) was incorrectly required to belong
to a UI operation. Fault-check rows alone misleadingly showed 231 passes because
the failed normal page pair skipped its fault matrix; inspect normal sample
statuses as well. The attempt was stopped and retained. The correction accepts
only text-opcode, exact ping/pong payloads explicitly classified by the server
audit as control traffic with no operation/revision. Byte/hash/index parity is
still required; control bytes are retained separately per observation window,
and known controls after readiness do not invalidate application readiness.
Unknown, misclassified, binary or late application messages still fail. Focused
socket tests pass 12 cases and the full runner suite passes 115, with Ruff clean.
Fresh qualification uses build `cc6a066a6c528b3b2aa7034563a01f888e9e765b4bf8677873e75455ca26be75`
and run `20260914T135400Z-6f59f0ec`. No measurements from the failed attempt are
accepted as the final comparison.

The initial measurement plan repeated three normal blocks during qualification
and then scheduled another three for timing. This was excessive for the user's
local diagnostic comparison. After the user questioned the duration, the plan
changed to reuse qualification blocks 1 and 2 as timing observations: these run
the same page/action procedure with fresh application processes and no fault
injection. Block 0 contains the fault exercises and is excluded from the timing
report. Retain the complete original run and identify the report's selected
blocks and parent manifest explicitly; do not describe this as a separate timing
run. The user explicitly rejected repeating the timing matrix.

Memory uses one separate sweep of eleven frameworks at two sizes, with the same
page-pair and memory-observer functions. A retained external orchestration script
records its own digest and the effective one-block sampling budget alongside
the unchanged prepared-build identity. Independent read review confirmed the
22 page pairs and existing cleanup/error paths. Future qualification should
use a short correctness sweep, with repeated blocks reserved for timing.

The corrected qualification completed with 1,320 successful observations and
242 passing fault checks. The derived timing artifact is
`.benchmarks/results/vue-migration-cohort-latency-derived/20260914T135400Z-6f59f0ec-blocks-1-2`:
880 observations, 40 per framework/size combination. Root verified all three
filtered JSONL files byte-for-byte against their parent rows. Phase segments
sum to total latency for all 876 observations with measured attribution; four
Citry filter observations retain total latency but lack a single-HTTP-exchange
phase breakdown.

Current Citry medians at 140 outputs are 100.8 ms first load, 68.35 ms second
load, 40.8 ms select, and 41.75 ms insert. At 1,400 they are 456.8, 414.0,
328.95, and 316.35 ms respectively. Django + HTMX + Alpine's corresponding
1,400-output medians are 326.85, 320.05, 613.5, and 886.8 ms. The earlier
second-load parity is not preserved by the current migration state. Keep this
regression visible and investigate after delivering the report; do not cite
the historical optimized result as current performance. Second-load Citry
server preparation is approximately 205 ms at 1,400 outputs.

The one-block memory run
`20260914T145234Z-memory-one-block-ae46802e` completed with 430 successful
scenario observations, one Reflex 1,400-output probe failure, and nine skipped
actions. The memory file retains 430 valid rows and one invalid row. All
framework/size page-load measurements are present. Reflex's failure is a
socket count mismatch and remains visible; do not repeat the matrix to hide
it. USS is unavailable where macOS denies process access. For the second
1,400-output load, Citry server/browser RSS is 96.7/488.1 MiB; Django + HTMX +
Alpine is 70.6/556.2 MiB. These are one-sweep diagnostics, without forced GC.

The combined `report.html` and adjacent `summary.json` are in the derived timing
directory above. The report exposes both output counts, first/second-load and
action latency stacks, response/request/HTML sizes, server output preparation,
and separate memory charts. Its status explicitly identifies reused timing
blocks, one invalid memory observation and nine skipped observations. Root
opened the report in Chromium, exercised size/action/load selectors, checked
the 1,400-output memory graph, and observed no JavaScript errors. Report-only
provenance/label changes were made after measurement; 33 results tests pass.
Independent review confirmed all 44 initial memory captures, explicit USS
unavailability, separation of memory from timing, and truthful failure counts.
The derived-report validator checks parent identity and selected block IDs;
it does not itself compare every derived row with its parent. Root's exact
byte comparison supplies that evidence for this artifact. Do not assume this
manual verification automatically applies to future derived reports.

After the report, work resumed on the server-render benchmark fixture's Vue
controls. Its prepared attachment rows use a parent Vue provider and a child
injection: each row's JSON index selects the current reactive parent item.
Python loop locals are not browser expressions. Tags initialize from server
data, watch incoming tag-list replacements, and emit edits to the parent.
Review caught native handlers still reading an undefined `index`; a first-row
removal test had passed accidentally because `splice(undefined, 1)` removes
index zero. All handlers now use the prepared `rowIndex`, and the browser test
edits the second item before removing the first and checking the shifted item
and its Tags. Three focused browser tests pass, including the large page's
tabs/Bookmark and real Escape-key Dialog dismissal; plain and Const renders
also pass. These fixture changes are later than the report and do not alter
its captured canonical web benchmark applications.

CAlert's registered SVG glyphs now follow CIcon's authenticated source path:
only markup returned by the icon registry is passed to `render_template`, and
the alert template renders the resulting content with its logical-direction
metadata. Arbitrary user strings are not trusted as markup. All 43 CAlert
server tests pass. Its six older browser tests initially failed before
rendering because their Page fixture still used Alpine. The fixture now owns
Vue data, passes five native props, cleans up its test controller on unmount,
and uses the existing live asset server. All six semantic, focus, reactive
validation, RTL and CSS browser tests pass without weakening their assertions.

Mechanical repository cleanup passed Ruff formatting and focused parser
Clippy. A partial Ruff rule-selection mistake removed suppressions unrelated
to the selected rules; the agent restored the newly exposed line/rule pairs
and verified the remaining diagnostic set. It did not retain a byte snapshot
of that transient state, so restoration is not claimed byte-for-byte. The
remaining lint/type/protocol/test work is still open; this is not a green
repository gate.

The shared Events protocol coverage records now match its existing v1
schemas. The documented legacy HTML, explicit HTML and prepared Vue render
forms remain supported by their corresponding validators; this correction
changes coverage pointers and targeted invalid-message cases, not the wire
contract. Removing `clientGraphRevision` from the earlier graph-free manifest
accounts for its three retired schema constraints. Final focused evidence:
122 Python tests, 16 JavaScript tests, and zero coverage-tool problems, with
all call/descriptor/manifest/result constraints assigned. Type-checking and
the remaining UI tests still need completion.

Typing cleanup now shares a read-only metadata protocol between the prototype
PreparedView and production AssembledView. Compiler functions still require
the full PreparedView. An explicit retained mypy proof accepts both metadata
views and rejects AssembledView as compiler input; an inert pytest-shaped
proof file was removed. Exact compiler-input annotations and role-specific
locals reduced errors in browser extension preparation, Events and direct
capture from 87 to 34; 198 focused runtime tests pass. Six LSP errors caused
by reused locals and indirect tuple narrowing are resolved, with focused mypy
and four JS-data tests passing. A fresh non-incremental check confirmed the
native wrapper exports and seven-value component-analysis stub already match
Rust; the earlier missing-export errors were stale, so no stub change was made.

The next render-part typing correction preserves the runtime inheritance
checked by Const and Events/i18n hooks. The internal RenderPart alias was
narrower than the values already stored in CitryRender.parts. It can describe
the closed set of prepared part records without changing the component API or
creating a new node hierarchy. Keep nested attribute/binding metadata outside
that part union, retain serializer validation, and avoid runtime conversion
or copying solely for typing. This correction is implemented: capture typing
errors fell from 22 to zero and 555 focused Const, i18n/Events binding, prepared
capture and serialization tests pass. The first fallback guard incorrectly
excluded valid string subclasses; the existing list/custom-string/Slot tests
exposed it, and accepting string subclasses restored those cases without a
second conversion. Subsequent direct/leaf annotation work passed 318 tests
and reduced its scoped errors from 61 to 30. Exact compiler-metadata field
typing is the next bounded follow-up.

Eight remaining UI server-anatomy test modules now opt into static fallback
only where their assertions concern initial HTML. Runtime, assets, error and
translation checks retain their regular paths. All 121 tests in that batch
pass with their original behavior assertions. The modules are Tooltip, Hover
Card, Toolbar, Form, Button Group, Pagination, Infinite Scroll and Color Picker.

The action module passes all 96 tests after target/encoder harness migration
and the marker-warning correction. The updated older timing case passes,
including conditional-removal and unmount cancellation; the five combined
timing cases also pass against the rebuilt runtime. Together with the prior
14 passing selected browser cases, these close the bounded timing regression
gate. No additional client rebuild is needed for the Python-only dynamic
Events correction.

The legacy client-prop suite is migrated by contract, not by replacing syntax
inside Python strings. Obsolete raw-expression contribution and explicit JS
registration matrices are replaced by compact removed-syntax rejection cases;
existing native binding/authentication coverage stays in its original modules.
Two missing proofs now verify separation from typed Python kwargs and native
binding forwarding through a runtime-selected component. The migrated module
and two existing direct-call regressions pass 12 cases. This changes test
inventory, so failure-count reductions are not reported as one-for-one fixes.

The subsequent authoring gate passes on the shared-props/Mark source: 552 LSP
tests, 111 VS Code tests with compilation, Biome and package inventory, and
70 Pygments tests. Four LSP warnings concern the test client's advertised
Markdown capability. No source changes, dependency synchronization or native
rebuild were needed for these checks.

The marker suite now passes 21 cases. The added extension-hook case renders an
authored marker while the synthetic wrapper is active and proves that its
alias survives. This guards against identifying synthetic nodes through
ambient render state.

The existing i18n revision stage is another concrete constraint: it merges one
incoming subtree with providers outside that subtree. Two stages independently
prepared from the same old state cannot simply publish in sequence. A grouped
transaction needs one combined candidate and one plugin preparation/publication,
with all replaced roots explicitly available when determining retained
providers. Target translation must share its reserved-ID set, and callback
cleanup and delivery must deduplicate across the group. These are production
integration requirements, not evidence supplied by the earlier browser proof.

The current-doc audit also found a remaining authoring gap. The diagnostic
catalog still advertises unknown, missing and incompatible browser component
props using the retired attribute syntax. Initial source search found their
codes only in the catalog and generated binding, while native Vue prop
extraction feeds component scope typing. Restore or locate the call-site
diagnostic producers before describing these as working Vue diagnostics;
changing only the examples would conceal the missing behavior. This is a
runtime/tooling integration priority ahead of UI examples.

The semantic review must separate required/typed props from undeclared
attributes. Native Vue accepts undeclared bindings as fallthrough attributes,
and the current component options preserve that behavior. The strict unknown
prop error from the dedicated prop channel cannot simply be applied to every
`:name` binding. Restore only diagnostics justified by the selected Vue
contract; remove a retired diagnostic if that contract no longer has a valid
trigger. Missing and incompatible declared prop checks are now implemented in
the LSP and pass four focused extraction/diagnostic tests. They require a
statically resolved child and
proven current Vue prop declarations, and use source order to avoid blaming an
earlier value that a later dynamic binding could replace. Optional null values
and Vue Boolean casting remain accepted conservatively. Loop-local bindings
take precedence over equally named outer data. Parsed template nodes retain
byte offsets, including nested template values; a character-indexed tag scan
would not align with the browser expression source maps. The obsolete
unknown-prop catalog entry is removed and the two supported examples now use
native Vue bindings. Catalog validation, generated-binding checks and focused
Ruff checks pass. These checks do not establish CLI parity.

A cross-surface review found that the CLI checker does not invoke the LSP's
browser diagnostics. The initial implementation was therefore LSP-only; its
semantic rules needed to move into shared analysis with a CLI adapter.
Reuse the CLI's existing collection of current inline/file JavaScript and its
parsed template, consumer facts and byte-coordinate conversion. The two hosts
may resolve components and map diagnostics differently; source-order,
requiredness and accepted-type rules must have one implementation. Do not
remove the catalog's CLI surface merely to hide an unfinished migration.

The shared evaluator and CLI adapter now pass their focused qualification:
10 cases across CLI, core extraction and LSP, including inline/file source
parameters. The evaluator owns declared-prop semantics; each host supplies
component resolution and value-type evidence. The CLI reuses collected source
without executing loaders and proves literal values, treating other values as
unknown. Review corrected the CLI's authored-tag lookup and missing-component
exception handling before testing. The tests cover unknown and registered
tags together, required/default/null semantics, value mismatches, binding
order, shared consumers and UTF-8 spans with editor columns. A patched loader
that throws verifies that checking uses collected source without executing
the component JavaScript loader. Focused test lint and format checks pass;
this is not a fresh full authoring-suite result.

A current-doc search still finds retired prop/runtime guidance in
`advanced/dynamic-components.md`, `advanced/alpine-runtime.md`, `docs.md`,
`guides/migrate-from-tetra.md` and `guides/troubleshooting.md`. Those are current
product pages to migrate after the behavior settles, not historical benchmark
material to preserve. Remaining UI examples and scenarios retain last priority.

The bounded current-doc pass is now reviewed. The runtime page moves to
`advanced/vue-runtime.md` with the existing redirect catalog preserving its
published old URL. Dynamic components, fragments, troubleshooting, compatibility,
the docs landing page and Tetra migration guidance now describe Vue. The Tetra
snippet uses Vue Options and a same-component Render action. Review rejected an
initial rewrite that still described removed ownership comments; the corrected
page describes the generated host, configuration and fragment descriptor from
the actual producer. The serializer docstring distinguishes static root
attributes from prepared Vue delivery. A subsequent source-reviewed pass also
updates `security.md` against final-output CSP and JavaScript validation.
Executable migration snippets pass, as do three focused page-expansion cases,
22 redirect/link tests and validation of the published runtime-page redirect.
These checks do not constitute a full docs-site build.

The next current-API pass covers HTML attributes, simple components, component
JavaScript/CSS, fragments, Events actions and the migration parity table.
Review corrected native Vue fallthrough, callback arguments, declarative
fragment content and the distinction between compatible updates and element
replacement that loses focus. The parity table now identifies the deferred
ignore capability accurately. The Render docstring and action guide describe
the same contiguous immediate group restriction. All 44 cross-reference and
live-code tests pass, and the docstring passes Ruff and formatting. Root
reviewed the changed prose separately against the current source. These docs
checks do not qualify grouped runtime behavior.

The independent prose pass corrects `js_data()` documentation, the CLI
description, component binding metadata, dependency/i18n comments and both
State-on-component error messages. It describes Vue instance fields and native
prop bindings, while retaining explicit rejection of unsupported syntax. The
matching error-message test passes and Ruff lint passes for all eight changed
Python files. Two format-only discrepancies in concurrently changed runtime
files are assigned to the next routine check; no whole-file formatting claim
is made yet. Root reviewed the changed prose against the current implementation.

Callback instance types must distinguish readonly props and nested State from
writable server data and local values. Computed values with setters and
injected refs cannot be classified as universally readonly. Where analysis
lacks that distinction, a conservative writable unknown value is preferable
to a false readonly diagnostic. Official Vue namespace signatures should be
generated and version-checked rather than maintained as a handwritten facade.

A subsequent independent authoring audit identified four remaining LSP cases.
Conditional `js_data` roots retain presence information during analysis but
lose it when the callback instance type is generated; open shapes also become
closed types. Preserve known fields, make conditional fields optional, and
allow unknown writable names only when analysis cannot close the namespace.
Shared scripts must retain each actual component owner's constraints.

Known `js_data` collisions with Options, reserved or plugin-owned instance
names also need source-mapped diagnostics. Unknown data shapes alone do not
prove a collision. An optional conflicting field may fail when supplied, so
its diagnostic must not claim every render fails. The configured i18n plugin's
public `$i18n` getter needs its service-or-null callback type and participates
in those collision checks. Finally, unknown inject sections must keep their
known names without making Vue's official inject generic reject additional
names. These four corrections are implemented; existing readonly props,
deep-readonly State values and writable local values remain the contract.
VS Code delegates this projection to the LSP and needs no second declaration
implementation.

Six focused tests pass, including actual TypeScript checks for invalid scalar
computed definitions, valid computed getters and setters, known names inside
open inject declarations, nullable callback `$i18n`, and optional/open
`js_data` roots shared by two component owners. These tests also retain the
inferred-data and public-name collision checks. The full LSP package suite
also passes: 534 tests, with four test-harness/client-capability warnings.
Package-wide Ruff lint and formatting pass as well (26 files).

The editor gate also passes TypeScript compilation, Biome, 111 tests and VSIX
inventory checks; the Pygments suite passes 70 tests. The source-control audit
found the global `node_modules` ignore rule hid the vendored Vue declarations.
Two path-specific exceptions now expose only the LSP's declaration tree.
Its inventory matches 31 payload files: 11 declarations, 10 package manifests
and 10 licenses, totaling 1,838,309 bytes. All payload paths and the inventory
are visible to Git, while unrelated dependency directories remain ignored.
The local LSP wheel also passes closed inventory, checkout-byte equality,
metadata, RECORD and license verification. Its compressed size is 350,764
bytes, below the existing 512 KiB limit. This qualifies the local wheel;
the final integrated repository gate remains pending.

Missing workspace test dependencies were installed from the existing lockfile
using the exact existing CPython 3.12.13 environment, after a dry run proved the
operation only added 14 packages. The interpreter and native extension were not
recreated. Subsequent checks use explicit existing interpreter/tool paths.

The existing locked `e2e` dependency group was later exported without workspace
packages and installed into that same environment. A dry run confirmed exactly
13 additions and no removals. This supplies Playwright and its pytest fixtures
without rebuilding the native extension during in-progress source changes.
Browser checks reuse the existing pinned Chromium installation under
`.benchmarks/browsers`; a missing optional test fixture is no longer a reason
to skip the mounted integration proofs.

## Component-call bindings

Prepared Vue component calls preserve Vue's authored binding syntax instead of
converting browser expressions into Python kwargs. On an ordinary
`<c-Child>`, `:name` and `v-bind:name` are native props, bare `v-bind` is a Vue
object binding, `@name` and `v-on:name` are native component listeners, and
`ref` or `:ref` are respectively static and expression refs. Static refs retain
their literal value; they are never reinterpreted as JavaScript identifiers.
Python `c-*` attributes and `c-bind` remain server-evaluated component inputs.
`@c-*` remains the Citry Events channel, while `:c-*` remains HTML state syntax
and is invalid on a component boundary. The retired `$c-props` and
`c-$c-props` spellings are not aliases for native Vue props.

The existing component-input resolver records source-ordered browser bindings
without evaluating their expression text. Direct prepared capture emits those
bindings on the generated Vue child call and supplies a typed declaration for
each binding to the compiler. A declaration carries its kind, authored
attribute name, expression or literal value, and UTF-8
source span. Object bindings and explicit bindings keep Vue's normal
source-order behavior; Citry does not add a last-wins or duplicate-target rule
beyond what the pinned Vue compiler accepts.

The native Vue compiler is the trust boundary for generated call attributes.
It matches every declaration to the exact child opening span and source bytes,
rejects undeclared or mismatched generated bindings, and returns normalized
binding metadata. Python compares that validated result with its request,
includes it in the definition identity and helper contract, and publishes it
with the compiled definition. Browser validation checks the normalized
artifact identity but leaves value evaluation to Vue in the caller's lexical
scope. Other host-language implementations remain unchanged; these
declarations belong only to the prepared Vue compiler path.

Calls that cannot prove this contract, including optimized call runs carrying
unsupported bindings, use the ordinary prepared-call path or fail closed
before compilation. They never discard a binding. Coverage includes native
props, object bindings, listeners, both ref forms, server Events separation,
Python kwargs, slots, UTF-8 spans, source ordering, fabricated declarations,
and updates evaluated in the caller's Vue scope.

## Component JavaScript analysis

The native implementation in `crates/citry_template_parser/src/browser.rs`
uses JavaScript syntax and lexical scope to collect public names from Options
props, methods, computed properties, inject entries, and object returns from
data/setup. Python analysis, the checker and LSP consume these facts and their
explicit unknown-section state. The callback-context and i18n consumers still
need final verification against the actual two-field `onServerRender` contract.

Each known name retains its origin and exact source position for diagnostics
and navigation. A computed
property name, unknown object spread or indirect return must remain explicitly
unknown; do not claim to know every returned field or execute JavaScript during
analysis. Callback context analysis must describe the actual
`onServerRender` context. General free-name analysis must also cover Options
methods and setup bodies, with ordinary JavaScript lexical shadowing.

The cross-binding audit covers Rust output, PyO3 tuples, Python stubs/wrappers, exported
analysis types, checker consumers, LSP generated declarations, i18n consumers
and tests. Passing directive tests alone cannot close the authoring-tools stage.

### Reviewed native analysis contract

Independent review found that a flat set of names is insufficient. Return a
state for each Options section: absent, complete, or unknown, with the source
span and reason for unknown results. A spread or computed key inside one
section leaves its explicit sibling declarations available while making the
additional names unknown. At the top level, a later spread can replace an
earlier section completely; a later explicit section restores knowledge of
that section. Do not present declarations from a possibly replaced section as
unconditionally present.

Each public-name record keeps the authored name, the name Vue exposes, its
origin, exact name span and optional value span. This preserves prop
camelization and existing constructor/default/required type information. Keep
duplicate declaration records and source order for downstream diagnostics;
collecting facts does not introduce new errors for duplicates that native Vue
permits. Apply Citry's actual runtime collision rules, including `js_data` and
installed plugin context names.

The proposed native result contains authenticated helper call/argument spans,
free references, public-name records, section states, callback-context bindings,
and component-instance member references. `onServerRender` bindings expose
`component` and `revision`, including local aliases and resolved reference
spans. Retire the unused callback scope-write analysis rather than carrying it
into this model.

Prior art also exposed two syntax authorities: Rust's OXC visitor recognizes
the root-unresolved `$component` helper, while
`ext/dependencies/scripts.py::_component_call_spans` uses a hand scanner.
Runtime transformation and `uses_component` must consume the authenticated
native helper spans too. Test locally shadowed helpers, property access and
multiple or conditional registrations so analysis describes the code that
Citry actually registers.

I18n extraction needs exact instance-member references. Recognize
`this.$i18n` inside native Options methods, computed getters/setters and data
functions, plus nested arrows that
inherit that `this`, plus `component.$i18n` through the resolved server-callback
binding. Ignore unrelated objects, local variables with the same spelling,
shadowed aliases and `this` inside nested ordinary functions. The Python
extension, checker and LSP must consume the same proven receiver spans.

The concrete cross-binding update covers `browser.rs` and its Rust exports,
`citry_core_py/src/template_parser.rs`, `_rust.pyi`, the Python template-parser
wrapper, `_browser_expressions.py`, public `analysis.py` exports, checker
namespace construction, LSP synchronized JavaScript asset loading and hover
declarations, i18n extraction, and the component script transformer. The host
language code generators do not consume this analysis result; their grammar
and generated component templates are unchanged by this stage.

Decisive tests cover object/array props, direct data/setup object returns,
methods/computed/inject, unknown spreads and indirect returns, top-level
override order, duplicate and normalized prop names, UTF-8 spans, callback
aliases/shadowing, authenticated i18n receivers, free globals in owned callable
bodies, and matching transformer/analyzer helper selection. Checker and LSP
must both resolve known Options names and avoid closed-namespace errors when
the available namespace is unknown. This requires no new template grammar.

## Native directive coverage still required

The prepared compiler currently permits a bounded helper set. Its model helper
coverage includes text inputs, while checkbox, radio and select models need
their native Vue helpers before the corresponding UI widgets can migrate.
Custom translation directives also need `resolveDirective` and runtime lifecycle
metadata. The current lifecycle classification recognizes model and show.

Expand this contract from actual widget and translation examples. Keep native
helper validation, Python helper selection, generated artifact identity and
browser execution consistent. Directive removal or changes to modifiers must
still trigger the agreed element replacement and cleanup behavior. Do not admit
a helper without testing its generated call and its browser lifecycle, or bypass
the compiler by evaluating expression strings in a plugin.

The replacement identity must include the selected runtime directive behavior,
not only the authored directive name, argument and modifiers. For example,
changing an input from text to checkbox can change Vue's model helper while
keeping `v-model` unchanged. Qualify that transition and dynamic input types
with real events so stale input listeners cannot survive a server revision.
Also cover an enclosing replacement's descendant cleanup and callback order.

## Dynamic ordinary elements

The next bounded implementation retains parser-authenticated static event and
property binding source on dynamic elements, separately from Python attribute
data, and adds the existing evaluated `#c-key` behavior. The current dynamic
producer loses that distinction when it combines all attributes into a dict.
The correction must apply the same source/data collision and unsafe-property
checks as ordinary elements and preserve provenance through cache replay.
Accepting executable Python attribute strings would bypass that distinction;
adding a wrapper Vue component would add an instance without solving it.
Tag-dependent directives remain a separate compiler qualification task.

`#c-ignore` also remains separate. An ordinary directive cannot prevent Vue
from reconciling child VNodes. Preserving a subtree across server revisions
needs an explicit lifecycle primitive, with tests for replacement, removal,
nested components and cleanup. A passive HTML marker is not an implementation.
The canonical rendering benchmark needs both the dynamic-element correction
and migration of its authored examples, which still construct executable
Alpine attribute strings in Python.

The first implementation of dynamic bindings passes the author's focused
Python and cache selections and is under independent review and browser proof.
Its event support is specifically named `@event` and `v-on:event`; object-form
`v-on` still needs a separate authenticated classification. Review found that
object and dynamic-argument bindings could collide with a Citry-generated key
when no other Python attribute was present. Both dynamic and ordinary element
paths need the correction: an evaluated private key counts as a prepared
target for those ambiguity checks. Key-only cases are required regressions.

The final key and root-marker corrections are independently accepted across
ordinary, dynamic and optimized leaf paths. Browser testing also found a
nested supplied-slot predicate reading the caller's preparedData while its
selection value lived on the receiver. Store that value with the context that
evaluates the generated predicate, preserving the receiver and movement guards.
Independent review accepts this bounded correction. Caller lexical scope and
independent cached instances pass two browser cases; tag/key revision cases
await the corrected event-timing build and are not yet counted as passing.

The dynamic `<c-element>` built-in currently constructs trusted opening and
closing HTML strings in `components/dynamic.py`. Prepared Vue output needs
typed element boundaries from that exact producer, after the same tag-name,
attribute-hook and void-child checks. Python-resolved attributes remain data.
Directly authored static Vue bindings on a dynamic tag remain an explicit
prepared-output error until their tag-dependent semantics are carried through
the native declaration contract.

An independently reviewed implementation direction is to emit a unique
placeholder tag for each declared dynamic element site. The native compiler
must classify only those exact tags as ordinary custom elements, validate each
against its declared parsed site, and return the checked mapping as part of the
compiled artifact. The existing VNode helper wrappers translate the placeholder
to the validated ordinary DOM tag. This avoids a wrapper element or Vue
component instance. It prevents Vue component resolution for qualified ordinary
tags, including literal `component` and `slot` elements.

Directive compilation can depend on the actual tag. In particular, model
bindings on dynamic inputs, selects and textareas need separate qualification;
the compiler must not choose behavior from the placeholder name. Admit a
directive on this path only after proving that its generated behavior is
tag-independent or explicitly providing the real tag to its transformation.

The mapping must be definition-scoped or use collision-proof aliases. Its
identity belongs in the compiled content and helper contract. Authored or
undeclared reserved aliases are errors. Rewriting generated JavaScript to add
another helper call was rejected because it would require parsing the generated
code a second time.

Dynamic `script`, `style`, and `template` are rejected in prepared output;
an alias cannot bypass that policy. DOM behavior for
`textarea` and `title`, SVG/MathML namespace propagation,
`foreignObject`, case-sensitive attributes and changing tags on a server
revision all need browser proof. Unsupported cases remain explicit errors until
that proof and implementation are complete. Static and JavaScript-omitted
serialization retain their existing ordinary HTML behavior.

## Prepared root-marker projection

Prepared Vue definitions preserve the generic internal root-marker facility
as data-origin attributes. Each component's own markers precede inherited
markers by normalized attribute name. Markers project onto every physical root;
when a child component or supplied slot fill occupies that root position, the
markers continue to that output's physical roots. Nested elements do not inherit
them. This preserves CSS-variable scoping as well as non-executable extension
markers without restoring Events ownership stamps.

The prepared path accepts one ordinary bare or double-quoted `data-*` attribute
per marker. Vue directives, other attribute namespaces, unsafe DOM properties,
malformed markers, and normalized-name conflicts with authored or resolved root
attributes fail explicitly. Dynamic values travel in occurrence data. Static
grouped markup retains immutable opening-depth metadata when it is compiled and
receives a compiler-owned `v-bind` at each physical root, with matching native
element metadata; assembly does not parse the HTML again and marker values never
become executable template source. Leaf programs use their already-recorded
typed fallback when root inspection is required, without reevaluating Python
expressions or hooks.

Prepared stylesheet assets carry the sorted stable occurrence IDs that require
them. A subtree revision replaces only references owned by that subtree. The
browser loads a new content-addressed sheet before publishing the revision and
removes the old element only after the Vue update succeeds and no committed
occurrence or in-flight stage in that app references it. Initial styles retain
their app identity and content URL in exact ownership markers. Each app owns
its own stylesheet element, so disposing one app preserves another app's sheet
and unrelated authored links, including links with the same URL.

Every prepared script and stylesheet has a closed owner union and source union.
Component stylesheet owners name the stable type and exact selected occurrence
IDs; extension owners name the installed browser extension. Component references
are replaced with their selected subtree. Extension contributions describe assets
selected by one render, so their references accumulate for the app lifetime and
retire when that app is disposed; a child revision does not imply a complete
replacement of an extension's prior assets. Shared URLs deduplicate only when
their effective source attributes and integrity metadata are identical.

Inline extension assets are published as Citry-owned content-addressed resources.
External URLs retain their structured dependency attributes, including
`integrity` and `crossorigin`. Declared integrity metadata is validated before
loading; Citry-owned resources also carry the digest of their response bytes.
The existing `citry` integrity policy permits third-party URLs without declared
integrity. No additional mandatory third-party integrity setting is introduced.
The page nonce is fixed by the bootstrap and applied by the client, and extension
contributions cannot replace it. Executable extension scripts load at most once
per app and URL; their effects are not described as rollback-safe.

### Citry UI navigation and compound-output pass, 2026-09-13

Accordion root/item, Listbox root/option, NavigationMenu, Tabs, Tree, Toolbar,
and Pagination client hooks now use native Vue `onServerRender`. Public-prop
fallbacks live under `serverDefaults`. Listbox, NavigationMenu, Tree, and
Toolbar browser suites pass 4/4, 5/5, 3/3, and 4/4 respectively.

Accordion and Menu direct-child validators now traverse typed prepared parts
while their existing HTML parsers retain declaration identity and order, one
expected root, transparent-only wrappers, and rejection of stray text,
comments, and elements. Accordion plus Disclosure pass 70/70 focused server
tests. At this earlier checkpoint, Menu passed its first 29 browser cases,
including keyboard, hover transfer, radio, submenu, and native-fieldset
behavior. Its four-case controlled and uncontrolled disabled handoff matrix
also passed. SplitButton passed 7/7, including native submit/reset ordering and
shadow-root registry cleanup. The current family totals appear at the start
of this document.

TimePicker options carry the authored `#c-key="option.value"`. Native selection,
form submission, editing, and reset flows pass. Its remaining locale failure
also reproduces in the core direct-provider test. CButton now keeps public-prop
fallbacks under explicit `serverDefaults`; this removed the `block` collision
and unblocked Toolbar's browser suite.

The Menu, ContextMenu and SplitButton native browser selections now pass. One
full Menu run transiently observed the root native popover closed after a loop
configuration handoff even though nested focus and popovers were restored; the
same focused case and a fresh complete run passed, so no timing workaround was
added. ContextMenu's earlier nested-text and document-shell assembly blockers
were resolved in the typed runtime rather than bypassed in component code.

The current executable source sweep finds no legacy `$component` `init` hook or
callback context containing `els`, `scope`, or the retired `init` data/effect
arguments. This pass migrated six file-backed UI runtimes and regenerated each
source/min asset pair; the five Infinite Scroll snippets, landing editor, and
browser-i18n example now use Vue Options or `onServerRender({ component })`.
The CFormCollection instructional snippets are already on the current Vue API.
Historical migration notes and versioned material may still mention the old
contract as context, but they are not executable current examples.

## Python-composed component occurrence sites

An authored `<c-child>` call already carries its parser source span, explicit
key and authenticated component-tag bindings. A component returned directly by
a callable `Slot` has no such authored call. At that public Python callable
boundary, direct rendering marks an exact returned component root, or immediate
component-root children of an exact transparent render, with a typed
Python-composition call. Authored children already carrying parser call metadata
remain authored calls. Direct rendering also records template fills through
their `DirectFillSource`, each `DirectSlotRender` execution, its
receiver outlet source/span, writer source/span and the nested execution chain;
`DirectSlotRender` keeps a component-root result as one structured child rather
than flattening it. This is the prior-art traversal boundary for an explicit
Python-composition call site.

The prepared identity for that call is positional: nearest logical occurrence
owner, the existing stable slot placement route, a local Python-composition
ordinal, and stable component type. Two sibling returned components receive
different local ordinals. Repeated executions of one callable outlet receive
distinct stable placement sites from the outlet's existing site counter.
Transparent wrappers retain the route while their physical children are
traversed. The identity never includes a Python object identity, live render
ID, or rendered user text. The same type at the same position retains its
occurrence; changing type replaces it, and reordering unkeyed Python-composed
siblings has positional semantics.

Only the explicit internal Python-composition call variant may use this route.
It carries no authored Vue props or events and cannot manufacture authenticated
bindings. Native template calls continue to require their parser-issued call
metadata. Cache export and replay preserve the variant and its local ordinal so
replay cannot silently turn a Python-composed call into an authored call.

## Fragment dependency loading

Interactive fragments retain the inert
`script[type="application/json"][data-citry-vue-fragment]` transport. A versioned
`citry-vue-fragment/1` protocol record carries the app id, exact host selector, and
prepared configuration as structured JSON; the browser does not recover a
mount command by parsing JavaScript source. The fragment record contains only
that Vue descriptor: legacy dependency fields are rejected even when empty.
Before loading assets it validates the complete definition, script, style,
owner and extension contract, then requires the bound host to resolve exactly
once inside `body` and outside every other live Citry Vue host. Styles load
before scripts, scripts execute in manifest order, and the host binding is
rechecked after asynchronous loads and plugin preparation and immediately
before plugin activation and mounting. If a load settles after the host moves
or is removed, the guard rejects the mount and disposes its staged app.
Pending and mounted fragment hosts are tracked. From the start of loading, a
child-list or attribute mutation that leaves the exact host selector, original
parent, body containment, or foreign managed-host boundary invalid aborts that
attempt's consumer waits, even when the underlying resource never settles.
This covers selector dependencies expressed through element and ancestor
attributes, including `id` and `class`; it does not claim changes that exist
only in selector pseudo-state. Rejection releases the exact attempt's partial
app and unreferenced stylesheet records; immutable asset loads shared by
another app continue independently.

The fragment observer consumes each exact manifest element once and scans only
new element subtrees. Repeated public loads of the same manifest tag receive
the same settled or pending promise. A separate attribute observer exists only
while fragment hosts are pending and disconnects when the pending count returns
to zero, avoiding steady-state observation of Vue attribute mutations. The
child-list observer tracks mounted fragment hosts; after a mutation batch, one
microtask checks those hosts for disconnection and unmounts their prepared
apps. Component scripts are shared by immutable URL identity;
extension scripts and all stylesheet ownership remain per app. Dynamically
created assets always use the nonce captured by the loaded document runtime,
never a later fragment response's nonce.

## Settled-output security scanning

JavaScript and CSP validation inspect final HTML bytes after serialization
hooks. They must not send those bytes back through Citry's template compiler:
generated JavaScript and literal `{{` text are output data, not Python template
expressions. The scanner uses html5gum's tokenizer with html5ever's tree-builder
feedback so tokenizer states follow HTML parsing rules across RCDATA, script
data, SVG and MathML integration points, malformed table/select content,
foreign-content breakouts, and HTML self-closing syntax.

The language-neutral scanner lives in `citry_html_transform`; the PyO3 layer
only converts its source facts. Facts retain exact UTF-8 byte spans for each
originating start tag and every authored attribute. Trust applies only to an
exact originating start-token offset. The security consumers conservatively
inspect source token facts and may reject a token that the final DOM omits;
they do not infer trusted provenance, parentage, or form ancestry from a
separate hand-written tree builder. Browser comparisons and relevant html5lib
cases cover HTML `title`/`textarea`, SVG and MathML integration points,
foreign breakouts, ignored insertion-mode tokens, scripting-enabled `noscript`,
escaped script states, duplicate attributes, malformed markup, and multibyte
span boundaries.
