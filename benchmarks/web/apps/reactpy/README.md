# ReactPy project board

This app uses ReactPy 1.1.0's Python components, state hooks, native form
events and WebSocket layout updates. Starlette 0.52.1 and Uvicorn 0.52.4 serve
the production application. Starlette 1.x removed `add_websocket_route`, which
ReactPy's supported backend still calls, so this app pins the compatible
0.x release. Package versions were checked on 2026-09-10.

The implementation follows ReactPy's official
[production backend guidance](https://reactpy.dev/docs/guides/getting-started/running-reactpy.html)
and [JavaScript component interface](https://reactpy.dev/docs/guides/escape-hatches/javascript-components.html).
The installed release's client bundle uses Preact with React compatibility.
It sends layout models over a persistent connection; its work is not a Python
HTML serialization measurement.

The app sets `REACTPY_DEBUG_MODE`, `REACTPY_ASYNC_RENDERING`,
`REACTPY_CHECK_VDOM_SPEC` and `REACTPY_CHECK_JSON_ATTRS` to `false` before importing
ReactPy. These match the pinned release's production defaults, including its
synchronous renderer. The runner supplies `CITRY_BENCH_RUNTIME_DIR`; each process
creates a temporary module directory inside it, outside the immutable build.
Direct local launches use the system temporary directory. An inherited
`REACTPY_WEB_MODULES_DIR` does not select the output directory.

## Application behavior

The Python page composes the canonical shell, five mounted tab bodies, phase
and output expansion panels, notes, comments, roles, bookmarks, output forms,
dependencies and attachments from ReactPy components. ReactPy's native form
serialization sends controls in DOM order. Each form handler closes over its
action and optional output ID, while the submitted operation remains the first
hidden control. Inputs have no server change handler, so typing
does not send extra messages before submission. The server rejects malformed
actions rather than emitting a successful readiness marker.

A small local JavaScript component implements the client-only disclosure and
draft input through ReactPy's supported `bind` interface. It owns only that
sibling subtree. A local delegated listener switches the ReactPy-rendered tab
panels without a server event; native `details` elements own panel expansion.
All page rendering, state changes and server event delivery
use ReactPy's unchanged implementation. Its module and the package's client
assets are served locally; navigation needs no CDN.

## Readiness and connection evidence

The board includes a normal ReactPy script component whose key changes with
the revision. In the pinned client, `ScriptElement` evaluates it through its
post-commit effect. The script supplies the server's session, operation and
revision to the observer. The observer waits for local disclosure initialization,
checks the committed board attributes and requires no pending form submissions.
A microtask defers the marker beyond the script component's current effect stack.
Behavioral assertions verify the resulting UI; script execution alone is not
accepted as proof of correctness.

This endpoint includes ReactPy's script-effect scheduling and local-module
initialization. It may be later than the earliest moment a control could work.
Instrumentation can affect timings; semantic snapshot cost is reported separately,
while residual event-loop effects are not calibrated. This app is not yet
qualified for a public performance comparison. It does not estimate readiness
from a WebSocket receipt or animation frame.

The launch command disables WebSocket per-message compression. The runner must
also verify the handshake negotiates no extensions. The ASGI host accepts only
localhost or loopback hosts with a matching browser Origin. Missing, foreign
or scheme-mismatched origins are rejected before ReactPy accepts the socket;
non-browser clients must supply the same origin explicitly. No authentication
or database is included in this isolated synthetic-data scenario.

A passive ASGI observer
retains each original message string and monotonic timestamp. It does not
rewrite messages, add protocol fields, or calculate hashes during delivery.
After browser capture, the runner retrieves
`/__bench/operations?session=TOKEN` through its own HTTP client.

The audit returns `records` containing connection ID, direction (`received` or
`sent`, from the server's perspective), per-direction index, original text,
UTF-8 byte count, SHA-256, operation and revision. With compression disabled,
`encoded_identity_bytes` equals `decoded_utf8_bytes`; these are message-body
bytes, excluding WebSocket framing, masking, TCP and TLS overhead. The browser
capture must independently match their order, contents and counts.

For a correlated update, `server_ms` spans ASGI receive completion to the
corresponding ASGI send preparation. It includes event dispatch, application
work, ReactPy layout work and JSON encoding, but excludes socket transmission.
Initial `server_ms` starts when the backend accepts that connection. Hashing,
JSON audit decoding and byte accounting happen at audit collection. Retaining
message strings changes their lifetime, and the small recording overhead still
belongs to the observed run. HTTP `Server-Timing` measures ASGI entry through
response-start preparation, including request handling but excluding body
transmission.

Each correlated layout update also records `prepare_ms`. This narrower duration
starts after ReactPy's render queue produces work, covers active layout-model
construction and its existing JSON serialization, and ends before awaiting the
socket send. It includes the board snapshot and component traversal performed
inside layout construction. The passive audit correlates the retained serializer
string with the original outgoing frame after readiness; it does not hash or
encode the payload in the measured path.

The pinned client has automatic reconnection behavior. This app qualifies
only one uninterrupted connection; disconnects, reconnects, extra messages,
missing correlation and failed actions must be recorded as failed trials.
Concurrent submissions and independent updates are not qualified. The shared
scenario's limits on deeper preservation and asynchronous assets also apply.

## Run locally

Run `uv sync --frozen --python 3.12`, then use the command in `adapter.toml`.
Open `/?count=14&session=manual`; 140 outputs exercise the linear 10x cohort,
and the optional 1400-output case exercises the 100x cohort.
The app uses the shared scenario from the repository, or `scenario/` when the
runner copies it into an isolated snapshot. `/health` returns the runner's
process nonce without rendering. All HTTP responses use `Cache-Control: no-store`.

Run the passive transport checks with:

```sh
.venv/bin/python -m unittest test_audit test_configuration
```
