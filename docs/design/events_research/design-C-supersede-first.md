# Component.Events design proposal C: supersede the prior art

Design lens: a user of django-components' `Component.View`, django-unicorn,
Tetra, or livecomponents should read this and conclude that migrating to citry
gets them everything they use today, minus the parts that keep breaking on
them, plus things none of those tools have (compile-time checked bindings,
typed handlers, OpenAPI). The union of their must-haves drives the API; the
parity matrix in section 2 is the requirements document.

Status: proposal for the design-doc track named in
`docs/design/extensions_roadmap.md:62` ("Server-interactive / reactive
components", one extension, one design exploration). This document covers the
`Component.Events` core of that exploration: handler model, client API, wire
protocol, transports, state, security, schema, migration. The Alpine
scoped-slot mechanic named in the same roadmap row is acknowledged in section
13 as a later layer on the same extension; nothing here blocks it.

## 0. Prior art

Everything below is grounded in seven recon reports (this session's
scratchpad: `recon-citry-extensions.md`, `recon-js-runtime.md`,
`recon-old-djc.md`, `recon-unicorn.md`, `recon-tetra.md`,
`recon-livecomponents.md`, `recon-ecosystem.md`,
`undefined/recon-citry-history.md`) and direct verification against source:

- Substrate verified: `Extension` base with `name`/`class_name`/`urls`/`citry`
  (`packages/py/citry/citry/extension.py:359-401`); `URLRoute` /
  `RouteResponse` are sync-handler, content/content_type/status only
  (`packages/py/citry/citry/util/routing.py:36-84`); the ASGI adapter calls
  handlers synchronously with the raw scope and never passes `receive`, so a
  request body is unreachable today
  (`packages/py/citry/citry/contrib/asgi.py:94`); the client runtime's only
  per-instance surface is the `$onComponent` payload `{id, els, data}`
  (`packages/py/citry/citry/extensions/dependencies/client/citry.js:150`) and
  the manager's seven public methods (`citry.js:218-227`).
- Mandate verified: handlers named by the event, each declaring what it
  accepts, a route derived per event, weighing HTTP vs WebSocket
  (`docs/design/extensions_roadmap.md:62`,
  `docs/design/dependencies.md:641-663`).
- Grammar verified: attribute names like `@click` parse as ordinary
  attributes (`crates/citry_template_parser/src/grammar.pest:228,253-255`),
  while bare `c-*` attributes are already the dynamic-expression channel
  (`packages/py/citry/citry/nodes/__init__.py:432-434`), which settles the
  template binding prefix (section 4.1).
- `Kwargs` verified: typed kwargs are constructed with
  `cls.Kwargs(**raw_kwargs)`, no coercion
  (`packages/py/citry/citry/component.py:474-475`).

Nothing named `events` exists in the package; the extension name is free
(duplicate/conflict validation at `extension.py:620-624` per recon).

## 1. The whole loop in one example

A to-do list. Server-rendered, no JavaScript written by the user, two event
handlers, one of them typed and GET-addressable, updates to two components
from one event.

```python
from datetime import date

from citry import Component
from citry.extensions.events import Event, event


class TodoBadge(Component):
    class Kwargs:
        project_id: int

    def template_data(self):
        return {"count": open_todo_count(self.kwargs.project_id)}

    template = """
    <span class="badge">{{ count }}</span>
    """


class TodoList(Component):
    class Kwargs:
        project_id: int
        show: str = "open"

    class Events:
        def add(self, e: Event, text: str, due: date | None = None):
            create_todo(e.props.project_id, text, due)
            # Returning None re-renders this component with the same props.
            # The badge is updated in the same response, addressed by CSS
            # selector, so no second round trip and no client event plumbing.
            return [
                e.render(),
                e.render_other(TodoBadge(project_id=e.props.project_id),
                               target="#todo-badge"),
            ]

        @event(methods=("GET",))
        def filter(self, e: Event, show: str = "open"):
            return e.render(show=show)

    def template_data(self):
        return {"items": todos(self.kwargs.project_id, self.kwargs.show)}

    template = """
    <div>
      <form @submit.prevent="add(text=$value('input[name=text]'))">
        <input name="text" @loading.attr="disabled">
        <button @loading.class="is-busy">Add</button>
      </form>
      <nav>
        <a @click.prevent="filter(show='open')">Open</a>
        <a @click.prevent="filter(show='done')">Done</a>
      </nav>
      <ul>
        <c-for each="item in items">
          <li>{{ item.text }}</li>
        </c-for>
      </ul>
    </div>
    """
```

What the user did not have to do: register a URL, write fetch code, pick an
HTTP verb, add htmx or Alpine, thread a parent id, copy kwargs into a state
class, or configure a Redis store. What they got that no prior-art tool gives
them: `add(text=..., due=...)` is validated and coerced against the Python
signature (a bad `due` is a 422 with a field path, not a 500), the bindings
are checked at component-definition time (a typo in `@click="filte(...)"`
fails at startup with the template location), and `citry ext run events
openapi` documents both endpoints.

## 2. Feature parity matrix

The five columns to beat: django-components `Component.View` (DJC View),
django-unicorn (unicorn), Tetra, livecomponents (LC), and the never-built
djc-ninja idea (typed handlers + OpenAPI, recon-old-djc section 8). The last
column is this design's answer; v1/v1.1/v2 tags match the delivery plan in
section 13.

| Capability | DJC View | unicorn | Tetra | LC | ninja idea | citry Events |
|---|---|---|---|---|---|---|
| Handler declaration | one method per HTTP verb | any public method (opt-out denylist) | `@public` methods | `@command` methods | decorated routes | methods on nested `Events` class; the namespace is the allowlist (v1) |
| Many actions per component | no (query-param multiplexing) | yes | yes | yes | yes | yes, one handler per event, route per event (v1) |
| URL per action | one URL per class | one shared endpoint | one shared endpoint | one shared endpoint | one route per operation | `ext/events/{component}/{event}` per action under one fixed mount (v1) |
| URL builder from Python | `get_component_url(query, fragment, args, kwargs)` | n/a | n/a | `{% call_command %}` tag | `reverse` | `events.url_for(Comp, "event", query=..., fragment=...)` on the mount contract (v1) |
| Typed, coerced args | no (raw `HttpRequest`) | yes (ast-parsed strings + hint coercion) | extended-JSON args, no validation | no (`**kwargs` splat) | yes (pydantic per operation) | yes: JSON args validated/coerced against the signature, 422 with field paths (v1) |
| Access to raw request | yes (Django only) | limited | yes (Django only) | yes (Django only) | yes | `e.request` neutral object + `.native` host escape hatch (v1) |
| HTML re-render response | manual `render_to_response` | automatic full morph | automatic morph | dirty-set OOB morphs | n/a | render ops, morph by default, `None` return re-renders self (v1) |
| JSON return to caller | no | `$returnValue` | promise resolves with return value | no | yes | data op; `await $sendEvent(...)` resolves with it (v1) |
| Update N components per response | no | parent hack | children state sync | yes (dirty set) | no | yes: list of self-addressed render ops (v1) |
| Redirect / URL ops | HTTP redirect | `redirect` field | `_redirect`, `_pushUrl` | `RedirectPage`, `PushUrl`, ... | HTTP redirect | nav ops: redirect, push, replace, refresh (v1) |
| Server-dispatched browser events | no | `self.call` (JS-call list) | `_dispatch` callback | `TriggerEvents` | no | event ops -> `$onEvent` / DOM CustomEvent (v1) |
| Declarative template bindings | no | `unicorn:click` etc | Alpine `@click` | htmx attrs | no | `@click="handler(...)"` compiled and checked at class definition (v1) |
| Binding modifiers | no | prevent/stop/debounce/lazy/defer/... | Alpine's | htmx's | no | prevent, stop, self, once, key filters, debounce-N, throttle-N (v1) |
| Loading / pending states | no | `unicorn:loading` family | request events | htmx indicators | no | `@loading.class/.attr/.show/.hide` + lifecycle DOM events (v1) |
| Dirty states | no | `unicorn:dirty` | no | no | no | dropped (section 11, D7) |
| Polling | no | `unicorn:poll` | no | no | no | `@poll.N="handler"` (v1) |
| State across calls | none | full state through client, 8-char checksum | encrypted pickle token | Redis pickle per page session | none | signed JSON props envelope, full-length HMAC, no object revival (v1); opt-in server store (v2) |
| Exposure model | verbs auto-public | public-by-default | `@public` opt-in | `@command` opt-in | explicit routes | opt-in by construction: only `Events` methods exist on the wire (v1) |
| CSRF | Django's | Django's | Django's | Django's via htmx header | Django's | required custom header + host-token integration per adapter (v1) |
| Auth per handler | manual in method | endpoint-level | manual | opt-in decorator per method | per-route | `auth=` per handler, per component, or one global hook; deny-by-policy in one place (v1) |
| File upload | manual | no (issue backlog) | yes (temp-file staging) | yes | yes | multipart with `Upload` params (v1); staged uploads deferred (section 11, D8) |
| Forms integration | manual | Django forms (`form_class`) | `FormComponent` | manual | pydantic | error op carries field errors; `ValidationError` mapping (v1); `FormEvents` helper (v2) |
| WebSocket / push | no | no | yes (Channels) | no | no | deferred to v2 with a concrete design (section 8); `@poll` in v1 |
| OpenAPI / schema | no | no | no | no | yes (the whole point) | yes: per-event operations from signatures, CLI command (v1), served endpoint + client manifest (v1.1) |
| Host frameworks | Django only | Django only | Django only | Django only | Django only | Django, FastAPI, Flask, Starlette, plain ASGI/WSGI (v1) |
| Client prerequisites | user-supplied (htmx etc) | own JS lib | Alpine + own lib | htmx + 2 extensions + Alpine + morph + config | n/a | one owned runtime file, zero third-party (v1) |
| Compile-time template checks | no | no (runtime breakage catalog) | no | no | n/a | binding targets, arg names, arg literals checked at class definition (v1) |

Two rows in that table are capabilities nobody in the comparison set has
(compile-time checked bindings; OpenAPI from event handlers). Those are the
migration argument, not just parity.

## 3. The Python API

### 3.1 Declaring handlers

`Events` is a nested class on the component, following the established
extension config pattern (synthesized as
`type("Events", (user_cls, GlobalDefaults, ext.Config), ...)`,
`extension.py:777-803` per recon). A handler is any callable defined directly
in the user's `Events` class body whose name does not start with `_`. There
is no decorator requirement to become a handler; putting the method in the
`Events` namespace is the explicit opt-in (LiveView's model: an event exists
only if you wrote it). The `@event(...)` decorator exists only to attach
per-handler configuration.

The extension captures the user's raw nested class in
`on_component_class_created` (before the config rebuild replaces it), exactly
the way the dependencies extension captures `Dependencies`
(`extensions/dependencies/__init__.py:187-192` per recon). At that moment it:

1. Enumerates handlers and builds each handler's argument model from the
   signature (section 3.3).
2. Validates handler names (must be valid URL path segments; collisions with
   reserved names rejected).
3. Compiles and validates the component template's `@...` bindings against
   the handler set (section 4.1). Errors raise at class definition, naming
   the template location.

### 3.2 The Event context

Every handler receives the config instance as `self` and an `Event` as the
first positional argument. Handlers run outside a render lifecycle, so the
config is instantiated with `component=None` (the supported out-of-lifecycle
case, `extension.py:331-346` per recon); everything a handler needs is on the
`Event`.

```python
@dataclass(frozen=True, slots=True)
class Event:
    citry: Citry                    # the engine instance
    component_class: type[Component]
    name: str                       # the event name ("add")
    instance_id: str | None         # the DOM instance that fired it, if any
    props: Any                      # verified round-tripped kwargs
                                    # (Kwargs dataclass instance when declared,
                                    # else a plain dict); None when the call
                                    # carried no props envelope
    args: dict[str, Any]            # validated+coerced args (also bound to
                                    # the handler's parameters)
    request: Request                # framework-neutral request (section 12)
```

`event.request` is the escape hatch the brief requires: `Request` exposes
`method`, `path`, `headers`, `query`, `cookies`, `body` (bytes), `form`,
`files`, and `native`, where `native` is the untouched host object (Django
`HttpRequest`, ASGI scope, WSGI environ). Handlers that need host-specific
behavior reach through `native` and accept the portability cost knowingly.

`Event` also carries the response-building helpers:

```python
e.render(**prop_overrides)        # re-render this component; overrides merge
                                  # into the verified props
e.render_other(element, target="#css-selector", mode="morph")
                                  # server-render any component/element into
                                  # an explicit target
e.dispatch(name, detail=None, scope="component")   # browser event op
e.redirect(url) / e.push_url(url) / e.replace_url(url) / e.refresh()
e.fail(message, fields=None, status=422)           # raise a typed error
```

### 3.3 Typed args, coercion, validation

At class definition the extension builds an argument model per handler from
the signature, the way django-ninja builds one per operation (recon-ecosystem
axis 5). Parameters after `e: Event` are event args. Sources:

- POST/PUT/... : the JSON body's `args` object (or multipart, section 5).
- GET (when the handler allows it): query parameters.

Coercion rules, in order of preference:

1. If pydantic is installed, a `TypeAdapter` per parameter (the realized
   precedent is the old repo's `PydanticExtension`, recon-old-djc section 7).
2. Otherwise a built-in coercer covering JSON primitives plus `datetime`,
   `date`, `time`, `UUID`, `Decimal`, `Enum` (by value), `Optional`, `list`,
   `dict`, and dataclass parameters constructed from objects. This is
   unicorn's best idea (hint-driven coercion) without its transport (no
   ast-parsed call strings; the wire carries structured JSON only).

What is deliberately NOT coerced: ORM models by primary key. Livewire's model
binding turned an argument into an unauthorized database fetch and unicorn's
`Model.objects.get(pk=...)` has the same footgun; the handler fetches and
authorizes explicitly. This is a documented drop (section 11, D1).

Failure produces a 422 error op with per-field paths
(`{"fields": {"due": "invalid date"}}`), never a host 500. Extra keys are
rejected (mirroring `Kwargs(**raw)` strictness, `component.py:474`).

Uploads: a parameter annotated `Upload` (or `list[Upload]`) accepts a
multipart file part; `Upload` is a small neutral object (`filename`,
`content_type`, `size`, `read()`, `save(path)`).

### 3.4 What handlers return

The return value maps onto the wire ops (section 5). The full contract:

| Return | Meaning |
|---|---|
| `None` | re-render self with the verified props (the default; side effects on the database show up because `template_data` runs again) |
| `Op` or `list[Op]` | exactly those ops, in order |
| a `CitryElement` (e.g. `ThankYou(name=n)`) | render op replacing this instance's content with that element's output (the DJC form_submission pattern, one line) |
| JSON-safe value (dict, list, str, int, float, bool) | data op; the client promise resolves with it, no DOM change |
| `Raw(content, content_type, status=200, headers=())` | bypass the protocol entirely (file downloads, custom payloads); the client hands non-protocol responses to the download/navigation path |

Ops constructors are module-level too (`render`, `dispatch`, `redirect`,
...) so handlers can build responses without the context object when that
reads better.

Ambiguity rule: a returned dict is always a data op. To re-render with new
props, use `e.render(...)`; to target another component, `e.render_other`.
No guessing.

### 3.5 Error handling

- Unknown component or event: 404 error op.
- HTTP method not allowed for the handler: 405.
- Missing/invalid props signature: 409 with code `stale`; the client
  dispatches `citry:events:stale` on the instance roots (default UI action:
  none; documented recovery is a reload prompt, but unlike livecomponents'
  hard 410 the page keeps working for other components).
- Arg validation: 422 with field paths.
- Auth: 401/403 (section 7).
- Handler exception: the extension catches it, fires its own
  `on_event_error` emit hook (subscribers may replace the response, e.g. a
  Sentry extension or a custom error page), then defaults to a 500 error op
  with a generic message; the traceback rides only when `citry.debug` is on.
  Adapters never see the exception, closing the "TypeError becomes host 500"
  gap (recon-citry-extensions gap 8).

The HTTP status always mirrors the first error op, so plain HTTP tooling
(curl, monitoring) reads correctly, while the body stays protocol-shaped.

### 3.6 Per-handler and per-component config

Per-component config: plain class attributes on `Events`, resolved through
the standard three-level defaults (component > `extensions_defaults["events"]`
> factory defaults), which the substrate already provides.

```python
class Events:
    methods = ("POST",)          # default for handlers without @event
    auth = None                  # callable(Event) -> None, raises/returns error
    csrf = "auto"                # "auto" | "host" | "header" | "off"
    props = "signed"             # "signed" | "off"
    props_fields = None          # tuple of kwarg names to include, None = all
    props_max_bytes = 8192
    debounce = None              # default client debounce (ms) for bindings
```

Per-handler config via the decorator, overriding the class values:

```python
@event(methods=("GET",), auth=staff_only, debounce=300, name="search")
def search_items(self, e: Event, query: str = ""): ...
```

`name=` decouples the wire name from the Python name (rename server
internals without touching templates). `throttle=` mirrors `debounce=`.
Booleans and flags follow the house rule (positive actions).

### 3.7 URLs and the URL builder

One fixed dispatch route tree, registered via `Extension.urls`:

```
POST|GET  ext/events/{component}/{event}     the dispatch endpoint
POST|GET  ext/events/{component}             View-compat verb dispatch (3.8)
GET       ext/events/runtime.js              the events client runtime
GET       ext/events/openapi.json            optional, config-gated (v1.1)
```

`{component}` is the registered component name (kebab form; `Citry.get` is
case-insensitive per recon), `{event}` the handler's wire name. Fixed
patterns with path params survive Django's snapshot-at-`urlpatterns()` model
(recon-citry-extensions gap 5); ASGI/WSGI match live tables anyway. Only
registered components are addressable: registration is part of the exposure
story.

URL building goes through the mount contract
(`Citry.build_url`, `set_mounted_prefix`; `dependencies.md` 9.3):

```python
from citry.extensions.events import url_for

url_for(citry, TodoList, "filter", query={"show": "done"}, fragment="top")
# -> /citry/ext/events/todo-list/filter?show=done#top
```

This is the `get_component_url` return promised in
`migration_djc.md:1100`, and the first caller of the ported `format_url`
(`migration_djc.md:859`). Building without a mounted prefix raises with
guidance, same as fragments.

### 3.8 The View compat shim

For DJC `Component.View` users, a drop-in verb adapter, implemented as ~40
lines on top of Events (reserved handler names + one extra route):

```python
from citry.extensions.events.compat import ViewEvents

class ProfileCard(Component):
    class Events(ViewEvents):
        def get(self, e: Event):
            return e.render()

        def post(self, e: Event):
            name = e.request.form.get("name", "stranger")
            return ThankYou(name=name)
```

Requests to `ext/events/profile-card` (no event segment) dispatch by HTTP
method to the same-named handler; `url_for(citry, ProfileCard)` returns that
URL. The old `form_submission` example ports with the handler body unchanged.
The shim is a bridge, not the recommended shape; its docstring says to name
events after actions once there is more than one mutation.

### 3.9 Extension-owned hooks

Following the emit() convention (`extensions.md:313-319` per recon), Events
owns duck-typed hooks other extensions can implement, and adds no core hooks:

- `on_event(ctx)`: before dispatch (observability, rate limiting).
- `on_event_auth(ctx)`: contribute to the authorization decision.
- `on_event_result(ctx)`: map/extend the ops list (threaded, `result="map"`).
- `on_event_error(ctx)`: replace the error response.

## 4. The client JS API

One runtime file (`citry-events.js`, plain JS in v1, moving to
`packages/js/citry-client` TypeScript with the existing runtime per
`dependencies.md:509-515`). Zero third-party dependencies; DOM morphing uses
a vendored idiomorph (MIT, ~4 KB min) inside the bundle, with `replace` as
the no-morph fallback mode. Delivered through the dependencies pipeline: the
extension appends a `Script` for `ext/events/runtime.js` via the
`on_dependencies` hook whenever a rendered component has handlers or
bindings, so documents and fragments both load and dedupe it through the
existing manifest machinery (recon-js-runtime seam 3).

### 4.1 Declarative template bindings

Binding prefix decision: `@`, not `c-`. Verified: bare `c-*` attributes are
already the dynamic Python-expression channel
(`nodes/__init__.py:432-434`), so `c-on:click` would be evaluated as Python;
`@click` parses as an ordinary attribute (`grammar.pest:228`) and matches
both Vue and the maintainer's own DJC-era sketch
(`@updateItemsCount="handleItemsCount"`, recon-old-djc section 5). No grammar
or compiler change is needed, so this stays out of CLAUDE.md's high-risk
areas.

```html
<button @click="add(text='hi')">Add</button>
<input  @input.debounce-300="filter(show=$value)">
<form   @submit.prevent="save()">
<div    @poll-5000="refresh_stats()">
```

Grammar of the value: `handler` or `handler(key=literal, ...)`. Literals are
JSON literals plus single-quoted strings; specials are `$value`, `$checked`,
`$key` (resolved client-side from the triggering element/event, no
expression evaluation), and `$value('css selector')` reading a sibling
field's value. Args are keyword-only, matching the Kwargs culture.

Modifiers: `.prevent`, `.stop`, `.self`, `.once`, `.debounce-N`,
`.throttle-N`, key filters for keyboard events (`.enter`, `.escape`, `.tab`,
`.ctrl`, `.shift`, `.meta`). Loading vocabulary (unicorn's, trimmed):
`@loading.class="x"`, `@loading.attr="disabled"`, `@loading.show`,
`@loading.hide`, optional `.for-handlerName` scoping. Polling:
`@poll-N="handler"` (pauses on hidden tabs).

How it works: at template load (`on_template_loaded`, string level, before
parse and caching) the extension rewrites each recognized binding into a
`data-cev-*` attribute whose value is a base64 JSON spec: owner `class_id`,
handler wire name, static args, specials, modifiers, merged per-handler
debounce config. The client runtime installs one delegated listener per
event type and, at event time, walks up from the target to the nearest
element with a `data-cev-*` binding, resolves the owning instance from the
nearest `data-cid-*` marker consistent with the spec's `class_id` (this
matters when a child component's root is nested inside the parent's DOM),
and sends. The client never parses author expressions; the spec is data.

Recognition rule (Alpine coexistence): an `@x="..."` attribute is a binding
only when its value matches the grammar above AND names a declared handler
of the component whose template it sits in. Anything else passes through to
HTML untouched, so `@click="open = !open"` still belongs to Alpine. A
recognized-but-wrong binding (right handler, bad arg name, bad literal) is a
class-definition error with the template location; that compile-time check
is the citry differentiator over every runtime-scanned prior art.

Known v1 caveat, stated honestly: the load-time rewrite is textual and can
match binding-shaped text inside `<c-raw>` blocks or attribute values, the
same class of caveat the shipped `$onComponent` substring rewrite already
has (recon-js-runtime section 1). The refinement path is a node-level
transform in `on_template_compiled`; the authored syntax and the emitted
`data-cev-*` contract do not change when that lands.

### 4.2 The $ magic family

Same family and delivery mechanism as `$onComponent`: textual rewrites
applied in the extension's own `on_js_loaded` hook (which runs before the
dependencies cache/rewrite, so no coupling to that code path;
recon-js-runtime seam 2). Both work whether the JS is inlined (IIFE-wrapped)
or cache-served (raw), since the rewrite is scope-independent.

