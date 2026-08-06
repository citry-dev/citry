# Protocol runtime ownership: Stage 4

**Status (2026-08-04): complete; independent review passed.**

Stage 4 moves the Python server's fixed `citry-client-graph/1` construction,
canonicalization, comments, revisions, and validation into the protocol
package. Citry still decides which settled render-tree records belong in the
final document.

## Ownership moved

The canonical package at
`packages/protocol/client_graph/v1/python/citry_client_graph/` now owns:

- every closed manifest, graph, record, and client-binding payload shape;
- deterministic validation issues, strict in-memory JSON checks, and
  defensive copying for ordinary callers;
- canonical JSON bytes, SHA-256 revisions, and inert-script escaping;
- ownership-comment construction and parsing for the literal `citry:g1`
  format; and
- structural and logical relationship validation for the complete graph.

The byte-identical shipped copy lives at
`packages/py/citry/citry/_protocol/client_graph/` and is maintained by
`scripts/sync_protocol_python.py`. The package has no runtime dependency
outside the Python standard library.

The standalone `validate.py` imports the same package. It retains the optional
JSON Schema comparison, but the package validator is the executable contract
used even under `python -S` without `jsonschema`.

## Product boundary

`ownership_manifest.py` still traverses the settled render tree, selects live
instances, nested components, fills, and slot regions, and resolves their
product-only relationships. It now gives those facts to protocol-owned record
builders and uses protocol-owned graph assembly, manifest signing, comment
formatting, and final serialization. Product code no longer defines wire
field sets, canonical JSON, revision hashing, or ownership-comment syntax.

The public builders validate and copy inputs by default. Citry's trusted
writer avoids repeating those per-record checks while it creates records. In
development it then runs the complete cross-record relationship audit. Final
emission in both modes always checks the fixed structure, rebuilds the
canonical unsigned bytes, and rejects a revision mismatch. Production skips
only the expensive relationship pass. Tests cover both the complete
development audit and revision-consistent structural mutation at the
production emission boundary.

## Compatibility and conformance

The focused protocol and writer selection passed 75 tests. It covers:

- all 47 valid and invalid protocol examples;
- the shared exact-path and exact-category mutation cases;
- strict Python-only failure modes such as cycles, non-finite values, and
  integers outside the browser range;
- defensive builder copies and relationship rejection at construction;
- canonical integer normalization and ownership comments;
- use of the protocol manifest boundary by the real writer;
- final-emission mutation detection; and
- byte identity between the canonical and embedded packages.

The existing writer golden output remains unchanged. A further 480 tests for
metadata, client bindings, client props, and cache construction and replay
also passed. The focused Chromium graph selection passed all 83 tests across
the ownership-manifest lifecycle and shared graph corpus.

Both canonicalization programs passed the same 13 vectors. The standalone
checker passed all 47 fixtures with the built-in validator, and scoped Ruff,
Mypy, generated-copy freshness, and `git diff --check` passed.
The protocol tooling reported no package problems; its deliberately bounded
mutation inventory covers 13 of 215 schema constraints, with the exhaustive
constraint audit still assigned to Stage 6.

## Independent review corrections

The first adversarial pass found six related contract gaps, all corrected
before re-review:

- production final emission now rejects schema-invalid output even when a
  caller recomputes its revision;
- unhashable modes and invalid numeric builder inputs produce pointed
  `ProtocolValueError` issues instead of raw Python exceptions;
- multi-fault validation follows schema field order, including source
  locations, DOM-event payloads, and the top-level graph/delimiter order;
- adjacent in-memory UTF-16 surrogate code units canonicalize to the same
  literal scalar as JavaScript;
- ownership comments accept ASCII decimal identifiers only; and
- the JSON Schema now carries the `renderId` pattern already enforced by both
  executable readers, with a shared Python/JavaScript mutation case.

## Performance and moving baseline

The Stage 4 opening seven-sample medians were 14.121 ms for the 25-component
document and 233.768 ms for the 325-component document. An initial direct
migration repeated complete validation too often and crossed the stop gate.
The final implementation removes repeated strict-JSON walks for every nested
record while still checking the complete fixed shape at final emission.

Two closing seven-sample runs measured:

| Scenario | Opening | Closing run 1 | Closing run 2 |
| --- | ---: | ---: | ---: |
| 25 components | 14.121 ms | 14.574 ms | 14.594 ms |
| 325 components | 233.768 ms | 236.489 ms | 237.441 ms |

Both repeats clear the Stage 4 stop threshold. The 25-component change is
about 3.3 percent and under 0.5 ms; the 325-component change is under 1.6
percent.

Stage 4 did not change either browser bundle. At close, concurrent work had
the core bundle at 320,040 bytes with SHA-256
`4a109b85cba5c996feda3cec2696d1c2726dfefaca6efeb92dfa2ebf638d2675`
and the Events bundle at 326,781 bytes with SHA-256
`cdca0dfb56dc584ddb2cc601d89dd410296fa164c7a5a7c09b09ae9ef7fa896a`.
Their combined size was 646,821 raw and 134,997 deterministic gzip bytes. The
closing scope identity was
`16643f2d90b6e16845b370c5a274233a32fc42ec7a87bd1ba46e121491ae53bd`.

## Work held for later stages

The browser's graph validator remains product-local until Stage 5. Stage 5
will generate the protocol helper block, run shared cases through real browser
staging and adoption, and preserve the existing atomic DOM boundary. The
complete constraint-coverage audit, Firefox and WebKit matrix, artifact tests,
and full repository gate remain Stage 6 work.

## Independent review result

The corrected stage passed adversarial re-review with no remaining blockers.
The reviewer independently reproduced the 75 focused Python tests, 47
standalone fixtures, both 13-vector canonicalizers, 8 JavaScript package
tests, 83 Chromium tests, schema tooling, embedded-copy identity, Ruff, Mypy,
and diff checks. Its isolated timing sample measured 14.367 ms for 25
components and 233.474 ms for 325 components, also inside the stop rule.

## Commands

```bash
uv run --no-sync python scripts/sync_protocol_python.py --check
python -S packages/protocol/client_graph/v1/validate.py
python -S packages/protocol/client_graph/v1/tests/check_canonicalization.py
node packages/protocol/client_graph/v1/tests/check_canonicalization.mjs
uv run pytest -q \
  packages/py/citry/tests/test_client_graph_protocol_runtime.py \
  packages/py/citry/tests/test_client_graph_protocol_package.py \
  packages/py/citry/tests/test_client_graph_conformance.py \
  packages/py/citry/tests/test_ownership_manifest.py
uv run --directory packages/py/citry --group e2e pytest -q -m e2e \
  tests/e2e/test_ownership_manifest_e2e.py \
  tests/e2e/test_client_graph_corpus_e2e.py \
  --browser chromium
uv run --no-sync python scripts/protocol_runtime_baseline.py --timings
```
