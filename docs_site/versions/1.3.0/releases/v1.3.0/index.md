---
title: v1.3.0
url: https://citry.dev/v/1.3.0/releases/v1.3.0/
description: "What changed in citry v1.3.0."
---
# v1.3.0

Citry 1.3.0 is a security release. In Events, it fixes these problems:
an `async def` guard, `_context` function or `_csrf` function never ran;
a handler's own guard turned off the component's guard; a guard that
returned `False` let the call through; and deeply nested event data or
State writes could end the server process on PyPy. It also renews State
tokens that are in use, so a page in use no longer gets the "page is out
of date" error (`stale_state`), and adds helpers that check redirect
URLs. Some changes refuse code or calls that 1.2.0 accepted, so read the
Changed section and the entries that start with "Security:" before you
upgrade. The PyPy fixes change nothing on CPython. Citry applies them on
every Python implementation except CPython, such as GraalPy. Citry 1.3.0
still requires citry-core 2.1.2.

## Added

- A page that is in use no longer gets `stale_state` (the "page is out
  of date" error) when its State token gets old. A call made once the
  token is past half its lifetime (12 hours by default, or half your
  `State._max_age`) now gets a new token, even when the call does not
  change State. A component that gets no call in the second half of
  its token's lifetime still expires. A renewal sends the public State
  again, so a watcher on an object or list field of `$state` runs. With
  server-stored State, each new token adds one cache entry. See
  [Treat State as input](https://citry.dev/security/#treat-state-as-client-input).
- You can now check that a redirect URL from the request stays on your
  site with `local_url_or()` and `is_local_url()` from
  `citry.ext.events`, for example
  `actions.Redirect(local_url_or(data.next, "/"))`. They read the URL
  the way a browser does, so `//other.example` and `/\other.example`
  get the fallback. Pass `allowed_hosts` to also accept a full URL on
  your site. See
  [Check redirect URLs](https://citry.dev/security/#check-redirect-urls).
- `RouteRequest` has a new `scheme` field: `"http"` or `"https"`, as
  your server reports it. The ASGI, WSGI and Django adapters fill it in.
  If you build a `RouteRequest` yourself, set it, because Events skip
  the https `Origin` check when it is empty.
- `citry check` now knows the `switch` attribute of `<input>`. It
  reports `switch="false"`, which still turns the switch on
  (`rule_invalid_attribute_value`), and suggests `switch` for a typo
  such as `swich` (`rule_misspelled_attribute`). Both rules are errors
  by default, so a template with either now fails `citry check`.

## Changed

- Security: Events now refuse a call that is not a `GET`, with status
  403 and `csrf_failed`, when your server says it arrived over https
  and its `Origin` header is not https. This stops a plain-http page on
  the same host from calling your app. 1.2.0 accepted these calls.
  Citry already refused them from browsers that send `Sec-Fetch-Site`,
  so browser traffic on a correctly configured site should not change.
  Behind a proxy that serves your site over https and passes plain http
  to your app, nothing changes. If your site is served to browsers
  over plain http while your server says https, every call that is
  not a `GET` now fails; see
  [Fix an http Origin](https://citry.dev/advanced/web-frameworks/#fix-an-http-origin).
- Citry's browser code now sends a GET event call's State token in the
  `X-Citry-State-Token` header instead of the URL, so server and proxy
  access logs do not record it by default. The server still reads the
  `_citry_state_token` query parameter, so clients that send it there
  keep working. A GET call that sends different tokens in the header and
  the query parameter gets a `400` error, so a URL cannot choose a token
  other than the one the browser sent. If a server from an earlier
  release answers `invalid_state`, as during a deploy or after a
  rollback, the browser sends the call once more with the token in the
  URL; a custom transport's `send` then runs twice for that call. If
  your event URL is on another origin and your CORS setup lists the
  allowed request headers, add `X-Citry-State-Token`. When a GET call
  sends the header and the handler sets its own `Cache-Control`, Citry
  makes the policy `private` and drops `public`, `s-maxage`, and
  CDN-only headers such as `CDN-Cache-Control`, so a CDN that ignores
  `Vary` cannot give one visitor's answer to another. See
  [Allow GET requests](https://citry.dev/events/routes/#expose-a-read-only-get-endpoint).
- Security: `actions.Dispatch` now raises `ValueError` for the name of
  a standard DOM event, such as `click`, `submit`, `input`, `change`,
  `keydown` or `focus`, because the event would run the page's own
  listeners for it, including `@c-*` bindings that call the server.
  This includes common words that are also browser events, such as
  `close`, `toggle`, `error`, `load`, `message`, `select` and
  `progress`. It also refuses names that start with `vue:` or `vnode-`,
  as it already refused `citry:`. Letter case is ignored in every
  check, so `Citry:ready` is now refused like `citry:ready`.
  `Citry.events.applyActions` in the browser refuses the same names.
  If you dispatch such a name, prefix it with your component's name
  and listen for the new name:

    ```python
    actions.Dispatch("click")          # now raises ValueError
    actions.Dispatch("TaskRow:click")  # works
    ```

    See [`Dispatch` browser events](https://citry.dev/events/actions/#notify-browser-code-that-something-happened).
- Security: a call that a guard refuses now gets the guard's error,
  such as 403, even when its args are invalid; 1.2.0 answered 422
  `invalid_args` and listed the invalid fields. Events now run
  `_context` and the guards before they check the args against the
  handler's `data` class, so both also run, with any side effects, for
  calls whose args are invalid. A guard that reads `self.event.args` can
  see a missing key or a value of the wrong type, and a guard that
  raises on one answers 500, so read each value with `.get()` and check
  its type. The experimental `on_event` hook now runs before the check
  too, and when it answers a call, Citry skips the check. As in 1.2.0, a
  guard sees the browser's writes to `State._model` fields, so leave the
  fields a guard decides on out of `_model`. See
  [Authorize every event](https://citry.dev/security/#authorize-every-event).

## Fixes

- Security: an `async def` event guard, `_context` or `_csrf` function
  is now refused with an error when the component class is defined.
  Citry calls these without awaiting them, so the code inside an async
  one never ran: an async guard let every call through, and an async
  `_csrf` function skipped your own token check. An app that has one
  now fails at startup: rewrite the function as a plain `def`. A plain
  `def` guard or `_csrf` function that returns a coroutine, another
  awaitable, a generator or an async generator now fails the call, and
  so does a `_context` that returns a coroutine. See
  [GHSA-gj9m-wwqx-m37j](https://github.com/citry-dev/citry/security/advisories/GHSA-gj9m-wwqx-m37j).
- Security: a handler's own `@event(guard=...)` now runs after the
  component's `_guard` (or the app-wide `_guard` in
  `extensions_defaults["events"]`) instead of replacing it, and either
  one can refuse the call. A call the component's guard refuses now
  fails on every handler of the component, including handlers with
  their own guard. To let a public handler through, return early from
  `_guard` when `self.event.name` names it, or set
  `@event(component_guard=False)` on the handler, which skips the
  component's or app-wide `_guard` for that handler only. See
  [GHSA-2jch-pr4c-gf9m](https://github.com/citry-dev/citry/security/advisories/GHSA-2jch-pr4c-gf9m).
- Security: applying `@event(...)` to a function that already has
  `@event` settings (two stacked decorators, or one function decorated
  again for another class) now raises an error, and so does a decorator
  above `@event(...)` that keeps `__wrapped__` but drops the settings.
  Code that did this loaded in 1.2.0, but only one set of settings took
  effect, so a `guard=` could be dropped without an error. Put every
  setting in one `@event(...)`, and write decorators with
  `functools.wraps`. A handler now also keeps the `@event` settings it
  had when its class was created, so changing the function's `@event`
  settings later does not change how that class's handler behaves, and
  a function used as a `ViewEvents` verb handler in one class no longer
  changes the HTTP methods it accepts in another class. See
  [GHSA-2jch-pr4c-gf9m](https://github.com/citry-dev/citry/security/advisories/GHSA-2jch-pr4c-gf9m).
- Security: an event guard that returns any false value except `None`
  (such as `False`, `0`, or an empty list or QuerySet), or an exception
  other than `EventError`, now refuses the call with a 403, and one that
  returns an `EventError` refuses it with that error's status and
  message, as if it had raised it. Before, a guard written as
  `return user.is_staff` or `return Document.objects.filter(owner=user)`
  let every caller through. `None` and `True` let the call go ahead. A
  guard that returns a function, as `return self.can_edit` does without
  the `()`, fails the call with a 500 and logs the guard's name. Any
  other true value lets the call go ahead and logs a warning that names
  the guard and the component. A returned value whose true-or-false test
  raises an error fails the call with a 500. See
  [GHSA-2jch-pr4c-gf9m](https://github.com/citry-dev/citry/security/advisories/GHSA-2jch-pr4c-gf9m).
- Security: on PyPy, the nesting limit for event data and browser writes
  to State is now 32 levels, down from 64, so that PyPy's stack can hold
  the check. Data nested deeply enough to end the server process in
  earlier releases gets a 422 instead. Wrap validators, unions,
  `Sequence[...]` fields and `OnErrorOmit` items each count as more than
  one level, and so does each level of a recursive type with a
  `WrapSerializer` or other serializer function, so on PyPy some data
  that earlier releases accepted gets a 422 that says it is nested too
  deeply. The limit does not stop every case. The process can still end
  if your schema has many validators at each level (especially with a
  free-form field deep inside it), if a handler stores event data in a
  State field of a different type that has a serializer, if a handler
  stores a Pydantic class built from a plain dataclass `data` class in a
  free-form State field such as `Any`, or if your own code validates
  nested data again. See
  [Event data on PyPy](https://citry.dev/security/#event-data-on-pypy)
  and
  [GHSA-29wx-2wvw-8962](https://github.com/citry-dev/citry/security/advisories/GHSA-29wx-2wvw-8962).
- Security: on PyPy, a component whose event `data` class or
  browser-writable State field holds a recursive type inside
  `Json[...]`, such as a model that can hold itself or a recursive list
  alias, now raises `ValueError` when it is defined, so the app fails
  at import. A class that Citry first meets at a call, such as a
  Pydantic model inside a plain dataclass, gets a 422 for that call
  instead. Give the recursive type that the error names a wrap
  validator of its own, or use `Json[Any]` or `Json[JsonValue]` for
  free-form JSON. In a `data` class you can instead change `Json[Tree]`
  to `Tree`; the field then takes the value itself, not JSON text.
- Security: on PyPy, a State that Citry checks only as JSON text, such
  as one with `strict=True`, now raises `ValueError` when a field the
  browser may write holds a recursive type of any kind, such as a
  recursive list alias; earlier releases refused only a recursive
  class there. Make the State lax, leave the field out of `_model`, or
  give the recursive type a wrap validator of its own.
- Security: on PyPy, defining a component now raises `ValueError` in two
  cases. In the first, its event `data` class or a State field has a
  serializer whose return type leads into a recursive type with a
  serializer of its own, such as
  `Annotated[Any, PlainSerializer(f, return_type=Tree)]`. In the second,
  a recursive type in that `data` class or State field has a
  `PlainValidator` on one of its levels, as in
  `Tree = Annotated[list[Tree], PlainValidator(f)]`. In both, Pydantic
  calls Python at every level of the value when Citry writes the State
  out. Remove `return_type`, annotate a `field_serializer` or
  `model_serializer` as returning `Any`, or use an `AfterValidator` or
  `WrapValidator` in place of the `PlainValidator`. The first case also
  refuses two shapes that would not end PyPy: a recursive return type
  whose only serializer is on a value that does not nest, such as a
  `field_serializer` for a date field, and a recursive Pydantic
  dataclass whose wrap `field_serializer` is annotated as returning its
  own type. Annotate those serializers as returning `Any`.
- When an event guard, `_context`, an `on_event` hook or a State
  validator raises an unexpected error, the server log, and in debug
  mode the error message, now name the function that failed instead of
  the event handler, which never ran.
- A component with Events that comes from the render cache now writes
  the same HTML as when it renders without the cache. Earlier releases
  gave its root element an extra `data-cid` attribute.
- On free-threaded Python with the GIL off, the request data from an
  Events check that failed, and the result of one that passed, are now
  freed about a second after your code lets go of them, not up to 60
  seconds later.
- With `State._storage = "server"`, a call that changes State no longer
  leaves an unused entry in your cache when its answer cannot carry the
  new token. That covers a form posted without JavaScript, and a call
  that fails because a public State value is one the browser cannot read.