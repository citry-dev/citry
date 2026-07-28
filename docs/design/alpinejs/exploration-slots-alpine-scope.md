# Slot-fill Alpine scope: verified exploration

Status: redone 2026-07-19 against the real Citry server, pinned Alpine
3.15.12, pinned morph 3.15.12, the current Citry client runtime, and three
browser engines. This report replaces the unretained 2026-07-18 scratch
exploration. It is research, not a product implementation.

The earlier report is not a trustworthy source. Its opening example put
`$state` inside `{{ ... }}`, even though braces contain Python expressions.
It also made several claims that the retained source and new harnesses
disprove: an initial-load `interceptInit` stamp does not capture ancestor
`x-data`; a copied data stack does not move lexical Alpine magics; a marker
on a direct `x-if` or `x-for` template does not appear on the generated root;
synthetic event redispatch is lossy; an ancestor bubble listener cannot stop
the target listener that already ran; suppressing a nested component boundary
breaks isolation; and an unmarked child fallback can inherit the surrounding
parent fill scope.

This report calls `$c-props`, an Alpine handler such as `@click`, or a Citry
handler such as `@c-save` or `@c-poll.5s` on a nested `<c-*>` tag a
**component-tag client binding**. The parent owns the expression or server
handler, while the child supplies the component boundary where the browser
applies it. Later references shorten this to “client binding.”

## 1. Result

The intended ownership rule survives the redo, with more precise language:

1. Supplied fill markup belongs to the exact Alpine call-site scope outside
   the component receiving the slot.
2. The receiving component's fallback markup belongs to that child.
3. Every nested ownership transition must be preserved. A parent fill can
   invoke a child fallback inside itself, and a fill can contain another
   isolated component.
4. Lexical expression ownership is separate from physical DOM ownership.
   Ordinary names and lexical Alpine magics follow the logical source;
   `$el`, `$dispatch`, `$event`, native `target`, and native `currentTarget`
   remain physical.
5. Fill-local event handlers need no event redispatch. They run on the
   physical target with the original event while evaluating through the
   source scope. Native capture and bubbling continue through the physical
   DOM.

The old four-part mechanism is rejected. A checked-in split-phase prototype
does prove a viable Alpine primitive for initial scope linking, the tested
teleport and direct-template-root shapes, multi-root fills, and live source
re-election. It does not prove the complete scoped-fill product path. Shipping
that path still requires choosing and serializing a structural source,
transition, and optional range representation, then integrating it with the
already-designed general client-instance registry, Citry evaluator and
magics, queue ownership, the already-proven rootless and mirrored lifetime
mechanism, and the landed product morph path. These are a mixture of
representation decisions and integrated acceptance work, not seven separate
design explorations. The component-first architecture question should be
resolved before that representation is frozen; see
[`exploration-alpine-component-first.md`](exploration-alpine-component-first.md).

## 2. The corrected DX

`{{ ... }}` is Python. Alpine runtime state belongs in an Alpine directive:

```python
class Page(Component):
    template = """
      <c-tooltip>
        <button
          @click="$state.saves++"
          x-text="`saved ${$state.saves} times`"
        ></button>
      </c-tooltip>
    """


class Tooltip(Component):
    template = """
      <div x-data="{ open: false }"
           @mouseenter="open = true"
           @mouseleave="open = false">
        <template x-teleport="body">
          <div class="popup" x-show="open">
            <c-slot />
          </div>
        </template>
      </div>
    """
```

The button was supplied at `Page`'s `<c-tooltip>` call site. Its
`$state.saves` must therefore resolve to `Page`, not `Tooltip`, even after the
child teleports it. Its click handler receives the original click on the
physical button. This does not imply that the click has a synthetic logical
DOM path through `Page`.

"Vue-like" is useful only for the lexical render-scope rule. Vue documents
that slot expressions use the scope where the slot was defined. It does not
mean a child is absent from native event propagation, and it does not define
Citry's policy for Python-created slot values.

## 3. Evidence and reproduction

The retained evidence is:

- [`slots_scope_server_harness.py`](slots_scope_server_harness.py), which
  exercises Citry's real parser, slots, render tree, and serializer.
- [`slots_scope_adapter.js`](slots_scope_adapter.js), a research-only Alpine
  source-link prototype.
- [`slots_scope_scenarios.js`](slots_scope_scenarios.js), the browser cases.
- [`slots_scope_harness.py`](slots_scope_harness.py), which runs the cases
  three times each in Chromium 149.0.7827.55, Firefox 151.0, and WebKit 26.5
  through Playwright 1.61.0. Its second mode loads the actual Citry client
  bundle, not a second Alpine copy.

