# `forbid` on the no-JavaScript Events answer (GHSA-m644)

- **Advisory:**
  [GHSA-m644-8j2v-8c23](https://github.com/citry-dev/citry/security/advisories/GHSA-m644-8j2v-8c23),
  published 2026-11-18, severity medium (CVSS 3.1 score 4.7)
- **Affected and fixed versions:** `citry >= 0.6.0, < 1.0.1`; fixed in
  1.0.1
- **Fix:** `1857f6dcc`, committed to `main` 2026-11-18. Citry keeps
  `security_javascript="forbid"` on the HTML page that an Events handler
  sends in answer to a plain form post or a link. An answer that needs
  JavaScript now fails with the plain-text 500 error this answer gives
  for any handler error. This holds when either the app that serves the
  handler or the app that owns the rendered component sets `"forbid"`.
- **Reviewer:** separate reviewing agents: the settings audit that found
  it, a review of the finding, a review of the fix that ran the form and
  link routes in three browsers, and a review of the whole release
  candidate
- **Code:** `_compat_security_javascript` in
  `packages/py/citry/citry/ext/events/results.py`, used by
  `HtmlFragmentRenderEncoder.encode`; tests in
  `packages/py/citry/tests/test_events_compat_security_modes.py`

## Who controls the input

`security_javascript="forbid"` makes Citry raise an error instead of
sending a page that needs JavaScript, such as a page with a
`javascript:` link, an `onclick` attribute or a `<script>` tag. An
Events handler (a Python function that the browser calls) can answer a
plain HTML form post, or a link that opens a `GET` handler, with a whole
HTML page. On that answer Citry used `"omit"`, which only warns, in
place of the app's setting. Releases 0.4.6 to 0.5.1 applied the app's
setting on this answer; 0.6.0 to 1.0.0 did not.

The inputs, by who first supplies them:

- **The setting.** The app author turns on `"forbid"` as a safety net.
- **What the rendered component holds.** A URL attribute filled from
  request data whose scheme the app did not check, so anyone who can
  send the request supplies it; or an `onclick` or `<script>` the
  template author wrote. The browser runs the script in the app's origin,
  a `<script>` at once and a link or handler when the visitor clicks.

Checking the scheme of a URL from request data stays the app's job
([#601](https://github.com/citry-dev/citry/issues/601)); `"forbid"` is
the safety net that did not apply here.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches "URL attributes", "Navigation", "The opt-in output
checks" and "Responses Citry serves".

## How it was checked

- **Browsers.** Chromium 159, Firefox 159 and WebKit 27.2 through
  Playwright 1.65.2, on 1.0.0 and on the fix. Each case used a harmless
  effect that is easy to see.
- **Releases.** 1.0.0 was run. 0.4.6, 0.5.0, 0.5.1 and 0.6.0 to 0.9.0
  were read from the release tags.
- **Hosts.** WSGI, ASGI and Django.
- **Routes.** A form `POST`, a `GET` handler opened by a link from
  another site, a `GET` form, `ViewEvents` `GET` and `POST`, and async
  handlers.
- **Kinds of input.** Script URLs from request data in several places in
  the component (a plain element, a bare value, rendered markup, the
  template, and a template that holds another template language), and an
  `onclick` and a `<script>` written in the template.
- **Browser result.** 9 of 9 cases ran the effect on 1.0.0, and 0 of 9 on
  the fix.
- **Tests.** 13 of the 21 new tests fail on 1.0.0. The whole Python suite
  without browser tests passed (14,139), apart from 2 failures that come
  from the test environment and fail the same way on `main`.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked these kinds: sanitizer bypass
  (`sanitizer-bypass`), URLs (`xss-url`), error pages (`error-page`),
  script loading (`script-load`), missing escaping (`xss-escape`), server
  data reaching the client (`source-exposure`), the expression sandbox
  (`sandbox`) and translated messages (`i18n-xss`).

## Ruled out

- **Other places that replace the app's mode.** A sweep found this was
  the only one. The preview server, Citry UI tools, slots and error
  fallbacks use the app's mode.
- **`security_csp`.** It was not replaced on this answer
  (`test_strict_csp_refuses_template_script_in_the_answer`).
- **The answer the JavaScript runtime reads.** It already answered 500.
- **The batch route.** It never answers without JavaScript.
- **Other results.** A `Redirect` to a script or `data:` URL, several
  `Render` results, and a `Render` with a `Redirect` were checked.
- **Changing apps that do not set `"forbid"`.** With `"allow"`, `"warn"`
  or `"omit"`, the answer is served as before, with a warning where the
  mode gives one (`test_the_answer_is_served_with_a_warning`), and
  Citry's own scripts stay out of it
  (`test_citry_scripts_stay_out_of_the_answer`).
- **Author-only by design.** A custom hook or encoder that writes HTML,
  and a `RouteResponse` a handler returns, are app code; Citry does not
  check them.

## Fixed during the review

- When the rendered component belonged to another Citry app whose mode
  was the default `"allow"`, the serving app's `"forbid"` was dropped.
  Both apps' settings are now read.
- One test could not fail; it now uses a component with `js`.
- A stale line reference in a design doc, and wording in a docstring.

## Not tested

- Real Safari, and a page sent with a Content Security Policy header.
- ASGI and Django hosts in a browser; these were checked over HTTP only.
- The browser end-to-end tests and the full repository gate.

## Follow-ups

- [#601](https://github.com/citry-dev/citry/issues/601): checking the
  scheme of a URL from request data stays the app's job.
- `docs_site/content/security.md` ("Limit page JavaScript") says that
  `"forbid"` covers this answer and that it applies when either app sets
  it.
