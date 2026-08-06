# Design: AlpineJS and the Citry client component model

**Status (2026-08-04): normative landed design; A0 through A10, client
ambient context, and ComponentRange morphing implemented.** The maintainer selected
the Citry graph-first Alpine architecture and the
`$c-props` component-boundary directive after the research and spike program indexed in
[`alpinejs/`](alpinejs/README.md). This document is the source of truth for
Alpine ownership, client component scopes, props, component-tag event
handlers, slot-fill scope, root shapes, and their interaction with the Events
runtime. [`events.md`](events.md) remains normative for the Events protocol,
State, actions, transport, and queue. [`component_slots.md`](component_slots.md) remains normative
for Python slot values and server rendering. If their older Alpine-specific
wording conflicts with this document, this document wins.

Section 4.7 summarizes the implemented client `$provide`, `$inject`, and
`$unprovide` design. Its complete public semantics, prior-art review, phasing,
and acceptance plan live in
[`component_provide.md`](component_provide.md#10-client-provide-inject-and-unprovide-design).

The graph-first target is the supported production baseline. Section 12
summarizes the landed architecture and the separate future extensions that
were deliberately left outside it. Implementation history and closeout
evidence live in [`alpinejs_plan.md`](alpinejs_plan.md).

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. Decision in one paragraph

Citry owns a runtime-neutral graph of component instances, lexical source
locations, slot fills, physical DOM regions, and stable browser anchors.
Pinned stock Alpine remains the expression evaluator, directive engine,
reactivity layer, DOM-magic provider, and morph integration. Citry adapts
Alpine to the graph where logical ownership differs from DOM ancestry. It does
not replace Alpine with a virtual DOM, a second evaluator, or a fork. Citry
component boundaries are isolated by default. Values cross them only through
explicit channels: `$c-props` down, component-tag Alpine or Citry handlers up,
slot ownership links across, provide/inject for intentional ambient context,
and Events State for the server contract.

This is graph-first Alpine, not Alpine-first component discovery. HTML remains
the authoring surface and Alpine still executes `x-*`, but Citry's component
and slot graph decides which logical scope an expression belongs to.

## 2. Goals and invariants

The design has eight non-negotiable invariants.

1. **Isolation is the default.** A child Citry component does not inherit the
   parent's Alpine data, refs, IDs, or Citry magics merely because its roots
   are DOM descendants.
2. **Crossing a boundary is explicit.** Props, handlers, fills, ambient
   context, and server State each have separate contracts.
3. **Authored source and physical carrier are separate.** A handler may be
   authored in the parent and physically listen on a child root. Both facts
   remain available at evaluation time.
4. **Components are not required to have one element root.** Single-root,
   multi-root, text-only, empty, mirrored, nested, and adjacent regions all
   have one logical lifecycle model.
5. **User `x-data` is user-owned.** Citry never writes component fields into
   it and never flattens a child into an ancestor's data stack.
6. **Server and browser identities stay distinct.** Fresh render IDs describe
   server output. Render IDs use only lowercase ASCII letters, digits,
   hyphens, and underscores because they are embedded in case-insensitive
   `data-cid-*` attribute names. Stable browser anchors own continuity across
   compatible morphs.
7. **Alpine integration is pinned and tested.** Private API use is allowed
   when it is the best mechanism, but it is version-coupled, isolated behind
   an adapter, and guarded by canaries.
8. **No wrapper element is introduced for framework convenience.** Logical
   ranges and groups carry framework metadata when rendered HTML has no
   suitable element.

## 3. Responsibilities

### 3.1 Citry owns

Citry owns:

- the component, fill, source-location, physical-region, and browser-anchor
  graph;
- component isolation and explicit ownership transitions;
- `$c-props` and all `$c-*` client-runtime directives;
- relocation of component-tag Alpine and Citry handlers;
- the component registration, init, cleanup, and managed-helper lifecycle;
- grouped listeners for multi-root targets;
- comment-owned logical ranges for rootless targets;
- stable instance continuity and the transaction around server morphs;
- the bridge from an authored source location to Alpine evaluation;
- Citry magics such as `$state`, `$loading`, `$error`, `$sendEvent`, and
  `$onEvent`;
- diagnostics when a Citry-owned contract cannot be satisfied.

### 3.2 Alpine owns

Pinned stock Alpine owns:

- `x-data`, `x-bind`, `x-on`, `x-model`, `x-show`, `x-transition`, `x-if`,
  `x-for`, `x-teleport`, `x-effect`, refs, IDs, and ordinary Alpine plugins;
- parsing and evaluating Alpine expressions;
- reactivity primitives and effect scheduling;
- standard directive semantics inside a Citry-owned logical scope;
- physical DOM magics where this design says the physical carrier wins;
- DOM morph mechanics through the pinned `@alpinejs/morph` plugin.

Citry keeps genuine Alpine directive names unchanged. Its component-boundary
props behavior is the Citry-owned `$c-props` directive.

### 3.3 Events owns

The Events extension owns the server-interactive layer:

- State tokens and `$state` writes;
- event declaration, validation, dispatch, transport, queueing, actions, and
  loading/error surfaces;
- Events anchors and keyed continuity where those are consumed by a server
  render;
- compiled `@c-*`, `:c-*`, and `#c-*` behavior described in
  [`events.md`](events.md).

The general Citry client registry sits below Events. A component can be
client-active because it has `$component`, `$c-props`, a relocated handler, a
client-owned scope, or an Alpine-owned fill even when it declares no Events.
Events attaches its State and queue state to the same stable browser identity
when present.

## 4. Public authoring model

### 4.1 Registering component client behavior

Each component class may register client behavior exactly once with
`$component`. A second registration for the class throws before changing the
original registration.

The bare form receives the context and may return a cleanup:

```js
$component(({ els, data }) => {
  const chart = drawChart(els[0], data);
  return () => chart.destroy();
});
```

The config form adds a prop declaration:

```js
$component({
  props: {
    theme: { type: String, default: "light" },
    onSelect: { type: Function, required: true },
  },
  init: ({ els, props, scope, effect }) => {
    scope.select = props.onSelect;
    effect(() => updateTheme(els, props.theme));
  },
});
```

`init` may return the same cleanup as the bare callback. The registration is
one definition per component class, but its callback fires for each live
instance render revision after the declaration, current prop supply, source
links, and ancestor init dependencies are ready. On a correlated rerender,
Citry disposes managed effects, runs the previous callback cleanup, and then
fires the callback with the fresh `id` and `data`. This preserves the landed
`js_data()` lifecycle contract; it does not mean one callback invocation for
the whole lifetime of a stable browser anchor.

`init` is synchronous. Returning a Promise does not extend the invocation or
delay descendants: Citry logs a pointed unsupported-init diagnostic, handles
rejection, and settles that DAG node synchronously. A Promise continuation
cannot register a managed effect or decorator cleanup after the invocation is
disposed. Direct writes that such a continuation kept on the stable
`scope` object are ordinary JavaScript writes and cannot be cancelled; code
that needs asynchronous work must own and guard that work explicitly.

The target context is:

```js
{
  id,       // current server render id
  els,      // stable live array of all current element roots
  data,     // inert js_data() payload for this render
  state,    // Events State facade, or null
  props,    // reactive read-only declared-props view
  scope,    // stable reactive component-local Alpine scope
  effect,   // managed Alpine effect
  reactive, // managed Alpine reactive helper
  graph,    // current ownership route and source metadata
  provide,   // client ambient-context helper; section 4.7
  inject,    // client ambient-context helper; section 4.7
  unprovide, // client ambient-context helper; section 4.7
  sendEvent,
  onEvent,
}
```

`els` keeps its array identity while its members track the live physical
roots. Rootless output has an empty `els` array. Under the locked hybrid mirror
policy, one logical owner sees all governed live roots in physical document
order while ordinary Alpine state and directive lifetime remain local to each
physical copy.

`data` remains the hash-deduplicated, inert result of `js_data()`. It must not
be mutated to expose instance-local Alpine variables because sibling
instances can share it. `scope` is the mutable client-local bag. `state` is
the server contract. `props` is the one-way input contract.

### 4.2 Supplying props with `$c-props`

The parent supplies client props on the child component tag:

```html
<c-chart-card $c-props="{ theme: $state.theme }" />
```

`$c-props` is a Citry client-runtime directive. Its value is an Alpine
expression evaluated in the exact scope where the component tag was authored.
It must synchronously return a plain object.

The server-dynamic attribute form is deliberately allowed:

```html
<c-chart-card c-$c-props="props_expression" />
```

Here the ordinary `c-` rule evaluates the Python expression
`props_expression`; the result is the raw client expression string carried by
the `$c-props` binding. This is a **component-tag client binding**: a
browser-side `$c-props`, Alpine event handler such as `@click`, or Citry
handler such as `@c-save` or `@c-poll.5s`, resolved from a nested `<c-*>` tag.
The parent owns the expression or server handler, while the child supplies the
component boundary where the browser applies it. The `c-$c-props` spelling
looks unusual because two orthogonal rules are composed. That is preferable to
inventing an exception. A `c-bind` mapping may likewise contain a `$c-props`
key.

Direct, server-dynamic, and `c-bind` contributions resolve in template source
order. For an exact client binding key, the last contribution wins. `None` or `False`
removes it, `True` is invalid, and a present value must be a string.
`$c-props` and Alpine handler values are Alpine expressions. A Citry `@c-*`
value is an Events binding: a declared server handler name with an optional
parenthesized Alpine expression for its argument object. Replacing a winner
keeps the winning contribution's position in final handler order. Removing and
later re-adding places it at the re-add position. `@click` and `x-on:click`
remain distinct exact keys.

`$c-props` is valid only on a Citry component boundary, including
`<c-component>`. A runtime dynamic component records the A1-locked transparent
caller-to-selected-target init edge; the wrapper remains diagnostic server
detail and never becomes the client binding target. A literal occurrence on plain HTML
is a template-load error. A dynamically resolved occurrence fails at render
time. `<c-element>` chooses a plain HTML element, so it rejects `$c-props` and
follows the normal HTML path for handlers and bindings.

After those source-ordered contributions resolve, a surviving `$c-props`
binding requires a live `$component(...)` registration in the **actual target
component's** JavaScript. This is a capability check, not a root-shape check:
transparent and rootless components may receive props when they register, but
ordinary components and framework built-ins without a registration fail at
render time. Runtime `<c-component>` selectors are followed through every
transparent wrapper to the final selected target, and diagnostics retain the
authored call site. A final `None` or `False` removes the binding and therefore
requires no registration. Cached ownership is checked against the current
target registration before replay staging; stale artifacts fall back to the
same live-render validation.

Authoring, diagnostics, implementation, and normative examples use
`$c-props`.

The name is lowercase and its expression is non-empty. Stock Alpine ignores
it; Citry discovers and evaluates it. Alpine `x-bind:$c-props` and an
`$c-props` key in Alpine's object-form `x-bind` do not create the directive on
Alpine 3.15.12, so dynamic server-time presence uses `c-$c-props` or Citry
`c-bind`. Runtime code uses attribute APIs or `CSS.escape`; a raw
`[$c-props]` selector is invalid CSS. HTML parsing, cloning, mutation, morph,
table/select contextual parsing, and HTML-parsed SVG preserve the name.
Standalone XML and XML SVG do not, and are not supported transports for this
directive.

### 4.3 Prop declaration and updates

Each prop definition supports:

- `type`: one constructor or an array of accepted constructors;
- `required`: false by default;
- `default`: a value or a per-instance factory.

Object and array defaults must be factories. Citry calls a factory once per
logical instance and keeps that result for the instance lifetime. This avoids
cross-instance sharing. The resolved props view rejects top-level assignment
but does not deep-freeze nested objects.

Only declared keys enter the props view. Unknown own enumerable keys are
ignored while valid siblings apply. Citry reports one direct console error per
instance and key failure episode; a later evaluation without the bad key
re-arms the report. Prototype-sensitive keys are never assigned.

Initialization waits for the first valid supply or for defaults when no supply
exists. A missing required prop, wrong type, invalid declaration, thrown
supplier expression, Promise, thenable, or non-object result produces a
pointed diagnostic. First-supply failure skips init but settles the dependent
branch so unrelated work cannot deadlock.

Updates commit per declared field. A valid sibling applies even when another
field is invalid. An omitted optional field returns to its stable per-instance
default, or to `undefined` when it has no default. A missing required field or
a value with the wrong type clears that field to `undefined`. A thrown
supplier, Promise, thenable, array, class instance, or other non-plain-object
result clears the whole declared bag to `undefined`. A later valid evaluation
recovers normally. Diagnostics are deduplicated for one continuous
instance-and-key failure episode and re-arm after that key recovers.

### 4.4 Ordinary attributes remain component inputs

Only these component-tag families receive special client-boundary treatment:

- `$c-props`;
- Alpine handlers, including `@...` and `x-on:...`;
- Citry event handlers, `@c-*`.

Everything else, including `x-show`, `x-model`, `:class`, `x-transition`, and
ordinary `class`, remains a Python render-time component kwarg. Citry does not
provide general root-attribute fallthrough.

The recommended arbitrary-attribute API is a child-declared mapping:

```html
<c-card c-attrs="{
  'x-show': 'visible',
  ':class': '{ selected: selected }',
}" />
```

```html
<article c-bind="attrs"><c-slot /></article>
```

The child decides whether the mapping belongs on one root, every root, or a
nested element.

### 4.5 Handlers authored on a child component tag

Both Alpine and Citry bindings authored on a child component tag belong to the
parent source, but their values have different contracts:

```html
<div x-data="{ selected: false }">
  <c-action-button
    @click="selected = true"
    @c-save="saveSelection({ selected })"
  />
</div>
```

The component tag disappears. Citry binds the logical listeners to the
child's physical `RootGroup`, the one-listener adapter over all current element
roots. The whole `@click` value is an Alpine expression evaluated at the exact
authored source location. For `@c-save`, `saveSelection` names a declared
server handler on the source parent; only the optional `{ selected }` argument
expression is evaluated there, and its object result is sent to that handler.

The following evaluation split applies to the Alpine handler expression and
to a Citry binding's optional argument expression. It does not apply to the
Citry server-handler name:

| Value | Owner |
|---|---|
| Ordinary variables, `$data`, `$root`, `$id`, `$refs`, and other lexical magics | Exact parent source location |
| `$el` | Physical child carrier |
| `$dispatch` | Physical child carrier and child-bound dispatch |
| `$event` | Exact delivered event at the child carrier |
| Native `event.target` and `event.currentTarget` | Browser event semantics, untouched |

There is no fallback from a missing parent name into child `x-data`.
`currentTarget` can be a child root, `window`, `document`, or `null` after an
async delay because Citry does not synthesize it.

A handler authored inside the child's template is child-local. If the parent
wants to grant the child a callback, it passes that callback through a declared
prop and the child deliberately exposes or invokes it:

```html
<c-action-button $c-props="{ givenCallback: () => selected = true }" />
```

```js
$component({
  props: { givenCallback: { type: Function, required: true } },
  init: ({ props, scope }) => {
    scope.givenCallback = props.givenCallback;
  },
});
```

```html
<button @click="givenCallback">Run</button>
```

For `@c-*`, the exact source parent Events anchor owns server-handler
validation, dispatch, and queueing. The child is still the physical trigger
and carries its busy marker. A relocated `@c-submit` preserves ordinary Events
form semantics: named controls are collected from the physical child form and
the source-authored explicit argument object wins on key collisions. `:c-*`
remains invalid on a component tag.

### 4.6 Slot and fill ownership

Template-authored supplied fill content uses the exact scope at the fill's
actual call site. Fallback content uses the receiving child's scope. Nested
fills can therefore cross from parent-owned supply into child-owned fallback
and back again.

```html
<div x-data="{ saves: 3 }">
  <c-card>
    <c-fill name="footer">
      <span x-text="`saved ${saves} times`"></span>
    </c-fill>
  </c-card>
</div>
```

The `x-text` expression sees the data at the call site even though the span is
physically rendered inside `Card`. Python `{{ ... }}` interpolation remains a
server expression and never contains Alpine `$` magics.

This rule follows structural ownership, not nearest DOM ancestry and not where
a reusable Python `Slot` object happened to be constructed. Template fills
record both the correct Python rendering owner and the exact component-call
invocation used as their client source carrier. Python-provided `Slot`
objects, callables, trusted HTML, and typed defaults have an explicit detached
Python origin with no invented lexical client source. In an already-active
client graph they receive an empty isolated base, so fill-local `x-data` works
without seeing receiver data. Detached content alone does not activate the
client graph or Alpine runtime. A public detached-source opt-in is outside A7.
Template fills activate this machinery when their settled region output
contains an Alpine directive or another client feature already requires the
graph. Plain server-only slot HTML does not load Alpine solely because it
crossed a component boundary.

### 4.7 Client ambient context

**Status: implemented on 2026-07-24.** Citry exposes three Alpine
magics and the same three methods inside the `$component` context:

```html
<section x-init="$provide('theme', theme)">
  <span x-text="$inject('theme').name"></span>

  <div x-init="$unprovide('theme')">
    <!-- A nearer descendant provider may restore the key. -->
  </div>
</section>
```

```js
$component(({ reactive, provide, inject, unprovide }) => {
  const parent = inject("parent-service", null);
  const service = reactive({ parent, active: true });

  provide("local-service", service);
  unprovide("parent-service");
});
```

The API accepts a non-empty string or symbol key. `provide(key, value)` stores
the exact JavaScript value. `inject(key, defaultValue?)` returns the nearest
ancestor value, returns an explicitly supplied default when missing, or
throws when no default was supplied. A provided `undefined` is present, and
an explicit `undefined` default is valid. `unprovide(key)` blocks the inherited
key for descendants until a nearer provide restores it.

Provides and blocks are outgoing only. An inject on the same element or in
the same component hook does not see that owner's own writes. This matches the
server `Component.provide()`/`inject()`/`unprovide()` contract and removes
directive-order dependence on one element.

`provide` and `unprovide` are synchronous initialization operations. Component
authors call them from `$component` initialization; template authors normally
call the magics from `x-init`. Dynamic client state is expressed by providing
one stable Alpine-reactive object. Citry stores and returns values as-is.
Runtime installation, replacement, or cleanup of a provider declaration
invalidates live Alpine expressions that use `$inject`, so morphs and
directive removal re-resolve their nearest value. A value already captured by
component setup remains the value that call returned.

The hook methods own the whole logical component, including multi-root and
rootless output. On a single root, a hook provide has the same descendant
effect as `$provide` on that root. On several roots, the hook has the coverage
of placing the magic on every root while running only once per logical
callback invocation. A magic may instead establish a narrower element
subtree. Under the mirror policy, hook context is logical and shared; an
element magic is placement-local like ordinary Alpine directive state.

A shared hook frame has one occurrence per physical placement, each with its
own outer rendered route. Hook `inject()` compares the result at every
occurrence. It returns only when all outcomes agree under `Object.is`, or when
all are missing and the same default/error rule applies. A found `undefined`
does not equal missing. Conflicting outcomes throw instead of selecting the
first placement. Descendant lookup remains placement-specific.

Ambient lookup follows a dedicated **rendered context route**. It does not use
the component's isolated Alpine data stack, `Component.parent`, lexical fill
source, or `parentElement` alone. This adds a fifth graph concern beside
lexical source, logical owner, physical region, and stable lifecycle:

```text
rendered call site
        |
        v
component ambient frame       hook provide/unprovide
        |
        v
template element frame        magic provide/unprovide
        |
        v
child component or slot site
```

Each frame holds values or private blocked markers and has one occurrence per
live placement. Citry derives each occurrence's outer route from the existing
component, fill, and physical-range records, ordinary HTML ancestry, and
Alpine's teleport-origin backlink. No additional manifest relation is needed,
and JavaScript values never enter the server manifest.

Slots make the separate route necessary. A supplied fill keeps the caller's
lexical Alpine source for normal expressions, while ambient lookup follows
the receiver's rendered slot site. The slot-site route is laid over the
caller-side ambient route, so a nearer receiver provider wins. Fallback uses
the receiver route directly. A `$provide` inside a fill evaluates its value
in caller scope, then provides it to descendants where that fill is rendered.

Teleport preserves the ambient route at the authored origin. Rootless
components use hook frames without an element. Magic-frame contributions
belong to the synchronous Alpine directive invocation that registered them;
hook frames use callback-invocation cleanup. Incoming routes and hook
registrations participate in the existing atomic graph and DOM adoption
transaction. A
preserved element keeps an unchanged directive registration, but a changed or
removed declaring directive cleans its complete registration set before
descendants resume. Captured helpers become invalid when their owner
invocation retires.

The exact directive owner comes from a narrow build-time instrumentation of
pinned Alpine's `getDirectiveHandler`, covering built-ins and plugin
directives without expression-text or directive-order inference. It registers
cleanup through that directive's own `utilities.cleanup`, including virtual
directives created by object-form `x-bind` and programmatic `Alpine.bind()`.
A stored
`$inject` helper remains bound to the element where the magic was read,
including across `await`, matching Alpine's usual magic capture behavior.
During morph cloning, detached reads temporarily route through the live source
element; detached provider writes are rejected and the live directive performs
the registration.

An ancestor magic registration settles before a descendant hook, and an
ancestor hook settles before a descendant magic lookup. The guarantee applies
to documents, fragments, object-form `x-bind`, structural copies, teleport
origins, and compatible reused nodes. Moving a live element or complete
component range invalidates dependent lookups so they resolve against the new
HTML ancestors. The three magic names are reserved on Citry's Alpine instance;
plugin collisions fail before startup without a partial overwrite.

The archived `alpine-provide-inject` plugin provides useful names and
ancestor-only behavior, but its `_provides` element property and
`parentElement` walk are not suitable for Citry's graph. The full review,
exact signatures, error contract, Tabs boundary example, rejected
alternatives, and test matrix are normative in
[`component_provide.md`](component_provide.md#10-client-provide-inject-and-unprovide-design).

## 5. The graph model

### 5.1 Node identities

The runtime keeps these identities separate:

| Identity | Meaning | Lifetime |
|---|---|---|
| Component class ID | Component definition | Class registration |
| Render component ID | Faithful ID stamped by one server render | One render revision |
| Logical instance | One client component lifecycle | Until replacement or removal |
| Source location ID | Exact lexical evaluation location | One graph revision, remapped on compatible morph |
| Fill ID | One logical supplied or fallback fill | Its owning instance/revision |
| Physical region ID | One element group or comment-capped range | One rendered placement |
| Stable browser anchor | Client continuity and queue/State owner | Across compatible render revisions |

No one ID is overloaded to do all jobs. In particular, rewriting a fresh
`data-cid-*` attribute in an Alpine `x-for` clone cannot mint a valid component
instance because it does not create the rest of the graph or server contract.

### 5.2 Required edge types

The graph needs typed relationships rather than inferred DOM proximity:

- component instance to component class;
- logical parent to child invocation;
- component or fill to exact lexical source location;
- supplied template fill to its exact source component-call invocation;
- component or fill to one or more physical regions;
- supplied fill to caller source;
- fallback fill to receiver source;
- render component ID to stable browser anchor;
- Events anchor to the general client instance when Events is present;
- mirror placements to the shared logical owner and copy-local physical
  directive owners selected by the hybrid mirror policy;
- teleport origin to teleported physical region;
- init dependency from logical ancestor to descendant;
- each component invocation, slot outlet, and lazily registered directive
  ambient-frame occurrence to its next outer rendered context position.

The graph can be represented as normalized records rather than object
references. Its wire form is versioned, deterministic, and validated as one
unit before adoption.

### 5.3 Evaluation inputs and ambient lookup

Every adapted expression names four independent inputs:

1. **Lexical source:** which scope, data stack, refs, IDs, and Citry magics are
   visible.
2. **Physical carrier:** which element or logical region supplies `$el`, event
   dispatch, directive cleanup, and native DOM behavior.
3. **Logical owner:** which component owns lifecycle, managed effects, props,
   State, queueing, and diagnostics.
4. **Current graph revision:** which mappings are live during a morph or
   dynamic target replacement.

Most ordinary Alpine expressions use the same DOM element for all four. Citry
must keep the inputs explicit precisely where that assumption is false.

The ambient-context API adds one operation-specific input:

5. **Rendered context route or route set:** which ordered provider and blocker
   frames an `$inject` lookup visits. A shared hook resolves every live
   occurrence route and applies the section 4.7 consensus rule.

That route does not replace the four expression inputs. In particular, a
supplied fill evaluates the key and default expressions through its lexical
source while resolving the key through its rendered slot route.

### 5.4 Server capture and serialization

Citry captures ownership before rendering flattens components and slots into
HTML. The capture points include component invocation, body-slot creation,
fill collection, slot invocation, and final region emission. The server emits
a compact versioned manifest that can reconstruct the typed edges and physical
caps without parsing component meaning back out of the final DOM.

Manifest adoption is atomic:

1. parse and validate the complete graph revision;
2. resolve or stage the referenced physical regions;
3. prepare new source links, scopes, and instance records;
4. switch the active revision;
5. initialize newly ready instances in dependency order;
6. retire old regions and cleanups exactly once.

A malformed revision does not partially relink the page.

The capture half is implemented by A1 as an in-memory `OwnershipGraph` with
fresh per-execution source locations, typed immutable snapshots, explicit
graph-local ID provenance, and active/retired output lifecycle. A2 now emits
the deterministic `citry-client-graph/1` wire manifest and exact comment caps,
then validates and commits each concrete revision atomically before dependent
Events or component callbacks run. Its locked contract is
[`alpinejs/a2_client_graph.md`](alpinejs/a2_client_graph.md). The wire record
now includes a nullable `sourceInvocation`: it is required for supplied
template fills, forbidden for fallback and detached fills, and must refer to a
component-call location owned by the fill owner. Fallback fills instead carry
a slot-outlet fallback location. Location kinds and region slot locations are
validated rather than treated as interchangeable numeric IDs.
A3 now normalizes every committed revision into read-only typed indexes and
separate render-record, logical-instance, and stable-browser-anchor identities.
It also provides the explicit correspondence transaction A8 now calls: a
same-class mapping can preserve both client identities, a class replacement
preserves only the positional anchor, and plain output retires both. A3 does
not infer correspondence by itself.

A4 now attaches a stable reactive scope and live root array to each active
logical identity, projects isolated Alpine stacks, schedules callbacks through
the init ancestry DAG, and owns effects, extension resources, returned
cleanup, and rootless cap lifetime. A5 adds reactive props supply and exact
source-owned component-boundary handlers. A6 adds dynamic RootGroups,
comment-bounded range validation, contextual range morphing, nested-island
protection, fill-region groups, and stable shared-root evaluator routing. The
replacement hook preserves stable lifecycle objects only for an explicit
same-class correspondence. A7 adds exact supplied and fallback source
projection, receiver-specific forwarded-fill attachments, detached isolation,
structural-template propagation, teleport composition, and source-owned
Citry-magic routing. A8 has now integrated those layers: it validates the
incoming graph, Events, and dependency package before DOM mutation, publishes
only an internal provisional graph during morph, applies explicit
correspondence, commits the landed physical caps, and then initializes
dependencies and retires displaced ownership. A detached-package validation
failure leaves the epoch, DOM, public registries, and prior ownership
unchanged. An unexpected failure after DOM mutation fails closed: the target
DOM and incoming ownership are removed, the incoming revision is rejected,
waiters fail, and the adoption hold is released. A8 does not promise to
restore arbitrary pre-morph DOM after such a runtime failure.

## 6. Alpine adapter

### 6.1 Version and boot ownership

Citry embeds exact Alpine 3.15.12 and `@alpinejs/morph` 3.15.12 today. The
runtime follows the Livewire ownership pattern:

- one bundled Alpine instance serves the page;
- another detected instance produces a clear warning;
- plugins, magics, root selectors, init interception, manifest observers, and
  Citry hooks register before startup;
- only `Alpine.start()` waits for DOM readiness;
- the embedded Alpine instance is exported as `globalThis.Alpine` for page
  integration;
- component and fragment loading cannot start Alpine a second time.

A3 consolidates Alpine extension registration behind the permanent
`Citry.alpine` broker. Hooks that cannot unregister are installed once and
dispatch through replaceable providers. The core manager owns mutation
fan-out; the current pinned bundle contributes Alpine, morph, Events
providers, and the guarded startup. It loads for every client-active graph,
including graphs with no Events instances. `beforeStart(callback)` is the
public extension point for plugins, custom magics, directives, and data
providers; late registration fails pointedly. Duplicate Citry bundles and a
foreign Alpine preserve the first Citry-owned instance and cannot stack
interceptors, selectors, observers, magics, or startup calls.

### 6.2 Private APIs

Private Alpine access is an engineering cost, not an automatic rejection. The
current runtime already uses `Alpine.addScopeToNode`, `_x_dataStack`, and the
morph bridge's `Alpine.cloneNode`. The target may continue using private APIs
when public hooks cannot preserve the required semantics.

Every private dependency must have:

- an exact Alpine and plugin pin;
- one typed adapter boundary;
- a header comment explaining the invariant;
- a canary that fails on upstream shape change;
- focused behavior tests, not only symbol-existence tests;
- an explicit bump checklist and three-browser run.

### 6.3 Component isolation and user `x-data`

Each client-active logical instance owns a stable reactive `scope`. Citry
attaches the appropriate scope stack to every physical root while cutting
ambient component inheritance. An `x-data` authored by the user remains an
ordinary Alpine layer local to its subtree. Citry does not merge component
scope into the user's object and does not mutate user data.

The logical component scope applies to every root, even though Alpine needs a
physical root on which to attach directives. Variables written to `scope` are
visible from Alpine expressions under any of the instance's roots. Nested
Citry component boundaries cut that visibility unless a source link or other
explicit channel crosses it.

Citry's boundary directive runs after an ancestor's queued Alpine directives
but before `x-data` and ordinary directives on the component root. This gives
source-owned suppliers a parent stack that is fully initialized, then projects
the child scope. If Component.js or another init dependency is still pending,
the same phase suppresses the remaining child subtree and a later `initTree`
pass initializes it after that branch settles.

### 6.4 Managed helpers

`effect()` and `reactive()` always use Citry's embedded Alpine instance.
Effects registered during init are owned by the logical instance and released
exactly once on replacement or removal. Users do not call `Alpine.release`
for these helpers.

### 6.5 Fill source projection

A7 turns each fill edge included in the graph into a live Alpine source frame. A supplied
fill takes its carrier from the exact target range of its recorded component
invocation, including transparent dynamic `<c-component>` selection. A
fallback fill follows the inverse ownership transition to the receiver. Citry
does not choose either source by nearest DOM ancestor, component class, or
physical outlet order.

The internal fill-source directive runs before `x-ref`, `x-data`, and ordinary
directives. Its source frame therefore sees source `x-data` that Alpine has
already initialized, while fill-local `x-data` remains a higher local layer.
On a slot-only shared root, Citry removes the receiver scope router from the
fill expression stack, so a missing source name cannot leak through to child
scope. A nested Citry component establishes its own isolated scope as usual.

Direct `x-if` and `x-for` templates copy the source marker to their generated
root. A direct `x-teleport` template also stamps the generated root so
retirement can unlink both the origin and teleported placement. Teleport
composes the Citry source backlink with Alpine's existing teleport ancestry.
`$refs`, `$id`, and source-owned `$root` follow that lexical path; `$el`,
`$event`, target, and currentTarget remain physical. A root with its own
fill-local `x-data` remains its ordinary Alpine `$root`.

Every mirrored outlet uses the same recorded source frame. Moving or removing
one copy updates physical membership without electing another source. A
same-revision fill-region morph is restamped and reprojected. Removing the
last live region or the recorded source retires the projection and it cannot
resurrect from a nearby node. Retirement removes the source directive, scope
frame, route indexes, ref/ID caches, and teleport backlinks. If Alpine leaves
a teleported placement physically connected after its source becomes invalid,
Citry gives that retired DOM an empty tombstone scope instead of exposing its
receiver or placement scopes. Internal source-route tokens include the graph
revision, so independently inserted fragment graphs cannot collide with the
document or one another. Cross-revision source replacement is part of the A8
atomic correspondence transaction.

## 7. Root shapes and lifecycle

### 7.1 Single element root

The element is the physical region and participates in the stable `els`
array. Component scope and directives attach to it before Alpine initializes
the subtree.

### 7.2 Several element roots

One logical `RootGroup` owns all roots. Props are supplied once, but their
reactive bag and component scope affect every root. `els` contains every live
root in document order.

Relocated handlers are one logical listener over the group, not independent
copies. The group provides:

- union containment for `.outside` and `.away`;
- shared `.once`, debounce, and throttle state;
- one `window` or `document` delivery;
- dynamic root membership through compatible morphs;
- native event objects without synthetic redispatch;
- one cleanup and one poll cadence;
- open-shadow containment where the platform exposes the composed path.

This is aggregation across a set of DOM nodes. It does not pretend that the
set is one geometric element, so pointer capture and enter/leave behavior
follow explicit tested policies rather than invented browser state.

Mouse and pointer enter/leave ignore a native event whose `relatedTarget` is
inside any other live root in the same group. This union filter runs for both
relocated Alpine and Citry handlers before shared `.once`, debounce, or
throttle state is consumed. A transition from the group to a real outside
target still delivers from the physical root that received the native event.
Pointer capture remains owned by the actual element that called
`setPointerCapture()`; Citry does not transfer capture to another root or
normalize engine-specific delivery after release.

After a `.once` binding consumes its first eligible event, Citry detaches the
native listener from every current root immediately. Roots that join the group
later do not receive that consumed binding.

A6 implements this contract in the general client registry. Membership is
derived from the outermost authored marked roots inside the instance's exact
physical caps. An unmarked serialization-extension wrapper can contain those
roots without replacing them in `els`; a cloned marker outside the caps cannot
join the group. Membership updates in place after DOM mutations. Direct
delivery uses the element that received the native event. Global, outside,
and polling delivery uses the first connected live root in document order and
reelects after membership changes. Pending work tied to a removed direct
carrier is dropped, and final range retirement cancels all group work.

### 7.3 Text-only or empty output

An instance may initialize and resolve props without an HTML element. The
proved baseline owns comment caps around the logical range and stores scope,
props, effects, polling, State, and cleanup on the logical instance. `els` is
empty until an element appears.

Range updates use context-sensitive parsing, including table, select, SVG, and
the validated top-level Document-to-body context. Nested and adjacent ranges
remain isolated. Cross-parent nested islands temporarily move only their
Citry-owned comments and body interval into an inert holder, then restore the
same comment identities before lifecycle reconciliation resumes. Fresh server
render IDs are correlated according to the O9 policy before adoption. The
proved baseline
uses Citry-owned comments as load-bearing caps and fails pointedly if a host
strips or changes them. A2 settled O11: `citry:g1` is the literal required
comment prefix, the exact protocol is locked, and production minification,
sanitization, and deployment must preserve the caps. The protocol has no fixed
manifest byte ceiling; CI keeps scenario payload budgets. A6 validates exact marker
text, ordering, parent topology, and recorded nesting throughout the lifetime.
A same-task complete-range move remains live after the mutation checkpoint;
an invalid split, reversal, partial removal, or later detach retires once and
cannot resurrect. Each range keeps the topology mode validated at adoption;
the narrow Document-to-body parser exception cannot be entered later by
moving one cap. Roots for that exception are still filtered to the exact
start/end interval, never admitted by an unbounded document marker query.

Props, init, managed effects, scope, polling, State, and cleanup do not need a
physical element. A component-tag Alpine handler or DOM-event `@c-*` binding
does need a native EventTarget on the child. If the child has no element root,
Citry reports a pointed handler-placement error instead of adding a wrapper or
synthesizing a native event target. The client binding remains dormant, so the same
logical lifecycle can activate it if a later range update supplies an element
root, and detach it again if roots disappear. `@c-poll` is a logical timer
binding and can follow the rootless lifecycle without an EventTarget.

### 7.4 Mirrored placements

One server-authored logical fill can appear at several physical slot outlets.
A6 groups those uniquely capped regions under one stable live `els` array and
locks the hybrid mirror model:

- component props, Citry `scope`, Events State, component init, managed
  effects, returned cleanup, and component-boundary RootGroup state are
  shared by the logical owner;
- ordinary Alpine `x-data`, child-local listeners, refs, IDs, transitions,
  focus, and Alpine directive cleanup belong to each physical copy;
- a direct native event uses its actual triggering copy; window, document,
  outside, away, and poll use the first connected live carrier in document
  order;
- removing one copy performs that copy's physical Alpine cleanup while the
  logical lifecycle stays active; removing the final copy performs the one
  logical cleanup and cancels shared work.

The exact lexical source is graph-owned. Removing or reordering a physical
copy never elects a new source merely because it becomes first. A7 projects
the recorded fill source and retires it with the last copy or source carrier.
A8 carries that source across graph revisions through explicit incoming
correspondence. When morph preserves a fill element, its stable Alpine source
frame is retargeted to the incoming descriptor and reactively refreshes
existing evaluators without resetting same-root local `x-data`.

The copy-local refs/IDs rule describes each copied Alpine directive's storage
and cleanup. Expressions in the copy still resolve the graph-selected source
registry. Citry does not convert duplicate Alpine refs into arrays or add a
fallback across component boundaries. Within one native Alpine root, repeated
same-name `x-ref` follows pinned Alpine behavior: the last initialized ref is
visible, and removing another clone may clear that shared name while a peer
remains. An `x-id` registry declared on each structural or mirrored root stays
copy-local; a copy that uses only the graph-selected source `x-id` resolves
that source registry. These rules are explicit native behavior, not a Citry
ordering guarantee.

`liveSlotRegions` and the stable combined `els` array follow current physical
document order after a complete range move. This reorders carrier preference
without resetting logical modifier or timer state.

A single Events `Render` action whose selector matches several elements has
the settled rule in [`events.md`](events.md): it inserts one shared Events
instance, State, and token at every match. A8 normalizes this into the same
logical/shared and physical/copy-local model without changing that public
rule. The first copy preserves the canonical `citry:g1` caps from the unchanged
`citry-client-graph/1` wire package. Additional copies receive client-owned
`citry:p1` caps with a runtime placement ID. Every placement routes to one
logical component, State object, props view, lifecycle, and fill source, while
ordinary Alpine state and cleanup remain copy-local. Placement identity is
not inferred from fresh render IDs or DOM position.

### 7.5 Shared physical roots

More than one logical identity can reference the same physical element, for
example at a component boundary with source-linked handlers. The graph keeps
their scope and lifecycle records separate. A6 selects the innermost active
owner from the ordered graph markers and keeps one stable reactive router on
the element. When dynamic membership changes the owner, existing Alpine
directive evaluators see the router's new target without directive teardown
and without resetting same-root user `x-data`. No ownership is inferred from
which record happened to attach last.

## 8. Structural Alpine directives

### 8.1 `x-if` and `x-for`

Stock Alpine remains responsible for `x-if` and `x-for`. Citry propagates
source-location metadata through the structural template and its clones so
expressions inside supplied fills keep their lexical owner.

Direct `x-for` cloning of a server-rendered Citry component is not solved by
changing a marker. A valid clone needs a fresh logical identity, source links,
regions, lifecycle record, and possibly a server-addressable contract. The
named client-target or browser blueprint protocol remains a separate design
item. Citry rejects a client-active server component beneath native `x-for`,
`x-if`, or `x-teleport` before graph activation and descendant initialization.
Use server `<c-for>` for server component lists, or place an ordinary Alpine
loop inside an already valid component scope. The complete deferred protocol
inventory is in
[`a9_client_instantiation.md`](alpinejs/a9_client_instantiation.md).

For valid supplied fills, removing one structural clone retires that clone's
source route even while sibling clones and the shared source descriptor stay
live. Keyed reorder preserves the clone, iteration layer, model, local IDs, and
source frame. Recreation mints ordinary fresh Alpine physical state.

### 8.2 `x-teleport`

Teleport has two simultaneous truths:

- lexical Alpine and Citry ownership follows the teleport origin;
- native DOM target, currentTarget, focus, bubbling, and containment follow
  the teleported placement.

Citry composes Alpine's teleport ancestry with its source-location graph. It
does not redispatch events or globally restamp the teleported subtree. Stock
Alpine's own template-listener forwarding remains Alpine behavior; Citry adds
no second delivery path.

### 8.3 Refs and IDs

Boundary-relocated handlers resolve `$refs` and `$id` at the exact source
location, not from the child target. Child-local expressions use child refs
and IDs. Ref and ID collision never causes fallback across the component
boundary.

### 8.4 Transitions and models

Ordinary `x-transition`, `x-model`, `x-show`, and bindings inside a component
remain Alpine behavior. Passing their attribute strings into a child is
ordinary Python kwarg handling as described in 4.4. In a mirror, ordinary
Alpine directive and transition state is physical-copy-local. Rootless output
has no element on which an Alpine transition can run.

Pinned Alpine morph intentionally skips attribute patching while an element
is transitioning or when old and incoming shown state differs. After an A8
correspondence, Citry therefore reconciles only its graph-owned `data-cid`
and `data-cid-*` markers inside the adopted exact caps. It does not overwrite
Alpine's style, shown state, transition state, model, ref, or user attributes.
The stable component `scope`, `els`, model value, refs, and transition cleanup
continue through a compatible morph.

## 9. Morph, identity, and transactions

### 9.1 Render identity and client continuity

The server emits a fresh component ID for each render. The landed Events path
maps that revision ID to a stable Events anchor, which owns reactive State,
pending writes, queue epochs, and call correlation across its accepted render
updates. The graph-first runtime uses an explicit continuity identity
for scope, props, RootGroups, effects, and cleanup, rather than treating a
fresh server ID as proof of a wholly new browser object.

O9 is settled as follows:

- A same-class self-render preserves the stable browser anchor and logical
  instance. Its State, queue identity, scope, `els`, props view, and lifecycle
  continue while the fresh render ID becomes the active route.
- A self-render whose component class changes preserves only the stable
  browser anchor. The old logical instance cleans up once and the incoming
  class receives a fresh logical instance.
- Plain HTML replacing the self target retires both the browser anchor and the
  logical instance.
- A same-class keyed child match preserves its browser anchor and logical
  instance, including when that child has no Events sidecar. Component identity
  is `(component class, morphKey)` on the comment-bounded virtual range, not a
  key copied onto a root element.
- After keyed matches are reserved, remaining old and incoming unkeyed direct
  children pair by position; only same-class pairs preserve identity. There is
  no scan-ahead, so reordering unkeyed siblings does not move their identity.
- Uncorrelated incoming IDs receive fresh identities. Class or key mismatches
  replace the range, and an unmatched component is opaque to descendant keys.

The old render records become inactive at correspondence or retirement and
are no longer routable. Their physical caps and logical lifecycles retire even
when immutable diagnostic records remain in a still-live revision snapshot.
Once a revision has no active links, pending graph callbacks, live fills,
client bindings, or Events adoption, the client prunes its public and internal records.
A separate used-revision tombstone still rejects replay of that revision.

### 9.2 Atomic morph transaction

Graph and DOM changes use one coordinated transaction:

1. parse and validate the incoming graph, Events, and dependency manifests;
2. build provisional physical and logical correspondence candidates without
   mutating the live document or running dependency code;
3. seed retention from old-side ordinary `#c-ignore` barriers and ignored
   ComponentRanges, then close transitively over shared component, fill,
   slot-region, and mirror records;
4. remove retained old and excluded incoming branches, discard provisional
   matches, and compute final correspondence from scratch: reserve keyed
   same-class children, then positionally pair remaining unkeyed children;
5. stage only accepted source links, props suppliers, RootGroups, descriptors,
   dependencies, and logical ranges;
6. expose private mappings needed while Alpine morph evaluates accepted
   incoming expressions and morph the physical DOM;
7. validate and adopt the landed canonical and runtime-placement caps;
8. commit the new graph revision and initialize ready instances;
9. reconcile bindings and busy state, then retire old records, timers,
   subscriptions, effects, and unused descriptor revisions exactly once.

The old mapping remains available only for the portion of morph evaluation
that needs it. Provisional routes are private and public readiness waiters are
rejected if adoption aborts. Public physical-placement arrays are frozen
snapshots rather than mutable views of internal state.

Failure handling has two precise levels:

- Malformed graph, Events, or dependency data is rejected during detached
  preflight, before epoch, DOM, anchor, callback, or public-registry mutation.
- An unexpected activation, morph, or landed-cap failure after mutation fails
  closed. Citry aborts provisional routes, fills, client bindings, and links, removes
  transferred incoming caps and the live target DOM, rejects the revision and
  its waiters, restores the previous Events class registry, releases the
  adoption hold, and runs retired cleanup once. It does not claim general DOM
  rollback after Alpine has begun morphing.

A6 supplies the contextual range-operation half used by this transaction. A8
adds a complete, read-only correspondence plan before DOM mutation. Explicitly
addressed roots correlate first. Within each matched parent, provisional
physical candidates exist only to discover old-side ignore closure; after
that closure is removed, the planner recomputes direct-child correspondence
from scratch. It first reserves unique non-null keys by component class, then
zips all remaining unkeyed positions and accepts only same-class pairs. An
unmatched component is opaque, so a descendant key cannot leak through it.

An old ordinary ignored element is an opaque physical barrier: the element
itself may still participate in its surrounding Alpine sibling match, but its
attributes and descendants remain old. An old ignored ComponentRange retains
every placement and every graph-owned resource in its closure. Incoming
callbacks, fills, dependencies, inline scripts, styles, and manifest hooks
from excluded branches never become observable. `swap="replace"` bypasses
range ignore because it deliberately does not perform a morph transaction.

The physical adapter makes every component range atomic to its parent's
ordinary element walk and recursively applies fresh server HTML inside matched
ranges. A stationary range stays connected between temporary paired sentinels.
Citry filters the range's ordinary roots out of Alpine's flat keyed-sibling map
before matching, then makes the enclosing walk skip directly to the closing
sentinel. The live caps and contents are never reparented, preserving focus,
selection, scroll containers, iframe documents, and other browser-owned
resources. Nested stationary component and equivalent slot-region ranges are
processed inside-out; an unmatched intermediate virtual range vetoes this
connected path. A real move uses a temporary portable holder and can cross
ordinary wrappers or depths. Unmatched ranges are replaced atomically. All temporary
nodes disappear synchronously before lifecycle reconciliation resumes. The
scan covers every live ownership revision, including independently inserted
fragment graphs and runtime mirror placements.

`swap="morph"` keeps matched physical caps and nodes where the recursive morph
permits it. `swap="replace"` applies the same logical correspondence plan but
wholesale replaces physical DOM and caps. A8 owns validation, commit, preflight
rejection, and invocation of this adapter as one graph plus Events transaction.
Events and dependency descriptors are revision-scoped: retained old anchors
continue routing through their old immutable descriptor revision, accepted
incoming anchors use the new revision, and installation rollback restores the
prior snapshot. A revision is pruned only after no live anchor or pending call
still references it. A malformed graph, Events manifest, or dependency package
is rejected before epoch, DOM, public graph, callback, or anchor mutation.

### 9.3 Key preservation

A component `#c-key` is authored on the parent invocation and stored on the
stable logical component range. It never lives on the child's root DOM. A
same-class child self-render has no parent invocation in its incoming graph, so
Citry retains both the parent-authored `morphKey` and the external logical
parent relation while transferring the fresh render ID. The next parent render
can therefore rediscover the child without copying or reconstructing a DOM
attribute. A class change creates a fresh logical instance and cannot inherit
the old component key. An element `#c-key` on the child's root is an independent
ordinary morph key.

## 10. Events and queue integration

Citry magics resolve through the logical owner selected by the graph, not only
through `closest()` DOM ancestry. Inside ordinary child content, they resolve
to the child Events anchor. Inside a parent-owned supplied fill, they resolve
according to the fill's source owner. Inside a relocated parent `@c-*`
binding, server-handler dispatch and queue ownership are explicitly the source
parent's anchor, and its optional argument expression uses the parent source
scope, while the child remains the physical trigger.

Queue containment is computed from logical component ownership, then checked
against live physical regions where liveness matters. Source-linked content
must not silently dispatch through the nearest physical child's queue.
This graph-ancestry containment and dequeue-time physical liveness check are
landed in A8.

Compiled `@c-*` bindings and `$sendEvent` are source-owned because both are
declarative Citry expressions. The public
`Citry.events.send(element, event, args)` method deliberately remains
physical-element-owned: its explicit element selects the nearest physical
Citry component rather than the element's projected fill source. If that call
waits in the queue, dequeue re-resolution also uses physical markers and
cannot transfer it to the projected lexical source.
Source-owned queue nodes lock that anchor when they are created and carry a
live-source predicate. If the source retires while a call waits behind an
earlier event, the call is cancelled; it never re-resolves through the
physical child. The predicate is also checked before immediate dispatch, so a
captured `$sendEvent` closure cannot outlive its fill source. Busy marking and
containment still use the physical trigger.

Graph revision, Events manifest, dependency manifest, and DOM patch adoption
must be ordered so no callback observes a render ID before its owner or State
mapping exists.

## 11. Loading, plugins, CSP, and future source formats

Deferred Alpine/Citry interoperability work from this section and the native
clone-instantiation boundary is tracked in the catch-all
[issue #37](https://github.com/citry-dev/citry/issues/37); TypeScript/compiler
work remains in #10 and ESM delivery in #35.

### 11.1 Plugins

Citry owns Alpine startup and offers a pre-start extension point for approved
plugins. A page should not include a second Alpine build. Compatibility with
ordinary Alpine plugins is a goal, but a plugin that assumes DOM ancestry is
the only scope authority may require an adapter or may be incompatible with
source-linked content.

### 11.2 CSP

The standard Alpine build evaluates expression strings and therefore requires
`unsafe-eval` on pages that use those expressions. This is an explicit current
tradeoff. A constrained future mode may combine Alpine's CSP build with a
restricted expression vocabulary, but it is not part of this target.

### 11.3 ESM and compiled languages

The Alpine graph and manifest are runtime-neutral. They do not assume that a
component's JavaScript source is wrapped in a function or emitted as a classic
script. Current component scripts and the Events bundle remain classic IIFEs.
ESM, TypeScript output format, top-level imports, source maps, and registration
binding are parked in [`esm.md`](esm.md) and
[`asset_compiler.md`](asset_compiler.md). This design must not close those
paths.

`$component` source rewriting remains the current registration mechanism. A
future module design must replace or bind it without wrapping static imports
inside a function and without regex rewriting arbitrary user identifiers.

### 11.4 Startup and lazy activation

Alpine initialization is synchronous today. The production audit found pages
with hundreds of roots, so startup cost is a real scaling risk. The target
does not add lazy activation speculatively because delaying a directive tree
changes init order, refs, effects, transitions, and event readiness. A lazy or
chunked mode requires measured product evidence, explicit lifecycle controls,
and its own compatibility matrix.

## 12. Current implementation versus target

| Area | Current repository | Accepted target |
|---|---|---|
| Alpine bundle | Pinned Alpine and morph, classic IIFE, permanent `Citry.alpine` broker, one owned startup | Keep; split or rename the historical Events-named bundle only as packaging work |
| Events anchors | Optional sidecars bridged one-to-one onto general stable anchors | Keep State and queue data Events-owned while graph identity stays general |
| Isolation | Stable component `scope`, exact parent-source boundary evaluation, exact supplied/fallback fill source frames, atomic cross-revision frame retargeting, and structural-clone retirement; same-root user `x-data` remains the higher layer | Keep |
| `$component` | One registration per class; per-render callbacks carry stable lifecycle data plus reactive read-only props | Keep the A5 channels without changing class registration |
| Prop declarations | Stable defaults, validation, read-only view, diagnostic episodes, and update recovery are landed | Keep |
| Prop supply | Source-ordered `$c-props`, `c-$c-props`, and `c-bind` winners evaluate reactively at the parent source and survive compatible A8 correspondence | Keep |
| Component-tag handlers | Alpine expressions and Citry argument expressions run at the parent source with physical child event values; server dispatch stays source-owned; compatible caller rerenders replace old client binding resources exactly once | Keep |
| General registry | A3 through A9 provide identity, lifecycle, props, client bindings, exact physical ranges, RootGroups, fill projection, atomic graph plus DOM adoption, and structural hardening | Keep |
| Multi-root | Dynamic cap-bounded `els`, grouped native handlers, shared modifiers/timers, one poll cadence, deterministic carrier re-election, fill source projection, and compatible revision continuity are landed | Keep |
| Rootless | Required `citry:g1` caps own lifecycle, reactive props, init settlement, logical polling, contextual morphing, nested-island protection, dormant DOM-handler recovery, and atomic cap adoption | Preserve caps through deployment |
| Mirrors | Server-authored fills and client-owned `p1` placements expose one shared logical lifetime with copy-local Alpine physical state and explicit native ref/ID rules | Keep |
| Slot scope | Exact invocation-owned supply, inverse-transition fallback, detached empty base, shared-root isolation, native teleport composition, per-clone retirement, cleanup, and cross-revision frame retargeting are landed | Keep |
| Client ambient context | `$provide`, `$inject`, `$unprovide`, and the matching hook methods use component ranges, rendered slot positions, and teleport origins; hook injection checks every mirrored placement; exact directive cleanup covers literal, object-bound, and programmatic declarations | Keep the dual public surface and lifecycle rules specified in section 4.7 and `component_provide.md` section 10; keep the explicit remaining-case matrix there |
| Morph | Graph, Events, dependency, DOM, O9 correspondence, key preservation, client binding succession, transition-safe marker adoption, and retirement are one coordinated transaction | Keep |
| `x-if`, `x-for`, teleport | Stock Alpine behavior with graph source propagation, keyed continuity, exact clone cleanup, and native teleport movement; copied client-active server components fail pointedly | Keep stock Alpine; client component instantiation needs its separate protocol decision |
| `$c-props` spelling | Exact parser placement/value contract, typed client binding capture, and A5 client execution are landed; the winner stays out of component raw kwargs | Normative public spelling and Citry directive behavior |

Research adapters and harnesses in [`alpinejs/`](alpinejs/README.md) are
evidence, not production code.

## 13. Diagnostics and acceptance rules

Every diagnostic names:

- the component class and current instance when available;
- the authored directive or handler;
- the source location and target shape when relevant;
- what failed;
- why the runtime cannot continue that branch;
- the concrete author or deployment fix.

Minimum acceptance covers Chromium, Firefox, and WebKit and includes:

- nested isolated components with colliding data, refs, and IDs;
- single, multi, rootless, mirrored, shared-root, nested, and adjacent shapes;
- source-ordered direct, `c-*`, and `c-bind` client binding contributions;
- prop validation at init, update, removal, recovery, and cleanup;
- parent-scoped Alpine handler expressions and Citry argument expressions with
  physical event magics and source-parent server dispatch;
- `.once`, debounce, throttle, outside, away, window, document, polling,
  shadow DOM, pointer, and delayed delivery;
- supplied fill, fallback, nested ownership transitions, `x-if`, `x-for`, and
  teleport;
- client ambient context through hook and magic surfaces, including nearest
  replacement, block and restore, multi-root, rootless, fill rendered-route
  lookup, mirror locality, teleport origin, morph replacement, and cleanup;
- initial document, inserted fragment, same-class morph, keyed parent morph,
  class replacement, target replacement, and removal;
- Events State, queue containment, busy state, subscriptions, and stale
  response handling;
- malformed and partial manifests with atomic rejection;
- private Alpine canaries and duplicate-hook detection;
- performance and payload bounds against realistic component counts.

The executable mapping for those claims is the
[`A10 conformance matrix`](alpinejs/a10_conformance.md). Deterministic bundle,
graph, and document byte limits plus the browser measurement method are locked
in [`A10 performance and payload budgets`](alpinejs/a10_performance.md).

Observe-then-lock tests must be shown to fail when their mechanism is removed
before their expected output is committed.

## 14. Rejected architecture families

The following are not the selected direction:

- **Alpine-first DOM inference as the final model.** It cannot faithfully
  recover slot ownership, rootless lifetime, or exact source scope after
  server rendering has flattened the tree.
- **A Citry virtual DOM.** It duplicates Alpine and morph responsibility
  without evidence that graph metadata plus stock Alpine is insufficient.
- **A second Citry expression evaluator or directive language.** It would
  divide Alpine compatibility and require recreating models, transitions,
  refs, plugins, and expression behavior.
- **An Alpine fork now.** No proven blocker requires carrying a fork. Private
  adapter use is cheaper while canaries remain effective.
- **Wrapper custom elements.** They change emitted DOM and CSS/layout behavior
  to solve metadata ownership that comment ranges and graph records can carry.
- **Synthetic event redispatch.** It breaks native event identity,
  currentTarget, timing, default prevention, and plugin assumptions.
- **Global restamping or copied data stacks.** They leak scopes across nested
  boundaries and fail when structural directives create later clones.

A fork, replacement evaluator, or compiled binding runtime is reconsidered
only if the integrated graph-first product gate proves a concrete stock-Alpine
blocker that the adapter cannot safely isolate.

## 15. Research record

The saved evidence, reproduction commands, status notes, and historical
wording live in [`alpinejs/README.md`](alpinejs/README.md). The most direct
inputs are:

- [`exploration-alpine-component-first.md`](alpinejs/exploration-alpine-component-first.md);
- [`exploration-x-props-round-2.md`](alpinejs/exploration-x-props-round-2.md);
- [`exploration-slots-alpine-scope.md`](alpinejs/exploration-slots-alpine-scope.md);
- [`spike-citry-handler-refs.md`](alpinejs/spike-citry-handler-refs.md);
- [`spike-root-group.md`](alpinejs/spike-root-group.md);
- [`spike-rootless-lifecycle.md`](alpinejs/spike-rootless-lifecycle.md);
- [`spike-component-identity.md`](alpinejs/spike-component-identity.md);
- [`spike-keyed-morph.md`](alpinejs/spike-keyed-morph.md);
- [`spike-morph-alpine.md`](alpinejs/spike-morph-alpine.md);
- [`a9_client_instantiation.md`](alpinejs/a9_client_instantiation.md).

Those reports explain and reproduce the decisions. This document owns the
current decision when an older report records a superseded candidate.
