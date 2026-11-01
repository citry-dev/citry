# This same set of tests is also found in django-components, to ensure that
# this implementation can be replaced with the django-components' pure-python implementation

import pytest

from citry_core.html_transform import (
    _JAVASCRIPT_MIME_TYPES,
    _check_output_html,
    _classify_dependency_attribute,
    _csp_attribute_problem,
    _is_javascript_url,
    _script_type_is_executable,
    browser_fragment_matches_nodes,
    mark_html,
    transform_html,
    validate_html_fragment_boundary,
)


def test_strict_fragment_boundary():
    for html in ("", "<div>x</div><br>", "<svg><path/></svg>", "<math><mspace/></math>"):
        validate_html_fragment_boundary(html)
    for html in ("<div>", "</div>", "<div/>", "<li>a<li>b"):
        with pytest.raises(ValueError, match="self-contained strict fragment"):
            validate_html_fragment_boundary(html)
    # A tokenizer error is named by its name in the HTML standard.
    with pytest.raises(ValueError, match=r"^opaque HTML has the HTML parse error eof-in-comment$"):
        validate_html_fragment_boundary("<!-- unfinished")
    # A character reference the browser decodes to text is accepted.
    for html in ("<p>&copy 2026</p>", "<b>a&#127;b</b>", "<b>a&#x80;b</b>", "<p>a&foo;b</p>"):
        validate_html_fragment_boundary(html)


def test_browser_fragment_matches_nodes_reads_every_event_kind():
    marker = [("data-allow-mismatch", "children")]
    html = '<main id="m"><!--[--><aside data-allow-mismatch="children"></aside><!--]--></main>'
    expected = [
        ("open", "main", [("id", "m")]),
        ("comment", "[", []),
        ("shell", "aside", marker),
        ("comment", "]", []),
        ("close", "main", []),
    ]
    assert browser_fragment_matches_nodes(html, "div", expected) is True
    # The same tree with the anchors in another order is a different Vue tree.
    swapped = [expected[0], expected[3], expected[2], expected[1], expected[4]]
    assert browser_fragment_matches_nodes(html, "div", swapped) is False
    # A shell with written content would hide that content's mismatches.
    filled = html.replace("></aside>", "><b>x</b></aside>")
    assert browser_fragment_matches_nodes(filled, "div", expected) is False
    root_text = [("open", "p", []), ("close", "p", []), ("text", "\n", [])]
    assert browser_fragment_matches_nodes("<p></p>\n", "div", root_text)


def test_browser_fragment_matches_nodes_rejects_malformed_events():
    with pytest.raises(ValueError, match="unknown expected node kind"):
        browser_fragment_matches_nodes("<p></p>", "div", [("element", "p", [])])
    for kind in ("close", "comment", "text"):
        with pytest.raises(ValueError, match=f"a {kind} event cannot carry attributes"):
            browser_fragment_matches_nodes("<p></p>", "div", [(kind, "p", [("id", "x")])])


def test_basic_transformation():
    html = "<div><p>Hello</p></div>"
    result, _ = transform_html(html, ["data-root"], ["data-all"])
    expected = '<div data-root="" data-all=""><p data-all="">Hello</p></div>'
    assert result == expected


def test_multiple_roots():
    html = "<div>First</div><span>Second</span>"
    result, _ = transform_html(html, ["data-root"], ["data-all"])
    expected = '<div data-root="" data-all="">First</div><span data-root="" data-all="">Second</span>'
    assert result == expected


def test_complex_html():
    html = """
        <div class="container" id="main">
            <header class="flex">
                <h1 title="Main Title">Hello & Welcome</h1>
                <nav data-existing="true">
                    <a href="/home">Home</a>
                    <a href="/about" class="active">About</a>
                </nav>
            </header>
            <main>
                <article data-existing="true">
                    <h2>Article 1</h2>
                    <p>Some text with <strong>bold</strong> and <em>emphasis</em></p>
                    <img src="test.jpg" alt="Test Image"/>
                </article>
            </main>
        </div>
        <footer id="footer">
            <p>&copy; 2024</p>
        </footer>
    """

    result, _ = transform_html(html, ["data-root"], ["data-all", "data-v-123"])
    expected = """
        <div class="container" id="main" data-root="" data-all="" data-v-123="">
            <header class="flex" data-all="" data-v-123="">
                <h1 title="Main Title" data-all="" data-v-123="">Hello & Welcome</h1>
                <nav data-existing="true" data-all="" data-v-123="">
                    <a href="/home" data-all="" data-v-123="">Home</a>
                    <a href="/about" class="active" data-all="" data-v-123="">About</a>
                </nav>
            </header>
            <main data-all="" data-v-123="">
                <article data-existing="true" data-all="" data-v-123="">
                    <h2 data-all="" data-v-123="">Article 1</h2>
                    <p data-all="" data-v-123="">Some text with <strong data-all="" data-v-123="">bold</strong> and <em data-all="" data-v-123="">emphasis</em></p>
                    <img src="test.jpg" alt="Test Image" data-all="" data-v-123=""/>
                </article>
            </main>
        </div>
        <footer id="footer" data-root="" data-all="" data-v-123="">
            <p data-all="" data-v-123="">&copy; 2024</p>
        </footer>
    """  # noqa: E501
    assert result == expected


