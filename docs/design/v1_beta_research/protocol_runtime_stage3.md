# Protocol runtime ownership: Stage 3

**Status (2026-08-04): complete; independent review passed.**

Stage 3 moves the browser's fixed `citry-events/1` construction and validation
into the private JavaScript protocol package. The product runtime still owns
DOM work, Alpine state, transport choice, request execution, timers, queues,
downloads, and application of already-validated actions.

## Ownership moved

The package at `packages/protocol/events/v1/js/` now owns:

- the complete TypeScript view of calls, results, actions, errors,
  capabilities, descriptors, instances, and manifests;
- protocol, action, swap, error-code, capability, and call-limit vocabulary;
- strict JSON checks and defensive copies of application-owned JSON;
- outgoing call and call-envelope construction;
- incoming result, action, error, descriptor, instance, and manifest checks;
- request ID, result count, `sendSequence`, capability, data-action, and
  transport-edge relationships; and
- deterministic first issues with the shared JSON Pointer and category
  contract.

The browser runtime imports the package as a pnpm workspace dependency. esbuild
includes it in the existing `citry-events.js` IIFE. There is no separately
published npm package, browser global, additional request, or load-order
dependency.

## Product boundaries

`citry-events.ts` now gives normalized facts to `buildCall` and
`buildCallEnvelope`. It passes untrusted result envelopes through complete
preflight before settling any result, and passes manifests through complete
validation before mutating class or instance registries. The public
`applyActions` entry point uses the same action-list validator.

The package returns a validated manifest to the staging adapter. Later
ownership callbacks receive that staged value rather than returning to the
untrusted parsed object. Result preflight validates every slot before the
product applies the first action, preserving batch atomicity.

The old product-local field sets, vocabularies, manifest checker, result
checker, action checker, and envelope literals were removed. Product-only
checks remain where they depend on live DOM or runtime state.

## Executable coverage

The JavaScript package compiles its TypeScript entry with esbuild during its
Node tests. It then:

- applies every shared JavaScript conformance mutation and requires the exact
  expected issue path and category;
- accepts every valid descriptor, manifest, call, and result example and
  rejects every invalid descriptor and manifest example;
- checks every ordinary golden call/result relationship;
- checks builder copies, cycles, non-finite values, sparse arrays, hidden and
  symbol-keyed fields, accessors, batch atomicity, and valid and invalid
  transport-edge errors; and
- runs under the client package's ES2020 type boundary.

The browser pass covers real transport capture, result preflight, manifest
staging, public action validation, atomic rejection, edge fan-out, downloads,
and live server round trips. The committed-bundle canary reconstructs the IIFE
and compares it byte for byte with the shipped file.

## Moving payload baseline

The Stage 3 opening Events artifact was 290,278 bytes. The reviewed
protocol-owned Events artifact is 326,781 bytes with SHA-256
`cdca0dfb56dc584ddb2cc601d89dd410296fa164c7a5a7c09b09ae9ef7fa896a`.
That 36,503-byte raw increase crossed the earlier hard payload guard. The
maintainer approved the protocol-binding cost before work continued. The
closing value includes the later builder-copy, carrier-ownership, strict
in-memory JSON, and download-identity review corrections.

Concurrent client-graph work then moved `citry.js` to 319,508 bytes. The Stage
3 closing snapshot is 646,289 raw and 134,882 deterministic gzip bytes. The
moving guards are 647,000 raw and 136,000 gzip, leaving 711 raw and 1,118
gzip bytes of headroom. This records concurrent movement separately from the
Events artifact's attributable increase. Broader optimization remains part of
the dedicated benchmarking work.

## Verification

- The built-in package checker passed 19 exchanges, 9 descriptors, and 8
  manifests.
- The JavaScript protocol package passed type checking, lint, and 11 runtime
  tests.
- The browser package passed type checking, lint, 10 pinned-runtime canaries,
  bundle rebuilding, and exact source-to-bundle comparison.
- The focused Python protocol, payload, action, binding, dispatcher, and route
  selection passed 509 tests.
- The Chromium transport, client-manifest, and action-applier selection passed
  99 tests. Three focused GET and form-carrier tests passed again after the
  carrier-name ownership correction.
- The moving-baseline snapshot recorded content identity
  `c8e46be907bb2b0b8d59c40215edb93d342c56765ca9d20cc0c37c7937d000f5`.

## Work held for later stages

Stage 3 does not claim exhaustive mutation coverage for every schema keyword.
The bounded shared case set now executes in both languages, while the complete
constraint audit remains a Stage 6 completion gate. Firefox and WebKit also
remain in the final browser matrix rather than multiplying this bounded stage.

## Commands

```bash
python -S packages/protocol/events/v1/validate.py
pnpm --dir packages/protocol/events/v1/js run check
pnpm --dir packages/js/citry-client run build
pnpm --dir packages/js/citry-client run check
uv run pytest -q \
  packages/py/citry/tests/test_client_performance_payload.py \
  packages/py/citry/tests/test_events_protocol_runtime.py \
  packages/py/citry/tests/test_events_actions.py \
  packages/py/citry/tests/test_events_bindings.py \
  packages/py/citry/tests/test_events_dispatch.py \
  packages/py/citry/tests/test_events_routes.py
uv run --directory packages/py/citry --group e2e pytest -q -m e2e \
  tests/e2e/test_events_transport_e2e.py \
  tests/e2e/test_events_client_e2e.py \
  tests/e2e/test_events_applier_e2e.py \
  --browser chromium
python scripts/protocol_runtime_baseline.py --details
```
