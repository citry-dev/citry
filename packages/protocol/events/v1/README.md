# citry-events/1

Citry Events turns a browser interaction into a named server call, then turns
the server's answer into browser actions. A click might send `save` with JSON
arguments; the answer might replace a component, update a state token,
dispatch a DOM event, or resolve the caller with data.

This directory is the language-neutral contract for protocol major 1. It
defines the JSON sent in both directions and the inert manifest that teaches
the browser which handlers and State belong to each rendered component.

Start with [`spec.md`](spec.md). It walks through a complete exchange before
defining the exact fields and checks.

## What is in this directory

- [`spec.md`](spec.md) explains calls, results, actions, the browser manifest,
  HTTP adapters, strict validation, and conformance.
- [`call.schema.json`](call.schema.json) defines the client-to-server call
  envelope.
- [`result.schema.json`](result.schema.json) defines the server-to-client
  result envelope and every v1 action.
- [`descriptor.schema.json`](descriptor.schema.json) defines one component
  class descriptor from the browser manifest.
- [`manifest.schema.json`](manifest.schema.json) defines the complete
  `data-citry-events` JSON block.
- [`validate.py`](validate.py) checks the package without third-party
  dependencies.
- [`tests/`](tests/) contains golden call/result exchanges plus valid and
  deliberately invalid descriptor and manifest examples.

## Who follows this contract

The Python server's [`emission.py`](../../../py/citry/citry/ext/events/emission.py)
writes manifests and its
[`dispatcher.py`](../../../py/citry/citry/ext/events/dispatcher.py) accepts
calls and produces results. The browser's
[`citry-events.ts`](../../../js/citry-client/src/citry-events.ts) reads
manifests, creates calls, validates complete result envelopes, and applies
their actions.

The shared examples keep both sides honest:

- [`test_events_conformance.py`](../../../py/citry/tests/test_events_conformance.py)
  renders the conformance component and replays every golden exchange through
  the real Python dispatcher.
- [`test_events_protocol_package.py`](../../../py/citry/tests/test_events_protocol_package.py)
  exercises the schemas and package validator.
- [`test_events_applier_e2e.py`](../../../py/citry/tests/e2e/test_events_applier_e2e.py)
  replays the result examples through the browser action interpreter.
- [`test_events_transport_e2e.py`](../../../py/citry/tests/e2e/test_events_transport_e2e.py)
  checks browser-created calls, strict result validation, HTTP transport, and
  full live round trips.

## Running the checks

From the repository root:

```bash
# Language-neutral package check.
python -S packages/protocol/events/v1/validate.py

# Server writer and dispatcher conformance.
python -m pytest \
  packages/py/citry/tests/test_events_protocol_package.py \
  packages/py/citry/tests/test_events_conformance.py

# Browser reader and transport. Repeat with Firefox and WebKit before release.
python -m pytest \
  packages/py/citry/tests/e2e/test_events_applier_e2e.py \
  packages/py/citry/tests/e2e/test_events_transport_e2e.py \
  --browser chromium
```

The normal repository gate also runs the language-neutral validator and the
non-browser tests:

```bash
python scripts/check.py --reporter agent
```

## What strict means in v1

Fixed protocol records accept exactly their documented fields. Missing
required fields, extra fields, unknown action kinds, unknown swaps, unknown
capabilities, and unknown error codes are errors on both sides. The browser
validates a complete result envelope before applying its first action, so a
bad later action cannot leave an earlier side effect behind.

Only intentional application-data containers are open:

- handler names inside `eventHandlers`;
- `args`, `stateUpdates`, `publicState`, and `fieldErrors` keys;
- the JSON value of a `data` action and the optional `detail` of an `event`
  action.

This is deliberate. There is no installed-base compatibility need yet, and a
future extension point should be designed when a real use case appears.

## Changing the protocol

A wire change is not done until all of these move together:

1. Explain the rule in [`spec.md`](spec.md).
2. Update every affected schema.
3. Teach [`validate.py`](validate.py) the relationship if JSON Schema cannot
   express it clearly.
4. Update the Python writer or dispatcher and the TypeScript browser reader.
5. Add a golden exchange or valid/invalid corpus case that proves the rule.
6. Run the server and browser conformance suites.

When the protocol is changed, every producer, consumer, schema, example, test,
and current document must change together.

This protocol package is not separately published. It ships inside Citry. See
[`docs/codebase.md`](../../../../docs/codebase.md) for the monorepo release
process.
