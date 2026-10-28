from __future__ import annotations

import ast
import sys
import textwrap

import pytest

from citry._symbol_table import symtable
from citry._template_python import _method_bound_names, _renamable_method_locals
from citry.analysis import (
    TemplatePythonControl,
    TemplatePythonQuery,
    TemplatePythonRoot,
    TemplatePythonSlotDataType,
    TemplatePythonValueType,
    build_inferred_template_shadow,
    build_schema_template_shadow,
    template_python_queries,
    template_python_query_at,
    template_static_input_queries,
)
from citry_core.template_parser import parse_template

requires_symtable = pytest.mark.skipif(symtable is None, reason="PyPy has no _symtable; see #434")


def _query(source: str, marker: str):
    index = source.index(marker) + len(marker)
    query = template_python_query_at(parse_template(source), index)
    assert query is not None
    return query


def test_interpolation_carries_exact_expression_range() -> None:
    source = "<p>{{ user.name }}</p>"

    query = _query(source, "user.na")

    assert query.source == "user.name "
    assert source.encode()[query.start_index : query.end_index].decode() == "user.name "
    assert query.host_kind == "interpolation"
    assert query.controls == ()


def test_query_free_names_preserve_python_scope_shadowing() -> None:
    source = "{{ (x.foo, [x for x in items], (lambda arg: arg)(value)) }}"

    query = _query(source, "x.foo")

    assert query.free_names == ("x", "items", "value")


def test_combined_condition_and_loop_recreate_runtime_scope_order() -> None:
    source = '<p c-if="account is not None" c-for="item in account.items" c-title="item.name">{{ item.name }}</p>'

    condition = _query(source, "account is not")
    loop = _query(source, "account.items")
    attribute = _query(source, 'c-title="item.na')
    interpolation = _query(source, "{{ item.na")

    assert condition.controls == ()
    assert loop.controls == (TemplatePythonControl("if", "account is not None", free_names=("account",)),)
    expected = (
        TemplatePythonControl("if", "account is not None", free_names=("account",)),
        TemplatePythonControl("for", "item in account.items", ("item",), ("account",)),
    )
    assert attribute.controls == expected
    assert interpolation.controls == expected


def test_explicit_destructuring_loop_preserves_all_introduced_names() -> None:
    source = '<c-for each="name, score in scores.items()"><p>{{ score.real }}</p></c-for>'

    query = _query(source, "score.re")

    assert query.controls == (
        TemplatePythonControl(
            "for",
            "name, score in scores.items()",
            ("name", "score"),
            ("scores",),
        ),
    )


def test_nested_template_inherits_shorthand_loop_scope() -> None:
    source = '<c-card c-for="item in items" c-body="<><span>{{ item.name }}</span></>" />'

    query = _query(source, "item.na")

    assert query.source == "item.name "
    assert query.controls == (TemplatePythonControl("for", "item in items", ("item",), ("items",)),)


def test_control_attribute_does_not_see_its_own_loop_target() -> None:
    source = '<li c-for="item in items">{{ item.name }}</li>'

    query = _query(source, "item in items")

    assert query.host_kind == "loop"
    assert query.controls == ()


def test_elif_and_else_inherit_the_false_prior_branch_context() -> None:
    source = (
        '<c-if cond="value is None">{{ value }}</c-if>\n'
        '<c-elif cond="value == 0">{{ value.real }}</c-elif>\n'
        "<c-else>{{ value.bit_length() }}</c-else>"
    )

    elif_condition = _query(source, "value ==")
    elif_body = _query(source, "value.real")
    else_body = _query(source, "value.bit_length")

    first_false = TemplatePythonControl("if", "not (\nvalue is None\n)", free_names=("value",))
    second_false = TemplatePythonControl("if", "not (\nvalue == 0\n)", free_names=("value",))
    assert elif_condition.controls == (first_false,)
    assert elif_body.controls == (
        first_false,
        TemplatePythonControl("if", "value == 0", free_names=("value",)),
    )
    assert else_body.controls == (first_false, second_false)


def test_non_whitespace_content_breaks_a_condition_chain() -> None:
    source = '<c-if cond="value is None">first</c-if>text<div>{{ value }}</div>'

    query = _query(source, "{{ value")

    assert query.controls == ()


def test_fill_binding_is_unknown_only_inside_its_body() -> None:
    source = '<c-card><c-fill name="item" data="{record as row}">{{ row.name }}</c-fill></c-card>'

    inner = _query(source, "row.na")

    assert inner.controls == (TemplatePythonControl("unknown", "", ("row",)),)


def test_fill_data_name_records_the_component_and_slot_it_reads() -> None:
    # A fill inside the component's `<c-if>` still belongs to the component,
    # and the fallback name is not the slot's data.
    source = (
        '<c-Card><c-if cond="ok"><c-fill name="footer" data="card" fallback="fb">'
        "{{ card.title }}</c-fill></c-if></c-Card>"
    )

    query = _query(source, "card.ti")

    assert query.controls[-2:] == (
        TemplatePythonControl("unknown", "", ("card",), slot_target=("c-Card", "footer")),
        TemplatePythonControl("unknown", "", ("fb",)),
    )


