---
title: Serve pages with FastAPI
description: Put a Citry component behind a FastAPI route and connect the browser to Citry's own routes.
---

# Serve pages with FastAPI

So far you rendered components to a file. A real app serves pages from a web
server, and a server is also what lets a click in the browser run Python. In
this step you serve the choice picker from the last step with
[FastAPI](https://fastapi.tiangolo.com/){: target="_blank" rel="noopener"}.
Its browser behavior keeps working, and Citry gets the routes it needs for
the [server events](/events/) in the next steps.

This tutorial uses FastAPI to keep the setup concrete. Citry also works
with:

- [FastAPI / Starlette](/web-frameworks/#fastapi-and-starlette)
- [Django](/web-frameworks/#django)
- [Flask](/web-frameworks/#flask)
- Other [ASGI or WSGI applications](/web-frameworks/#bare-asgi-and-wsgi).

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

<c-include-file path="docs_site/snippets/getting_started/citry_setup.py" language="citry" />

Every other file in the app imports this same
[`Citry`][citry.Citry] instance, so the components, the rendered pages, and
Citry's browser routes all use the same settings.

The secret lets Citry detect when someone changes data that passes through
the browser. Citry uses it once you add [`State`][citry.Component.State] in a
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

<c-include-file path="docs_site/snippets/getting_started/components_step8.py" language="citry" />

The `New in this step` comments mark what changed from the browser-only
version. Each existing component gets one new line:

```citry
class ChoiceButton(Component):
    citry = citry_app
    ...
```

[`Component.citry`][citry.Component.citry] tells the class which Citry
instance it belongs to. The new `TutorialPage` component is the complete
HTML page that FastAPI will return.

## Create the FastAPI app

Save this as `app.py` beside the other two files. The whole file is new, and
its `New in this step` comments mark the three places where FastAPI and
Citry meet.

<c-include-file path="docs_site/snippets/getting_started/app.py" language="citry" />

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
[`citry_app.initialize()`][citry.Citry.initialize] gets the components ready
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
    page = str(TutorialPage())
    return HTMLResponse(page)
```

`HTMLResponse` tells FastAPI and the browser that the string is an HTML
document. If you returned the plain string, FastAPI would send it as JSON.
Your existing routes can return Citry pages the same way.

### Add Citry's routes

The last line adds Citry's own routes to the FastAPI app:

```python
mount(app, citry_app)
```

[`mount(app, citry_app)`][citry.contrib.fastapi.mount] puts them under
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

To use another framework, the [Web frameworks](/web-frameworks/) guide shows
the matching setup for Django, Flask, Starlette, and plain ASGI or WSGI apps.
