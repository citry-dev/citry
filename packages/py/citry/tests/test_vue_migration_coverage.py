"""
Focused contracts for the native Vue capture boundary.

These tests exercise the validation branches that are easy to miss when the
usual component fixtures only take the happy path.  They are deliberately
small: each one describes a value that crosses the Python-to-Vue boundary and
the rejection rule that keeps that value safe and deterministic.
"""

from __future__ import annotations

import gc
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from citry import Citry, Component, Const, Extension
from citry._pure import PureInteriorBody
from citry._serialization_security import _ScriptSecurityMaterializer
from citry._simple_runtime import SimpleRender
from citry._vue import events as vue_events
from citry._vue.capture import (
    PreparedAttribute,
    PreparedConstantNode,
    PreparedConstPrecomputeAdapter,
    PreparedDynamicElementOpen,
    PreparedElementClose,
    PreparedElementCloseNode,
    PreparedElementOpen,
    PreparedElementOpenNode,
    PreparedExprNode,
    PreparedSourceText,
    PreparedSourceTextNode,
    PreparedStaticRunNode,
    PreparedTrustedHtmlValue,
    StaticRunOpening,
    StaticRunStructure,
    _normalize_control_bindings,
    _normalize_event_bindings,
    _normalize_poll_bindings,
    _normalize_runtime_poll_bindings,
    _validate_prepared_render,
    coalesce_prepared_static_nodes,
    is_authenticated_browser_binding,
    is_authenticated_dynamic_element_open,
    prepared_browser_binding,
    prepared_dynamic_element_open,
    render_prepared_direct,
    render_prepared_marker_replacement,
    typed_render_scope,
)
from citry._vue.direct import (
    DirectCallRunRender,
    DirectFillSource,
    DirectNestedTemplateRender,
    DirectProjectionRender,
    DirectPythonComponentRender,
    DirectRenderSession,
    DirectSlotRender,
    UnboundNestedTemplateRender,
    active_execution,
    begin_slot_execution,
    bind_nested_template,
    bind_template_fill,
    capture_slot_call,
    direct_execution_scope,
    direct_fill_source,
    direct_receiver_scope,
    direct_render_scope,
    wrap_nested_template,
    wrap_python_composition_result,
    wrap_slot_result,
)
from citry._vue.direct_capture import (
    UnsupportedPreparedView,
    _checked_component_tag,
    _event_directive_attrs,
    _issue_cache_replay_identity,
    _json_plain,
    _logical_typed_body,
    _matches_cache_replay_identity,
    _prepared_root_markers,
    _register_dynamic_binding_data,
    _run_eligible_component,
    _stable_owner,
)
from citry._vue.document import typed_document_shell
from citry._vue.events import _validate_script_assets, _validate_style_assets, default_events_producer
from citry._vue.leaf_program import (
    _Open,
    _prepared_open,
    _spread_attrs_renderer,
    _spread_data_attrs,
    _spread_passthrough_is_live,
    _validate_data_attrs,
    _validate_open,
)
from citry._vue.prepared import (
    ComponentCall,
    ElementClose,
    ElementOpen,
    FillClosure,
    ForwardedSlot,
    Html,
    LocalComponentCall,
    PreparedDefinition,
    PreparedFill,
    PreparedMarker,
    PreparedOccurrence,
    PreparedSlotOutlet,
    PreparedView,
    RuntimeDirective,
    SlotOutlet,
    TextBinding,
    replace_definition_ids,
)
from citry._vue.serialization import (
    VueSerializationAnalysis,
    VueSerializationPlan,
    _HostValidator,
    _reject_head_browser_activity,
    _selected_renders,
    _vue_shell,
    analyze_vue_serialization,
    prepare_vue_serialization,
)
from citry.citry_context import CitryContext
from citry.citry_render import (
    CitryRender,
    DeferredComponent,
    Placeholder,
    PreparedOccurrenceMetadata,
    RenderDecoration,
    RenderFrame,
)
from citry.component_render import (
    _attach_template_position,
    _capture_pure_part,
    _component_path,
    _contains_deferred,
    _contains_render,
    _finalize,
    _get_compiled_template,
    _merge_dependencies,
    _render_and_capture_pure_body,
    _render_body,
    _render_ids,
    _render_ids_from_parts,
    _render_objects,
    _render_objects_from_parts,
    _render_one,
    _render_pure_live_item,
    _render_selection,
    _replace_in_parts,
    _replacement_parts,
    _replay_pure_body,
    _scan_deferred,
    _settle_render,
    _validate_client_props_target,
)
from citry.ext.dependencies.emission import VUE_RUNTIME_EMITTED_KEY
from citry.ext.dependencies.types import DependencyRecord, Script
from citry.ext.i18n.bindings import CapturedTranslationText
from citry.extension import OnSerializeContext
from citry.nodes import StaticHtmlAttr
from citry.slots import Slot


def _event(event_id: str = "citryEventabc", **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": event_id,
        "event": "click",
        "handler": "save",
        "args": None,
        "prevent": False,
        "stop": False,
        "self": False,
        "once": False,
        "key": None,
        "debounce": None,
        "throttle": None,
    }
    value.update(overrides)
    return value


