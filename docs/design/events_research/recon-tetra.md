# Recon: Tetra (Django + Alpine.js full-stack component framework)

Research input for the citry Component.Events extension design. Sources: the
tetra-framework/tetra GitHub repo (main branch, fetched 2026-07-04), its docs
(`docs/*.md` in the repo, rendered at tetra.readthedocs.io), the Django forum
announcement thread, PyPI/pypistats. Line numbers refer to upstream files
`src/tetra/...` and `src/tetra/js/tetra.core.js` at main as of 2026-07-04
(local copies in this scratchpad: `tetra_views.py`, `tetra_state.py`,
`tetra_base.py`, `tetra.core.js`, `changelog.md`).

Note on the brief: the requested output path was `undefined/recon-tetra.md`
(an unresolved variable in the orchestrator). This report was written to the
session scratchpad instead.

## 1. Programming model

Class hierarchy: `BasicComponent` (render-only, no server state; since 0.9.2 it
may carry simple JS without Alpine/state access), `Component` (stateful, public
methods), `FormComponent` / `ModelFormComponent` (Django forms integration),
`ReactiveComponent` (websocket subscriptions). Components are grouped into
"libraries" per Django app; each library's JS/CSS is bundled with esbuild into
one file per library.

A component colocates all four concerns as class attributes with marker type
annotations (`django_html`, `javascript`, `css`) so editors can highlight them.
Inline strings or directory-based files both work:

```python
from tetra import Component, public

class Counter(Component):
    # private attribute: pickled into server state, not visible to JS
    something: str = "My string"

    # public attributes: become Alpine.js reactive data in the browser
    count = public(0)
    message = public("hi")

    def load(self, start=0, *args, **kwargs):
        # runs at first render AND after every state resumption;
        # attributes set here are NOT saved into the state token
        self.count = start

    @public
    def increment(self):
        self.count += 1   # re-render is the default after a public method

    @public.watch("message").debounce(200)
    def message_change(self, value, old_value, attr):
        ...

    template: django_html = """
    <div {% ... attrs %} @click="increment()">
      <span x-text="count"></span>
    </div>
    """
    script: javascript = """
    export default {
        init() { /* Alpine init */ },
        clientMethod(msg) { alert(msg) },
    }
    """
    style: css = """
    .thing { color: #f00; }
    """
```

Key semantics:

- Public attributes (`public(...)`) must be serializable in Tetra's extended
  JSON (standard JSON plus datetime, date, time, set; encoded with a
  `__type` tag, `tetra.core.js:1949-1982`). They become the Alpine `x-data`
  model. Private attributes can be anything picklable through the safe-list
  (see section 4).
- `@public` marks methods callable from the browser. Modifiers chain off it:
  `.watch("attr")` (server method fires when a public attribute changes),
  `.debounce(ms)` / `.throttle(ms, leading=..., trailing=...)` (rate limits
  enforced client-side by generated wrappers, `tetra.core.js:1534-1541`),
  `.listen("keyup.shift.enter")` (subscribe to DOM events), and
  `@public(update=False)` to skip the default re-render. `public(...)
  .store("name")` syncs an attribute with an Alpine global store.
- `load()` re-runs on every resume and its writes are deliberately excluded
  from the saved state (freshness + smaller tokens). Its call arguments ARE
  saved and replayed on resume.
- Attribute life cycle on a method call, in override order: class defaults ->
  decrypted state -> `load()` -> client-sent data; then a
  `recalculate_attrs(component_method_finished)` hook runs before and after
  the method (docs `component-life-cycle.md`).
- Template usage: `{% Counter start=5 / %}` or open/close form with content;
  `attrs: class="x"` passes HTML attributes through to the root element
  (unpacked with `{% ... attrs %}`); `context: var` or `context: __all__`
  passes template context (never saved with state; excluded from state by
  default since 0.9.2, a breaking change). Slots via `{% slot %}`. One top
  level root node is required.

## 2. Client side

