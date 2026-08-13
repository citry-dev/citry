# Design and guide: Cross-Site Request Forgery protection

**Status (2026-08-12): implemented for Citry Events.** The host owns token
generation and validation. Citry preserves the host's middleware and token
convention on requests made by Citry's browser runtime, and adds an always-on
cross-site request floor to non-GET Events calls. Native forms continue to use
the host's normal hidden-field convention.

This document is the focused source of truth for CSRF ownership and usage.
The full Events transport design remains [`events.md`](events.md), especially
sections 5.2 and 7.4. Public user-facing guidance lives on the docs site's
[`security.md`](../../docs_site/content/security.md) page. CSP is independent
and lives in [`security_csp.md`](security_csp.md).

---

## 1. Decision

Citry must not invent a second application-wide CSRF token scheme.

- Django, or equivalent host middleware, owns token creation, rotation,
  storage, trusted-origin configuration, and validation.
- Citry-owned fetches attach the host token using a configurable source and
  header.
- Citry Events adds a host-neutral cross-site request floor beneath any
  per-handler setting.
- Native form posts include the host's hidden field explicitly.
- Authentication and record-level authorization remain separate checks.

This division follows the actual request boundary. The host sees the request
first and knows its sessions, cookies, proxies, origins, and authentication.
Citry knows which browser requests it creates and can make those requests
carry the expected signals.

## 2. What CSRF protects against

Browsers automatically attach ambient credentials such as session cookies to
matching requests. Without CSRF protection, a malicious site can cause a
victim's browser to submit a state-changing request to another application
where that victim is logged in.

The classic attack is:

1. A user signs in to `bank.example`, and the browser stores that site's
   authentication or session cookie.
2. The user later visits `evil.example` without signing out of the bank.
3. The malicious page submits a form whose `action` targets a state-changing
   `bank.example` URL, such as a transfer endpoint.
4. The form belongs to `evil.example`, but the request is addressed to
   `bank.example`. Subject to the cookie's `SameSite` and other cookie rules,
   the browser attaches cookies belonging to `bank.example` to that outgoing
   request.
5. If the bank treats the authentication cookie as sufficient proof, it may
   perform the action as the signed-in user even though that user never
   intended to make the request.

The malicious site normally cannot read the bank's cookie or response because
of the same-origin policy. It does not need to read either one to cause a
state change. A CSRF token adds proof that the request came through an
application surface that received the unpredictable token, rather than from a
cross-site form that merely benefits from the browser's ambient cookies.

`SameSite=Lax` or `SameSite=Strict` cookies block important forms of this
attack, including many cross-site POST cases. They are valuable defense in
depth, but Citry must not assume that every application cookie, browser,
subdomain relationship, or request flow is covered. Host CSRF validation and
Citry's request floor remain necessary.

CSRF protection answers a narrower question than authentication:

- authentication asks who the request is acting as;
- CSRF checks whether a credentialed browser request was intentionally made
  from the application; and
- authorization asks whether that user may perform this action on this
  record.

A valid CSRF token never replaces a guard or a permission check.

## 3. The implemented Events layers

Every non-GET Citry Events request passes the following layers.

### 3.1 Always-on Citry floor

For JSON bodies, the request must carry the `X-Citry-Events` header. Citry's
browser client sends the value `1`; the server currently checks header
presence, not that exact value. A plain HTML form cannot add that custom
header, and cross-origin JavaScript normally triggers a CORS preflight before
it can send it.

When the browser supplies an `Origin` header, Citry compares its authority to
the request `Host`. When the browser supplies `Sec-Fetch-Site`, Citry accepts
only `same-origin` or `none`. This floor cannot be disabled by
`csrf=False`.

The Origin check is deliberately described as a cross-site request floor, not
an exact origin comparison. Citry's current host-neutral request record does
not carry the request scheme, so the implementation compares authority
(`host[:port]`) rather than scheme, host, and port together. Host middleware
remains responsible for its stronger origin policy.

### 3.2 Host middleware

Django Events routes are ordinary views under `CsrfViewMiddleware`. Citry
does not mark them `csrf_exempt`, and a component setting cannot bypass the
middleware because it runs before Citry resolves a handler.

