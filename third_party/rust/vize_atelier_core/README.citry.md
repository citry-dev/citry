# Citry's patched copy of `vize_atelier_core`

This directory is a locally patched copy of the upstream
`vize_atelier_core` 0.420.0 crate. It is not wholly Citry-authored and is not a
separate hosted fork. The source came from the crates.io archive whose
SHA-256 is
`8db1544b90c72dbe51fe237437ff296d59934e44af7b99686f02cf09d0298d4e`; the
upstream repository is <https://github.com/ubugeeei-prod/vize> at commit
`b7b308966c9baf4aa32d053448dc6d5ace6359c2`. Citry identifies the patched
package as `0.420.0+citry.5`.

The registry archive's `Cargo.toml.orig` is preserved byte-for-byte as
`Cargo.upstream.toml`, because Cargo reserves `Cargo.toml.orig` when building
a source package. `LICENSE` retains the upstream MIT license text from that
commit.

Relative to that archive, the Citry delta is:

- `Cargo.toml`: records the local `0.420.0+citry.5` package version (the two
  patched crates share one version, so it moves when either changes),
  registers the `v_for_unwrapped_runtime_directives`,
  `event_handler_statements`, and `event_key_modifiers` regression targets,
  depends on `htmlize` 1.1.0 (already a dependency of `vize_armature`) for
  `src/entity.rs`, and drops the upstream `davinci` benchmark target because
  its source is not included here.
- `src/entity.rs` and `src/lib.rs`: add `authored_expression_text` and
  `authored_expression_str`, which return the text Vue reads from an
  expression written in the template: a directive value decoded by the
  HTML attribute rule, and an interpolation's text by the text rule.
- `src/lane/element.rs` (`transform_interpolation`): decodes an
  interpolation's character references by the text rule, which the parser
  leaves as written, so `{{ 'a &amp; b' }}` shows `a & b` as in Vue.
- `src/codegen/expression/generate.rs`, `src/codegen/props/events.rs`,
  `src/codegen/props/v_model.rs`, `src/codegen/slots/params.rs`,
  `src/lane/context.rs`, `src/lane/element.rs`,
  `src/lane/patterned_template.rs`, `src/lane/structural.rs`,
  `src/lane/structural_keys.rs`, `src/lane/traverse.rs`,
  `src/steps/expression.rs`, `src/steps/legacy.rs`, `src/steps/text.rs`,
  `src/steps/v_memo.rs`, `src/steps/v_model.rs`, and `src/steps/v_slot.rs`:
  where a step reads an expression back from the template source by its
  span, it reads it through `authored_expression_text`, so it sees the
  decoded text that the parser hands over for a simple expression.
  Arguments and other names stay as written. Only the slot-parameter and
  `v-model` update-handler read-backs changed output in testing; the other
  read-backs decode too, so a compound expression that reaches one reads
  the same text, though no test input reached them. `take_structural_directive` takes the allocator for the
  decoded copy.
- `src/codegen/element/directives.rs`: emits custom-directive modifier names as
  quoted and escaped JavaScript object keys.
- `src/codegen/props/v_model.rs`: emits `v-model` modifier names as quoted and
  escaped JavaScript object keys.
- `src/codegen/v_for/generate.rs`: keeps a keyed single child inside the
  per-row Fragment while still applying the child's custom-directive,
  `v-model`, and `v-show` wrappers and matching closing calls to that child.
- `src/codegen/v_for/helpers.rs`: adds the `has_element_key` helper used by
  the loop generator to detect static and `:key` bindings.
- `src/codegen/v_if/branch.rs`: keeps a keyed single child inside the
  conditional branch Fragment rather than treating the child as the branch's
  identity.
- `src/steps/expression.rs`, `src/steps/expression/rewrite.rs`,
  `src/steps/expression/reparse.rs`, `src/steps/expression/parse_checks.rs`,
  `src/steps/expression/shape_checks.rs`, and
  `src/steps/expression/inline_handler.rs`: read text as a list of
  statements only for an event handler that contains `;`, as
  `@vue/compiler-core` does, and report every other statement as an invalid
  expression, in the TypeScript fallback too. The handler reference and
  function checks also require the parsed expression to be the whole text, so
  `a; b()` is compiled as two statements rather than passed on as the
  reference `a`. With `is_ts`, both checks read the text after its
  TypeScript syntax is removed, so `foo!` is still the reference `foo`. For
  `() => a(); b()` this departs from Vue, whose function check reads only
  the first statement and writes text that does not parse.
- `src/codegen.rs`, `src/codegen/expression.rs`, and
  `src/codegen/expression/generate.rs`: write line comments in an event
  handler as block comments, so a trailing `// note` cannot hide the closing
  `}` of `$event => {...}` or the `,` before the next prop.
- `src/codegen/props/events.rs` and `src/codegen/patch_flag.rs`: keep a key
  modifier such as `.enter` only on a keyboard event or a dynamic event
  name, as `@vue/compiler-dom` does, and drop it on any other event instead
  of wrapping the handler in `withKeys`. An event counts as a keyboard event
  when its handler key, lowercased, is `onkeyup`, `onkeydown`, or
  `onkeypress`. On a dynamic event name, `.left` and `.right` are checked
  both as keys and as mouse buttons. A click with a dropped key modifier
  keeps Vue's patch flag without hydration. Two differences from Vue remain:
  `.native` is dropped as an option (Vue reads it as a key name), and a click
  with `.native` still sets `NEED_HYDRATION`. Citry's template parser
  rejects `.native` on a non-keyboard event.
- `tests/v_for_unwrapped_runtime_directives.rs`: adds regression coverage for
  custom, `v-show`, and `v-model` directives in unwrapped loops, modifier-key
  escaping, keyed loop and conditional children, mixed directives, and ordinary
  versus multi-child loop shapes.
- `tests/event_key_modifiers.rs`: adds regression coverage for key, mouse
  button, and unknown modifiers on keyboard, non-keyboard, component, and
  dynamic events, compared with the output of `@vue/compiler-dom` 3.5.42.
- `tests/event_handler_statements.rs`: adds regression coverage for the
  statement rule in event handlers, bound attributes, interpolations,
  conditions, and loop sources (with and without TypeScript), for handlers
  that start with a function, for a TypeScript handler reference, and for
  trailing line comments with and without identifier prefixing.

All other source and test files are the upstream crate as archived above.
