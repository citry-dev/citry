"""Portable browser-expression and JSON-wire analysis contracts."""

from __future__ import annotations

import pytest

from citry._browser_expressions import BrowserExpression, browser_component_prop_sites
from citry.analysis import (
    ComponentJsLintConsumer,
    VueLintConsumer,
    analyze_browser_component_source,
    analyze_browser_expression,
    analyze_js_data_source,
    browser_bindings,
    browser_client_prop_accepts,
    browser_component_props,
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
    lint_unknown_component_js_variables,
    lint_unknown_vue_variables,
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
        '<main><button @click="sendEvent(\'save\')" :class="tone"></button>'
        '<span v-for="item in items" v-text="item.name + title" '
        'v-model.lazy="query"></span></main>'
    )
    template = parse_template(source)

    expressions = browser_expressions(template)

    assert [(item.attribute, item.mode) for item in expressions] == [
        ("@click", "statement"),
        (":class", "expression"),
        ("v-for", "loop"),
        ("v-text", "expression"),
        ("v-model.lazy", "expression"),
    ]
    click = expressions[0]
    calls = browser_literal_calls(click, frozenset({"sendEvent", "$sendEvent"}))
    assert [(call.function, call.value) for call in calls] == [("sendEvent", "save")]
    text = expressions[3]
    assert [(binding.name, binding.kind, binding.position) for binding in text.binding_details] == [
        ("item", "v-for", 0)
    ]
    binding = text.binding_details[0]
    assert source.encode()[binding.start_index : binding.end_index].decode() == "item"
    assert [(item.name, item.root) for item in browser_identifiers(text)] == [
        ("item", False),
        ("name", False),
        ("title", True),
    ]


def test_browser_hosts_keep_citry_state_bindings_out_of_vue_analysis():
    source = '<input :c-query.debounce.300ms="refresh" /><input :C-query="ordinaryVueBinding" />'

    expressions = browser_expressions(parse_template(source))

    # Citry prefixes are case-sensitive. The exact lowercase channel belongs
    # to Events, while the case variant remains ordinary Vue shorthand.
    assert [(item.attribute, item.source, item.host) for item in expressions] == [
        (":C-query", "ordinaryVueBinding", "vue")
    ]


def test_native_slot_pattern_binds_only_its_body_and_reports_initializer_references():
    source = (
        '<NativeChild :value="item" #[slotName]="{ item: local = fallback, nested: [first, ...rest] }">'
        '<span :title="local + first + rest.length" />'
        '</NativeChild><p :title="item" />'
    )
    template = parse_template(source)
    expressions = browser_expressions(template)
    by_attribute = [(item.attribute, item) for item in expressions]

    value = next(item for attribute, item in by_attribute if attribute == ":value")
    dynamic_name = next(
        item for attribute, item in by_attribute if attribute == "#[slotName]" and item.mode == "expression"
    )
    pattern = next(
        item for attribute, item in by_attribute if attribute == "#[slotName]" and item.mode == "binding-pattern"
    )
    body = next(item for attribute, item in by_attribute if attribute == ":title" and "local" in item.source)
    sibling = next(item for attribute, item in by_attribute if attribute == ":title" and item.source == "item")

    assert [(item.name, item.root) for item in browser_identifiers(value)] == [("item", True)]
    assert [(item.name, item.root) for item in browser_identifiers(dynamic_name)] == [("slotName", True)]
    assert [item.name for item in analyze_browser_expression(pattern).references] == ["fallback"]
    assert [(item.name, item.root) for item in browser_identifiers(body)] == [
        ("local", False),
        ("first", False),
        ("rest", False),
        ("length", False),
    ]
    assert [(item.name, item.root) for item in browser_identifiers(sibling)] == [("item", True)]
    assert [(item.name, item.kind) for item in browser_bindings(template)] == [
        ("local", "v-slot"),
        ("first", "v-slot"),
        ("rest", "v-slot"),
    ]