def test_void_elements():
    test_cases = [
        (
            '<meta charset="utf-8">',
            '<meta charset="utf-8" data-root="" data-v-123=""/>',
        ),
        (
            '<meta charset="utf-8"/>',
            '<meta charset="utf-8" data-root="" data-v-123=""/>',
        ),
        (
            "<div><br><hr></div>",
            '<div data-root="" data-v-123=""><br data-v-123=""/><hr data-v-123=""/></div>',
        ),
        (
            '<img src="test.jpg" alt="Test">',
            '<img src="test.jpg" alt="Test" data-root="" data-v-123=""/>',
        ),
    ]

    for input_html, expected in test_cases:
        result, _ = transform_html(input_html, ["data-root"], ["data-v-123"])
        assert result == expected


def test_html_head_with_meta():
    html = """
        <head>
            <meta charset="utf-8">
            <title>Test Page</title>
            <link rel="stylesheet" href="style.css">
            <meta name="description" content="Test">
        </head>"""

    result, _ = transform_html(html, ["data-root"], ["data-v-123"])
    expected = """
        <head data-root="" data-v-123="">
            <meta charset="utf-8" data-v-123=""/>
            <title data-v-123="">Test Page</title>
            <link rel="stylesheet" href="style.css" data-v-123=""/>
            <meta name="description" content="Test" data-v-123=""/>
        </head>"""
    assert result == expected


def test_watch_attribute():
    html = """
        <div data-id="123">
            <p>Regular element</p>
            <span data-id="456">Nested element</span>
            <img data-id="789" src="test.jpg"/>
        </div>"""

    result: str
    captured: dict[str, list[str]]
    result, captured = transform_html(
        html,
        ["data-root"],
        ["data-v-123"],
        track_added_attributes_for_tags_with_this_attribute="data-id",
    )
    expected = """
        <div data-id="123" data-root="" data-v-123="">
            <p data-v-123="">Regular element</p>
            <span data-id="456" data-v-123="">Nested element</span>
            <img data-id="789" src="test.jpg" data-v-123=""/>
        </div>"""
    assert result == expected

    # Verify attribute capturing
    assert len(captured) == 3

    # Root element should have both root and all attributes
    assert "123" in captured
    assert "data-root" in captured["123"]
    assert "data-v-123" in captured["123"]

    # Non-root elements should only have all attributes
    assert "456" in captured
    assert captured["456"] == ["data-v-123"]
    assert "789" in captured
    assert captured["789"] == ["data-v-123"]


def test_whitespace_preservation():
    html = """<div>
        <p>  Hello  World  </p>
        <span> Text with spaces </span>
    </div>"""

    result, _ = transform_html(html, ["data-root"], ["data-all"])
    expected = """<div data-root="" data-all="">
        <p data-all="">  Hello  World  </p>
        <span data-all=""> Text with spaces </span>
    </div>"""
    assert result == expected


# The behavior depth of `mark_html` is covered by the Rust tests
# (crates/citry_html_transform/tests/marker.rs); these check the shapes that
# cross the Python boundary.


def test_mark_html_roots_and_placeholder():
    segments, placeholders = mark_html(
        '<div>a</div><template c-render-id="c2"></template>',
        ["data-cid-c1"],
        "c-render-id",
    )
    assert segments == ['<div data-cid-c1="">a</div>', ""]
    assert placeholders == [
        ("c2", '<template c-render-id="c2" data-cid-c1=""></template>', ["data-cid-c1"]),
    ]


