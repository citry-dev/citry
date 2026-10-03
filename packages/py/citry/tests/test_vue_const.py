from __future__ import annotations

import gc
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from weakref import ref

import pytest

from citry import Citry, Component, Const, Extension, Markup
from citry._vue.capture import PreparedExprNode, render_prepared_direct, typed_render_scope
from citry._vue.direct_capture import assemble_typed_render
from citry.constness import _MAX_UNROLL_ITERATIONS
from citry.nodes import ExprHtmlAttr, ForNode
from tests.test_const import _track_prepared_expression


def test_prepared_const_expression_specializes_by_equal_value(monkeypatch) -> None:
    app = Citry(autodiscover=False)
    # Const precomputing evaluates through PreparedExprNode, while a live
    # plain-JSON value runs the generated evaluator; the helper counts both.
    calls = _track_prepared_expression(monkeypatch, "value")

    class Value(Component):
        citry = app
        template = "<p>{{ value }}</p>"

        def template_data(self, kwargs, slots):
            return {"value": kwargs["value"]}

    values = (Const(1), Const(1), Const(2), 3, 4)
    output = [render_prepared_direct(Value(value=value)).serialize(deps_strategy="ignore") for value in values]

    assert [text.split(">", 1)[1].split("<", 1)[0] for text in output] == ["1", "1", "2", "3", "4"]
    # Equal Const values share one precomputed body; each live value is evaluated.
    assert calls == [(1,), (2,), (3,), (4,)]


def test_prepared_const_preserves_text_escaping_and_trusted_markup() -> None:
    app = Citry(autodiscover=False)

    class Value(Component):
        citry = app
        template = "<p>{{ value }}</p>"

        def template_data(self, kwargs, slots):
            return {"value": kwargs["value"]}

    escaped = render_prepared_direct(Value(value=Const("{{ unsafe }} <b>"))).serialize(deps_strategy="ignore")
    trusted = render_prepared_direct(Value(value=Const(Markup("<b>trusted</b>")))).serialize(deps_strategy="ignore")

    assert "{{ unsafe }} &lt;b&gt;" in escaped
    assert "<b>trusted</b>" in trusted

    assembled = assemble_typed_render(
        render_prepared_direct(Value(value=Const("{{ unsafe }} <b>"))),
        revision=0,
        tag_for_type=lambda value: "x-" + value.lower().replace("_", "-"),
    )
    templates = [value.template for value in assembled.compile_inputs.values()]
    assert all("{{ unsafe }}" not in template for template in templates)


def test_prepared_const_prunes_branches_and_unrolls_loops(monkeypatch) -> None:
    app = Citry(autodiscover=False)

    class Value(Component):
        citry = app
        template = (
            '<c-if cond="show">yes</c-if><c-else>no</c-else><c-for each="item in items"><i>{{ item }}</i></c-for>'
        )

        def template_data(self, kwargs, slots):
            return {"show": kwargs["show"], "items": kwargs["items"]}

    iterations = 0
    original = ForNode.iter_bodies

    def counted(self, context):
        nonlocal iterations
        iterations += 1
        yield from original(self, context)

    monkeypatch.setattr(ForNode, "iter_bodies", counted)
    html = "".join(
        render_prepared_direct(Value(show=Const(True), items=Const((1, 2)))).serialize(  # noqa: FBT003
            deps_strategy="ignore"
        )
        for _ in range(2)
    )

    assert "yes" in html
    assert "no" not in html
    assert html.count("<i") == 4
    assert ">1</i>" in html
    assert ">2</i>" in html
    assert iterations == 1


def test_prepared_const_structured_values_render_fresh() -> None:
    app = Citry(autodiscover=False)
    calls: list[str] = []

    class Inner(Component):
        citry = app
        template = "<i>inner</i>"

        def template_data(self, kwargs, slots):
            calls.append("inner")
            return {}

    class Holder(Component):
        citry = app
        template = "<div>{{ content }}</div>"

        def template_data(self, kwargs, slots):
            return {"content": kwargs["content"]}

    element = Inner()
    first = render_prepared_direct(Holder(content=Const(element)))
    second = render_prepared_direct(Holder(content=Const(element)))

    assert calls == ["inner", "inner"]
    assert first.frame.render_id != second.frame.render_id


