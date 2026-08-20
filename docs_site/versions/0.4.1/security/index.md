---
title: Security
url: https://citry.dev/v/0.4.1/security/
description: "Protect Citry templates and server events with expression sandboxing, explicit State, CSRF checks, and authorization."
---
# Security

Citry protects two different boundaries. Template expressions run in a Python
sandbox. Server events receive values that have traveled through the browser,
so their handlers need the same validation, CSRF protection, and authorization
as any other HTTP endpoint.

The sandbox is on by default. Event routes also apply a same-origin floor by
default, but only your application can decide whether the current user may act
on a particular record.

## Choose a CSP compatibility mode

Citry can validate its rendered component subtree against the expression
language in its pinned Alpine CSP runtime:


```citry
from secrets import token_urlsafe

app = Citry(security_csp="strict")

nonce = token_urlsafe(16)
html = Page().render().serialize(csp_nonce=nonce)
```


The modes have distinct rollout purposes:

- `"off"` keeps the standard Alpine runtime and existing output.
- `"warn"` keeps that same runtime and HTML, but emits one `RuntimeWarning`
  containing incompatible reached expressions or rendered markup. Findings
  stay separate per rendered instance when a late string hook prevents Citry
  from proving that two occurrences came from one authored source site.
- `"strict"` selects Citry's version-matched Alpine CSP runtime and rejects
  incompatible output before returning HTML.

Strict validation covers component-boundary expressions that may disappear
during rendering and the final HTML after extension hooks. It rejects Alpine
syntax the pinned CSP evaluator cannot interpret, raw `<script>` and `<style>`
elements, any ASCII-case-insensitive `on*` attribute, and `javascript:` URLs.
Put complex browser logic in `Component.js` and call a scope method from the
template. Put trusted
scripts and styles in `Component.js`, `Component.css`, or structured
[`Dependencies`][citry.ext.dependencies.Dependencies].

Citry UI's production component definitions are checked in CI against the
pinned Alpine CSP expression subset. That guarantee covers the public library
components and its registered internal renderers. Documentation snippets are
teaching material and are not a compatibility allowlist; run `citry check`
before copying an example's browser expressions into a strict application.

Run `citry check` or use the Citry editor extension to get the same pinned
expression findings at source locations. Per-render mode overrides are
enforced during serialization; project tooling reports the configured engine
default.

Citry owns runtime selection and its rendered subtree. Your application still
owns the response header, nonce generation, layouts, third-party resources,
and directives other than the documented Citry boundary.

## Choose how much JavaScript Citry may deliver

JavaScript delivery is separate from CSP. Set `security_javascript` on the
engine, or override it for one serialization:


```citry
app = Citry(security_javascript="forbid")

email_html = Page().render().serialize(
    security_javascript="omit",
)
```


The four modes answer different questions:

- `"allow"` preserves normal interactive output.
- `"warn"` preserves those exact bytes and emits one `RuntimeWarning` that
  inventories reached browser behavior.
- `"omit"` removes Citry-managed executable scripts, Alpine and Events
  runtimes, preloaders, and browser manifests. Server-rendered HTML and CSS
  remain. Authored Alpine attributes remain inert.
- `"forbid"` rejects a rendered subtree that needs executable client
  behavior, even when `deps_strategy="simple"` or `"ignore"` would otherwise
  hide the corresponding runtime or dependency tag.

The inventory covers active component-boundary bindings, final structured
dependencies after hooks, and settled HTML after string-level extensions. It
recognizes Alpine and Events attributes, executable script types, native
`on*` handlers, `javascript:` URLs, and executable HTML embedded through
`iframe srcdoc` or HTML data documents. A declared but unused Events method
is not by itself an active requirement.

`"omit"` is a static-export tool, not an HTML sanitizer. Raw executable
scripts, native handlers, and JavaScript URLs are left unchanged and reported;
use `"forbid"` when they must make serialization fail. Omit also warns about
high-confidence fallback hazards such as `x-cloak`, structural Alpine
templates, and handler-only controls. Check the resulting page without
JavaScript and provide native links or forms for essential actions.