- `$sendEvent(name, args?, opts?)` rewrites to
  `Citry.events.send("<class_id>", name, args, opts)`. Returns a promise
  that resolves with the data op's value (or `undefined`), and rejects with
  a typed error (`{status, code, message, fields}`). Instance resolution:
  `opts.id` wins; otherwise, if exactly one live instance of the class is on
  the page, it is used; otherwise the promise rejects with guidance to use
  the instance-scoped API. This rule keeps the magic honest for list-rendered
  components instead of silently picking one.
- `$onEvent(name, fn)` rewrites to `Citry.events.on("<class_id>", name, fn)`
  and returns an unsubscribe function (the DJC todo.py sketch's `$on`
  contract). `fn(detail, {id, els})` fires when a server event op with
  component scope targets an instance of this class.

Instance-scoped API, for precision: the `$onComponent` payload gains one
property (the payload object at `citry.js:150` is the designed extension
point):

```js
$onComponent(({ id, els, data, events }) => {
  els[0].querySelector(".more").addEventListener("click", async () => {
    const page = await events.send("load_more", { after: data.cursor });
    renderExtra(page);           // data-op path: JSON in, author renders
  });
  const off = events.on("todo:added", (detail) => flash(detail.text));
});
```

`events.send` / `events.on` are pre-bound to that instance. Server-dispatched
events with `scope: "document"` additionally fire as real DOM CustomEvents
(`citry:<name>` on `document`), so non-citry code can listen too.

