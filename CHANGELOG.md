# Release notes

## Unreleased

Events now refuses event data and State writes that are too large, too
deeply nested, or too slow to check, and Pydantic classes in Events need
Pydantic 2.13.0 or newer. The upgrade notes below list what can fail or
change.

### Upgrading from 0.7.x

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
      models.

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
- **Deeply nested trees in event data are refused:** event data that
  holds a tree like the one above, with no discriminator on the union of
  node classes, fails with a 422 under `fieldErrors._args` that says it
  is too large or nested too deeply to check. When `And` and `Or` hold
  their children in fields of the same name, a Pydantic model fits about
  15 levels with one child per node, and about 8 with two. More
  children, or more data in each node, lower those numbers. Declare the discriminator as above to check deeper trees.
  Citry checks a plain class or dataclass itself, without reading
  discriminators, so make the node classes Pydantic models, or keep the
  nesting shallow
  ([details](https://citry.dev/security/#trees-in-event-data)).
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

### Added

- You can now set the page's CSRF token once with
  `Citry.configure({csrf: {...}})`. Event calls and `$i18n` message
  requests both read it.

### Changed

- State tokens in the default signed storage now use a key that Citry
  derives from your secret for this one use, so values that other code
  signs with the same secret (such as Django's `SECRET_KEY`) cannot be
  used as State. Signed tokens from earlier versions stop working when
  you upgrade: an open page asks the visitor to reload on its next event
  call. During a rolling deploy, old and new processes reject each
  other's signed tokens until every process runs the new version.
- Script and stylesheet tags that Citry writes for files it serves now
  carry `integrity` and `crossorigin="anonymous"` at every
  `security_script_integrity` value, including `/citry/citry.js` and
  `local_files = "serve"` files. The browser now refuses a file that a
  proxy or CDN changed, and a `citry.js` from a different version than the
  page, so clear proxy, CDN, and whole-page caches when you upgrade. A CDN
  that serves these files from another host must send
  `Access-Control-Allow-Origin`. During a rolling deploy, a page can fail
  until a reload reaches the same version.
- The security guide now recommends `base-uri 'self'` in your Content
  Security Policy.

### Fixes

- `css_data()` now raises `ValueError` for a value with a control
  character outside a quoted string, so the browser reads the value the
  way Citry checked it. Tab, newline, carriage return and form feed are
  still allowed. Remove the character, or keep it inside a quoted string.
- A `css_data()` stylesheet in a configured cache is now built again from
  its stored values each time it is served. One stored by an earlier
  version returns 404 until a page with the same values renders again,
  and a cached component with `css_data()` values renders again once.
  Upgrade every process that shares the cache: one on an earlier
  version keeps writing entries that the new version does not serve.
- `$i18n.switchLocale()` no longer fails with status 403 on Django: the
  request that loads the new locale's messages now sends the page's CSRF
  token, the same way event calls do.
- A few kinds of long input no longer take seconds or more to handle:
  a `style` value with many unclosed `/*` comments, a request path for
  a route with several parameters in one path segment (such as
  `{name}-{version}`, which an extension can add), and, in the
  browser, a `Redirect` URL with a long run of spaces. Each now takes
  time in step with its length and gives the same result as before.
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

## v0.8.0

### Fixes

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
- `Citry(secret=...)` now raises an error for a secret that is empty or
  only whitespace, whether passed alone or as an entry of a list, and for
  an entry that is not a plain `str`. Before, Citry accepted such a
  secret, and a request could then send State signed with it. If your
  secret can come out empty, for example
  `[os.environ["NEW"], os.environ.get("OLD", "")]`, `Citry(...)` now
  raises a `ValueError` that gives the entry's position; leave out keys
  that are not set. `citry.contrib.django.secret()` skips such entries
  for you. The setting takes a string, a list, or a tuple; pass any other
  collection as a list.
- After you change a component's `State._storage`, a page rendered before
  the change gets a `stale_state` error on its next event call, and the
  visitor is asked to reload.
- Event calls sent by the built-in transport now send the CSRF token only
  to the page's own origin, and a redirect answer makes the call fail
  instead of being followed. Return `actions.Redirect` to send the visitor
  to another page. `Citry.events.configure({csrf})` now rejects a header
  name that `Citry.configure` rejects.
- Event calls, `$i18n` message requests, and the `Redirect`, `PushUrl`,
  and `ReplaceUrl` actions now resolve a relative URL against the page's
  own address, so a `<base>` element no longer changes where they go. If
  your page sets `<base href>` on purpose, write these URLs as paths that
  start with `/`.
- Events now refuses event data and State writes that nest more than 40
  objects and unions deep, when a Pydantic v2 class checks them. The call
  gets a 422 that says the data is nested too deeply, and Citry logs a
  warning naming the class. If your server runs requests on threads with
  less than 1 MiB of stack, raise it with `threading.stack_size()`
  ([details](https://citry.dev/security/#check-event-data)).

## v0.7.0

Citry 0.7.0 catches more mistakes. A component input of the wrong type
now raises `TypeError` when the component renders, and `citry check` and
the editor report many HTML, Vue, and Events mistakes they used to miss.
Pages that repeat a `simple = "vue"` component render much faster on
standard CPython. Vue scoped slots and listener modifiers such as
`.outside` now work in templates. Citry supports Python 3.15 and needs
3.11 or newer.

### Upgrading from 0.6.x

- **Upgrade the packages together:** install `citry-ui` 0.4.0 and
  `citry-lsp` 0.3.0 with Citry 0.7.0. Citry UI 0.3.0 rejects some valid
  inputs under the new type check and fails to render under the new
  `$c-tr` rule, and citry-lsp 0.2.0 cannot read your app's lint data once
  `security_csp` is set. citry-lsp 0.3.0 runs over stdio only. The VS
  Code extension 0.3.0 accepts citry-lsp 0.3.0. It also stays off,
  highlighting included, in VS Code's Restricted Mode until you trust the
  workspace.
- **Python 3.11 or newer:** raise `requires-python` to `">=3.11"` before
  upgrading.
- **Inputs of the wrong type raise `TypeError`:** fix the value or widen
  the annotation. To keep the old behavior, set
  `check_input_types = False` in a component's nested `class Lint:` or in
  `LintSettings`.
- **`alt=""` on a component tag passes `""`:** write a bare attribute,
  such as `<c-Grid compact />`, to pass `True`. `<c-cache enabled="">`
  and `<c-i18n client="">` now raise.
- **Deep templates have a limit:** a template can nest tags at most 512
  levels deep, and at most 256 of those levels can be `c-` tags or
  `c-if`/`c-for` attributes. Move a deeper part into its own component.
- **`$c-tr` bindings are written in the template:** a binding that comes
  from Python data, through `c-$c-tr:...`, a `$c-tr` key in `c-bind`, or
  an `on_attrs_resolved` hook, raises `VueCodeError`.
- **More values are checked before they reach the browser:** for example,
  `actions.Redirect` to a scheme other than `http:` or `https:`, and a
  `c-bind` key such as `onclick` or `innerHTML`, raise `ValueError`.
  Write such attributes in the template, and use an `http:` or `https:`
  URL for `Redirect`.
- **HTML fragments on a page with a CSP nonce:** serialize them with
  `csp_nonce=page_nonce`, or they do not start. An interactive page also
  refuses a `data:` URL for a component script.
- **Some expressions are now errors:** `{{ }}` and an expression with an
  unmatched `)` raise `SyntaxError`.
- **`citry check` may fail on a project that passed before:** the new
  HTML, Vue, and Events rules can fail the check; each has a `rule_*`
  setting. With `security_csp` set, the check also reports inline
  scripts, styles, and `on*` attributes.
- **`citry check --format json` ranges count from 0,** with columns in
  UTF-16 code units.
- **Forms send text:** with `@c-submit`, number and range inputs send
  `"3"`, not `3`, so a Pydantic model in strict mode needs a change.
- **A `<c-fill fallback="...">` with a `@c-` handler or a Vue binding
  that reads Vue data now raises.**
- **`dict[K, V]` fields in an Events `data` class are converted:** a
  handler gets `data.scores[3]` for a `dict[int, ...]` field, not
  `data.scores["3"]`.
- **Extension routes that serve JavaScript or CSS need the right
  `content_type`,** because every Citry route now sends `nosniff`.
- **`citry.contrib.django.secret()` returns a list** when
  `SECRET_KEY_FALLBACKS` is set.
- **`ext-preview` needs Playwright 1.64.1 or newer;** run
  `playwright install chromium` again.
- **Event request limits:** if you set `_max_envelope_bytes`, rename it to
  `_max_body_bytes`.
- **Sub-path URLs:** if you passed your sub-path to `set_mounted_prefix()`
  in a process that also calls `mount()` or `urlpatterns()`, remove it
  there, or the URLs start with it twice.

The sections below list every change.

### Added

- An extension's route can limit how much of a request body Citry
  reads: pass `URLRoute(max_body_bytes=...)` a function that returns the
  limit in bytes. Citry reads at most one byte past the limit, so the
  handler must still reject a longer body
  ([details](https://citry.dev/advanced/extensions/#serve-extension-routes)).
- You can write an Events `State` as a Pydantic v2 or v1 model, by hand or
  through `model_base`. A handler that sets a field to a value the model
  rejects fails that call, before Citry stores it
  ([details](https://citry.dev/events/state/#pydantic-state)).
- You can make every plain `class Kwargs:`, `TemplateData`, `JsData`,
  `CssData`, `State`, and Events `data` class a Pydantic model that subclasses your
  own `BaseModel` subclass, so its `model_config` applies to all of them:
  pass it as `Citry(model_base=MyModel)`. A dataclass base or
  `typing.NamedTuple` works too
  ([details](https://citry.dev/concepts/inputs-and-validation/#model-base)).
- `citry check` and the editor now report a `<script>` or `<style>`
  element, an `on*` attribute such as `onclick`, or a `javascript:` URL
  written directly in a template, when `security_csp` is `"warn"` or
  `"strict"`. They are warnings with `"warn"` and errors with `"strict"`,
  so a project that uses `"strict"` can see `citry check` fail after the
  upgrade
  ([details](https://citry.dev/ide/template-linting/#find-csp-problems)).
  If your editor's language server runs an older citry-lsp, update it
  too: once `security_csp` is set, it reports "App worker protocol
  mismatch" and stops reading your app.
- A component can pass Vue data to a fill, as a Vue scoped slot: write
  `<c-slot name="item" :row="row" />`, and read it in the fill with
  `<c-fill name="item" v-slot="{ row }">`. Python slot data (`c-item`,
  `data="..."`) works beside it
  ([details](https://citry.dev/vue/slots/#scoped-slots)). When the server
  knows the slot's values, it writes the fill's HTML with them.
  `citry check` warns when `v-slot="{ ... }"` reads a name the slot does
  not pass, which Vue would leave `undefined`.
- Citry now supports Python 3.15.
- You can now use `.outside`, `.window`, `.document`, `.debounce`, and
  `.throttle` on Vue listeners such as `@click` on HTML elements, as in
  `@click.outside="open = false"` or `@input.debounce.300ms="search()"`
  ([details](https://citry.dev/syntax/vue/#listener-modifiers)).
- A handler declared with `@event(detached=True)` can be called with
  `$sendEvent(name, args, {wait: false})`, so a read-only call such as a
  spell check no longer waits behind the app's slower calls. A detached
  handler may return data, `Dispatch`, `Redirect`, URL changes, and
  `Download`, but not a render or a State change
  ([details](https://citry.dev/events/actions/#skip-the-queue-for-a-read-only-call)).
- When `template_data()` builds its result through a helper, you can list
  its keys in `Lint.template_data_keys`. `citry check` and the editor then
  report only names outside the list, not every name in the template.
  `citry check` also warns about a literal key the list leaves out.
  Rendering ignores the list
  ([details](https://citry.dev/ide/template-linting/#list-template-data-keys)).
- `citry check` now fails on a misspelled directive such as
  `<div c-iff="show">`, which Citry would render as an `iff` attribute; set
  `rule_misspelled_directive` to change the severity.
- `citry check --static` now uses the severity a component's own `Lint`
  class sets as a plain string, such as `rule_alpine_attribute = "ignore"`.
  Editor tools can read the same values from
  `PythonTemplateRegion.owner_lint`, a tuple of `ComponentSourceLint`.
- `citry check` and the editor now report HTML mistakes that the browser
  passes over without an error: a misspelled attribute, tag, or `aria-*`
  name (`titel`, `<dvi>`, `aria-expandd`), a block such as `<div>` inside
  a `<p>`, two elements with the same `id`, and an `<img>` without alt
  text. The image check is a warning and the others are errors, so
  `citry check` may now fail on an existing project; each rule has a
  `rule_*` setting
  ([details](https://citry.dev/ide/template-linting/)). With your
  application loaded, a component's only top-level `<img>` is reported when
  the component sets `inheritAttrs: false`, because no parent's `alt` can
  reach it then.
- `citry check` and the editor now report Vue mistakes that would stop a
  component from rendering: an expression that is not valid JavaScript,
  such as `v-if="open &&"` (`rule_invalid_vue_expression`), where the
  message names the JavaScript parser's error and the editor underlines the
  place it points to, and `v-model`
  on an element that holds no value, such as `<form>`
  (`rule_invalid_model_target`). A misspelled DOM event in a listener,
  such as `@clik`, is a warning (`rule_misspelled_event`).
- `citry check` and the editor now run Vue's compiler over every template,
  every `<c-if>` branch included, and report what it rejects at the line you
  wrote, such as a `<div>` directly inside a `<table>`, a `<button>` inside a
  `<button>`, or a `v-else` with no `v-if` before it, before a component that
  uses Vue fails to render (`rule_vue_compile_error`, an error by default)
  ([details](https://citry.dev/ide/template-linting/#templates-vue-cannot-compile)).
- The misspelled-directive check now also reports a typo in a Vue
  directive, such as `v-iff` or `v-elif`, which otherwise stops the page
  with an error in the browser. With your application loaded, a custom
  directive that the component registers in the `directives` option of
  `$component()` is not reported.
- With your application loaded, `citry check` now reports more mistakes
  that fail only when the page runs
  ([details](https://citry.dev/ide/template-linting/)):
    - a component that `<c-for>` repeats without `#c-key` on a page that uses
      Vue (`rule_missing_component_key`);
    - a component that assigns to its own prop, such as
      `@click="open = false"` in its template or `this.open = false` in its
      JavaScript (`rule_prop_assignment`), which the editor reports too;
    - `@c-*` arguments the server would reject: an unknown key, a missing
      required field, or a literal of the wrong type, such as
      `save({amount: '1'})` for an `int` field
      (`rule_unknown_server_event_field`, `rule_missing_server_event_field`,
      `rule_incompatible_server_event_field`);
    - a control in a form whose `@c-submit` sends the form's fields, when
      the handler's data class does not declare its `name`, such as
      `<input name="qeury">`, or no control is named after a required field
      (`rule_unknown_form_field`, `rule_missing_form_field`);
    - a `var(--name)` that misspells a `css_data()` key, such as
      `var(--acent)`, as a warning (`rule_misspelled_css_variable`).

    These are errors by default except the CSS check, so `citry check` may
    now fail on an existing project.

- With your application loaded, `citry check` now warns about a link to a
  page or file your app does not serve, such as `<a href="/abuot">` or
  `<img src="/static/avtar.svg">`, and suggests the path you likely meant
  (`rule_unknown_url`). It asks the web framework you mount Citry with
  through `citry.contrib.flask.mount()`, `citry.contrib.fastapi.mount()`,
  or `citry.contrib.django.urlpatterns()`, so point `--app` at the module
  that mounts Citry
  ([details](https://citry.dev/ide/template-linting/#find-links-to-missing-pages)).
  Links such as `/shop/about`, in an app served below a sub-path such as
  `/shop`, are checked too: `citry check` reads the sub-path from FastAPI's
  `root_path`, Flask's `APPLICATION_ROOT`, or Django's
  `FORCE_SCRIPT_NAME`.
- With your application loaded, `citry check` now warns about a
  `self.inject("bord")` whose key no component above it provides, and
  suggests the key the page does provide, such as `board`
  (`rule_unknown_inject_key`,
  [details](https://citry.dev/ide/template-linting/#find-unknown-inject-keys)).
- If you build editor tooling on `citry.analysis`, you can now check a
  fill's `data` name against the slot's `SlotInput[T]`: pass
  `slot_data_types` to `build_schema_template_shadow()` or
  `build_inferred_template_shadow()`, keyed by the `slot_target` that
  `TemplatePythonControl` now records.
- With your application loaded, `citry check` now warns when `js_data()`
  sends a module-level value that JSON cannot carry, such as a
  `PurePosixPath`, including one nested in a dict or list, behind a
  conditional or `Const(...)`, or read as an attribute such as
  `config.EXPORT_DIR`.
- `Citry.inspect_components()` now says, for each Events handler, whether
  an argument key the data class does not declare fails the call
  (`extra_fields`) and whether Citry or Pydantic checks the values
  (`validated_by`).
- `citry check --static` now lists, as a note, each template it skips
  because the component's base class comes from another module of your
  project.
- `discover_python_templates()` and `discover_python_component_assets()`
  accept `app_components`, the classes a loaded application registers in
  the file, so a tool can find the templates of components whose base
  class comes from another module.
- `citry check --types` now reports a parent method used as a child
  component's event listener, such as `@hide="hideCard"`, when it cannot
  accept the values the child's typed `emits` declares, for example a
  method that needs a second value the child never sends. The
  [props and events guide](https://citry.dev/vue/props-and-events/) shows
  how to type an event's values so both the child's `$emit` and the
  parent's method are checked.
- You can now wrap a server-only value, such as an API token, in
  `citry.Secret`, and Citry refuses to send it to the browser: rendering
  fails with an error naming the component and key when `js_data()`,
  `css_data()`, or State holds one, `citry check` warns about one in
  `js_data()`, and a template shows it as `***`. Annotate a `Kwargs` field
  as `Secret[str]` to reject a plain string. A cached component cannot take
  a `Secret` input unless its `Cache.vary()` leaves the secret out
  ([details](https://citry.dev/advanced/secrets/)).
- With your application loaded, `citry check` now warns when a template
  class misspells one the component's CSS styles, such as `class="bord"`
  for `.board`; such an element renders unstyled with no error
  (`rule_misspelled_css_class`,
  [details](https://citry.dev/ide/template-linting/#find-misspelled-css-classes)).
- You can now turn on two stricter CSS checks, off by default:
  `rule_undeclared_css_class` reports every template class that no CSS
  Citry reads declares, and `rule_undeclared_css_variable` reports every
  `var(--name)` without a fallback that nothing sets. Turn them on in
  `LintSettings` or in a component's `Lint` class
  ([details](https://citry.dev/ide/template-linting/#find-classes-without-css)).
- With `Citry(mode="development")`, turning a page into HTML now warns
  when two of its elements share an `id`, such as two components that
  both write `id="board"` or one component rendered twice, and names the
  components ([details](https://citry.dev/guides/development-mode/#repeated-ids)).
- With `Citry(mode="development")`, the browser console now warns when
  Vue's first render of a part it builds in the browser differs from the
  HTML the server sent, for example a `created()` hook that opens a panel
  on wide windows. A production page does not load the check
  ([details](https://citry.dev/vue/server-rendering/#first-render-warnings)).

### Changed

- **Breaking:** Citry now checks and converts each key and value of a
  `dict[K, V]` field in an Events `data` class, as it already did for each
  item of a list. A key such as `"3"` fills a `dict[int, ...]` field as
  the number `3`, and a value typed as a dataclass arrives as an instance
  of it. If a handler reads such a field as `data.scores["3"]` or
  `data.points["a"]["x"]`, use the declared types instead:
  `data.scores[3]` and `data.points["a"].x`. A Pydantic `data` class
  already did this.
- `$error(handler).fieldErrors` now lists at most 20 errors for fields
  that the call's `data` class does not declare (or `State` fields it may
  not write), and at most 20 item errors in each list or dict field.
  `message` then ends with how many more there were, as in "1,000 more
  field errors are not shown." Errors for other fields, and the fields of
  an `EventError` you raise, are always listed in full.
- Every response from a Citry route now has the standard
  `X-Content-Type-Options: nosniff` header, so the browser uses the
  route's `Content-Type` as given. If an extension route of yours serves
  JavaScript or CSS, give it the right `content_type`.
- `citry.contrib.django.secret()` now includes Django's
  `SECRET_KEY_FALLBACKS`, so `Citry(secret=secret())` keeps accepting
  values signed with an old key while you rotate `SECRET_KEY`. With
  fallbacks set it returns a list of keys, so its return type is now
  `str | list[str]`; without fallbacks it still returns the plain string.
- `citry check` now leaves out findings in the components of a library
  you registered with `register_library()`, such as Citry UI, so an app
  that uses Citry UI no longer fails the check on code it cannot change.
  One note says how many findings it left out. Pass
  `--include-libraries`, or set `LintSettings(include_libraries=True)`, to
  report them
  ([details](https://citry.dev/advanced/cli/#check-library-components)).
- **Breaking:** a template can now nest tags at most 512 levels deep, and
  at most 256 of those levels can be Citry logic: every `c-` tag except
  `<c-raw>`, and each `c-if=`, `c-elif=`, `c-else`, `c-for=` or `c-empty`
  attribute. A deeper template raises `SyntaxError` at the tag that goes
  too deep, and `citry check` reports it as `citry.parse.too-deep`; move
  the inner part into its own component. Plain elements nested more than
  512 deep used to render.
- **Breaking:** a written empty value on a component tag, such as
  `<c-Avatar alt="" />`, now passes `""` instead of `True`, so a `str`
  input accepts it. To pass `True` to a `bool` input, write the bare
  attribute, as in `<c-Grid compact />`; `compact=""` now fails with a
  `TypeError` that says so. The same holds for data passed to a fill
  (`<c-slot x="" />` gives the fill `""`), and `<c-cache enabled="">` and
  `<c-i18n client="">` now raise too, with the same advice to write the
  bare attribute. HTML elements are unchanged,
  and so is the tag form `<c-if cond="">`. A component that forwards its
  inputs to an element with `c-bind` now writes `alt=""` there instead
  of a bare `alt`, which HTML reads the same way.

    ```citry-html
    <c-Avatar alt="" />      <!-- before: True; now "" -->
    <c-Grid compact="" />    <!-- now "": a bool input rejects it -->
    <c-Grid compact />       <!-- True, as before -->
    ```

- Output that an `on_render` hook passes to another component, as in
  `return Frame(body=result)`, or that an `on_component_rendered` hook
  passes on as `ctx.render`, no longer carries the component's own
  `data-cid-*` and `data-ccss-*` markers on its top elements, the same as
  content passed as a nested template. The other component's root
  element, which is now the component's root, still carries them, so
  scoped CSS and `[data-cid-*]` selectors match that root instead. When
  both components set the same `css_data` variable, the passed output
  takes the value from that root.
- **Breaking:** Citry now requires Python 3.11 or newer, because Python
  3.10 reached its end of life on October 1, 2026. On Python 3.10, pip
  keeps installing Citry 0.6.x. If your project declares
  `requires-python = ">=3.10"`, raise it to `">=3.11"` before upgrading,
  or uv and other lockfile tools cannot pick this release.
- **Breaking:** a component input of the wrong type now raises
  `TypeError` when the component renders, in development and in
  production. Fix the value or widen the annotation; to keep the old
  behavior, set `check_input_types = False` in a component's nested
  `class Lint:`, or pass
  `Citry(lint=LintSettings(check_input_types=False))`. If you use Citry
  UI, upgrade it at the same time: earlier Citry UI releases reject some
  valid inputs under this check. A value that equals a `Literal` member,
  such as a `StrEnum` member or `Markup("sm")`, passes the check. For a
  component from a registered library such as Citry UI, the error names
  the library and asks you to change the value you pass.

    ```python
    class Card(Component):
        class Kwargs:
            title: str

    card = Card(title=123)
    str(card)
    # TypeError: Card.Kwargs.title expects str, got int (123). ...
    ```

    Citry checks only the outer type of each `Kwargs`, `TemplateData`,
    `JsData`, `CssData`, and Events `State` field, so `list[str]` accepts
    any list. A field's own default always passes, so `title: str = None`
    keeps working, and Pydantic models keep their own rules
    ([details](https://citry.dev/concepts/inputs-and-validation/#typed-kwargs-checks)).

- `citry check` now fails, and the editor shows an error, on an HTML
  attribute value the browser does not accept, such as
  `<button type="sumbit">`. Set `rule_invalid_attribute_value="warning"` in
  `LintSettings` to keep the previous behavior.
- `citry check` now fails on a boolean attribute with a value such as
  `disabled="false"`, which still disables the element. Leave the
  attribute out to turn it off, or let Vue set it from a JavaScript
  boolean, as in `:disabled="saving"`.
- `citry check` now also reports a listener on a component tag whose
  lowercase name the child does not declare, such as `@hdie`, and suggests
  the declared event it probably means (`hide`). DOM event names such as
  `@click` still pass. Set `rule_undeclared_component_event` to change
  the severity, which is a warning by default.
- `citry check` and the editor now report a string for a Boolean Vue prop,
  such as `:open="open ? 'open' : 'closed'"`, unless the string is empty
  or the prop's own name. They also check both results of a condition
  whose results are literals.
- The render error for a component that `<c-for>` repeats without
  `#c-key`, or with a duplicate one, now names the tag, its template and
  line, and the repeated value, and says to combine the loop values into
  one key when loops are nested. An element whose `#c-key` clashes with
  another key now names its template, line and column.
- A server expression that reads a Vue `v-for` variable, such as
  `c-name="member.name"` inside `<li v-for="member in members">`, now fails
  with an error that names the tag, its template, and the line, says the
  variable exists only in the browser, and shows the `<c-for>` that fixes
  it, instead of a bare `KeyError`. It is still a `KeyError`, so an
  existing `except KeyError` keeps catching it.
- In `citry check --format json`, every finding's `range` now counts lines
  and columns from 0, with columns in UTF-16 code units, as the Language
  Server Protocol does. Syntax errors, unknown variables, unknown
  components, and i18n catalog errors used to count from 1; if your tool
  subtracted 1 from those, stop. Each `range` also says which text it
  counts in, `"source_kind": "file"` or `"inline"` (a string written on
  the class, such as `template`), and a `JsData` field's `origin` now
  names its Python file
  ([details](https://citry.dev/advanced/cli/#check-json-output)).
- The render error for `v-model` on an element that holds no value, such
  as `<div>` or `<form>`, now names each such element with its template
  and line and lists the elements `v-model` works on, instead of an
  internal Vue compiler message.
- A form submitted through `@c-submit` now gives the handler the same
  values as the same form posted without JavaScript: text such as `"3"`
  fills an `int` or `float` field, a checked checkbox fills a `bool`
  field, and the submit button that sent the form adds its `name`. Number
  and range inputs now send their text, so a handler that reads
  `event.args` directly, or a Pydantic model in strict mode, gets `"3"`
  instead of `3`, as it already did without JavaScript.
- The `ext-preview` extra now needs Playwright 1.64.1 or newer, whose
  bundled Node.js does not trust the affected emSign root certificate when
  `playwright install` downloads browsers. After upgrading, run
  `playwright install chromium` again to fetch the matching browser.
- In a component that uses Vue, a slot's fallback that a caller shows
  through `<c-fill fallback="...">` now raises an error when it holds a
  `@c-` event handler or a Vue attribute that uses Vue data, such as
  `:title="message"` or `ref`. These used to read the caller's Vue data
  and run the caller's handler of the same name. To fix it, leave the
  slot unfilled so the receiving component shows its own fallback. Or
  pass the value with a `c-` binding such as `c-title`, which reads the
  receiving component's Python values. Or put the Vue binding on an
  element in the caller's fill around `{{ fallback }}`, where it reads
  the caller's Vue data.
- A template expression with an unmatched `)`, such as `{{ a) or (b }}`,
  now raises `SyntaxError`, and so does an empty one such as `{{ }}`.
  Citry used to run the first as `(a) or (b)` and render the second as
  `()`.
- **Breaking:** write a `$c-tr` translation binding and its values in the
  template. A binding that comes from Python data, through `c-$c-tr:...`,
  a `$c-tr` key in a `c-bind` mapping, or an `on_attrs_resolved` hook, now
  raises `VueCodeError`, because its value is browser JavaScript. To let
  the server decide whether the browser translates an element, return a
  flag from `js_data()` and make the binding's values expression return
  `null` where the server-rendered text should stay
  ([details](https://citry.dev/i18n/browser/#keep-the-server-text)):

    ```citry-html
    <!-- Before -->
    <span c-$c-tr:my-app-save="True if use_catalog else None">
    <!-- After: useCatalog comes from js_data() -->
    <span $c-tr:my-app-save="useCatalog ? {} : null">
    ```

- Events State kept on the server (`_storage = "server"`) now expires after
  24 hours unless `State._max_age` sets another lifetime, so a page left
  open longer asks the visitor to reload. A browser write that would make
  it larger than `State._max_bytes`, now 64 KiB by default for server
  storage, answers 422 before the handler runs; set `_max_bytes` higher, or
  to `None`, to allow more. The default `InMemoryCache` counts this State
  against a 64 MiB budget, apart from other entries, and drops the entry
  used longest ago when full; set `InMemoryCache(state_max_bytes=...)` to
  change that. `max_entries` no longer counts these entries
  ([details](https://citry.dev/performance/cache-backends/#server-stored-state)).
- **Breaking:** Citry now checks more of the values it sends to the
  browser. Each of these raises an error, a `ValueError` unless the item
  says otherwise:
  - `actions.Redirect(url)` with a scheme other than `http:` or `https:`.
    A URL with no scheme, such as `/projects/`, still works. Use a full
    `https:` URL or a URL with no scheme instead. A URL containing a control
    character, such as a line break, also raises.
  - A `c-bind` mapping key, or a name an `on_attrs_resolved` hook adds,
    that starts with `on`, such as `onclick`, or that is `innerHTML`,
    `outerHTML`, or `srcdoc`. The same holds for such a name passed to
    `<c-element>` through `c-bind`, `<c-component c-is>`, or Python code.
    Write the attribute in the template instead: `@click` on a Vue page,
    `@c-click` to call a handler of your component, or `onclick="..."`. A
    hook can still change the value of a handler the template wrote, but
    it cannot add one. A `<c-element>` with `c-is` or `c-bind` also
    refuses a handler written in the template, because it cannot tell a
    name you wrote from one passed in as data. There, use a Vue `@event`
    in a component with `js`, or write a plain element in a `c-if`
    branch.
  - An attribute name that your code supplies, such as a `c-bind` key,
    and that contains whitespace, a control character, a quote, a
    byte-order mark, a lone surrogate, or a Unicode noncharacter. Rename
    the key.
  - A tag such as `script`, `style`, `iframe`, or `xmp`, whose
    contents the browser reads as raw text or code, passed to a
    `<c-element>` that has `c-is` or `c-bind`, or to the built-in
    `element` component in a Python call. Write such an element directly
    in the template.
  - Markup inside a `<c-element>` that renders `textarea` or `title` in
    an interactive component raises `TypeError`: a tag, a child
    component, `<c-raw>`, or a `Markup` value. Put only text there.
  - A `css_data()` value that has a comment, a brace, `<`, or a backslash
    outside a string or `url()`; a `;` or `!` outside brackets; an
    unbalanced bracket; or a malformed string or `url()`. A null or
    surrogate character, `</style`, or `<!--` raises anywhere. Text with
    whitespace that does not start with a function is quoted for you, so
    only a null or surrogate character, `</style`, or `<!--` fails there.
    `rgb()`, `calc()`, and `url()` values, SVG data URLs included, still
    work.
  - An Events binding on one of Vue's lifecycle hooks, such as
    `@c-vnode-mounted` or `@c-vue:mounted`, whether the template writes it
    (a `SyntaxError` when the template loads) or a `c-bind` mapping key
    supplies it (a `ValueError` when the page renders). Vue ran such a
    binding when the element or component mounted, updated, or unmounted,
    not on a browser event. Bind the handler to a browser event, such as
    `@c-click`.
  - An Events binding whose event name starts with something other than a
    letter, or contains a character other than a letter, digit, `-`, `_`
    or `:`, such as `@c-1x` or `@c-a;b`. Rename the event.
- **Breaking:** on a page with a CSP nonce, an HTML fragment whose
  components use Vue or server events starts only when you serialize it
  with the page's nonce, as in
  `serialize(deps_strategy="fragment", csp_nonce=page_nonce)`. Otherwise
  it does not start, and the browser console shows an error. For a
  `Render` that a server event returns as HTML to a client of your own,
  set `extensions_defaults["events"]["_csp_nonce"]` to a function that
  returns the calling page's nonce
  ([details](https://citry.dev/security/#html-fragments)).
- **Breaking:** on an interactive page, Citry refuses a `data:` URL for a
  component script, so the page's Vue app, or the fragment, does not start
  ([details](https://citry.dev/advanced/dependency-files/#add-a-library-url)).

### Fixes

- A form field named `__proto__` is now sent with the Events call like
  any other field.
- An Events `actions.Redirect` to a relative URL, such as `"?page=2"` or
  `"next"`, now takes a visitor who posts a plain HTML form without
  JavaScript to the same page as with JavaScript, not to a "not found"
  page. The server resolves the URL against the page in the `Referer`
  header, so on a page whose `Referrer-Policy` hides its address, use a path
  that starts with `/` ([details](https://citry.dev/events/actions/#redirect-to-a-page)).
- An Events `actions.Redirect` to a URL with non-ASCII characters, such as
  `"/café"` or `"https://bücher.example/"`, now takes a visitor who posts a
  plain HTML form without JavaScript to the same page as with JavaScript,
  instead of the wrong page or a server error.
- An Events request whose JSON nests arrays and objects more than 200
  levels deep is now rejected with a 400 error that says so, instead of a
  server error. The i18n messages route applies the same limit.
- Citry now also checks inside the type of a browser write to an Events
  `State` field: each item of a `list[int]` or `tuple`, each value of a
  `dict[str, int]`, and the listed values of a `Literal[...]`. The error
  names the item that failed, such as `tags.2`. A Pydantic `State` already
  did this.
- An Events `State` field or `data` field typed as a `TypedDict`, or as a
  list of them, no longer causes a server error. Citry checks that the
  value is an object; it does not check the keys inside it. A `data` field
  typed as a `Protocol` without `@runtime_checkable` now gets an error
  that names the field, instead of a server error.
- In a component that uses Vue, Vue syntax inside an element with `v-pre`
  stays as written, as Vue does. `v-once`, `@click.bogus`, or
  `<transition>` there no longer stops the template from loading, and a
  `<slot>`, `<component>`, `<teleport>`, or `<keep-alive>` there is a
  plain element. The server now writes an attribute such as `:x="y"`
  there; it used to appear only after Vue ran.
- In a component that uses Vue, Citry's `{{ }}` values, `c-` bindings
  such as `c-title`, `<c-if>`, `<c-for>`, and `simple = True` and
  transparent components inside an element with `v-pre` now render, and
  the `v-pre` element's own `c-` bindings and `#c-key` work. The page
  used to show internal names such as `{{ $citryPrepared.citryText0 }}`,
  or the template failed to compile.
  Where Citry's values meet something Vue reads, such as a child
  component, a `<c-slot>`, or a `:title` on the `v-pre` element itself,
  rendering raises an error that says what to move. A `v-pre` element that
  holds only HTML and Vue syntax renders as before.
- `citry check` and the editor now leave Vue syntax on or inside an
  element with `v-pre` as written, as Vue does. A `v-if="a"` there no
  longer reports that `a` is not available, and a `:dir="'rlt'"` there is
  no longer reported as a wrong `dir` value. The editor no longer offers
  Vue completion or hover help there. Both elements of a `v-if`/`v-else`
  pair there are in the page, so a repeated `id` on them is now reported.
- `citry format` and the editor's format command no longer add a line break
  where two tags touch, such as between `<td>` cells or `<option>`s or just
  inside a `<c-fill>`, or at the start or end of a template string written
  right against its quotes. That line break was new text in the rendered
  HTML. Whitespace you wrote is still re-indented; to spread compact markup
  over lines, add a line break between the tags once.
- An oversized request to Citry's event endpoints no longer fills the
  server's memory: by default Citry stops reading a body past 1 MiB and
  rejects a form post with more than 1,000 fields, both with
  `payload_too_large`. Change the limits
  with `_max_body_bytes` and `_max_form_fields` in
  `extensions_defaults["events"]`
  ([details](https://citry.dev/security/#limit-event-request-sizes)). On
  Django, these limits now govern event requests in place of
  `DATA_UPLOAD_MAX_MEMORY_SIZE`. If you set the undocumented
  `_max_envelope_bytes`, `Citry(...)` now raises `ValueError`; rename it
  to `_max_body_bytes`.
- Apps served below a sub-path, such as `/shop`, now load Citry's
  scripts and styles and reach its Events endpoints. Citry's URLs start
  with the sub-path each request was served under, whether a proxy,
  `uvicorn --root-path`, a WSGI mount, or Django's `FORCE_SCRIPT_NAME`
  sets it. With FastAPI and Starlette, `mount()` adds a middleware that
  reads each request's `root_path`
  ([details](https://citry.dev/advanced/web-frameworks/#serve-below-a-sub-path)).
  The render cache keeps separate entries per sub-path. To delete an entry
  from a background job when only your server sets the sub-path, pass it
  to `component_cache_key()` or `fragment_cache_key()` as `sub_path=`.
  If you worked around this by passing the sub-path to
  `set_mounted_prefix()` in a process that also calls `mount()` or
  `urlpatterns()`, remove the sub-path there, or the URLs start with it
  twice.
- On PyPy, `import citry` no longer fails with `No module named
  '_symtable'`. On PyPy, `citry check` and the editor check `js_data()`
  values and template types less fully, and both print a note saying so.
- A `<c-for>` whose clause ends with a comment, such as
  `each="item in items  # every item"`, now renders. It used to fail with
  "unexpected EOF while parsing".
- In a component that uses Vue, when `<c-fill fallback=...>` cannot show
  the receiving component's fallback, the error now says what to change
  instead of reporting an internal error. This happens when your fill
  puts `{{ fallback }}` inside a component that is not transparent, such
  as `<c-Box>{{ fallback }}</c-Box>`, or when the receiving component
  placed that `<c-slot>` inside content it passes to another component.
  With a transparent receiving component, the first case used to render
  without the fallback. When a fallback shown this way prints a `Slot`,
  such as `{{ icon }}`, the error names it as slot content.
- `citry check` now checks a `<c-trans>` whose `c-values` starts on an
  indented line, which it used to skip.
- `citry format` and the editor's format command no longer add trailing
  spaces to blank lines in a component's `template`, `js`, or `css` string
  in a Python file, which Ruff flags as `W293`.
- A Vue listener with Alpine's `.minus`, `.underscore`, or `.spacebar` key
  modifier now fails when the template loads and says what to write
  instead. Vue matches none of these names, so the listener never ran.
- In a component that uses Vue, a fill that holds a Citry component now
  fails at render, with an error that names both components, when the
  receiving component's `<c-slot>` sits inside a Vue `v-for`. The page used
  to fail in the browser once the list held more than one item. Loop with
  `c-for` around the `<c-slot>` instead
  ([details](https://citry.dev/vue/slots/#scoped-slot-limits)).
- Without a configured cache, the stylesheets that `css_data()` produces
  no longer pile up in memory, one per distinct set of values, for the
  life of the process. They now count toward `vue_asset_max_bytes`, and
  Citry drops the ones used longest ago first. If a page that stays open
  loses its styles, raise the limit or configure a cache.
- In a component that uses Vue, a Vue expression holding an unpaired
  surrogate escape, such as `v-text="'a\ud800b'"`, no longer makes the
  server write U+FFFD and the escape's hex digits into the page. Vue now
  writes that value in the browser instead.
- In a component that uses Vue, a `{` before a Citry tag and a `{` after
  it, as in `{<c-if cond="True">{ x }}</c-if>`, now show as text, as they
  do without Vue. Vue used to read the two braces as an interpolation and
  run the text between them as JavaScript, and a `{` right before a value,
  as in `{<c-if cond="True">{{ x }}</c-if>`, failed to compile.
- In a component that uses Vue, a `<c-raw>` block, a `Markup` value, or
  `#c-ignore` contents now renders inside `<c-i18n>`, `<c-provide>`, or
  another transparent component whose content ends up in a component's
  slot. Rendering the page used to fail with "prepared opaque HTML values
  do not match definition declarations".
- Rendering on several threads at once, as a server's workers do, no
  longer fails, hangs, or holds up other threads in these cases:
    - When several threads render their first pages at the same time,
      such as right after the server starts, those renders no longer fail
      with "dictionary changed size during iteration" on a page with
      `simple = "vue"` components, or, on a page serialized for Vue, with
      "early selected-tree compilation does not match the current render
      preparation".
    - On free-threaded Python, a component's first render now fails less
      often with "dictionary changed size during iteration" while another
      thread renders, but it can still happen.
    - Without `initialize()`, renders that start on several threads at
      once no longer fail with `CitryLifecycleInProgress`: renders on
      other threads wait for the first one to finish discovery. A render
      inside a module import or a reset hook still raises instead of
      waiting, and so does a wait longer than a minute
      ([details](https://citry.dev/advanced/component-discovery/#initialize-before-starting-worker-threads)).
      Call `initialize()` at startup to avoid the wait.
    - A slow cache backend, such as Redis over the network, no longer
      holds up cached renders on other threads or a hot reload while
      Citry writes to it, and a hot reload no longer waits while
      `Citry.clear()` wipes the backend.
    - A slow load hook, such as a template preprocessor in
      `on_template_loaded`, no longer holds up renders of other
      components. When several threads render a component for the first
      time at once, such a hook can run once per thread, and every render
      gets the same result
      ([details](https://citry.dev/advanced/extensions/#hooks-that-run-twice)).
    - A render no longer hangs when an extension's load or compile hook,
      a function in a component's `Dependencies` class, or a function
      marked `Const` renders another component while another thread
      resets a template or files, as a hot reload does.
    - A hot reload that arrives while Citry loads a component's template,
      JS, CSS, or messages, or prepares its template for `Const` values,
      no longer leaves the old content in use.
- In a component that uses Vue, a `<c-fill fallback="...">` that shows
  the receiving component's fallback now shows the receiving component's
  values, not the caller's values with the same names, and no longer fails
  when a value is `Markup`. A fallback shown this way can now hold
  components, including inside a `<c-provide>` or a component marked
  `transparent = True`. One that holds a `<c-slot>`, or any other
  component with content between its tags, raises an error, where it
  used to drop that content or fail with an unrelated error.
- In a component that uses Vue, when one component captures a fill as a
  `Slot` and a transparent component elsewhere shows it, the fill now
  shows its own text. It used to be able to show some of the page's text
  in its place.
- In a component that uses Vue, `&amp;#40;` written in text or an
  attribute value now shows `&#40;`, as the same component without Vue
  does; it used to show `(`. A static `style` with `&quot;` inside a
  declaration and a static `<component is="...">` now read their character
  references correctly too, and a dynamic slot name that is not
  JavaScript, such as `#[x&amp;y]`, now reports Vue's invalid-expression
  error instead of compiling to broken JavaScript.
- Printing a slot's result in a component and also passing it to a child
  component tag that prints it now raises "This content is printed in more
  than one place", naming the component that prints it the second time,
  before the slot's components render twice. It used to render them twice
  and then fail with "deferred part vanished", or fail at serialization
  with "The same rendered component id was encountered more than once".
  Both this error and the one for a rendered component printed twice,
  such as `Badge().render()`, now say what to do: pass the slot without
  calling it, or the element `Badge()`
  ([details](https://citry.dev/concepts/slots/#show-a-fill-in-two-places)).
- On a page that uses Vue, printing a rendered component twice now raises
  `RuntimeError`, as it does on other pages. It used to raise a
  `TypeError`: "render occurrence appears more than once".
- With `@event(latest_wins=True)`, a call that a newer call replaced no
  longer changes the page. Its remaining actions are dropped, including
  delayed ones with `wait=False`. The newer call no longer waits for its
  delays, and `$loading()` and `citry:events:after` stop reporting it as a
  success.
- When an Events handler's `Render` replaces its component and also
  schedules a delayed action with `wait=False`, such as
  `Dispatch("Form:saved", delay=3, wait=False)`, that action no longer
  runs once the page has accepted a newer result from the component that
  replaced it.
- A delayed `Redirect` with `wait=False` now runs even when the page
  accepted a newer result for its component first, because it reports a
  result the server already produced. It is dropped only when its call
  is superseded, its component is removed, or the page's Vue app shuts
  down.
- In a component that uses Vue, a character reference inside a directive
  value now means what it means in Vue: `@click="msg = 'Tom &amp; Jerry'"`
  sets `Tom & Jerry`. Citry used to keep `&amp;` in strings written in
  `@click`, `v-if`, `v-show`, `v-for`, `v-slot`, `v-model` and other
  directives.
- A template expression nested deeper than about 97 chained operators such
  as `+`, or 65 nested brackets, now raises `SyntaxError`, and so does a
  template with more than 100,000 `{`. Much deeper input used to crash the
  process, and input just past these limits used to render, so split such an
  expression into smaller ones.
- A template that nests 50 or more `<c-if>` or `<c-for>` tags now renders.
  It used to fail with `SyntaxError: too many nested parentheses`.
- `js_data()` nested about 1,000 levels or deeper no longer raises
  `RecursionError` while Citry copies it. `js_data()` that holds itself,
  and has no other bad key, now raises `ValueError: Circular reference
  detected`.
- In a component that uses Vue, `<c-for>` tags nested a few hundred deep,
  each with a `<c-empty>`, no longer raise `RecursionError` while Citry
  writes the data Vue receives, on Python 3.11 and PyPy or when your web
  framework already uses part of Python's stack.
- Rendering, serializing, or running `citry check` on a template nested
  up to 256 levels deep no longer raises `RecursionError`, even when your
  web framework already uses part of Python's stack. This includes
  `<c-slot>` tags nested inside each other's fallback content.
- Slot content that a long chain of components passes on with
  `<c-fill><c-slot /></c-fill>` no longer raises `RecursionError`.
  Content passed on through an expression, such as `{{ content }}` where
  `template_data()` returns `slots["default"]`, can still raise it after
  about 80 components.
- In a component that uses Vue, a `Markup` value without tags, such as
  `Markup("a&#127;b")`, now keeps a character such as U+007F, or the
  Unicode noncharacter U+FDD0, that a numeric reference names, as the
  same component without Vue does. It used to drop it and show `ab`.
- In a component that uses Vue, an attribute value such as
  `href="/search?q=x&region=eu"` now keeps `&region=eu` as written, as
  the browser and Vue do. Citry used to read `&reg` in it as `®`,
  which broke the link.
- A `security_csp` or `security_javascript` report now names the
  innermost component around the reported element, where it said
  "settled render output". Content passed into a slot counts under the
  component that renders the slot.
- With `security_javascript="omit"`, a submit button, an input, a
  `select`, or a `textarea` inside a `<form>` is no longer reported as a
  control with no fallback, because the browser can submit the form
  without JavaScript. A `type="button"` button and an input of type
  `button` or `reset` are still reported.
- In a component that uses Vue, a `<c-raw>` block, a `Markup` value, or
  `#c-ignore` contents that self-close an element whose contents the
  browser reads as text, such as `<iframe/>`, `<textarea/>`, or
  `<script src="…"/>`, now fail the render with "is not a complete HTML
  fragment". The browser ignores the `/` on these tags and reads the rest
  of the page as that element's text. Write the end tag instead:
  `<iframe></iframe>`.
- When `DJANGO_SETTINGS_MODULE` is set, `citry check` and the other
  `citry --app` commands now start Django before they import the `--app`
  module, as `manage.py` does, so a module such as `config.urls` whose
  views import models no longer fails with `AppRegistryNotReady`. If
  Django is installed but cannot start, the command shows why. Without
  Django installed, Citry ignores the variable.
- A form that calls a server event can now keep Django's hidden
  `csrfmiddlewaretoken` input inside it. The server removes that field
  before it checks the event's data class, with or without JavaScript,
  instead of rejecting the call for an unknown field. Name other token
  fields in `extensions_defaults={"events": {"_csrf_field_names": [...]}}`.
- In a component that uses Vue, a component call inside a `<table>`,
  `<tbody>`, `<thead>`, `<tfoot>`, `<tr>`, or `<colgroup>` now renders.
  It used to fail with "Foster parenting moved this element before the
  nearest open table".
- A component can now insert markup it received in a `c-*` attribute
  more than once, such as `<div>{{ body }}</div><aside>{{ body }}</aside>`.
  Each place gets its own render of the markup, as a `<c-slot />` used
  twice does, so the components inside render once for each place. It
  used to fail with "deferred part vanished from its .parts list before
  resolution". A slot called once in `template_data()` whose result the
  template prints twice now fails with an error that names the component,
  before any component inside it renders.
- An Events data class field annotated as `Literal[...]` now accepts the
  values it lists. Every call used to fail with "Unsupported annotation".
- An Events `State` field annotated as a tuple is a tuple again in event
  handlers, instead of the list that JSON turned it into.
- A `security_csp="warn"` or `security_javascript="warn"` warning now
  points at the line in your code that turned the page into HTML, not at
  a line inside Citry. A warning from an Events response points at the
  web framework code that called Citry, because your handler has already
  returned.
- With `security_csp="warn"`, a Vue page that cannot hydrate and whose
  body holds a raw `<style>` element with an attribute, such as
  `<style media="print">`, now keeps its body out of the served page until
  Vue mounts, as it already did for a `<style>` without attributes.
- On Python 3.11, `security_javascript` now reports an
  `<iframe>`, `<object>`, or `<embed>` whose `data:text/html;base64,` URL
  has padding that is not valid base64, such as a stray `=` after a
  complete group, as it already did on Python 3.12 and later.
- If Citry's `security_csp` or `security_javascript` check of the finished
  page hits an internal bug, `serialize()` now reports the page as one it
  could not read, as it already does for a page it cannot parse, so
  `security_csp="warn"` warns and returns the page. It used to raise an
  error that `except Exception` does not catch.
- A Vue page whose body text contains `</body>`, for example inside a
  comment, now serializes instead of raising `ValueError`; until Vue
  mounts, its body is empty.
- A component's `on_dependencies()` now runs once per rendered instance
  each time an interactive page is serialized, as documented, instead of
  twice.
- Serializing a render again with `deps_strategy="simple"`, after an
  interactive `"document"` or `"fragment"` serialization of it, now writes
  its scripts and stylesheets like a fresh render instead of leaving them
  out.
- In a template expression, a string with a lone surrogate escape, such
  as `row['\ud800']`, now means U+D800, as it does in Python. With the
  expression sandbox on (the default), some templates used to read U+FFFD
  (the replacement character), so the same lookup could read a different
  key in different templates. Also with the sandbox on, an f-string in a
  template expression now behaves as in Python: `f'{{a}}'` gives `{a}`
  instead of raising `KeyError`, `'x' f'{y}'` keeps its `'x'`, and
  `f'{x=}'` shows `x=` before the value.
- A Vue page whose text or attribute values hold a control character such
  as DEL (U+007F) or U+0001, or a Unicode noncharacter such as U+FDD0, now
  hydrates, so Vue no longer builds it again in the browser. A `<c-raw>`
  block or `Markup` value holding one of these characters in an
  interactive component now renders. It used to fail with "is not a
  complete HTML fragment".
- On Python 3.14, a `simple = "vue"` component now renders when its class
  body, or a plain base class it inherits from, holds an annotation such as
  `start: int = 3`. It used to fail with "instance member
  __annotate_func__ is not supported".
- A numeric character reference with thousands of digits, such as `&#`
  followed by 5,000 zeros and `106;`, now reads as the browser reads it
  (here `j`) instead of raising `ValueError` ("Exceeds the limit (4300
  digits) for integer string conversion"). This covers `citry check`,
  `Markup` values in text and in `c-` attributes such as `c-href`, the
  `security_csp` and `security_javascript` checks in `serialize()`, and
  any attribute of a page with a `<textarea>` that serializes without
  JavaScript. An Events timing with that many digits, such as
  `@c-input.debounce.<5,000 digits>ms`, now fails with the JavaScript
  safe-integer error, and one written with digits other than ASCII
  `0`-`9` is now an unknown modifier.
- In an interactive component, a `<c-raw>` block or `Markup` value whose
  HTML writes a character reference the browser reads as text, such as
  `&copy 2026` without `;`, `&nbsp`, `&#127;` or `&#x80;`, now renders.
  It used to fail with "is not a complete HTML fragment". Other HTML the
  browser repairs, such as a stray `<` or an unfinished comment, now
  fails with "is not well-formed HTML" and names the parse error.
- On Python 3.14, a t-string built in a template expression with the
  expression sandbox on now gives each `Interpolation` its source text as
  `expression` (`t'{x + 1}'` gives `'x + 1'`), as it does with the sandbox
  off. It used to be `''`.
- On Python 3.14, an Events `State` class with one annotation that does not
  resolve (such as a type imported only for type checkers) now keeps the
  type checks on its other fields when the module has no `from __future__
  import annotations`. Every field used to accept any value from the
  browser.
- An `on_render` hook that passes the output it received to another
  component, such as `return Frame(body=result)`, now works inside another
  component's template and on pages that use Vue. The same holds for an
  `on_component_rendered` hook that wraps `ctx.render`, and when the
  component or one around it is cached. It used to raise `RuntimeError:
  The same rendered component id was encountered more than once`, and on
  a Vue page it failed even for a component used on its own, as did a
  hook that returns `result` unchanged.
- In a component that uses Vue, the server now writes more elements whose
  attributes the browser reads as plain text, such as `foo="1"`, so less
  of the page waits for the browser to build it. A `<form>` with an
  attribute that may match the `name` or `id` of a control inside it now
  leaves the form's parent to the browser, or the whole page when the
  form is at the page root.
- In Safari, when a stylesheet linked in the served page fails to load,
  Citry now requests it again and reports an error if it still fails, as it
  does in other browsers. Before, the page mounted without its styles and no
  error appeared.
- In a component that uses Vue, an `<input>`, `<select>`, `<option>`, or
  `<textarea>` inside or carrying `v-pre` no longer gets a stray
  `v-citry-vue-owned` attribute in the page. A `v-pre` element also no
  longer fails to render when it holds a transparent component with
  `#c-key`, such as `<c-provide>`, or when it holds Vue attributes such as
  `:title` and sits in slot content that a component writes for another
  component it does not enclose. At the root of a component with `css_data()`, a
  `v-pre` element now renders, or raises an error that says what to move,
  where it used to fail with an internal compiler error.
- In a component that uses Vue, the server now writes `hidden`,
  `disabled`, `readonly` and the other boolean attributes the way Vue's
  server renderer does, so an element whose `hidden` is a string such as
  `'false'` or `'until-found'`, or a number other than 0, is hidden (or
  searchable) in the HTML the server sends instead of showing until Vue
  starts.
- Rendering, checking, or formatting a deeply nested template, or a page
  whose data nests hundreds of levels, no longer crashes the Python
  process on a thread with a small stack, such as a thread on musl Linux
  or one started after a small `threading.stack_size()`.
- In a component that uses Vue, the server now writes elements nested up
  to 400 deep, where it used to stop at about 130 and leave the rest of
  that part of the page for the browser to build.
- A component's scoped CSS now reaches all of its top-level tags, and only
  those, when `Markup` or a `<c-raw>` block in it holds a self-closed tag
  such as `<div/>`, the content of `<xmp>` or `<iframe>`, or tags the
  browser closes on its own.
- A child component placed inside a `<textarea>` now writes its HTML
  there, where the page showed Citry's internal `<template c-render-id>`
  placeholder.
- `citry format` now wraps a tag when the text after it makes the line
  too long, where it used to measure only the tag.
- `citry format` no longer fails on an expression that is valid only
  inside parentheses, and it leaves an expression as you wrote it when it
  cannot reformat it safely.
- A component's nested extension config class written as an abstract
  base class, such as `class Events(metaclass=ABCMeta):`, no longer fails
  with "'_abc_impl' is not a recognized Events config attribute".
- Citry's Vue runtime and server events keep working when data puts an
  `id` or `name` on an element that matches a name Citry reads, such as
  `<div id="Citry">` or `<form name="createElement">`. A form field named after a form method, such
  as `addEventListener`, can still stop the component that holds the form,
  so do not take field names from data unchecked
  ([details](https://citry.dev/security/#check-form-field-names)).
- Citry now labels the JavaScript and CSS files it serves as UTF-8, and
  writes each non-ASCII character in a `css_data()` value as a CSS escape
  (`表` becomes `\8868`). Before, a page declared in an encoding such as
  GBK or Big5 could misread such a character in a linked stylesheet and end
  a quoted string early. Styles render the same, but script that reads the
  custom property with `getComputedStyle()` now gets the escape text instead
  of the character.
- A dynamic slot name, as in `<c-slot c-name="which" />`, now picks only a
  field that the component's `Slots` class declares. Before, a name such as
  `__class__` or `_fields` could select another attribute of the `Slots`
  object.
- A tag with thousands of attributes no longer ends the process when the
  output checks (`security_csp`, `security_javascript`), the checks on
  `Markup` and `<c-raw>` HTML, or the hydration checks read the page.
  These checks now refuse HTML with more than 1,024 attributes on one tag,
  or more than 16 start tags of any one of `<html>`, `<head>` and
  `<body>`, which could take seconds to read: the output checks report the
  page as unreadable, `Markup` and `<c-raw>` HTML in an interactive
  component raise `ValueError`, and hydration leaves the server HTML out.
- The same checks now also refuse HTML that keeps more than 512 elements
  open at once (about 510 nested elements), or that leaves formatting tags
  such as `<b>` and `<i>` open or misnested so often that the parser would
  copy more than 250,000 elements and attributes. Reading such HTML could
  take minutes or gigabytes of memory. The checks react as they do to the
  limits above. A template that nests about 510 elements or more makes a
  page over the 512-element limit, so the output checks report it as
  unreadable.
- The i18n number formatters and `tr()` raise `ValueError` for a
  `Decimal` with more than 32,768 digits before or after the decimal point,
  before writing any digits.
- WSGI, Flask and Django hosts no longer read the body of a GET, HEAD or
  OPTIONS request, the same as ASGI hosts.
- `InMemoryCache` removes an expired entry at the next write, even when
  nothing reads it again.
- A call whose caller cannot use a new State token, such as a plain JSON
  API call, no longer writes server-stored State to the cache.
- Citry checks how deeply request JSON nests before parsing it, and
  refuses more than 200 levels, the same on every Python version. A State
  nested that deep now fails when its token is made, naming the component,
  instead of on the next call.
- `parse_string_style`, and the `style` values Citry merges or formats
  in Python, now take time that grows with the length of the string, and
  split it into declarations exactly as before.
- The built-in asset routes now match long request paths in linear time.
- Citry's routes now answer `404` to a path with a second `/` after the
  mount prefix, such as `/citry//ext/events/call`, with a line break at
  the end, or without its leading `/`, and `405` to a `HEAD` request on a
  route that does not accept `GET`, such as the Events call route. Before,
  these got past a path or method rule in your web framework (on Django,
  only the `HEAD` request did, and it also skipped the CSRF check). If a
  client of yours builds Citry URLs by joining a base that ends in `/`
  with a path that starts with `/`, it now gets `404`, as it already did
  on Django
  ([details](https://citry.dev/advanced/extensions/#serve-extension-routes)).
- `citry ext run preview serve` and `preview render` now answer only
  requests addressed to `http://localhost` or `http://127.0.0.1`, and
  refuse calls and fetches sent from pages on other sites. Open the URL
  the command prints; to reach it from another machine, forward the port
  and open it as `localhost`. `render --base-url` needs such an address
  too
  ([details](https://citry.dev/advanced/previews/#browse-the-gallery)).
- Citry now sends `charset=utf-8` with every `text/*` response it builds
  from a string, such as the plain-text and HTML body that a form post
  without JavaScript gets back, so the browser does not have to guess the
  encoding.
- A render cache entry is reused only when the templates running in this
  process wrote the same template text, `$c-tr` bindings, and values
  expressions, so an entry left by a different version of a template is
  rendered again. After a restart, a cached component may render once more
  before its entry is used.
- The `security_csp` and `security_javascript` checks now also report a
  `javascript:` URL that an SVG `<animate>` or `<set>` writes into a link,
  such as `<set attributeName="href" to="javascript:...">`, the same as
  they report `href="javascript:..."`. A page that has one raises
  `ValueError` under `security_csp="strict"` and
  `security_javascript="forbid"`, and warns under `security_csp="warn"` and
  `security_javascript="warn"` or `"omit"`. Use a normal URL instead.
- `security_javascript` now reports a `data:` URL of an SVG, other XML,
  or unknown type, such as `data:image/svg+xml,...`, with or without a
  script, wherever the page loads or opens it as a document: in an
  `iframe`, `frame`, `object`, or `embed`, in a link or form, or in a
  `<meta http-equiv="refresh">`. The browser can run scripts in such a
  document, and Citry does not read it. It also checks HTML `data:` URLs
  there for a script, including one with tabs or line breaks or written
  with `; base64`, and reports one in UTF-16. `"forbid"` raises
  `ValueError`, and `"warn"` and `"omit"` warn. To show an SVG image, use
  `<img>`, which runs no scripts and is not reported. A download link
  such as `<a download href="data:application/zip;base64,...">` is
  reported too unless its type is plain text, CSS, CSV, JSON, an image,
  media, a font, a PDF, or `application/octet-stream`; serve the file
  from a URL or give it the type `application/octet-stream`.

### Performance

- `citry check` is much faster on deeply nested templates: checking one
  component nested to the limits took up to about a minute, and now takes
  less than a second.
- The editor responds much faster on large and deeply nested templates.
  With a `<c-if>`/`<c-elif>` chain at each of 256 nesting levels, the work
  it redoes on each edit takes about 24 ms instead of about 3.6 seconds.
  On a template with 400 expressions in 200 sibling elements, it takes
  about 7 ms instead of about 1 second.
- With a shared cache such as Redis, a render no longer asks the cache
  about every component's JS and CSS and every served `Dependencies`
  file. Each process asks about each one at most once a minute, so if the
  cache drops a served file, it can take up to a minute to come back.
- Large templates parse much faster: a 92 KB template that took more than
  a second to parse now takes about 10 ms.
- Citry now reports a template error that covers many lines, such as an
  invalid expression spread over thousands of lines, in well under a
  second. A 20,000-line expression with an error took more than a minute to
  report.
- On standard CPython (built with the GIL), pages that repeat a
  `simple = "vue"` component render much faster on the server than with
  Citry 0.6.0. In Citry's board benchmark at 1,400 rows, the server
  takes about 62 ms to render the page instead of about 115 ms when the
  same page is requested again, close to twice as fast. On the first
  request it takes about 113 ms instead of about 166 ms, about 1.5 times
  as fast. The Rust renderer that does this work runs only on standard
  CPython; PyPy, Pyodide, and free-threaded CPython use the Python
  renderer.
- The browser now caches component scripts and stylesheets between page
  loads. A file whose URL holds a hash of its content is kept for a year,
  and other component files are checked with the server and downloaded
  again only after they change
  ([details](https://citry.dev/advanced/web-frameworks/#how-browsers-cache-files)).
- `serialize()` with `security_csp` or `security_javascript` set is much
  faster on large pages. On a page with 1,400 table rows,
  `serialize(security_csp="strict")` takes about 100 ms instead of about
  560 ms.
- In browsers such as Safari, an i18n message given an exact decimal with
  a long run of zeros before its last digit, such as 100,000 zeros, no
  longer holds up the page for seconds.
- When a page hydrates, the server now writes a Vue element's merged or
  array `:style`, and an object spread onto it with `v-bind`, in time
  proportional to the size of the value; before, the time grew with its
  square. A `:style` holding 40,000 declarations took several seconds and
  now takes tens of milliseconds. The HTML is the same as before: style
  text is split and keys are ordered by the same rules.

## v0.6.0

Citry 0.6.0 replaces Alpine with Vue. Most Python components, templates,
`c-*` attributes, slots, and Events handlers keep working, but browser code
moves to Vue and some Python code changes too, such as lint settings,
`js_data()` key names, and extension hooks.
[Upgrade to Citry 0.6.0](https://citry.dev/guides/upgrading-to-0-6-0/)
walks through every step.

### Highlights

- Write Vue directives, bindings, props, events, and slots in component
  templates, and Vue Options or Vue's Composition API (`Citry.vue`) in
  component JavaScript.
- Citry compiles each component to Vue on the server and sends one pinned
  Vue runtime only to the pages that need it, so you need no Node.js or
  frontend build step.
- Interactive pages send their content in the served HTML, so search
  engines and readers without JavaScript see it, and Vue takes over that
  HTML instead of building the page again.
- An Events handler can render one region of the page again: wrap it in
  `<c-mark name="cart-badge">` and return
  `actions.Render(CartBadge(count=n), target="mark:cart-badge")`, or target
  one rendered component with `render:<id>`.
- `citry check --types` type-checks component JavaScript and Vue
  expressions with TypeScript, Python template expressions with ty, and
  each `c-*` input against the child's `Kwargs`, reporting findings as the
  editor does; it needs `citry-lsp`, Node.js, and TypeScript's `tsc`.
- `simple = "vue"` gives a component its own Vue state and assets without a
  Python component instance.

### Upgrading from 0.5.x

- **Upgrade the packages together:** install `citry-ui` 0.3.0 and
  `citry-lsp` 0.2.0 with Citry 0.6.0, because older versions fail to start
  or lose their browser behavior
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#upgrade-the-packages-together)).
- **Alpine syntax becomes Vue:** rewrite `x-*` attributes, Alpine-only
  modifiers, `$dispatch`, and `$c-props` with their Vue forms; `citry check`
  lists the `x-*` attributes you missed
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#replace-alpine-directives-with-vue)).
- **Component tag attributes become Vue bindings:** `:name`, `v-*`, and
  `ref` on a component tag no longer reach the child as kwargs,
  `#c-ignore` works only on plain HTML elements, not on component tags or
  `<c-element>`, and Vue slot syntax such as `<template #title>` inside a
  component tag fails when the template loads; fill the slot with
  `<c-fill name="title">`
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#update-attributes-on-component-tags)).
- **Vue names from Python data stop the render:** a `c-bind` key, a `c-*`
  attribute such as `c-@click`, or an `on_attrs_resolved` hook that sets
  an attribute name starting with `v-`, `:`, `.`, `^`, `@`, or `#` now
  raises the new `citry.VueCodeError`, a `TypeError`, when the template
  renders, on every page. If a script you load yourself, such as Alpine,
  read these names on an HTML element, spread the long form, such as
  `x-on:click`
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#move-python-bindings)).
- **Component JavaScript moves to Vue Options:** the `$component` callback
  gets a smaller context, and `js_data()` keys that start with `$` or `_`
  must be renamed
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#move-component-initializers-to-vue-options)).
- **Events code:** render targets are `mark:<name>` or `render:<id>`
  instead of CSS selectors, custom transports must forward
  `request.headers`, and a `state` action you build, for
  `Citry.events.applyActions` or an `on_event_result` hook, needs a
  `publicState` object. `.enter` and `.escape` on a `@c-*` binding work
  only on `keydown`, `keyup`, or `keypress`, and on a `:c-*` binding only
  with `.on:keydown`, `.on:keyup`, or `.on:keypress`. A `:c-*` binding
  that names two `.on:` events, a binding with two key filters, and a
  second `@c-*` binding for the same event on one element now fail
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#update-events-code)).
- **Handlers that return a different component:** a handler can no longer
  replace the outermost component of a page or HTML fragment with a
  different component; move the part that changes into a child component
  or a `<c-mark>` region. Replacing any other calling component still
  works, and the old component's browser state is still lost
  ([docs](https://citry.dev/events/actions/#swap-in-a-different-component)).
- **Page scripts and selectors:** `Citry.alpine`, `Citry.manager`, and
  `Citry.i18n` are removed, and Vue-rendered elements carry no
  `data-cid-*` or `data-citry-key` attributes
  ([globals](https://citry.dev/guides/upgrading-to-0-6-0/#replace-removed-browser-globals),
  [selectors](https://citry.dev/guides/upgrading-to-0-6-0/#clean-up-integrations)).
- **Deployment and security:** several worker processes need a shared
  cache backend, and a proxy or CDN may need to pass Citry's CORS header
  through
  ([cache](https://citry.dev/guides/upgrading-to-0-6-0/#share-the-cache-between-worker-processes),
  [proxy](https://citry.dev/guides/upgrading-to-0-6-0/#proxies-and-cdns)).
- **Lint settings and diagnostic codes:** the Alpine names become Vue
  names, such as `rule_unknown_vue_variable` and
  `citry.vue.unknown-variable`, and `citry.csp.incompatible-browser-code`
  is removed: Vue expressions compile on the server and never need
  `unsafe-eval`
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#update-settings-and-extensions)).
- **Extensions and Python tools:** dependency scripts on interactive pages
  must be classic JavaScript, `OnSerializeContext` and
  `OnDependenciesContext` gain `selected_render`, `ctx.before_manifest`
  becomes `ctx.early_scripts`, `URLRoute` checks `methods`,
  `citry.analysis` results leave `self` out of `parameters`,
  `citry.analysis.lint_csp_compatibility` and `CspCompatibilityFinding` are
  removed, and the `TemplateNode` class is removed
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#update-settings-and-extensions)).
- **Subclasses name the parent class to add inputs:** a nested `Kwargs`,
  `Slots`, `State`, `TemplateData`, `JsData`, or `CssData` on a subclass
  now replaces the parent's class, like any nested Python class, so write
  `class Kwargs(Parent.Kwargs):` to keep the parent's fields. Citry warns
  with `NestedSchemaReplacedWarning` when a subclass leaves out a parent's
  fields. A replacing `State` also drops the parent's `_public`, `_model`,
  and `_max_age`, and Citry warns. A component whose parents declare
  different `Kwargs`, or that replaces a `State` with
  `_storage = "server"` without setting `_storage`, raises `ValueError`
  when defined. `Events`, `Dependencies`, and other settings
  classes still add to the parent's
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#name-the-parent-class)).
- **HTML returned from `on_render` shows as text:** `on_render()` now
  escapes a plain `str` it returns or yields, as `{{ }}` does, so user
  input in it cannot add a script. Wrap HTML in `Markup` or return a
  component. The extension hooks `on_component_rendered()` and
  `on_slot_rendered()` follow the same rule; wrap their HTML in `Markup`
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#wrap-html-returned-from-on-render)).
- **`Markup` in an attribute is escaped:** a `Markup` value in an HTML
  attribute is now escaped like any other value, so a `"` in it can no
  longer end the attribute and add another one. An entity such as
  `&amp;` still reads as its character
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#markup-attribute-values)).

### Other additions

- A component tag accepts `v-if`, `v-else-if`, `v-else`, `v-model`,
  `v-show`, and custom directives.
- `onServerRender({ component, revision, onEvent })` runs after mount and
  after each server render of the component, and it may be `async`.
- `Citry.vue.use(plugin)` installs a Vue plugin on every Vue app Citry
  creates.
- A text input, `<textarea>`, or `<select>` keeps what the user typed when
  its component renders again, until the server sends a different value.
- Interactive pages served through Citry's routes link their stylesheets
  and preload their scripts in `<head>`, so they are styled from the first paint, and browser assets
  are minified.
- Interactive fragments load their own assets, so HTMX pages no longer
  need the `citry-htmx.js` helper or `hx-ext="citry-fragments"`.
- `citry check` and the editor report misspelled component members, Vue
  bindings that read Python loop variables, undeclared emitted events,
  leftover `x-*` attributes, invalid HTML attribute values
  (`rule_invalid_attribute_value`), and `js_data()` values Citry cannot
  prove it can send as JSON.
- A translation catalog may leave messages out: `citry check` now warns,
  instead of failing, when a `tr()` call or a message in
  `I18n.client_messages` would show text from a fallback language. Set
  `LintSettings(rule_i18n_cross_language_fallback="error")` to require
  complete translations; a `<c-trans>` message still needs every
  translation.
- `citry check --types` checks `c-class`, `c-style`, and bound attributes
  such as `:style` against their expected types, which can report existing
  bindings such as `:aria-expanded="String(open)"`.
- Interactive pages start inside an iframe sandboxed without
  `allow-same-origin`, because Citry's asset routes send
  `Access-Control-Allow-Origin: *`.
- A Content Security Policy needs no nonce or hash for a page's app data,
  which the browser reads as JSON without running it, and
  `csp_script_hashes` lists only the scripts the browser runs.
- `Citry(vue_asset_max_bytes=...)` caps the memory a process without a
  configured cache spends on compiled component code (default 64 MiB).
- Render-cache entries saved by 0.5.x count as misses and are saved again,
  so you do not need to clear the cache.

### Fixes

- `parse_string_style()`, `normalize_style()`, and `merge_attrs()` no longer
  drop text that looks like a CSS comment inside a quoted value or after a
  backslash, such as `content: "/* note */"`, matching Vue.
- `class Kwargs(Parent.Kwargs):` on a subclass now keeps the parent's
  field defaults, and a nested data class such as `Kwargs` can list a
  required field after one with a default.
- `$state` and State bindings now show the State an Events handler changed
  when the handler returns nothing, returns data, or renders only a
  `<c-mark>` region, instead of keeping the old values until the component
  renders again.
- On Python 3.10, an i18n catalog package without `__init__.py` now loads
  instead of failing with a `TypeError`.
- Events handlers declared with `PUT`, `DELETE`, or another non-POST
  method now work, and each still rejects other methods and checks CSRF.
- `GET` Events calls reject arguments with unpaired surrogates instead of
  silently replacing characters.
- `citry check` no longer reports every template variable as undeclared
  when `template_data()`, `js_data()`, or `css_data()` runs several `if`
  checks before it returns.
- `citry check` no longer reports the keys of a `template_data()` written
  as a `@staticmethod` or `@classmethod` as undeclared, and checks the
  value types of a `js_data()` written that way.
- `citry check` no longer reports browser names such as `Document` or
  `btoa` as unknown in component JavaScript.
- `citry check` no longer reports `citry.js-data.unsupported-type` for a
  `js_data()` value that reads a `Kwargs` field annotated with a type
  alias of a `Literal`.
- In an app without i18n settings, `citry check` no longer reports
  "Unknown i18n format profile" for a formatter call in component
  JavaScript or one guarded by `self.i18n.configured`, matching the
  editor; an unguarded Python call is still reported.
- `citry check` no longer crashes with a traceback when a component's
  `messages` fail to compile, for example a selector variable that is not
  declared as a number with `@param`. It reports
  `citry.i18n.catalog-invalid` instead, and the JSON output gives the line
  and column inside the `messages` block.
- Fallback text that runs in the other direction, such as English on an
  Arabic page, no longer reorders the surrounding sentence when the
  browser translates it with `$i18n.tr()`, `$c-tr`, `i18n.bind()`, or
  `resolve()`. The browser now adds the same direction marks the server
  adds, and `resolve().direction` matches the server.

- `citry create` now rejects a name whose file would be a Python keyword,
  such as `citry create class`, instead of writing a module nobody can
  import.
- A Flask mount prefix written with a trailing slash, such as
  `prefix="/citry/"`, now serves Citry's routes instead of sending every
  Citry request to your app. A FastAPI or Flask prefix without a leading
  `/` raises Citry's `ValueError` without changing the app.
- Server-side State is now stored under `citry:state:` cache keys, so a
  State token can only refer to State that Citry stored. After the
  upgrade, events from a page opened earlier fail with a `stale_state`
  error until the page is reloaded.
- A component that declares `Dependencies` with an empty `css` list no
  longer makes a fragment raise `RuntimeError` when no web integration is
  mounted.
- An `on_render` or `on_component_rendered` hook that returns
  `str(result)` with extra HTML no longer writes the component's
  `data-cid-*` attribute twice on one tag.
- An extension hook that returns a value of the wrong type, such as an
  `on_component_rendered()` that returns a number, an `on_serialize()`
  that returns something other than a `str`, or an `on_event_result()`
  that returns something other than a list of actions, now raises a
  `TypeError` that names the hook and the extension, before the next
  extension runs. Before, the error blamed the next extension or appeared
  later without naming the extension, and `serialize()` returned whatever
  `on_serialize()` gave.
- An attribute that an `on_dependencies()` hook adds to a script or
  stylesheet in one render no longer appears in later renders of the same
  component.
- mypy and pyright now accept `self.events.url()`, and it is listed in
  the API reference.
- `enable_hot_reload(engine, mode="restart")` from `citry.contrib.django`
  now restarts the Django dev server when a component file changes.
- `enable_hot_reload` now notices component files under `Citry(dirs=...)`
  outside Django's template folders. Point `dirs` at your component
  folders, since the reloader checks every file under them.
- A component that keeps rendering itself, such as a tree node whose data
  lists the node among its own children, now fails quickly with a
  `RecursionError` naming the component instead of running until the
  process runs out of memory. Pass `Citry(max_component_depth=...)`
  (default 2000) if a page really nests deeper.
- An element with an empty `class` or `style`, such as
  `<p class c-class="name">` or `<p style="" c-style="styles">`, no
  longer raises `TypeError: Invalid class value: True` (or
  `Invalid style value: True`) when it also has a `c-class`, `c-style`,
  `c-bind`, or other `c-*` attribute. The empty attribute adds nothing to
  the value from Python. With no Python value, the element keeps the empty
  attribute.

## v0.5.1

_11 Sep 2026_

- **Values passed to `template_data()` are no longer `Const()`.**

    When you define a literal value in a template, Citry knows it's a literal
    and wraps it in `Const(...)` to optimize the template rendering:

    `<c-MyCard text="Hello">` -> `<c-MyCard c-text="Const('Hello')">`

    `Const()` is a [wrapt](https://github.com/GrahamDumpleton/wrapt) proxy - it
    copies the methods and behavior of the underlying
    value, so you rarely notice the difference.

    When such value is passed to a component, component's `template_data()`
    may receive `Const()` instead of the underlying value.

    We discovered critical problems:
    - `is` keyword does NOT respect the proxying.
    - Python's `pathlib` does NOT accept a string wrapped in a proxy.
    - and more...

    Because of this, values passed to `template_data()` are now always unwrapped.
    So that you don't have to deal with flaky behavior.

    The tradeoff is ~10% slower render time.

    Fixes ([#107](https://github.com/citry-dev/citry/issues/107)).

- The linter (`citry check`) now reports error for State bindings (`:c-*` HTML attributes) when:
   - Placed on unsupported elements and or `<input>` with unsupported type.
   - Unknown State key or unknown event handler is set.

- `citry check` validates `$component` callback data members against declared
  or inferred JavaScript data schemas
  ([#113](https://github.com/citry-dev/citry/issues/113)).

## v0.5.0

_9 Sep 2026_

### Added

- Define named component variants with `PreviewExtension`, customize variant
  and page layouts with templates or components, browse previews with
  `citry --app module:app ext run preview serve`, and capture PNGs with the
  extension's `render` command. Preview endpoints exist only in servers started
  by these commands.

- Components, including `LibraryComponent` definitions, can declare `simple = True` to render
  presentation templates without an independent instance or component hooks,
  keeping data callbacks live; incompatible declarations and calls raise errors.
  See the [simple component guide](https://citry.dev/performance/simple-components/).

- `RenderFrame` gains an `is_transparent_root` field defaulting to `False`,
  identifying a transparent component's whole output separately from caller-owned
  interiors. `RenderFrame.from_context()` and `CitryRender` accept the same keyword.

### Changed

- `simple` is a reserved, immutable boolean declaration on `Component` and
  `LibraryComponent`, including when set to `False`. Rename existing unrelated
  class attributes with this name.
- Direct `ElementAttrsNode.render()` calls can return plain `str` where they
  previously returned `Markup`. The `format_attrs()` helper still returns `Markup`.
- Persisted render-cache entries from earlier versions become cache misses and
  are regenerated when used after upgrading.
- Repeated component renders do less ownership bookkeeping, attribute
  normalization and text traversal. Core builds with native ownership storage
  further improve larger component trees. Renders without nested component calls
  avoid native storage setup.

### Fixed

- Dynamic HTML tags forwarded through constant component inputs render correctly
  from templates, including on repeated renders ([#107](https://github.com/citry-dev/citry/issues/107)).
- Components rendered through nested standalone templates, loops, and layout
  slots now initialize their JavaScript and `js_data()` state correctly.
- Transparent components with nested template blocks and slot fills emit one
  ownership boundary, allowing the browser to initialize their content.
- Deeply nested render fragments avoid Python's recursion limit during
  scheduling and serialization.

## v0.4.6

_30 Aug 2026_

### Fixed

- The published browser playground now loads the Citry Core 1.6.1 runtime
  required by Citry 0.4.5 and newer.
- The Django starter's Alpine-only help button no longer schedules an unrelated
  server refresh while the user starts searching.

## v0.4.5

_30 Aug 2026_

### Fixed

- `citry check` now validates server-handler names used by two-way `:c-*`
  State bindings as well as `@c-*` event bindings.

## v0.4.4

_26 Aug 2026_

### Added

- Inspect one registered component or alias with
  `citry --app module:engine inspect component --json`, retaining the versioned
  runtime catalog envelope.
- Inspect authored component dependencies and reverse references with
  `Citry.inspect_component_graph()`, including exact source locations,
  unresolved dynamic or unknown targets, partial-source problems, and
  deterministic versioned JSON.

### Fixed

- A component reintroduced by a fragment regains its class stylesheet after
  all earlier instances leave the page.
- Strict-CSP fragment stylesheets receive the loaded document's nonce.
- A fragment whose accepted CSS or JavaScript fails to load no longer replaces
  the live region or its ownership graph, and Citry removes styles introduced
  only by that failed transaction.

## v0.4.3

_22 Aug 2026_

### Added

- Template-engine adapters can declare provider-owned UTF-8 source spans,
  resolve them through owner-dispatched compile hooks, and render protected
  compiled bodies without using Citry's private render functions.
- `Citry.render_template()` renders standalone Citry source with variables,
  slots, globals, provides, source origins, and provider compile contexts
  through a bounded per-engine cache.

### Changed

- App-aware `citry check` treats extension-owned template ranges as unknown
  source and avoids unresolved-variable findings when a host range may
  introduce body bindings.
- Host-selected Citry segments remain structured until the enclosing render is
  serialized, preserving page-wide dependencies, ownership, events, and CSP
  processing.

## v0.4.2

_21 Aug 2026_

### Added

- Components that declare source messages can translate them without engine
  i18n settings, can name their message language with `I18n.messages_locale`,
  and can use another component's source key through the same engine catalog.
- Browser translations can bind reactive text, attributes, and custom
  destinations through checked `$c-tr` directives and `i18n.bind()` callbacks.

### Performance

- Repeated equal instances of a component declared with `pure = True` can now reuse its side-effect-free body work within one root render.
- Large component trees render faster by batching Alpine analysis in Rust,
  canonicalizing client graphs in Rust, caching stable ownership metadata, and
  avoiding transient attribute and ownership records.
- Repeated large-tree renders avoid redundant attribute-name validation,
  Events dispatch, replacement selection, and ownership-tree traversals.

### Changed

- Rendered ownership comments now use readable eight-character revision aliases while manifests and browser APIs retain complete graph revisions.

### Fixed

- Source-free i18n link units retain the masked punctuation needed to validate
  formatter calls when package catalogs are linked into an application.

## v0.4.1

_20 Aug 2026_

### Fixed

- Triple-quoted inline assets now keep ordinary quotes and use readable,
  host-relative multiline framing for formatted JavaScript and CSS.

## v0.4.0

_Beta release · 18 Aug 2026_

Citry v0.4.0 is the first beta release! 🎉

The Citry API is now mostly stable. There might be occasional bugs and minor API breakages.

### Added

- Configure CSP compatibility, JavaScript delivery, script integrity, and per-response nonces; strict mode ships an Alpine CSP runtime and rejects incompatible output.
- Build server and browser localization with Fluent catalogs, locale fallback, typed `tr()`/`fmt`, `<c-i18n>`, `<c-trans>`, `$i18n`, `$c-tr`, strict localized input, time-zone/DST handling, and coverage/extract/check/compile/inspect commands.
- Analyze Citry, Python, Alpine, JavaScript, CSS, and Fluent in editors through portable catalogs, source maps, diagnostics, completion, hover, and definition lookup.
- Run `citry check --static` or `citry --app module:attribute check` with stable finding codes and deterministic JSON output.
- Run `citry format` on Citry templates and conservatively discovered Python, JavaScript, and CSS assets, with check/diff modes and explicit Biome providers.
- Format definite inline component assets programmatically with `format_python_templates()`, `prepare_python_component_assets()`, `finish_python_component_assets()`, and `format_python_component_assets()`.
- Seed every component Alpine scope directly from `js_data()`; equal wire payloads still produce independent nested state per instance and refresh safely on rerender.
- Supply explicit root context with `render(provides=...)` and pass existing values unchanged with `provide(key, value)`.
- Configure shared and component-specific lint severity/types with `LintSettings` and `Component.Lint`.
- Use `citry.ext.i18n.make_context()`, `citry.Markup`, `citry.SecurityError`, and the typed public `Component.Events` contract.
- Inspect registry-complete component metadata with `Citry.template_analysis()`, portable catalog serialization, declaring-module provenance, and conservative asset ownership fingerprints.

### Changed

- Declared `TemplateData`, `JsData`, and `CssData` schemas now return their normalized defaults and coercions to templates and extensions.
- Inline `template`, `js`, and `css` declarations now remove shared Python indentation; file-backed assets remain byte-exact.
- Tag identity is now explicit: lowercase `c-`, case-insensitive component suffixes and HTML tag/attribute identity, but case-sensitive component inputs, slots, State fields, handlers, and custom events.
- Event modifiers follow dispatched-event capabilities: `.prevent` works for cancelable custom names and `.enter`/`.escape` filter any keyed event.
- `<select multiple>` State values are now `list[str]`, while custom-element State uses the element's typed `value` property in both directions.
- `:c-*` now accepts editable native controls or custom elements only; unsupported/unknown input types fail explicitly and recover safely after live type changes.
- Literal Events bindings are compiled from parser-proven attributes, so binding-shaped text in raw/comment/verbatim bodies stays literal.
- `<c-element>` validates State against its resolved HTML tag and attributes dynamic bindings to the lexical authoring component.
- `#c-key=None` now omits the key for that render; `False`, `0`, and `""` remain keys.
- Browser handler state is callable: `$error.message` becomes `$error()?.message`, with matching `error(name?)` and `loading(name?)` callback accessors.
- `actions.Data` always waits for its caller; `wait=False` now raises `ValueError` and the wire format omits `wait`.

### Fixed

- Component `#c-key` and `#c-ignore` now protect complete comment-delimited component ranges, including multi-root, rootless, transparent, keyed, and moved output.
- HTML `@c-*` bindings now receive non-bubbling native/custom events on their owning element with correct `.stop` and synchronous `$event.currentTarget`.
- Python 3.14 retains typed `TemplateData`/`Kwargs` source and C3-composed schema behavior.
- JavaScript/CSS formatting now handles final newlines, quote/escape variants, CRLF/lone-CR output, bounded streams, timeouts, and Windows cleanup without partial edits.
- Python comments inside `{{ ... }}` no longer consume apostrophes/braces or the host `}}` delimiter.
- `LibraryComponent` now exposes the complete public `Component` type surface in editors and static checkers.

## v0.3.1

_29 Jul 2026_

### Fix

- Event handlers now work when Citry is installed from PyPI. In 0.3.0 the
  browser runtime that Citry serves for `Events` was left out of the published
  package, so a page with an event handler loaded a script the server could not
  produce, and the call never reached Python. Upgrade to use `Events`; no code
  change is needed.
- `format_attrs()` now omits empty `class` and `style` values produced by
  `merge_attrs()`, matching hand-built structured values.
- `<c-error-fallback>` now escapes ordinary fallback strings. Use a fallback
  fill when the fallback needs markup.
- `$component()` is now recognized only as a live call expression. Matching
  text inside strings, comments, template-literal text, regular expressions,
  and function or method declarations no longer activates Citry's browser
  runtime or gets rewritten as a component callback.
- A configured extension instance can no longer be silently moved from one
  `Citry` engine to another. Pass the extension class or create a fresh
  instance for each engine. A failed engine construction restores the
  instance's previous owner.
- `citry create` now scaffolds both `Kwargs` and `Slots`, and relies on Citry's
  default template data instead of generating a redundant data method.

## v0.3.0

_28 Jul 2026_

### Breaking changes

- The built-in extensions package is now `citry.ext`: anything
  you imported from `citry.extensions.*` now lives at `citry.ext.*` (for
  example `from citry.ext.dependencies import Script`). The
  `Citry(extensions=[...])` setting is unchanged.
- The six JS/CSS dependency types (`Script`, `Style`,
  `CitryDependencies`, `Dependency`, `DependencyRecord`, and
  `OnDependenciesContext`) are now importable only from
  `citry.ext.dependencies`, so `from citry import Script` stops working. The
  one-line fix: `from citry.ext.dependencies import Script` (and likewise for
  the other five).

### New features and fixes

- Added a `Citry(mode="production" | "development")` setting (production by
  default) that selects the build environment. It is the single source of truth
  for developer-only output; today, in development the client ownership graph
  carries source provenance that production omits. An unrecognized `mode` value
  is rejected at construction.
- Fixed: a `@c-<event>` handler for a custom event whose name begins with
  `poll` (for example `@c-pollchange`) rendered fine on the server but made
  the browser reject the page's whole ownership manifest, so client behavior
  never activated. The browser now treats only the exact `@c-poll.<interval>`
  form as polling, matching the server.
- The `citry-client-graph/1` protocol package now ships a full golden-fixture
  corpus (valid and invalid manifests with a machine-readable index), and its
  reference validator rejects four manifest defects it previously accepted:
  component-tag client-binding payloads under the wrong binding key, nested
  component parent regions naming
  no region, one render id reused across graphs, and instance-ancestry
  cycles. Manifests the Citry server emits already satisfied these rules;
  they matter for hand-built or third-party manifests.

- Slot outlet data now arrives at fills as an immutable, slotted `SlotData`
  record. Identifier keys support attribute access while the mapping interface
  remains available for unusual keys and names that collide with mapping
  methods. `<c-fill data="...">` also supports one-level destructuring,
  `source as target` aliases, and a final `**rest` binding, with parse-time
  identifier, duplicate, ordering, and variable-shadowing validation.
  Parameterized `SlotInput[T]` declarations also validate explicit
  destructuring sources against `T`'s fields when the effective slot name and
  data binding are static, while dynamic or unresolved shapes retain the
  runtime missing-field check.
- Added first-class component-library publishing. Package authors can define
  inert `LibraryComponent` classes in an explicit `ComponentLibrary` manifest,
  and applications can install the package into each engine with
  `Citry.register_library()`. Imported definitions support direct template tags
  after registration and contextual Python composition through the exact
  per-Citry installation. Catalog classes and installation records publish and
  roll back atomically, repeated registration is idempotent, `clear()` retires
  old handles, required extension names are validated before class creation,
  and module-relative assets and component declaration inheritance are
  preserved during per-engine materialization. Ordered manifest inputs are
  enforced, failed installation removes loaded-file index entries, public
  publishing annotations resolve for introspection tools, and static checkers
  see the normal `Component` instance-authoring methods on inert definitions
  without treating those definitions as concrete `Component` classes.
- Nested component declarations now inherit automatically through the
  component class's C3 MRO. Child `Kwargs`, `Slots`, data-output schemas,
  extension config classes, Events, and State declarations add to their
  parents without explicitly naming the parent nested class; nearer fields,
  methods, and handlers win. Assigning the nested name to `None` resets that
  component-level inheritance, while a nearer declaration can reopen the
  chain. Dependencies keeps its branch-based merge while accepting reusable
  definition bases and preserving their module-relative asset provenance.
  Cross-branch schemas preserve a consistent frozen dataclass mode and reject
  incompatible adapter families, mixed frozen modes, NamedTuple branches, and
  multiple slotted dataclass layouts instead of silently losing fields.
  Concrete nested declarations are immutable after class creation,
  and extension `class_name` values must be valid, unique, and non-reserved.
  Extension class-created hooks can inspect the
  exact authored chain through `ctx.nested_declarations(name)`, whose
  `NestedClassDeclaration` records retain source classes even after Citry
  builds the effective runtime config.
- Added the runtime-checkable `ComponentLike` protocol for context-dependent
  Python composition. A third-party value can implement
  `__citry_element__(citry)` and render through `{{ ... }}`, slot content, or
  `Component.on_render` while preserving the active Citry instance,
  provide/inject scope, dependency collection, and component ownership.
  Resolution is single-step and rejects non-elements and elements associated
  with another Citry instance; there is no global fallback outside a render.
- Added `Component.unprovide(key)` for compound-component boundaries. The
  current component can still inject the inherited payload, descendants see
  the key as missing, and a nearer provider can establish a fresh value.
- Added rendered client context through `$component`'s `provide`, `inject`,
  and `unprovide` helpers plus Alpine's `$provide`, `$inject`, and
  `$unprovide` magics.
- Fixed dependency declarations and delivery at their edge cases:
  whitespace-only `Component.js`/`css` no longer creates fragment URLs that
  return 404, mixed-case inline closing tags are rejected safely, unhashable
  pre-rendered `__html__` entries de-duplicate and emit normally, and invalid
  `Dependencies.css` media values now identify the media key and component.
- Added opt-in output caching through per-component `Component.Cache` and the
  reserved, transparent `<c-cache>` fragment component, with
  typed effective-kwargs variation, custom `Cache.vary()`, strict Slot-source
  handling, TTL and version controls, detached subtree replay, and exact-key
  deletion. Hits keep current-call ownership and fresh descendant identities,
  notify observers only after ownership settles, and expose safe DEBUG
  diagnostics without retaining live render state. Fragment bodies preserve
  current Slot-writer ownership and replay dependency and Events payloads with
  fresh descendant identities. Active Debug highlighting conservatively
  bypasses render caching.
- Hardened render-cache replay and untrusted entries. A literal `<c-slot>`
  nested inside `<c-cache>` now preserves a caller fill through transitive Slot
  writers, including nested components. Stale CSS-variable payloads are
  rejected when the current component has only whitespace CSS, then rerendered
  and overwritten without leaking markers or repair writes. Artifact strings
  and object keys must be valid UTF-8, multibyte limits use encoded byte size,
  and deeply nested or malformed entries fail as controlled cache misses rather
  than serialization or recursion errors.
- Component class garbage collection now invokes no Citry lifecycle operation,
  registry mutation, cached-body eviction, or extension callback, preventing a
  finalizer from blocking on a lock held by the code it interrupted. Extensions
  perform deterministic cleanup for explicit component removal in
  `on_component_unregistered`, while weak indexes continue to discard collected
  classes automatically. `Citry.clear()` remains a bulk teardown and emits no
  per-component unregistration hooks. The unsafe GC-time
  `on_component_class_deleted` hook and its
  `OnComponentClassDeletedContext` have been removed; extensions must move
  cleanup to `on_component_unregistered`.
- Added exact render-cache key helpers at `citry.ext.cache`, with typed,
  bounded canonical variation encoding and explicit local or deployment-shared
  key scopes. Cache engine defaults now validate at `Citry` construction.
  First-party cache backends apply one strict TTL contract, the in-memory LRU
  is thread-safe, and Redis fractional TTLs round upward. Mutations from
  `on_component_input` now pass through final typed kwargs and Slots validation
  before component data methods run, with defaults and factories evaluated
  once.
- Citry instances and component class generations now expose stable
  process-lifetime identity tokens for exact same-process metadata joins. The
  new frozen component-introspection records provide validated schema, asset,
  extension, and canonical JSON value shapes for tooling integrations. Shared
  dataclass field discovery now follows constructor inputs by accepting
  `InitVar` fields and excluding `init=False` fields. You can query registered
  component definitions with `Citry.inspect_component()` and
  `Citry.inspect_components()`, including optional path resolution and portable
  schema defaults, without loading or compiling component assets. Runtime
  component identities are immutable even during class-created hooks, and
  dynamically generated class names now produce route-safe `class_id` values.
  Effective schema fields also expose conservative per-field authoring module,
  qualified class, and already-loaded source-file provenance, including the
  distinct declaration owners of C3-composed schemas.
- Component introspection now supports explicitly requested, versioned
  extension metadata. Extension authors can publish allowlisted JSON through
  `Extension.inspect_component()` using `ComponentIntrospectionContext`, with
  failures reported as `ComponentIntrospectionError`. The built-in Events
  projection exposes stable public handler, request-schema, return-type,
  docstring, and client-timing metadata without publishing executable or
  private configuration. The built-in Cache projection exposes effective
  component policy, normalized TTL, lossless tagged versions, variation mode,
  and declaration-level Slot-source possibility without running user code or
  exposing backend scope secrets.
- Added the built-in Events extension: typed server handlers, signed State,
  generated per-event and batch routes, protocol schemas, Alpine magics,
  declarative `@c-*` bindings and forms, queueing, transports, render actions,
  and keyed state-preserving morphs now form one end-to-end client/server
  contract. `State._public` controls client visibility and `State._model`
  controls client writability; a narrowed or empty `_model` now travels in the
  class descriptor so the browser rejects disallowed `$state` writes before
  mutating reactive State or queueing an update. Live descriptor refreshes
  update every instance of the class and discard newly forbidden pending or
  failed-call updates with a warning, while the server remains the authority
  on every call. A mirrored instance self-renders all of its placements while
  preserving each placement's local Alpine state. Concurrent non-blocking
  calls retain accurate busy state, polling and custom transports remain
  stable across runtime startup, and delayed binding flushes protect unsent
  drafts. Browser calls to GET handlers use pasteable per-event URLs, while
  pending two-way writes wait for the next mutating call.
- Events handlers can now return `actions.PushUrl(...)` or
  `actions.ReplaceUrl(...)` to update browser history without navigation, or
  return `actions.Download(...)` from a dedicated `@event(bundle=False)`
  handler to send a file with safe ASCII and UTF-8 filename headers. Download
  saves begin only after the call survives timeout and latest-wins checks.
  Unicode-only basenames now receive a usable `download` ASCII fallback while
  retaining their extension and exact UTF-8 filename.
  Raw `RouteResponse` handlers use the same per-event, unbundled contract and
  must leave State unchanged because their responses bypass the normal result
  envelope.
- Events transports now validate a complete response envelope before applying
  any batch result, including protocol, correlation, result count, shape, and
  epoch echoes. Malformed or mismatched custom-transport responses therefore
  cannot apply an earlier result before a later invalid slot is discovered.
  Server result hooks cannot emit actions outside the client's advertised
  capabilities, and a failing error observer retains the original controlled
  500 response. Compatibility responses also handle non-JSON values without
  leaking a host exception.
- Events data validation now accepts parameterized `Mapping` fields as object
  shapes. Component introspection also excludes the exact deferred
  `typing.ClassVar` spelling from published request fields, and a subclass can
  use any `ClassVar` form to remove an inherited input field.
- `citry inspect --json` now emits the selected engine's compact, versioned
  runtime component catalog for local scripts and CI. It completes normal
  discovery, uses the introspection API defaults, and deliberately has no
  static-analysis fallback. `citry list` now projects the same catalog while
  retaining its merged names, class, path, and built-in rows; catalog ordering
  makes rows and extra manual aliases deterministic.
- Component-catalog `FieldInfo` records now carry optional per-field source
  module, qualified class name, and already-loaded absolute module path. The
  provenance identifies the authored declaration across inherited and
  C3-composed schemas, while generated or otherwise unprovable fields leave it
  absent for conservative editor navigation.
- Client-active pages now share one Citry-owned Alpine instance, including
  pages whose components use Alpine or Component.js without declaring Events.
  `Citry.alpine.beforeStart(callback)` is the supported pre-start extension
  point for Alpine plugins, magics, directives, and data providers. Component
  callbacks also receive a validated `graph` route with distinct render,
  logical-instance, and stable-browser-anchor identities. Duplicate Citry or
  foreign Alpine bundles are diagnosed while the original Citry runtime keeps
  its single startup and permanent hooks.
- Fragment component callbacks now wait for their stylesheets to load, share
  concurrent CSS requests, retry failed loads, and reload a class stylesheet
  after its last-instance cleanup collected the previous link.
- `$c-props` now raises during rendering when its final resolved target has no
  `$component(...)` registration, instead of shipping an ownership manifest
  for a browser no-op. The check follows runtime `<c-component>` selectors to
  the actual target and also rejects stale detached cache replays before
  extension staging; a final `None` or `False` still removes the binding.
- Client component boundaries now support declared reactive `$c-props`,
  parent-scoped Alpine and `@c-*` handlers, exact call-site scope for supplied
  slot content, receiver scope for fallback content, multi-root listener
  groups, and rootless lifecycle ownership. Client-active deployment must
  preserve Citry's ownership manifest, `citry:g1` ownership comments, and `data-cid-*` /
  `data-citry-*` markers through minification and DOM updates.
- Built-in render IDs now use a `c` prefix followed by eight lowercase
  base-36 characters. Custom
  `id_generator` values must contain only lowercase ASCII letters, digits,
  hyphens, and underscores. This prevents distinct mixed-case IDs from
  collapsing onto one `data-cid-*` marker because HTML attribute names are
  case-insensitive; graph and Events consumers reject unsafe wire values too.
- Component autodiscovery no longer crashes when editor or OS junk files sit
  inside a scanned directory. Files and directories with a dot in their name
  (an `.#card.py` editor lock file, a macOS `._card.py` copy, a `.cache/`
  tree, a `card.old.py` backup) are now skipped during the scan, the same way
  underscore-prefixed paths already were, and a dotted directory name hides
  its whole subtree.
- Added the opt-in `citry.ext.debug.Debug` extension for development-time
  component and slot highlighting. It draws labeled blue component boundaries
  and red slot boundaries, configured globally through
  `extensions_defaults["debug"]` or per component with a nested `Debug` class.
  Authored roots keep their Citry markers, transparent components and full
  documents are not wrapped, and embedded renders remain safe when their root
  engine does not install Debug. The wrappers are real DOM elements and are
  intended for inspection, not production or layout-sensitive tests.
- Unregistering a component's final name now releases its cached render body,
  and render-cache keys hold component classes weakly. Fully rendered classes
  can therefore be garbage-collected after plugin unload or hot replacement,
  and their weak file-index entries disappear with them. Replacing a class
  with the same module and name also refreshes its class-level JavaScript and
  CSS instead of serving the retired class's cached assets. Generated class
  asset URLs are content-addressed, so retained old classes and overlapping
  workers cannot overwrite the cached version named by a page. Mixing
  fragments from different deployed versions in one live page remains
  unsupported; use worker draining, version-sticky routing, or a full reload.
- Servers can now call `app.initialize()` before starting request workers to
  complete configured component discovery, built-in registration, and
  parse-time tag-rule construction at a known startup point. Concurrent first
  use or component mutation now raises `CitryLifecycleInProgress` promptly
  instead of exposing partial state; failed initialization remains retryable.
- Failed built-in initialization and component autodiscovery no longer leave an
  engine marked ready with empty or partial component state. Citry rolls back the
  failing registration work and retries on a later lookup. Recursive discovery
  now raises clearly, built-in names remain protected during extension hooks,
  and engine-level mutations keep hooks, class-ID lookup, caches, and discovery
  state synchronized.
- Component classes now have one immutable `Citry` owner. `app.register()`
  supports aliases and re-registration only for classes owned by `app`, and a
  concrete component subclass uses the same owner as its concrete component
  bases. Reusable modules can expose `register_components(app)` to define a
  fresh component tree bound to that Citry instance during startup. Component registration,
  lookup, initialization, and clearing are public through `Citry`; the
  standalone `ComponentRegistry` API and `app.registry` attribute have been
  removed.
- Added `Citry.atomic_registration()` for publishing an additive group of
  component classes as one Citry-owned registry change. An exception restores
  names, class-ID lookup, tag rules, and discovery state without compensating
  unregistration hooks; unrelated extension and Python side effects remain
  outside that rollback.
- Inherited `template_file`, `js_file`, and `css_file` declarations now stay
  anchored beside the class that declared them, so subclasses in another
  module load the correct files. Absolute `PathLike` entries in
  `Dependencies.css` and `Dependencies.js` are treated as local files and
  inlined instead of becoming root-relative URLs. A component whose template
  declares a slot outside its closed `Slots` schema now raises on every render,
  rather than only on the first compilation attempt.
- A tag now accepts one explicit spelling per logical attribute: `x` together
  with `c-x` is a parse error, including typed kwargs, dynamic tag names,
  slot/fill fields, and component-tag client bindings such as `$c-props`,
  `@click`, and `@c-poll.5s` on a nested `<c-*>` tag. Plain-element
  `class`/`c-class` and
  `style`/`c-style` remain accumulating exceptions. `c-bind` can interlace with
  one explicit spelling and repeats in source order because a spread key is
  known only at render time. A slot/fill `c-bind` value of `None` contributes
  nothing, and dynamic duplicate fill names are checked after resolution.
  Bare, empty, and whitespace-only static `is` values on
  `<c-component>` and `<c-element>` are now parse errors, while dynamically
  resolved empty targets retain their runtime errors.
- Mixed static `is="..."` and `c-bind="..."` now stays on the dynamic path for
  `<c-component>` and `<c-element>`, so the rightmost source-order contribution
  selects the real target and void-element validation applies to that winner.
  Dynamic elements also merge every `class` and `style` contribution like a
  statically written element. Runtime-produced HTML attribute names are now
  checked before formatting, so non-string or malformed spread keys raise a
  targeted error instead of emitting broken markup. Component and dynamic tag
  names ending in a newline are rejected too.
- Structural tags now reject attributes they cannot consume: `c-bind` directly
  on `<c-if>`, `<c-elif>`, `<c-else>`, `<c-for>`, `<c-empty>`, or `<c-raw>` is a
  parse error (the same spread remains valid on an element/component carrying a
  control-flow shortcut), and special `c-bind`, `c-is`, `c-name`, and
  `c-required` inputs reject nested-template values when their tag contract
  requires an expression.
- Slot metadata now follows authored source order around one explicit name or
  requiredness provider and any `c-bind` contributions; fill `data`/`fallback`
  variable metadata stays
  conservative after a spread. Bare, empty, and whitespace-only static
  slot/fill names fail at parse time, and template comments surrounded by any
  amount of formatting whitespace no longer create or satisfy an implicit
  default fill. Static slots inside template-valued attributes now propagate to
  the writer component's metadata and closed `Slots` validation.
- Template-valued `c-*` attributes can now render `<>...</>` fragments. The
  grouping delimiters are removed before the nested template is compiled, so
  text, expressions, multiple roots, and nested components render instead of
  raising a parse error. The delimiters must wrap the entire non-whitespace
  value and cannot be mixed with sibling roots. Adjacent real-tag roots need no
  fragment; their boundary detection now follows the grammar's tag-name rules
  and recognizes a final HTML void element instead of relying on a narrower
  hard-coded closing-tag alphabet or a raw `/>` suffix.
- Control-flow shortcut attributes are now validated with the same semantics
  as their explicit tag forms: `c-if`/`c-elif` require expression values,
  `c-for` requires a loop clause, `c-else`/`c-empty` reject values, and orphaned
  or out-of-order shortcut branches are parse errors instead of being lowered
  into invalid runtime nodes.
- Loop and fill no-shadow validation is now lexical and scope-aware. Using a
  newly bound name in its own body is valid, while self-reading loop targets,
  duplicate targets, nested reuse, and collisions with the actual render
  context fail before the binding is applied. Const body caches partition on
  the visible-name set, and const-unrolled loops retain a live binding guard.
- Errors inside nested template-valued attributes now report positions and
  source lines from the complete outer template. Recursive nesting no longer
  double-counts offsets, Unicode prefixes use character columns, and malformed
  nested tags raise `SyntaxError` instead of escaping as a Rust panic.
- Component JavaScript registration is now `$component(...)`; update existing
  `$onComponent(...)` calls when upgrading. The config-object form now uses
  `init` for its callback instead of `handler`. Each component class accepts
  one registration, and a second definition throws an error naming the class.
- Constructing `CitrySettings(...)` directly now applies the same normalization
  and validation as `Citry(...)`: directory entries become absolute `Path`s (a
  relative one raises `ValueError`), and the extension/resolver/codec sequences
  and the `extensions_defaults`/`template_globals` mappings are copied into the
  frozen settings, so editing the values you passed in afterwards can no longer
  change them. Before, only `Citry(...)` applied these.
- Route handlers now receive a framework-neutral request and can set response
  headers. Under every web adapter (ASGI/FastAPI, WSGI/Flask, Django) a
  handler's first argument is a `citry.RouteRequest` with `method`, `path`,
  `query` (repeated keys preserved), case-insensitive `headers`, the raw
  `body` bytes, `content_type`, and `native` (the untouched host request
  object), so the same handler can read a POST body under any framework; a
  handler that ignored its `request` argument keeps working unchanged.
  `citry.RouteResponse` gains a `headers` field of `(name, value)` pairs that
  every adapter forwards to the client (under Django a repeated header name
  raises a pointed error instead, since Django's response object holds one
  value per name). Under the ASGI adapter a handler can
  now be `async def` (it is awaited), and plain handlers run in a worker
  thread so a slow one no longer blocks the event loop; the synchronous WSGI
  and Django adapters reject an `async def` handler with a `TypeError` that
  points at the ASGI adapter as the fix.
- You can now hot-reload component files during development: edit a component's
  `template_file`, `js_file`, or `css_file` and the next render shows the new
  content without restarting the process. Run `citry watch` to watch your
  component directories (or `citry watch --path some/dir`), and install a fast
  native watcher with `pip install citry[watcher-watchfiles]` (or
  `citry[watcher-watchdog]`); a dependency-free polling fallback is built in, so
  `citry watch` works without either. On Django, call
  `citry.contrib.django.enable_hot_reload(citry_instance)` from your
  `AppConfig.ready()` to drive the reloads off Django's own autoreloader; on
  FastAPI or Starlette, pass `citry.contrib.asgi.reload_lifespan(citry_instance)`
  as the app's `lifespan` so the watcher starts and stops with the app. Under the
  hood `citry_instance.invalidate_file(path)` drops the cached template/JS/CSS
  for every component that loaded that file and returns those components (and
  `invalidate_all()` resets every loaded component when a change cannot be pinned
  to one file), so you can call them directly to wire up any other watcher.
  Watcher callbacks receive resolved, de-duplicated paths even when a backend
  reports multiple aliases for the same file.
- You can now define template variables once and have them available in every
  component, instead of returning the same value from every `template_data()`.
  Set them when you build the engine with `Citry(template_globals={...})`, or
  change them on a live instance through `citry.template_globals`, which is a
  plain dict (`citry.template_globals["site_name"] = "Acme"`, `.update(...)`,
  `del citry.template_globals["site_name"]`). The default `citry` instance can
  be configured this way too, after import. You can also set globals for a single
  render with `element.render(template_globals={...})`, layered on top of the
  instance's globals for that render only and reaching every component in it,
  which suits per-request values like the current user without touching the
  shared engine. A component's own `template_data` wins when it returns a key of
  the same name, so globals act as defaults, and a global never has to appear in
  a component's declared `TemplateData`.
- You can now read a component's inputs directly in its template without
  writing `template_data`: by default `template_data` returns the component's
  `kwargs`, so a `Kwargs` field named `title` is available as `{{ title }}`
  with no boilerplate. Returning your own dict from `template_data` still
  overrides the default, and a declared `TemplateData` still validates the
  result. One consequence: a template now resolves an input name ahead of a
  same-named `template_globals` entry, so an input shadows a global of the same
  name (your component's own data wins over globals, the documented
  precedence).
- You can now use the `citry` command line, installed with the package. Scaffold
  a component with `citry create MyButton`, list the components an engine has
  registered with `citry list` (one row per component, with all its registered
  names and the file that defines it, when it has one), and list
  or run the commands your extensions
  provide with `citry ext list` and `citry ext run <extension> <command>`. Point
  any command at a specific engine you built with `citry --app module:attribute
  ...`; the target resolves against your working directory the way ASGI/WSGI
  servers resolve theirs, so `citry --app app:engine list` works from a plain
  project root. Check the version with `citry --version`. An extension declares its
  own commands by listing `ExtensionCommand` subclasses (with argparse-style
  `CommandArg` arguments) in `Extension.commands`; the commands your extensions
  provide then show up under `citry ext list` and `citry ext run`.
- You can now control the per-render component id with `Citry(id_generator=...)`.
  Pass a function (or a `"path.to.func"` import string, or a class that builds
  one) returning the id stamped on each component as it renders, which is handy
  for stable ids in snapshot tests. It must return ids that are unique among the
  components on one page. This does not affect a component's `class_id`.
- You can now have citry import your component modules for you. Point it at your
  component directories with `Citry(dirs=["/path/to/components"])` and the
  modules under them are imported the first time you render a page, so their
  components register themselves without you importing each file by hand. It is
  on by default and does nothing until you set `dirs` (so existing setups are
  unaffected); turn it off with `Citry(autodiscover=False)`, or run it yourself
  with `citry_instance.autodiscover()`. The directories must be importable (on
  your `PYTHONPATH`); a directory that holds components but is not importable
  raises an error that says exactly that.
- `<c-raw>` now works. A `<c-raw>...</c-raw>` block renders its contents
  verbatim, with no template processing inside, so `{{ ... }}`, `{# ... #}`,
  and nested `<c-*>` tags are emitted literally (handy for showing template
  syntax or embedding code samples). It previously failed at render time with
  `No component registered as 'raw'`.
- You can now turn off the expression sandbox with
  `Citry(sandbox_expressions=False)`. Template expressions (`{{ ... }}` and
  dynamic `c-*` attributes) then run as plain Python, which is faster, but the
  checks that block dangerous operations are gone - so only do this when you
  trust every template you render. The sandbox stays on by default, and turning
  it off does not change the output of a successful render.
- Pages built from many components that share a constant value (a theme, a
  layout config) render faster. When a component input is computed entirely from
  constant values - like `<c-Tab c-class="base + '-active'" />` where `base` is
  constant - Citry now treats the result as constant too, so the child component
  can reuse the work it already did for that input, the same as it does for a
  plain literal like `c-class="'tab-active'"`. Inputs that depend on per-render
  data are unaffected.
- Rendering is faster, most noticeably on deeply nested pages: gathering a
  page's JS/CSS dependencies grew with the component tree's depth (work
  repeated at every level) and is now flat, so a large nested page's repeat
  render is several times quicker. Repeat renders are leaner across the board
  too: attribute formatting, HTML escaping, per-component id generation, and
  component construction each do less work per render.
- Flask and Django join FastAPI as supported hosts for citry's endpoints:
  `citry.contrib.flask.mount(app, citry_instance)` and
  `citry.contrib.django.urlpatterns(citry_instance, prefix=...)` (for
  `include()`-ing in your `urls.py`).
- More cache backends: `citry.contrib.caches.RedisCache` and `DiskCache`
  wrap a `redis.Redis` / `diskcache.Cache` you construct, and
  `citry.contrib.django.DjangoCache` reuses any cache your Django project
  already configured. All plug into `Citry(cache=...)`.
- Local-file `Dependencies` entries can now be served instead of inlined:
  set `local_files = "serve"` on a component's `Dependencies` class (or
  globally via `extensions_defaults={"dependencies": {"local_files":
  "serve"}}`) and the file is emitted as a fingerprinted URL
  (`asset/<content hash>.<ext>`), so browsers cache it and fragments
  de-duplicate it. Falls back to inlining when no web integration is
  mounted.
- `URLRoute` and `RouteResponse` are exported from the `citry` package, for
  extensions that declare their own HTTP endpoints (`Extension.urls`).
- HTML fragments now work end to end:
  `serialize(deps_strategy="fragment")` renders a partial for HTMX-style
  swaps (or any `fetch` + `innerHTML` insertion). Nothing is inlined; the
  fragment ends with a JSON manifest of URLs the client-side manager
  fetches, so a component used by many fragments is downloaded once per
  page, and a fragment landing on a page that lacks the manager loads it
  itself.
- You can now mount citry's endpoints (cached component JS/CSS, the client
  runtime) into your web app: `citry.contrib.fastapi.mount(app,
  citry_instance)` for FastAPI/Starlette, or the dependency-free
  `citry.contrib.asgi` / `citry.contrib.wsgi` sub-apps for everything else.
  On a mounted app, `"document"` pages serve the runtime by URL
  (browser-cacheable) and tell the manager which scripts the page already
  has, so later fragments refetch nothing.
- Extensions can now serve HTTP endpoints: declare framework-neutral routes
  on `Extension.urls` (they mount under `ext/<extension name>/`), reachable
  through the same adapters. Every extension instance also carries
  `self.citry` now, the back-reference to its engine instance.
- Multi-worker note: fragments reference per-render variables scripts by
  URL, and the worker serving the URL may not be the one that rendered the
  page, so production setups using fragments with `js_data()`/`css_data()`
  should configure a shared cache backend (`Citry(cache=...)`).
- Per-render data now reaches the browser. In your component's JS, register a
  callback with `$component(({ id, els, data }) => { ... })`: it runs once
  per rendered instance, with the instance's root elements and its
  `js_data()` result. Identical data is sent to the browser once, however
  many instances share it, and values are transported so they can never
  break out of the script tag.
- `css_data()` results become CSS custom properties scoped to the instance:
  the component's CSS reads them with `var(--name)`, backed by a generated
  stylesheet and a `data-ccss-<hash>` marker on the instance's root
  elements. Pure CSS: this works even with the `"simple"` strategy.
- Pages rendered with the `"document"` strategy include citry's client-side
  dependency manager (`globalThis.Citry.manager`) and a JSON page manifest,
  but only when some component actually registered a callback; other pages
  carry no extra JavaScript. The `"simple"` strategy never includes the
  runtime, so per-instance JS does not run there.
- Components' JS and CSS now reach the rendered page: every rendered
  component's `Component.js`/`css` and `Dependencies` entries are collected
  and placed into the final HTML at serialize time. CSS goes before the first
  `</head>`, JS before the last `</body>`; on a page with neither, CSS is
  prepended and JS appended. Inline component JS is wrapped in a
  self-executing function; duplicate dependencies (same URL or same content)
  are emitted once, however many components share them.
- New `<c-js />` and `<c-css />` built-in tags mark exactly where the
  collected scripts and stylesheets go. When the same tag appears more than
  once, the first one (in document order) receives the tags.
- `serialize()` (and `str()` on a render) takes `deps_strategy`
  (`"document"`, `"simple"`, `"ignore"`; `"fragment"` is reserved for the
  upcoming client-side manager) and `deps_position` (`"smart"`, `"prepend"`,
  `"append"`).
- `Dependencies` entries are emitted by type: URLs become
  `<script src>`/`<link href>` tags, local files are inlined, `Script`/`Style`
  objects control the exact tag, pre-rendered tags pass through verbatim. The
  CSS media type (`css = {"print": ...}`) becomes the tag's `media`
  attribute. `get_dependencies()` now returns local files as absolute `Path`
  objects (URLs stay strings).
- Two new hooks adjust the emitted tags: `Component.on_dependencies(scripts,
  styles)` (classmethod, this component's own entries) and an extension-level
  `on_dependencies` (the page-wide lists, after de-duplication).
- New extension hooks `on_render_context_merge` (a nested render's collected state
  merges into its parent; extensions own their slice) and `on_serialize`
  (rewrite the final HTML at the end of `serialize()`).
- You can now plug in a cache backend: `Citry(cache=...)` takes any object
  with `get`/`set`/`delete`/`has` (see `citry.CitryCache`), or a
  `"path.to.Cache"` import string. The default is a per-instance in-memory
  cache (`citry.InMemoryCache`). Citry stores derived content there, starting
  with the processed JS/CSS scripts of the dependency-rendering work.
- New `Component.js_data()` and `css_data()` methods (mirroring
  `template_data()`), with optional typed `JsData` / `CssData` schema classes:
  return per-render variables for the component's JS and CSS. The
  `on_component_data` extension hook now carries `js_data` and `css_data`
  alongside `template_data`. Delivery into the rendered page lands with the
  dependency-rendering emission phase.
- New `Script` and `Style` objects (importable from
  `citry.ext.dependencies`): declare a `<script>` / `<style>` /
  `<link rel="stylesheet">` dependency with exact control over the emitted
  tag, and use them directly as entries in a component's `Dependencies` class.
- Every component class now has a stable `class_id` (e.g. `Table_a1b2c3`),
  deterministic across processes; look classes up with
  `Citry.get_component_by_class_id()`.
- The `<c-component>` built-in tag now works: it renders the component named
  by `is` in its place (`<c-component c-is="comp" />`, where the value is a
  registered name or a `Component` class). All other attributes and the body
  (fills included) pass through to the target. A static `is="MyComp"` is
  resolved at compile time and costs nothing at render.
- New `<c-element>` built-in tag: renders a plain HTML element whose tag name
  is decided at render time (`<c-element c-is="heading_tag">...</c-element>`).
  Any tag name works, custom web components included; void elements (`br`,
  `img`, ...) reject children. A static `is="div"` compiles to the literal
  element. Misspelled *component* names still fail loudly: `<c-component>`
  never falls back to rendering an element.
- The names `component` and `element` are now reserved in the component
  registry for the built-in tags; registering a component under them (e.g. a
  class named `Element`) raises `AlreadyRegistered`.
- `citry_core.template_parser` now exports `HTML_VOID_ELEMENTS`, the HTML
  void-element names, single-sourced from the Rust parser.
- Dynamic attributes on plain HTML elements now work as documented:
  - `c-bind` spreads a dict onto the element (it previously rendered the dict
    as text).
  - A `True` value renders the bare attribute, `False` and `None` omit it
    (previously `disabled="True"` / `disabled="False"`).
  - `class` and `style` accept structured values (string, dict, nested
    lists, like Vue), and when one element gets them from several sources
    the values merge instead of overwriting.
- A tag rejects the static and dynamic form of the same logical attribute
  (`id="form"` together with `c-id="..."`). Plain-element `class`/`c-class`
  and `style`/`c-style` are the accumulating exceptions; conditional
  overrides belong in `c-bind`.
- A dynamic attribute with no value (`<div c-foo>`, `<div c-foo="">`) is now
  a parse error: there is nothing to evaluate, and it almost always means
  you wanted the static `foo` or forgot the value. The control-flow
  shorthands `c-else` and `c-empty` still take no value.
- New helpers for building attribute dicts in Python: `merge_attrs`,
  `format_attrs`, `normalize_class`, `normalize_style`, `parse_string_style`
  (importable from `citry`).
- New extension hook `on_attrs_resolved`: rewrite an element's resolved
  attribute dict before it is rendered (e.g. class deduplication).
- Render errors now tell you where they happened. The error message starts
  with the component path from the root down to the failure ("An error
  occurred while rendering components MyPage > Card > Card(slot:body)"), and
  when the failure sits in a template, it also shows the failing template
  lines with line numbers and a `^^^` underline.
- An extension can now recover from a component's render error: when a
  component fails, each enclosing component's `on_component_rendered` hook
  is called with the error on the way up, and returning replacement output
  swallows the error in that component's place. Untouched parts of the page
  still render; an error no extension handles raises as before.
- New `Component.on_render()` hook: return content to use it as the
  component's whole output instead of its template (a string, a composed
  element like `OtherComp(...)`, an already-rendered `CitryRender`, or a
  `Slot`), or return `None` (the default) to render the template as usual.
  The accepted values are published as the `RenderReplacement` type alias
  (importable from `citry`).
- `on_render()` also has a generator form: include a `yield` to receive the
  component's finished output (children included) as `(result, error)` and
  react to it. Return new content to replace the output, raise to replace
  the error, or return nothing to keep the result; if a child component
  failed, `error` is set and returning content swallows it (this is how
  error boundaries are built). You can yield replacement content any number
  of times; each yield receives the settled result of the previous one. The
  generator shape is published as `OnRenderGenerator` (importable from
  `citry`).
- New `<c-error-fallback>` built-in tag: an error boundary. Wrap content
  that might fail to render, and on error the fallback shows in its place
  while the rest of the page renders normally. Give the fallback as the
  `fallback` attribute, or as a `fallback` fill that receives the error as
  slot data (`<c-fill name="fallback" data="d">{{ d["error"] }}</c-fill>`).
  Boundaries nest (the innermost one wins), and a failing fallback defers
  to the next boundary up. The name `error-fallback` is now reserved in the
  component registry.
- New `Component.ancestors` property: iterate a component's ancestors during
  render, nearest first up to and including the root (e.g.
  `any(isinstance(c, Theme) for c in self.ancestors)`). Like `parent`, the
  chain follows who wrote the component: content passed into another
  component's slot keeps its author's chain (unlike Vue's `$parent`, which
  points at the slot host). For "am I rendered inside X, slots included",
  use `provide`/`inject`.
- `citry_core.safe_eval` now exports `format_error_with_context`, the
  formatter that adds an underlined source snippet to an error message
  (previously internal to `safe_eval`).
- Your component's `$component` callback can now return a cleanup function.
  The client runtime calls it right before the callback fires again for the
  same component instance (for example when the same fragment HTML is
  inserted into the page again), and now also when the instance's last element
  leaves the page, so event listeners, timers, and widgets set up in the
  callback are torn down both before they are re-created and when the component
  is removed rather than re-rendered. A callback that synchronously registers
  or calls another component while it runs no longer makes its own callback and
  cleanup run twice.

## v0.2.0

### Feat

- Citry now logs through the standard `logging` module, under the `"citry"`
  logger, with a `TRACE` level (5, below `DEBUG`). The logger traces each component,
  slot, and node as it renders. Turn it on to debug a render:

  ```python
  import logging
  logging.getLogger("citry").setLevel(5)
  ```

### Fix

- A default value for a slot set at `Component.Slot.<attr>` is now correctly used.

- Include JS runtime script when a Component has any JS/CSS scripts

### Refactor

- Citry now raises error when template contains `<c-slot name="X">`, but `Component.Slots` omits `X`.

  A component without a `Slots` class accepts any fills
  and is unaffected.

## v0.1.0

_30 Jun 2026_

Initial release.

## 2025-12-21

Initial commit.

This project was forked from [django-components/djc-core](https://github.com/django-components/djc-core) at commit [49e20dc](https://github.com/django-components/djc-core/commit/49e20dc).
