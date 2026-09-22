use vize_atelier_core::{
    CodegenOptions, CodegenResult, TransformOptions, generate, parse, transform,
};
use vize_s0::String;

fn result_output(result: &CodegenResult) -> String {
    let mut output = String::with_capacity(result.preamble.len() + result.code.len() + 1);
    output.push_str(&result.preamble);
    output.push('\n');
    output.push_str(&result.code);
    output
}

fn compile_result(source: &str) -> CodegenResult {
    let allocator = vize_s0::Allocator::new();
    let (mut root, errors) = parse(&allocator, source);
    assert!(errors.is_empty(), "Parse errors: {errors:?}");
    transform(&allocator, &mut root, TransformOptions::default(), None);
    generate(&root, CodegenOptions::default())
}

fn compile(source: &str) -> String {
    result_output(&compile_result(source))
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
fn unwrapped_template_loop_keeps_each_runtime_directive_kind() {
    let custom =
        compile(r#"<template v-for="item in items"><button v-focus>go</button></template>"#);
    assert!(custom.contains("withDirectives"));
    assert!(custom.contains("resolveDirective(\"focus\")"));

    let show =
        compile(r#"<template v-for="item in items"><p v-show="item.visible">x</p></template>"#);
    assert!(show.contains("withDirectives"));
    assert!(show.contains("vShow"));

    let model =
        compile(r#"<template v-for="item in items"><input v-model="item.name"></template>"#);
    assert!(model.contains("withDirectives"));
    assert!(model.contains("vModelText"));
}

#[test]
fn custom_directive_modifier_names_are_valid_javascript_properties() {
    let output = compile(
        r#"<template v-for="item in items"><button v-timing.debounce.30ms="item.handler"></button></template>"#,
    );
    assert!(
        output.contains(r#"{ "debounce": true, "30ms": true }"#),
        "{output}"
    );
}

#[test]
fn keyed_loop_child_stays_scoped_inside_the_row_fragment() {
    let keyed_row = compile(
        r#"<template v-for="item in items" :key="item.id"><input key="citryReplacementRevision" v-model="item.name"></template>"#,
    );
    let keyed_body = loop_body(&keyed_row);
    let keyed_row_fragment = keyed_body
        .find("_createElementBlock(_Fragment, { key: item.id }")
        .unwrap_or_else(|| {
            panic!("the keyed loop item is a Fragment keyed by item.id: {keyed_row}")
        });
    let keyed_child = input_element(keyed_body);
    assert!(keyed_row_fragment < keyed_child, "{keyed_row}");
    assert!(
        keyed_body[keyed_child..].contains(r#"key: "citryReplacementRevision""#),
        "{keyed_row}"
    );

    let positional_row = compile(
        r#"<template v-for="item in items"><input key="citryReplacementRevision" v-model="item.name"></template>"#,
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
    let output = compile(
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

#[test]
fn unwrapped_template_loop_keeps_mixed_directives_and_template_key() {
    let result = compile_result(
        r#"<template v-for="item in items" :key="item.id"><input v-model="item.name" v-show="item.visible" v-focus></template>"#,
    );
    let output = result_output(&result);
    assert!(result.preamble.contains("withDirectives"));
    assert!(result.preamble.contains("vModelText"));
    assert!(result.preamble.contains("vShow"));
    assert!(output.contains("resolveDirective(\"focus\")"));
    assert!(result.code.contains("_withDirectives("), "{}", result.code);
    assert!(
        result.code.contains("[_vModelText, item.name]"),
        "v-model directive tuple must use the loop-local item: {}",
        result.code
    );
    assert!(
        result.code.contains("[_vShow, item.visible]"),
        "v-show directive tuple must use the loop-local item: {}",
        result.code
    );
    assert!(
        result.code.contains("[_directive_focus]"),
        "custom directive tuple was dropped from the loop child: {}",
        result.code
    );
    assert!(result.code.contains("key: item.id"), "{}", result.code);
    assert!(
        result.code.contains("128 /* KEYED_FRAGMENT */"),
        "{}",
        result.code
    );
    assert!(
        result.code.contains("(item) => {") || result.code.contains("(item, _index) => {"),
        "loop expression should retain its item scope: {}",
        result.code
    );
}

#[test]
fn runtime_directives_survive_numeric_loop_in_a_distinct_conditional_branch() {
    let result = compile_result(
        r#"<template v-if="enabled"><template v-for="item in 3"><button v-show="item > 1" v-focus>{{ item }}</button></template></template><template v-else><button v-show="!enabled">off</button></template>"#,
    );
    assert!(result.preamble.contains("renderList"));
    assert!(result.preamble.contains("withDirectives"));
    assert!(result.preamble.contains("vShow"));
    let code = &result.code;
    assert!(code.contains("3"), "numeric loop bound missing: {code}");
    assert!(
        code.contains("item > 1"),
        "numeric loop alias missing: {code}"
    );
    assert!(
        code.contains("_withDirectives("),
        "runtime directive tuple missing: {code}"
    );
    assert!(
        code.contains("[_vShow, item > 1]"),
        "looped v-show tuple must stay attached to its child: {code}"
    );
    assert!(
        code.contains("enabled"),
        "conditional selector missing: {code}"
    );
    assert!(
        code.contains("off"),
        "distinct fallback branch missing: {code}"
    );
}

#[test]
fn ordinary_and_multi_child_loops_keep_their_existing_shapes() {
    let ordinary = compile(r#"<button v-for="item in items" v-show="item.visible">x</button>"#);
    assert!(ordinary.contains("withDirectives"));
    assert!(ordinary.contains("vShow"));

    let multiple = compile(
        r#"<template v-for="item in items"><button v-show="item.visible">x</button><span>{{ item }}</span></template>"#,
    );
    assert!(multiple.contains("Fragment"));
    assert!(multiple.contains("withDirectives"));
    assert!(multiple.contains("vShow"));
}
