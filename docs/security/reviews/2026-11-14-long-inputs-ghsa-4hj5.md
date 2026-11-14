# Long inputs that cost too much time and memory (GHSA-4hj5)

- **Advisory:**
  [GHSA-4hj5-rp55-8wh8](https://github.com/citry-dev/citry/security/advisories/GHSA-4hj5-rp55-8wh8),
  published 2026-11-14, severity high (CVSS 3.1 score 7.5)
- **Affected and fixed versions:** `citry < 0.8.0`; fixed in `citry` 0.8.0
- **Fix:**
  - `74eeb8d92` makes `style` values, route paths with several
    parameters in one segment, and Redirect URLs take time in proportion
    to their length.
  - It builds each event field path (the name of a field inside the data,
    such as `scores.alice.3`) from its parent's path and one key.
  - It limits how much field path text a call to a Pydantic class can
    produce (Pydantic is the Python library that checks data against a
    class).
  - `1331565fa`, in the same release, cuts the memory that a style value
    with long quoted text, backslash escapes or many short quoted strings
    uses.
- **Reviewer:** separate reviewing agents
- **Code:**
  - Style values: `_style_comment_re`, `_strip_style_comments` and
    `parse_string_style` in `packages/py/citry/citry/attrs.py`.
  - Route paths: `match_route_pattern` and `_match_segment` in
    `packages/py/citry/citry/util/routing.py`, and the Django route class
    built by `_citry_route_pattern_class` in
    `packages/py/citry/citry/contrib/django.py`.
  - Redirect URLs: `redirectScheme` in
    `packages/py/citry/citry/_vue/client.js` (and the built `runtime.js`
    beside it).
  - Event field paths: `FieldErrors`, `trimmed_path` and `PydanticTotal` in
    `packages/py/citry/citry/ext/events/errors.py`; `pydantic_can_report`
    in `packages/py/citry/citry/ext/events/schemas.py` and its callers in
    `tokens.py` beside it; `_pointer_at` and `_strict_json_issue` in
    `packages/protocol/events/v1/python/citry_events/issues.py` (with a
    copy in `packages/py/citry/citry/_protocol/events/issues.py`);
    `_shape_path` and `_freeze_json` in
    `packages/py/citry/citry/ext/cache/artifact.py`.
  - Tests: `test_attrs.py`, `test_route_pattern_linear.py`,
    `test_contrib_hosts.py`, `test_events_actions.py`,
    `test_events_routes.py`, `test_events_schemas.py`,
    `test_events_tokens.py`, `test_events_protocol_runtime.py` and
    `test_ext_cache_typed_artifact.py` under
    `packages/py/citry/tests/`, and
    `packages/js/citry-client/test/redirect-scheme.test.mjs`.

## Who controls the input

Four kinds of input made Citry use far more time or memory than their
size should need. Each is plain text that someone sends.
The risk is the cost: the server's processor and memory or, for Redirect
URLs, the visitor's own browser tab. No value reaches the page differently.
Who supplies each kind:

- **A `style` value** (through `c-style`, a `c-bind` spread, `merge_attrs`,
  a dynamic component or an i18n binding). The app's Python code supplies
  it, and the value can be request data or stored data that the app only
  passes along. Citry parses it into CSS properties before it writes it.
- **A request path matched against a route.** Anyone who can send a request
  supplies the path. The routes at risk are those with several parameters
  in one path segment, such as `{name}-{version}`, which an extension
  registers. Citry's own routes are not at risk.
- **A `Redirect` URL.** The app's event handler supplies it, and it can come
  from request data such as a "next" parameter. The browser checks its
  scheme before it follows it, so the cost lands in the visitor's tab.
- **Event call data: dict keys.** Events is how Citry lets the browser call
  a Python handler, and State is the per-page data a handler can read and
  the browser can ask to change. Anyone who can reach an Events URL can send
  an event call, with no login, up to the default 1 MiB body limit. Its
  arguments and State updates can hold a dict key that is very long or has
  many dots. Citry checks each item below the key, and Pydantic writes the
  whole path of a field into each error it reports, so one long key over
  many bad items multiplies the memory.

Of the places in the security pass list of
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
the change touches three: CSS (the style parser), navigation (the scheme
check on a `Redirect` URL, which decides whether the browser may follow
it) and the text of Citry's error responses (the 422 messages, 422 being
the HTTP status for invalid data). The first two are security checks, so
the fix had to give the same results as before. For event calls the
result changes on purpose (see "Ruled out").

