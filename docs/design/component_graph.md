# Design: authored component dependencies

**Status (2026-08-23): implemented.**

Citry exposes a static graph of the component references written in registered
components' primary templates. The graph helps tools answer two questions:

- Which registered components does this component reference?
- Which registered components reference this component?

The graph describes authored possibilities. It does not describe component
instances from one render, DOM placement, or every way Python can construct a
component.

## 1. Prior art

The design uses these existing contracts:

- `Citry.inspect_components()` copies one complete registry and builds frozen
  metadata after lifecycle coordination is released
  (`citry/citry.py:1168`, `citry/_component_introspection.py:256`).
- `citry check` reads effective inline and file templates without calling
  `get_template()`, rendering, running template-loading transforms, filling
  caches, or updating the hot-reload file index
  (`citry/_checker.py:189`).
- `_find_pair_declaration()` finds the effective inherited template owner, and
  `_inspect_asset_path()` checks file candidates without reading or changing
  runtime state (`citry/assets.py:110`, `citry/assets.py:157`).
- The parser exposes opening tags, ordered attributes, nested bodies, and
  exact UTF-8 byte ranges. `template_tag_uses()` already walks nested template
  attributes, but it returns tag names only and suppresses nested parse
  failures (`citry/_portable_ide.py:110`).
- `<c-component is="name">` selects a static target only when no exact
  `c-bind` is present. `c-is`, empty selectors, and spread-selected targets
  stay dynamic (`citry_template_parser/src/compiler.rs:315`, `:711`).
- Runtime authorship and physical slot placement are separate relationships.
  Citry has no single honest runtime parent relation
  (`docs/design/component_tracing.md:133`).

No grammar, AST, compiler-output, host-language, or PyO3 contract change is
needed.

## 2. Public contract

The engine method is:

```python
graph = app.inspect_component_graph(include_builtins=False)
```

The method completes ordinary discovery and built-in registration, copies the
name-to-class registry once, and releases lifecycle coordination before it
reads template files. The returned `ComponentGraph` contains copied values and
does not retain component classes.

Static means that Citry reads authored templates without rendering them. The
application still has to import successfully so Citry can know the complete
runtime registry, aliases, inheritance, and engine ownership.

`include_builtins=False` omits built-in nodes and references to them. Target
resolution still uses the complete copied registry, so an omitted built-in is
not reported as unknown. `include_builtins=True` includes built-in definitions
and references.

## 3. Value model

The public records are frozen and slotted:

- `ComponentGraphNode` identifies one exact registered class generation by
  `class_id`, `engine_id`, `definition_id`, primary name, aliases, and built-in
  status.
- `ComponentGraphLocation` identifies one authored occurrence. UTF-8
  `start_index` and `end_index` are authoritative. `source_range` uses the
  existing zero-based UTF-16 `LspRange` contract. `declaration_file` points to
  the Python declaration when available; `template_file` points to a resolved
  file-backed template.
- `ComponentGraphReference` records one resolved occurrence from a source
  definition to a target definition. It retains the exact authored target and
  the registered name that resolved it.
- `UnresolvedComponentReference` records an unknown component name or a target
  selected dynamically at render time.
- `ComponentGraphProblem` records a source that could not be inspected, while
  allowing the rest of the graph to remain useful.
- `ComponentGraph` is the versioned envelope. It owns canonical ordering,
  deterministic JSON serialization, and derived queries.

The graph schema version remains `1` while the `citry` package is below
`1.0.0`, following the repository's pre-release contract rule.

## 4. Dependency semantics

Every component invocation written anywhere in component A's effective primary
template is a dependency of A. Lexical nesting does not transfer authorship:

```citry-html
<c-panel>
  <c-button />
</c-panel>
```

If this source belongs to `Page`, it records `Page -> Panel` and
`Page -> Button`. It does not record `Panel -> Button` because `Panel` did not
author the button invocation.

References inside conditionals, loops, fills, and nested template-valued
attributes remain authored possibilities and are included. Repeated
invocations remain separate reference records with separate locations.
`dependencies()` and `dependents()` deduplicate component identities.

Self-references and cycles are valid. Query methods never recursively walk the
graph, so cycles cannot make a query loop forever.

Public terminology is:

- `dependencies(component)`: directly referenced registered definitions;
- `dependents(component)`: registered definitions that directly reference it;
- `references_from(component)`: resolved authored occurrences from it;
- `references_to(component)`: resolved authored occurrences targeting it;
- `unresolved_from(component=None)`: unresolved occurrences from one component
  or from the complete graph.

These names avoid suggesting runtime parentage or slot placement.

## 5. Name and selector resolution

A direct tag removes exactly one authored lowercase `c-` prefix, lowercases
the remaining suffix, and looks it up verbatim in the copied registry. This
matters for a registered name such as `c-foo`, which is referenced as
`<c-c-foo>`.

Primary names and aliases resolve to the same target node. A reference keeps
the authored spelling and the exact normalized registered name that matched.

`<c-component is="card">` produces a `static-selector` reference to `card`
when no exact `c-bind` attribute is present. `c-is` or any exact `c-bind`
produces one `dynamic-target` unresolved reference. Citry does not evaluate
Python expressions or spread values while building the graph. A missing,
bare, or empty selector is invalid Citry syntax and produces a
`template-syntax` problem, as it does during ordinary template parsing.

