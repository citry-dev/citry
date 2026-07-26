# `citry-client-graph/1`

Citry can usually render HTML and let the browser display it. Some pages also
need the browser to know which component produced which output, where slot
content came from, and which component starts first. HTML alone does not keep
those facts.

For those pages, the server sends one block of inert JSON:

```html
<script type="application/json" data-citry-graph>...</script>
```

This is the **graph manifest**. This package defines its JSON shape and the
checks a browser must make before using it. [`validate.py`](validate.py) is the
reference checker, and [`fixtures/`](fixtures/) contains worked examples.

## Why the browser needs more than the HTML

Rendering removes component tags and combines templates into ordinary HTML.
That loses four relationships the browser may still need.

1. **A component can produce any number of HTML nodes.** Suppose `Notice` also
   registers browser setup with `$component(...)`:

   ```html
   <!-- Page template -->
   <main><c-notice /></main>

   <!-- Notice template -->
   <strong>Ready</strong>
   <small>Updated now</small>
   ```

   The browser receives two sibling elements inside `<main>`. Nothing in that
   element tree says that both came from one `Notice` component. A text-only or
   empty component leaves even less evidence.

2. **Slot content can use the browser data of the component that supplied it.**

   ```html
   <!-- Page template -->
   <main x-data="{ title: 'Page title' }">
     <c-card>
       <c-fill name="title">
         <span x-text="title"></span>
       </c-fill>
     </c-card>
   </main>

   <!-- Card template -->
   <article x-data="{ title: 'Card title' }">
     <c-slot name="title" />
   </article>
   ```

   The `<span>` appears inside Card's `<article>`, but it was written in Page's
   template and must display `Page title`. DOM ancestry points to Card's data,
   so the browser needs the original ownership relationship.

3. **One supplied fill can render at several slot outlets.**

   ```html
   <!-- Page template -->
   <main x-data="{ badge: 'New' }">
     <c-mirror>
       <c-fill name="badge">
         <strong x-text="badge"></strong>
       </c-fill>
     </c-mirror>
   </main>

   <!-- Mirror template -->
   <header><c-slot name="badge" /></header>
   <footer><c-slot name="badge" /></footer>
   ```

   Page supplies one fill, but Mirror renders it twice. The graph records one
   fill and two slot regions. A slot region is one stretch of HTML produced
   each time a `Slot` renders a fill.

4. **DOM nesting does not always reveal component setup order.** Suppose both
   Parent and Child register browser setup with `$component(...)`:

   ```html
   <!-- Parent template -->
   <h1>Parent</h1>
   <c-child />

   <!-- Child template -->
   <button>Child</button>
   ```

   The `<h1>` and `<button>` become siblings. The graph still tells the browser
   to start Parent before Child:

   ```json
   {
     "componentExecutionOrderConstraints": [
       {
         "invocationId": 1,
         "parentRenderId": "c1",
         "childRenderId": "c2"
       }
     ]
   }
   ```

The graph lets Citry attach component behavior, route Events, pass browser
bindings from parent to child, give slot content the right browser data, and
keep those relationships when a fragment is inserted or replaced.

## When Citry sends the graph

Citry calls a rendered component occurrence **client-active** when the browser
needs to know that some output belongs to that exact component occurrence. In
practical terms, the component's template or JavaScript uses a Citry feature
that needs extra server-to-browser relationship data. Examples include setup
registered with `$component`, Events or State, bindings passed through a nested
`<c-*>` tag, Citry expressions that refer to the current component, and Alpine
directives inside a template-authored slot fill. Ordinary Alpine markup can
work without Citry component identity, so an `x-*` attribute alone does not
always make a component client-active.

Citry may also mark related components as client-active. For example, a client
binding needs both the parent that supplied it and the child that received it;
a slot fill with Alpine needs both the component that wrote the fill and the
component whose slot rendered it. Descendants are included when Citry must keep
their Alpine scopes separate. This is why the term can appear on a component
that did not directly use the feature that first required the graph.

The server emits a graph if the settled output contains at least one
client-active occurrence. Once a graph is needed, it retains every surviving
non-transparent component occurrence in that output, including static ones. A
transparent component is structural: its output joins the surrounding
component's output and gets no `data-cid-*` marker of its own. It is retained
only when a slot region refers to it. `client-active` is therefore an internal
condition, not an author-facing switch or a JSON field, and it is narrower than
`retained`.

## How the graph reaches the browser

