# Events Python runtime

`citry_events` is the canonical Python implementation of the fixed
`citry-events/1` wire contract. It builds and validates calls, results,
actions, errors, component descriptors, browser manifests, and decoded GET
carrier fields. It uses only the Python standard library.

Citry does not publish this as a separate package. Run
`python scripts/sync_protocol_python.py` from the repository root to copy it
byte for byte into `citry._protocol.events`. The repository gate runs the same
command with `--check` and fails when the shipped copy is missing, extra, or
stale.

Ordinary invalid wire data produces a `ValidationIssue` with an RFC 6901
`path`, stable `category`, and explanatory `message`. Validators return the
first issue and do not mutate their input. Builders raise `ProtocolValueError`
carrying that issue and return fresh copies of open application JSON.

Run the focused checks with:

```bash
uv run --no-sync python scripts/sync_protocol_python.py --check
uv run --no-sync pytest -q \
  packages/py/citry/tests/test_events_protocol_runtime.py \
  packages/py/citry/tests/test_events_conformance.py
```
