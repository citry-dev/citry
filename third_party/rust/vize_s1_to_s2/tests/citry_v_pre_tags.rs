//! Citry regressions for tags inside `v-pre`.
//!
//! Vue's parser decides whether an element is a slot outlet, a component,
//! or a built-in only outside `v-pre` (compiler-core's `onCloseTag`), so
//! inside a `v-pre` subtree, and on the element that opens one, `<slot>`,
//! `<component>`, `<teleport>`, `<keep-alive>`, `<transition>`, and any
//! component name stay plain elements. Vue also drops `is` from a plain
//! `<component>` there. Each case emits with `prefix_identifiers`, as Citry
//! does (no static hoisting), and expects the text `@vue/compiler-dom`
//! 3.5.42 writes for the same template.

#![allow(clippy::disallowed_macros)]

use vize_s0::Allocator;
use vize_s1_to_s2::{DomEmitOptions, LegacyCaps, emit_dom_source_with_options};

/// (template, the text Vue writes from `(_openBlock()`)
const CASES: &[(&str, &str)] = &[
    (
        r#"<div v-pre><slot name="a">FALLBACK</slot></div>"#,
        r#"_createElementVNode("slot", { name: "a" }, "FALLBACK")"#,
    ),
    // Vue also drops `is` from the plain `<component>`.
    (
        r#"<div v-pre><component is="x">c</component></div>"#,
        r#"_createElementVNode("component", null, "c")"#,
    ),
    (
        r#"<div v-pre><teleport to="body">t</teleport></div>"#,
        r#"_createElementVNode("teleport", { to: "body" }, "t")"#,
    ),
    (
        r#"<div v-pre><keep-alive>k</keep-alive></div>"#,
        r#"_createElementVNode("keep-alive", null, "k")"#,
    ),
    (
        r#"<div v-pre><transition>t</transition></div>"#,
        r#"_createElementVNode("transition", null, "t")"#,
    ),
    (
        r#"<div v-pre><Comp :x="1">c</Comp></div>"#,
        r#"_createElementVNode("Comp", { ":x": "1" }, "c")"#,
    ),
    // On the element that opens `v-pre`, too.
    (
        r#"<slot v-pre name="a">f</slot>"#,
        r#"(_openBlock(), _createElementBlock("slot", { name: "a" }, "f"))"#,
    ),
    (
        r#"<component v-pre is="x">c</component>"#,
        r#"(_openBlock(), _createElementBlock("component", null, "c"))"#,
    ),
];

fn emit(source: &str) -> String {
    let allocator = Allocator::new();
    // The options Citry compiles with: no static hoisting or handler cache.
    let options = DomEmitOptions {
        prefix_identifiers: true,
        hoist_static: false,
        cache_handlers: false,
        ..DomEmitOptions::DEFAULT
    };
    emit_dom_source_with_options(&allocator, source, LegacyCaps::VUE3, &options)
        .map(|emitted| emitted.assembled().to_string())
        .unwrap_or_else(|error| panic!("emit refused {source:?}: {error:?}"))
}

#[test]
fn tags_inside_v_pre_stay_plain_elements() {
    for (source, expected) in CASES {
        let output = emit(source);
        assert!(
            output.contains(expected),
            "{source}\nexpected Vue's\n{expected}\nin\n{output}"
        );
    }
}
