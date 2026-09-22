from __future__ import annotations

import pytest

from citry import Citry, Component
from citry._vue.capture import render_prepared
from citry._vue.direct_capture import UnsupportedPreparedView, assemble_typed_render
from citry.ext.cache.artifact import _prepared_call_from_wire, _prepared_call_to_wire


def _assemble(component: Component):
    return assemble_typed_render(
        render_prepared(component),
        revision=0,
        tag_for_type=lambda value: f"x-{value.lower().replace('_', '-')}",
    )


def test_empty_string_component_key_is_a_valid_explicit_identity() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class Child(Component):
        citry = app
        template = "<span>child</span>"

    class Page(Component):
        citry = app
        template = "<c-Child #c-key=\"''\" />"

    assembly = _assemble(Page())
    assert len(assembly.view.occurrences) == 2


def test_empty_string_component_key_roundtrips_through_cache_call_metadata() -> None:
    value = _prepared_call_from_wire(["x", [0, 1], "", None, True, False, []], "call")
    assert value.explicit_key == ""
    assert _prepared_call_to_wire(value)[2] == ""


def test_object_event_binding_roundtrips_through_cache_call_metadata() -> None:
    value = _prepared_call_from_wire(
        [
            'v-on="listeners"',
            [0, 16],
            None,
            None,
            True,
            False,
            [["events-object", "v-on", "listeners", 'v-on="listeners"', [0, 16], "authored"]],
        ],
        "call",
    )
    assert value.bindings[0].kind == "events-object"
    assert _prepared_call_to_wire(value)[6][0][0] == "events-object"


def test_empty_string_key_reaches_group_duplicate_detection() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class Child(Component):
        citry = app
        template = "<span>child</span>"

    class Page(Component):
        citry = app
        template = '<c-for each="item in items"><c-Child #c-key="\'\'" /></c-for>'

        def template_data(self, kwargs, slots):
            return {"items": [1, 2]}

    with pytest.raises(UnsupportedPreparedView, match="duplicate explicit #c-key"):
        _assemble(Page())


def test_component_range_ignore_is_explicitly_unsupported_in_prepared_vue() -> None:
    app = Citry(autodiscover=False, extensions=[])

    class Child(Component):
        citry = app
        template = "<span>child</span>"

    class Page(Component):
        citry = app
        template = "<c-Child #c-ignore />"

    with pytest.raises(TypeError, match="component #c-ignore is unsupported in prepared Vue"):
        render_prepared(Page())
