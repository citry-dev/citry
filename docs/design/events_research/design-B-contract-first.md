# Component.Events, proposal B: contract first

Status: design proposal (one of several competing drafts).
Date: 2026-07-04.
Charter: `docs/design/extensions_roadmap.md:62` (one extension, one design
exploration; HTTP vs WebSocket weighed together; `Component.View`, the `url`
extension, and the Vue-plugin prototype feed it and are not built separately).

The lens of this proposal: citry is multi-language by design (Python live,
JS/PHP/Go planned), so the durable artifacts are the **wire protocol** and the
**transport/format plugin interfaces**. The Python `Component.Events` API is
one binding of those contracts, not the contract itself. Everything a browser
or a non-Python server binding must understand is specified without reference
to Python.

---

## 1. Prior art

What was searched and verified for this proposal. Citations are `file:line`
in this repo unless marked external. Claims marked (v) were re-verified
against source during this design pass; the rest come from the seven recon
reports commissioned for this design (extension substrate, JS runtime, old
django-components snapshot, django-unicorn, Tetra, livecomponents, ecosystem
survey, citry history).

In-repo substrate, verified:

- `URLRoute` / `RouteResponse` / `match_route`: sync handler
  `(request, **path_params) -> RouteResponse`; response is content,
  content_type, status and nothing else; `{param}` path segments; first
  match wins (`packages/py/citry/citry/util/routing.py:36-141`). (v)
- The ASGI adapter never passes the `receive` channel, so a request body is
  unreachable through it today (`packages/py/citry/citry/contrib/asgi.py:94`),
  and non-http scopes raise (`contrib/asgi.py:72-74`). (v)
- User-extension routes are auto-namespaced under `ext/<name>/`
  (`packages/py/citry/citry/extension.py:660-685`); `emit()` supports
  duck-typed custom hooks with none/first/map result policies
  (`extension.py:719-773`). (v)
- `class_id` is `ClassName_<6-hex>` derived from the import path, stable
  across processes, reverse lookup via `Citry.get_component_by_class_id`
  (`packages/py/citry/citry/component.py:97-114`, `citry.py:333-345`). (v)
- Typed inputs: `cls.Kwargs(**raw_kwargs)` raises `TypeError` on
  unknown/missing keys; no coercion beyond dataclass construction
  (`component.py:463-475`). (v)
- URL building is mounted-prefix concatenation with a pointed error when
  unmounted (`citry.py:302-331`). (v)
- The client runtime's whole public surface is `Citry.manager` (register,
  data, call, load, mark); `$onComponent` callbacks receive exactly
  `{id, els, data}`; manifests are inert base64-armored JSON script tags with
  `markLoaded` / `fetch` / `calls`, ingested by a MutationObserver
  (`packages/py/citry/citry/extensions/dependencies/client/citry.js:34-238`). (v)
- The roadmap row that is this design's charter
  (`docs/design/extensions_roadmap.md:62`). (v)

From the recon reports (spot-checked where load-bearing):

- The fixed design slot: a future extension declares per-component routes
  through `Extension.urls`, handler shaped as render + fragment serialize
  (`docs/design/dependencies.md:641-663`); the mount contract and the
  multi-worker shared-cache constraint (`dependencies.md:594-616, 521-532`).
- The redesign rationale: DJC's `Component.View` named handlers after HTTP
  verbs and broke when one component backed several mutations
  (`docs/design/migration_djc.md:150, 1099-1100`).
- Old-DJC archaeology: `get_component_url` semantics, auto-public detection,
  the `$emit`/`$on` sketch in `sampleproject/components/todo/todo.py`, and
  the confirmed absence of any django-ninja PoC.
- External: django-unicorn (action queue, checksum, CVE-2021-42053 and
  CVE-2025-24370), Tetra (versioned envelope, `@public` promise wrappers,
  Fernet-pickled state), livecomponents (execution-result algebra, OOB
  fragment responses, pickle+Redis sessions), and the ecosystem survey
  (Livewire, LiveView, Turbo, htmx, Datastar, StimulusReflex, Inertia,
  django-ninja).

Nothing events-shaped exists in the Python package today (grep confirmed by
recon); the name `events` / nested class `Events` is free on `Component`.

---

## 2. Design overview

Three artifacts, in order of durability:

1. **The wire protocol** ("citry-events/1"): JSON message shapes for calling
   an event handler and for the server's response, plus the rules for
   versioning, batching, errors, and how HTML fragments and JSON data coexist
   in one response. Language-neutral; specified as JSON Schema plus golden
   fixtures under `packages/protocol/events/v1/`.
2. **The plugin interfaces**: a transport interface (HTTP, WebSocket,
   postMessage, anything that can move an envelope and bring one back) and a
   format interface (payload codecs for the uplink, result encoders for the
   downlink). Both exist on the server (Python now, other bindings later) and
   on the client (one small runtime, `citry-events.js`).
3. **The Python binding**: the `Component.Events` nested class, an `@event`
   decorator for per-handler config, a context object as the escape hatch, a
   small return-value algebra, signature-derived validation and OpenAPI.

The core model in one paragraph: a citry component is a pure function of its
inputs (kwargs), so the server does not need to keep live component objects
between requests. At render time the Events extension signs the component's
JSON-safe kwargs into an opaque **state token** delivered with the HTML. An
event call sends `{component, instance, event, args, state}` up; the server
verifies the token, validates the args against the handler's signature, runs
the handler, and answers with an ordered list of **self-addressed operations**
(render this fragment here, resolve the caller's promise with this JSON,
dispatch this browser event, redirect). Re-rendering is just calling the
component again with (possibly updated) kwargs and serializing with the
existing fragment strategy; the existing manifest machinery loads any assets
the fragment needs. HTTP is the v1 transport; WebSocket and others implement
the same dispatch interface later, and server push reuses the same operation
vocabulary over whatever channel exists.

