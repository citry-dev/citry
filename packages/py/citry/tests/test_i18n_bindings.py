"""Checked `$c-tr` server records and marker behavior."""

from __future__ import annotations

import json
import re

import pytest

from citry import Citry, Component
from citry.ext.i18n.usage import CLIENT_CONTEXT_KEY, EXTRA_KEY

_MANIFEST = re.compile(r'<script type="application/json" data-citry-i18n>(.*?)</script>', re.DOTALL)


def _app() -> Citry:
    return Citry(
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
            }
        }
    )


def _manifest(html: str) -> dict[str, object]:
    match = _MANIFEST.search(html)
    assert match is not None
    return json.loads(match.group(1))


def test_attribute_binding_emits_only_opaque_marker_and_checked_record() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <button c-aria-label="tr('save')" $c-tr:save[aria-label]>Save</button>
</c-i18n>\
"""
        messages = "save = Save"

    html = Page().render().serialize()
    assert "$c-tr" not in html
    marker = re.search(r'data-citry-i18n-binding="([^"]+)"', html)
    assert marker is not None
    requirement = _manifest(html)["requirements"][0]
    assert requirement["rendered_locale"] == "en-US"
    assert requirement["outputs"] == ["save"]
    assert requirement["bindings"] == [
        {
            "id": marker.group(1),
            "message": "save",
            "target": {"kind": "attribute", "name": "aria-label"},
            "values": {},
        }
    ]


def test_text_binding_requires_and_captures_one_complete_translation() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main"><span $c-tr:loading>{{ tr("loading") }}</span></c-i18n>\
"""
        messages = "loading = Loading"

    html = Page().render().serialize()
    assert ">Loading</span>" in html
    binding = _manifest(html)["requirements"][0]["bindings"][0]
    assert binding["target"] == {"kind": "text"}


def test_ordinary_spread_before_one_expression_does_not_create_a_text_binding() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = '<progress c-bind="attrs">{{ label }}</progress>'

        def template_data(self, kwargs, slots):
            return {"attrs": {"max": 10, "value": 4}, "label": "Four of ten"}

    html = Page().render().serialize()

    assert '<progress max="10" value="4"' in html
    assert ">Four of ten</progress>" in html
    assert "data-citry-i18n-binding" not in html


def test_server_dynamic_and_spread_forms_preserve_values_expression() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <button
    c-title="tr('dismiss', title=title)"
    c-$c-tr:dismiss[title]="browser_expression"
  ></button>
  <button c-bind="{
    'aria-label': tr('dismiss', title=title),
    '$c-tr:dismiss[aria-label]': '{ title: toast.title }',
  }"></button>