- The rendered root element gets `x-data="app__lib__component('<json>')"` and
  a `tetra-component-id` attribute (`components/base.py:427,554`). The initial
  JSON data includes a `__state` key holding the encrypted server-state token
  (`components/base.py:1809-1814`), so the state rides inside Alpine data, not
  in a separate hidden field.
- `Tetra.makeAlpineComponent` merges, into one Alpine data object: the user's
  `script` export, the public attributes (initial data), generated async
  wrappers for every public method, and built-in mixins
  (`tetra.core.js:1547-1568`). So component JS and templates call server
  methods as plain methods: `this.increment()` / `@click="increment()"`. Each
  wrapper is `async` and resolves to the Python method's return value
  (`tetra.core.js:1530-1533`, result extracted at `tetra.core.js:1685,1789`).
- Built-in client mixins: `_updateHtml(html)` (Alpine.morph),
  `_updateData(data)`, `_replaceComponent(html)`, `_removeComponent()`,
  `_dispatch(event, data)` (bubbling CustomEvent; parents listen with
  `@my-event="handler($event)"`), `_redirect`, `_pushUrl`,
  `_updateSearchParam`, `_setValueByName`, `_fetchHtml` (calls the reserved
  `_refresh` method) (`tetra.core.js:984-1310`).
- State sync back to the server: before each call, the client collects every
  public attribute plus the encrypted `__state`, recursively including child
  components (`getStateWithChildren`, `tetra.core.js:1571-1589`), and sends it
  all with the request. The server therefore gets both the trusted encrypted
  snapshot and the untrusted current public data.
- DOM update strategy: `Alpine.morph` with three server-selected data modes
  (`components/base.py:415-427,1831-1840`, applied at
  `tetra.core.js:1179-1198`):
  - INIT: fresh `x-data` (first render),
  - MAINTAIN: keep the client's existing Alpine data across the morph
    (`x-data-maintain`),
  - UPDATE: overwrite client data with server data, but per key only if the
    client value has not changed since it was submitted (`x-data-update` +
    `x-data-update-old` old-value comparison). This is a small operational
    conflict-resolution protocol for concurrent user input.
- `_updateData` additionally skips the key bound (via `x-model`) to the
  currently focused input, so a server push never clobbers text the user is
  typing (`tetra.core.js:1212-1236`).
- Lifecycle DOM events (all `tetra:` namespaced CustomEvents carrying the
  component in `detail`): `tetra:before-request`, `tetra:after-request`,
  `tetra:component-updated`, `tetra:component-data-updated`,
  `tetra:component-before-remove`, `tetra:component-stale`,
  `tetra:method-error`, `tetra:new-message` (Django messages), plus websocket
  (`tetra:websocket-connected/-disconnected`, subscription events) and offline
  queue events (`tetra:call-queued`, `tetra:call-reconciled`,
  `tetra:call-rolled-back`, `tetra:call-conflict`, ...).

## 3. Transport and protocol

Two HTTP endpoints total (`src/tetra/urls.py:7-8`): `POST /__tetra__/call/`
(one unified endpoint for all component method calls, introduced in 0.9.0,
previously per-component URLs) and `POST /__tetra__/navigate/` (fire-and-forget
client-side navigation notify, 204 response). Reactive components additionally
use one websocket at `/ws/tetra/` (`tetra.core.js:221`).

Request envelope (`tetra.core.js:1839-1855`, validated in
`src/tetra/views.py:52-70`):

```json
{
  "protocol": "tetra-1.0",
  "id": "<random request id>",
  "type": "call",
  "payload": {
    "component_id": "...",
    "method": "increment",
    "args": [...],
    "state": { "count": 1, "__serverStores": {...} },
    "encrypted_state": "<fernet token>",
    "children_state": [ ...recursive same shape... ],
    "app_name": "myapp", "library_name": "default", "component_name": "counter"
  }
}
```

