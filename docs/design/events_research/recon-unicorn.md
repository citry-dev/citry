# Recon: django-unicorn (for citry Component.Events design)

Date: 2026-07-04. Sources: django-commons/django-unicorn GitHub repo (main branch, verified via GitHub API on 2026-07-04), its `docs/source/*.md`, PyPI/CVE databases, HN (Algolia API), and Adam Hill's maintainer post. All `src/django_unicorn/...` and `docs/source/...` citations are upstream repo paths; line numbers are from main as of 2026-07-04. Local mirrors of every cited file are in `/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/unicorn-src/` (path separators replaced with `_`) and `.../unicorn-docs/`.

Note on the given output path: the orchestrator passed `undefined/recon-unicorn.md` (unresolved template variable), so this report lives at the scratchpad path above.

---

## 1. Programming model

A "component" is a Python class plus a Django template. The class inherits from `UnicornView` (which itself derives from Django's `TemplateView`, per `docs/source/faq.md:5`). Naming is convention-driven: component name `hello-world` maps to file `hello_world.py`, class `HelloWorldView`, template `hello-world.html` (`docs/source/views.md:5`). Components are placed with a template tag, and the page must carry a CSRF token:

```html
{% load unicorn %}
{% csrf_token %}
{% unicorn 'hello-world' "Hello" name="World" key='first' %}
```

Args/kwargs land in `self.component_args` / `self.component_kwargs`, readable in `mount()` (`docs/source/components.md:76-98`). `key` disambiguates multiple instances of the same component (`components.md:134-160`).

**State** is plain class attributes. Everything public is serialized to JSON and becomes both template context and browser-visible state. Supported types: str, int, Decimal, float, list, dict, Django Model, QuerySet, dataclass, Pydantic models, and custom classes via a `to_json()` method or the `UnicornField` helper (`docs/source/views.md:21-34, 91-111`). Mutable class-attribute defaults are a documented footgun (shared across instances); the docs tell you to initialize them in `mount()` (`views.md:36-71`).

**Data binding**: `unicorn:model="name"` (alias `u:model`, synonym `unicorn:bind`) ties an input to a field, updating on `input` events by default. Nested paths use dot notation (`book.title`, `book_ratings.excellent.title`), and list items must be addressed by index path built with `{{ forloop.counter0 }}` (`items.0.name`), because the loop variable name does not exist in the serialized state; using it silently breaks after re-render and morphdom clears the input (`docs/source/templates.md:70-117`).

**Actions**: any DOM event name becomes an attribute: `unicorn:click`, `unicorn:keyup`, `unicorn:mouseenter`, etc. The attribute value is a Python-like call expression string, e.g. `unicorn:click="set('Bob')"`. Server-side, that string is parsed with `ast.parse` and arguments evaluated with `ast.literal_eval` (`src/django_unicorn/call_method_parser.py:70-169`). Supported literal arg types: str, int, float, bool, list, tuple, dict, set. Type hints on the method drive coercion: `datetime`/`date`/`time`/`timedelta`/`UUID` from strings or epochs, Enum from its value, Django Model instances fetched by pk (`DbModel.objects.get(pk=value)` in `src/django_unicorn/views/action_parsers/call_method.py:209-220`), and arbitrary custom classes instantiated from the value (`docs/source/actions.md:60-203`).

There is also a **property-setter shortcut** with no method at all: `unicorn:click="name='Bob'"` (`actions.md:205-224`).

**Special methods**: `$refresh` (re-render from current state), `$reset` (revert to initial state, bypasses cache), `$toggle('field', 'nested.field')`, `$validate`. **Special args**: `$event` (e.g. `update($event.target.value.trim())`), `$returnValue`, `$parent` (`actions.md:309-385`).

**Modifiers** on actions: `.prevent`, `.stop`, `.discard` (drop pending model updates before the call, for cancel buttons), `.debounce-1000`, `.disable` (disable element while in flight). On models: `.lazy` (blur instead of input), `.debounce-N`, `.defer` (batch the model write with the next action), chainable (`actions.md:226-307`, `templates.md:175-236`).

**Lifecycle hooks** on the class: `mount()`, `hydrate()`, `updating/updated/resolved(name, value)` plus per-property variants `updating_name` / `updated_name` / `resolved_name`, `calling(name, args)` / `called(name, args)`, `complete()`, `rendered(html)`, `parent_rendered(html)` (`docs/source/views.md:325-399`). Since 0.66.0 each hook also emits a Django signal (`component_hydrated`, `component_method_called`, etc., used in `src/django_unicorn/views/message.py:15-21`).

**JS interop**: `Unicorn.call('component-name-or-key', 'method', args...)` triggers a method from outside the component; `Unicorn.getReturnValue()` reads the last action's return value (`actions.md:387-431`). Server-to-JS: `self.call("fn", ...)` queues a browser call, gated by the `ALLOWED_JS_CALL_LIST` setting, default `["Unicorn"]`, as an XSS defense (`src/django_unicorn/components/unicorn_view.py:353-358`, `docs/source/settings.md:25-27`).

Parameterless public methods are also exposed to the template context and callable like properties (`views.md:284-323`).

## 2. Transport and protocol

**Endpoint layout**: one URL for everything: `POST /unicorn/message/<component_name>` (`src/django_unicorn/urls.py:9`). The view is `csrf_protect` + `require_POST`, wrapped in an error handler that converts framework errors into `{"error": "..."}` JSON, 401 for auth failures, and a 304 `HttpResponseNotModified` when the render did not change (`src/django_unicorn/views/__init__.py:29-55`).

**Request body** (parsed in `src/django_unicorn/views/request.py:43-90`):

```json
{
  "id": "<component id>",
  "epoch": 1719999999,                  // client timestamp, orders requests, discards stale responses
  "key": "<optional component key>",
  "data": { "name": "World", ... },     // full public state as the client last saw it
  "meta": "<checksum>:<dom-hash>:<epoch>",  // consolidated in 0.66.0; older clients sent separate checksum/hash fields
  "actionQueue": [
    { "type": "syncInput",  "payload": { "name": "name", "value": "Bob" } },
    { "type": "callMethod", "payload": { "name": "set('Bob', count=2)" } , "partials": [...] }
  ]
}
```

The action queue batches multiple interactions into one POST. `syncInput` sets a property (dot-path capable); `callMethod` carries the raw call-expression string that is ast-parsed server-side. Special methods travel as names in the same payload (`"$refresh"`, `"$toggle('x')"`).

**Server flow** (`src/django_unicorn/views/message.py:122-291`): re-create the component (from a module cache or the Django cache), replay `data` onto it via `set_property_from_data`, run `hydrate()`, apply each queued action, run `validate()` (changed fields only, unless `$validate`), re-render the template, and diff `data` against the original to compute a minimal `data` delta for the response.

**Response body** (`src/django_unicorn/views/response.py:59-128`, docstring at `views/__init__.py:65-73`):

```json
{
  "id": "...",
  "dom": "<div unicorn:id=... unicorn:meta=...>...</div>",   // full re-rendered component HTML
  "data": { "name": "Bob" },            // only keys that changed (full state after $refresh/$reset)
  "errors": { "field": [{"code": "required", "message": "..."}] },
  "calls": [ {"fn": "...", "args": [...]} ],                 // queued JS calls, incl. children
  "meta": "<data-checksum>:<dom-hash>:<epoch>",
  "partials": [ {"key": "checked-key", "dom": "<span ...>"} ],  // replaces "dom" when partial targeting
  "return": { "method": "set", "args": ["Bob"], "kwargs": {}, "value": ... },
  "redirect": { "url": "/somewhere", "refresh": true, "title": "..." },
  "poll": { "timing": 2000, "disable": false, "method": "get_date" },
  "parent": { "id": "...", "dom": "...", "data": {...}, "meta": "..." }   // when parent force_render
}
```

**Initial render**: the `{% unicorn %}` tag renders the template and stamps the root element with `unicorn:id`, `unicorn:name`, `unicorn:key`, `unicorn:data` (the entire serialized state as an HTML attribute), `unicorn:calls`, and `unicorn:meta` (the data checksum) (`src/django_unicorn/components/unicorn_template_response.py:222-235`). The JS library scans the DOM for `unicorn:`/`u:` attributes and wires listeners (`docs/source/architecture.md:11-15`); since 0.65.0 a MutationObserver auto-initializes components inserted later.

**Concurrency**: an optional `SERIAL` setting queues requests for the same component id in the Django cache and merges their action queues, explicitly experimental and dependent on a shared cache backend (`views/message.py:44-120`, `docs/source/queue-requests.md`).

## 3. State model, checksum, and security

State round-trips fully through the client: serialized into the `unicorn:data` attribute at first render, sent back in every request's `data`, mutated server-side, and returned as a delta. Two integrity mechanisms:

- **Checksum**: `generate_checksum` = HMAC-SHA256 keyed on Django `SECRET_KEY` over `str(data)`, then shortuuid-encoded and truncated to 8 characters (`src/django_unicorn/utils.py:33-61`). Every request is rejected if the checksum over `data` does not match (`views/request.py:98-116`). This stops casual tampering with the client-held state but signs only the data dict, and 8 characters is a deliberate size/robustness trade-off.
- **Server-side cache**: components are also pickled into a module-level dict and the Django cache between requests (`unicorn_view.py:524-530`, `cacher.py`). The docs carry an explicit RCE warning: anyone with write access to the cache backend owns your process, because restore is `pickle.loads` (`docs/source/views.md:619-630`).

**What stops calling arbitrary methods**: `_is_public(name)` (`unicorn_view.py:836-940`). It is an opt-out denylist: names starting with `_`, a hardcoded list of ~50 framework attribute names, lifecycle hooks, and `Meta.exclude` entries are blocked; everything else on the class is callable from the wire (`call_method.py:177-180`) and settable via the setter shortcut (`call_method.py:74-76`). Authentication is coarse: when Django 5.1's `LoginRequiredMiddleware` is active, the message endpoint requires an authenticated user unless the component sets `Meta.login_not_required = True` (`views/message.py:130-139`). Finer authorization is entirely the developer's job inside methods.

**Meta knobs** (`docs/source/views.md:401-617`):
- `exclude`: hidden from both template context and browser.
- `javascript_exclude`: available to the Django template but never serialized to the browser; supports dotted paths into nested objects (`unicorn_view.py:543-559`). This is the standard fix for "big static choice lists bloating every payload".
- `safe`: by default every updated field value is HTML-encoded before being returned (the fix shipped after the 2021 XSS CVE); `Meta.safe = ("field",)` opts a field out via `mark_safe` (`unicorn_view.py:313-324`).
- `form_class`, `component_key`, `template_name`, `template_html`, `login_not_required`.

**Data exposure footgun**: putting a Django Model or QuerySet in state serializes every field of the model into page source; the docs warn to use `.values()` or the exclude mechanisms (`docs/source/django-models.md:9-15,122-125`).

**CVE history** (both inherent to the wire-format design):
- CVE-2021-42053: stored XSS, versions <= 0.35.3; AJAX-returned values were not escaped. Fix: encode by default, `Meta.safe` to opt out.
- CVE-2025-24370: Python class pollution via `set_property_value`, the function that applies client-supplied dotted property paths. Crafted `actionQueue` payloads could traverse into Python internals and rewrite runtime state, yielding XSS, DoS, and auth bypass "in almost every Django-Unicorn-based application" (GHSA-g9wf-5777-gq43). Fixed in 0.62.0 (Feb 2025). A follow-up hardening commit ("Prevent bulk data tampering (defense in depth)") landed as late as 0.67.0 (Mar 2026).

## 4. DOM update

- **Morphing**: full component HTML comes back and is merged into the live DOM with morphdom by default; the `MORPHER` setting can swap in the Alpine.js morph plugin (needed when Alpine manages state inside a component) (`docs/source/architecture.md:29`, `docs/source/custom-morphers.md`, `settings.md:65-75`). Merge identity uses `unicorn:id`, then `unicorn:key`, then element `id` (`templates.md:270`).
- **Hard constraint**: exactly one root element per component; the server checks and warns (`unicorn_template_response.py:113-147`). `<tr>` components are a documented trouble spot (browser foster-parenting breaks the diff, `templates.md:5-26`; there is a dedicated `table-limitations.md`).
- **Partial updates**: `unicorn:partial="target"` (with `.id` / `.key` modifiers, multiple allowed) makes the response carry only the targeted fragments. Implementation detail worth knowing: the server still renders the whole component, then extracts the subtree with lxml (`views/message.py:251-286`), so partials save bandwidth and DOM churn, not server render time.
- **Skip-if-unchanged**: the server hashes the rendered DOM; if it equals the client-sent hash and there is no return value or JS call, it raises `RenderNotModifiedError` and answers 304 (`views/response.py:82-95`). The 0.66.0 epoch mechanism additionally lets the client discard stale out-of-order responses.
- **Loading states**: `unicorn:loading` (show), `.remove` (hide), `.attr="disabled"`, `.class="..."`, `.class.remove`, `.delay` (only show after 200 ms); scoped to a trigger with `unicorn:target="id-or-key"` including `*` wildcards (`docs/source/loading-states.md`).
- **Dirty states**: `unicorn:dirty.attr` / `.class` / `.class.remove` mark inputs whose model value has not yet synced (`docs/source/dirty-states.md`).
- **Polling**: `unicorn:poll` on the root element, default 2 s, `unicorn:poll-5000="method"` for custom period/method, `.disable="field"` (negatable with `!`), pauses on inactive tabs, and a `PollUpdate` return object lets an action retune or stop polling dynamically (`docs/source/polling.md`).
- **Escape hatch**: `unicorn:ignore` excludes an element subtree from morphing (Select2 and friends) (`templates.md:294-343`).
- **Visibility**: `unicorn:visible` fires a method when the element scrolls into the viewport (`docs/source/visibility.md`).

## 5. Validation and Django form integration

- `Meta.form_class = SomeForm` attaches a plain Django `Form`/`ModelForm` for validation, so the same form works in classic views and in the component (`docs/source/validation.md:1-43`).
- On every render the form is constructed over current attributes and `is_valid()` runs; cleaned values are written back into the frontend variables using each widget's `format_value`, with special-casing for checkboxes and selects (`unicorn_view.py:566-596, 605-620`).
- After normal actions only the changed fields are validated; the `$validate` magic action, `self.validate()`, or `self.is_valid()` validate everything (`views/message.py:223-233`, `validation.md:45-97`).
- Errors surface three ways: `unicorn:error:invalid` / `unicorn:error:required` attributes injected onto the bound elements (CSS-targetable), the `unicorn.errors` template context, and a `{% unicorn_errors %}` tag (`validation.md:99-154`). Errors also ride in the response `errors` dict.
- Manual path: raise `ValidationError({"model.field": "msg"}, code="required")` from any action; it is merged into `component.errors` (`validation.md:156-183`, `views/message.py:200-201`).
- Form instances passed in as template kwargs are auto-excluded from browser state and stripped before pickling; they are `None` on subsequent AJAX requests, which the docs call out (`views.md:210-245`).

## 6. Pain points, limits, and project status (as of 2026-07)

**Status**: originally adamghill/django-unicorn; Adam Hill published a request-for-maintainers on 2025-06-03 (dev.to) after 4+ years solo, and the project moved into the django-commons org. New maintainers revived it: releases 0.63.3 through 0.67.0 shipped Jan-Mar 2026 (vs a gap through most of 2025), largely driven by one new contributor (JohananOppongAmoateng per changelog credits). Repo: 2656 stars, 132 forks, 51 open issues, last push 2026-05-22, not archived. Still versioned 0.x after six years; the docs themselves say "Unicorn isn't in the same league as htmx or alpine.js" (`faq.md:43`).

**Self-admitted architecture problems** (from the maintainer request): complex custom JS + backend integration, reliance on undocumented Django APIs, and "child components and caching approaches need rethinking".

**Issue-tracker themes** (top-reacted/most-commented open issues, 2026-07-04):
- Performance and concurrency: async message endpoint (#19), general performance optimization (#110), rapid-fire action events (#111), a component inside a `{% for %}` loop re-runs its DB query or full render per element (#643).
- Production breakage: "Error 500 in production" (#408, 24 comments, typically cache/multi-process related), type-hint resolution failures in `_attribute_names()` (#639).
- Integration gaps: Django Forms integration "not working well" (#469), no easy full-form rendering (#745), validation for object-valued fields (#220), file download from actions (#486), broken `stopPropagation` (#515).
- Architecture wishes: router pattern (#183), dynamic page component loading (#235).

**Inherent limits worth internalizing**:
- One POST per interaction; a keystroke without `.lazy`/`.debounce`/`.defer` is a network round trip plus a full server re-render plus pickling. The FAQ's defense is "you'd need an AJAX call anyway" (`faq.md:23-25`).
- Full state through the browser: payload grows with state, secrets leak by default (models), and `javascript_exclude` bookkeeping becomes mandatory hygiene.
- Two CVEs both came from the same root: the client sends rich, interpretable structures (Python call expressions, dotted set-paths) that the server trusts after a thin checksum.
- Child components are the weakest subsystem: pickling RecursionError (fixed 0.63.0), non-reactive children (#738), `self.parent.force_render = True` as the documented way to update a parent (`child-components.md:59-74`), and heavy parent-DOM reconciliation logic in `views/response.py:130-206`.
- Context processors do not run on component re-renders; the docs teach workarounds (`templates.md:345-429`).
- HTML shape constraints (single root, no bare `tr`, index-path model names in loops) fail at runtime, sometimes silently (cleared inputs).

**Community sentiment**: HN comments are largely positive from actual users ("extremely productive", "using it in prod", winrid 2023-2024) but the recurring counterpoints are: client-side-capable validation still costs a POST per keystroke (sgt, 2023-08), fine-grained UX control eventually demands hand-written JS anyway (phil-martin, 2022-07), and htmx+Alpine won the Django ecosystem's default mindshare (acknowledged in Hill's own maintainer post).

## 7. What to steal, what to avoid

### Worth stealing (top 5)

1. **The attribute vocabulary and modifier grammar.** `x:click="method(arg)"` plus chainable modifiers (`.prevent`, `.stop`, `.debounce-N`, `.lazy`, `.defer`, `.discard`, `.disable`) and the sibling attributes `loading`/`dirty`/`target`/`ignore`/`poll` is a complete, learnable UX vocabulary that covers 90 percent of interactivity needs. citry's `<c-*>` syntax can adopt this grammar nearly verbatim, and since citry compiles templates it can validate targets at compile time instead of unicorn's runtime lookups.
2. **Type-hint-driven argument coercion.** Client sends primitives; the method signature's annotations coerce to datetime/UUID/Enum/model-by-pk/custom classes (`call_method.py:186-229`). This keeps templates clean and Python idiomatic. Steal the coercion, not the transport (see mistake 5).
3. **Cheap no-op detection: content hash 304s and epoch-ordered responses.** Hash the rendered output, let the client tell you what it has, answer 304 when nothing changed, and stamp responses with the request epoch so the client can drop stale ones (`views/response.py:82-95`, 0.66.0 changelog). Very high value for a polling/typeahead world at near-zero design cost.
4. **Action queue batching with deferred model writes.** Bundling `defer`-ed input syncs with the next action into one request (`architecture.md:19`) collapses chatty interactions into single round trips. Combined with per-action `partials` targeting, it is a good latency/payload budget system.
5. **Host-framework-native validation.** Reusing Django forms, mapping errors onto elements as attributes (`unicorn:error:invalid`) plus an errors dict, and validating only changed fields per interaction is the right shape: no parallel validation DSL. For citry: reuse whatever the host app already validates with, and define the error-to-element channel in the protocol from day one.

### Mistakes to avoid (top 3, plus two dishonorable mentions)

1. **Do not round-trip full component state through the client guarded by a thin checksum.** It leaks data by default (whole-model serialization warnings in unicorn's own docs), bloats every request, requires `javascript_exclude` hygiene forever, and made the server a deserializer of attacker-shaped state, which is exactly where CVE-2025-24370 lived. Keep authoritative state server-side (signed component id into a server store), or if state must travel, sign the complete envelope (id + name + data) with a full-length MAC and validate against a declared field schema, not against "whatever public attributes exist".
2. **Do not make "public by default" the security model.** In unicorn every non-underscore method and field is remotely callable/settable, with an opt-out denylist (`_is_public`, `unicorn_view.py:836-940`). The safe default is inverted: events callable from the wire should be explicitly registered (decorator or Meta allowlist), and settable fields explicitly declared. This also kills the class-pollution attack surface (client-supplied dotted paths into arbitrary Python objects) by construction.
3. **Do not build persistence on pickle in a shared cache.** It couples correctness to cache topology (the "works in dev, 500s in production" issue class, #408), turns any cache-write compromise into RCE (their docs say so), and makes every non-picklable attribute a landmine (generators, forms, recursive children). Use an explicit, versioned, serializable state format.
4. Avoid coupling component identity to fragile HTML shape at runtime: one-root-only, `tr` breakage, and loop-variable model names that silently clear inputs are all runtime failures a compiling framework can catch statically. citry's parser can assign stable keys and reject invalid shapes at build time.
5. Avoid shipping executable-looking strings as the wire format. Parsing `"set('Bob', count=2)"` server-side with `ast.parse`/`literal_eval` was clever but produced a large parsing/coercion subsystem (`call_method_parser.py` + 267-line handler), an LRU cache over attacker-controlled strings, and a fuzzier security review story. Parse the expression client-side (or compile-time) into structured JSON: `{"method": "set", "args": ["Bob"], "kwargs": {"count": 2}}`, and keep the type coercion from steal-item 2.
