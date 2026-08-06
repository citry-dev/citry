# A1 server ownership capture

**Status:** implementation contract for A1, locked 2026-07-20.

This note narrows A1 in [`../alpinejs_plan.md`](../alpinejs_plan.md) to the
server-side information that must survive before component and slot rendering
flattens it. A1 records ownership only. A2 owns the wire schema, manifest,
physical caps, and browser reconstruction.

## 1. Prior art and constraints

The implementation follows the capture clocks established by
[`component_first_server_ownership_findings.md`](component_first_server_ownership_findings.md):

1. `ComponentNode.render` still knows the executed call, post-template-hook
   runtime source span, source owner, source-ordered attribute contributions,
   and any containing fill region.
2. Body-slot construction still knows whether content is an implicit fill,
   named fill, or receiver fallback and which Python render context authored
   it.
3. A real `Slot` call is the last point that can distinguish one logical fill
   from each mirrored physical occurrence, including text-only and empty
   output.
4. `_render_one` is where a target receives its render ID and can bind a
   deferred invocation to one logical instance and one init-ancestry edge.
5. The settled render tree and final HTML are too late to reconstruct these
   relations reliably.

A1 does not change the Rust AST, compiler output, generated node signatures,
Lang bindings, or PyO3 surface. Existing compiled Python nodes already keep
their source text and exact spans. A **component-tag client binding** is
browser behavior such as `$c-props="{ theme }"`, `@click="select()"`, or
`@c-poll.5s="refresh()"` resolved from a nested `<c-*>` tag. The parent owns
the expression or handler, while the child supplies the component boundary
where the browser applies it. One narrow parser-validation change is required:
component TagRules must recognize those three binding families as boundary
instructions instead of checking them as declared Python kwargs.
This changes validation only and adds no syntax or output field.

The Events template-load rewrite must likewise leave `@c-*` intact on a real
component boundary so `ComponentNode` can capture it, while continuing to
reject `:c-*` there. `<c-element>` is the exception because it selects plain
HTML and keeps both handler families on the ordinary element rewrite path.

In A1, "source" means the executed `CitryTemplate.source` after
`on_template_loaded` hooks. Snippets and positions are exact in that runtime
source, and the original template origin is recorded, but an earlier rewrite
can shift author-file line and column coordinates. Mapping those runtime spans
back to pre-hook author coordinates is not claimed by A1 and must be decided
before A2 exposes author-coordinate diagnostics on the wire.

## 2. Record and ID policy

One root render owns one `OwnershipGraph`. Nested deferred renders, template
fills, fallback calls, and composed values rendered while that root is active
join the same graph. Each `CitryContext` stores the graph that was active when
the context was created.

Graph-local IDs always travel with their owning graph on internal deferred
elements. This matters for a template `Slot` saved from one completed root
and supplied to a later root: the new attachment is a detached Python-origin
fill in the new graph, while any lazily rendered template descendants keep
their original graph. IDs are never looked up in whichever graph happens to
be current. A2 or a later active-content feature must fail closed or require
an explicit source descriptor for that detached cross-graph case.

Graph-local IDs are distinct typed integer domains, allocated monotonically in
capture order:

- component invocation ID;
- source location ID;
- logical fill ID;
- physical region request ID.

The existing string `component.id` remains the render ID. A1 does not replace
or reinterpret it.

Source locations are fresh per executed location, not normalized per compiled
node. A loop that executes one component tag three times therefore creates
three source-location records over the same static span. Each record stores
the source owner render ID, owner class ID, complete source text, source kind,
and the contributed mapping key when the location came from `c-bind`.
`byte_span` is the parser's exact half-open `(start, end)` range in UTF-8 bytes.
`span` is the corresponding half-open range in Python Unicode code points and
is the coordinate system used by `snippet`, `line`, and `column`. A2 must name
the coordinate system it serializes because JavaScript string offsets use
UTF-16 code units. It may later deduplicate source text or normalized spans
without changing the A1 ownership relation.

## 3. Component invocations and client bindings

`ComponentNode.render` resolves attributes left to right into two independent
channels:

1. ordinary Python kwargs;
2. client bindings.

The supported keys are exactly:

- `$c-props`;
- Alpine `@...` and `x-on:...` handlers;
- Citry `@c-*` handlers.

Every other attribute remains an ordinary Python kwarg. `<c-element>` remains
on the plain-HTML path, so none of its handlers become component-tag client bindings and an
active `$c-props` still fails as invalid on a plain element.

For a client binding, the last contribution to the exact key wins. `None` and `False`
remove it, `True` is invalid, and a present value must be a non-empty string.
Replacement removes and reinserts the exact key, so final client binding order follows
the winning contribution positions. Direct, `c-*`, and `c-bind` forms record
the winning attribute span; a spread record additionally stores its mapping
key.

