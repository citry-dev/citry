---
title: Web frameworks
description: Mount Citry on FastAPI, Starlette, Flask, Django, or bare ASGI/WSGI so it can serve component assets, fragments, and server events.
---

# Web frameworks

Citry renders HTML in any Python program, but an interactive page also
needs URLs: the browser downloads Citry's runtime (the JavaScript that
starts interactive components and sends server events, Vue included) and
your components' code from them, and sends server events to them. Mounting
Citry on your web framework adds those URLs to your app.

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

After you upgrade Citry, a page whose runtime is gone recovers by itself
only when its view passes the request method to `serialize()`. See
[Pass the request method](#pass-the-request-method).

## Link the runtime by hand

Citry links the runtime in a full page that contains interactive
components. A page that only receives
[HTML fragments](/advanced/html-fragments/) must link it itself, whether
you write its HTML or render it with Citry. Get the runtime's URL from
[`citry.runtime_url()`][citry.Citry.runtime_url] in the view that builds
the page:

```python
from citry import citry

runtime_src = citry.runtime_url()
# For example "/citry/citry.<hash>.js". Put it in the page as
# <script src="..."></script>.
```

The URL includes the mount prefix and any sub-path your app is served
below. `runtime_url()` raises `RuntimeError` when Citry is not mounted on
your web app, because the URL would point nowhere.

Call it each time you build the page. A static HTML file that you write
once would keep the old hash after you upgrade Citry, so link the stable
`/citry/citry.js` from such a file instead. The browser downloads that
file on every page load.

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
mount(app, citry)
```

`mount()` also adds a middleware to `app`. It reads each request's
`root_path`, so Citry's URLs include the sub-path your app is served
below (see [Serve below a sub-path](#serve-below-a-sub-path)). Call
`mount()` before the server starts the app, for example at module level
as above, not inside `lifespan`. Starlette accepts middleware only until
then, so a later `mount()` skips the middleware, and Citry's URLs use
`app.root_path` only.

Your middleware runs for Citry's routes, but `dependencies=` on the app
does not, so a login check written as a dependency does not protect
Citry's events. See [Protect Citry's routes](#protect-citrys-routes).

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

Requests under the prefix go to Citry before Flask sees them, so your
`before_request` hooks, and extensions built on them, do not run for
Citry's routes. See [Protect Citry's routes](#protect-citrys-routes).

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

## Protect Citry's routes { #protect-citrys-routes }

Check who may call an event in the component: a `_guard` method on its
`Events` class runs before every handler, and `@event(guard=...)` runs
before one handler. These checks run under every framework; see
[Authorize every event](/security/#authorize-every-event).

Do not rely on a login check that your framework runs only for its own
routes. On FastAPI, Starlette, and Flask, requests under the prefix go to
Citry before your framework's own routing, so some of the code you attach
to your app does not run for them. Citry's own
CSRF checks still run (see
[What Citry always checks](/security/#what-citry-always-checks)), but a
token check you add yourself may not:

| Framework | Runs for Citry's routes | Does not run for them |
|---|---|---|
| FastAPI, Starlette | Middleware, such as `@app.middleware("http")` | `dependencies=` on the app |
| Flask | WSGI middleware that wraps `app.wsgi_app` after `mount()`, or wraps the Flask app object | `before_request`, `after_request`, other request hooks, and extensions that use them, such as Flask-WTF's `CSRFProtect` |
| Django | Everything in `MIDDLEWARE`; Citry's routes are ordinary views | Nothing |
| Bare ASGI, WSGI | Middleware that wraps the app you serve (on WSGI, after you add the `DispatcherMiddleware`) | Nothing |

Use middleware for code that must run on every request, such as rate
limits or response headers. With the bare sub-apps, you can also wrap
only Citry's routes, as in `MyMiddleware(asgi_app(citry))` or
`{"/citry": MyMiddleware(wsgi_app(citry))}`.

On Django, middleware that requires a login for every view, such as
`LoginRequiredMiddleware` (Django 5.1 and later), also applies to Citry's
routes. Visitors who are not logged in then get a redirect instead of
Citry's scripts, and the interactive parts of a public page do not start.
Mark Citry's views as open to everyone, and check the login in a guard:

```python
from django.contrib.auth.decorators import login_not_required

citry_patterns = citry_urls(citry_instance, prefix="/citry")
for pattern in citry_patterns:
    pattern.callback = login_not_required(pattern.callback)
```

### Read the Flask session

A guard that checks the logged-in user needs the session. Using
`flask.request`, `session`, or `g` in an event handler or guard raises
`RuntimeError: Working outside of request context`, because Flask never
handled the call. To read the session, give Flask the request back:
`request.native` holds the raw WSGI request data (the `environ` dict the
server passes to the app), and `app.request_context()` turns it into a
Flask request:

```citry
from citry import Component
from citry.ext.events import EventError
from flask import session

from myapp import app  # the Flask app you passed to mount()


class Profile(Component):
    class Events:
        def save(self, data: ProfileIn, request):
            with app.request_context(request.native):
                user_id = session.get("user_id")
            if user_id is None:
                raise EventError("Log in first.", status=403)
            update_profile(user_id, data)
```

In a guard, pass `self.request.native` instead.

Changes to the session inside this block are not saved, because Flask
writes the session cookie only on its own responses. Set session values
in a Flask route instead. With an app factory such as `create_app()`,
there is no module-level `app` to import. Store the app that
`create_app()` returns in a module, such as `myapp/wsgi.py`, and import
it from there.

### Order WSGI middleware

`mount()` replaces `app.wsgi_app` with a function that sends Citry's
paths to Citry and everything else to the `app.wsgi_app` it found. A
middleware that wraps `app.wsgi_app` before `mount()` ends up on the
Flask side only, so it never sees Citry's routes:

```python
# Wrong: Citry's routes skip this middleware
app.wsgi_app = MyMiddleware(app.wsgi_app)
mount(app, citry)

# Right: the middleware sees every request
mount(app, citry)
app.wsgi_app = MyMiddleware(app.wsgi_app)
```

The same goes for the bare WSGI sub-app: wrap `app.wsgi_app` after you
add the `DispatcherMiddleware`.

## Share the cache { #share-the-cache-between-worker-processes }

With several worker processes, an interactive page can show its HTML but
never start: the browser console shows 404 responses for component code,
stylesheets, or Citry's runtime.

This happens because the worker that renders a page stores that page's
compiled component code, stylesheets, and CSS variables. The browser
then downloads them by URL, and another worker may answer. If each
worker keeps them in its own memory, that worker has nothing stored.

Point every worker at one shared cache backend: DiskCache, Redis, or your
Django cache through `DjangoCache` (see
[Cache backends](/performance/cache-backends/)). Citry stores these entries
without an expiry time, because a page that is already open may ask for
them at any later time. Give the backend enough room that it does not drop
them while such pages are still in use. Browser runtimes are the
exception: Citry keeps each one for 30 days after it was last written,
which covers pages rendered before a deploy (see
[Deploy a Citry upgrade](#deploy-a-new-version)).

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
every request, replacing any value the visitor sent. On Flask, wrap
`ProxyFix` after `mount()`, as
[Order WSGI middleware](#order-wsgi-middleware) shows. Otherwise a visitor
can make the page load scripts from another path on your site, and a
shared HTTP cache that ignores the header can serve that page to others.
On the tags Citry writes, the browser also checks each file against a hash
and refuses different content. See
[Pin files with SRI](/security/#pin-citry-managed-scripts-with-sri).

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

## Run behind a proxy

**Symptom:** pages load, but every event call that is not a `GET` fails
with status 403 and the message "The call failed the CSRF check; reload
the page and try again."

On each such call, the browser sends an `Origin` header with the site's
address, and Citry checks that its host and port match the request's
`Host` header (see
[What Citry always checks](/security/#what-citry-always-checks)). A
reverse proxy that replaces `Host` with your app server's address, such
as `127.0.0.1:8000`, makes every call fail that check. To confirm the
cause, turn on the `citry` logger's `DEBUG` level locally: it logs
`Origin '...' does not match the request host '127.0.0.1:8000'`.

Have the proxy pass the `Host` header the browser sent. Caddy and Traefik
do this by default. nginx does not, so set it. Use `$http_host`, not
`$host`, which drops the port:

```text
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $http_host;
}
```

With Apache, turn on `ProxyPreserveHost On`.

Citry reads only the `Host` header, not `X-Forwarded-Host`, and Django's
`USE_X_FORWARDED_HOST` setting does not change that. If the proxy already
sends the browser's host in `X-Forwarded-Host` and you cannot change its
`Host`, a WSGI middleware that copies `X-Forwarded-Host` into `Host`, such as
Werkzeug's `ProxyFix(x_host=1)`, also works. Use it only behind a proxy
you run, and on Flask, wrap it after `mount()`
([Order WSGI middleware](#order-wsgi-middleware)).

## URLs Citry serves

Under the prefix, Citry serves:

- `{prefix}/citry.{hash}.js`: the browser runtime. `{hash}` is a hash of
  the file, so the URL changes whenever a Citry release changes the file.
  Pages that Citry renders link this URL;
- `{prefix}/citry.js`: the same runtime at a stable URL, one that stays
  the same across releases, for a page that cannot link the hashed URL
  (see [Link the runtime by hand](#link-the-runtime-by-hand));
- `{prefix}/ext/i18n/runtime.{hash}.js` and its stable URL
  `{prefix}/ext/i18n/runtime.js`: the browser code for translations,
  which pages that translate text in the browser link;
- `{prefix}/cache/{class_id}.{script_type}`: a component's JavaScript or
  CSS;
- `{prefix}/cache/{class_id}.{hash}.{script_type}`: the same, named by a
  hash of its content, or the CSS variables that one
  render's `css_data()` produced;
- `{prefix}/asset/{file_name}`: a file that a component depends on;
- `{prefix}/ext/events/definitions/{digest}.js` and
  `{prefix}/ext/events/assets/{digest}.css`: the compiled component code
  and stylesheets that interactive pages load.

The built-in Events extension also serves
`{prefix}/ext/events/runtime.js` (the same runtime as `citry.js`), the
URL the browser posts event calls to, and one URL per event handler. See
[Server events](/events/), and read
[Security](/security/#protect-event-posts-from-csrf) before you deploy
those routes.

### Check cache headers { #how-browsers-cache-files }

A component's script or stylesheet named by a hash of its content
(`{prefix}/cache/{class_id}.{hash}.js`), a file served from
`{prefix}/asset/` (its name is a hash of the file), and the Events
definitions and stylesheets never change at their URL. Citry sends them
with `Cache-Control: public, max-age=31536000, immutable`, so the browser
keeps them for a year without asking again. When the content changes, the
page links a new URL.

`{prefix}/cache/{class_id}.{script_type}` and the stylesheet built from
one render's `css_data()` can change at the same URL, for example when
you upgrade Citry. Citry sends them with `Cache-Control: no-cache` and an
`ETag`. The browser keeps a copy but asks before each use, and Citry
answers `304 Not Modified`, with no body, while the copy is current.

The browser runtimes that pages link, `{prefix}/citry.{hash}.js` and
`{prefix}/ext/i18n/runtime.{hash}.js`, are also named by a hash of their
content and sent as `immutable`. The browser downloads each one again
only after a Citry release changes the file, not on every page load. A
page always names the runtime it was rendered for, so it never starts
with a runtime from another release.

The stable runtime URLs, `{prefix}/citry.js`,
`{prefix}/ext/events/runtime.js`, and `{prefix}/ext/i18n/runtime.js`, keep
their address across releases. Citry sends them with
`Cache-Control: no-store`, so the browser downloads them on each page load.

A missing file gets `404` with `no-store`, because another worker may
store it a moment later. On FastAPI, Flask, and bare ASGI or WSGI apps, a
path under the prefix that matches no route also gets `404` with
`no-store`. On Django, such a path gets your project's own `404` page.

A CDN or proxy in front of your app should pass these headers through
unchanged. If it stores a stable runtime URL anyway, a page that links
that URL runs the old runtime after you upgrade Citry. See
[Keep files unchanged](/security/#keep-files-unchanged).

## Deploy a Citry upgrade { #deploy-a-new-version }

A page rendered before you upgrade Citry still links the old runtime. It
starts anyway when the browser kept that file, or when a
[shared cache](#share-the-cache-between-worker-processes) still holds it.
The cache keeps each runtime for 30 days after it was last written. To
keep every page working after an upgrade:

- pass the request method to `serialize()`, so a page whose runtime is
  gone can reload itself once (below);
- clear whole-page caches when you deploy;
- give every worker one shared cache.

When neither the browser nor the server has the old runtime, the server
answers `404`. The page keeps the HTML the server sent: links and plain
forms work, interactive components do not start, and the browser console
shows `Citry could not load its runtime`. A page whose view passed the
request method then reloads once to get fresh HTML. Any other page stays
as it is until the visitor opens it again.

The reload comes from the script Citry writes to start the page. A page
that links the runtime with a `<script>` tag you wrote yourself does not
reload. It picks up the new runtime the next time your view builds the
page.

### Pass the request method

Pass the request's method to `serialize()` in every view that returns a
page:

```python
@app.get("/contact")
async def contact(request: Request) -> HTMLResponse:
    contact_page = ContactPage()
    page = contact_page.render()
    html = page.serialize(request_method=request.method)
    return HTMLResponse(html)
