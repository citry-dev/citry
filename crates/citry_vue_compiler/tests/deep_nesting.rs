//! Deeply nested templates compile, read, render and drop on a small thread.
//!
//! Vue's compiler, the reader of the render function it emits, the HTML
//! writers and `eval` call themselves once per nesting level, so without a
//! guard a deep template overflows the stack and aborts the process. These
//! tests run every step for templates at the nesting limits planned in #272
//! (512 nested tags, 256 of them control flow) on threads with 128 KiB and
//! 384 KiB stacks. 128 KiB is the default for threads on musl Linux. On it a
//! render starts on a new 1 MiB segment, while 384 KiB is just enough to
//! start on the thread's own stack, so the guard at each level must work in
//! both. A crash aborts this test binary, which fails the test run.

use std::collections::HashMap;

use citry_vue_compiler::server_render::{
    HydrationRender, RenderRequest, ServerRenderProgram, read_program, render_for_hydration,
};
use citry_vue_compiler::{CompileRequest, compile};
use serde_json::json;

/// Tags nested in the deepest templates these tests build.
const TOTAL_DEPTH: usize = 512;

/// Control-flow tags nested in the deepest templates.
const LOGIC_DEPTH: usize = 256;

/// How many elements deep the server writes inside the host before it
/// leaves the rest to the browser (`MAX_ELEMENT_DEPTH`).
const ELEMENT_DEPTH: usize = 400;

/// The thread stack sizes every render runs on.
const STACK_SIZES: [usize; 2] = [128 * 1024, 384 * 1024];

/// Compile, read and render a one-component page, then drop everything.
fn render_page(template: &str, prepared: &str) -> HydrationRender {
    let artifact = compile(CompileRequest {
        template: template.to_owned(),
        local_calls: Vec::new(),
        local_call_runs: Vec::new(),
        element_bindings: Vec::new(),
        dynamic_elements: Vec::new(),
    });
    assert!(
        artifact.diagnostics.is_empty(),
        "{:?}",
        artifact.diagnostics
    );
    let program: ServerRenderProgram = read_program(&artifact.code, &[]).expect("reads");
    let programs = HashMap::from([("def-root".to_owned(), &program)]);
    // Written as text, because building and freeing a deep `serde_json::Value`
    // here would itself call itself once per level.
    let manifest = format!(
        r#"{{"rootId":"occ-root","occurrences":[{{"id":"occ-root","typeKey":"Root","definitionId":"def-root","preparedData":{prepared},"serverData":{{}}}}]}}"#
    );
    let tags = HashMap::from([("Root".to_owned(), "citry-root".to_owned())]);
    let result = render_for_hydration(&RenderRequest {
        programs: &programs,
        manifest_json: &manifest,
        tags: &tags,
        threshold: 0,
        full_parse_check: false,
    });
    drop(programs);
    drop(program);
    result
}

/// Render `template` on each of `STACK_SIZES`, returning the results.
fn render_on_small_stacks(template: &str, prepared: &str) -> Vec<HydrationRender> {
    STACK_SIZES
        .iter()
        .map(|&stack_size| {
            let template = template.to_owned();
            let prepared = prepared.to_owned();
            std::thread::Builder::new()
                .stack_size(stack_size)
                .spawn(move || render_page(&template, &prepared))
                .unwrap()
                .join()
                .unwrap_or_else(|_| panic!("failed on a {stack_size}-byte stack"))
        })
        .collect()
}

/// Render `template` on small stacks and check the server wrote all of it:
/// no part was left for the browser to build.
fn renders_fully_on_small_stacks(template: &str, prepared: &str) {
    for result in render_on_small_stacks(template, prepared) {
        assert_eq!(result.reason, None, "{:?}", result.declines);
        assert!(result.declines.is_empty(), "{:?}", result.declines);
        assert!(
            result
                .html
                .as_deref()
                .is_some_and(|html| html.contains(">x<"))
        );
    }
}