def test_v_for_and_v_slot_scopes_keep_same_element_props_outside_slot_bindings():
    source = (
        '<NativeChild v-for="row in rows" :value="item + row" #default="{ item = fallback(row) }">'
        '<span :title="item + row" />'
        '</NativeChild><p :title="item + row" />'
    )
    expressions = browser_expressions(parse_template(source))
    same_element = next(item for item in expressions if item.attribute == ":value")
    pattern = next(item for item in expressions if item.mode == "binding-pattern")
    body = next(item for item in expressions if item.attribute == ":title" and item.source == "item + row")
    sibling = [item for item in expressions if item.attribute == ":title" and item.source == "item + row"][1]

    assert [(item.name, item.root) for item in browser_identifiers(same_element)] == [
        ("item", True),
        ("row", False),
    ]
    pattern_analysis = analyze_browser_expression(pattern)
    assert [item.name for item in pattern_analysis.references] == ["fallback", "row"]
    assert "row" in pattern.bindings
    assert [(item.name, item.root) for item in browser_identifiers(body)] == [
        ("item", False),
        ("row", False),
    ]
    assert [(item.name, item.root) for item in browser_identifiers(sibling)] == [
        ("item", True),
        ("row", True),
    ]


@pytest.mark.parametrize(
    ("directive", "bindings"),
    [('#default="x, y"', ("x", "y")), ('#default="...args"', ("args",))],
)
def test_native_slot_parameter_lists_are_scoped_only_to_descendants(directive, bindings):
    source = (
        f'<NativeChild :title="x + y + args" {directive}>'
        '<span :title="x + y + args" />'
        '</NativeChild><p :title="x + y + args" />'
    )
    expressions = browser_expressions(parse_template(source))
    same_element, body, sibling = [item for item in expressions if item.attribute == ":title"]

    assert all(item.root for item in browser_identifiers(same_element))
    assert {item.name for item in browser_identifiers(body) if not item.root} == set(bindings)
    assert all(item.root for item in browser_identifiers(sibling))


@pytest.mark.parametrize("conditional", ["v-if", "v-else-if"])
def test_same_element_vue_condition_precedes_v_for_and_slot_bindings(conditional):
    source = (
        f'<NativeChild v-for="row in rows" {conditional}="row.visible" '
        '#default="{ item = fallback(row) }">'
        '<span :title="item + row" />'
        "</NativeChild>"
    )
    expressions = browser_expressions(parse_template(source))
    condition = next(item for item in expressions if item.attribute == conditional)
    pattern = next(item for item in expressions if item.mode == "binding-pattern")
    body = next(item for item in expressions if item.attribute == ":title")

    assert [(item.name, item.root) for item in browser_identifiers(condition)] == [
        ("row", True),
        ("visible", False),
    ]
    assert "row" in pattern.bindings
    assert [(item.name, item.root) for item in browser_identifiers(body)] == [
        ("item", False),
        ("row", False),
    ]


def test_only_whole_dynamic_slot_arguments_create_name_expressions():
    source = (
        '<template #foo[bar]="{ item }"><span :title="item" /></template>'
        '<template v-slot:foo[other]="{ item }"><span :title="item" /></template>'
        '<template #[slots[名]].tail="{ item }"><span :title="item" /></template>'
        '<template #[slots[\'[\']].tail="{ item }"><span :title="item" /></template>'
        '<template #[slots[`[`]].tail="{ item }"><span :title="item" /></template>'
        '<template #[slots[a][foo.bar]].tail="{ item }"><span :title="item" /></template>'
    )
    expressions = browser_expressions(parse_template(source))
    slot_name_expressions = [
        item for item in expressions if item.mode == "expression" and item.attribute.startswith(("#", "v-slot:"))
    ]

    assert [(item.attribute, item.source) for item in slot_name_expressions] == [
        ("#[slots[名]].tail", "slots[名]].tail"),
        ("#[slots['[']].tail", "slots['[']].tail"),
        ("#[slots[`[`]].tail", "slots[`[`]].tail"),
        ("#[slots[a][foo.bar]].tail", "slots[a][foo.bar]].tail"),
    ]
    dynamic = slot_name_expressions[0]
    assert source.encode()[dynamic.start_index : dynamic.end_index].decode() == dynamic.source
    analysis = analyze_browser_expression(dynamic)
    assert analysis.valid
    assert [(item.name, item.start_index, item.end_index) for item in analysis.references] == [
        (
            "slots",
            dynamic.start_index,
            dynamic.start_index + len("slots"),
        ),
        (
            "名",
            dynamic.start_index + len("slots["),
            dynamic.start_index + len("slots[名".encode()),
        ),
    ]


