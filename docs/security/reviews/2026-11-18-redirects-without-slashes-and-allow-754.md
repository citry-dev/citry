# Redirects without slashes, and `Allow` on 405 (#754)

- **Pull request:** [#754](https://github.com/citry-dev/citry/pull/754),
  merged 2026-11-18 (8fd2e328a)
- **Reviewer:** a separate reviewing agent (security, the advisory
  survey and a prose pass), as the pull request description states. The
  pull request holds no report, comment or review thread. This record is
  built from the description, the merged change and its tests.
- **Code:** `_resolve_redirect_url` in
  `packages/py/citry/citry/ext/events/routes.py`;
  `route_allowed_methods` in `packages/py/citry/citry/util/routing.py`
  and its callers in the ASGI, WSGI and Django adapters
  (`packages/py/citry/citry/contrib/asgi.py`, `wsgi.py`, `django.py`);
  `framework_base` in `packages/py/citry/citry/ext/events/handlers.py`,
  applied to `ViewEvents` in `view_events.py`. Tests:
  `test_events_routes.py`, `test_events_view_events.py`,
  `test_route_path_rules.py` and `test_url_scheme_readers.py`, all under
  `packages/py/citry/tests/`

## Who controls the input

The change touches three things:

- **The `Redirect` URL on the no-JavaScript form path.** An Events
  handler returns `actions.Redirect(url)`. The app's Python code chooses
  the URL, and it may contain request data. With JavaScript, Citry's
  browser code resolves the URL against the page. Without JavaScript,
  `_resolve_redirect_url` turns it into the `Location` header of a 303
  answer, and the browser resolves that header against the handler's
  URL. A URL such as `http:next` on an `http:` page is relative to the
  browser, and it now resolves against a same-host `Referer` (the
  request header that names the page the visitor came from), as other
  relative URLs already did. A URL with a `/` or `\` right after the
  colon, or one whose scheme differs from the page's, goes out
  unchanged. The browser navigates to the result.
- **The `Allow` header on a 405 answer.** The route table that the app
  author writes decides the methods. Anyone can send a request with
  another method. The ASGI and WSGI adapters now name the accepted
  methods in an `Allow` header, and every adapter, Django included, names
  `HEAD` wherever the route accepts `GET`.
- **Which methods become handlers.** Every public method on an `Events`
  class becomes a handler that any request can call by name. Citry's own
  `ViewEvents` base class is now skipped like `Events`. It has no public
  method today, so nothing changes now. A helper added to it later will
  not become a handler on every subclass.

Of the places in the list of where values reach the browser (Mechanism 7
in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "Navigation" (`Redirect` and the `Location` header
on the no-JavaScript form path) and "Responses Citry serves".

## How it was checked

- **Code read and focused tests.** The reviewer read the change with a
  security brief for navigation and for the responses Citry serves. The
  author ran the redirect, scheme reader, Events routes, route path
  rules, `ViewEvents`, Django, host adapter and host parity tests with
  the published `citry-core` 2.1.1 wheel: 732 passed.
- **New tests fail without the fix.** The author checked that each new
  test fails on `main` for the expected reason: the old `Location`, no
  `Allow` header, no `HEAD` in the list, and the helper becoming a
  handler.
- **URL forms that parsers read differently.** New tests fix the
  expected `Location` for URL forms that browsers and URL parsers can
  read with different hosts, such as a backslash, credentials, a scheme
  without `//`, and escaped or full-width slashes. Each `Location` keeps
  the URL the app returned, with non-ASCII characters percent-encoded,
  or resolves it against the page where the browser would read it as
  relative.
- **The browser's reading, through Node.** Node's `URL` class follows
  the URL standard that browsers use. For every case, resolving the
  `Location` against the handler's URL reached the same address as
  resolving the original URL against the page: 100 cases from the
  author and 500 from the reviewer, with no differences.
- **Other frameworks' advisories (Mechanism 8).** The reviewer checked
  these kinds from the maintainers' survey: open redirects, header
  injection, HTTP caching, and method and CSRF confusion. It found no
  hole.
- **Linters.** `ruff check`, `ruff format` and `mypy` on the touched
  modules (also with `--platform linux`) were clean, and the validator
  for `docs/design/trust_boundaries.md` passed.

## Ruled out

- **A redirect that lands somewhere the page's own browser code would
  not send it.** The no-JavaScript path now resolves the same relative
  forms the browser code resolves, and the Node comparison found no
  case where the two reach different addresses.
- **The server picking a host for a URL that parsers disagree on.**
  The server does not check hosts. It keeps the app's URL, or resolves
  it only where the browser would read it as relative, and the tests fix
  that output for each such form.
- **A `Referer` from another host steering the result.** Only a
  same-host `Referer` is used. With no `Referer`, or one from another
  host, the URL passes through unchanged, and for a method other than
  `GET` Citry logs a warning that names the fix. Tests cover a `Referer`
  with no path and one with a port. One case cannot be detected on the
  server: a `Referrer-Policy` that sends only the origin makes every
  page look like the site root. The docs ask such pages to redirect to
  a path that starts with `/`.
- **A future helper on `ViewEvents` becoming callable by request.**
  `ViewEvents` joins the classes that handler discovery skips, and a
  test adds a public method to it and checks that it is not a handler.

## Fixed during the review

- Wording in comments, docs and the changelog.
- New tests for a `Referer` with no path and with a port, and for the
  warning when there is no `Referer`.
- One stale code reference in a `trust_boundaries.md` row.

## Not tested

- **Real browsers.** No browser ran the redirects. Node's `URL` class
  stood in for the browser's URL parser.
- **The full repository gate.** Only the focused tests and linters
  above ran.

## Follow-ups

- [#769](https://github.com/citry-dev/citry/issues/769): tighten the
  Events CSRF origin check so that it also reads the scheme of the
  `Origin` header in one case. It is part of the release batch in
  [#776](https://github.com/citry-dev/citry/issues/776).