def test_prepared_const_keeps_custom_value_protocol_live() -> None:
    app = Citry(autodiscover=False)
    calls = 0

    class CustomHtml:
        def __html__(self):
            nonlocal calls
            calls += 1
            return "<b>custom</b>"

    class Holder(Component):
        citry = app
        template = "<div>{{ content }}</div>"

        def template_data(self, kwargs, slots):
            return {"content": kwargs["content"]}

    value = Const(CustomHtml())
    first = render_prepared_direct(Holder(content=value)).serialize(deps_strategy="ignore")
    second = render_prepared_direct(Holder(content=value)).serialize(deps_strategy="ignore")

    assert "<b>custom</b>" in first
    assert "<b>custom</b>" in second
    assert calls == 2


def test_prepared_const_keeps_registered_exact_string_handler_live() -> None:
    # Registering str as component-like sends every str through the
    # component-like protocol, and a str has no __citry_element__, so each
    # render that dispatches live raises that AttributeError. A Const string
    # must do so too, even after an earlier render stored it as plain text.
    source = """
from citry import Citry, Component, Const
from citry._vue.capture import render_prepared_direct
from citry.component_like import ComponentLike

app = Citry(autodiscover=False)

class Value(Component):
    citry = app
    template = "{{ value }}"

    def template_data(self, kwargs, slots):
        return {"value": kwargs["value"]}

renders = (
    lambda: render_prepared_direct(Value(value=Const("custom"))).serialize(deps_strategy="ignore"),
    lambda: Value(value=Const("custom")).render().serialize(deps_strategy="ignore"),
)
assert [render() for render in renders] == ["custom", "custom"]
ComponentLike.register(str)
for render in renders * 2:
    try:
        render()
    except AttributeError as error:
        assert "__citry_element__" in str(error), error
    else:
        raise AssertionError("a Const str bypassed the registered component-like handler")
"""
    # Registration is process-wide, so it runs in its own interpreter.
    result = subprocess.run([sys.executable, "-c", source], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_prepared_const_specializes_element_key_but_keeps_attrs_hook_live(monkeypatch) -> None:
    key_calls = 0
    attr_calls: list[str] = []
    original = ExprHtmlAttr.resolve

    def counted(self, context):
        nonlocal key_calls
        key_calls += 1
        return original(self, context)

    monkeypatch.setattr(ExprHtmlAttr, "resolve", counted)

    class Probe(Extension):
        name = "probe"

        def on_attrs_resolved(self, ctx):
            attr_calls.append(ctx.tag_name)

    app = Citry(autodiscover=False, extensions=[Probe])

    class Keyed(Component):
        citry = app
        template = '<div #c-key="key">x</div>'

        def template_data(self, kwargs, slots):
            return {"key": kwargs["key"]}

    for value in ("one", "one", "two", "two"):
        render_prepared_direct(Keyed(key=Const(value)))

    assert key_calls == 2
    assert attr_calls == ["div"] * 4


def test_prepared_const_element_key_failure_stays_live(monkeypatch) -> None:
    calls = 0
    original = ExprHtmlAttr.resolve

    def counted(self, context):
        nonlocal calls
        calls += 1
        return original(self, context)

    monkeypatch.setattr(ExprHtmlAttr, "resolve", counted)
    app = Citry(autodiscover=False)

    class Keyed(Component):
        citry = app
        template = "<div #c-key=\"cfg['missing']\">x</div>"

        def template_data(self, kwargs, slots):
            return {"cfg": kwargs["cfg"]}

    for _ in range(2):
        with pytest.raises(KeyError):
            render_prepared_direct(Keyed(cfg=Const({"present": 1})))

    assert calls == 3


def test_prepared_const_keeps_attribute_hooks_and_slots_fresh() -> None:
    attr_calls: list[str] = []

    class Probe(Extension):
        name = "probe"

        def on_attrs_resolved(self, ctx):
            attr_calls.append(ctx.tag_name)

    app = Citry(autodiscover=False, extensions=[Probe])
    slot_calls: list[str] = []

    class Box(Component):
        citry = app
        template = '<section c-title="title"><c-slot /></section>'

        def template_data(self, kwargs, slots):
            return {"title": kwargs["title"]}

    def fill(_ctx):
        slot_calls.append("fill")
        return "body"

    for _ in range(2):
        render_prepared_direct(Box(title=Const("stable"), slots={"default": fill}))

    assert attr_calls == ["section", "section"]
    assert slot_calls == ["fill", "fill"]


def test_prepared_const_failed_precompute_defers_to_each_render() -> None:
    app = Citry(autodiscover=False)

    class Value(Component):
        citry = app
        template = '{{ cfg["missing"] }}'

        def template_data(self, kwargs, slots):
            return {"cfg": kwargs["cfg"]}

    for _ in range(2):
        with pytest.raises(KeyError):
            render_prepared_direct(Value(cfg=Const({"present": 1})))


def test_prepared_const_cache_is_retired_when_engine_clears(monkeypatch) -> None:
    app = Citry(autodiscover=False)
    calls = 0
    original = PreparedExprNode.evaluate

    def counted(self, variables, *, sandboxed):
        nonlocal calls
        calls += 1
        return original(self, variables, sandboxed=sandboxed)

    monkeypatch.setattr(PreparedExprNode, "evaluate", counted)

    class Value(Component):
        citry = app
        template = "{{ value }}"

        def template_data(self, kwargs, slots):
            return {"value": kwargs["value"]}

    render_prepared_direct(Value(value=Const(1)))
    render_prepared_direct(Value(value=Const(1)))
    assert len(app._const_body_cache) == 1
    app.clear()
    assert len(app._const_body_cache) == 0
    app.register(Value)
    render_prepared_direct(Value(value=Const(1)))

    assert calls == 2


def test_prepared_const_cache_does_not_retain_unregistered_class() -> None:
    app = Citry(autodiscover=False)

    class Temporary(Component):
        citry = app
        template = "{{ value }}"

        def template_data(self, kwargs, slots):
            return {"value": kwargs["value"]}

    render_prepared_direct(Temporary(value=Const(1)))
    temporary_ref = ref(Temporary)
    app.unregister(Temporary)
    del Temporary
    gc.collect()

    assert temporary_ref() is None
    assert len(app._const_body_cache) == 0


def test_prepared_const_equal_concurrent_build_runs_once(monkeypatch) -> None:
    app = Citry(autodiscover=False)
    calls = 0
    original = PreparedExprNode.evaluate

    def counted(self, variables, *, sandboxed):
        nonlocal calls
        calls += 1
        return original(self, variables, sandboxed=sandboxed)

    monkeypatch.setattr(PreparedExprNode, "evaluate", counted)

    class Value(Component):
        citry = app
        template = "{{ value }}"

        def template_data(self, kwargs, slots):
            return {"value": kwargs["value"]}

    app.initialize()

    def render() -> str:
        return render_prepared_direct(Value(value=Const(1))).serialize(deps_strategy="ignore")

    with ThreadPoolExecutor(max_workers=4) as executor:
        outputs = list(executor.map(lambda _: render(), range(8)))

    assert outputs == ["1"] * 8
    assert calls == 1


def test_prepared_const_standalone_cache_belongs_to_template_record(monkeypatch) -> None:
    app = Citry(autodiscover=False)
    calls = 0
    original = PreparedExprNode.evaluate

    def counted(self, variables, *, sandboxed):
        nonlocal calls
        calls += 1
        return original(self, variables, sandboxed=sandboxed)

    monkeypatch.setattr(PreparedExprNode, "evaluate", counted)

    def render() -> str:
        with typed_render_scope(direct=True, vue=True):
            return app.render_template("{{ value }}", {"value": Const(1)}).serialize(deps_strategy="ignore")

    assert render() == "1"
    assert render() == "1"
    assert calls == 1
    (template,) = app._standalone_template_cache.values()
    assert len(template.prepared_standalone_bodies) == 1

    app.clear()
    assert len(app._standalone_template_cache) == 0


def test_prepared_const_loop_cap_stays_dynamic_and_scope_guard_stays_live(monkeypatch) -> None:
    app = Citry(autodiscover=False)
    iterations = 0
    original = ForNode.iter_bodies

    def counted(self, context):
        nonlocal iterations
        iterations += 1
        yield from original(self, context)

    monkeypatch.setattr(ForNode, "iter_bodies", counted)

    class Value(Component):
        citry = app
        template = '<c-for each="item in items">.</c-for>'

        def template_data(self, kwargs, slots):
            return dict(kwargs)

    items = Const(range(_MAX_UNROLL_ITERATIONS + 1))
    for _ in range(2):
        html = render_prepared_direct(Value(items=items)).serialize(deps_strategy="ignore")
        assert len(html) == _MAX_UNROLL_ITERATIONS + 1
    assert iterations == 3

    with pytest.raises(RuntimeError, match="Variable shadowing"):
        render_prepared_direct(Value(items=Const((1,)), item="outer"))
