---
title: Migrate from Component.View
url: https://citry.dev/v/0.4.1/guides/migrate-from-component-view/
description: "Port django-components Component.View handlers to typed Citry Events, then split HTTP verbs into named interactions."
---
# Migrate from Component.View

If one component's `post()` now inspects a flag to decide whether to save,
archive, or preview, the HTTP verb has become a second router. Citry Events lets
the initial verb-shaped handler keep working, then lets you move each operation
to a named, typed handler without changing component ownership.

The mental-model shift is small: a component still owns its HTTP behavior, but
the public operation is named after what the user does. Handlers return page
effects such as a render, browser event, redirect, or JSON value.

The Citry examples assume the configured `citry_app` from
[Server events](/v/0.4.1/events/#configure-a-signing-secret-before-using-state)
and these imports:


```python
from typing import Any

from citry import Component
from citry.ext.events import ViewEvents, actions, event, get_event_url
```


## Start with the verb compatibility route

A typical `Component.View` form reads the host request and constructs an HTTP
response itself:


```citry
class ContactForm(Component):
    class View:
        def post(self, request):
            name = request.POST.get("name", "stranger")
            return ThankYouMessage.render_to_response(kwargs={"name": name})
```


For the first port, subclass `ViewEvents`. The HTTP method still selects
`post`, while `data` is parsed and validated from the form fields. Returning a
`Render` describes where the new fragment belongs:


```citry
class ThankYouMessage(Component):
    citry = citry_app

    class Kwargs:
        name: str

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"name": kwargs.name}

    template = """
      <p id="thank-you">
        Thank you, {{ name }}!
      </p>
    """


class ContactIn:
    name: str = "stranger"


class ContactForm(Component):
    citry = citry_app

    class Events(ViewEvents):
        def post(self, data: ContactIn):
            return actions.Render(
                ThankYouMessage(name=data.name),
                target="#result",
                swap="inner",
            )

    def template_data(self, kwargs, slots) -> dict[str, Any]:
        submit_url = self.citry.build_url(f"ext/events/e/{type(self).class_id}")
        return {"submit_url": submit_url}

    template = """
      <form method="post" c-action="submit_url">
        <input name="name">
        <button type="submit">Send</button>
      </form>
      <div id="result"></div>
    """


```


The compatibility URL ends at the component class id, so a native POST can
reach it without naming an event. This is the mechanical bridge used by a form
that is not running JavaScript.

The native forms in this guide omit host-specific CSRF markup for brevity.
They are not deployable without it: include the host's normal form token, such
as Django's `csrfmiddlewaretoken`, because host middleware still applies. See
[Protect event posts from CSRF](/v/0.4.1/security/#protect-event-posts-from-csrf).

Only the route shape is mechanical. Update each old handler body deliberately:

- Replace `request.POST` and `request.GET` parsing with a typed `data` class.
- Use the framework-neutral `request` injectable only for facts such as the
  current user, headers, or the host request under `request.native`.
- Return a component, `actions.Render`, `actions.Redirect`, or JSON data rather
  than constructing a host response.
- Keep State out of verb handlers. The token-optional compatibility route does
  not inject `state`; stateful interactions belong in named handlers.

## Name the operation after the user action

Once the form works, make its public operation `submit`. The same handler can
serve the Citry client and a native form fallback through its per-event URL:


```citry
class NamedContactForm(Component):
    citry = citry_app

    class Events:
        def submit(self, data: ContactIn):
            return actions.Render(
                ThankYouMessage(name=data.name),
                target="#result",
                swap="inner",
            )

    def template_data(self, kwargs, slots) -> dict[str, Any]:
        return {"submit_url": self.events.url("submit")}

    template = """
      <form
        method="post"
        c-action="submit_url"
        @c-submit.prevent="submit"
      >
        <input name="name">
        <button type="submit">Send</button>
      </form>
      <div id="result"></div>
    """


```


With JavaScript, `@c-submit.prevent` sends the typed call and applies the render
without navigation. Without JavaScript, the browser posts to `submit_url` and
the server translates the same render result into an HTML response. That
native post also needs the host's normal CSRF form token.

Use `self.events.url("submit")` during rendering, or
`get_event_url(ContactForm, "submit")` outside the component. Both builders
also accept `query=` and `fragment=`.

## Replace query multiplexing with named handlers

A `get()` that branches on `?type=preview` or `?type=details` hides several
operations behind one endpoint:


```citry
class FragmentLoader(Component):
    class View:
        def get(self, request):
            kind = request.GET.get("type")
            if kind == "preview":
                return render_preview()
            if kind == "details":
                return render_details()
            return render_page()
```


Declare one handler per operation. Each gets its own URL, method policy,
schema, OpenAPI operation, and middleware path:


```citry
class LoadedFragment(Component):
    citry = citry_app

    class Kwargs:
        kind: str

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, Any]:
        return {"kind": kwargs.kind}

    template = """
      <section class="loaded-fragment">
        Loaded {{ kind }}
      </section>
    """


class FragmentLoader(Component):
    citry = citry_app

    class Events:
        @event(methods=("GET",))
        def preview(self):
            return actions.Render(
                LoadedFragment(kind="preview"),
                target="#fragment-target",
                swap="inner",
            )

        @event(methods=("GET",))
        def details(self):
            return actions.Render(
                LoadedFragment(kind="details"),
                target="#fragment-target",
                swap="inner",
            )

    template = """
      <nav>
        <button @c-click="preview">Preview</button>
        <button @c-click="details">Details</button>
      </nav>
      <div id="fragment-target"></div>
    """


```


Returning a Citry fragment activates its component JavaScript, CSS, Alpine
scope, and Events bindings through one lifecycle. There is no separate htmx or
fetch activation step to maintain.

## Translate dynamic HTML attributes

Citry treats an ordinary HTML attribute value as a literal string. The Django
template spelling therefore leaves braces in the browser:


```html
<!-- Wrong in a Citry template: the href contains literal braces. -->
<a href="{{ detail_url }}">Details</a>
```


Prefix a dynamic attribute with `c-` so Citry evaluates the Python expression:


```html
<!-- Right: detail_url is evaluated during the component render. -->
<a c-href="detail_url">Details</a>
```


This rule applies to `action`, `src`, `class`, and other dynamic attributes as
well as `href`. Text content still uses `{{ expression }}`.

## Syntax mapping

| Component.View pattern | Citry Events spelling |
|---|---|
| `class View: def post(...)` | Initial port: `class Events(ViewEvents): def post(...)` |
| Several operations inside `post()` | One named method per operation in `class Events` |
| `request.POST.get("name")` | `data: ContactIn`, validated from the request |
| `request.user` | `request` or an authenticated `_context` value |
| `HttpResponse(component_html)` | Return the component or `actions.Render(...)` |
| `HttpResponseRedirect(url)` | `actions.Redirect(url)` |
| `get_component_url(...)` | `self.events.url(name, query=..., fragment=...)` |
| Handwritten fetch or htmx target | `@c-*` plus `actions.Render(target=...)` |
| Full-page reload after mutation | Targeted render or redirect, chosen by the handler |

## Keep the public boundary narrow

Citry deliberately asks each operation to declare its name and input shape.
It does not revive arbitrary ORM objects from primary-key arguments, expose
host request parsing as the handler contract, or treat a method name supplied
in form data as a dispatcher. Those shortcuts make authorization difficult to
audit. Load records from validated ids and authorize them inside every
handler.

`ViewEvents` is a bridge, not a second permanent API. Keep it while a
component is still genuinely verb-shaped. Add named methods beside its verbs,
then use a plain `Events` class when the last compatibility handler is gone.

## Finish the port

Before shipping a migrated component, check that:

- each handler has one action-shaped name;
- request fields are represented by a typed `data` class;
- every record lookup repeats authorization for the current request;
- native forms have a real `method` and dynamic `c-action` URL when they need
  a no-JavaScript path;
- render actions name the smallest target that should change; and
- State is used only by named handlers and contains the minimum durable input
  needed for the next call.

Continue with the [Events guides](/v/0.4.1/events/) for the full API, or use the
[Events migration parity matrix](/v/0.4.1/guides/events-migration-parity/) to
compare the remaining Component.View behavior with the other migration paths.