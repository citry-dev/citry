# Exploration: x-props round two (relocation and mechanics)

**Historical spelling note (2026-07-20):** this report tested `x-props` and
retains that name as evidence. The maintainer later selected graph-first
Alpine and `$c-props`, including `c-$c-props`. The normative contract is now
[`../alpinejs.md`](../alpinejs.md), and remaining work is in
[`../alpinejs_plan.md`](../alpinejs_plan.md).

**Citry binding scope correction (2026-07-21):** a Citry `@c-*` value names a
declared server handler and may contain one parenthesized Alpine expression for
its argument object. References below to evaluating a Citry handler mean that
optional argument expression, not the handler name or the whole attribute
value. The retained spike used an arbitrary expression as a scope stand-in; it
did not prove handler parsing, source Events validation, dispatch, or queueing.

This historical report calls `x-props`, an Alpine handler such as `@click`,
or a Citry handler such as `@c-save` or `@c-poll.5s` on a nested `<c-*>` tag
a **component-tag client binding**. The accepted props spelling is now
`$c-props`. In either spelling, the parent owns the expression or server
handler, while the child supplies the component boundary where the browser
applies it. Later references shorten this to “client binding.”

A maintainer-decision report for the second WP23 design round. The stage-one
report chose `x-props`; the maintainer's 2026-07-17 review then ratified that
historical spelling and amended the authoring surface: a
parent writes `x-props` and boundary event handlers on the **child component
tag**, and Citry relocates them. This report designs that relocation and the
remaining runtime mechanics. Analysis only; no runtime or parser code changed.

Maintainer review through 2026-07-19 accepted the relocation direction and
sections 4, 5, and 6. It also amended the component-tag client binding
surface: `x-props`, Alpine event handlers, and Citry `@c-*` event handlers are
the only ordinary-looking attributes with special component-boundary
behavior. Sections 8 and 9 are
also accepted; section 7 remains a recommendation pending maintainer review.
Root grouping, rootless
lifetimes, and browser-instantiated identities were explicit spikes rather
than silently assumed v1 behavior; the first two mechanisms and the focused
boundary-handler isolation mechanism passed on 2026-07-19 under the conditions
recorded below, while named browser identity remains open.

Run on 2026-07-18 against commit `53aec72` plus the uncommitted Events and
rename work in the working tree. Alpine and `@alpinejs/morph` are both pinned
at 3.15.12. File ranges below name the relevant symbol as well as the lines,
because the client wave remains under active edit.

Two terms recur:

- A **client binding** is the structured render record made from one of those
  component-tag attributes. It records the target instance, supplying
  instance, authored client source, and source position after the component
  tag itself has disappeared. The client source is a props or Alpine handler
  expression, or a compiled Citry handler name plus optional argument
  expression.
- The **instance registry** is the general component-id index proposed below.
  It sits below the Events anchor registry. Every client binding target has an instance
  record; only an Events-declaring instance also has an anchor and `$state`.

## Prior art (what was searched)

Normative Citry sources, read against the live tree:

- [`exploration-client-props-passing.md`](exploration-client-props-passing.md),
  the complete stage-one report; the 2026-07-17 maintainer amendments now
  synthesized in [`../alpinejs.md`](../alpinejs.md); `events.md` 5.3, 5.5,
  5.6, and 16.1; and `events_plan.md` WP17.1 and WP23.
- The component-tag path:
  `crates/citry_template_parser/src/parser.rs:815-917` (attribute parsing),
  `compiler.rs:930-1030` (`ComponentNode` emission), and
  `packages/py/citry/citry/nodes/__init__.py:719-866`
  (`ComponentNode.render` and `_resolve_kwargs`). The key precedent is
  `#c-key`: compiler metadata stays out of kwargs, evaluates in the parent
  render context, travels on `CitryElement.morph_key`, and lands on the child
  roots (`citry_element.py:53-95`, `component_render.py:596-620`).
- The root serializer:
  `packages/py/citry/citry/serialize.py:95-140,183-223`. It stamps every root,
  inherits a wrapper's markers through a child placeholder, and merges
  same-name valued markers. The locked cases are in
  `packages/py/citry/tests/test_markers.py`: single and multi roots at
  `:16-43`, and two or more logical instances sharing one root at `:76-128`.
- The dependency manager:
  `packages/py/citry/citry/ext/dependencies/client/citry.js:156-233`
  (registration, calls, and cleanup), `:311-390` (`flushCalls`), and the
  manifest path in `ext/dependencies/emission.py:107-182,227-284`. The current
  queue deliberately passes an unready call and continues with later ready
  calls (`flushCalls:323-329`).
- The Events runtime:
  `packages/js/citry-client/src/citry-events.ts:719-758`
  (`interceptInit`), `:1051-1077` (boundary attachment), `:1079-1128`
  (manifest processing), `:1130-1164` (innermost-id magic resolution),
  `:4490-4600` (the landed default-only prop resolver), and `:4602-4645`
  (the `$component` payload decorator). Events anchors are currently created
  only for classes declaring `Events`
  (`packages/py/citry/citry/ext/events/emission.py:130-189`), while a valid
  Component.js callback can exist without `Events`; that distinction rules
  out using the anchor map as the complete client binding registry.

Pinned Alpine 3.15.12 source, read directly under
`packages/js/citry-client/node_modules/alpinejs/src/`:

- `x-for.js:93-129`: a clone receives one reactive iteration scope through
  `addScopeToNode`, stores `_x_refreshXForScope`, and is then initialized.
- `evaluator.js:43-68,116-133,166-228`: `evaluateLater(el, expression)`
  captures the element's stack; call-time `extras.scope` is merged before that
  captured stack. Its receiver-based error path is unsuitable for an init
  gate because some failures never call the receiver. Public `evaluate`
  (called `evaluateRaw` inside the module) instead returns or throws directly,
  and returns a Promise for an asynchronous expression.
- `lifecycle.js:90-112` and `directives.js:83-103,204-228`: tree initialization
  walks parent first, init interceptors run before directives, and deferred
  directive handlers flush in encounter order.
- `reactivity.js:30-56`: one directive utility's `effect` helper retains only
  its last cleanup closure. A Citry directive that processes several client binding
  tokens must therefore use one aggregate effect, not one utility effect per
  token.
- `x-on.js:6-21`, `utils/on.js:4-89`, and `binds.js:5-14,37-66`: event
  expressions normally evaluate from the element carrying the handler;
  modifiers can move the listener to `window` or `document`, add outside
  containment checks, or alter lifetime; public `Alpine.bind(element,
  bindings)` installs real Alpine directives and returns their cleanup.
- `alpine.js:24-87`: the embedded module exposes `reactive`, `effect`,
  `release`, `evaluateLater`, `evaluateRaw`, `addScopeToNode`, and `bind`.
  Citry must use this module-local object: the runtime deliberately leaves a
  different existing `globalThis.Alpine` in place, with a warning
  (`citry-events.ts:700-715`).

Repository archaeology and audited production prior art:

- `docs/design/alpinejs/alpine-vuetify-audit.md`: the old
  alpine-composition runtime evaluated `x-props` from `el.parentNode`, used a
  Vue-style returned-bindings object, and needed refs/watchers plus explicit
  disposal to keep returned primitives live. Its production patch replaced
  one watcher per prop with one watcher per whole props expression.
- `old-vuetify.zip` (`alpine-composition/src/component.ts`), `old-chk.zip`
  (the production component call sites), and `old-djc.zip`
  (`other/alpine-comp-modified.js`) were checked through the existing audits
  and directly where the exposure mechanics were relevant. They confirm the
  parent evaluation precedent, but none solves Citry's multi-root or
  shared-root identity because those runtimes attach one client component to
  one element.

Current framework comparison, version-stamped on 2026-07-18:

