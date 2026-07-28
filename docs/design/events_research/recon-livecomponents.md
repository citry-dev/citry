# Recon: livecomponents (om-proptech) for citry Component.Events design

Research date: 2026-07-04. Sources: the GitHub repo (https://github.com/om-proptech/livecomponents),
its docs site (https://om-proptech.github.io/livecomponents/), and the source files on `main`
(fetched at commit state of v1.20.0, 2026-04-30). Where a claim is load-bearing I cite the repo
file path or doc page; line numbers were not retrievable through the fetch tooling, so citations
are at file granularity.

## 0. What it is

"Django Live Components": a Django library for interactive server-rendered components, built as a
glue layer over three third-party pieces: django-components (component classes and template tags),
htmx (transport and DOM swapping), and Alpine.js with the morph plugin (client-side DOM diffing).
The docs index page itself calls the design a leaky abstraction: livecomponents is glue code
between htmx, Django, and django-components, and the developer is expected to touch the underlying
layers. MIT license, by OM PropTech GmbH (Germany). 23 stars, 4 forks, 227 commits, 32 releases.

## 1. Programming model

### Component classes

A live component is two classes (docs: `livecomponents/` "Livecomponent Anatomy" page; source:
`livecomponents/component.py`):

- A **state class** inheriting `LiveComponentsModel` (a Pydantic `BaseModel` subclass). Holds all
  mutable data the component needs to re-render itself. The docs are explicit: "The state must
  include parameters passed to the component as keyword arguments, so that the component gets all
  the necessary information to re-render itself." This is a manual contract, not enforced.
- A **component class** inheriting `LiveComponent[StateType]`, which extends
  `django_components.component.Component` via a custom metaclass. It must implement
  `init_state(context: InitStateContext) -> State` and may implement
  `update_state(context: UpdateStateContext)` (called in place when a parent re-render passes new
  kwargs) and `get_extra_context_data(extra_context_request: ExtraContextRequest[State]) -> dict`
  (computed template context derived from state).

`StatelessLiveComponent` is a subclass for display-only children: `get_state()` returns an empty
`StatelessModel()`, `set_state()` is a no-op, and it only calls `state_manager.ensure_session()`
so the session stays discoverable. Registration reuses django-components'
`@component.register("name")`.

A scaffolding command exists: `./manage.py createlivecomponent <app> <dir/name>` (with a
`--stateless` flag).

### Commands and CallContext

Commands are methods decorated with `@command` (the decorator just sets a marker attribute;
`livecomponents/component.py`, `livecomponents/decorators.py`). Signature pattern:

```python
@command
def increment(self, call_context: CallContext[RootState], value: int):
    call_context.state.value += value
```

`CallContext` (source: `livecomponents/manager/manager.py`, `livecomponents/types.py`) carries:
`request` (Django HttpRequest), `state` (the deserialized state instance), `state_address`
(session id + component id), `state_manager`, and `execution_results` (accumulator of what to
re-render). Mutating `call_context.state` is enough; the framework saves state and marks the
component dirty after the command returns. No return value needed for the default
"mutate and re-render me" path.

Cross-component calls: `call_context.find_one(component_id)` returns a CallContext repositioned at
another component; `call_context.parent` is shorthand for the immediate parent;
`call_context.find_ancestor(type)` walks up by component type. A `__getattr__` trick makes
`call_context.parent.set_message("Hello")` dispatch the parent's command with the same
execution-results accumulator carried along, so one HTTP request can dirty several components.

### Addressing and hierarchy

Component IDs are path-like strings encoding the full ancestry (docs: `component_ids/` page;
source: `livecomponents/types.py`, `livecomponents/utils.py`):

```
|parent_type:parent_own_id|child_type:child_own_id
e.g.  |form:0|button:submit
```

`ComponentId` is a `str` subclass with a pipe operator to build child IDs
(`component_id | ("child_type", "own_id")`). `StateAddress` is a frozen Pydantic model of
`session_id` + `component_id` with `get_parent()`, `find_ancestor(type)`, etc. The docs compare the
whole mechanism to `os.path`: hierarchy features are string parsing over the ID. Crucially, the
hierarchy only exists if the template author threads it through by hand: a parent template must
pass `parent_id=component_id` to each child tag, and if it forgets, `component_ancestor` returns an
empty string and command calls from the child fail (docs: `nested_components/` page).

### Invoking commands from templates

Template tags (source: `livecomponents/templatetags/livecomponents.py`; docs: `templatetags/`):

- `{% livecomponent "name" ... %}` / `{% livecomponent_block %}...{% endlivecomponent_block %}`:
  wrappers over django-components' tags that additionally capture the raw inter-tag template
  source (via token capture) so the component can be re-rendered later in isolation.
- `{% component_attrs component_id %}`: emitted on the component's root element; renders
  `data-livecomponent-id="..."`, `hx-swap-oob="morph:[data-livecomponent-id='...']"`, and
  `key="..."`. Optional `swap_style="outerHTML"` overrides morphing.
- `{% call_command component_id "command_name" %}`: renders the endpoint URL with query params;
  used as an `hx-post` value. Arguments travel separately via `hx-vals='{"value": 1}'` (JSON,
  thanks to the htmx json-enc extension).
- `{% component_ancestor component_id "root_type" as root_id %}`: child templates use this to get
  the parent's ID and post to parent commands.
- `{% livecomponents_session_id as ... %}`: exposes the per-page session id to the DOM.
- `{% component_selector %}`, `{% no_morph %}`: JS conveniences.

Canonical child-calls-parent pattern (docs `nested_components/`):

```html
{% component_ancestor component_id "nestedcounter/root" as root_id %}
<button {% component_attrs component_id %}
    hx-post='{% call_command root_id "increment" %}'
    hx-vals='{"value": 1}'>+1</button>
```

## 2. Transport and protocol

- **Endpoints** (`livecomponents/urls.py`, verbatim): exactly two,
  `livecomponents/call_command/` -> `views.call_command` and `livecomponents/clear_session/` ->
  `views.clear_session`, mounted by the app under a user-chosen prefix.
- **Request**: htmx `POST` to
  `/livecomponents/call_command/?session_id=<sid>&component_id=<|a:1|b:2>&command_name=<name>`.
  Routing data is in the query string (parsed into a Pydantic `CallMethodRequestArgs`); command
  arguments are in the body, JSON by default (json-enc extension) with form-encoded fallback;
  `parse_body()` in `livecomponents/views.py` handles both. Body kwargs are splatted directly into
  the command: `command(call_context, **kwargs)`.
- **Response**: HTML fragments of every dirty component joined with newlines, plus response
  headers accumulated by execution results (HX-Redirect, HX-Refresh, HX-Push-Url, HX-Replace-Url,
  HX-Trigger). Because the page sets htmx `defaultSwapStyle: "none"` and every component root
  carries `hx-swap-oob="morph:[data-livecomponent-id='...']"`, htmx treats each fragment as an
  out-of-band swap and morphs it into the matching element wherever it sits on the page. One
  response can update any number of components.
- **Page prerequisites** (docs `quickstart/`): htmx 2.x plus the json-enc and alpine-morph
  extensions, Alpine.js 3.x plus its morph plugin, a `htmx-config` meta tag
  (`{"defaultSwapStyle":"none","allowNestedOobSwaps":false}`), and body attributes
  `hx-ext="alpine-morph, json-enc"` and `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'`.
- **CSRF**: standard Django CSRF via that `hx-headers` token; no extra endpoint auth by default.
- **Errors**: expired session returns HTTP 410 Gone; the documented client-side recovery is a
  hand-written `htmx:responseError` listener that reloads the page on 410 (docs
  `error_handling/`). Unknown component/command raise `BadRequest` (400).

## 3. State model

- **Session scoping** (`livecomponents/sessions.py`): a session id is
  `secrets.token_urlsafe(16)` generated fresh "for every page reload". It is not the Django auth
  session; it is a per-page-load capability token embedded in the DOM. Two tabs are two sessions.
- **Store** (`livecomponents/manager/stores.py`): pluggable `IStateStore`; default
  `RedisStateStore`, plus `MemoryStateStore` for tests. Redis layout per session:
  `lc:states:<sid>` (component states), `lc:ctxs:<sid>` (saved contexts),
  `lc:templates:<sid>` (component id -> template hash), and a shared
  `lc:template_cache:<hash>` (raw template source keyed by truncated MD5, deduplicated across
  sessions). TTL defaults: 1 day, refreshed on access; `clear_session` does a soft delete by
  dropping the TTL to 1 hour (`ttl_gc`) so the browser back button still works briefly.
- **Serialization** (`livecomponents/manager/serializers.py`): default `PickleStateSerializer`, a
  custom pickler with special handling: saved Django models pickle as (app, model, pk) and are
  re-fetched from the DB on load (raising if the row is gone); unsaved models pickle their
  `__dict__`; Pydantic models round-trip through `model_dump()` so fields can be added without
  breaking old blobs; Django forms store `initial` + bound data and re-run `full_clean()` on load.
  Output is shrunk with `pickletools.optimize()`.
- **Outer context**: templates re-render in isolation, so page context is gone on re-render. Two
  mitigations: copy what you need into state inside `init_state` (the documented contract), or
  `save_context="var1,var2"` on the tag to persist named context variables to the store
  (docs `context/`). `filter_flat_context()` strips `request`, underscore-prefixed vars, etc.
- **Security posture**: possession of the session id is authorization; any client with the id can
  invoke any `@command` in that session. Authentication is opt-in, per method, via
  `@livecomponents_login_required` on `init_state` and each command (docs `decorators/`).
  Body kwargs hit command signatures unvalidated beyond Python's TypeError (1.13.x releases were
  partly about turning bad client input into 400s instead of 500s). Pickle in Redis is a real
  deserialization surface if the store is ever attacker-writable, though the client never sends
  pickles. `xframe_options_exempt` setting (default False) controls iframe embedding.
- **Config** (docs `configuration/`): a `LIVECOMPONENTS` settings dict with three pluggable
  classes (`state_serializer`, `state_store`, `state_manager`), each `cls` + `config`.

## 4. Partial re-render mechanics

1. Command runs; default result is "this component is dirty". Explicit `IExecutionResult` returns
   override that (docs `execution_results/`; source `livecomponents/manager/execution_results.py`):
   `ComponentClean` (no render), `ComponentDirty` (self, or `ComponentDirty("other-id")` for
   another component), `ParentDirty`, `RedirectPage`, `RefreshPage`, `ReplaceUrl`, `PushUrl`,
   `TriggerEvents([Event(name=..., detail=...)])`; a command may return a list combining several.
2. The view collects the dirty set and deduplicates by hierarchy: because a child's id has the
   parent's id as a string prefix, any child whose ancestor is already dirty is dropped, since the
   parent's render subsumes it (`livecomponents/views.py`).
3. For each remaining dirty component the view re-renders from the stored raw template: component
   id -> template hash -> cached template source, rendered in a fresh `RequestContext` with state
   (plus saved context vars). This is the reason raw template source is stored at all: by the time
   Django's tag handler runs, only tokens/nodes exist, and slot content ("fills") could not
   otherwise be reproduced on an isolated re-render (docs `templates/`). Livecomponents subclasses
   django-components' `ComponentNode` as `LiveComponentNode` to capture the raw source at parse
   time.
4. Fragments return as OOB morph swaps (section 2). Parent re-render replaces the whole subtree;
   children get `update_state()` called with the parent's fresh kwargs. Alpine-morph preserves
   client-side state (focus, Alpine data) across swaps.
5. JS caveats (docs `javascript_integration/`): morph does not re-run `<script>` tags; workarounds
   are `swap_style="outerHTML"`, `{% no_morph %}` on the script, `allowNestedOobSwaps:false`, and
   `allowScriptTags:true` config, plus stashing JS object refs on DOM nodes and `hx-preserve` for
   expensive widgets. This page is effectively a catalog of glue-layer footguns.
6. Recommended architecture for trees (docs `nested_components/`): "root with stateless children":
   one stateful root owns all state and all commands; children are `StatelessLiveComponent`s whose
   templates post to the root via `component_ancestor`. This trades component reusability for a
   single source of truth and fewer state-sync problems.

## 5. Pain points and maintenance status (as of 2026-07)

Status: alive but slow and effectively single-company. Last release 1.20.0 on 2026-04-30 (fixes
for stateless-component commands and decorators, docs work); before that roughly one small release
a month through late 2025 (1.19.0 2025-10-27 TriggerEvents; 1.18.0 PushUrl; 1.17.x Sentry,
state-saving perf). GitHub metadata: pushed_at 2026-04-30, 0 open issues, 23 stars. First release
1.0.0 on 2023-10-24. It is deliberately not on PyPI: `pyproject.toml` carries the
`Private :: Do Not Upload` classifier and the documented install is
`pip install git+https://github.com/om-proptech/livecomponents@<SHA>`. Read: an internal tool that
happens to be public, not a community project.

Observed and admitted pain points:

- **Frozen on ancient django-components internals.** `pyproject.toml` pins
  `django-components = "^0.28.3"` (a 2023-era version; upstream django-components is far past that
  with heavily rewritten internals, and the quickstart still references
  `django_components.safer_staticfiles`, long removed upstream). Livecomponents subclasses the
  private `ComponentNode` and captures raw parser tokens, so it cannot track upstream without a
  rewrite. This is the canonical cost of building on someone else's private API.
- **Self-described leaky abstraction.** Users must know htmx attributes, htmx config flags,
  Alpine morph behavior, and OOB swap semantics to do anything nontrivial; the JS-integration page
  is a list of workarounds for the stack's own seams.
- **Manual context plumbing.** Outer template context does not survive re-render; the developer
  must remember to copy inputs into state or whitelist them via `save_context`. Forgetting is a
  silent wrong-render, not an error.
- **Manual hierarchy plumbing.** `parent_id=component_id` must be threaded by hand into every
  child tag; forgetting yields an empty ancestor id and broken commands at runtime.
- **Pickle-based state.** Deploys that change class internals can strand unpicklable Redis blobs;
  model-by-pk rehydration raises if the row was deleted; and pickle is an arbitrary-code surface
  if the store is compromised. They mitigated (Pydantic dict round-trip, model-by-pk) but the base
  choice remains fragile.
- **Session lifecycle friction.** Per-page-load sessions mean state duplication per tab, a
  hard-coded 410-and-reload recovery path, and a Redis dependency even in development.
- **Weak input validation at the boundary.** Client JSON is splatted into command signatures;
  several 1.13.x releases were fixes turning crashes on malformed input into 400s.

## 6. What to steal, what to avoid (for citry Component.Events)

### Worth stealing

1. **Declarative execution results.** Commands mutate state; the return value is a small algebra
   of intents (`ComponentDirty/Clean`, `ParentDirty`, `RedirectPage`, `PushUrl`, `ReplaceUrl`,
   `TriggerEvents`, or a list of them) that the framework maps onto the render set and response
   headers. This cleanly separates "what changed" from "how the response is shaped" and is easy to
   test. The default (return nothing -> re-render self) is the right ergonomic default.
2. **Path-shaped component addresses with prefix-based dedup.** `|type:id|type:id` ids make
   ancestor lookup, parent access, and re-render deduplication (drop any dirty child whose
   ancestor is also dirty) trivial string operations. Cheap, debuggable, log-friendly. Citry can
   generate these automatically during compilation instead of requiring manual `parent_id`
   threading, keeping the good idea and deleting the footgun.
3. **One endpoint, many targets, via out-of-band swaps keyed by a stable component-id attribute.**
   A single POST returns N fragments, each self-addressed (`hx-swap-oob="morph:[selector]"`), so
   any command can update any set of components anywhere on the page without client-side routing
   logic. Whatever transport citry picks, "response = set of self-addressed fragments" is the
   right shape.
4. **CallContext as the single command argument, with fluent cross-component calls.**
   `ctx.state`, `ctx.request`, `ctx.parent.some_command(...)`, `ctx.find_one(id)` sharing one
   dirty-set accumulator gives multi-component workflows in one request with no event-bus
   ceremony.
5. **Pluggable store/serializer with TTL plus soft-delete GC.** The `cls` + `config` settings
   shape, `MemoryStateStore` for tests, TTL refresh on access, and lowering the TTL instead of
   deleting on session clear (so the back button keeps working for a grace period) are all small,
   proven decisions worth copying. Deduplicating shared blobs by content hash (their template
   cache) is a good trick wherever citry stores anything per-component-instance.

### Mistakes to avoid

1. **Do not depend on private internals of the layer below.** Livecomponents subclassed
   django-components' `ComponentNode` and captured raw parser tokens, and is now pinned to a
   2023-era `^0.28.3` while upstream moved on. Citry owns its parser and compiler, so
   Component.Events must get a first-class, supported re-render entry point ("render component X
   with stored inputs Y") rather than anything that re-parses stored template source. Storing raw
   template strings in Redis to re-render later is the workaround to avoid, not the pattern to
   copy.
2. **Do not make re-render inputs an honor-system contract.** "The state must include parameters
   passed to the component" plus `save_context` is a silent-failure design: forget one variable
   and the second render is wrong with no error. Citry knows a component's inputs at compile time;
   the framework should capture and persist the render inputs automatically, and loudly error on
   anything it cannot serialize.
3. **Do not use pickle for durable state.** Prefer an explicit schema (the state class is already
   Pydantic-shaped; serialize via its own dump/load), version the blobs, and treat
   "cannot deserialize" as a recoverable re-init, not an exception. This removes the deploy
   fragility and the deserialization attack surface in one move.
4. **Do not pass client JSON straight into method signatures, and do not make auth opt-in per
   method.** Validate and coerce command arguments against the command's signature (400 on
   mismatch) from day one, and make the security default "commands inherit the page's auth
   requirements" with opt-out, instead of a `login_required` decorator the developer must remember
   on every command and on `init_state`.
5. **Do not ship a five-library client prerequisite.** The htmx + json-enc + alpine-morph +
   Alpine + morph-plugin + meta-config + body-attribute setup is where most of livecomponents'
   documented footguns live (scripts not re-running, nested OOB swaps, morph vs replace). Citry
   already owns a JS runtime layer; Component.Events should need at most one small runtime it
   controls, with morphing behavior it can guarantee.

## Source list

- Repo: https://github.com/om-proptech/livecomponents (metadata via GitHub API: pushed 2026-04-30, 23 stars, 0 open issues)
- Docs: https://om-proptech.github.io/livecomponents/ (pages: quickstart/, livecomponents/, nested_components/, component_ids/, context/, templates/, execution_results/, templatetags/, decorators/, configuration/, error_handling/, javascript_integration/, uploads/)
- Source files read (branch `main`): `livecomponents/urls.py`, `views.py`, `sessions.py`, `types.py`, `component.py`, `manager/manager.py`, `manager/stores.py`, `manager/serializers.py`, `templatetags/livecomponents.py`, `CHANGELOG.md`, `pyproject.toml`
- Related but distinct project (not covered): dylanjcastillo/django-live-components, a blog-post demo of the same idea