</c-i18n>\
"""
        messages = "# @param {str} $title\ndismiss = Dismiss { $title }"

        def template_data(self, kwargs, slots):
            return {
                "browser_expression": "{ title: toast.title }",
                "title": "Notice",
            }

    bindings = _manifest(Page().render().serialize())["requirements"][0]["bindings"]
    assert [binding["values_expression"] for binding in bindings] == [
        "{ title: toast.title }",
        "{ title: toast.title }",
    ]
    assert [binding["values"] for binding in bindings] == [
        {"title": {"type": "str", "value": "Notice"}},
        {"title": {"type": "str", "value": "Notice"}},
    ]


def test_binding_is_dormant_without_client_provider() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = "<button c-title=\"tr('save')\" $c-tr:save[title]>Save</button>"
        messages = "save = Save"

    html = Page().render().serialize()
    assert 'title="Save"' in html
    assert "$c-tr" not in html
    assert "data-citry-i18n-binding" not in html
    assert "data-citry-i18n" not in html


def test_binding_constness_stays_render_local_in_both_provider_orders() -> None:
    def render_in_order(*, client_first: bool) -> tuple[str, str]:
        app = _app()
        app.set_mounted_prefix("/citry")

        class Page(Component):
            citry = app
            template = '<c-i18n c-client="True" tag="main"></c-i18n>'

        class Bound(Component):
            citry = app
            template = "<button c-title=\"tr('save')\" $c-tr:save[title]>Save</button>"
            messages = "save = Save"

        rendered_page = Page().render()
        (provider,) = [
            record for record in rendered_page.context.extra[EXTRA_KEY].values() if record.provider is not None
        ]
        client_provides = {
            "citry_i18n": provider.provider.context,
            CLIENT_CONTEXT_KEY: provider.render_id,
        }

        def render_client() -> str:
            return Bound().render(provides=client_provides).serialize(deps_strategy="fragment")

        def render_server() -> str:
            return Bound().render().serialize(deps_strategy="fragment")

        return (render_client(), render_server()) if client_first else (render_server(), render_client())

    client_first, client_then_server = render_in_order(client_first=True)
    server_first, server_then_client = render_in_order(client_first=False)
    marker = re.compile(r"<button\b[^>]*\bdata-citry-i18n-binding=")

    assert marker.search(client_first)
    assert marker.search(client_then_server) is None
    assert marker.search(server_first) is None
    assert marker.search(server_then_client)


def test_later_spread_false_removes_a_direct_binding_destination() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <button c-title="tr('save')" $c-tr:save[title] c-bind="{'$c-tr:save[title]': False}"></button>
</c-i18n>\
"""
        messages = "save = Save"

    html = Page().render().serialize()
    assert 'title="Save"' in html
    assert re.search(r"<button\b[^>]*\bdata-citry-i18n-binding=", html) is None


def test_dynamic_true_enables_a_binding_without_a_values_expression() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <button c-title="tr('save')" c-$c-tr:save[title]="enabled"></button>
  <button c-bind="{'aria-label': tr('save'), '$c-tr:save[aria-label]': enabled}"></button>
</c-i18n>\
"""
        messages = "save = Save"

        def template_data(self, kwargs, slots):
            return {"enabled": True}

    bindings = _manifest(Page().render().serialize())["requirements"][0]["bindings"]
    assert len(bindings) == 2
    assert all("values_expression" not in binding for binding in bindings)


def test_binding_rejects_a_different_server_translation() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <button c-title="tr('other')" $c-tr:save[title]></button>
</c-i18n>\
"""
        messages = "save = Save\nother = Other"

    with pytest.raises(RuntimeError, match=r"names 'save'.*resolved 'other'"):
        Page().render()


def test_events_compilation_preserves_neighboring_translation_binding() -> None:
    app = _app()

    class Page(Component):
        citry = app

        class Events:
            def save(self):
                return None

        template = """\
<c-i18n c-client="True" tag="main">
  <button @c-click="save" c-title="tr('save')" $c-tr:save[title]>Save</button>
</c-i18n>\
"""
        messages = "save = Save"

    html = Page().render().serialize()
    assert "data-cev-on" in html
    assert "data-citry-i18n-binding" in html


@pytest.mark.parametrize(
    ("attribute", "match"),
    [
        ("$c-tr", "requires ':'"),
        ("$c-tr[]", "requires ':'"),
        ("$c-tr:", "non-empty message ID"),
        ("$c-tr:save[]", "non-empty HTML attribute"),
        ("$c-tr:save.", "non-empty Fluent attribute"),
    ],
)
def test_every_reserved_directive_spelling_is_validated(attribute: str, match: str) -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = f"<button {attribute}></button>"

    with pytest.raises(ValueError, match=match):
        Page().render()


@pytest.mark.parametrize("attribute", ["$c-tr", "$c-tr[]", "$c-tr:", "$c-tr:save[]", "$c-tr:save."])
def test_malformed_spread_directive_keys_are_rejected(attribute: str) -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = '<button c-bind="attrs"></button>'

        def template_data(self, kwargs, slots):
            return {"attrs": {attribute: True}}

    with pytest.raises(ValueError, match=r"requires|non-empty"):
        Page().render()


def test_malformed_owned_name_is_rejected_when_i18n_is_unconfigured() -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<button $c-tr:></button>"

    with pytest.raises(ValueError, match="non-empty message ID"):
        Page().render()
