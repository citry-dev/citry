//! Citry regressions for event-handler statements and line comments.
//!
//! `@vue/compiler-core` reads expression text as a list of statements only
//! for an event handler whose text contains `;`. This emitter refuses the
//! text that the `vize_atelier_core` transform reports as an invalid
//! expression, so the caller falls back to that transform and reports it.
//! These tests emit with `prefix_identifiers`, as Citry does, and compare
//! the handler that is written with the one Vue 3.5 writes for the same
//! template. Where Vue writes JavaScript that does not parse, the test says
//! so and checks that this emitter writes JavaScript that does.

#![allow(
    clippy::disallowed_macros,
    clippy::disallowed_types,
    clippy::disallowed_methods
)]

use oxc_parser::Parser;
use oxc_span::SourceType;
use vize_s0::Allocator;
use vize_s1_to_s2::{
    DomEmitOptions, EmitError, LegacyCaps, UnsupportedReason, emit_dom_source_with_options,
};

fn emit_with(source: &str, is_ts: bool) -> Result<String, EmitError> {
    emit_with_prefixing(source, true, is_ts)
}

fn emit_with_prefixing(
    source: &str,
    prefix_identifiers: bool,
    is_ts: bool,
) -> Result<String, EmitError> {
    let allocator = Allocator::new();
    emit_dom_source_with_options(
        &allocator,
        source,
        LegacyCaps::VUE3,
        &DomEmitOptions {
            prefix_identifiers,
            is_ts,
            ..DomEmitOptions::DEFAULT
        },
    )
    .map(|emitted| emitted.assembled().to_string())
}

fn assembled(source: &str) -> String {
    emit_with(source, false).unwrap_or_else(|error| panic!("emit refused {source:?}: {error:?}"))
}

fn refused_reason(source: &str, is_ts: bool) -> Option<UnsupportedReason> {
    match emit_with(source, is_ts) {
        Ok(output) => panic!("emit accepted {source:?} (is_ts={is_ts}):\n{output}"),
        Err(error) => error.reason(),
    }
}

/// The render module must parse, or the browser rejects the whole template.
fn assert_parses_as_javascript(output: &str) {
    let allocator = Allocator::new();
    let parsed = Parser::new(allocator.as_oxc(), output, SourceType::mjs()).parse();
    assert!(
        parsed.diagnostics.is_empty(),
        "generated code does not parse: {:?}\n{output}",
        parsed.diagnostics
    );
}

/// The `is_ts` values to test. Without the `typescript` feature, every
/// `is_ts` emit is refused for that reason alone, so only `false` is tested.
fn typescript_cases() -> &'static [bool] {
    if cfg!(feature = "typescript") {
        &[false, true]
    } else {
        &[false]
    }
}

#[test]
fn handler_without_semicolon_must_be_one_expression() {
    // Vue reports "Error parsing JavaScript expression" for this handler.
    for &is_ts in typescript_cases() {
        assert_eq!(
            refused_reason(r#"<button @click="if (ok) run()"></button>"#, is_ts),
            Some(UnsupportedReason::PrefixExpressionRejected),
            "is_ts={is_ts}"
        );
    }
}

#[test]
fn handler_with_semicolon_compiles_as_statements() {
    // Vue writes exactly these handlers.
    for (source, handler) in [
        (
            r#"<button @click="a; b()"></button>"#,
            "onClick: $event => {_ctx.a; _ctx.b()}",
        ),
        (
            r#"<button @click="if (ok) run();"></button>"#,
            "onClick: $event => {if (_ctx.ok) _ctx.run();}",
        ),
    ] {
        let output = assembled(source);
        assert!(output.contains(handler), "{source}: {output}");
        assert_parses_as_javascript(&output);
    }
}

#[test]
fn function_followed_by_a_statement_is_not_a_function_handler() {
    // Vue checks only the first statement here and writes the text
    // unwrapped (`onClick: () => _ctx.run(); _ctx.log()`), which does not
    // parse. The whole text is two statements, so it takes the block form.
    let output = assembled(r#"<button @click="() => run(); log()"></button>"#);
    assert!(
        output.contains("onClick: $event => {() => _ctx.run(); _ctx.log()}"),
        "{output}"
    );
    assert_parses_as_javascript(&output);
}

#[test]
fn statements_in_interpolations_and_conditions_are_refused() {
    // Vue reports each of these as an invalid expression.
    for source in [
        r#"<p>{{ a; b }}</p>"#,
        r#"<p>{{ if (a) b }}</p>"#,
        r#"<p v-if="a; b">x</p>"#,
    ] {
        for &is_ts in typescript_cases() {
            assert_eq!(
                refused_reason(source, is_ts),
                Some(UnsupportedReason::PrefixExpressionRejected),
                "{source} is_ts={is_ts}"
            );
        }
    }
}

#[test]
fn trailing_line_comment_cannot_hide_the_end_of_a_block_handler() {
    // Vue writes `$event => {_ctx.count++; _ctx.log() // note},` here, so the
    // comment swallows the closing `}` and the `,` before `title`.
    let output = assembled(r#"<button @click="count++; log() // note" :title="t"></button>"#);
    assert!(
        output.contains("onClick: $event => {_ctx.count++; _ctx.log() /*  note */},\n"),
        "{output}"
    );
    assert_parses_as_javascript(&output);

    // A `//` inside a string is not a comment, so the text stays as written,
    // as it does in Vue.
    let in_string = assembled(r#"<button @click="count++; run('a // b')"></button>"#);
    assert!(
        in_string.contains("onClick: $event => {_ctx.count++; _ctx.run('a // b')}"),
        "{in_string}"
    );
    assert_parses_as_javascript(&in_string);

    // With the newline the author typed, Vue's unchanged comment
    // (`onClick: _ctx.foo // note`) still parses. This copy converts the
    // comment anyway, as `vize_atelier_core`'s codegen does, and this case
    // pins that conversion.
    let reference = assembled("<button @click=\"foo // note\n\" :title=\"t\"></button>");
    assert!(
        reference.contains("onClick: _ctx.foo /*  note */\n,"),
        "{reference}"
    );
    assert_parses_as_javascript(&reference);
}

#[test]
fn trailing_line_comment_cannot_hide_the_end_of_an_unprefixed_handler() {
    // Without prefixing, a handler that is one expression is written as
    // authored. Vue, with `prefixIdentifiers`, reports both templates as
    // invalid expressions; writing the comment unchanged would hide the `)`
    // or `,` that follows it.
    for (source, handler) in [
        (
            r#"<button @click="run() // note" :title="t"></button>"#,
            "onClick: $event => (run() /*  note */),\n",
        ),
        (
            r#"<button @click="foo // note" :title="t"></button>"#,
            "onClick: foo /*  note */,\n",
        ),
    ] {
        let output = emit_with_prefixing(source, false, false)
            .unwrap_or_else(|error| panic!("emit refused {source:?}: {error:?}"));
        assert!(output.contains(handler), "{source}: {output}");
        assert_parses_as_javascript(&output);
    }
}

#[cfg(feature = "typescript")]
#[test]
fn typescript_handler_reference_stays_a_reference() {
    // `foo!` is the reference `foo` once its type syntax is removed, so it is
    // passed on unwrapped. Wrapping it as `$event => (_ctx.foo)` would return
    // the function instead of calling it. Vue writes `_ctx.foo!`.
    let output = emit_with(r#"<button @click="foo!"></button>"#, true)
        .unwrap_or_else(|error| panic!("emit refused: {error:?}"));
    assert!(output.contains("{ onClick: _ctx.foo }"), "{output}");
    assert_parses_as_javascript(&output);
}
