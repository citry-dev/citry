use citry_template_parser::compiler::compile_template;
use citry_template_parser::{
    parse_template_with_options, ForeignSpan, ParseOptions, TemplateElement,
};

fn options(spans: Vec<ForeignSpan>) -> ParseOptions {
    ParseOptions::with_foreign_spans(spans)
}

fn span(start: usize, end: usize, ordinal: usize) -> ForeignSpan {
    ForeignSpan::from_parts(start, end, "host", ordinal, false)
}

fn controlling_span(start: usize, end: usize, ordinal: usize) -> ForeignSpan {
    ForeignSpan::from_parts(start, end, "host", ordinal, true)
}

#[test]
fn body_claim_preserves_original_text_and_order() {
    let source = "before {% if active %}after";
    let start = source.find("{% ").unwrap();
    let end = start + "{% if active %}".len();
    let template =
        parse_template_with_options(source, None, None, &options(vec![span(start, end, 0)]))
            .unwrap();

    assert_eq!(template.elements.len(), 3);
    assert!(
        matches!(&template.elements[0], TemplateElement::Text(text) if text.token.content == "before ")
    );
    assert!(matches!(
        &template.elements[1],
        TemplateElement::Foreign(part)
            if part.token.content == "{% if active %}"
                && part.token.start_index == start
                && part.token.end_index == end
                && part.provider == "host"
                && part.ordinal == 0
    ));
    assert!(
        matches!(&template.elements[2], TemplateElement::Text(text) if text.token.content == "after")
    );
}

#[test]
fn whole_expression_claim_never_reaches_expression_parser() {
    let source = "{{ django.value|default:'x' }}";
    let template =
        parse_template_with_options(source, None, None, &options(vec![span(0, source.len(), 0)]))
            .unwrap();

    assert!(
        matches!(&template.elements[..], [TemplateElement::Foreign(part)] if part.token.content == source)
    );
}

#[test]
fn unicode_before_claim_keeps_byte_offsets_and_character_columns() {
    let source = "žlutý {% value %}";
    let start = source.find("{% ").unwrap();
    let template = parse_template_with_options(
        source,
        None,
        None,
        &options(vec![span(start, source.len(), 0)]),
    )
    .unwrap();
    let TemplateElement::Foreign(part) = &template.elements[1] else {
        panic!("expected foreign part");
    };
    assert_eq!(part.token.start_index, start);
    assert_eq!(part.token.line_col, (1, 7));
    assert_eq!(part.token.content, "{% value %}");
}

#[test]
fn adjacent_claims_remain_distinct() {
    let source = "{% a %}{% b %}";
    let split = "{% a %}".len();
    let template = parse_template_with_options(
        source,
        None,
        None,
        &options(vec![span(0, split, 0), span(split, source.len(), 1)]),
    )
    .unwrap();
    assert!(matches!(
        &template.elements[..],
        [TemplateElement::Foreign(first), TemplateElement::Foreign(second)]
            if first.ordinal == 0 && second.ordinal == 1
    ));
}

#[test]
fn invalid_and_overlapping_claims_fail_before_pest() {
    let source = "éabc";
    for spans in [
        vec![span(1, 2, 0)],
        vec![span(2, 2, 0)],
        vec![span(2, 99, 0)],
        vec![span(0, 3, 0), span(2, 4, 1)],
        vec![span(0, 2, 0), span(2, 4, 0)],
    ] {
        assert!(parse_template_with_options(source, None, None, &options(spans)).is_err());
    }
}

