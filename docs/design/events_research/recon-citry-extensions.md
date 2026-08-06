# Recon: citry's extension system as the substrate for Component.Events

Audit date: 2026-07-04. Code is authoritative; the design doc
(`docs/design/extensions.md`) matches the implementation closely (status line
at `docs/design/extensions.md:3` says "built, except the caching/short-circuit
phase"). All paths below are relative to `/Users/mac/repos/citry/` unless
absolute. The Python package root is `packages/py/citry/citry/`.

Directly load-bearing for this task: the extensions roadmap already names
`Component.Events` as part of a single "server-interactive / reactive
components" design exploration
(`docs/design/extensions_roadmap.md:62`): "handlers named by the event they
handle, multiple endpoints per component", to be designed together with the
HTTP-vs-WebSocket transport question and the Tetra / Alpine / live-components
/ `Component.View` approaches. The old `url` extension is explicitly subsumed
by this work (`docs/design/extensions_roadmap.md:135`).

---

## 1. Extension anatomy

### Declaration

An extension subclasses `Extension`
(`packages/py/citry/citry/extension.py:359`) and sets `name` (lowercase Python
identifier, validated in `__init_subclass__`, `extension.py:403-415`).
`class_name` (the nested per-component config class name) is derived
`snake_to_pascal(name)` at subclass creation (`extension.py:414-415`), so an
extension named `events` owns a nested `class Events:` on components.

Extensions are scoped per `Citry` instance and passed at construction:
`Citry(extensions=[...], extensions_defaults={...})` freezes the spec into
`CitrySettings.extensions` (a tuple; `citry.py:104-113`,
`settings.py:83-84`) and builds the `ExtensionManager` at the end of
`Citry.__init__` (`citry.py:190-191`), firing `on_extension_created`
immediately (`citry.py:191`). A spec entry may be a class, an instance, or a
`"pkg.mod.Class"` import string (`extension.py:579-593`). No
post-construction mutation; the instances tuple is immutable
(`extension.py:603`).

Built-ins are prepended by `_builtin_extensions()`; today that is exactly
`(DependenciesExtension,)` (`extension.py:535-549`). Built-in names are
reserved via duplicate-name validation (`extension.py:619-631`), and an
extension name that collides with existing `Component` API (either
`ext.name` or `ext.class_name` as an attribute) is rejected
(`extension.py:620-624`). `Component` has no `events`/`Events` attribute
today, so the name is free.

Every extension instance gets a `citry` back-reference set by the manager
(`extension.py:594-597`, declared `extension.py:385-388`). Lookup:
`manager.get_extension(name)` is O(1) (`extension.py:633-638`).

### The per-component nested config (the Component.Cache mechanism)

Base: `ExtensionConfig` (`extension.py:314-351`). Holds a weakref to the
component; `component=None` is a supported out-of-lifecycle case (kept for
Storybook-style extensions, `docs/design/extensions.md:191-213`), and the
`.component` property raises a clear `RuntimeError` for both the no-component
and the garbage-collected cases (`extension.py:336-351`).

At component class definition, the metaclass fires
`on_component_class_created` and then `_init_component_class`
(`component.py:176-177`), which for each extension synthesizes
`type(class_name, (user_nested_class, GlobalDefaults, ext.Config), {"component_class": cls})`
and assigns it back onto the component class (`extension.py:777-803`).
Precedence is therefore component-level > `extensions_defaults[name]` (from
settings, `settings.py:34-38,84`) > factory defaults (attributes on the
extension's `Config`). If the component defines no nested class, the
synthesized class is just `ext.Config`.

Consequence worth knowing for Events: the rebuild REPLACES the user's nested
class on the component. An extension that needs the raw declaration exactly
as the user wrote it (for example to enumerate handler methods) must capture
it in `on_component_class_created`, which fires before the rebuild; the
dependencies extension does exactly this via
`ctx.component_class.__dict__["Dependencies"]`
(`packages/py/citry/citry/extensions/dependencies/__init__.py:187-192`).
User-defined methods do survive the rebuild through inheritance (the user
class is the first base), so `component.events.my_handler` style access works
without the capture trick.

### Config at runtime

Per render, `_init_component_instance` instantiates each extension's config
class with the component and attaches it as `component.<ext.name>`
(`extension.py:805-819`), called from the render pipeline right before
`on_component_input` (`component_render.py:531-532`). Class-level config is
read as `getattr(comp_cls, ext.class_name)`. Global defaults come from
`citry.settings.extensions_defaults` (`extension.py:787`).

---

## 2. The hook catalog

All contexts are `@dataclass(frozen=True, slots=True)`
(`extension.py:54-261`); every context carries `citry`, render-scoped ones
also carry `component`. Manager dispatch is name-keyed and calls only
extensions that actually override a hook (`_extensions_with_hook`, cached per
name, `extension.py:689-717`; `has_hook` at `extension.py:978-980`). Hot-path
hooks skip even building the context when nothing subscribes
(`extension.py:859, 879, 932, 961, 995`).

Hooks declared on the `Extension` base (signature -> return; firing site):

| Hook | Context fields | Return | Fired from |
|---|---|---|---|
| `on_extension_created` (`extension.py:419`) | citry, extension | None | `citry.py:191` |
| `on_component_class_created` (`extension.py:424`) | citry, component_class | None | metaclass, `component.py:176` |
| `on_component_registered` (`extension.py:430`) | citry, name, component_class | None | `Citry.register`, `citry.py:210` |
| `on_component_unregistered` (`extension.py:433`) | citry, name, component_class | None | `Citry.unregister`, `citry.py:229` |
| `on_component_input` (`extension.py:438`) | citry, component, kwargs (mutable dict), slots (mutable dict) | None (mutate-only by design, `docs/design/extensions.md:290-299`) | `component_render.py:532` |
| **`on_component_data`** (`extension.py:445`) | citry, component, context (CitryContext), template_data, js_data, css_data (all mutable dicts) | None | `component_render.py:576` |
| **`on_component_rendered`** (`extension.py:451`) | citry, component, render (`CitryRender \| str \| None`), error | `CitryRender \| str \| None` (replace output; raise replaces error; threading semantics in `extension.py:921-943`) | `_finalize`, `component_render.py:446` |
| `on_slot_rendered` (`extension.py:458`) | citry, component, slot, slot_name, slot_node, slot_is_required, result | `RenderPart \| None` (threaded) | `nodes/__init__.py:1148` |
| **`on_attrs_resolved`** (`extension.py:466`) | citry, component, tag_name, attrs (resolved dict) | `dict \| None` (threaded); fires per element with at least one dynamic attribute | `nodes/__init__.py:596`, `components/dynamic.py:213` |
| **`on_render_context_merge`** (`extension.py:476`) | citry, parent_context, child_context | None; each extension merges its own slice of `child_context.extra` into `parent_context.extra` | `component_render.py:1006-1022` |
| **`on_serialize`** (`extension.py:488`) | citry, context (root CitryContext), html, placeholders (id -> exact text), deps_strategy, deps_position | `str \| None`, threaded on `html` (map policy, `extension.py:899-919`) | `serialize.py:152` |
| `on_template_loaded` (`extension.py:501`) | citry, component_class, content | `str \| None` (threaded) | `assets.py:229` |
| `on_template_compiled` (`extension.py:507`) | citry, component_class, nodes (`list[BodyItem]`) | `list \| None`; runs once per built node list, result is cached in the const-body cache | `component_render.py:651` |
| `on_js_loaded` (`extension.py:515`) | citry, component_class, content | `str \| None` | `assets.py:272` |
| `on_css_loaded` (`extension.py:521`) | citry, component_class, content | `str \| None` | `assets.py:274` |

Bolded rows are the serving/rendering/serialization seams most relevant to
Events: `on_component_data` is where an extension records per-render state
into `context.extra` (namespaced by owner,
`docs/design/extensions.md:373-387`), `on_render_context_merge` bubbles that
state up the tree, `on_serialize` is where page-wide output rewriting happens
(the dependencies extension inserts its script/style tags there), and
`on_attrs_resolved` could stamp event-binding attributes onto elements.

Custom (duck-typed, not on the base class) hooks that already exist:

- `on_files_reset`: fired by the core at asset reset (`assets.py:325`,
  manager method `extension.py:1045-1058`, context `extension.py:227-232`).
  Explicitly "the first consumer of the duck-typed custom-hook dispatch".
- `on_dependencies`: owned and fired by the dependencies extension at
  serialize time via `manager.emit("on_dependencies", ctx)`
  (`extensions/dependencies/emission.py:133-134` and `:464-465`; context
  `emission.py:61-78`, mutable `scripts`/`styles` lists).

Component-level hooks (distinct from the extension hooks, same names can
coexist): `Component.on_render` (replace/observe own output, generator form
for error boundaries, `component.py:592-662`) and the per-component
classmethod `Component.on_dependencies` (`component.py:566-590`). An Events
design will face the same duality: extension-level hooks vs per-component
handler methods.

---

## 3. Extension.urls and the contrib adapters

### Declaring routes

`Extension.urls` is a property (or attribute) returning `list[URLRoute]`
(`extension.py:390-401`); handlers reach engine state through `self.citry`.
`ExtensionManager.urls` combines all extensions' routes: built-ins own their
paths at the root of the citry prefix; a user extension's routes are wrapped
in `URLRoute(f"ext/{extension.name}/", children=...)`
(`extension.py:660-685`). `Citry.urls` delegates to it (`citry.py:274-283`).
Both are properties re-evaluated on each access, so the route table can be
dynamic in principle.

### URLRoute and the request/response abstraction

`citry/util/routing.py` is framework-neutral:

- `URLRoute(path, handler=None, children=(), name=None, methods=("GET",), extra={})`
  (`routing.py:56-84`). `{name}` path parameters match `[^/]+` and become
  handler keyword arguments (`routing.py:111-125`). Matching is definition
  order, first wins (`routing.py:128-141`).
- Handler contract: a plain sync callable `(request, **path_params) -> RouteResponse`;
  "`request` is whatever the adapter passes (citry's own handlers never read
  it)" (`routing.py:12-14`, protocol at `routing.py:36-39`).
- `RouteResponse(content: str | bytes = "", content_type: str = "text/plain", status: int = 200)`
  (`routing.py:42-53`). Nothing else: no headers, no cookies, no streaming.

So the abstraction is framework-neutral only because handlers so far never
read the request. What the `request` argument actually is per adapter:

- ASGI (`contrib/asgi.py:57-97`): the ASGI `scope` dict. The handler is
  called synchronously (`asgi.py:94`); the `receive` channel is NOT passed,
  so a request body is unreachable through this adapter today. Method not in
  `route.methods` gives 405 (`asgi.py:88-90`). Non-http scopes raise
  (`asgi.py:72-74`), so no WebSocket support. Also provides
  `reload_lifespan` for dev hot reload (`asgi.py:100-132`).
- WSGI (`contrib/wsgi.py:33-57`): the WSGI `environ` dict
  (`wsgi.py:54`); a body would be readable host-specifically via
  `environ["wsgi.input"]`.
- Django (`contrib/django.py:59-109`): the Django `HttpRequest`
  (`django.py:74`); `urlpatterns(citry_instance, prefix=...)` converts routes
  to `path()`/`re_path()` entries once, at call time (`django.py:94-109`).
  Route names pass through to Django's URL naming (`django.py:106,108`).
- FastAPI (`contrib/fastapi.py:30-36`) and Flask (`contrib/flask.py:33-53`)
  are one-call mounts over the ASGI/WSGI apps; both also call
  `set_mounted_prefix`.

Routing dynamism differs by adapter: ASGI and WSGI re-match against the live
`citry_instance.urls` on every request (`asgi.py:84`, `wsgi.py:45`); Django
snapshots the flattened table when `urlpatterns()` is called.

### URL shape and URL building

Built-in (dependencies) endpoints, mounted at the recorded prefix
(`extensions/dependencies/routes.py:4-11`, table at `routes.py:105-121`):

    <prefix>/cache/{class_id}.{script_type}             class JS/CSS (repopulates cache on miss)
    <prefix>/cache/{class_id}.{vars_hash}.{script_type} per-render variables script (needs shared cache multi-worker, routes.py:12-17)
    <prefix>/asset/{file_name}                          served Dependencies file
    <prefix>/citry.js                                   the client runtime

A user extension's routes land at `<prefix>/ext/<name>/...`.

The mount prefix is recorded via `Citry.set_mounted_prefix`
(`citry.py:302-314`); `Citry.build_url(path)` is plain
`f"{prefix}/{path}"` concatenation and raises `RuntimeError` with guidance
when nothing is mounted (`citry.py:316-331`). There is no reverse-by-name
with parameters; the dependencies extension formats its own paths
(`routes.py:43-57`).

End-to-end proof under FastAPI: `tests/test_contrib_fastapi.py` covers mount
prefix recording, runtime and cached-script serving, 404/405, and the full
fragment round trip where every URL in a fragment manifest is servable
(`test_contrib_fastapi.py:83-108`).

Public exports relevant here: `Extension`, `ExtensionConfig`,
`ExtensionManager`, `ExtensionCommand`, `URLRoute`, `RouteResponse`,
`CommandArg`... are all exported from `citry/__init__.py`
(`__init__.py:37-45,95`).

---

## 4. Rendering a component server-side on demand

The complete on-demand chain, all pieces existing today:

1. **Lookup by name**: `citry_instance.get(name)` -> component class
   (`citry.py:231-234`); names are normalized case-insensitively and a
   PascalCase class also registers its kebab-case form
   (`component_registry.py:10,53-64,141-146`). Lookup by stable id:
   `Citry.get_component_by_class_id(class_id)` (`citry.py:333-345`), which is
   how the script-serving endpoint reverses a URL to a class
   (`routes.py:75`). `class_id` is deterministic across processes (class
   name + hash of import path, `component.py:98-114`).
2. **Compose**: calling the class returns a `CitryElement`, not an instance
   (`component.py:188-211`); `slots` is a reserved kwarg carried separately
   (`component.py:199-211`).
3. **Render**: `element.render(template_globals=...) -> CitryRender`
   (`citry_element.py:86-111`). `template_globals` is the per-request channel
   (current user, request id) reaching every nested component
   (`component_render.py:84-115`).
4. **Serialize**: `render.serialize(deps_strategy=..., deps_position=...) -> str`
   (`citry_render.py:132-176`). `deps_strategy="fragment"` produces HTML
   meant for insertion into an already-loaded page: nothing inlined, a JSON
   manifest of asset URLs the client runtime fetches once per page; requires
   a mounted web integration (`citry_render.py:151-156`). This is the
   natural response body for an event endpoint that re-renders a component.

**Kwargs typing**: `Component.__init__` normalizes inputs to a plain dict
(`to_dict`) and, when a `Kwargs` dataclass is declared, constructs
`cls.Kwargs(**raw_kwargs)` (`component.py:463-475`); the metaclass converts a
plain annotated nested `Kwargs` class to a slots dataclass
(`component.py:154-162`). So unknown or missing kwargs raise `TypeError` at
instance creation. There is no type coercion or value validation beyond
dataclass construction; values keep whatever runtime types the caller (e.g. a
JSON body) supplies. `template_data`/`js_data`/`css_data` outputs are
validated against their optional schemas in `_normalize_data`
(`component_render.py:988-1003`).

---

## 5. ExtensionCommand and emit()

### Commands

`ExtensionCommand` (`extension.py:269-306`) is fully declarative: `name`,
`help`, `arguments` (`CommandArg`/`CommandArgGroup`, field names mirror
argparse one for one, `command.py:68-127`), `subcommands`, optional
`subparser_input`, and `handle(**parsed_options)`. The runner
(`command.py:161-239`) builds an argparse tree, stashes the matched command
instance via `parser.set_defaults(_command=..., _parser=...)`
(`command.py:183`), binds `citry` onto every command instance
(`command.py:179-180`), and dispatches. An extension lists commands in
`Extension.commands` (`extension.py:382-383`); aggregation is
`ExtensionManager.commands` / `Citry.commands` keyed by extension name
(`extension.py:647-658`, `citry.py:285-295`); the CLI path is
`citry ext run <extension> <command>`. Status: the CLI is complete, including
`ext list`/`ext run`, `--app` engine selection, and core `list`/`create`
commands; a Django management-command bridge and an MCP server were
considered and deliberately not built (`docs/design/extensions_commands.md:3-12`).

### emit()

`manager.emit(name, ctx, result="none"|"first"|"map", field=None)`
(`extension.py:719-773`):

- `"none"`: call every subscriber, ignore returns.
- `"first"`: return the first non-None return (short-circuit).
- `"map"`: thread `ctx.<field>`; each non-None return replaces it via
  `dataclasses.replace` (so the ctx must be a dataclass exposing that field,
  `extension.py:763-771`), and the final field value is returned.

Subscription is duck-typed: for a name not declared on the `Extension` base,
any extension defining a callable method of that name qualifies
(`extension.py:689-717`). This is exactly how an Events extension would own
its own hooks (say `on_event` / `on_event_handled`) for other extensions to
implement, mirroring `on_dependencies` (`emission.py:133-134`) and the planned
cache extension's `on_component_cache`/`on_component_cache_hit`
(`docs/design/extensions.md:313-319,446`). The per-name subscriber cache is
never invalidated, which is sound because the extension tuple is fixed at
construction.

---

## 6. Gaps: what Component.Events needs that does not exist

Grep confirms there is no events concept anywhere in the Python package
today (only file-watcher and threading "events"). The gaps, ordered by how
hard they bite:

1. **No request abstraction, and the ASGI adapter cannot deliver a POST
   body at all.** Handlers receive an opaque host object: the ASGI scope
   dict (`asgi.py:94`), the WSGI environ (`wsgi.py:54`), or a Django
   `HttpRequest` (`django.py:74`). The ASGI adapter never passes the
   `receive` channel, so under FastAPI/Starlette a handler has no way to
   read a request body. Every existing handler is GET-only and ignores
   `request` (`routes.py:64`). Events needs body + query + headers access,
   which means either a framework-neutral Request object filled by each
   adapter, or per-adapter handler wrappers. This is the single biggest
   substrate change required.
2. **Sync-only, HTTP-only handlers.** The ASGI adapter calls handlers
   synchronously inside its async app (`asgi.py:94`) and rejects non-http
   scopes (`asgi.py:72-74`). No async handlers, no streaming, no WebSocket
   seam, though the roadmap requires weighing WebSocket transport
   (`extensions_roadmap.md:62`).
3. **`RouteResponse` is too small for interactive endpoints**: content,
   content_type, status only (`routing.py:42-53`). No response headers
   (HTMX `HX-*`, `Set-Cookie`, cache control), no redirect, no JSON helper.
4. **No CSRF/auth/session story for POST.** The Django adapter's view is a
   plain function (`django.py:69-77`); Django's CSRF middleware would reject
   POSTs to it by default, and nothing marks it exempt or validates tokens.
   Host-neutral handlers cannot see host authentication.
5. **Dynamic per-component routes break under Django.** ASGI/WSGI adapters
   match against the live `Citry.urls` per request (`asgi.py:84`,
   `wsgi.py:45`), but Django snapshots patterns when `urlpatterns()` is
   called (`django.py:94-109`). A safe Events design uses a fixed dispatch
   route (e.g. `ext/events/{component}/{event}` resolved through the
   registry per request) rather than minting one route per component class.
6. **No reverse-URL helper with parameters.** `Citry.build_url` is prefix
   concatenation (`citry.py:316-331`); Events must format its own endpoint
   URLs (the pattern `routes.py:43-52` uses) and needs the mounted-prefix
   contract (`citry.py:302-331`) honored in every process that renders.
7. **No server-side state channel from a render to a later HTTP call.**
   Re-rendering a component on an event needs its inputs back. The
   dependencies extension's analog stores per-render artifacts in
   `Citry.cache` keyed by hashes and warns that multi-worker fragment
   setups need a shared backend (`routes.py:12-17`). Nothing exists for
   serializing/signing component kwargs into the page or persisting them
   server-side; that is new design surface (and a security surface).
8. **No error-to-HTTP mapping.** Adapters do not catch handler exceptions
   (`asgi.py:94`, `wsgi.py:54`, `django.py:74`); a `TypeError` from
   `Kwargs(**payload)` (`component.py:474`) would surface as a host 500.
   Payload validation is dataclass-construction only, with no coercion of
   JSON primitives.
9. **No client-side event runtime.** The shipped runtime (`citry.js`) is
   the dependency manager; per-instance JS gets `$onComponent(els, data)`
   (`test_contrib_fastapi.py:28`). Intercepting DOM events and POSTing to
   an endpoint, then swapping in a fragment response, is new JS. Delivery
   paths for it already exist (a route like `routes.py:120`, or
   `Script`/`Style` entries).
10. **No around-request or around-handler hook.** Extensions cannot observe
    another extension's route handling; if Events wants observability or
    pluggable behavior around event dispatch, it should define its own
    `emit()` hooks, which the substrate supports without core changes.

What Events does NOT need to build, because the substrate provides it: the
nested `Component.Events` config class (name `events` is free and the
three-level defaults merge comes for free, `extension.py:777-819`); capturing
the raw nested class before the rebuild if handler enumeration must see the
user's declaration verbatim (`dependencies/__init__.py:187-192` pattern);
out-of-lifecycle config instantiation with `component=None`
(`extension.py:331-346`); on-demand server render + fragment serialization
(section 4); per-render state bubbling via `context.extra` +
`on_render_context_merge` (owner-namespaced keys,
`docs/design/extensions.md:373-387`); attribute injection at render time via
`on_attrs_resolved`; page-level output rewriting via `on_serialize`;
`class_id` reverse lookup for URL-to-class resolution (`citry.py:333-345`);
`template_globals` for request-scoped render inputs (`citry_element.py:86-111`);
CLI commands; and `emit()` for Events-owned hooks.
