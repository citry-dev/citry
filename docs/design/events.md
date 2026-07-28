# Design: the Events extension (`Component.Events`)

**Status (2026-07-26): Events v1 is implemented but not yet frozen or
released as the v1 beta.** The exact current wire contract is
[`packages/protocol/events/v1/spec.md`](../../packages/protocol/events/v1/spec.md);
this document owns the product and implementation design behind it. The Alpine and
frontend-boundary source of truth is now [`alpinejs.md`](alpinejs.md); this
document remains normative for the Events protocol, State, actions,
transport, and queue. The full
section-by-section maintainer readthrough completed 2026-07-07 (three
review rounds overall), and the client-model round (nested anchor
continuity, targeted renders, the event queue, the `#c-*` channel) was
decided by the maintainer 2026-07-15 against the analyses and spike in
[`events_research/`](events_research/) and is folded into sections 5.1,
5.3, 5.5, 5.6, and the decision records in 14.3. The 2026-07-17
review round ratified that round's six drafted recommendations into
normative text, made the event queue an explicit dependency DAG (5.6,
14.3.4), settled the `#c-key` depth rule (5.3) and the `$component`
props declaration (5.5). The 2026-07-19 client-boundary review accepted props
and event relocation, the init ancestry DAG, managed Alpine helpers, and the
stable reactive `scope`; it also accepted the round-two unknown-key,
default-reuse, and update-validation contracts. The
2026-07-19 `RootGroup`
spike then proved the multi-root listener mechanism
and stable live `els` representation across Chromium, Firefox, and WebKit;
the rootless comment-range spike proved text/empty logical lifetime,
stable-anchor normalization, grouped mirrors, contextual parsing,
nested/adjacent isolation, and exact cleanup in the same three engines. The
focused boundary-handler isolation spike passed the same browser matrix and
locked whole Alpine handler expressions and optional Citry argument
expressions to the exact authored source scope. `$el`, `$dispatch`, and
`$event` come from the physical child; native `currentTarget` remains
untouched and follows DOM listener mode and timing. Server-handler validation,
serialization, registry, component-tag client bindings (`$c-props`, Alpine
handlers such as `@click`, and Citry handlers such as `@c-save` or
`@c-poll.5s` resolved from a nested `<c-*>` tag), and morph integration are
now landed. The parent owns each binding's expression or server handler, while
the child supplies the component boundary where the browser applies it, as
recorded in [`alpinejs_plan.md`](alpinejs_plan.md). On
2026-07-20 the maintainer selected graph-first Alpine and the public Citry
props directive `$c-props`, including the orthogonal `c-$c-props` form. The
2026-07-22 WP26 closeout further pinned canonical first-live-root event
dispatch, natural-event draft protection before `.on:`/`.lazy` flushes, and
the remaining strict-JSON and client-queue edge behavior. This is
the design doc the
roadmap calls for in its "Server-interactive / reactive components" row
([`extensions_roadmap.md`](extensions_roadmap.md) section 3): one extension
that serves component event handlers over HTTP (and later WebSocket) and
drives client interactivity, superseding django-components'
`Component.View`, the old `url` extension, the Vue-plugin prototype, and the
external tools users would otherwise reach for (django-unicorn, Tetra,
livecomponents). The delegation companion is
[`events_plan.md`](events_plan.md); a change to this design must be
checked against the affected work-package entries there.

Process note: this document synthesizes three competing drafts (one
optimizing developer experience, one the wire contract, one the migration
story). The drafts were judged adversarially against the citry source and
the prior-art record. Two maintainer review rounds then reshaped the core
decisions (the explicit `Component.State` contract, the `@c-*` binding
vocabulary, the single return channel for actions, no built-in events,
the `_context` hook, the `/e/` route segment). Section 14 records
every contested decision with its reason. A production-usage audit of the
maintainer's own django-components application grounds the design
empirically (section 1.4).

Related docs: the extension substrate this plugs into is
[`extensions.md`](extensions.md); the fragment pipeline, mount contract, and
URL layer it stands on are [`dependencies.md`](dependencies.md) sections 8
and 9; the migration verdicts it fulfills are in
[`migration_djc.md`](migration_djc.md) (search "Component.Events").
Operating rules: [`/CLAUDE.md`](../../CLAUDE.md).

---

## Demo

Copy-paste material for a talk, a thread, or a README: each demo is
self-contained, uses only the designed v1 surface, and kills one
specific pain. The setup they all share is the one every citry app
already has (Events is a built-in extension, so there is nothing to
register):

```python
from citry import Citry

citry = Citry()
citry.contrib.fastapi.mount(app, citry)  # or django / flask / asgi / wsgi
```

**1. Clicks that never deserved a server round trip.** In unicorn,
Livewire, or htmx, every +1 is a POST. Here the click mutates client
state; the server hears about it once, when it matters:

```python
from citry import Component

class Counter(Component):
    class Kwargs:
        count: int = 0

    class State(Kwargs):
        pass

    class Events:
        def save(self, state):
            persist_count(state.count)

    def template_data(self, kwargs, slots):
        return {"count": kwargs.count}

    template = """
      <div>
        <button @click="$state.count++">
          +1
        </button>
        <span x-text="$state.count">
          {{ count }}
        </span>
        <button @c-click="save">
          Save
        </button>
      </div>
    """
```

The `+1` button is pure client (Alpine's `@click` writing the reactive
`$state`); `@c-click="save"` is the one server call, and it carries the
whole State with it.

**2. A form that validates on the server and shows errors inline, with
no page reload.** Named form fields populate the handler's input schema
on submit; server-side errors land next to the inputs:

```python
from citry import Component
from citry.ext.events import EventError

class ContactIn:
    email: str
    message: str

class ContactForm(Component):
    class Events:
        def submit(self, data: ContactIn):
            if not valid_email(data.email):
                raise EventError(
                    "Please fix the errors.",
                    fields={
                        "email": "Enter a valid email address."
                    },
                )
            send_message(data.email, data.message)
            return {"sent": True}

    template = """
      <form @c-submit="submit">
        <input name="email">
        <span x-text="$error?.fieldErrors.email"></span>
        <textarea name="message"></textarea>
        <button type="submit" :disabled="$loading()">
          Send
        </button>
      </form>
    """
```

**3. One click updates a different part of the page.** The add-to-cart
button lives in the product card; the badge lives in the header. The
handler renders the badge into its own target and dispatches an event
anyone can listen to:

```python
from citry import Component
from citry.ext.events import actions

class CartIn:
    product_id: int

class AddToCart(Component):
    class Events:
        def add(self, data: CartIn):
            cart = add_item(data.product_id)
            return [
                actions.Render(
                    CartBadge(count=cart.count),
                    target="#cart-badge",
                ),
                actions.Dispatch(
                    "cart:updated",
                    {"count": cart.count},
                ),
            ]

    template = """
      <button @c-click="add({ product_id: 42 })">
        Add to cart
      </button>
    """
```

Any other component can react with one function call, no wiring:
```html
<div x-init="
  $onEvent('cart:updated', () => {
    $sendEvent('refresh');
  })
">...</div>
```

**4. Every handler is a real, typed endpoint.** No second routing layer,
no separate API app. A JSON-returning handler has its own URL that curl,
middleware, rate limiters, and the OpenAPI command all see:

```python
from citry import Component
from citry.ext.events import event

class Stats(Component):
    class Events:
        @event(methods=("GET",))
        def summary(self) -> dict:
            return {
                "users": count_users(),
                "active_today": count_active(),
            }
```

Target event handler with curl:

```bash
$ curl 'http://localhost:8000/citry/ext/events/e/Stats_ab12cd/summary'
```

Generate OpenAPI document:

```bash
$ citry ext run events openapi
```

**5. It works with JavaScript disabled (and plays nice with htmx).**
The same handler serves a classic form post; the response is HTML, a
redirect is a real 303:

```python
from citry import Component
from citry.ext.events import actions

class SignupIn:
    email: str

class Signup(Component):
    class Events:
        def submit(self, data: SignupIn):
            create_account(data)
            return actions.Redirect("/welcome")

    def template_data(self, kwargs, slots):
        return {
            "submit_url": self.events.url("submit"),
        }

    template = """
      <form method="post" c-action="submit_url">
        <input name="email">
        <button type="submit">
          Sign up
        </button>
      </form>
    """
```

htmx users can point `hx-post` at the same URL and get a fragment back,
without adopting the citry client at all.

**6. Dashboards without a WebSocket.** Interval refresh is one
attribute; polling pauses in hidden tabs:

```python
from citry import Component

class JobStatus(Component):
    class Kwargs:
        job_id: int

    class State(Kwargs):
        pass

    class Events:
        def refresh(self, state):
            return JobStatus(job_id=state.job_id)

    def template_data(self, kwargs, slots):
        return {
            "status": job_status(kwargs.job_id),
        }

    template = """
      <div @c-poll.30s="refresh">
        Job is {{ status }}
      </div>
    """
```

---

## 1. Prior art (what was searched)

### 1.1 In this repo (verified against source)

The substrate (the core extension machinery this design stands on) is
already built, and this design adds no core hooks:

- **Extension anatomy.** `Extension` with `name`, auto-derived `class_name`
  (`events` -> `Events`), `urls`, `commands`, and the `citry` back-reference
  ([`extension.py:359-401`](../../packages/py/citry/citry/extension.py)).
  The name `events` is free (conflict check at `extension.py:620-624`).
  Per-component nested config classes are rebuilt at class definition with
  three-level defaults (component > `extensions_defaults` > factory,
  `extension.py:777-803`); the config is instantiated per render as
  `component.<name>` with a weakref to the live component, and the
  out-of-lifecycle `component=None` case is supported
  (`extension.py:331-346`). An extension can capture the user's raw nested
  class in `on_component_class_created` before the rebuild, the way the
  dependencies extension does
  ([`dependencies/__init__.py:187-192`](../../packages/py/citry/citry/ext/dependencies/__init__.py)).
- **Custom hooks.** `emit(name, ctx, result="none"|"first"|"map")` lets an
  extension own its own lifecycle hooks (`extension.py:719-773`); the rule
  that extension lifecycle points are `emit()` hooks, not core hooks, is
  settled ([`extensions.md`](extensions.md) section 9.2).
- **Routing.** `URLRoute(path, handler, methods, name)` with `{param}`
  segments and first-match-in-definition-order resolution
  ([`routing.py:36-141`](../../packages/py/citry/citry/util/routing.py));
  user-extension routes are namespaced under `ext/<name>/`
  (`extension.py:660-685`); URL building goes through the mount contract
  (`Citry.build_url`, [`citry.py:316-331`](../../packages/py/citry/citry/citry.py))
  and raises with guidance when nothing is mounted. `RouteResponse` is
  content, content type, and status only, handlers are sync, and the ASGI
  adapter never passes `receive`, so **a POST body is unreachable today**
  ([`contrib/asgi.py:94`](../../packages/py/citry/citry/contrib/asgi.py));
  section 12 lists the substrate fixes.
- **The design slot.** [`dependencies.md`](dependencies.md) section 9.5
  fixes this extension's shape in advance: per-event routes through
  `Extension.urls`, handlers built on
  `Cls(**kwargs).render().serialize(deps_strategy="fragment")`, standing on
  the mount contract. The interim pattern (a user-written host route) is the
  FastAPI test app
  ([`test_contrib_fastapi.py`](../../packages/py/citry/tests/test_contrib_fastapi.py)).
- **The client runtime baseline.** Before the Events decorator extends it in
  5.5, `Citry.manager` exposes seven public methods and `$component` callbacks
  receive exactly `{id, els, data}`
  ([`citry.js:150`](../../packages/py/citry/citry/ext/dependencies/client/citry.js));
  fragments deliver assets and calls through inert base64-encoded JSON
  manifest tags picked up by a MutationObserver (`citry.js:201-213`).
  `$component(` is a cache-time regex rewrite to
  `Citry.manager.registerComponent("<class_id>", `
  ([`scripts.py:56-66`](../../packages/py/citry/citry/ext/dependencies/scripts.py)),
  which means component JS is cached **per class** and anything per-instance
  must flow through the callback's argument object, not the JS text.
- **Typed inputs.** A nested `Kwargs` class becomes a non-frozen
  `dataclass(slots=True)`
  ([`component.py:154-162`](../../packages/py/citry/citry/component.py));
  instances are built with `cls.Kwargs(**raw)`, so unknown or missing keys
  raise (`component.py:463-475`). The Events extension gives its `State`
  nested class (section 3.2) the same dataclass treatment, applied by the
  extension itself so the core stays unaware of it. An explicit `id=`
  argument pins the render id (`component.py:447-456`); the Events design
deliberately leaves it unused and relies on the client anchor for
continuity instead (5.3, 5.5).
- **The template grammar.** Attribute names like `@c-click`,
  `@c-submit.prevent`, and `:c-query.lazy` parse as ordinary static
  attributes
  ([`grammar.pest:228-255`](../../crates/citry_template_parser/src/grammar.pest));
  plain attribute values are atomic strings with no interpolation. Bare
  `c-*` attributes (names starting with `c-`) are the dynamic
  Python-expression channel, and the `c-` prefix is stripped when the
  resolved attribute is emitted
  ([`nodes/__init__.py:430-441`](../../packages/py/citry/citry/nodes/__init__.py),
  `:631`), so `c-data-id="item.id"` renders `data-id="3"`. The `@c-*` and `:c-*` names
  start with `@` and `:`, so they never touch that channel (and `:c-*` is
  likewise distinct from the `c-bind` attribute spread,
  [`template_html_attrs.md`](template_html_attrs.md)). Both facts shape the vocabulary
  (section 5).
- **The push-channel precedent.** Browser live-reload already sketches an
  extension mounting a dev-only SSE or WebSocket endpoint via
  `Extension.urls` ([`hot_reload.md:431-438`](hot_reload.md)); nothing
  WebSocket-shaped exists in the adapters yet.
- **Migration verdicts.** `Component.View`'s HTTP-method-named handler API
  is dropped, "the concept returns redesigned as `Component.Events`"
  ([`migration_djc.md`](migration_djc.md), view.py rows);
  `get_component_url` returns with this design on `Extension.urls` plus the
  fragment strategy; the ported `format_url` is explicitly waiting for "a
  future component-URL builder" as its first caller.

### 1.2 The old django-components snapshot (`old-djc.zip`)

The snapshot lives at the repo root as `old-djc.zip`; paths below are inside
its `django-components/` tree (it holds uncommitted prototype work that no
public checkout has).

- **`Component.View` as shipped** (`src/django_components/extensions/view.py`):
  one method per HTTP verb, one URL per component class, `public`
  auto-detection cached by mutating the user's class, `get_route_path()`
  override, `get_component_url(query, fragment, args, kwargs)`. Where it
  broke down, with evidence: the fragments example multiplexes one `get()`
  across three behaviors via `?type=alpine|js|htmx`
  (`docs/examples/fragments/page.py:123-139`); handlers hand-parse raw
  requests (`request.POST.get("name", "stranger")`,
  `docs/examples/form_submission/component.py`); and there is no client
  half at all (every fetch/swap in the examples is user-authored glue).
  Section 1.4 quantifies both failure modes in production.
- **The `$emit`/`$on` sketch** (`sampleproject/components/todo/todo.py`):
  the maintainer's own design sandbox for a component event API, with
  `$emit("updateItemsCount", count)`, `$on(name, handler)` returning an
  unsubscribe function, and template-level `@event="handler"` binding at
  the call site. Never shipped; the shapes survive in this design's
  `Dispatch` action and `onEvent` surface.
- **The Vue/Alpine prototype** (`src/django_vue/`, plus the patched
  `alpine-composition` bundle under `other/`): Vue-fidelity event emitting
  (declared emits, validator functions, `onX` handler props) built on
  Alpine, plus scoped slots across the server boundary via `x-teleport`.
  Recorded failure modes this design avoids: props-vs-attributes ambiguity
  needing a runtime middleman, module-global per-render stores with manual
  cleanup, and an abandoned `data-x-init` JSON attribute channel for
  server-to-client state.
- **`Component.Ninja` produced no code in this snapshot.** The only trace
  in the tree is `GIT_TODOS_1.md:5`, "Add djc-ninja integration."; grep for
  `NinjaAPI` / `import ninja` over every Python file returns nothing.
  A commented-out proof-of-concept does exist elsewhere: in the production
  application audited in section 1.4 (`prompt_playground.py` carries an
  extension sketch with named endpoints under a nested class,
  `on_component_class_created` registration, and URL lookup by handler
  name). The intention (typed component endpoints plus OpenAPI) is absorbed
  into this design as a property of every handler (section 9).

### 1.3 The field (external survey)

Full per-tool findings live in [`events_research/`](events_research/)
(the AlpineJS research is in [`alpinejs/`](alpinejs/)); the load-bearing
conclusions:

- **django-unicorn**: the attribute-and-modifier template grammar is its
  best-liked surface and is kept (as `@c-*`); its wire format (Python
  expression strings parsed server-side), public-by-default method
  exposure, full-state round-trip per keystroke, and truncated checksum are
  the cautionary tales. Its CVE record is summarized in section 7.6.
- **Tetra**: server methods that return promises to client JS, the
  versioned envelope, and declared-once debounce config are kept; pickled
  encrypted state tokens (key leak equals remote code execution, deploy
  invalidation storms) and Alpine as a hard dependency are not.
- **livecomponents**: its execution-result return values (a handler
  returns a list of things for the client to do) and
  one-response-many-fragments updates are kept; the Redis pickle session
  store, manual `parent_id` threading, and the five-library client stack
  are not. Its silent-wrong-render bug (re-render losing context the
  original render had) is made structurally visible here instead (section
  7.5).
- **Livewire / LiveView / Turbo / htmx / Datastar**: the converged shapes
  this design adopts are self-addressed action lists (Turbo Streams and
  htmx out-of-band swaps call them streams or operations), morph-by-default
  DOM updates, one socket per page when WS exists, signed channel names for
  push (Turbo), pending-state hooks instead of optimistic rollback, and the
  post-2024 trend away from WebSocket-required architectures.
- **django-ninja**: handler signatures as the single source of truth for
  validation and OpenAPI. No surveyed interactive framework generates
  schemas from its event handlers; doing so is a citry differentiator.

### 1.4 Production usage audit (the golden reference)

To ground the design in real usage rather than framework-demo intuition,
every `Component.View`-bearing component in the maintainer's production
django-components application was audited (snapshot `old-chk.zip`, audited
2026-07-04: 38 View-bearing files, 36 analyzable components after skips,
21 pages and 15 widgets, plus the surrounding templates and client JS).
This section is the reference for how events are actually used; the design
decisions it grounds are cross-referenced.

**Verbs degrade into arbitrary RPC slots by the second action.** 18 of 36
components implement two or more HTTP verbs, and 21 of 36 multiplex beyond
verb-per-action. `ProcessStepsPage` maps POST to update, PATCH to clone,
and DELETE to delete; `PromptPlayground` uses PATCH for a read-only lookup
because POST was taken; create-vs-edit pages bake a `submit_method` string
(`"POST"`/`"PATCH"`) into their own kwargs so the client knows which verb
to fire. This is the failure mode the charter (the roadmap row this design
answers) recorded, now observed at scale, and the reason handlers are named
by event (section 3.1).

**State is small ids, everywhere, without exception.** All 52 typed query
schemas in the project carry only ids, short enums, and booleans (median 2
fields, max 5). The state the citry design would round-trip per component:
median ~45 bytes, maximum ~150 bytes; as full signed tokens (state, class
id, timestamp, HMAC, base64) that is roughly 150 to 300 bytes, one to two
orders of magnitude under the size canary (the mint-time cap that flags
oversized State, section 7.1). What components
*render* is vastly larger (step trees, choice lists, layout data) and is
always refetched: every handler starts from `get_object_or_404` on the id
fields. The project already practices id-plus-reload universally; it even
built the state channel by hand, unsigned, as 15 to 60 bytes of render
facts baked into URLs at render time.

**The explicit State mapping is what production code already does.** Only
5 of 36 components would have a State trivially mirroring their kwargs
(`class State(Kwargs): pass`). The dominant shape, 31 of 36, is exactly
the decoupled contract of section 3.2: kwargs hold rich inputs (ORM
objects, layout data) while the surviving state is a few ids and flags
derived from them. 32 of 36 components are faithfully rebuildable from
that state, and 8 of them already re-render themselves from query ids
today, meaning the handler is the rebuild recipe, already written. This
settled the "is explicit State just ceremony" question empirically
(section 15.3) and drove the removal of built-in re-render events
(section 3.4): the handlers already decide and perform the rendering.

**Interactive components receive no slot fills in practice.** All 138
`{% fill %}` uses in the project flow into generic UI components (Table,
Dialog, Form, Tabs) *inside* the interactive components' own templates;
zero View-bearing components receive fills at their call sites (verified
programmatically). Interactive components are self-contained subtrees in
practice; the fills contract (section 7.5, re-renders replace the
subtree and never replay call-site fills) is therefore a library-author
note, not an app-code hazard.

**The missing client half is the dominant tax.** One client pattern rules:
the server bakes endpoint URLs via `get_component_url` into templates and
JS props (116 non-test references), and Alpine fires them through a
hand-rolled `$fetch` helper (47 call sites) that wraps `fetch` and injects
the CSRF token by hand. htmx is absent. Because nothing can apply a
server response to the page, 23 of 36 components end every mutation in
`window.location.reload()` or a redirect, and two pages substitute a
freshly created id into a `'00000'` placeholder URL client-side because
the server could not express a redirect. The `Redirect` action, the
`render` action, and the runtime's CSRF autowiring each have five-plus
ready call sites per app area.

**Request-scoped context is load-bearing, not optional.** `request.user`
or session data is read inside 25 of 38 View bodies (permission checks,
audit user ids, per-user API clients), and auth decorators wrap all 38.
This grounds the `_context` hook (section 3.6) and the guarantee that
the `request` injectable is always populated (section 3.3).

**The Ninja ancestor.** `prompt_playground.py` contains a commented-out
extension sketch of named endpoints under a nested class with
`on_component_class_created` registration and URL lookup by handler name:
the maintainer's own earlier arrival at this design's shape, abandoned
only for lack of the surrounding machinery this doc specifies.

---

## 2. The design in one page

A citry component is a function of its inputs. The Events extension makes a
component interactive by giving it named, server-side **event handlers**, an
explicit **State** contract for what round-trips (travels to the browser
and back with every call), and a client runtime that calls the handlers:

- The user declares a nested `class Events:` on a component. Every
  non-underscore method on it is an event handler, callable from the page.
  Placement is the allowlist; there is no `public` flag and there are no
  built-in events.
- Handlers that need data across calls declare a nested `class State:`, a
  JSON-serializable dataclass that is **deliberately separate from
  `Kwargs`**. Only State round-trips; kwargs and slots can hold anything
  (ORM objects, slot fills) because they never travel. For a leaf component
  whose kwargs are already JSON-safe, `class State(Kwargs): pass` is the
  one-line spelling; the production audit (1.4) shows the common case is a
  few ids derived from richer kwargs. At render time the extension signs
  the State into an opaque token delivered with the HTML; nothing lives on
  the server between calls, and components without handlers pay zero cost.
- An event call POSTs a small JSON envelope carrying
  `{event, args, state}` (the full shape is 4.2) to a real per-event
  URL. The
  server verifies the token, validates the args against the handler's
  signature, and runs the handler, injecting by name what its signature
  declares (`data`, the validated input schema; `state`; `context`;
  `request`; `event`).
- **The handler's return value is the response**: a single channel carrying
  a list of **actions** the browser runtime resolves. Each action is
  self-addressed, meaning it carries its own target: morph this fragment
  here, deliver this JSON, dispatch this browser event, refresh this
  token, redirect. Rendering is always explicit: the
  original inputs (kwargs, slot fills) are not available at event time, so
  new HTML is always a fresh component tree the handler chooses to build,
  usually from state. Returning `None` acknowledges; returning a dict
  resolves the caller's promise; returning an element renders it over the
  calling instance.
- The wire is always a 200 envelope; nothing is expressed in HTTP
  semantics, which is what keeps the same protocol working over WebSocket
  and SSE later.
- Rendered HTML in a response is a complete
  `serialize(deps_strategy="fragment")` output, so assets, JS/CSS
  variables, and `$component` re-fire through the existing manifest
  machinery unchanged. The fragment pipeline is the update vehicle; Events
  adds the missing client half (transport, bindings, morph) and the missing
  server half (dispatch, validation, state).
- Templates opt into zero-JS interactivity with a small attribute
  vocabulary: `@c-*` for events and `:c-*` for state bindings
  (`@c-click="add"`, `:c-query.debounce.300ms="refresh"`,
  `@c-poll.30s="refresh"`), rewritten at template load so the authored
  syntax never reaches the browser; component JS gets `sendEvent` / `onEvent` on the `$component`
  callback object for everything else.
- HTTP is the v1 transport. The dispatcher is transport-agnostic, so
  WebSocket (v2) and anything custom (a GraphQL mutation, postMessage from
  a sandboxed preview) carry the same envelopes through the same code path.

What this deliberately is not: a reactive-attributes framework. Only the
declared State round-trips, only declared handlers are callable, and the
wire carries data, never expressions or revivable objects. Every remote-code
and class-pollution CVE in the prior art lived in rich rehydration of
client-sent state; this design refuses the category (section 7.6).

### What a user writes

Events is a **built-in extension**, the second after `dependencies`
(built-ins are prepended to every instance's extension set with their
names reserved, [`extensions.md`](extensions.md) section 2). So there is
nothing to register; setup is the mount that fragments already require:

```python
from citry import Citry

citry = Citry()
# then, as today: citry.contrib.fastapi.mount(app, citry), or the Django/Flask adapter
```

The counter:

```python
from citry import Component

class Counter(Component):
    class Kwargs:
        count: int = 0

    class State(Kwargs):
        pass

    class Events:
        def increment(self, state):
            state.count += 1
            return Counter(count=state.count)

    def template_data(self, kwargs, slots):
        return {"count": kwargs.count}

    template = """
      <button @c-click="increment">
        Clicked {{ count }} times
      </button>
    """
```

Click the button; the handler runs on the server, mutates the typed state,
and builds a fresh `Counter` from it. The new HTML is morphed over the
instance (patched in place rather than replaced). Returning the element
is the explicit "and show this" step; there is no hidden re-render.

Live search, with a two-way binding: `:c-query` binds the input to the
State field, and the attribute's value names the handler that receives
each (debounced) update, so who updates the state and when is spelled out
in the template:

```python
class LiveSearch(Component):
    class Kwargs:
        query: str = ""

    class State(Kwargs):
        pass

    class Events:
        def refresh(self, state):
            return LiveSearch(query=state.query)

    def template_data(self, kwargs, slots):
        results = find_products(kwargs.query) if kwargs.query else []
        return {"results": results}

    template = """
      <div>
        <input
          type="search"
          placeholder="Search..."
          :c-query.debounce.300ms="refresh"
        >
        <ul :class="{ searching: $loading() }">
          <c-for each="item in results">
            <li>{{ item.name }}</li>
          </c-for>
        </ul>
      </div>
    """
```

A form with server-side validation errors, where a failed submit keeps
the user's input (nothing re-renders on failure). Form fields populate
the handler's `data` schema, collected from the form like a native
submit, so this
component needs no State at all:

```python
from citry import Component
from citry.ext.events import EventError

class ContactIn:
    name: str = ""
    email: str = ""

class ContactForm(Component):
    class Kwargs:
        name: str = ""
        email: str = ""
        sent: bool = False

    class Events:
        def submit(self, data: ContactIn):
            if "@" not in data.email:
                raise EventError(
                    "Please fix the errors.",
                    fields={"email": "Enter a valid email address."},
                )
            send_contact_email(data.name, data.email)
            return ContactForm(name=data.name, email=data.email, sent=True)

    def template_data(self, kwargs, slots):
        return {"sent": kwargs.sent}

    template = """
      <c-if cond="sent">
        <p>Thanks, we'll be in touch!</p>
      </c-if>
      <c-else>
        <form @c-submit.prevent="submit">
          <input name="name">
          <input name="email">
          <span x-text="$error?.fieldErrors.email"></span>
          <button type="submit" :disabled="$loading()">Send</button>
        </form>
      </c-else>
    """
```

No routes registered by hand, no fetch code, no swap code, no state
store, no client stack to assemble. (`$loading` and `$error` are read-only
magics, Alpine's `$`-prefixed expression helpers, which the runtime provides
to every interactive component's Alpine scope, section 5.5; `:class`,
`:disabled`, and `x-text` are plain Alpine.)

### Reading the data flow (the LiveSearch trace)

The LiveSearch example is deliberately traceable top to bottom with
nothing held in your head; this trace is how to think about an
interactive component, and it doubles as the skeleton for the docs-site
tutorial:

1. `query` is declared as a component input (`Kwargs`).
2. `class State(Kwargs)` declares that the same fields round-trip as
   state.
3. `template_data` derives the render-time data from it
   (`find_products(kwargs.query)`).
4. The template renders `results` item by item via `<c-for>`.
5. `:c-query` on the `<input>` binds the input's value to the `query`
   state field: the input shows what the state holds.
6. The initial value traces up through State into Kwargs: the default is
   `""`, so the input starts empty.
7. The modifiers and the value, `.debounce.300ms="refresh"`, make the
   binding two-way: an edit is debounced 300 ms, then one call carries
   the `query` update together with the `refresh` event.
8. `refresh` is found on `Events`, where every public method is a
   handler.
9. `refresh` declares `state` in its signature (injected by name, 3.3)
   and builds a fresh `LiveSearch` from it: the state-to-inputs
   conversion is explicit in the return, not hidden in machinery.
10. The returned element is the instance's **next rendering** (3.4): the
    unit of server rendering is the component, so the whole `LiveSearch`
    instance is replaced, never just the `<input>`, and the morph keeps
    the focused input's value and caret while the result list changes
    under it.
11. Had `refresh` returned a list of actions instead, those would apply
    in order; the single element is just the most common value on the
    same return channel.

### Who this wins over, in one line each

- **Component.View (django-components)**: any number of named actions per
  component instead of one method per HTTP verb; the URL comes back
  (`component.events.url("submit")`); the client half finally exists.
- **django-unicorn**: the same attribute-and-modifier feel, but only the
  declared State round-trips (not every public attribute), handlers are
  opt-in by placement, and the wire carries structured JSON, never
  expression strings.
- **Tetra**: the same "server method feels like a client method"
  ergonomics, without pickled live objects as state and without making a
  generated Alpine data object the source of component identity. Citry ships
  pinned stock Alpine under its graph-first component ownership model.
- **livecomponents**: the same one-response-many-fragments update shape,
  without Redis, without manual `parent_id` threading, and without a
  five-library client stack.
- **the old Component.Ninja idea**: handlers that return JSON are typed
  endpoints with schema generation (section 9), so a component can carry
  its own mini-API.

---

## 3. The Python API

### 3.1 Declaring handlers

Every non-underscore method defined on the component's own `Events` class
is an event handler. **In the class means exposed; not in the class means
not exposed.** There are no reserved public methods and no built-in
events, so the rule has no exceptions: public `def` means handler,
underscore `def` means private helper (or the `_context` hook, 3.6),
underscore attributes mean configuration (3.5). The extension enumerates
handlers from Citry's preserved nested declaration chain, so inherited
config-base members are never mistaken for handlers. When a component child
declares its own `class Events:`, Citry automatically combines it with the
parent declarations in component C3 order. Parent handlers therefore remain
available without spelling `class Events(Parent.Events)`, and a child method
with the same name overrides the parent. `Events = None` stops that
component-level inheritance; a nearer `class Events:` above the reset starts a
new chain. `*args` / `**kwargs` in a handler signature are
rejected at class definition (the signature is the schema).

