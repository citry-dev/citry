# Document check for HTML with many leading comments (GHSA-xg8c)

- **Advisory:**
  [GHSA-xg8c-rmvr-mj4m](https://github.com/citry-dev/citry/security/advisories/GHSA-xg8c-rmvr-mj4m),
  published 2026-11-14, severity low (CVSS 3.1 score 3.7)
- **Affected and fixed versions:** `citry >= 0.6.0, < 0.8.0`; fixed in
  `citry` 0.8.0
- **Fix:** `5408ee671`. The pattern that tests whether HTML starts like a
  whole document now reads the leading comments in one pass, so its time
  grows in proportion to the length of the HTML.
- **Reviewer:** a separate reviewing agent
- **Code:** `_DOCUMENT_ROOT_RE` and `_looks_like_document` in
  `packages/py/citry/citry/serialize.py` (the function that joins a
  render's finished HTML calls it); `omit_around_document` in
  `packages/py/citry/citry/citry_render.py`; `Debug` in
  `packages/py/citry/citry/ext/debug.py`, which sets it; tests in
  `packages/py/citry/tests/test_document_root_linear.py`

## Who controls the input

An extension can draw a wrapper around a component's output, as the
development-only `Debug` extension does with `highlight_components=True`.
It can also tell Citry to skip the wrapper when the output is a whole HTML
document (`omit_around_document`). Citry decides that with a regular
expression (a pattern the Python `re` module matches against text) that
asks whether the HTML starts with optional whitespace, a byte order mark
(an invisible character that some files start with), any number of
comments, and then a doctype (the `<!doctype html>` line) or an `<html>`
tag. The part of the pattern that matched one comment at a time
backtracked, which means that after a failure it tried every other way of
splitting the text. On HTML that starts with many comments and then does
not match, the time doubled with each comment.

The input is the HTML a render produces:

- The template author writes the comments. Plain data cannot add a
  comment, because Citry escapes it, as the advisory says.
- Data can decide how many times a comment appears. A template that writes
  a comment inside a `<c-for>` (Citry's loop tag) over request data
  repeats it once for each item.
- Only an extension that asks for the check reaches the pattern. `Debug` is
  the only one in Citry (`omit_around_document=True` is set nowhere else in
  `packages/py/citry/citry`). A third-party extension can ask too.

So anyone who controls the length of a list that such a template loops
over, in an app that runs such an extension, controls how long the worker
spends on the check. The cost is server time. The check only decides
whether the wrapper is drawn, so no value reaches the browser differently
through this change. None of the places where values reach the browser,
listed under Mechanism 7 in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
is affected.

## How it was checked

The fix's author and the reviewer each wrote probe programs that compare
the old and new patterns, time the new one, and measure a whole render:

- **Same answers, the author's programs.** One comparison ran both patterns
  on about 5,000,000 random texts built from pieces such as comment
  openers and closers, dashes, spaces of several kinds, a byte order mark,
  doctype and `<html>` fragments, and letters that change when matching
  upper and lower case. It kept the number of comment openers small, so
  the old pattern stayed fast and could serve as the reference answer. A
  second comparison tried every sequence of up to seven pieces from a list
  of ten (11,111,111 sequences). Each prints any input where the two
  patterns disagree. Neither found a difference.
- **Same answers, the reviewer's program.** An independent comparison used
  random characters (including spaces from many scripts and characters that
  change when matching upper and lower case), random pieces, and structured
  inputs of a prefix, comment-like text and a root tag, again with few
  comment openers. It ran about 4,450,000 inputs, with no difference.
- **Time on hard inputs.** A reviewer's timing program built families of
  text meant to make a pattern backtrack and timed the new pattern at
  10,000, 100,000 and 1,000,000 characters (with an option for 4,000,000).
  The families were runs of closers, runs of openers, runs of dashes, runs
  of spaces and byte order marks, and near misses of a doctype and of
  `<html>` after many closers. An author's program timed similar shapes at
  growing sizes up to 80,000 repetitions. A pattern that reads the text
  once roughly doubles its time when the text doubles, and the new pattern
  did in every family. The author recorded
  50,000 comments in under 1 ms and 4,000,000 characters of the slowest
  shape (leading whitespace) in 0.12 s.
- **Time on ordinary documents.** The reviewer timed documents of 100,000 to
  10,000,000 characters with the old and the new pattern: a document after
  one comment, a document with no comment, and a comment followed by another
  tag. The numbers are not recorded.
- **A whole render.** The reviewer built a component that includes itself 50
  to 400 levels deep, with a comment at each level, and timed the
  serialization step (the step that joins the HTML) with `Debug` on, using
  the new pattern, the old one, and no check, so the cost of the check could
  be compared with the rest of the work. The new pattern was about 4 times
  faster than the old one there. Another reviewer program showed that a
  component with State and a Vue binding under `Debug` does reach the check.
- **The fix's tests**, in `test_document_root_linear.py` (as at commit
  `45e44a7a3`; pull request
  [#634](https://github.com/citry-dev/citry/pull/634) later made the
  timing tests steadier on slow machines):
  - `test_document_root_answers` pins the expected answer for 21 inputs:
    documents after whitespace, a byte order mark or comments, and near
    misses such as `<html` without its end, `<htmlx>`, a doctype without
    `>`, a comment closed with `--!>`, and a comment written as `<!-->`.
  - `test_a_run_of_comments_does_not_double_the_time` refuses runs of 10
    and 20 comments in three shapes and fails if doubling the comments
    more than about doubles the time.
  - `test_long_runs_of_comments_grow_in_step_with_their_length` runs six
    shapes of 50,000 and of 400,000 comments in a child process and fails
    if eight times the text takes much more than eight times as long. A
    timeout of 120 s only stops a hang.
  - `test_debug_boundary_around_comments_from_data_is_quick` and
    `test_debug_omits_boundary_around_document_after_comments_from_data`
    render a `<c-for>` of template comments through `Debug`, once for
    output that is not a document (the wrapper is drawn) and once for a
    document that follows the comments (the wrapper is skipped).
  - On the old pattern the answer test passes and the timing tests fail.

## Ruled out

- **A change in which HTML counts as a document.** The advisory says the
  fix accepts exactly the same documents as before. The 21 answers in
  `test_document_root_answers` include a case the new pattern keeps on
  purpose: text between two comments counts as part of the leading comments
  when a doctype or `<html>` follows, as it did under the old pattern, so
  the fix changes only the speed. The comparison programs above were
  written to find any other difference, and found none.
- **Other extensions in Citry that skip the wrapper.** Only `Debug` sets
  `omit_around_document=True`.

## Fixed during the review

- **The timing tests could hang on a regression.** The reviewer found that
  on the old pattern they could run for a very long time instead of
  failing. The long runs now go in a child process with a timeout
  (`test_long_runs_of_comments_grow_in_step_with_their_length`, named
  `test_long_runs_of_comments_finish_quickly` at the fix commit), and the
  other timing tests use a small count of comments (25 in the fix commit),
  so a regression fails.

## Not tested

- Third-party extensions that ask for the check. The tests and programs use
  `Debug`, and a direct call to the check.
- Python versions and machines. The pattern runs on Python's own `re`
  module. No run on another Python version or another regular-expression
  engine is recorded.
- Components with State and Vue bindings. They reach the check, and no test
  covers them.
- Data that carries comment markup. The tests repeat a comment that the
  template contains, over a list of plain numbers. None passes `Markup` or
  other values marked as safe HTML through the check.

## Follow-ups

None.
