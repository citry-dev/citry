---
title: v0.7.0
url: https://citry.dev/v/0.7.0/releases/v0.7.0/
description: "What changed in citry v0.7.0."
---
# v0.7.0

Citry 0.7.0 catches more mistakes. A component input of the wrong type
now raises `TypeError` when the component renders, and `citry check` and
the editor report many HTML, Vue, and Events mistakes they used to miss.
Pages that repeat a `simple = "vue"` component render much faster on
standard CPython. Vue scoped slots and listener modifiers such as
`.outside` now work in templates. Citry supports Python 3.15 and needs
3.11 or newer.

## Upgrading from 0.6.x

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

## Added

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

## Changed

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

## Fixes

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

## Performance

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