Lifecycle honesty: the runtime keeps an instance registry (id -> class,
envelope, roots) fed by the props envelopes in delivered HTML; entries are
dropped lazily when no `data-cid-<id>` element remains (checked on send and
on a periodic observer sweep). There is no full unmount lifecycle in v1;
that matches the existing runtime's model and is listed as a v2 item.

### 4.3 Multi-component updates

One response, many self-addressed operations (the Turbo/OOB convergence,
recon-ecosystem axis 2c). A handler updates other components by
server-rendering them into explicit targets (`e.render_other(...)`), never by
asking the client to make follow-up requests (Livewire's extra round trip).
For "tell interested components something happened without rendering them",
the event op + `$onEvent` covers it. The dirty-set idea from livecomponents
survives as "the ops list", without the manual parent-id plumbing.

### 4.4 Optimistic UI and pending states

Following the field's convergence (recon-ecosystem, "pending state, not
predicted state"): no rollback machinery. What exists:

- `@loading.*` attributes (4.1) on the trigger and any element.
- Instance roots get a `citry-ev-pending` class while a call is in flight.
- Lifecycle DOM CustomEvents on the instance roots:
  `citry:events:start|success|error|finish` with `{name, args}` detail.
- `events.send` returns a promise, so genuinely optimistic behavior (mutate
  locally, reconcile on response) lives in the component's own JS, where it
  belongs.

## 5. The wire protocol

Language-neutral by construction: the same protocol serves the planned
JS/PHP/Go hosts, so nothing in it is Python-shaped. Names are lowerCamel,
times are ISO-8601 strings, errors are stable string codes (never exception
class names, which Tetra leaks), and the arg object's keys are whatever the
handler declared (hosts keep their own naming conventions).

Media type `application/json`; every message carries `protocol: 1` (integer;
bump on breaking change, additive fields do not bump). Endpoint accepts only
requests with the `X-Citry-Events: 1` header (section 7).

Request (`POST /citry/ext/events/todo-list/add`):

```json
{
  "protocol": 1,
  "calls": [
    {
      "component": "todo-list",
      "event": "add",
      "instance": "c1A2b3c",
      "props": {
        "v": 1,
        "c": "todo-list",
        "p": { "project_id": 7, "show": "open" },
        "t": "2026-07-04T12:00:00Z",
        "sig": "hex-hmac-sha256"
      },
      "args": { "text": "buy milk", "due": "2026-07-10" }
    }
  ]
}
```

`calls` is an array so batching is a client-runtime feature, not a protocol
change (the v1 client sends one call; v1.1 coalesces same-tick calls; the
URL of a batched request is the first call's, and the server routes each
call by its own `component`/`event` fields). GET calls carry `args` as query
parameters and `props` as a base64 query parameter; GET handlers are for
idempotent reads and are what makes an event URL pasteable into HTMX or a
plain link.

Multipart variant: when args include files, the client sends
`multipart/form-data` with the JSON envelope in a `payload` field and files
as parts named `file:<argName>` (Tetra's proven shape).

Response:

```json
{
  "protocol": 1,
  "results": [
    {
      "ops": [
        { "op": "render", "target": { "instance": "c1A2b3c" },
          "mode": "morph", "html": "<div data-cid-c1A2b3c ...>...</div>",
          "assets": { "markLoaded": {}, "fetch": {"js": [], "css": []}, "calls": [] } },
        { "op": "render", "target": { "selector": "#todo-badge" },
          "mode": "morph", "html": "<span ...>3</span>", "assets": null },
        { "op": "event", "name": "todo:added",
          "detail": { "text": "buy milk" }, "scope": "component" },
        { "op": "data", "value": { "id": 42 } },
        { "op": "nav", "kind": "push", "url": "/todos?show=open" },
        { "op": "error", "status": 422, "code": "validation",
          "message": "invalid args", "fields": { "due": "invalid date" } }
      ]
    }
  ]
}
```

How HTML and JSON coexist: they are just different ops in one ordered list.
A response may morph two components, resolve the caller's promise with JSON,
and fire a named event, in one round trip. `results` is index-aligned with
`calls`.

The `assets` field of a render op is exactly the dependencies manifest
object the fragment serializer already produces (markLoaded/fetch/calls,
base64-armored fields; recon-js-runtime section 3), so a rendered component
that brings new JS/CSS activates through the existing manager, not a second
mechanism. The runtime processes `assets` via
`Citry.manager._loadComponentScripts` before morphing the HTML in.

Refreshed props ride inside the re-rendered HTML itself: each instance's
root element carries `data-cev="<base64 envelope>"` (stamped by the
extension at serialize time through the root-marker mechanism the
dependencies extension already uses for `data-ccss-*`). Morphing the new
HTML in therefore updates the envelope automatically; no separate props op,
and fragments delivered by any means stay self-contained.

Non-protocol responses: if the response is not protocol JSON (a `Raw` return,
e.g. a CSV download with `Content-Disposition: attachment`), the client
detects it and routes it to the browser's download/navigation path.

## 6. Transports

### 6.1 The shared core

All transports call one Python entry point; this is the pluggability seam on
the server:

```python
def dispatch(citry, *, component: str, event: str, instance: str | None,
             props: dict | None, args: dict, request: Request) -> EventResult
# EventResult = ops list + status; transports only translate framing.
```

HTTP handlers, the future WebSocket consumer, and any custom mount (a
GraphQL mutation resolver, a JSON-RPC method) are thin wrappers over
`dispatch`. The protocol section 5 shapes are the framing; `dispatch` is the
semantics. That split is what "pluggable transports" concretely means here.

Client side, symmetric seam:

```js
Citry.events.transports = {
  http: { send(call) -> Promise<result> },          // v1, default
  // ws:  { send(call), subscribe(topics, onOps) }, // v2
};
Citry.events.use("ws", { fallback: "http" });
```

The runtime picks a transport per call; ops handling is transport-agnostic
because the response shape is identical everywhere (the Turbo lesson: push
is an additive transport when the payload does not change).

### 6.2 HTTP (v1)

Works on WSGI and ASGI alike, which is why it is the v1 transport (the
ecosystem trend since ~2024 is away from WS-required designs). Concretely:
the dispatch route registered via `Extension.urls`, handlers sync, bodies
size-capped (default 1 MB, config), responses one-shot JSON. Requires the
substrate work in section 12 (neutral `Request` with a body; today the ASGI
adapter cannot deliver one, `contrib/asgi.py:94`).

### 6.3 WebSocket (v2, designed now so v1 does not paint over it)

- One socket per page, `ext/events/ws`, multiplexed; never per component
  (unanimous in the field).
- Frames are the section 5 shapes plus a `type` discriminator:
  `{"type": "call", ...}` up, `{"type": "result", ...}` and
  `{"type": "push", "ops": [...]}` down, plus ping/pong.
- Requires ASGI; the adapter surface grows a WebSocket handler protocol next
  to `URLRoute` (Django needs Channels; documented as optional).
- Reconnect is a re-subscribe, not a resume (LiveView lesson); in-flight
  calls reject and the page keeps working over HTTP.
- The client uses WS when connected, HTTP otherwise; per-call override via
  `opts.transport`.

### 6.4 SSE (considered, not built)

The ops-list response format is already SSE-friendly (one op or one result
per frame), so a streaming down-channel needs no protocol change. Not
scheduled; recorded so the door stays open (Datastar precedent).

## 7. State model and security

### 7.1 What round-trips: the signed props envelope

Citry components are stateless render units; the server needs a component's
inputs back to re-render it. Chosen model: 4a-lite from the ecosystem recon.
At serialize time, for each rendered instance whose class has handlers, the
extension captures the instance's `raw_kwargs`, requires them JSON-safe
(loud error at render time listing offending keys, per the livecomponents
lesson: never an honor-system contract), canonicalizes, signs, and stamps
the envelope on the root element (`data-cev`):

```
envelope = { v, c (component name), p (props), t (issued-at), sig }
sig = HMAC-SHA256(secret, canonical_json({v, c, p, t}))    # full length
```

On dispatch, the signature is verified before anything else; `e.props` is
the verified object, reconstructed through `Kwargs(**p)` when the component
declares typed kwargs. Rules, each closing a named prior-art hole:

- Full-length MAC over the whole envelope including the component name
  (unicorn: 8-char checksum over `str(data)` only).
- Props are data, never revived objects; no pickle anywhere (unicorn cache
  RCE warning, Tetra's whitelist unpickler, livecomponents' Redis pickle).
  A component whose kwargs are not JSON-safe either narrows them
  (`props_fields`), passes ids and refetches in `template_data`, or turns
  props off (`props = "off"`, handlers then work URL-only).
- Size-capped (`props_max_bytes`, default 8 KB) with a render-time error,
  not silent truncation. The cap is a canary: components that trip it are
  holding state that belongs in the database.
- Visible by design: props are signed, not encrypted; the docs say plainly
  that kwargs of an events-enabled component are user-visible page data,
  same as anything rendered into HTML. (Tetra's encrypted tokens hide state
  but bought that with Fernet key management and deploy-invalidation
  storms.)
- Optional `t`-based expiry (config, default off). Expired or tampered
  envelopes give the 409 stale path, which degrades per component, not per
  page.

Secret: `EventsExtension(secret=...)` or
`extensions_defaults["events"]["secret"]`; the Django adapter documentation
shows passing `settings.SECRET_KEY`. First signed render without a secret
raises with guidance (the house explicit-error pattern,
`dependencies.md:521-532`).

Server-held state is deliberately not in v1: it forces the socket/process
model or a shared store, and every prior-art system that led with it grew
the worst failure modes (410 storms, cache 500s). v2 adds an opt-in
`props = "server"` mode (envelope replaced by an opaque key into a pluggable
store with TTL + soft-delete GC, memory store for tests, livecomponents'
good half) for components whose inputs are genuinely large.

### 7.2 Method exposure

Only methods on the `Events` class exist on the wire; nothing else on the
component is reachable, there are no property setters over the wire, no
dotted paths, no callable-string parsing. This is the inverse of unicorn's
public-by-default `_is_public` denylist, and it removes the class-pollution
attack surface (CVE-2025-24370) by construction rather than by filter.

### 7.3 CSRF

Layered, per adapter reality:

1. Always: the dispatch endpoint rejects requests without the
   `X-Citry-Events: 1` header. A custom header cannot be attached by HTML
   form submission and forces a CORS preflight cross-origin, which blocks
   classic CSRF on every host framework with zero configuration.
2. Host token integration (`csrf = "host"` or `"auto"`): config carries a
   cookie->header mapping (Django default: `csrftoken` ->
   `X-CSRFToken`); the client mirrors it, and under the Django adapter the
   request passes through Django's own CSRF middleware untouched (the
   dispatch view is not exempted). Under FastAPI/Flask, where no CSRF
   middleware exists by default, mode `"auto"` resolves to header-only.
3. The props signature independently prevents cross-site forging of
   meaningful re-renders even where 1 and 2 are misconfigured.

### 7.4 Auth

- `auth=` per handler or per component: a callable receiving the `Event`;
  raise `e.fail(status=403)` or return an error op to deny. Sync, boring,
  testable.
- One global policy point: the `on_event_auth` emit hook, so an app enforces
  "every event requires an authenticated user unless marked public" in one
  place instead of livecomponents' per-method decorator memory game.
- What is NOT promised: automatic "inherit the page's auth". Citry cannot
  know host middleware semantics framework-neutrally; pretending otherwise
  is how tools ship auth bypasses. The docs lead with the global-hook recipe
  per adapter (Django: check `request.native.user`; FastAPI: verify the
  session/token dependency equivalent).

## 8. Server push

Deferred to v2, explicitly, with the design fixed enough that v1 cannot
contradict it:

- Transport: the 6.3 WebSocket; one socket per page.
- Subscription: a component declares topics
  (`Events.topics = ("project:{project_id}",)` formatted from props at
  render time); the serializer stamps signed topic names into the envelope
  (Turbo's signed stream names), and the client subscribes on connect. A
  client cannot subscribe to a topic it was not handed.
- Server API: `citry.get_extension("events").push(topic, *ops)` from
  anywhere (a view, a task queue); the payload is the same ops array as an
  HTTP response, so a push can morph components, fire `$onEvent` handlers,
  or navigate.
- What v1 ships instead: `@poll-N="handler"` bindings (visibility-aware),
  which covers dashboards and progress bars at zero infrastructure cost, and
  keeps parity with unicorn's most-used push substitute.

Reasoning for the deferral, honestly: WS multiplies the deployment story
(ASGI-only, Channels on Django, sticky reconnect questions) and none of the
four migration sources except Tetra's `ReactiveComponent` users lose
anything in v1. The trend evidence (Datastar, Turbo demoting WS, LiveView's
longpoll pain) says HTTP-first is not a compromise position.

## 9. OpenAPI and schema generation

The argument models from 3.3 are the single source of truth, django-ninja
style:

- `citry ext run events openapi [--out openapi.json]` (an
  `ExtensionCommand`; the CLI substrate is complete per recon) walks
  registered components, and emits one operation per handler:
  path `ext/events/{component}/{event}`, method(s) from config,
  `operationId = "<ComponentName>.<event>"`, request schema from the arg
  model (query params for GET), response schema = the protocol envelope with
  the data op's `value` typed from the handler's return annotation, error
  responses 401/403/404/405/409/422 predeclared. Handler docstrings become
  operation descriptions (they are already API-reference quality per the
  house docstring rule).
- v1.1: the same document served at `ext/events/openapi.json` when enabled
  (`EventsExtension(openapi=True)`), and a machine-readable client manifest
  (event names + arg shapes per component) exposed through the component
  introspection API (issue #26) for the planned Storybook command and future
  TypeScript codegen.
- Scope honesty: render ops are HTML-bearing and OpenAPI describes them only
  as the envelope schema; the schema story is at its best for data-op
  handlers, which is exactly the djc-ninja use case (typed component-scoped
  JSON endpoints) that never got built upstream (recon-old-djc section 8).

No surveyed interactive framework generates schemas for its events
(recon-ecosystem axis 5); this section is a differentiator, not parity.

## 10. Migration stories

### 10.1 From django-components Component.View

Before (DJC):

```python
class ContactForm(Component):
    class View:
        def post(self, request):
            name = request.POST.get("name", "stranger")
            return ThankYou.render_to_response(kwargs={"name": name})

# template: <form hx-post="{{ submit_url }}" ...> plus {% csrf_token %},
# submit_url minted with get_component_url(ContactForm)
```

After (citry), two options. Verb-for-verb with the shim (section 3.8), or
the idiomatic form:

```python
class ContactForm(Component):
    class Events:
        def submit(self, e: Event, name: str = "stranger"):
            return ThankYou(name=name)

    template = """
    <form @submit.prevent="submit(name=$value('input[name=name]'))">
      <input name="name">
      <button @loading.attr="disabled">Send</button>
    </form>
    """
```

Gone: urlpatterns, htmx, hand-minted URL, query-param multiplexing when a
second action appears (it just becomes a second handler). The
`?type=alpine|js|htmx` dispatch in DJC's fragments example becomes three GET
handlers. `get_component_url` callers switch to `url_for` (same
capabilities: query, fragment; route params are the component/event
segments).

### 10.2 From django-unicorn

Before:

```python
class SearchView(UnicornView):
    query = ""
    results = []

    def updated_query(self, value):
        self.results = search(value)

# template: <input unicorn:model.debounce-300="query">
```

After:

```python
class Search(Component):
    class Kwargs:
        query: str = ""

    class Events:
        @event(methods=("GET",))
        def set_query(self, e: Event, query: str = ""):
            return e.render(query=query)

    def template_data(self):
        return {"results": search(self.kwargs.query)}

    template = """
    <div>
      <input value="{{ query }}" @input.debounce-300="set_query(query=$value)">
      <ul><li c-for="r in results">{{ r }}</li></ul>
    </div>
    """
```

The mental shift: no mutable server-side attribute bag; the component's
props plus the database are the state, and a handler's job is to compute the
next props. What unicorn users keep: the attribute+modifier grammar (near
verbatim), hint-driven coercion, loading states, polling, morphing that
preserves focus. What they gain: no full-state payload on every keystroke,
no `javascript_exclude` hygiene, no checksum-vs-CVE story, compile-time
binding checks instead of the silently-cleared-input runtime failures their
docs catalog. What they lose is listed in section 11 (D2, D5, D7).

### 10.3 From Tetra

Before: `count = public(0)`, `@public def increment(self): self.count += 1`,
encrypted pickle token in `x-data`, Alpine required.

After:

```python
class Counter(Component):
    class Kwargs:
        count: int = 0

    class Events:
        def increment(self, e: Event, by: int = 1):
            return e.render(count=e.props.count + by)

    template = """
    <div>
      <span>{{ count }}</span>
      <button @click="increment(by=1)">+</button>
    </div>
    """
    js = """
    $onComponent(({ events }) => {
      // Tetra's `await this.method()` becomes:
      // const n = await events.send("increment", { by: 10 });
    });
    """
```

Kept from Tetra: server methods callable from JS returning promises of the
return value (their best idea), the versioned envelope, debounce/throttle
declared once in Python, the asset side-channel on responses. Dropped:
pickled live state (their whitelist unpickler and 410 storms are the
argument), Alpine as a hard dependency, the open `self.client.*` callback
channel (replaced by dispatch events; Tetra itself retreated to a nine-item
whitelist). Tetra's `ReactiveComponent` users wait for v2 push and keep
`@poll` meanwhile.

### 10.4 From livecomponents

Before: Pydantic state class + `init_state` mirroring kwargs by hand,
`@command def increment(self, call_context, value)`, Redis + pickle,
`hx-post='{% call_command root_id "increment" %}'` with hand-threaded
`parent_id`, five-library client stack.

After: kwargs ARE the state contract (captured and signed automatically;
forgetting a field is impossible by construction), a command is an `Events`
handler, the execution-results algebra maps one-to-one onto ops
(`ComponentDirty` -> `e.render()`, `ComponentDirty(other)` ->
`e.render_other`, `RedirectPage`/`PushUrl` -> nav ops, `TriggerEvents` ->
dispatch), the client stack is one file, and there is no Redis in
development. Cross-component command chaining (`ctx.parent.cmd(...)`)
becomes either a direct `render_other` or a dispatched event the parent's
JS or a follow-up handler consumes; the shared-dirty-set fluency is the one
real regression, listed in section 11 (D5).

### 10.5 The Component.Ninja idea

The intention "typed component endpoints + OpenAPI" ships as a property of
every handler rather than a separate integration: data-op handlers with
typed args and typed returns, per-operation paths, 422 semantics, and the
generated document (section 9) are exactly the djc-ninja feature set, without
a second routing layer or a pydantic hard dependency.

## 11. Dropped prior-art features, and why users will accept

- D1. ORM-model argument revival (unicorn's pk fetch, Livewire model
  binding). Dropped for the authorization footgun and the RCE lineage of
  rich rehydration. Acceptance: one explicit fetch line in the handler,
  which most teams' review guidelines wanted anyway.
- D2. Mutable server-state attribute bag with automatic diffing (unicorn
  `data`, Tetra private attrs). Dropped: it is where the payload bloat, the
  leak-by-default, and both unicorn CVEs live. Acceptance: props + database
  express the same apps with less magic; the envelope cap tells you when
  you are fighting the model.
- D3. Property setters and call expressions over the wire
  (`unicorn:click="name='Bob'"`, ast-parsed strings). Dropped: executable
  wire formats are unauditable. Acceptance: a one-line handler per setter,
  which is also where validation was supposed to happen.
- D4. Arbitrary server-to-client callback invocation (Tetra
  `self.client.*`). Dropped: an eval-shaped channel that Tetra itself had to
  whitelist down, breaking its docs. Acceptance: dispatch events cover the
  legitimate uses (the component's own JS decides what runs).
- D5. Automatic component hierarchy state plumbing (`$parent`,
  livecomponents path ids and shared dirty sets, Tetra `children_state`).
  Deferred, not rejected: v1 covers the cases with `render_other`, targets,
  and events; automatic instance topology needs the introspection API and
  is v2+ ground. Acceptance: livecomponents' own recommended pattern (one
  stateful root, stateless children) translates directly and loses nothing.
- D6. Offline call queue with rollback (Tetra). Dropped: high complexity,
  tiny audience, breaks across deploys even in Tetra. Acceptance: the
  promise-based send makes app-level retry trivial where it matters.
- D7. Dirty-input tracking (`unicorn:dirty`). Dropped from v1 for scope;
  the lifecycle DOM events make it buildable in userland CSS/JS in a few
  lines. Revisit on demand.
- D8. Staged multi-request file uploads (Tetra temp-file staging). v1 does
  single-request multipart only. Acceptance: covers forms and imports; a
  staging story can layer on later without protocol changes.
- D9. Pickled/persistent per-page sessions (livecomponents). Dropped
  entirely; the v2 server props store is schema'd and optional, never
  pickle, never required.

## 12. Substrate changes required (the honest cost list)

Ordered; each is a small standalone PR against existing seams, none touches
the Rust contract (no grammar/AST/compiler/LangImpl/PyO3 changes, so
CLAUDE.md Mechanisms 2/4 are not triggered by v1):

1. Neutral `Request` object (`citry/util/request.py`) and adapter
   population. ASGI adapter buffers the body for http scopes (size-capped)
   before invoking sync handlers; WSGI reads `wsgi.input`; Django wraps
   `HttpRequest`. Existing handlers never read `request`
   (`routing.py:12-14`), so passing the wrapper instead of the raw host
   object is behavior-compatible; `.native` preserves the escape hatch.
2. `RouteResponse.headers: tuple[tuple[str, str], ...] = ()`
   (`routing.py:42-53`); adapters forward them. Needed for
   `Raw(...)` downloads and cache-control on GET handlers.
3. Serialize-time root markers with values: extend the root-marker mechanism
   (used today for `data-ccss-<hash>`) to stamp `data-cev="<value>"`.
4. (v2 only) WebSocket handler protocol next to `URLRoute` in the ASGI
   adapter.

## 13. Incremental delivery plan

- v1.0 (the migration-worthy core): substrate PRs 1-3; the extension with
  handler enumeration, arg models and coercion, signed props envelope,
  dispatch route, ops protocol, error mapping; the client runtime
  (transport, delegation bindings with modifiers, loading states, poll,
  morph via vendored idiomorph, `$sendEvent`/`$onEvent`, `events` payload
  API, instance registry); CSRF layers and auth hooks; `ViewEvents` shim and
  `url_for`; the OpenAPI CLI command; e2e tests reproducing DJC's
  form_submission and fragments examples plus a unicorn-style search demo.
- v1.1: client-side same-tick batching (protocol already allows it), served
  `openapi.json`, introspection-API event manifest, no-op detection
  (client-sent content hash, `noop` op), node-level binding transform
  replacing the textual one, GET-handler cache headers.
- v2: WebSocket transport + signed-topic subscriptions + `push()`;
  `FormEvents` helper (host-forms error mapping); opt-in server props store;
  TypeScript types generated from the manifest; the Alpine scoped-slot
  mechanic from the roadmap row, layered on this extension (it may be the
  piece that finally justifies parse-time hooks, decided then per
  `extensions_roadmap.md:81-85`).

Build-time verification points (unknowns flagged during design, to check in
the first spike): whether root markers accept valued attributes or need an
`on_serialize` assist; whether `on_template_compiled` node shapes support
attribute rewriting (fallback: stay textual); exact placement of the
runtime `Script` injection via `on_dependencies` for pages with bindings but
no component JS.

## 14. Falsifiability

Concrete outcomes that would prove this design wrong:

1. Migration test: if porting DJC's `form_submission` and `fragments`
   examples, a unicorn search component, a Tetra counter, and a
   livecomponents nested-counter each does not reach feature parity with
   fewer lines and zero third-party client libraries, the supersede claim
   fails and the API needs rework, not marketing.
2. Props envelope viability: instrument the e2e suite and two realistic apps;
   if more than ~10 percent of events-enabled components exceed the 8 KB
   envelope cap in practice, the stateless-first model is wrong and the v2
   server store must move into v1.
3. Security review: if the Django integration cannot pass a review without
   marking the dispatch view csrf-exempt, or if any input path reaches a
   handler without signature or schema validation, the layered CSRF/exposure
   design is falsified.
4. Binding ergonomics: if the compile-time binding checks produce false
   positives on real Alpine-using templates (legitimate `@x` attributes
   rejected), the recognition rule is wrong and the prefix must become
   configurable or opt-in per component.
5. Multi-instance magic: if list-rendered components make
   `$sendEvent`'s single-instance rule a recurring support question rather
   than a rare edge, the class-scoped magics should be demoted to
   documentation of the instance-scoped API only.
6. Performance: if dispatch overhead (routing + signature check + arg
   validation, excluding the user handler and render) exceeds ~2 ms p50 on
   commodity hardware, the per-call machinery is too heavy for
   keystroke-frequency events and needs a fast path.
7. Protocol neutrality: if the first non-Python host (JS) cannot implement
   the wire protocol and client runtime without consulting Python semantics
   (e.g. arg coercion rules that only make sense for Python types), the
   protocol failed its language-neutrality requirement.
