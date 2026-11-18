# Checks in the Vue fragment loader (GHSA-3x88)

- **Advisory:**
  [GHSA-3x88-p9rc-qjw6](https://github.com/citry-dev/citry/security/advisories/GHSA-3x88-p9rc-qjw6),
  published 2026-11-18, severity medium (CVSS 3.1 score 4.7)
- **Affected and fixed versions:** `citry >= 0.6.0, < 1.0.1` (the nonce
  case from 0.7.0); fixed in 1.0.1
- **Fix:** `9bf0c83c2`, committed to `main` 2026-11-18, for issue
  [#720](https://github.com/citry-dev/citry/issues/720). Citry's browser
  code starts a fragment only when both its tag and its JSON data carry
  the page's nonce. On a page whose Citry script has no nonce, it starts
  a fragment found in the page only when every script it names is a file
  Citry serves from the page's own origin and path, its server events
  and message requests go to Citry's own routes, and it mounts into the
  element Citry wrote for it. Scripts and stylesheets that Citry's
  browser code adds now resolve against the page's address, not a
  `<base>` tag.
- **Reviewer:** separate reviewing agents in three rounds, each with a
  technical and security review in three browser engines, an
  advisory-survey check and a prose pass
- **Code:** `installFragmentManager` in
  `packages/js/citry-client/src/citry-fragments.ts`; the URL and host
  checks in `packages/py/citry/citry/_vue/client.js` (built into
  `_vue/fragments.js` and `_vue/runtime.js`); `_preloader_script` in
  `packages/py/citry/citry/ext/dependencies/emission.py`; tests in
  `packages/py/citry/tests/e2e/test_fragment_without_nonce_e2e.py`,
  `tests/e2e/test_fragment_nonce_e2e.py` and
  `packages/js/citry-client/test/fragment-nonce.test.mjs`

## Who controls the input

A Vue fragment is a piece of Vue-rendered HTML that arrives after the
page loads, such as an Events `Render` answer. Citry's browser code finds
the fragment's JSON data block in the page and starts it: it loads the
scripts the block names, sends server events where the block says, and
mounts the fragment into an element.

The data block should only ever come from the server. The advisory shows
that HTML injected into the page could write one:

- **On a page with a nonce-based CSP** (a nonce is a random value the
  server puts on each script the policy allows), Citry checked only the
  tag's nonce. Injected markup could make the browser give a genuine
  tag's nonce to a tag the attacker wrote, so Citry loaded scripts from
  any address under the page's policy.
- **On a page without a nonce,** Citry started every block it found.

The inputs, by who first supplies them:

- **The data block.** Citry's server writes it. An attacker who can
  already inject HTML into the page could write one too. The fix does not
  remove that injection; it stops Citry's browser code from turning it
  into scripts that the page's policy would otherwise block.
- **Data passed to `Citry.fragments.load()`.** The app's own script
  supplies it, and the docs mark it as author-only: pass only data your
  own server wrote.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches "JavaScript and JSON", "Embedded documents"
(`srcdoc` frames), "Markers for Citry's browser code", "Addresses and keys the browser code takes from the server",
"Element `id` and `name`" and "The CSP nonce".

## How it was checked

- **Browsers.** Chromium 159, Firefox 159 and WebKit 27.2 through
  Playwright 1.65.2. A page counted as a hit when a script it should not
  load ran, or a request it should not send arrived.
- **Releases.** 1.0.0 (with `citry-core` 2.1.0) was run in the browsers.
  0.5.0 to 0.9.0 were read from the release tags: 0.5.x has no fragment
  loader, 0.6.0 starts every block, and 0.7.0 adds the nonce check.
- **Policies.** No CSP, `script-src 'self'`, a hash-based policy with
  `'strict-dynamic'` that allows Citry's script by its hash, and a
  nonce-based policy.
- **Routes.** Markup the server renders before the data block, markup
  the page's own code inserts later, the document's configuration block,
  the fragment preloader, Events `Render` answers, documents in `srcdoc`
  frames, and `Citry.fragments.load()`.
- **Kinds of input.** Injected tags that try to take a genuine tag's
  attributes; script, event and message URLs that name another origin or
  scheme, or try to leave Citry's path through encodings, case changes
  or credentials; injected `<base>` tags at several moments of the load;
  a second or renamed copy of Citry's script, or one hosted elsewhere;
  elements whose `id` or `name` hides a `document` member; forged mount
  targets; and served-file names and paths a visitor might choose.
- **Size.** The review tests grew from 36 per engine in the first round
  to 235 in the last, including 52 path cases per engine across the four
  policies. The new end-to-end file has 83 tests per engine.
- **Tests that catch the old code.** In the second round, 33 of that
  file's then 40 tests failed against the released script, and 10 failed
  against the first version of the fix.
- **Test runs on the third version of the fix** (the fourth changed only
  text). Node tests in
  `packages/js/citry-client`: 346 of 348 pass; the two failures are Vue
  version checks caused by a local package mismatch. `tsc --noEmit`
  passes. The browser end-to-end suite in three engines: 1,835 pass and 8
  fail, and each of the 8 also fails on `main`. Python unit tests: 13,622
  pass, with 2 failures that `main` has too.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked these kinds: script loading (`script-load`),
  data accepted as trusted because of its shape (`trusted-shape`), DOM
  clobbering (`dom-clobber`), URLs (`xss-url`, `client-url`), CSRF and
  CSRF token leaks (`csrf`, `xsrf-leak`), open redirects
  (`open-redirect`), hydration (`hydration`), translated messages
  (`i18n-xss`), and path traversal and path access
  (`path-trav`, `path-authz`).

## Ruled out

- **A nonce taken from a genuine tag.** A block needs the nonce in its
  JSON as well as on its tag, and `serialize(csp_nonce=...)` writes both
  (`test_injected_tag_that_takes_a_genuine_nonce_through_a_repeated_attribute_does_not_run`).
- **A block that chooses its scripts or calls on a page without a
  nonce.** Script, definition, served-file, event and message URLs
  outside Citry's routes are refused
  (`test_injected_fragment_on_a_page_without_a_nonce_cannot_choose_its_scripts`,
  `test_definition_url_outside_citrys_routes_is_refused`,
  `test_events_endpoint_outside_citrys_routes_is_refused`,
  `test_forged_i18n_messages_url_is_refused`). A block that sets its own
  CSRF options is refused.
- **An injected `<base>` that moves a file.** Citry resolves its URLs
  against the page's address, also when the `<base>` arrives between the
  check and the load
  (`test_base_inserted_between_the_check_and_the_load_moves_nothing`).
- **Another copy of Citry's script choosing the origin.** A second
  script tag, or a copy hosted on another site and allowed by its hash,
  cannot make Citry accept files from another origin
  (`test_runtime_from_another_site_under_a_runtime_hash_policy_does_not_move_the_prefix`).
  A copy that injected markup runs can still choose the directory on the
  page's own origin; the follow-ups below list this limit.
- **Named elements.** An element whose `id` or `name` matches a
  `document` member does not change the URL Citry reads
  (`test_named_elements_do_not_hide_the_runtime_url`).
- **Mounting into other content.** A forged block cannot choose its mount
  element, and an earlier element with the host's `id` does not win
  (`test_forged_fragment_cannot_mount_into_other_page_content`).
- **Breaking real setups.** Fetched fragments, a site under a sub-path, a
  CDN that serves only Citry's script at its usual path,
  `local_files="serve"` and the i18n locale switch still work.

## Fixed during the review

- The first round found that the first version refused real fragments
  with `local_files="serve"` and behind a CDN; left the message URL
  unchecked, so a request with the CSRF header could reach a same-site
  path of the attacker's choice; let a `<base>` added between the check
  and the load move a file; resolved URLs differently in the check and in
  the request; and let a forged block choose its mount element.
- The second round found that under the hash-based policy, a copy of
  Citry's script allowed by its hash, or a `<base>` placed before the
  preloader, set the path Citry accepts. It also found that the URL
  resolution Citry uses inside an `iframe srcdoc` document followed
  `<base>` without checking the origin, that upper-case
  hex digits in a served file name were accepted, that one existing browser test broke, and that the
  upgrade note had no workaround.
- Sweeps during the revisions found that Citry's check that a stylesheet
  loaded followed `<base>`, and that blocks could carry CSRF options. Both were fixed.
- The last round found only text problems, which were corrected. Those
  text edits got no further review pass.

## Not tested

- Safari, Edge and mobile browsers (only Playwright's builds were used).
- Any release other than 1.0.0 in a browser.
- htmx, Turbo, a real app's JSON block, and real Django CSRF middleware.
- A site where visitors upload files to a path they choose; this was
  only simulated.
- A server that decodes an encoded `?` or `#` in a path.
- Biome, `mypy`, `scripts/check.py`, and a rebuild with the pinned Vue
  3.5.44.

## Follow-ups

- Limits documented in `docs_site/content/security.md`,
  `docs_site/content/reference/browser-apis.md` ("Fragments"),
  `docs_site/content/advanced/html-fragments.md` and
  `docs/design/trust_boundaries.md`: on a page without a
  nonce, injected markup can still start the app's own components with
  data it chooses, and on a site where visitors can put files at a path
  they choose, it can load those files. A copy of Citry's script allowed
  by its hash, or an inline or renamed one, decides the path on the
  page's origin, and so does a copy that injected markup runs. Tags in the page's own HTML still follow `<base>`. A CDN
  that changes the path, and a fragment that names a `Script(url=...)`
  dependency, need a nonce-based CSP or `Citry.fragments.load()`. Pages
  that receive fragments should use a nonce-based CSP.
- No issue is open yet for passing a `Request` object to
  `csrfHeaders()`, or for checking the URL fields that other extensions
  add to a block.
