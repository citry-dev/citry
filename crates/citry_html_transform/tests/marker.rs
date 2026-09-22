//! Tests for `mark_html`, the root-marking scan used by the Python
//! serializer. Expected values were captured by running the scanner on each
//! input and locking the observed output.

use citry_html_transform::{mark_html, MarkedHtml};

fn mark(html: &str, roots: &[&str]) -> MarkedHtml {
    let roots: Vec<String> = roots.iter().map(|s| s.to_string()).collect();
    mark_html(html, &roots, "c-render-id")
}

/// Reassemble the marked frame from segments + placeholder texts.
fn joined(result: &MarkedHtml) -> String {
    let mut out = result.segments[0].clone();
    for (ph, seg) in result.placeholders.iter().zip(&result.segments[1..]) {
        out.push_str(&ph.html);
        out.push_str(seg);
    }
    out
}

#[test]
fn single_root_gets_attribute() {
    let result = mark("<div>x</div>", &["data-cid-c1"]);
    assert_eq!(result.segments, vec![r#"<div data-cid-c1="">x</div>"#]);
    assert!(result.placeholders.is_empty());
}

#[test]
fn multiple_roots_each_get_attribute() {
    let result = mark("<div>a</div><span>b</span>", &["data-cid-c1"]);
    assert_eq!(
        result.segments,
        vec![r#"<div data-cid-c1="">a</div><span data-cid-c1="">b</span>"#]
    );
}

#[test]
fn nested_elements_are_untouched() {
    let result = mark("<div><span>x</span></div>", &["data-cid-c1"]);
    assert_eq!(
        result.segments,
        vec![r#"<div data-cid-c1=""><span>x</span></div>"#]
    );
}

#[test]
fn void_root_is_marked_and_not_normalized() {
    let result = mark(r#"<img src="a.png">"#, &["data-cid-c1"]);
    assert_eq!(result.segments, vec![r#"<img src="a.png" data-cid-c1="">"#]);

    // The splice lands after the tag name, before trailing whitespace.
    let result = mark("<br />", &["data-cid-c1"]);
    assert_eq!(result.segments, vec![r#"<br data-cid-c1="" />"#]);
}

#[test]
fn self_closing_root_is_marked() {
    let result = mark("<my-tag/>", &["data-cid-c1"]);
    assert_eq!(result.segments, vec![r#"<my-tag data-cid-c1=""/>"#]);
}

#[test]
fn root_placeholder_inherits_all_attributes() {
    let result = mark(
        r#"<template c-render-id="cAb3"></template>"#,
        &["data-cid-c2", "data-cid-c1"],
    );
    assert_eq!(result.segments, vec!["", ""]);
    assert_eq!(result.placeholders.len(), 1);
    let ph = &result.placeholders[0];
    assert_eq!(ph.id, "cAb3");
    assert_eq!(
        ph.html,
        r#"<template c-render-id="cAb3" data-cid-c2="" data-cid-c1=""></template>"#
    );
    assert_eq!(ph.added_attributes, vec!["data-cid-c2", "data-cid-c1"]);
}

#[test]
fn nested_placeholder_is_reported_without_attributes() {
    let result = mark(
        r#"<div><template c-render-id="cAb3"></template></div>"#,
        &["data-cid-c1"],
    );
    assert_eq!(result.segments, vec![r#"<div data-cid-c1="">"#, "</div>"]);
    let ph = &result.placeholders[0];
    assert_eq!(ph.id, "cAb3");
    assert_eq!(ph.html, r#"<template c-render-id="cAb3"></template>"#);
    assert!(ph.added_attributes.is_empty());
}

#[test]
fn placeholder_with_whitespace_body_is_recognized() {
    let result = mark(
        "<template c-render-id=\"cX\">\n  </template>",
        &["data-cid-c1"],
    );
    assert_eq!(result.placeholders.len(), 1);
    assert_eq!(
        result.placeholders[0].html,
        "<template c-render-id=\"cX\" data-cid-c1=\"\">\n  </template>"
    );
}

#[test]
fn template_with_real_body_is_not_a_placeholder() {
    let result = mark(
        r#"<template c-render-id="cX"><b>y</b></template>"#,
        &["data-cid-c1"],
    );
    assert!(result.placeholders.is_empty());
    assert_eq!(
        result.segments,
        vec![r#"<template c-render-id="cX" data-cid-c1=""><b>y</b></template>"#]
    );
}

#[test]
fn empty_root_attributes_still_segments_placeholders() {
    let result = mark(r#"a<template c-render-id="cX"></template>b"#, &[]);
    assert_eq!(result.segments, vec!["a", "b"]);
    assert_eq!(result.placeholders[0].id, "cX");
    assert_eq!(
        result.placeholders[0].html,
        r#"<template c-render-id="cX"></template>"#
    );
    assert!(result.placeholders[0].added_attributes.is_empty());
}

#[test]
fn text_only_and_empty_inputs() {
    let result = mark("hello", &["data-cid-c1"]);
    assert_eq!(result.segments, vec!["hello"]);
    assert!(result.placeholders.is_empty());

    let result = mark("", &["data-cid-c1"]);
    assert_eq!(result.segments, vec![""]);
    assert!(result.placeholders.is_empty());
}

#[test]
fn comments_doctype_and_cdata_pass_through() {
    let result = mark("<!-- a <div> inside --><p>x</p>", &["data-cid-c1"]);
    assert_eq!(
        result.segments,
        vec![r#"<!-- a <div> inside --><p data-cid-c1="">x</p>"#]
    );

    let result = mark(
        "<!DOCTYPE html><![CDATA[<not-a-tag>]]><p>x</p>",
        &["data-cid-c1"],
    );
    assert_eq!(
        result.segments,
        vec![r#"<!DOCTYPE html><![CDATA[<not-a-tag>]]><p data-cid-c1="">x</p>"#]
    );
}

#[test]
fn script_content_is_raw_text() {
    // Markup-like text inside <script> is not markup: the closing </script>
    // is found and the following <p> is still a root.
    let result = mark(
        r#"<script>if (a < b) { el.innerHTML = "</div><p>"; }</script><p>x</p>"#,
        &["data-cid-c1"],
    );
    assert_eq!(
        result.segments,
        vec![
            r#"<script data-cid-c1="">if (a < b) { el.innerHTML = "</div><p>"; }</script><p data-cid-c1="">x</p>"#
        ]
    );

    let result = mark("<textarea><div></textarea><p>x</p>", &["data-cid-c1"]);
    assert_eq!(
        result.segments,
        vec![r#"<textarea data-cid-c1=""><div></textarea><p data-cid-c1="">x</p>"#]
    );
}

#[test]
fn quoted_attribute_values_may_contain_gt() {
    let result = mark(
        r#"<div title="a > b" data-x='1>2'>x</div>"#,
        &["data-cid-c1"],
    );
    assert_eq!(
        result.segments,
        vec![r#"<div title="a > b" data-x='1>2' data-cid-c1="">x</div>"#]
    );
}

#[test]
fn boolean_and_unquoted_attributes() {
    let result = mark("<div hidden data-n=3>x</div>", &["data-cid-c1"]);
    assert_eq!(
        result.segments,
        vec![r#"<div hidden data-n=3 data-cid-c1="">x</div>"#]
    );
}

#[test]
fn non_ascii_content_is_preserved() {
    let result = mark("<div>čítry 漢字</div><p>ž</p>", &["data-cid-c1"]);
    assert_eq!(
        result.segments,
        vec![r#"<div data-cid-c1="">čítry 漢字</div><p data-cid-c1="">ž</p>"#]
    );
}

#[test]
fn placeholder_matching_is_ascii_case_insensitive() {
    let result = mark(
        r#"<TEMPLATE C-RENDER-ID="cX"></TEMPLATE>"#,
        &["data-cid-c1"],
    );
    assert_eq!(result.placeholders[0].id, "cX");
    assert_eq!(
        result.placeholders[0].html,
        r#"<TEMPLATE C-RENDER-ID="cX" data-cid-c1=""></TEMPLATE>"#
    );
}

#[test]
fn malformed_input_never_panics() {
    // Lenient by design: junk in, junk out, but always segments + 1 invariant.
    for html in [
        "</div><p>x</p>",
        "<div class=",
        "<",
        "a < b",
        "<!-- unterminated",
        "<![CDATA[ unterminated",
        "<script>never closed",
        "<template c-render-id=\"cX\">",
    ] {
        let result = mark(html, &["data-cid-c1"]);
        assert_eq!(result.segments.len(), result.placeholders.len() + 1);
    }
}

#[test]
fn reassembly_invariant_holds() {
    // joined(segments, placeholders) reproduces the fully marked frame.
    let result = mark(
        r#"<div>a</div><template c-render-id="cA"></template><p><template c-render-id="cB"></template></p>"#,
        &["data-cid-c1"],
    );
    assert_eq!(
        joined(&result),
        r#"<div data-cid-c1="">a</div><template c-render-id="cA" data-cid-c1=""></template><p data-cid-c1=""><template c-render-id="cB"></template></p>"#
    );
    assert_eq!(result.placeholders.len(), 2);
    assert_eq!(result.placeholders[0].id, "cA");
    assert_eq!(result.placeholders[0].added_attributes, vec!["data-cid-c1"]);
    assert_eq!(result.placeholders[1].id, "cB");
    assert!(result.placeholders[1].added_attributes.is_empty());
}
