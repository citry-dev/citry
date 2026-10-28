//! Templates may nest 512 tags of any kind and 256 of Citry's logic levels.
//!
//! At each limit a template parses and compiles. One level more is a
//! `citry.parse.too-deep` error that points at the tag that goes too deep.
//! These tests cover how levels are counted: control-flow shorthand
//! attributes add wrappers, `<c-else>` is a sibling, void and self-closing
//! tags count, and a template in an attribute continues its parent's depth.

use citry_template_parser::ast::{Node, Template, TemplateElement};
use citry_template_parser::compiler::{compile_prepared_template, compile_template};
use citry_template_parser::error::{CompileError, ParseError};
use citry_template_parser::nesting::{MAX_LOGIC_NESTING, MAX_TAG_NESTING};
use citry_template_parser::parser::parse_template;

fn nest(open: &str, inner: &str, close: &str, depth: usize) -> String {
    format!("{}{inner}{}", open.repeat(depth), close.repeat(depth))
}

/// `depth` nested copies of `open`, where `{i}` in it becomes each level's
/// number, so loops at different levels bind different names.
fn nest_numbered(open: &str, inner: &str, close: &str, depth: usize) -> String {
    let opens: String = (0..depth)
        .map(|level| open.replace("{i}", &level.to_string()))
        .collect();
    format!("{opens}{inner}{}", close.repeat(depth))
}

/// Parse and compile `source` in both output modes; all three must succeed.
fn accepts(source: &str) {
    let template = parse_template(source, None, None).unwrap_or_else(|error| panic!("{error}"));
    compile_template(template.clone(), None).unwrap();
    compile_prepared_template(template, None).unwrap();
}

/// Parse `source`, which must fail as too deep; return the diagnostic.
fn rejects(source: &str) -> citry_template_parser::error::ParseDiagnostic {
    let error = parse_template(source, None, None).unwrap_err();
    assert!(matches!(error, ParseError::TooDeep(..)), "{error:?}");
    let diagnostic = error.diagnostic();
    assert_eq!(diagnostic.code, "citry.parse.too-deep");
    diagnostic
}

/// The byte offset of the `n`th (0-based) occurrence of `needle` in `source`.
fn offset_of(source: &str, needle: &str, n: usize) -> usize {
    source.match_indices(needle).nth(n).unwrap().0
}

#[test]
fn the_limits_are_512_and_256() {
    assert_eq!(MAX_TAG_NESTING, 512);
    assert_eq!(MAX_LOGIC_NESTING, 256);
}

#[test]
fn plain_elements_nest_to_the_total_limit() {
    accepts(&nest("<div>", "x", "</div>", MAX_TAG_NESTING));
    let source = nest("<div>", "x", "</div>", MAX_TAG_NESTING + 1);
    let diagnostic = rejects(&source);
    // The 513th <div> is the one that goes too deep, on line 1.
    let tag = offset_of(&source, "<div>", MAX_TAG_NESTING);
    assert_eq!(diagnostic.start_index, Some(tag));
    assert_eq!(
        (diagnostic.start_line, diagnostic.start_column),
        (Some(1), Some(tag + 1))
    );
    assert!(
        diagnostic
            .message
            .contains("This <div> is nested 513 levels deep"),
        "{}",
        diagnostic.message
    );
}

#[test]
fn logic_tags_nest_to_the_logic_limit() {
    accepts(&nest(
        "<c-if cond=\"x\">",
        "x",
        "</c-if>",
        MAX_LOGIC_NESTING,
    ));
    let source = nest("<c-if cond=\"x\">", "x", "</c-if>", MAX_LOGIC_NESTING + 1);
    let diagnostic = rejects(&source);
    assert_eq!(
        diagnostic.start_index,
        Some(offset_of(&source, "<c-if", MAX_LOGIC_NESTING))
    );
    assert!(
        diagnostic
            .message
            .contains("This <c-if> is 257 Citry logic levels deep"),
        "{}",
        diagnostic.message
    );
}

