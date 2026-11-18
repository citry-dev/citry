"""MarkupTreeParser opens and closes elements where a browser does."""

from __future__ import annotations

import time

import pytest

from citry_ui.components._markup_tree import MarkupTreeParser, Namespace


class _PathRecorder(MarkupTreeParser[str]):
    """Record each element as the path of its ancestors, with SVG and MathML names prefixed."""

    def __init__(self) -> None:
        super().__init__()
        self.paths: list[str] = []
        self.unmatched: list[str] = []

    def open_element(self, tag: str, attrs: list[tuple[str, str | None]], namespace: Namespace) -> str:
        label = tag if namespace == "html" else f"{namespace}:{tag}"
        path = "/".join([*(element.value for element in self.open_elements), label])
        self.paths.append(path)
        return label

    def unmatched_end_tag(self, tag: str) -> None:
        self.unmatched.append(tag)


class _Silent(MarkupTreeParser[None]):
    """Keep nothing for each element, so only the parser's own work is timed."""

    def open_element(self, tag: str, attrs: list[tuple[str, str | None]], namespace: Namespace) -> None:
        pass


def _paths(html: str) -> list[str]:
    parser = _PathRecorder()
    parser.feed(html)
    parser.close()
    return parser.paths


# Each expected tree is the one Chromium, Firefox and WebKit build from the
# same HTML in a document body (read with DOMParser), so a change that breaks
# one of these breaks agreement with the browsers.
BROWSER_TREES = {
    "svg-style-holds-elements": (
        "<div><svg><style><g tabindex=0></g></style></svg></div>",
        ["div", "div/svg:svg", "div/svg:svg/svg:style", "div/svg:svg/svg:style/svg:g"],
    ),
    "html-tag-leaves-svg": (
        "<svg><style><span>x</span></style></svg>",
        ["svg:svg", "svg:svg/svg:style", "span"],
    ),
    "font-without-attributes-stays-svg": (
        "<svg><font><b></b></font></svg>",
        ["svg:svg", "svg:svg/svg:font", "b"],
    ),
    "math-annotation-holds-math": (
        "<math><annotation-xml><style><button></button></style></annotation-xml></math>",
        [
            "math:math",
            "math:math/math:annotation-xml",
            "math:math/math:annotation-xml/math:style",
            "math:math/math:annotation-xml/math:style/math:button",
        ],
    ),
    "svg-title-holds-html": (
        "<svg><title><button>x</button></title></svg>",
        ["svg:svg", "svg:svg/svg:title", "svg:svg/svg:title/button"],
    ),
    "foreign-object-style-is-text": (
        "<svg><foreignObject><style><button></button></style></foreignObject></svg>",
        ["svg:svg", "svg:svg/svg:foreignobject", "svg:svg/svg:foreignobject/style"],
    ),
    "math-text-style-is-text": (
        "<math><mi><style><button></button></style></mi></math>",
        ["math:math", "math:math/math:mi", "math:math/math:mi/style"],
    ),
    "html-annotation-style-is-text": (
        '<math><annotation-xml encoding="text/html"><style><button></button></style></annotation-xml></math>',
        ["math:math", "math:math/math:annotation-xml", "math:math/math:annotation-xml/style"],
    ),
    "cdata-in-svg-is-text": ("<svg><![CDATA[<b>]]><g></g></svg>", ["svg:svg", "svg:svg/svg:g"]),
    "cdata-in-html-ends-at-gt": ("<div><![CDATA[ x><span></span>]]></div>", ["div", "div/span"]),
    "void-end-tag-ignored": (
        "<div><link></link><span></span></div><button></button>",
        ["div", "div/link", "div/span", "button"],
    ),
    "br-and-p-end-tags-create-elements": (
        "<div></img></br></p><span></span></div>",
        ["div", "div/br", "div/p", "div/span"],
    ),
    "html-self-closing-stays-open": ("<div><span/></span><i></i></div>", ["div", "div/span", "div/i"]),
    "table-cell-hides-outer-div": (
        "<div><table><tr><td></div><button></button></td></tr></table></div>",
        ["div", "div/table", "div/table/tr", "div/table/tr/td", "div/table/tr/td/button"],
    ),
    "foreign-object-hides-svg-end": (
        "<svg><foreignObject><div></svg><button></button></div></foreignObject></svg>",
        [
            "svg:svg",
            "svg:svg/svg:foreignobject",
            "svg:svg/svg:foreignobject/div",
            "svg:svg/svg:foreignobject/div/button",
        ],
    ),
    "html-end-tag-closes-svg": ("<div><svg></div><button></button>", ["div", "div/svg:svg", "button"]),
    "form-end-tag-keeps-children-open": (
        "<form><span></form></span><button></button>",
        ["form", "form/span", "button"],
    ),
    "second-form-ignored": ("<form><form><span></span></form><i></i>", ["form", "form/span", "i"]),
    "button-closes-button": ("<button>x<button>y</button>", ["button", "button"]),
    "a-closes-a": ("<a href=#>x<a href=#>y</a>", ["a", "a"]),
    "li-closes-li": ("<ul><li>a<li>b<div>c<li>d</ul>", ["ul", "ul/li", "ul/li", "ul/li/div", "ul/li"]),
    "div-closes-p": ("<p>a<div>b</div>", ["p", "div"]),
    "font-color-leaves-svg": ("<svg><font color=red><g></g></font></svg>", ["svg:svg", "font", "font/g"]),
    "mglyph-stays-math": (
        "<math><mi><mglyph><b></b></mglyph></mi></math>",
        ["math:math", "math:math/math:mi", "math:math/math:mi/math:mglyph", "math:math/math:mi/b"],
    ),
    "p-end-tag-leaves-svg": ("<svg><g></p><i></i></svg>", ["svg:svg", "svg:svg/svg:g", "p", "i"]),
    "textarea-is-text": ("<div><textarea></div><b></textarea><i></i></div>", ["div", "div/textarea", "div/i"]),
    "marked-section-ends-at-gt": ("<div><![if x]><b></b><![endif]></div>", ["div", "div/b"]),
    "image-is-img": ("<div><image src=x><span></span></div>", ["div", "div/img", "div/span"]),
}