Headers: `T-Request: true`, `T-Current-URL`, `X-CSRFToken`; CSRF protected.
Normally `application/json`; if any public attribute holds a `File`, the client
switches to `multipart/form-data` with the JSON envelope in a `tetra_payload`
form field and files as separate parts (`tetra.core.js:1867-1889`,
`views.py:38-39,100-102`). Method dispatch is registry lookup by
app/library/component name; the method must be in the component's
`_public_methods` list or be the reserved `_refresh` (`views.py:77-90`).

Response (`components/base.py:1919-1934`):

```json
{
  "protocol": "tetra-1.0",
  "type": "call.response",
  "success": true,
  "payload": { "result": <method return value>, "html": "<re-rendered html>" },
  "metadata": {
    "js": ["<library bundle urls>"],
    "styles": ["..."],
    "messages": [<django messages>],
    "callbacks": [ {"callback": ["_updateData"], "args": [{...}]} ]
  }
}
```

Client handling (`tetra.core.js:1633-1799`): lazily inject any listed js/css
bundle not yet in the page, morph `payload.html` into the DOM if present, then
execute `metadata.callbacks` in order, and finally resolve the caller's promise
with `payload.result`. Server-raised exceptions come back as
`success: false, error: {code: <exception class name>, message}` with HTTP 500
(`base.py:1937-1950`); stale state returns HTTP 410 with code
`StaleComponentState` and the client removes the component and fires
`tetra:component-stale` (`views.py:126-140`, `tetra.core.js:1635-1653`).
A `FileResponse` returned from a public method bypasses JSON entirely; the
client sniffs `Content-Disposition: attachment` and triggers a download
(`base.py:1905-1908`, `tetra.core.js:1657-1666`).

The callbacks channel is how Python drives the client: `self.client.foo(...)`
is a recording proxy (`components/callbacks.py`, `CallbackList` /
`CallbackPath`) that appends `{callback: [path...], args: [...]}` entries;
built-ins like `update()`, `update_data()`, `replace_component()`,
`push_url()` are implemented on top of it (`base.py:1852-1889`). On the
client, a whitelist restricts execution to the nine built-in `_` methods and
blocks `__proto__`/`constructor`/`prototype` path segments
(`tetra.core.js:1741-1768`). Notable drift: the docs still show calling custom
component JS via `self.client.clientMethod('A value')`, which the current
whitelist blocks; only `_dispatch` remains as the sanctioned generic channel.

Websocket protocol mirrors the same envelope style: typed messages
`subscription.response`, `notify` (server-dispatched CustomEvents),
`component.data_changed`, `component.created`, `component.removed`, plus
ping/pong (`tetra.core.js:286-327`). A `ComponentDispatcher` lets any server
code push to channel groups; automatic per-client groups exist for
`auth.user.{id}`, `session.{key}`, and `broadcast` (docs
`reactive-components.md`). Offline calls are queued in memory with a pre-call
snapshot (public data + encrypted state + HTML) and replayed on reconnect,
with per-status reconciliation: 200 apply, 401/403 rollback without retry,
409 refresh, 5xx rollback and retry (docs `offline-queue.md`).

## 4. State model and security

Tetra pickles the entire live component object, then wraps it as
`version:timestamp:hmac_sha256_signature:` + gzip(pickle), then encrypts the
whole envelope with Fernet (AES-128-CBC + HMAC) (`state.py:550-604`). The
Fernet key is derived per user session: HKDF-SHA256 over Django's
`SECRET_KEY` with salt = session_key + username and info `"tetra-state"`
(`state.py:511-531`), so a token from one session/user cannot be replayed in
another. The HMAC signature uses a separate SHA-256 key derived from
`SECRET_KEY` + a constant (`state.py:475-487`). Tokens expire after
`TETRA_STATE_MAX_AGE` (default 24h, `state.py:43`); expiry, version mismatch,
or bad signature raise `StateException` with "refresh the page" messaging
(`state.py:640-666`).

