---
title: Migrate from Component.View
description: Port django-components Component.View handlers to typed Citry Events, then split HTTP verbs into named interactions.
---

# Migrate from Component.View

This guide is for django-components users whose components handle requests
with a nested `class View`, through methods such as `get()` and `post()`. It
shows how to move that code to Citry's server events in two steps: first keep
the verb methods as they are, then give each user action its own named
method.

Most of the shape carries over. The component still owns its request
handling, and a plain HTML form can still post to the component's own URL.
What changes most is the method body. In Citry, a **handler** is a public
method in the component's nested `class Events`, and the browser calls it by
name (see [Server events](/events/)). A handler does not read `request.POST`
or build an `HttpResponse`. It receives the form fields as a typed object,
and what it returns decides what the page does next.

The Citry examples assume the `citry_app` instance configured in
[Server events](/events/#configure-a-signing-secret-before-using-state)
and these imports:

```python
from typing import Any

from citry import Component
from citry.ext.events import ViewEvents, actions, event, get_event_url
```

## Syntax mapping

| Component.View | Citry |
|---|---|
| `class View: def post(...)` | First step: `class Events(ViewEvents): def post(...)` |
| Several operations inside one `post()` | One named handler per operation |
| `request.POST.get("name")` | A `data` parameter with a typed class |
| `request.user` | `request.native.user`, or a value from `_context` |
| `HttpResponse` with component HTML | Return the component |
| `HttpResponseRedirect(url)` | Return `actions.Redirect(url)` |
| `get_component_url(...)` | `self.events.url(name)` or `get_event_url(...)` |
| Handwritten fetch or htmx swap | `@c-*` attribute plus `actions.Render(target=...)` |
| Full-page reload after a change | Re-render one part of the page, or redirect |

The sections below show the common rows in context.

## Fix dynamic attributes

When you copy a template over, check its attributes first. Citry treats an
ordinary HTML attribute value as a literal string, so the Django spelling
leaves the braces in the page:

```citry-html
<!-- Wrong in a Citry template: the href contains literal braces. -->
<a href="{{ detail_url }}">Details</a>
```

Prefix the attribute with `c-`, and Citry evaluates its value as a Python
expression:

```citry-html
<!-- Right: detail_url is evaluated during the component render. -->
<a c-href="detail_url">Details</a>
```

The same applies to `action`, `src`, `class`, and any other attribute. Text
between tags still uses `{{ expression }}`. See
[Attributes](/syntax/dynamic-attributes/#c-dynamic-attributes).

## Port a verb method

A typical `Component.View` form reads the host request and builds the HTTP
response itself:

```citry
class ContactForm(Component):
    class View:
        def post(self, request):
            name = request.POST.get("name", "stranger")
            return ThankYouMessage.render_to_response(
                kwargs={"name": name},
            )
```

For the first step, make the nested class `class Events(ViewEvents)`.
`ViewEvents` keeps the verb names: `post` still answers POST requests, at a
URL that ends with the ID Citry gives the component class, so the form does
not need to name a handler. The `data` parameter receives the form fields, checked
against `ContactIn`:

```citry
--8<-- "docs_site/snippets/migrate_component_view.py:view-events"
```

The handler returns `ThankYouMessage`, and Citry sends its rendered HTML as
the whole response to the form post.

Only the URL carries over unchanged. Update each method body by hand:

- Replace `request.POST` and `request.GET` parsing with a typed `data` class.
  See [Handle and validate forms](/events/forms/).
- For facts such as the current user or a header, add a `request`
  parameter. It is Citry's request object, which looks the same under every
  web framework, and `request.native` is the Django request itself. A
  `_context` method on `class Events` can load shared values such as the
  user once; see [Authorize every event](/security/#authorize-every-event).
- Return a component, `actions.Render`, `actions.Redirect`, or a `dict`
  instead of building a response. See [Event actions](/events/actions/).
- Leave `state` out of verb methods. State is the set of values Citry keeps
  for a component between calls. Citry raises `ValueError` when a verb
  method declares it. Values that must survive between calls belong in a
  named handler, as described in [Event state](/events/state/).

!!! warning "Add the CSRF token to every plain form"

    The forms on this page leave out the CSRF token to stay short. Django's
    CSRF middleware still applies to Citry's routes, so a real form needs
    `{% csrf_token %}` or the equivalent `csrfmiddlewaretoken` field. See
    [Protect event posts from CSRF](/security/#protect-event-posts-from-csrf).

## Name each operation

Once the form works, rename its operation after what the user does. One
`submit` handler can serve both the Citry browser code and a plain form post:

```citry
--8<-- "docs_site/snippets/migrate_component_view.py:named-event"
```

`@c-submit.prevent="submit"` is an event binding: an `@c-<event>` attribute
calls the handler when that browser event fires (see
[Bind events in templates](/events/bindings/)). With JavaScript, the browser
sends the form fields to `submit` without leaving the page. The handler
returns `actions.Render` with `target="mark:result"`, which puts the thank-you
message into the `<c-mark name="result">` region and leaves the rest of the
form alone.

Without JavaScript, the browser posts to `submit_url` instead, and Citry
turns the same return value into an HTML response.

`self.events.url("submit")` builds that URL while the component renders.
Outside the component, use `get_event_url(NamedContactForm, "submit")`. Both
accept `query=` and `fragment=`.

## Split query branches

A `get()` that branches on `?type=preview` or `?type=details` hides several
operations behind one URL:

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

Declare one handler per operation instead. `@event(methods=("GET",))` lets a
handler answer GET requests:

```citry
--8<-- "docs_site/snippets/migrate_component_view.py:named-fragments"
```

Each handler now has its own URL, allowed HTTP methods, input type, and entry
in Citry's [OpenAPI export](/events/routes/#expose-a-read-only-get-endpoint).
The component a handler returns brings its own JavaScript, CSS, and event
bindings with it, so there is no htmx or fetch code to wire it up.

## Plan for differences

### Authorize every record

As with a Django view, this stays your job. Citry does not turn an id in the request into a model instance, and it does
not let form data choose which method runs. Each handler declares its name
and input type. Load records from the validated ids inside the handler, and
check the current user's permission there, every time. See
[Authorize every event](/security/#authorize-every-event).

### Retire ViewEvents later

`ViewEvents` lets you port a component that has one method per HTTP verb
without renaming anything. Add
named handlers next to the verb methods as you go. When the last verb method
is gone, change the base back to a plain `class Events`.

### Build the verb URL

The verb URL has no builder function, so the first example builds it with
`self.citry.build_url(...)`. `self.events.url("post")` builds a different
URL: the one for the handler named `post`.

## Finish the port

Before shipping a migrated component, check that:

- each handler is named after one user action;
- request fields arrive through a typed `data` class;
- every record lookup checks the current user's permission;
- plain forms that must work without JavaScript have `method="post"`, a
  `c-action` URL, and a CSRF token;
- each `actions.Render` targets the smallest part of the page that changes;
  and
- only named handlers use State, and it holds only what the next call needs.

The [Events migration parity matrix](/guides/events-migration-parity/)
compares the rest of Component.View's behavior with Citry. The
[Server events](/events/) guides cover the full API.
