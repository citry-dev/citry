from __future__ import annotations

import pytest

from citry import Citry, Component
from citry._vue.capture import render_prepared
from citry._vue.direct_capture import assemble_typed_render
from citry.ext.events.bindings import RUNTIME_CONTROL_ATTR
from citry.extension import Extension


def _assembly(component: Component):
    return assemble_typed_render(
        render_prepared(component),
        revision=0,
        tag_for_type=lambda type_key: f"x-{type_key.lower().replace('_', '-')}",
    )


def test_later_attribute_hook_cannot_change_authored_control_to_invalid_input_type() -> None:
    class ChangeType(Extension):
        name = "change_type"

        def on_attrs_resolved(self, ctx):
            if ctx.tag_name == "input":
                return {**ctx.attrs, "type": "file"}
            return None

    registry = Citry(secret="test-secret", autodiscover=False, extensions=[ChangeType])  # noqa: S106

    class Search(Component):
        citry = registry
        template = '<input type="text" :c-query="search" c-bind="attrs">'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"title": "changed later"}}

    with pytest.raises(ValueError, match=r'<input type="file"> cannot be bound to State'):
        _assembly(Search())


def test_authored_static_control_reaches_final_validator_as_normalized_control(monkeypatch) -> None:
    from citry.ext.events import bindings as events_bindings
    from citry.ext.events import extension as events_extension_module

    calls: list[str] = []
    final_calls: list[tuple[str, tuple[dict[str, object], ...]]] = []
    original = events_extension_module.rewrite_resolved_attrs
    original_final = events_bindings._validate_final_control_bindings

    def spy(*args, **kwargs):
        calls.append(args[2])
        return original(*args, **kwargs)

    def final_spy(tag_name, attrs, specs, **kwargs):
        final_calls.append((tag_name, tuple(dict(spec) for spec in specs)))
        return original_final(tag_name, attrs, specs, **kwargs)

    monkeypatch.setattr(events_extension_module, "rewrite_resolved_attrs", spy)
    monkeypatch.setattr(events_bindings, "_validate_final_control_bindings", final_spy)
    registry = Citry(secret="test-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry
        template = '<input type="text" :c-query="search">'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

    assembly = _assembly(Search())
    root = assembly.view.occurrences[0]
    assert next(iter(root.prepared_data["controlBindings"].values()))["field"] == "query"
    # Authored controls reach the final validator directly; the Events spread
    # rewrite hook is not a serialized-carrier consumer for this path.
    assert calls == []
    assert len(final_calls) == 1
    tag_name, [final_spec] = final_calls[0]
    assert tag_name == "input"
    assert final_spec["field"] == "query"
    assert final_spec["binding_mode"] == "two-way"
    assert type(final_spec["id"]) is str
    assert final_spec["id"]


def test_static_c_element_input_uses_its_typed_target_tag_for_control_validation() -> None:
    registry = Citry(secret="test-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry
        template = '<c-element is="input" :c-query="search" />'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

    assembly = _assembly(Search())
    root = assembly.view.occurrences[0]
    [control] = root.prepared_data["controlBindings"].values()
    assert (control["field"], control["handler"], control["binding_mode"]) == (
        "query",
        "search",
        "two-way",
    )


def test_static_c_element_input_rejects_invalid_final_input_type() -> None:
    registry = Citry(secret="test-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry
        template = '<c-element is="input" type="submit" :c-query="search" />'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

    with pytest.raises(ValueError, match=r'<input type="submit"> cannot be bound to State'):
        _assembly(Search())


def test_static_c_element_div_rejects_state_control() -> None:
    registry = Citry(secret="test-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry
        template = '<c-element is="div" :c-query="search" />'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

    with pytest.raises(ValueError, match=r"<div> holds no value"):
        _assembly(Search())


def test_static_c_element_custom_control_requires_explicit_update_event() -> None:
    registry = Citry(secret="test-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry
        template = '<c-element is="native-control" :c-query="search" />'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

    with pytest.raises(ValueError, match=r"custom element.*\.on:<event>"):
        _assembly(Search())


@pytest.mark.parametrize(
    "browser_binding",
    [
        'v-bind:type="kind"',
        '.type="kind"',
        '.type.prop="kind"',
        ':type.prop="kind"',
        'v-bind:type.prop="kind"',
        'v-bind="attrs"',
        'v-bind.prop="attrs"',
        ':[name]="kind"',
        '.[name]="kind"',
        'v-bind:[name]="kind"',
    ],
)
def test_browser_binding_that_can_replace_input_type_defers_static_type_validation(browser_binding: str) -> None:
    registry = Citry(secret="test-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry
        template = f'<input type="file" {browser_binding} :c-query="search">'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

        def js_data(self, kwargs, slots):
            return {"kind": "text", "name": "type", "attrs": {"type": "text"}}

    _assembly(Search())


def test_literal_unsupported_input_type_still_rejects_without_dynamic_type_binding() -> None:
    registry = Citry(secret="test-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry
        template = '<input type="file" :c-query="search">'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

    with pytest.raises(ValueError, match=r'<input type="file"> cannot be bound to State'):
        _assembly(Search())


def test_unrelated_browser_binding_does_not_make_static_input_type_dynamic() -> None:
    registry = Citry(secret="test-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry
        template = '<input type="file" :title="title" :c-query="search">'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

        def js_data(self, kwargs, slots):
            return {"title": "search"}

    with pytest.raises(ValueError, match=r'<input type="file"> cannot be bound to State'):
        _assembly(Search())


def test_runtime_state_spread_is_validated_and_preserved_as_typed_control() -> None:
    registry = Citry(secret="test-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry
        template = '<input c-bind="attrs">'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"type": "text", ":c-query": "search"}}

    assembly = _assembly(Search())
    root = assembly.view.occurrences[0]
    [control] = root.prepared_data["controlBindings"].values()
    assert (control["field"], control["handler"], control["binding_mode"]) == (
        "query",
        "search",
        "two-way",
    )


def test_forged_runtime_control_carrier_is_rejected_after_hooks() -> None:
    class ForgeCarrier(Extension):
        name = "forge_carrier"

        def on_attrs_resolved(self, ctx):
            if RUNTIME_CONTROL_ATTR in ctx.attrs:
                return {**ctx.attrs, RUNTIME_CONTROL_ATTR: "forged"}
            return None

    registry = Citry(secret="test-secret", autodiscover=False, extensions=[ForgeCarrier])  # noqa: S106

    class Plain(Component):
        citry = registry
        template = '<input c-bind="attrs">'

        class State:
            query: str = ""

        class Events:
            def search(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {":c-query": "search"}}

    with pytest.raises(TypeError, match="runtime State control metadata lacks Events producer provenance"):
        _assembly(Plain())


def test_ordinary_static_attrs_keep_fast_path_without_final_control_validation(monkeypatch) -> None:
    from citry.ext.events import bindings

    calls = 0
    original = bindings._validate_final_control_bindings

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(bindings, "_validate_final_control_bindings", counted)
    registry = Citry(autodiscover=False, extensions=[])

    class Plain(Component):
        citry = registry
        template = '<div class="ordinary">plain</div>'

    _assembly(Plain())
    assert calls == 0
