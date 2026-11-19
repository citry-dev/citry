"""
Browser proof that two renders serialized with ``deps_position="separate"`` work as two apps on one page.

A host such as citry-django serializes each interactive region on its own,
keeps one copy of each shared tag, and writes the HTML and the tags into its
own page. Here the page holds two such apps with a single runtime script.
Both must hydrate the server HTML (keep the elements the server wrote), run
their own click handlers, and log no error.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component

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


def test_two_separate_islands_hydrate_and_run_on_one_page(
    serve_live: Callable[..., str],
    open_citry_page: Callable[..., None],
    page: Any,
) -> None:
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
