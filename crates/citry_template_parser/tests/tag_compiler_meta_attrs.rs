// Tests for the `#c-*` framework-metadata channel (compiler half).
//
// On a plain HTML element, `#c-key="expr"` compiles to an ElementKeyNode
// wrapping the expression attribute. That runtime node owns the complete
// composite output attribute, so `None` can omit it without leaving an empty
// scope prefix. `#c-ignore` compiles to the literal
// ` data-citry-morph="ignore"` marker. On a component tag, metadata rides in
// the ComponentNode's tagged trailing tuple, never as one of the kwargs
// attributes. See docs/design/component_ranges_plan.md.
//
// These tests assert the exact generated Python source string
// (observe-then-lock, like tag_compiler.rs).

#[cfg(test)]
mod tests {
    use citry_template_parser::compiler::compile_template;
    use citry_template_parser::parser::parse_template;

    /// Wrap an expected `body` list in the `generate_template()` boilerplate.
    fn wrap(body_list: &str) -> String {
        format!(
            "def generate_template():\n    body = {}\n    return body\n",
            body_list
        )
    }

    /// Parse + compile `input`, then assert the generated code matches
    /// `wrap(expected_body_list)`.
    fn assert_compile(input: &str, expected_body_list: &str) {
        let template = parse_template(input, None, None)
            .unwrap_or_else(|e| panic!("parse failed for {input:?}: {e:?}"));
        let result = compile_template(template, None)
            .unwrap_or_else(|e| panic!("compile failed for {input:?}: {e:?}"));
        assert_eq!(result, wrap(expected_body_list), "input: {input:?}");
    }

    // =============================================================================
    // PLAIN ELEMENTS: #c-key
    // =============================================================================

    #[test]
    fn test_key_on_element() {
        assert_compile(
            r#"<li #c-key="item.id">x</li>"#,
            r##"["""<li""", ElementKeyNode(ExprHtmlAttr(source, (4, 20,), """#c-key""", """item.id""", ("item",))), """>x</li>""",]"##,
        );
    }

    #[test]
    fn test_key_emits_after_static_attrs() {
        assert_compile(
            r#"<li class="a" #c-key="item.id">x</li>"#,
            r##"["""<li class=\"a\"""", ElementKeyNode(ExprHtmlAttr(source, (14, 30,), """#c-key""", """item.id""", ("item",))), """>x</li>""",]"##,
        );
    }

    #[test]
    fn test_key_emits_after_dynamic_attr_region() {
        // The ordinary attributes stay one ElementAttrsNode region; the key is
        // its own fragment after it, invisible to the attrs machinery.
        assert_compile(
            r#"<li c-class="cls" #c-key="item.id">x</li>"#,
            r##"["""<li""", ElementAttrsNode(source, (0, 35,), (ExprHtmlAttr(source, (4, 17,), """c-class""", """cls""", ("cls",)),), ("cls",)), ElementKeyNode(ExprHtmlAttr(source, (18, 34,), """#c-key""", """item.id""", ("item",))), """>x</li>""",]"##,
        );
    }

    #[test]
    fn test_key_on_void_element() {
        assert_compile(
            r#"<input #c-key="'draft'" />"#,
            r##"["""<input""", ElementKeyNode(ExprHtmlAttr(source, (7, 23,), """#c-key""", """'draft'""", ())), """/>""",]"##,
        );
    }

    #[test]
    fn test_key_inside_c_for_evaluates_per_item() {
        // The key fragments sit inside the loop branch's body, so the
        // expression re-evaluates per iteration.
        assert_compile(
            r#"<c-for each="item in items"><li #c-key="item.id">{{ item.name }}</li></c-for>"#,
            r##"[ForNode(source, (((0, 77,), (ExprHtmlAttr(source, (7, 27,), """each""", """item in items""", ("items",)),), ["""<li""", ElementKeyNode(ExprHtmlAttr(source, (32, 48,), """#c-key""", """item.id""", ("item",))), """>""", ExprNode(source, (49, 64,), """item.name """, ("item",)), """</li>""",], ("item",),),), ("items",)),]"##,
        );
    }

    #[test]
    fn test_key_with_c_for_shorthand() {
        // The `c-for` attribute wraps the element in a ForNode; the key stays
        // on the element, inside the loop body.
        assert_compile(
            r#"<li c-for="item in items" #c-key="item.id">x</li>"#,
            r##"[ForNode(source, (((0, 49,), (ExprHtmlAttr(source, (4, 25,), """each""", """item in items""", ("items",)),), ["""<li""", ElementKeyNode(ExprHtmlAttr(source, (26, 42,), """#c-key""", """item.id""", ("item",))), """>x</li>""",], ("item",),),), ("items",)),]"##,
        );
    }

    // =============================================================================
    // PLAIN ELEMENTS: #c-ignore
    // =============================================================================

    #[test]
    fn test_ignore_on_element() {
        assert_compile(
            "<div #c-ignore>x</div>",
            r#"["""<div data-citry-morph=\"ignore\">x</div>""",]"#,
        );
    }