@pytest.mark.parametrize(
    ("source", "target"),
    [
        # A fill belongs to the nearest component call around it.
        (
            '<c-Outer><c-fill name="body"><c-Card><c-fill name="footer" data="card">{{ card.x }}'
            "</c-fill></c-Card></c-fill></c-Outer>",
            ("c-Card", "footer"),
        ),
        (
            '<c-Card><c-for each="i in items"><c-fill name="footer" data="card">'
            "{{ card.x }}</c-fill></c-for></c-Card>",
            ("c-Card", "footer"),
        ),
        # The rightmost of `name`, `c-name`, and `c-bind` names the slot.
        (
            '<c-Card><c-fill c-bind="opts" name="footer" data="card">{{ card.x }}</c-fill></c-Card>',
            ("c-Card", "footer"),
        ),
        # Recorded as written; the editor leaves the built-in tag untyped.
        (
            '<c-component is="c-Card"><c-fill name="footer" data="card">{{ card.x }}</c-fill></c-component>',
            ("c-component", "footer"),
        ),
    ],
)
def test_fill_data_name_records_the_nearest_component_call(source: str, target: tuple[str, str]) -> None:
    query = _query(source, "card.")

    assert [control.slot_target for control in query.controls if control.names == ("card",)] == [target]


@pytest.mark.parametrize(
    "source",
    [
        # The slot name is computed, or a later `c-bind` may replace it.
        '<c-Card><c-fill c-name="slot" data="card">{{ card.x }}</c-fill></c-Card>',
        '<c-Card><c-fill name="footer" c-bind="opts" data="card">{{ card.x }}</c-fill></c-Card>',
    ],
)
def test_fill_data_name_without_a_known_slot_records_none(source: str) -> None:
    query = _query(source, "card.")

    assert [control.slot_target for control in query.controls] == [None]


_SLOT_DATA = {
    ("c-Card", "footer"): TemplatePythonSlotDataType(
        "FooterData",
        (("title", "str"), ("count", "int"), ("owner", "app.models.Owner"), ("items", "list[str]"), ("lost", None)),
    )
}


def test_fill_data_name_is_declared_as_a_mapping_with_the_slot_fields() -> None:
    source = '<c-Card><c-fill name="footer" data="card">{{ card.titel }}</c-fill></c-Card>'
    query = _query(source, "card.ti")
    module = "class TemplateData:\n    pass\n"

    shadow = build_schema_template_shadow(module, "TemplateData", (), query, slot_data_types=_SLOT_DATA)

    assert shadow is not None
    generated = shadow.source[shadow.source.index("def __citry_analyze_template") :]
    # `items` is a mapping method on the runtime value, so it is not a field;
    # a field whose annotation did not resolve stays untyped.
    assert (
        "    class FooterData(_citry_slot_Mapping[str, _citry_slot_Any]):\n"
        "        title: str\n"
        "        count: int\n"
        "        owner: _citry_slot_0_2_0.Owner\n"
        "        lost: _citry_slot_Any\n"
        "    card = _citry_slot_cast(FooterData, None)\n"
    ) in generated
    assert "    import app.models as _citry_slot_0_2_0\n" in generated
    ast.parse(shadow.source)


def test_fill_data_class_takes_another_name_when_the_query_reads_its_own() -> None:
    source = '<c-Card><c-fill name="footer" data="card">{{ FooterData }}</c-fill></c-Card>'
    query = _query(source, "Footer")

    shadow = build_schema_template_shadow("", "object", (), query, slot_data_types=_SLOT_DATA)

    assert shadow is not None
    assert "class FooterDataSlotData(" in shadow.source
    assert "class FooterData(" not in shadow.source


def test_fill_data_class_does_not_hide_a_class_of_the_module_it_is_copied_from() -> None:
    # A data class in the template's own module may name itself in a field,
    # and the copied module may read it, so the generated class takes
    # another name.
    source = '<c-Card><c-fill name="footer" data="card">{{ card.parent.title }}</c-fill></c-Card>'
    query = _query(source, "card.pa")
    module = "class FooterData:\n    parent: FooterData\nclass TemplateData:\n    pass\n"
    slot_data = {("c-Card", "footer"): TemplatePythonSlotDataType("FooterData", (("parent", "app.FooterData"),))}

    shadow = build_schema_template_shadow(
        module, "TemplateData", (), query, source_module="app", slot_data_types=slot_data
    )

    assert shadow is not None
    assert "class FooterDataSlotData(_citry_slot_Mapping[str, _citry_slot_Any]):\n        parent: FooterData\n" in (
        shadow.source
    )


def test_fill_data_name_stays_unknown_when_user_text_uses_the_generated_prefix() -> None:
    source = '<c-Card><c-fill name="footer" data="card">{{ card.x }}</c-fill></c-Card>'
    query = _query(source, "card.")

    shadow = build_schema_template_shadow("_citry_slot = 1\n", "object", (), query, slot_data_types=_SLOT_DATA)

    assert shadow is not None
    assert "card: __citry_Any = None" in shadow.source


def test_static_and_browser_values_are_not_python_queries() -> None:
    source = '<c-slot name="header" required /><c-card :items="items"></c-card>'
    template = parse_template(source)

    for index in (source.index("header") + 1, source.index("required") + 1, source.rindex("items") + 1):
        assert template_python_query_at(template, index) is None


