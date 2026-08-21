# Client graph protocol tests

These files are worked examples of the JSON the server sends the browser (the
graph manifest). Some are correct manifests any reader should accept; the ones
whose names start with `error_` are deliberately broken and any reader should
reject them before letting them change the page. The examples were written from
the spec and stand in for it: if an implementation disagrees with an example,
the implementation is wrong, until someone deliberately changes the protocol
and updates the examples, schema, and spec together in one PR.
[`../spec.md`](../spec.md) defines the manifest and every term used here
(graph, component class, component instance, nested component, fill, slot
region, and source location).

To check that the examples still agree with the rules, run
[`../validate.py`](../validate.py) on its own (it needs only the standard
library; it uses the `jsonschema` package when that is installed and an
equivalent built-in checker otherwise). CI runs the same checks through pytest
(`packages/py/citry/tests/test_client_graph_protocol_package.py`).

Check the revision vectors in both languages with:

```bash
python -S packages/protocol/client_graph/v1/tests/check_canonicalization.py
node packages/protocol/client_graph/v1/tests/check_canonicalization.mjs
```

[`conformance-cases.json`](conformance-cases.json) is the cross-language
structural mutation set. Each case points to one valid manifest here, changes
one small thing, and records the expected issue path and category. Check it
and print the remaining schema coverage with:

```bash
uv run python -m packages.protocol._tooling.check packages/protocol/client_graph/v1
pnpm --dir packages/protocol/client_graph/v1/js run check
```

The existing `error_*.manifest.json` corpus continues to own relationship
rules and browser staging or adoption behavior.

The manifest fixtures keep complete revisions and therefore do not duplicate
the physical comment syntax. Comment tests in both protocol implementations
lock the eight-character alias grammar, while the browser corpus locks active
alias collision rejection and release after an aborted transaction.

[`constraint-ownership.json`](constraint-ownership.json) groups all 219
structural schema constraints under their Python and JavaScript validator
functions and supporting test files. Each group stores its expected count and
content fingerprint, so a schema change fails the tooling check until its
runtime ownership is reviewed. This complete assignment is separate from the
smaller mutation set, which proves exact cross-language issue paths and
categories for selected boundaries.

[`canonicalization.json`](canonicalization.json) is a separate set of exact
byte vectors for the revision algorithm. It is an object with format
`citry-client-graph-canonicalization/1` and a `vectors` array. A vector carries
one of `manifest`, `input`, `inputJson`, or `equivalentInputJson`; valid vectors
record canonical UTF-8 hex and usually a SHA-256 digest, while rejected vectors
carry `"expect": "reject"`. Runners remove `revision` only from a `manifest`
vector. They parse JSON strings before canonicalizing them and require every
entry in `equivalentInputJson` to produce the same bytes.

## What passing means

**A reader passes when it accepts every `"expect": "valid"` example and rejects
every `"expect": "invalid"` one without letting any of it change the page.**
Rejecting is the rule that has to hold; which error message a reader prints is
up to the reader. CI holds both readers to the examples: the reference
validator through the pytest module named above, and the browser through
`packages/py/citry/tests/e2e/test_client_graph_corpus_e2e.py`.

**A writer passes when rendering an example's setup produces exactly that
example's manifest.** The two are compared as decoded JSON values; because the
`revision` is a hash of the canonical form, equal values also mean equal bytes.
The setups are the small components in
`packages/py/citry/tests/test_client_graph_conformance.py`, which also lists
the three things a writer has to hold fixed to get the exact same bytes every
run (render ids, class ids, template origins). A writer in another language can
check the looser rule instead: everything it produces passes
[`../manifest.schema.json`](../manifest.schema.json) and the rules in
`validate.py`.

## What each index entry says

[`index.json`](index.json) is the machine-readable list, one entry per example.
Test runners read the list, never this prose.

- `manifest`: the file name. Broken examples start with `error_`.
- `expect`: `"valid"` or `"invalid"`.
- `locks` (valid only): one line on what the example nails down.
- `defect` (invalid only): one line on what is broken.
- `problem` (invalid only): a substring that has to appear somewhere in the
  reference validator's list of problems. A help for other implementations,
  not a rule they have to match.
- `harness` (invalid only, optional): `"adoption"` when the browser only
  catches the defect while preparing to adopt the graph, a step after its first
  round of checks. The default, `"stage"`, means that first round rejects it on
  its own, with no page structure set up.
- `preserveRevision` (invalid only, optional): `true` when the broken thing is
  the `revision` itself, so the maintenance tool must not recompute it.

## Why each broken example targets one rule

Every broken example changes exactly one thing and, except for the
tampered-revision example itself, is then re-signed so the `revision` check
passes and the one broken thing is what trips. A few rules cannot be broken one
at a time, so a single change can trip more than one check. Two cases worth
knowing: a cycle in the component execution order forces a cycle in the parent
chain too. Giving a detached fill an owner also breaks the rule that an owner
and its source location go together. Fixture runners require rejection, while
the shared conformance mutations separately lock exact issue paths and
categories in both runtime languages and at the browser boundary.

## What the valid examples nail down

