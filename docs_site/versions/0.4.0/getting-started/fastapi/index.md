---
title: Serve pages with FastAPI
url: https://citry.dev/v/0.4.0/getting-started/fastapi/
description: "Put a Citry component behind a FastAPI route and connect the browser to Citry's own routes."
---
# Serve pages with FastAPI

The components you have built so far can render without a web server. Now you
will put the choice picker from the last step behind [FastAPI](https://fastapi.tiangolo.com/){: target="_blank" rel="noopener"}. Its browser
behavior will keep working, and Citry will gain a place to receive the [server
events](/events/) in the next steps.

This tutorial uses FastAPI to keep the setup concrete.
Citry comes with integrations for:

- [FastAPI / Starlette](/v/0.4.0/web-frameworks/#fastapi-and-starlette)
- [Django](/v/0.4.0/web-frameworks/#django)
- [Flask](/v/0.4.0/web-frameworks/#flask)
- Other [ASGI or WSGI applications](/v/0.4.0/web-frameworks/#bare-asgi-and-wsgi).

You can switch to your framework after you finish this journey.

## Install the packages

Inside an existing `uv` project, add
[FastAPI](https://fastapi.tiangolo.com/){: target="_blank" rel="noopener"}
and
[Uvicorn](https://uvicorn.dev/){: target="_blank" rel="noopener"}:


```sh
uv add fastapi uvicorn
```


Or, with pip:


```sh
python -m pip install fastapi uvicorn
```


FastAPI provides the application and its routes. Uvicorn runs that application
as a local web server.

## Create Citry instance

Create a new folder for this small app. Inside it, save the following as
`citry_setup.py`:

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

The other files in this small app import the same
[`Citry`](/v/0.4.0/reference/citry/#citry-citry) instance. That keeps its components, rendered pages,
and mounted browser routes together.

The secret lets Citry detect changes to data that travels through the browser.
You will use that feature when you add [`State`](/v/0.4.0/reference/component/#citry-component-state).

!!! warning

    Keep the secret outside of your
    source code so it does not end up in version control.

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


Use a stable secret from your deployment's secret store in production. All
workers for the same app need the same value.

## Create the page

Save this next file as `components.py`:

Look for the `New in this step` comments. Compared with the browser-only
version, this file now:

- imports the shared `citry_app` and assigns it to every component; and
- exposes `TutorialPage`, the full page that the FastAPI route will render.

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
      <button class="choice-button" type="button">
        Choose
        <span
          class="choice-button__label"
          x-text="clientProps.label"
        ></span>
      </button>
    """

    js = """
      $component({
        props: {
          label: { type: String, required: true },
        },
        init: ({ props, scope }) => {
          scope.clientProps = props;
        },
      });
    """


class ChoicePicker(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="choice-picker" x-data="{ choice: 'Ocean' }">
        <p>
          Current choice:
          <output
            class="choice-picker__value"
            x-text="choice"
          ></output>
        </p>

        <c-ChoiceButton
          $c-props="{ label: choice }"
          @click="choice = choice === 'Ocean' ? 'Forest' : 'Ocean'"
        />
      </section>
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

## Connect components with Citry

The complete file above repeats one new line on every component. Here is the
same change with the unchanged parts folded away:


```citry
class ChoiceButton(Component):
    citry = citry_app
    ...

class ChoicePicker(Component):
    citry = citry_app
    ...

class TutorialPage(Component):
    citry = citry_app
    ...
```


[`Component.citry`](/v/0.4.0/reference/component/#citry-component-citry) tells each class which Citry
instance owns it. `ChoiceButton` and `ChoicePicker` keep the browser behavior
you already built. `TutorialPage` gives the FastAPI route one complete page to
return.

## Create the FastAPI app

Save this as `app.py` beside the other two files:

This whole file is new. Its `New in this step` comments mark the three
connections between FastAPI and Citry.

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
    page = str(TutorialPage())
    return HTMLResponse(page)


# New in this step: add Citry's browser and event routes.
mount(app, citry_app)

```

## Load the components

The two local imports in the file above connect the page to the same Citry instance:


```python
from citry_setup import citry_app
from components import TutorialPage
```


Importing `TutorialPage` runs the class definitions in `components.py`. Those
classes register with `citry_app`, so they are present before the application
starts serving requests.

## Initialize Citry when FastAPI starts

FastAPI calls the [lifespan](https://fastapi.tiangolo.com/advanced/events/){: target="_blank" rel="noopener"} function once when the application starts:


```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    citry_app.initialize()
    yield

app = FastAPI(lifespan=lifespan)
```


[`citry_app.initialize()`](/v/0.4.0/reference/citry/#citry-citry-initialize) prepares the registered
components before requests can arrive. The `yield` hands control back to
FastAPI so it can run the application.

## Define FastAPI endpoint

`home` is a regular FastAPI route. Inside it, we build `TutorialPage`, render it to a string, and returns that
string as HTML:


```python
@app.get("/")
def home() -> HTMLResponse:
    page = str(TutorialPage())
    return HTMLResponse(page)
```


A larger application can render a Citry
page from its existing routes in the same way. `HTMLResponse` tells FastAPI and
the browser that the returned string is an HTML document. Returning the plain
string directly would make FastAPI encode it as a JSON string.

## Mount Citry's routes

The final line gives Citry its own routes inside the FastAPI application:


```python
mount(app, citry_app)
```


[`mount(app, citry_app)`](/v/0.4.0/reference/contrib/#citry-contrib-fastapi-mount) uses `/citry` by
default. The rendered page uses those routes to load Citry's browser code. Passing the same
`citry_app` keeps those routes connected to the components you initialized.

In the next lessons will use these routes to reach components' server-side event handlers.

## Start the app

Run Uvicorn from the folder containing the three files:


```sh
uv run uvicorn app:app --reload
```


In `app:app`, the first `app` names `app.py` and the second names the FastAPI
object inside that file. `--reload` restarts the local server when you save a
change.

If you installed with pip, run:


```sh
python -m uvicorn app:app --reload
```


Visit `http://127.0.0.1:8000/`. You should see the choice picker inside the
“Reading room” page. Click its button and watch “Ocean” change to “Forest,”
just as it did without a server.

You can also visit `http://127.0.0.1:8000/citry/citry.js`. Seeing JavaScript at
that address confirms that the Citry routes are mounted.

The [Web frameworks](/v/0.4.0/web-frameworks/) guide shows the matching setup for
Django, Flask, Starlette, and bare ASGI or WSGI apps.

## Next steps

The page and Citry now share one running server. Next, [call
Python from a click](/getting-started/call-python/).