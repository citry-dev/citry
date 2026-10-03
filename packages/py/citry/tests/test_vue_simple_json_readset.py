from __future__ import annotations

import pytest

from citry import Citry, Component
from citry._vue.leaf_program import (
    PreparedLeafProgram,
    _compile_simple_json_expr,
    _SimpleJsonCodegen,
)


def _instrument_readset(monkeypatch: pytest.MonkeyPatch):
    results: list[bool] = []
    evaluate_calls: list[None] = []
    build_calls: list[None] = []
    original_build = _SimpleJsonCodegen.build

    def build(builder):
        build_calls.append(None)
        program = original_build(builder)
        original_preflight = program.readset_preflight
        original_evaluate = program.evaluate
        assert original_preflight is not None

        def preflight(context):
            admitted = original_preflight(context)
            results.append(admitted)
            return admitted

        def evaluate(*args, **kwargs):
            evaluate_calls.append(None)
            return original_evaluate(*args, **kwargs)

        object.__setattr__(program, "readset_preflight", preflight)
        object.__setattr__(program, "evaluate", evaluate)
        return program

    monkeypatch.setattr(_SimpleJsonCodegen, "build", build)
    return results, evaluate_calls, build_calls


def test_eligible_simple_json_plan_runs_automatically_and_compiles_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = Citry(autodiscover=False, extensions=[])
    template_calls = 0
    readset_results, evaluate_calls, build_calls = _instrument_readset(monkeypatch)

    class Leaf(Component):
        citry = registry
        template = "<article><span>{{ label }}</span></article>"

        def template_data(self, kwargs, slots):
            nonlocal template_calls
            template_calls += 1
            return {"label": "hello & bye"}

    first = Leaf().render().serialize(deps_strategy="ignore")
    second = Leaf().render().serialize(deps_strategy="ignore")

    assert "hello &amp; bye" in first
    assert "hello &amp; bye" in second
    assert template_calls == 2
    assert build_calls == [None]
    assert readset_results == [True, True]
    assert evaluate_calls == [None, None]


@pytest.mark.parametrize(
    "row",
    [
        {"label": "inactive branch"},
        {"label": "inactive branch", "title": {"unexpected": "mapping"}},
    ],
)
def test_readset_falls_back_before_inactive_branch_values_are_accessed(
    monkeypatch: pytest.MonkeyPatch,
    row: dict[str, object],
) -> None:
    registry = Citry(autodiscover=False, extensions=[])
    template_calls = 0
    readset_results, evaluate_calls, _build_calls = _instrument_readset(monkeypatch)

    class Leaf(Component):
        citry = registry
        template = "<c-if cond=\"show\">{{ row['title'] }} {{ row['label'] }}</c-if><c-else>closed</c-else>"

        def template_data(self, kwargs, slots):
            nonlocal template_calls
            template_calls += 1
            return {"show": [], "row": row}

    rendered = Leaf().render()
    assert isinstance(rendered.parts[0], PreparedLeafProgram)
    assert readset_results == [False]
    assert evaluate_calls == []
    assert template_calls == 1
    html = rendered.serialize(deps_strategy="ignore")
    assert "closed" in html
    assert "inactive branch" not in html


def test_non_plain_text_value_falls_back_without_duplicate_stringification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = Citry(autodiscover=False, extensions=[])
    stringify_calls = 0
    readset_results, evaluate_calls, _build_calls = _instrument_readset(monkeypatch)

    class SideEffectValue:
        def __str__(self) -> str:
            nonlocal stringify_calls
            stringify_calls += 1
            return f"value-{stringify_calls}"

    class Leaf(Component):
        citry = registry
        template = "<p>{{ title }}</p>"

        def template_data(self, kwargs, slots):
            return {"title": SideEffectValue()}

    rendered = Leaf().render()
    assert isinstance(rendered.parts[0], PreparedLeafProgram)
    assert readset_results == [False]
    assert evaluate_calls == []
    assert stringify_calls == 1

    html = rendered.serialize(deps_strategy="ignore")
    assert "value-1" in html
    assert stringify_calls == 1


def test_attribute_hooks_skip_generated_preflight_for_dynamic_openings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = Citry(autodiscover=False, extensions=[])
    readset_results, evaluate_calls, build_calls = _instrument_readset(monkeypatch)

    class Leaf(Component):
        citry = registry
        template = '<p c-title="title">body</p>'

        def template_data(self, kwargs, slots):
            return {"title": "ready"}

    rendered = Leaf().render()
    assert isinstance(rendered.parts[0], PreparedLeafProgram)
    assert build_calls == [None]
    assert readset_results == []
    assert evaluate_calls == []
    assert 'title="ready"' in rendered.serialize(deps_strategy="ignore")


def test_readset_loop_target_shadow_falls_back_before_generated_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = Citry(autodiscover=False, extensions=[])
    template_calls = 0
    readset_results, evaluate_calls, _build_calls = _instrument_readset(monkeypatch)

    class Leaf(Component):
        citry = registry
        template = '<p c-for="item in items">{{ item }}</p>'

        def template_data(self, kwargs, slots):
            nonlocal template_calls
            template_calls += 1
            return {"items": ["loop value"], "item": "root value"}

    with pytest.raises(RuntimeError, match="variable name is already taken"):
        Leaf().render()
    assert readset_results == [False]
    assert evaluate_calls == []
    assert template_calls == 1


def test_readset_never_executes_a_callable_c_bind_expression_during_admission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = Citry(autodiscover=False, extensions=[])
    template_calls = 0
    attrs_calls = 0
    readset_results, evaluate_calls, build_calls = _instrument_readset(monkeypatch)

    def attrs():
        nonlocal attrs_calls
        attrs_calls += 1
        return {"data-call": "once"}

    class Leaf(Component):
        citry = registry
        template = '<article c-bind="attrs()"><span c-title="title">body</span></article>'

        def template_data(self, kwargs, slots):
            nonlocal template_calls
            template_calls += 1
            return {"attrs": attrs, "title": "safe"}

    rendered = Leaf().render()
    assert isinstance(rendered.parts[0], PreparedLeafProgram)
    assert attrs_calls == 1
    assert template_calls == 1
    assert build_calls == []
    assert readset_results == []
    assert evaluate_calls == []
    assert 'data-call="once"' in rendered.serialize(deps_strategy="ignore")


@pytest.mark.parametrize(
    ("source", "used_vars"),
    [
        ("_private", ("_private",)),
        ("forloop", ("forloop",)),
        ("1", ()),
        ("row['_secret']", ("row",)),
        ("row[0]", ("row",)),
        ("'text'['key']", ()),
        ("a if 'yes' else b", ("a", "b")),
        ("a if b else c + d", ("a", "b", "c", "d")),
        ("row +", ("row",)),
        ("row['key']", ()),
        (b"row", ("row",)),
        ("row", ["row"]),
    ],
)
def test_expressions_outside_the_plain_json_subset_are_not_compiled(source, used_vars):
    # Each refusal sends the template back to the ordinary Python evaluator,
    # so a wrong admission here would change what the page renders.
    assert _compile_simple_json_expr(source, used_vars) is None


def test_plain_json_paths_and_conditions_are_compiled():
    expression = _compile_simple_json_expr("row['a']['b'] if flag else 'none'", ("row", "flag"))

    assert expression is not None
    assert expression.kind == "if"
