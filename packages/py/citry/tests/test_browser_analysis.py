"""Portable browser-expression and JSON-wire analysis contracts."""

from __future__ import annotations

from citry.analysis import (
    AlpineLintConsumer,
    ComponentJsLintConsumer,
    analyze_browser_component_source,
    analyze_browser_expression,
    analyze_js_data_source,
    browser_client_prop_accepts,
    browser_component_prop_uses,
    browser_component_props,
    browser_component_scope_writes,
    browser_declarative_events,
    browser_expressions,
    browser_identifiers,
    browser_literal_calls,
    browser_literal_wire_type,
    browser_member_at,
    json_wire_type_from_annotation,
    json_wire_type_from_expression,
    lint_unknown_alpine_variables,
    lint_unknown_component_js_variables,
    python_event_handler_range,
)
from citry_core.template_parser import parse_template


def test_json_wire_types_map_supported_shapes_and_flag_known_unsupported_values():
    annotation = json_wire_type_from_annotation("dict[str, list[str | None]]")
    literal = json_wire_type_from_expression("{'title': 'Card', 'count': 2, 'active': True}")
    unsupported = json_wire_type_from_annotation("set[datetime.date]")

    assert annotation.javascript == "{[key: string]: Array<string | null>}"
    assert literal.javascript == '{title: "Card", count: 2, active: true}'
    assert unsupported.javascript == "unknown"
    assert unsupported.unsupported == ("sets are not JSON-serializable",)


def test_json_wire_literal_inference_flags_set_values_and_non_string_object_keys():
    set_value = json_wire_type_from_expression("{1, 2}")
    object_value = json_wire_type_from_expression("{1: 'one'}")

    assert set_value.unsupported == ("set literals are not JSON-serializable",)
    assert object_value.unsupported == ("JSON objects require string keys",)


def test_json_wire_expression_uses_only_explicitly_proven_member_types():
    member_types = {
        "kwargs": {
            "submitting": json_wire_type_from_annotation("bool"),
            "label": json_wire_type_from_annotation("str | None"),
        }
    }

    submitting = json_wire_type_from_expression("kwargs.submitting", member_types=member_types)
    label = json_wire_type_from_expression("kwargs.label if enabled else None", member_types=member_types)

    assert submitting.javascript == "boolean"
    assert label.javascript == "string | null"
    assert json_wire_type_from_expression("other.submitting", member_types=member_types).javascript == "unknown"


def test_js_data_source_keeps_only_browser_identifier_roots():
    source = (
        "class Card:\n"
        "    def js_data(self, kwargs, slots):\n"
        "        data = {'title': 'Card', 'optional': None, 'not-valid': 1}\n"
        "        return data\n"
    )

    shape = analyze_js_data_source(source, "Card")

    assert shape is not None
    assert [root.name for root in shape.roots] == ["optional", "title"]
    assert shape.parameters == ("self", "kwargs", "slots")


def test_browser_hosts_preserve_loop_bindings_and_literal_event_ranges():
    source = (
        '<main x-data="{}"><button @click="sendEvent(\'save\')" :class="tone"></button>'
        '<span x-for="item in items" x-text="item.name + title" '
        'x-model.lazy="query" x-intersect.once="load()"></span></main>'
    )
    template = parse_template(source)

    expressions = browser_expressions(template)

    assert [(item.attribute, item.mode) for item in expressions] == [
        ("x-data", "expression"),
        ("@click", "statement"),
        (":class", "expression"),
        ("x-for", "loop"),
        ("x-text", "expression"),
        ("x-model.lazy", "expression"),
        ("x-intersect.once", "statement"),
    ]
    click = expressions[1]
    calls = browser_literal_calls(click, frozenset({"sendEvent", "$sendEvent"}))
    assert [(call.function, call.value) for call in calls] == [("sendEvent", "save")]
    text = expressions[4]
    assert [(binding.name, binding.kind, binding.position) for binding in text.binding_details] == [
        ("item", "x-for", 0)
    ]
    binding = text.binding_details[0]
    assert source.encode()[binding.start_index : binding.end_index].decode() == "item"
    assert [(item.name, item.root) for item in browser_identifiers(text)] == [
        ("item", False),
        ("name", False),
        ("title", True),
    ]


