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
import time

import pytest

from citry import Citry, Component
from citry.ext.debug import Debug
from citry.serialize import _looks_like_document

# Generous, so a slow CI machine never fails a pattern whose time grows in
# step with the length.
_BOUND_SECONDS = 0.5
# A pattern that tries every way of splitting a run of comments takes about
# 2 s for 25 comments, so this count fails the bound quickly instead of
# hanging the test run.
_FEW_COMMENTS = 25
_MANY_COMMENTS = 50_000

_COMMENT_RUNS = [
    "<!-- r -->" * _FEW_COMMENTS + "x",
    "<!---->" * _FEW_COMMENTS + "x",
    "<!--" + "--><!--" * _FEW_COMMENTS + "x",
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


@pytest.mark.parametrize("html", _COMMENT_RUNS, ids=["comments", "empty-comments", "joined-comments"])
def test_a_run_of_comments_does_not_double_the_time(html: str) -> None:
    start = time.perf_counter()
    result = _looks_like_document(html)
    elapsed = time.perf_counter() - start
    # The input must be one the check refuses, or the timing proves nothing.
    assert result is False
    assert elapsed < _BOUND_SECONDS


def test_long_runs_of_comments_finish_quickly() -> None:
    # A pattern that splits a run of comments in every way would never
    # finish on these, so they run in a child process with a time limit
    # and a regression fails the test instead of hanging the run.
    script = textwrap.dedent(
        f"""
        import time
        from citry.serialize import _looks_like_document

        n = {_MANY_COMMENTS}
        inputs = [
            "<!-- r -->" * n + "x",
            "<!---->" * n + "x",
            "<!--" + "--><!--" * n + "x",
            "<!--" + "-->" * n + "x",
            "<!--" + "--> " * n + "<htm",
            "<!--" * n + "x",
        ]
        for html in inputs:
            start = time.perf_counter()
            assert _looks_like_document(html) is False
            assert time.perf_counter() - start < {_BOUND_SECONDS}
        """
    )
    subprocess.run([sys.executable, "-c", script], check=True, timeout=30)


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

    start = time.perf_counter()
    html = str(Rows(items=list(range(_FEW_COMMENTS))))
    elapsed = time.perf_counter() - start
    # Not a document, so Debug draws its boundary around it.
    assert html.startswith('<div class="citry-debug citry-debug-component"')
    assert html.count("<!-- r -->") == _FEW_COMMENTS
    assert elapsed < _BOUND_SECONDS


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