Note on `self`: inside a handler, `self` is the per-call **Events config
instance**, never the component (no component instance exists during
dispatch; the substrate's `component=None` mode). The separate `State`
contract keeps that visible: there is no `self.kwargs` at event time, and
nothing that looks like one.

### 3.2 The State contract

`class State:` on the component declares **exactly what round-trips**
between the browser and the handlers. The extension rebuilds it as a
non-frozen `dataclass(slots=True)` (the same treatment the core gives
`Kwargs`, applied by the extension). A child `class State:` automatically adds
to its parents' State fields in component C3 order; `State = None` resets the
inherited State, and a nearer declaration can reopen the chain. Rules:

- State is deliberately **separate from `Kwargs`**. Kwargs and slots are
  render-time inputs and can hold anything: ORM instances, big structures,
  slot fills. None of that travels. State must be JSON-serializable,
  enforced when the token is minted, with an error naming the component and
  field.
- Because State is the only thing that survives the render, it is
  structurally clear inside a handler that the original inputs are gone.
  A design that reused Kwargs as the state would leave "does this still
  include the slots?" as a documentation question; the separate class makes
  the answer visible in the code.
- `class State(Kwargs): pass` is the explicit one-line spelling for leaf
  components whose kwargs are already JSON-safe: it inherits the field
  declarations, and the default capture (below) fills it from the kwargs.
  The production audit (1.4) found this is the minority case (5 of 36);
  the norm is a State of a few ids derived from richer kwargs.
- **Capture at render time**: the component may define
  `state_data(self, kwargs, slots)` alongside its `template_data` /
  `js_data` / `css_data` (the same data-method family, and where users
  think about data flow). It returns the State (or a dict for it) for the
  instance being rendered. The default derivation builds State from
  same-named kwargs; fields with no kwarg match use their State defaults,
  and a field with neither is a render-time error.

  ```python
  class Document(Component):
      class Kwargs:
          doc: Doc  # ORM object; never travels
          title: str = ""

      class State:
          doc_id: int
          title: str = ""

      def state_data(self, kwargs, slots):
          return {
              "doc_id": kwargs.doc.pk,
              "title": kwargs.title,
          }
  ```

- **Underscore means meta, on State too** (mirroring the Events rule).
  A State field whose name starts with `_` cannot be declared (fields are
  the wire contract); underscore *attributes* are reserved for the
  framework's meta settings. Handlers always read and mutate every field;
  the meta only governs the client-side channels and the token. The full
  State meta surface:

  | Attribute | Type | Default | What it does |
  |---|---|---|---|
  | `_public` | tuple of field names | all fields | Which fields templates and client bindings may touch, and the only fields whose plain values ship client-side (4.4, 7.2). Omission from `_public` is how a field becomes server-only. |
  | `_model` | tuple of field names | same as `_public` | Which public fields the client may write, through two-way bindings or `$state`; declare it only to clamp down. Must be a subset of `_public` (7.2). |
  | `_storage` | `"signed"` \| `"server"` | `"signed"` | Where the round-trip State lives: signed into the client token (7.1), or, opt-in, a server-side store keyed by an opaque token (the livecomponents migration's step one, 10). |
  | `_max_bytes` | `int` | `8192` | Mint-time cap on the serialized State; a design-smell canary, not a technical limit (7.1). |
  | `_max_age` | `timedelta` | none | Optional token expiry; expired tokens answer `stale_state` and degrade per component, not per page (7.1). |

  Details and the security doctrine in 7.2.
- State may carry methods; they survive the dataclass conversion. The
  recommended convention is a `render()` method holding the component's
  rebuild recipe, so multiple handlers share it (`self` inside it is the
  state instance):

  ```python
  class State:
      doc_id: int
      title: str = ""

      def render(self):
          return Document(
              doc=load_doc(self.doc_id),
              title=self.title,
          )
  ```

  This is a convention, not API: nothing in the framework calls it. The
  audit's strongest pattern (8 of 36 components already re-render
  themselves from a few ids; "the handler is the rebuild recipe, already
  written") is exactly this method, extracted.
- A component with handlers but no State has stateless handlers
  (the `state` injectable is `None`, calls carry no token).

### 3.3 The handler signature

Handler parameters come from a **fixed name vocabulary**, and a handler
declares only what it needs. A parameter outside the vocabulary is a
class-definition error: typos die loudly, and every signature can be fully
classified when the class is created (`*args` / `**kwargs` are rejected
for the same reason). The design is grounded in two research reports
([`events_research/typing-lab-report.md`](events_research/typing-lab-report.md),
[`events_research/binding-models-report.md`](events_research/binding-models-report.md));
the contested calls are recorded in 14.1.11.

| Parameter | What is injected |
|---|---|
| `data` | The user input, as **one schema object** (the whole wire `args` payload validated against the annotation). Omit it for handlers that take no input. |
| `state` | The typed `State` instance, rebuilt from the verified token plus any pending two-way binding updates. Mutable; mutations travel back in the refreshed token. `None` when the component declares no State. |
| `context` | Whatever the `_context` hook returned for this call (3.6); `None` when no hook is configured. |
| `request` | A small framework-neutral request (`method`, `headers`, `query`, `body`, `form`, `files`) plus `native`, the untouched host object. **Always populated**: HTTP fills everything; WebSocket fills headers and cookies from connect time; every transport that reaches the server has a real carrier (the postMessage transport arrives as the bridge's HTTP request). Only `native`'s type varies per adapter, and `event.transport` discriminates. |
| `event` | Call metadata: `name`, `instance_id`, `transport`, and the raw args payload. |

```python
class SearchIn:
    query: str = ""
    limit: int = 10

class TodoState:
    project_id: int

    def render(self):
        return TodoList(project_id=self.project_id)

class TodoList(Component):
    class Kwargs:
        project_id: int
        query: str = ""

    State = TodoState

    class Events:
        def search(self, data: SearchIn, state: TodoState):
            return TodoList(
                project_id=state.project_id,
                query=data.query,
            )

        def refresh(self, state: TodoState):
            return state.render()
```

**Injection is by name; annotations are advisory.** The dispatcher never
resolves the annotations on `state` / `context` / `request` / `event` at
runtime. Python's annotation scoping rules for nested classes (the
typing-lab report's subject) therefore cannot break dispatch, and users
annotate purely for their editor. The typed spelling that is green on both
mypy and pyright with zero ceremony is the **root-level State class**
assigned onto the component (`State = TodoState`, as above). The nested
`class State(Kwargs)` spelling remains for the terse untyped case, where
the `state` parameter is simply left unannotated. (Name-based recognition
is safe here where it famously was not in Litestar, because user data
never shares the parameter namespace: it all lives inside `data`.)

**`data` is deliberately a single schema, not spread arguments.** A
schema class per action is more verbose than arg-by-arg for a two-field
handler, and that verbosity is chosen on purpose: schemas are reusable
(CRUD inputs, form shapes shared between handlers and tests), importable,
and they nudge projects toward explicit contracts. The annotation is any
annotated class (given the same dataclass treatment as `Kwargs` and
`State`), a dataclass, or a Pydantic model when the integration is
installed. It is the one annotation the dispatcher must resolve at
runtime, because it is the validator, so module-level schema classes are
the documented style. Validation and coercion: fields coerce from JSON
primitives (`int`/`float` cross-coercion, `str` to `UUID | datetime |
date | time | Decimal | Enum`, which parse from strings because a
string is their canonical JSON encoding, `list` to `tuple`/`set`,
nested annotated
classes from objects); extra keys are a 422, missing required fields are
a 422 with per-field messages, never a host 500. A JSON payload sending
a string where the schema declares `int`, `float`, or `bool` is a 422,
not a coercion: JSON can express those types natively, so a mistyped
field there is a client bug worth surfacing (the audit rationale
below). The string transports cannot express them: form posts and GET
query strings carry only strings, so for those codecs (6.2) the binding
is source-aware, and strings additionally bind to declared `int` /
`float` / `bool` fields (`"5"` binds to `int`; boolean spellings accept
the HTML form vocabulary: `"true"` / `"false"` / `"1"` / `"0"` / `"on"`;
anything else is the per-field 422). File fields are declared
as `UploadedFile` (or `list[UploadedFile]`) on the schema and arrive via
the multipart codec (6.2).

Deliberately absent: ORM-model-by-primary-key coercion (Livewire and
unicorn both do it; it turns an argument into an unauthorized database
fetch). Handlers fetch and authorize their own models. The audit backs the
strictness: every production handler starts from `get_object_or_404` on
id arguments, and the audit found one client sending an undeclared field
that the schema silently dropped; here extra keys are a 422, not silence.

**Ambient access exists, but the signature is the style.** The same
per-call values live as attributes on the Events config instance
(`self.state`, `self.context`, `self.request`, `self.event`), because
guards, `_context`, and result resolvers receive that instance and need
them. Handlers may use them too. For those who prefer that style, the
optional generic base (`class Events(citry.Events[TodoState]):`, the one
spelling the typing lab found green for `self.*` on both checkers) types
them. The documented style is the signature, and the pitch examples never
import a base. Action constructors are imported
(`from citry.ext.events import actions`, 3.4), and a handler that
needs its component class names it directly.

### 3.4 The return channel: actions

A handler's return value is the response. There is exactly one channel
(no collector, no side-effect accumulation), and what flows through it is
**actions**: self-addressed instructions the browser runtime applies in
order. Since the original inputs are not available at event time,
rendering is always explicit: new HTML is a fresh component tree the
handler builds, usually from state.

Action constructors are imported once
(`from citry.ext.events import actions`); the capitalized names
signal that these **construct values to return**, they do not perform
anything when called:

| Constructor | Wire action | Meaning |
|---|---|---|
| `actions.Render(element, target=None, swap="morph")` | `render` | Render the element server-side, deliver it as a fragment, morph it into `target` (default: the calling instance). |
| `actions.Data(value)` | `data` | Resolve the client caller's promise with this JSON value. |
| `actions.Dispatch(name, detail=None)` | `event` | Dispatch a named browser event (DOM CustomEvent; `onEvent` listeners and plain `addEventListener` react). |
| `actions.Redirect(url)` | `redirect` | Navigate the page. |
| `actions.PushUrl(url)` / `actions.ReplaceUrl(url)` (v1.x) | `url` | History update without navigation, pushing onto or replacing the top of the history stack (the htmx `HX-Push-Url` / `HX-Replace-Url` sibling pair). The client preserves `history.state`; Citry does not synthesize `popstate` or restore component HTML or State on later Back/Forward navigation. |
| `actions.Download(content, filename, content_type=...)` (v1.x) | none (escape) | A file download. Sugar over the raw-response escape below, so its handler uses `@event(bundle=False)`, runs through the per-event HTTP route, leaves State unchanged, and returns the download bare or as a list's only element. It cannot share a list or request with another result. The client accepts a successful attachment response for one call, buffers the blob, and starts the save only after the call survives timeout and supersession checks. |

Every envelope-riding constructor also accepts the timing fields
`delay` (seconds) and `wait` (4.3). `Render`'s `target` accepts a CSS
selector string (all matches) and defaults to the calling instance
(4.3). On an instance-less compatibility / no-JS HTTP request, a targetless
render instead supplies the whole response body; the internal compatibility
translation consumes it before any action reaches a client.

Return-value rules, strict by design (ambiguity is refused, not guessed):

| Return | Meaning |
|---|---|
| `None` | Acknowledged, no actions. If the handler mutated the state, the response still refreshes the client's token (the `state` action, 4.3). In debug mode the runtime logs a hint when state changed but nothing visible was returned. |
| an action instance | That action. |
| a `list` / `tuple` | Ordered actions; each element coerced by these same rules. Empty means acknowledged. |
| a `CitryElement` / `CitryRender` | `Render` targeting the calling instance. The element can be any component; you are building a fresh tree, not resuming the old one. |
| a `dict` | `Data` (the one scalar convenience: a dict cannot be mistaken for an action or an element, and it is the overwhelmingly common typed-endpoint return). |
| anything else (`str`, numbers, custom objects) | A pointed error naming the fix. A string is ambiguous (HTML or JSON?) so it is never guessed: use `actions.Data(s)`, and HTML only ever comes from rendering a component. Custom classes either wrap in `Data(...)` or register a **result resolver** once (6.2), after which returning them bare works. |

One rule behind the element coercion, stated because it answers the
natural question at the call site ("does this replace the whole component
or just the element that triggered the event?"): **a returned element is
the calling instance's next rendering.** The unit of server-side
rendering is the component, so the unit of replacement is always the
component instance, never the triggering element (the server could not
render "just the input" if it wanted to; an input is not a component).
Anything other than the calling instance is addressed explicitly
(`Render(..., target=...)`). Mechanically the morph applies the new
rendering as a minimal diff (5.3), so the untouched parts of the DOM,
including the focused control that triggered the call, stay in place.
For a classic form or pasted compatibility URL with no calling instance,
returning an element is also valid: its HTML is the complete HTTP response,
not a client-side morph action.

```python
from citry.ext.events import actions

# OrderState is a root State class with a render() recipe (3.2);
# AppContext comes from the _context hook (3.6); CartBadge is a component.

class CartIn:
    product_id: int

class Events:
    def save(self, state: OrderState):
        order = create_order(state.draft_id)
        return [
            actions.Dispatch("order-saved", {"id": order.id}),
            actions.Redirect(f"/orders/{order.id}"),
        ]

    def add_to_cart(self, data: CartIn, context: AppContext):
        cart = add_item(context.user, data.product_id)
        return [
            actions.Render(
                CartBadge(count=cart.count),
                target="#cart-badge",
            ),
            # dict coerces to Data -> resolves caller's promise
            {"count": cart.count},
        ]

    def refresh(self, state: OrderState):
        # element coerces to Render on this instance
        return state.render()
```

Multi-component updates have two tiers: same-response self-addressed
renders (`Render(..., target=...)`) when the server knows the target, and
loose coupling (`Dispatch("cart-updated")`, with the listener reacting
via `onEvent` in JS or
`x-init="$onEvent('cart-updated', () => $sendEvent('refresh'))"`
in the template, 5.5) when it does not.
Both are the field's converged answers, and the audit found five-plus
ready call sites per app area for `Redirect` alone (production mutations
today end in full page reloads for lack of exactly these actions).

`RouteResponse(...)` remains the HTTP-transport, per-event-route escape
hatch (file downloads, custom content types). Its handler uses
`@event(bundle=False)` and leaves State unchanged because the raw response
bypasses the result envelope and its state-token refresh. It is rejected with
a clear error on the batch endpoint and non-HTTP transports.

**The import paths are governed by one public-API rule.** Public is:
what the root `citry` package exports, plus what each extension's and
contrib module's root exports (`citry.ext.events`, `citry.contrib.fastapi`).
Any deeper module is private by convention. No underscore prefixes are
needed, because the public `__init__.py` files are **pure re-export
surfaces** (`__all__` and imports, never logic), so API definition and
implementation never share a file. The docs build points griffe at
exactly these entrypoints, making the API reference the enforcement of
the rule (docs as contract). The complete list of public entrypoints is
therefore three shapes and nothing else: `citry`, `citry.contrib.<name>`,
and `citry.ext.<name>`. (The extensions directory itself is renamed
`citry/extensions/` to `citry/ext/`, the SQLAlchemy precedent; a
mechanical pre-1.0 task alongside the v0 substrate work.)

There are **no built-in events** and no framework-initiated re-render: the
audit showed handlers already decide and perform the rendering themselves,
so the design gives them the full freedom to render anything (or nothing)
rather than privileging self-re-render. A component that wants a refresh
or a bind-flush event defines one, typically one line reusing the
`State.render` convention.

### 3.5 Per-handler and per-component configuration

Per-handler config is the optional `@event` decorator; bare methods get
defaults. Per-component config is **underscore-prefixed class attributes
on `Events`**, merged through the substrate's three-level defaults for
free. The underscore is load-bearing: config lives in the framework
namespace, so every public name remains available as an event (a
component can have an event called `guard` or `methods`). Defining a
reserved underscore name IS the act of configuring it, the same
mechanism as `_context` (3.6) and State's `_public` / `_model` (3.2).

```python
from citry.ext.events import EventError, event

class DocState:
    doc_id: int
    title: str = ""

    def render(self):
        return Document(doc=load_doc(self.doc_id), title=self.title)

class WordCountIn:
    doc_id: int

class Document(Component):
    # Kwargs and state_data as in 3.2

    State = DocState

    class Events:
        def _guard(self):
            # _context has already run;
            # guards see the ambient attributes
            user = self.context.user
            if not user.can_edit(self.state.doc_id):
                raise EventError(
                    "You cannot edit this document.",
                    status=403,
                )

        @event(debounce=400)
        def autosave(self, state: DocState):
            save_draft(state.doc_id, state.title)

        # read-only, cacheable;
        # omits state, so its URL carries no token
        @event(methods=("GET",))
        def word_count(self, data: WordCountIn) -> dict:
            return {"words": count_words(data.doc_id)}

        def refresh(self, state: DocState):
            return state.render()
```

The component-level config surface, exhaustively:

| Attribute | Type / signature | Default | What it does |
|---|---|---|---|
| `_guard` | `def _guard(self): ...` inline, or `_guard = my_check` assigning any `callable(events)`; both bind identically. Receives the Events instance with the ambient per-call attributes populated (`self.state`, `self.context`, `self.request`, `self.event`; the raw unvalidated payload is `self.event.args`). Raise `EventError` (e.g. `status=403`) to deny, return to allow. It takes no `data` because one guard covers handlers with different schemas; payload-dependent authorization belongs in the handler body, where `data` is typed. | engine default from `extensions_defaults["events"]`, else none | Authorization for every handler of the component. Resolution is most-specific-wins: `@event(guard=...)` beats `_guard` beats the engine default (7.4). |
| `_context` | `def _context(self) -> Any`; receives the Events instance (request populated, guards not yet run) | engine default from `extensions_defaults["events"]`, else none | Builds the per-call `context` injectable (3.6). Usually configured once, engine-wide. |
| `_csrf` | `"auto"` \| `False` \| `callable(request) -> None` (raise to reject) | `"auto"` | HTTP CSRF policy for the component's handlers (7.4). Beneath any setting sits the always-on baseline: the `X-Citry-Events` header requirement (HTML forms cannot attach custom headers, and cross-origin JS attempting it hits a CORS preflight the browser blocks) plus `Origin` / `Sec-Fetch-Site` same-origin checks (browser-set, unforgeable by page JS). `"auto"` adds the host token where the host has one (Django); `False` drops only citry's own token layer (the baseline never turns off, and a host framework's token check, like Django's `CsrfViewMiddleware`, is governed by the host and stays on, 7.4); a callable replaces citry's token check and runs on top of the baseline and any host check. |
| `_methods` | tuple of HTTP method names | `("POST",)` | The allowed methods for handlers that do not set `@event(methods=...)`. GET opts a handler into read-only, cacheable-in-principle (served `no-store` until GET caching lands, section 16), pasteable-URL calls (7.4). |
| `_debounce` / `_throttle` | `int`, milliseconds | none | Component-wide client-timing defaults; see the `@event` row below for the mechanics. |
| `_topics` | tuple of topic-name templates formatted from State fields, e.g. `("project:{project_id}",)` | `()` | v2 server push (section 8): the serializer formats and signs these at render time; a client can subscribe only to topics it was handed. |

State's own meta lives on State (`_public` / `_model`, sections 3.2 and
7.2), not here: Events holds handlers, State holds state.

The per-handler decorator, exhaustively (kwargs need no underscore, they
live in no shared namespace):

| `@event(...)` key | Type | Default | What it does |
|---|---|---|---|
| `name` | `str` | the method name | Wire name override: rename the Python method without touching templates. |
| `methods` | tuple of HTTP method names | the component's `_methods` | Per-handler method allowlist. |
| `guard` | same signature as `_guard` | the component's `_guard` | Per-handler authorization; most specific wins, it replaces rather than stacks. |
| `csrf` | same values as `_csrf` | the component's `_csrf` | Per-handler CSRF override (e.g. `csrf=False` on a token-authenticated endpoint). |
| `debounce` / `throttle` | `int`, milliseconds | the component's `_debounce` / `_throttle` | Client-side timing instructions, not server machinery: they travel in the class descriptor (4.4) and the runtime holds calls back before sending, so the server never sees the suppressed ones (server-side rate limiting is the `on_event` hook or a guard). An explicit modifier on a binding overrides both levels. |
| `latest_wins` | `bool` | `False` | Newest-wins for this handler on one instance, opt-in (5.6): when a newer call to this handler enqueues from the same anchor, queued-not-sent predecessors are dropped before sending, and an in-flight predecessor is abandoned (its response's actions are dropped on arrival); either way the predecessor's promise rejects with the `superseded` reason and the drop event fires (the settle table, 5.2). Opting in is the author's statement that overlapping runs of this handler are safe (idempotent), because the server still executes every call it received. The default preserves every call: a killed save is data loss, so newest-wins is never a default (14.3.4). Like the timing hints, it travels in the class descriptor (4.4), which is how the runtime knows it at queue time. |
| `bundle` | `bool` | `True` | Whether calls to this handler may share a batch envelope with other calls that become eligible together at dequeue (5.6). `bundle=False` sends alone, for handlers that should never ride a shared request (a slow export next to fast toggles). It travels in the class descriptor (4.4) like the timing hints. |

`latest_wins` and `bundle` are per-handler on purpose, never per call
site: two call sites that need different overlap or bundling semantics
are two handlers, which keeps a binding's behavior readable from the
handler it names.

Two per-handler knobs from earlier drafts are **derived, not
configured**. Token requirement follows the signature. A handler
declaring `state` on a component with no State class is a
class-definition error. On a State-declaring component, POST calls
always carry the token: pending two-way updates ride the next call and
must be verified, applied, and re-signed whether or not the handler
reads state. GET calls carry the token in the query only when the
handler declares `state`, which is what keeps read-only GET URLs
pasteable and token-free. Token expiry is a property of the one shared
State, not of any handler, so it lives on State meta (`_max_age`, 3.2
and 7.1) alongside `_storage` and `_max_bytes`.

Engine-wide configuration splits along one line, because Events is a
built-in extension the user never instantiates. Config that a component
can override rides `extensions_defaults["events"]` (default `_guard`,
default `_context`), the mechanism that exists precisely
for configuring extensions without touching them. The envelope size cap
(`_max_envelope_bytes`) also rides `extensions_defaults["events"]` but
is engine-wide only, with no per-component override: it guards the
transport before any component resolves, and one batch envelope spans
components, so declaring it on a component's `Events` class fails at
class definition. Engine-wide registries
and secrets are `CitrySettings` fields: `secret` (7.1),
`event_result_resolvers` (result resolvers, 6.2), and
`event_payload_codecs` (payload codecs, 6.2).

### 3.6 Per-call context: the `_context` hook

Most real handlers need request-derived context: the current user,
permissions, a per-user API client (the audit found `request.user` or
session reads in 25 of 38 production handler bodies). The GraphQL-server
pattern fits: one function derives a context object from the incoming
call, and every handler receives it.

```python
# receives the Events instance pre-dispatch
def build_context(events):
    user = get_user(events.request)
    return AppContext(
        user=user,
        api=monday_client_for(user),
    )

citry = Citry(
    extensions_defaults={
        "events": {
            "_context": build_context,
        },
    },
)
```

- `_context` is a method on `Events` (underscore-prefixed, so it can never
  be mistaken for a handler). It is usually configured **once, globally**,
  via `extensions_defaults` (the Apollo-server shape: all handlers across
  all components share one context function), and any component can
  override it like any config.
- Its return value is the `context` injectable in handlers (and
  `self.context` for guards and resolvers, which receive the instance).
  No hook configured means the context is `None`.
- Call order per dispatch, cheapest rejection first: verify token,
  validate args against the signature (pure, no I/O), run `_context`
  (may touch the DB), run guards (which read `self.context`), run the
  handler.
- Settings are frozen at construction (the substrate's immutability
  rule), and config classes are rebuilt when component classes are
  defined, reading `extensions_defaults` at that moment. So there is no
  lazy configuration of the module-level default instance; an app that
  wants engine-wide events config constructs its own `Citry`, as above,
  which is the recommended shape anyway.
- For exotic transports, `_context` is also the normalization layer: it
  sees `self.request` and `self.event.transport` and produces whatever
  app-level object makes handlers transport-agnostic.

Note on template globals, recording a corrected confusion: an earlier
draft had a hook to "recompute template globals" for event-time renders.
That conflated two things. Template globals apply to event-time renders
the same way they apply to any render (a returned element goes through a
normal render pass); there is nothing to recompute, and event handlers do
not necessarily render at all. What handlers actually need is per-call
request-derived context, which is `_context`.

### 3.7 Errors

- **Validation failures** (args do not bind, a two-way binding update
  fails its State field's type, the state token is invalid or stale) return structured error
  envelopes with real HTTP statuses (422, 403, 409), never a host 500.
- **User-raised**: `raise EventError(message, fields=None, status=422)`.
  `fields` is the per-field error map the client receives, keyed by
  data-schema field names (`{"email": "Enter a valid email address."}`)
  and surfaced as `$error.fieldErrors` for inline display next to inputs,
  while `message` is the human summary for a toast or banner. Schema
  validation fills the same map automatically on `invalid_args`. One
  error class with a status argument covers forbidden, not-found, and conflict
  without an exception zoo (a user-raised 403 carries the wire code
  `forbidden`, 404 carries `not_found`, 409 carries `conflict`, and any
  other status carries the catch-all code `error`; the protocol spec's
  error-code table is the authoritative list).
- **Unexpected exceptions**: caught by the dispatcher, logged, fired
  through the extension's own `on_event_error` emit hook (a Sentry
  extension can observe or replace the response), then answered as a
  generic 500. The exception text rides only in debug mode; never a
  traceback on the wire.
- **Observability**: the extension owns `emit()` hooks in the established
  pattern:
  - `on_event` fires before the handler (after token verification
  and arg validation, before `_context` and guards; `result="first"`, so
  a policy extension can veto or answer, and it is where rate limiting plugs in),
  - `on_event_result` fires after the handler (`result="map"` over the
  encoded actions list),
  - `on_event_error` fires on an uncaught
  handler exception. No new core hooks.

### 3.8 URLs

Routes, declared via `Extension.urls` and mounted under
`<prefix>/ext/events/`. Component dispatch lives under its own `e/`
segment, so the extension can add root-level endpoints forever without
colliding with component addressing:

```
POST      ext/events/call               batch endpoint
                                        (envelope w/ calls[])
GET       ext/events/runtime.js             events JS code
GET|POST  ext/events/e/{class_id}/{event}   per-event dispatch
```

The per-event route (`ext/events/e/{class_id}/{event}`) is one fixed
parametrized pattern resolved through the registry per request (never one
route per component), so it survives Django's routing, which snapshots
the URL set once when `urlpatterns()` is built. `class_id` is used
rather than the registered name because it always exists. The URL is
authoritative: on the per-event route, a body naming a different
component or event is rejected; the batch endpoint is where calls name
their own targets.

Every handler therefore has a real URL that host middleware, rate
limiters, access logs, curl, and OpenAPI all see:

```
curl -X POST http://localhost:8000/citry/ext/events/e/Counter_a1b2c3/increment \
  -H 'content-type: application/citry-events+json' -H 'x-citry-events: 1' \
  -d '{"protocol":"citry-events/1","requestId":"r1","calls":[{"componentClassId":"Counter_a1b2c3","handlerName":"increment","callerRenderId":"c9zk1q00","args":{},"stateToken":"cev1..."}]}'
```

`component.events.url("submit", query=..., fragment=...)` builds event URLs
during render; module-level `get_event_url(Cls, "submit", ...)` does the
same anywhere. Both sit on `Citry.build_url` and the ported `format_url`
(this is the earmarked first caller), and raise the standard pointed error
when no integration is mounted. The audit found 116 references to the old
`get_component_url` doing exactly this job by hand.

`call` is the batch endpoint: one POST carrying a multi-call envelope.
Its first v1 consumer is the event queue's dequeue bundling (queued
events that become eligible together ride one envelope, 5.6);
client-side same-tick coalescing (merging calls made in the same JS
tick into one request) remains a v2 feature. The endpoint exists from
day one so neither needs a protocol change. Method configs govern the
**per-event route only**: batch calls are envelope items, not HTTP
requests, so a GET-configured handler invoked via batch loses nothing
but cacheability and gains the batch POST's CSRF coverage.

---

## 4. The wire protocol: citry-events/1

The protocol is the language-neutral shared surface (extensions are
host-language-specific by design, the wire and the client runtime are not),
so nothing in it is Python-shaped: named args only, no expression strings,
no Python types.

### 4.1 The protocol package

`packages/protocol/events/v1/` is the source of truth, merged before any
server code:

```
spec.md                  # prose spec, normatively worded
call.schema.json         # JSON Schema 2020-12 for the call envelope
result.schema.json       # for the result envelope
descriptor.schema.json   # for the class descriptor (4.4)
manifest.schema.json     # for the complete browser manifest (4.4)
tests/                   # golden exchanges plus valid/invalid descriptor
                         # and manifest examples, dynamic fields declared
validate.py              # dependency-free package self-check
```

Every server binding (Python now; JS/PHP/Go later) must pass the same
example suite; the client runtime's tests replay the results into a
DOM harness. This is the repo's observe-then-lock testing discipline (run
the real code, observe its output, lock that output into the assertion)
applied to the protocol: any protocol change lands as an example and schema
change in the same PR. Golden exchanges declare `dynamic_fields` for values
that necessarily change between renders, such as render IDs, state tokens,
and rendered HTML. Error message texts, including the per-field
`invalid_args` messages, are authored in the examples and are contract from
then on.
The state token is exempt from cross-binding conformance by design: it
is opaque, minted and verified by the same binding.

### 4.2 Call envelope (uplink)

```json
{
  "protocol": "citry-events/1",
  "requestId": "r_8f2k1c",
  "capabilities": {
    "swaps": ["replace", "morph"],
    "actions": ["render", "data", "state", "event", "redirect", "url"]
  },
  "calls": [
    {
      "componentClassId": "TodoList_a1b2c3",
      "handlerName": "add",
      "callerRenderId": "c9zk1q00",
      "args": { "text": "Buy milk" },
      "stateToken": "cev1.eyJ...9mYt",
      "stateUpdates": { "query": "shoes" },
      "sendSequence": 4
    }
  ]
}
```

- `protocol`: exactly `citry-events/<major>`; unknown majors are rejected.
- `requestId`: client-minted correlation id, echoed back (needed for WebSocket
  multiplexing, harmless over HTTP).
- `capabilities`: what the client runtime can apply, keyed `swaps` (swap
  strategies) and `actions` (action kinds). The server never emits a swap
  or action outside the advertised set; it downgrades instead (`morph` to
  `replace`). An absent field means the **protocol baseline**: one fixed
  constant per protocol major, defined in the protocol package's spec and
  tests. For v1 that is every swap except `morph` plus all six v1
  action kinds, named `CAPABILITIES_BASELINE_V1`. The server therefore
  holds a single constant per major, not a table of runtime versions; the
  dispatcher applies it at encode time. This is what lets a stale cached
  runtime survive a deploy: after a release ships `morph`, a browser
  still running yesterday's cached runtime advertises nothing beyond the
  baseline and receives `replace`.
- `calls`: an array from day one (one to sixteen entries; the cap is
  part of the protocol schema, 7.4), so batching is a client feature,
  not a protocol change. The v1 client sends one call per gesture; the
  event queue bundles queued calls that become eligible together into
  one envelope at dequeue (5.6), and same-tick coalescing (merging
  calls made in the same JS tick) is a
  v2 client feature. Every canonical call names `componentClassId`,
  `handlerName`, and `args`. On the per-event route, transport adapters build
  those fields from the authoritative URL; an explicit canonical envelope
  must match it.
- `callerRenderId`: the calling component occurrence's render ID, when known; the server
  uses it to self-address render and state actions, and `event` actions
  a handler returns without an explicit target (4.3). It is absent
  whenever the caller is not the runtime acting for a DOM instance: a
  curl or API client hitting a data handler's URL (the Component.Ninja
  use), a hand-written form posting to a per-event URL without the
  hidden caller field, or host-page JS invoking a handler without a
  component. Such calls still run; they just have no default
  self-render target on the JSON/wire path (handlers address targets
  explicitly) and no client registry entry to refresh. The compatibility /
  no-JS HTTP path is the one exception: a targetless render becomes the
  whole HTML response body, so it needs no client-side target.
- `args`: a required JSON object, named keys only. Validated server-side.
- `stateToken`: the opaque state token, echoed verbatim. Absent for stateless
  handlers.
- `stateUpdates`: two-way binding updates (`_model` State fields, 7.2)
  carried by this call. The designed flush is the binding's named handler
  (5.1). When another call from the instance fires while an update's
  debounce timer is still pending, that call carries the update too,
  closing the stale-state race.
- `sendSequence`: a monotonic counter kept per **anchor** (the stable,
  client-internal identity of one interactive DOM position, 5.5), the
  out-of-order guard. The runtime increments it on every send from an
  anchor and remembers the highest epoch it has applied there; the
  response echoes the request's value. The browser implementation calls the
  same counter an epoch internally; `sendSequence` is the wire name.
  A response's instance-mutating actions (the self-targeted render,
  the `state` token refresh) apply only when its epoch is **strictly
  greater** than the anchor's highest-applied; otherwise they are
  dropped, while its `data` still resolves the caller's own promise
  and non-instance actions apply normally. Over HTTP's at-most-once
  delivery, dropping at equal-or-lower behaves exactly like dropping
  only the lower ones (a response's own epoch becomes the highest
  applied the moment it applies), and the comparison is stated
  strictly because that is the form one bookkeeping move can lean on:
  setting an anchor's highest-applied to its send counter invalidates
  every in-flight call at once, which is exactly what the
  keyed-linking horizon cut does (5.5; the epoch-comparison
  restatement in the "Machinery every option needs" list of
  [`events_research/analysis-nested-anchor-continuity.md`](events_research/analysis-nested-anchor-continuity.md)).
  The classic case: two rapid
  debounced updates, the network delivers the second response first,
  and without the guard the first response would overwrite newer state
  with older (a shipped bug class in unicorn and Livewire). The component
  id changes on every render (5.5), so the guard tracks the anchor, not
  the id; the epoch itself stays an opaque echoed field the server never
  interprets, so moving its bookkeeping to the anchor changes nothing on
  the wire. The event queue (5.6) serializes sends from overlapping
  anchors client-side, so in practice the guard's work narrows to what
  the queue cannot see: `wait: false` sends, responses arriving from
  unrelated anchors' calls, and future transports with different
  delivery
  orders. The guard itself is unchanged; it is the net beneath the
  queue.