def test_declarative_event_handlers_preserve_wire_names_arguments_and_nested_ranges():
    source = (
        '<button @c-click="save-card" @c-blur="update(name)"></button>'
        "<c-panel c-body=\"<><button @c-click='literal(handler)'></button></>\" />"
    )
    template = parse_template(source)

    events = browser_declarative_events(
        template,
        frozenset({"save-card", "literal(handler)"}),
    )

    assert [(event.name, source.encode()[event.start_index : event.end_index].decode()) for event in events] == [
        ("save-card", "save-card"),
        ("update", "update"),
        ("literal(handler)", "literal(handler)"),
    ]


def test_oxc_browser_analysis_distinguishes_free_roots_from_javascript_locals():
    template = parse_template(
        '<div x-text="items.map((item) => ({ label: item.name, value: suffix }))" '
        '@click="const next = count + 1; submit(next)"></div>'
    )
    text, click = browser_expressions(template)

    text_analysis = analyze_browser_expression(text)
    click_analysis = analyze_browser_expression(click)

    assert text_analysis.valid
    assert [(item.name, item.start_index, item.end_index) for item in text_analysis.references] == [
        ("items", text.start_index, text.start_index + len(b"items")),
        (
            "suffix",
            text.start_index + len(b"items.map((item) => ({ label: item.name, value: "),
            text.start_index + len(b"items.map((item) => ({ label: item.name, value: suffix"),
        ),
    ]
    assert click_analysis.valid
    assert [item.name for item in click_analysis.references] == ["count", "submit"]


def test_oxc_loop_analysis_checks_only_the_outer_iterable_expression():
    template = parse_template('<template x-for="(color, index) in colors.filter(Boolean)"></template>')
    expression = browser_expressions(template)[0]

    analysis = analyze_browser_expression(expression)

    assert analysis.valid
    assert [item.name for item in analysis.references] == ["colors", "Boolean"]


def test_oxc_browser_analysis_declines_invalid_source_without_partial_roots():
    template = parse_template('<button @click="submit("></button>')

    analysis = analyze_browser_expression(browser_expressions(template)[0])

    assert not analysis.valid
    assert analysis.references == ()


def test_unknown_alpine_lint_is_strict_configurable_and_scope_aware():
    template = parse_template(
        '<main x-data="{ local: 1 }" :class="known + missing">'
        '<template x-for="color in colors"><span x-text="color + local + missing"></span></template>'
        "<button @click=\"$dispatch('open'); console.log(known)\"></button>"
        "</main>"
    )
    expressions = browser_expressions(template)
    consumers = (
        AlpineLintConsumer(frozenset({"known", "colors"}), "error"),
        AlpineLintConsumer(frozenset({"known", "colors", "missing"}), "warning"),
    )

    findings = lint_unknown_alpine_variables(expressions, consumers)

    assert [(item.name, item.severity) for item in findings] == [
        ("missing", "error"),
        ("missing", "error"),
    ]


def test_unknown_alpine_lint_honors_ignore_and_declines_invalid_hosts():
    template = parse_template('<button :disabled="missing" @click="broken("></button>')

    findings = lint_unknown_alpine_variables(
        browser_expressions(template),
        (AlpineLintConsumer(frozenset(), "ignore"),),
    )

    assert findings == ()


def test_component_source_analysis_keeps_initializer_bindings_and_free_names_separate():
    source = """
const outside = missingOutside;
$component(({ scope: alpineScope, data }) => {
  const local = data.ready;
  alpineScope.ready = local;
  console.log(missingInside);
});
"""

    analysis = analyze_browser_component_source(source)

    assert analysis.valid
    assert [(item.name, item.local_name) for item in analysis.bindings] == [
        ("scope", "alpineScope"),
        ("data", "data"),
    ]
    assert [item.name for item in analysis.references] == ["console", "missingInside"]
    assert [item.name for item in analysis.scope_writes] == ["ready"]


def test_unknown_component_js_lint_is_strict_configurable_and_initializer_only():
    source = """
const outside = missingOutside;
$component(({ data }) => {
  console.log(data.ready, configured, missingInside);
});
"""

    findings = lint_unknown_component_js_variables(
        source,
        (
            ComponentJsLintConsumer(frozenset({"configured"}), "error"),
            ComponentJsLintConsumer(frozenset({"configured", "missingInside"}), "warning"),
        ),
    )

    assert [(item.name, item.severity) for item in findings] == [("missingInside", "error")]


