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

## Mount Citry on your framework

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
`/`, or the call raises `ValueError` before it changes your app. A
trailing slash is ignored, so `"/citry/"` works like `"/citry"`.

For complete, runnable apps, see the
[starter projects]({{ repo_url }}/tree/{{ repo_edit_branch }}/examples){: target="_blank" rel="noopener"}
for FastAPI, Django, Flask, bare ASGI, and bare WSGI.

## Initialize Citry at startup

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
[Component discovery and startup](/advanced/component-discovery/#initialize-before-starting-worker-threads)
for what happens when initialization fails or runs twice.

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
restart (see [Hot reload](/guides/dev-server/#django)).

## Bare ASGI and WSGI

On any other ASGI or WSGI stack, mount Citry's sub-app yourself. These
sub-apps do not know where you mounted them, so also call
`set_mounted_prefix()` with the same path. Without it, building fragment
URLs fails.

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
`405 Method Not Allowed` for a method the route does not accept.

## Share the cache between worker processes

With several worker processes, an interactive page can show its HTML but
never start: the browser console shows 404 responses for component code or
stylesheets.

This happens because the worker that renders a page stores that page's
compiled component code, stylesheets, and CSS variables in the Citry
cache. The browser then downloads them by URL, and another worker may
answer. If each worker keeps its own cache in memory, that worker has
nothing stored.

Point every worker at one shared cache backend: DiskCache, Redis, or your
Django cache through `DjangoCache` (see
[Cache backends](/performance/cache-backends/)). Citry stores these entries
without an expiry time, because a page that is already open may ask for
them at any later time. Give the backend enough room that it does not drop
them while such pages are still in use.

A single process without a configured cache keeps this code in memory, up
to the `vue_asset_max_bytes` setting; see
[Limit memory for interactive page assets](/performance/cache-backends/#limit-memory-for-interactive-page-assets).

## Build URLs in a process that does not serve requests

A background worker may render fragments that your web process later
serves. That worker never mounts Citry, so tell it where the web process
mounted Citry's routes:

```python
from citry import citry

# The same prefix the web app mounts at.
citry.set_mounted_prefix("/citry")
```

## URLs that Citry serves

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