def test_default_v_slot_modifier_form_still_introduces_bindings():
    template = parse_template('<template v-slot.foo="{ item }"><span :title="item" /></template>')
    body = next(item for item in browser_expressions(template) if item.attribute == ":title")

    assert [(item.name, item.root) for item in browser_identifiers(body)] == [("item", False)]


def test_invalid_slot_pattern_is_one_invalid_host_without_spurious_bindings():
    template = parse_template('<template #default="{ item:"><span :title="item" /></template>')
    patterns = [item for item in browser_expressions(template) if item.mode == "binding-pattern"]

    assert len(patterns) == 1
    assert not analyze_browser_expression(patterns[0]).valid
    assert browser_bindings(template) == ()
    assert "item" not in patterns[0].bindings


@pytest.mark.parametrize("attribute", ["v-slot", "#default", 'v-slot=""', '#default=""'])
def test_empty_native_slot_directive_has_no_pattern_or_binding(attribute):
    template = parse_template(f'<template {attribute}><span :title="outer" /></template>')

    assert all(item.mode != "binding-pattern" for item in browser_expressions(template))
    assert browser_bindings(template) == ()


def test_citry_slot_channels_do_not_create_native_vue_bindings():
    template = parse_template('<c-Card><c-fill name="body" data="item"><span #c-key="item" /></c-fill></c-Card>')

    assert browser_bindings(template) == ()


def test_browser_hosts_capture_csp_element_attribute_and_evaluator_context():
    source = (
        '<main><span V-TEXT="open"></span></main>'
        '<c-card @click="save()" @c-save="save({ id: item.id })" />'
        '<button @C-CLICK="save(() => 1)"></button>'
    )

    expressions = browser_expressions(parse_template(source))

    assert [(item.canonical_attribute, item.element, item.host, item.evaluator) for item in expressions] == [
        ("v-text", "span", "vue", "normal"),
        ("@click", "c-card", "vue", "raw"),
        ("@c-save", "c-card", "citry-event-args", "raw"),
        ("@c-click", "button", "vue", "normal"),
    ]
    assert expressions[1].bindings == ()
    encoded = source.encode()
    assert [
        encoded[item.attribute_start_index : item.attribute_end_index].decode()  # type: ignore[index]
        for item in expressions
    ] == ["V-TEXT", "@click", "@c-save", "@C-CLICK"]


def test_case_variant_dynamic_element_uses_vue_precompiled_evaluator_context():
    source = (
        '<c-Element is="SCRIPT" @click="value = 1"></c-Element>'
        '<c-Element is="IFRAME" v-text="value"></c-Element>'
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
        (VueLintConsumer(frozenset({"value"}), "ignore"),),
        "strict",
    )
    assert findings == ()


def test_vue_precompiled_expressions_do_not_use_the_legacy_csp_evaluator():
    expressions = browser_expressions(parse_template('<div v-html="markup"></div><button @click="save()"></button>'))
    consumer = VueLintConsumer(frozenset({"markup", "save"}), "ignore")

    assert lint_csp_compatibility(expressions, (consumer,), "off") == ()
    assert lint_csp_compatibility(expressions, (consumer,), "warn") == ()
    assert lint_csp_compatibility(expressions, (consumer,), "strict") == ()
    with pytest.raises(ValueError, match="Unknown CSP compatibility mode"):
        lint_csp_compatibility(expressions, (consumer,), "invalid")  # type: ignore[arg-type]


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
        '<div v-text="items.map((item) => ({ label: item.name, value: suffix }))" '
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
    source_text = "<span v-text=\"$i18n.tr('čau') + other.tr('skip') + $i18n['tr']('skip')\"></span>"
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
        "<span v-text=\"$i18n.format.number(total, {format: 'measurement'}) "
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
          <span v-text="$i18n.tr('outer')"></span>
          <c-i18n tag="section">
            <span v-text="$i18n.tr('blocked')"></span>
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


