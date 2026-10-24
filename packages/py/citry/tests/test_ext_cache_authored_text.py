"""
A stored render-cache entry replays only template text that a live template wrote.

The cache backend is shared storage that other processes can write. Replay
puts some stored strings back into the page and the Vue template as markup:
text between tags, `<c-raw>` bodies, joined static markup, and `$c-tr` values
expressions. Each test stores a real entry, changes one of those strings in
the backend, and checks that the next render ignores the entry and renders
fresh, as for any other unusable entry.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from citry import Citry, Component, InMemoryCache
from citry.ext.cache import component_cache_key

if TYPE_CHECKING:
    from collections.abc import Callable

_INJECTED = "<img src=x onerror=alert(1)>"


def _card(*, template: str, js: str | None = None, messages: str | None = None) -> tuple[type[Component], Any]:
    backend = InMemoryCache()
    app = Citry(
        cache=backend,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )
    calls: list[int] = []
    body: dict[str, Any] = {
        "citry": app,
        "Cache": type("Cache", (), {"enabled": True}),
        "template": template,
        "template_data": lambda self, kwargs, slots: calls.append(1) or {"v": 1},  # noqa: ARG005
    }
    if js is not None:
        body["js"] = js
    if messages is not None:
        body["messages"] = messages
    card = type("Card", (Component,), body)
    card.calls = calls  # type: ignore[attr-defined]
    return card, backend


def _edit_parts(value: str, tag: str, edit: Callable[[list[Any]], None]) -> str:
    """Apply ``edit`` to every stored part whose wire tag is ``tag``."""
    data = json.loads(value)
    found = 0

    def walk(node: object) -> None:
        nonlocal found
        if isinstance(node, list):
            if node and node[0] == tag:
                edit(node)
                found += 1
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for item in node.values():
                walk(item)

    walk(data)
    assert found, f"the stored entry has no {tag!r} part to change"
    return json.dumps(data, separators=(",", ":"))


def _store_then_tamper(card: type[Component], backend: Any, tag: str, edit: Callable[[list[Any]], None]) -> None:
    str(card())
    key = component_cache_key(card, vary={})
    stored = backend.get(key)
    assert stored is not None
    # An untouched entry is a hit, so the data method does not run again.
    str(card())
    assert card.calls == [1]  # type: ignore[attr-defined]
    backend.set(key, _edit_parts(stored, tag, edit))


_VUE_TEMPLATE = """
<p class="x">Authored text {{ v }}</p>
"""
_VUE_JS = """
$component({});
"""
# Text beside a provider stays a separate `source_text` part.
_TEXT_TEMPLATE = """
<c-i18n c-client="True" tag="main">Authored text {{ v }}</c-i18n>
"""


def test_source_text_that_differs_from_its_span_is_a_miss() -> None:
    card, backend = _card(template=_TEXT_TEMPLATE, js=_VUE_JS)

    def edit(part: list[Any]) -> None:
        # Keep the real template source and span; change only the text.
        part[3] = _INJECTED

    _store_then_tamper(card, backend, "source_text", edit)

    html = str(card())
    assert _INJECTED not in html
    assert "Authored text 1" in html
    assert card.calls == [1, 1]  # type: ignore[attr-defined]


def test_source_text_from_an_unknown_template_source_is_a_miss() -> None:
    card, backend = _card(template=_TEXT_TEMPLATE, js=_VUE_JS)

    def edit(part: list[Any]) -> None:
        # A self-consistent span over a source no live template has.
        part[1] = _INJECTED
        part[2] = [0, len(_INJECTED.encode())]
        part[3] = _INJECTED

    _store_then_tamper(card, backend, "source_text", edit)

    html = str(card())
    assert _INJECTED not in html
    assert "Authored text 1" in html
    assert card.calls == [1, 1]  # type: ignore[attr-defined]


def test_static_markup_that_no_template_produced_is_a_miss() -> None:
    card, backend = _card(template=_VUE_TEMPLATE, js=_VUE_JS)

    def edit(part: list[Any]) -> None:
        part[1] = part[1].replace('<p class="x">', '<p class="x" v-html="1">')

    _store_then_tamper(card, backend, "static_run", edit)

    html = str(card())
    assert "v-html" not in html
    assert card.calls == [1, 1]  # type: ignore[attr-defined]


def test_raw_body_that_differs_from_its_span_is_a_miss() -> None:
    card, backend = _card(
        template="""
<p>x</p>
<c-raw><i>raw body</i></c-raw>
""",
    )

    def edit(part: list[Any]) -> None:
        part[3] = _INJECTED

    _store_then_tamper(card, backend, "verbatim_html", edit)

    html = str(card())
    assert _INJECTED not in html
    assert card.calls == [1, 1]  # type: ignore[attr-defined]


def test_values_expression_that_no_template_wrote_is_a_miss() -> None:
    card, backend = _card(
        template="""
<c-i18n c-client="True" tag="main">
  <span $c-tr:greeting="{ name: who }">{{ tr("greeting", name="S") }}</span>
</c-i18n>
""",
        js="""
$component({ data() { return { who: 'A' } } });
""",
        messages="""
# @param {str} $name
greeting = Hi { $name }
""",
    )

    def edit(part: list[Any]) -> None:
        binding = part[4]
        assert binding is not None
        # The binding's wire record keeps its values expression in one slot;
        # find it by the authored text rather than by position.
        index = binding.index("{ name: who }")
        binding[index] = "{ name: (globalThis.ran = 1, who) }"

    _store_then_tamper(card, backend, "text_value", edit)

    html = str(card())
    assert "globalThis.ran" not in html
    assert card.calls == [1, 1]  # type: ignore[attr-defined]
