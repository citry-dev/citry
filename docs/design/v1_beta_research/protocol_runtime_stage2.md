# Protocol runtime ownership: Stage 2

**Status (2026-08-04): complete; independent review passed.**

Stage 2 moves the Python server's fixed `citry-events/1` wire construction and
validation into the versioned protocol package. Product code still decides
which handler runs, how State changes, and which HTTP response mode applies.

## Ownership moved

The canonical package now owns:

- protocol, action, swap, error-code, capability, call-limit, and reserved
  carrier vocabularies;
- deterministic `ValidationIssue` values and strict-JSON parsing, checking,
  and copying;
- call and capability validation before the first handler runs;
- action, result, error, rejection, and final result-envelope construction;
- validation of mappings returned by `on_event_result` and
  `on_event_error`;
- component descriptor, instance, and Events manifest construction;
- decoded flat/form/query carrier splitting and per-event route completion;
- the fixed OpenAPI error records.

The canonical files live in
`packages/protocol/events/v1/python/citry_events/`. The byte-identical shipped
copy lives in `packages/py/citry/citry/_protocol/events/` and is maintained by
`scripts/sync_protocol_python.py`. Neither location uses `jsonschema` or any
other runtime dependency.

## Compatibility evidence

The focused server pass currently covers 449 existing and new tests across
actions, dispatch, emission, routes, golden exchanges, and runtime ownership.
The shared mutation records run directly against the embedded validators. Call
mutations also pass through the real dispatcher and must produce the same
protocol-owned message before any application handler could run.

Existing behaviors retained by focused tests include mirrored batch failures
when a request ID permits per-call correlation, `sendSequence` echoes, strict
JSON, the pointed unencodable-result response, capability downgrade rules,
explicit hook-authored `data.delay: 0`, omitted zero delay from builders,
script-safe manifest transport, GET carrier defaults, and compatibility-mode
responses.

A malformed request without a usable `requestId` cannot correlate result slots.
It therefore produces the one transport-edge error permitted by
`result.schema.json`, even when the malformed input contains multiple calls.
Both the dispatcher and the real batch route cover this case. The HTTP encoder
also validates every final result envelope through the embedded protocol
package before serialization.

## Performance evidence

The Stage 0 medians were 17.580 microseconds for one Events call and 244.181
microseconds for sixteen calls. The corrected Stage 2 run measured 17.623 and
234.998 microseconds respectively using the same seven-sample command. The
single-call change is below both parts of the stop threshold, and the batch is
faster.

The moving-baseline snapshot at this close found the shipped Events browser
bundle at 290,278 bytes with SHA-256
`b96e27e5c318118590b578ccf0f7d18597e717585eb973cfa228f3cc3d97750f`.
It changed concurrently after the first Stage 2 snapshot. Stage 2 does not
edit browser code, so this records the observed close rather than attributing
the change to the Python migration.

## Independent review corrections

The first adversarial review found four blockers, all corrected before
re-review:

- wire validators now reject non-JSON mapping containers, while builders
  normalize the mapping inputs their signatures declare;
- strict parsing and every numeric wire field reject integers a browser would
  parse as a non-finite number;
- multi-fault cases lock schema field order and keep relationship checks after
  structural checks; and
- product code imports the protocol-owned swap vocabulary, while exchange
  validation reuses the protocol-owned capability baseline.

The independent re-review reproduced all four original failures against the
corrected code and passed Stage 2. Its separate timing sample measured 17.940
microseconds for one call and 233.353 microseconds for sixteen calls, also
within the Stage 0 guard.

## Scope held for later stages

The browser implementation and complete JavaScript conformance pass belong to
Stage 3. The conformance report still shows uncovered schema constraints; the
bounded Stage 1 mutation set remains a coverage report rather than a claim of
complete constraint coverage. Stage 3 runs the shared cases against the actual
JavaScript validators and adds cases needed by the migrated boundaries. The
exhaustive constraint audit remains the Stage 6 completion gate, where any new
case must pass in Python and JavaScript together.

## Commands

```bash
uv run --no-sync python scripts/sync_protocol_python.py --check
uv run --no-sync python packages/protocol/events/v1/validate.py
uv run --no-sync python -m packages.protocol._tooling.check \
  packages/protocol/events/v1 packages/protocol/client_graph/v1
uv run --no-sync pytest -q \
  packages/py/citry/tests/test_events_protocol_runtime.py \
  packages/py/citry/tests/test_events_actions.py \
  packages/py/citry/tests/test_events_dispatch.py \
  packages/py/citry/tests/test_events_emission.py \
  packages/py/citry/tests/test_events_routes.py \
  packages/py/citry/tests/test_events_conformance.py
uv run --no-sync python scripts/protocol_runtime_baseline.py --timings
```

At the recorded close, the Events contract report had no problems. The combined
contract command also reported two client-graph conformance records whose
constraint paths no longer exist in the concurrently changing client-graph
schema. That separate working-tree condition is not caused by the Events
Python migration and must be resolved before the repository-wide gate passes.
