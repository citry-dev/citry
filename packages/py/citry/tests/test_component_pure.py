from __future__ import annotations

import re
from dataclasses import dataclass

import pytest

from citry import Citry, Component
from citry._pure import PurePreparedPart
from citry._vue.capture import (
    PreparedBrowserBinding,
    PreparedElementClose,
    PreparedElementOpen,
    PreparedSourceText,
    PreparedStaticRun,
    PreparedTextValue,
    PreparedVerbatimHtml,
    render_prepared,
)
from citry._vue.direct_capture import assemble_typed_render
from citry.citry_context import CitryContext
from citry.component_render import _capture_pure_part


class _RenderedProbe:
    def __init__(self, value: str) -> None:
        self.value = value
        self.calls = 0

    def __str__(self) -> str:
        self.calls += 1
        return self.value


def test_pure_component_reuses_equal_body_with_fresh_component_ids() -> None:
    app = Citry()

    class PureLeaf(Component):
        citry = app
        pure = True
        template = "<p>{{ value }}</p>"

    class Page(Component):
        citry = app
        template = '<c-PureLeaf c-value="value" /><c-PureLeaf c-value="value" />'

    probe = _RenderedProbe("same")
    html = Page(value=probe).render().serialize()

    assert probe.calls == 1
    markers = re.findall(r'<p data-cid-([^=]+)="" data-cid-([^=]+)="">same</p>', html)
    assert len(markers) == 2
    assert markers[0][0] != markers[1][0]
    assert markers[0][1] == markers[1][1]


def test_prepared_pure_component_reuses_immutable_text_with_fresh_occurrences() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class PureLeaf(Component):
        citry = app
        pure = True
        template = "<section><span>fixed</span>{{ value }}</section>"

    class Page(Component):
        citry = app
        template = '<c-PureLeaf c-value="value" /><c-PureLeaf c-value="value" />'

    probe = _RenderedProbe("same")
    assembly = assemble_typed_render(
        render_prepared(Page(value=probe)),
        revision=0,
        tag_for_type=lambda key: f"x-{key.lower().replace('_', '-')}",
    )

    assert probe.calls == 1
    leaves = [occurrence for occurrence in assembly.view.occurrences if occurrence.parent_id is not None]
    assert len(leaves) == 2
    assert leaves[0].id != leaves[1].id
    assert leaves[0].definition_id == leaves[1].definition_id
    assert all("same" in occurrence.prepared_data.values() for occurrence in leaves)
    definition = assembly.compile_inputs[leaves[0].definition_id]
    assert "<section><span>fixed</span>" in definition.template


def test_pure_capture_whitelists_only_context_free_prepared_parts() -> None:
    context = CitryContext(variables={})
    safe = (
        PreparedSourceText("source", (0, 6), "source"),
        PreparedStaticRun("<p>fixed</p>"),
        PreparedElementClose("</p>", (0, 4), "p"),
        PreparedTextValue("{{ value }}", (0, 11), "value"),
    )
    assert all(isinstance(_capture_pure_part(part, context), PurePreparedPart) for part in safe)

    forged_binding = PreparedBrowserBinding("$binding", "id", "text")
    unsafe = (
        PreparedTextValue("{{ value }}", (0, 11), "value", browser_binding=forged_binding),
        PreparedTextValue("{{ value }}", (0, 11), ("not", "a", "scalar")),
        PreparedElementOpen(
            "<p>",
            (0, 3),
            "p",
            (),
            is_void=False,
            is_self_closing=False,
            element_metadata=None,
        ),
        PreparedVerbatimHtml("<c-raw>x</c-raw>", (0, 20), "<b>x</b>"),
    )
    assert all(_capture_pure_part(part, context) is None for part in unsafe)


def test_pure_simple_component_reuses_safe_typed_text() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class PureLabel(Component):
        citry = app
        pure = True
        simple = True
        template = "<span>{{ value }}</span>"

    class Page(Component):
        citry = app
        template = '<c-PureLabel c-value="value" /><c-PureLabel c-value="value" />'

    probe = _RenderedProbe("same")
    assert Page(value=probe).render().serialize().count("same</span>") == 2
    assert probe.calls == 1


def test_pure_i18n_bindings_remain_live_for_each_occurrence() -> None:
    app = Citry(extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}})

    class PureLabel(Component):
        citry = app
        pure = True
        template = "<span $c-tr:save>{{ tr('save') }}</span>"
        messages = "save = Save"

    class Page(Component):
        citry = app
        template = '<c-i18n c-client="True" tag="main"><c-PureLabel /><c-PureLabel /></c-i18n>'

    html = Page().render().serialize()
    binding_ids = re.findall(r'"id":"([^"]+~i18n-[^"]+)"', html)
    assert len(binding_ids) == 2
    assert len(set(binding_ids)) == 2


