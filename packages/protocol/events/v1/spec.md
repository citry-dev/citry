# `citry-events/1`

Citry Events lets browser code call a named component handler on the Python server.
The browser sends JSON describing what events to call, and the server answers with a
small list of actions such as render this fragment, update this component's
State, dispatch this DOM event, or return this data value.

This document defines protocol major 1. The JSON Schemas are the exact
structural rules, [`validate.py`](validate.py) checks the worked examples, and
[`tests/`](tests/) shows complete exchanges and deliberate failures.

## One exchange from start to finish

Suppose a `TodoList` template contains this button:

```html
<button @c-click="add({text: newItem})">Add</button>
```

When the server renders `TodoList`, its Events manifest tells the browser the
class's `componentClassId`, its public handler names, this occurrence's
`renderId`, and its State token. A click can then send:

```json
{
  "protocol": "citry-events/1",
  "requestId": "r_8f2k1c",
  "calls": [
    {
      "componentClassId": "TodoList_a1b2c3",
      "handlerName": "add",
      "callerRenderId": "c9zk1q00",
      "args": {"text": "Buy milk"},
      "stateToken": "cev1.eyJ...9mYt",
      "sendSequence": 4
    }
  ]
}
```

The server runs the handler and answers:

```json
{
  "protocol": "citry-events/1",
  "requestId": "r_8f2k1c",
  "results": [
    {
      "ok": true,
      "sendSequence": 4,
      "actions": [
        {
          "action": "render",
          "target": "render:c9zk1q00",
          "swap": "replace",
          "html": "<div>...</div>"
        }
      ]
    }
  ]
}
```

Three relationships make that round trip predictable:

1. `requestId` connects one result envelope to one call envelope.
2. `results[i]` answers `calls[i]`.
3. `sendSequence` connects a result to the caller's send order, so an older
   response cannot overwrite a newer render.

The rest of this document explains those objects and the manifest that gives
the browser its starting handler and State information.

## The contract is strict

Fixed protocol records contain exactly their documented fields. A missing
required field or an extra field is an error. The same rule applies to call
envelopes, calls, capabilities, result envelopes, results, errors, actions,
manifests, component class records, component instance records, and handler
options.

The browser checks the complete result envelope and every action's protocol
shape before it applies the first action. If the tenth action has an invalid
field or value, none of the first nine runs. A result can still fail after
that check for reasons outside the JSON shape, such as a target that names a
component the page no longer shows or malformed rendered content. The server
performs the equivalent full protocol check before it runs a call.

Only places that deliberately carry application data remain open:

- handler names are dynamic keys inside `eventHandlers`;
- `args`, `stateUpdates`, `publicState`, and `fieldErrors` accept application
  field names;
- a `data` action's `value` and an `event` action's `detail` accept any JSON
  value.

All wire values are standard JSON. `NaN`, infinities, executable expressions,
revivable objects, and other language-specific values are not part of the
protocol. Servers produce deterministic JSON apart from values that are
naturally minted per render, such as render IDs, state tokens, and HTML that
contains them. Optional fields at their default value are omitted.

## TypeScript view of the JSON

These interfaces are a quick map of the complete wire format after it has
passed validation. They are documentation types, not the browser runtime's
types for untrusted input. A `?` means the property is omitted when absent;
`| null` means the property is still present in JSON with the value `null`.

TypeScript cannot express every protocol rule. It does not make object fields
exact, prove that numbers are finite integers, check string patterns or unique
array values, connect an error code to its required status, or enforce
relationships between records. The JSON Schemas and the checks later in this
document remain authoritative.

Application-owned values use ordinary JSON:

```ts
type JsonPrimitive = string | number | boolean | null;
type JsonValue = JsonPrimitive | JsonValue[] | JsonObject;

interface JsonObject {
  [key: string]: JsonValue;
}
```

### Calls

One call envelope contains one or more handler calls. `capabilities` and its
three properties may be omitted to use the v1 defaults.

