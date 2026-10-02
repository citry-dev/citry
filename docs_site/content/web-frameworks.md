---
title: Web frameworks
description: Mount Citry on FastAPI, Starlette, Flask, Django, or bare ASGI/WSGI so it can serve component assets, fragments, and server events.
---

# Web frameworks

Citry serves a few HTTP endpoints of its own: the browser runtime, component
JS and CSS, dependency files, the compiled code of interactive components, and
server events. Mounting Citry on your web app connects those endpoints to real
URLs.

Mount Citry when:

- you render a component that declares server events. Without a mount,
  serializing it raises `ValueError`, because the browser would have no URL
  to send its calls to;
- you serve HTML fragments (HTMX-style page updates). A fragment references
  its scripts by URL instead of inlining them, and until Citry is mounted,
  building those URLs raises a `RuntimeError`.

A full page without server events can render without a mount. It carries
its scripts and styles inline instead, so the browser cannot reuse cached
files between pages. See
[HTML fragments](/advanced/html-fragments/) for the full fragment flow.

## The default citry instance

Every component attaches to a [Citry][citry.Citry] instance through its
`citry = ...` class attribute. If you do not create one, components use the
ready-made default instance, exported as [citry][citry.citry]:

```python
from citry import citry  # a shared Citry() singleton
```

Pass whichever instance your components use to the adapter below. If you create
your own `Citry()`, mount that one, not the default. Components registered on one
instance are not visible on the other.

## Initialize before serving requests

Mounting Citry connects its HTTP routes, but it does not import your component
modules or prepare the component registry. Call
[`initialize()`][citry.Citry.initialize] after startup-time registration and
before the server starts request threads:

```python
citry.initialize()
```

Initialization imports configured component Python modules, creates built-ins,
and builds parse-time tag rules. It prevents two first requests from racing
through that work. Component template, JavaScript, and CSS asset files remain
lazy.

