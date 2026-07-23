// Exact generated-source locks for the A0 `$c-props` syntax contract.
//
// A0 intentionally retains the generic attribute node representations. A1
// extracts these contributions into typed boundary records at render time.

mod common;

#[cfg(test)]
mod tests {
    use citry_template_parser::compiler::compile_template;
    use citry_template_parser::parser::parse_template;

    fn wrap(body_list: &str) -> String {
        format!(
            "def generate_template():\n    body = {}\n    return body\n",
            body_list
        )
    }

    fn assert_compile(input: &str, expected_body_list: &str) {
        let template = parse_template(input, None, None)
            .unwrap_or_else(|err| panic!("parse failed for {input:?}: {err:?}"));
        let result = compile_template(template, None)
            .unwrap_or_else(|err| panic!("compile failed for {input:?}: {err:?}"));
        assert_eq!(result, wrap(expected_body_list), "input: {input:?}");
    }

    #[test]
    fn test_direct_form_retains_static_attribute_node() {
        assert_compile(
            r#"<c-child $c-props="{ count: localCount }" />"#,
            r#"[ComponentNode(source, (0, 44,), (StaticHtmlAttr(source, (9, 41,), """$c-props""", """{ count: localCount }""", ()),), [], (), """child""", False),]"#,
        );
    }

    #[test]
    fn test_server_dynamic_form_retains_expression_attribute_node() {
        assert_compile(
            r#"<c-child c-$c-props="props_source" />"#,
            r#"[ComponentNode(source, (0, 37,), (ExprHtmlAttr(source, (9, 34,), """c-$c-props""", """props_source""", ("props_source",)),), [], ("props_source",), """child""", False),]"#,
        );
    }

    #[test]
    fn test_direct_form_and_spread_preserve_source_order() {
        assert_compile(
            r#"<c-child $c-props="first" c-bind="spread" />"#,
            r#"[ComponentNode(source, (0, 44,), (StaticHtmlAttr(source, (9, 25,), """$c-props""", """first""", ()), ExprHtmlAttr(source, (26, 41,), """c-bind""", """spread""", ("spread",)),), [], ("spread",), """child""", False),]"#,
        );
    }

    #[test]
    fn test_static_dynamic_component_rewrites_to_selected_target() {
        assert_compile(
            r#"<c-component is="child" $c-props="{ count: 1 }" />"#,
            r#"[ComponentNode(source, (0, 50,), (StaticHtmlAttr(source, (24, 47,), """$c-props""", """{ count: 1 }""", ()),), [], (), """child""", False),]"#,
        );
    }

    #[test]
    fn test_compile_is_deterministic() {
        let input = r#"<c-child $c-props="first" c-bind="spread" />"#;
        let first = compile_template(parse_template(input, None, None).unwrap(), None).unwrap();
        for _ in 0..5 {
            let again = compile_template(parse_template(input, None, None).unwrap(), None).unwrap();
            assert_eq!(first, again);
        }
    }
}
