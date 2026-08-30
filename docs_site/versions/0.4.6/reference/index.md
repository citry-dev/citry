---
title: API reference
url: https://citry.dev/v/0.4.6/reference/
description: "The citry public API, by area."
---
# API reference

The citry public API, by area.

- [Component](/v/0.4.6/reference/component/) - The base class every component subclasses.
- [Component introspection](/v/0.4.6/reference/component-introspection/) - Frozen metadata records for component catalogs, schemas, assets, and extensions.
- [Component graph](/v/0.4.6/reference/component-graph/) - Authored component dependencies, reverse references, source locations, and partial-analysis problems.
- [Component libraries](/v/0.4.6/reference/component-libraries/) - Engine-neutral component definitions, explicit manifests, and per-Citry installations.
- [Citry instance and config](/v/0.4.6/reference/citry/) - The `Citry` instance that scopes components, settings, and caches.
- [Rendering](/v/0.4.6/reference/rendering/) - The render pipeline, its output structs, and Citry's trusted-HTML marker. `citry.Markup` is exactly [`markupsafe.Markup`](https://markupsafe.palletsprojects.com/en/stable/escaping/#markupsafe.Markup). `Markup(value)` trusts the complete value without sanitizing or validating anything.
- [Slots](/v/0.4.6/reference/slots/) - The slot value and fill types.
- [Nodes](/v/0.4.6/reference/nodes/) - The runtime node classes the compiled template instantiates.
- [Template analysis](/v/0.4.6/reference/template-analysis/) - Discovery, analysis, source mapping, and formatting for Python-embedded templates.
- [Extensions](/v/0.4.6/reference/extensions/) - The plugin system: the extension base, its commands, and the hook context objects.
- [Dependencies](/v/0.4.6/reference/dependencies/) - The JS/CSS dependency types collected and placed at serialize time, and the built-in `citry.ext.dependencies` extension that owns them.
- [Render cache keys](/v/0.4.6/reference/cache-keys/) - Exact key helpers and errors for component and named-fragment render caches.
- [Internationalization](/v/0.4.6/reference/internationalization/) - Locale contexts, messages, named formats, and strict localized-input parsers.
- [Events](/v/0.4.6/reference/events/) - Event handlers declared on components: the `class Events:` contract, the typed base for it, and the built-in `citry.ext.events` extension that owns it.
- [Browser APIs](/v/0.4.6/reference/browser-apis/) - Component JavaScript, Citry's Alpine magics, and page-wide browser methods.
- [HTML attributes](/v/0.4.6/reference/attributes/) - Helpers for Vue-like class/style merging on HTML elements.
- [Web integration](/v/0.4.6/reference/web/) - The route table a web framework mounts, and the request/response types handlers use (see `citry.contrib`).
- [Contrib integrations](/v/0.4.6/reference/contrib/) - Adapters mounting citry into web frameworks, and cache adapters for shared stores (the `citry.contrib.<name>` modules).
- [Built-in tags](/v/0.4.6/reference/builtins/) - The built-in `<c-*>` tags every component can use.
