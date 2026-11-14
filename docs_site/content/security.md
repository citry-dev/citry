---
title: Security
description: Protect Citry templates and server events with expression sandboxing, explicit State, CSRF checks, and authorization.
---

# Security

You are about to put a Citry app in front of real users and want to know
what you must do to keep it safe. Citry protects some things by default and
leaves others to you:

| Risk | Citry by default | You |
|---|---|---|
| A user edits the values a handler receives | Signs State so it cannot be changed silently | Validate State and check permissions in every handler |
| Another site posts to your event routes | Rejects cross-site calls | Keep your framework's CSRF check on |
| A template expression reads or calls something it should not | Runs expressions in a sandbox that refuses known unsafe names and calls | Put in the template context only objects that every template author may read and call |
| A secret ends up in the page source | Refuses to send a value wrapped in `Secret` | Wrap each secret in `Secret` and read it on the server |
| Injected scripts on the page | Adds a hash to the tags of files it serves; the rest needs your opt-in | Send a [Content Security Policy](#apply-a-request-csp-nonce-centrally) with a nonce and `base-uri 'self'` |

The first two rows apply to every app that uses
[server events](/events/), and the next two to every app. The Content
Security Policy (CSP) sections later on are optional hardening.

## Treat State as input { #treat-state-as-client-input }

An event handler receives its [State](/events/state/) from the browser, so
treat it like any other form input. With the default storage, every State
value is visible in the page source. Citry signs the values, so a user
cannot change them silently, but it does not encrypt them. Fields listed in
`State._model` (every public field, by default) can also be changed on
purpose through `$state` and two-way `:c-*` bindings.

Keep secrets out of State. A value wrapped in
[`Secret`](#keep-secrets-on-the-server) makes the render fail, but a
secret in a plain string goes into the page like any other value. Store
a small record id instead, then load the record and check the current
user's permission in every handler:

```citry
class ProjectPanel(Component):
    class State:
        project_id: int
        page: int = 1

    class Events:
        def refresh(self, state, request):
            project = load_project_for_user(
                project_id=state.project_id,
                user=current_user(request),
            )
            return ProjectPanel(
                project=project,
                page=state.page,
            )
```

Citry sends the signed State to the page as a string, the State token,
and the browser sends it back with each call. The signature shows that
Citry wrote a State value, not that the value is the latest one. Anyone
who has a token Citry issued can send it back, and Citry accepts it until
it expires. A token is not tied to a user or a session either. So keep
counters, balances, and one-time flags in your database, under an id that
State holds, as in the example above. With server storage
(`State._storage = "server"`, below), an older token works until its
cache entry expires or the cache drops it.

A token expires `State._max_age` (a `timedelta`) after Citry issues it.
With the default storage and no `_max_age`, it never expires. Setting
`_max_age` later does not shorten the tokens Citry has already issued.

To stop accepting every signed token issued so far, give
`Citry(secret=...)` a new secret and drop the one that signed them. A page
that is already open then gets a `stale_state` error on its next call,
and Citry's browser code offers to reload the page. If you pass
`citry.contrib.django.secret()`, that means changing Django's
`SECRET_KEY` and not keeping the old key in `SECRET_KEY_FALLBACKS`. That
also ends Django's sessions and signs every user out. Give Citry a secret
of its own if you want to replace it separately. Citry accepts a value
signed with any entry of the secret list, so `Citry(...)` raises an error
when the secret or an entry is empty or only whitespace.

Two State settings narrow what the browser sees and changes. Neither one
replaces the permission check:

- `State._public` lists the fields the browser can read as plain values
  through `$state` and bindings. The other fields still travel to the
  browser, inside the signed value.
- `State._model` lists the public fields the browser may change.

To keep State values out of the page, set `State._storage = "server"`.
Citry then keeps the values in its configured cache and sends only a lookup
key. This hides only the fields left out of `_public`: public fields are
still sent as plain values, so list the fields the browser needs in
`_public`. With several server processes, the cache must be shared between
them. Server storage does not replace the permission check either: still
authorize every use of the restored values.

Server storage adds a cache entry at every render and after every call
that changes State, and keeps each one until it expires: after
`State._max_age`, or after 24 hours when you do not set it. With several
server processes, use a shared backend and set its memory limit and
eviction policy. A browser write that would make the stored
State larger than `State._max_bytes` (64 KiB by default) gets a 422
before the handler runs. With the default signed storage, Citry makes
the same check when the call gets a new token. The limit covers only
browser writes, so when a handler copies request data into State, limit its size yourself. The
default `InMemoryCache` counts such State against a 64 MiB budget and
drops the entry used longest ago when it is full; see
[Server-stored State](/performance/cache-backends/#server-stored-state).
One client that sends many calls can push other visitors' State out, and
those visitors then see a reload prompt, so rate-limit the Events routes
if that matters for your app.

## Authorize every event

Every public method in `class Events` can be called by anyone who can reach
the page. Check that the current user may perform the action, in one of
three places:

- `_guard` on `Events`, which runs before every handler of the component;
- `@event(guard=...)`, which runs before one handler;
- a check inside the handler body.

A guard rejects a call by raising `EventError`:

```citry
from citry.ext.events import EventError


class DocumentEditor(Component):
    class State:
        document_id: int

    class Events:
        def _context(self):
            return build_event_context(self.request)

        def _guard(self):
            document = load_document(self.state.document_id)
            if not can_edit(self.context.user, document):
                raise EventError(
                    "You cannot edit this document.",
                    status=403,
                )

        def save(self, data: SaveIn, state):
            save_document(state.document_id, data.body)
```

Use a guard for a rule every handler shares. Put a check that depends on
the submitted data in the handler body, where the data has already been
validated.

Citry does not log users in. Your web framework does, and a handler reads
the user from the `request` it receives, or from `request.native` for the
framework's own request object.

[Event routes](/events/routes/) covers the HTTP side of event calls.

## Check redirect URLs { #check-redirect-urls }

A handler that redirects to a URL from the request, such as a `next`
parameter after a login, can send the visitor to another site if someone
puts that site's address in the link. Check the URL before you return
[`actions.Redirect`](/events/actions/#redirect-to-a-page), and redirect to
a fixed page when the check fails.

A prefix check is not enough. Browsers load both `//other.example/` and
`/\other.example/` from `other.example`, and both start with `/`:

```python
# Not enough: "//other.example/" passes
if data.next.startswith("/"):
    return actions.Redirect(data.next)
```

Use a check that parses the URL the way a browser does. Under Django, use
`url_has_allowed_host_and_scheme`. In this example the login page copies
its `next` query parameter into a hidden `<input name="next">`, so the
handler receives it as `data.next`:

```python
from django.utils.http import (
    url_has_allowed_host_and_scheme,
)


class Events:
    def login(self, data: LoginIn, request):
        # log_in is your own code that checks the password
        log_in(request, data)
        host = request.native.get_host()
        is_safe = url_has_allowed_host_and_scheme(
            data.next,
            allowed_hosts={host},
            require_https=request.native.is_secure(),
        )
        target = data.next if is_safe else "/"
        return actions.Redirect(target)
```

Outside Django, follow the cases Django's function rejects when you write
your own check. Citry plans a built-in check
([#568](https://github.com/citry-dev/citry/issues/568)).

## Check URL attributes { #check-url-attributes }

A URL is something the browser acts on, so a value that request data puts in
an `href`, `src` or `action` can run script when the visitor clicks: a
`javascript:` URL does. Citry escapes a value for the place it lands, but it
does not check the scheme of a URL you give to a plain HTML attribute, and
plain Vue, Jinja and Django behave the same way. Check the scheme before you
pass a URL from the request to an attribute, and allow only `http:`,
`https:`, `mailto:`, `tel:` and relative URLs. The Citry UI components that
take a link or an image URL refuse other schemes themselves.

## Check form field names { #check-form-field-names }

A browser lets a form's fields replace the form's own methods: inside
`<form>`, `<input name="addEventListener">` replaces the form's
`addEventListener` method with that input. Vue calls such methods on the
forms it renders, so a field name that data chooses can stop the component
that holds the form. Citry's own browser code ignores these fields. It also
ignores an element whose `id` matches a global it reads, such as
`<div id="Citry">`, and a `form`, `img`, `iframe`, `embed` or `object`
whose `name` matches a `document` method, such as
`<form name="createElement">`. Before you take a field name from request
or stored data, check it against the fields you expect, or add a fixed
prefix such as `field-`.

## Protect against CSRF { #protect-event-posts-from-csrf }

A cross-site request forgery (CSRF) is another site making the user's
browser call your app with the user's cookies. Citry rejects these calls on
every event route. Under Django, Django's own CSRF token check also runs.

When Citry's own check rejects a call, it fails with status 403 and the message "The call failed the
CSRF check; reload the page and try again."

### What Citry always checks

Every event call that is not a `GET` must pass these checks:

- A call with a JSON body must send the `X-Citry-Events` header. Citry's
  browser code adds it for you.
- When the browser sends an `Origin` header, its host must match the
  request's `Host` header. Behind a reverse proxy, the proxy must pass the
  browser's `Host` header on; see
  [Run behind a proxy](/advanced/web-frameworks/#run-behind-a-proxy).
- When the browser sends a `Sec-Fetch-Site` header, it must be
  `same-origin` or `none`.

These checks cannot be turned off, not even with `csrf=False`.

Citry's built-in requests send the CSRF token only to the page's own
origin, and event calls sent by the built-in transport do not follow HTTP
redirects. See
[`Citry.configure`](/reference/browser-apis/#citry-configure).

### Use Django's token { #use-djangos-token }

Django's `CsrfViewMiddleware` checks Citry's routes like any other view, so
keep it enabled. Citry's browser code reads Django's `csrftoken` cookie and
sends it as the `X-CSRFToken` header on event calls and on the request
that loads messages when [`$i18n`](/i18n/browser/) switches locale. Django
still creates, rotates, stores, and checks the token.

Django sets the `csrftoken` cookie only when the view, or a template it
renders, calls `get_token()`, as `{% csrf_token %}` does. A page built
only from Citry components does neither, so decorate its view with
Django's `ensure_csrf_cookie`:

```python
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def profile(request):
    page = ProfilePage()
    html = page.render().serialize()
    return HttpResponse(html)
```

If Django stores the token in the session, or makes the CSRF cookie
`HttpOnly`, browser code cannot read the cookie. Render the token into the
page instead, and tell Citry where to find it. Citry templates do not
understand Django's `{% csrf_token %}` tag, so pass the value of Django's
`get_token(request)` to the component as a `csrf_token` input:

```citry-html
<input
  type="hidden"
  name="csrfmiddlewaretoken"
  c-value="csrf_token"
>
```

```javascript
Citry.configure({
  csrf: {
    token: () => document.querySelector(
      '[name="csrfmiddlewaretoken"]',
    ).value,
  },
});
```

Event calls and the requests that load `$i18n` messages both read the
token from this setting. See
[`Citry.configure`](/reference/browser-apis/#citry-configure). The same
hidden input also works for a normal HTML form post. With this recipe the
token is part of the rendered HTML, and Django gives a different token
string on every request. Keep the hidden input in a part of the page that
is not cached; see
[Protect private output](/performance/caching/#protect-private-output).

### Tokens inside forms { #csrf-tokens-in-forms }

The hidden input can also sit inside a form that calls a server event with
`@c-submit`. Such a form sends every named control, so the token arrives as
one more field. Citry removes the `csrfmiddlewaretoken` field before it
checks the event's data class, so the handler never sees it and the call
is not rejected for an unknown field. If your framework names its token
field differently, list the names Citry should remove:

```python
citry = Citry(
    extensions_defaults={
        "events": {"_csrf_field_names": ["authenticity_token"]},
    },
)
```

The list replaces the default, so keep `"csrfmiddlewaretoken"` in it if
you still use Django's input. A single string instead of a list fails when
`Citry(...)` is created. A data class that declares a field with one of
these names still receives it.

### Use your own token { #other-frameworks }

FastAPI, Starlette, Flask, and plain ASGI or WSGI apps have no standard
CSRF token. If your app uses one, check it with a function set as `_csrf`
on `Events` for the whole component, or with `@event(csrf=...)` for one
handler. The function receives the request and raises `EventError` to
reject the call:

```citry
from citry.ext.events import EventError, event


def check_csrf(request):
    expected = current_csrf_token(request)
    if request.headers.get("x-csrf-token") != expected:
        raise EventError(
            "The call failed the CSRF check; reload and try again.",
            status=403,
        )


class Profile(Component):
    class Events:
        _csrf = check_csrf

        def save(self, data: ProfileIn):
            update_profile(data)

        @event(csrf=False)
        def token_authenticated_callback(self, request):
            verify_bearer_token(request)
```

Then tell the browser where to read the token and which header to send it
in, with [`Citry.configure`][Citry.configure]. Call it before the page
makes its first event call or switches language. Citry sends this token
on event calls and on the request that loads `$i18n` messages:

```javascript
Citry.configure({
  csrf: {
    cookie: "app_csrf",
    header: "X-CSRF-Token",
  },
});
```

`csrf=False` turns off only this token function. The checks Citry always
makes still run, and so does your framework's own CSRF protection: it does
not exempt a Django route from `CsrfViewMiddleware`.

### `GET` handlers skip CSRF

`GET` event handlers skip every CSRF check, because a `GET` must only read
data. Citry makes sure the call uses the declared HTTP method, but it cannot
tell whether your Python code changes anything. Declare a handler as `GET`
only when calling it twice has the same effect as calling it once.

## Limit request sizes { #limit-event-request-sizes }

Anyone can post to Citry's event endpoints, so Citry stops reading a
request that is too large and rejects it before it parses it:

| Setting | What it limits | Default |
| --- | --- | --- |
| `_max_body_bytes` | the request body, in bytes | 1 MiB (1,048,576) |
| `_max_form_fields` | the fields of one form post (the kind a plain HTML form sends) | 1,000 |

One request also carries at most 16 event calls, and more fail the same
way. You cannot change that limit.

Citry also refuses request JSON that nests arrays and objects more than
200 levels deep, before parsing it: an Events body gets a 400 error, a
State token gets the 403 for a malformed token, and an i18n request gets
a 400. Citry also refuses to make a State token from State nested that
deep. You cannot change this limit.

Citry stops reading a body once it passes `_max_body_bytes`, even when the
request's `Content-Length` is wrong or missing. A request over either
limit fails with the error code `payload_too_large`: an event call made
from the page fails with that code, and a plain HTML form post gets HTTP
status 413. Both limits apply to the whole app, so set them in
`Citry(extensions_defaults=...)`, not on a component's `Events` class:

```python
citry = Citry(
    extensions_defaults={
        "events": {
            "_max_body_bytes": 4 * 1024 * 1024,
            "_max_form_fields": 2000,
        },
    },
)
```

`Citry(...)` raises `ValueError` when either value is not a positive whole
number, and setting either one on a component's `Events` class raises
`ValueError` when the class is defined.

On Django, Citry reads event requests itself, so `_max_body_bytes`
applies to them in place of `DATA_UPLOAD_MAX_MEMORY_SIZE`. A few setups
read the body before Citry sees it:

- **Django middleware.** A form post or upload that middleware such as
  `CsrfViewMiddleware` parses first has already been read whole; Citry
  still rejects it when its declared size is over `_max_body_bytes`.
- **Servers and frameworks that buffer the body.** Some read the whole
  body before Citry sees it (Django's ASGI handler writes it to a
  temporary file), so also set a limit in your server or proxy.
- **Chunked bodies on WSGI.** On a WSGI server that does not mark where a
  chunked body ends, Citry reads such a body as empty.

Citry never reads the body of a GET, HEAD or OPTIONS request, on any
host. A server that buffers bodies (see above) may still read one, so
keep a limit in the server or proxy.

Citry does not accept file uploads by default. If you add your own code
that turns the request into
[`UploadedFile`][citry.ext.events.UploadedFile] values, the files come
from the same body, so `_max_body_bytes` limits them too.

## Check event data { #check-event-data }

Citry checks a call's data against the `data` class (the class of the
handler's `data` parameter) before the handler runs, and checks the
browser's writes against the State class. When the data fails a check,
the call gets a 422 error and the handler does not run. The 422 can list
fewer problems than the data has, because Citry stops checking early:

- Each list, set, tuple, or dict reports only its first bad item. The
  exceptions are listed below.
- Data with more than about 1,000 errors gets one message in place of the
  field messages. The message sits under `fieldErrors._args`, the key for
  a message about the whole call's data (`fieldErrors._state` for a State
  write). The number can be lower for data with long keys or long
  messages.
- A Pydantic v2 class that forbids extra keys gets one message when the
  data holds more than 100 keys it does not declare. A TypedDict or
  dataclass inside that class has the same limit, unless it sets its own
  extra-keys setting.
- A 422 lists field messages until their text would pass 65,536
  characters. Its message ends with how many field messages it left out.
- A 422 cuts a field message longer than 1,000 characters to that
  length, ending it with "…".

These parts report more than their first bad item:

- A browser write to a Pydantic v1 State reports every bad item. The
  422 lists up to 20 for each list or dict field.
- A list or dict inside a wrap validator reports every bad item, because
  your function may need every error. A wrap validator is a validator
  that receives the value and the next validator (`WrapValidator`, or a
  validator with `mode="wrap"`). This includes a list or dict in the
  text of a `Json[...]` field that has the wrap validator around it
  (`Json[...]` is a Pydantic type that makes a field read its value from
  JSON text). The 422 lists up to 20 for each list or dict field.
- A fixed-length tuple in a Pydantic class, such as `tuple[int, int]`,
  reports each position.
- Extra keys that a model allows and checks against a type report each
  bad key. A model declares them with `extra="allow"` and
  `__pydantic_extra__: dict[str, X]`, and a TypedDict with
  `extra_items`.

A wrap validator that drops bad items cannot rescue data with more than
about 1,000 errors: the call still gets the single message.

A form that shows only the message next to each field shows nothing when
Citry sends `fieldErrors._args` or `fieldErrors._state`, so show those
messages too ([how](/events/forms/#eventerror-field-errors)).

Citry refuses data that nests more than 64 levels of models, dataclasses,
TypedDicts, unions, wrap validators, and `Iterable` fields, when a
Pydantic v2 class checks it. Each model, dataclass, TypedDict, wrap
validator, and `Iterable[...]` or `Generator[...]` field that a value
passes through counts one level. So does each union whose members could
read the value. Citry checks the items of an `Iterable[...]` field
before the handler runs, and the handler gets an iterator over the
checked items.

Deeper data fails with a 422 under `fieldErrors._args`
(`fieldErrors._state` for a State write) that says the data is nested
too deeply, and Citry logs a warning naming the class.

The limit applies to event data and to browser writes to State, not to
restoring State the server saved. You cannot change it.

Your handler gets the checked data on your server's own thread. Code of
yours that walks it level by level, such as `model_dump()` on a model
that holds a model on each level, needs room on that thread's stack: on
macOS with Python 3.14, about 100 levels fit in 512 KiB, so data at the
limit fits with room to spare, while 128 KiB (the default on musl Linux
such as Alpine) fits only about 22. If your server's request
threads have less than 512 KiB, call `threading.stack_size()` before
the server starts them. It applies only to threads Python starts after
the call:

```python
import threading

threading.stack_size(512 * 1024)
```

Citry checks the data on a thread of its own with a 16 MiB stack, so the
limit is the same whatever stack size your server gives its threads.
Citry also builds State for a render, writes State out for its token,
and checks State a handler changed, all on those threads. Your request
thread waits each time Citry hands work to such a thread, which takes
about 10 to 40 microseconds (measured on macOS); a call that writes
State does this about a dozen times. Citry starts these threads when
checks need them, keeps up to two idle, and runs at most 32 per server
process; a check that finds all 32 busy waits for one to finish its
current check. A validator that waits for the network or a database
keeps its thread busy while it waits, so slow validators can make other
checks and renders wait. On Windows, each thread's 16 MiB counts
toward the system's memory commit limit while the thread lives.

Your validators, serializers and `__post_init__` methods run on that
thread too, and Citry reads the items of `Iterable` fields there. They
can read the request's context variables (`contextvars`), but a value
your code stores with `threading.local` is unset there, and a context
variable that a validator sets does not reach your handler. A validator
that uses Django's database gets the check thread's own connection,
which stays open while the thread lives and does not see rows the
request wrote inside an unfinished transaction, and a write from it
waits for that transaction. A validator must not wait for a lock that
the request's thread holds.
Under gevent or eventlet the check runs on a real thread, so other
greenlets do not run while a validator waits, and a validator must not
wait for anything another greenlet holds.

Where Python cannot start a thread or set its stack size, as in Pyodide
(Python in the browser), Citry checks the data on the calling thread,
and the limit is 32 levels.

When Citry can check a State only as JSON text
([which ones](#schemas-citry-refuses)), it counts only wrap validators,
because counting each class would change how the class reads JSON. So
defining the component raises `ValueError` when a field the browser may
write holds a recursive model, dataclass, or TypedDict (one that can
hold itself) with no wrap validator on the way back to itself. A loop
that passes through an `Iterable` field is still such a loop. Fix it by
removing what makes Citry check the State only as JSON, by leaving the
field out of `_model`, or by adding a wrap validator to the recursive
class.

Citry stops checking a request's data once its checks have used about 1
second of CPU time. The call then fails with a 422 that says the data
took too long to check, and Citry logs a warning naming the class. A slow
check also delays the other requests that the same worker handles, so run
more than one worker process.

Restoring State at the start of a call, checking a State your handler
changed, and building a Pydantic dataclass State again after a browser
write do not count toward that second, except for a Pydantic v1 State
(below).

Every check of a Pydantic v1 State counts toward that second: restoring
it at the start of a call, checking a browser write to it, and checking
it again after your handler changes it. A restore counts because the
token may hold values the browser wrote in an earlier request. Citry
cannot stop a restore partway, so it can run past the second, and the
request's later checks have less time left. Once the time is gone, a
later call whose State is a Pydantic v1 model gets the "took too long"
422 before Citry restores its State.

Citry stops a v1 check when the time is gone, as it does a v2 check. It
reads the clock once for every 256 values the model checks, so the write
ends with a 422 that says the data took too long, and it can run past
the second by the time it takes to check up to 256 more values.

A slow validator function of your own is not interrupted, because Citry
reads no clock inside it. When such a check ends with the time gone,
the model's own checks accept or refuse the write, and Citry logs a
warning that names the model. A later check in the same request that
reads the clock, such as another v1 State write or a large v2 check, is then
refused with the "took too long" 422.

Use a Pydantic v2 model when the browser sends large or nested data.

Citry cannot limit the work your own validators do. If a validator
parses a string, check the string's length first. If it calls another
model's `model_validate`, declare that model as a field type instead,
so the limits apply to it.

### Allow deep filter trees { #trees-in-event-data }

Event data can hold a tree, such as a filter whose `And` and `Or` nodes
hold more nodes. Citry limits how deeply such data may nest when the
union of node classes has no discriminator (a field, or a function, that
tells Pydantic which class in a union a value is) and two or more of the
classes can hold more nodes. Deeper data fails with a 422 error under
`fieldErrors._args` that says the data is too large or nested too deeply
to check, and Citry logs a warning naming the class.

How deep depends on your classes. A Pydantic model fits about 15 levels
with one child per node. When `And` and `Or` hold their children in
fields of the same name, it fits about 8 levels with two children per
node. More children, or more data in each node, lower that number.

To check deeper trees, declare the discriminator where you define the
recursive type (a type that contains itself, here `Node`), and give each
class a `Literal` tag field. Then each node counts one level toward the
[nesting limit](#check-event-data), so a tree can nest about 60 levels:

```python
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Cond(BaseModel):
    type: Literal["cond"] = "cond"
    field: str


class And(BaseModel):
    type: Literal["and"] = "and"
    items: list["Node"]


class Or(BaseModel):
    type: Literal["or"] = "or"
    any: list["Node"]


Node = Annotated[And | Or | Cond, Field(discriminator="type")]
```

A discriminator on the field that holds the tree does not reach the
unions inside it. With a tag field, each node the browser sends must
carry its `type`, so update browser code that builds nodes. A callable
`Discriminator` with a `Tag` on each class works too, and reads fields
the nodes already have, when each class has a field the others lack
(here `items`, `any` and `field`); the code is in
[Fix a tree in State](/events/state/#trees-in-state). Citry checks a
plain class or dataclass itself, and that check does not read
discriminators, so make the recursive type a Pydantic model, or keep the
nesting shallow.

### Fix a refused schema { #schemas-citry-refuses }

Defining the component raises `ValueError` when its `data` or State
class holds one of the parts below. The error names the field (or the
class, when the part sits outside any field) and a change that fixes
it, so you rarely need this list. The usual fixes are the discriminator
above, another type for the extra keys or items, or `_model` set to the
fields the browser may change, without that field. For a `data` class,
declaring the field as the type itself instead of `Json[...]` works
too.

- **A tree without a discriminator.** A union of node classes where two
  or more can hold more nodes, as in the filter tree above.
    - Refused: a `Json[...]` field (in State, one the browser may write)
      that holds such a tree.
    - Refused: a field of a Pydantic model State that the browser may
      write, with or without `Json[...]`. This includes a plain
      `class State:` that `Citry(model_base=BaseModel)` turns into a
      model. When you do not set `_model`, the browser may write every
      public field. [Fix a tree in State](/events/state/#trees-in-state)
      shows the fixes and what each changes for browser code.
- **Extra keys with a type that can fail with many errors.** A class
  allows extra keys and checks each one against a type, such as
  `__pydantic_extra__: dict[str, X]`.
    - Refused: `X` can fail with more than one error, or with a message
      that lists many values. That is a model, a list or dict, a union
      of several types, or a `Literal` or `Enum` with many or long
      values.
    - Fine: `X` fails with one short message, such as `int`, `str`, or
      `int | None`.
    - Where it applies: in a `Json[...]` field, and in a field of a
      Pydantic model State that the browser may write, when Citry can
      check the State only as JSON text (see below) or when the keys sit
      inside a type in a union or an `OnErrorOmit` item.
- **A `Json[...]` field with a wrap validator around it.**
    - Refused: a list or dict whose items can fail with several errors
      or with a message that lists many values, such as a list of models
      or of a union of several types like `date | time`.
    - Refused: a list or dict inside a dict in its text, unless its items
      are plain JSON values such as `int`, `str`, `bool` or `None`, as
      in `Json[dict[str, list[date]]]`.
    - Fine: items such as `int`, `str`, a date or a URL, alone or in a
      union with `None` (as in `date | None`), nested lists of those,
      and a union of plain JSON types such as `int | str | None`.
    - Fine: a wrap validator inside the `Json[...]`, as in
      `Json[Annotated[list[Item], WrapValidator(...)]]`. Your validator
      then does not run when the text is not valid JSON.
- **A `pydantic.v1` model or dataclass in a `data` class or in a
  Pydantic v2 State.** Citry checks event data, and the fields of a
  Pydantic v2 State, with dataclasses, annotated classes and Pydantic v2
  models, not with `pydantic.v1` classes.
    - Refused: a `data` class that is a `pydantic.v1` model or dataclass,
      or that holds one in a field, a list, dict, optional or union, a
      nested class, or a Pydantic v2 class. Inside a Pydantic v2 class
      this covers a field typed as the v1 class, and a validator that is
      a method of it, as in `PlainValidator(Model.parse_obj)`. The error
      names the `data` class and the v1 class.
    - Refused: a Pydantic v2 State with a field, writable or not, typed
      as a `pydantic.v1` class or checked with a method of one. The
      error names the State and the v1 class.
    - Fine: a State that is itself a `pydantic.v1` model, which Citry
      checks as described in
      [Use Pydantic in events](#pydantic-classes-in-events).
    - Fine: `InstanceOf[Model]` in a Pydantic v2 model, which only tests
      that the value is an instance, so a JSON object gets a 422 that
      says "Input should be an instance of Model".
    - Not seen: a v1 class that your own validator function calls from
      inside its code, as in a lambda. Citry counts that check's errors
      and stops it as it does for a v1 State write (see
      [Use Pydantic in events](#pydantic-classes-in-events)), but the
      class is not refused, so keep v1 classes out of your validators.
      In a Pydantic v2 State, Citry counts and stops such a check when
      the browser writes the field, but not when it restores the State
      at the start of a call.
    - Fix a refused class: make the v1 class a Pydantic v2 model.

Citry looks for these parts when the component class is defined. It
cannot look inside a class it meets only when a call arrives: a Pydantic
model inside a plain `data` class, or a `data` or State class whose
forward references were not resolved by then. A call that reaches such a
class (for State, a call that writes it) fails with a 422 that says "The
value could not be checked.", and Citry logs the field and the fix once.
A `pydantic.v1` class that Citry meets only at a call gets the same 422
and does not run.

The extra keys rule and the [path limit](#the-path-limit) depend on how
Citry checks a browser write to a model State. It checks the write as
Python values when that gives the same answer as checking JSON text. It
can check the write only as JSON text when the State has one of these:

- a strict setting: `strict=True`, or a strict field of a type that JSON
  has no form for, such as a date, a tuple, or a model;
- the `val_json_bytes` setting;
- a custom type that checks JSON input differently from Python input;
- a model that forbids extra keys and gives a field an alias.

Without any of these, Citry checks the write as Python values first.
When that check accepts the write, Citry then reads it as JSON text.
A State checked only as JSON text cannot let the browser write a
recursive class ([nesting limit](#check-event-data)).

### Use Pydantic in events { #pydantic-classes-in-events }

Events needs Pydantic 2.13.0 or newer for a Pydantic v2 `data` or State
class, including one used inside a plain `data` class. On an older
Pydantic, defining the component raises `RuntimeError`.

Citry checks a Pydantic v2 class with the same rules as the class,
apart from the limits on this page. A few things differ:

- Citry does not call your class's `model_validate`, or an override of
  it, for event data. Put such logic in a `model_validator`.
- Pydantic plugins, such as Logfire, do not record the checks of event
  data and State writes, because Citry runs them with its own copy of
  the class's validator.
- Citry can check a browser write to a Pydantic model State both as
  Python values and as JSON. A validator that reads `info.mode` and
  answers differently can then refuse a valid write, so keep such
  validators out of a model State.
- Citry checks each browser write to a Pydantic dataclass State when it
  arrives; see
  [Pydantic dataclass State](/events/state/#pydantic-dataclass-state).
- A validator that raises an exception other than `ValueError` or
  `AssertionError`, such as `RuntimeError`, refuses a State write with
  "The State could not be checked." under `fieldErrors._state`.

A field typed `ImportString` (or `pydantic.v1.PyObject`) lets the data
choose a Python module for the server to import, so never use one in a
`data` class or in a State field that the browser may write.

An Events `data` class can't be a `pydantic.v1` model, and neither a
`data` class nor a Pydantic v2 State can hold one
([details](#schemas-citry-refuses)). Use a Pydantic v2 model.

A `pydantic.v1` State checks a browser write itself, and a bad value gets
a 422 with field messages. Citry cannot give a v1 model the copy of its
validator that it gives a v2 class, so it guards the check of a write in
three ways:

- Before the model runs, Citry refuses writes whose
  [field paths are too long](#the-path-limit).
- Citry counts the errors the model builds as it builds them. When a
  check reaches about 1,000 errors, Citry stops it and the write gets
  the single "too many errors" message described under
  [Check event data](#check-event-data).
- Citry reads the clock while the model checks, and stops the check when
  the request's CPU time is gone.

Citry adds these checks to `pydantic.v1` only while one of its own
checks of event data or State writes runs, and only once your app has
loaded `pydantic.v1`. Other code that uses `pydantic.v1` in another
thread at that moment runs a little slower, and Citry does not count its
errors.

A union without a discriminator that holds a tree can make a v1 model
check the same data again at each level, and the clock is what stops
that. To avoid the repeats, give the union a discriminator, as in
`Field(..., discriminator="type")` with a `Literal` field called `type`
on each member.

A v1 union tries its members in turn, and the errors of a member that
fails do not count when a later member accepts the value. A member that
builds more than about 1,000 errors by itself (fewer when the data has
long keys) still ends the check with the "too many errors" message, even
when a later member would accept the data.

Keep secrets out of the messages your v1 validators raise. Pydantic v1
turns a `TypeError` raised in a validator into a field error, and Citry
sends its message to the browser, as it does for a `ValueError`.

### Shorten long field paths { #the-path-limit }

A valid call can fail with a 422 that says "The field paths in this data
are too long in total to check. Send shorter keys or fewer items." Citry
adds up the length of every field path in the data, such as
`scores.alice.3`, before Pydantic runs. When the total is over
16,777,216 characters, or over 32 times the size of the data (counted in
characters of text) if that is larger, the call fails with this 422 and
Pydantic does not run. You cannot change this limit. It can refuse a
valid call, because it runs before Pydantic decides whether the data is
valid.

Citry applies this limit to three kinds of data: a browser write to a
Pydantic v1 State, the browser's writes to a model State that Citry can
check only as JSON text
(see [Fix a refused schema](#schemas-citry-refuses)), and, rarely, a
Pydantic v2 class whose checks Citry could not set up (Citry logs an
error when that happens).

Some data adds more path text than its own size:

- A union without a discriminator adds the data's paths once for each
  type in the union, because each type reports its own errors. Give the
  union a discriminator to add them once.
- A model with many required fields adds a path for each of them to every
  object, because an empty object reports them all as missing. A long
  list of objects next to many required fields can reach the limit.
- When the class has any `Json[...]` field, each string in the data adds
  as much path text as if it held JSON text.
- A dict key of a few kilobytes over thousands of items can reach the
  limit in any of the three kinds.

## Sandbox template code { #sandbox-python-template-expressions }

Anything inside `{{ }}` or a `c-*` attribute is a Python expression. Citry
runs it in a sandbox that refuses the known ways an expression could reach
dangerous parts of Python. The sandbox is on by default and modeled on
Jinja's sandbox.

The sandbox is a second layer of protection, not a promise that a template
from a stranger is safe to run. It checks the names and calls that the
expression text writes. It does not check what the objects you pass in can
do. Two things decide how much you can trust a template with:

- **Who writes the template text.** Only the template author writes
  expressions. Never build a template, or any part of an expression, from
  request data or from text a site visitor saved. Pass that data to the
  template as values in the render context, where an expression can read
  them.
- **What you put in the render context.** An expression can read every
  attribute and call every method of a context object whose name does not
  start with `_`. If you pass a settings object, a template can read
  `settings.SECRET_KEY`. If you pass a user model, a template can call its
  public methods. Pass only what every template author may use.

### What is blocked { #what-the-sandbox-blocks }

- **Names starting with `_`.** An attribute such as `obj.__class__` or
  `obj._cache`, a variable such as `_x`, and a string dict key such as
  `data['_key']` are all blocked. This closes the usual path from an
  object to Python's globals and builtins.
- **Dangerous functions.** A list of builtins such as `eval`, `exec`,
  `__import__`, `getattr`, `setattr`, and `open` is blocked. The check
  compares the function itself, not its name, so passing `eval` into the
  context under another name, or wrapped in `functools.partial`, does not
  get around it.
- **Formatting methods that follow paths.** A format string such as
  `'{0.name}'` reads attributes by name, and it skips the checks above. So
  `format` and `format_map` are blocked on every kind of string: `str`,
  subclasses of `str` such as `Markup`, and `collections.UserString`. Every
  method of a `string.Formatter` is blocked, and so is building an
  `operator.attrgetter` or `operator.methodcaller`. Use an f-string
  instead.
- **Statements.** Assignments, `del`, `import`, `raise`, `assert`,
  `async`/`await`, and `yield` are not expressions.
- **Names the sandbox uses itself.** The sandbox's own helpers have names
  that start with `_sx_`. A lambda parameter or loop variable with that
  prefix, including a `<c-for>` loop variable, fails with `SyntaxError`,
  because it could replace one of the sandbox's checks. Every other name
  works, such as `source` in `<source c-for="source in sources">`.

A statement fails with `SyntaxError` when Citry compiles the template. A
blocked access fails with [`SecurityError`][citry.SecurityError] only when
the expression runs:

```python
from citry import SecurityError
from citry_core.safe_eval import safe_eval

compiled = safe_eval("f('1+1')")
try:
    # eval is blocked even under another name
    compiled({"f": eval})
except SecurityError as e:
    # The message starts with: Error in call: SecurityError:
    # function '<built-in function eval>' is unsafe
    print(e)
```

### Builtins are missing { #why-builtins-are-not-available }

`{{ len(items) }}` fails with `KeyError: 'len'`. Expressions can use only
the names in the render context, and Python builtins such as `len`, `str`,
and `range` are not in it.

Compute the value in `template_data`, which is ordinary Python, and pass
the result to the template:

```citry
class Cart(Component):
    def template_data(self, kwargs, slots):
        return {"count": len(kwargs["items"])}

    template = """
      <p>{{ count }} items</p>
    """
```

See [Expressions](/syntax/expressions/) for more.

### What the sandbox misses { #what-the-sandbox-does-not-protect }

The sandbox checks names. It does not know what your code does, and it is
not guaranteed to block every way out:

- **Your objects expose every public attribute and method.** An expression
  can read any attribute and call any method of a context object whose name
  does not start with `_`. A secret kept in a public attribute is readable.
  A method that deletes data can be called. A database queryset in the
  context lets a template filter it with any field lookup.
- **Your functions can be called.** A function you put in the context is
  allowed until you block it, as shown next.
- **Helpers that call other functions or look up names from text run
  without the checks.** The sandbox checks the calls and lookups that the
  expression text writes. A function you put in the context that calls its
  arguments (`map`, `functools.reduce`, the `key=` argument of `sorted`
  or `list.sort`) or reads an attribute from a string (a `getattr`-style
  helper, `inspect`, `importlib`, Django's `format_html`) does that work
  unchecked. Do not put such helpers in the context.
- **Dict keys that start with `_` are not hidden.** `data['_key']` is
  blocked, but `data.get('_key')`, looping over `data`, and
  `'%(_key)s' % data` read the same item.
- **The blocked list covers known dangers.** It is a list of specific
  functions and types, not a guarantee.
- **Time and memory are not limited.** An expression can run as long
  and use as much memory as the server process allows. To cap them, set
  limits on the worker process that renders pages.

Put only objects and functions in the render context that you are
comfortable letting template authors use.

### Block your functions { #marking-your-own-functions-unsafe }

To stop templates from calling one of your functions, decorate it with
`unsafe`. A method with the Django-style attribute `alters_data = True` is
blocked the same way:

```python
from citry_core.safe_eval import unsafe

@unsafe
def delete_account(user):
    ...
```

A template that calls `delete_account(...)` then fails with
`SecurityError`.

### Turn the sandbox off { #turning-the-sandbox-off }

If every template on a [`Citry`][citry.Citry] instance comes from a trusted
source, you can turn the sandbox off with `sandbox_expressions=False`. This
removes the access checks for that instance only:

```python
from citry import Citry

app = Citry(sandbox_expressions=False)
```

A successful render gives the same output either way, and a walrus
assignment (`:=`) still writes into the template's variables. On CPython,
builtins are still missing, so only the blocked accesses behave
differently. On PyPy, every builtin is available with the sandbox off,
including `open` and `__import__`, so `{{ len(items) }}` renders there
while CPython and the sandbox reject it. This does not change who you can
trust: with the sandbox off, a template can already reach any Python
object.

## Keep secrets server-side { #keep-secrets-on-the-server }

Visitors can read everything a component returns from `js_data()` or
`css_data()`, and, with the default storage, its State: it ends up in the
page or in files the page loads. Wrap an API key, token, or password in
[`Secret`][citry.Secret] where you load it:

```python
import os

from citry import Secret

API_TOKEN = Secret(os.environ["API_TOKEN"])
```

Citry then refuses to send it to the browser: rendering fails with an
error that names the component and the key. `citry check` reports
such a `Secret` in `js_data()` before the page runs when it can see where
the value comes from; see
[Catch secrets early](/advanced/secrets/#check-for-secrets). Read the value on
the server with `get_secret_value()` where you need it. In a template it
shows as `***`.

Citry detects only the values you wrap. A secret kept in a plain string
is sent like any other text. See [Secrets](/advanced/secrets/) for a
full example.

## Keep debug logs off { #keep-debug-logs-off-in-production }

When an event handler, or its guard, raises an unexpected exception, the
call fails with status 500 and the browser gets the message "The event handler
raised an unexpected error." With debug logs on, the message also
includes the exception's type and text, such as
`RuntimeError: connection to db-internal:5432 refused`. That text can
reveal internal details to anyone who triggers the error.

Citry adds the exception text when the `citry` logger's level is `DEBUG`
or lower, including Citry's `TRACE` level (5). It makes no
difference whether you set that level on the `citry` logger or it comes
from the root logger, as with `logging.basicConfig(level=logging.DEBUG)`. Django's `DEBUG` setting
and Flask's debug mode do not affect it. In production, set the `citry`
logger to `INFO` or `WARNING`:

```python
import logging

logging.getLogger("citry").setLevel(logging.INFO)
```

With debug logs on or off, Citry logs the full traceback on the server
at `ERROR` level, and the browser never receives it.

## Use a CSP nonce { #apply-a-request-csp-nonce-centrally }

A Content Security Policy is a response header that tells the browser
which scripts and styles it may run. A nonce is a random value, new for
each response, that you list in the header and put on every trusted
`<script>` and `<style>` tag. Injected markup does not know the nonce, so
the browser refuses to run it.

Generate the nonce, pass it to Citry when you serialize the page, and put
the same value in the header:

```python
from secrets import token_urlsafe

# 128 random bits, as the CSP specification recommends
nonce = token_urlsafe(16)
page = Page()
serialized = page.render().serialize_result(csp_nonce=nonce)

policy = (
    "default-src 'self'; "
    f"script-src 'self' 'nonce-{nonce}'; "
    f"style-src 'self' 'nonce-{nonce}'; "
    "base-uri 'self'"
)
```

Your web framework sends `serialized.html` with `policy` as the
`Content-Security-Policy` header. Citry checks that the nonce is valid CSP
base64. You own the rest: how random and how fresh it is, the header, and
every resource outside the Citry render. See the
[CSP specification](https://www.w3.org/TR/CSP/#security-nonces).

Citry puts the nonce on every structured
[`Script`][citry.ext.dependencies.Script] and
[`Style`][citry.ext.dependencies.Style], including external scripts and
stylesheet links. It adds the nonce after dependency hooks have run. A
dependency that already carries the same nonce is fine. A different or
malformed nonce raises `ValueError`.

Citry does not change the dependency objects, so you can serialize one
render several times with different nonces.

Your policy never needs `'unsafe-eval'` for Citry. Citry compiles Vue
templates on the server, so the browser never evaluates directive strings,
and you can write any JavaScript in Vue expressions. Under a CSP, Vue
rebuilds the page in the browser instead of reusing the server HTML, so
focus and text typed before Vue starts are lost; see
[Replaced pages](/vue/server-rendering/#pages-vue-replaces-instead-of-adopting).

Citry does not add the nonce to a `<script>` or `<style>` tag written
directly in a template, so the browser blocks it. Move that code to
`Component.js`, `Component.css`, or a structured
[`Dependencies`][citry.Component.Dependencies] entry.

!!! warning "Cache the page and its header together"

    When you cache a full response, cache its HTML and its CSP header as
    one unit. Cached HTML served with a new header carries the wrong nonce,
    and the browser blocks its scripts.

### Limit the `<base>` tag { #limit-the-base-tag }

Add `base-uri 'self'` to your policy, as the example above does. A nonce
stops injected script tags, but it does not stop injected markup from
changing where your own trusted tags load their files.

A `<base>` tag changes where the browser looks for the relative URLs that
follow it, even ones that start with `/`. A tag with a valid nonce still
runs the file its URL now points to. The nonce says the tag is trusted. It
does not say where the file comes from.

`default-src` does not cover `<base>`. `base-uri 'self'` lets a `<base>`
tag point only at your own site, so it can still move relative URLs within
your site. If your pages have no `<base>` tag, use `base-uri 'none'`: the
browser then ignores the address in any `<base>` tag.

Citry [adds a hash to the tags it writes](#pin-citry-managed-scripts-with-sri)
for files it serves. If a `<base>` tag moves one of those files, the browser
refuses it and the page's scripts do not start. The wrong file does not run,
but the page still breaks, so you still need `base-uri`. Citry adds no hash
to these:

- A file you list by URL, such as `Script(url="/static/app.js")` or a URL
  in a [`Dependencies`][citry.Component.Dependencies] class. Put your own
  `integrity` value in its `attrs`, as
  [Third-party scripts](#third-party-scripts) shows for a file from another
  site.
- A `<script>` or `<link>` tag you write in a layout or template, including
  a tag you write by hand for `/citry/citry.js`.
- A tag that an `on_dependencies` hook points at another URL or builds as a
  new `Script` or `Style`, because Citry keeps the file's hash on the
  original object.

### Nonces in fragments { #html-fragments }

When an [HTML fragment](/advanced/html-fragments/) has components that use
Vue or server events, serialize it with the nonce of the page that
receives it:

```python
html = card.render().serialize(
    deps_strategy="fragment",
    csp_nonce=page_nonce,
)
```

The fragment request is a new response, so your server must know the
nonce of the page that sent it. For example, keep the nonce in the user's
session when you render the page. A session holds one nonce, so when a
user opens the app in a second tab, fragments sent to the first tab stop
starting. Store the nonce per page if your users work in several tabs.

A server event can return a [`Render`](/events/actions/) as an HTML
fragment, to a client of your own that posts the event call and inserts
the HTML it gets back. Citry serializes that fragment itself, so it needs
the nonce of the page that sent the call. Set `_csp_nonce` to a function
that takes the call's [`EventRequest`][citry.ext.events.EventRequest] and
returns that nonce, or `None` when the page has none:

```python
def page_nonce(request):
    # On Django: the nonce your app kept when it rendered the page.
    return request.native.session.get("csp_nonce")


citry = Citry(
    extensions_defaults={"events": {"_csp_nonce": page_nonce}},
)
```

Citry calls the function once for each call it answers with such a
fragment. `Citry(...)` raises `ValueError` when the setting is not a plain
function (an `async def` is refused too), and setting it on a component's
`Events` class raises `ValueError` when the class is defined. When the
function raises, or returns something other than a valid nonce string or
`None`, the call fails with the error code `handler_error`; an
`EventError` it raises answers with its own status instead.

Citry's own Vue runtime does not need the setting: it applies a server
event's update to the app already on the page. A form or htmx post to a
handler's own URL gets plain HTML without Vue, so the setting only adds
the nonce to that HTML's inline styles.

Citry's browser code reads the nonce on its own script tag when it loads.
It starts a fragment only when the fragment carries that same nonce, so
injected markup cannot start a fake fragment that loads its own scripts. A
fragment without the nonce does not start, and the browser console shows
an error. When a fragment starts, Citry puts the page's nonce on every
script, inline style, and stylesheet link the fragment adds.

Citry can check only a nonce that its own script tag carries. When that tag
has none, for example under a hash-based policy, Citry starts every
fragment in the page. Under `'strict-dynamic'`, the scripts such a fragment
names then run too, so give pages that receive fragments a nonce policy.

Under `security_csp="strict"`, a fragment does not load Citry's browser
code, so insert it only into a page that already has it.

### App data needs the nonce

An interactive page sends its data, such as the rows of a table, as JSON in
a script tag. Citry puts the nonce on that tag too. The browser does not
need it there, but Citry's browser code does: it starts the page only from
data that carries the same nonce as its own script, so injected markup
cannot supply fake data.

## Check output for CSP { #choose-a-csp-compatibility-mode }

Once you send a CSP header, markup that the policy blocks fails silently in
the browser. `security_csp` makes Citry find that markup when it
serializes the page:

```python
from secrets import token_urlsafe

app = Citry(security_csp="strict")

nonce = token_urlsafe(16)
page = Page()
html = page.render().serialize(csp_nonce=nonce)
```

| Mode | What happens |
|---|---|
| `"off"` (default) | No check. |
| `"warn"` | The output is unchanged, with one `RuntimeWarning` listing the problems. Use it while you roll out the policy. |
| `"strict"` | Raises `ValueError` listing the problems instead of returning HTML. |

The check scans the final HTML, after extensions have changed it. It
reports:

- `<script>` and `<style>` tags written directly in templates;
- native event attributes such as `onclick`, in any letter case;
- `javascript:` URLs.

The URL check reads the attributes that hold a link: `href`, `src`,
`action`, `formaction`, `xlink:href`, and `data` on `<object>`. An SVG
`<animate>` or `<set>` whose `attributeName` is `href` counts too,
because it can write its `to`, `from`, `by`, or `values` into the link
while the page is open. For `values`, which is a list separated by `;`,
any item that starts with `javascript:` is reported. The check decodes
character references and skips the tabs and line breaks that browsers
remove from a URL, so `java&#9;script:` is reported. It also reports a few
spellings that Chromium and Firefox did not run when tested, such as
`xlink:href` and `attributeName="HREF"`, in case another browser reads the
name more loosely.

Use a Vue binding such as `@click` instead of `onclick`, and move scripts
and styles to `Component.js`, `Component.css`, or structured
[`Dependencies`][citry.Component.Dependencies].

`"strict"` also raises:

- `ValueError` when the output contains a script (inline or loaded by URL)
  or an inline style, and you did not pass `csp_nonce`;
- `TypeError` when a dependency is not a structured `Script` or `Style`.

Citry's HTML checks refuse HTML that has a tag with more than 1,024
attributes, more than 16 start tags of any one of `<html>`, `<head>` and
`<body>`, more than 512 elements open at once (about 510 nested
elements), or formatting tags such as `<b>` and `<i>` left open or
misnested so often that the parser would copy more than 250,000 elements
and attributes. No ordinary page comes close.

Citry's output checks also stop at a fixed amount of work for one page,
because they may read a page several times (see
[Pages read several ways](#pages-read-several-ways)). They refuse a page
that keeps hundreds of elements open across much of it and also holds
markup that browsers read in more than one way. The message says "HTML
would take too long to check". Close elements sooner or nest them less
deeply.

Both output checks (`security_csp` and `security_javascript`) report a
page over any of these limits, or over the work limit, as one they could
not read. `"forbid"` and the CSP check's `"strict"` raise `ValueError`.
The other modes warn and still return the page.

The exception is the JavaScript check's `"omit"` mode. It marks each
element that has an event or poll binding, so it can remove the binding
later. If it cannot read the page, it cannot remove those marks, so it
raises `ValueError` instead of returning a page that still holds them.

In an interactive component, `Markup` HTML or a `<c-raw>` block over one
of the size limits raises `ValueError`. The work limit applies only to the
output checks. You cannot change these limits.

If a page spreads a dict onto an element with `c-bind`, limit how many
keys the dict can hold when its keys come from request data.

You can pass `security_csp` to `serialize()` to override the mode for one
render. Any other value raises `ValueError`, both in `Citry(...)` and in
`serialize()`.

With `"warn"` or `"strict"`, the editor and `citry check` report these
problems where a template writes them directly, such as
`onclick="..."`; see
[Strict CSP problems](/ide/template-linting/#find-csp-problems). Both
need your app loaded, so `citry check --static` reports none of them.
Values from Citry bindings and the nonce checks above appear only when
Citry serializes a page, so render the pages you serve with `"warn"`
before you switch to `"strict"`. Neither check sees what Vue builds in
the browser from a binding such as `:href`.

Citry checks only what it renders. Your app owns the response header, the
nonce, layouts, third-party resources, and every other CSP directive.

## Limit page JavaScript { #choose-how-much-javascript-citry-may-deliver }

Some output must not run JavaScript at all, such as an HTML email or a
static export. `security_javascript` controls how much JavaScript Citry
sends. It is separate from CSP. Set it on the app, or override it for one
serialization:

```python
app = Citry(security_javascript="forbid")

page = Page()
email_html = page.render().serialize(
    security_javascript="omit",
)
```

| Mode | What happens |
|---|---|
| `"allow"` (default) | Normal interactive output. |
| `"warn"` | The same output, with one `RuntimeWarning` listing what needs JavaScript in the browser. |
| `"omit"` | Leaves out the scripts Citry manages: the Vue runtime, the Events client, component JavaScript, and the data that starts Vue. The HTML and CSS stay. |
| `"forbid"` | Raises `ValueError` when the rendered output needs JavaScript, even when `deps_strategy="simple"` or `"ignore"` would hide the script tags. |

Any other value raises `ValueError`.

Citry looks for these when it decides what needs JavaScript: Vue and Events
bindings that are in use, executable scripts, native `on*` attributes,
`javascript:` URLs (including the ones an SVG `<animate>` or `<set>` writes
into a link, as [described for
`security_csp`](#choose-a-csp-compatibility-mode)), and HTML that runs
scripts through `iframe srcdoc` or a data URL. Citry checks every data
URL the page loads or opens as a document: in an `iframe`, `frame`,
`object`, or `embed`, in a link or form (`href`, `xlink:href`, `action`,
`formaction`, and the value of an SVG animation of a link, since any link
can open in a frame), and in a `<meta http-equiv="refresh">`. It reads an HTML data URL, and counts any
other type as needing JavaScript, with or without a script, because the
browser runs the scripts of an SVG or other XML document. A data URL of
plain text, CSS, CSV, JSON, an image, audio, video, a font, a PDF, or
`application/octet-stream` does not count. An HTML data URL counts when
it has a script or when Citry cannot read it, such as invalid base64 or
any text outside plain ASCII, because a browser can read that text in
another encoding. Write such text in the document as a percent-encoded
reference, such as `%26%23233;` for `é`. A raw `#` would end the document.
A download link (`<a download>`) counts too, so give a file you
offer for download one of those types, such as
`application/octet-stream`, or serve it from a URL. It checks dependencies
and HTML after extensions have changed them. An `Events` method that no
template calls does not count.

A `<script>` whose `type` holds a control or non-ASCII character, other
than ordinary whitespace, counts as executable, because browsers differ in
which such characters they skip.

Citry reads the page as text, but a browser reads it in the encoding the
response or a `<meta charset>` names. Citry also reports text that would
change the page's tags in another encoding: the ESC control character
(U+001B) followed by `$` or `(`, which ISO-2022-JP, a Japanese encoding,
uses to switch modes, non-ASCII text in a `<![CDATA[` section, and a `<`
followed by a NUL byte, which spells a tag when a response names
UTF-16.

Citry writes the ESC character in an escaped value as `&#27;`, so a report
like this points to text Citry does not escape: `Markup`, `<c-raw>`, the
inline content of a `Script` or `Style`, and your template's own text. That
includes a value you pass to `Markup.format()`, `%`, `+` or `join`, which
call MarkupSafe's own escaping and leave ESC in place. A value can still fail
`"forbid"` for another reason, such as a URL or script type that the check
counts as code. Citry applies the same rule to the text inside an
`iframe srcdoc`, after decoding the attribute, so an escaped value bound to
`srcdoc` that holds `ESC $`, `ESC (`, non-ASCII text in a `<![CDATA[`
section, or a `<` followed by a NUL byte counts as running code and
fails `"forbid"`, even with no script in it.
Remove such text from raw HTML, and write CDATA text as ordinary escaped
text instead. `"warn"` and `"omit"` keep this text in the page and warn.

Send every page with `Content-Type: text/html; charset=utf-8`, so the
browser reads the page the way Citry does. Citry's Django, ASGI and WSGI
adapters add this when a Citry route returns a text response whose body is
a string. A view of your own must set this header itself.

### Pages read several ways { #pages-read-several-ways }

Browsers also differ from each other on a few parsing rules, and a page
can hide a script behind that difference. Current browsers keep tags such
as `<style>` and `<svg>` inside a `<select>`, and older browsers drop them,
so the same bytes can be a running script in one browser and a comment in
another. Firefox and Chromium also each handle a few misplaced end tags in
SVG in their own way. For these, Citry's check reads the page once for
each way browsers read it, and reports what any of those readings finds.
Each such pass over the page is a reading. An ordinary `<select>` reads
the same every way, so this changes nothing for it, even with images or
icons in its options.

The same HTML can also build a different page depending on where the
browser puts it. Citry's check covers three places:

- a whole document, which is how a browser loads your page;
- HTML put into the body of a page that is already open (the host page),
  by setting `innerHTML` on an ordinary element there, such as a `<div>`.
  Your own script or a library can do this, for example to show a Vue
  fragment response;
- HTML built by setting `innerHTML` on a `<template>` element, which is
  how Citry's browser runtime (through Vue) builds an HTML block. Your own
  script can do the same.

A Vue `v-html` binding, which sets `innerHTML`, already counts as needing
JavaScript.

Citry's check does not cover HTML that your own script inserts with
`innerHTML` into an element with special parsing rules, such as `<svg>`,
`<math>`, `<table>` and its parts (`<tbody>`, `<tr>`, `<td>`),
`<select>` or `<form>`. A browser reads the HTML by that element's own
rules, the check does not follow them, and so it cannot report code in
such HTML. To insert a fragment into one of these, set it on a
`<template>` element first, which builds it the way Citry's check reads
it, then move the template's contents into place:

```javascript
// html: the HTML string to insert
// tbody: the element to insert it into
const template = document.createElement("template");
template.innerHTML = html;
tbody.append(template.content);
```

To add shapes to an `<svg>` or `<math>` element, wrap the HTML in an
outer `<svg>` or `<math>` tag first, because a template reads a bare
`<circle>` as an ordinary HTML element. Then move the wrapper's
children: `svg.append(...template.content.firstChild.childNodes)`.

In the host page's body, a `<frameset>` builds nothing, so the markup after
it is read as ordinary HTML. The host page's doctype, not yours, also
decides whether the browser uses quirks mode (an older way of reading HTML
that some doctypes, or no doctype, switch on, as opposed to standards
mode). In quirks mode a `<table>`
inside an open `<p>` leaves the `<p>` open, which can change where later
elements end. So Citry's check also reads a page that holds a `<frameset>`
or a `<table>` inside an open `<p>` as markup in the host page's body, in
both quirks and standards mode, and reports what any reading finds.

An `iframe srcdoc` document gets the same two readings of its mode:
Chromium picks the mode from the document's doctype, with no doctype
meaning quirks mode, and Firefox always reads it in standards mode.

In an interactive component, Vue inserts some HTML, such as `Markup` or a
`<c-raw>` block, as one opaque HTML block: a piece of HTML that Vue does
not read itself. Vue builds that block in the browser inside a
`<template>`. Chromium reads the HTML inside a `<noscript>` there as real
elements, which load and run once Vue moves them into the page. So
Citry's check also reads a page with tags inside a `<noscript>` that way,
and reports a handler or script there. Remove the handler or script from
the `<noscript>`.

If a reading reports a script or handler that you wrote on purpose, move
it into `Component.js`, or into structured
[`Dependencies`][citry.Component.Dependencies], instead of writing it in
HTML that Citry does not escape.

For a few other kinds of markup, the parser behind Citry's check builds a
different page from the one browsers build, and the check does not try to
rebuild the browser's page. `"forbid"` raises `ValueError` instead, and
`"warn"` and `"omit"` warn. Each message gives the byte range of the tag
in the page, such as `settled HTML bytes 10:15`, then says "Citry cannot
tell what the page runs" and names what to change. Pages rarely need such
markup, and most of it is a mistake:

- a MathML `<annotation-xml>` whose `encoding` is `text/html` or
  `application/xhtml+xml`. This is valid MathML, but it makes the element
  hold HTML, which browsers read differently from Citry's check. Remove
  the element or give it another encoding;
- a `</select>` or `</form>` end tag inside an open `<annotation-xml>`.
  Close the `<annotation-xml>` first;
- an `<svg>` or `<math>` that starts while a formatting element was closed
  by the end of the element around it, as in `<p><b>Bold</p><svg>`.
  Browsers open a new `<b>` around the `<svg>`. Close the `<b>` before the
  `</p>`, or put text between the `</p>` and the `<svg>`;
- a misplaced formatting end tag such as `</b>` inside an SVG `<title>`,
  `<desc>` or `<foreignObject>`, or inside a MathML `<mi>`, `<mo>`, `<mn>`,
  `<ms>`, `<mtext>` or `<annotation-xml>`. Close the formatting element
  before the element around it ends;
- an end tag inside an SVG or MathML element that holds HTML (such as
  `<desc>` or `<mi>`) or inside a `<search>` element, after the page
  opened four or more copies of one formatting element with the same
  attributes, as in `<svg><desc><b><b><b><b>x</b></b></b></b>`. Citry's
  check cannot then tell which formatting elements are still open. Use
  fewer copies, or give each copy different attributes;
- an end tag, or a `<li>`, `<dd>` or `<dt>` start tag, that reaches past an
  open `<search>` to close an element outside it. Chromium closes that
  element and Firefox does not. Close the `<search>` first;
- an `<isindex>`. Remove it;
- a formatting element that is open across the start or end of a
  `<select>`, or one that an earlier end tag closed while a `<select>`
  starts, and an `<input>` that closes such a `<select>`. Close formatting
  elements before the `<select>` starts, and close the ones opened inside
  it before it ends;
- an `<option>`, `<optgroup>` or `<hr>` that closes a `<p>`, `<li>`,
  `<dd>` or the like inside a `<select>`. Close that element first;
- a `<thead>` in a `<template>` with no `<table>` around it, followed by
  another table part or by `</table>`. Put table parts inside a `<table>`;
- a `<table>` that starts inside an open `<p>` on a page whose doctype
  makes a browser use quirks mode where Citry's check does not. Chromium
  and Firefox both do this for a doctype whose public identifier (the first
  quoted text after `PUBLIC`) starts with
  `+//Silmaril//dtd html Pro v0r11 19970101//`. Chromium also does it for
  an HTML 4.01 Frameset or Transitional public identifier with an empty
  system identifier (the second quoted text), as in
  `<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "">`.
  Close the `<p>` first, or use `<!DOCTYPE html>`.

A formatting element, in this list, is one of the tags `<a>`, `<b>`,
`<big>`, `<code>`, `<em>`, `<font>`, `<i>`, `<nobr>`, `<s>`, `<small>`,
`<strike>`, `<strong>`, `<tt>` and `<u>`, which a browser opens again at
the next tag or text after an end tag closed it early.

These cases apply to HTML Citry does not escape, such as `Markup`. In an
`iframe srcdoc` or a `data:` document, such markup counts as running code.
They belong to `security_javascript`; `security_csp` does not report
them. Citry's check does not run the page in a browser, so it covers only
the differences found so far. A difference not yet found, or a parsing
change in a later browser version, can still hide a script.

### What `"omit"` leaves

`"omit"` is not an HTML sanitizer. It leaves Vue attributes such as
`@click` in the HTML, where the browser ignores them. It also leaves
`<script>` tags written in templates, native event attributes, and
`javascript:` URLs unchanged, and warns about them. Use `"forbid"` when
these must make serialization fail.

`"omit"` also warns about parts that will not work without JavaScript,
such as Vue-only conditions and buttons that only call a handler. Check
the page with JavaScript off, and use plain links or forms for the
actions that matter.

### What `"omit"` does to CSS

CSS stays in every mode. An `"omit"` fragment includes its CSS directly,
so it needs no Citry route and no Citry runtime on the page.
`deps_strategy="ignore"` still leaves out collected CSS too.

When a structured stylesheet or a data-only script carries an event
attribute such as `onload`, `"omit"` removes that attribute and keeps the CSS or data. It
removes a dependency that renders its own HTML, because Citry cannot tell
what tag it creates.

With `security_csp="strict"`, `"omit"` and `"forbid"` still report script
markup written in templates, and still put the nonce on the inline styles
they keep.

## Pin files with SRI { #pin-citry-managed-scripts-with-sri }

Subresource Integrity (SRI) makes the browser use a file only when its
bytes match a hash. Citry adds an `integrity` attribute to the script and
stylesheet tags it writes for files it serves, such as `/citry/citry.js`.
You do not need a setting for this. Citry adds no hash to a file you list
by URL, because it never downloads that file. You can add one yourself, as
[Third-party scripts](#third-party-scripts) shows.

### Get hashes for CSP

With `security_script_integrity="citry"`, Citry also computes SHA-384
hashes for the inline scripts it outputs and gives you these hashes, and
those of its external scripts, to put in your CSP header:

```python
app = Citry(security_script_integrity="citry")

page = Page()
serialized = page.render().serialize_result()
html = serialized.html
script_sources = " ".join(
    serialized.security.csp_script_hashes,
)
```

Citry hashes each inline script in the exact form it is sent.
`csp_script_hashes` lists the hashes, quoted, ready to add to `script-src`.
`serialized.security.scripts` holds one record per script. Citry does not
build the whole CSP header, because your app also owns layouts, analytics,
and every resource outside the render.

`security_script_integrity` works together with `security_csp="strict"`
but does not turn it on. The default is `"off"`, which reports no hashes
and keeps the `integrity` attributes on Citry's own files. Any value other
than `"off"` or `"citry"` raises `ValueError`, both in `Citry(...)` and in
`serialize()`.

### Hash each response

The short script that starts an interactive page names an app id that is
random for each response. Compute the hashes for each response, as for any
page with inline scripts.

The page's data, such as the rows of a table, is JSON that the browser
never runs. `csp_script_hashes` leaves it out, because your policy does not
need to allow it. `serialized.security.scripts` still records it with its
hash.

### Third-party scripts

For a script from another site, put its published `integrity` value on the
[`Script`][citry.ext.dependencies.Script]. Citry checks the value's format
and keeps it, but reports it as unverified: it never downloads the script.
Set `crossorigin` on that `Script` yourself, because the browser checks the
hash only when the other site sends CORS headers.

## Keep the CORS header { #keep-the-cors-header-when-a-proxy-or-cdn-serves-citrys-files }

**Symptom:** the page shows its server-rendered HTML, but interactive
components never start or styles are missing, and the browser console
shows a CORS or Subresource Integrity error.

Citry adds `integrity` to the scripts and stylesheets it serves. It writes
those tags with `crossorigin="anonymous"`, and its file routes answer with
`Access-Control-Allow-Origin: *`. These routes are `/citry/citry.js`, the
component JS and CSS, the files a component serves with
`local_files = "serve"`, and the compiled component code.

A same-origin page needs no CORS header. Two setups make these requests
cross-origin:

- **A sandboxed iframe.** Inside `<iframe sandbox="allow-scripts">`, every
  request counts as cross-origin.
- **A CDN or HTML optimizer** that rewrites Citry's file URLs to another
  host.

In both setups, the browser refuses a file whose response lacks
`Access-Control-Allow-Origin`. Configure the proxy or CDN to pass the
header through for Citry's file URLs, or to add it.

The header is safe on these routes: they return the same public files to
every caller and never read cookies. Citry's event, message, and preview
routes do not send it.

### Keep files unchanged

The browser also refuses a file that changed after Citry sent it, even on a
same-origin page. The file's hash in the page must match the file:

- **A proxy that rewrites files.** Stop the proxy from minifying these files
  or adding code to them, for every URL under your Citry prefix.
- **A cache in front of Citry's files.** `/citry/citry.js` keeps its URL
  across Citry upgrades, and Citry marks it `no-store`. A cache that ignores
  this keeps serving the old file, so the browser refuses it until you clear
  the cache.
- **A cache of whole pages.** A page cached before an upgrade names the old
  file's hash, so the browser refuses the new `citry.js`. Clear these caches
  when you upgrade Citry.
- **A rolling deploy.** A page from one version that loads `citry.js` from
  another gets a file that does not match. The page's scripts do not start
  until a reload reaches the same version. This ends when every process
  runs the new version.

## How we check advisories { #how-we-check }

Other web frameworks have shipped security bugs and published advisories
about them. Citry turns Python values into HTML, CSS and JavaScript too,
so it could repeat those bugs. This section explains how the maintainers
check for them. You do not need to do anything for it.

### Which projects we watch

- Django
- Next.js
- Angular, with AngularJS and Angular Universal
- Nuxt, with Nitro and h3, the server parts Nuxt runs on
- Svelte, with SvelteKit
- devalue, the library Svelte and Nuxt use to send data to the page
- React, with React Server Components
- Vue, with Vue I18n
- Jinja, with MarkupSafe, the escaping library Jinja uses
- django-components
- htmx
- Alpine.js

The first review covered 456 advisories from 9 of these projects. 450
came from GitHub. 6 appeared only in the US National Vulnerability
Database (NVD), which the monthly job does not search, so a maintainer
adds those by hand. htmx, Alpine.js and MarkupSafe had none.
django-components had one, about its own CI setup, which Citry does not
share, so it is not counted.

### Review each advisory

Once a month, a scheduled job asks GitHub for advisories from these
projects that the maintainers have not reviewed yet, and lists them in an
issue only the maintainers can see. For each one, a maintainer:

1. Sorts it by the kind of bug it describes, for example text written
   into HTML without escaping, or a file path that leaves its folder.
2. Finds the part of Citry that would have the same bug.
3. Tries the attack against Citry with a harmless test value, or reads
   the code when a test cannot reach it.
4. Fixes Citry if the bug is there.

Some advisories do not apply. Citry has no image optimizer, for example,
so an image optimizer bug has nothing to check.

### Check each code change

The maintainers keep the kinds of bug from these advisories as a
checklist. Before a change to the code of Citry's published packages
merges, a reviewer other than its author picks the kinds of bug the
change could bring in and checks the change for each one. Short records
of past security reviews are in
[`docs/security/reviews/`](https://github.com/citry-dev/citry/tree/main/docs/security/reviews).

### When we find a problem

If a released version has the problem, we handle it in a private
advisory, as
[SECURITY.md](https://github.com/citry-dev/citry/blob/main/SECURITY.md)
describes: we release the fix first and publish the advisory after. If
no release has it yet, we fix it in a public pull request. To report a
problem you found, follow SECURITY.md.

Once a fix is released, we publish an advisory for the problem.
[Citry's published advisories](https://github.com/citry-dev/citry/security/advisories)
lists them.
