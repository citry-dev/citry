//! Deeply nested templates parse and compile on a small thread.
//!
//! The compiler, the parse of a template written in an attribute value, and
//! printing a `Template` call themselves once per nesting level, so each
//! level runs through a stack guard that moves the work to a new stack
//! segment when the current one runs low. The parser's other passes, and
//! cloning, comparing and dropping a `Template`, keep their own list of
//! what is left to visit.
//!
//! These tests parse, clone, compare, print, compile and drop templates up to
//! 512 tags deep (512 for plain elements, 256 for control-flow and component
//! tags) on threads with 256 KiB and 128 KiB stacks. 128 KiB is the default
//! for threads on musl Linux, and Rust spawns threads with 2 MiB by default.
//! A crash aborts this test binary, which fails the test run.
//!
//! Each test enters the parser through `with_enough_stack`, as the Python
//! bindings do for each parse and compile call. Called with no guard at
//! entry, a debug build's parse and compile need about 100 KB of the
//! thread's own stack at any depth, and a 128 KiB Windows thread does not
//! have that free: a new Windows thread has about 26 KiB less of its stack
//! free than a Linux one (a 256 KiB thread reports 228,896 bytes left on
//! Windows and 255,024 on Linux). The entry guard sees how little is left
//! and moves the work to a new stack segment taken from the heap, so a
//! caller that enters the way the bindings do is safe on any thread.
//!
//! On a 256 KiB thread, and on a 128 KiB thread outside Windows, more than
//! the guard's red zone (the amount below which it switches stacks) is
//! left, so the guards inside the parser still switch stacks there and a
//! missing one still crashes the test. A separate test enters the guard
//! with just over its red zone left, the least a guarded caller can bring.

use citry_template_parser::ast::Template;
use citry_template_parser::ast::{Comment, StaticNamedSlot, TemplateElement, Token};
use citry_template_parser::compiler::{compile_prepared_template, compile_template};
use citry_template_parser::nesting::{MAX_LOGIC_NESTING, MAX_TAG_NESTING};
use citry_template_parser::parser::parse_template;
use citry_template_parser::stack::{with_enough_stack, RED_ZONE};

/// Tags nested in the deepest templates these tests build: the most a
/// template may nest.
const TOTAL_DEPTH: usize = MAX_TAG_NESTING;

/// Citry logic levels nested in the deepest templates: the most a template
/// may nest.
const LOGIC_DEPTH: usize = MAX_LOGIC_NESTING;

/// Parse, clone, compare, print, compile and drop `source`.
fn parse_and_compile(source: &str) {
    let template: Template =
        parse_template(source, None, None).unwrap_or_else(|error| panic!("{error}"));
    let copy = template.clone();
    // Comparing and printing walk the whole tree; Python reaches them
    // through `==` and `repr()`.
    assert!(copy == template);
    assert!(!format!("{template:?}").is_empty());
    compile_template(template.clone(), None).unwrap();
    compile_prepared_template(template.clone(), None).unwrap();
    drop(template);
    drop(copy);
}

/// Run `parse_and_compile` on threads with small stacks, entering through
/// the guard as the Python bindings do.
fn handles_on_small_stacks(source: String) {
    for stack_size in [256 * 1024, 128 * 1024] {
        let source = source.clone();
        std::thread::Builder::new()
            .stack_size(stack_size)
            .spawn(move || {
                // Without room above the red zone the entry guard moves all
                // the work to the heap, and the inner guards go untested.
                // Windows keeps more of each thread back, so its 128 KiB
                // thread is the one case that runs on the heap.
                if !(cfg!(windows) && stack_size < 256 * 1024) {
                    let left = stacker::remaining_stack().unwrap();
                    assert!(left > RED_ZONE, "{left} bytes left");
                }
                with_enough_stack(|| parse_and_compile(&source));
            })
            .unwrap()
            .join()
            .unwrap_or_else(|_| panic!("failed on a {stack_size}-byte stack"));
    }
}

/// Use stack until at most `left` bytes remain, then run `work`.
#[inline(never)]
fn with_stack_left(left: usize, work: &mut dyn FnMut()) {
    // Each level takes a little over 512 bytes, so the call lands within
    // about 1 KiB above `left`.
    let pad = std::hint::black_box([0u8; 512]);
    if stacker::remaining_stack().unwrap() > left + 1024 {
        with_stack_left(left, work);
    } else {
        work();
    }
    std::hint::black_box(&pad);
}

/// `open` repeated `depth` times around `inner`, closed by `close`.
fn nest(open: &str, inner: &str, close: &str, depth: usize) -> String {
    format!("{}{inner}{}", open.repeat(depth), close.repeat(depth))
}

#[test]
fn nested_elements() {
    handles_on_small_stacks(nest("<div>", "{{ x }}", "</div>", TOTAL_DEPTH));
}

#[test]
fn nested_if_tags() {
    handles_on_small_stacks(nest("<c-if cond=\"x\">", "{{ x }}", "</c-if>", LOGIC_DEPTH));
}

#[test]
fn nested_for_tags_that_each_bind_a_variable() {
    // Every level introduces a name and the body reads all of them, so the
    // used-variable and binding passes walk the whole depth.
    let open: String = (0..LOGIC_DEPTH)
        .map(|level| format!("<c-for each=\"v{level} in items\">"))
        .collect();
    let used: String = (0..LOGIC_DEPTH)
        .map(|level| format!("{{{{ v{level} }}}}"))
        .collect();
    handles_on_small_stacks(format!("{open}{used}{}", "</c-for>".repeat(LOGIC_DEPTH)));
}

