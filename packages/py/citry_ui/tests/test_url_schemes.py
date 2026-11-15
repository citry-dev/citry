"""Every Citry UI input that becomes a link or an image source refuses URLs outside its allowed schemes."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from html import unescape

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CAvatar, CBreadcrumbItem, CImage
from citry_ui.components._url import _read_scheme, attribute_text, check_link_url, is_image_url_allowed
from citry_ui.components.cimage.cimage import _srcset_urls

# Each case spells a refused scheme the way a browser would still read it:
# mixed case, padding, and tab or newline characters inside the scheme.
_REFUSED_EVERYWHERE = [
    "javascript:alert(1)",
    "JavaScript:alert(1)",
    "  javascript:alert(1)",
    "java\tscript:alert(1)",
    "\x01javascript:alert(1)",
    "vbscript:msgbox(1)",
    " VBScript:msgbox(1)",
    "data:text/html,<script>alert(1)</script>",
    " DATA:text/html;base64,PHNjcmlwdD4=",
    "da\nta:text/html,x",
]
_REFUSED_LINKS = [*_REFUSED_EVERYWHERE, "blob:https://example.com/id", "x-app:open"]
_REFUSED_IMAGES = [*_REFUSED_EVERYWHERE, "mailto:a@example.com", "file:///etc/passwd"]

_ACCEPTED_LINKS = [
    "/orders/7",
    "?page=2",
    "#top",
    "//example.com/x",
    "https://example.com/a?b=c#d",
    "HTTP://EXAMPLE.COM",
    "mailto:team@example.com",
    "tel:+15551234567",
    "sms:+15551234567?body=Hi",
]
_ACCEPTED_IMAGES = [
    "/avatar.png",
    "https://example.com/a.png",
    "//cdn.example.com/a.png",
    "data:image/png;base64,AAAA",
    "DATA:Image/SVG+XML,%3Csvg/%3E",
    "blob:https://example.com/0d3c",
]

_LINK_ERROR = r"must be a relative URL or an http:, https:, mailto:, sms:, or tel: URL\."
_IMAGE_ERROR = r"must be a relative URL or an http:, https:, blob:, or data:image/ URL\."


def _render(template: str, data: dict[str, object]) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return data

    Page.template = template
    return Page().render().serialize(deps_strategy="ignore")


# One template per Citry UI input that writes a URL into a link, form, or image.
# Each takes the URL from Python data, the way an app passes a stored value.
_LINK_TEMPLATES = {
    "CButton href": '<c-CButton c-href="url">Go</c-CButton>',
    "CListItem href": '<c-CList><c-CListItem c-href="url">Go</c-CListItem></c-CList>',
    "CMenuItem href": """
      <c-CMenu id="m">
        <c-fill name="activator" data="{ activator_attrs }">
          <button type="button" c-bind="activator_attrs">Open</button>
        </c-fill>
        <c-fill name="default">
          <c-CMenuItem c-href="url">Go</c-CMenuItem>
        </c-fill>
      </c-CMenu>
    """,
    "CNavigationMenuLink href": """
      <c-CNavigationMenu label="Main">
        <c-CNavigationMenuLink c-href="url">Go</c-CNavigationMenuLink>
      </c-CNavigationMenu>
    """,
    "CPagination href": '<c-CPagination c-pages="3" c-href="url + \'{page}\'" />',
    "CForm action": '<c-CForm c-action="url">Body</c-CForm>',
    # A submit Button's formaction replaces its form's action.
    "CButton attrs formaction": '<c-CButton type="submit" c-attrs="form_attrs">Go</c-CButton>',
    "CSplitButton primary_attrs formaction": """
      <c-CSplitButton
        type="submit"
        label="Save actions"
        menu_label="More save actions"
        c-primary_attrs="form_attrs"
      >
        <c-fill name="default">Save</c-fill>
        <c-fill name="menu"><c-CMenuItem value="copy">Copy</c-CMenuItem></c-fill>
      </c-CSplitButton>
    """,
}
_IMAGE_TEMPLATES = {
    "CAvatar src": '<c-CAvatar c-src="url" alt="Ada" />',
    "CImage src": '<c-CImage c-src="url" alt="Ada" c-width="1" c-height="1" />',
    "CImage srcset": '<c-CImage src="/a.png" c-srcset="url + \' 2x\'" alt="Ada" c-width="1" c-height="1" />',
}


def _render_link(name: str, url: str) -> str:
    if name == "CBreadcrumbItem href":
        items = [CBreadcrumbItem("Home", url), CBreadcrumbItem("Here")]
        return _render('<c-CBreadcrumbs c-items="items" />', {"items": items})
    return _render(_LINK_TEMPLATES[name], {"url": url, "form_attrs": {"formaction": url}})


_LINK_INPUTS = ["CBreadcrumbItem href", *_LINK_TEMPLATES]


@pytest.mark.parametrize("url", _REFUSED_LINKS)
@pytest.mark.parametrize("name", _LINK_INPUTS)
def test_link_inputs_refuse_urls_that_run_script(name: str, url: str) -> None:
    with pytest.raises(ValueError, match=_LINK_ERROR):
        _render_link(name, url)


@pytest.mark.parametrize("url", _ACCEPTED_LINKS)
@pytest.mark.parametrize("name", _LINK_INPUTS)
def test_link_inputs_accept_ordinary_urls(name: str, url: str) -> None:
    html = _render_link(name, url)
    # The URL reaches the attribute unchanged; Pagination fills in page 1 for the first link.
    assert (f'="{url}1"' if name == "CPagination href" else f'="{url}"') in html


# Entity-encoded spellings of a refused scheme. Citry writes a Markup value's
# HTML decoded, so an input that passes Markup through reaches the browser
# with the refused scheme.
_ENCODED_LINKS = [
    Markup("javascript&#58;alert(1)"),
    Markup("javascript&colon;alert(1)"),
    Markup("javascript&#x3a;alert(1)"),
    Markup("java&#115;cript:alert(1)"),
    Markup("&#x4A;ava&#X53;cript&#X3A;alert(1)"),
]
_ENCODED_IMAGES = [
    Markup("data&#58;text/html,x"),
    Markup("data&colon;text/html,x"),
    Markup("data&#x3a;text/html,x"),
    Markup("d&#97;ta:text/html,x"),
    Markup("&#x44;ATA&#X3A;text/html,x"),
]
# These inputs pass a Markup value to the page as HTML. The others copy it to
# a plain string first, so the page shows its text as typed.
_MARKUP_LINK_INPUTS = [
    "CButton href",
    "CForm action",
    "CButton attrs formaction",
    "CSplitButton primary_attrs formaction",
]
_URL_ATTRIBUTE = re.compile(r'\s(?:href|action|formaction|src|srcset)="([^"]*)"')


def _written_schemes(page: str) -> set[str | None]:
    # Read each URL attribute the way the browser does: decode it, then take its scheme.
    return {_read_scheme(unescape(value))[0] for value in _URL_ATTRIBUTE.findall(page)}


@pytest.mark.parametrize("url", _ENCODED_LINKS)
@pytest.mark.parametrize("name", _MARKUP_LINK_INPUTS)
def test_link_inputs_read_markup_urls_as_the_browser_does(name: str, url: Markup) -> None:
    with pytest.raises(ValueError, match=_LINK_ERROR):
        _render_link(name, url)


@pytest.mark.parametrize("url", _ENCODED_LINKS)
@pytest.mark.parametrize("name", [name for name in _LINK_INPUTS if name not in _MARKUP_LINK_INPUTS])
def test_link_inputs_that_copy_markup_to_text_write_it_as_typed(name: str, url: Markup) -> None:
    # The page shows the Markup's text as typed, which the browser reads as a
    # relative URL. If one of these inputs starts passing Markup through as
    # HTML, its check refuses the URL and it belongs in _MARKUP_LINK_INPUTS.
    assert _written_schemes(_render_link(name, url)) <= {None}


@pytest.mark.parametrize("name", _LINK_INPUTS)
def test_link_inputs_accept_ordinary_markup_urls(name: str) -> None:
    page = _render_link(name, Markup("/search?a=1&amp;b=2"))
    assert "/search?a=1&amp;" in page


@pytest.mark.parametrize("url", _ENCODED_IMAGES)
@pytest.mark.parametrize("name", _IMAGE_TEMPLATES)
def test_image_inputs_write_markup_urls_as_typed(name: str, url: Markup) -> None:
    # Every image input copies its URL to a plain string first.
    assert _written_schemes(_render(_IMAGE_TEMPLATES[name], {"url": url})) <= {None}


@pytest.mark.parametrize("url", _ENCODED_IMAGES)
def test_image_check_reads_markup_urls_as_the_browser_does(url: Markup) -> None:
    assert not is_image_url_allowed(url)
    assert is_image_url_allowed(str(url))


@pytest.mark.parametrize("name", _IMAGE_TEMPLATES)
def test_image_inputs_accept_ordinary_markup_urls(name: str) -> None:
    page = _render(_IMAGE_TEMPLATES[name], {"url": Markup("/a.png?w=1&amp;h=2")})
    assert "/a.png?w=1&amp;" in page


def test_url_checks_read_the_text_citry_writes() -> None:
    # A plain string is written as typed; Markup is written decoded.
    assert attribute_text("a&amp;b") == "a&amp;b"
    assert attribute_text(Markup("a&amp;b&#58;&quot;")) == 'a&b:"'
    assert attribute_text(Markup("/a?copy&copy=1")) == "/a?copy&copy=1"


@pytest.mark.parametrize("url", _REFUSED_IMAGES)
@pytest.mark.parametrize("name", _IMAGE_TEMPLATES)
def test_image_inputs_refuse_urls_that_are_not_images(name: str, url: str) -> None:
    # CImage refuses ASCII control characters before it reads the scheme.
    match = "cannot contain ASCII controls" if name.startswith("CImage") and re.search(r"[\x00-\x1f]", url) else None
    with pytest.raises(ValueError, match=match or _IMAGE_ERROR):
        _render(_IMAGE_TEMPLATES[name], {"url": url})


@pytest.mark.parametrize("url", _ACCEPTED_IMAGES)
@pytest.mark.parametrize("name", _IMAGE_TEMPLATES)
def test_image_inputs_accept_image_urls(name: str, url: str) -> None:
    html = _render(_IMAGE_TEMPLATES[name], {"url": url})
    assert (f'srcset="{url} 2x"' if name == "CImage srcset" else f'src="{url}"') in html


def test_cimage_sources_srcset_uses_the_image_rule() -> None:
    image = CImage(
        src="/a.png",
        alt="Ada",
        width=1,
        height=1,
        sources=[citry_ui.CImageSource(srcset="/a.webp 1x, javascript:alert(1) 2x", type="image/webp")],
    )
    with pytest.raises(ValueError, match=r"CImage sources\[0\]\.srcset " + _IMAGE_ERROR):
        _render("{{ image }}", {"image": image})


# The HTML srcset parser does not nest parentheses in a descriptor, so the
# browser reads the second candidate in each of these.
_HIDDEN_CANDIDATES = [
    "/a.png 1x((), javascript:alert(1) 2x",
    "/a.png 1x(()), data:text/html,x 2x",
]


@pytest.mark.parametrize("srcset", _HIDDEN_CANDIDATES)
def test_cimage_srcset_reads_candidates_like_the_browser(srcset: str) -> None:
    with pytest.raises(ValueError, match=_IMAGE_ERROR):
        _render('<c-CImage src="/a.png" c-srcset="url" alt="Ada" c-width="1" c-height="1" />', {"url": srcset})


@pytest.mark.parametrize(
    ("url", "scheme"),
    [
        ("java\tscript:x", "javascript"),
        ("\x00\x1f JavaScript:x", "javascript"),
        ("ja+va.s-1:x", "ja+va.s-1"),
        ("1javascript:x", None),
        ("/javascript:x", None),
        ("orders/a:b", None),
        ("java script:x", None),
        (":x", None),
        ("", None),
    ],
)
def test_scheme_reader_matches_the_whatwg_url_parser(url: str, scheme: str | None) -> None:
    assert _read_scheme(url)[0] == scheme


def test_link_check_returns_the_url_unchanged() -> None:
    assert check_link_url("X href", " /a ") == " /a "


def test_data_image_media_type_may_follow_whitespace() -> None:
    # The data: URL processor strips whitespace around the media type.
    assert is_image_url_allowed("data: image/png,x")
    assert not is_image_url_allowed("data: text/html,x")


def _browser_function(js: str, name: str) -> str:
    # Each browser runtime declares the rule as one arrow function; cut it out
    # by its declaration line and the matching closing line at that indent.
    pattern = rf"^( *)const {name} = \(value\) => \{{\n.*?^\1\}};$"
    match = re.search(pattern, js, re.MULTILINE | re.DOTALL)
    assert match is not None
    return match.group(0)


def _run_node(script: str) -> object:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    # Send the script on stdin, which has no command-line length limit.
    result = subprocess.run([node, "-"], input=script, capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


@pytest.mark.parametrize("component", [CAvatar, CImage], ids=lambda component: component.__name__)
def test_browser_image_rule_matches_the_python_rule(component: type) -> None:
    cases = [*_REFUSED_IMAGES, *_ACCEPTED_IMAGES, "data: image/png,x", "\x00 https://x", "ja+va:x", "#a", "?a"]
    script = (
        _browser_function(component.js, "isImageUrlAllowed")
        + f"\nprocess.stdout.write(JSON.stringify({json.dumps(cases)}.map(isImageUrlAllowed)));"
    )
    assert _run_node(script) == [is_image_url_allowed(case) for case in cases]


def test_browser_srcset_reader_matches_the_python_reader() -> None:
    cases = [
        *_HIDDEN_CANDIDATES,
        "/a.png 1x, /b.png 2x",
        "/a.png 1x, javascript:alert(1) 2x",
        "/a.png (x, y) 1x, /b.png",
        "data:image/png;base64,AA== 1x,javascript:x 2x",
        ",,/a.png,, /b.png",
    ]
    script = (
        _browser_function(CImage.js, "isImageUrlAllowed")
        + "\n"
        + _browser_function(CImage.js, "refusedSet")
        + f"\nprocess.stdout.write(JSON.stringify({json.dumps(cases)}.map(refusedSet)));"
    )
    expected = [not all(is_image_url_allowed(url) for url in _srcset_urls(case)) for case in cases]
    assert _run_node(script) == expected
