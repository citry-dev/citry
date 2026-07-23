// Tests for dynamic attributes (c-* prefix) in HTML-like tags

mod common;

#[cfg(test)]
mod tests {
    use citry_template_parser::parser::parse_template;

    use super::common::{
        assert_parse_error, expr_attr, expr_attr_unquoted, node_elem, self_closing_node_vars,
        start_tag, template_attr, template_with_vars, token, with_used_vars,
    };

    #[test]
    fn test_c_attr_expression() {
        // <c-my-tag c-class="is_active" />
        // 0         1         2         3
        // 01234567890123456789012345678901
        let input = r#"<c-my-tag c-class="is_active" />"#;
        let result = parse_template(input, None, None).unwrap();

        let is_active_var = token("is_active", 19, 1, 20);

        let expected = template_with_vars(
            vec![node_elem(self_closing_node_vars(
                start_tag(
                    token(r#"<c-my-tag c-class="is_active" />"#, 0, 1, 1),
                    token("c-my-tag", 1, 1, 2),
                    vec![with_used_vars(
                        expr_attr(token("c-class", 10, 1, 11), token("is_active", 19, 1, 20)),
                        vec![is_active_var.clone()],
                    )],
                    true,
                ),
                vec![is_active_var.clone()],
            ))],
            vec![is_active_var],
        );

        assert_eq!(result, expected);
    }

    #[test]
    fn test_c_attr_unquoted_value() {
        // Unquoted c-* attribute value should be interpreted as Expression
        // <c-my-tag c-class=is_active />
        // 0         1         2
        // 012345678901234567890123456789
        let input = "<c-my-tag c-class=is_active />";
        let result = parse_template(input, None, None).unwrap();

        let is_active_var = token("is_active", 18, 1, 19);

        let expected = template_with_vars(
            vec![node_elem(self_closing_node_vars(
                start_tag(
                    token("<c-my-tag c-class=is_active />", 0, 1, 1),
                    token("c-my-tag", 1, 1, 2),
                    vec![with_used_vars(
                        expr_attr_unquoted(
                            token("c-class", 10, 1, 11),
                            token("is_active", 18, 1, 19),
                        ),
                        vec![is_active_var.clone()],
                    )],
                    true,
                ),
                vec![is_active_var.clone()],
            ))],
            vec![is_active_var],
        );

        assert_eq!(result, expected);
    }

    #[test]
    fn test_c_attr_with_template() {
        // c-* attribute with nested template (starts/ends with HTML)
        // <c-my-tag c-title="<span>{{ name }}</span>" />
        // 0         1         2         3         4
        // 0123456789012345678901234567890123456789012345
        let input = r#"<c-my-tag c-title="<span>{{ name }}</span>" />"#;
        let result = parse_template(input, None, None).unwrap();

        let name_var = token("name", 28, 1, 29);

        let expected = template_with_vars(
            vec![node_elem(self_closing_node_vars(
                start_tag(
                    token(r#"<c-my-tag c-title="<span>{{ name }}</span>" />"#, 0, 1, 1),
                    token("c-my-tag", 1, 1, 2),
                    vec![with_used_vars(
                        template_attr(
                            token("c-title", 10, 1, 11),
                            token("<span>{{ name }}</span>", 19, 1, 20),
                        ),
                        vec![name_var.clone()],
                    )],
                    true,
                ),
                vec![name_var.clone()],
            ))],
            vec![name_var],
        );

        assert_eq!(result, expected);
    }

    #[test]
    fn test_unterminated_python_strings_in_dynamic_attrs_error() {
        for input in [
            r#"<c-my-tag c-title="'unterminated" />"#,
            r#"<c-my-tag c-title='"unterminated' />"#,
        ] {
            assert_parse_error(input, "missing closing quote in string literal");
        }
    }

    // =============================================================================
    // DUPLICATE / CONFLICTING ATTRIBUTE NAMES
    // =============================================================================
    // One explicit provider per logical attribute. Plain-element class/style
    // are the accumulating exceptions, and c-bind stays repeatable/dynamic.

    #[test]
    fn test_static_and_dynamic_class_style_forms_accumulate_on_elements() {
        for input in [
            r#"<div class="x" c-class="y">hi</div>"#,
            r#"<div c-class="y" class="x">hi</div>"#,
            r#"<c-element is="div" style="color: red" c-style="styles" />"#,
            r#"<c-element is="div" c-style="styles" style="color: red" />"#,
        ] {
            assert!(
                parse_template(input, None, None).is_ok(),
                "input: {input:?}"
            );
        }
    }

    #[test]
    fn test_static_and_dynamic_form_of_same_logical_attr_rejected() {
        for input in [
            r#"<form id="form" c-id="my_var">hi</form>"#,
            r#"<form c-id="my_var" id="form">hi</form>"#,
            r#"<c-card title="static" c-title="dynamic" />"#,
            r#"<c-card c-title="dynamic" title="static" />"#,
            r#"<c-card class="static" c-class="dynamic" />"#,
            r#"<c-slot style="static" c-style="dynamic" />"#,
        ] {
            let err = parse_template(input, None, None).unwrap_err();
            assert!(format!("{:?}", err).contains("same logical attribute"));
        }
    }

    #[test]
    fn test_structural_directive_and_spread_do_not_alias_plain_attrs() {
        assert!(parse_template(
            r#"<label for="field" c-for="field in fields">x</label>"#,
            None,
            None
        )
        .is_ok());
        assert!(parse_template(r#"<div bind="x" c-bind="attrs">x</div>"#, None, None).is_ok());
        assert!(parse_template(r#"<div foo="x" c-c-foo="y">x</div>"#, None, None).is_ok());
    }

    #[test]
    fn test_exact_duplicate_attr_rejected() {
        let err = parse_template(r#"<div class="x" class="y">hi</div>"#, None, None).unwrap_err();
        assert!(format!("{:?}", err).contains("Duplicate attribute"));

        let err =
            parse_template(r#"<div c-class="x" c-class="y">hi</div>"#, None, None).unwrap_err();
        assert!(format!("{:?}", err).contains("Duplicate attribute"));
    }

    #[test]
    fn test_repeated_c_bind_allowed() {
        assert!(parse_template(r#"<div c-bind="a" c-bind="b">hi</div>"#, None, None).is_ok());
    }

    // =============================================================================
    // DYNAMIC ATTRIBUTES REQUIRE A VALUE
    // =============================================================================
    // A `c-*` attribute's value is an expression, so a bare or empty one has
    // nothing to evaluate and is almost certainly a mistake (the user meant
    // the static `foo`, or forgot the value). The control-flow shorthand
    // attributes that take no value by design (c-else, c-empty) are exempt.

    #[test]
    fn test_value_less_dynamic_attr_rejected() {
        for input in [
            "<div c-foo>hi</div>",
            r#"<div c-foo="">hi</div>"#,
            r#"<div c-foo="   ">hi</div>"#,
            "<c-Card c-foo />",
        ] {
            let err = parse_template(input, None, None).unwrap_err();
            assert!(
                format!("{:?}", err).contains("must have a non-empty value"),
                "input: {input:?}"
            );
        }
    }

    #[test]
    fn test_value_less_control_flow_attr_rejected_with_plain_message() {
        // c-if/c-elif/c-for miss their condition/iterable; the message must
        // not suggest a static boolean attribute for them.
        let err = parse_template("<div c-if>hi</div>", None, None).unwrap_err();
        let msg = format!("{:?}", err);
        assert!(msg.contains("'c-if' attribute must have a non-empty value."));
        assert!(!msg.contains("static boolean"));
    }

    #[test]
    fn test_value_less_c_else_and_c_empty_allowed() {
        assert!(parse_template(r#"<p c-if="x">a</p><p c-else>b</p>"#, None, None).is_ok());
        assert!(parse_template(
            r#"<li c-for="i in items">x</li><li c-empty>n</li>"#,
            None,
            None
        )
        .is_ok());
    }
}
