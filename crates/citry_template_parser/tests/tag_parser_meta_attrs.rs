// Tests for the `#c-*` framework-metadata attribute channel (parser half).
//
// The channel has exactly two members: `#c-key="expr"` (expression-valued,
// server-evaluated) and the bare `#c-ignore` marker. They parse into
// `HtmlAttr` with `HtmlAttrKind::Meta`; every other `#c-*` name, a valueless
// `#c-key`, a valued `#c-ignore`, either member on a reserved structural
// tag, and a child component, slot, or Vue binding inside a `#c-ignore`
// element are parse errors. See docs/design/component_ranges_plan.md.

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
    fn test_meta_ignore_allowed_on_component_and_element_tags() {
        for input in [
            "<c-Card #c-ignore />",
            r#"<c-component is="Card" #c-ignore />"#,
            r#"<c-element c-is="tag" #c-ignore />"#,
        ] {
            let node = parse_first_node(input).unwrap();
            let ignore = node
                .attrs()
                .iter()
                .find(|attr| attr.key.content == "#c-ignore")
                .unwrap_or_else(|| panic!("missing #c-ignore in {input:?}"));
            assert_eq!(ignore.kind, HtmlAttrKind::Meta);
            assert!(ignore.inner_value.is_none());
        }
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
    fn test_meta_attrs_exempt_from_user_attr_rules() {
        // A component's declared attribute rules constrain its inputs.
        // `#c-*` is framework metadata, not an input, so a rules-restricted
        // component still accepts both members.
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

        let input = r#"<c-my-comp id="1" #c-key="k" #c-ignore></c-my-comp>"#;
        let result = parse_template(input, None, Some(&rules_rc));
        assert!(
            result.is_ok(),
            "#c-* must bypass user attribute rules: {:?}",
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
            "'#c-ignore' takes no value. Write the bare marker ('#c-ignore') on an HTML element to keep its contents as the server first rendered them.",
        );
    }

    #[test]
    fn test_valued_ignore_on_component_is_error() {
        assert_parse_error(
            r#"<c-Card #c-ignore="yes" />"#,
            "'#c-ignore' takes no value. Write the bare marker ('#c-ignore') on an HTML element to keep its contents as the server first rendered them.",
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
    fn test_ignore_on_reserved_tag_is_error() {
        assert_parse_error(
            r#"<c-if cond="x" #c-ignore>y</c-if>"#,
            "'#c-ignore' is not supported on '<c-if>' (line 1, column 16). Put it on a plain HTML element, whose contents the browser then keeps as the server first rendered them.",
        );
    }

    #[test]
    fn test_ignore_rejected_on_every_reserved_structural_tag() {
        let cases = [
            (r#"<c-if cond="x" #c-ignore />"#, "c-if"),
            (r#"<c-for each="x in xs" #c-ignore />"#, "c-for"),
            (r#"<c-slot name="s" #c-ignore />"#, "c-slot"),
            (
                r#"<c-Card><c-fill name="s" #c-ignore /></c-Card>"#,
                "c-fill",
            ),
            ("<c-raw #c-ignore>y</c-raw>", "c-raw"),
        ];

        for (input, tag_name) in cases {
            assert_parse_error(
                input,
                &format!("'#c-ignore' is not supported on '<{tag_name}>'"),
            );
        }
    }

    #[test]
    fn test_reserved_structural_tag_case_variants_get_spelling_error() {
        for (input, canonical) in [
            (r#"<c-If cond="x" #c-key="k" />"#, "c-if"),
            (r#"<c-For each="x in xs" #c-ignore />"#, "c-for"),
            (r#"<c-Slot name="s" #c-key="k" />"#, "c-slot"),
            (r#"<c-Raw #c-ignore>x</c-Raw>"#, "c-raw"),
        ] {
            assert_parse_error(
                input,
                &format!("Reserved Citry structural tags are lowercase. Write '<{canonical}>'"),
            );
        }
    }

    #[test]
    fn test_uppercase_citry_prefix_gets_pointed_error() {
        assert_parse_error(
            "<C-Card />",
            "Citry component tag prefixes are lowercase. Write '<c-Card>'",
        );
        assert_parse_error(
            "<c-Card></C-Card>",
            "Citry component tag prefixes are lowercase. Write '</c-Card>'",
        );
    }

    #[test]
    fn test_structural_closing_tag_requires_lowercase_spelling() {
        assert_parse_error(
            r#"<c-if cond="x">x</c-IF>"#,
            "Reserved Citry structural tags are lowercase. Write '</c-if>'",
        );
    }

    #[test]
    fn test_key_on_slot_tag_is_error() {
        assert_parse_error(
            r#"<c-slot name="s" #c-key="k" />"#,
            "'#c-key' is not supported on '<c-slot>' (line 1, column 18). It belongs on a plain HTML element or a component tag, where it is the key Vue uses to match that element or child instance across renders.",
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

    // =============================================================================
    // CONTENTS OF A #c-ignore ELEMENT
    // =============================================================================

    #[test]
    fn test_ignored_element_accepts_server_rendered_contents() {
        // Plain HTML, expressions, control flow, `<c-raw>`, a nested
        // `#c-key`, and a `c-for` shorthand all render once on the server.
        let input = concat!(
            r#"<div #c-ignore><canvas class="c"></canvas>{{ label }}"#,
            r#"<c-if cond="ok"><b>yes</b></c-if><c-else>no</c-else>"#,
            r#"<ul><li c-for="x in xs" #c-key="x">{{ x }}</li></ul>"#,
            r#"<c-raw><i>{{ raw }}</i></c-raw></div>"#,
        );
        parse_template(input, None, None).unwrap();
    }

    #[test]
    fn test_ignored_element_rejects_component_child() {
        assert_parse_error(
            "<div #c-ignore>\n  <c-Card />\n</div>",
            "'#c-ignore' on <div> (line 1, column 6) keeps the element's contents exactly as the server first rendered them, so they cannot hold <c-Card> (line 2, column 4): it needs Vue to render it. Inside a '#c-ignore' element, write plain HTML, '{{ }}' expressions, '<c-if>', '<c-for>', and '<c-raw>'. Move <c-Card> outside the <div> element.",
        );
    }

    #[test]
    fn test_ignored_element_rejects_citry_tags_that_need_vue() {
        for (input, tag_name) in [
            (r#"<div #c-ignore><c-slot name="s" /></div>"#, "c-slot"),
            (
                r#"<div #c-ignore><c-component is="Card" /></div>"#,
                "c-component",
            ),
            (
                r#"<div #c-ignore><c-element c-is="tag" /></div>"#,
                "c-element",
            ),
            (
                r#"<div #c-ignore><c-mark name="m">x</c-mark></div>"#,
                "c-mark",
            ),
            (
                r#"<div #c-ignore><p><c-if cond="x"><c-Card /></c-if></p></div>"#,
                "c-Card",
            ),
        ] {
            assert_parse_error(input, &format!("so they cannot hold <{tag_name}>"));
        }
    }

    #[test]
    fn test_ignored_element_rejects_vue_bindings_in_its_contents() {
        for (input, name) in [
            (
                r#"<div #c-ignore><button @click="go()">x</button></div>"#,
                "@click",
            ),
            (r#"<div #c-ignore><b :title="t">x</b></div>"#, ":title"),
            (r#"<div #c-ignore><p v-if="ok">x</p></div>"#, "v-if"),
            (
                r#"<div #c-ignore><p><b v-text="t"></b></p></div>"#,
                "v-text",
            ),
            (
                r#"<div #c-ignore><button @c-click="save">x</button></div>"#,
                "@c-click",
            ),
            (r#"<div #c-ignore><input :c-name /></div>"#, ":c-name"),
        ] {
            assert_parse_error(input, &format!("so the browser never runs '{name}'"));
        }
    }

    #[test]
    fn test_ignored_element_rejects_a_ref_with_the_way_to_reach_the_child() {
        assert_parse_error(
            r#"<div #c-ignore><canvas ref="chart"></canvas></div>"#,
            "'#c-ignore' on <div> (line 1, column 6) keeps the element's contents exactly as the server first rendered them, so the browser never runs 'ref' on <canvas> (line 1, column 24). Inside a '#c-ignore' element, write plain HTML, '{{ }}' expressions, '<c-if>', '<c-for>', and '<c-raw>'. Put the 'ref' on the <div> element itself and find the child from there, for example with this.$refs.<name>.querySelector(...).",
        );
    }

    #[test]
    fn test_ignored_element_keeps_its_own_vue_bindings() {
        // The element itself stays Vue-managed, so its own bindings are fine.
        parse_template(
            r#"<div #c-ignore ref="map" :class="cls" @click="go()"><p>x</p></div>"#,
            None,
            None,
        )
        .unwrap();
    }

    #[test]
    fn test_ignore_placements_without_element_contents_are_errors() {
        assert_parse_error(
            "<br #c-ignore>",
            "'#c-ignore' is not supported on <br> (line 1, column 5). <br> has no contents to keep. Remove '#c-ignore'.",
        );
        assert_parse_error(
            "<textarea #c-ignore>x</textarea>",
            "<textarea> holds text, not elements, so there is nothing to keep.",
        );
        for input in [
            "<svg #c-ignore><g></g></svg>",
            "<svg><g #c-ignore><circle></circle></g></svg>",
            "<math><mi #c-ignore>x</mi></math>",
        ] {
            assert_parse_error(
                input,
                "Put '#c-ignore' on an HTML element that wraps the <svg> or <math> element.",
            );
        }
        // Wrapping the SVG element in an HTML element works.
        parse_template("<div #c-ignore><svg><g></g></svg></div>", None, None).unwrap();
    }
}
