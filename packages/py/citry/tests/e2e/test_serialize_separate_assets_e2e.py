"""
Browser proof that two renders serialized with ``deps_position="separate"`` work as two apps on one page.

A host such as citry-django serializes each interactive region on its own,
keeps one copy of each shared tag, and writes the HTML and the tags into its
own page. Here the page holds two such apps with a single runtime script.
Both must hydrate the server HTML (keep the elements the server wrote), run
their own click handlers, and log no error. A host may also keep one
stylesheet link for apps that serve the same file: ``combine_assets()``
writes one link that names every app, in its ``data-citry-vue-style-app``
attribute.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component, combine_assets

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry import SerializedRender

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e

# Remember the buttons the server wrote. A classic script at the end of the
# body runs before the module scripts that start the apps.
_CAPTURE = "<script>window.__served = [...document.querySelectorAll('button')];</script>"


def _first_of_each(tags: list[str]) -> list[str]:
    # What a host does with the shared groups: keep the first of equal tags.
    return list(dict.fromkeys(tags))


def _page(results: list[SerializedRender]) -> str:
    head = _first_of_each([tag for result in results for tag in result.runtime_assets.css])
    head += _first_of_each([tag for result in results for tag in result.component_assets.css])
    head += [tag for result in results for tag in result.app_assets.css]
    scripts = _first_of_each([tag for result in results for tag in result.runtime_assets.js])
    scripts += _first_of_each([tag for result in results for tag in result.component_assets.js])
    scripts += [tag for result in results for tag in result.app_assets.js]
    body = "".join(f"<section>{result.html}</section>" for result in results)
    return (
        f"<!DOCTYPE html><html><head><title>Islands</title>{''.join(head)}</head>"
        f"<body>{body}{_CAPTURE}{''.join(scripts)}</body></html>"
    )


def _counter_engine() -> tuple[Citry, Any]:
    engine = Citry(autodiscover=False)
    engine.set_mounted_prefix("/citry")

    class Counter(Component):
        citry = engine

        class Kwargs:
            label: str

        template = """
<div class="counter"><button @click="n++">{{ label }}</button><output v-text="n"></output></div>
"""
        js = """
$component({data() { return {n: 0}; }});
"""
        css = """
