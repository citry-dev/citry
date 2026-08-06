# Recon: prior in-house work in the old django-components snapshot

Archaeology report for the design of citry's Component.Events extension.

## Scope and provenance

- The orchestrator's path variable for the extracted repo was unresolved (`undefined`). The snapshot was located as `/Users/mac/repos/citry/old-djc.zip` (zip entries dated up to 2026-06-30, includes uncommitted scratch files like `abc.html`, `.cursor/`, `.DS_Store`) and extracted read-only to `/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/old-djc/django-components/`. All relative paths below are relative to that extraction root, abbreviated `DJC/`. `.venv`, `node_modules`, `.git`, `__MACOSX`, `.DS_Store` were excluded at extraction; `build/` and `site/` were kept and included in the searches.
- Two sibling checkouts exist (`/Users/mac/repos/django-components`, `/Users/mac/repos/dcomp-rel-0.151.1`) but neither contains `GIT_TODOS_1.md` at depth 3; the zip is the copy with the uncommitted prototype work and was used exclusively.

## 1. Component.View: the shipped HTTP mechanism

Source: `DJC/src/django_components/extensions/view.py` (417 lines, complete and shipped; the docs contract is `DJC/docs/concepts/fundamentals/component_views_urls.md`).

### Exact API

`ComponentView` subclasses both the extension config base and Django's class-based `View` (`view.py:118`):

```py
class ComponentView(ExtensionComponentConfig, View):
```

User-facing surface, all under a nested `class View:` on the component:

- **One method per HTTP verb.** `get/post/put/patch/delete/head/options/trace` (`view.py:317-339`). Each default implementation delegates to a same-named method on a fresh component instance, e.g. `return self.component_cls().get(request, *args, **kwargs)` (`view.py:317-318`). That is backwards compatibility for the pre-0.137 style where handlers lived directly on `Component`; the `TODO_V1` comment at `view.py:308-316` says v1 should instead default to `render_to_response(...)` or `NotImplementedError` and drop Component-level handlers.
- **`component_cls`** attribute gives the handler access to the owning component class (`view.py:191-203`); a deprecated `component` dummy instance is kept for back-compat (`view.py:175-189`, `205-210`).
- **`public: ClassVar[bool | None] = None`** (`view.py:263`). Three-state: `True` forces a URL, `False` forbids one, `None` (default) auto-decides.
- **`get_route_path()` classmethod**, default `f"components/{cls.component_cls.class_id}/"` (`view.py:212-236`); overridable to add Django route params (`<str:username>/<int:user_id>/`).
- **`url` property** on the View config, equal to `get_component_url(self.component_cls)` (`view.py:238-257`).
- **Module-level `get_component_url(component, query=None, fragment=None, args=None, kwargs=None) -> str`** (`view.py:33-39`). Raises `RuntimeError` if the component is not public (`view.py:109-111`), reverses the route by name, then appends query/fragment via `format_url` (`view.py:113-115`). Query handling: `True` renders as a bare flag (`?enabled`), `False`/`None` are omitted, other values render normally (`view.py:57-61`); `args`/`kwargs` are passed to `django.urls.reverse` to fill route params (`view.py:82-107`).

### URL generation and registration

- Route name is `f"__component_url__{component.class_id}"` (`view.py:29-30`), so the URL identifies a component **class**, not an action.
- The `ViewExtension` (name `"view"`, auto-added to all components, `view.py:342-356`) creates the route in the `on_component_class_created` hook: `URLRoute(path=route_path, handler=comp_cls.as_view(), name=route_name)` and calls `extensions.add_extension_urls("view", [route])` (`view.py:363-381`). Routes live in a `WeakKeyDictionary` keyed by component class and are removed in `on_component_class_deleted` (`view.py:384-389`).
- Full URL anatomy: users mount `include("django_components.urls")`; that file mounts everything under `components/` (`DJC/src/django_components/urls.py:6-16`), extensions sit under `ext/` (`DJC/src/django_components/extension.py:1750-1754`), each extension under its name (`extension.py:1389`), so the final shape is `/components/ext/view/components/<class_id>/` (example in `view.py:79`, `166`).
- Registration-order gotcha: Django processes `urlpatterns` once; components created after that require forcing Django to re-process the resolvers, handled inside `extension.py:1436-1446`.

