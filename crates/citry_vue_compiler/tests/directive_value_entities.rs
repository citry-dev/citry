//! Character references in Vue directive values and interpolations, on both
//! compiler lanes.
//!
//! Vue decodes the references in a directive value by the HTML attribute
//! rule, and in an interpolation (`{{ }}`) by the text rule, before it reads
//! the JavaScript, so `@click="msg = 'Tom &amp; Jerry'"` assigns
//! `Tom & Jerry`. Vize compiles a template on one of two lanes: the S2
//! emitter in `vize_s1_to_s2` writes it when it can, and the patched
//! `vize_atelier_core` code generator writes it when S2 declines. Each case
//! runs on each lane, with `prefix_identifiers` and without static hoisting,
//! as Citry compiles, and expects a part of the code that
//! `@vue/compiler-dom` 3.5.44 writes for the same template.

#![allow(clippy::disallowed_macros)]

use vize_atelier_dom::{Allocator, DomCompilerOptions, compile_template_legacy_with_options};
use vize_s1_to_s2::{DomEmitOptions, LegacyCaps, emit_dom_source_with_options};

/// (template, a part of the code `@vue/compiler-dom` 3.5.44 writes for it)
const CASES: &[(&str, &str)] = &[
    // An event handler: `&amp;` decodes to `&`, so the handler holds no `;`
    // and stays one expression rather than a statement block.
    (
        r#"<p @click="msg = 'Tom &amp; Jerry'">t</p>"#,
        r#"onClick: $event => (_ctx.msg = 'Tom & Jerry')"#,
    ),
    // Each reference decodes once: `&amp;#40;` reads as `&#40;`, whose `;`
    // makes the handler a statement block, as in Vue.
    (
        r#"<p @click="go('&amp;#40;')">t</p>"#,
        r#"$event => {_ctx.go('&#40;')}"#,
    ),
    (
        r#"<p @click="go('a&copy')">t</p>"#,
        "onClick: $event => (_ctx.go('a\u{a9}'))",
    ),
    // Conditions, including one whose raw text is not JavaScript.
    (
        r#"<p v-if="msg == 'Tom &amp; Jerry'">t</p>"#,
        r#"(_ctx.msg == 'Tom & Jerry')"#,
    ),
    (r#"<p v-if="n &gt; 0">t</p>"#, r#"(_ctx.n > 0)"#),
    (
        r#"<div><p v-if="a">x</p><p v-else-if="n &lt; 0">t</p></div>"#,
        r#": (_ctx.n < 0)"#,
    ),
    (
        r#"<p v-show="s == '&lt;&#65;&eacute;'">t</p>"#,
        "[_vShow, _ctx.s == '<A\u{e9}']",
    ),
    (
        r#"<p v-for="i in xs" :key="'&amp;' + i">t</p>"#,
        r#"key: '&' + i"#,
    ),
    // A loop source, and a key on a `<template v-for>`. `&amp;amp;` decodes
    // once, to `&amp;`.
    (
        r#"<p v-for="x in a['&amp;amp;']">{{ x }}</p>"#,
        r#"_renderList(_ctx.a['&amp;'], (x) =>"#,
    ),
    (
        r#"<template v-for="i in xs" :key="'&amp;amp;' + i"><p>t</p></template>"#,
        r#"key: '&amp;' + i"#,
    ),
    // A slot outlet's bound name.
    (
        r#"<slot :name="'s&amp;amp;'"></slot>"#,
        r#"_renderSlot(_ctx.$slots, 's&amp;')"#,
    ),
    // Slot parameters, on a component and on a `<template>`.
    (
        r#"<C v-slot="{ a = '&amp;' }">{{ a }}</C>"#,
        r#"default: _withCtx(({ a = '&' }) =>"#,
    ),
    (
        r#"<C><template #s="{ x = '&copy;' }">t</template></C>"#,
        "s: _withCtx(({ x = '\u{a9}' }) =>",
    ),
    // `v-model` reads and its update handler writes the decoded value.
    (
        r#"<input v-model="m['&amp;']">"#,
        r#""onUpdate:modelValue": $event => ((_ctx.m['&']) = $event)"#,
    ),
    (
        r#"<input v-model="m['&amp;']">"#,
        r#"[_vModelText, _ctx.m['&']]"#,
    ),
    (
        r#"<C v-model:foo="m['&amp;']" />"#,
        r#""onUpdate:foo": $event => ((_ctx.m['&']) = $event)"#,
    ),
    (r#"<p v-text="'&amp;'"></p>"#, r#"'&'"#),
    (r#"<p v-html="'&amp;lt;'"></p>"#, r#"innerHTML: '&lt;'"#),
    (r#"<p v-foo="'&amp;'"></p>"#, r#"[_directive_foo, '&']"#),
    (r#"<p v-memo="['&amp;']">t</p>"#, r#"_withMemo(['&'],"#),
    (
        r#"<p v-on="{ click: () => go('&amp;') }">t</p>"#,
        r#"_toHandlers({ click: () => _ctx.go('&') }, true)"#,
    ),
    (
        r#"<p v-bind="{ title: '&amp;' }">t</p>"#,
        r#"_guardReactiveProps({ title: '&' })"#,
    ),
    // A bound value keeps a legacy name that `=` follows, by the attribute
    // rule, and a dynamic argument is a name, so it is not decoded.
    (r#"<p :title="'a&copy=b'">t</p>"#, r#"title: 'a&copy=b'"#),
    (r#"<p :[k]="'&amp;'">t</p>"#, r#"[_ctx.k || ""]: '&'"#),
    // Interpolations decode by the text rule, where `&copy=` decodes too.
    (
        r#"<p>{{ 'Tom &amp; Jerry' }}</p>"#,
        r#"_toDisplayString('Tom & Jerry')"#,
    ),
    (
        r#"<p>{{ a &gt; b }}</p>"#,
        r#"_toDisplayString(_ctx.a > _ctx.b)"#,
    ),
    (
        r#"<p>x {{ 'a&copy=b' }} y</p>"#,
        "\"x \" + _toDisplayString('a\u{a9}=b') + \" y\"",
    ),
];

/// The S2 lane alone. A refusal fails the test: each case must stay on it.
fn emit_s2(source: &str) -> String {
    let allocator = Allocator::new();
    let options = DomEmitOptions {
        prefix_identifiers: true,
        hoist_static: false,
        ..DomEmitOptions::DEFAULT
    };
    emit_dom_source_with_options(&allocator, source, LegacyCaps::VUE3, &options)
        .map(|emitted| emitted.assembled().to_string())
        .unwrap_or_else(|error| panic!("S2 refused {source:?}: {error:?}"))
}

/// The `vize_atelier_core` lane alone, with S2 turned off.
fn emit_shipped(source: &str) -> String {
    let allocator = Allocator::new();
    let options = DomCompilerOptions {
        prefix_identifiers: true,
        hoist_static: false,
        cache_handlers: false,
        ..DomCompilerOptions::default()
    };
    let (_, errors, result) = compile_template_legacy_with_options(&allocator, source, options);
    assert!(errors.is_empty(), "{source}: {errors:?}");
    format!("{}\n{}", result.preamble, result.code)
}

#[test]
fn the_s2_lane_decodes_as_vue_compiler_dom() {
    for (source, expected) in CASES {
        let output = emit_s2(source);
        assert!(
            output.contains(expected),
            "{source}\nexpected Vue's\n{expected}\nin\n{output}"
        );
    }
}

#[test]
fn the_vize_atelier_core_lane_decodes_as_vue_compiler_dom() {
    for (source, expected) in CASES {
        let output = emit_shipped(source);
        assert!(
            output.contains(expected),
            "{source}\nexpected Vue's\n{expected}\nin\n{output}"
        );
    }
}
