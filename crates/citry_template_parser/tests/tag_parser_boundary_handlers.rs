// Parser validation for Alpine and Citry handlers authored on component calls.

mod common;

#[cfg(test)]
mod tests {
    use std::collections::HashMap;
    use std::rc::Rc;

    use citry_template_parser::parser::parse_template;
    use citry_template_parser::parser_context::TagRules;

    use super::common::assert_parse_error;

    fn child_rules() -> Rc<HashMap<String, TagRules>> {
        let mut rules = HashMap::new();
        rules.insert(
            "c-child".to_string(),
            TagRules {
                allowed_attrs: Some(vec![vec!["title".to_string()]]),
                required_attrs: vec![],
                allowed_slots: None,
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        Rc::new(rules)
    }

    #[test]
    fn test_component_boundary_handlers_bypass_python_kwarg_allowlist() {
        let rules = child_rules();
        let template = r#"
            <c-child
                title="ok"
                @click="direct"
                c-@change="server_handler"
                x-on:focus="focus"
                c-x-on:blur="server_longhand"
                @c-save="save"
                c-@c-reset="server_citry_handler"
            />
        "#;

        assert!(parse_template(template, None, Some(&rules)).is_ok());
    }

    #[test]
    fn test_unknown_python_kwarg_remains_rejected() {
        let rules = child_rules();
        let error = parse_template(r#"<c-child title="ok" unknown="no" />"#, None, Some(&rules))
            .unwrap_err();

        assert!(format!("{error}").contains("unknown"));
    }

    #[test]
    fn test_direct_and_server_dynamic_handlers_coexist_only_on_component_boundaries() {
        for input in [
            r#"<button @click="first" c-@click="second"></button>"#,
            r#"<button c-@click="second" @click="first"></button>"#,
            r#"<button x-on:click="first" c-x-on:click="second"></button>"#,
        ] {
            assert_parse_error(input, "provide the same logical attribute");
        }

        for input in [
            r#"<c-child @click="first" c-@click="second" />"#,
            r#"<c-child c-x-on:click="second" x-on:click="first" />"#,
            r#"<c-child @c-save="first" c-@c-save="second" />"#,
        ] {
            assert!(
                parse_template(input, None, None).is_ok(),
                "input: {input:?}"
            );
        }
    }

    #[test]
    fn test_distinct_handler_names_and_spreads_can_interlace() {
        for input in [
            r#"<button @click="first" x-on:click="second" c-bind="attrs"></button>"#,
            r#"<c-child @click="first" x-on:click="second" c-bind="attrs" />"#,
        ] {
            assert!(
                parse_template(input, None, None).is_ok(),
                "input: {input:?}"
            );
        }
    }

    #[test]
    fn test_reserved_control_flow_tag_does_not_gain_handler_bypass() {
        assert_parse_error(
            r#"<c-if cond="ok" @click="no">x</c-if>"#,
            "can only have the following attributes",
        );
    }
}
