---
title: Web frameworks
description: Mount Citry on FastAPI, Starlette, Flask, Django, or bare ASGI/WSGI so it can serve component assets, fragments, and server events.
---

# Web frameworks

Citry renders HTML in any Python program, but an interactive page also
needs URLs: the browser downloads Citry's runtime and your components' code
from them, and sends server events to them. Mounting Citry on your web
framework adds those URLs to your app.

You must mount Citry when you:

- render a component that has server [Events](/events/). Without a mount,
  serializing it raises `ValueError`, because the browser would have no URL
  to send its calls to;
- return [HTML fragments](/advanced/html-fragments/), for example to HTMX.
  A fragment links its scripts by URL, and building those URLs raises
  `RuntimeError` until Citry is mounted.

A full page without server events works without a mount. Its scripts and
styles are then written into the page itself, so the browser cannot cache
them between pages.

## Mount Citry

Each framework has a small adapter in `citry.contrib`:

| Framework | Call |
|---|---|
| FastAPI / Starlette | `citry.contrib.fastapi.mount(app, citry, prefix="/citry")` |
| Flask | `citry.contrib.flask.mount(app, citry, prefix="/citry")` |
| Django | `citry.contrib.django.urlpatterns(citry, prefix="/citry")` |
| Bare ASGI | `citry.contrib.asgi.asgi_app(citry)` |
| Bare WSGI | `citry.contrib.wsgi.wsgi_app(citry)` |

Pass the [Citry][citry.Citry] instance your components use. A component
uses the instance named in its `citry = ...` class attribute, or the
shared default instance [citry][citry.citry] when it names none:

```python
from citry import citry  # the default instance
```

If you create your own `Citry()`, mount that one. Components registered on
one instance are not visible to another.

The `prefix` is the URL path where Citry's routes live. It must start with
`/`: `mount()`, `urlpatterns()`, and `set_mounted_prefix()` raise
`ValueError` otherwise, before they change your app. A
trailing slash is ignored, so `"/citry/"` works like `"/citry"`.

