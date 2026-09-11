# ruff: noqa: S101
"""Check the declared card API and user-visible rendered content."""

import copy
import importlib
from dataclasses import dataclass, field
from html.parser import HTMLParser
from types import ModuleType
from typing import get_type_hints

import pytest

from citry import Component


@dataclass
class Element:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    children: list = field(default_factory=list)

    def text(self) -> str:
        return "".join(child.text() if isinstance(child, Element) else child for child in self.children).strip()

    def find(self, tag: str | None = None, class_name: str | None = None) -> list:
        found = []
        for child in self.children:
            if isinstance(child, Element):
                if (tag is None or child.tag == tag) and (
                    class_name is None or class_name in (child.attrs.get("class") or "").split()
                ):
                    found.append(child)
                found.extend(child.find(tag, class_name))
        return found


class Document(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("document")
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = Element(tag, dict(attrs))
        self.stack[-1].children.append(element)
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.stack.append(element)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


@pytest.fixture
def submitted() -> ModuleType:
    return importlib.import_module("app")


def cards(html: str) -> list[Element]:
    assert isinstance(html, str)
    return Document(html).root.find("article", "product-card")


def assert_card(card: Element, title: str, price: str, description: str, footer: str) -> None:
    for tag, class_name, expected in [
        ("h2", None, title),
        (None, "price", price),
        (None, "description", description),
        ("footer", None, footer),
    ]:
        matches = card.find(tag, class_name)
        assert len(matches) == 1
        assert matches[0].text() == expected


def test_typed_component_and_python_slots(submitted: ModuleType) -> None:
    component = submitted.ProductCard
    assert issubclass(component, Component)
    assert get_type_hints(component.Kwargs)["title"] is str
    assert get_type_hints(component.Kwargs)["price_cents"] is int
    assert {"default", "footer"} <= get_type_hints(component.Slots).keys()
    result = cards(
        str(component(title="Notebook", price_cents=1205, slots={"default": "Plain paper", "footer": "In stock"}))
    )
    assert len(result) == 1
    assert_card(result[0], "Notebook", "$12.05", "Plain paper", "In stock")


def test_order_prices_and_footer_fallback(submitted: ModuleType) -> None:
    items = [
        {"title": "Free", "price_cents": 0, "description": "First"},
        {"title": "Pencil", "price_cents": 9, "description": "Second", "footer": None},
        {"title": "Book", "price_cents": 12345, "description": "Third", "footer": "Limited"},
        {"title": "Silent", "price_cents": 100, "description": "Fourth", "footer": ""},
    ]
    before = copy.deepcopy(items)
    result = cards(submitted.render_cards(items))
    assert len(result) == len(items)
    for card, item, price, footer in zip(
        result,
        items,
        ["$0.00", "$0.09", "$123.45", "$1.00"],
        ["Available now", "Available now", "Limited", ""],
        strict=True,
    ):
        assert_card(card, item["title"], price, item["description"], footer)
    assert items == before


@pytest.mark.parametrize("field_name", ["title", "description", "footer"])
def test_untrusted_text_is_escaped(submitted: ModuleType, field_name: str) -> None:
    payload = '<img src=x onerror="alert(1)"> & "quoted" <script>bad()</script>'
    item = {"title": "Safe", "price_cents": 205, "description": "Text", "footer": "Footer"}
    item[field_name] = payload
    result = cards(submitted.render_cards([item]))
    assert len(result) == 1
    assert_card(result[0], item["title"], "$2.05", item["description"], item["footer"])
    assert not result[0].find("img")
    assert not result[0].find("script")


def test_empty_and_consecutive_calls(submitted: ModuleType) -> None:
    assert cards(submitted.render_cards([])) == []
    for title, cents in [("Alpha", 100), ("Beta", 709), ("Alpha", 301)]:
        result = cards(submitted.render_cards([{"title": title, "price_cents": cents, "description": title}]))
        assert len(result) == 1
        assert_card(result[0], title, f"${cents // 100}.{cents % 100:02d}", title, "Available now")
    assert cards(submitted.render_cards([])) == []
