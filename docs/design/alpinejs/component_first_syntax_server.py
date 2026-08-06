# ruff: noqa: ANN001, ANN202, ARG002, S101, T201
"""
Server-side syntax evidence for the candidate ``$c-*`` client directives.

Run from the repository root:

    uv run python docs/design/alpinejs/component_first_syntax_server.py

The harness uses the real V3 parser, compiler, Python render nodes, and HTML
serializer. It now locks the accepted A0 spelling and placement contract; the
future graph client_binding remains outside this harness.
"""

from __future__ import annotations

import json
import re
from typing import Any

from citry import Citry, Component
from citry.constness import const_value
from citry_core import _rust

_CID_RE = re.compile(r' data-cid-[^= ]+=""')


def _scrub_ids(html: str) -> str:
    return _CID_RE.sub("", html)


def _parse_compile(source: str) -> dict[str, Any]:
    template = _rust.template_parser.parse_template(source)
    node = template.elements[0]._0
    attrs = node.start_tag.attrs
    compiled = _rust.template_parser.compile_template(template)
    return {
        "attrs": [
            {
                "key": attr.key.content,
                "value": None if attr.inner_value is None else attr.inner_value.content,
                "usedVariables": [token.content for token in attr.used_variables],
            }
            for attr in attrs
        ],
        "compiled": compiled,
    }


def parser_and_compiler_cases() -> dict[str, Any]:
    direct = _parse_compile('<c-Child $c-props="{ count: localCount }" />')
    dynamic = _parse_compile('<c-Child c-$c-props="props_source" />')
    spread = _parse_compile('<c-Child c-bind="attrs" />')
    namespace = _parse_compile('<c-Child $c-props="{ count: 1 }" $c-on:click.once="save()" $c-model="name" />')

    assert direct["attrs"] == [{"key": "$c-props", "value": "{ count: localCount }", "usedVariables": []}]
    assert "StaticHtmlAttr" in direct["compiled"]
    assert "ExprHtmlAttr" not in direct["compiled"]

    assert dynamic["attrs"] == [{"key": "c-$c-props", "value": "props_source", "usedVariables": ["props_source"]}]
    assert "ExprHtmlAttr" in dynamic["compiled"]
    assert "c-$c-props" in dynamic["compiled"]

    assert spread["attrs"] == [{"key": "c-bind", "value": "attrs", "usedVariables": ["attrs"]}]
    assert "ExprHtmlAttr" in spread["compiled"]

    assert [attr["key"] for attr in namespace["attrs"]] == [
        "$c-props",
        "$c-on:click.once",
        "$c-model",
    ]
    assert all(not attr["usedVariables"] for attr in namespace["attrs"])
    assert '"""$c-on:click.once""", """save()"""' in namespace["compiled"]

    empty_error = None
    try:
        _rust.template_parser.parse_template('<c-Child $c-props="" />')
    except Exception as error:  # noqa: BLE001
        empty_error = {"type": type(error).__name__, "message": str(error)}
    assert empty_error is not None
    assert "must have a non-empty client expression value" in empty_error["message"]

    duplicate_error = None
    try:
        _rust.template_parser.parse_template('<c-Child $c-props="a" $c-props="b" />')
    except Exception as error:  # noqa: BLE001
        duplicate_error = {"type": type(error).__name__, "message": str(error)}
    assert duplicate_error is not None
    assert "Duplicate attribute '$c-props'" in duplicate_error["message"]

    return {
        "direct": direct,
        "dynamic": dynamic,
        "spread": spread,
        "namespace": namespace,
        "empty": empty_error,
        "duplicate": duplicate_error,
    }


def _direct_component_case() -> dict[str, Any]:
    registry = Citry()
    captured: list[dict[str, dict[str, Any]]] = []

    class Child(Component):
        citry = registry
        template = """
            <div>child</div>
        """

        def template_data(self, kwargs, slots):
            captured.append(
                {
                    "kwargs": {key: const_value(value) for key, value in kwargs.items()},
                    "rawKwargs": {key: const_value(value) for key, value in self.raw_kwargs.items()},
                }
            )
            return {}

    class Page(Component):
        citry = registry
        template = """
            <c-child $c-props="{ count: localCount }" />
        """

    html = _scrub_ids(Page().render().serialize()).strip()
    assert captured == [{"kwargs": {}, "rawKwargs": {"$c-props": "{ count: localCount }"}}]
    assert html == "<div>child</div>"
    return {"childInputs": captured[0], "html": html}


