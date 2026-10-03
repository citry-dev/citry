---
title: Hot reload during development
description: Pick up edits to a component's template, JS, or CSS file on the next render without restarting, using citry watch and the reload helpers.
---

# Hot reload during development

While you develop, you want an edit to a component's template, JavaScript,
or CSS file to show up when you reload the page, without restarting the
server. Turn on Citry's hot reload: when such a file changes, Citry forgets
its stored copy, and the next render reads the file again.

## What reloads

Hot reload covers the files a component loads: the ones named by
`template_file`, `js_file`, and `css_file`, and file entries in its
`Dependencies`.

An inline `template`, `js`, or `css` string lives in a `.py` file, so
editing it is a Python change. Your framework's own reloader picks that up
by restarting the process: Django's `runserver`, `uvicorn --reload`, or
Flask's reloader. A new component is a Python change too, because its class
has to be imported.

The two work together: your framework restarts for Python edits, and Citry
reloads template and asset files in place, which is faster than a restart.
It also sees template and asset directories that `uvicorn --reload` does
not watch by default.

## Enable in Django

Call `enable_hot_reload` once at startup, from your app config's `ready()`.
It uses the reloader that Django's `runserver` already runs, so you install
no second watcher:

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

Django's reloader already watches your Python files and your Django
template directories, and `enable_hot_reload` adds every file under the
engine's `dirs` (the directories you pass to `Citry(dirs=[...])`). When a
component file there changes, Citry reloads it and Django keeps running.
When a Python file changes, Django restarts the server as usual.

Point `dirs` at your component folders, not the project root. The
reloader checks every file under them, so a large folder makes it slow.

To restart the server instead of reloading in place, for example when
other code reads component files at startup, pass `mode="restart"`. The
server then restarts when a component file that has already been
rendered changes; other files under `dirs` never restart it:

```python
enable_hot_reload(engine, mode="restart")
```

!!! warning "Keep component files where Django's reloader looks"

    Besides Python files, the reloader reports only files under the
    engine's `dirs` and your Django template directories (the `DIRS` of a
    `DjangoTemplates` backend in `TEMPLATES` and, with the app directories
    loader, each app's `templates/` folder). An edit to a component file
    anywhere else, such as next to a component's `.py` file outside those
    directories, does not show up. Move the file into one of those
    directories, or use
    [`citry.reload.watch`](#enable-in-any-other-app) instead.

## Enable in FastAPI

Add `reload_lifespan` to your app's lifespan; Starlette works the same
way. Initialize Citry first, then start the watcher inside it:

```python
from contextlib import asynccontextmanager

from citry.contrib.asgi import reload_lifespan
from fastapi import FastAPI
from myapp import engine

watch_lifespan = reload_lifespan(engine)


@asynccontextmanager
async def lifespan(app):
    engine.initialize()
    async with watch_lifespan(app):
        yield


app = FastAPI(lifespan=lifespan)
```

`reload_lifespan` only starts and stops the watcher; it does not initialize
Citry. Use the watcher only in development, and keep `engine.initialize()`
in production too.

## Enable in any other app

For any other stack, start the watcher from your development entry point
with `watch()`. It runs in the background and returns a handle you can wait
on and stop:

```python
from citry.reload import watch
from myapp import engine

handle = watch(engine)  # watches engine.settings.dirs
try:
    handle.wait()  # blocks until you stop it
except KeyboardInterrupt:
    handle.stop()
```

`watch()` and `reload_lifespan()` accept the same keyword options:

- `roots=`: the directories to watch, instead of the engine's `dirs`;
- `watcher=`: the file-watching backend (see the next section);
- `on_reload=`: a function to call after each batch of changes.

## Use a faster watcher

Citry can notice file changes three ways, and uses the best one installed:

- **watchfiles** (recommended): fast, and uses your operating system's
  file-change events. Install the `watcher-watchfiles` extra.
- **watchdog**: an alternative for projects that already use it. Install
  the `watcher-watchdog` extra.
- **polling**: checks the directories again on a timer. It needs nothing
  installed, but it is slower. Citry uses it when neither extra is
  installed.

```sh
pip install "citry[watcher-watchfiles]"
```

To pick a backend yourself, pass an instance from `citry.reload`, such as
`watch(engine, watcher=WatchfilesWatcher())`.

## Use `citry watch`

The `citry` command (see the [CLI reference](/advanced/cli/)) has a `watch`
subcommand. It reloads files only inside its own process, so it suits a
script that renders components in that same process. For a web server,
use one of the helpers above, which run inside the server.

```sh
citry watch --path components/
```

`--path` (or `-p`) names a directory to watch and can be repeated. Without
it, the command watches the engine's `dirs`. To use a specific Citry
instance instead of the default one, put `--app module:attribute` before
`watch`:

```sh
citry --app myproject.app:engine watch
```

It prints each reload until you press Ctrl-C:

```text
citry: watching for component file changes (Ctrl-C to stop)
reloaded /app/components/greeting.html (Greeting)
citry: stopped watching
```

The name in parentheses is the component Citry reset. It reads
`(no loaded component)` when no component has rendered from that file in
this process yet.

## Use your own watcher

Every helper above ends in one call on the [Citry][citry.Citry] instance:
`invalidate_file(path)`. If your app already runs a file watcher, call it
from there and skip Citry's watcher.

Take a [Component][citry.Component] whose template lives in a file:

```citry-html
<!-- components/greeting.html -->
<p>Hello, {{ name }}!</p>
```

```citry
from pathlib import Path

from citry import Citry, Component

BASE_DIR = Path(__file__).parent
engine = Citry(dirs=[BASE_DIR / "components"])


class Greeting(Component):
    citry = engine
    template_file = "greeting.html"

    def template_data(self, kwargs, slots):
        return {"name": "Ada"}


greeting = Greeting()

# The first render reads greeting.html and stores it.
print(greeting)

# After you edit greeting.html, drop the stored copy.
# The next render reads the file again.
engine.invalidate_file(BASE_DIR / "components" / "greeting.html")
print(greeting)
```

The second `print` shows your edited text. `invalidate_file` accepts a
string or a `Path` and returns the component classes it reset, here
`[Greeting]`. An empty list means no loaded component uses the file, so
your handler can fall back to something else, such as a restart.

Two related calls help when one path is not enough:

- `invalidate_all()` resets every component that has loaded a file, for a
  change you cannot tie to one path, such as a branch switch. It also
  returns the reset classes.
- `get_components_for_file(path)` returns the components that loaded a
  file without resetting them, so your handler can decide what to do.

## Use in development only

A reload clears only the process it runs in. With several worker
processes, each keeps its own copy, so an edit shows up one worker at a
time. Run a single process while you develop.

In production, do not run `citry watch` and do not add the framework
helpers.