### Public/private mechanism

`_is_view_public` (`view.py:392-416`): explicit `public` wins; otherwise it checks whether any of the 8 verb methods was overridden relative to `ComponentView` and if so sets `view_cls.public = True`. The decision is computed **once** and cached by mutating the user's class; methods added or removed dynamically afterwards are not picked up (comment at `view.py:402-406`).

### Version history (from `DJC/CHANGELOG.md`)

- v0.92: `Component` stopped subclassing `View`; nested `Component.View` introduced (`CHANGELOG.md:3494`, `component_views_urls.md:3-4`).
- v0.137: verb handlers directly on `Component` deprecated, removal planned for v1.0 (`component_views_urls.md:65-83`).
- v0.140.0: `Component.Url` merged into `Component.View`; `ComponentUrl` renamed `ComponentView` (`CHANGELOG.md:1007`, `1026`, `1272-1276`).
- v0.142.0: query-parameter handling of `True/False/None` in `get_component_url` (`CHANGELOG.md:723`, `820`).
- v0.142.3: auto-public when any handler is defined; explicit `public = True` became optional (`CHANGELOG.md:657-698`).
- v0.144.0: `get_route_path()` override plus `args`/`kwargs` on `get_component_url` (`CHANGELOG.md:492-524`).

### The documented contract

`DJC/docs/concepts/fundamentals/component_views_urls.md` frames it as: define handlers on `Component.View` (`:22-55`); either register manually in `urlpatterns` via `Component.as_view()` (`:98-115`) or let the library auto-register and fetch the URL with `get_component_url()` ("an anonymous HTTP endpoint that triggers the component's handlers without having to register the component in urlpatterns", `:16`, `:117-133`); customize the path with `get_route_path()` (`:166-190`). Note an inconsistency: the docstring example embeds `class_id` in the custom route path (`view.py:95`) but the docs example does not (`component_views_urls.md:176-177`), so path uniqueness under custom routes is left to the user.

## 2. Fragments example (server + client)

`DJC/docs/examples/fragments/` demonstrates HTML-over-the-wire with three client techniques against one component URL.

Server side (`page.py`):

- The page component's `View.get` **multiplexes on a query parameter** because a component has exactly one URL and one handler per verb: `?type=alpine|js|htmx` returns a fragment, no param returns the whole page (`fragments/page.py:123-139`).
- Fragment responses use `deps_strategy="fragment"` on `render_to_response` (`fragments/page.py:130-139`) so the fragment's JS/CSS are loaded when inserted into an already-rendered page (strategy docs: `DJC/docs/concepts/advanced/rendering_js_css.md:102-170`).
- URLs are minted with `get_component_url(FragmentsPage, query={"type": ...})` in `get_template_data` and passed to the template (`fragments/page.py:17-26`).

Client side (`page.py` template):

- Vanilla JS: `fetch(url)` then `outerHTML` swap (`fragments/page.py:109-118`).
- AlpineJS: button `@click` fetch into an `x-html`-bound variable (`fragments/page.py:65-89`).
- HTMX: `hx-get="{{ htmx_url }}" hx-swap="outerHTML" hx-target="#target-htmx"` (`fragments/page.py:97-105`), htmx loaded from CDN (`:33`).

Fragment components (`component.py`):

- `SimpleFragment` runs client code via the shipped `$onComponent(({ message }, ctx) => ...)` hook, with data supplied by `get_js_data()` (`fragments/component.py:21-30`).
- `AlpineFragment` ships its markup inside `<template x-if="false">` so Alpine does not render it before the fragment's JS registers the Alpine component (`Alpine.data('frag', ...)`), then flips `x-if` to true (`fragments/component.py:50-84`). This is a hand-rolled workaround for "fragment JS must run before its reactive markup activates".

