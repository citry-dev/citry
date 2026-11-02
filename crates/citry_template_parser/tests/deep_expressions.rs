//! Deep expressions and deep `{` nesting end in a clean error, never a crash.
//!
//! The template grammar calls itself once per `{` inside `{{ ... }}`, and the
//! expression passes call themselves once per tree level. These tests run on
//! a thread with a 256 KiB stack, much smaller than Rust's 2 MiB default for
//! spawned threads, so a missing stack guard or depth check aborts this test
//! binary.

use citry_template_parser::parser::parse_template;

/// Run `check` on a thread with a 256 KiB stack.
fn on_small_stack(check: impl FnOnce() + Send + 'static) {
    std::thread::Builder::new()
        .stack_size(256 * 1024)
        .spawn(check)
        .unwrap()
        .join()
        .unwrap();
}

/// The parse error's text, for a template that must fail.
fn parse_error(source: &str) -> String {
    format!("{:?}", parse_template(source, None, None).unwrap_err())
}

#[test]
fn deep_braces_in_an_expression_fail_cleanly() {
    on_small_stack(|| {
        // Below the brace limit the grammar runs on a stack sized for the
        // count, and the expression check then rejects the expression. Past
        // it, the parser stops before the grammar runs. The two braces of
        // `{{` count too.
        for (depth, expected) in [
            (300, "expression is nested too deeply"),
            (20_000, "expression is nested too deeply"),
            // The most braces accepted, the largest stack the grammar asks for.
            (99_998, "expression is nested too deeply"),
            (99_999, "holds more than 100000 `{` characters"),
            (200_000, "holds more than 100000 `{` characters"),
        ] {
            let source = format!("{{{{ {}{} }}}}", "{".repeat(depth), "}".repeat(depth));
            let error = parse_error(&source);
            assert!(error.contains(expected), "depth {depth}: {error}");
        }
    });
}

#[test]
fn braces_closed_inside_strings_and_comments_fail_cleanly() {
    on_small_stack(|| {
        // The grammar skips a `}` inside a Python string or `#` comment, so
        // these open one grammar level per `{` while a count that also
        // subtracted every `}` would stay near zero. 1,000 levels is far past
        // what a 256 KiB stack holds without the guard (about 150), and keeps
        // the 1,000-line comment case fast.
        for repeated in ["{'}'", "{\"}\"", "{# }\n"] {
            let source = format!("{{{{ {}{} }}}}", repeated.repeat(1_000), "}".repeat(1_000));
            let error = parse_error(&source);
            assert!(
                error.contains("expression is nested too deeply"),
                "{repeated}: {error:.300}"
            );
        }
    });
}

#[test]
fn deep_braces_in_text_still_parse() {
    on_small_stack(|| {
        // Braces in text are not expressions, so only the brace limit applies
        // to them, far above what a typical style or script holds. They are
        // spaced, because `{{` would start a template expression.
        let style = format!("<style>{}{}</style>", "{ ".repeat(500), "} ".repeat(500));
        assert!(parse_template(&style, None, None).is_ok());
    });
}

#[test]
fn deep_expressions_in_a_template_fail_cleanly() {
    on_small_stack(|| {
        for depth in [150, 10_000] {
            for expression in [
                "[".repeat(depth) + &"]".repeat(depth),
                "1".to_string() + &"+1".repeat(depth),
                "not ".repeat(depth) + "x",
                "-".repeat(depth) + "1",
                "a".to_string() + &".b".repeat(depth),
                "1 if x else ".repeat(depth) + "2",
            ] {
                let error = parse_error(&format!("{{{{ {expression} }}}}"));
                assert!(error.contains("expression is nested too deeply"), "{error}");
                let error = parse_error(&format!("<p c-title=\"{expression}\"></p>"));
                assert!(error.contains("expression is nested too deeply"), "{error}");
            }
        }
    });
}

#[test]
fn ordinary_deep_expressions_still_parse_on_a_small_stack() {
    on_small_stack(|| {
        // 60 nested lists stay within the expression limit (65).
        let expression = "[".repeat(60) + &"]".repeat(60);
        assert!(parse_template(&format!("{{{{ {expression} }}}}"), None, None).is_ok());
    });
}
