"""Checked `$c-tr` server records and marker behavior."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

import pytest
from markupsafe import Markup

from citry import Citry, Component, VueCodeError
from citry._vue.capture import PreparedElementOpen, PreparedTextValue, render_prepared_direct
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.events import default_events_producer
from citry.citry_render import CitryRender
from citry.ext.i18n.usage import CLIENT_CONTEXT_KEY, EXTRA_KEY
from citry_core import _rust

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry_element import CitryElement


class _StrSubclass(str):
    """A key whose overridden methods try to hide its real text."""

    __slots__ = ()

    def lower(self) -> str:  # type: ignore[override]
        return "plain"

    def casefold(self) -> str:  # type: ignore[override]
        return "plain"

    def startswith(self, *args: object, **kwargs: object) -> bool:  # type: ignore[override]
        return False


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


def test_null_capable_text_binding_keeps_untranslated_plain_text() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <span $c-tr:save="useCatalog ? {} : null">{{ label }}</span>
</c-i18n>\
"""
        messages = "save = Save"

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    def leaves(value: object):
        if isinstance(value, CitryRender):
            for part in value.parts:
                yield from leaves(part)
            return
        yield value

    plain = tuple(leaves(render_prepared_direct(Page(label="Plain & safe"))))

    # A body that no tr() call produced keeps its exact text, and the
    # browser receives that text as the value to show for `null`.
    (text,) = [part for part in plain if isinstance(part, PreparedTextValue) and part.value == "Plain & safe"]
    assert text.browser_binding is not None
    assert text.browser_binding.fallback == "Plain & safe"
    assert text.browser_binding.values_expression == "useCatalog ? {} : null"
    with pytest.raises(RuntimeError, match="renders HTML markup"):
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


def test_spread_binding_is_rejected_without_an_i18n_catalog() -> None:
    app = Citry()

    class Page(Component):
        citry = app
        template = '<button c-bind="attrs">Save</button>'

        def template_data(self, kwargs, slots):
            return {"attrs": {"aria-label": "Save", "$c-tr:save[aria-label]": True}}

    with pytest.raises(VueCodeError, match=r"sets '\$c-tr:save\[aria-label\]'.*js_data\(\)"):
        Page().render()


def test_authored_values_expression_is_kept_exactly() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <button
    c-title="tr('dismiss', title=title)"
    $c-tr:dismiss[title]="{ title: toast.title }"
  ></button>
  <span $c-tr:dismiss="{ title: toast.title }">{{ tr('dismiss', title=title) }}</span>
</c-i18n>\
"""
        messages = "# @param {str} $title\ndismiss = Dismiss { $title }"

        def template_data(self, kwargs, slots):
            return {"title": "Notice"}

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


_ATTACK = "{ title: (globalThis.ran = 1, 'x') }"


@pytest.mark.parametrize(
    ("element", "data"),
    [
        # The `c-` form, whose Python value used to become the expression.
        ('<span c-$c-tr:dismiss="expression">{{ tr("dismiss", title="t") }}</span>', {"expression": _ATTACK}),
        (
            '<button c-title="tr(\'dismiss\', title=\'t\')" c-$c-tr:dismiss[title]="expression"></button>',
            {"expression": _ATTACK},
        ),
        ('<span c-$C-TR:dismiss="expression">{{ tr("dismiss", title="t") }}</span>', {"expression": _ATTACK}),
        ('<span c-$c-tr:dismiss="True">{{ tr("dismiss", title="t") }}</span>', {}),
        ('<span c-$c-tr:dismiss="None">{{ tr("dismiss", title="t") }}</span>', {}),
        # A key in a spread mapping, in every spelling the parser reserves.
        ('<span c-bind="attrs">{{ tr("dismiss", title="t") }}</span>', {"attrs": {"$c-tr:dismiss": _ATTACK}}),
        (
            '<button c-title="tr(\'dismiss\', title=\'t\')" c-bind="attrs"></button>',
            {"attrs": {"$c-tr:dismiss[title]": _ATTACK}},
        ),
        ('<span c-bind="attrs">{{ tr("dismiss", title="t") }}</span>', {"attrs": {"$C-TR:dismiss": _ATTACK}}),
        ('<span c-bind="attrs">{{ tr("dismiss", title="t") }}</span>', {"attrs": {"$c-tr": _ATTACK}}),
        ('<span c-bind="attrs">{{ tr("dismiss", title="t") }}</span>', {"attrs": {"$c-Tr.x": _ATTACK}}),
        ('<span c-bind="attrs">{{ tr("dismiss", title="t") }}</span>', {"attrs": {"$c-tr[title]": _ATTACK}}),
        ('<span c-bind="attrs">{{ tr("dismiss", title="t") }}</span>', {"attrs": {"$c-tr:dismiss": True}}),
        ('<span c-bind="attrs">{{ tr("dismiss", title="t") }}</span>', {"attrs": {"$c-tr:dismiss": None}}),
        (
            '<span c-bind="attrs">{{ tr("dismiss", title="t") }}</span>',
            {"attrs": {_StrSubclass("$c-tr:dismiss"): _ATTACK}},
        ),
    ],
)
def test_python_data_cannot_supply_a_binding(element: str, data: dict[str, object]) -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = f'<c-i18n c-client="True" tag="main">{element}</c-i18n>'
        messages = "# @param {str} $title\ndismiss = Dismiss { $title }"

        def template_data(self, kwargs, slots):
            return data

    # The name is rejected whatever its value, so Python never chooses
    # whether a binding exists or what its browser expression says.
    with pytest.raises(VueCodeError, match=r"\$c-tr binding.*js_data\(\)"):
        Page().render()


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


def test_null_capable_attribute_binding_keeps_an_untranslated_value() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <button c-title="label" $c-tr:save[title]="useCatalog ? {} : null"></button>
</c-i18n>\
"""
        messages = "save = Save"

        def template_data(self, kwargs, slots):
            return {"label": "My own label"}

    rendered, manifest = _prepared_i18n(Page())
    html = rendered.serialize(deps_strategy="ignore")
    assert 'title="My own label"' in html
    (binding,) = manifest["requirements"][0]["bindings"]
    # No tr() call filled the attribute, so the binding carries no server values.
    assert binding["values"] == {}
    (opening,) = [part for part in _prepared_parts(rendered) if isinstance(part, PreparedElementOpen)]
    assert [item.fallback for item in opening.browser_bindings] == ["My own label"]


