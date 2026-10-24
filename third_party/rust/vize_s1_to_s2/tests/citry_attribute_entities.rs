//! Citry regressions for character references in attribute values.
//!
//! The browser and Vue's compiler-dom read a legacy entity name written
//! without `;` (such as `&reg` or `&copy`) by two rules. In text it always
//! decodes, so `&copyX` reads as `©X`. In an attribute value it stays as
//! written when `=` or a letter or digit follows it, so a URL such as
//! `?q=x&region=eu` keeps its `&region`. A bound value such as `:title` is
//! an attribute value too. A name, such as a slot or directive modifier name, is never
//! decoded. Each case emits with `prefix_identifiers` and without static
//! hoisting, as Citry does, and expects the text that `@vue/compiler-dom`
//! 3.5.44 writes for the same template.

#![allow(clippy::disallowed_macros)]

use vize_s0::Allocator;
use vize_s1_to_s2::{DomEmitOptions, LegacyCaps, emit_dom_source_with_options};

/// (template, a part of the text Vue writes for it)
const CASES: &[(&str, &str)] = &[
    // A static attribute keeps `&region=` and still decodes `&copy` at the
    // end, while the text beside it decodes `&copyX`.
    (
        r#"<a href="/s?q=x&region=eu&copy">t &copyX</a>"#,
        r#"_createElementBlock("a", { href: "/s?q=x&region=eu©" }, "t ©X")"#,
    ),
    (
        r#"<p class="a&region=b">t</p>"#,
        r#"_createElementBlock("p", { class: "a&region=b" }, "t")"#,
    ),
    // A string inside a bound expression, `v-html` included.
    (
        r#"<a :href="'/s?q=x&region=eu'">t</a>"#,
        r#"_createElementBlock("a", { href: '/s?q=x&region=eu' }, "t")"#,
    ),
    (
        r#"<p :title="'a&copy=b' + x">t</p>"#,
        r#"title: 'a&copy=b' + _ctx.x"#,
    ),
    (
        r#"<p v-html="'x&region=1'"></p>"#,
        r#"_createElementBlock("p", { innerHTML: 'x&region=1' }"#,
    ),
    // A slot's name and props, and a component prop.
    (
        r#"<slot name="s&region=1" title="x&region=1"></slot>"#,
        r#"_renderSlot(_ctx.$slots, "s&region=1", { title: "x&region=1" })"#,
    ),
    (
        r#"<Comp label="x&region=1&copy" />"#,
        r#"_createBlock(_component_Comp, { label: "x&region=1©" })"#,
    ),
    // A static `key` on a `v-for` row is an attribute value too.
    (
        r#"<div v-for="i in xs" key="a&region=b&copy">t</div>"#,
        r#"_createElementBlock("div", { key: "a&region=b©" }, "t")"#,
    ),
    // HTML never decodes a reference in a name, so a directive modifier, a
    // slot name, and a slot prop name keep `&copy` as written.
    (
        r#"<div v-foo.m&copy="x"></div>"#,
        r#"[_directive_foo, _ctx.x, void 0, { "m&copy": true }]"#,
    ),
    (
        r#"<C><template #a&copy>x</template></C>"#,
        r#""a&copy": _withCtx("#,
    ),
    (r#"<C v-slot:b&copy="p">x</C>"#, r#""b&copy": _withCtx("#),
    (
        r#"<slot data-a&copy="1"></slot>"#,
        r#"_renderSlot(_ctx.$slots, "default", { "dataA&copy": "1" })"#,
    ),
];

fn emit(source: &str) -> String {
    let allocator = Allocator::new();
    let options = DomEmitOptions {
        prefix_identifiers: true,
        hoist_static: false,
        ..DomEmitOptions::DEFAULT
    };
    emit_dom_source_with_options(&allocator, source, LegacyCaps::VUE3, &options)
        .map(|emitted| emitted.assembled().to_string())
        .unwrap_or_else(|error| panic!("emit refused {source:?}: {error:?}"))
}

#[test]
fn attribute_values_follow_vue_compiler_dom() {
    for (source, expected) in CASES {
        let output = emit(source);
        assert!(
            output.contains(expected),
            "{source}\nexpected Vue's\n{expected}\nin\n{output}"
        );
    }
}