Tests only assert server-side rendering of the page and both fragments (`fragments/test_example_fragments.py:20-51`); the client flows are demonstrated, not asserted.

## 3. Form submission example

`DJC/docs/examples/form_submission/` is the flagship "self-contained endpoint" flow:

- The form component computes its own submit URL: `submit_url = get_component_url(ContactFormComponent)` in `get_template_data` (`form_submission/component.py:25-30`).
- Template posts to itself with HTMX: `<form hx-post="{{ submit_url }}" hx-target="#thank-you-container" hx-swap="innerHTML">` with `{% csrf_token %}` (`form_submission/component.py:33-34`); component URLs are ordinary Django views so CSRF applies normally.
- `View.post` reads `request.POST.get("name", "stranger")` by hand and responds with a different component's rendered HTML: `ThankYouMessage.render_to_response(kwargs={"name": name})` (`form_submission/component.py:55-62`). No form class, no schema, no urlpatterns edit (README pitch at `form_submission/README.md:3-11`).

## 4. Real usage in sampleproject

- `DJC/sampleproject/components/urls.py:9-16`: every real page is registered **manually** with `Component.as_view()` (`greeting`, `alpinui`, `vue-python`, three calendars). Nothing in the sampleproject uses `get_component_url`; the auto-URL mechanism is exercised only by the docs examples and tests.
- `DJC/sampleproject/components/todo/todo.py` is not a working app; it is a **design sandbox for a client-side events API** (see next section). `todo.html` is a trivial div+slot (`todo/todo.html:1-3`), `todo.js` is a stale calendar click alert (`todo/todo.js:1-4`), and `rando/rando.ts` exists to exercise relative TS imports from component JS (`todo.py:47`, `rando/rando.ts:1-5`).

## 5. The $emit/$on events sketch (most direct Events prior art)

`DJC/sampleproject/components/todo/todo.py` sketches, in comments and non-functional component JS, a parent/child event bus for component JS:

- Child emits: `$emit('updateItemsCount', itemsCount)` and multi-arg `$emit('updateItemsCount', itemsCount, $els, 123)` (`todo.py:97-106`).
- Parent binds a handler name in the **template** at the component call site: `{% component "my_comp" @updateItemsCount="handleItemsCount" / %}` (`todo.py:109-117`), i.e. Vue's `@event="handler"` syntax on the component tag.
- Parent registers handlers in JS with `$on("handleItemsCount", (newCount) => ...)`; multiple handlers per name are allowed and `$on` returns a stop function (`todo.py:119-134`).
- Parent-to-child data is solved by a callback-passing workaround: child `$emit('requestData', updateParentData)`, parent handler calls the callback with data (`todo.py:137-168`).
- The same file exercises the JS magic variables `$id, $data, $name, $els` and `$on` inside component `js:` blocks (`todo.py:56-83`, `201-243`).

Important status distinction: in the shipped JS runtime (`DJC/src/django_components_js/src/manager.ts`) the real API is `registerComponent(compClsId, async (data, { id, name, els }) => ...)` plus `registerComponentData`/`callComponent` (`manager.ts:43-66`, `487-517`, `713-715`), and `$onComponent(` is regex-rewritten to `DjangoComponents.manager.registerComponent("<comp_cls_id>", ` at serve time (`DJC/src/django_components/dependencies.py:505-513`). There is **no `$emit`/`$on` in the shipped runtime**; those exist only in the todo.py sketch and in the user's own alpine-composition library (next section). The `@event="handler"` component-tag syntax was never parsed by the template engine.

## 6. Events in alpine-composition, and what was patched (other/alpine-comp-*.js)

Both files are the user's own library, `alpine-composition v0.1.29` "By Juro Oravec" (`other/alpine-comp-orig.js:4-6`), vendored for hacking.

