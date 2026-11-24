# A GET call sends its State token in a header (#868)

- **Pull request:** [#868](https://github.com/citry-dev/citry/pull/868),
  merged 2026-11-24 (31841a7ec)
- **Reviewer:** a separate reviewing agent, in three rounds, as the pull
  request description states. The description names the Mechanism 7 pass
  and the check against the maintainers' survey of security advisories
  published for other frameworks (Mechanism 8). The pull request holds no
  report, comment or review thread. This record is built from the
  description, the merged change and its tests.
- **Code:** the server side in `packages/py/citry/citry/ext/events/`:
  `decode_query_request` and `_merge_header_state_token` in `codecs.py`;
  `_early_refusal`, `_with_cache_marks`, `_private_cache_policy`,
  `_private_cache_control`, `_split_cache_directives` and
  `_with_page_nonce_marks` in `routes.py`. The header name,
  `STATE_TOKEN_HEADER`, lives in
  `packages/protocol/events/v1/python/citry_events/carriers.py`, is synced
  into `packages/py/citry/citry/_protocol/events/carriers.py`, and has a
  JavaScript counterpart, `CARRIER_HEADERS`, in
  `packages/protocol/events/v1/js/src/calls.ts`. The browser side is
  `createVueEventsBridge` and `answersInvalidState` in
  `packages/js/citry-client/src/citry-events-vue.ts`. Tests:
  `TestGetHandlers` in `packages/py/citry/tests/test_events_routes.py`,
  `_stateful_get_token_header` in `test_events_host_parity.py`,
  `packages/js/citry-client/test/vue-events.test.mjs`, and
  `test_a_get_call_that_reads_state_sends_its_token_in_a_header` in
  `packages/py/citry/tests/e2e/test_vue_events_default_e2e.py`

## Who controls the input

State is data that a component keeps between calls. The browser holds a
State token and sends it back with a call, so the server can restore the
State. An Events handler (Python code that the browser calls) that reads
State needs the token.

- **The State token.** It is request data: an opaque string that the
  server gave the browser earlier, and that any client can send back or
  alter. The server verifies it as before. This change moves where
  Citry's browser code sends it on a `GET` call to a handler that
  declares `state`: in an `X-Citry-State-Token` request header, not in
  the `_citry_state_token` query parameter. The server still reads the
  query parameter, for a client that sends it there.
- **The handler's own `Cache-Control` and CDN headers.** App code sets
  them. A CDN is a caching service in front of the app. When a `GET` call
  sends the token header, Citry narrows these headers so that only the
  visitor's own browser may keep the answer. Citry also lists
  `X-Citry-State-Token` in the answer's `Vary` header, which tells a cache
  which request headers change the answer.

What is at risk is not what the browser shows. It is where one visitor's
token goes: into server and proxy access logs, which record the URL, and
into shared caches that could give one visitor's answer to another.

The contributor rules in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)
(Mechanism 7) keep a list of the places where a value can reach the
browser. The description lists the places touched as "State tokens and
Events request headers, Events responses (`Vary`, `Cache-Control`)". The
nearest items in that list are "Addresses and keys the browser code takes
from the server" (Events request URLs) and "Responses Citry serves"
(`Cache-Control`).

## How it was checked

- **Three review rounds.** The description says each round checked every
  route the token can take. The results are in "Ruled out".
- **Other frameworks' advisories (Mechanism 8).** The description says
  the reviewer checked the survey's kinds for HTTP and cross-user
  caching, cache keys, header spoofing and injection, CSRF, log injection
  and token leakage, and that after the fixes listed below the change
  introduces none of them.
- **Server tests.** `TestGetHandlers` covers the header read, the same
  and different tokens, a repeated query field next to the header, an
  empty header, a malformed header, a stateless handler, a renewal
  through the header, `Vary`, cache policy narrowing, CDN headers, a long
  hostile policy, and 405 refusals. `_stateful_get_token_header` runs the
  same call on Django and FastAPI (ASGI), and
  `test_wsgi_reads_the_state_token_header_on_a_get_call` runs it on WSGI.
- **Browser tests.** `vue-events.test.mjs` covers the header in place of
  the query, no token for a stateless `GET`, the retry and no-retry
  cases, and a custom transport with and without headers. The protocol's
  JavaScript package exports `CARRIER_HEADERS`.
- **End to end.** One test in Chromium confirms that a `GET` call that
  reads State sends its token in the header.