def _poll(binding_id: str = "citryPollabc", **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {"id": binding_id, "handler": "poll", "args": None, "interval": 1000}
    value.update(overrides)
    return value


def _control(binding_id: str = "citryControlabc", **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": binding_id,
        "field": "value",
        "binding_mode": "one-way",
        "handler": None,
        "lazy": False,
        "on": None,
        "key": None,
        "debounce": None,
        "throttle": None,
    }
    value.update(overrides)
    return value


def test_browser_and_dynamic_bindings_require_authenticated_shapes() -> None:
    binding = prepared_browser_binding(helper="$probe", operand="value", target="text")
    assert is_authenticated_browser_binding(binding)
    assert not is_authenticated_browser_binding(replace(binding))

    for kwargs, message in (
        ({"helper": "probe", "operand": "x", "target": "text"}, "helper"),
        ({"helper": "$probe", "operand": "x", "target": "style"}, "target"),
        ({"helper": "$probe", "operand": "x", "target": "text", "name": "title"}, "disagree"),
        ({"helper": "$probe", "operand": "x", "target": "attribute", "name": None}, "disagree"),
        ({"helper": "$probe", "operand": "x", "target": "text", "values_expression": ""}, "non-empty"),
        ({"helper": "$probe", "operand": "x", "target": "text", "values_expression": 1}, "non-empty"),
    ):
        with pytest.raises(ValueError, match=message):
            prepared_browser_binding(**kwargs)

    opening = prepared_dynamic_element_open("input", {"value": "x"})
    assert is_authenticated_dynamic_element_open(opening)

    def forged(**changes: object) -> PreparedDynamicElementOpen:
        value = replace(opening, **changes)
        object.__setattr__(value, "_producer_token", object())
        return value

    assert not is_authenticated_dynamic_element_open(
        forged(authored_attrs=(PreparedAttribute("title", "data", (0, 1), "x"),))
    )
    assert not is_authenticated_dynamic_element_open(forged(key=1))
    assert not is_authenticated_dynamic_element_open(forged(tag="not a tag"))
    assert not is_authenticated_dynamic_element_open(forged(is_void=False))


def test_dynamic_element_provenance_checks_source_bytes_and_runtime_candidates() -> None:
    opening = prepared_dynamic_element_open("button", {}, key="key")

    def forged(**changes: object) -> PreparedDynamicElementOpen:
        value = replace(opening, **changes)
        object.__setattr__(value, "_producer_token", object())
        object.__setattr__(value, "_producer_token", opening._producer_token)
        return value

    authored = replace(
        opening,
        authored_attrs=(PreparedAttribute("@click", "source", (0, 6), "@click"),),
        authored_source="@click",
    )
    object.__setattr__(authored, "_producer_token", opening._producer_token)
    assert is_authenticated_dynamic_element_open(authored)
    for attrs, source in (
        ((PreparedAttribute("title", "data", (0, 6), "title"),), "title"),
        ((PreparedAttribute("@click", "source", (0, 6), "wrong"),), "@click"),
        ((PreparedAttribute("@click", "source", (1, 2), "é"),), "é"),
    ):
        value = replace(opening, authored_attrs=attrs, authored_source=source)
        object.__setattr__(value, "_producer_token", opening._producer_token)
        assert not is_authenticated_dynamic_element_open(value)
    runtime = forged()
    object.__setattr__(runtime, "runtime_event_bindings", (_event("citryRuntimeEventabc"),))
    assert not is_authenticated_dynamic_element_open(runtime)
    invalid_tag = forged(tag="not a valid tag")
    assert not is_authenticated_dynamic_element_open(invalid_tag)


def test_prepared_const_and_expression_adapters_keep_fallbacks_live() -> None:
    context = CitryContext({"value": "hello"})
    adapter = PreparedConstPrecomputeAdapter()
    expression = PreparedExprNode("{{ value }}", (0, 10), "value", ("value",))
    constant = adapter.expression(expression, context)
    assert isinstance(constant, PreparedConstantNode)
    assert adapter.expression(object(), context) is not None
    missing = PreparedExprNode("{{ missing }}", (0, 12), "missing", ("missing",))
    assert adapter.expression(missing, context) is missing

    static = PreparedElementOpenNode(
        source="<p>",
        start_span=(0, 3),
        tag="p",
        attrs=(),
        used_vars=(),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
    )
    specialized = adapter.element_attrs(static, context)
    assert isinstance(specialized, PreparedConstantNode)
    assert adapter.element_attrs(object(), context) is not None
    assert adapter.static_parts(PreparedSourceTextNode("x", (0, 1), "x"))
    assert adapter.static_parts(PreparedElementCloseNode("</p>", (0, 4), "p"))
    assert adapter.static_parts(PreparedConstantNode(PreparedTrustedHtmlValue("<b>x</b>")))
    assert adapter.static_parts(object()) is None

    sink = SimpleNamespace(component_name="Card")
    with pytest.raises(RuntimeError, match="Text cannot"):
        PreparedSourceTextNode("x", (0, 1), "text").collect_fills(context, sink)
    PreparedSourceTextNode("x", (0, 1), " \n").collect_fills(context, sink)


def test_marker_replacement_and_const_adapter_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    selected = render_prepared_direct(Page())
    with typed_render_scope(direct=True, vue=False), pytest.raises(RuntimeError, match="another prepared"):
        render_prepared_marker_replacement(selected, citry=app, name="ready")
    ordinary = CitryRender(parts=[], context=selected.context, render_target="html")
    with pytest.raises(TypeError, match="typed prepared"):
        render_prepared_marker_replacement(ordinary, citry=app, name="ready")
    fake_citry = SimpleNamespace(get=lambda _name: object(), _is_builtin_component=lambda _component: False)
    with pytest.raises(ValueError, match="engine-owned"):
        render_prepared_marker_replacement(selected, citry=fake_citry, name="ready")

    adapter = PreparedConstPrecomputeAdapter()

    class BrokenOpen(PreparedElementOpenNode):
        def render(self, _context: CitryContext) -> PreparedElementOpen:
            raise RuntimeError("cannot precompute")

    broken = BrokenOpen(
        source="<p>",
        start_span=(0, 3),
        tag="p",
        attrs=(),
        used_vars=(),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
    )
    assert adapter.element_attrs(broken, CitryContext()) is broken
    marker = adapter.element_metadata(object(), frozenset(), CitryContext())
    assert marker is not None
    assert adapter.element_key(object(), CitryContext()) is not None

    from citry._vue import capture

    expr = PreparedExprNode("{{ value }}", (0, 10), "value", ("value",))
    monkeypatch.setattr(
        capture,
        "_render_value",
        lambda *_args, **_kwargs: capture.PreparedTextValue("source", (0, 1), "fallback"),
    )
    assert isinstance(expr.resolve_evaluated_value(object(), CitryContext()), capture.PreparedTextValue)
    monkeypatch.setattr(capture, "_render_value", lambda *_args, **_kwargs: object())
    with pytest.raises(TypeError, match="fallback"):
        expr.resolve_evaluated_value(object(), CitryContext())


def test_prepared_capture_rejects_runtime_binding_collisions_and_validation_cycles() -> None:
    from citry.ext.events.bindings import (
        _RUNTIME_CONTROL_TOKEN,
        _RUNTIME_EVENTS_TOKEN,
        RUNTIME_CONTROL_ATTR,
        RUNTIME_EVENTS_ATTR,
        _RuntimeControlBindings,
        _RuntimeEventBindings,
    )

    event = _event()
    node = PreparedElementOpenNode(
        source="<button>",
        start_span=(0, 8),
        tag="button",
        attrs=(),
        used_vars=(),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
        event_bindings=(event,),
    )
    runtime_event = _RuntimeEventBindings(
        ({key: value for key, value in event.items() if key != "id"},), (), _RUNTIME_EVENTS_TOKEN
    )
    with pytest.raises(ValueError, match="one element supports one"):
        node._prepared_from_resolved(
            {RUNTIME_EVENTS_ATTR: runtime_event}, context=CitryContext(), extension_validated=True
        )
    duplicate_events = _RuntimeEventBindings(
        (
            {key: value for key, value in event.items() if key != "id"},
            {key: value for key, value in _event(handler="other").items() if key != "id"},
        ),
        (),
        _RUNTIME_EVENTS_TOKEN,
    )
    with pytest.raises(ValueError, match="one element supports one"):
        node._prepared_from_resolved(
            {RUNTIME_EVENTS_ATTR: duplicate_events}, context=CitryContext(), extension_validated=True
        )
    runtime_control = _RuntimeControlBindings(
        ({key: value for key, value in _control().items() if key != "id"},), _RUNTIME_CONTROL_TOKEN
    )
    with pytest.raises(ValueError, match="exactly one runtime State"):
        node._prepared_from_resolved(
            {
                RUNTIME_CONTROL_ATTR: _RuntimeControlBindings(
                    (
                        {key: value for key, value in _control().items() if key != "id"},
                        {key: value for key, value in _control(field="checked").items() if key != "id"},
                    ),
                    _RUNTIME_CONTROL_TOKEN,
                )
            },
            context=CitryContext(),
            extension_validated=True,
        )
    control_node = PreparedElementOpenNode(
        source="<input>",
        start_span=(0, 7),
        tag="input",
        attrs=(),
        used_vars=(),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
        control_bindings=(_control(),),
    )
    with pytest.raises(ValueError, match="one :c"):
        control_node._prepared_from_resolved(
            {RUNTIME_CONTROL_ATTR: runtime_control}, context=CitryContext(), extension_validated=True
        )
    with pytest.raises(TypeError, match="reserved internal"):
        node._prepared_from_resolved(
            {"DATA-CITRY-RUNTIME-EVENTS": "x"}, context=CitryContext(), extension_validated=True
        )
    with pytest.raises(RuntimeError, match="compiler-owned"):
        node._prepared_from_resolved({"data-cev-test": "x"}, context=CitryContext(), extension_validated=True)
    assert node.tag == "button"

    with pytest.raises(TypeError, match="unresolved runtime"):
        _validate_prepared_render(
            CitryRender(parts=[Placeholder("runtime")], context=CitryContext(), render_target="prepared")
        )
    repeated = CitryRender(parts=[], context=CitryContext(), render_target="prepared")
    repeated.parts.append(repeated)
    _validate_prepared_render(repeated)


def test_capture_binding_normalizers_reject_malformed_records() -> None:
    assert len(_normalize_event_bindings((_event(),))) == 1
    assert len(_normalize_poll_bindings((_poll(),))) == 1
    assert len(_normalize_runtime_poll_bindings((_poll("citryRuntimePollabc"),))) == 1
    assert len(_normalize_control_bindings((_control(),))) == 1

    event_cases = (
        ({}, "exact trusted"),
        ({"id": "wrong", **{key: value for key, value in _event().items() if key != "id"}}, "identity"),
        (_event(event=""), "identity"),
        (_event(handler=""), "identity"),
        (_event(args=1), "args"),
        (_event(prevent=1), "boolean"),
        (_event(key=1), "key"),
        (_event(debounce=-1), "integer"),
        (_event(), "duplicated"),
    )
    for value, message in event_cases:
        bindings = (value, value) if message == "duplicated" else (value,)
        with pytest.raises((TypeError, ValueError), match=message):
            _normalize_event_bindings(bindings)

    poll_cases = (
        ({}, "exact trusted"),
        (_poll("wrong"), "identity"),
        (_poll(handler=""), "handler"),
        (_poll(args=1), "args"),
        (_poll(interval=0), "interval"),
        (_poll(), "duplicated"),
    )
    for value, message in poll_cases:
        bindings = (value, value) if message == "duplicated" else (value,)
        with pytest.raises((TypeError, ValueError), match=message):
            _normalize_poll_bindings(bindings)

    runtime_poll_cases = (
        ({}, "exact trusted"),
        (_poll("wrong"), "identity"),
        (_poll("citryRuntimePollabc", handler=""), "handler"),
        (_poll("citryRuntimePollabc", args="x"), "must be null"),
        (_poll("citryRuntimePollabc", interval=0), "interval"),
        (_poll("citryRuntimePollabc"), "duplicated"),
    )
    for value, message in runtime_poll_cases:
        bindings = (value, value) if message == "duplicated" else (value,)
        with pytest.raises((TypeError, ValueError), match=message):
            _normalize_runtime_poll_bindings(bindings)

    control_cases = (
        ({}, "exact trusted"),
        (_control("wrong"), "identity"),
        (_control(field=""), "field"),
        (_control(binding_mode="two-way", handler=None), "disagrees"),
        (_control(handler=1), "handler"),
        (_control(lazy=1), "boolean"),
        (_control(on=""), "non-empty"),
        (_control(debounce=-1), "integer"),
        (_control(), "duplicated"),
    )
    for value, message in control_cases:
        bindings = (value, value) if message == "duplicated" else (value,)
        with pytest.raises((TypeError, ValueError), match=message):
            _normalize_control_bindings(bindings)


def test_dynamic_open_and_prepared_render_reject_reserved_or_unresolved_parts() -> None:
    event = _event()
    with pytest.raises(ValueError, match="candidate site"):
        PreparedDynamicElementOpen("button", {}, is_void=False, runtime_event_bindings=(event,))

    static = object.__new__(StaticHtmlAttr)
    static.source = "<p data-citry-runtime-events='x'>"
    static.position = (3, 4)
    static.key = "data-citry-runtime-events"
    static.value = "x"
    with pytest.raises(ValueError, match="reserved"):
        PreparedElementOpenNode(
            source="<p data-citry-runtime-events='x'>",
            start_span=(0, 31),
            tag="p",
            attrs=(static,),
            used_vars=(),
            is_void=False,
            is_self_closing=False,
            element_metadata=(),
        )
    with pytest.raises(ValueError, match="timing"):
        PreparedElementOpenNode(
            source='<p v-citry-event-timing="x">',
            start_span=(0, 30),
            tag="p",
            attrs=(StaticHtmlAttr("<p v-citry-event-timing='x'>", (3, 4), "v-citry-event-timing", "x", ()),),
            used_vars=(),
            is_void=False,
            is_self_closing=False,
            element_metadata=(),
        )

    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>value</p>"

    rendered = render_prepared_direct(Page())
    rendered.parts.append(Placeholder("unresolved"))
    with pytest.raises(TypeError, match="unresolved runtime"):
        _validate_prepared_render(rendered)

    ordinary = CitryRender(parts=["ordinary"], context=rendered.context, render_target="html")
    with pytest.raises(TypeError, match="ordinary HTML"):
        _validate_prepared_render(ordinary)

    rendered.parts[:] = [""]
    _validate_prepared_render(rendered)


def test_static_capture_coalesces_structured_runs_and_preserves_document_boundaries() -> None:
    source = PreparedSourceTextNode("x", (0, 1), "x")
    structure = StaticRunStructure(
        (StaticRunOpening(0, 0, 3, 0, frozenset()),),
        1,
        (("open", "p"),),
    )
    run = PreparedStaticRunNode("<p>", structure)
    detached = PreparedStaticRunNode("raw")
    result = coalesce_prepared_static_nodes([source, run, detached])
    assert len(result) == 2
    assert isinstance(result[0], PreparedStaticRunNode)
    assert result[0]._prepared.root_structure is not None
    assert isinstance(result[1], PreparedStaticRunNode)

    close = PreparedElementCloseNode("</p>", (0, 0), "p")
    opening = PreparedElementOpenNode(
        source="<p/>",
        start_span=(0, 4),
        tag="p",
        attrs=(),
        used_vars=(),
        is_void=False,
        is_self_closing=True,
        element_metadata=(),
    )
    coalesced = coalesce_prepared_static_nodes([opening, close])
    assert len(coalesced) == 1
    assert isinstance(coalesced[0], PreparedStaticRunNode)
    doctype = PreparedSourceTextNode("<!doctype html>", (0, 15), "<!doctype html>")
    assert coalesce_prepared_static_nodes([doctype])[0] is doctype


def test_direct_capture_json_and_document_helpers_validate_boundaries() -> None:
    assert _json_plain(Const({"x": (1, True)})) == {"x": [1, True]}
    assert _json_plain(CapturedTranslationText("translated")) == "translated"
    assert _json_plain(1.5) == 1.5
    for value, message in ((float("nan"), "finite"), ({1: "x"}, "keys"), (object(), "strict JSON")):
        with pytest.raises((TypeError, ValueError), match=message):
            _json_plain(value)
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(ValueError, match="cycle"):
        _json_plain(cyclic)

    source = [
        PreparedSourceText("shell", (0, 5), "<!doctype html>"),
        PreparedElementOpen(
            "<body>",
            (0, 6),
            "body",
            (),
            is_void=False,
            is_self_closing=False,
            element_metadata=(),
        ),
        PreparedSourceText("body", (0, 4), "content"),
        PreparedElementClose("</body>", (0, 7), "body"),
    ]
    assert [part.text for part in _logical_typed_body(source) if isinstance(part, PreparedSourceText)] == ["content"]
    with pytest.raises(UnsupportedPreparedView, match="one authored body"):
        _logical_typed_body([PreparedSourceText("<!doctype html>", (0, 15), "<!doctype html>")])
    with pytest.raises(UnsupportedPreparedView, match="unclosed"):
        _logical_typed_body(source[:-1])

    assert _checked_component_tag("Root", lambda _: "citry-root") == "citry-root"
    with pytest.raises(UnsupportedPreparedView, match="exact string"):
        _checked_component_tag("Root", lambda _: 1)  # type: ignore[return-value]
    with pytest.raises(UnsupportedPreparedView, match="safe custom"):
        _checked_component_tag("Root", lambda _: "Root")
    assert _prepared_root_markers(("data-ready", 'data-label="A &amp; B"', "data-ready")) == (
        ("data-ready", True),
        ("data-label", "A & B"),
    )
    for marker in ("role=button", "onclick=bad", "data-x=bad", "data-on="):
        with pytest.raises(UnsupportedPreparedView):
            _prepared_root_markers((marker,))

    app = Citry(autodiscover=False)

    class Replay(Component):
        citry = app
        template = "<p>replay</p>"

    detached = CitryContext()
    assert not _matches_cache_replay_identity(detached, app, Replay)
    _issue_cache_replay_identity(detached, app, Replay)
    assert _matches_cache_replay_identity(detached, app, Replay)
    assert not _matches_cache_replay_identity(detached, Citry(autodiscover=False), Replay)
    detached.component = Replay()
    assert not _matches_cache_replay_identity(detached, app, Replay)
    assert _stable_owner(None, {}) is None
    with pytest.raises(UnsupportedPreparedView, match="unprepared"):
        _stable_owner("missing", {})

    nested_body = [
        PreparedSourceText("", (0, 0), "<!doctype html>"),
        PreparedElementOpen("", (0, 0), "body", (), is_void=False, is_self_closing=False, element_metadata=()),
        PreparedElementOpen("", (0, 0), "body", (), is_void=False, is_self_closing=False, element_metadata=()),
        PreparedSourceText("", (0, 0), "nested"),
        PreparedElementClose("", (0, 0), "body"),
        PreparedElementClose("", (0, 0), "body"),
    ]
    assert (
        next(part.text for part in _logical_typed_body(nested_body) if isinstance(part, PreparedSourceText))
        == "nested"
    )


def test_event_directive_and_dynamic_binding_metadata_are_deterministic() -> None:
    event = _event(prevent=True, stop=True, self=True, once=True, key="enter", args="value")
    poll = _poll()
    control = _control("citryControlabc", binding_mode="two-way", handler="update")
    part = PreparedElementOpen(
        "<button>",
        (0, 8),
        "button",
        (),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
        event_bindings=(event,),
        poll_bindings=(poll,),
        control_bindings=(control,),
    )
    attrs = _event_directive_attrs(part)
    assert "v-on:click.prevent.stop.self.once.enter" in attrs[0]
    assert "v-citry-event-timing" in attrs[1]
    assert "v-citry-control" in attrs[2]

    dynamic = PreparedDynamicElementOpen(
        "button",
        {},
        is_void=False,
        event_bindings=(event,),
        poll_bindings=(poll,),
        runtime_events_candidate=True,
    )
    values: dict[str, object] = {}
    _register_dynamic_binding_data(values, dynamic)
    assert set(values) == {"eventBindings", "pollBindings"}
    values["eventBindings"][event["id"]] = {"different": True}  # type: ignore[index]
    with pytest.raises(UnsupportedPreparedView, match="conflicting"):
        _register_dynamic_binding_data(values, dynamic)
    with pytest.raises(UnsupportedPreparedView, match="one Events binding"):
        _event_directive_attrs(replace(part, event_bindings=(event, event)))
    with pytest.raises(AssertionError, match="container"):
        _register_dynamic_binding_data({"eventBindings": []}, dynamic)


def test_render_frame_captures_component_binding_provenance_and_rejects_forged_values() -> None:
    app = Citry(autodiscover=False)

    class Child(Component):
        citry = app
        template = "child"

    class Parent(Component):
        citry = app
        template = '<c-Child :disabled="disabled" />'

    rendered = render_prepared_direct(Parent(disabled=True))
    child_render = next(part for part in rendered.parts if isinstance(part, CitryRender))
    frame = child_render.frame
    assert frame.prepared_occurrence is not None
    assert frame.prepared_occurrence.component_tag_client_bindings
    assert frame.prepared_occurrence.component_tag_client_bindings[0].key == ":disabled"

    component = child_render.context.component
    assert component is not None
    from citry.client_directives import ComponentTagClientBinding, ComponentTagClientBindingKind

    component._component_tag_client_bindings = (
        ComponentTagClientBinding(ComponentTagClientBindingKind.PROP, ":x", "value", 1, (0, 1)),
    )
    with pytest.raises(TypeError, match="source"):
        RenderFrame.from_context(child_render.context, is_component_root=True)


def test_direct_session_and_prepared_view_validation_reject_closed_or_inconsistent_state() -> None:
    session = DirectRenderSession()
    assert session.next_composition() == 0
    assert session.next_execution() == 1
    session.active = False
    with pytest.raises(RuntimeError, match="closed"):
        session.next_composition()
    with pytest.raises(RuntimeError, match="closed"):
        session.next_execution()

    definition = PreparedDefinition("root-def", "Root", (TextBinding("citryText0"),))
    occurrence = PreparedOccurrence("root", "Root", "root-def", {}, {}, None, None)
    with pytest.raises(ValueError, match="revision"):
        PreparedView(-1, "root", (occurrence,), (definition,))
    with pytest.raises(ValueError, match="marker"):
        PreparedView(0, "root", (occurrence,), (definition,), (PreparedMarker("root", "bad.name", "root"),))
    with pytest.raises(ValueError, match="missing"):
        PreparedView(0, "root", (occurrence,), (PreparedDefinition("other", "Root", ()),))


def test_direct_projection_validates_session_and_source_contract() -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    selected = render_prepared_direct(Page())
    fill = DirectFillSource(
        DirectRenderSession(), "render", "fill", "default", "<p>", (0, 3), None, strict_session=True
    )
    with pytest.raises((TypeError, ValueError)):
        DirectProjectionRender(
            object(),
            execution_index=1,
            fill_source=fill,
            parent_execution=None,
            public_name="default",
            receiver_render_id="receiver",
            source="<p>",
            span=(0, 3),
        )
    with pytest.raises(ValueError, match="positive"):
        DirectProjectionRender(
            selected,
            execution_index=0,
            fill_source=fill,
            parent_execution=None,
            public_name="default",
            receiver_render_id="receiver",
            source="<p>",
            span=(0, 3),
        )
    invalid_values = (
        {"public_name": ""},
        {"receiver_render_id": ""},
        {"source": 1},
        {"span": (4, 3)},
    )
    for changes in invalid_values:
        kwargs: dict[str, object] = {
            "execution_index": 1,
            "fill_source": fill,
            "parent_execution": None,
            "public_name": "default",
            "receiver_render_id": "receiver",
            "source": "<p>",
            "span": (0, 3),
        }
        kwargs.update(changes)
        with pytest.raises(ValueError, match=r"public|identity|source span"):
            DirectProjectionRender(selected, **kwargs)  # type: ignore[arg-type]

    assert (
        wrap_nested_template(
            selected,
            lexical_render_id="x",
            public_name="x",
            source="x",
            span=(0, 1),
            origin=None,
        )
        is selected
    )
    assert capture_slot_call(__import__("citry.slots", fromlist=["Slot"]).Slot("x"), lambda: "plain") == "plain"

    with direct_render_scope():
        slot = __import__("citry.slots", fromlist=["Slot"]).Slot("x")
        bind_template_fill(
            slot,
            lexical_render_id="render",
            kind="fill",
            public_name="default",
            source="x",
            span=(0, 1),
            origin=None,
        )
        bound_fill = direct_fill_source(slot)
        assert bound_fill is not None
        with pytest.raises(TypeError, match="structured"):
            wrap_slot_result(
                "plain",
                fill_source=bound_fill,
                public_name="default",
                receiver_render_id="receiver",
                source="x",
                span=(0, 1),
                execution=begin_slot_execution(
                    bound_fill,
                    public_name="default",
                    receiver_render_id="receiver",
                    source="x",
                    span=(0, 1),
                ),
            )
        with pytest.raises(TypeError, match="receiving component"):
            capture_slot_call(slot, lambda: selected)
        with pytest.raises(TypeError, match="receiving component"):
            bind_nested_template(
                wrap_nested_template(
                    selected,
                    lexical_render_id="x",
                    public_name="x",
                    source="x",
                    span=(0, 1),
                    origin=None,
                ),
                CitryContext(),
            )
        decoration = RenderDecoration(
            parts=[],
            context=selected.context,
            opening=(
                PreparedElementOpen(
                    "div", (0, 5), "div", (), is_void=False, is_self_closing=False, element_metadata=()
                ),
            ),
            closing=(PreparedElementClose("div", (0, 6), "div"),),
            frame=selected.frame,
        )
        assert isinstance(wrap_python_composition_result(decoration), DirectPythonComponentRender)
        wrapped_decoration = wrap_slot_result(
            decoration,
            fill_source=bound_fill,
            public_name="default",
            receiver_render_id="receiver",
            source="x",
            span=(0, 1),
            execution=begin_slot_execution(
                bound_fill,
                public_name="default",
                receiver_render_id="receiver",
                source="x",
                span=(0, 1),
            ),
        )
        assert isinstance(wrapped_decoration, DirectSlotRender)
        assert not _run_eligible_component("ordinary")
        assert not _run_eligible_component(CitryRender(parts=[], context=selected.context, render_target="prepared"))


def test_typed_document_shell_preserves_physical_head_and_validates_body() -> None:
    context = CitryContext()
    doctype = PreparedSourceText("doc", (0, 15), "<!doctype html>")
    html_open = PreparedElementOpen(
        "html", (0, 6), "html", (), is_void=False, is_self_closing=False, element_metadata=()
    )
    head_open = PreparedElementOpen(
        "head", (0, 6), "head", (), is_void=False, is_self_closing=False, element_metadata=()
    )
    head_text = PreparedSourceText("title", (0, 5), "<title>Demo</title>")
    head_close = PreparedElementClose("head", (0, 7), "head")
    body_open = PreparedElementOpen(
        "body", (0, 6), "body", (), is_void=False, is_self_closing=False, element_metadata=()
    )
    body_text = PreparedSourceText("body", (0, 4), "<main>old</main>")
    body_close = PreparedElementClose("body", (0, 7), "body")
    html_close = PreparedElementClose("html", (0, 7), "html")
    render = CitryRender(
        parts=[doctype, html_open, head_open, head_text, head_close, body_open, body_text, body_close, html_close],
        context=context,
        render_target="prepared",
    )
    shell = typed_document_shell(render, '<div id="mount"></div>')
    assert shell is not None
    assert (
        shell.html == '<!doctype html><html><head><title>Demo</title></head><body><div id="mount"></div></body></html>'
    )
    assert shell.head_only_render_ids == frozenset()
    assert (
        typed_document_shell(
            CitryRender(parts=[PreparedSourceText("", (0, 0), "<p>x</p>")], context=context, render_target="prepared"),
            "host",
        )
        is None
    )

    dynamic = PreparedDynamicElementOpen("span", {}, is_void=False)
    with pytest.raises(TypeError, match="unsupported typed part"):
        typed_document_shell(
            CitryRender(
                parts=[doctype, html_open, head_open, dynamic, head_close, body_open, body_close, html_close],
                context=context,
                render_target="prepared",
            ),
            "host",
        )
    with pytest.raises(ValueError, match="Interactive Vue bindings"):
        typed_document_shell(
            CitryRender(
                parts=[
                    doctype,
                    html_open,
                    head_open,
                    PreparedElementOpen(
                        "title",
                        (0, 7),
                        "title",
                        (PreparedAttribute("v-if", "source", (0, 4), "true"),),
                        is_void=False,
                        is_self_closing=False,
                        element_metadata=(),
                    ),
                    head_close,
                    body_open,
                    body_close,
                    html_close,
                ],
                context=context,
                render_target="prepared",
            ),
            "host",
        )
    with pytest.raises(ValueError, match="exactly one body"):
        typed_document_shell(
            CitryRender(
                parts=[doctype, html_open, body_open, body_close, body_open, body_close, html_close],
                context=context,
                render_target="prepared",
            ),
            "host",
        )
    with pytest.raises(ValueError, match="one well-ordered"):
        typed_document_shell(
            CitryRender(parts=[doctype, html_open, body_open], context=context, render_target="prepared"), "host"
        )


def test_vue_serialization_helpers_validate_mounts_and_collect_requirements() -> None:
    validator = _HostValidator("mount")
    validator.feed('<div id="mount"><!--filled--></div>')
    validator.close()
    assert validator.count == 1
    assert not validator.empty
    bad = _HostValidator("mount")
    bad.feed('<span id="mount"></span><div id="mount"></div>')
    bad.close()
    assert bad.count == 2
    assert not bad.valid_attrs

    assert _vue_shell("<p>plain</p>", "host") == "host"
    assert _vue_shell("<!doctype html><body>old</body>", "host") == "<!doctype html><body>host</body>"
    with pytest.raises(ValueError, match="exactly one"):
        _vue_shell("<body><body></body>", "host")
    with pytest.raises(ValueError, match="exactly one"):
        _vue_shell("<body>old", "host")

    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    selected = render_prepared_direct(Page())
    selected.context.js_data["ready"] = True
    event = _event()
    prepared = PreparedElementOpen(
        "<button>",
        (0, 8),
        "button",
        (),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
        event_bindings=(event,),
        browser_bindings=(prepared_browser_binding(helper="$probe", operand="value", target="text"),),
    )
    combined = CitryRender(
        parts=[prepared, selected], context=selected.context, frame=selected.frame, render_target="prepared"
    )
    analysis = analyze_vue_serialization(combined)
    assert {"js_data", "events", "vue_binding"} <= analysis.runtime_requirements
    assert "events" in analysis.active_policy_requirements
    assert _selected_renders(combined)[0] is combined


def test_component_render_tree_walkers_handle_deferred_cross_context_and_cycles() -> None:
    app = Citry(autodiscover=False)

    class Child(Component):
        citry = app
        template = "<span>child</span>"

    class Page(Component):
        citry = app
        template = "<main>page</main>"

    selected = render_prepared_direct(Page())
    parent = selected.context.component
    assert parent is not None
    deferred = DeferredComponent(Child(), parent)
    interior = CitryRender(parts=[deferred, "text"], context=selected.context, render_target="prepared")
    other_context = CitryContext(component=parent)
    other = CitryRender(parts=["other"], context=other_context, render_target="prepared")
    no_id = CitryRender(
        parts=["no-id"],
        context=CitryContext(),
        frame=RenderFrame(None, None, None, is_component_root=False, root_markers=()),
        render_target="prepared",
    )
    root = CitryRender(
        parts=[interior, other, no_id, "raw"],
        context=selected.context,
        frame=selected.frame,
        render_target="prepared",
    )
    tasks = _scan_deferred(root)
    assert len(tasks) == 1
    assert _contains_deferred(root)
    assert _render_ids(root) == {selected.frame.render_id}
    ids, objects = _render_selection(root)
    assert selected.frame.render_id in ids
    assert id(root) in objects
    assert _render_ids_from_parts([interior]) == {selected.frame.render_id}
    assert id(root) in _render_objects(root)
    assert id("text") in _render_objects_from_parts(["text"])
    assert _contains_render(root, interior)
    assert not _contains_render(interior, root)
    root.parts.append(root)
    assert _contains_deferred(root)
    assert _render_ids(root, exclude_render_id=selected.frame.render_id) == set()
    assert _contains_render(root, root)
    assert _render_objects(root)
    assert id(interior) in _render_objects_from_parts([interior])
    _render_selection(root)
    assert _render_ids_from_parts(["raw", interior]) == {selected.frame.render_id}
    cycle = CitryRender(parts=[], context=selected.context, render_target="prepared")
    cycle.parts.append(cycle)
    assert not _contains_deferred(cycle)
    assert not _contains_render(cycle, interior)
    assert _component_path(parent) == ["Page"]
    assert _component_path(None) == []

    replacement = CitryRender(parts=[], context=selected.context, render_target="prepared")
    _replace_in_parts(interior.parts, 0, deferred, replacement)
    assert interior.parts[0] is replacement
    interior.parts.append(deferred)
    _replace_in_parts(interior.parts, 0, deferred, replacement)
    assert interior.parts[-1] is replacement
    with pytest.raises(RuntimeError, match="vanished"):
        _replace_in_parts(interior.parts, 0, deferred, replacement)
    assert _capture_pure_part("text", selected.context) == "text"
    assert _capture_pure_part(PreparedSourceText("x", (0, 1), "x"), selected.context) is not None
    assert _capture_pure_part(
        CitryRender(parts=["x"], context=selected.context, render_target="prepared"), selected.context
    )
    assert _capture_pure_part(selected, selected.context) is None
    assert (
        _capture_pure_part(CitryRender(parts=[], context=other_context, render_target="prepared"), selected.context)
        is None
    )


def test_prepared_render_error_boundary_and_invalid_settled_replacement() -> None:
    app = Citry(autodiscover=False)

    class Replacement(Component):
        citry = app
        template = "<b>replacement</b>"

    class OwnFailure(Component):
        citry = app
        template = "<p>{{ fail() }}</p>"

        def template_data(self, kwargs, slots):
            def fail():
                raise ValueError("body failure")

            return {"fail": fail}

        def on_render(self):
            _result, error = yield
            assert error is not None
            _result, error = yield None
            assert error is not None
            return Replacement()

    recovered = render_prepared_direct(OwnFailure())
    assert "replacement" in recovered.serialize(deps_strategy="ignore")

    class InvalidSettledYield(Component):
        citry = app
        template = "<p>original</p>"

        def on_render(self):
            _result, error = yield
            assert error is None
            _result, error = yield 42
            assert isinstance(error, TypeError)
            return Replacement()

    settled = render_prepared_direct(InvalidSettledYield())
    assert "replacement" in settled.serialize(deps_strategy="ignore")

    class PlainGenerator(Component):
        citry = app
        template = "<p>plain</p>"

        def on_render(self):
            if False:
                yield

    plain = render_prepared_direct(PlainGenerator())
    assert "plain" in plain.serialize(deps_strategy="ignore")

    class OwnFailurePropagates(Component):
        citry = app
        template = "<p>{{ fail() }}</p>"

        def template_data(self, kwargs, slots):
            def fail():
                raise ValueError("unhandled body failure")

            return {"fail": fail}

        def on_render(self):
            yield

    with pytest.raises(ValueError, match="unhandled body failure"):
        render_prepared_direct(OwnFailurePropagates())


def test_settle_guards_cache_publication_and_componentless_generators() -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    bare = CitryRender(parts=[], context=CitryContext(), render_target="prepared")
    bare.context.extra["citry_cache_miss_plan"] = object()
    with pytest.raises(TypeError, match="live component"):
        _settle_render(bare)

    rendered = render_prepared_direct(Page())
    component = rendered.context.component
    assert component is not None
    extensions = component.citry.extensions._extensions_by_name
    original_cache = extensions["cache"]
    extensions["cache"] = object()
    rendered.context.extra["citry_cache_miss_plan"] = object()
    try:
        with pytest.raises(TypeError, match="CacheExtension"):
            _settle_render(rendered)
    finally:
        extensions["cache"] = original_cache

    def replacement_generator():
        _result = yield
        yield "<p>replacement</p>"

    generator = replacement_generator()
    next(generator)
    componentless = CitryRender(parts=[], context=CitryContext(), render_target="html")
    with pytest.raises(RuntimeError, match="no component"):
        _settle_render(componentless, generator)


def test_component_render_specialized_paths_cover_simple_provides_and_client_props() -> None:
    app = Citry(autodiscover=False)

    class Simple(Component):
        citry = app
        simple = True
        template = "<span>simple</span>"

    class Owner(Component):
        citry = app
        template = "<main>owner</main>"

    owner_render = render_prepared_direct(Owner())
    owner = owner_render.context.component
    assert owner is not None
    initial = _render_one(Simple(), owner, owner._provides_inherited)
    assert isinstance(initial.render, SimpleRender)
    assert "simple" in str(initial.render)

    class Provider(Component):
        citry = app
        template = "<p>provider</p>"

        def template_data(self, kwargs, slots):
            self.provide("answer", 42)
            return {}

    provider = render_prepared_direct(Provider())
    assert provider.context.provides["answer"] == 42

    class Target(Component):
        citry = app
        template = "<span>target</span>"

    element = Target()
    element.component_tag_client_bindings = (SimpleNamespace(key="$c-props"),)
    with pytest.raises(RuntimeError, match=r"no \$component"):
        _validate_client_props_target(element)

    class InputProvide(Extension):
        name = "input_provide"

        def on_component_input(self, ctx):
            ctx.component.provide("from_input", "yes")

    input_app = Citry(extensions=[InputProvide], autodiscover=False)

    class InputProvided(Component):
        citry = input_app
        template = "<p>input</p>"

    input_render = render_prepared_direct(InputProvided())
    assert input_render.context.provides["from_input"] == "yes"

    cache_app = Citry(autodiscover=False)

    class CachePage(Component):
        citry = cache_app
        template = "<p>cache</p>"

    cache_extensions = cache_app.extensions._extensions_by_name
    old_cache = cache_extensions["cache"]
    cache_extensions["cache"] = object()
    try:
        with pytest.raises(TypeError, match="CacheExtension"):
            render_prepared_direct(CachePage())
    finally:
        cache_extensions["cache"] = old_cache


def test_standalone_prepared_templates_evict_old_body_variants() -> None:
    app = Citry(autodiscover=False)
    with typed_render_scope(direct=True, vue=True):
        renders = [
            app.render_template(
                "{{ value }}",
                {"value": index, f"unused_{index}": index},
            )
            for index in range(66)
        ]
    assert len(renders) == 66
    assert renders[-1].context.variables["value"] == 65

    from citry.citry_element import _TemplateElement
    from citry.citry_template import CitryTemplate

    app._ensure_registry_ready()
    root_class = app._template_root_class
    assert root_class is not None
    template = CitryTemplate("{{ value }}", "<manual standalone>", kind="standalone")
    manual = [
        _render_one(
            _TemplateElement(
                root_class,
                {"value": index, f"extra_{index}": index},
                {},
                template,
            )
        )
        for index in range(66)
    ]
    _render_one(_TemplateElement(root_class, {"value": 65, "extra_65": 65}, {}, template))
    assert len(manual) == 66
    assert len(template.standalone_bodies) == 64


def test_pure_body_replay_and_template_error_diagnostics_keep_structure() -> None:
    app = Citry(autodiscover=False)

    class Pure(Component):
        citry = app
        pure = True
        template = "<p>pure</p>"

    rendered = render_prepared_direct(Pure())
    component = rendered.context.component
    assert component is not None
    parts, plan, cached_count = _render_and_capture_pure_body(["static"], rendered.context, component)
    assert parts == ["static"]
    assert plan == ("static",)
    assert cached_count == 0
    replayed = _replay_pure_body(("static", PureInteriorBody(("nested",))), rendered.context)
    assert replayed[0] == "static"
    assert isinstance(replayed[1], CitryRender)
    assert replayed[1].parts == ["nested"]
    assert replayed[1].context is rendered.context

    class Exploding:
        source = "<p>{{ bad }}</p>"
        position = (0, 1)

        def render(self, _context):
            raise ValueError("pure body failed")

    with pytest.raises(ValueError, match="pure body failed"):
        _render_pure_live_item(Exploding(), rendered.context, tracing=False)

    import citry.component_render as component_render_module

    trace_monkeypatch = pytest.MonkeyPatch()
    trace_monkeypatch.setattr(component_render_module, "is_tracing", lambda: True)
    try:
        assert (
            _render_pure_live_item(
                type("ValueNode", (), {"render": lambda _self, _ctx: "ok"})(), rendered.context, tracing=True
            )
            == "ok"
        )
    finally:
        trace_monkeypatch.undo()

    error = ValueError("diagnostic")
    _attach_template_position(error, Exploding(), CitryContext(component=component))
    assert "diagnostic" in str(error)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        component_render_module,
        "load_template",
        lambda _component: (_ for _ in ()).throw(OSError()),
    )
    try:
        fallback_error = ValueError("fallback diagnostic")
        _attach_template_position(fallback_error, Exploding(), CitryContext(component=component))
        assert "fallback diagnostic" in str(fallback_error)
    finally:
        monkeypatch.undo()

    slot_monkeypatch = pytest.MonkeyPatch()
    slot_monkeypatch.setattr(component_render_module, "_render_slot_value", lambda *_args: "plain slot")
    try:
        assert _replacement_parts(Slot("slot"), rendered.context, component) == ["plain slot"]
    finally:
        slot_monkeypatch.undo()

    class PublishOnEnter:
        def __enter__(self):
            template.prepared_generate = list
            return self

        def __exit__(self, *_args):
            return False

    from citry.citry_template import CitryTemplate

    template = CitryTemplate("<p>cached</p>", "<compile lock>")
    template.compile_lock = PublishOnEnter()  # type: ignore[assignment]
    assert _get_compiled_template(Pure, template_override=template, prepared=True) is template