```ts
type EventSwap =
  | "morph"
  | "replace"
  | "inner"
  | "append"
  | "prepend"
  | "remove"
  | "none";

type EventActionKind =
  | "render"
  | "data"
  | "state"
  | "event"
  | "redirect"
  | "url";

type EventRenderer = "html-fragment/1" | "vue-prepared/1";

interface EventsCapabilities {
  swaps?: EventSwap[];
  actions?: EventActionKind[];
  renderers?: EventRenderer[];
}

interface EventCall {
  componentClassId: string;
  handlerName: string;
  callerRenderId?: string;
  args: JsonObject;
  stateToken?: string;
  stateUpdates?: JsonObject;
  sendSequence?: number;
}

interface EventsCallEnvelope {
  protocol: "citry-events/1";
  requestId: string;
  capabilities?: EventsCapabilities;
  calls: EventCall[];
}
```

### Results and errors

The literal `ok` property selects the success or error shape. `sendSequence`
is present exactly when the corresponding call included it.

```ts
type EventErrorCode =
  | "invalid_args"
  | "invalid_state"
  | "stale_state"
  | "unknown_event"
  | "unknown_component"
  | "forbidden"
  | "not_found"
  | "conflict"
  | "error"
  | "csrf_failed"
  | "payload_too_large"
  | "protocol_mismatch"
  | "handler_error";

interface EventProtocolError {
  status: number;
  code: EventErrorCode;
  message: string;
  fieldErrors?: Record<string, string>;
}

interface EventSuccessResult {
  ok: true;
  sendSequence?: number;
  actions: EventAction[];
}

interface EventErrorResult {
  ok: false;
  sendSequence?: number;
  error: EventProtocolError;
}

type EventResult = EventSuccessResult | EventErrorResult;

interface EventsAnsweredResultEnvelope {
  protocol: "citry-events/1";
  requestId: string;
  results: EventResult[];
}

interface EventEarlyErrorResult {
  ok: false;
  error: EventEarlyProtocolError;
}

type EventEarlyProtocolError =
  | {
      status: 400;
      code: "protocol_mismatch";
      message: string;
    }
  | {
      status: 413;
      code: "payload_too_large";
      message: string;
    };

interface EventsEarlyErrorEnvelope {
  protocol: "citry-events/1";
  requestId: null;
  results: [EventEarlyErrorResult];
}

type EventsResultEnvelope =
  | EventsAnsweredResultEnvelope
  | EventsEarlyErrorEnvelope;
```

### Actions

The literal `action` property selects one of six action shapes. Every action
may be delayed. Most actions may set `wait` to `false` so later actions can
continue immediately. A data action always waits because applying it resolves
the caller's promise.

```ts
interface ActionTiming {
  delay?: number;
  wait?: false;
}

// render:<renderId> or mark:<callerRenderId>:<name>
type RenderActionTarget = `render:${string}` | `mark:${string}:${string}`;
type EventActionTarget = `render:${string}`;

interface LegacyRenderAction extends ActionTiming {
  action: "render";
  target: RenderActionTarget;
  swap: EventSwap;
  html: string;
}

interface HtmlRenderAction extends ActionTiming {
  action: "render";
  target: RenderActionTarget;
  swap: EventSwap;
  renderer: "html-fragment/1";
  html: string;
}

interface PreparedRenderAction extends ActionTiming {
  action: "render";
  target: RenderActionTarget;
  swap: "morph";
  renderer: "vue-prepared/1";
  prepared: JsonObject;
}

type RenderAction = LegacyRenderAction | HtmlRenderAction | PreparedRenderAction;

interface DataAction {
  action: "data";
  value: JsonValue;
  delay?: number;
}

interface StateAction extends ActionTiming {
  action: "state";
  targetRenderId: string;
  stateToken: string;
  publicState: JsonObject;
}

interface DispatchEventAction extends ActionTiming {
  action: "event";
  eventName: string;
  detail?: JsonValue;
  target?: EventActionTarget;
}

interface RedirectAction extends ActionTiming {
  action: "redirect";
  url: string;
}

interface UpdateUrlAction extends ActionTiming {
  action: "url";
  url: string;
  mode: "push" | "replace";
}

type EventAction =
  | RenderAction
  | DataAction
  | StateAction
  | DispatchEventAction
  | RedirectAction
  | UpdateUrlAction;
```

### Manifest records

The manifest contains one descriptor per component class and one record per
rendered component occurrence that declares Events. The standalone
[`descriptor.schema.json`](descriptor.schema.json) describes the same
`EventComponentClass` shape used here.