- **Checks run locally.** The `citry` Python tests (15,522 passed,
  without the end-to-end tests), the Events end-to-end file (74 passed),
  the `citry-client` checks (398 passed) and the protocol JavaScript
  package checks (18 passed). Linters, mypy on macOS and with
  `--platform linux`, the repository's validators, the check that the
  synced protocol copy matches, and a strict docs build (0 errors, 0
  warnings) also passed.
- **Versioning.** The JSON envelope (the JSON body that carries a call)
  does not change, so no `citry-events/2` is needed. The description
  says an earlier optional request header, added in 1.2.0, set the
  precedent for adding a header without a new protocol version. It
  targets 1.3.0.
  The `400` for two different tokens refuses input that earlier releases
  accepted, and the changelog marks it "Security:". A page from 1.3.0 that
  calls a 1.2.0 server keeps working through one retry (see "Ruled out").

## Ruled out

- **Server and proxy access logs.** The description gives this route as
  safe for Citry's browser code, which sends the token in the header, so
  the URL holds none. The cases that still put a token in the URL are
  under "Follow-ups".
- **Logging or tracing tools that record request headers.** The docs say
  to leave the header out of them. See "Follow-ups".
- **`Referer` and browser history.** Not applicable. The URL of a `fetch`
  call becomes neither.
- **Shared caches and CDNs.** Every `GET` answer, including a refusal sent
  before dispatch, lists `X-Citry-State-Token` in `Vary` and carries
  `no-store` by default. When a call sends the header, Citry keeps only
  the `Cache-Control` directives that a browser cache follows behind
  `private` (or `no-store`), and drops CDN-only headers
  (`*CDN-Cache-Control`, `Surrogate-Control`, `Edge-Control`,
  `X-Accel-Expires`). The description gives the reason: some CDNs ignore
  `Vary`.
- **The header and the query parameter disagreeing.** Different tokens, or
  the header next to a repeated query field, answer `400
  protocol_mismatch` before the handler runs. The message echoes neither
  value. A repeated header fails token verification.
- **A cross-origin event URL.** Unchanged. Such calls were already
  preflighted (the browser asks the server's permission first) because of
  the `X-Citry-*` headers.
- **A retry that sends a call twice.** The browser retries a call once,
  with the token in the query and without the header, only when the
  answer is a single `invalid_state` error and its `Vary` does not list
  the header (a server older than 1.3.0), or the browser cannot read
  `Vary` (another origin, a custom transport). It never retries after a
  cancel or a timeout. A code comment in `citry-events-vue.ts` says the
  first answer refused the call before its handler ran, so sending it
  again is safe.

## Fixed during the review

- Refusals sent before dispatch had no `Vary` header.
- The retry first fired on any `invalid_state`. It now fires only when the
  server does not read the header.
- A handler's `public` cache policy behind a CDN that ignores `Vary` could
  share one visitor's answer.
- The first cache policy parser missed quoted and qualified `Cache-Control`
  values and CDN-only headers, and used a regular expression that could
  take time that grows with the square of a long value's length.
- `Vary: *` was not handled. The browser now treats it as listing the
  token header.
- Stale line references in `docs/design/trust_boundaries.md`, and several
  docs and spec passages.

## Not tested

- **Real CDNs and proxies.** The description lists no test through a CDN
  that ignores `Vary` or a proxy that drops the header. The tests check
  Citry's own answers.
- **A real 1.2.0 server.** The retry is tested in `vue-events.test.mjs`.
  The description lists no test against an older release.
- **Firefox and WebKit.** The description lists one end-to-end test, in
  Chromium.

## Follow-ups

The pull request closes
[#761](https://github.com/citry-dev/citry/issues/761). The pull request
documents these limits, in
[`security.md`](../../../docs_site/content/security.md) ("Treat State as
input") and in the "State tokens on GET" section of the
[Events v1 spec](../../../packages/protocol/events/v1/spec.md):

- A token still reaches a log when a client sends the query parameter,
  when the browser retries against a server older than 1.3.0, and in logs
  written before 1.3.0.
- A log or tracing tool that records request headers also records
  `X-Citry-State-Token`.
- A proxy in front of a 1.3.0 server must forward the header. If it drops
  it, the server answers `invalid_state` with the header in `Vary`, and
  the browser does not retry.
- A custom transport (code that an app supplies to send calls in place of
  the browser's `fetch`) can now run its `send` twice for one call.
  `docs_site/content/reference/browser-apis.md` and the changelog say so.
- An app that sets cross-origin (CORS) rules and lists the request headers
  it allows must add `X-Citry-State-Token`, which the changelog says.
