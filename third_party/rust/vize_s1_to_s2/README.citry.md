# Citry's patched copy of `vize_s1_to_s2`

This directory is a locally patched copy of the upstream
`vize_s1_to_s2` 0.420.0 crate. It is not wholly Citry-authored and is not a
separate hosted fork. The source came from the crates.io archive whose
SHA-256 is
`13d57e14a66a37b558d10c5a46c6c1deb857ffbbfaa7f99118db584646ca096d`; the
upstream repository is <https://github.com/ubugeeei-prod/vize> at commit
`b7b308966c9baf4aa32d053448dc6d5ace6359c2`. Citry identifies the patched
package as `0.420.0+citry.7`.

The registry archive's `Cargo.toml.orig` is preserved byte-for-byte as
`Cargo.upstream.toml`, because Cargo reserves `Cargo.toml.orig` when building
a source package. `LICENSE` retains the upstream MIT license text from that
commit.

Relative to that archive, the Citry delta is:

- `Cargo.toml`: records the local `0.420.0+citry.7` package version, omits the
  upstream `emit_for` test target (the published manifest does not contain its
  `vize_atelier_dom` development dependency, and adding it would create a
  cycle), registers the `citry_runtime_directives`,
  `citry_event_handler_statements`, `citry_event_key_modifiers`,
  `citry_v_pre_tags`, and `citry_attribute_entities` regression targets,
  and drops the upstream `davinci_storage` benchmark target because its
  source is not included here.
- `src/emit/directive.rs`: keeps runtime directive and `v-model` wrappers on a
  single element unwrapped from `<template v-for>`; custom-directive modifier
  names are emitted as quoted and escaped JavaScript object keys.
- `src/emit/tpl.rs`: preserves keyed elements when an unwrapped
  `<template v-for>` would otherwise drop the row Fragment, and preserves
  keyed elements, components, and slots inside conditional Fragments. The
  component and slot loop shapes were already retained.
- `src/emit/prefix.rs`, `src/emit/prefix/rewrite.rs`,
  `src/emit/prefix/shape.rs`, `src/emit/prefix/handler.rs`, and
  `src/emit/on/wrapped.rs`: apply the same statement rule as the patched
  `vize_atelier_core` (statements only in an event handler that contains `;`,
  and handler shape checks that must match the whole text, read after
  TypeScript syntax is removed when `is_ts` is on), so the emitter refuses
  the text that `vize_atelier_core` reports as an invalid expression. They
  also write trailing line comments in an event handler so that they cannot
  hide the closing `}` or the `,` before the next prop.
- `src/emit/on.rs`, `src/emit/on/tests.rs`, and `src/emit/props_object.rs`:
  apply the same key-modifier rule as the patched `vize_atelier_core` (keep
  a key modifier only on a keyboard event or a dynamic event name, and check
  `.left` and `.right` both ways on a dynamic name), so the emitter writes
  the listener and patch flag that `@vue/compiler-dom` writes. The element
  kind is passed down because it decides the handler key that the keyboard
  check reads.
- `src/emit/entity.rs` and `src/emit/js.rs`: add
  `decode_html_attribute_entities` and `escape_js_attribute_string`, which
  decode an attribute value by the HTML attribute rule: a legacy name (a
  named reference HTML also accepts without `;`) that `=` or a letter or
  digit follows stays as written, so `href="?q=x&region=eu"` keeps its
  `&region`. They also add `escape_js_name`, which escapes a name without
  decoding it. The emitters for static attributes, bound values (`:name`,
  `v-bind`), `class`, `style`, `key` (on elements, `v-for` rows, and
  `<template>` wrappers), `v-html`, slot names, and slot props
  (`src/emit/prefix.rs`, `src/emit/props_value.rs`, `src/emit/props_class.rs`,
  `src/emit/style.rs`, `src/emit/html.rs`, `src/emit/outlet.rs`,
  `src/emit/outlet_props.rs`, `src/emit/tpl.rs`, `src/emit/tpl/fragment.rs`,
  `src/emit/vif.rs`, `src/emit/vfor/keys.rs`, `src/emit/hoist/props.rs`, and
  `src/emit/props_object/bind_pair.rs`) call the attribute versions. Text
  nodes keep the text rule, as `@vue/compiler-dom` does. Slot
  names written as `#name`, slot prop names, the attribute names that a
  `<template>` wrapper or a static prop writes, directive names, and
  directive modifiers go through `escape_js_name` (`src/emit/directive.rs`,
  `src/emit/create_slots/entry.rs`, `src/emit/slots/params.rs`,
  `src/emit/outlet_props.rs`, `src/emit/tpl/fragment.rs`, and
  `src/emit/props_static/hoist_pair.rs`), because HTML never decodes a
  reference in a name.