```ts
interface EventHandlerOptions {
  httpMethod: string;
  usesState?: true;
  debounceMilliseconds?: number;
  throttleMilliseconds?: number;
  latestCallWins?: true;
  allowBatching?: false;
}

interface EventComponentClass {
  componentClassId: string;
  eventHandlers: Record<string, EventHandlerOptions>;
  writableStateFields?: string[];
}

interface EventComponentInstance {
  renderId: string;
  componentClassId: string;
  stateToken: string | null;
  publicState: JsonObject;
}

interface EventsManifest {
  protocol: "citry-events/1";
  componentClasses: EventComponentClass[];
  componentInstances: EventComponentInstance[];
}
```

### What each identifier identifies

The IDs are deliberately separate because they answer different questions:

| Field | What it identifies |
|---|---|
| `requestId` | One call envelope and the result envelope that answers it. |
| `componentClassId` | The registered component class containing the Python handler. |
| `renderId` | One rendered occurrence of a component. Each new render receives a new ID. |
| `callerRenderId` | The rendered occurrence that sent a call. |
| `targetRenderId` | The rendered occurrence whose State token and public State values a `state` action updates. |
| `render:<renderId>` | A render or DOM-event action target that names one rendered occurrence. |
| `mark:<callerRenderId>:<name>` | A render action target that names one `<c-mark>` region inside the calling occurrence. |
| `handlerName` | The Python handler the server runs. |
| `eventName` | The browser DOM `CustomEvent` an `event` action dispatches. |
| `sendSequence` | The order in which one stable browser record sent its calls. |

## The call envelope

[`call.schema.json`](call.schema.json) is authoritative for structure. The
top-level fields are:

| Field | Rule | Purpose |
|---|---|---|
| `protocol` | Required; exactly `citry-events/1`. | Selects the protocol major. |
| `requestId` | Required non-empty string. | A client-created request ID that the server echoes. |
| `capabilities` | Optional strict object. | Says which v1 actions, swaps, and renderers this browser can apply. See [Capabilities](#capabilities). |
| `calls` | Required array of 1 to 16 calls. | `results[i]` answers `calls[i]`. |

Each call contains:

| Field | Rule | Purpose |
|---|---|---|
| `componentClassId` | Required non-empty string. | Identifies the registered component class that owns the handler. |
| `handlerName` | Required non-empty string. | Names the public event handler. |
| `callerRenderId` | Optional string matching `^[a-z0-9_-]+$`. | Identifies the rendered component occurrence that sent the call. |
| `args` | Required object. | Open application data passed to the handler. An empty call uses `{}`. |
| `stateToken` | Optional non-empty string. | The caller's opaque signed State token. |
| `stateUpdates` | Optional object. | Open application data containing browser-writable State changes to apply before the handler. |
| `sendSequence` | Optional integer at least 0. | The increasing send counter for the browser's stable record of this caller. |

`componentClassId` and `handlerName` describe the server code to run.
`callerRenderId` describes where the call came from in the rendered page. They
are separate because an API client or hand-written form can call a stateless
handler without representing a rendered component.

The server verifies `stateToken`, applies `stateUpdates` only to fields the
State contract makes browser-writable, validates `args`, and then invokes the
handler. Authentication, cookies, CSRF headers, and transport credentials do
not ride inside the envelope.

### Send order

The browser keeps a stable internal record for an interactive component as it
re-renders and receives new render IDs. The implementation calls this record
an **anchor**. Every call from it increments a counter and sends that value as
`sendSequence`. The server copies the value into the corresponding result,
whether that result succeeds or fails.

When responses arrive out of order, the browser can discard an older action
that would replace that caller's HTML or State token. The older caller may
still receive its own `data` value, and actions aimed elsewhere keep their
normal meaning. Some internal variables still call the counter an epoch; the
wire name is always `sendSequence`.

### Envelope limits

One envelope carries at most 16 calls. More than 16 rejects the whole
envelope with `payload_too_large`. A transport may also enforce a configured
HTTP body limit before parsing, using the same error code. A client that wants
to send more calls splits them into successive envelopes.

## The result envelope

[`result.schema.json`](result.schema.json) defines the exact downlink shape:

| Field | Rule | Purpose |
|---|---|---|
| `protocol` | Required; exactly `citry-events/1`. | Names the server's protocol. |
| `requestId` | Required non-empty string, or `null` when the request supplied no usable ID. | Echoes the call envelope's request ID when available. |
| `results` | Required non-empty array. | Holds one answer per call, in call order. |

A success result is:

```json
{"ok": true, "sendSequence": 4, "actions": []}
```

An error result is:

```json
{
  "ok": false,
  "sendSequence": 4,
  "error": {
    "status": 422,
    "code": "invalid_args",
    "message": "Validation failed for 1 field(s).",
    "fieldErrors": {"text": "This field is required."}
  }
}
```

`sendSequence` is present exactly when the answered call carried it and must
equal that call's value. A success always has `actions`, even when the array is
empty. An error has `error` and never has `actions`.

### Actions

Actions are a closed v1 vocabulary:

| Action | Required fields | Optional fields | Meaning |
|---|---|---|---|
| `render` | `target`, `swap`, and `html` or `prepared` | `renderer`, `delay`, `wait` | Update one component occurrence, or one marked region inside the caller, with newly rendered content, as `swap` says. |
| `data` | `value` | `delay` | Resolve the caller with any JSON value, including `null`. A result has at most one data action. |
| `state` | `targetRenderId`, `stateToken`, `publicState` | `delay`, `wait` | Replace one rendered component occurrence's State token and the public State values the browser shows. |
| `event` | `eventName` | `detail`, `target`, `delay`, `wait` | Dispatch a bubbling DOM `CustomEvent`. Names beginning `citry:` are reserved. |
| `redirect` | `url` | `delay`, `wait` | Navigate the page. |
| `url` | `url`, `mode` | `delay`, `wait` | Push or replace browser history without navigation. `mode` is `push` or `replace`. |

A render action carries its content in one of two forms, selected by its
`renderer` (see [Capabilities](#capabilities)):

- `html-fragment/1` carries `html`, a complete HTML fragment. When the
  content is interactive, the fragment mounts its own Vue app and includes
  the inert JSON and asset tags that app needs, including its Events records.
- `vue-prepared/1` carries `prepared`, a JSON object that the browser merges
  into the Vue app already on the page. Its Events records are inside that
  object.

The v1 swaps are `morph`, `replace`, `inner`, `append`, `prepend`, `remove`,
and `none`. A `vue-prepared/1` render always uses `morph`: the browser updates
the mounted component in place, while the other swaps insert, remove, or skip
DOM content, which prepared content never does. An `html-fragment/1` render
may use any v1 swap. Citry's browser client applies only `vue-prepared/1`
renders; `html-fragment/1` serves other clients and form posts without
JavaScript, which read the HTML directly.

### State refresh

A handler can change State without rendering the calling component again, for
example when it only returns data or renders a `<c-mark>` region. The browser
still shows the old values in `$state` and in State bindings, and it still
holds a token for State that the server has replaced. So the server places a
`state` action before the handler's own actions. A counter handler that only
runs `state.count += 1` answers:

```json
{
  "action": "state",
  "targetRenderId": "c9zk1q00",
  "stateToken": "cev1.eyJ...k2Qa",
  "publicState": {"count": 1, "name": "Counter"}
}
```

`publicState` holds every public State field of the target after the handler
ran, under the same rules as `publicState` in the manifest's component
instance record. A field outside the component's public State never appears.
A render of the calling component carries its fresh token and values in its
Events records instead, so the server sends no `state` action for it.

The browser applies the action in three steps:

1. It stores `stateToken`, which the component's next call sends back.
2. It sets each field of the target's browser State object to the value in
   `publicState`. A field the browser changed but has not sent yet keeps the
   browser's value, and that value travels with the next call.
3. It removes a field that is missing from `publicState`, unless that field
   has an unsent browser value.

Citry's browser client applies a `state` action that has no `delay` and no
`wait: false` before the other actions in the result, so code triggered while
later actions run sees the fresh token and values.

These inputs fail or degrade as follows:

- A missing `publicState`, or one that is not a JSON object, fails protocol
  validation. The receiver rejects the whole result before it applies any
  action.
- Field names inside `publicState` are application data, so the protocol does
  not reject an extra or missing field. The browser adds the extra field and
  removes the missing one, as the steps above say. When the class record omits
  `writableStateFields`, Citry's browser client also treats an extra field as
  writable, and the server then rejects the next call that sends it as
  `invalid_args`. A server sends exactly the component's public fields.
- The protocol does not check a field's value against the State declaration.
  The browser shows the value it receives, so a server sends values of the
  declared types. The server still validates every browser write against the
  declaration when the next call carries it.
- Citry's browser client skips a `state` action in a server result whose
  `targetRenderId` names no component that its Vue app currently shows. Page
  code that passes such an action to `Citry.events.applyActions` gets a
  rejected promise instead, because that function first finds the component
  each action names.

### Targets

A target tells the browser which rendered component an action is about. It
names the component directly, so the browser finds it in its own records
instead of searching the page. There are two forms:

1. `render:<renderId>` names one rendered component occurrence. The ID
   matches `^[a-z0-9_-]+$`, the same rule as `renderId` in the manifest.
2. `mark:<callerRenderId>:<name>` names one `<c-mark name="...">` region that
   the calling component rendered. Marker names are unique only inside the
   component that renders them, so the target carries the caller's render ID
   as well. The name matches `^[A-Za-z][A-Za-z0-9_-]*$`.

A handler can update a small part of its own output without re-rendering the
whole component. Given this template fragment:

```citry-html
<c-mark name="cart-badge">
  <c-CartBadge c-count="count" />
</c-mark>
```

a handler returns
`actions.Render(CartBadge(count=3), target="mark:cart-badge")`, and the server
writes the caller's render ID into the wire target:

```json
{
  "action": "render",
  "target": "mark:c9zk1q00:cart-badge",
  "swap": "morph",
  "renderer": "vue-prepared/1",
  "prepared": {"...": "..."}
}
```

Render actions accept both forms. An `event` action's optional `target`
accepts only `render:<renderId>`; the event fires on that component's first
connected element and bubbles from there. The server only ever addresses an
event to the calling component. The `targetRenderId` of a `state`
action uses the same ID rule without the `render:` prefix.

When the server creates a render, State refresh, or event action without an
explicit target, it targets the `callerRenderId` automatically. A call
without a rendered caller cannot have an automatic component target: the
server fails a render without a target, or with a `mark:` target, as a
`handler_error`, and an unaddressed event dispatches on `document`.

A target in any other form, such as a CSS selector (`#cart`), a marker
without its caller (`mark:cart-badge`), or an empty ID (`render:`), fails
protocol validation, so a receiver rejects the whole result before it applies
any action.

Citry's browser client also rejects the whole result, before any action runs
and with the caller's promise rejected, in these cases:

- A render target names a component that is not currently mounted in the
  caller's Vue app, or a marker whose caller is not the component that sent
  the call. This happens when the component was replaced or removed while the
  call was in flight.
- An event target names a component other than the caller.
- A result holds several `vue-prepared/1` renders and any of these is
  true: they are not next to each other in the list, one has a positive
  `delay` or `wait: false`, or two name the same component or a component
  and one inside it. The browser applies such a group as one update.

### Order and timing

Actions keep their list order. Each action may add `delay`, a finite number of
seconds at least 0 that is omitted at 0. Every action except `data` may also
add `wait: false` to schedule the delayed action and continue with the
following action immediately. A data action must remain in the sequence
because applying it settles the caller's promise.

Only `false` is valid when `wait` is present. A blocking delay preserves order.
When a delayed action runs, Citry's browser client first checks that the
calling component is still mounted and that no newer result for it has been
applied; otherwise it skips a non-blocking action and fires
`citry:events:stale`, or rejects the caller's promise for a blocking one.
This check is what keeps a delayed `state` action from replacing newer State
values and a newer token with older ones.
Actions after a redirect race the navigation, so a server should warn when it encodes
such a list even though the authored order remains unchanged.

### Errors

Every wire error has exactly `status`, `code`, and `message`, plus optional
`fieldErrors`. `fieldErrors` maps application field names to string messages.

| Code | Status | Meaning |
|---|---:|---|
| `invalid_args` | 422 | Handler args or State updates failed validation. |
| `invalid_state` | 403 | The State token is malformed or fails signature verification. |
| `stale_state` | 409 | The token expired or was signed only by a rotated-out secret. |
| `unknown_event` | 404 | The component class declares no handler under that name. |
| `unknown_component` | 404 | No registered component class has that ID. |
| `forbidden` | 403 | Application authorization denied the call. |
| `not_found` | 404 | Application code reported a missing domain object. |
| `conflict` | 409 | Application code reported a domain conflict. |
| `error` | 400 to 599 | A deliberately raised application error with another status. |
| `csrf_failed` | 403 | The transport's CSRF check rejected the request. |
| `payload_too_large` | 413 | A call-count or configured transport-size limit rejected the envelope. |
| `protocol_mismatch` | 400 | The envelope names an unsupported protocol, or a fixed protocol record is malformed. |
| `handler_error` | 500 | Unexpected handler failure or a result that cannot be represented as strict JSON. |

Unexpected exceptions use a generic non-debug message. They never expose a
traceback on the wire. Error code and status pairings are strict; a future or
misspelled code is not silently treated as generic.

### Failures before a request ID can be read

An unknown protocol or more than 16 calls rejects the whole envelope before
per-call execution. If the server can read a usable request ID and the calls,
it echoes the ID and mirrors the same error into one result per call. This
preserves the index relationship.

Some failures leave the server without a usable request ID, for example
malformed JSON, a missing or invalid `requestId`, or an HTTP body rejected
before parsing. In that case the server answers with `requestId: null` and
exactly one error result, even if it could read a `calls` array from the
malformed input. That result has no `sendSequence`, because there is no valid
request to correlate it with. The built-in browser transport applies that
early error to every local call it sent. `null` has this one meaning; it is not
a wildcard request ID. An unreadable or structurally invalid body answers
`protocol_mismatch`; one rejected by the transport's byte cap answers
`payload_too_large`.

## Capabilities

Clients advertise the swaps, action kinds, and renderers they can apply:

```json
{
  "swaps": ["replace", "morph"],
  "actions": ["render", "data", "state", "event", "redirect", "url"],
  "renderers": ["html-fragment/1"]
}
```

All arrays contain unique known values. The object and its arrays are strict.
Any key may be omitted; an omitted key uses that key's v1 baseline. The
server never emits outside the advertised set. In particular, it downgrades an
`html-fragment/1` render from `morph` to `replace` for a client that did not
advertise morphing. A `vue-prepared/1` render has no such fallback, so a client
that advertises `vue-prepared/1` must also advertise `morph`; otherwise a call
that renders fails with `handler_error`. Any other render outside the
advertised swaps or renderers also fails with `handler_error`, because the
server never drops or reorders actions.

Citry's own browser client advertises exactly what it applies:

```json
{
  "swaps": ["morph"],
  "actions": ["render", "data", "state", "event", "redirect", "url"],
  "renderers": ["vue-prepared/1"]
}
```

When the complete `capabilities` object is absent, all three keys use
`CAPABILITIES_BASELINE_V1`:

```json
{
  "swaps": ["replace", "inner", "append", "prepend", "remove", "none"],
  "actions": ["render", "data", "state", "event", "redirect", "url"],
  "renderers": ["html-fragment/1"]
}
```

The baseline includes every v1 action and every v1 swap except `morph`, which
needs a morphing runtime.

An omitted Render `renderer` means `html-fragment/1` and requires the legacy
`html` string. An explicit `html-fragment/1` action also carries only `html`.
A `vue-prepared/1` action carries only a strict JSON `prepared` object. Unknown
renderers, mixed content representations, and renderer output absent from the
caller's advertised set are invalid.

## State tokens

`stateToken` is opaque to the client. The browser stores the string and sends
it back verbatim. The server binding that minted it owns its internal format
and verifies it.

The plain public State values are separate. They appear in `publicState` in
two places: the component's Events record, where browser code reads them to
set up the component's reactive State, and a `state` action, which updates
them after a handler changes State (see [State refresh](#state-refresh)). Server-only values never appear in either
place. A refreshed token arrives the same two ways: in the Events records of a
new render, or in a `state` action beside the refreshed values.

## How the browser learns what it can call

The call protocol needs initial browser information that ordinary HTML does
not contain: which handler names a component class exposes, which State fields
the browser may write, which State values belong to one rendered occurrence,
and which opaque token that occurrence must send back.

For each render, the server first builds one Events manifest for every
component in it that declares Events, and validates the whole manifest.
[`manifest.schema.json`](manifest.schema.json) defines the complete shape. A
typical manifest is:

```json
{
  "protocol": "citry-events/1",
  "componentClasses": [
    {
      "componentClassId": "TodoList_a1b2c3",
      "eventHandlers": {
        "add": {"httpMethod": "POST", "usesState": true},
        "filter": {
          "httpMethod": "GET",
          "usesState": true,
          "debounceMilliseconds": 300
        }
      },
      "writableStateFields": ["query"]
    }
  ],
  "componentInstances": [
    {
      "renderId": "c9zk1q00",
      "componentClassId": "TodoList_a1b2c3",
      "stateToken": "cev1.eyJ...9mYt",
      "publicState": {"query": "shoes"}
    }
  ]
}
```

The manifest does not travel to the browser as one object. The server copies
each instance record, together with its class record, into that component's
entry in the page's Vue app data. The app data is inert JSON, carried in a
`<script type="application/json">` tag in the page or fragment, or in the
`prepared` object of a `vue-prepared/1` render action. Before embedding JSON in
HTML, the server escapes `<` as `\u003c`, so State containing `</script>`
cannot close the script element. This escaping is what **script-safe JSON**
means here; parsing restores the original value. The browser parses the tag as
JSON and never executes its contents.

Before a component sends a call, the browser checks that component's records:
the class record must pass the descriptor checks and name the same
`componentClassId` as the instance. A component whose records fail the check
cannot send calls; the browser rejects the call instead of sending it.

### Top-level fields

| Field | Meaning |
|---|---|
| `protocol` | Exactly `citry-events/1`. |
| `componentClasses` | Class-wide handler and writable-State descriptors. |
| `componentInstances` | Per-render occurrence tokens and public State values. |

### Component classes

Every class record requires `componentClassId` and `eventHandlers`, plus
optional `writableStateFields`. Class IDs are unique in one manifest.

`eventHandlers` maps each non-empty public handler name to a strict options
object:

| Hint | Rule | Meaning |
|---|---|---|
| `httpMethod` | Required uppercase HTTP token. | Method used on the per-handler route. |
| `usesState` | Optional; when present it is exactly `true`. | The handler receives State. |
| `debounceMilliseconds` | Optional non-negative integer. | Default debounce for compiled browser bindings. |
| `throttleMilliseconds` | Optional non-negative integer. | Default throttle for compiled browser bindings. |
| `latestCallWins` | Optional; when present it is exactly `true`. | A newer call supersedes older calls to this handler in the client queue. |
| `allowBatching` | Optional; when present it is exactly `false`. | Calls to this handler must travel alone. |

The defaults are omitted: State is unused, timing is absent, older calls are
not superseded, and batching is allowed.

`writableStateFields` narrows which public State fields `$state` and two-way
bindings may change. Omission means every public field is writable. An empty
array means public State is readable but not writable. Values are unique,
non-empty strings.

[`descriptor.schema.json`](descriptor.schema.json) is the same component class
record schema exposed on its own for tools that inspect descriptors without a
whole manifest.

### Component instances

Each instance record requires:

| Field | Meaning |
|---|---|
| `renderId` | The rendered occurrence ID that `render:` action targets and a call's `callerRenderId` name. |
| `componentClassId` | A class ID present in `componentClasses` in the same manifest. |
| `stateToken` | A non-empty opaque token, or `null` for a stateless instance. |
| `publicState` | Open application data used to initialize the reactive browser State object. |

Render IDs are unique and match `^[a-z0-9_-]+$`. A stateless record has
`stateToken: null` and an empty `publicState`. A stateful record keeps its
public values and token separate so browser code never needs to parse or
rewrite the token.

### Checks that connect the records

JSON Schema checks individual object shapes. Executable checks handle the
relationships that are clearer in code:

- The reference validator checks unique class and render IDs, class
  references, and the stateless `stateToken: null` plus empty `publicState`
  rule.
- The exchange checker verifies that `results[i]` answers `calls[i]`, request
  IDs match, every `sendSequence` is echoed exactly, results stay within the
  advertised capabilities, and each result contains at most one `data`
  action.

The server validates a complete call envelope before running its first
handler. The browser validates a complete result envelope before applying its
first action. The server validates a complete Events manifest before it hands
any record to a component. A failure rejects that whole unit.

## HTTP adapters

The protocol is transport-neutral. The built-in HTTP transport mounts:

```text
POST      <prefix>/ext/events/call
GET       <prefix>/ext/events/runtime.js
GET|POST  <prefix>/ext/events/e/{componentClassId}/{handlerName}
```

The batch route accepts the standard protocol envelope and always uses POST. The
per-handler route uses the handler's allowed method and mirrors a single error
result's status onto HTTP for useful middleware and access logs. Redirects
remain actions, never HTTP 30x responses.

A standard JSON envelope uses
`Content-Type: application/citry-events+json`. The batch route may also accept
it under `application/json`. On the per-handler route, plain JSON, form data,
and query strings are convenience adapters: they build a standard one-call
envelope, then enter the same strict dispatcher. The URL supplies
`componentClassId` and `handlerName`; an explicit protocol body must agree
with it.

For GET, handler arguments keep their query names and protocol metadata uses:

| Query field | Protocol field |
|---|---|
| `_citry_protocol` | `protocol` |
| `_citry_request_id` | `requestId` |
| `_citry_capabilities` | JSON-encoded `capabilities` |
| `_citry_caller_render_id` | `callerRenderId` |
| `_citry_state_token` | `stateToken` |
| `_citry_send_sequence` | `sendSequence` |

Adapters remove these reserved fields before validating handler arguments. A
hand-authored GET URL may omit all of them. The adapter supplies the current
protocol, a transport-local request ID, baseline capabilities, and no caller,
token, or send sequence.

## Versioning

The protocol major is part of the exact `protocol` string. This directory is
the working pre-release v1 contract. Until the owning Citry package reaches
`1.0.0`, clearer field names and other incompatible corrections change v1 in
place, but schemas, examples, server, browser, tests, and current docs must
move together.

Unknown fields and values are not a minor-version extension mechanism. A v1
reader rejects them. If a future extension or third-party integration needs
more wire data, design that point deliberately and add conformance examples.
After Citry reaches `1.0.0`, an incompatible shape starts `v2/` and uses
`citry-events/2`.

## The conformance component

Every server binding ports this component as its conformance surface. The
template, defaults, handler names, and behavior stay the same across
languages. The Python implementation is the reference:

```python
from citry import Component
from citry.ext.events import EventError, actions, event


class RenameIn:
    name: str


class SquareIn:
    value: int


class FailIn:
    status: int


class CounterState:
    count: int = 0
    name: str = "Counter"


class Counter(Component):
    class Kwargs:
        count: int = 0
        name: str = "Counter"

    State = CounterState

    class Events:
        def _guard(self):
            if self.event.name == "rename":
                name = self.event.args.get("name")
                if name == "admin":
                    raise EventError(
                        "The name 'admin' is reserved.",
                        status=403,
                    )

        def increment(self, state: CounterState):
            state.count += 1
            return Counter(count=self.count, name=self.name)

        def rename(self, data: RenameIn, state: CounterState):
            state.name = data.name
            return [
                actions.Dispatch(
                    "counter:renamed",
                    {"name": state.name},
                    delay=1.5,
                    wait=False,
                ),
                {"name": state.name},
            ]

        def crash(self, state: CounterState):
            raise RuntimeError("boom")

        @event(methods=("GET",))
        def square(self, data: SquareIn):
            return actions.Data({"value": data.value * data.value})

        def history(self):
            return [
                actions.PushUrl(
                    "/counters?page=2",
                    delay=0.25,
                    wait=False,
                ),
                actions.ReplaceUrl("/counters?page=3"),
            ]

        def fail(self, data: FailIn):
            raise EventError(
                "The counter cannot do that.",
                status=data.status,
            )

    def template_data(self, kwargs, slots):
        return {
            "count": kwargs.count,
            "name": kwargs.name,
        }

    template = """
      <div>
        <h2>{{ name }}</h2>
        <button @c-click="increment">
          Clicked {{ count }} times
        </button>
      </div>
    """
```

The examples use `increment` for rendering and capability downgrade,
`rename` for event and data actions plus a State refresh, `crash` for an
unexpected handler failure, `square` for stateless data over GET, `history`
for the two URL modes, and `fail` for deliberate application errors.

## Conformance

A server binding passes when it:

1. accepts every valid golden call in [`tests/index.json`](tests/index.json);
2. produces the matching golden result, differing only at its listed
   `dynamic_fields`;
3. emits calls, results, descriptors, and manifests that validate against the
   schemas;
4. rejects each deliberately invalid descriptor and manifest for the same
   reason as the reference validator.

A browser reader passes when it:

1. accepts every valid manifest and rejects every invalid manifest before
   using any of its records;
2. validates a complete result before any action side effect;
3. applies every valid result example with the documented ordering, targeting,
   State, and send-order behavior.

[`tests/README.md`](tests/README.md) explains the corpora and
`dynamic_fields`. When an implementation and a worked example disagree, fix
the implementation unless the protocol itself is deliberately changing. A
protocol change updates the spec, schemas, validator, examples, server,
browser, and tests together.
