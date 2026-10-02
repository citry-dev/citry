---
title: Server events
description: Call a Python event handler from a Citry component and update the page without reloading it.
---

# Server events

Some clicks and form submits need Python: save a record, run a query, check a
permission. Server events let a button in your component call a Python method
on that component, then update the page with the result. The page does not
reload, and you write no JavaScript or API endpoint.

Events are built in. There is nothing to install, and pages that use them load
the browser code automatically.

## Call Python from a button

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

[`State`][citry.Component.State] holds the values the next call needs, here
the current count. Citry sends it to the browser and back with each call.

Every public method on [`Events`][citry.Component.Events] can be called from
the browser. A method whose name starts with an underscore cannot, so use that
for helpers.

## Configure a signing secret before using State

Citry signs State before sending it to the browser, so it can detect when
someone changes it. Signing needs a secret. Rendering a component that has
State without one raises an error.

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

In Django, pass `citry.contrib.django.secret()` to reuse Django's own secret.
[Web frameworks](/web-frameworks/) shows how to mount Citry in other
frameworks.

## Choose your next step

- [Keep State between calls](/events/state/): decide which values survive
  from one call to the next.
- [Handle and validate forms](/events/forms/): receive form fields as typed
  Python data and show validation errors.
- [Bind events in templates](/events/bindings/): call handlers on any DOM
  event, connect inputs to State, and show loading and errors.
- [Event actions](/events/actions/): decide what happens after the handler
  runs, such as re-rendering, notifying other code, or redirecting.
- [Use event routes directly](/events/http/): call handlers by URL from
  plain HTML forms, htmx, or downloads.

## Coming from another server-component library?

Each migration guide starts from how the other library works and shows the
Citry equivalent:

- [Component.View](/guides/migrate-from-component-view/)
- [django-unicorn](/guides/migrate-from-django-unicorn/)
- [Tetra](/guides/migrate-from-tetra/)
- [livecomponents](/guides/migrate-from-livecomponents/)

Before porting a component that uploads files, changes browser history, or
receives updates pushed from the server, check the
[Events migration parity matrix](/guides/events-migration-parity/).