def _dynamic_component_case() -> dict[str, Any]:
    registry = Citry()
    captured: list[dict[str, dict[str, Any]]] = []

    class Child(Component):
        citry = registry
        template = """
            <div>child</div>
        """

        def template_data(self, kwargs, slots):
            captured.append(
                {
                    "kwargs": {key: const_value(value) for key, value in kwargs.items()},
                    "rawKwargs": {key: const_value(value) for key, value in self.raw_kwargs.items()},
                }
            )
            return {}

    class Page(Component):
        citry = registry
        template = """
            <c-child c-$c-props="props_source" />
        """

        def template_data(self, kwargs, slots):
            return {"props_source": "{ count: 2 }"}

    html = _scrub_ids(Page().render().serialize()).strip()
    assert captured == [{"kwargs": {}, "rawKwargs": {"$c-props": "{ count: 2 }"}}]
    assert html == "<div>child</div>"
    return {"childInputs": captured[0], "html": html}


def _spread_component_case() -> dict[str, Any]:
    registry = Citry()
    captured: list[dict[str, dict[str, Any]]] = []

    class Child(Component):
        citry = registry
        template = """
            <div>child</div>
        """

        def template_data(self, kwargs, slots):
            captured.append(
                {
                    "kwargs": {key: const_value(value) for key, value in kwargs.items()},
                    "rawKwargs": {key: const_value(value) for key, value in self.raw_kwargs.items()},
                }
            )
            return {}

    class Page(Component):
        citry = registry
        template = """
            <c-child c-bind="attrs" />
        """

        def template_data(self, kwargs, slots):
            return {"attrs": {"$c-props": "{ count: 3 }"}}

    html = _scrub_ids(Page().render().serialize()).strip()
    assert captured == [{"kwargs": {}, "rawKwargs": {"$c-props": "{ count: 3 }"}}]
    assert html == "<div>child</div>"
    return {"childInputs": captured[0], "html": html}


def _element_case(template: str, data: dict[str, Any]) -> str:
    registry = Citry()
    source_template = template

    class Page(Component):
        citry = registry
        template = source_template

        def template_data(self, kwargs, slots):
            return data

    return _scrub_ids(Page().render().serialize()).strip()


def _element_error(template: str, data: dict[str, Any]) -> dict[str, str]:
    try:
        _element_case(template, data)
    except Exception as error:  # noqa: BLE001
        return {"type": type(error).__name__, "message": str(error)}
    raise AssertionError(f"Expected the element case to fail: {template}")


def render_cases() -> dict[str, Any]:
    direct_element = _element_error(
        """
            <div $c-props="{ count: 1 }"></div>
        """,
        {},
    )
    dynamic_element = _element_error(
        """
            <div c-$c-props="props_source"></div>
        """,
        {"props_source": "{ count: 2 }"},
    )
    spread_element = _element_error(
        """
            <div c-bind="attrs"></div>
        """,
        {"attrs": {"$c-props": "{ count: 3 }"}},
    )
    omitted_element = _element_case(
        """
            <div c-bind="attrs"></div>
        """,
        {"attrs": {"$c-props": None}},
    )

    assert direct_element["type"] == "SyntaxError"
    assert "belongs on a Citry component tag" in direct_element["message"]
    assert dynamic_element["type"] == "SyntaxError"
    assert "belongs on a Citry component tag" in dynamic_element["message"]
    assert spread_element["type"] == "RuntimeError"
    assert "only valid on a Citry component tag" in spread_element["message"]
    assert omitted_element == "<div></div>"

    return {
        "components": {
            "direct": _direct_component_case(),
            "dynamic": _dynamic_component_case(),
            "spread": _spread_component_case(),
        },
        "elements": {
            "direct": direct_element,
            "dynamic": dynamic_element,
            "spread": spread_element,
            "spreadNone": omitted_element,
        },
    }


def main() -> None:
    observed = {
        "parserCompiler": parser_and_compiler_cases(),
        "render": render_cases(),
    }
    print(json.dumps(observed, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
