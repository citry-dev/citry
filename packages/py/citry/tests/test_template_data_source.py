"""Tests for conservative ``template_data()`` source-shape inference."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent, indent

from citry.analysis import (
    analyze_css_data_source,
    analyze_template_data_source,
    python_class_asset_resolution_signature,
    python_class_defines_direct_method,
    python_class_direct_method_first_line,
    python_class_resolution_signature,
    python_class_static_asset_matches,
)


def _css_shape(body: str):
    source = "class Card:\n    def css_data(self, kwargs, slots):\n" + indent(dedent(body), "        ")
    result = analyze_css_data_source(source, "Card")
    assert result is not None
    return source, result


def _shape(body: str, *, kwargs_fields: tuple[str, ...] | None = ()):
    source = "class Card:\n    def template_data(self, kwargs):\n" + indent(dedent(body), "        ")
    result = analyze_template_data_source(source, "Card", kwargs_fields=kwargs_fields)
    assert result is not None
    return source, result


def test_direct_literal_reports_exact_utf16_key_and_value_ranges():
    source = 'class Card:\n    def template_data(self, kwargs):\n        prefix = "😀"; return {"title": value}\n'

    shape = analyze_template_data_source(source, "Card", kwargs_fields=())

    assert shape is not None
    assert shape.completeness == "closed"
    assert [(root.name, root.presence) for root in shape.roots] == [("title", "always")]
    definition = shape.roots[0].definitions[0]
    assert definition.key_range.start.line == 2
    assert definition.key_range.start.character == len('        prefix = "😀"; return {'.encode("utf-16-le")) // 2
    assert definition.value_range is not None
    assert definition.value_range.end.character - definition.value_range.start.character == len("value")


def test_duplicate_literal_and_subscript_writes_keep_only_the_last_definition():
    source, shape = _shape(
        """
        data = {"item": first, "item": second}
        data["item"] = third
        return data
        """,
    )

    root = shape.roots[0]
    assert root.name == "item"
    assert len(root.definitions) == 1
    assert root.definitions[0].key_range.start.line == 4
    assert source.splitlines()[4][root.definitions[0].key_range.start.character :].startswith('"item"')


def test_alias_mutation_known_unpack_and_union_follow_mapping_identity():
    _source, shape = _shape(
        """
        base = {"first": one}
        alias = base
        alias["second"] = two
        result = {**base, "third": three}
        result |= {"fourth": four}
        return result
        """,
    )

    assert [root.name for root in shape.roots] == ["first", "fourth", "second", "third"]
    assert shape.completeness == "closed"


def test_unknown_unpack_opens_shape_and_invalidates_only_preceding_value_definition():
    _source, shape = _shape(
        """
        return {"before": first, **unknown, "after": second}
        """,
    )

    roots = {root.name: root for root in shape.roots}
    assert shape.completeness == "open"
    assert roots["before"].presence == "always"
    assert roots["before"].definitions == ()
    assert len(roots["after"].definitions) == 1


def test_branches_join_always_and_conditional_roots_with_all_definitions():
    _source, shape = _shape(
        """
        if condition:
            return {"shared": one, "left": value}
        return {"shared": two, "right": value}
        """,
    )

    roots = {root.name: root for root in shape.roots}
    assert roots["shared"].presence == "always"
    assert len(roots["shared"].definitions) == 2
    assert roots["left"].presence == "conditional"
    assert roots["right"].presence == "conditional"


def test_returned_formal_parameter_uses_only_proven_kwargs_fields():
    _source, known = _shape("return kwargs\n", kwargs_fields=("title", "count"))
    _source, unknown = _shape("return kwargs\n", kwargs_fields=None)

    assert [(root.name, root.origins) for root in known.roots] == [
        ("count", frozenset({"kwargs"})),
        ("title", frozenset({"kwargs"})),
    ]
    assert known.completeness == "closed"
    assert unknown.roots == ()
    assert unknown.completeness == "open"


def test_unsupported_escape_withholds_roots_but_a_later_fresh_literal_recovers():
    _source, escaped = _shape(
        """
        data = {"unsafe": value}
        consume(data)
        return data
        """,
    )
    _source, fresh = _shape(
        """
        data = {"unsafe": value}
        consume(data)
        return {"safe": value}
        """,
    )

    assert escaped.roots == ()
    assert escaped.completeness == "open"
    assert [root.name for root in fresh.roots] == ["safe"]
    assert fresh.completeness == "closed"


def test_non_identical_python_identifier_keys_and_invalid_source_are_withheld():
    _source, shape = _shape(
        """
        return {"valid": one, "\\N{KELVIN SIGN}": two, "café": three, "not-valid": four}
        """,
    )

    assert [root.name for root in shape.roots] == ["valid"]
    assert shape.completeness == "open"
    assert analyze_template_data_source("class Card(:", "Card", kwargs_fields=()) is None


def test_css_data_accepts_exact_runtime_suffixes_without_treating_kwargs_as_data():
    source, shape = _css_shape(
        """
        data = {"chart_height": height, "row-color": color, "café": accent}
        data["conditional"] = kwargs.get("value")
        return data
        """,
    )

    assert [root.name for root in shape.roots] == ["café", "chart_height", "conditional", "row-color"]
    assert shape.completeness == "closed"
    row_color = next(root for root in shape.roots if root.name == "row-color")
    start = row_color.definitions[0].key_range.start
    assert source.splitlines()[start.line][start.character :].startswith('"row-color"')

    _source, kwargs_shape = _css_shape("return kwargs\n")
    assert kwargs_shape.roots == ()
    assert kwargs_shape.completeness == "open"


def test_css_data_rejects_invalid_suffixes_and_tracks_conditional_returns():
    _source, shape = _css_shape(
        """
        if compact:
            return {"accent": color, "bad key": value}
        return {"accent": color, "wide-only": width}
        """,
    )

    roots = {root.name: root for root in shape.roots}
    assert roots["accent"].presence == "always"
    assert roots["wide-only"].presence == "conditional"
    assert "bad key" not in roots
    assert shape.completeness == "open"


def test_owner_and_direct_method_resolution_decline_ambiguity_and_decorators():
    valid = "class Outer:\n    class Card:\n        def template_data(self, kwargs):\n            return {}\n"
    decorated = "@decorate\nclass Card:\n    def template_data(self, kwargs):\n        return {}\n"
    duplicate = "class Card:\n    pass\nclass Card:\n    pass\n"
    replaced = (
        "class Card:\n"
        "    def template_data(self, kwargs):\n"
        "        return {'stale': 1}\n"
        "    template_data = descriptor\n"
    )

    assert python_class_defines_direct_method(valid, "Outer.Card", "template_data") is True
    assert python_class_direct_method_first_line(valid, "Outer.Card", "template_data") == 3
    assert analyze_template_data_source(valid, "Outer.Card", kwargs_fields=()) is not None
    assert python_class_defines_direct_method(decorated, "Card", "template_data") is None
    assert python_class_defines_direct_method(duplicate, "Card", "template_data") is None
    assert python_class_defines_direct_method(replaced, "Card", "template_data") is None
    assert analyze_template_data_source(replaced, "Card", kwargs_fields=()) is None


def test_raise_terminates_flow_and_nested_call_side_effects_taint_a_mapping():
    _source, raised = _shape(
        """
        raise RuntimeError
        return {"unreachable": value}
        """,
    )
    _source, mutated = _shape(
        """
        data = {"before": value}
        data["after"] = consume(data)
        return data
        """,
    )

    assert raised.roots == ()
    assert raised.completeness == "open"
    assert mutated.roots == ()
    assert mutated.completeness == "open"


def test_only_a_pristine_kwargs_carrier_or_simple_alias_exposes_schema_fields():
    _source, pristine_alias = _shape(
        """
        data = kwargs
        return data
        """,
        kwargs_fields=("title", "count"),
    )
    _source, cleared = _shape(
        """
        kwargs.clear()
        return kwargs
        """,
        kwargs_fields=("title", "count"),
    )
    _source, popped = _shape(
        """
        kwargs.pop("title")
        return kwargs
        """,
        kwargs_fields=("title", "count"),
    )
    _source, escaped = _shape(
        """
        mutate(kwargs)
        return kwargs
        """,
        kwargs_fields=("title", "count"),
    )
    _source, assigned = _shape(
        """
        kwargs["title"] = 42
        return kwargs
        """,
        kwargs_fields=("title", "count"),
    )
    _source, unpacked_after_clear = _shape(
        """
        kwargs.clear()
        return {**kwargs}
        """,
        kwargs_fields=("title", "count"),
    )
    _source, authored_method = _shape(
        """
        kwargs.update(extra=1)
        return kwargs
        """,
        kwargs_fields=("title",),
    )

    assert [root.name for root in pristine_alias.roots] == ["count", "title"]
    for shape in (cleared, popped, escaped, assigned, authored_method):
        assert shape.roots == ()
        assert shape.completeness == "open"
    assert unpacked_after_clear.roots == ()
    assert unpacked_after_clear.completeness == "open"


def test_resolution_signature_covers_bindings_but_ignores_live_method_and_template_edits():
    source = (
        "Selected = Base\n"
        "class Card(Selected):\n"
        "    template = '{{ old }}'\n"
        "    def template_data(self, kwargs):\n"
        "        return {'old': 1}\n"
    )
    signature = python_class_resolution_signature(source, "Card")
    imported = "from first import Base\nclass ImportedCard(Base):\n    pass\n"
    imported_signature = python_class_resolution_signature(imported, "ImportedCard")

    assert signature is not None
    assert (
        python_class_resolution_signature(source.replace("Selected = Base", "Selected = Other"), "Card") != signature
    )
    assert (
        python_class_resolution_signature(
            imported.replace("from first import Base", "from second import Other as Base"),
            "ImportedCard",
        )
        != imported_signature
    )
    live_edits = source.replace("{{ old }}", "{{ new }}").replace("{'old': 1}", "{'new': 1}")
    assert python_class_resolution_signature(live_edits, "Card") == signature

    selected_source = (
        "class Base:\n"
        "    def template_data(self, kwargs):\n"
        "        return {'old': 1}\n"
        "class Other:\n"
        "    pass\n"
        "class Config:\n"
        "    template = 'base'\n"
        "Selected = Base if Config.template == 'base' else Other\n"
        "class SelectedCard(Selected):\n"
        "    pass\n"
    )
    selected_signature = python_class_resolution_signature(selected_source, "SelectedCard")
    assert selected_signature is not None
    assert (
        python_class_resolution_signature(
            selected_source.replace("template = 'base'", "template = 'other'"),
            "SelectedCard",
        )
        != selected_signature
    )


def test_asset_resolution_signature_is_consumer_specific_and_ignores_interfaces():
    source = (
        "from citry import Component\n"
        "class Base(Component):\n"
        "    template_file = 'shared.html'\n"
        "    class TemplateData:\n"
        "        value: str\n"
        "class Child(Base):\n"
        "    pass\n"
        "class Current(Component):\n"
        "    template = '{{ value }}'\n"
    )
    signatures = {name: python_class_asset_resolution_signature(source, name) for name in ("Base", "Child", "Current")}
    child_moved = source.replace("class Child(Base):", "class Child(Component):")
    base_moved = source.replace("'shared.html'", "'other.html'")
    schema_edited = source.replace("value: str", "value: int")
    inline_edited = source.replace("{{ value }}", "{{ value.upper() }}")
    unrelated_assets_edited = source.replace(
        "    class TemplateData:\n",
        "    js = 'console.log(1)'\n    css = '.card {}'\n    def helper(self): return 1\n    class TemplateData:\n",
    )
    current_method_added = source.replace(
        "    template = '{{ value }}'\n",
        "    template = '{{ value }}'\n    def helper(self): return 1\n",
    )

    assert python_class_asset_resolution_signature(child_moved, "Child") != signatures["Child"]
    assert python_class_asset_resolution_signature(child_moved, "Base") == signatures["Base"]
    assert python_class_asset_resolution_signature(child_moved, "Current") == signatures["Current"]
    assert python_class_asset_resolution_signature(base_moved, "Base") != signatures["Base"]
    assert python_class_asset_resolution_signature(base_moved, "Child") != signatures["Child"]
    assert python_class_asset_resolution_signature(base_moved, "Current") == signatures["Current"]
    for name, signature in signatures.items():
        assert python_class_asset_resolution_signature(schema_edited, name) == signature
        assert python_class_asset_resolution_signature(inline_edited, name) == signature
        assert python_class_asset_resolution_signature(unrelated_assets_edited, name) == signature
        assert python_class_asset_resolution_signature(current_method_added, name) == signature


def test_asset_resolution_signature_tracks_dynamic_selector_dependencies():
    source = (
        "from citry import Component\n"
        "class Config:\n"
        "    template = 'base'\n"
        "class Base(Component):\n"
        "    template_file = 'base.html'\n"
        "class Other(Component):\n"
        "    template_file = 'other.html'\n"
        "Selected = Base if Config.template == 'base' else Other\n"
        "class Card(Selected):\n"
        "    pass\n"
    )
    signature = python_class_asset_resolution_signature(source, "Card")

    assert signature is not None
    assert (
        python_class_asset_resolution_signature(
            source.replace("template = 'base'", "template = 'other'"),
            "Card",
        )
        != signature
    )


def test_asset_resolution_signature_declines_dynamic_class_namespace_mutation():
    bodies = (
        "    exec(\"template_file = 'card.html'\")\n",
        "    locals().update(template_file='card.html')\n",
        "    vars()['template_file'] = 'card.html'\n",
        "    def __init_subclass__(cls): pass\n",
    )
    for body in bodies:
        source = "class Card:\n" + body
        assert python_class_asset_resolution_signature(source, "Card") is None

    decorated = "@decorate\nclass Card:\n    template_file = 'card.html'\n"
    custom_metaclass = "class Card(metaclass=Meta):\n    template_file = 'card.html'\n"
    assert python_class_asset_resolution_signature(decorated, "Card") is None
    assert python_class_asset_resolution_signature(custom_metaclass, "Card") is None


def test_static_asset_proof_accepts_literals_and_pathlib_path():
    inline = "class Card:\n    template = '<main></main>'\n"
    path = "from pathlib import Path\nclass Card:\n    template_file = Path('card.html')\n"
    qualified = "import pathlib as pl\nclass Card:\n    template_file = pl.Path('card.html')\n"

    assert python_class_static_asset_matches(inline, "Card", "<main></main>", None)
    assert not python_class_static_asset_matches(inline, "Card", "<aside></aside>", None)
    assert python_class_static_asset_matches(path, "Card", None, Path("card.html"))
    assert python_class_static_asset_matches(qualified, "Card", None, Path("card.html"))


def test_css_asset_proof_tracks_ownership_but_ignores_authored_css_edits():
    inline = "class Card:\n    css = '.card { color: red; }'\n"
    edited = inline.replace("red", "blue")
    moved = "class Card:\n    css_file = 'other.css'\n"

    assert python_class_static_asset_matches(inline, "Card", ".card { color: red; }", None, "css")
    assert python_class_asset_resolution_signature(inline, "Card", "css") == python_class_asset_resolution_signature(
        edited,
        "Card",
        "css",
    )
    assert python_class_asset_resolution_signature(inline, "Card", "css") != python_class_asset_resolution_signature(
        moved,
        "Card",
        "css",
    )


def test_asset_resolution_declines_unproven_or_runtime_mutated_bindings():
    imported = "from settings import CARD_TEMPLATE\nclass Card:\n    template_file = CARD_TEMPLATE\n"
    post_class_mutation = (
        "class Card:\n    template_file = 'card.html'\nAlias = Card\nAlias.template_file = 'card.html'\n"
    )
    helper_mutation = (
        "class Card:\n    template_file = 'card.html'\ndef mutate():\n    Card.template_file = 'card.html'\nmutate()\n"
    )
    shadowed_path = "from pathlib import Path\nPath = factory\nclass Card:\n    template_file = Path('card.html')\n"

    assert python_class_asset_resolution_signature(imported, "Card") is None
    assert not python_class_static_asset_matches(imported, "Card", None, "card.html")
    assert not python_class_static_asset_matches(post_class_mutation, "Card", None, "card.html")
    assert not python_class_static_asset_matches(helper_mutation, "Card", None, "card.html")
    assert python_class_asset_resolution_signature(shadowed_path, "Card") is None


def test_literal_boolean_branches_exclude_unreachable_returns():
    _source, false_branch = _shape(
        """
        if False:
            return {"impossible": 1}
        return {"actual": 2}
        """,
    )
    _source, true_branch = _shape(
        """
        if True:
            return {"actual": 1}
        return {"impossible": 2}
        """,
    )

    assert [root.name for root in false_branch.roots] == ["actual"]
    assert [root.name for root in true_branch.roots] == ["actual"]
    assert false_branch.roots[0].presence == "always"
    assert true_branch.roots[0].presence == "always"


def test_generator_method_never_claims_return_statement_mappings():
    _source, shape = _shape(
        """
        if False:
            yield value
        return {"not_a_runtime_mapping": 1}
        """,
    )

    assert shape.roots == ()
    assert shape.completeness == "open"


def test_any_non_alias_use_of_typed_kwargs_withholds_schema_claims():
    _source, attribute_read = _shape(
        """
        ignored = kwargs.dangerous
        return kwargs
        """,
        kwargs_fields=("title",),
    )
    _source, subscript_read = _shape(
        """
        ignored = kwargs["title"]
        return kwargs
        """,
        kwargs_fields=("title",),
    )

    for shape in (attribute_read, subscript_read):
        assert shape.roots == ()
        assert shape.completeness == "open"


def test_assignment_calls_and_unknown_computed_writes_withhold_stale_claims():
    _source, call_assignment = _shape(
        """
        data = {"x": 1}
        ignored = mutate(data)
        return data
        """,
    )
    _source, computed_literal = _shape(
        """
        return {"x": 1, key: 2}
        """,
    )
    _source, computed_subscript = _shape(
        """
        data = {"x": 1}
        data[key] = 2
        return data
        """,
    )
    _source, unknown_keyword_update = _shape(
        """
        data = {"x": 1}
        data.update(**unknown)
        return data
        """,
    )

    assert call_assignment.roots == ()
    assert call_assignment.completeness == "open"
    for shape in (computed_literal, computed_subscript, unknown_keyword_update):
        assert [root.name for root in shape.roots] == ["x"]
        assert shape.roots[0].definitions == ()
        assert shape.completeness == "open"


def test_unsupported_rebindings_and_tainted_unpacks_never_reuse_stale_roots():
    _source, destructured = _shape(
        """
        data = {"stale": 1}
        data, other = values
        return data
        """,
    )
    _source, loop_rebound = _shape(
        """
        data = {"stale": 1}
        for data in values:
            pass
        return data
        """,
    )
    _source, walrus_rebound = _shape(
        """
        data = {"stale": 1}
        if data := replacement:
            pass
        return data
        """,
    )
    _source, tainted_unpack = _shape(
        """
        data = {"stale": 1}
        consume(data)
        return {"safe": 2, **data}
        """,
    )

    for shape in (destructured, loop_rebound, walrus_rebound):
        assert shape.roots == ()
        assert shape.completeness == "open"
    assert [root.name for root in tainted_unpack.roots] == ["safe"]
    assert tainted_unpack.roots[0].definitions == ()
    assert tainted_unpack.completeness == "open"


def test_bound_methods_and_nested_container_aliases_taint_local_mappings():
    _source, bound_pop = _shape(
        """
        data = {"gone": 1}
        remove = data.pop
        remove("gone")
        return data
        """,
    )
    _source, list_alias = _shape(
        """
        data = {"gone": 1}
        box = [data]
        box[0].clear()
        return data
        """,
    )
    _source, dict_alias = _shape(
        """
        data = {"gone": 1}
        box = {"mapping": data}
        box["mapping"].clear()
        return data
        """,
    )

    for shape in (bound_pop, list_alias, dict_alias):
        assert shape.roots == ()
        assert shape.completeness == "open"
