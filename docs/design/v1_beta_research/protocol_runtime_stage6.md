# Protocol runtime ownership: Stage 6

**Status (2026-08-04): implementation complete; independent review passed;
the full repository gate is blocked by concurrent work listed below.**

Stage 6 closes the executable protocol-ownership work from GitHub issue #39.
It checks that every schema rule has an implementation owner, audits the real
server and browser boundaries, proves the built distribution, and exercises the
protocols across the supported browser engines. It does not turn the protocol
tooling into a general JSON Schema compiler.

## Constraint ownership

Each protocol now has a `tests/constraint-ownership.json` registry. Every
structural schema constraint belongs to exactly one named validator family.
Each family names its schema selection, Python validator, JavaScript validator,
and supporting test files. The checker rejects missing and overlapping
assignments, missing source symbols, and any schema change that does not update
the registry's count and fingerprint.

| Protocol schema | Constraints | Assigned | Families | Exact mutation coverage |
| --- | ---: | ---: | ---: | ---: |
| Events call | 37 | 37 | 3 | 6 |
| Events descriptor | 24 | 24 | 2 | 4 |
| Events manifest | 49 | 49 | 3 | 2 |
| Events result | 147 | 147 | 4 | 7 |
| Client graph manifest | 215 | 215 | 11 | 13 |
| **Total** | **472** | **472** | **23** | **32** |

