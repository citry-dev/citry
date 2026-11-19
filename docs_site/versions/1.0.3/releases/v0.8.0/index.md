---
title: v0.8.0
url: https://citry.dev/v/1.0.3/releases/v0.8.0/
description: "What changed in citry v0.8.0."
---
# v0.8.0

Citry 0.8.0 makes Events refuse event data and State writes that are
too large, too deeply nested, or too slow to check. Pydantic classes in
Events now need Pydantic 2.13.0 or newer. Signed State tokens from
earlier versions stop working. The output checks `security_javascript`
and `security_csp` now find more scripts and event handlers that
browsers run, so a page that passed them before can now be reported.
Tags for files that Citry serves now carry `integrity`, and event calls
send the CSRF token only to the page's own origin. The upgrade notes
below list what can fail or change.

Citry 0.8.0 does not import on Pyodide (Python in the browser), so use
Citry 0.9.0 or later there. For the same reason the docs site has no
0.8.0 entry in its version picker.

## Upgrading from 0.7.x

- **Signed State tokens from earlier versions stop working:** State
  tokens in the default signed storage now use a key that Citry derives
  from your secret only for State tokens, so values that other code
  signs with the same secret (such as Django's `SECRET_KEY`) cannot be
  used as State. After you upgrade, a page that was open before the
  upgrade asks the visitor to reload on its next event call. During a
  rolling deploy, old and new processes reject each other's signed
  tokens until every process runs the new version.
- **Pages that passed the output checks can now be reported:** the
  `security_javascript` and `security_csp` checks now read a page in
  each way a browser may build it, and with
  `security_javascript="forbid"` such a page raises `ValueError`. The
  checks also refuse a page that would take too long to read every way.
  Citry also writes the ESC character in an escaped value as `&#27;`,
  which `<style>`, `<xmp>` and `<script type="text/plain">` show as
  written. The Fixes below list each case.
- **Clear proxy, CDN, and whole-page caches when you upgrade:** script
  and stylesheet tags that Citry writes for files it serves now carry
  `integrity` and `crossorigin="anonymous"` at every
  `security_script_integrity` value, including `/citry/citry.js` and
  `local_files = "serve"` files. The browser now refuses a file that a
  proxy or CDN changed, and a `citry.js` from a different version than
  the page, so a page cached before the upgrade fails to load its files.
  A CDN that serves these files from another host must send
  `Access-Control-Allow-Origin`. During a rolling deploy, a page can
  fail until a reload reaches the same version.
- **An empty or non-string secret now raises an error:**
  `Citry(secret=...)` raises `ValueError` for a secret, or an entry of a
  list, that is empty or only whitespace, and `TypeError` for an entry
  that is not a plain `str`. The error gives the entry's position. If
  your secret can come out empty, for example
  `[os.environ["NEW"], os.environ.get("OLD", "")]`, leave out keys that
  are not set. `citry.contrib.django.secret()` skips such entries for
  you. The setting takes a string, a list, or a tuple; pass any other
  collection as a list.
- **Event calls send the CSRF token only to the page's origin and no
  longer follow a redirect:** event calls to an events `url` on another
  origin now carry no token from the built-in transport, and a redirect
  answer makes the call fail. Return `actions.Redirect` to send the
  visitor to another page. `Citry.events.configure({csrf})` now rejects
  a header name that `Citry.configure` rejects.
- **A `<base>` element no longer changes where Citry's requests and URL
  actions go:** event calls, `$i18n` message requests, and the
  `Redirect`, `PushUrl`, and `ReplaceUrl` actions now resolve a relative
  URL against the page's own address. If your page sets `<base href>` on
  purpose, write these URLs as paths that start with `/`.
- **Upgrade every process that shares a cache:** a `css_data()`
  stylesheet in a configured cache is now built again from its stored
  values each time it is served. One stored by an earlier version
  returns 404 until a page with the same values renders again, and a
  cached component with `css_data()` values renders again once. A
  process on an earlier version keeps writing entries that the new
  version does not serve.
- **A State that holds a filter tree needs a discriminator:** if a field
  the browser may write holds a tree of nodes of different classes, such
  as `And | Or | Cond` where `And` and `Or` hold more nodes, and the
  union has no discriminator (a field, or a function, that tells Pydantic
  which class a node is), defining the component raises `ValueError`.
  When you do not set `_model`, the browser may write every public field.
  This also applies to a plain `class State:` that
  `Citry(model_base=BaseModel)` turns into a model. Pick one fix
  ([details](https://citry.dev/events/state/#trees-in-state)):

    - Give each node class a `Literal` tag field, and declare the
      discriminator on the `Node` type below. Every node the browser
      writes must then carry the tag, and a node without it is refused,
      so update browser code that builds nodes. A page opened before the
      deploy with an untagged tree in its State asks the visitor to
      reload once, on its next event call.

        ```python
        from typing import Annotated, Literal

        from pydantic import BaseModel, Field


        class And(BaseModel):
            type: Literal["and"] = "and"
            items: list["Node"]


        # Or and Cond get a tag field of their own in the same way.
        Node = Annotated[
            And | Or | Cond, Field(discriminator="type")
        ]
        ```

    - Use a callable `Discriminator` with a `Tag` on each class. When each
      class has a field the others lack (below, `items` on `And`, `any`
      on `Or`, `field` on `Cond`), the browser writes the same data as
      before. This is the only discriminator fix when some types in the
      union are lists or tuples, as in
      `Node = list[Node] | tuple[Node, ...] | int`.

        ```python
        from typing import Annotated

        from pydantic import Discriminator, Tag


        def pick(v):
            if isinstance(v, dict):
                if "any" in v:
                    return "or"
                return "and" if "items" in v else "cond"
            return {And: "and", Or: "or", Cond: "cond"}.get(type(v))


        Node = Annotated[
            Annotated[And, Tag("and")]
            | Annotated[Or, Tag("or")]
            | Annotated[Cond, Tag("cond")],
            Discriminator(pick),
        ]
        ```

    - Set `_model` to the fields the browser may change, without the
      tree. The browser can then no longer write that field.

- **Pydantic classes in Events need Pydantic 2.13.0 or newer:** on an
  older Pydantic, defining a component raises `RuntimeError` when its event `data` class
  or State is a Pydantic v2 model or Pydantic dataclass, or when its
  plain `data` class holds one. This includes the `data` and State
  classes that `Citry(model_base=BaseModel)` turns into models. Upgrade
  Pydantic before upgrading Citry.
- **Some other schemas are refused when the component class is
  defined:** defining the component raises `ValueError`, and the error
  names the field and the fix, when a field that the browser may write,
  or a `Json[...]` field (a Pydantic type that makes a field read its
  value from JSON text), holds one of these:

    - a tree like the one above, in a `Json[...]` field or in a field of
      a Pydantic model State;
    - extra keys that the class allows and checks against a type that can
      fail with many errors, such as a model, a list or dict, or a union
      of several types;
    - items that can fail with several errors, in a list or dict inside a
      `Json[...]` field that has a wrap validator around it (a validator
      that receives the value and the next validator), such as a list of
      models;
    - a recursive model, dataclass, or TypedDict (one that can hold
      itself) with no wrap validator on the way back to itself, in a
      model State where Citry reads browser writes only as JSON text, as
      it does with `ConfigDict(strict=True)`.

    To fix the last case, remove the setting that makes Citry read the
    State only as JSON text (the strict setting, for example), leave the
    field out of `_model`, or add a wrap validator to the recursive
    class, which makes Citry apply the 32-level limit there.

    The details list every case, including the ones that are fine
    ([details](https://citry.dev/security/#schemas-citry-refuses)).
    Citry cannot run this check on a class it sees only when a call
    arrives, such as a model inside a plain `data` class. A call that
    reaches it (for State, a call that writes it) fails with a 422
    (`invalid_args`) that says "The value could not be checked.", and
    Citry logs the field and the fix once.
- **A `pydantic.v1` class can't be used in an Events `data` class or
  inside a Pydantic v2 State:** defining a component now raises
  `ValueError`, naming the class, when its `data` class is, or holds, a
  `pydantic.v1` model or dataclass. This covers a field, a list, dict,
  optional or union, a nested class, and a Pydantic v2 class that holds
  one or checks a field with one of its methods, such as
  `PlainValidator(Model.parse_obj)`. A Pydantic v2 State whose fields
  hold such a class, or are checked with such a method, is refused the
  same way. Some of these worked in 0.7.x and are now refused: a
  `pydantic.v1` dataclass as the `data` class, a plain class that holds
  one, and a field checked with a v1 method. Before you upgrade, make the
  v1 classes Pydantic v2 models, and check fields with Pydantic v2
  validators. A State that is itself a `pydantic.v1`
  model still works
  ([details](https://citry.dev/security/#schemas-citry-refuses)).
- **Clear server-stored State:** if a component sets
  `State._storage = "server"` and your cache keeps its data across
  restarts (Redis, for example), delete the keys that contain
  `citry:state:` once every process runs the new version, so that Citry
  restores only State that the new version saved. A cache `prefix`, or
  the `KEY_PREFIX` of a Django cache, goes in front of that text, so the
  pattern below matches it anywhere in the key. With Redis, for example:

    ```sh
    redis-cli --scan --pattern '*citry:state:*' | xargs redis-cli unlink
    ```

    Add `-h`, `-p` and `-n` to both `redis-cli` calls if your Redis needs
    them, and check first that no other application on that Redis keeps
    keys that contain the same text. If you skip this, State that the
    older version saved stays in the cache, and Citry restores it as it
    was saved, until each entry expires. An entry expires after
    `State._max_age`, or after 24 hours when you do not set it, so
    waiting that long works too. A page that is open when the keys go asks
    the visitor to reload on its next event call. An in-memory cache
    starts empty on every restart, so it needs nothing.
- **A 422 names only the first bad item of each list or dict:** code or
  tests that expect a message for every bad row must change. Show the
  first bad row and let the user fix it and send again, or declare the
  field loosely (for example `list[dict]`), check each row in your
  handler, and raise `EventError` with a message for each bad one. A
  browser write to a Pydantic v1 State still lists up to 20 items, and
  so does a list or dict inside a wrap validator. A fixed-length tuple
  lists each bad position, and extra keys that a model allows and checks
  against a type list each bad key
  ([details](https://citry.dev/security/#check-event-data)).
- **Data with too many errors gets one message:** event data with more
  than about 1,000 errors gets a single message in place of the field
  messages. The message sits under `fieldErrors._args`, the key for a
  message about the whole call's data, and a State write gets it under
  `fieldErrors._state`. A form that shows
  only the message next to each field then shows nothing, so also show
  the message, as in `$error('submit')?.fieldErrors?._args` for a
  handler named `submit`
  ([how](https://citry.dev/events/forms/#eventerror-field-errors)).
- **Checking one request's data stops after about 1 second of CPU time:** once
  the request's checks have used that time, the call being checked fails
  with a 422 that says the data took too long to check, under
  `fieldErrors._args` (`fieldErrors._state` for a State write). A
  browser write to a Pydantic v1 State stops the same way. Citry does
  not interrupt a slow validator of your own. Every check of a
  `pydantic.v1` State, including restoring it at the start of a call,
  counts toward that second, so a request with several such calls can
  get the "took too long" 422.
  Run more than one worker process so one slow request does not delay
  others ([details](https://citry.dev/security/#check-event-data)).
- **Deep trees in event data need a discriminator:** event data that
  holds a tree like the one above, with no discriminator on the union of
  node classes, fails with a 422 under `fieldErrors._args` that says the
  data is nested too deeply to check, or too large or nested too deeply
  to check. A Pydantic model fits about 14 levels with one child per
  node. When `And` and `Or` hold their children in fields of the same
  name, it fits about 8 levels with two. More children, or more data in
  each node, lower those numbers. Declare the discriminator as above and
  a tree can nest about 30 levels.
  Citry checks a plain class or dataclass itself, without reading
  discriminators, so make the node classes Pydantic models, or keep the
  nesting shallow
  ([details](https://citry.dev/security/#trees-in-event-data)).
- **Data nested more than 32 levels is refused:** a Pydantic v2 class
  that checks event data or a browser State write now stops at 32
  levels, and the call fails with a 422 under `fieldErrors._args`
  (`fieldErrors._state` for a State write) that says the data is nested
  too deeply. Citry logs a warning naming the class. A model,
  dataclass, TypedDict, wrap validator, `Iterable[...]` or
  `Generator[...]` field, or union of classes each counts as one level
  (a model State that Citry reads only as JSON text counts only wrap
  validators, as explained above). Send data with fewer levels, or give
  a recursive union a discriminator. The limit does not apply when
  Citry restores State that the server saved. If your server runs
  requests on threads with less than 1 MiB of stack (some Windows and
  Alpine setups), call `threading.stack_size(1024 * 1024)` before the
  server starts them
  ([details](https://citry.dev/security/#check-event-data)).
- **Events checks every item of an `Iterable` field before the handler
  runs:** a bad item of an `Iterable[...]` or `Generator[...]` field in
  event data or a State write now fails the call with a 422. Before, it
  raised a `ValidationError` when the handler read the item, so a `try`
  around your loop no longer catches it. A union whose `Iterable`
  member has a bad item now tries its next member. The handler gets an
  iterator over the checked items, and the items count toward the same
  limits as the rest of the data.
- **Pydantic dataclass State writes are checked when they arrive:**
  without `validate_assignment`, on a browser write Citry runs the
  class's field validators, model validators, `__post_init__`, and any
  `default_factory` that takes the other fields, as the class does when
  it is built. A value the class refuses now fails the call with
  `invalid_args` (422) and a message for that field in `fieldErrors`
  (`fieldErrors._state` for an error from a model validator or
  `__post_init__`), and the State does not change. Before, the call
  succeeded and the next call failed with `stale_state`. The State still
  keeps each value as the browser sent it, as the class does: a
  `tuple[int, ...]` field written as `[1, 2]` holds the list `[1, 2]`
  until the next call restores it as the tuple `(1, 2)`. With
  `validate_assignment`, Citry checks each assigned field, as the class
  does.
- **A Pydantic dataclass State refuses a write when a validator raises
  an unexpected error:** when a validator of a Pydantic dataclass State
  raises an exception other than `ValueError` or `AssertionError`, such
  as `RuntimeError`, while Citry checks a browser write, the call now
  fails at once with a 422 and "The State could not be checked." under
  `fieldErrors._state`, with or without `validate_assignment`. Before, a
  dataclass State without `validate_assignment` accepted the write, and
  the next call failed with `stale_state` or a server error. A model
  State already answered this way.
- **Calls in one request that carry the same State can share one
  restore of it:** a request can carry several calls, and when they
  carry the same State values, Citry can restore the State once and give each
  call its own copy. A validator with a side effect, or a default that
  changes each time, such as `default_factory=uuid4`, can then run fewer
  times than there are calls.
- **Citry no longer calls your `data` class's `model_validate`,** or an
  override of it, for event data. Move that logic into a
  `model_validator`.
- **Pydantic plugins no longer record event checks:** plugins such as
  Logfire do not see the checks of event data and State writes, because
  Citry runs them with its own copy of the class's validator.
- **Validators that read `info.mode` can fail State writes:** Citry
  can check a browser write to a Pydantic model State both as Python
  values and as JSON, so a validator that answers differently in the two
  modes can refuse a valid write. Keep such validators out of a model
  State.
- **Long field paths can refuse a valid call:** with a Pydantic v1
  State, a Pydantic model State whose browser writes
  Citry can check only as JSON text (a strict one, for example), or,
  rarely, a Pydantic v2 class whose checks Citry could not set up (it
  logs an error), Citry adds up the length of the field paths in the
  data (such as `scores.alice.3`) and answers with a 422 before Pydantic
  runs when they add up to too much text. This most often refuses a
  large write to such a State when it has a union without a
  discriminator or many required fields. Send shorter keys or fewer
  items, or give the union a discriminator
  ([details](https://citry.dev/security/#the-path-limit)).
- **A signed State write past `State._max_bytes` is refused before the
  handler:** a browser write that makes a State in the default signed
  storage larger than `State._max_bytes` now gets a 422 before the
  handler runs, when the response would carry a new State. Such a call
  used to fail with a server error after the handler, or succeed when
  the handler made the State small again. Raise `_max_bytes`, or have
  the browser write less.
- **Text with an unpaired surrogate is refused in State writes:** a
  browser write of text with an unpaired surrogate character, which
  JSON allows as an escape such as `"\ud800"`, now gets a 422 before
  the handler runs. It used to fail with a server error after the
  handler (a server-stored `pydantic.v1` State saved it).
- **Deeply nested `pydantic.v1` State writes are refused sooner:** a
  browser write to a `pydantic.v1` State now fits about 120 levels of
  nesting, down from about 135. A deeper write gets a 422 that says it
  is nested too deeply.

## Added

- You can now set the page's CSRF token once with
  `Citry.configure({csrf: {...}})`. Event calls and `$i18n` message
  requests both read it.

## Changed

- The security guide now recommends `base-uri 'self'` in your Content
  Security Policy.

## Fixes

- `$i18n.switchLocale()` no longer fails with status 403 on Django: the
  request that loads the new locale's messages now sends the page's CSRF
  token, the same way event calls do.
- A few kinds of long input no longer take seconds or more to handle:
  a `style` value with many unclosed `/*` comments, a request path for
  a route with several parameters in one path segment (such as
  `{name}-{version}`, which an extension can add), and, in the
  browser, a `Redirect` URL with a long run of spaces. Each now takes
  time in step with its length. The style and route results are the
  same as before, and a `Redirect` URL is refused for its scheme exactly
  when it was before.
- Parsing a long `style` value, or an event request with long strings,
  now uses less memory.
- When an event call's arguments or State updates hold a very long
  dict key, or a dict key with many dots, Citry no longer copies that
  key into the field path of every item below it. The field messages
  are the same as before.
- Citry now stops checking event data and State writes early once they
  fail (see Upgrading from 0.7.x). A 422 also stops listing field
  messages once their text would pass 65,536 characters, and its
  message says how many it left out. It cuts a field message longer
  than 1,000 characters to that length
  ([details](https://citry.dev/security/#check-event-data)).
- A call with bad input to a Pydantic dataclass `data` class, or to a
  Pydantic dataclass State with `validate_assignment`, now gets a 422
  with field messages, not a server error.
- A call that writes to a `pydantic.v1` State is faster: Citry checks
  each written State once, before the handler, and reuses that result
  for the rest of the request.
- A `pydantic.v1` State write that Citry cannot read back from the State
  it stores now gets a 422 with field messages before the handler, not a
  server error after it.
- A browser write to a `pydantic.v1` State that holds a model with a
  forward reference Pydantic never resolved now gets a 422, not a server
  error after the handler, and Citry logs Pydantic's message, which
  names the model.
- A `data` class whose own code raises, such as a `__post_init__`, no
  longer ends the whole request: only its call fails. An `EventError`
  keeps its own status, any other error becomes a `handler_error` (500),
  and the request's other calls still run.
- `security_javascript` now counts a `<script>` as running when its
  `type` holds a character such as U+3000, and finds a `data:` URL in a
  `<meta http-equiv="refresh">` padded the same way. Chromium skips these
  characters, so it ran the script or opened the URL.
- `security_javascript` now counts an HTML `data:` document as running
  code when it holds anything outside plain ASCII, because a browser can
  read such text in another encoding. Write such text as a character
  reference with `&` and `#` percent-encoded, such as `%26%23233;` for `é`.
- `security_javascript` now reports text that changes a page's tags when
  a browser reads the page in another encoding: the escape bytes `ESC $`
  and `ESC (`, non-ASCII text in a `<![CDATA[` section, and a `<` followed
  by a NUL byte, which spells a tag when a response names UTF-16. A page
  could use `<meta charset>` to hide a script from the check. Only text
  Citry does not escape, such as `Markup`, can trigger this. Send pages
  with `charset=utf-8` in the `Content-Type` header, so the browser reads
  them the way Citry does.
- `security_csp` and `security_javascript` now find more scripts and
  event handlers in pages that browsers read differently from the way
  Citry's check read them. A page in `Markup` could hide a script from
  the check, and the browser would run it with no click:
    - Inside `<select>`, current browsers keep tags such as `<style>` and
      `<svg>`, and older ones drop them. Citry's check now reads such a
      page both ways.
    - Around SVG and MathML elements that hold HTML, such as an SVG
      `<title>`, Citry's check closed elements that browsers keep open.
    - Firefox and Chromium each differ from the HTML standard on a few
      misplaced end tags, such as `</p>` in an SVG `<title>`. Citry's check
      now also reads such a page the way each of them does.
    - An `iframe srcdoc` document is now read in both quirks and standards
      mode, because Chromium and Firefox pick different modes for it.
    - Your app's own script can put HTML into the body of a page that is
      already open, with `innerHTML` on an ordinary element such as a
      `<div>`. Browsers build some tags differently there: a `<frameset>`
      builds nothing, and the open page's doctype picks the mode. Citry's
      check now also reads such HTML that way, in both quirks and
      standards mode.
    - In an interactive component, Vue inserts HTML such as `Markup` as one
      block, which Chromium builds with the markup inside a `<noscript>` as
      real elements. Citry's check now reports an event handler or script
      inside a `<noscript>` too.

    The check does not cover HTML that your own script inserts with
    `innerHTML` into an element with special parsing rules, such as
    `<svg>`, `<math>`, `<table>` and its parts, `<select>` or `<form>`.
    Build such HTML in a `<template>` element and move its contents into
    place instead (see the security page).

- `security_javascript="forbid"` now raises `ValueError` for a page with
  markup that browsers may build into a page that Citry's check does
  not build, and `"warn"` and `"omit"` warn about it. A page that
  passed before can now raise. Such markup is rare, and usually a
  mistake, for example an `<svg>` or `<math>` right after a formatting
  element that an outer end tag closed, as in `<p><b>Bold</p><svg>`
  (close the `<b>` first). A valid MathML
  `<annotation-xml encoding="text/html">` and a `<table>` inside an
  unclosed `<p>` under a few old doctypes (see the security page) are
  refused too. The error names what to change, and the security page
  lists every case.
- The output checks now refuse a page that keeps hundreds of elements open
  across much of it while it also holds markup that Citry reads in several
  ways, so that checking any page stays fast. No ordinary page comes
  close.
- Citry now writes the ESC character in an escaped value as `&#27;`, in
  text and attributes, on normal and Vue pages. On a page read as
  ISO-2022-JP, a raw ESC could change how the browser read the HTML after
  it, so that ordinary escaped values could run code. Visitors see the
  same text, except inside `<style>`, `<xmp>` and
  `<script type="text/plain">`, which show `&#27;` as written, as they
  already do for `&lt;`. `Markup.format()`, `%`, `+` and `join` use
  MarkupSafe's own escaping, which keeps ESC.
- `security_csp` and `security_javascript` now read a numeric reference
  to a control character in an attribute value as the browser does, so
  `java&#1;script:` is a relative link, not a `javascript:` URL, and
  `Markup` in an attribute keeps such a character.
- `citry preview` now sends `charset=utf-8` with text responses, as the
  Django, ASGI and WSGI adapters do.
- With the `Debug` extension on, a render whose HTML starts with many
  comments, such as a comment inside a `<c-for>` over a long list, could
  take minutes. It now takes time in step with the length of the HTML.
  The same fix applies to third-party extensions that, like `Debug`, skip
  their wrapper around a whole HTML document.
- After you change a component's `State._storage`, a page rendered before
  the change gets a `stale_state` error on its next event call, and the
  visitor is asked to reload.
- `css_data()` now raises `ValueError` for a value with a control
  character outside a quoted string, so the browser reads the value the
  way Citry checked it. Tab, newline, carriage return and form feed are
  still allowed. Remove the character, or keep it inside a quoted string.