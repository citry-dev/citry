# ComponentRange implementation plan

Status: implemented  
Date: 2026-08-04  
Normative design: [`component_ranges.md`](component_ranges.md)

This plan records the compiler-output migration and its full downstream blast
radius before production code changes begin. It is subordinate to the
normative semantics in `component_ranges.md`: when the two disagree, the
design document wins.

All six stages below are complete. Focused compiler, runtime, protocol,
cache, dependency, client, and three-browser acceptance suites cover the
landed behavior; closeout still uses the repository-wide check as the final
integration gate.

## Prior art

The implementation extends existing ownership machinery; it does not create a
second representation of components.

- `crates/citry_template_parser/src/grammar.pest`, `src/grammar.rs`, and
  `docs/design/template_grammar.md` already recognize `#c-key` and `#c-ignore`
  as meta attributes. No grammar rule or AST shape needs to change.
- `crates/citry_template_parser/src/compiler.rs:931`
  (`compile_component_node`) already separates component metadata from normal
  kwargs and appends an optional eighth `ComponentNode` argument for
  `#c-key`. `src/compiler.rs:24` documents that source contract.
- `packages/py/citry/citry/nodes/__init__.py:987` (`ComponentNode`) evaluates
  the current key expression; `packages/py/citry/citry/constness.py` clones
  that node state for constant templates.
- `packages/py/citry/citry/ownership.py:197`
  (`ComponentInvocationRecord`) and
  `packages/py/citry/citry/ownership_manifest.py` already own and serialize
  `morph_key`. The key is therefore already logical invocation metadata, even
  though the browser currently plans only keyed ranges.
- `packages/protocol/client_graph/v1/spec.md:396`, the JSON schema, and the
  canonical Python and TypeScript record packages define the strict
  `NestedComponent` wire record. The protocol has no optional-field convention:
  a new nullable field must be required and present on every valid record.
- `packages/py/citry/citry/ext/dependencies/client/citry.js:4425` begins the
  current keyed-component planner. Its ownership normalizer, range links,
  slot-region links, caps, sentinels, and replacement transaction are the
  physical substrate for ComponentRange.
- `packages/py/citry/citry/ext/events/client/citry-events.js:7277` stages an
  Events manifest before the fragment transaction, while
  `packages/py/citry/citry/ext/dependencies/client/citry.js:6129` stages
  dependency calls. Both currently assume the whole incoming revision will be
  adopted.
- `packages/py/citry/citry/ext/dependencies/emission.py:527`
  (`_emit_fragment`) currently renders `before_manifest` dependencies as live
  tags before the dependency manifest. That is unsafe for an incoming branch
  which an old `#c-ignore` barrier later excludes.
- `packages/py/citry/citry/ext/cache/artifact.py:20` fixes the strict render
  cache artifact at version 1; `ext/cache/replay.py` exports and decodes
  invocation metadata without a morph mode.
- `docs/design/alpinejs/spike-keyed-component-ranges.md` proved that the
  existing ownership comments can move a multi-root range, but it deliberately
  did not solve unkeyed matching, range ignore, slot mirrors, or transactional
  graph retention.

## Chosen design

### 1. Compiler metadata envelope

`ComponentNode` keeps its existing seven arguments byte-for-byte when there is
no range or element metadata. When metadata exists, its eighth argument becomes
a tagged tuple with a canonical entry order:

```python
# A normal component or runtime <c-component>
ComponentNode(..., (
    "range",
    ("key", ExprHtmlAttr(...)),
    ("morph", "ignore"),
))

# A runtime <c-element>; both directives remain ordinary element semantics
ComponentNode(..., (
    "element",
    ("key", ExprHtmlAttr(...)),
    ("morph", "ignore"),
))
```

Absent entries are omitted; the key entry precedes the morph entry regardless
of source order. An ignore-only range is
`("range", ("morph", "ignore"))`. The tagged form lets the runtime distinguish
logical range metadata from private metadata which must be materialized on a
dynamic ordinary element. It also leaves old metadata-free generated source
unchanged.

