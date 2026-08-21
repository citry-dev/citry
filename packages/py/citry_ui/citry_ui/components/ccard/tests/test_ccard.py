from __future__ import annotations

import re
from dataclasses import fields

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CCard
from citry_ui.quality.asset_sources import read_component_source_css


def _render(card: object, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>{{ card }}</main>{{ css }}
        """

        def template_data(self, kwargs, slots):
            return {
                "card": card,
                "css": app.get("css")() if include_css else "",
            }

    return str(Page())


def test_card_schemas_keep_every_slot_optional_and_part_destination_explicit():
    assert [field.name for field in fields(CCard.Kwargs)] == [
        "tag",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
        "media_attrs",
        "header_attrs",
        "header_actions_attrs",
        "body_attrs",
        "footer_attrs",
        "actions_attrs",
    ]
    assert [field.name for field in fields(CCard.Slots)] == [
        "media",
        "header",
        "header_actions",
        "default",
        "footer",
        "actions",
    ]
    assert all(field.default is None for field in fields(CCard.Slots))


def test_body_only_card_uses_the_neutral_root_and_omits_other_anatomy():
    html = _render(CCard(slots={"default": "Reading chair"}))

    assert '<div class="cui-card" data-variant="elevated" data-size="md"' in html
    assert 'data-citry-ui-part="card"' in html
    assert 'data-citry-ui-part="body"' in html
    assert "Reading chair" in html
    assert 'data-citry-ui-part="media"' not in html
    assert 'data-citry-ui-part="header"' not in html
    assert 'data-citry-ui-part="footer"' not in html


def test_header_only_and_media_plus_actions_do_not_require_an_empty_body():
    header = _render(CCard(slots={"header": "Material note"}))
    media_actions = _render(
        CCard(
            slots={
                "media": '<img src="chair.webp" alt="Oak chair">',
                "actions": "Compare",
            }
        )
    )

    assert 'data-citry-ui-part="header"' in header
    assert 'data-citry-ui-part="body"' not in header
    assert 'data-citry-ui-part="media"' in media_actions
    assert 'data-citry-ui-part="actions"' in media_actions
    assert 'data-citry-ui-part="body"' not in media_actions


def test_full_anatomy_renders_once_in_the_documented_order():
    html = _render(
        CCard(
            tag="article",
            variant="outline",
            size="lg",
            slots={
                "media": "Media",
                "header": "Header",
                "header_actions": "Save",
                "default": "Body",
                "footer": "Footer",
                "actions": "Buy",
            },
        )
    )

    root = re.search(r'<article[^>]+data-citry-ui-part="card"[^>]*>', html)
    assert root is not None
    assert 'data-variant="outline"' in root.group(0)
    assert 'data-size="lg"' in root.group(0)
    parts = re.findall(r'data-citry-ui-part="([^"]+)"', html)
    assert parts == ["card", "media", "header", "header-actions", "body", "footer", "actions"]
    assert "cui-card__header-content" in html
    assert "cui-card__footer-content" in html
    assert 'data-citry-ui-part="header-content"' not in html
    assert 'data-citry-ui-part="footer-content"' not in html


def test_media_can_be_the_only_supplied_section():
    html = _render(CCard(slots={"media": "Media only"}))

    assert html.count('data-citry-ui-part="card"') == 1
    assert html.count('data-citry-ui-part="media"') == 1
    assert 'data-citry-ui-part="header"' not in html
    assert 'data-citry-ui-part="body"' not in html
    assert 'data-citry-ui-part="footer"' not in html


def test_root_and_part_attrs_have_exact_destinations():
    html = _render(
        CCard(
            class_=["catalog-card", {"is-featured": True}],
            style={"--cui-card-radius": "1rem"},
            attrs={"id": "chair-card", "class": "from-attrs", "data-catalog": "seating"},
            media_attrs={"data-region": "photograph"},
            header_attrs={"data-region": "heading"},
            header_actions_attrs={"role": "group", "aria-label": "Save options"},
            body_attrs={"data-region": "description"},
            footer_attrs={"data-region": "availability"},
            actions_attrs={"role": "group", "aria-label": "Chair actions"},
            slots={
                "media": "Media",
                "header": "Header",
                "header_actions": "Save",
                "default": "Body",
                "footer": "Footer",
                "actions": "Buy",
            },
        )
    )

    root = re.search(r'<div[^>]+data-citry-ui-part="card"[^>]*>', html)
    assert root is not None
    assert 'id="chair-card"' in root.group(0)
    assert 'class="cui-card from-attrs catalog-card is-featured"' in root.group(0)
    assert 'style="--cui-card-radius: 1rem;"' in root.group(0)
    assert 'data-catalog="seating"' in root.group(0)
    assert re.search(r'<div[^>]+data-region="photograph"[^>]+data-citry-ui-part="media"', html)
    assert re.search(r'<div[^>]+data-region="heading"[^>]+data-citry-ui-part="header"', html)
    assert re.search(r'<div[^>]+aria-label="Save options"[^>]+data-citry-ui-part="header-actions"', html)
    assert re.search(r'<div[^>]+data-region="description"[^>]+data-citry-ui-part="body"', html)
    assert re.search(r'<div[^>]+data-region="availability"[^>]+data-citry-ui-part="footer"', html)
    assert re.search(r'<div[^>]+aria-label="Chair actions"[^>]+data-citry-ui-part="actions"', html)


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"tag": 2}, TypeError, "tag must be a string"),
        ({"tag": "main"}, ValueError, "tag must be one of"),
        ({"variant": 2}, TypeError, "variant must be a string"),
        ({"variant": "flat"}, ValueError, "variant must be one of"),
        ({"size": 2}, TypeError, "size must be a string"),
        ({"size": "xl"}, ValueError, "size must be one of"),
        ({"attrs": []}, TypeError, "attrs must be a mapping"),
        ({"body_attrs": []}, TypeError, "body_attrs must be a mapping"),
    ],
)
def test_invalid_inputs_fail_deterministically(kwargs, error, match):
    with pytest.raises(error, match=match):
        _render(CCard(**kwargs, slots={"default": "Body"}))


def test_card_rejects_no_supplied_slot():
    with pytest.raises(ValueError, match="at least one supplied slot"):
        _render(CCard())


@pytest.mark.parametrize(
    ("input_name", "slots"),
    [
        ("media_attrs", {"default": "Body"}),
        ("header_attrs", {"default": "Body"}),
        ("header_actions_attrs", {"header": "Header"}),
        ("body_attrs", {"header": "Header"}),
        ("footer_attrs", {"default": "Body"}),
        ("actions_attrs", {"footer": "Footer"}),
    ],
)
def test_nonempty_part_attrs_require_their_destination(input_name, slots):
    with pytest.raises(ValueError, match=rf"{input_name} requires"):
        _render(CCard(**{input_name: {"data-test": "value"}}, slots=slots))


@pytest.mark.parametrize(
    "input_name",
    [
        "media_attrs",
        "header_attrs",
        "header_actions_attrs",
        "body_attrs",
        "footer_attrs",
        "actions_attrs",
    ],
)
def test_empty_part_attrs_are_harmless_when_the_destination_is_absent(input_name):
    html = _render(CCard(**{input_name: {}}, slots={"default": "Body"}))

    assert "Body" in html


@pytest.mark.parametrize(
    ("input_name", "attribute", "slots"),
    [
        ("attrs", "data-variant", {"default": "Body"}),
        ("attrs", "data-size", {"default": "Body"}),
        ("attrs", "data-citry-ui-part", {"default": "Body"}),
        ("media_attrs", "data-citry-ui-part", {"media": "Media"}),
        ("header_attrs", "data-citry-morph", {"header": "Header"}),
        ("body_attrs", "data-cid", {"default": "Body"}),
        ("footer_attrs", "data-cev-action", {"footer": "Footer"}),
        ("actions_attrs", "data-citry-key", {"actions": "Action"}),
    ],
)
def test_owned_and_reserved_runtime_attrs_are_rejected(input_name, attribute, slots):
    with pytest.raises(ValueError, match=r"owned attribute|reserved Citry runtime"):
        _render(CCard(**{input_name: {attribute: "consumer"}}, slots=slots))


def test_hostile_slot_text_is_escaped_and_trusted_part_listeners_are_preserved():
    html = _render(
        CCard(
            body_attrs={"x-data": "{}", "@click": "opened = true"},
            slots={"default": "<script>window.__cardPwned = true</script>"},
        )
    )

    assert "&lt;script&gt;window.__cardPwned = true&lt;/script&gt;" in html
    assert "<script>window.__cardPwned" not in html
    assert 'x-data="{}"' in html
    assert '@click="opened = true"' in html


def test_card_has_static_css_and_no_javascript_asset():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)
    card = installed[CCard]
    runtime_css = card.get_css()
    css = read_component_source_css("ccard")

    assert card.get_js() is None
    assert runtime_css is not None
    assert "--cui-card-background" in css
    assert "--cui-card-actions-justify" in css
    assert "overflow: clip" in css
    assert "position: static" in css
    assert "@media (forced-colors: active)" in css
    assert "@media print" in css


def test_template_schema_rejects_unknown_and_duplicate_fills():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Unknown(Component):
        citry = app
        template = """
          <c-CCard>
            <c-fill name="unknown">No</c-fill>
          </c-CCard>
        """

    class Duplicate(Component):
        citry = app
        template = """
          <c-CCard>
            <c-fill name="header">One</c-fill>
            <c-fill name="header">Two</c-fill>
          </c-CCard>
        """

    with pytest.raises(Exception, match=r"unknown|slot"):
        str(Unknown())
    with pytest.raises(Exception, match=r"duplicate|header"):
        str(Duplicate())
