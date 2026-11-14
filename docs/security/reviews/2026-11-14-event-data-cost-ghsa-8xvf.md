# The cost of checking event data and State writes (GHSA-8xvf)

- **Advisory:**
  [GHSA-8xvf-qw9c-538m](https://github.com/citry-dev/citry/security/advisories/GHSA-8xvf-qw9c-538m),
  published 2026-11-14, severity high (CVSS 3.1 score 7.5)
- **Affected and fixed versions:** `citry >= 0.3.0, < 0.8.0`; fixed in
  `citry` 0.8.0
- **Fix:** `1331565fa`. Events (Citry's extension that lets the browser call
  Python event handlers) checks event data and State writes (the browser's
  changes to the values a component keeps between calls) with limits on
  errors, size, nesting depth and checking time. It uses a copy of each
  Pydantic validator (Pydantic is the Python library that checks the data)
  that stops at the first bad item. Two parts of the fix landed in a later
  commit, `8d57d1799`:
  - It checks the items of `Iterable[...]` and `Generator[...]` fields
    before the handler runs.
  - It refuses, when the component is defined, a State that Citry can read
    only as JSON text if a writable field holds a recursive class (one
    that refers to itself) without a wrap validator.
- **Reviewer:** separate reviewing agents, in eleven rounds
- **Code:** in `packages/py/citry/citry/ext/events/`:
  `_pydantic_bounded.py` (the copies and the limits: `checker_for`,
  `fields_checker_for`, `WorkBudget`, `request_work`, `validation_scope`,
  `check_state_class`, `pydantic_v1_model_in`), `schemas.py`
  (`check_no_pydantic_v1`), `state.py` (`restore_state`,
  `check_changed_state`), `tokens.py`, `dispatcher.py`, `errors.py`,
  `extension.py` and `openapi.py`; `packages/py/citry/citry/attrs.py`; and
  `check_json_depth` in `packages/py/citry/citry/_protocol/events/issues.py`
  and in its protocol copy
  `packages/protocol/events/v1/python/citry_events/issues.py`. Tests, in
  `packages/py/citry/tests/`: `test_events_pydantic_bounded.py`,
  `test_events_pydantic_v1_data.py`, `test_json_depth_limit.py`,
  `test_events_tokens.py`, `test_events_schemas.py`,
  `test_events_dispatch.py`, `test_events_actions.py`,
  `test_events_routes.py`, `test_events_openapi.py` and `test_attrs.py`

## Who controls the input

Before an event handler runs, Citry checks the call's data against the
schema the app declared, and it checks the browser's writes to State the
same way. Pydantic could need memory or CPU time far out of proportion to
the size of the request. One small request from any visitor could then
slow down or stop a server worker.

Three kinds of input reach these checks:

- **Event call data.** Anyone who can call the event sends it.
- **State writes.** Anyone who can write a State field sends them. Every
  public field is writable unless the component sets `_model`, the list of
  State fields the browser may change.
- **Saved State.** On each call, Citry rebuilds State from its saved values
  and checks them again. The browser first supplied the values it wrote, and
  the app's own code supplied the rest.

The app's Python code supplies the schema, so it decides which shapes are
costly: many required fields, long messages, a union (a field that accepts
several types) inside a type that refers to itself, `pydantic.v1` models
(the Pydantic 1 interface that Pydantic 2 still ships), and fields typed
`Iterable[...]`. It also supplies its own validators, and Citry cannot
limit what those do. What is at risk is the server's memory and CPU time,
and the size of the 422 (validation error) response. The fix writes no
new content into the page.

## How it was checked

Eleven rounds of review by separate agents read the change as it grew.
Two changes came after the last round read the code:

- `1331565fa` refuses a `pydantic.v1` class inside a Pydantic v2 State
  when the component is defined.
- `8d57d1799` is the later commit described under "Fix".

"Not tested" says what covers them. The reviewers sent real requests
through WSGI (the standard Python web server interface), one fresh
process per case, and measured peak memory growth and CPU time. They ran
on macOS with Python 3.14.9, against Pydantic 2.14.1 and 2.13.0, and
compared each case with citry 0.7.0 and with the latest commit the
previous round had read. The probes in each round covered:

- the shapes that the advisory lists, and the same shapes as State writes,
  as saved State, inside `Json[...]` fields (a Pydantic type that reads a
  field's value from JSON text), under wrap validators (validators that
  receive the value and the next validator), and in Citry's own check for
  plain dataclasses;
- valid data of ordinary size, to see that the limits do not refuse it;
- a request of 16 calls, forms, threads and asyncio tasks.

The reviewers also compared the copy of the validator with the class's own
validator on generated payloads:

- 16,000 cases of event data and State writes in the first round;
- 25,500 cases per seed (two seeds, which are two random starting values
  for the generated payloads), both Pydantic versions, first in round 3 and
  again in round 4. This harness compared the locations of errors only. It
  found no differences;
- about 96,700 cases per run on `Json[...]` and wrap-validator shapes, two
  seeds, both versions, in round 4, compared by full error list or value.
  Early runs found value differences and a strict-dataclass failure; the
  fixes below closed them. Later runs left only differences in how a set
  of NaN values is ordered and, on Pydantic 2.13.0, cases where the class
  itself raised an error.

Early in the fix, the author ran the 660,000-payload comparison per
Pydantic version that the advisory reports, and 168,784 State-write cases.
The probe table of round 11 measures 13 shapes on 0.7.0 and on the latest
commit that round read, among them the shapes of the advisory's cost table.

The final two rounds read the whole change for problems that should stop it,
and found no code blocker and no must-fix. On the latest commit that
round 11 read:

- The events test files passed in four runs (Pydantic 2.14.1 and 2.13.0,
  each serial and with four parallel workers).
- The whole `packages/py/citry/tests` folder passed on 2.14.1.
- `ruff`, `ruff format` and `mypy` (on macOS and with `--platform linux`)
  were clean, and the docs build had no errors or warnings.

After the `pydantic.v1` refusal, the events tests ran the same four ways
(2213 passed, 1 skipped), and `mypy` and the docs build were clean. One
parallel run on a heavily loaded machine had four timing tests fail, and
all passed on two reruns. The author also broke the `pydantic.v1` limits
in 14 deliberate ways, and each time a test failed as it should.

The reviewers also checked the change against the kinds of bug that other
frameworks have published advisories for, as `CLAUDE.md` asks (Mechanism 8):
slowdown and memory growth from small inputs, crashes, body size, cached
values shared between requests or calls, error text and source exposure,
and log injection. Kinds about page content, URLs, scripts, redirects and
headers do not apply, because the change writes only fixed error text.
Separate agents also read the docs and changelog text of the change several
times, as a first-time reader.

## Ruled out

- **A budget or State that leaks between requests or calls.** The work
  budget (a cap on how much data Citry may read again while it checks one
  request) and the time limit belong to one request. A thread or task started
  during a request does not keep its budget after the request ends. Three
  calls with the same saved `pydantic.v1` State, where the first handler
  changed the State in place, each saw the saved values.
- **Many calls multiplying the limit.** The calls of one request share one
  budget. A request of 16 calls with a deep union took 0.59 seconds,
  against 0.43 for one call, so the budget is shared, not multiplied.
- **A browser value reaching an unchecked step.** Two rounds looked for a
  path by which browser-written values reach the rebuild or restore
  without first passing a limited check, and found none in the code then
  reviewed. A later round found one remaining case: State fields that
  call a `pydantic.v1` model from inside a Pydantic v2 State. Citry now
  refuses the forms it can see when the component is defined. A
  `pydantic.v1` call hidden in the app's own function stays under "Limits
  that remain" in the advisory.
- **The `pydantic.v1` limits reaching other code.** To count v1 errors and
  read the clock, Citry temporarily replaces functions inside `pydantic.v1`
  while one of its checks runs. A plain `pydantic.v1` check that another
  thread ran at the same time got v1's own result. The replaced functions
  were put back on every way a check can end: too many errors, an error in
  an app validator, running out of Python frames, and running out of time.
- **A server error or leaked exception text from browser data.** The last
  round found none, on macOS with Python 3.14.9. No thread stack size is
  recorded, and no 128 KiB thread stack run is on file. The 422 text is
  fixed, and class names appear only in logs. Warnings name the class,
  not the data.
- **A stored value that differs from the class's own.** The last round
  found none for valid data, and the comparisons with the class's own
  validator above agree.
- **The time limit applying to one thread only.** The limit counts CPU time
  per request under threads and under asyncio.
- **Tests that pass alone and fail in `scripts/check.py`.** A round found
  two tests that failed when run in parallel, as `scripts/check.py` runs
  them. They were made steady, and the later full runs passed.

## Fixed during the review

The rounds found problems in the fix itself, and each was corrected before
the fix merged. Many were shapes that the early versions of the fix still
left costly. The advisory covers those shapes too, because the same cost
existed in 0.7.0. The kinds were:

- **Errors the limit did not count.** Extra keys that the class checks
  against a type (typed extra keys), collections under a wrap validator,
  variable-length tuples under a wrap validator, and items inside
  `Json[...]` read in the copies that cannot count them. Each was
  counted, or refused when the component is defined.
- **Work the budget did not charge.** The budget counted entries, not the
  work below them. Long strings that a check parses cost far more than the
  early charge assumed. A CPU-time ceiling was added as a backstop, and the
  charge was changed to follow the size of what each check reads.
- **Memory the fix itself added.** The cache of measured sizes grew with the
  payload in several shapes. It now keeps a bounded set of entries.
- **Valid data refused or changed.** A strict Pydantic dataclass failed on
  every call. Validators that signal "omit this item" or "use the default"
  were refused. A wrap validator that catches the inner error and carries on
  saw different errors than with the class. Some unions of scalar types read
  a value differently from the class. Validators that read `info.data` or
  `info.field_name` broke every browser write to a Pydantic dataclass State.
  Each was fixed and has a test.
- **Saved State.** Restoring State ran the class's own check on values the
  browser had written, so a value that was cheap to write stayed costly on
  every later call. Restore and the check of changed State now go through
  the copy.
- **`pydantic.v1`.** An early version of the error limit refused valid data
  inside a v1 union as too many errors. The rounds also found v1 gaps that
  exist in 0.7.0 and that the advisory lists: a recursive v1 union
  rechecking the same list at each level, a v1 check behind a Pydantic v2
  validator with no bound, and checks of a written v1 State and of its
  restores outside the limits. Each now counts toward the limits.
- **Claims in the docs and changelog that the code did not support**, found
  in several rounds, such as how often a State is restored in one request.

## Not tested

- **Other platforms and Python versions.** The review ran on macOS with
  Python 3.14.9. Linux, CI timing, Python 3.11 to 3.13, free-threaded Python
  and gevent were not covered.
- **A real browser.** The change writes only fixed error text, so no round
  used one.
- **A shared cache backend.** Server-stored State was tested with an
  in-memory cache, not Redis or memcached.
- **Other Pydantic versions**, such as 2.14.3.
- **Larger token sizes** for a Pydantic v2 State with a field checked by a
  `pydantic.v1` method.
- **`pydantic.v1` cost end to end.** A recursive v1 type failed to build on
  Python 3.14.9, so one v1 cost claim rests on a unit probe and a code read.
- **The `pydantic.v1` refusal in a Pydantic v2 State.** Its evidence here
  is its tests, a rerun of the probes, the test runs above and a read of
  its text by a separate agent.
- **`8d57d1799`.** The eleven rounds read the fix before this commit. Its
  evidence in this record is its tests, such as
  `test_the_items_of_an_iterable_field_count_toward_the_nesting_limit`.
- **Limits the advisory names.** The checks that stay outside the limits:
  work that app validators do, one long check running past the time limit,
  and a restore of a `pydantic.v1` State that runs to its end. Reviewers
  measured some of them; the advisory lists all of them.

## Follow-ups

- The advisory and the fix describe a nesting limit of 32 levels. Since
  [#653](https://github.com/citry-dev/citry/pull/653), checks run on threads
  that Citry starts, and the limit is 64 there. That is on `main`, not in
  0.8.0, which uses 32. It is 32 where no such thread can start, as in
  Pyodide (Python in the browser).
