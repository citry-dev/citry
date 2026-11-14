# Route matching and ambiguous routes (#640)

- **Pull request:** [#640](https://github.com/citry-dev/citry/pull/640),
  merged 2026-11-14 (31038d79d); closes
  [#602](https://github.com/citry-dev/citry/issues/602)
- **Reviewer:** independent reviews, as the pull request description
  says. No review report or review comment is on file in the pull
  request, so this record rests on the merged change and its tests.
- **Code:** `packages/py/citry/citry/util/routing.py`
  (`check_route_table`, `_parse_route_path`, `match_route_pattern`,
  `route_reverse_regex`); `packages/py/citry/citry/contrib/django.py`
  (`_citry_route_pattern_class`, `_ReverseConverter`); the mount functions
  in `contrib/asgi.py` and `contrib/wsgi.py`, which the Flask and FastAPI
  `mount()` call; tests in `packages/py/citry/tests/`:
  `test_route_pattern_linear.py`, `test_route_path_rules.py`,
  `test_django_route_reverse.py`, `test_route_mounts_linear.py` and
  `_route_oracle.py`

## Who controls the input

This change replaces the regular expression (a pattern the Python `re`
module runs by trying splits one after another) that matched request
paths with a matcher whose time grows in step with the path's length. It
also refuses routes that put two parameters side by side, such as
`{name}{ext}`.

A `URLRoute` is how an app or an extension declares an HTTP route: a path
such as `files/{name}.{ext}`, where each `{name}` is a parameter that
reaches the handler as a keyword argument. Three kinds of input meet in
this change:

- **The route paths and `dotless_params`** (a set of parameter names that
  must not hold a `.`). The app's Python code or an extension author writes
  them. A child route's path is joined to its parent's as plain text, so
  two routes that look fine alone can join into a bad one.
- **The request path.** Anyone who can send a request to the app's Citry
  URLs controls it, including its length. Matching it with a regular
  expression can take far longer to reject a long path than its length
  suggests, when a segment holds two parameters next to each other. That
  costs the server CPU time.
- **The values given to Django's `reverse()`.** The app's Python code passes
  them, but they can come from a request or from stored data, such as a
  name or an id. `reverse()` builds the URL for a route name, and Citry
  then reads that URL back into parameter values when the browser follows
  it.

No HTML or script is involved. What is at risk is the server's time, and
whether the values a handler receives match what the app built or checked.
The change also touches how Citry decides which path reaches a route, which
matters to an app that guards Citry's URLs with a rule in its web framework,
such as middleware that checks the start of the path.

## How it was checked

The pull request description says independent reviews covered the matcher,
the checks made when routes are mounted, the Django `reverse()` change, the
security pass for request routing and URL building, and a prose pass. It
gives no findings beyond the one unproven case listed below. The results
here come from the merged code and tests on `main`.

- **Matcher against the earlier regex.** `_route_oracle.py` keeps the
  regular expression Citry used before. `test_route_pattern_linear.py`
  builds 600 random routes with one to four parameters, with text between
  them from a set that includes `.`, `-`, `/`, a newline and a non-ASCII
  letter, and random `dotless_params`. For each route it tries up to 40
  paths, some built by filling in the route and some random, and compares
  the matcher's answer with the regex's, including the order of the
  parameters. The test asserts it compared more than 10,000 pairs. Routes
  with two parameters side by side are expected to raise instead, and the
  test asserts that happened more than 50 times.
- **Growth tests.** The same file times a long non-matching path and one
  eight times as long, and fails when the longer run takes 24 or more times
  as long as the shorter one (growth in step with length gives about 8
  times; `_growth.py` explains why the comparison does not depend on the
  machine's speed). The cases cover Citry's own `cache/...` routes, routes
  with two and three parameters in one segment, routes with
  `dotless_params`, and the three ways the matcher splits a segment (a
  search from the right, a split at each `.`, and a general walk for a
  dotless parameter followed by other text). The longer input in each pair
  runs from 8,000 to 80,000 characters, and the shorter one is an eighth of
  it. The same test file also checks parent and child routes defined by an
  extension.
- **Refusal at mount.** `test_route_path_rules.py` mounts a parent route
  that ends in a parameter with a child route that starts with one, through
  `asgi_app()`, `wsgi_app()`, the Flask and FastAPI `mount()`, and Django's
  `urlpatterns()`. Each raises `ValueError` and leaves the host app (or the
  Citry instance's mounted prefix) as it was. The `check_route_table` tests
  in `test_route_pattern_linear.py` cover the other shapes: two parameters
  side by side in one path, below a parent, inside a parent's path, and a
  repeated parameter name in one path or across parent and child. Each
  message names the route, and both routes when the join causes it.
- **`reverse()` against the earlier regex.** `test_django_route_reverse.py`
  builds 150 random routes, mounts each once through Citry and once as a
  plain `re_path` with the earlier regex, and calls `reverse()` on both with
  30 random value sets each. Values include empty strings, `/`, `.`, a
  newline, a non-ASCII letter and `%`. The test asserts these results:
  - when every value fits the parameter (not empty, no `/`, and no `.` for
    a dotless parameter), both give the same URL;
  - otherwise Citry's `reverse()` refuses;
  - every URL it returns resolves to the route;
  - positional and keyword values give the same answer.

  It asserts more than 300 URLs built, more than 300 refused and more than
  20 refused where the earlier regex would have built one. Growth tests
  time `reverse()`, and the new regex on its own, with values and URLs from
  1,600 to 20,000 characters.
- **Tests for web framework rules, unchanged.** The existing tests in
  `test_route_path_rules.py` send an extra leading `/`, a path without its
  leading `/`, a path with a doubled `/` inside, a trailing newline and
  HEAD on a POST-only route through each adapter (the code that connects
  Citry to a web framework), and check the handler never runs.
  `test_the_whole_path_must_match` also checks that a trailing newline does
  not reach a route. The pull request does not change
  `match_path_below_mount` or `route_allows_method`, and these tests run
  against the matcher.

The pull request description says the route tests pass on Django 4.2.30,
5.2.19 and 6.0.6, and that ruff and mypy (including `--platform linux`) are
clean.

## Ruled out

- **Slow rejection of a long path:** every adapter matches with one matcher
  (`match_route` for ASGI, WSGI and the preview extension's host,
  `match_route_pattern` for Django). It splits the path at each `/` and
  splits each segment between its parameters with searches that read each
  part of the path a fixed number of times, however long the path is, so no
  regex runs on a request. The growth tests above are the evidence. For the
  `reverse()` cases, the test comments say the earlier regex still finishes
  at 1,600 characters and fails the growth test there.
- **A different answer from the earlier matching:** on the generated
  routes and paths, the matcher agreed with the regex, apart from routes
  it refuses. Where a segment can split in more than one way, the earlier
  parameter takes as much as it can: `files/a.b.c` gives `name="a.b"`
  and `ext="c"`.
- **A route that skips the mount check:** `_parse_route_path` runs the same
  check, so a route table that was never mounted, or one matched with
  `match_route` directly, raises on every request for a route with
  adjacent parameters. The test
  `test_a_route_that_skipped_the_check_is_refused_on_every_request` covers
  it.
- **A path reaching a route it should not:** the matcher compares the path
  text exactly. A trailing newline, a doubled `/` and a missing leading `/`
  match nothing, as in the web framework rule tests above.
- **Request data choosing what is cached or compiled:** `_parse_route_path`
  is cached by route path and `dotless_params`. Its callers are
  `match_route`, which passes paths from the route table,
  `match_route_pattern`, which the Django pattern calls with the path it
  was built with, and `route_reverse_regex`, which also reads a route
  path. A request path never reaches that cache.
- **`reverse()` building a URL from values the route refuses:**
  `_ReverseConverter` refuses an empty value, a value with `/`, and a value
  with `.` for a dotless parameter. A value that holds the text following
  another parameter can still change how the route reads the URL (see the
  follow-ups). Django's `reverse()` also uses a regex group that cannot
  retry other splits for each parameter, so building and checking the URL
  takes time in step with its length.
- **A route nobody can read back:** two parameters side by side are refused
  when the routes are mounted, so no route has to guess where one value
  ends. A repeated parameter name is refused the same way.
- **A wrong `dotless_params` type:** `URLRoute` raises `TypeError` at
  construction unless it is a `frozenset` of names.

## Fixed during the review

Nothing recorded.

## Not tested

- **The case of a parent `re_path`, which is unproven.** The pull request
  description records one case as unproven: an app author's own parent
  `re_path` (Django's function for a pattern written as a regular
  expression) that refuses its own text but matches a longer prefix, which
  reaches into the part of the URL that Citry's route handles. No test in
  the pull request covers it, and this record does not claim it is safe.
  The tests that mount Citry below a parent use a parent `path()`, not a
  `re_path`.
- Timing on short inputs. When the shorter run in a growth test takes less
  than a millisecond, `_growth.py` compares the longer run with a fixed
  bound of 24 milliseconds, which rejects the slow code these tests guard
  against but not a small slowdown.
- Django versions other than the three the pull request lists, and Flask
  and FastAPI versions (the mount tests skip when the framework is not
  installed).

## Follow-ups

- No public issue tracks the unproven parent `re_path` case yet.
- `reverse()` can still return a URL that the route reads as different
  values, when a value holds the text that follows another parameter. For
  `{name}-{ver}`, a `ver` that holds a `-` can be read back as a longer
  `name` and a shorter `ver`. The route does accept the URL, and the limit
  is described in the `_ReverseConverter` docstring in
  `packages/py/citry/citry/contrib/django.py`. It is not in the user docs.