The 35 shared mutation records touch 32 unique structural constraints. Those
cases remain the precise cross-language proof that Python and JavaScript return
the same first issue path and category after one controlled edit. Ownership is
broader: it proves that all 472 constraints are routed to concrete validators
and tests, but it does not claim 472 separate mutation cases. The optional
exhaustive expansion is isolated in
[#54](https://github.com/citry-dev/citry/issues/54).

The protocol tooling's own suite has 23 tests for selection, fingerprints,
overlap, missing assignments, and source/test references. Its live report has
no package problems.

## Producer and consumer audit

The fixed wire vocabulary is owned by the private protocol packages. The audit
found no remaining product-local closed field set, protocol literal, action
vocabulary, canonicalizer, revision algorithm, or ownership-comment parser.

| Direction | Product boundary | Protocol-owned operation |
| --- | --- | --- |
| Server to browser, client graph | `ownership_manifest.py` selects settled render-tree facts | record builders, graph and manifest assembly, comments, revision, validation, serialization |
| Server to browser, Events | actions, errors, results, emission, OpenAPI, dispatcher, and routes | closed builders, strict validation, carrier conversion, manifest and result envelopes |
| Browser to server, Events | `citry-events.ts` gathers call state and chooses transport | call and envelope construction plus strict outgoing validation |
| Server receiving Events | dispatcher and route adapters | call-envelope validation before dispatch |
| Browser receiving Events | Events transport and manifest processor | manifest staging and complete result-envelope preflight before application |
| Browser receiving client graph | generated block in `citry.js` | complete logical validation and ownership-comment parsing before DOM work |

The product still owns facts that are not wire grammar: record selection,
live-DOM cap discovery and pairing, physical placement, lifecycle state,
dispatch, transport, and action effects. Existing boundary tests capture calls
at the transport edge, mutate server results and manifests, and exercise
atomic rejection before product state changes.

## Distribution proof

`scripts/verify_citry_distribution.py` builds a Citry wheel and sdist, builds a
second wheel from the sdist outside the checkout, compares inventories and
file hashes, and installs both wheels into fresh environments outside the
repository. The smoke process removes Node from `PATH`, verifies that
`jsonschema` is absent, imports the top-level package, runs CLI help, exercises
both embedded protocol packages, checks both shipped browser files, and checks
`py.typed`.

The final proof used a locally built companion `citry-core` wheel because the
working tree contains an unreleased core API:

| Artifact | Files | Bytes | Content SHA-256 |
| --- | ---: | ---: | --- |
| Installed Citry payload | 121 | n/a | `0cb389436ebb49b2a1ff3af064b31e827d0cf6c2c7dab1187b408f285f091221` |
| Source wheel | 127 | 667,504 | `f5346119347a5ed4dab430a7d15b9741539cb1b25e23ee913b2a09155229cacc` |
| Wheel rebuilt from sdist | 127 | 667,504 | `f5346119347a5ed4dab430a7d15b9741539cb1b25e23ee913b2a09155229cacc` |
| Sdist | 232 | 1,148,032 | `53083c251a5aadc0dfe583d3843a3dd480a519d702244586f98c07c501d7c2dc` |

The source wheel archive SHA-256 was
`be9c28ed273010c81513ec0f5d1382496b70b972b05bdd6280546ffc0f0f619b`;
the rebuilt wheel archive SHA-256 was
`18a627e57b4798ac5144c140f554fd10b3bf48dae526bea2bd07a6344cc505a0`.
Archive metadata can differ, so the verifier compares normalized member names,
sizes, and content hashes instead of requiring byte-identical zip containers.
The sdist archive SHA-256 was
`606babd5cb11c1621110394d478364966389e1e3918d9048e7258e52a8048271`.
Both isolated smoke environments reported `nodeAvailable: false` and
`jsonschemaInstalled: false`.

A plain install against current PyPI correctly fails. The working Citry tree
imports an unreleased companion-core API; the current first missing module is
`citry_core.template_formatter`, which is absent from the published
`citry-core==1.4.0` wheel. This is a release-order blocker, not a reason to
weaken the smoke test: publish the matching core release before the Citry
release. The Citry publish workflow now runs the artifact verifier and
therefore enforces that order.

The Citry package metadata now uses the PEP 639 license expression, includes a
package-local MIT `LICENSE`, and requires a sufficiently recent setuptools to
build that metadata consistently.

## Documentation and CI

The protocol READMEs explain the difference between validator ownership and
exact mutation cases and give the local commands. `docs/codebase.md` documents
canonical packages, embedded Python copies, generated JavaScript boundaries,
the ownership checker, distribution verification, and release ordering.
`docs/agent/INDEX.md` points future agents to that operational source.

The Citry publish workflow runs the distribution verifier against the artifacts
it is about to publish. Existing repository checks continue to run the protocol
checker, embedded-copy freshness, both JavaScript packages, and the product
client build. Rebuilding the Events bundle also refreshed the docs playground's
committed copy; its check passes.

## Browser and payload proof

The complete focused protocol matrix passed 594 tests in Chromium, Firefox,
and WebKit. It covers ownership-manifest staging, the shared client-graph
corpus, Events transport, client lifecycle, and result application.

The matrix exposed three browser-owned differences and one portable diagnostic
problem. Citry now includes the normalized save error message in its own
console text because Firefox otherwise displays only `Error`. Tests accept the
optional browser network diagnostic for an intercepted HTTP 500 and compare
WebKit download filenames after Unicode NFC normalization. The four corrected
cases pass in all three engines before and as part of the complete matrix.

The final browser artifacts remain below the maintainer-approved guard:

| Artifact | Raw bytes | SHA-256 |
| --- | ---: | --- |
| `citry.js` | 320,067 | `094d943eef233baed5a4707b307d6b7feadead7149c4b22bec9f5beb28c276f1` |
| `citry-events.js` | 327,663 | `d4e72572c9665219bcab5e13a2b315c748ebac145d2634f316dd797f71c9b41f` |
| Combined | 647,730 | n/a |
| Deterministic gzip | 136,955 | n/a |

The 649,000 raw / 138,000 gzip guard has 1,270 raw and 1,045 gzip bytes of
headroom.

## Bounded performance check

The final seven-sample medians were:

| Scenario | Comparison baseline | Final | Difference |
| --- | ---: | ---: | ---: |
| One Events dispatch | 17.580 us | 17.097 us | -0.483 us, -2.7% |
| Sixteen Events dispatches | 244.181 us | 207.907 us | -36.274 us, -14.9% |
| 25-component graph document | 14.121 ms | 14.526 ms | +0.405 ms, +2.9% |
| 325-component graph document | 233.768 ms | 236.438 ms | +2.670 ms, +1.1% |

No comparison satisfies both parts of the stop rule. The graph comparison uses
the Stage 4 opening measurement immediately before the graph runtime migration.
The much older Stage 0 graph documents are not comparable because unrelated
graph and browser features continued landing in the shared working tree, as
the moving-baseline policy anticipated. Broader performance exploration stays
in the dedicated benchmarking work.

## Independent review corrections

The adversarial review found two cross-language differences before sign-off.
Python's public Events validators checked object shape before strict JSON, so a
cycle could report a required or type issue while JavaScript reported
`strict_json`. Python also rejected JSON-decoded integral numbers such as
`1.0` in integer schema fields even though JavaScript and JSON Schema accept
them. Both differences are corrected in the canonical package and embedded
copy.

All 11 public Events schema-boundary validators now have Python and JavaScript
cycle coverage that locks the first issue path and category. Both runtimes also
have integral-number coverage. The Python strict-JSON checker uses a shallow
recursive fast path and falls back to the iterative walker for very deep values;
a 1,500-level value and cycle lock that behavior without imposing a protocol
depth limit. Composed validators and server-owned result builders reuse already
completed checks so strict boundary validation does not multiply work
internally. The initial strict-first implementation crossed the performance
stop rule; the corrected implementation produces the final measurements above
and clears it.

## Full repository gate

`python scripts/check.py --reporter agent` ran to completion. The protocol
contracts, Python-copy freshness, Events JavaScript, client-graph JavaScript,
Citry client, validators, Rust checks, typing checks, and VS Code extension all
passed. The initially stale docs-playground result was caused by the final
Events rebuild; its generated copy was refreshed and now passes.

The aggregate gate is still red because concurrent, non-Stage-6 work currently
has:

- 10 Ruff findings and five Ruff-format candidates in the in-progress Python
  template-formatting work, plus an intentionally invalid Python fixture that
  the repository-wide formatter check currently tries to parse;
- one reproducible failure in
  `test_independent_fragment_revision_cannot_overwrite_document_fill_routes`,
  where inserting the fetched fragment destroys the page execution context;
  and
- total coverage of 90.95% against the required 93% after the concurrent code
  expansion.

Those files and behavior were not changed to make Stage 6 appear green. They
must be resolved by their active work before the repository can publish. The
focused Stage 6 suite itself remains green.

## Focused verification

- 365 focused Events protocol, package, dispatcher, and route tests passed.
- The combined protocol ownership, distribution, package, runtime,
  conformance, and ownership-manifest suite passed 214 tests.
- The protocol tooling plus focused distribution suite passed 25 tests.
- The Events standalone checker passed 19 exchanges, 9 descriptors, and 8
  manifests without `jsonschema`.
- The client-graph standalone checker passed all 47 examples without
  `jsonschema`.
- Events JavaScript passed 13 tests; client-graph JavaScript passed 15 tests,
  build freshness, and the prototype check; the Citry client passed 10
  canaries and exact source-to-bundle comparison.
- The corrected browser subset passed 12 tests across three engines; the full
  focused matrix passed 594.
- `uv lock --check`, embedded-copy freshness, protocol tooling, scoped Ruff,
  package builds, docs-playground freshness, and the isolated distribution
  verifier passed.

Independent review passed with no remaining Stage 6 blocker. The final moving
scope contains 332 paths and has content identity
`5ffab48541afdf1b1ffea3326769efe7591c38b71e86053e14d513011064186f`.

## Commands

```bash
uv run --no-sync python -m packages.protocol._tooling.check \
  packages/protocol/events/v1 packages/protocol/client_graph/v1
uv run --no-sync python scripts/sync_protocol_python.py --check
pnpm --dir packages/protocol/events/v1/js run check
pnpm --dir packages/protocol/client_graph/v1/js run check
pnpm --dir packages/js/citry-client run check
uv run --no-sync python scripts/verify_citry_distribution.py \
  --core-wheel /path/to/current/citry_core.whl
uv run --directory packages/py/citry --group e2e pytest -q -m e2e \
  tests/e2e/test_ownership_manifest_e2e.py \
  tests/e2e/test_client_graph_corpus_e2e.py \
  tests/e2e/test_events_transport_e2e.py \
  tests/e2e/test_events_client_e2e.py \
  tests/e2e/test_events_applier_e2e.py \
  --browser chromium --browser firefox --browser webkit
uv run --no-sync python scripts/protocol_runtime_baseline.py --timings
python scripts/check.py --reporter agent
```