def test_i18n_bind_calls_accept_only_authenticated_member_owner_spans() -> None:
    source = "component.$i18n.bind({message:'allowed'}); other.$i18n.bind({message:'forged'});"
    expression = BrowserExpression(source, 0, len(source.encode()), "statement", "component-js")
    owner_start = source.index("$i18n")

    calls = browser_i18n_bind_calls(
        expression,
        frozenset({"$i18n"}),
        authenticated_owner_spans=frozenset({(owner_start, owner_start + len("$i18n"))}),
    )

    assert [(call.message, call.owner_start_index) for call in calls] == [("allowed", owner_start)]


def test_browser_i18n_message_calls_keep_parameter_and_attribute_spans():
    source = "$i18n.tr('account-title', { name: accountName, count }, { attr: 'aria-label' })"
    expression = BrowserExpression(source, 11, len(source.encode("utf-8")) + 11, "expression", "v-text")

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
    template = parse_template('<template v-for="(color, index) in colors.filter(Boolean)"></template>')
    expression = browser_expressions(template)[0]

    analysis = analyze_browser_expression(expression)

    assert analysis.valid
    assert [item.name for item in analysis.references] == ["colors", "Boolean"]


def test_oxc_browser_analysis_declines_invalid_source_without_partial_roots():
    template = parse_template('<button @click="submit("></button>')

    analysis = analyze_browser_expression(browser_expressions(template)[0])

    assert not analysis.valid
    assert analysis.references == ()


def test_unknown_vue_lint_is_strict_configurable_and_v_for_scope_aware():
    template = parse_template(
        '<main :class="known + missing">'
        '<div v-for="color in colors"><span v-text="color + missing"></span></div>'
        "<button @click=\"$sendEvent('open'); console.log(known)\"></button>"
        "</main>"
    )
    expressions = browser_expressions(template)
    consumers = (
        VueLintConsumer(frozenset({"known", "colors"}), "error"),
        VueLintConsumer(frozenset({"known", "colors", "missing"}), "warning"),
    )

    findings = lint_unknown_vue_variables(expressions, consumers)

    assert [(item.name, item.severity) for item in findings] == [
        ("missing", "error"),
        ("missing", "error"),
    ]


def test_unknown_vue_lint_honors_ignore_and_declines_invalid_hosts():
    template = parse_template('<button :disabled="missing" @click="broken("></button>')

    findings = lint_unknown_vue_variables(
        browser_expressions(template),
        (VueLintConsumer(frozenset(), "ignore"),),
    )

    assert findings == ()


def test_unknown_vue_lint_uses_native_names_and_respects_unknown_namespace() -> None:
    template = parse_template('<button @click="save(opaque)"></button>')
    expressions = browser_expressions(template)

    assert (
        lint_unknown_vue_variables(
            expressions,
            (VueLintConsumer(frozenset({"save"}), "error", "unknown"),),
        )
        == ()
    )
    findings = lint_unknown_vue_variables(
        expressions,
        (VueLintConsumer(frozenset({"save"}), "error", "closed"),),
    )
    assert [item.name for item in findings] == ["opaque"]


def test_component_source_analysis_keeps_initializer_bindings_and_free_names_separate():
    source = """
const outside = missingOutside;
$component({ onServerRender({ component: current, revision, onEvent: listen, data }) {
  const local = data.ready;
  current.ready = local;
  listen("cart:changed", detail => console.log(revision, detail, missingInside));
} });
"""

    analysis = analyze_browser_component_source(source)

    assert analysis.valid
    assert [(item.name, item.local_name) for item in analysis.bindings] == [
        ("component", "current"),
        ("revision", "revision"),
        ("onEvent", "listen"),
    ]
    assert [item.name for item in analysis.references] == ["console", "missingInside"]


