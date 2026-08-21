---
title: Web frameworks
url: https://citry.dev/v/0.4.2/web-frameworks/
description: "Mount Citry on FastAPI, Starlette, Flask, Django, or bare ASGI/WSGI so it can serve component assets, fragments, and server events."
---
# Web frameworks

Citry serves a few HTTP endpoints of its own: component JS and CSS, dependency
files, client runtimes, HTML fragments, and named server events. Mounting Citry
on your web app connects those endpoints to real URLs.

You need this once you serve HTML fragments (HTMX-style page updates), because a
fragment references its scripts by URL instead of inlining them. Until Citry is
mounted, building those URLs raises a `RuntimeError`. See
[HTML fragments](/v/0.4.2/advanced/html-fragments/) for the full fragment flow.

## The default citry instance

Every component attaches to a [Citry](/v/0.4.2/reference/citry/#citry-citry) instance through its
`citry = ...` class attribute. If you do not create one, components use the
ready-made default instance, exported as [citry](/v/0.4.2/reference/citry/#citry-citry-2):


```python
from citry import citry  # a shared Citry() singleton
```


Pass whichever instance your components use to the adapter below. If you create
your own `Citry()`, mount that one, not the default. Components registered on one
instance are not visible on the other.

## Initialize before serving requests

Mounting Citry connects its HTTP routes, but it does not import your component
modules or prepare the component registry. Call
[`initialize()`](/v/0.4.2/reference/citry/#citry-citry-initialize) after startup-time registration and
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
[Component discovery and startup](/v/0.4.2/advanced/component-discovery/#initialize-before-starting-worker-threads)
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

The `prefix` must start with `/` and is stored without a trailing slash (so
`"/citry/"` becomes `"/citry"`).

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
mount(app, citry)                             # serves /citry/... (default prefix)
# mount(app, citry, prefix="/assets/citry")   # or a custom prefix

# After mounting, citry.mounted_prefix == "/citry" and the client runtime
# is served at /citry/citry.js.
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
    mount(app, citry)           # serves /citry/...
    citry.initialize()          # after startup registration, before workers
    return app
```


## Django

`urlpatterns` returns a list of Django URL patterns you `include()`. Passing
`prefix` also records where the routes are mounted.


```python
# urls.py
from django.urls import path, include
from citry.contrib.django import urlpatterns as citry_urlpatterns
from myapp import citry_instance

urlpatterns = [
    path("citry/", include(citry_urlpatterns(citry_instance, prefix="/citry"))),
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

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/citry": wsgi_app(citry)})
citry.set_mounted_prefix("/citry")
citry.initialize()  # before handing app.wsgi_app to a threaded server
```


Both sub-apps return `404 Not Found` for an unmatched path and
`405 Method Not Allowed` when the method is not in the route's `methods`. Under
the hood they walk the instance's route table, a tuple of
[URLRoute](/v/0.4.2/reference/web/#citry-urlroute) objects, and each handler returns a
[RouteResponse](/v/0.4.2/reference/web/#citry-routeresponse) the sub-app translates to the host's
response type.

## What mounting serves

Once mounted, the prefix exposes four dependency and asset endpoints:

- `/{prefix}/citry.js` the client runtime that loads component JS/CSS on demand.
- `/{prefix}/cache/{class_id}.{script_type}` a component's cached class-level JS or CSS.
- `/{prefix}/cache/{class_id}.{vars_hash}.{script_type}` the per-instance JS/CSS variables for one render.
- `/{prefix}/asset/{file_name}` a file a component depends on.

The built-in Events extension also exposes its client runtime, batch endpoint,
and one URL per named component handler. See
[Server events](/v/0.4.2/events/) for the handler workflow and
[Security](/v/0.4.2/security/#protect-event-posts-from-csrf) before deploying those
routes.

The per-instance variables endpoint cannot be rebuilt from the component class
on a cache miss. If you run more than one worker process and serve fragments,
point every worker at a shared cache backend (Redis, Memcached, or DiskCache),
or those URLs return 404 on a worker that did not render them.

## URL building in a render-only process

If a background worker renders fragments that a different process serves, that
worker never mounts anything. Call `set_mounted_prefix` on its instance with the
same prefix the serving process mounts at, so the fragment URLs match:


```python
from citry import citry

citry.set_mounted_prefix("/citry")   # same prefix the web app mounts at
```
