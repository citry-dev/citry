"""Portable browser-expression and JSON-wire analysis contracts."""

from __future__ import annotations

import json
from pathlib import Path

from citry._alpine_csp import ALPINE_CSP_COMPATIBILITY_VERSION, classify_alpine_csp
from citry._browser_expressions import BrowserExpression
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
    browser_i18n_bind_calls,
    browser_i18n_binding_directives,
    browser_i18n_message_calls,
    browser_i18n_profile_calls,
    browser_identifiers,
    browser_literal_calls,
    browser_literal_wire_type,
    browser_member_at,
    browser_member_literal_calls,
    json_wire_type_from_annotation,
    json_wire_type_from_expression,
    lint_csp_compatibility,
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


def test_browser_hosts_keep_citry_state_bindings_out_of_alpine_analysis():
    source = '<input :c-query.debounce.300ms="refresh" /><input :C-query="ordinaryAlpineBinding" />'

    expressions = browser_expressions(parse_template(source))

    # Citry prefixes are case-sensitive. The exact lowercase channel belongs
    # to Events, while the case variant remains ordinary Alpine shorthand.
    assert [(item.attribute, item.source, item.host) for item in expressions] == [
        (":C-query", "ordinaryAlpineBinding", "alpine")
    ]


def test_browser_hosts_capture_csp_element_attribute_and_evaluator_context():
    source = (
        '<main X-DATA="{ open: true }"><span X-TEXT="open"></span></main>'
        '<c-card @click="save()" @c-save="save({ id: item.id })" $c-props="{ id: item.id }" />'
        '<button @C-CLICK="save(() => 1)"></button>'
    )

    expressions = browser_expressions(parse_template(source))

    assert [(item.canonical_attribute, item.element, item.host, item.evaluator) for item in expressions] == [
        ("x-data", "main", "alpine", "normal"),
        ("x-text", "span", "alpine", "normal"),
        ("@click", "c-card", "alpine", "raw"),
        ("@c-save", "c-card", "citry-event-args", "raw"),
        ("$c-props", "c-card", "citry-props", "raw"),
        ("@c-click", "button", "alpine", "normal"),
    ]
    assert "open" in expressions[1].bindings
    encoded = source.encode()
    assert [
        encoded[item.attribute_start_index : item.attribute_end_index].decode()  # type: ignore[index]
        for item in expressions
    ] == ["X-DATA", "X-TEXT", "@click", "@c-save", "$c-props", "@C-CLICK"]


def test_case_variant_dynamic_element_uses_the_rendered_html_evaluator_context():
    source = (
        '<c-Element is="SCRIPT" @click="value = 1"></c-Element>'
        '<c-Element is="IFRAME" x-text="value"></c-Element>'
        '<c-Card @click="value = 1" />'
    )
    expressions = browser_expressions(parse_template(source))

    assert [(item.element, item.evaluator) for item in expressions] == [
        ("script", "normal"),
        ("iframe", "normal"),
        ("c-card", "raw"),
    ]
    findings = lint_csp_compatibility(
        expressions,
        (AlpineLintConsumer(frozenset({"value"}), "ignore"),),
        "strict",
    )
    assert len(findings) == 2
    assert [source.encode()[item.start_index : item.end_index].decode() for item in findings] == [
        "@click",
        "x-text",
    ]


