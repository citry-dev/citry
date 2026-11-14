# Deep Events data on large-stack threads (#653)

- **Pull request:** [#653](https://github.com/citry-dev/citry/pull/653),
  merged 2026-11-14 (1d8595a9b)
- **Reviewer:** none on file. The pull request has no review comments and
  its description names no separate reviewer, so this record is built from
  the merged change and its tests.
- **Code:** `packages/py/citry/citry/ext/events/_pydantic_bounded.py`
  (`run_on_check_thread`, `_CheckThreads`, `MAX_CHECK_DEPTH`,
  `SMALL_STACK_CHECK_DEPTH`, `validate_json`); the callers that hand work to
  it in `schemas.py` (`validate_args`, `json_value_error`), `state.py`
  (`state_wire_values`, `restore_state`, `check_changed_state`),
  `tokens.py` (State writes from the browser) and `extension.py`
  (`build_state`); tests in
  `packages/py/citry/tests/test_events_pydantic_bounded.py`

## Who controls the input

Events is Citry's way for the browser to call a Python handler. Before a
handler runs, Citry checks the call's data against the handler's class,
written with Pydantic (the Python library that checks data against a
class's types), and it checks a browser write to a component's State (the
values the component keeps between browser calls) the same way.
Anyone who can send a request to the app's Events URLs controls that data,
including how deeply it nests. Citry also reads State back from its signed
token, which holds values the app built or Citry checked earlier.

Each level of nesting takes room on the stack of the thread that runs the
check (the stack is the memory a thread uses for nested calls). A thread
that runs out of stack ends the whole server process, not only the request.
So Citry refuses data that nests more than a set number of levels, and the
number has to fit the smallest thread stack a server might use.

This change runs the checks on a small set of threads that Citry starts,
each with a 16 MiB stack, and sets the limit to 64. Three kinds of input
are involved:

- **The data a request sends:** its depth and shape are the risk, and the
  cost is the process's stability and the server's memory and time.
- **The app's own validators, State serializers and `__post_init__`
  methods:** the app author writes them, and they run on Citry's check
  threads, not on the request's thread.
- **The server's own settings:** the stack size of its request threads, and
  whether the platform lets Citry start threads or set their stack size.

## How it was checked

No review is recorded, so the evidence is the code and the tests that the
pull request adds or changes. Each deep-data test runs in a separate
Python process, because too little stack would end the whole test run.

- **Deep data from a small calling thread.** A thread with 128 KiB of stack
  (the default on musl Linux, a C library some Linux builds use) checks
  data nested 1,000 levels. The cases are a chain of models, a
  self-referencing list type, Pydantic's `Json[...]` text of 1,000
  brackets, and a model whose validator validates again inside itself. It
  also sends a deep browser write to State and a restore of State from
  token values. In these tests every answer is a refusal and the process
  stays up (macOS, Python 3.11 and 3.14).
- **Data at the limit.** Nine data shapes that use the stack differently
  are each built at three depths. The shapes are a wrap validator on a
  field (a validator that wraps Pydantic's own check), wrap validators on a
  model and on its field, a union of models, a union of Pydantic
  dataclasses, a union of plain dataclasses, a list of models, a
  discriminated union (a union whose members carry a tag field), an
  `Iterable` of models, and a union inside an `Iterable`. The depths are
  the deepest the limit accepts (the test finds it for each shape), the
  same with a bad value at the leaf, and one level too deep. All 27 cases
  are checked from a 128 KiB calling thread on check threads whose stack is
  halved to 8 MiB, and each answer must equal the answer from the main
  thread.
- **State round trip.** After a deep State write is accepted, Citry writes
  State out for its token, checks State a handler changed, and builds State
  for a render. A test does all of that for a keep, a change and a render
  handler, from a 128 KiB calling thread, and all three succeed.
- **The handler's side.** A test builds a chain of `MAX_CHECK_DEPTH` models
  on a 512 KiB thread and calls `model_dump()` and `model_dump_json()` (the
  Pydantic methods that turn a model back into plain data) on it, as a
  handler might.
- **The set of check threads.** Unit tests cover the check seeing the
  caller's context variables, a check inside a check, errors that reach the
  caller with their traceback, more callers than threads (with the thread
  limit set to 2), the CPU time of the check thread counting toward the
  request's limit, a child process made by `fork` getting new check threads,
  a platform that cannot start a thread, a platform that cannot set the
  stack size, a failure to set the size back (which is logged), a failure in
  the thread's own loop, and whether a finished or failed check keeps the
  request's data alive.

The pull request description reports 206 passing tests in
`test_events_pydantic_bounded.py`, ruff passing, and mypy passing for macOS
and for `--platform linux`.

## Ruled out

- **A process crash from deeply nested data, in the cases the PR tested:**
  a check runs on a thread with a 16 MiB stack whatever stack the calling
  thread has (tested from 128 KiB). Later commits on `main` changed more
  State paths; this record does not cover them. The code
  comments report that the heaviest shape per level (wrap validators on a
  model and on its field) needs about 14 KB per level on macOS (a Python
  3.11 build), so data at the limit of 64 needs about 0.9 MiB. The
  half-stack test above leaves a large margin.
- **A crash in the check from a stack that Citry did not choose:** where no
  check thread can start (Pyodide, which runs Python in the browser, or a
  platform with no settable stack size), the check runs on the calling
  thread with the lower limit of 32,
  `SMALL_STACK_CHECK_DEPTH`. Tests with a refused stack size and a refused
  thread start show that fallback, and that Citry sets the process-wide
  stack size back right after each start.
- **Deep JSON text reported as plain invalid text:** Pydantic's JSON reader
  refuses text nested past its own limit and calls it invalid.
  `validate_json` turns that one error into the "nested too deeply" answer.
  It does so only when the whole text is refused, not when one `Json[...]`
  field's text is; a test checks the function that tells the two apart.
- **A higher limit giving more work per request:** the work budget, the
  error limits and the CPU time limit are not changed by this pull request.
  Raising the nesting limit only lets valid data nest deeper, inside those
  limits.
- **Unbounded threads or memory:** at most 32 check threads exist
  (`MAX_CHECK_THREADS`), two stay idle, and the others end after 60 seconds
  without work. A check past 32 waits in a queue, and a test shows the third
  caller waits when the limit is 2. An idle thread does not keep the last
  request's data, context or result: tests check this with weak references
  (references that do not keep an object alive), including when the check
  raised.
- **Lost errors and hangs:** a check's exception reaches the caller with its
  traceback. If the thread's own loop fails, the code gives the waiting
  callers an error and gives the thread's place back, so later checks can
  start a new thread. A test covers the case where the check had already
  run: the caller keeps the check's own answer.
- **A check running on a thread with a different CPU clock:** the check
  thread's own CPU time counts toward the request's limit, and a test checks
  the amount with a clock set by hand.
- **Handlers on small server threads:** the handler still receives the
  checked data on the server's own thread, which Citry cannot enlarge. A
  handler that walks data at the limit (`model_dump()` on a chain of
  models, for example) needs room there. The pull request description
  reports about 100 levels in 512 KiB and about 22 in 128 KiB
  (macOS, a Python 3.14 build), so data at the limit of 64 fits in 512 KiB
  but not in 128 KiB for that handler. These figures are the PR's own
  measurements (#653), not current advice. The app's server setup decides
  this, and the security page (`docs_site/content/security.md`) and
  the changelog on `main` now tell the author to give request threads at
  least 2 MiB with `threading.stack_size()`.
- **Validators that block or deadlock:** a validator that waits for the
  network or a database keeps its check thread busy, and one that waits for
  a lock the request's thread holds can deadlock. Only the app author's own
  code can do this, not request data, and the security page says so.

## Fixed during the review

Nothing recorded.

## Not tested

- **Windows, Linux and musl.** The measurements in the code comments and
  the pull request description are from macOS (Python 3.11 and 3.14).
  The description says CI would show the Linux and Windows results. On
  Windows, each thread's 16 MiB counts against the system's commit limit
  (the memory it lets programs reserve) while the thread lives (the
  security page says so); no measurement of that cost is recorded.
- **Real gevent or eventlet** (libraries that replace Python's threads
  with their own). The code reads the original thread functions
  when either library has patched `threading`. The test replaces
  `threading.Thread` with a stub that fails if used, and no test imports
  either library, so the two library-specific branches of
  `_os_thread_functions` are not run.
- **Many real concurrent requests.** The pool is tested with a thread
  limit of 2, not with 32 or more simultaneous requests.
- **The short stack-size window.** While Citry starts a check thread it sets
  the process-wide stack size, then sets it back. The code comment says a
  thread another part of the app starts in that moment also gets the
  16 MiB stack. No test sends concurrent thread starts to measure it.
- **Pydantic v1 classes.** The nesting limit applies to Pydantic v2 checks.
  No new test sends deep data to a Pydantic v1 State.
- **Cost.** The pull request reports 10 to 40 microseconds to hand a check
  to a thread, measured on macOS only. A call that writes State does it
  about a dozen times.

## Follow-ups

None. The limits above are in the docs: request threads need at least
2 MiB, validators run on Citry's threads, and Windows counts each check
thread's stack against its commit limit.
