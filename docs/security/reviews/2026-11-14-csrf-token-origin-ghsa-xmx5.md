# CSRF token and request URLs in the browser (GHSA-xmx5)

- **Advisory:**
  [GHSA-xmx5-6846-xq2r](https://github.com/citry-dev/citry/security/advisories/GHSA-xmx5-6846-xq2r),
  published 2026-11-14, severity low (CVSS 3.1 base score 3.1)
- **Affected and fixed versions:** `citry` 0.3.0 up to but not including
  0.8.0; fixed in 0.8.0
- **Fix:**
  [`f5f079137`](https://github.com/citry-dev/citry/commit/f5f079137f28615b61bfd5295d5a9afe562c5ff5):
  the built-in event transport (the browser code that sends event calls)
  sends the CSRF token only to the page's own origin and does not follow
  redirects, and Citry's browser code resolves relative request URLs
  against the page's own address
- **Reviewer:** a separate reviewing agent
- **Code:** `packages/js/citry-client/src/citry-events-vue.ts`
  (`eventRequestTarget`, the `redirect: "manual"` request);
  `packages/js/citry-client/src/page-dom.ts` (`resolveOnPage`,
  `onPageOrigin`, `pageOrigin`);
  `packages/js/citry-client/src/citry-i18n-vue.ts`;
  `packages/py/citry/citry/_vue/client.js` (`resolveOnPage`,
  `updateHistory`, `Citry.events.configure`); the built files
  `packages/py/citry/citry/_vue/runtime.js`, `vue.js` and `events.js`;
  tests in `packages/js/citry-client/test/vue-events.test.mjs`,
  `runtime-events.test.mjs` and `redirect-scheme.test.mjs`, and in
  `packages/py/citry/tests/e2e/test_events_csrf_origin_e2e.py` and
  `test_i18n_django_csrf_e2e.py`

## Who controls the input

Citry's browser runtime sends the page's CSRF token (the secret value a
server checks to tell its own pages from forged requests) in a header on
each event call (a browser call to a Python event handler). Before the fix
it built the call's URL from the page's base URL and followed HTTP
redirects. A page where an attacker can already inject HTML could therefore
send event calls, with the token, to another site. Adding a `<base href>`
element (an element that moves the address relative URLs resolve against)
was enough, and so was a server redirect. The other site had to approve the
cross-origin request first. The advisory notes that on Django the token
alone is of limited use, because the CSRF cookie is `SameSite=Lax` by
default and Django checks `Origin`.

The inputs, by who first supplies them:

- **The `<base>` element.** It comes from whoever injects HTML: request
  data or stored data that reaches the page as markup.
- **A redirect answer.** It comes from the server that answers the
  call. The attack needs a redirect on a route the page calls.
- **The events URL and CSRF settings.** An app author sets these in
  Python or with `Citry.events.configure`. A URL that names another host
  is the author's own choice.
- **The URL in the `$i18n` message request** (the browser request that
  loads translated messages). The server writes it.
- **The URLs in the `Redirect`, `PushUrl` and `ReplaceUrl` actions**
  (server answers that send the visitor to a URL or change the address
  bar). The app's Python code chooses them, and they may contain request
  data, which Citry's docs already warn about for `Redirect`.

Both followed `<base>` too. The token was not attached to them.

The browser sends a request to the address the URL resolves to, with the
token header in the case of event calls. The places in the Mechanism 7
list (the list in `CLAUDE.md` of places where a value reaches the browser)
that the fix touches are the addresses the browser code takes from the
server and navigation (`Redirect`, `PushUrl`, `ReplaceUrl`). The reviewer
also tried element `id` and `name` against the runtime's reads of `window`
and `document` members.

## How it was checked

**A browser test script, old runtime against the fix.** It used
Chromium and Firefox through Playwright (a tool that drives real browsers
from a script). The review did not record the browser versions. One local
server served a Citry counter page and Citry's routes. A second server
stood in for another site: it approved every CORS preflight (the check a
browser makes before it sends a cross-origin request with extra headers)
and recorded each request and its headers. A harmless token sat
in the cookie. Six cases ran in each browser:

- a `<base>` element pointing at the second server, added after the page
  started;
- a server answering the event call with a 307 and with a 302 to the second
  server;
- two events URLs that name the second server, set through
  `Citry.events.configure`, with a token set explicitly;
- a same-origin control.

On the old runtime the second server received the token in all five
non-control cases, in both browsers: three that an attacker can cause (the
`<base>` element and the two redirects) and two that an app author sets up
(the configured URLs). On the fix, with the `<base>`
element, the call went to the page's own origin and worked, and nothing
reached the second server. With both redirects the call failed with an
error, and nothing reached the second server. With the two events URLs
that name the other host, the call reached that host with no CSRF header.

**A second test script by the reviewer.** It ran 32 cases in each of
Chromium and Firefox against the fix. The bullets below cover 28 of them.
The other four put a `<base>` element in the markup the page first loads.
Only their script-file result is recorded (see "Not tested").

- the same-origin control, and a `<base>` element added after the page
  loaded, which sent the call and its token to the page's own origin only;
- the same `<base>` on a page whose elements carry names and ids that match
  members of `window` and `document` (such as `origin`, `location`, `URL`,
  `baseURI`, `cookie`, `fetch` and `globalThis`). Nothing reached the other
  site in either browser. In Chromium this case sent no token to the page's
  own origin either, where the control sent one. The output does not say
  why. The test script's own write of the cookie may have been hidden by
  the named element, so this case shows no leak but may not have exercised
  the token path in Chromium;
- redirect answers with codes 301, 302, 303, 307 and 308, each to the
  other site and to a route on the same site. All ten failed as calls and
  none was followed. The other site's server log stayed empty. Chromium's
  own request log shows the browser started a request to the other site's
  address with no token, and that server never received it;
- eight spellings of an events URL, each set with an explicit token
  (scheme-relative, backslash forms, forms with a tab, a newline or a space
  around the slashes, a scheme with no slashes, and a relative path with no
  slash). The browser reads six of them as another host. Those six reached
  that host as configured and sent no CSRF header. The other two resolved
  to the page's own origin;
- the counter inside an iframe, loaded from a URL and from `srcdoc` (an
  iframe whose page is written inline in the iframe tag), in several
  combinations of sandboxing (with and without `allow-same-origin`) and a
  `<base>` element. A sandboxed page loaded from a URL has no origin of
  its own, and its calls failed. A `srcdoc` page that
  was sandboxed, or had a `<base>` element, refused the call. A plain
  `srcdoc` page worked. Nothing reached the other site in any frame case.

The reviewer's page had a `GET`, a `POST` and a `PUT` handler. In the
same-origin control the `POST` and `PUT` calls carried the token and the
`GET` call did not, and none of the three sent it to another host.

**Tests added.** The JavaScript tests cover:

- an event call with a `<base>` element that names another site, and a
  sub-path kept in the call's URL;
- a URL on another origin that gets no token even when the token is set
  explicitly, and a sandboxed page (origin `"null"`) that sends none;
- an `about:srcdoc` page (an inline page that inherits its base from the
  page that holds it), which uses that base only on its own origin;
- a redirect that fails the call, and the header check in
  `Citry.events.configure`;
- redirects resolved against the page's address, including a generated
  set of URLs.

The browser tests drive a real
page with a `<base>` element for an event call, a redirect to another
origin and a `Redirect` action, and drive a Django app with its CSRF check
for the `$i18n` message request.

## Ruled out

- **The token reaching another origin through `<base>`.** The call
  resolves against the page's address (`location.href`), and the
  header is added only when the resolved address has the page's origin.
- **The token reaching another origin through a redirect.** Event calls are
  sent with `redirect: "manual"`, and a redirect answer fails the call.
  Redirects to the same site fail too.
- **A page with no origin of its own.** `pageOrigin()` reads `window.origin`,
  which is `"null"` for a sandboxed document, and `onPageOrigin` never
  matches that, so such a page sends no token.
- **Page elements shadowing `document` members.** The reviewer's named
  elements sent nothing to another host. Citry's event code reads the document
  through `pageDocument`. The Chromium result above limits what this case
  proves.
- **The `$i18n` request, `Redirect`, `PushUrl` and `ReplaceUrl` following
  `<base>`.** The fix resolves their URLs against the page's address with
  the same helper, and the message request checks the token against that
  same resolved address. Tests cover the message request and `Redirect`.
  `PushUrl` and `ReplaceUrl` rest on the code change (see "Not tested").
- **A mismatch between the check and the request.** The check and the
  request take their address from one resolved value.
- **An events URL on another host, set by the app author.** The call goes
  where the author sent it, without the token. This is author-only by
  design, and the browser reference says a request to any other address
  goes without the token "even when you set `token` yourself". The call
  itself still reaches that host, with its arguments and, for a `GET`, the
  State token (the signed component state that a call carries) in its
  address.
- **A custom transport.** A transport added with
  `Citry.events.registerTransport` (a transport is the code that sends
  event calls) is page code that picks its own destination, so it gets the
  URL and token as configured. The docs say so.

## Fixed during the review

The reviewer's follow-up test scripts looked at the `Redirect` and URL
actions and the `Citry.events.configure` case below. The advisory states
that the actions and the message request followed `<base>` in the earlier
code. The review did not record a run that showed it. The merged fix
contains all three changes:

- The `$i18n` message request followed `<base>`. It carried no token. It
  now resolves against the page's address, and
  `test_locale_switch_ignores_a_base_href_that_points_elsewhere` covers it.
- The `Redirect`, `PushUrl` and `ReplaceUrl` actions followed `<base>`.
  They now resolve through `resolveOnPage` (`client.js`), and
  `test_redirect_action_ignores_an_injected_base_href` covers `Redirect`.
- `Citry.events.configure` read the caller's `csrf` object twice, so an
  object with a getter could pass the header checks with one value and
  store another. It now copies the object first and checks the copy.

## Not tested

- Browsers other than Chromium and Firefox, and the browser versions. The
  review did not record them.
- Which commit of the fix each browser run used. The outputs do not say.
- `PushUrl` and `ReplaceUrl` in a browser. No test checks the resolved
  address that `updateHistory` passes to the history call, and the
  JavaScript tests replace that call with a fake. The browser itself
  refuses a history URL on another origin.
- Custom transports, which are outside the fix by design.
- A `<base>` element that is in the markup when the page first loads moves
  the addresses of Citry's own script and stylesheet files. That is the
  subject of
  [GHSA-x6rm-5x8c-wr5c](https://github.com/citry-dev/citry/security/advisories/GHSA-x6rm-5x8c-wr5c).
  The reviewer's test script loaded such a page and saw the file requested
  from the other site, but this review did not examine that fix.

## Follow-ups

None open. If a page sets `<base href>` on purpose, write Citry's event,
message and action URLs as paths that start with `/`. The changelog
and the browser reference
([`docs_site/content/reference/browser-apis.md`](https://github.com/citry-dev/citry/blob/f5f079137f28615b61bfd5295d5a9afe562c5ff5/docs_site/content/reference/browser-apis.md))
say so.
