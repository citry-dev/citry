---
title: Security
url: https://citry.dev/v/0.3.1/security/
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

Every non-GET Events request passes Citry's always-on same-origin checks. JSON
calls must carry the `X-Citry-Events` header, and browser-supplied `Origin` and
`Sec-Fetch-Site` headers must identify the same origin. These checks remain in
place even when a handler sets `csrf=False`.

Django's `CsrfViewMiddleware` applies to Citry routes normally. Citry does not
exempt them. The client runtime reads Django's `csrftoken` cookie and sends it
as `X-CSRFToken` by default, so keep the middleware enabled. A native form post
also follows Django's normal token rules.

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


Use [`Citry.events.configure`](/v/0.3.1/reference/browser-apis/#citry-events-configure) to tell the browser
where to find and send a custom token before the runtime starts making calls:


```javascript
Citry.events.configure({
  csrf: {
    cookie: "app_csrf",
    header: "X-CSRF-Token",
  },
});
```


The `csrf=False` override disables Citry's configurable token layer, whether
it was automatic or callable. The always-on same-origin/header checks and
independently configured host middleware still apply.

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

For the handler and State workflow, see [Server events](/v/0.3.1/events/). The
[direct event routes](/v/0.3.1/events/http/) page covers the HTTP-facing cases.

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
  access raises `SecurityError`.

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
from citry_core.safe_eval import safe_eval, SecurityError

# Dunder / private attribute access is blocked at eval time
compiled = safe_eval("obj.__class__")
try:
    compiled({"obj": object()})
except SecurityError as e:
    print(e)  # attribute '__class__' on object '<class 'object'>' is unsafe
```


And the identity-based callable check, which catches a renamed builtin:


```python
from citry_core.safe_eval import safe_eval, SecurityError

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
pass the result to the template. See [Expressions](/v/0.3.1/syntax/expressions/) for
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
from citry_core.safe_eval import safe_eval, unsafe, SecurityError

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
currently ships Alpine's standard build, whose expression evaluator requires
`unsafe-eval` in `script-src`. A nonce can authorize inline Citry scripts, but
it cannot replace that evaluator permission.

Citry does not currently support Alpine's CSP build. See
[Alpine runtime](/v/0.3.1/advanced/alpine-runtime/#content-security-policy) for the
client-side loading and policy contract.

### Turning the sandbox off

If every template on a citry instance comes from a trusted source, you can turn
the sandbox off with [Citry](/v/0.3.1/reference/citry/#citry-citry) and `sandbox_expressions=False`. This
removes the access checks for that instance. Do this only for trusted input.


```python
from citry import Citry

app = Citry(sandbox_expressions=False)
```


Two things stay the same even with the sandbox off, so a successful render
produces byte-identical output either way: builtins remain unavailable, and a
walrus assignment still writes back into the variables mapping. The difference
shows only on failures.