"""
The check for HTML that starts like a whole document takes time in step with its length.

The Debug extension asks Citry not to draw its boundary around a render
that is a whole document. Citry decides that by matching the rendered HTML
against a pattern: optional whitespace and a byte order mark, optional
leading comments, then a doctype or ``<html>``. A comment inside a
``<c-for>`` repeats once per data item, so data decides how many comments
the pattern reads. These tests lock which HTML counts as a document and
check that the time grows in step with the length of a long run of
comments.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from citry import Citry, Component
from citry.ext.debug import Debug
from citry.serialize import _looks_like_document

from ._growth import assert_grows_in_step

# A pattern that tries every way of splitting a run of comments takes twice
# as long for each added comment. Twice the comments is therefore enough to
# tell it apart from a check that reads the text once, and the longer run
# still ends quickly instead of hanging the test run.
_FEW_COMMENTS = 10
_TWICE_AS_MANY = 2 * _FEW_COMMENTS
# For the long runs, a child process compares this many comments with eight
# times as many.
_MANY_COMMENTS = 50_000
_GROWTH_FACTOR = 8

_COMMENT_RUNS = [
    lambda count: "<!-- r -->" * count + "x",
    lambda count: "<!---->" * count + "x",
    lambda count: "<!--" + "--><!--" * count + "x",
]


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ("<html>", True),
        ("<HTML lang='en'>", True),
        ("<!DOCTYPE html>", True),
        ("<!doctype html x>", True),
        ("\ufeff <html>", True),
        ("  \n<!-- a -->\n<!-- b -->\n<!doctype html>", True),
        ("<!----><html>", True),
        # Everything from the first `<!--` to a `-->` that a doctype or
        # `<html>` follows counts as leading comments, even text between
        # two comments.
        ("<!-- a --> x --> <html>", True),
        ("<!-- <!-- --> --> <html>", True),
        ("", False),
        ("<html", False),
        ("<htmlx>", False),
        ("<!doctypehtml>", False),
        ("<!doctype html", False),
        ("x<html>", False),
        ("<!-- a --> x <html>", False),
        ("<!-- a --!> <html>", False),
        ("<!--><html>", False),
        ("<!---><html>", False),
        ("<!-- a -->\ufeff<html>", False),
        ("\ufeff\ufeff<html>", False),
    ],
)
def test_document_root_answers(html: str, *, expected: bool) -> None:
    assert _looks_like_document(html) is expected


@pytest.mark.parametrize("build", _COMMENT_RUNS, ids=["comments", "empty-comments", "joined-comments"])
def test_a_run_of_comments_does_not_double_the_time(build) -> None:
    def refuse(html: str) -> None:
        # The input must be one the check refuses, or the timing proves nothing.
        assert _looks_like_document(html) is False

    # Twice the comments may take about twice as long, not a thousand times.
    assert_grows_in_step(refuse, build(_FEW_COMMENTS), build(_TWICE_AS_MANY), factor=2)


def test_long_runs_of_comments_grow_in_step_with_their_length() -> None:
    # A pattern that splits a run of comments in every way would never
    # finish on these, so they run in a child process. The child compares
    # each run with one eight times as long. The process timeout only stops
    # a hang, and is far above what a check that reads the text once needs.
    script = textwrap.dedent(
        f"""
        import sys

        sys.path.append({str(Path(__file__).parent)!r})
        from _growth import assert_grows_in_step
        from citry.serialize import _looks_like_document

        shapes = [
            lambda n: "<!-- r -->" * n + "x",
            lambda n: "<!---->" * n + "x",
            lambda n: "<!--" + "--><!--" * n + "x",
            lambda n: "<!--" + "-->" * n + "x",
            lambda n: "<!--" + "--> " * n + "<htm",
            lambda n: "<!--" * n + "x",
        ]

        def refuse(html):
            assert _looks_like_document(html) is False

        few, many = {_MANY_COMMENTS}, {_GROWTH_FACTOR * _MANY_COMMENTS}
        for shape in shapes:
            assert_grows_in_step(refuse, shape(few), shape(many), factor={_GROWTH_FACTOR}, repeats=3)
        """
    )
    subprocess.run([sys.executable, "-c", script], check=True, timeout=120)


def _debug_app() -> Citry:
    return Citry(
        extensions=[Debug],
        extensions_defaults={"debug": {"highlight_components": True, "highlight_slots": False}},
        autodiscover=False,
    )


def test_debug_boundary_around_comments_from_data_is_quick() -> None:
    app = _debug_app()

    class Rows(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return {"items": kwargs["items"]}

        template = """
            <c-for each="x in items"><!-- r --></c-for>x
        """

    def render(count: int) -> None:
        html = str(Rows(items=list(range(count))))
        # Not a document, so Debug draws its boundary around it.
        assert html.startswith('<div class="citry-debug citry-debug-component"')
        assert html.count("<!-- r -->") == count

    # Twice the items may take about twice as long, not a thousand times.
    assert_grows_in_step(render, _FEW_COMMENTS, _TWICE_AS_MANY, factor=2)


def test_debug_omits_boundary_around_document_after_comments_from_data() -> None:
    app = _debug_app()

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return {"items": kwargs["items"]}

        template = """
            <c-for each="x in items"><!-- r --></c-for>
            <!doctype html>
            <html><head></head><body>page</body></html>
        """

    html = str(Page(items=list(range(50))))
    assert "citry-debug" not in html
    assert html.lstrip().startswith("<!-- r -->")
