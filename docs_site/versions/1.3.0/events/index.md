---
title: Server events
url: https://citry.dev/v/1.3.0/events/
description: "Call a Python event handler from a Citry component and update the page without reloading it."
---
# Server events

Some clicks and form submits need Python: save a record, run a query, check a
permission. Server events let a button in your component call a Python method
on that component, then update the page with the result. The page does not
reload, and you write no JavaScript or API endpoint.

Events are built in. There is nothing to install, and pages that use them load
the browser code automatically.

## Call Python on click

Put the method in a nested `class Events`, and name it in an `@c-click`
attribute:


```citry
from citry import Component


class Counter(Component):
    citry = citry_app

    class Kwargs:
        count: int = 0

    class State(Kwargs):
        pass

    class Events:
        def increment(self, state):
            state.count += 1
            return Counter(count=state.count)

    def template_data(self, kwargs, slots):
        return {"count": kwargs.count}

    template = """
      <button @c-click="increment">
        Clicked {{ count }} times
      </button>
    """
```


Clicking the button calls `increment` on the server. The handler returns a new
`Counter`, and Citry renders it and puts it in place of the old one, so the
button text changes.

[`State`](/v/1.3.0/reference/component/#citry-component-state) holds the values the next call needs, here
the current count. Citry sends it to the browser and back with each call.
`citry_app` needs a signing secret for this, as the next section shows.

Every public method on [`Events`](/v/1.3.0/reference/component/#citry-component-events) can be called from
the browser. A method whose name starts with an underscore cannot, so use that
for helpers.

## Set a signing secret

By default, Citry signs State before sending it to the browser, so it can
detect when someone changes it. Signing needs a secret. Rendering a component
that has State without one raises an error.

Give your Citry instance a long random secret, then register and mount that
same instance:


```python
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from citry import Citry
from citry.contrib.fastapi import mount

citry_app = Citry(secret=os.environ["CITRY_SECRET"])


@asynccontextmanager
async def lifespan(_app):
    citry_app.initialize()
    yield


web_app = FastAPI(lifespan=lifespan)
mount(web_app, citry_app)
```


[Web frameworks](/v/1.3.0/advanced/web-frameworks/) shows how to mount Citry in other
frameworks.

### Use Django's secret key

In Django, pass `citry.contrib.django.secret()` to reuse Django's own secret.
When you rotate Django's key with `SECRET_KEY_FALLBACKS`, Citry follows the
rotation: `SECRET_KEY` signs new values, and a value signed with a fallback
key still verifies. Pages that visitors already have open keep working
until you remove the old key from the fallbacks.

### Rotate a secret

To rotate a secret of your own, pass a list. The first entry signs new
values, and Citry accepts a value signed with any entry. Pages that
visitors already have open keep working until you remove the old entry:


```python
keys = [
    os.environ["CITRY_SECRET"],
    os.environ.get("CITRY_OLD_SECRET"),
]
citry_app = Citry(secret=[key for key in keys if key])
```


The last line leaves out a key that is not set. An empty entry would let
anyone sign a value, so `Citry(...)` raises an error for an entry that is
empty or only whitespace.

### Rotate during a deploy

During a deploy, old and new workers can run at the same time. Rotate in
two deploys, so that every worker can check every value it receives:

1. Add the new secret as the second entry, and deploy. Every worker can
   now check values signed with it.
2. In a later deploy, move the new secret to the front, so it signs new
   values.

In Django, step 1 adds the new key to `SECRET_KEY_FALLBACKS`. Step 2 makes
it `SECRET_KEY` and moves the old key into `SECRET_KEY_FALLBACKS`.

If you skip step 1, a worker that does not have the new secret yet
treats State signed with that secret as out of date, and the page shows
the [out-of-date error](/v/1.3.0/reference/browser-apis/#out-of-date-pages). The
worker also answers 404 for the URL of a `css_data()` stylesheet (the
CSS Citry builds from a component's `css_data()` values) made with the
new secret.

## Choose your next step

- [Event state](/v/1.3.0/events/state/): decide which values survive
  from one call to the next.
- [Handle and validate forms](/v/1.3.0/events/forms/): receive form fields as typed
  Python data and show validation errors.
- [Bind events in templates](/v/1.3.0/events/bindings/): call handlers on any DOM
  event, connect inputs to State, and show loading and errors.
- [Event actions](/v/1.3.0/events/actions/): decide what happens after the handler
  runs, such as re-rendering, notifying other code, or redirecting.
- [Event routes](/v/1.3.0/events/routes/): call handlers by URL from plain HTML
  forms, htmx, or GET requests.

## Migrate from a library

Each migration guide starts from how the other library works and shows the
Citry equivalent:

- [Component.View](/v/1.3.0/guides/migrate-from-component-view/)
- [django-unicorn](/v/1.3.0/guides/migrate-from-django-unicorn/)
- [Tetra](/v/1.3.0/guides/migrate-from-tetra/)
- [livecomponents](/v/1.3.0/guides/migrate-from-livecomponents/)

Before porting a component that uploads files, changes browser history, or
receives updates pushed from the server, check the
[Events migration parity matrix](/v/1.3.0/guides/events-migration-parity/).