#[test]
fn components_slots_and_fills_are_logic_levels() {
    // Each level is a component holding a fill holding the next component:
    // two logic levels per step.
    let step_open = "<c-card><c-fill name=\"default\">";
    let step_close = "</c-fill></c-card>";
    accepts(&nest(step_open, "x", step_close, MAX_LOGIC_NESTING / 2));
    let diagnostic = rejects(&nest(
        step_open,
        "<c-card>x</c-card>",
        step_close,
        MAX_LOGIC_NESTING / 2,
    ));
    assert!(
        diagnostic.message.contains("<c-card>"),
        "{}",
        diagnostic.message
    );
    // <c-raw> is a Citry tag but not a logic level.
    accepts(&nest(
        "<c-if cond=\"x\">",
        "<c-raw>x</c-raw>",
        "</c-if>",
        MAX_LOGIC_NESTING,
    ));
}

#[test]
fn each_shorthand_attribute_adds_a_wrapper_level() {
    // `<div c-if c-for>` is three levels, two of them logic.
    let open = "<div c-if=\"x\" c-for=\"y{i} in z\">";
    accepts(&nest_numbered(open, "x", "</div>", MAX_LOGIC_NESTING / 2));
    let diagnostic = rejects(&nest_numbered(
        open,
        "x",
        "</div>",
        MAX_LOGIC_NESTING / 2 + 1,
    ));
    assert!(
        diagnostic
            .message
            .contains("is 258 Citry logic levels deep"),
        "{}",
        diagnostic.message
    );
    // The wrappers count toward the total limit too. `<p c-for>` is two
    // levels, one of them logic, so 256 of them sit at both limits, and one
    // more plain tag inside goes past the total one.
    let open = "<p c-for=\"y{i} in z\">";
    accepts(&nest_numbered(open, "x", "</p>", MAX_LOGIC_NESTING));
    let diagnostic = rejects(&nest_numbered(open, "<b>x</b>", "</p>", MAX_LOGIC_NESTING));
    assert!(
        diagnostic
            .message
            .contains("This <b> is nested 513 levels deep"),
        "{}",
        diagnostic.message
    );
}

#[test]
fn else_and_elif_are_siblings_of_their_if() {
    let inner = "<c-if cond=\"a\">1</c-if><c-elif cond=\"b\">2</c-elif><c-else>3</c-else>";
    accepts(&nest(
        "<c-if cond=\"x\">",
        inner,
        "</c-if>",
        MAX_LOGIC_NESTING - 1,
    ));
}

#[test]
fn shorthands_on_void_and_self_closing_tags_count() {
    // 510 <div> tags, then a <br> with a wrapper: 512 levels.
    accepts(&nest(
        "<div>",
        "<br c-if=\"x\">",
        "</div>",
        MAX_TAG_NESTING - 2,
    ));
    rejects(&nest(
        "<div>",
        "<br c-if=\"x\">",
        "</div>",
        MAX_TAG_NESTING - 1,
    ));
    // 254 <c-if> tags, then a component with a loop: 256 logic levels.
    accepts(&nest(
        "<c-if cond=\"x\">",
        "<c-row c-for=\"i in xs\" />",
        "</c-if>",
        MAX_LOGIC_NESTING - 2,
    ));
    let diagnostic = rejects(&nest(
        "<c-if cond=\"x\">",
        "<c-row c-for=\"i in xs\" />",
        "</c-if>",
        MAX_LOGIC_NESTING - 1,
    ));
    assert!(
        diagnostic.message.contains("<c-row>"),
        "{}",
        diagnostic.message
    );
}

#[test]
fn a_template_in_an_attribute_counts_from_its_parents_depth() {
    // 510 <div> tags, a component at 511, and a <b> in its attribute
    // template at 512.
    let at_limit = nest(
        "<div>",
        "<c-x c-body='<b>x</b>' />",
        "</div>",
        MAX_TAG_NESTING - 2,
    );
    accepts(&at_limit);
    let source = nest(
        "<div>",
        "<c-x c-body='<b>x</b>' />",
        "</div>",
        MAX_TAG_NESTING - 1,
    );
    let diagnostic = rejects(&source);
    // The error points at the <b> inside the attribute, in the outer source.
    assert_eq!(diagnostic.start_index, Some(offset_of(&source, "<b>", 0)));
}

