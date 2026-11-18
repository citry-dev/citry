# Refused redirects and the i18n configuration comparison (#756)

- **Pull request:** [#756](https://github.com/citry-dev/citry/pull/756),
  merged 2026-11-18 (0f7f679dc), closing issue
  [#660](https://github.com/citry-dev/citry/issues/660)
- **Reviewer:** a separate reviewing agent (security, a check against the
  maintainers' private survey of security bugs published for other
  frameworks, and a prose pass), as the pull request description states.
  The pull request holds no report, comment or review thread. This record
  is built from the description, the merged change and its tests.
- **Code:** `navigateToRedirect` and `csrfHeaders` in
  `packages/py/citry/citry/_vue/client.js`; `sameJsonContent` in
  `packages/js/citry-client/src/citry-i18n-core.ts`, called from
  `configureManifest` and `sameParsers` in `citry-i18n-runtime.ts` and
  from the artifact merge check (`artifactsAgree`) in `citry-i18n-vue.ts`.
  The built files `runtime.js` and `ext/i18n/client/vue-plugin.source.js`
  are rebuilt from these. Tests: `redirect-scheme.test.mjs`,
  `csrf-headers.test.mjs` and `i18n-configuration-order.test.mjs` under
  `packages/js/citry-client/test/`, and
  `packages/py/citry/tests/e2e/test_i18n_events_render_e2e.py`

## Who controls the input

The change touches three places in Citry's browser code:

- **Redirects passed to `Citry.events.applyActions()`.** The actions come
  from an Events result or from browser code the app author wrote. The
  browser code already refused to navigate to a URL with a scheme other
  than `http:` or `https:`, a value that is not a string, or a URL that
  leaves the page's origin. Now `navigateToRedirect` throws on such a URL,
  so the Promise that `applyActions()` returns rejects and the actions
  after the redirect do not run. Before, it logged an error and the
  Promise resolved. A redirect marked `wait: false` is still only logged.
  The server already refuses these redirects, so in an event call only the
  experimental `on_event_result` hook can produce one.
- **The URL passed to `csrfHeaders`.** Plugin code passes the URL. The
  browser plugin host (the experimental object Citry gives browser
  plugins) has a `csrfHeaders(url)` that gives plugin code the CSRF header
  for a URL on the page's own origin. It now reads only a string or a
  `URL` and gives `{}` for any other value.
- **The i18n configuration in an Events `Render`.** A `Render` of a region
  with `<c-i18n c-client>` sends the project's i18n configuration again.
  The app's Python code and its message files decide it. The runtime
  compared it with the page's copy as JSON text, so a different key order
  failed the call. It now compares formats by content (object keys as a
  set, array order kept), parsers by locale, and locales as a set.

Of the places in the list of where values reach the browser (Mechanism 7
in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "Navigation", "Addresses and keys the browser code
takes from the server" and "Translated messages".

## How it was checked

- **Code read.** The reviewer read the change with a security brief for
  the three places named above.
- **Node tests.** `pnpm --dir packages/js/citry-client run check`: 364
  passed. New tests: `i18n-configuration-order.test.mjs` (3; the reordered
  configuration fails against the `main` sources), `csrf-headers.test.mjs`
  (1), and two redirect tests (the rejection, and a `wait: false` redirect
  that only logs).
- **A real browser.** A new end-to-end test runs two `Render`s of a
  `<c-i18n c-client>` region with several format profiles. It fails with
  the `main` i18n plugin with the "different project configuration" error
  from #660 and passes now. The full end-to-end suite in Chromium, without
  the benchmark file, passed: 609 passed, 3 skipped.
- **Python tests that read the built runtime files:** 148 passed.
- **Other frameworks' advisories (Mechanism 8).** The reviewer checked
  these kinds from the survey: open redirects, URL schemes, CSRF handling
  and prototype keys. It found no hole.

## Ruled out

- **A refused URL causing navigation.** The reviewer found none: the
  change only alters what happens after the refusal.
- **Two different configurations compared as equal.** `sameJsonContent`
  tells arrays and objects apart, keeps array order, and compares a
  `__proto__` key as data.
- **`csrfHeaders` reading a value that is not a URL.** It accepts only a
  string or a `URL` and gives no header for anything else.

## Fixed during the review

- The `wait: false` case is now documented and tested.
- `docs/design/security_csrf.md` describes the new `csrfHeaders` rule.

## Not tested

- **Other browsers.** The end-to-end suite ran in Chromium only.

## Follow-ups

- None. The description asked whether the `applyActions()` change, which
  alters a documented browser API, needs a minor release. The pull request
  treated it as a bug fix: the changelog lists it under Fixes in
  "Unreleased" and says that code that awaits `applyActions()` may now
  need a `catch`.
