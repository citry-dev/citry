// Parser contract for Citry's `$c-props` component-boundary directive.
//
// A0 reserves two exact authored spellings. `$c-props` carries an inert
// browser expression, while `c-$c-props` carries a Python expression whose
// result is the complete browser expression. Both are valid only on Citry
// component tags. A `$c-props` mapping key supplied by `c-bind` is enforced
// later because mapping keys do not exist at parse time.

mod common;

#[cfg(test)]
mod tests {
    use std::collections::HashMap;
    use std::rc::Rc;

    use citry_template_parser::ast::HtmlAttrKind;
    use citry_template_parser::parser::parse_template;
    use citry_template_parser::parser_context::TagRules;

    use super::common::{assert_parse_error, parse_first_node};

    #[test]
    fn test_direct_form_is_static_with_exact_source_spans() {
        let node = parse_first_node(r#"<c-child $c-props="{ count: localCount }" />"#).unwrap();
        let attr = &node.attrs()[0];

        assert_eq!(attr.kind, HtmlAttrKind::Static);
        assert_eq!(attr.token.content, r#"$c-props="{ count: localCount }""#);
        assert_eq!((attr.token.start_index, attr.token.end_index), (9, 41));
        assert_eq!(attr.token.line_col, (1, 10));
        assert_eq!(attr.key.content, "$c-props");
        assert_eq!((attr.key.start_index, attr.key.end_index), (9, 17));
        assert_eq!(
            attr.inner_value.as_ref().unwrap().content,
            "{ count: localCount }"
        );
        assert_eq!(
            (
                attr.inner_value.as_ref().unwrap().start_index,
                attr.inner_value.as_ref().unwrap().end_index,
            ),
            (19, 40)
        );
        assert!(attr.used_variables.is_empty());
    }

    #[test]
    fn test_server_dynamic_form_is_python_expression_with_exact_source_spans() {
        let node = parse_first_node(r#"<c-child c-$c-props="props_source" />"#).unwrap();
        let attr = &node.attrs()[0];

        assert_eq!(attr.kind, HtmlAttrKind::Expression);
        assert_eq!(attr.token.content, r#"c-$c-props="props_source""#);
        assert_eq!((attr.token.start_index, attr.token.end_index), (9, 34));
        assert_eq!(attr.token.line_col, (1, 10));
        assert_eq!(attr.key.content, "c-$c-props");
        assert_eq!((attr.key.start_index, attr.key.end_index), (9, 19));
        assert_eq!(attr.inner_value.as_ref().unwrap().content, "props_source");
        assert_eq!(attr.used_variables.len(), 1);
        assert_eq!(attr.used_variables[0].content, "props_source");
        assert_eq!(
            (
                attr.used_variables[0].start_index,
                attr.used_variables[0].end_index,
            ),
            (21, 33)
        );
    }

    #[test]
    fn test_direct_dynamic_and_spread_forms_resolve_in_source_order() {
        for input in [
            r#"<c-child $c-props="first" c-$c-props="second" />"#,
            r#"<c-child c-$c-props="second" $c-props="first" />"#,
            r#"<c-child $c-props="first" c-bind="spread" />"#,
            r#"<c-child c-$c-props="second" c-bind="spread" />"#,
        ] {
            assert!(parse_template(input, None, None).is_ok());
        }
    }

    #[test]
    fn test_component_and_dynamic_component_accept_both_forms() {
        for input in [
            r#"<c-child $c-props="{ count: 1 }" />"#,
            r#"<c-child c-$c-props="expr" />"#,
            r#"<c-component is="child" $c-props="{ count: 1 }" />"#,
            r#"<c-component c-is="target" c-$c-props="expr" />"#,
        ] {
            assert!(
                parse_template(input, None, None).is_ok(),
                "input should parse: {input:?}"
            );
        }
    }

    #[test]
    fn test_client_props_bypasses_component_kwarg_allowlist() {
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
        let rules = Rc::new(rules);

        assert!(parse_template(
            r#"<c-child title="ok" $c-props="{ count: 1 }" c-bind="spread" />"#,
            None,
            Some(&rules),
        )
        .is_ok());
    }

    #[test]
    fn test_client_props_does_not_satisfy_required_python_kwarg() {
        let mut rules = HashMap::new();
        rules.insert(
            "c-child".to_string(),
            TagRules {
                allowed_attrs: None,
                required_attrs: vec![vec!["title".to_string()]],
                allowed_slots: None,
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        let rules = Rc::new(rules);

        let err = parse_template(r#"<c-child $c-props="{ count: 1 }" />"#, None, Some(&rules))
            .unwrap_err();
        assert!(format!("{err}").contains("must have a 'title' attribute"));
    }

    #[test]
    fn test_direct_form_rejects_missing_empty_and_whitespace_values() {
        for input in [
            "<c-child $c-props />",
            r#"<c-child $c-props="" />"#,
            r#"<c-child $c-props="   " />"#,
        ] {
            assert_parse_error(
                input,
                "'$c-props' must have a non-empty client expression value",
            );
        }
    }

    #[test]
    fn test_both_forms_reject_plain_element_and_c_element_placements() {
        for input in [
            r#"<div $c-props="{ count: 1 }"></div>"#,
            r#"<div c-$c-props="expr"></div>"#,
            r#"<x-card $c-props="{ count: 1 }"></x-card>"#,
            r#"<c-element is="div" $c-props="{ count: 1 }" />"#,
            r#"<c-Element is="div" $c-props="{ count: 1 }" />"#,
            r#"<c-element c-is="tag" c-$c-props="expr" />"#,
        ] {
            assert_parse_error(
                input,
                "is a client props directive and belongs on a Citry component tag",
            );
        }
    }

    #[test]
    fn test_both_forms_reject_reserved_citry_tags() {
        for input in [
            r#"<c-if cond="ok" $c-props="{ count: 1 }"></c-if>"#,
            r#"<c-IF cond="ok" $c-props="{ count: 1 }"></c-IF>"#,
            r#"<c-slot c-$c-props="expr" />"#,
            r#"<c-child><c-fill name="x" $c-props="{ count: 1 }"></c-fill></c-child>"#,
            r#"<c-raw $c-props="{ count: 1 }">x</c-raw>"#,
        ] {
            assert_parse_error(
                input,
                "is a client props directive and belongs on a Citry component tag",
            );
        }
    }

    #[test]
    fn test_case_variants_are_pointed_errors() {
        for input in [
            r#"<c-child $C-PROPS="{ count: 1 }" />"#,
            r#"<c-child c-$C-PROPS="expr" />"#,
        ] {
            assert_parse_error(input, "Citry client directive names are lowercase");
        }
    }

    #[test]
    fn test_only_exact_directive_names_are_reserved() {
        for input in [
            r#"<div $c-props-extra="ordinary" x-show="open"></div>"#,
            r#"<div c-$c-props-extra="expr" x-show="open"></div>"#,
        ] {
            assert!(parse_template(input, None, None).is_ok());
        }

        assert_parse_error(
            r#"<div $c-props-extra="ordinary" c-$c-props-extra="expr"></div>"#,
            "provide the same logical attribute '$c-props-extra'",
        );
    }

    #[test]
    fn test_exact_duplicate_direct_form_is_rejected() {
        assert_parse_error(
            r#"<c-child $c-props="first" $c-props="second" />"#,
            "Duplicate attribute '$c-props' found.",
        );
    }
}