1. While templates render, the server records component relationships,
   bindings, fills, slot regions, and required setup order.
2. Once rendering settles, it discards records for output that did not make it
   into the response. Paired HTML comments mark every retained component and
   slot region without forcing wrapper elements into the page.
3. It writes the manifest after Citry's core dependency manager and before the
   Events and dependency blocks that use it.
4. The browser checks the complete JSON and every expected comment pair before
   publishing any of the new records. If a check fails, it rejects the whole
   incoming graph and keeps previously accepted state unchanged.

## How to read one graph

A manifest can contain several graphs. Nested rendering normally stays in the
current graph, while a separately rendered or pre-rendered subtree can bring
its own. References never cross from one graph to another.

Start with these records:

- **`componentInstances`** contains one record for each component occurrence whose
  result remains in the response after rendering settles. Failed, replaced, or
  discarded output does not count. A surviving component still counts if it
  rendered several elements, only text, or nothing visible. Every surviving
  non-transparent component is retained; a transparent component is retained
  only when a slot region refers to it. These are rendered occurrences, not
  every Python `Component` object created along the way.
- **`nestedComponents`** contains one record for each nested component tag
  (`<c-*>`) executed by a parent template. It connects that parent to the
  resulting child and records the tag location and bindings that crossed the
  boundary. The record's `invocationId` identifies that one execution. Here,
  invocation does not mean constructing `MyComp(...)` in Python, and it is not
  a DOM placement. Every invocation has exactly one child instance. A directly
  rendered graph root has no invocation.
- **`fills`** describes content supplied to a slot or a slot's fallback
  content. For template-authored content, its owner is the component whose
  browser data Alpine and Citry expressions use. Python template expressions
  have already run before the manifest exists. The receiver is the component
  whose slot accepts the content.
- **`slotRegions`** contains one record for each slot region: one stretch of HTML
  produced each time a `Slot` renders a fill. If two outlets render the same
  fill, that is one fill with two slot regions. A direct Python call to the
  same `Slot` also creates a slot region. Every slot region points to its fill
  through `fillId`.

The remaining collections support those relationships:

| Collection | Purpose |
|---|---|
| `componentClasses` | Maps each `classId` to a component class name. |
| `componentExecutionOrderConstraints` | Records only the parent-before-child setup order the browser must enforce. |
| `sourceLocations` | Adds template source positions in development mode. |

The main identifiers also have separate jobs:

- `graphId` is the graph's position in the top-level `graphs` array.
- `instanceId`, `invocationId`, `fillId`, and `regionId` identify their own
  record types inside one graph.
- `renderId` is a rendered component occurrence's runtime identity. It is
  unique across the manifest. Every non-transparent element root gets a
  `data-cid-<renderId>` attribute name. A client-active root also lists the id
  as a value in `data-cid`.
- `classId` identifies a component class through the `componentClasses`
  collection.

An Events response can place one returned fragment into several matching DOM
targets. Those placements share one set of graph records; the browser tracks
the extra DOM copies separately. It does not duplicate component instances,
nested-component records, fills, or slot regions.

For a first pass, read `componentInstances`, then `nestedComponents`, then
`fills` and `slotRegions`. Read `componentExecutionOrderConstraints` when
browser setup order matters and `sourceLocations` when you need development
source positions. The remaining sections define the exact wire shape and
validation rules.

## TypeScript view of the JSON

The following interfaces present the complete JSON shape in a form that is
easy to scan. Their names are documentation labels; only the property names and
values appear on the wire. Every property shown is required. A property whose
type includes `null` is still present in the JSON when its value is null.

TypeScript describes the shape but cannot enforce every protocol rule. In
particular, `number` does not guarantee an integer or a minimum value,
TypeScript permits extra properties in many assignments, and these interfaces
cannot prove unique ids, valid references, allowed cross-field combinations,
the development/production location rules, or a correct revision hash. The
JSON Schema and the checks later in this document remain authoritative.

### `ClientGraphManifest`

The top-level object identifies the protocol and carries every graph in one
server response.

```ts
interface ClientGraphManifest {
  protocol: "citry-client-graph/1";
  revision: string;
  mode: "production" | "development";
  graphs: ClientGraph[];
  delimiters: GraphDelimiters;
}
```

### `GraphDelimiters`

This value tells the reader which HTML markers locate component instances and
slot regions.

```ts
interface GraphDelimiters {
  format: "comment-v1";
}
```

### `ClientGraph`

