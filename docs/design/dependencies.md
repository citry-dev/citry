# Design: JS/CSS dependency rendering, fragments, and host integration

**Status (updated 2026-08-13): built and under integration hardening.** Phases
1-5 (section 16), the `packages/js/citry-client` TypeScript/minification build,
and the user-facing dependency documentation are implemented. The core
dependency manager remains readable package-data JavaScript because other
extension runtimes register against it. This document designs the
emission half of the dependency story: how a component's JS and CSS (primary
`js`/`css` pairs, secondary `Dependencies` entries, and per-render JS/CSS
variables) get collected during a render and placed into the final HTML; the
`<c-js>`/`<c-css>` built-in tags; HTML fragment support and the client-side
dependency manager; the URL endpoints that serve scripts and fragments; and
the two plug-and-play integration surfaces this requires, web servers and
cache backends.

It is the successor to three "deferred" markers in the existing docs: the
emission phase of the `dependencies` extension
([`asset_loading.md`](asset_loading.md) section 7.5), phases 4-5 of the render
pipeline ([`component_rendering.md`](component_rendering.md) sections 5-6), and extension phasing
items 2 and 6 ([`extensions.md`](extensions.md) section 13).

Upstream references: django-components
[#1144](https://github.com/django-components/django-components/issues/1144)
(media becomes an extension),
[#1340](https://github.com/django-components/django-components/issues/1340) /
[#897](https://github.com/django-components/django-components/issues/897)
(fragments/partials),
[#1650](https://github.com/django-components/django-components/issues/1650)
(preserve structured render data for safe cache replay),
[#1444](https://github.com/django-components/django-components/issues/1444)
(head tag extension),
[#1230](https://github.com/django-components/django-components/issues/1230)
(scoped CSS, a future consumer of the root-marker hook).

---

## 1. Prior art (what was searched)

In `packages/py/citry/_djc_reference/`:

- **`dependencies.py`** (1925 lines) is the blueprint. The pieces:
  - `Script`/`Style`/`Dependency` structs with `kind`
    (`core`/`component`/`variables`/`extra`), url-or-content exclusivity,
    `to_json`/`from_json`, dedupe by url-or-content (`:114-401`, `:1410`).
  - The script cache: keys like `__components:<class_id>:js:<vars_hash>`
    (`:436-443`), `cache_component_js/css` (`:503`, `:584`),
    `cache_component_js_vars`/`cache_component_css_vars` which hash the
    variables JSON and cache a generated script per hash (`:548-652`).
  - The `$component(` to `registerComponent("<class_id>", ` source rewrite
    (`:492-500`).
  - The CSS-variables stylesheet: `[data-djc-css-<hash>] { --key: value }`
    (`:616-652`), bound to elements via an attribute spliced onto component
    root elements (`set_component_attrs_for_js_and_css`, `:663-707`).
  - The string transport this design replaces: `<!-- _RENDERED
    class_id,comp_id,js_hash,css_hash -->` comments prepended per instance
    (`:727-746`, written from `component_render.py:662-671`), regex-extracted
    by `_process_dep_declarations` (`:1022-1275`).
  - `render_dependencies()` with six strategies
    (`document`/`fragment`/`simple`/`prepend`/`append`/`ignore`) and the
    **flagged TODO** that prepend/append should be insertion positions, not
    strategies (`:876-880`).
  - Categorization: component JS/CSS and variables inline for document/simple
    but fetch-in-client for fragment; `Media` entries likewise; everything
    emitted inline is also "marked as loaded" so the client manager never
    re-fetches it (`:1140-1222`, `:1278-1407`).
  - The exec script: a `<script type="application/json" data-djc>` JSON
    manifest (base64-armored) telling the client manager what to fetch, what
    to mark loaded, and which component instances to call (`:1635-1745`).
  - Default placement: CSS before the first `</head>`, JS before the last
    `</body>`, by string search over the final HTML (`:1751-1805`).
  - `cached_script_view` + `urlpatterns`: GET endpoint serving cached scripts
    at `cache/<class_id>.<vars_hash>.<js|css>` (`:1825-1861`).
  - `{% component_js_dependencies %}` / `{% component_css_dependencies %}`
    placeholder tags (`:1883-1925`), which become `<c-js>`/`<c-css>` here.
  - The **flagged TODO_V1** (`:1367-1371`): `Media` should give `Script`/
    `Style` objects directly rather than rendering to strings and re-parsing
    (`_parse_dependency_from_string`/`TagAttrParser`, `:1421-1559`).
- **`static/django_components/django_components.min.js`**: the client manager.
  Read in minified form; the API surface is `registerComponent`,
  `registerComponentData`, `callComponent`, `loadJs`/`loadCss` from JSON tag
  descriptors, `markScriptLoaded`/`isScriptLoaded`, a MutationObserver that
  picks up inserted `<script data-djc>` tags, and a queue that delays
  component calls until their script and data dependencies are loaded.
- **`component.py:3390-3420`**: `_call_data_methods` computes
  `get_template_data`, `get_js_data`, `get_css_data` together and validates
  each against `TemplateData`/`JsData`/`CssData`.
- **`component_render.py:487-493`**: scripts are (re)cached during render;
  variables are hashed into `js_input_hash`/`css_input_hash` per render.
- **`cache.py:29-50`**: `get_component_media_cache()` returns the Django cache
  named by `COMPONENTS.cache`, else an unbounded `LocMemCache`.
- **`extensions/dependencies.py`** (29 lines): eagerly caches each class's
  JS/CSS at class creation so fragment requests survive a server restart.
- **`util/routing.py`**: `URLRoute`/`URLRouteHandler`, already
  framework-neutral. **`compat/django.py:132-165`**: `routes_to_django`, the
  pattern every host adapter follows. **`urls.py`**: mounts dependency +
  extension routes under `components/`.
- **`extensions/view.py`**: `Component.View` + `get_component_url` (`:33`),
  the "component served at a URL" feature; Django-coupled, but the
  registration shape informs section 9.5.
- **`util/css.py`** (`serialize_css_var_value`) and `util/misc.py`
  (`format_url`, `hash_comp_cls`): small helpers this package pulls in.

In `packages/py/citry/citry/`:

- `extensions/dependencies.py`: the built-in extension with the loading half
  (captured declarations, `CitryDependencies` merge). This design adds the
  emission half to the same extension, as planned.
- `component_render.py:887-900`: `_merge_dependencies`, the TODO-marked hook
  where a child render's `extra` reaches its parent.
- `citry_context.py`: `extra`, the tree-wide bag "for extensions", currently
  unused.
- `serialize.py`: the two-pass frame machinery; `data-cid-<id>` markers are
  spliced onto component root elements via `mark_html` (`:77-80`), and child
  components ride `<template c-render-id="...">` placeholders. This is the
  splice point for CSS-variable markers and for `<c-js>`/`<c-css>`.
- `extension.py`: smart dispatch + `emit` (`:568`), `_builtin_extensions()`
  (`:428`), `on_component_data` currently carrying only `template_data`
  (the 7.5 TODO in [`extensions.md`](extensions.md)).
- `component_registry.py:39`: `js` and `css` are already reserved built-in
  component names.
- `settings.py`: `CitrySettings` (frozen), currently `extensions`,
  `extensions_defaults`, `dirs`.
- `citry.py`: the instance that owns registry, caches, file index; new
  instance state (class-id index, cache, mounted prefix) lands here per the
  #1413 rule.

---

## 2. The shape of the whole: one extension, two integration hooks

Everything user-visible in this package is owned by the existing built-in
`dependencies` extension (realizing DJC #1144 end to end). The core engine
gains only generic hooks: the `on_render_context_merge` hook, a serialize hook, a
placeholder part type, the routing types, and the cache protocol. The core
never knows what JS or CSS are.

The end-to-end document flow:

1. A component declares assets (`js`/`css` pairs, `Dependencies` entries) and
   optionally per-render variables (`js_data()`/`css_data()`, section 5).
2. During its render, the extension caches the class's scripts (once) and the
   render's variables scripts (per distinct data), and records "this exact
   class version and instance rendered, with these variable hashes" into
   `CitryContext.extra`.
3. As child renders are consumed, records bubble upward through the
   `on_render_context_merge` hook, preserving order.
4. At `serialize()`, the extension turns the collected records into
   `Script`/`Style` lists, runs the `on_dependencies` hooks, and places the
   rendered tags: into `<c-js>`/`<c-css>` placeholders if present, else into
   `</head>`/`</body>` (section 7).

The fragment flow differs only at step 4: nothing is inlined; instead a JSON
manifest tells the client-side manager which URLs to fetch (section 8). That
is what requires the two integration hooks:

- **Web server integration** (section 9): the URLs that serve cached scripts
  (and the client runtime) must be mounted into some host app. Citry owns a
  framework-neutral route table; thin adapters mount it.
- **Cache integration** (section 10): the scripts behind those URLs live in a
  cache that must be reachable from whichever process serves the request, so
  the backend is pluggable via settings.

Because dependencies travel as data on render objects, the entire DJC string
transport disappears: no `<!-- _RENDERED -->` comments, no regex extraction,
no re-parsing of rendered HTML. Nested renders need no "ignore when nested"
special case either: deps merge upward structurally, and placement happens
only at the one explicit `serialize()` call.

---

## 3. Data model: `Script` and `Style`

Ported nearly as-is into the extension's package (section 13):

```python
@dataclass
class Script:           # renders <script src="..."> or <script>...</script>
    content: str | None = None
    url: str | None = None
    attrs: dict[str, str | bool] = field(default_factory=dict)
    kind: DependencyKind = "extra"     # "core" | "component" | "variables" | "extra"
    origin_class_id: str | None = None
    wrap: bool = True                  # IIFE-wrap inline classic-JS content

@dataclass
class Style:            # renders <link rel="stylesheet" href="..."> or <style>...</style>
    ...                  # same fields minus wrap
```

Kept from DJC: url-or-content mutual exclusivity, the `</script>`-in-content
validity check, `render()`/`render_json()`, `to_json`/`from_json` (the cache
storage format), equality and hashing by url-or-content, the IIFE wrap rule
keyed on the `type` attribute, and `__html__`. Closing-tag checks follow HTML's
case-insensitive tag-name rule, so mixed-case `</script>` and `</style>` forms
are rejected too. Dependency lists de-duplicate by equality in first-seen
order; a pre-rendered `__html__` object does not need to be hashable.

One deliberate reshape, resolving DJC's flagged TODO_V1
(`dependencies.py:1367`): **`Script`/`Style` objects are first-class
`Dependencies` entries.** A user writes

```python
class Chart(Component):
    class Dependencies:
        js = [Script(url="https://cdn.example.com/chart.js", attrs={"defer": True}), "helpers.js"]
        css = {"print": Style(url="/static/print.css")}
```

and the extension's entry resolution (the existing `_resolve_entry`) passes
them through as objects. String/path entries normalize *into* `Script`/`Style`
at emission time. DJC's path, rendering `Media` to HTML strings and re-parsing
them with an HTMLParser (`_parse_dependency_from_string`, `TagAttrParser`), is
not ported; the `__html__` escape hatch remains for genuinely pre-rendered
tags, which are wrapped into a content-bearing object verbatim.

Each `Dependencies.css` media value must be one entry or a list/tuple of
entries. Invalid values fail during normalization with an error that names the
media key and component, before emission begins.

---

## 4. Component identity and the script cache

### 4.1 `Component.class_id` (resolves the migration doc's ❓)

Cache keys and script URLs need a stable, URL-safe identifier per component
class. Citry adopts DJC's scheme (`hash_comp_cls`): the class name plus a
short hash of the full import path, e.g. `Table_a1b2c3`. Properties that
matter:

- **Deterministic across processes and restarts** (derived from the import
  path, not `id()`), so cache keys written by one worker resolve in another.
- Reverse lookup: `Citry` keeps a `WeakValueDictionary[str, type[Component]]`
  from `class_id` to class, maintained at class registration, so the script
  endpoint can find the class. Instance state per #1413, no module global.

`class_id` is computed lazily and cached on the class. `get_import_path`
ports from DJC `util/misc.py` alongside it.

### 4.2 What is cached, under which keys

Same scheme as DJC (`dependencies.py:436`), with the citry prefix:

| Key | Value (JSON) |
|---|---|
| `citry:<class_id>:js` | mutable compatibility entry for the current class's `Component.js` |
| `citry:<class_id>:css` | mutable compatibility entry for the current class's `Component.css` |
| `citry:<class_id>:js:component:<content_hash>` | immutable `Script` for one class JS version (post-hook, `$component` transformed) |
| `citry:<class_id>:css:component:<content_hash>` | immutable `Style` for one class CSS version |
| `citry:<class_id>:js:<vars_hash>` | generated script registering one distinct `js_data()` result |
| `citry:<class_id>:css:<vars_hash>` | generated stylesheet defining one distinct `css_data()` result |

During a live render, empty and whitespace-only `Component.js` or
`Component.css` content is absent from dependency delivery. It creates no live
dependency record, component-asset cache entry, fragment URL, variables
payload, runtime manifest, or CSS-presence record. This same rule is used
during collection, document emission, and fragment emission, so every
advertised component URL has substantive content to serve.

`<content_hash>` is the first 12 hex characters of the md5 of the serialized
class-level object. Generated class-script URLs include it, so old and new
workers sharing a cache cannot overwrite the payload named by one another's
pages. The stable keys remain for compatibility with unversioned URLs. A read
through one of those URLs validates the stored payload against the class in
that worker and repairs a mismatch before returning its local version.

`<vars_hash>` is the first 32 hexadecimal characters of the SHA-256 digest of
the canonical variables JSON. Identical data across instances of the same
component shares one cached script, so a large variables payload is fetched by
the browser once.

### 4.3 Lazy repopulation instead of eager caching (flagged divergence)

DJC's `extensions/dependencies.py` eagerly caches every class's JS/CSS at
class creation, so a fragment request arriving after a server restart still
finds the class scripts. Citry's asset loading is deliberately lazy (no file
I/O at import), so instead the **script endpoint repopulates on demand**: on
a cache miss for a class-level key (no vars hash), it looks the class up by
`class_id` and re-caches from `Component.get_js()`/`get_css()` before
retrying. That covers the restart case without import-time I/O.

Variables scripts cannot be regenerated (the data existed only during the
render that produced them), so they genuinely need a cache that outlives the
rendering process; section 10 documents that operational requirement.

`reset_files()` already fires `on_files_reset`; the extension extends its
existing handler to also delete the class's mutable compatibility keys (the
citry equivalent of DJC's `evict_component_scripts`). New content gets a new
immutable key and URL on its next use.

Removing a component's final registry alias deletes the same class-level JS
and CSS compatibility keys. A replacement class may intentionally have the
same deterministic `class_id`; payload validation and its distinct content
hash ensure it cannot consume a retired class's content, even if the old class
is retained and writes again or old and new workers share a backend. Removing
only one alias keeps the compatibility entries because the same class remains
registered. Immutable class-version and variables-script keys follow the
cache backend's normal expiry or capacity policy.

---

## 5. JS and CSS variables

### 5.1 The data methods

Mirroring `template_data` (kwargs-and-slots only, no args, no context):

```python
class Table(Component):
    js = "..."           # may use $component(...)
    css = "..."          # may use var(--row-color)

    class JsData:        # optional typed schema, auto-dataclass like TemplateData
        rows: int

    def js_data(self, kwargs, slots):
        return {"rows": kwargs.row_count}

    def css_data(self, kwargs, slots):
        return {"row-color": kwargs.color}
```

`render_impl` calls all three data methods together (as DJC's
`_call_data_methods` does), validates `JsData`/`CssData` when declared, and
`on_component_data`'s context gains `js_data` and `css_data`, closing the
TODO in [`extensions.md`](extensions.md) section 7.5. CSS data still needs a
component CSS consumer. JS data is captured when `$component` or rendered
Alpine expressions can consume it; data alone does not activate the client.

### 5.2 How variables reach the browser

The mechanism ports from DJC conceptually unchanged:

- **CSS variables** become a cached stylesheet
  `[data-ccss-<hash>] { --row-color: red; }` (values serialized via the
  ported `serialize_css_var_value`), and the rendering component's root
  elements get a `data-ccss-<hash>` marker attribute. Citry splices it in the
  existing serialize marker pass: the marker list at `serialize.py:77-80` is
  already plural, so the extension only needs a way to contribute markers per
  component instance (the **root-marker hook**, section 7.4).
  Keys must be exact strings and safe custom-property suffixes. Values are
  limited to strings, finite numbers, or `None`; booleans and structured JSON
  values are rejected. Quoted strings use CSSOM-style escaping, while raw CSS
  text is checked for declaration and style-tag breakout plus balanced blocks,
  strings, and comments. This is a structural containment check, not a full
  CSS grammar validator.
- **JS variables** become a cached script that calls
  `Citry.manager.registerComponentData("<class_id>", "<hash>", json_source)`.
  Each client-active instance produces an explicit component call
  (`class_id`, `component_id`, `js_vars_hash`, `init | seed`) in the
  serialize-time manifest. `init` seeds the instance's Alpine scope and then
  runs `$component`; `seed` performs only the first operation. The content
  stays deduplicated by hash, while the manager parses a fresh graph per call
  so sibling instances never share nested mutable values.
- **`$component` sugar**: a regex rewrite applied once when the class's JS is
  first cached: `$component(` becomes
  `Citry.manager.registerComponent("<class_id>", `.

A component that declares `JsData` or overrides `js_data()` receives the
seed-only call when its rendered output uses Alpine, even if that render
returns an empty mapping. The empty call clears keys owned by an earlier
correlated render. A component that inherits the framework's always-empty
default does not receive a seed call.

Citry already stamps `data-cid-<id>` on component root elements, which is
exactly the element-association half DJC had to add by post-processing HTML
(`set_component_attrs_for_js_and_css`); here it falls out of the existing
serialize pass.

---

## 6. Collection during render

The extension's render-time job, all through existing or already-designed
hooks:

1. **`on_component_data`**: compute `vars_hash`es (caching the variables
   scripts, section 4.2), ensure the class scripts are cached, and append a
   record to the current render's `CitryContext.extra` under the extension's
   key:

   ```python
   DependencyRecord(
       class_id,
       component_id,
       js_vars_hash,
       css_vars_hash,
       component_class=type(component),
   )
   ```

   The hook context must expose the render's `CitryContext` (or the record
   is attached via the component instance's current context); this is the
   one context-surface addition the design needs, and it is flagged as such
   in section 11.
2. **`on_render_context_merge`** (the hook that replaces the direct
   `_merge_dependencies` call, [`extensions.md`](extensions.md) section 9.1):
   the extension extends the parent's record list with the child's,
   preserving order. This wires the so-far-empty hook at
   `component_render.py:890`; the deferred-render queue consumes children in
   template order, so the merged list approximates document order, which is
   what script-execution order wants. Building this hook is part of this
   package (first real consumer).

Records hold four small scalar fields plus the exact component class that
rendered them; the heavy content lives in the cache. Retaining that class for
the lifetime of an unfinished or caller-retained `CitryRender` is intentional. It
ensures serialization uses the matching dependencies even if a hot replacement
with the same deterministic `class_id` is registered between `render()` and
`serialize()`. Releasing the render releases this ownership. This mirrors
DJC's comment payload, minus the string smuggling. This retains class identity,
not an immutable snapshot of its file caches: calling `reset_files()` on that
same class before serialization deliberately makes serialization load its new
JS/CSS.

---

## 7. Emission at serialize

### 7.1 Strategy and position (resolving DJC's flagged TODO)

DJC has six strategies and a TODO (`dependencies.py:876`) saying two of them
are really insertion positions. Citry implements the TODO:

```python
render.serialize(
    deps_strategy="document",   # "document" | "simple" | "fragment" | "ignore"
    deps_position="smart",      # "smart" | "prepend" | "append"   (document/simple only)
)
```

- **`document`** (default): emit all tags inline, plus the client runtime and
  a mark-as-loaded manifest so later fragments dedupe against the page.
- **`simple`**: tags only, no client runtime, no manifest. For static pages
  and emails.
- **`fragment`**: no tags inlined; emit the pre-loader plus a JSON manifest
  of URLs for the client manager to fetch (section 8).
- **`ignore`**: content unchanged.
- **`deps_position`**: `smart` uses placeholders/default locations (7.3);
  `prepend`/`append` put the tags before/after the whole output.

The call-local `security_javascript` policy is a ceiling over these strategies.
`warn` keeps their exact output, `omit` removes executable dependencies and
manager manifests while retaining HTML and CSS, and `forbid` rejects reached
client requirements even when `simple` or `ignore` would not emit the manager.
An omit fragment takes a dedicated CSS-only path: styles are emitted directly,
so it needs neither a preloader nor a mounted integration.

`str(render)` keeps using the defaults. Strategy lives at serialize, per the
decision already recorded in [`component_rendering.md`](component_rendering.md) section 5.1.

### 7.2 The serialize hook

`serialize_render` gains one extension hook: after the frames are built and
joined, the manager fires a core hook (working name **`on_serialize`**,
threaded on the HTML) carrying the root `CitryContext`, the joined HTML, the
strategy/position arguments, and the placeholder map (7.3). The
`dependencies` extension implements it to do everything in this section; the
core knows nothing about JS/CSS. A render with no component and no records
passes through untouched.

Inside its `on_serialize`, the extension:

1. Resolves each collected record into `Script`/`Style` lists (class scripts
   and variables scripts from the cache, `Dependencies` entries from the
   already-built `CitryDependencies`), categorized per strategy exactly as
   DJC does (`dependencies.py:1140-1222`): inline vs fetch-in-client vs
   mark-as-loaded.
2. Fires `Component.on_dependencies(scripts, styles)` per rendered class
   (ported) and then the extension-owned **`on_dependencies`** custom hook
   via `emit` (the first real custom hook, as planned in
   [`extensions.md`](extensions.md) section 9.2), letting other extensions
   filter/extend the final lists.
3. Dedupes first-seen by url-or-content, `Dependencies` entries before
   component scripts (DJC's order: a base's vendored lib loads before the
   component code that uses it).
4. Renders the tags and places them (7.3).

### 7.3 Placement: `<c-js>`/`<c-css>`, then default locations

The two built-in components finally land (names long reserved in the
registry):

```html
<head>
  <c-css />
</head>
<body>
  ...
  <c-js />
</body>
```

Each renders a **placeholder part**, a small core-known part type that rides
the existing serialize placeholder machinery (the same
`<template c-render-id="...">` mechanism child components use, with a
reserved key like `deps:js`). The serialize pass reports placeholder
positions to the `on_serialize` hook; the extension supplies the replacement
text. No regex over arbitrary HTML, which was DJC's `PLACEHOLDER_REGEX`
fragility.

When a placeholder is absent (per type), default placement falls back to
DJC's proven string pass over the final HTML: CSS before the first
`</head>`, JS before the last `</body>` (`_insert_js_css_to_default_locations`
ports nearly verbatim). This is the hybrid answer to the (i)-vs-(ii) fork
deferred in [`component_rendering.md`](component_rendering.md) section 5.2: structured placement
where the user gave us structure (the placeholder tags), one bounded string
scan as the fallback. If neither a placeholder nor the target tag exists
(content with no `<head>`), the tags are appended/prepended like DJC does
via `deps_position`.

Divergence from DJC, flagged: DJC duplicates all tags into *every*
placeholder occurrence (and documents that as a footgun). Citry fills the
first occurrence per type and leaves later ones empty.

### 7.4 The root-marker hook

The extension needs to add `data-ccss-<hash>` next to the `data-cid-<id>`
marker on a component's root elements (5.2). Rather than a JS/CSS-specific
field, the core exposes a generic per-component **extra root markers**
contribution point that serialize consults when building the root-marker
list (already plural for the `data-cid` marker). The dependencies extension
registers the CSS hash marker per instance; the future scoped-CSS extension
(#1230) is the second customer.

Built as two internal methods on `CitryContext`: `_add_root_markers(markers)`
(the extension calls it on the component's own context) and
`_get_root_markers()` (serialize reads it). They store the markers under the
citry-core `extra` namespace, `extra["citry"]["root_markers"]`. The
namespacing is the general rule for `extra`: it is shared across the render
tree, so each top-level key belongs to one owner (an extension uses its own
name; core-owned, multiply-contributed concepts use the `"citry"` key,
`EXTRA_CITRY_KEY`). The accessor methods keep the magic strings in one place
and out of both call sites. They are underscore-prefixed (not public API):
the only writer today is the built-in dependencies extension, so the
contract can firm up before it is promoted for third-party extensions.

---

## 8. Fragments and the client-side dependency manager

### 8.1 What a fragment is

A fragment is a render serialized with `deps_strategy="fragment"`: HTML meant
to be inserted into an already-loaded page (HTMX swap, Unpoly, Turbo,
`fetch` + `innerHTML`, jQuery `.load()`). Its dependencies cannot go into
`<head>`, so the output carries, after the HTML:

1. In the default and CSP warning modes, a **pre-loader** script: if
   `globalThis.Citry` is missing, inject a `<script src>` for the standard
   runtime, then remove itself. So those fragments work even on pages that
   were not rendered with the `document` strategy. Strict CSP fragments omit
   this executable bootstrap and require a matching CSP manager in the base
   document; without one, their inert manifest remains inactive.
2. An **exec manifest**: `<script type="application/json" data-citry>`
   containing (base64-armored, as in DJC, so content cannot break out of the
   script tag): the script/style tag descriptors to fetch, and the component
   calls to run. Because it is JSON, never executable JS, it is inert no
   matter how the fragment is inserted; the manager's MutationObserver picks
   it up even from `innerHTML` insertions, where ordinary scripts would not
   execute.

A component fragment may also carry inert ownership, Events, i18n, or other
framework manifests beside the exec manifest. Events parses this complete
package once. The ownership/morph planner first produces an unpublished set of
accepted incoming render IDs. Registered framework-manifest handlers then run
asynchronous `prepare` hooks against that owner filter; only after every prepare
succeeds does Events insert the fragment, commit the handlers, and release
component activation. Rollback runs in reverse order and leaves the old live
region unchanged when preparation fails. A handler therefore may load and
validate data before incoming Alpine directives or `$component` callbacks can
observe the fragment.

A page rendered with `document` strategy emits a mark-as-loaded manifest, so
a later fragment referencing the same component fetches nothing. Each manifest
also records `alpineRuntime` as `"standard"` or `"csp"`. The manager rejects a
different variant before adopting any fragment dependencies.

### 8.2 The client runtime

Citry ships its own browser runtime with the same responsibilities as DJC's
manager, renamed (`globalThis.Citry`, `data-citry`, `citry.min.js`):

- `registerComponent(classId, definition)` (the `$component` target),
  `registerComponentData(classId, hash, data)`, `callComponent(classId,
  componentId, varsHash, revision, mode)`; calls queue until their script and
  data arrive, then seed the graph-owned scope and optionally run against the
  elements matching `[data-cid-<componentId>]`.
  A class accepts exactly one component registration. A second registration
  throws an error naming the class and explaining that only one `$component`
  registration is allowed. The definition is either the bare callback or a
  config object with `init` and optional `props`. One registration represents
  one component definition, not a subscriber list. That is why the authoring
  name is `$component`, while `$onEvent` remains the listener API; `init`
  likewise names the component lifecycle phase instead of a generic handler.
  A graph-linked call is validated against its exact revision, render ID, and
  class before it enters the queue. Its callback payload also carries `graph`,
  a frozen route to the render record, logical client instance, and stable
  browser anchor.
- Two hooks for other extensions on the callback path (contracts pinned in
  `events.md` 12.5): `decorateContext(fn)` registers a decorator that adds
  members to the `$component` payload object in place just before the
  callback runs (and returns an unregister function), and the callback may
  return a cleanup function that runs before the callback fires again for
  the same instance id.
- `loadJs`/`loadCss` from JSON tag descriptors; `markScriptLoaded`/
  `isScriptLoaded` keyed by URL. URL stylesheets share one in-flight promise,
  settle on the browser's load or error event, and can retry after failure.
  Graph-linked component callbacks wait for their CSS and sequential
  JavaScript dependencies, so a callback never treats an inserted but still
  loading stylesheet as ready.
- One permanent MutationObserver handles graph and dependency manifests and
  fans batches out to extension providers. The same core owns
  `Citry.alpine`, whose permanent selector, init, magic, morph, and startup
  hooks dispatch through replaceable providers.
- `registerFrameworkManifest(name, handler)` registers an inert-manifest
  lifecycle with exact `match`, asynchronous `prepare`, synchronous `commit`,
  and reverse-order `rollback` hooks. Events uses the core private
  prepare/commit bridge for parsed fragments; ordinary streaming/document
  insertion still goes through the permanent observer. The i18n extension is
  the first consumer and uses the accepted-owner set to filter requirements
  during partial morph adoption.
- Planned, not yet in the runtime: a console warning for a stuck call (one
  whose component script or data never arrives). Today such a call just
  stays queued, silently.

The dependency manager ships inside the `citry` Python package as readable
package-data JavaScript. The pinned Alpine, morph, and Events source lives in
`packages/js/citry-client/`; its committed classic-IIFE build also ships as
Python package data. It is served by citry's own URL routes (9.2), so no
staticfiles-like setup is needed.
Improvement over DJC, flagged: in `document` mode, if no web integration is
mounted (no URL to `src` from), the runtime is **inlined** into the page
instead, so the zero-integration experience still works end to end;
fragments are the only feature that hard-requires mounting (8.3).

### 8.3 Operational requirements for fragments

Two, both diagnosed with explicit errors rather than silent breakage:

- **A mounted web integration** (section 9), because the manifest references
  script URLs. `serialize(deps_strategy="fragment")` raises with a pointed
  message when the instance has no mounted prefix.
- **A shared cache** (section 10) when running multiple processes: variables
  scripts are written by the rendering worker and may be served by another.
  Class-level scripts self-heal via lazy repopulation (4.3); variables
  scripts cannot. Documented as the production guidance: fragments + JS/CSS
  variables + multi-worker means configure a shared cache backend.

### 8.4 The component-instance lifecycle: teardown on removal and CSS cleanup

The manager already runs an instance's `$component` cleanup (8.2) when a
new call for the same instance id arrives, which covers a component that
re-renders under the same id. Three additions complete the lifecycle for
the cases that path never reaches. All three stay keyed by the component id
and the class id the manifests already carry; they need no new client
concept.

- **Teardown on removal.** An instance's cleanup also runs when its last
  `[data-cid-<id>]` element leaves the DOM. The manager keeps the set of
  instance ids whose callbacks have fired and, on DOM mutation and after
  each render, sweeps that set against the live DOM; an id with no live
  element left has its stored cleanups run and then discarded. The sweep
  catches both a real node removal and an in-place attribute swap (the same
  node losing its old `data-cid-<id>`), so a re-render that changes an
  instance's id retires the old id exactly once. This closes the case where
  a component's id never recurs: without the sweep its cleanup would stay
  queued and its resources (a chart, a map, an editor) would leak.
- **`Component.css` cleanup on the last instance of a class.** A
  class-level `Component.css` sheet is tagged
  `data-citry-css-class="<class>"` at emission (7, and the serializer note
  below). The manager removes that sheet when the last live instance of the
  class leaves the DOM, so a class that is gone from the page stops carrying
  its stylesheet. The per-render CSS-variables sheets (`data-ccss-<hash>`,
  5.2) are left in place for now; reclaiming them is out of scope here.

  **This cleanup must be deferred to a later task, not run the instant an
  instance retires.** A component that re-renders in place first retires its
  old instance id and only then registers the fresh one, so at the moment of
  retirement a solo instance of a class can momentarily look like the
  class's last, even though a same-class render is about to land. Running
  the check inline would drop the class's sheet on every such re-render.
  Deferring the check to a later task and re-counting the live instances then
  lets the arriving same-class render cancel it; a genuine last-instance
  departure still collects the sheet. Collection clears the stylesheet's
  loaded marker, so a later instance can fetch and apply the URL again.
- **Re-entrant flush safety.** When the manager flushes queued calls it
  snapshots and clears the pending list before iterating it, so a callback
  or context decorator that synchronously triggers another flush cannot
  re-run a call that is still in flight. This keeps a nested flush from
  firing a cleanup twice or recursing without bound.

Two matching additions belong to the serializer that emits the manifests
(7), not to this runtime: tagging each `Component.css` sheet with
`data-citry-css-class="<class>"` so the cleanup can find it, and emitting a
small instance-to-class presence record for instances that carry CSS but no
`$component` JS, so the manager can still count a class's live instances
when nothing else registers them. The record's shape, pinned by the WP4
amendment that consumes it: a top-level `cssInstances` key holding a list
of `[classId, componentId]` pairs, each element base64-armored like the
`calls` entries.

---

## 9. URLs and web-server integration

### 9.1 Routing surface: `URLRoute` ports into citry

DJC's `util/routing.py` is already framework-free; it ports as
`citry/util/routing.py` (`URLRoute`, `URLRouteHandler`, nested `children`).
This also resolves the TODO in [`extensions.md`](extensions.md) section 11:
**`Extension.urls`** becomes a real surface; the manager collects each
extension's routes, and `Citry.urls` exposes the combined table:

```
<prefix>/cache/<class_id>.<js|css>                # compatibility/current class script
<prefix>/cache/<class_id>.<content_hash>.<js|css> # immutable class version
<prefix>/cache/<class_id>.<vars_hash>.<js|css>    # variables script
<prefix>/citry.min.js                             # the client runtime
<prefix>/ext/<extension_name>/...                 # extension-provided routes
```

The first three are the `dependencies` extension's own `urls`; the `ext/`
namespace mirrors DJC's `urls.py` layout.

Handlers stay framework-neutral by keeping the logic out of them: the
endpoint body is a plain function on the extension,
`get_cached_script(class_id, script_type, vars_hash) -> (content, mime) |
None` (with the lazy repopulation from 4.3). Adapters wrap that in a
host-native view; the only host-specific code is request parsing and
response construction, a dozen lines each.

### 9.2 Adapters: generic ASGI/WSGI core, thin sugar per framework

The key observation from surveying hosts: one **ASGI sub-application** and
one **WSGI sub-application** cover almost every modern Python web server,
because all of them can mount a foreign app at a prefix. So citry ships:

- `citry.contrib.asgi`: `asgi_app(citry_instance)`, a tiny ASGI app routing
  the `Citry.urls` table. Mountable in Starlette/FastAPI (`app.mount`),
  Litestar, Quart, Django (ASGI), aiohttp (via adapter), etc.
- `citry.contrib.wsgi`: the WSGI twin, for Flask
  (`DispatcherMiddleware`), Pyramid, Bottle, classic Django WSGI.
- `citry.contrib.fastapi`: sugar producing an `APIRouter` plus a `mount()`
  convenience; this is also the integration the test suite uses (FastAPI's
  `TestClient` exercises the endpoints without a running server). FastAPI is
  a dev-only dependency; remember the mirrored-deps gotcha (root
  `pyproject.toml` dev extras).
- `citry.contrib.flask`: `mount()` wrapping the app's `wsgi_app` callable
  directly (no Flask import needed; works for anything exposing that
  attribute).
- `citry.contrib.django`: `urlpatterns(citry_instance)` converting
  `Citry.urls` into Django url patterns (a port of DJC's `routes_to_django`,
  `compat/django.py:132`), plus the Django cache wrapper (10.2). Citry owns
  this adapter itself rather than leaving it to django-components: how (and
  whether) django-components ends up living on top of citry is still open,
  and using plain citry with Django must not depend on that outcome. If
  django-components does become a citry wrapper, it reuses this adapter.

Adapter modules import their host packages lazily and are reachable as
extras (`pip install citry[fastapi]`). Further adapters (Litestar, aiohttp,
Tornado, Sanic) are by-demand; the ASGI/WSGI apps already serve them.

### 9.3 The mount contract and URL building

`get_script_url` needs to know where the routes are mounted (DJC used
Django's `reverse()`; citry has no global resolver). Each adapter's mount
step records the prefix on the instance:

```python
from citry.contrib.fastapi import mount
mount(fastapi_app, citry_instance, prefix="/citry")
```

`mount()` registers the routes *and* sets the instance's mounted prefix
(runtime instance state, like the file index; per #1413). URL building
formats `prefix + route path` (the ported `format_url` handles query/fragment
suffixes). Building a script URL with no mounted prefix raises with guidance.

Alternative considered and rejected: a `CitrySettings.url_prefix` field.
Settings are frozen at construction, but mounting happens later and
elsewhere; a setting would duplicate what the mount call already knows and
can silently disagree with reality. The adapter recording it at mount time
keeps one source of truth. (If a deployment needs URL building in a process
that never mounts, an explicit `citry_instance.set_mounted_prefix(...)`
escape hatch covers it; same mechanism.)

### 9.4 What local-file `Dependencies` entries become (new decision)

DJC `Media` entries leaned on Django staticfiles: an entry was a
static-relative name that `static()` turned into a URL. Citry dropped that
tier, so emission must decide what an entry that resolved to a local file
becomes:

- **`inline` (default)**: read the file (utf8) and emit
  `<style>...</style>` / `<script>...</script>`. Works with zero
  integration, no extra requests; the cost is page weight on repeats and no
  browser caching.
- **`serve`**: cache the file content (keyed by content hash) and emit a
  URL on the citry routes, e.g. `<prefix>/asset/<hash>.<ext>`. Browser
  caching and client-manager dedupe work across pages and fragments;
  requires a mounted integration.

The choice is an extension setting (`Dependencies` config or
`extensions_defaults["dependencies"]`), default `inline` so the
zero-configuration path is correct. URL entries (`http://`, `/...`) pass
through as before; `Script`/`Style` object entries say explicitly what they
are. Flagged as a divergence from DJC per migration principle 5: there is no
staticfiles tier to lean on, so citry serves or inlines the content itself.

### 9.5 Components served at a URL by Events

The built-in Events extension fills this slot with named per-component routes
and fragment-render actions over `Extension.urls`, as specified in
[`events.md`](events.md).

---

## 10. Cache integration

### 10.1 The protocol

A minimal, string-valued protocol in core (`citry/cache.py`), because a
second consumer is already planned (the component-render caching extension):

```python
class CitryCache(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ttl: float | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def has(self, key: str) -> bool: ...
```

String values keep every backend trivial (the dependency extension stores
JSON). Configured on settings, defaulting to a per-instance in-memory dict:

```python
app = Citry(cache=DiskCache("/var/cache/citry"))   # or "myproj.caches.RedisCitryCache"
```

`CitrySettings.cache: CitryCache | str | None = None`; `None` builds the
built-in `InMemoryCache` (unbounded by default, optional `max_entries` with
LRU eviction; dropping the least recently used entry keeps the memory cap
honest for vars-heavy workloads). Import strings are supported like
extension specs. `Citry.clear()` clears it.

This resolves the two ❓ rows in the migration doc (`cache.py`'s
`component_media_cache` and `app_settings.cache`): the concept returns as a
citry protocol; Django's `BaseCache` does not.

### 10.2 Backends worth shipping

| Backend | Where | Why |
|---|---|---|
| `InMemoryCache` | citry core | zero-config default; single-process dev |
| Django cache wrapper | `citry.contrib.django.DjangoCache` | adapts any configured Django cache to the protocol; Django users point at their existing `CACHES` entry (lives with the Django URL adapter, 9.2) |
| `diskcache` adapter | `citry.contrib.caches.DiskCache` | shared across workers on one host with no extra service; the best default answer to the multi-worker fragment requirement (8.3). Wraps a `diskcache.Cache` the user constructs |
| Redis adapter | `citry.contrib.caches.RedisCache` | multi-host deployments; wraps a redis-py client the user constructs |
| Memcached / cachetools / others | by demand | the protocol is four methods; users can write these in minutes, document the recipe |

The render-caching extension (extensions.md phasing item 3) will reuse the
same protocol and settings field when it lands; nothing here forecloses it.

### 10.3 Deployment version skew in one browser page

Content-addressed class-script keys and URLs make the server/cache boundary
version-safe: an old worker cannot overwrite the payload named by a new
worker's URL, and delayed serialization retains the exact rendering class.
This does not make component versions composable inside one live browser page.
The client manager registers callbacks and tracks CSS lifetime by stable
`class_id`, so a page that already loaded one version must not insert a
fragment produced by another deployed version of that same class.

Deployments serving fragments must prevent that version skew with worker
draining or version-sticky routing, or force a full-page reload when the
application version changes. Supporting mixed versions in one page would
require a separate client protocol where the content version participates in
callback, instance-call, and CSS ownership identity; that is outside this
cache-lifetime fix.

---

## 11. New and changed core surface (summary)

Everything the *core* gains, kept deliberately generic:

| Surface | Change |
|---|---|
| `CitrySettings` | `cache` field (10.1) |
| `Citry` | `class_id` reverse index; cache instance; mounted-prefix state + `urls` property (9.1, 9.3) |
| `Component` | `class_id`; `js_data()` / `css_data()` + `JsData` / `CssData`; `on_dependencies()` (5.1, 7.2) |
| `render_impl` | calls the three data methods together; `on_component_data` ctx gains `js_data`, `css_data`, and access to the render's `CitryContext` (6) |
| `extension.py` | `on_render_context_merge` core hook replacing the direct `_merge_dependencies` call; `on_serialize` core hook; `Extension.urls` (6, 7.2, 9.1) |
| `serialize.py` | placeholder part type + placeholder reporting; extra-root-markers lookup; fires `on_serialize` (7.3, 7.4) |
| `citry/cache.py` | `CitryCache` protocol + `InMemoryCache` (10.1) |
| `citry/util/routing.py` | `URLRoute`, `URLRouteHandler` (9.1) |
| `citry/contrib/` | `asgi`, `wsgi`, `fastapi`, `flask`, `django` adapters; later `diskcache`, `redis` (9.2, 10.2) |
| `citry/util/` | `format_url`, `serialize_css_var_value`, `get_import_path` ports |

Everything else (Script/Style, records, emission, manifests, endpoints'
logic, the client runtime contract) lives in the `dependencies` extension.

---

## 12. DJC surface tracking

| DJC surface | citry status | Note |
|---|---|---|
| `Script`/`Style`/`Dependency`, kinds, dedupe, to/from JSON | Ported | plus first-class use as `Dependencies` entries (3) |
| `_parse_dependency_from_string` / `TagAttrParser` | Dropped | entries are objects; DJC's own TODO_V1 (3) |
| `cache_component_js/css`, `cache_component_js_vars/css_vars`, key scheme | Ported | `citry:` prefix (4.2) |
| Eager class-creation caching (djc `extensions/dependencies.py`) | Replaced | lazy endpoint repopulation (4.3), flagged divergence |
| `evict_component_scripts` | Ported | folded into the existing `on_files_reset` handler (4.3) |
| `get_js_data` / `get_css_data` / `JsData` / `CssData` | Ported (reshaped) | `js_data(kwargs, slots)` / `css_data(kwargs, slots)` (5.1) |
| `$component` transform | Ported | target is `Citry.manager.registerComponent` (5.2) |
| CSS vars stylesheet + `data-djc-css-<hash>` | Ported | `data-ccss-<hash>` via the root-marker hook (5.2, 7.4) |
| `set_component_attrs_for_js_and_css` | Superseded | `data-cid-<id>` already stamped at serialize; CSS marker rides the same pass |
| `<!-- _RENDERED -->` comments + regex extraction | Superseded | `DependencyRecord`s in `CitryContext.extra` (6) |
| `render_dependencies()` six strategies | Reshaped | four strategies + `deps_position`, implementing DJC's own TODO (7.1) |
| "ignore when nested" default | Superseded | structural: deps merge upward; placement only at the explicit serialize (2) |
| `{% component_js/css_dependencies %}` | Ported | `<c-js>` / `<c-css>` built-ins; first occurrence wins (7.3), flagged divergence |
| `_insert_js_css_to_default_locations` | Ported | the fallback half of hybrid placement (7.3) |
| `OnDependenciesContext` / `extensions.on_dependencies` | Ported (reshaped) | extension-owned `emit` hook, not core (7.2) |
| `Component.on_dependencies` | Ported | (7.2) |
| Exec script JSON manifest + base64 armor | Ported | `data-citry` attribute (8.1) |
| Client manager (`django_components.min.js`) | Rewritten | `packages/js/citry-client`, `globalThis.Citry` (8.2) |
| Manager served via Django static | Replaced | served by citry routes; inlined when nothing is mounted (8.2) |
| `cached_script_view` + `urlpatterns` | Ported (split) | neutral endpoint logic + host adapters (9.1, 9.2) |
| `URLRoute` / `URLRouteHandler` | Ported | `citry/util/routing.py`; `Extension.urls` lands (9.1) |
| `routes_to_django` | Ported | `citry.contrib.django`, so plain citry works with Django without django-components (9.2) |
| `Media` entries via staticfiles URLs | Replaced | inline-or-serve decision (9.4), flagged divergence |
| `Component.View` / `get_component_url` | Built (reshaped) | named handler routes and URL building ship through Events over `Extension.urls` (9.5; [`events.md`](events.md)) |
| `get_component_media_cache` / `COMPONENTS.cache` | Replaced | `CitryCache` protocol + `CitrySettings.cache` (10) |
| `hash_comp_cls` / `get_component_by_class_id` | Ported | `class_id` + per-instance reverse index (4.1), resolves the ❓ rows |
| `format_url`, `serialize_css_var_value`, `get_import_path` | Ported | with this package |

---

## 13. Layout

- `citry/extensions/dependencies.py` grows into a package
  `citry/extensions/dependencies/`:
  - `__init__.py`: the extension (existing loading half + new hooks)
  - `types.py`: `Script`, `Style`, `DependencyRecord`
  - `scripts.py`: caching, vars hashing, `$component` transform, CSS vars
    stylesheet generation
  - `emission.py`: record resolution, categorization, dedupe, manifests,
    placement
  - `routes.py`: the extension's `URLRoute`s + endpoint logic
  - `client/`: the vendored built `citry.min.js` (package data)
- `packages/js/citry-client/`: the runtime's TypeScript source + build.
- Core files per the table in section 11.
- Tests: `tests/test_deps.py` (extend), `tests/test_deps_emission.py`,
  `tests/test_deps_fragments.py`, `tests/test_contrib_fastapi.py`,
  `tests/test_cache.py`.

---

## 14. Interactions

- **Const folding** ([`component_constness.md`](component_constness.md)): unaffected by design;
  a folded component boundary still mints a fresh render and re-records its
  dependencies each render (the component_rendering.md section 7 agreement). Variables
  hashing happens per render, after folding.
- **Deferred rendering**: the queue is where `on_render_context_merge` fires; record
  order follows queue order (6).
- **Render caching (#1650)**: the detached `CachedRenderArtifact` in
  [`caching.md`](caching.md) stores stable class IDs and canonical dependency
  data, not live records or rendered tags. Replay mints fresh component IDs and
  rebuilds dependency records for the current page (6).
- **Error fallback / on_render**: replacement output can reuse the original
  context, whose record collection may still contain replaced descendants.
  Render-cache export therefore filters dependencies to final active reachable
  render IDs as specified in [`caching.md`](caching.md), rather than copying the
  context collection.
- **Streaming (#1337)**: still held off; the manifest-based fragment path is
  the likely streaming delivery mechanism later (deps at the component's own
  location), and nothing here forecloses it.
- **Scoped CSS (#1230)**: becomes feasible on two hooks built here, the
  root-marker lookup (7.4) and `on_template_compiled`; not part of this
  package.

---

## 15. Open questions

- ~~The exact shape of the root-marker and placeholder hooks~~ decided:
  `CitryContext._add_root_markers` / `_get_root_markers` (internal), storing
  under the namespaced `extra["citry"]["root_markers"]` (7.4), and a core `Placeholder`
  part riding the serializer's template-tag machinery, reported to
  `on_serialize` as an id-to-exact-text map (7.3).
- ~~How `on_component_data` exposes the render's `CitryContext`~~ decided:
  the hook context carries a `context` field (6).
- ~~Whether the `document` manifest should always be emitted~~ decided: the
  manifest and the runtime are emitted when a rendered component used
  `$component`, or when a mounted page carries component assets a later
  fragment must dedup against (so `markLoaded` can list their cache URLs).
- ~~Naming~~ settled at implementation: `data-ccss-<hash>` for the CSS vars
  marker, `on_serialize` for the hook.
- ~~Whether `serve` mode fingerprints URLs~~ decided yes: the asset URL *is*
  the content hash (`asset/<hash>.<ext>`), so a changed file gets a new URL
  and the old one can be cached forever.

---

## 16. Phasing

1. **Core plumbing - built.** `class_id` + reverse index; `CitryCache`
   protocol, `InMemoryCache`, `CitrySettings.cache`; `Script`/`Style` types
   (accepted as `Dependencies` entries); `js_data`/`css_data` +
   `JsData`/`CssData` + the `on_component_data` context additions. The
   render-context access for `on_component_data` (section 15) was deferred
   to phase 2, where its consumer (record collection) lands.
2. **Collection + document emission - built.** `DependencyRecord`s into
   `extra`; the `on_render_context_merge` hook (the `_merge_dependencies` hook now
   only fires it); the `on_serialize` hook + the `Placeholder` part type;
   `<c-js>`/`<c-css>` built-ins; strategies `document`/`simple`/`ignore`
   with positions; default-location insertion; `Component.on_dependencies` +
   the `on_dependencies` emit hook (the first real custom hook). Full pages
   with inlined JS/CSS work with no integration mounted. Decisions made in
   code: the `on_component_data` context carries the render's `CitryContext`
   (the 15-series open question); placeholders ride the serializer's
   existing `<template c-render-id>` machinery under unique keys, and the
   hook receives an id-to-exact-text map; resolved local-file `Dependencies`
   entries are `Path` objects (so emission can tell a file from a URL
   string) and are inlined, per the 9.4 default.
3. **Client runtime + variables - built.** Vars scripts and hashing;
   `$component`; `data-ccss-` markers via the root-marker hook; the
   document manifest (mark-as-loaded + component calls); runtime inlining.
   Decisions made in code: the root-marker hook is the internal
   `CitryContext._add_root_markers` / `_get_root_markers`, storing under the
   namespaced `extra["citry"]["root_markers"]`, read by serialization next
   to the `data-cid` marker; the manifest (and the
   runtime with it) is emitted when a rendered component used `$component`, or
   when a mounted page carries component assets a later fragment must dedup
   against; `document` vs `simple` now genuinely differ: `simple` is
   the no-JS-runtime mode, so JS variables and component calls are
   document-only while CSS variables (pure CSS) work under both; the runtime
   core manager ships as readable plain JS package data
   (`citry/extensions/dependencies/client/citry.js`); the pinned Alpine,
   Events, CSP, and i18n runtimes are built and checked from
   `packages/js/citry-client` TypeScript sources.
4. **URLs + fragments - built.** `URLRoute` port + `Extension.urls` +
   `Citry.urls`; endpoint logic with lazy repopulation; ASGI/WSGI apps +
   FastAPI adapter (used by the tests) + mount contract; `fragment` strategy
   end to end. Decisions made in code: route paths use `{param}` syntax
   matched first-wins by a tiny built-in router, with an explicit `methods`
   field on `URLRoute` (deviation from DJC, which left method checks to
   views); every extension instance carries a `citry` back-reference (set by
   the manager), which is how route handlers reach engine state; built-in
   extensions' routes mount at the prefix root, user extensions' under
   `ext/<name>/`; a mounted `document` page serves the runtime by URL and
   marks the inlined scripts' cache URLs as loaded, so later fragments fetch
   nothing they already have; a fragment whose components carry no assets
   needs no mounted integration; local-file `Dependencies` entries ride
   fragments as inline tag descriptors (pre-rendered `__html__` entries are
   rejected loudly there, since an opaque tag string cannot become a
   descriptor). The 9.4 `serve` mode for local files moves to phase 5.
5. **Breadth - built** (except as noted). `citry.contrib.flask.mount`
   (wraps the app's `wsgi_app`, needs no Flask import);
   `citry.contrib.django` (`urlpatterns()` over `Citry.urls`, using
   `re_path` where two parameters share a path segment, plus the
   `DjangoCache` wrapper); the cache adapters as
   `citry.contrib.caches.RedisCache` / `DiskCache` (one module, wrapping
   client objects the user constructs, so citry imports nothing from the
   host packages); the `serve` mode for local-file entries (9.4): a
   `local_files` setting on the `Dependencies` config (per component or via
   `extensions_defaults`), emitting fingerprinted content-hash URLs on the
   new `asset/{file_name}` endpoint, falling back to inline when unmounted.
   The TypeScript/minification build and user-facing fragment/production docs
   now ship. Named component event URLs ship through Events (9.5).
