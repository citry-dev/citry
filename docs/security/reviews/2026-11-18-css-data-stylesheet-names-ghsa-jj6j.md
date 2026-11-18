# Secret-based names for `css_data()` stylesheets (GHSA-jj6j)

- **Advisory:**
  [GHSA-jj6j-m5j4-2vpm](https://github.com/citry-dev/citry/security/advisories/GHSA-jj6j-m5j4-2vpm),
  published 2026-11-18, severity low (CVSS 3.1 score 3.7)
- **Affected and fixed versions:** `citry >= 0.1.0, < 1.0.1`; fixed in
  1.0.1
- **Fix:** `53978fa24`, committed to `main` 2026-11-18. Citry builds the
  `css_data()` stylesheet URL from the values and a key taken from the
  `secret` setting (or, with no `secret` and no configured cache, a key
  made at random once per process). It never serves a `js_data()` script
  from the cache, and it refuses and deletes a stylesheet entry left in a
  shared cache without this release's key. Two public changes in the
  same release harden the same routes: `4ab759b28` checks the shape of
  cache keys that come from requests, and `598f5bbe6` leaves `secret`
  out of the settings `repr`.
- **Reviewer:** separate reviewing agents in three rounds, each with a
  technical, security and advisory-survey pass; prose passes in the first
  two rounds, and a separate prose and first-time-reader pass after the
  third
- **Code:** in `packages/py/citry/citry/`, `ext/dependencies/scripts.py`
  (`_css_data_key`, `_css_data_hash`, `get_script`,
  `_read_css_data_stylesheet`, `check_css_data_stylesheet_copy`),
  `ext/dependencies/routes.py`, `ext/dependencies/extension.py`,
  `_vue/events.py` (`_load_asset`) and the `secret` docstring in
  `settings.py`; tests in `packages/py/citry/tests/`
  (`test_css_data_stylesheet_names.py`,
  `test_css_data_stylesheet_keys.py`, `test_css_data_refusals.py`, and
  `test_cache_keys_from_requests.py` for `4ab759b28`)

## Who controls the input

A component's `css_data()` returns values that Citry writes into a small
stylesheet of CSS custom properties. Citry serves that stylesheet at a URL
named after a hash of the values. Since 0.6.0 an interactive page also
gets a copy at a URL named after the hash of the stylesheet's bytes.
Neither hash used a secret, so anyone who guessed the values could work
out the URL and ask for it. A stylesheet answer meant that some visitor's
page had used those values.

In 0.1.0 to 0.5.1, Citry also kept every `js_data()` result in its cache
with no expiry and served it at a URL built the same way. Later releases
stopped writing these entries but still served one that an earlier
release had left in a shared cache. In 0.1.0 and 0.2.0 the names were
short enough to try every one.

The inputs, by who first supplies them:

- **The `css_data()` and `js_data()` values.** The app's Python code
  returns them, and they often come from stored data about a visitor: a
  progress percentage, a plan name, a colour from a short list. A value
  that only the template author writes, or that is the same for every
  visitor, tells someone who guesses nothing new.
- **The requested URL.** Anyone can send it, with no session, and from
  another site through a visitor's browser, because these answers carry
  `Access-Control-Allow-Origin: *`. Nothing runs in the browser; the
  risk is that the answer confirms a guess.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches "CSS", "Responses Citry serves" and "CORS headers".

## How it was checked

- **Releases.** 1.0.0 was run. 0.1.0 to 0.9.0 were read from the release
  tags. Cache entries in the formats of older releases were written by
  hand. In one run, the released 1.0.0 rendered pages into a shared cache
  and the fixed code read that cache back.
- **Hosts and caches.** CPython 3.14 and 3.15, Django 6.1.3. Raw WSGI
  (`wsgiref`), Flask, Django's WSGI handler, FastAPI on uvicorn and
  Citry's ASGI adapter. Citry's in-process cache, Django's local-memory
  and memcached backends (key checks only, without a running server), a
  stand-in for Redis, and DiskCache 5.6.3.
- **Browsers.** On 1.0.0, a page on another origin sent guesses through
  Chromium 159, Firefox 159 and WebKit 27.2 (Playwright builds) and could
  tell a hit from a miss. The last round repeated the cross-site check in
  Chrome against the version of the fix before its final change to cache
  reads.
- **Kinds of input.** Guessed values for one component; entries left by
  each earlier release; names made with a secret the worker does not
  hold; entries that are not JSON; unknown class ids; keys and file
  names that are too long, hold spaces or control characters, or are not
  ASCII; and about 20 unusual file extensions.
- **Response time.** 2,000 interleaved samples per case, with a simulated
  delay of 0 or 200 µs per cache call, compared refused names with plain
  misses.
- **Tests.** In the second round, 22 of the 31 route tests failed on
  1.0.0. The whole Python
  suite without browser tests passed (13,890), apart from 2 failures and
  2 errors that `main` also has. `ruff`, and `mypy` on macOS and with
  `--platform linux`, passed.
- **Mutation checks.** Removing any of the cache reads that make a
  refusal cost the same as a miss, or any of the deletions, makes a test
  that a refusal costs the same as a miss fail. Restoring the old file-extension rule, or
  replacing the stylesheet-copy check with a stub, makes its test fail.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked these kinds: cache keys and cache entries
  shared between users (`cache-key`, `cache-http`, `cache-xuser`),
  timing leaks of secrets (`secret-timing`), server data reaching the
  client (`source-exposure`), error pages (`error-page`), header and log
  injection (`header-inj`, `log-inj`), server data written into the page
  (`ssr-serialize`), resource use and crashes (`dos-amplify`,
  `dos-crash`), path traversal (`path-trav`), slow regular expressions
  (`redos`) and raw-text elements (`xss-rawtext`).

## Ruled out

- **Confirming a guess through either URL.** Both names now need the key
  (`test_a_guessed_value_cannot_be_confirmed_through_the_stylesheet_url`,
  `test_the_vue_stylesheet_url_cannot_be_computed_from_a_guessed_value`).
- **Serving an entry from an earlier release.** A stored `js_data()`
  script is never served, and a stylesheet without this release's key is
  a miss
  (`test_a_js_data_script_left_in_a_shared_cache_by_an_older_release_is_not_served`,
  `test_an_unreadable_leftover_stylesheet_entry_is_a_miss`).
- **Telling a refused name from a miss by response time.** A refused name
  does the same cache work as a miss, and a cache that refuses deletes
  still answers 404
  (`test_every_refused_stylesheet_name_does_the_same_cache_work_as_a_miss`,
  `test_a_cache_that_refuses_deletes_still_answers_404`).
- **App code handing out the key.** The key is built so that app code
  that signs text with the raw `secret` does not produce it
  (`test_app_code_that_signs_the_label_with_the_raw_secret_does_not_hand_out_the_key`).
- **One visitor's stylesheet shown to another.** The route rebuilds the
  stylesheet from the stored values and checks its name before serving
  it, so the `integrity` value still matches.
- **Listing component classes.** An unknown class and a miss give the
  same 404.
- **Server errors from malformed keys.** A State token, `cache/` or
  `asset/` URL of the wrong shape is refused before it reaches the cache
  (`test_a_server_token_key_of_another_shape_is_refused_before_the_cache`).

## Fixed during the review

- The first round found that `js_data()` scripts left by older releases
  were still served; that the key was built in an order that app code
  could reproduce; that the asset-name check was too narrow; that tests
  imported private names; and that the docs lacked a CDN purge step.
- The second round found that a left-over entry could still be told
  apart by response time, that the order for rotating `secret` broke
  stylesheets on Vue pages, that some file names could not be reached
  under WSGI and Flask, and that a non-ASCII render-cache hash caused a
  server error.
- The third round found that the timing fix made every 404 write to the
  cache, which cut 404 throughput on DiskCache from about 60,000 to about
  1,500 per second, and that a cache that refuses writes then answered
  with a server error. The fix now pads a refusal with cache reads. Throughput was not
  measured again on the final code.

## Not tested

- Response time over a real network. Small CPU differences remain on the
  first request for a left-over entry and for renamed or removed classes
  until the old cache keys are deleted, as the advisory's upgrade steps
  require; whether they can be measured remotely is unproven.
- Real memcached, Redis and pylibmc servers, and eviction under memory
  pressure.
- Firefox and WebKit on the final code.
- The browser end-to-end tests, the docs build and `scripts/check.py`.

## Follow-ups

None open. These limits are documented in
`docs_site/content/advanced/js-and-css-dependencies.md` and
`docs_site/content/events/index.md`:

- With a configured `cache` and no `secret`, the URL stays a plain hash
  of the values and a guess can still be confirmed. Citry logs a warning
  in that setup.
- Workers that share a cache must all set `secret` or all leave it unset,
  and a `secret` is rotated in two deploys.
- After upgrading, apps with a shared cache must delete the old cache
  keys, and apps behind a CDN must purge `/cache/` and
  `/ext/events/assets/`.
