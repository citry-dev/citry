# Component.Events, design A: developer experience first

Status: design proposal (one of several competing drafts). Lens: optimize for
the Livewire / django-unicorn crowd. The primary metric is how little a user
writes for the three canonical tasks (counter, form, live search), how
inevitable the magic feels, and how good the defaults are. Escape hatches
exist at every layer, but they are hatches, not the main door. Where DX
conflicts with architectural purity, this design chooses DX and says so
(section 12 lists every such call).

This document fulfills the mandate at `docs/design/extensions_roadmap.md:62`:
one extension covering server-interactive components, weighing HTTP vs
WebSocket and the Tetra / Alpine / live-components / `Component.View` /
`Component.Events` approaches together. Handlers are named by the event they
handle, with a route derived per event (`docs/design/migration_djc.md:150`,
`docs/design/dependencies.md:653-661`).

---

## 0. The pitch: what a user writes

Three complete, working components. No routes registered by hand, no fetch
code, no swap code, no state store, no JS build step. Setup is two lines: add
the extension to the `Citry` instance and mount it (mounting is already
required for fragments today).

```python
from citry import Citry
from citry.extensions.events import EventsExtension

citry = Citry(
    extensions=[EventsExtension],
    extensions_defaults={"events": {"secret": SECRET_KEY}},
)
# then, as today: citry.contrib.fastapi.mount(app, citry) or the Django/Flask adapter
```

### Counter

```python
from citry import Component

class Counter(Component):
    class Kwargs:
        count: int = 0

    class Events:
        def increment(self):
            self.kwargs.count += 1

    def template_data(self, kwargs, slots):
        return {"count": kwargs.count}

    template = """
    <button @click="increment">
      Clicked {{ count }} times
    </button>
    """
```

Click the button; the handler runs on the server, mutates the typed kwargs,
the component re-renders, and the new HTML is morphed into the page. The
user wrote one method and one attribute.

### Live search

```python
from citry import Component

class LiveSearch(Component):
    class Kwargs:
        query: str = ""

    class Events:
        pass  # opts the component in; @bind uses the built-in $set event

    def template_data(self, kwargs, slots):
        results = find_products(kwargs.query) if kwargs.query else []
        return {"results": results}

    template = """
    <div>
      <input type="search" @bind.live.debounce.300ms="query" placeholder="Search...">
      <ul @loading.class="searching">
        <c-for each="item in results">
          <li>{{ item.name }}</li>
        </c-for>
        <c-empty>
          <li>No results</li>
        </c-empty>
      </ul>
    </div>
    """
```

Zero handler methods. `@bind.live` sends the input value to the built-in
`$set` event (debounced client-side), the server validates it against the
`Kwargs` field type, re-renders, and morphs. The focused input is never
clobbered by the morph.

### Form with validation

```python
from citry import Component
from citry.extensions.events import EventError

class ContactForm(Component):
    class Kwargs:
        name: str = ""
        email: str = ""
        sent: bool = False

    class Events:
        def submit(self):
            if "@" not in self.kwargs.email:
                raise EventError("Please fix the errors.", fields={"email": "Enter a valid email address."})
            send_contact_email(self.kwargs.name, self.kwargs.email)
            self.kwargs.sent = True

    def template_data(self, kwargs, slots):
        return {"sent": kwargs.sent}

    template = """
    <c-if cond="sent">
      <p>Thanks, we'll be in touch!</p>
    </c-if>
    <c-if cond="not sent">
      <form @submit.prevent="submit">
        <input name="name" @bind="name">
        <input name="email" @bind="email">
        <span @error="email"></span>
        <button type="submit" @loading.attr="disabled">Send</button>
      </form>
    </c-if>
    """
```

`@bind` without `.live` batches field values with the next event (here, the
submit). Validation errors travel in a dedicated response channel and land in
the `@error` element; nothing re-renders on a failed submit, so the user's
input stays put.

### Who this wins over, in one line each

- **Component.View (django-components)**: any number of named actions per
  component instead of one method per HTTP verb; the URL comes back
  (`component.events.url("submit")`), the client half finally exists.
- **django-unicorn**: the same attribute-and-modifier feel, but only declared
  kwargs round-trip (not every public attribute), handlers are opt-in by
  placement (not public-by-default), and the wire format is structured JSON
  (not Python expression strings).
- **Tetra**: the same "server method feels like a client method" ergonomics,
  without pickled live objects as state and without hard-wiring Alpine.
- **livecomponents**: the same one-endpoint / many-self-addressed-fragments
  response shape, without Redis, without manual `parent_id` threading, and
  without a five-library client stack.
- **the old Component.Ninja idea**: `@event(render=False)` handlers are typed
  JSON endpoints with schema generation (section 8), so a component can carry
  its own mini-API.

---

## 1. Prior art and inputs

Everything below was verified against source on 2026-07-04. Recon reports
(full versions in the session scratchpad): citry extension substrate, citry JS
runtime, old django-components snapshot, django-unicorn, Tetra,
livecomponents, ecosystem survey (Livewire, LiveView, Turbo, htmx, Datastar,
StimulusReflex, Inertia, django-ninja), and citry history/mandate.

Load-bearing facts checked directly in this repo:

- `URLRoute(path, handler, children, name, methods=("GET",), extra)` and
  `RouteResponse(content, content_type, status)`; handlers are sync
  `(request, **path_params)`; `request` is host-opaque
  (`packages/py/citry/citry/util/routing.py:36-84`).
- The ASGI adapter calls handlers synchronously with only the scope and never
  passes `receive`, so a POST body is unreachable today
  (`packages/py/citry/citry/contrib/asgi.py:94`). This is the single biggest
  substrate gap (section 11).
- Extension anatomy: `name`, auto-derived `class_name`, `Config`, `commands`,
  `urls` property, `citry` back-reference
  (`packages/py/citry/citry/extension.py:359-401`). User extension routes are
  namespaced under `ext/<name>/`.
- Client runtime callback payload is exactly `{ id, els, data }`
  (`packages/py/citry/citry/extensions/dependencies/client/citry.js:150`);
  manifests are inert JSON script tags picked up by a MutationObserver
  (`citry.js:201-213`); the public surface is `Citry.manager` only.
- `$onComponent(` is a cache-time regex rewrite to
  `Citry.manager.registerComponent("<class_id>", `
  (`packages/py/citry/citry/extensions/dependencies/scripts.py:56-66`).
- Typed kwargs: a plain annotated nested `Kwargs` class becomes a
  `dataclass(slots=True)` (not frozen, so in-place mutation works)
  (`packages/py/citry/citry/component.py:154-162`); instances are built with
  `cls.Kwargs(**raw_kwargs)`, so unknown/missing keys raise `TypeError`
  (`component.py:474`).