Use the host's root startup lifecycle. A mounted ASGI subapplication does not
provide a reliable startup lifespan, so mounting Citry alone is not a substitute
for initializing the instance. See
[Component discovery and startup](/advanced/component-discovery/#initialize-before-starting-worker-threads)
for retry and concurrent-access behavior.

## One entry point per framework

Each framework has a thin adapter under `citry.contrib`. Pick the row that
matches your stack.

| Framework | Entry point |
|---|---|
| FastAPI / Starlette | `citry.contrib.fastapi.mount(app, citry, prefix="/citry")` |
| Flask | `citry.contrib.flask.mount(app, citry, prefix="/citry")` |
| Django | `citry.contrib.django.urlpatterns(citry, prefix="/citry")` |
| Bare ASGI | `citry.contrib.asgi.asgi_app(citry)` |
| Bare WSGI | `citry.contrib.wsgi.wsgi_app(citry)` |

Pass a `prefix` that starts with `/`, such as `"/citry"`. A trailing slash is
dropped, so `"/citry/"` serves the same paths. `mount()`, `urlpatterns()`,
and `set_mounted_prefix()` reject a prefix without the leading `/` with a
`ValueError`, before they change your app or the Citry instance. Flask's
`mount()` also rejects the root prefix `"/"`, because every request would
then go to Citry and none to your Flask routes.

If you would rather run and copy a complete application, the
[starter project matrix]({{ repo_url }}/tree/{{ repo_edit_branch }}/examples){: target="_blank" rel="noopener"}
contains independently locked FastAPI, Django, Flask, bare ASGI, and bare WSGI
projects. They intentionally remain separate from the smaller examples built
into this documentation site.

## FastAPI and Starlette

`mount` attaches Citry's routes under the prefix and records where they live, so
URL building works afterwards. It needs no FastAPI import of its own, and the
same call works for Starlette (both expose a Starlette-style `.mount`).

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from citry.contrib.fastapi import mount
from citry import citry  # or your own Citry() instance

@asynccontextmanager
async def lifespan(_app):
    citry.initialize()
    yield


app = FastAPI(lifespan=lifespan)
# Serves /citry/... (the default prefix).
mount(app, citry)
# Or choose another prefix:
# mount(app, citry, prefix="/assets/citry")

# Now citry.mounted_prefix == "/citry", and the
# browser runtime is served at /citry/citry.js.
```

## Flask

`mount` wraps the app's `wsgi_app`. Requests under the prefix reach Citry;
everything else falls through to your app untouched (a lookalike path like
`/citryx` correctly goes to Flask, not Citry).

```python
from flask import Flask
from citry.contrib.flask import mount
from citry import citry

def create_app():
    app = Flask(__name__)
    mount(app, citry)  # serves /citry/...
    # After startup registration, before workers start.
    citry.initialize()
    return app
```

## Django

`urlpatterns` returns a list of Django URL patterns you `include()`. Passing
`prefix` also records where the routes are mounted.

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

Initialize the same instance from the project application config:

```python
# apps.py
from django.apps import AppConfig

from myapp import citry_instance


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        citry_instance.initialize()
```

Django also ships two extras in `citry.contrib.django`: `DjangoCache`, which
adapts a Django cache backend to Citry (`Citry(cache=DjangoCache(caches["default"]))`),
and `enable_hot_reload`, which clears a component's cache when its file changes
in development.

## Bare ASGI and WSGI

For any other stack, mount the dependency-free sub-app directly. These do not
record the mount prefix, so call `set_mounted_prefix` yourself, otherwise URL
building for fragments breaks.

```python
# Generic ASGI (no FastAPI needed)
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from citry.contrib.asgi import asgi_app
from citry import citry

@asynccontextmanager
async def lifespan(_app):
    citry.initialize()
    yield


app = Starlette(lifespan=lifespan)
app.mount("/citry", asgi_app(citry))
citry.set_mounted_prefix("/citry")   # asgi_app does not record it
```

```python
# Generic WSGI sub-mount (Pyramid, Bottle, classic WSGI)
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from citry.contrib.wsgi import wsgi_app
from citry import citry

app.wsgi_app = DispatcherMiddleware(
    app.wsgi_app,
    {"/citry": wsgi_app(citry)},
)
citry.set_mounted_prefix("/citry")
citry.initialize()  # before handing app.wsgi_app to a threaded server
```

Both sub-apps return `404 Not Found` for an unmatched path and
`405 Method Not Allowed` when the method is not in the route's `methods`. Under
the hood they walk the instance's route table, a tuple of
[URLRoute][citry.URLRoute] objects, and each handler returns a
[RouteResponse][citry.RouteResponse] the sub-app translates to the host's
response type.

## What mounting serves

Once mounted, the prefix exposes four dependency and asset endpoints:

- `{prefix}/citry.js`: the browser runtime, which bundles Vue with the code
  that starts interactive components and sends server events.
- `{prefix}/cache/{class_id}.{script_type}`: a component's JS or CSS.
- `{prefix}/cache/{class_id}.{hash}.{script_type}`: a component's JS or CSS
  addressed by a content hash, or the CSS variables that one render's
  `css_data()` produced.
- `{prefix}/asset/{file_name}`: a file a component depends on.

The built-in Events extension also exposes its own client script, the
endpoint the browser posts event calls to, and one URL per named component
handler. See
[Server events](/events/) for the handler workflow and
[Security](/security/#protect-event-posts-from-csrf) before deploying those
routes. It also serves the compiled component code and stylesheets that
interactive pages load, at `{prefix}/ext/events/definitions/{digest}.js` and
`{prefix}/ext/events/assets/{digest}.css`.

## Share the cache between worker processes

The worker that renders a page stores the page's per-instance variables,
compiled component code, and stylesheets in the Citry cache, or in its own
memory when no cache is configured. The browser then requests them by URL,
and a different worker may answer. Without a shared cache, that worker has
nothing stored and answers 404, so the page's interactive components
cannot load their code or styles.

If you run more than one worker process, point every worker at a shared cache
backend: DiskCache, Redis, or your Django cache through `DjangoCache` (see
[Cache backends](/performance/cache-backends/)). Citry writes these entries
without an expiry, because a page that is already open can request them at
any later time. Give the backend enough room that it does not drop them
while such pages are still in use. A single worker without a configured
cache keeps compiled code and stylesheets in memory up to the
`vue_asset_max_bytes` setting; see
[Limit memory for interactive page assets](/performance/cache-backends/#limit-memory-for-interactive-page-assets).

## URL building in a render-only process

If a background worker renders fragments that a different process serves, that
worker never mounts anything. Call `set_mounted_prefix` on its instance with the
same prefix the serving process mounts at, so the fragment URLs match:

```python
from citry import citry

# The same prefix the web app mounts at.
citry.set_mounted_prefix("/citry")
```
