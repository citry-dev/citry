---
title: Use event routes directly
description: Call Citry event handlers through GET requests, native forms, htmx, and dedicated download responses.
---

# Use event routes directly

Every event handler has its own URL. Citry's browser code calls it for you,
but you can also call it yourself: from a plain HTML form that must work
without JavaScript, from htmx, from other code that reads data with a GET
request, or to download a file.

## Protect every handler like an HTTP endpoint

Anyone can send a request to a handler's URL, with any arguments. Check the
current user's permissions in every handler, and load records by id rather
than trusting values from the browser. State is signed, so it cannot be
forged, but anyone can read it, and fields the browser may change can hold
any value.

Set up your web framework's CSRF protection as described in
[Security](/security/#protect-event-posts-from-csrf).

## Keep a form working without JavaScript

Point a plain form's `action` at the handler's URL. `self.events.url()` builds
it while the component renders:

```citry
from citry.ext.events import actions


class SignupIn:
    email: str


class Signup(Component):
    citry = citry_app

    class Events:
        def submit(self, data: SignupIn):
            create_account(data.email)
            return actions.Redirect("/welcome")

    def template_data(self, kwargs, slots):
        return {"submit_url": self.events.url("submit")}

    template = """
      <form method="post" c-action="submit_url">
        <input name="email">
        <button type="submit">Sign up</button>
      </form>
    """
```

The response depends on what the handler returns: HTML for a component, a
real HTTP redirect for `actions.Redirect`, or JSON for data. htmx can post to
the same URL and swap in the returned HTML.

## Download a file from one event

Return [`actions.Download`][citry.ext.events.actions.Download] on its own, and
mark the handler with `@event(bundle=False)`:

```python
from citry.ext.events import actions, event


class Events:
    @event(bundle=False)
    def export_orders(self):
        return actions.Download(
            make_orders_csv(),
            "orders.csv",
            content_type="text/csv; charset=utf-8",
        )
```

The file is the whole HTTP response. By default, the browser may send several
calls in one request; `bundle=False` makes it send this call on its own.

Call the handler as usual, from `@c-*`, `$sendEvent`, or
[`Citry.events.send`][Citry.events.send]. The Promise resolves with
`undefined` once the browser starts saving the file.

A download cannot be combined with other actions in a list, and its handler
must not change State. The file response has no room for the new State.

## Expose a read-only GET endpoint

Allow GET on a handler that only reads data. Browser code, server
middleware, and the Events OpenAPI command can then use its URL:

```citry
from citry.ext.events import event


class Stats(Component):
    citry = citry_app

    class Events:
        @event(methods=("GET",))
        def summary(self) -> dict:
            return {
                "users": count_users(),
                "active_today": count_active(),
            }
```

Build the URL while rendering with `self.events.url("summary")`, or elsewhere
with [`get_event_url()`][citry.ext.events.get_event_url]. A GET handler must
not change anything on the server. Its arguments arrive in the query string,
which holds strings, booleans, numbers, and non-empty lists of those.

!!! note "Which HTTP methods a handler accepts"

    `methods` accepts `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`, and
    `OPTIONS`. Any other method raises `ValueError` when the class is
    defined. A request with a method the handler does not accept gets a
    `405` response that lists the accepted ones.

    Citry's browser code cannot call a handler whose first method is `HEAD`
    or `OPTIONS`; it raises an error before sending. Call such a handler
    from a server-side HTTP client.