def test_mark_html_nested_placeholder_gets_no_attributes():
    segments, placeholders = mark_html(
        '<div><template c-render-id="c2"></template></div>',
        ["data-cid-c1"],
        "c-render-id",
    )
    assert segments == ['<div data-cid-c1="">', "</div>"]
    assert placeholders == [("c2", '<template c-render-id="c2"></template>', [])]


def test_mark_html_reads_structure_the_way_the_browser_does():
    # `<xmp>` holds text, and a self-closed `<div/>` stays open.
    segments, _ = mark_html("<xmp></div></xmp><p>x</p>", ["data-cid-c1"], "c-render-id")
    assert segments == ['<xmp data-cid-c1=""></div></xmp><p data-cid-c1="">x</p>']
    segments, _ = mark_html("<div/><p>x</p>", ["data-cid-c1"], "c-render-id")
    assert segments == ['<div data-cid-c1=""/><p>x</p>']


def test_mark_html_no_attributes_no_placeholders():
    segments, placeholders = mark_html("hello", [], "c-render-id")
    assert segments == ["hello"]
    assert placeholders == []


def test_check_output_html_returns_only_what_the_rules_report() -> None:
    events, cleaned = _check_output_html(
        '<p data-cid-a1 onclick="go()">x</p><script type="module">run()</script><b data-m>y</b>',
        pre_extension=False,
        csp=True,
        javascript="omit",
        marker_prefix=None,
        trusted_tag_starts=frozenset(),
        omit_handler_marker="data-m",
    )
    assert events == [
        ("csp-native-event", "p", "onclick", 15, 22, 0, ("a1",)),
        ("js-native-handler", "p", "onclick", 15, 22, 0, ("a1",)),
        ("element", "script", 35, 36, 42, 71, False, True, False, ()),
    ]
    assert cleaned == '<p data-cid-a1 onclick="go()">x</p><script type="module">run()</script><b>y</b>'
    with pytest.raises(ValueError, match="unknown security_javascript mode"):
        _check_output_html(
            "",
            pre_extension=False,
            csp=False,
            javascript="allow",  # type: ignore[arg-type]
            marker_prefix=None,
            trusted_tag_starts=frozenset(),
            omit_handler_marker=None,
        )


def test_the_shared_output_predicates() -> None:
    assert _script_type_is_executable(" Text/JavaScript ;x")
    assert not _script_type_is_executable("module;x")
    assert _classify_dependency_attribute("script", "@load", None) == 1
    assert _classify_dependency_attribute("link", "ONLOAD", "x") == 2
    assert _classify_dependency_attribute("link", "href", " java\tscript:x") == 4
    assert _is_javascript_url("\x00JAVA\u017fCRIPT:x")
    assert "text/javascript" in _JAVASCRIPT_MIME_TYPES


@pytest.mark.parametrize(
    ("tag", "name", "raw_value", "expected"),
    [
        ("button", "OnClick", "go()", "native-event"),
        ("button", "onclick", None, "native-event"),
        ("a", "href", "java&#115;cript:go()", "javascript-url"),
        ("A", "HREF", " java\tscript:go()", "javascript-url"),
        ("object", "data", "javascript:go()", "javascript-url"),
        ("div", "data", "javascript:go()", None),
        ("a", "href", None, None),
        ("a", "href", "/home", None),
    ],
)
def test_a_template_attribute_gets_the_problem_the_page_check_reports(
    tag: str, name: str, raw_value: str | None, expected: str | None
) -> None:
    assert _csp_attribute_problem(tag, name, raw_value) == expected
    # The same attribute in a finished page must give the same answer, so
    # `citry check` and the render-time check agree.
    attribute = name if raw_value is None else f'{name}="{raw_value}"'
    events, _cleaned = _check_output_html(
        f"<{tag} {attribute}></{tag}>",
        pre_extension=False,
        csp=True,
        javascript=None,
        marker_prefix=None,
        trusted_tag_starts=frozenset(),
        omit_handler_marker=None,
    )
    from_page = [event[0].removeprefix("csp-") for event in events if event[0].startswith("csp-")]
    assert from_page == ([] if expected is None else [expected])


def test_a_lone_surrogate_in_a_template_attribute_matches_no_rule() -> None:
    # The page check never sees one, because a page must be valid UTF-8, but
    # a template's text comes from Python and can hold one. It reads as
    # U+FFFD, which is not one of the characters skipped before a scheme.
    assert _csp_attribute_problem("a", "href", "\ud800javascript:go()") is None
    assert _csp_attribute_problem("a", "on\ud800", None) == "native-event"
