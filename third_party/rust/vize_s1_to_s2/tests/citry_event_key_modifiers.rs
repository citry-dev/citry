//! Citry regressions for key modifiers such as `.enter` on event listeners.
//!
//! Vue's compiler-dom keeps a key modifier only when the event can carry a
//! key: a keyboard event (`keydown`, `keyup`, `keypress`) or a dynamic
//! event name. On any other event it drops the modifier, so `@click.enter`
//! runs on every click. This emitter must write what the patched
//! `vize_atelier_core` writes. Each case emits with `prefix_identifiers`,
//! as Citry does, and expects the props object and patch flag that
//! `@vue/compiler-dom` 3.5.42 writes for the same template.

#![allow(clippy::disallowed_macros)]

use vize_s0::Allocator;
use vize_s1_to_s2::{DomEmitOptions, LegacyCaps, emit_dom_source_with_options};

/// (template, the text Vue writes from `(_openBlock()` through the patch flag)
const CASES: &[(&str, &str)] = &[
    // A key modifier on an event that has no key is dropped, and a click without
    // one keeps Vue's fast path (`8 /* PROPS */`, no hydration).
    (
        r#"<button @click.enter="go()"></button>"#,
        r#"(_openBlock(), _createElementBlock("button", {
    onClick: $event => (_ctx.go())
  }, null, 8 /* PROPS */, ["onClick"]))"#,
    ),
    (
        r#"<button @click.enter.stop="go()"></button>"#,
        r#"(_openBlock(), _createElementBlock("button", {
    onClick: _withModifiers($event => (_ctx.go()), ["stop"])
  }, null, 8 /* PROPS */, ["onClick"]))"#,
    ),
    (
        r#"<button @click.enter.capture="go()"></button>"#,
        r#"(_openBlock(), _createElementBlock("button", {
    onClickCapture: $event => (_ctx.go())
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["onClickCapture"]))"#,
    ),
    (
        r#"<button @mouseover.enter="go()"></button>"#,
        r#"(_openBlock(), _createElementBlock("button", {
    onMouseover: $event => (_ctx.go())
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["onMouseover"]))"#,
    ),
    (
        r#"<button @focus.enter="go()"></button>"#,
        r#"(_openBlock(), _createElementBlock("button", {
    onFocus: $event => (_ctx.go())
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["onFocus"]))"#,
    ),
    (
        r#"<button @click="go()"></button>"#,
        r#"(_openBlock(), _createElementBlock("button", {
    onClick: $event => (_ctx.go())
  }, null, 8 /* PROPS */, ["onClick"]))"#,
    ),
    (
        r#"<Comp @select.enter="go()" />"#,
        r#"(_openBlock(), _createBlock(_component_Comp, {
    onSelect: $event => (_ctx.go())
  }, null, 8 /* PROPS */, ["onSelect"]))"#,
    ),
    (
        r#"<Comp @click.enter="go()" />"#,
        r#"(_openBlock(), _createBlock(_component_Comp, {
    onClick: $event => (_ctx.go())
  }, null, 8 /* PROPS */, ["onClick"]))"#,
    ),
    // `left`, `right`, and `middle` are mouse buttons on a click, and `right`
    // still renames the event when a dropped key modifier follows it.
    (
        r#"<button @click.left="go()"></button>"#,
        r#"(_openBlock(), _createElementBlock("button", {
    onClick: _withModifiers($event => (_ctx.go()), ["left"])
  }, null, 8 /* PROPS */, ["onClick"]))"#,
    ),
    (
        r#"<button @click.right.enter="go()"></button>"#,
        r#"(_openBlock(), _createElementBlock("button", {
    onContextmenu: _withModifiers($event => (_ctx.go()), ["right"])
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["onContextmenu"]))"#,
    ),
    (
        r#"<button @click.middle="go()"></button>"#,
        r#"(_openBlock(), _createElementBlock("button", {
    onMouseup: _withModifiers($event => (_ctx.go()), ["middle"])
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["onMouseup"]))"#,
    ),
    // A keyboard event keeps its key modifiers. Vue compares the handler key
    // lowercased, so `key-down` counts and an element's case-preserving
    // `on:keyDown` key does not.
    (
        r#"<input @keydown.enter="go()">"#,
        r#"(_openBlock(), _createElementBlock("input", {
    onKeydown: _withKeys($event => (_ctx.go()), ["enter"])
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["onKeydown"]))"#,
    ),
    (
        r#"<input @keydown.left="go()">"#,
        r#"(_openBlock(), _createElementBlock("input", {
    onKeydown: _withKeys($event => (_ctx.go()), ["left"])
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["onKeydown"]))"#,
    ),
    (
        r#"<input @key-down.enter="go()">"#,
        r#"(_openBlock(), _createElementBlock("input", {
    onKeyDown: _withKeys($event => (_ctx.go()), ["enter"])
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["onKeyDown"]))"#,
    ),
    (
        r#"<input @keyDown.enter="go()">"#,
        r#"(_openBlock(), _createElementBlock("input", {
    "on:keyDown": $event => (_ctx.go())
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["on:keyDown"]))"#,
    ),
    (
        r#"<input @KeyUp.enter="go()">"#,
        r#"(_openBlock(), _createElementBlock("input", {
    "on:KeyUp": $event => (_ctx.go())
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["on:KeyUp"]))"#,
    ),
    (
        r#"<Comp @key-down.enter="go()" />"#,
        r#"(_openBlock(), _createBlock(_component_Comp, {
    onKeyDown: _withKeys($event => (_ctx.go()), ["enter"])
  }, null, 8 /* PROPS */, ["onKeyDown"]))"#,
    ),
    // A dynamic event name may be either kind, so key modifiers stay and
    // `left` is checked both as a key and as a mouse button.
    (
        r#"<div @[ev].enter="go()"></div>"#,
        r#"(_openBlock(), _createElementBlock("div", {
    [_toHandlerKey(_ctx.ev)]: _withKeys($event => (_ctx.go()), ["enter"])
  }, null, 16 /* FULL_PROPS */))"#,
    ),
    (
        r#"<div @[ev].left="go()"></div>"#,
        r#"(_openBlock(), _createElementBlock("div", {
    [_toHandlerKey(_ctx.ev)]: _withKeys(_withModifiers($event => (_ctx.go()), ["left"]), ["left"])
  }, null, 16 /* FULL_PROPS */))"#,
    ),
    // A modifier Vue does not know on a non-keyboard event is dropped too.
    (
        r#"<input @input.trim="go()">"#,
        r#"(_openBlock(), _createElementBlock("input", {
    onInput: $event => (_ctx.go())
  }, null, 40 /* PROPS, NEED_HYDRATION */, ["onInput"]))"#,
    ),
];

fn emit(source: &str) -> String {
    let allocator = Allocator::new();
    let options = DomEmitOptions {
        prefix_identifiers: true,
        ..DomEmitOptions::DEFAULT
    };
    emit_dom_source_with_options(&allocator, source, LegacyCaps::VUE3, &options)
        .map(|emitted| emitted.assembled().to_string())
        .unwrap_or_else(|error| panic!("emit refused {source:?}: {error:?}"))
}

#[test]
fn key_modifiers_follow_vue_compiler_dom() {
    for (source, expected) in CASES {
        let output = emit(source);
        assert!(
            output.contains(expected),
            "{source}\nexpected Vue's\n{expected}\nin\n{output}"
        );
    }
}