One graph groups retained records that were produced together during rendering.
Its arrays use the record types defined below.

```ts
interface ClientGraph {
  graphId: number;
  componentClasses: ComponentClassRecord[];
  componentInstances: ComponentInstanceRecord[];
  sourceLocations: SourceLocation[];
  nestedComponents: NestedComponent[];
  componentExecutionOrderConstraints: ComponentExecutionOrderConstraint[];
  fills: SlotFill[];
  slotRegions: SlotRegion[];
}
```

### `ComponentClassRecord`

This record pairs a component class's stable id with its display name.

```ts
interface ComponentClassRecord {
  classId: string;
  className: string;
}
```

### `ComponentInstanceRecord`

This record identifies one retained component occurrence. A root component
instance has null invocation and parent references.

```ts
interface ComponentInstanceRecord {
  instanceId: number;
  renderId: string;
  classId: string;
  invocationId: number | null;
  parentRenderId: string | null;
  transparent: boolean;
}
```

### `SourceOffset`

This half-open range counts UTF-8 bytes in the executed template source.

```ts
interface SourceOffset {
  start: number;
  end: number;
}
```

### `SourcePosition`

This position gives people a one-based line and column for diagnostics.

```ts
interface SourcePosition {
  line: number;
  column: number;
}
```

### `SourceLocation`

Development manifests use this record to point from a nested component tag,
binding, fill, or slot back to its template source. Production graphs keep
`sourceLocations` empty.

```ts
interface SourceLocation {
  locationId: number;
  kind:
    | "component-call"
    | "boundary-relay"
    | "implicit-fill"
    | "named-fill"
    | "fallback-fill"
    | "slot-outlet";
  ownerRenderId: string;
  ownerClassId: string;
  carrierInstanceId: number;
  origin: string | null;
  sourceOffset: SourceOffset;
  sourcePos: SourcePosition;
  mappingKey: string | null;
  mappingIndex: number | null;
}
```

### `NestedComponent`

This record connects one executed occurrence of an authored component tag to
the child instance it produced. Relays carry the bindings that crossed that
component boundary.

```ts
interface NestedComponent {
  invocationId: number;
  sourceRenderId: string;
  sourceClassId: string;
  locationId: number | null;
  tagName: string;
  targetClassId: string;
  targetRenderId: string;
  parentRegionId: number | null;
  relays: BoundaryRelay[];
}
```

### `BoundaryRelay`

This record carries one browser-side binding that a parent handed to a child,
plus how it was written and its typed payload.

```ts
interface BoundaryRelay {
  key: string;
  source: "direct" | "server-dynamic" | "spread";
  locationId: number | null;
  payload: BoundaryRelayPayload;
}
```

### `BoundaryRelayPayload`

The `type` property selects exactly one of the four payload shapes.

```ts
type BoundaryRelayPayload =
  | PropsRelayPayload
  | AlpineHandlerRelayPayload
  | CitryDomEventRelayPayload
  | CitryPollRelayPayload;
```

### `PropsRelayPayload`

This payload passes one Alpine expression through `$c-props`.

```ts
interface PropsRelayPayload {
  type: "props";
  expression: string;
}
```

### `AlpineHandlerRelayPayload`

This payload passes one Alpine handler expression to a child boundary.

```ts
interface AlpineHandlerRelayPayload {
  type: "alpine-handler";
  expression: string;
}
```

### `CitryDomEventRelayPayload`

This payload carries a compiled Citry handler for one DOM event.

```ts
interface CitryDomEventRelayPayload {
  type: "citry-dom-event";
  classId: string;
  event: string;
  handler: string;
  args: string | null;
  prevent: boolean;
  stop: boolean;
  self: boolean;
  once: boolean;
  key: string | null;
  debounce: number | null;
  throttle: number | null;
}
```

### `CitryPollRelayPayload`

This payload carries a compiled Citry polling handler and its interval.

```ts
interface CitryPollRelayPayload {
  type: "citry-poll";
  classId: string;
  handler: string;
  args: string | null;
  interval: number;
}
```

### `ComponentExecutionOrderConstraint`

This edge requires one parent component to initialize before one child.

```ts
interface ComponentExecutionOrderConstraint {
  invocationId: number;
  parentRenderId: string;
  childRenderId: string;
}
```

### `SlotFill`

This record describes content supplied to one receiver's slot. The policy
determines which nullable relationship fields must be null or non-null.

