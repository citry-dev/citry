---
title: v1.0.2
url: https://citry.dev/v/1.3.0/releases/v1.0.2/
description: "What changed in citry v1.0.2."
---
# v1.0.2

Citry 1.0.2 is a patch release with browser runtime, Events and render-cache
fixes. It still requires citry-core 2.1.1. citry-ui 0.7.0 is released at the
same time.

## Fixes

- The check that an extension's `on_serialize` hook kept the element
  Vue mounts on now reads the elements inside it the way a browser
  does. A hook result that a browser reads correctly, such as one
  with a `<p>` that a later `<div>` closes, no longer fails with
  "Vue serialization hooks must preserve exactly one empty Citry
  mount host", and content after an end tag that a browser ignores,
  such as `</link>`, now counts as inside that element.
- The browser i18n runtime now reports a format profile, parser or
  message ID named after a built-in JavaScript object member, such as
  `constructor` or `__proto__`, as unknown, with the same error code as
  any other unknown name. Before, such a name could format with default
  options or fail with a plain `TypeError`
  ([#701](https://github.com/citry-dev/citry/issues/701)).
- A form control named after a built-in form method or property, such
  as `contains` or `dispatchEvent`, no longer breaks Citry's event
  bindings on that form or the `citry:events:*` events fired from it
  ([#703](https://github.com/citry-dev/citry/issues/703)). Vue itself
  can still fail on such a name; see
  [Check form field names](https://citry.dev/security/#check-form-field-names).
- Citry's browser code now skips a CSRF cookie whose value has a broken
  `%` escape and uses the next cookie with the same name.
- An Events `Render` of a region that contains `<c-i18n c-client>` no
  longer fails with "an i18n fragment uses a different project
  configuration" when the server lists the same formats and parsers in
  another order ([#660](https://github.com/citry-dev/citry/issues/660)).
- `Citry.events.applyActions()` now rejects its Promise when Citry
  refuses a redirect, such as one to a URL with a scheme other than
  `http:` or `https:`, so your code learns that the page did not move.
  Before, the browser only logged an error and the Promise resolved, so
  code that awaits `applyActions()` may now need a `catch`. A redirect
  marked `wait: false` is still only logged. An event call whose result
  holds such a redirect now fails the same way.
- Without JavaScript, `actions.Redirect("http:next")` on an `http:` page
  (or `"https:next"` on an `https:` page) now lands next to the page, as
  it does with JavaScript. Before, it landed next to the handler's URL,
  usually on a "not found" page.
- A 405 answer from the ASGI and WSGI adapters now carries an `Allow`
  header that names the methods the route accepts, as HTTP requires. On
  every adapter, including Django, the list names `HEAD` wherever the
  route accepts `GET`.
- A component with `Cache` turned on that writes a value into a
  `<textarea>` no longer comes back with an empty textarea when its
  render is replayed from the cache.
- With a configured cache, the stylesheet a `css_data()` component links
  no longer answers 404 when the cache dropped its entry after the
  render. Citry now writes it again when it writes the page.
- A Django lazy translation, such as `gettext_lazy("active")`, now works
  as a class name in `c-class`, in a list or as a dict key. It used to
  raise.
- A `Markup` dict key in `c-class` or `c-style` is no longer escaped twice.
- A carriage return in an attribute value set from Python is now written
  as `&#13;`, so the browser keeps it rather than reading a line feed.
  Server-rendered HTML on an interactive Vue page is not changed.
- With `security_csp` turned on, Citry now warns when it leaves the
  element Vue mounts into empty because the server-rendered HTML would
  break your CSP. The warning lists what the check found. Before, it
  said nothing.