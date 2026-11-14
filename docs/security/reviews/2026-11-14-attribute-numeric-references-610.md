# Attribute values decoded like the browser (#610)

- **Pull request:** [#610](https://github.com/citry-dev/citry/pull/610),
  merged 2026-11-14 (3adf79d71)
- **Reviewer:** none on file. The pull request carries no review
  comments or report.
- **Code:** `LongReferenceSafeParser` and `decode_attribute_entities` in
  `packages/py/citry/citry/util/html.py`; the parsers built on it:
  `_IdScanner` in `citry/_page_ids.py`, `_HostValidator` and
  `_PreloadHeadLocator` in `citry/_vue/serialization.py`,
  `_PreparedMarkupTracker` in `citry/serialize.py`, and the output parsers
  in `packages/py/citry_ui/citry_ui/components/` (such as
  `_ContentOutputParser` in `cdisclosure/cdisclosure.py`); tests in
  `packages/py/citry/tests/test_attribute_numeric_references.py`,
  `packages/py/citry/tests/test_page_ids.py` and
  `packages/py/citry_ui/tests/test_output_parsers.py`

## Who controls the input

This change makes Citry's HTML parsers decode attribute values as the
browser does, not with `html.unescape`.

HTML can write one character as a numeric character reference, such as
`&#27;` for the character with code 27. Citry reads back the HTML it
renders, to run some of its own checks. That HTML comes from the template
author and from the app's Python code, for example a `Markup` value (text
the app marks as safe HTML). The pull request does not say who supplies
it; this record assumes request data can reach it through `Markup`.

`LongReferenceSafeParser` is Citry's wrapper around Python's `HTMLParser`
(the standard-library HTML reader). It also handles references with
more than 4,300 digits, which Python's `html.unescape` rejects.
`HTMLParser` decodes attribute values with `html.unescape`, which drops
some characters that a browser keeps: the control characters U+0001 to
U+0008, U+000B, U+000E to U+001F and U+007F, and noncharacters (code
points Unicode reserves) such as U+FDD0. So `html.unescape` makes Citry's
parsers read some values differently from the page the browser builds.
The parsers are:

- `_IdScanner`, behind the development warning for an `id` used twice;
- `_HostValidator`, which checks, after the serialization hooks (extension
  code that rewrites the page), that the page still holds exactly one
  empty element with the expected id for Vue to mount on;