Event mechanics (identical in both copies, Vue-semantics): `emit(instance, event, ...args)` validates the event against the component's `emits` options (warning if neither declared nor present as a handler prop), runs an optional per-event validator function, then calls the **handler prop** `props[toHandlerKey(event)]` (i.e. `onEventName`), plus a `...Once` variant deduplicated via `instance._emitted` (`other/alpine-comp-orig.js:255-306`). Exposed on instances as `$emit` and `$emitsOptions` (`orig:733-741`). So events travel parent-to-child as `on*` props evaluated in the parent's Alpine scope; there is no bus.

What the modified copy changes (diff is 316 changed lines, annotated with `// TODO CHANGED` markers):

1. **Update-watcher rework.** Original had one global `watchEffect` touching all reactives and all props, torn down and re-created every time a ref was registered, guarded by an init flag (`orig:342-393`). Modified replaces it with one persistent props watcher plus one persistent watcher per registered ref, each with its own setup flag, all calling a shared `onReactiveChange()` that fires `onBeforeUpdated`/`onUpdated` callbacks. Motive: performance and not re-touching the world on every new ref.
2. **Proxy bypass.** `createReactivityAPI(instance, _self)` gains a second argument, "so that we can more efficiently access fields ... which don't need to go through magics / proxies"; call sites pass the raw vm (diff around `orig:336` and `orig:772-773`).
3. **Props handling hardened.** `useProps` signature changed from `(Alpine, instance, ...)` to `(Alpine, compName, el, ...)` so props evaluate before instance creation; it now **throws on unexpected props**, with an exemption for keys starting with `on` (treated as event-handler props); prop type metadata is computed once outside the watcher callback (diff around `orig:593-662`; the `on` check carries a TODO to require the third letter capitalized).
4. **Perf instrumentation**: `window.timeSpentInUseProps` and `window.timeSpentIn_init` counters.
5. **Alpine internals shortcuts**: `makeInstance` uses `closestDataStack(el)[0]` instead of `mergeProxies(...)` when there is one layer; `applySetupContextToVm` writes into the current data layer through the reactive proxy so updates stay reactive.
6. **`loadInitState` removed** (commented out): the mechanism that read a `data-x-<initKey>` JSON attribute into `instance.$initState`, i.e. the server-to-client initial-state channel; its server side also appears, commented out, as `"data-x-init": json.dumps({"slots": self.is_filled})` in `DJC/src/django_vue/component.py:66-73`.

Takeaway for Events: the user already built and tuned Vue-fidelity event emitting (declared emits, validators, `onX`/`onXOnce` handler props) on top of Alpine, and hit the practical issues (prop-vs-attr ambiguity, proxy overhead, init-state transport) in code.

## 7. The django_vue prototype (client-reactivity mechanics attempted)

`DJC/src/django_vue/` is an unfinished package (`pyproject.toml` present) that tried to make Django components behave like Vue SFCs with Alpine as the runtime. All of it is prototype-grade: key methods raise placeholder errors (`plugins/vue.py:113` `raise 1`; `component.py:51` `raise 3`), one converter is `pass` (`utils/vue_alpine2django.py:179-181`), and it targets extension hooks that did not exist yet (root `todo/TODO.md:10` shouts "IMPLEMENT `on_template_loaded`!!!!").

Mechanics attempted, per file:

- **`plugins/vue.py` (VueExtension).** Loads Alpine plus four of the user's own Alpine plugins from CDN (`alpine-alpine`, `alpine-provide-inject`, `alpine-reactivity`, `alpine-composition`, `vue.py:32-45`). In `on_extra_media` it emits a `<script type="module">` that: waits for `AlpineComposition`, loads each component's JS **as an ES module from a Blob URL** (`loadAsModule`, `vue.py:187-202`) because Vue components are default exports, registers them via `AlpineComposition.createAlpineComposition().registerComponent(Alpine, comp)`, and marks the scripts loaded in the dependency manager (`vue.py:83-101`, `122-180`). In `on_template_loaded` it stamps `x-data="<ClassName>"` on every root element of the component template (disabled by `raise 1`, `vue.py:107-119`). Ships `genAttrs`, a global that turns a getter over refs into Alpine `x-bind` attributes with correct reactivity tracking (`vue.py:208-279`).
- **`plugins/alpine_slot.py` (AlpineSlotPlugin).** Implements Vue-style **scoped slots across the server boundary**: a `{% fill ... alpine="{ abc: varOne }" %}` renders, at the original slot position, only `<span id="{component_id}--{slot_id}"></span>`; the actual fill content is wrapped in `<template x-teleport="#slot_id"><span x-data="{ $slot: {...js data...} }"><span x-data="{destructured}">...</span></span></template>` and appended after the component render in `on_template_postprocess` (`alpine_slot.py:30-70` docstring, `154-205` the shuffle, `208-217` the append). The `alpine` input is smuggled through tag validation by mutating the tag spec in `on_tag_fill`/`on_tag_slot` (`alpine_slot.py:84-141`); slot-side JS data comes from `js:`-prefixed kwargs. Python-defined slots opt in via an `alpine_slot()` decorator writing `Slot.meta` (`alpine_slot.py:314-318`). Prototype hazards visible: module-global mutable stores keyed by component id with manual cleanup (`alpine_slot.py:25-26`, `210-215`).
- **`plugins/html_component.py`.** Two things: (a) a comment-spec for transforming `<c-my-component ...>` HTML syntax into `{% component %}` tags, including `:prop` for Python inputs, `attrs:` for plain HTML attributes, `js:` for JS expressions, `<fill>`/`<slot>` tags, and self-closing to `/ %}` (`html_component.py:12-125`); this is the direct ancestor of citry's V3 `<c-*>` syntax. (b) A working `PydanticExtension` that validates component args/kwargs/slots on input and the template/js/css data on output against the class's generic type params using `TypeAdapter` (`html_component.py:215-247`); relevant to Events because it is the repo's only realized typed-payload validation mechanism.
- **`utils/vue_alpine2django.py`.** Source-to-source converter from Vue/Alpine template syntax to Django templates. Doctrine: client-side directives (`:x`, `@x`, `x-*`, `v-bind`) collapse into `x-bind="genAttrs(() => ({...}))"`, while **server-side constructs get an `ssr-` prefixed dialect**: `ssr-bind` (spread attrs), `ssr:key=val`, `ssr-text`/`ssr-html` (interpolation), `ssr-if`/`ssr-else-if`/`ssr-else`/`ssr-for` (control flow), `ssr-required` on slots (`vue_alpine2django.py:1-30`, `94-148`, `608-657`). Slots/fills conversion is implemented; component-tag conversion is not (`:179-181`) because of the recorded blocker: for `<MyComp ...>` you cannot know statically which bindings are props and which are HTML attributes, so a runtime "middleman" component would be needed to split them into `x-props` vs `x-bind` (`vue_alpine2django.py:155-166`). Also recorded: "SLOTS ARE RESOLVED AT SSR, JS-SIDE DYNAMIC SLOTS NOT SUPPORTED" (`:659`).
- **`component.py` (VueComponent).** Base class with `js_wrap_in_function = False`, `js_autoload = False` so component JS can be a module default export (`component.py:42-47`); commented-out `on_render_before` shows the intended root-element wiring: `x-data` = class name, `x-props` = generated props expression, `data-x-init` = JSON of server state such as which slots are filled (`component.py:54-77`).
- **`apps.py`.** `.vue` SFC ingestion: scan component dirs for `.vue` files, parse `<template>/<script>/<style>/<server>` blocks (`<server>` holds Python that defines the class), and **generate explicit Python component modules into a top-level `vue/` dir**, regenerated on server restart with content hashing planned (`apps.py:14-63`, `100-204`, `207-225`).

## 8. django-ninja proof of concept: definitive answer

**No PoC code exists anywhere in the tree.** Evidence:

- Case-insensitive grep for `ninja|openapi` over all `*.py`, `*.md`, `*.yml`, `*.yaml` in the extraction (excluding only `.venv`, `node_modules`, `.git`, `.asv`; `build/` and `site/` included) returns exactly one hit: `DJC/GIT_TODOS_1.md:5` - `"21. Add djc-ninja integration."`, listed under the `----- v0.140 -----` heading (`GIT_TODOS_1.md:4-6`, next to `"22. Finish storybook integration."`). v0.140.0 shipped (CHANGELOG.md:1007) without it.
- Grep for `from ninja|import ninja|ninja.Schema|NinjaAPI` over all `*.py` (same exclusions): zero hits.
- `DJC/pyproject.toml` has no ninja dependency (grep: zero hits).
- Bare "Schema" was not swept as a word (it over-matches pydantic/JSON-schema usage); the ninja-qualified forms above are the discriminating signatures and all are absent.

So djc-ninja was an intention only. The closest realized artifact to "typed endpoint payloads" is the `PydanticExtension` (`html_component.py:215-247`) and the `Kwargs` classes used across examples (e.g. `fragments/component.py:10-12`).

## 9. Where the verb-per-method model broke down

Observed limits, each with evidence in the snapshot:

1. **One URL per component class, at most one handler per verb.** Any component needing more than one GET-shaped operation must multiplex by hand: `FragmentsPage.View.get` dispatches on `?type=` to return either the full page or one of two fragments (`fragments/page.py:123-139`). Actions have no names; the verb is the only routing dimension the extension gives you.
2. **No typed request/response contract.** Handlers take raw `HttpRequest` and hand-parse (`request.POST.get("name", "stranger")`, `form_submission/component.py:59`). No schema validation, no serialization, no OpenAPI; that is precisely the gap the unbuilt djc-ninja line (`GIT_TODOS_1.md:5`) was meant to fill.
3. **Defaults are a migration shim.** Unoverridden verb methods delegate to deprecated Component-level methods (`view.py:317-339`); if neither exists the failure is an `AttributeError` on the component instance rather than a clean 405. The `TODO_V1` block admits the intended contract (render or `NotImplementedError`) was never landed (`view.py:308-316`).
4. **Public detection is one-shot and mutating.** `_is_view_public` caches its answer by writing `view_cls.public`, and dynamic method changes are explicitly not picked up (`view.py:402-406`, `412-415`).
5. **URL lifecycle is tied to class-creation timing**, requiring the urlpatterns re-processing workaround in `extension.py:1436-1446`.
6. **Custom route paths shift collision-avoidance to the user.** The docstring example manually embeds `class_id` in the custom path (`view.py:95`) while the docs version omits it (`component_views_urls.md:176-177`); route *names* stay unique but path patterns can shadow.
7. **No client half.** The View extension ends at HTTP. Everything client-side in the examples (fetch/HTMX wiring, fragment activation ordering like the `<template x-if="false">` trick at `fragments/component.py:50-67`) is user-authored glue; the server cannot describe "call me back on event X".

What demonstrably worked and is worth keeping: self-contained endpoint-per-component with zero urlpatterns editing (`form_submission`), URL minting from Python with query/fragment/route-param support (`get_component_url`), auto-exposure by defining a handler (v0.142.3), the `deps_strategy="fragment"` contract so fragment JS/CSS activate on insertion, and the `$onComponent` data-to-JS channel fed by `get_js_data()`.

## 10. Complete inventory of Events-relevant roadmap notes