The valid examples are all `mode: "development"`, so they carry the full shape
including source provenance (`sourceLocations`). Production acceptance (an
empty `sourceLocations` array and null references) is exercised by the Python
conformance tests and the two production error examples.

| Example | Nails down |
|---|---|
| `minimal` | The smallest complete graph: one component class, one root component instance, everything else empty. |
| `component_tag_client_bindings` | One nested component carrying all four component-tag client binding kinds (`props`, `alpine-handler`, `citry-dom-event` with a key filter and a debounce, and `citry-poll`), the closed `morphMode: "ignore"` component-range mode, an execution-order constraint, and binding source locations. For example, `$c-props="{n: 1}"`, `@click="open = true"`, `@c-click.prevent="save({x: 1})"`, and `@c-poll.5s="tick"` become separate `clientBindings` records. The parent owns each expression or server handler, while the child supplies the component boundary where the browser applies it. Also nails down the poll rule: only the exact event `poll` is a poll, so the custom DOM event `@c-pollchange` stays a DOM event. |
| `dynamic_spread_loop` | The `spread` and `server-dynamic` client-binding sources, spread mapping keys and indices on source locations, and implicit fills from a loop body. |
| `supplied_fills` | A named fill written in a template, carrying the nested component it came from, rendered through two outlets of one slot: one fill, two slot regions. |
| `fallback_fill` | A slot with nothing supplied to it rendering its own client-active fallback: a `fallback` fill with a `fallbackLocationId` and no source nested component. |
| `detached_fills` | A fill supplied from Python and a fill left to a typed default, on one receiver: both detached, with no owning template and no source location. |
| `nested_slot_regions` | Cache slot regions nested inside each other with parent links, scope transitions, result owners, nested components that sit inside a slot region, and transparent component instances. |
| `multi_graph` | Two graphs in the order they appear; both number their records from 1 the same way, and render ids stay unique across both. |
| `utf8_offsets` | Offsets counted in UTF-8 bytes: the template is ``π<c-child @c-click="save()" />`` and the client-binding location's `start`/`end` slice its UTF-8 bytes to exactly `@c-click="save()"`. |

## What the broken examples cover

One example per rule family in `validate.py`, with extra examples for the
rules where the reference checker and the browser most easily fall out of step.
Grouped by area:

- **Encoding and envelope**: wrong protocol major version, an unknown ownership
  comment prefix, an unknown `mode` value, an extra top-level member, a
  tampered revision.
- **Identity**: an uppercase render id, the same render id twice in one graph,
  one render id in two graphs, the same record id twice, a graph id that is not
  its position.
- **Modes**: a production manifest whose `sourceLocations` collection is not
  empty, and a production manifest with a non-null source-location reference.
- **Source locations**: a location carried by no component instance, a location
  whose class is not its owner's, a byte range that ends before it starts, a
  nested component whose location is not marked as a component call, a child
  instance whose parent disagrees with the nested component that rendered it,
  and a nested component that no child instance points back to.
- **Component-tag client bindings**: browser-side bindings resolved from a
  nested component tag, such as `$c-props="{ theme }"`, `@click="select()"`,
  or `@c-poll.5s="refresh"`. The parent owns each expression or server handler,
  while the child supplies the component boundary where the browser applies
  it. Broken examples cover a wrong location kind, invalid payload field types,
  a `props` payload not under `$c-props`, a DOM-event payload whose event name
  disagrees with its key, a DOM-event payload placed under the poll key, a poll
  payload under an event key, and a Citry handler whose class is not its
  parent's.
- **Fills**: a fill whose kind and location kind disagree, a supplied fill
  missing the nested component it came from, a fallback fill that carries a
  source nested component, and a detached fill that claims an owner.
- **Ancestry**: an uninvoked instance that names a parent, a cycle in component
  execution order, a slot region that is its own parent, a slot-region
  transition that disagrees with its nesting, a parent-chain cycle built from
  nested components that each look fine on their own, and a nested component
  pointing at a slot region that does not exist.

Some rules have no example of their own yet, because another example in the
same family already exercises the same code: duplicate class ids, an
alpine-handler payload under a non-Alpine key, an unknown parent render,
unknown nested-component or client-binding source locations, an unknown fill source
nested component, fill owner or receiver class mismatches, a slot region that
disagrees with its fill, a slot region's slot-location receiver and kind, and
execution-order constraints that disagree with their nested component.

## Keeping the examples in sync

- The valid examples are regenerated, never hand-edited:
  `.venv/bin/python packages/py/citry/tests/test_client_graph_conformance.py --freeze`.
- The four client-binding type and location errors are derived from that valid
  example with [`derive_client_binding_errors.py`](derive_client_binding_errors.py).
- After hand-editing a broken example, recompute its `revision` with
  [`resign.py`](resign.py) (standard library only):
  `python packages/protocol/client_graph/v1/tests/resign.py`. It leaves the
  examples marked `preserveRevision` alone.
- The HTML comments that mark where each piece sits are HTML, not JSON, so
  these examples cover the JSON and its revision only. Whether those comments
  pair up, nest, and refuse to be cloned is covered by the browser end-to-end
  tests against live pages.