Unpickling is restricted by a custom `StateUnpickler.find_class` whitelist
(`state.py:321-455`): safe builtins; named classes from datetime, decimal,
collections, pathlib, uuid, itertools; ALL of `django.template.*` and
`tetra.templates.*`; any `BasicComponent` subclass; any `Model` subclass from
a `*.models` module; all of `django.forms.*`. Registered "picklers" store
references instead of values: `QuerySet` as model + query (re-executed lazily),
`Model` as class + pk (refetched on resume, `None` if deleted, which is what
feeds the 410 stale path), `FieldFile` and temp uploaded files as path
references, template `BlockNode` by origin + path key (`state.py:109-241`).
The docs are explicit that the token doubles as an authorization capability:
state is captured "after any view based authentication" and "holds onto that
authentication when resumed later" (docs `state-security.md`).

Honest assessment: this is a carefully hardened version of a fundamentally
risky choice. The safe-list unpickler only landed in 0.9.0 (2026-02); before
that, pickle depth-charge safety rested entirely on Fernet secrecy, meaning a
leaked `SECRET_KEY` was remote code execution, and even now the whitelist is
broad (all django.forms, all Model and BasicComponent subclasses). Pickling
live objects also couples tokens to code layout: renaming a class or deploying
a change can invalidate every open page (410/StateException), and server
restarts break queued offline calls (documented limitation). Tokens ride in
every render and every request, so state size is a per-interaction tax that
needed gzip, context-stripping (`state.py:535-585`), and load()-exclusion
mitigations.

## 5. Forms, files, websockets

- `FormComponent`/`ModelFormComponent`: public attributes are auto-generated
  from form fields; `validate()` (server) populates `form_errors`; `submit()`
  runs validation then `form_valid()`/`form_invalid()` like Django CBVs.
  `DynamicFormMixin` adds per-field hooks (`get_<field>_queryset/disabled/
  hidden/required`) combined with `@public.watch` on driving fields for
  dependent-field UIs (docs `form-components.md`).
- Files: uploads happen implicitly on the first POST carrying a `File` value;
  the file is stashed in a named temp file server-side (custom upload handler,
  `views.py:22-27`) and survives across calls via the temp-path pickler until
  `submit()` copies it to final storage. Downloads: return a `FileResponse`
  from a public method. Known TODOs in the client: multi-file uploads and
  avoiding re-upload of already-sent files (`tetra.core.js:1870,1878`).
- Websockets: optional, via Django Channels + Redis + ASGI server;
  `ReactiveComponent` with a `subscription` attribute or `get_subscription()`.
  The connection is only opened when a page actually renders a reactive
  component (0.9.1 fix). `ComponentDispatcher.data_changed/notify/
  component_created/component_removed` push to groups from anywhere. Reactive
  Models (0.8.2) auto-broadcast model changes. Echo suppression prevents the
  originating client from double-applying its own update.

## 6. Maintenance status and adoption (as of 2026-07)

- History: created and announced by Sam Willis in May 2022 (Django forum
  thread, 2022-05-24). Releases stalled after 0.0.5 (2022-06); the project
  was dormant until 0.1.x in April 2024, when Christian González (nerdoc,
  nerdocs.at) effectively took over under the tetra-framework org.
- Concentration: 8 contributors ever; nerdoc has 789 of ~826 commits, Sam
  Willis 24. Effectively a one-person project.
- Activity: healthy through early 2026: 0.9.0 2026-02-17, 0.9.2 on PyPI
  2026-03-18, changelog 0.9.3 dated 2026-03-20 (not on PyPI at fetch time),
  last push 2026-03-27. Then a roughly three-month quiet spell to July 2026.
- Adoption: 611 GitHub stars, 23 forks, 32 issues total (3 open), ~1,884
  PyPI downloads/month. Tiny compared to htmx/django-unicorn ecosystems.
- Constraints: requires Python >= 3.12; still 0.x with an explicit "no
  promises about API stability" banner; repeated breaking changes (0.4.0
  rewrote the template tag syntax and renamed `block` to `slot`; 0.9.0 moved
  the endpoint; 0.9.2 stopped saving context by default).