def test_component_source_analysis_reports_vue_options_and_authenticated_helper_spans():
    source = """
$component /* trivia */ ({
  props: ["display-name"],
  methods: { save() {}, ...extra },
  data() { return { ready: true } },
  setup: () => ({ selected: seed }),
  computed: { label() { return this.$i18n.locale } },
});
"""

    analysis = analyze_browser_component_source(source)

    assert analysis.valid
    assert len(analysis.component_calls) == 1
    call = analysis.component_calls[0]
    encoded = source.encode()
    assert encoded[call.callee_start_index : call.callee_end_index] == b"$component"
    assert encoded[call.open_paren_end_index - 1 : call.open_paren_end_index] == b"("
    assert [(item.origin, item.exposed_name) for item in analysis.public_names] == [
        ("props", "displayName"),
        ("methods", "save"),
        ("data", "ready"),
        ("setup", "selected"),
        ("computed", "label"),
    ]
    assert next(item for item in analysis.sections if item.name == "methods").state == "unknown"
    assert [(item.receiver, item.name) for item in analysis.member_references] == [("this", "$i18n")]


def test_component_source_analysis_preserves_native_unknown_states_and_vue_camelization():
    analysis = analyze_browser_component_source("$component({ props: { 'foo--bar': { type: String, ...details } } })")

    prop = next(item for item in analysis.public_names if item.origin == "props")
    assert prop.exposed_name == "foo-Bar"
    assert (prop.required, prop.has_default, prop.type_source) == (None, None, None)
    computed = analyze_browser_component_source(
        "$component({ props: { first: String }, methods: { save() {} }, [key]: value })"
    )
    assert computed.public_names == ()
    assert all(section.state == "unknown" for section in computed.sections)


def test_component_member_literal_calls_require_native_receiver_authentication():
    source = "$component({ methods: { label() { return this.$i18n.resolve('message') } } })"
    analysis = analyze_browser_component_source(source)
    owner_spans = frozenset(
        (item.start_index, item.end_index) for item in analysis.member_references if item.name == "$i18n"
    )
    expression = BrowserExpression(source, 0, len(source.encode()), "statement", "component-js")

    assert [
        call.value
        for call in browser_member_literal_calls(
            expression,
            frozenset({"$i18n"}),
            frozenset({"resolve"}),
            authenticated_owner_spans=owner_spans,
        )
    ] == ["message"]
    assert not browser_member_literal_calls(expression, frozenset({"$i18n"}), frozenset({"resolve"}))


def test_unknown_component_js_lint_is_strict_configurable_and_initializer_only():
    source = """
const outside = missingOutside;
$component({
  onServerRender({ component }) {
    console.log(component.ready, configured, missingInside);
  }
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
    source = "$component({ onServerRender({ component }) { scope.ready = component.ready; } });"

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
        "count: { type: [Number, String], default: null } }, "
        "onServerRender({ component }) { component.$props.title } })"
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
    assert browser_component_props("$component({ props: makeProps(), onServerRender() {} })") is None


def test_component_prop_types_compare_only_proven_broad_json_shapes():
    assert browser_client_prop_accepts("number | null", browser_literal_wire_type("2"))
    assert browser_client_prop_accepts("number | null", browser_literal_wire_type("null"))
    assert not browser_client_prop_accepts("number | null", browser_literal_wire_type("'two'"))
    assert browser_literal_wire_type("calculate() ").kind == "unknown"


def test_native_component_prop_sites_preserve_nested_utf8_ranges_and_dynamic_uncertainty():
    source = (
        'é<template><c-card v-bind="{ title: name }" :display-name.camel="name" '
        ':ignored.prop="value" :ignored-attr.attr="value" :unknown.future="value" />'
        "</template>"
    )

    sites = browser_component_prop_sites(parse_template(source))

    assert len(sites) == 1
    site = sites[0]
    encoded = source.encode("utf-8")
    assert encoded[site.tag_start_index : site.tag_end_index].decode() == "c-card"
    assert [(item.name, item.source, item.dynamic) for item in site.contributions] == [
        ("title", "name", False),
        ("display-name", "name", False),
        (None, "value", True),
    ]
    dynamic = site.contributions[-1]
    assert encoded[dynamic.name_start_index : dynamic.name_end_index].decode() == ":unknown.future"
    assert encoded[dynamic.value_start_index : dynamic.value_end_index].decode() == "value"
