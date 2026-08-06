---
title: Server events
description: Call a Python event handler from a Citry component and update the page without reloading it.
---

# Server events

When a click or form submit needs Python, Citry can call a named handler on
the component and apply its result without reloading the page. You write the
handler, declare the small amount of [`State`][citry.Component.State] that may
travel through the browser, and choose what the response should do.

Events is built in. There is no extension to install. Pages that use it load
the client runtime automatically.

## Configure a signing secret before using State

By default, State travels through the browser in a signed token. Give your
Citry instance a long random secret, then register and mount that same
instance:

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

Django projects can pass `citry.contrib.django.secret()` to reuse Django's
configured secret. Stateless handlers do not mint a State token, but using one
configured instance consistently keeps stateful components ready. See
[Web frameworks](/web-frameworks/) for the other mounting adapters.

## Call Python from a button

The smallest server interaction is a public method inside `class Events`. The
template's `@c-click` value names it:

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

Clicking the button calls `increment` on the server. Returning a component
element renders a fresh component tree and morphs it over the calling instance,
so the button text changes without a page reload.

Every public method declared on the component's own [`Events`][citry.Component.Events] class is callable.
An underscore-prefixed method is a private helper or configuration hook.

## Choose your next step

- [Keep State between calls](/events/state/) when a later handler needs values
  from the current component.
- [Handle and validate forms](/events/forms/) when named controls should become
  typed Python data.
- [Bind events in templates](/events/bindings/) for `@c-*`, `:c-*`, polling,
  loading feedback, and errors.
- [Event actions](/events/actions/) for renders, browser
  events, history changes, and stable update targets.
- [Use event routes directly](/events/http/) for GET handlers, native forms,
  htmx, downloads, and endpoint security.

## Coming from another server-component library?

Each migration guide starts from the source library's own mental model and
ends at the same Events contract:

- [Component.View](/guides/migrate-from-component-view/) begins with the
  verb-shaped compatibility route, then moves to named handlers.
- [django-unicorn](/guides/migrate-from-django-unicorn/) maps public State,
  model bindings, validation, and browser calls.
- [Tetra](/guides/migrate-from-tetra/) maps public methods, promise results,
  Alpine behavior, and the client callback channel.
- [livecomponents](/guides/migrate-from-livecomponents/) uses a two-step State
  migration: server-held first, signed per component when appropriate.

Use the [Events migration parity matrix](/guides/events-migration-parity/) to
check uploads, history, server push, and other capabilities before porting a
component that depends on them.