## How it was checked

The reviewers read the code and wrote probe programs. Most compare the
released code (the release before the fix) with the fixed code on the same
inputs, so a different answer shows up as a difference. Counts and times
are given only where the review recorded them; some programs have no
recorded output, and those are described without a result.

- **Style values.** A comparison program ran the released comment pattern
  and the fixed one on strings built from quotes, backslash escapes,
  comment markers, line breaks, NUL, lone surrogates and `url(...)`
  values: 153,391,689 exhaustive comparisons over short strings and
  1,500,000 random ones, with no difference. It tested the comment pattern
  of the fix, not the later memory change. A timing program ran 13,188
  runs of short repeated units, with several prefixes, through
  `parse_string_style`. The slowest, runs with backslash escapes, took
  0.064 s at 80,000 characters. That is little time, but it grew faster
  than the text did (17.7 times as long for four times the text).
  `1331565fa` later changed the pattern so that each character is read
  once; "Style memory" below measures it.
  `normalize_style` on 1,000,000 characters took 0.02 to 0.08 s for each
  shape tried, measured on the tree before the memory change in
  `1331565fa`. Other programs sent a long style string through each entry
  point the advisory names, except the i18n binding, which was only read.
- **Style memory.** For `1331565fa`, the peak memory inside
  `parse_string_style` was measured for about 1 MiB of text on released
  code and on the fix. A run of backslash escapes went from about 27 bytes
  for each character to no measurable peak, many short quoted strings from
  about 19 to none, and back-to-back empty comments from about 2 to none.
  Plain declarations cost about 9 bytes for each character before and
  after, which is the parsed result itself. Then 600,000 random strings
  and six long cases gave the same results as the released code.
- **Route paths.** A comparison program checked `match_route_pattern`
  against the released regular expression (a text pattern) on random and
  exhaustive routes and paths: special pattern characters in the fixed
  text, text that repeats or overlaps a parameter, many parameters,
  control characters and lone surrogates, a trailing newline or carriage
  return, repeated parameter names and brace-like text. It made 825,000
  random and 30,308,550 exhaustive comparisons, with no difference. In
  97,878 of the random cases the released pattern itself rejected the
  route, and the fixed code raised the same error. Timing programs used
  paths that get past the cheap length, start and end checks, so the time
  is spent splitting the segment, through the matcher, the Django route
  class and real web requests.
- **Redirect URLs.** The fix author compared the released rule with the
  fixed one on 3,000,000 random URLs. A reviewer's program read the shipped
  `redirectScheme` out of the built `runtime.js` and `client.js`, so the
  shipped text is the text under test, and compared it with the released
  rule on every string of up to six characters from a seven-character
  alphabet and on 3,000,000 random ones (about 3.1 million in all). Both
  found no difference. Other programs timed the rule and compared the
  schemes it lets through with the URL parser of Node.js; none of those
  has a recorded result. The fix's own test uses 3,000 generated URLs from
  a fixed seed and checks that each is followed or refused exactly as the
  released rule decides, and a second test checks that a long run of
  spaces inside a URL is handled in well under a second.
- **Event field paths and messages.** A comparison program ran seeded
  payloads through Events validation and State writes on the released code
  and on the fix: three seeds of 60,000 cases (180,000 in all) gave
  identical results. Other programs measured memory and time in child
  processes with limits, through real web requests (WSGI and ASGI are the
  standard Python server interfaces), for arguments and State updates.
- **Do the timing tests for deeply nested data fail without the fix?** The
  fix author and a reviewer each ran the two timing tests, with the 1 s
  bound they had then, on the fix before its last path-handling change.
  Both tests failed that bound without hanging, and passed after the
  change. The State write test is
  `test_marking_the_lists_of_deep_errors_in_a_write_takes_time_in_step_with_their_depth`
  and took 2.1 s for the author and 2.42 s for the reviewer, then 0.35 s
  and 0.43 s. The `validate_args` test is
  `test_marking_the_lists_of_deep_errors_takes_time_in_step_with_their_depth`
  and took 3.7 s and 4.00 s, then 0.26 s and 0.29 s (up to 0.60 s under
  coverage).