    #[test]
    fn test_key_and_ignore_together() {
        assert_compile(
            r#"<div #c-key="k" #c-ignore>x</div>"#,
            r##"["""<div""", ElementKeyNode(ExprHtmlAttr(source, (5, 15,), """#c-key""", """k""", ("k",))), """ data-citry-morph=\"ignore\">x</div>""",]"##,
        );
    }

    // =============================================================================
    // COMPONENT TAGS: tagged metadata envelope
    // =============================================================================

    #[test]
    fn test_key_on_component_tag() {
        // The key entry is in the trailing range envelope, NOT one of the attrs
        // (argument 3), so it can never become a kwarg. Its variables still
        // count into the node's used_vars (argument 5).
        assert_compile(
            r#"<c-Card #c-key="item.id" title="Hi">body</c-Card>"#,
            r##"[ComponentNode(source, (0, 49,), (StaticHtmlAttr(source, (25, 35,), """title""", """Hi""", ()),), ["""body""",], ("item",), """card""", False, ("range", ("key", ExprHtmlAttr(source, (8, 24,), """#c-key""", """item.id""", ("item",)),),)),]"##,
        );
    }

    #[test]
    fn test_key_on_component_tag_with_dynamic_attr() {
        assert_compile(
            r#"<c-Card c-title="t" #c-key="k" />"#,
            r##"[ComponentNode(source, (0, 33,), (ExprHtmlAttr(source, (8, 19,), """c-title""", """t""", ("t",)),), [], ("t", "k",), """card""", False, ("range", ("key", ExprHtmlAttr(source, (20, 30,), """#c-key""", """k""", ("k",)),),)),]"##,
        );
    }

    #[test]
    fn test_unkeyed_component_output_unchanged() {
        // No trailing argument when the tag carries no metadata: the emitted
        // code for existing templates stays byte-identical.
        assert_compile(
            r#"<c-Card title="Hi" />"#,
            r#"[ComponentNode(source, (0, 21,), (StaticHtmlAttr(source, (8, 18,), """title""", """Hi""", ()),), [], (), """card""", False),]"#,
        );
    }

    #[test]
    fn test_key_on_c_element_with_static_is_compiles_to_plain_element() {
        // The static `is` rewrite turns <c-element> into the named element,
        // so the key takes the plain-element form (empty scope segment).
        assert_compile(
            r#"<c-element is="div" #c-key="k">x</c-element>"#,
            r##"["""<div""", ElementKeyNode(ExprHtmlAttr(source, (20, 30,), """#c-key""", """k""", ("k",))), """>x</div>""",]"##,
        );
    }

    #[test]
    fn test_key_on_case_variant_c_element_keeps_element_locus() {
        assert_compile(
            r#"<c-Element is="div" #c-key="k">x</c-Element>"#,
            r##"["""<div""", ElementKeyNode(ExprHtmlAttr(source, (20, 30,), """#c-key""", """k""", ("k",))), """>x</div>""",]"##,
        );
    }

    #[test]
    fn test_key_on_c_component_with_static_is() {
        // The static `is` rewrite resolves the component name at compile time;
        // the key rides in the range envelope like on any component tag.
        assert_compile(
            r#"<c-component is="Card" #c-key="k" />"#,
            r##"[ComponentNode(source, (0, 36,), (), [], ("k",), """card""", False, ("range", ("key", ExprHtmlAttr(source, (23, 33,), """#c-key""", """k""", ("k",)),),)),]"##,
        );
    }

    #[test]
    fn test_ignore_on_component_tag() {
        assert_compile(
            "<c-card #c-ignore />",
            r#"[ComponentNode(source, (0, 20,), (), [], (), """card""", False, ("range", ("morph", "ignore",),)),]"#,
        );
    }

    #[test]
    fn test_component_metadata_is_canonical() {
        assert_compile(
            r#"<c-card #c-ignore #c-key="k" />"#,
            r##"[ComponentNode(source, (0, 31,), (), [], ("k",), """card""", False, ("range", ("key", ExprHtmlAttr(source, (18, 28,), """#c-key""", """k""", ("k",)),), ("morph", "ignore",),)),]"##,
        );
    }

    #[test]
    fn test_dynamic_element_metadata() {
        assert_compile(
            r#"<c-element c-is="tag" #c-key="k" #c-ignore />"#,
            r##"[ComponentNode(source, (0, 45,), (ExprHtmlAttr(source, (11, 21,), """c-is""", """tag""", ("tag",)),), [], ("tag", "k",), """element""", False, ("element", ("key", ExprHtmlAttr(source, (22, 32,), """#c-key""", """k""", ("k",)),), ("morph", "ignore",),)),]"##,
        );
    }

    #[test]
    fn test_compile_is_deterministic() {
        // Same input compiles to the same bytes across repeated runs (the
        // emitted fragments come from source-ordered Vecs, never a set).
        let input = r#"<c-Card c-title="t" #c-ignore #c-key="k" /><li class="a" #c-key="item.id" #c-ignore>x</li>"#;
        let template = parse_template(input, None, None).unwrap();
        let first = compile_template(template, None).unwrap();
        for _ in 0..5 {
            let template = parse_template(input, None, None).unwrap();
            let again = compile_template(template, None).unwrap();
            assert_eq!(first, again);
        }
    }
}
