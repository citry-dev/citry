---
title: Hot reload during development
url: https://citry.dev/v/0.4.6/guides/dev-server/
description: "Pick up edits to a component's template, JS, or CSS file on the next render without restarting, using citry watch and the reload helpers."
---
# Hot reload during development

While you are developing, editing a component's template, JS, or CSS file should
show up right away. Citry drops the cached copy of the changed file so the next
render reads it fresh from disk, with no server restart. This page covers the
`citry watch` command, the one-line helpers for Django and ASGI apps, and the
low-level call they all reduce to.

## What reloads, and what still needs a restart

Citry's hot reload is for the files a component loads: the ones named by
`template_file`, `js_file`, and `css_file` (and file entries in a component's
`Dependencies`). Edit one of those and citry reloads it in place.

An inline `template`, `js`, or `css` string lives in a `.py` file instead.
Editing that `.py` file is a Python code change, so it is your framework's own
reloader (Django's `runserver`, `uvicorn --reload`, Flask's reloader) that
restarts the process and picks it up. Adding a brand-new component is the same:
its class has to be imported, which is a restart.

So the two reloaders split the work cleanly. Your framework handles Python edits
and new files; citry handles edits to the template and asset files, in place.
Because citry's reload runs inside your process, it is faster than a full
restart, and for a tool like `uvicorn --reload` it also picks up the template
and asset directories that reloader skips by default.

## Turn on hot reload

The watcher can run two ways, and both end in the same reload step:

- The `citry watch` command, for a process you drive from the command line.
- A one-line helper for your web framework, which starts the watcher inside the
  running server.

### The `citry watch` command

Installing citry gives you a `citry` command (see the [CLI reference](/v/0.4.6/cli/)).
Its `watch` subcommand watches your component directories and reloads changed
files:


```sh
citry watch --path components/
```


`--path` (short `-p`) names a directory to watch and can be repeated; leave it
off to watch the engine's configured `dirs`. To watch against a specific engine
rather than the default one, put a leading `--app module:attribute` before the
subcommand:


```sh
citry --app myproject.app:engine watch
```


While it runs, it prints each reload and waits until you press Ctrl-C:


```text
citry: watching for component file changes (Ctrl-C to stop)
reloaded /app/components/greeting.html (Greeting)
citry: stopped watching
```


The name in parentheses is the component that was reset. If the changed file
does not back any component that has rendered in this process yet, that reads
`(no loaded component)` instead, because a reload only affects the caches of the
process it runs in. That is the key thing about `citry watch`: it reloads the
engine in the command's own process, so it fits a workflow where you render from
that same process. A web server runs in its own process, so there you want the
watcher running inside the server. The next two sections do exactly that.

### Django

Call `enable_hot_reload` once at startup, from your app config's `ready`. It
hooks into Django's own autoreloader (the one `runserver` already runs), so
there is no second watcher to install:


```python
# apps.py
from django.apps import AppConfig
from citry.contrib.django import enable_hot_reload
from myapp import engine

class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        enable_hot_reload(engine)
```


When a watched file changes, citry clears the caches of the components that
loaded it and lets Django keep running. That is the default, `mode="hot"`
(handle the change in place). Pass `mode="restart"` to instead let Django
restart the process, the same thing it does for a Python edit:


```python
enable_hot_reload(engine, mode="restart")
```


Either way, a file that backs no citry component falls through to Django's
normal handling.

### FastAPI and Starlette

Compose `reload_lifespan` into the app's root lifespan. Initialize Citry before
the server starts worker threads, then start the development watcher:


```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from citry.contrib.asgi import reload_lifespan
from myapp import engine

watch_lifespan = reload_lifespan(engine)

@asynccontextmanager
async def lifespan(app):
    engine.initialize()
    async with watch_lifespan(app):
        yield

app = FastAPI(lifespan=lifespan)
```


Starlette uses the same root-lifespan pattern. The helper manages only the
watcher; it deliberately does not initialize Citry. If you already have a
lifespan, nest the watcher inside it and keep `engine.initialize()` before the
first `yield`. Add the watcher only in development; keep the initialization in
production.

### Any other host: run the watcher yourself