#[test]
fn a_far_too_deep_template_stops_at_the_first_tag_too_many() {
    let source = nest("<c-if cond=\"x\">", "x", "</c-if>", 100_000);
    let diagnostic = rejects(&source);
    let tag = offset_of(&source, "<c-if", MAX_LOGIC_NESTING);
    assert_eq!(diagnostic.start_index, Some(tag));
    // The template is one 2.2 MB line. The message shows only the part of
    // it around the tag, with the tag's real position in the header.
    assert!(
        diagnostic.message.len() < 2_000,
        "{} bytes",
        diagnostic.message.len()
    );
    assert!(
        diagnostic.message.contains(&format!("--> 1:{}", tag + 1)),
        "{}",
        diagnostic.message
    );
}

/// A tree nested `depth` levels deep, built by hand rather than parsed.
fn hand_built_tree(depth: usize) -> Template {
    let mut template = parse_template("<div>x</div>", None, None).unwrap();
    let TemplateElement::Node(node) = template.elements[0].clone() else {
        unreachable!()
    };
    for _ in 1..depth {
        let mut outer = node.clone();
        let Node::WithBody { body, .. } = &mut outer else {
            unreachable!()
        };
        body.elements = std::mem::take(&mut template.elements);
        template.elements = vec![TemplateElement::Node(outer)];
    }
    template
}

#[test]
fn the_compiler_rejects_a_hand_built_tree_past_the_limit() {
    compile_template(hand_built_tree(MAX_TAG_NESTING), None).unwrap();
    let error = compile_template(hand_built_tree(MAX_TAG_NESTING + 1), None).unwrap_err();
    let CompileError::Syntax(message) = error else {
        panic!("{error:?}")
    };
    assert!(message.contains("nested 513 levels deep"), "{message}");
    assert!(message.contains("line 1, column 1"), "{message}");
}

#[test]
fn raw_and_text_container_tags_count_like_any_tag() {
    // These tags have their own grammar rules, but they nest like any other.
    for inner in [
        "<c-raw>x</c-raw>",
        "<script>x</script>",
        "<style>x</style>",
        "<textarea>x</textarea>",
        "<title>x</title>",
    ] {
        accepts(&nest("<div>", inner, "</div>", MAX_TAG_NESTING - 1));
        let source = nest("<div>", inner, "</div>", MAX_TAG_NESTING);
        let diagnostic = rejects(&source);
        // The error points at the inner tag, the 513th level.
        assert_eq!(
            diagnostic.start_index,
            Some(offset_of(&source, &inner[..inner.find('>').unwrap()], 0)),
            "{inner}"
        );
    }
    // Their shorthand attributes count too.
    let inner = "<textarea c-if=\"y\">x</textarea>";
    accepts(&nest(
        "<c-if cond=\"x\">",
        inner,
        "</c-if>",
        MAX_LOGIC_NESTING - 1,
    ));
    rejects(&nest(
        "<c-if cond=\"x\">",
        inner,
        "</c-if>",
        MAX_LOGIC_NESTING,
    ));
}

#[test]
fn a_template_in_a_text_container_attribute_counts_from_that_tag() {
    // The empty <c-if> sibling must not change where the attribute template
    // starts counting: it starts from the <textarea>'s own depth.
    let deep_attribute = nest("<c-if cond=\"x\">", "x", "</c-if>", MAX_LOGIC_NESTING - 1);
    accepts(&format!(
        "<c-x><c-if cond=\"a\"></c-if><textarea c-body='{deep_attribute}'></textarea></c-x>"
    ));
    // 510 <div> tags, the <textarea> at 511 and two <b> in its attribute at
    // 512 and 513.
    rejects(&nest(
        "<div>",
        "<textarea c-body='<b><b>x</b></b>'></textarea>",
        "</div>",
        MAX_TAG_NESTING - 2,
    ));
}
