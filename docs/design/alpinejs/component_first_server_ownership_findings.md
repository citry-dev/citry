# Component-first server ownership spike

Status: research-only server spike, run on 2026-07-20 against the real Citry
parser, Python render objects, deferred renderer, slot implementation, and
serializer. It changes no production source and makes no decision about which
fills should receive client-visible range markers.

Implementation status: this report preserves the evidence available before
A1. A1 subsequently landed the production ownership graph described in
[`a1_server_ownership.md`](a1_server_ownership.md). In particular, production
code now forwards one call identity through dynamic `<c-component>` and gives
Python-provided slots an explicit detached-source policy. The harness still
reports those former gaps because it remains a record of the research
prototype, not a second implementation of A1.

The executable artifact is
[`component_first_server_ownership_harness.py`](component_first_server_ownership_harness.py).
Run it from the repository root:

```console
uv run python docs/design/alpinejs/component_first_server_ownership_harness.py
uv run python docs/design/alpinejs/component_first_server_ownership_harness.py --full
```

The first command prints a compact result. The second prints the baseline
render trees, current HTML markers, and every prototype record. Both run the
same semantic assertions.

## Result

Citry already knows enough to serialize component-first ownership for normal
template component calls and template fills, but it knows the pieces at
different times. They must be recorded before the current objects discard
them:

1. `ComponentNode.render` knows the authoring component, the executed call,
   and the static source span before it creates a `DeferredComponent`.
2. `_make_body_slot` knows the lexical writer and whether this closure is a
   named fill, implicit fill, or child fallback.
3. Each actual Slot invocation knows the receiving component and can mint one
   physical region. This is where a nested child fallback can record the
   inverse transition back into child ownership.
4. `_render_one` mints the target component render ID. It can bind that ID to
   the earlier call record.
5. Serialization can consume those records, but cannot reconstruct them from
   the settled `CitryRender` tree or flattened HTML.

The prototype captures those five moments and emits runtime-neutral comment
caps around each observed slot invocation:

```html
<!--citry-research-region-start:region1-->
...
<!--citry-research-region-end:region1-->
```

The comments are deliberately research spellings. Their purpose is to prove
that single-root, multi-root, text-only, and empty output can all share one
region representation. They do not establish a cap-every-fill policy.

Two origins remain under-specified by current objects:

- A Python-provided `Slot` has no rendered supply location. Its optional
  `source_position` is construction metadata, not a live component call
  location.
- The selected target of dynamic `<c-component>` is rendered as a
  `CitryElement` from the transparent wrapper's expression path. The target
  reaches `_render_one` without the wrapper as `parent` and without a
  `ComponentNode` call record.

These are real representation gaps. The harness reports them as
`missing-python-slot-source` and `missing-call-identity` rather than assigning
invented owners.

## Prior art and current code

The spike read and exercised:

- [`../component_slots.md`](../component_slots.md), especially fill collection, fallback, queue,
  and repeated-slot semantics.
- [`exploration-slots-alpine-scope.md`](exploration-slots-alpine-scope.md),
  especially the nested fallback and serialization findings.
- [`exploration-x-props-round-2.md`](exploration-x-props-round-2.md), for the
  general registry, call edge, shared root, rootless, mirror, and dynamic
  target requirements.
- [`spike-rootless-lifecycle.md`](spike-rootless-lifecycle.md), for physical
  range tokens and one logical instance owning several physical ranges.

The load-bearing current implementation is:

- `ComponentNode` still owns its template source and exact span when it
  resolves inputs and creates the deferred child
  ([`nodes/__init__.py:719`](../../../packages/py/citry/citry/nodes/__init__.py#L719),
  [`nodes/__init__.py:770`](../../../packages/py/citry/citry/nodes/__init__.py#L770)).
- `_make_body_slot` closes over the writer's `CitryContext`; the resulting
  `CitryRender` therefore retains the writer component while unflattened
  ([`nodes/__init__.py:209`](../../../packages/py/citry/citry/nodes/__init__.py#L209)).
- `SlotNode.render` creates the fallback and invokes either fill or fallback
  before the result reaches `on_slot_rendered`
  ([`nodes/__init__.py:1120`](../../../packages/py/citry/citry/nodes/__init__.py#L1120),
  [`nodes/__init__.py:1166`](../../../packages/py/citry/citry/nodes/__init__.py#L1166)).
- `CitryRender` retains only parts, context, and the component-root flag. A
  `DeferredComponent` retains element, parent, and provides. Neither has a
  call, source-location, fill, transition, or region field
  ([`citry_render.py:99`](../../../packages/py/citry/citry/citry_render.py#L99),
  [`citry_render.py:215`](../../../packages/py/citry/citry/citry_render.py#L215)).
- The renderer searches all nested renders for deferred children, including
  cross-owner fill renders, but this walk records only the context in which a
  deferred child was found
  ([`component_render.py:360`](../../../packages/py/citry/citry/component_render.py#L360)).
- The serializer marks component element roots, then recursively joins every
  non-component-root interior render. That join erases slot boundaries and
  ownership transitions
  ([`serialize.py:62`](../../../packages/py/citry/citry/serialize.py#L62),
  [`serialize.py:226`](../../../packages/py/citry/citry/serialize.py#L226)).
- `Slot` says `component_name` and `slot_name` are debugging names and
  `source_position` is only an optional `<c-fill>` span. Normalization may
  retain one named Slot object across uses
  ([`slots.py:130`](../../../packages/py/citry/citry/slots.py#L130),
  [`slots.py:266`](../../../packages/py/citry/citry/slots.py#L266)).
- Dynamic `<c-component>` constructs its selected target in
  `template_data`, then exposes it through `{{ target }}`
  ([`components/dynamic.py:55`](../../../packages/py/citry/citry/components/dynamic.py#L55)).

## The five identities are different

The prototype deliberately keeps these records separate:

| Identity | Meaning | Lifetime in the prototype |
|---|---|---|
| Render ID | One rendered component instance, currently `component.id`. | From `_render_one` through browser instance cleanup. |
| Call/init edge | One executed component call connecting an authoring component to a target render. | Minted at `ComponentNode.render`, bound to the target render ID at `_render_one`. |
| Lexical source location | One executed location whose client scope owns authored expressions. It includes the writer render plus source span, but has its own ID because one static node may execute repeatedly. | From call/fill creation through source re-election or teardown. |
| Logical fill | One supplied fill or fallback closure. Repeated slot outlets may invoke it several times. Reusing one Python Slot object at two supply calls creates two logical fills, not one. | From supply until its receiver or supplying location dies. |
| Physical region | One actual output occurrence of a logical fill. It may contain one root, many roots, text, or nothing. | One cap pair or equivalent physical representation. |

One graph cannot substitute for the others. Component ancestry answers init
ordering. A lexical source location answers expression ownership. A logical
fill groups repeated or mirrored output. A physical region answers DOM
liveness and morph targeting.

## Scenario evidence

All ten requested cases complete. Targeted assertions cover fill-kind
classification, nested fallback inversion, component-call ownership inside a
fill, shape-independent region creation, reused Slot identity versus supply
identity, mirrored region uniqueness, and the dynamic target gap. The table
also summarizes inspected trace fields that are retained in `--full` output;
it is capture-site evidence, not a production serializer acceptance suite.

| Case | Current output | Prototype finding |
|---|---|---|
| Ordinary named fill | The receiver and parent markers stack on the receiver root. There is no fill marker. | One logical named fill and one physical transition from receiver scope to writer scope. |
| Implicit fill | Same flattening as a named fill. | One logical implicit fill with the component-call span as its source location. |
| Child fallback nested in parent fill | The outer parent-owned `<b>` carries component root markers. The nested child-owned `<i>` has no inverse marker. | The outer region transitions child to parent. A nested region whose `physicalParentRegionId` names the outer region transitions parent back to child. |
| Component inside fill | The nested component gets its own element marker. Physical placement alone does not say who authored its call. | The nested component call edge points to the fill writer, and the call record also names the containing fill region. |
| Multi-root fill | Both roots carry the same component markers; intervening text is unmarked. | One physical region covers two element roots and text without a wrapper. |
| Text-only fill | No component marker exists anywhere in the output. | One physical region still exists and can own a client lifetime. |
| Empty fill | Final HTML contains only template formatting whitespace. | One empty physical region remains addressable by its cap pair. |
| Reused Python Slot | The same Slot content renders under two independently rendered receivers, but neither output carries supply provenance. | The shared Slot content object produces two logical fills and two physical regions. Both lexical source locations stay unknown. The two embedded receiver components also reach `_render_one` without component-call records. |
| Mirrored outlet | The same fill renders at two `<c-slot>` sites and both copies carry only component markers. | One logical fill owns two uniquely tokened physical regions. |
| Dynamic component | The selected target and page markers reach the target root; the transparent wrapper has no marker. | The Page-to-wrapper call exists. The selected target has no call/init edge or parent link. The fill still carries Page ownership into the target because the same Slot closure passes through. |

The full harness output includes the exact current HTML, pre-serialization
render tree, element marker groups, and prototype records for each row.

## Latest safe capture points

### Component calls

Capture a fresh call record during each execution of `ComponentNode.render`,
not once per compiled node. The record needs:

```text
call ID
source render ID
source location ID
target class
physical parent region ID, when authored inside a fill
```

When `_render_one` creates the target component, bind its render ID to that
record and emit the init edge. A static `(writer ID, source span)` tuple is not
itself a live source identity because loops can execute the same node several
times.

### Template fills and fallbacks

Capture one logical-fill record when `_make_body_slot` creates the closure.
The caller must state whether it is creating a named fill, implicit fill, or
fallback. The current function arguments do not encode that distinction.

Capture one physical-region record around every actual invocation. This is
earlier than `on_slot_rendered`: a parent fill may invoke the child fallback
inside its own body, and the nested fallback invocation must establish its
own region before the outer slot result is returned.

Each region needs:

```text
physical region ID
logical fill ID
receiver render ID and slot-site span
lexical source location ID
lexical owner render ID
containing physical region ID, when nested
```

The prototype's containing-region field is what proves the fallback inversion
without inspecting flattened HTML.

### Python and expression composition

Python-provided content needs an explicit supply descriptor at the point it
is attached to a rendered component invocation. Slot object identity is only
content identity. It cannot stand for a logical fill because the same object
can be supplied at several locations.

Likewise, a `CitryElement` rendered from `{{ ... }}` needs an explicit policy
and call record if the client model intends it to participate in component
ancestry. The normal `ComponentNode` path cannot recover a source span for a
value created in arbitrary Python. It can still record a runtime source
owner supplied by the embedding expression operation, if that is the chosen
policy.

Dynamic `<c-component>` is narrower: the wrapper already has a real rendered
instance and a real Page-to-wrapper call. Its selected target should receive
an explicit wrapper-to-target or transparent-forwarded Page-to-target edge
when the `CitryElement` is created. Current target rendering supplies neither.

## What the settled tree can and cannot derive

The final unflattened `CitryRender` tree can still derive:

- every component root render that remains structurally nested;
- the component ID and class attached to each retained context;
- component element-root markers after serialization;
- a change of context owner across a nested interior render.

It cannot derive:

- which `ComponentNode` execution created a target;
- the source span of that call;
- whether an interior writer-owned render is a named fill, implicit fill, a
  direct embedded render, or another interior construct;
- two occurrences of the same string or reused `CitryRender` by object
  identity;
- the nested fallback invocation after its result has been joined into its
  surrounding fill;
- a logical group around text or empty output;
- the live supply location of a Python Slot;
- the selected target's ancestry through dynamic `<c-component>`.

Context-owner changes are useful validation, but they are not a complete wire
format. Adding caps after flattening would preserve the wrong amount of
information.

## Implications for the component-first exploration

The lowest-risk server direction is an explicit render-side ownership record,
not DOM inference:

1. Mint call and source-location records at component-call execution.
2. Mint logical-fill records when closures are created.
3. Mint physical regions and transition records at each invocation.
4. Bind component render IDs during `_render_one`.
5. Let serialization choose an element carrier, comment caps, or manifest-only
   representation based on whether the record is client-active and on its
   output shape.

The spike supports a component-first graph, but does not select its final
schema. In particular, it does not prove that every inert fill needs comments,
that `Slot` should publicly expose these identities, or that the research
monkeypatch locations are the production API boundaries. It proves the
information clocks and the cases that fail when capture happens later.

No runtime implementation is authorized or included.