def test_pure_component_memo_is_scoped_to_one_root_render() -> None:
    app = Citry()

    class PureLeaf(Component):
        citry = app
        pure = True
        template = "{{ value }}"

    class Page(Component):
        citry = app
        template = '<c-PureLeaf c-value="value" /><c-PureLeaf c-value="value" />'

    probe = _RenderedProbe("same")
    Page(value=probe).render()
    Page(value=probe).render()
    assert probe.calls == 2


def test_pure_component_replays_transparent_control_flow_structure() -> None:
    app = Citry()

    class PureLeaf(Component):
        citry = app
        pure = True
        template = "<c-if cond>{{ value }}</c-if>"

    class Page(Component):
        citry = app
        template = '<c-PureLeaf c-value="value" /><c-PureLeaf c-value="value" />'

    probe = _RenderedProbe("same")
    html = Page(value=probe).render().serialize()

    assert probe.calls == 1
    assert html.count("same") == 2


def test_pure_component_keys_equal_dataclass_values_by_value() -> None:
    app = Citry(template_globals={})
    string_calls = 0

    @dataclass(frozen=True)
    class Value:
        text: str

        def __str__(self) -> str:
            nonlocal string_calls
            string_calls += 1
            return self.text

    class PureLeaf(Component):
        citry = app
        pure = True
        template = "{{ value }}"

    class Page(Component):
        citry = app
        template = '<c-PureLeaf c-value="make_value()" /><c-PureLeaf c-value="make_value()" />'

    app.template_globals["make_value"] = lambda: Value("same")
    assert Page().render().serialize().count("same") == 2
    assert string_calls == 1


def test_ordinary_component_does_not_memoize_its_body() -> None:
    app = Citry()

    class OrdinaryLeaf(Component):
        citry = app
        template = "{{ value }}"

    class Page(Component):
        citry = app
        template = '<c-OrdinaryLeaf c-value="value" /><c-OrdinaryLeaf c-value="value" />'

    probe = _RenderedProbe("same")
    Page(value=probe).render()
    assert probe.calls == 2


def test_pure_body_with_child_component_is_not_memoized() -> None:
    app = Citry()

    class Child(Component):
        citry = app
        template = "{{ value }}"

    class PureParent(Component):
        citry = app
        pure = True
        template = '<c-Child c-value="value" />'

    class Page(Component):
        citry = app
        template = '<c-PureParent c-value="value" /><c-PureParent c-value="value" />'

    probe = _RenderedProbe("same")
    Page(value=probe).render()
    assert probe.calls == 2


def test_pure_body_caches_safe_work_around_a_live_child_hole() -> None:
    app = Citry()

    class Child(Component):
        citry = app
        template = "{{ child_value }}"

    class PureParent(Component):
        citry = app
        pure = True
        template = '{{ stable_value }}<c-Child c-child_value="child_value" />'

    class Page(Component):
        citry = app
        template = (
            '<c-PureParent c-stable_value="stable" c-child_value="child" />'
            '<c-PureParent c-stable_value="stable" c-child_value="child" />'
        )

    stable = _RenderedProbe("stable")
    child = _RenderedProbe("child")
    html = Page(stable=stable, child=child).render().serialize()

    assert html.count("stablechild") == 2
    assert stable.calls == 1
    assert child.calls == 2


def test_pure_body_caches_safe_work_around_a_live_slot_hole() -> None:
    app = Citry()

    class PureFrame(Component):
        citry = app
        pure = True
        template = "{{ stable_value }}:<c-slot />"

    class Page(Component):
        citry = app
        template = (
            '<c-PureFrame c-stable_value="stable">{{ content }}</c-PureFrame>'
            '<c-PureFrame c-stable_value="stable">{{ content }}</c-PureFrame>'
        )

    stable = _RenderedProbe("stable")
    content = _RenderedProbe("content")
    html = Page(stable=stable, content=content).render().serialize()

    assert html.count("stable:content") == 2
    assert stable.calls == 1
    assert content.calls == 2


def test_purity_requires_an_exact_bool_and_does_not_inherit() -> None:
    app = Citry()

    with pytest.raises(ValueError, match="pure must be an exact bool"):

        class Invalid(Component):
            citry = app
            pure = 1  # type: ignore[assignment]

    class PureBase(Component):
        citry = app
        pure = True

    class Child(PureBase):
        pass

    assert PureBase.pure is True
    assert Child.pure is False
    with pytest.raises(AttributeError, match="pure-component declaration"):
        PureBase.pure = False