CSS remains allowed in every mode. An omit fragment emits its CSS directly,
without a preloader, manifest, mounted route, or existing browser manager.
`deps_strategy="ignore"` keeps its existing meaning and suppresses collected
CSS too. When an exact structured stylesheet or inert data script carries an
executable attribute, omit removes that attribute while retaining the CSS or
data. Opaque dependency renderers are removed because Citry cannot prove what
tag they create.

With `security_csp="strict"`, omit and forbid do not validate inert Alpine
expressions because no Alpine runtime is emitted. Strict CSP still validates
raw executable markup and applies the response nonce to retained structured
inline styles.

## Pin Citry-managed scripts with SRI

Set `security_script_integrity="citry"` when you want Citry to bind its
structured script output to exact bytes:


```citry
app = Citry(security_script_integrity="citry")

serialized = Page().render().serialize_result()
html = serialized.html
script_sources = " ".join(serialized.security.csp_script_hashes)
```


Citry computes SHA-384 after inline script wrapping, adds `integrity` to
external scripts whose response bytes it owns, and carries the attribute into
fragment dependency descriptors. The result includes immutable per-script
records and quoted hash sources suitable for adding to the host's
`script-src`. Citry does not construct the complete CSP header because the host
also owns layouts, analytics, and every resource outside the component render.

