# Ecosystem recon: event/interactivity patterns for a Component.Events extension

Research input for the citry `Component.Events` design (named in
`docs/design/extensions_roadmap.md:62` as part of the single
server-interactive design exploration). Frameworks surveyed: Laravel
Livewire v3, Phoenix LiveView, Hotwire/Turbo Streams, StimulusReflex, htmx,
Datastar, Inertia.js, and django-ninja (for its signature-to-OpenAPI model).
Organized by pattern, not by framework. "Applicability" notes assume citry's
situation: server-rendered components that already ship scoped JS and CSS
(`Component.js` / `Component.css` class attributes, with a JS runtime script
injected when present), and an existing `Extension.urls` route surface
mounted under `ext/<extension-name>/`
(`packages/py/citry/citry/extension.py:391` and `:661-684`).

---

## Axis 1: transport

### Pattern 1a: single shared HTTP endpoint for all component updates

**Used by:** Livewire v3 (every interaction POSTs to `/livewire/update`).
The payload names the component(s) and the method calls; routing happens
inside the framework, not in the host router.

**Tradeoffs.** One route to secure, one CSRF story, trivial to mount. The
cost is that the endpoint is a generic RPC dispatcher: the host framework's
routing, middleware-per-route, and URL-based tooling (rate limiting per
action, OpenAPI, access logs that mean something) see only one opaque URL.
Livewire compensates by replaying the original page's route middleware from
data stored in the snapshot.

**Applicability to citry.** Fits `Extension.urls` perfectly: one route like
`ext/events/update` works identically under Django/FastAPI/Flask adapters.
The single-endpoint model is the cheapest cross-adapter option because citry
does not own the host router.

### Pattern 1b: per-component or per-action routes

**Used by:** htmx and Datastar (every `hx-post` / `@post()` targets a real
app route you write), Inertia (normal app routes), django-ninja (each
operation is a route). Turbo Streams also rides normal form-submission
routes.

**Tradeoffs.** Each handler is a first-class URL: host middleware, auth
decorators, caching, and schema tooling all apply per action. The cost is
route explosion and boilerplate, and the framework must either generate the
routes or make the user register them. For a component framework this also
leaks component internals into the URL space unless the URLs are generated
and treated as opaque.

**Applicability.** citry can get this almost free: generate one child route
per registered component-event pair under the extension namespace, e.g.
`ext/events/<component>/<event>`. This preserves the single mount point
(pattern 1a's deploy simplicity) while giving per-action URLs (pattern 1b's
middleware and schema benefits). django-ninja demonstrates the registration
model: decorated handlers collected on a router object, then mounted once.

### Pattern 1c: persistent WebSocket

**Used by:** Phoenix LiveView (one socket per page at `/live`, one channel
per LiveView on the page), StimulusReflex (Rails ActionCable), Turbo Streams
in broadcast mode (ActionCable subscription per stream).

**Tradeoffs.** Lowest per-event latency, and the only transport that gives
true server push plus per-connection server state. Costs: a connection
process/task per visitor, sticky or distributed infrastructure (LiveView's
longpoll fallback requires all nodes connected because resuming a session
must reach the original process, per the Phoenix issue tracker), and a
second auth model (authenticate the socket, not each request). In the
Python world this also forces ASGI and rules out plain WSGI deployments.

### Pattern 1d: SSE as the down-channel, plain HTTP up

**Used by:** Datastar (browser sends normal fetch requests; the response is
a Server-Sent Events stream that can carry many patches over one
connection, and a long-lived SSE connection doubles as a push channel).
htmx has SSE and WS as extensions. Turbo Streams can also arrive over SSE.

**Tradeoffs.** Server push without WebSocket infrastructure; each response
can stream multiple updates over time (progress bars, multi-step effects);
works through most proxies. Costs: one-directional (uplink is still
request/response), long-lived connections still consume a worker unless the
server is async, and browsers cap concurrent HTTP/1.1 connections per host
(HTTP/2 mostly removes this).

**Applicability.** For citry, plain HTTP request/response should be the v1
transport (works on WSGI and ASGI alike), with the response format designed
so it could later be streamed as SSE frames without changing the payload
schema. That is exactly Datastar's shape: its SSE events
(`datastar-patch-elements`, `datastar-patch-signals`) are self-contained
messages that also make sense as a one-shot response body.

### Batching and debouncing

- Livewire v3 bundles simultaneous updates from multiple components on a
  page into a single network request by default; a component opts out with
  `#[Isolate]` (lazy-loaded components are isolated by default so they load
  in parallel). Input events use `wire:model.live` with a default 150 ms
  debounce, tunable per binding (`.debounce.500ms`).
  Source: https://livewire.laravel.com/docs/3.x/bundling
