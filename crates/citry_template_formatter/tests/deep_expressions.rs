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
