"""Checked `$c-tr` server records and marker behavior."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from markupsafe import Markup

from citry import Citry, Component
from citry._vue.capture import PreparedElementOpen, PreparedTextValue, render_prepared_direct
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.events import default_events_producer
from citry.citry_render import CitryRender
from citry.ext.i18n.usage import CLIENT_CONTEXT_KEY, EXTRA_KEY

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry_element import CitryElement


def _app() -> Citry:
    return Citry(
        extensions_defaults={
            "i18n": {
                "source_locale": "en-US",
                "locales": ("en-US", "cs-CZ"),
            }
        }
    )


def _prepared_i18n(
    component: CitryElement,
    *,
    provides: Mapping[str, object] | None = None,
) -> tuple[CitryRender, dict[str, object]]:
    """Read i18n metadata from the actual Vue producer and retain typed parts."""
    app = component.comp_cls.citry
    rendered = render_prepared_direct(component, provides=provides)
    manifest = default_events_producer(app).prepare_from_render(
        rendered,
        citry=app,
        app_id="i18n-bindings-unit",
        revision=0,
    )
    extensions = manifest["extensions"]
    assert type(extensions) is dict
    extension = extensions["i18n"]
    assert type(extension) is dict
    assert extension["schemaVersion"] == 1
    payload = extension["payload"]
    assert type(payload) is dict
    return rendered, payload


def _prepared_parts(value: object):
    if isinstance(value, CitryRender):
        for part in value.parts:
            yield from _prepared_parts(part)
        return
    yield value


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

    rendered, manifest = _prepared_i18n(Page())
    html = rendered.serialize(deps_strategy="ignore")
    assert "$c-tr" not in html
    marker = re.search(r'data-citry-i18n-binding="([^"]+)"', html)
    assert marker is not None
    requirement = manifest["requirements"][0]
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
    binding_id = requirement["bindings"][0]["id"]
    assert marker.group(1) == binding_id
    assert any(
        isinstance(part, PreparedElementOpen)
        and any(binding.operand == binding_id for binding in part.browser_bindings)
        for part in _prepared_parts(rendered)
    )


def test_text_binding_requires_and_captures_one_complete_translation() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main"><span $c-tr:loading>{{ tr("loading") }}</span></c-i18n>\
"""
        messages = "loading = Loading"

    rendered, manifest = _prepared_i18n(Page())
    html = rendered.serialize(deps_strategy="ignore")
    assert ">Loading</span>" in html
    binding = manifest["requirements"][0]["bindings"][0]
    assert binding["target"] == {"kind": "text"}
    assert any(
        isinstance(part, PreparedTextValue)
        and part.value == "Loading"
        and part.browser_binding is not None
        and part.browser_binding.operand == binding["id"]
        for part in _prepared_parts(rendered)
    )


def test_prepared_text_binding_escapes_translation_without_compiling_vue_syntax() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main"><span $c-tr:literal>{{ tr("literal") }}</span></c-i18n>\
"""
        messages = 'literal = Angle < & {"{{ state }}"}'

    rendered, manifest = _prepared_i18n(Page())
    omitted = rendered.serialize(security_javascript="omit")

    binding = manifest["requirements"][0]["bindings"][0]
    assert binding["target"] == {"kind": "text"}
    assert any(
        isinstance(part, PreparedTextValue)
        and part.value == "Angle < & {{ state }}"
        and part.browser_binding is not None
        and part.browser_binding.operand == binding["id"]
        for part in _prepared_parts(rendered)
    )
    assert ">Angle &lt; &amp; {{ state }}</span>" in omitted
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        template_context_names=("$citryI18nBinding", "$i18n"),
    )
    templates = [value.template for value in assembly.compile_inputs.values()]
    assert all("{{ state }}" not in template for template in templates)


def test_prepared_inactive_text_binding_keeps_plain_text_typed_without_trusting_html() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <span c-$c-tr:save="enabled">{{ label }}</span>
</c-i18n>\
"""
        messages = "save = Save"

        def template_data(self, kwargs, slots):
            return {"enabled": False, "label": kwargs["label"]}

    def leaves(value: object):
        if isinstance(value, CitryRender):
            for part in value.parts:
                yield from leaves(part)
            return
        yield value

    plain = tuple(leaves(render_prepared_direct(Page(label="Plain & safe"))))

    assert any(isinstance(part, PreparedTextValue) and part.value == "Plain & safe" for part in plain)
    with pytest.raises(TypeError, match="unsupported raw output: Markup"):
        render_prepared_direct(Page(label=Markup("<strong>Trusted</strong>")))


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


def test_dormant_dynamic_binding_is_rejected_instead_of_rendered_as_html() -> None:
    app = Citry()

    class Page(Component):
        citry = app
        template = '<button c-bind="attrs">Save</button>'

        def template_data(self, kwargs, slots):
            return {"attrs": {"aria-label": "Save", "$c-tr:save[aria-label]": True}}

    with pytest.raises(RuntimeError, match="no active i18n catalog"):
        Page().render()


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

    _rendered, manifest = _prepared_i18n(Page())
    bindings = manifest["requirements"][0]["bindings"]
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
            rendered, payload = _prepared_i18n(Bound(), provides=client_provides)
            assert payload["requirements"][0]["bindings"]
            return rendered.serialize(deps_strategy="ignore")

        def render_server() -> str:
            return render_prepared_direct(Bound()).serialize(deps_strategy="ignore")

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

    rendered, manifest = _prepared_i18n(Page())
    html = rendered.serialize(deps_strategy="ignore")
    assert 'title="Save"' in html
    assert re.search(r"<button\b[^>]*\bdata-citry-i18n-binding=", html) is None
    assert manifest["requirements"] == []


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

    _rendered, manifest = _prepared_i18n(Page())
    bindings = manifest["requirements"][0]["bindings"]
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


def test_binding_rejects_equal_text_replacement_without_translation_identity() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <button c-title="tr('save')" $c-tr:save[title] c-bind="{'title': tr('save') + ''}"></button>
</c-i18n>\
"""
        messages = "save = Save"

    # The spread produces the same visible string from the same message ID,
    # but its concatenation loses the captured translation identity.
    with pytest.raises(
        RuntimeError,
        match=r"must pair with the complete winning 'title' value returned directly by tr\(\)",
    ):
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

    rendered, manifest = _prepared_i18n(Page())
    event_openings = [
        part
        for part in _prepared_parts(rendered)
        if isinstance(part, PreparedElementOpen) and part.event_bindings and part.browser_bindings
    ]
    assert len(event_openings) == 1
    assert manifest["requirements"][0]["bindings"]


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