- LiveView debounces/throttles per binding (`phx-debounce`, `phx-throttle`)
  and serializes events per channel.
- htmx has `hx-sync` to coalesce or replace in-flight requests; Datastar has
  per-listener modifiers (`data-on-input__debounce.500ms`).

**Lesson:** debounce belongs on each event listener, as an attribute
modifier, and batching belongs in the client runtime (queue
events for one tick, send one request). Both are client-runtime concerns
that citry's shipped JS runtime is well placed to own. Batching only pays
off if the wire format allows multiple component calls per request, so
decide that in the payload schema up front even if v1 sends one call.

### Optimistic UI

No surveyed server-driven framework does true optimistic mutation. The
converged pattern is "pending state, not predicted state": Livewire
`wire:loading` / `wire:dirty`, LiveView loading classes plus `JS` commands
that run instantly client-side (toggle/class changes with zero round trip),
htmx `hx-indicator`, Datastar local signal mutation before the request.
Inertia leaves it to the client framework entirely. **Lesson:** provide
pending-state hooks (a class on the triggering element, an event the scoped
JS can listen to) and let genuinely optimistic behavior live in the
component's own JS; do not build rollback machinery.

---

## Axis 2: payload direction and format

### Pattern 2a: JSON commands up, HTML down (re-render the component)

**Used by:** Livewire v3. Uplink: JSON with the component snapshot, property
updates, and method calls. Downlink: the component's fully re-rendered HTML
plus a new snapshot; the client morphs it into the DOM (Alpine-based
morphing).

**Tradeoffs.** Dead simple mental model (the server just renders the
component again, same code path as first render). Payload is the whole
component's HTML every time, so large components pay for small changes.
Morphing HTML into a DOM that client JS has mutated is the classic conflict
zone; every framework in this family documents "the morph ate my
client-side change" issues.

### Pattern 2b: static/dynamic diffs down

**Used by:** Phoenix LiveView. The template compiles into static string
parts and dynamic slots; after the first render the server sends only the
changed dynamic slots, and the client (morphdom) patches the DOM. Sources:
https://hexdocs.pm/phoenix_live_view/Phoenix.LiveView.html

**Tradeoffs.** Smallest payloads in the field and the best latency, but it
requires (a) a compile step that knows which template parts are static
(citry's compiler already distinguishes constant parts, see the constness
machinery in `packages/py/citry/citry/constness.py`), and (b) the server
remembering the previous render per client, which drags in server-held
state (axis 4). Diffing is what makes LiveView effectively
WebSocket-only in practice.

### Pattern 2c: multi-fragment HTML down, each fragment self-addressed

**Used by:** Turbo Streams (`<turbo-stream action="replace" target="dom_id">`
elements; nine actions: append, prepend, before, after, replace, update,
remove, morph, refresh; one response or broadcast can contain any number of
them). htmx out-of-band swaps (`hx-swap-oob` attribute on any element in
the response body; the main target gets the primary content, every OOB
element updates its own target elsewhere). Datastar
(`datastar-patch-elements` events, morphed by element ID, any number per
response). Sources: https://turbo.hotwired.dev/handbook/streams ,
https://htmx.org/attributes/hx-swap-oob/ ,
https://data-star.dev/reference/sse_events

**Tradeoffs.** This is the field's answer to "one event updates multiple
components": the response is a list of (target, action, HTML) operations,
addressed by DOM id, requiring no client-side registry of components. It is
stateless, works over any transport (HTTP body, SSE frame, WS message), and
degrades to "just HTML". Cost: the server must know the DOM ids of
everything it wants to update, and ids become a public contract.

**Applicability.** Strongest candidate for citry's downlink format. A
response shaped as a list of operations
`[{target, action, html}, ...]` (or the equivalent HTML encoding) lets one
event handler re-render its own component and any other affected
components in the same response, without a second round trip. Livewire's
alternative (component A dispatches an event, listening components B and C
each make their own bundled follow-up request) costs an extra round trip
and needs client-side event plumbing.

### Pattern 2d: JSON only, client renders

**Used by:** Inertia.js. Response is a page object
`{component, props, url, version}`; the client framework (Vue/React/Svelte)
re-renders. Partial reloads let the client request only some props via
`X-Inertia-Partial-Data` / `X-Inertia-Partial-Except` headers.
Source: https://inertiajs.com/the-protocol

