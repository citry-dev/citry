use citry_template_parser::parser::parse_template;

fn assert_error(source: &str, message: &str) {
    let error = parse_template(source, None, None).unwrap_err().to_string();
    assert!(error.contains(message), "expected {message:?} in {error:?}");
}

#[test]
fn shorthand_conditions_reject_template_values() {
    for source in [
        r#"<p c-if="<></>">if</p>"#,
        r#"<p c-if="<>{{ x }}</>">if</p>"#,
        r#"<p c-if="<c-child />">if</p>"#,
        r#"<p c-if="x">if</p><p c-elif="<>{{ y }}</>">elif</p>"#,
    ] {
        assert_error(source, "must be an expression");
    }
}

#[test]
fn shorthand_for_rejects_template_values() {
    for source in [
        r#"<p c-for="<></>">item</p>"#,
        r#"<p c-for="<c-child />">item</p>"#,
    ] {
        assert_error(source, "for-loop clause");
    }
}

#[test]
fn marker_shortcuts_reject_every_value_form() {
    for source in [
        r#"<p c-if="x">if</p><p c-else="x">else</p>"#,
        r#"<p c-if="x">if</p><p c-else="">else</p>"#,
        r#"<p c-if="x">if</p><p c-else="   ">else</p>"#,
        r#"<p c-if="x">if</p><p c-else="<></>">else</p>"#,
        r#"<p c-for="i in items">item</p><p c-empty="x">empty</p>"#,
        r#"<p c-for="i in items">item</p><p c-empty="">empty</p>"#,
        r#"<p c-for="i in items">item</p><p c-empty="   ">empty</p>"#,
        r#"<p c-for="i in items">item</p><p c-empty="<></>">empty</p>"#,
    ] {
        assert_error(source, "takes no value");
    }
}

#[test]
fn shorthand_branches_enforce_group_ordering() {
    for source in [
        r#"<p c-elif="x">orphan</p>"#,
        r#"<p c-else>orphan</p>"#,
        r#"<p c-empty>orphan</p>"#,
        r#"<p c-if="x">if</p>text<p c-else>else</p>"#,
        r#"<p c-for="i in items">item</p>text<p c-empty>empty</p>"#,
        r#"<p c-if="x">if</p><p c-else>else</p><p c-elif="y">late</p>"#,
        r#"<p c-if="x">if</p><p c-else>else</p><p c-else>duplicate</p>"#,
        r#"<p c-for="i in items">item</p><p c-empty>empty</p><p c-empty>duplicate</p>"#,
        r#"<p c-if="x" c-for="i in items">item</p><p c-empty>wrong group</p>"#,
    ] {
        assert_error(source, "must follow one of");
    }
}

#[test]
fn mixed_explicit_and_shorthand_branches_remain_valid() {
    for source in [
        "<c-if cond=\"x\">if</c-if>\n<p c-else>else</p>",
        "<p c-if=\"x\">if</p>\n<c-elif cond=\"y\">elif</c-elif>",
        "<c-for each=\"i in items\">item</c-for>\n<p c-empty>empty</p>",
        "<p c-for=\"i in items\">item</p>\n<c-empty>empty</c-empty>",
    ] {
        parse_template(source, None, None)
            .unwrap_or_else(|error| panic!("valid mixed control-flow rejected: {error}"));
    }
}