def test_query_enumeration_covers_nested_and_structural_hosts_once() -> None:
    source = """<c-card c-if="visible" c-body='<><span c-title="user.name">{{ user.label }}</span></>' />"""

    queries = template_python_queries(parse_template(source))

    assert [(query.source.strip(), query.host_kind) for query in queries] == [
        ("visible", "attribute"),
        ("user.name", "attribute"),
        ("user.label", "interpolation"),
    ]


def test_schema_shadow_keeps_an_exact_query_copy() -> None:
    module_source = textwrap.dedent(
        """
        class Card:
            class TemplateData:
                method: str | None
        """
    )
    query = TemplatePythonQuery("method.lower()", 12, 26, "interpolation")

    shadow = build_schema_template_shadow(
        module_source,
        "Card.TemplateData",
        (TemplatePythonRoot("method", "always", "attribute"),),
        query,
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert len(shadow.copies) == 1
    copy = shadow.copies[0]
    assert shadow.source[copy.shadow_start : copy.shadow_end] == query.source
    assert (copy.template_start, copy.template_end) == (12, 26)
    assert "method = __citry_data.method" in shadow.source


def test_schema_shadow_binds_a_canonical_analysis_only_type() -> None:
    source = "class Card:\n    class TemplateData:\n        pass\n"

    shadow = build_schema_template_shadow(
        source,
        "Card.TemplateData",
        (TemplatePythonRoot("request", "always", "analysis", type_display="framework.Request"),),
        TemplatePythonQuery("request.accepted", 0, 16, "interpolation"),
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert "import framework" in shadow.source
    assert "request = __citry_cast(framework.Request, None)" in shadow.source


@pytest.mark.parametrize("display", ["factory()", "str; exposed = 1", "lambda: str"])
def test_template_python_root_rejects_executable_type_displays(display: str) -> None:
    with pytest.raises(ValueError, match="type display"):
        TemplatePythonRoot("request", "always", "analysis", type_display=display)


@requires_symtable
def test_inferred_shadow_evaluates_query_at_each_method_return() -> None:
    module_source = textwrap.dedent(
        """
        from typing import Any

        class Card:
            def template_data(self, args: object, kwargs: object, slots: object) -> dict[str, Any]:
                method = "post"
                if bool(args):
                    return {"method": method}
                return {"method": None}
        """
    )
    query = TemplatePythonQuery("method.lower()", 5, 19, "attribute")

    shadow = build_inferred_template_shadow(
        module_source,
        "Card",
        (TemplatePythonRoot("method", "always"),),
        query,
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert shadow.source.startswith(module_source[: module_source.index("class Card")])
    assert len(shadow.copies) == 2
    assert all(shadow.source[item.shadow_start : item.shadow_end] == query.source for item in shadow.copies)
    assert shadow.source.count("__citry_data['method']") == 2


def _shadow_source_without_symtable(
    monkeypatch: pytest.MonkeyPatch,
    module_source: str,
    query: TemplatePythonQuery,
) -> str | None:
    """Build the shadow as an interpreter with no symbol table (PyPy) would."""
    # Both helpers cache by source text, so clear them before and after the
    # patch to keep each answer tied to the symtable state that produced it.
    _renamable_method_locals.cache_clear()
    _method_bound_names.cache_clear()
    monkeypatch.setattr("citry._template_python.symtable", None)
    try:
        shadow = build_inferred_template_shadow(module_source, "Card", (TemplatePythonRoot("value", "always"),), query)
    finally:
        monkeypatch.undo()
        _renamable_method_locals.cache_clear()
        _method_bound_names.cache_clear()
    return None if shadow is None else shadow.source


@requires_symtable
@pytest.mark.parametrize(
    "module_source",
    [
        # The method binds no template name.
        "class Card:\n    def template_data(self, kwargs):\n        other = 'a'\n        return {'value': other}\n",
        # The method only reads `len`, which the template also reads; a read is never a local.
        "class Card:\n    def template_data(self, kwargs):\n        return {'value': str(len([1]))}\n",
    ],
)
def test_shadow_without_symtable_matches_cpython_when_the_method_binds_no_template_name(
    monkeypatch: pytest.MonkeyPatch,
    module_source: str,
) -> None:
    query = TemplatePythonQuery("len(value)", 0, 10, "interpolation")
    with_table = build_inferred_template_shadow(module_source, "Card", (TemplatePythonRoot("value", "always"),), query)

    assert with_table is not None
    assert _shadow_source_without_symtable(monkeypatch, module_source, query) == with_table.source


@requires_symtable
@pytest.mark.parametrize(
    "module_source",
    [
        "class Card:\n    def template_data(self, kwargs):\n        value = 'a'\n        return {'value': value}\n",
        # A function named like the class must not be read in the class's place.
        (
            "def Card():\n"
            "    def template_data():\n"
            "        pass\n"
            "class Card:\n"
            "    def template_data(self, kwargs):\n"
            "        value = 'a'\n"
            "        return {'value': value}\n"
        ),
    ],
)
def test_shadow_without_symtable_gives_no_answer_when_the_method_binds_a_template_name(
    monkeypatch: pytest.MonkeyPatch,
    module_source: str,
) -> None:
    query = TemplatePythonQuery("value.lower()", 0, 13, "interpolation")

    # CPython renames the clashing local and answers; without the table the
    # local cannot be renamed safely, so there is no answer at all.
    assert build_inferred_template_shadow(module_source, "Card", (TemplatePythonRoot("value", "always"),), query)
    assert _shadow_source_without_symtable(monkeypatch, module_source, query) is None


def test_inferred_shadow_ignores_a_return_after_an_unconditional_return() -> None:
    module_source = (
        "class Card:\n"
        "    def template_data(self, kwargs):\n"
        "        return {'value': 'hello'}\n"
        "        return {'value': 1}\n"
    )

    shadow = build_inferred_template_shadow(
        module_source,
        "Card",
        (TemplatePythonRoot("value", "always"),),
        TemplatePythonQuery("value.lower()", 0, 13, "interpolation"),
    )

    assert shadow is not None
    assert len(shadow.copies) == 1


def test_inferred_shadow_declines_a_return_from_a_finally_suite() -> None:
    module_source = (
        "class Card:\n"
        "    def template_data(self, kwargs):\n"
        "        try:\n"
        "            return {'value': 1}\n"
        "        finally:\n"
        "            return {'value': 'hello'}\n"
    )

    shadow = build_inferred_template_shadow(
        module_source,
        "Card",
        (TemplatePythonRoot("value", "always"),),
        TemplatePythonQuery("value.lower()", 0, 13, "interpolation"),
    )

    assert shadow is None


def test_inferred_shadow_declines_a_return_mutated_by_a_finally_suite() -> None:
    module_source = (
        "class Card:\n"
        "    def template_data(self, kwargs):\n"
        "        data = {'value': 1}\n"
        "        try:\n"
        "            return data\n"
        "        finally:\n"
        "            data['value'] = 'hello'\n"
    )

    shadow = build_inferred_template_shadow(
        module_source,
        "Card",
        (TemplatePythonRoot("value", "always"),),
        TemplatePythonQuery("value.lower()", 0, 13, "interpolation"),
    )

    assert shadow is None


@pytest.mark.parametrize("builder", ["schema", "inferred"])
def test_shadow_placeholder_cannot_collide_with_authored_source(builder: str) -> None:
    sentinel = "__citry_template_expression_query__"
    if builder == "schema":
        module_source = f"# {sentinel}\nclass Card:\n    class TemplateData:\n        user: str\n"
        shadow = build_schema_template_shadow(
            module_source,
            "Card.TemplateData",
            (TemplatePythonRoot("user", "always", "attribute"),),
            TemplatePythonQuery("user.lower()", 0, 12, "interpolation"),
        )
    else:
        module_source = (
            f"# {sentinel}\n"
            "class Card:\n"
            "    def template_data(self, kwargs):\n"
            f"        marker = '{sentinel}'\n"
            "        return {'user': 'hello'}\n"
        )
        shadow = build_inferred_template_shadow(
            module_source,
            "Card",
            (TemplatePythonRoot("user", "always"),),
            TemplatePythonQuery("user.lower()", 0, 12, "interpolation"),
        )

    assert shadow is not None
    ast.parse(shadow.source)
    assert len(shadow.copies) == 1
    assert shadow.source.startswith(f"# {sentinel}\n")


def test_shadow_placeholder_cannot_collide_with_rewritten_module_name() -> None:
    sentinel = "__citry_template_expression_query__"
    module_source = "from .models import User\nclass Card:\n    class TemplateData:\n        user: User\n"

    shadow = build_schema_template_shadow(
        module_source,
        "Card.TemplateData",
        (TemplatePythonRoot("user", "always", "attribute"),),
        TemplatePythonQuery("user.wave", 0, 9, "interpolation"),
        source_module=f"{sentinel}.app",
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert len(shadow.copies) == 1
    assert f"from {sentinel}.models import User" in shadow.source


@pytest.mark.parametrize("indent", ["  ", "\t"])
def test_inferred_shadow_preserves_the_authored_class_suite_indent(indent: str) -> None:
    module_source = f"class Card:\n{indent}def template_data(self, kwargs):\n{indent}    return {{'title': 'hello'}}\n"
    query = TemplatePythonQuery("title.lower()", 0, 13, "interpolation")

    shadow = build_inferred_template_shadow(
        module_source,
        "Card",
        (TemplatePythonRoot("title", "always"),),
        query,
    )

    assert shadow is not None
    ast.parse(shadow.source)


@pytest.mark.parametrize(
    ("source_module", "import_source", "absolute_source"),
    [
        ("pkg.component", "from .models import User as ModelUser", "from pkg.models import User as ModelUser"),
        ("pkg.component", "from . import models", "from pkg import models"),
        ("pkg.sub.component", "from ..models import User", "from pkg.models import User"),
    ],
)
def test_inferred_shadow_mirrors_direct_relative_import_forms(
    source_module: str,
    import_source: str,
    absolute_source: str,
) -> None:
    module_source = (
        f"{import_source}\nclass Card:\n    def template_data(self, kwargs):\n        return {{'title': 'hello'}}\n"
    )
    query = TemplatePythonQuery("title.lower()", 0, 13, "interpolation")

    shadow = build_inferred_template_shadow(
        module_source,
        "Card",
        (TemplatePythonRoot("title", "always"),),
        query,
        source_module=source_module,
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert absolute_source in shadow.source


def test_inferred_shadow_rewrites_a_method_local_relative_import() -> None:
    module_source = (
        "class Card:\n"
        "    def template_data(self, kwargs):\n"
        "        from .models import User as LocalUser\n"
        "        return {'user': LocalUser()}\n"
    )
    query = TemplatePythonQuery("user.wave()", 0, 11, "interpolation")

    shadow = build_inferred_template_shadow(
        module_source,
        "Card",
        (TemplatePythonRoot("user", "always"),),
        query,
        source_module="pkg.component",
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert "from pkg.models import User as LocalUser" in shadow.source


@pytest.mark.parametrize(
    "module_source",
    [
        (
            "class Base:\n"
            "    from .models import User\n"
            "class Card(Base):\n"
            "    def template_data(self, kwargs):\n"
            "        return {'user': self.User()}\n"
        ),
        (
            "def make_user():\n"
            "    from .models import User\n"
            "    return User()\n"
            "class Card:\n"
            "    def template_data(self, kwargs):\n"
            "        return {'user': make_user()}\n"
        ),
    ],
)
def test_inferred_shadow_rewrites_relative_imports_in_copied_supporting_scopes(module_source: str) -> None:
    shadow = build_inferred_template_shadow(
        module_source,
        "Card",
        (TemplatePythonRoot("user", "always"),),
        TemplatePythonQuery("user.lower()", 0, 12, "interpolation"),
        source_module="pkg.component",
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert "from pkg.models import User" in shadow.source
    assert "from .models import User" not in shadow.source


def test_inferred_shadow_resolves_relative_import_from_a_package_initializer() -> None:
    module_source = (
        "from .models import User\n"
        "class Card:\n"
        "    def template_data(self, kwargs):\n"
        "        return {'user': User()}\n"
    )

    shadow = build_inferred_template_shadow(
        module_source,
        "Card",
        (TemplatePythonRoot("user", "always"),),
        TemplatePythonQuery("user.wave()", 0, 11, "interpolation"),
        source_module="pkg",
        source_is_package=True,
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert "from pkg.models import User" in shadow.source


def test_inferred_shadow_keeps_module_relative_star_import_at_module_scope() -> None:
    shadow = build_inferred_template_shadow(
        "from .models import *\nclass Card:\n    def template_data(self, kwargs):\n        return {}\n",
        "Card",
        (),
        TemplatePythonQuery("1", 0, 1, "interpolation"),
        source_module="pkg.component",
    )

    assert shadow is not None
    assert "from pkg.models import *" in shadow.source


def test_inferred_shadow_declines_method_local_relative_star_import() -> None:
    shadow = build_inferred_template_shadow(
        "class Card:\n    def template_data(self, kwargs):\n        from .models import *\n        return {}\n",
        "Card",
        (),
        TemplatePythonQuery("1", 0, 1, "interpolation"),
        source_module="pkg.component",
    )

    assert shadow is None


def test_inferred_shadow_types_the_effective_kwargs_parameter_without_importing_it() -> None:
    module_source = textwrap.dedent(
        """
        class Component:
            def template_data(self, kwargs, slots):
                return kwargs
        """
    )
    query = TemplatePythonQuery("title.lower()", 0, 13, "interpolation")

    shadow = build_inferred_template_shadow(
        module_source,
        "Component",
        (TemplatePythonRoot("title", "always", "attribute"),),
        query,
        kwargs_type=("app", "Card.Kwargs"),
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert "import app as __citry_schema_module" in shadow.source
    assert "kwargs: __citry_schema_module.Card.Kwargs" in shadow.source


def test_inferred_shadow_captures_same_module_owner_before_authored_name_shadowing() -> None:
    module_source = (
        "class Card:\n"
        "    class Kwargs:\n"
        "        title: str\n"
        "    def template_data(self, kwargs):\n"
        "        Card = int\n"
        "        return kwargs\n"
    )

    shadow = build_inferred_template_shadow(
        module_source,
        "Card",
        (TemplatePythonRoot("title", "always", "attribute", "app", "Card.Kwargs"),),
        TemplatePythonQuery("title.lower()", 0, 13, "interpolation"),
        source_module="app",
        kwargs_type=("app", "Card.Kwargs"),
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert "kwargs: Kwargs" in shadow.source
    # A returned variable is read directly, so ty keeps what it knows about it.
    assert "title = kwargs.title" in shadow.source
    assert "__citry_cast(Card.Kwargs, kwargs).title" not in shadow.source


def test_schema_root_types_can_come_from_distinct_declaring_classes() -> None:
    module_source = textwrap.dedent(
        """
        class A:
            class TemplateData:
                title: str
        class B:
            class TemplateData:
                count: int
        """
    )
    roots = (
        TemplatePythonRoot("title", "always", "attribute", "app", "A.TemplateData"),
        TemplatePythonRoot("count", "always", "attribute", "app", "B.TemplateData"),
    )

    shadow = build_schema_template_shadow(
        module_source,
        "A.TemplateData",
        roots,
        TemplatePythonQuery("title.lower()", 0, 13, "interpolation"),
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert "__citry_cast(__citry_type_0.A.TemplateData, __citry_data).title" in shadow.source
    assert "__citry_cast(__citry_type_1.B.TemplateData, __citry_data).count" in shadow.source


def test_shadow_recreates_condition_loop_and_unknown_binding_scope() -> None:
    query = TemplatePythonQuery(
        "row.name.lower()",
        1,
        17,
        "interpolation",
        (
            TemplatePythonControl("if", "items is not None", free_names=("items",)),
            TemplatePythonControl("for", "item in items", ("item",), ("items",)),
            TemplatePythonControl("unknown", "", ("row",)),
        ),
    )
    module_source = "class Card:\n    class TemplateData:\n        items: list[str] | None\n"

    shadow = build_schema_template_shadow(
        module_source,
        "Card.TemplateData",
        (TemplatePythonRoot("items", "always", "attribute"),),
        query,
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert "if (\n        items is not None\n    ):" in shadow.source
    assert "for item in [\n            item\n            for item in items\n        ]:" in shadow.source
    assert "row: __citry_Any = None" in shadow.source


def test_control_comments_cannot_consume_generated_python_framing() -> None:
    module_source = "class Card:\n    class TemplateData:\n        items: list[str]\n"
    query = TemplatePythonQuery(
        "item.lower()",
        0,
        12,
        "interpolation",
        (
            TemplatePythonControl(
                "if",
                "items  # keep the condition",
                free_names=("items",),
            ),
            TemplatePythonControl(
                "for",
                "item in items  # keep the loop",
                ("item",),
                ("items",),
            ),
        ),
    )

    shadow = build_schema_template_shadow(
        module_source,
        "Card.TemplateData",
        (TemplatePythonRoot("items", "always", "attribute"),),
        query,
    )

    assert shadow is not None
    ast.parse(shadow.source)


def test_loop_host_uses_real_comprehension_syntax_and_keeps_exact_mapping() -> None:
    query = TemplatePythonQuery("item in items", 10, 23, "loop")
    module_source = "class Card:\n    class TemplateData:\n        items: list[str]\n"

    shadow = build_schema_template_shadow(
        module_source,
        "Card.TemplateData",
        (TemplatePythonRoot("items", "always", "attribute"),),
        query,
    )

    assert shadow is not None
    ast.parse(shadow.source)
    assert "None for item in items" in shadow.source
    copy = shadow.copies[0]
    assert shadow.source[copy.shadow_start : copy.shadow_end] == query.source


def test_shadow_declines_ambiguous_or_decorated_source_owners() -> None:
    query = TemplatePythonQuery("value", 0, 5, "interpolation")
    roots = (TemplatePythonRoot("value", "always"),)

    assert build_inferred_template_shadow("class Card:\n    pass\n", "Card", roots, query) is None
    assert (
        build_inferred_template_shadow(
            "@decorate\nclass Card:\n    def template_data(self, args, kwargs, slots):\n        return {'value': 1}\n",
            "Card",
            roots,
            query,
        )
        is None
    )
    assert build_schema_template_shadow("class Card:\n    pass\n", "Card[TemplateData]", roots, query) is None


def test_c_attribute_queries_name_their_target() -> None:
    source = '<c-TaskCard c-task="task" c-if="show" /><div c-class="classes" title="x">{{ label }}</div>'

    assert _query(source, 'c-task="ta').attribute_target == ("c-TaskCard", "task")
    assert _query(source, 'c-class="cla').attribute_target == ("div", "class")
    # Control attributes and interpolations have no attribute to type.
    assert _query(source, 'c-if="sh').attribute_target is None
    assert _query(source, "{{ lab").attribute_target is None


def _checked_shadow(value_type: TemplatePythonValueType, *, source_module: str = "app.board") -> str:
    source = '<c-TaskCard c-task="task" />'
    shadow = build_schema_template_shadow(
        "class Board:\n    class TemplateData:\n        task: int\n",
        "Board.TemplateData",
        (TemplatePythonRoot("task", "always", "attribute"),),
        _query(source, 'c-task="ta'),
        source_module=source_module,
        value_type=value_type,
    )
    assert shadow is not None
    # The authored value is still copied exactly once, inside the assignment.
    assert [shadow.source[copy.shadow_start : copy.shadow_end] for copy in shadow.copies] == ["task"]
    return shadow.source


def test_value_check_assigns_the_value_to_an_annotated_name() -> None:
    source = _checked_shadow(TemplatePythonValueType("app.store.Task | None", "app.cards"))

    assert "    import app.store as __citry_checked_type_0\n" in source
    assert "    __citry_checked_value: __citry_checked_type_0.Task | None = (\ntask\n)" in source
    ast.parse(source)


def test_value_check_reads_bare_names_from_their_module_and_typing() -> None:
    source = _checked_shadow(TemplatePythonValueType("Literal['sm', 'md'] | Sequence[Task]", "app.cards"))

    assert "import typing as __citry_checked_type_0" in source
    assert "import app.cards as __citry_checked_type_1" in source
    assert (
        "__citry_checked_value: __citry_checked_type_0.Literal['sm', 'md'] | "
        "__citry_checked_type_0.Sequence[__citry_checked_type_1.Task] = (\ntask\n)"
    ) in source


def test_value_check_keeps_names_from_the_copied_module_bare() -> None:
    # The generated code is a copy of `app.board`, so importing the real
    # module would name a different class than the copied value has.
    source = _checked_shadow(TemplatePythonValueType("app.board._Registry", "app.cards"))

    assert "__citry_checked_value: _Registry = (\ntask\n)" in source
    assert "import app.board" not in source


@pytest.mark.parametrize(
    "value_type",
    [
        # A bare name with no module to read it from proves nothing.
        TemplatePythonValueType("Task", None),
        # A call is not an annotation.
        TemplatePythonValueType("make_type()", "app.cards"),
    ],
)
def test_value_check_is_skipped_when_the_annotation_cannot_be_resolved(value_type) -> None:
    source = _checked_shadow(value_type)

    assert "__citry_checked_value" not in source


def test_value_check_is_added_at_each_inferred_template_data_return() -> None:
    module_source = textwrap.dedent(
        """
        class Board:
            def template_data(self, kwargs, slots):
                if kwargs:
                    return {"task": 1}
                return {"task": 2}
        """
    )
    source = '<c-TaskCard c-task="task" />'

    shadow = build_inferred_template_shadow(
        module_source,
        "Board",
        (TemplatePythonRoot("task", "always"),),
        _query(source, 'c-task="ta'),
        source_module="app.board",
        value_type=TemplatePythonValueType("app.store.Task"),
    )

    assert shadow is not None
    assert shadow.source.count("__citry_checked_value: __citry_checked_type_0.Task = (\ntask\n)") == 2
    ast.parse(shadow.source)


@requires_symtable
def test_inferred_shadow_renames_method_locals_that_template_names_reuse() -> None:
    module_source = textwrap.dedent(
        """
        import os.path

        class Board:
            def template_data(self, kwargs, slots):
                resolved: list[int] = [1]
                def read():
                    return resolved
                try:
                    pass
                except ValueError as item:
                    pass
                import json as label
                os = 1
                return {"items": read(), "label": label}
        """
    )
    source = '<c-for each="resolved in items"><p c-title="(resolved, item, label, os)"></p></c-for>'

    shadow = build_inferred_template_shadow(
        module_source,
        "Board",
        (TemplatePythonRoot("items", "always"), TemplatePythonRoot("label", "always")),
        _query(source, "(resolved, it"),
        source_module="app.board",
    )

    assert shadow is not None
    ast.parse(shadow.source)
    method = shadow.source[shadow.source.index("def __citry_analyze_template") :]
    # Every binding of a reused name, including a closure read and an import
    # alias, moves to its own generated name, so the template names are free.
    assert "__citry_local_resolved: list[int] = [1]" in method
    assert "return __citry_local_resolved" in method
    assert "except ValueError as __citry_local_item:" in method
    assert "import json as __citry_local_label" in method
    assert "'label': __citry_local_label" in method
    assert "__citry_local_os = 1" in method
    assert "for resolved in [resolved for resolved in items]:" in method


@pytest.fixture
def _fresh_renamable_locals():
    # The function caches by source text, so a stale answer from another
    # symtable state would hide what these tests check.
    _renamable_method_locals.cache_clear()
    yield
    _renamable_method_locals.cache_clear()


_RENAMABLE_LOCALS_SOURCE = textwrap.dedent(
    """
    class Board:
        def template_data(self, kwargs, slots):
            resolved = [1]
            label = "x"
            return {"items": resolved, "label": label}
    """
)


@requires_symtable
@pytest.mark.usefixtures("_fresh_renamable_locals")
def test_renamable_method_locals_lists_the_locals_when_symtable_is_present() -> None:
    names = _renamable_method_locals(_RENAMABLE_LOCALS_SOURCE, "Board")

    assert names == {"self", "kwargs", "slots", "resolved", "label"}


@pytest.mark.usefixtures("_fresh_renamable_locals")
def test_renamable_method_locals_has_no_answer_when_symtable_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    # PyPy has no `_symtable`, so the module global is None there.
    monkeypatch.setattr("citry._template_python.symtable", None)

    assert _renamable_method_locals(_RENAMABLE_LOCALS_SOURCE, "Board") is None


@requires_symtable
def test_inferred_shadow_keeps_locals_that_cannot_be_renamed_safely() -> None:
    module_source = textwrap.dedent(
        """
        class Board:
            def template_data(self, kwargs, slots):
                item = 1
                def touch():
                    global item
                import os.path
                return {"items": [item, os.path.sep]}
        """
    )
    source = '<c-for each="item in items"><p c-title="(item, os)"></p></c-for>'

    shadow = build_inferred_template_shadow(
        module_source,
        "Board",
        (TemplatePythonRoot("items", "always"),),
        _query(source, 'c-title="(it'),
        source_module="app.board",
    )

    assert shadow is not None
    # Renaming would point the nested `global` at a different name, and an
    # alias on `import os.path` binds the submodule, not `os`.
    assert "__citry_local_item" not in shadow.source
    assert "__citry_local_os" not in shadow.source


def test_inferred_shadow_reads_present_optional_keys_by_subscript() -> None:
    module_source = textwrap.dedent(
        """
        class Board:
            def template_data(self, kwargs, slots):
                if kwargs:
                    return {"extra": 1}
                return {}
        """
    )

    shadow = build_inferred_template_shadow(
        module_source,
        "Board",
        (TemplatePythonRoot("extra", "conditional"),),
        TemplatePythonQuery("extra", 0, 5, "interpolation", free_names=("extra",)),
    )

    assert shadow is not None
    # `.get()` would merge every value of the dict into one union, so it is
    # used only at the return that may lack the key.
    assert "extra = __citry_data['extra']" in shadow.source
    assert "extra = __citry_data.get('extra')" in shadow.source


@requires_symtable
@pytest.mark.parametrize(
    ("method_body", "kept"),
    [
        # A nested function's parameter of the same name, called by keyword.
        ("item = 1\n        def helper(item):\n            return item\n        helper(item=item)\n", "item"),
        # A nested class attribute of the same name.
        ("item = 1\n        class Inner:\n            item = 2\n        Inner.item\n", "item"),
        # A nested function that reads the module's `item`, while a
        # comprehension variable makes `item` a method local on Python 3.12+.
        ("[item for item in [1]]\n        def read():\n            return item\n", "item"),
    ],
)
def test_inferred_shadow_keeps_a_local_that_nested_code_binds_or_reads_globally(method_body: str, kept: str) -> None:
    module_source = (
        "item = 0\n"
        "class Board:\n"
        "    def template_data(self, kwargs, slots):\n"
        f"        {method_body}"
        "        return {'items': [1]}\n"
    )
    source = '<c-for each="item in items"><p c-title="item"></p></c-for>'

    shadow = build_inferred_template_shadow(
        module_source,
        "Board",
        (TemplatePythonRoot("items", "always"),),
        _query(source, 'c-title="it'),
        source_module="app.board",
    )

    assert shadow is not None
    # Renaming every occurrence would change what the nested code means.
    assert f"__citry_local_{kept}" not in shadow.source


@pytest.mark.skipif(sys.version_info < (3, 12), reason="generic class syntax needs Python 3.12")
@requires_symtable
def test_inferred_shadow_renames_locals_in_a_generic_class() -> None:
    module_source = (
        "class Board[T]:\n"
        "    def template_data(self, kwargs, slots):\n"
        "        item: list[int] = [1]\n"
        "        return {'items': item}\n"
    )
    source = '<c-for each="item in items"><p c-title="item"></p></c-for>'

    shadow = build_inferred_template_shadow(
        module_source,
        "Board",
        (TemplatePythonRoot("items", "always"),),
        _query(source, 'c-title="it'),
        source_module="app.board",
    )

    assert shadow is not None
    assert "__citry_local_item: list[int] = [1]" in shadow.source


@requires_symtable
def test_inferred_shadow_reads_a_returned_root_through_the_copy() -> None:
    # `data` is both the returned variable and a template root, and a nested
    # `nonlocal` keeps it from being renamed, so reading the other roots from
    # `data` would read the value the generated code just assigned to it.
    module_source = textwrap.dedent(
        """
        class Board:
            def template_data(self, kwargs, slots):
                data = {"data": 1, "other": "s"}
                def touch():
                    nonlocal data
                return data
        """
    )

    shadow = build_inferred_template_shadow(
        module_source,
        "Board",
        (TemplatePythonRoot("data", "always"), TemplatePythonRoot("other", "always")),
        TemplatePythonQuery("other", 0, 5, "interpolation", free_names=("other",)),
    )

    assert shadow is not None
    assert "other = __citry_data['other']" in shadow.source


def test_inferred_shadow_reads_keys_before_a_spread_as_optional() -> None:
    module_source = textwrap.dedent(
        """
        class Board:
            def template_data(self, kwargs, slots):
                if kwargs:
                    return {"extra": 1, **kwargs, "after": 2}
                return {}
        """
    )

    shadow = build_inferred_template_shadow(
        module_source,
        "Board",
        (TemplatePythonRoot("extra", "conditional"), TemplatePythonRoot("after", "conditional")),
        TemplatePythonQuery("(extra, after)", 0, 14, "interpolation", free_names=("extra", "after")),
    )

    assert shadow is not None
    # The spread may replace `extra`, so only `after` is read by subscript.
    assert "extra = __citry_data.get('extra')" in shadow.source
    assert "after = __citry_data['after']" in shadow.source


def test_static_input_queries_cover_quoted_component_attributes() -> None:
    source = (
        '<c-Card lane="todo" mark=\'a&amp;b\' flag empty="" bare=x slash="a\\\\b">'
        '<c-if cond="ok"><c-Inner n="5" /></c-if>'
        "</c-Card>"
        '<p title="x"></p>'
    )

    queries = template_static_input_queries(parse_template(source))

    # Each source is the quoted text, a Python literal of the string the
    # child receives, an empty one included. A value-less, unquoted, or
    # backslash value and an HTML element's attribute are left out.
    assert [(query.source, query.attribute_target) for query in queries] == [
        ('"todo"', ("c-Card", "lane")),
        ("'a&amp;b'", ("c-Card", "mark")),
        ('""', ("c-Card", "empty")),
        ('"5"', ("c-Inner", "n")),
    ]
    assert all(source.encode()[query.start_index : query.end_index].decode() == query.source for query in queries)


def test_value_check_imports_a_nested_class_from_its_module() -> None:
    nested = (("app.store.Board.Row", "app.store"),)

    source = _checked_shadow(TemplatePythonValueType("list[app.store.Board.Row] | None", class_modules=nested))
    same_module = _checked_shadow(
        TemplatePythonValueType("app.store.Board.Row", class_modules=nested), source_module="app.store"
    )

    # The module is imported and the nested path read from it; in a copy of
    # that same module the outer class is a bare name.
    assert "import app.store as __citry_checked_type_0" in source
    assert "__citry_checked_value: list[__citry_checked_type_0.Board.Row] | None = (\ntask\n)" in source
    assert "__citry_checked_value: Board.Row = (\ntask\n)" in same_module