| Framework | Version checked | Update validation | Unknown component inputs |
|---|---:|---|---|
| Vue | 3.5.40 | The development build warns after assigning the new value; production omits this validation. See the [props guide](https://vuejs.org/guide/components/props) and [tagged resolver source](https://github.com/vuejs/core/blob/v3.5.40/packages/runtime-core/src/componentProps.ts). | Undeclared keys become fallthrough attrs; a multi-root component warns when it cannot apply them automatically. See [fallthrough attributes](https://vuejs.org/guide/components/attrs). |
| React | 19.2.7 | React 19 removed runtime `propTypes` checking. Manually calling `prop-types` 15.8.1 logs a deduplicated error but does not block rendering. See the [React 19 upgrade guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide) and [`prop-types`](https://www.npmjs.com/package/prop-types). | Custom components accept arbitrary props. Warnings concern values later forwarded to native DOM elements. See [React's unknown-prop warning](https://react.dev/warnings/unknown-prop). |
| Svelte | 5.56.5 | Type annotations are build-time only; the new value reaches the consumer at runtime. See [`$props`](https://svelte.dev/docs/svelte/%24props) and [Svelte TypeScript](https://svelte.dev/docs/svelte/typescript). | `$props()` contains supplied keys and rest destructuring captures extras. Static checking may reject them, but runtime does not. |
| Lit | 3.3.3 | A property's `type` is an attribute-conversion hint, not runtime validation; direct assignments render. See [reactive properties](https://lit.dev/docs/components/properties/). | Unknown attributes remain inert DOM attributes; unknown JS properties are ordinary non-reactive properties, with no warning. |

Citry's ratified fail-closed rule is intentionally stricter than all four.
The comparison calibrates the surface; it does not override the decision.

The checked-in browser harness
[`xprops_round_two_harness.py`](xprops_round_two_harness.py) answers the two
remaining Alpine uncertainties reproducibly. Run it with:

```bash
uv sync --locked --all-packages --group e2e
.venv/bin/python docs/design/alpinejs/xprops_round_two_harness.py
uv sync --locked --all-packages
```

Playwright 1.61.0 drove the already-installed Chromium against the repo's real
Alpine 3.15.12 CDN bundle. The interceptor saw `_x_refreshXForScope` before
directives and captured exactly `item` and `index`. A keyed reorder reused the
same clone serials while refreshing both values; removing a clone ran its
directive cleanup. Separately, an `x-text` span first rendered `"ok"` and
became empty when its reactive value changed to `undefined`. The optional
group was then removed; `uv pip freeze` had the same SHA-256 before and after
(`57bf95b92ca31968406cffe42df06966dab89d232a62ae2028ba8346fd76239a`). The
harness proves the pinned private mechanism, not yet a public Citry
client-instance target.

The observed sequence was `a(serial 1, value 10, index 0)` and
`b(serial 2, value 20, index 1)` initially; after keyed reorder it was
`b(serial 2, value 25, index 0)` and `a(serial 1, value 11, index 1)`.
Removing `a` recorded cleanup for serial 1, and the surviving `b` reached
`value 30, index 0` on serial 2. The `x-text` result was the empty string.

## Result in one picture

```text
parent template: <c-Child x-props="..." @click="..." />
       |
       | ComponentNode splits client binding attrs from kwargs
       v
CitryElement client binding metadata, still naming the supplying component
       |
       | child render assigns target id and ancestor-call edge
       v
data-citry manifest client binding record + opaque root carrier token
       |
       | general instance registry resolves target and source
       +---------------------------+
       |                           |
       v                           v
first target root             supported handler root(s)
one supplier effect          Alpine.bind + root evaluator
                              plus parent-data facade
       |                           |
       +------------+--------------+
                    v
          target instance lifecycle
     props bag, init gate, managed cleanup
```

The client binding is structured because one physical root can represent several
logical components. Raw same-name attributes cannot preserve two target IDs,
two parent scopes, or two independent handler expressions on that root.

## 1. Supply relocation

### Accepted: split resolved contributions at ComponentNode and carry a manifest client binding

The extraction point is `ComponentNode.render`, where the component tag's
attribute contributions are already evaluated in the parent's render context
but before the child validates its kwargs. Refactor the current
`_resolve_kwargs` work into one source-ordered resolver returning
`(kwargs, client_bindings)`. A raw pre-resolution partition is insufficient because a
`c-bind` mapping or a dynamic `c-*` attribute can intentionally add, replace,
or remove a client binding.

The resolver classifies these keys specially on semantic component targets:
ordinary registered `<c-*>` components and transparent `<c-component>`, but
not the HTML-producing `<c-element>` built-in:

- `x-props`;
- Alpine event shorthand `@event.modifiers` and its `x-on:event.modifiers`
  long form;
- Citry event shorthand `@c-event.modifiers`, recognized before the generic
  Alpine `@...` branch.

These are the complete special boundary surface. `x-show`, `x-model`,
`:class`, `x-transition`, ordinary `class`, and every other HTML or Alpine
attribute remain ordinary Python render-time component inputs. Citry does not
guess which child root or nested element should receive them. A reusable
component should expose an `attrs` kwarg and place it explicitly:

```html
<c-card
  x-props="{ compact: compact }"
  @click="selectCard()"
  @c-save="saveCard"
  attrs="{
    'x-show': 'visible',
    ':class': '{ selected: selected }',
    'class': 'card',
  }"
/>
```

```html
<!-- Card.template: the child owns this placement decision. -->
<article c-bind="attrs">
  <c-slot />
</article>
```

The same `attrs` input could instead be spread onto a different root or a
nested element. This keeps arbitrary attribute forwarding explicit while the
three special forms retain their directional meaning: props travel down;
Alpine and Citry events authored by the parent react at the child boundary.
`:c-*` remains invalid on a component tag because it binds State to an HTML
control; `#c-*` keeps its separate parser-level rules.

`<c-element>` follows HTML-element semantics despite being implemented by a
transparent built-in. It rejects `x-props` because it cannot be a client
component target. Alpine handlers, `@c-*`, and `:c-*` pass through as the
selected HTML element's attributes and use the ordinary HTML-element rewrite
and resolved-attrs hooks; they are not client bindings.

Direct, dynamic, and spread client binding contributions are all valid. Resolve every
contribution from left to right, including `c-bind` mapping entries in mapping
iteration order. Apply these exact rules:

1. The last contribution to an exact key wins. A final `None` or `False`
   removes that client binding; `True` is a pointed error because an expression client binding
   cannot be valueless.
2. A present client binding value must be a string containing the raw client
   expression or Citry handler spelling. Do not stringify arbitrary values.
3. Final client binding order follows each winning contribution's source position. On
   exact-key replacement, remove the old entry and insert the winner at the
   replacement position; removal deletes it, and a later re-add occupies that
   later position. Thus `@click="a" x-on:click="b"` followed by a spread that
   replaces `@click` runs the surviving `x-on:click` before the winning
   `@click`. Do not canonicalize those two spellings; Alpine permits both and
   they remain distinct handlers.
4. A direct key uses its attribute span. A key contributed by `c-bind` reports
   the spread's span plus the mapping key, so render-time errors still point
   to an actionable source.

For example, `c-x-props` may return a raw Alpine expression string or
omission, and a `c-bind` mapping may conditionally contribute `x-props`,
`@click`, or `@c-click`. Static `x-props` on a plain HTML element remains a
template-load error; a dynamically contributed one on a plain element fails
when attributes resolve. This dynamic support is deliberately different from
`#c-key`, whose expression-valued parser syntax remains template-authored
only.

`CitryElement` gains immutable client binding metadata next to `morph_key`. Once the
child instance has an ID, dependency emission writes a client binding record with at
least:

```js
{
  targetId: "c-child",
  targetClassId: "ChartCard_a1b2c3",
  sourceId: "c-parent",
  sourceClassId: "Dashboard_d4e5f6",
  parentCallId: "c-parent",
  clientBindings: [
    {
      kind: "props",
      expression: "{ theme: $state.theme }",
      sourcePosition: { template: "Dashboard.template", start: 182, end: 219 },
    },
    {
      kind: "alpine-event",
      bindingId: "r2",
      attribute: "@click.prevent",
      expression: "selectCard()",
      sourcePosition: { template: "Dashboard.template", start: 220, end: 247 },
    },
    {
      kind: "citry-event",
      bindingId: "r3",
      attribute: "@c-save",
      compiledSpec: { event: "save", handler: "saveCard", modifiers: [] },
      sourcePosition: { template: "Dashboard.template", start: 248, end: 271 },
    },
  ],
}
```

The exact armoring follows the existing manifests: JSON text in an inert
script, with values base64-encoded where they can terminate HTML. Roots carry
only opaque client binding tokens. A token may use an internal value of the registered
`x-props` directive for a props client binding and an inert `data-citry-client-binding` marker
for handler-only client bindings; the authored client source itself must not be copied
into a root attribute. Same-name carrier tokens may merge space-separated
because each token resolves to an independent record keyed by `targetId`.

Client binding metadata itself must force a dependency instance record. The current
dependency extension omits a component with no assets, and a handler-only
client binding may validly target exactly such a display component.

### The general instance registry

The dependency manager should create an instance record while processing the
manifest, before `flushCalls` can run:

```text
component id -> class id, roots, parent-call id, client binding records,
                expects-supply, client scope, init status,
                Events anchor (optional)
```

The Events `idToAnchor` map then becomes an optional field or sibling index
over this registry. It remains the owner of State, epochs, and event calls.
This avoids two false negatives in an anchor-only design:

1. a Component.js props consumer may declare no `Events`, so it has no anchor;
2. a handler-only client binding may target a Citry component with no Component.js at
   all.

The existing `liveInstances` map cannot substitute: it is private to
`citry.js` and is populated only after init or its validation skip
(`citry.js:384-387`), after the first-supply gate needed it.

The registry also exposes a current loader gap. `emit_events_dependencies`
injects the Alpine-bearing Events runtime only when an `Events` instance was
captured, but `decorateComponentContext` explicitly supports Component.js
instances without `Events`, and the prop resolver lives in that runtime. A
client binding must therefore force Events-runtime injection even when neither source
nor target declares `Events`. The defaults-only config form has the same
pre-existing gap when a page contains no Events instance and no client binding.

Recommended v1 loader rule: when the Events extension is enabled and a page
emits any client binding record or `$component` call, emit its runtime and bootstrap
before the dependency manifest. Display-only components still pay nothing
because they emit neither. Do not try to infer a `props` key by another regex
over Component.js: that would be unsafe for the ESM/source-language path
recorded in `asset_compiler.md` and `esm.md`. A later structured asset compiler
may provide finer class metadata without changing this public contract.

### Parent-scope evaluation

The supply evaluator is
`Alpine.evaluateRaw(targetRoot.parentNode, expression, extras)`, called inside
the aggregate Alpine effect. `evaluateRaw` preserves synchronous return and
throw semantics, while the enclosing effect still records reactive reads. In
contrast, `evaluateLater` routes syntax and runtime errors through Alpine's
error handler and may never invoke its receiver, which cannot settle an init
gate deterministically. The physical evaluation node preserves ordinary
Alpine `x-data` visible at the child's position. The client binding's `sourceId`
additionally selects a source facade passed in `extras.scope`:

- the source instance's exposed client `scope` (section 6);
- source-specific `$state`, `$loading`, `$error`, `$sendEvent`, and
  `$onEvent` when it has an Events anchor;
- the captured `x-for` iteration scope when applicable (section 3).

Alpine merges `extras.scope` before the captured parent stack
(`evaluator.js:116-133`), so these explicit logical-parent values win without
opening the child boundary to ambient inheritance. Ordinary Alpine DOM magics
retain `el.parentNode` semantics. In particular, `$el` is the real parent
evaluation node, not a phantom server component tag.

The source facade matters when a wrapper's entire template is
`<c-Card ... />`. Wrapper and Card share one physical root, so a DOM-only
innermost-id lookup selects Card and loses Wrapper's `$state`. `sourceId`
restores the logical supplier while physical parent evaluation still supplies
ordinary surrounding `x-data`.

### Root-shape matrix

| Rendered target | Example | `x-props` | Relocated handlers |
|---|---|---|---|
| One element root | `<article>...</article>` | The only root owns one aggregate supplier effect. | Bind to that root with ordinary element semantics. |
| Several element roots | `<h2>...</h2><p>...</p>` | The first live root owns supply, but the props bag, `scope`, effects, cleanup, and complete `ctx.els` belong to the one logical instance. | Supported by the positive `RootGroup` spike; stage two must lock real client binding and morph integration. |
| Template is exactly another component | `template = "<c-Card />"` | The inherited carrier reaches the shared root; target IDs keep wrapper and child contracts distinct. | Bind for the logical target, even though several logical instances may share one root. |
| Text-only or empty output | `template = "Done"` or `template = ""` | Supported by the positive isolated comment-range spike; stage two must integrate its identity normalization, mirror grouping, contextual parsing, nested-island, and preserved-comment requirements. | A DOM event binding still needs an `EventTarget`; the spike proved one logical `@c-poll` cadence without an Element. |

The maintainer's first-root hunch is therefore correct for `x-props`, but not
cosmetic. Evaluating on all roots would allocate duplicate effects, create
several competing first supplies, and make update order observable. First
root is the one correct owner; the bag remains instance-scoped and shared by
all roots.

"First" means the first currently live carrier, not the first root forever.
Every carrier initializes its one aggregate element-bound effect and watches
an element-local reactive set of active client binding tokens. The instance registry
elects one carrier per target by putting the target token only in that
carrier's active set. When the elected root is removed or replaced while
another carrier survives, cleanup unregisters it, the registry moves the
token to the next live carrier, and that carrier evaluates immediately
against the same instance props bag and already-settled init state. No second
init runs. Removal of the last carrier performs the ordinary logical-instance
teardown. Stage two must lock partial first-root removal and morph replacement,
not merely whole-instance removal.

Event handlers differ. An ordinary click in root B never bubbles through its
sibling root A, so first-root-only loses behavior. Naive all-root copying also
loses behavior:

- `.window` and `.document` install duplicate global listeners;
- `.outside` and `.away` treat a click in root A as outside root B;
- `.once` becomes once per root rather than once for the authored handler;
- debounce and throttle allocate independent timing state per root.

Public `Alpine.bind(root, {"@click.modifiers": clientBindingCallback})` is the right
single-root mechanism. Alpine retains modifier semantics and returns cleanup.
The listener and modifier semantics belong to the physical child root, but the
authored expression belongs to the exact parent source location. The client binding
callback therefore evaluates against the live source-location carrier, never
the child evaluator. Ordinary names and lexical Alpine magics such as `$data`,
`$root`, `$id`, and `$refs` all come from that source. Evaluator extras replace
only `$el`, `$dispatch`, and `$event` with physical-child values; native
`event.currentTarget` is never forged. Assignment such as `selected = true`
writes the owning parent data object, and a missing parent name cannot fall
through to child `x-data`.

The explicit source Citry facade needs a write-through own-accessor bridge
when it is supplied through evaluator extras. A nested Alpine merge proxy
preserves reads, but Alpine's outer merge proxy does not recognize the inner
proxy's virtual keys as owned when assigning. Stage two must expose each
facade key as an own getter/setter that delegates to the original reactive
facade, with the three physical overrides taking precedence. The focused
spike proves both facade reads and assignment for the Alpine handler and the
Citry stand-in argument expression.

This is the isolation boundary for an Alpine handler expression and a Citry
binding's optional argument expression authored on a child component tag. A
handler authored inside the child's own template is different because its
source location is inside that child; it keeps the child's local Alpine scope
and refs. Passing a callback through declared `x-props`, exposing it explicitly
through the child's stable `scope` in init, and then calling it from a
child-local handler is the deliberate way to grant child code that capability.

```html
<c-action-button
  x-props="{ givenCallback: () => selected = true }"
/>
```

```js
$component({
  props: {
    givenCallback: { type: Function, required: true },
  },
  init: ({ props, scope }) => {
    scope.givenCallback = props.givenCallback;
  },
});
```

```html
<!-- ActionButton.template -->
<button @click="givenCallback">Run</button>
```

A faithful multi-root grouped listener needs a Citry-owned `RootGroup` and
`onGroup` adapter, including modifier ordering parity with `utils/on.js`;
copying attributes is not that adapter. The group owns the ordered live roots,
shared listener state, and one cleanup lifetime. The minimum proof matrix was:

[React's Canary Fragment instance](https://react.dev/reference/react/Fragment)
is useful aggregation and lifecycle prior art: it can add listeners across a
Fragment's first-level roots, but it does not define Alpine's union modifiers.
[Vue's multi-root fallthrough rule](https://vuejs.org/guide/components/attrs#attribute-inheritance-on-multiple-root-nodes)
shows the conservative alternative: it declines automatic forwarding when no
single root is unambiguous. Citry had to prove the stronger grouped contract
rather than assuming either precedent already supplied it.

- attach ordinary listeners to each root, but attach `.window` and `.document`
  once for the group;
- define `.outside` and `.away` against union containment, so an event inside
  any root is inside the component;
- share `.once`, debounce, throttle, and timer state across roots;
- treat `.self` as any member root, preserve capture/passive ordering, and
  apply key filters exactly once;
- suppress non-capturing `mouseenter`, `mouseleave`, `pointerenter`, and
  `pointerleave` transitions whose `relatedTarget` is another member root;
- preserve native `event.currentTarget`. A direct listener reports its real
  root; a deferred callback follows native semantics rather than manufacturing
  a wrapper target.

Do not deduplicate by Event object: the
[DOM dispatch algorithm](https://dom.spec.whatwg.org/#concept-event-dispatch)
permits an Event to be dispatched again after its dispatch flag clears. The
union is a set of DOM nodes, not a wrapper's geometry; gaps between roots
remain outside. The pointer enter/leave cases must follow the
[Pointer Events definition](https://w3c.github.io/pointerevents/#the-pointerenter-event)
and suppress only moves whose `relatedTarget` remains in the member union.
Focus keeps aggregate native semantics rather than inventing a hidden group-
focus boundary. Because Alpine's `utils/on.js` is not a public API, Citry owns
the adapter and keeps a single-root differential canary against the pinned
Alpine version.

**Spike result, 2026-07-19:** the
[`RootGroup` browser spike](spike-root-group.md) passed this matrix in Chromium,
Firefox, and WebKit. Its single-root output matched public `Alpine.bind` for
the pinned modifier canaries, while grouped cases proved union containment,
one shared once/timing lifetime, dynamic root changes, native current-target
values, open-shadow composed paths, one poll cadence, and a stable live `els`
array. The mechanism gate is therefore clear and the generic multi-root error
is not the v1 path. Stage two must retain the spike's explicit policies:
ordinary listeners per root; one global/outside listener; a separately
captured evaluation carrier without forged `currentTarget`; any-visible-root
outside eligibility; pending direct work dropped with its dead carrier; and
full teardown canceling pending work. Closed-shadow outside/away remains a
specific unsupported case until it has a shadow-local listener design.

Handler-only client bindings are first-class. A child need not have `x-props`,
Component.js, or an Events class merely because its parent authored `@click`
on the component tag. `interceptInit` resolves each opaque
`data-citry-client-binding` token, installs the binding with `Alpine.bind`, and stores
the returned cleanup under that element and logical client binding. The installed
binding invokes the isolated source evaluator; it never passes the authored
expression directly to `Alpine.bind`, which would capture the child stack.
Attribute/morph
replacement runs the old binding cleanup before installing the replacement;
logical target teardown runs any remaining cleanup exactly once. This path
must not wait for a component callback registration that will never exist.

### Citry event handlers stay owned by the logical parent

An `@c-*` handler on a child component tag remains owned by the component in
whose template it was authored. The child roots are only the physical event
carriers. Template-load validation therefore checks the handler and modifiers
against the source class, then client binding emission preserves `sourceId`,
`sourceClassId`, `targetId`, `bindingId`, and the compiled binding spec.

Dispatch must use the exact captured source Events anchor. A nearest-anchor
walk from the triggering child root would incorrectly send from the child.
The optional argument expression follows the shared boundary-handler
isolation rule above. It uses the captured parent lexical/data scope and source
Citry magics; it never evaluates against the child or overlays a partial parent
object. The server-handler name itself is parsed and validated, not evaluated.
Physical `$el`, `$event`, and `$dispatch` still belong to the triggering child
root. Native `event.currentTarget` remains untouched. The focused
[`boundary-handler scope spike`](spike-citry-handler-refs.md) locked this split
for whole Alpine expressions and optional Citry argument expressions in
colliding ordinary-data and ref cases, single and grouped roots, a shared
physical root, morph, debounce, teleport, and liveness across Chromium,
Firefox, and WebKit. Citry's additional design rule is Events ownership:
dispatch and queue state use the exact captured source Events anchor rather
than the child's nearest anchor. The spike did not prove that parsing,
validation, dispatch, or queue integration.

The queue node likewise validates logical source liveness and physical target
liveness separately. It remains owned by the parent anchor through dequeue,
replacement, and retirement. Loading belongs to the source anchor, while the
triggering child root also receives the per-trigger busy marker. `@c-poll`
creates one logical timer per client binding or root group, sourced from the parent.
`:c-*` remains an error on semantic component targets: State bindings attach
to concrete HTML controls and are not an events-up boundary channel.

Suggested fallback root-shape errors if the corresponding spike fails:

```text
x-props on <c-plain-text> cannot be applied because PlainText rendered no
HTML element root. Add an element root or remove x-props.
```

```text
@click on <c-two-roots> cannot be relocated faithfully because TwoRoots
rendered 2 element roots and the grouped-listener adapter did not accept this
modifier combination. Add one wrapper root or put the handler on an element
inside TwoRoots.
```

### Worked roots

```html
<!-- Single root: one supply and one click client binding. -->
<c-chart-card
  x-props="{ theme: $state.theme }"
  @click="selected = true"
/>
```

```python
class ChartCard(Component):
    template = "<article><canvas></canvas></article>"
```

The rendered `<article>` carries an opaque client binding token. The props record is
evaluated once for ChartCard against the parent, while the click uses
`Alpine.bind` on the article and evaluates `selected = true` in that same
parent context.

```python
class Wrapper(Component):
    template = '<c-ChartCard x-props="{ theme: $state.theme }" />'
```

Wrapper and ChartCard share the article. The record still names ChartCard as
the target and Wrapper as the source. A second client binding supplied to Wrapper by
its own parent remains a separate token and cannot collide.

```python
class Summary(Component):
    template = "<h2 x-text=\"title\"></h2><p x-text=\"detail\"></p>"
```

For an `x-props` client binding, the `<h2>` owns the supplier effect, but both roots
receive the same stable `scope` layer. `ctx.els` initially contains both the
`<h2>` and `<p>`, so fields written to `scope` can drive Alpine expressions on
either root. The supplier's location does not narrow the logical instance.
If partial root changes do not rerun init, stage two must choose and test either
a stable `ctx.els` array updated in place or a getter returning current roots;
the existing one-time snapshot cannot satisfy a live-roots promise.

### Rootless lifecycle spike

An element is not intrinsically required to validate props, run `$component`
init, own managed effects, or expose an instance with `ctx.els = []`. The
plausible representation for text-only or empty output is a comment range:

```html
<!--citry-start:c7-->Done<!--citry-end:c7-->
```

The instance registry can own the range, evaluate supply from the range's
parent plus captured source facade, and run init and teardown without a fake
wrapper. Event client bindings that require a DOM `EventTarget` still fail; `@c-poll`
may work because it is a logical timer rather than a DOM listener. The pinned
morph package has a `morphBetween(startComment, endComment, html)` primitive,
but its string parser and positional treatment of arbitrary comments are not a
general range lifetime.

**Spike result, 2026-07-19:** the cross-browser
[`rootless lifecycle spike`](spike-rootless-lifecycle.md) is positive. A
Citry-owned registry proved text/empty init, reactive supply, managed helpers,
one poll cadence, stable in-place `els`, text/Element transitions, contextual
`tr`/`td`/`option`/SVG parsing, stable-anchor normalization, grouped mirrors,
keys, movement, nested and adjacent ranges, and exact cleanup in Chromium,
Firefox, and WebKit. The identity and morph adapters are load-bearing:
incoming HTML is parsed with `Range.createContextualFragment()` into a shallow
clone of the real parent before `morphBetween`, and live nested ranges are
normalized to stable anchor keys and temporarily collapsed to keyed inert
templates during an outer morph. Mirrored physical pairs share one logical
lifetime. Stock
string morphing fails the `tbody` control, while unguarded stock morphing
destroys nested comment identity. Preserving Citry comments is a deployment
requirement; pre-adoption stripping fails pointedly. DOM event client bindings still
fail pointedly while `els=[]`, but logical polling is supported. Stage two may
therefore support rootless client activity without an observable wrapper.

### Dynamic `<c-component>` must be transparent to client bindings

Static `<c-component is="Card">` already compiles to the selected component
node. The dynamic built-in must forward resolved client bindings separately from kwargs
when it creates the selected target `CitryElement`:

```html
<c-component
  c-is="selected_component"
  x-props="{ value: currentValue }"
  @click="select()"
  @c-save="persist({ id: currentValue.id })"
/>
```

The selected class and its actual instance are the target; the component that
invoked `<c-component>` remains the source; the transparent built-in never
becomes a client-side binding identity. Acceptance must cover direct, `c-*`, and
`c-bind` client binding contributions, ordinary attributes remaining target kwargs,
and a selected-class replacement cleaning the old client binding registrations exactly
once.

### Alternative orthogonal authoring surfaces remain open

The direct boundary syntax is the primary design, but three alternatives are
worth keeping as possible advanced or future front ends to the same client binding
protocol:

1. A non-rendering `<c-client-bind>` meta component wrapping exactly one child
   component. It is visually explicit but adds nesting and another structural
   rule.
2. One Alpine `x-bind` object bundle carrying props and handlers. Alpine can
   install directive keys from objects, but the pinned version evaluates the
   top-level object once and does not diff changing key sets, so Citry would
   own reevaluation, key diffing, cleanup, and source diagnostics.
3. An advanced JS or TS child-reference/connect API. This is orthogonal and
   ESM-friendly, but it still needs target identity, ordering, and teardown.

None is a separate runtime model. If adopted, each compiles or registers the
same structured client binding records. They do not justify making general HTML attrs
fall through automatically.

## 2. x-props on a non-Citry target is an error

Use exact registry membership, never `closest()`.

At template load, placement is statically knowable for a literal attribute:
authored `x-props` is valid on a component tag and invalid on a plain HTML tag
or `<c-element>`. A future named-client-component helper must add a
parser-recognizable target marker if it wants the template loader to make a
static exception; `x-data="meter"` alone is indistinguishable from an ordinary
Alpine data provider. The current parser error should be:

```text
'x-props' is only valid on a Citry component tag; <div> is a plain HTML
element. Put it on the <c-...> tag whose Component.js declares the prop.
```

At render time, `c-x-props` or a `c-bind` mapping key that resolves to
`x-props` on a plain element receives the equivalent pointed error. At
runtime, host-inserted HTML, Alpine-created attributes, and future named
client components require a dynamic check. The registered directive must
resolve the exact target element or client binding token to an instance-registry entry,
and for a server component confirm the root carries the exact
`data-cid-<targetId>` marker. A plain descendant inside an interactive
component is still plain; accepting it because `closest("[data-cid]")` finds
an ancestor would silently reintroduce prop inheritance.

Suggested runtime error:

```text
[Citry] x-props on <div id="preview"> does not target a Citry client
component instance. Author x-props on the <c-...> component tag; Citry
relocates it to that instance.
```

A second error covers a real Citry component whose class registration has no
declared client props:

```text
[Citry] component 'ChartCard_a1b2c3' instance 'c7' received x-props, but its
$component registration declares no props. Add a props map or remove x-props.
```

Static placement errors fire during template load. At runtime, exact target
membership is decided after draining any colocated manifest so a valid
fragment is not rejected merely because its observer callback has not run.
Morph application must likewise register fragment client binding records before the
morph, matching the existing link-before-morph rule.

The "declares no props" error has a later clock. Directive initialization can
legitimately precede an external Component.js class registration, so absence
from the current registration table is not evidence that the eventual class
has no props. Keep that client binding node deferred until class registration is
definitive (or server metadata definitively says no client registration will
arrive). A later bare-callback registration or a config registration without
`props` rejects the waiting node and settles its DAG branch. This must use the
same registration wake-up path as ordinary pending dependency calls, not a
timer.

## 3. x-for without an extra wrapper

### The scope mechanism is sound

Alpine itself marks the direct clone. `x-for.js:117-128` creates the clone,
prepends its reactive iteration scope, assigns `_x_refreshXForScope`, and only
then calls `initTree`. Citry's init interceptor runs before directives, so it
can detect:

```js
typeof el._x_refreshXForScope === "function"
```

and capture `el._x_dataStack[0]` into a WeakMap immediately before boundary
attachment truncates the stack. The `x-props` evaluator remains rooted at
`el.parentNode`, but receives the captured reactive loop object in
`extras.scope`. Thus `item`, `index`, enclosing parent `x-data`, and the
explicit Citry source facade are all visible. Reused keyed clones update the
same reactive loop object through `_x_refreshXForScope`, so the supplier
effect tracks later item/index refreshes.

This is a new private-Alpine dependency. The checked-in harness observed all
of the following against 3.15.12; stage two must lock them in the real Events
bundle:

1. `_x_refreshXForScope` exists before the clone's directives run;
2. `_x_dataStack[0]` is the reactive loop scope at interception time;
3. Citry captures it before isolation truncation;
4. a keyed clone refresh re-evaluates `{ value: item.value, index }`;
5. directive teardown releases the one aggregate supplier effect.

### The product target has a separate prerequisite

Alpine `x-for` clones DOM. Cloning a real server-rendered Citry root also
clones `data-cid-<id>`, producing several DOM copies of one server-minted
instance. Rewriting only that attribute would make the copies look different
without giving them independent runtime identity. That is invalid, not a
supported way to compose Citry server components, exactly as `events.md` 5.5
already states.

The landed runtime also has no named-client-component helper or registry.
Therefore there is no honest end-to-end v1 example for direct `x-for`
`x-props` **yet**: a plain Alpine `x-data` element is a non-Citry target and
must error, while a server Citry root must not be cloned.

### Why intercepting `x-for` is possible but is a different feature

Timing is not the fundamental blocker. An interceptor runs after Alpine has
created a clone and before its directives initialize, so it could allocate
fresh values. The complete operation, however, is not a `data-cid-*` rewrite.
It is client-side instantiation of a server-rendered component blueprint. For
every clone it would need to recursively remap:

- all per-instance and fixed `data-cid` markers;
- general-registry records, dependency calls, init/cleanup ownership, ancestry
  edges, and client binding target/source references;
- Events anchors, State objects, epochs, pending calls, loading, errors,
  subscriptions, poll timers, and binding IDs;
- keyed-morph identity, root groups, prototype-sensitive maps, and any
  component IDs embedded in manifest payloads;
- ordinary DOM identity references when present, including `id`, `for`, and
  ARIA IDREF attributes.

Alpine's own `x-for` also clones only the template's `firstElementChild`, so a
multi-root or text-root Citry blueprint would already be truncated before the
identity work began. Nested and shared-root component records make the remap
recursive rather than local.

This is ambitious but not theoretically impossible. The Citry State token
binds the component class and State payload, not the render's component ID,
and the server is largely instance-stateless between calls. A future blueprint
protocol might therefore mint independent client anchors and lifetimes from
one authenticated initial descriptor without a server round trip per clone.
That needs its own security, identity, morph, call, and teardown design; it
must not be smuggled into WP23 as an attribute rewrite. Server lists remain
`<c-for>`. Client loops can target a named client-component helper only if
that separately designed helper enters v1; otherwise WP23 makes no direct
`x-for` component-composition claim.

Recommendation: build and canary the loop-scope capture in WP23, and make
public wrapper-free `x-for` support conditional on bringing the already
designed named-client-component helper into v1. Such a helper must create one
fresh client instance-registry entry per clone. During `interceptInit`, it
must recognize and register the marked client target before the `x-props`
directive runs; `x-data` registration by itself is neither target membership
nor sufficient ordering. A direct shape can then be:

```html
<template x-for="(item, index) in items" :key="item.id">
  <div
    x-data="meter"
    data-citry-client="meter"
    x-props="{ value: item.value, index }"
  ></div>
</template>
```

Here both `meter` and `data-citry-client` are schematic, not proposed public
spellings. The important requirement is an explicit marker that lets the
parser and runtime distinguish a Citry client target from an arbitrary
`Alpine.data` call, plus a fresh registry identity per clone. The helper's
name and public API need their own ratification. If that helper does not enter
v1, the no-wrapper mechanism still lands as proven substrate but WP23 must not
claim a user-visible `x-for` composition case it cannot create.

Round-two item 3 is therefore only partially met. Loop-scope capture,
keyed-refresh tracking, and teardown are proven; the required public target
constructor does not exist and remains a product-design blocker.

## 4. Deferred init ordering

Maintainer status: accepted for WP23 stage two on 2026-07-19.

### Accepted: an ancestry DAG, not a global barrier

Extend each dependency call node with the nearest ancestor component-call ID
and an instance-level `expectsSupply` bit (or client binding-record reference). The
server knows both from the render tree and the child client binding metadata. A props
declaration alone is not enough: a component with no authored `x-props`
resolves defaults immediately.

One call moves through:

```text
waiting-registration -> waiting-data -> waiting-first-supply
                     -> waiting-ancestor -> running -> settled
                                                \-> cancelled
```

It may run only when its class registration and `js_data` are ready, its first
supply has settled when `expectsSupply`, and its nearest ancestor call has
settled. Settlement includes successful init, validation skip, callback
failure, and removal cancellation; failures release descendants rather than
deadlocking them. Independent branches have no edge and continue.

The comparison:

| Choice | Benefit | Cost | Verdict |
|---|---|---|---|
| Global pending-supply barrier | Tiny change; literal total document order. | One missing or malformed supply freezes every later component, including unrelated UI. It regresses the current queue's pass-unready behavior. | Reject. |
| Ancestry DAG | Preserves the load-bearing order, parent before descendant, while independent branches start. Failure and cancellation have explicit release semantics. | Adds parent-call metadata and per-node state. | Accepted. |

This is cheaper than the Events request DAG because component ancestry is
static and the server already has `component.parent`. Emit the edge rather
than reconstructing it from DOM: calls can arrive before roots parse, and a
shared root does not encode containment faithfully enough.

The existing snapshot/reentrancy rule remains. Cleanup for an old invocation
runs once when its replacement node enters deferral, not on each retry. A
deferred node removed before supply is cancelled, any late supply is ignored,
and it must be tracked before today's post-init `liveInstances` insertion.

Alpine's initial walk supplies the common path naturally: parent-first tree
walking plus synchronous first effect execution makes parent supply nodes
settle before descendant directive handlers flush. The explicit DAG covers
head-placed manifests, late class scripts, shared roots, and fragments where
those timings otherwise differ.

Worked order:

```text
Page init (ready)
  Chart init (waiting for first supply)
    Legend init (ready, but waits for Chart)
  Search init (ready, independent)
```

`Page` runs, `Chart` blocks only `Legend`, and `Search` proceeds. Whether the
Chart supply validates or fails, Chart then settles and Legend is released.

### Supply-expression failure settlement

The aggregate effect calls module-local `Alpine.evaluateRaw` inside a
`try`/`catch`; it must not use `evaluateLater`'s receiver as a completion
signal. A successful supply synchronously returns a plain object whose
prototype is `Object.prototype` or `null`. `null`, arrays, functions, class
instances, Promises, and other thenables are invalid. In particular, an
expression containing `await` returns a Promise from Alpine's raw evaluator
and is rejected rather than turning first supply into an unbounded async gate.

On the first supply, a syntax error, runtime throw, or invalid result shape is
terminal for that component invocation. Log one pointed error, skip init,
deactivate the supplier token, and settle the node as a validation skip so
descendants are released. Removal can still cancel a node that has not yet
reached this decision. Example messages:

```text
[Citry] component 'ChartCard_a1b2c3' instance 'c7' could not evaluate
x-props: selectedTheme is not defined. Client init was skipped.
```

```text
[Citry] component 'ChartCard_a1b2c3' instance 'c7' x-props must
synchronously return a plain object; got Promise. Client init was skipped.
```

After a successful init, the same failure classes are recoverable update
failures. Clear every declared resolved prop to `undefined` in one reactive
write phase, log once per failure signature, and keep the effect alive. The
next valid plain-object evaluation repopulates the bag. Clearing every key is
necessary because no object result exists from which valid siblings or
omissions can be distinguished. These failures also fire no Events lifecycle
event.

Stage two must cover malformed syntax, a missing-name runtime throw, a
throwing getter, Promise/thenable, `null`, array, and a valid recovery. It must
also prove that every first-supply failure settles its ancestry branch instead
of freezing descendants or unrelated calls.

## 5. Managed effect() and reactive()

Maintainer status: accepted for WP23 stage two on 2026-07-19.

Expose exactly these two context helpers:

```ts
reactive<T extends object>(value: T): T
effect(callback: () => void): () => void
```

`reactive(value)` delegates to the embedded module-local `Alpine.reactive`.
A reactive proxy has no release operation; it becomes collectible when the
instance and user references disappear.

`effect(callback)` delegates to module-local `Alpine.effect`, records the
effect reference under the current init invocation, and returns an idempotent
`stop()` that calls module-local `Alpine.release` and removes it from the
managed set. The callback is wrapped in an `active` guard: Alpine's scheduler
may already contain a runner when teardown calls `release`, so the guard
prevents one queued post-destroy callback.

There is no separate `release` context member. Early disposal uses the
returned stop function; normal disposal is automatic. This keeps users away
from both the global Alpine object and Alpine's effect-reference/release
pairing.

The dependency manager should let a context decorator return an
instance-cleanup function, changing today's documented ignored return. The
Events decorator installs `effect` and `reactive` and returns
`disposeManagedEffects`; the manager stores it before the cleanup returned by
`init`, then drains managed effects before user teardown. If init throws after
creating an effect, managed disposal runs immediately. One failing cleanup is
logged and does not skip the rest, matching current cleanup isolation.

The helper should catch and log a user effect callback exception so one
invalidated prop read cannot abort Alpine's whole scheduler queue. It does not
convert that programming error into `$error` or an R3 event.

Required stage-two tests:

- a managed effect re-runs after a managed reactive write;
- manual stop is idempotent;
- teardown suppresses an already queued rerun;
- init throwing after effect creation disposes immediately;
- a re-render owns a fresh effect set and old cleanup runs once;
- another `globalThis.Alpine` receives no helper calls;
- one cleanup throwing does not skip the others.

## 6. Exposing init values to Alpine expressions

Maintainer status: accepted for WP23 stage two on 2026-07-19.

### Accepted: a stable reactive `scope` context member

Keep the init return value exclusively for cleanup. Add `scope`, one stable
`Alpine.reactive({})` per logical component instance:

```js
$component({
  props: {
    query: { type: String, required: true },
  },

  init({ scope, props, effect }) {
    scope.queryLength = 0;
    scope.clear = () => {
      scope.queryLength = 0;
    };

    effect(() => {
      scope.queryLength = props.query == null ? 0 : props.query.length;
    });
  },
});
```

The template reads `queryLength` and calls `clear()` directly. Reassigning
`scope.queryLength` mutates the same reactive property, so no `ref()` layer is
needed.

Mechanically, extend the fixed-name `data-cid` marker to every client-active
general-registry instance, not only Events anchors. Its server serialization
order remains outermost to innermost, with the innermost ID last. The init
interceptor reads that fixed marker and attaches exactly the last ID's stable
reactive scope object to the physical root; outer shared-root instances stay
registry-only on that element. This choice comes from the marker's structural
order and must not depend on client binding-record or manifest iteration order. The
one-shot `boundaryAttached` guard is then safe because it never attaches an
outer scope first and attempts to replace it later. Stage two must include a
shared root whose manifest records arrive in the reverse order.

This replaces today's fresh `{}` boundary entry per root with the innermost
instance's shared reactive scope object and attaches that same object to all
of that instance's roots. General-registry records, and therefore their scope
objects, must be created before directive evaluation. The registered
`x-props` client binding directive runs before `x-data` and ordinary expression
directives; first supply can then release init and populate `scope` before
`x-text="queryLength"` evaluates. A user's `x-data` on the same root remains a
separate higher-precedence layer and can intentionally shadow an exposed
name. Citry never mutates the user's object.

For a multi-root component, `ctx.els` still contains every element root and
the same `scope` object is attached to every normal root even though only the
first live root owns the supplier effect. Thus a value written through
`scope` is visible to Alpine expressions on all roots. The positive
`RootGroup` spike pins `els` as a stable array updated in place, including
clearing it on teardown. Stage two must update that array during real morph
membership changes rather than leaving today's one-time snapshot stale.

On a physical root shared by wrapper and child, only the innermost component
has an Alpine expression surface, as already true for `$state`. If that
innermost general instance declares no Events anchor, Events magics resolve to
their existing inert mid-boundary behavior rather than falling back to the
outer instance. The wrapper's scope remains available to its own Component.js
callback and through the explicit source facade when it supplies the child.

Rejected for v1: a Vue-style object returned from init. It collides with the
existing cleanup return, and a returned primitive does not follow later local
rebinding without refs or property-rewriting machinery. The old audited stack
paid exactly that complexity. Direct mutation of one stable reactive `scope`
has the needed identity using only Alpine's existing engine.

`scope` is the deliberate name: `data` already means server `js_data`,
`state` means server Events State, and `props` means declared parent inputs.
`js_data` may be hash-deduplicated and shared between sibling instances, so
mutating `ctx.data` to expose Alpine names would also be an identity bug.

## Pending maintainer review boundary

Section 7 remains a recommendation pending maintainer review. It must not yet
be read as ratified Events behavior or unconditional stage-two scope. Sections
8 and 9 were accepted on 2026-07-19 and are now part of the stage-two contract.

## 7. Update-validation failure surface

### Recommendation: clear the rejected resolved value and keep the scheduler alive

Default factories run once when the logical instance record is created and
their results are stored by prop. Every successful plain-object evaluation
resolves from that same per-instance default table, not from the previous
props bag. An omitted optional prop resets to its stored default value (the
same object identity for that instance), or to `undefined` when it has no
default. An explicitly supplied value that fails validation clears to
`undefined`; it never falls back to the default. This distinguishes omission,
which asks the declaration to resolve the value, from an invalid explicit
input, which must remain visible as a contract failure.

Every supplier evaluation validates every declared prop. On an update:

1. A type mismatch or missing required key sets that resolved prop to
   `undefined`. The previous value is never retained, and an explicitly
   invalid value never falls back to the default.
2. Independently valid sibling keys apply in the same evaluation.
3. A direct `console.error` names class, instance, prop, expected type, and
   the clearing behavior. Deduplicate by instance, prop, and failure signature
   for one failure episode; a valid value clears the episode and re-arms it.
4. Do not throw from the supplier effect. Do not touch `$error`.
5. Fire neither `citry:events:error` nor `citry:events:stale`. The former is
   an event-call failure; the latter has an enumerated set of request/action
   drop reasons. A client props contract violation is neither.
6. The next valid update writes the valid value and ordinary reactivity
   recovers. `init` does not run again.

Exact messages:

```text
[Citry] component 'ResultMeter_9f2c41' instance 'meter-7' prop 'query'
rejected an x-props update: expected String, got number. The resolved prop
was cleared; the previous value was not retained.
```

```text
[Citry] component 'ResultMeter_9f2c41' instance 'meter-7' prop 'query' is
required, but the x-props update omitted it. The resolved prop was cleared;
the previous value was not retained.
```

The real-Alpine browser check above proves a direct `x-text` binding becomes
empty when its reactive value becomes `undefined`, then can repaint on the
next valid value. Stage two should preserve that as an e2e assertion, not rely
on the DOM conversion incidentally.

The limit must be documented honestly: Citry can clear the props bag and
reactive bindings, but cannot generically reverse arbitrary imperative DOM a
previous effect drew. A managed effect receives `undefined` and should handle
the invalid state, as the `scope` example does. If it throws, the managed
helper logs the callback error and isolates the scheduler, but old imperative
output may remain until a valid update recovers it. A future component-level
invalid-state hook is preferable to silently retaining the valid prop.

At first supply, the existing fail-before-init contract remains: a missing
required or wrong-typed value logs the pointed validation failure and skips
init. Defaults-only instances keep today's immediate resolution.

## 8. Unknown supplied keys

### Accepted: reject the key, apply valid siblings, no setting

An unknown own enumerable key is ignored and reported with one direct
`console.error` per instance/key episode. Its value never enters the resolved
bag. Valid declared siblings still apply. If the typo also leaves a required
declared prop absent, report both failures; first init remains gated by the
required-prop failure.

```text
[Citry] component 'ChartCard_a1b2c3' instance 'card-4' received unknown
x-props key 'titel'; declared props are 'theme', 'title'. The unknown key was
ignored.
```

No throw, `$error`, R3 event, or framework setting. `x-props` is an explicit
schema channel, while ordinary HTML/Alpine attributes and one declared object
prop remain the extensible channels. A `strictProps` or `allowUnknownProps`
knob would make the same component contract page-dependent without a proven
use case.

Enumerate own keys only. Never assign `__proto__`, `prototype`, or
`constructor` from supplied data. If field experience finds a real open-ended
contract, add an explicit declaration-level rest facility rather than making
all contracts permissive.

This is stricter than Vue fallthrough attrs, React component props, Svelte
rest props, and Lit's inert unknown attributes. That difference is intended:
the maintainer ratified rejected-by-default specifically to catch optional
prop typos that those systems permit.

## 9. Default-value reuse documentation

**Accepted 2026-07-19.**

Proposed user-facing paragraph:

> Object and array defaults must be factory functions, for example
> `default: () => ({})` or `default: () => []`. A component's prop declaration
> is stored once per class, so a literal object or array would be the same
> JavaScript reference for every instance. If one instance mutated a nested
> value, whether directly or through a library that retained the object,
> sibling instances would observe the same mutation. Citry's read-only props
> view blocks reassignment of declared top-level keys, but deliberately does
> not deep-freeze nested objects or arrays: supplied values may be
> Alpine-reactive or intentionally shared by reference. Citry therefore calls
> each default factory once per instance and reuses that instance's result for
> its lifetime, keeping defaults isolated without cloning or freezing user
> data.

## Accepted stage-two shape and remaining gates

The accepted implementation direction is:

1. Resolve semantic component-target contributions in source order, then split
   the result into kwargs and structured client bindings. Only `x-props`, Alpine event
   handlers, and Citry `@c-*` event handlers become client bindings. Dynamic and `c-bind`
   contributions follow the same exact-key ordering and type rules;
   `<c-element>` remains on the HTML-element path.
2. Carry client bindings on `CitryElement`. Rendering assigns actual target ID, source
   ID and class, the nearest ancestor call edge, and `expectsSupply`.
   Dependency emission includes client binding-only instances.
3. Create a general instance registry beneath optional Events anchors before
   calls flush. Every client-active instance gets one stable reactive `scope`;
   the first live root owns supply while all roots share props, scope, effects,
   cleanup, and `ctx.els` membership.
4. Evaluate supply through module-local Alpine against the physical parent and
   explicit source facade. Schedule init through the accepted ancestry DAG,
   so one waiting or failed branch never blocks unrelated components.
5. Expose `{ id, els, data, state, props, scope, effect, reactive, sendEvent,
   onEvent }`. Managed effects dispose before user cleanup and immediately on
   init failure.
6. Forward client bindings through dynamic `<c-component>` to its actual selected
   target. Alpine handler expressions and optional Citry argument expressions
   evaluate against the exact source location while `$el`, `$dispatch`, and
   `$event` come from the physical child. Native `currentTarget` remains
   untouched. A component-tag `@c-*` binding additionally keeps its parsed
   server-handler name
   and the source parent Events anchor.
7. Adopt client binding records before incoming roots initialize, and cancel deferred
   init, listeners, timers, and managed effects exactly once on removal or
   replacement.

The grouped multi-root `RootGroup` mechanism gate is DONE and positive, and
its stable in-place root array pins the live `ctx.els` representation; real
morph adoption still needs stage-two acceptance coverage. The rootless
comment-range mechanism gate is also DONE and positive under the contextual
parsing, nested-island, and preserved-comment requirements recorded above;
real serialization, registry, and morph integration still need stage-two
acceptance coverage. The focused boundary-handler isolation gate is DONE and
positive for Alpine handler expressions and Citry argument expressions:
evaluate ordinary names and lexical magics against the exact source location
at delivery, never against the child or the source instance's first root. Only
`$el`, `$dispatch`, and `$event` come from the physical child; native
`currentTarget` remains untouched. Real Citry handler parsing, source Events
validation, client binding, source-location election, morph, and dynamic-target
integration remain stage-two acceptance work. The named client-target helper
gates the
user-visible direct-`x-for` case. A later client-side blueprint-instantiation
feature would be required to clone server-rendered Citry identity safely;
rewriting `data-cid-*` alone is not that feature.

Section 7 remains pending. Its invalid-update recommendation must not enter
normative stage-two tests until the maintainer completes that part of the
review. Sections 8 and 9 are accepted: unknown keys are ignored and reported
per episode while valid siblings apply, and default factories run once per
logical instance with that result reused for the instance lifetime.

## Fold status for events.md 5.5

The accepted parts of this report, including sections 8 and 9 plus the
boundary-handler isolation spike result, are folded into `events.md` 5.1 and
5.5 as part of the 2026-07-19 documentation update. Pending section 7 stays
here as a recommendation rather than being copied into normative design text.

## Decision status

Accepted for WP23 stage two on 2026-07-19:

1. **Relocation path:** resolve source-ordered contributions in
   `ComponentNode.render`, split the result into kwargs and client bindings, carry
   client bindings through `CitryElement`, and emit manifest-backed per-instance
   records. Direct, dynamic, and `c-bind` forms share one resolution contract.
2. **Boundary taxonomy:** only `x-props`, Alpine `@...` / `x-on:...`, and
   Citry `@c-*` client binding. All other HTML and Alpine attributes remain Python
   kwargs; the child explicitly places a declared `attrs` mapping.
3. **Registry and loading:** add a general dependency-runtime instance
   registry beneath optional Events anchors. With Events enabled, any emitted
   client binding or `$component` call loads the runtime; never regex-scan user code for
   a `props` declaration.
4. **Supply evaluation:** call module-local `Alpine.evaluateRaw` inside the
   effect, rooted at the physical parent, and add an explicit source facade.
   Require a synchronous plain-object result.
5. **Roots:** the first live root owns supply, while the logical instance owns
   all roots, props, `scope`, effects, and cleanup. Wrapper-only output inherits
   the client binding. The multi-root handler and stable live `ctx.els` mechanism is
   spike-proven, with real client binding/morph integration still to test. The rootless
   mechanism is also spike-proven subject to stable-anchor normalization,
   grouped mirrored ranges, contextual parsing, the nested-island guard, and
   preserved comments; real serialization, registry, and morph integration
   remain stage-two work.
6. **Handlers:** Alpine handler expressions and optional Citry argument
   expressions authored on a child component tag evaluate in the exact parent
   source scope. The child root supplies only `$el`, `$dispatch`, and `$event`;
   native `currentTarget` remains untouched. Citry `@c-*` additionally carries
   a parsed server-handler name and dispatches through the source parent Events
   anchor. `:c-*` remains invalid on component tags.
7. **Dynamic target:** transparent `<c-component>` forwards client bindings separately
   from kwargs to the actual selected target and never becomes their client
   identity.
8. **Non-Citry error:** reject statically on plain template elements and by
   exact instance-registry membership for dynamic/manual DOM. Defer "class
   declares no props" until class registration is definitive.
9. **Direct x-for substrate:** keep the `_x_refreshXForScope` canary. Public
   wrapper-free support requires a named client-target helper with fresh clone
   identities; never clone server Citry IDs as the implementation.
10. **Init ordering and expression settlement:** emit parent-call edges plus
    `expectsSupply` and release through an ancestry DAG. Independent branches
    proceed; first-supply expression failures settle their branch, while later
    failures clear and may recover.
11. **Managed helpers:** expose `effect` and `reactive`, no `release` member.
    `effect` returns an idempotent stop and auto-disposes through module-local
    Alpine before user cleanup.
12. **Alpine exposure:** add one stable reactive `scope` context member shared
    by all roots, reserve init's return for cleanup, and do not mutate `data`,
    user `x-data`, or add a Vue-style refs layer.
13. **Unknown keys:** section 8 ignores and reports each unknown own enumerable
    key per instance/key episode, applies valid siblings, and adds no
    framework strictness setting.
14. **Defaults:** section 9 requires object/array factories called once per
    logical instance and reuses that result for the instance lifetime without
    cloning or deep-freezing supplied values.
15. **Boundary-handler isolation:** component-target Alpine handler
    expressions and optional Citry argument expressions use ordinary data,
    `$data`, `$root`, `$id`, `$refs`, and other lexical magics from the exact
    authored source location at delivery. The physical child root owns only
    `$el`, `$dispatch`, and `$event`. Native `event.currentTarget` remains
    untouched. A handler authored inside the child template keeps the child
    scope.

Still pending maintainer review:

16. **Invalid updates:** section 7 recommends clearing the resolved prop to
    `undefined`, applying valid siblings, logging a deduplicated direct error,
    and recovering on the next valid update.

## Falsifiers

- **F1, client binding transport:** if a manifest client binding cannot force dependency
  emission for a target with no assets, the proposed carrier is incomplete;
  do not fall back to raw attributes.
- **F2, shared-root scope:** if the explicit `sourceId` facade cannot make a
  wrapper's `$state` and exposed `scope` resolve while its child is the
  innermost physical instance, parent evaluation is not solved.
- **F3, boundary-handler isolation:** for either Alpine or Citry component-tag
  handler, if a child-only ordinary name or ref is visible, or a colliding
  child value wins, the boundary leaked. Parent ordinary data, `$data`,
  `$root`, `$id`, and `$refs` must resolve at the exact authored source
  location. Conversely, `$el`, `$dispatch`, and `$event` must come from the
  real triggering child root. Native `$event.currentTarget` must remain
  untouched: root, `window`, `document`, and delayed `null` are all valid
  according to listener mode and delivery timing.
- **F4, first-root election:** if stage-two instrumentation observes more than
  one active supplier evaluation per target, or removing the elected root
  fails to activate the next live carrier immediately, the carrier election
  is wrong.
- **F5, grouped handlers:** the isolated `RootGroup` spike passed Alpine
  modifier ordering, union containment, shared timing/lifetime, dynamic roots,
  and native DOM event values across the browser matrix. The same observations
  remain stage-two acceptance falsifiers for real client binding and morph integration.
  Use a pointed error only for a concrete unsupported case. Independently, a
  handler-only target must work without waiting for a nonexistent component
  registration.
- **F6, x-for identity:** if a proposed test demonstrates wrapper-free support
  by cloning `data-cid-*`, the test is invalid. It must show fresh client
  registry identities and a parser-recognizable client-target marker, or the
  public claim is falsified.
- **F7, private Alpine:** if any pinned-version canary loses
  `_x_refreshXForScope`, the loop-scope integration must be redesigned before
  upgrading Alpine.
- **F8, DAG cost:** if emitted parent-call edges cannot survive fragment
  dedupe or keyed linking, use explicit ancestor lists; do not reconstruct
  ancestry from shared-root DOM. If any first-supply syntax, runtime, shape,
  or validation failure leaves a descendant waiting, failure settlement is
  incomplete.
- **F9, scheduler isolation:** if an invalid prop followed by a throwing
  managed effect prevents an unrelated effect from running, managed callback
  isolation is insufficient and must be fixed before shipping clear-to-
  `undefined`.
- **F10, DOM clearing:** if the full Events bundle behaves differently from
  the pinned-Alpine harness and `x-text` retains or renders `"undefined"`, the
  chosen invalid representation is not public-contract safe.
- **F11, partial updates:** if applying valid siblings while clearing invalid
  ones produces inconsistent real component snapshots, make one supplier
  evaluation atomic and clear every supplied declared key for that run.
- **F12, open-ended props:** if real components require arbitrary keys through
  `x-props`, add an explicit declaration-level rest contract; that evidence
  falsifies the no-rest surface, not the framework-wide rejection default.
- **F13, exposure timing and identity:** if an expression directive can
  evaluate before a supplied component's init populates `scope`, the
  x-props-before-data directive priority or init gate is incomplete. If
  reversed manifest order attaches an outer shared-root scope, fixed-marker
  innermost selection is incomplete.
- **F14, cleanup:** if `Alpine.release` still permits one queued callback after
  the active guard is false, the helper must remove/deactivate scheduler jobs
  another way before claiming teardown safety.
- **F15, runtime loading:** if injecting the Events runtime for every client binding or
  `$component` call is an unacceptable measured cost, the structured asset
  pipeline must emit a reliable class capability bit. A regex search for a
  `props` token is not an acceptable fallback.
- **F16, expression recovery:** if a post-init expression failure can leave
  any previously resolved prop in the bag, clearing is incomplete; if a later
  valid object does not repaint, recovery is incomplete.
- **F17, optional omission:** if omitting an optional prop constructs a new
  default object, retains its last supplied value, or falls through to a
  class-level reference, the per-instance default table is not being used.
- **F18, client binding resolution:** if exact-key replacement/removal differs between
  direct, dynamic, and `c-bind` contributions, or an invalid spread value loses
  its spread span and mapping key, the post-resolution split is incomplete. A
  winning replacement must also occupy its winning source position.
- **F19, Citry event ownership:** if a component-tag `@c-*` binding dispatch selects the
  child's nearest anchor, resolves missing names from child `x-data`, or forges
  `event.currentTarget`, the logical-source and physical-target split failed.
- **F20, dynamic target:** if a dynamic `<c-component>` client binding registers against
  the transparent built-in rather than the selected child, or replacement
  cleans a client binding more or less than once, transparent forwarding failed.
- **F21, rootless lifetime:** if comment ranges cannot survive contextual HTML,
  nested/adjacent ranges, morph transitions, and removal with exact cleanup,
  rootless client activity remains unsupported in v1. The 2026-07-19 spike
  passed this falsifier only with contextual parsing, the nested-island guard,
  pre-morph stable-anchor normalization, grouped mirrored regions, and
  preserved Citry comments; omitting any required adapter is still a failure.
- **F22, live roots:** if partial root replacement leaves `ctx.els` stale while
  the instance survives, use a stable updated array or getter before claiming
  that `els` represents the logical instance's current roots.
- **F23, boundary-handler scope:** the focused spike had to lock the complete
  source-versus-carrier split for a whole Alpine handler expression and an
  optional Citry argument expression. The 2026-07-19 spike passed: evaluate
  those expressions at the exact source location, resolved at delivery, and
  override only `$el`, `$dispatch`, and `$event`; native `currentTarget`
  remains untouched. Child-only data and refs must not leak, source-root-first
  or component-union selection is wrong, parent assignment and explicit
  source-facade assignment must both write through. A handler authored locally
  inside the child must retain child scope. Citry handler parsing, validation,
  dispatch, and queue integration remain separate stage-two falsifiers.
