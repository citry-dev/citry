//! Write a string literal into the generated code from its own source text.
//!
//! ruff's Python parser, which this crate uses, decodes every string literal
//! into a Rust string, and the generator writes a literal back from that
//! decoded value. A lone surrogate escape such as `\ud800` or `\U0000dfff`
//! has no Rust form, so the parser decodes it to U+FFFD (the replacement
//! character), and code written back from the decoded value would hold a
//! different string from the one Python reads. For a literal holding such an
//! escape, the transformer writes the literal's source text into the
//! generated code, and Python decodes the escape itself when the code runs.
//!
//! The module also writes f-string text into the `str.format` template the
//! sandbox builds for an f-string, with each literal brace doubled.

use ruff_python_ast::name::Name;
use ruff_python_ast::{Expr, ExprContext, ExprName, StringFlags};
use ruff_text_size::TextRange;

/// Whether `text`, the source of a string literal that is not raw, holds an
/// escape for a lone surrogate (U+D800 to U+DFFF), which the parser cannot
/// decode as Python does.
///
/// `text` may be a whole literal (prefix and quotes included) or the text
/// between an f-string's or t-string's interpolations. A prefix, a quote or
/// a brace never starts an escape, so passing them in cannot cause a false
/// match.
pub fn has_surrogate_escape(text: &str) -> bool {
    let bytes = text.as_bytes();
    let mut index = 0;
    while index < bytes.len() {
        if bytes[index] != b'\\' {
            index += 1;
            continue;
        }
        let digits = match bytes.get(index + 1) {
            Some(b'u') => 4,
            Some(b'U') => 8,
            // For any other escape, `\\` included, skip the backslash and the
            // character after it, so the second backslash of `\\ud800` never
            // starts an escape.
            _ => {
                index += 2;
                continue;
            }
        };
        let hex = text.get(index + 2..index + 2 + digits);
        if let Some(code) = hex.and_then(|hex| u32::from_str_radix(hex, 16).ok())
            && hex.is_some_and(|hex| hex.bytes().all(|byte| byte.is_ascii_hexdigit()))
            && (0xD800..=0xDFFF).contains(&code)
        {
            return true;
        }
        index += 2;
    }
    false
}

/// An expression the generator writes exactly as `text`.
///
/// ruff's AST has no node for raw source text, so this builds a name node
/// whose identifier is the text: the generator writes a name's identifier as
/// it is. Only the code generator reads the result, because the transformer
/// has finished with the node by then.
pub fn source_text(text: String, range: TextRange) -> Expr {
    Expr::Name(ExprName {
        node_index: Default::default(),
        range,
        id: Name::new(text),
        ctx: ExprContext::Load,
    })
}

/// The text between an f-string's or t-string's interpolations, rewritten
/// as the body of an ordinary string literal that decodes to the same
/// value.
///
/// The two bodies differ only in their braces: the f-string writes a
/// literal brace twice (`{{`), an ordinary string once. The braces of a
/// `\N{...}` escape are part of the escape and stay as they are.
pub fn interpolated_text_as_plain_body(text: &str) -> String {
    let mut body = String::with_capacity(text.len());
    let mut chars = text.chars().peekable();
    while let Some(current) = chars.next() {
        match current {
            '\\' => {
                body.push('\\');
                match chars.peek() {
                    // `\N{NAME}` keeps its braces, which are not doubled.
                    Some('N') => {
                        body.push(chars.next().expect("peeked"));
                        if chars.peek() == Some(&'{') {
                            for name_char in chars.by_ref() {
                                body.push(name_char);
                                if name_char == '}' {
                                    break;
                                }
                            }
                        }
                    }
                    // A backslash before a doubled brace is a literal
                    // backslash, as the parser reads it; the brace pair is
                    // handled on the next step.
                    Some('{' | '}') | None => {}
                    Some(_) => body.push(chars.next().expect("peeked")),
                }
            }
            '{' | '}' => {
                // A single brace would have started an interpolation, so
                // every brace here comes doubled; keep one of the pair.
                if chars.peek() == Some(&current) {
                    chars.next();
                }
                body.push(current);
            }
            other => body.push(other),
        }
    }
    body
}

/// An ordinary string literal with `body` between the quotes of `flags`.
///
/// `body` comes from a literal with the same quotes, so it cannot close them
/// early. Two endings need care, because the text was cut from inside a
/// longer literal: a trailing backslash would escape the closing quote, and
/// a triple-quoted body that ends with the quote character would join the
/// closing quotes.
pub fn plain_literal_text(body: &str, flags: impl StringFlags) -> String {
    let quotes = flags.quote_str();
    let quote = flags.quote_style().as_char();
    let mut body = body.to_owned();
    // Text taken from between a literal's quotes and an interpolation can end
    // in a backslash (`f'\ud800\{x}'`), which the f-string kept as a literal
    // backslash; doubled, it cannot escape the closing quote.
    let trailing_backslashes = body.bytes().rev().take_while(|byte| *byte == b'\\').count();
    if trailing_backslashes % 2 == 1 {
        body.push('\\');
    }
    if flags.is_triple_quoted() && body.ends_with(quote) {
        let backslashes = body[..body.len() - 1]
            .bytes()
            .rev()
            .take_while(|byte| *byte == b'\\')
            .count();
        // An even run of backslashes leaves the quote unescaped.
        if backslashes % 2 == 0 {
            body.pop();
            body.push('\\');
            body.push(quote);
        }
    }
    format!("{quotes}{body}{quotes}")
}

/// `value` written into a `str.format` template so the template gives it
/// back unchanged: each brace is doubled.
pub fn escape_format_braces(value: &str) -> String {
    value.replace('{', "{{").replace('}', "}}")
}

#[cfg(test)]
mod tests {
    use super::{has_surrogate_escape, interpolated_text_as_plain_body};

    #[test]
    fn finds_only_escapes_of_lone_surrogates() {
        for text in [
            r"'\ud800'",
            r"'a\uDFFFb'",
            r"'\U0000d800'",
            r"'\\\ud800'",
            r"\udc00",
        ] {
            assert!(has_surrogate_escape(text), "{text}");
        }
        for text in [
            r"'\\ud800'",
            r"'퟿'",
            r"'\U0001f600'",
            r"'�'",
            r"'\xd8'",
            r"'\N{BULLET}'",
            r"'\ud80'",
            r"'\u+800'",
            "'\u{fffd}'",
            r"'\",
        ] {
            assert!(!has_surrogate_escape(text), "{text}");
        }
    }

    #[test]
    fn interpolated_text_keeps_escapes_and_halves_doubled_braces() {
        for (text, body) in [
            (r"a{{b}}c", r"a{b}c"),
            (r"\ud800{{", r"\ud800{"),
            (r"\N{BULLET}{{", r"\N{BULLET}{"),
            (r"\\{{", r"\\{"),
            (r"\{{", r"\{"),
            (r"\'", r"\'"),
        ] {
            assert_eq!(interpolated_text_as_plain_body(text), body, "{text}");
        }
    }
}