- Quality signals: docs are extensive but drift from code (custom
  `self.client.*` callbacks documented but blocked by the JS whitelist; the
  old tetraframework.com/docs URLs 404; changelog contains the impossible
  date "2026-02-31" for 0.8.2 at `docs/changelog.md:95`). Open issue #91
  (models encode to bare pk for JS, limiting frontend reactivity) is a real
  design seam. Open issue #78 records a serious 2024 discussion between
  nerdoc and Emil Stenström about rebasing Tetra's `BasicComponent` on
  django-components; nerdoc was favorable ("working together is always
  better"), but it has not happened. Directly relevant to citry given its
  django-components lineage.

## 7. What to steal, what to avoid

### Worth stealing (for citry Component.Events)

1. Server methods as plain client methods with declared rate limits. One
   `@public` decorator makes a Python method appear as `this.method(...)` in
   component JS and `@click="method()"` in templates, returning a promise of
   the Python return value; `.debounce/.throttle/.watch` metadata is declared
   once in Python and enforced by generated client wrappers
   (`tetra.core.js:1527-1545`). This is the single best ergonomic idea in
   Tetra and maps cleanly onto a citry Events/RPC surface.
2. One versioned envelope, one endpoint, typed messages. `protocol:
   "tetra-1.0"` on every HTTP and websocket message, `type` discriminators,
   and a `metadata` side-channel (asset urls, messages, callbacks) separate
   from `payload` (result, html). The lazily-injected per-library asset URLs
   in responses solve "component arrived on a page that never loaded its
   JS/CSS", a natural fit for citry's asset compiler.
3. A recorded, whitelisted server-to-client callback queue. `self.client.x()`
   as a recording proxy serialized into the response, executed client-side
   against a closed set of built-ins with prototype-traversal guards
   (`components/callbacks.py`, `tetra.core.js:1741-1768`). Python can drive
   the client (update, dispatch event, push URL, remove node) without any
   eval-like channel. Design it closed-by-default from day one (see mistakes).
4. The data-merge discipline: INIT/MAINTAIN/UPDATE morph modes with old-value
   conflict checks, plus never overwriting the focused input's bound field
   (`tetra.core.js:1179-1198,1212-1236`). These small rules are what make
   server-pushed state feel non-destructive; any citry state-sync story
   should adopt equivalents.
5. Namespaced lifecycle DOM events carrying the component in `detail`
   (`tetra:before-request`, `tetra:component-updated`, ...), plus `_dispatch`
   for bubbling child-to-parent communication. A cheap, framework-neutral
   extension point users already know how to consume.

### Mistakes to avoid

1. Pickling live objects as the client-held state token. It forced an entire
   custom whitelist unpickler, was an RCE-if-key-leaks design for its first
   two years, bloats every request/response, and breaks across deploys and
   restarts (410 storms, dead offline queues). Serialize an explicit,
   declared state shape instead, and version it.
2. Betting the whole client model on one third-party library's internals.
   Tetra is inseparable from Alpine (`x-data`, morph plugin, stores); there is
   no abstraction seam, so Alpine's constraints (single root element, morph
   quirks, store naming) leak straight into the component API and even into
   the wire protocol (`x-data-maintain` attributes).
3. Retrofitting security onto an open callback channel. The
   `callback: ["path", "to", "method"]` traversal API shipped open, then got a
   whitelist that silently broke the documented custom-callback feature. The
   lesson is both "closed by default" and "when you close it, fix the docs".
4. Slow, breaking 0.x drift under a bus factor of one. Four years in, still
   pre-1.0, with syntax-level breaking changes as late as 0.4.0 and protocol
   moves at 0.9.0; combined with a single active maintainer and a Python
   >= 3.12 floor, adoption stayed near zero despite genuinely good ideas.
   Stability promises and upgrade paths are features.
5. Leaking model objects to the client as bare primary keys with no declared
   projection (open issue #91). Decide up front how rich server objects
   project into client state, or every non-trivial reactive UI hits the wall.