`<c-element>` selects HTML rather than a component and never creates a graph
reference. Parser-owned structural tags such as `<c-if>`, `<c-for>`,
`<c-fill>`, and `<c-slot>` do not create references.

An unregistered direct tag or static selector produces an
`unknown-component` unresolved reference. The graph does not invent a target.

## 6. Template acquisition and source positions

Citry groups effective templates by their physical source, parses each source
once, and projects the discovered occurrences onto every registered component
that consumes it. An inherited inline template therefore has one parse and one
reference set per registered subclass. Components that point at the same
resolved file behave the same way.

Inline templates use Citry's ordinary common-indent normalization. File-backed
templates remain byte-exact. All nested-template offsets are rebased into the
normalized root template before Citry computes the UTF-8 indices and UTF-16
range.

Graph construction reads authored source directly. It does not call
`get_template()`, run `on_template_loaded`, compile, render, populate the
template cache, or register files for hot reload. Component invocations added
by a runtime transform are outside this graph because Citry cannot map them
back to authored locations.

Host-template adapters can identify their authored foreign ranges through
`on_template_foreign_spans`, the same analysis hook used by `citry check`.
Consumers sharing one physical template must report the same spans. A provider
failure or disagreement produces `template-namespace-unavailable`. A span
that may control a body produces `foreign-source-controls-body`, because the
provider can hide component invocations from Citry even though references in
the rest of the template remain useful. Provider-generated invocations remain
outside the graph until providers can publish authored graph facts and source
maps.

The parser runs without component `TagRules`. A wrong input or slot should not
hide an otherwise identifiable dependency edge. Base Citry syntax and built-in
structural rules still apply.

## 7. Problems and completeness

One component's source failure does not discard references from other
components. `ComponentGraphProblem` uses one of these codes:

- `template-declaration`
- `template-language-unsupported`
- `template-value-invalid`
- `template-file-not-found`
- `template-file-unreadable`
- `template-namespace-unavailable`
- `foreign-source-controls-body`
- `template-syntax`
- `nested-template-syntax`

A problem lists every selected component definition affected by that physical
source. A component with no template is a valid leaf and creates no problem.

`coverage_complete` is true when no source problem prevented inspection.
`fully_resolved` is true when coverage is complete and every discovered
reference has a static registered target. Unknown and dynamic references make
`fully_resolved` false without changing `coverage_complete`.

These properties apply only to registered components' authored primary
templates. They make no claim about Python composition, `CitryElement` values
returned from expressions, direct `render()` calls, routes, fragments,
library invocations, or extension replacements.

## 8. Snapshot, caching, and privacy

Nodes and name resolution come from one copied registry generation. Another
thread may register, unregister, or replace a component after that copy; the
graph still describes the copied generation through its `engine_id` and each
node's `definition_id`.

Template files can change while a graph is being built. The graph is one
observational result, not a long-lived cache. `Citry` stores no graph cache,
and callers build a fresh graph when they need current source.

Serialized locations can contain absolute developer-machine paths. Graph JSON
is a local tooling artifact and must not be served unchanged from a public
endpoint.

## 9. Alternatives considered

### Add relationship fields to `ComponentInfo`

Rejected. The catalog describes runtime registration metadata without reading
source bodies. The graph reads authored templates, can be partial, and has a
separate completeness contract.

### Use the runtime ownership graph

Rejected. Runtime ownership contains occurrences from one selected execution,
omits branches that did not render, and distinguishes authored ownership from
physical placement. It cannot answer definition-wide source references.

### Scan Python without importing the application

Rejected for this API. A source-only scan cannot prove dynamic registration,
cross-module inheritance, aliases, configured directories, or the effective
runtime engine. That requires a separate partially known IDE record.

### Find application roots from `render()` calls

Rejected. Components can enter through routes, fragments, direct composition,
expressions, libraries, and dynamic calls. A grep-based result would present
an incomplete set as authoritative.

## 10. Falsifiers

This design is insufficient if a consumer requires any of these as a complete
fact:

1. Components created from Python rather than authored component tags.
2. References inserted by a template-loading transform without an authored
   source mapping.
3. The runtime target of a dynamic selector.
4. Physical slot placement or the component-instance tree from one render.
5. Application entry points across routes, events, fragments, and direct calls.

Those needs require Python analysis, an extension source-mapping contract, or
runtime tracing. The static authored graph must not guess them.

## 11. Acceptance matrix

| Area | Required evidence |
|---|---|
| Names | Primary names, aliases, case variants, and a registered name beginning with `c-` resolve correctly. |
| References | Repeated occurrences retain locations; dependency and dependent queries deduplicate nodes. |
| Syntax | Bodies, control flow, fills, and nested template attributes are walked; HTML, structural tags, and `<c-element>` are omitted. |
| Dynamic targets | Static selectors resolve; expression and spread selectors remain explicit unresolved references. |
| Sources | Inline, file-backed, inherited, and shared templates keep correct provenance and root-relative positions. |
| Failures | Missing, unreadable, malformed, unsupported, and invalid sources create problems without stopping other components. |
| Graph shape | Self-reference and cycles are valid; canonical ordering and deterministic serialization are locked. |
| Runtime isolation | Building a graph does not render, run template-loading transforms, populate template caches, or update hot-reload state. |
| Snapshot | Concurrent registration changes cannot mix names or generations from two registry snapshots. |
