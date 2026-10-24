//! Character references in static template text and static attribute
//! values, on both compiler lanes.
//!
//! The browser and Vue decode each reference in static text or a static
//! attribute value once, so a written `&amp;#40;` shows `&#40;`. In an
//! attribute value, a legacy name (a named reference HTML also accepts
//! without `;`) that a letter or digit follows stays as written, as the
//! browser reads it: `title="a&notin"` keeps `a&notin`, where text shows
//! `a¬in`. Vue's compiler writes `a¬in` in the attribute too; Citry follows
//! the browser. Each case runs on the S2 emitter in `vize_s1_to_s2` alone and
//! on the patched `vize_atelier_core` code generator alone, with the options
//! Citry uses, and checks that the render code contains the expected
//! fragment.

#![allow(clippy::disallowed_macros)]

use vize_atelier_core::ErrorCode;
use vize_atelier_dom::{Allocator, DomCompilerOptions, compile_template_legacy_with_options};
use vize_s1_to_s2::{DomEmitOptions, LegacyCaps, emit_dom_source_with_options};

/// (template, a part of the render code for it)
const CASES: &[(&str, &str)] = &[
    // Each reference decodes once, in an attribute value and in text.
    (
        r#"<p title="&amp;#40;">&amp;#40; &#40; &amp;amp;#65;</p>"#,
        r#"_createElementBlock("p", { title: "&#40;" }, "&#40; ( &amp;#65;")"#,
    ),
    (r#"<p title="&amp;#x22;">t</p>"#, r#"{ title: "&#x22;" }"#),
    // The attribute rule keeps `&not` before a letter; text decodes it.
    (
        r#"<p title="a&notin">a&notin</p>"#,
        "{ title: \"a&notin\" }, \"a\u{ac}in\")",
    ),
    // A static `is` is an attribute value too, escaped for the literal.
    (
        r#"<component is="a&amp;b"></component>"#,
        r#"_resolveDynamicComponent("a&b")"#,
    ),
    (
        r#"<component is="a&quot;b"></component>"#,
        r#"_resolveDynamicComponent("a\"b")"#,
    ),
    // A static `style` decodes before it is split at `;`, so `&quot;` stays
    // inside its declaration.
    (
        r#"<p style="font-family:&quot;A B&quot;,serif" :style="x">t</p>"#,
        r#"_normalizeStyle([{"font-family":"\"A B\",serif"}, _ctx.x])"#,
    ),
];

/// The S2 lane alone, with comments kept when `comments` is set.
fn emit_s2_with(source: &str, comments: bool) -> Result<String, String> {
    let allocator = Allocator::new();
    let options = DomEmitOptions {
        prefix_identifiers: true,
        hoist_static: false,
        comments,
        ..DomEmitOptions::DEFAULT
    };
    emit_dom_source_with_options(&allocator, source, LegacyCaps::VUE3, &options)
        .map(|emitted| emitted.assembled().to_string())
        .map_err(|error| format!("{error:?}"))
}

/// The S2 lane alone, as Citry compiles.
fn emit_s2(source: &str) -> Result<String, String> {
    emit_s2_with(source, false)
}

/// The `vize_atelier_core` lane alone, with S2 turned off: the render code
/// and the codes of the errors it reports.
fn emit_shipped_with(source: &str, comments: bool) -> (String, Vec<ErrorCode>) {
    let allocator = Allocator::new();
    let options = DomCompilerOptions {
        prefix_identifiers: true,
        hoist_static: false,
        cache_handlers: false,
        comments,
        ..DomCompilerOptions::default()
    };
    let (_, errors, result) = compile_template_legacy_with_options(&allocator, source, options);
    let codes = errors.iter().map(|error| error.code).collect();
    (format!("{}\n{}", result.preamble, result.code), codes)
}

/// The `vize_atelier_core` lane alone, as Citry compiles.
fn emit_shipped(source: &str) -> (String, Vec<ErrorCode>) {
    emit_shipped_with(source, false)
}

#[test]
fn static_references_decode_once_on_both_lanes() {
    for (source, expected) in CASES {
        // Each case must compile on S2 rather than fall back.
        let s2 = emit_s2(source).unwrap_or_else(|error| panic!("S2 refused {source:?}: {error}"));
        assert!(
            s2.contains(expected),
            "{source}\nexpected\n{expected}\nin S2\n{s2}"
        );
        let (shipped, errors) = emit_shipped(source);
        assert!(errors.is_empty(), "{source}: {errors:?}");
        assert!(
            shipped.contains(expected),
            "{source}\nexpected\n{expected}\nin vize_atelier_core\n{shipped}"
        );
    }
}

#[test]
fn a_dynamic_slot_name_that_is_not_javascript_is_an_invalid_expression() {
    // A dynamic argument is part of the attribute name, so `&amp;` stays as
    // written and the name is not JavaScript. Vue reports an invalid
    // expression. S2 refuses, so `vize_atelier_core` compiles the template
    // and reports it too, rather than S2 writing an empty slot name.
    for source in [
        r#"<C><template #[x&amp;y]>t</template></C>"#,
        r#"<C v-slot:[n&amp;m]="p">t</C>"#,
    ] {
        assert!(emit_s2(source).is_err(), "S2 wrote {source:?}");
        let (_, errors) = emit_shipped(source);
        assert!(
            errors.contains(&ErrorCode::InvalidExpression),
            "{source}: {errors:?}"
        );
    }
}

#[test]
fn a_kept_comment_keeps_its_references_on_both_lanes() {
    // Citry drops comments, but a lane that keeps them must write the text as
    // written, as Vue does.
    let source = r#"<p><!--a&#40;b-->t</p>"#;
    let expected = r#"_createCommentVNode("a&#40;b")"#;
    let s2 = emit_s2_with(source, true).unwrap_or_else(|error| panic!("S2 refused: {error}"));
    assert!(s2.contains(expected), "S2\n{s2}");
    let (shipped, errors) = emit_shipped_with(source, true);
    assert!(errors.is_empty(), "{errors:?}");
    assert!(shipped.contains(expected), "vize_atelier_core\n{shipped}");
}
