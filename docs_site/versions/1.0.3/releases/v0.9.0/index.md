---
title: v0.9.0
url: https://citry.dev/v/1.0.3/releases/v0.9.0/
description: "What changed in citry v0.9.0."
---
# v0.9.0

Citry 0.9.0 states the order in which a page's scripts and
`onServerRender` callbacks run, and what happens when one of them fails;
see
[When scripts run](https://citry.dev/advanced/js-and-css-dependencies/#when-scripts-run).
A component script that throws now keeps the page's Vue app from
starting, and a third-party script that fails to load, such as one an ad
blocker refuses, no longer keeps the Vue app from starting on a page
served through a web framework integration. Pages now link Citry's
runtimes by a URL that holds a hash of the file, so a deploy needs the
cache steps in the upgrade notes. Several changes can break code that
worked: `Citry(...)`, `CitrySettings`, `LintSettings` and `URLRoute`
take their options by name, `URLRoute` no longer takes `extra=`, a
`URLRoute` path with no text between two parameters, such as
`"{year}{month}"`, raises an error when your app starts, a component
cannot be named `lazy`, `teleport`, `transition` or `suspense`, a
template whose `v-for` alias or `v-slot` pattern starts with `$`, `_` or
`citry` fails to load, and `Events` classes can no longer set `_topics`.
Citry now checks event data on threads of its own and allows 64 levels
of nesting. Upgrade citry-lsp to 0.4.0 or later, and citry-ui to 0.5.0
or later if you use it, at the same time. Citry imports on Pyodide
again. The upgrade notes below list what can fail or change.

## Upgrading from 0.8.x

- **Put text between two route parameters:** a `URLRoute` path such as
  `"{year}{month}"` now raises `ValueError` naming the route when your
  app starts, in `asgi_app()`, `wsgi_app()`, the Flask and FastAPI
  `mount()`, and Django's `urlpatterns()`. Before, it matched, and the
  first parameter took all but the last character. Citry cannot tell
  where one value ends and the next begins, so write `"{year}-{month}"`
  or another separator.
  ([details](https://citry.dev/advanced/extensions/#separate-two-parameters))
- The same error comes from a parent route whose path ends in a
  parameter and a child whose path starts with one, such as
  `"files/{name}"` with `"{ext}"`, because a child's path is added to its
  parent's as plain text. The message names both routes. End the
  parent's path with `/`, or start the child's path with text such as
  `.`.
- Routes with text between their parameters, such as
  `"files/{name}.{ext}"`, match the same paths with the same values as
  before.
- **A component script that throws now keeps the Vue app from
  starting:** if a component's `js` throws while it runs, or has a
  syntax error, the page's Vue app does not start, and the console names
  the component. Before, the page usually started while the error showed
  in the console. Fix the script, or catch the error inside it when it
  is expected, for example when an optional browser feature is missing.
  The page's `error` event still receives the original error.
- **A third-party script that fails to load no longer stops the page:**
  on a page served through a web framework integration, a dependency
  file or extension script from another origin that fails to load (an ad
  blocker, a content security policy, a failed integrity check, or a
  network error) is skipped with a console warning, and the app starts.
  Citry cannot tell your own CDN from a third party, so this holds for
  every file from another origin. Serve a file the page must not run
  without, such as a consent manager, from your own origin.
- **`onServerRender` callbacks after a server render now run children
  before their parent, and siblings in the order they first mounted,**
  as on the first mount. Before, they ran in the order the server's
  response listed the components, which often put the parent first. If
  your code relied on that, check it against the new order. citry-ui
  0.4.0 and earlier relied on the old order, so upgrade citry-ui to
  0.5.0 or later.
- **A callback that throws on the first mount now stops the callbacks
  after it,** as it already did after a server render. Catch an error
  you expect inside the callback.
- **Extension scripts that register a browser plugin now run before
  component scripts on every interactive page.** Before, a page written
  without a web framework integration ran them after. If you write an extension
  whose plugin script reads a value a component script sets, read it
  later, for example inside a callback.
- **Citry runs your validators, State serializers and `__post_init__`
  methods on its own threads:** this covers event data and State, and
  your request thread waits for them. They can read the request's
  context variables, but a value stored with `threading.local` is unset
  there, and a context variable a validator sets does not reach your
  handler. A validator that uses Django's database gets a separate
  connection, which stays open while the thread lives and does not see
  rows the request wrote in an unfinished transaction. A write from it
  waits for that transaction. A validator must not wait for a lock that
  the request's thread holds, or, under gevent or eventlet, for anything
  another greenlet holds
  ([details](https://citry.dev/security/#check-event-data)).
- **Raise the stack size you set for request threads to 2 MiB:** if you
  followed the 0.8.0 advice and call `threading.stack_size(1024 * 1024)`
  before your server starts its threads, change it to
  `threading.stack_size(2 * 1024 * 1024)`. Your handler, and a Pydantic
  `Kwargs`, `Slots` or `TemplateData` class that a render builds from
  event data, still get the checked data on your server's threads, and
  code of yours that walks it level by level needs the room
  ([details](https://citry.dev/security/#check-event-data)).
- **A page can outlive the runtime it links:** pages now link Citry's
  runtime by a URL that changes with each release (see Changed). When
  a page rendered before a deploy names a runtime that neither the
  browser nor a shared cache still holds, the page keeps its server
  HTML, its interactive components do not start, and the browser
  console shows `Citry could not load its runtime: <url>`. Reloading
  the page fixes it, unless a cache serves the whole page (next item).
- **Clear whole-page caches when you deploy, and give every worker the
  same cache during rolling deploys:** a page cached before a deploy
  names the old runtime's URL. During a rolling deploy, give every
  worker the same cache backend, or use sticky sessions. See
  [Deploy a Citry upgrade](https://citry.dev/advanced/web-frameworks/#deploy-a-new-version).
- **Fixed app ids get a new script hash:** if you set `id_generator` so
  the script that starts a page's Vue app has the same CSP hash on every
  response, that hash now also changes when Citry's runtime file
  changes. Take the hashes from `csp_script_hashes`, as before.
- **Interactive renders now write to your cache:** with a cache backend
  set, every render that links the runtime by URL, fragments included,
  makes sure the runtime is stored there, checking at most once a minute
  per process. A cache backend error therefore fails the render. Citry
  calls the backend's `set` with `ttl=` as a keyword argument, so a custom
  backend's `set` must accept it under that name.
- **Rename a component called `lazy`, `teleport`, `transition` or
  `suspense`:** Citry keeps these names for built-in tags it plans to
  add, so a component class named `Teleport`, or one given one of these
  names through `name` or `register()`, now raises `AlreadyRegistered`
  when it is defined or registered.
  A component library that contains one raises `ValueError`. Rename it,
  for example to `TeleportTarget`, and update the tags in your
  templates. Longer names that contain one of these words, such as
  `LazyCard`, still work
  ([reserved names](https://citry.dev/reference/builtins/#reserved-names)).
- **Event data for a plain class or dataclass now has the 64-level
  nesting limit:** when an event's `data` class is a plain class, a
  dataclass or a Pydantic dataclass, data that nests more than 64 of its
  objects inside each other now gets a 422 that says the data is nested
  too deeply, as a Pydantic model's data already did. Before, Citry's
  own check of such a class did not count levels. If valid data nests
  this deeply, flatten the data.
- **Pass the options of `Citry(...)`, `CitrySettings`, `LintSettings`
  and `URLRoute` by name:** these now raise `TypeError` for an argument
  passed by position, so an option added later cannot change what your
  call means. `URLRoute` still takes the path and the handler by
  position.

    ```python
    Citry(extensions=[MyExtension])  # not Citry([MyExtension])
    # the path and the handler stay positional
    URLRoute("status", status, name="status")
    ```

- **Remove `extra=` from `URLRoute`:** Citry never read it, and passing it
  now raises `TypeError`. If you used it to carry your own data, keep
  that data where the handler can reach it, for example in a closure.
- **Delete `_topics` from your `Events` classes and from
  `extensions_defaults["events"]`:** Citry did not use it. A component
  that sets it now raises `ValueError` when the class is defined, and
  `Citry(...)` raises it for the default.
- **A template with a reserved name in `v-for` or `v-slot` fails to
  load:** Citry now refuses a `v-for` alias, or a `v-slot` or `#name`
  pattern on a Vue component or `<template>`, that uses a name starting
  with `$`, `_`, or `citry`, as in
  `v-for="(_, index) in items"`. Citry keeps those prefixes for the
  values it gives the template, such as `$i18n`, and such a name could
  hide one. Rename it; the error suggests a name, and `citry check` and
  the editor report the same error.
- **`<c-slot>` and `<c-fill>` raise `VueCodeError` for a Vue-code
  `c-bind` key:** a `c-bind` key such as `":row"` or `"v-slot"` on
  `<c-slot>` or `<c-fill>` now raises `VueCodeError`, the error that
  elements and component tags already raise for such a key, instead of
  `RuntimeError`. The render failed before too. Code that catches
  `RuntimeError` around it must also catch `TypeError`, which
  `VueCodeError` subclasses.
- **`<c-slot>` raises `VueCodeError` for two more bindings:** it used to
  pass them to the fill as slot data, and now refuses a `$c-tr` binding
  written as a `c-` attribute (`<c-slot c-$c-tr:x="y" />`) and a
  `c-bind` key that is just `"."`. Write a `$c-tr` binding on an HTML
  element, and remove a `"."` key from the `c-bind` mapping.
- **Upgrade citry-lsp and citry-ui together with this release:**
  citry-lsp 0.3.0 and earlier cannot read the editor data this release
  writes, so for every project, even one without i18n, the editor falls
  back to checking template syntax only. Install citry-lsp 0.4.0 or
  later. citry-ui 0.4.0 and earlier break some overlays under the new
  `onServerRender` order: the date and time pickers, nested popovers,
  nested dialogs and drawers, and `CAccordion`. If you use citry-ui,
  install 0.5.0 or later.

## Added

- `Citry.runtime_url()` returns the URL of Citry's browser runtime, for a
  page whose HTML you write yourself. See
  [Link the runtime by hand](https://citry.dev/advanced/web-frameworks/#link-the-runtime-by-hand).
- You can now import `safe_eval`, which runs an expression in Citry's
  sandbox, and `unsafe`, which marks a function that sandboxed
  expressions must not call, from `citry`
  ([Sandbox template code](https://citry.dev/security/#sandbox-python-template-expressions)).
  The `citry_core.safe_eval` import still works.
- You can turn Citry's deprecation warnings into test errors with
  `CitryDeprecationWarning`, the class Citry will use for every
  deprecated feature (none is deprecated today): add `"error::citry.CitryDeprecationWarning"` to pytest's
  `filterwarnings`.
- The hot reload API in `citry.reload` (`watch`, `WatchHandle`,
  `FileWatcher`, `WatchfilesWatcher`, `WatchdogWatcher` and
  `PollingWatcher`) is now public, listed in `__all__`, and documented
  in the API reference.
- `I18nExtension`, the type of the object
  `app.extensions.get_extension("i18n")` returns, is now in
  `citry.ext.i18n.__all__`, so it is public API.

## Changed

- `Citry.inspect_component_graph()` and `ComponentGraph` are now marked
  experimental: they and their JSON output may change in a minor release.
- A `URLRoute` path that uses one parameter name twice, such as
  `"{id}/{id}"`, now raises `ValueError` naming the route when your app
  starts. Before, it raised a regular expression error: under Django
  when `urlpatterns()` ran, and under ASGI and WSGI on every request that
  reached the route.
  ([details](https://citry.dev/advanced/extensions/#separate-two-parameters))
- `URLRoute(dotless_params=...)` now raises `TypeError` when the route is
  built unless it is a `frozenset` of parameter names. Before, a set or a
  list failed when Django's `urlpatterns()` ran, or on the first request
  under ASGI, WSGI, Flask and FastAPI.
- Django's `reverse()` for a Citry route now raises `NoReverseMatch` for
  a value that is empty, holds a `/`, or holds a `.` for a parameter in
  `dotless_params`. Before, it could return a URL that the route splits
  into different values, such as `cache/a.b.js` for `class_id="a.b"`,
  which Citry reads as `class_id="a"`.
- **Event data may nest 64 levels, and the check no longer depends on
  your threads' stack size:** Citry now checks event data, browser
  writes to State, and State read back from its token on threads of its
  own, each with a 16 MiB stack. The nesting limit rises from 32 to 64
  levels, so a tree whose node classes have a discriminator can nest
  about 60 levels.

  Your handler still gets the checked data on your server's own thread,
  so give request threads at least 2 MiB of stack with
  `threading.stack_size()`. Lists and dicts do not count toward the
  64-level limit, and on Python 3.11, calling `model_dump()` on 196
  nested lists in a `JsonValue` field ended the process with 1 MiB of
  stack and passed with 2 MiB.
  The official `python:3.12-alpine` image gives a Python thread about
  1 MiB (measured on arm64), so set a larger size there. macOS gives a
  thread that Python does not start only 512 KiB, against 16 MiB for
  one that it starts.

  Where Python cannot start threads, as in Pyodide (Python in the
  browser), the limit stays at 32
  ([details](https://citry.dev/security/#check-event-data)).
- Pages now link Citry's runtimes by a URL that holds a hash of the
  file, such as `/citry/citry.<hash>.js`, so the browser keeps them
  between page loads instead of downloading them on every page. The URL
  changes when a release changes the file. The stable URLs, such as
  `/citry/citry.js`, keep working.
- A `404` for a missing Events definition or stylesheet, or (on FastAPI,
  Flask, ASGI, and WSGI) for a path under Citry's prefix that matches no
  route, now sends `Cache-Control: no-store`, so a CDN does not keep a
  miss that another worker could answer.
- These are now marked experimental, so the 1.0.0 stability promise
  will not cover them and they may change in a minor release. Their
  behavior does not change in this release:
    - the template analysis API that `citry check`, `citry format` and
      the `citry-lsp` language server use (except `LspPosition` and
      `LspRange`), and `Citry.template_analysis()`;
    - embedding Citry tags in another template engine: `CompiledBody`,
      `render_compiled_body`, `collect_compiled_body_fills`, the
      `Foreign*` types, and the hooks `on_template_foreign_spans` and
      `on_template_foreign_compiled`;
    - `citry.ext.preview` and the `citry ext run preview` commands;
    - the `"payload"` render cache mode;
    - `Extension.browser_plugin()` and
      `Extension.prepare_browser_render()`;
    - the `on_event`, `on_event_result` and `on_event_error` hooks that
      the Events extension calls on your extension;
    - the `event_result_resolvers` and `event_payload_codecs` settings;
    - `RenderFrame` and `CitryRender.frame`.
- The `on_*` methods of `ExtensionManager` (and
  `has_attrs_resolved_hook`) are now documented as internal: Citry calls
  them itself, and they may change in any release. To react to a hook,
  implement it on your `Extension` subclass.

## Fixes

- Django's `reverse()` for a Citry route with several parameters in one
  path segment, such as `{name}-{version}`, now takes time in step with
  the length of the values you pass.
- **Citry imports on Pyodide again:** Citry 0.8.0 failed to import on
  Pyodide with `AttributeError: module 'time' has no attribute
  'thread_time'`, because the Events limit on CPU time read a clock that
  Pyodide does not have. Citry now uses the CPU time of the thread that
  runs the check where the platform has it, then the CPU time of the
  process, then the wall clock. Linux, macOS and Windows keep using the
  thread's CPU time.
- **Writing State back for the page now runs on Citry's own threads:**
  a State with `validate_assignment=True` checks each value again when
  Citry writes it back, so a State value nested about 196 levels deep no
  longer ends the process on a server whose threads have 1 MiB of stack
  or less.
- When an event handler leaves State nested deeper than Pydantic can
  write as JSON, the error now says the State nests too deeply instead
  of naming only `ValueError`. Rendering such a State raises the same
  message. Pydantic's limit is lower on Windows, PyPy and Pyodide than
  on Linux and macOS.
- A browser write to a Pydantic model State that nests deeper than
  Pydantic can write as JSON now gets a 422 "nested too deeply" field
  error before the event handler runs. A call whose State token holds
  a State nested deeper than this server's Pydantic or Python can write
  now answers `stale_state`, and the browser offers a reload.
- A `c-bind` key that is a `str` subclass with its own `startswith` or
  `__eq__` can no longer slip past the checks on `<c-slot>`, `<c-fill>`,
  and component tags.
- `citry preview` no longer fails with a Vue compile error at
  `<!doctype>` for components that use Events. The preview now renders
  them, and their event handlers work. The same applies when a template
  places a whole-page template through a variable, such as `{{ page }}`.
- `<c-cache>` around an element with a `$c-tr` attribute (the one that
  updates the element's text when the language changes) no longer breaks
  the page when a request is served from the cache. The browser console
  showed `binding ... is not active` and the Vue app did not start. The
  same fix covers `$c-tr` elements in slot content that a caller passes
  to a cached component.
- The development warning for a repeated `id` now reads a numeric
  character reference in an `id` as the browser does, so `id="a&#1;b"`
  and `id="ab"` are no longer reported as the same id. When one element
  has two `id` attributes, the warning now counts only the first, which
  is the one the browser uses.
- Citry now adds its preload links to a page's `<head>` when the page
  holds a numeric character reference with thousands of digits. It used
  to skip them when such a reference fell where Citry splits the page to
  read it.