/// Render `template` on small stacks and check the page hydrates with one
/// shell where the depth ran out.
fn hydrates_with_a_depth_shell(template: &str, prepared: &str) {
    for result in render_on_small_stacks(template, prepared) {
        assert_eq!(result.reason, None, "{:?}", result.declines);
        let codes: Vec<_> = result.declines.iter().map(|decline| decline.code).collect();
        assert_eq!(codes, ["nesting-depth"]);
        assert!(result.declines[0].shell_tag.is_some());
        assert!(
            result
                .html
                .as_deref()
                .is_some_and(|html| html.contains(r#"data-allow-mismatch="children""#))
        );
    }
}

/// `open` repeated `depth` times around `inner`, closed by `close`.
fn nest(open: &str, inner: &str, close: &str, depth: usize) -> String {
    format!("{}{inner}{}", open.repeat(depth), close.repeat(depth))
}

const VALUE: &str = "{{ $citryPrepared.t }}";

const PLAIN_DATA: &str = r#"{"t":"x"}"#;

#[test]
fn nested_elements() {
    renders_fully_on_small_stacks(&nest("<div>", VALUE, "</div>", ELEMENT_DEPTH), PLAIN_DATA);
}

#[test]
fn nested_elements_with_v_if() {
    let inner = nest("<div>", VALUE, "</div>", ELEMENT_DEPTH - LOGIC_DEPTH);
    renders_fully_on_small_stacks(
        &nest(
            "<div v-if=\"$citryPrepared.t\">",
            &inner,
            "</div>",
            LOGIC_DEPTH,
        ),
        PLAIN_DATA,
    );
}

#[test]
fn nested_templates_with_v_for() {
    // Each level reads its own row, as the rows of nested `<c-for>` tags do.
    let open: String = (0..LOGIC_DEPTH)
        .map(|level| format!("<template v-for=\"r{level} in $citryPrepared.rows\">"))
        .collect();
    let inner = nest("<div>", VALUE, "</div>", TOTAL_DEPTH - LOGIC_DEPTH);
    renders_fully_on_small_stacks(
        &format!("{open}{inner}{}", "</template>".repeat(LOGIC_DEPTH)),
        &json!({"t": "x", "rows": [1]}).to_string(),
    );
}

#[test]
fn elements_past_the_element_cap_become_a_shell() {
    // Chrome's parser would move elements this deep out of their parents.
    hydrates_with_a_depth_shell(
        &format!(
            "<section>{}</section>",
            nest("<div>", VALUE, "</div>", TOTAL_DEPTH)
        ),
        PLAIN_DATA,
    );
}

#[test]
fn levels_past_the_writer_cap_become_a_shell() {
    // A `<template v-if>` costs two reader and two writer levels and opens
    // no element, while a `<div>` costs one reader and two writer levels.
    // 650 of the first around 399 of the second read about 1,700 levels,
    // under the reader's cap of 2,048, and write about 2,100, past the
    // writer's, while staying under the element cap.
    let inner = nest("<div>", VALUE, "</div>", ELEMENT_DEPTH - 1);
    hydrates_with_a_depth_shell(
        &format!(
            "<section>{}</section>",
            nest(
                "<template v-if=\"$citryPrepared.t\">",
                &inner,
                "</template>",
                650
            )
        ),
        PLAIN_DATA,
    );
}

#[test]
fn elements_with_v_for_at_every_level_compile_on_a_small_thread() {
    // Vue's compiler needs the most stack for this shape: about 9.3 MiB at
    // this depth in a debug build. The list is known only in the browser, so
    // the page mounts there; the test checks that nothing crashes.
    render_on_small_stacks(
        &nest("<div v-for=\"i in list\">", "x", "</div>", TOTAL_DEPTH),
        "{}",
    );
}

/// `{"t":"x","deep":[[...["x"]...]]}` with `depth` arrays, as JSON text.
fn deep_data(depth: usize) -> String {
    format!(
        r#"{{"t":"x","deep":{}"x"{}}}"#,
        "[".repeat(depth),
        "]".repeat(depth)
    )
}

#[test]
fn data_nested_deeper_than_serde_json_reads_by_default() {
    // A page's data nests about two levels for each `<c-for>` around it, so
    // 256 of them send data about 520 levels deep.
    renders_fully_on_small_stacks(&format!("<p>{VALUE}</p>"), &deep_data(2 * LOGIC_DEPTH + 8));
}

#[test]
fn data_deeper_than_the_manifest_limit_mounts_in_the_browser() {
    for result in render_on_small_stacks(&format!("<p>{VALUE}</p>"), &deep_data(5_000)) {
        assert_eq!(result.reason, Some("manifest"));
        assert_eq!(result.html, None);
    }
}