def test_alpine_csp_classifier_matches_the_pinned_expression_corpus():
    fixture = json.loads(
        (Path(__file__).parents[3] / "js/citry-client/test/fixtures/alpine-csp-3.16.2.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture["alpineVersion"] == ALPINE_CSP_COMPATIBILITY_VERSION

    for case in fixture["cases"]:
        expression = BrowserExpression(
            case["source"],
            0,
            len(case["source"].encode()),
            "expression",
            "x-text",
            transform=case.get("transform", "identity"),
        )
        actual = classify_alpine_csp(expression).outcome
        expected = case.get("staticOutcome", "compatible" if case["outcome"] == "accepted" else "incompatible")
        assert actual == expected, case["id"]


def test_alpine_csp_checker_handles_directives_casing_derived_code_and_mode():
    source = (
        '<div X-HTML></div><SCRIPT x-text="value"></SCRIPT>'
        '<input x-modelable="count + 1">'
        '<template x-for="item in rows?.items"></template>'
    )
    expressions = browser_expressions(parse_template(source))
    consumer = AlpineLintConsumer(frozenset({"count", "rows", "value"}), "ignore")

    assert lint_csp_compatibility(expressions, (consumer,), "off") == ()
    warnings = lint_csp_compatibility(expressions, (consumer,), "warn")
    errors = lint_csp_compatibility(expressions, (consumer,), "strict")

    assert len(warnings) == 4
    assert {finding.severity for finding in warnings} == {"warning"}
    assert {finding.severity for finding in errors} == {"error"}
    assert all(finding.code == "citry.csp.incompatible-browser-code" for finding in errors)
    assert [source.encode()[finding.start_index : finding.end_index].decode() for finding in errors] == [
        "X-HTML",
        "x-text",
        "count + 1",
        "?.",
    ]


def test_alpine_csp_checker_requires_explicit_scope_for_javascript_globals():
    expression = browser_expressions(parse_template('<span x-text="Math.max(1, 2)"></span>'))[0]

    missing = lint_csp_compatibility(
        (expression,),
        (AlpineLintConsumer(frozenset(), "ignore"),),
        "strict",
    )
    supplied = lint_csp_compatibility(
        (expression,),
        (AlpineLintConsumer(frozenset({"Math"}), "ignore"),),
        "strict",
    )

    assert len(missing) == 1
    assert "unprovided JavaScript global 'Math'" in missing[0].message
    assert supplied == ()
    undefined = browser_expressions(parse_template('<span x-text="undefined"></span>'))[0]
    assert lint_csp_compatibility((undefined,), (AlpineLintConsumer(frozenset(), "ignore"),), "strict") == ()


def test_alpine_csp_checker_reports_unterminated_strings_without_raising():
    expression = BrowserExpression("'unterminated", 7, 20, "expression", "x-text")

    classification = classify_alpine_csp(expression)
    findings = lint_csp_compatibility(
        (expression,),
        (AlpineLintConsumer(frozenset(), "ignore"),),
        "strict",
    )

    assert classification.outcome == "incompatible"
    assert classification.detail == "an unterminated string"
    assert (classification.start_index, classification.end_index) == (7, 20)
    assert len(findings) == 1


def test_alpine_csp_directive_empty_rules_use_javascript_whitespace_semantics():
    source = '<div x-data="\u001c"></div><button @click="\u001c"></button><div x-init="\ufeff"></div>'
    expressions = browser_expressions(parse_template(source))
    findings = lint_csp_compatibility(expressions, (), "strict")

    assert len(findings) == 2
    assert [source.encode()[item.start_index : item.end_index].decode() for item in findings] == [
        "\u001c",
        "\u001c",
    ]


def test_declarative_event_handlers_preserve_wire_names_arguments_and_nested_ranges():
    source = (
        '<button @c-click="save-card" @c-blur="update(name)"></button>'
        '<input :c-query="refresh" :c-other="refresh(args)">'
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
        ("refresh", "refresh"),
        ("refresh(args)", "refresh(args)"),
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


def test_member_literal_calls_keep_direct_i18n_calls_and_exact_utf8_ranges():
    source_text = "<span x-text=\"$i18n.tr('čau') + other.tr('skip') + $i18n['tr']('skip')\"></span>"
    template = parse_template(source_text)
    expression = browser_expressions(template)[0]

    calls = browser_member_literal_calls(
        expression,
        frozenset({"$i18n"}),
        frozenset({"resolve", "tr"}),
    )

    assert [(call.owner, call.function, call.value) for call in calls] == [("$i18n", "tr", "čau")]
    source = source_text.encode()
    assert source[calls[0].start_index : calls[0].end_index].decode() == "čau"


def test_i18n_profile_calls_keep_nested_method_and_literal_option_ranges():
    source_text = (
        "<span x-text=\"$i18n.format.number(total, {format: 'measurement'}) "
        "+ $i18n.parse.percent(value, { format: 'editing' }) + other.format.number(1, {format: 'skip'})"
        '"></span>'
    )
    expression = browser_expressions(parse_template(source_text))[0]

    calls = browser_i18n_profile_calls(expression)

    assert [(call.namespace, call.operation, call.profile) for call in calls] == [
        ("format", "number", "measurement"),
        ("parse", "percent", "editing"),
    ]
    encoded = source_text.encode()
    assert [encoded[call.start_index : call.end_index].decode() for call in calls] == ["measurement", "editing"]


def test_i18n_magic_binding_follows_client_provider_and_server_barrier():
    for client_input in ('c-client="True"', "client"):
        source = f"""
        <c-i18n {client_input} tag="main">
          <span x-text="$i18n.tr('outer')"></span>
          <c-i18n tag="section">
            <span x-text="$i18n.tr('blocked')"></span>
          </c-i18n>
        </c-i18n>
        """

        expressions = browser_expressions(parse_template(source))

        assert [expression.bindings for expression in expressions] == [("$i18n",), ()]


def test_i18n_bind_calls_extract_only_bounded_literal_object_roots():
    source = """
        i18n.bind({
          message: 'toast-title',
          output: 'aria-label',
          values: () => ({ title }),
          onChange(text) { el.setAttribute('aria-label', text) },
        });
        i18n.bind({ message: 'dynamic-output', output, onChange: apply });
        i18n.bind(options);
        other.bind({ message: 'skip', onChange: apply });
    """
    expression = BrowserExpression(source, 7, len(source.encode()) + 7, "statement", "component-js")

    calls = browser_i18n_bind_calls(expression)

    assert [(call.message, call.output, call.has_dynamic_output) for call in calls] == [
        ("toast-title", "aria-label", False),
        ("dynamic-output", None, True),
    ]
    encoded = source.encode()
    assert encoded[calls[0].message_start_index - 7 : calls[0].message_end_index - 7].decode() == "toast-title"
    assert encoded[calls[0].output_start_index - 7 : calls[0].output_end_index - 7].decode() == "aria-label"


def test_browser_i18n_message_calls_keep_parameter_and_attribute_spans():
    source = "$i18n.tr('account-title', { name: accountName, count }, { attr: 'aria-label' })"
    expression = BrowserExpression(source, 11, len(source.encode("utf-8")) + 11, "expression", "x-text")

    calls = browser_i18n_message_calls(expression)

    assert len(calls) == 1
    call = calls[0]
    assert (call.message, call.attribute) == ("account-title", "aria-label")
    assert [(item.name, item.value_source) for item in call.arguments] == [
        ("name", "accountName"),
        ("count", "count"),
    ]
    encoded = source.encode()
    assert encoded[call.message_start_index - 11 : call.message_end_index - 11].decode() == "account-title"
    assert [encoded[item.start_index - 11 : item.end_index - 11].decode() for item in call.arguments] == [
        "name",
        "count",
    ]


def test_browser_i18n_binding_directives_keep_names_values_and_errors() -> None:
    source = """\
<div
  $c-tr:notice.aria-label[title]="{ name: person.name, count: 2 }"
  c-$c-tr:dynamic[aria-label]="binding"
  $c-tr:broken[]
></div>
"""
    directives = browser_i18n_binding_directives(parse_template(source))

    assert len(directives) == 3
    direct, server_dynamic, malformed = directives
    assert (direct.message, direct.output, direct.target) == ("notice", "aria-label", "title")
    assert [argument.name for argument in direct.arguments] == ["name", "count"]
    assert not direct.has_dynamic_arguments
    encoded = source.encode()
    assert encoded[direct.message_start_index : direct.message_end_index].decode() == "notice"
    assert encoded[direct.output_start_index : direct.output_end_index].decode() == "aria-label"
    assert encoded[direct.target_start_index : direct.target_end_index].decode() == "title"
    assert server_dynamic.message == "dynamic"
    assert server_dynamic.server_dynamic
    assert server_dynamic.has_dynamic_arguments
    assert malformed.message is None
    assert malformed.error is not None
    assert "non-empty HTML attribute" in malformed.error


def test_browser_i18n_binding_value_is_an_alpine_expression_host() -> None:
    template = parse_template('<span $c-tr:greeting="{ name: person.name }"></span>')
    expressions = browser_expressions(template)

    assert len(expressions) == 1
    assert expressions[0].attribute == "$c-tr:greeting"
    assert expressions[0].host == "citry-i18n-values"
    assert expressions[0].source == "{ name: person.name }"


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
