use citry_template_parser::parser::parse_template;
use citry_template_parser::TemplateElement;

fn variable<'a>(
    template: &'a citry_template_parser::Template,
    name: &str,
) -> &'a citry_template_parser::Token {
    template
        .used_variables
        .iter()
        .find(|token| token.content == name)
        .unwrap_or_else(|| {
            panic!(
                "expected variable {name:?}, got {:?}",
                template.used_variables
            )
        })
}

#[test]
fn recursive_template_attributes_keep_absolute_positions() {
    let source = r#"<c-x c-body="<c-y c-body='<span>{{ z }}</span>' />" />"#;
    let template = parse_template(source, None, None).expect("nested template should parse");
    let z = variable(&template, "z");

    assert_eq!((z.start_index, z.end_index), (35, 36));
    assert_eq!(z.line_col, (1, 36));

    let multiline_source = "<c-x c-body=\"<c-y\n c-body='<span>{{ z }}</span>' />\" />";
    let multiline = parse_template(multiline_source, None, None)
        .expect("multiline nested template should parse");
    let z = variable(&multiline, "z");
    assert_eq!(z.start_index, multiline_source.find('z').unwrap());
    assert_eq!(z.line_col, (2, 19));
}

#[test]
fn cropped_tokens_track_multiline_and_unicode_prefixes() {
    let quoted_source = "<c-x\n c-title=\"name\" />";
    let quoted = parse_template(quoted_source, None, None).expect("quoted attribute should parse");
    let TemplateElement::Node(quoted_node) = &quoted.elements[0] else {
        panic!("expected component node");
    };
    let inner = quoted_node.attrs()[0]
        .inner_value
        .as_ref()
        .expect("attribute value");
    assert_eq!(inner.line_col, (2, 11));

    let comment_source = "x\n{# hello #}";
    let commented = parse_template(comment_source, None, None).expect("comment should parse");
    assert_eq!(commented.comments[0].value.line_col, (2, 3));

    let fragment_source = "<c-x c-body=\" \n<>{{ z }}</>\" />";
    let fragment = parse_template(fragment_source, None, None).expect("fragment should parse");
    let z = variable(&fragment, "z");
    assert_eq!(z.start_index, fragment_source.find('z').unwrap());
    assert_eq!(z.line_col, (2, 6));

    let unicode_source = "<c-x c-body=\"\u{2003}<>{{ z }}</>\" />";
    let unicode =
        parse_template(unicode_source, None, None).expect("unicode-spaced fragment should parse");
    let z = variable(&unicode, "z");
    assert_eq!(z.start_index, unicode_source.find('z').unwrap());
    assert_eq!(z.line_col, (1, 20));
}

#[test]
fn unicode_before_for_target_uses_character_columns() {
    let source = r#"<c-for each="é, name in items">{{ name }}</c-for>"#;
    let template = parse_template(source, None, None).expect("loop should parse");
    let TemplateElement::Node(node) = &template.elements[0] else {
        panic!("expected for node");
    };
    let introduced = node.introduced_variables();
    let name = introduced
        .iter()
        .find(|token| token.content == "name")
        .expect("name target");

    assert_eq!(name.start_index, source.find("name").unwrap());
    assert_eq!(name.line_col, (1, 17));
}

#[test]
fn unclosed_nested_templates_return_errors_instead_of_panicking() {
    for source in [
        r#"<c-long-component c-body="<div><span></span>" />"#,
        r#"<c-x c-body="<><div></>" />"#,
    ] {
        let outcome = std::panic::catch_unwind(|| parse_template(source, None, None).is_err());
        assert!(outcome.is_ok(), "parser panicked for {source:?}");
        assert!(outcome.unwrap(), "invalid template parsed: {source:?}");
    }
}

#[test]
fn nested_errors_show_the_root_source_and_absolute_position() {
    let source = "before\n<c-x c-body=\"<div></span>\" />";
    let error = parse_template(source, None, None).unwrap_err().to_string();

    assert!(error.contains("--> 2:19"), "{error}");
    assert!(
        error.contains(r#"<c-x c-body="<div></span>" />"#),
        "{error}"
    );

    let deep_source = "before\n<c-x c-body=\"<c-y c-body='<div></span>' />\" />";
    let deep_error = parse_template(deep_source, None, None)
        .unwrap_err()
        .to_string();
    let closing_index = deep_source.find("</span>").unwrap();
    let line_start = deep_source.find('\n').unwrap() + 1;
    let closing_col = deep_source[line_start..closing_index].chars().count() + 1;
    assert!(
        deep_error.contains(&format!("--> 2:{closing_col}")),
        "{deep_error}"
    );
    assert!(
        deep_error.contains(r#"<c-x c-body="<c-y c-body='<div></span>' />" />"#),
        "{deep_error}"
    );
}

#[test]
fn nested_expression_errors_show_the_root_source() {
    let source = "before\n<c-x c-body=\"<div>{{ 1 + }}</div>\" />";
    let error = parse_template(source, None, None).unwrap_err().to_string();

    assert!(error.contains("--> 2:22"), "{error}");
    assert!(
        error.contains(r#"<c-x c-body="<div>{{ 1 + }}</div>" />"#),
        "{error}"
    );
}

#[test]
fn nested_validation_errors_show_the_root_source() {
    let source = "before\n<c-x c-body=\"<c-if>oops</c-if>\" />";
    let error = parse_template(source, None, None).unwrap_err().to_string();

    assert!(error.contains("--> 2:14"), "{error}");
    assert!(
        error.contains(r#"<c-x c-body="<c-if>oops</c-if>" />"#),
        "{error}"
    );
    assert!(error.contains("must have a 'cond' attribute"), "{error}");
}

#[test]
fn nested_validator_errors_use_root_absolute_tokens() {
    let cases = [
        (
            "before\n<c-x c-body=\"<div c-title></div>\" />",
            "c-title",
            "must have a non-empty value",
        ),
        (
            "before\n<c-x c-body=\"<c-fill name='x'></c-fill>\" />",
            "<c-fill",
            "must be inside a component tag",
        ),
        (
            "before\n<c-x c-body=\"<div id='a' id='b'></div>\" />",
            "id='b'",
            "Duplicate attribute 'id'",
        ),
    ];

    for (source, marker, expected_message) in cases {
        let error = parse_template(source, None, None).unwrap_err().to_string();
        let marker_index = source.find(marker).unwrap();
        let line_start = source.find('\n').unwrap() + 1;
        let marker_col = source[line_start..marker_index].chars().count() + 1;

        assert!(error.contains(&format!("--> 2:{marker_col}")), "{error}");
        assert!(error.contains(&source[line_start..]), "{error}");
        assert!(error.contains(expected_message), "{error}");
    }
}

#[test]
fn nested_grammar_errors_are_rebased_without_nested_diagnostics() {
    let source = "before\n<c-x c-body=\"<>{{</>\" />";
    let error = parse_template(source, None, None).unwrap_err().to_string();

    assert!(error.contains("--> 2:"), "{error}");
    assert!(error.contains(r#"<c-x c-body="<>{{</>" />"#), "{error}");
    assert_eq!(error.matches("-->").count(), 1, "{error}");
}
