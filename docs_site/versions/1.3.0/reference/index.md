---
title: API reference
url: https://citry.dev/v/1.3.0/reference/
description: "The citry public API, by area."
---
# API reference

The citry public API, by area.

- [Component](/v/1.3.0/reference/component/) - The base class every component subclasses, and the warning Citry emits when a subclass's nested data class drops its parent's fields.
- [Component introspection](/v/1.3.0/reference/component-introspection/) - Frozen metadata records for component catalogs, schemas, assets, and extensions.
- [Component graph](/v/1.3.0/reference/component-graph/) - Authored component dependencies, reverse references, source locations, and partial-analysis problems. Experimental, so these classes may change in a minor release.
- [Component libraries](/v/1.3.0/reference/component-libraries/) - Engine-neutral component definitions, explicit manifests, and per-Citry installations.
- [Citry instance and config](/v/1.3.0/reference/citry/) - The `Citry` instance that scopes components, settings, and caches, and the warning class for deprecated features.
- [Rendering](/v/1.3.0/reference/rendering/) - The render pipeline, its output structs, Citry's trusted-HTML marker, and the `Secret` marker that keeps a value out of the data sent to the browser. `citry.Markup` is exactly [`markupsafe.Markup`](https://markupsafe.palletsprojects.com/en/stable/escaping/#markupsafe.Markup). `Markup(value)` trusts the complete value without sanitizing or validating anything. `safe_eval` runs an expression in the sandbox, `unsafe` marks a function that sandboxed expressions must not call, and `SecurityError` is what a blocked access raises. Four parts of this page are experimental and may change in a minor release: `RenderFrame`; the asset tags that `deps_position="separate"` returns (`SerializedAssets`, `SerializedAssetEntry`, the asset fields of `SerializedRender`, `CitryRender.needs_browser_runtime()`, `combine_assets()`, and `OutsideSlotContentError`); the API for embedding Citry tags in another template engine (`CompiledBody`, `render_compiled_body` and `collect_compiled_body_fills`); and `page_nonce_from_headers()`, which reads the page's CSP nonce from a request, with the `PAGE_NONCE_HEADER` name it reads.
- [Slots](/v/1.3.0/reference/slots/) - The slot value and fill types.
- [Nodes](/v/1.3.0/reference/nodes/) - The runtime node classes the compiled template instantiates.
- [Template analysis](/v/1.3.0/reference/template-analysis/) - Discovery, analysis, source mapping, and formatting for Python-embedded templates. Everything here except `LspPosition` and `LspRange` is experimental, so it may change in a minor release.
- [Preview](/v/1.3.0/reference/preview/) - Component examples, layouts, and metadata for command-owned preview pages. Experimental, so these names and the `citry ext run preview` commands may change in a minor release.
- [Extensions](/v/1.3.0/reference/extensions/) - The plugin system: the extension base, its commands, and the hook context objects. Some hooks and types on this page are experimental and may change in a minor release; each entry says so. The experimental parts are the API for embedding Citry tags in another template engine, the `"payload"` render cache mode, `browser_plugin()`, and `prepare_browser_render()`.
- [Dependencies](/v/1.3.0/reference/dependencies/) - The JS/CSS dependency types collected and placed at serialize time, and the built-in `citry.ext.dependencies` extension that owns them.
- [Render cache keys](/v/1.3.0/reference/cache-keys/) - Exact key helpers and errors for component and named-fragment render caches.
- [Internationalization](/v/1.3.0/reference/internationalization/) - Locale contexts, messages, named formats, and strict localized-input parsers.
- [Events](/v/1.3.0/reference/events/) - Event handlers declared on components: the `class Events:` contract, the typed base for it, and the built-in `citry.ext.events` extension that owns it.
- [Browser APIs](/v/1.3.0/reference/browser-apis/) - Component JavaScript, Vue integration, page-wide settings, and component Events helpers.
- [HTML attributes](/v/1.3.0/reference/attributes/) - Helpers for Vue-like class/style merging on HTML elements, and the error raised when Python data sets an attribute name that Vue reads as code.
- [Web integration](/v/1.3.0/reference/web/) - The route table a web framework mounts, and the request/response types handlers use (see `citry.contrib`).
- [Hot reload](/v/1.3.0/reference/hot-reload/) - The `citry.reload` module, which watches component files and reloads them in place while you develop (see the [hot reload guide](/v/1.3.0/guides/hot-reload/)).
- [Contrib integrations](/v/1.3.0/reference/contrib/) - Adapters mounting citry into web frameworks, and cache adapters for shared stores (the `citry.contrib.<name>` modules).
- [Built-in tags](/v/1.3.0/reference/builtins/) - The built-in `<c-*>` tags every component can use.