@pytest.mark.parametrize(
    "expression",
    [
        "{}",
        "useCatalog ? {} : 'null'",
        "useCatalog ? {} : nullValue",
        "useCatalog ? {} : values.null",
        "useCatalog /* null */ ? {} : {}",
    ],
)
def test_binding_without_a_null_token_still_requires_tr(expression: str) -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = f"""\
<c-i18n c-client="True" tag="main">
  <span $c-tr:save="{expression}">{{{{ label }}}}</span>
</c-i18n>\
"""
        messages = "save = Save"

        def template_data(self, kwargs, slots):
            return {"label": "Mine"}

    # Only a `null` keyword token can mean "keep the server text"; a string,
    # a longer name, a property, or a comment that spells null does not.
    with pytest.raises(RuntimeError, match=r"exactly one complete \{\{ tr\(\.\.\.\) \}\} expression"):
        Page().render()


def test_null_capable_binding_still_checks_a_tr_message() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <span $c-tr:save="useCatalog ? {} : null">{{ tr('other') }}</span>
  <button c-title="tr('other')" $c-tr:save[title]="useCatalog ? {} : null"></button>
</c-i18n>\
"""
        messages = "save = Save\nother = Other"

    with pytest.raises(RuntimeError, match=r"names 'save'.*resolved 'other'"):
        Page().render()


def test_null_capable_attribute_binding_rejects_a_composed_tr_value() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <button c-title="tr('save') + '!'" $c-tr:save[title]="useCatalog ? {} : null"></button>
</c-i18n>\
"""
        messages = "save = Save"

    # The value called tr(), so it is not an author's own label, and a
    # composed translation still has to pair with tr() exactly.
    with pytest.raises(RuntimeError, match="must pair with the complete winning 'title' value"):
        Page().render()


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

    # Every reserved spelling is refused as Python-supplied browser code
    # before the binding parser could read it.
    with pytest.raises(VueCodeError, match=r"\$c-tr binding"):
        Page().render()


def test_malformed_owned_name_is_rejected_when_i18n_is_unconfigured() -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<button $c-tr:></button>"

    with pytest.raises(ValueError, match="non-empty message ID"):
        Page().render()


def test_values_expression_reads_character_references_as_an_attribute_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # An authored `$c-tr:` value is an attribute value, so `&amp;` in it means
    # `&` in the browser, for a text target and an attribute target alike.
    compiled: list[str] = []
    compile_vue = _rust.vue._compile_vue

    def record(*args: Any) -> str:
        result = compile_vue(*args)
        compiled.append(json.loads(result)["code"])
        return result

    monkeypatch.setattr(_rust.vue, "_compile_vue", record)
    app = _app()

    class Page(Component):
        citry = app
        template = """\
<c-i18n c-client="True" tag="main">
  <span $c-tr:greeting="{ name: 'a &amp; b' }">{{ tr("greeting", name="x") }}</span>
  <span
    $c-tr:greeting[title]="{ name: 'c &amp; d' }"
    c-title="tr('greeting', name='y')"
  >t</span>
</c-i18n>\
"""
        messages = "# @param {str} $name\ngreeting = Hello { $name }"

    Page().render().serialize()
    code = "\n".join(compiled)
    assert "() => ({ name: 'a & b' })" in code
    assert "() => ({ name: 'c & d' })" in code
