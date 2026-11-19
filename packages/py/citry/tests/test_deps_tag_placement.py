"""
Where Citry puts CSS and JS tags when an attribute value holds end-tag text.

An interactive page writes ``<`` and ``>`` raw in attribute values, so a
value such as ``</head>`` from request data looks like a tag to a text
search. Citry must place its tags at the page's real ``</head>`` and
``</body>``, or at the start or end of the output when there are none,
never inside the value: a tag's own ``"`` would end the attribute and turn
the rest of the value into markup.
"""

from __future__ import annotations

import pytest

from citry import Citry, Component

# Each value hides end-tag text before markup that would run in a browser.
DECOYS = ["</head>", "</body>", "</HEAD>", "</BODY>"]
# Author shells: a fragment, a document without <head>, and a document
# written in uppercase.
FRAGMENT = "<c-Widget />"
NO_HEAD = "<!doctype html><html><body><c-Widget /></body></html>"
UPPERCASE = "<!DOCTYPE html><HTML><HEAD><TITLE>t</TITLE></HEAD><BODY><c-Widget /></BODY></HTML>"


def _value(decoy: str) -> str:
    return f"X{decoy}Y<img id=pwn src=x onerror=window.__pwn=1>"


def _page(value: str, *, route: str, shell: str, cache: bool = False) -> type[Component]:
    """Define a page holding an interactive widget with CSS whose title is ``value``."""
    engine = Citry(autodiscover=False)
    engine.set_mounted_prefix("/citry")
    calls: list[int] = []

    class Widget(Component):
        citry = engine

        if cache:

            class Cache:
                enabled = True

        # c-title writes the value on the server; :title binds it in Vue.
        # Both reach the hydrated page with < and > raw.
        if route == "server":
            template = """
                <div c-title="value">x</div>
            """
        else:
            template = """
                <div :title="value">x</div>
            """
        js = """
            console.log(1)
        """
        css = """
            .a { color: red; }
        """

        def template_data(self, kwargs, slots):
            calls.append(1)
            return {"value": value}

        def js_data(self, kwargs, slots):
            return {"value": value}

    class Page(Component):
        citry = engine
        template = shell

    Page.calls = calls  # type: ignore[attr-defined]
    return Page


@pytest.mark.parametrize("decoy", DECOYS)
@pytest.mark.parametrize("route", ["server", "vue"])
@pytest.mark.parametrize("shell", [FRAGMENT, NO_HEAD, UPPERCASE], ids=["fragment", "no-head", "uppercase"])
def test_tags_never_land_inside_an_attribute_value(decoy: str, route: str, shell: str) -> None:
    value = _value(decoy)
    html = _page(value, route=route, shell=shell)().render().serialize()

    # The value reaches the page whole, with nothing inserted into it.
    assert f'title="{value}"' in html
    assert "<link" in html
    assert "<script" in html


@pytest.mark.parametrize("route", ["server", "vue"])
def test_uppercase_document_tags_are_found(route: str) -> None:
    html = _page(_value("</head></body>"), route=route, shell=UPPERCASE)().render().serialize()

    # Browsers read tag names without regard to case, so the author's
    # </HEAD> and </BODY> are where the tags go.
    head_end = html.index("</HEAD>")
    body_end = html.index("</BODY>")
    assert html.index("<link") < head_end < html.index("<BODY>")
    assert html.rindex("</script>") < body_end
    assert html[body_end:] == "</BODY></HTML>"


@pytest.mark.parametrize("route", ["server", "vue"])
def test_fragment_tags_go_before_and_after_the_output(route: str) -> None:
    html = _page(_value("</head></body>"), route=route, shell=FRAGMENT)().render().serialize()

    assert html.startswith("<link")
    assert html.endswith("</script>")


def test_ordinary_document_keeps_its_placement() -> None:
    shell = "<!doctype html><html><head><title>t</title></head><body><c-Widget /></body></html>"
    html = _page(_value("</head></body>"), route="vue", shell=shell)().render().serialize()

    head_end = html.index("</head><body>")
    assert html.index("<link") < head_end
    assert html.rindex("</script>") < html.rindex("</body></html>")
    assert html.endswith("</script></body></html>")


def test_a_cached_render_replays_safely() -> None:
    value = _value("</head></body>")
    page = _page(value, route="server", shell=FRAGMENT, cache=True)

    outputs = [page().render().serialize() for _ in range(3)]

    # The later renders come from the cache, and each keeps the value whole.
    assert len(page.calls) == 1  # type: ignore[attr-defined]
    for html in outputs:
        assert f'title="{value}"' in html
        assert html.startswith("<link")


@pytest.mark.parametrize("route", ["server", "vue"])
def test_separate_assets_leave_the_value_whole(route: str) -> None:
    value = _value("</head></body>")
    result = _page(value, route=route, shell=FRAGMENT)().render().serialize_result(deps_position="separate")

    assert f'title="{value}"' in result.html
    assert "<link" not in result.html
    assert "<script" not in result.html
    assert result.app_assets.css or result.runtime_assets.css