def test_unknown_component_js_lint_flags_a_missing_context_destructure():
    source = "$component(({ data }) => { scope.ready = data.ready; });"

    findings = lint_unknown_component_js_variables(
        source,
        (ComponentJsLintConsumer(frozenset(), "error"),),
    )

    assert [(item.name, item.code, item.severity) for item in findings] == [
        ("scope", "citry.component-js.unknown-variable", "error")
    ]


def test_simple_data_and_scope_members_are_identified_without_chained_guesses():
    template = parse_template('<button @click="data.title + scope.count + other.title"></button>')
    expression = browser_expressions(template)[0]

    data_index = expression.start_index + len(b"data.ti")
    scope_index = expression.start_index + len(b"data.title + scope.co")
    chained_index = expression.start_index + len(b"data.title + scope.count + other.ti")

    assert browser_member_at(expression, data_index).owner == "data"  # type: ignore[union-attr]
    assert browser_member_at(expression, scope_index).owner == "scope"  # type: ignore[union-attr]
    assert browser_member_at(expression, chained_index).owner == "other"  # type: ignore[union-attr]


def test_component_props_and_event_method_provenance_use_conservative_source_shapes():
    js = (
        "$component({ props: { title: { type: String, required: true }, "
        "count: { type: [Number, String], default: null } }, init({ props }) { props.title } })"
    )
    props = browser_component_props(js)
    source = (
        "class Card:\n    class Events:\n        @event(name='save-card')\n        def save(self):\n            pass\n"
    )

    assert props is not None
    assert [(prop.name, prop.javascript, prop.required, prop.has_default) for prop in props] == [
        ("title", "string", True, False),
        ("count", "number | string | null", False, True),
    ]
    source_range = python_event_handler_range(source, "Card.Events.save", "save", "save-card")
    assert source_range is not None
    assert (source_range.start.line, source_range.start.character) == (3, 12)
    assert (source_range.end.line, source_range.end.character) == (3, 16)
    assert python_event_handler_range(source, "Card.Events.save", "save", "other") is None


def test_dynamic_component_props_remain_unknown_instead_of_looking_empty():
    assert browser_component_props("$component({ props: makeProps(), init() {} })") is None


def test_component_prop_uses_keep_direct_keys_beside_dynamic_spreads():
    source = "<c-child $c-props=\"{ title: label, count: 2, ...extra, '😀': enabled, [computed]: other }\" />"
    uses = browser_component_prop_uses(parse_template(source))

    assert len(uses) == 1
    use = uses[0]
    assert use.tag_name == "c-child"
    assert use.has_dynamic_keys
    assert [(field.name, field.value_source) for field in use.properties] == [
        ("title", "label"),
        ("count", "2"),
        ("😀", "enabled"),
    ]
    encoded = source.encode()
    assert [encoded[field.start_index : field.end_index].decode() for field in use.properties] == [
        "title",
        "count",
        "'😀'",
    ]


def test_component_prop_uses_resolve_only_static_dynamic_component_targets():
    static = parse_template('<c-component is="child" $c-props="{ title }" />')
    dynamic = parse_template('<c-component c-is="target" $c-props="{ title }" />')

    assert [use.tag_name for use in browser_component_prop_uses(static)] == ["c-child"]
    assert browser_component_prop_uses(dynamic) == ()


def test_component_prop_types_compare_only_proven_broad_json_shapes():
    assert browser_client_prop_accepts("number | null", browser_literal_wire_type("2"))
    assert browser_client_prop_accepts("number | null", browser_literal_wire_type("null"))
    assert not browser_client_prop_accepts("number | null", browser_literal_wire_type("'two'"))
    assert browser_literal_wire_type("calculate() ").kind == "unknown"


def test_component_scope_writes_preserve_utf8_ranges_and_exact_value_source():
    source = (
        "const prefix = '😀';\n"
        "$component(({ scope }) => {\n"
        "  scope.title = data.title;\n"
        "  Object.assign(scope, { count: 2 });\n"
        "  setTimeout(() => { scope.late = true; });\n"
        "});\n"
    )

    writes = browser_component_scope_writes(source)
    encoded = source.encode()

    assert [(write.name, write.value_source) for write in writes] == [
        ("title", "data.title"),
        ("count", "2"),
    ]
    assert [encoded[write.start_index : write.end_index].decode() for write in writes] == [
        "title",
        "count",
    ]
