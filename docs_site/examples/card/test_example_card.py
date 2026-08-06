"""Verify the typed Card recipe, including its useful failure paths."""

import re

import pytest
from docs_site._internal.examples import get_example_registry
from docs_site.examples.card.page import CardPage

from citry import Component, citry


def test_card_example_page_renders() -> None:
    html = str(CardPage())
    assert '<article class="demo-card"' in html
    assert '<h2 class="demo-card__title">Welcome</h2>' in html
    assert "Choose the accent color, then add any content you like." in html
    assert "--accent: #8250df" in html
    assert "border-top: 0.25rem solid var(--accent)" in html


def test_card_accepts_one_typed_input_and_one_default_slot() -> None:
    get_example_registry()
    card = citry.get("card")

    html = str(card(accent="#0969da", slots={"default": "Typed and composable."}))

    assert "Typed and composable." in html
    assert "--accent: #0969da" in html

    class TwoCardsPage(Component):
        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <main>
            <c-Card accent="#0969da">A blue card.</c-Card>
            <c-Card accent="#8250df">A purple card.</c-Card>
          </main>
        """

    page_html = str(TwoCardsPage())
    marker = re.compile(r"data-ccss-([0-9a-f]{32})")
    assert "A blue card." in page_html
    assert "A purple card." in page_html
    assert "--accent: #0969da" in page_html
    assert "--accent: #8250df" in page_html
    assert len(set(marker.findall(page_html))) == 2


def test_plain_schema_annotation_does_not_validate_the_value_type() -> None:
    get_example_registry()
    card = citry.get("card")

    html = str(card(accent=123, slots={"default": "Annotations guide type checkers."}))

    assert "--accent: 123" in html


def test_card_requires_its_accent_and_content() -> None:
    get_example_registry()
    card = citry.get("card")

    with pytest.raises(TypeError, match="missing 1 required positional argument: 'accent'"):
        str(card(slots={"default": "Missing accent."}))

    with pytest.raises(TypeError, match="missing 1 required positional argument: 'default'"):
        str(card(accent="#0969da"))

    with pytest.raises(TypeError, match="unexpected keyword argument 'body'"):
        str(card(accent="#0969da", slots={"body": "Wrong slot."}))