FastAPI, Starlette, Flask, bare ASGI, and bare WSGI do not share one standard
CSRF token convention. An application that installs host middleware keeps
using its middleware and configures Citry's browser token carrier to match.

### 3.3 Per-handler Citry policy

`Events._csrf` and `@event(csrf=...)` control an optional Citry-side callable:

- `"auto"` adds no second Citry token check. The host middleware and the
  always-on floor still apply.
- a callable receives the neutral Citry request and raises to reject;
- `False` disables only that optional callable layer.

The callable is useful for a host without middleware or for an application
with a custom double-submit or header token convention. It should not
duplicate Django's middleware merely for symmetry.

### 3.4 GET handlers

GET handlers are exempt from CSRF checks because safe HTTP methods must not
change server state. Citry enforces the declared method but cannot prove that
the Python handler body is side-effect free. A GET event is therefore a
developer contract: expose only reads.

## 4. Django recipes

### 4.1 Default readable CSRF cookie

Keep `CsrfViewMiddleware` enabled. Citry's browser runtime reads Django's
default `csrftoken` cookie and sends it as `X-CSRFToken` on Events requests.
No component-specific wiring is required.

```python
MIDDLEWARE = [
    # ...
    "django.middleware.csrf.CsrfViewMiddleware",
    # ...
]
```

The Events request still uses `credentials: "same-origin"`, so the session
cookie and CSRF cookie follow normal browser cookie rules.

### 4.2 Session-backed or HttpOnly CSRF cookie

When `CSRF_USE_SESSIONS=True` or `CSRF_COOKIE_HTTPONLY=True`, browser
JavaScript cannot read the token cookie. Ask Django for the masked form token,
pass it into the Citry component, and expose it in a hidden input:

```python
from django.http import HttpResponse
from django.middleware.csrf import get_token


def profile(request):
    html = ProfilePage(csrf_token=get_token(request)).render().serialize()
    return HttpResponse(html)
```

```citry-html
<input
  type="hidden"
  name="csrfmiddlewaretoken"
  c-value="csrf_token"
>
```

Configure the Citry Events client before it sends a request:

```javascript
Citry.events.configure({
  csrf: {
    token: () => document.querySelector(
      '[name="csrfmiddlewaretoken"]',
    ).value,
  },
});
```

Citry templates intentionally do not interpret Django's
`{% csrf_token %}` template tag. Component context isolation must not be
weakened to make a host context processor appear ambiently. The masked token
is an explicit component input.

### 4.3 Native Django form post

A native `<form method="post">` does not use Citry's browser runtime or JSON
envelope and cannot attach the `X-Citry-Events` header. The example below posts
to an ordinary host route, so put Django's masked token in the expected hidden
field:

```citry-html
<form method="post" action="/profile/">
  <input
    type="hidden"
    name="csrfmiddlewaretoken"
    c-value="csrf_token"
  >
  <!-- fields -->
</form>
```

The host validates that request exactly as it validates any other native form.
The same hidden input can serve both native forms and the token function in
section 4.2.

A native form may instead target Citry's per-event form-compatibility route.
It still cannot send the custom Events header, so the host token, Origin and
Fetch Metadata checks, and the event route's form decoding remain the relevant
layers.

## 5. Custom host token

Tell the browser where to read the token and which header to send:

```javascript
Citry.events.configure({
  csrf: {
    cookie: "app_csrf",
    header: "X-CSRF-Token",
  },
});
```

For a meta element, hidden input, or in-memory source, provide a string or a
zero-argument function instead of `cookie`:

```javascript
Citry.events.configure({
  csrf: {
    token: () => document.querySelector(
      'meta[name="csrf-token"]',
    ).content,
    header: "X-CSRF-Token",
  },
});
```

If the host does not validate that header before dispatch, add a Citry-side
callable:

```python
from citry.ext.events import EventError


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
```

Token comparison, expiry, rotation, and storage are application concerns.
The callable should use a constant-time comparison where the token design
requires it and should avoid logging secrets.

## 6. When `csrf=False` is appropriate

An event authenticated entirely by an explicit bearer credential may not need
an additional Citry-side CSRF token callable:

```python
from citry.ext.events import event


class Callback(Component):
    class Events:
        @event(csrf=False)
        def receive(self, request):
            verify_bearer_token(request)
```

This setting does not:

- disable the `X-Citry-Events`, Origin, or Fetch Metadata floor;
- exempt a Django route from `CsrfViewMiddleware`;
- remove browser token attachment; or
- replace authentication and authorization inside the handler.

The name is narrower than it first appears: it opts out of Citry's optional
callable, not all CSRF protection surrounding the route.

## 7. Upstream problem and Citry answer

Three django-components reports exposed two distinct jobs:

- [issue #12](https://github.com/django-components/django-components/issues/12)
  reported a Django CSRF tag disappearing inside component HTML;
- [issue #909](https://github.com/django-components/django-components/issues/909)
  showed isolated component context dropping processor values such as
  `csrf_token`; and
- [discussion #441](https://github.com/django-components/django-components/discussions/441)
  required separate token-header setup for client-triggered requests.

Citry keeps component isolation and addresses the jobs separately:

1. native forms receive the host token as an explicit input and render the
   host's hidden field; and
2. the Events runtime attaches the configured token to requests it owns.

This avoids ambient context leakage without asking every event binding to
repeat token plumbing.

## 8. Ownership matrix

| Concern | Host | Citry | Component author |
|---|---|---|---|
| Generate, rotate, store, and validate token | Owns | Does not duplicate | Does not invent |
| Cookies, SameSite, trusted origins, and proxy setup | Owns | Preserves browser behavior | Does not override locally |
| Events custom header and Fetch credentials | Configures convention | Owns transport | Normally no work |
| Non-GET cross-site request floor | May add stronger checks | Owns and keeps enabled | Cannot disable |
| Native form hidden field | Supplies token | Renders explicit input | Declares the input and field |
| Optional custom callable | Defines policy | Invokes after floor | Selects component or handler scope |
| Authentication and authorization | Supplies identity and policy | Exposes request and guards | Checks every action and record |

## 9. Known limits and future work

- The current Citry Origin floor compares authority to `Host`, not a complete
  origin tuple. Host middleware should remain authoritative.
- Citry cannot prove that a GET handler is read-only.
- The checker and VS Code extension could add a low-confidence warning for a
  GET handler whose Python AST contains mutation-sounding calls. This must use
  a real Python parser, potentially Ruff's parser if Citry adopts it, rather
  than regular expressions. Calls named `delete_items()`, `mutate_x()`,
  `change_y()`, `create_record()`, `save()`, `update()`, `insert()`,
  `commit()`, or similar would produce an advisory finding at the call site.
  The rule must remain a warning with an explicit suppression because names
  can mislead, indirect calls can hide mutations, and a linter cannot prove
  absence of side effects. It is an early-feedback aid, not part of the CSRF
  guarantee.
- A host layout or third-party JavaScript can still make requests outside the
  Citry runtime; those calls must follow the host's normal CSRF convention.
- WebSocket handshakes and future transports need their own origin and
  credential review. This document covers the shipped HTTP Events transport.
- CORS is not CSRF protection by itself. Keep state-changing routes protected
  even when cross-origin reads are disallowed.

## 10. Implemented acceptance evidence

The shipped contract is covered by focused Events route and Django integration
tests, including the custom header, Origin and Fetch Metadata checks, Django
middleware without `csrf_exempt`, default cookie/header wiring, custom token
sources, callable policy, and the limited effect of `csrf=False`.

The landing page may accurately say that Citry preserves host CSRF protection
and wires the requests it owns. It must not say that Citry supplies a universal
token scheme, authentication, or complete application security.

## 11. References

- [Django CSRF reference](https://docs.djangoproject.com/en/6.0/ref/csrf/)
- [Django security guide](https://docs.djangoproject.com/en/6.0/topics/security/)
- [`citry.ext.events.csrf`](../../packages/py/citry/citry/ext/events/csrf.py)
- [Events browser transport](../../packages/js/citry-client/src/citry-events.ts)
- [Public Citry security guide](../../docs_site/content/security.md)
