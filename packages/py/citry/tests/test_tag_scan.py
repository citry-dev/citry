"""
Tests for ``scan_document_tags``: which ``</head>``, ``</body>`` and ``<body>`` tags it reports.

Citry places CSS and JS at the tags this scan reports, so a reported tag
must be one the browser reads as a tag. Text that only looks like a tag
(inside an attribute value, a comment, or raw text) must never be reported.
Where the browser's reading depends on the surrounding element, the scan
reports only tags that every reading agrees on.
"""

from __future__ import annotations

import pytest

from citry.util import _tag_scan
from citry.util._tag_scan import scan_document_tags

DOC = "<!doctype html><html><head>{head}</head><body>{body}</body></html>"


def _ends(html: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    tags = scan_document_tags(html)
    return tags.head_ends, tags.body_ends


def _real(html: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    # The real tags of a page built from DOC are the ones DOC writes; every
    # other copy is the decoy under test.
    return (html.index("</head><body>"),), (html.rindex("</body></html>"),)


def test_plain_document() -> None:
    html = DOC.format(head="<title>t</title>", body="<p>x</p>")
    tags = scan_document_tags(html)
    assert (tags.head_ends, tags.body_ends) == _real(html)
    assert tags.body_starts == ((html.index("<body>"), html.index("<body>") + len("<body>")),)
    assert tags.is_document


@pytest.mark.parametrize(
    "body",
    [
        # An interactive page writes < and > raw in attribute values.
        '<div title="</head></body>">x</div>',
        "<div title='</head></body>'>x</div>",
        '<div data-x = "</head></body>">x</div>',
        '<div a="1"b="</head></body>">x</div>',
        "<!-- </head></body> -->",
        "<!-- a --!> <p>x</p>",
        "<!x </head> >",
        "<? </body> ?>",
        "</ </body> >",
        "<textarea></head></body></textarea>",
        "<title></head></body></title>",
        "<style>a::after { content: '</head></body>'; }</style>",
        "<xmp></head></body></xmp>",
        "<iframe></head></body></iframe>",
        "<noembed></head></body></noembed>",
        "<noframes></head></body></noframes>",
        '<script>var a = "</head></body>";</script>',
        # After "<!--" a "<script>" makes the next "</script>" part of the text.
        "<script><!--<script></script></head></body>--></script>",
        # The end tag of a raw-text element can carry attributes.
        '<textarea>x</textarea title="></head></body>">',
    ],
)
def test_decoys_in_a_document_are_not_reported(body: str) -> None:
    html = DOC.format(head="", body=body)
    assert _ends(html) == _real(html)


@pytest.mark.parametrize(
    "html",
    [
        '<div title="</head>x</body>">x</div>',
        "<!-- </body> -->",
        '<p title="</HEAD>"></p>',
    ],
)
def test_a_fragment_with_only_decoys_reports_nothing(html: str) -> None:
    assert _ends(html) == ((), ())
    assert not scan_document_tags(html).is_document


def test_letter_case_and_whitespace_follow_the_browser() -> None:
    html = '<!DOCTYPE html><HTML><HEAD></HEAD ><BODY><div title="</body>"></div></Body\n></HTML>'
    assert _ends(html) == ((html.index("</HEAD"),), (html.index("</Body"),))
    # "</headx>" is a different tag, and only ASCII letters match without case.
    assert _ends("<!doctype html></headx></bodyx>") == ((), ())


def test_only_ascii_letters_fold_case() -> None:
    # U+017F (long s) folds to "s" in Unicode, but browsers read "<\u017fcript>"
    # as an unknown element, so the "</body>" after it is a real tag.
    html = "<!doctype html><html><body><\u017fcript></body></html>"
    assert _ends(html) == ((), (html.index("</body>"),))


@pytest.mark.parametrize(
    "body",
    [
        # Inside SVG, <title> is read as markup, so its "</title>" here sits
        # in an attribute value and the decoy follows it.
        '<svg><title><a x="</title></body>"></a></title></svg>',
        # In <select> and after <template><col>, <style> may be ignored.
        '<select><style><option title="</style></body>"></option></style></select>',
        '<template><col><style><p title="</style></body>"></p></style></template>',
        # Without scripting, <noscript> content is markup.
        '<noscript><p title="</noscript></body>"></p></noscript>',
        # In SVG, CDATA ends at "]]>"; in HTML content at the first ">".
        "<svg><![CDATA[ > </body> ]]></svg>",
    ],
)
def test_context_dependent_raw_text_reports_only_agreed_tags(body: str) -> None:
    html = DOC.format(head="", body=body)
    assert _ends(html) == _real(html)


def test_readings_agree_again_after_ordinary_svg() -> None:
    # Both readings of "<title>Close</title>" end at the same place, so the
    # real "</body>" after it is still found.
    html = DOC.format(head="", body="<svg><title>Close</title><style>.a{}</style></svg>")
    assert _ends(html) == _real(html)


def test_a_fragment_may_be_inserted_anywhere() -> None:
    # Without a doctype or <html>, a fragment may land inside SVG, so its
    # <title> may be markup and the decoy stays unreported.
    html = '<title><a x="</title></body>"></a></title>'
    assert _ends(html) == ((), ())


@pytest.mark.parametrize(
    "html",
    [
        '<!doctype html><div title="never closed></body>',
        "<!doctype html><!-- never closed </body>",
        "<!doctype html><script> never closed </body>",
        "<!doctype html><plaintext></body>",
    ],
)
def test_nothing_after_an_unclosed_construct_is_reported(html: str) -> None:
    assert _ends(html) == ((), ())


def test_too_many_readings_report_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    # Past the limit on readings followed at once, the scan reports nothing
    # rather than guess. Two readings of one <style> already pass a limit of 1.
    monkeypatch.setattr(_tag_scan, "_MAX_READINGS", 1)
    html = DOC.format(head="", body="<svg><style><p></p><style></style></style></svg>")
    assert _ends(html) == ((), ())
