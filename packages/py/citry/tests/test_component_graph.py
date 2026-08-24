"""Tests for the static graph of authored component-template dependencies."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path
from textwrap import dedent
from threading import Event

import pytest

from citry import (
    Citry,
    Component,
    ComponentGraph,
    ComponentGraphLocation,
    ComponentGraphNode,
    ComponentGraphReference,
    Extension,
    ForeignSpan,
    ForeignSpanSet,
    LspPosition,
    LspRange,
    NotRegistered,
)


def test_direct_references_preserve_occurrences_and_queries_deduplicate_targets():
    app = Citry(autodiscover=False)

    class Button(Component):
        citry = app
        template = """
          <button></button>
        """

    class Page(Component):
        citry = app
        template = """
          <p>ž</p>
          <c-BUTTON />
          <div c-body="<><c-button /><c-button /></>"></div>
        """

    graph = app.inspect_component_graph()

    page = graph.component("PAGE")
    button = graph.component("button")
    assert graph.component(page) is page
    assert graph.dependencies(page) == (button,)
    assert graph.dependents(button) == (page,)
    assert len(graph.references_from(page)) == 3
    assert graph.references_to(button) == graph.references_from(page)
    assert [reference.authored_name for reference in graph.references_from(page)] == [
        "BUTTON",
        "button",
        "button",
    ]
    normalized_source = dedent(Page.template)
    for reference in graph.references_from(page):
        start = reference.location.start_index
        end = reference.location.end_index
        assert normalized_source.encode()[start:end].decode().casefold() in {"c-button", "button"}
        assert reference.location.source_range.start.line >= 1
    # The nested reference comes after a non-ASCII character. Its byte and
    # UTF-16 positions therefore use different units but point at one token.
    nested = graph.references_from(page)[1]
    prefix = normalized_source.encode()[: nested.location.start_index].decode()
    assert nested.location.start_index > len(prefix)
    assert nested.location.source_range.start.character >= 0


def test_unresolved_names_and_dynamic_selectors_are_explicit():
    app = Citry(autodiscover=False)

    class Card(Component):
        citry = app
        template = """
          card
        """

    class Page(Component):
        citry = app
        template = """
          <c-missing />
          <c-component c-is="choice" />
          <c-component is="card" />
          <c-component is="card" c-bind="attrs" />
        """

    graph = app.inspect_component_graph()

    assert graph.coverage_complete is True
    assert graph.fully_resolved is False
    assert graph.dependencies("page") == (graph.component("card"),)
    assert [(item.reason, item.authored_name, item.syntax) for item in graph.unresolved_from("page")] == [
        ("unknown-component", "missing", "tag"),
        ("dynamic-target", None, "dynamic-selector"),
        ("dynamic-target", None, "dynamic-selector"),
    ]
    assert graph.unresolved_from() == graph.unresolved


def test_aliases_and_static_selectors_resolve_to_the_canonical_node():
    app = Citry(autodiscover=False)

    class ProductCard(Component):
        citry = app
        template = "card"

    app.register(ProductCard, "legacy-card")

    class Page(Component):
        citry = app
        template = """
          <c-LEGACY-CARD />
          <c-component is=PRODUCTCARD />
        """

    graph = app.inspect_component_graph()
    card = graph.component("legacy-card")

    assert card is graph.component("PRODUCTCARD")
    assert card.name == "product-card"
    assert card.aliases == ("legacy-card", "productcard")
    assert graph.dependencies("page") == (card,)
    assert [(item.registered_name, item.authored_name, item.syntax) for item in graph.references_from("page")] == [
        ("legacy-card", "LEGACY-CARD", "tag"),
        ("productcard", "PRODUCTCARD", "static-selector"),
    ]


@pytest.mark.parametrize(
    "source",
    [
        "<c-component />",
        "<c-component is />",
        '<c-component is="" />',
        '<c-component is="card" c-is="choice" />',
    ],
)
def test_invalid_dynamic_selector_forms_are_source_problems(source: str):
    app = Citry(autodiscover=False)

    class Broken(Component):
        citry = app
        template = source

    graph = app.inspect_component_graph()

    assert graph.references == ()
    assert graph.unresolved == ()
    assert [problem.code for problem in graph.problems] == ["template-syntax"]


def test_structural_and_html_targets_are_not_dependencies_and_builtins_are_optional():
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = """
          <c-if cond="True">
            <c-element is="section" />
            <c-provide key="theme" mode="dark"></c-provide>
          </c-if>
        """

    default_graph = app.inspect_component_graph()
    complete_graph = app.inspect_component_graph(include_builtins=True)

    assert default_graph.dependencies("page") == ()
    assert "provide" not in {node.name for node in default_graph.nodes}
    assert complete_graph.dependencies("page") == (complete_graph.component("provide"),)


def test_registered_name_beginning_with_component_prefix_resolves_once():
    app = Citry(autodiscover=False)

    class Prefixed(Component):
        citry = app
        name = "c-foo"
        template = """
          target
        """

    class Page(Component):
        citry = app
        template = """
          <c-c-foo />
        """

    graph = app.inspect_component_graph()
    reference = graph.references_from("page")[0]

    assert graph.dependencies("page") == (graph.component("c-foo"),)
    assert reference.authored_name == "c-foo"
    assert reference.registered_name == "c-foo"


def test_inherited_file_template_is_projected_onto_each_registered_consumer(tmp_path: Path):
    source_path = tmp_path / "shared.html"
    source_path.write_text("<c-leaf />\n", encoding="utf-8")
    app = Citry(autodiscover=False)

    class Leaf(Component):
        citry = app
        template = """
          leaf
        """

    class Base(Component):
        citry = app
        template_file = source_path

    class First(Base):
        pass

    class Second(Base):
        pass

    graph = app.inspect_component_graph()

    for component in ("base", "first", "second"):
        reference = graph.references_from(component)[0]
        assert graph.dependencies(component) == (graph.component("leaf"),)
        assert reference.location.template_file == source_path
        expected_owner = (
            f"{__name__}.test_inherited_file_template_is_projected_onto_each_registered_consumer.<locals>.Base"
        )
        assert reference.location.declared_on == expected_owner
        assert source_path.read_bytes()[reference.location.start_index : reference.location.end_index] == b"c-leaf"
    assert app._file_index == {}


def test_source_problems_do_not_discard_the_rest_of_the_graph(tmp_path: Path):
    app = Citry(autodiscover=False)

    class Leaf(Component):
        citry = app
        template = """
          leaf
        """

    class Good(Component):
        citry = app
        template = """
          <c-leaf />
        """

    class Broken(Component):
        citry = app
        template = """
          <c-if>
        """

    class Missing(Component):
        citry = app
        template_file = tmp_path / "missing.html"

    class Unreadable(Component):
        citry = app
        template_file = tmp_path

    class Unsupported(Component):
        citry = app
        template = "unsupported"
        template_lang = "js"

    class TemplateLess(Component):
        citry = app
        template = None

    graph = app.inspect_component_graph()

    assert graph.coverage_complete is False
    assert graph.fully_resolved is False
    assert graph.dependencies("good") == (graph.component("leaf"),)
    assert graph.dependencies("template-less") == ()
    assert {problem.code for problem in graph.problems} == {
        "template-file-not-found",
        "template-file-unreadable",
        "template-language-unsupported",
        "template-syntax",
    }
    assert all(problem.component_definition_ids for problem in graph.problems)


def test_invalid_inline_unicode_becomes_a_source_problem():
    app = Citry(autodiscover=False)

    class Broken(Component):
        citry = app
        template = "\ud800"

    graph = app.inspect_component_graph()

    assert graph.coverage_complete is False
    assert [problem.code for problem in graph.problems] == ["template-value-invalid"]


def test_astral_source_position_uses_utf8_bytes_and_utf16_editor_units():
    app = Citry(autodiscover=False)

    class Button(Component):
        citry = app
        template = "button"

    class Page(Component):
        citry = app
        template = "😀<c-button />"

    location = app.inspect_component_graph().references_from("page")[0].location

    assert location.start_index == 5
    assert location.source_range.start == LspPosition(0, 3)


def test_template_attribute_parse_failure_is_reported_at_the_root_source_range():
    app = Citry(autodiscover=False)

    class Broken(Component):
        citry = app
        template = """
          <p>ž</p>
          <div c-body="<><c-if></>"></div>
        """

    graph = app.inspect_component_graph()
    problem = graph.problems[0]

    assert problem.code == "template-syntax"
    assert problem.location is not None
    source = dedent(Broken.template)
    fragment = source.encode()[problem.location.start_index : problem.location.end_index].decode()
    assert fragment == "<c-if>"
    assert problem.location.source_range.start.line == 2


def test_provider_controlled_body_marks_graph_coverage_as_partial():
    class Host(Extension):
        name = "host"

        def on_template_foreign_spans(self, ctx):
            token = b"[[<c-hidden />]]"
            start = ctx.content.encode().find(token)
            if start < 0:
                return None
            return ForeignSpanSet((ForeignSpan(start, start + len(token), may_control_body=True),))

        def on_template_foreign_compiled(self, ctx):
            ctx.nodes.clear()
            ctx.mark_resolved(*ctx.claims)

    app = Citry(extensions=[Host], autodiscover=False)

    class Page(Component):
        citry = app
        template = "[[<c-hidden />]]"

    graph = app.inspect_component_graph()

    assert graph.dependencies("page") == ()
    assert graph.unresolved == ()
    assert graph.coverage_complete is False
    assert [problem.code for problem in graph.problems] == ["foreign-source-controls-body"]


@pytest.mark.parametrize(("start", "end"), [(1, 2), (999, 1000)])
def test_invalid_provider_span_becomes_a_namespace_problem(start: int, end: int):
    class Host(Extension):
        name = "host"

        def on_template_foreign_spans(self, ctx):
            return ForeignSpanSet((ForeignSpan(start, end, may_control_body=True),))

        def on_template_foreign_compiled(self, ctx):
            ctx.mark_resolved(*ctx.claims)

    app = Citry(extensions=[Host], autodiscover=False)

    class Page(Component):
        citry = app
        template = "ž<c-hidden />"

    graph = app.inspect_component_graph()

    assert graph.references == ()
    assert graph.unresolved == ()
    assert graph.problems[0].code == "template-namespace-unavailable"
    assert graph.problems[0].location is None


def test_shared_source_provider_disagreement_becomes_one_namespace_problem():
    class Host(Extension):
        name = "host"

        def on_template_foreign_spans(self, ctx):
            if ctx.component_class.__name__ == "Base":
                return None
            return ForeignSpanSet((ForeignSpan(0, 1),))

        def on_template_foreign_compiled(self, ctx):
            ctx.mark_resolved(*ctx.claims)

    app = Citry(extensions=[Host], autodiscover=False)

    class Base(Component):
        citry = app
        template = "plain"

    class Child(Base):
        pass

    graph = app.inspect_component_graph()
    problem = graph.problems[0]

    assert problem.code == "template-namespace-unavailable"
    assert problem.component_definition_ids == tuple(sorted((Base.definition_id, Child.definition_id)))


def test_cycles_and_self_references_are_valid_direct_dependencies():
    app = Citry(autodiscover=False)

    class Alpha(Component):
        citry = app
        template = """
          <c-alpha />
          <c-beta />
        """

    class Beta(Component):
        citry = app
        template = """
          <c-alpha />
        """

    graph = app.inspect_component_graph()

    assert graph.dependencies("alpha") == (graph.component("alpha"), graph.component("beta"))
    assert graph.dependents("alpha") == (graph.component("alpha"), graph.component("beta"))
    assert graph.coverage_complete is True
    assert graph.fully_resolved is True


def test_graph_build_does_not_load_transform_cache_or_render_templates():
    loaded: list[type[Component]] = []

    class LoadProbe(Extension):
        name = "load_probe"

        def on_template_loaded(self, ctx):
            loaded.append(ctx.component_class)
            return ctx.template

    app = Citry(extensions=[LoadProbe], autodiscover=False)

    class Leaf(Component):
        citry = app
        template = """
          leaf
        """

    class Page(Component):
        citry = app
        template = """
          <c-leaf />
        """

    graph = app.inspect_component_graph()

    assert graph.dependencies("page") == (graph.component("leaf"),)
    assert loaded == []
    assert "_citry_template" not in Page.__dict__
    assert "_citry_template" not in Leaf.__dict__


def test_graph_serialization_is_versioned_deterministic_and_json_ready():
    app = Citry(autodiscover=False)

    class Leaf(Component):
        citry = app
        template = """
          leaf
        """

    class Page(Component):
        citry = app
        template = """
          <c-leaf />
        """

    graph = app.inspect_component_graph()
    document = graph.to_dict()

    assert document["schema_version"] == 1
    assert json.loads(graph.to_json()) == document
    assert graph.to_json() == graph.to_json()
    assert [node["name"] for node in document["nodes"]] == ["leaf", "page"]
    assert document["references"][0]["authored_name"] == "leaf"


def test_graph_queries_reject_a_component_from_another_graph():
    first = Citry(autodiscover=False)
    second = Citry(autodiscover=False)

    class First(Component):
        citry = first
        template = """
          first
        """

    class Second(Component):
        citry = second
        template = """
          second
        """

    first_graph = first.inspect_component_graph()
    second_graph = second.inspect_component_graph()

    with pytest.raises(NotRegistered):
        first_graph.component("missing")
    with pytest.raises(NotRegistered):
        first_graph.component(second_graph.component("second"))


def test_graph_uses_one_registry_snapshot_while_registration_changes(monkeypatch):
    app = Citry(autodiscover=False)

    class Original(Component):
        citry = app
        template = "original"

    app.register(Original, "old-alias")
    citry_module = import_module("citry.citry")
    original_builder = citry_module._build_component_graph
    snapshot_copied = Event()
    continue_build = Event()

    def paused_builder(engine, registrations, *, include_builtins):
        snapshot_copied.set()
        assert continue_build.wait(timeout=5)
        return original_builder(engine, registrations, include_builtins=include_builtins)

    monkeypatch.setattr(citry_module, "_build_component_graph", paused_builder)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(app.inspect_component_graph)
        assert snapshot_copied.wait(timeout=5)
        app.unregister("old-alias")

        class Replacement(Component):
            citry = app
            template = "replacement"

        app.register(Replacement, "old-alias")
        continue_build.set()
        graph = pending.result(timeout=5)

    assert graph.component("old-alias").definition_id == Original.definition_id
    with pytest.raises(NotRegistered):
        graph.component("replacement")


def test_public_value_records_validate_their_basic_contracts():
    node = ComponentGraphNode(
        class_id="Leaf_123",
        engine_id="eng_123",
        definition_id="def_123",
        name="leaf",
        aliases=(),
        builtin=False,
    )
    location = ComponentGraphLocation(
        origin="example.py::Page.template",
        source_kind="inline",
        declared_on="example.Page",
        declaration_file=Path(__file__).resolve(),
        template_file=None,
        start_index=0,
        end_index=6,
        source_range=LspRange(LspPosition(0, 0), LspPosition(0, 6)),
    )
    graph = ComponentGraph(
        schema_version=1,
        citry_version="0.0.0",
        engine_id="eng_123",
        nodes=(node,),
        references=(),
        unresolved=(),
        problems=(),
    )

    assert graph.component("leaf") == node
    target = ComponentGraphNode(
        class_id="Target_123",
        engine_id="eng_123",
        definition_id="def_456",
        name="target",
        aliases=(),
        builtin=False,
    )
    contradictory = ComponentGraphReference(
        source_definition_id=node.definition_id,
        target_definition_id=target.definition_id,
        registered_name="leaf",
        authored_name="leaf",
        syntax="tag",
        location=location,
    )
    with pytest.raises(ValueError, match="registration of its target"):
        ComponentGraph(
            schema_version=1,
            citry_version="0.0.0",
            engine_id="eng_123",
            nodes=(node, target),
            references=(contradictory,),
            unresolved=(),
            problems=(),
        )

    reference_z = ComponentGraphReference(
        source_definition_id=node.definition_id,
        target_definition_id=target.definition_id,
        registered_name="target",
        authored_name="z",
        syntax="tag",
        location=location,
    )
    reference_a = ComponentGraphReference(
        source_definition_id=node.definition_id,
        target_definition_id=target.definition_id,
        registered_name="target",
        authored_name="a",
        syntax="tag",
        location=location,
    )
    with pytest.raises(ValueError, match="canonical order"):
        ComponentGraph(
            schema_version=1,
            citry_version="0.0.0",
            engine_id="eng_123",
            nodes=(node, target),
            references=(reference_z, reference_a),
            unresolved=(),
            problems=(),
        )

    with pytest.raises(ValueError, match="aliases"):
        ComponentGraphNode(
            class_id="Leaf_123",
            engine_id="eng_123",
            definition_id="def_123",
            name="leaf",
            aliases=("leaf",),
            builtin=False,
        )
    with pytest.raises(ValueError, match="template_file"):
        ComponentGraphLocation(
            origin=location.origin,
            source_kind="inline",
            declared_on=location.declared_on,
            declaration_file=location.declaration_file,
            template_file=Path(__file__).resolve(),
            start_index=0,
            end_index=1,
            source_range=LspRange(LspPosition(0, 0), LspPosition(0, 1)),
        )
