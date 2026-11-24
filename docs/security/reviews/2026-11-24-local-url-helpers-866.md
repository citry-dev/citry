# Helpers that keep a redirect on the site (#866)

- **Pull request:** [#866](https://github.com/citry-dev/citry/pull/866),
  merged 2026-11-24 (61e83a3ad)
- **Reviewer:** a separate reviewing agent (security, versioning and a
  prose pass, and a check against the maintainers' survey of security
  advisories published for other frameworks, which `CLAUDE.md` calls
  Mechanism 8), then a separate
  agent that read the docs as a first-time reader would, as the pull
  request description states.
  The pull request holds no report, comment or review thread. This record
  is built from the description, the merged change and its tests.
- **Code:** `is_local_url` and `local_url_or` in
  `packages/py/citry/citry/ext/events/local_urls.py` (new), exported from
  `citry.ext.events`; the URL scheme reader in
  `packages/py/citry/citry/_urls.py` that they share with `Redirect`;
  the `Redirect` docstring in
  `packages/py/citry/citry/ext/events/actions.py`. Tests:
  `test_events_local_urls.py` in `packages/py/citry/tests/`

## Who controls the input

An Events handler (Python code that the browser calls) can return
`actions.Redirect(url)` to send the visitor to another page. The change
adds two helpers that the app calls first, to check a URL it got from the
request:

```python
return actions.Redirect(local_url_or(data.next, "/"))
```

`is_local_url(url)` says whether a URL stays on the site.
`local_url_or(url, fallback)` returns the URL when it does, and the
fallback when it does not.


- **`url`.** The app passes it in. The description's own example is a
  `next` URL from the request, so request data supplies it. The helper
  accepts a relative URL, or an `http` or `https` URL on a host that the
  app lists. The browser then navigates to the URL that the app returns.
- **`allowed_hosts` and `require_https`.** These arguments name the hosts
  the helper accepts, and whether it refuses `http`. They are arguments of
  the call, so the app's code sets them.
- **`fallback`.** The URL `local_url_or()` returns when `url` is not
  local. The app's code sets it. `local_url_or()` checks it on every call
  and raises `ValueError` when it is not a local URL, so a bad fallback
  shows up in the first test.

Citry applies nothing here by itself: an app that does not call the
helper gets no new check. The risk is a helper that accepts a URL which a
browser loads from another site (an open redirect). The description does
not name a place from the list that the contributor rules in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)
(Mechanism 7) keep of the places where a value can reach the browser. The
helper exists for `actions.Redirect`, which that list calls
"Navigation".

## How it was checked

- **Compared with Django.** The helper follows Django's
  `url_has_allowed_host_and_scheme`, with some deliberate differences. The
  test table marks each one with `django_agrees=False`, and a test runs
  Django on every case to keep the table honest.
