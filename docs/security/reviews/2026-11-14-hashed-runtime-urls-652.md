# Runtime files at URLs that hold their hash (#652)

- **Pull request:** [#652](https://github.com/citry-dev/citry/pull/652),
  merged 2026-11-14 (469b54855), for issue
  [#578](https://github.com/citry-dev/citry/issues/578)
- **Reviewer:** two independent reviews, as the pull request description
  records. The description gives their conclusion and the routes they
  covered, not how each one worked.
- **Code:** `packages/py/citry/citry/_hashed_runtime.py` (`HashedRuntime`,
  `is_content_digest`, `not_found`); the routes and links in
  `ext/dependencies/routes.py`, `ext/dependencies/emission.py`,
  `ext/i18n/emission.py`, `ext/i18n/routes.py` and `ext/events/routes.py`;
  the start script in `_vue/serialization.py`
  (`_start_script_for_mounted_page`); the 404 answers in `contrib/asgi.py`
  and `contrib/wsgi.py`; tests in `tests/test_hashed_runtime.py`,
  `tests/test_asset_cors.py`, `tests/test_vue_document_configuration.py`,
  `tests/test_deps_fragments.py`, `tests/test_sub_path_urls.py`,
  `tests/test_owned_file_integrity.py` and
  `tests/e2e/test_runtime_hashed_urls_e2e.py` (all under
  `packages/py/citry/`)

## Who controls the input

Citry's browser runtimes are the JavaScript files that start a page's
interactive parts. A page links a URL that holds the SHA-256 hash of the
file, such as `/citry/citry.<hash>.js`, and the server lets the browser
keep the file for a year. The fixed URLs still work, and carry `no-store`
(a header telling browsers not to keep a file).

- **The URL a page links** comes from Citry: the hash of the runtime file,
  the mount prefix (the path where the app mounts Citry's routes, which
  the app author's Python code sets), and, when the app is served below a
  sub-path such as `/shop`, that sub-path from the request. The
  sub-path is checked by `normalize_sub_path`, reviewed in
  [#479](2026-10-28-sub-path-urls-479.md). No template data chooses it.
  The browser runs the file at that URL, and the URL also appears in a
  preload hint (a tag that tells the browser to fetch the file early), in
  the script that starts the page, and in the loader for HTML fragments.
- **The hash in a request path** comes from anyone who can reach the
  server. It decides which file the server looks up.
- **A copy in the shared cache.** When the app sets `CitrySettings.cache`,
  each process writes the runtime it links to that cache for 30 days, so a
  worker on another version can answer for it during a rolling deploy. The
  cache backend belongs to the app, and anyone who can write to it
  controls those bytes.

What is at risk: the browser runs whatever a runtime URL returns, and a
miss answered with the wrong headers could be kept by a browser or CDN
(a caching server in front of the app).

## How it was checked

The pull request records two independent reviews that found no security
hole. They covered these routes (section 9 of
`docs/design/runtime_hashed_urls.md` lists more, named under "Not
tested"): the runtime URL in `<script src>`, the preload hint, the start
script and the fragment loader; `Citry.runtime_url()`; the hash in the
path; the shared-cache entry; and the `404` answer with its CORS header
(CORS is the browser rule that decides whether one site may read a
response from another).

The record is built from that description, the merged change and its
tests. The tests that bear on security:

- **Unit tests** (`test_hashed_runtime.py`, `test_asset_cors.py`) send each
  runtime route through the route table (the list of URL patterns) and
  through the WSGI and ASGI apps (Citry's adapters for two Python server
  standards), with and without a shared cache. They use a recording cache
  backend that logs every key it is asked for.
- **Start script tests** (`test_vue_document_configuration.py`) lock the
  script's exact text and render it with mount prefixes that hold a
  backslash, a line-separator character, or markup that could end a script
  early.
- **Browser tests** (`test_runtime_hashed_urls_e2e.py`, with
  `test_fragment_e2e.py` and `test_base_element_e2e.py`) ran on Chromium,
  Firefox and WebKit: 58 passed and 2 skipped (the prerender test runs on Chromium only), as
  the description reports.
  They run a real WSGI server that logs each request, so the tests count
  what reached the server.

## Ruled out

- **Data choosing the runtime URL.** The URL is the file's hash plus the
  prefix and sub-path above. The start script writes it as a JSON string
  that is only printed by `console.error`. The fragment loader writes it
  as JSON with `<` escaped. The start script tests use prefixes with a
  backslash, a line separator and script-ending markup, and the loader
  test uses a prefix with a quote. Each reads back exactly the URL the
  page links.
- **Wrong bytes under a hash.** A copy from the shared cache is served only
  when its SHA-256 equals the hash in the URL. A mismatch is a miss, and
  the entry is deleted
  (`test_a_stored_copy_whose_bytes_do_not_match_its_hash_is_a_miss_and_is_removed`).
  Each runtime reads only its own cache key prefix, so a copy stored for
  one runtime is not served as the other.
- **A cache key built from request data.** The server checks that the hash
  is 64 lowercase hex characters before it builds a key. For upper case,
  wrong length, non-hex, dash and empty values, the test shows the cache
  backend is never asked. A path with an extra dot matches no route,
  because the route's hash segment (`digest`) never holds a dot.
- **A browser or CDN keeping a 404.** Every `404` from these routes sends
  `Cache-Control: no-store`, with an empty body that does not repeat the
  path. That holds for a hash the worker lacks, for a malformed hash, for
  `HEAD` requests (which ask for headers only), and for the Events
  definition and stylesheet routes.
  The WSGI and ASGI apps send `no-store` on a path that matches no route,
  because that path may gain a route after a deploy. Tests use both apps.
- **The CORS header on a `404`.** Any site can read whether a given
  runtime hash exists on this server. That is by design: only answers
  about public files may carry the header. Pages load the runtime with
  `crossorigin` and `integrity` (the browser checks the file's hash
  against `integrity` only on a response it may read), and a sandboxed
  frame counts every request as cross-origin. Without
  `Access-Control-Allow-Origin: *` on the `404`, the console would show a
  CORS error that hides the missing file.
- **The header on other routes.** `not_found()` is the one function that
  builds these answers. The wildcard stays off the routes that run events,
  read the request body or answer a path with no route
  (`test_request_routes_do_not_send_a_cors_header`,
  `test_a_path_that_matches_no_route_is_a_404_that_nothing_keeps`). The
  public file responses carry no `Access-Control-Allow-Credentials` and
  no `Vary`.
- **The console in a sandboxed frame.** With no origin, the browser test
  finds no CORS message in the console on Chromium and WebKit
  (`test_a_sandboxed_frame_with_no_origin_reports_a_missing_runtime_once`).
- **Page markup taking over Citry's window names.** An element with the id
  `__citryRuntime` is readable as `window.__citryRuntime`. The start script
  reads both of its names with `hasOwnProperty`, which an element id never
  satisfies. A browser test adds such elements and checks the outcome is
  the same whether the runtime loads or not.
- **The missing-runtime message causing other effects.** On a mounted
  page the start script starts the app when the runtime loaded. Otherwise
  it writes one console error and keeps the server HTML. Browser tests
  check that it sends no request of its own, does not navigate or reload,
  and stores nothing in `sessionStorage`. Two apps on one page report
  once. The script holds no page data, so its CSP hash (the hash a
  Content Security Policy uses to allow one inline script) depends only on
  the app id and the URL. It appears in `csp_script_hashes`, and it
  carries the CSP nonce (the per-page token that does the same job).
- **An old page open across a deploy.** The browser test for the back
  button upgrades the runtime on the server between two pages and checks
  that the first page still runs the runtime its own HTML names, with
  `integrity` off and on. Tags for the hashed URL carry `integrity`
  (`test_owned_file_integrity.py`).
- **The stable URLs.** `citry.js`, `ext/events/runtime.js` and
  `ext/i18n/runtime.js` serve the same bytes as the hashed URL with
  `no-store` and the same CORS header.

## Fixed during the review

The description says the reviews led to these fixes before the merge, and
names no security hole among them: a leftover sentence about a reload check
in the design document, a stale reason for the CORS header in the Events
spec, a troubleshooting row that matched on `Uncaught Error`, a dropped
`citry.js` `404` row, the cases for a stale `citry.js`, and wording in the
changelog and docs.

## Not tested

- **The advisory survey check** (Mechanism 8 in `CLAUDE.md`) is not
  recorded as done. The description says the second reviewer could not
  open the survey.
- **The full repository gate and Biome** (the JavaScript linter) were not
  run locally, as the description says.
- **One focused test**,
  `test_javascript_delivery_policy_sees_client_i18n_and_can_omit_it` in
  `test_i18n_client.py`, failed in the author's run because the local
  `citry_core` build was older than `main`. The description says it fails
  the same way before this change.
- **Routes the description does not name.** Section 9 also lists an Events
  `Render` result, cached renders, and the `security_csp`,
  `security_javascript` and `security_script_integrity` output checks.
  The description names none.
- **A real shared cache and a real rolling deploy.** The tests use an
  in-memory recording backend, and the browser test plays the upgraded
  worker from the server side.
- **A CDN that keeps `404` answers for a fixed time.** It ignores
  `no-store`. The docs page `docs_site/content/advanced/web-frameworks.md`
  ("Stop CDNs caching 404s") names that setting, and no test uses a CDN.
- **Django.** Its unmatched-path `404` is Django's own, as the Events
  spec says. The tests send the hashed routes through the WSGI and ASGI
  apps and the route table, not through the Django adapter.
- **Firefox on the console wording.** Firefox words a blocked script as a
  CORS failure even when the header is present, so that one check is
  skipped there. The prerender test (it loads a page in the background)
  runs on Chromium only and does not run a script started inside a
  prerendered page.
- **Docs site, snapshots and playground.** The change also updates
  `docs_site/_internal/static_deps.py`, `assemble.py` and the playground
  preview. No separate security check of them is on file.

## Follow-ups

- [#665](https://github.com/citry-dev/citry/issues/665): reload a page
  automatically when its runtime is gone after a deploy, left for after
  1.0.0.
- [#645](https://github.com/citry-dev/citry/issues/645) (found while
  working on this change): a single quote in the mount prefix makes Vue
  pages fail to render with an error.