- `DJC/GIT_TODOS_1.md:5`: "Add djc-ninja integration." (v0.140 bucket; never built). `:6` storybook.
- `DJC/todo/TODO.md:80`: "TODO - Add events to JS - See https://github.com/tetra-framework/tetra/discussions/71#discussioncomment-10641556" (the single most direct Events note).
- `DJC/todo/TODO.md:85-89`: Tetra inspiration list (JSON encoder/decoder, special handling of Django Models via `._as_dict()`, attrs merging).
- `DJC/todo/TODO.md:99-100`: comparison set for reactive/live-component frameworks, from upstream discussion #310: "Unicorn, Tetra, Reactor, TurboDjango, Sockpuppet, djhtmx".
- `DJC/todo/TODO.md:104-132`: planned `setAlpineData($els, {...})` helper to push data from component JS into Alpine scopes.
- `DJC/todo/TODO.md:134-177`: Alpine slot/teleport encapsulation plan (realized as `alpine_slot.py`).
- `DJC/todo/TODO.md:181-198`: more competition noted: Streamlit, Solara, Reactpy, FastHTML, Trame (with a Trame server-driven UI snippet).
- `DJC/todo/TODO.md:203-208`: long-term vision: an AlpineJS port of Vuetify ("AlpineUI") with a standardized data-passing convention, bindable from Python/Go/Rust.
- `DJC/todo/TODO_v2.md:13-18`: plugin ability to pre-process tag inputs (`alpine=` on slot/fill) and transform templates.
- `DJC/TODO_VUE PLUGIN.md:1-93`: full pipeline design for JS-scoped slot data (`js:` kwargs on `{% slot %}`, `alpine=` on `{% fill %}`, validation bypass, teleport wrapping, per-render-id state, cleanup).
- `DJC/todo/TODO_VUE_COMPAT.md:136, 189, 251`: unchecked Vue-compat items `emits`, `$emit()`, `defineProps() & defineEmits()` (nothing in the matrix is checked off).
- `DJC/docs/guides/integrations/TODO_alpine.md:1-6`: stub pointing at upstream PR #821 and issues #818, #791 for Alpine integration docs.
- `DJC/docs/guides/cookbook/TODO_alpine_composition.md` and `TODO_alpine_reactivity.md`: both zero-byte placeholders.
- `DJC/todo/feature-comp-dvc.md:12`: declare slots on the component class as a `Slots` TypedDict for documentation and typing (shape precedent for declaring an Events schema on the class).
- `DJC/src/django_vue/component.py:167-176`: django-vue roadmap (finish djc v1, django-vue templating, alpinui, then continue).
- **Websockets/SSE/live components: zero notes.** Grep for `websocket|liveview|live component|server-sent|SSE|django-channels` over all `*.md`/`*.yml` (excluding venvs, generated `site/`, `build/`, CHANGELOG) returns only irrelevant hits ("Discord channels", "youtube channels"). The prior art is entirely request/response (fetch/HTMX) plus client-side Alpine reactivity; nothing push-based was ever planned on paper.
- Root `DJC/TODO.yml` (27 lines): community/marketing tasks only, nothing on events/interactivity.
- Incidental: `DJC/ai/ai_component.py` is an unrelated experiment (LLM-generated components via OpenAI).

## 11. Raw material the Events design can lift directly

- Naming and semantics of the client event API already sketched: `$emit(name, ...args)` multi-arg, `$on(name, handler)` returning an unsubscribe function, multiple handlers per name, template-level `@event="handler"` binding at the call site (`todo.py:97-168`).
- Vue-fidelity event validation model: declared `emits` map with optional per-event validator, handler props `onX`/`onXOnce`, warn-on-undeclared (`alpine-comp-orig.js:255-306`).
- Server-to-client data channels that shipped: `get_js_data()` into `$onComponent(data, {id, name, els})` (`fragments/component.py:21-30`, `manager.ts:43-66`), and the abandoned `data-x-init` JSON attribute channel (`component.py:66-73`, removed in the modified Alpine bundle).
- Endpoint plumbing that shipped: per-class anonymous URL under an extension-owned prefix, name-based reverse, auto-exposure, weak-ref route cleanup (`view.py:342-389`).
- Typed payload validation precedent: `PydanticExtension.on_input`/`on_data` (`html_component.py:215-247`).
- The recorded failure modes to avoid: one-shot cached publicness, query-param multiplexing for multiple actions, untyped handlers, props-vs-attrs ambiguity needing a runtime middleman (`vue_alpine2django.py:155-166`), global mutable per-render stores with manual cleanup (`alpine_slot.py:25-26`).
