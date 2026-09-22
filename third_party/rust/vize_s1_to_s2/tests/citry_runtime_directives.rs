//! Citry regressions for runtime directives on unwrapped template loop items.

#![allow(
    clippy::disallowed_macros,
    clippy::disallowed_types,
    clippy::disallowed_methods
)]

mod support;

use support::with_transformed;
use vize_s1_to_s2::emit_dom;

fn assembled(source: &str) -> String {
    with_transformed(source, |lowered, _folio, facts, _budget| {
        emit_dom(lowered, facts)
            .unwrap_or_else(|error| panic!("emit refused {source:?}: {error:?}"))
            .assembled()
            .to_string()
    })
}

fn loop_body(output: &str) -> &str {
    let (_, after_render_list) = output
        .split_once("_renderList(")
        .expect("template loop emits renderList");
    let (_, body) = after_render_list
        .split_once("=> {")
        .expect("renderList emits a loop callback");
    body
}

fn input_element(output: &str) -> usize {
    [
        "_createElementBlock(\"input\"",
        "_createElementVNode(\"input\"",
        "_createVNode(\"input\"",
    ]
    .into_iter()
    .find_map(|call| output.find(call))
    .unwrap_or_else(|| panic!("render output has no input element call: {output}"))
}

#[test]
fn template_v_for_unwrapped_root_keeps_runtime_directive_wrappers() {
    for (source, expected) in [
        (
            r#"<template v-for="item in blocks"><div v-masonry-tile :class="item.class"></div></template>"#,
            "_directive_masonry_tile",
        ),
        (
            r#"<template v-for="item in blocks"><div v-show="item.visible"></div></template>"#,
            "[_vShow, item.visible]",
        ),
        (
            r#"<template v-for="item in blocks"><input v-model="item.name"></template>"#,
            "[_vModelText, item.name]",
        ),
    ] {
        let output = assembled(source);
        assert!(output.contains("_withDirectives("), "{source}: {output}");
        assert!(output.contains(expected), "{source}: {output}");
    }
}

#[test]
fn runtime_directive_modifier_names_are_valid_javascript_properties() {
    let output = assembled(
        r#"<template v-for="item in blocks"><input v-timing.debounce.30ms="item.handler"></template>"#,
    );
    assert!(
        output.contains(r#"{ "debounce": true, "30ms": true }"#),
        "{output}"
    );
}

#[test]
fn keyed_loop_child_stays_scoped_inside_the_row_fragment() {
    let keyed_row = assembled(
        r#"<template v-for="item in blocks" :key="item.id"><input key="citryReplacementRevision" v-model="item.name"></template>"#,
    );
    let keyed_body = loop_body(&keyed_row);
    let keyed_row_fragment = keyed_body
        .find("_createElementBlock(_Fragment, { key: item.id }")
        .expect("the keyed loop item is a Fragment keyed by item.id");
    let keyed_child = input_element(keyed_body);
    assert!(keyed_row_fragment < keyed_child, "{keyed_row}");
    assert!(
        keyed_body[keyed_child..].contains(r#"key: "citryReplacementRevision""#),
        "{keyed_row}"
    );

    let positional_row = assembled(
        r#"<template v-for="item in blocks"><input key="citryReplacementRevision" v-model="item.name"></template>"#,
    );
    let positional_body = loop_body(&positional_row);
    let positional_fragment = positional_body
        .find("_createElementBlock(_Fragment, null")
        .expect("the unkeyed loop item stays a positional Fragment");
    let positional_child = input_element(positional_body);
    assert!(positional_fragment < positional_child, "{positional_row}");
    assert!(
        positional_body[positional_child..].contains(r#"key: "citryReplacementRevision""#),
        "{positional_row}"
    );
}

#[test]
fn bound_conditional_child_key_stays_inside_the_branch_fragment() {
    let output = assembled(
        r#"<template v-if="ready"><input :key="JSON.stringify(['citryReplacementRevision', item.id])" v-model="item.name"></template>"#,
    );
    let branch_fragment = output
        .find("_createElementBlock(_Fragment, { key: 0 }")
        .expect("the conditional branch remains a Fragment");
    let child = input_element(&output);
    assert!(branch_fragment < child, "{output}");
    assert!(
        output[child..].contains("key: JSON.stringify(['citryReplacementRevision', item.id])"),
        "the composite lifecycle key stays on the input: {output}"
    );
}