@pytest.mark.parametrize(("html", "expected"), list(BROWSER_TREES.values()), ids=list(BROWSER_TREES))
def test_the_parser_builds_the_tree_a_browser_builds(html: str, expected: list[str]) -> None:
    assert _paths(html) == expected


def test_the_parser_reads_the_html_when_fed_in_pieces() -> None:
    html = "<div><svg><style><g tabindex=0></g></style></svg></div>"
    parser = _PathRecorder()
    for character in html:
        parser.feed(character)
    parser.close()
    assert parser.paths == BROWSER_TREES["svg-style-holds-elements"][1]


def test_an_end_tag_that_matches_nothing_open_is_reported_unless_the_browser_always_ignores_it() -> None:
    parser = _PathRecorder()
    parser.feed("</div></link></span><b></b>")
    parser.close()
    # ``</link>`` closes nothing in any page; the other two could close an
    # element outside the HTML the parser read.
    assert parser.unmatched == ["div", "span"]


def test_an_end_tag_hidden_by_a_scope_limit_is_ignored_not_reported() -> None:
    parser = _PathRecorder()
    parser.feed("<table><tr><td></div><b></b>")
    parser.close()
    # The cell hides any ``<div>`` outside it, so the browser ignores the end
    # tag whatever surrounds the HTML.
    assert parser.unmatched == []
    assert parser.paths[-1] == "table/tr/td/b"


def test_end_tags_take_time_in_proportion_to_the_input_not_its_depth() -> None:
    # Each end tag below matches nothing and sits under 20,000 open elements.
    # Walking the open elements for each one would take many seconds.
    depth = 20_000
    parser = _Silent()
    started = time.perf_counter()
    parser.feed("<div>" + "<span>" * depth + "</i>" * depth)
    parser.close()
    assert time.perf_counter() - started < 2
