---
title: Serve pages with FastAPI
url: https://citry.dev/v/0.6.0/getting-started/fastapi/
description: "Put a Citry component behind a FastAPI route and connect the browser to Citry's own routes."
---
# Serve pages with FastAPI

So far you rendered components to a file. A real app serves pages from a web
server, and a server is also what lets a click in the browser run Python. In
this step you serve the choice picker from the last step with
[FastAPI](https://fastapi.tiangolo.com/){: target="_blank" rel="noopener"}.
Its browser behavior keeps working, and Citry gets the routes it needs for
the [server events](/v/0.6.0/events/) in the next steps.

This tutorial uses FastAPI to keep the setup concrete. Citry also works
with:

- [FastAPI and Starlette](/v/0.6.0/advanced/web-frameworks/#fastapi-and-starlette)
- [Django](/v/0.6.0/advanced/web-frameworks/#django)
- [Flask](/v/0.6.0/advanced/web-frameworks/#flask)
- Other [ASGI or WSGI applications](/v/0.6.0/advanced/web-frameworks/#bare-asgi-and-wsgi).

You can switch to your framework after you finish the tutorial.

## Install FastAPI

FastAPI defines the application and its routes.
[Uvicorn](https://uvicorn.dev/){: target="_blank" rel="noopener"} runs that
application as a local web server. Inside an existing `uv` project, add both:


```sh
uv add fastapi uvicorn
```


Or, with pip:


```sh
python -m pip install fastapi uvicorn
```


## Set up Citry

A `Citry` instance holds your app's components and settings. Create a new
folder for this small app, and save this inside it as `citry_setup.py`:

```citry
import os

from citry import Citry

# New in this step: create one Citry instance for the whole app.
secret = os.environ.get("CITRY_SECRET")
if not secret:
    msg = "Set CITRY_SECRET before starting the app."
    raise RuntimeError(msg)

citry_app = Citry(secret=secret)

```

Every other file in the app imports this same
[`Citry`](/v/0.6.0/reference/citry/#citry-citry) instance, so the components, the rendered pages, and
Citry's browser routes all use the same settings.

The secret lets Citry detect when someone changes data that passes through
the browser. Citry uses it once you add [`State`](/v/0.6.0/reference/component/#citry-component-state) in a
later step, but `citry_setup.py` stops with an error when the secret is
missing, so set it now.

Create a random development secret in your current terminal:


```sh
export CITRY_SECRET="$(
  python -c 'import secrets; print(secrets.token_urlsafe(32))'
)"
```


In PowerShell, use:


```powershell
$env:CITRY_SECRET = python -c "import secrets; print(secrets.token_urlsafe(32))"
```


!!! warning "Keep the secret out of your source code"

    Read the secret from the environment so it never ends up in version
    control. In production, use a stable secret from your deployment's
    secret store, and give every worker of the app the same value.

## Create the page

Save this as `components.py`:

```citry
# New in this step: every component uses the app's Citry instance.
from citry_setup import citry_app

from citry import Component


class ChoiceButton(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <button
        class="choice-button"
        type="button"
        @click="$emit('select')"
      >
        Choose
        <span
          class="choice-button__label"
          v-text="label"
        ></span>
      </button>
    """

    js = """
      $component({
        props: {
          label: { type: String, required: true },
        },
        emits: ['select'],
      });
    """


class ChoicePicker(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="choice-picker">
        <p>
          Current choice:
          <output
            class="choice-picker__value"
            v-text="choice"
          ></output>
        </p>

        <c-ChoiceButton
          :label="choice"
          @select="toggleChoice"
        />
      </section>
    """

    js = """
      $component({
        data() {
          return { choice: 'Ocean' };
        },
        methods: {
          toggleChoice() {
            this.choice =
              this.choice === 'Ocean' ? 'Forest' : 'Ocean';
          },
        },
      });
    """


# New in this step: FastAPI will return this complete page.
class TutorialPage(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Reading room</title>
        </head>
        <body>
          <main>
            <h1>Reading room</h1>
            <c-ChoicePicker />
          </main>
        </body>
      </html>
    """

```

The `New in this step` comments mark what changed from the browser-only
version. Each existing component gets one new line:


```citry
class ChoiceButton(Component):
    citry = citry_app
    ...
```


[`Component.citry`](/v/0.6.0/reference/component/#citry-component-citry) tells the class which Citry
instance it belongs to. The new `TutorialPage` component is the complete
HTML page that FastAPI will return.

## Create the FastAPI app

Save this as `app.py` beside the other two files. The whole file is new, and
its `New in this step` comments mark the three places where FastAPI and
Citry meet.

```citry
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from citry_setup import citry_app
from components import TutorialPage
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from citry.contrib.fastapi import mount


# New in this step: initialize Citry before serving requests.
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    citry_app.initialize()
    yield


app = FastAPI(lifespan=lifespan)


# New in this step: render a Citry page from a regular route.
@app.get("/")
def home() -> HTMLResponse:
    page = TutorialPage()
    html = str(page)
    return HTMLResponse(html)


# New in this step: add Citry's browser and event routes.
mount(app, citry_app)

```

The next three sections walk through those places.

### Initialize at startup


```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    citry_app.initialize()
    yield

app = FastAPI(lifespan=lifespan)
```


FastAPI runs this
[lifespan](https://fastapi.tiangolo.com/advanced/events/){: target="_blank" rel="noopener"}
function once when the app starts.
[`citry_app.initialize()`](/v/0.6.0/reference/citry/#citry-citry-initialize) gets the components ready
before the first request arrives. The `yield` hands control back to FastAPI
so it can serve requests.

Importing `TutorialPage` at the top of `app.py` runs the class definitions in
`components.py`, so every component already belongs to `citry_app` when
`initialize()` runs.

### Return the page

`home` is an ordinary FastAPI route. It renders `TutorialPage` to a string
and returns it as HTML:


```python
@app.get("/")
def home() -> HTMLResponse:
    page = TutorialPage()
    html = str(page)
    return HTMLResponse(html)
```


`HTMLResponse` tells FastAPI and the browser that the string is an HTML
document. If you returned the plain string, FastAPI would send it as JSON.
Your existing routes can return Citry pages the same way.

### Add Citry's routes

The last line adds Citry's own routes to the FastAPI app:


```python
mount(app, citry_app)
```


[`mount(app, citry_app)`](/v/0.6.0/reference/contrib/#citry-contrib-fastapi-mount) puts them under
`/citry` by default. The page loads Citry's browser code from these routes,
and in the next steps, clicks use them to call Python.

## Start the app

Run Uvicorn from the folder that holds the three files:


```sh
uv run uvicorn app:app --reload
```


If you installed with pip, run:


```sh
python -m uvicorn app:app --reload
```


In `app:app`, the first `app` is the file `app.py`, and the second is the
FastAPI object inside it. `--reload` restarts the server when you save a
change.

Visit `http://127.0.0.1:8000/`. You see the choice picker on the
“Reading room” page. Click its button, and “Ocean” changes to “Forest,” just
as it did without a server.

To confirm that Citry's routes work, visit
`http://127.0.0.1:8000/citry/citry.js`. You should see JavaScript.

## Next steps

The page and Citry now run on one server. Next, [call Python from a
click](/getting-started/call-python/).

To use another framework, the [Web frameworks](/v/0.6.0/advanced/web-frameworks/) guide shows
the matching setup for Django, Flask, Starlette, and plain ASGI or WSGI apps.