Run them from the repository root:

```console
uv run python docs/design/alpinejs/slots_scope_server_harness.py

uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
  python docs/design/alpinejs/slots_scope_harness.py

uv run pytest -q \
  packages/py/citry/tests/test_slot_fills.py \
  packages/py/citry/tests/test_slot_node.py \
  packages/py/citry/tests/test_slots.py \
  packages/py/citry/tests/test_component_dynamic.py
```

Observed for this redo:

```text
browser harness: 3 engines x 3 fresh pages, all assertions passed
server harness: all assertions passed
slot/dynamic-component suites: 168 passed
```

The browser prototype deliberately has positive cases and failing controls.
A positive prototype result proves the Alpine mechanism it exercises, not
that Citry already emits or consumes the required metadata.

## 4. Prior art and current implementation

Load-bearing prior work:

- [`../alpinejs.md`](../alpinejs.md) section 4.6 records the accepted
  call-site ownership contract that this report stress-tested.
- [`exploration-x-props-round-2.md`](exploration-x-props-round-2.md) separates
  parent-authored boundary behavior from child-local template behavior.
- [`spike-citry-handler-refs.md`](spike-citry-handler-refs.md) proves why an
  exact source location matters for `$refs`, `$root`, `$id`, and multi-root
  sources.
- [`spike-root-group.md`](spike-root-group.md) proves grouped native listener
  semantics while preserving the original event and physical carrier.
- [`spike-rootless-lifecycle.md`](spike-rootless-lifecycle.md) proves
  comment-owned range lifetime and why an initialized root must not be
  destructively restamped after a move.
- [`../component_slots.md`](../component_slots.md) defines the server closure and fallback model.

Pinned Alpine facts:

- `initTree` walks the tree and runs all init interceptors while directive
  handlers are deferred
  ([`lifecycle.js:90-113`](../../../packages/js/citry-client/node_modules/alpinejs/src/lifecycle.js#L90),
  [`directives.js:79-103`](../../../packages/js/citry-client/node_modules/alpinejs/src/directives.js#L79)).
- `x-ref` registers through an inline handler during that walk
  ([`x-ref.js:4-18`](../../../packages/js/citry-client/node_modules/alpinejs/src/directives/x-ref.js#L4)).
- `x-data` evaluates later and prepends its reactive layer
  ([`x-data.js:13-42`](../../../packages/js/citry-client/node_modules/alpinejs/src/directives/x-data.js#L13)).
- Directive priority is `ref`, `id`, `data`, then the remaining groups unless
  a custom directive inserts itself earlier
  ([`directives.js:204-228`](../../../packages/js/citry-client/node_modules/alpinejs/src/directives.js#L204)).
- `addScopeToNode` replaces `_x_dataStack` with a new leading layer and the
  chosen reference stack
  ([`scope.js:6-11`](../../../packages/js/citry-client/node_modules/alpinejs/src/scope.js#L6)).
- Alpine root lookup follows `_x_teleportBack`
  ([`lifecycle.js:56-77`](../../../packages/js/citry-client/node_modules/alpinejs/src/lifecycle.js#L56)).
- `x-if` and `x-for` clone the template's first element and seed its stack
  from the template, not its attributes
  ([`x-if.js:14-25`](../../../packages/js/citry-client/node_modules/alpinejs/src/directives/x-if.js#L14),
  [`x-for.js:114-128`](../../../packages/js/citry-client/node_modules/alpinejs/src/directives/x-for.js#L114)).
- `x-teleport` uses a backlink, a data-stack link, and narrow opt-in event
  redispatch for event names declared on the source template
  ([`x-teleport.js:13-54`](../../../packages/js/citry-client/node_modules/alpinejs/src/directives/x-teleport.js#L13)).

Current Citry facts:

- The current client attaches an isolation boundary only when a `data-cid`
  root belongs to an Events-manifest instance
  ([`citry-events.ts:732-758`](../../../packages/js/citry-client/src/citry-events.ts#L732),
  [`citry-events.ts:1053-1076`](../../../packages/js/citry-client/src/citry-events.ts#L1053)).
  Universal one-boundary-per-component behavior belongs to the planned
  general registry, not the landed runtime.
- Citry magics still choose the innermost physical `data-cid`
  ([`citry-events.ts:1132-1164`](../../../packages/js/citry-client/src/citry-events.ts#L1132)).
- Compiled Citry bindings, public `send(element)`, and queue overlap do not
  all have the same contract
  ([`citry-events.ts:1983-2018`](../../../packages/js/citry-client/src/citry-events.ts#L1983),
  [`citry-events.ts:2417-2431`](../../../packages/js/citry-client/src/citry-events.ts#L2417),
  [`citry-events.ts:4659-4695`](../../../packages/js/citry-client/src/citry-events.ts#L4659)).

## 5. Server findings

### 5.1 Python interpolation and Alpine attributes are distinct

The server harness parses the exact bad example and gets a `SyntaxError` at
`$`. The corrected `x-text="`saved ${$state.saves} times`"` survives as an
ordinary HTML attribute. The parser is behaving correctly; the old report's
example was not.

### 5.2 Template fills already retain the correct Python owner

`_make_body_slot` closes over the writer's `CitryContext` and returns a
`CitryRender` with that context
([`nodes/__init__.py:209-268`](../../../packages/py/citry/citry/nodes/__init__.py#L209)).
Fallback creates the same kind of closure over the receiving child's current
context
([`nodes/__init__.py:1120-1200`](../../../packages/py/citry/citry/nodes/__init__.py#L1120)).

The harness observed an inline fill supplied by `Page` to `Box` as:

```text
CitryRender owner: Page
Slot.component_name: "box"
Slot.source_position: present
```

`Slot.component_name` is receiver-oriented debug metadata, not the lexical
owner. The code says so at
[`slots.py:150-157`](../../../packages/py/citry/citry/slots.py#L150).

### 5.3 Plain Python strings are not active HTML

Slot normalization escapes ordinary strings at construction
([`slots.py:227-250`](../../../packages/py/citry/citry/slots.py#L227)). The
harness observed:

```html
<div>&lt;button x-text=&#34;bad&#34;&gt;&lt;/button&gt;</div>
```

Active programmatic HTML requires a trusted `SafeString`, a callable that
returns trusted/renderable output, a `CitryElement`, or a `CitryRender`. The
old report's "Python string element root" origin does not exist for a plain
string.

### 5.4 Construction origin is not a browser source location

A reusable `Slot(SafeString(...))` was rendered under two different `x-data`
locations, A and B. It produced two active copies, but the Slot had no source
position and the final HTML had no provenance. The two copies must later use
A and B respectively. Therefore:

- where a Python object was constructed is not the lexical Alpine source;
- the source policy must attach at each actual component or slot-supply call
  site;
- one reusable Slot may produce several independent source descriptors.

Existing Slot metadata cannot identify those live locations. Normalization
preserves optional caller-provided metadata and does not mint invocation
identity
([`slots.py:266-312`](../../../packages/py/citry/citry/slots.py#L266)).

Typed slot defaults and directly composed root components may have no outside
component call site at all. Their client-scope policy remains an explicit
open decision.

### 5.5 Fallback can form a child-owned island inside a parent fill

This legal template:

```html
<c-card>
  <c-fill name="x" fallback="fb">
    <b x-text="parent">{{ fb }}</b>
  </c-fill>
</c-card>
```

with child fallback:

```html
<c-slot name="x"><i x-text="child"></i></c-slot>
```

produced this unflattened render tree:

```text
CitryRender(Page)
└── CitryRender(Card)
```

and, with generated component-id attributes omitted for readability, this
final HTML:

```html
<b x-text="parent"><i x-text="child"></i></b>
```

The real outer `<b>` carries the ordinary stacked Page/Card component-root
markers. The nested `<i>` carries no ownership-transition marker. Component
markers alone therefore cannot recover the alternating slot ownership.

If Citry marks only the outer `<b>` as parent-owned and emits no inverse
boundary for fallback, the `<i>` inherits the parent link. "Never mark
fallback" is therefore wrong. The serializer must preserve every nested
render ownership transition, including fallback and passthrough transitions.

### 5.6 Serialization currently discards slot provenance

`CitryRender` has parts, context, and `is_component_root`; `DeferredComponent`
has element, parent, and provides. Neither carries a rendered slot invocation
or source token
([`citry_render.py:99-130`](../../../packages/py/citry/citry/citry_render.py#L99),
[`citry_render.py:215-251`](../../../packages/py/citry/citry/citry_render.py#L215)).

The serializer marks component root frames and flattens interior renders
([`serialize.py:100-140`](../../../packages/py/citry/citry/serialize.py#L100),
[`serialize.py:226-280`](../../../packages/py/citry/citry/serialize.py#L226)).
It emits no fill range, source comment, scope transition, or invocation token.

After omitting generated component-id attributes, the harness confirms the
missing shape for multi-root, text-only, and empty fills:

```text
multi-root: <span>A</span>text<b>B</b>
text-only:  plain text
empty:      ""
```

There is no logical fill group in browser output today.

## 6. Client baseline and the failed old mechanism

### 6.1 Default behavior under an isolated child

An ordinary fill physically nested inside an interactive child reaches the
child's truncated data stack. Current Citry magics independently find the
child through the nearest `data-cid`. Those are separate resolution paths.

The real-runtime harness linked ordinary Alpine scope to the source but did
not modify Citry's closure-private magic resolver. It observed:

```text
ordinary Alpine owner: parent-alpine
$refs/$root source:    parent
$state.owner:          child-state
```

This is direct evidence that Alpine source linking does not solve Citry
logical ownership. `$state`, `$loading`, `$error`, `$sendEvent`, `$onEvent`,
and a compiled `@c-*` binding's optional argument evaluation and server
dispatch need an explicit source record in their respective evaluation and
send paths.

### 6.2 Why the interceptor stamp fails

The old proposal called:

```js
Alpine.addScopeToNode(fillRoot, {}, sourceComment)
```

inside `interceptInit`.

On initial `Alpine.start()`, the source ancestor's `x-data` handler has only
been queued when the nested fill interceptor runs. The populated comment
registry therefore points at an ancestor whose reactive data does not exist
yet. The retained negative control rendered `missing` and captured an empty
source layer. A registry scan cannot repair this ordering.

Teleport can conceal the bug: the `x-teleport` directive itself runs after
ancestor `x-data`, then initializes its relocated clone. Success in that path
does not prove the nested initial-load path.

### 6.3 Why a copied stack is incomplete

`addScopeToNode` changes ordinary data lookup. Alpine injects magics from the
physical evaluation element, and `$refs`, `$root`, `$id`, and `x-ref`
registration walk Alpine roots from that element. A comment is sufficient as
a `closestDataStack` reference, but it is not a complete evaluation carrier:
`closestRoot` calls `matches()` while traversing Elements.

The full equivalence target is "as if this authored fill element occurred at
the source call site":

| Surface | Required owner |
|---|---|
| ordinary names and writes | source call-site stack, plus fill-local layers |
| `$data` | the same composed stack |
| `$refs` and `x-ref` | fill-local roots first, then source root; never the receiving child wrapper |
| `$root` | normal Alpine result at the logical source; a fill's own `x-data` remains its own root |
| `$id` and `x-id` | normal nearest logical ID root |
| `$el`, `$dispatch` | physical fill element |
| `$event`, `target`, `currentTarget` | original physical event values |
| Citry magics and an authored `@c-*` binding's optional argument expression | exact live Citry source anchor |
| authored `@c-*` server-handler validation, dispatch, and queue | exact live Citry source anchor; the handler name is not evaluated |
| queue containment | source send owner plus physical overlap, not one substituted for the other |

## 7. The split-phase Alpine prototype

The browser harness tests a research-only `x-cfill` directive. This name and
wire format are not a product recommendation.

### 7.1 Phase 1: link lexical root traversal inline

The directive is ordered before `x-ref`. Its `inline` hook runs during
Alpine's tree walk and elects:

- a durable source comment for identity; and
- that comment's parent Element as the Alpine magic carrier.

For an ordinary fill root, it installs a teleport-like `_x_teleportBack` to
the source Element before `x-ref` registers. For a fill root already created
by one or more native `x-teleport` directives, it walks the complete valid
reverse-link chain, preserves every clone-to-template backlink, and adds the
Citry backlink at the terminal native source template. The resulting chain is
fill clone to each native template to logical source, rather than a shortcut
that flattens Alpine's teleport ancestry. Alpine's existing `findClosest` can
then skip the receiving child wrapper while keeping the physical fill element
for `$el` and events.

### 7.2 Phase 2: install data after source `x-data`, before fill `x-data`

The directive's deferred body is encountered after earlier source ancestors
in tree order, but sorted before the fill root's `x-id` and `x-data`. At flush:

1. source ancestor `x-id` and `x-data` have run;
2. the fill source frame is installed;
3. the fill root's own `x-id` and `x-data` run above it;
4. `x-init`, `x-text`, and listeners evaluate against the result.

The prototype uses a live proxy frame keyed to a source descriptor instead
of copying the source's current stack objects. A source re-election increments
a reactive version, retargets backlinks, and invalidates `$refs`/`$id` caches
for the linked roots.

When an `x-if` or `x-for` clone already inherited that exact frame, the
directive retains the clone's complete stack instead of adding the frame
again. This is load-bearing for `x-for` iteration variables and any local
layers above the source.

Across all three engines the ordinary case proved:

- source reads and writes;
- no receiving-child-only names;
- `$data` source ownership;
- source `$refs`, `$root`, and `$id`;
- source-owned `x-ref` registration;
- fill-local `x-data` shadowing above the source;
- physical `$el`;
- two-way reactive writes into the source.

This is a promising primitive, not a final product mechanism. It depends on
private Alpine fields and needs canaries with the exact dependency pin.

### 7.3 Direct `x-if` and `x-for` template roots

The old report said the attribute marker automatically survives these
clones. It does not. Alpine clones `template.content.firstElementChild`, so a
marker on the template is absent from the generated root.

The first prototype tried to recover the source by scanning inherited stacks
in an init interceptor. An adversarial case disproved it: descendants also
inherit that stack, so the interceptor linked each descendant directly to the
source and bypassed intervening fill-local `x-data`, `x-id`, and `x-ref`
ownership. Checking only for an element's own seeded stack still misclassifies
nested structural clones.

The corrected prototype explicitly copies the research `x-cfill` directive
from the structural template to `template.content.firstElementChild` before
Alpine clones it. Only the actual generated fill root receives the directive.
Alpine's normal clone stack retains the loop frame and the already installed
source frame, so the generated directive adds only the lexical backlink and
does not destructively replace that stack.

The harness proved for both directives:

- generated roots received the explicitly propagated `x-cfill` marker;
- fill-local `x-data`, `$root`, `$id`, and `x-ref` ownership remained local;
- source-only ordinary data and source refs remained visible below that local
  root;
- descendants, nested `x-if` clones, and late-initialized descendants did not
  receive a direct source backlink;
- `x-for` iteration variables remained visible; and
- `x-if` removal and recreation produced a fresh correctly linked root.

That answers the narrow direct-template-root problem. It does not solve
general cloned Citry component identity.

### 7.4 Client `x-for` call sites

When a whole component invocation is cloned by client `x-for`, its source
comment token is cloned too. A global token-to-one-comment registry is
ambiguous. The prototype paired each nested fill with its nearest preceding
matching source comment and correctly obtained iteration values A and B in
all engines.

This proves only a possible scope-location pairing rule for a connected,
non-relocated fixture. It does not solve:

- a fill teleported before positional pairing;
- nested or crossed range ambiguity;
- cloned server `data-cid` values;
- fresh Citry component instances, manifests, anchors, queues, and cleanup.

The named client identity prerequisite from the x-props exploration remains.
Changing a source marker alone cannot turn cloned server DOM into independent
Citry instances.

### 7.5 Teleport

The child teleported a marked fill root to a separate destination. A second
case put `x-cfill` and `x-teleport` on the same source template and gave its
generated element a fill-local `x-data`, `x-id`, and refs. A third case nested
two native teleports before the marked fill. The prototype preserved:

- the parent ordinary scope;
- parent `$refs`, `$root`, and `x-ref` ownership;
- no child-only names;
- Alpine's full fill-to-inner-template-to-outer-template backlink chain;
- the fill-local root, ID, and refs ahead of the parent source, without
  registering those local refs on the parent; and
- the original event, physical target, and physical `$el`.

The fill-local target handler ran in the source scope. Native bubbling did
not visit the source or child because the destination was outside both.
Lexical relocation and native event propagation are therefore separate
problems, even though the same source descriptor can support lexical lookup.

### 7.6 Multi-root, morph, restamp, and source replacement

Two ordinary fill roots shared one source descriptor. Each retained its own
physical `$el`, and writes from both updated one source state. Text between
them had no Alpine directives and needed no element wrapper.

A same-shape Alpine morph retained the live fill element, fill-local `x-data`,
and source layer. A deliberate blanket restamp reduced a two-layer local plus
source stack to one source layer and made the local name disappear. Therefore:

- adopt new roots before their directives initialize;
- retain initialized roots without restamping;
- re-elect the descriptor for a changed source;
- do not rebuild an initialized element's whole stack after movement.

The prototype also removed an old source root while a linked fill remained,
inserted a new source with the same logical token, and explicitly re-elected
it. Ordinary data, source `$refs`, `$root`, and text moved from the old source
to the new one. This proves the live-facade direction. It does not yet prove
fill-authored `x-ref` migration, mirrored copies, delayed handlers, or product
morph ownership.

## 8. Events: corrected semantics

### 8.1 A fill-local handler already runs before a child bubble stop

The retained native-event case delivered one original event in this order:

```text
source capture
child capture
fill target handler
child bubble stop
component-boundary listener on the same child root
```

The outer source bubble listener did not run. The fill target handler did run
and updated source state. `stopPropagation()` on the child cannot retroactively
prevent the target listener. It also does not prevent other listeners on the
same child node; that would require `stopImmediatePropagation()`.

This is the correct isolation model for fill-local expressions:

- child state is not visible to the expression;
- the child DOM remains part of the native event path.

Those are not contradictory.

### 8.2 Generic stop-and-redispatch is rejected

The harness implemented the old proposal exactly: stop the original at the
fill and dispatch `new e.constructor(e.type, e)` from the source comment. It
observed:

- document capture saw both the original and the synthetic event;
- child capture saw the original before forwarding;
- the child-root component-boundary bubble listener lost the event;
- the synthetic target was `#comment`;
- the synthetic path omitted the fill and child;
- the synthetic event was a different object and untrusted;
- preventing the synthetic event did not set `defaultPrevented` on the
  original dispatch.

The same design is also incompatible with document-delegated Citry bindings:
stopping the original before document prevents the binding listener from
seeing its annotated element, while the synthetic comment has no binding.

Alpine teleport's narrow forwarding is useful source code to understand, not
proof of a faithful general logical DOM. Generic slot event forwarding is not
part of the recommendation.

### 8.3 Component-tag handlers and teleported descendants

An Alpine or Citry handler authored on `<c-child>` is a component-tag client
binding owned by the parent and physically attached through the child's
`RootGroup`. For a nested fill event, the original native event normally
reaches that group. Synthetic fill forwarding would incorrectly suppress it.

A teleported fill outside the child roots is different: native propagation
does not reach the child's RootGroup or the source ancestor. The product must
state separately whether:

1. only handlers authored directly on the teleported fill are guaranteed; or
2. component-tag or outer ancestor listeners also need a logical propagation
   abstraction.

Option 2 is a new event-system feature. It cannot reuse the rejected generic
redispatch while claiming native parity.

## 9. Nested components and nested ownership

### 9.1 A component inside a fill remains isolated

The harness put an isolated component inside an ordinary source-linked fill.
Its own template saw its child-local data and no parent-only name. A naive
deep-descendant `closest('[data-cfill]')` search still found the outer fill
mark, demonstrating why marker lookup must stop or arbitrate at nested
component frames.

### 9.2 Marking the nested component root leaks the parent

The negative control marked the nested component root as an ordinary fill
root. Its local `owner` shadowed the source value, which can make the result
look correct, but a parent-only name remained visible underneath. Suppressing
the child boundary has the same leak.

The correct structural rule is:

- ordinary HTML authored directly in the fill gets the fill source link;
- a nested component invocation starts a new isolated component frame;
- parent-authored props and Alpine/Citry component-tag handlers cross that
  frame through the x-props client binding;
- child-template directives remain child-local.

One physical root can represent both a nested component and its parent-authored
client bindings. That requires multiple logical records, not one
last-write-wins `_x_dataStack`.

### 9.3 Fallback needs the inverse transition

The browser harness mirrored the server's parent-fill-with-child-fallback
tree. With an explicit child source transition, the outer element saw
`fallback-parent` and the nested fallback saw `fallback-child`. The unmarked
fallback control saw `fallback-parent`.

This is the decisive reason to serialize ownership transitions from the
unflattened render tree rather than merely decorate each outer fill root.

## 10. Citry ownership and queue semantics

Fill-authored Citry expressions and server-handler bindings need the same
exact source descriptor, but not a blanket rewrite of every element-based
resolver.

The required split is:

1. **Expression owner:** `$state`, `$loading`, `$error`, `$sendEvent`,
   `$onEvent`, and an `@c-*` binding's optional argument expression use the
   exact live source anchor recorded for the authored fill segment.
2. **Server binding owner:** the parsed `@c-*` handler name is validated,
   dispatched, and queued through that same source anchor; Citry does not
   evaluate the handler name as client code.
3. **Physical dispatch element:** the actual fill element remains available
   for event fields, busy state, forms, and containment.
4. **Queue overlap:** a source-owned send physically inside a child should
   include the source anchor and the physically overlapping child anchors.
   `relatedAnchorsOf` gathers a set; replacing the child with the source would
   lose information.
5. **Public `Citry.events.send(element)`:** this currently means nearest
   physical instance. Changing it merely because an element lies inside a
   fill is a separate public API decision, not an automatic consequence of
   authored scope ownership.

The source descriptor should be an explicit evaluator/send input for
compiler-authored fill expressions. Global DOM-walk inversion is too broad.

## 11. Fill origins and the source policy

The old phrase "where it was written" is only precise for template fills.
The client policy should use the actual supply call site outside the receiver:

| Origin | What the server currently knows | Client source policy |
|---|---|---|
| inline implicit or named template fill | writer `CitryContext`, static source span | exact rendered component invocation call site |
| child fallback | receiving child's current context and slot site | exact child slot-site scope |
| plain Python string | escaped text, no active HTML | no Alpine element work |
| trusted Python HTML or callable result | active output, normally no lexical DOM position | the actual component/slot supply call site |
| reusable Python `Slot` | optional debug metadata, reusable across calls | a fresh descriptor per invocation, never construction location |
| `CitryElement` or `CitryRender` in a slot | component/render context, but no slot call-site identity | slot call-site transition outside; nested component template stays isolated |
| typed default or root-level direct composition | potentially no outside component owner | open policy; must be explicit |
| dynamic `<c-component>` | transparent wrapper can disappear; target parent links are not source identity | source descriptor belongs to the dynamic invocation call site |

The final DOM may intentionally be origin-blind. The render pipeline is not:
template fills and fallbacks retain distinct contexts until serialization.
Citry should preserve the structural ownership it already knows and add
invocation identity where Python-origin content lacks it.

## 12. Old-report claim ledger

| Old claim | Verified result |
|---|---|
| `{{ $state.saves }}` is valid | Rejected. It is invalid Python expression syntax. |
| every Python string can be an active fill root | Rejected. Plain strings are escaped. |
| fill content uses scope outside the receiver | Retained, renamed exact call-site ownership. |
| fallback is child-owned | Retained, but nested fallback needs an explicit inverse boundary. |
| `interceptInit` closes the first-paint race | Rejected for initial nested fills. Source `x-data` has not run. |
| registry population is the only ordering issue | Rejected. Registry readiness and source-scope readiness are different. |
| a comment is a complete evaluation carrier | Rejected. It can reference a data stack but is not an Element for root traversal. |
| `addScopeToNode` provides complete source scope | Rejected. It does not by itself move lexical magics or `x-ref` ownership. |
| an attribute survives `cloneNode` | Retained when the marked node itself is cloned. |
| a direct marked `x-if`/`x-for` template automatically transfers its mark | Rejected. The generated first element has no template attribute. |
| direct template roots are unsalvageable | Rejected. Explicitly propagating the directive to the template-content root worked in all engines without linking nested clones. |
| client `x-for` needs only one static token | Rejected. Clones need physical source disambiguation and full Citry identity. |
| nested and teleported fill scope can share a source abstraction | Retained for lexical scope. |
| nested and teleported native events are the same problem | Rejected. Their physical paths differ. |
| child bubble stop prevents the fill target handler | Rejected by native event order. |
| generic synthetic redispatch faithfully reaches the parent | Rejected by target, path, capture, cancellation, delegation, and RootGroup controls. |
| component-tag handlers are unrelated | Rejected. They are parent-owned RootGroup DOM client bindings. |
| all four Citry element consumers should redirect | Rejected. Logical owner, public target selection, and physical overlap differ. |
| suppress the boundary when fill root equals component root | Rejected. It leaks source names into child-local template scope. |
| mark only outer fill roots | Rejected by nested fallback and nested component transitions. |
| restamp every render path | Rejected. It erases fill-local scope layers. |
| same-node morph can retain the source link | Supported for the tested same-shape case. |
| multi-root ordinary data can share one source | Supported; logical range lifetime still needs integration. |
| both scenarios are implementation-ready v1 work | Rejected as a research conclusion. Scheduling is a product-plan decision. |

## 13. Recommended architecture to take forward

### 13.1 Server

1. Preserve scope ownership as a structural render concept until final
   serialization. Do not infer it from flattened HTML afterward.
2. Mint a fresh logical source descriptor at each actual component or slot
   supply invocation.
3. Encode every transition: parent fill, nested child fallback, passthrough,
   nested component, dynamic component, and extension replacement.
4. When a fill is client-active or must retain identity across shape
   transitions, represent its logical region independently from its element
   roots. Keep whether inert text-only and empty fills need range caps open;
   the rootless spike did not prove that every fill should pay that cost.
5. Never decorate a nested component's rendered root as ordinary parent fill
   HTML. Record parent-authored client bindings separately.

This will require changing render/serialization metadata. Whether it can stay
inside Python or touches the Rust HTML marker contract must be decided only
after walking the actual proposed representation through `mark_html` and all
bindings.

### 13.2 Client registry and adoption

1. Integrate source descriptors with the planned general component registry,
   not the Events-only index.
2. Adopt source records and any emitted logical fill ranges before arriving
   Alpine directives initialize.
3. Use a split phase or an equivalent evaluator design:
   - early lexical backlink before inline directives such as `x-ref`;
   - source data availability after ancestor `x-data` but before fill-local
     `x-id`/`x-data` and expressions.
4. Carry a private source frame through Alpine-created template clones.
5. Re-elect live source carriers without destructively replacing initialized
   root stacks.
6. Any source or range identity represented by comments must be preserved in
   deployment, with pointed failure and exact cleanup if it disappears.
   Whether every fill receives range comments remains an open serialization
   policy.

The prototype's `_x_teleportBack` plus live frame is one candidate. A global
source-aware evaluator with explicit physical magic overrides is another.
The latter could avoid mutating Alpine root traversal globally, but it must
still solve inline `x-ref` registration and ordinary directive evaluation.

### 13.3 Citry expressions and events

1. Feed compiler-authored fill expressions an explicit source descriptor.
2. Keep source anchor and physical element as separate fields through sends
   and queue construction.
3. Keep the original native event and physical propagation.
4. Reuse x-props client bindings when the fill content itself is a nested
   component invocation.
5. Do not add generic fill event redispatch.

### 13.4 Multi-root and rootless lifetime

Reuse the proved mechanisms, not their names alone:

- RootGroup-style stable live element membership where one logical binding
  targets several roots.
- Rootless comment ranges for client-active text/empty output or shape
  transitions. Whether inert fills need caps remains open.
- One shared source descriptor across the fill's live roots or physical
  regions.
- Cleanup once when the last physical region dies, not when one root moves or
  disappears.

## 14. Remaining falsifiers before product build

The split-phase Alpine primitive passed its isolated matrix. Product work is
not ready until an integrated spike or implementation proves:

1. **Serialization provenance:** template fill, implicit fill, trusted Python
   HTML, callable, reusable Slot at two call sites, `{{ slot }}`, fallback
   inside fill, nested passthrough, typed default, `CitryElement`,
   `CitryRender`, dynamic `<c-component>`, extension replacement, repeated
   slot sites, multi-root, text, empty, and mirrored output.
2. **General boundaries:** components with and without Events, shared physical
   roots, multi-root children, rootless children, and wrapper-only nested
   components.
3. **Alpine completeness:** ordinary data, writes, `$data`, `$refs`, `$root`,
   `$id`, `x-ref`, fill-local `x-data`, source replacement, ref replacement,
   template roots, teleport, shadow DOM, and comment stripping.
4. **Citry completeness:** all five magics, compiled `@c-*`, declared-event
   failure behavior, forms, physical overlap, dequeue re-verification, busy
   state, and public `send(element)` semantics.
5. **Lifecycle:** initial parse, head-loaded runtime, late fragment, same-node
   morph, replaced source, replaced fill roots, moves, non-morph swaps,
   mirrored outlets, root-count changes, and exact once-only cleanup.
6. **Client loops:** unique complete component identity for every client
   clone, plus source pairing under nested and teleported shapes.
7. **Event decision:** an explicit acceptance answer for whether outer or
   component-tag listeners must observe teleported fill events. If logical
   propagation is desired, it needs a separate event-system design and
   cannot claim native equivalence.

## 15. Final recommendation

Carry these conclusions into the Alpine source of truth:

- Scoped slot ownership is exact-call-site ownership, with child-owned
  fallback and nested structural transitions.
- Alpine lexical ownership and physical DOM/event ownership are separate.
- The old interceptor stamp, stack-only scope, blanket resolver redirect,
  synthetic event bridge, component-boundary suppression, and blanket
  restamping are rejected.
- The split-phase backlink plus source-frame prototype is credible prior art
  for the Alpine portion, including the tested direct-template-root and
  teleport shapes.
- Product design must start at the unflattened render tree and the general
  registry, then carry explicit logical source plus physical element through
  Citry evaluation and queueing.
- Rootless, mirrored, client-cloned, and teleported-listener semantics remain
  explicit gates, not implied successes.

No runtime implementation is authorized or included by this spike.
