from __future__ import annotations

import ast
import textwrap

import pytest

from citry.analysis import (
    TemplatePythonControl,
    TemplatePythonQuery,
    TemplatePythonRoot,
    build_inferred_template_shadow,
    build_schema_template_shadow,
    template_python_queries,
    template_python_query_at,
)
from citry_core.template_parser import parse_template


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


def test_static_and_browser_values_are_not_python_queries() -> None:
    source = '<c-slot name="header" required /><c-card $c-props="items"></c-card>'
    template = parse_template(source)

    for marker in ("header", "required", "items"):
        index = source.index(marker) + 1
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
    assert "title = __citry_data.title" in shadow.source
    assert "__citry_cast(Card.Kwargs, __citry_data).title" not in shadow.source


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
