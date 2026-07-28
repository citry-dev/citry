# Implementation plan: settled Alpine activation

**Status:** proposed on 2026-07-26.

Citry should run plain Alpine markup without requiring an unrelated
`$component`, Events, State, or slot-fill feature elsewhere on the page. A
real Alpine directive in the settled output should activate the owning Citry
client graph and Citry's pinned Alpine runtime.

This plan covers that behavior change. It also removes the duplicated trigger
lists that currently decide whether to build a graph and which component
occurrences belong to its client lifecycle.

For the accepted Alpine ownership model, see
[`alpinejs.md`](alpinejs.md). For repository operating rules, see
[`CLAUDE.md`](../../CLAUDE.md).

## Prior art and binding risk

This plan changes an additive PyO3 surface, so its implementation must start
from the current cross-crate contract:

- [`serialize_render()`](../../packages/py/citry/citry/serialize.py#L80-L101)
  first asks `ownership_manifest_required()` and then calls
  `prepare_ownership_manifest()`.
- [`prepare_ownership_manifest()`](../../packages/py/citry/citry/ownership_manifest.py#L169-L243)
  and
  [`ownership_manifest_required()`](../../packages/py/citry/citry/ownership_manifest.py#L690-L757)
  independently walk the settled tree and repeat the trigger list.
- [`_build_frame()`](../../packages/py/citry/citry/serialize.py#L300-L380)
  defines the serializer's exact rules for strings, nested component
  placeholders, interior renders, physical regions, and extension
  placeholders.
- [`mark_html()`](../../crates/citry_html_transform/src/marker.rs#L43-L168),
  [`lex_start_tag()`](../../crates/citry_html_transform/src/marker.rs#L185-L276),
  and
  [`raw_text_content_end()`](../../crates/citry_html_transform/src/marker.rs#L304-L328)
  are the existing raw-text-aware, fail-soft HTML scanner.
- The binding is registered in
  [`citry_core_py/src/lib.rs`](../../crates/citry_core_py/src/lib.rs#L21-L35),
  wrapped in
  [`citry_core_py/src/html_transform.rs`](../../crates/citry_core_py/src/html_transform.rs#L1-L75),
  declared in
  [`_rust.pyi`](../../packages/py/citry_core/citry_core/_rust.pyi#L31-L89),
  and re-exported from
  [`citry_core.html_transform`](../../packages/py/citry_core/citry_core/html_transform/__init__.py).
- The ownership artifact enters document delivery in
  [`dependencies/emission.py`](../../packages/py/citry/citry/ext/dependencies/emission.py#L147-L199)
  and fragment delivery in the
  [same module](../../packages/py/citry/citry/ext/dependencies/emission.py#L530-L602).
  The combined Alpine and Events bundle is selected in
  [`events/emission.py`](../../packages/py/citry/citry/ext/events/emission.py#L211-L257).
- Cache replay rebuilds fresh render parts, frames, IDs, and physical regions
  before serialization in
  [`ext/cache/replay.py`](../../packages/py/citry/citry/ext/cache/replay.py#L1891-L1969).

The chosen design below preserves `mark_html`'s return shape, adds one narrow
attribute-span query through every Python binding layer, and does not add
activation metadata to the cache artifact or client-graph wire format.

## 1. Outcome

After this work, the following component works by itself under the default
`document` strategy:

```python
class Counter(Component):
    template = """
      <button x-data="{ count: 0 }" @click="count++" x-text="count">
        0
      </button>
    """
```

Citry will detect the rendered `x-data`, `@click`, and `x-text` attributes,
emit the client ownership graph, load its owned Alpine runtime, and isolate
the component from unrelated Citry component scopes. The component does not
need a meaningless `$component(() => {})` block just to make Alpine start.

The behavior is based on final rendered output:

- static `x-*`, `@*`, and `:*` attributes activate;
- dynamic `c-x-*`, `c-@*`, `c-:*`, and `c-bind` contributions activate only
  when their resolved attributes remain in the selected output;
- selected conditions, loops, slots, trusted HTML, cache replays, and
  `on_render()` replacements are inspected;
- discarded branches and replaced output do not activate;
- directive-looking text in comments, examples, scripts, styles, attribute
  values, `textarea`, or `title` does not activate.

The dependency strategies keep their existing meanings:

| Strategy | Plain Alpine directive in settled output |
|---|---|
| `document` | Emit the graph, dependency manager, and owned Alpine runtime |
| `fragment` | Emit the graph and runtime URL descriptors; require a mounted Citry integration |
| `simple` | Preserve the attributes but emit no graph or runtime |
| `ignore` | Preserve the attributes but emit no graph or runtime |

Automatic activation does not expose `js_data()` to Alpine expressions.
Python-provided browser data still belongs to a component's `$component`
callback.

## 2. One answer, with reasons

The implementation must not add another free-standing `uses_alpine` flag to
the current trigger checks. That would make the next feature update one list
and forget another.

Instead, serialization will create one immutable
`ClientActivationAnalysis`. It answers all of these questions together:

- which settled component occurrences and physical regions were reached;
- which graphs and snapshots describe them;
- which client feature activated each occurrence;
- which slot relationships must project a source or install an empty base;
- which descendants must become isolation boundaries;
- whether the output needs a client graph. The graph artifact is also the
  runtime-selection signal.

Activation reasons use a closed internal enum:

```python
class ClientActivationReason(Enum):
    ALPINE_ATTRIBUTE = "alpine-attribute"
    COMPONENT_SETUP = "component-setup"
    COMPONENT_TAG_BINDING = "component-tag-binding"
    EVENTS = "events"
    STATE = "state"
```

Ambient-context magics do not need a separate trigger. They can only run from
an Alpine directive in rendered markup or from `$component`, and both paths
are already represented above.

The analysis records an activation reason against an exact graph and render
ID, with an optional physical region ID for region-derived activation. Reasons
are internal diagnostics and test facts. They do not change the
`citry-client-graph/1` JSON shape.

`requires_client_graph` is derived from the frozen reason set. Under the
accepted graph-first policy, every reason in the enum requires Citry's graph
and owned Alpine runtime. There is deliberately no separate
`requires_owned_alpine` or `uses_alpine` boolean.

The data flow becomes:

```text
settled CitryRender
    -> analyze_client_activation()
        -> frozen reasons, reached output, graph snapshots, active boundaries
            -> prepare_ownership_manifest(analysis)
                -> OwnershipManifestArtifact
                    -> markers and caps
                    -> graph JSON
                    -> dependency manager
                    -> owned Alpine runtime
                    -> optional Events manifest and bootstrap
```

`ownership_manifest_required()` should disappear from serialization. If it is
temporarily retained for an internal caller, it must be a trivial query over
an existing analysis, never another tree walk.

## 3. Why the current code drifts

### 3.1 Settled render structure

[`citry_render.py`](../../packages/py/citry/citry/citry_render.py) retains
strings, nested renders, physical slot regions, placeholders, and component
identity until serialization. Dynamic attributes have resolved by then.
`on_render()` has selected its replacement and retired discarded ownership.
Cache replay has rebuilt fresh render IDs, region IDs, ownership records, and
parts.

This is the earliest common point that sees every normal HTML producer and the
latest point at which Citry still knows who owns each stretch of output.

### 3.2 The duplicated decision

[`serialize.py`](../../packages/py/citry/citry/serialize.py) currently calls
`ownership_manifest_required(root)` and then calls
`prepare_ownership_manifest(root)`. Both functions in
[`ownership_manifest.py`](../../packages/py/citry/citry/ownership_manifest.py)
walk the tree and maintain their own versions of the trigger list.

The second path also performs work that the first path cannot express: active
invocation endpoints, slot-region projection, and descendant isolation. A new
plain-Alpine check added only to the first path would load a graph whose
component boundaries were still missing. A check added only to the second
path would never run.

### 3.3 HTML scanning

The current Alpine checks are regular expressions over individual strings.
They can mistake comments, raw-text contents, and quoted examples for markup.
They can also miss a real start tag split across static text and a resolved
dynamic attribute part.

[`marker.rs`](../../crates/citry_html_transform/src/marker.rs) already has the
right low-level prior art. Its non-normalizing scanner understands start
tags, quoted attributes, comments, declarations, raw-text elements, void
elements, and malformed input without reserializing user HTML.

### 3.4 Runtime delivery

An `OwnershipManifestArtifact` already causes the dependency extension to
emit the graph and core dependency manager. The Events extension already
injects the combined pinned Alpine and Events bundle for a graph even when no
Events instance exists.

That packaging can stay in place. Runtime delivery should be a consequence of
the one artifact, not a new scan in either extension.

## 4. Chosen design

### 4.1 Add one HTML-aware attribute detector

Add one narrow Rust/PyO3 function with this contract:

```python
def find_alpine_attribute_spans(html: str) -> list[tuple[int, int]]: ...
```

Each pair is the start-inclusive, end-exclusive UTF-8 byte span of one Alpine
attribute name, returned in document order. Attribute names are ASCII at the
matched prefix, so every span is also a valid Python string boundary. Empty
input and input without a match return an empty list. Malformed HTML is
handled fail-soft and does not raise.

The helper must:

- compare HTML attribute names using ASCII case-insensitive matching;
- require at least one character after the prefix, so bare `x-`, `@`, and `:`
  do not count;
- accept boolean, quoted, unquoted, multiline, namespaced, and modified Alpine
  forms such as `x-cloak`, `x-on:click.window`, `@click.prevent`, and
  `:class`;
- inspect attributes on `script`, `style`, `textarea`, and `title` start tags
  while ignoring directive-looking text inside their bodies;
- ignore comments, CDATA, processing instructions, declarations, end tags,
  escaped example text, and mentions inside ordinary attribute values;
- copy `mark_html`'s fail-soft treatment of malformed input rather than
  introducing a new render error.

Refactor the private scanner enough that `mark_html` and the new detector use
the same tokenization rules. Do not copy the start-tag grammar into a second
Rust loop.

Do not change `mark_html`'s return tuple. Add a separate function so the
existing Rust and PyO3 contract stays compatible.

This additive PyO3 surface requires all of the following in the same stage:

- Rust implementation and export in `crates/citry_html_transform`;
- Rust lexer and regression tests;
- wrapper and module registration in `crates/citry_core_py`;
- the `_rust.pyi` declaration;
- the `citry_core.html_transform` re-export and `__all__` entry;
- Python binding-shape tests.

This is an Alpine-specific query exposed through Citry's existing HTML
inspection binding. Keeping the public input to one string avoids a broad
prefix-matching API with unclear empty-prefix and non-ASCII behavior. It does
not change the template parser or a language-specific template
implementation. No JavaScript, PHP, or Go binding currently mirrors this
HTML-transform API, so there is no cross-language API to update.

### 4.2 Scan complete frames with ownership labels

One rendered start tag can span several `CitryRender.parts`. The analysis must
not call the detector once per string.

It also must not scan a physical region without its surrounding HTML parser
state. A slot region may sit inside `textarea`, `script`, `style`, `title`, a
comment, or a quoted value. Scanning that region alone could mistake text for
a start tag.

Build one complete pre-marker frame for the serialization root, whether it is
transparent or not, plus one for each nested non-transparent component root.
Use the same part rules as `_build_frame()`:

- strings and interior renders stay in exact byte order;
- physical-region contents stay inline, with no caps yet;
- a nested component root becomes the same neutral `<template c-render-id>`
  placeholder that serialization uses, and the child gets its own frame;
- an extension `Placeholder` becomes its serializer-equivalent neutral
  template placeholder;
- nested transparent component output stays in the current frame.

Factor these traversal rules into one shared private projection helper used by
the activation planner and `_build_frame()`. Byte-lock both consumers against
the same fixtures. Do not let a second placeholder/interior-render policy grow
independently.

The projection records child candidates and their placeholder IDs. Count a
child as physically reached only when the same marker lexer recognizes that
placeholder in the complete parent frame. This matters when trusted
composition puts placeholder-looking bytes inside raw text or a comment,
where final serialization does not substitute the child. Align the
serializer's child stack with the same recognized-placeholder result so an
absent child cannot activate or enter the graph.

Alongside each frame's bytes, keep ordered, non-overlapping ownership spans. A
span identifies either the component-authored frame or the innermost physical
region that supplied those bytes. Nested region labels replace outer labels
for their byte range, while the ownership snapshot separately retains the
containing-region chain.

Call `find_alpine_attribute_spans()` once per complete frame. Map each returned
attribute-name span back to the label that covers its first byte. The complete
frame gives Rust the correct raw-text, comment, tag, and quoted-value state;
the side table gives Python the exact component or region observation.

A valid attribute name must sit inside one ownership label. If an attribute
name itself crosses a component or physical-region boundary, fail an internal
invariant with the involved frame and region IDs. Do not guess an owner. A
directive value may cross labels because ownership follows the attribute name,
not the JavaScript text in its value.

Child component output is scanned in the child's unit and excluded from the
parent's direct reasons. A child-only Alpine directive therefore activates the
child branch, not the parent or an unrelated sibling.

For a transparent serialization root, an Alpine observation inside a physical
region follows that region's recorded endpoint policy. Component-authored
Alpine bytes outside a region have no non-transparent component boundary to
own them. Under `document` or `fragment`, raise a pointed error naming the
transparent component and tell the author to render it inside a normal root
component. `simple` and `ignore` keep their intentional no-runtime behavior.
Do not silently assign those bytes to the transparent structural helper.

### 4.3 Freeze one analysis

The mutable builder validates occurrence uniqueness and records graph order,
reachable render IDs, transparent occurrences, reached physical regions,
complete frames, and byte ownership spans. It then snapshots each reached
ownership graph once.

After HTML inspection, one monotonic `require()` operation adds direct
activation records. A finalization pass applies relation rules and descendant
isolation exactly once. The result is frozen before manifest preparation.

The analysis should contain, at minimum:

```text
root Citry instance and mode
graph captures in physical order, each with one OwnershipSnapshot
reachable component occurrences and transparent occurrences
reached physical regions and their containing-region chain
direct activation observations with reason codes and optional region IDs
derived activation records for relation endpoints and isolation boundaries
the final client-active render-ID set
the derived requires_client_graph property
```

Use immutable tuples and frozen sets in the final object. Do not leave mutable
dictionaries reachable through a frozen dataclass.

The analysis is local to one `serialize()` call. Do not store it on a
component class, a cache artifact, or a live render for reuse. Different cache
variants, `on_render()` results, dynamic attributes, and dependency strategies
can make a later serialization reach a different answer.

Only the existing manifest artifact needs to enter `CitryContext.extra` for
the serialization hooks that consume it. Repeated serialization must replace
or remove that artifact as it does today.

### 4.4 Apply all activation rules in one place

Keep direct observations separate from derived active boundaries. A direct
observation says where Citry found a client feature. A derived record says
which render ID became active through a direct component, binding endpoint,
slot endpoint, or descendant-isolation step. Each derived record points back
to its originating observation, so tests and diagnostics can explain the
whole path.

For each reachable component occurrence, one
`_component_activation_reasons(...)` function returns all direct reasons from
the rendered Alpine observation, `$component`, Events, and State. No other
function may repeat that component trigger list. Component-tag bindings enter
the same observation collection from active invocation records because their
source and target relationship is graph data, not class metadata.

One `finalize_activation()` function then applies this exact rule table:

| Settled feature | Direct activation |
|---|---|
| Alpine attribute in component-authored output | Owning component occurrence |
| `$component` setup for a component class | That rendered occurrence |
| Events class | That rendered occurrence |
| State class | That rendered occurrence |
| Component-tag client binding | Source and selected target occurrences |
| Alpine in a template-authored supplied or fallback region | Template endpoint closure below |
| Alpine in detached Python or typed-default region | Detached endpoint closure below |

For every directly observed Alpine region, follow
`PhysicalRegionRequestRecord.containing_region_id` to the outermost reached
region in the same graph. This produces the Alpine-bearing region closure.
Cycles, missing containing regions, failed or retired regions, and a relation
to another graph remain errors under the existing v1 validation rules.

For each region in that closure, resolve its active logical fill and add the
following non-null render IDs:

- for `SourcePolicy.TEMPLATE`: the fill's `lexical_owner_render_id` and
  `receiver_render_id`, plus the region's `lexical_owner_render_id`,
  `receiver_render_id`, `transition_from_render_id`, and
  `result_owner_render_id`;
- for `SourcePolicy.PYTHON` and `SourcePolicy.TYPED_DEFAULT`:
  the fill's `receiver_render_id`, plus the region's `receiver_render_id`,
  `transition_from_render_id`, and `result_owner_render_id`. The lexical-owner
  fields must satisfy their existing detached-policy invariants and are never
  activated as an invented source.

Every non-null endpoint must be an active serialized instance in the same
captured graph. An inert outer region may still be omitted under the existing
same-graph render-hook rebase rule. An Alpine-bearing region cannot be dropped
as inert; if one of its required endpoints was omitted with the caller, keep
the existing pointed cross-graph or unavailable-source failure.

After direct and relation-derived activation, the existing logical-descendant
closure adds boundaries below every active occurrence. That preserves Citry's
scope isolation. Unrelated graph branches remain present in graph data when
the v1 protocol requires them, but they do not receive active root markers or
lifecycles.

Detached Python and typed-default content keep the accepted empty-base rule.
If their settled region contains Alpine, they now activate enough receiver
ownership to install that isolated base. They do not inherit receiver data and
do not acquire a fictional caller scope. Detached content without Alpine
remains server-only.

### 4.5 Make the artifact the only runtime trigger

For `document` and `fragment`, serialization will:

1. build `ClientActivationAnalysis` once;
2. skip manifest work when `requires_client_graph` is false;
3. pass the same analysis to `prepare_ownership_manifest()` when it is true;
4. use the resulting artifact for all caps, markers, graph JSON, and runtime
   delivery.

`prepare_ownership_manifest()` must consume the analysis's graph snapshots,
reached records, and final active set. It must not walk the root again to
rediscover triggers.

The Events extension still decides whether to emit an Events manifest and
bootstrap from its captured Events entries. It decides whether to emit the
owned Alpine bundle from the ownership artifact only. Events entries without
an artifact become an internal invariant error instead of a second fallback
activation path.

Apply the symmetric rule to dependency calls. Resolved per-instance
`$component` calls under `document` or `fragment` require an ownership
artifact. Calls without one are an internal invariant error, not an
independent reason to emit a manager-only manifest. Component asset URLs may
still require only the dependency manager so an initial document can mark
them loaded for later fragments; they do not select the Alpine bundle.

The dependency extension remains the delivery owner. A graph in
`before_manifest` causes the document manager or fragment preloader to be
emitted. The graph revision continues to link the ownership, dependency, and
Events packages. Only artifact presence selects the combined Alpine bundle.

No client runtime change should be needed for the basic activation rule. The
existing client graph already knows how to create boundaries, start Alpine,
and project slot sources.

## 5. Accepted behavior and limits

### 5.1 Full graph activation is intentional

A runtime-only alternative would make plain Alpine run, but it would leave
component inheritance dependent on unrelated page contents. The same nested
component could inherit an outer `x-data` when it is the only interactive
feature, then become isolated after another component adds Events. That is the
contextual behavior this work is meant to remove.

Plain rendered Alpine therefore activates the full graph-first ownership
model. This has visible consequences:

- nested Citry components become Alpine scope boundaries;
- graph markers and payload appear on pages that previously kept inert Alpine
  attributes without a runtime;
- a native Alpine structural template cannot clone a server-rendered
  client-active Citry component, because cloning would duplicate graph
  identity. Use server-side `<c-if>` and `<c-for>` around Citry component
  instances.

These are accepted ownership rules, not accidental packaging effects. Browser
tests must lock them so they cannot change indirectly.

### 5.2 Custom prefixes and programmatic directives

The automatic detector covers Alpine's standard `x-*`, `@*`, and `:*`
attribute forms. It cannot infer:

- a custom Alpine prefix;
- directives installed later with `Alpine.bind()` or client code;
- an extension that inserts new interactive HTML only during
  `on_serialize`, after graph ownership was chosen.

`$component`, Events, State, or a component-tag client binding still activates
the runtime for programmatic behavior. A public explicit
`requires_alpine` extension contribution or custom-prefix setting needs its
own API design and is not part of this change.

Normal component hooks are covered when they finish before serialization,
including `on_attrs_resolved`, slot rendering hooks, `on_component_rendered`,
and `on_render()`.

### 5.3 Component-less output

A hand-built `CitryRender` with no owning component has no Citry instance that
can emit dependencies or describe a component boundary. Keep its current
no-runtime behavior. The normal public component render path is the supported
automatic-activation path.

### 5.4 Malformed HTML

Follow `mark_html`'s forgiving behavior. A malformed or truncated tag must not
produce a new server exception. The detector only counts a directive when the
shared lexer recognizes it as an attribute on a start tag. It does not fall
back to a broad string search.

## 6. Alternatives rejected

### 6.1 Load Alpine without a client graph

Rejected because component scope isolation and slot behavior would still
depend on whether another feature happened to request a graph. It also creates
two browser startup modes that future features would have to keep aligned.

### 6.2 Broaden the Python regular expression

Rejected because a regular expression over strings cannot reliably separate
real attributes from comments, raw text, quoted examples, or tags split across
render parts.

### 6.3 Instrument every HTML producer

Rejected as the primary mechanism. Static templates, dynamic attributes,
`c-bind`, control flow, slots, trusted strings, `on_render()`, and cache replay
would each need to remember to report activation. That producer list will
grow, and cached metadata would need versioning. Settled-output inspection
covers them through one path.

### 6.4 Change `mark_html`'s return value

Rejected because `mark_html` is an existing Rust and PyO3 contract and it runs
after the graph decision has already affected caps and root markers. A
separate detector can share its lexer without changing that return shape.

### 6.5 Run the marker and cap pass speculatively

Rejected because `_build_frame()` needs the ownership artifact before it can
insert component and region caps. Running the final marker pass with a guessed
artifact and then repeating it would entangle activation with output mutation.
The chosen lightweight projection assembles only unmarked bytes, child
placeholder facts, and ownership labels. Normal serialization applies markers
and caps once after the analysis is frozen.

### 6.6 Move Alpine out of the Events-named bundle now

Rejected as unrelated packaging churn. The bundle already installs Alpine for
graphs without Events. Renaming routes or splitting the generated bundle can
be reviewed separately.

## 7. Implementation stages

Each stage ends with focused tests and an observe-then-lock check. Do not start
the next stage while the current behavior is ambiguous.

### Stage 0: lock the defect and baseline

- Add a plain-Alpine-only server and browser fixture with no `$component`,
  Events, State, client binding, or slot trigger.
- Record that the current output has no graph/runtime and the click stays
  inert, then turn that observation into the failing target test.
- Add reproductions for a resolved `c-bind` Alpine attribute and the current
  comment/script/quoted-value false positives inside a scanned physical
  region. Component-authored plain Alpine is not scanned today, so it cannot
  demonstrate that baseline by itself.
- Record current static-page bytes and the existing 325-instance measurements
  from `test_client_performance_payload.py` and
  `alpinejs/a10_performance.md` before changing selection semantics.

**Gate:** every new target failure is caused by activation, not by a missing
browser route, test fixture dependency, or unrelated runtime error.

### Stage 1: add the shared Rust detector

- Refactor the marker lexer so marking and inspection share start-tag and
  raw-text rules.
- Add `find_alpine_attribute_spans()` and its Rust tests, including exact UTF-8
  byte spans and ordered results.
- Complete the PyO3 wrapper, registration, type stub, Python re-export, and
  boundary tests.
- Prove byte-for-byte that existing `mark_html` fixtures do not change.

**Gate:** the detector passes positive and false-positive cases in Rust and
through Python, and the existing marker suite is unchanged.

### Stage 2: build the settled activation analysis

- Add the reason enum, private builder, and immutable analysis types.
- Walk the selected render tree once, assembling complete component frames
  with ownership-labeled byte spans and capturing each graph snapshot once.
- Apply direct reasons, slot policy, invocation endpoints, and descendant
  isolation through one finalization path.
- Remove the regex scanners and duplicated trigger discovery.
- Change manifest preparation to consume the analysis.

**Gate:** unit tests can assert not only that a graph exists, but why each
occurrence is active. No trigger is rediscovered inside manifest generation.

### Stage 3: connect serialization and delivery

- Replace `ownership_manifest_required()` in `serialize_render()` with the
  one analysis.
- Make artifact presence the sole owned-Alpine bundle trigger.
- Preserve Events manifest/bootstrap selection as a separate content choice.
- Make Events entries or per-instance dependency calls without the required
  artifact fail as internal invariant violations. Preserve manager-only asset
  URL emission.
- Lock unmounted and mounted `document`, mounted and unmounted `fragment`,
  `simple`, and `ignore` behavior.
- Verify repeated serialization clears or replaces the artifact correctly.

**Gate:** plain Alpine runs alone for documents and fragments, static output
stays graph-free, and the runtime starts once.

### Stage 4: ownership, cache, and lifecycle acceptance

- Lock component-authored, template-fill, fallback, detached Python, and
  typed-default ownership rules.
- Exercise child-only, parent-with-descendants, unrelated sibling,
  transparent, multi-root, rootless, mirrored, and nested-region shapes.
- Exercise cache miss, cache replay, variant changes, and repeated
  serialization without adding activation metadata to cache artifacts.
- Verify selected and discarded `on_render()` output.
- Run the plain-Alpine document and fragment cases in Chromium, Firefox, and
  WebKit.

**Gate:** Alpine behavior no longer changes when an unrelated component is
added or removed, and detached content can use local `x-data` without seeing
receiver data.

### Stage 5: payload, documentation, and closeout

- Add a deterministic large plain-Alpine tree and a matching static tree to
  the payload suite.
- Record raw and gzip graph/document costs. The combined runtime byte budget
  should not grow for a server-side detection change.
- Update the normative, implementation, research, and public docs listed in
  section 10.
- Run an independent adversarial review, focused tests, the three-browser
  compact gate, docs checks, and `python scripts/check.py --reporter agent`.

**Gate:** measured budgets and all documentation describe the implemented
behavior, not the proposed behavior.

## 8. Test matrix

### 8.1 Detector tests

Positive cases:

- `x-data`, `x-text`, `x-show`, `x-model`, `x-bind:class`, and `x-on:click`;
- `@click`, `:class`, boolean `x-cloak`, modifiers, mixed ASCII case,
  whitespace, quoted and unquoted values;
- attributes on void elements, `<template>`, SVG, table, and select content;
- an Alpine start-tag attribute on a raw-text element itself.

Negative cases:

- comments, CDATA, declarations, processing instructions, and end tags;
- escaped examples such as `&lt;button x-data&gt;`;
- directive-looking text in `script`, `style`, `textarea`, and `title`;
- an ordinary attribute value containing `<button x-data>`;
- `data-x-data`, `hx-data`, `xml:x-data`, bare `x-`, bare `@`, and bare `:`;
- malformed input that never presents a recognized attribute.

Python frame-attribution tests must also put a physical region boundary inside
raw-text content, a comment, and a quoted attribute value. Directive-looking
region text must remain inert because the complete surrounding frame controls
HTML parsing.

### 8.2 Settled-output tests

- static attributes and each shorthand activate without another feature;
- dynamic `c-x-*`, `c-@*`, `c-:*`, and `c-bind` additions activate;
- a winning dynamic removal with `None` or `False` does not activate;
- `on_attrs_resolved` additions and removals decide from final output;
- a tag split across strings and interior renders is scanned as one tag;
- the returned attribute-name byte span maps to exactly one component or
  innermost-region ownership label;
- an attribute name crossing an ownership label fails the internal invariant
  instead of choosing an arbitrary owner;
- Alpine in a directly serialized transparent root region follows its recorded
  endpoints, while component-authored Alpine with no physical region raises
  the pointed missing-owner error under `document` and `fragment`;
- selected control-flow branches activate and unselected branches do not;
- returned `on_render()` content activates and discarded content does not;
- a child placeholder not recognized by the marker lexer inside raw text or a
  comment is absent from both activation analysis and final child joining;
- trusted HTML and cache replay use the same detector;
- repeated `document -> simple -> document` and `fragment -> ignore`
  serializations have no stale decision.

### 8.3 Ownership tests

- a child-only directive activates the child branch;
- a parent directive adds descendant isolation boundaries;
- unrelated siblings stay outside the active lifecycle;
- template-supplied and fallback regions preserve their existing source rules;
- Alpine-bearing detached Python and typed-default regions activate an empty
  isolated base, while plain detached content stays server-only;
- nested and mirrored regions propagate through the exact recorded path;
- cross-graph and omitted-caller failures stay pointed;
- `simple` and `ignore` add no graph markers.

Tests should assert reason codes as well as rendered markers. This makes a
missing rule fail at the single authority rather than later as a vague runtime
symptom.

### 8.4 Delivery and browser tests

- an unmounted document inlines the owned runtime;
- a mounted document uses the runtime route;
- a mounted fragment carries graph JSON, the dependency preloader, and the
  runtime URL, with matching revisions and no Events manifest when Events are
  absent;
- an unmounted Alpine-bearing fragment raises the existing mounted-integration
  error;
- a plain-Alpine fragment inserted into a manager-only page initializes and
  handles a click;
- repeated fragments do not start Alpine twice;
- a foreign Alpine copy keeps the existing duplicate warning;
- Events entries without an artifact and `$component` calls without an
  artifact fail the server-side invariants in focused tests;
- asset-only document bookkeeping may still emit the dependency manager
  without an Alpine bundle or graph;
- nested components are isolated without `$component` hiding the result;
- native structural cloning of a client-active server component keeps its
  existing pointed rejection.

The primary browser fixture must not contain `$component`, Events, State,
component-tag client bindings, or an Alpine-bearing slot fill. Any of those
would let the old contextual behavior pass.

### 8.5 Cache and payload tests

- component cache miss and hit both activate the same settled Alpine output;
- Alpine and static cache variants do not share stale activation in either
  order;
- fragment cache replay preserves Alpine activation and region ancestry;
- a large static page remains graph-free;
- a matching large plain-Alpine page has deterministic raw and gzip budgets;
- the plain-Alpine graph contains no synthetic Events entries, dependency
  calls, or client bindings;
- serialization remains byte-for-byte repeatable.

Do not add a wall-clock threshold for the Rust scan in normal CI. Use the
deterministic payload scenario and the existing browser performance harness;
record a focused benchmark only if the new prepass is measurable.

## 9. What would falsify this design

Stop and revisit the design instead of adding special cases if any of these is
observed:

- settled render parts cannot reconstruct a real start tag without crossing
  an ownership boundary that the current model cannot assign;
- cache replay drops the structural information needed to distinguish a
  component unit from a physical region;
- the analysis needs a second render-tree trigger scan during manifest
  generation to stay correct;
- ordinary Alpine activation changes a required native `x-if`, `x-for`, or
  teleport workflow in a way the accepted server-component identity rule
  cannot support;
- large static pages regress materially despite producing no activation
  reasons;
- a graph snapshot can change between analysis and manifest generation
  without the existing unchanged assertion catching it;
- the Rust helper cannot share marker tokenization without changing existing
  `mark_html` output.

If an ownership boundary can split a valid start tag, prefer a deliberate
serializer planning pass with an explicit chunk protocol. Do not fall back to
regexes or producer-specific flags.

## 10. Documentation updates after the code lands

The implementation change and these updates belong in the same reviewed
change. Historical probes should remain as history, with new evidence added
after them.

### 10.1 Normative architecture

- [`alpinejs.md`](alpinejs.md): update the trigger model, settled-output
  analysis, component and slot ownership rules, detached-content activation,
  startup behavior, current implementation table, and acceptance matrix.
- [`client graph v1 spec`](../../packages/protocol/client_graph/v1/spec.md):
  update **When Citry sends the graph**. State that the selection rule changed
  but the v1 JSON shape did not, so no protocol version bump is needed.
- [`component_slots.md`](component_slots.md): update section 10.1 for Alpine in
  detached Python and typed-default content.
- [`dependencies.md`](dependencies.md): update document and fragment runtime
  selection, `simple` and `ignore`, and the mounted-fragment failure.
- [`events.md`](events.md): make the client-active trigger summary point to the
  shared analysis and stop implying that Events entries are a runtime fallback.
- [`component_on_render.md`](component_on_render.md): state that activation
  follows the selected settled replacement.
- [`caching.md`](caching.md): state that activation is recalculated after
  replay and is not persisted in cache artifacts.
- [`component_provide.md`](component_provide.md): replace ambient-context-only
  detector wording with the shared rendered-attribute analysis.
- [`citry_html_transform/AGENTS.md`](../../crates/citry_html_transform/AGENTS.md):
  update its entry-point and export inventory for the new scanner query.
- [`citry_core_py/README.md`](../../crates/citry_core_py/README.md): update the
  binding example and module inventory if they still enumerate individual
  HTML-transform functions when the code lands.
- [`CitryRender.serialize()`](../../packages/py/citry/citry/citry_render.py#L195-L207):
  update the public strategy docstring, which currently describes automatic
  client startup through `$component` only.

### 10.2 Implementation ledgers and evidence

- [`alpinejs_plan.md`](alpinejs_plan.md): add a post-A10 landed work package
  linking to this focused plan. Reconcile A7 and O3 without rewriting their
  historical result silently.
- [`alpinejs/a2_client_graph.md`](alpinejs/a2_client_graph.md): update the
  exact graph-emission trigger list.
- [`alpinejs/a10_conformance.md`](alpinejs/a10_conformance.md): add the
  detector, strategy, fragment, cache, slot, and browser coverage.
- [`alpinejs/a10_performance.md`](alpinejs/a10_performance.md): add the measured
  plain-Alpine and static comparison if the payload scenario lands.
- [`docs_content.md`](docs_content.md): mark settled Alpine activation as a
  landed prerequisite after verification.
- [`getting_started_journey.md`](docs_content_research/getting_started_journey.md):
  preserve the defect rationale but update current behavior and blocker status.
- [`evidence_log.md`](docs_content_research/evidence_log.md): retain the old
  contextual-activation probe and append the fixed server/browser results.
- [`ui_research/citry-baseline.md`](ui_research/citry-baseline.md): refresh the
  dated active baseline for automatic Alpine and detached-region activation.

### 10.3 Public behavior

- [`advanced/alpine-runtime.md`](../../docs_site/content/advanced/alpine-runtime.md):
  verify its existing forward-looking claim, then document exact settled-output
  detection and all four dependency strategies.
- [`concepts/client-interactivity.md`](../../docs_site/content/concepts/client-interactivity.md):
  update the detached-content statement and automatic activation explanation.
- [`advanced/html-fragments.md`](../../docs_site/content/advanced/html-fragments.md):
  lock its Alpine-only mounted-fragment guidance to the implemented test.
- [`README.md`](../../README.md): verify the fragment and plain-Alpine summary.
- [`CHANGELOG.md`](../../CHANGELOG.md): record that plain rendered Alpine now
  activates Citry's owned runtime and component isolation without an unrelated
  client feature. Mention the duplicate-Alpine implication for users who load
  their own copy.

The new Getting started browser-interactivity page remains separate content
work. This implementation unblocks it but does not absorb that authoring task.

## 11. Verification commands

Focused checks during implementation:

```bash
cargo test -p citry_html_transform -p citry_core_py
uv run pytest packages/py/citry_core/tests/test_html_transformer.py
uv run pytest packages/py/citry/tests/test_ownership_manifest.py
uv run pytest packages/py/citry/tests/test_deps_emission.py packages/py/citry/tests/test_deps_fragments.py
uv run pytest packages/py/citry/tests/test_ext_cache.py packages/py/citry/tests/test_ext_cache_replay.py
uv run pytest packages/py/citry/tests/test_client_performance_payload.py
```

Run the dedicated activation browser file in Chromium, Firefox, and WebKit,
then the existing Alpine ownership, slot, fragment, cache replay, and
structural suites in all three engines. Run docs link/build checks after the
same-change documentation updates.

Close with:

```bash
python scripts/check.py --reporter agent
```

An independent reviewer should specifically look for a second trigger list,
per-string scanning, cache-persisted activation, missing detached-region
ownership, an Events-entry runtime fallback, and claims that were updated in
one design document but left stale elsewhere.
