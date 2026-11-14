# First value of a repeated attribute (#674)

- **Pull request:** [#674](https://github.com/citry-dev/citry/pull/674),
  merged 2026-11-14 (e55f87c97)
- **Reviewer:** none on file in the pull request.
- **Code:** `_first_attribute_occurrences` and `LongReferenceSafeParser`
  in `packages/py/citry/citry/util/html.py`; its users `_IdScanner` in
  `packages/py/citry/citry/_page_ids.py` and `_HostValidator` in
  `packages/py/citry/citry/_vue/serialization.py`; the functions
  `first_attribute_occurrences` and `visible_markup_text` of Citry UI (the
  `citry_ui` component library) in
  `packages/py/citry_ui/citry_ui/components/_validation.py`, and the
  checks in `cdisclosure.py`, `cimage.py`, `clistbox.py`, `ctree.py` and
  `ccommand_palette.py` under `packages/py/citry_ui/citry_ui/components/`;
  tests in `packages/py/citry/tests/test_attribute_numeric_references.py`,
  `packages/py/citry/tests/test_long_character_references.py` and
  `packages/py/citry_ui/tests/test_output_parsers.py`

## Who controls the input

The pull request makes three changes. Citry's checks of rendered HTML read
the first value of a repeated attribute, as the browser does. The parser
waits when a piece of input ends in a lone `&`. Citry UI error messages
write control characters in tag names as escapes.

When a tag repeats an attribute, as in `<div a="1" a="2">`, a browser keeps
the first value and ignores the rest. Python's standard-library HTML reader
(`HTMLParser`) reports every occurrence, and the common way to turn that
list into a lookup, `dict(attrs)`, keeps the last one. A check built that
way can judge a tag by a value the browser never uses.

Citry reads rendered HTML in several places to decide whether to accept it:

- the development warning for an `id` that appears twice on a page;
- the check that Vue's mount element (the `<div>` Vue takes over in the
  browser) is still there exactly once after extensions have changed the
  page;
- the Citry UI components that check the HTML they receive as slot content
  (a fill) after it renders: `CDisclosure`, `CImage`, `CListbox`, `CTree`
  and `CCommandPalette`. They refuse content such as an interactive
  element in a place that must not hold one, or a native popover (HTML's
  pop-up attribute).

The template author writes most of that HTML. The pull request does not
say who else supplies a fill. This record assumes request data or stored
data can reach one, for example HTML an app marks safe with `Markup`. Then
anyone whose text reaches a page can choose which attributes a tag repeats
and in what order. The risk is a wrong verdict: a check that accepts a tag
the browser reads as unsafe, or refuses one that is fine.

Citry releases before 0.9.0 give a check every occurrence of a repeated
name, and Citry UI declares `citry>=0.7.0`, so Citry UI picks the first
value itself.

The third change has its own input: the tag name in an error message. A
name in rendered HTML can hold a control character, and an escape
character in a message would reach the developer's terminal.

## How it was checked

No separate security review is on file in the pull request: it has no
review comments, and its description records no reviewer. This record is
built from the merged diff, the tests and the code on `main`.

The description says the two smaller fixes in the pull request (the split
reference and the escaped tag names) were found while reviewing
[#610](2026-11-14-attribute-numeric-references-610.md). The tests that the
pull request adds, and what they cover:

- `test_output_parsers_read_a_repeated_attribute_as_its_first_value` in
  `citry_ui/tests/test_output_parsers.py` has one case for each changed
  Citry UI check. Each case writes a tag with one repeated attribute, whose
  first value the check refuses and whose second value it accepts. The test
  expects the tag to be refused, and expects it to be accepted with the two
  values swapped. Each case runs twice: with the current
  `LongReferenceSafeParser`, and with the code that keeps only the first
  value switched off, which is how Citry releases before 0.9.0 behave.
- `test_a_repeated_attribute_reads_as_its_first_value` checks that
  `LongReferenceSafeParser` gives one entry per name with the first value,
  whatever the letter case of the name, both for a tag with a numeric
  character reference and for one without. The two kinds take different
  paths through the parser.
- `test_the_id_check_counts_only_the_first_id_of_an_element` and
  `test_the_vue_host_check_reads_a_repeated_id_as_the_browser_does` check
  the `id` warning and the Vue mount check.
- `test_output_parser_messages_show_control_characters_in_tag_names_as_escapes`
  checks five message cases, one for each kind of changed message.
- `test_the_parser_reads_long_references_wherever_the_input_is_split`
  feeds a page with numeric references of thousands of digits in two
  pieces, split at every position except inside the 5,000-digit runs of
  zeros, where it splits at every 1,000th position. That covers a piece
  that ends right after `&`.

The description states that each new test was run against the code without
its fix and fails there. This was not repeated for the record.

## Ruled out

- **Last value winning in a check.** Every changed check in the Citry UI
  components and in the `id` warning reads the first occurrence.
  `LongReferenceSafeParser` does this for a subclass that reads attribute
  values. Citry UI calls its own function as well, so the checks stay
  correct on older Citry releases. Subclasses that never read attribute
  values (`_reads_attribute_values = False`) are not changed.
- **Letter case of a repeated name.** Names come from `HTMLParser`
  already lowercased, so `TITLE` after `title` counts as a repeat, as in
  the browser. A test covers it.
- **Escape sequences from tag names.** `visible_markup_text` writes every
  unprintable character in a quoted tag name as a visible escape such as
  `\x1b`, so the message holds no raw control character.
- **A page read in pieces.** The parser waits for the next piece when a
  piece ends in a lone `&`, as it does after `&#` and digits. Without the
  wait, a split right after `&` in a very long numeric reference raised
  `ValueError`. The root changelog says earlier releases skipped Citry's
  preload links for such a page. The split-at-every-position test covers
  it.

## Fixed during the review

Nothing recorded.

## Not tested

- **A separate review**, including the check against other frameworks'
  security advisories (Mechanism 8 in `CLAUDE.md`). Neither is on file in
  the pull request.
- **Real browsers.** No test in this change loads a page in a browser. The
  tests compare Citry's reading with the rule the pull request states.
- **Real older Citry releases.** Citry UI is tested with the code that
  keeps only the first value switched off, not against an installed Citry
  release before 0.9.0.
- **A limit noted in the code.** `HTMLParser` lowercases names slightly
  differently from a browser, for one non-ASCII letter (U+212A, the Kelvin
  sign). The code comment
  says no check reads a name that this affects.
- **Build and test scripts.** `scripts/vue_render_parity/check.py`,
  `scripts/generate_html_attribute_values.py`,
  `docs_site/_internal/base_path.py` and `docs_site/_internal/assemble.py`
  still use `dict(attrs)` or `dict(tag.attrs)`. The pull request says they
  read Citry's own output and decide nothing about user pages.
- **Two Rust lookups in `crates/citry_html_transform`** do not use the
  browser's rule for repeated attributes. `marker.rs` reads the
  `c-render-id` of a `<template>` placeholder, which the server replaces
  with the child's HTML before it sends the page. `transformer.rs` handles
  the `track_added_attributes_for_tags_with_this_attribute` option, which
  `citry` does not use.

## Follow-ups

None. The pull request leaves the two Rust lookups for a separate change
and names no issue for them. The related review is
[#610](2026-11-14-attribute-numeric-references-610.md).
