# An http `Origin` on an https request (#865)

- **Pull request:** [#865](https://github.com/citry-dev/citry/pull/865),
  merged 2026-11-24 (32ad42230)
- **Reviewer:** a separate reviewing agent (technical, security,
  versioning and prose passes, and a check against the maintainers'
  survey of security advisories published for other frameworks, which
  `CLAUDE.md` calls Mechanism 8), then a separate agent that read the
  docs as a first-time reader would, as the pull request description
  states. The pull
  request holds no report, comment or review thread. This record is built
  from the description, the merged change and its tests.
- **Code:** `enforce_floor` in
  `packages/py/citry/citry/ext/events/csrf.py`; the new `scheme` field of
  `RouteRequest` in `packages/py/citry/citry/util/routing.py`, filled by
  `_build_request` in `packages/py/citry/citry/contrib/asgi.py`,
  `wsgi.py` and `django.py`, and by the preview host in
  `packages/py/citry/citry/ext/preview/host.py`. Tests, all under
  `packages/py/citry/tests/`: `test_events_origin_scheme.py`,
  `TestCsrfFloor` in `test_events_routes.py`, and
  `test_contrib_request.py`

## Who controls the input

Events is Citry's server events feature: the browser calls a Python
handler. For every call that is not a `GET`, Citry runs an always-on check
against cross-site request forgery (CSRF, where a page on another site
makes the visitor's browser send a call to the app). The check is
`enforce_floor`. It already required the host and port of the `Origin`
header to match the request's `Host`, and it refused a `Sec-Fetch-Site`
value (a header that browsers set to say where a request came from) other
than `same-origin` or `none`.

The change reads two inputs:

- **The `Origin` request header.** A browser sets it on a call from a
  page. A client that is not a browser can send any value. The check now
  also refuses an `Origin` that is not `https:` when the server reports
  that the call arrived over https. The risk is a plain-http page on the
  same host, which anyone on the network can rewrite, sending a call to an
  https app. Citry refuses such a call with a 403 `csrf_failed` answer.
- **The request's scheme.** The server reports it, and the app author's
  setup decides what it says. It is a new `scheme` field on
  `RouteRequest`, the object that each adapter (the code that connects
  Citry to ASGI, WSGI or Django) builds from a request. The ASGI adapter
  reads the scope's `scheme` (the ASGI default is `http`), the WSGI
  adapter reads `wsgi.url_scheme`, and the Django adapter reads
  `request.scheme`, which follows `SECURE_PROXY_SSL_HEADER`. Behind a
  proxy that handles https and passes plain http to the app, the app sees
  `http` unless its server reads the scheme the proxy forwards.

The contributor rules in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)
(Mechanism 7) keep a list of the places where a value can reach the
browser. The description names none of them. The change is about how
Citry's server reads a request that anyone can send.

## How it was checked

- **Review passes.** The reviewer ran a technical pass, a security pass, a
  check against the survey of other frameworks' advisories (Mechanism 8),
  a versioning pass and a prose pass. The description does not name the
  kinds of bug it picked from the survey. It says no hole was found.
- **The same call through three adapters.** `test_events_origin_scheme.py`
  sends one call through WSGI, ASGI and Django for every pairing of request
  scheme and `Origin` scheme: https with an http `Origin` (403), https with
  https (200), http with https (200, the proxy case), and http with http
  (200). It also covers Django with `SECURE_PROXY_SSL_HEADER`, a form posted
  without JavaScript from an http page (403), the `csrf_failed` error
  answer, and how the ASGI and WSGI adapters read and lowercase the scheme.
- **Unit cases.** `TestCsrfFloor` covers every pairing of schemes,
  uppercase values, a request with no `Origin`, and an `Origin` that
  `urlsplit` (Python's URL splitter) cannot parse.
- **New tests fail without the fix.** The description says the adapter,
  Django proxy and unit refusal tests fail on `main` before this change.
- **Checks run locally.** The focused Events, contrib, Django, route and
  preview host tests passed (2,677 before the review fixes, and the
  changed files again after them). Linters, mypy on macOS and with
  `--platform linux`, and `scripts/validate.py` also passed. The cargo
  phases did not run, because the change is Python only.
- **Versioning.** The new `RouteRequest.scheme` field has a default and
  comes last, so positional and keyword callers keep working. The
  description targets release 1.3.0. It says refusing these calls
  refuses requests that earlier releases accepted, which the versioning
  rules in `docs/codebase.md` ("Breaking changes") allow for a security
  tightening, and that the changelog entry says so.

## Ruled out

- **An http page on the same host calling an https app.** An https
  request with an `Origin` that is not `https:` is refused, including a
  form posted without JavaScript. The scheme comparison ignores case.
- **A proxy that handles https for the app (the app author's setup
  decides).** An http request accepts an `Origin` of either scheme, so a
  site served over https through such a proxy keeps working. The check
  runs only when the server reads the forwarded scheme (Django
  `SECURE_PROXY_SSL_HEADER`, Uvicorn `--forwarded-allow-ips`, Werkzeug
  `ProxyFix(x_proto=1)`). The new "Read the proxy's scheme"
  section of `docs_site/content/advanced/web-frameworks.md` tells them so,
  and `docs_site/content/security.md` states the rule.
- **An `Origin` that cannot be parsed.** `urlsplit` raises `ValueError`
  for a malformed IPv6 host. Citry now refuses it through the same 403
  path. The dispatcher already answered the error with `csrf_failed`, so
  only the log changes: it holds a one-line refusal reason and no
  traceback.
- **A request with an unknown scheme.** An empty `scheme` skips the
  scheme check. The description gives a hand-built
  `RouteRequest` as the case. The ASGI adapter falls back to `http`. The
  WSGI adapter reads `wsgi.url_scheme` and leaves `scheme` empty when the
  key is missing, which skips the check
  (`test_wsgi_adapter_reports_the_environ_scheme` covers the case).

## Fixed during the review

- A scheme comparison that was case-sensitive for hand-built requests.
- A missing test for a form posted from an http page, and missing tests
  for how the adapters read the scheme.
- A stale statement in `docs/design/security_csrf.md`, and stale line
  numbers in `docs/design/trust_boundaries.md`.
- Docs that did not say the check is skipped behind a proxy that handles
  https, unless the server reads the forwarded scheme.
- From a second prose pass: a wrong Uvicorn flag, a missing note on
  where Flask's `ProxyFix` goes, and an inaccurate code comment.

## Not tested

- **Real browsers.** The description says the exact `Sec-Fetch-Site`
  value each engine sends for an http page posting to an https page on
  the same host was not checked in a real browser. Citry refuses both
  `same-site` and `cross-site`.
- **Real proxy setups.** The tests set the scheme through the adapters
  and a Django `SECURE_PROXY_SSL_HEADER` setting. The description lists no
  test that runs Uvicorn with `--forwarded-allow-ips`, Werkzeug's
  `ProxyFix`, Flask or FastAPI. Flask and FastAPI reach the check through
  the WSGI and ASGI adapters.

## Follow-ups

No issue is open. The pull request closes
[#769](https://github.com/citry-dev/citry/issues/769). The pull request
documents two limits:

- A proxy that handles https hides the scheme from the check unless the
  server reads the forwarded scheme. See "Read the proxy's scheme" in
  [`web-frameworks.md`](../../../docs_site/content/advanced/web-frameworks.md).
- A site served to browsers over plain http while its server reports
  https fails every call that is not a `GET`. See "Fix an http Origin" on
  the same page.