```ts
interface SlotFill {
  fillId: number;
  kind: "implicit" | "named" | "fallback" | "python" | "typed-default";
  slotName: string;
  policy: "template" | "python-detached" | "typed-default-detached";
  ownerRenderId: string | null;
  ownerClassId: string | null;
  locationId: number | null;
  sourceInvocationId: number | null;
  receiverRenderId: string | null;
  receiverClassId: string | null;
  fallbackLocationId: number | null;
}
```

### `SlotRegion`

This record describes one rendered occurrence of a fill. Its ownership fields
tell the browser which component's data applies inside that stretch of HTML.

```ts
interface SlotRegion {
  regionId: number;
  fillId: number;
  receiverRenderId: string | null;
  slotLocationId: number | null;
  ownerRenderId: string | null;
  sourceLocationId: number | null;
  parentRegionId: number | null;
  transitionFromRenderId: string | null;
  resultOwnerRenderId: string | null;
}
```

## What the server puts in the JSON

The top-level object has exactly these members, no more and no fewer:

- `protocol`: the exact string `citry-client-graph/1`.
- `revision`: a fingerprint of the manifest. The server takes the whole object
  with `revision` left out, serializes it canonically (sorted keys, no
  whitespace, UTF-8), hashes that with SHA-256, and writes the lowercase hex
  digest here. **Any edit to the manifest changes this value.**
  
  **IMPORTANT:** The revision is a
  plain content hash, not a signature: there is no secret. Revision only confirms that
  manifest is **internally consistent**, but **it does NOT
  prove your server produced it**. Anyone who can inject the script tag can
  compute a matching hash, but they could inject any markup anyway, so this is
  an integrity and identity check, never authentication.
- `mode`: the build that produced this manifest, `production` or `development`.
  In development the manifest carries source provenance through
  `sourceLocations` and references to those records. In production every
  required `sourceLocations` array is present but empty and every location
  reference is null, because the browser never needs the provenance and it is
  roughly half of the manifest.
  See
  [`../../../../docs/design/dev_prod_mode.md`](../../../../docs/design/dev_prod_mode.md).
- `graphs`: the graphs themselves, in the order they were first seen in the
  HTML. Each graph has a dense `graphId` (0, 1, 2, and so on) and numbers its
  own records from 1; a record id only means something inside its own graph.
- `delimiters`: the object `{ "format": "comment-v1" }`. It names the format of
  the paired HTML comments that bracket the start and end of each piece (see
  "Where each piece sits in the HTML").

The manifest writes strings in place: a render id, class id, name, expression,
or slot name is the JSON string itself, not an index into a shared table. Every
reference from one record to a component stays inside the same graph. If keeping
some relationship would force the server to point from one graph into another,
the server refuses to emit the manifest rather than write a cross-graph
reference.

At a component boundary the server hands the browser a set of bindings, called
**boundary relays**, and each relay says which kind it is. A `props` or
`alpine-handler` relay carries one Alpine expression string. A `citry-dom-event`
or `citry-poll` relay carries a server-handler binding that is already compiled,
plus an optional opaque Alpine argument-expression. The browser never takes a
Citry handler value and re-reads it as if it were one whole Alpine expression.

## Where things were written: source locations (development only)

In development the server records where each nested component tag (`<c-*>`),
relay, fill, and slot was written, in a graph's `sourceLocations` array. It never
copies the source text; each location points at it. A location carries the
`origin` it came from (a file or an inline-template marker), a `sourceOffset`
(a `{start, end}` UTF-8 byte range into the template source as it stands after
the `on_template_loaded` template hook runs, not the author's original file and
not the delivered HTML or DOM), a `sourcePos` (`{line, column}` for error
messages), and the `carrierInstanceId` of the
retained instance whose template execution produced it.

These offsets are provenance for tooling, such as a future error overlay that
maps a runtime failure back to its authored template snippet; the browser
validates their shape but does not act on them. Production keeps the required
`sourceLocations` array empty and nulls every reference to it, so a production
reader has nothing to check here.

## Render ids must be safe as an HTML attribute name

Every component instance's `renderId` matches `^[a-z0-9_-]+$`. An instance
with an element root uses its render id as the suffix of a
`data-cid-<render-id>` attribute name. When the server marks that root as a
Citry-managed Alpine boundary, the root also includes its render id as one
whitespace-separated token in `data-cid`. HTML attribute names are
case-insensitive, so an uppercase letter is forbidden: two ids that differed
only in case would collapse onto one identity. The same rule applies to
transparent instances, which use comment delimiters rather than an element
marker. The reference validator, the server, and the browser all enforce it.

