# citry-client-graph/1

When the server renders a page that has client-side behavior, it tells the
browser which component owns which part of the HTML by sending one block of
JSON in a `<script type="application/json" data-citry-graph>` tag. This
directory is the language-neutral contract for that JSON: protocol major 1. It
is the source of truth every implementation follows, in any language.

The manifest keeps its complete 64-character revision as the graph identity.
The surrounding ownership comments carry the first eight characters as a
page-local alias, which keeps rendered HTML readable while the browser still
routes every range through the complete manifest revision.

A **component-tag client binding** is browser behavior resolved from a nested
component tag, such as `$c-props="{ theme }"`, `@click="select()"`, or
`@c-poll.5s="refresh()"`. The parent owns the expression or handler, while the
child supplies the component boundary where the browser applies it.

Start with [`spec.md`](spec.md), which explains the JSON and defines every
term the other files use: graph, component instance, nested component,
component-tag client binding, fill, slot region, and source location.

## What is in this directory

- [`spec.md`](spec.md) is the rules in prose: what the server puts in the JSON
  and what a browser must check before it trusts it. Read this first.
- [`manifest.schema.json`](manifest.schema.json) is the JSON shape, written as
  a JSON Schema (Draft 2020-12). It checks structure only; the rules that go
  beyond structure live in the spec and the validator.
- [`python/citry_client_graph/`](python/citry_client_graph/) contains the
  standard-library-only Python builders and validators. Citry embeds this
  directory byte for byte as `citry._protocol.client_graph`.
- [`js/`](js/) contains the private TypeScript validator used by both browser
  bundles. Its build inserts one generated helper block into `citry.js` and
  check mode rejects a stale or duplicated block.
- [`validate.py`](validate.py) is the reference checker. It confirms the
  example manifests in `tests/` behave the way `index.json` says they
  should, using the schema and the executable Python validator. It needs only
  the standard library, so anyone can run it without installing anything.
- [`tests/`](tests/) holds worked example manifests, correct ones and
  deliberately broken ones, that every implementation is checked against.
  [`tests/README.md`](tests/README.md) says what each one nails down and
  how to regenerate them.
  [`tests/constraint-ownership.json`](tests/constraint-ownership.json) assigns
  every structural schema rule to its Python and JavaScript validators and
  supporting test family.

## Who follows this contract, and how it is checked

Two parts of Citry implement this contract today, and both are checked against
the files here:

- The Python protocol package builds every closed record, signs the manifest,
  and checks the complete graph. The server-side writer,
  [`ownership_manifest.py`](../../../py/citry/citry/ownership_manifest.py),
  selects records from the settled render tree and gives those facts to the
  package. Its output is compared to the correct example manifests by
  [`test_client_graph_conformance.py`](../../../py/citry/tests/test_client_graph_conformance.py).
- The JavaScript protocol package checks the closed JSON shape, revision, and
  logical record relationships. Its generated helper is embedded in
  [`citry.js`](../../../py/citry/citry/ext/dependencies/client/citry.js), which
  keeps only checks that need live DOM comment caps before it adopts a graph.
  Both layers run against the same correct and broken examples through
  [`test_client_graph_corpus_e2e.py`](../../../py/citry/tests/e2e/test_client_graph_corpus_e2e.py).

The public Python builders validate and defensively copy their inputs. Citry's
writer has a narrower trusted path for records it just built through those
helpers. Final emission always checks the complete fixed shape, recreates the
canonical unsigned bytes, and rejects a manifest whose revision no longer
matches. Development additionally performs the expensive cross-record
relationship audit; production omits that pass. Delayed mutation therefore
cannot silently change the shape or bytes that are sent.

`validate.py` is a standalone reader: it never renders a page, it only checks
the JSON through the same executable Python package. Keeping the server, the
standalone checker, and the browser in step is the whole point of the fixture
set. [`tests/README.md`](tests/README.md) states exactly what "a
reader passes" and "a writer passes" mean.

The schema tooling reports two kinds of evidence. Shared mutations make one
small change to valid JSON and require matching Python and JavaScript issue
paths and categories. The ownership registry groups all 219 structural rules
by the runtime functions and tests responsible for them. Each group's count
and fingerprint must be updated deliberately when the schema changes. This
keeps complete assignment separate from the smaller set of surgical
cross-language examples.