Explicitly not in the envelope: CSRF tokens, cookies, auth (transport
concerns, section 6), and executable expressions of any kind. Events are
referenced by name only; argument values are JSON literals. Beyond the
security record (7.6), inline code in bindings would also visually mix two
different worlds that only look alike: `{{ }}` expressions evaluate against
render-time template data, while a handler runs later against State. A
syntax that blurred which world a snippet runs in would mislead readers of
the template.

### 4.3 Result envelope (downlink)

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
          "swap": "morph",
          "html": "<button data-cid-c9zk1q00 ...>...</button>
            <script type=\"application/json\" data-citry>...</script>
            <script type=\"application/json\" data-citry-events>...</script>"
        },
        {
          "action": "data",
          "value": { "id": 17 }
        },
        {
          "action": "event",
          "eventName": "todo:added",
          "detail": { "id": 17 },
          "target": "render:c9zk1q00"
        }
      ]
    }
  ]
}
```

`results[i]` answers `calls[i]`; each is `{ok: true, actions: [...]}` or
`{ok: false, error: {...}}`. **All actions are resolved in the browser by
the events runtime; the wire itself is always a 200 envelope** (only
per-call `error.status` mirrors onto the per-event route's HTTP status so
logs and middleware read correctly). Nothing user-facing is expressed as
HTTP semantics: a redirect is an action, not a 30x, both because `fetch`
follows redirects transparently and because actions must mean the same
thing arriving over WebSocket or SSE. Action application is observable and
interceptable client-side: each action fires its `citry:events:*`
lifecycle event first, and `Citry.events.applyActions` is a public entry
point, so a page can override what any action does for its instances.

The vocabulary is the industry-converged self-addressed list (Turbo
Streams and htmx out-of-band swaps are the same shape):

| Action | Fields | Meaning |
|---|---|---|
| `render` | `target`, `swap`, `html` | Insert or update HTML. `html` is a complete citry fragment (markup plus the inert `data-citry` and `data-citry-events` manifest tags), so the existing MutationObserver machinery loads assets and re-fires `$component` with zero new insertion mechanics. |
| `data` | `value` | Resolve the calling instance's promise with this JSON value. At most one per result: a handler whose return would encode two `data` actions is an encode-time error naming the fix (two bare dicts in one list is semantically contradictory, which promise value wins?), unlike the trailing-after-redirect case, whose actions are individually valid and merely unreliable, so it warns. |
| `state` | `targetRenderId`, `stateToken` | Replace the stored state token for a rendered component occurrence whose handler mutated state without re-rendering; the server places it before the handler's own actions. (A `render` action needs no companion; the fresh fragment's manifest carries the new token.) Client rule, either carrier: the runtime applies a result's token refresh to its registry before applying the actions array, so user code running mid-application (a dispatch listener that immediately sends) already carries the fresh token. |
| `event` | `eventName`, `detail`, `target` | Dispatch one bubbling DOM CustomEvent under the **exact given name** on the target instance's first live root, or on `document`. A multi-root or mirrored instance uses one canonical root deliberately: dispatching the same logical action on every root would duplicate document/global delivery and `onEvent` callbacks. Raw names are the field's converged interop choice (Livewire and htmx both fire developer-chosen names verbatim); `citry:*` is reserved for the runtime's own events, and the documented best practice is prefixing with the component name (`MyCard:submit`, the BEM idea applied to events). A handler-returned `event` action with no explicit target is self-addressed by the server at encode time to the caller's `callerRenderId`; only calls without a rendered caller produce a document-targeted dispatch. |
| `redirect` | `url` | Navigate the page. |
| `url` | `url`, `mode` | History push or replace without navigation. `PushUrl` and `ReplaceUrl` are its two producers; the client accepts only exact `push` or `replace` modes, preserves `history.state`, and skips invalid or browser-rejected updates without interrupting later actions. |

Targets: a plain string is a **CSS selector** and applies to **all
matches** (`querySelectorAll`, so comma unions work natively; the
all-matches rule is the field's unanimous answer, per Turbo's `targets`,
htmx's out-of-band selector swaps, and Datastar). A selector matching
nothing logs a zero-match warning instead of silently doing nothing. The
optional `render:<render id>` form targets a specific rendered component occurrence
(the elements carrying its `data-cid-<id>` marker); it is what the
runtime uses for self-renders, and `render:` is a reserved prefix. Its ID uses
the case-safe `^[a-z0-9_-]+$` render-ID grammar, and the same constraint
applies to `state.targetRenderId`. The
client rejects an unsafe suffix before constructing a `data-cid-*` selector.
A selector that targets a non-component region makes
that region's structure part of the page's contract; prefer instance
targets where possible. Swaps: `morph`
(default when the client advertises it), `replace`, `inner`, `append`,
`prepend`, `remove`, `none`.

**Ordering is faithful, including `redirect`.** Actions apply strictly
in list order; the framework never reorders or drops them. Other
frameworks reorder because their transports cannot preserve order
(header maps, separate structs for dispatches and redirects); an ordered
JSON list can preserve it, so it does, per the design's
explicit-and-deterministic rule.
The caveats are documented instead: actions listed after a `redirect`
race the navigation and are unreliable by nature, so the dispatcher
emits a debug warning when anything follows a `redirect` (and when a
`render` coexists with one: the rendered content is never seen). A
dispatch fired just before a redirect reaches listeners on the outgoing
page, which is usually not what a toast wants; the tool for that is the
timing fields below.
The dispatcher emits the same encode-time debug warning when a
self-addressed action follows a selector-targeted render: the selector
may resolve to a region that contains the caller, and that earlier
render then retires the caller's anchor, so the later self-addressed
action drops at apply time (per-action liveness, 5.5 machinery item
4). The authoring note the docs teach for this class: dispatch before
the render that destroys its audience, so an `event` action meant for
a region is listed ahead of the action that removes it.

**Timing fields.** Every action carries two optional fields:
`delay` (seconds, float, default 0) waits before applying the action,
and `wait` (default `true`) decides whether the queue holds for it.
With `wait: true` the delay is blocking, preserving order; with
`wait: false` the action is scheduled and subsequent actions proceed
immediately. `actions.Redirect(url, delay=5, wait=False)` lets a
farewell toast be read while later actions still apply. A scheduled
action (a nonzero `delay`, or `wait: false`) re-resolves its target,
re-runs the per-action liveness checks (5.5 machinery item 4), and,
when it is instance-mutating, re-runs the epoch comparison (4.2) at
the moment it fires, never at response arrival: it applies to the DOM
as it is then, which may have changed while the action waited, and an
action fresh at arrival but stale by fire time drops instead of
applying old state (the concrete case: a delayed token refresh firing
after a newer response already landed).
(`delay` is
seconds because action timing is UX-scale; client input debounce stays
in milliseconds per that convention's own field norm. The Python kwarg
is `wait` rather than a raw `async` flag because `async` is a reserved
word and the house rule prefers positive names.)

The action set is **closed in v1**. The browser validates the complete result
and every action before applying the first one; an unknown kind, swap, missing
field, or extra field rejects the response atomically. Custom client behavior goes through
the `event` action: dispatch a named event and let the page's or
component's own JS decide what happens (Tetra's open server-calls-your-JS
channel, retroactively whitelisted down to nine methods after shipping,
is the cautionary tale). If a real consumer needs an extension, design that
protocol point then rather than treating unknown fields as an implicit
extension API. Interception never requires custom actions: `on_event_result` (server) and
`applyActions` plus the lifecycle events (client) see every action as
data.

Error results carry `{status, code, message, fieldErrors?}` with stable string
codes, each with a fixed status except the catch-all: `invalid_args`
(422), `invalid_state` (403, a malformed token), `stale_state` (409, an
expired or rotated-out token), `unknown_event` and `unknown_component`
(404), `forbidden` (403), `not_found` (404), `conflict` (409), `error`
(the catch-all for user-raised statuses with no dedicated code, 3.7;
it ships the raised 400-599 unchanged), `csrf_failed` (403),
`payload_too_large` (413), `protocol_mismatch` (400), `handler_error`
(500); the protocol spec's error-code table is the authoritative list.
When a token's
signature verifies against no current secret, the payload decides
between the two token codes: a payload that still parses as a
well-formed token (valid base64 and JSON with the version, component
class, and state fields) answers `stale_state`, because a token signed
by a rotated-out secret looks exactly like that; anything less (bad
base64, bad JSON, wrong version, missing fields) answers
`invalid_state`. A signature-only tamper is indistinguishable from an
honest rotated-out token, so it takes the 409 path; the payload's
values are only used to pick the error code, never trusted before the
signature verifies. On the per-event route
the HTTP status mirrors the call's status; the batch endpoint answers 200
with per-call statuses inside (one batch can mix outcomes). `fieldErrors` is
the per-field error map, surfaced client-side as `$error.fieldErrors` (5.5).

### 4.4 How the state token reaches the client

Alongside the existing `data-citry` asset manifest, serialize emits a
second inert JSON tag, `data-citry-events`, for every page or fragment
containing an Events-declaring component:

```html
<script type="application/json" data-citry-events>
  {
    "protocol": "citry-events/1",
    "clientGraphRevision": null,
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
        "publicState": {"query": "shoes", "show": "open"}
      }
    ]
  }
</script>
```

Manifest entries are named JSON objects embedded directly in the inert script
block. The server escapes `<` as `\u003c`, so application State cannot close
the script tag. `clientGraphRevision` links the Events sidecar to the ownership
graph from the same render, or is `null` when no graph was emitted.

`componentClasses` carries handler names and browser hints. Each handler has
`httpMethod`; the optional non-default hints are `usesState: true`,
`debounceMilliseconds`, `throttleMilliseconds`, `latestCallWins: true`, and
`allowBatching: false`. `writableStateFields` carries a narrowed
`State._model` capability in declaration order. It is omitted when `_model`
equals `_public`, while an explicit empty list means all public State is
read-only.

`componentInstances` carries each occurrence's `renderId`, class reference,
opaque `stateToken`, and `publicState`. `publicState` seeds one-way bindings
and `$state` reads; non-public fields appear nowhere in it. A stateless record
uses `stateToken: null` and an empty `publicState` object.

The runtime rejects an out-of-model `$state` write before changing reactive
State or queueing an update; the server independently enforces the same list.
The server stays the authority, the descriptor is a client convenience. A re-rendered
fragment carries its own manifest, so morphing it in updates the client
registry automatically; fragments stay self-contained however they are
delivered. (A valued root-element attribute was considered and rejected:
it would need a core serialization change, while the manifest tag reuses
the shipped pattern with no core change; see section 14.)

### 4.5 Versioning

The major lives in the protocol string. Every fixed v1 structure is strict:
missing and extra fields, unknown action kinds, swaps, capabilities, and error
codes are errors. Only documented application-data bags remain open. Until
the v1 beta freezes, incompatible corrections may change v1 in place as long
as the spec, schemas, examples, server, browser, tests, and current docs move
together. After that freeze, an incompatible wire shape starts v2.

---

## 5. The client API

The pinned Alpine/Events bundle is served at `ext/events/runtime.js` and
injected automatically through the existing `on_dependencies` hook whenever
a rendered page or fragment contains a client-active ownership graph. The
bundle embeds **AlpineJS as its reactivity layer** (decision record 14.1.10)
and installs exact Alpine 3.15.x plus morph into the permanent
`Citry.alpine` broker. The broker owns the single startup, root selector,
init interceptor, mutation fan-out, magic dispatchers, morph entry point, and
duplicate-instance warning. Events-declaring components create Events
anchors; any instance with `$component` or client binding activity also
enters the general client-instance registry and gets the stable scope
described in 5.5. Components with none of those client surfaces pay no
initialization cost
(Alpine's startup is one synchronous DOM walk; the audited production
pages that froze on init are the motivating case). The DOM morph is
`@alpinejs/morph` (2.1 KB gzip, Livewire's production backbone), pinned
tightly. The morph spike, the proof-of-concept milestone of 13.2, is the
gate; vendored idiomorph is the recorded fallback if the spike's
assertions fail on it. Planned TypeScript
home: `packages/js/citry-client/`, the same track as the existing
runtime. The Alpine integration design (scopes, magics, `$state`
semantics, how the bindings ride on Alpine) is section 5.5.

### 5.1 The template vocabulary: `@c-*` events and `:c-*` bindings

Two prefixes to teach: **`@c-` binds events, `:c-` binds state.** They
look different because they are different things: an `@c-*` attribute
names a DOM event and the handler it sends, a `:c-*` attribute names a
State field a control is bound to. Both prefixes are citry-owned by
construction, so there is nothing to disambiguate. On a plain HTML element,
plain `@click`, `:class`, and every other attribute pass through to the final
HTML untouched by the citry compiler, and since citry ships Alpine (5.5),
inside any Alpine scope they are simply ordinary Alpine syntax. At a component
boundary, 5.5's narrow client binding rule applies: only `$c-props`, Alpine event
handlers, and Citry `@c-*` event handlers are relocated. `<c-element>` is an
HTML-element target, not a component boundary: it rejects `$c-props`, while
Alpine and Citry event/State bindings become attributes of its selected HTML
element and follow the ordinary element path. (The
citry prefixes include their trailing hyphen: `:class` and the other
Alpine bind shorthands do not match `:c-` and are never touched.) The five attribute channels stay visually distinct: `@c-*` events,
`:c-*` state bindings, `#c-*` framework metadata about node identity
and morphing (the block below), bare `c-*` dynamic expressions, and the `c-bind`
attribute spread ([`template_html_attrs.md`](template_html_attrs.md)); the event and
state channels never
touch the expression channels (verified in section 1.1), and `#c-*` is
its own grammar channel by construction.

| Attribute | Meaning |
|---|---|
| `@c-click="handler"` (any DOM event) | Send the named event to the server handler; optional args as one parenthesized Alpine expression evaluating to an object: `@c-click="rate({stars: 5})"` (5.1 Arguments). |
| modifiers | See the modifier table below. |
| `@c-poll.30s="handler"` | Send the named event on an interval, paused on hidden tabs. The interval is seconds, one time segment exactly (`.30s`; a second time segment is a template-load error rather than guessing whether units add or conflict). |

The modifiers, exhaustively, for a binding on one HTML element. A component-
boundary `@c-*` client binding follows 5.5's spike-proven `RootGroup` contract instead:
`.self` means any member root and `.once` is one shared client binding lifetime. A
pointed error is reserved for a concrete unsupported case rather than silently
becoming once-per-root.

| Modifier | Applies to | Effect |
|---|---|---|
| `.prevent` | event bindings | `preventDefault()` before sending. |
| `.stop` | event bindings | `stopPropagation()`. |
| `.self` | event bindings | Send only when `event.target` is the bound HTML element itself, ignoring events bubbling up from descendants. |
| `.once` | event bindings | The HTML-element binding fires at most once per element lifetime. |
| `.enter` / `.escape` | keyboard event bindings | Send only for that key; a template-load error on non-keyboard events. |
| `.debounce[.300ms]` | event bindings, two-way bindings | Hold until the trigger has been idle that long (bare `.debounce` is 250 ms); overrides the `_debounce` / `@event(debounce=...)` defaults (3.5). |
| `.throttle[.1s]` | event bindings, two-way bindings | At most one send per window (bare `.throttle` is 250 ms); same override chain. |
| `.lazy` | two-way bindings only | Use the control's committed-value event instead of its active event (table below); a template-load error elsewhere. |
| `.on:<event>` | two-way bindings only | Override the update event outright; required for controls the table below does not know; `.lazy` together with `.on:` is a conflict error. |
| `.30s` (time segment) | `@c-poll` only | The poll interval, seconds. |

`@c-poll` is settled by the same test that settles everything in this
table: a timer is a browser-side trigger naming a server handler, the
same shape as `@c-click`. Three further attributes from the drafts
(`@c-loading`, `@c-error`, `@c-on:`) failed that test in maintainer
review and were removed; their jobs live in the Alpine layer instead
(5.5): pending state is the `$loading` magic plus the per-trigger busy
attribute, error display is the `$error` magic with plain Alpine, and
server-event listening is `$onEvent`. The critique
record is in 14.1 and section 16's history.

**State bindings (`:c-*`).** The shorthand is the whole surface: the
attribute name carries the State field, which is always expressible
because State fields are dataclass fields (valid identifiers; case and
underscores survive because the rewrite is server-side, so browser
attribute-name lowercasing never sees the authored spelling). A longhand
was considered and rejected (14.1.9); `:c-field="..."` stays reserved if
one ever proves needed.

- **One-way** `:c-<key>`: apply the public State field's value to this
  control, server to client. It says nothing about updates; it is also
  what the runtime re-applies after morphs (5.3). Update-timing modifiers
  on a one-way binding (`.lazy`, `.debounce`, `.on:`) are a template-load
  error.
- **Two-way** `:c-<key>[.modifiers]="handler"`: a value turns the binding
  two-way, and the value names the handler that receives the update. On
  the control's update event, debounced or throttled per modifier, the
  runtime sends **one call** carrying both the field update and the named
  event, so the handler always sees fresh state, and who updates the
  state and when is spelled out in the attribute
  (`:c-query.debounce.300ms="refresh"`).
- **Which DOM event is "the control's update event"**: the fixed
  default table below, the same one two-way binding needs everywhere.
  `.on:<event>` overrides it outright (`:c-query.on:keyup.enter="search"`)
  and is **required** for controls the table does not know, so the table
  never needs to be user-extensible. The override changes the **flush**
  trigger, not draft detection: ordinary `input`/`change` activity marks a
  known control as an unsent draft immediately, so a render before the
  eventual `.on:` trigger cannot clobber what the user has typed.
- **State bindings are HTML-element-only.** A `:c-*` attribute on a semantic
  component target is a template-load error with guidance: a child binds its
  own State to controls in its own template. An `@c-*` handler is different:
  on a child component target it is a parent-owned events-up client binding (5.5). The
  handler name remains validated, queued, and loaded against the source parent
  Events instance; its optional argument expression is evaluated at the exact
  parent source. The child root is its physical DOM event carrier.
  `<c-element>` is the explicit exception because its semantic target is the
  selected HTML element: both event and State bindings use that element's
  normal resolved-attrs path.

The update-event table for two-way bindings:

| Control | Default (active) | With `.lazy` (committed) |
|---|---|---|
| text-like `<input>` (text, search, email, url, password, tel, number, the date and time family) | `input` | `change` |
| `<textarea>` | `input` | `change` |
| `<input type="range">` | `input` | `change` |
| `<select>`, `<input type="checkbox">`, `<input type="radio">` | `change` | template-load error where the type is statically known (`change` is already the committed value) |
| `<input type="file">` | not two-way bindable: files cannot live in State (6.2); a template-load error where the type is statically known, pointing at event args |
| custom elements, anything else | `.on:<event>` required |

A binding belongs to the nearest enclosing interactive component instance
(walk up to the closest registered `data-cid-*` marker).

**Framework metadata (`#c-*`).** The third citry-owned prefix names
neither a handler nor a State field: a `#c-*` attribute is an
instruction to the framework about the node itself, how it is
identified and morphed. It earns its own channel by the same test that
settled the rest of the vocabulary (14.1.9's taxonomy; the decision
record is 14.3.1): a key is not a browser event (`@c-` wrong), not a
State field (`:c-` wrong), and not render data destined for an HTML
attribute the author named (`c-` wrong; its value feeds the runtime's
identity machinery). The channel is **reserved for keying and morphing
features only**, never event call-site configuration (call-site knobs
stay on `@event`, 3.5). Two members exist:

- `#c-key="expr"`: the keying attribute. Expression-valued and
  server-evaluated like a `c-*` expression. On a plain element it is
  the morph pairing key; on a `<c-*>` component tag it is anchor
  continuity across a parent render. Both halves, including what the
  attribute compiles to, are specified in 5.3; the linking rule it
  drives is in 5.5. Keys must be unique wherever they compete, an
  authored contract, not a hint: among siblings (within one sibling
  window) for an element key, per class across one applied render
  region for a component key (5.3, 5.5).
- `#c-ignore`: the whole-subtree morph opt-out marker, bare (no value),
  valid on plain elements; it compiles to the runtime marker the morph
  hook reads (5.3). The marker is bare by design; an expression-valued
  form (a per-render condition deciding the opt-out) is reserved for
  later and deliberately unbuilt. On a `<c-*>` component tag the
  marker is a template-load
  error pointing at the fix (put it on an element inside the child's
  own template below the template's root element, or on a wrapper
  element), because an ignore on an instance root is unsupported, and
  a child template's own root element is an instance root too (5.3).

Unlike HTML-element `@c-*` and `:c-*`, which dissolve in the rewrite below,
`#c-*` is a real parser channel: the grammar, the AST, and the
compiler carry it, because `#c-key` holds a server-evaluated expression
that must ride the same expression machinery as `c-*`. That parser work
is its own work package (`events_plan.md` WP21), and the client wave
depends on it. The channel reserves nothing outside its prefix: plain
`key` and `c-key` stay completely ordinary (an HTML attribute and its
dynamic twin on elements, an ordinary `key` kwarg on component tags),
no kwarg is reserved, and no `c-bind` escape is needed. In v1 the
channel is template-authored only: a `#c-*` key arriving through an
attribute spread or dynamic attributes is a render-time error naming
the fix (author it on the tag in the template). If real component
libraries turn out to compose keys through spreads the way the audit
showed them composing `@c-*`, the `on_attrs_resolved` pass extends to
`#c-*`; that demand signal is the test.

**HTML-element syntax dissolves before it reaches the browser.** At template
load (`on_template_loaded`, string level, before parse and caching) the
extension rewrites each HTML-element `@c-*` and `:c-*` attribute into a
`data-cev-*` attribute carrying a base64 JSON spec: owner class id, handler
wire name, the raw arg expression when one was written, modifiers, and merged
per-handler debounce config. The shipped HTML is spec-valid and the internals
stay internal. For event bindings, the client runtime installs one delegated
listener per DOM event type at the document root and reads the specs at event
time, so the bindings survive morphs and cost nothing server-side. State
bindings apply through the instance's Alpine scope (one-way as a reactive
effect over `$state`, two-way as a `$state` write plus the named handler,
5.5). The client parses no Citry syntax at event time; arg expressions are the
one author-code part, carried verbatim and handed to Alpine's evaluator like
any Alpine attribute (5.1 Arguments).

A semantic component-target `@c-*` takes the client binding path instead. The template-
load pass validates a literal binding against the source component class but
leaves or encodes enough structure for `ComponentNode.render` to attach the
compiled spec and source identity to the selected child. Dynamic and `c-bind`
forms are validated when they resolve. They never become child kwargs or
select the child's Events anchor. `<c-element>` remains on the HTML-element
path described above.

The HTML-element rewrite is **two-stage**, because attributes can also be
contributed at render time: a parent may pass an attrs dict as a kwarg
(`<c-card attrs="{'@c-click': 'select'}">`) that the child spreads with
the `c-bind` attribute spread. The production audit found that spread
pattern pervasive with Alpine attributes. The template-load pass (above) handles
everything written literally in templates; a second pass in the existing
`on_attrs_resolved` hook (which fires per element after dynamic
attributes resolve) rewrites HTML-element `@c-*` / `:c-*` keys that arrive
through spreads or dynamic attributes. Component-tag client-binding keys instead join
the source-ordered client binding split in 5.5. Bindings contributed this way are
validated at that moment rather than at template load: still
server-side, still a loud error, just later.

**Validation is a hard error.** Because `@c-*` and `:c-*` can belong to
nothing else and there are no built-in events, validation has no special
cases. Every `@c-click`/`@c-poll` value must name a declared handler of
its owning source component (the name part, before any parenthesized
expression). Every `:c-*` key must name a **public** State field (and a
`_model` field when two-way, 7.2). Modifier combinations must parse:
unknown modifiers, a second `@c-poll` time segment, `.lazy` with `.on:`,
and `.lazy` on one-way bindings are all hard server-side errors. The `#c-*` channel
validates at parse, being a grammar channel: an unknown `#c-*` name, a
valued `#c-ignore`, a valueless `#c-key`, and `#c-ignore` on a
component tag are template-load errors like the rest. Literal bindings are
checked when the template loads (for inline templates, at class definition
time); dynamic/spread contributions are checked when they resolve. Both fail
with the best available template location. Arg expressions are Alpine
expressions, checked at event time when they run; the server's schema
validation backstops whatever they produce (3.3). No surveyed framework has compile-time checked
bindings; unicorn's troubleshooting docs are a catalog of the runtime
failures this removes.

Known v1 caveat, stated honestly: the load-time rewrite is textual and can
match binding-shaped text inside `<c-raw>` blocks, the same caveat class as
the shipped `$component` substring rewrite. The refinement path is a
node-level transform in `on_template_compiled` (an existing hook, no
grammar change); the authored syntax and the emitted `data-cev-*` contract
do not change when that lands.