## How fills point back to where they came from

A fill is content handed to a component's slot. The rendered content usually
sits at the receiver's `<c-slot>` outlet, but browser-side Alpine and Citry
expressions in template-authored content must keep using the data scope of the
component that wrote it. Python template expressions have already run on the
server by this point. When the author writes the content in a template (an
`implicit` or `named` fill), the server records a non-null
`sourceInvocationId` on it. That
points at the exact nested component tag execution (an `invocation`) where the
Slot was created. The invocation's source is the component whose template
contains the fill, so it is the fill's owner. Even when the same live Slot is
passed along to a later receiver, that original invocation stays the recorded
source. Each receiving component gets its own fill record. Each time a `Slot`
renders that fill, whether through an authored outlet or a direct Python call,
it creates another slot region for the same fill.

When a slot renders its own fallback content instead of author-supplied
content, that fill has no `sourceInvocationId`. In development it carries a
non-null `fallbackLocationId` that identifies the receiver's `slot-outlet`
which chose the fallback. The fill's own `locationId` identifies where the
fallback content was written, and a slot region points to both roles as its slot
and source locations. Fills supplied from Python directly, and fills that
fall back to a typed default, carry neither a source invocation, an owner, nor a
source location, and the browser never treats their receiver as a source.

In development the `kind` of a location is checked: a nested component tag
uses the wire value `component-call`, a fill's own location uses its matching
`implicit-fill`, `named-fill`, or `fallback-fill` kind, and a slot or fallback
location uses `slot-outlet`.

## Where each piece sits in the HTML

The server wraps each rendered component instance and slot region in one pair
of HTML comments, its delimiters, that mark where it starts and ends:

```text
<!--citry:g1:<revision>:<graph>:i:<instance-id>:s-->
<!--citry:g1:<revision>:<graph>:i:<instance-id>:e-->
<!--citry:g1:<revision>:<graph>:r:<region-id>:s-->
<!--citry:g1:<revision>:<graph>:r:<region-id>:e-->
```

A start and its end share one parent, nest properly inside outer pairs, and
never cross. There is one exception, forced by how the HTML parser moves
comments around: for a complete document that the author did not wrap in an
`<html>` element, the parser may leave the opening comment under the `Document`
node while moving the closing comment under the implicit `body`. The browser
accepts only that one exact `Document`-to-`body` pairing. This comment scheme
works for single-root, multi-root, and rootless content, for adjacent and
nested pieces, for fragments in table, select, and SVG contexts, and for the
same slot rendered several times, all without the server inventing a wrapper
element.

## How the browser checks the manifest before using it

Before any part of the manifest can affect the page, the browser checks the
whole thing in a holding area and commits only if every check passes. It
confirms the exact set of fields, the protocol and mode strings, the canonical
SHA-256 revision, integer bounds, unique ids, and that every reference points at
something that exists. In development it also checks the source locations (their
kind, owner, and byte ranges); in production it requires no location records
and no location references. It confirms that each component instance agrees
with the nested component record that produced it (same source and target),
that each slot region agrees with its fill, that each supplied fill agrees with
its source invocation, that component execution order and slot-region nesting
contain no cycles, that scope
transitions are valid, and that the logical parent-child structure matches the
nesting of the paired HTML comments. No record from the graph becomes visible
to the rest of the page until all of that passes. The server and browser both
cap one manifest at 1,000,000 UTF-8 bytes.

A malformed or partial fragment commits nothing and leaves already-committed
revisions untouched. The browser processes each script node once, keyed on the
node's own identity, which cannot be cloned; a `data-*-processed` attribute may
be shown for debugging but never decides whether a node was handled. Inserting
or cloning a second script tag that carries an already-committed revision is
rejected, because that revision's ids and comment markers describe one concrete
place in the page and must not be duplicated. Moving the original DOM nodes
does not produce a second manifest.

When an Events block names this graph's revision, Events decodes every class
and instance before it changes any of its own registries, and then reports that
it adopted the graph. Dependency callbacks that were waiting on the graph wait
for that report. If Events fails to decode, it exposes no new anchor and drops
those callbacks.

The server includes a manifest with `document` and `fragment` output only when
the rendered tree requires a graph in the browser. The `simple` and `ignore`
output modes never carry graph comments or a manifest.
