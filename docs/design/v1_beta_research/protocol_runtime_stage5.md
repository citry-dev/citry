# Protocol runtime ownership: Stage 5

**Status (2026-08-04): complete; independent review passed.**

Stage 5 moves the browser's fixed `citry-client-graph/1` validation into the
private JavaScript protocol package. The core runtime still owns physical
comment-cap discovery and every check that needs live DOM nodes.

## Ownership moved

The package at `packages/protocol/client_graph/v1/js/` now owns:

- the complete TypeScript view of the manifest and every graph record;
- strict in-memory JSON checks for cycles, non-finite numbers, sparse arrays,
  symbols, hidden fields, accessors, and non-JSON objects;
- exact closed record shapes, scalar rules, and deterministic first issues;
- canonical JSON, synchronous SHA-256 revisions, and revision comparison;
- every logical reference, identity, ancestry, fill, slot-region, binding, and
  component execution-order relationship; and
- the literal `citry:g1` ownership-comment parser shared by both browser
  bundles.

The runtime validator accepts all 9 valid manifests and rejects all 38 invalid
manifests. It also executes every shared structural mutation with the exact
expected issue path and category and matches all 13 cross-language
canonicalization vectors.

## Generated core boundary

`build.mjs` bundles `src/core-embed.ts` for ES2020, minifies it, and places it
between one marker pair immediately after the core IIFE's outer `"use strict"`
directive. The initial insertion required `build:initialize`. Normal builds
replace only the marked bytes. Check mode reconstructs the complete expected
file in memory and rejects an absent, duplicated, moved, reversed, or stale
region.

The generated browser API contains only the ownership-comment prefix and
parser, `ProtocolValueError`, and `assertValidManifest`. Product code no longer
repeats closed field sets, canonicalization, hashing, logical graph checks, or
the canonical ownership-comment parser.

The Events TypeScript source imports the same comment parser as a workspace
dependency. esbuild includes that small helper in `citry-events.js`, preserving
the pre-existing core-before-Events order while avoiding a new request or a new
dependency on the generated `CitryClientGraphProtocol` global.

## Product boundary and atomicity

Core staging validates the complete manifest through
`assertValidManifest` before walking DOM comments. It then derives the expected
component-instance and slot-region caps, checks their physical pairing and
nesting, and freezes the staged snapshot only after every logical and physical
check succeeds.

The product keeps physical-cap pairing, same-parent topology, crossing and
closure checks, physical parent slot-region checks, lifecycle state, registry
mutation, and adoption. These rules cannot live in the protocol package
because they depend on the current document.

Browser corpus assertions now inspect the stable protocol issue `path` and
`category` rather than the old product validator's message prose. All 15
shared mutations also run through the real browser staging function. Invalid
manifests are rejected before the missing-cap fallback, and existing ownership
tests retain the atomic staging and adoption boundary.

## Approved browser payload guard

The Stage 4 opening pair was 646,821 raw and 134,997 deterministic gzip bytes.
The first complete Stage 5 build measured 647,618 raw and 136,958 gzip, crossing
the previous 647,000 / 136,000 moving guard. The maintainer approved raising
the guard before work continued.

The target guard is 649,000 raw and 138,000 gzip. After the review correction
that removed the remaining product-local comment parser, the current artifacts
are 647,660 raw and 136,932 gzip, leaving 1,340 raw and 1,068 gzip bytes of
headroom:

| Artifact | Raw bytes | SHA-256 |
| --- | ---: | --- |
| `citry.js` | 320,067 | `094d943eef233baed5a4707b307d6b7feadead7149c4b22bec9f5beb28c276f1` |
| `citry-events.js` | 327,593 | `c0c5fe058117b5fd706b99a99a4e7be2f85d718858c536a9771af9c9d3bf9d9f` |

The committed marker-to-marker span is 34,676 bytes including its markers.
Broader
payload optimization remains assigned to the dedicated benchmarking work.

## Verification before review

- The standalone checker passed all 47 fixtures without `jsonschema`.
- The JavaScript client-graph package passed type checking, lint, generated
  freshness, payload reporting, and 15 runtime tests.
- The JavaScript Events package passed type checking, lint, and 11 runtime
  tests.
- The client source package passed type checking, lint, 10 canaries, and exact
  source-to-bundle comparison.
- The documented focused Python selection passed 79 tests: 75 client-graph
  and writer tests plus 4 payload-budget tests.
- The focused Chromium client-graph selection passed 99 tests, including all
  15 shared issue cases at browser staging and direct physical-comment parser
  coverage.
- The focused Chromium Events selection passed 99 tests after the shared
  ownership-comment parser migration.
- Protocol tooling found no package problems. Its bounded mutation inventory
  covers 13 of 215 schema constraints; the exhaustive audit remains Stage 6.
- The payload budget selection passed with the approved guard.

The closing scope identity from `protocol_runtime_baseline.py` is
`033128db239c7812115ba4e4ec66f0a38a934c9b2c4c6e155330d59ad7ef5ed6`.

## Independent review

The first adversarial pass found four review gaps and one later call-site bug,
all corrected before PASS:

- core physical-cap scanning now uses the protocol-owned ownership-comment
  parser rather than repeating the comment suffix grammar;
- generated-boundary tests now lock surrounding-byte preservation and reject
  duplicate, reversed, moved, and invalid-initialization markers;
- documentation now distinguishes the parser's lack of a generated-global
  dependency from the pre-existing core-before-Events runtime order;
- evidence reports the actual committed marker span and complete focused test
  count; and
- both initial staging and commit-time live adoption use the corrected
  physical-cap validator signature.

The reviewer independently reproduced 47-fixture Python/JavaScript first-issue
parity, all 15 shared cases, 13 canonical vectors, 79 focused Python tests, 99
Chromium client-graph tests, 99 Chromium Events tests, package and generated
freshness checks, protocol tooling, the approved payload guard, and the exact
closing hashes. No Stage 5 blocker remains.

## Commands

```bash
python -S packages/protocol/client_graph/v1/validate.py
pnpm --dir packages/protocol/client_graph/v1/js run check
pnpm --dir packages/js/citry-client run check
pnpm --dir packages/protocol/events/v1/js run check
uv run pytest -q \
  packages/py/citry/tests/test_client_graph_protocol_runtime.py \
  packages/py/citry/tests/test_client_graph_protocol_package.py \
  packages/py/citry/tests/test_client_graph_conformance.py \
  packages/py/citry/tests/test_ownership_manifest.py \
  packages/py/citry/tests/test_client_performance_payload.py
uv run --directory packages/py/citry --group e2e pytest -q -m e2e \
  tests/e2e/test_ownership_manifest_e2e.py \
  tests/e2e/test_client_graph_corpus_e2e.py \
  --browser chromium
uv run --directory packages/py/citry --group e2e pytest -q -m e2e \
  tests/e2e/test_events_transport_e2e.py \
  tests/e2e/test_events_client_e2e.py \
  tests/e2e/test_events_applier_e2e.py \
  --browser chromium
uv run --no-sync python scripts/protocol_runtime_baseline.py
```
