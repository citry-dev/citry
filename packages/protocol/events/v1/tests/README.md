# Worked examples for citry-events/1

This directory holds three small corpora:

- the top-level `*.call.json` and `*.result.json` files are golden exchanges
  for the conformance component in [`../spec.md`](../spec.md);
- [`descriptors/`](descriptors/) contains component class descriptors the
  schema must accept or reject;
- [`manifests/`](manifests/) contains complete browser manifests the schema
  and relationship checks must accept or reject.

Run every corpus with:

```bash
python -S packages/protocol/events/v1/validate.py
```

## Golden exchanges

Each exchange has a call file and the result a conforming server returns. A
server binding passes when it replays every call and matches the corresponding
result exactly, except for the environment-dependent values listed in
`dynamic_fields`.

The runner starts each exchange from a fresh render of the conformance
`Counter`, substitutes live call values such as its class ID, render ID, and
state token, sends the call, then masks the named dynamic result values before
comparison. Everything else must match exactly and validate against the
schemas.

[`index.json`](index.json) is the machine-readable list:

```json
{
  "call": "happy_render.call.json",
  "result": "happy_render.result.json",
  "dynamic_fields": ["call.calls[0].stateToken"]
}
```

`dynamic_fields` means fields whose concrete values naturally change between
renders or environments. It is not permission to ignore unstable output. A
path must start with `call.` or `result.`, use `.key` for object fields and
`[n]` for array indexes, and name one complete value. Call paths are replaced
before dispatch; result paths must exist but are ignored during exact
comparison.

Typical dynamic values are class IDs, render IDs, state tokens, rendered HTML,
and self-addressed `render:` targets derived from a live render ID.

| Exchange | What it proves |
|---|---|
| `happy_render` | A stateful call returns a `morph` render when advertised and echoes `sendSequence`. |
| `baseline_swap` | Omitting capabilities uses the v1 baseline, so `morph` becomes `replace`. |
| `data_only` | A stateless call can omit caller State metadata and return one data value. |
| `history` | `push` and `replace` history actions retain their authored order and timing. |
| `rename_coerce` | A State mutation returns the token refresh first, then an event and data value. |
| `batch_two` | `results[i]` answers `calls[i]`, including mixed stateful and stateless calls. |
| `error_invalid_args` | `invalid_args` carries a strict `fieldErrors` map. |
| `error_invalid_state` | A malformed or tampered token answers `invalid_state`. |
| `error_stale_state` | An expired or rotated-out token answers `stale_state`. |
| `error_unknown_event` | An undeclared handler answers `unknown_event`. |
| `error_unknown_component` | An unregistered class ID answers `unknown_component`. |
| `error_forbidden` | A guard-raised 403 answers `forbidden`. |
| `error_not_found` | A user-raised 404 answers `not_found`. |
| `error_conflict` | A user-raised 409 answers `conflict`. |
| `error_generic` | Another user-raised status uses code `error` and keeps its status. |
| `error_csrf_failed` | A transport CSRF rejection answers `csrf_failed`. |
| `error_payload_too_large` | More than 16 calls rejects the whole envelope and mirrors one error per slot. |
| `error_protocol_mismatch` | An unknown protocol major rejects the whole envelope. |
| `error_handler_error` | An unexpected exception answers the generic non-debug handler error. |

`error_stale_state` needs the harness to mint a token that is already expired
or signed only by a rotated-out secret. `error_csrf_failed` needs the harness
to fail the transport's CSRF check.

`error_payload_too_large.call.json` and
`error_protocol_mismatch.call.json` are deliberate rejection inputs, so each
violates exactly the rule its result demonstrates. `validate.py` repairs only
that one fault before checking the rest of the call shape.

## Descriptor corpus

[`descriptors/index.json`](descriptors/index.json) lists `valid` and `invalid`
files. The valid examples cover the smallest descriptor and all optional
handler hints. The invalid examples prove that required fields, exact field
names, uppercase HTTP methods, and default-value omission are strict.

## Manifest corpus

[`manifests/index.json`](manifests/index.json) also lists `valid` and `invalid`
files. Besides JSON shape, the validator checks relationships that are easier
to understand in code than in JSON Schema:

- component class IDs and render IDs are unique;
- every component instance refers to a class in the same manifest;
- a stateless instance has `stateToken: null` and an empty `publicState`.

## Adding or changing an example

1. Make the rule clear in the spec and schema first.
2. Add the smallest example that proves it. For a rejection rule, prefer a
   valid example and a copy with one deliberate fault.
3. Add it to the relevant `index.json`.
4. Run `validate.py`, Python conformance, and browser conformance.
5. Update the tables above when the example introduces a new behavior.

Do not make an existing expected file match accidental implementation output.
If the protocol itself changed, update the spec, schemas, validator,
implementations, and examples as one change.