For a stack without one of the helpers above, start the watcher in your own dev
entry point with `watch`. It returns a handle you can wait on and stop:


```python
from citry.reload import watch
from myapp import engine

handle = watch(engine)  # watches engine.settings.dirs
try:
    handle.wait()  # blocks until you stop it
except KeyboardInterrupt:
    handle.stop()
```


`watch(engine)` accepts a few keyword options (the ASGI `reload_lifespan`
forwards the same three): `roots=` to watch specific directories, `watcher=` to
choose a backend (next section), and `on_reload=` for a callback that runs after
each batch of changes.

## Choose a watcher backend

Citry can watch files three ways and uses the best one installed:

- **watchfiles** (recommended): a fast native backend that uses the operating
  system's own file-change events. Install it with the `watcher-watchfiles`
  extra.
- **watchdog**: an alternative native backend, for projects already using it.
  Install it with the `watcher-watchdog` extra.
- **polling**: a dependency-free fallback that re-scans the directories on a
  timer. Always available, but slower. This is what runs when neither extra is
  installed.

Install the recommended backend with:


```sh
pip install "citry[watcher-watchfiles]"
```


or the alternative:


```sh
pip install "citry[watcher-watchdog]"
```


Plain `citry` still watches with the polling fallback, so hot reload works
before you install anything; the extra just makes it faster and lighter. To
choose a backend yourself rather than by what is installed, pass a `watcher=`
instance (importable from `citry.reload`) to `watch`, for example
`watch(engine, watcher=WatchfilesWatcher())`. The ASGI `reload_lifespan`
forwards a `watcher=` too.

## Wire your own watcher to `invalidate_file`

Every path above ends in the same call on the [Citry](/v/0.4.6/reference/citry/#citry-citry) engine:
`invalidate_file`. If your host already runs its own file watcher, wire that
watcher straight to this method and skip citry's watcher entirely.

Take a [Component](/v/0.4.6/reference/component/#citry-component) whose template lives in a file:


```html
<!-- components/greeting.html -->
<p>Hello, {{ name }}!</p>
```



```citry
from pathlib import Path

from citry import Citry, Component

BASE_DIR = Path(__file__).parent
engine = Citry(dirs=[BASE_DIR / "components"])

class Greeting(Component):
    citry = engine  # bind to this engine (default engine otherwise)
    template_file = "greeting.html"

    def template_data(self, kwargs, slots):
        return {"name": "Ada"}

# The first render reads greeting.html from disk and caches it.
print(str(Greeting()))

# After you edit greeting.html, drop its cached template.
# The next render re-reads the file.
engine.invalidate_file(BASE_DIR / "components" / "greeting.html")
print(str(Greeting()))
```


The first `print` shows `Hello, Ada!`. Once you edit `greeting.html` and call
`invalidate_file`, the second `print` shows the new text. `invalidate_file`
returns the component classes it reset (here `[Greeting]`); an empty list means
the file backs no loaded component, which a custom handler can read as "not
mine" and, for example, fall through to a restart. It accepts a string or a
`Path`.

Two related calls help when a single path is not enough:

- `invalidate_all()` resets every component that has loaded a file, for a change
  you cannot tie to one path (a bulk edit, a branch switch). It returns the
  reset classes too.
- `get_components_for_file(path)` returns the components that loaded a file
  without resetting them, for a handler that wants to decide what to do itself.

## What hot reload covers

- **Asset files, not Python.** Template, JS, and CSS files reload in place;
  Python edits and new component files are your framework's restart.
- **One process at a time.** A reload clears the caches of the process it runs
  in. Run several workers and each keeps its own caches, so a change shows up one
  worker at a time; development usually runs a single process, which is where hot
  reload fits.
- **Development only.** Hot reload is a development convenience. In production,
  do not run `citry watch` and do not add the framework helper; leaving them out
  is all it takes.

For how Citry reuses rendered work, see
[Performance](/v/0.4.6/advanced/performance/) and
[Cache rendered output](/v/0.4.6/advanced/caching/). For loading JavaScript and CSS
from files, see [Dependency files](/v/0.4.6/advanced/dependency-files/).