Mutation coverage is change-driven, not a quota of one case per schema
pointer. Add a shared mutation when a change introduces a new schema keyword
or distinct validator branch, when a drift bug needs a regression case, or
when an exact first issue path and category matter. Do not add hundreds of
cases that only repeat the same required-field, type, constant, or
closed-object helper. If repeated drift shows that this policy is too weak,
revisit broader generation with evidence from those failures. The analysis
behind this policy is in
[`protocol_mutation_coverage_exploration.md`](../../../../docs/design/v1_beta_research/protocol_mutation_coverage_exploration.md).

## Running the checks

From the repository root:

```bash
# Language-neutral self-check: do the examples still match the rules?
python packages/protocol/client_graph/v1/validate.py

# Exact shared mutations plus complete validator ownership.
uv run python -m packages.protocol._tooling.check \
  packages/protocol/client_graph/v1

# Server writer: does its output still match the correct examples?
python -m pytest \
  packages/py/citry/tests/test_client_graph_protocol_runtime.py \
  packages/py/citry/tests/test_client_graph_conformance.py

# JavaScript validator and generated core helper freshness.
pnpm --dir packages/protocol/client_graph/v1/js run check

# Browser reader: does it accept the correct examples and reject the broken
# ones? Repeat for firefox and webkit before a release.
python -m pytest \
  packages/py/citry/tests/e2e/test_client_graph_corpus_e2e.py --browser chromium
```

`validate.py` also runs inside the normal test suite through
[`test_client_graph_protocol_package.py`](../../../py/citry/tests/test_client_graph_protocol_package.py),
so `python scripts/check.py` (the full repository gate) covers
everything here except the browser end-to-end tests.

## Changing the protocol

The manifest is one contract shared by the writer, the readers, and these
files, so a change is not done until all of them move together in one PR:

1. [`spec.md`](spec.md): state the new rule in prose.
2. [`manifest.schema.json`](manifest.schema.json): update the shape if any
   field changed.
3. Update both executable protocol packages:
   [`python/citry_client_graph/`](python/citry_client_graph/) and
   [`js/`](js/). [`validate.py`](validate.py) and the JavaScript package check
   run them against the shared examples.
4. The writer
   ([`ownership_manifest.py`](../../../py/citry/citry/ownership_manifest.py))
   and every reader (the browser
   [`citry.js`](../../../py/citry/citry/ext/dependencies/client/citry.js), and
   any future language binding): make them produce or accept the new shape.
5. [`tests/`](tests/): add an example that locks the new rule, a correct
   one and usually a broken one the rule rejects, then regenerate and re-sign
   as [`tests/README.md`](tests/README.md) describes.
6. Update
   [`tests/constraint-ownership.json`](tests/constraint-ownership.json) for the
   changed validator family. Follow the change-driven mutation policy above
   when deciding whether an exact cross-language issue path/category example
   is useful.

Two rules of thumb keep this honest: the reference checker and the browser
must agree on every example, and a rule you cannot show with a fixture is a
rule no other implementation can test against. This is a high-risk change that
spans languages; follow the gate in the repository
[`CLAUDE.md`](../../../../CLAUDE.md) before you start.

## Versions and releases

Every manifest names its protocol as the exact string `citry-client-graph/1`,
and every reader rejects anything else. Each object also requires an exact set
of fields, so a reader rejects a manifest that carries a field it does not
know.

This directory is still the working pre-release v1 contract. Until the owning
Citry package reaches `1.0.0`, its shape may change in place, but the writer,
every reader, the schema, fixtures, tests, and docs must move together. After
`1.0.0`, clearer wording and checker fixes may stay in `v1/`, while any change
to what a valid manifest emits or accepts starts a sibling `v2/` package with
protocol string `citry-client-graph/2`. The frozen `v1/` package then remains
available for existing pages and implementations.

This package is not published on its own. It ships inside the Citry repository
and rides Citry's normal release. Record anything a user would notice in the
[`CHANGELOG.md`](../../../../CHANGELOG.md), and see
[`docs/codebase.md`](../../../../docs/codebase.md) for how the monorepo builds
and releases.

## Common maintainer tasks

- Change what the manifest contains: follow "Changing the protocol" above.
- Add or regenerate a fixture, or re-sign one after editing it: see
  [`tests/README.md`](tests/README.md), "Keeping the examples in sync".
- Look up a term (graph, component instance, nested component, component-tag
  client binding, fill, slot region, or source location): see
  [`spec.md`](spec.md).
- Check everything at once: `python scripts/check.py` from the
  repository root, plus the browser command above for the end-to-end tests.
