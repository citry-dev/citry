from __future__ import annotations

import re
from dataclasses import dataclass

import pytest

from citry import Citry, Component


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