**Tradeoffs.** Clean protocol, fully typed-friendly, but it presumes a
client rendering engine. Not a fit for citry's server-rendered components;
relevant only as (a) prior art for header-based protocol negotiation
(`X-Inertia`, version header forcing a full reload on asset change) and
(b) the prop-selection idea, which maps to "re-render only these slots".

### Side channel: response-triggered client events

htmx's `HX-Trigger` response header (JSON map of event name to detail)
lets the server fire arbitrary client-side events after a swap; LiveView's
`push_event/3` does the same over the socket, dispatched with a `phx:`
prefix. **Applicability:** citry components already ship scoped JS, so a
"server can dispatch a named browser event with a JSON detail" channel is
cheap and immediately useful (the component's own JS listens for it). This
is the natural citry story for effects that are not DOM swaps (focus,
scroll, toast, chart update).

---

## Axis 3: handler naming and dispatch

### Pattern 3a: public-method convention (implicit exposure)

**Used by:** Livewire (`wire:click="increment"` calls the public PHP method
`increment`; arguments are written as literals in the template expression
and serialized into the `calls` array). StimulusReflex
(`data-reflex="click->CounterReflex#increment"`; only methods on `Reflex`
subclasses are callable).

**Tradeoffs.** Zero ceremony, but every public method becomes a remote
endpoint whether the author meant it or not. Livewire's own security
guidance says to treat every public property and method as user-facing
input; the ecosystem's worst vulnerabilities (unmarshaling RCEs, see
Synacktiv's Livewire research) sit on this surface. Argument coercion is
another soft spot: Livewire coerces call arguments to parameter type hints
(including resolving Eloquent models by ID, which quietly turns an argument
into a database fetch that needs its own authorization).

### Pattern 3b: explicit registration (opt-in exposure)

**Used by:** LiveView (an event exists only if you wrote a
`handle_event("name", params, socket)` clause; names are arbitrary strings
you pattern-match), htmx/Datastar/django-ninja (a handler exists only if
you registered a route/decorated a function).

**Tradeoffs.** Slightly more ceremony; nothing is exposed by accident. The
event name is decoupled from the method name, which allows renaming server
internals without touching templates.

**Applicability.** The roadmap already leans this way: "handlers named by
the event they handle" (`docs/design/extensions_roadmap.md:62`). The clean
Python shape is a nested `class Events:` namespace on the component where
only methods defined there (or only methods decorated `@event`) are
exposed. Opt-in is the right default given citry renders arbitrary user
components; Livewire's implicit model is the cautionary tale.

### Argument encoding and coercion

- LiveView: values come from `phx-value-*` attributes or a `JS.push` value
  map, arriving as a string-keyed map with string values; the handler
  parses. No coercion, no magic, no schema.
- Livewire: literal args in the template expression, JSON-encoded, coerced
  to PHP type hints server-side.
- Datastar: no per-call args at all; the whole signal state travels with
  every request (GET: `datastar` query param, otherwise JSON body;
  underscore-prefixed signals stay client-only).
  Source: https://data-star.dev/guide/backend_requests
- django-ninja: the gold standard for coercion; see axis 5.

**Lesson:** args as a JSON object validated against the Python signature
(django-ninja style) beats both LiveView's stringly-typed maps and
Livewire's coerce-anything approach. citry can do this because the handler
is a Python function whose signature is introspectable at registration
time.

---

## Axis 4: state model and security

### Pattern 4a: client-held signed state, stateless server

**Used by:** Livewire v3. The component's public properties are serialized
into a JSON "snapshot" `{data, memo, checksum}` embedded in the page; every
update POST sends it back; the server verifies
`hash_hmac('sha256', snapshot, app_key)` before rehydrating, applies
updates and calls, re-renders, and returns a new snapshot.
Sources: https://livewire.laravel.com/docs/3.x/hydration ,
https://www.synacktiv.com/en/publications/livewire-remote-command-execution-through-unmarshaling

**Tradeoffs.** No server session, horizontal scaling is free, state
survives server restarts. Costs: state size rides every request both ways;
state is user-visible (signed, not encrypted, in Livewire's case); and the
rehydration machinery (synthesizers reviving rich PHP objects from JSON
tuples) has been the root of real RCEs. Critically, the checksum covers
only the snapshot; the `updates` and `calls` fields are legitimately
user-controlled input and must be authorized like any request body.
`#[Locked]` properties exist because "any public property is writable" was
too permissive.

### Pattern 4b: server-held state per connection

**Used by:** LiveView (assigns live in the LiveView process for the life of
the socket; the page embeds only a signed session token used to re-mount),
StimulusReflex (Rails session plus re-running the controller action).

**Tradeoffs.** Nothing sensitive leaves the server, payloads are minimal,
diffs become possible. Costs: memory per connected client, state dies with
the connection (LiveView re-runs `mount` on reconnect; anything not
reconstructible from params/session/DB is lost, and form recovery needs a
dedicated mechanism, `phx-auto-recover`), and multi-node deployments need
distribution.

### Pattern 4c: no framework state; every request rebuilds from scratch

**Used by:** htmx, Turbo, Datastar (Datastar keeps client state in signals
and sends all of it up each request, so the server is stateless but fully
informed). Auth and CSRF are the host framework's normal per-request story.

**Applicability.** For citry v1, 4a-lite is the pragmatic model: send back
the component's input props (kwargs) as a signed payload so the server can
re-render statelessly, but keep it (a) HMAC-signed with the host secret,
(b) restricted to JSON-safe values with no rich-object revival (the
Livewire RCE lesson: hydration of arbitrary types is the dangerous part,
not signing), and (c) size-capped. Server-held state (4b) should not be a
v1 requirement because it forces the WebSocket/process model. CSRF: the
Livewire precedent is to require the host CSRF token on the update
endpoint; Turbo's precedent for push channels is signed stream names so a
client cannot subscribe to streams it was not given.

---

## Axis 5: schema and typing (the django-ninja model)

How django-ninja turns a signature into an API: at registration the
decorator inspects the view function's signature; path parameters bind by
name, scalar-annotated params become query params, params annotated with a
`Schema`/pydantic model become the JSON body; a pydantic model is built per
operation, so parsing, validation, coercion, and error responses (422 with
field paths) all come from one source of truth; the same models emit
`/openapi.json` and Swagger UI, with `operationId` derived from the
function name. Sources: https://django-ninja.dev/guides/input/body/ ,
https://github.com/vitalik/django-ninja (see `ninja/signature/`,
`ninja/openapi/schema.py`).

**No surveyed interactive framework generates schemas for its events.**
LiveView params are untyped string maps; Livewire has no schema at all;
Turbo/htmx/Datastar have no handler concept to type. The nearest ecosystem
moves are Inertia-adjacent TypeScript prop/route generators (e.g. Laravel
Wayfinder) which are codegen bolted on afterwards.

**What it would take for citry (and why it is a differentiator):**
event handlers are plain Python methods, so citry can do what django-ninja
does at component-registration time: build a pydantic (or lighter) model
from each handler's signature, use it to validate and coerce the JSON args
of incoming events, and emit two artifacts from the same source: (1) an
optional OpenAPI document for the generated event routes (free if events
get per-action routes, pattern 1b), and (2) a client-side manifest (event
names plus arg shapes) that the shipped JS runtime and the planned
Storybook `ExtensionCommand` (`docs/design/extensions_roadmap.md:66`) can
consume, including TS type generation later. None of the eight frameworks
offers this; it aligns with citry's existing type-hint-driven culture.

---

## Axis 6: WebSocket specifics (if/when citry adds a push channel)

- **Connection granularity:** the converged answer is one socket per page,
  multiplexed. LiveView: one `LiveSocket` to `/live`, each LiveView on the
  page is its own channel/topic on that socket; components within a
  LiveView share its channel (`pushEventTo` targets a component).
  StimulusReflex/Turbo: one ActionCable consumer per page, one subscription
  per channel/stream. Nobody opens a socket per component; per-component
  sockets do not survive real pages with dozens of components.
- **Reconnect/resume:** LiveView reconnects with backoff and re-runs
  `mount` from the signed session token, then re-renders and re-diffs; in-
  flight client state is lost unless recovered explicitly (form recovery
  via `phx-auto-recover`). The design lesson: reconnect is a re-mount, not
  a resume; do not promise resumable server state.
- **Fallback:** LiveView ships a long-poll fallback
  (`longPollFallbackMs`) but its own issue tracker shows the fallback
  sticking and requiring node affinity; ActionCable has no HTTP fallback.
  Datastar sidesteps the whole problem by never needing WS (SSE
  reconnection is built into the browser EventSource model).
- **Server push:** LiveView: `handle_info` + Phoenix.PubSub mutate assigns
  and diff down; `push_event/3` reaches page JS (dispatched as `phx:`
  events on `window`). Turbo: `broadcast_*_to` renders stream fragments to
  subscribers of a signed stream name; the page markup opts in with one
  `turbo_stream_from` tag. The Turbo model (page subscribes to named,
  signed streams; server broadcasts self-addressed fragments) is the most
  portable push design because the payload is identical to the HTTP
  response format.

---

## Tradeoffs matrix

| Pattern | Who | Latency | Server cost | Deploy complexity | Multi-component updates | Degrades to no-JS/plain HTTP | Typing/schema potential | Main risk |
|---|---|---|---|---|---|---|---|---|
| 1a Single endpoint, JSON up / HTML down | Livewire | 1 RTT | Stateless render | Lowest | Extra round trips via client events | No | Poor (opaque RPC) | Implicit method exposure, rehydration attacks |
| 1b Per-action routes | htmx, Datastar, ninja | 1 RTT | Stateless render | Low | Via OOB fragments in response | Yes (htmx) | Best (route = operation) | Route sprawl if hand-written |
| 1c WebSocket + server state + diffs | LiveView, StimulusReflex | Lowest | Process per client | Highest (ASGI, affinity/distribution) | Free (any assign change diffs down) | Needs fallback machinery | Untyped in practice | Reconnect = state loss; infra burden |
| 1d HTTP up / SSE down | Datastar | 1 RTT, streamable | Async worker per open stream | Medium | Free (N patches per stream) | Partially | Good | Long-lived connections on sync servers |
| 2c Self-addressed fragment list | Turbo, htmx OOB, Datastar | n/a | n/a | n/a | The reference solution | Yes | n/a | DOM ids become contract |
| 2d JSON page object | Inertia | 1 RTT | Serialize only | Low | Whole-page props | No | Good | Requires client renderer |

## What the field has converged on vs what is still contested

**Converged:**
1. HTML over the wire, morphed into the live DOM, is the standard downlink
   for server-rendered components; JSON-down lost everywhere a server
   renderer exists.
2. Multi-target updates ship as a list of self-addressed operations
   (target id + action + fragment) in one response; Turbo Streams, htmx
   OOB, and Datastar independently landed on the same shape.
3. Explicit per-binding debounce/throttle modifiers on the client
   attribute, and pending-state indicators instead of optimistic mutation.
4. One multiplexed connection per page when there is a push channel, never
   per component.
5. Signed/HMAC-protected anything-that-round-trips (Livewire snapshots,
   LiveView session tokens, Turbo stream names), with host CSRF on the
   uplink.
6. A server-to-client named-event side channel (HX-Trigger, push_event)
   for non-DOM effects, which is exactly the hook scoped component JS
   needs.

**Still contested:**
1. Transport: stateless HTTP (Livewire, htmx), SSE (Datastar), and
   stateful WS (LiveView) each have thriving camps; the trend since ~2024
   (Datastar, LiveView's own longpoll fallback, Turbo demoting WS to
   optional broadcasts) is away from WS-required designs.
2. Where state lives: signed client snapshot vs server process vs
   client signals; no winner, and it is the main fork in the road for any
   new design.
3. Exposure model: implicit public methods (Livewire) vs explicit
   registration (LiveView); the security record argues for explicit.
4. Diff granularity: full-component morph vs static/dynamic slot diffs;
   diffs need compiler support and per-client memory, and only LiveView
   has judged that worth it.
5. Typed events: nobody generates schemas from handler signatures; this is
   open ground where a Python framework can import the django-ninja model
   wholesale.

## Sources

- https://livewire.laravel.com/docs/3.x/hydration
- https://livewire.laravel.com/docs/3.x/bundling
- https://www.synacktiv.com/en/publications/livewire-remote-command-execution-through-unmarshaling
- https://hacktricks.wiki/en/pentesting-web/deserialization/livewire-hydration-synthesizer-abuse.html
- https://hexdocs.pm/phoenix_live_view/Phoenix.LiveView.html
- https://hexdocs.pm/phoenix_live_view/js-interop.html
- https://hexdocs.pm/phoenix_live_view/bindings.html
- https://github.com/phoenixframework/phoenix/issues/5720 (longpoll fallback behavior)
- https://turbo.hotwired.dev/handbook/streams
- https://htmx.org/attributes/hx-swap-oob/
- https://htmx.org/headers/hx-trigger/
- https://docs.stimulusreflex.com/guide/morph-modes
- https://docs.stimulusreflex.com/guide/reflexes
- https://data-star.dev/guide/backend_requests
- https://data-star.dev/reference/sse_events
- https://data-star.dev/guide/reactive_signals
- https://inertiajs.com/the-protocol
- https://django-ninja.dev/guides/input/body/
- https://github.com/vitalik/django-ninja