- the output parsers of Citry UI (the `citry_ui` component library), which
  reject component output that holds, for example, a `popover` value
  (HTML's pop-up attribute) Citry does not accept.

The Citry UI changelog entry that
[#674](2026-11-14-repeated-attribute-first-value-674.md) added says that
decoding values as the browser does applies "with Citry 0.9.0 or later",
so earlier releases decode these values with `html.unescape`.

If a parser reads a value differently from the browser, a check can pass
on markup the browser reads another way, or refuse markup it reads as
harmless. The change also touches what a developer's terminal receives,
because an `id` read as the browser reads it can hold a control character
that the warning prints.

## How it was checked

No separate review is on file. This record is built
from the merged change, its tests, and the checks the author lists in the
description:

- **Browsers.** Chromium 156 and Firefox 157 each loaded a page with a
  `title` attribute written with each reference in a table, and returned
  the same value for every row. The tests hold that table
  (`BROWSER_READS` in `test_attribute_numeric_references.py`). It covers
  the dropped characters above, the references browsers map to another
  character (`&#x80;`, `&#x9f;`), and references past the end of Unicode or
  in the surrogate range, which read as U+FFFD.
- **Generated tags.** About 6,000 generated start tags, split into
  chunks in many ways, gave the same names as the parser did before the
  change and the same values as a known answer (the description does not
  say where the answer came from). This ran on each of CPython 3.11.15,
  3.11.17, 3.12.15, 3.13.17, 3.14.9 and 3.15.1.
- **Removing safeguards.** The description says that deleting any one of
  five safeguards makes a new test fail: that the tag text lines up with
  what `HTMLParser` read, that the names match, that text already read is
  dropped, the check of the parser's parent classes, and the marker that
  shows a handler was wrapped.
- **Test runs.** The description reports ruff and mypy (also with
  `--platform linux`) clean and the focused `citry` and `citry_ui` suites
  passing.

## Ruled out

- **A different value than the browser reads.** The tests check the
  decoder and the parser against the table for decimal and hexadecimal
  forms, in double-quoted, single-quoted and unquoted values. A named
  reference with no `;`, as in a URL query, stays as typed before `=`, as
  in the browser. A reference with thousands of digits reads correctly,
  including one in an attribute name.
- **A tag split across feeds.** A tag fed in many small pieces, even one
  character at a time, still gets its own values and no other tag's
  (`test_each_tag_gets_its_own_values_however_the_input_is_split`).
- **Decoding going wrong when the parser cannot match a tag to its
  original text.** The parser pairs each name `HTMLParser` found with the
  value read from the original text, and falls back to `HTMLParser`'s own
  values when the pairing does not hold, and nothing reports the
  fallback. Two cases are tested: a Python digit limit that changes while
  a tag is split, and a later Python that lacks the patterns Citry reads
  from `html.parser`.
- **A subclass skipping the browser's values.** A handler defined in a
  subclass body gets the browser's values, including one that calls its
  parent through `super()` (the parent's handler), one that is a copy made
  with `functools.wraps`, and a subclass of a parser that opted out (it
  sets `_reads_attribute_values = False`).
- **Extra cost for the server.** The parser keeps the original text only
  when a handler reads values, and drops the text before the tag it is
  reading. A test feeds 200 long tags in 4,096-character chunks and finds
  the parser holds under three chunks. Parsers that never read values
  (`_PreparedMarkupTracker`, `_PreloadHeadLocator`, and the two Citry UI
  menu and accordion parsers) opt out and keep no text.
- **Two ids that differ by a reference.** `a&#1;b` and `ab` are different
  ids, as in the browser (`test_page_ids.py`). The Vue host check does
  not count an element whose id the browser reads as another value
  (`test_the_vue_host_check_matches_the_id_the_browser_reads`). The
  Citry UI content parser refuses a `popover` value that `html.unescape`
  reads as `manual` but that the browser reads with an extra character
  in it
  (`test_the_content_parser_reads_a_popover_value_as_the_browser_does`).
- **Control characters reaching a terminal.** The repeated-id warning
  writes each unprintable character in an id as an escape (`_visible` in
  `_page_ids.py`). The test uses ESC (the escape character) and checks
  the message holds none.
  The check runs only with `Citry(mode="development")`.
- **Static and interactive pages differing.** A `Markup` value with
  references gives the same attribute on a static page (no component
  script) and an interactive one (the component has a `js` script), on
  both render paths. `class` and `style` pieces keep the character too.

## Fixed during the review

Nothing recorded.

## Not tested

- **A separate review**, including the check against other frameworks'
  security advisories (Mechanism 8 in `CLAUDE.md`). Neither is on file in
  the pull request.
- **Browsers other than Chromium 156 and Firefox 157.** The description
  names no other browser, and the tests do not drive a browser: they hold
  the values the author read.
- **Handlers added later.** A handler set on an instance, or defined by
  a mixin (a class listed before the parser), gets `HTMLParser`'s values,
  not the browser's. The class docstring says so.
- **Text.** With `convert_charrefs=True` (the `HTMLParser` option that
  decodes references in text) the parser still decodes text
  with `html.unescape`, so a reference such as `&#1;` in text reads as
  nothing. The class docstring says so.
- **Readers outside these Python parsers.** The change touches only the
  Python parsers above.
  [#674](2026-11-14-repeated-attribute-first-value-674.md) lists two Rust
  lookups in `crates/citry_html_transform` that read repeated attributes
  differently from the browser. This record did not check them.
- **A tag that repeats an attribute name.** The tests here do not cover
  it; #674 does.
- **Three tests in `tests/test_check.py`** (reserved names in `v-for` and
  `v-slot`) failed in the author's run because the local `citry_core`
  build was older than `main`. The description says they fail the same
  way before this change with that build.

## Follow-ups

- The description says Citry decodes a reference to a carriage return
  (`&#13;`) to a carriage return and writes it as a raw character, and
  that the browser then reads a raw carriage return as a line feed. No
  issue for it is linked in the pull request.
- [#674](2026-11-14-repeated-attribute-first-value-674.md) fixes a failure
  when a chunk ends in a lone `&` and escapes control characters in Citry
  UI error messages.