The compiler will classify the metadata locus explicitly:

- user component and runtime `<c-component>`: `range`;
- runtime `<c-element>`: `element`;
- static `<c-element>`: compile as the resolved ordinary element, using the
  ordinary attribute path.

`#c-ignore` remains a valueless directive. Structural tags continue to reject
it. A normal component never receives either meta attribute as a kwarg and
never projects either attribute to a root element.

The exact Python constructor contract is:

```python
type ComponentNodeMetadataEntry = (
    tuple[Literal["key"], ExprHtmlAttr]
    | tuple[Literal["morph"], Literal["ignore"]]
)
type ComponentNodeMetadata = tuple[
    Literal["range", "element"],
    *tuple[ComponentNodeMetadataEntry, ...],
]

ComponentNode(
    source,
    position,
    attrs,
    body,
    used_vars,
    name,
    contains_fills,
    metadata: ComponentNodeMetadata | None = None,
)
```

The constructor parses the tuple once into `_metadata_locus`, `key`, and
`morph_mode`. It rejects a non-tuple envelope, an unknown locus, a malformed
entry, an unknown entry name, duplicate `key`/`morph` entries, a non-
`ExprHtmlAttr` key payload, and any morph payload other than `"ignore"` with a
`TypeError`. `metadata=None` produces `_metadata_locus=None`, `key=None`, and
`morph_mode=None`. `constness._precompute_into` clones the original `metadata`
tuple, not reconstructed fields.

These are the exact compiler goldens (including Python tuple commas):

```python
# key only
[ComponentNode(source, (0, 49,), (StaticHtmlAttr(source, (25, 35,), """title""", """Hi""", ()),), ["""body""",], ("item",), """card""", False, ("range", ("key", ExprHtmlAttr(source, (8, 24,), """#c-key""", """item.id""", ("item",)),),)),]

# ignore only
[ComponentNode(source, (0, 20,), (), [], (), """card""", False, ("range", ("morph", "ignore",),)),]

# both; canonical key-then-morph output despite ignore-first source order
[ComponentNode(source, (0, 31,), (), [], ("k",), """card""", False, ("range", ("key", ExprHtmlAttr(source, (18, 28,), """#c-key""", """k""", ("k",)),), ("morph", "ignore",),)),]

# dynamic ordinary element
[ComponentNode(source, (0, 45,), (ExprHtmlAttr(source, (11, 21,), """c-is""", """tag""", ("tag",)),), [], ("tag", "k",), """element""", False, ("element", ("key", ExprHtmlAttr(source, (22, 32,), """#c-key""", """k""", ("k",)),), ("morph", "ignore",),)),]

# metadata-free output stays byte-identical
[ComponentNode(source, (0, 21,), (StaticHtmlAttr(source, (8, 18,), """title""", """Hi""", ()),), [], (), """card""", False),]
```

### 2. Python runtime and server ownership

`ComponentNode` normalizes the tagged tuple into private immutable metadata.
For a range locus it evaluates `#c-key` once and records:

- `None` as no key;
- `False`, `0`, and `""` as real keys after string conversion;
- `morph_mode="ignore"` for `#c-ignore`, otherwise `None`.

For a dynamic-element locus, evaluating the key produces the exact immutable
carrier
`_ElementMorphMetadata(key: str | None, morph_mode: Literal["ignore"] | None)`.
`CitryElement.element_morph_metadata` carries it to the instantiated dynamic
component, whose private `_element_morph_metadata` field is set by
`component_render._render_one` before input hooks run. `components/dynamic.py`
appends ` data-citry-key=":{escape(key)}"` when `key is not None` and
` data-citry-morph="ignore"` when the mode is `"ignore"`, after ordinary attr
merging and extension rewrites. Thus `None` omits a key while `False`, `0`, and
`""` emit `:False`, `:0`, and `:` respectively. When the corresponding private
metadata is active, `_format_element_attrs` rejects an ordinary
`data-citry-key` or `data-citry-morph` both before and after
`on_attrs_resolved`; this catches literal/dynamic/`c-bind` contributions and
extension injection before HTML with duplicate attributes can be produced.
Tests cover both injection paths. The private fields are not user kwargs and
cannot be overwritten by `c-bind` or `on_attrs_resolved`.