.counter { color: rgb(0, 0, 255); }
"""

        def template_data(self, kwargs: Kwargs, slots: object) -> dict[str, object]:
            return {"label": kwargs.label}

    return engine, Counter


def test_two_separate_islands_hydrate_and_run_on_one_page(
    serve_live: Callable[..., str],
    open_citry_page: Callable[..., None],
    page: Any,
) -> None:
    engine, Counter = _counter_engine()
    results = [
        Counter(label=label).render().serialize_result(deps_position="separate") for label in ("first", "second")
    ]
    # The server wrote the HTML for Vue to adopt, as it does with "smart".
    assert all('"hydrate":true' in result.app_assets.js[0] for result in results)
    html = _page(results)
    # One runtime for the page, one data block and start script per app.
    assert html.count('<script src="/citry/citry.') == 1
    assert html.count("data-citry-vue-document=") == 2
    assert html.count('<script type="module"') == 2

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    open_citry_page(serve_live(engine, html, ""), apps=2)

    # Vue kept the buttons the server wrote instead of building new ones.
    assert page.evaluate("() => window.__served.every(button => button.isConnected)")
    assert page.evaluate("() => window.__served.length") == 2

    page.locator("button", has_text="second").click()
    page.locator("button", has_text="second").click()
    page.locator("button", has_text="first").click()
    page.wait_for_function("() => document.querySelectorAll('output')[1].textContent === '2'")
    assert page.locator("output").all_text_contents() == ["1", "2"]
    assert page.locator(".counter").first.evaluate("element => getComputedStyle(element).color") == "rgb(0, 0, 255)"
    assert errors == []


# The order to write the groups in, as the asset placement docs give it.
_GROUP_ORDER = ("runtime_assets", "component_assets", "app_assets")
_STYLE_APP = re.compile(r' data-citry-vue-style-app="([0-9a-f]{32})"')


@pytest.mark.parametrize(
    ("named", "links_after"),
    [
        # The shared link names both apps, so each adopts it and adds none.
        ("both", 1),
        # A link that names only the first app: the second requests the file itself.
        ("first", 2),
        # A malformed list (an id repeated) names no app, so each app requests the file.
        ("malformed", 3),
    ],
)
def test_two_islands_share_one_stylesheet_link(
    serve_live: Callable[..., str],
    open_citry_page: Callable[..., None],
    page: Any,
    named: str,
    links_after: int,
) -> None:
    engine, Counter = _counter_engine()
    results = [
        Counter(label=label).render().serialize_result(deps_position="separate") for label in ("first", "second")
    ]
    # Both apps serve the same stylesheet file, in links that differ only by the app id.
    first, second = (result.app_assets.css for result in results)
    assert len(first) == len(second) == 1
    app_ids = [_STYLE_APP.search(tags[0]).group(1) for tags in (first, second)]  # type: ignore[union-attr]
    assert _STYLE_APP.sub("", first[0]) == _STYLE_APP.sub("", second[0])
    listed = {
        "both": " ".join(app_ids),
        "first": app_ids[0],
        "malformed": " ".join([app_ids[0], *app_ids]),
    }[named]
    shared = _STYLE_APP.sub(f' data-citry-vue-style-app="{listed}"', first[0])

    head = _first_of_each([tag for result in results for tag in result.runtime_assets.css])
    head += _first_of_each([tag for result in results for tag in result.component_assets.css])
    head.append(shared)
    scripts = _first_of_each([tag for result in results for tag in result.runtime_assets.js])
    scripts += _first_of_each([tag for result in results for tag in result.component_assets.js])
    scripts += [tag for result in results for tag in result.app_assets.js]
    body = "".join(f"<section>{result.html}</section>" for result in results)
    html = (
        f"<!DOCTYPE html><html><head><title>Islands</title>{''.join(head)}</head>"
        f"<body>{body}{_CAPTURE}{''.join(scripts)}</body></html>"
    )
    assert html.count('rel="stylesheet"') == 1

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    open_citry_page(serve_live(engine, html, ""), apps=2)

    links = page.evaluate(
        """() => [...document.querySelectorAll('link[rel="stylesheet"]')]
            .map(link => link.getAttribute("data-citry-vue-style-app"))"""
    )
    assert len(links) == links_after
    # The served link is still the first one, unchanged.
    assert links[0] == listed
    # Each app the link does not name added its own link, as it would with no shared link.
    assert links[1:] == (app_ids[1:] if named == "first" else app_ids if named == "malformed" else [])
    for label, expected in (("first", "1"), ("second", "1")):
        page.locator("button", has_text=label).click()
        page.wait_for_function(
            "([label, n]) => [...document.querySelectorAll('.counter')]"
            ".some(c => c.textContent.includes(label) && c.querySelector('output').textContent === n)",
            arg=[label, expected],
        )
    colors = page.locator(".counter").evaluate_all("els => els.map(el => getComputedStyle(el).color)")
    assert colors == ["rgb(0, 0, 255)", "rgb(0, 0, 255)"]
    assert errors == []


def test_combine_assets_gives_two_islands_one_stylesheet_link(
    serve_live: Callable[..., str],
    open_citry_page: Callable[..., None],
    page: Any,
) -> None:
    engine, Counter = _counter_engine()
    results = [
        Counter(label=label).render().serialize_result(deps_position="separate") for label in ("first", "second")
    ]
    groups = [combine_assets(getattr(result, name) for result in results) for name in _GROUP_ORDER]
    head = "".join(tag for group in groups for tag in group.css)
    scripts = "".join(tag for group in groups for tag in group.js)
    body = "".join(f"<section>{result.html}</section>" for result in results)
    html = (
        f"<!DOCTYPE html><html><head><title>Islands</title>{head}</head><body>{body}{_CAPTURE}{scripts}</body></html>"
    )
    assert html.count('rel="stylesheet"') == 1
    assert html.count('<script src="/citry/citry.') == 1

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    open_citry_page(serve_live(engine, html, ""), apps=2)

    # Both apps adopted the one served link, so neither added its own.
    assert page.locator('link[rel="stylesheet"]').count() == 1
    assert page.evaluate("() => window.__served.every(button => button.isConnected)")
    page.locator("button", has_text="second").click()
    page.locator("button", has_text="first").click()
    page.wait_for_function("() => [...document.querySelectorAll('output')].every(o => o.textContent === '1')")
    colors = page.locator(".counter").evaluate_all("els => els.map(el => getComputedStyle(el).color)")
    assert colors == ["rgb(0, 0, 255)", "rgb(0, 0, 255)"]
    assert errors == []
