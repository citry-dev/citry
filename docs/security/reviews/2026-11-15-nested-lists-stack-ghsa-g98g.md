# Deeply nested Events data and small thread stacks (GHSA-g98g)

- **Advisory:**
  [GHSA-g98g-g2cx-2jf8](https://github.com/citry-dev/citry/security/advisories/GHSA-g98g-g2cx-2jf8),
  published 2026-11-15, severity medium (CVSS 3.1 score 5.9)
- **Affected and fixed versions:** `citry >= 0.3.0, < 0.9.0`; fixed in
  `citry` 0.9.0
- **Fix:** five commits on `main`, built in the advisory's private fork and
  released in 0.9.0. They extend
  [#653](https://github.com/citry-dev/citry/pull/653) (`1d8595a9b`), which
  moved most of the Events checks onto threads that Citry starts itself
  with a 16 MiB stack (its record is
  [Deep Events data on large-stack threads](2026-11-14-bounded-check-threads-653.md)).
  - `ade18b6c3`: Citry writes State fields back for the page on those
    threads too, and its own check of a dataclass or plain `data` class
    counts each object as one level toward the 64-level nesting limit (a
    `data` class is the class that describes an event's data).
  - `8b05ef1f2`: the docs tell servers to give request threads at least
    2 MiB of stack, and correct the thread stack size given for the
    official Alpine Python images.
  - `5b6bceda9`: a State too deeply nested to restore raises the
    documented "nested too deeply" error, so the call answers
    `stale_state` (409) where it used to answer a generic 500. The scan
    that looks for lone surrogates in a State write (broken halves of a
    character, which cannot be written as UTF-8) no longer calls itself
    for each level, so deep nesting cannot use up the request thread's
    stack.
  - `ec35f9927`: makes that scan faster.
  - `21b17136e`: Citry writes a Pydantic model State out as JSON before
    the handler runs, so a write that cannot be written out is refused
    first.
- **Reviewer:** separate reviewing agents, one or more for each stage of
  the fix (code, security and the advisory survey; the stack figures in the
  docs; the advisory text). This record is built from their reports, the
  commits and their tests.
- **Code:** `packages/py/citry/citry/ext/events/_pydantic_bounded.py`
  (`run_on_check_thread`, `counted_level`, `CHECK_STACK_BYTES`), called
  from `emission.py` (`capture_instance`, `_write_plain_values`),
  `schemas.py` (`_validate_object`), `state.py` (`_restore_state`),
  `tokens.py` (`_model_state_check`, `_holds_lone_surrogate`,
  `_quick_lone_surrogate_scan`) and `dispatcher.py`
  (`_too_deep_to_write`), all in the same folder; tests in
  `packages/py/citry/tests/test_events_pydantic_bounded.py`

## Who controls the input

Events is Citry's way for the browser to call a Python handler. Before the
handler runs, Citry checks the call's data, and each browser write to State
(the values a component keeps between calls), against classes written with
Pydantic. Anyone who can call the event controls that data, including how
deeply its lists and dicts nest inside each other.

Pydantic checks nested data through nested function calls, and each call
takes room on the stack of the thread that runs it. A field typed
`pydantic.JsonValue`, or `Any`, accepts nested lists and dicts, and Citry's
nesting limit does not count those levels. Released versions ran these
checks, and the steps that write State out, on the server's own request
thread. On a server whose request threads have a small stack (about 1 MiB
in the official Alpine Python images, for example), one small request could
end the whole process (measured on Python 3.11, and for a model State write
also on 3.14). The advisory lists each case and the stack sizes
that were measured.

The inputs, by who first supplies them:

- **Event data and State writes.** Anyone who can send a request supplies
  them. The fix runs every check, and every step that builds, checks again
  or writes out State, on Citry's own threads.
- **A State token (the signed copy of State that the browser sends back
  with each call).** The server wrote it, so its
  content is the app's own, but the browser sends it back. A token that
  this server cannot restore or write out answers `stale_state` (409)
  before the handler runs.
- **What the handler does with the value.** The app's Python code decides
  this. Code that checks or writes out a deeply nested value again on the
  request thread, such as `model_dump()` or rendering a component whose
  Pydantic `Kwargs` class holds the value, still uses that thread's stack.
  The docs tell servers to give request threads at least 2 MiB of stack,
  and the advisory gives the same advice.

The change reaches the browser only through error answers, so of the
places in the list of where values reach the browser (Mechanism 7 in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser))
it touches only "Responses Citry serves", through the text of those
answers. The risk it addresses is the cost of a request to the server.

## How it was checked

No browser was needed. Every check ran on the server, on macOS on Apple
silicon with Pydantic 2.14, mostly on Python 3.11 and 3.14. The thread
stack sizes were also measured in Linux containers on the same machine.

- **Released versions.** The author installed citry 0.3.0, 0.4.0, 0.5.1,
  0.6.0, 0.7.0 and 0.8.0 and ran the advisory's cases on threads with set
  stack sizes (some cases only on 0.8.0, as the advisory says), to find
  which releases are affected and which stack size is enough. Those runs
  give the figures in the advisory.
- **The fixed code, on small stacks.** The new tests start a separate
  process with a 512 KiB thread and render model and Pydantic dataclass
  State from it, with nested lists and with nested dicts. On the code
  before the fix they end the process on Python 3.11 and fail with a 500
  answer on 3.14.
- **Every Events step.** A separate agent read every other place where
  Events sets, copies, restores, writes out, hashes to see whether it
  changed, signs or caches State, and found each one already on Citry's
  threads or bounded by the 200-level limit on request JSON. Reviewers then
  ran each fixed route on Python 3.11 and 3.14: event data, State writes,
  writing State fields back, tokens, restore, cached renders, and a
  `Kwargs` class that is not a Pydantic class.
- **Every built-in way to send a call.** A reviewer checked that browser
  data cannot reach the restore or the lone-surrogate scan with more
  nesting than the request limit allows, through the JSON envelope, flat
  JSON, form posts, GET tokens, multipart bodies and cached replies.
- **Platforms where Pydantic stops writing JSON at a lower depth.**
  Pydantic stops writing nested values out at a lower depth on Windows,
  PyPy and Pyodide. The tests make Pydantic stop at that depth on
  purpose. The token in those
  tests is made from a plain dataclass, so they also pass on platforms
  where Pydantic really stops there.
- **Stack figures in the docs.** The author measured the thread stack in
  the `python:3.11-alpine`, `python:3.12-alpine` and `python:3.13-alpine`
  images and on macOS, and a reviewer ran the measurements again,
  including `python:3.14-alpine` and an emulated x86_64 image.
- **The lone-surrogate scan's speed.** The author timed the new scan
  against the earlier code on several kinds of State write, up to a
  2.6 MB body. A reviewer compared its answers with `json.dumps` on 200,000
  generated values, including subclasses, enums, NaN, keys that are not
  strings, and tuples.
- **A test checked against removed code.** The test of the level count
  fails when the step that undoes the count after an early stop is
  removed.
- **The author's runs.** The Events, State and token tests passed on
  Python 3.11, 3.12, 3.13 and 3.14 in the author's environments, apart
  from tests that also fail on the code before the fix in those
  environments, because the local Pydantic version differs from the
  locked one or the local `citry_core` build was out of date. `ruff`
  passed, and `mypy` passed with `--platform darwin` and `linux` (and
  `win32` on the last commit).
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks (Mechanism 8 in `CLAUDE.md`) and checked these kinds: crashes
  and work out of proportion to a request, large request bodies, State
  shared between requests, unsafe deserialization, error pages and source
  shown in errors, text written into logs, cache entries and keys, State
  tokens and secrets compared by timing, response headers, and sanitizer
  bypass. The fix introduces none of them.

## Ruled out

- **A check left on the request thread.** The sweep found no other Events
  step that runs Pydantic on browser data on the request thread. Steps
  that run there read data already bounded by the 200-level limit.
  Writing such data out as JSON passed on a 128 KiB thread on Python 3.11
  to 3.14.
- **A `data` class that the depth count skipped.** Citry builds a
  dataclass, plain class or Pydantic dataclass `data` class one object at a
  time with its own code. Each object now counts as one level, so such a
  class stops at the same 64 levels as a chain of models. This refuses
  data that 0.8.0 accepted, and the changelog says so under its upgrade
  notes.
- **The handler running on a State that cannot be saved.** A model State is
  written out before the handler runs, so a write that Pydantic cannot
  write out gets a 422 answer and the handler does not run.
- **Error text in the answer.** When Pydantic cannot turn a written State
  into JSON for a reason other than depth, the call gets the fixed message
  "The State could not be checked." Pydantic's own text, which can name
  the app's classes, goes
  only to the log.
- **A restore error that escapes.** A restore that meets Python's own
  recursion limit (Python 3.11 to 3.13) now raises the documented "nested
  too deeply" error, and the call answers `stale_state` where it used to
  answer a generic 500. Browser data cannot reach this, because only a
  State that the app built and signed can nest that deeply, and a test
  covers such a Pydantic v1 State.
- **The cost of the new scan.** The lone-surrogate scan reads each item
  once and does not recurse. Within the default 1 MiB body limit its worst
  shapes took under 100 ms in the review. A value that holds itself, which
  only a direct caller can pass, goes to a slower scan that reads each
  list and dict once, so it gets a right answer, never a wrong one.
- **Handler code.** What a handler does with a value is the app's own
  code. The security page and the Events design doc say that lists and
  dicts do not count toward the limit, and tell servers to give request
  threads at least 2 MiB.

## Fixed during the review

- The tests did not show that the level count stays balanced when a check
  stops early. A test was added, and it fails without that step.
- The first advisory text had the wrong release range for a Pydantic
  dataclass State, said too little about which Python versions were
  tested, and described the render case wrongly. All three were corrected
  before publication.
- A first version of the restore fix reported a check that stopped for too
  many errors as too deep, and re-raised more than the depth case from the
  v1 write check. Both were narrowed to the depth case. Missing tests for
  the dispatcher and for the cause of the error were added.
- The tests for writing State out failed on platforms where Pydantic
  really stops early, because they made the token with Pydantic. They now
  make it from a plain dataclass.
- When Pydantic could not turn a written State into JSON for a reason
  other than depth, its text went into the answer. The call now gets the
  fixed message.
- The docs said threads on musl Linux have 128 KiB. A thread that Python
  starts in the official Alpine images has about 1 MiB, so the docs were
  corrected, and the 128 KiB figure kept only for threads that Python does
  not start.

## Not tested

- Linux on real hardware, glibc Linux, Windows and PyPy. The Windows and
  PyPy case was run only by making Pydantic stop early on macOS.
- Python 3.12 and 3.13 for most crash figures, and free-threaded Python.
- Rendering a component whose Pydantic `Kwargs` class holds a deeply
  nested value, on Python 3.12 to 3.14.
- Several rounds of wording and small code changes made after a review
  were not reviewed a second time.

## Follow-ups

- A Pydantic `Kwargs`, `Slots` or `TemplateData` class is still built on
  the thread that renders, so a deeply nested `JsonValue` passed into it
  needs a large enough stack there. The maintainer chose to document this,
  and the security page says so.
- Turning State into JSON before the handler runs, and again when Citry
  checks a returned State token, is not counted toward the CPU budget for
  a call. The cost grows with the body size, which the body limit
  bounds.
- Some code comments still say that a Python thread on musl Linux gets
  128 KiB. That is true only for a thread that Python does not start. No
  public issue tracks the correction yet.