`ComponentInvocationRecord`, ownership graph construction, constant-template
cloning, and ownership-manifest emission gain `morph_mode`. Range-directive
presence becomes one shared predicate used by activation and manifest
emission, so ignore-only ranges cannot be optimized away.

### 3. Strict protocol and cache migration

Every `NestedComponent` record gains required
`morphMode: "ignore" | null`. Schema, prose spec, Python records, TypeScript
types and validators, canonicalization corpus, constraint-ownership inventory,
fixtures, fixture signatures, shipped Python copy, and embedded browser
validator move together.

The pre-1.0 render-cache artifact remains version 1. Its invocation records
require `morph_mode` with the closed value set `null | "ignore"`; no default is
applied during decode. Other versions remain safe cache misses. Boundary
invocations remain owned by the live caller and are not overwritten by replay.

### 4. One immutable, ancestor-ordered morph plan

The browser replaces the keyed-only prepass with a pure mixed planner. The
planner consumes the old and incoming ownership revisions plus detached
incoming DOM and produces all decisions before any live mutation:

- logical component matches, retention, replacement, removal, and insertion;
- accepted incoming and retained old render/invocation/fill/slot-region IDs;
- excluded incoming records and dependency owners;
- physical range, slot-region, root-group, and ordinary-element operations for
  every placement/mirror;
- ordinary `#c-ignore` barriers and the transitive retention closure for shared
  logical records projected through those barriers.

The normalizer records stable direct-child logical order. At each matched
parent the planner performs these phases in this order:

1. build preliminary old/incoming mixed physical pairs and discover provisional
   component candidates without committing logical correspondence;
2. use the old side of those pairs to seed ordinary-element and ComponentRange
   ignore barriers, then expand the shared-record retention closure to a fixed
   point;
3. remove all retained old and excluded incoming endpoints from the active
   pool;
4. reserve keyed active children by `(classId, morphKey)`;
5. take the complete remaining old and incoming direct-child sequences in
   invocation order and zip them position by position; accept a pair only when
   both are unkeyed and have the same class;
6. never forward-scan, regroup by class, retry, or return a closure-removed
   endpoint to the pool.

For example, remaining unkeyed old `[A, B]` and incoming `[B, A]` produce two
replacements. They do not preserve both instances by grouping the lists by
class. Tests pin this example.

The physical planner walks ancestors before descendants and treats component
ranges, slot regions, and ordinary nodes as peers. An old ordinary element
with `#c-ignore` is paired as an opaque barrier: the element itself may receive
the framework's private marker repair, but author attributes, descendants,
form state, Alpine state, and event state remain untouched. A range ignore
retains the entire logical ComponentRange and every physical projection of its
retention closure.

The applier consumes only the frozen plan. It must not discover new matches or
consult mutable DOM state for policy while applying operations.

### 5. Transaction phases and side-effect boundary

Fragment adoption becomes:

1. parse and prepare detached HTML;
2. stage strict graph and Events data without installing descriptors, anchors,
   hooks, or dependencies;
3. compute the mixed morph plan and accepted/retained owner sets;
4. mutate DOM according to the plan;
5. commit accepted ownership, Events descriptors/anchors, routes, caps, and
   dependencies;
6. discard excluded incoming state without surfacing it as an application
   error.

Events descriptors live in
`Map<graphRevision, Map<classId, ClassDescriptor>>`; every anchor stores the
descriptor revision it accepted. A retained anchor continues resolving props,
callbacks, validation, and State through that revision across any number of
later transactions. A descriptor revision is pruned only when no live anchor,
route, pending call, retained physical branch, or other ownership liveness root
references it. Old hooks are cleanup guards, not the source of ignore policy.

The graph-linked dependency manifest changes only for fragment transactions.
Its exact owner-aware shape is:

```json
{
  "markLoaded": {"js": [], "css": []},
  "fetch": {
    "js": [["<base64 descriptor JSON>", ["<base64 owner render id>"]]],
    "css": [["<base64 descriptor JSON>", null]]
  },
  "calls": [["<base64 class id>", "<base64 render id>", null]],
  "cssInstances": [["<base64 class id>", "<base64 render id>"]],
  "beforeManifest": ["<base64 dependency descriptor JSON>"],
  "graph": "<revision>"
}
```

Each component-derived fetch descriptor has a sorted, non-empty, deduplicated
owner list. Server-side deduplication unions owner sets while preserving the
first descriptor position. `calls` and `cssInstances` use their existing
render-ID entries as ownership. Entries added by the global
`on_dependencies` hook have no component owner and instead go into fetch with
an owner value of `null`; they activate only if the plan accepts at least one
incoming render ID. A component-derived descriptor with no accepted owner is
discarded. `calls` and `cssInstances` are filtered to accepted incoming render
IDs. Retained branches keep their old loaded assets, calls, and CSS-instance
claims; retirement uses the existing live-instance/reference cleanup and runs
exactly once when their last retained owner leaves.

The second fetch-tuple item is exactly
`null | ["<base64 owner render id>", ...]`. Detached validation rejects a
non-two-item tuple, a non-string descriptor, malformed descriptor JSON, an
owner value other than `null` or an array, an empty owner array, a non-string
or invalid-base64 owner, a duplicate owner, or an owner render ID absent from
the prepared graph. Owner arrays must already be sorted by decoded render ID;
out-of-order input is rejected rather than canonicalized in the browser.

Fragment `before_manifest` entries no longer render as live arbitrary tags.
The server keeps framework-owned ownership and Events
`<script type="application/json">` manifests as the existing top-level inert
tags, but encodes every other hook-added entry through `Dependency.render_json`
into required `beforeManifest`. Fragment parsing recognizes only those
top-level framework JSON scripts and the dependency script as machinery, so no
staging wrapper can become a morph root. It strictly validates all
`beforeManifest` descriptors while detached, creates no elements, and records
their order. After DOM application succeeds and at least one incoming render
ID is accepted, commit reconstructs fresh elements in source order immediately
before fetch/call activation. An all-excluded transaction creates none. Any
pre-commit failure discards the decoded values; a reconstruction or activation
failure follows the existing post-mutation fail-closed cleanup. Document-mode
emission remains unchanged because it has no branch-exclusion transaction.

`swap="replace"` remains an explicit physical replacement and bypasses ignore.
A same-class self-render using replace preserves its external logical metadata
contract while replacing the physical range.

## Cross-binding audit

This change alters generated Python source but does not alter the parser AST,
the `LangImpl` trait, or a PyO3-exposed type.

| Surface | Required action |
|---|---|
| `src/lang/python.rs` | No method change; existing tuple/string/constructor emitters encode the envelope. |
| `src/lang/js.rs` | No change; structural stub does not consume Python node codegen. |
| `src/lang/php.rs` | No change; structural stub does not consume Python node codegen. |
| `src/lang/go.rs` | No change; structural stub does not consume Python node codegen. |
| `src/lang/rust.rs` | No change; structural stub does not consume Python node codegen. |
| `crates/citry_core_py/src/lib.rs` | No registration change; AST/PyO3 surface is unchanged. |
| `packages/py/citry_core/citry_core/_rust.pyi` | No signature change; no exposed Rust class changes. |
| Python wrapper under `packages/py/citry_core` | No change; compiler returns the same generated-source type. |
| Rust tests | Update compiler goldens, placement errors, determinism, and no-metadata compatibility. |
| Python tests | Update `ComponentNode`, dynamic element, ownership, manifest, protocol, cache, fragment, Events, and browser suites. |

The generated-source format change is intentionally Python-runtime-specific;
the five-language compiler abstraction itself remains unchanged.

## Implementation stages and gates