- **A browser run by the author** (a one-off script that is not in the
  repository). It built about 32,000 URLs from the test cases (short
  combinations of `/`, `\`, `:`, `@`, `https:`, hosts, spaces and
  full-width slashes) and 40,000 random token strings. For every URL the
  check accepts, with and without `allowed_hosts` and `require_https`, it
  resolved the URL with `new URL(url, base)` against an `https:` page and
  an `http:` page in Chromium 158, Firefox 159 and WebKit 27.2. It
  checked that each result is `http:` or `https:` on an allowed host, or
  the page's own host for a relative URL. The first run found one case:
  the check treated Unicode whitespace at the ends of a URL as strippable,
  as Django does, and Chromium reads such a URL as a host other than the
  one shown. The check now strips only ASCII spaces. After that fix, no
  URL leaked in any of the three browsers.
- **A browser run by the reviewer.** The reviewer tried about 48,000 more
  URLs (C1 control characters, Unicode case and dot lookalikes,
  full-width delimiters, lone surrogates, and percent-encoded dots and
  slashes) through both redirect paths in Chromium, Firefox and WebKit:
  `location.assign` with JavaScript, and the `Location` header that the
  server builds without JavaScript, including real 303 navigations. The
  description names no browser versions for this run. It says no URL that
  the helper accepts was loaded from another site.
- **Unusual arguments.** Entries such as `"*"` and `".shop.example"` in
  `allowed_hosts` match only themselves. None of the tried strings made
  the helper raise, and `Redirect` accepts every value that
  `local_url_or()` returns.
- **Tests.** `test_events_local_urls.py` holds the table of 93 URLs, the
  Django comparison, the error modes, and a test that `Redirect` accepts
  every URL the check passes. The existing Events actions, redirect
  scheme and routes tests pass.
- **Linters and docs.** `ruff check`, `ruff format --check` and mypy on
  `packages/py/citry/citry` (also with `--platform linux`),
  `scripts/validate.py`, the docs config tests and
  `python -m docs_site build-check` passed.
- **Other frameworks' advisories (Mechanism 8).** The reviewer ran the
  check against the maintainers' survey. The description does not name the
  kinds picked from it.
- **Versioning.** The change adds two public names and changes no
  existing behavior, so the description targets 1.3.0 as a minor-release
  feature. It notes that once the helper is released, its accept and
  refuse rules are behavior that the versioning rules protect, so a later
  tightening ships only as a security fix.

## Ruled out

The helper reads a URL as browsers do, following the WHATWG URL standard
that `location.assign()` and a `Location` header use.

- **A URL that a browser reads as another site.** The check refuses:
  - a control character anywhere in the URL (U+0000 to U+001F, U+007F and
    U+0080 to U+009F, including a tab or newline);
  - whitespace at either end other than ASCII spaces, which are the only
    characters the check strips;
  - a `\` that makes a browser read another host. The check reads `\` as
    `/`, so `\\host` and `/\host` name another host and are refused;
  - an `@` in the part of the URL that names the host, whether or not `\`
    is read as `/`;
  - an `http` or `https` URL that is not written as `scheme://host`, such
    as one with no `//` after the scheme or with extra slashes.
- **Host comparison.** The comparison lowercases ASCII letters only,
  because Unicode case mapping can differ from the mapping that browsers
  use for internationalized host names. It compares the rest as written,
  including the port, a trailing dot and the spelling of a non-ASCII host.
  `allowed_hosts` entries are literal.
- **A helper that hands `Redirect` a URL it raises on.** The helper
  refuses tabs and newlines because `Redirect` raises `ValueError` on them,
  and a test checks that `Redirect` accepts every URL the check passes.
  Django drops tabs and newlines and accepts the URL.
- **A long URL costing extra time.** The description says the check takes
  time in proportion to the URL's length and does no Unicode
  normalization, so it has no length limit like Django's 2,048
  characters.
- **An app that never calls the helper.** The app author's own code
  decides this. The pull request updates
  `docs_site/content/security.md` ("Check redirect URLs") and the warning
  in `docs_site/content/events/actions.md` to show `local_url_or()`, and
  the `Redirect` row of `docs/design/trust_boundaries.md` points at it.

## Fixed during the review

- C1 control characters in the middle of a URL passed the check, although
  the docs said "any control character". The check now refuses them.
- The docs' comparison with Django was corrected. The docs now say that
  `allowed_hosts` entries are literal, and spell out the fallback and
  port rules.
- A docs sentence said `is_local_url()` takes "the same arguments" as
  `local_url_or()`. That is wrong, because `is_local_url()` has no
  fallback. That reader caught it.
- The line numbers in the `Redirect` row of
  `docs/design/trust_boundaries.md` were refreshed.

## Not tested

- **Other browsers and versions.** The author's run used Chromium 158,
  Firefox 159 and WebKit 27.2. The description names no versions for the
  reviewer's run.
- **A rerun of the browser runs.** The author's script is not committed,
  so the roughly 72,000 URLs it built are not a test in the repository.
  The repository keeps the 93-URL table.

## Follow-ups

The description says the later `Redirect(url, same_host=True)` option from
[#568](https://github.com/citry-dev/citry/issues/568) changes the Events
protocol and is not part of this pull request. It names no issue for that
option.
