# citry-client-graph/1

When the server renders a page that has client-side behavior, it tells the
browser which component owns which part of the HTML by sending one block of
JSON in a `<script type="application/json" data-citry-graph>` tag. This
directory is the language-neutral contract for that JSON: protocol major 1. It
is the source of truth every implementation follows, in any language.

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
- [`validate.py`](validate.py) is the reference checker. It confirms the
  example manifests in `tests/` behave the way `index.json` says they
  should, using the schema plus every rule from the spec. It needs only the
  standard library, so anyone can run it without installing anything.
- [`tests/`](tests/) holds worked example manifests, correct ones and
  deliberately broken ones, that every implementation is checked against.
  [`tests/README.md`](tests/README.md) says what each one nails down and
  how to regenerate them.

## Who follows this contract, and how it is checked

Two parts of Citry implement this contract today, and both are checked against
the files here:

- The server-side writer,
  [`ownership_manifest.py`](../../../py/citry/citry/ownership_manifest.py),
  builds the manifest. Its output is compared to the correct example manifests
  by
  [`test_client_graph_conformance.py`](../../../py/citry/tests/test_client_graph_conformance.py).
- The browser-side reader,
  [`citry.js`](../../../py/citry/citry/ext/dependencies/client/citry.js),
  checks the manifest and then adopts it. It is run against the same examples,
  correct and broken, by
  [`test_client_graph_corpus_e2e.py`](../../../py/citry/tests/e2e/test_client_graph_corpus_e2e.py).

`validate.py` is a third, language-neutral reader: it never renders a page, it
only checks the JSON. Keeping all three in step is the whole point of the
fixture set; both the writer and the browser pass today and are kept passing
in CI. [`tests/README.md`](tests/README.md) states exactly what "a
reader passes" and "a writer passes" mean.

## Running the checks

From the repository root:

```bash
# Language-neutral self-check: do the examples still match the rules?
python packages/protocol/client_graph/v1/validate.py

# Server writer: does its output still match the correct examples?
python -m pytest packages/py/citry/tests/test_client_graph_conformance.py

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
3. [`validate.py`](validate.py): add or change the matching rule so the
   reference checker enforces it.
4. The writer
   ([`ownership_manifest.py`](../../../py/citry/citry/ownership_manifest.py))
   and every reader (the browser
   [`citry.js`](../../../py/citry/citry/ext/dependencies/client/citry.js), and
   any future language binding): make them produce or accept the new shape.
5. [`tests/`](tests/): add an example that locks the new rule, a correct
   one and usually a broken one the rule rejects, then regenerate and re-sign
   as [`tests/README.md`](tests/README.md) describes.

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

This directory is still the working pre-release v1 contract. Until the
maintainers explicitly freeze it for the v1 beta, its shape may change in
place, but the writer, every reader, the schema, fixtures, tests, and docs must
move together. After that freeze, clearer wording and checker fixes may stay in
`v1/`, while any change to what a valid manifest emits or accepts starts a
sibling `v2/` package with protocol string `citry-client-graph/2`. The frozen
`v1/` package then remains available for existing pages and implementations.

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
