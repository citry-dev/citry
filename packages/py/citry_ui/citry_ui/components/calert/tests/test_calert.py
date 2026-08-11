from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component, Const
from citry_ui import CAlert, CIcon, CIconName


class _SelfReturningSafeString(str):
    __slots__ = ()

    def __html__(self):
        return self

    def __str__(self):
        return self


class _HostileHtml:
    def __html__(self):
        return 'Recovery" autofocus="true'


def _render(value: object) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "<main>{{ value }}</main>"

        def template_data(self, kwargs, slots):
            return {"value": value}

    return Page().render().serialize(deps_strategy="ignore")


def _root(html: str) -> str:
    match = re.search(r'<div[^>]+data-citry-ui-part="alert"[^>]*>', html)
    assert match is not None
    return match.group(0)


def _part(html: str, name: str) -> str:
    match = re.search(rf'<div[^>]+data-citry-ui-part="{name}"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_alert_schema_is_exact():
    assert [field.name for field in fields(CAlert.Kwargs)] == [
        "intent",
        "variant",
        "size",
        "announce",
        "icon",
        "icon_name",
        "actions_label",
        "class_",
        "style",
        "attrs",
        "actions_attrs",
    ]
    assert [field.name for field in fields(CAlert.Slots)] == ["title", "default", "actions"]
    assert get_type_hints(CAlert.Kwargs)["icon_name"] == CIconName | None


def test_alert_renders_complete_anatomy_and_keeps_actions_outside_live_region():
    html = _render(
        CAlert(
            intent="warn",
            variant="outline",
            size="lg",
            announce="polite",
            actions_label="Forecast actions",
            actions_attrs={"data-owner": "weather"},
            slots={
                "title": "Cloud cover",
                "default": "The western ridge may disappear.",
                "actions": "View forecast",
            },
        )
    )

    root = _root(html)
    content = _part(html, "content")
    actions = _part(html, "actions")
    assert 'data-intent="warn"' in root
    assert 'data-variant="outline"' in root
    assert 'data-size="lg"' in root
    assert 'data-announce="polite"' in root
    assert " data-icon" in root
    assert 'role="status"' in content
    assert 'role="group"' in actions
    assert 'aria-label="Forecast actions"' in actions
    assert 'data-owner="weather"' in actions
    assert html.index('data-citry-ui-part="indicator"') < html.index('data-citry-ui-part="content"')
    assert html.index('data-citry-ui-part="content"') < html.index('data-citry-ui-part="actions"')


@pytest.mark.parametrize(
    ("slots", "present", "absent"),
    [
        ({"default": "Message only"}, "message", "title"),
        ({"title": "Title only"}, "title", "message"),
    ],
)
def test_alert_supports_title_or_message_only(slots, present, absent):
    html = _render(CAlert(slots=slots))
    assert f'data-citry-ui-part="{present}"' in html
    assert f'data-citry-ui-part="{absent}"' not in html
    assert " role=" not in _part(html, "content")


def test_alert_requires_content_and_action_destinations():
    with pytest.raises(ValueError, match="requires a title or default message"):
        _render(CAlert())
    with pytest.raises(ValueError, match="actions_attrs requires"):
        _render(CAlert(actions_attrs={"data-test": "x"}, slots={"default": "Message"}))
    with pytest.raises(ValueError, match="actions_label requires"):
        _render(CAlert(actions_label="Actions", slots={"default": "Message"}))


def test_alert_renders_one_svg_with_automatic_or_fixed_registered_glyphs():
    automatic = _render(CAlert(slots={"default": "Automatic"}))
    fixed = _render(CAlert(icon_name="back", slots={"default": "Fixed"}))

    assert automatic.count("<svg") == 1
    assert automatic.count("data-cui-alert-intent=") == 4
    assert automatic.count("<g") == 4
    assert fixed.count("<svg") == 1
    assert "data-cui-alert-intent" not in fixed
    assert "cui-alert__glyph--logical" in fixed
    assert fixed.count("<g") == 1


def test_alert_icon_false_keeps_a_hidden_zero_behavior_destination():
    html = _render(CAlert(icon=False, slots={"default": "No icon"}))
    root = _root(html)
    indicator = _part(html, "indicator")

    assert " data-icon" not in root
    assert " hidden" in indicator
    assert "display: none !important" in CAlert.css


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"intent": "neutral"}, "intent must be one of"),
        ({"variant": "plain"}, "variant must be one of"),
        ({"size": "xl"}, "size must be one of"),
        ({"announce": "loud"}, "announce must be one of"),
        ({"icon": 1}, "icon must be a bool"),
        ({"icon_name": "missing"}, "documented icon name"),
        ({"actions_label": "   "}, "non-whitespace"),
        ({"actions_label": "bad\0label"}, r"U\+0000"),
    ],
)
def test_alert_rejects_invalid_inputs(kwargs, message):
    with pytest.raises((TypeError, ValueError), match=message):
        _render(CAlert(**kwargs, slots={"default": "Message", "actions": "Action"}))


