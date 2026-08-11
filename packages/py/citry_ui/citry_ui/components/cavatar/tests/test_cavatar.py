from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CAvatar


def _render(avatar: object, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "<main>{{ avatar }}</main>{{ css }}"

        def template_data(self, kwargs, slots):
            return {"avatar": avatar, "css": app.get("css")() if include_css else ""}

    return str(Page())


def _root(html: str) -> str:
    match = re.search(r'<span[^>]+data-citry-ui-part="avatar"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_avatar_schema_and_type_hints_are_public():
    assert [field.name for field in fields(CAvatar.Kwargs)] == [
        "src",
        "alt",
        "variant",
        "size",
        "shape",
        "class_",
        "style",
        "attrs",
        "img_attrs",
    ]
    assert [field.name for field in fields(CAvatar.Slots)] == ["default"]
    assert get_type_hints(CAvatar.Kwargs)["shape"] is not None


def test_default_avatar_is_decorative_fallback_with_exact_anatomy():
    html = _render(CAvatar())
    root = _root(html)
    assert 'data-status="fallback"' in root
    assert 'data-variant="soft"' in root
    assert 'data-size="md"' in root
    assert 'data-shape="circle"' in root
    assert "role=" not in root
    assert "aria-label" not in root
    assert len(re.findall(r'<span[^>]+data-citry-ui-part="fallback"', html)) == 1
    assert len(re.findall(r'<img[^>]+data-citry-ui-part="image"', html)) == 1
    assert re.search(r'<img[^>]+alt(?:="")?[^>]+hidden', html)


def test_named_image_uses_one_root_semantic_and_decorative_internal_image():
    html = _render(CAvatar(src="/mira.jpg", alt="Mira Vale", slots={"default": "MV"}))
    root = _root(html)
    assert 'role="img"' in root
    assert 'aria-label="Mira Vale"' in root
    assert 'data-status="loading"' in root
    assert 'src="/mira.jpg"' in html
    assert re.search(r'<img[^>]+alt(?:="")?', html)
    assert "MV" in html


def test_root_and_image_attributes_have_distinct_destinations():
    html = _render(
        CAvatar(
            alt="Fen guide",
            class_="expedition-avatar",
            style={"--cui-avatar-size": "4rem"},
            attrs={"data-guide": "fern"},
            img_attrs={"loading": "lazy", "decoding": "async", "class": "portrait"},
        )
    )
    root = _root(html)
    assert "expedition-avatar" in root
    assert 'style="--cui-avatar-size: 4rem;' in root
    assert 'data-guide="fern"' in root
    image = re.search(r'<img[^>]+data-citry-ui-part="image"[^>]*>', html)
    assert image is not None
    assert 'loading="lazy"' in image.group(0)
    assert 'decoding="async"' in image.group(0)
    assert "portrait" in image.group(0)


@pytest.mark.parametrize(
    ("input_name", "bad_value", "error", "match"),
    [
        ("src", "", ValueError, "src must be non-empty"),
        ("src", 3, TypeError, "src must be a string or None"),
        ("alt", None, TypeError, "alt must be a string"),
        ("variant", "raised", ValueError, "variant must be one of"),
        ("size", "xl", ValueError, "size must be one of"),
        ("shape", "pill", ValueError, "shape must be one of"),
        ("attrs", [], TypeError, "attrs must be a mapping"),
        ("img_attrs", [], TypeError, "img_attrs must be a mapping"),
    ],
)
def test_invalid_inputs_fail_deterministically(input_name, bad_value, error, match):
    with pytest.raises(error, match=match):
        _render(CAvatar(**{input_name: bad_value}))


@pytest.mark.parametrize(
    ("destination", "attribute"),
    [
        ("attrs", "role"),
        ("attrs", "ARIA-LABEL"),
        ("attrs", "tabindex"),
        ("attrs", "data-status"),
        ("attrs", ":data-shape"),
        ("attrs", "x-if"),
        ("attrs", "data-citry-morph"),
        ("img_attrs", "src"),
        ("img_attrs", "srcset"),
        ("img_attrs", "alt"),
        ("img_attrs", "onload"),
        ("img_attrs", "@error"),
        ("img_attrs", "x-bind:src"),
    ],
)
def test_owned_attributes_and_runtime_paths_are_rejected(destination, attribute):
    with pytest.raises(ValueError, match=r"cannot|inert"):
        _render(CAvatar(**{destination: {attribute: "consumer"}}))


def test_direct_strings_are_detrusted_and_escaped():
    html = _render(CAvatar(src=Markup('/a" onload="evil'), alt=Markup('Mira" aria-hidden="true')))
    assert 'onload="evil"' not in html
    assert 'aria-hidden="true"' not in _root(html)
    assert "&quot;" in html
    with pytest.raises(ValueError, match=r"U\+0000"):
        _render(CAvatar(alt="bad\x00name"))


def test_css_and_js_expose_the_ratified_surface():
    html = _render(CAvatar(), include_css=True)
    for variable in (
        "size",
        "background",
        "foreground",
        "border-color",
        "border-width",
        "radius",
        "font-size",
        "font-weight",
        "image-fit",
        "image-position",
    ):
        assert f"--_cui-avatar-{variable}: var(--cui-avatar-{variable}," in html
    assert "onStatusChange" in CAvatar.js
    assert 'addEventListener("load"' in CAvatar.js
    assert 'addEventListener("error"' in CAvatar.js