- `src/lower/cx.rs`, `src/lower/element.rs`, and the lowering of each
  directive (`src/lower/binding.rs`, `src/lower/bindop.rs`,
  `src/lower/forop.rs`, `src/lower/html.rs`, `src/lower/once_memo.rs`,
  `src/lower/show.rs`, `src/lower/slot.rs`, `src/lower/structural.rs`,
  `src/lower/structural/wrapper.rs`, `src/lower/sugar.rs`, and
  `src/lower/vtext.rs`): decode the character references in a directive
  value by the attribute rule before the value is parsed as JavaScript, as
  Vue does, so `@click="msg = 'Tom &amp; Jerry'"` assigns `Tom & Jerry` and
  is read as one expression. `src/lower/leaf.rs` and `src/lower/text/run.rs`
  decode an interpolation's text by the text rule, as Vue does. Names and
  dynamic arguments are not decoded. Each decoded value is allocated once,
  and `Cx` maps any part of it back to the span of the authored value
  (`decoded_directive_value`, `decoded_interpolation_text`).
- `src/lower/element.rs`: inside `v-pre`, and on the element that opens it,
  `<slot>`, components, and the built-ins (`<component>`, `<teleport>`,
  `<keep-alive>`, `<transition>`) stay plain elements, as Vue's parser
  leaves them, and a plain `<component>` drops its `is` attribute, as
  Vue's `buildProps` does.
- `src/emit/entity.rs`: every decoder reads each reference once, so a
  written `&amp;#40;` in text, an attribute value or an expression reads as
  `&#40;`, as in Vue and the browser.
- `src/emit/builtin.rs`: decodes and escapes a static `is` on `<component>`
  as an attribute value.
- `src/emit/style.rs`: decodes a static `style` before splitting it at `;`,
  as Vue does, so a `&quot;` inside a declaration stays in it.
- `src/emit/children.rs`: writes a kept comment as written, without
  decoding it, as Vue does.
- `src/emit/create_slots/entry.rs`, `src/emit/slots.rs`, and
  `src/emit/slots/params.rs`: refuse a dynamic slot name that is not
  JavaScript, such as `#[x&amp;y]`, so `vize_atelier_core` reports it as an
  invalid expression, as Vue does, rather than writing an empty name.
- `src/emit/prefix.rs`, `src/emit/cx.rs`, `src/emit/html.rs`,
  `src/emit/props_value.rs`, `src/emit/props_class.rs`, and
  `src/emit/style.rs`: read a decoded directive value as it arrives from the
  lowering, without decoding it again. When the lowering decoded a value,
  the emitter decodes the quoted value from the template the same way to
  recover the whitespace around it, which the shipped lane keeps. Without
  `prefix_identifiers` (Citry always turns it on), event handlers,
  `v-model`, the `v-on` object, `v-if`, `v-show` and slot parameters still
  drop that whitespace for a decoded value.
- `tests/emit_tpl.rs`: adds regression assertions for keyed component and slot
  children inside `v-if` template branches.
- `tests/citry_runtime_directives.rs`: adds Citry coverage for custom,
  `v-show`, and `v-model` wrappers in unwrapped loops, modifier-key escaping,
  keyed loop and conditional children, and mixed runtime directives.
- `tests/citry_event_key_modifiers.rs`: adds Citry coverage for the
  key-modifier rule, compared with the output of `@vue/compiler-dom` 3.5.42.
- `tests/citry_attribute_entities.rs`: adds Citry coverage for the attribute
  rule in static, bound, `v-html`, `v-for` key, slot, and component
  attributes, and for names that stay as written, compared with the output
  of `@vue/compiler-dom` 3.5.44.
- `tests/citry_v_pre_tags.rs`: adds Citry coverage for the `v-pre` rule
  above: a slot, a component, and each built-in stay plain elements inside
  `v-pre` and on the element that opens it, and `is` is dropped on a plain
  `<component>`.
- `tests/citry_event_handler_statements.rs`: adds Citry coverage for the
  statement rule in event handlers, interpolations, and conditions (with and
  without TypeScript when the `typescript` feature is on), for handlers that
  start with a function, for a TypeScript handler reference, and for trailing
  line comments with and without identifier prefixing.

All other source and test files are the upstream crate as archived above.
