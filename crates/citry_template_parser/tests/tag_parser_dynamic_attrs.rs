// Tests for dynamic attributes (c-* prefix) in HTML-like tags

mod common;

#[cfg(test)]
mod tests {
    use citry_template_parser::parser::parse_template;

    use super::common::{
        expr_attr, expr_attr_unquoted, node_elem, self_closing_node_vars, start_tag, template_attr,
        template_with_vars, token, with_used_vars,
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

    // =============================================================================
    // DUPLICATE / CONFLICTING ATTRIBUTE NAMES
    // =============================================================================
    // A static and a dynamic form of the same attribute may coexist: attributes
    // resolve left to right at render time (last one wins; class/style merge).
    // An exact duplicate of the same name is still rejected (except c-bind).
    // See docs/design/html_attrs.md section 4.

    #[test]
    fn test_static_and_dynamic_form_of_same_attr_allowed() {
        assert!(parse_template(r#"<div class="x" c-class="y">hi</div>"#, None, None).is_ok());
        assert!(parse_template(r#"<form c-id="my_var" id="form">hi</form>"#, None, None).is_ok());
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
