"""
Cross-browser e2e for the ``document`` strategy (everything inlined on one page).

Proves the client runtime actually works in a real browser: a component's JS
runs and receives its ``js_data``, and its CSS applies with the injected
``css_data`` variables. Run across chromium/firefox/webkit via pytest-playwright's
``--browser`` flag. This is a lean starter suite; additional cases should grow
from the completed migration ledger and native Citry contracts.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.dependencies import Script, Style

pytestmark = pytest.mark.e2e


def _build_page() -> type[Component]:
    c = Citry()

    class Widget(Component):
        citry = c
        template = '<div class="widget">hi</div>'
        js = "$component(({ els, data }) => { els[0].setAttribute('data-label', data.label); });"
        css = ".widget { color: var(--accent); }"

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"label": "ran"}

        def css_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"accent": "rgb(12, 34, 56)"}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><c-css /></head>
            <body>
              <c-widget />
              <c-js />
            </body>
          </html>
        """

    return Page


def _build_scoped_css_page() -> type[Component]:
    c = Citry()

    class Static(Component):
        citry = c
        template = '<div id="static-box" class="static-box">static</div>'
        css = ".static-box { background-color: rgb(233, 236, 239); width: 100px; }"

    class Themed(Component):
        citry = c
        template = '<div class="themed-box">themed</div>'
        css = ".themed-box { background-color: var(--bg-color); width: var(--box-width); height: var(--box-height); }"

        class Kwargs:
            color: str

        def css_data(self, kwargs: Kwargs, slots: Any) -> dict[str, str]:
            return {"bg-color": kwargs.color, "box-width": "80px", "box-height": "40px"}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><c-css /></head>
            <body>
              <c-static />
              <div id="box-red"><c-themed color="red" /></div>
              <div id="box-green"><c-themed color="green" /></div>
              <div id="box-blue"><c-themed color="blue" /></div>
            </body>
          </html>
        """

    return Page


def _build_dependency_order_page(probe_kind: str, probe_first: bool) -> type[Component]:
    c = Citry()

    class Alpha(Component):
        citry = c
        template = '<div id="alpha" class="alpha alpha-dependency">alpha</div>'
        js = "window.__assetOrder.push('alpha:component'); window.__alphaComponent = true;"
        css = ".alpha { color: rgb(12, 34, 56); }"

        class Dependencies:
            js = [
                Script(
                    content=(
                        "window.__assetOrder = window.__assetOrder || [];"
                        "window.__assetOrder.push('alpha:dependency');"
                        "window.__alphaDependency = true;"
                    ),
                    wrap=False,
                )
            ]
            css = [Style(content=".alpha-dependency { background-color: rgb(210, 220, 230); }")]

    class Beta(Component):
        citry = c
        template = '<div id="beta">beta</div>'
        js = "window.__assetOrder.push('beta:component'); window.__betaComponent = true;"

        class Dependencies:
            js = [
                Script(
                    content=(
                        "window.__assetOrder = window.__assetOrder || [];"
                        "window.__assetOrder.push('beta:dependency');"
                        "window.__betaDependency = true;"
                    ),
                    wrap=False,
                )
            ]

    class AssetGroup(Component):
        citry = c
        template = "<section><c-alpha /><c-beta /></section>"

    probe_js = """
      window.__assetSnapshot = {
        alphaDependency: window.__alphaDependency ?? null,
        betaDependency: window.__betaDependency ?? null,
        alphaComponent: window.__alphaComponent ?? null,
        betaComponent: window.__betaComponent ?? null,
        order: [...(window.__assetOrder || [])],
      };
    """

    class ComponentProbe(Component):
        citry = c
        template = "<i>component probe</i>"
        js = probe_js

    class DependencyProbe(Component):
        citry = c
        template = "<i>dependency probe</i>"

        class Dependencies:
            js = [Script(content=probe_js, wrap=False)]

    probe_tag = "c-component-probe" if probe_kind == "component" else "c-dependency-probe"
    children = f"<{probe_tag} /><c-asset-group />" if probe_first else f"<c-asset-group /><{probe_tag} />"

    class Page(Component):
        citry = c
        template = f"<html><head><c-css /></head><body>{children}<c-js /></body></html>"

    return Page


def _build_no_data_js_page() -> type[Component]:
    c = Citry()

    class Interactive(Component):
        citry = c
        template = """
          <section id="no-data-widget">
            <span id="immediate-marker">pending</span>
            <button type="button">run</button>
            <output></output>
          </section>
        """
        js = """
          var citryE2eNoGlobalLeak = 123;
          document.querySelector('#immediate-marker').textContent = 'immediate';
          $component(({ els, data }) => {
            const root = els[0];
            root.dataset.nullData = String(data === null);
            root.querySelector('button').addEventListener('click', () => {
              root.querySelector('output').textContent = 'clicked';
            });
          });
        """

    class Page(Component):
        citry = c
        template = "<html><head></head><body><c-interactive /><c-js /></body></html>"

    return Page


def _build_distinct_js_data_page() -> type[Component]:
    c = Citry()

    class Payload(Component):
        citry = c
        template = """
          <section class="payload-widget">
            <button type="button">{{ name }}</button>
            <output></output>
          </section>
        """
        js = """
          $component(({ els, data }) => {
            const root = els[0];
            root.dataset.name = data.name;
            root.dataset.payload = JSON.stringify(data.meta);
            root.querySelector('button').addEventListener('click', () => {
              root.querySelector('output').textContent =
                `${data.message}|${data.meta.count}|${data.meta.points[1][0]}`;
            });
          });
        """

        class Kwargs:
            name: str
            message: str
            count: int

        def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, str]:
            return {"name": kwargs.name}

        def js_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:
            return {
                "name": kwargs.name,
                "message": kwargs.message,
                "meta": {"count": kwargs.count, "points": [[1.25, 2.5], [kwargs.count + 0.5, 4.75]]},
            }

    class Page(Component):
        citry = c
        template = """
          <html>
            <head></head>
            <body>
              <c-payload name="red" message="Red clicked" c-count="10" />
              <c-payload name="green" message="Green clicked" c-count="20" />
              <c-payload name="blue" message="Blue clicked" c-count="30" />
              <c-js />
            </body>
          </html>
        """

    return Page


def test_component_js_runs_and_receives_data(page: Any, serve_document: Any) -> None:
    html = _build_page()().render().serialize(deps_strategy="document")
    page.goto(serve_document(html))
    page.wait_for_function("document.querySelector('.widget')?.dataset.label === 'ran'")
    assert page.locator(".widget").get_attribute("data-label") == "ran"


def test_component_js_without_data_runs_immediately_and_stays_scoped(page: Any, serve_document: Any) -> None:
    html = _build_no_data_js_page()().render().serialize(deps_strategy="document")
    page.goto(serve_document(html))
    page.wait_for_function("document.querySelector('#no-data-widget')?.dataset.nullData === 'true'")

    assert page.locator("#immediate-marker").text_content() == "immediate"
    assert page.evaluate("() => typeof window.citryE2eNoGlobalLeak") == "undefined"
    page.locator("#no-data-widget button").click()
    assert page.locator("#no-data-widget output").text_content() == "clicked"


def test_component_js_data_is_isolated_per_document_instance(page: Any, serve_document: Any) -> None:
    html = _build_distinct_js_data_page()().render().serialize(deps_strategy="document")
    page.goto(serve_document(html))
    page.wait_for_function("document.querySelectorAll('.payload-widget[data-payload]').length === 3")

    widgets = page.locator(".payload-widget")
    assert [widgets.nth(index).get_attribute("data-name") for index in range(3)] == ["red", "green", "blue"]
    assert [widgets.nth(index).get_attribute("data-payload") for index in range(3)] == [
        '{"count":10,"points":[[1.25,2.5],[10.5,4.75]]}',
        '{"count":20,"points":[[1.25,2.5],[20.5,4.75]]}',
        '{"count":30,"points":[[1.25,2.5],[30.5,4.75]]}',
    ]

    for index in range(3):
        widgets.nth(index).locator("button").click()
    assert [widgets.nth(index).locator("output").text_content() for index in range(3)] == [
        "Red clicked|10|10.5",
        "Green clicked|20|20.5",
        "Blue clicked|30|30.5",
    ]


def test_component_css_applies_with_injected_vars(page: Any, serve_document: Any) -> None:
    html = _build_page()().render().serialize(deps_strategy="document")
    page.goto(serve_document(html))
    color = page.eval_on_selector(".widget", "el => getComputedStyle(el).color")
    assert color == "rgb(12, 34, 56)"


def test_component_css_is_static_and_scoped_per_instance(page: Any, serve_document: Any) -> None:
    html = _build_scoped_css_page()().render().serialize(deps_strategy="document")
    page.goto(serve_document(html))
    page.wait_for_function("""() => {
        const boxes = [...document.querySelectorAll('.themed-box')];
        const colors = boxes.map((box) => getComputedStyle(box).backgroundColor);
        return colors.join('|') === 'rgb(255, 0, 0)|rgb(0, 128, 0)|rgb(0, 0, 255)';
    }""")

    static = page.eval_on_selector(
        "#static-box",
        """el => ({
            background: getComputedStyle(el).backgroundColor,
            width: getComputedStyle(el).width,
            attrs: [...el.attributes].map((attr) => attr.name),
        })""",
    )
    assert static["background"] == "rgb(233, 236, 239)"
    assert static["width"] == "100px"
    assert not any(name.startswith("data-ccss-") for name in static["attrs"])

    themed = page.eval_on_selector_all(
        ".themed-box",
        """els => els.map((el) => ({
            background: getComputedStyle(el).backgroundColor,
            width: getComputedStyle(el).width,
            height: getComputedStyle(el).height,
            hash: [...el.attributes]
                .map((attr) => attr.name)
                .find((name) => name.startsWith('data-ccss-'))
                ?.slice('data-ccss-'.length),
        }))""",
    )
    assert [item["background"] for item in themed] == [
        "rgb(255, 0, 0)",
        "rgb(0, 128, 0)",
        "rgb(0, 0, 255)",
    ]
    assert all(item["width"] == "80px" and item["height"] == "40px" for item in themed)
    hashes = [item["hash"] for item in themed]
    assert all(hash_ is not None and re.fullmatch(r"[0-9a-f]{32}", hash_) for hash_ in hashes)
    assert len(set(hashes)) == 3


@pytest.mark.parametrize(
    ("probe_kind", "probe_first", "expected"),
    [
        (
            "component",
            False,
            {
                "alphaDependency": True,
                "betaDependency": True,
                "alphaComponent": True,
                "betaComponent": True,
                "order": ["alpha:dependency", "beta:dependency", "alpha:component", "beta:component"],
            },
        ),
        (
            "dependency",
            False,
            {
                "alphaDependency": True,
                "betaDependency": True,
                "alphaComponent": None,
                "betaComponent": None,
                "order": ["alpha:dependency", "beta:dependency"],
            },
        ),
        (
            "dependency",
            True,
            {
                "alphaDependency": None,
                "betaDependency": None,
                "alphaComponent": None,
                "betaComponent": None,
                "order": [],
            },
        ),
    ],
    ids=["component-probe-last", "dependency-probe-last", "dependency-probe-first"],
)
def test_component_and_dependency_assets_execute_in_bucket_order(
    page: Any,
    serve_document: Any,
    probe_kind: str,
    probe_first: bool,
    expected: dict[str, Any],
) -> None:
    html = _build_dependency_order_page(probe_kind, probe_first)().render().serialize(deps_strategy="document")
    page.goto(serve_document(html))
    page.wait_for_function("window.__assetSnapshot !== undefined && window.__betaComponent === true")

    assert page.evaluate("() => window.__assetSnapshot") == expected
    styles = page.eval_on_selector(
        "#alpha",
        "el => ({color: getComputedStyle(el).color, background: getComputedStyle(el).backgroundColor})",
    )
    assert styles == {"color": "rgb(12, 34, 56)", "background": "rgb(210, 220, 230)"}


def test_component_and_dependency_css_apply_without_javascript(browser: Any, serve_document: Any) -> None:
    html = _build_dependency_order_page("component", probe_first=False)().render().serialize(deps_strategy="document")
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    try:
        page.goto(serve_document(html))
        styles = page.eval_on_selector(
            "#alpha",
            "el => ({color: getComputedStyle(el).color, background: getComputedStyle(el).backgroundColor})",
        )
        assert styles == {"color": "rgb(12, 34, 56)", "background": "rgb(210, 220, 230)"}
        assert page.evaluate("() => window.__assetOrder") is None
    finally:
        context.close()
