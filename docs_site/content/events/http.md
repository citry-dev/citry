---
title: Use event routes directly
description: Call Citry event handlers through GET requests, native forms, htmx, and dedicated download responses.
---

# Use event routes directly

Every Citry event handler has an HTTP route. The browser runtime normally calls
it for you, but the same route can serve a read-only request, a native form, an
htmx request, or a dedicated file download.

## Expose a typed read endpoint

Opt a handler into GET when it is read-only. It gets a real per-event URL that
browser code, host middleware, and the Events OpenAPI command can use:

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

Build a URL during rendering with `self.events.url("summary")`, or outside a
component with [`get_event_url()`][citry.ext.events.get_event_url]. GET handlers
must not mutate server state. Their flat query format accepts scalar strings,
booleans, finite numbers, and non-empty arrays of those values.

## Keep a form working without JavaScript

The same per-event route accepts a native form post. Use the component's URL
builder as a dynamic `action` attribute:

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

A native post receives HTML for a render result, a real HTTP redirect for a
redirect result, or JSON for a data result. Host CSRF middleware still applies.
htmx can post to the same URL and consume the fragment response.

## Download a file from one event

A download uses its event's HTTP response, so its handler must opt out of
bundling and return the download by itself:

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

Call the handler normally from `@c-*`, `$sendEvent`, or
[`Citry.events.send`][Citry.events.send]. The returned promise resolves with
`undefined` after the browser save starts. A download cannot share a return
list with actions or ride a batch request. Its handler must also leave Citry
State unchanged, because the file response has no result envelope in which to
refresh the signed State token.

## Protect every handler like an HTTP endpoint

State signatures stop tampering with the server-minted value, but State remains
visible browser input and writable public fields are deliberately changeable.
Reload records by id, authorize the current user, and validate what the action
is allowed to do on every call. Configure host CSRF protection as described in
[Security](/security/#protect-event-posts-from-csrf).