def test_replacement_parts_cover_slot_foreign_render_and_simple_child() -> None:
    app = Citry(autodiscover=False)

    class Foreign(Component):
        citry = app
        template = "<i>foreign</i>"

    class Simple(Component):
        citry = app
        simple = True
        template = "<b>simple</b>"

    class Host(Component):
        citry = app
        template = "<p>host</p>"

    host_render = render_prepared_direct(Host())
    host = host_render.context.component
    assert host is not None
    slot = Slot("slot text", slot_name="body")
    slot_parts = _replacement_parts(slot, host_render.context, host)
    assert slot_parts
    foreign = Foreign().render()
    foreign_slot = Slot(foreign, slot_name="body")
    assert _replacement_parts(foreign_slot, host_render.context, host)
    simple_parts = _replacement_parts(Simple(), host_render.context, host)
    assert isinstance(simple_parts[0], DeferredComponent)


def test_finalize_and_merge_handle_simple_componentless_and_extension_failures() -> None:
    empty_context = CitryContext()
    simple = SimpleRender(parts=[], context=empty_context, render_target="prepared")
    assert _finalize(simple, None) is simple
    with pytest.raises(ValueError, match="simple failure"):
        _finalize(simple, ValueError("simple failure"))

    ordinary = CitryRender(parts=[], context=empty_context, render_target="prepared")
    assert _finalize(ordinary, None) is ordinary
    with pytest.raises(ValueError, match="ordinary failure"):
        _finalize(ordinary, ValueError("ordinary failure"))
    _merge_dependencies(CitryContext(), empty_context)

    class Broken(Extension):
        name = "broken_finalize"

        def on_component_rendered(self, _ctx):
            raise RuntimeError("extension failure")

    app = Citry(extensions=[Broken], autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    with pytest.raises(RuntimeError, match="extension failure"):
        render_prepared_direct(Page())

    class Odd(Extension):
        name = "odd_finalize"

        def on_component_rendered(self, _ctx):
            return object()  # type: ignore[return-value]

    odd_app = Citry(extensions=[Odd], autodiscover=False)

    class OddPage(Component):
        citry = odd_app
        template = "<p>odd</p>"

    with typed_render_scope(direct=True, vue=True):
        initial = _render_one(OddPage())
        assert _finalize(initial.render, None) is not None


def test_component_render_rejects_raw_prepared_outputs_and_foreign_spans() -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    with typed_render_scope(direct=True, vue=True):
        rendered = render_prepared_direct(Page())
        with pytest.raises(TypeError, match="raw compiled output"):
            _render_body(["raw"], rendered.context)

        class RawNode:
            position = (0, 1)

            def render(self, _context):
                return "raw node"

        with pytest.raises(TypeError, match="raw output"):
            _render_body([RawNode()], rendered.context)

        prepared = _get_compiled_template(Page, prepared=True)
        assert prepared is not None
        assert _get_compiled_template(Page, prepared=True) is prepared

        from citry.citry_template import CitryTemplate

        foreign = CitryTemplate(
            "<p>foreign</p>",
            "<foreign>",
            foreign_spans=(object(),),
            foreign_prepared=True,
        )
        with pytest.raises(TypeError, match="foreign template spans"):
            _get_compiled_template(Page, template_override=foreign, prepared=True)


def test_component_render_finalization_propagates_hook_failures_and_keeps_render_on_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The finalizer must preserve the render when a hook declines to replace it."""
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    rendered = render_prepared_direct(Page())
    monkeypatch.setattr(app.extensions, "on_component_rendered", lambda *_args: (None, None, False))
    assert _finalize(rendered, None) is rendered

    def fail(*_args):
        raise RuntimeError("finalizer failed")

    monkeypatch.setattr(app.extensions, "on_component_rendered", fail)
    with pytest.raises(RuntimeError, match="finalizer failed"):
        _finalize(rendered, None)


def test_prepared_value_types_reject_untrusted_identity_and_spans() -> None:
    with pytest.raises(ValueError, match="text binding"):
        TextBinding("text")
    with pytest.raises(ValueError, match="element tag"):
        ElementOpen("1p", (), None, None, (0, 0))
    with pytest.raises(ValueError, match="element binding"):
        ElementOpen("p", (), "attrs", None, (0, 0))
    with pytest.raises(TypeError, match="source span"):
        ElementOpen("p", (), None, None, (1, 0))
    with pytest.raises(ValueError, match="element tag"):
        ElementClose("p!", (0, 0))
    with pytest.raises(TypeError, match="source span"):
        ElementClose("p", (0, "1"))  # type: ignore[arg-type]

    fill = PreparedFill("citrySlotFill", "body", ())
    with pytest.raises(ValueError, match="local component call id"):
        LocalComponentCall("call", "Child", "citry-child", (0, 1))
    with pytest.raises(TypeError, match="type key"):
        LocalComponentCall("citryCall0", "", "citry-child", (0, 1))
    with pytest.raises(ValueError, match="custom-element"):
        LocalComponentCall("citryCall0", "Child", "Child", (0, 1))
    with pytest.raises(TypeError, match="source span"):
        LocalComponentCall("citryCall0", "Child", "citry-child", (1, 0))
    with pytest.raises(ValueError, match="duplicate"):
        LocalComponentCall("citryCall0", "Child", "citry-child", (0, 1), (fill, fill))

    for constructor, args in (
        (PreparedFill, ("slot", "body", ())),
        (PreparedSlotOutlet, ("slot", "body", ())),
        (ForwardedSlot, ("slot", "body")),
    ):
        with pytest.raises(ValueError, match="slot site"):
            constructor(*args)
    with pytest.raises(TypeError, match="slot public"):
        PreparedFill("citrySlot0", "", ())

    with pytest.raises(ValueError, match="directive site"):
        RuntimeDirective("directive", "v-show")
    with pytest.raises(TypeError, match="argument"):
        RuntimeDirective("citryDirective0", "v-show", 1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="modifiers"):
        RuntimeDirective("citryDirective0", "v-show", modifiers=(1,))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="sorted"):
        RuntimeDirective("citryDirective0", "v-show", modifiers=("stop", "prevent"))
    duplicate_directive = RuntimeDirective("citryDirective0", "v-show")
    with pytest.raises(ValueError, match="duplicated"):
        PreparedDefinition("root-def", "Root", (), (duplicate_directive, duplicate_directive))

    with pytest.raises(TypeError, match="placement key"):
        PreparedOccurrence("root", "Root", "definition", {}, {}, "parent", None)
    with pytest.raises(TypeError, match="exact dict"):
        PreparedOccurrence("root", "Root", "definition", [], {}, None, None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="string"):
        PreparedOccurrence("root", "Root", "definition", {1: "x"}, {}, None, None)  # type: ignore[dict-item]


def test_prepared_view_checks_markers_tree_references_and_definition_rebinding() -> None:
    child_definition = PreparedDefinition("child-def", "Child", ())
    root_definition = PreparedDefinition("root-def", "Root", (ComponentCall("child"),))
    root = PreparedOccurrence(
        "root",
        "Root",
        "root-def",
        {},
        {"calls": {"child": {"id": "child", "key": "k", "parentId": "root"}}},
        None,
        None,
    )
    child = PreparedOccurrence("child", "Child", "child-def", {}, {}, "root", "k")
    valid = PreparedView(2, "root", (root, child), (root_definition, child_definition))
    rebound = replace_definition_ids(valid, {"root-def": "compiled-root", "child-def": "compiled-child"})
    assert {item.id for item in rebound.definitions} == {"compiled-root", "compiled-child"}
    with pytest.raises(ValueError, match="exactly cover"):
        replace_definition_ids(valid, {"root-def": "compiled-root"})
    with pytest.raises(ValueError, match="unique"):
        replace_definition_ids(valid, {"root-def": "same", "child-def": "same"})

    marker = PreparedMarker("root", "one", "child")
    assert PreparedView(2, "root", (root, child), (root_definition, child_definition), (marker,))
    for markers, message in (
        ((PreparedMarker("other", "one", "child"),), "unknown"),
        ((PreparedMarker("root", "one", "child"), PreparedMarker("root", "one", "child")), "aliases"),
        ((PreparedMarker("root", "z", "root"), PreparedMarker("root", "a", "child")), "sorted"),
    ):
        with pytest.raises(ValueError, match=message):
            PreparedView(2, "root", (root, child), (root_definition, child_definition), markers)

    with pytest.raises(ValueError, match="definition has no"):
        PreparedView(
            2, "root", (root, child), (root_definition, child_definition, PreparedDefinition("orphan", "Orphan", ()))
        )
    with pytest.raises(ValueError, match="type keys"):
        PreparedView(
            2,
            "root",
            (root, child),
            (root_definition, PreparedDefinition("child-def", "Wrong", ())),
        )
    with pytest.raises(ValueError, match="missing parent"):
        PreparedView(
            2,
            "root",
            (root, replace(child, parent_id="missing")),
            (root_definition, child_definition),
        )
    duplicate_child = PreparedOccurrence("other", "Child", "child-def", {}, {}, "root", "k")
    with pytest.raises(ValueError, match="placement key"):
        PreparedView(
            2,
            "root",
            (root, child, duplicate_child),
            (root_definition, child_definition),
        )
    with pytest.raises(ValueError, match="unknown occurrence"):
        PreparedView(
            2,
            "root",
            (root, child),
            (PreparedDefinition("root-def", "Root", (ComponentCall("missing"),)), child_definition),
        )


def test_prepared_slots_and_ownership_references_are_validated() -> None:
    site = "citrySlotSite"
    fill = FillClosure(site, "body", "root", "child", (Html("<b>x</b>", "template"),))
    slot = SlotOutlet(site, "body", "child", fill)
    root_definition = PreparedDefinition("root-def", "Root", (ComponentCall("child"),))
    child_definition = PreparedDefinition("child-def", "Child", (slot,))
    root = PreparedOccurrence(
        "root",
        "Root",
        "root-def",
        {},
        {"calls": {"child": {"id": "child", "key": "k", "parentId": "root"}}},
        None,
        None,
    )
    child = PreparedOccurrence("child", "Child", "child-def", {}, {}, "root", "k")
    assert PreparedView(0, "root", (root, child), (root_definition, child_definition))

    bad_identity = SlotOutlet(site, "other", "child", fill)
    with pytest.raises(ValueError, match="identity"):
        PreparedView(
            0, "root", (root, child), (root_definition, PreparedDefinition("child-def", "Child", (bad_identity,)))
        )
    bad_owner = SlotOutlet(site, "body", "root", fill)
    with pytest.raises(ValueError, match="receiver"):
        PreparedView(
            0, "root", (root, child), (root_definition, PreparedDefinition("child-def", "Child", (bad_owner,)))
        )
    bad_reference = PreparedDefinition("root-def", "Root", (ComponentCall("missing"),))
    with pytest.raises(ValueError, match="unknown occurrence"):
        PreparedView(0, "root", (root, child), (bad_reference, child_definition))


def test_prepared_asset_security_metadata_accepts_valid_shapes_and_rejects_tampering() -> None:
    view = SimpleNamespace(occurrences=(SimpleNamespace(id="root", type_key="Root"),))
    digest = "0" * 64
    component_style = {
        "owner": {"kind": "component", "typeKey": "Root", "occurrenceIds": ["root"]},
        "source": {"kind": "owned", "url": "/assets/style.css", "sha256": digest, "attrs": {"rel": "stylesheet"}},
        "lazyAllowed": True,
    }
    external_style = {
        "owner": {"kind": "extension", "extensionName": "preview"},
        "source": {"kind": "external", "url": "https://cdn.example/style.css", "attrs": {"rel": "stylesheet"}},
        "lazyAllowed": False,
    }
    component_script = {
        "owner": {"kind": "component", "typeKey": "Root"},
        "source": {"kind": "owned", "url": "/assets/script.js", "sha256": digest},
        "lazyAllowed": True,
        "registersOptions": True,
    }
    external_script = {
        "owner": {"kind": "extension", "extensionName": "preview"},
        "source": {"kind": "external", "url": "https://cdn.example/script.js", "attrs": {}},
        "lazyAllowed": False,
        "registersOptions": False,
    }
    _validate_style_assets([component_style, external_style], view)
    _validate_script_assets([component_script, external_script])

    style_cases: list[tuple[list[dict[str, object]], str]] = []
    style_cases.append(([{}], "invalid shape"))
    for mutator in (
        lambda value: value.update(extra=True),
        lambda value: value.update(owner="bad"),
        lambda value: value.update(source="bad"),
        lambda value: value.update(lazyAllowed=1),
    ):
        value = deepcopy(component_style)
        mutator(value)
        style_cases.append(([value], "metadata"))
    value = deepcopy(component_style)
    value["source"]["url"] = "relative.css"
    style_cases.append(([value], "metadata"))
    value = deepcopy(component_style)
    value["source"]["url"] = "/assets//style.css"
    style_cases.append(([value], "metadata"))
    value = deepcopy(component_style)
    value["source"]["sha256"] = "bad"
    style_cases.append(([value], "metadata"))
    value = deepcopy(external_style)
    value["source"]["extra"] = True
    style_cases.append(([value], "metadata"))
    value = deepcopy(component_style)
    value["source"]["kind"] = "mystery"
    style_cases.append(([value], "metadata"))
    value = deepcopy(component_style)
    value["source"]["attrs"] = {}
    style_cases.append(([value], "metadata"))
    value = deepcopy(component_style)
    value["owner"] = {"kind": "component", "typeKey": "Root", "occurrenceIds": []}
    style_cases.append(([value], "metadata"))
    value = deepcopy(component_style)
    value["owner"]["occurrenceIds"] = ["missing"]
    style_cases.append(([value], "metadata"))
    value = deepcopy(external_style)
    value["owner"] = {"kind": "extension", "extensionName": 1}
    style_cases.append(([value], "metadata"))
    value = deepcopy(component_style)
    value["source"]["url"] = "/assets/same.css"
    duplicate = deepcopy(value)
    duplicate["source"]["sha256"] = "1" * 64
    style_cases.append(([value, duplicate], "metadata"))
    for values, _message in style_cases:
        with pytest.raises(ValueError, match=r"invalid|metadata"):
            _validate_style_assets(values, view)

    script_cases: list[tuple[list[dict[str, object]], str]] = []
    script_cases.append(([{"owner": "bad", "source": {}, "lazyAllowed": True, "registersOptions": False}], "metadata"))
    value = deepcopy(component_script)
    value.pop("registersOptions")
    script_cases.append(([value], "invalid shape"))
    value = deepcopy(component_script)
    value["registersOptions"] = 1
    script_cases.append(([value], "metadata"))
    value = deepcopy(component_script)
    value["owner"] = {"kind": "component", "typeKey": 1}
    script_cases.append(([value], "metadata"))
    value = deepcopy(external_script)
    value["owner"]["extensionName"] = 1
    script_cases.append(([value], "metadata"))
    value = deepcopy(external_script)
    value["registersOptions"] = True
    script_cases.append(([value], "metadata"))
    value = deepcopy(component_script)
    value["source"]["url"] = 1
    script_cases.append(([value], "metadata"))
    value = deepcopy(component_script)
    value["source"]["kind"] = "mystery"
    script_cases.append(([value], "metadata"))
    value = deepcopy(component_script)
    value["source"]["sha256"] = "bad"
    script_cases.append(([value], "metadata"))
    value = deepcopy(external_script)
    value["source"]["extra"] = True
    script_cases.append(([value], "metadata"))
    value = deepcopy(component_script)
    value["source"]["url"] = "/assets/dupe.js"
    duplicate = deepcopy(value)
    duplicate["source"]["sha256"] = "1" * 64
    script_cases.append(([value, duplicate], "metadata"))
    for values, message in script_cases:
        with pytest.raises(ValueError, match=message):
            _validate_script_assets(values)


def test_direct_relationship_helpers_cover_session_and_slot_execution_boundaries() -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    selected = render_prepared_direct(Page())
    plain = CitryRender(parts=[], context=selected.context, render_target="prepared")
    with direct_render_scope() as session:
        with direct_render_scope() as nested:
            assert nested is session
        assert active_execution() is None
        slot = __import__("citry.slots", fromlist=["Slot"]).Slot("slot")
        assert direct_fill_source(slot) is None
        bind_template_fill(
            slot,
            lexical_render_id="render",
            kind="fill",
            public_name="body",
            source="<c-fill>",
            span=(0, 8),
            origin="template",
        )
        fill = direct_fill_source(slot)
        assert fill is not None
        assert fill.session is session

        wrapped = wrap_nested_template(
            plain,
            lexical_render_id="render",
            public_name="body",
            source="<c-fill>",
            span=(0, 8),
            origin="template",
        )
        assert isinstance(wrapped, UnboundNestedTemplateRender)
        bound = bind_nested_template(wrapped, selected.context)
        assert isinstance(bound, DirectNestedTemplateRender)
        assert bind_nested_template("ordinary", selected.context) == "ordinary"

        execution = begin_slot_execution(
            fill,
            public_name="body",
            receiver_render_id=selected.context.component.id,  # type: ignore[union-attr]
            source="<c-slot>",
            span=(0, 8),
        )
        with direct_execution_scope(execution):
            assert active_execution() is execution
        assert active_execution() is None

        with direct_receiver_scope(selected.context):
            captured = capture_slot_call(slot, lambda: plain)
        assert isinstance(captured, DirectSlotRender)

        execution = begin_slot_execution(
            fill,
            public_name="body",
            receiver_render_id=selected.context.component.id,  # type: ignore[union-attr]
            source="<c-slot>",
            span=(0, 8),
        )
        with direct_execution_scope(execution):
            captured = capture_slot_call(slot, lambda: plain)
            assert execution.consumed
        assert isinstance(captured, DirectSlotRender)

        other_slot = __import__("citry.slots", fromlist=["Slot"]).Slot("other")
        bind_template_fill(
            other_slot,
            lexical_render_id="render",
            kind="nested",
            public_name="other",
            source="nested",
            span=(0, 6),
            origin=None,
        )
        other_fill = direct_fill_source(other_slot)
        assert other_fill is not None
        with direct_execution_scope(execution), direct_receiver_scope(selected.context):
            nested_capture = capture_slot_call(other_slot, lambda: plain)
        assert isinstance(nested_capture, DirectSlotRender)

        assert wrap_nested_template(
            plain, lexical_render_id="x", public_name="x", source="x", span=(0, 1), origin=None
        )

    with pytest.raises(RuntimeError, match="different"):
        with direct_render_scope():
            begin_slot_execution(
                fill,
                public_name="body",
                receiver_render_id="receiver",
                source="x",
                span=(0, 1),
            )

    assert wrap_python_composition_result("text") == "text"
    with direct_render_scope():
        component = wrap_python_composition_result(selected)
        assert isinstance(component, DirectPythonComponentRender)
        composite = CitryRender(parts=[selected], context=selected.context, render_target="prepared")
        changed = wrap_python_composition_result(composite)
        assert isinstance(changed, CitryRender)
        assert isinstance(changed.parts[0], DirectPythonComponentRender)
        assert wrap_python_composition_result(plain) is plain

    with pytest.raises(TypeError, match="component root"):
        DirectPythonComponentRender(plain, local_ordinal=0)
    with pytest.raises(ValueError, match="nonnegative"):
        DirectPythonComponentRender(selected, local_ordinal=-1)
    authored_frame = replace(
        selected.frame,
        prepared_occurrence=PreparedOccurrenceMetadata(
            call=object(), raw_slots_present=False, component_tag_client_bindings=()
        ),
    )
    authored = CitryRender(parts=[], context=selected.context, frame=authored_frame, render_target="prepared")
    with pytest.raises(TypeError, match="authored"):
        DirectPythonComponentRender(authored, local_ordinal=0)
    assert isinstance(
        DirectCallRunRender(plain, call_node=SimpleNamespace(source="x", position=(0, 1)), child_type_key="Child"),
        DirectCallRunRender,
    )


def test_vue_events_cache_collision_eviction_and_collected_engine_are_explicit() -> None:
    """Content-addressed assets reject collisions and remain bounded by engine lifetime."""
    app = Citry(autodiscover=False)
    producer = default_events_producer(app)

    producer._publish_bundle("same", b"first")
    with pytest.raises(RuntimeError, match="bundle digest collision"):
        producer._publish_bundle("same", b"different")
    for index in range(130):
        producer._publish_bundle(f"bundle-{index}", str(index).encode())
    assert vue_events.definition_bundle(app, "bundle-0") is None
    assert vue_events.definition_bundle(app, "bundle-129") == b"129"

    producer._publish_style("same-style", b"first")
    with pytest.raises(RuntimeError, match="stylesheet asset digest collision"):
        producer._publish_style("same-style", b"different")
    for index in range(130):
        producer._publish_style(f"style-{index}", str(index).encode())
    assert vue_events.style_asset(app, "style-0") is None
    assert vue_events.style_asset(app, "style-129") == b"129"

    del app
    gc.collect()
    with pytest.raises(RuntimeError, match="engine owning this Vue producer was collected"):
        producer._tag_for_type("missing")


def test_vue_events_rejects_componentless_roots_and_incomplete_compiler_output() -> None:
    app = Citry(autodiscover=False)
    bare = CitryRender(parts=[], context=CitryContext(), render_target="prepared")
    with pytest.raises(UnsupportedPreparedView, match="no current component registry"):
        default_events_producer(app).prepare_from_render(bare, citry=app, app_id="bare", revision=0)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    producer = default_events_producer(app)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(producer, "_compile_view", lambda _assembly: {})
    try:
        with pytest.raises(ValueError, match="exactly cover the prepared definitions"):
            producer.prepare_from_render(render_prepared_direct(Page()), citry=app, app_id="missing", revision=0)
    finally:
        monkeypatch.undo()


def test_vue_events_validates_opaque_html_before_and_after_payload_assembly() -> None:
    class RawPage(Component):
        citry = Citry(autodiscover=False, security_javascript="warn", security_csp="warn")
        template = '<main><c-raw><button onclick="window.x=1">raw</button></c-raw></main>'

    app = RawPage.citry
    render = render_prepared_direct(RawPage())
    payload = default_events_producer(app).prepare_from_render(render, citry=app, app_id="raw", revision=0)
    assert payload["occurrences"]

    original_assemble = vue_events.assemble_typed_render

    def mutate_before_validation(*args, **kwargs):
        assembly = original_assemble(*args, **kwargs)
        record = next(iter(assembly.view.occurrences[0].prepared_data["opaqueHtml"].values()))
        record["html"] = object()
        return assembly

    producer = default_events_producer(Citry(autodiscover=False))
    plain_app = producer._builtin_citry_ref() if producer._builtin_citry_ref is not None else None
    assert plain_app is not None

    class PlainRaw(Component):
        citry = plain_app
        template = "<main><c-raw><em>raw</em></c-raw></main>"

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(vue_events, "assemble_typed_render", mutate_before_validation)
    try:
        with pytest.raises(AssertionError, match="opaque HTML record changed type"):
            producer.prepare_from_render(render_prepared_direct(PlainRaw()), citry=plain_app, app_id="raw", revision=0)
    finally:
        monkeypatch.undo()

    render = render_prepared_direct(PlainRaw())
    original_manifest = vue_events.prepared_manifest

    def mutate_after_validation(*args, **kwargs):
        payload = original_manifest(*args, **kwargs)
        record = next(iter(payload["occurrences"][0]["preparedData"]["opaqueHtml"].values()))
        record["html"] = object()
        return payload

    monkeypatch.setattr(vue_events, "prepared_manifest", mutate_after_validation)
    try:
        with pytest.raises(AssertionError, match="opaque HTML payload changed type"):
            producer.prepare_from_render(render, citry=plain_app, app_id="raw", revision=0)
    finally:
        monkeypatch.undo()


def test_vue_events_dependency_metadata_guards_cover_fallback_nonce_and_class_identity() -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    render = render_prepared_direct(Page())
    root_id = render.frame.render_id
    assert root_id is not None
    render.context.extra.setdefault("dependencies", {})[
        DependencyRecord(Page.class_id, root_id, component_class=None)
    ] = None
    payload = default_events_producer(app).prepare_from_render(render, citry=app, app_id="fallback", revision=0)
    assert payload["occurrences"]

    app_mismatch = Citry(autodiscover=False)

    class MismatchPage(Component):
        citry = app_mismatch
        template = "<p>page</p>"

    class Other(Component):
        citry = app_mismatch
        template = "<p>other</p>"

    mismatched = render_prepared_direct(MismatchPage())
    mismatch_id = mismatched.frame.render_id
    assert mismatch_id is not None
    mismatched.context.extra.setdefault("dependencies", {})[
        DependencyRecord(MismatchPage.class_id, mismatch_id, component_class=Other)
    ] = None
    with pytest.raises(ValueError, match="component class changed before Vue metadata preparation"):
        default_events_producer(app_mismatch).prepare_from_render(
            mismatched, citry=app_mismatch, app_id="mismatch", revision=0
        )

    nonce_app = Citry(autodiscover=False)

    class NoncePage(Component):
        citry = nonce_app
        template = "<p>nonce</p>"

        class Dependencies:
            js = [Script(content="window.nonceReady=true", attrs={"nonce": "request-token"}, wrap=False)]

    nonce_render = render_prepared_direct(NoncePage())
    nonce_materializer = _ScriptSecurityMaterializer(collect_integrity=False, csp_nonce="request-token")
    nonce_result = default_events_producer(nonce_app)._prepare_from_render_result(
        nonce_render,
        citry=nonce_app,
        app_id="nonce",
        revision=0,
        dependency_options={"script_security": nonce_materializer},
    )
    assert nonce_result.payload["scripts"]
    assert all("nonce" not in item["source"]["attrs"] for item in nonce_result.payload["scripts"])


def test_vue_events_reports_missing_event_descriptor_and_unowned_hook_asset(monkeypatch: pytest.MonkeyPatch) -> None:
    from citry.ext.dependencies import emission

    class AddAsset(Extension):
        name = "add_unowned_asset"

        def on_dependencies(self, ctx):
            ctx.scripts.append(Script(content="window.unowned=true", wrap=False))

    app = Citry(autodiscover=False, extensions=[AddAsset])

    class Page(Component):
        citry = app
        template = '<button @c-click="save">save</button>'

        class Events:
            def save(self):
                return None

    original_resolve = emission._resolve_records

    def inject_stale_owner(*args, **kwargs):
        resolved = original_resolve(*args, **kwargs)
        if resolved.scripts:
            resolved.script_owners[id(resolved.scripts[0])].add("stale-render-id")
        return resolved

    monkeypatch.setattr(emission, "_resolve_records", inject_stale_owner)

    payload = default_events_producer(app).prepare_from_render(
        render_prepared_direct(Page()), citry=app, app_id="owned", revision=0
    )
    assert any(item["owner"]["typeKey"] == Page.class_id for item in payload["scripts"])

    original_manifest = vue_events.build_events_manifest

    def missing_descriptor(*args, **kwargs):
        manifest = original_manifest(*args, **kwargs)
        manifest["componentClasses"] = []
        return manifest

    monkeypatch.setattr(vue_events, "build_events_manifest", missing_descriptor)
    with pytest.raises(ValueError, match="no matching component descriptor"):
        default_events_producer(app).prepare_from_render(
            render_prepared_direct(Page()), citry=app, app_id="descriptor", revision=0
        )


def test_prepared_view_rejects_tampered_graph_identity_and_slot_relationships() -> None:
    """The immutable prepared graph still checks every relationship at its boundary."""
    with pytest.raises(TypeError, match="non-string object key"):
        PreparedOccurrence("root", "Root", "root-def", {"nested": {1: "bad"}}, {}, None, None)

    root_definition = PreparedDefinition("root-def", "Root", ())
    root = PreparedOccurrence("root", "Root", "root-def", {}, {}, None, None)
    with pytest.raises(TypeError, match="exact PreparedMarker"):
        PreparedView(0, "root", (root,), (root_definition,), markers=(object(),))

    parented_root = PreparedOccurrence("root", "Root", "root-def", {}, {}, "child", "root")
    child = PreparedOccurrence("child", "Root", "root-def", {}, {}, "root", "child")
    with pytest.raises(ValueError, match="root occurrence has a parent"):
        PreparedView(0, "root", (parented_root, child), (root_definition,))

    malformed_child = PreparedOccurrence("child", "Root", "root-def", {}, {}, "root", "child")
    object.__setattr__(malformed_child, "placement_key", None)
    with pytest.raises(AssertionError, match="placement key"):
        PreparedView(0, "root", (root, malformed_child), (root_definition,))

    cycle_a = PreparedOccurrence("a", "Root", "root-def", {}, {}, "root", "a")
    cycle_b = PreparedOccurrence("b", "Root", "root-def", {}, {}, "a", "b")
    object.__setattr__(cycle_a, "parent_id", "b")
    with pytest.raises(ValueError, match="parent cycle"):
        PreparedView(0, "root", (root, cycle_a, cycle_b), (root_definition,))

    site = "citrySlotGraph"
    fill = FillClosure(site, "body", "root", "root", ())
    invalid_slot = SlotOutlet(site, "body", "root", fill)
    object.__setattr__(invalid_slot, "site_id", "invalid")
    object.__setattr__(fill, "site_id", "invalid")
    invalid_slot_definition = PreparedDefinition("root-def", "Root", (invalid_slot,))
    with pytest.raises(ValueError, match="slot site id"):
        PreparedView(0, "root", (root,), (invalid_slot_definition,))

    valid_fill = FillClosure(site, "body", "root", "root", ())
    duplicate_slots = PreparedDefinition(
        "root-def",
        "Root",
        (
            SlotOutlet(site, "body", "root", valid_fill),
            SlotOutlet(site, "body", "root", valid_fill),
        ),
    )
    with pytest.raises(ValueError, match="slot site id is duplicated"):
        PreparedView(0, "root", (root,), (duplicate_slots,))

    prepared_duplicate = PreparedDefinition(
        "root-def",
        "Root",
        (SlotOutlet(site, "body", "root", valid_fill), PreparedSlotOutlet(site, "body", ())),
    )
    with pytest.raises(ValueError, match="slot site id is duplicated"):
        PreparedView(0, "root", (root,), (prepared_duplicate,))

    unknown_owner = FillClosure(site, "body", "unknown", "root", ())
    ownership_definition = PreparedDefinition("root-def", "Root", (SlotOutlet(site, "body", "root", unknown_owner),))
    with pytest.raises(ValueError, match="unknown ownership occurrence"):
        PreparedView(0, "root", (root,), (ownership_definition,))

    self_reference = PreparedDefinition("root-def", "Root", (ComponentCall("root"),))
    with pytest.raises(ValueError, match="root must not be referenced"):
        PreparedView(0, "root", (root,), (self_reference,))


def test_vue_serialization_plan_rejects_runtime_removal_and_missing_standalone_assets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = Citry(autodiscover=False)
    plan_context = CitryContext(extra={VUE_RUNTIME_EMITTED_KEY: True})
    plan = VueSerializationPlan(
        shell_html='<div id="citry-vue-app"></div>',
        host_id="citry-vue-app",
        configuration="{}",
        scripts=(Script(content="Citry interactive runtime"), Script(content="bootstrap();")),
        styles=(),
        script_security=None,
        javascript_policy=None,
        render_context=plan_context,
        validate_metadata=lambda: None,
    )
    with pytest.raises(ValueError, match="required Citry runtime asset"):
        plan.finalize('<div id="citry-vue-app"></div>')

    class Page(Component):
        citry = app
        template = "<button :title=\"'ready'\">page</button>"

    render = render_prepared_direct(Page())
    context = OnSerializeContext(
        citry=app,
        context=render.context,
        selected_render=render,
        html='<div id="citry-vue-app"></div>',
        placeholders={},
        deps_strategy="document",
        deps_position="smart",
    )
    context.context.extra["_vue_app_id"] = 1
    with pytest.raises(TypeError, match="app ID metadata"):
        prepare_vue_serialization(
            context,
            script_security=None,
            _security_csp="off",
            javascript_policy=None,
            security_javascript="allow",
            analysis=VueSerializationAnalysis(frozenset({"vue_binding"}), frozenset()),
        )

    # Invalid dependency strategies have a documented component-JS-only escape hatch.
    context.context.extra.pop("_vue_app_id")
    component_only = VueSerializationAnalysis(frozenset({"component_js"}), frozenset())
    context = replace(context, deps_strategy="custom")
    assert (
        prepare_vue_serialization(
            context,
            script_security=None,
            _security_csp="off",
            javascript_policy=None,
            security_javascript="allow",
            analysis=component_only,
        )
        is None
    )
    context = replace(context, deps_strategy="custom")
    with pytest.raises(ValueError, match="deps_strategy='document' or 'fragment'"):
        prepare_vue_serialization(
            context,
            script_security=None,
            _security_csp="off",
            javascript_policy=None,
            security_javascript="allow",
            analysis=VueSerializationAnalysis(frozenset({"events"}), frozenset()),
        )

    original_initial = __import__(
        "citry._vue.serialization", fromlist=["_prepare_initial_result"]
    )._prepare_initial_result

    def missing_plugin(*_args, **_kwargs):
        return (
            {"occurrences": [], "definitions": [], "scripts": [], "styles": []},
            {},
            lambda: None,
            (SimpleNamespace(name="bad", plugin=None),),
        )

    monkeypatch.setattr("citry._vue.serialization._prepare_initial_result", missing_plugin)
    context = replace(context, deps_strategy="document")
    context.context.extra.pop("_vue_app_id", None)
    with pytest.raises(TypeError, match="no registered plugin descriptor"):
        prepare_vue_serialization(
            context,
            script_security=None,
            _security_csp="off",
            javascript_policy=None,
            security_javascript="allow",
            analysis=VueSerializationAnalysis(frozenset({"vue_binding"}), frozenset()),
        )
    monkeypatch.setattr("citry._vue.serialization._prepare_initial_result", original_initial)


def test_vue_serialization_head_and_standalone_asset_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Citry(autodiscover=False)
    bare = CitryRender(parts=[], context=CitryContext(), render_target="prepared")
    with pytest.raises(ValueError, match="component-owned root"):
        _reject_head_browser_activity(bare, frozenset({"head"}))

    class EventsPage(Component):
        citry = app
        template = '<button @c-click="save">save</button>'

        class Events:
            def save(self):
                return None

    event_render = render_prepared_direct(EventsPage())
    event_id = event_render.frame.render_id
    assert event_id is not None
    event_key = type("EventKey", (), {"render_id": event_id})()
    event_render.context.extra["events"] = {event_key: None}
    with pytest.raises(ValueError, match="Events are unsupported"):
        _reject_head_browser_activity(event_render, frozenset({event_id}))

    class StaticPage(Component):
        citry = app
        template = "<p>static</p>"

    render = render_prepared_direct(StaticPage())
    context = OnSerializeContext(
        citry=app,
        context=render.context,
        selected_render=render,
        html='<div id="citry-vue-app"></div>',
        placeholders={},
        deps_strategy="document",
        deps_position="smart",
    )

    def fake_initial(*_args, **_kwargs):
        return (
            {
                "occurrences": [],
                "definitions": [{"sha256": "a" * 64}],
                "scripts": [],
                "styles": [],
            },
            {},
            lambda: None,
            (),
        )

    monkeypatch.setattr("citry._vue.serialization._prepare_initial_result", fake_initial)
    with pytest.raises(RuntimeError, match="definition bundle was not published"):
        prepare_vue_serialization(
            context,
            script_security=None,
            _security_csp="off",
            javascript_policy=None,
            security_javascript="allow",
            analysis=VueSerializationAnalysis(frozenset({"vue_binding"}), frozenset()),
        )

    def fake_script(*_args, **_kwargs):
        return (
            {
                "occurrences": [],
                "definitions": [],
                "scripts": [{"source": {"kind": "owned", "sha256": "b" * 64}}],
                "styles": [],
            },
            {},
            lambda: None,
            (),
        )

    monkeypatch.setattr("citry._vue.serialization._prepare_initial_result", fake_script)
    with pytest.raises(RuntimeError, match="script asset was not retained"):
        prepare_vue_serialization(
            context,
            script_security=None,
            _security_csp="off",
            javascript_policy=None,
            security_javascript="allow",
            analysis=VueSerializationAnalysis(frozenset({"vue_binding"}), frozenset()),
        )

    def fake_style(*_args, **_kwargs):
        return (
            {
                "occurrences": [],
                "definitions": [],
                "scripts": [],
                "styles": [{"source": {"kind": "owned", "sha256": "c" * 64, "url": "/c.css"}}],
            },
            {},
            lambda: None,
            (),
        )

    monkeypatch.setattr("citry._vue.serialization._prepare_initial_result", fake_style)
    with pytest.raises(RuntimeError, match="stylesheet was not retained"):
        prepare_vue_serialization(
            context,
            script_security=None,
            _security_csp="off",
            javascript_policy=None,
            security_javascript="allow",
            analysis=VueSerializationAnalysis(frozenset({"vue_binding"}), frozenset()),
        )


def test_vue_capture_authentication_rejects_inconsistent_dynamic_provenance() -> None:
    opening = prepared_dynamic_element_open("button", {})

    def trusted(**changes: object) -> PreparedDynamicElementOpen:
        value = replace(opening, **changes)
        object.__setattr__(value, "_producer_token", opening._producer_token)
        return value

    # Authored attributes and their source are an all-or-nothing provenance pair.
    assert not is_authenticated_dynamic_element_open(
        trusted(authored_attrs=(PreparedAttribute("@click", "source", (0, 6), "@click"),))
    )
    assert not is_authenticated_dynamic_element_open(trusted(authored_source="@click"))
    # The key check must run after the private producer token has been verified.
    assert not is_authenticated_dynamic_element_open(trusted(key=1))

    with pytest.raises(ValueError, match="authenticated compiled candidate"):
        PreparedElementOpen(
            "<button>",
            (0, 8),
            "button",
            (),
            is_void=False,
            is_self_closing=False,
            element_metadata=(),
            runtime_event_bindings=(_event("citryRuntimeEventguard"),),
        )


def test_direct_relationship_guards_cover_closed_sessions_and_composition_edges() -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    selected = render_prepared_direct(Page())
    with pytest.raises(TypeError, match="authenticated fill source"):
        DirectProjectionRender(
            selected,
            execution_index=1,
            fill_source=object(),  # type: ignore[arg-type]
            parent_execution=None,
            public_name="body",
            receiver_render_id="receiver",
            source="x",
            span=(0, 1),
        )

    with direct_render_scope() as session:
        session.active = False
        with pytest.raises(RuntimeError, match="closed"):
            with direct_render_scope():
                pass

    slot = __import__("citry.slots", fromlist=["Slot"]).Slot("outside")
    bind_template_fill(
        slot,
        lexical_render_id="outside",
        kind="fill",
        public_name="body",
        source="x",
        span=(0, 1),
        origin=None,
    )
    assert direct_fill_source(slot) is None

    with direct_render_scope() as first_session:
        first_slot = __import__("citry.slots", fromlist=["Slot"]).Slot("first")
        bind_template_fill(
            first_slot,
            lexical_render_id="first",
            kind="fill",
            public_name="body",
            source="x",
            span=(0, 1),
            origin=None,
        )
        old_fill = direct_fill_source(first_slot)
        assert old_fill is not None
        assert old_fill.session is first_session

    with direct_render_scope():
        current_slot = __import__("citry.slots", fromlist=["Slot"]).Slot("current")
        bind_template_fill(
            current_slot,
            lexical_render_id="current",
            kind="fill",
            public_name="body",
            source="x",
            span=(0, 1),
            origin=None,
        )
        current_fill = direct_fill_source(current_slot)
        assert current_fill is not None
        execution = begin_slot_execution(
            current_fill,
            public_name="body",
            receiver_render_id="receiver",
            source="x",
            span=(0, 1),
        )
        with pytest.raises(RuntimeError, match="different or closed"):
            wrap_slot_result(
                selected,
                fill_source=old_fill,
                public_name="body",
                receiver_render_id="receiver",
                source="x",
                span=(0, 1),
                execution=execution,
            )

        decoration = RenderDecoration(
            parts=[],
            context=selected.context,
            opening=(
                PreparedElementOpen(
                    "div", (0, 5), "div", (), is_void=False, is_self_closing=False, element_metadata=()
                ),
            ),
            closing=(PreparedElementClose("div", (0, 6), "div"),),
            frame=selected.frame,
        )
        composite = CitryRender(
            parts=[decoration],
            context=selected.context,
            frame=replace(selected.frame, is_component_root=False),
            render_target="prepared",
        )
        wrapped = wrap_python_composition_result(composite)
        assert isinstance(wrapped, CitryRender)
        assert isinstance(wrapped.parts[0], DirectPythonComponentRender)


def test_leaf_projection_validates_spreads_and_prepared_dom_properties() -> None:
    spread_source = "<div c-bind>"
    spread_attr = StaticHtmlAttr(spread_source, (5, 11), "c-bind", value=True, used_vars=())
    spread_node = PreparedElementOpenNode(
        spread_source,
        (0, len(spread_source)),
        "div",
        (spread_attr,),
        (),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
    )
    assert _spread_attrs_renderer(spread_node, spread_node) is spread_node
    assert _spread_passthrough_is_live(spread_node, CitryContext())
    assert not _spread_passthrough_is_live(object(), CitryContext())

    static_source = "<button title='x'>"
    static_attr = StaticHtmlAttr(static_source, (8, 17), "title", "x", ())
    static_node = PreparedElementOpenNode(
        static_source,
        (0, len(static_source)),
        "button",
        (static_attr,),
        (),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
    )
    prepared = PreparedElementOpen(
        static_source,
        (0, len(static_source)),
        "button",
        (PreparedAttribute("title", "source", (8, 17), "title='x'"),),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
    )
    assert _spread_data_attrs(static_node, prepared) == {"title": "x"}
    with pytest.raises(AssertionError, match="parsed identity"):
        _spread_data_attrs(
            static_node,
            replace(prepared, attrs=(PreparedAttribute("title", "source", (9, 17), "itle='x'"),)),
        )

    unsafe = PreparedElementOpen(
        "<button>",
        (0, 8),
        "button",
        (PreparedAttribute("onclick", "data", (0, 1), "window.x()"),),
        is_void=False,
        is_self_closing=False,
        element_metadata=(),
    )
    assert _validate_open(unsafe) is not None
    assert _validate_data_attrs({"data-cev-forged": "x"}, tag="button") is not None
    assert _validate_data_attrs({"data-citry-runtime-events": "x"}, tag="button") is not None

    operation = _Open(
        spread_node,
        spread_node,
        None,
        None,
        None,
        None,
        None,
        spread_node,
        (),
        (),
        None,
    )
    projected = _prepared_open(operation, {"title": "ready", "skip": None})
    assert projected.data_attrs == {"title": "ready"}


def test_direct_capture_cache_identity_handles_evicted_component(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    context = CitryContext()
    _issue_cache_replay_identity(context, app, Page)
    monkeypatch.setattr(Citry, "get_component_by_class_id", lambda _self, _class_id: (_ for _ in ()).throw(KeyError))
    assert not _matches_cache_replay_identity(context, app, Page)


def test_vue_document_shell_rejects_unresolved_non_dependency_placeholder() -> None:
    render = CitryRender(
        parts=[
            PreparedSourceText("doc", (0, 15), "<!doctype html>"),
            PreparedElementOpen(
                "body",
                (0, 6),
                "body",
                (),
                is_void=False,
                is_self_closing=False,
                element_metadata=(),
            ),
            Placeholder("unresolved"),
            PreparedElementClose("body", (0, 7), "body"),
        ],
        context=CitryContext(),
        render_target="prepared",
    )
    with pytest.raises(TypeError, match="unresolved placeholder"):
        typed_document_shell(render, '<div id="mount"></div>')


def test_vue_serialization_rejects_unmounted_events_before_browser_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<p>page</p>"

    render = render_prepared_direct(Page())
    context = OnSerializeContext(
        citry=app,
        context=render.context,
        selected_render=render,
        html='<div id="citry-vue-app"></div>',
        placeholders={},
        deps_strategy="document",
        deps_position="smart",
    )

    def fake_initial(*_args, **_kwargs):
        return (
            {"occurrences": [{"eventContext": {}}], "definitions": [], "scripts": [], "styles": []},
            {},
            lambda: None,
            (),
        )

    monkeypatch.setattr("citry._vue.serialization._prepare_initial_result", fake_initial)
    with pytest.raises(ValueError, match="mounted web integration"):
        prepare_vue_serialization(
            context,
            script_security=None,
            _security_csp="off",
            javascript_policy=None,
            security_javascript="allow",
            analysis=VueSerializationAnalysis(frozenset({"events"}), frozenset()),
        )
