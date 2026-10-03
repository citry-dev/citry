---
title: Event routes
description: Call Citry event handlers by URL from plain HTML forms, htmx, and GET requests.
---

# Event routes

Every event handler has its own URL. Citry's browser code calls it for you,
but you can also call it yourself: from a plain HTML form that must work
without JavaScript, from htmx, or from other code that reads data with a
GET request. To send a file from a handler, see
[`Download` a file](/events/actions/#download-a-file).

## Protect every handler

Anyone can send a request to a handler's URL, with any arguments. Check the
current user's permissions in every handler, and load records by id rather
than trusting values from the browser. State is signed, so it cannot be
forged, but anyone can read it, and fields the browser may change can hold
any value.

Set up your web framework's CSRF protection as described in
[Security](/security/#protect-event-posts-from-csrf).

## Post a plain form { #keep-a-form-working-without-javascript }

A plain HTML form keeps working when JavaScript is off or has not loaded
yet. Point its `action` at the handler's URL.
[`self.events.url()`][citry.Events.url] builds the URL while the component
renders, and [`get_event_url()`][citry.ext.events.get_event_url] builds it
outside a render:

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

## Allow GET requests { #expose-a-read-only-get-endpoint }

Allow GET on a handler that only reads data, with the `methods` option of
[`@event()`][citry.ext.events.event]. Browser code and other servers
can then call its URL, and Citry's
[OpenAPI export](/cli/#run-an-extension-command) describes it:

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

Build the URL while rendering with
[`self.events.url("summary")`][citry.Events.url], or elsewhere with
[`get_event_url()`][citry.ext.events.get_event_url]. A GET handler must
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