For a third-party URL, provide its published `integrity` value on a
[`Script`](/v/0.4.1/reference/dependencies/#citry-ext-dependencies-script). Citry validates and preserves the
value but reports it as unverified; it never downloads third-party code during
serialization. Configure CORS and `crossorigin` as required by that resource.

This option provides byte identity and hash metadata. It composes with
`security_csp="strict"`, but does not enable that expression policy by itself.

## Apply a request CSP nonce centrally

Generate a fresh unpredictable nonce for each response, place its matching
source in the host-owned CSP header, and pass the raw value at final
serialization:


```citry
from secrets import token_urlsafe

nonce = token_urlsafe(16)  # 128 random bits before URL-safe base64 encoding
serialized = Page().render().serialize_result(csp_nonce=nonce)

policy = (
    "default-src 'self'; "
    f"script-src 'self' 'nonce-{nonce}'; "
    f"style-src 'self' 'nonce-{nonce}'"
)
```


Your web framework still sends `serialized.html` with `policy` as the
`Content-Security-Policy` response header. Citry validates the nonce's CSP
base64 syntax, but the host owns its entropy, freshness, response header, and
every resource outside the Citry render. The
[CSP specification](https://www.w3.org/TR/CSP/#security-nonces) recommends at
least 128 random bits before encoding.

Citry adds the value after dependency hooks have run. Every structured
[`Script`](/v/0.4.1/reference/dependencies/#citry-ext-dependencies-script), including external scripts and inert
JSON manifests, receives it. Every structured inline
[`Style`](/v/0.4.1/reference/dependencies/#citry-ext-dependencies-style) receives it; external stylesheet links
do not. A matching explicit nonce is accepted, while a different or malformed
one is an error. The original dependency objects are not mutated, so one render
can be serialized for separate responses with separate nonces.

Raw `<script>` and `<style>` elements written directly in template HTML are not
automatically trusted or nonced. Move trusted code to `Component.js`,
`Component.css`, or a structured dependency. Strict mode rejects those raw
elements after all render hooks have run.

The browser manager records the nonce that authorized its own script tag. When
a later fragment creates a structured script or inline style, the manager adds
that document nonce if the descriptor omits it and rejects a different value
before inserting the dependency batch. Off and warning fragments may load the
standard manager through their preloader. Strict fragments contain only inert
markup and manifests and require a strict Citry base document with an existing
CSP manager. A present manager rejects nonce or runtime-variant mismatches
before adoption; without one, the fragment remains inert.

Do not cache nonce-bearing HTML separately from its response header. If a full
response is cached, its HTML and CSP header must remain one artifact.

## Treat State as client input

With the default signed storage, every State value is visible in the page
source. The signature stops a user from silently changing the server-minted
token, but it does not encrypt the token. Public fields may also be changed
deliberately through `$state` and two-way `:c-*` bindings.

`State._public` controls which values `$state` and bindings can read in plain
form. It does not make the other State fields secret because those fields still
travel inside the signed token. `State._model` narrows which public fields the
browser may write. Neither list replaces authorization.

Keep secrets out of State. Prefer a small record id, then reload the record and
check the current user's permission in every handler:


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


If State cannot be readable in the page at all, `State._storage = "server"`
stores its values in the configured Citry cache and sends an opaque lookup key.
That adds a shared-cache requirement in multi-worker deployments. It does not
change the client-input rule: authorize every use of the restored values.

## Protect event posts from CSRF

Every non-GET Events request passes Citry's always-on cross-site request
floor. JSON calls must carry the `X-Citry-Events` header. When the browser
supplies `Origin`, its authority must match the request's `Host`; when it
supplies `Sec-Fetch-Site`, the value must be `same-origin` or `none`. These
checks remain in place even when a handler sets `csrf=False`.

Django's `CsrfViewMiddleware` applies to Citry routes normally. Citry does not
exempt them. The client runtime reads Django's `csrftoken` cookie and sends it
as `X-CSRFToken` by default, so keep the middleware enabled. Django still owns
token creation, rotation, cookie or session storage, and validation. Citry
only carries the token on requests made by its browser runtime.

If Django stores the token in the session or makes the CSRF cookie `HttpOnly`,
JavaScript cannot read that cookie. Render Django's masked token into the DOM,
then configure a token function instead:


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


Citry templates do not interpret Django's `{% csrf_token %}` tag. Pass the
masked token returned by Django's `get_token(request)` as the component's
`csrf_token` input. The same hidden input is what a native form post needs, so
native forms continue to follow the host's normal token rules.

FastAPI, Starlette, Flask, and bare ASGI or WSGI do not provide one standard
host token scheme. If your application requires an additional token, configure
a callable on the component or one handler:


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


Use [`Citry.events.configure`](/v/0.4.1/reference/browser-apis/#citry-events-configure) to tell the browser
where to find and send a custom token before the runtime starts making calls:


```javascript
Citry.events.configure({
  csrf: {
    cookie: "app_csrf",
    header: "X-CSRF-Token",
  },
});
```


The `csrf=False` override disables only Citry's configurable callable token
check. The always-on cross-site request floor and independently configured
host middleware still apply. It does not exempt a Django route from
`CsrfViewMiddleware`.

GET event handlers are exempt from CSRF protection because GET must be safe and
read-only. Citry enforces the declared HTTP method, but it cannot prove that the
Python body has no side effects. Expose only idempotent reads as GET handlers.

## Authorize every event

Placement inside `class Events` makes a public method remotely callable. Use a
component-wide `_guard`, a per-handler `@event(guard=...)`, or an explicit check
inside the handler. A guard runs for every matching call and may reject it with
`EventError`:


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


Guards are useful for rules shared by all handlers. Keep payload-dependent
authorization in the typed handler body, after the input has been validated.
Authentication still belongs to the host application and is available through
the injected neutral `request` or `request.native`.

For the handler and State workflow, see [Server events](/v/0.4.1/events/). The
[direct event routes](/v/0.4.1/events/http/) page covers the HTTP-facing cases.

## Sandbox Python template expressions

Anything inside `{{ }}` or a `c-*` attribute is Python code. Citry evaluates it
through a sandbox that blocks the ways an expression could reach dangerous
parts of the runtime.

### How the sandbox works

An expression passes through two layers before it produces a value.

- A Rust layer parses the expression and allows only a whitelist of
  expression shapes. Statements (assignments, `del`, `import`, `raise`,
  `assert`, `async`/`await`, `yield`) are not expressions, so they are rejected
  when the expression is compiled. This raises a `SyntaxError`.
- A Python layer runs at evaluation time. It rewrites every variable read,
  attribute access, subscript, and call into a checked version, and those
  checks enforce the actual access rules against your render context. A blocked
  access raises [`SecurityError`](/v/0.4.1/reference/rendering/#citry-securityerror).

The two layers fail at different times. Forbidden syntax fails when the
expression is compiled; a blocked access fails only when the expression is
evaluated with a context.

### What the sandbox blocks

The sandbox is modeled on Jinja's sandbox. It blocks the known escape routes:

- **Private and dunder attributes.** Any attribute whose name starts with an
  underscore is blocked, including dunders like `__class__`. This closes the
  usual traversal from an object to `__globals__` and `__builtins__`.
- **Underscore names and dict keys.** A variable name starting with `_`, a
  walrus target starting with `_`, and a string dict key starting with `_`
  (for example `data['_key']`) are all blocked.
- **Dangerous callables.** A denylist covers `eval`, `exec`, `__import__`,
  `getattr`, `setattr`, `open`, `str.format`, and others. The check is by
  identity, so passing one into the context under a harmless name does not get
  around it.

Here is the private-attribute rule in action:


```python
from citry import SecurityError
from citry_core.safe_eval import safe_eval

# Dunder / private attribute access is blocked at eval time
compiled = safe_eval("obj.__class__")
try:
    compiled({"obj": object()})
except SecurityError as e:
    print(e)  # attribute '__class__' on object '<class 'object'>' is unsafe
```


And the identity-based callable check, which catches a renamed builtin:


```python
from citry import SecurityError
from citry_core.safe_eval import safe_eval

# eval() is blocked even when smuggled in under a harmless-looking name
compiled = safe_eval("totally_no_e_val('1+1')")
try:
    compiled({"totally_no_e_val": eval})
except SecurityError as e:
    print(e)  # function '<built-in function eval>' is unsafe
```


`str.format` and `str.format_map` are blocked because their format syntax can
reach `__builtins__`. Use f-strings, which the parser rewrites into a safe
call.

### Why builtins are not available

No Python builtins are exposed inside expressions. `len`, `str`, `range`, and
the rest are not there. This is a direct consequence of the sandbox: builtins
are looked up in your render context, and the context does not contain them
unless you put them there. So `{{ len(items) }}` fails with `KeyError: 'len'`.

The recommended fix is to compute derived values in a component's
`template_data` method, which is plain Python with every builtin available, and
pass the result to the template. See [Expressions](/v/0.4.1/syntax/expressions/) for
the full pattern.


```citry
class Cart(Component):
    template = """
      <p>{{ count }} items</p>
    """

    def template_data(self, kwargs, slots):
        return {"count": len(kwargs["items"])}
```


### Marking your own functions unsafe

The denylist covers known-dangerous builtins, but a function you write is
allowed to be called from an expression by default. To forbid a specific
function, decorate it with `unsafe`. Django-style methods with
`alters_data=True` are blocked the same way.


```python
from citry import SecurityError
from citry_core.safe_eval import safe_eval, unsafe

@unsafe
def dangerous_function():
    return "dangerous"

compiled = safe_eval("dangerous_function()")
try:
    compiled({"dangerous_function": dangerous_function})
except SecurityError:
    print("blocked")
```


### What the sandbox does not protect

Be honest about the boundary. The sandbox is a whitelist of allowed syntax plus
a denylist and attribute filter at runtime. It blocks the documented escape
vectors, but it is not a formally proven-complete jail.

- **Custom objects expose their whole public API.** Any object you place in the
  context is reachable through every attribute and method that does not start
  with an underscore. If one of those methods can do something dangerous, an
  expression can call it. The sandbox filters attribute names; it does not
  reason about what your methods do.
- **Your own callables are allowed unless you opt out.** A function you write is
  callable from an expression until you mark it `unsafe` or set
  `alters_data=True`.
- **The denylist is a denylist.** It covers the known-dangerous builtins. Treat
  it as blocking specific vectors, not as an absolute guarantee.

The rule of thumb: only put objects and functions into your render context that
you are comfortable exposing to template authors.

### Browser CSP and Alpine expressions

The Python sandbox described above does not govern browser expressions. Citry
ships both Alpine's standard evaluator and a version-matched CSP evaluator.
The standard `security_csp="off"` and `"warn"` modes require `unsafe-eval` when
they evaluate Alpine attributes. `security_csp="strict"` selects the CSP
runtime and enforces its smaller expression language before serialization.

See [Alpine runtime](/v/0.4.1/advanced/alpine-runtime/#use-content-security-policy) for
the client-side loading and fragment contract.

### Turning the sandbox off

If every template on a citry instance comes from a trusted source, you can turn
the sandbox off with [Citry](/v/0.4.1/reference/citry/#citry-citry) and `sandbox_expressions=False`. This
removes the access checks for that instance. Do this only for trusted input.


```python
from citry import Citry

app = Citry(sandbox_expressions=False)
```


Two things stay the same even with the sandbox off, so a successful render
produces byte-identical output either way: builtins remain unavailable, and a
walrus assignment still writes back into the variables mapping. The difference
shows only on failures.