#[test]
fn nested_control_flow_attributes() {
    handles_on_small_stacks(nest("<div c-if=\"x\">", "{{ x }}", "</div>", LOGIC_DEPTH));
}

#[test]
fn control_flow_and_elements_mixed() {
    // 256 `<c-if>` tags, each around a `<div>`: 512 tags in all.
    handles_on_small_stacks(nest(
        "<c-if cond=\"x\"><div>",
        "{{ x }}",
        "</div></c-if>",
        TOTAL_DEPTH / 2,
    ));
}

#[test]
fn nested_components() {
    handles_on_small_stacks(nest("<c-my-comp>", "{{ x }}", "</c-my-comp>", LOGIC_DEPTH));
}

#[test]
fn a_fill_under_deep_control_flow_in_a_component() {
    // The parser collects a component's fills through the control flow
    // around them. The component and the fill are logic levels too, so this
    // nests exactly LOGIC_DEPTH of them.
    let deep_fill = nest(
        "<c-if cond=\"x\">",
        "<c-fill name=\"a\">{{ x }}</c-fill>",
        "</c-if>",
        LOGIC_DEPTH - 2,
    );
    handles_on_small_stacks(format!("<c-my-comp>{deep_fill}</c-my-comp>"));
}

#[test]
fn deep_content_under_c_ignore() {
    // `#c-ignore` makes the parser check the whole subtree under it.
    let inner = nest("<div>", "x", "</div>", TOTAL_DEPTH - 1);
    handles_on_small_stacks(format!("<div #c-ignore>{inner}</div>"));
}

#[test]
fn deep_template_in_an_attribute() {
    // A template written inside an attribute value is parsed on its own.
    let inner = nest("<div>", "{{ x }}", "</div>", TOTAL_DEPTH - 1);
    handles_on_small_stacks(format!("<c-my-tag c-body=\"{inner}\" />"));
}

#[test]
fn printing_a_template_matches_the_derived_format() {
    // `Template` prints itself through the stack guard; the text must be
    // what `#[derive(Debug)]` would print, which tests elsewhere compare.
    #[derive(Debug)]
    #[allow(dead_code)]
    struct Template<'a> {
        elements: &'a Vec<TemplateElement>,
        comments: &'a Vec<Comment>,
        used_variables: &'a Vec<Token>,
        slots: &'a Vec<StaticNamedSlot>,
    }
    let source = "<div>{# note #}<c-slot name=\"a\">{{ x }}</c-slot><p c-if=\"y\">t</p></div>";
    let template = parse_template(source, None, None).unwrap();
    let derived = Template {
        elements: &template.elements,
        comments: &template.comments,
        used_variables: &template.used_variables,
        slots: &template.slots,
    };
    assert_eq!(format!("{template:?}"), format!("{derived:?}"));
    assert_eq!(format!("{template:#?}"), format!("{derived:#?}"));
}

#[test]
fn an_invalid_expression_fails_cleanly_on_a_small_stack() {
    // Reporting an invalid expression needs far more stack than parsing a
    // valid one, at any depth, in the template or in an attribute value.
    for source in [
        "{{ x + }}".to_string(),
        "<c-x c-body=\"<div>{{ x + }}</div>\" />".to_string(),
        nest("<c-if cond=\"x\">", "{{ x + }}", "</c-if>", LOGIC_DEPTH),
    ] {
        std::thread::Builder::new()
            .stack_size(128 * 1024)
            // Enter through the guard, as the Python bindings do.
            .spawn(move || {
                with_enough_stack(|| {
                    let error = parse_template(&source, None, None).unwrap_err();
                    assert!(
                        error.to_string().contains("Failed to parse expression"),
                        "{error}"
                    );
                });
            })
            .unwrap()
            .join()
            .unwrap();
    }
}

#[test]
fn the_entry_guard_holds_deep_templates_from_just_above_its_red_zone() {
    // A guarded caller can arrive with just over the red zone left, and the
    // guard then keeps the work on the thread's stack. The code before the
    // first inner guard must fit in what is left, at the deepest templates.
    let inner = nest("<div>", "{{ x }}", "</div>", TOTAL_DEPTH - 1);
    let sources = [
        nest("<div>", "{{ x }}", "</div>", TOTAL_DEPTH),
        nest("<c-if cond=\"x\">", "{{ x }}", "</c-if>", LOGIC_DEPTH),
        nest("<div c-if=\"x\">", "{{ x }}", "</div>", LOGIC_DEPTH),
        nest("<c-my-comp>", "{{ x }}", "</c-my-comp>", LOGIC_DEPTH),
        format!(
            "<div #c-ignore>{}</div>",
            nest("<div>", "x", "</div>", TOTAL_DEPTH - 1)
        ),
        format!("<c-my-tag c-body=\"{inner}\" />"),
    ];
    let invalid = nest("<c-if cond=\"x\">", "{{ x + }}", "</c-if>", LOGIC_DEPTH);
    std::thread::Builder::new()
        .stack_size(8 * 1024 * 1024)
        .spawn(move || {
            for source in &sources {
                with_stack_left(RED_ZONE, &mut || {
                    with_enough_stack(|| parse_and_compile(source));
                });
            }
            with_stack_left(RED_ZONE, &mut || {
                with_enough_stack(|| assert!(parse_template(&invalid, None, None).is_err()));
            });
        })
        .unwrap()
        .join()
        .unwrap();
}
