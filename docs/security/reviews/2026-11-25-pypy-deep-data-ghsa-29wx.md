# Deeply nested event data on PyPy (GHSA-29wx)

- **Advisory:**
  [GHSA-29wx-2wvw-8962](https://github.com/citry-dev/citry/security/advisories/GHSA-29wx-2wvw-8962),
  published 2026-11-25, severity medium (CVSS 3.1 score 5.9)
- **Affected and fixed versions:** `citry >= 1.0.0, < 1.3.0`; fixed in
  1.3.0
- **Fix:** the commits from `4a3994467` to `f51d2ef1b`, merged to `main`
  2026-11-25 with the other 1.3.0 security fixes in `31bc11ef5`
  ([#881](https://github.com/citry-dev/citry/pull/881)). On Python
  implementations other than CPython, such as PyPy, Citry's check of
  event data and State writes counts each level where Pydantic runs
  Python code, and allows 32 levels in place of 64. Defining a
  component raises `ValueError` for the few schema shapes the count
  cannot bound. CPython keeps the rules it had.
- **Reviewer:** separate reviewing agents, in seven rounds on the fix,
  plus a read of the docs, changelog and advisory text as a first-time
  reader
- **Code:** `packages/py/citry/citry/ext/events/_pydantic_bounded.py`
  (the counted copy of the data check, `SMALL_STACK_CHECK_DEPTH`,
  `serializer_return_loop`); tests in
  `packages/py/citry/tests/test_events_pydantic_bounded.py`

## Who controls the input

An event handler is a Python function that the browser calls. Before
one runs, Citry checks the call's data against the handler's Pydantic
`data` class (the class that declares the call's data), and it checks
each browser write to State (the data a component keeps between calls)
the same way. The check answers with a 422 when the data nests
too deeply.

- **The data.** Anyone who can call the event supplies it, in a request
  of under 1 KB.
- **The schema.** The app author writes the `data` class and the State
  fields. Only schemas with a recursive type (a type that contains
  itself) whose levels Citry's count skipped were affected: either
  Pydantic calls Python code at each level, as for `Sequence[...]`,
  `OnErrorOmit[...]` or a serializer function, or the levels sit inside
  `Json[...]` text.

What was at risk is the server process, not the page. PyPy lets each
thread use a fixed amount of stack, and when Pydantic's compiled code
uses it up, PyPy ends the whole process instead of raising an error.
Citry's nesting count missed some of those Python calls, so data below
the limit could end a PyPy server. CPython raises an error in the same
place, and Citry answers it.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches none: no value reaches the browser by a new route.
The risk is to the server: one request could end the whole process.

The fix also makes defining a component raise `ValueError`, with a
message that names the type and a way to fix it, for schemas the count
cannot bound: a recursive type inside `Json[...]` without a wrap
validator of its own, a recursive field in a State that Citry checks
only as JSON text, and a serializer whose return type leads into a
recursive type with a serializer of its own.

## How it was checked

- **Interpreter.** PyPy 7.3.23 on Linux with Pydantic 2.14.4, on 1.0.0,
  1.2.0 and the fix, and on 0.8.0. 0.9.0 and the releases from 1.0.1
  to 1.1.1 were read from the release tags.
- **Kinds of input.** About 40 recursive schema shapes, each sent as
  event data, as a State write (lax and strict State), and as event
  data that the handler stores in State, at depths up to the 200-level
  JSON limit. The shapes covered recursive models, list and tuple
  aliases, `Sequence`, `OnErrorOmit`, `Json[...]` text nested in other
  JSON text, and app validators and serializers. Each review round
  looked for a shape that the round before had missed, and the fix grew
  to cover each one found.
- **Margin.** At the limit, the heaviest ordinary accepted shapes used
  at most about 70% of PyPy's stack at the default recursion limit.
- **CPython.** The same data was checked on CPython, with the same
  answers as 1.2.0.
- **Tests.** The new tests run the PyPy rules on CPython, so ordinary CI
  covers them. Each part of the fix was removed in turn to check that a
  test fails without it.
- **CI.** Nothing ran in the private fork, because GitHub Actions does
  not run there. CI ran on the public pull request
  ([#881](https://github.com/citry-dev/citry/pull/881)) before it
  merged.
- **Other frameworks' advisories (Mechanism 8).** Not done: no check
  against the maintainers' survey is recorded for this fix.

## Ruled out

- **CPython.** It is not affected, and the fix changes nothing there.
- **Releases before 1.0.0.** 0.8.0 and 0.9.0 refuse Pydantic event
  classes on PyPy, so they never run the check. Releases before 0.8.0
  do not have this copy of the check.
- **The thread's stack size.** A larger thread stack does not help on
  PyPy, so a server setting cannot be the fix.

## Fixed during the review

Each review round found shapes that the fix of the round before did not
bound, and the fix was extended before it merged:

- recursive types reached through `Json[...]` text, including JSON text
  nested in other JSON text and one long JSON string;
- recursive fields in a State that Citry checks only as JSON text;
- app serializer functions at each level, on the type itself, on a
  reference to it, and in event data that the handler stores in State;
- a serializer whose return type leads into a recursive type with a
  serializer of its own;
- schemas that the first versions of the fix refused although they were
  safe, such as `Json[JsonValue]`;
- tests that could pass without the fix, and wrong margin figures in the
  docs.

## Not tested

- PyPy 8.0, a newer PyPy release for which no `citry-core` wheel exists
  yet.
- PyPy on arm64 and on musl Linux. The margins were measured on amd64
  Linux. Citry ships PyPy wheels only for Linux.
- Python implementations other than CPython and PyPy. Citry applies the
  PyPy rules to them too.

## Follow-ups

- Some schemas can still end a PyPy server below the limit, such as a
  schema with dozens of validators at each level or an app validator
  that checks nested data again. `docs_site/content/security.md`
  ("Event data on PyPy") lists them.
- The maintainers reported to the PyPy project that PyPy ends the
  process when C extension code uses up the stack, where CPython raises
  `RecursionError`.