#[test]
fn compiler_emits_fail_closed_foreign_runtime_node() {
    let source = "A{% value %}B";
    let start = 1;
    let end = source.len() - 1;
    let template =
        parse_template_with_options(source, None, None, &options(vec![span(start, end, 4)]))
            .unwrap();
    let generated = compile_template(template, None).unwrap();
    assert!(
        generated.contains(r#"ForeignNode(source, (1, 12,), "host", 4, """{% value %}""", False)"#),
        "{generated}"
    );
}

#[test]
fn ordinary_attribute_value_is_an_ordered_raw_start_tag_program() {
    let source = r#"<div class="{% if active %}on{% endif %}">x</div>"#;
    let open_start = source.find("{% if").unwrap();
    let open_end = open_start + "{% if active %}".len();
    let close_start = source.find("{% endif").unwrap();
    let close_end = close_start + "{% endif %}".len();
    let template = parse_template_with_options(
        source,
        None,
        None,
        &options(vec![
            span(open_start, open_end, 0),
            span(close_start, close_end, 1),
        ]),
    )
    .unwrap();

    let TemplateElement::Node(node) = &template.elements[0] else {
        panic!("expected HTML node");
    };
    assert_eq!(node.attrs()[0].foreign_parts.len(), 2);

    let generated = compile_template(template, None).unwrap();
    let open = generated
        .find(r#"ForeignNode(source, (12, 27,), "host", 0"#)
        .unwrap();
    let literal = generated[open..].find(r#""""on""""#).unwrap() + open;
    let close = generated
        .find(r#"ForeignNode(source, (29, 40,), "host", 1"#)
        .unwrap();
    assert!(open < literal && literal < close, "{generated}");
}

#[test]
fn between_attribute_foreign_source_retains_authored_order() {
    let source = r#"<div {% html_attrs attrs %} class="card">x</div>"#;
    let start = source.find("{% html_attrs").unwrap();
    let end = start + "{% html_attrs attrs %}".len();
    let template =
        parse_template_with_options(source, None, None, &options(vec![span(start, end, 0)]))
            .unwrap();
    let generated = compile_template(template, None).unwrap();

    let foreign = generated.find("ForeignNode(").unwrap();
    let class = generated.find(r#" class=\"card\">"#).unwrap();
    assert!(foreign < class, "{generated}");
}

#[test]
fn between_attribute_and_quoted_value_claims_share_one_ordered_program() {
    let source = r#"<div {% html_attrs attrs %} class="{% if active %}on{% endif %}">x</div>"#;
    let snippets = ["{% html_attrs attrs %}", "{% if active %}", "{% endif %}"];
    let spans = snippets
        .iter()
        .enumerate()
        .map(|(ordinal, snippet)| {
            let start = source.find(snippet).unwrap();
            span(start, start + snippet.len(), ordinal)
        })
        .collect();
    let template = parse_template_with_options(source, None, None, &options(spans)).unwrap();
    let generated = compile_template(template, None).unwrap();

    let first = generated.find(r#""host", 0"#).unwrap();
    let second = generated.find(r#""host", 1"#).unwrap();
    let third = generated.find(r#""host", 2"#).unwrap();
    assert!(first < second && second < third, "{generated}");
    assert_eq!(generated.matches("ForeignNode(").count(), 3, "{generated}");
}

#[test]
fn foreign_start_tag_rejects_citry_dynamic_attribute_rewrites() {
    let source = r#"<div {% html_attrs attrs %} c-class="classes">x</div>"#;
    let start = source.find("{% html_attrs").unwrap();
    let end = start + "{% html_attrs attrs %}".len();
    let error =
        parse_template_with_options(source, None, None, &options(vec![span(start, end, 0)]))
            .unwrap_err();
    assert!(error
        .to_string()
        .contains("FOREIGN_SPAN_UNSUPPORTED_POSITION"));
}

#[test]
fn component_static_input_uses_distinct_foreign_attribute_node() {
    let source = r#"<c-card title="prefix {% value %}"/>"#;
    let start = source.find("{% value").unwrap();
    let end = start + "{% value %}".len();
    let template =
        parse_template_with_options(source, None, None, &options(vec![span(start, end, 0)]))
            .unwrap();
    let generated = compile_template(template, None).unwrap();
    assert!(generated.contains("ForeignHtmlAttr("), "{generated}");
    assert!(generated.contains("ForeignNode("), "{generated}");
}

#[test]
fn foreign_source_inside_raw_and_text_containers_is_not_dropped() {
    for source in [
        "<c-raw>{% value %}</c-raw>",
        "<script>{% value %}</script>",
        "<style>{% value %}</style>",
        "<textarea>{% value %}</textarea>",
        "<title>{% value %}</title>",
    ] {
        let start = source.find("{% value").unwrap();
        let end = start + "{% value %}".len();
        let template =
            parse_template_with_options(source, None, None, &options(vec![span(start, end, 0)]))
                .unwrap();
        let generated = compile_template(template, None).unwrap();
        assert!(generated.contains("ForeignNode("), "{source}: {generated}");
    }
}

#[test]
fn nested_template_attribute_retains_projection_for_lazy_reparse() {
    let source = r#"<c-card c-body="<div>{% value %}</div>"/>"#;
    let start = source.find("{% value").unwrap();
    let end = start + "{% value %}".len();
    let nested_start = source.find("<div>").unwrap();
    let nested_end = source.find("</div>").unwrap() + "</div>".len();
    let template =
        parse_template_with_options(source, None, None, &options(vec![span(start, end, 7)]))
            .unwrap();
    let generated = compile_template(template, None).unwrap();
    assert!(
        generated.contains(&format!(
            r#"(({}, {}, "host", 7, False,),), {}"#,
            start, end, nested_start
        )),
        "{generated}"
    );

    let nested_source = &source[nested_start..nested_end];
    let nested = parse_template_with_options(
        nested_source,
        None,
        None,
        &ParseOptions::with_projection(vec![span(start, end, 7)], nested_start, source.to_string()),
    )
    .unwrap();
    let TemplateElement::Node(node) = &nested.elements[0] else {
        panic!("expected nested div");
    };
    let citry_template_parser::Node::WithBody { body, .. } = node else {
        panic!("expected nested div body");
    };
    assert!(matches!(
        &body.elements[..],
        [TemplateElement::Foreign(part)]
            if part.token.start_index == start && part.token.end_index == end
    ));
}

#[test]
fn controlling_foreign_claims_may_select_component_fills() {
    let source = r#"<c-card>{% if show %}<c-fill name="default">yes</c-fill>{% endif %}</c-card>"#;
    let open_start = source.find("{% if").unwrap();
    let open_end = open_start + "{% if show %}".len();
    let close_start = source.find("{% endif").unwrap();
    let close_end = close_start + "{% endif %}".len();

    parse_template_with_options(
        source,
        None,
        None,
        &options(vec![
            controlling_span(open_start, open_end, 0),
            controlling_span(close_start, close_end, 1),
        ]),
    )
    .unwrap();
}

#[test]
fn non_controlling_foreign_claim_next_to_fill_stays_invalid() {
    let source = r#"<c-card>{% value %}<c-fill name="default">yes</c-fill></c-card>"#;
    let start = source.find("{% value").unwrap();
    let end = start + "{% value %}".len();

    let error =
        parse_template_with_options(source, None, None, &options(vec![span(start, end, 0)]))
            .unwrap_err();
    assert!(error
        .to_string()
        .contains("Non-controlling foreign content"));
}

#[test]
fn masking_cannot_turn_an_authored_tag_name_into_body_text() {
    let source = "<div/>";
    let error =
        parse_template_with_options(source, None, None, &options(vec![span(1, 4, 0)])).unwrap_err();
    let message = error.to_string();
    assert!(message.contains("cannot own a tag name"), "{message}");
    assert!(message.contains("provider \"host\" span 1..4"), "{message}");
}
