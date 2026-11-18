# Size limit for request `Decimal` values (GHSA-qhcg)

- **Advisory:**
  [GHSA-qhcg-m32p-2mcr](https://github.com/citry-dev/citry/security/advisories/GHSA-qhcg-m32p-2mcr),
  published 2026-11-18, severity medium (CVSS 3.1 score 5.9)
- **Affected and fixed versions:** `citry >= 0.3.0, < 1.0.1`; fixed in
  1.0.1
- **Fix:** `fe80eabe7`, committed to `main` 2026-11-18. Citry refuses a
  request `Decimal` whose size is 1e309 or more (either sign), or that
  has more than 308 decimal places, with the usual 422 `invalid_args`
  error. The check covers Events arguments (checked by Citry or by
  Pydantic, sent as JSON or from a form), browser writes to a Pydantic
  State, and the State a State token holds each time the token is read.
- **Reviewer:** separate reviewing agents in five rounds: a review of the
  finding, then a review of each of three versions of the fix, then a
  review of the whole release candidate
- **Code:** `packages/py/citry/citry/util/decimals.py`
  (`request_decimal_in_range`, `decimal_in_range`,
  `find_oversized_decimal`), called from
  `packages/py/citry/citry/ext/events/` (`schemas.py`,
  `_pydantic_bounded.py`, `tokens.py`, `dispatcher.py`, `cache.py`) and
  `ext/i18n/extension.py`; tests in
  `packages/py/citry/tests/test_events_decimal_size.py`

## Who controls the input

A short `Decimal` with a large exponent describes a number with a huge
number of digits. Storing it costs nothing, but writing it out does: a
fixed-point format such as `f"{amount:.2f}"` writes every digit, and
`"%d" % amount` or `int(amount)` computes every digit first.

The inputs, by who first supplies them:

- **The value.** Anyone who can send a request supplies it: as an
  argument of an Events handler (since 0.3.0), which arrives as JSON or
  from a plain HTML form, or as a browser write to a Pydantic State field
  (since 0.7.0). Citry or Pydantic turns the text into a `Decimal`.
- **The code that writes it out.** The app author writes the template or
  Python code that formats the value with a fixed-point spec or `%d`, or
  converts it with `int()`, `round()` or `math.floor()`. Showing the
  value with `{{ amount }}` stays short.

The risk is the server's memory and CPU time: one request could cost
about 1 GB of output and several GB of memory, or hours of CPU time, and
stop the worker. Nothing reaches the browser, and no data is read or
changed. `citry` 0.7.0 bounded the same kind of value for the i18n
number formatters only
([GHSA-vgc3-4q38-q7vf](https://github.com/citry-dev/citry/security/advisories/GHSA-vgc3-4q38-q7vf)).

The Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)
covers values that reach the browser, so it has no entry for this
input. This review covers how Citry's server reads a request that anyone
can send.

## How it was checked

- **Hosts.** CPython 3.13.17 and 3.14.9 on macOS. Raw WSGI with
  `wsgiref`, FastAPI's `TestClient`, and uvicorn over a real socket.
- **Releases.** 1.0.0 was run. 0.2.0, 0.3.0, 0.6.0 and 0.7.0 were read
  at their release tags.
- **Routes.** The Events JSON request, the no-JavaScript form post,
  arguments read from a form, a `GET` query, Pydantic models and
  dataclasses in many shapes, Pydantic State writes (Pydantic 1 and 2
  models, and Pydantic dataclasses), State restored from a signed token
  and from the server cache, a cached render replayed, and two calls in
  one batch. A State token signed by the released 1.0.0 was sent to the
  fix with the same secret.
- **Cost before the fix.** As the exponent of a short value grew, a
  fixed-point format wrote 1 MB, 10 MB and 100 MB, with peak memory up to
  about 1.1 GB; growth is linear, so the largest values reach several GB
  per request. The integer conversion took CPU time that grows with the
  square of the exponent, from a fraction of a second to about 24
  seconds in the runs, about 40 minutes at an exponent ten times larger,
  and hours for the largest values, by extrapolation.
- **Choosing the bound.** A first bound at the edge of what a `Decimal`
  context allows still let a list of 10,000 values cost 328 MB of output
  and 4.65 GB of memory. The final bound matches the range of a float.
  With it, the most costly list tried (720 KB) gave 30 MB of output and
  475 MB of memory in 0.76 seconds.
- **Cost of the check.** Citry's pass over the request data that looks
  for such values (the walk) took, on a 1 MiB request, 0.03 to 0.23
  seconds, growing with size and not with nesting depth.
- **Tests.** 41 of the 79 new tests fail on the 1.0.0 code with only the
  new `decimals.py` added. The whole
  Python suite without browser tests passed (14,191), with `ruff`, and
  `mypy` on macOS and with `--platform linux`.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked these kinds: resource use from a small input
  (`dos-amplify`), costly template filters (`filter-dos`, the same kind
  as two Django `floatformat` reports), request body size (`dos-body`),
  unsafe deserialization (`deserialize`), error pages (`error-page`), log
  injection (`log-inj`), State shared between requests and component
  State (`xreq-state`, `island`), sanitizer bypass (`sanitizer-bypass`)
  and cache keys (`cache-key`).

## Ruled out

- **Other number types.** Integers are bounded by Python's limit on
  integer digits, and a float out of range becomes infinity, which is
  refused.
- **A plain State.** It cannot hold a `Decimal`.
- **The i18n formatters.** They already had their own bound, and now use
  the same function with their own range.
- **A value kept in a token.** A token signed by an affected release that
  holds such a number is refused and not signed again
  (`test_a_token_holding_an_oversized_decimal_is_refused`), and a cached
  render with such a State is not replayed
  (`test_a_cached_render_with_an_oversized_state_decimal_is_not_replayed`).
- **Pydantic `max_digits` alone.** It does not bound a zero with a far
  exponent, so Citry's check always runs
  (`test_max_digits_does_not_bound_a_zero_and_the_check_still_runs`).
- **Values inside iterables.** Items of `Iterable` and generator fields
  are checked without consuming them (`test_iterable_and_generator_items`).
- **The error itself.** The message names the range, never the value
  (`test_the_message_does_not_echo_the_value`), and a call gets one
  message however many values it holds.
- **The walk.** It builds nothing, runs no properties, handles cycles,
  and keeps its state per validation in a context variable, so requests
  do not share it.
- **The largest accepted value.** It formats quickly
  (`test_the_largest_accepted_value_formats_quickly`).

## Fixed during the review

- Items of `Iterable` and `Generator` fields were not checked.
- Nested Pydantic 1 models in a State were not checked.
- The walk took quadratic time on nested Pydantic dataclasses, 8.6
  seconds for one 1 MiB request.
- `Secret[Decimal]` values were not checked.
- A State token signed by an affected release was restored and signed
  again, so it kept such a number forever. Restored State is now
  checked.
- A field that a validator derives and that ends up equal to its earlier
  value, and a value written into an object already walked, were not
  checked.
- The docs now say what happens to a State the app itself fills.
- Literal test values were removed from the changelog and docs.

## Not tested

- Python 3.11, 3.12 and PyPy, and Linux.
- Django and ASGI hosts in a browser, and the browser end-to-end tests.
- Full-size values; the largest costs above come from extrapolation.
- Cached-render replay and the Events `Render` action over HTTP; these
  rest on reading the code and on unit tests.

## Follow-ups

- Documented limits, in `docs_site/content/security.md` ("Check event
  data"): the check runs after the app's own Pydantic validators, and it
  does not read into the app's own classes, so an app type that wraps a
  `Decimal`, or app code that builds one from text, needs its own check.
- No issue is open yet for further hardening: a size cap in the
  expression sandbox's `format` helper, and counting the walk against
  the request's work budget.
