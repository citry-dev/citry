//! The formatter handles the deepest expressions the parser accepts.
//!
//! Ruff's formatter and the syntax-tree comparisons call themselves once per
//! tree level, with larger frames than python_safe_eval's passes. These tests run
//! on a thread with a 256 KiB stack, much smaller than Rust's 2 MiB default
//! for spawned threads, so a missing stack guard aborts this test binary.

use citry_template_formatter::format_template;

/// Shapes that nest the tree, each repeated `n` times.
fn shapes(n: usize) -> Vec<String> {
    vec![
        "1".to_string() + &"+1".repeat(n),
        "[".repeat(n) + &"]".repeat(n),
        "not ".repeat(n) + "x",
        "a".to_string() + &".b".repeat(n),
        "f".to_string() + &"()".repeat(n),
        "1 if x else ".repeat(n) + "2",
        "lambda: ".repeat(n) + "1",
    ]
}

/// The deepest expression of each shape that the parser accepts.
///
/// Formatting adds parentheses to some of them, so the depth bound of their
/// formatted text is above the limit of 200. `format_template` must still
/// succeed, keeping them as written.
fn deepest_accepted() -> Vec<String> {
    let accepted = |expression: &str| {
        citry_template_parser::parser::parse_template(
            &format!("{{{{ {expression} }}}}"),
            None,
            None,
        )
        .is_ok()
    };
    (0..shapes(1).len())
        .map(|shape| {
            let mut n = 1;
            while accepted(&shapes(n + 1)[shape]) {
                n += 1;
            }
            shapes(n).swap_remove(shape)
        })
        .collect()
}

#[test]
fn the_deepest_accepted_expressions_format_on_a_small_stack() {
    // Find the limits on a large stack first, so only formatting runs on the
    // small one.
    let expressions = deepest_accepted();
    std::thread::Builder::new()
        .stack_size(256 * 1024)
        .spawn(move || {
            for expression in expressions {
                for template in [
                    format!("<p>{{{{ {expression} }}}}</p>"),
                    format!("<p c-title=\"{expression}\"></p>"),
                ] {
                    if let Err(error) = format_template(&template) {
                        panic!("{expression:.60}: {error}");
                    }
                }
            }
        })
        .unwrap()
        .join()
        .unwrap();
}

#[test]
fn the_deepest_accepted_c_for_clause_formats() {
    // A `c-for` clause has its own generator wrapper. Wrapping it a second
    // time would push a clause at the parser's limit over it, so the
    // formatter would reject a template the parser accepts.
    let accepted = |terms: usize| {
        let clause = format!("x in a{}", "+a".repeat(terms));
        let template = format!("<c-for each=\"{clause}\"><b>{{{{ x }}}}</b></c-for>");
        citry_template_parser::parser::parse_template(&template, None, None)
            .is_ok()
            .then_some(template)
    };
    let mut terms = 1;
    while accepted(terms + 1).is_some() {
        terms += 1;
    }
    let template = accepted(terms).expect("a short clause parses");
    let skipped = template.replace("\"><b>", "  # fmt: skip\n\"><b>");
    for template in [template, skipped] {
        if let Err(error) = format_template(&template) {
            panic!("{terms} terms: {error}");
        }
    }
}

#[test]
fn a_multiline_expression_at_the_depth_limit_settles() {
    // When Ruff's output would nest past the parser's limit, the formatter
    // keeps the author's text. It must keep the bytes as they are: indenting
    // the kept text again on every pass would never settle.
    let accepted = |terms: usize| {
        let template = format!("<p>{{{{ a\n{} }}}}</p>", "+a\n".repeat(terms));
        citry_template_parser::parser::parse_template(&template, None, None)
            .is_ok()
            .then_some(template)
    };
    let mut terms = 1;
    while accepted(terms + 1).is_some() {
        terms += 1;
    }
    let template = accepted(terms).expect("a short expression parses");
    let formatted = format_template(&template).unwrap_or_else(|error| panic!("{terms}: {error}"));
    assert_eq!(format_template(&formatted).unwrap(), formatted);
}
