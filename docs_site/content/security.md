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
| A template expression reaches dangerous Python | Runs expressions in a sandbox | Put only safe objects in the template context |
| Injected scripts on the page | Nothing until you opt in | Send a Content Security Policy with a nonce |

The first two rows apply to every app that uses
[server events](/events/), and the third to every app. The Content
Security Policy (CSP) sections later on are optional hardening.

## Treat State as input { #treat-state-as-client-input }

An event handler receives its [State](/events/state/) from the browser, so
treat it like any other form input. With the default storage, every State
value is visible in the page source. Citry signs the values, so a user
cannot change them silently, but it does not encrypt them. Fields listed in
`State._model` (every public field, by default) can also be changed on
purpose through `$state` and two-way `:c-*` bindings.

Keep secrets out of State. Store a small record id instead, then load the
record and check the current user's permission in every handler:

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
  request's `Host` header.
- When the browser sends a `Sec-Fetch-Site` header, it must be
  `same-origin` or `none`.

These checks cannot be turned off, not even with `csrf=False`.

### Use Django's token

Django's `CsrfViewMiddleware` checks Citry's routes like any other view, so
keep it enabled. Citry's browser code reads Django's `csrftoken` cookie and
sends it as the `X-CSRFToken` header. Django still creates, rotates, stores,
and checks the token.

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
Citry.events.configure({
  csrf: {
    token: () => document.querySelector(
      '[name="csrfmiddlewaretoken"]',
    ).value,
  },
});
```

The same hidden input also works for a normal HTML form post.

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
in, with [`Citry.events.configure`][Citry.events.configure]. Call it before
the page makes its first event call:

```javascript
Citry.events.configure({
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

## Sandbox template code { #sandbox-python-template-expressions }

Anything inside `{{ }}` or a `c-*` attribute is a Python expression. Citry
runs it in a sandbox that blocks the known ways an expression could reach
dangerous parts of Python. The sandbox is on by default and modeled on
Jinja's sandbox.

### What is blocked { #what-the-sandbox-blocks }

- **Names starting with `_`.** An attribute such as `obj.__class__` or
  `obj._cache`, a variable such as `_x`, and a string dict key such as
  `data['_key']` are all blocked. This closes the usual path from an
  object to Python's globals and builtins.
- **Dangerous functions.** A list of builtins such as `eval`, `exec`,
  `__import__`, `getattr`, `setattr`, and `open` is blocked. The check
  compares the function itself, not its name, so passing `eval` into the
  context under another name does not get around it.
- **`str.format` and `str.format_map`.** Their format syntax can reach
  builtins. Use an f-string instead.
- **Statements.** Assignments, `del`, `import`, `raise`, `assert`,
  `async`/`await`, and `yield` are not expressions.

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

### What it does not stop { #what-the-sandbox-does-not-protect }

The sandbox checks names. It does not know what your code does, and it is
not guaranteed to block every way out:

- **Your objects expose every public method.** An expression can call any
  attribute or method of a context object whose name does not start with
  `_`. If one of them deletes data, a template can call it.
- **Your functions can be called.** A function you put in the context is
  allowed until you block it, as shown next.
- **The blocked list covers known dangers.** It is a list of specific
  functions, not a guarantee.

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

A successful render gives the same output either way. Builtins are still
missing, and a walrus assignment (`:=`) still writes into the template's
variables. Only the blocked accesses behave differently.

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
    f"style-src 'self' 'nonce-{nonce}'"
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

### Nonces in fragments { #html-fragments }

Citry's browser code reads the page's nonce when the page loads. When an
[HTML fragment](/advanced/html-fragments/) arrives later, it puts that nonce
on every script, inline style, and stylesheet link it adds, so the
fragment response does not need to know the nonce. Under
`security_csp="strict"`, a fragment does not load Citry's browser code, so
insert it only into a page that already has it.

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

Use a Vue binding such as `@click` instead of `onclick`, and move scripts
and styles to `Component.js`, `Component.css`, or structured
[`Dependencies`][citry.Component.Dependencies].

`"strict"` also raises:

- `ValueError` when the output contains a script (inline or loaded by URL)
  or an inline style, and you did not pass `csp_nonce`;
- `TypeError` when a dependency is not a structured `Script` or `Style`.

You can pass `security_csp` to `serialize()` to override the mode for one
render. Any other value raises `ValueError`, both in `Citry(...)` and in
`serialize()`.

The Citry editor extension and `citry check` report the same problems at
their place in your source files, when the problem is visible in the
source file.

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
`javascript:` URLs, and HTML that runs scripts through `iframe srcdoc` or
an HTML data URL. It checks dependencies and HTML after extensions have
changed them. An `Events` method that no template calls does not count.

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

## Pin scripts with SRI { #pin-citry-managed-scripts-with-sri }

Subresource Integrity (SRI) makes the browser run a script only when its
bytes match a hash. With `security_script_integrity="citry"`, Citry
computes SHA-384 hashes for the scripts it outputs and gives you the
hashes to put in your CSP header:

```python
app = Citry(security_script_integrity="citry")

page = Page()
serialized = page.render().serialize_result()
html = serialized.html
script_sources = " ".join(
    serialized.security.csp_script_hashes,
)
```

Citry adds an `integrity` attribute to external scripts it serves, and
hashes each inline script in the exact form it is sent. `csp_script_hashes` lists the
hashes, quoted, ready to add to `script-src`.
`serialized.security.scripts` holds one record per script. Citry does not
build the whole CSP header, because your app also owns layouts, analytics,
and every resource outside the render.

The option works together with `security_csp="strict"` but does not turn
it on. The default is `"off"`. Any value other than `"off"` or `"citry"`
raises `ValueError`, both in `Citry(...)` and in `serialize()`.

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
components never start, and the browser console shows a CORS or
Subresource Integrity error.

Citry always adds `integrity` to the scripts and stylesheets it serves for
interactive components, even without the option above. It loads them with
`crossorigin="anonymous"`, and its file routes answer with
`Access-Control-Allow-Origin: *`. These routes are `/citry/citry.js`, the
component JS and CSS, and the compiled component code.

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