- An explicit `id=` argument pins the render id
  (`component.py:451-452`), which is what makes stable instance identity
  across re-renders possible.
- Templates see only what `template_data()` returns (`component.py:494-513`,
  `component_render.py:543`).
- The V3 grammar accepts `@click`, `v-model`-style names, and dotted names as
  plain attribute names (documented in the grammar itself,
  `crates/citry_template_parser/src/grammar.pest:220-255`), and the compiler
  gives them no special meaning, so they pass through to the HTML as static
  attributes. The `c-*` attribute prefix IS special (dynamic Python-expression
  attributes, `grammar.pest:25`), so the events vocabulary must not use it.
- Plain attribute values are atomic strings with no `{{ }}` interpolation
  (`grammar.pest:271-285`); only `c-*` attribute values evaluate expressions.
  This shapes how per-item arguments reach bindings (section 3.2).
- `build_url` is mounted-prefix concatenation and raises when unmounted
  (`packages/py/citry/citry/citry.py:316-331`); `get_component_by_class_id`
  reverses a class id (`citry.py:333-345`).
- The dependencies extension captures the user's raw nested class in
  `on_component_class_created` before the config rebuild
  (`packages/py/citry/citry/extensions/dependencies/__init__.py:187-192`);
  Events uses the same trick for handler enumeration.

What does not exist and must be added (detailed in section 11): a
framework-neutral request object with a body, response headers, a client
transport, a DOM morph, and a signing secret setting.

---

## 2. The Python API

### 2.1 Declaring handlers

A component becomes interactive by declaring a nested `class Events:`. Every
method defined on it (not underscore-prefixed, not a reserved name) is an
event handler, callable from the page. That is the whole exposure rule:

- **In the class = exposed. Not in the class = not exposed.** There is no
  `public = True`, no auto-detection, no denylist. Placement is the opt-in.
  This is the explicit-registration model the security record demands
  (unicorn's public-by-default and Livewire's implicit exposure are the
  cautionary tales), but with zero per-method ceremony because the class
  itself is the allowlist.