`mount()` and `urlpatterns()` also let `citry check` and the editor ask
your framework whether it serves each link in your templates, so a link
to a missing page is reported before anyone opens it. For that, point
`citry --app` at the module that mounts Citry. See
[Links to missing pages](/ide/template-linting/#find-links-to-missing-pages).

For complete, runnable apps, see the
[starter projects]({{ repo_url }}/tree/{{ repo_edit_branch }}/examples){: target="_blank" rel="noopener"}
for FastAPI, Django, Flask, bare ASGI, and bare WSGI.

## `initialize()` at startup

Mounting adds the routes, but it does not import your component modules.
Call [`initialize()`][citry.Citry.initialize] once at startup, after you
register components and before the server starts handling requests:

```python
citry.initialize()
```

This imports your component modules and prepares Citry once, so the first
requests do not all try to do it at the same time. Component templates,
JavaScript, and CSS files still load the first time a component needs them.

Call it from your app's own startup code, as the examples below show. A
mounted ASGI sub-app does not reliably receive startup events, so mounting
Citry does not initialize it for you. See
[Discovery and startup](/advanced/component-discovery/#initialize-before-starting-worker-threads)
for what happens when initialization fails, runs twice, or starts from
two threads at once.

## FastAPI and Starlette

`mount()` adds Citry's routes under the prefix and records the prefix, so
Citry can build its URLs. The same call works for Starlette.

```python
from contextlib import asynccontextmanager

from citry import citry
from citry.contrib.fastapi import mount
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(_app):
    citry.initialize()
    yield


app = FastAPI(lifespan=lifespan)
# Serves Citry under /citry, the default prefix.
# The browser runtime is then at /citry/citry.js.
mount(app, citry)
```

`mount()` also adds a middleware to `app`. It reads each request's
`root_path`, so Citry's URLs include the sub-path your app is served
below (see [Serve below a sub-path](#serve-below-a-sub-path)). Call
`mount()` before the server starts the app, for example at module level
as above, not inside `lifespan`. Starlette accepts middleware only until
then, so a later `mount()` skips the middleware, and Citry's URLs use
`app.root_path` only.

## Flask

`mount()` sends requests under the prefix to Citry and every other request
to your Flask app. A path that only starts with the same letters, such as
`/citryx`, still goes to Flask.

```python
from citry import citry
from citry.contrib.flask import mount
from flask import Flask


def create_app():
    app = Flask(__name__)
    mount(app, citry)  # serves /citry/...
    # After you register components, before workers start.
    citry.initialize()
    return app
```

Flask's `mount()` rejects the root prefix `"/"` with `ValueError`, because
every request would then go to Citry and none to your Flask routes.

## Django

`urlpatterns()` returns Django URL patterns to `include()`. Pass the same
`prefix` as the path you include them under, so Citry builds matching URLs:

```python
# urls.py
from django.urls import include, path

from citry.contrib.django import urlpatterns as citry_urls
from myapp import citry_instance

urlpatterns = [
    path(
        "citry/",
        include(citry_urls(citry_instance, prefix="/citry")),
    ),
]
```

Initialize the instance from your app config:

```python
# apps.py
from django.apps import AppConfig

from myapp import citry_instance


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        citry_instance.initialize()
```

`citry.contrib.django` also has `DjangoCache`, which lets Citry store its
data in a Django cache (`Citry(cache=DjangoCache(caches["default"]))`), and
`enable_hot_reload`, which shows edits to component files without a
restart (see [Hot reload](/guides/hot-reload/#enable-in-django)).

## Bare ASGI and WSGI

On any other ASGI or WSGI stack, mount Citry's sub-app yourself. These
sub-apps do not know where you mounted them, so also call
`set_mounted_prefix()` with the same path. Without it, building fragment
URLs fails. Below a sub-path, include it in that path, as
[Serve below a sub-path](#serve-below-a-sub-path) shows.

```python
# Any ASGI app, here Starlette
from contextlib import asynccontextmanager

from citry import citry
from citry.contrib.asgi import asgi_app
from starlette.applications import Starlette


@asynccontextmanager
async def lifespan(_app):
    citry.initialize()
    yield


app = Starlette(lifespan=lifespan)
app.mount("/citry", asgi_app(citry))
citry.set_mounted_prefix("/citry")
```

```python
# Any WSGI app: Pyramid, Bottle, plain WSGI
from citry import citry
from citry.contrib.wsgi import wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app.wsgi_app = DispatcherMiddleware(
    app.wsgi_app,
    {"/citry": wsgi_app(citry)},
)
citry.set_mounted_prefix("/citry")
# Before a threaded server starts handling requests.
citry.initialize()
```

Both sub-apps answer `404 Not Found` for a path they do not serve and
`405 Method Not Allowed` for a method the route does not accept. Neither
sub-app knows your app's routes, so with only these mounted, `citry check`
checks no links and prints one note saying so.

## Share the cache { #share-the-cache-between-worker-processes }

With several worker processes, an interactive page can show its HTML but
never start: the browser console shows 404 responses for component code or
stylesheets.

This happens because the worker that renders a page stores that page's
compiled component code, stylesheets, and CSS variables. The browser
then downloads them by URL, and another worker may answer. If each
worker keeps them in its own memory, that worker has nothing stored.

Point every worker at one shared cache backend: DiskCache, Redis, or your
Django cache through `DjangoCache` (see
[Cache backends](/performance/cache-backends/)). Citry stores these entries
without an expiry time, because a page that is already open may ask for
them at any later time. Give the backend enough room that it does not drop
them while such pages are still in use.

A single process without a configured cache keeps the compiled code,
stylesheets, and `css_data()` stylesheets in memory, up to the
`vue_asset_max_bytes` setting; see
[Limit asset memory](/performance/cache-backends/#limit-memory-for-interactive-page-assets).

## Render-only workers

A background worker may render fragments that your web process later
serves. That worker never mounts Citry, so tell it where the web process
mounted Citry's routes:

```python
from citry import citry

# The same prefix the web app mounts at.
citry.set_mounted_prefix("/citry")
```

## Serve below a sub-path

When a proxy or your server serves the app below a sub-path, such as
`/shop`, Citry starts every URL it writes with that sub-path. The browser
then loads Citry's scripts and styles, and sends event calls, under
`/shop/citry/`. The adapters above read the sub-path for you, so most
apps need no change. At the site root, the URLs stay as they are.

Inside a request, each adapter reads the sub-path from the request.
Outside one, such as a page rendered in a script or a test, it reads the
app's setting:

| Framework | Inside a request | Outside a request |
| --- | --- | --- |
| FastAPI | the request's `root_path`, set by `uvicorn --root-path`, `FastAPI(root_path=...)`, or your middleware | `app.root_path` |
| Starlette | the request's `root_path` | the site root |
| Flask | the request's `script_root`, from the server's `SCRIPT_NAME` or `ProxyFix` | `APPLICATION_ROOT` |
| Django | `FORCE_SCRIPT_NAME` when set, otherwise the request's `SCRIPT_NAME` (WSGI) or `root_path` (ASGI) | the script prefix Django last set, `FORCE_SCRIPT_NAME` after `django.setup()` |

The sub-path decides where the page loads Citry's scripts from, so it
must come from your own deployment, never from a visitor. Set it with
`uvicorn --root-path`, `FastAPI(root_path=...)`, your server's
`SCRIPT_NAME`, or Django's `FORCE_SCRIPT_NAME`. If a proxy passes it in a
header such as `X-Forwarded-Prefix`, read that header only from the proxy
you run, for example with Werkzeug's `ProxyFix(x_prefix=1)` behind exactly
one trusted proxy, and make sure the proxy sets or removes that header on
every request, replacing any value the visitor sent. Otherwise a visitor
can make the page load scripts from another path on your site, and a
shared HTTP cache that ignores the header can serve that page to others.
With [`security_script_integrity="citry"`](/security/#pin-citry-managed-scripts-with-sri),
the browser also refuses a Citry script whose content does not match.

A trailing `/` is ignored, and `/` (Flask's default `APPLICATION_ROOT`)
means the site root. Citry ignores a sub-path that does not start with a
single `/`, such as `shop` or `//shop`, and writes its URLs from the site
root. A value such as `//shop` would otherwise point the page's scripts
at another site.

Some setups need care:

- **Your own threads.** A page rendered in a thread you start with
  `loop.run_in_executor()` or `threading.Thread` cannot see the request,
  so its URLs use the app's setting. Use `asyncio.to_thread()` or
  Starlette's `run_in_threadpool()`, which pass the request along.
- **Flask streamed responses.** A generator response sees the sub-path
  only when you wrap it with `stream_with_context()`. Without it, the
  streamed page's URLs use `APPLICATION_ROOT`, and its scripts fail to
  load.
- **The render cache** keeps separate entries for each sub-path. To
  delete one entry from a background job when only your server sets the
  sub-path, pass `sub_path=` to `component_cache_key()` or
  `fragment_cache_key()`, as [Caching](/performance/caching/) shows.
- **Render-only workers and the bare sub-apps.** A
  [render-only worker](#render-only-workers) and the bare ASGI and WSGI
  sub-apps cannot see the sub-path, so give `set_mounted_prefix()` the
  full path: `citry.set_mounted_prefix("/shop/citry")`. Do this only in
  a process that never calls `mount()` or `urlpatterns()`. Those already
  add the sub-path from the app's setting, so the URLs would start with
  `/shop/shop`.

## URLs Citry serves

Under the prefix, Citry serves:

- `{prefix}/citry.js`: the browser runtime, which includes Vue and the code
  that starts interactive components and sends server events;
- `{prefix}/cache/{class_id}.{script_type}`: a component's JavaScript or
  CSS;
- `{prefix}/cache/{class_id}.{hash}.{script_type}`: the same, named by a
  hash of its content, or the CSS variables that one
  render's `css_data()` produced;
- `{prefix}/asset/{file_name}`: a file that a component depends on;
- `{prefix}/ext/events/definitions/{digest}.js` and
  `{prefix}/ext/events/assets/{digest}.css`: the compiled component code
  and stylesheets that interactive pages load.

The built-in Events extension also serves its own browser script, the URL
the browser posts event calls to, and one URL per event handler. See
[Server events](/events/), and read
[Security](/security/#protect-event-posts-from-csrf) before you deploy
those routes.

### How browsers cache files

A component's script or stylesheet named by a hash of its content
(`{prefix}/cache/{class_id}.{hash}.js`), a file served from
`{prefix}/asset/` (its name is a hash of the file), and the Events
definitions and stylesheets never change at their URL. Citry sends them
with `Cache-Control: public, max-age=31536000, immutable`, so the browser
keeps them for a year without asking again. When the content changes, the
page links a new URL.

`{prefix}/citry.js`, `{prefix}/cache/{class_id}.{script_type}`, and the
stylesheet built from one render's `css_data()` can change at the same
URL, for example when you upgrade Citry. Citry sends them with
`Cache-Control: no-cache` and an `ETag`. The browser keeps a copy but asks
before each use, and Citry answers `304 Not Modified`, with no body, while
the copy is current. The Events and i18n browser scripts
(`{prefix}/ext/events/runtime.js` and `{prefix}/ext/i18n/runtime.js`) are
sent with `Cache-Control: no-store`, so the browser downloads them on each
page load. A missing file gets `404` with `no-store`, because another
worker may store it a moment later.

A CDN or proxy in front of your app should pass these headers through
unchanged. If it drops `no-cache` and stores a file anyway, visitors keep
the old `citry.js` after you upgrade Citry.
