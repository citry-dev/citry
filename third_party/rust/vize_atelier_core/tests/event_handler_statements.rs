//! Citry regressions for event-handler statements and line comments.
//!
//! `@vue/compiler-core` reads expression text as a list of statements only
//! for an event handler whose text contains `;`. Every other position must
//! hold one expression, and a statement there is reported as an invalid
//! expression. These tests compile with `prefix_identifiers`, as Citry does,
//! and compare the handler that is written with the one Vue 3.5 writes for
//! the same template. Where Vue writes JavaScript that does not parse, the
//! test says so and checks that this copy writes JavaScript that does.

use oxc_allocator::Allocator as OxcAllocator;
use oxc_parser::Parser;
use oxc_span::SourceType;
use vize_atelier_core::{
    CodegenOptions, CodegenResult, CompilerError, ErrorCode, TransformOptions, generate, parse,
    transform,
};
use vize_s0::String;

struct Compiled {
    output: String,
    errors: Vec<CompilerError>,
}

fn result_output(result: &CodegenResult) -> String {
    let mut output = String::with_capacity(result.preamble.len() + result.code.len() + 1);
    output.push_str(&result.preamble);
    output.push('\n');
    output.push_str(&result.code);
    output
}

fn compile_with(source: &str, prefix_identifiers: bool, is_ts: bool) -> Compiled {
    let allocator = vize_s0::Allocator::new();
    let (mut root, parse_errors) = parse(&allocator, source);
    assert!(parse_errors.is_empty(), "Parse errors: {parse_errors:?}");
    let errors = transform(
        &allocator,
        &mut root,
        TransformOptions {
            prefix_identifiers,
            is_ts,
            ..Default::default()
        },
        None,
    );
    let output = result_output(&generate(
        &root,
        CodegenOptions {
            prefix_identifiers,
            ..Default::default()
        },
    ));
    Compiled { output, errors }
}

/// Compile the way Citry does: identifiers prefixed, JavaScript expressions.
fn compile(source: &str) -> Compiled {
    compile_with(source, true, false)
}

fn has_invalid_expression(compiled: &Compiled) -> bool {
    compiled
        .errors
        .iter()
        .any(|error| error.code == ErrorCode::InvalidExpression)
}

/// The render module must parse, or the browser rejects the whole template.
fn assert_parses_as_javascript(output: &str) {
    let allocator = OxcAllocator::default();
    let parsed = Parser::new(&allocator, output, SourceType::mjs()).parse();
    assert!(
        parsed.diagnostics.is_empty(),
        "generated code does not parse: {:?}\n{output}",
        parsed.diagnostics
    );
}

#[test]
fn handler_without_semicolon_must_be_one_expression() {
    // Vue reports "Error parsing JavaScript expression" for this handler,
    // because without `;` the text is read as one expression.
    let source = r#"<button @click="if (ok) run()"></button>"#;
    for is_ts in [false, true] {
        let compiled = compile_with(source, true, is_ts);
        assert!(
            has_invalid_expression(&compiled),
            "is_ts={is_ts}: {:?}\n{}",
            compiled.errors,
            compiled.output
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
        let compiled = compile(source);
        assert!(
            compiled.errors.is_empty(),
            "{source}: {:?}",
            compiled.errors
        );
        assert!(
            compiled.output.contains(handler),
            "{source}: {}",
            compiled.output
        );
        assert_parses_as_javascript(&compiled.output);
    }
}

#[test]
fn function_followed_by_a_statement_is_not_a_function_handler() {
    // Vue checks only the first statement here and writes the text
    // unwrapped (`onClick: () => _ctx.run(); _ctx.log()`), which does not
    // parse. The whole text is two statements, so it takes the block form.
    let compiled = compile(r#"<button @click="() => run(); log()"></button>"#);
    assert!(compiled.errors.is_empty(), "{:?}", compiled.errors);
    assert!(
        compiled
            .output
            .contains("onClick: $event => {() => _ctx.run(); _ctx.log()}"),
        "{}",
        compiled.output
    );
    assert_parses_as_javascript(&compiled.output);
}

#[test]
fn statements_outside_an_event_handler_are_invalid_expressions() {
    // Vue reports each of these as an invalid expression.
    for source in [
        r#"<div :title="a; b"></div>"#,
        r#"<div :title="if (ok) run()"></div>"#,
        r#"<p>{{ a; b }}</p>"#,
        r#"<p v-if="a; b">x</p>"#,
        r#"<p v-for="x in a; b">x</p>"#,
    ] {
        for is_ts in [false, true] {
            let compiled = compile_with(source, true, is_ts);
            assert!(
                has_invalid_expression(&compiled),
                "{source} is_ts={is_ts}: {:?}\n{}",
                compiled.errors,
                compiled.output
            );
        }
    }
}

#[test]
fn trailing_line_comment_cannot_hide_the_end_of_a_block_handler() {
    // Vue writes `$event => {_ctx.count++; _ctx.log() // note},` here, so the
    // comment swallows the closing `}` and the `,` before `title`.
    let compiled = compile(r#"<button @click="count++; log() // note" :title="t"></button>"#);
    assert!(compiled.errors.is_empty(), "{:?}", compiled.errors);
    assert!(
        compiled
            .output
            .contains("onClick: $event => {_ctx.count++; _ctx.log() /*  note */},\n"),
        "{}",
        compiled.output
    );
    assert_parses_as_javascript(&compiled.output);

    // Without prefixing, the handler is wrapped by codegen instead of the
    // transform, and that path converts the comment too.
    let unprefixed = compile_with(
        r#"<button @click="count++; log() // note" :title="t"></button>"#,
        false,
        false,
    );
    assert!(
        unprefixed
            .output
            .contains("onClick: $event => {count++; log() /*  note */},\n"),
        "{}",
        unprefixed.output
    );
    assert_parses_as_javascript(&unprefixed.output);

    // A `//` inside a string is not a comment, so the text stays as written,
    // as it does in Vue.
    let in_string = compile(r#"<button @click="count++; run('a // b')"></button>"#);
    assert!(
        in_string
            .output
            .contains("onClick: $event => {_ctx.count++; _ctx.run('a // b')}"),
        "{}",
        in_string.output
    );
    assert_parses_as_javascript(&in_string.output);

    // With the newline the author typed, Vue's unchanged comment
    // (`onClick: _ctx.foo // note`) still parses. This copy converts the
    // comment anyway, as `vize_atelier_core`'s codegen does, and this case
    // pins that conversion.
    let reference = compile("<button @click=\"foo // note\n\" :title=\"t\"></button>");
    assert!(
        reference
            .output
            .contains("onClick: _ctx.foo /*  note */\n,"),
        "{}",
        reference.output
    );
    assert_parses_as_javascript(&reference.output);
}

#[test]
fn typescript_handler_reference_stays_a_reference() {
    // `foo!` is the reference `foo` once its type syntax is removed, so it is
    // passed on unwrapped. Wrapping it as `$event => (_ctx.foo)` would return
    // the function instead of calling it. Vue writes `_ctx.foo!`.
    let compiled = compile_with(r#"<button @click="foo!"></button>"#, true, true);
    assert!(compiled.errors.is_empty(), "{:?}", compiled.errors);
    assert!(
        compiled.output.contains("{ onClick: _ctx.foo }"),
        "{}",
        compiled.output
    );
    assert_parses_as_javascript(&compiled.output);
}