**Arguments are Alpine expressions.** A binding value is a bare handler
name (`@c-click="save"`) or a handler name with one parenthesized
expression. citry does not parse the expression: the rewrite carries it
verbatim in the spec, and at event time the runtime evaluates it as an
ordinary Alpine expression **bound to the owning element**, so it sees
everything Alpine sees there: `$state`, `$el`, `$event`, and any user
`x-data` or `x-for` scope variables in play. It must evaluate to an
object; its keys become the fields of the wire args payload (the `data`
schema's fields), and anything else is a runtime error naming the
binding.

```html
<button @c-click="rate({stars: 5})">5 stars</button>
<input @c-input="search({query: $event.target.value})">
```

Per-item args in server-rendered loops ride data attributes through the
existing `c-*` expression channel and are read back in the expression
(`c-data-id="item.id"` renders `data-id="3"`, which the DOM exposes as
`$el.dataset.id`, 1.1):

```html
<c-for each="item in items">
  <li>
    {{ item.name }}
    <button
      c-data-id="item.id"
      @c-click="remove({id: $el.dataset.id})"
    >x</button>
  </li>
</c-for>
```

One element may carry several event bindings for different DOM events;
each evaluates its own expression against the same element (an e2e test
case, section 13).

**Form fields populate the data schema.** When the triggering event is a
form's `submit`, the runtime serializes the form's named controls into
the wire args payload (explicit expression args win on collision),
mirroring the urlencoded no-JS codec (6.2): the JS path and the no-JS
path deliver the same call. Control `name` attributes map to schema
fields, schema validation produces the 422 `fieldErrors` map for the error
display, and a failed submit re-renders nothing, so the DOM keeps the
user's input:

```html
<form @c-submit.prevent="submit">
  <input name="email">
  <input name="quantity" type="number">
  <button type="submit">Order</button>
</form>
```

```python
class OrderIn:
    email: str
    quantity: int = 1

class Events:
    def submit(self, data: OrderIn):
        ...
```
Forms therefore need neither State nor bindings (the form example in
section 2), and the old batched-updates channel does not exist:
`stateUpdates` on the wire carries two-way binding values only.

### 5.2 Component JS: `sendEvent` and `onEvent`

The `$component` callback object grows two members (extending the object
built at `citry.js:150`; no new source rewrites):

```python
class PointsIn:
    window: str = "7d"

class Chart(Component):
    class Kwargs:
        dataset_id: int

    class State(Kwargs):
        pass

    class Events:
        def points(self, data: PointsIn, state) -> dict:
            points_data = load_points(
                state.dataset_id,
                data.window,
            )
            return {"points": points_data}

    js = """
      $component(({ id, els, data, sendEvent, onEvent }) => {
        const chart = drawChart(els[0], data.initialPoints);

        const rangeEl = els[0].querySelector(".range");
        rangeEl.addEventListener("change", async (e) => {
          const result = await sendEvent("points", {
            window: e.target.value,
          });
          chart.update(result.points);
        });

        const stop = onEvent("dataset-changed", (data) => {
          chart.flash(data.id);
        });

        // cleanup: runs before this callback re-fires
        //          after a server update
        return () => { stop(); chart.destroy(); };
      });
    """
```

- `sendEvent(name, args?, opts?) -> Promise`: bound to this instance (id
  and state token resolved from the registry); resolves with the `data`
  action's value, rejects with a structured error (`{status, code,
  message, fieldErrors?}`). `opts` carries the per-call overrides: `timeout`
  (the `configure` field below) and `wait` (default `true`;
  `wait: false` bypasses the event queue, 5.6).
- `onEvent(name, fn) -> unsubscribe`: fires for `event` actions targeting
  this instance.
- **Teardown (new runtime capability)**: a `$component` callback may
  return a cleanup function; the runtime calls it before re-invoking the
  callback for the same instance (which happens after every server
  re-render, because the fresh fragment carries a fresh manifest entry).

The originally floated `$sendEvent(` / `$onEvent(` source rewrites are
deliberately not built: the rewrite mechanism binds a class id at cache
time but can never bind an instance, so a free-standing `$sendEvent` would
either guess the instance (wrong under `c-for` lists, the normal case) or
grow an element argument, at which point it is not simpler than the
context members. The capability is identical; the names live on as the
member names.

**Escape hatches outside component JS: the `Citry.events` global.** For
page scripts, other libraries, and tests, the same capabilities exist
unscoped on `Citry.events` (calls made before the runtime loads are
queued by the bootstrap stub, per Load ordering below):

| Method | What it does | Scoped counterpart |
|---|---|---|
| `Citry.events.send(target, name, args?, opts?)` | Send an event to any instance on the page. `target` is an instance id or an Element inside one; the runtime resolves the instance's registry entry (class, token, pending updates, epoch) and dispatches over the configured transport. Same promise contract as the scoped form. | `sendEvent(name, args?, opts?)` on the `$component` payload and `$sendEvent` in Alpine expressions: the same call with the instance pre-bound. |
| `Citry.events.on(name, fn)` | Listen for server-dispatched events (`Dispatch` actions) under their raw name, from any instance; returns the unsubscribe function. Sugar over `document.addEventListener` that unwraps `e.detail`. | `onEvent(name, fn)` / `$onEvent(name, fn)`: the same, filtered to events targeting that instance. |
| `Citry.events.configure(opts)` | Set page-wide runtime defaults once, from the host page; fields below. | None page-wide; a one-off override rides `sendEvent`'s `opts` (e.g. a per-call `timeout`). |
| `Citry.events.registerTransport(name, impl)` | Register a transport under a name: `impl` is `{send(envelope) -> Promise<resultEnvelope>, subscribe?}` (`subscribe` is the v2 push half, 6.1). The built-in fetch transport registers through this same function; selection is `configure({transport: name})`. | None (transports are page-level by nature). |
| `Citry.events.applyActions(actions)` | The action interpreter as a public entry point: apply a result envelope's `actions` array to the page, firing the same lifecycle events (4.3). Exposed for tests, custom transports, and pages that override what an action does. | None. |

What `configure` actually configures, field by field:

| Field | Default | What it overrides |
|---|---|---|
| `csrf` | `{cookie: "csrftoken", header: "X-CSRFToken"}` | Where the CSRF token comes from and which request header carries it (7.4): `cookie` names the cookie to read, `header` names the request header the token is sent in (the defaults are Django's; the same shape as axios's `xsrfCookieName` / `xsrfHeaderName`). For token sources that are not cookies (a meta tag, a JS variable), set `token` to a string or a zero-arg function instead of `cookie`; `header` still names the carrier. |
| `timeout` | `30000` | Milliseconds before an in-flight call's promise rejects with a timeout error and its queue dependents release (5.6). The server is not cancelled; the client stops waiting, and a response that still arrives afterwards is dropped with the drop event (reason `timeout`). A hung request must never hold its dependents forever, which is why an unbounded setting is deliberately not offered; raise the number for known-slow handlers, per call via `sendEvent` opts or here page-wide. |
| `transport` | `"fetch"` | Which registered transport `send` uses. Only meaningful once an alternative is registered (alternatives are v1.x; the registration function itself is v1). |
| `url` | from the manifest | Base URL of the events routes, for the rare deployment where the URL the server emitted is wrong from the browser's viewpoint (a path-rewriting reverse proxy in front of the app). Normally never set. |

The runtime's own lifecycle also surfaces as
bubbling DOM CustomEvents, all under the reserved `citry:` prefix:

| Event | Fires | Extra `detail` fields |
|---|---|---|
| `citry:events:before` | Just before a call is sent. Cancellable: `e.preventDefault()` stops the send and rejects the caller's promise. | none |
| `citry:events:after` | When a call settles, success and failure alike (the stop-side counterpart to `before`). | `ok` (boolean) |
| `citry:events:error` | When a call fails: a transport failure, an error result, or a timeout (5.6). | `error`: the `{status, code, message, fieldErrors?}` envelope (3.7) |
| `citry:events:swapped` | After a `render` action has updated the DOM. | `els`: the swapped-in root elements |
| `citry:events:stale` | Something was dropped or cancelled, and this is the one event that says so (research doc R3): every drop the runtime performs, of a response's application, of a queued call it cancels before sending, or of a one-shot send it drops at fire time (5.5 machinery item 5), fires it with a `reason` naming the cause. (The one cancel outside the claim is a send stopped by a `citry:events:before` listener's `preventDefault`: the page performed that cancel itself and already knows.) The reasons: `epoch` (an out-of-order response: its echoed epoch, 4.2, is not newer than what the anchor already applied, so its instance-mutating actions, the self-targeted render and the token refresh, drop rather than roll newer state back to older; the caller's promise still resolves with its `data` and all other actions apply), `retired` (the response's instance, or a single action's target, left the DOM, 5.5), `cancelled` (a send's dispatching element was dead when it was due to fire, at dequeue, 5.6, or at a one-shot closure's fire time, 5.5: never sent, promise rejected), `superseded` (a newer call superseded it under `@event(latest_wins=True)`, 3.5), `timeout` (a response arrived after its call timed out, 5.6), `version` (the version-skew prompt of 4.5 rides this same event under this reason; its default handling is the soft reload prompt). The `epoch` case in one line: a custom input sends on every keystroke through `sendEvent(..., {wait: false})`, you typed "ab" then "abc", "abc" answered first, and the slower "ab" response would overwrite newer results with older ones, so its application is dropped and this event fires instead. | `reason`, plus the dropped result's `event` name |

**How each drop settles.** Every dropped or cancelled call still
settles its caller's promise (the R3 contract, 14.3.6). The drop
event's `reason` names what was dropped; this table pins the matching
promise outcome, so no drop path is left to guesswork:

| Reason | What was dropped | The caller's promise |
|---|---|---|
| `epoch` | a stale response's instance-mutating actions (4.2) | unaffected: resolves with the result's `data` |
| `retired` | instance-mutating actions, or one action's dead target (5.5 machinery item 4) | unaffected: settles from its own result (a `data` action resolves it, an error result rejects it) |
| `cancelled` | a send whose dispatching element died before it fired, at dequeue (5.6) or at a one-shot closure's fire time (5.5 machinery item 5): never sent | rejects with code `cancelled`; a framework-fired one-shot (a debounce flush) holds no caller promise, so the drop event plus the debug log is its whole surface |
| `superseded` | a predecessor call under `@event(latest_wins=True)` (3.5): a queued-not-sent predecessor is never sent, an in-flight one's response drops on arrival | rejects with code `superseded`, sent or not |
| `timeout` | a late response's application | already rejected with code `timeout` when the call timed out (5.6) |
| `version` | nothing call-scoped: the version-skew prompt of 4.5 rides this reason | no call promise involved; a stale-state call settles through its own error result |

Client-minted rejections (`cancelled`, `superseded`, `timeout`) carry
the same `{status, code, message, fieldErrors?}` envelope contract as server
errors, so one rejection handler covers both: `code` is the reason,
`status` is `0` (no server verdict exists; the browser's own convention
for a request that got no response), and `fieldErrors` is absent. The other two
failure surfaces compose by reason: a timeout is a failed call, so it
sets `$error` (5.5) and fires `citry:events:error` (5.6), while
`cancelled` and `superseded` are routine queue outcomes, so they set
neither and fire no error event; the drop event plus the rejection is
their whole surface. A rejection
nobody catches surfaces as the browser's standard unhandled-rejection
log, the accepted cost of every promise settling.

Server-dispatched events fire under their own raw names (4.3),
never a citry prefix. Every lifecycle event's `detail` carries
`{ instance, class, event }` plus the extra fields above, so Alpine,
htmx, or vanilla code integrates with zero citry API:

```js
// global error toast: `error` on the detail is
// `{status, code, message, fieldErrors?}` envelope from 3.7
document.addEventListener("citry:events:error", (e) => {
  const { event, error } = e.detail;
  showToast(`${event} failed: ${error.message}`);
});

// cancel sends while offline: `before` is cancellable
document.addEventListener("citry:events:before", (e) => {
  if (!navigator.onLine) e.preventDefault();
});

// page-global progress indicator: start it on `before`,
// stop it on `after`, which fires when a call settles
// (success and failure alike; `e.detail.ok` says which)
document.addEventListener("citry:events:after", (e) => {
  progressBar.done();
});

// re-run a DOM-enhancing library (tooltips, date pickers) on
// freshly server-rendered HTML: `swapped` fires after a render
// action lands, and `e.detail.els` are the swapped-in root elements
document.addEventListener("citry:events:swapped", (e) => {
  e.detail.els.forEach((el) => initTooltips(el));
});

// `stale` fires whenever the runtime dropped or cancelled something;
// `e.detail.reason` says why (epoch, retired, cancelled, superseded,
// timeout, version). Epoch drops are normal under fast `wait: false`
// sends; the rarer reasons are the breadcrumb for "my update
// disappeared"
document.addEventListener("citry:events:stale", (e) => {
  console.debug(`${e.detail.event} dropped (${e.detail.reason})`);
});

// react to a server-dispatched event with no citry API at all
// (the handler returned actions.Dispatch("MyCard:saved", {...}))
document.addEventListener("MyCard:saved", (e) => {
  analytics.track("card_saved", e.detail);
});
```

**Load ordering.** Fragment script execution order is not guaranteed, so
the extension injects a compact inline bootstrap stub through the manifest
(inline manifest scripts run synchronously during processing). The stub
defines a queueing `Citry.events`: early `send`, `configure`,
`registerTransport`, `on`, and instance-listener calls are retained, while
early `send` and `applyActions` return promises that settle after the full
runtime arrives. It also registers a context decorator via a hook on
the dependencies manager, `Citry.manager.decorateContext(fn)`, the hook
through which the events runtime adds its members
(`state` / `sendEvent` / `onEvent`; the `props` member of 5.5 rides
the `$component` registration itself, extended in citry.js) to
every `$component` payload object (substrate item 12.5).

Bootstrap replay has one intentional exception to FIFO order: every queued
`registerTransport` declaration is installed in a first pass, then all other
queued calls replay in their original relative order. Thus an early
`configure({transport: name})` or `send` can select a custom transport whose
registration appeared later in parser execution. Transport declarations do
not represent work and return no promise; declaration-first replay makes the
load-order race deterministic. Queued `applyActions` retains normal FIFO
position in the second pass and keeps its promise contract.

The spike (13.2) pinned three boot-order rules that make this
race-proof, because citry.js processes manifest tags DURING page parse
(parser insertions are mutations, delivered mid-parse):

- The pinned runtime ships as a classic script (an IIFE bundle, not a page
  module) evaluated after citry.js. It registers Events providers and the
  context decorator at evaluation time, then marks the permanent broker
  ready. Only the broker's guarded `Alpine.start()` waits for DOM readiness.
  The core manager's single observer processes graph records, fans the batch
  out to Events, and only then handles dependency calls.
- The serializer emits the `data-citry-events` tag BEFORE the
  `data-citry` tag, so whenever a call can fire, the events manifest is
  already parsed.
- The context decorator drains any unprocessed events manifests before
  decorating, covering the window where a tag is in the DOM but its
  mutation record has not yet reached the observer.

### 5.3 DOM updates: morph by default

Responses patch the DOM by morphing (`@alpinejs/morph`, with idiomorph
as the spike-gated fallback, section 5 intro), not replacement, because
morph-by-default is what makes forms and focus survive updates for the
audience this extension targets. Rules:

- The patch target is the element set carrying the instance marker. The
  server mints a fresh component id on every render, so `data-cid-<id>`
  always shows the server's current truth, never a reused id; continuity
  across the update rides a separate, client-internal **anchor** instead
  (the stable identity of one interactive DOM position, owned by the
  events runtime, 5.5). The runtime ties the changing component id to its
  anchor through an in-memory index it re-links as each render lands, and
  routes a response to the right anchor by the call-correlation id (the
  envelope `requestId`, 4.2), never by the component id. So the server needs no
  id-reuse policy and nothing new rides the wire.
- **Link before morph.** The runtime binds the fresh component id to the
  anchor and updates the anchor's `$state` *before* it calls morph,
  because morph re-evaluates the incoming fragment's bound expressions
  during the patch; linking afterwards makes every incoming `$state` read
  fail. For the same reason `$state` stays inert (an empty read, never a
  throw) for a marker-bearing node whose id is momentarily unregistered
  in the middle of a morph.
- What survives a patch is one explicit model, pinned in 5.5's
  preservation block: the server wins by default, and a draft is
  protected exactly while the server has not seen it. After
  every patch the runtime re-applies `:c-*` bindings from `$state` to
  bound controls (that application is exactly what a one-way binding
  is, and for a field with a pending unsent write it restores the
  preserved draft; a control whose live value the patch-time guard
  below kept is exempt, per 5.5's preservation block), so templates
  need not echo `value=` for bound fields.
- Per-action `swap` override; per-subtree opt-out via `#c-ignore`
  (5.1), which compiles to the runtime marker attribute
  `data-citry-morph="ignore"` the morph hook reads, for DOM subtrees
  that another JS
  library builds and owns (the classic case is a select-enhancement
  library like Select2; Livewire's `wire:ignore` analogue). The
  compiled form is a plain
  marker in the `data-citry-*` runtime namespace, like `data-citry-busy`;
  the authored form lives in the `#c-*` channel because it names no
  handler, no State field, and no rendered attribute value: it is
  framework metadata about the node, the channel test of 5.1 applied.
- After patching, the fragment's manifests are picked up by the existing
  observer unchanged: assets dedupe by URL, `$component` re-fires with
  teardown first.
- The morph preserves the instance's living Alpine scope: `$state` is
  updated in place per the reconcile rule (5.5), never recreated, so
  reactive subscribers carry across re-renders.

**The morph call, concretely.** Pinned against the shipped plugin source
(`@alpinejs/morph` 3.15.x) so the implementation and the spike exercise
the same contract:

```js
// The package's named `morph` export is the PLUGIN INSTALLER, not the
// raw function (spike finding F1): register the plugin, then call
// Alpine.morph.
import morph from "@alpinejs/morph"; // compiled into the runtime bundle
Alpine.plugin(morph);

Alpine.morph(rootEl, fragmentHtml, {
  // Child matching pairs elements by tag name plus a key. The key the
  // runtime reads is citry's composite key attribute (what #c-key
  // compiles to, below), never the plain `key` attribute, which keeps
  // its ordinary HTML meaning. The callback is consulted for every
  // comparison, so it must stay a bare attribute read (keyed-morph
  // spike F-KM-8: the callback is hot).
  key(el) { return el.getAttribute?.("data-citry-key"); },
  // (the real signature carries a sixth skipUntil argument beyond
  // these five; spike finding F10)
  updating(el, toEl, childrenOnly, skip, skipChildren) {
    // the ignore marker (what #c-ignore compiles to): leave this
    // element and its subtree untouched
    if (el.getAttribute?.("data-citry-morph") === "ignore") return skip();
    // the patch-time half of the preservation rule (5.5): keep a
    // focused two-way-bound control's live value while it holds a
    // draft the server has not seen. hasUnsentDraft covers both draft
    // stages: a pending unsent $state write, and the unflushed
    // two-way draft before it (the flush timer still pending, the DOM
    // value diverging from $state). A control with nothing unsent
    // takes the server's value, focused or not (submit-then-clear)
    if (el === document.activeElement && isTwoWayBound(el) && hasUnsentDraft(el)) {
      keepLiveValue(el, toEl);
    }
  },
  // No `removed` hook: instance teardown on removal is not the morph's
  // job. When an instance leaves the DOM, the dependency manager's
  // removal reconciler (dependencies.md 8.4; component-identity spike
  // F-CI-5) finds the retired id in a DOM sweep and runs its stored
  // cleanups, so the events runtime wires only `updating`.
});
```

Two operational facts from the spike, worth knowing when debugging:
morph permanently patches `Element.prototype.setAttribute` page-wide on
its first call (to tolerate at-prefixed attribute names; harmless), and
local `$state` writes reach the DOM on the next tick, not in the same
task (Alpine schedules effects).

The call needs exactly three inputs, all of which the runtime already
holds: the instance's root element (registry lookup, resolved from the
action's target), the fragment's HTML string (morph parses it
internally), and the fixed hook policy above. Nothing morph-related
rides the wire beyond the action's `swap` field; hooks are runtime
policy, never per-response data.

- **The ignore marker needs no DOM surgery.** Morph libraries support
  opting subtrees out natively through their hooks; nothing is detached
  or re-inserted. This is exactly how Livewire implements
  `wire:ignore`: its directive stamps a flag on the element at init and
  its `updating` hook returns `skip()` when it sees the flag. We read
  the marker attribute directly in the hook, so no init pass is needed,
  and the marker attribute is a public surface of its own for DOM built
  outside citry templates (a third-party library's init code can stamp
  the subtree it owns; `#c-ignore` covers everything template-authored,
  5.1). On an instance root the marker is unsupported: skipping the
  root leaves the old component id in the DOM while the fragment's
  manifest introduces a fresh id that never lands, so registry and DOM
  diverge. The runtime logs a debug warning when it finds the marker on
  a root, and the documented fix is an ignore on an element inside the
  child's own template below its root, or on a wrapper element: the
  template's own root element is itself an instance root, so the
  marker there hits the same unsupported case, and only this warning
  catches it (`#c-ignore` on a component tag is already a
  template-load error, 5.1).
  The hook vocabulary is richer than v1 uses: `childrenOnly()` patches
  children while leaving the element's own attributes alone (Livewire's
  `wire:ignore.self`), `skipChildren()` is the reverse, and
  `removing`/`adding` can cancel a node swap. An `"ignore-self"` marker
  value would map to `childrenOnly()` and stays reserved until someone
  needs it; the finer per-attribute preservation tier every long-lived
  morph framework eventually grew is a recorded v2 expectation, not
  built (16.1).
- **Keys are user-authored, and `#c-key` is the keying attribute**,
  like Vue's `:key` and Livewire's
  `wire:key`: only the author knows which domain field identifies a
  list item or a child instance, so the runtime never invents identity.
  `#c-key="item.id"` on a plain element is the morph pairing key:
  within one sibling window, morph moves the real keyed nodes, so
  values, checkedness, and selection travel with the key (the
  form-field flip: two keyed inputs that swap positions carry their
  typed values with them; keyed-morph spike F-KM-2). `#c-key` on a
  `<c-*>` component tag is anchor continuity: the child instance keeps
  its client state across a parent render (the keyed-linking rule,
  5.5). Unkeyed lists pair
  positionally, which is correct until items reorder or are inserted
  mid-list; from that point per-element state (focus, a caret, an
  ignored subtree) sticks to the position rather than the item, and an
  unkeyed interactive child resets wholesale under every parent render
  (5.5). The docs guidance is therefore two-tier: add `#c-key` to
  `<c-for>` items whose list
  can reorder; and on interactive children under a re-rendering parent
  a key is required for correct behavior, not an optimization (the
  Livewire-strength wording; that ecosystem's most repeated fix is the
  missing key). Two authored contracts ride the attribute. Keys are
  **unique wherever they compete**, or behavior is incorrect. For an
  element key that means unique among siblings, within one sibling
  window: morph compares keys across all children of a matched parent
  pair whatever their tags or classes (spike F-KM-1), so two same-key
  siblings mispair however different they otherwise look, while
  duplicates in separate windows never meet. A window duplicate is
  author error with no defined pairing, documented as the author's
  responsibility the way Vue documents `:key` (the spike's verdict).
  For a component key the contract means unique per class across one
  applied render region, the scope the keyed linker matches over
  (5.5): two same-class instances carrying one key anywhere in a
  region compete for the same link, whatever their depths.
  Component-key duplicates are author error too; those the runtime
  matches in document order with a debug warning (5.5). And a keyed
  move still resets what the
  browser ties to document presence (focus, scroll positions, iframe
  documents, media playback; spike F-KM-3/F-KM-4, which also shows the
  move cost cascading from the first out-of-order sibling to the end of
  the window), so reorder-prone keyed lists should not wrap heavy
  embedded content lightly.
- **An element key works within one sibling window only.** The
  natural expectation is that a key carries a node and its state
  anywhere in the template; it does not. A key
  rescues reordering among the direct children of one matched parent
  pair; a keyed node whose position moves to a different parent or a
  different depth between renders is recreated, not moved, and its
  DOM-held state (a typed value, checkedness, a caret) dies with the
  old node (spike F-KM-1: shallow-to-deep and cross-parent moves
  always produced a fresh clone, whatever the key). The shape that
  hits this in practice is a conditional branch changing an element's
  nesting:

  ```html
  <c-if cond="editing">
    <input #c-key="'draft'" />
  </c-if>
  <c-else>
    <div class="highlight">
      <input #c-key="'draft'" />
    </div>
  </c-else>
  ```

  Switching branches recreates the input and the typed value is gone,
  identical keys notwithstanding: one branch renders it as a direct
  child, the other inside a wrapper, and keys never pair across
  depths or parents. The authoring guidance: keep a keyed element at
  the same tree position across branches (render the same wrapper
  structure in both, varying its attributes or classes instead), or
  carry the value through something that outlives the node, a two-way
  binding's pending writes in State (5.5) or, for a client-owned
  region, a `#c-ignore` opt-out (5.1).
- **What `#c-key` emits: one composite attribute.** The evaluated key
  is stamped into a single runtime data attribute on the rendered
  element, `data-citry-key`, never into the plain `key` attribute,
  which keeps its ordinary HTML meaning end to end (nothing in this
  machinery reads it). The value is composite, a scope segment plus the
  evaluated key: on a component instance root the scope is the child's
  class id (`TodoItem_a1b2c3:5`), the keyed-morph spike's
  class-id-scoped form, pinned by its verdict because morph key
  matching proved sibling-window scoped (F-KM-1: keys are compared only
  among direct children of one matched parent pair, so class-scoped
  values can never cross-pair and need no runtime normalization); on a
  plain element the scope segment is empty (`:5`), which keeps element
  keys and instance keys from ever pairing with each other. On a
  component tag the serializer stamps the attribute onto every root
  marker element of the child (a multi-root instance is one unit of
  continuity, so all of its roots carry its key). Emitted keys never
  embed per-render component ids (spike F-KM-7: raw ids inside keys
  are strictly worse than no keys at all); the id-to-anchor normalized
  form, a per-call key callback mapping ids to anchors on both sides,
  is empirically proven and recorded as the fallback if a future
  mechanism ever needs ids inside keys (spike F-KM-6 and its verdict).
  The parser channel and the emission path are WP21
  (`events_plan.md`); the falsifying outcome is named in section 15.
- **A parent-authored key survives the child's own re-render.** A
  component key is written in the *parent's* template but lands on the
  *child's* DOM: the parent's render stamps
  `data-citry-key="<child class id>:<key>"` (the composite form above)
  onto the child's root elements. When that child later renders itself,
  the server renders only the child, from the child's own template,
  which never carried the parent's key, so the fresh fragment's root
  arrives keyless. Morph compares root keys before any hook runs
  (keyed-morph spike), so a keyed old root against a keyless new root
  reads as a mismatch and forces a wholesale swap instead of an
  in-place patch. Two failures follow: the caret, focus, and scroll die
  on the child's own re-render (breaking the same-class reconcile
  promise, 5.5), and the swapped-in root now carries no key, so the
  next parent render can no longer link the child and it resets. The
  author's `#c-key` would quietly stop working after the child's first
  self-render. The applier prevents this by carrying the old root's key
  onto the incoming fragment roots during a same-class reconcile
  self-render, and only when the key's class-id prefix matches the
  caller's own class (`preserveCallerKey` in the client runtime): a key
  authored inside the child's own template re-renders with the fragment
  and needs no carrying, and a foreign class's key must never survive a
  class change (the different-class branch of the three-way split, 5.5).
- **`morph()` is single-root by construction**: it consumes only the
  first element of the parsed HTML. Multi-root instances (fragment
  components) morph pairwise, root by root, while the old and new root
  counts match, and fall back to replacing the whole root range when
  they differ. `Alpine.morphBetween(startNode, endNode, html)` (3.15.x)
  morphs a comment-delimited range and is the upgrade path if pairwise
  proves insufficient; it needs boundary markers the fragments do not
  emit today, so it stays out of v1 unless the spike says otherwise.
  Because the call consumes only the first root, a fragment's trailing
  `data-citry-events` and `data-citry` manifest tags are never part of
  a morph patch, and neither manifest observer reacts to a script tag
  patched in place (both process manifest tags only from added
  elements). Delivering the tags after the patch is therefore the
  applier's job; the normative rule is 5.5's machinery item 2. The
  harness symptom that falsifies it is assets not loading or
  `$component` never firing for a freshly rendered instance.
- **A parent's morph does not skip nested instance roots.** Livewire's
  skip is a whole architecture, not just a client rule: on a parent
  re-render its server does not re-render children at all, emitting
  only a placeholder root stub keyed by `wire:id`; the morph `updating`
  hook then sees the stub paired against the live child root and calls
  `skip()`, leaving the child's DOM untouched. Children update only
  through their own requests, which is why parent-to-child props go
  stale in Livewire unless explicitly marked reactive. Citry re-renders
  the whole subtree server-side, so the child's fresh HTML (and fresh
  manifest entry) is part of the parent's fragment: props flow
  naturally, the child's scope survives through the plugin's Alpine
  bridge, and the fresh manifest re-registers it, teardown first (5.2),
  with `$state` reconciled per 5.5. What the parent's fragment does to
  each child's client identity is the uncorrelated-id lifecycle (5.5):
  an unkeyed child resets, a `#c-key`-matched child links.
- **Alpine-state survival is the plugin's own machinery, not ours**: it
  clones the live `_x_dataStack` onto incoming nodes during the patch.
  That is the concrete content of the idiomorph question (section 5
  intro): idiomorph covers the ignore marker (`beforeNodeMorphed`
  returning `false`) and focused values (`ignoreActiveValue: true`)
  natively, but has no Alpine bridge, so falling back to it means
  re-implementing scope survival by hand. The spike's verdict weighs
  exactly that trade.

The first implementation milestone is a spike proving exactly this loop
(section 13); if the existing manifest machinery fights it, the client
model is redesigned before any server work hardens.

**Optimistic UI stance**: pending states, not predicted state. The runtime
stamps `data-citry-busy` on the triggering element and the instance
roots (from the gesture: a queued call is busy from enqueue, 5.6),
fires the lifecycle DOM events, and exposes `$loading` (5.5);
a component that truly wants optimism mutates `$state` or its own DOM
before `await sendEvent(...)`. No rollback machinery; no surveyed
framework ships one that works.

### 5.4 JS and CSS variables across re-renders

Components deliver per-instance data to their JS and CSS through
`js_data()` / `css_data()` (the variables pipeline,
[`dependencies.md`](dependencies.md) section 5). Events adds no second
mechanism: a `render` action's HTML is a full fragment serialize, so the
variables ride the fragment's own manifest exactly as they do for any
host-inserted fragment today. New `js_data` values arrive as a fresh
variables script keyed by a new hash. The manifest's `calls` entry re-fires
`$component` with the **new** `data` payload (after the previous
teardown ran). New `css_data` values load as a fresh hashed stylesheet
whose hook attribute rides the re-rendered roots, so the morph carrying
the new attribute is what switches the styles.

**What belongs in `js` vars versus State.** The production app's usage
makes the split concrete:

- `js_data` is for the client: data derived from the component's inputs
  that its JS needs in order to act, typically prebuilt URLs (the
  endpoint a chart fetches, the link a row opens). It is recomputed on
  every render and never travels back to the server.
- State is for the server: the data an event handler needs when a call
  arrives, typically ids (enough to re-render or fetch) and form state
  (what a submission mutates). It round-trips signed (7.1).
- The relationship is a one-way derivation chain: State re-renders the
  component, and the component's inputs derive its `js` vars. Deriving
  State from `js` vars, or mirroring one into the other, is backwards:
  put the id in State and derive the URL at render.

Two consequences to verify and document:

- The morph spike (section 13) must assert all three: teardown before
  re-fire, re-fire with the new `js_data` payload, and the new CSS
  variables taking effect on the morphed roots with the old ones inert.
- Events inherits the fragments deployment constraint verbatim: variables
  scripts are written by the rendering worker and may be served by another,
  so multi-process deployments need a shared cache
  ([`dependencies.md`](dependencies.md) section 8.3). The Events docs
  repeat that guidance rather than assuming the reader saw it.

### 5.5 The Alpine layer: scopes, `$state`, and the magics

This section records the Events-specific projection of the client model. The
normative ownership graph, isolation, props, boundary handlers, slot scope,
and root-shape rules live in [`alpinejs.md`](alpinejs.md). The graph is the
authority for logical ownership; pinned Alpine is its expression, directive,
reactivity, and morph engine. Within an Events anchor, Alpine's reactive State
object remains the single source of client-side truth for State. Bindings,
magics, morphs, and `$component` members read and write that one object.

**Scopes.** During manifest processing, before `Alpine.start()`, the runtime
creates one general registry record for every instance the ownership graph
marks client-active. Reasons include an Events anchor, a `$component`
registration/call, a client binding, an explicit component scope, or a
supplied/fallback fill whose Alpine expressions need a source projection.
[`alpinejs.md`](alpinejs.md) owns the complete trigger set. Events anchors
remain the owners of State, epochs, and server calls; the general record also
covers components that need Alpine ownership without declaring Events. The
mechanics are pinned here because they decide what can conflict with user code:

**Render, logical, and anchor identities.** Every interactive instance keeps
the server render record, client logical generation, and stable browser
anchor separate on purpose.
The **component id** (`data-cid-<id>`) is the server's faithful surface:
the server mints a fresh id on every render, so the DOM, telemetry, and
`$component` always show the server's current id, never a reused or
stale one. The **anchor** is a stable, client-internal identity for one
interactive DOM position, owned by the general registry. The logical client
instance and optional Events sidecar attach to it; reactive State and the
epoch guard (4.2) remain Events-owned sidecar data, so they survive a
re-render even as the component id under them changes. The runtime ties the
two through a
component-id-to-anchor index (a plain in-memory map, re-linked as each
render lands), and routes a render response to the right anchor by the
call-correlation id (the envelope `requestId`, 4.2), never by the component id.
Because continuity rides the anchor, the server needs no id-reuse policy
and nothing new rides the wire.

- **The reactive State object lives in the runtime's registry**
  (`Alpine.reactive({...})` keyed by the anchor, seeded with the
  instance's public State fields from the manifest values map, 4.4),
  never on an element. Keying by the anchor rather than the component id
  is exactly what lets one reactive object outlive a re-render: the id
  changes with every render, but the anchor is stable, so the same object
  keeps serving that DOM position across updates. An element expando
  (`el._citry_state`) would die under morph, whose swap path clones nodes
  (`cloneNode` drops expandos, 5.3); attributes survive cloning, so the
  DOM carries only a marker and the registry holds the object. Multi-root
  instances share the one object for free.
- **`$state` and the other magics resolve through graph evaluation context,
  not the Alpine scope stack or DOM proximity alone**: a physical marker can
  locate candidate graph records, but it is not the ownership authority.
  Ordinary child-template expressions select the child's logical record. A
  source-linked fill or relocated component-tag handler selects its exact
  authored source record even though the evaluating element lives under a
  physical child. That record then resolves the optional Events anchor for
  State and call state. An owner with no Events anchor keeps the inert
  mid-boundary behavior rather than falling through to an unrelated physical
  ancestor. When one element roots multiple logical instances, graph-record
  precedence and the current evaluation facade choose the owner; array order
  in a marker is only transport data. The fixed-name `data-cid` marker may
  remain as a physical lookup optimization alongside per-instance markers,
  but `el.closest("[data-cid]")` cannot decide logical ownership.
- **Nothing is written into `x-data`, ever.** A user's own `x-data` on
  the instance root, or anywhere inside, coexists untouched: citry adds
  no enumerable keys to any user scope object (verified on the scope
  stack itself; Alpine's merged `$data` proxy hides every key from
  `Object.keys`, a proxy-trap quirk, so tests must check the stack),
  and the `$`-prefixed magics cannot
  collide with scope properties. The rejected alternative, merging
  State into the user's `x-data` object, would pollute key enumeration
  and invite name collisions.
- **The one thing placed on the Alpine scope stack is the instance's stable
  reactive `scope` object** at each normal root (`addScopeToNode`, the pinned-version
  private API from the audit), together with registering the instance
  marker as an Alpine root selector through the permanent broker
  (`[data-citry-root]`, with `[data-cid]` retained for Events roots, using
  Alpine's public `addRootSelector` API and the
  Livewire pattern; without it Alpine never walks a scopeless citry
  root, spike finding F5): the pair makes the subtree
  Alpine-active whether or not the user wrote `x-data`, and the
  boundary entry is where
  the ~15-line stack truncation from the maintainer's
  alpine-composition cuts inheritance, so a nested citry component does
  not inherit its parent's scopes, mirroring the server-side isolation
  of component inputs. It starts empty and gains only names the component
  writes explicitly through its `$component` context. On a shared physical
  root, structural `data-cid` order chooses the innermost client-active
  instance's scope independent of manifest order; outer scopes stay registry-
  only there. The same object is attached to every normal root of a multi-root
  instance.

Components with no graph-declared client activity get no scope and pay
nothing, which is the main
mitigation for Alpine's synchronous startup walk. Scope creation is
eager at manifest time; lazy activation (viewport entry with a margin,
plus first interaction) stays in reserve if the dogfood port (section
13's planned rewrite of the audited production app) finds real cost
(section 16). A user's own `x-data`
inside a component's template nests normally, sees the citry magics,
and is the right home for client-only UI state (accordion flags,
draft toggles) that does not belong in State.

**The magics.** Registered through the plugin pattern lifted from
alpine-composition, available in any Alpine expression inside a citry
scope (and, where noted, as members of the `$component` payload):

| Magic | What it is |
|---|---|
| `$state` | The graph-selected Events owner's reactive State (public fields). Reads are reactive. Writes work on any public field not clamped by `_model` and throw a pointed error otherwise (client-only UI state belongs in your own `x-data`). A write queues a pending update: it rides the next call from that owner, whatever sends it (the designed flush is the event you send; the piggyback rule of 4.2 applies). |
| `$loading` | Callable: `$loading()` is true while any call from this instance is queued or in flight (busy spans the queue, 5.6); `$loading('save')` scopes to one handler. An unknown handler name throws the pointed error naming the declared handlers (the class descriptor carries the list). Read-only. |
| `$error` | The instance's last error envelope (`{status, code, message, fieldErrors?}`) or `null`; set on a failed call (an error result, a transport failure, or a timeout; `cancelled` and `superseded` rejections leave it untouched, 5.2), cleared on the next successful one. Read-only. |
| `$sendEvent(name, args?)` | Send an event from an Alpine expression; the same function the `$component` payload carries. An unknown event name throws the pointed error client-side, before anything hits the wire (the same descriptor check as `$loading`). |
| `$onEvent(name, fn)` | Listen for server-dispatched events targeting this instance; returns the unsubscribe function. |

A listen-and-forward shorthand (a `$forwardEvent` magic) is deliberately
absent: forwarding is the one-line composition
`$onEvent(name, () => $sendEvent(handler))`, and the magics list stays
minimal (16 tracks it as a community-demand item).

The `$component` payload is
`{ id, els, data, state, props, scope, effect, reactive, sendEvent, onEvent }`.
`state` is the same reactive Events proxy; `props` carries the declared client
inputs and is empty under the bare callback form. `scope` is the one stable
reactive object shared by all of the instance's normal roots. `effect(fn)`
uses Citry's embedded Alpine, returns an idempotent early-stop function, and
auto-disposes before user cleanup; `reactive(value)` returns an Alpine
reactive proxy. There is no separate `release` member. Init's return remains
the user cleanup function. The logical registry owns prop supply and lifecycle
independently of physical roots, so rootless components can resolve props and
run init. `els` contains every current element root and is empty for a
rootless instance. The positive RootGroup spike pins it as one stable array
whose membership updates in place and which clears on logical teardown; A6
connects product morph membership to that array.

**Client-side writes and the local-first pattern.** Because `$state` is
writable (on `_model` fields), interactions that need no server work
stay local:

```python
class Counter(Component):
    class Kwargs:
        count: int = 0

    class State(Kwargs):
        pass

    class Events:
        def save(self, state):
            persist_count(state.count)
            return Counter(count=state.count)

    def template_data(self, kwargs, slots):
        return {"count": kwargs.count}

    template = """
      <div>
        <button @click="$state.count++">
          Clicked
          <span x-text="$state.count">
            {{ count }}
          </span>
          times
        </button>
        <button @c-click="save">Save</button>
      </div>
    """
```

The increments are pure client mutations; they queue as updates and
travel only when `save` is called, so the server sees the final count
without a round trip per click. (The section 2 counter stays the
canonical server-round-trip form; this is the local-first variant.)

**Reconcile rule.** When a response arrives, the runtime updates
`$state` in place: **server wins per field, except fields with a
pending, not-yet-sent local write, which keep the local value** (they
are still queued and will reach the server on the next call). Combined
with `@alpinejs/morph` preserving the living Alpine scope across morphs,
a re-render never recreates the scope; `$state` object identity is
stable for the anchor's lifetime, and reactivity propagates the new
values into `x-text` / `x-show` / effect subscribers automatically. The
`$component` teardown-then-re-fire cycle remains for imperative JS
that manages what a library draws and owns outside Alpine (charts,
maps, editors).

**Preservation: server wins by default, deviations are explicit.** One
rule covers every layer of an update: the server's render is
authoritative, and anything that outlives it is something the author,
or the user's still-unsent input, explicitly made outlive it. The
explicit deviations are exactly three: a **pending unsent write** wins
its field until the flush carries it (the reconcile rule above);
**`#c-ignore`** opts a whole subtree out of patching (5.3);
**`#c-key`** carries identity, and with it the anchor's client state,
across reorders and parent renders (5.3, and the lifecycle below).
Focus is deliberately not a fourth: the runtime never treats "the user
is focused here" as a silent preservation signal. The two recorded
field failures are the poles this construction avoids: with no
protection at all, every keystroke-driven patch can eat a draft
(morphdom issue 135); with blanket focused-element protection, a
handler that legitimately clears a still-focused field can never land
the clear (Turbo issue 1194, the submit-then-clear chat box). Here a
draft is protected exactly as long as it is still unsent (in the
field, or still in the control ahead of its flush), and stops being
protected the moment the flush hands it to the
server, so the handler's clear wins. The acceptance tests are both
poles at once (research R1): fast typing over a patch loses nothing,
and submit-then-clear clears. The updates piggyback (4.2) is the
lifted-input-state half of the story: a pending write rides whatever
call the instance sends next, poll ticks included, so a poll uploads
the draft instead of racing it; `data-citry-busy` plus `$loading` are
the disable-while-loading half (5.3). Grounding for all of it:
[`events_research/research-rerender-preservation-and-concurrency.md`](events_research/research-rerender-preservation-and-concurrency.md)
(R1).

After a patch, the runtime re-applies `:c-*` bindings from `$state` to
bound controls (the application a one-way binding is, 5.1), and a
field holding a pending unsent write re-applies too: its `$state`
value **is** the preserved draft, so the re-apply restores what the
patch may have visually reverted. One exemption keeps the re-apply
from fighting the patch-time guard in 5.3's hook: a control whose
live value that guard kept (a focused control holding an unflushed
two-way draft, one its debounce has not yet written into `$state`) is
skipped, because for that control `$state` still holds the pre-draft
value and re-applying it would clobber exactly what the guard
preserved. The guard's `hasUnsentDraft` check therefore covers both
draft stages, a pending unsent `$state` write and the unflushed DOM
draft before it, and the one loss window left open is the unflushed
draft in a control that is **not** focused when the patch lands
(typed, then tabbed away before the debounce flushed): the guard is
focus-scoped, protection still derives from the unsent draft, and
focus only picks out the control the user is actively editing. So
fast typing over a patch loses nothing, whether the draft sits in
`$state` or is still mid-debounce.

The three layers compose into one rule set: the reconcile rule
preserves flushed-but-unsent writes at the state layer, the patch-time
guard keeps a focused control's unflushed mid-debounce draft, and the
re-apply skips guard-kept controls so it can never undo the guard. The
re-apply itself is focus-independent (a field with pending unsent
writes re-applies from `$state` after a patch, focused or not), and
the one exposed loss is the window named above: an unflushed draft
whose control lost focus before the patch.

**What a re-render does to the scope: the three-way split.** The
reconcile rule above is one of three branches, chosen by a single check
when a handler's render replaces the anchor's own DOM: the runtime
compares the anchor's current class id against the incoming render
token's class field (`c`, 7.1).

- **Same class**: reconcile, exactly as above. The anchor's Alpine scope
  and `$state` object identity persist, the server wins per field except
  fields with a pending unsent local write, and a focused two-way-bound
  input holding an unsent draft keeps its value and caret (the
  preservation block above).
- **Different class**: discard the old state and adopt the server's fresh
  token and values wholesale, with no per-field reconcile (the fields do
  not correspond), then rebuild the boundary scope for the new class. The
  anchor persists but its contents are rebuilt, so a later send carries
  the new class's token and the server's `cls.State(**s)` rebuild (7.1)
  succeeds instead of failing on a stale token.
- **Plain HTML** (the render carries no component): the anchor becomes
  non-interactive, its state and scope are discarded, its instance's
  cleanup runs, and no new instance is created.

**The uncorrelated-id lifecycle: one rule for every arrival that is
not the caller's own.** The three-way split above is the property of
exactly one path: a correlated self-render, where the envelope's
correlation id resolves the caller's anchor and the target agrees.
Every other way an instance id reaches the DOM (the initial page load,
a host-inserted fragment, a render action targeting a selector, a
parent's fragment carrying fresh child ids, v2 server push) follows
one rule instead: **a render arriving from anywhere other than the
region's own correlated call replaces the region's client state
wholesale.** Fresh manifest ids mint fresh anchors seeded from the
server-rendered token and values; anchors whose ids leave the DOM
retire. This is the client mirror of the golden rule (7.5): the
handler's returned tree shares nothing with what it replaces, so the
client does not pretend its regions do either, and it can never
attribute state to the wrong entity because it never guesses identity
(positional matching was rejected for exactly that reason, 14.3.2).

**Keyed linking is the one continuity mechanism on top.** A child
instance whose root carries the same class and the same `#c-key` value
on both sides of an applied render links instead of resetting: its
anchor, meaning the `$state` object identity, the pending unsent
writes, the `$loading` counters, the `$error` box, the epoch pair, and
its subscriptions, carries across and reconciles by the same-class
branch above. For that link to keep working across the child's own
later self-renders, the applier re-stamps the parent-authored key onto
the child's otherwise-keyless fragment during that same-class reconcile
(the caller-key preservation, 5.3); without it a child would go keyless
after its first self-render and the next parent render could not link
it. Busy display carries with the counters: a linked anchor
whose loading count is nonzero after the swap re-stamps
`data-citry-busy` on its new roots, and on the triggering element
where it survived the patch (the morph strips client-stamped
attributes from surviving elements, so the per-trigger stamp of 5.6
needs the same restore), so the one continuous busy state
(5.6) stays visible through the parent's render, per-trigger pending
UI included. Matching is
swap-agnostic (it reads the composite key
attribute, 5.3, on the old region and on the pre-parsed fragment, so
the same semantics hold under `replace`, where the anchor payload
survives even though the DOM state dies with the node), scoped per
applied region, and recursive (a linked child's subtree is itself a
region for its keyed grandchildren); the region is also the scope of
the authored uniqueness contract for component keys (5.3), because
two same-class instances carrying one key anywhere in it compete for
the same link. Duplicate keys within a region
match in document order with a debug warning; everything unkeyed or
unmatched follows the reset rule above. One sub-rule rides every link,
the **horizon cut**: at link time the child's highest-applied epoch is
set to its send counter, so instance-mutating actions of the child's
own in-flight calls drop when their responses arrive (the guard
applies only strictly-greater epochs, 4.2, so this one assignment
covers them all; their `data` still resolves; the drop event fires
with its reason). The parent's
render replaced the child's token with a parent-derived one, and
applying a pre-parent render or token afterwards would resurrect that
replaced state into the child's next send. With the queue (5.6)
serializing sends from overlapping anchors, the cut's remaining work
is `wait: false` sends and arrivals from unrelated anchors' calls,
the same residue the
epoch guard nets. The alternative, last-writer-wins for late child
responses, is recorded with the decision (14.3.2); both are
client-internal, so if dogfood users report "my save's UI never
showed" more than they would tolerate stale-parent flicker, the cut is
the piece to revisit.

**Targeted renders are remove-and-replace.** A `render` action whose
target names anything other than the calling instance is, to the state
model, a region teardown plus a fragment insert: departing instance
ids retire with their anchors, the fragment's manifest mints fresh
ones (or links keyed matches per the rule above), and no epoch
comparison ties the apply to the target's past, because the target
keeps no surviving counter. Continuity is owned by a region's own
correlated self-renders, and by keyed matches, alone; a handler whose
selector happens to resolve to its own region gets replace semantics,
not the three-way split (self-continuity rides only the runtime's
`render:` self-address). Races to one target from unrelated anchors (two
different
callers rendering into `#cart-badge`) stay last-write-wins in arrival
order and are answered in userland by the ordering patterns the docs
teach: render current truth, not deltas (a handler that renders truth
leaves a briefly stale region that self-corrects on the next event),
and dispatch-and-refresh for contested regions (`Dispatch` plus the
region's own listener re-rendering itself, so the region's anchor
serializes its own updates). Helper utilities for that cross-caller
target ordering are a possible later addition, not v1 (16.1). One documented
author trade: a `wait: false` send's targeted render bypasses the
queue's ordering (5.6), so repeat-firing `wait: false` sends into one
region can paint out of arrival order; bypassing the queue accepts
last-arrival-wins there.

**A selector matching several elements inserts one shared instance,
mirrored per match.** The same fragment (one instance id, one anchor,
one State, one token) lands at every match; every copy carries the
instance's marker, and a `$state` write in one reflects in all (the
canonical case: the cart badge in the desktop header and the mobile
drawer always agree). A later self-render of the duplicated instance
applies its fragment to each marker-carrying element independently,
and the applier strips the trailing manifest tags from all but the
first insertion (machinery item 2 below). Independent per-region widgets are the other
tool: one `Render` action per target, each its own instance. The
user-guide framing of the distinction is WP19 scope
(`events_plan.md`).

**The five machinery requirements.** Option-independent runtime
obligations, normative for the client applier work package
(`events_plan.md` WP16.1); they were required under every
candidate lifecycle, which is why the decision round adopted them as a
unit ([`events_research/analysis-nested-anchor-continuity.md`](events_research/analysis-nested-anchor-continuity.md)
"Machinery every option needs";
[`events_research/analysis-target-other-renders.md`](events_research/analysis-target-other-renders.md)
option A mechanics):

1. **Fragment ids register before the morph.** The applier parses the
   fragment's events manifest out of the action's HTML and
   creates-or-links anchors for every id it names before any swap
   runs, so every `$state` read the morph's Alpine bridge evaluates
   mid-patch resolves to real state (an inert read tracks no reactive
   dependency and never recovers). This is link-before-morph,
   generalized from the correlated caller to the whole fragment.
2. **The applier owns manifest-tag delivery.** Both trailing manifest
   tags are inserted as new elements after a morph patch (the
   single-root call never carries them, 5.3), unmarked, so the
   post-swap observer pass stays the single mechanism across swap
   kinds (for an id registered before the swap that pass is
   idempotent, refreshing only the token); on a multi-match target the
   tags ride only the first insertion, so the dependency manager runs
   one teardown-and-refire cycle rather than one per copy.
3. **The anchor retirement sweep.** After a swap settles, and on DOM
   mutation (host JS also removes subtrees), any anchor whose
   component id has no live element retires: unlink the id, drop the
   anchor from the registry, null its fields. When the sweep retires
   an anchor still holding pending unsent writes or a nonzero loading
   count, it logs a debug warning naming the class and the dropped
   field keys: that is the exact moment reset discards user input, and
   without the warning the silent revert is undiagnosable in the
   field.
4. **Per-action liveness checks.** Liveness of an action's target and
   of the caller's anchor is re-checked per action in faithful list
   order, never once per response: an earlier action in the same
   result can retire a later action's target (a targeted render that
   replaces the region containing the caller, followed by the caller's
   self-render, drops the self-render). The same rule
   spans results within one batch envelope (5.6): an earlier result's
   render can retire a later result's caller. A response correlating
   to a retired anchor behaves like a stale one: its `data` resolves,
   its instance-mutating actions drop, the drop event fires with
   reason `retired`, and a debug line records it. Every per-action
   dead-target drop surfaces the same way: the drop event (reason
   `retired`, 5.2) plus a debug log. That includes a self-addressed
   `event` action whose target id is dead, which drops rather than
   falling back to a document dispatch (that would change delivery
   semantics silently). Liveness and its `retired` surface belong to
instance-addressed work alone (the caller's anchor, `render:`
   targets, the self-addressed defaults): a plain-selector target is
   never live or dead, so a selector that stops matching, whatever
   earlier action or host mutation removed its matches, surfaces only
   4.3's zero-match warning, and one action never fires both
   surfaces.
5. **Recurring timers retire with their region, and never
   double-poll.** Retiring an anchor cancels the interval timers
   registered to it, or timers are keyed to the element with one timer
   per element so a morph survivor dedupes against the fresh
   instance's own manifest-initialized interval instead of
   compounding; either form guarantees a replaced `@c-poll` region
   never leaves a dead interval firing forever. One-shot closures (a
   debounce flush, a captured `$sendEvent`) re-resolve
   element-to-anchor when they fire; a fire-time miss, or a hit on a
   class that does not declare the event, drops the send before
   anything is sent, and the drop settles like the dequeue-time
   cancel (5.6): where a caller holds the promise (a captured
   `$sendEvent`), it rejects with reason `cancelled` and the drop
   event fires (reason `cancelled`, 5.2), while a framework-fired
   one-shot (a debounce flush) holds no caller promise, so the drop
   event plus a debug log is its whole surface. Nothing on this path
   throws: the runtime never turns a routine race into a bare
   exception, and the one console artifact left is the browser's own
   unhandled-rejection log when a caller ignored a promise that had
   to settle (every promise settles, 14.3.6).

Falsifiers for this lifecycle, split by when the evidence can exist.
Checkable pre-v1, in WP21 and the client wave: if `#c-key` forwarding
onto child root markers cannot stay inside WP21's
compiler-to-serializer path, the keyed-linking cost claim is falsified
(section 15); and if the typed-text revert reproduces in a realistic
unkeyed demo page, the keying guidance escalates to requirement
wording wherever interactive children sit under re-rendering parents.
Checkable only in the post-v1 dogfood port (section 13): if the port
surfaces a recurring pattern of targeted renders into regions holding
live client state that dispatch-and-refresh cannot express, wholesale
reset is too destructive and adopt-in-place comes forward from the v2
continuity design (16.1).

**How `:c-*` and `@c-*` ride on Alpine.** The compiled `data-cev-*`
specs stay exactly as specified in 5.1 (spec-valid HTML; handler names are
never evaluated as code); what changes is what they drive. A one-way
`:c-<key>` registers an Alpine `effect()` over `$state.<key>` that
applies the value to the control, so re-application after morphs is
just reactivity. A two-way binding writes `$state.<key>` (which queues
the update) and sends the named handler, in one call. Event bindings
keep the delegated listeners. The raw-Alpine equivalences are worth
teaching, because they demystify the sugar:

```html
<!-- compiled, template-load validated -->
<button @c-click="save">
<!-- same behavior, plain Alpine -->
<button @click="$sendEvent('save')">

<span
  x-text="$error?.fieldErrors.email"
  :class="{
    'c-error-active': $error?.fieldErrors.email
  }"
></span>
```

The compiled forms add template-load validation and never evaluate handler
names. A compiled `@c-*` call may still evaluate its optional parenthesized
Alpine argument expression; the plain-Alpine forms trade server binding
validation for full expression control. Both are first-class.

**Pending and error display need no vocabulary.** The runtime stamps
`data-citry-busy` on the **triggering element** for the duration of its
call, from the moment the gesture enqueues it (5.6), in addition to
the instance roots, so per-trigger pending UI is a
CSS attribute selector in the component's own CSS
(`.toggle[data-citry-busy] { opacity: .5 }`). That resolves the
granularity critique with zero new syntax: a settings page of
independently saving toggles lights up only the toggle that is saving. Error
display is plain Alpine over `$error`, as above: `x-text` sets
`textContent`, never HTML, so the display is safe by construction, and
any preprocessing (unwrapping, prefixing) is an ordinary Alpine
expression or a helper on the user's own `x-data`.

**Client-side composition: props down, events up.** Between client
scopes, three channels exist and each has one job. Scope inheritance is
not a data channel: named client components (user-defined Alpine
components registered through the runtime's component helper) are
isolated like citry scopes, so a
descendant can never implicitly absorb an ancestor's inputs; anonymous
inline `x-data` keeps Alpine-native nesting for local UI state. Explicit
per-instance inputs are **props**: declared by the component that consumes
them, supplied by an exact component-boundary source record to a
graph-identified child instance, one-way down and reactive. Repeated siblings
have distinct target records even when their DOM shape matches. This is the
client mirror of the server contracts: `Kwargs` at the server boundary,
`State` at the wire boundary, props at the client boundary, each
declaring, documenting, and validating what crosses.

**Props are declared and consumed through `$component`** (renamed and
one-registration-per-class contract ratified 2026-07-17), which accepts two
forms. A component class has exactly one registration; a second `$component`
call for the same class throws an error naming the class and stating that the
component is already defined. `$component` is the registration spelling.

- The existing **bare callback**, unchanged:
  `$component((ctx) => { ... })`. It declares no props, and the
  context's `props` member is an empty object.
- A **config object** with a required `init` and an optional
  `props` map:

  ```js
  $component({
    props: {
      name: { type: String, required: false },
    },
    init: ({ props: { name } }) => { ... },
  });
  ```

  `init` carries the bare form's exact contract: it receives the
  context and may return a cleanup (5.2).

The config object, rather than a second argument, is deliberate: it
is the future home for other JS-side component settings, which is why
`props` is a named key inside it. Named client components registered
through the runtime's component helper declare props with this same
config shape, so one declaration form serves component JS and client
components alike. Prop definitions are Vue-object-API style, one
entry per prop name; the v1 definition fields are `type` (a
constructor the resolved value must match, or an array of
constructors any one of which may match, `type: [String, Boolean]`),
`required` (default
`false`), and `default` (the value used when the parent supplies none).
Object and array defaults must be factories such as `default: () => ({})` or
`default: () => []`; Citry calls each factory once per logical instance and
reuses that result for the instance lifetime. This prevents accidental
cross-instance sharing without cloning or freezing user data. The read-only
props view blocks top-level declared-key reassignment but deliberately does
not deep-freeze nested supplied/default objects or arrays. Anything beyond
those three (a
`validator` callback) is a future field, added on
demand. Resolved prop **values** arrive on the callback context under
`props` (`{ id, els, data, state, props, scope, effect, reactive, sendEvent,
onEvent }`),
reactive through plain Alpine reactivity like the rest of the layer:
a parent-side change propagates to effects reading `props.<name>`,
and nothing Vue-flavored is layered on top. Validation runs when the
instance initializes, before init: a missing required prop or
a type mismatch fails loudly, naming the component and the prop. This
carries the recorded requirements (16.1's record): the contract is
explicit per child (documented, required-checked, defaulted), inputs
are per logical sibling instance, and isolation
stands, so no prop is ever inherited implicitly across depth.

**Props are supplied with `$c-props` on the child component tag.** The parent
writes one Alpine object expression where the child is invoked:

```html
<c-chart-card $c-props="{ theme: $state.theme }" />
```

`$c-props` is client-evaluated and must survive to the browser. Its `$c-*`
spelling identifies Citry-owned client-runtime behavior without claiming
Alpine's `x-*` namespace or the server-evaluated `#c-*` channel.
`ComponentNode.render` resolves the tag's attribute contributions in source
order, then splits them into ordinary Python kwargs and structured client binding
records. Three families become client bindings across a component boundary: `$c-props`, Alpine
event handlers (`@...` and `x-on:...`), and Citry event handlers (`@c-*`,
classified before generic `@...`). Every other non-reserved attribute,
including `x-show`, `x-model`, `:class`, `x-transition`, and ordinary `class`,
remains a Python render-time component input. `:c-*` and `#c-*` retain their
separate 5.1 rules. There is no general root-attribute fallthrough.

This client binding split applies to registered component targets and transparent
`<c-component>`. `<c-element>` instead produces one selected HTML element: it
rejects `$c-props`, and its Alpine handlers, `@c-*`, and `:c-*` use the normal
HTML-element attribute/rewrite path.

The recommended arbitrary-attribute API is a child-declared `attrs` mapping:

```html
<c-card c-attrs="{ 'x-show': 'visible', ':class': '{ selected: selected }' }" />
```

```html
<!-- Card.template: the child chooses the destination. -->
<article c-bind="attrs"><c-slot /></article>
```

The child may instead apply that mapping to another root or nested element.
Direct, server-dynamic (`c-$c-props`, `c-@click`, `c-@c-save`), and
component-tag `c-bind` contributions resolve left to right; exact-key
last-one-wins; final `None` or `False` removes the client binding; `True` is invalid;
and a present value must be a string. `$c-props`
and Alpine handler values are raw Alpine expressions. A Citry `@c-*` value is
a declared server handler name with an optional parenthesized Alpine argument
expression. An exact-key winner occupies its winning contribution's position
in final handler order; remove-then-readd likewise occupies the re-add
position. Keep `@click` and `x-on:click` distinct. Spread diagnostics name both
the `c-bind` span and mapping key. A literal `$c-props` on plain HTML is a
template-load error; a dynamically contributed one fails when attributes
resolve.

The client binding record names the exact lexical source, logical owner, actual child
target, and current graph revision after the component tag disappears. Supply
evaluates through that source record, not through the child's physical parent
or nearest DOM stack. One logical supplier effect belongs to the child
instance even for multi-root or rootless output. The props bag, stable
`scope`, managed effects, cleanup, and full `els` collection remain
instance-scoped and shared by all roots. A parent change therefore updates
effects reading `props.<name>` through plain Alpine reactivity.

First init waits until declaration and first supply meet. Parent init settles
before descendant init through an ancestry DAG; only the dependent branch
waits, and failure or removal settles that branch rather than freezing
unrelated components. `effect` and `reactive` use the embedded Alpine instance
and follow the managed lifetime described above.

`$c-props` must synchronously return a plain object. On first supply, a syntax
error, runtime throw, Promise/thenable, or invalid result shape logs a pointed
error, skips init, deactivates that supplier, and settles the ancestry branch
so descendants cannot deadlock. After successful init, invalid data must not
remain exposed as if valid and the supplier must not stop the scheduler. The
exact field-versus-whole-bag transaction, clear-to-`undefined` behavior, and
recovery diagnostic remain open in [`alpinejs_plan.md`](alpinejs_plan.md) O5.
The failure does not write `$error` or fire an Events lifecycle event unless
that final decision explicitly changes the contract.

Only own enumerable keys from the supplied object participate in resolution.
An unknown key is ignored and reported with one direct `console.error` per
instance/key failure episode; a later evaluation without that key re-arms the
report. Valid declared siblings still apply, and a typo that also omits a
required prop reports both failures. Unknown keys do not throw, write
`$error`, fire an Events lifecycle event, or enter the resolved props bag.
There is no page-level strictness setting. `__proto__`, `prototype`, and
`constructor` are never assigned from supplied data; a future open-ended
contract requires an explicit declaration-level rest facility.

An Alpine event handler authored on a child component tag evaluates its whole
value in the exact parent source scope. A Citry `@c-*` value instead names a
declared server handler and may include one parenthesized Alpine expression for
its argument object; only that argument expression uses the parent source
evaluator. Ordinary data, `$data`, `$root`, `$id`, `$refs`, and the other
lexical magics come from the location where the tag was authored, so a missing
source name never falls through to child `x-data`. Only `$el`, the child-bound
`$dispatch`, and the exact `$event` come from the physical child. Native
`event.currentTarget` is untouched, so the listener mode and delivery timing
determine whether it is a child root, `window`, `document`, or `null`. The
listener and modifier machinery therefore binds to the child `RootGroup`, but
only the Alpine handler or Citry argument expression evaluates against the
live source-location carrier. See the cross-browser
[`boundary-handler scope spike`](alpinejs/spike-citry-handler-refs.md).

Citry `@c-*` has one additional ownership rule: its server-handler name is
validated, dispatched, and queued through the exact source parent Events
anchor, never the child's nearest anchor. The child root remains the physical
trigger and receives the per-trigger busy marker. A relocated `@c-submit`
still collects named controls from the physical child form using the ordinary
Events codec; an explicit source-authored argument object is merged afterward
and wins on collisions. `:c-*` remains invalid on a component tag.

A handler authored inside the child's own template remains child-local. To
grant child code an intentional parent capability, pass a callback through a
declared prop, expose it through the child's stable `scope` during init, and
call it from the child's Alpine template:

```html
<c-action-button
  $c-props="{ givenCallback: () => selected = true }"
/>
```

```js
$component({
  props: {
    givenCallback: { type: Function, required: true },
  },
  init: ({ props, scope }) => {
    scope.givenCallback = props.givenCallback;
  },
});
```

```html
<!-- ActionButton.template -->
<button @click="givenCallback">Run</button>
```

This explicit props path is how the parent chooses to share behavior. Merely
placing a handler on `<c-action-button>` never grants it access to child scope.

Static `<c-component is="Card">` already compiles to its selected target. The
dynamic `<c-component c-is="selected">` path must forward client bindings separately
from kwargs to the actual selected `CitryElement`; the transparent built-in is
never the client binding target. Replacement cleans the old target's client binding lifetime
exactly once.

The multi-root `RootGroup` mechanism and stable live `els` representation are
proved by the cross-browser
[`RootGroup` spike](alpinejs/spike-root-group.md) and landed in Alpine plan A6
together with the real client binding. The cross-browser
[`rootless lifecycle spike`](alpinejs/spike-rootless-lifecycle.md) proves a
comment-owned lifetime for text-only or empty client-active output, with
stable-anchor normalization, grouped mirrored regions, contextual parsing,
and a nested-range island guard; A6 lands those range mechanisms. A2 already
settled O11 by requiring exact `citry:g1` caps and cap-preserving deployment.
A8 landed atomic incoming graph, Events, dependency, and DOM adoption with
rollback before publication.
The remaining gated edge mechanism is a named
client-target helper that creates fresh identities for direct `x-for` clones. A later
browser-side blueprint-instantiation feature would be needed to clone a
server-rendered Citry component safely; rewriting `data-cid-*` values alone is
insufficient. The complete edge matrices and fallback errors live in the
[round-two report](alpinejs/exploration-x-props-round-2.md).

Ambient context that should cross component boundaries (theme, locale) is
**provide/inject**, which deliberately pierces isolation and is never
used for per-instance inputs. Events travel up through native bubbling,
parent-owned component-target handler client bindings, or `Dispatch` / `$onEvent` for
server-touched paths. Two boundary facts keep this channel small: Citry
components never need client props for their own server inputs (that passing
happened server-side, kwargs to `state_data` to a seeded scope, per instance),
and server-generated lists stay `<c-for>` plus morph. If the separately
designed named client-target helper enters v1, client `x-for` may target it
rather than cloning a server-rendered Citry identity; the landed graph-first
runtime makes no direct `x-for` component-composition claim. A later blueprint-instantiation
protocol is a separate feature.

**What `js_data()` remains for.** State is the small reactive contract;
`js_data()` is the big inert per-render payload. `js_data` stays
non-reactive and hash-deduplicated across instances (5.4), arrives as
the `data` member of `$component`, and is recomputed wholesale on
re-render. It must not be mutated to expose Alpine variables because sibling
instances may share the deduplicated object; write instance-local client names
to `scope`. The rule: if it must survive calls or drive server bindings, it is
State; if it is derived for this render, it is `js_data`; if it is local
client state exposed by init, it is `scope`.

**Content security policy, stated honestly.** The embedded Alpine is the
standard build, which evaluates expression strings, so pages using
Alpine expressions need `unsafe-eval` in their CSP, the same trade
Livewire makes. citry's compiled bindings evaluate author code only
where the author wrote an arg expression (5.1); argless bindings
evaluate nothing. A future constrained mode pairing Alpine's CSP
build with argless compiled bindings is therefore possible; it is
recorded in section 16, not planned.

### 5.6 The event queue: a dependency DAG

Two sends can overlap: a slow save races a fast toggle, a poll tick
lands mid-edit, the network reorders. The queue is the client-side
answer, and it is an explicit dependency graph: **queued events are
nodes in a DAG** (a directed acyclic graph: every edge is a wait, and
because edges only ever point at earlier events, no cycle can form).
At enqueue, the new event gains a dependency edge to every
not-yet-settled event whose dispatching owner is the same logical owner as,
an ancestor of, or a descendant of the new event's dispatching owner in the
active Citry ownership graph. Physical roots and markers locate live regions;
they do not define ancestry. Logical containment and physical liveness are
re-verified at dequeue because both the graph revision and DOM may have
changed while the event waited. An event
dispatches when every edge it holds is settled; the graph's roots, the
events with no unsettled dependencies, are exactly the dispatchable
set. Independent branches of the DAG run in parallel: events from
sibling or otherwise unrelated anchors share no edge and never wait on
each other, while events whose anchors overlap are ordered by their
edges in enqueue order, so overlapping work applies in the order the
user caused it.
Serializing within one identity unit with siblings parallel is the
field's convergent shape (Livewire per component, LiveView per view,
React's `useActionState` per hook;
[`events_research/research-rerender-preservation-and-concurrency.md`](events_research/research-rerender-preservation-and-concurrency.md)
dimension 2). The containment scope is citry's own, because citry is
the framework where a parent's response rewrites its children (5.3),
so parent-child overlap is exactly the pair that must never
interleave; the DAG carries that scope one edge at a time, so an event
dispatched from an anchor sitting inside two overlapping in-flight
scopes simply holds one edge to each.

**Settled means applied.** An in-flight event holds every event that
depends on it until its response's actions have been **applied to the
DOM**, not merely received: a dependent event must see the world its
predecessor's render produced, and carry the token that render
delivered, or the edges are cosmetic. Applied means all of the
result's actions processed, whatever their kinds, so a result with no
render action settles the same way: a data-only result settles at
promise resolution and holds its dependents no longer than its own
application. The timing
fields (4.3) split along the same line: a blocking delay
(`wait: true`) is part of the application, so it holds the event's
dependents for its duration, while a scheduled `wait: false` action
holds nothing, safe exactly because its fire-time re-checks (target
re-resolution, liveness, and the epoch comparison, 4.3) drop it if
the world moved on while it waited.

**Failure settles too.** A transport error, an error result, or a
timeout settles the call and releases its dependents; a hung request
must never freeze a subtree forever. The timeout is therefore bounded
by default: `configure({timeout})` (5.2) defaults to 30000
milliseconds, overridable per call through `sendEvent` opts, and an
unbounded setting is deliberately not offered, because a queue that
holds neighbors cannot afford a request that never stops holding
them. A timeout rejects the
caller's promise with the timeout error, fires `citry:events:error`,
clears busy state, and releases the dependents; the server is still
not cancelled (the 5.2 stance), and a response that arrives after its
call timed out is dropped with the drop event (reason `timeout`) and a
debug log, because its caller was already told it failed.

**Dequeue re-verifies, batches, and cancels early.** When an event's last edge
settles it becomes dispatchable. Before anything goes on the wire, the queue
maps its stored logical dispatch-owner record into the active graph revision
and re-verifies that owner's containment against not-yet-settled events. It
separately verifies that the physical carrier still belongs to a live target
region. Morph may replace or relocate that carrier, but its DOM position never
changes the event's source logical owner.
Re-verification adds edges only to events enqueued earlier that are
still unsettled, preserving the invariant that edges point at earlier
events, so the graph stays acyclic; overlap with an event enqueued
later needs no edge from this step, because the later event already
holds its own enqueue-time edge to this one. A live logical owner and carrier
send. A missing logical owner or dead carrier cancels early: the event is never
sent, its promise rejects with the
named `cancelled` reason, the drop event fires (reason `cancelled`,
5.2), and a debug line records it. A queued click on a region that a
predecessor's render just replaced must not fire a ghost call at
whatever now occupies the position. When several events become
dispatchable together, they batch into **one** envelope: each stays
its own `calls[]` entry with its own promise and its own result (4.2
reserved the array from day one; this is Livewire-style
cross-component bundling, and it is why a burst costs one request). A
batch larger than the envelope's sixteen-call cap splits into
successive envelopes in order. Two `@event` knobs govern a handler's
place in this (3.5): `bundle=False` keeps its calls out of shared
envelopes, and `latest_wins=True` lets a newer call drop queued-not-sent
predecessors and abandon an in-flight one, sending without waiting for
the abandoned response, which is exactly why that opt-in is the
author's statement that overlapping runs of the handler are safe.
Neither knob has a call-site form by design: a call site that needs
different semantics names a different handler.

**`wait: false` joins no graph.** A send with
`{wait: false}` neither waits nor is waited on: it fires
immediately, it gains no dependency edges, no later event gains an
edge to it, and its late
responses are exactly what the per-anchor epoch guard (4.2) exists to
net. The guard is unchanged and remains the floor beneath the queue
for the three things the queue cannot see: `wait: false` sends,
responses arriving from calls the graph holds no edge for (a targeted
render from an unrelated anchor, 5.5), and future transports with
different delivery orders.
The send-level `wait` is the sibling of the action-level `wait` of
4.3; both mean "do not hold the queue for me", one at the event
queue, one at the action-application queue. The documented trade for
`wait: false` targeted renders is in 5.5: last-arrival-wins ordering.

**Busy state spans the queue.** The user's gesture, not the send,
starts the pending UI: `data-citry-busy` stamps and `$loading` counts
from enqueue, one continuous busy state through queue, flight, and
apply. A button whose click is waiting behind an in-flight ancestor
looks busy, because to the user it is: the gesture is already
committed, and a control that shows idle while its click sits in the
queue misreports it.

**Recurring timers do not pile up.** A `@c-poll` tick that fires while
the binding's previous call is still queued or in flight is skipped
with a debug breadcrumb, never enqueued behind it: at most one
outstanding call per recurring binding, the queue's own tick-skip
rule. (Timer lifetime is the separate concern of 5.5's machinery item
5: one timer per element, retired with its region.) Debounced two-way
flushes enqueue like any send and carry the piggybacked updates as
always (4.2).

**What the queue replaces, and its fallback.** The concurrency
research recommended drop-plus-surface alone for the parent-child
overlap (its R2), on the ground that no surveyed framework derives a
serialization scope from the component tree. The queue supersedes that
recommendation: the tree-scoped race is a citry-specific consequence
of fresh ids plus whole-subtree re-renders, the field's convergent
shape wherever serialization exists is "serialize within one identity
unit, siblings parallel, nothing dropped", and the maintainers of the
largest queue-owning system state serialization as the only safe
default for UI-affecting state (Livewire's `#[Async]` warning, quoted
in the research). Drop-plus-surface is recorded as the fallback, and
the evidence window decides which release ships it: if the queue work
package's harness (`events_plan.md` WP16.3) proves
settled-means-applied undeliverable, v1 ships R2's
drop-plus-surface behind the same drop event; if the post-v1 dogfood
port (section 13) proves the queue impractical through head-of-line
blocking the knobs cannot relieve, a v1.x release ships the same
fallback and the queue returns as a v2 design (the decision record is
14.3.4; the falsifier is 15.11). The fallback replaces only the
containment edges: same-anchor overlap still serializes, per R2's
other
half (per-anchor serialize-with-merge: at most one in-flight call per
anchor, later sends coalesce and follow as one request), so a rapid
second send from one instance still waits for its predecessor's
response and carries the refreshed token instead of racing it.
Send-versus-apply pipelining (dispatching a dependent while its
predecessor's actions are still applying) is a recorded v2 candidate,
not designed (16.1).

The test that falsifies the queue's core rule, runnable in the WP16.3
harness: with a slow parent poll in flight, a child send must wait and
then observe the parent's applied render (fresh token, fresh DOM)
before it fires; with two sibling widgets, one slow save must never
delay the other's toggle; an event enqueued under two overlapping
in-flight scopes must dispatch only after both settle (one edge each);
and a network-failed send must release its dependents within the
timeout.

---

## 6. Transports

### 6.1 The dispatcher boundary

**What the dispatcher does, in plain terms.** When a user clicks a
button and the browser runtime sends an event, some server code has to
receive that request, work out which component instance and handler it
names, check permissions, run the handler, and package the results for
the browser to apply. That code is the dispatcher. It is the receiving
end of client-to-server calls, never a sender: the server does not
initiate anything in v1 (server push is v2, section 8). There is exactly
one dispatcher implementation, and every transport hands its requests to
it.

**The envelope** is the one JSON object a transport hands the dispatcher
per request: the call envelope of 4.2 (`protocol`, `requestId`, optional
`capabilities`, and `calls`, where each call carries `componentClassId`,
`handlerName`, optional `callerRenderId`, `args`, optional `stateToken`,
optional `stateUpdates`, and optional `sendSequence`). The
dispatcher returns the matching result envelope of 4.3 (`results[i]`
answers `calls[i]`). Transports never look inside either; they carry
bytes.

How the pieces relate (the transport is swappable and dumb; the
dispatcher is single and owns all behavior; codecs sit at the transport
edge translating request shapes into the one envelope shape):

```
browser runtime    transport (swappable)    server (single)
---------------    ---------------------    ---------------
sendEvent(...)   --call envelope (4.2)-->   codec decodes the
                   (as bytes)               bytes into the
                   HTTP POST today;         envelope (6.2)
                   Later: WS frame or              |
                   postMessage bridge              |
                                                   |
                                                   v
                                    EventsDispatcher.dispatch(
                                      envelope, ctx
                                    )
                                    runs the whole pipeline
                                    (table below)
                                                   |
                                                   |
                                                   v
applyActions     <--result envelope (4.3)--  encoded results
(5.2)               (as bytes)
                    same transport
```

```python
@dataclass(frozen=True, slots=True)
class TransportContext:
    # "http", "ws", "graphql", ...
    transport: str
    citry: Citry
    # Django HttpRequest, ASGI scope, WS connection
    host_request: Any = None
    # case-insensitive view; empty when N/A
    headers: Mapping[str, str] = ...

class EventsDispatcher:
    def dispatch(
        self,
        # the decoded call envelope of 4.2
        envelope: dict,
        ctx: TransportContext,
    ) -> dict:  # the result envelope of 4.3
        ...
    async def dispatch_async(
        self,
        envelope: dict,
        ctx: TransportContext,
    ) -> dict: ...
```

What the dispatcher owns, item by item (transports own only bytes,
framing, CSRF attachment, and native error signaling; anything two
transports would both need belongs in the dispatcher, never duplicated):

| Responsibility | What it does | Implementation note |
|---|---|---|
| Envelope validation | Structural check of the call envelope (field presence, types, the 16-call cap) before any other work. | Plain Python checks, not JSON-Schema loading at runtime; the protocol package's schemas bind in tests (plan WP18). Cap violations map to `payload_too_large` (413). |
| Version and capabilities | Reject unknown protocol majors; resolve an absent `capabilities` field to the baseline; hand the resolved set to action encoding so `morph` downgrades to `replace` and no action kind outside the set is ever emitted. | The baseline constant is the protocol package's `CAPABILITIES_BASELINE_V1`; rejections mirror per call so `results[i]` always answers `calls[i]`. |
| Component and event resolution | The per-event URL is authoritative; explicit `componentClassId` and `handlerName` fields must match it. A failed lookup produces the wire error codes `unknown_component` / `unknown_event` (protocol constants from the 3.7 table, status 404), never a lookup of any user-defined name: there is no magic fallback component or handler to define. Custom not-found behavior hangs off the `on_event_error` hook or host middleware on the real URLs. | `Citry.get_component_by_class_id` resolves the class; wire names come from the handler metadata captured at class creation (plan WP7). |
| Token verification and updates | Verify the signed `stateToken` (malformed 403, expired or rotated-out 409; the split is payload well-formedness, per the error-codes rule in 4.3), rebuild State, apply `_model`-gated `stateUpdates` with per-field 422s. | `verify_state_token` / `apply_state_updates` (plan WP8). |
| Args validation | Validate the wire args payload against the handler's `data` schema with the 3.3 coercions; failures are per-field 422s, never host 500s. | The data-schema machinery (plan WP9) returns structured results that the error mapping consumes. |
| Per-call context and guards | `on_event` emit (veto), then the `_context` hook, then guards most-specific-wins (engine default, component `_guard`, `@event(guard=...)`). | Pipeline order is normative (3.6, 3.7): a guard must see `_context`'s result. |
| Handler invocation | By-name injection of `data` / `state` / `context` / `request` / `event`; the same values populate the ambient attributes on the per-call events instance. | Async dispatch awaits `async def` handlers; sync handlers offload to a worker thread via the routing helper `call_maybe_sync` (plan WP2). |
| Action encoding | Return-value coercion, result resolvers, faithful ordering, and the render-to-fragment serialize. | The actions module (plan WP11); a `Render` re-enters the normal fragment serialize, so its HTML carries a fresh manifest. |
| State re-sign | Changed State means a fresh token in the response: riding the render action's manifest when there is one, else as an explicit `state` action placed before the handler's actions (4.3). | Mint via plan WP8; the request's `sendSequence` echoes per result. |
| Error mapping | `EventError` and uncaught exceptions map to the fixed code-to-status table (3.7); tracebacks only in debug mode. | Message content is contract: tests assert the text, not just the exception type. |

The "custom transport" story is honest and small: call the dispatcher
from your own endpoint (a GraphQL mutation resolver is about ten lines;
section 16 tracks a packaged GraphQL story). Client-side the mirror entry point
is `Citry.events.registerTransport(name, {send, subscribe?})`.

### 6.2 HTTP (v1)

The routes from 3.8. The handler parses the envelope through a payload
codec, dispatches, and encodes the result. Sync handlers are offloaded to a
worker thread under ASGI (so a blocking ORM call does not stall the event
loop); `async def` handlers are awaited natively under ASGI and rejected
with a pointed error under WSGI. How that split is decided: there is no
runtime detection; the knowledge lives in the host adapter the app
mounted (`citry.contrib.asgi` / `wsgi` / `django` / `fastapi` / `flask`),
because each adapter knows its own concurrency model. The ASGI adapter
runs on an event loop, so it awaits `async def` handlers and pushes sync
ones through the routing substrate's `call_maybe_sync` helper (12.3)
into a worker thread. WSGI and sync Django are thread-per-request with
no event loop: sync handlers run inline (blocking is the model there),
and an `async def` handler is rejected with the pointed error naming the
fix (deploy under ASGI). The FastAPI and Flask adapters inherit the
behavior of the ASGI and WSGI cores they wrap.

**Payload codecs (uplink)** translate whatever a request carries into
the one call envelope (4.2) before the dispatcher sees it. They are a
registry keyed by content type; user codecs ride
`CitrySettings.event_payload_codecs` and prepend to the built-ins:

| Codec | Content type | Status | What it does |
|---|---|---|---|
| Envelope | `application/citry-events+json` | v1 | The identity codec: the body already is the envelope. What the runtime sends. The vendor media type is what distinguishes an envelope from flat JSON, so classification never depends on body shape (a user schema could legitimately declare fields named `v` or `calls`). The batch route takes only the envelope and accepts it under plain `application/json` too, since a batch body has no flat reading. |
| Flat JSON | `application/json` | v1 | Flat handler fields as one JSON object (`POST {"email": "a@b.c"}`), per-event route only: what an external API client sends without knowing the protocol. Fields bind per 3.3's JSON rules (native types, strict); the reserved `_citry_state_token` / `_citry_caller_render_id` keys map into the envelope like the form codec's. |
| Form | `application/x-www-form-urlencoded` | v1 | Classic form posts: fields become the args payload; the reserved `_citry_state_token` / `_citry_caller_render_id` fields map into the envelope; the source-aware binding rule (3.3) turns the strings into typed values, including `int` / `float` / `bool` fields. |
| Query | GET query string | v1 | Args ride as query parameters, bound per the same source-aware rule (3.3); the state token rides `_citry_state_token` only when the handler declares State (3.5). Browser calls additionally reserve `_citry_protocol`, `_citry_request_id`, and JSON `_citry_capabilities` for the flattened envelope, plus `_citry_caller_render_id` and `_citry_send_sequence` for call metadata. |
| Multipart | `multipart/form-data` | v1.x | File uploads: the envelope JSON rides as one part, each file as its own part, bound to `UploadedFile` fields ("Files, precisely" below). |
| Msgpack | `application/msgpack` | candidate, unscheduled | A binary envelope for apps where payload size matters; would pair with symmetric response encoding negotiated via `Accept`. Open an issue when someone measures the need. |

CBOR would fill the same niche as msgpack with less Python and JS
mindshare; schema-compiled formats (protobuf, Avro) are a wrong fit for
a dynamic envelope and are not planned.

A codec is a small object:

```python
class MsgpackCodec:
    # the content type this codec claims
    content_type = "application/msgpack"

    def decode(self, body: bytes, request: RouteRequest) -> dict:
        # Return the call envelope of 4.2, exactly as if it had
        # arrived as JSON. Raise EventError(status=400) for a
        # malformed body.
        return msgpack.unpackb(body)

citry = Citry(event_payload_codecs=[MsgpackCodec()])
```

**Downlink needs no codec registry.** The uplink registry exists because
browsers legitimately send different request shapes (envelope JSON from
the runtime, urlencoded from a plain form, query strings on GET). The
downlink consumer is always known: the citry runtime, which reads
envelope JSON. So the response's content type is the server's choice,
keyed on the request's `Accept` intent, never on the request's content
type: `application/json` (the result envelope) for runtime-originated
calls, HTML or a 303 for the compatibility mode below. A future binary
codec would extend this by declaring symmetric response encoding; until
one exists there is nothing to configure on the way down.

**Files, precisely.** The default request is `application/json`. At send
time the client runtime deep-scans the outgoing args payload for `File` /
`Blob` / `FileList` values (a value check, never inferred from bindings,
so files attached via Alpine or plain JS are caught) and switches that
one call to multipart: the envelope JSON rides as one part, each file as
its own part, referenced from the args payload by path.
Server-side, the multipart codec reassembles the envelope and binds file
parts to `UploadedFile`-annotated fields on the handler's `data` schema.
`UploadedFile` is citry's own framework-neutral class (`filename`,
`size`, `content_type`, a **synchronous** `read()`, `save(path)`, and
`native` exposing the host's underlying object), the converged shape of
Ninja's and FastAPI's equivalents.
Files can never travel through the state channel: State is
JSON-serializable by contract, so a `$state` write holding a `File` is a
loud client-side error naming event args as the file channel. The
multipart codec gets a dedicated CSRF conformance fixture (multipart
endpoints are a known CSRF soft spot; the `X-Citry-Events` header and
host-token rules apply to it unchanged).

**Result resolvers (return values to actions)** teach the return
channel the app's own value types, so the strict coercion table (3.4)
does not force conversion boilerplate on every handler. A resolver is
registered once, engine-wide, and claims values of its type. (The name
is deliberate: a resolver turns a Python value into action objects;
nothing here is a string format.)

```python
class PydanticResolver:
    def resolve(self, value, events):
        # -> list[Action] | None;
        # None means "not mine, keep looking"
        # (later resolvers in event_result_resolvers run)
        if isinstance(value, pydantic.BaseModel):
            return [
                actions.Data(value.model_dump(mode="json"))
            ]
        return None

citry = Citry(event_result_resolvers=[PydanticResolver()])
```

After that, any handler anywhere may `return my_model` bare; the
resolver turns it into a `Data` action. The coercion pipeline per
returned item: action instances pass through, then the built-in
coercions (element to `Render`, dict to `Data`, list flattening,
`None`), then registered resolvers in order with the first claim
winning, then the pointed error. Built-ins run first so resolvers can
only teach the channel new types, never change what a dict or an
element means. Resolvers map to any action, not just `Data` (a domain
notification object can resolve to `Dispatch`), and the optional
Pydantic integration is delivered as exactly this resolver, keeping the
core dependency-free.

Payload codecs and result resolvers are what "pluggable formats"
concretely means. Note the direction split: form data (urlencoded,
multipart) is a request format, while responses are envelope JSON or
HTML via the compatibility mode; anything beyond that is a user result
resolver.

**Compatibility / no-JS mode (v1).** When the per-event endpoint receives
`Accept: text/html` (or a classic form post without the `X-Citry-Events`
header), the response is not an envelope: the primary render action's HTML
is the body, a redirect becomes HTTP 303, and errors carry their HTTP
status. Two things fall out, both intentional: a plain
`<form method="post" c-action="submit_url">` (the URL provided by
`template_data` from `self.events.url("submit")`) works with
JavaScript disabled, and htmx or Turbo users can point `hx-post` at an
event URL and get a fragment back without adopting the citry client. This
keeps the roadmap's "no htmx pack" rule while staying interoperable, and it
is a real adoption path for livecomponents users mid-migration.

### 6.3 WebSocket (v2)

One socket per page, multiplexed at `ext/events/ws`, never per component
(the unanimous industry answer). Frames wrap the same envelopes with a
`type` discriminator (`call` / `result` / `push` / `ping` / `pong`);
correlation is the envelope `requestId` the client already mints. Because every
call carries its own state token, **the socket holds no per-connection
component state**: it is a faster pipe plus a push channel, reconnect is a
re-subscribe with nothing to resume, and the dispatcher is byte-for-byte
the HTTP one (the conformance fixtures run against both). Requires ASGI
and a `WSRoute` sibling of `URLRoute` (section 12); WSGI hosts simply stay
on HTTP. The client upgrades only when the server advertises the transport
in the page manifest. SSE remains on the table as the cheaper push-only
half (down-only transport, zero protocol change); measured before v2
commits.

### 6.4 postMessage (v1.x, the proof the transport boundary holds)

Concrete consumer: sandboxed or cross-origin preview iframes where the
planned Storybook adapter or docs-site live example cannot use a safe
same-origin route or reverse proxy with ordinary cookies and CSRF. The iframe
runtime registers a postMessage transport; a small bridge on the embedding
page forwards envelopes to its own HTTP transport, which has cookies and
CSRF. Same-origin and reverse-proxied previews use HTTP directly. No
server-side work is required for the bridge, and the envelope crosses two
transports unchanged, which is the proof the transport abstraction is real.
If the WS or postMessage transport ever requires changing the dispatcher
signature or an envelope field, the abstraction is fake and gets redesigned;
see section 15. The bridge is also a policy point: a preview host can
allowlist events by inspecting envelopes, possible precisely because the
protocol is transparent JSON.

---

## 7. State model and security

### 7.1 What round-trips: the signed State, nothing else

At serialize time, for each rendered instance of an Events-declaring
component with a State, the extension captures the State (via
`state_data`, section 3.2), serializes it to JSON, and signs it into the
state token. The token is **opaque at the protocol level**: the client
stores and echoes it, never parses it, so its internal format stays a
per-binding detail and no cross-language canonical-JSON signing problem
exists. The Python binding's format:

```
cev1 . base64url(payload_json) . base64url(hmac_sha256(secret, payload_json))
payload_json = {"v": 1, "c": "<class_id>", "s": {<state>}, "t": <mint epoch>, "x": <expiry epoch | null>}
```

Rules, each closing a named prior-art hole:

- Full-length HMAC-SHA256, constant-time comparison, bound to the class id
  and protocol version. The secret's single home is the new
  `CitrySettings.secret`, with a pointed error at first mint naming the
  one-line fix per host (Django users pass `SECRET_KEY` via the
  `citry.contrib.django.secret()` helper). The secret accepts a list for
  rotation: first entry signs, all entries verify.
- **JSON-safe values only, enforced at mint time** with an error naming
  the component and the State field. Kwargs are unconstrained; only State
  must serialize. No pickle, no rich-object revival, ever: verified state
  re-enters through `cls.State(**s)`, a plain dataclass constructor that
  raises on unknown or missing keys. There is no hydration machinery to
  attack (section 7.6).
- Size-capped (State meta `_max_bytes`, default 8192). The cap is a **design
  smell canary, not a technical limit**: the audit measured real tokens
  at 150 to 300 bytes (section 1.4), so a component approaching the cap
  is holding state that belongs in the database, and the error says so
  (keep an id in State, reload the rest in the rebuild). The one nearby
  technical budget is GET handlers, whose token rides a query parameter
  under practical URL length limits of roughly 2 KB.
- Signed, not encrypted: State values are visible to their own user, like
  anything rendered into HTML. The docs lead with the symptom ("anything
  in State is visible in the page source"); the mitigations, in order: do
  not put secrets in State; keep an id in State and re-derive per call;
  use server-side State storage when the values must not ride in the token.
- Optional expiry via State meta (`_max_age`, a `timedelta`); expired or
  rotated-out tokens answer `stale_state` (409), malformed ones
  `invalid_state` (403; the split is payload well-formedness, per the
  error-codes rule in 4.3), and both degrade per component, not per
  page.

On each call the order is: verify token (cheapest rejection first), check
the class id against the route, rebuild `cls.State(**s)`, apply `stateUpdates`
to `_model` fields (7.2), validate args, run `_context`, run guards, run the
handler. After the handler, a mutated State is re-signed and returned
(inside the fragment manifest when a render action exists, as a `state`
action otherwise), so the client's stored token always reflects the
latest state and the browser is never left holding stale client-side
state.

An optional server-side state store (the token becomes a random key into
`Citry.cache`) ships in v1 as the opt-in `_storage = "server"`
State meta. It exists for three cases. Two of them a signed
round-tripping token cannot serve: State too large to ship back and
forth on every call, and State whose values must not be readable in the
page source at all (the token is signed against tampering, not
encrypted, so anyone can decode and read its payload; the visibility
doctrine of 7.2). The third is the livecomponents migration's first step
(10): port a component mechanically while keeping server-held behavior,
then switch to signed tokens as a separate, optional second step. The
cost of opting in: it adds the shared-cache multi-worker constraint
fragments already document, and the prior art that led with server-held
state grew the worst failure modes (session TTL storms, Redis in dev).
The protocol does not change either way; that is the point of the
opaque token.

### 7.2 State visibility and writability: `_public` and `_model`

Two layered, server-side sets on the State class govern what the client
side may touch. Handlers are unaffected: they read and mutate every
field, always.

- **`_public`**: the fields templates and bindings may use, and the only
  fields whose plain values ship in the events manifest (4.4), which is
  what one-way bindings read; non-public fields ride only inside the
  opaque token, invisible to the binding layer. Defaults to **all
  fields**. Public is about API surface, not secrecy: the token is
  signed, not encrypted, so nothing in State is secret from its own user
  either way (7.1).
- **`_model`**: the subset of public fields the client may write
  (through two-way bindings or `$state`); `stateUpdates` entries outside it
  are rejected, and each accepted value must satisfy the field's type.
  Defaults to **the same fields as `_public`**: public means visible
  and writable, and `_model = (...)` exists only to clamp down (a
  visible-but-read-only display flag). Every `_model` field must be
  public (template-load error otherwise). An earlier draft defaulted
  `_model` to the set of fields found by a static template scan. The
  side effect: bindings defined dynamically (e.g. inserted via
  `c-bind="{...}"`) were invisible to the scan, so they had to be
  declared in `_model` explicitly. In practice that forced even the
  simplest examples to spell out the `_model` list, dragging an
  advanced, niche feature into the happy path.

  The class descriptor in the events manifest carries `writableStateFields` only when this
  list narrows `_public`; omission therefore preserves the common all-public-
  fields-writable case without repeating field names. `writableStateFields: []`
  is not an omission: it is the explicit capability for read-only public State. The
  browser applies that gate before local mutation or pending-queue insertion,
  and refreshes the gate when a later manifest updates a live class
  descriptor. If the refreshed contract removes a field that was already
  pending, the runtime drops that pending update with a warning; a failed
  in-flight call likewise cannot requeue a field the current descriptor no
  longer permits. This prevents deploy skew from making every later event
  retry an update the server must reject. The client gate is a convenience and
  early diagnostic, not a replacement for the server's authoritative update
  validation.

The security doctrine, stated as the symptom: **every State field is
client input, exactly like a form field.** State exists for exactly two
purposes, and each carries the same obligations as its plain-HTTP
equivalent: re-rendering UI (apply the same permission checks as when
serving the page fresh) and action or form submission (treat it like
any request body the browser sent). The signed token makes state
trustworthy *as the server last minted it*; the `stateUpdates` channel makes
public fields writable on top. Pretending State is secure would be
worse than admitting it is input, because a false sense of security is
the more dangerous failure. A handler must authorize what it does with
state values the same way it authorizes its args (the audited
production handlers already behave this way: fetch by id, then check
permissions). Omitting a field from `_public` keeps it out of bindings and
`$state`, but not out of the browser: with signed storage it still rides inside
the readable token. A non-public field is a full member of State (declared,
typed, rebuilt on every call, readable and writable in handlers), but it is
absent from the client-side values map and cannot be read or written by
templates, bindings, or `$state`. Use `_storage = "server"` when the State
values themselves must not ride through the browser.

Two properties of the omission model, stated because they matter:

- **The underscore namespace on State belongs to the framework.**
  Fields are the non-underscore annotated names; underscore attributes
  are the State meta API (`_public`, `_model`), and an unrecognized
  underscore attribute is a class-definition error. That rule is what
  makes typos loud (`_pubic = (...)` fails instead of silently doing
  nothing) and lets the meta API grow without ever colliding with a
  user's field.
- **A narrowed `_public` fails closed.** Once a component declares
  `_public`, a newly added field is private until listed, which is the
  safe direction; the declarative paths fail loudly (a `:c-` binding to
  a non-public field is a template-load error), while `$state` reads of
  a non-public field are simply `undefined`, the same as any key the
  client has no business knowing exists.

Expected usage frequency, recorded as a design bet: most components set
neither (the defaults do the right thing), a few narrow `_public` for
server-truth fields, and `_model` clamps are rare.

### 7.3 Exposure

The remotely callable surface of a component is exactly the
non-underscore methods its author wrote inside `class Events`. No other
method, property, or attribute is reachable; there is no dotted-path
traversal of any object graph; extra arg keys are rejected, not absorbed.

### 7.4 CSRF and auth

- **Universal floor, all hosts**: POST by default, the `X-Citry-Events: 1`
  header required (unattachable by HTML forms, forces a CORS preflight
  cross-origin), and `Origin` / `Sec-Fetch-Site` same-origin verification.
  The header requirement covers every JSON-bodied call: the envelope's
  `application/citry-events+json` vendor type, any other `+json` suffix
  type, and flat `application/json` alike (so an external API client
  sends one static header); a form post without the header takes the
  compat path (6.2).
- **Host token by default.** Under Django the routes are plain views, so
  Django's CSRF middleware applies untouched; the client runtime
  auto-attaches the token (by default it reads Django's `csrftoken`
  cookie and sends it as `X-CSRFToken`; the `csrf` config object in 5.2
  renames either side or supplies a non-cookie token source, covering
  FastAPI/Flask conventions). The Django
  integration must pass a security review without a single `csrf_exempt`;
  that is a falsifier (section 15). The runtime never invents its own
  token scheme. (The audit's hand-rolled `$fetch` helper exists mostly to
  inject the CSRF token; this is that helper, absorbed.)
- GET handlers are opt-in, csrf-exempt by nature, and read-only by
  contract; their args ride as query parameters, and the state token
  rides as a `_citry_state_token` query parameter only when the handler
  declares `state` in its signature (3.5), so read-only GET URLs stay
  pasteable and token-free (the docs note URL length limits and the
  id-plus-reload fix for large-State components).
  The per-handler descriptor carries `usesState: true` only when the handler
  declares the State injectable, so the browser can enforce that URL rule.
  The built-in browser transport selects GET for a single call to a
  GET-declared handler. It serializes scalar string, boolean, and finite
  number args, and non-empty arrays of those values as repeated query
  parameters; a value with no unambiguous flat-query representation rejects
  locally with `transport_error`. Browser calls also carry `_citry_protocol`,
  `_citry_request_id`, and JSON `_citry_capabilities`, preserving version rejection,
  response correlation, and morph/action negotiation from the ordinary
  envelope. `_citry_caller_render_id` and `_citry_send_sequence` preserve call metadata;
  `_citry_state_token` appears only for a state-declaring handler. The query codec
  removes those reserved fields before input validation. A GET call never flushes or consumes pending
  two-way writes: those remain queued for the next mutating call. A mixed or
  multi-call envelope still uses the POST-only batch endpoint, including when
  one item names a GET-declared handler.
- **Guards inherit**: engine-wide default, per-component `_guard`,
  per-handler `@event(guard=...)`, most specific wins. A guard is
  `callable(events)` that raises `EventError(status=403)` to deny, reading
  `self.context` (3.6) or `self.request.native`. Opt-out, not opt-in
  (livecomponents' per-method decorator is the anti-pattern: forgetting one
  method is an open endpoint). Honest limitation, documented: citry cannot
  inherit "the page's auth" framework-neutrally; the guard plus host
  middleware on the real per-event URLs are the tools.
- Abuse limits: envelope size cap (413), `calls` length cap (16 in the
  schema), state verified before args are parsed, `on_event` as the
  rate-limit attachment point.

### 7.5 Rich components and slots

Because State is separate from the render inputs, **any component can
declare handlers**, including components that take ORM kwargs or receive
slot fills. What such a component cannot do is faithfully rebuild itself:
slot fills live in the parent template and are not available at event
time, and the separate State makes that structurally visible instead of a
surprise. Concretely:

- Handlers on a slotted component can freely return data, dispatch events,
  and surgically update regions inside it by rendering leaf components
  into explicit targets (`Render(Badge(...), target="#badge")`).
- A `render` action replaces the targeted subtree with exactly the tree
  the handler returned; nothing about the instance's original render is
  replayed. Fills are call-site content, so a handler that re-renders a
  fill-receiving instance renders it without the fills, or with whatever
  different fills it passes (`Card(title="hi", slots={"footer": ...})`).
  This is the same contract that lets a handler return a different
  component class entirely: the handler's return is authoritative, and
  the error path is the ordinary render-time input validation (a
  required slot missing fails the render loudly, whoever triggered it;
  nothing here is events-specific). The one caveat the docs carry: a
  reusable component with optional slots that re-renders itself simply
  will not contain the call site's fill content. Authors of generic
  interactive library components therefore wrap the interactive region
  in its own fill-free child. The audit found zero fill-receiving interactive
  components in production app code, so this is a library-author note,
  not an app-code hazard.

**The golden rule to teach** (it earns a highlighted spot in the user
guide): the component tree a handler renders shares NO inputs and NO
fills with the component's original render. There is no hidden
carry-over; a handler passes every input explicitly, exactly like any
other Python call site. That is not a limitation to soften but the
source of the freedom above: because nothing is implicitly reused, a
handler can re-render the same component (passing its inputs again,
typically from State), render something else entirely, or render
nothing and just return data.

Storing raw template source server-side to replay fills (the
livecomponents mechanism) is rejected outright; citry renders from
component entry points, never from captured template text, and never
caches serialized HTML. Cross-request output caching uses the detached,
validated replay artifact designed in [`caching.md`](caching.md).

### 7.6 The prior-art CVE record, and what it dictates

Every serious vulnerability in the surveyed family came from the same
root: the client sends rich, interpretable structures and the server
rehydrates or traverses them.

- django-unicorn CVE-2021-42053 (stored XSS: AJAX-returned values were not
  HTML-encoded) and CVE-2025-24370 (class pollution: the endpoint applied
  client-supplied dotted property paths, letting crafted payloads traverse
  into Python internals; XSS, DoS, and auth bypass). Its docs also warn
  that its server-side component pickling means cache write access equals
  remote code execution.
- Tetra pickles the whole live component into an encrypted token; a leaked
  key means attacker-crafted tokens reach the unpickler, mitigated by a
  whitelist unpickler that also broke its own documented client-call API.
- Livewire has a history of property-hydration remote-code-execution
  issues (client-sent component state unmarshaled into live objects), most
  recently CVE-2025-54068 in Livewire v3.
- livecomponents stores pickle in Redis and treats possession of the
  session id as authorization.

This design's answers, restated once: events are referenced by name only;
args are structured JSON bound to declared signatures; there are no
expression strings, no property paths, and no revivable objects anywhere
in the protocol; exposure is opt-in by placement; and the only thing the
client holds is an opaque signed token whose contents re-enter through a
plain dataclass constructor.

---

## 8. Server push

Deferred, with the extension points designed now and a v1 stopgap:

- **v1**: `@c-poll.30s="refresh"` (interval events, tab-aware, calling the
  component's own handler). Zero infrastructure; covers dashboards and
  job-status pages.
- **v2**: push over the WebSocket (or SSE) channel. In plain terms, a
  **topic** is a named channel an instance subscribes to so server code
  can later send updates to everyone watching the same thing: a
  component showing project 42 subscribes to `project:42`, and a view or
  background task pushes actions to that name whenever the project
  changes. A component declares
  topic templates formatted from its State at render time
  (`Events._topics = ("project:{project_id}",)`); the serializer stamps the
  **signed topic names** into the events manifest (Turbo's signed stream
  names), so a client can only subscribe to topics it was handed. Server
  API: `citry_instance.extensions.get_extension("events").push(topic, *actions)`
  (instance-attribute access to the extension manager, not the retired
  module path)
  from anywhere (a view, a task queue). The pushed payload is the same
  actions list as an HTTP response, so push is an additive transport, not
  a second protocol. Reconnect is a re-subscribe; missed pushes are lost,
  and the documented correctness pattern is push-to-refresh (push a named
  event, listeners send their own refresh), not push-as-source-of-truth.

---

## 9. OpenAPI and schema generation

Handlers are introspectable signatures, so citry can do what django-ninja
does and no interactive framework ever has (and what the audit shows the
maintainer already reached for: the production app wraps every View in
hand-declared ninja Schemas):

- Each handler's request schema IS its `data` schema (3.3), the same
  class that powers runtime validation, so the document can never drift
  from behavior, and operations get real named schemas (`ContactIn`)
  instead of synthesized per-operation objects.
- `citry ext run events openapi --out openapi.json` (an `ExtensionCommand`;
  the CLI substrate is complete) emits OpenAPI 3.1: one operation per
  (component, event) over the per-event URL template
  (`ext/events/e/{class_id}/{event}`), `operationId`
  `<ComponentName>_<event>`, request body (or query parameters for GET)
  from the handler's `data` schema, the 422 field-error shape, and `data` typed
  from the return annotation for handlers annotated with JSON-able
  returns. `--only-data` restricts to those handlers, the useful
  API-surface view. Handler docstrings become operation descriptions (they
  are already API-reference quality per the house docstring rule).
- The same walk feeds the class descriptors in the events manifest, a
  future TypeScript codegen in `packages/js/citry-client`, and the planned
  Storybook extension. The component introspection API
  ([#26](https://github.com/citry-dev/citry/issues/26)) now exposes a separate,
  versioned and allowlisted projection of the same handler metadata. The
  manifest remains the browser runtime protocol; component introspection is a
  tooling contract and does not serialize the manifest.

### 9.1 Component introspection metadata

The Events extension implements component introspection version 1. A caller
requests it explicitly with `include_extensions=("events",)`. The `data`
object under the component's `events` extension entry has this exact top-level
shape:

```json
{
  "handlers": [
    {
      "name": "save",
      "methods": ["POST"],
      "request_schema": {
        "kind": "fields",
        "import_path": "shop.events.SaveIn",
        "fields": [
          {
            "name": "title",
            "required": true,
            "type_display": "str",
            "type_fidelity": "normalized",
            "description": null
          }
        ]
      },
      "return_type_display": "dict[str, int]",
      "return_type_fidelity": "normalized",
      "description": "Save one item.",
      "debounce": null,
      "throttle": null
    }
  ]
}
```

Every handler object always contains exactly these keys:

- `name` is the public wire name, including a name supplied by
  `@event(name=...)`.
- `methods` contains the resolved uppercase HTTP methods. Their configured
  order is preserved.
- `request_schema` is `null` when the handler declares no `data` parameter.
  Otherwise it is an object with exactly `kind`, `import_path`, and `fields`.
  `import_path` is the safely copied schema-class import path when one is
  available, or `null`. A recognized runtime data schema has `kind: "fields"`;
  its fields remain in the schema adapter's declaration order. A schema the
  adapter cannot describe has `kind: "opaque"` and an empty `fields` array. An
  empty recognized schema has `kind: "fields"` and an empty array, so consumers
  can distinguish the two.
- Each request field contains exactly `name`, `required`, `type_display`,
  `type_fidelity`, and `description`. Type display uses the safe normalized
  formatter from component introspection. Fidelity is `"normalized"` when
  display text is present and `"unavailable"` when it is not. Request field
  defaults and default factories are never included, even when the caller
  requests component default values.
- `return_type_display` and `return_type_fidelity` follow the same normalized
  or unavailable pair. The inspector reads the stored return annotation
  without resolving it: string annotations are copied, and unsupported values
  become `null` plus `"unavailable"`. It does not call `get_type_hints()`,
  import an annotation target, or call an arbitrary object's `repr()` or
  `str()`.
- `description` is the cleaned handler docstring or `null`.
- `debounce` and `throttle` are the resolved client timing values in
  milliseconds or `null`. A value must be a non-negative JavaScript-safe
  integer, at most `2**53 - 1`; larger values are invalid at declaration time.

The `handlers` array is sorted lexically by public wire `name`, independent of
Python method declaration order. This makes the versioned JSON stable while
preserving the configured method order inside each handler.

An absent effective `Events` declaration, including an explicit
`Events = None`, makes the inspector return `None`; the component then has no
`events` entry. An explicit or inherited effective `Events` class with no
handlers returns `{ "handlers": [] }`. The catalog's `extension_versions`
still records Events version 1 whenever the caller requests the installed
inspector, including when every inspected component returns `None`.

Version 1 deliberately excludes Python method names, injectable parameter
names, handler functions, `latest_wins`, `bundle`, State and raw State values,
topics, guards, context and CSRF callables, and all other executable or private
configuration. OpenAPI and the runtime manifest may expose different
allowlisted projections for their own purposes; those do not silently expand
this introspection version.

---

## 10. Migration

The maintained
[`events-migration-parity.md`](../../docs_site/content/guides/events-migration-parity.md)
matrix records every audited prior-tool capability, this design's answer, and
its delivery tag. It links the four source-framework migration pages and
serves as the acceptance checklist for v1. The summary argument per audience:

**From `Component.View`** (django-components): any number of named actions
instead of one method per verb; the `?type=` and verb multiplexing die (21
of 36 production components multiplex today, section 1.4); requests are
parsed and validated; the client half exists, so mutate-then-full-reload
(23 of 36 production components) becomes a targeted render or a
server-expressed `Redirect`. `get_component_url`'s powers return as
`events.url(name, query=..., fragment=...)`. For verb-shaped code, a
compat shim ships: `class Events(ViewEvents):` reserves `get`/`post`/...
handler names and adds one extra route (`ext/events/e/{class_id}`
dispatching by HTTP method). Only the verb-shaped route maps mechanically:
old handlers must replace host request parsing and response construction with
typed `data`, the neutral `request`, and Events return values. The compatibility
route does not require a State token, and verb handlers cannot inject `state`;
a named runtime call to a verb on a State-declaring component may still carry
the component token. The shim's docstring says to name events after actions
once a component has more than one mutation.

**From django-unicorn**: the template grammar carries over nearly verbatim
(`unicorn:click` -> `@c-click`, `unicorn:model.debounce-300` ->
`:c-query.debounce.300ms="refresh"`, a two-way binding naming its flush
handler); the class attributes that were
the wire state become a declared `State`; action methods move under
`Events`, and where unicorn re-rendered implicitly, the handler returns a
fresh component or explicit `Render`. Gone by design: implicit public class
attributes and `javascript_exclude` as the visibility model (only declared
State round-trips, and `_public` narrows its browser projection), plus
property-setter expressions on the wire (a one-line handler replaces them).
A two-way binding sends an explicit field delta alongside the current signed
token, which contains the full declared State; this is a clearer mutation
contract, not a claim that each request omits the rest of State. Django-forms
validation maps to `EventError` after normalizing each field's `ErrorList` to
one string message; a `form_class` sugar is a v1.x nicety.

**From Tetra**: `public(0)` attributes become State fields; `@public`
methods become `Events` methods; `await this.method()` becomes
`await sendEvent(...)`; encrypted pickled state becomes the signed JSON
State; `@public.debounce(200)` becomes `@event(debounce=200)`. Not
carried: making generated Alpine data the component state and identity model,
and the open `self.client.*` callback channel. Citry still supplies pinned
stock Alpine for expressions, directives, reactivity, and morphing, while its
graph owns component and slot scope. The closed action vocabulary plus
`onEvent` covers the legitimate callback uses; Tetra itself had to whitelist
that channel down after shipping it open.

**From livecomponents**: `@command` methods with `CallContext` become
`Events` methods; `call_context.state` becomes the `state` injectable, backed
by a declared strict-JSON State. Common execution results become explicit
return values (`ComponentDirty` becomes a fresh component or `Render`, an
explicit parent-region update becomes `Render(..., target=...)` or `Dispatch`
+ `onEvent`, and `RedirectPage` becomes `Redirect`). This is not a one-to-one
algebra: implicit dirty propagation, `find_one`/ancestor command navigation,
and history actions need deliberate replacements; history navigation uses
`PushUrl` or `ReplaceUrl`. `parent_id` threading disappears, and Redis with its TTL
expiry storms can be replaced by `Citry.cache` when server-held State is kept.
Migration is deliberately two-step, and the guide leads with it. Step one
preserves the server-held storage policy via `_storage = "server"`, but the
port still changes serialization to strict JSON, makes results explicit, and
requires `_public` to omit server-only values from the browser projection.
Step two, per component and optional, drops the server store for the signed
token. Components whose State cannot fit a signed token can stay on the server
store.

**The Component.Ninja idea** ships as a property of every handler: typed
args, typed JSON returns, per-operation URLs, 422 semantics, and the
OpenAPI command, without a second routing layer or a hard Pydantic
dependency. The commented-out sketch found in the production app (1.4) is
this exact shape, minus the machinery.

Features deliberately dropped from the union of prior-art capabilities,
each with its acceptance argument, are tracked in the migration guide
skeleton: ORM-pk argument revival (authorization footgun), mutable server
attribute bags (the CVE home), wire-level property setters and call
expressions (unauditable, and they mix render-time and event-time
contexts in one syntax), arbitrary server-to-client JS invocation
(eval-shaped), offline call queues (tiny audience, breaks across
deploys), dirty-input tracking (buildable in userland from the lifecycle
events), and staged multi-request uploads. Staged uploads are Livewire's
pattern: JS pre-uploads the file to a temporary endpoint or an S3
presigned URL, then the action references the stored stub. The pattern
exists for upload progress bars, validation before submit,
direct-to-storage offload, and keeping files out of re-render cycles.
The planned v1.x design is single-request multipart, which covers the
form-submit case; staged uploads return to the table only if direct-to-storage
demand shows.

---

## 11. Cross-language conformance

The protocol package (4.1) is the source of truth. Conformance is how a
binding proves it implements the protocol, and it is checked by replay:
fed each test case's call envelope, the binding must produce that case's
result envelope. The two envelopes must match exactly, except at the
paths its `dynamic_fields` declares (4.1). On top of the replay,
everything the binding emits must validate against the schemas. Python
runs the examples through `EventsDispatcher` in pytest; the client
replays result examples through `Citry.events.applyActions` in a DOM
harness, plus one Playwright e2e driving a real round trip (the
`test_fragment_e2e.py` pattern). Nothing in the suite is Python-shaped:
the examples are JSON, the conformance component is Citry syntax, and
dynamic values are declared as JSON paths. When JS/PHP/Go server
bindings arrive they import the same `tests/` directory.

Rust involvement in v1: none. The render walk stays in Python (settled
performance decision), and no grammar, AST, compiler, `LangImpl`, or PyO3
surface changes, so CLAUDE.md Mechanisms 2 and 4 are not triggered. Two
candidates could ever justify grammar work: a grammar-level binding syntax
(only if the template-load rewrite proves insufficient) and the Alpine
scoped-slot mechanic; each is decided when its milestone is built, per the
roadmap's rule, and nothing in v1 depends on either.

---

## 12. Substrate changes required (core, before the extension)

Each is small, independently shippable, and useful beyond Events. The first
two are hard prerequisites (a POST body is unreachable through the ASGI
adapter today).

1. **A framework-neutral `RouteRequest`** (`citry/util/routing.py`):
   `method`, `path`, `query`, case-insensitive `headers`, `body: bytes`,
   `content_type`, and `native` (the host object). Adapters construct it:
   ASGI drains `receive` for bodied methods, WSGI reads `wsgi.input` per
   `CONTENT_LENGTH`, Django wraps `HttpRequest`. Existing handlers never
   read `request` (documented in the module), so this is a contract
   tightening, pre-1.0, with a CHANGELOG entry.
2. **ASGI async support**: await `async def` handlers; run sync handlers in
   a worker thread instead of blocking the event loop.
3. **`RouteResponse.headers: tuple[tuple[str, str], ...] = ()`**, forwarded
   by all adapters (needed for downloads and cache headers; Django's
   response object holds one value per header name, so a repeated name is
   a pointed error under that adapter rather than silent loss).
4. **Three `CitrySettings` fields**: `secret: str | list[str] | None`
   (the canonical signing-secret home, plus a
   `citry.contrib.django.secret()` convenience),
   `event_result_resolvers`, and `event_payload_codecs` (the engine-wide
   registries, 6.2). Settings grow
   field-by-field as subsystems land, per the settings-schema design;
   these are the Events fields. Because Events ships as a built-in
   extension, its object-carrying config must live where users already
   pass objects at construction, not on an extension they never
   instantiate.
5. **Two client-runtime extension points in `citry.js`** (owned by the dependencies
   extension, coordinated, not forked): `Citry.manager.decorateContext(fn)`
   (about ten lines; any extension can enrich the `$component` payload)
   and cleanup-function returns from callbacks (teardown, 5.2). The
   decorator contract, pinned here so implementation does not invent it:
   `fn(ctx)` receives the payload object at flush time, just before the
   callbacks run, and mutates it in place, adding members (the return
   value is ignored, so no replace variant exists to reason about);
   decorators run in registration order; a throwing decorator is caught
   and logged like a callback error and the flush continues;
   `decorateContext` returns an unregister function.
6. **The `citry/extensions/` to `citry/ext/` rename** (mechanical,
   pre-1.0, SQLAlchemy precedent) together with regularizing the public
   `__init__.py` files of `ext` and `contrib` to pure re-export
   surfaces per the API rule (3.4).
7. **(v2 only)** `WSRoute` plus an `asgi_ws_app` adapter for the WebSocket
   transport.

The `State` dataclass conversion and the `state_data` component method are
deliberately **not** core changes: the extension applies the dataclass
treatment itself in `on_component_class_created` and reads `state_data`
by name, so the core stays unaware of extension-owned surfaces.

---

## 13. Delivery plan

**v0, substrate**: items 1 to 6 above, each its own PR with contrib
tests (item 6, the `ext/` rename, is mechanical but everything v1
imports depends on it).
Exit: a POST handler under FastAPI, Flask, and Django can read a JSON body
and set a response header.

**v1.0, the extension (HTTP)**, in order:

1. **Protocol package first**: spec, schemas, and protocol tests merged before server
   code.
2. **The morph spike** (gate for all client work): a re-rendered fragment
   with a pinned instance id morphs over the live DOM; `$component`
   re-fires exactly once, after teardown, with the new `js_data` payload;
   new CSS variables take effect on the morphed roots; assets dedupe; a
   focused two-way-bound control keeps value and caret through a
   debounced update cycle; a `state` action updates the registry without
   any DOM change; the instance's Alpine scope survives the morph
   with `$state` object identity intact and the reconcile rule applied
   (5.5); and a multi-root (fragment) instance updates through the
   pairwise per-root morph, falling back to range replacement when the
   root count changes. Failure here redesigns the client model before
   server work hardens.
3. Server: handler enumeration, State capture (`state_data`) and dataclass
   conversion, `data`-schema validation and coercion, signed tokens and the
   token-refresh rule, the opt-in server-side state store
   (`_storage = "server"`, the livecomponents migration's step one),
   dispatcher plus HTTP routes and codecs (JSON,
   urlencoded, GET query), the compatibility/no-JS mode, `_context`,
   guards and CSRF wiring, the action constructors and return coercions,
   emit hooks, `events.url()`, the `ViewEvents` shim, the OpenAPI command.
   Exit: the counter works via curl under FastAPI and Django; protocol tests
   green.
4. Client: `citry-events.js` (embedded pinned Alpine plus
   `@alpinejs/morph`; scope attach with isolation at manifest time; the
   magics of 5.5 including writable `$state` with the queue and
   reconcile rules; the `@c-*`/`:c-*` rewrite with hard template-load
   validation, Alpine-expression args, one- and two-way bindings riding
   the Alpine scope, form-fields-into-data collection, `@c-poll`;
   per-trigger
   `data-citry-busy`), fetch transport with CSRF
   autowiring, the event queue (5.6), epoch handling, morph with keyed
   linking and the explicit preservation rules (5.3, 5.5),
   `sendEvent`/`onEvent`, bootstrap stub, DOM CustomEvents. Exit: the three
   pitch examples pass e2e under WSGI and ASGI at (or under) the line
   counts shown in section 2, and the e2e suite includes one element
   carrying several event bindings for different DOM events.
5. Docs: user guide, the security page (visibility, CSRF, guards), and
   migration guides with the parity matrix; ports of the old
   form-submission and fragments examples plus a unicorn-style search as
   e2e tests.

**v1.x, fast follows in value order**: multipart uploads; the postMessage
transport and bridge (unblocks Events-backed Storybook previews that cannot
use a same-origin route or proxy); served
`openapi.json`; Django `form_class` sugar; optional token encryption;
node-level binding rewrite replacing the textual one
if the textual pass proves insufficient.

**The acceptance dogfood, once v1 lands**: fork the production
application audited in 1.4 and rewrite its interactive components in
citry Events with the Alpine runtime. It is the ready-made corpus for
falsifiers 15.2, 15.3, and 15.8 and for the post-v1 half of 15.11
(head-of-line blocking, the queue's dogfood check): 36 real
components, known behavior to reproduce, known pain points that must
disappear. The port doubles as the migration guide's worked example.

**v2, each its own decision point**: WebSocket transport and server push
(signed topics, `push()`); client-side same-tick batching; SSE evaluated
against WS. Alpine scoped-slot ownership is no longer a v2 Events milestone:
the graph-first client runtime landed source-owned supplied fills and
receiver-owned fallback content in Alpine plan A7.

---

## 14. Contested decisions and their resolutions

### 14.1 Maintainer-review revisions

Decisions from the synthesized draft that were reversed or reshaped in
maintainer review, recorded with the reasons because the earlier
design-panel decisions argued the other way:

1. **State is a separate, explicit contract (`class State:`), never
   derived from kwargs.** The draft used the component's kwargs as the
   round-trip state, which read beautifully for leaf components and broke
   down structurally for real ones: it forced interactive components to
   have JSON-only inputs and no slot fills, pushing all interactivity to
   leaf nodes. The separate State decouples the two: kwargs and slots can
   hold anything (they never travel), any component can carry handlers,
   and, decisively, the JSON-only State makes it **visibly true in the
   code** that the original inputs are gone at event time; a handler
   cannot wonder whether "the state" still includes slots, because the
   State class in front of them answers it. Re-rendering is therefore
   always an explicit act of building a new component tree. An implicit
   "State defaults to Kwargs" variant was considered and rejected:
   explicit beats implicit, and one model is easier to hold than a
   conditional one. `class State(Kwargs): pass` is the explicit leaf-case
   spelling. The production audit then confirmed the call empirically:
   only 5 of 36 real components have a trivially kwargs-shaped State; the
   norm is a few ids derived from richer kwargs (1.4).
2. **The binding vocabulary is `@c-*`, owned by citry outright.** The
   draft used bare `@click` with a recognition rule (a binding counts only
   if it parses and names a declared handler) to coexist with Alpine. The
   rule was the draft's most fragile part: it made validation soft and put
   citry in the business of guessing intent. `@c-*` removes the ambiguity
   by construction: citry owns the prefix, every binding error is a hard
   template-load error, plain `@click` passes through untouched for Alpine
   or in-DOM Vue, and the authored syntax is rewritten away at template
   load so no nonstandard attribute reaches the browser. Verified safe:
   `@c-*` names start with `@`, so they never touch the `c-*` expression
   channel.
3. **One return channel; action constructors, not an effects collector.**
   An earlier draft split responses between return values and a mutating
   `self.fx` accumulator, two ways to say one thing. Resolved to the
   return channel only: a handler returns its actions (or values that
   coerce to them), which keeps handlers pure functions of (state, args),
   trivially testable, with the whole response visible at the return site,
   and keeps `return` annotations meaningful for OpenAPI. The constructors
   hang off `self.actions` so nothing needs importing, and they are
   **capitalized** (`Render`, `Data`, `Dispatch`, `Redirect`) because in
   Python a capitalized call reads as constructing a value, which is
   exactly the signal needed: these build data to return, they do nothing
   when called. The name `actions` replaced the draft's `fx`, which failed
   the first-time-reader test, and the wire vocabulary uses the same word
   end to end. Coercions are strict: dict means `Data`, element means
   `Render`, list means ordered actions, `None` means acknowledged, and
   everything else (strings especially, which are ambiguously HTML-or-
   JSON) is a pointed error rather than a guess; result resolvers extend
   the table for user types. The known cost, accepted: a constructed
   action that is not returned does nothing (debug mode warns about
   constructed-but-unreturned actions).
4. **No built-in events, and no send-by-itself bind mode.** The draft
   shipped `$set` / `$refresh` built-ins and a `@c-bind.live` mode that
   invoked them. The audit showed production handlers already decide and
   perform their own rendering, so the built-ins privileged a self-
   re-render path the design philosophy had already rejected. Dropping
   them means: every event named in a template is a handler the author
   wrote (validation has zero special cases), the rebuild recipe
   (`State.render`) demotes from API to a recommended convention, and
   components that want refresh events define them in one to three
   lines. (The binding side of this entry was subsequently redesigned
   wholesale; entry 9 supersedes it there.)
5. **`_context` replaces the draft's globals hook.** The draft carried an
   `Events.globals` hook framed as recomputing template globals for
   event-time renders; that conflated two things (template globals apply
   to event-time renders like any render, and handlers do not necessarily
   render). What handlers actually need is per-call request-derived
   context, so the GraphQL-server pattern is adopted: one `_context`
   function, usually configured globally via `extensions_defaults`,
   producing `self.context` for every handler and guard. The underscore
   prefix keeps the public-def-means-handler rule exception-free.
6. **`state_data` lives on the Component; State methods are conventions.**
   Placing capture on the Events class was inconsistent with the
   `template_data` / `js_data` / `css_data` family and smudged the
   handler/non-handler line; placing it on State would need a classmethod
   contortion (the state does not exist yet at capture time). On the
   Component it sits where users think about data flow.
7. **Component dispatch lives under `ext/events/e/`.** The flat
   `ext/events/{class_id}/{event}` relied on literals-first route ordering
   to keep `call` and `runtime.js` reachable; the extra segment makes the
   namespace structurally safe, so the extension can add root-level
   endpoints forever without colliding with component addressing.
8. **Events is a built-in extension; engine-wide registries move to
   `CitrySettings`.** Interactivity is core to the product, so Events
   ships like `dependencies`: prepended to every instance, nothing to
   register, and the setup example is just the mount. Since users never
   instantiate the extension, its config splits along one line:
   component-overridable config rides `extensions_defaults["events"]` and
   the nested class (guard, `_context`), joined by the envelope size cap
   as an engine-wide-only entry (it guards the transport before any
   component resolves, so it has no per-component override), while
   engine-wide
   registries and secrets become settings fields (`secret`,
   `event_result_resolvers`, `event_payload_codecs`). An alternative was
   considered and
   rejected: letting a user-supplied `EventsExtension` instance in
   `extensions=[...]` override the built-in, which would allow
   constructor-style config but reintroduces exactly the mutable-
   extension-set ambiguity the substrate forbids (extensions are a frozen
   tuple with reserved built-in names). The settings-field naming went
   through two rounds: a first pass chose short names for brevity, and
   the section 6 maintainer review reversed that. Final names:
   `event_result_resolvers` and `event_payload_codecs`, verbose on
   purpose (the two-word forms did not say what they do), and "resolver"
   over "encoder" because these translate Python values to action
   objects while "encoder" connotes string formats.

9. **State bindings get their own channel: `:c-*`.** The draft spelled
   the binding `@c-bind="query"`, which failed three ways at once: it
   looked exactly like an event binding while meaning something entirely
   different, `@c-` had been established as the event prefix, and the
   name collided with the shipped `c-bind` attribute spread
   ([`template_html_attrs.md`](template_html_attrs.md)). (Process note: every draft
   inherited the unicorn/Livewire "model binding" frame, binding as a
   member of the event family, and the adversarial review scrutinized
   the event prefix without re-deriving the binding taxonomy against
   citry's own attribute channels; the maintainer caught it on read.)
   The redesign: `:c-<key>` shorthand only (no longhand; `:c-field` is
   the reserved candidate if one ever proves needed); a value makes it
   two-way and names the flush handler (trigger semantics: one call
   carries the update and the event, so the handler sees fresh state and
   the "pending updates ride with the next call, whatever it is"
   implicitness is gone, demoted to race protection for calls that beat
   a debounce timer); `.on:<event>` as the general trigger override,
   with `.lazy` as table-backed sugar, which also makes the per-control
   default table closed (unknown controls require `.on:`). Forms dropped
   out of binding entirely: submit-triggered events collect form fields
   as typed named args, mirroring the no-JS codec, so the batch-update
   mode ceased to exist. The writable allowlist moved off Events onto
   State as underscore meta (`_public` / `_model`, 7.2): it is state
   policy, not handler policy, and Events holds handlers.

10. **AlpineJS is the Events runtime.** Decided after the dedicated
    research round ([`alpinejs/`](alpinejs/)): the client runtime embeds
    a pinned, vendored Alpine 3.15.x (the Livewire playbook: compile it
    in, boot it ourselves, warn on a second instance) rather than
    shipping a dependency-free runtime. The positioning argument
    decided it: being the Livewire equivalent for Python is worth more
    than a zero-third-party-dependencies claim. Supporting facts:
    upstream is healthy and stable (monthly 3.15.x patches, the x-for
    performance rewrite landed in 3.15.9, no Alpine 4 on the horizon);
    the community TS fork is unlicensed, unpublished, and dormant; the
    maintainer's own packages prove the model in production (all named
    components in the audited app run on alpine-composition) and
    contribute the scope-isolation mechanism, which is safe to use
    precisely because the embedded Alpine version is pinned. The
    declarative pending/error/server-event surfaces resolve inside this
    direction as read-only magics; `:c-*` bindings ride Alpine's
    reactive scope; the integration design is section 5.5. Bindings contributed through render-time
    attribute spreads are handled by a second rewrite stage in
    `on_attrs_resolved` (5.1), chosen over rejecting them because the
    audited codebase shows the spread pattern is how component libraries
    actually compose attributes.

11. **The handler signature: a fixed name vocabulary with a single-input
    schema.** Decided after the typing and binding research
    ([`events_research/typing-lab-report.md`](events_research/typing-lab-report.md),
    [`events_research/binding-models-report.md`](events_research/binding-models-report.md)).
    User data arrives as one `data` schema object rather than spread
    arguments: deliberately more verbose (a schema class per action) in
    exchange for reusable, importable input contracts, and it makes
    every parameter's role knowable without the keyword-only zone an
    earlier draft of this round proposed (the zone existed only to fence
    an open set of data params from injectables; a single slot needs no
    fence). Injection is by fixed name (`data`, `state`, `context`,
    `request`, `event`), safe where Litestar's name-based inference
    famously failed because user data never shares the parameter
    namespace; annotations on injectables are advisory, never resolved
    at runtime, which sidesteps the nested-class annotation scoping
    rules entirely. The typing lab set the documented styles: root-level
    State classes assigned onto the component are green on both checkers
    with zero ceremony; bare nested-class annotations are dead
    everywhere; the generic base `citry.Events[State]` works (bare
    sibling names resolve in base lists) but is demoted to a niche
    opt-in since the signature carries the types. Action constructors
    are imported (`from citry.ext.events import actions`),
    superseding 14.1.3's no-import rationale: once the signature is the
    surface, one explicit import beats an untyped `self` namespace, and
    per-call values left `self` entirely as the documented style
    (ambient attributes remain for guards, `_context`, and resolvers).

12. **The actions round: faithful order, CSS-default targets, timing
    fields, and the public-API rule.** Grounded in
    [`events_research/actions-semantics-report.md`](events_research/actions-semantics-report.md).
    Action order is replayed exactly as returned, never reordered or
    server-filtered: the surveyed frameworks suppress renders and
    reorder around redirects because their transports cannot preserve
    order, ours can, and explicit-and-deterministic wins; the caveats
    became debug warnings plus documentation instead. The maintainer
    added the timing fields (`delay` in seconds, `wait` for
    non-blocking) so redirect-after-toast is expressible without
    reordering. Targets: plain CSS selector by default applying to all
    matches (the unanimous field answer), `render:` kept as the explicit
    instance override. Server-dispatched events fire under their exact
    names (Livewire and htmx precedent), `citry:*` reserved,
    component-name prefixes documented as the convention. `PushUrl` /
    `ReplaceUrl` ship as siblings (htmx's pair; the boolean-flag
    alternative is a default-disagreement trap). `Download` is sugar
    over the raw-response escape, never a base64 tunnel. The public-API
    rule: root exports plus each ext/contrib root are public; deeper
    modules private by convention; public `__init__.py` files are pure
    re-export surfaces with `__all__` and no logic; griffe is pointed
    at exactly these entrypoints, and the complete public surface is
    three entrypoint shapes: `citry`, `citry.contrib.<name>`, and
    `citry.ext.<name>` (an earlier draft of this round added a
    `citry.events` alias for built-ins; dropped, one path per thing);
    the extensions directory renames to `citry/ext/`.

13. **Binding args are Alpine expressions.** The pre-Alpine draft
    carried a citry-owned literal parser (JSON literals plus `$value` /
    `$event.<path>` specials) and a parallel per-item attribute channel;
    with Alpine as the runtime both are one mechanism too many. A
    binding's parenthesized part is now an ordinary Alpine expression,
    JS-shaped (`rate({stars: 5})`, not Python-shaped `rate(stars=5)`),
    evaluated at event time bound to the owning element with full scope
    access, and per-item loop data rides plain `c-*` data attributes
    read back via `$el.dataset`. The honest cost, recorded: the
    "compiled bindings evaluate no author code" claim narrows to
    argless bindings (arg expressions are author code handed to
    Alpine's evaluator), load-time validation covers the handler name
    while expressions are runtime-checked, and the section 16 CSP
    constrained mode shrinks accordingly.

14. **The fills guard is removed: a re-render is authoritative, not an
    error.** An earlier revision made a `render` action targeting an
    instance whose original render received slot fills a pointed
    server-side error, carried by a fills flag in the signed token. The
    section 7 maintainer review removed both: the handler's return is a
    new component tree by contract (the same contract that lets a
    handler return a different component class), so rendering without
    fills, or with different fills, is legitimate output, not silently
    dropped content. The error path is the ordinary one, a required
    slot missing fails the render loudly regardless of what triggered
    it, and the optional-slots case (a reusable component's
    self-re-render lacking call-site fill content) is a documented
    library-author note with the wrap-in-a-child pattern, not
    machinery. The token's fills flag went with the guard.


### 14.2 Decided during the design panel

Each was verified against source or the prior-art record during the
adversarial judging:

1. **Opaque state token.** A structured wire-visible envelope (client
   parses `{v, c, p, t, sig}`) drags the token format into the
   cross-language contract and invites JSON re-serialization signature
   failures; the token is an opaque string echoed verbatim.
2. **URL is authoritative; class ids, not registered names.** Routing by
   body fields under a per-event URL lets a body bypass per-action host
   middleware and rate limits; and registered-name addressing adds a hidden
   registration requirement (class ids always exist). Batch calls go to the
   explicit batch endpoint.
3. **CSRF defaults to the host token.** A custom-header-only default under
   Django means a bare POST is rejected by Django's own middleware or the
   route gets exempted; both are wrong for the most important migration
   host.
4. **Morph ships in v1.** A `replace`-only v1 loses focus on every live
   search keystroke, which loses the exact audience this extension exists
   to win. If the spike or the schedule falsifies the client scope, morph
   (not the binding vocabulary) slips one minor version behind the
   `capabilities`
   gate.
5. **No new `$`-source rewrites.** The rewrite mechanism cannot bind
   instances and has known substring sharp edges; the capability ships as
   `$component` payload members.
6. **State delivery via the inert events manifest tag**, not a valued
   root-element attribute: the manifest reuses the shipped dependencies
   pattern with zero core serialization change.
7. **Named wire args only.** A positional `args` list is a Python calling
   convention leaked into a language-neutral protocol; client sugar like
   `rate({stars: 5})` encodes named.

Alternatives rejected wholesale, with the one-line reason: HTTP-verb
handlers (the charter's recorded failure mode, quantified in 1.4);
reactive public-attribute mirroring (the CVE family lives there, section
7.6); WebSocket-first (forces ASGI and connection state on every deploy
against the ecosystem trend); delegating the client half to htmx (the
five-library client stack is the counterexample; interop is preserved via
the compatibility mode instead); a single opaque RPC endpoint only (host
middleware, logs, rate limits, and OpenAPI all want real URLs); optimistic
rollback machinery (wrong 10 percent of the time is worse than an honest
busy state); storing raw template source to re-render (citry renders from
component entry points, never from captured text); expression strings in
bindings (unauditable, and they mix render-time and event-time contexts
in one syntax); an open custom-action vocabulary (the `event` action plus
component JS covers the need; Tetra's open channel is the cautionary
tale).

### 14.3 The client-model round (2026-07-15)

Decided by the maintainer against the three decision-input documents
and the keyed-morph spike in [`events_research/`](events_research/),
which carry the full option matrices and scenario walkthroughs;
recorded here with the alternatives and why they lost.

1. **A `#c-*` meta-attribute channel joins the attribute language.**
   The channel test that settled the vocabulary (14.1.9 and the 16.2
   record) settled this too: `@c-` names browser events, `:c-` names
   State fields, bare `c-` names render-time data, and node identity
   and morph behavior are none of those, so they get their own prefix
   rather than overloading one. `#c-*` is reserved for keying and
   morphing features only, never event call-site configuration. First
   members: `#c-key` (expression-valued, server-evaluated) and
   `#c-ignore` (bare subtree marker); the per-attribute preservation
   tier is a recorded v2 expectation (16.1). Alternatives rejected:
   reserving the plain `key` attribute or a `key` kwarg (steals
   ordinary names; `key` already has HTML rendering semantics and any
   component may legitimately want a `key` input), and a `c-bind`
   escape hatch (nothing needs escaping once the channel exists). The
   channel is real parser work (grammar, AST, compiler, the five
   `LangImpl` surfaces, PyO3, the `.pyi` stub), planned as WP21 with
   the client wave depending on it (`events_plan.md`).
2. **Nested anchor continuity: reset baseline plus keyed linking
   (options A plus C), with the horizon cut.** Every uncorrelated
   instance id follows reset: fresh ids mint fresh anchors, departed
   anchors retire; `#c-key` is the only linking mechanism,
   author-asserted identity exactly where Livewire's `wire:key`,
   LiveView's `:id`, and React's keys all converged. Option B
   (positional matching) rejected as a default: a guessed link can
   send one entity's unsent draft into another entity's State, and
   misattribution is the only outcome on the board worse than loss
   (React's decade of unkeyed-list state bleed, with the stakes raised
   because citry's pending writes reach the server). Option D
   (Livewire-style islands) rejected: it reverses the landed server
   model (a parent's render carries its children, 5.3) and
   reintroduces the stale-props disease that model exists to avoid.
   The horizon cut (drop a linked child's in-flight instance-mutating
   actions at link time) chosen over last-writer-wins: a late
   pre-parent render would resurrect a replaced child's state; both
   are client-internal, so the choice is revisitable on dogfood
   evidence. Key emission pinned by the keyed-morph spike's verdict:
   one composite data attribute in the class-id-scoped form (morph key
   matching proved sibling-window scoped, F-KM-1), with the
   id-to-anchor normalized form proven feasible and recorded as the
   fallback (F-KM-6). Inputs:
   [`events_research/analysis-nested-anchor-continuity.md`](events_research/analysis-nested-anchor-continuity.md),
   [`alpinejs/spike-keyed-morph.md`](alpinejs/spike-keyed-morph.md).
3. **Targeted renders: remove-and-replace (option A).** A render
   addressed to anything but the caller retires the region's anchors
   and mints fresh ones; continuity belongs to correlated self-renders
   and keyed matches alone (5.5). Option B (widening the epoch drop
   rule to every render action of a stale response) rejected as
   unnecessary once the queue exists: same-caller repeat-fire
   serializes client-side, so the stale overwrite the widening
   targeted cannot occur for queued sends, and the residual
   `wait: false` ordering is a documented author trade (5.5). The 4.2
   drop set therefore stays narrow (instance-mutating actions only),
   and 5.2's drop-event row was aligned to it. Option C
   (adopt-in-place against the target's anchor) rejected: two rules
   where A has one, degenerate under multi-match targets, and it is
   the v2 anchor-update question (server push, 16.1) arriving early
   for the rarest consumer. Option D (server-declared region identity)
   rejected: a wire change for a race the surveyed field leaves
   unguarded at apply time by default. Races to one target from
   unrelated anchors
   are userland (render truth, not deltas; dispatch-and-refresh
   for contested regions), with helper utilities a possible later
   addition (16.1); multi-target inserts are one shared instance
   mirrored per match (5.5). Input:
   [`events_research/analysis-target-other-renders.md`](events_research/analysis-target-other-renders.md).
4. **The event queue (5.6), superseding the research's drop-only
   recommendation.** The concurrency research (R2) recommended
   drop-plus-surface alone for the parent-child overlap (with
   same-anchor overlap serialized per anchor with merge), on the
   ground that no surveyed
   framework derives a serialization scope from a component tree.
   Overridden: the tree-scoped race is a citry-specific consequence of
   fresh ids plus whole-subtree re-renders, the field's convergent
   shape wherever serialization exists is "serialize within one
   identity unit, siblings parallel, nothing dropped", and the
   maintainers of the largest queue-owning system state serialization
   as the only safe default for UI-affecting state (Livewire's
   `#[Async]` warning). Drop-plus-surface is recorded as the
   fallback, split by evidence window in falsifier 15.11: applier
   evidence in the WP16.3 harness would put it in v1, dogfood evidence
   in a v1.x.
   Newest-wins abort rejected as a default (a killed save is data loss
   from the user's viewpoint; Unpoly's documented sharp edge); the
   per-handler `@event` knobs carry the variance instead (3.5):
   `latest_wins` as the opt-in, `bundle=False` as the opt-out from
   default-on bundling.
   **Amended 2026-07-17: the queue is an explicit dependency DAG in
   v1**, superseding the containment-chain framing this decision was
   first drafted in. Chains model overlapping scopes awkwardly: a
   second event dispatched from an anchor inside an in-flight event's
   scope would need a second stored chain, where the DAG expresses
   the relation as one dependency edge; and the DAG's roots-first
   structure (dispatch whatever holds no unsettled edges) is the
   natural organization for the same semantics. The observable rules
   are those of the original decision: overlapping events apply in
   enqueue order, independent events run in parallel (5.6, the
   normative statement). Send-versus-apply
   pipelining stays a recorded v2 candidate (16.1). Input:
   [`events_research/research-rerender-preservation-and-concurrency.md`](events_research/research-rerender-preservation-and-concurrency.md).
5. **Preservation: server wins by default, deviations explicit, focus
   is not a signal.** R1's mechanism stack ratified as one unit (keys,
   the subtree marker, the updates piggyback as the lifted-input-state
   story, busy plus `$loading` as disable-while-loading), with the
   focused-element rule reframed out of silent-default status:
   protection derives from a pending unsent write, never from focus,
   the construction that sits between the two recorded field failures
   (morphdom 135, no protection; Turbo 1194, blanket protection
   fighting a legitimate clear). The rule and its acceptance tests are
   5.5's preservation block.
6. **Surfacing: R3 ratified in full.** Every drop fires the one drop
   event with a `reason` field (5.2); every promise settles; the toast
   pattern stays two-tier (per-call rejection, global
   `citry:events:error`). citry never cancels server work: the drop,
   where one exists, is of client application only, and every call
   settles on the client in R3's terms, a resolution, a structured
   rejection, or a drop that still resolves its `data` (the settle
   table, 5.2). Choosing between viable calls is never a default:
   newest-wins abort is rejected, and supersession exists solely as
   the `@event(latest_wins=True)` opt-in (3.5). The two default ways a
   call ends early are not such choices: the dequeue-time cancel of a
   call whose dispatching element died (never sent, 5.6) and the
   bounded timeout (the client stops waiting; the server still runs,
   5.6).

---

## 15. Falsifiability

Concrete outcomes that would prove this design wrong, checkable early:

1. **The morph spike fails** (13.2): the manifest/runtime machinery double
   fires callbacks, loses focus, re-executes assets, or delivers stale
   JS/CSS variables. Consequence: the client model is redesigned before v1
   server work hardens.
2. **The pitch line counts fail**: the counter, search, or form examples
   need hidden glue (a route registration, a JS import, manual state
   plumbing) beyond section 2. Consequence: the DX thesis is unmet; do not
   ship as-is.
3. **The State model, tested against production (largely settled).** The
   2026-07-04 audit of 36 real interactive components (1.4) answered the
   two original concerns: real state is 150 to 300 bytes signed (nowhere
   near the size caps), and explicit State is not boilerplate (only 5 of 36
   would be trivial kwargs mirrors; the id-derivation mapping is what the
   code already does by hand). What remains open for citry dogfooding: if
   the first real citry apps diverge from this profile (median token over
   ~2 KB, or any component hitting the 8 KB canary), the signed-token
   model needs the server store promoted into core; and if explicit
   rendering proves noisy in practice (every handler ending in the same
   `return state.render()` line), reconsider sugar, not the model.
4. **Adapter parity breaks**: the e2e suite behaves differently under
   Django/WSGI vs FastAPI/ASGI in user-visible ways. Consequence: the
   neutral `RouteRequest` abstraction is wrong; per-host handler wrappers
   are a different architecture.
5. **The Django CSRF story fails review**: the integration cannot pass a
   security review without a `csrf_exempt`, or any input path reaches a
   handler without signature and schema validation. Consequence: the
   layered CSRF/exposure design is falsified.
6. **The transport abstraction is fake**: implementing WS or postMessage
   requires changing the dispatcher signature or any envelope field.
   Consequence: redesign the `TransportContext` boundary before v2.
7. **Per-event URLs deliver no value**: Django users cannot in practice
   attach per-route policy through the citry include, and logs plus
   OpenAPI alone do not justify the path surface. Consequence: collapse to
   the batch endpoint as primary in the next protocol minor (the envelope
   already carries per-call addressing).
8. **The migration pitch does not convert**: porting one real example each
   from unicorn, Tetra, and livecomponents produces longer code or needs
   custom JS for behavior the original had declaratively. Consequence: the
   vocabulary is missing an attribute; fix that, not the marketing.
9. **The textual `@c-*`/`:c-*` rewrite misfires on real templates** (`<c-raw>`
   blocks, binding-shaped text in attribute values). Consequence: the
   node-level transform in `on_template_compiled` moves from v1.x into v1.
10. **Protocol neutrality fails**: the first non-Python binding cannot
    implement the protocol from the protocol examples without consulting Python
    semantics. Consequence: strip the offending fields into
    binding-private extensions and re-cut the schemas.
11. **The dependency-DAG queue proves unworkable** (5.6), with two
    evidence
    windows and a consequence per window. Before v1, in the WP16.3
    harness: settled-means-applied proves undeliverable in the
    applier. Consequence: v1 ships the recorded fallback of 5.6
    (drop-plus-surface for the parent-child overlap, same-anchor
    sends still serialized per anchor, per the concurrency
    research's R2) behind the
    same drop event, and the queue returns as a v2 design. After v1,
    in the dogfood port (section 13): head-of-line blocking that
    `latest_wins`, `bundle=False`, and `wait: false` cannot relieve.
    Consequence: a v1.x release ships the same fallback and the queue
    is redesigned for v2; the drop event and the settled promises
    hold under both rules, so the swap narrows behavior without
    breaking the surfacing contract.
12. **`#c-key` emission cannot stay inside WP21's
    compiler-to-serializer path**: forwarding a component-tag key onto
    the child's root markers turns out to demand a core serialization
    redesign. Consequence: re-price keyed linking against the recorded
    id-to-anchor normalized form (the keyed-morph spike's F-KM-6)
    before the client wave hardens. Here the fallback does a
    different job than the one the spike priced: it removes the
    stamping path entirely. The child's roots already carry the
    per-render component id (`data-cid-*`), the authored key rides
    the child's events-manifest entry instead of a stamped attribute,
    and a per-call key callback maps both sides through the
    component-id-to-anchor index. The spike proved the callback
    feasible (and hot, F-KM-8) but never priced the manifest
    carriage; the re-pricing weighs both against the serialization
    redesign.

---

## 16. Open questions and resolved records

Two registers share this section, labeled so a reader knows what still
needs an answer: 16.1 holds the questions genuinely open, and 16.2 holds
questions raised during design that are now resolved, kept here because
their critique records shaped the design.

### 16.1 Open (tracked, non-blocking)

- **A packaged GraphQL transport, and the transport candidate list.**
  The dispatcher boundary makes a GraphQL integration nearly free
  server-side: a mutation resolver decodes the envelope, calls
  `dispatch`, and returns the result envelope (about ten lines, 6.1).
  The open work is the packaged story: a documented contrib recipe or a
  `citry.contrib` shim for the dominant Python GraphQL libraries, plus
  a registered client transport that sends the envelope through the
  page's existing GraphQL client. The value is positioning as much as
  plumbing: a team already running GraphQL connects the citry endpoints
  to the stack it trusts and gets a Livewire/Vue-like frontend with no
  new infrastructure. Utility needs validation with real users before
  anything is built; open a feature issue once events ship. Other
  transport candidates, considered, with their status: WebSocket (v2,
  6.3), SSE (evaluated against WS at v2, section 8), postMessage (v1.x,
  the cross-origin or sandboxed Storybook route, 6.4), and in-process
  (already free: the dispatcher API itself is the transport that tests and
  conformance use).
  Nothing else earns a seat yet.
- **A `$forwardEvent(name, handler)` listen-and-forward magic.** Kept out
  of v1 on the fewest-globals principle: it is the one-line
  composition `$onEvent(name, () => $sendEvent(handler))`, so nothing
  is blocked without it. Open a feature issue once v1 ships and let
  community demand decide.
- **Lazy scope activation**, only if the dogfood port (section 13) shows
  eager creation costing real startup time on dense pages. The
  reserve design is settled so the future implementer builds the
  right thing:
  - Deferring a citry scope defers Alpine's walk of the whole
    subtree, and user `x-for` / `x-if` content inside it does not
    exist until that walk runs (their `<template>` bodies are
    client-generated), so interaction cannot be the only trigger.
  - Activation trigger is a union, whichever fires first: viewport
    entry via one shared IntersectionObserver with a configurable
    margin (pre-activate components shortly before they scroll into
    view), first interaction or focus landing inside the subtree
    (keyboard navigation and find-in-page beat the observer), or any
    programmatic send or server event action targeting the instance.
  - Activation is top-down: triggering any deferred root activates
    its outermost deferred ancestor, whose `initTree` initializes the
    chain (surrounding content may reference the ancestor's scope).
    Scope isolation keeps the chain short: citry components never
    depend on ancestor component scopes, and user `x-data` outside
    deferred subtrees is initialized eagerly at start.
  - No template classification: the union trigger applies to every
    deferred component, rather than detecting content-generating
    directives per template (spreads and user JS can add Alpine
    behavior the classifier would miss).
- **Client-side component instantiation.** Props down, events up, managed
  lifecycle helpers, RootGroups, rootless ownership, slot-source projection,
  and atomic graph plus Events adoption are landed. Native `x-for`, `x-if`,
  and `x-teleport` still cannot clone a server-rendered client-active component:
  rewriting `data-cid-*` attributes cannot mint independent registry,
  lifecycle, State, timer, cap, and cleanup identity. A named client target or
  browser blueprint is a separate protocol decision; see
  [`alpinejs/a9_client_instantiation.md`](alpinejs/a9_client_instantiation.md).
- **A constrained CSP mode** pairing Alpine's CSP build with
  argless-compiled-bindings usage (5.5 records the trade; the standard
  build needs `unsafe-eval` like Livewire).
- **GET event caching**: `no-store` default now; `@event(cache=...)`
  recipes when the Cache extension lands.
- **Anchor creation versus update for server push and host-inserted
  fragments** (create designed, update open). Minting a fresh anchor for
  an uncorrelated component id is designed and covers the initial page
  load and a plain fragment insert. The update case, where a push
  replaces an existing region and wants to keep that region's anchor
  without a correlation id, is unresolved; it is v2 scope (server push,
  section 8), and it is where adopt-in-place for targeted renders
  (rejected for v1, 14.3.3) folds in, so the continuity upgrades get
  designed once, with push updates, targeted adopt-in-place, and any
  keying extensions as the consumers.
- **Send-versus-apply pipelining** (v2 candidate, recorded by 14.3.4;
  5.6's queue dispatches a dependent only after its predecessor's
  actions have applied). The shape, named so a future design starts
  from it: dispatch the next call while the previous result's actions
  are still applying. Recorded, not designed; the queue's observable
  semantics (5.6) are the compatibility bar.
- **A per-attribute preservation tier** (v2 expectation, recorded by
  14.3.1; `#c-ignore` is the v1 subtree tier, 5.3). Every long-lived
  morph framework grew one after its subtree marker (LiveView's
  `JS.ignore_attributes`, Turbo's `turbo:before-morph-attribute`,
  Datastar's `data-preserve-attr`), because browser-owned attributes
  like `open` on `<details>` keep getting stripped by faithful
  patches. Expected demand, deliberately unbuilt; the `"ignore-self"`
  marker value stays reserved alongside it (5.3).
- **Queue helpers for target ordering across unrelated anchors**
  (userland in v1,
  14.3.3). The v1 answer to two unrelated callers racing one target
  region is
  the documented patterns (render truth, not deltas;
  dispatch-and-refresh for contested regions, 5.5). If the dogfood
  shows those patterns repeated verbatim, a packaged helper (a
  target-scoped ordering utility) earns a design round.
- **A devtools root-element attribute**: whether the events instance
  data should additionally ride a root-element
  attribute for devtools debuggability (deferred to client profiling; the
  manifest tag is the contract either way). A related, still-open aid is
  surfacing the anchor (5.5) on its root as a re-stamped
  `data-canchor-<id>` attribute so it is visible in devtools; the
  component-identity spike confirms this attribute can be kept stable
  across every morph kind, but it would be a debugging aid layered on the
  in-memory index, never the tie itself.
- **Where the TypeScript home (`packages/js/citry-client`) starts**: with
  this runtime or with the JS-binding milestone (the runtime ships as
  plain JS package data either way, like the dependencies runtime today).
- **Deferred binding features**, to revisit once design and
  implementation settle:
  - Per-instance programmatic modifiers (e.g. a debounce value coming
    from kwargs). Today `@event(debounce=...)` covers the class level.
  - A user-registered per-control update-event table. Only if `.on:`
    proves repetitive in practice.
- **Whether the WebSocket transport must ship with v1** rather than v2.
  This
  doc recommends v2 (HTTP covers every adapter today, and the stateless
  dispatcher makes WS purely additive), but if first-release WS is a
  product requirement, the substrate item is `WSRoute` plus the ASGI
  WebSocket app and nothing about the protocol changes.

### 16.2 Resolved, kept for the record

- **The `$state` inert-fallback, confirmed against the real magics**
  (resolved when the WP15 client runtime landed). The runtime treats
  `$state` on a marker-bearing node whose id is momentarily
  unregistered mid-morph as an inert empty read rather than a throw
  (5.3, 5.5), and the boundary scope self-heals right before Alpine
  initializes a root whose manifest arrived early (a head-placed
  `<c-js />` exercises this); both are locked by the WP15 e2e suite.
- **The pending-state, error-display, and server-event surfaces resolved
  into the Alpine layer** (the drafts' `@c-loading`, `@c-error`,
  `@c-on:`; resolution in 5.5, decision in 14.1.10; the critique record
  below is kept because it drove the channel taxonomy). All three
  failed the channel test in maintainer review: they are not event
  handlers (`@c-` wrong; `@c-on:` additionally breaks the invariant that
  `@c-*` reacts to browser events, since it reacts to server events),
  not render-time data (`c-*` wrong), and not State fields (`:c-*`
  wrong); loading and error are runtime meta-state with no channel of
  their own. Further recorded critiques:
  - Granularity: loading was per-instance (all-or-nothing); real UIs
    (a settings page of independently saving toggles) need per-trigger
    control, and handler-name scoping is not enough when many controls
    share one handler.
  - Incompleteness: the meta-state was not reachable as data from JS
    (only as a CSS attribute and lifecycle DOM events).
  - Provenance: the vocabulary was inherited from unicorn's
    `unicorn:loading` family and Livewire's `wire:loading` and survived
    the prefix renames without ever being re-derived against citry's
    channel taxonomy, the same failure mode the binding redesign fixed
    (14.1.9).
  **Direction decided (14.1.10): AlpineJS is the Events runtime.** Each
  interactive instance gets an Alpine scope whose reactive data is the
  public State fields, with runtime meta exposed as read-only magics
  (`$loading`, `$error`) and the JS surface as magics too (`$sendEvent`,
  `$onEvent`).
  The research grounding lives in [`alpinejs/`](alpinejs/); the
  integration design is section 5.5, which settled the sub-designs:
  writable `$state` gated by `_model` with the queue and reconcile
  rules, bindings riding the Alpine scope, eager scope creation at
  manifest time, per-trigger `data-citry-busy` for pending UI, and
  error display as plain Alpine over `$error` (text-only by
  construction). The items that remained genuinely open from this round
  (`$forwardEvent`, lazy scope activation, the `$loaded` signal, and the CSP
  mode) live in 16.1. The landed client-boundary contract is normative in
  [`alpinejs.md`](alpinejs.md).
- **A `$loaded`-style readiness signal**: not ported (the manifest
  ordering, bootstrap queue, and lifecycle events cover its old job)
- **Anchor lifecycle for nested instances** (resolved 2026-07-15 in
  the client-model round; it stood here while the anchor model was
  proven only for a top-level instance re-rendering itself). The
  question: a citry instance rendered inside another instance's region
  gets a fresh child component id inside the parent's fragment with no
  correlation of its own, so nothing said which old child, if any, the
  fresh id continues. The resolution is the uncorrelated-id lifecycle
  (5.5): reset is the baseline for every uncorrelated id, `#c-key` is
  the one linking mechanism (with the horizon cut), and the five
  machinery requirements became normative scope for the client
  applier work package (WP16.1). The decision
  record with the rejected alternatives (positional matching, islands)
  is 14.3.2; the inputs were
  [`events_research/analysis-nested-anchor-continuity.md`](events_research/analysis-nested-anchor-continuity.md)
  and the keyed-morph spike.
- **A render addressed to a different element** (resolved 2026-07-15
  in the client-model round; it stood here as two open halves: which
  anchor's epoch guards a targeted render, and what happens to the
  target region's client state). The resolution is remove-and-replace
  (5.5): the target region's anchors retire, fresh manifest ids mint
  (or keyed matches link), no epoch ties the apply to the target's
  past, and same-caller ordering is answered by the event queue (5.6)
  rather than by widening the epoch guard. The decision record with
  the B, C, and D rejections is 14.3.3; the input was
  [`events_research/analysis-target-other-renders.md`](events_research/analysis-target-other-renders.md).