What this deliberately is not: it is not a reactive-attributes framework
(unicorn/Tetra/Livewire style "public attributes mirror to the browser").
Citry components already have a declared input contract (`Kwargs`); Events
round-trips that contract and nothing else. The CVE record of the
attribute-mirroring family (unicorn CVE-2025-24370 class pollution, Livewire
unmarshaling RCEs, Tetra's pickled tokens) is the argument: every one of those
vulnerabilities lived in "the client sends rich state and the server
rehydrates it". Signed, schema-checked, JSON-only inputs remove that surface
by construction.

---

## 3. The wire protocol: citry-events/1

### 3.1 Terms

- **Envelope**: one JSON document sent over a transport, either a *call
  envelope* (client to server) or a *result envelope* (server to client).
- **Call**: one event invocation inside a call envelope.
- **Operation (op)**: one instruction inside a result, applied by the client
  in order (insert HTML, deliver data, dispatch event, navigate).
- **State token**: an opaque string minted by the server at render time that
  lets the server re-render the component later. The client never inspects
  it; it only stores and echoes it. Its internal format is a host-binding
  detail (section 8.1), not part of the protocol.
- **Instance id**: the component render id (`c` + 6 base62 chars) already
  stamped in the DOM as the `data-cid-<id>` marker.
- **Class id**: the stable component class identifier (`Table_a1b2c3`)
  already used by cache URLs and reverse lookup.

### 3.2 Call envelope (uplink)

```json
{
  "protocol": "citry-events/1",
  "id": "r_8f2k1c",
  "caps": { "swaps": ["replace", "morph"], "ops": ["render", "data", "event", "redirect", "url"] },
  "calls": [
    {
      "component": "TodoList_a1b2c3",
      "instance": "c1A2b3c",
      "event": "add_item",
      "args": { "text": "Buy milk" },
      "state": "cev1.eyJjIjoiVG9kb0xpc3RfYTFiMmMzIi4uLn0.9mYt..."
    }
  ]
}
```

Field rules:

| Field | Type | Required | Notes |
|---|---|---|---|
| `protocol` | string | yes | Exactly `citry-events/<major>`. Unknown major is rejected with `protocol_mismatch`. |
| `id` | string | yes | Client-minted correlation id, echoed in the result envelope. Needed for WebSocket multiplexing; harmless over HTTP. |
| `caps` | object | no | What the client runtime can apply. Absent means the v1 baseline (`swaps: ["replace"]`, all v1 ops). The server must not emit an op or swap outside the advertised set; it downgrades instead (e.g. `morph` to `replace`). |
| `calls` | array | yes | One or more calls, processed in order. v1 clients send one; the array exists so batching is a client-runtime feature, not a protocol change (lesson from Livewire's request bundling). |
| `calls[].component` | string | yes | Class id. |
| `calls[].instance` | string | no | Render id of the calling instance, when known. Used to self-address the default re-render. |
| `calls[].event` | string | yes | Handler name; `[a-z_][a-z0-9_]*`. |
| `calls[].args` | object | no | JSON object only (never an array or scalar). Validated server-side against the handler signature. Default `{}`. |
| `calls[].state` | string or null | no | The state token from render, echoed verbatim. Null/absent when the handler does not need re-render context. |

Explicitly not in the envelope: CSRF tokens, cookies, auth headers. Those are
transport-level concerns (section 4); the envelope must stay meaningful over
transports that have no headers (postMessage, WebSocket frames).

Also explicitly not in the envelope: executable expressions. Args are data.
django-unicorn ships `"set('Bob', count=2)"` strings and parses them
server-side with `ast.parse`; that bought it a parsing subsystem over
attacker-controlled strings and a fuzzy security story. Structured args plus
server-side coercion (section 6.2) keep the same ergonomics without the
surface.

### 3.3 Result envelope (downlink)

```json
{
  "protocol": "citry-events/1",
  "id": "r_8f2k1c",
  "results": [
    {
      "ok": true,
      "ops": [
        {
          "op": "render",
          "target": "cid:c1A2b3c",
          "swap": "replace",
          "html": "<div data-cid-c9Xy12z ...>...</div><script type=\"application/json\" data-citry>...</script><script type=\"application/json\" data-citry-events>...</script>"
        },
        { "op": "data", "value": { "count": 4 } },
        { "op": "event", "name": "todo:added", "detail": { "id": 17 }, "target": "cid:c1A2b3c" }
      ]
    }
  ]
}
```

`results[i]` answers `calls[i]`. Each result is either
`{ "ok": true, "ops": [...] }` or
`{ "ok": false, "error": {...} }` (error shape in 3.6). Ops across all
results apply in envelope order.

### 3.4 The operation vocabulary

This is the converged industry shape (Turbo Streams, htmx out-of-band swaps,
and Datastar all independently landed on "a list of self-addressed
target + action + fragment operations"), adapted to citry's existing
identifiers.

| Op | Fields | Meaning |
|---|---|---|
| `render` | `target`, `swap`, `html`, and optionally `title` | Insert or update HTML. `html` is a complete citry fragment (serialized with `deps_strategy="fragment"`): markup with `data-cid-*` markers, the pre-loader, the `data-citry` asset manifest, and the `data-citry-events` manifest (3.7). The existing MutationObserver machinery loads assets and runs component JS after insertion with zero new work. |
| `data` | `value` | Resolve the calling instance's send promise with this JSON value. At most one per result; a result with no `data` op resolves the promise with `null`. |
| `event` | `name`, `detail`, `target` | Dispatch a DOM `CustomEvent` named `name` with `detail`, bubbling, on the target instance's root elements, or on `document` when `target` is `"document"`. The server-to-client side channel for non-DOM effects (focus, toast, chart update); same role as htmx's `HX-Trigger` and LiveView's `push_event`. |
| `redirect` | `url` | Navigate the page (`location.assign`). |
| `url` | `url`, `mode` (`"push"` or `"replace"`) | History update without navigation. |

Target addressing:

- `"cid:<instance id>"`: all elements carrying the `data-cid-<id>` marker.
  This is the primary form; instance markers already exist in every
  serialized page.
- `"css:<selector>"`: any CSS selector, for updating things that are not
  citry instances (a counter badge, a flash area). Selectors become a public
  contract of the page, same tradeoff Turbo accepts; use `cid:` when
  possible.

Swap vocabulary (for `render`): `replace` (remove the old target elements,
insert the fragment's elements at the first old element's position),
`morph` (structure-preserving merge; v1.1, see 7.3), `inner`, `append`,
`prepend`, `remove` (no `html` needed), `none` (insert nothing; used to ship
only manifests/assets). Servers must honor `caps.swaps` and downgrade
`morph` to `replace` for clients that do not advertise it.

A `render` op whose `target` is the calling instance and whose fragment
carries a *new* instance id retires the old id: the client swaps the
elements, reads the new id and state token from the fragment's events
manifest, and future sends from that component use the new identity. This is
the normal case; citry mints a fresh render id per render by design.

### 3.5 Versioning and capabilities

- `protocol: "citry-events/<major>"`. One major = one compatible message
  family. The server rejects unknown majors (`protocol_mismatch`, HTTP 400).
- Within a major, evolution is additive only: new optional envelope fields,
  new op types, new swap strategies. Anything additive that the client must
  *act on* is gated by `caps`; the server never sends an op or swap the
  client did not advertise (absent `caps` means the v1 baseline). Unknown
  *fields* on known structures are ignored by both sides.
- The client runtime and the server extension ship in the same package, so
  version skew is rare (a cached runtime after a deploy). The `caps`
  mechanism makes stale-client behavior graceful rather than broken; a
  client that receives an op it cannot apply (should never happen, but
  defense in depth) logs, fires `citry:events:protocol-error` on `document`,
  and rejects the pending promise.
- Tetra's `protocol: "tetra-1.0"` envelope tag is the direct precedent; the
  addition here is the explicit capability negotiation, which is what lets
  v1 ship `replace` and add `morph` later without a major bump.

### 3.6 Errors

Transport-level failures (malformed JSON, unknown protocol major, payload
too large, CSRF rejection) fail the whole envelope; over HTTP they map to
4xx status codes with a body of
`{"protocol": "citry-events/1", "error": {...}}`.

Per-call failures ride inside `results[i]`:

```json
{
  "ok": false,
  "error": {
    "status": 422,
    "code": "invalid_args",
    "message": "add_item: invalid arguments",
    "fields": { "text": ["required"] }
  }
}
```

| `code` | `status` | Meaning |
|---|---|---|
| `protocol_mismatch` | 400 | Unknown protocol major (envelope-level). |
| `invalid_envelope` | 400 | Envelope fails schema validation (envelope-level). |
| `payload_too_large` | 413 | Envelope or args over the configured cap (envelope-level). |
| `csrf_failed` | 403 | Transport-level CSRF check failed (HTTP only, envelope-level). |
| `unknown_component` | 404 | No registered component class with that class id. |
| `unknown_event` | 404 | Component has no handler by that name. |
| `forbidden` | 403 | A guard rejected the call (section 6.5). |
| `invalid_args` | 422 | Args failed validation/coercion; `fields` maps arg name to messages. |
| `invalid_state` | 403 | State token signature/format check failed. |
| `stale_state` | 410 | State token expired or minted for another protocol/component version. Client fires `citry:events:stale`; the documented recovery is re-rendering or reloading the region (the 410 idea proven by Tetra and livecomponents). |
| `handler_error` | 500 | Uncaught exception in the handler. Message is generic in production; includes the exception text only when the engine runs in debug mode. Never a traceback on the wire. |

HTTP status mapping: the batch endpoint always answers 200 when the envelope
itself was processable, with per-call statuses inside (JSON-RPC style,
because one batch can mix outcomes). The per-event endpoint (4.2), which
carries exactly one call, mirrors the call's `error.status` as the HTTP
status so host middleware, logs, and rate limiters see real failure codes.

### 3.7 The events manifest (how state tokens and metadata reach the client)

The dependencies extension already delivers per-fragment instructions as an
inert JSON script tag (`data-citry`) because JSON survives any insertion
method, including `innerHTML`. Events uses the same mechanism with its own
tag, rather than growing the dependencies manifest (separate owners, separate
formats):

```html
<script type="application/json" data-citry-events>
  { "instances": [["<b64 instance id>", "<b64 class id>", "<b64 state token>"]],
    "classes":   { "<b64 class id>": "<b64 class descriptor JSON>" } }
</script>
```

All strings base64-armored, exactly like the dependencies manifest. Emitted
during serialize for every page or fragment that contains at least one
instance of an Events-declaring component. `instances` seeds the client
registry (instance id, class, token). `classes` carries the class
descriptor: the event names, their client hints (debounce/throttle defaults,
declared HTTP method), and arg names, generated once per class:

```json
{ "events": { "add_item": { "args": ["text"] },
              "search":   { "args": ["query"], "debounce": 300, "method": "GET" } } }
```

The class descriptor is a client convenience (validation messages, future
declarative bindings, TS codegen input); the server remains the authority.

### 3.8 Batching semantics

`calls` are dispatched sequentially in order, each with its own validation
and guard run; `results` is a parallel array. One transport round trip may
therefore carry several event calls (the client runtime may coalesce sends
issued in the same tick, a Livewire-proven optimization). The protocol fixes
the semantics now; v1 client sends single-call envelopes, and coalescing is
a v2 client feature requiring zero protocol change. There is no cross-call
transaction: call 2 runs even if call 1 failed. A future `atomic: true`
envelope flag is reserved but not specified.

### 3.9 Where the schemas live

`packages/protocol/events/v1/`:

```
spec.md                  # prose spec (this section, normatively worded)
call.schema.json         # JSON Schema 2020-12 for the call envelope
result.schema.json       # for the result envelope
descriptor.schema.json   # for the class descriptor
fixtures/
  call_single.json           result_render_replace.json
  call_batch.json            result_data_only.json
  call_no_state.json         result_mixed_ops.json
  error_invalid_args.json    error_stale_state.json
  ...
```

The fixtures are golden request/response pairs against a small canonical
fixture component defined in the spec (a counter with `increment`, `rename`,
and `crash` events). Every server binding (Python now, JS/PHP/Go later) must
pass the same fixture suite; the client runtime's tests replay the same
result fixtures into a DOM harness. This mirrors the repo's "observe, then
lock" rule for compiler output: the protocol is locked by fixtures, not by
whichever binding shipped first. Excerpt of `call.schema.json` to fix the
level of rigor:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://citry.dev/protocol/events/v1/call.schema.json",
  "type": "object",
  "required": ["protocol", "id", "calls"],
  "properties": {
    "protocol": { "const": "citry-events/1" },
    "id": { "type": "string", "minLength": 1, "maxLength": 64 },
    "caps": {
      "type": "object",
      "properties": {
        "swaps": { "type": "array", "items": { "type": "string" } },
        "ops": { "type": "array", "items": { "type": "string" } }
      },
      "additionalProperties": true
    },
    "calls": {
      "type": "array", "minItems": 1, "maxItems": 16,
      "items": {
        "type": "object",
        "required": ["component", "event"],
        "properties": {
          "component": { "type": "string", "pattern": "^[A-Za-z_][A-Za-z0-9_]*$" },
          "instance": { "type": ["string", "null"] },
          "event": { "type": "string", "pattern": "^[a-z_][a-z0-9_]*$" },
          "args": { "type": "object" },
          "state": { "type": ["string", "null"], "maxLength": 16384 }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

---

## 4. Transports

### 4.1 The transport contract

A transport's whole job is: move a call envelope to the server, hand it to
the dispatcher, move the result envelope back. The dispatcher is
transport-agnostic and is the single implementation of protocol semantics
per server binding.

Server side (Python signature; other bindings mirror it):

```python
@dataclass(frozen=True, slots=True)
class TransportContext:
    """Everything a transport knows about the incoming call, host object included."""

    transport: str                      # "http", "ws", "graphql", ...
    citry: Citry
    host_request: Any = None            # the escape hatch: Django HttpRequest,
                                        # ASGI scope, WS connection, or None
    headers: Mapping[str, str] = ...    # case-insensitive view; empty when N/A


class EventsDispatcher:
    def dispatch(self, envelope: dict, ctx: TransportContext) -> dict:
        """Validate the envelope, run each call, return the result envelope."""

    async def dispatch_async(self, envelope: dict, ctx: TransportContext) -> dict:
        """Same, awaiting async handlers; sync handlers run in a worker thread."""
```

The dispatcher owns: envelope schema validation, protocol version check,
component/event resolution, state-token verification, guard evaluation, arg
validation and coercion, handler invocation, return-value encoding into ops,
error mapping, and the `caps` downgrade. Transports own: bytes on the wire,
framing, content-type negotiation (via payload codecs, 4.6), CSRF, and
mapping envelope-level errors to their native error signaling.

Client side, the mirror interface (TypeScript notation; shipped as plain JS):

```ts
interface EventsTransport {
  /** Send one call envelope; resolve with the result envelope. */
  send(envelope: CallEnvelope, opts: SendOpts): Promise<ResultEnvelope>;
  /** Optional: long-lived transports expose a push feed (section 9). */
  subscribe?(channel: string, onOps: (ops: Op[]) => void): () => void;
}

Citry.events.registerTransport(name: string, transport: EventsTransport);
Citry.events.configure({ transport: "http", ...transportOptions });
```

The runtime picks the configured default transport; a single send may
override it (`c.send("save", args, { transport: "ws" })`). Registering a
transport is the entire client plugin story; the runtime never special-cases
transport names.

### 4.2 HTTP transport (v1, ships first)

Server routes, declared via `Extension.urls` and therefore automatically
namespaced under `<prefix>/ext/events/` (verified: `extension.py:660-685`):

| Route | Methods | Purpose |
|---|---|---|
| `ext/events/call` | POST | The batch endpoint. Body = call envelope (JSON codec). Always answers 200 with a result envelope when the envelope is processable. |
| `ext/events/c/{class_id}/{event}` | per-handler (default POST) | The per-event endpoint. One fixed parametrized route (never one route per component, so Django's snapshot-at-`urlpatterns()`-time routing works; recon confirmed dynamic per-component routes 404 under Django). Component and event come from the path; the body may be a bare call object, a full envelope with one call, or a non-JSON payload handled by a codec (4.6). HTTP status mirrors the call outcome. This is the URL that host middleware, rate limiters, OpenAPI, and plain `<form>` posts see. |
| `ext/events/runtime.js` | GET | The events client runtime. |

Request headers used by the HTTP transport (transport-level, not envelope):

- `Content-Type`: selects the payload codec (4.6).
- `X-Citry-Events: 1`: marks runtime-originated requests (distinguishes them
  from plain form posts in the progressive-enhancement path).
- CSRF header per host convention (section 8.3).
- `Accept`: `application/json` (default, result envelope) or `text/html`
  (compatibility mode, below).

Response headers: `Content-Type: application/json` plus any headers a
handler attached through the escape hatch (`RouteResponse.headers`, a v0
substrate addition, section 12).

**Compatibility / no-JS mode.** When the per-event endpoint receives a
request with `Accept: text/html` (or a classic form post without
`X-Citry-Events`), the response is not an envelope: the primary `render`
op's HTML is returned as the body (`text/html`), a `redirect` op becomes an
HTTP 303, and errors become their HTTP status with an HTML-safe message.
Consequences, both intentional: a plain `<form method="post" action="{{ url }}">`
against an event handler works with JavaScript disabled, and htmx/Turbo
users can point `hx-post` at an event URL and get a fragment back without
adopting the citry client at all. This satisfies the roadmap's "no htmx
component pack" rule while staying interoperable with htmx.

Handler-side plumbing (all inside the extension, host-neutral):

```python
class EventsExtension(Extension):
    name = "events"

    @property
    def urls(self) -> list[URLRoute]:
        return [
            URLRoute("call", handler=self._handle_batch, methods=("POST",),
                     name="citry_events_call"),
            URLRoute("c/{class_id}/{event}", handler=self._handle_single,
                     methods=("GET", "POST"), name="citry_events_event"),
            URLRoute("runtime.js", handler=self._serve_runtime, methods=("GET",),
                     name="citry_events_runtime"),
        ]

    def _handle_batch(self, request: RouteRequest) -> RouteResponse:
        envelope = self._codec_for(request.content_type).decode(request)
        ctx = TransportContext(transport="http", citry=self.citry,
                               host_request=request.host, headers=request.headers)
        result = self.dispatcher.dispatch(envelope, ctx)
        return RouteResponse(json.dumps(result), content_type="application/json")
```

This depends on the v0 substrate work (section 12): `RouteRequest` with a
body, `RouteResponse.headers`, and the ASGI adapter draining `receive`.
Today's adapter literally cannot deliver a POST body (`contrib/asgi.py:94`),
so that change is a hard prerequisite, not an optimization.

**URL building.** `get_event_url(TodoList, "add_item", query={...})` formats
`ext/events/c/{class_id}/{event}` through `Citry.build_url` (mounted-prefix
contract, `citry.py:316-331`) and the already-ported `format_url` helper,
which the migration doc explicitly earmarked for "a future component-URL
builder" (`migration_djc.md:859`). Raises the standard pointed error when
nothing is mounted. Also exposed as `component.events.url("add_item")` for
template use.

### 4.3 WebSocket transport (v2)

One socket per page, multiplexed, never per component (the unanimous
industry answer; LiveView, ActionCable). ASGI-only; WSGI hosts simply do not
get this transport, and nothing else in the design degrades.

Frames are the same envelopes with a `type` discriminator added at the frame
level (the envelope schemas are unchanged; the frame wraps them):

```json
// client -> server
{ "type": "call", "envelope": { "protocol": "citry-events/1", "id": "r_1", "calls": [...] } }
{ "type": "ping" }

// server -> client
{ "type": "result", "envelope": { "protocol": "citry-events/1", "id": "r_1", "results": [...] } }
{ "type": "push", "channel": "todo:board:42", "ops": [ ... ] }     // section 9
{ "type": "pong" }
```

Correlation is the envelope `id` the client already mints. Server side, the
transport is a small ASGI app accepting `websocket` scopes at
`ext/events/ws`, authenticating once at connect (host session/cookie), then
looping: decode frame, `await dispatcher.dispatch_async(envelope, ctx)`,
send result frame. The dispatcher is byte-for-byte the one HTTP uses; the
conformance fixtures run against both.

Substrate this needs (spec'd now, built in v2): a `WSRoute` sibling of
`URLRoute` (path + async connection handler) and an `asgi_ws_app` adapter;
`contrib/asgi.py` currently raises on non-http scopes by design. Reconnect
policy: a reconnect is a new connection, not a resume; in-flight promises
reject with a transport error and components keep working because all
per-call context rides in the envelope (stateless dispatch is what makes the
WS transport additive rather than a second architecture). This is the
LiveView lesson inverted: because citry does not hold per-connection server
state, reconnection has nothing to lose.

### 4.4 postMessage transport (the exotic one, proving the interface)

Concrete consumer: embedded previews. The Storybook extension
(roadmap section 3) and the docs site's live examples render components
inside sandboxed iframes that have no same-origin network path, no cookies,
and no CSRF token. The iframe's runtime cannot fetch; it can `postMessage`.

Client transport, complete implementation against the interface:

```js
// Inside the sandboxed preview iframe.
Citry.events.registerTransport("postmessage", (function () {
  var pending = new Map(); // envelope id -> {resolve, reject}

  window.addEventListener("message", function (msg) {
    var data = msg.data;
    if (!data || data.citryEvents !== 1 || data.type !== "result") return;
    var entry = pending.get(data.envelope.id);
    if (!entry) return;
    pending.delete(data.envelope.id);
    entry.resolve(data.envelope);
  });

  return {
    send: function (envelope) {
      return new Promise(function (resolve, reject) {
        pending.set(envelope.id, { resolve: resolve, reject: reject });
        window.parent.postMessage(
          { citryEvents: 1, type: "call", envelope: envelope },
          "*" // the embedding host validates origin on ITS side; results
              // return only to the source window
        );
        setTimeout(function () {
          if (pending.delete(envelope.id)) reject(new Error("citry events: postMessage timeout"));
        }, 15000);
      });
    },
  };
})());
Citry.events.configure({ transport: "postmessage" });
```

Bridge on the embedding page (Storybook manager, docs shell), forwarding to
its own HTTP transport, which has cookies and CSRF:

```js
window.addEventListener("message", async function (msg) {
  if (msg.origin !== PREVIEW_ORIGIN) return;                 // strict allowlist
  var data = msg.data;
  if (!data || data.citryEvents !== 1 || data.type !== "call") return;
  var result = await fetch("/citry/ext/events/call", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Citry-Events": "1",
               "X-CSRFToken": readCsrf() },
    body: JSON.stringify(data.envelope),
  }).then(function (r) { return r.json(); });
  msg.source.postMessage({ citryEvents: 1, type: "result", envelope: result },
                         msg.origin);
});
```

No server-side work at all: the bridge reuses the HTTP transport, and the
envelope crossed two transports unchanged. That is the proof the abstraction
is real. The bridge is also where a preview host can enforce its own policy
(read-only mode: reject anything but allowlisted events) by inspecting the
envelope, which is possible precisely because the protocol is transparent
JSON rather than host-specific request objects.

**GraphQL, as a sketch** (not planned, included to show the seam): a host
that standardizes on GraphQL exposes one mutation and calls the same
dispatcher; roughly ten lines with any Python GraphQL library:

```python
def resolve_citry_event(root, info, envelope: dict) -> dict:
    ctx = TransportContext(transport="graphql", citry=citry_instance,
                           host_request=info.context["request"])
    return dispatcher.dispatch(envelope, ctx)
```

Typed per-event GraphQL fields could be generated from the same schema
models that feed OpenAPI (section 10), but that is an ecosystem add-on, not
core.

### 4.5 What is shared between transports

Shared: the envelopes and op vocabulary, the dispatcher (validation, guards,
state, coercion, encoding, errors), the fixtures, the client-side instance
registry and swap engine, busy states, and the promise semantics of `send`.
Per-transport: framing, connection lifecycle, CSRF/auth attachment, and
error signaling native to the channel. The design rule: anything two
transports would both need belongs in the dispatcher or the runtime core,
never duplicated in a transport.

### 4.6 Format plugins

**Payload codecs (uplink).** A codec turns a raw transport payload into a
call envelope. Registered on the extension, keyed by content type:

```python
class PayloadCodec(Protocol):
    content_types: tuple[str, ...]

    def decode(self, request: RouteRequest, *, class_id: str | None = None,
               event: str | None = None) -> dict:
        """Return a call envelope. class_id/event are pre-bound on the per-event route."""
```

Built-in codecs:

- `application/json`: the identity codec (body is the envelope, or a bare
  call object on the per-event route).
- `application/x-www-form-urlencoded`: form fields become `args` (strings;
  the handler's signature coercion turns them into ints/bools/dates), the
  reserved fields `_citry_state` and `_citry_instance` map to `state` and
  `instance`. This codec is what makes plain `<form>` progressive
  enhancement work.
- `multipart/form-data` (v1.1): like urlencoded, plus file parts surface as
  `UploadedFile` values (name, content type, size, a read handle) bound to
  handler parameters annotated `UploadedFile`. The JSON part of a
  runtime-originated multipart request rides in a `_citry_envelope` field
  (Tetra's proven shape).
- Query-args on GET: for handlers declared `method="GET"` (read-only,
  cacheable events), query parameters become `args` via the urlencoded
  rules.

`EventsExtension(codecs=[MyCodec(), ...])` prepends user codecs; first
matching content type wins.

**Result encoders (downlink).** An encoder maps a handler's Python return
value onto ops. The built-in table covers the return algebra (section 6.3);
users register encoders for their own domain types:

```python
class ResultEncoder(Protocol):
    def encode(self, value: Any, ctx: EventContext) -> list[Op] | None:
        """Return ops for values this encoder owns, else None (next encoder runs)."""
```

Example: an encoder that turns any `pydantic.BaseModel` return into a `data`
op via `model_dump()`. Encoders make "pluggable response formats" a
first-class seam instead of an if-chain inside the dispatcher.

---

## 5. How a page actually behaves (end to end)

1. A page renders `TodoList(items=[...])`. Serialization stamps
   `data-cid-c1A2b3c` markers (existing), the dependencies manifest
   (existing), and the events manifest with
   `[instance id, class id, state token]` plus the class descriptor (new).
   The dependencies pipeline also emits a `<script src=".../ext/events/runtime.js">`
   tag (via the `on_dependencies` hook) whenever the page or fragment
   contains an Events-declaring component, deduped by URL like every other
   script.
2. The events runtime loads, registers `Citry.events`, processes events
   manifests (an observer for `data-citry-events`, same pattern as the
   dependencies observer), and installs a context decorator into the
   dependencies manager (one new core seam, section 7.1).
3. The component's own JS runs via `$onComponent`; its context now carries
   `send` and `on`.
4. `c.send("add_item", { text })` builds a call envelope from the registry
   (class id, instance id, token), stamps `data-citry-busy` on the instance's
   root elements, fires `citry:events:before` (bubbling CustomEvent), and
   hands the envelope to the configured transport.
5. The server dispatches: token verified, args validated and coerced,
   handler runs, `Render(items=[...])` re-renders the component with merged
   kwargs and serializes it as a fragment; the result envelope carries a
   `render` op targeting `cid:c1A2b3c` plus whatever else the handler
   returned.
6. The runtime applies ops in order: swap the fragment in (the dependencies
   observer picks up the fragment's manifests exactly as it does for any
   host-inserted fragment today; assets dedupe by URL), update the instance
   registry from the new events manifest, resolve the promise with the
   `data` op's value (or null), clear busy state, fire `citry:events:after`.

No new asset pipeline, no second insertion mechanism: the fragment path that
is already tested end to end under FastAPI is the delivery vehicle; Events
adds the missing client half (transport + swap) and the missing server half
(dispatch + state).

---

## 6. The Python API (one binding of the protocol)

### 6.1 Declaring handlers

```python
from citry import Component
from citry.extensions.events import event, EventContext, Render, BrowserEvent, Redirect


class TodoList(Component):
    class Kwargs:
        items: list[str]
        title: str = "Todo"

    class Events:
        def add_item(self, ctx: EventContext, text: str) -> Render:
            """Add one item and re-render. Exposed because it is defined here."""
            items = [*ctx.kwargs["items"], text.strip()]
            return Render(items=items)

        def clear(self, ctx: EventContext) -> list:
            return [Render(items=[]), BrowserEvent("todo:cleared")]

        @event(method="GET", csrf=False, debounce=300)
        def search(self, ctx: EventContext, query: str, limit: int = 10) -> list[str]:
            """Read-only lookup; returns JSON to the caller's promise."""
            return [i for i in ctx.kwargs["items"] if query.lower() in i.lower()][:limit]

        def _helper(self) -> None:
            """Underscore-prefixed: never exposed, plain method."""

    template = """
        <div class="todo">
          <h2>{{ title }}</h2>
          <ul>
            <c-for item in="items">
              <li>{{ item }}</li>
            </c-for>
          </ul>
          <input class="todo-input" placeholder="Add..." />
        </div>
    """

    js = """
        $onComponent(({ els, send, on }) => {
          const input = els[0].querySelector(".todo-input");
          input.addEventListener("keydown", async (e) => {
            if (e.key !== "Enter") return;
            await send("add_item", { text: input.value });
            input.value = "";
          });
          on("todo:cleared", () => input.focus());
        });
    """
```

Rules, all enforced at component-class creation (the extension captures the
user's raw nested class in `on_component_class_created`, the same trick the
dependencies extension uses, because the substrate later rebuilds the nested
class):

- **Exposure is the act of definition.** A method defined on the component's
  own `Events` class (or inherited from another *component's* Events class
  up the component hierarchy) whose name does not start with `_` is a
  handler. Methods inherited from the extension's `Config` base are never
  handlers. There is no `public` flag to forget and no denylist to maintain;
  this is the explicit-registration camp (LiveView, django-ninja), chosen
  against the implicit camp's security record (Livewire, unicorn).
- Handler signature: `(self, ctx, <typed args...>)`. `*args` and `**kwargs`
  are rejected at class creation with a pointed error, because the signature
  is the schema (section 6.2 and 10); an unschematizable handler is a bug,
  not a feature.
- `self` is the per-component Events config instance, constructed with
  `component=None` because no component instance exists during dispatch
  (the substrate explicitly supports out-of-lifecycle config instantiation).
  Class-level config attributes (6.5) are readable on `self`; `self.component`
  raises the standard helpful error. Everything about the call lives on `ctx`.
- Handlers may be `async def`. The ASGI path awaits them and runs sync
  handlers in a worker thread (so a blocking ORM call does not stall the
  event loop); WSGI and sync Django run sync handlers natively and reject
  async handlers with a clear error naming the deployment fix.

### 6.2 Typed args: validation and coercion

At class creation, each handler's signature is compiled into an argument
model. Incoming `args` are validated against it; failures produce
`invalid_args` with per-field messages, never a 500.

- Passthrough JSON types: `str`, `int`, `float`, `bool`, `None`,
  `list[...]`, `dict[str, ...]`, `Literal[...]`, unions of these,
  `Optional[...]`, with defaults honored.
- Coercions from strings and JSON scalars (the django-unicorn steal, minus
  its transport): `datetime`, `date`, `time`, `UUID`, `Decimal`, `Enum` (by
  value), and dataclasses (from objects, recursively). Type-hint driven,
  standard library only.
- When Pydantic is installed and a parameter is annotated with a
  `BaseModel`, validation delegates to it (aligning with the roadmap's
  optional Pydantic integration). Not required.
- Deliberately absent: "model by primary key" coercion (Livewire and unicorn
  both do it; it silently turns an argument into a database fetch that needs
  its own authorization). Fetch your own models inside the handler where the
  guard already ran.

The same argument models later feed OpenAPI (section 10). One source of
truth, django-ninja's proven shape.

### 6.3 The return algebra

A handler returns what should happen; the dispatcher encodes it into ops.
Small, closed set (the livecomponents execution-results steal, adapted):

| Return | Encodes to |
|---|---|
| `Render(**kwarg_overrides)` | Re-render the calling component: verified token kwargs merged with the overrides, `Cls(**kwargs).render().serialize(deps_strategy="fragment")`, a `render` op targeting the calling instance, and a fresh state token in the fragment's events manifest. `Render()` re-renders unchanged. |
| `Render(element, target="css:#sidebar", swap="inner")` | Render any `CitryElement` (another component included) to an explicit target. Cross-component updates in the same response, no second round trip. |
| any JSON-able value (dict, list, str, int, dataclass, ...) | A `data` op; resolves the client promise. |
| `BrowserEvent(name, detail=None, target="instance")` | An `event` op. |
| `Redirect(url)` / `Url(url, mode="push")` | `redirect` / `url` ops. |
| a `list`/`tuple` of the above | Ops in order. |
| `None` | Success with no ops (an acknowledgment). Explicit over implicit: re-rendering costs a render, so it is spelled `return Render()`. |
| `RouteResponse(...)` | HTTP-transport, per-event-route escape hatch only (file downloads, custom content types); bypasses the envelope entirely. Raises a clear error on the batch endpoint and non-HTTP transports. |

Errors: raise `EventError(status=..., code=..., message=..., fields=...)` for
deliberate failures; raise anything else and the dispatcher answers
`handler_error` (500) with the detail withheld outside debug mode. A
`ValidationError`-style helper `invalid(field="msg", ...)` covers the common
form case.

### 6.4 EventContext: the escape hatch and the call's world

```python
@dataclass(frozen=True, slots=True)
class EventContext:
    citry: Citry
    component_class: type[Component]
    event: str                          # handler name as called
    args: dict[str, Any]                # validated + coerced
    kwargs: dict[str, Any] | None       # resumed from the state token, or None
    instance_id: str | None             # calling instance render id, or None
    transport: str                      # "http", "ws", ...
    headers: Mapping[str, str]          # transport headers (empty when N/A)
    request: Any                        # the raw host object: Django HttpRequest,
                                        # ASGI scope + body, WS connection, or None
```

`ctx.request` is the requirement-mandated escape hatch: full host power when
needed (sessions, auth user, cookies), at the documented cost of writing
host-specific code. Everything else on the context is host-neutral, and
handlers that stay on the neutral surface run unchanged under every adapter.

### 6.5 Per-handler and per-component configuration

Per handler, via the decorator (plain methods get all defaults):

```python
@event(
    name="submit",              # wire name override (default: method name)
    method="POST",              # "POST" (default) or "GET" (read-only, csrf-exempt-able)
    csrf=True,                  # HTTP-transport CSRF enforcement (default True)
    guard=None,                 # callable(ctx) -> bool | raises; overrides class guard
    state="optional",           # "optional" (default) | "required" | "none"
    expires=None,               # timedelta; per-handler token max age
    debounce=None, throttle=None,   # client hints, delivered via the class descriptor
)
```

Per component, attributes on the `Events` class (participating in the
substrate's three-level defaults: component > `extensions_defaults["events"]`
> factory defaults, all for free):

```python
class Events:
    guard = staticmethod(require_authenticated)   # default guard for every handler
    csrf = True
    state_fields = None        # None = all kwargs round-trip; or a tuple naming which
    expires = None             # timedelta for token age, None = no expiry
```

Engine-wide, on the extension instance:

```python
Citry(extensions=[
    EventsExtension(
        secret=None,           # HMAC key; resolution order in section 8.1
        max_body=256 * 1024,   # envelope size cap
        max_state=16 * 1024,   # state token size cap
        codecs=[...], encoders=[...],
        guard=None,            # engine-wide default guard
    ),
])
```

### 6.6 Extension-owned hooks and commands

Following the substrate rule that extension lifecycle points are `emit()`
custom hooks (the `on_dependencies` precedent), Events fires:

- `on_event_call(ctx)` before guard/dispatch, `result="first"`: another
  extension may veto or answer (returning an error or ops short-circuits).
  This is the observability and policy seam (audit logging, rate limiting).
- `on_event_result(ctx)` after encoding, `result="map"` on the ops list:
  transform outgoing ops (e.g. a debug extension appending timing events).

CLI commands (`citry ext run events ...`): `openapi` and `manifest`
(section 10), and `routes` (print the resolved event URL table for an app).

---

## 7. The client JS API

### 7.1 The magic surface

The existing magic family stays exactly one member: `$onComponent`. Its
callback context grows two members, so the full object is
`{ id, els, data, send, on }`:

```js
$onComponent(({ id, els, data, send, on }) => {
  // send(event, args?, opts?) -> Promise<jsonValue>
  //   opts: { transport?, timeout?, signal? }
  //   resolves with the `data` op value (or null); rejects with
  //   EventCallError { status, code, message, fields } on a failed result.
  // on(name, fn) -> stop function
  //   listens for server-dispatched `event` ops targeted at this instance
  //   (and, later, push ops); multiple handlers per name; teardown by
  //   calling the returned function.
});
```

Why not `$sendEvent(...)` / `$onEvent(...)` as new source rewrites, which the
requirements floated: the `$onComponent` rewrite is a substring/regex
expansion done at JS cache time; it can bind the class id but can never bind
an instance id, because instances exist only at render time. A free-standing
`$sendEvent` would therefore either be ambiguous (which instance?) or need an
element argument, at which point it is not simpler than `send` on the
per-instance context, which is correct by construction. The rewrite approach
also has a known sharp edge (it matches inside strings and comments). So the
per-instance API rides the context, and the names stay short (`send`, `on`)
because they are already namespaced by the context object. This is a
deliberate improvement on the requested shape, not an omission; the
capability set is identical.

Programmatic API, for code outside component JS (host pages, other
libraries):

```js
Citry.events.send(classId, instanceId, event, args, opts) -> Promise
Citry.events.instance(instanceId) -> { send, on } | null    // from the registry
Citry.events.on(name, fn) -> stop        // document-level server events
Citry.events.configure({ transport, url, csrf, timeout })
Citry.events.registerTransport(name, transport)
Citry.events.applyOps(ops)               // the op interpreter, exposed for tests
```

**The one new core seam.** `citry.js` (the dependencies manager) gains a
context-decorator hook: `Citry.manager.decorateContext(fn)`; every decorator
runs over the callback payload object at flush time. The events runtime
registers one decorator that attaches `send`/`on` bound to the instance.
To make ordering airtight (fragment script execution order is not
guaranteed, a verified gap), Events injects a tiny inline bootstrap (a
15-line queueing stub defining `Citry.events` and registering the decorator)
via the `on_dependencies` hook; inline manifest scripts execute synchronously
during manifest processing, before any URL-loaded component script can run.
`send` before the full runtime arrives returns a promise that resolves once
it has; promises absorb the async arrival naturally.

### 7.2 Loading states, lifecycle events, optimistic UI

While a call is in flight, the runtime stamps the boolean attribute
`data-citry-busy` on the instance's root elements (CSS:
`[data-citry-busy] .spinner { display: block }`) and fires namespaced,
bubbling CustomEvents with `{ instanceId, classId, event }` detail:

```
citry:events:before      cancellable; preventDefault() aborts the send
citry:events:after       success, ops applied
citry:events:error       carries { status, code, message, fields }
citry:events:swapped     after each render op lands (per target)
citry:events:stale       stale_state received for this instance
```

Optimistic UI stance, matching the industry convergence: pending-state hooks,
not predicted state. No rollback machinery ships; a component that wants
optimism mutates its own DOM in its own JS before `await send(...)` and
reconciles when the render op lands. The busy attribute plus the event set is
the complete surface.

### 7.3 The swap engine

v1 ships `replace` (and `inner`/`append`/`prepend`/`remove`/`none`): remove
the target elements, insert the fragment's element(s) at the first target's
position. Honest cost: `replace` loses focus and scroll state inside the
swapped region, which is why every mature framework morphs. Morphing is
v1.1: vendor idiomorph (small, standalone, no framework coupling) behind the
`morph` swap and the `caps` negotiation, so v1 clients keep working
unchanged. The runtime never depends on Alpine, htmx, or any third-party
page library (the livecomponents five-library stack is the counterexample);
one owned runtime file, loaded once, deduped by URL.

### 7.4 Declarative template binding (v1.1, protocol-free)

JS-free wiring for the common cases, attribute grammar borrowed from
unicorn's (its best-liked surface), namespaced into citry's `c-` family:

```html
<button c-on:click="add_item" c-args='{"text": "Milk"}'>Add</button>
<input c-on:input.debounce-300="search" c-arg:query="value" />
```

Mechanics: these are plain HTML attributes that pass through the template
pipeline untouched; the events runtime installs one delegated listener per
DOM event name at the document root, resolves the owning instance by walking
up to the nearest `data-cid-*` marker, and issues the same `send`. Modifiers:
`.prevent`, `.stop`, `.debounce-N`, `.throttle-N`, `.once`. Server-declared
`debounce`/`throttle` hints from the class descriptor apply when the
attribute does not override them.

This is purely client-runtime sugar over the same protocol; no envelope
change, no parser change, no new server surface. Two open checks before
building, per the roadmap's decide-while-building rule: (a) confirm the V3
parser passes `c-on:click` through as a literal attribute (if the `c-`
prefix collides with tag/attribute grammar, fall back to `data-on:*`); (b)
decide whether compile-time validation of event names against the class
descriptor is worth a parse-time hook, which is exactly the kind of evidence
the roadmap wants before adding `on_tag_*` hooks. If (a) fails and (b) is
wanted, that becomes a grammar/AST change and triggers CLAUDE.md Mechanisms
2 and 4; the v1/v1.1 design does not depend on it.

---

## 8. State model and security

### 8.1 The state token

What round-trips: the component's declared inputs (kwargs), nothing else.
Minted at serialize time for every rendered instance of an Events-declaring
component, delivered in the events manifest, stored in the client registry,
echoed in calls.

Python binding format (host-opaque at the protocol level; the client treats
it as an opaque string, so other server bindings may differ, and no
cross-language canonical-JSON problem exists):

```
cev1 . base64url(payload_json) . base64url(hmac_sha256(secret, payload_json))
payload_json = {"v": 1, "c": "<class_id>", "k": {<kwargs>}, "t": <mint epoch>, "x": <expiry epoch | null>}
```

Rules:

- HMAC-SHA256, full length, constant-time comparison. Not truncated
  (unicorn truncates to 8 shortuuid chars as a size tradeoff; state here is
  per-instance, not per-keystroke, so the 32 bytes are cheap).
- Signed, not encrypted: kwargs values are visible to the page author's
  browser, which already received them rendered into HTML. Documented rule:
  kwargs must not carry secrets the page must not see; `state_fields`
  excludes fields from the token (an excluded field makes `Render()` fail
  loudly unless the handler supplies it, no silent wrong renders, the
  livecomponents lesson).
- Bound to the class id and protocol version; a token minted for one
  component or protocol major fails `invalid_state` on another.
- JSON-safe values only. A component that declares Events but has a
  non-JSON-safe kwarg fails **at render time** with an error naming the
  kwarg and the fixes (make it JSON-safe, list it in `state_fields`
  exclusions, or set `state="none"` on the handlers). Loud and early, never
  a silent broken re-render.
- Size-capped (`max_state`, default 16 KiB) at mint time, with the error
  naming the component; oversized state is a design smell the developer
  should see, not a slow page they discover.
- No rich-object revival, ever. Verified kwargs re-enter through the same
  door as any render: `Cls(**kwargs)`, where a declared `Kwargs` dataclass
  raises on unknown/missing keys (verified `component.py:463-475`). This is
  the structural answer to the Livewire-unmarshaling / Tetra-pickle / unicorn
  class-pollution family: there is no hydration machinery to attack.
- Expiry optional (`expires`), default none; expired tokens answer
  `stale_state` (410), and the client surfaces `citry:events:stale`.
- Secret resolution: `EventsExtension(secret=...)` wins; else
  `CitrySettings.secret` (new v0 setting); else host auto-detection (Django's
  `SECRET_KEY` via a documented `citry.contrib.django.secret()` helper used
  at construction); else the first mint raises a pointed error. Key rotation:
  `secret` accepts a list; first entry signs, all entries verify.

An optional server-side state store (livecomponents-style, pluggable
backend, instance-addressed) is a considered v2+ extension point for apps
whose inputs are too large or too sensitive to round-trip: the token then
carries only a random capability id. It is deliberately not in v1: it adds a
shared-storage dependency, TTL/eviction UX (410 storms), and multi-worker
coupling for a need the signed token covers in the common case. The protocol
does not change either way, which is the point of the token being opaque.

### 8.2 Method exposure

Restated as the security property: **the remotely callable surface of a
component is exactly the non-underscore methods its author wrote inside
`class Events`.** No other method of the component, its config, or its base
classes is reachable; no property is settable; there is no dotted-path
traversal of any object graph (the exact mechanism of unicorn's
CVE-2025-24370 does not exist here). Args bind only to declared parameters;
extra keys are `invalid_args`, not absorbed.

### 8.3 CSRF and auth

- **CSRF is transport-level.** The HTTP transport enforces it; WS
  authenticates at connect (plus origin check); postMessage delegates to the
  bridge's HTTP call. Default HTTP policy: reject state-changing calls
  (POST) without a valid host CSRF token; `@event(csrf=False)` opts a
  handler out (for token-authenticated APIs), and GET handlers are
  csrf-exempt by nature but must be read-only by contract.
- Host wiring: under Django, citry routes become plain Django views, so
  Django's own CSRF middleware applies; the client runtime attaches the
  token per configurable source, default
  `cookie:csrftoken -> header:X-CSRFToken` under Django, and
  `Citry.events.configure({ csrf: { header, cookie | meta | value } })`
  covers FastAPI/Flask conventions. The runtime never invents its own token
  scheme; it carries the host's.
- **Auth inherits by default, per-handler override.** The engine-wide and
  per-component `guard` runs for every call (livecomponents' opt-in
  per-method decorator is the anti-pattern: forgetting one method is an
  open endpoint). A guard is `callable(ctx) -> bool | None` or raises
  `EventError`; it reads host auth through `ctx.request`. Because per-event
  calls hit a real URL, host-native protection (Django decorators via
  middleware, FastAPI dependencies on the mount, WAF rules, rate limits)
  also applies per action, which the single-opaque-endpoint designs
  (Livewire, unicorn) cannot offer.
- Instance ids and class ids are identifiers, not secrets; possession of a
  valid state token is not authorization (unlike livecomponents' session
  id). Authorization is the guard plus host auth, evaluated per call.

### 8.4 Abuse limits

Envelope size cap (413), `calls` length cap (schema: 16), args validated
before any handler code runs, state verified before args are even looked at
(cheapest rejection first), and the `on_event_call` hook as the rate-limit
seam. Handlers are user code; the dispatcher never evaluates strings, never
imports from wire data, never touches attribute paths derived from wire
data.

---

## 9. Server push: explicit deferral, designed seam

Deferred to v3 (after the WS transport). The design already contains its
seam, so deferral costs nothing structurally:

- The pushed payload is an ops list, identical to a result's ops (the Turbo
  Streams model: push is the same format over another channel, which the
  ecosystem survey identified as the most portable push design).
- The reserved frame is `{ "type": "push", "channel": "...", "ops": [...] }`
  over any transport with a `subscribe` capability (WS first; SSE would slot
  in as a down-only transport with zero protocol change).
- Channel names are server-signed strings a render embeds in the events
  manifest (Turbo's signed stream names); a client can subscribe only to
  channels it was handed. Server API sketch, not committed:
  `citry.events.publish(channel, [Render(Board(id=42), target="css:#board")])`.
- Until v3, the documented pattern for near-live UIs is polling an
  `@event(method="GET")` handler, which the protocol supports today.

What v3 must decide (recorded now): worker-to-socket fan-out (a broker
dependency), reconnect semantics (re-subscribe, no resume, consistent with
4.3), and whether SSE ships alongside WS for WSGI-adjacent stacks.

---

## 10. OpenAPI and schema generation

Per-event routes make this nearly free, the django-ninja model applied to
component events (no surveyed interactive framework generates schemas from
event handlers; this is open ground and a citry differentiator):

- Every handler already compiles to an argument model (6.2). The
  `citry ext run events openapi --app my_app:citry --out openapi.json`
  command walks registered Events-declaring components and emits OpenAPI 3.1
  over the per-event URL template: one operation per (component, event),
  `operationId = f"{ComponentName}_{event}"`, request body (or query
  parameters for GET handlers) from the argument model, responses documented
  as the result envelope (`application/json`) plus `text/html` for the
  compatibility mode, 422 with the field-error shape, and the state/CSRF
  parameters as documented headers/fields.
- The same walk emits the client manifest
  (`citry ext run events manifest`): a JSON document of classes, events, arg
  schemas, and hints. Consumers: the class descriptor (3.7) at runtime,
  TypeScript type generation in the future `packages/js/citry-client`, the
  planned Storybook extension, and the component introspection API
  (issue #26) as a data source rather than a dependency; when #26 lands,
  the manifest becomes one of its views.
- WS gets an AsyncAPI document later, generated from the same models;
  explicitly out of v1 scope.

Limits stated honestly: return types are not schematized in v1 (handlers may
return unions of ops and values; the envelope schema documents the container,
not each handler's `data` payload). A v2 opt-in
(`@event(returns=SomeModel)`) can tighten per-operation response schemas for
API-first users.

---

## 11. Cross-language conformance

The protocol is the shared artifact; each host language reimplements the
dispatcher; the client runtime is shared by everyone. Keeping five future
implementations honest requires machinery, specified now:

- `packages/protocol/events/v1/` (section 3.9) is the source of truth:
  prose spec, JSON Schemas, and golden fixtures against the canonical
  fixture component (defined in the spec in citry template syntax, so every
  binding can implement it).
- A binding passes conformance when: (a) every fixture call envelope
  produces the fixture result envelope modulo declared-volatile fields
  (instance ids, state tokens, hashes; the fixture format marks volatile
  JSON paths, the same discipline as the compiler's locked-output tests),
  and (b) every envelope it emits validates against the schemas.
- Python: a pytest module in the citry package loads the fixtures and runs
  them through `EventsDispatcher` with the fixture component registered;
  schema validation via a vendored JSON Schema checker in tests only.
- Client: the runtime's tests replay result fixtures through
  `Citry.events.applyOps` in a DOM harness, plus one Playwright e2e that
  drives a real browser round trip against a live server (the
  `test_fragment_e2e.py` pattern already in the repo).
- Rule recorded in the spec: any protocol change lands as a fixture/schema
  change in the same PR, and additive-only within a major (3.5). When the
  JS/PHP/Go server bindings arrive, they import the same fixture directory;
  nothing about the suite is Python-shaped (fixtures are JSON, the component
  is citry-syntax, volatility is declared as JSON paths).
- The state token is exempt from cross-binding conformance by design: it is
  opaque, minted and verified by the same binding.

Rust involvement: none in v1; there is no proven shared primitive here (the
render walk stays in Python per the settled performance decision). If a
compile-time event-binding validation ever justifies grammar work (7.4),
that is a separate, Mechanism-2-gated change.

---

## 12. Substrate changes required (v0, before the extension)

Each is small, independently shippable, and useful beyond Events. Listed
because the extension is impossible without the first two (a POST body is
literally unreachable through the ASGI adapter today).

1. **`RouteRequest`.** A frozen dataclass
   (`method, path, query: Mapping, headers: Mapping, body: bytes,
   content_type, host: Any`) built by every adapter and passed as the
   handler's `request` argument. Existing citry handlers never read
   `request` (documented in `routing.py:12-14`), so this is a contract
   tightening with no behavior change for them; the old host object stays
   reachable at `request.host`. CHANGELOG entry (public API of the routing
   util changes).
2. **ASGI body + async.** The ASGI adapter drains `receive` into
   `RouteRequest.body`, awaits async handlers, and runs sync handlers in a
   worker thread instead of blocking the event loop. WSGI reads
   `environ["wsgi.input"]`; Django adapter reads `request.body` and maps
   async handlers to async views (sync WSGI rejects async handlers with a
   pointed error).
3. **`RouteResponse.headers`**: `tuple[tuple[str, str], ...] = ()`, applied
   by all adapters. Backward compatible (default empty).
4. **`CitrySettings.secret: str | list[str] | None`** plus the
   `citry.contrib.django.secret()` convenience.
5. **`citry.js` context-decorator seam** (`Citry.manager.decorateContext`),
   about ten lines, generic (any extension can enrich the `$onComponent`
   context). While in the file, add the long-promised stuck-call console
   warning (design-doc promise at `dependencies.md:507`, currently
   unimplemented); unrelated but adjacent.
6. **(v2) `WSRoute` + `asgi_ws_app`** for the WebSocket transport.

---

## 13. Migration stories

### 13.1 django-components `Component.View`

```python
# Before (django-components): one method per HTTP verb, multiplexing by hand
class Calendar(Component):
    class View:
        def get(self, request, *args, **kwargs):
            if request.GET.get("type") == "events":     # verb exhausted, so: query multiplexing
                return self.component_cls.render_to_response(...)
            return self.component_cls.render_to_response(...)
        def post(self, request, *args, **kwargs):
            date = request.POST.get("date")             # untyped hand parsing
            ...

url = get_component_url(Calendar, query={"type": "events"})
```

```python
# After (citry): one handler per action, typed, each with its own URL
class Calendar(Component):
    class Events:
        @event(method="GET", csrf=False)
        def month(self, ctx, year: int, month: int) -> Render:
            return Render(year=year, month=month)

        def save_entry(self, ctx, date: date, title: str) -> Render:
            ...
            return Render()

url = get_event_url(Calendar, "month", query={"year": 2026, "month": 7})
```

What carries over: self-contained endpoints with zero urlpatterns edits, URL
minting from Python (query/params supported), auto-exposure by defining a
handler. What is gone: verb squatting, `?type=` multiplexing, the one-shot
cached `public` flag, per-class dynamic routes (the fixed parametrized route
avoids DJC's urlpatterns re-processing workaround entirely).

### 13.2 django-unicorn

```python
# Before: public attributes are the wire state; any public method is callable
class SearchView(UnicornView):
    query = ""
    results = []
    def search(self):
        self.results = lookup(self.query)
```

```html
<input unicorn:model.debounce-300="query" /> <button unicorn:click="search">Go</button>
```

```python
# After: inputs are declared kwargs; exposure is explicit; args are typed
class Search(Component):
    class Kwargs:
        results: list[str] = ()

    class Events:
        @event(method="GET", debounce=300)
        def search(self, ctx, query: str) -> Render:
            return Render(results=lookup(query))
```

```html
<input c-on:input.debounce-300="search" c-arg:query="value" />   <!-- v1.1 -->
```

Kept from unicorn: the modifier grammar, type-hint coercion, host-native
validation with field errors on the wire. Dropped deliberately: full state
through the client (only declared kwargs travel, signed), public-by-default
callability, pickle-in-cache persistence, executable call-expression
strings. The per-keystroke-POST cost model also improves: GET handlers are
cacheable and debounce is declared once server-side.

### 13.3 Tetra

```python
# Before: @public methods, whole live object pickled+encrypted into the page
class Counter(Component):
    count = public(0)
    @public
    def increment(self):
        self.count += 1
```

```python
# After: same ergonomics, state is the declared input, token is signed JSON
class Counter(Component):
    class Kwargs:
        count: int = 0

    class Events:
        def increment(self, ctx) -> Render:
            return Render(count=ctx.kwargs["count"] + 1)

    js = """
        $onComponent(({ els, send }) => {
          els[0].querySelector("button").onclick = () => send("increment");
        });
    """
```

Kept from Tetra: the versioned envelope with typed messages, server methods
returning promises to client JS, rate limits declared once in Python and
enforced client-side, 410 stale-state semantics, the file-download escape
(return a host response from the per-event route). Dropped: pickling live
objects (with its whitelist-unpickler and key-leak-equals-RCE history),
Alpine as a hard dependency, and the open then retroactively whitelisted
callback channel (citry's server-to-client channel is the closed op
vocabulary from day one).

### 13.4 livecomponents

```python
# Before: Pydantic state class + @command + manual parent_id threading + Redis
@command
def increment(self, call_context: CallContext[RootState], value: int):
    call_context.state.value += value
```

```python
# After: no session store, no manual hierarchy; cross-component update by target
class Root(Component):
    class Events:
        def increment(self, ctx, value: int):
            new_total = ctx.kwargs["value"] + value
            return [
                Render(value=new_total),
                Render(Badge(count=new_total), target="css:#badge", swap="replace"),
            ]
```

Kept: the execution-result algebra as a return-value algebra, one response
updating N self-addressed targets, return-nothing-is-cheap defaults.
Dropped: the Redis/pickle session (and its 410-reload UX), raw template
source stored server-side (citry re-renders from a first-class entry point,
never from captured template text), honor-system state-mirrors-kwargs
(citry captures kwargs automatically and errors loudly on the
unserializable), per-method opt-in auth (guards inherit).

---

## 14. Incremental delivery plan

**v0, substrate (independent small PRs):** section 12 items 1-5. Exit
criterion: a POST route handler under FastAPI, Flask, and Django can read a
JSON body and set a response header, proven by contrib tests.

**v1, the extension (HTTP only):**

- Protocol package: spec.md, schemas, fixtures (the first artifact merged).
- Dispatcher: envelope validation, exposure rules, guards, state tokens,
  arg validation/coercion, return algebra, error mapping, `caps` downgrade.
- HTTP transport: batch + per-event routes, JSON and urlencoded codecs,
  compatibility/no-JS mode, CSRF wiring, URL builder
  (`get_event_url` / `component.events.url`).
- Client runtime: registry, events manifest observer, HTTP transport,
  `send`/`on` context members via the decorator seam, `replace`-family
  swaps, busy attribute, lifecycle CustomEvents.
- Conformance: fixture suite green in pytest; op-application tests; one
  Playwright e2e (button click to re-rendered fragment with assets).
- Docs: user guide plus the security page (what round-trips, what is
  exposed, CSRF per host).

**v1.1:** `morph` swap (vendored idiomorph) behind `caps`; declarative
`c-on:*` bindings + modifier grammar with server hints; multipart codec +
`UploadedFile`; `openapi` / `manifest` / `routes` commands; postMessage
transport + bridge (unblocks the Storybook extension's interactive
previews).

**v2:** WebSocket transport (`WSRoute`, `asgi_ws_app`, connect auth, frame
handling; dispatcher unchanged); client-side send coalescing into batch
envelopes; optional pluggable server-side state store.

**v3:** server push (signed channels, `publish`, WS delivery; SSE
evaluated); AsyncAPI generation.

Each stage leaves the previous one fully working; nothing in v1 is
throwaway because later stages add transports and ops, never reshape the
envelope (that is what the protocol-first ordering buys).

---

## 15. Falsifiability

Concrete outcomes that would prove parts of this design wrong, and what each
would force:

1. **The signed-kwargs state model is wrong** if, when migrating the three
   worked examples (form submission, fragments demo, autocomplete) plus two
   real components, more than one in five Events-declaring components cannot
   express its re-render inputs as JSON-safe kwargs under the 16 KiB cap
   without contortions. Consequence: the pluggable server-side store moves
   from v2-optional to v1-required (the protocol survives; the token becomes
   a capability id).
2. **The v1 `replace` swap is insufficient** if the migrated form example
   cannot keep focus/scroll behavior acceptable for a text-input-heavy flow,
   i.e. testers reach for htmx anyway. Consequence: morph moves into v1.
3. **The transport abstraction is fake** if implementing the WS transport
   (v2) or the postMessage bridge requires changing the dispatcher's
   signature or any envelope field. Consequence: redesign the
   `TransportContext` boundary before v2 ships.
4. **The protocol is Python-shaped** if the conformance fixtures cannot be
   consumed unmodified by the client runtime's test harness (v1) or require
   per-language forks when the first non-Python binding arrives.
   Consequence: strip the offending fields into binding-private extensions
   and re-cut the schemas.
5. **Per-event routes are the wrong HTTP grain** if host-level middleware
   (Django decorators, FastAPI dependencies) cannot express a real app's
   per-action auth without falling back to guards for everything, across
   both Django and FastAPI test apps. Consequence: promote the guard system
   and demote the per-event route to an alias.
6. **Batching is speculative** if by v2 no measured page produces
   multi-call envelopes worth coalescing (the field stays a single-element
   array in practice). Consequence: keep the array (cost is zero) but drop
   the client coalescing feature.
7. **The no-JS compatibility mode is dead weight** if no documented example
   or user request exercises it by v1.1. Consequence: demote it from
   guaranteed contract to best-effort behavior in the spec.

---

## 16. Alternatives considered and rejected

- **HTTP-verb handlers (Component.View shape).** Rejected by charter and by
  the recorded failure mode: verbs run out and actions end up multiplexed
  through query params (`migration_djc.md:150`; the fragments example's
  `?type=` dispatch is the exhibit).
- **Reactive public attributes with full state round-trip**
  (unicorn/Tetra/Livewire family). Rejected: it requires either client-held
  rich state (the documented CVE surface: rehydration, class pollution,
  pickle) or server-held live objects (process affinity, WS coupling).
  Citry components are input-driven by design; signing the declared inputs
  gets stateless re-render with none of the rehydration machinery. The cost,
  accepted openly: no "just mutate self" ergonomics; state changes are
  explicit `Render(**changes)`.
- **WebSocket-first (LiveView shape).** Rejected for v1: it forces ASGI and
  connection-state infrastructure on every deployment, while the ecosystem
  trend since ~2024 runs the other way (Datastar, Turbo demoting WS,
  LiveView's own longpoll fallback pains). HTTP works under every adapter
  citry ships today; WS arrives as an additive transport precisely because
  dispatch is stateless.
- **Delegating the client half to htmx.** Rejected: the roadmap excludes an
  htmx pack, and livecomponents demonstrates where a five-library client
  prerequisite leads (a documentation page that is a footgun catalog).
  Interop is preserved instead: per-event URLs speak form-encoding and
  `Accept: text/html`, so htmx can consume Events endpoints without citry
  adopting htmx.
- **A single opaque RPC endpoint only (no per-event URLs).** Rejected:
  per-action host middleware, meaningful access logs, rate limiting, and
  OpenAPI all want real URLs (the django-ninja lesson); the fixed
  parametrized route gives them without dynamic route registration. The
  batch endpoint exists alongside it because batching and per-action
  addressing are both real needs.
- **New `$sendEvent`/`$onEvent` source rewrites.** Rejected in favor of
  context members (7.1): rewrites cannot bind instance identity and the
  substring-matching transform has known sharp edges. The requested
  capability ships; the spelling is safer.
- **Storing raw template/render state server-side to re-render** (the
  livecomponents mechanism). Rejected outright: citry owns its compiler and
  re-renders from `Cls(**kwargs)`; nothing ever re-parses stored template
  text, and no HTML string is ever cached or replayed (the repo's standing
  cache rule).

---

## 17. Open questions (tracked, non-blocking)

1. Does the V3 grammar pass `c-on:click` through as a literal attribute
   (7.4)? Check before v1.1; fallback spelling `data-on:*` reserved.
2. Should GET event handlers set cache headers by default (`no-store` vs
   opt-in caching)? Leaning `no-store` default with `@event(cache=...)`
   later.
3. Multi-instance shared rendering: when several instances of the same
   component with identical kwargs exist, one `render` op per instance is
   emitted today; a `target: "cids:[...]"` plural form is reserved if this
   ever measures as heavy.
4. Whether `citry-client` (TypeScript home for both runtimes) starts in
   v1.1 or waits for the JS binding milestone; the runtime ships as plain JS
   package data either way, matching the dependencies runtime today.