1. **Latent metadata foundation.** Add the compiler envelope, runtime
   normalization, server ownership field, strict protocol migration, and cache
   v3 while deliberately leaving `parser.validate_meta_attr_placement`'s
   component-ignore rejection in place. Compiler ignore cases use hand-built
   AST unit tests; server/browser fixtures may construct `morphMode="ignore"`
   directly. Gate: metadata-free parser behavior plus compiler/node/ownership/
   protocol/cache suites pass, and user templates still cannot opt a component
   range out.
2. **Pure browser planner.** Add logical child order, preliminary physical
   candidates, ignore closure, closure-pool removal, keyed reservation,
   positional unkeyed matching, mirror/slot plans, and parity canaries against
   the pinned Alpine behavior when every incoming branch is accepted. Gate:
   planner unit and synthetic DOM tests pass, including old `[A, B]` / incoming
   `[B, A]`, without enabling component `#c-ignore` syntax.
3. **Transactional adoption.** Split prepare/plan/apply/commit/discard; subset
   ownership replacement; revision-scoped Events staging; owner-aware fetches;
   descriptor-backed `beforeManifest` staging. Gate: accepted-all regressions
   plus excluded-branch DOM, Events, callback, fetch, inline-script, style, and
   cleanup non-observability tests pass.
4. **Syntax enablement and end-to-end semantics.** Only after stages 2 and 3
   pass, change `parser.validate_meta_attr_placement` to accept `#c-ignore` on
   user components, `<c-component>`, and `<c-element>` while structural tags
   still reject it. Replace the hand-built compiler cases with source-parsed
   goldens and add single-root, multi-root, nested, keyed/unkeyed,
   wrapper-change, root-level ordinary ignore, slot/mirror, self-render,
   replace-bypass, and form/Alpine/Events preservation tests across Chromium,
   Firefox, and WebKit.
5. **Artifacts and documentation.** Rebuild canonical protocol packages and
   embedded validators, the dependency client and Events bundle as required,
   fixture hashes, shipped Python protocol copy, playground copy when its
   source bundle changes, payload budgets, syntax docs, and architecture
   indexes.
6. **Verification and review.** Run focused Rust, Python, protocol, Node, and
   cross-browser suites, then `python scripts/check.py`. Classify any failures
   against the pre-existing dirty-worktree baseline. A fresh high-effort agent
   performs adversarial review before delivery.

## Alternatives considered

### Project component metadata to a root element

Rejected. It gives a virtual component the identity and ignore policy of one
physical root, fails for multi-root and wrapper-changing components, collides
with author root keys, and cannot describe mirrored slot projections.

### Add a ninth `ComponentNode` argument for ignore

Rejected. Parallel optional positional arguments do not identify whether
metadata belongs to a ComponentRange or a dynamic ordinary element, make future
range directives increasingly brittle, and invite key/ignore ordering drift.

### Discover ignore during DOM mutation

Rejected. Mutation-time discovery lets descendants, Events manifests, and
dependencies become observable before an ancestor later retains them. It also
makes results depend on traversal and placement order.

## Falsifiers

The design must be revisited rather than patched around if any of these proves
true:

- ownership comments cannot reconstruct the same logical child order in every
  physical placement without adding a new delimiter format;
- an ordinary ignore barrier can retain one projection of a shared invocation,
  fill, or slot record while safely adopting another projection of that same
  record;
- the pure accepted-all operation plan cannot match the pinned Alpine morph
  behavior for ordinary DOM and form controls;
- ownership or Events state must be installed before the planner can compute
  matches, creating an unavoidable side effect from an excluded branch;
- extension `before_manifest` hooks require parse-time execution rather than
  post-plan activation;
- a metadata-free component changes generated source or runtime behavior;
- any JS/PHP/Go/Rust or PyO3 contract actually consumes the changed Python
  constructor shape and therefore requires an unplanned migration.

## Dirty-worktree discipline

This repository already contains broad user-owned and prior-session changes,
including edits in most target files. Each implementation patch is based on
the current worktree, uses narrow context, and preserves unrelated edits. No
target is restored from `HEAD`, and generated artifacts are rebuilt only from
their current checked-in sources.