@pytest.mark.parametrize(
    "value",
    [
        Markup('Recovery" autofocus="true'),
        _SelfReturningSafeString('Recovery" autofocus="true'),
        Const(Markup('Recovery" autofocus="true')),
    ],
)
def test_alert_detrusts_safe_action_labels(value):
    html = _render(
        CAlert(
            actions_label=value,
            slots={"default": "Message", "actions": "Retry"},
        )
    )
    actions = _part(html, "actions")

    assert ' autofocus="' not in actions
    assert "Recovery&#34; autofocus=&#34;true" in actions


def test_alert_rejects_arbitrary_html_action_label_values():
    with pytest.raises(TypeError, match="must be a string"):
        _render(
            CAlert(
                actions_label=_HostileHtml(),
                slots={"default": "Message", "actions": "Retry"},
            )
        )


def test_alert_merges_root_class_style_and_trusted_unrelated_attrs():
    html = _render(
        CAlert(
            class_="observatory-alert",
            style={"--cui-alert-radius": "1rem"},
            attrs={"class": "from-attrs", "data-observatory": "north", "x-show": "visible"},
            slots={"default": "Message"},
        )
    )
    root = _root(html)

    assert "observatory-alert" in root
    assert "from-attrs" in root
    assert "--cui-alert-radius: 1rem" in root
    assert 'data-observatory="north"' in root
    assert 'x-show="visible"' in root


@pytest.mark.parametrize(
    ("destination", "attribute"),
    [
        ("attrs", "role"),
        ("attrs", "ARIA-LIVE"),
        ("attrs", "tabindex"),
        ("attrs", ":contenteditable"),
        ("attrs", "data-intent"),
        ("attrs", "x-bind"),
        ("attrs", "x-for"),
        ("attrs", "x-html"),
        ("attrs", "x-if"),
        ("attrs", "x-ignore.self"),
        ("attrs", "x-teleport"),
        ("attrs", "data-citry-root"),
        ("actions_attrs", "role"),
        ("actions_attrs", "aria-label"),
        ("actions_attrs", "aria-labelledby"),
        ("actions_attrs", "aria-hidden"),
        ("actions_attrs", "x-bind:aria-live"),
        ("actions_attrs", ".tabindex"),
        ("actions_attrs", "x-text"),
        ("actions_attrs", "x-ignore"),
        ("actions_attrs", "x-teleport"),
    ],
)
def test_alert_rejects_owned_static_dynamic_and_structural_attrs(destination, attribute):
    with pytest.raises(ValueError, match="CAlert"):
        _render(
            CAlert(
                **{destination: {attribute: "value"}},
                slots={"default": "Message", "actions": "Retry"},
            )
        )


def test_alert_and_icon_share_logical_and_physical_registered_glyph_resolution():
    alert = _render(CAlert(icon_name="back", slots={"default": "Back"}))
    icon = _render(CIcon(name="back"))

    assert "cui-alert__glyph--logical" in alert
    assert "cui-icon--logical" in icon
    glyph = '<path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path>'
    assert glyph in alert
    assert glyph in icon


def test_alert_assets_keep_the_frozen_client_and_environment_contracts():
    assert "data-citry-alert-initialized" in CAlert.js
    assert "addEventListener" not in CAlert.js
    assert "MutationObserver" not in CAlert.js
    assert 'announce === "polite"' in CAlert.js
    assert 'announce === "assertive"' in CAlert.js
    assert "@layer citry-ui.theme" in CAlert.css
    assert "@media (forced-colors: active)" in CAlert.css
    assert "@media print" in CAlert.css
    assert "overflow: hidden" not in CAlert.css
    assert "z-index" not in CAlert.css
