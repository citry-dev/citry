// Tests for fill placement, constraints, overflow detection, identity, and duplicates

mod common;

#[cfg(test)]
mod tests {
    use std::collections::{BTreeMap, HashMap};
    use std::rc::Rc;

    use citry_template_parser::parser::parse_template;
    use citry_template_parser::parser_context::TagRules;
    use citry_template_parser::{Node, Template, TemplateElement};

    use super::common::assert_parse_error;

    fn first_fill(template: &Template) -> &Node {
        let TemplateElement::Node(component) = &template.elements[0] else {
            panic!("expected an outer component");
        };
        let Node::WithBody { body, .. } = component else {
            panic!("expected the outer component to have a body");
        };
        body.elements
            .iter()
            .find_map(|element| match element {
                TemplateElement::Node(node) if node.tag_name() == "c-fill" => Some(node),
                _ => None,
            })
            .expect("expected a c-fill child")
    }

    fn rules_with_slot_data(slot_name: &str, fields: &[&str]) -> Rc<HashMap<String, TagRules>> {
        let mut slot_data_fields = BTreeMap::new();
        slot_data_fields.insert(
            slot_name.to_string(),
            fields.iter().map(|field| (*field).to_string()).collect(),
        );
        let mut rules = HashMap::new();
        rules.insert(
            "c-grid".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![],
                allowed_slots: Some(vec![slot_name.to_string()]),
                required_slots: vec![],
                slot_data_fields,
            },
        );
        Rc::new(rules)
    }

    // #######################################
    // FILL PLACEMENT AND CONSTRAINTS
    // #######################################

    #[test]
    fn test_fill_cannot_mix_with_other_tags() {
        // <c-fill> tags cannot be siblings with non-fill, non-control-flow tags

        // <div> then <c-fill>
        let input = r#"<c-my-comp><div>Hello</div><c-fill name="footer">B</c-fill></c-my-comp>"#;
        assert_parse_error(input, "must be grouped");

        // <c-fill> then <div>
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><div>Hello</div></c-my-comp>"#;
        assert_parse_error(input, "must be grouped");

        // Multiple <c-fill> tags together is fine
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-fill name="footer">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Multiple c-fill siblings should succeed: {:?}",
            result.err()
        );

        // <c-fill> then <c-if> containing only c-fill
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-if cond="x"><c-fill name="footer">B</c-fill></c-if></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-fill then c-if (containing only c-fill) should succeed: {:?}",
            result.err()
        );

        // <c-if> containing only c-fill then <c-fill>
        let input = r#"<c-my-comp><c-if cond="x"><c-fill name="header">A</c-fill></c-if><c-fill name="footer">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-if (containing only c-fill) then c-fill should succeed: {:?}",
            result.err()
        );

        // <c-fill> then <c-for> containing only c-fill
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-for each="s in slots"><c-fill c-name="s">X</c-fill></c-for></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-fill then c-for (containing only c-fill) should succeed: {:?}",
            result.err()
        );

        // <c-for> containing only c-fill then <c-fill>
        let input = r#"<c-my-comp><c-for each="s in slots"><c-fill c-name="s">X</c-fill></c-for><c-fill name="footer">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-for (containing only c-fill) then c-fill should succeed: {:?}",
            result.err()
        );

        // <c-fill> then nested control flow (c-if > c-for > c-fill)
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-if cond="x"><c-for each="s in slots"><c-fill c-name="s">X</c-fill></c-for></c-if></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-fill then nested control flow containing only c-fill should succeed: {:?}",
            result.err()
        );

        // Nested control flow (c-if > c-for > c-fill) then <c-fill>
        let input = r#"<c-my-comp><c-if cond="x"><c-for each="s in slots"><c-fill c-name="s">X</c-fill></c-for></c-if><c-fill name="footer">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Nested control flow containing only c-fill then c-fill should succeed: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_control_flow_sibling_must_contain_only_fills() {
        // c-if with <div> AFTER c-fill
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-if cond="x"><div>Not a fill</div></c-if></c-my-comp>"#;
        assert_parse_error(input, "contains non-fill content");

        // c-if with <div> BEFORE c-fill
        let input = r#"<c-my-comp><c-if cond="x"><div>Bad</div></c-if><c-fill name="header">A</c-fill></c-my-comp>"#;
        assert_parse_error(input, "contains non-fill content");

        // c-if with text AFTER c-fill
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-if cond="x">Some text</c-if></c-my-comp>"#;
        assert_parse_error(input, "contains non-fill content");

        // c-if with text BEFORE c-fill
        let input = r#"<c-my-comp><c-if cond="x">Some text</c-if><c-fill name="header">A</c-fill></c-my-comp>"#;
        assert_parse_error(input, "contains non-fill content");

        // c-if with expression AFTER c-fill
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-if cond="x">{{ expr }}</c-if></c-my-comp>"#;
        assert_parse_error(input, "contains non-fill content");

        // c-if with expression BEFORE c-fill
        let input = r#"<c-my-comp><c-if cond="x">{{ expr }}</c-if><c-fill name="header">A</c-fill></c-my-comp>"#;
        assert_parse_error(input, "contains non-fill content");

        // c-if with component AFTER c-fill
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-if cond="x"><c-other>Z</c-other></c-if></c-my-comp>"#;
        assert_parse_error(input, "contains non-fill content");

        // c-if with component BEFORE c-fill
        let input = r#"<c-my-comp><c-if cond="x"><c-other>Z</c-other></c-if><c-fill name="header">A</c-fill></c-my-comp>"#;
        assert_parse_error(input, "contains non-fill content");

        // Nested control flow with bad content AFTER c-fill
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-if cond="x"><c-for each="s in slots"><div>Bad</div></c-for></c-if></c-my-comp>"#;
        assert_parse_error(input, "contains non-fill content");

        // Nested control flow with bad content BEFORE c-fill
        let input = r#"<c-my-comp><c-if cond="x"><c-for each="s in slots"><div>Bad</div></c-for></c-if><c-fill name="header">A</c-fill></c-my-comp>"#;
        assert_parse_error(input, "contains non-fill content");
    }

    #[test]
    fn test_fill_cannot_nest_inside_fill() {
        // <c-fill> cannot be nested inside another <c-fill>
        let input = r#"<c-my-comp><c-fill name="outer"><c-fill name="inner">X</c-fill></c-fill></c-my-comp>"#;
        assert_parse_error(input, "cannot be inside");
    }

    #[test]
    fn test_fill_must_be_inside_component() {
        // <c-fill> at the top level (not inside any component) should fail
        let input = r#"<c-fill name="footer">X</c-fill>"#;
        assert_parse_error(input, "must be inside a component");

        // <c-fill> inside a regular HTML tag should fail
        let input = r#"<div><c-fill name="footer">X</c-fill></div>"#;
        assert_parse_error(input, "must be inside a component");
    }

    #[test]
    fn test_fill_inside_control_flow() {
        // <c-fill> CAN be inside control flow tags when those are inside a component

        // Inside c-if
        let input =
            r#"<c-my-comp><c-if cond="x"><c-fill name="header">A</c-fill></c-if></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-fill inside c-if should succeed: {:?}",
            result.err()
        );

        // Inside c-elif
        let input = r#"<c-my-comp><c-if cond="x"><c-fill name="a">A</c-fill></c-if><c-elif cond="y"><c-fill name="b">B</c-fill></c-elif></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-fill inside c-elif should succeed: {:?}",
            result.err()
        );

        // Inside c-else
        let input = r#"<c-my-comp><c-if cond="x"><c-fill name="a">A</c-fill></c-if><c-else><c-fill name="b">B</c-fill></c-else></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-fill inside c-else should succeed: {:?}",
            result.err()
        );

        // Inside c-for
        let input = r#"<c-my-comp><c-for each="item in items"><c-fill name="row">X</c-fill></c-for></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-fill inside c-for should succeed: {:?}",
            result.err()
        );

        // Inside c-empty (after c-for)
        let input = r#"<c-my-comp><c-for each="item in items"><c-fill name="row">X</c-fill></c-for><c-empty><c-fill name="empty">None</c-fill></c-empty></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-fill inside c-empty should succeed: {:?}",
            result.err()
        );

        // Counter examples: same templates WITHOUT the encapsulating <c-my-comp> should fail
        // because <c-fill> must be inside a component tag.

        // c-fill inside c-if at root
        let input = r#"<c-if cond="x"><c-fill name="header">A</c-fill></c-if>"#;
        assert_parse_error(input, "must be inside a component");

        // c-fill inside c-elif at root
        let input =
            r#"<c-if cond="x">A</c-if><c-elif cond="y"><c-fill name="b">B</c-fill></c-elif>"#;
        assert_parse_error(input, "must be inside a component");

        // c-fill inside c-else at root
        let input = r#"<c-if cond="x">A</c-if><c-else><c-fill name="b">B</c-fill></c-else>"#;
        assert_parse_error(input, "must be inside a component");

        // c-fill inside c-for at root
        let input = r#"<c-for each="item in items"><c-fill name="row">X</c-fill></c-for>"#;
        assert_parse_error(input, "must be inside a component");

        // c-fill inside c-empty at root
        let input = r#"<c-for each="item in items">X</c-for><c-empty><c-fill name="empty">None</c-fill></c-empty>"#;
        assert_parse_error(input, "must be inside a component");
    }

    #[test]
    fn test_fill_inside_reserved_tag_c_raw() {
        // <c-raw> treats everything inside as raw text, so <c-fill> inside it
        // is not parsed as a tag - it's just literal text
        let input = r#"<c-my-comp><c-raw><c-fill name="header">A</c-fill></c-raw></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-fill inside c-raw is treated as raw text, should succeed: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_with_data_and_fallback_attrs() {
        // <c-fill> with data attr introduces a variable that is available in the body.
        // The introduced variable is excluded from the node's used_variables (not propagated to parent).
        let input = r#"<c-my-comp><c-fill name="header" data="x">{{ x }}</c-fill></c-my-comp>"#;
        let template = parse_template(input, None, None).unwrap();

        // "x" is introduced by data="x", so it should NOT appear in the template's used_variables
        let used_var_names: Vec<&str> = template
            .used_variables
            .iter()
            .map(|v| v.content.as_str())
            .collect();
        assert!(
            !used_var_names.contains(&"x"),
            "template.used_variables should NOT contain 'x' (introduced by data attr): {:?}",
            used_var_names
        );

        // Same for fallback attr
        let input = r#"<c-my-comp><c-fill name="header" fallback="y">{{ y }}</c-fill></c-my-comp>"#;
        let template = parse_template(input, None, None).unwrap();

        let used_var_names: Vec<&str> = template
            .used_variables
            .iter()
            .map(|v| v.content.as_str())
            .collect();
        assert!(
            !used_var_names.contains(&"y"),
            "template.used_variables should NOT contain 'y' (introduced by fallback attr): {:?}",
            used_var_names
        );

        // Using a variable NOT introduced by the fill - should be in used_variables
        let input = r#"<c-my-comp><c-fill name="header" data="x">{{ z }}</c-fill></c-my-comp>"#;
        let template = parse_template(input, None, None).unwrap();

        let used_var_names: Vec<&str> = template
            .used_variables
            .iter()
            .map(|v| v.content.as_str())
            .collect();
        assert!(
            used_var_names.contains(&"z"),
            "template.used_variables should contain 'z' (from outer scope): {:?}",
            used_var_names
        );
        assert!(
            !used_var_names.contains(&"x"),
            "template.used_variables should NOT contain 'x' (introduced by data attr): {:?}",
            used_var_names
        );

        // Other attributes on c-fill should fail (only name, c-name, data, fallback, c-bind are allowed)
        let input = r#"<c-my-comp><c-fill name="header" class="foo">X</c-fill></c-my-comp>"#;
        assert_parse_error(input, "can only have");

        // "default" is not an allowed c-fill attribute (the fallback-variable attr is "fallback")
        let input = r#"<c-my-comp><c-fill name="header" default="y">{{ y }}</c-fill></c-my-comp>"#;
        assert_parse_error(input, "can only have");
    }

    #[test]
    fn test_fill_data_destructuring_records_fields_aliases_rest_and_targets() {
        let input = r#"<c-my-comp><c-fill name="default" data="{
            root_attrs,
            table_attrs as inner_table_attrs,
            **rest,
        }">{{ root_attrs }}{{ inner_table_attrs }}{{ rest }}</c-fill></c-my-comp>"#;
        let template = parse_template(input, None, None).unwrap();
        let fill = first_fill(&template);
        let pattern = fill
            .attrs()
            .iter()
            .find(|attr| attr.key.content == "data")
            .and_then(|attr| attr.fill_data_pattern.as_ref())
            .expect("direct data has a parsed pattern");

        assert!(pattern.whole.is_none());
        assert_eq!(
            pattern
                .fields
                .iter()
                .map(|field| (field.source.content.as_str(), field.target.content.as_str()))
                .collect::<Vec<_>>(),
            vec![
                ("root_attrs", "root_attrs"),
                ("table_attrs", "inner_table_attrs")
            ]
        );
        assert_eq!(
            pattern.rest.as_ref().map(|token| token.content.as_str()),
            Some("rest")
        );
        assert_eq!(
            fill.introduced_variables()
                .iter()
                .map(|token| token.content.as_str())
                .collect::<Vec<_>>(),
            vec!["root_attrs", "inner_table_attrs", "rest"]
        );
        assert!(template.used_variables.is_empty());
    }

    #[test]
    fn test_fill_data_destructuring_accepts_single_rest_unicode_and_unquoted_forms() {
        for input in [
            r#"<c-my-comp><c-fill name="default" data="{ **rest }">{{ rest }}</c-fill></c-my-comp>"#,
            r#"<c-my-comp><c-fill name="default" data="{ café as résultat }">{{ résultat }}</c-fill></c-my-comp>"#,
            r#"<c-my-comp><c-fill name="default" data={value}>{{ value }}</c-fill></c-my-comp>"#,
        ] {
            let template = parse_template(input, None, None);
            assert!(
                template.is_ok(),
                "expected valid destructuring for {input:?}: {template:?}"
            );
        }
    }

    #[test]
    fn test_fill_data_destructuring_rejects_malformed_or_ambiguous_patterns() {
        for input in [
            "{}",
            "{, x}",
            "{x,, y}",
            "{x y}",
            "{x as}",
            "{as y}",
            "{x AS y}",
            "{x as y as z}",
            "{x as {y}}",
            "{x.y}",
            "{x[0]}",
            "{'x'}",
            "{x: y}",
            "{*rest}",
            "{***rest}",
            "{**}",
            "{**rest as other}",
            "{x, **rest, y}",
            "{**rest, **other}",
            "{class}",
        ] {
            let template = format!(
                "<c-my-comp><c-fill name=\"default\" data=\"{input}\">body</c-fill></c-my-comp>"
            );
            assert_parse_error(&template, "<c-fill>");
        }
    }

    #[test]
    fn test_fill_data_destructuring_rejects_duplicate_sources_and_targets() {
        for (binding, message) in [
            ("{x as y, x}", "field 'x' more than once"),
            ("{x as y, y}", "variable 'y' more than once"),
            ("{x as rest, **rest}", "variable 'rest' more than once"),
            ("{x as K, y as K}", "variable 'K' more than once"),
        ] {
            let template = format!(
                "<c-my-comp><c-fill name=\"default\" data=\"{binding}\">body</c-fill></c-my-comp>"
            );
            assert_parse_error(&template, message);
        }
    }

    #[test]
    fn test_fill_data_bindings_follow_python_identifier_normalization() {
        let template = parse_template(
            r#"<c-my-comp><c-fill name="default" data="{ x as K }">{{ K }}</c-fill></c-my-comp>"#,
            None,
            None,
        )
        .unwrap();
        let fill = first_fill(&template);
        assert_eq!(
            fill.introduced_variables()
                .iter()
                .map(|token| token.content.as_str())
                .collect::<Vec<_>>(),
            vec!["K"]
        );
        assert!(template.used_variables.is_empty());
    }

    #[test]
    fn test_typed_slot_data_accepts_known_sources_aliases_whole_and_rest() {
        let rules = rules_with_slot_data("row", &["item", "index"]);
        for binding in [
            "data",
            "{ item as current_item, index }",
            "{ item, **rest }",
            "{ **rest }",
        ] {
            let template =
                format!("<c-grid><c-fill name=\"row\" data=\"{binding}\">body</c-fill></c-grid>");
            let result = parse_template(&template, None, Some(&rules));
            assert!(
                result.is_ok(),
                "expected known slot-data binding {binding:?} to parse: {:?}",
                result.err()
            );
        }
    }

    #[test]
    fn test_typed_slot_data_rejects_unknown_explicit_source() {
        let rules = rules_with_slot_data("row", &["item", "index"]);
        let input = r#"<c-grid><c-fill name="row" data="{ missing }">body</c-fill></c-grid>"#;
        let error = parse_template(input, None, Some(&rules)).unwrap_err();
        let message = error.to_string();
        assert!(message.contains("does not expose a slot-data field named 'missing'"));
        assert!(message.contains("Available fields: item, index."));
        assert!(message.contains("data=\"{ missing }\""));
    }

    #[test]
    fn test_typed_slot_data_empty_shape_rejects_explicit_source() {
        let rules = rules_with_slot_data("empty", &[]);
        let input = r#"<c-grid><c-fill name="empty" data="{ value }">body</c-fill></c-grid>"#;
        let error = parse_template(input, None, Some(&rules)).unwrap_err();
        assert!(error
            .to_string()
            .contains("slot's declared data shape has no fields"));
    }

    #[test]
    fn test_typed_slot_data_defers_dynamic_or_unknown_shapes() {
        let rules = rules_with_slot_data("row", &["item"]);
        let dynamic_name =
            r#"<c-grid><c-fill c-name="slot_name" data="{ missing }">body</c-fill></c-grid>"#;
        assert!(parse_template(dynamic_name, None, Some(&rules)).is_ok());

        let mut unknown_rules = HashMap::new();
        unknown_rules.insert(
            "c-grid".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![],
                allowed_slots: Some(vec!["row".to_string()]),
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        let unknown_rules = Rc::new(unknown_rules);
        let unknown_shape =
            r#"<c-grid><c-fill name="row" data="{ missing }">body</c-fill></c-grid>"#;
        assert!(parse_template(unknown_shape, None, Some(&unknown_rules)).is_ok());
    }

    #[test]
    fn test_typed_slot_data_uses_effective_rightmost_providers() {
        let rules = rules_with_slot_data("row", &["item"]);

        let dynamic_data = r#"<c-grid><c-fill data="{ missing }" c-bind="attrs" name="row">body</c-fill></c-grid>"#;
        assert!(parse_template(dynamic_data, None, Some(&rules)).is_ok());

        let direct_data = r#"<c-grid><c-fill c-bind="attrs" name="row" data="{ missing }">body</c-fill></c-grid>"#;
        let error = parse_template(direct_data, None, Some(&rules)).unwrap_err();
        assert!(error
            .to_string()
            .contains("does not expose a slot-data field named 'missing'"));
    }

    #[test]
    fn test_fill_destructured_targets_follow_source_order_around_c_bind() {
        let template = parse_template(
            r#"<c-my-comp><c-fill name="header" data="{x}" c-bind="attrs">{{ x }}</c-fill></c-my-comp>"#,
            None,
            None,
        )
        .unwrap();
        assert_eq!(
            template
                .used_variables
                .iter()
                .map(|var| var.content.as_str())
                .collect::<Vec<_>>(),
            vec!["x", "attrs"]
        );

        let template = parse_template(
            r#"<c-my-comp><c-fill name="header" c-bind="attrs" data="{x as y, **rest}">{{ y }}{{ rest }}</c-fill></c-my-comp>"#,
            None,
            None,
        )
        .unwrap();
        assert_eq!(
            template
                .used_variables
                .iter()
                .map(|var| var.content.as_str())
                .collect::<Vec<_>>(),
            vec!["attrs"]
        );
    }

    #[test]
    fn test_fill_introduced_vars_follow_source_order_around_c_bind() {
        let template = parse_template(
            r#"<c-my-comp><c-fill name="header" data="x" c-bind="attrs">{{ x }}</c-fill></c-my-comp>"#,
            None,
            None,
        )
        .unwrap();
        let used_var_names: Vec<&str> = template
            .used_variables
            .iter()
            .map(|var| var.content.as_str())
            .collect();
        assert_eq!(used_var_names, vec!["x", "attrs"]);

        let template = parse_template(
            r#"<c-my-comp><c-fill name="header" c-bind="attrs" data="x">{{ x }}</c-fill></c-my-comp>"#,
            None,
            None,
        )
        .unwrap();
        let used_var_names: Vec<&str> = template
            .used_variables
            .iter()
            .map(|var| var.content.as_str())
            .collect();
        assert_eq!(used_var_names, vec!["attrs"]);

        let template = parse_template(
            r#"<c-my-comp><c-fill name="header" data="x" c-bind="attrs" fallback="y">{{ x }}{{ y }}</c-fill></c-my-comp>"#,
            None,
            None,
        )
        .unwrap();
        let used_var_names: Vec<&str> = template
            .used_variables
            .iter()
            .map(|var| var.content.as_str())
            .collect();
        assert_eq!(used_var_names, vec!["x", "attrs"]);
    }

    #[test]
    fn test_slot_and_fill_static_names_must_be_nonempty() {
        let inputs = [
            "<c-slot name />",
            r#"<c-slot name="" />"#,
            r#"<c-slot name="   " />"#,
            "<c-my-comp><c-fill name>body</c-fill></c-my-comp>",
            r#"<c-my-comp><c-fill name="">body</c-fill></c-my-comp>"#,
            r#"<c-my-comp><c-fill name="   ">body</c-fill></c-my-comp>"#,
        ];

        for input in inputs {
            assert_parse_error(input, "static 'name' must have a non-empty value");
        }
    }

    #[test]
    fn test_slot_without_name_is_default_slot() {
        // A <c-slot> with no name-providing attribute is the default slot,
        // collected in template.slots under the name "default".
        let template = parse_template("<c-slot />", None, None).unwrap();
        assert_eq!(template.slots.len(), 1);
        assert_eq!(template.slots[0].token.content, "default");
        assert_eq!(template.slots[0].required, Some(false));

        // The synthesized name token is anchored at the start-tag token
        // (there is no name in the source to point at).
        assert_eq!(template.slots[0].token.start_index, 0);
        assert_eq!(template.slots[0].token.end_index, 10);

        // The required flag works on the bare form too.
        let template = parse_template("<c-slot required>fb</c-slot>", None, None).unwrap();
        assert_eq!(template.slots.len(), 1);
        assert_eq!(template.slots[0].token.content, "default");
        assert_eq!(template.slots[0].required, Some(true));

        // A dynamic name (c-name, or c-bind which may supply one) is not
        // statically known, so the slot is not collected.
        let template = parse_template(r#"<c-slot c-name="x" />"#, None, None).unwrap();
        assert_eq!(template.slots.len(), 0);
        let template = parse_template(r#"<c-slot c-bind="b" />"#, None, None).unwrap();
        assert_eq!(template.slots.len(), 0);

        // c-required makes requiredness unknown, but the name stays static.
        let template =
            parse_template(r#"<c-slot name="hdr" c-required="x" />"#, None, None).unwrap();
        assert_eq!(template.slots.len(), 1);
        assert_eq!(template.slots[0].token.content, "hdr");
        assert_eq!(template.slots[0].required, None);
    }

    #[test]
    fn test_slot_metadata_follows_source_order() {
        let template = parse_template(
            r#"<c-slot c-bind="attrs" name="header" required />"#,
            None,
            None,
        )
        .unwrap();
        assert_eq!(template.slots.len(), 1);
        assert_eq!(template.slots[0].token.content, "header");
        assert_eq!(template.slots[0].required, Some(true));

        let template = parse_template(
            r#"<c-slot name="header" required c-bind="attrs" />"#,
            None,
            None,
        )
        .unwrap();
        assert!(template.slots.is_empty());
    }

    #[test]
    fn test_slot_explicit_logical_providers_conflict() {
        for input in [
            r#"<c-slot name="header" c-name="dynamic" />"#,
            r#"<c-slot c-name="dynamic" name="header" />"#,
            r#"<c-slot required c-required="dynamic" />"#,
            r#"<c-slot c-required="dynamic" required />"#,
        ] {
            assert_parse_error(input, "same logical attribute");
        }
    }

    #[test]
    fn test_comments_and_multiple_whitespace_nodes_are_not_implicit_content() {
        let mut rules = HashMap::new();
        rules.insert(
            "c-a".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![],
                allowed_slots: Some(vec!["header".to_string()]),
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        let rules = Rc::new(rules);
        let input = "<c-a>\n  {# first #}\n  {# second #}\n</c-a>";
        let result = parse_template(input, None, Some(&rules));
        assert!(
            result.is_ok(),
            "comments and formatting whitespace are not a default fill: {:?}",
            result.err()
        );

        let mut required_rules = HashMap::new();
        required_rules.insert(
            "c-a".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![],
                allowed_slots: Some(vec!["default".to_string()]),
                required_slots: vec!["default".to_string()],
                slot_data_fields: Default::default(),
            },
        );
        let required_rules = Rc::new(required_rules);
        let error = parse_template(input, None, Some(&required_rules)).unwrap_err();
        assert!(
            error.to_string().contains("requires 1 slot(s), but only 0"),
            "comments and formatting whitespace must not satisfy a required default slot: {error}"
        );
    }

    #[test]
    fn test_fill_cannot_mix_with_text_or_expr() {
        // Non-whitespace text before a fill
        let input = r#"<c-my-comp>text<c-fill name="x">hi</c-fill></c-my-comp>"#;
        assert_parse_error(input, "Text cannot appear next to '<c-fill>'");

        // Non-whitespace text after a fill
        let input = r#"<c-my-comp><c-fill name="x">hi</c-fill>tail</c-my-comp>"#;
        assert_parse_error(input, "Text cannot appear next to '<c-fill>'");

        // An expression next to a fill
        let input = r#"<c-my-comp>{{ x }}<c-fill name="x">hi</c-fill></c-my-comp>"#;
        assert_parse_error(input, "Expression cannot appear next to '<c-fill>'");

        // Whitespace-only text around fills is fine (formatting only; the
        // runtime neither captures nor renders it).
        let input = "<c-my-comp>\n  <c-fill name=\"x\">hi</c-fill>\n</c-my-comp>";
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Whitespace around fills should parse: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_group_content_checked_inside_control_flow() {
        // Text next to a fill INSIDE a control flow tag (no direct fill sibling
        // at the top level, so the per-sibling check alone would miss it).
        let input =
            r#"<c-my-comp><c-if cond="x">text<c-fill name="a">hi</c-fill></c-if></c-my-comp>"#;
        assert_parse_error(input, "Text cannot appear next to '<c-fill>'");

        // A non-fill tag inside a control flow sibling, where the fills live in
        // a DIFFERENT control flow tag (again no direct fill sibling).
        let input = r#"<c-my-comp><c-if cond="x"><c-fill name="a">hi</c-fill></c-if><c-if cond="y"><div>hi</div></c-if></c-my-comp>"#;
        assert_parse_error(input, "Tag '<div>' cannot appear next to '<c-fill>'");
    }

    #[test]
    fn test_fill_duplicate_names() {
        // Duplicate static fill names should always fail, even without user-defined rules
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-fill name="header">B</c-fill></c-my-comp>"#;
        assert_parse_error(input, "Duplicate");

        // Dynamic expressions are resolved at runtime, so identical source
        // does not prove that two fills resolve to the same name.
        let input = r#"<c-my-comp><c-fill c-name="slot_var">A</c-fill><c-fill c-name="slot_var">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Repeated dynamic fill expressions should parse: {:?}",
            result.err()
        );

        // The same expression can be stateful and return a different name on
        // each evaluation.
        let input = r#"<c-my-comp><c-fill c-name="next(names)">A</c-fill><c-fill c-name="next(names)">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Repeated stateful fill expressions should parse: {:?}",
            result.err()
        );

        // Different names are fine
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-fill name="footer">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Different fill names should succeed: {:?}",
            result.err()
        );

        // The same name in mutually exclusive control flow branches is fine:
        // at most one branch materializes at runtime. (Duplicates that DO
        // materialize together are caught at runtime, during fill collection.)
        let input = r#"<c-my-comp><c-if cond="x"><c-fill name="header">A</c-fill></c-if><c-else><c-fill name="header">B</c-fill></c-else></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Same fill name in exclusive branches should succeed: {:?}",
            result.err()
        );

        // Same rule for a control-flow fill duplicating a top-level one: the
        // parser cannot know whether the branch is taken, so it defers to the
        // runtime check.
        let input = r#"<c-my-comp><c-fill name="header">A</c-fill><c-if cond="x"><c-fill name="header">B</c-fill></c-if></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Control-flow fill duplicating a top-level fill parses (runtime checks it): {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_static_and_dynamic_name_conflict() {
        for input in [
            r#"<c-my-comp><c-fill name="fallback" c-name="slot_name">A</c-fill></c-my-comp>"#,
            r#"<c-my-comp><c-fill c-name="slot_name" name="fallback">A</c-fill></c-my-comp>"#,
        ] {
            assert_parse_error(input, "must have only one of the attributes: name, c-name");
        }
    }

    // #######################################
    // FILL OVERFLOW DETECTION
    // Overflow happens when there are more dynamic fills than allowed slots.
    // #######################################

    #[test]
    fn test_fill_overflow_all_slots_filled_plus_dynamic() {
        // allowed_slots=["h", "f"], 2 static fills + 1 dynamic fill (not in control flow) -> error
        // The dynamic fill will either duplicate an existing slot or use a non-allowed name.
        let mut rules = HashMap::new();
        rules.insert(
            "c-a".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![],
                allowed_slots: Some(vec!["h".to_string(), "f".to_string()]),
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        let rules_rc = Rc::new(rules);

        let input = r#"<c-a><c-fill name="h">X</c-fill><c-fill name="f">Y</c-fill><c-fill c-name="some_var">Z</c-fill></c-a>"#;
        let result = parse_template(input, None, Some(&rules_rc));
        let err = result.unwrap_err();
        let err_msg = format!("{}", err);
        assert!(
            err_msg.contains("slot(s)"),
            "Expected 'slot(s)' in overflow error, got: {}",
            err_msg
        );
    }

    #[test]
    fn test_fill_overflow_one_remaining_slot() {
        // allowed_slots=["h", "f"], 1 static fill + 1 dynamic fill -> ok (1 remaining slot)
        let mut rules = HashMap::new();
        rules.insert(
            "c-a".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![],
                allowed_slots: Some(vec!["h".to_string(), "f".to_string()]),
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        let rules_rc = Rc::new(rules);

        let input = r#"<c-a><c-fill name="h">X</c-fill><c-fill c-name="some_var">Z</c-fill></c-a>"#;
        let result = parse_template(input, None, Some(&rules_rc));
        assert!(
            result.is_ok(),
            "1 static fill + 1 dynamic fill with 2 allowed slots should succeed (1 remaining): {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_overflow_single_allowed_slot() {
        // allowed_slots=["h"], 1 static fill + 1 dynamic fill -> error (0 remaining)
        let mut rules = HashMap::new();
        rules.insert(
            "c-a".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![],
                allowed_slots: Some(vec!["h".to_string()]),
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        let rules_rc = Rc::new(rules);

        let input = r#"<c-a><c-fill name="h">X</c-fill><c-fill c-name="some_var">Z</c-fill></c-a>"#;
        let result = parse_template(input, None, Some(&rules_rc));
        let err = result.unwrap_err();
        let err_msg = format!("{}", err);
        assert!(
            err_msg.contains("slot(s)"),
            "Expected 'slot(s)' in overflow error, got: {}",
            err_msg
        );
    }

    #[test]
    fn test_fill_overflow_dynamic_inside_control_flow_excluded() {
        // allowed_slots=["h"], 1 static fill + 1 dynamic fill inside <c-if> -> ok
        // Fills inside control flow are excluded from the overflow check.
        let mut rules = HashMap::new();
        rules.insert(
            "c-a".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![],
                allowed_slots: Some(vec!["h".to_string()]),
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        let rules_rc = Rc::new(rules);

        // Static fill at top level + dynamic fill inside c-if (excluded from overflow)
        let input = r#"<c-a><c-fill name="h">X</c-fill><c-if cond="x"><c-fill c-name="some_var">Z</c-fill></c-if></c-a>"#;
        let result = parse_template(input, None, Some(&rules_rc));
        assert!(
            result.is_ok(),
            "Dynamic fill inside c-if should be excluded from overflow check: {:?}",
            result.err()
        );

        // Compare: same fills NOT inside control flow would fail (tested in test_fill_overflow_single_allowed_slot)
    }

    #[test]
    fn test_fill_overflow_dynamic_cbind_outside_control_flow() {
        // allowed_slots=["h"], 1 static fill + 1 c-bind fill (not in control flow) -> error
        let mut rules = HashMap::new();
        rules.insert(
            "c-a".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![],
                allowed_slots: Some(vec!["h".to_string()]),
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        let rules_rc = Rc::new(rules);

        let input = r#"<c-a><c-fill name="h">X</c-fill><c-fill c-bind="my_dict">Z</c-fill></c-a>"#;
        let result = parse_template(input, None, Some(&rules_rc));
        let err = result.unwrap_err();
        let err_msg = format!("{}", err);
        assert!(
            err_msg.contains("slot(s)"),
            "Expected 'slot(s)' in overflow error with c-bind, got: {}",
            err_msg
        );
    }

    #[test]
    fn test_fill_overflow_dynamic_inside_c_for_excluded() {
        // allowed_slots=["h"], 1 static fill + 1 dynamic fill inside <c-for> -> ok
        let mut rules = HashMap::new();
        rules.insert(
            "c-a".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![],
                allowed_slots: Some(vec!["h".to_string()]),
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        let rules_rc = Rc::new(rules);

        // Static fill at top level + dynamic fill inside c-for (excluded from overflow)
        let input = r#"<c-a><c-fill name="h">X</c-fill><c-for each="s in slots"><c-fill c-name="s">Z</c-fill></c-for></c-a>"#;
        let result = parse_template(input, None, Some(&rules_rc));
        assert!(
            result.is_ok(),
            "Dynamic fill inside c-for should be excluded from overflow check: {:?}",
            result.err()
        );
    }

    // #######################################
    // FILL IDENTITY AND DUPLICATE c-bind
    // #######################################

    #[test]
    fn test_fill_repeated_cbind_source_parses() {
        // A spread is evaluated for each fill, so identical source does not
        // imply identical resolved names.
        let input =
            r#"<c-my-comp><c-fill c-bind="x">A</c-fill><c-fill c-bind="x">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Repeated c-bind expressions should parse: {:?}",
            result.err()
        );

        let input = r#"<c-my-comp><c-fill c-bind="next(bindings)">A</c-fill><c-fill c-bind="next(bindings)">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Repeated stateful c-bind expressions should parse: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_duplicate_cbind_different_values() {
        // Two <c-fill> with different c-bind values -> ok (different identities)
        let input =
            r#"<c-my-comp><c-fill c-bind="x">A</c-fill><c-fill c-bind="y">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Different c-bind values should succeed: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_repeated_cbind_tuple_parses() {
        // Even the same sequence of spreads may resolve differently on each
        // fill because evaluation is stateful.
        let input = r#"<c-my-comp><c-fill c-bind="a" c-bind="b">A</c-fill><c-fill c-bind="a" c-bind="b">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Repeated c-bind tuples should parse: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_duplicate_cbind_different_order() {
        // Two <c-fill> with same c-bind values in different order -> ok (can resolve to different values, so different identity tuples)
        let input = r#"<c-my-comp><c-fill c-bind="a" c-bind="b">A</c-fill><c-fill c-bind="b" c-bind="a">B</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "c-bind with different order should succeed (different identity): {:?}",
            result.err()
        );
    }

    // #######################################
    // FILL IDENTITY RESOLUTION
    // #######################################

    #[test]
    fn test_fill_identity_cbind_then_name_resolves_to_static() {
        // <c-fill c-bind="b" name="a"> -> rightmost is `name` -> StaticName("a")
        // <c-fill name="a"> -> also StaticName("a")
        // Both resolve to StaticName("a"), so this is a duplicate -> error
        let input = r#"<c-my-comp><c-fill c-bind="b" name="a">X</c-fill><c-fill name="a">Y</c-fill></c-my-comp>"#;
        assert_parse_error(input, "Duplicate");
    }

    #[test]
    fn test_fill_identity_name_then_cbind_is_dynamic() {
        // <c-fill name="a" c-bind="b"> -> rightmost is `c-bind` -> dynamic
        // <c-fill name="a"> -> StaticName("a")
        // Different identity types -> ok (not a duplicate)
        let input = r#"<c-my-comp><c-fill name="a" c-bind="b">X</c-fill><c-fill name="a">Y</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "name='a' c-bind='b' (dynamic) vs name='a' (static) should not be duplicates: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_identity_cbind_cbind_cname_is_dynamic() {
        // <c-fill c-bind="c" c-bind="b" c-name="a"> -> rightmost is `c-name` -> dynamic
        // <c-fill c-name="a"> -> also dynamic
        // Dynamic identities are compared only after runtime resolution.
        let input = r#"<c-my-comp><c-fill c-bind="c" c-bind="b" c-name="a">X</c-fill><c-fill c-name="a">Y</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Dynamic identities with identical source should parse: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_identity_cbind_name_cbind_is_dynamic() {
        // <c-fill c-bind="c" name="a" c-bind="b"> -> rightmost is `c-bind`
        // This is a unique identity, should not conflict with a simple StaticName("a")
        let input = r#"<c-my-comp><c-fill c-bind="c" name="a" c-bind="b">X</c-fill><c-fill name="a">Y</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "A final c-bind vs a final static name should defer only the dynamic identity: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_identity_cbind_cname_cbind_is_dynamic() {
        // <c-fill c-bind="c" c-name="a" c-bind="b"> -> rightmost is `c-bind`
        // Dynamic identities do not participate in parse-time equality.
        let input = r#"<c-my-comp><c-fill c-bind="c" c-name="a" c-bind="b">X</c-fill><c-fill c-name="a">Y</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Dynamic fill identities should not be compared at parse time: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_fill_identity_two_cbinds_only() {
        // <c-fill c-bind="c" c-bind="b"> -> rightmost is `c-bind`
        // Two identical authored spreads are still resolved independently.
        let input = r#"<c-my-comp><c-fill c-bind="c" c-bind="b">X</c-fill><c-fill c-bind="c" c-bind="b">Y</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Repeated dynamic bind identities should parse: {:?}",
            result.err()
        );

        // But different order should be ok
        let input = r#"<c-my-comp><c-fill c-bind="c" c-bind="b">X</c-fill><c-fill c-bind="b" c-bind="c">Y</c-fill></c-my-comp>"#;
        let result = parse_template(input, None, None);
        assert!(
            result.is_ok(),
            "Different c-bind order should not be duplicates: {:?}",
            result.err()
        );
    }

    #[test]
    fn test_vue_slot_template_in_component_body_is_rejected() {
        // Each Vue slot spelling names the `<c-fill>` to write instead.
        let cases = [
            (
                "<c-card><template #title>x</template></c-card>",
                r#"Vue slot syntax '<template #title>' does not fill a slot of <c-card>; use '<c-fill name="title">' instead."#,
            ),
            (
                "<c-card><template v-slot:title>x</template></c-card>",
                r#"'<template v-slot:title>' does not fill a slot of <c-card>; use '<c-fill name="title">'"#,
            ),
            (
                "<c-card><template v-slot>x</template></c-card>",
                r#"'<template v-slot>' does not fill a slot of <c-card>; use '<c-fill name="default">'"#,
            ),
            (
                "<c-card><template v-slot.foo>x</template></c-card>",
                r#"'<template v-slot.foo>' does not fill a slot of <c-card>; use '<c-fill name="default">'"#,
            ),
            (
                "<c-card><template #default>x</template></c-card>",
                r#"'<template #default>' does not fill a slot of <c-card>; use '<c-fill name="default">'"#,
            ),
            (
                "<c-card><template #[name]>x</template></c-card>",
                r#"use '<c-fill c-name="...">' with the slot name as a Python expression instead."#,
            ),
            (
                "<c-card><template #[a.b]>x</template></c-card>",
                r#"use '<c-fill c-name="...">' with the slot name as a Python expression"#,
            ),
            // Every letter case is rejected: any spelling is a mistake here.
            (
                "<c-card><template V-SLOT:title>x</template></c-card>",
                r#"'<template V-SLOT:title>' does not fill a slot of <c-card>; use '<c-fill name="title">'"#,
            ),
            (
                "<c-card><template v-Slot:title>x</template></c-card>",
                r#"'<template v-Slot:title>' does not fill a slot of <c-card>"#,
            ),
            (
                "<c-card><TEMPLATE #title>x</TEMPLATE></c-card>",
                r#"'<TEMPLATE #title>' does not fill a slot of <c-card>"#,
            ),
            // Vue slot props point at the fill's `data` attribute.
            (
                r#"<c-card><template #item="{ row }">x</template></c-card>"#,
                r#"use '<c-fill name="item">' instead. Read Vue slot props with the fill's 'v-slot="{ ... }"', or Python slot data with its 'data="..."'."#,
            ),
            (
                r#"<c-card><template c-v-slot:title="x">x</template></c-card>"#,
                r#"'<template c-v-slot:title>' does not fill a slot of <c-card>; use '<c-fill name="title">' instead."#,
            ),
            // Slot syntax on an element other than `<template>` is the same mistake.
            (
                "<c-card><div #title>x</div></c-card>",
                r#"Vue slot syntax '<div #title>' does not fill a slot of <c-card>; use '<c-fill name="title">' instead."#,
            ),
            (
                r#"<c-card><span v-slot:title="{ a }">x</span></c-card>"#,
                r#"'<span v-slot:title>' does not fill a slot of <c-card>"#,
            ),
            (
                r#"<c-card><c-element is="div" #title>x</c-element></c-card>"#,
                r#"'<c-element #title>' does not fill a slot of <c-card>"#,
            ),
            // `<c-provide>` and `<c-cache>` render their body in place, so
            // the template still lands in the outer component's body.
            (
                r#"<c-card><c-provide key="k"><template #title>x</template></c-provide></c-card>"#,
                "does not fill a slot of <c-card>",
            ),
            (
                r#"<c-card><c-cache key="k"><template #title>x</template></c-cache></c-card>"#,
                "does not fill a slot of <c-card>",
            ),
            // `<c-mark>` renders its own boundary.
            (
                r#"<my-widget><c-mark name="m"><template #title>x</template></c-mark></my-widget>"#,
                "does not fill a slot of <c-mark>",
            ),
            // Control flow renders its content in place, so the `<template>`
            // still lands directly in the component body.
            (
                r#"<c-card><c-if cond="x"><template #title>x</template></c-if></c-card>"#,
                "does not fill a slot of <c-card>",
            ),
            (
                r#"<c-card><c-for each="i in xs"><template #title>x</template></c-for></c-card>"#,
                "does not fill a slot of <c-card>",
            ),
            (
                r#"<c-component is="card"><template #title>x</template></c-component>"#,
                "does not fill a slot of <c-component>",
            ),
            (
                r#"<c-outer><c-fill name="body"><c-card><template #title>x</template></c-card></c-fill></c-outer>"#,
                "does not fill a slot of <c-card>",
            ),
        ];
        for (input, message) in cases {
            assert_parse_error(input, message);
        }
    }

    #[test]
    fn test_vue_slot_template_c_form_has_no_slot_props_hint() {
        // A `c-` form's value is a Python expression, not Vue slot props.
        let error = parse_template(
            r#"<c-card><template c-v-slot:title="x">x</template></c-card>"#,
            None,
            None,
        )
        .unwrap_err()
        .to_string();
        assert!(!error.contains("Read Vue slot props"), "{error}");
    }

    #[test]
    fn test_vue_slot_template_reports_the_attribute_position() {
        let error = parse_template(
            "<c-card>\n  <template #title>x</template>\n</c-card>",
            None,
            None,
        )
        .unwrap_err()
        .to_string();
        assert!(error.contains("--> 2:13"), "{error}");
    }

    #[test]
    fn test_vue_slot_template_outside_citry_component_body_parses() {
        let inputs = [
            // A `<template>` without slot syntax is ordinary default-slot content.
            "<c-card><template>plain</template></c-card>",
            "<c-card><template #c-ignore>x</template></c-card>",
            // `v-slots` names another directive.
            "<c-card><template v-slots>x</template></c-card>",
            // `<c-element>` and a non-`c-` tag may be Vue components that a
            // plugin registers.
            r#"<c-element is="my-widget"><template #header>x</template></c-element>"#,
            "<my-widget><template #header>x</template></my-widget>",
            "<c-card><my-widget><template #header>x</template></my-widget></c-card>",
            // `<c-provide>` passes its body to the tag around it, here a
            // possible plugin Vue component.
            r#"<my-widget><c-provide key="k"><template #header>H</template></c-provide></my-widget>"#,
            r#"<c-provide key="k"><template #header>H</template></c-provide>"#,
            // Slot syntax on other elements outside a Citry component tag is
            // left to Vue.
            "<div><span #title>x</span></div>",
            "<my-widget><div #title>x</div></my-widget>",
            // The root of a template, a fill, or a slot fallback can reach a
            // Vue component through a transparent component, such as
            // `<c-provide>`, that the parser cannot see.
            "<template #title>T</template>",
            r#"<c-card><c-fill name="body"><template #title>x</template></c-fill></c-card>"#,
            r#"<c-slot name="s"><template #title>x</template></c-slot>"#,
            // Under a plain element, Vue decides what the slot syntax means.
            "<div><template #title>T</template></div>",
            "<c-card><div><template #title>x</template></div></c-card>",
        ];
        for input in inputs {
            let result = parse_template(input, None, None);
            assert!(result.is_ok(), "{input}: {:?}", result.err());
        }
    }

    /// Every node's tag name and `contains_fills` flag, parents first.
    fn fill_flags(template: &Template) -> Vec<(String, bool)> {
        let mut flags = Vec::new();
        for element in &template.elements {
            if let TemplateElement::Node(node) = element {
                flags.push((node.tag_name().to_string(), node.contains_fills()));
                if let Node::WithBody { body, .. } = node {
                    flags.extend(fill_flags(body));
                }
            }
        }
        flags
    }

    #[test]
    fn test_contains_fills_reaches_through_nested_control_flow() {
        // The parser sets each node's flag from its children's flags, so a
        // fill two control-flow levels down must still mark every level
        // above it. A control-flow tag whose body holds only a plain element
        // stays false.
        let template = parse_template(
            r#"<c-card><c-if cond="a"><c-for each="i in xs"><c-fill c-name="i">x</c-fill></c-for></c-if><c-else><c-fill name="b">y</c-fill></c-else></c-card><c-if cond="z"><div>no fill</div></c-if>"#,
            None,
            None,
        )
        .unwrap();
        let expected = [
            ("c-card", true),
            ("c-if", true),
            ("c-for", true),
            ("c-fill", false),
            ("c-else", true),
            ("c-fill", false),
            ("c-if", false),
            ("div", false),
        ];
        let expected: Vec<(String, bool)> = expected
            .iter()
            .map(|(tag, flag)| (tag.to_string(), *flag))
            .collect();
        assert_eq!(fill_flags(&template), expected);
    }
}
