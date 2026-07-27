// Tests for the `#c-*` framework-metadata attribute channel (parser half).
//
// The channel has exactly two members: `#c-key="expr"` (expression-valued,
// server-evaluated) and the bare `#c-ignore` marker. They parse into
// `HtmlAttr` with `HtmlAttrKind::Meta`; every other `#c-*` name, a valueless
// `#c-key`, a valued `#c-ignore`, and either member on a tag that cannot
// carry it are parse errors. See docs/design/events.md section 5.1.

mod common;

#[cfg(test)]
mod tests {
    use std::collections::HashMap;
    use std::rc::Rc;

    use citry_template_parser::ast::HtmlAttrKind;
    use citry_template_parser::parser::parse_template;
    use citry_template_parser::parser_context::TagRules;

    use super::common::{
        assert_parse_error, meta_attr, meta_bool_attr, node_elem, parse_first_node,
        self_closing_node_vars, start_tag, static_attr, template_with_vars, token, with_used_vars,
    };

    // =============================================================================
    // AST SHAPE
    // =============================================================================

    #[test]
    fn test_meta_key_parses_as_meta_kind_with_expression_vars() {
        // <input #c-key="item.id" />
        // 0         1         2
        // 01234567890123456789012345
        let input = r#"<input #c-key="item.id" />"#;
        let result = parse_template(input, None, None).unwrap();

        let item_var = token("item", 15, 1, 16);

        let expected = template_with_vars(
            vec![node_elem(self_closing_node_vars(
                start_tag(
                    token(r#"<input #c-key="item.id" />"#, 0, 1, 1),
                    token("input", 1, 1, 2),
                    vec![with_used_vars(
                        meta_attr(token("#c-key", 7, 1, 8), token("item.id", 15, 1, 16)),
                        vec![item_var.clone()],
                    )],
                    true,
                ),
                vec![item_var.clone()],
            ))],
            vec![item_var],
        );

        assert_eq!(result, expected);
    }

    #[test]
    fn test_meta_ignore_parses_as_bare_meta_kind() {
        // <div #c-ignore>x</div>
        // 0         1         2
        // 0123456789012345678901
        let input = "<div #c-ignore>x</div>";
        let result = parse_template(input, None, None).unwrap();

        let node = match &result.elements[0] {
            citry_template_parser::ast::TemplateElement::Node(node) => node,
            other => panic!("expected a node, got {:?}", other),
        };
        let attrs = node.attrs();
        assert_eq!(attrs.len(), 1);
        assert_eq!(attrs[0], meta_bool_attr(token("#c-ignore", 5, 1, 6)));
        assert_eq!(attrs[0].kind, HtmlAttrKind::Meta);
        assert!(attrs[0].used_variables.is_empty());
    }

    #[test]
    fn test_hash_attr_outside_channel_stays_static() {
        // A `#`-prefixed name that is not `#c-*` is an ordinary attribute:
        // the channel reserves nothing outside its own prefix.
        // <div #foo="1">x</div>
        // 0         1         2
        // 012345678901234567890
        let input = r#"<div #foo="1">x</div>"#;
        let result = parse_template(input, None, None).unwrap();

        let node = match &result.elements[0] {
            citry_template_parser::ast::TemplateElement::Node(node) => node,
            other => panic!("expected a node, got {:?}", other),
        };
        let attrs = node.attrs();
        assert_eq!(attrs.len(), 1);
        assert_eq!(
            attrs[0],
            static_attr(token("#foo", 5, 1, 6), token("1", 11, 1, 12))
        );
        assert_eq!(attrs[0].kind, HtmlAttrKind::Static);
    }

    #[test]
    fn test_meta_key_allowed_on_component_tag() {
        let node = parse_first_node(r#"<c-Card #c-key="item.id" />"#).unwrap();
        let attrs = node.attrs();
        assert_eq!(attrs.len(), 1);
        assert_eq!(attrs[0].key.content, "#c-key");
        assert_eq!(attrs[0].kind, HtmlAttrKind::Meta);
        assert_eq!(attrs[0].used_variables.len(), 1);
        assert_eq!(attrs[0].used_variables[0].content, "item");
    }

    #[test]
    fn test_meta_key_and_ignore_can_share_an_element() {
        // A keyed element may also opt its subtree out of morphing; the two
        // members do not conflict.
        let node = parse_first_node(r#"<div #c-key="k" #c-ignore>x</div>"#).unwrap();
        let attrs = node.attrs();
        assert_eq!(attrs.len(), 2);
        assert_eq!(attrs[0].key.content, "#c-key");
        assert_eq!(attrs[1].key.content, "#c-ignore");
        assert!(attrs.iter().all(|attr| attr.kind == HtmlAttrKind::Meta));
    }

    #[test]
    fn test_meta_key_exempt_from_user_attr_rules() {
        // A component's declared attribute rules constrain its inputs.
        // `#c-key` is framework metadata, not an input, so a rules-restricted
        // component still accepts it.
        let mut rules = HashMap::new();
        rules.insert(
            "c-my-comp".to_string(),
            TagRules {
                allowed_attrs: Some(vec![vec!["id".to_string()]]),
                required_attrs: vec![],
                allowed_slots: None,
                required_slots: vec![],
                slot_data_fields: Default::default(),
            },
        );
        let rules_rc = Rc::new(rules);

        let input = r#"<c-my-comp id="1" #c-key="k"></c-my-comp>"#;
        let result = parse_template(input, None, Some(&rules_rc));
        assert!(
            result.is_ok(),
            "#c-key must bypass user attribute rules: {:?}",
            result.err()
        );
    }

    // =============================================================================
    // MEMBER ERRORS (unknown name, wrong value shape)
    // =============================================================================

    #[test]
    fn test_unknown_meta_name_is_error_naming_both_members() {
        assert_parse_error(
            r#"<div #c-bogus="1">x</div>"#,
            "Unknown '#c-*' attribute '#c-bogus'. The '#c-*' channel is reserved for framework metadata about the node, and has exactly two members: '#c-key' and '#c-ignore'.",
        );
    }

    #[test]
    fn test_bare_meta_prefix_is_error() {
        // `#c-` with nothing after it is still an unknown member.
        assert_parse_error(r#"<div #c-="1">x</div>"#, "Unknown '#c-*' attribute '#c-'.");
    }

    #[test]
    fn test_valueless_key_is_error() {
        assert_parse_error(
            "<div #c-key>x</div>",
            "'#c-key' must have an expression value whose result is the node's key, e.g. #c-key=\"item.id\".",
        );
    }

    #[test]
    fn test_empty_key_value_is_error() {
        assert_parse_error(
            r#"<div #c-key="">x</div>"#,
            "'#c-key' must have an expression value whose result is the node's key",
        );
    }

    #[test]
    fn test_whitespace_key_value_is_error() {
        assert_parse_error(
            r#"<div #c-key="   ">x</div>"#,
            "'#c-key' must have an expression value whose result is the node's key",
        );
    }

    #[test]
    fn test_valued_ignore_is_error() {
        assert_parse_error(
            r#"<div #c-ignore="yes">x</div>"#,
            "'#c-ignore' takes no value. Write the bare marker ('#c-ignore') to opt this element and its subtree out of morphing.",
        );
    }

    #[test]
    fn test_empty_valued_ignore_is_error() {
        // `#c-ignore=""` is still a valued spelling, rejected the same way.
        assert_parse_error(
            r#"<div #c-ignore="">x</div>"#,
            "'#c-ignore' takes no value.",
        );
    }

    #[test]
    fn test_duplicate_key_is_error() {
        assert_parse_error(
            r#"<div #c-key="a" #c-key="b">x</div>"#,
            "Duplicate attribute '#c-key' found.",
        );
    }

    // =============================================================================
    // PLACEMENT ERRORS
    // =============================================================================

    #[test]
    fn test_ignore_on_component_tag_is_error_pointing_at_fix() {
        assert_parse_error(
            r#"<c-Card #c-ignore />"#,
            "'#c-ignore' is not supported on '<c-Card>' (line 1, column 9): it would opt out a component instance's root element. Put it on an element inside the child's own template below the template's root element, or on a wrapper element around '<c-Card>'.",
        );
    }

    #[test]
    fn test_ignore_on_dynamic_component_tag_is_error() {
        // `<c-component>` renders a component instance, so the marker would
        // sit on an instance root there too.
        assert_parse_error(
            r#"<c-component is="Card" #c-ignore />"#,
            "'#c-ignore' is not supported on '<c-component>' (line 1, column 24)",
        );
    }

    #[test]
    fn test_ignore_on_reserved_tag_is_error() {
        assert_parse_error(
            r#"<c-if cond="x" #c-ignore>y</c-if>"#,
            "'#c-ignore' is not supported on '<c-if>' (line 1, column 16). Put it on the HTML element whose subtree should be left alone, or on a wrapper element.",
        );
    }

    #[test]
    fn test_ignore_on_raw_tag_is_error() {
        assert_parse_error(
            "<c-raw #c-ignore>y</c-raw>",
            "'#c-ignore' is not supported on '<c-raw>' (line 1, column 8).",
        );
    }

    #[test]
    fn test_key_on_slot_tag_is_error() {
        assert_parse_error(
            r#"<c-slot name="s" #c-key="k" />"#,
            "'#c-key' is not supported on '<c-slot>' (line 1, column 18). It belongs on a plain HTML element (the morph pairing key) or on a component tag (the key of the child instance).",
        );
    }

    #[test]
    fn test_key_on_control_flow_tag_is_error() {
        assert_parse_error(
            r#"<c-if cond="x" #c-key="k">y</c-if>"#,
            "'#c-key' is not supported on '<c-if>' (line 1, column 16).",
        );
    }

    #[test]
    fn test_key_on_fill_tag_is_error() {
        assert_parse_error(
            r#"<c-Card><c-fill name="f" #c-key="k">y</c-fill></c-Card>"#,
            "'#c-key' is not supported on '<c-fill>' (line 1, column 26).",
        );
    }

    #[test]
    fn test_key_on_raw_tag_is_error() {
        assert_parse_error(
            r#"<c-raw #c-key="k">y</c-raw>"#,
            "'#c-key' is not supported on '<c-raw>' (line 1, column 8).",
        );
    }

    #[test]
    fn test_placement_error_reports_real_template_location() {
        // The rendered snippet in the error covers only the attribute's own
        // text, so the message is what carries the template position; it
        // must be the attribute's real line and column in the template.
        assert_parse_error(
            "<div>\n  <c-if cond=\"x\" #c-key=\"k\">y</c-if>\n</div>",
            "'#c-key' is not supported on '<c-if>' (line 2, column 18).",
        );
    }
}