```

`str(ContactPage())`, `str(page)`, and `bytes(page)` pass no method, so
use `serialize()`. The same expression, `request.method`, works in
Django and Flask.

Only a page that answers `GET` or `HEAD` reloads, and the reload repeats
that `GET` request. A page that answers anything else, such as a form
`POST`, never reloads, because reloading it would send the form again,
and some browsers do that without asking the visitor. A page rendered
without `request_method` never reloads either.

Pass the method the request really used. If repeating a `GET` request
is not harmless, for example because the view uses up a one-time link,
do not pass `request_method` from that view.

Pass `request.method` as it is; `get` and `GET` both count. A value that
is not an HTTP method name raises `ValueError`. Citry never writes the
value to the page.

### Clear whole-page caches

A CDN or page cache that stores whole HTML pages keeps serving pages that
name the old runtime after a deploy, and a page that reloads itself gets
the same page again. Clear those caches when you deploy a Citry upgrade.

### Handle rolling deploys { #rolling-deploys }

During a rolling deploy, a page rendered by a worker on the new release
can ask a worker still on the old release for its runtime. Give every
worker the same [shared cache](#share-the-cache-between-worker-processes),
or use sticky sessions so that one visitor's requests reach one worker.
Each worker writes the runtimes it links to the shared cache, so any
worker can answer for them. Workers on Citry 0.8.0 or earlier cannot
serve these runtimes, even from a shared cache.

### Stop CDNs caching 404s

Citry sends a `404` for its files with `Cache-Control: no-store`. Most
CDNs follow that header. Some have a setting that caches error answers,
such as `404`, for a fixed time whatever the headers say. Turn it off for
URLs under your Citry prefix, or a runtime that one worker could not
serve during a deploy keeps failing after every worker has it. Citry
0.8.0 and earlier send their `404` without `no-store`, so after you
upgrade from those versions, clear any `404` answers your CDN stored
under your Citry prefix.