- **Does the comparison see a wrong answer?** A reviewer broke the fix on
  purpose, to check that the event comparison of two versions of the fix
  would notice a mistake. Removing the handling of list and dict values
  changed the answer in 303 of 1,288 cases, and removing only the dict
  values in 232 of 1,259. Removing the skip for an empty key changed none,
  because the generator never makes that case, so a separate program
  covered it.
- **Tests.** The fix adds tests in the files listed under "Code". The
  tests that compare with the released behavior use generated inputs
  (`test_it_parses_exactly_as_the_released_regex_on_random_text`,
  `test_match_route_pattern_gives_the_regex_answer_on_generated_routes`
  and `test_it_keeps_exactly_the_released_messages_on_random_fields`). The
  timing tests compare a short input with a longer one, or use loose
  bounds, so a slow machine does not fail them.

## Ruled out

- **A different result for style values and route paths.** The comparisons
  above found no difference from the released code.
- **A different result for Redirect URLs.** The comparisons of 3,000,000
  and about 3.1 million URLs and the fix's own test of 3,000 generated
  URLs found no difference.
- **A different result for event messages.** The comparison of 180,000
  cases found no difference.
- **A long key copied once for each item.** Tests named for this
  (`test_a_long_key_over_many_bad_items_costs_little`,
  `test_a_long_key_under_many_messages_is_placed_once`,
  `test_a_strict_json_problem_names_its_pointer_without_copying_keys` and
  `test_render_data_with_a_long_key_is_checked_without_copying_the_key`)
  cover the event checks, the strict JSON check that Events uses for
  protocol values, and the cache's check of the data stored with a cached
  render. Each builds
  a path from its parent's path and one key, and writes the text only for a
  message it keeps.
- **A rejected write to a Pydantic dataclass State changing the State.**
  `test_a_refused_value_rejects_the_whole_batch_and_changes_nothing` covers
  it. A review run also compared random bad writes to such a State on two
  versions of the fix (1,500 cases) and found no difference.
- **Two answers that change on purpose.** The path limit can refuse a valid
  call, and the public docs say when. For a Pydantic dataclass `data` class,
  the answer to bad input is a 422 with field messages, where the released
  code gave a server error. The changelog says both.

## Fixed during the review

- **The test for a field that accepts several model types (a union) needed
  a payload that costs something.** A reviewer found that the test's input
  cost almost nothing to check, so it could not show whether the limit
  worked. The test now uses a payload that costs more under one union
  member, and it runs at 1, 10, 100 and 1,000 rows: the costly member runs
  for the first three and the limit stops it at 1,000.

## Not tested

- **A real browser.** The Redirect checks ran in Node.js with a fake page
  object. The time the check takes in a browser tab is the advisory's
  figure.
- **Other Python versions and operating systems.** The last recorded timing
  runs used macOS, Python 3.14.9 and Pydantic 2.14.1.
- **Django `reverse()`.** At this fix it still used the route's regular
  expression, and the advisory tells apps not to pass request data to it.
- **Strings that an app's own validator parses.** The path limit does not
  count them (the advisory says so), so the app should check their length
  first.
- **The refusal point of the path limit in 0.8.0.** The review measured the
  smallest refused call for a model with many required fields and a list of
  small objects, and confirmed it with real requests (one point below was
  accepted, and at the point the answer was a 422). It measured this
  before the error limit for Pydantic v2 classes, described in the
  advisory, was added. In 0.8.0 the path limit applies only to the three
  kinds of data the advisory lists: browser writes to a `pydantic.v1`
  State, State that Citry can check only as JSON text, and, rarely, a
  Pydantic v2 class whose checks Citry could not set up. No result is
  recorded for the union and long-key cases that the docs also name.
- **Other memory and time that Pydantic needs.** The path limit counts the
  length of field paths only. The rest is the subject of
  [GHSA-8xvf-qw9c-538m](https://github.com/citry-dev/citry/security/advisories/GHSA-8xvf-qw9c-538m).

## Follow-ups

None.