- Underscore-prefixed methods are private helpers.
- Handlers inherit: a component subclass inherits its parent's `Events`
  methods through normal Python inheritance (the substrate rebuilds the
  nested class with the user's class as first base, so this works today).

```python
class TodoList(Component):
    class Kwargs:
        items: list[str]
        new_item: str = ""

    class Events:
        def add(self):
            if self.kwargs.new_item.strip():
                self.kwargs.items.append(self.kwargs.new_item.strip())
                self.kwargs.new_item = ""

        def remove(self, index: int):
            del self.kwargs.items[index]

        def clear(self):
            self.kwargs.items = []

        def _dedupe(self):   # private helper, not callable from the page
            self.kwargs.items = list(dict.fromkeys(self.kwargs.items))
```

The `events` extension enumerates handlers from the raw nested class captured
in `on_component_class_created` (the same pattern the dependencies extension
uses), so config attributes and base-class helpers are never mistaken for
handlers. A handler whose name collides with a reserved name (section 2.5)
fails loudly at class definition time with a rename suggestion.

### 2.2 What a handler sees: `self`

Handlers run outside the render lifecycle (the substrate's supported
`component=None` mode). `self` is the per-call Events instance with:

| Attribute | What it is |
|---|---|
| `self.kwargs` | The component's typed `Kwargs` instance for this call, rebuilt from the verified props token plus any `@bind` updates. Mutable; mutations feed the re-render. |
| `self.request` | A small framework-neutral request: `method`, `headers`, `query`, `body`, and `native` (the host's own request object: Django `HttpRequest`, ASGI scope, WSGI environ). The escape hatch required by the brief. |
| `self.event` | Call metadata: `name`, `instance_id`, raw `args` / `named_args`. |
| `self.fx` | The effects accumulator (section 2.4). |
| `self.component_class` | The owning component class (from the substrate). |

`self.kwargs.count += 1` is the state mutation surface. There is no separate
state class: **the component's kwargs are the state that round-trips**
(section 6 covers signing and visibility). This is deliberate: citry
components are already functions of their kwargs, so "mutate kwargs,
re-render" needs no new mental model.

### 2.3 Typed arguments and coercion

Handler parameters are ordinary typed Python parameters. The wire carries
`args` (positional list) and `kwargs` (named object); the extension binds them
against the signature and coerces JSON primitives to the annotations:

```python
class Events:
    def rate(self, stars: int, comment: str = ""):
        ...

    def reschedule(self, when: datetime.date):
        ...  # "2026-07-04" coerces to date
```

Coercion covers what JSON cannot express natively: `int`/`float`
cross-coercion, `str -> UUID | datetime | date | time | Decimal | Enum`, and
`list -> tuple/set`. This is the unicorn coercion idea with the structured
wire format (never expression strings). Anything that does not bind or coerce
produces a structured validation error (section 2.6), not a host 500. Rich
coercion (nested models) comes from the optional Pydantic integration later;
the built-in layer stays dependency-free.

Two built-in events exist and are reserved (their names start with `$`, which
can never collide with a Python method name):

- `$set`: apply `@bind` updates and re-render. Used by `@bind.live`.
- `$refresh`: re-render with current kwargs. Used by `@poll` and available
  everywhere.

### 2.4 What a handler returns, and effects

The return algebra optimizes the common cases to zero thought:

1. **Return `None`** (the default): the component re-renders with the
   (possibly mutated) kwargs and the client morphs it in. The counter case.
2. **Return a JSON-able value**: the value is delivered to the client
   caller's promise (`sendEvent(...)` resolves with it), AND the component
   still re-renders. Matching Livewire/Tetra behavior avoids the "my return
   value suppressed my update" surprise.
3. **`@event(render=False)`**: pure data endpoint; no re-render, no patch.
   This is the Component.Ninja story: the handler is a typed JSON endpoint
   attached to the component. Kwargs mutations in such a handler do not
   persist (there is no re-render to carry a new token) and doing so warns in
   dev.

Everything else is an explicit effect on `self.fx`, accumulated into the
response envelope:

```python
class Events:
    def save(self):
        order = create_order(self.kwargs)
        self.fx.dispatch("order-saved", {"id": order.id})   # named client event, page-wide
        self.fx.redirect(f"/orders/{order.id}")             # client navigates; no re-render

    def add_to_cart(self):
        cart = add_item(self.kwargs.product_id)
        # update ANOTHER component in the same response: self-addressed patch
        self.fx.render(CartBadge(count=cart.count), target="#cart-badge")

    def noop(self):
        self.fx.skip_render()   # acknowledge without re-render
```

`fx` surface for v1: `dispatch(name, detail=None)`, `redirect(url)`,
`render(element, target, mode="morph")`, `skip_render()`. `push_url(url)` and
`download(...)` are v1.x. The dirty-set idea from livecomponents is here in
imperative form (accumulator methods, like Livewire's `$this->dispatch()`),
because imperative reads better in small handlers than importing result
classes.

Multi-component updates therefore have two tiers:

- **Same response** (server knows the target): `self.fx.render(element,
  target=...)` appends a self-addressed patch. `target` is a render id or a
  CSS selector the page author owns.
- **Loose coupling** (server does not know who cares):
  `self.fx.dispatch("cart-updated")`; any other component listens with
  `@on:cart-updated.window="refresh"` (section 3.4) and refreshes itself.
  This is the Livewire model; it costs an extra round trip and that is fine.

### 2.5 Per-handler and per-component configuration

Per-handler config is the optional `@event` decorator; bare methods get
defaults. Per-component config is class attributes on `Events` (which the
substrate merges with `extensions_defaults["events"]` and the extension's
factory defaults, in that precedence, for free):

```python
from citry.extensions.events import event

class Document(Component):
    class Kwargs:
        doc_id: int
        title: str = ""

    class Events:
        # per-component config (reserved names, all optional)
        guard = staticmethod(require_editor)   # callable(ctx) -> None or raise
        model = ("title",)                     # explicit @bind allowlist (default: scanned from template)
        csrf = "django"                        # "header" (default) | "django" | callable | False

        @event(debounce=400)                   # client-enforced, declared once here
        def autosave(self):
            save_draft(self.kwargs.doc_id, self.kwargs.title)

        @event(render=False)
        def word_count(self) -> dict:
            return {"words": count_words(self.kwargs.doc_id)}

        @event(methods=("GET", "POST"), guard=None)   # opt into GET for cacheable reads
        def preview(self):
            ...
```

Config keys on `Events` (all reserved names): `guard`, `csrf`, `model`,
`methods` (default `("POST",)`), `max_props_bytes` (default 8192), `globals`
(a method returning per-call template globals, section 6.4), `slots`
(section 6.5). `@event(...)` keys: `name` (wire name override), `debounce`,
`throttle`, `render`, `methods`, `guard`, `csrf`.

### 2.6 Errors

- **Validation** (args do not bind/coerce, `@bind` update fails its field
  type, props token invalid): the extension returns a structured error
  envelope with HTTP 422 (or 409 for a stale token), never a host 500.
- **User-raised**: `raise EventError(message, fields=None, status=422)`.
  `fields` feeds the `@error` template channel and the response `errors`
  object. One public error class with a status argument covers forbidden
  (403), not found (404), and conflict cases without an exception zoo.
- **Unexpected handler exceptions**: caught by the dispatcher, logged, and
  returned as a `server` error envelope with HTTP 500. The message body is
  the exception text in debug mode and a generic string otherwise.
- **Observability**: the extension owns `emit()` hooks in the established
  pattern (`on_event`, `on_event_handled`, `on_event_error`), so logging,
  metrics, or an authorization extension can wrap every dispatch without any
  new core hook.

### 2.7 URLs

Every handler has a real URL: `POST <prefix>/ext/events/{class_id}/{event}`.
`component.events.url("submit")` builds it during render (this is
`get_component_url` reborn, built on `Citry.build_url` and the ported
`format_url`, exactly as `migration_djc.md:859` earmarked). Because it is a
real per-action URL, host middleware, access logs, rate limiters, and curl
all see meaningful paths:

```
curl -X POST http://localhost:8000/citry/ext/events/Counter_a1b2c3/increment \
  -H 'content-type: application/json' -H 'x-citry-events: 1' \
  -d '{"citry": 1, "instance": "c9Zk1q", "args": [], "props": "eyJjIjo..."}'
```

---

## 3. The client API

The events client runtime is one new file, `citry-events.js` (planned
TypeScript home: `packages/js/citry-client/`, same track as the existing
runtime). It is self-contained and order-independent, served at
`<prefix>/ext/events/runtime.js`, and injected automatically (via the
existing `on_dependencies` emit hook) whenever a rendered page or fragment
contains an interactive component. Users add nothing to their pages.

### 3.1 Template bindings: the `@` vocabulary

One rule to teach: **an attribute starting with `@` is read by the events
runtime.** These are plain HTML attributes (the parser passes them through
untouched, verified against the grammar), wired client-side with delegated
listeners, so they survive morphs and cost nothing server-side.

| Attribute | Meaning |
|---|---|
| `@click="handler"` (any DOM event name) | Send the event to the server handler. Value is the handler name, optionally with literal args: `@click="rate(5)"`. |
| `@submit.prevent="save"` | Modifiers: `.prevent`, `.stop`, `.self`, `.once`, `.debounce[.300ms]`, `.throttle[.1s]`, `.enter` / `.escape` (key filters on keyboard events). |
| `@bind="field"` | Two-way binding of an input/select/textarea to a kwarg. Default is batched: the value rides with the next event. `.live` sends immediately via `$set` (150 ms debounce default), `.lazy` on blur, `.debounce.300ms` tunes it. |
| `@poll.30s="handler"` | Send an event on an interval (default handler: `$refresh`). Pauses when the tab is hidden. |
| `@loading` / `@loading.remove` / `@loading.class="x"` / `@loading.attr="disabled"` | Pending-state vocabulary while any event from this component is in flight; scope to one trigger with `@target="handler"`. |
| `@error="field"` | Shows the field's validation error text (from the response `errors` channel); empty and hidden otherwise. |
| `@on:name="handler"` / `@on:name.window="handler"` | React to a named server-dispatched event (`self.fx.dispatch(...)`) by sending another event. `.window` listens page-wide (cross-component refresh). |

Binding scope: a binding belongs to the **nearest enclosing interactive
component instance** (found by walking up to the closest element carrying a
`data-cid-*` marker registered with the events runtime). Same mental model as
Alpine scoping, predictable under nesting.

Event names in binding values are checked against the class manifest at wire
time; a typo logs a console error naming the component and the known events
(and a compile-time template lint is a v2 option once the extension can scan
templates via `on_template_loaded`).

Honest collision note: Alpine also reads `@click` inside `x-data` scopes. If
a page runs both (the Alpine scoped-slot mechanic from the same roadmap row
may bring this back), the prefix is configurable
(`Citry.events.configure({prefix: "citry:"})` makes it `citry:click`), and
the runtime skips elements inside `[x-data]` subtrees when configured to.
Livewire and Alpine coexist with exactly this kind of prefix split.

### 3.2 Arguments from templates

Because plain attribute values are static in citry (no `{{ }}` inside them,
verified in the grammar), there are two argument forms:

1. **Inline literals**, parsed client-side by a tiny literal parser (JSON
   literals plus the magics `$value` and `$event.<path>`); never `eval`, so
   CSP-safe:

   ```html
   <button @click="rate(5)">5 stars</button>
   <input @input="search($value)">
   ```

2. **Dynamic per-item args** via `arg:*` attributes, whose values CAN be
   dynamic through the existing `c-*` mechanism (`c-arg:index="i"` renders
   `arg:index="3"`):

   ```html
   <c-for each="item in items">
     <li>
       {{ item.name }}
       <button @click="remove" c-arg:id="item.id">x</button>
     </li>
   </c-for>
   ```

   The runtime collects `arg:*` attributes from the triggering element into
   named args. Writing `@click="remove(item.id)"` (a template variable in an
   inline arg) fails loudly in the console with a pointer to `c-arg:*`.

### 3.3 The JS surface: `sendEvent` and `onEvent`

The `$onComponent` callback payload grows two fields (this needs no source
rewrite; it extends the object built at `citry.js:150`):

```python
class Chart(Component):
    class Kwargs:
        dataset_id: int

    class Events:
        @event(render=False)
        def points(self, window: str = "7d") -> list:
            return load_points(self.kwargs.dataset_id, window)

    js = """
    $onComponent(({ id, els, data, sendEvent, onEvent }) => {
      const chart = drawChart(els[0], data.initialPoints);

      // send to a server handler; resolves with the handler's return value
      els[0].querySelector(".range").addEventListener("change", async (e) => {
        chart.update(await sendEvent("points", { window: e.target.value }));
      });

      // handle named events dispatched by any handler (self.fx.dispatch)
      const stop = onEvent("dataset-changed", (detail) => chart.flash(detail.id));

      // cleanup: runs before this callback re-runs after a server update
      return () => { stop(); chart.destroy(); };
    });
    """
```

- `sendEvent(name, args?) -> Promise<result.data>`; rejects with a structured
  error object on failure. Bound to this instance (id and props token
  resolved internally).
- `onEvent(name, fn) -> unsubscribe`; fires for events dispatched in
  responses to this instance's calls and for page-wide dispatches naming this
  instance.
- **Teardown (new runtime capability)**: an `$onComponent` callback may now
  return a cleanup function; the runtime calls it before re-invoking the
  callback for the same instance id (which happens after every server
  re-render, because the fresh fragment carries a fresh manifest entry). This
  closes the re-init gap the current runtime has and is the documented way to
  make event-driven components idempotent.

Escape hatches outside component JS:

- `Citry.events.send(target, name, args?)`: `target` is an instance id or an
  Element (resolved via its closest `data-cid-*` marker). For host-page code.
- `Citry.events.on(name, fn)`: page-level listener for dispatched events.
- Everything also surfaces as bubbling DOM CustomEvents, so Alpine, htmx, or
  vanilla code can integrate with zero citry API: `citry:send`,
  `citry:update` (after patch), `citry:error`, `citry:event:<name>` (for
  `fx.dispatch`), all carrying `{instance, event, ...}` in `detail`.

Considered and rejected: top-level `$sendEvent(` / `$onEvent(` source
rewrites in the `$onComponent` family. Component JS runs once per class, but
sending needs an instance; a class-scoped `$sendEvent` would either guess the
instance or grow a confusing dual signature. The payload fields give correct
instance scope for free and keep one magic (`$onComponent`) as the entry
point. The names live on as the payload fields.

### 3.4 Multi-component updates, optimistic UI, loading states

- **Multi-component**: patches in one response (server-addressed,
  section 2.4) plus `fx.dispatch` + `@on:name.window="refresh"` for loose
  coupling. Both shapes are the field's converged answers (Turbo/htmx OOB
  lists; Livewire events).
- **Loading**: automatic `citry-busy` class on the component root and the
  triggering element for the duration of a call, plus the `@loading`
  vocabulary. CSS-only spinners work with zero JS.
- **Optimistic UI**: deliberately **not** predicted-state rollback machinery
  (no surveyed framework ships one; they all converged on pending-state
  hooks). The pieces provided: instant pending states, focused-input
  protection during morphs, `.debounce` batching, and full freedom in
  component JS (`sendEvent` + your own DOM writes) when a component truly
  wants optimism. This is a DX-informed refusal: rollback magic that is wrong
  10 percent of the time is worse DX than an honest busy state.

### 3.5 DOM updates: morph by default

Responses patch the DOM by morphing (vendored idiomorph, MIT, a few KB
minified), not `outerHTML` replacement, because morph-by-default is what
makes forms and focus survive updates; replacement would feel broken to the
Livewire/unicorn crowd this design targets. Rules:

- Patch target: the element(s) carrying `data-cid-<instance>` (the marker
  already exists; the server pins the render id on re-render, so identity is
  stable).
- The focused element's value is never overwritten if it is `@bind`-bound
  (the Tetra rule), and after every patch the runtime re-applies its recorded
  `@bind` values to unfocused bound inputs, so templates do not need to echo
  `value=` for bound fields.
- Per-patch `mode`: `morph` (default) | `replace` | `append` | `prepend` |
  `remove`; per-element opt-out `@morph.ignore` for widget-owned subtrees
  (the Select2 escape hatch).
- After patching, the fragment's manifest tag is picked up by the existing
  MutationObserver machinery unchanged: assets dedupe by URL, `$onComponent`
  re-fires for the updated instance (with teardown first, section 3.3).

---

## 4. The wire protocol

Language-neutral, versioned, JSON with embedded HTML. The protocol is the
shared surface across future host languages (the extension logic is
host-language-specific by design, the wire and the client runtime are not),
so nothing in it is Python-shaped: no Python types, no expression strings,
names are plain JSON.

### 4.1 Request

`POST <prefix>/ext/events/{class_id}/{event}` with
`content-type: application/json` and header `X-Citry-Events: 1`:

```json
{
  "citry": 1,
  "instance": "c9Zk1q",
  "args": [5],
  "kwargs": {"comment": "great"},
  "props": "eyJjIjoiQ291bnRlcl9hMWIyYzMiLCJrIjp7ImNvdW50IjozfX0.h4x9...",
  "updates": {"query": "shoes"},
  "epoch": 4
}
```

- `citry`: protocol major version. Unknown major -> structured error.
- `args` / `kwargs`: the Python calling convention, language-neutrally
  (positional list + named object). The client never needs parameter-name
  knowledge for positional calls; the server binds against the signature.
- `props`: the signed component-inputs token (section 6). Base64url payload
  plus HMAC tag.
- `updates`: batched `@bind` values since the last call (empty for none).
- `epoch`: per-instance monotonic counter; responses echo it so the client
  drops stale out-of-order responses (the unicorn 0.66 mechanism).

Addressing rides in the URL (per-event routes), not the body, so host
middleware and logs see real operations. The route is a single `{param}`
pattern (`ext/events/{class_id}/{event}`) resolved through the registry per
request, so it survives Django's snapshot-at-mount routing.

### 4.2 Response

```json
{
  "citry": 1,
  "status": "ok",
  "epoch": 4,
  "data": null,
  "patches": [
    {
      "target": "c9Zk1q",
      "mode": "morph",
      "html": "<button data-cid-c9Zk1q=\"\" @click=\"increment\">Clicked 4 times</button>\n<script type=\"application/json\" data-citry>...</script><script type=\"application/json\" data-citry-events>...</script>"
    }
  ],
  "events": [{"name": "order-saved", "detail": {"id": 7}}],
  "errors": null,
  "location": null
}
```

- **HTML and JSON coexist by embedding**: each `patches[].html` is a complete
  `serialize(deps_strategy="fragment")` output (markup + inert manifest
  tags), carried as a JSON string. Insertion activates assets and callbacks
  through the existing manifest machinery; the new props token for the
  instance rides inside the fragment's events manifest, so the response needs
  no separate token field. `data` is the handler's return value for the
  caller's promise. One envelope, both worlds.
- `patches` is a list of self-addressed operations (`target` = instance id or
  CSS selector), the Turbo/htmx-OOB converged shape, so one event can update
  any number of components in one response.
- `events`: named client events to dispatch after patching (the HX-Trigger /
  push_event analog).
- `errors`: field-keyed validation messages for the `@error` channel.
- `location`: `{ "url": "...", "mode": "redirect" | "push" }` or null.

Error responses use the same envelope with `status: "error"` and an `error`
object `{type, message, fields?}` where `type` is one of `validation`,
`stale_props`, `unknown_event`, `forbidden`, `payload_too_large`, `server`.
The HTTP status mirrors the type (422, 409, 404, 403, 413, 500), so proxies,
host middleware, and logs behave sensibly.

### 4.3 Batching and files

- The envelope is single-call in v1; `updates` piggybacking already collapses
  the chatty case (typed input + action = one request), which is most of what
  Livewire's bundling buys. A `POST ext/events/batch` accepting
  `{"citry": 1, "calls": [ ...each with "component" and "event"... ]}` is
  specified now (so the schema never breaks) and shipped when measurement
  shows multi-component chatter (v2).
- Files (v1.x): `multipart/form-data` with the JSON envelope in a
  `citry-envelope` part and each file as its own part, referenced from args
  by part name; handler parameters annotated `UploadedFile`. The Tetra
  multipart shape, minus implicit upload-on-first-POST.
- Form-encoded fallback (v1.x): a plain `<form method="post"
  action="{{ ...events.url('submit') }}">` posts urlencoded fields; the
  server maps them to `updates`, runs the handler, and (per `Accept`)
  returns full-page HTML or a redirect. This is the no-JS progressive
  enhancement story and the "form-data" response-format requirement.

### 4.4 Versioning

`citry: 1` is the protocol major. Additive fields are minor and never gated.
A major bump changes the field; the server answers old majors with a
`protocol` error telling the client to reload (the runtime shows nothing;
the page keeps working server-rendered). The runtime and server ship
together in one wheel, so version skew only exists across deploys; the
`stale_props` and `protocol` errors both surface as a `citry:stale` DOM
event whose default handling (configurable) is a soft reload prompt.

---

## 5. Transports

### 5.1 What is shared

The dispatcher is a pure function, envelope in, envelope out:

```python
class EventsExtension(Extension):
    name = "events"

    def dispatch(self, call: EventCall, *, request: EventRequest) -> EventResult:
        """Verify, bind, guard, run the handler, re-render, build the result."""
```

Every transport (built-in HTTP, future WebSocket, and any custom one) calls
`dispatch`. `EventCall` and `EventResult` are plain dataclasses mirroring the
wire envelope one to one. This is the pluggable-transport interface: it is
deliberately not a class hierarchy of Transport objects, because the honest
integration point for "RPC, GraphQL?" is "call `dispatch` from your own
endpoint":

```python
# custom transport example: a GraphQL mutation resolver
def resolve_component_event(root, info, class_id, event, payload):
    ext = citry_instance.extensions.get_extension("events")
    result = ext.dispatch(EventCall.from_json(payload, class_id, event),
                          request=EventRequest.from_native(info.context.request))
    return result.to_json()
```

Client-side, the transport is one swappable async function:

```js
Citry.events.configure({
  transport: async (url, envelope) => {   // default: fetch POST
    return myRpc.call("citry.events", { url, envelope });
  },
});
```

### 5.2 HTTP (v1)

One `URLRoute` from `Extension.urls`:

```python
@property
def urls(self):
    return [
        URLRoute("{class_id}/{event}", handler=self._http_handler,
                 methods=("POST", "GET"), name="citry_event"),
        URLRoute("runtime.js", handler=self._serve_runtime, name="citry_events_runtime"),
    ]
    # mounted by the manager under ext/events/, per the existing namespacing
```

The handler parses the envelope from `request.body`, checks the per-handler
method allowlist (GET only for handlers that opted in), and translates
`EventResult` to a `RouteResponse` with JSON content and headers. Works
identically under Django, FastAPI/Starlette, Flask, plain ASGI and WSGI once
the substrate request/response fixes land (section 11). Sync handlers only in
v1 (offloaded to a worker thread under ASGI); `async def` handlers are a
v1.x ASGI-only addition.

### 5.3 WebSocket (v2)

- One socket per page, multiplexed (`ext/events/ws`), never per component
  (the converged granularity).
- Frames are the same envelopes wrapped with a frame type and correlation id:
  `{"citry": 1, "type": "call", "id": "r7", "component": ..., "event": ...,
  ...}` up; `{"type": "result", "id": "r7", ...}` down; `{"type": "event",
  ...}` for push. Because props ride each call, **the socket carries no
  per-connection component state**; it is purely a faster pipe plus a push
  channel. Reconnect is trivial (nothing to resume), which is the payoff of
  the stateless model and the biggest divergence from LiveView.
- Requires ASGI and an adapter extension: `URLRoute` grows
  `extra={"protocol": "websocket"}`, the ASGI adapter learns to accept
  websocket scopes for such routes, WSGI hosts simply never mount it and the
  client stays on HTTP. The dev hot-reload design already anticipates
  exactly this seam (`docs/design/hot_reload.md:431-438`).
- The client upgrades only when the server advertises it in the page
  manifest; HTTP remains the default and the fallback.

SSE is the cheaper alternative for the push-only half (browser-native
reconnect, no new uplink); the envelope works as SSE frames unchanged. The
HTTP-up/SSE-down option is explicitly kept open until v2 measurement; the
trend away from WS-required designs is real.

---

## 6. State model and security

### 6.1 What round-trips: signed kwargs, nothing else

At render time, for each interactive component instance, the extension
serializes the component's raw kwargs to canonical JSON and signs them:

```
props = base64url({"c": class_id, "k": {...kwargs...}, "v": 1}) + "." + base64url(HMAC_SHA256(secret, payload))
```

- Full-length HMAC-SHA256 with the configured secret (`extensions_defaults
  ["events"]["secret"]`, falling back to the proposed `CitrySettings.secret`;
  a loud error at first sign if absent, with the one-line fix for each host).
- **JSON-safe values only, enforced at sign time**: a kwarg that does not
  survive JSON round-tripping raises at first render, naming the component,
  the field, and the fixes (make it JSON-safe, exclude it and re-derive in
  `load`, or drop Events). No pickle, no rich-object revival, ever. The
  Livewire RCEs, the Tetra unpickler, and the unicorn class-pollution CVE
  all lived in rich rehydration; this design refuses the category.
- Size-capped (`max_props_bytes`, default 8 KB) with a pointed error
  suggesting the id-plus-reload pattern (`kwargs = {"doc_id": 7}`, load the
  rest in `template_data`) - which is also just better component design.
- On an event call: verify tag (constant-time), check class id matches the
  route, rebuild `cls.Kwargs(**k)` (same TypeError-to-422 path as args),
  apply `updates` to writable fields, run the handler.

Tampering model: `props` is trusted after verification (the server minted
it); `args`, `kwargs`, and `updates` are user input, validated against the
signature and the writable-field set. `updates` may only touch fields in the
`model` set (scanned from the component's own template's `@bind` targets at
class creation, or declared explicitly), and each value must satisfy the
`Kwargs` field type.

Visibility: the token is signed, not encrypted; kwargs are readable by their
own user (base64). That is usually fine (they rendered the page), but a
server-only kwarg (an internal flag, a cost price) would leak. Three
mitigations, in recommended order: do not put secrets in kwargs; exclude the
field (`model`-independent `exclude = (...)` on Events) and re-derive it in a
`load()` method that runs before each handler; or enable token encryption
(v1.x, optional, requires the `cryptography` package). The docs lead with the
symptom ("anything in Kwargs is visible in the page source of an interactive
component").

### 6.2 Exposure rules

Stated once more because it is the security core: only methods on the nested
`Events` class are callable; only template-bound (or declared) kwargs are
settable; everything else on the component is unreachable from the wire.
There is no dotted-path property setting of any kind (the unicorn
CVE-2025-24370 shape is unrepresentable in this protocol).

### 6.3 CSRF and auth

- **Baseline (all hosts)**: POST only by default, `X-Citry-Events: 1`
  required (forces a CORS preflight cross-origin), and `Origin` /
  `Sec-Fetch-Site` same-origin verification. This is the modern
  fetch-baseline and it is on by default (`csrf = "header"`).
- **Django**: `csrf = "django"` makes the adapter run Django's token
  validation (client auto-attaches the token from the cookie or a meta tag).
  The Django adapter documentation covers the middleware interaction
  explicitly, since a bare POST to a citry route would otherwise be rejected
  or unprotected depending on setup.
- **Custom**: `csrf = callable(request) -> None or raise`.
- **Auth**: `guard` at extension default, component, or handler level:
  `callable(ctx)` receiving the request (with `.native` for host user
  lookup), raising `EventError(status=403)` to deny. Honest limitation: citry
  cannot inherit "the page's auth" framework-neutrally because it does not
  know which page rendered the component; the guard plus host middleware on
  the real per-event URLs are the tools. The migration guide shows the
  two-line Django `login_required` guard.

### 6.4 Request-scoped render inputs

`template_globals` from the original page render do not round-trip. This is
livecomponents' silent-wrong-render problem, handled loudly: interactive
components should derive template data from kwargs plus storage; when a
per-request value is genuinely needed (current user), `Events.globals(self)
-> dict` computes template globals per event call from `self.request`. A dev-
mode warning fires when an interactive component's first render consumed
template globals and no `globals` method exists.

### 6.5 Slots

An interactive component that received slot fills raises at first render:
slot content lives in the parent template and cannot be re-rendered from an
event. The error says exactly that and names the fix (wrap the slotted
region in its own component, or set `slots = "default"` on Events to
re-render with slot defaults when that is acceptable). Storing raw template
source to replay fills (the livecomponents approach) is explicitly rejected.

---

## 7. Server push

Deferred to v2, with the seam designed now and one v1 stopgap:

- **v1 stopgap**: `@poll` (interval refresh, tab-aware). Zero infrastructure,
  covers dashboards and job-status pages today.
- **v2 push**: over the WebSocket (or SSE) channel. Server API:
  `citry_instance.extensions.get_extension("events").push(channel, name,
  detail=None)` plus `push_render(channel, element, target=...)`. Pages
  subscribe to **signed channel names** the server printed into the page
  manifest (`Events.channels(self) -> list[str]` at render time), the Turbo
  precedent, so a client cannot subscribe to a channel it was not handed.
  Crucially, the pushed payload is the same result envelope as an HTTP
  response (self-addressed patches, named events), so push is an additive
  transport, not a second protocol.
- Reconnect is a re-subscribe, not a resume; missed pushes are lost, and the
  documented pattern for correctness is push-to-refresh (push a named event;
  bindings refresh via `$refresh`), not push-as-source-of-truth.

The Alpine scoped-slot mechanic named in the same roadmap row (client-side
slot data via x-teleport) is part of this extension's exploration but is
orthogonal to the wire protocol; it becomes its own milestone after v1, and
per the roadmap its parse-time hook needs are decided while building it, not
here.

---

## 8. OpenAPI and schema generation

Handlers are introspectable Python signatures, so citry can do what
django-ninja does and no interactive framework ever has:

- At class creation the extension builds, per handler, a parameter model
  (name, annotation, default, coercion) - the same model that powers runtime
  validation, so the schema can never drift from behavior.
- `citry ext run events schema --format openapi -o openapi.json` (an
  `ExtensionCommand`, CLI already built) emits one operation per
  (component, event): path `POST /ext/events/{class_id}/{event}`,
  `operationId` `<ComponentName>_<event>`, request body = the call envelope
  with `args`/`kwargs` typed from the signature, responses = the result
  envelope, with `data` typed from the return annotation for
  `render=False` handlers. `--only-data` restricts output to `render=False`
  handlers, which is the useful API-surface view; patch-returning handlers
  are documented as returning the envelope with `text/html` patches.
- The same models feed the client manifest (event names, parameter names,
  debounce hints) that the runtime already needs, and later TS type
  generation and the planned Storybook command. Synergy with the component
  introspection API (#26): introspection lists components and inputs; events
  adds the per-component operations table to that surface rather than
  duplicating it.
- Pydantic remains optional: when the (already roadmapped) Pydantic
  integration is installed, annotated models validate bodies and enrich the
  emitted schema; the core stays dependency-free with the lighter coercion.

This is a genuine differentiator (LiveView params are untyped maps, Livewire
has no schema, unicorn parses expression strings), and it lands almost free
because validation needs the models anyway.

---

## 9. Migration stories

### 9.1 From django-components Component.View

```python
# before (django-components)
class ContactForm(Component):
    class View:
        public = True
        def post(self, request, *args, **kwargs):
            name = request.POST.get("name", "stranger")
            return ThankYou.render_to_response(kwargs={"name": name})

url = get_component_url(ContactForm)

# after (citry)
class ContactForm(Component):
    class Kwargs:
        name: str = ""

    class Events:
        def submit(self):
            self.fx.render(ThankYou(name=self.kwargs.name), target="#thank-you")

url = component.events.url("submit")   # in template_data, or the @submit binding does it all
```

One URL per verb becomes one URL per named action; `?type=` multiplexing
dies; the request is parsed and validated for you; the client half (binding,
fetch, swap) exists. `get_component_url`'s query/fragment/route-param powers
return via `events.url(name, query=..., fragment=...)` on the ported
`format_url`.

### 9.2 From django-unicorn

```html
<!-- before -->
<input unicorn:model.debounce-300="query">
<button unicorn:click="add_todo">Add</button>

<!-- after -->
<input @bind.live.debounce.300ms="query">
<button @click="add_todo">Add</button>
```

Python side: class attributes become declared `Kwargs` fields (only these
round-trip; there is no `javascript_exclude` hygiene because nothing else is
serialized); action methods move under `class Events:`; `$refresh` exists;
`$reset` is a two-line handler that reassigns defaults; type-hint coercion
carries over. Django forms validation maps to raising
`EventError(fields=form.errors)` from a handler (a `form_class` sugar is a
candidate v1.x nicety). What unicorn users give up: the property-setter
shortcut (`unicorn:click="name='Bob'"`), by design (no settable paths on the
wire); the replacement is a one-line handler.

### 9.3 From Tetra

```python
# before                                   # after
count = public(0)                          class Kwargs:
                                               count: int = 0
@public
def increment(self):                       class Events:
    self.count += 1                            def increment(self):
                                                   self.kwargs.count += 1
@public.debounce(200)
def message_change(self, value, ...):          @event(debounce=200)
    ...                                        def message_change(self, value: str): ...
```

Template `@click="increment()"` stays almost literally the same. Encrypted
pickled state tokens become signed JSON kwargs (smaller, deploy-stable,
no unpickler); `load()` maps to `Events.globals`/`load` for re-derived
values; `self.client.foo()` maps to `self.fx.dispatch` plus `onEvent` in
component JS (a closed channel from day one, so no whitelist retrofit
breaking documented behavior); `_dispatch` child-to-parent maps to
`fx.dispatch` + `@on:name.window`. Not carried over: Alpine as the mandatory
client model, per-attribute server watches (use `@bind.live` + a handler),
and the offline call queue (out of scope, stated).

### 9.4 From livecomponents

`@command` methods with `CallContext` become `Events` methods with `self`;
`call_context.state` becomes `self.kwargs`; the Redis session store
disappears (state is the signed token; no TTL 410s, no per-tab duplication,
no Redis in dev); `parent_id` threading disappears (targets are explicit:
`fx.render(target=...)` or dispatched events); execution results map one to
one onto `fx` calls (`ComponentDirty` -> default re-render, `ParentDirty` ->
`fx.dispatch` + parent `@on:`, `RedirectPage`/`PushUrl` -> `fx.redirect` /
`fx.push_url`, `TriggerEvents` -> `fx.dispatch`). What they give up:
server-held state between calls; components whose state genuinely cannot
live in kwargs (a wizard holding a big draft) wait for the optional
server-side props store (section 10, later), and the migration guide says so
honestly.

---

## 10. Incremental delivery

**Substrate first (core PRs, each small, each with tests; section 11):**
A1 request object + adapter bodies; A2 `RouteResponse.headers`; A3 ASGI
sync-handler thread offload; A4 `CitrySettings.secret`.

**v1.0, HTTP core (the extension):**

- B1 server: extension skeleton, handler enumeration (raw-class capture),
  arg binding + coercion + errors, signed props, `$set`/`$refresh`,
  per-event route + dispatcher, `fx` effects, emit hooks
  (`on_event`, `on_event_handled`, `on_event_error`), `events.url()`.
  Exit criterion: the counter works via curl under FastAPI and Django.
- B2 client: `citry-events.js` (bindings `@<event>`, `arg:*`, modifiers,
  `@bind`, `@poll`, `@loading`, `@error`, `@on:`), fetch transport with
  header CSRF, epoch handling, morph (vendored idiomorph) with
  focused-input protection, manifest ingestion, `sendEvent` / `onEvent`
  payload fields, `$onComponent` teardown support, DOM CustomEvents.
  Exit criterion: the three pitch examples pass e2e in the existing harness
  under WSGI and ASGI.
- B3 docs: user guide, security page (visibility, CSRF, guards), migration
  guides (section 9), and the extension's own design doc updated from this
  proposal.

**v1.x (fast follows, in value order):** OpenAPI/schema command; multipart
file uploads; no-JS form fallback; Django `form_class` sugar; async handlers
under ASGI; `fx.push_url`/`download`; optional token encryption; optional
server-side props store (opt-in `props = "server"`: token becomes a random
key into `Citry.cache`, for kwargs-too-big or kwargs-too-secret components;
inherits the documented shared-cache-multi-worker constraint fragments
already have).

**v2 (each its own decision point):** WebSocket or SSE push channel + `push`
API + signed channels; batch endpoint; compile-time binding lint (and only
then, if scanning proves insufficient, any grammar-level `c-on:` form, which
would trigger the full high-risk-area process); the Alpine scoped-slot
milestone.

---

## 11. Substrate changes required (core, not the extension)

Called out explicitly because they precede the extension and touch shared
surfaces:

1. **Framework-neutral request** (`citry/util/routing.py`): a small
   `Request` dataclass (`method`, `path`, `query` multidict, `headers`
   case-insensitive, `body: bytes`, `native: Any`). Adapters construct it:
   ASGI drains `receive` for bodied methods (today it never passes `receive`,
   `contrib/asgi.py:94`), WSGI reads `wsgi.input` per `CONTENT_LENGTH`,
   Django wraps `HttpRequest`. Existing handlers never read `request`, so
   the contract change is safe in-repo; it is pre-1.0 and the docstring
   already reserves the slot.
2. **`RouteResponse.headers: tuple[tuple[str, str], ...] = ()`**: additive;
   adapters forward them.
3. **ASGI sync-handler offload**: run handlers via a worker thread
   (`anyio.to_thread` / loop executor) instead of blocking the event loop;
   matters once handlers do real work.
4. **`CitrySettings.secret: str | None = None`**: canonical signing secret
   home (the extension config can override; Django users pass
   `SECRET_KEY`). Frozen-at-construction semantics unchanged.
5. **Runtime payload extension + teardown** in `citry.js`: add fields to the
   callback object (backward compatible) and support cleanup-function
   returns. Owned by the dependencies extension's client file; coordinated,
   not forked.

None of these touch the Rust contract (grammar, AST, compiler, LangImpl,
PyO3), so no Mechanism 2/4 process is triggered by v1. The only candidate
Rust involvement ever is a compile-time binding check, explicitly deferred.

---

## 12. Where DX won over purity (the honest list)

1. **Kwargs are the mutable state.** Purists would keep render inputs
   immutable and thread new state functionally. `self.kwargs.count += 1` is
   the entire reason the counter is three lines; the cost (kwargs are
   visible, size-capped, and must be JSON-safe) is fenced with loud errors.
2. **Handlers by placement, not by decorator.** A mandatory `@event` on
   every method would be more explicit; the nested class already is the
   explicit boundary, and the decorator exists for the cases that need
   config. Chosen for the "it just worked" first five minutes.
3. **Morph by default, vendored.** Owning a morph dependency is a real
   maintenance cost; replace-by-default would be purer (no third-party DOM
   semantics) and would feel broken next to Livewire. DX wins; the morph is
   vendored and pinned, with `mode="replace"` one flag away.
4. **Return value both resolves the promise and re-renders.** A stricter
   algebra (data XOR render) is cleaner; it also produces the classic "my
   update stopped happening when I added a return" bug report. Matching
   Livewire/Tetra behavior was chosen deliberately.
5. **`@` prefix despite the Alpine overlap.** `citry:click` everywhere would
   be collision-proof and uglier. The target audience reads `@click`
   natively; the prefix is configurable for mixed pages, and the tradeoff is
   documented rather than avoided.
6. **Template scan as the default `model` allowlist.** A purist design would
   demand explicit declaration of writable fields; scanning the component's
   own template for `@bind` targets is the same author intent expressed
   once. The explicit `model = (...)` override remains for dynamic-template
   edge cases, and the scan happens server-side at class creation, so the
   client can never widen it.

---

## 13. Falsifiability

Concrete outcomes that would prove this design wrong, checkable early:

1. **The morph spike fails.** Before B2 starts, a spike must show: a
   re-rendered fragment with a pinned instance id morphs over the live DOM,
   `$onComponent` re-fires exactly once with teardown, assets dedupe, and a
   focused `@bind` input keeps its value and caret through a `@bind.live`
   cycle. If the existing manifest/runtime machinery fights this (double
   fires, lost focus, asset re-execution), the client model needs redesign
   before any server work hardens.
2. **The LOC claim fails.** Once B1+B2 exist, the pitch examples must work
   at (or under) the line counts shown in section 0 with no hidden glue. If
   the real counter needs a route registration, a JS import, or manual state
   plumbing, the DX thesis is dead and the design should not ship as-is.
3. **Kwargs-as-state proves too small.** If, dogfooding the first ~10 real
   interactive components, more than ~3 need server-held state beyond
   kwargs-plus-database (or median token size exceeds ~2 KB, or any example
   hits the 8 KB cap), the stateless default is wrong for real apps and the
   server-side props store must move from v1.x-optional to core, which also
   reopens the transport question.
4. **Adapter parity breaks.** The same e2e suite must pass under
   Django/WSGI and FastAPI/ASGI unmodified. A body-handling or CSRF asymmetry
   that leaks into user-visible behavior falsifies the framework-neutral
   `Request` abstraction (the alternative being per-host handler wrappers,
   a different architecture).
5. **Per-event URLs deliver no value.** The claimed benefits are host
   middleware, logs, and OpenAPI. If in practice Django users cannot attach
   per-route policy through the citry include (plausible: Django decorates
   at `urlpatterns` level, and citry's routes are matched internally), and
   logs/OpenAPI alone do not justify the extra path surface, collapse to the
   single `update` endpoint (Livewire-style) in the protocol's next minor;
   the envelope already carries `component`/`event` in the batch shape, so
   the change is contained.
6. **The migration pitch does not convert.** Port one real example from each
   of unicorn, Tetra, and livecomponents docs. If any port is longer than
   its original or needs custom JS for behavior the original got
   declaratively, the "reason to migrate" requirement is unmet in that
   direction and the vocabulary needs the missing attribute, not marketing.

---

## Appendix: open questions for review

- `@bind` naming: `@bind` vs `@model` (Vue familiarity vs plain words; this
  draft chose plain words).
- Should `class Events: pass` be required for `@bind`-only components, or
  should `model = (...)` alone opt a component in? (This draft requires the
  class; one rule, "interactive means Events exists".)
- `EventError` as the single user-raised error vs a small hierarchy
  (`Forbidden`, `NotFound`); status codes on one class chosen for API
  surface minimalism.
- Whether the events instance manifest should also ride a root-element
  attribute (debuggability in devtools) in addition to the inert manifest
  tag; deferred to B2 profiling (attribute size vs manifest locality).
- GET events and caching: opt-in exists; whether to document
  `Cache-Control` recipes in v1 or hold for the Cache extension pairing.