Client bindings travel on `CitryElement` separately from kwargs. They never appear in
typed kwargs, untyped kwargs, or `raw_kwargs`.

A1 preserves each winning client binding value as opaque source text. For a Citry
handler client binding, that text is a server-handler binding with optional arguments,
not a client expression to evaluate wholesale. A2 must compile it into a
handler name plus an optional Alpine argument expression before client
delivery.

Each executed component tag also creates a component-invocation record and a
render-queue deferral record. `_render_one` binds them to the actual target
render ID and creates a typed init-ancestry edge from the source-owner render
to the target render. A component call authored while a fill region is active
also records that physical parent region request ID.

## 4. Dynamic component policy

Runtime `<c-component>` is a transparent selection mechanism, not a client
identity. Its authored invocation, client bindings, source location, and init ancestry
forward to the actual selected target. The transparent Python wrapper may be
recorded as a server-rendered logical instance for diagnostics, but it does
not consume the invocation or become the client binding target.

The invocation target class is finalized when the selected target reaches
`_render_one`. Selecting a different target on a later root render therefore
binds that fresh render graph to the replacement class without carrying the
old target.

Static `<c-component is="...">` already compiles to the selected component and
uses the ordinary direct path.

## 5. Fill and fallback policy

Every template body slot creates one logical-fill record:

- an implicit component body uses the component-call span and caller owner;
- a named `<c-fill>` uses the fill span and caller owner;
- a `<c-slot>` fallback uses the slot span and receiver owner.

Attaching supplied slots to the rendered receiver binds the receiver render ID
without changing the fill's lexical owner. One logical fill may have zero,
one, or several physical region requests.

Every actual `Slot` call creates a fresh physical-region request before its
content runs. The record identifies the logical fill, receiver, invoked slot-site
location, lexical owner and location, containing physical region request, and
the ownership transition's source render. This works without changing its
rendered bytes or public `RenderPart` contract, so one record shape covers
single-root, multi-root, text-only, and empty output. Text and empty results
carry a unique HTML-safe occurrence identity internally, because equal strings
from sibling regions are not the same placement. Mirrored outlets create
several region requests for one logical fill.

The active physical region remains set while a fill body is walked. A fallback
called from inside that body therefore records the inverse transition and its
containing region before either result is flattened. Component invocations
authored inside the fill capture the same containing region even though the
deferred target renders later.

Ownership records also carry output lifecycle. When an `on_render` generator
or `on_component_rendered` extension replaces settled output, the discarded
invocations, instances, init edges, authored fills, and physical regions are
marked retired. Deferred siblings dropped during error unwinding are retired
without being rendered. Failed work remains distinguishable in the render
queue. A2 can therefore select active records without consulting final DOM
ancestry, while retired records remain available for diagnostics.

`on_slot_rendered` maps the output of an existing outlet rather than removing
that outlet. Its selected result is rebound to the same physical-region ID;
discarded nested components and nested regions retire, while the outlet region
and its logical fill stay active. Slot calls made by the hook are captured as
children of that known outlet region, then preserved or retired with the
selected result. This keeps CSS-scoping and wrapper hooks representable when A2
emits physical caps.

## 6. Python-origin policy

Python-provided `Slot` objects, callables, strings, trusted HTML, composed
elements, rendered values, and typed slot defaults remain valid Python render
inputs. Each attachment to a rendered receiver creates a distinct logical
fill even when several receivers reuse the same `Slot` object.

These inputs receive an explicit Python-origin kind but no lexical source
location and no invented source-owner render. Object identity is content
identity, not a source location. A later client-active feature must either
provide an explicit source descriptor or fail closed; it must not guess a
scope from DOM placement, receiver identity, or an old optional
`Slot.source_position`.

This policy changes no Python slot output and does not prevent server-only
callables or trusted HTML from rendering.

## 7. A1 acceptance boundary

Server tests inspect the graph before serialization and cover:

- nested direct component calls and deferred binding;
- direct, server-dynamic, spread, replacement, removal, and re-addition client binding
  contributions with exact winning runtime-source spans;
- static and runtime dynamic component targets;
- named and implicit supplied fills;
- receiver fallbacks and nested fallback inversion;
- a component call authored inside fill content;
- one fill mirrored across several outlets;
- rootless, text-only, empty, and multi-root slot output without DOM inference;
- one Python `Slot` object attached to several receivers;
- repeated execution of one compiled source span;
- delayed template fills reused after their original root and across a later
  root without graph-local ID collisions;
- generator and extension output replacement, failed work, and deferred
  sibling retirement.

A1 deliberately does not emit comments, attributes, or a graph manifest; does
not initialize Alpine; and does not implement client props or handlers. Those
are A2 and later batches.
