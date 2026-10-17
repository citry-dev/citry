"""Browser parsing of static non-void self-closing markup in HTML namespaces."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e


def test_static_coalescer_preserves_siblings_in_html_custom_svg_and_foreign_object(page: Any) -> None:
    app = Citry(autodiscover=False, extensions=[])

    class HtmlContext(Component):
        citry = app
        template = '<main id="html-context"><div id="html-empty"/><span id="html-next"/></main>'

    class CustomContext(Component):
        citry = app
        template = '<main id="custom-context"><x-box id="custom-empty"/><span id="custom-next"/></main>'

    class SvgContext(Component):
        citry = app
        template = '<svg id="svg-context"><path id="svg-empty"/><circle id="svg-next"/></svg>'

    class ForeignObjectContext(Component):
        citry = app
        template = (
            '<svg id="foreign-context"><foreignObject>'
            '<div id="foreign-empty"/><p id="foreign-next"/>'
            "</foreignObject></svg>"
        )

    html = "".join(
        component().render().serialize(deps_strategy="ignore")
        for component in (HtmlContext, CustomContext, SvgContext, ForeignObjectContext)
    )
    page.set_content(f"<!doctype html><html><body>{html}</body></html>")
    result = page.evaluate(
        """() => {
          const summary = id => {
            const element = document.getElementById(id);
            const parent = element.parentElement;
            return {
              tag: element.localName,
              namespace: element.namespaceURI,
              parent: parent.id || parent.localName,
              children: [...element.children].map(child => child.localName),
              previous: element.previousElementSibling?.id ?? null,
            };
          };
          return {
            htmlEmpty: summary('html-empty'), htmlNext: summary('html-next'),
            customEmpty: summary('custom-empty'), customNext: summary('custom-next'),
            svgEmpty: summary('svg-empty'), svgNext: summary('svg-next'),
            foreignEmpty: summary('foreign-empty'), foreignNext: summary('foreign-next'),
          };
        }"""
    )

    html_namespace = "http://www.w3.org/1999/xhtml"
    svg_namespace = "http://www.w3.org/2000/svg"
    assert result == {
        "htmlEmpty": {
            "tag": "div",
            "namespace": html_namespace,
            "parent": "html-context",
            "children": [],
            "previous": None,
        },
        "htmlNext": {
            "tag": "span",
            "namespace": html_namespace,
            "parent": "html-context",
            "children": [],
            "previous": "html-empty",
        },
        "customEmpty": {
            "tag": "x-box",
            "namespace": html_namespace,
            "parent": "custom-context",
            "children": [],
            "previous": None,
        },
        "customNext": {
            "tag": "span",
            "namespace": html_namespace,
            "parent": "custom-context",
            "children": [],
            "previous": "custom-empty",
        },
        "svgEmpty": {
            "tag": "path",
            "namespace": svg_namespace,
            "parent": "svg-context",
            "children": [],
            "previous": None,
        },
        "svgNext": {
            "tag": "circle",
            "namespace": svg_namespace,
            "parent": "svg-context",
            "children": [],
            "previous": "svg-empty",
        },
        "foreignEmpty": {
            "tag": "div",
            "namespace": html_namespace,
            "parent": "foreignObject",
            "children": [],
            "previous": None,
        },
        "foreignNext": {
            "tag": "p",
            "namespace": html_namespace,
            "parent": "foreignObject",
            "children": [],
            "previous": "foreign-empty",
        },
    }
